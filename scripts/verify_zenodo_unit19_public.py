#!/usr/bin/env python3
"""Independently and anonymously verify the public Zenodo Unit 19 record."""

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
PREDECESSOR_ID = 22104426
PREDECESSOR_DOI = "10.5281/zenodo.22104426"
PREDECESSOR_VERSION = "2026.08.26-unit16"
PREDECESSOR_TITLE = "Geometri Diferensial dan Manifold Mulus — Edisi Bahasa Indonesia (Batas Unit 16)"
PREDECESSOR_READBACK_REL = "qa/unit-16/ZENODO_PUBLIC_READBACK_RECEIPT.json"
PREDECESSOR_READBACK_SHA256 = (
    "1c846dd93cf66c60822577b39e5b3ecf5a42a3c1f950ae56d30da0a493ddd063"
)
PREDECESSOR_ORDER = [
    "geometri-diferensial-manifold-mulus-hingga-unit-16-id.pdf",
    "geometri-diferensial-manifold-mulus-unit16-html-20260826.zip",
    "geometri-diferensial-manifold-mulus-unit16-source-20260826.zip",
    "LICENSE.md",
    "RELEASE_NOTES_UNIT16_20260826.md",
    "FILE_MANIFEST.json",
    "SHA256SUMS.txt",
]
VERSION = "2026.08.26-unit19"
PUBLICATION_DATE = "2026-08-26"
TITLE = "Geometri Diferensial dan Manifold Mulus — Edisi Bahasa Indonesia (Batas Unit 19)"
MODEL = "OpenAI Codex gpt-5.6-sol, Ultra"
PDF_NAME = "geometri-diferensial-manifold-mulus-hingga-unit-19-id.pdf"
HTML_ZIP_NAME = "geometri-diferensial-manifold-mulus-unit19-html-20260826.zip"
SOURCE_ZIP_NAME = "geometri-diferensial-manifold-mulus-unit19-source-20260826.zip"
EXPECTED_ORDER = [
    PDF_NAME,
    HTML_ZIP_NAME,
    SOURCE_ZIP_NAME,
    "LICENSE.md",
    "RELEASE_NOTES_UNIT19_20260826.md",
    "FILE_MANIFEST.json",
    "SHA256SUMS.txt",
]
RDM_ACCEPT = "application/vnd.inveniordm.v1+json"
TTP_RE = re.compile(r"(?i)(?:\bTTP\b|Translation\s+and\s+Transcription\s+Project)")


def fail(message: str) -> None:
    raise RuntimeError(message)


def local_profile_name_present(value: str) -> bool:
    if os.name != "nt":
        return False
    profile_name = Path.home().name.strip()
    if len(profile_name) < 4:
        return False
    return re.search(
        r"(?i)(?<![A-Za-z])" + re.escape(profile_name) + r"(?![A-Za-z])",
        value,
    ) is not None


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


def all_boolean_leaves_true(value: Any) -> bool:
    leaves: list[bool] = []

    def walk(item: Any) -> None:
        if isinstance(item, bool):
            leaves.append(item)
        elif isinstance(item, dict):
            for child in item.values():
                walk(child)
        elif isinstance(item, list):
            for child in item:
                walk(child)

    walk(value)
    return bool(leaves) and all(leaves)


def identity_occurs(value: Any, wanted: dict[str, Any]) -> bool:
    if isinstance(value, dict):
        if value.get("bytes") == wanted["bytes"] and value.get("sha256") == wanted["sha256"]:
            return True
        return any(identity_occurs(child, wanted) for child in value.values())
    if isinstance(value, list):
        return any(identity_occurs(child, wanted) for child in value)
    return False


def anonymous_get(url: str, *, accept: str | None = None) -> urllib.response.addinfourl:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != "zenodo.org" or "access_token" in parsed.query.lower():
        fail("refusing a non-public or non-Zenodo URL")
    headers = {"User-Agent": "O011-unit19-independent-readback/1.0"}
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
        or "active_partial" not in description
        or "Kuliah 1–19" not in description
        or "Lembar Kerja 1–19" not in description
        or "CC BY-SA 4.0" not in description
        or "Component media retain their file-specific rights; no blanket media license is inferred." not in description
    ):
        fail("public Unit 19 metadata lost its exact scope, rights, or provenance disclosure")

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
    serialized_metadata = json.dumps(metadata, ensure_ascii=False)
    if len(TTP_RE.findall(serialized_metadata)) != 1:
        fail("TTP does not occur exactly once in public metadata")
    if local_profile_name_present(serialized_metadata):
        fail("local profile name leaked into public Zenodo metadata")

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


def verify_predecessor(root: Path) -> dict[str, Any]:
    receipt_path = root / PREDECESSOR_READBACK_REL
    if (
        not receipt_path.is_file()
        or hash_file(receipt_path)["sha256"] != PREDECESSOR_READBACK_SHA256
    ):
        fail("exact Unit 16 public-readback receipt is absent or changed")
    receipt = load_object(receipt_path, "Unit 16 public-readback receipt")
    receipt_files = receipt.get("files")
    if (
        receipt.get("schema_version") != 1
        or receipt.get("workflow") != "o011-independent-zenodo-unit16-public-readback-v1"
        or receipt.get("status") != "pass"
        or receipt.get("record_id") != PREDECESSOR_ID
        or receipt.get("concept_record_id") != CONCEPT_ID
        or receipt.get("doi") != PREDECESSOR_DOI
        or receipt.get("concept_doi") != CONCEPT_DOI
        or receipt.get("version") != PREDECESSOR_VERSION
        or receipt.get("authentication_used") is not False
        or receipt.get("rdm_file_order") != PREDECESSOR_ORDER
        or not isinstance(receipt_files, list)
        or [item.get("name") for item in receipt_files if isinstance(item, dict)] != PREDECESSOR_ORDER
    ):
        fail("Unit 16 public-readback receipt is not the exact passing predecessor proof")
    with anonymous_get(f"https://zenodo.org/api/records/{PREDECESSOR_ID}", accept=RDM_ACCEPT) as response:
        predecessor = json.load(response)
    if (
        record_id(predecessor) != PREDECESSOR_ID
        or concept_id(predecessor) != str(CONCEPT_ID)
        or record_doi(predecessor) != PREDECESSOR_DOI
        or (predecessor.get("metadata") or {}).get("version") != PREDECESSOR_VERSION
        or (predecessor.get("metadata") or {}).get("title") != PREDECESSOR_TITLE
        or predecessor.get("status") != "published"
        or (predecessor.get("access") or {}).get("record") != "public"
    ):
        fail("public predecessor is not the exact Unit 16 version")
    order, entries, preview = inventory(predecessor)
    if (
        order != PREDECESSOR_ORDER
        or set(entries) != set(PREDECESSOR_ORDER)
        or preview != receipt.get("pdf_default_preview")
    ):
        fail("public predecessor inventory/order/preview differs from the exact Unit 16 proof")
    expected = {str(item["name"]): item for item in receipt_files if isinstance(item, dict)}
    for name in PREDECESSOR_ORDER:
        if (
            entries[name].get("size") != expected[name].get("bytes")
            or entry_md5(entries[name]) != expected[name].get("md5")
        ):
            fail(f"public predecessor file identity differs from Unit 16 proof: {name}")
    return {
        "record_id": PREDECESSOR_ID,
        "doi": PREDECESSOR_DOI,
        "version": PREDECESSOR_VERSION,
        "file_count": len(entries),
        "file_order": order,
        "default_preview": preview,
        "status": "pass",
    }


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
    parser.add_argument(
        "--source-package-integrity-receipt",
        type=Path,
        default=Path("qa/unit-19/SOURCE_PACKAGE_INTEGRITY.json"),
    )
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()

    root = args.root.resolve()
    preparation_path = inside(root, root / args.preparation_receipt, "preparation receipt")
    publication_path = inside(root, root / args.publication_receipt, "publication receipt")
    integrity_path = inside(
        root,
        root / args.source_package_integrity_receipt,
        "source-package integrity receipt",
    )
    receipt_path = inside(root, root / args.receipt, "public-readback receipt")
    if receipt_path.exists():
        fail("refusing to overwrite the independent public-readback receipt")

    preparation = load_object(preparation_path, "release-preparation receipt")
    publication = load_object(publication_path, "publication receipt")
    integrity = load_object(integrity_path, "source-package integrity receipt")
    rows = preparation.get("files")
    if (
        preparation.get("schema_version") != 1
        or preparation.get("workflow") != "o011-prepare-release-unit19-v1"
        or preparation.get("status") != "pass"
        or preparation.get("version") != VERSION
        or preparation.get("coverage") != "active_partial_through_unit_19"
        or preparation.get("remote_state_mutated") is not False
        or not isinstance(rows, list)
        or [row.get("filename") for row in rows if isinstance(row, dict)] != EXPECTED_ORDER
    ):
        fail("release-preparation receipt is not the exact passing Unit 19 stage")
    expected = {str(row["filename"]): row for row in rows if isinstance(row, dict)}
    if set(expected) != set(EXPECTED_ORDER):
        fail("release-preparation file inventory is malformed")
    if preparation.get("public_file_order") != EXPECTED_ORDER:
        fail("release-preparation reader-first order is not exact")
    if any(not isinstance(row.get("bytes"), int) or row["bytes"] < 0 for row in rows):
        fail("release-preparation file sizes are malformed")
    total_public_bytes = sum(row["bytes"] for row in rows)
    privacy = preparation.get("privacy_scan")
    if (
        preparation.get("lineage")
        != {
            "concept_record_id": CONCEPT_ID,
            "predecessor_record_id": PREDECESSOR_ID,
            "new_concept_created": False,
        }
        or preparation.get("public_file_count") != len(EXPECTED_ORDER)
        or preparation.get("public_bytes") != total_public_bytes
        or preparation.get("total_public_bytes") != total_public_bytes
        or total_public_bytes > 500_000_000
        or not isinstance(privacy, dict)
        or privacy.get("status") != "pass"
        or privacy.get("private_locator_hits") != 0
        or privacy.get("credential_like_content_hits") != 0
        or privacy.get("local_profile_name_hits") != 0
    ):
        fail("release-preparation lineage, size, or privacy contract is not exact")
    pdf_identity = {key: expected[PDF_NAME].get(key) for key in ("bytes", "sha256")}
    if not identity_occurs(preparation.get("input_bindings"), pdf_identity):
        fail("release preparation does not bind its PDF to the validated reader gate")

    clean = integrity.get("clean_rebuilds")
    source_identity = {
        key: expected[SOURCE_ZIP_NAME].get(key) for key in ("bytes", "sha256")
    }
    html_identity = {
        key: expected[HTML_ZIP_NAME].get(key) for key in ("bytes", "sha256")
    }
    if (
        integrity.get("schema_version") != 1
        or integrity.get("workflow") != "o011-verify-source-package-unit19-v1"
        or integrity.get("status") != "pass"
        or not identity_occurs(integrity.get("source_zip"), source_identity)
        or not isinstance(clean, list)
        or len(clean) != 2
        or any(not isinstance(item, dict) or item.get("status") != "pass" for item in clean)
        or any(not identity_occurs(item, pdf_identity) for item in clean)
        or any(not identity_occurs(item, html_identity) for item in clean)
        or not all_boolean_leaves_true(integrity.get("cross_cycle_identity"))
        or not all_boolean_leaves_true(integrity.get("checks"))
    ):
        fail("source-package integrity receipt lacks the exact passing two-cycle Unit 19 gate")

    if (
        publication.get("schema_version") != 1
        or publication.get("workflow") != "o011-publish-zenodo-unit19-v1"
        or publication.get("status") != "pass"
        or publication.get("concept_record_id") != CONCEPT_ID
        or publication.get("predecessor_record_id") != PREDECESSOR_ID
        or publication.get("version") != VERSION
        or publication.get("coverage") != "active_partial_through_unit_19"
        or publication.get("reader_content_extended_from_predecessor") is not True
        or publication.get("reader_first_order") != EXPECTED_ORDER
        or not isinstance(publication.get("public_file_order"), list)
        or not publication["public_file_order"]
        or publication["public_file_order"][0] != PDF_NAME
        or len(publication["public_file_order"]) != len(EXPECTED_ORDER)
        or set(publication["public_file_order"]) != set(EXPECTED_ORDER)
        or publication.get("pdf_default_preview_verified") is not True
        or publication.get("authentication_used_for_public_readback") is not False
        or publication.get("publication_action")
        not in ("published_new_version", "recovered_existing_exact_publication")
        or publication.get("release_preparation_receipt_sha256")
        != hash_file(preparation_path)["sha256"]
        or publication.get("source_package_integrity_receipt_sha256")
        != hash_file(integrity_path)["sha256"]
    ):
        fail("publication receipt is not the exact passing Unit 19 transaction")
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
        or not order
        or order[0] != PDF_NAME
        or order != publication.get("public_file_order")
        or set(entries) != set(EXPECTED_ORDER)
        or len(entries) != len(EXPECTED_ORDER)
    ):
        fail("public Unit 19 lineage, access, preview, or inventory is not exact")
    validate_metadata(record)

    verified: list[dict[str, Any]] = []
    predecessor = verify_predecessor(root)
    with tempfile.TemporaryDirectory(prefix="o011-unit19-anonymous-readback-") as temporary:
        temporary_root = Path(temporary)
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
                            fail("public Unit 19 source ZIP failed CRC/inventory verification")
                except zipfile.BadZipFile:
                    fail("public Unit 19 source ZIP is malformed")
            verified.append({"name": name, **actual})

    receipt = {
        "schema_version": 1,
        "workflow": "o011-independent-zenodo-unit19-public-readback-v1",
        "status": "pass",
        "verified_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "authentication_used": False,
        "record_id": published_id,
        "concept_record_id": CONCEPT_ID,
        "predecessor_record_id": PREDECESSOR_ID,
        "doi": expected_doi,
        "concept_doi": CONCEPT_DOI,
        "version": VERSION,
        "coverage": "active_partial_through_unit_19",
        "record_status": "published",
        "pdf_default_preview": PDF_NAME,
        "pdf_default_preview_verified": True,
        "rdm_file_order": order,
        "expected_reader_first_order": EXPECTED_ORDER,
        "file_count": len(verified),
        "total_bytes": sum(int(row["bytes"]) for row in verified),
        "all_inventory_md5_matches": True,
        "all_downloaded_bytes_sha256_md5_match": True,
        "predecessor_boundary": predecessor,
        "public_source_zip_crc_verified": True,
        "temporary_downloads_removed": True,
        "preparation_receipt_sha256": hash_file(preparation_path)["sha256"],
        "publication_receipt_sha256": hash_file(publication_path)["sha256"],
        "source_package_integrity_receipt_sha256": hash_file(integrity_path)["sha256"],
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
