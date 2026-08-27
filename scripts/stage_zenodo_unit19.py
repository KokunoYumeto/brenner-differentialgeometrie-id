#!/usr/bin/env python3
"""Stage the seven deterministic, reader-first Unit 19 release files.

This script mutates no remote state.  It refuses to stage until the current
PDF, HTML, backend, and durable-control surfaces form one hash-bound Unit 19
checkpoint.  The source ZIP includes the compact transitive closure needed for
clean reconstruction while excluding credentials, private locators, renders,
caches, raw dumps, and remote-publication receipts.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import shutil
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any, Iterable


RELEASE_DATE = "2026-08-26"
VERSION = "2026.08.26-unit19"
TITLE = "Geometri Diferensial dan Manifold Mulus — Edisi Bahasa Indonesia (Batas Unit 19)"
ZIP_TIMESTAMP = (2026, 8, 26, 0, 0, 0)
MODEL = "OpenAI Codex gpt-5.6-sol, Ultra"
MAX_PUBLIC_BYTES = 500_000_000
PREDECESSOR_RECORD_ID = 22104426
CONCEPT_RECORD_ID = 22059977

PDF_REL = "output/pdf/geometri-diferensial-manifold-mulus-hingga-unit-19-id.pdf"
HTML_ROOT_REL = "output/html/unit-19"
HTML_ENTRY_REL = f"{HTML_ROOT_REL}/index.html"
HTML_MANIFEST_REL = f"{HTML_ROOT_REL}/manifest.json"
BUILD_QA_REL = "qa/unit-19/build.json"
PDF_STRUCTURAL_QA_REL = "qa/unit-19/pdf_structural_qa.json"
PDF_VISUAL_QA_REL = "qa/unit-19/PDF_VISUAL_QA.json"
HTML_READER_QA_REL = "qa/unit-19/HTML_READER_QA.json"
HTML_BROWSER_QA_REL = "qa/unit-19/HTML_BROWSER_QA.json"
BACKEND_MANIFEST_REL = "backend/MANIFEST.json"
BACKEND_QA_REL = "qa/unit-19/backend.json"
LICENSE_SOURCE_REL = "qa/unit-19/LICENSE_RELEASE_UNIT19.md"
README_SOURCE_REL = "qa/unit-19/PACKAGE_README.md"
NOTES_SOURCE_REL = "qa/unit-19/RELEASE_NOTES_20260826.md"
METADATA_REL = "qa/unit-19/ZENODO_METADATA_UNIT19.json"

PDF_NAME = "geometri-diferensial-manifold-mulus-hingga-unit-19-id.pdf"
HTML_ZIP_NAME = "geometri-diferensial-manifold-mulus-unit19-html-20260826.zip"
SOURCE_ZIP_NAME = "geometri-diferensial-manifold-mulus-unit19-source-20260826.zip"
LICENSE_NAME = "LICENSE.md"
NOTES_NAME = "RELEASE_NOTES_UNIT19_20260826.md"
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

DEFAULT_OUTPUT_REL = "output/release-unit19"
DEFAULT_RECEIPT_REL = "qa/unit-19/RELEASE_PREPARATION_RECEIPT.json"

CONTROL_PUBLIC_PATHS = (
    "00_control/GOAL_AND_WORKFLOW.md",
    "00_control/CURRENT_STATE.md",
    "00_control/CURSOR.json",
    "00_control/DECISION_LOG.md",
    "00_control/AUTHORITY_FREEZE.md",
    "00_control/SCOPE_AND_OVERLAP.md",
    "00_control/TERMINOLOGY.csv",
    "00_control/ADVERSE_LEDGER.csv",
)

AUTHORITY_LEDGER_PATHS = (
    "authority/brenner_94_link_classification.csv",
    "authority/brenner_export_and_title_inventory_receipt.txt",
    "authority/brenner_media_rights_manifest.csv",
    "authority/brenner_selected_root_revisions.csv",
    "authority/brenner_selected_surface_revisions.csv",
)

FIXED_SUPPORT_PATHS = (
    "source/unit_media.json",
    "source/unit07_interactive_media.json",
    "source/unit11_interactive_media.json",
    "authority/expanded/script_preamble_source.de.tex",
    "build/brenner-compat.tex",
    "build/through-unit-10.tex",
    "build/generated/through-unit-19-driver.tex",
)

HTML_GENERATION_BINDING_PATHS = (
    *(f"qa/unit-{unit:02d}_media.json" for unit in range(1, 20)),
    "qa/unit-07/INTERACTIVE_MEDIA_QA.json",
    "qa/unit-11/INTERACTIVE_MEDIA_QA.json",
    "qa/unit-12/ANIMATED_MEDIA_QA.json",
    "qa/unit-12/HTML_ANIMATED_MEDIA_QA.json",
    "qa/unit-18/ANIMATED_MEDIA_QA.json",
)

SCRIPT_PATHS = (
    "scripts/build_through_unit10.ps1",
    "scripts/build_through_unit19.ps1",
    "scripts/export_backend_v10.py",
    "scripts/export_backend_v19.py",
    "scripts/export_html_v10.py",
    "scripts/export_html_v13.py",
    "scripts/export_html_v19.py",
    "scripts/prepare_unit_media.py",
    "scripts/prepare_unit_tex.py",
    "scripts/stage_zenodo_unit19.py",
    "scripts/test_html_v19_pipeline.py",
    "scripts/verify_backend_v10.py",
    "scripts/verify_backend_v19.py",
    "scripts/verify_html_animated_media.py",
    "scripts/verify_html_v10.py",
    "scripts/verify_html_v13.py",
    "scripts/verify_html_v19.py",
    "scripts/verify_source_package_unit13_r1.py",
    "scripts/verify_source_package_unit19.py",
    "scripts/verify_through_unit06_pdf.py",
    "scripts/verify_through_unit10_pdf.py",
    "scripts/verify_through_unit13_pdf.py",
    "scripts/verify_through_unit19_pdf.py",
    "scripts/verify_unit_translation.py",
)

BACKEND_PATHS = (
    "backend/MANIFEST.json",
    "backend/records.csv",
    "backend/records.jsonl",
    "backend/schema/o011-record-v1.schema.json",
)

ESSENTIAL_QA_PATHS = (
    "qa/unit-10/HTML_READER_QA.json",
    "qa/unit-10/ZENODO_PUBLIC_READBACK_RECEIPT.json",
    "qa/unit-13/HTML_READER_QA.json",
    "qa/unit-13/ZENODO_PUBLIC_READBACK_RECEIPT_R1.json",
    "qa/unit-13/GITHUB_PUBLIC_READBACK_RECEIPT_R1.json",
    "qa/unit-19/AUTHORITY_PREFLIGHT.json",
    "qa/unit-19/AUTHORITY_PREFLIGHT_VERIFY.json",
    "qa/unit-19/HTML_BROWSER_QA.json",
    "qa/unit-19/HTML_READER_QA.json",
    "qa/unit-19/MEDIA_ALIAS_RECEIPT.json",
    "qa/unit-19/PDF_VISUAL_QA.json",
    "qa/unit-19/POST_CORRECTION_MATH_QA.json",
    "qa/unit-19/UNIT10_PREFIX_PRESERVATION_RECEIPT.json",
    "qa/unit-19/WRAPPER_DERIVATION_RECEIPT.json",
    "qa/unit-19/backend.json",
    "qa/unit-19/build.json",
    "qa/unit-19/pdf_structural_qa.json",
    "qa/unit-19/solution_closure.json",
    "qa/unit-19/ZENODO_METADATA_UNIT19.json",
)

PREDECESSOR_FILES = (
    "output/pdf/geometri-diferensial-manifold-mulus-hingga-unit-10-id.pdf",
    "output/release-unit13-r1/geometri-diferensial-manifold-mulus-brenner-id-unit13-html-20260825.zip",
    "qa/unit-13/HTML_BROWSER_QA.json",
    "qa/unit-13/PDF_VISUAL_QA.json",
)

PREDECESSOR_TREES = (
    "output/html/unit-10",
    "output/html/unit-13",
    "output/release-unit10",
    # The PDF driver consumes the deterministic prepared TeX surfaces
    # directly.  They are small, public-safe, and required for an offline
    # clean build; include the complete current generated-input closure.
    "build/generated",
)

TEXT_SUFFIXES = {
    "", ".csv", ".css", ".html", ".json", ".jsonl", ".md", ".ps1",
    ".py", ".svg", ".tex", ".txt",
}
PRIVATE_PATTERNS = (
    re.compile(rb"[A-Za-z]:[\\/]+Users[\\/]", re.I),
    re.compile(rb"(?<!:)\/Users\/", re.I),
    re.compile(rb"(?<!:)\/home\/[^\/\x00\r\n]+\/", re.I),
    re.compile(rb"\\\\[^\\\r\n]+\\Users\\", re.I),
)
ADMITTED_PUBLIC_UPSTREAM_LOCATORS = (
    b"/home/aoleg/diverse/wiki",
    b"/home/.../diverse/wiki",
)
SECRET_PATTERNS = (
    re.compile(rb"github_pat_[A-Za-z0-9_]{40,}"),
    re.compile(rb"gh[pousr]_[A-Za-z0-9]{36,}"),
    re.compile(
        rb"(?:access[_-]?token|api[_-]?token|password|secret)\s*[:=]\s*[\"'][^\"'\r\n]{16,}[\"']",
        re.I,
    ),
)
FORBIDDEN_PACKAGE_PATHS = {
    "00_control/PRIVATE_LOCAL_LOCATORS.md",
    "qa/unit-05/ZENODO_PUBLICATION_RECEIPT.md",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def md5(path: Path) -> str:
    digest = hashlib.md5()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def identity(path: Path, label: str | None = None) -> dict[str, int | str]:
    result: dict[str, int | str] = {"bytes": path.stat().st_size, "sha256": sha256(path)}
    return {"path": label, **result} if label is not None else result


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"cannot load required JSON {path}: {exc}") from exc


def safe_relative(value: str) -> PurePosixPath:
    parsed = PurePosixPath(value)
    if parsed.is_absolute() or ".." in parsed.parts or "\\" in value or ":" in value:
        raise RuntimeError(f"unsafe project-relative path: {value}")
    return parsed


def project_path(root: Path, relative: str) -> Path:
    path = root.joinpath(*safe_relative(relative).parts)
    if not path.is_file():
        raise RuntimeError(f"required file is missing: {relative}")
    return path


def resolve_output(root: Path, value: Path) -> Path:
    path = (value if value.is_absolute() else root / value).resolve()
    if path != root and root not in path.parents:
        raise RuntimeError(f"output must remain inside project root: {path}")
    return path


def assert_record(root: Path, record: Any, expected_path: str) -> dict[str, int | str]:
    if not isinstance(record, dict) or record.get("path") != expected_path:
        raise RuntimeError(f"missing or mismatched identity record for {expected_path}")
    actual = identity(project_path(root, expected_path), expected_path)
    declared = {key: record.get(key) for key in ("path", "bytes", "sha256")}
    if declared != actual:
        raise RuntimeError(f"stale identity binding for {expected_path}: {declared} != {actual}")
    return actual


def contains_record(value: Any, expected: dict[str, int | str]) -> bool:
    if isinstance(value, dict):
        if all(value.get(key) == expected[key] for key in ("path", "bytes", "sha256")):
            return True
        return any(contains_record(item, expected) for item in value.values())
    if isinstance(value, list):
        return any(contains_record(item, expected) for item in value)
    return False


def require_bound(document: Any, expected: dict[str, int | str], surface: str) -> None:
    if not contains_record(document, expected):
        raise RuntimeError(f"{surface} does not bind current {expected['path']}")


def all_true(mapping: Any) -> bool:
    return isinstance(mapping, dict) and bool(mapping) and all(value is True for value in mapping.values())


def verify_html_tree(root: Path, manifest: dict[str, Any], qa: dict[str, Any]) -> dict[str, Any]:
    html_root = root / HTML_ROOT_REL
    if not html_root.is_dir():
        raise RuntimeError(f"semantic HTML directory is missing: {HTML_ROOT_REL}")
    records = manifest.get("files")
    if not isinstance(records, list) or not records:
        raise RuntimeError("HTML manifest has no file inventory")
    expected_names: set[str] = set()
    for record in records:
        relative = record.get("path") if isinstance(record, dict) else None
        if not isinstance(relative, str):
            raise RuntimeError("invalid HTML manifest file record")
        expected_names.add(relative)
        assert_record(root, {**record, "path": f"{HTML_ROOT_REL}/{relative}"}, f"{HTML_ROOT_REL}/{relative}")
    expected_names.add("manifest.json")
    actual_names = {
        path.relative_to(html_root).as_posix()
        for path in html_root.rglob("*")
        if path.is_file()
    }
    if actual_names != expected_names:
        raise RuntimeError(
            "HTML tree inventory mismatch: "
            + json.dumps({"missing": sorted(expected_names - actual_names), "unexpected": sorted(actual_names - expected_names)})
        )
    qa_records = qa.get("output_inventory")
    if not isinstance(qa_records, list) or len(qa_records) != len(expected_names):
        raise RuntimeError("HTML QA inventory is absent or incomplete")
    qa_names: set[str] = set()
    for record in qa_records:
        relative = record.get("path") if isinstance(record, dict) else None
        if not isinstance(relative, str) or not relative.startswith(f"{HTML_ROOT_REL}/"):
            raise RuntimeError("invalid HTML QA inventory record")
        qa_names.add(relative.removeprefix(f"{HTML_ROOT_REL}/"))
        assert_record(root, record, relative)
    if qa_names != expected_names:
        raise RuntimeError("HTML QA inventory differs from current HTML tree")
    return {
        "files": len(expected_names),
        "bytes": sum((html_root / name).stat().st_size for name in expected_names),
    }


def verify_durable_controls(root: Path, gate: dict[str, Any]) -> dict[str, Any]:
    state_path = project_path(root, "00_control/CURRENT_STATE.md")
    cursor_path = project_path(root, "00_control/CURSOR.json")
    decision_path = project_path(root, "00_control/DECISION_LOG.md")
    state = state_path.read_text(encoding="utf-8")
    cursor_text = cursor_path.read_text(encoding="utf-8")
    decision = decision_path.read_text(encoding="utf-8")
    required_tokens = (
        str(gate["pdf"]["sha256"]),
        str(gate["html_entry"]["sha256"]),
        str(gate["backend_records_jsonl"]["sha256"]),
        str(gate["coverage"]["backend_records"]),
    )
    combined = state + "\n" + cursor_text + "\n" + decision
    missing = [token for token in required_tokens if token not in combined]
    if missing:
        raise RuntimeError(f"durable controls do not yet bind the finalized Unit 19 checkpoint: {missing}")
    lowered = combined.lower()
    if "unit 20" not in lowered and "unit_20" not in lowered and "u20" not in lowered:
        raise RuntimeError("durable controls do not yet record Unit 20 as the next production action")
    return {
        "current_state": identity(state_path, "00_control/CURRENT_STATE.md"),
        "cursor": identity(cursor_path, "00_control/CURSOR.json"),
        "decision_log": identity(decision_path, "00_control/DECISION_LOG.md"),
        "unit20_next_action_recorded": True,
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
    current = {name: identity(project_path(root, rel), rel) for name, rel in paths.items()}
    build = load_json(root / BUILD_QA_REL)
    structural = load_json(root / PDF_STRUCTURAL_QA_REL)
    visual = load_json(root / PDF_VISUAL_QA_REL)
    html_manifest = load_json(root / HTML_MANIFEST_REL)
    html_qa = load_json(root / HTML_READER_QA_REL)
    html_browser = load_json(root / HTML_BROWSER_QA_REL)
    backend_manifest = load_json(root / BACKEND_MANIFEST_REL)
    backend_qa = load_json(root / BACKEND_QA_REL)

    if build.get("workflow") != "o011-through-unit19-pdf-build-v1" or build.get("deterministic_clean_cycles") is not True:
        raise RuntimeError("Unit 19 PDF build receipt is not the deterministic settled workflow")
    assert_record(root, build.get("output"), PDF_REL)
    cycles = build.get("cycles")
    if not isinstance(cycles, list) or len(cycles) != 2 or any(cycle.get("sha256") != current["pdf"]["sha256"] for cycle in cycles):
        raise RuntimeError("PDF receipt does not prove two byte-identical clean cycles")
    if structural.get("passed") is not True:
        raise RuntimeError("PDF structural QA has not passed")
    assert_record(root, structural.get("pdf"), PDF_REL)
    require_bound(structural, current["build_qa"], "PDF structural QA")
    if visual.get("status") != "pass" or not all_true(visual.get("checks")):
        raise RuntimeError("PDF visual QA has not passed all checks")
    assert_record(root, visual.get("surface"), PDF_REL)
    if visual["surface"].get("build_receipt_sha256") != current["build_qa"]["sha256"]:
        raise RuntimeError("PDF visual QA is not bound to current build receipt")

    if html_manifest.get("workflow") != "o011-export-html-v19" or html_manifest.get("model_identification") != MODEL:
        raise RuntimeError("HTML manifest workflow/model contract is not current")
    if html_manifest.get("text_license") != "CC BY-SA 4.0" or html_manifest.get("non_endorsement") is not True:
        raise RuntimeError("HTML manifest rights/non-endorsement contract is not current")
    if html_qa.get("status") != "pass" or not all_true(html_qa.get("checks")):
        raise RuntimeError("HTML structural QA has not passed all checks")
    assert_record(root, html_qa.get("entry"), HTML_ENTRY_REL)
    assert_record(root, html_qa.get("manifest"), HTML_MANIFEST_REL)
    if html_qa.get("counts", {}).get("exercises") != 394 or html_qa.get("counts", {}).get("source_supplied_solutions") != 54:
        raise RuntimeError("HTML exercise/solution census changed")
    if html_browser.get("status") != "pass" or not all_true(html_browser.get("checks")):
        raise RuntimeError("HTML browser QA has not passed all checks")
    require_bound(html_browser.get("surface"), current["html_entry"], "HTML browser QA")
    require_bound(html_browser.get("surface"), current["html_manifest"], "HTML browser QA")
    require_bound(html_browser.get("surface"), current["html_reader_qa"], "HTML browser QA")
    html_tree = verify_html_tree(root, html_manifest, html_qa)

    if backend_manifest.get("workflow") != "o011-export-backend-v19":
        raise RuntimeError("backend manifest workflow changed")
    claims = backend_manifest.get("claims")
    if not isinstance(claims, dict) or not all_true(claims):
        raise RuntimeError("backend manifest claims are incomplete")
    combined = backend_manifest.get("combined")
    backend_record_count = combined.get("record_count") if isinstance(combined, dict) else None
    if not isinstance(backend_record_count, int) or backend_record_count <= 3208:
        raise RuntimeError("backend cumulative record count does not extend the 3,208-record Unit 16 prefix")
    entity_counts = combined.get("entity_counts")
    backend_correction_count = entity_counts.get("correction") if isinstance(entity_counts, dict) else None
    if not isinstance(backend_correction_count, int) or backend_correction_count <= 193:
        raise RuntimeError("backend cumulative correction count does not extend the 193-record Unit 16 prefix")
    closure = backend_manifest.get("reader_closure")
    if not isinstance(closure, dict) or closure.get("status") != "cumulative_html_pdf_reader_bound" or closure.get("through_unit") != 19:
        raise RuntimeError("backend manifest does not bind cumulative Unit 19 readers")
    for name in ("pdf", "pdf_structural_qa", "pdf_visual_qa", "html_entry", "html_manifest", "html_reader_qa", "html_browser_qa"):
        require_bound(backend_manifest, current[name], "backend manifest")
    if backend_qa.get("status") != "pass" or not all_true(backend_qa.get("checks")):
        raise RuntimeError("backend verifier has not passed all checks")
    if backend_qa.get("combined_records") != backend_record_count or backend_qa.get("determinism", {}).get("second_export_matches_first") is not True:
        raise RuntimeError("backend verifier count/determinism contract is incomplete")
    for name in ("pdf", "pdf_structural_qa", "pdf_visual_qa", "html_entry", "html_manifest", "html_reader_qa", "html_browser_qa"):
        require_bound(backend_qa.get("reader_closure"), current[name], "backend verifier")
    backend_outputs: dict[str, dict[str, int | str]] = {}
    for key, relative in (
        ("records_csv", "backend/records.csv"),
        ("records_jsonl", "backend/records.jsonl"),
    ):
        backend_outputs[key] = assert_record(root, backend_qa.get("outputs", {}).get(key), relative)
        assert_record(root, backend_manifest.get("outputs", {}).get(key), relative)
    assert_record(root, backend_qa.get("outputs", {}).get("manifest"), BACKEND_MANIFEST_REL)

    page_count = structural.get("pdf", {}).get("pages")
    if not isinstance(page_count, int) or page_count <= 261:
        raise RuntimeError("canonical Unit 19 PDF does not extend the 261-page Unit 16 boundary")
    gate = {
        **current,
        "backend_records_csv": backend_outputs["records_csv"],
        "backend_records_jsonl": backend_outputs["records_jsonl"],
        "html_tree": html_tree,
        "coverage": {"units": 19, "exercises": 394, "source_supplied_solutions": 54, "backend_records": backend_record_count, "backend_corrections": backend_correction_count, "pdf_pages": page_count},
    }
    gate["durable_controls"] = verify_durable_controls(root, gate)
    documents = {
        "build": build,
        "html_manifest": html_manifest,
        "backend_manifest": backend_manifest,
    }
    return gate, documents


def text_scan_payload(payload: bytes, name: str) -> bytes:
    """Redact only complete Python ``re.compile`` detector definitions."""
    if PurePosixPath(name).suffix.lower() != ".py":
        return payload
    try:
        text = payload.decode("utf-8-sig")
        tree = ast.parse(text)
    except (UnicodeDecodeError, SyntaxError):
        return payload
    redacted_lines: set[int] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        function = node.func
        if not (
            isinstance(function, ast.Attribute)
            and function.attr == "compile"
            and isinstance(function.value, ast.Name)
            and function.value.id == "re"
        ):
            continue
        start = getattr(node, "lineno", None)
        end = getattr(node, "end_lineno", None)
        if isinstance(start, int) and isinstance(end, int):
            redacted_lines.update(range(start, end + 1))
    return "\n".join(
        "" if number in redacted_lines else line
        for number, line in enumerate(text.splitlines(), 1)
    ).encode("utf-8")


def scan_bytes(label: str, payload: bytes) -> None:
    scan_payload = text_scan_payload(payload, label)
    # Preserve but explicitly exempt the one locator already published inside
    # the frozen canonical Commons SVG and its bounded disclosure.  Any other
    # Unix home locator remains a hard failure.
    for admitted in ADMITTED_PUBLIC_UPSTREAM_LOCATORS:
        scan_payload = scan_payload.replace(admitted, b"[admitted-public-upstream-locator]")
    if any(pattern.search(scan_payload) for pattern in PRIVATE_PATTERNS):
        raise RuntimeError(f"private locator content found in {label}")
    if any(pattern.search(scan_payload) for pattern in SECRET_PATTERNS):
        raise RuntimeError(f"credential-like content found in {label}")
    if os.name == "nt":
        profile_name = Path.home().name.strip().encode("utf-8")
        if len(profile_name) >= 4:
            profile_pattern = re.compile(
                rb"(?i)(?<![A-Za-z])" + re.escape(profile_name) + rb"(?![A-Za-z])"
            )
            if profile_pattern.search(scan_payload):
                raise RuntimeError(f"local profile name found in public payload {label}")


def scan_zip_text(label: str, path: Path) -> tuple[int, int]:
    members = 0
    text_members = 0
    with zipfile.ZipFile(path, "r") as bundle:
        if bundle.testzip() is not None:
            raise RuntimeError(f"nested ZIP CRC failure: {label}")
        for info in bundle.infolist():
            if info.is_dir():
                continue
            members += 1
            suffix = PurePosixPath(info.filename).suffix.lower()
            if suffix in TEXT_SUFFIXES and info.file_size <= 20_000_000:
                text_members += 1
                scan_bytes(f"{label}!/{info.filename}", bundle.read(info.filename))
    return members, text_members


def privacy_scan_files(files: Iterable[tuple[str, Path]]) -> dict[str, int]:
    files_considered = 0
    text_files_scanned = 0
    nested_zip_members = 0
    nested_zip_text_members = 0
    for label, path in files:
        files_considered += 1
        if path.suffix.lower() in TEXT_SUFFIXES:
            text_files_scanned += 1
            scan_bytes(label, path.read_bytes())
        elif path.suffix.lower() == ".zip":
            members, texts = scan_zip_text(label, path)
            nested_zip_members += members
            nested_zip_text_members += texts
    return {
        "files_considered": files_considered,
        "text_files_scanned": text_files_scanned,
        "nested_zip_members_considered": nested_zip_members,
        "nested_zip_text_members_scanned": nested_zip_text_members,
        "private_locator_hits": 0,
        "credential_like_content_hits": 0,
        "local_profile_name_hits": 0,
    }


def add_mapping(mapping: dict[str, Path], archive_name: str, source: Path) -> None:
    safe_relative(archive_name)
    if archive_name in FORBIDDEN_PACKAGE_PATHS:
        raise RuntimeError(f"forbidden package path: {archive_name}")
    if not source.is_file():
        raise RuntimeError(f"required package source is missing: {source}")
    previous = mapping.get(archive_name)
    if previous is not None and previous != source:
        raise RuntimeError(f"duplicate package target: {archive_name}")
    mapping[archive_name] = source


def add_tree(mapping: dict[str, Path], root: Path, relative: str) -> None:
    base = root.joinpath(*safe_relative(relative).parts)
    if not base.is_dir():
        raise RuntimeError(f"required package tree is missing: {relative}")
    for source in sorted((path for path in base.rglob("*") if path.is_file()), key=lambda path: path.relative_to(root).as_posix()):
        add_mapping(mapping, source.relative_to(root).as_posix(), source)


def add_bound_record(mapping: dict[str, Path], root: Path, record: Any, *, allow_current_reader: bool = False) -> None:
    if not isinstance(record, dict) or not isinstance(record.get("path"), str):
        raise RuntimeError("invalid bound input record")
    relative = record["path"]
    assert_record(root, record, relative)
    is_current_reader = relative == PDF_REL or relative.startswith(f"{HTML_ROOT_REL}/")
    if allow_current_reader or not is_current_reader:
        add_mapping(mapping, relative, project_path(root, relative))


def copy_source_tree(root: Path, staging: Path, documents: dict[str, Any], gate: dict[str, Any]) -> dict[str, Any]:
    mapping: dict[str, Path] = {}
    add_mapping(mapping, "README.md", project_path(root, README_SOURCE_REL))
    add_mapping(mapping, "PACKAGE_README.md", project_path(root, README_SOURCE_REL))
    add_mapping(mapping, LICENSE_NAME, project_path(root, LICENSE_SOURCE_REL))
    add_mapping(mapping, NOTES_NAME, project_path(root, NOTES_SOURCE_REL))
    for relative in (
        *CONTROL_PUBLIC_PATHS,
        *AUTHORITY_LEDGER_PATHS,
        *FIXED_SUPPORT_PATHS,
        *HTML_GENERATION_BINDING_PATHS,
        *SCRIPT_PATHS,
        *BACKEND_PATHS,
        *ESSENTIAL_QA_PATHS,
        *PREDECESSOR_FILES,
    ):
        add_mapping(mapping, relative, project_path(root, relative))
    for relative in PREDECESSOR_TREES:
        add_tree(mapping, root, relative)

    build_inputs = documents["build"].get("inputs")
    if not isinstance(build_inputs, list) or not build_inputs:
        raise RuntimeError("build receipt has no transitive input inventory")
    for record in build_inputs:
        add_bound_record(mapping, root, record)

    html_manifest = documents["html_manifest"]
    for record in html_manifest.get("inputs", []):
        add_bound_record(mapping, root, record)
        relative = record["path"]
        target_name = PurePosixPath(relative).name
        if not target_name.endswith(".id.tex"):
            raise RuntimeError(f"unexpected translated source filename: {relative}")
        source_relative = "authority/expanded/" + target_name.removesuffix(".id.tex") + "_source.de.tex"
        add_mapping(mapping, source_relative, project_path(root, source_relative))
    for media in html_manifest.get("media", []):
        source_record = media.get("source") if isinstance(media, dict) else None
        add_bound_record(mapping, root, source_record)

    backend_inputs = documents["backend_manifest"].get("inputs")
    if not isinstance(backend_inputs, dict):
        raise RuntimeError("backend manifest has no input binding map")
    for record in backend_inputs.values():
        add_bound_record(mapping, root, record)

    # The backend's asset entities are part of the resumable mathematical and
    # rights closure even when an asset is not rendered on the current HTML
    # surface (for example, downloadable interactive companions).  Include and
    # bind every declared asset rather than relying only on the HTML manifest.
    records_path = project_path(root, "backend/records.jsonl")
    for line_number, line in enumerate(records_path.read_text(encoding="utf-8").splitlines(), start=1):
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"invalid backend JSONL at line {line_number}") from exc
        if not isinstance(record, dict) or record.get("entity_type") != "asset":
            continue
        relative = record.get("path")
        if not isinstance(relative, str) or not relative:
            raise RuntimeError(f"backend asset lacks a path at line {line_number}")
        source = project_path(root, relative)
        actual = identity(source)
        if (
            actual["bytes"] != record.get("expected_bytes")
            or actual["sha256"] != record.get("source_sha256")
        ):
            raise RuntimeError(f"backend asset identity is stale: {relative}")
        add_mapping(mapping, relative, source)

    for archive_name, source in sorted(mapping.items()):
        destination = staging.joinpath(*PurePosixPath(archive_name).parts)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        if identity(destination) != identity(source):
            raise RuntimeError(f"copy identity mismatch: {archive_name}")
    privacy = privacy_scan_files((name, staging.joinpath(*PurePosixPath(name).parts)) for name in sorted(mapping))
    rows = [
        {"path": name, **identity(staging.joinpath(*PurePosixPath(name).parts))}
        for name in sorted(mapping)
    ]
    tree_sha256 = hashlib.sha256(
        "".join(f"{row['path']}\0{row['bytes']}\0{row['sha256']}\n" for row in rows).encode("utf-8")
    ).hexdigest()
    backend_checkpoint = documents["backend_manifest"].get("checkpoint")
    extension_units = (documents["backend_manifest"].get("units17_19_extension") or {}).get("units")
    translation_states = {
        str(value.get("translation_state"))
        for value in extension_units.values()
        if isinstance(value, dict)
    } if isinstance(extension_units, dict) else set()
    if (
        not isinstance(backend_checkpoint, str)
        or not backend_checkpoint
        or len(translation_states) != 1
    ):
        raise RuntimeError("backend manifest lacks one reproducible checkpoint/translation-state contract")
    backend_translation_state = translation_states.pop()
    package_manifest = {
        "schema_version": 1,
        "workflow": "o011-unit19-compact-source-package-v1",
        "status": "active_partial",
        "coverage": "Kuliah 1–19 dan Lembar Kerja 1–19 dari 29 pasangan inti",
        "model_identification": MODEL,
        "reader_and_backend_bindings": gate,
        "rebuild_commands": [
            "pwsh -NoProfile -File scripts/build_through_unit19.ps1",
            "python scripts/verify_through_unit19_pdf.py",
            "python scripts/export_html_v19.py --root . --output output/html/unit-19 --replace",
            "python scripts/verify_html_v19.py --root . --output output/html/unit-19",
            "python scripts/test_html_v19_pipeline.py",
            f"python scripts/export_backend_v19.py --root . --checkpoint {backend_checkpoint} --translation-state {backend_translation_state}",
            "python scripts/verify_backend_v19.py --root .",
        ],
        "files_excluding_manifest_surfaces": len(rows),
        "bytes_excluding_manifest_surfaces": sum(int(row["bytes"]) for row in rows),
        "tree_sha256": tree_sha256,
        "files": rows,
        "deliberate_exclusions": [
            "Unit 19 PDF and semantic HTML reader, published separately as the first two files",
            "raw MediaWiki/XML dumps and bulk provenance export trees",
            "temporary page renders, contact sheets, diagnostics, caches, and TeX auxiliaries",
            "private locators, credentials, and remote-publication receipts",
            "duplicate generated build trees not required by the transitive build receipt",
        ],
    }
    manifest_path = staging / "PACKAGE_MANIFEST.json"
    manifest_path.write_bytes(json_bytes(package_manifest))
    checksum_files = sorted((path for path in staging.rglob("*") if path.is_file()), key=lambda path: path.relative_to(staging).as_posix())
    checksum_path = staging / "PACKAGE_CHECKSUMS.sha256"
    checksum_path.write_text(
        "".join(f"{sha256(path)}  {path.relative_to(staging).as_posix()}\n" for path in checksum_files),
        encoding="utf-8",
        newline="\n",
    )
    scan_bytes("PACKAGE_MANIFEST.json", manifest_path.read_bytes())
    scan_bytes("PACKAGE_CHECKSUMS.sha256", checksum_path.read_bytes())
    return {
        "files": len([path for path in staging.rglob("*") if path.is_file()]),
        "uncompressed_bytes": sum(path.stat().st_size for path in staging.rglob("*") if path.is_file()),
        "tree_sha256": tree_sha256,
        "privacy_scan": privacy,
    }


def directory_mapping(root: Path) -> dict[str, Path]:
    return {
        path.relative_to(root).as_posix(): path
        for path in root.rglob("*")
        if path.is_file()
    }


def create_zip(mapping: dict[str, Path], archive: Path) -> None:
    if archive.exists():
        raise RuntimeError(f"refusing to overwrite archive: {archive}")
    archive.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=9, strict_timestamps=True) as bundle:
        for name in sorted(mapping):
            info = zipfile.ZipInfo(name, date_time=ZIP_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.flag_bits |= 0x800
            bundle.writestr(info, mapping[name].read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def verify_zip(mapping: dict[str, Path], archive: Path) -> dict[str, Any]:
    expected = {name: identity(path) for name, path in mapping.items()}
    with zipfile.ZipFile(archive, "r") as bundle:
        infos = bundle.infolist()
        if [info.filename for info in infos] != sorted(expected):
            raise RuntimeError(f"ZIP inventory/order mismatch: {archive.name}")
        if bundle.testzip() is not None:
            raise RuntimeError(f"ZIP CRC failure: {archive.name}")
        for info in infos:
            if info.date_time != ZIP_TIMESTAMP or info.flag_bits & 0x1:
                raise RuntimeError(f"ZIP timestamp/encryption contract failed: {info.filename}")
            payload = bundle.read(info.filename)
            actual = {"bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}
            if actual != expected[info.filename]:
                raise RuntimeError(f"ZIP member identity mismatch: {info.filename}")
    return {
        "entries": len(expected),
        "uncompressed_bytes": sum(int(item["bytes"]) for item in expected.values()),
        "archive_bytes": archive.stat().st_size,
        "archive_sha256": sha256(archive),
        "crc_and_identity_verified": True,
        "timestamps_normalized": True,
        "encrypted_members": 0,
    }


def verify_reproducible(mapping: dict[str, Path], archive: Path, temporary_root: Path) -> bool:
    replica = temporary_root / (archive.name + ".replica")
    create_zip(mapping, replica)
    if identity(replica) != identity(archive):
        raise RuntimeError(f"second deterministic ZIP serialization differs: {archive.name}")
    return True


def validate_metadata(document: Any) -> None:
    if not isinstance(document, dict) or set(document) != {"metadata"} or not isinstance(document["metadata"], dict):
        raise RuntimeError("Zenodo metadata outer contract mismatch")
    metadata = document["metadata"]
    expected_keys = {
        "title", "description", "creators", "contributors", "license",
        "publication_date", "version", "language", "keywords", "related_identifiers",
    }
    if set(metadata) != expected_keys:
        raise RuntimeError("Zenodo metadata key contract mismatch")
    if metadata["creators"] != [{"name": "Brenner, Holger"}] or metadata["contributors"] != [{"name": "TTP", "type": "Other"}]:
        raise RuntimeError("Zenodo creator/contributor contract mismatch")
    if metadata["license"] != "other-open" or metadata["language"] != "ind":
        raise RuntimeError("Zenodo rights/language contract mismatch")
    if metadata["publication_date"] != RELEASE_DATE or metadata["version"] != VERSION:
        raise RuntimeError("Zenodo date/version contract mismatch")
    if metadata["title"] != TITLE:
        raise RuntimeError("Zenodo title contract mismatch")
    description = metadata["description"]
    for phrase in (
        "active_partial",
        "Kuliah 1–19",
        "Lembar Kerja 1–19",
        "CC BY-SA 4.0",
        "Component media retain their file-specific rights; no blanket media license is inferred.",
        MODEL,
    ):
        if phrase not in description:
            raise RuntimeError(f"Zenodo description lacks required phrase: {phrase}")
    forbidden = re.compile(r"\bTTP\b|Translation and Transcription Project", re.I)
    if forbidden.search(metadata["title"]) or forbidden.search(description):
        raise RuntimeError("umbrella organization label leaked into title/description")
    serialized = json.dumps(document, ensure_ascii=False, sort_keys=True)
    if len(forbidden.findall(serialized)) != 1:
        raise RuntimeError("metadata must contain exactly one organization-label occurrence")
    scan_bytes("Zenodo metadata", serialized.encode("utf-8"))


def write_public_manifest(release: Path) -> None:
    rows = [{"path": name, **identity(release / name)} for name in PUBLIC_FILE_ORDER[:5]]
    document = {
        "schema_version": 1,
        "workflow": "o011-unit19-public-file-manifest-v1",
        "status": "active_partial",
        "coverage": "Kuliah 1–19 dan Lembar Kerja 1–19 dari 29 pasangan inti",
        "model_identification": MODEL,
        "public_file_order": list(PUBLIC_FILE_ORDER),
        "files": rows,
        "bytes_bound": sum(int(row["bytes"]) for row in rows),
    }
    (release / MANIFEST_NAME).write_bytes(json_bytes(document))
    (release / CHECKSUMS_NAME).write_text(
        "".join(f"{sha256(release / name)}  {name}\n" for name in PUBLIC_FILE_ORDER[:6]),
        encoding="ascii",
        newline="\n",
    )


def verify_public_surfaces(release: Path, license_source: Path) -> list[dict[str, Any]]:
    actual_names = {path.name for path in release.iterdir() if path.is_file()}
    if actual_names != set(PUBLIC_FILE_ORDER) or any(path.is_dir() for path in release.iterdir()):
        raise RuntimeError("release directory does not contain exactly the seven public files")
    if (release / LICENSE_NAME).read_bytes() != license_source.read_bytes():
        raise RuntimeError("public LICENSE.md is not byte-identical to approved Unit 19 license")
    manifest = load_json(release / MANIFEST_NAME)
    rows = manifest.get("files") if isinstance(manifest, dict) else None
    if not isinstance(rows, list) or [row.get("path") for row in rows] != list(PUBLIC_FILE_ORDER[:5]):
        raise RuntimeError("FILE_MANIFEST.json inventory/order mismatch")
    for row in rows:
        actual = identity(release / row["path"])
        if {"bytes": row.get("bytes"), "sha256": row.get("sha256")} != actual:
            raise RuntimeError(f"FILE_MANIFEST.json identity mismatch: {row['path']}")
    expected_lines = [f"{sha256(release / name)}  {name}" for name in PUBLIC_FILE_ORDER[:6]]
    if (release / CHECKSUMS_NAME).read_text(encoding="ascii").splitlines() != expected_lines:
        raise RuntimeError("SHA256SUMS.txt inventory/order mismatch")
    return [{"path": name, **identity(release / name)} for name in PUBLIC_FILE_ORDER]


def atomic_write_new(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp-unit19-stage")
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
    if not root.is_dir():
        raise RuntimeError(f"project root not found: {root}")
    output_dir = resolve_output(root, args.output_dir)
    receipt_path = resolve_output(root, args.receipt)
    metadata_path = project_path(root, METADATA_REL)

    gate, documents = collect_gate(root)
    metadata = load_json(metadata_path)
    validate_metadata(metadata)
    if output_dir.exists() or receipt_path.exists():
        raise RuntimeError("refusing to overwrite existing release directory or receipt")
    output_dir.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="unit19-release-stage-", dir=output_dir.parent) as temporary_name:
        temporary_root = Path(temporary_name)
        release = temporary_root / "release"
        source_tree = temporary_root / "source-package"
        release.mkdir()
        source_tree.mkdir()

        shutil.copyfile(project_path(root, PDF_REL), release / PDF_NAME)
        shutil.copyfile(project_path(root, LICENSE_SOURCE_REL), release / LICENSE_NAME)
        shutil.copyfile(project_path(root, NOTES_SOURCE_REL), release / NOTES_NAME)

        html_mapping = directory_mapping(root / HTML_ROOT_REL)
        html_archive = release / HTML_ZIP_NAME
        create_zip(html_mapping, html_archive)
        html_zip = verify_zip(html_mapping, html_archive)
        html_zip["reproducible_second_serialization"] = verify_reproducible(html_mapping, html_archive, temporary_root)

        source_summary = copy_source_tree(root, source_tree, documents, gate)
        source_mapping = directory_mapping(source_tree)
        source_archive = release / SOURCE_ZIP_NAME
        create_zip(source_mapping, source_archive)
        source_zip = verify_zip(source_mapping, source_archive)
        source_zip["reproducible_second_serialization"] = verify_reproducible(source_mapping, source_archive, temporary_root)

        write_public_manifest(release)
        public_files = verify_public_surfaces(release, root / LICENSE_SOURCE_REL)
        privacy = privacy_scan_files((str(item["path"]), release / str(item["path"])) for item in public_files)
        public_bytes = sum(int(item["bytes"]) for item in public_files)
        if public_bytes > MAX_PUBLIC_BYTES:
            raise RuntimeError(f"public release exceeds 500,000,000-byte cap: {public_bytes}")

        publisher_files = [
            {
                "filename": str(item["path"]),
                "bytes": int(item["bytes"]),
                "sha256": str(item["sha256"]),
                "md5": md5(release / str(item["path"])),
            }
            for item in public_files
        ]
        receipt = {
            "schema_version": 1,
            "workflow": "o011-prepare-release-unit19-v1",
            "status": "pass",
            "release_date": RELEASE_DATE,
            "version": VERSION,
            "coverage": "active_partial_through_unit_19",
            "model_identification": MODEL,
            "lineage": {
                "concept_record_id": CONCEPT_RECORD_ID,
                "predecessor_record_id": PREDECESSOR_RECORD_ID,
                "new_concept_created": False,
            },
            "public_directory": output_dir.relative_to(root).as_posix(),
            "public_file_count": len(public_files),
            "public_file_order": list(PUBLIC_FILE_ORDER),
            "public_bytes": public_bytes,
            "total_public_bytes": public_bytes,
            "maximum_public_bytes": MAX_PUBLIC_BYTES,
            "under_500000000_bytes": True,
            "public_files": public_files,
            "files": publisher_files,
            "metadata": identity(metadata_path, METADATA_REL),
            "input_bindings": gate,
            "zip_verification": {"html": html_zip, "source": source_zip},
            "source_package": source_summary,
            "manifest_contract": {
                "file_manifest_rows": list(PUBLIC_FILE_ORDER[:5]),
                "checksum_rows": list(PUBLIC_FILE_ORDER[:6]),
                "receipt_binds_all_seven_public_files": True,
            },
            "rights": {
                "text_and_adaptation": "CC BY-SA 4.0",
                "component_media": "file-specific rights retained in component ledger and reader attribution",
                "non_endorsement_preserved": True,
                "license_byte_identical_to": LICENSE_SOURCE_REL,
            },
            "privacy_scan": {"status": "pass", **privacy},
            "deterministic_archives": {"status": "pass", "html": html_zip, "source": source_zip},
            "deterministic_zip_timestamp": list(ZIP_TIMESTAMP),
            "excluded": [
                "raw provenance dumps and caches",
                "private locators and credentials",
                "temporary page renders, contact sheets, diagnostics, and duplicate builds",
                "remote publication receipts not yet created",
            ],
            "remote_state_mutated": False,
        }
        receipt_payload = json_bytes(receipt)
        scan_bytes("release-preparation receipt", receipt_payload)

        release.rename(output_dir)
        atomic_write_new(receipt_path, receipt_payload)

    print(json.dumps({
        "status": "pass",
        "public_directory": output_dir.relative_to(root).as_posix(),
        "public_files": len(PUBLIC_FILE_ORDER),
        "public_bytes": public_bytes,
        "metadata": METADATA_REL,
        "receipt": receipt_path.relative_to(root).as_posix(),
        "remote_state_mutated": False,
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
