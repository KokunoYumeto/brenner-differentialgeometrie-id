#!/usr/bin/env python3
"""Anonymously verify the clean latest Unit 5 Zenodo version and every byte."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path

import requests


RECORD_ID = 22060146
CONCEPT_ID = "22059977"
DOI = "10.5281/zenodo.22060146"
CONCEPT_DOI = "10.5281/zenodo.22059977"
LOCAL_FILES = {
    "geometri-diferensial-manifold-mulus-hingga-unit-05-id.pdf":
        "output/pdf/geometri-diferensial-manifold-mulus-hingga-unit-05-id.pdf",
    "geometri-diferensial-manifold-mulus-brenner-id-unit05-20260822.zip":
        "output/zenodo/geometri-diferensial-manifold-mulus-brenner-id-unit05-20260822.zip",
    "RELEASE_NOTES_20260822.md": "qa/unit-05/RELEASE_NOTES_20260822.md",
}


def hashes(path: Path) -> tuple[int, str, str]:
    sha256 = hashlib.sha256()
    md5 = hashlib.md5()
    size = 0
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            size += len(block)
            sha256.update(block)
            md5.update(block)
    return size, sha256.hexdigest(), md5.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    args = parser.parse_args()

    root = args.root.resolve()
    output_dir = args.output_dir.resolve()
    if output_dir.exists():
        raise SystemExit(f"refusing to overwrite readback directory: {output_dir}")
    output_dir.mkdir(parents=True)
    expected_metadata = json.loads(
        (root / args.metadata).read_text(encoding="utf-8")
    )["metadata"]

    response = requests.get(
        f"https://zenodo.org/api/records/{RECORD_ID}",
        timeout=60,
    )
    if response.status_code != 200:
        raise SystemExit(f"anonymous record read failed: HTTP {response.status_code}")
    record = response.json()
    metadata = record.get("metadata") or {}
    if record.get("id") != RECORD_ID or str(record.get("conceptrecid")) != CONCEPT_ID:
        raise SystemExit("public record identity mismatch")
    if record.get("doi") != DOI or record.get("conceptdoi") != CONCEPT_DOI:
        raise SystemExit("public DOI identity mismatch")
    for field in (
        "title",
        "description",
        "publication_date",
        "version",
        "language",
        "keywords",
    ):
        if metadata.get(field) != expected_metadata.get(field):
            raise SystemExit(f"public metadata mismatch: {field}")
    if (metadata.get("license") or {}).get("id") != expected_metadata.get("license"):
        raise SystemExit("public record-wide license mismatch")
    creators = [item.get("name") for item in metadata.get("creators", [])]
    contributors = [
        {"name": item.get("name"), "type": item.get("type")}
        for item in metadata.get("contributors", [])
    ]
    if creators != [item["name"] for item in expected_metadata["creators"]]:
        raise SystemExit("public creator mismatch")
    if contributors != expected_metadata["contributors"]:
        raise SystemExit("public contributor mismatch")
    if "TTP" in metadata.get("title", "") or "TTP" in metadata.get("description", ""):
        raise SystemExit("umbrella label leaked into title or description")
    if sum(item.get("name") == "TTP" for item in metadata.get("contributors", [])) != 1:
        raise SystemExit("expected exactly one TTP contributor")

    remote_by_name = {item["key"]: item for item in record.get("files", [])}
    if set(remote_by_name) != set(LOCAL_FILES):
        raise SystemExit("public three-file inventory mismatch")
    result_files = []
    for name, relative in LOCAL_FILES.items():
        local = (root / relative).resolve()
        local_size, local_sha256, local_md5 = hashes(local)
        remote = remote_by_name[name]
        if remote.get("size") != local_size:
            raise SystemExit(f"public API size mismatch: {name}")
        if str(remote.get("checksum", "")).removeprefix("md5:") != local_md5:
            raise SystemExit(f"public API checksum mismatch: {name}")
        download = requests.get(remote["links"]["self"], stream=True, timeout=300)
        if download.status_code != 200:
            raise SystemExit(f"anonymous download failed for {name}: HTTP {download.status_code}")
        destination = output_dir / name
        with destination.open("wb") as stream:
            for block in download.iter_content(1024 * 1024):
                if block:
                    stream.write(block)
        public_size, public_sha256, public_md5 = hashes(destination)
        if (public_size, public_sha256, public_md5) != (
            local_size,
            local_sha256,
            local_md5,
        ):
            raise SystemExit(f"anonymous public-byte mismatch: {name}")
        result_files.append(
            {
                "name": name,
                "bytes": public_size,
                "sha256": public_sha256,
                "md5": public_md5,
                "download_url": remote["links"]["self"],
                "matches_local": True,
            }
        )

    result = {
        "status": "pass",
        "authentication_used": False,
        "verified_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "record_id": RECORD_ID,
        "concept_record_id": int(CONCEPT_ID),
        "doi": DOI,
        "concept_doi": CONCEPT_DOI,
        "record_url": f"https://zenodo.org/records/{RECORD_ID}",
        "api_url": f"https://zenodo.org/api/records/{RECORD_ID}",
        "metadata_license": expected_metadata["license"],
        "files": result_files,
    }
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))


if __name__ == "__main__":
    main()
