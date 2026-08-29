#!/usr/bin/env python3
"""Stage the deterministic seven-file complete O011 release without remote mutation."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any, Iterable


def load_unit22() -> Any:
    path = Path(__file__).resolve().with_name("stage_zenodo_unit22.py")
    spec = importlib.util.spec_from_file_location("o011_stage_unit22_base", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load the hardened Unit 22 release stager")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


U = load_unit22()
B = U.B

RELEASE_DATE = "2026-08-28"
VERSION = "2026.08.28-complete"
TITLE = "Geometri Diferensial dan Manifold Mulus — Edisi Bahasa Indonesia"
MODEL = "OpenAI Codex gpt-5.6-sol, Ultra"
ZIP_TIMESTAMP = (2026, 8, 28, 0, 0, 0)
MAX_PUBLIC_BYTES = 500_000_000
PREDECESSOR_RECORD_ID = 22146873
CONCEPT_RECORD_ID = 22059977

PDF_REL = "output/pdf/geometri-diferensial-manifold-mulus-edisi-lengkap-id.pdf"
HTML_ROOT_REL = "output/html/complete"
HTML_ENTRY_REL = f"{HTML_ROOT_REL}/index.html"
HTML_MANIFEST_REL = f"{HTML_ROOT_REL}/manifest.json"
BUILD_QA_REL = "qa/complete/build.json"
PDF_STRUCTURAL_QA_REL = "qa/complete/pdf_structural_qa.json"
DRIVER_QA_REL = "qa/complete/driver_derivation.json"
HTML_READER_QA_REL = "qa/complete/HTML_READER_QA.json"
HTML_BROWSER_QA_REL = "qa/complete/HTML_BROWSER_QA.json"
BACKEND_MANIFEST_REL = "backend/MANIFEST.json"
BACKEND_QA_REL = "qa/complete/backend.json"
LICENSE_SOURCE_REL = "qa/complete/LICENSE_RELEASE_COMPLETE.md"
README_SOURCE_REL = "qa/complete/PACKAGE_README.md"
NOTES_SOURCE_REL = "qa/complete/RELEASE_NOTES_COMPLETE_20260828.md"
METADATA_REL = "qa/complete/ZENODO_METADATA_COMPLETE.json"

PDF_NAME = "geometri-diferensial-manifold-mulus-edisi-lengkap-id.pdf"
HTML_ZIP_NAME = "geometri-diferensial-manifold-mulus-edisi-lengkap-html-20260828.zip"
SOURCE_ZIP_NAME = "geometri-diferensial-manifold-mulus-edisi-lengkap-source-backend-20260828.zip"
LICENSE_NAME = "LICENSE.md"
NOTES_NAME = "RELEASE_NOTES_COMPLETE_20260828.md"
MANIFEST_NAME = "FILE_MANIFEST.json"
CHECKSUMS_NAME = "SHA256SUMS.txt"
PUBLIC_FILE_ORDER = (
    PDF_NAME,
    HTML_ZIP_NAME,
    SOURCE_ZIP_NAME,
    LICENSE_NAME,
    NOTES_NAME,
    MANIFEST_NAME,
    CHECKSUMS_NAME,
)
DEFAULT_OUTPUT_REL = "output/release-complete"
DEFAULT_RECEIPT_REL = "qa/complete/RELEASE_PREPARATION_RECEIPT.json"

SCRIPT_PATHS = (
    "scripts/build_complete_reader.ps1",
    "scripts/verify_complete_reader.py",
    "scripts/export_html_complete.py",
    "scripts/verify_html_complete.py",
    "scripts/export_backend_complete.py",
    "scripts/verify_backend_complete.py",
    "scripts/export_backend_v10.py",
    "scripts/verify_backend_v10.py",
    "scripts/export_backend_v19.py",
    "scripts/verify_backend_v19.py",
    "scripts/export_backend_v22.py",
    "scripts/verify_backend_v22.py",
    "scripts/export_html_v10.py",
    "scripts/export_html_v13.py",
    "scripts/export_html_v19.py",
    "scripts/export_html_v22.py",
    "scripts/verify_html_v10.py",
    "scripts/verify_html_v13.py",
    "scripts/verify_html_v19.py",
    "scripts/verify_html_v22.py",
    "scripts/test_html_v19_pipeline.py",
    "scripts/verify_html_animated_media.py",
    "scripts/prepare_unit_tex.py",
    "scripts/prepare_unit_media.py",
    "scripts/stage_zenodo_unit19.py",
    "scripts/stage_zenodo_unit22.py",
    "scripts/stage_zenodo_complete.py",
    "scripts/verify_source_package_unit22.py",
    "scripts/verify_source_package_complete.py",
    "scripts/publish_zenodo_unit22.py",
    "scripts/publish_zenodo_complete.py",
    "scripts/verify_zenodo_complete_public.py",
)
BASELINE_TREES = (
    "output/html/unit-10",
    "output/html/unit-13",
    "output/html/unit-19",
    "output/html/unit-22",
)
FIXED_SUPPORT_PATHS = (
    "requirements-release.txt",
    "authority/brenner_media_rights_manifest.csv",
    "source/unit_media.json",
    "source/unit07_interactive_media.json",
    "source/unit11_interactive_media.json",
    "authority/expanded/script_preamble_source.de.tex",
    "build/brenner-compat.tex",
    "build/generated/through-unit-22-driver.tex",
    "build/generated/complete-reader-driver.tex",
    "backend/README.md",
    "backend/schema/o011-record-v1.schema.json",
    "backend/MANIFEST.json",
    "backend/records.csv",
    "backend/records.jsonl",
    "qa/unit-10/HTML_READER_QA.json",
    "qa/unit-10/ZENODO_PUBLIC_READBACK_RECEIPT.json",
    "output/release-unit10/geometri-diferensial-manifold-mulus-brenner-id-unit10-html-20260823.zip",
    "qa/unit-13/HTML_READER_QA.json",
    "qa/unit-13/ZENODO_PUBLIC_READBACK_RECEIPT_R1.json",
    "qa/unit-13/GITHUB_PUBLIC_READBACK_RECEIPT_R1.json",
    "output/release-unit13-r1/geometri-diferensial-manifold-mulus-brenner-id-unit13-html-20260825.zip",
    "qa/unit-19/HTML_READER_QA.json",
    "qa/unit-22/ZENODO_PUBLIC_READBACK_RECEIPT.json",
)


def patch_base_globals() -> None:
    values = {
        "RELEASE_DATE": RELEASE_DATE,
        "VERSION": VERSION,
        "TITLE": TITLE,
        "ZIP_TIMESTAMP": ZIP_TIMESTAMP,
        "MODEL": MODEL,
        "MAX_PUBLIC_BYTES": MAX_PUBLIC_BYTES,
        "PREDECESSOR_RECORD_ID": PREDECESSOR_RECORD_ID,
        "CONCEPT_RECORD_ID": CONCEPT_RECORD_ID,
        "PDF_REL": PDF_REL,
        "HTML_ROOT_REL": HTML_ROOT_REL,
        "HTML_ENTRY_REL": HTML_ENTRY_REL,
        "HTML_MANIFEST_REL": HTML_MANIFEST_REL,
        "BUILD_QA_REL": BUILD_QA_REL,
        "PDF_STRUCTURAL_QA_REL": PDF_STRUCTURAL_QA_REL,
        "HTML_READER_QA_REL": HTML_READER_QA_REL,
        "HTML_BROWSER_QA_REL": HTML_BROWSER_QA_REL,
        "BACKEND_MANIFEST_REL": BACKEND_MANIFEST_REL,
        "BACKEND_QA_REL": BACKEND_QA_REL,
        "LICENSE_SOURCE_REL": LICENSE_SOURCE_REL,
        "README_SOURCE_REL": README_SOURCE_REL,
        "NOTES_SOURCE_REL": NOTES_SOURCE_REL,
        "METADATA_REL": METADATA_REL,
        "PDF_NAME": PDF_NAME,
        "HTML_ZIP_NAME": HTML_ZIP_NAME,
        "SOURCE_ZIP_NAME": SOURCE_ZIP_NAME,
        "LICENSE_NAME": LICENSE_NAME,
        "NOTES_NAME": NOTES_NAME,
        "MANIFEST_NAME": MANIFEST_NAME,
        "CHECKSUMS_NAME": CHECKSUMS_NAME,
        "PUBLIC_FILE_ORDER": PUBLIC_FILE_ORDER,
        "DEFAULT_OUTPUT_REL": DEFAULT_OUTPUT_REL,
        "DEFAULT_RECEIPT_REL": DEFAULT_RECEIPT_REL,
    }
    for name, value in values.items():
        setattr(B, name, value)


patch_base_globals()


def required_identity(root: Path, relative: str, label: str) -> dict[str, int | str]:
    path = root / relative
    if not path.is_file():
        raise RuntimeError(f"complete-release gate is waiting for {label}: {relative}")
    return B.identity(path, relative)


def identity_occurs(value: Any, wanted: dict[str, Any]) -> bool:
    if isinstance(value, dict):
        if value.get("bytes") == wanted.get("bytes") and value.get("sha256") == wanted.get("sha256"):
            return True
        return any(identity_occurs(child, wanted) for child in value.values())
    if isinstance(value, list):
        return any(identity_occurs(child, wanted) for child in value)
    return False


def collect_gate(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    paths = {
        "pdf": (PDF_REL, "the final complete PDF"),
        "build_qa": (BUILD_QA_REL, "the deterministic complete-PDF build receipt"),
        "pdf_structural_qa": (PDF_STRUCTURAL_QA_REL, "the complete-PDF structural receipt"),
        "driver_qa": (DRIVER_QA_REL, "the complete-PDF driver derivation receipt"),
        "html_entry": (HTML_ENTRY_REL, "the complete semantic HTML entry"),
        "html_manifest": (HTML_MANIFEST_REL, "the complete semantic HTML manifest"),
        "html_reader_qa": (HTML_READER_QA_REL, "the complete semantic HTML deterministic receipt"),
        "html_browser_qa": (HTML_BROWSER_QA_REL, "the complete real-browser desktop/mobile receipt"),
        "backend_manifest": (BACKEND_MANIFEST_REL, "the complete stable-ID backend manifest"),
        "backend_qa": (BACKEND_QA_REL, "the complete stable-ID backend verifier receipt"),
        "metadata": (METADATA_REL, "the complete Zenodo metadata"),
    }
    current = {name: required_identity(root, relative, label) for name, (relative, label) in paths.items()}
    build = B.load_json(root / BUILD_QA_REL)
    structural = B.load_json(root / PDF_STRUCTURAL_QA_REL)
    driver = B.load_json(root / DRIVER_QA_REL)
    html_manifest = B.load_json(root / HTML_MANIFEST_REL)
    html_qa = B.load_json(root / HTML_READER_QA_REL)
    html_browser = B.load_json(root / HTML_BROWSER_QA_REL)
    backend_manifest = B.load_json(root / BACKEND_MANIFEST_REL)
    backend_qa = B.load_json(root / BACKEND_QA_REL)

    if build.get("workflow") != "o011-complete-reader-pdf-build-v1":
        raise RuntimeError("complete PDF build workflow differs")
    B.assert_record(root, build.get("output"), PDF_REL)
    cycles = build.get("cycles")
    if not isinstance(cycles, list) or len(cycles) != 2 or any(not identity_occurs(cycle, current["pdf"]) for cycle in cycles):
        raise RuntimeError("complete PDF receipt does not prove two byte-identical cycles")
    core_units = build.get("core_units")
    if (
        not isinstance(core_units, list)
        or not all(isinstance(row, dict) for row in core_units)
        or [row.get("unit") for row in core_units if isinstance(row, dict)] != list(range(23, 30))
        or any(set(row) != {"unit", "source_supplied_solution_numbers"} for row in core_units if isinstance(row, dict))
    ):
        raise RuntimeError("complete PDF unit-extension census differs")
    if build.get("exam_surfaces") != {"learner_forms": 10, "official_solution_forms": 10, "original_repairs": 6}:
        raise RuntimeError("complete PDF exam-surface census differs")
    if driver.get("workflow") != "o011-complete-reader-driver-derivation-v1" or driver.get("unit_extension") != list(range(23, 30)):
        raise RuntimeError("complete PDF driver derivation differs")
    if structural.get("workflow") != "o011-complete-reader-structural-qa-v1" or structural.get("status") != "pass":
        raise RuntimeError("complete PDF structural QA has not passed")
    if not identity_occurs(structural, current["pdf"]) or not identity_occurs(structural, current["build_qa"]):
        raise RuntimeError("complete PDF structural QA does not bind the final PDF/build receipt")
    if isinstance(structural.get("checks"), dict) and not B.all_true(structural["checks"]):
        raise RuntimeError("complete PDF structural checks are not all passing")
    pages = structural.get("pages")
    if pages is None and isinstance(structural.get("pdf"), dict):
        pages = structural["pdf"].get("page_count")
    if not isinstance(pages, int) or pages <= 0:
        raise RuntimeError("complete PDF structural QA lacks a positive exact page count")

    if (
        html_manifest.get("workflow") != "o011-export-html-complete-v1"
        or html_manifest.get("status") != "complete_edition"
        or html_manifest.get("model_identification") != MODEL
        or html_manifest.get("text_license") != "CC BY-SA 4.0"
        or html_manifest.get("non_endorsement") is not True
        or html_manifest.get("units") != list(range(1, 30))
    ):
        raise RuntimeError("complete HTML manifest workflow/scope/rights contract differs")
    if html_qa.get("workflow") != "o011-verify-html-complete-v1" or html_qa.get("status") != "pass" or not B.all_true(html_qa.get("checks")):
        raise RuntimeError("complete HTML deterministic QA has not passed")
    B.assert_record(root, html_qa.get("entry"), HTML_ENTRY_REL)
    B.assert_record(root, html_qa.get("manifest"), HTML_MANIFEST_REL)
    counts = html_qa.get("counts", {})
    required_counts = {
        "units": 29,
        "core_exercises": 576,
        "core_source_supplied_solutions": 84,
        "exam_forms": 10,
        "exam_nominal_slots": 147,
        "exam_actual_occurrences": 123,
        "exam_zero_point_placeholders": 24,
        "exam_source_supplied_solutions": 117,
        "exam_original_missing_solution_repairs": 6,
        "original_bridges": 2,
        "bridge_solution_bearing_items": 32,
    }
    if any(counts.get(key) != value for key, value in required_counts.items()):
        raise RuntimeError("complete HTML semantic census differs")
    if html_browser.get("status") != "pass" or not B.all_true(html_browser.get("checks")):
        raise RuntimeError("complete HTML browser QA has not passed")
    for wanted in (current["html_entry"], current["html_manifest"], current["html_reader_qa"]):
        if not identity_occurs(html_browser, wanted):
            raise RuntimeError("complete HTML browser QA does not bind every deterministic HTML surface")
    html_tree = B.verify_html_tree(root, html_manifest, html_qa)

    if backend_manifest.get("workflow") != "o011-export-backend-complete" or backend_manifest.get("combined", {}).get("record_count") != 6912:
        raise RuntimeError("complete backend manifest workflow/count differs")
    if not isinstance(backend_manifest.get("claims"), dict) or not B.all_true(backend_manifest["claims"]):
        raise RuntimeError("complete backend manifest claims are incomplete")
    extension = backend_manifest.get("extension", {})
    exam = extension.get("exam_authority", {})
    originals = extension.get("original_solution_bearing_items", {})
    if (
        extension.get("record_count") != 2588
        or extension.get("core_final") != {"exercises": 576, "source_supplied_solutions": 84}
        or exam.get("actual_occurrences") != 123
        or exam.get("source_supplied_solutions") != 117
        or exam.get("source_missing_solutions") != 6
        or originals.get("total") != 38
    ):
        raise RuntimeError("complete backend semantic extension census differs")
    if backend_qa.get("workflow") != "o011-verify-backend-complete" or backend_qa.get("status") != "pass" or not B.all_true(backend_qa.get("checks")):
        raise RuntimeError("complete backend verifier has not passed")
    if backend_qa.get("combined_records") != 6912 or backend_qa.get("determinism", {}).get("second_reconstruction_matches_first") is not True:
        raise RuntimeError("complete backend count/determinism contract differs")
    backend_outputs: dict[str, dict[str, int | str]] = {}
    for key, relative in (("records_csv", "backend/records.csv"), ("records_jsonl", "backend/records.jsonl")):
        backend_outputs[key] = B.assert_record(root, backend_qa.get("outputs", {}).get(key), relative)
        B.assert_record(root, backend_manifest.get("outputs", {}).get(key), relative)
    B.assert_record(root, backend_qa.get("outputs", {}).get("manifest"), BACKEND_MANIFEST_REL)

    gate = {
        **current,
        "backend_records_csv": backend_outputs["records_csv"],
        "backend_records_jsonl": backend_outputs["records_jsonl"],
        "html_tree": html_tree,
        "coverage": {
            "core_units": 29,
            "core_exercises": 576,
            "core_source_supplied_solutions": 84,
            "exam_actual_occurrences": 123,
            "exam_source_supplied_solutions": 117,
            "original_solution_bearing_items": 38,
            "backend_records": 6912,
            "pdf_pages": pages,
        },
    }
    return gate, {"build": build, "html_manifest": html_manifest, "backend_manifest": backend_manifest}


def validate_metadata(document: Any) -> None:
    if not isinstance(document, dict) or set(document) != {"metadata"} or not isinstance(document["metadata"], dict):
        raise RuntimeError("Zenodo metadata outer contract differs")
    metadata = document["metadata"]
    expected_keys = {"title", "description", "creators", "contributors", "license", "publication_date", "version", "language", "keywords", "related_identifiers"}
    if set(metadata) != expected_keys:
        raise RuntimeError("Zenodo metadata keys differ")
    if metadata["title"] != TITLE or metadata["version"] != VERSION or metadata["publication_date"] != RELEASE_DATE:
        raise RuntimeError("Zenodo date/version/title contract differs")
    if metadata["creators"] != [{"name": "Brenner, Holger"}] or metadata["contributors"] != [{"name": "TTP", "type": "Other"}]:
        raise RuntimeError("Zenodo creator/contributor contract differs")
    if metadata["license"] != "other-open" or metadata["language"] != "ind":
        raise RuntimeError("Zenodo mixed-rights/language contract differs")
    description = str(metadata["description"])
    required = (
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
    if any(phrase not in description for phrase in required) or description.count(MODEL) != 1:
        raise RuntimeError("Zenodo description lacks exact complete scope, rights, or provenance")
    serialized = json.dumps(document, ensure_ascii=False)
    without_contributors = json.dumps({"metadata": {key: value for key, value in metadata.items() if key != "contributors"}}, ensure_ascii=False)
    if serialized.count("TTP") != 1 or "TTP" in without_contributors or "Translation and Transcription Project" in serialized:
        raise RuntimeError("organization label must appear exactly once and only in contributor metadata")
    B.scan_bytes("complete Zenodo metadata", json.dumps(document, ensure_ascii=False, sort_keys=True).encode("utf-8"))


def add_records(mapping: dict[str, Path], root: Path, records: Iterable[Any]) -> None:
    for record in records:
        if isinstance(record, dict) and isinstance(record.get("path"), str):
            B.add_bound_record(mapping, root, record, allow_current_reader=True)


def add_html_generation_closure(mapping: dict[str, Path], root: Path) -> None:
    """Add the exact transitive QA/authority closure used by v13/v19/v22."""
    for unit in range(11, 23):
        tag = f"{unit:02d}"
        unit_directory = root / f"source/units/unit-{tag}"
        if not unit_directory.is_dir():
            raise RuntimeError(f"HTML generation closure lacks source unit directory: {unit_directory.relative_to(root)}")
        targets = sorted(unit_directory.glob("*.id.tex"), key=lambda path: path.name)
        if not targets:
            raise RuntimeError(f"HTML generation closure has no translated surfaces for Unit {unit}")
        for target in targets:
            target_relative = target.relative_to(root).as_posix()
            receipt_relative = f"qa/unit-{tag}/{target.name.removesuffix('.id.tex')}_translation.json"
            receipt_path = B.project_path(root, receipt_relative)
            receipt = B.load_json(receipt_path)
            authority_relative = receipt.get("source") if isinstance(receipt, dict) else None
            if not isinstance(authority_relative, str) or not authority_relative:
                raise RuntimeError(f"translation receipt lacks its authority source: {receipt_relative}")
            B.add_mapping(mapping, target_relative, target)
            B.add_mapping(mapping, receipt_relative, receipt_path)
            B.add_mapping(mapping, authority_relative, B.project_path(root, authority_relative))
        post_relative = f"qa/unit-{tag}/POST_CORRECTION_MATH_QA.json"
        B.add_mapping(mapping, post_relative, B.project_path(root, post_relative))
    verify_relative = "qa/unit-22/POST_CORRECTION_MATH_QA_VERIFY.json"
    B.add_mapping(mapping, verify_relative, B.project_path(root, verify_relative))
    for unit in range(1, 23):
        relative = f"qa/unit-{unit:02d}_media.json"
        B.add_mapping(mapping, relative, B.project_path(root, relative))
    for relative in (
        "qa/unit-07/INTERACTIVE_MEDIA_QA.json",
        "qa/unit-11/INTERACTIVE_MEDIA_QA.json",
        "qa/unit-12/ANIMATED_MEDIA_QA.json",
        "qa/unit-12/HTML_ANIMATED_MEDIA_QA.json",
        "qa/unit-18/ANIMATED_MEDIA_QA.json",
    ):
        B.add_mapping(mapping, relative, B.project_path(root, relative))


def copy_source_tree(root: Path, staging: Path, documents: dict[str, Any], gate: dict[str, Any]) -> dict[str, Any]:
    mapping: dict[str, Path] = {}
    for archive_name, relative in (
        ("README.md", README_SOURCE_REL),
        ("PACKAGE_README.md", README_SOURCE_REL),
        (LICENSE_NAME, LICENSE_SOURCE_REL),
        (NOTES_NAME, NOTES_SOURCE_REL),
        ("ZENODO_METADATA.json", METADATA_REL),
        (README_SOURCE_REL, README_SOURCE_REL),
        (LICENSE_SOURCE_REL, LICENSE_SOURCE_REL),
        (NOTES_SOURCE_REL, NOTES_SOURCE_REL),
        (METADATA_REL, METADATA_REL),
    ):
        B.add_mapping(mapping, archive_name, B.project_path(root, relative))
    for relative in (*FIXED_SUPPORT_PATHS, *SCRIPT_PATHS):
        B.add_mapping(mapping, relative, B.project_path(root, relative))
    for relative in BASELINE_TREES:
        B.add_tree(mapping, root, relative)
    add_html_generation_closure(mapping, root)

    build_inputs = documents["build"].get("inputs")
    if isinstance(build_inputs, dict):
        add_records(mapping, root, build_inputs.values())
    elif isinstance(build_inputs, list):
        add_records(mapping, root, build_inputs)
    else:
        raise RuntimeError("complete PDF build receipt has no transitive input inventory")
    html_manifest = documents["html_manifest"]
    add_records(mapping, root, html_manifest.get("inputs", []))
    for media in html_manifest.get("media", []):
        if isinstance(media, dict):
            add_records(mapping, root, [media.get("source")])
    for media in html_manifest.get("source_linked_media", []):
        if isinstance(media, dict):
            add_records(mapping, root, [media.get("source")])
    backend_inputs = documents["backend_manifest"].get("inputs")
    if not isinstance(backend_inputs, dict):
        raise RuntimeError("complete backend manifest input inventory is absent")
    add_records(mapping, root, backend_inputs.values())
    for relative in (BUILD_QA_REL, PDF_STRUCTURAL_QA_REL, DRIVER_QA_REL, HTML_READER_QA_REL, HTML_BROWSER_QA_REL, BACKEND_QA_REL):
        B.add_mapping(mapping, relative, B.project_path(root, relative))

    records_path = B.project_path(root, "backend/records.jsonl")
    for number, line in enumerate(records_path.read_text(encoding="utf-8").splitlines(), 1):
        record = json.loads(line)
        if not isinstance(record, dict) or record.get("entity_type") != "asset":
            continue
        relative = record.get("path")
        if not isinstance(relative, str) or not relative:
            raise RuntimeError(f"backend asset lacks a path at line {number}")
        source = B.project_path(root, relative)
        actual = B.identity(source)
        if actual["bytes"] != record.get("expected_bytes") or actual["sha256"] != record.get("source_sha256"):
            raise RuntimeError(f"backend asset identity is stale: {relative}")
        B.add_mapping(mapping, relative, source)

    for archive_name, source in sorted(mapping.items()):
        destination = staging.joinpath(*PurePosixPath(archive_name).parts)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        if B.identity(destination) != B.identity(source):
            raise RuntimeError(f"copy identity mismatch: {archive_name}")
    privacy = B.privacy_scan_files((name, staging.joinpath(*PurePosixPath(name).parts)) for name in sorted(mapping))
    rows = [{"path": name, **B.identity(staging.joinpath(*PurePosixPath(name).parts))} for name in sorted(mapping)]
    tree_sha256 = hashlib.sha256("".join(f"{row['path']}\0{row['bytes']}\0{row['sha256']}\n" for row in rows).encode("utf-8")).hexdigest()
    backend_manifest = documents["backend_manifest"]
    checkpoint = backend_manifest.get("checkpoint")
    state = backend_manifest.get("translation_state")
    if not isinstance(checkpoint, str) or not checkpoint or not isinstance(state, str) or not state:
        raise RuntimeError("complete backend manifest lacks checkpoint/translation state")
    package_manifest = {
        "schema_version": 1,
        "workflow": "o011-complete-compact-source-backend-package-v1",
        "status": "complete_edition",
        "coverage": "29 core lecture/worksheet pairs, ten exam forms, two original bridges, and six original exam repairs",
        "model_identification": MODEL,
        "reader_and_backend_bindings": gate,
        "rebuild_commands": [
            "pwsh -NoProfile -File scripts/build_complete_reader.ps1",
            "python scripts/verify_complete_reader.py",
            "python scripts/export_html_complete.py --root . --output output/html/complete --replace",
            "python scripts/verify_html_complete.py --root . --output output/html/complete",
            f"python scripts/export_backend_complete.py --root . --checkpoint {checkpoint} --translation-state {state}",
            "python scripts/verify_backend_complete.py --root . --check-only",
        ],
        "files_excluding_manifest_surfaces": len(rows),
        "bytes_excluding_manifest_surfaces": sum(int(row["bytes"]) for row in rows),
        "tree_sha256": tree_sha256,
        "files": rows,
        "deliberate_exclusions": [
            "complete PDF and semantic HTML reader, published separately as the first two files",
            "raw MediaWiki/XML dumps and bulk provenance export trees",
            "temporary renders, contact sheets, diagnostics, caches, and TeX auxiliaries",
            "private locators, credentials, and remote-publication receipts other than the public predecessor proof",
            "duplicate generated build trees not required by bound rebuild inputs",
        ],
    }
    (staging / "PACKAGE_MANIFEST.json").write_bytes(B.json_bytes(package_manifest))
    checksum_files = sorted((path for path in staging.rglob("*") if path.is_file()), key=lambda path: path.relative_to(staging).as_posix())
    (staging / "PACKAGE_CHECKSUMS.sha256").write_text("".join(f"{B.sha256(path)}  {path.relative_to(staging).as_posix()}\n" for path in checksum_files), encoding="utf-8", newline="\n")
    B.scan_bytes("PACKAGE_MANIFEST.json", (staging / "PACKAGE_MANIFEST.json").read_bytes())
    B.scan_bytes("PACKAGE_CHECKSUMS.sha256", (staging / "PACKAGE_CHECKSUMS.sha256").read_bytes())
    return {
        "files": len([path for path in staging.rglob("*") if path.is_file()]),
        "uncompressed_bytes": sum(path.stat().st_size for path in staging.rglob("*") if path.is_file()),
        "tree_sha256": tree_sha256,
        "privacy_scan": privacy,
    }


def write_public_manifest(release: Path) -> None:
    rows = [{"path": name, **B.identity(release / name)} for name in PUBLIC_FILE_ORDER[:5]]
    document = {
        "schema_version": 1,
        "workflow": "o011-complete-public-file-manifest-v1",
        "status": "complete_edition",
        "version": VERSION,
        "title": TITLE,
        "model_identification": MODEL,
        "public_file_order": list(PUBLIC_FILE_ORDER),
        "files": rows,
        "bytes_bound": sum(int(row["bytes"]) for row in rows),
    }
    (release / MANIFEST_NAME).write_bytes(B.json_bytes(document))
    (release / CHECKSUMS_NAME).write_text("".join(f"{B.sha256(release / name)}  {name}\n" for name in PUBLIC_FILE_ORDER[:6]), encoding="ascii", newline="\n")


def atomic_write_new(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp-complete-stage")
    if path.exists() or temporary.exists():
        raise RuntimeError(f"refusing to overwrite existing output: {path}")
    temporary.write_bytes(payload)
    os.replace(temporary, path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output-dir", type=Path, default=Path(DEFAULT_OUTPUT_REL))
    parser.add_argument("--receipt", type=Path, default=Path(DEFAULT_RECEIPT_REL))
    args = parser.parse_args()
    root = args.root.resolve()
    output_dir = B.resolve_output(root, args.output_dir)
    receipt_path = B.resolve_output(root, args.receipt)
    metadata_path = B.project_path(root, METADATA_REL)
    gate, documents = collect_gate(root)
    validate_metadata(B.load_json(metadata_path))
    if output_dir.exists() or receipt_path.exists():
        raise RuntimeError("refusing to overwrite existing complete-release directory or receipt")
    output_dir.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="complete-release-stage-", dir=output_dir.parent) as temporary_name:
        temporary_root = Path(temporary_name)
        release, source_tree = temporary_root / "release", temporary_root / "source-package"
        release.mkdir()
        source_tree.mkdir()
        shutil.copyfile(B.project_path(root, PDF_REL), release / PDF_NAME)
        shutil.copyfile(B.project_path(root, LICENSE_SOURCE_REL), release / LICENSE_NAME)
        shutil.copyfile(B.project_path(root, NOTES_SOURCE_REL), release / NOTES_NAME)

        html_mapping = B.directory_mapping(root / HTML_ROOT_REL)
        html_archive = release / HTML_ZIP_NAME
        B.create_zip(html_mapping, html_archive)
        html_zip = B.verify_zip(html_mapping, html_archive)
        html_zip["reproducible_second_serialization"] = B.verify_reproducible(html_mapping, html_archive, temporary_root)
        source_summary = copy_source_tree(root, source_tree, documents, gate)
        source_mapping = B.directory_mapping(source_tree)
        source_archive = release / SOURCE_ZIP_NAME
        B.create_zip(source_mapping, source_archive)
        source_zip = B.verify_zip(source_mapping, source_archive)
        source_zip["reproducible_second_serialization"] = B.verify_reproducible(source_mapping, source_archive, temporary_root)

        write_public_manifest(release)
        public_files = B.verify_public_surfaces(release, root / LICENSE_SOURCE_REL)
        privacy = B.privacy_scan_files((str(item["path"]), release / str(item["path"])) for item in public_files)
        public_bytes = sum(int(item["bytes"]) for item in public_files)
        if public_bytes > MAX_PUBLIC_BYTES:
            raise RuntimeError(f"public release exceeds {MAX_PUBLIC_BYTES}-byte cap")
        receipt = {
            "schema_version": 1,
            "workflow": "o011-prepare-release-complete-v1",
            "status": "pass",
            "release_date": RELEASE_DATE,
            "version": VERSION,
            "coverage": "complete_edition",
            "model_identification": MODEL,
            "lineage": {"concept_record_id": CONCEPT_RECORD_ID, "predecessor_record_id": PREDECESSOR_RECORD_ID, "new_concept_created": False},
            "public_directory": output_dir.relative_to(root).as_posix(),
            "public_file_count": len(public_files),
            "public_file_order": list(PUBLIC_FILE_ORDER),
            "public_bytes": public_bytes,
            "total_public_bytes": public_bytes,
            "maximum_public_bytes": MAX_PUBLIC_BYTES,
            "under_500000000_bytes": True,
            "public_files": public_files,
            "files": [{"filename": str(item["path"]), "bytes": int(item["bytes"]), "sha256": str(item["sha256"]), "md5": B.md5(release / str(item["path"]))} for item in public_files],
            "metadata": B.identity(metadata_path, METADATA_REL),
            "input_bindings": gate,
            "zip_verification": {"html": html_zip, "source": source_zip},
            "source_package": source_summary,
            "manifest_contract": {"file_manifest_rows": list(PUBLIC_FILE_ORDER[:5]), "checksum_rows": list(PUBLIC_FILE_ORDER[:6]), "receipt_binds_all_seven_public_files": True},
            "rights": {"text_and_adaptation": "CC BY-SA 4.0", "component_media": "file-specific rights retained in component ledger and reader attribution", "non_endorsement_preserved": True, "license_byte_identical_to": LICENSE_SOURCE_REL},
            "privacy_scan": {"status": "pass", **privacy},
            "deterministic_archives": {"status": "pass", "html": html_zip, "source": source_zip},
            "deterministic_zip_timestamp": list(ZIP_TIMESTAMP),
            "excluded": ["raw provenance dumps and caches", "private locators and credentials", "temporary renders, contact sheets, diagnostics, and duplicate builds", "remote publication receipts not required for predecessor proof"],
            "remote_state_mutated": False,
        }
        payload = B.json_bytes(receipt)
        B.scan_bytes("complete release-preparation receipt", payload)
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        staged_receipt = receipt_path.with_name(receipt_path.name + ".tmp-complete-stage")
        if staged_receipt.exists():
            raise RuntimeError(f"refusing to overwrite existing staged receipt: {staged_receipt}")
        staged_receipt.write_bytes(payload)
        try:
            release.rename(output_dir)
            os.replace(staged_receipt, receipt_path)
        except Exception:
            if output_dir.exists() and not release.exists():
                output_dir.rename(release)
            if staged_receipt.exists():
                staged_receipt.unlink()
            raise
    print(json.dumps({"status": "pass", "public_directory": output_dir.relative_to(root).as_posix(), "public_files": 7, "public_bytes": public_bytes, "metadata": METADATA_REL, "receipt": receipt_path.relative_to(root).as_posix(), "remote_state_mutated": False}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
