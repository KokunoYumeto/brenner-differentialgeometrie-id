#!/usr/bin/env python3
"""Stage the deterministic seven-file, reader-first Unit 22 checkpoint.

This is a narrow Unit 22 adaptation of ``stage_zenodo_unit19.py``.  It reuses
the hardened ZIP, privacy, path-safety, and hash-binding helpers while applying
the current Unit 22 PDF/HTML/backend contracts.  It mutates no remote state.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import tempfile
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any


def load_unit19() -> Any:
    path = Path(__file__).resolve().with_name("stage_zenodo_unit19.py")
    spec = importlib.util.spec_from_file_location("o011_stage_unit19_base", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load the hardened Unit 19 release stager")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


B = load_unit19()

RELEASE_DATE = "2026-08-28"
VERSION = "2026.08.28-unit22"
TITLE = "Geometri Diferensial dan Manifold Mulus — Edisi Bahasa Indonesia (Batas Unit 22)"
ZIP_TIMESTAMP = (2026, 8, 28, 0, 0, 0)
MODEL = "OpenAI Codex gpt-5.6-sol, Ultra"
MAX_PUBLIC_BYTES = 500_000_000
PREDECESSOR_RECORD_ID = 22134954
CONCEPT_RECORD_ID = 22059977

PDF_REL = "output/pdf/geometri-diferensial-manifold-mulus-hingga-unit-22-id.pdf"
HTML_ROOT_REL = "output/html/unit-22"
HTML_ENTRY_REL = f"{HTML_ROOT_REL}/index.html"
HTML_MANIFEST_REL = f"{HTML_ROOT_REL}/manifest.json"
BUILD_QA_REL = "qa/unit-22/build.json"
PDF_STRUCTURAL_QA_REL = "qa/unit-22/pdf_structural_qa.json"
PDF_VISUAL_QA_REL = "qa/unit-22/PDF_VISUAL_QA.json"
HTML_READER_QA_REL = "qa/unit-22/HTML_READER_QA.json"
HTML_BROWSER_QA_REL = "qa/unit-22/HTML_BROWSER_QA.json"
BACKEND_MANIFEST_REL = "backend/MANIFEST.json"
BACKEND_QA_REL = "qa/unit-22/backend.json"
LICENSE_SOURCE_REL = "qa/unit-22/LICENSE_RELEASE_UNIT22.md"
README_SOURCE_REL = "qa/unit-22/PACKAGE_README.md"
NOTES_SOURCE_REL = "qa/unit-22/RELEASE_NOTES_20260828.md"
METADATA_REL = "qa/unit-22/ZENODO_METADATA_UNIT22.json"

PDF_NAME = "geometri-diferensial-manifold-mulus-hingga-unit-22-id.pdf"
HTML_ZIP_NAME = "geometri-diferensial-manifold-mulus-unit22-html-20260828.zip"
SOURCE_ZIP_NAME = "geometri-diferensial-manifold-mulus-unit22-source-20260828.zip"
LICENSE_NAME = "LICENSE.md"
NOTES_NAME = "RELEASE_NOTES_UNIT22_20260828.md"
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
DEFAULT_OUTPUT_REL = "output/release-unit22"
DEFAULT_RECEIPT_REL = "qa/unit-22/RELEASE_PREPARATION_RECEIPT.json"

CONTROL_PUBLIC_PATHS = B.CONTROL_PUBLIC_PATHS
AUTHORITY_LEDGER_PATHS = B.AUTHORITY_LEDGER_PATHS
FIXED_SUPPORT_PATHS = (
    "source/unit_media.json",
    "source/unit07_interactive_media.json",
    "source/unit11_interactive_media.json",
    "authority/expanded/script_preamble_source.de.tex",
    "build/brenner-compat.tex",
    "build/through-unit-10.tex",
    "build/generated/through-unit-19-driver.tex",
    "build/generated/through-unit-22-driver.tex",
)
HTML_GENERATION_BINDING_PATHS = (
    *(f"qa/unit-{unit:02d}_media.json" for unit in range(1, 23)),
    "qa/unit-07/INTERACTIVE_MEDIA_QA.json",
    "qa/unit-11/INTERACTIVE_MEDIA_QA.json",
    "qa/unit-12/ANIMATED_MEDIA_QA.json",
    "qa/unit-12/HTML_ANIMATED_MEDIA_QA.json",
    "qa/unit-18/ANIMATED_MEDIA_QA.json",
)
SCRIPT_PATHS = (
    "scripts/build_through_unit10.ps1",
    "scripts/build_through_unit19.ps1",
    "scripts/build_through_unit22.ps1",
    "scripts/export_backend_v10.py",
    "scripts/export_backend_v19.py",
    "scripts/export_backend_v22.py",
    "scripts/export_html_v10.py",
    "scripts/export_html_v13.py",
    "scripts/export_html_v19.py",
    "scripts/export_html_v22.py",
    "scripts/prepare_unit_media.py",
    "scripts/prepare_unit_tex.py",
    "scripts/stage_zenodo_unit19.py",
    "scripts/stage_zenodo_unit22.py",
    "scripts/test_html_v19_pipeline.py",
    "scripts/verify_backend_v10.py",
    "scripts/verify_backend_v19.py",
    "scripts/verify_backend_v22.py",
    "scripts/verify_html_animated_media.py",
    "scripts/verify_html_v10.py",
    "scripts/verify_html_v13.py",
    "scripts/verify_html_v19.py",
    "scripts/verify_html_v22.py",
    "scripts/verify_source_package_unit13_r1.py",
    "scripts/verify_source_package_unit19.py",
    "scripts/verify_source_package_unit22.py",
    "scripts/verify_through_unit06_pdf.py",
    "scripts/verify_through_unit10_pdf.py",
    "scripts/verify_through_unit13_pdf.py",
    "scripts/verify_through_unit19_pdf.py",
    "scripts/verify_through_unit22_pdf.py",
    "scripts/verify_unit_translation.py",
)
BACKEND_PATHS = B.BACKEND_PATHS
ESSENTIAL_QA_PATHS = (
    *B.ESSENTIAL_QA_PATHS,
    "qa/unit-20/POST_CORRECTION_MATH_QA.json",
    "qa/unit-21/POST_CORRECTION_MATH_QA.json",
    "qa/unit-22/AUTHORITY_PREFLIGHT.json",
    "qa/unit-22/AUTHORITY_PREFLIGHT_VERIFY.json",
    "qa/unit-22/HTML_BROWSER_QA.json",
    "qa/unit-22/HTML_READER_QA.json",
    "qa/unit-22/MEDIA_ALIAS_RECEIPT.json",
    "qa/unit-22/PDF_VISUAL_QA.json",
    "qa/unit-22/POST_CORRECTION_MATH_QA.json",
    "qa/unit-22/POST_CORRECTION_MATH_QA_VERIFY.json",
    "qa/unit-22/UNIT10_PREFIX_PRESERVATION_RECEIPT.json",
    "qa/unit-22/WRAPPER_DERIVATION_RECEIPT.json",
    "qa/unit-22/backend.json",
    "qa/unit-22/build.json",
    "qa/unit-22/pdf_structural_qa.json",
    "qa/unit-22/solution_closure.json",
    METADATA_REL,
)
PREDECESSOR_FILES = (
    *B.PREDECESSOR_FILES,
    "output/pdf/geometri-diferensial-manifold-mulus-hingga-unit-19-id.pdf",
    "qa/unit-19/build.json",
    "qa/unit-19/pdf_structural_qa.json",
    "qa/unit-19/HTML_READER_QA.json",
)
PREDECESSOR_TREES = (
    *B.PREDECESSOR_TREES,
    "output/html/unit-19",
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
        "PDF_VISUAL_QA_REL": PDF_VISUAL_QA_REL,
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
        "CONTROL_PUBLIC_PATHS": CONTROL_PUBLIC_PATHS,
        "AUTHORITY_LEDGER_PATHS": AUTHORITY_LEDGER_PATHS,
        "FIXED_SUPPORT_PATHS": FIXED_SUPPORT_PATHS,
        "HTML_GENERATION_BINDING_PATHS": HTML_GENERATION_BINDING_PATHS,
        "SCRIPT_PATHS": SCRIPT_PATHS,
        "BACKEND_PATHS": BACKEND_PATHS,
        "ESSENTIAL_QA_PATHS": ESSENTIAL_QA_PATHS,
        "PREDECESSOR_FILES": PREDECESSOR_FILES,
        "PREDECESSOR_TREES": PREDECESSOR_TREES,
    }
    for name, value in values.items():
        setattr(B, name, value)


patch_base_globals()


def verify_durable_controls(root: Path, gate: dict[str, Any]) -> dict[str, Any]:
    state_path = B.project_path(root, "00_control/CURRENT_STATE.md")
    cursor_path = B.project_path(root, "00_control/CURSOR.json")
    decision_path = B.project_path(root, "00_control/DECISION_LOG.md")
    combined = "\n".join(path.read_text(encoding="utf-8") for path in (state_path, cursor_path, decision_path))
    required = (
        str(gate["pdf"]["sha256"]),
        str(gate["html_entry"]["sha256"]),
        str(gate["backend_records_jsonl"]["sha256"]),
        str(gate["coverage"]["backend_records"]),
    )
    missing = [token for token in required if token not in combined]
    if missing:
        raise RuntimeError(f"durable controls do not bind finalized Unit 22 checkpoint: {missing}")
    lowered = combined.lower()
    if "unit 23" not in lowered and "unit_23" not in lowered and "u23" not in lowered:
        raise RuntimeError("durable controls do not record Unit 23 as the next production action")
    return {
        "current_state": B.identity(state_path, "00_control/CURRENT_STATE.md"),
        "cursor": B.identity(cursor_path, "00_control/CURSOR.json"),
        "decision_log": B.identity(decision_path, "00_control/DECISION_LOG.md"),
        "unit23_next_action_recorded": True,
    }


def collect_gate(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    paths = {
        "pdf": PDF_REL,
        "build_qa": BUILD_QA_REL,
        "pdf_structural_qa": PDF_STRUCTURAL_QA_REL,
        "pdf_visual_qa": PDF_VISUAL_QA_REL,
        "html_entry": HTML_ENTRY_REL,
        "html_manifest": HTML_MANIFEST_REL,
        "html_reader_qa": HTML_READER_QA_REL,
        "html_browser_qa": HTML_BROWSER_QA_REL,
        "backend_manifest": BACKEND_MANIFEST_REL,
        "backend_qa": BACKEND_QA_REL,
        "metadata": METADATA_REL,
    }
    current = {name: B.identity(B.project_path(root, rel), rel) for name, rel in paths.items()}
    build = B.load_json(root / BUILD_QA_REL)
    structural = B.load_json(root / PDF_STRUCTURAL_QA_REL)
    visual = B.load_json(root / PDF_VISUAL_QA_REL)
    html_manifest = B.load_json(root / HTML_MANIFEST_REL)
    html_qa = B.load_json(root / HTML_READER_QA_REL)
    html_browser = B.load_json(root / HTML_BROWSER_QA_REL)
    backend_manifest = B.load_json(root / BACKEND_MANIFEST_REL)
    backend_qa = B.load_json(root / BACKEND_QA_REL)

    if build.get("workflow") != "o011-through-unit22-pdf-build-v1" or build.get("deterministic_clean_cycles") is not True:
        raise RuntimeError("Unit 22 PDF build receipt is not the settled deterministic workflow")
    B.assert_record(root, build.get("output"), PDF_REL)
    cycles = build.get("cycles")
    if not isinstance(cycles, list) or len(cycles) != 2 or any(cycle.get("sha256") != current["pdf"]["sha256"] for cycle in cycles):
        raise RuntimeError("PDF receipt does not prove two byte-identical cycles")
    if structural.get("passed") is not True:
        raise RuntimeError("PDF structural QA has not passed")
    B.assert_record(root, structural.get("pdf"), PDF_REL)
    B.require_bound(structural, current["build_qa"], "PDF structural QA")
    if visual.get("status") != "pass" or not B.all_true(visual.get("checks")):
        raise RuntimeError("PDF visual QA has not passed every check")
    B.assert_record(root, visual.get("surface"), PDF_REL)
    if visual["surface"].get("build_receipt_sha256") != current["build_qa"]["sha256"]:
        raise RuntimeError("PDF visual QA does not bind the current build receipt")

    if html_manifest.get("workflow") != "o011-export-html-v22" or html_manifest.get("model_identification") != MODEL:
        raise RuntimeError("HTML manifest workflow/model contract differs")
    if html_manifest.get("text_license") != "CC BY-SA 4.0" or html_manifest.get("non_endorsement") is not True:
        raise RuntimeError("HTML rights/non-endorsement contract differs")
    if html_qa.get("status") != "pass" or not B.all_true(html_qa.get("checks")):
        raise RuntimeError("HTML structural QA has not passed")
    B.assert_record(root, html_qa.get("entry"), HTML_ENTRY_REL)
    B.assert_record(root, html_qa.get("manifest"), HTML_MANIFEST_REL)
    counts = html_qa.get("counts", {})
    if counts.get("units") != 22 or counts.get("exercises") != 457 or counts.get("source_supplied_solutions") != 64:
        raise RuntimeError("HTML Unit/exercise/solution census differs")
    if html_browser.get("status") != "pass" or not B.all_true(html_browser.get("checks")):
        raise RuntimeError("HTML browser QA has not passed")
    for name in ("html_entry", "html_manifest", "html_reader_qa"):
        B.require_bound(html_browser.get("surface"), current[name], "HTML browser QA")
    html_tree = B.verify_html_tree(root, html_manifest, html_qa)

    if backend_manifest.get("workflow") != "o011-export-backend-v22":
        raise RuntimeError("backend manifest workflow differs")
    if not isinstance(backend_manifest.get("claims"), dict) or not B.all_true(backend_manifest["claims"]):
        raise RuntimeError("backend manifest claims are incomplete")
    combined = backend_manifest.get("combined") or {}
    if combined.get("record_count") != 4324 or (combined.get("entity_counts") or {}).get("correction") != 282:
        raise RuntimeError("backend cumulative record/correction census differs")
    extension = backend_manifest.get("units20_22_extension") or {}
    if extension.get("record_count") != 577 or extension.get("exercise_count") != 63 or extension.get("source_supplied_solution_count") != 10:
        raise RuntimeError("backend Unit 20--22 extension census differs")
    if backend_qa.get("status") != "pass" or not B.all_true(backend_qa.get("checks")):
        raise RuntimeError("backend verifier has not passed")
    if backend_qa.get("combined_records") != 4324 or backend_qa.get("determinism", {}).get("second_export_matches_first") is not True:
        raise RuntimeError("backend verifier count/determinism contract differs")
    backend_outputs: dict[str, dict[str, int | str]] = {}
    for key, relative in (("records_csv", "backend/records.csv"), ("records_jsonl", "backend/records.jsonl")):
        backend_outputs[key] = B.assert_record(root, backend_qa.get("outputs", {}).get(key), relative)
        B.assert_record(root, backend_manifest.get("outputs", {}).get(key), relative)
    B.assert_record(root, backend_qa.get("outputs", {}).get("manifest"), BACKEND_MANIFEST_REL)

    pages = (structural.get("pdf") or {}).get("pages")
    if pages != 345:
        raise RuntimeError("canonical Unit 22 PDF page count differs")
    gate = {
        **current,
        "backend_records_csv": backend_outputs["records_csv"],
        "backend_records_jsonl": backend_outputs["records_jsonl"],
        "html_tree": html_tree,
        "coverage": {
            "units": 22,
            "exercises": 457,
            "source_supplied_solutions": 64,
            "backend_records": 4324,
            "backend_corrections": 282,
            "pdf_pages": pages,
        },
    }
    gate["durable_controls"] = verify_durable_controls(root, gate)
    return gate, {"build": build, "html_manifest": html_manifest, "backend_manifest": backend_manifest}


def validate_metadata(document: Any) -> None:
    if not isinstance(document, dict) or set(document) != {"metadata"} or not isinstance(document["metadata"], dict):
        raise RuntimeError("Zenodo metadata outer contract differs")
    metadata = document["metadata"]
    expected_keys = {"title", "description", "creators", "contributors", "license", "publication_date", "version", "language", "keywords", "related_identifiers"}
    if set(metadata) != expected_keys:
        raise RuntimeError("Zenodo metadata keys differ")
    if metadata["creators"] != [{"name": "Brenner, Holger"}] or metadata["contributors"] != [{"name": "TTP", "type": "Other"}]:
        raise RuntimeError("Zenodo creator/contributor contract differs")
    if metadata["license"] != "other-open" or metadata["language"] != "ind":
        raise RuntimeError("Zenodo rights/language contract differs")
    if metadata["publication_date"] != RELEASE_DATE or metadata["version"] != VERSION or metadata["title"] != TITLE:
        raise RuntimeError("Zenodo date/version/title contract differs")
    description = str(metadata["description"])
    for phrase in ("active_partial", "Kuliah 1–22", "Lembar Kerja 1–22", "345-page", "457 source exercises", "64 source-supplied solutions", "CC BY-SA 4.0", "Component media retain their file-specific rights; no blanket media license is inferred.", MODEL):
        if phrase not in description:
            raise RuntimeError(f"Zenodo description lacks required phrase: {phrase}")
    if "TTP" in metadata["title"] or "TTP" in description or "Translation and Transcription Project" in json.dumps(document, ensure_ascii=False):
        raise RuntimeError("umbrella organization label leaked outside its single contributor entry")
    if json.dumps(document, ensure_ascii=False).count("TTP") != 1:
        raise RuntimeError("metadata must contain exactly one organization-label occurrence")
    B.scan_bytes("Zenodo metadata", json.dumps(document, ensure_ascii=False, sort_keys=True).encode("utf-8"))


def copy_source_tree(root: Path, staging: Path, documents: dict[str, Any], gate: dict[str, Any]) -> dict[str, Any]:
    mapping: dict[str, Path] = {}
    B.add_mapping(mapping, "README.md", B.project_path(root, README_SOURCE_REL))
    B.add_mapping(mapping, "PACKAGE_README.md", B.project_path(root, README_SOURCE_REL))
    B.add_mapping(mapping, LICENSE_NAME, B.project_path(root, LICENSE_SOURCE_REL))
    B.add_mapping(mapping, NOTES_NAME, B.project_path(root, NOTES_SOURCE_REL))
    for relative in (*CONTROL_PUBLIC_PATHS, *AUTHORITY_LEDGER_PATHS, *FIXED_SUPPORT_PATHS, *HTML_GENERATION_BINDING_PATHS, *SCRIPT_PATHS, *BACKEND_PATHS, *ESSENTIAL_QA_PATHS, *PREDECESSOR_FILES):
        B.add_mapping(mapping, relative, B.project_path(root, relative))
    for relative in PREDECESSOR_TREES:
        B.add_tree(mapping, root, relative)

    build_inputs = documents["build"].get("inputs")
    if not isinstance(build_inputs, list) or not build_inputs:
        raise RuntimeError("build receipt has no transitive input inventory")
    for record in build_inputs:
        B.add_bound_record(mapping, root, record)
    html_manifest = documents["html_manifest"]
    for record in html_manifest.get("inputs", []):
        B.add_bound_record(mapping, root, record)
        relative = record["path"]
        target_name = PurePosixPath(relative).name
        if not target_name.endswith(".id.tex"):
            raise RuntimeError(f"unexpected translated source filename: {relative}")
        authority = "authority/expanded/" + target_name.removesuffix(".id.tex") + "_source.de.tex"
        B.add_mapping(mapping, authority, B.project_path(root, authority))
    for media in html_manifest.get("media", []):
        B.add_bound_record(mapping, root, media.get("source") if isinstance(media, dict) else None)
    for record in (documents["backend_manifest"].get("inputs") or {}).values():
        B.add_bound_record(mapping, root, record)

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
    units = (backend_manifest.get("units20_22_extension") or {}).get("units")
    states = {str(value.get("translation_state")) for value in units.values() if isinstance(value, dict)} if isinstance(units, dict) else set()
    if not isinstance(checkpoint, str) or not checkpoint or len(states) != 1:
        raise RuntimeError("backend manifest lacks one reproducible checkpoint/state contract")
    state = states.pop()
    package_manifest = {
        "schema_version": 1,
        "workflow": "o011-unit22-compact-source-package-v1",
        "status": "active_partial",
        "coverage": "Kuliah 1–22 dan Lembar Kerja 1–22 dari 29 pasangan inti",
        "model_identification": MODEL,
        "reader_and_backend_bindings": gate,
        "rebuild_commands": [
            "pwsh -NoProfile -File scripts/build_through_unit22.ps1",
            "python scripts/verify_through_unit22_pdf.py",
            "python scripts/export_html_v22.py --root . --output output/html/unit-22 --replace",
            "python scripts/verify_html_v22.py --root . --output output/html/unit-22",
            f"python scripts/export_backend_v22.py --root . --checkpoint {checkpoint} --translation-state {state}",
            "python scripts/verify_backend_v22.py --root .",
        ],
        "files_excluding_manifest_surfaces": len(rows),
        "bytes_excluding_manifest_surfaces": sum(int(row["bytes"]) for row in rows),
        "tree_sha256": tree_sha256,
        "files": rows,
        "deliberate_exclusions": [
            "Unit 22 PDF and semantic HTML reader, published separately as the first two files",
            "raw MediaWiki/XML dumps and bulk provenance export trees",
            "temporary page renders, contact sheets, diagnostics, caches, and TeX auxiliaries",
            "private locators, credentials, and remote-publication receipts",
            "duplicate generated build trees not required by the transitive build receipt",
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
        "workflow": "o011-unit22-public-file-manifest-v1",
        "status": "active_partial",
        "coverage": "Kuliah 1–22 dan Lembar Kerja 1–22 dari 29 pasangan inti",
        "model_identification": MODEL,
        "public_file_order": list(PUBLIC_FILE_ORDER),
        "files": rows,
        "bytes_bound": sum(int(row["bytes"]) for row in rows),
    }
    (release / MANIFEST_NAME).write_bytes(B.json_bytes(document))
    (release / CHECKSUMS_NAME).write_text("".join(f"{B.sha256(release / name)}  {name}\n" for name in PUBLIC_FILE_ORDER[:6]), encoding="ascii", newline="\n")


def atomic_write_new(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp-unit22-stage")
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
        raise RuntimeError("refusing to overwrite existing release directory or receipt")
    output_dir.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="unit22-release-stage-", dir=output_dir.parent) as temporary_name:
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
            "workflow": "o011-prepare-release-unit22-v1",
            "status": "pass",
            "release_date": RELEASE_DATE,
            "version": VERSION,
            "coverage": "active_partial_through_unit_22",
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
            "excluded": ["raw provenance dumps and caches", "private locators and credentials", "temporary page renders, contact sheets, diagnostics, and duplicate builds", "remote publication receipts not yet created"],
            "remote_state_mutated": False,
        }
        payload = B.json_bytes(receipt)
        B.scan_bytes("release-preparation receipt", payload)
        release.rename(output_dir)
        atomic_write_new(receipt_path, payload)
    print(json.dumps({"status": "pass", "public_directory": output_dir.relative_to(root).as_posix(), "public_files": 7, "public_bytes": public_bytes, "metadata": METADATA_REL, "receipt": receipt_path.relative_to(root).as_posix(), "remote_state_mutated": False}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
