#!/usr/bin/env python3
"""Independently and anonymously verify the public Zenodo Unit 13 r1 record."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path
from typing import Any


CONCEPT_ID = 22059977
CONCEPT_DOI = "10.5281/zenodo.22059977"
PREDECESSOR_ID = 22096736
PREDECESSOR_DOI = "10.5281/zenodo.22096736"
VERSION = "2026.08.25-unit13-r1"
PUBLICATION_DATE = "2026-08-25"
TITLE = "Geometri Diferensial dan Manifold Mulus — Edisi Bahasa Indonesia (Batas Unit 13, Revisi Paket Sumber)"
MODEL = "OpenAI Codex gpt-5.6-sol, Ultra"
PDF_NAME = "geometri-diferensial-manifold-mulus-hingga-unit-13-id.pdf"
HTML_ZIP_NAME = "geometri-diferensial-manifold-mulus-brenner-id-unit13-html-20260825.zip"
SOURCE_ZIP_NAME = "geometri-diferensial-manifold-mulus-unit13-source-r1-20260825.zip"
EXPECTED_ORDER = [
    PDF_NAME,
    HTML_ZIP_NAME,
    SOURCE_ZIP_NAME,
    "LICENSE.md",
    "RELEASE_NOTES_UNIT13_R1_20260825.md",
    "FILE_MANIFEST.csv",
    "CHECKSUMS.sha256",
]
PDF_IDENTITY = {
    "bytes": 6_396_207,
    "sha256": "a4d7e55604de9bfb6556d78461db8255a6c584d36b8934a0993b2386ad5832a7",
}
HTML_IDENTITY = {
    "bytes": 5_331_749,
    "sha256": "22dacc34c9381c44aebeccf0c48e7cf107c991d7ff3c8c74ec4d950e77e77cf7",
}
RDM_ACCEPT = "application/vnd.inveniordm.v1+json"
TTP_RE = re.compile(r"(?i)(?:\bTTP\b|Translation\s+and\s+Transcription\s+Project)")
REQUIRED_CORRECTION_SENTENCE = (
    "Reader content and validated PDF/HTML bytes are unchanged from record "
    "22096736; this revision corrects the resumable source package and its documentation."
)


def fail(message: str) -> None:
    raise RuntimeError(message)


def inside(root: Path, path: Path, label: str) -> Path:
    resolved = path.resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        fail(f"{label} escaped the repository root")
    return resolved


def load_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        fail(f"unable to read valid {label} JSON")
    if not isinstance(value, dict):
        fail(f"{label} must be a JSON object")
    return value


def hash_file(path: Path) -> dict[str, Any]:
    sha = hashlib.sha256()
    md5 = hashlib.md5()
    size = 0
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            size += len(block)
            sha.update(block)
            md5.update(block)
    return {"bytes": size, "sha256": sha.hexdigest(), "md5": md5.hexdigest()}


def anonymous_get(url: str, *, accept: str | None = None) -> urllib.response.addinfourl:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != "zenodo.org" or "access_token" in parsed.query.lower():
        fail("refusing a non-public or non-Zenodo URL")
    headers = {"User-Agent": "O011-unit13-r1-independent-readback/1.0"}
    if accept:
        headers["Accept"] = accept
    for attempt in range(5):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=300)
        except urllib.error.HTTPError as exc:
            if exc.code in (502, 503, 504) and attempt < 4:
                time.sleep(min(2**attempt, 8))
                continue
            raise
        except urllib.error.URLError:
            if attempt < 4:
                time.sleep(min(2**attempt, 8))
                continue
            raise
    fail("anonymous GET exhausted retries")


def download(url: str, destination: Path) -> dict[str, Any]:
    with anonymous_get(url) as response, destination.open("wb") as output:
        while True:
            block = response.read(1024 * 1024)
            if not block:
                break
            output.write(block)
    return hash_file(destination)


def record_id(record: dict[str, Any]) -> int:
    value = record.get("id")
    if not str(value).isdigit():
        fail("public record lacks a numeric ID")
    return int(value)


def concept_id(record: dict[str, Any]) -> str:
    return str(record.get("conceptrecid") or (record.get("parent") or {}).get("id") or "")


def record_doi(record: dict[str, Any]) -> str:
    return str(record.get("doi") or (((record.get("pids") or {}).get("doi") or {}).get("identifier")) or "")


def inventory(record: dict[str, Any]) -> tuple[list[str], dict[str, dict[str, Any]], str | None]:
    files = record.get("files")
    if isinstance(files, dict) and isinstance(files.get("entries"), dict):
        entries = files["entries"]
        order = files.get("order")
        order = list(order) if isinstance(order, list) and order else list(entries)
        preview = files.get("default_preview")
    elif isinstance(files, list):
        entries = {}
        order = []
        preview = None
        for item in files:
            if not isinstance(item, dict) or not isinstance(item.get("key"), str):
                fail("public file inventory is malformed")
            entries[item["key"]] = item
            order.append(item["key"])
    else:
        fail("public file inventory is absent")
    if not all(isinstance(name, str) and isinstance(item, dict) for name, item in entries.items()):
        fail("public file inventory contains a malformed entry")
    return order, entries, preview


def entry_md5(entry: dict[str, Any]) -> str:
    return str(entry.get("checksum", "")).removeprefix("md5:")


def entry_url(entry: dict[str, Any]) -> str:
    links = entry.get("links") or {}
    value = links.get("content") or links.get("self")
    if not isinstance(value, str):
        fail("public file entry lacks a content URL")
    parsed = urllib.parse.urlparse(value)
    if parsed.scheme != "https" or parsed.hostname != "zenodo.org" or "access_token" in parsed.query.lower():
        fail("public content URL is unsafe")
    return value


def validate_metadata(record: dict[str, Any]) -> None:
    metadata = record.get("metadata") or {}
    description = metadata.get("description")
    resource_type = metadata.get("resource_type") or {}
    if (
        not isinstance(resource_type, dict)
        or resource_type.get("id") != "publication-book"
        or metadata.get("title") != TITLE
        or metadata.get("publication_date") != PUBLICATION_DATE
        or metadata.get("version") != VERSION
        or not isinstance(description, str)
        or description.count(MODEL) != 1
        or REQUIRED_CORRECTION_SENTENCE not in description
        or "active_partial" not in description
        or "Kuliah 1–13" not in description
        or "Lembar Kerja 1–13" not in description
        or "CC BY-SA 4.0" not in description
        or "Component media retain their file-specific rights; no blanket media license is inferred." not in description
    ):
        fail("public corrective metadata lost its exact scope, rights, provenance, or correction disclosure")

    creators = metadata.get("creators") or []
    creator_names = [(item.get("person_or_org") or item).get("name") for item in creators if isinstance(item, dict)]
    contributors = metadata.get("contributors") or []
    contributor_projection = []
    for item in contributors:
        if not isinstance(item, dict):
            fail("public contributor metadata is malformed")
        person = item.get("person_or_org") or item
        role = item.get("role") or {}
        contributor_projection.append(
            {
                "name": person.get("name"),
                "type": str(person.get("type", "")).lower(),
                "role": role.get("id") if isinstance(role, dict) else role,
            }
        )
    if creator_names != ["Brenner, Holger"]:
        fail("public source-author attribution is not exact")
    if contributor_projection != [{"name": "TTP", "type": "organizational", "role": "other"}]:
        fail("public metadata lacks the one exact organizational contributor anchor")
    if len(TTP_RE.findall(json.dumps(metadata, ensure_ascii=False))) != 1:
        fail("TTP does not occur exactly once in public metadata")

    languages = metadata.get("languages") or []
    rights = metadata.get("rights") or []
    language_ids = [item.get("id") for item in languages if isinstance(item, dict)]
    right_ids = [item.get("id") for item in rights if isinstance(item, dict)]
    if language_ids != ["ind"] or right_ids != ["other-open"]:
        fail("public language or mixed-rights metadata is not exact")
    related = metadata.get("related_identifiers") or []
    if len(related) != 1 or not isinstance(related[0], dict):
        fail("public source relationship metadata is absent or ambiguous")
    relation = related[0].get("relation_type") or {}
    related_resource = related[0].get("resource_type") or {}
    if (
        related[0].get("identifier")
        != "https://de.wikiversity.org/wiki/Kurs:Differentialgeometrie_(Osnabr%C3%BCck_2023)"
        or related[0].get("scheme") != "url"
        or not isinstance(relation, dict)
        or relation.get("id") != "isderivedfrom"
        or not isinstance(related_resource, dict)
        or related_resource.get("id") != "publication-book"
    ):
        fail("public source relationship metadata is not exact")


def verify_predecessor_readers(
    expected: dict[str, dict[str, Any]],
    temporary_root: Path,
) -> list[dict[str, Any]]:
    with anonymous_get(f"https://zenodo.org/api/records/{PREDECESSOR_ID}", accept=RDM_ACCEPT) as response:
        predecessor = json.load(response)
    if (
        record_id(predecessor) != PREDECESSOR_ID
        or concept_id(predecessor) != str(CONCEPT_ID)
        or record_doi(predecessor) != PREDECESSOR_DOI
        or (predecessor.get("metadata") or {}).get("version") != "2026.08.25-unit13"
    ):
        fail("public predecessor is not the exact original Unit 13 version")
    _, entries, _ = inventory(predecessor)
    results: list[dict[str, Any]] = []
    for name in (PDF_NAME, HTML_ZIP_NAME):
        if name not in entries:
            fail(f"public predecessor lacks {name}")
        wanted = {key: expected[name].get(key) for key in ("bytes", "sha256", "md5")}
        if entries[name].get("size") != wanted["bytes"] or entry_md5(entries[name]) != wanted["md5"]:
            fail(f"predecessor inventory differs from corrective stage: {name}")
        actual = download(entry_url(entries[name]), temporary_root / f"predecessor-{name}")
        if actual != wanted:
            fail(f"anonymously downloaded predecessor reader differs: {name}")
        results.append({"name": name, **actual, "matches_corrective_reader": True})
    return results


def write_once(path: Path, value: dict[str, Any]) -> None:
    if path.exists():
        fail("refusing to overwrite the independent public-readback receipt")
    payload = (json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n").encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    if temporary.exists():
        fail("refusing to overwrite a temporary public-readback receipt")
    temporary.write_bytes(payload)
    os.replace(temporary, path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--preparation-receipt", type=Path, required=True)
    parser.add_argument("--publication-receipt", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()

    root = args.root.resolve()
    preparation_path = inside(root, root / args.preparation_receipt, "preparation receipt")
    publication_path = inside(root, root / args.publication_receipt, "publication receipt")
    receipt_path = inside(root, root / args.receipt, "public-readback receipt")
    if receipt_path.exists():
        fail("refusing to overwrite the independent public-readback receipt")

    preparation = load_object(preparation_path, "release-preparation receipt")
    publication = load_object(publication_path, "publication receipt")
    rows = preparation.get("files")
    if (
        preparation.get("schema_version") != 1
        or preparation.get("workflow") != "o011-prepare-release-unit13-source-r1-v1"
        or preparation.get("status") != "pass"
        or not isinstance(rows, list)
        or [row.get("filename") for row in rows if isinstance(row, dict)] != EXPECTED_ORDER
    ):
        fail("release-preparation receipt is not the exact passing Unit 13 r1 stage")
    expected = {str(row["filename"]): row for row in rows if isinstance(row, dict)}
    if set(expected) != set(EXPECTED_ORDER):
        fail("release-preparation file inventory is malformed")
    for name, identity in ((PDF_NAME, PDF_IDENTITY), (HTML_ZIP_NAME, HTML_IDENTITY)):
        if {key: expected[name].get(key) for key in ("bytes", "sha256")} != identity:
            fail(f"release preparation changed validated reader bytes: {name}")

    if (
        publication.get("schema_version") != 1
        or publication.get("workflow") != "o011-publish-zenodo-unit13-source-r1-v1"
        or publication.get("status") != "pass"
        or publication.get("concept_record_id") != CONCEPT_ID
        or publication.get("predecessor_record_id") != PREDECESSOR_ID
        or publication.get("version") != VERSION
        or publication.get("reader_content_unchanged") is not True
    ):
        fail("publication receipt is not the exact passing Unit 13 r1 transaction")
    published_id = publication.get("record_id")
    if not isinstance(published_id, int) or published_id <= 0:
        fail("publication receipt lacks a valid public record ID")
    expected_doi = f"10.5281/zenodo.{published_id}"
    if publication.get("doi") != expected_doi or publication.get("concept_doi") != CONCEPT_DOI:
        fail("publication receipt DOI lineage is not exact")

    with anonymous_get(f"https://zenodo.org/api/records/{published_id}", accept=RDM_ACCEPT) as response:
        record = json.load(response)
    order, entries, default_preview = inventory(record)
    if (
        record_id(record) != published_id
        or concept_id(record) != str(CONCEPT_ID)
        or record_doi(record) != expected_doi
        or record.get("status") != "published"
        or (record.get("access") or {}).get("record") != "public"
        or default_preview != PDF_NAME
        or set(entries) != set(EXPECTED_ORDER)
        or len(entries) != len(EXPECTED_ORDER)
    ):
        fail("public Unit 13 r1 lineage, access, preview, or inventory is not exact")
    validate_metadata(record)

    verified: list[dict[str, Any]] = []
    predecessor_readers: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="o011-unit13-r1-anonymous-readback-") as temporary:
        temporary_root = Path(temporary)
        predecessor_readers = verify_predecessor_readers(expected, temporary_root)
        for name in EXPECTED_ORDER:
            if Path(name).name != name:
                fail(f"unsafe public filename: {name}")
            entry = entries[name]
            wanted = {key: expected[name].get(key) for key in ("bytes", "sha256", "md5")}
            if entry.get("size") != wanted["bytes"] or entry_md5(entry) != wanted["md5"]:
                fail(f"public inventory differs before download: {name}")
            destination = temporary_root / name
            actual = download(entry_url(entry), destination)
            if actual != wanted:
                fail(f"anonymously downloaded public bytes differ: {name}")
            if name == SOURCE_ZIP_NAME:
                try:
                    with zipfile.ZipFile(destination, "r") as archive:
                        if archive.testzip() is not None or not archive.infolist():
                            fail("public corrective source ZIP failed CRC/inventory verification")
                except zipfile.BadZipFile:
                    fail("public corrective source ZIP is malformed")
            verified.append({"name": name, **actual})

    receipt = {
        "schema_version": 1,
        "workflow": "o011-independent-zenodo-unit13-source-r1-public-readback-v1",
        "status": "pass",
        "verified_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "authentication_used": False,
        "record_id": published_id,
        "concept_record_id": CONCEPT_ID,
        "predecessor_record_id": PREDECESSOR_ID,
        "doi": expected_doi,
        "concept_doi": CONCEPT_DOI,
        "version": VERSION,
        "coverage": "active_partial_through_unit_13",
        "correction_scope": "resumable_source_package_and_documentation_only",
        "record_status": "published",
        "pdf_default_preview": PDF_NAME,
        "pdf_default_preview_verified": True,
        "rdm_file_order": order,
        "expected_reader_first_order": EXPECTED_ORDER,
        "file_count": len(verified),
        "total_bytes": sum(int(row["bytes"]) for row in verified),
        "all_inventory_md5_matches": True,
        "all_downloaded_bytes_sha256_md5_match": True,
        "reader_bytes_unchanged_from_predecessor": predecessor_readers,
        "public_source_zip_crc_verified": True,
        "temporary_downloads_removed": True,
        "preparation_receipt_sha256": hash_file(preparation_path)["sha256"],
        "publication_receipt_sha256": hash_file(publication_path)["sha256"],
        "files": verified,
    }
    write_once(receipt_path, receipt)
    print(
        json.dumps(
            {
                "status": "pass",
                "record_id": published_id,
                "files": len(verified),
                "bytes": receipt["total_bytes"],
                "receipt": receipt_path.relative_to(root).as_posix(),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
