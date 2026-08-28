#!/usr/bin/env python3
"""Independently and anonymously verify the public Zenodo Unit 22 bytes."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import urllib.request
from pathlib import Path
from typing import Any


RECORD_ID = 22146873
CONCEPT_ID = 22059977
PREDECESSOR_ID = 22134954
DOI = "10.5281/zenodo.22146873"
CONCEPT_DOI = "10.5281/zenodo.22059977"
VERSION = "2026.08.28-unit22"
PDF_NAME = "geometri-diferensial-manifold-mulus-hingga-unit-22-id.pdf"
PREPARATION = Path("qa/unit-22/RELEASE_PREPARATION_RECEIPT.json")
PUBLICATION = Path("qa/unit-22/ZENODO_PUBLICATION_RECEIPT.json")
DEFAULT_RECEIPT = Path("qa/unit-22/ZENODO_PUBLIC_READBACK_RECEIPT.json")


def fail(message: str) -> None:
    raise RuntimeError(message)


def api_json(url: str) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.inveniordm.v1+json",
            "User-Agent": "O011-unit22-independent-zenodo-verifier/1.0",
        },
    )
    with urllib.request.urlopen(request, timeout=180) as response:
        value = json.load(response)
    if not isinstance(value, dict):
        fail(f"non-object response from {url}")
    return value


def stream_identity(url: str) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={"Accept": "*/*", "User-Agent": "O011-unit22-independent-zenodo-verifier/1.0"},
    )
    sha256 = hashlib.sha256()
    md5 = hashlib.md5()
    size = 0
    with urllib.request.urlopen(request, timeout=300) as response:
        while True:
            block = response.read(1024 * 1024)
            if not block:
                break
            size += len(block)
            sha256.update(block)
            md5.update(block)
    return {"bytes": size, "sha256": sha256.hexdigest(), "md5": md5.hexdigest()}


def checksum_md5(entry: dict[str, Any]) -> str:
    return str(entry.get("checksum") or "").removeprefix("md5:")


def write_once(path: Path, value: dict[str, Any]) -> None:
    if path.exists():
        fail(f"refusing to overwrite {path}")
    serialized = json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n"
    lowered = serialized.lower()
    if any(marker in lowered for marker in ("access_token", "authorization: bearer", "zenodo_token")):
        fail("receipt failed credential scan")
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(serialized, encoding="utf-8", newline="\n")
    os.replace(temporary, path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, default=DEFAULT_RECEIPT)
    args = parser.parse_args()
    root = args.root.resolve()
    receipt_path = (root / args.receipt).resolve()
    receipt_path.relative_to(root)

    stage_path = root / PREPARATION
    publication_path = root / PUBLICATION
    stage = json.loads(stage_path.read_text(encoding="utf-8"))
    publication = json.loads(publication_path.read_text(encoding="utf-8"))
    rows = stage.get("files")
    if (
        stage.get("status") != "pass"
        or stage.get("workflow") != "o011-prepare-release-unit22-v1"
        or stage.get("version") != VERSION
        or not isinstance(rows, list)
        or len(rows) != 7
    ):
        fail("Unit 22 release preparation is not exact")
    if (
        publication.get("status") != "pass"
        or publication.get("workflow") != "o011-publish-zenodo-unit22-v1"
        or publication.get("record_id") != RECORD_ID
        or publication.get("doi") != DOI
    ):
        fail("Unit 22 publication receipt is not exact")
    expected = {str(row["filename"]): row for row in rows}

    record = api_json(f"https://zenodo.org/api/records/{RECORD_ID}")
    metadata = record.get("metadata") or {}
    files = record.get("files") or {}
    entries = files.get("entries") or {}
    if (
        str(record.get("id")) != str(RECORD_ID)
        or str(record.get("conceptrecid") or (record.get("parent") or {}).get("id")) != str(CONCEPT_ID)
        or str(record.get("doi") or ((record.get("pids") or {}).get("doi") or {}).get("identifier")) != DOI
        or record.get("status") != "published"
        or (record.get("access") or {}).get("record") != "public"
        or (record.get("access") or {}).get("files") != "public"
        or metadata.get("version") != VERSION
        or files.get("default_preview") != PDF_NAME
        or not isinstance(entries, dict)
        or set(entries) != set(expected)
    ):
        fail("public Unit 22 record metadata, access, preview, or inventory differs")
    if "Unit 22" not in str(metadata.get("title") or ""):
        fail("public Unit 22 title differs")
    versions = api_json(f"https://zenodo.org/api/records/{RECORD_ID}/versions?size=25")
    version_hits = ((versions.get("hits") or {}).get("hits"))
    if (
        not isinstance(version_hits, list)
        or [str(item.get("id")) for item in version_hits[:2] if isinstance(item, dict)]
        != [str(RECORD_ID), str(PREDECESSOR_ID)]
    ):
        fail("public Unit 22 direct predecessor differs")

    verified: list[dict[str, Any]] = []
    for name in stage.get("public_file_order", []):
        wanted = expected[name]
        entry = entries[name]
        if entry.get("size") != wanted.get("bytes") or checksum_md5(entry) != wanted.get("md5"):
            fail(f"public Unit 22 inventory identity differs: {name}")
        links = entry.get("links") or {}
        url = str(links.get("content") or links.get("self") or "")
        if not url.startswith("https://zenodo.org/") or "access_token=" in url.lower():
            fail(f"unsafe anonymous download URL: {name}")
        actual = stream_identity(url)
        wanted_identity = {key: wanted.get(key) for key in ("bytes", "sha256", "md5")}
        if actual != wanted_identity:
            fail(f"anonymous Unit 22 bytes differ: {name}")
        verified.append({"name": name, **actual, "download_url": url})

    latest_url = str((record.get("links") or {}).get("latest") or "")
    latest = api_json(latest_url)
    if str(latest.get("id")) != str(RECORD_ID):
        fail("Unit 22 is not latest in its Zenodo concept")
    receipt = {
        "schema_version": 1,
        "workflow": "o011-independent-zenodo-unit22-public-readback-v1",
        "status": "pass",
        "verified_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "authentication_used": False,
        "record_id": RECORD_ID,
        "concept_record_id": CONCEPT_ID,
        "predecessor_record_id": PREDECESSOR_ID,
        "doi": DOI,
        "concept_doi": CONCEPT_DOI,
        "version": VERSION,
        "record_url": f"https://zenodo.org/records/{RECORD_ID}",
        "record_status": "published",
        "record_access": "public",
        "files_access": "public",
        "pdf_default_preview": PDF_NAME,
        "pdf_default_preview_verified": True,
        "expected_reader_first_order": stage.get("public_file_order"),
        "rdm_file_order": list(entries),
        "files": verified,
        "file_count": len(verified),
        "total_bytes": sum(int(row["bytes"]) for row in verified),
        "all_downloaded_bytes_sha256_md5_match": True,
        "latest_in_concept": True,
        "publication_receipt_sha256": hashlib.sha256(publication_path.read_bytes()).hexdigest(),
        "preparation_receipt_sha256": hashlib.sha256(stage_path.read_bytes()).hexdigest(),
    }
    write_once(receipt_path, receipt)
    print(json.dumps({"status": "pass", "record_id": RECORD_ID, "doi": DOI, "files": len(verified), "bytes": receipt["total_bytes"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
