#!/usr/bin/env python3
"""Publish the verified complete O011 edition in its existing Zenodo lineage.

This thin specialization reuses the hardened Unit 22 transaction engine while
replacing every scope-sensitive constant and validation hook.  It performs all
local, package-integrity, metadata, and public-predecessor checks before reading
the runtime token.  Do not import this module as an authorization to publish;
publication occurs only when its command-line entry point is explicitly run.
"""

from __future__ import annotations

import importlib.util
import json
import zipfile
from pathlib import Path
from typing import Any


def load_base() -> Any:
    path = Path(__file__).resolve().with_name("publish_zenodo_unit22.py")
    spec = importlib.util.spec_from_file_location("o011_publish_unit22_base", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load the hardened Unit 22 publisher")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


B = load_base()

CONCEPT_ID = 22059977
CONCEPT_DOI = "10.5281/zenodo.22059977"
PREDECESSOR_ID = 22146873
PREDECESSOR_DOI = "10.5281/zenodo.22146873"
PREDECESSOR_VERSION = "2026.08.28-unit22"
PREDECESSOR_TITLE = "Geometri Diferensial dan Manifold Mulus — Edisi Bahasa Indonesia (Batas Unit 22)"
PREDECESSOR_READBACK_REL = "qa/unit-22/ZENODO_PUBLIC_READBACK_RECEIPT.json"
PREDECESSOR_READBACK_SHA256 = "0d3b14210fee7552cce8dd1aa442ea3c0f85b4dbb5686f4ee6e9cf9aa759c7c9"
PREDECESSOR_ORDER = [
    "geometri-diferensial-manifold-mulus-hingga-unit-22-id.pdf",
    "geometri-diferensial-manifold-mulus-unit22-html-20260828.zip",
    "geometri-diferensial-manifold-mulus-unit22-source-20260828.zip",
    "LICENSE.md",
    "RELEASE_NOTES_UNIT22_20260828.md",
    "FILE_MANIFEST.json",
    "SHA256SUMS.txt",
]
VERSION = "2026.08.28-complete"
PUBLICATION_DATE = "2026-08-28"
TITLE = "Geometri Diferensial dan Manifold Mulus — Edisi Bahasa Indonesia"
MODEL = "OpenAI Codex gpt-5.6-sol, Ultra"
SOURCE_URL = "https://de.wikiversity.org/wiki/Kurs:Differentialgeometrie_(Osnabr%C3%BCck_2023)"
RELEASE_DIR = Path("output/release-complete")
PREPARATION_WORKFLOW = "o011-prepare-release-complete-v1"
INTEGRITY_WORKFLOW = "o011-verify-source-package-complete-v1"
PDF_NAME = "geometri-diferensial-manifold-mulus-edisi-lengkap-id.pdf"
HTML_ZIP_NAME = "geometri-diferensial-manifold-mulus-edisi-lengkap-html-20260828.zip"
SOURCE_ZIP_NAME = "geometri-diferensial-manifold-mulus-edisi-lengkap-source-backend-20260828.zip"
EXPECTED_ORDER = [
    PDF_NAME,
    HTML_ZIP_NAME,
    SOURCE_ZIP_NAME,
    "LICENSE.md",
    "RELEASE_NOTES_COMPLETE_20260828.md",
    "FILE_MANIFEST.json",
    "SHA256SUMS.txt",
]


def patch_globals() -> None:
    values = {
        "__doc__": __doc__,
        "CONCEPT_ID": CONCEPT_ID,
        "CONCEPT_DOI": CONCEPT_DOI,
        "PREDECESSOR_ID": PREDECESSOR_ID,
        "PREDECESSOR_DOI": PREDECESSOR_DOI,
        "PREDECESSOR_VERSION": PREDECESSOR_VERSION,
        "PREDECESSOR_TITLE": PREDECESSOR_TITLE,
        "PREDECESSOR_READBACK_REL": PREDECESSOR_READBACK_REL,
        "PREDECESSOR_READBACK_SHA256": PREDECESSOR_READBACK_SHA256,
        "PREDECESSOR_ORDER": PREDECESSOR_ORDER,
        "VERSION": VERSION,
        "PUBLICATION_DATE": PUBLICATION_DATE,
        "TITLE": TITLE,
        "MODEL": MODEL,
        "SOURCE_URL": SOURCE_URL,
        "RELEASE_DIR": RELEASE_DIR,
        "PREPARATION_WORKFLOW": PREPARATION_WORKFLOW,
        "INTEGRITY_WORKFLOW": INTEGRITY_WORKFLOW,
        "PDF_NAME": PDF_NAME,
        "HTML_ZIP_NAME": HTML_ZIP_NAME,
        "SOURCE_ZIP_NAME": SOURCE_ZIP_NAME,
        "EXPECTED_ORDER": EXPECTED_ORDER,
    }
    for name, value in values.items():
        setattr(B, name, value)


def verify_source_archive(root: Path, local: dict[str, dict[str, Any]]) -> None:
    archive_path = local[SOURCE_ZIP_NAME]["path"]
    required = (
        "README.md",
        "LICENSE.md",
        "requirements-release.txt",
        "scripts/build_complete_reader.ps1",
        "scripts/verify_complete_reader.py",
        "scripts/export_html_complete.py",
        "scripts/verify_html_complete.py",
        "scripts/test_html_v19_pipeline.py",
        "scripts/export_backend_complete.py",
        "scripts/verify_backend_complete.py",
        "scripts/stage_zenodo_unit19.py",
        "scripts/stage_zenodo_unit22.py",
        "scripts/stage_zenodo_complete.py",
        "scripts/verify_source_package_unit22.py",
        "scripts/verify_source_package_complete.py",
        "scripts/publish_zenodo_unit22.py",
        "scripts/publish_zenodo_complete.py",
        "scripts/verify_zenodo_complete_public.py",
        "backend/records.jsonl",
        "backend/records.csv",
        "backend/MANIFEST.json",
        "qa/complete/build.json",
        "qa/complete/pdf_structural_qa.json",
        "qa/complete/driver_derivation.json",
        "qa/complete/HTML_READER_QA.json",
        "qa/complete/HTML_BROWSER_QA.json",
        "qa/complete/backend.json",
        "qa/complete/ZENODO_METADATA_COMPLETE.json",
        "PACKAGE_MANIFEST.json",
        "PACKAGE_CHECKSUMS.sha256",
    )
    try:
        with zipfile.ZipFile(archive_path, "r") as archive:
            if archive.testzip() is not None:
                B.fail("complete source/backend archive failed its CRC test")
            entries = B.safe_archive_entries(archive, "complete source/backend archive")
            if any(name.endswith("/00_control/PRIVATE_LOCAL_LOCATORS.md") for name in entries):
                B.fail("complete source/backend archive contains a private-locator control")
            for suffix in required:
                if suffix not in entries:
                    B.fail(f"complete source/backend archive lacks required dependency {suffix}")
            if archive.read(entries["LICENSE.md"]) != local["LICENSE.md"]["path"].read_bytes():
                B.fail("complete source archive and staged LICENSE.md differ")
    except (OSError, RuntimeError, zipfile.BadZipFile):
        B.fail("unable to verify the complete source/backend archive")


def verify_integrity_receipt(
    path: Path,
    source: dict[str, Any],
    html: dict[str, Any],
    pdf: dict[str, Any],
) -> dict[str, Any]:
    receipt = B.load_object(path, "complete source-package integrity receipt")
    if (
        receipt.get("schema_version") != 1
        or receipt.get("workflow") != INTEGRITY_WORKFLOW
        or receipt.get("status") != "pass"
    ):
        B.fail("source-package integrity receipt is not the passing complete-edition workflow")
    if not B.identity_occurs(receipt.get("source_zip"), source):
        B.fail("complete source-package receipt does not bind the staged source ZIP")
    clean = receipt.get("clean_rebuilds")
    if not isinstance(clean, list) or len(clean) != 2:
        B.fail("complete source-package receipt must contain exactly two clean rebuilds")
    outer = receipt.get("outer_release")
    outer_html = (outer.get("html") or {}) if isinstance(outer, dict) else {}
    if not B.identity_occurs(outer_html, html):
        B.fail("complete source-package receipt does not bind the staged HTML ZIP")
    outputs: list[dict[str, Any]] = []
    for item in clean:
        rebuilt = item.get("outputs") if isinstance(item, dict) else None
        if not isinstance(rebuilt, dict) or item.get("offline_proxy_blocking") is not True:
            B.fail("a complete-edition clean rebuild is absent or not offline")
        if not B.identity_occurs(rebuilt.get("pdf"), pdf):
            B.fail("a clean rebuild does not bind the complete PDF bytes")
        if rebuilt.get("html_tree_sha256") != outer_html.get("tree_sha256"):
            B.fail("a clean rebuild HTML tree does not bind the staged HTML archive")
        outputs.append(rebuilt)
    if outputs[0] != outputs[1]:
        B.fail("complete-edition clean rebuild outputs differ across cycles")
    if not B.all_boolean_leaves_true(receipt.get("checks")):
        B.fail("complete source-package integrity checks are absent or not all passing")
    return receipt


def local_payload(
    root: Path,
    preparation_path: Path,
    integrity_path: Path,
) -> tuple[dict[str, Any], dict[str, dict[str, Any]], list[str]]:
    stage = B.load_object(preparation_path, "complete release-preparation receipt")
    if (
        stage.get("schema_version") != 1
        or stage.get("workflow") != PREPARATION_WORKFLOW
        or stage.get("status") != "pass"
        or stage.get("version") != VERSION
        or stage.get("coverage") != "complete_edition"
        or stage.get("model_identification") != MODEL
        or stage.get("remote_state_mutated") is not False
    ):
        B.fail("release-preparation receipt is not the passing local-only complete workflow")
    rows = stage.get("files")
    if not isinstance(rows, list) or [row.get("filename") for row in rows if isinstance(row, dict)] != EXPECTED_ORDER:
        B.fail("complete release-preparation receipt has the wrong seven-file inventory")
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
        B.fail("complete release-preparation receipt has the wrong lineage or reader-first order")
    release = root / RELEASE_DIR
    if not release.is_dir():
        B.fail("complete release directory is absent")
    if sorted(path.name for path in release.iterdir() if path.is_file()) != sorted(EXPECTED_ORDER):
        B.fail("complete release directory contains a missing or extra loose file")
    local: dict[str, dict[str, Any]] = {}
    total = 0
    for row in rows:
        if not isinstance(row, dict):
            B.fail("complete release-preparation file row is malformed")
        name = row.get("filename")
        if name not in EXPECTED_ORDER or Path(str(name)).name != name:
            B.fail("complete release-preparation filename is unsafe")
        file_path = release / str(name)
        if not file_path.is_file():
            B.fail(f"staged complete-edition file is missing: {name}")
        actual = {
            "path": file_path,
            "bytes": file_path.stat().st_size,
            "sha256": B.digest(file_path),
            "md5": B.digest(file_path, "md5"),
        }
        if any(actual[key] != row.get(key) for key in ("bytes", "sha256", "md5")):
            B.fail(f"staged complete-edition file changed after preparation: {name}")
        local[str(name)] = actual
        total += int(actual["bytes"])
    if (
        total > B.MAX_PUBLIC_BYTES
        or stage.get("public_bytes") != total
        or stage.get("total_public_bytes") != total
        or stage.get("maximum_public_bytes") != B.MAX_PUBLIC_BYTES
        or stage.get("under_500000000_bytes") is not True
    ):
        B.fail("complete public payload exceeds 500 MB or its bound total changed")
    pdf_identity = {key: local[PDF_NAME][key] for key in ("bytes", "sha256")}
    if not B.identity_occurs(stage.get("input_bindings"), pdf_identity):
        B.fail("complete stage does not bind its PDF to the validated reader gate")
    privacy = stage.get("privacy_scan")
    if (
        not isinstance(privacy, dict)
        or privacy.get("status") != "pass"
        or privacy.get("private_locator_hits") != 0
        or privacy.get("credential_like_content_hits") != 0
        or privacy.get("local_profile_name_hits") != 0
    ):
        B.fail("complete stage lacks a passing privacy scan")
    archives = stage.get("deterministic_archives")
    if not isinstance(archives, dict) or archives.get("status") != "pass":
        B.fail("complete stage lacks passing deterministic-archive evidence")
    verify_source_archive(root, local)
    integrity = verify_integrity_receipt(
        integrity_path,
        {key: local[SOURCE_ZIP_NAME][key] for key in ("bytes", "sha256")},
        {key: local[HTML_ZIP_NAME][key] for key in ("bytes", "sha256")},
        pdf_identity,
    )
    expected_identities = {
        name: {key: local[name][key] for key in ("bytes", "sha256")}
        for name in EXPECTED_ORDER
    }
    outer_rows = (integrity.get("outer_release") or {}).get("files")
    if (
        not isinstance(outer_rows, list)
        or {
            str(row.get("filename")): {key: row.get(key) for key in ("bytes", "sha256")}
            for row in outer_rows
            if isinstance(row, dict)
        }
        != expected_identities
    ):
        B.fail("complete integrity receipt does not bind all seven staged public files")
    for cycle in integrity.get("clean_rebuilds", []):
        if not isinstance(cycle, dict) or cycle.get("restaged_files") != expected_identities:
            B.fail("a clean complete-edition cycle does not restage all seven public files byte-identically")
    return stage, local, EXPECTED_ORDER.copy()


def metadata_pair(path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    payload = B.load_object(path, "complete Zenodo metadata")
    if set(payload) != {"metadata"} or not isinstance(payload["metadata"], dict):
        B.fail("complete metadata must contain exactly one metadata object")
    legacy = payload["metadata"]
    required_keys = {
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
    if set(legacy) != required_keys:
        B.fail("complete Zenodo metadata schema is not exact")
    if legacy.get("title") != TITLE or legacy.get("version") != VERSION or legacy.get("publication_date") != PUBLICATION_DATE:
        B.fail("complete title, version, or publication date is not exact")
    description = legacy.get("description")
    required_description = (
        "Complete reader-first Indonesian adaptation",
        "all 29 lecture and worksheet pairs",
        "576 source exercises",
        "84 source-supplied worksheet solutions",
        "123 actual problem occurrences",
        "117 source-supplied solution occurrences",
        "38 original solution-bearing items",
        "6,912 stable-ID records",
        "CC BY-SA 4.0",
        "Component media retain their file-specific rights; no blanket media license is inferred.",
        MODEL,
    )
    if not isinstance(description, str) or any(text not in description for text in required_description):
        B.fail("complete description lacks exact scope, rights, or provenance")
    if description.count(MODEL) != 1 or B.PRIVATE_RE.search(description) or B.SECRET_RE.search(description):
        B.fail("complete description duplicated provenance or exposed private material")
    if legacy.get("creators") != [{"name": "Brenner, Holger"}]:
        B.fail("complete source creator attribution is not exact")
    if legacy.get("contributors") != [{"name": "TTP", "type": "Other"}]:
        B.fail("complete metadata must contain exactly one organizational contributor")
    serialized = json.dumps(legacy, ensure_ascii=False)
    without_contributors = json.dumps({key: value for key, value in legacy.items() if key != "contributors"}, ensure_ascii=False)
    if len(B.TTP_RE.findall(serialized)) != 1 or B.TTP_RE.search(without_contributors):
        B.fail("organization label must appear exactly once and only in contributor metadata")
    if legacy.get("license") != "other-open" or legacy.get("language") != "ind":
        B.fail("complete mixed-rights license or Indonesian language metadata is not exact")
    keywords = legacy.get("keywords")
    if not isinstance(keywords, list) or not keywords or not all(isinstance(item, str) and item.strip() for item in keywords):
        B.fail("complete metadata keywords are malformed")
    expected_related = [{
        "identifier": SOURCE_URL,
        "relation": "isDerivedFrom",
        "resource_type": "publication-book",
        "scheme": "url",
    }]
    if legacy.get("related_identifiers") != expected_related:
        B.fail("complete source relationship metadata is not exact")
    modern = {
        "resource_type": {"id": "publication-book"},
        "title": TITLE,
        "publisher": "Zenodo",
        "publication_date": PUBLICATION_DATE,
        "description": description,
        "version": VERSION,
        "creators": [{"person_or_org": {"type": "personal", "name": "Brenner, Holger", "given_name": "Holger", "family_name": "Brenner"}}],
        "contributors": [{"person_or_org": {"type": "organizational", "name": "TTP"}, "role": {"id": "other"}}],
        "subjects": [{"subject": item} for item in keywords],
        "languages": [{"id": "ind"}],
        "rights": [{"id": "other-open"}],
        "related_identifiers": [{
            "identifier": SOURCE_URL,
            "scheme": "url",
            "relation_type": {"id": "isderivedfrom"},
            "resource_type": {"id": "publication-book"},
        }],
    }
    return legacy, modern


def predecessor_ok(record: dict[str, Any]) -> None:
    metadata = record.get("metadata") or {}
    if (
        B.record_id(record) != PREDECESSOR_ID
        or B.concept_id(record) != str(CONCEPT_ID)
        or B.record_doi(record) != PREDECESSOR_DOI
        or metadata.get("version") != PREDECESSOR_VERSION
        or metadata.get("title") != PREDECESSOR_TITLE
        or record.get("status") != "published"
        or (record.get("access") or {}).get("record") != "public"
        or (record.get("access") or {}).get("files") != "public"
    ):
        B.fail("Zenodo predecessor is not the exact public Unit 22 boundary")


def verify_predecessor_boundary(root: Path, predecessor: dict[str, Any]) -> dict[str, Any]:
    receipt_path = root / PREDECESSOR_READBACK_REL
    if not receipt_path.is_file() or B.digest(receipt_path) != PREDECESSOR_READBACK_SHA256:
        B.fail("exact Unit 22 public-readback receipt is absent or changed")
    receipt = B.load_object(receipt_path, "Unit 22 public-readback receipt")
    receipt_files = receipt.get("files")
    if (
        receipt.get("schema_version") != 1
        or receipt.get("workflow") != "o011-independent-zenodo-unit22-public-readback-v1"
        or receipt.get("status") != "pass"
        or receipt.get("record_id") != PREDECESSOR_ID
        or receipt.get("concept_record_id") != CONCEPT_ID
        or receipt.get("doi") != PREDECESSOR_DOI
        or receipt.get("concept_doi") != CONCEPT_DOI
        or receipt.get("version") != PREDECESSOR_VERSION
        or receipt.get("authentication_used") is not False
        or receipt.get("expected_reader_first_order") != PREDECESSOR_ORDER
        or not isinstance(receipt.get("rdm_file_order"), list)
        or set(receipt.get("rdm_file_order")) != set(PREDECESSOR_ORDER)
        or not isinstance(receipt_files, list)
        or [item.get("name") for item in receipt_files if isinstance(item, dict)] != PREDECESSOR_ORDER
    ):
        B.fail("Unit 22 readback receipt is not the exact passing predecessor proof")
    order, entries, default_preview = B.public_inventory(predecessor)
    if set(order) != set(PREDECESSOR_ORDER) or set(entries) != set(PREDECESSOR_ORDER) or default_preview != receipt.get("pdf_default_preview"):
        B.fail("public Unit 22 inventory or preview differs from its exact proof")
    expected = {str(item["name"]): item for item in receipt_files if isinstance(item, dict)}
    for name in PREDECESSOR_ORDER:
        if entries[name].get("size") != expected[name].get("bytes") or B.checksum_md5(entries[name]) != expected[name].get("md5"):
            B.fail(f"public Unit 22 file identity differs from its proof: {name}")
    return {
        "record_id": B.record_id(predecessor),
        "doi": B.record_doi(predecessor),
        "version": (predecessor.get("metadata") or {}).get("version"),
        "file_count": len(entries),
        "file_order": order,
        "default_preview": default_preview,
        "status": "pass",
    }


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
    _, _, default_preview = B.public_inventory(record)
    result: dict[str, Any] = {
        "schema_version": 1,
        "workflow": "o011-publish-zenodo-complete-v1",
        "status": "pass",
        "publication_action": action,
        "authentication_used_for_publication_path": authenticated,
        "authentication_used_for_public_readback": False,
        "verified_at_utc": B.dt.datetime.now(B.dt.timezone.utc).isoformat(),
        "record_id": B.record_id(record),
        "concept_record_id": CONCEPT_ID,
        "predecessor_record_id": PREDECESSOR_ID,
        "doi": B.record_doi(record),
        "concept_doi": CONCEPT_DOI,
        "record_url": f"https://zenodo.org/records/{B.record_id(record)}",
        "version": VERSION,
        "coverage": "complete_edition",
        "predecessor_boundary": predecessor_proof,
        "reader_content_extended_from_predecessor": True,
        "reader_first_order": order,
        "public_file_order": public_order,
        "pdf_default_preview": default_preview,
        "pdf_default_preview_verified": default_preview == PDF_NAME,
        "files": files,
        "metadata_title": legacy["title"],
        "release_preparation_receipt_sha256": B.digest(preparation_path),
        "source_package_integrity_receipt_sha256": B.digest(integrity_path),
        "remote_state_mutated": action == "published_new_version",
    }
    if draft is not None:
        normalized = dict(draft)
        if normalized.get("origin") == "created_from_exact_unit19_predecessor":
            normalized["origin"] = "created_from_exact_unit22_predecessor"
        result["draft"] = normalized
    return result


patch_globals()
B.verify_source_archive = verify_source_archive
B.verify_integrity_receipt = verify_integrity_receipt
B.local_payload = local_payload
B.metadata_pair = metadata_pair
B.predecessor_ok = predecessor_ok
B.verify_predecessor_boundary = verify_predecessor_boundary
B.publication_receipt = publication_receipt


if __name__ == "__main__":
    raise SystemExit(B.main())
