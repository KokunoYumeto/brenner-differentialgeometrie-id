#!/usr/bin/env python3
"""Publish the verified Unit 19 checkpoint to the existing Zenodo concept.

The transaction is fail-closed and lineage-preserving.  Before a credential is
read it proves the exact seven-file local stage, the independent two-cycle
source-package reconstruction receipt, the validated PDF/HTML reader bytes,
and public predecessor record 22104426.  It then resumes at most one
unambiguous concept-bound draft, publishes it, and anonymously hashes every
public byte before writing a sanitized receipt.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import time
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import quote

import httpx


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
SOURCE_URL = "https://de.wikiversity.org/wiki/Kurs:Differentialgeometrie_(Osnabr%C3%BCck_2023)"
API_MEDIA = "application/vnd.inveniordm.v1+json"
RELEASE_DIR = Path("output/release-unit19")
PREPARATION_WORKFLOW = "o011-prepare-release-unit19-v1"
INTEGRITY_WORKFLOW = "o011-verify-source-package-unit19-v1"
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
PUBLIC_CONTROL_FILES = (
    "GOAL_AND_WORKFLOW.md",
    "CURRENT_STATE.md",
    "CURSOR.json",
    "DECISION_LOG.md",
    "AUTHORITY_FREEZE.md",
    "SCOPE_AND_OVERLAP.md",
    "TERMINOLOGY.csv",
    "ADVERSE_LEDGER.csv",
)
MAX_PUBLIC_BYTES = 500_000_000
PRIVATE_RE = re.compile(
    r"(?i)(?:[A-Z]:[\\/]+Users[\\/]|/Users/|/home/|file://|AppData[\\/]|"
    r"[\\/](?:Downloads|Documents)[\\/]|\\\\[^\\\s]+\\)"
)
SECRET_RE = re.compile(
    r"(?i)(?:access[_-]?token\s*[=:]|authorization\s*:\s*bearer|"
    r"github_pat_[A-Za-z0-9_]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|"
    r"zenodo[_-]?token\s*[=:])"
)
TTP_RE = re.compile(r"(?i)(?:\bTTP\b|Translation\s+and\s+Transcription\s+Project)")


def fail(message: str) -> None:
    raise SystemExit(message)


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


def digest(path: Path, algorithm: str = "sha256") -> str:
    value = hashlib.new(algorithm)
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def inside(root: Path, path: Path, label: str) -> Path:
    resolved = path.resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        fail(f"{label} must resolve inside the repository root")
    return resolved


def load_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        fail(f"unable to read valid {label} JSON")
    if not isinstance(value, dict):
        fail(f"{label} must be a JSON object")
    return value


def safe_archive_entries(archive: zipfile.ZipFile, label: str) -> dict[str, zipfile.ZipInfo]:
    entries: dict[str, zipfile.ZipInfo] = {}
    for info in archive.infolist():
        if info.is_dir():
            continue
        name = info.filename.replace("\\", "/")
        parts = PurePosixPath(name).parts
        if not name or name.startswith("/") or ".." in parts or re.match(r"^[A-Za-z]:", name):
            fail(f"{label} contains an unsafe member name")
        if name in entries:
            fail(f"{label} contains a duplicate member name")
        if info.flag_bits & 0x1:
            fail(f"{label} contains an encrypted member")
        entries[name] = info
    if not entries:
        fail(f"{label} is empty")
    return entries


def unique_suffix(entries: dict[str, zipfile.ZipInfo], suffix: str, label: str) -> str:
    wanted = suffix.replace("\\", "/").lstrip("/")
    matches = [name for name in entries if name == wanted or name.endswith("/" + wanted)]
    if len(matches) != 1:
        fail(f"{label} must contain exactly one {wanted}")
    return matches[0]


def archive_identity(archive: zipfile.ZipFile, info: zipfile.ZipInfo) -> dict[str, Any]:
    sha = hashlib.sha256()
    size = 0
    with archive.open(info, "r") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            size += len(block)
            sha.update(block)
    return {"bytes": size, "sha256": sha.hexdigest()}


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


def verify_source_archive(root: Path, local: dict[str, dict[str, Any]]) -> None:
    archive_path = local[SOURCE_ZIP_NAME]["path"]
    try:
        with zipfile.ZipFile(archive_path, "r") as archive:
            if archive.testzip() is not None:
                fail("Unit 19 source archive failed its CRC test")
            entries = safe_archive_entries(archive, "Unit 19 source archive")
            if any(name.endswith("/00_control/PRIVATE_LOCAL_LOCATORS.md") or name == "00_control/PRIVATE_LOCAL_LOCATORS.md" for name in entries):
                fail("Unit 19 source archive contains the private-locator control")

            anchor_suffix = "00_control/GOAL_AND_WORKFLOW.md"
            anchor = unique_suffix(entries, anchor_suffix, "Unit 19 source archive")
            package_prefix = anchor[: -len(anchor_suffix)]

            control_root = root / "00_control"
            controls = [control_root / name for name in PUBLIC_CONTROL_FILES]
            for path in controls:
                if not path.is_file():
                    fail(f"local public durable control is missing: {path.name}")
                member = package_prefix + f"00_control/{path.name}"
                if member not in entries:
                    fail(f"Unit 19 source archive lacks durable control {path.name}")
                if archive_identity(archive, entries[member]) != {
                    "bytes": path.stat().st_size,
                    "sha256": digest(path),
                }:
                    fail(f"Unit 19 source archive changed durable control {path.name}")

            required = (
                "README.md",
                "LICENSE.md",
                "scripts/build_through_unit19.ps1",
                "scripts/export_html_v19.py",
                "scripts/export_backend_v19.py",
                "scripts/verify_through_unit19_pdf.py",
                "scripts/verify_html_v19.py",
                "scripts/verify_backend_v19.py",
                "scripts/verify_source_package_unit19.py",
                "backend/records.jsonl",
                "backend/records.csv",
                "backend/MANIFEST.json",
                "qa/unit-19/build.json",
                "qa/unit-19/pdf_structural_qa.json",
                "qa/unit-19/PDF_VISUAL_QA.json",
                "qa/unit-19/HTML_READER_QA.json",
                "qa/unit-19/backend.json",
            )
            for suffix in required:
                member = package_prefix + suffix
                if member not in entries:
                    fail(f"Unit 19 source archive lacks required dependency {suffix}")

            staged_license = local["LICENSE.md"]["path"].read_bytes()
            archive_license = package_prefix + "LICENSE.md"
            if archive_license not in entries:
                fail("Unit 19 source archive lacks its root LICENSE.md")
            if archive.read(entries[archive_license]) != staged_license:
                fail("source archive and staged LICENSE.md differ")
    except (OSError, RuntimeError, zipfile.BadZipFile):
        fail("unable to verify the Unit 19 source archive")


def verify_integrity_receipt(
    path: Path,
    source: dict[str, Any],
    html: dict[str, Any],
    pdf: dict[str, Any],
) -> dict[str, Any]:
    receipt = load_object(path, "source-package integrity receipt")
    if (
        receipt.get("schema_version") != 1
        or receipt.get("workflow") != INTEGRITY_WORKFLOW
        or receipt.get("status") != "pass"
    ):
        fail("source-package integrity receipt is not the passing Unit 19 workflow")
    if not identity_occurs(receipt.get("source_zip"), source):
        fail("source-package integrity receipt does not bind the staged source ZIP")
    clean = receipt.get("clean_rebuilds")
    if not isinstance(clean, list) or len(clean) != 2:
        fail("source-package integrity receipt must contain exactly two clean rebuilds")
    for item in clean:
        if not isinstance(item, dict) or item.get("status") != "pass":
            fail("a clean source-package rebuild is not passing")
        if not identity_occurs(item, pdf) or not identity_occurs(item, html):
            fail("a clean rebuild does not bind the validated Unit 19 PDF and HTML reader bytes")
    if not all_boolean_leaves_true(receipt.get("cross_cycle_identity")):
        fail("source-package cross-cycle identity gate is absent or not passing")
    if not all_boolean_leaves_true(receipt.get("checks")):
        fail("source-package integrity checks are absent or not all passing")
    return receipt


def local_payload(
    root: Path,
    preparation_path: Path,
    integrity_path: Path,
) -> tuple[dict[str, Any], dict[str, dict[str, Any]], list[str]]:
    stage = load_object(preparation_path, "release-preparation receipt")
    if (
        stage.get("schema_version") != 1
        or stage.get("workflow") != PREPARATION_WORKFLOW
        or stage.get("status") != "pass"
        or stage.get("version") != VERSION
        or stage.get("coverage") != "active_partial_through_unit_19"
        or stage.get("remote_state_mutated") is not False
    ):
        fail("release-preparation receipt is not the passing local-only Unit 19 workflow")
    rows = stage.get("files")
    if not isinstance(rows, list) or [row.get("filename") for row in rows if isinstance(row, dict)] != EXPECTED_ORDER:
        fail("release-preparation receipt does not declare the exact reader-first Unit 19 inventory")
    if (
        stage.get("lineage")
        != {
            "concept_record_id": CONCEPT_ID,
            "predecessor_record_id": PREDECESSOR_ID,
            "new_concept_created": False,
        }
        or stage.get("public_file_count") != len(EXPECTED_ORDER)
        or stage.get("public_file_order") != EXPECTED_ORDER
    ):
        fail("release-preparation receipt has the wrong Unit 19 lineage or reader-first order")

    release = root / RELEASE_DIR
    if not release.is_dir():
        fail("Unit 19 release directory is absent")
    loose = sorted(path.name for path in release.iterdir() if path.is_file())
    if loose != sorted(EXPECTED_ORDER):
        fail("Unit 19 release directory contains a missing or extra loose file")

    local: dict[str, dict[str, Any]] = {}
    total = 0
    for row in rows:
        if not isinstance(row, dict):
            fail("release-preparation file row is malformed")
        name = row.get("filename")
        if name not in EXPECTED_ORDER or Path(str(name)).name != name:
            fail("release-preparation filename is unsafe")
        path = release / str(name)
        if not path.is_file():
            fail(f"staged public file is missing: {name}")
        actual = {
            "path": path,
            "bytes": path.stat().st_size,
            "sha256": digest(path),
            "md5": digest(path, "md5"),
        }
        if any(actual[key] != row.get(key) for key in ("bytes", "sha256", "md5")):
            fail(f"staged public file changed after preparation: {name}")
        local[str(name)] = actual
        total += int(actual["bytes"])
    if (
        total > MAX_PUBLIC_BYTES
        or stage.get("public_bytes") != total
        or stage.get("total_public_bytes") != total
        or stage.get("maximum_public_bytes") != MAX_PUBLIC_BYTES
        or stage.get("under_500000000_bytes") is not True
    ):
        fail("Unit 19 public payload exceeds 500 MB or its bound total changed")
    pdf_identity = {key: local[PDF_NAME][key] for key in ("bytes", "sha256")}
    if not identity_occurs(stage.get("input_bindings"), pdf_identity):
        fail("Unit 19 stage does not bind its PDF to the validated reader gate")
    privacy_scan = stage.get("privacy_scan")
    if (
        not isinstance(privacy_scan, dict)
        or privacy_scan.get("status") != "pass"
        or privacy_scan.get("private_locator_hits") != 0
        or privacy_scan.get("credential_like_content_hits") != 0
        or privacy_scan.get("local_profile_name_hits") != 0
    ):
        fail("Unit 19 stage lacks a passing privacy scan")
    if not isinstance(stage.get("deterministic_archives"), dict) or stage["deterministic_archives"].get("status") != "pass":
        fail("Unit 19 stage lacks passing deterministic-archive evidence")
    verify_source_archive(root, local)
    verify_integrity_receipt(
        integrity_path,
        {key: local[SOURCE_ZIP_NAME][key] for key in ("bytes", "sha256")},
        {key: local[HTML_ZIP_NAME][key] for key in ("bytes", "sha256")},
        pdf_identity,
    )
    return stage, local, EXPECTED_ORDER.copy()


def metadata_pair(path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    payload = load_object(path, "Zenodo metadata")
    if set(payload) != {"metadata"} or not isinstance(payload["metadata"], dict):
        fail("metadata file must contain exactly one metadata object")
    legacy = payload["metadata"]
    required = {
        "title",
        "description",
        "creators",
        "contributors",
        "license",
        "publication_date",
        "version",
        "language",
        "keywords",
        "related_identifiers",
    }
    if set(legacy) != required:
        fail("Unit 19 metadata schema is not exact")
    if (
        legacy.get("title") != TITLE
        or legacy.get("version") != VERSION
        or legacy.get("publication_date") != PUBLICATION_DATE
    ):
        fail("Unit 19 title, version, or publication date is not exact")
    description = legacy.get("description")
    required_description = (
        MODEL,
        "active_partial",
        "Kuliah 1–19",
        "Lembar Kerja 1–19",
        "CC BY-SA 4.0",
        "Component media retain their file-specific rights; no blanket media license is inferred.",
    )
    if not isinstance(description, str) or any(text not in description for text in required_description):
        fail("Unit 19 description lacks exact scope, rights, or provenance disclosure")
    if (
        description.count(MODEL) != 1
        or PRIVATE_RE.search(description)
        or SECRET_RE.search(description)
        or local_profile_name_present(description)
    ):
        fail("Unit 19 description duplicated the model identifier or exposed private material")
    if legacy.get("creators") != [{"name": "Brenner, Holger"}]:
        fail("source creator attribution is not exact")
    if legacy.get("contributors") != [{"name": "TTP", "type": "Other"}]:
        fail("metadata must contain exactly one organizational TTP contributor")
    serialized = json.dumps(legacy, ensure_ascii=False)
    without_contributors = json.dumps(
        {key: value for key, value in legacy.items() if key != "contributors"},
        ensure_ascii=False,
    )
    if len(TTP_RE.findall(serialized)) != 1 or TTP_RE.search(without_contributors):
        fail("TTP must appear exactly once and only in contributor metadata")
    if local_profile_name_present(serialized):
        fail("local profile name leaked into Zenodo metadata")
    if legacy.get("license") != "other-open" or legacy.get("language") != "ind":
        fail("mixed-rights license or Indonesian language metadata is not exact")
    keywords = legacy.get("keywords")
    if not isinstance(keywords, list) or not keywords or not all(isinstance(item, str) and item.strip() for item in keywords):
        fail("metadata keywords are malformed")
    expected_related = [
        {
            "identifier": SOURCE_URL,
            "relation": "isDerivedFrom",
            "resource_type": "publication-book",
            "scheme": "url",
        }
    ]
    if legacy.get("related_identifiers") != expected_related:
        fail("source relationship metadata is not exact")

    modern = {
        "resource_type": {"id": "publication-book"},
        "title": TITLE,
        "publisher": "Zenodo",
        "publication_date": PUBLICATION_DATE,
        "description": description,
        "version": VERSION,
        "creators": [
            {
                "person_or_org": {
                    "type": "personal",
                    "name": "Brenner, Holger",
                    "given_name": "Holger",
                    "family_name": "Brenner",
                }
            }
        ],
        "contributors": [
            {
                "person_or_org": {"type": "organizational", "name": "TTP"},
                "role": {"id": "other"},
            }
        ],
        "subjects": [{"subject": item} for item in keywords],
        "languages": [{"id": "ind"}],
        "rights": [{"id": "other-open"}],
        "related_identifiers": [
            {
                "identifier": SOURCE_URL,
                "scheme": "url",
                "relation_type": {"id": "isderivedfrom"},
                "resource_type": {"id": "publication-book"},
            }
        ],
    }
    return legacy, modern


def projection(record: dict[str, Any]) -> dict[str, Any]:
    metadata = record.get("metadata") or {}

    def people(key: str) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for item in metadata.get(key, []) or []:
            person = item.get("person_or_org") or item
            kind = person.get("type")
            if key == "creators" and kind is None:
                kind = "personal"
            if isinstance(kind, str) and kind.lower() in {"other", "organization", "organizational"}:
                kind = "organizational"
            result.append({"name": person.get("name"), "type": kind})
        return result

    def identifiers(key: str, legacy_key: str) -> list[dict[str, Any]]:
        values = metadata.get(key, metadata.get(legacy_key, []))
        if isinstance(values, (str, dict)):
            values = [values]
        return [{"id": item if isinstance(item, str) else item.get("id")} for item in values or []]

    related: list[dict[str, Any]] = []
    for item in metadata.get("related_identifiers", []) or []:
        relation = item.get("relation_type") or item.get("relation") or {}
        resource = item.get("resource_type") or {}
        relation_id = relation if isinstance(relation, str) else relation.get("id")
        resource_id = resource if isinstance(resource, str) else resource.get("id")
        related.append(
            {
                "identifier": item.get("identifier"),
                "scheme": item.get("scheme"),
                "relation_type": {"id": str(relation_id).lower()},
                "resource_type": {"id": resource_id},
            }
        )
    subjects = metadata.get("subjects")
    if subjects is None:
        subjects = [{"subject": value} for value in metadata.get("keywords", [])]
    return {
        "resource_type": (metadata.get("resource_type") or {}).get("id")
        if isinstance(metadata.get("resource_type"), dict)
        else metadata.get("resource_type"),
        "title": metadata.get("title"),
        "description": metadata.get("description"),
        "publication_date": metadata.get("publication_date"),
        "version": metadata.get("version"),
        "creators": people("creators"),
        "contributors": people("contributors"),
        "subjects": subjects,
        "languages": identifiers("languages", "language"),
        "rights": identifiers("rights", "license"),
        "related_identifiers": related,
    }


def record_id(record: dict[str, Any]) -> int:
    value = record.get("id")
    if not str(value).isdigit():
        fail("Zenodo record lacks a numeric ID")
    return int(value)


def concept_id(record: dict[str, Any]) -> str:
    return str(record.get("conceptrecid") or (record.get("parent") or {}).get("id") or "")


def record_doi(record: dict[str, Any]) -> str:
    return str(record.get("doi") or (((record.get("pids") or {}).get("doi") or {}).get("identifier")) or "")


def public_inventory(record: dict[str, Any]) -> tuple[list[str], dict[str, dict[str, Any]], str | None]:
    files = record.get("files")
    order: list[str] = []
    entries: dict[str, dict[str, Any]] = {}
    default_preview: str | None = None
    if isinstance(files, list):
        for item in files:
            if not isinstance(item, dict) or not isinstance(item.get("key"), str):
                fail("public Zenodo file inventory is malformed")
            order.append(item["key"])
            entries[item["key"]] = item
    elif isinstance(files, dict) and isinstance(files.get("entries"), dict):
        default_preview = files.get("default_preview")
        configured_order = files.get("order")
        entries = files["entries"]
        if not all(isinstance(key, str) and isinstance(value, dict) for key, value in entries.items()):
            fail("public RDM file inventory is malformed")
        order = list(configured_order) if isinstance(configured_order, list) and configured_order else list(entries)
    else:
        fail("public Zenodo file inventory is absent")
    if len(entries) != len(set(entries)):
        fail("public Zenodo file inventory contains a duplicate name")
    return order, entries, default_preview


def draft_files(record: dict[str, Any]) -> dict[str, dict[str, Any]]:
    files = record.get("files")
    entries = files.get("entries") if isinstance(files, dict) else None
    if not isinstance(entries, dict):
        fail("Zenodo draft file representation is malformed")
    return entries


def checksum_md5(entry: dict[str, Any]) -> str:
    return str(entry.get("checksum", "")).removeprefix("md5:")


def content_url(entry: dict[str, Any]) -> str:
    links = entry.get("links") or {}
    value = links.get("content") or links.get("self")
    if not isinstance(value, str) or not value.startswith("https://") or "access_token=" in value.lower():
        fail("public file lacks a safe anonymous download URL")
    return value


def has_pdf_preview(record: dict[str, Any], default_preview: str | None) -> bool:
    if default_preview == PDF_NAME:
        return True
    links = record.get("links") or {}
    thumbnails = links.get("thumbnails") or {}
    candidates = [value for key, value in links.items() if "preview" in str(key).lower() and isinstance(value, str)]
    if isinstance(thumbnails, dict):
        candidates.extend(value for value in thumbnails.values() if isinstance(value, str))
    encoded = quote(PDF_NAME, safe="")
    return any(PDF_NAME in value or encoded in value for value in candidates)


def exact_public(
    record: dict[str, Any],
    modern: dict[str, Any],
    local: dict[str, dict[str, Any]],
    order: list[str],
) -> bool:
    if concept_id(record) != str(CONCEPT_ID) or record.get("status") != "published":
        return False
    if projection(record) != projection({"metadata": modern}):
        return False
    try:
        effective_order, entries, default_preview = public_inventory(record)
    except SystemExit:
        return False
    return (
        bool(effective_order)
        and effective_order[0] == PDF_NAME
        and set(entries) == set(order)
        and len(entries) == len(order)
        and len(effective_order) == len(order)
        and set(effective_order) == set(order)
        and has_pdf_preview(record, default_preview)
        and all(
            entries[name].get("size") == local[name]["bytes"]
            and checksum_md5(entries[name]) == local[name]["md5"]
            for name in order
        )
    )


def api_json(
    client: httpx.Client,
    method: str,
    url: str,
    statuses: tuple[int, ...],
    label: str,
    **kwargs: object,
) -> dict[str, Any]:
    response: httpx.Response | None = None
    for attempt in range(5):
        try:
            response = client.request(method, url, timeout=300, **kwargs)
        except httpx.HTTPError:
            if method.upper() == "GET" and attempt < 4:
                time.sleep(min(2**attempt, 8))
                continue
            fail(f"{label} failed before a response")
        if response.status_code in (502, 503, 504) and method.upper() == "GET" and attempt < 4:
            time.sleep(min(2**attempt, 8))
            continue
        break
    if response is None or response.status_code not in statuses:
        code = "no response" if response is None else f"HTTP {response.status_code}"
        fail(f"{label} failed: {code}")
    try:
        value = response.json()
    except ValueError:
        fail(f"{label} returned malformed JSON")
    if not isinstance(value, dict):
        fail(f"{label} returned a non-object response")
    return value


def api_status(
    client: httpx.Client,
    method: str,
    url: str,
    statuses: tuple[int, ...],
    label: str,
    **kwargs: object,
) -> None:
    try:
        response = client.request(method, url, timeout=300, **kwargs)
    except httpx.HTTPError:
        fail(f"{label} failed before a response")
    if response.status_code not in statuses:
        fail(f"{label} failed: HTTP {response.status_code}")


def predecessor_ok(record: dict[str, Any]) -> None:
    metadata = record.get("metadata") or {}
    if (
        record_id(record) != PREDECESSOR_ID
        or concept_id(record) != str(CONCEPT_ID)
        or record_doi(record) != PREDECESSOR_DOI
        or metadata.get("version") != PREDECESSOR_VERSION
        or metadata.get("title") != PREDECESSOR_TITLE
        or record.get("status") != "published"
        or (record.get("access") or {}).get("record") != "public"
    ):
        fail("Zenodo predecessor is not the exact published Unit 16 boundary")


def latest(client: httpx.Client, seed: dict[str, Any]) -> dict[str, Any]:
    url = (seed.get("links") or {}).get("latest")
    if not isinstance(url, str) or not url.startswith("https://zenodo.org/api/records/"):
        fail("Zenodo predecessor omitted a safe latest-version link")
    value = api_json(client, "GET", url, (200,), "anonymous latest-version read")
    if concept_id(value) != str(CONCEPT_ID):
        fail("latest-version link escaped the expected concept")
    return value


def version_hits(client: httpx.Client, seed_id: int) -> list[dict[str, Any]]:
    value = api_json(
        client,
        "GET",
        f"https://zenodo.org/api/records/{seed_id}/versions?size=25",
        (200,),
        "anonymous concept-version listing",
    )
    hits = ((value.get("hits") or {}).get("hits"))
    if not isinstance(hits, list):
        fail("Zenodo concept-version listing is malformed")
    return [item for item in hits if isinstance(item, dict) and concept_id(item) == str(CONCEPT_ID)]


def ensure_no_duplicate_version(
    client: httpx.Client,
    seed_id: int,
    allowed_exact_id: int | None = None,
) -> None:
    matches = [item for item in version_hits(client, seed_id) if (item.get("metadata") or {}).get("version") == VERSION]
    if not matches:
        return
    if allowed_exact_id is not None and len(matches) == 1 and record_id(matches[0]) == allowed_exact_id:
        return
    fail("duplicate or conflicting Unit 19 version already exists")


def streamed_identity(client: httpx.Client, url: str, label: str) -> dict[str, Any]:
    sha = hashlib.sha256()
    md5 = hashlib.md5()
    size = 0
    try:
        with client.stream(
            "GET",
            url,
            timeout=300,
            headers={"Accept": "*/*"},
        ) as response:
            if response.status_code != 200:
                fail(f"anonymous download failed HTTP {response.status_code}: {label}")
            for block in response.iter_bytes(1024 * 1024):
                if block:
                    size += len(block)
                    sha.update(block)
                    md5.update(block)
    except httpx.HTTPError:
        fail(f"anonymous streamed download failed: {label}")
    return {"bytes": size, "sha256": sha.hexdigest(), "md5": md5.hexdigest()}


def verify_predecessor_boundary(root: Path, predecessor: dict[str, Any]) -> dict[str, Any]:
    """Bind the exact public predecessor without pretending new readers are unchanged."""
    receipt_path = root / PREDECESSOR_READBACK_REL
    if not receipt_path.is_file() or digest(receipt_path) != PREDECESSOR_READBACK_SHA256:
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
    order, entries, default_preview = public_inventory(predecessor)
    if (
        order != PREDECESSOR_ORDER
        or set(entries) != set(PREDECESSOR_ORDER)
        or default_preview != receipt.get("pdf_default_preview")
    ):
        fail("public predecessor inventory/order/preview differs from the exact Unit 16 proof")
    expected = {str(item["name"]): item for item in receipt_files if isinstance(item, dict)}
    for name in PREDECESSOR_ORDER:
        if (
            entries[name].get("size") != expected[name].get("bytes")
            or checksum_md5(entries[name]) != expected[name].get("md5")
        ):
            fail(f"public predecessor file identity differs from Unit 16 proof: {name}")
    return {
        "record_id": record_id(predecessor),
        "doi": record_doi(predecessor),
        "version": (predecessor.get("metadata") or {}).get("version"),
        "file_count": len(entries),
        "file_order": order,
        "default_preview": default_preview,
        "status": "pass",
    }


def anonymous_readback(
    client: httpx.Client,
    record: dict[str, Any],
    modern: dict[str, Any],
    local: dict[str, dict[str, Any]],
    order: list[str],
) -> tuple[list[str], list[dict[str, Any]]]:
    if not exact_public(record, modern, local, order):
        fail("public Unit 19 record is not an exact metadata/file match")
    public_order, entries, _ = public_inventory(record)
    results: list[dict[str, Any]] = []
    for name in order:
        actual = streamed_identity(client, content_url(entries[name]), name)
        wanted = {key: local[name][key] for key in ("bytes", "sha256", "md5")}
        if actual != wanted:
            fail(f"anonymous public bytes differ from the local stage: {name}")
        results.append({"name": name, **actual, "matches_local": True, "download_url": content_url(entries[name])})
    return public_order, results


def read_token(path: Path) -> str:
    try:
        raw = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError):
        fail("unable to read the Zenodo token file")
    candidates: list[str] = []
    for raw_line in raw.splitlines():
        line = raw_line.strip().strip("`")
        if not line or line.startswith("#"):
            continue
        if "=" in line and "token" in line.split("=", 1)[0].lower():
            line = line.split("=", 1)[1].strip().strip("`\"'")
        elif ":" in line and "token" in line.split(":", 1)[0].lower():
            line = line.split(":", 1)[1].strip().strip("`\"'")
        if line and not any(char.isspace() for char in line):
            candidates.append(line)
    candidates = list(dict.fromkeys(candidates))
    if len(candidates) != 1 or len(candidates[0]) < 20:
        fail("Zenodo token file does not contain exactly one usable credential")
    return candidates[0]


def sanitized(value: Any) -> bool:
    if isinstance(value, dict):
        for key, item in value.items():
            if any(term in str(key).lower() for term in ("token", "password", "credential", "authorization")):
                return False
            if not sanitized(item):
                return False
        return True
    if isinstance(value, list):
        return all(sanitized(item) for item in value)
    if isinstance(value, str):
        return (
            not PRIVATE_RE.search(value)
            and not SECRET_RE.search(value)
            and "access_token=" not in value.lower()
            and not local_profile_name_present(value)
        )
    return True


def write_once(path: Path, value: dict[str, Any]) -> None:
    if path.exists():
        fail("refusing to overwrite the Zenodo publication receipt")
    if not sanitized(value):
        fail("publication receipt failed its credential/private-locator scan")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def publication_receipt(
    action: str,
    record: dict[str, Any],
    legacy: dict[str, Any],
    predecessor_proof: dict[str, Any],
    order: list[str],
    public_order: list[str],
    files: list[dict[str, Any]],
    authenticated: bool,
    preparation_path: Path,
    integrity_path: Path,
    draft: dict[str, Any] | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "schema_version": 1,
        "workflow": "o011-publish-zenodo-unit19-v1",
        "status": "pass",
        "publication_action": action,
        "authentication_used_for_publication_path": authenticated,
        "authentication_used_for_public_readback": False,
        "verified_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "record_id": record_id(record),
        "concept_record_id": CONCEPT_ID,
        "predecessor_record_id": PREDECESSOR_ID,
        "doi": record_doi(record),
        "concept_doi": CONCEPT_DOI,
        "record_url": f"https://zenodo.org/records/{record_id(record)}",
        "version": VERSION,
        "coverage": "active_partial_through_unit_19",
        "predecessor_boundary": predecessor_proof,
        "reader_content_extended_from_predecessor": True,
        "reader_first_order": order,
        "public_file_order": public_order,
        "pdf_default_preview_verified": True,
        "files": files,
        "metadata_title": legacy["title"],
        "release_preparation_receipt_sha256": digest(preparation_path),
        "source_package_integrity_receipt_sha256": digest(integrity_path),
        "remote_state_mutated": action == "published_new_version",
    }
    if draft is not None:
        result["draft"] = draft
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--token-file", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--release-preparation-receipt", type=Path, required=True)
    parser.add_argument("--source-package-integrity-receipt", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--draft-id", type=int)
    args = parser.parse_args()

    root = args.root.resolve()
    metadata_path = inside(root, root / args.metadata, "metadata")
    preparation_path = inside(root, root / args.release_preparation_receipt, "release-preparation receipt")
    integrity_path = inside(root, root / args.source_package_integrity_receipt, "source-package integrity receipt")
    receipt_path = inside(root, root / args.receipt, "publication receipt")
    if receipt_path.exists():
        fail("refusing to overwrite the Zenodo publication receipt")

    legacy, modern = metadata_pair(metadata_path)
    _, local, order = local_payload(root, preparation_path, integrity_path)

    # Keep the RDM media type for record JSON so the public representation
    # retains controlled-vocabulary fields such as ``resource_type``. Binary
    # downloads override this header explicitly in ``streamed_identity``.
    public_headers = {"User-Agent": "O011-unit19-public-check/1.0", "Accept": API_MEDIA}
    with httpx.Client(trust_env=False, follow_redirects=True, timeout=300, headers=public_headers) as public:
        predecessor = api_json(
            public,
            "GET",
            f"https://zenodo.org/api/records/{PREDECESSOR_ID}",
            (200,),
            "anonymous predecessor read",
        )
        predecessor_ok(predecessor)
        predecessor_proof = verify_predecessor_boundary(root, predecessor)
        current = latest(public, predecessor)
        if exact_public(current, modern, local, order):
            current_id = record_id(current)
            ensure_no_duplicate_version(public, current_id, current_id)
            public_order, files = anonymous_readback(public, current, modern, local, order)
            receipt = publication_receipt(
                "recovered_existing_exact_publication",
                current,
                legacy,
                predecessor_proof,
                order,
                public_order,
                files,
                False,
                preparation_path,
                integrity_path,
            )
            write_once(receipt_path, receipt)
            print(json.dumps({"status": "pass", "record_id": current_id, "doi": record_doi(current), "action": "recovered"}, sort_keys=True))
            return 0
        if record_id(current) != PREDECESSOR_ID:
            fail("a different public version is already latest; refusing a duplicate or branch")
        ensure_no_duplicate_version(public, PREDECESSOR_ID)

        token = read_token(args.token_file.resolve())
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": API_MEDIA,
            "User-Agent": "O011-unit19-publisher/1.0",
        }
        auth = httpx.Client(trust_env=False, follow_redirects=True, timeout=300, headers=headers)
        del token, headers
        try:
            listing = api_json(
                auth,
                "GET",
                "https://zenodo.org/api/user/records?q=is_published:false&size=100&page=1",
                (200,),
                "authenticated draft listing",
            )
            hits = ((listing.get("hits") or {}).get("hits"))
            if not isinstance(hits, list):
                fail("authenticated draft listing is malformed")
            drafts = [
                item
                for item in hits
                if isinstance(item, dict)
                and item.get("status") == "new_version_draft"
                and concept_id(item) == str(CONCEPT_ID)
            ]
            if len(drafts) > 1:
                fail("multiple new-version drafts exist in the concept; refusing ambiguity")
            if args.draft_id is not None:
                drafts = [item for item in drafts if record_id(item) == args.draft_id]
                if len(drafts) != 1:
                    fail("--draft-id is not exactly one listed concept-bound draft")

            if drafts:
                draft_id = record_id(drafts[0])
                origin = "resumed_exact_listed_new_version_draft"
            else:
                if args.draft_id is not None:
                    fail("requested Zenodo draft does not exist")
                created = api_json(
                    auth,
                    "POST",
                    f"https://zenodo.org/api/records/{PREDECESSOR_ID}/versions",
                    (201,),
                    "Unit 19 new-version creation",
                )
                if concept_id(created) != str(CONCEPT_ID):
                    fail("new-version response escaped the expected concept")
                draft_id = record_id(created)
                origin = "created_from_exact_unit16_predecessor"

            draft_url = f"https://zenodo.org/api/records/{draft_id}/draft"
            unmodified_draft = api_json(auth, "GET", draft_url, (200,), "pre-mutation Unit 19 draft read")
            unmodified_metadata = unmodified_draft.get("metadata") or {}
            unmodified_projection = projection({"metadata": unmodified_metadata})
            predecessor_projection = projection(predecessor)
            target_projection = projection({"metadata": modern})
            inherited_projection_matches = {
                key: value
                for key, value in unmodified_projection.items()
                if key not in {"version", "publication_date"}
            } == {
                key: value
                for key, value in predecessor_projection.items()
                if key not in {"version", "publication_date"}
            }
            # Zenodo assigns the current UTC date when it creates a new-version
            # draft even though every substantive inherited metadata field is
            # still the predecessor's.  Admit only that exact platform-assigned
            # date (or the predecessor's original date), never an arbitrary
            # third date, so a freshly created draft remains safely resumable.
            created_date = str(unmodified_draft.get("created", "")).split("T", 1)[0]
            inherited_date = unmodified_projection.get("publication_date")
            predecessor_date = predecessor_projection.get("publication_date")
            exact_inherited_state = (
                inherited_projection_matches
                and unmodified_projection.get("version") in (None, PREDECESSOR_VERSION)
                and inherited_date in {predecessor_date, created_date}
            )
            exact_target_state = unmodified_projection == target_projection
            if (
                record_id(unmodified_draft) != draft_id
                or concept_id(unmodified_draft) != str(CONCEPT_ID)
                or unmodified_draft.get("status") != "new_version_draft"
                or not (exact_inherited_state or exact_target_state)
            ):
                fail("existing draft is not the exact inherited Unit 16 state or exact Unit 19 target")
            initial = {
                "metadata": modern,
                "access": {"record": "public", "files": "public"},
                "files": {"enabled": True},
            }
            api_json(
                auth,
                "PUT",
                draft_url,
                (200,),
                "initial Unit 19 metadata update",
                json=initial,
                headers={"Content-Type": "application/json", "Accept": API_MEDIA},
            )
            draft = api_json(auth, "GET", draft_url, (200,), "Unit 19 draft read")
            if record_id(draft) != draft_id or concept_id(draft) != str(CONCEPT_ID):
                fail("Unit 19 draft escaped the expected concept")
            entries = draft_files(draft)
            exact_files = len(entries) == len(order) and all(
                name in entries
                and entries[name].get("size") == local[name]["bytes"]
                and checksum_md5(entries[name]) == local[name]["md5"]
                for name in order
            )
            uploads: list[dict[str, str]] = []
            file_base = f"https://zenodo.org/api/records/{draft_id}/draft/files"
            if not exact_files:
                for name in list(entries):
                    api_status(
                        auth,
                        "DELETE",
                        f"{file_base}/{quote(name, safe='')}",
                        (200, 204),
                        f"delete obsolete draft file {name}",
                    )
                api_json(
                    auth,
                    "POST",
                    file_base,
                    (200, 201),
                    "initialize Unit 19 files",
                    json=[{"key": name} for name in order],
                    headers={"Content-Type": "application/json", "Accept": API_MEDIA},
                )
                for name in order:
                    with local[name]["path"].open("rb") as stream:
                        try:
                            response = auth.put(
                                f"{file_base}/{quote(name, safe='')}/content",
                                content=stream,
                                timeout=300,
                                headers={"Content-Type": "application/octet-stream", "Accept": API_MEDIA},
                            )
                        except httpx.HTTPError:
                            fail(f"upload failed before a response: {name}")
                    if response.status_code not in (200, 201):
                        fail(f"upload failed HTTP {response.status_code}: {name}")
                    committed = api_json(
                        auth,
                        "POST",
                        f"{file_base}/{quote(name, safe='')}/commit",
                        (200, 201),
                        f"commit Unit 19 file {name}",
                    )
                    if (
                        committed.get("size") != local[name]["bytes"]
                        or checksum_md5(committed) != local[name]["md5"]
                    ):
                        fail(f"committed draft file identity mismatch: {name}")
                    uploads.append({"name": name, "status": "uploaded_exact"})

            final = {
                "metadata": modern,
                "access": {"record": "public", "files": "public"},
                "files": {"enabled": True, "default_preview": PDF_NAME, "order": order},
            }
            api_json(
                auth,
                "PUT",
                draft_url,
                (200,),
                "final Unit 19 metadata update",
                json=final,
                headers={"Content-Type": "application/json", "Accept": API_MEDIA},
            )
            verified = api_json(auth, "GET", draft_url, (200,), "final Unit 19 draft verification")
            if projection({"metadata": verified.get("metadata") or {}}) != projection({"metadata": modern}):
                fail("final Unit 19 draft metadata differs from the approved metadata")
            verified_entries = draft_files(verified)
            if set(verified_entries) != set(order) or len(verified_entries) != len(order):
                fail("final Unit 19 draft file set differs from the exact staged inventory")
            for name in order:
                if (
                    verified_entries[name].get("size") != local[name]["bytes"]
                    or checksum_md5(verified_entries[name]) != local[name]["md5"]
                ):
                    fail(f"final Unit 19 draft file identity mismatch: {name}")
            files_config = verified.get("files") or {}
            configured_order = files_config.get("order")
            effective_order = (
                list(configured_order)
                if isinstance(configured_order, list) and configured_order
                else list(verified_entries)
            )
            if (
                files_config.get("default_preview") != PDF_NAME
                or not effective_order
                or effective_order[0] != PDF_NAME
                or len(effective_order) != len(order)
                or set(effective_order) != set(order)
            ):
                fail("final Unit 19 draft lost reader-first preview/order semantics")

            latest_before = latest(public, predecessor)
            if record_id(latest_before) != PREDECESSOR_ID:
                fail("predecessor ceased to be latest before Unit 19 publication")
            ensure_no_duplicate_version(public, PREDECESSOR_ID)
            published = api_json(
                auth,
                "POST",
                f"{draft_url}/actions/publish",
                (201, 202),
                "Unit 19 publication",
            )
            published_id = record_id(published) if str(published.get("id", "")).isdigit() else draft_id
        finally:
            auth.close()

        recovered: dict[str, Any] | None = None
        for _ in range(40):
            candidate = api_json(
                public,
                "GET",
                f"https://zenodo.org/api/records/{published_id}",
                (200,),
                "anonymous post-publication read",
            )
            if exact_public(candidate, modern, local, order):
                recovered = candidate
                break
            time.sleep(3)
        if recovered is None:
            fail("Unit 19 publication did not become an exact anonymous metadata/byte match")
        ensure_no_duplicate_version(public, published_id, published_id)
        public_order, files = anonymous_readback(public, recovered, modern, local, order)
        receipt = publication_receipt(
            "published_new_version",
            recovered,
            legacy,
            predecessor_proof,
            order,
            public_order,
            files,
            True,
            preparation_path,
            integrity_path,
            {"id": draft_id, "origin": origin, "uploads": uploads},
        )
        write_once(receipt_path, receipt)
        print(
            json.dumps(
                {"status": "pass", "record_id": record_id(recovered), "doi": record_doi(recovered), "action": "published"},
                sort_keys=True,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
