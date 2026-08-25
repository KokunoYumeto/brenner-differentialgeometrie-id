#!/usr/bin/env python3
"""Independently read back and hash the public Zenodo Unit 13 release."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


RECORD_ID = 22096736
CONCEPT_ID = 22059977
DOI = "10.5281/zenodo.22096736"
CONCEPT_DOI = "10.5281/zenodo.22059977"
VERSION = "2026.08.25-unit13"
TITLE = "Geometri Diferensial dan Manifold Mulus — Edisi Bahasa Indonesia (Batas Unit 13)"
PDF_NAME = "geometri-diferensial-manifold-mulus-hingga-unit-13-id.pdf"
RDM_ACCEPT = "application/vnd.inveniordm.v1+json"


def fail(message: str) -> None:
    raise RuntimeError(message)


def get(url: str, *, accept: str | None = None) -> urllib.response.addinfourl:
    headers = {"User-Agent": "O011-unit13-independent-readback/1.0"}
    if accept:
        headers["Accept"] = accept
    for attempt in range(5):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=300)
        except urllib.error.HTTPError as exc:
            if exc.code in (502, 503, 504) and attempt < 4:
                time.sleep(min(2 ** attempt, 8))
                continue
            raise
        except urllib.error.URLError:
            if attempt < 4:
                time.sleep(min(2 ** attempt, 8))
                continue
            raise
    fail(f"anonymous GET exhausted retries: {url}")


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        fail(f"expected a JSON object: {path}")
    return value


def hash_file(path: Path) -> dict[str, int | str]:
    sha = hashlib.sha256()
    md5 = hashlib.md5()
    size = 0
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            size += len(block)
            sha.update(block)
            md5.update(block)
    return {"bytes": size, "sha256": sha.hexdigest(), "md5": md5.hexdigest()}


def download(url: str, destination: Path) -> dict[str, int | str]:
    with get(url) as response, destination.open("wb") as output:
        while True:
            block = response.read(1024 * 1024)
            if not block:
                break
            output.write(block)
    return hash_file(destination)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--preparation-receipt", type=Path, required=True)
    parser.add_argument("--publication-receipt", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()

    root = args.root.resolve()
    preparation_path = (root / args.preparation_receipt).resolve()
    publication_path = (root / args.publication_receipt).resolve()
    receipt_path = (root / args.receipt).resolve()
    for path in (preparation_path, publication_path, receipt_path):
        if path != root and root not in path.parents:
            fail(f"path escaped project root: {path}")
    if receipt_path.exists():
        fail(f"refusing to overwrite public-readback receipt: {receipt_path}")

    preparation = load_json(preparation_path)
    publication = load_json(publication_path)
    expected_rows = preparation.get("files")
    if preparation.get("status") != "pass" or not isinstance(expected_rows, list) or len(expected_rows) != 7:
        fail("release-preparation receipt is not the passing seven-file Unit 13 boundary")
    expected = {str(row["filename"]): row for row in expected_rows if isinstance(row, dict)}
    if len(expected) != 7 or PDF_NAME not in expected:
        fail("release-preparation inventory is malformed")
    if publication.get("status") != "pass" or publication.get("record_id") != RECORD_ID:
        fail("publication receipt is not the passing Unit 13 record")

    with get(f"https://zenodo.org/api/records/{RECORD_ID}", accept=RDM_ACCEPT) as response:
        record = json.load(response)
    metadata = record.get("metadata") or {}
    files = record.get("files") or {}
    entries = files.get("entries") or {}
    if (
        str(record.get("id")) != str(RECORD_ID)
        or str((record.get("parent") or {}).get("id")) != str(CONCEPT_ID)
        or ((record.get("pids") or {}).get("doi") or {}).get("identifier") != DOI
        or record.get("status") != "published"
        or metadata.get("title") != TITLE
        or metadata.get("version") != VERSION
        or (record.get("access") or {}).get("record") != "public"
        or files.get("default_preview") != PDF_NAME
        or not isinstance(entries, dict)
        or set(entries) != set(expected)
    ):
        fail("public Unit 13 record metadata, lineage, access, preview, or inventory is not exact")

    verified: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="o011-unit13-anonymous-readback-") as temporary:
        temporary_root = Path(temporary)
        for name in expected:
            if Path(name).name != name:
                fail(f"unsafe public filename: {name}")
            entry = entries[name]
            expected_row = expected[name]
            inventory_md5 = str(entry.get("checksum", "")).removeprefix("md5:")
            if entry.get("size") != expected_row.get("bytes") or inventory_md5 != expected_row.get("md5"):
                fail(f"public inventory identity differs before download: {name}")
            url = (entry.get("links") or {}).get("content")
            if not isinstance(url, str) or not url.startswith("https://zenodo.org/"):
                fail(f"unsafe or absent public content URL: {name}")
            actual = download(url, temporary_root / name)
            wanted = {key: expected_row.get(key) for key in ("bytes", "sha256", "md5")}
            if actual != wanted:
                fail(f"anonymous downloaded bytes differ: {name}")
            verified.append({"name": name, **actual})

    receipt = {
        "schema_version": 1,
        "workflow": "o011-independent-zenodo-unit13-public-readback-v1",
        "status": "pass",
        "verified_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "authentication_used": False,
        "record_id": RECORD_ID,
        "concept_record_id": CONCEPT_ID,
        "doi": DOI,
        "concept_doi": CONCEPT_DOI,
        "version": VERSION,
        "coverage": "active_partial_through_unit_13",
        "record_status": "published",
        "pdf_default_preview": PDF_NAME,
        "pdf_default_preview_verified": True,
        "rdm_file_order": files.get("order"),
        "file_count": len(verified),
        "total_bytes": sum(int(row["bytes"]) for row in verified),
        "all_inventory_md5_matches": True,
        "all_downloaded_bytes_sha256_md5_match": True,
        "temporary_downloads_removed": True,
        "preparation_receipt_sha256": hash_file(preparation_path)["sha256"],
        "publication_receipt_sha256": hash_file(publication_path)["sha256"],
        "files": verified,
    }
    payload = (json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = receipt_path.with_name(receipt_path.name + ".tmp")
    if temporary_path.exists():
        fail(f"refusing to overwrite temporary receipt: {temporary_path}")
    temporary_path.write_bytes(payload)
    os.replace(temporary_path, receipt_path)
    print(json.dumps({"status": "pass", "record_id": RECORD_ID, "files": len(verified), "bytes": receipt["total_bytes"], "receipt": receipt_path.relative_to(root).as_posix()}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
