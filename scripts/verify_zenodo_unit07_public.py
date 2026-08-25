#!/usr/bin/env python3
"""Independently verify the public Unit 7 Zenodo bytes and single concept lineage."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path

import httpx


RECORD_ID = 22071323
PREDECESSOR_ID = 22070425
CONCEPT_ID = "22059977"
CONCEPT_DOI = "10.5281/zenodo.22059977"
PDF_NAME = "geometri-diferensial-manifold-mulus-hingga-unit-07-id.pdf"
MODEL = "OpenAI Codex gpt-5.6-sol, Ultra"


def digest_bytes(value: bytes, algorithm: str = "sha256") -> str:
    return hashlib.new(algorithm, value).hexdigest()


def get_json(client: httpx.Client, url: str) -> dict:
    response = client.get(url, timeout=90)
    if response.status_code != 200:
        raise RuntimeError(f"HTTP {response.status_code}: {url}")
    value = response.json()
    if not isinstance(value, dict):
        raise RuntimeError(f"non-object JSON: {url}")
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    receipt = (root / args.receipt).resolve()
    if receipt.exists():
        raise RuntimeError(f"refusing to overwrite receipt: {receipt}")

    local_dir = root / "output/release-unit07"
    manifest = json.loads((root / "qa/unit-07/RELEASE_PREPARATION_RECEIPT.json").read_text(encoding="utf-8"))
    local = {}
    for item in manifest["files"]:
        path = local_dir / item["filename"]
        data = path.read_bytes()
        local[item["filename"]] = {
            "bytes": len(data),
            "sha256": digest_bytes(data),
            "md5": digest_bytes(data, "md5"),
        }
        if local[item["filename"]] != {k: item[k] for k in ("bytes", "sha256", "md5")}:
            raise RuntimeError(f"local payload changed: {item['filename']}")
    expected_names = list(local)

    with httpx.Client(trust_env=False, follow_redirects=True, timeout=90) as client:
        record = get_json(client, f"https://zenodo.org/api/records/{RECORD_ID}")
        predecessor = get_json(client, f"https://zenodo.org/api/records/{PREDECESSOR_ID}")
        versions = get_json(client, f"https://zenodo.org/api/records/{RECORD_ID}/versions")

        if record.get("id") != RECORD_ID or str(record.get("conceptrecid")) != CONCEPT_ID or record.get("conceptdoi") != CONCEPT_DOI:
            raise RuntimeError("record/concept identity mismatch")
        if record.get("status") != "published" or (record.get("metadata") or {}).get("version") != "2026.08.23-unit07":
            raise RuntimeError("Unit 7 record is not published with the expected version")
        if predecessor.get("id") != PREDECESSOR_ID or str(predecessor.get("conceptrecid")) != CONCEPT_ID:
            raise RuntimeError("predecessor lineage mismatch")
        latest_url = ((predecessor.get("links") or {}).get("latest"))
        latest = get_json(client, latest_url)
        if latest.get("id") != RECORD_ID:
            raise RuntimeError("predecessor latest link does not resolve to Unit 7")

        metadata = record.get("metadata") or {}
        title = str(metadata.get("title", ""))
        description = str(metadata.get("description", ""))
        if "TTP" in title or "TTP" in description or "Translation and Transcription Project" in title or "Translation and Transcription Project" in description:
            raise RuntimeError("umbrella label leaked into title/description")
        if MODEL not in description or "active_partial" not in description:
            raise RuntimeError("truthful scope/model disclosure missing")
        contributors = metadata.get("contributors") or []
        ttp_count = sum(1 for x in contributors if (x.get("name") if isinstance(x, dict) else None) == "TTP")
        if ttp_count != 1:
            raise RuntimeError("TTP organization anchor is not exactly once")

        public_files = record.get("files") or []
        public_by_name = {x.get("key"): x for x in public_files if isinstance(x, dict)}
        if set(public_by_name) != set(expected_names):
            raise RuntimeError("public file set differs from local six-file payload")
        thumbnails = ((record.get("links") or {}).get("thumbnails") or {})
        if not any(PDF_NAME in str(url) for url in thumbnails.values()):
            raise RuntimeError("PDF is not exposed as Zenodo's default preview surface")

        file_results = []
        for name in expected_names:
            item = public_by_name[name]
            if item.get("size") != local[name]["bytes"] or str(item.get("checksum", "")).removeprefix("md5:") != local[name]["md5"]:
                raise RuntimeError(f"public manifest identity mismatch: {name}")
            url = ((item.get("links") or {}).get("self"))
            if not url:
                raise RuntimeError(f"missing public download URL: {name}")
            response = client.get(url, timeout=300)
            if response.status_code != 200:
                raise RuntimeError(f"public download HTTP {response.status_code}: {name}")
            value = {"bytes": len(response.content), "sha256": digest_bytes(response.content), "md5": digest_bytes(response.content, "md5")}
            if value != local[name]:
                raise RuntimeError(f"anonymous byte mismatch: {name}")
            file_results.append({"name": name, **value, "matches_local": True, "download_url": url})

        hits = (versions.get("hits") or {}).get("hits") or []
        same_concept = [x for x in hits if str(x.get("conceptrecid")) == CONCEPT_ID]
        same_version = [x for x in same_concept if (x.get("metadata") or {}).get("version") == "2026.08.23-unit07"]
        if len(same_version) != 1:
            raise RuntimeError("duplicate Unit 7 version detected in concept lineage")

    result = {
        "schema_version": 1,
        "workflow": "o011-verify-zenodo-unit07-public-v1",
        "status": "pass",
        "verified_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "record_id": RECORD_ID,
        "concept_record_id": int(CONCEPT_ID),
        "doi": record.get("doi"),
        "concept_doi": CONCEPT_DOI,
        "record_url": f"https://zenodo.org/records/{RECORD_ID}",
        "predecessor_id": PREDECESSOR_ID,
        "public_file_order": [x.get("key") for x in public_files],
        "reader_first_order": expected_names,
        "pdf_default_preview_verified": True,
        "version_count_in_concept_response": len(same_concept),
        "unit07_version_count_in_concept_response": len(same_version),
        "files": file_results,
        "metadata_title": title,
        "ttp_organization_anchor_count": ttp_count,
        "authentication_used": False,
    }
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text(json.dumps(result, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"status": "pass", "record_id": RECORD_ID, "doi": record.get("doi"), "files": len(file_results)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
