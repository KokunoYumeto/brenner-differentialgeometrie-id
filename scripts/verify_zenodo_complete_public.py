#!/usr/bin/env python3
"""Independently and anonymously verify a public complete O011 Zenodo record."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import urllib.request
from pathlib import Path
from typing import Any


CONCEPT_ID = 22059977
CONCEPT_DOI = "10.5281/zenodo.22059977"
PREDECESSOR_ID = 22146873
VERSION = "2026.08.28-complete"
PUBLICATION_DATE = "2026-08-28"
TITLE = "Geometri Diferensial dan Manifold Mulus — Edisi Bahasa Indonesia"
MODEL = "OpenAI Codex gpt-5.6-sol, Ultra"
SOURCE_URL = "https://de.wikiversity.org/wiki/Kurs:Differentialgeometrie_(Osnabr%C3%BCck_2023)"
PDF_NAME = "geometri-diferensial-manifold-mulus-edisi-lengkap-id.pdf"
EXPECTED_ORDER = [
    PDF_NAME,
    "geometri-diferensial-manifold-mulus-edisi-lengkap-html-20260828.zip",
    "geometri-diferensial-manifold-mulus-edisi-lengkap-source-backend-20260828.zip",
    "LICENSE.md",
    "RELEASE_NOTES_COMPLETE_20260828.md",
    "FILE_MANIFEST.json",
    "SHA256SUMS.txt",
]
PREPARATION = Path("qa/complete/RELEASE_PREPARATION_RECEIPT.json")
PUBLICATION = Path("qa/complete/ZENODO_PUBLICATION_RECEIPT.json")
METADATA_CONTRACT = Path("qa/complete/ZENODO_METADATA_COMPLETE.json")
DEFAULT_RECEIPT = Path("qa/complete/ZENODO_PUBLIC_READBACK_RECEIPT.json")


def fail(message: str) -> None:
    raise RuntimeError(message)


def api_json(url: str) -> dict[str, Any]:
    if not url.startswith("https://zenodo.org/api/records/") or "access_token=" in url.lower():
        fail("unsafe anonymous Zenodo API URL")
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.inveniordm.v1+json",
            "User-Agent": "O011-complete-independent-zenodo-verifier/1.0",
        },
    )
    with urllib.request.urlopen(request, timeout=180) as response:
        value = json.load(response)
    if not isinstance(value, dict):
        fail(f"non-object response from {url}")
    return value


def stream_identity(url: str) -> dict[str, Any]:
    if not url.startswith("https://zenodo.org/") or "access_token=" in url.lower():
        fail("unsafe anonymous Zenodo download URL")
    request = urllib.request.Request(
        url,
        headers={"Accept": "*/*", "User-Agent": "O011-complete-independent-zenodo-verifier/1.0"},
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


def record_id(record: dict[str, Any]) -> int:
    value = record.get("id")
    if not str(value).isdigit():
        fail("public record lacks a numeric ID")
    return int(value)


def concept_id(record: dict[str, Any]) -> str:
    return str(record.get("conceptrecid") or (record.get("parent") or {}).get("id") or "")


def record_doi(record: dict[str, Any]) -> str:
    return str(record.get("doi") or (((record.get("pids") or {}).get("doi") or {}).get("identifier")) or "")


def public_inventory(record: dict[str, Any]) -> tuple[list[str], dict[str, dict[str, Any]], str | None]:
    files = record.get("files")
    if isinstance(files, dict) and isinstance(files.get("entries"), dict):
        entries = files["entries"]
        if not all(isinstance(name, str) and isinstance(value, dict) for name, value in entries.items()):
            fail("public RDM file inventory is malformed")
        configured = files.get("order")
        order = list(configured) if isinstance(configured, list) and configured else list(entries)
        return order, entries, files.get("default_preview")
    if isinstance(files, list):
        entries: dict[str, dict[str, Any]] = {}
        order: list[str] = []
        for item in files:
            if not isinstance(item, dict) or not isinstance(item.get("key"), str) or item["key"] in entries:
                fail("public legacy file inventory is malformed")
            entries[item["key"]] = item
            order.append(item["key"])
        return order, entries, None
    fail("public Zenodo file inventory is absent")


def content_url(entry: dict[str, Any]) -> str:
    links = entry.get("links") or {}
    value = str(links.get("content") or links.get("self") or "")
    if not value.startswith("https://zenodo.org/") or "access_token=" in value.lower():
        fail("public file lacks a safe anonymous content URL")
    return value


def metadata_is_exact(metadata: dict[str, Any], expected: dict[str, Any]) -> None:
    if (
        metadata.get("title") != TITLE
        or metadata.get("title") != expected.get("title")
        or metadata.get("version") != VERSION
        or metadata.get("version") != expected.get("version")
        or metadata.get("publication_date") != PUBLICATION_DATE
        or metadata.get("publication_date") != expected.get("publication_date")
        or metadata.get("publisher") != "Zenodo"
        or (metadata.get("resource_type") or {}).get("id") != "publication-book"
    ):
        fail("public complete-edition title, version, date, publisher, or resource type differs")
    description = metadata.get("description")
    if not isinstance(description, str) or description != expected.get("description") or description.count(MODEL) != 1:
        fail("public complete-edition description lacks exact model provenance")
    required = (
        "Complete reader-first Indonesian adaptation",
        "all 29 lecture and worksheet pairs",
        "6,912 stable-ID records",
        "CC BY-SA 4.0",
        "Component media retain their file-specific rights; no blanket media license is inferred.",
    )
    if any(value not in description for value in required):
        fail("public complete-edition description lacks exact scope or rights")
    creators = metadata.get("creators") or []
    if len(creators) != 1 or not isinstance(creators[0], dict):
        fail("public source creator attribution differs")
    creator = creators[0].get("person_or_org") or creators[0]
    if {
        "type": creator.get("type"),
        "name": creator.get("name"),
        "given_name": creator.get("given_name"),
        "family_name": creator.get("family_name"),
    } != {
        "type": "personal",
        "name": "Brenner, Holger",
        "given_name": "Holger",
        "family_name": "Brenner",
    }:
        fail("public source creator attribution or person type differs")
    contributors = metadata.get("contributors") or []
    if len(contributors) != 1 or not isinstance(contributors[0], dict):
        fail("public complete-edition contributor metadata differs")
    contributor = contributors[0].get("person_or_org") or contributors[0]
    role = contributors[0].get("role") or {}
    if contributor.get("type") != "organizational" or contributor.get("name") != "TTP" or role.get("id") != "other":
        fail("public complete-edition contributor type, name, or role differs")
    without_contributors = json.dumps({key: value for key, value in metadata.items() if key != "contributors"}, ensure_ascii=False)
    serialized_contributors = json.dumps(contributors, ensure_ascii=False)
    if "TTP" in without_contributors or "Translation and Transcription Project" in without_contributors or serialized_contributors.count("TTP") != 1:
        fail("organization label is not confined to exactly one contributor entry")
    keywords = expected.get("keywords")
    if not isinstance(keywords, list) or [item.get("subject") for item in metadata.get("subjects") or [] if isinstance(item, dict)] != keywords:
        fail("public complete-edition subjects differ from the exact metadata contract")
    if [item.get("id") for item in metadata.get("languages") or [] if isinstance(item, dict)] != [expected.get("language")]:
        fail("public complete-edition language differs from the exact metadata contract")
    if [item.get("id") for item in metadata.get("rights") or [] if isinstance(item, dict)] != [expected.get("license")]:
        fail("public complete-edition rights identifier differs from the exact metadata contract")
    related = metadata.get("related_identifiers") or []
    normalized_related = [
        {
            "identifier": item.get("identifier"),
            "scheme": item.get("scheme"),
            "relation": (item.get("relation_type") or {}).get("id"),
            "resource_type": (item.get("resource_type") or {}).get("id"),
        }
        for item in related
        if isinstance(item, dict)
    ]
    if normalized_related != [{
        "identifier": SOURCE_URL,
        "scheme": "url",
        "relation": "isderivedfrom",
        "resource_type": "publication-book",
    }]:
        fail("public complete-edition source relationship differs from the exact metadata contract")


def write_once(path: Path, value: dict[str, Any]) -> None:
    if path.exists():
        fail(f"refusing to overwrite {path}")
    serialized = json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n"
    lowered = serialized.lower()
    if any(marker in lowered for marker in ("access_token", "authorization: bearer", "zenodo_token")):
        fail("public readback receipt failed credential scan")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(serialized, encoding="utf-8", newline="\n")
    os.replace(temporary, path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--record-id", type=int, required=True)
    parser.add_argument("--receipt", type=Path, default=DEFAULT_RECEIPT)
    args = parser.parse_args()
    root = args.root.resolve()
    receipt_path = (root / args.receipt).resolve()
    try:
        receipt_path.relative_to(root)
    except ValueError:
        fail("readback receipt must resolve inside the repository root")
    stage_path = root / PREPARATION
    publication_path = root / PUBLICATION
    metadata_contract_path = root / METADATA_CONTRACT
    stage = json.loads(stage_path.read_text(encoding="utf-8"))
    publication = json.loads(publication_path.read_text(encoding="utf-8"))
    metadata_contract_wrapper = json.loads(metadata_contract_path.read_text(encoding="utf-8"))
    if set(metadata_contract_wrapper) != {"metadata"} or not isinstance(metadata_contract_wrapper["metadata"], dict):
        fail("local complete-edition metadata contract is malformed")
    metadata_contract = metadata_contract_wrapper["metadata"]
    rows = stage.get("files")
    if (
        stage.get("schema_version") != 1
        or stage.get("status") != "pass"
        or stage.get("workflow") != "o011-prepare-release-complete-v1"
        or stage.get("coverage") != "complete_edition"
        or stage.get("version") != VERSION
        or stage.get("remote_state_mutated") is not False
        or stage.get("public_file_order") != EXPECTED_ORDER
        or not isinstance(rows, list)
        or [row.get("filename") for row in rows if isinstance(row, dict)] != EXPECTED_ORDER
    ):
        fail("complete release preparation is not exact")
    if (
        publication.get("schema_version") != 1
        or publication.get("status") != "pass"
        or publication.get("workflow") != "o011-publish-zenodo-complete-v1"
        or publication.get("coverage") != "complete_edition"
        or publication.get("record_id") != args.record_id
        or publication.get("concept_record_id") != CONCEPT_ID
        or publication.get("predecessor_record_id") != PREDECESSOR_ID
        or publication.get("version") != VERSION
        or publication.get("authentication_used_for_public_readback") is not False
        or publication.get("pdf_default_preview_verified") is not True
    ):
        fail("complete publication receipt is not exact")
    expected_doi = f"10.5281/zenodo.{args.record_id}"
    if publication.get("doi") != expected_doi or publication.get("concept_doi") != CONCEPT_DOI:
        fail("complete publication DOI lineage differs")
    expected = {str(row["filename"]): row for row in rows if isinstance(row, dict)}

    record = api_json(f"https://zenodo.org/api/records/{args.record_id}")
    metadata = record.get("metadata") or {}
    if not isinstance(metadata, dict):
        fail("public complete-edition metadata is malformed")
    metadata_is_exact(metadata, metadata_contract)
    order, entries, default_preview = public_inventory(record)
    if (
        record_id(record) != args.record_id
        or concept_id(record) != str(CONCEPT_ID)
        or record_doi(record) != expected_doi
        or record.get("status") != "published"
        or (record.get("access") or {}).get("record") != "public"
        or (record.get("access") or {}).get("files") != "public"
        or set(entries) != set(EXPECTED_ORDER)
        or len(entries) != len(EXPECTED_ORDER)
        or set(order) != set(EXPECTED_ORDER)
        or len(order) != len(EXPECTED_ORDER)
        or default_preview != PDF_NAME
    ):
        fail("public complete record lineage, access, preview, or inventory differs")
    configured_order = (record.get("files") or {}).get("order") if isinstance(record.get("files"), dict) else None
    if isinstance(configured_order, list) and configured_order and configured_order != EXPECTED_ORDER:
        fail("public configured file order is not reader-first")

    versions = api_json(f"https://zenodo.org/api/records/{args.record_id}/versions?size=100&page=1")
    hit_container = versions.get("hits") or {}
    hits = hit_container.get("hits")
    total = hit_container.get("total")
    if (
        not isinstance(hits, list)
        or (isinstance(total, int) and total != len(hits))
        or [str(item.get("id")) for item in hits[:2] if isinstance(item, dict)] != [str(args.record_id), str(PREDECESSOR_ID)]
    ):
        fail("public complete-edition direct predecessor differs")

    verified: list[dict[str, Any]] = []
    for name in EXPECTED_ORDER:
        wanted = expected[name]
        entry = entries[name]
        if entry.get("size") != wanted.get("bytes") or checksum_md5(entry) != wanted.get("md5"):
            fail(f"public complete-edition inventory identity differs: {name}")
        url = content_url(entry)
        actual = stream_identity(url)
        wanted_identity = {key: wanted.get(key) for key in ("bytes", "sha256", "md5")}
        if actual != wanted_identity:
            fail(f"anonymous complete-edition bytes differ: {name}")
        verified.append({"name": name, **actual, "download_url": url})

    latest_url = str((record.get("links") or {}).get("latest") or "")
    latest = api_json(latest_url)
    if record_id(latest) != args.record_id:
        fail("complete edition is not latest in its Zenodo concept")
    receipt = {
        "schema_version": 1,
        "workflow": "o011-independent-zenodo-complete-public-readback-v1",
        "status": "pass",
        "verified_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "authentication_used": False,
        "record_id": args.record_id,
        "concept_record_id": CONCEPT_ID,
        "predecessor_record_id": PREDECESSOR_ID,
        "doi": expected_doi,
        "concept_doi": CONCEPT_DOI,
        "version": VERSION,
        "record_url": f"https://zenodo.org/records/{args.record_id}",
        "record_status": "published",
        "record_access": "public",
        "files_access": "public",
        "pdf_default_preview": PDF_NAME,
        "pdf_default_preview_verified": True,
        "expected_reader_first_order": EXPECTED_ORDER,
        "rdm_file_order": order,
        "files": verified,
        "file_count": len(verified),
        "total_bytes": sum(int(row["bytes"]) for row in verified),
        "all_downloaded_bytes_sha256_md5_match": True,
        "latest_in_concept": True,
        "metadata_contract_verified": True,
        "publication_receipt_sha256": hashlib.sha256(publication_path.read_bytes()).hexdigest(),
        "preparation_receipt_sha256": hashlib.sha256(stage_path.read_bytes()).hexdigest(),
    }
    write_once(receipt_path, receipt)
    print(json.dumps({"status": "pass", "record_id": args.record_id, "doi": expected_doi, "files": len(verified), "bytes": receipt["total_bytes"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
