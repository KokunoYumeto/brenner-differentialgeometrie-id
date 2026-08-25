#!/usr/bin/env python3
"""Publish the verified Unit 10 checkpoint in the existing Zenodo lineage.

This transaction is deliberately fail-closed.  It proves the exact local
seven-file payload and the public Unit 7 predecessor before reading a token,
resumes at most one unambiguous new-version draft, publishes only an exact
metadata/file match, and anonymously reads every published byte back before
writing a sanitized receipt.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import time
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import quote

import httpx


CONCEPT_ID = "22059977"
CONCEPT_DOI = "10.5281/zenodo.22059977"
PREDECESSOR_ID = 22071323
PREDECESSOR_DOI = "10.5281/zenodo.22071323"
VERSION = "2026.08.23-unit10"
PUBLICATION_DATE = "2026-08-23"
MODEL = "OpenAI Codex gpt-5.6-sol, Ultra"
API_MEDIA = "application/vnd.inveniordm.v1+json"
RELEASE_DIR = Path("output/release-unit10")
PDF_NAME = "geometri-diferensial-manifold-mulus-hingga-unit-10-id.pdf"
HTML_ZIP_NAME = "geometri-diferensial-manifold-mulus-brenner-id-unit10-html-20260823.zip"
SOURCE_ZIP_NAME = "geometri-diferensial-manifold-mulus-brenner-id-unit10-source-20260823.zip"
LICENSE_SUPPORT = Path("qa/unit-10/LICENSE_RELEASE_UNIT10.md")
PACKAGE_README_SUPPORT = Path("qa/unit-10/PACKAGE_README.md")
BUILD_RECEIPT = Path("qa/unit-10/build.json")
HTML_RECEIPT = Path("qa/unit-10/HTML_READER_QA.json")
PDF_RECEIPT = Path("qa/unit-10/pdf_structural_qa.json")
EXPECTED_ORDER = [
    PDF_NAME,
    HTML_ZIP_NAME,
    SOURCE_ZIP_NAME,
    "LICENSE.md",
    "RELEASE_NOTES_20260823.md",
    "FILE_MANIFEST.csv",
    "CHECKSUMS.sha256",
]
MAX_PUBLIC_BYTES = 500_000_000
SOURCE_URL = "https://de.wikiversity.org/wiki/Kurs:Differentialgeometrie_(Osnabr%C3%BCck_2023)"
PRIVATE_RE = re.compile(r"(?i)(?:[A-Z]:[\\/]+Users[\\/]|/Users/|/home/|file://|AppData[\\/]|[\\/](?:Downloads|Documents)[\\/]|\\\\[^\\\s]+\\)")
SECRET_RE = re.compile(r"(?i)(?:access[_-]?token\s*[=:]|authorization\s*:\s*bearer|github_pat_[A-Za-z0-9_]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|zenodo[_-]?token\s*[=:])")
TTP_RE = re.compile(r"(?i)(?:\bTTP\b|Translation\s+and\s+Transcription\s+Project)")


def fail(message: str) -> None:
    raise SystemExit(message)


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


def archive_entries(archive: zipfile.ZipFile, label: str) -> dict[str, zipfile.ZipInfo]:
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
        entries[name] = info
    if not entries:
        fail(f"{label} is empty")
    return entries


def unique_archive_suffix(entries: dict[str, zipfile.ZipInfo], suffix: str, label: str) -> str:
    normalized = suffix.replace("\\", "/").lstrip("/")
    matches = [name for name in entries if name == normalized or name.endswith("/" + normalized)]
    if len(matches) != 1:
        fail(f"{label} must contain exactly one {normalized}")
    return matches[0]


def archive_member_identity(archive: zipfile.ZipFile, info: zipfile.ZipInfo) -> dict[str, Any]:
    sha = hashlib.sha256()
    size = 0
    with archive.open(info, "r") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            size += len(block)
            sha.update(block)
    return {"bytes": size, "sha256": sha.hexdigest()}


def receipt_file_binding(receipt: dict[str, Any], path: str, label: str) -> dict[str, Any]:
    inputs = receipt.get("inputs")
    if not isinstance(inputs, list):
        fail(f"{label} input inventory is malformed")
    matches = [item for item in inputs if isinstance(item, dict) and item.get("path") == path]
    if len(matches) != 1 or not isinstance(matches[0].get("bytes"), int) or not isinstance(matches[0].get("sha256"), str):
        fail(f"{label} does not bind exactly one {path}")
    return matches[0]


def verify_release_support(root: Path, local: dict[str, dict[str, Any]]) -> None:
    try:
        approved_license = (root / LICENSE_SUPPORT).read_bytes()
        approved_readme = (root / PACKAGE_README_SUPPORT).read_bytes()
        license_text = approved_license.decode("utf-8")
        readme_text = approved_readme.decode("utf-8")
    except (OSError, UnicodeError):
        fail("unable to read the approved Unit 10 release-support text")
    if local["LICENSE.md"]["path"].read_bytes() != approved_license:
        fail("staged LICENSE.md is not byte-identical to the approved Unit 10 rights text")
    required_license_text = (
        "Creative Commons Attribution-ShareAlike 4.0 International",
        "https://creativecommons.org/licenses/by-sa/4.0/",
        "Media do not inherit a blanket repository license.",
        "authority/brenner_media_rights_manifest.csv",
        "source/unit_media.json",
        MODEL,
    )
    if any(value not in license_text for value in required_license_text) or license_text.count(MODEL) != 1:
        fail("approved Unit 10 rights text lost its CC BY-SA 4.0, per-media-rights, or model disclosure")
    if MODEL not in readme_text or readme_text.count(MODEL) != 1:
        fail("approved Unit 10 package README lacks the exact single model identification")

    pdf_receipt = load_object(root / PDF_RECEIPT, "Unit 10 PDF receipt")
    pdf = pdf_receipt.get("pdf")
    media_closure = pdf_receipt.get("media_closure")
    provenance = ((pdf_receipt.get("structure_and_content") or {}).get("model_provenance") or {})
    if (
        pdf_receipt.get("schema_version") != 1
        or pdf_receipt.get("workflow") != "o011-through-unit10-pdf-structural-accessibility-qa-v1"
        or pdf_receipt.get("passed") is not True
        or not isinstance(pdf, dict)
        or pdf.get("bytes") != local[PDF_NAME]["bytes"]
        or pdf.get("sha256") != local[PDF_NAME]["sha256"]
        or provenance != {"exact_text": MODEL, "occurrences": 1}
        or not isinstance(media_closure, dict)
        or media_closure.get("missing_figure_or_attribution_text") != []
        or media_closure.get("missing_required_uris") != []
        or media_closure.get("unexpected_uris") != []
        or media_closure.get("static_media_count") != media_closure.get("expected_static_media_count")
    ):
        fail("staged PDF is not the exact passing Unit 10 reader with model and per-media-rights closure")

    html_receipt = load_object(root / HTML_RECEIPT, "Unit 10 HTML receipt")
    html_checks = html_receipt.get("checks")
    html_inventory = html_receipt.get("output_inventory")
    if (
        html_receipt.get("schema_version") != 1
        or html_receipt.get("workflow") != "o011-verify-html-v10"
        or html_receipt.get("status") != "pass"
        or not isinstance(html_checks, dict)
        or html_checks.get("local_media_alt_caption_rights_closure") is not True
        or html_checks.get("license_provenance_non_endorsement") is not True
        or html_checks.get("manifest_and_file_hash_closure") is not True
        or not isinstance(html_inventory, list)
    ):
        fail("Unit 10 HTML rights/hash receipt is absent or not passing")
    try:
        with zipfile.ZipFile(local[HTML_ZIP_NAME]["path"], "r") as archive:
            entries = archive_entries(archive, "Unit 10 HTML archive")
            matched: set[str] = set()
            for item in html_inventory:
                if not isinstance(item, dict) or not isinstance(item.get("path"), str):
                    fail("Unit 10 HTML receipt inventory is malformed")
                prefix = "output/html/unit-10/"
                if not item["path"].startswith(prefix):
                    fail("Unit 10 HTML receipt escaped the reader root")
                member = unique_archive_suffix(entries, item["path"][len(prefix):], "Unit 10 HTML archive")
                if member in matched or archive_member_identity(archive, entries[member]) != {"bytes": item.get("bytes"), "sha256": item.get("sha256")}:
                    fail(f"Unit 10 HTML archive member differs from its passing receipt: {item['path']}")
                matched.add(member)
            if matched != set(entries):
                fail("Unit 10 HTML archive contains files outside the passing reader inventory")
    except (OSError, zipfile.BadZipFile, RuntimeError):
        fail("unable to verify the Unit 10 HTML archive")

    build_receipt = load_object(root / BUILD_RECEIPT, "Unit 10 build receipt")
    if build_receipt.get("schema_version") != 1 or build_receipt.get("workflow") != "o011-through-unit10-pdf-build-v1":
        fail("Unit 10 build receipt is not the expected workflow")
    rights_bindings = [
        receipt_file_binding(build_receipt, "authority/brenner_media_rights_manifest.csv", "Unit 10 build receipt"),
        receipt_file_binding(build_receipt, "source/unit_media.json", "Unit 10 build receipt"),
    ]
    try:
        with zipfile.ZipFile(local[SOURCE_ZIP_NAME]["path"], "r") as archive:
            entries = archive_entries(archive, "Unit 10 source archive")
            for binding in rights_bindings:
                member = unique_archive_suffix(entries, str(binding["path"]), "Unit 10 source archive")
                if archive_member_identity(archive, entries[member]) != {"bytes": binding["bytes"], "sha256": binding["sha256"]}:
                    fail(f"Unit 10 source archive changed its rights binding: {binding['path']}")
            license_member = unique_archive_suffix(entries, "LICENSE.md", "Unit 10 source archive")
            readme_member = unique_archive_suffix(entries, "README.md", "Unit 10 source archive")
            if archive.read(entries[license_member]) != approved_license or archive.read(entries[readme_member]) != approved_readme:
                fail("Unit 10 source archive changed its approved license or package README")
    except (OSError, zipfile.BadZipFile, RuntimeError):
        fail("unable to verify the Unit 10 source archive")


def api_json(client: httpx.Client, method: str, url: str, statuses: tuple[int, ...], label: str, **kwargs: object) -> dict[str, Any]:
    try:
        response = client.request(method, url, timeout=300, **kwargs)
    except httpx.HTTPError:
        fail(f"{label} failed before a response")
    if response.status_code not in statuses:
        fail(f"{label} failed: HTTP {response.status_code}")
    try:
        value = response.json()
    except ValueError:
        fail(f"{label} returned malformed JSON")
    if not isinstance(value, dict):
        fail(f"{label} returned a non-object response")
    return value


def api_status(client: httpx.Client, method: str, url: str, statuses: tuple[int, ...], label: str, **kwargs: object) -> None:
    try:
        response = client.request(method, url, timeout=300, **kwargs)
    except httpx.HTTPError:
        fail(f"{label} failed before a response")
    if response.status_code not in statuses:
        fail(f"{label} failed: HTTP {response.status_code}")


def local_payload(root: Path, receipt_path: Path) -> tuple[dict[str, Any], dict[str, dict[str, Any]], list[str]]:
    stage = load_object(receipt_path, "release-preparation receipt")
    if stage.get("schema_version") != 1 or stage.get("workflow") != "o011-prepare-release-unit10-v1" or stage.get("status") != "pass":
        fail("release-preparation receipt is not the passing Unit 10 workflow")
    if stage.get("remote_state_mutated") is not False:
        fail("release-preparation receipt does not prove a local-only operation")
    files = stage.get("files")
    if not isinstance(files, list) or [x.get("filename") for x in files if isinstance(x, dict)] != EXPECTED_ORDER:
        fail("release-preparation receipt does not declare the exact reader-first seven-file order")
    local: dict[str, dict[str, Any]] = {}
    total = 0
    for item in files:
        if not isinstance(item, dict):
            fail("release-preparation file entry is malformed")
        name = item.get("filename")
        if name not in EXPECTED_ORDER or Path(str(name)).name != name:
            fail("release-preparation filename is unsafe")
        path = root / RELEASE_DIR / str(name)
        if not path.is_file():
            fail(f"public file is missing: {name}")
        actual = {"path": path, "bytes": path.stat().st_size, "sha256": digest(path), "md5": digest(path, "md5")}
        if any(actual[key] != item.get(key) for key in ("bytes", "sha256", "md5")):
            fail(f"local public file identity changed: {name}")
        local[str(name)] = actual
        total += int(actual["bytes"])
    if total > MAX_PUBLIC_BYTES or stage.get("total_public_bytes") not in (None, total):
        fail("public payload exceeds the 500 MB cap or its total changed")
    if not isinstance(stage.get("privacy_scan"), dict) or stage["privacy_scan"].get("status") != "pass":
        fail("release-preparation privacy gate is absent or not passing")
    if not isinstance(stage.get("deterministic_archives"), dict) or stage["deterministic_archives"].get("status") != "pass":
        fail("release-preparation archive-reproducibility gate is absent or not passing")
    verify_release_support(root, local)
    return stage, local, EXPECTED_ORDER.copy()


def legacy_and_modern_metadata(path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    payload = load_object(path, "Zenodo metadata")
    if set(payload) != {"metadata"} or not isinstance(payload["metadata"], dict):
        fail("metadata file must contain exactly one metadata object")
    metadata = payload["metadata"]
    required = {"title", "description", "creators", "contributors", "license", "publication_date", "version", "language", "keywords", "related_identifiers"}
    if set(metadata) != required:
        fail("Unit 10 metadata schema is not exact")
    expected_title = "Geometri Diferensial dan Manifold Mulus — Edisi Bahasa Indonesia (Batas Unit 10)"
    if metadata.get("title") != expected_title or metadata.get("version") != VERSION or metadata.get("publication_date") != PUBLICATION_DATE:
        fail("Unit 10 title/version/publication date is not exact")
    description = metadata.get("description")
    if not isinstance(description, str) or description.count(MODEL) != 1 or "active_partial" not in description:
        fail("metadata description lacks the exact model or truthful active_partial disclosure")
    if "Kuliah 1–10" not in description or "Lembar Kerja 1–10" not in description:
        fail("metadata description does not state exact Unit 1--10 coverage")
    if PRIVATE_RE.search(description) or SECRET_RE.search(description):
        fail("metadata description contains a private locator or credential-like text")
    if metadata.get("creators") != [{"name": "Brenner, Holger"}]:
        fail("source creator metadata is not exact")
    contributors = metadata.get("contributors")
    expected_contributors = [{"name": "TTP", "type": "Other"}]
    if contributors != expected_contributors:
        fail("contributors must be exactly one organization anchor named TTP")
    serialized = json.dumps(metadata, ensure_ascii=False)
    if len(TTP_RE.findall(serialized)) != 1:
        fail("TTP must appear exactly once and the expanded organization name must not appear")
    without_contributors = json.dumps({key: value for key, value in metadata.items() if key != "contributors"}, ensure_ascii=False)
    if TTP_RE.search(without_contributors):
        fail("organization naming leaked into title, description, or repeated metadata")
    if metadata.get("license") != "other-open" or metadata.get("language") != "ind":
        fail("mixed-rights license or Indonesian language metadata is not exact")
    keywords = metadata.get("keywords")
    if not isinstance(keywords, list) or not keywords or not all(isinstance(x, str) and x.strip() for x in keywords):
        fail("metadata keywords are malformed")
    related = metadata.get("related_identifiers")
    expected_related = [{"identifier": SOURCE_URL, "relation": "isDerivedFrom", "resource_type": "publication-book", "scheme": "url"}]
    if related != expected_related:
        fail("source relationship metadata is not exact")
    modern = {
        "resource_type": {"id": "publication-book"},
        "title": metadata["title"],
        "publisher": "Zenodo",
        "publication_date": metadata["publication_date"],
        "description": metadata["description"],
        "version": metadata["version"],
        "creators": [{"person_or_org": {"type": "personal", "name": "Brenner, Holger", "given_name": "Holger", "family_name": "Brenner"}}],
        "contributors": [{"person_or_org": {"type": "organizational", "name": "TTP"}, "role": {"id": "other"}}],
        "subjects": [{"subject": value} for value in keywords],
        "languages": [{"id": "ind"}],
        "rights": [{"id": "other-open"}],
        "related_identifiers": [{"identifier": SOURCE_URL, "scheme": "url", "relation_type": {"id": "isderivedfrom"}, "resource_type": {"id": "publication-book"}}],
    }
    return metadata, modern


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
        related.append({
            "identifier": item.get("identifier"),
            "scheme": item.get("scheme"),
            "relation_type": {"id": str(relation_id).lower()},
            "resource_type": {"id": resource_id},
        })
    subjects = metadata.get("subjects")
    if subjects is None:
        subjects = [{"subject": value} for value in metadata.get("keywords", [])]
    return {
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


def public_inventory(record: dict[str, Any]) -> tuple[list[str], dict[str, dict[str, Any]]]:
    files = record.get("files")
    if not isinstance(files, list):
        fail("public Zenodo file inventory is malformed")
    order: list[str] = []
    found: dict[str, dict[str, Any]] = {}
    for item in files:
        if not isinstance(item, dict) or not isinstance(item.get("key"), str):
            fail("public Zenodo file entry is malformed")
        name = item["key"]
        if name in found:
            fail("public Zenodo file inventory contains a duplicate name")
        order.append(name)
        found[name] = item
    return order, found


def draft_files(record: dict[str, Any]) -> dict[str, dict[str, Any]]:
    files = record.get("files")
    entries = files.get("entries") if isinstance(files, dict) else None
    if not isinstance(entries, dict):
        fail("Zenodo draft file representation is malformed")
    return entries


def has_pdf_preview(record: dict[str, Any]) -> bool:
    links = record.get("links") or {}
    thumbnails = links.get("thumbnails") or {}
    preview_links = [value for key, value in links.items() if "preview" in str(key).lower() and isinstance(value, str)]
    preview_links.extend(value for value in thumbnails.values() if isinstance(value, str))
    return any(PDF_NAME in value or quote(PDF_NAME, safe="") in value for value in preview_links)


def exact_public(record: dict[str, Any], modern: dict[str, Any], local: dict[str, dict[str, Any]], order: list[str]) -> bool:
    if str(record.get("conceptrecid")) != CONCEPT_ID or record.get("conceptdoi") != CONCEPT_DOI:
        return False
    if record.get("status") != "published" or projection(record) != projection({"metadata": modern}):
        return False
    try:
        public_order, files = public_inventory(record)
    except SystemExit:
        return False
    return (
        set(files) == set(order)
        and len(files) == len(order)
        and has_pdf_preview(record)
        and all(files[name].get("size") == local[name]["bytes"] and str(files[name].get("checksum", "")).removeprefix("md5:") == local[name]["md5"] for name in order)
    )


def predecessor_ok(record: dict[str, Any]) -> None:
    metadata = record.get("metadata") or {}
    if record.get("id") != PREDECESSOR_ID or str(record.get("conceptrecid")) != CONCEPT_ID or record.get("doi") != PREDECESSOR_DOI or record.get("conceptdoi") != CONCEPT_DOI:
        fail("Zenodo predecessor is not the exact Unit 7 concept record")
    if metadata.get("version") != "2026.08.23-unit07" or "Batas Unit 07" not in str(metadata.get("title")):
        fail("Zenodo predecessor is not the exact published Unit 7 boundary")


def latest(client: httpx.Client, predecessor: dict[str, Any]) -> dict[str, Any]:
    url = ((predecessor.get("links") or {}).get("latest"))
    if not isinstance(url, str) or not url.startswith("https://zenodo.org/api/records/"):
        fail("Zenodo predecessor omitted a safe latest-version link")
    value = api_json(client, "GET", url, (200,), "anonymous latest-version read")
    if str(value.get("conceptrecid")) != CONCEPT_ID:
        fail("latest-version link escaped the expected concept")
    return value


def version_hits(client: httpx.Client, seed_id: int) -> list[dict[str, Any]]:
    # Zenodo caps unauthenticated page size at 25. This concept has far fewer
    # versions, so the maximum public page gives complete bounded coverage.
    value = api_json(client, "GET", f"https://zenodo.org/api/records/{seed_id}/versions?size=25", (200,), "anonymous concept-version listing")
    hits = ((value.get("hits") or {}).get("hits"))
    if not isinstance(hits, list):
        fail("Zenodo concept-version listing is malformed")
    return [item for item in hits if isinstance(item, dict) and str(item.get("conceptrecid")) == CONCEPT_ID]


def ensure_no_duplicate_public_version(client: httpx.Client, seed_id: int, allowed_exact_id: int | None = None) -> None:
    matches = [item for item in version_hits(client, seed_id) if (item.get("metadata") or {}).get("version") == VERSION]
    if not matches:
        return
    if allowed_exact_id is not None and len(matches) == 1 and int(matches[0].get("id", -1)) == allowed_exact_id:
        return
    fail("duplicate or conflicting Unit 10 version already exists in the concept lineage")


def anonymous_readback(client: httpx.Client, record: dict[str, Any], modern: dict[str, Any], local: dict[str, dict[str, Any]], order: list[str]) -> list[dict[str, Any]]:
    if not exact_public(record, modern, local, order):
        fail("public Unit 10 record is not an exact metadata/file match")
    _, files = public_inventory(record)
    results: list[dict[str, Any]] = []
    for name in order:
        url = ((files[name].get("links") or {}).get("self"))
        if not isinstance(url, str) or not url.startswith("https://") or "access_token=" in url.lower():
            fail(f"public file lacks a safe anonymous download URL: {name}")
        sha = hashlib.sha256()
        md5 = hashlib.md5()
        size = 0
        try:
            with client.stream("GET", url, timeout=300) as response:
                if response.status_code != 200:
                    fail(f"anonymous download failed HTTP {response.status_code}: {name}")
                for block in response.iter_bytes(1024 * 1024):
                    if block:
                        size += len(block)
                        sha.update(block)
                        md5.update(block)
        except httpx.HTTPError:
            fail(f"anonymous streamed download failed: {name}")
        if (size, sha.hexdigest(), md5.hexdigest()) != (local[name]["bytes"], local[name]["sha256"], local[name]["md5"]):
            fail(f"anonymous byte mismatch: {name}")
        results.append({"name": name, "bytes": size, "sha256": sha.hexdigest(), "md5": md5.hexdigest(), "matches_local": True, "download_url": url})
    return results


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
        return not PRIVATE_RE.search(value) and not SECRET_RE.search(value) and "access_token=" not in value.lower()
    return True


def write_once(path: Path, value: dict[str, Any]) -> None:
    if path.exists():
        fail("refusing to overwrite the publication receipt")
    if not sanitized(value):
        fail("publication receipt failed the credential/private-locator scan")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def publication_receipt(action: str, record: dict[str, Any], legacy: dict[str, Any], order: list[str], public_order: list[str], files: list[dict[str, Any]], authenticated: bool, draft: dict[str, Any] | None = None) -> dict[str, Any]:
    record_id = int(record["id"])
    result: dict[str, Any] = {
        "schema_version": 1,
        "workflow": "o011-publish-zenodo-unit10-rdm-v1",
        "status": "pass",
        "publication_action": action,
        "authentication_used_for_publication_path": authenticated,
        "authentication_used_for_public_readback": False,
        "verified_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "record_id": record_id,
        "concept_record_id": int(CONCEPT_ID),
        "predecessor_record_id": PREDECESSOR_ID,
        "doi": record.get("doi"),
        "concept_doi": CONCEPT_DOI,
        "record_url": f"https://zenodo.org/records/{record_id}",
        "version": VERSION,
        "coverage": "active_partial_through_unit_10",
        "reader_first_order": order,
        "public_file_order": public_order,
        "pdf_default_preview_verified": True,
        "files": files,
        "metadata_title": legacy["title"],
        "remote_state_mutated": action == "published_new_version",
    }
    if draft is not None:
        result["draft"] = draft
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--token-file", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--release-preparation-receipt", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--draft-id", type=int)
    args = parser.parse_args()

    root = args.root.resolve()
    metadata_path = inside(root, root / args.metadata, "metadata")
    preparation_path = inside(root, root / args.release_preparation_receipt, "release-preparation receipt")
    receipt_path = inside(root, root / args.receipt, "publication receipt")
    if receipt_path.exists():
        fail("refusing to overwrite the publication receipt")
    legacy, modern = legacy_and_modern_metadata(metadata_path)
    _, local, order = local_payload(root, preparation_path)

    with httpx.Client(trust_env=False, follow_redirects=True, timeout=300, headers={"User-Agent": "O011-unit10-public-check/1.0"}) as public:
        predecessor = api_json(public, "GET", f"https://zenodo.org/api/records/{PREDECESSOR_ID}", (200,), "anonymous predecessor read")
        predecessor_ok(predecessor)
        current = latest(public, predecessor)
        if exact_public(current, modern, local, order):
            current_id = int(current["id"])
            ensure_no_duplicate_public_version(public, current_id, current_id)
            files = anonymous_readback(public, current, modern, local, order)
            public_order, _ = public_inventory(current)
            write_once(receipt_path, publication_receipt("recovered_existing_exact_publication", current, legacy, order, public_order, files, False))
            print(json.dumps({"status": "pass", "record_id": current_id, "doi": current.get("doi"), "action": "recovered"}, sort_keys=True))
            return 0
        if int(current.get("id", -1)) != PREDECESSOR_ID:
            fail("a different public version is already latest; refusing a duplicate or branch")
        ensure_no_duplicate_public_version(public, PREDECESSOR_ID)

        token = read_token(args.token_file.resolve())
        headers = {"Authorization": f"Bearer {token}", "Accept": API_MEDIA, "User-Agent": "O011-unit10-publisher/1.0"}
        auth = httpx.Client(trust_env=False, follow_redirects=True, timeout=300, headers=headers)
        del token, headers
        try:
            draft_listing = api_json(auth, "GET", "https://zenodo.org/api/user/records?q=is_published:false&size=100&page=1", (200,), "authenticated draft listing")
            hits = ((draft_listing.get("hits") or {}).get("hits"))
            if not isinstance(hits, list):
                fail("authenticated draft listing is malformed")
            concept_drafts = [
                item for item in hits
                if isinstance(item, dict)
                and item.get("status") == "new_version_draft"
                and str((item.get("parent") or {}).get("id")) == CONCEPT_ID
            ]
            if len(concept_drafts) > 1:
                fail("multiple new-version drafts exist in the concept; refusing ambiguity")
            if args.draft_id is not None:
                matching = [item for item in concept_drafts if int(item.get("id", -1)) == args.draft_id]
                if len(matching) != 1:
                    fail("--draft-id is not exactly one listed new-version draft in this concept")
                concept_drafts = matching
            if concept_drafts:
                draft_id = int(concept_drafts[0]["id"])
                origin = "resumed_exact_listed_new_version_draft"
            else:
                if args.draft_id is not None:
                    fail("requested draft does not exist")
                created = api_json(auth, "POST", f"https://zenodo.org/api/records/{PREDECESSOR_ID}/versions", (201,), "new-version creation")
                if not str(created.get("id", "")).isdigit() or str((created.get("parent") or {}).get("id")) != CONCEPT_ID:
                    fail("new-version response omitted an exact concept-bound draft ID")
                draft_id = int(created["id"])
                origin = "created_new_version_from_exact_unit07_predecessor"

            draft_url = f"https://zenodo.org/api/records/{draft_id}/draft"
            initial = {"metadata": modern, "access": {"record": "public", "files": "public"}, "files": {"enabled": True}}
            api_json(auth, "PUT", draft_url, (200,), "initial Unit 10 metadata update", json=initial, headers={"Content-Type": "application/json", "Accept": API_MEDIA})
            draft = api_json(auth, "GET", draft_url, (200,), "draft read")
            if str((draft.get("parent") or {}).get("id")) != CONCEPT_ID or int(draft.get("id", -1)) != draft_id:
                fail("draft escaped the expected concept")
            entries = draft_files(draft)
            exact_files = (
                len(entries) == len(order)
                and all(name in entries and entries[name].get("size") == local[name]["bytes"] and str(entries[name].get("checksum", "")).removeprefix("md5:") == local[name]["md5"] for name in order)
            )
            uploads: list[dict[str, str]] = []
            base = f"https://zenodo.org/api/records/{draft_id}/draft/files"
            if not exact_files:
                for name in list(entries):
                    api_status(auth, "DELETE", f"{base}/{quote(name, safe='')}", (200, 204), f"delete old draft file {name}")
                api_json(auth, "POST", base, (200, 201), "draft file initialization", json=[{"key": name} for name in order], headers={"Content-Type": "application/json", "Accept": API_MEDIA})
                for name in order:
                    with local[name]["path"].open("rb") as stream:
                        try:
                            response = auth.put(f"{base}/{quote(name, safe='')}/content", content=stream, timeout=300, headers={"Content-Type": "application/octet-stream", "Accept": API_MEDIA})
                        except httpx.HTTPError:
                            fail(f"upload failed before response: {name}")
                    if response.status_code not in (200, 201):
                        fail(f"upload failed HTTP {response.status_code}: {name}")
                    committed = api_json(auth, "POST", f"{base}/{quote(name, safe='')}/commit", (200, 201), f"commit {name}")
                    if committed.get("size") != local[name]["bytes"] or str(committed.get("checksum", "")).removeprefix("md5:") != local[name]["md5"]:
                        fail(f"committed draft file identity mismatch: {name}")
                    uploads.append({"name": name, "status": "uploaded_exact"})

            final = {"metadata": modern, "access": {"record": "public", "files": "public"}, "files": {"enabled": True, "default_preview": PDF_NAME, "order": order}}
            api_json(auth, "PUT", draft_url, (200,), "final Unit 10 metadata update", json=final, headers={"Content-Type": "application/json", "Accept": API_MEDIA})
            verified = api_json(auth, "GET", draft_url, (200,), "final draft verification")
            if projection({"metadata": verified.get("metadata") or {}}) != projection({"metadata": modern}):
                fail("final draft metadata differs from the approved Unit 10 metadata")
            verified_entries = draft_files(verified)
            if len(verified_entries) != len(order) or set(verified_entries) != set(order):
                fail("final draft file set differs from the exact seven-file payload")
            for name in order:
                if verified_entries[name].get("size") != local[name]["bytes"] or str(verified_entries[name].get("checksum", "")).removeprefix("md5:") != local[name]["md5"]:
                    fail(f"final draft file identity mismatch: {name}")
            draft_files_config = verified.get("files") or {}
            if draft_files_config.get("default_preview") != PDF_NAME or draft_files_config.get("order") not in ([], order):
                fail("final draft does not preserve the PDF default preview or an admitted inventory-order representation")

            latest_before = latest(public, predecessor)
            if int(latest_before.get("id", -1)) != PREDECESSOR_ID:
                fail("predecessor ceased to be latest before publication")
            ensure_no_duplicate_public_version(public, PREDECESSOR_ID)
            published = api_json(auth, "POST", f"{draft_url}/actions/publish", (201, 202), "Unit 10 draft publication")
            published_id = int(published.get("id", draft_id)) if str(published.get("id", draft_id)).isdigit() else draft_id
        finally:
            auth.close()

        recovered: dict[str, Any] | None = None
        for _ in range(40):
            candidate = api_json(public, "GET", f"https://zenodo.org/api/records/{published_id}", (200,), "anonymous post-publication read")
            if exact_public(candidate, modern, local, order):
                recovered = candidate
                break
            time.sleep(3)
        if recovered is None:
            fail("published Unit 10 record was not visible as an exact anonymous byte/metadata match")
        ensure_no_duplicate_public_version(public, published_id, published_id)
        files = anonymous_readback(public, recovered, modern, local, order)
        public_order, _ = public_inventory(recovered)
        receipt_value = publication_receipt(
            "published_new_version",
            recovered,
            legacy,
            order,
            public_order,
            files,
            True,
            {"id": draft_id, "origin": origin, "uploads": uploads},
        )
        write_once(receipt_path, receipt_value)
        print(json.dumps({"status": "pass", "record_id": recovered["id"], "doi": recovered.get("doi"), "action": "published"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
