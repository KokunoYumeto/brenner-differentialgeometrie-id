#!/usr/bin/env python3
"""Strict cumulative PDF QA for the Indonesian O011 reader through Unit 7.

This is a Unit-7-specific adaptation of ``verify_through_unit06_pdf.py``.  It
reuses only that verifier's read-only PDF helpers; all bindings, page ranges,
source identities, media surfaces, and content assertions below are frozen for
the Unit 7 boundary.  A failed identity, missing closure, unsafe annotation,
or diagnostic is a hard failure.  The emitted JSON is deterministic for the
same bytes (no timestamps or machine paths are written).
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import pdfplumber
import pypdf
from pypdf import PdfReader


PROJECT_ROOT = Path(__file__).resolve().parent.parent
HELPER_PATH = Path(__file__).with_name("verify_through_unit06_pdf.py")
_spec = importlib.util.spec_from_file_location("_unit06_pdf_helpers", HELPER_PATH)
if _spec is None or _spec.loader is None:  # pragma: no cover - installation failure
    raise RuntimeError(f"cannot load bounded helper: {HELPER_PATH}")
_helpers = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_helpers)

# Read-only helper functions and constants from the already validated Unit 6
# verifier.  No Unit 6 main routine is called by this module.
sha256 = _helpers.sha256
bytes_sha = _helpers.bytes_sha
normalize_text = _helpers.normalize_text
deref = _helpers.dereference
indirect_key = _helpers.indirect_key
add_blocker = _helpers.add_blocker
collect_fonts = _helpers.collect_fonts
scan_raw_objects = _helpers.scan_raw_objects
collect_bookmarks = _helpers.collect_bookmarks
inspect_annotations = _helpers.inspect_annotations
scan_logs = _helpers.scan_logs
FORBIDDEN_TEXT = _helpers.FORBIDDEN_TEXT
FORBIDDEN_RAW = _helpers.FORBIDDEN_RAW
UNSAFE_ANNOTATION_SUBTYPES = _helpers.UNSAFE_ANNOTATION_SUBTYPES
SAFE_ACTIONS = _helpers.SAFE_ACTIONS
FATAL_LOG_PATTERNS = _helpers.FATAL_LOG_PATTERNS
WARNING_LOG_PATTERNS = _helpers.WARNING_LOG_PATTERNS


PDF_REL = "output/pdf/geometri-diferensial-manifold-mulus-hingga-unit-07-id.pdf"
OUTPUT_REL = "qa/unit-07/pdf_structural_qa.json"
BUILD_REL = "qa/unit-07/build.json"
PREFIX_BUILD_REL = "qa/unit-06/build.json"
PREFIX_PDF_REL = "output/pdf/geometri-diferensial-manifold-mulus-hingga-unit-06-id.pdf"
LECTURE_SOURCE_REL = "source/units/unit-07/lecture07.id.tex"
WORKSHEET_SOURCE_REL = "source/units/unit-07/worksheet07.id.tex"
LECTURE_TRANSLATION_REL = "qa/unit-07/lecture07_translation.json"
WORKSHEET_TRANSLATION_REL = "qa/unit-07/worksheet07_translation.json"
MEDIA_QA_REL = "qa/unit-07_media.json"
MEDIA_CONFIG_REL = "source/unit_media.json"
INTERACTIVE_REL = "source/unit07_interactive_media.json"
INTERACTIVE_QA_REL = "qa/unit-07/INTERACTIVE_MEDIA_QA.json"

EXPECTED_PDF = {"bytes": 4_950_232, "sha256": "8c2cf76230b45d66a8236c0cd92a048809ff5ec0cce343132dd902684cb05ec6"}
EXPECTED_PAGES = 117
EXPECTED_BUILD = {"bytes": 9_419, "sha256": "bb3b6bc858948291b0fa6a000c57761aef3d055fceae43000b303b1aaaacf08d"}
EXPECTED_PREFIX_BUILD = {"bytes": 5_146, "sha256": "253141e382d97605c374442604a57de2d3f7c5262c275131f46e00c4318ce480"}
EXPECTED_PREFIX_PDF = {"bytes": 4_765_606, "sha256": "40bf26d196ff04c38c6c99e8e9669a86bb5e6d31124b904b7ad154e7948cdec1"}
EXPECTED_LECTURE = {"bytes": 20_487, "sha256": "5faec64b0b20a6999e61fc3fa6a32db812e324d1e8a272d1978c67bc76c3c7b0"}
EXPECTED_WORKSHEET = {"bytes": 8_029, "sha256": "af223f98696a9353e7967d3ac150a8f2f5de3c49bef506c69fe0d452e7717658"}
EXPECTED_MEDIA_QA = {"bytes": 5_306, "sha256": "4bc9627f78dbe99f9223f08f6fcb33d8a7b7fed1cad888e8df0a54ee54916ef9"}
EXPECTED_MEDIA_CONFIG = {"bytes": 2_869, "sha256": "0f12d3057ca69c3ed8be75bcfdc391f31e9759c6b99d0cd48c1474630a0fe74d"}
EXPECTED_INTERACTIVE = {"bytes": 1_823, "sha256": "79a6509a87fa0da8f96527f798ca02b40d10c223300c439ee08dbdea1d2d3352"}
EXPECTED_INTERACTIVE_QA = {"bytes": 1_428, "sha256": "a6077a07a4ec03f1a33500781bf3256fa81da9d8efb091318fc6dd59dfdca193"}

EXPECTED_A4 = [595.276, 841.89]
EXPECTED_MARGIN_MM = 22.0
EXPECTED_MARGIN_POINTS = EXPECTED_MARGIN_MM * 72.0 / 25.4
EXPECTED_METADATA = {
    "/Author": "Holger Brenner, Terjemahan Bahasa Indonesia independen",
    "/Title": "Geometri Diferensial dan Manifold Mulus Pembaca kumulatif hingga Unit 7",
    "/Creator": "LaTeX with hyperref",
}
EXPECTED_LABELS = ["1", "i", "ii", "iii"] + [str(i) for i in range(1, 114)]
EXPECTED_MODEL = "OpenAI Codex gpt-5.6-sol, Ultra"
EXPECTED_EXERCISES = Counter({str(i): 1 for i in range(1, 20)})
EXPECTED_SOLUTIONS = Counter({"4": 1, "7": 1, "13": 1})
EXPECTED_GRADED = {
    "7.15": r"Soal 7\.15\.\s*\(3 poin\)",
    "7.16": r"Soal 7\.16\.\s*\(5 poin\)",
    "7.17": r"Soal 7\.17\.\s*\(8 poin\)",
}

EXPECTED_TRANSLATIONS = {
    LECTURE_TRANSLATION_REL: {
        "target": LECTURE_SOURCE_REL,
        "target_identity": EXPECTED_LECTURE,
        "correction": "O011-TRANS-0070",
    },
    WORKSHEET_TRANSLATION_REL: {
        "target": WORKSHEET_SOURCE_REL,
        "target_identity": EXPECTED_WORKSHEET,
        "correction": "O011-TRANS-0071",
    },
}
EXPECTED_SOLUTION_FILES = {
    "source/units/unit-07/worksheet07_exercise04_solution.id.tex": {"bytes": 898, "sha256": "fcae797a689655b486d9ffed1fdede2059b0f15f3842cc5f38e1ba21d4499822"},
    "source/units/unit-07/worksheet07_exercise07_solution.id.tex": {"bytes": 1_695, "sha256": "b85aae3fecf5ff5c316fcd2f496134a2d60203b468d112b97ccda701bb77a49a"},
    "source/units/unit-07/worksheet07_exercise13_solution.id.tex": {"bytes": 332, "sha256": "b23f0e52a315ac6d47d1849f06d426e5e1815a244cc39c1c6ce741435ba20f37"},
}
CORRECTION_FILES = {
    "00_control/LECTURE07_PROTECTED_CORRECTIONS.json": {"bytes": 667, "sha256": "e4f2af5750074228b03dc7cd3ce5eaa0fccae03a1e2c3e5fc11d7efafe17fd70", "id": "O011-TRANS-0070"},
    "00_control/WORKSHEET07_PROTECTED_CORRECTIONS.json": {"bytes": 642, "sha256": "a3fb4ee0fbed8ba0bd0e3a5ef05dd625468d7c16f30004e49815a50506b291c6", "id": "O011-TRANS-0071"},
}
UNIT7_SOURCE_URIS = {
    "Stereographic projection in 3D.png": "https://commons.wikimedia.org/wiki/File:Stereographic_projection_in_3D.png",
    "Manifold zahyou3.png": "https://commons.wikimedia.org/wiki/File:Manifold_zahyou3.png",
    "Circle - black simple.svg": "https://commons.wikimedia.org/wiki/File:Circle_-_black_simple.svg",
}
GIF_URIS = {
    "Aufgabe75.22.1.gif": "https://commons.wikimedia.org/wiki/File:Aufgabe75.22.1.gif",
    "Aufgabe75.22.2.gif": "https://commons.wikimedia.org/wiki/File:Aufgabe75.22.2.gif",
}
EXPECTED_GIFS = {
    "Aufgabe75.22.1.gif": {"bytes": 200_686, "sha256": "dae99541dcac8721909366df89d67ee7ddc46ff49c24750c71f7d1e00245acca"},
    "Aufgabe75.22.2.gif": {"bytes": 1_640_205, "sha256": "091b7d19856eb36aaf704bd23e26e46d0119ed97fcd736fb68cababa7ab7e942"},
}


def relative(path: Path) -> str:
    return path.resolve().relative_to(PROJECT_ROOT).as_posix()


def identity_or_none(path: Path) -> dict[str, object] | None:
    return bytes_sha(path) if path.is_file() else None


def bind_file(rel: str, expected: dict[str, object], blockers: list[str], label: str | None = None) -> dict[str, object]:
    path = PROJECT_ROOT / rel
    actual = identity_or_none(path)
    if actual != expected:
        blockers.append(f"{label or rel} identity mismatch: {actual}")
    return {"path": rel, "expected": expected, "actual": actual, "matches": actual == expected}


def verify_build_binding(blockers: list[str]) -> tuple[dict[str, Any], dict[str, object]]:
    path = PROJECT_ROOT / BUILD_REL
    identity = identity_or_none(path)
    if identity != EXPECTED_BUILD:
        blockers.append(f"Unit 7 build receipt identity mismatch: {identity}")
    build = json.loads(path.read_text(encoding="utf-8"))
    if build.get("workflow") != "o011-through-unit07-pdf-build-v1":
        blockers.append("wrong Unit 7 build workflow")
    if build.get("deterministic_clean_cycles") is not True:
        blockers.append("build does not assert deterministic clean cycles")
    if build.get("cumulative_prefix_receipt") != PREFIX_BUILD_REL:
        blockers.append("wrong cumulative Unit 6 prefix receipt")
    expected_output = {"path": PDF_REL, **EXPECTED_PDF}
    if build.get("output") != expected_output:
        blockers.append(f"build output binding mismatch: {build.get('output')}")
    cycles = build.get("cycles", [])
    if len(cycles) != 2:
        blockers.append(f"expected exactly two clean cycles, found {len(cycles)}")
    cycle_checks: list[dict[str, object]] = []
    for expected_number, cycle in enumerate(cycles, start=1):
        actual = identity_or_none(PROJECT_ROOT / str(cycle.get("pdf", "")))
        passed = bool(
            cycle.get("cycle") == expected_number
            and cycle.get("bytes") == EXPECTED_PDF["bytes"]
            and cycle.get("sha256") == EXPECTED_PDF["sha256"]
            and actual == EXPECTED_PDF
        )
        cycle_checks.append({"cycle": expected_number, "path": cycle.get("pdf"), "actual": actual, "passed": passed})
        if not passed:
            blockers.append(f"clean cycle {expected_number} is not bound to the exact Unit 7 PDF")
    if len(cycle_checks) == 2 and cycle_checks[0]["actual"] != cycle_checks[1]["actual"]:
        blockers.append("two clean-cycle PDF identities differ")
    input_checks: list[dict[str, object]] = []
    for declared in build.get("inputs", []):
        rel = str(declared.get("path", ""))
        candidate = (PROJECT_ROOT / rel).resolve()
        within = PROJECT_ROOT == candidate or PROJECT_ROOT in candidate.parents
        actual = identity_or_none(candidate) if within else None
        expected = {"bytes": declared.get("bytes"), "sha256": declared.get("sha256")}
        passed = bool(actual and actual == expected)
        input_checks.append({"path": rel, "declared": expected, "actual": actual, "passed": passed})
        if not passed:
            blockers.append(f"build input identity mismatch: {rel}")
    log_scan = scan_logs(build, blockers)
    return build, {"receipt": {"path": BUILD_REL, **(identity or {})}, "cycles": cycle_checks, "inputs": input_checks, "log_scan": log_scan}


def verify_prefix(reader: PdfReader, plumber_pages: list[Any], blockers: list[str]) -> dict[str, object]:
    prefix_receipt = bind_file(PREFIX_BUILD_REL, EXPECTED_PREFIX_BUILD, blockers, "Unit 6 prefix build receipt")
    prefix_path = PROJECT_ROOT / PREFIX_PDF_REL
    prefix_identity = identity_or_none(prefix_path)
    if prefix_identity != EXPECTED_PREFIX_PDF:
        blockers.append(f"Unit 6 prefix PDF identity mismatch: {prefix_identity}")
    prefix_reader = PdfReader(str(prefix_path))
    if len(prefix_reader.pages) != 105:
        blockers.append(f"Unit 6 prefix page count is {len(prefix_reader.pages)}, expected 105")
    # Physical pages 5--101 are the complete Unit 1--6 reader body.  Compare
    # streams and independent text extraction so later pages cannot mask drift.
    start, stop = 4, 101  # zero-based [physical 5, physical 101]
    stream_mismatches: list[int] = []
    left_hashes: list[str] = []
    right_hashes: list[str] = []
    for index in range(start, stop):
        left = prefix_reader.pages[index].get_contents().get_data()
        right = reader.pages[index].get_contents().get_data()
        left_hashes.append(hashlib.sha256(left).hexdigest())
        right_hashes.append(hashlib.sha256(right).hexdigest())
        if left != right:
            stream_mismatches.append(index + 1)
    with pdfplumber.open(prefix_path) as prefix_plumber:
        text_mismatches = [
            index + 1
            for index in range(start, stop)
            if (prefix_plumber.pages[index].extract_text() or "") != (plumber_pages[index].extract_text() or "")
        ]
        prefix_sizes = [[round(float(page.width), 3), round(float(page.height), 3)] for page in prefix_plumber.pages[start:stop]]
    cumulative_sizes = [[round(float(page.width), 3), round(float(page.height), 3)] for page in plumber_pages[start:stop]]
    passed = not stream_mismatches and not text_mismatches and prefix_sizes == cumulative_sizes
    if stream_mismatches:
        blockers.append(f"Unit 1--6 content-stream prefix mismatches: {stream_mismatches}")
    if text_mismatches:
        blockers.append(f"Unit 1--6 pdfplumber text prefix mismatches: {text_mismatches}")
    if prefix_sizes != cumulative_sizes:
        blockers.append("Unit 1--6 page-size prefix mismatch")
    return {
        "prefix_receipt": prefix_receipt,
        "prefix_pdf": {"path": PREFIX_PDF_REL, **(prefix_identity or {}), "pages": len(prefix_reader.pages)},
        "compared_physical_pages": {"first": 5, "last": 101, "count": stop - start},
        "content_stream_aggregate_sha256_prefix": hashlib.sha256("\n".join(left_hashes).encode("ascii")).hexdigest(),
        "content_stream_aggregate_sha256_cumulative": hashlib.sha256("\n".join(right_hashes).encode("ascii")).hexdigest(),
        "content_stream_mismatch_pages": stream_mismatches,
        "pdfplumber_text_mismatch_pages": text_mismatches,
        "page_sizes_equal": prefix_sizes == cumulative_sizes,
        "passed": passed,
    }


def verify_translation_and_media(blockers: list[str]) -> dict[str, object]:
    files: dict[str, object] = {}
    for rel, spec in EXPECTED_TRANSLATIONS.items():
        path = PROJECT_ROOT / rel
        actual = bind_file(rel, {"bytes": path.stat().st_size, "sha256": sha256(path)} if path.is_file() else {"bytes": -1, "sha256": ""}, blockers, rel)
        data = json.loads(path.read_text(encoding="utf-8"))
        target = str(data.get("target", ""))
        if data.get("status") != "pass" or target != spec["target"]:
            blockers.append(f"translation receipt closure failure: {rel}")
        if data.get("target_bytes") != spec["target_identity"]["bytes"] or data.get("target_sha256") != spec["target_identity"]["sha256"]:
            blockers.append(f"translation receipt target identity mismatch: {rel}")
        if spec["correction"] not in data.get("declared_corrections", []):
            blockers.append(f"translation receipt missing correction binding: {rel}")
        files[rel] = {"identity": actual, "status": data.get("status"), "target": target, "declared_corrections": data.get("declared_corrections", [])}
    for rel, expected in EXPECTED_SOLUTION_FILES.items():
        files[rel] = bind_file(rel, expected, blockers, "source-supplied solution")
    for rel, spec in CORRECTION_FILES.items():
        entry = bind_file(rel, {"bytes": spec["bytes"], "sha256": spec["sha256"]}, blockers, "protected correction manifest")
        data = json.loads((PROJECT_ROOT / rel).read_text(encoding="utf-8"))
        ids = [str(row.get("correction_id")) for row in data.get("allowed_deltas", [])]
        if spec["id"] not in ids:
            blockers.append(f"protected correction manifest missing {spec['id']}: {rel}")
        files[rel] = {"identity": entry, "correction_ids": ids}
    media_entry = bind_file(MEDIA_QA_REL, EXPECTED_MEDIA_QA, blockers, "Unit 7 media QA")
    config_entry = bind_file(MEDIA_CONFIG_REL, EXPECTED_MEDIA_CONFIG, blockers, "media configuration")
    interactive_entry = bind_file(INTERACTIVE_REL, EXPECTED_INTERACTIVE, blockers, "interactive media manifest")
    interactive_qa_entry = bind_file(INTERACTIVE_QA_REL, EXPECTED_INTERACTIVE_QA, blockers, "interactive media QA")
    media = json.loads((PROJECT_ROOT / MEDIA_QA_REL).read_text(encoding="utf-8"))
    config = json.loads((PROJECT_ROOT / MEDIA_CONFIG_REL).read_text(encoding="utf-8"))
    if media.get("media_config_sha256") != EXPECTED_MEDIA_CONFIG["sha256"]:
        blockers.append("Unit 7 media QA is bound to the wrong media configuration")
    if media.get("source_count") != 3 or media.get("derivative_count") != 1 or len(media.get("media", [])) != 3:
        blockers.append("Unit 7 static media census is not 3 sources / 1 print derivative")
    static_checks = []
    for row in media.get("media", []):
        rel = str(row.get("canonical_path", ""))
        expected = {"bytes": row.get("canonical_bytes"), "sha256": row.get("canonical_sha256")}
        actual = identity_or_none(PROJECT_ROOT / rel)
        passed = actual == expected
        static_checks.append({"filename": row.get("filename"), "path": rel, "declared": expected, "actual": actual, "passed": passed})
        if not passed:
            blockers.append(f"Unit 7 static media identity mismatch: {rel}")
    interactive = json.loads((PROJECT_ROOT / INTERACTIVE_REL).read_text(encoding="utf-8"))
    interactive_qa = json.loads((PROJECT_ROOT / INTERACTIVE_QA_REL).read_text(encoding="utf-8"))
    if interactive_qa.get("status") != "pass" or interactive_qa.get("preserved_locally") is not True:
        blockers.append("interactive media QA does not pass/preserve local assets")
    interactive_checks = []
    for row in interactive.get("assets", []):
        filename = str(row.get("filename")); expected = EXPECTED_GIFS.get(filename)
        actual = identity_or_none(PROJECT_ROOT / "authority/media" / filename)
        passed = bool(expected and actual == expected and row.get("bytes") == expected["bytes"] and row.get("sha256") == expected["sha256"])
        interactive_checks.append({"filename": filename, "declared": {"bytes": row.get("bytes"), "sha256": row.get("sha256")}, "actual": actual, "passed": passed})
        if not passed:
            blockers.append(f"interactive asset identity mismatch: {filename}")
    if len(interactive.get("assets", [])) != 2:
        blockers.append("interactive manifest does not contain exactly two GIF assets")
    return {
        "translation_receipts": files,
        "media_qa": media_entry,
        "media_config": config_entry,
        "media_config_units": sum(1 for row in config if isinstance(row, dict)) if isinstance(config, list) else None,
        "static_media_checks": static_checks,
        "interactive_manifest": interactive_entry,
        "interactive_qa": interactive_qa_entry,
        "interactive_checks": interactive_checks,
    }


def inspect_punctuation_geometry(plumber_pages: list[Any]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    visual: list[dict[str, object]] = []
    concatenated: list[dict[str, object]] = []
    punctuation = {".", ",", ";", ":"}
    terminals = {".", "!", "?"}
    for page_number in range(103, 114):
        chars = plumber_pages[page_number - 1].chars
        for index, char in enumerate(chars):
            text = str(char.get("text", ""))
            if text in punctuation:
                nearest = min((_helpers.box_distance(char, other) for j, other in enumerate(chars) if j != index and str(other.get("text", "")).strip()), default=float("inf"))
                if nearest > 12.0:
                    visual.append({"page": page_number, "text": text, "nearest_glyph_distance_points": round(nearest, 3)})
            if text not in terminals:
                continue
            for j, other in enumerate(chars):
                if j == index:
                    continue
                other_text = str(other.get("text", ""))
                if not other_text or not other_text[0].isupper():
                    continue
                vertical = max(float(char["top"]), float(other["top"])) - min(float(char["bottom"]), float(other["bottom"]))
                gap = float(other["x0"]) - float(char["x1"])
                if vertical <= 1.5 and 0.0 <= gap <= 1.0:
                    concatenated.append({"page": page_number, "punctuation": text, "next_character": other_text, "gap_points": round(gap, 3)})
    return visual, concatenated


def main() -> int:
    blockers: list[str] = []
    warnings: list[str] = []
    limitations: list[str] = []
    script_path = Path(__file__).resolve()
    pdf_path = PROJECT_ROOT / PDF_REL
    output_path = PROJECT_ROOT / OUTPUT_REL
    if not pdf_path.is_file():
        blockers.append(f"missing target PDF: {PDF_REL}")
        receipt = {"schema_version": 1, "workflow": "o011-through-unit07-pdf-structural-qa-v1", "verdict": "FAIL", "passed": False, "blockers": blockers}
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
        print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True))
        return 1

    source_binding = verify_translation_and_media(blockers)
    build, build_binding = verify_build_binding(blockers)
    pdf_identity = identity_or_none(pdf_path)
    if pdf_identity != EXPECTED_PDF:
        blockers.append(f"target PDF identity mismatch: {pdf_identity}")
    reader = PdfReader(str(pdf_path))
    catalog = reader.root_object
    actual_pages = len(reader.pages)
    if actual_pages != EXPECTED_PAGES:
        blockers.append(f"page count is {actual_pages}, expected {EXPECTED_PAGES}")
    if reader.is_encrypted:
        blockers.append("PDF is encrypted")
    media_sizes = [[round(float(p.mediabox.width), 3), round(float(p.mediabox.height), 3)] for p in reader.pages]
    crop_sizes = [[round(float(p.cropbox.width), 3), round(float(p.cropbox.height), 3)] for p in reader.pages]
    rotations = [int(p.get("/Rotate", 0) or 0) % 360 for p in reader.pages]
    if not all(size == EXPECTED_A4 for size in media_sizes):
        blockers.append("one or more MediaBox dimensions are not A4")
    if not all(size == EXPECTED_A4 for size in crop_sizes):
        blockers.append("one or more CropBox dimensions are not A4")
    if any(rotations):
        blockers.append("one or more pages are rotated")
    page_labels = [str(item) for item in reader.page_labels]
    if page_labels != EXPECTED_LABELS:
        blockers.append("page-label sequence does not match front matter plus body labels 1--113")
    catalog_language = str(catalog.get("/Lang", ""))
    if catalog_language != "id-ID":
        blockers.append(f"catalog /Lang is {catalog_language!r}")
    metadata = {str(k): str(v) for k, v in (reader.metadata or {}).items()}
    metadata_mismatches = {k: {"expected": v, "actual": metadata.get(k)} for k, v in EXPECTED_METADATA.items() if metadata.get(k) != v}
    volatile_metadata = sorted(k for k in ("/CreationDate", "/ModDate") if k in metadata)
    if metadata_mismatches:
        blockers.append(f"metadata mismatch: {metadata_mismatches}")
    if volatile_metadata or reader.trailer.get("/ID"):
        blockers.append("volatile metadata/trailer identity present")

    pypdf_text = [p.extract_text() or "" for p in reader.pages]
    pypdf_empty = [i + 1 for i, text in enumerate(pypdf_text) if not text.strip()]
    with pdfplumber.open(pdf_path) as plumber:
        plumber_pages = list(plumber.pages)
        plumber_text = [p.extract_text() or "" for p in plumber_pages]
        plumber_sizes = [[round(float(p.width), 3), round(float(p.height), 3)] for p in plumber_pages]
        if len(plumber_pages) != actual_pages:
            blockers.append("pdfplumber page count differs from pypdf")
        plumber_empty = [i + 1 for i, text in enumerate(plumber_text) if not text.strip()]
        if pypdf_empty or plumber_empty:
            blockers.append(f"empty extracted pages: pypdf={pypdf_empty}, pdfplumber={plumber_empty}")
        geometry_source = PROJECT_ROOT / "build/through-unit-07.tex"
        geometry_line = r"\usepackage[a4paper,margin=22mm,headheight=15pt]{geometry}"
        geometry_present = geometry_line in geometry_source.read_text(encoding="utf-8")
        parts = {21, 37, 54, 70, 83, 102}
        content_pages = [p for p in list(range(6, 102)) + list(range(103, 114)) if p not in parts]
        expected_right = EXPECTED_A4[0] - EXPECTED_MARGIN_POINTS
        left_pages: list[int] = []
        right_pages: list[int] = []
        overruns: list[dict[str, object]] = []
        outside: list[dict[str, object]] = []
        page_layout: list[dict[str, object]] = []
        for page_number in content_pages:
            page = plumber_pages[page_number - 1]
            words = [w for w in page.extract_words() if float(w["top"]) >= 50.0 and float(w["bottom"]) <= 790.0]
            min_x = min((float(w["x0"]) for w in words), default=None)
            max_x = max((float(w["x1"]) for w in words), default=None)
            if min_x is not None and EXPECTED_MARGIN_POINTS - 3.0 <= min_x <= EXPECTED_MARGIN_POINTS + 1.0:
                left_pages.append(page_number)
            if any(abs(float(w["x1"]) - expected_right) <= 3.0 for w in words):
                right_pages.append(page_number)
            out = [w for w in words if float(w["x0"]) < EXPECTED_MARGIN_POINTS - 4.0 or float(w["x1"]) > expected_right + 4.0]
            off = [w for w in words if float(w["x0"]) < -0.5 or float(w["x1"]) > float(page.width) + 0.5 or float(w["top"]) < -0.5 or float(w["bottom"]) > float(page.height) + 0.5]
            if out:
                overruns.append({"page": page_number, "count": len(out), "samples": [str(w.get("text", "")) for w in out[:8]]})
            if off:
                outside.append({"page": page_number, "count": len(off), "samples": [str(w.get("text", "")) for w in off[:8]]})
            page_layout.append({"page": page_number, "body_min_x": None if min_x is None else round(min_x, 3), "body_max_x": None if max_x is None else round(max_x, 3)})
        required_left = int(len(content_pages) * 0.95)
        required_right = int(len(content_pages) * 0.60)
        if not geometry_present:
            blockers.append("hash-bound wrapper source does not declare geometry margin=22mm")
        if len(left_pages) < required_left:
            blockers.append(f"too few body pages exhibit 22 mm left anchor: {len(left_pages)} < {required_left}")
        if len(right_pages) < required_right:
            blockers.append(f"too few body pages reach symmetric 22 mm right anchor: {len(right_pages)} < {required_right}")
        prefix_integrity = verify_prefix(reader, plumber_pages, blockers)
        visual_orphans, sentence_concat = inspect_punctuation_geometry(plumber_pages)
    if plumber_sizes and not all(size == EXPECTED_A4 for size in plumber_sizes):
        blockers.append("pdfplumber found non-A4 pages")
    if visual_orphans:
        blockers.append(f"visually isolated Unit 7 punctuation glyphs: {visual_orphans}")
    if sentence_concat:
        blockers.append(f"Unit 7 sentence punctuation concatenation: {sentence_concat}")
    if overruns:
        warnings.append(f"content exceeds nominal 22 mm body box on pages {[x['page'] for x in overruns]}")
    if outside:
        warnings.append(f"extracted word geometry extends outside MediaBox on pages {[x['page'] for x in outside]}")

    full_text = "\n".join(pypdf_text)
    normalized_full = normalize_text(full_text)
    normalized_pages = [normalize_text(x) for x in pypdf_text]
    required_patterns = {
        "work title": r"\bGeometri Diferensial dan Manifold Mulus\b",
        "cumulative boundary": r"\bPembaca kumulatif hingga Unit 7\b",
        "Unit 7 part": r"\bBagian VII\s+Unit 7\b",
        "Unit 7 lecture": r"\bKuliah 7: Konsep sebuah manifold\b",
        "Unit 7 worksheet": r"\bLembar Kerja 7\b",
        "source-supplied solutions": r"\bSolusi yang disediakan oleh sumber\b",
        "text license": r"\bCC BY-SA 4\.0\b",
        "media rights": r"\bAtribusi dan Hak Media\b",
    }
    missing_required = [label for label, pattern in required_patterns.items() if not re.search(pattern, normalized_full)]
    if missing_required:
        blockers.append(f"missing required reader text: {missing_required}")
    unit7_part_pages = [i + 1 for i, text in enumerate(normalized_pages) if re.search(required_patterns["Unit 7 part"], text)]
    if unit7_part_pages != [102]:
        blockers.append(f"Unit 7 part boundary is not exactly physical page 102: {unit7_part_pages}")
    worksheet_text = normalize_text("\n".join(pypdf_text[108:111]))
    solution_text = normalize_text("\n".join(pypdf_text[111:113]))
    exercise_counts = Counter(re.findall(r"(?<!Solusi )\bSoal 7\.(\d+)\.(?!\d)", worksheet_text))
    solution_counts = Counter(re.findall(r"\bSolusi Soal 7\.(\d+)(?!\d)", solution_text))
    if exercise_counts != EXPECTED_EXERCISES:
        blockers.append(f"Unit 7 exercise headings mismatch: {dict(sorted(exercise_counts.items()))}")
    if solution_counts != EXPECTED_SOLUTIONS:
        blockers.append(f"Unit 7 source-supplied solution headings mismatch: {dict(sorted(solution_counts.items()))}")
    missing_graded = [label for label, pattern in EXPECTED_GRADED.items() if not re.search(pattern, worksheet_text)]
    if missing_graded:
        blockers.append(f"missing Unit 7 graded point markers: {missing_graded}")
    model_count = normalized_full.count(EXPECTED_MODEL)
    if model_count != 1:
        blockers.append(f"exact model provenance occurs {model_count} times, expected once")
    media_text_checks = {
        "Stereographic projection in 3D.png": "Stereographic projection in 3D.png" in normalized_full,
        "Manifold zahyou3.png": "Manifold zahyou3.png" in normalized_full,
        "Circle - black simple.svg": "Circle - black simple.svg" in normalized_full,
        "Mark.Howison": "Mark.Howison" in normalized_full,
        "132ninme": "132ninme" in normalized_full,
        "Dakdada": "Dakdada" in normalized_full,
    }
    missing_media_text = [key for key, present in media_text_checks.items() if not present]
    if missing_media_text:
        blockers.append(f"missing Unit 7 media/credit text: {missing_media_text}")
    bookmarks, bookmark_errors = collect_bookmarks(reader)
    bookmark_titles = [str(x["title"]) for x in bookmarks]
    required_bookmarks = {
        "Unit 7 part": r"^VII Unit 7$",
        "Unit 7 lecture": r"^Kuliah 7$",
        "Unit 7 worksheet": r"^Lembar Kerja 7$",
        "source solutions": r"^Solusi yang disediakan oleh sumber$",
        "media rights": r"^Atribusi dan Hak Media$",
        "Unit 7 media": r"^Unit 7$",
    }
    missing_bookmarks = [label for label, pattern in required_bookmarks.items() if not any(re.search(pattern, title) for title in bookmark_titles)]
    unresolved = [x for x in bookmarks if x["page"] is None]
    out_of_range = [x for x in bookmarks if isinstance(x["page"], int) and not 1 <= int(x["page"]) <= actual_pages]
    if bookmark_errors or missing_bookmarks or unresolved or out_of_range:
        blockers.append(f"bookmark closure failure: errors={bookmark_errors}, missing={missing_bookmarks}, unresolved={unresolved}, out_of_range={out_of_range}")
    fonts = collect_fonts(reader)
    fonts_without_tounicode = sorted(k for k, v in fonts.items() if not v["to_unicode"])
    fonts_not_embedded = sorted(k for k, v in fonts.items() if not v["embedded"])
    if fonts_without_tounicode:
        blockers.append(f"fonts without ToUnicode: {fonts_without_tounicode}")
    if fonts_not_embedded:
        blockers.append(f"fonts not embedded: {fonts_not_embedded}")
    subtypes, uris, internal_links, unsafe_actions, attachments = inspect_annotations(reader)
    uri_counts = {uri: uris[uri] for uri in sorted(set(UNIT7_SOURCE_URIS.values()) | set(GIF_URIS.values()))}
    for filename, uri in {**UNIT7_SOURCE_URIS, **GIF_URIS}.items():
        if uris[uri] < 1:
            blockers.append(f"required Unit 7 media URI absent: {filename}")
    license_uri = "https://creativecommons.org/licenses/by-sa/3.0/"
    if uris[license_uri] < 1:
        blockers.append("Unit 7 CC BY-SA 3.0 license URI absent")
    if unsafe_actions:
        blockers.append(f"unsafe annotation actions: {unsafe_actions}")
    unsafe_subtypes = sorted(k for k in subtypes if k in UNSAFE_ANNOTATION_SUBTYPES)
    names = deref(catalog.get("/Names", {})) or {}
    has_javascript = bool(names.get("/JavaScript"))
    has_embedded_files = bool(names.get("/EmbeddedFiles"))
    has_acroform = bool(catalog.get("/AcroForm")) or bool(reader.get_fields() or {})
    has_associated_files = bool(catalog.get("/AF"))
    has_collection = bool(catalog.get("/Collection"))
    unsafe_active = bool(has_javascript or has_embedded_files or has_acroform or has_associated_files or has_collection or attachments or unsafe_subtypes or unsafe_actions)
    if unsafe_active:
        blockers.append("PDF contains active, embedded, form, portfolio, or unsafe annotation content")
    extracted_hits = {label: sorted(set(m.group(0) for m in pattern.finditer(full_text))) for label, pattern in FORBIDDEN_TEXT.items() if pattern.search(full_text)}
    metadata_text = "\n".join(metadata.values())
    metadata_hits = {label: sorted(set(m.group(0) for m in pattern.finditer(metadata_text))) for label, pattern in FORBIDDEN_TEXT.items() if pattern.search(metadata_text)}
    raw_hits, stream_count, decoded_bytes, stream_errors = scan_raw_objects(reader, pdf_path)
    raw_hits = {k: v for k, v in raw_hits.items() if v}
    if extracted_hits or metadata_hits or raw_hits or stream_errors:
        blockers.append(f"privacy/residue scan failure: text={extracted_hits}, metadata={metadata_hits}, raw={raw_hits}, stream_errors={stream_errors}")
    mark_info = deref(catalog.get("/MarkInfo", {})) or {}
    tagged = bool(catalog.get("/StructTreeRoot")) and bool(mark_info.get("/Marked"))
    if not tagged:
        limitations.append(f"PDF is untagged; all {len(fonts)} fonts have ToUnicode and all {actual_pages} pages are extractable through pypdf/pdfplumber; semantic HTML remains the structured accessibility surface.")
    if build_binding["log_scan"]["overfull_hits"]:
        warnings.append("bound build logs record overfull boxes")
    if build_binding["log_scan"]["underfull_hits"]:
        warnings.append("bound build logs record underfull-box warnings")
    named_destinations = list(reader.named_destinations.keys())
    duplicate_named = len(named_destinations) != len(set(named_destinations))
    if duplicate_named:
        blockers.append("duplicate names detected in PDF named destinations")
    passed = not blockers
    if passed and warnings and limitations:
        verdict = "PASS_WITH_WARNINGS_AND_DOCUMENTED_LIMITATION"
    elif passed and warnings:
        verdict = "PASS_WITH_WARNINGS"
    elif passed and limitations:
        verdict = "PASS_WITH_DOCUMENTED_LIMITATION"
    else:
        verdict = "PASS" if passed else "FAIL"
    receipt = {
        "schema_version": 1,
        "workflow": "o011-through-unit07-pdf-structural-qa-v1",
        "verdict": verdict,
        "passed": passed,
        "execution_binding": {"project_root": ".", "script": {"path": relative(script_path), **bytes_sha(script_path)}, "pdf": {"path": PDF_REL, **EXPECTED_PDF}, "output": OUTPUT_REL},
        "build_binding": build_binding,
        "source_and_media_binding": source_binding,
        "prefix_integrity": prefix_integrity,
        "pdf": {"path": PDF_REL, **(pdf_identity or {}), "pages": actual_pages, "media_box_points": media_sizes[0] if media_sizes else None, "crop_box_points": crop_sizes[0] if crop_sizes else None, "all_media_boxes_a4": bool(media_sizes) and all(x == EXPECTED_A4 for x in media_sizes), "all_crop_boxes_a4": bool(crop_sizes) and all(x == EXPECTED_A4 for x in crop_sizes), "all_rotations_zero": not any(rotations), "page_labels": page_labels, "page_labels_match": page_labels == EXPECTED_LABELS, "catalog_language": catalog_language, "encrypted": reader.is_encrypted, "metadata": metadata, "metadata_mismatches": metadata_mismatches, "volatile_metadata_keys": volatile_metadata, "trailer_id_present": bool(reader.trailer.get("/ID")), "tagged": tagged, "has_structure_tree": bool(catalog.get("/StructTreeRoot")), "mark_info_marked": bool(mark_info.get("/Marked"))},
        "layout": {"expected_wrapper_margin_mm": EXPECTED_MARGIN_MM, "expected_wrapper_margin_points": round(EXPECTED_MARGIN_POINTS, 6), "expected_right_anchor_points": round(EXPECTED_A4[0] - EXPECTED_MARGIN_POINTS, 6), "content_pages_checked": content_pages, "left_anchor_pages": left_pages, "minimum_required_left_anchor_pages": required_left, "right_anchor_pages": right_pages, "minimum_required_right_anchor_pages": required_right, "centered_wrapper_passed": geometry_present and len(left_pages) >= required_left and len(right_pages) >= required_right, "page_body_extents": page_layout, "nominal_margin_overruns": overruns, "outside_media_box": outside},
        "accessibility": {"pypdf_version": pypdf.__version__, "pdfplumber_version": pdfplumber.__version__, "pypdf_pages_with_extractable_text": actual_pages - len(pypdf_empty), "pypdf_empty_text_pages": pypdf_empty, "pypdf_page_text_characters": [len(x) for x in pypdf_text], "pdfplumber_pages_with_extractable_text": len(plumber_text) - len(plumber_empty), "pdfplumber_empty_text_pages": plumber_empty, "unique_fonts": len(fonts), "fonts_with_tounicode": sum(1 for x in fonts.values() if x["to_unicode"]), "fonts_without_tounicode": fonts_without_tounicode, "fonts_not_embedded": fonts_not_embedded, "fonts": fonts},
        "content_closure": {"missing_required_text": missing_required, "unit7_part_physical_pages": unit7_part_pages, "worksheet_physical_pages_checked": [109, 110, 111], "solution_physical_pages_checked": [112, 113], "exercise_heading_counts": dict(sorted(exercise_counts.items(), key=lambda x: int(x[0]))), "expected_exercise_heading_counts": dict(sorted(EXPECTED_EXERCISES.items(), key=lambda x: int(x[0]))), "solution_heading_counts": dict(sorted(solution_counts.items(), key=lambda x: int(x[0]))), "expected_solution_heading_counts": dict(sorted(EXPECTED_SOLUTIONS.items(), key=lambda x: int(x[0]))), "missing_graded_markers": missing_graded, "model_provenance": {"exact_text": EXPECTED_MODEL, "occurrences": model_count}, "media_text_presence": media_text_checks, "missing_media_text": missing_media_text},
        "interactive_surface": {"gif_uri_counts": {name: uris[uri] for name, uri in GIF_URIS.items()}, "caption_presence": {"Konstruktion der Objekte": "Konstruktion der Objekte" in normalized_full, "Variation von S": "Variation von S" in normalized_full}},
        "bookmarks": {"count": len(bookmarks), "records": bookmarks, "errors": bookmark_errors, "unresolved": unresolved, "out_of_range": out_of_range, "missing_required": missing_bookmarks, "named_destination_count": len(named_destinations), "duplicate_named_destinations": duplicate_named},
        "links_and_active_content": {"external_uri_count": sum(uris.values()), "external_uri_counts": dict(sorted(uris.items())), "required_unit7_uri_counts": uri_counts, "internal_link_count": internal_links, "annotation_subtype_counts": dict(sorted(subtypes.items())), "unsafe_actions": unsafe_actions, "unsafe_annotation_subtypes": unsafe_subtypes, "attachment_markers": attachments, "javascript_name_tree": has_javascript, "embedded_files_name_tree": has_embedded_files, "acroform_or_fields": has_acroform, "catalog_associated_files": has_associated_files, "collection": has_collection, "unsafe_active_content_present": unsafe_active},
        "privacy_and_residue": {"extracted_text_hits": extracted_hits, "metadata_hits": metadata_hits, "raw_or_decompressed_object_hits": raw_hits, "decoded_stream_count": stream_count, "decoded_stream_bytes_scanned": decoded_bytes, "stream_scan_errors": stream_errors},
        "punctuation_regression": {"unit7_visual_orphans": visual_orphans, "unit7_sentence_concatenations": sentence_concat, "passed": not visual_orphans and not sentence_concat},
        "warnings": warnings,
        "limitations": limitations,
        "blockers": blockers,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
