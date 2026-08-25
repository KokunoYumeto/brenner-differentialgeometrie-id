#!/usr/bin/env python3
"""Anonymously verify the exact reader-first Unit 6 Zenodo release."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlparse

import requests


CONCEPT_ID = "22059977"
CONCEPT_DOI = "10.5281/zenodo.22059977"
CURRENT_RECORD = 22060387
MODEL_IDENTIFICATION = "OpenAI Codex gpt-5.6-sol, Ultra"
LANE_CAP_BYTES = 500_000_000
STAGING_WORKFLOW = "o011-prepare-release-unit06-v1"
SOURCE_WORKFLOW = "o011-stage-zenodo-unit06-v1"
VERIFY_WORKFLOW = "o011-verify-zenodo-public-unit06-v1"
EXPECTED_TITLE = (
    "Geometri Diferensial dan Manifold Mulus — Edisi Bahasa Indonesia "
    "(Batas Unit 06)"
)
EXPECTED_DESCRIPTION_SHA256 = (
    "889e8afdd0cc9a00b7bd8fd3a8df9c45c1521dada54595e3ddcc5b09b7d69f78"
)
EXPECTED_CREATORS = [{"name": "Brenner, Holger"}]
EXPECTED_CONTRIBUTORS = [
    {"name": "TTP", "type": "Other"},
    {"name": "Codex (OpenAI), at the user's direction", "type": "Other"},
]
EXPECTED_KEYWORDS = [
    "geometri diferensial",
    "manifold mulus",
    "differential geometry",
    "smooth manifolds",
    "transpor paralel",
    "Bahasa Indonesia",
    "buku teks terbuka",
    "open textbook",
    "pendidikan matematika",
    "Wikiversity",
    "Holger Brenner",
]
EXPECTED_SOURCE_RELATION = [
    {
        "identifier": (
            "https://de.wikiversity.org/wiki/"
            "Kurs:Differentialgeometrie_(Osnabr%C3%BCck_2023)"
        ),
        "relation": "isDerivedFrom",
        "resource_type": "publication-book",
        "scheme": "url",
    }
]
EXPECTED_METADATA_KEYS = {
    "title", "upload_type", "publication_type", "description", "creators",
    "contributors", "license", "access_right", "publication_date", "version",
    "language", "keywords", "related_identifiers",
}
FILES = (
    ("output/pdf/geometri-diferensial-manifold-mulus-hingga-unit-06-id.pdf",
     "geometri-diferensial-manifold-mulus-hingga-unit-06-id.pdf"),
    ("output/zenodo/geometri-diferensial-manifold-mulus-brenner-id-unit06-20260822.zip",
     "geometri-diferensial-manifold-mulus-brenner-id-unit06-20260822.zip"),
    ("qa/unit-06/LICENSE_RELEASE_UNIT06.md", "LICENSE.md"),
    ("qa/unit-06/RELEASE_NOTES_20260822.md", "RELEASE_NOTES_20260822.md"),
    ("output/release-unit06/FILE_MANIFEST.csv", "FILE_MANIFEST.csv"),
    ("output/release-unit06/CHECKSUMS.sha256", "CHECKSUMS.sha256"),
)
PUBLIC_NAMES = tuple(name for _, name in FILES)
PRIMARY_READER = PUBLIC_NAMES[0]
PRIMARY_ROLE = "primary reader; cumulative partial edition through Lecture/Worksheet 6"
STAGING_KEYS = {
    "coverage", "files", "lane_cap_bytes", "public_file_count",
    "public_payload_bytes", "reader_first", "remote_state_mutated",
    "schema_version", "source_package", "source_package_privacy",
    "source_package_receipt", "status", "substantive_payload_bytes", "workflow",
}
STAGING_FILE_KEYS = {
    "bytes", "filename", "md5", "rights_scope", "role", "sha256",
}
SOURCE_BINDING_KEYS = {"path", "bytes", "sha256", "workflow"}
SOURCE_PRIVACY_KEYS = {
    "all_files_raw_bytes_scanned", "credential_like_content_hits",
    "generic_privacy_scanner_pattern_literals",
    "historical_publication_receipts_excluded",
    "personal_contributor_wording_hits", "private_locator_hits", "text_files_scanned",
}
HEX32 = re.compile(r"[0-9a-f]{32}\Z")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")


def fail(message: str) -> None:
    raise SystemExit(message)


def plain_int(value: object) -> bool:
    return type(value) is int


def digest(path: Path, algorithm: str) -> str:
    value = hashlib.new(algorithm)
    try:
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                value.update(block)
    except OSError:
        fail(f"unable to read required local file: {path.name}")
    return value.hexdigest()


def identity(path: Path) -> tuple[int, str, str]:
    if not path.is_file():
        fail(f"required local release file is missing: {path.name}")
    return path.stat().st_size, digest(path, "sha256"), digest(path, "md5")


def read_json(path: Path, label: str) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        fail(f"{label} is missing or invalid UTF-8 JSON")
    if not isinstance(value, dict):
        fail(f"{label} must be a JSON object")
    return value


def project_people(value: object, keys: tuple[str, ...]) -> list[dict] | None:
    if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
        return None
    return [{key: item[key] for key in keys if item.get(key)} for item in value]


def project_related(value: object) -> list[dict] | None:
    if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
        return None
    keys = ("identifier", "relation", "resource_type", "scheme")
    return [{key: item[key] for key in keys if item.get(key)} for item in value]


def metadata_projection(value: object, *, public: bool) -> dict | None:
    if not isinstance(value, dict):
        return None
    license_value = value.get("license")
    if public:
        if not isinstance(license_value, dict):
            return None
        license_value = license_value.get("id")
    fields = (
        "title", "description", "access_right", "publication_date", "version",
        "language", "keywords",
    )
    result = {key: value.get(key) for key in fields}
    if not public:
        result["upload_type"] = value.get("upload_type")
        result["publication_type"] = value.get("publication_type")
    result["license"] = license_value
    result["creators"] = project_people(
        value.get("creators"), ("name", "affiliation", "orcid", "gnd")
    )
    result["contributors"] = project_people(
        value.get("contributors"), ("name", "type", "affiliation", "orcid", "gnd")
    )
    result["related_identifiers"] = project_related(value.get("related_identifiers"))
    return result


def validate_metadata_payload(payload: dict) -> dict:
    if set(payload) != {"metadata"} or not isinstance(payload.get("metadata"), dict):
        fail("metadata payload must contain exactly one metadata object")
    metadata = payload["metadata"]
    if set(metadata) != EXPECTED_METADATA_KEYS:
        fail("metadata payload schema is not the frozen Unit 6 schema")
    description = metadata.get("description")
    if not isinstance(description, str) or hashlib.sha256(
        description.encode("utf-8")
    ).hexdigest() != EXPECTED_DESCRIPTION_SHA256:
        fail("description is not the frozen Unit 6 description")
    scalars = {
        "title": EXPECTED_TITLE, "upload_type": "publication",
        "publication_type": "book", "access_right": "open",
        "license": "other-open", "publication_date": "2026-08-22",
        "version": "2026.08.22-unit06", "language": "ind",
    }
    if any(metadata.get(key) != value for key, value in scalars.items()):
        fail("metadata scalar fields are not the frozen Unit 6 values")
    if metadata.get("creators") != EXPECTED_CREATORS:
        fail("creator metadata is not exact")
    if metadata.get("contributors") != EXPECTED_CONTRIBUTORS:
        fail("contributor metadata is not exact")
    if metadata.get("keywords") != EXPECTED_KEYWORDS:
        fail("keyword metadata is not exact")
    if metadata.get("related_identifiers") != EXPECTED_SOURCE_RELATION:
        fail("source related_identifier is not exact")
    if sum(item.get("name") == "TTP" for item in metadata["contributors"]) != 1:
        fail("TTP must occur exactly once as a contributor")
    non_contributors = dict(metadata)
    del non_contributors["contributors"]
    text = json.dumps(non_contributors, ensure_ascii=False, sort_keys=True)
    if "TTP" in text or "Translation and Transcription Project" in text:
        fail("TTP may occur only in contributors")
    for phrase in (
        MODEL_IDENTIFICATION, "active_partial", "107 latihan", "14 solusi",
        "11 gambar", "1.173 rekaman", "Paket reader-first", "PDF pembaca",
    ):
        if phrase not in description:
            fail(f"description omits required disclosure: {phrase}")
    return metadata


def expected_public_projection(metadata: dict) -> dict:
    value = metadata_projection(metadata, public=False)
    assert value is not None
    value.pop("upload_type")
    value.pop("publication_type")
    return value


def validate_remote_metadata(value: object, expected: dict, *, public: bool, label: str) -> None:
    target = expected_public_projection(expected) if public else metadata_projection(
        expected, public=False
    )
    if metadata_projection(value, public=public) != target:
        fail(f"{label} metadata is not the exact Unit 6 metadata")
    assert isinstance(value, dict)
    contributors = project_people(
        value.get("contributors"), ("name", "type", "affiliation", "orcid", "gnd")
    )
    if contributors != EXPECTED_CONTRIBUTORS or sum(
        item.get("name") == "TTP" for item in contributors or []
    ) != 1:
        fail(f"{label} does not contain the exact contributors/TTP boundary")
    if project_related(value.get("related_identifiers")) != EXPECTED_SOURCE_RELATION:
        fail(f"{label} does not contain the exact source relationship")
    title_description = str(value.get("title") or "") + str(value.get("description") or "")
    if "TTP" in title_description or "Translation and Transcription Project" in title_description:
        fail(f"{label} leaks TTP outside contributors")


def safe_bound_path(root: Path, relative: object) -> Path:
    if not isinstance(relative, str):
        fail("source-package receipt binding path is malformed")
    candidate = Path(relative)
    if candidate.is_absolute() or ".." in candidate.parts:
        fail("source-package receipt binding escapes the project root")
    resolved = (root / candidate).resolve()
    if resolved != root and root not in resolved.parents:
        fail("source-package receipt binding escapes the project root")
    return resolved


def validate_privacy(value: object, label: str) -> dict:
    if not isinstance(value, dict) or set(value) != SOURCE_PRIVACY_KEYS:
        fail(f"{label} schema mismatch")
    for key in (
        "all_files_raw_bytes_scanned", "generic_privacy_scanner_pattern_literals",
        "text_files_scanned",
    ):
        if not plain_int(value.get(key)) or value[key] < 0:
            fail(f"{label} count is malformed: {key}")
    if (
        value.get("private_locator_hits") != 0
        or value.get("personal_contributor_wording_hits") != 0
        or value.get("credential_like_content_hits") != 0
        or value.get("historical_publication_receipts_excluded") is not True
    ):
        fail(f"{label} is not a zero-hit passing privacy boundary")
    return value


def validate_boundary(root: Path, metadata_path: Path, staging_path: Path) -> tuple[dict, dict, dict]:
    expected = validate_metadata_payload(read_json(metadata_path, "Zenodo metadata payload"))
    staging = read_json(staging_path, "release staging receipt")
    if set(staging) != STAGING_KEYS:
        fail("release staging receipt top-level schema mismatch")
    files = staging.get("files")
    if not isinstance(files, list) or len(files) != len(FILES):
        fail("release staging receipt must contain exactly six files")
    if (
        staging.get("schema_version") != 1 or not plain_int(staging.get("schema_version"))
        or staging.get("workflow") != STAGING_WORKFLOW or staging.get("status") != "pass"
        or staging.get("coverage") != "active_partial_through_unit_06"
        or staging.get("reader_first") is not True
        or staging.get("remote_state_mutated") is not False
        or staging.get("public_file_count") != 6
        or staging.get("lane_cap_bytes") != LANE_CAP_BYTES
        or not all(plain_int(staging.get(key)) for key in (
            "public_file_count", "lane_cap_bytes", "public_payload_bytes",
            "substantive_payload_bytes",
        ))
    ):
        fail("release staging workflow/reader-first/cap boundary mismatch")
    if [item.get("filename") if isinstance(item, dict) else None for item in files] != list(PUBLIC_NAMES):
        fail("release staging file list is not in the intended reader-first order")

    local: dict[str, dict] = {}
    staged_by_name: dict[str, dict] = {}
    for index, ((relative, name), item) in enumerate(zip(FILES, files)):
        if not isinstance(item, dict) or set(item) != STAGING_FILE_KEYS:
            fail(f"staging file-entry schema mismatch: {name}")
        if (
            item.get("filename") != name or not plain_int(item.get("bytes"))
            or item["bytes"] < 0 or not isinstance(item.get("sha256"), str)
            or not HEX64.fullmatch(item["sha256"]) or not isinstance(item.get("md5"), str)
            or not HEX32.fullmatch(item["md5"]) or not isinstance(item.get("role"), str)
            or not isinstance(item.get("rights_scope"), str)
        ):
            fail(f"staging file entry is malformed: {name}")
        if index == 0 and item["role"] != PRIMARY_ROLE:
            fail("staging receipt does not identify the primary reader PDF")
        path = (root / relative).resolve()
        size, sha256, md5 = identity(path)
        if (item["bytes"], item["sha256"], item["md5"]) != (size, sha256, md5):
            fail(f"local/staging identity mismatch: {name}")
        local[name] = {"path": path, "bytes": size, "sha256": sha256, "md5": md5}
        staged_by_name[name] = item
    total = sum(item["bytes"] for item in local.values())
    substantive = sum(local[name]["bytes"] for name in PUBLIC_NAMES[:4])
    if total != staging["public_payload_bytes"] or substantive != staging[
        "substantive_payload_bytes"
    ] or total >= LANE_CAP_BYTES:
        fail("recomputed payload totals or 500 MB cap mismatch")

    source_privacy = validate_privacy(staging.get("source_package_privacy"), "embedded privacy proof")
    binding = staging.get("source_package_receipt")
    if not isinstance(binding, dict) or set(binding) != SOURCE_BINDING_KEYS:
        fail("source-package receipt binding schema mismatch")
    if (
        binding.get("workflow") != SOURCE_WORKFLOW or not plain_int(binding.get("bytes"))
        or not isinstance(binding.get("sha256"), str) or not HEX64.fullmatch(binding["sha256"])
    ):
        fail("source-package receipt binding is malformed")
    bound_path = safe_bound_path(root, binding.get("path"))
    bound_size, bound_sha256, _ = identity(bound_path)
    if (bound_size, bound_sha256) != (binding["bytes"], binding["sha256"]):
        fail("source-package receipt byte binding mismatch")
    source = read_json(bound_path, "bound source-package receipt")
    source_package = source.get("package")
    if (
        source.get("schema_version") != 1 or source.get("workflow") != SOURCE_WORKFLOW
        or source.get("status") != "pass" or source.get("remote_state_mutated") is not False
        or source_package != staging.get("source_package")
        or source.get("privacy_scan") != source_privacy
    ):
        fail("bound source-package workflow/package/privacy proof mismatch")
    validate_privacy(source.get("privacy_scan"), "bound source-package privacy proof")
    zip_item = local[PUBLIC_NAMES[1]]
    if (
        not isinstance(source_package, dict)
        or source_package.get("archive_path") != FILES[1][0]
        or source_package.get("archive_bytes") != zip_item["bytes"]
        or source_package.get("archive_sha256") != zip_item["sha256"]
        or source_package.get("crc_and_identity_verified") is not True
        or source_package.get("reproducible_second_serialization") is not True
        or source_package.get("timestamps_normalized") is not True
    ):
        fail("source-package proof is not bound to the exact ZIP")

    manifest = local["FILE_MANIFEST.csv"]["path"]
    try:
        with manifest.open("r", encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream)
            rows = list(reader)
            columns = reader.fieldnames
    except (OSError, UnicodeError, csv.Error):
        fail("FILE_MANIFEST.csv cannot be parsed")
    expected_columns = ["filename", "role", "bytes", "sha256", "md5", "rights_scope"]
    if columns != expected_columns or [row.get("filename") for row in rows] != list(PUBLIC_NAMES[:4]):
        fail("FILE_MANIFEST.csv is not the intended reader-first manifest")
    for row in rows:
        name = row["filename"]
        staged = staged_by_name[name]
        if (
            row.get("role") != staged["role"] or row.get("rights_scope") != staged["rights_scope"]
            or row.get("bytes") != str(local[name]["bytes"])
            or row.get("sha256") != local[name]["sha256"] or row.get("md5") != local[name]["md5"]
        ):
            fail(f"FILE_MANIFEST.csv mismatch: {name}")
    if rows[0].get("filename") != PRIMARY_READER or rows[0].get("role") != PRIMARY_ROLE:
        fail("FILE_MANIFEST.csv does not prove the primary reader PDF")
    try:
        lines = local["CHECKSUMS.sha256"]["path"].read_text(encoding="ascii").splitlines()
    except (OSError, UnicodeError):
        fail("CHECKSUMS.sha256 cannot be parsed")
    parsed = []
    for line in lines:
        parts = line.split("  ", 1)
        if len(parts) != 2 or not HEX64.fullmatch(parts[0]):
            fail("CHECKSUMS.sha256 contains a malformed row")
        parsed.append((parts[1], parts[0]))
    if parsed != [(name, local[name]["sha256"]) for name in PUBLIC_NAMES[:5]]:
        fail("CHECKSUMS.sha256 is not the intended checksum surface")
    evidence = {
        "intended_order": list(PUBLIC_NAMES), "primary_reader": PRIMARY_READER,
        "primary_reader_role": PRIMARY_ROLE, "primary_reader_manifest_row": 1,
        "description_declares_reader_first_pdf": True,
    }
    return expected, local, evidence


def checksum(value: object) -> str:
    result = str(value or "")
    return result[4:] if result.startswith("md5:") else result


def file_view(item: object) -> tuple[str, int, str]:
    if not isinstance(item, dict):
        fail("Zenodo returned a non-object file entry")
    name = item.get("key") or item.get("filename") or item.get("name")
    size = item.get("size") if item.get("size") is not None else item.get("filesize")
    md5 = checksum(item.get("checksum"))
    if not isinstance(name, str) or not name or not plain_int(size) or size < 0 or not HEX32.fullmatch(md5):
        fail("Zenodo returned a malformed file identity")
    return name, size, md5


def inventory(value: object) -> tuple[list[str], dict[str, tuple[str, int, str]], dict[str, dict]]:
    if not isinstance(value, list):
        fail("Zenodo file inventory is not a list")
    order, by_name, raw = [], {}, {}
    for item in value:
        view = file_view(item)
        if view[0] in by_name:
            fail(f"Zenodo file inventory contains duplicate name: {view[0]}")
        order.append(view[0]); by_name[view[0]] = view; raw[view[0]] = item
    return order, by_name, raw


def zenodo_url(value: object, prefix: str) -> str:
    if not isinstance(value, str):
        fail("Zenodo response omitted a required URL")
    parsed = urlparse(value)
    if (
        parsed.scheme != "https" or parsed.hostname != "zenodo.org"
        or parsed.username is not None or parsed.password is not None
        or parsed.port not in (None, 443) or not parsed.path.startswith(prefix)
    ):
        fail("Zenodo response supplied an unsafe URL")
    return value


def get_json(session: requests.Session, url: str, label: str) -> dict:
    zenodo_url(url, "/api/records/")
    try:
        response = session.get(url, timeout=60)
    except requests.RequestException:
        fail(f"{label} failed before a response was received")
    if response.status_code != 200:
        fail(f"{label} failed: HTTP {response.status_code}")
    try:
        value = response.json()
    except (ValueError, json.JSONDecodeError):
        fail(f"{label} returned malformed JSON")
    if not isinstance(value, dict):
        fail(f"{label} returned a non-object JSON body")
    return value


def latest_public_record(session: requests.Session, seed: dict) -> tuple[dict, str]:
    links = seed.get("links")
    if not isinstance(links, dict) or not links.get("latest"):
        fail("public record omitted the authoritative latest-version link")
    url = zenodo_url(links["latest"], "/api/records/")
    latest = get_json(session, url, "anonymous latest-version proof")
    if str(latest.get("conceptrecid")) != CONCEPT_ID or not plain_int(latest.get("id")):
        fail("latest-version link escaped the expected concept")
    return latest, url


def record_matches(record: dict, expected: dict, local: dict) -> bool:
    try:
        record_id = record.get("id")
        if (
            not plain_int(record_id) or record_id <= 0
            or str(record.get("conceptrecid")) != CONCEPT_ID
            or record.get("doi") != f"10.5281/zenodo.{record_id}"
            or record.get("conceptdoi") != CONCEPT_DOI
            or metadata_projection(record.get("metadata"), public=True)
            != expected_public_projection(expected)
        ):
            return False
        order, files, _ = inventory(record.get("files"))
        return len(order) == 6 and set(files) == set(PUBLIC_NAMES) and all(
            files[name] == (name, local[name]["bytes"], local[name]["md5"])
            for name in PUBLIC_NAMES
        )
    except SystemExit:
        return False


def versions(session: requests.Session, seed: dict) -> list[dict]:
    links = seed.get("links")
    if not isinstance(links, dict) or not links.get("versions"):
        fail("public record omitted its concept-versions link")
    next_url = zenodo_url(links["versions"], "/api/records/")
    found, seen = [], set()
    for _ in range(20):
        if next_url in seen:
            fail("concept-version pagination looped")
        seen.add(next_url)
        page = get_json(session, next_url, "anonymous concept-versions read")
        hits = (page.get("hits") or {}).get("hits")
        if not isinstance(hits, list) or any(not isinstance(item, dict) for item in hits):
            fail("concept-version response schema mismatch")
        found.extend(hits)
        following = (page.get("links") or {}).get("next")
        if not following:
            return found
        next_url = zenodo_url(following, "/api/records/")
    fail("concept-version pagination exceeded its safety bound")


def remote_identity(session: requests.Session, url: str) -> tuple[int, str, str]:
    zenodo_url(url, "/")
    try:
        response = session.get(url, stream=True, timeout=300)
    except requests.RequestException:
        fail("anonymous Zenodo download failed before a response was received")
    if response.status_code != 200:
        fail(f"anonymous Zenodo download failed: HTTP {response.status_code}")
    sha256, md5, size = hashlib.sha256(), hashlib.md5(), 0
    try:
        for block in response.iter_content(1024 * 1024):
            if block:
                size += len(block); sha256.update(block); md5.update(block)
    except requests.RequestException:
        fail("anonymous Zenodo download was interrupted")
    return size, sha256.hexdigest(), md5.hexdigest()


def verify_public_record(
    session: requests.Session, record: dict, expected: dict, local: dict, evidence: dict
) -> tuple[list[dict], dict]:
    record_id = record.get("id")
    if (
        not plain_int(record_id) or record_id <= 0
        or str(record.get("conceptrecid")) != CONCEPT_ID
        or record.get("doi") != f"10.5281/zenodo.{record_id}"
        or record.get("conceptdoi") != CONCEPT_DOI
    ):
        fail("public Unit 6 record/DOI identity mismatch")
    validate_remote_metadata(record.get("metadata"), expected, public=True, label="public Unit 6")
    order, files, raw = inventory(record.get("files"))
    if len(order) != 6 or set(files) != set(PUBLIC_NAMES):
        fail("public Unit 6 six-file inventory mismatch")
    results = []
    for name in PUBLIC_NAMES:
        expected_value = (name, local[name]["bytes"], local[name]["md5"])
        if files[name] != expected_value:
            fail(f"public Zenodo API identity mismatch: {name}")
        links = raw[name].get("links")
        if not isinstance(links, dict) or not links.get("self"):
            fail(f"public Zenodo file omitted download URL: {name}")
        url = zenodo_url(links["self"], "/")
        value = remote_identity(session, url)
        if value != (local[name]["bytes"], local[name]["sha256"], local[name]["md5"]):
            fail(f"anonymous SHA-256/MD5 byte readback mismatch: {name}")
        results.append({
            "name": name, "bytes": value[0], "sha256": value[1], "md5": value[2],
            "download_url": url, "matches_local": True,
        })
    preserved = order == list(PUBLIC_NAMES)
    order_proof = {
        **evidence, "zenodo_api_file_order": order,
        "zenodo_api_preserved_intended_order": preserved,
        "zenodo_api_order_claim": (
            "reader-first order verified from the Zenodo API" if preserved else
            "no reader-first Zenodo API ordering claim; the primary PDF is proven by "
            "the exact description and byte-verified FILE_MANIFEST.csv"
        ),
    }
    return results, order_proof


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Anonymously verify exact Unit 6 metadata and all six public byte streams."
    )
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--record-id", type=int, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--staging-receipt", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    if args.record_id <= 0:
        fail("record-id must be positive")
    root = args.root.resolve()
    receipt = (root / args.receipt).resolve()
    if receipt.exists():
        fail(f"refusing to overwrite Zenodo public-readback receipt: {receipt}")
    expected, local, evidence = validate_boundary(
        root, (root / args.metadata).resolve(), (root / args.staging_receipt).resolve()
    )
    session = requests.Session(); session.trust_env = False
    record = get_json(
        session, f"https://zenodo.org/api/records/{args.record_id}",
        "anonymous Unit 6 record read",
    )
    files, order_proof = verify_public_record(session, record, expected, local, evidence)
    latest, latest_url = latest_public_record(session, record)
    result = {
        "schema_version": 1, "workflow": VERIFY_WORKFLOW, "status": "pass",
        "authentication_used": False,
        "verified_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "record_id": args.record_id, "concept_record_id": int(CONCEPT_ID),
        "doi": record.get("doi"), "concept_doi": CONCEPT_DOI,
        "record_url": f"https://zenodo.org/records/{args.record_id}",
        "api_url": f"https://zenodo.org/api/records/{args.record_id}",
        "latest_record_id": latest["id"], "latest_link": latest_url,
        "record_is_concept_latest": latest["id"] == args.record_id,
        "metadata_license": expected["license"], "reader_first_proof": order_proof,
        "files": files,
    }
    receipt.parent.mkdir(parents=True, exist_ok=True)
    try:
        with receipt.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(result, stream, ensure_ascii=True, indent=2, sort_keys=True)
            stream.write("\n")
    except FileExistsError:
        fail(f"refusing to overwrite Zenodo public-readback receipt: {receipt}")
    except OSError:
        fail("unable to write Zenodo public-readback receipt")
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))


if __name__ == "__main__":
    main()
