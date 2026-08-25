#!/usr/bin/env python3
"""Stage the corrective, source-complete Unit 13 r1 release locally.

The PDF and HTML reader archive are copied byte-for-byte from the already
published Unit 13 boundary.  Only the resumable source package, documentation,
manifest surfaces, and release metadata change.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
import shutil
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any, Iterable


RELEASE_DATE = "2026-08-25"
ZIP_TIMESTAMP = (2026, 8, 25, 0, 0, 0)
MODEL = "OpenAI Codex gpt-5.6-sol, Ultra"
MAX_PUBLIC_BYTES = 500 * 1024 * 1024

PDF_REL = "output/pdf/geometri-diferensial-manifold-mulus-hingga-unit-13-id.pdf"
HTML_ROOT_REL = "output/html/unit-13"
HTML_MANIFEST_REL = f"{HTML_ROOT_REL}/manifest.json"
HTML_ENTRY_REL = f"{HTML_ROOT_REL}/index.html"
HTML_PUBLISHED_ZIP_REL = "output/release-unit13/geometri-diferensial-manifold-mulus-brenner-id-unit13-html-20260825.zip"
BUILD_QA_REL = "qa/unit-13/build.json"
PDF_STRUCTURAL_QA_REL = "qa/unit-13/pdf_structural_qa.json"
PDF_VISUAL_QA_REL = "qa/unit-13/PDF_VISUAL_QA.json"
HTML_READER_QA_REL = "qa/unit-13/HTML_READER_QA.json"
HTML_VISUAL_QA_REL = "qa/unit-13/HTML_BROWSER_QA.json"
BACKEND_MANIFEST_REL = "backend/MANIFEST.json"
BACKEND_QA_REL = "qa/unit-13/backend.json"
LICENSE_SOURCE_REL = "qa/unit-13/LICENSE_RELEASE_UNIT13.md"
README_SOURCE_REL = "qa/unit-13/PACKAGE_README_R1.md"
NOTES_SOURCE_REL = "qa/unit-13/RELEASE_NOTES_UNIT13_R1_20260825.md"

PDF_NAME = "geometri-diferensial-manifold-mulus-hingga-unit-13-id.pdf"
HTML_ZIP_NAME = "geometri-diferensial-manifold-mulus-brenner-id-unit13-html-20260825.zip"
SOURCE_ZIP_NAME = "geometri-diferensial-manifold-mulus-unit13-source-r1-20260825.zip"
LICENSE_NAME = "LICENSE.md"
NOTES_NAME = "RELEASE_NOTES_UNIT13_R1_20260825.md"
MANIFEST_NAME = "FILE_MANIFEST.csv"
CHECKSUMS_NAME = "CHECKSUMS.sha256"
PUBLIC_FILE_ORDER = (
    PDF_NAME,
    HTML_ZIP_NAME,
    SOURCE_ZIP_NAME,
    LICENSE_NAME,
    NOTES_NAME,
    MANIFEST_NAME,
    CHECKSUMS_NAME,
)

DEFAULT_OUTPUT_REL = "output/release-unit13-r1"
DEFAULT_METADATA_REL = "qa/unit-13/ZENODO_METADATA_UNIT13_R1.json"
DEFAULT_RECEIPT_REL = "qa/unit-13/RELEASE_PREPARATION_RECEIPT_R1.json"

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
SOURCE_SUPPORT_PATHS = (
    "source/unit_media.json",
    "source/unit07_interactive_media.json",
    "source/unit11_interactive_media.json",
    "authority/expanded/script_preamble_source.de.tex",
    "build/brenner-compat.tex",
    "build/through-unit-10.tex",
    "build/generated/through-unit-13-driver.tex",
)
SCRIPT_PATHS = (
    "scripts/build_through_unit13.ps1",
    "scripts/export_backend_v10.py",
    "scripts/export_backend_v13.py",
    "scripts/export_html_v10.py",
    "scripts/export_html_v13.py",
    "scripts/prepare_unit_media.py",
    "scripts/prepare_unit_tex.py",
    "scripts/test_html_v13_pipeline.py",
    "scripts/verify_backend_v10.py",
    "scripts/verify_backend_v13.py",
    "scripts/verify_html_animated_media.py",
    "scripts/verify_html_v10.py",
    "scripts/verify_html_v13.py",
    "scripts/verify_source_package_unit13_r1.py",
    "scripts/verify_through_unit06_pdf.py",
    "scripts/verify_through_unit10_pdf.py",
    "scripts/verify_through_unit13_pdf.py",
    "scripts/verify_unit_translation.py",
)
BACKEND_PATHS = (
    "backend/MANIFEST.json",
    "backend/records.csv",
    "backend/records.jsonl",
    "backend/schema/o011-record-v1.schema.json",
)
ESSENTIAL_QA_PATHS = (
    "qa/unit-07/INTERACTIVE_MEDIA_QA.json",
    "qa/unit-10/HTML_READER_QA.json",
    "qa/unit-10/ZENODO_PUBLIC_READBACK_RECEIPT.json",
    "qa/unit-11/AUTHORITY_PREFLIGHT.json",
    "qa/unit-11/AUTHORITY_PREFLIGHT_VERIFY.json",
    "qa/unit-11/INTERACTIVE_MEDIA_QA.json",
    "qa/unit-11/POST_CORRECTION_MATH_QA.json",
    "qa/unit-11/solution_closure.json",
    "qa/unit-11_media.json",
    "qa/unit-12/AUTHORITY_PREFLIGHT.json",
    "qa/unit-12/AUTHORITY_PREFLIGHT_VERIFY.json",
    "qa/unit-12/ANIMATED_MEDIA_QA.json",
    "qa/unit-12/HTML_ANIMATED_MEDIA_QA.json",
    "qa/unit-12/POST_CORRECTION_MATH_QA.json",
    "qa/unit-12/solution_closure.json",
    "qa/unit-12_media.json",
    "qa/unit-13/AUTHORITY_PREFLIGHT.json",
    "qa/unit-13/AUTHORITY_PREFLIGHT_VERIFY.json",
    "qa/unit-13/HTML_BROWSER_QA.json",
    "qa/unit-13/HTML_READER_QA.json",
    "qa/unit-13/MEDIA_ALIAS_RECEIPT.json",
    "qa/unit-13/PDF_VISUAL_QA.json",
    "qa/unit-13/POST_CORRECTION_MATH_QA.json",
    "qa/unit-13/UNIT10_PREFIX_PRESERVATION_RECEIPT.json",
    "qa/unit-13/WRAPPER_DERIVATION_RECEIPT.json",
    "qa/unit-13/backend.json",
    "qa/unit-13/build.json",
    "qa/unit-13/pdf_structural_qa.json",
    "qa/unit-13/solution_closure.json",
    "qa/unit-13_media.json",
)

UNIT10_FIXED_PATHS = (
    "output/pdf/geometri-diferensial-manifold-mulus-hingga-unit-10-id.pdf",
    "qa/unit-10/build.json",
    "qa/unit-10/pdf_structural_qa.json",
)

UNIT10_TREE_ROOTS = (
    "output/html/unit-10",
    "output/release-unit10",
)

REBUILD_TREE_ROOTS = (
    "build/generated",
)

TEXT_SUFFIXES = {"", ".csv", ".css", ".html", ".json", ".jsonl", ".md", ".ps1", ".py", ".svg", ".tex", ".txt"}
PRIVATE_PATTERNS = (
    re.compile(rb"[A-Za-z]:[\\/]+Users[\\/]", re.I),
    re.compile(rb"(?<!:)\/Users\/", re.I),
    re.compile(rb"\\\\[^\\\r\n]+\\Users\\", re.I),
)
SECRET_PATTERNS = (
    re.compile(rb"github_pat_[A-Za-z0-9_]{40,}"),
    re.compile(rb"gh[pousr]_[A-Za-z0-9]{36,}"),
    re.compile(rb"(?:access[_-]?token|api[_-]?token|password|secret)\s*[:=]\s*[\"'][^\"'\r\n]{16,}[\"']", re.I),
)

FORBIDDEN_PACKAGE_PATHS = {
    "00_control/PRIVATE_LOCAL_LOCATORS.md",
    "qa/unit-05/ZENODO_PUBLICATION_RECEIPT.md",
}

REBUILD_COMMANDS = (
    "pwsh -NoProfile -File scripts/build_through_unit13.ps1",
    "python scripts/verify_through_unit13_pdf.py",
    "python scripts/export_html_v13.py --root . --output output/html/unit-13 --replace",
    "python scripts/verify_html_v13.py --root . --output output/html/unit-13",
    "python scripts/export_backend_v13.py --root . --checkpoint 2026-08-24T20:50:06Z --translation-state mathematically_reviewed",
    "python scripts/verify_backend_v13.py --root .",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def md5(path: Path) -> str:
    """Return the transport checksum required by the Zenodo file API."""
    digest = hashlib.md5()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def identity(path: Path, path_label: str | None = None) -> dict[str, int | str]:
    result: dict[str, int | str] = {"bytes": path.stat().st_size, "sha256": sha256(path)}
    if path_label is not None:
        result = {"path": path_label, **result}
    return result


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"cannot load required JSON {path}: {exc}") from exc


def project_path(root: Path, relative: str) -> Path:
    parsed = PurePosixPath(relative)
    if parsed.is_absolute() or ".." in parsed.parts or "\\" in relative or ":" in relative:
        raise RuntimeError(f"unsafe project-relative path: {relative}")
    path = root.joinpath(*parsed.parts)
    if not path.is_file():
        raise RuntimeError(f"required file is missing: {relative}")
    return path


def resolve_output(root: Path, value: Path) -> Path:
    path = (value if value.is_absolute() else root / value).resolve()
    if path != root and root not in path.parents:
        raise RuntimeError(f"output must remain inside project root: {path}")
    return path


def assert_record(root: Path, record: Any, expected_path: str) -> dict[str, int | str]:
    if not isinstance(record, dict):
        raise RuntimeError(f"missing identity record for {expected_path}")
    if record.get("path") != expected_path:
        raise RuntimeError(f"identity path mismatch for {expected_path}: {record.get('path')!r}")
    path = project_path(root, expected_path)
    actual = identity(path, expected_path)
    declared = {"path": record.get("path"), "bytes": record.get("bytes"), "sha256": record.get("sha256")}
    if declared != actual:
        raise RuntimeError(f"stale identity binding for {expected_path}: declared={declared}, actual={actual}")
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
    qa_names = set()
    for record in qa_records:
        relative = record.get("path") if isinstance(record, dict) else None
        if not isinstance(relative, str) or not relative.startswith(f"{HTML_ROOT_REL}/"):
            raise RuntimeError("invalid HTML QA inventory record")
        qa_names.add(relative.removeprefix(f"{HTML_ROOT_REL}/"))
        assert_record(root, record, relative)
    if qa_names != expected_names:
        raise RuntimeError("HTML QA inventory differs from the current HTML tree")
    return {"files": len(expected_names), "bytes": sum((html_root / name).stat().st_size for name in expected_names)}


def collect_gate(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    paths = {
        "pdf": PDF_REL,
        "build_qa": BUILD_QA_REL,
        "pdf_structural_qa": PDF_STRUCTURAL_QA_REL,
        "pdf_visual_qa": PDF_VISUAL_QA_REL,
        "html_entry": HTML_ENTRY_REL,
        "html_manifest": HTML_MANIFEST_REL,
        "html_reader_qa": HTML_READER_QA_REL,
        "html_visual_qa": HTML_VISUAL_QA_REL,
        "backend_manifest": BACKEND_MANIFEST_REL,
        "backend_qa": BACKEND_QA_REL,
    }
    current = {name: identity(project_path(root, rel), rel) for name, rel in paths.items()}
    build = load_json(root / BUILD_QA_REL)
    structural = load_json(root / PDF_STRUCTURAL_QA_REL)
    pdf_visual = load_json(root / PDF_VISUAL_QA_REL)
    html_manifest = load_json(root / HTML_MANIFEST_REL)
    html_qa = load_json(root / HTML_READER_QA_REL)
    html_visual = load_json(root / HTML_VISUAL_QA_REL)
    backend_manifest = load_json(root / BACKEND_MANIFEST_REL)
    backend_qa = load_json(root / BACKEND_QA_REL)

    if build.get("workflow") != "o011-through-unit13-pdf-build-v1" or build.get("deterministic_clean_cycles") is not True:
        raise RuntimeError("current Unit 13 PDF build receipt is not the deterministic settled workflow")
    assert_record(root, build.get("output"), PDF_REL)
    cycles = build.get("cycles")
    if not isinstance(cycles, list) or len(cycles) != 2 or any(cycle.get("sha256") != current["pdf"]["sha256"] for cycle in cycles):
        raise RuntimeError("PDF build receipt does not prove two byte-identical clean cycles")
    if structural.get("passed") is not True:
        raise RuntimeError("PDF structural QA has not passed")
    assert_record(root, structural.get("pdf"), PDF_REL)
    require_bound(structural, current["build_qa"], "PDF structural QA")
    if pdf_visual.get("status") != "pass" or not all_true(pdf_visual.get("checks")):
        raise RuntimeError("PDF visual QA has not passed all checks")
    assert_record(root, pdf_visual.get("surface"), PDF_REL)
    if pdf_visual["surface"].get("build_receipt_sha256") != current["build_qa"]["sha256"]:
        raise RuntimeError("PDF visual QA is not bound to the current build receipt")

    if html_manifest.get("model_identification") != MODEL or html_manifest.get("non_endorsement") is not True:
        raise RuntimeError("HTML manifest model/non-endorsement contract is not current")
    if html_manifest.get("text_license") != "CC BY-SA 4.0":
        raise RuntimeError("HTML manifest text license is not CC BY-SA 4.0")
    if html_qa.get("status") != "pass" or not all_true(html_qa.get("checks")):
        raise RuntimeError("semantic HTML structural QA has not passed all checks")
    assert_record(root, html_qa.get("entry"), HTML_ENTRY_REL)
    assert_record(root, html_qa.get("manifest"), HTML_MANIFEST_REL)
    if html_visual.get("status") != "pass" or not all_true(html_visual.get("checks")):
        raise RuntimeError("semantic HTML visual QA has not passed all checks")
    assert_record(root, html_visual.get("surface"), HTML_ENTRY_REL)
    surface = html_visual["surface"]
    if (surface.get("manifest_path"), surface.get("manifest_bytes"), surface.get("manifest_sha256")) != (
        HTML_MANIFEST_REL,
        current["html_manifest"]["bytes"],
        current["html_manifest"]["sha256"],
    ):
        raise RuntimeError("HTML visual QA is not bound to the current HTML manifest")
    if (surface.get("structural_qa_path"), surface.get("structural_qa_sha256")) != (
        HTML_READER_QA_REL,
        current["html_reader_qa"]["sha256"],
    ):
        raise RuntimeError("HTML visual QA is not bound to the current structural QA")
    html_inventory = verify_html_tree(root, html_manifest, html_qa)

    claims = backend_manifest.get("claims")
    if not isinstance(claims, dict) or any(
        claims.get(key) is not True
        for key in (
            "cumulative_html_present",
            "cumulative_pdf_present",
            "cumulative_reader_all_or_nothing",
            "cumulative_html_manifest_and_qa_current",
            "cumulative_pdf_structural_qa_current",
            "cumulative_pdf_visual_qa_current",
        )
    ):
        raise RuntimeError("backend manifest has not admitted both current reader surfaces")
    extension = backend_manifest.get("units11_13_extension")
    reader_status = extension.get("reader_status", "") if isinstance(extension, dict) else ""
    if reader_status != "cumulative_html_pdf_reader_bound" or extension.get("model_identification") != MODEL:
        raise RuntimeError(f"backend manifest reader/model status is not release-ready: {reader_status!r}")
    for name in ("pdf", "pdf_structural_qa", "pdf_visual_qa", "html_entry", "html_manifest", "html_reader_qa"):
        require_bound(backend_manifest, current[name], "backend manifest")
    if backend_qa.get("status") != "pass" or not all_true(backend_qa.get("checks")):
        raise RuntimeError("backend verifier has not passed all current checks")
    closure = backend_qa.get("reader_closure")
    if not isinstance(closure, dict) or closure.get("status") != "cumulative_html_pdf_reader_bound":
        raise RuntimeError("backend verifier does not report all-or-nothing PDF/HTML closure")
    for name in ("pdf", "pdf_structural_qa", "pdf_visual_qa", "html_entry", "html_manifest", "html_reader_qa"):
        require_bound(closure, current[name], "backend verifier reader closure")
    extension_qa = backend_qa.get("units11_13_extension")
    if not isinstance(extension_qa, dict) or extension_qa.get("pdf_reader_bound") is not True or extension_qa.get("html_reader_bound") is not True:
        raise RuntimeError("backend verifier has not bound both PDF and HTML readers")
    if backend_qa.get("determinism", {}).get("second_export_matches_first") is not True:
        raise RuntimeError("backend verifier does not prove deterministic re-export")
    assert_record(root, backend_qa.get("outputs", {}).get("manifest"), BACKEND_MANIFEST_REL)
    backend_outputs = {}
    for key, expected_path in (("records_csv", "backend/records.csv"), ("records_jsonl", "backend/records.jsonl")):
        backend_outputs[key] = assert_record(root, backend_qa.get("outputs", {}).get(key), expected_path)
        assert_record(root, backend_manifest.get("outputs", {}).get(key), expected_path)

    if MODEL not in json.dumps(structural, ensure_ascii=False):
        raise RuntimeError("PDF structural QA lacks exact model provenance")
    gate = {
        **current,
        "backend_records_csv": backend_outputs["records_csv"],
        "backend_records_jsonl": backend_outputs["records_jsonl"],
        "html_tree": html_inventory,
        "reader_status": reader_status,
    }
    documents = {
        "html_manifest": html_manifest,
        "html_qa": html_qa,
        "backend_manifest": backend_manifest,
        "backend_qa": backend_qa,
    }
    return gate, documents


def scan_bytes(label: str, payload: bytes) -> None:
    # Release scripts contain their own literal leak-detection regexes. Ignore
    # only those detector-definition lines so the detector does not flag
    # itself; every other byte of the scripts remains in scope.
    scan_payload = b"\n".join(
        b""
        if (
            b"re.compile" in line
            and any(marker in line.lower() for marker in (b"users", b"token", b"password", b"secret"))
        ) or (
            b"[A-Za-z]:[\\\\/]" in line
            and b"Users|Documents|AppData" in line
            and (b'r"(?:' in line or b'rb"(?:' in line)
        )
        else line
        for line in payload.splitlines()
    )
    if any(pattern.search(scan_payload) for pattern in PRIVATE_PATTERNS):
        raise RuntimeError(f"private locator content found in {label}")
    if any(pattern.search(scan_payload) for pattern in SECRET_PATTERNS):
        raise RuntimeError(f"credential-like content found in {label}")


def privacy_scan_files(files: Iterable[tuple[str, Path]]) -> dict[str, int]:
    raw_count = 0
    text_count = 0
    nested_zip_count = 0
    nested_text_count = 0
    for label, path in files:
        raw_count += 1
        if path.suffix.lower() in TEXT_SUFFIXES:
            text_count += 1
            scan_bytes(label, path.read_bytes())
        elif path.suffix.lower() == ".zip":
            nested_zip_count += 1
            with zipfile.ZipFile(path, "r") as bundle:
                if bundle.testzip() is not None:
                    raise RuntimeError(f"nested ZIP CRC failure during privacy scan: {label}")
                for member in bundle.infolist():
                    name = member.filename.replace("\\", "/").lstrip("./")
                    parsed = PurePosixPath(name)
                    if parsed.is_absolute() or ".." in parsed.parts or ":" in name:
                        raise RuntimeError(f"unsafe nested ZIP member path in {label}: {member.filename}")
                    if name in FORBIDDEN_PACKAGE_PATHS or name.endswith("/PRIVATE_LOCAL_LOCATORS.md"):
                        raise RuntimeError(f"forbidden private member in nested ZIP {label}: {name}")
                    if PurePosixPath(name).suffix.lower() in TEXT_SUFFIXES:
                        nested_text_count += 1
                        scan_bytes(f"{label}!/{name}", bundle.read(member))
    return {
        "files_considered": raw_count,
        "text_files_scanned": text_count,
        "nested_zip_files_scanned": nested_zip_count,
        "nested_zip_text_members_scanned": nested_text_count,
        "private_locator_hits": 0,
        "credential_like_content_hits": 0,
    }


def add_mapping(mapping: dict[str, Path], archive_name: str, source: Path) -> None:
    parsed = PurePosixPath(archive_name)
    if parsed.is_absolute() or ".." in parsed.parts or "\\" in archive_name or ":" in archive_name:
        raise RuntimeError(f"unsafe archive name: {archive_name}")
    if not source.is_file():
        raise RuntimeError(f"required package source is missing: {source}")
    previous = mapping.get(archive_name)
    if previous is not None and previous != source:
        raise RuntimeError(f"duplicate package target: {archive_name}")
    mapping[archive_name] = source


def add_tree(mapping: dict[str, Path], root: Path, relative_root: str) -> None:
    directory = root.joinpath(*PurePosixPath(relative_root).parts)
    if not directory.is_dir():
        raise RuntimeError(f"required package tree is missing: {relative_root}")
    files = sorted((path for path in directory.rglob("*") if path.is_file()), key=lambda path: path.relative_to(root).as_posix())
    if not files:
        raise RuntimeError(f"required package tree is empty: {relative_root}")
    for path in files:
        relative = path.relative_to(root).as_posix()
        if relative in FORBIDDEN_PACKAGE_PATHS or relative.endswith("/PRIVATE_LOCAL_LOCATORS.md"):
            raise RuntimeError(f"forbidden path appeared in required package tree: {relative}")
        add_mapping(mapping, relative, path)


def cumulative_correction_manifest_paths(root: Path) -> list[str]:
    paths: list[str] = []
    control = root / "00_control"
    paths.extend(path.relative_to(root).as_posix() for path in control.glob("*PROTECTED_CORRECTIONS.json") if path.is_file())
    for unit in range(1, 14):
        qa_dir = root / f"qa/unit-{unit:02d}"
        if qa_dir.is_dir():
            paths.extend(path.relative_to(root).as_posix() for path in qa_dir.glob("*PROTECTED_CORRECTIONS.json") if path.is_file())
    result = sorted(set(paths))
    if len(result) != 48:
        raise RuntimeError(f"cumulative correction-manifest census changed; expected 48, found {len(result)}")
    return result


def bound_input_paths(document: Any, surface: str) -> list[str]:
    if isinstance(document, dict):
        records = document.get("inputs")
    else:
        records = None
    values: list[Any]
    if isinstance(records, list):
        values = records
    elif isinstance(records, dict):
        values = list(records.values())
    else:
        raise RuntimeError(f"{surface} has no usable input-binding collection")
    paths: list[str] = []
    for record in values:
        if not isinstance(record, dict) or not isinstance(record.get("path"), str):
            raise RuntimeError(f"invalid input binding in {surface}")
        paths.append(record["path"])
    return sorted(set(paths))


def verify_static_rebuild_closure(staging: Path, unit10_build: dict[str, Any]) -> dict[str, Any]:
    missing: list[str] = []
    required = set(CONTROL_PUBLIC_PATHS)
    required.update(AUTHORITY_LEDGER_PATHS)
    required.update(SOURCE_SUPPORT_PATHS)
    required.update(SCRIPT_PATHS)
    required.update(BACKEND_PATHS)
    required.update(ESSENTIAL_QA_PATHS)
    required.update(UNIT10_FIXED_PATHS)
    required.update(bound_input_paths(unit10_build, "frozen Unit 10 PDF build receipt"))
    required.update(f"qa/unit-{unit:02d}_media.json" for unit in range(1, 14))
    for relative in sorted(required):
        if not staging.joinpath(*PurePosixPath(relative).parts).is_file():
            missing.append(relative)
    for relative_root in UNIT10_TREE_ROOTS:
        path = staging.joinpath(*PurePosixPath(relative_root).parts)
        if not path.is_dir() or not any(item.is_file() for item in path.rglob("*")):
            missing.append(relative_root + "/**")
    for relative_root in REBUILD_TREE_ROOTS:
        path = staging.joinpath(*PurePosixPath(relative_root).parts)
        if not path.is_dir() or not any(item.is_file() for item in path.rglob("*")):
            missing.append(relative_root + "/**")
    if missing:
        raise RuntimeError("clean-rebuild source closure is incomplete: " + ", ".join(missing))
    for forbidden in FORBIDDEN_PACKAGE_PATHS:
        if staging.joinpath(*PurePosixPath(forbidden).parts).exists():
            raise RuntimeError(f"forbidden private path entered source package: {forbidden}")
    unit10_release = staging / "output/release-unit10"
    unit10_names = sorted(path.name for path in unit10_release.iterdir() if path.is_file())
    if len(unit10_names) != 7:
        raise RuntimeError(f"frozen Unit 10 release must contain exactly seven files, found {unit10_names!r}")
    unit10_html = staging / "output/html/unit-10"
    html_names = sorted(path.relative_to(unit10_html).as_posix() for path in unit10_html.rglob("*") if path.is_file())
    if len(html_names) != 21:
        raise RuntimeError(f"frozen Unit 10 HTML tree must contain exactly 21 files, found {len(html_names)}")
    return {
        "status": "static_closure_pass",
        "commands": list(REBUILD_COMMANDS),
        "required_path_count": len(required),
        "unit10_release_files": unit10_names,
        "unit10_html_files": len(html_names),
        "unit10_transitive_build_inputs": len(bound_input_paths(unit10_build, "frozen Unit 10 PDF build receipt")),
        "forbidden_paths_absent": sorted(FORBIDDEN_PACKAGE_PATHS),
    }


def copy_source_tree(root: Path, staging: Path, documents: dict[str, Any], gate: dict[str, Any]) -> dict[str, Any]:
    mapping: dict[str, Path] = {}
    add_mapping(mapping, "README.md", project_path(root, README_SOURCE_REL))
    add_mapping(mapping, LICENSE_NAME, project_path(root, LICENSE_SOURCE_REL))
    add_mapping(mapping, NOTES_NAME, project_path(root, NOTES_SOURCE_REL))
    for relative in (
        *CONTROL_PUBLIC_PATHS,
        *AUTHORITY_LEDGER_PATHS,
        *SOURCE_SUPPORT_PATHS,
        *SCRIPT_PATHS,
        *BACKEND_PATHS,
        *ESSENTIAL_QA_PATHS,
        *UNIT10_FIXED_PATHS,
    ):
        add_mapping(mapping, relative, project_path(root, relative))
    for relative in cumulative_correction_manifest_paths(root):
        add_mapping(mapping, relative, project_path(root, relative))
    for unit in range(1, 14):
        relative = f"qa/unit-{unit:02d}_media.json"
        add_mapping(mapping, relative, project_path(root, relative))
    for relative_root in UNIT10_TREE_ROOTS:
        add_tree(mapping, root, relative_root)
    for relative_root in REBUILD_TREE_ROOTS:
        add_tree(mapping, root, relative_root)

    unit10_build = load_json(root / "qa/unit-10/build.json")
    unit13_build = load_json(root / BUILD_QA_REL)
    for relative in (
        *bound_input_paths(unit10_build, "frozen Unit 10 PDF build receipt"),
        *bound_input_paths(unit13_build, "current Unit 13 PDF build receipt"),
    ):
        add_mapping(mapping, relative, project_path(root, relative))

    html_manifest = documents["html_manifest"]
    for record in html_manifest["inputs"]:
        target_relative = record.get("path")
        if not isinstance(target_relative, str):
            raise RuntimeError("invalid translated-source binding in HTML manifest")
        assert_record(root, record, target_relative)
        add_mapping(mapping, target_relative, project_path(root, target_relative))
        target_name = PurePosixPath(target_relative).name
        if not target_name.endswith(".id.tex"):
            raise RuntimeError(f"unexpected translated source filename: {target_relative}")
        source_relative = "authority/expanded/" + target_name.removesuffix(".id.tex") + "_source.de.tex"
        add_mapping(mapping, source_relative, project_path(root, source_relative))
    for media in html_manifest.get("media", []):
        source_record = media.get("source") if isinstance(media, dict) else None
        if not isinstance(source_record, dict) or not isinstance(source_record.get("path"), str):
            raise RuntimeError("invalid media source binding in HTML manifest")
        source_relative = source_record["path"]
        assert_record(root, source_record, source_relative)
        add_mapping(mapping, source_relative, project_path(root, source_relative))
    for media in html_manifest.get("source_linked_media", []):
        source_record = media.get("source") if isinstance(media, dict) else None
        if not isinstance(source_record, dict) or not isinstance(source_record.get("path"), str):
            raise RuntimeError("invalid source-linked media binding in HTML manifest")
        source_relative = source_record["path"]
        assert_record(root, source_record, source_relative)
        add_mapping(mapping, source_relative, project_path(root, source_relative))

    # The backend input map is the authoritative compact closure for the new
    # Unit 11--13 extension.  Include every non-reader input it binds, which
    # captures translation receipts and correction manifests without copying
    # the separately published reader files into the source archive.
    backend_inputs = documents["backend_manifest"].get("inputs")
    if not isinstance(backend_inputs, dict):
        raise RuntimeError("backend manifest has no input binding map")
    for record in backend_inputs.values():
        if not isinstance(record, dict) or not isinstance(record.get("path"), str):
            raise RuntimeError("invalid backend input binding")
        relative = record["path"]
        assert_record(root, record, relative)
        if not relative.startswith("output/"):
            add_mapping(mapping, relative, project_path(root, relative))

    for archive_name, source in sorted(mapping.items()):
        destination = staging.joinpath(*PurePosixPath(archive_name).parts)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        if identity(destination) != identity(source):
            raise RuntimeError(f"copy identity mismatch: {archive_name}")
    privacy = privacy_scan_files((name, staging.joinpath(*PurePosixPath(name).parts)) for name in sorted(mapping))
    rebuild = verify_static_rebuild_closure(staging, unit10_build)

    rows = [
        {"path": name, **identity(staging.joinpath(*PurePosixPath(name).parts))}
        for name in sorted(mapping)
    ]
    tree_sha256 = hashlib.sha256(
        "".join(f"{row['path']}\0{row['bytes']}\0{row['sha256']}\n" for row in rows).encode("utf-8")
    ).hexdigest()
    package_manifest = {
        "schema_version": 1,
        "workflow": "o011-unit13-corrective-source-package-r1-v1",
        "status": "active_partial",
        "coverage": "Kuliah 1–13 dan Lembar Kerja 1–13 dari 29 pasangan inti",
        "model_identification": MODEL,
        "corrective_revision": {
            "version": "2026.08.25-unit13-r1",
            "scope": "source_package_and_documentation_only",
            "reader_record_predecessor": 22096736,
            "pdf_bytes_unchanged": True,
            "html_archive_bytes_unchanged": True,
            "reason": "The predecessor source ZIP omitted durable controls and exact incremental rebuild dependencies.",
        },
        "reader_and_backend_bindings": gate,
        "clean_rebuild": rebuild,
        "durable_controls": {
            "paths": list(CONTROL_PUBLIC_PATHS),
            "private_local_locators_excluded": True,
        },
        "cumulative_protected_correction_manifests": {
            "count": len(cumulative_correction_manifest_paths(root)),
            "paths": cumulative_correction_manifest_paths(root),
        },
        "frozen_unit10_dependencies": {
            "pdf": identity(project_path(root, UNIT10_FIXED_PATHS[0]), UNIT10_FIXED_PATHS[0]),
            "source_zip": identity(
                project_path(root, "output/release-unit10/geometri-diferensial-manifold-mulus-brenner-id-unit10-source-20260823.zip"),
                "output/release-unit10/geometri-diferensial-manifold-mulus-brenner-id-unit10-source-20260823.zip",
            ),
            "html_zip": identity(
                project_path(root, "output/release-unit10/geometri-diferensial-manifold-mulus-brenner-id-unit10-html-20260823.zip"),
                "output/release-unit10/geometri-diferensial-manifold-mulus-brenner-id-unit10-html-20260823.zip",
            ),
            "html_tree_files": rebuild["unit10_html_files"],
            "transitive_build_inputs": rebuild["unit10_transitive_build_inputs"],
        },
        "files_excluding_manifest_surfaces": len(rows),
        "bytes_excluding_manifest_surfaces": sum(int(row["bytes"]) for row in rows),
        "tree_sha256": tree_sha256,
        "files": rows,
        "deliberate_exclusions": [
            "Unit 13 primary PDF and semantic HTML reader (published unchanged as separate reader-first files)",
            "raw MediaWiki/XML dumps and bulk provenance export trees",
            "historical witness PDFs and duplicate generated build trees",
            "temporary renders, caches, TeX auxiliaries, private locators, credentials, and remote-publication receipts",
            "qa/unit-05/ZENODO_PUBLICATION_RECEIPT.md (known private publication receipt)",
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
        "files": len(list(path for path in staging.rglob("*") if path.is_file())),
        "uncompressed_bytes": sum(path.stat().st_size for path in staging.rglob("*") if path.is_file()),
        "tree_sha256": tree_sha256,
        "privacy_scan": privacy,
        "clean_rebuild": rebuild,
        "correction_manifest_count": len(cumulative_correction_manifest_paths(root)),
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


def directory_mapping(root: Path) -> dict[str, Path]:
    return {
        path.relative_to(root).as_posix(): path
        for path in root.rglob("*")
        if path.is_file()
    }


def metadata_document() -> dict[str, Any]:
    description = (
        "Reader-first active_partial Indonesian adaptation through Kuliah 1–13 and Lembar Kerja 1–13. "
        "Reader content and validated PDF/HTML bytes are unchanged from record 22096736; this revision corrects "
        "the resumable source package and its documentation. The release contains an A4 PDF, a reflowable "
        "semantic HTML reader, and a clean-buildable source/backend/QA package. Course text and the Indonesian "
        "adaptation are CC BY-SA 4.0. Component media retain their file-specific rights; no blanket media "
        "license is inferred. This is an "
        "independent adaptation and is not endorsed by the source author, Wikiversity, Wikimedia Commons, "
        "the Wikimedia Foundation, or media creators. Computational provenance: " + MODEL + "."
    )
    document = {
        "metadata": {
            "title": "Geometri Diferensial dan Manifold Mulus — Edisi Bahasa Indonesia (Batas Unit 13, Revisi Paket Sumber)",
            "description": description,
            "creators": [{"name": "Brenner, Holger"}],
            "contributors": [{"name": "TTP", "type": "Other"}],
            "license": "other-open",
            "publication_date": RELEASE_DATE,
            "version": "2026.08.25-unit13-r1",
            "language": "ind",
            "keywords": [
                "differential geometry",
                "smooth manifolds",
                "Indonesian translation",
                "open educational resources",
                "semantic HTML",
                "stable identifiers",
            ],
            "related_identifiers": [
                {
                    "identifier": "https://de.wikiversity.org/wiki/Kurs:Differentialgeometrie_(Osnabr%C3%BCck_2023)",
                    "relation": "isDerivedFrom",
                    "resource_type": "publication-book",
                    "scheme": "url",
                }
            ],
        }
    }
    validate_metadata(document)
    return document


def validate_metadata(document: dict[str, Any]) -> None:
    expected_keys = {
        "title", "description", "creators", "contributors", "license", "publication_date",
        "version", "language", "keywords", "related_identifiers",
    }
    if set(document) != {"metadata"} or not isinstance(document["metadata"], dict) or set(document["metadata"]) != expected_keys:
        raise RuntimeError("Zenodo metadata key contract mismatch")
    metadata = document["metadata"]
    if metadata["creators"] != [{"name": "Brenner, Holger"}] or metadata["contributors"] != [{"name": "TTP", "type": "Other"}]:
        raise RuntimeError("Zenodo creator/contributor contract mismatch")
    if metadata["license"] != "other-open" or metadata["language"] != "ind":
        raise RuntimeError("Zenodo rights/language contract mismatch")
    description = metadata["description"]
    for required in (
        "active_partial",
        "Kuliah 1–13",
        "Lembar Kerja 1–13",
        "Reader content and validated PDF/HTML bytes are unchanged from record 22096736; this revision corrects the resumable source package and its documentation.",
        "CC BY-SA 4.0",
        "Component media retain their file-specific rights; no blanket media license is inferred.",
    ):
        if required not in description:
            raise RuntimeError(f"Zenodo description lacks required phrase: {required}")
    if description.count(MODEL) != 1:
        raise RuntimeError("Zenodo description must contain the exact model string once")
    forbidden = re.compile(r"\bTTP\b|Translation and Transcription Project", re.I)
    if forbidden.search(metadata["title"]) or forbidden.search(description):
        raise RuntimeError("umbrella organization label leaked into title/description")
    serialized = json.dumps(document, ensure_ascii=False, sort_keys=True)
    if len(forbidden.findall(serialized)) != 1:
        raise RuntimeError("metadata must contain exactly one organization-label occurrence")
    if not isinstance(metadata["keywords"], list) or not metadata["keywords"] or any(not isinstance(item, str) or not item.strip() for item in metadata["keywords"]):
        raise RuntimeError("Zenodo keywords must be nonempty strings")
    scan_bytes("Zenodo metadata", serialized.encode("utf-8"))


def write_public_manifest(release: Path) -> None:
    manifest_inputs = PUBLIC_FILE_ORDER[:5]
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=["path", "bytes", "sha256"], lineterminator="\n")
    writer.writeheader()
    for name in manifest_inputs:
        writer.writerow({"path": name, **identity(release / name)})
    (release / MANIFEST_NAME).write_text(buffer.getvalue(), encoding="utf-8", newline="\n")
    checksum_inputs = PUBLIC_FILE_ORDER[:6]
    (release / CHECKSUMS_NAME).write_text(
        "".join(f"{sha256(release / name)}  {name}\n" for name in checksum_inputs),
        encoding="ascii",
        newline="\n",
    )


def verify_public_surfaces(release: Path, license_source: Path) -> list[dict[str, Any]]:
    actual_names = {path.name for path in release.iterdir() if path.is_file()}
    if actual_names != set(PUBLIC_FILE_ORDER) or any(path.is_dir() for path in release.iterdir()):
        raise RuntimeError("release directory does not contain exactly the seven public files")
    if (release / LICENSE_NAME).read_bytes() != license_source.read_bytes():
        raise RuntimeError("public LICENSE.md is not byte-identical to the approved Unit 13 license")
    rows = list(csv.DictReader(io.StringIO((release / MANIFEST_NAME).read_text(encoding="utf-8-sig"))))
    if [row.get("path") for row in rows] != list(PUBLIC_FILE_ORDER[:5]):
        raise RuntimeError("FILE_MANIFEST.csv inventory/order mismatch")
    for row in rows:
        actual = identity(release / row["path"])
        if (int(row["bytes"]), row["sha256"]) != (actual["bytes"], actual["sha256"]):
            raise RuntimeError(f"FILE_MANIFEST.csv identity mismatch: {row['path']}")
    checksum_lines = (release / CHECKSUMS_NAME).read_text(encoding="ascii").splitlines()
    expected_lines = [f"{sha256(release / name)}  {name}" for name in PUBLIC_FILE_ORDER[:6]]
    if checksum_lines != expected_lines:
        raise RuntimeError("CHECKSUMS.sha256 inventory/order mismatch")
    return [{"path": name, **identity(release / name)} for name in PUBLIC_FILE_ORDER]


def atomic_write_new(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp-unit13-stage")
    if path.exists() or temporary.exists():
        raise RuntimeError(f"refusing to overwrite existing output: {path}")
    temporary.write_bytes(payload)
    os.replace(temporary, path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output-dir", type=Path, default=Path(DEFAULT_OUTPUT_REL))
    parser.add_argument("--metadata", type=Path, default=Path(DEFAULT_METADATA_REL))
    parser.add_argument("--receipt", type=Path, default=Path(DEFAULT_RECEIPT_REL))
    args = parser.parse_args()

    root = args.root.resolve()
    if not root.is_dir():
        raise RuntimeError(f"project root not found: {root}")
    output_dir = resolve_output(root, args.output_dir)
    metadata_path = resolve_output(root, args.metadata)
    receipt_path = resolve_output(root, args.receipt)

    # This is deliberately the first material step. A stale one-reader backend
    # must never result in even a partial staging directory.
    gate, documents = collect_gate(root)
    if output_dir.exists() or metadata_path.exists() or receipt_path.exists():
        raise RuntimeError("refusing to overwrite existing release directory, metadata, or receipt")
    output_dir.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="unit13-release-stage-", dir=output_dir.parent) as temporary_name:
        temporary_root = Path(temporary_name)
        release = temporary_root / "release"
        source_tree = temporary_root / "source-package"
        release.mkdir()
        source_tree.mkdir()

        shutil.copyfile(project_path(root, PDF_REL), release / PDF_NAME)
        shutil.copyfile(project_path(root, LICENSE_SOURCE_REL), release / LICENSE_NAME)
        shutil.copyfile(project_path(root, NOTES_SOURCE_REL), release / NOTES_NAME)

        html_root = root / HTML_ROOT_REL
        html_mapping = directory_mapping(html_root)
        published_html_archive = project_path(root, HTML_PUBLISHED_ZIP_REL)
        html_archive = release / HTML_ZIP_NAME
        shutil.copyfile(published_html_archive, html_archive)
        html_zip = verify_zip(html_mapping, html_archive)
        html_zip["copied_byte_identically_from"] = identity(published_html_archive, HTML_PUBLISHED_ZIP_REL)
        if identity(html_archive) != identity(published_html_archive):
            raise RuntimeError("corrective revision changed the validated Unit 13 HTML archive bytes")
        html_zip["reproducible_second_serialization"] = verify_reproducible(html_mapping, html_archive, temporary_root)

        source_summary = copy_source_tree(root, source_tree, documents, gate)
        source_mapping = directory_mapping(source_tree)
        source_archive = release / SOURCE_ZIP_NAME
        create_zip(source_mapping, source_archive)
        source_zip = verify_zip(source_mapping, source_archive)
        source_zip["reproducible_second_serialization"] = verify_reproducible(source_mapping, source_archive, temporary_root)

        write_public_manifest(release)
        public_files = verify_public_surfaces(release, root / LICENSE_SOURCE_REL)
        privacy = privacy_scan_files((item["path"], release / str(item["path"])) for item in public_files if Path(str(item["path"])).suffix.lower() != ".zip")
        public_bytes = sum(int(item["bytes"]) for item in public_files)
        if public_bytes > MAX_PUBLIC_BYTES:
            raise RuntimeError(f"public release exceeds 500 MiB limit: {public_bytes} bytes")

        metadata = metadata_document()
        metadata_payload = json_bytes(metadata)
        scan_bytes("Zenodo metadata", metadata_payload)
        metadata_identity = {
            "path": metadata_path.relative_to(root).as_posix(),
            "bytes": len(metadata_payload),
            "sha256": hashlib.sha256(metadata_payload).hexdigest(),
        }
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
            "workflow": "o011-prepare-release-unit13-source-r1-v1",
            "status": "pass",
            "release_date": RELEASE_DATE,
            "coverage": "active_partial_through_unit_13",
            "model_identification": MODEL,
            "version": "2026.08.25-unit13-r1",
            "corrective_revision": {
                "predecessor_record_id": 22096736,
                "scope": "source_package_and_documentation_only",
                "pdf_unchanged_from_predecessor": True,
                "html_archive_unchanged_from_predecessor": True,
                "source_package_replaced": True,
            },
            "public_directory": output_dir.relative_to(root).as_posix(),
            "public_file_count": len(public_files),
            "public_file_order": list(PUBLIC_FILE_ORDER),
            "public_bytes": public_bytes,
            "total_public_bytes": public_bytes,
            "maximum_public_bytes": MAX_PUBLIC_BYTES,
            "under_500_mib": True,
            "public_files": public_files,
            "files": publisher_files,
            "metadata": metadata_identity,
            "input_bindings": gate,
            "zip_verification": {"html": html_zip, "source": source_zip},
            "source_package": source_summary,
            "manifest_contract": {
                "file_manifest_rows": list(PUBLIC_FILE_ORDER[:5]),
                "checksums_rows": list(PUBLIC_FILE_ORDER[:6]),
                "receipt_binds_all_seven_public_files": True,
            },
            "rights": {
                "text_and_adaptation": "CC BY-SA 4.0",
                "component_media": "mixed rights retained per component ledger and reader attribution surface",
                "non_endorsement_preserved": True,
                "license_byte_identical_to": LICENSE_SOURCE_REL,
            },
            "privacy_scan": {"status": "pass", **privacy},
            "deterministic_archives": {
                "status": "pass",
                "html": html_zip,
                "source": source_zip,
            },
            "deterministic_zip_timestamp": list(ZIP_TIMESTAMP),
            "excluded": [
                "raw provenance dumps and caches",
                "private locators and credentials",
                "temporary and duplicate builds",
                "remote publication receipts not yet created",
                "qa/unit-05/ZENODO_PUBLICATION_RECEIPT.md",
            ],
            "remote_state_mutated": False,
        }
        receipt_payload = json_bytes(receipt)
        scan_bytes("release-preparation receipt", receipt_payload)

        release.rename(output_dir)
        atomic_write_new(metadata_path, metadata_payload)
        atomic_write_new(receipt_path, receipt_payload)

    result = {
        "status": "pass",
        "public_directory": output_dir.relative_to(root).as_posix(),
        "public_files": len(PUBLIC_FILE_ORDER),
        "public_bytes": public_bytes,
        "metadata": metadata_path.relative_to(root).as_posix(),
        "receipt": receipt_path.relative_to(root).as_posix(),
        "remote_state_mutated": False,
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
