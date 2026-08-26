#!/usr/bin/env python3
"""Bounded cumulative PDF structural/accessibility QA through Unit 16.

The output PDF identity is learned only from the passing two-clean-cycle build
receipt, never hardcoded while Unit 16 is unfinished. Stable structural facts
(unit/exercise/solution closure, A4 geometry, 22 mm centered margins, media
roles, safety, and accessibility checks) remain explicit. The receipt contains
no timestamp or absolute machine path and is deterministic for fixed evidence.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

import pdfplumber
import pypdf
from pypdf import PdfReader
from pypdf.generic import IndirectObject, StreamObject


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PREFIX_VERIFIER = Path(__file__).with_name("verify_through_unit10_pdf.py")
_spec = importlib.util.spec_from_file_location("_unit10_pdf_helpers", PREFIX_VERIFIER)
if _spec is None or _spec.loader is None:  # pragma: no cover
    raise RuntimeError(f"cannot load exact Unit 10 verifier helpers: {PREFIX_VERIFIER}")
_prefix = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_prefix)

bytes_sha = _prefix.bytes_sha
normalize_text = _prefix.normalize_text
dereference = _prefix.dereference
collect_fonts = _prefix.collect_fonts
scan_raw_objects = _prefix.scan_raw_objects
collect_bookmarks = _prefix.collect_bookmarks
inspect_annotations = _prefix.inspect_annotations
scan_logs = _prefix.scan_logs
FORBIDDEN_TEXT = dict(_prefix.FORBIDDEN_TEXT)
# A bare ``[[`` is valid mathematical text for nested Lie brackets.  Treat it
# as MediaWiki residue only when the complete bracketed token has a wiki-like
# path, label separator, or namespace marker.
FORBIDDEN_TEXT["raw wiki markup"] = re.compile(
    r"(?:\[\[[^\]\n]*(?:\||/|:)[^\]\n]*\]\]|\{\{(?:Latex|Definitionslink|Relationskette|Math|"
    r"Abbildung)|(?:Kategorie|Kategori):Latexseite)",
    re.IGNORECASE,
)
UNSAFE_ANNOTATION_SUBTYPES = _prefix.UNSAFE_ANNOTATION_SUBTYPES


PDF_REL = "output/pdf/geometri-diferensial-manifold-mulus-hingga-unit-16-id.pdf"
BUILD_REL = "qa/unit-16/build.json"
MEDIA_CONFIG_REL = "source/unit_media.json"
OUTPUT_REL = "qa/unit-16/pdf_structural_qa.json"
DRIVER_REL = "build/generated/through-unit-16-driver.tex"
COMPAT_REL = "build/brenner-compat.tex"
EXPECTED_A4 = [595.276, 841.89]
EXPECTED_METADATA = {
    "/Author": "Holger Brenner, Terjemahan Bahasa Indonesia independen",
    "/Title": "Geometri Diferensial dan Manifold Mulus Pembaca kumulatif hingga Unit 16",
    "/Creator": "LaTeX with hyperref",
}
EXPECTED_MODEL = "OpenAI Codex gpt-5.6-sol, Ultra"
UMBRELLA_RAW = re.compile(
    rb"(?:\bTTP\b|Translation and Transcription Project)", re.IGNORECASE
)

PREFIX_BOUNDARY = {
    "build": {
        "path": "qa/unit-10/build.json",
        "bytes": 20_600,
        "sha256": "4f3146a4889e9be09e17ac5d7a1bb9bfb4a6c609debccd4befb078a1bd33b65d",
    },
    "structural_qa": {
        "path": "qa/unit-10/pdf_structural_qa.json",
        "bytes": 89_821,
        "sha256": "81451a5e7f78f63935e758fa3d277db28b9db252c09c6930fc1cea597c9a47d7",
    },
    "pdf": {
        "path": "output/pdf/geometri-diferensial-manifold-mulus-hingga-unit-10-id.pdf",
        "bytes": 5_733_895,
        "sha256": "4eaec807347feeab2b3334056d3109d5ce6e5eb30ed3649a507ae6124049856d",
    },
    "frozen_media_config_archive": {
        "path": "output/release-unit10/geometri-diferensial-manifold-mulus-brenner-id-unit10-source-20260823.zip",
        "bytes": 1_758_537,
        "sha256": "0c160e741e02a711bdbbb984a788459ccb1e4ca94f0809f5add25ec50f8beb3a",
    },
    "frozen_media_config_entry": {
        "path": "source/unit_media.json",
        "bytes": 3_709,
        "sha256": "1f5404aad71947dcff064b853f1820b302f5a7e14cbb862631623eeddc2b8cad",
    },
}

ROMAN = {
    1: "I",
    2: "II",
    3: "III",
    4: "IV",
    5: "V",
    6: "VI",
    7: "VII",
    8: "VIII",
    9: "IX",
    10: "X",
    11: "XI",
    12: "XII",
    13: "XIII",
    14: "XIV",
    15: "XV",
    16: "XVI",
}
EXPECTED_EXERCISE_NUMBERS = {
    **_prefix.EXPECTED_EXERCISE_NUMBERS,
    11: list(range(1, 40)),
    12: list(range(1, 30)),
    13: list(range(1, 25)),
    14: list(range(1, 19)),
    15: list(range(1, 17)),
    16: list(range(1, 22)),
}
EXPECTED_SOLUTION_NUMBERS = {
    **_prefix.EXPECTED_SOLUTION_NUMBERS,
    11: [10, 14],
    12: [11, 12],
    13: [1, 10, 11, 16, 18, 19, 21, 22],
    14: [5, 6, 9, 11, 12, 13, 14],
    15: [1, 11, 12, 13],
    16: [1, 12],
}
EXPECTED_EXERCISE_TOTAL = 342
EXPECTED_SOLUTION_TOTAL = 48

NEW_MEDIA = {
    11: ["Toroidal coord.png"],
    12: ["Fiddler crab mobius strip.gif", "Inclusion-exclusion.svg"],
    13: ["Möbius strip.jpg"],
    14: [],
    15: [],
    16: ["Georg Friedrich Bernhard Riemann.jpeg", "Sphere with three handles.png"],
}
EXPECTED_CONFIGURED_MEDIA = sorted(_prefix.EXPECTED_STATIC_MEDIA + sum(NEW_MEDIA.values(), []))
EXPECTED_INTERACTIVE_GIF = "Aufgabe79.27.gif"
EXPECTED_INTERACTIVE_URI = "https://commons.wikimedia.org/wiki/File:Aufgabe79.27.gif"
EXPECTED_GIF_DERIVATIVE = "build/generated/media/Fiddler_crab_mobius_strip.png"
EXPECTED_GIF_DESCRIPTION = (
    "Edisi PDF menampilkan bingkai pertama yang statis; animasi asli dipertahankan "
    "untuk edisi HTML dan unduhan."
)

REQUIRED_READER_PROSE = {
    "work title": r"\bGeometri Diferensial dan Manifold Mulus\b",
    "cumulative boundary": r"\bPembaca kumulatif hingga Unit 16\b",
    "source authority": r"Differentialgeometrie \(Osnabr.ck 2023\)",
    "text license": r"Teks sumber digunakan berdasarkan CC BY-SA 4\.0",
    "independent non-endorsement": (
        r"Terjemahan ini merupakan karya independen dan bukan edisi resmi atau dukungan "
        r"dari penulis maupun Wikiversity"
    ),
    "component media rights": r"Setiap gambar mengikuti status hak atau lisensi berkasnya sendiri",
    "honest solution closure": r"Bagian solusi hanya memuat solusi yang benar-benar disediakan oleh sumber",
    "model provenance": re.escape(EXPECTED_MODEL),
    "media rights section": r"\bAtribusi dan Hak Media\b",
    "license section": r"\bLisensi\b",
    "Unit 12 static GIF disclosure": re.escape(EXPECTED_GIF_DESCRIPTION),
}

SENSITIVE_FILENAME = re.compile(
    r"(?:New zenodo token\.md|Github Tokens\.md|Zenodo token\.md|Figshare Token\.md)",
    re.IGNORECASE,
)


def relative(path: Path) -> str:
    return path.resolve().relative_to(PROJECT_ROOT).as_posix()


def identity(path: Path) -> dict[str, object] | None:
    return bytes_sha(path) if path.is_file() else None


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def add(blockers: list[str], condition: bool, message: str) -> None:
    if not condition:
        blockers.append(message)


def safe_project_path(rel: str) -> Path | None:
    if not rel or Path(rel).is_absolute():
        return None
    candidate = (PROJECT_ROOT / rel).resolve()
    return candidate if candidate != PROJECT_ROOT and PROJECT_ROOT in candidate.parents else None


def require_input(
    input_map: dict[str, dict[str, object]], rel: str, blockers: list[str]
) -> dict[str, object] | None:
    row = input_map.get(rel)
    add(blockers, row is not None, f"required build input is undeclared: {rel}")
    return row


def verify_build(blockers: list[str]) -> dict[str, object]:
    path = PROJECT_ROOT / BUILD_REL
    actual_receipt = identity(path)
    if not path.is_file():
        blockers.append(f"missing build receipt: {BUILD_REL}")
        return {"receipt": None, "cycles": [], "inputs": [], "input_count": 0, "log_scan": None}

    data = load_json(path)
    add(blockers, data.get("workflow") == "o011-through-unit16-pdf-build-v1", "wrong build workflow")
    add(blockers, data.get("deterministic_clean_cycles") is True, "clean cycles are not deterministic")
    output = data.get("output", {})
    declared_pdf = {"bytes": output.get("bytes"), "sha256": output.get("sha256")}
    actual_pdf = identity(PROJECT_ROOT / PDF_REL)
    add(blockers, output.get("path") == PDF_REL, "wrong build output path")
    add(blockers, actual_pdf == declared_pdf, f"build output identity mismatch: {actual_pdf} != {declared_pdf}")

    prefix = data.get("cumulative_prefix", {})
    add(blockers, prefix.get("exact_through_unit") == 10, "wrong cumulative prefix boundary")
    for key, expected in PREFIX_BOUNDARY.items():
        add(blockers, prefix.get(key) == expected, f"exact Unit 10 prefix binding mismatch: {key}")
    prefix_preservation_rel = str(prefix.get("preservation_receipt", ""))
    prefix_preservation_path = safe_project_path(prefix_preservation_rel)
    prefix_preservation = (
        load_json(prefix_preservation_path)
        if prefix_preservation_path and prefix_preservation_path.is_file()
        else {}
    )
    add(
        blockers,
        prefix_preservation.get("workflow") == "o011-unit16-unit10-prefix-preservation-v2"
        and prefix_preservation.get("live_media_configuration", {}).get("untouched_byte_identically") is True
        and prefix_preservation.get("archive_evidence", {}).get("exact_entries_verified") is True
        and prefix_preservation.get("verification", {}).get(
            "public_pdf_and_historical_receipts_match_frozen_identities"
        )
        is True,
        "Unit 10 public-prefix preservation receipt is missing or not passing",
    )

    cycles = data.get("cycles", [])
    add(blockers, len(cycles) == 2, f"expected two clean cycles, found {len(cycles)}")
    cycle_checks: list[dict[str, object]] = []
    for expected_number, row in enumerate(cycles, start=1):
        rel = str(row.get("pdf", ""))
        actual = identity(PROJECT_ROOT / rel)
        passed = bool(
            row.get("cycle") == expected_number
            and row.get("bytes") == declared_pdf["bytes"]
            and row.get("sha256") == declared_pdf["sha256"]
            and actual == declared_pdf
        )
        cycle_checks.append(
            {
                "cycle": expected_number,
                "path": rel,
                "declared": {"bytes": row.get("bytes"), "sha256": row.get("sha256")},
                "actual": actual,
                "passed": passed,
            }
        )
        add(blockers, passed, f"clean cycle {expected_number} is not bound to the installed PDF")

    declared_inputs = data.get("inputs", [])
    input_map: dict[str, dict[str, object]] = {}
    input_checks: list[dict[str, object]] = []
    for row in declared_inputs:
        rel = str(row.get("path", ""))
        candidate = safe_project_path(rel)
        declared = {"bytes": row.get("bytes"), "sha256": row.get("sha256")}
        actual = identity(candidate) if candidate else None
        unique = rel not in input_map
        passed = bool(candidate and unique and actual == declared)
        input_checks.append(
            {
                "path": rel,
                "declared": declared,
                "actual": actual,
                "within_project": candidate is not None,
                "unique": unique,
                "passed": passed,
            }
        )
        add(blockers, passed, f"build input identity/uniqueness mismatch: {rel}")
        if unique:
            input_map[rel] = row

    required = {
        "scripts/build_through_unit16.ps1",
        "scripts/verify_through_unit16_pdf.py",
        "scripts/build_through_unit10.ps1",
        "scripts/verify_through_unit10_pdf.py",
        "scripts/prepare_unit_tex.py",
        "scripts/prepare_unit_media.py",
        "build/through-unit-10.tex",
        DRIVER_REL,
        COMPAT_REL,
        MEDIA_CONFIG_REL,
        "authority/brenner_media_rights_manifest.csv",
        "qa/unit-16/UNIT10_PREFIX_PRESERVATION_RECEIPT.json",
        "qa/unit-16/WRAPPER_DERIVATION_RECEIPT.json",
        "qa/unit-16/MEDIA_ALIAS_RECEIPT.json",
        "source/unit11_interactive_media.json",
        "qa/unit-11/INTERACTIVE_MEDIA_QA.json",
        "qa/unit-12/ANIMATED_MEDIA_QA.json",
        *[f"qa/unit-{unit:02d}/POST_CORRECTION_MATH_QA.json" for unit in range(11, 17)],
        *[f"qa/unit-{unit:02d}/solution_closure.json" for unit in range(11, 17)],
        *[
            f"qa/unit-16/cumulative-media/unit-{unit:02d}_media.json"
            for unit in range(11, 17)
        ],
    }
    for unit in range(11, 17):
        required.update(
            {
                f"source/units/unit-{unit:02d}/lecture{unit:02d}.id.tex",
                f"source/units/unit-{unit:02d}/worksheet{unit:02d}.id.tex",
                f"qa/unit-{unit:02d}/lecture{unit:02d}_translation.json",
                f"qa/unit-{unit:02d}/worksheet{unit:02d}_translation.json",
                f"qa/unit-{unit:02d}/lecture{unit:02d}_prepare.json",
                f"qa/unit-{unit:02d}/worksheet{unit:02d}_prepare.json",
                f"build/generated/lecture{unit:02d}.id.build.tex",
                f"build/generated/worksheet{unit:02d}.id.build.tex",
                f"build/generated/unit{unit:02d}-media-attribution-cumulative.tex",
            }
        )
        for exercise in EXPECTED_SOLUTION_NUMBERS[unit]:
            stem = f"worksheet{unit:02d}_exercise{exercise:02d}_solution"
            required.update(
                {
                    f"source/units/unit-{unit:02d}/{stem}.id.tex",
                    f"qa/unit-{unit:02d}/{stem}_translation.json",
                    f"qa/unit-{unit:02d}/{stem}_prepare.json",
                    f"build/generated/{stem}.id.build.tex",
                }
            )
    for rel in sorted(required):
        require_input(input_map, rel, blockers)

    unit_bindings = data.get("unit_bindings", [])
    add(
        blockers,
        [row.get("unit") for row in unit_bindings] == [11, 12, 13, 14, 15, 16],
        "unit binding order/closure mismatch",
    )
    for row in unit_bindings:
        unit = int(row.get("unit", 0))
        if unit not in (11, 12, 13, 14, 15, 16):
            continue
        add(
            blockers,
            row.get("exercise_count") == len(EXPECTED_EXERCISE_NUMBERS[unit]),
            f"Unit {unit} build exercise count mismatch",
        )
        add(
            blockers,
            row.get("supplied_solution_numbers") == EXPECTED_SOLUTION_NUMBERS[unit],
            f"Unit {unit} build solution closure mismatch",
        )
        post_rel = str(row.get("post_qa", {}).get("path", ""))
        post_path = safe_project_path(post_rel)
        post = load_json(post_path) if post_path and post_path.is_file() else {}
        add(blockers, post.get("status") == "pass", f"Unit {unit} POST QA no longer passes")
        source_closure = post.get("source_closure", {})
        authority = post.get("authority", {})
        post_solution_indices = source_closure.get("supplied_solution_indices")
        if post_solution_indices is None:
            post_solution_indices = authority.get("supplied_solution_indices")
        add(
            blockers,
            post_solution_indices == EXPECTED_SOLUTION_NUMBERS[unit],
            f"Unit {unit} POST QA supplied-solution closure changed",
        )

    wrapper = data.get("wrapper", {})
    add(blockers, wrapper.get("workflow") == "o011-unit16-wrapper-derivation-v1", "wrong wrapper derivation workflow")
    add(
        blockers,
        wrapper.get("geometry") == {"paper": "A4", "margin": "22mm", "centered": True, "class_option": "oneside"},
        "wrapper geometry contract mismatch",
    )
    add(blockers, wrapper.get("extension_units") == [11, 12, 13, 14, 15, 16], "wrapper unit extension mismatch")
    add(
        blockers,
        wrapper.get("supplied_solutions")
        == {
            "11": [10, 14],
            "12": [11, 12],
            "13": [1, 10, 11, 16, 18, 19, 21, 22],
            "14": [5, 6, 9, 11, 12, 13, 14],
            "15": [1, 11, 12, 13],
            "16": [1, 12],
        },
        "wrapper supplied-solution closure mismatch",
    )
    driver_path = PROJECT_ROOT / DRIVER_REL
    driver_text = driver_path.read_text(encoding="utf-8") if driver_path.is_file() else ""
    add(
        blockers,
        driver_text.count(r"\documentclass[11pt,a4paper,oneside]{book}") == 1
        and driver_text.count(r"\usepackage[a4paper,margin=22mm,headheight=15pt]{geometry}") == 1,
        "derived driver does not contain the exact centered A4/22mm contract",
    )

    log_blockers: list[str] = []
    log_scan = scan_logs(data, log_blockers)
    for message in log_blockers:
        if not message.startswith("build warning diagnostics:"):
            blockers.append(message)
    return {
        "receipt": {"path": BUILD_REL, **(actual_receipt or {})},
        "workflow": data.get("workflow"),
        "deterministic_clean_cycles": data.get("deterministic_clean_cycles"),
        "output": {"path": PDF_REL, **declared_pdf},
        "prefix": prefix,
        "cycles": cycle_checks,
        "inputs": input_checks,
        "input_count": len(input_checks),
        "required_input_count": len(required),
        "unit_bindings": unit_bindings,
        "wrapper": wrapper,
        "log_scan": log_scan,
    }


def bookmark_page(records: list[dict[str, object]], title: str) -> int | None:
    matches = [row.get("page") for row in records if row.get("title") == title]
    return int(matches[0]) if len(matches) == 1 and isinstance(matches[0], int) else None


def verify_reader_content(
    texts: list[str], records: list[dict[str, object]], blockers: list[str]
) -> dict[str, object]:
    full_text = "\n".join(texts)
    normalized = normalize_text(full_text)
    missing_prose = [
        label for label, pattern in REQUIRED_READER_PROSE.items() if not re.search(pattern, normalized)
    ]
    add(blockers, not missing_prose, f"missing required provenance/rights/media prose: {missing_prose}")
    model_count = normalized.count(EXPECTED_MODEL)
    add(blockers, model_count == 1, f"model provenance occurs {model_count} times, expected once")

    title_counts = Counter(str(row.get("title")) for row in records)
    required_bookmarks: list[str] = []
    for unit in range(1, 17):
        required_bookmarks.extend(
            [f"{ROMAN[unit]} Unit {unit}", f"Kuliah {unit}", f"Lembar Kerja {unit}", f"Unit {unit}"]
        )
    required_bookmarks.append("Atribusi dan Hak Media")
    missing_bookmarks = [title for title in required_bookmarks if title_counts[title] != 1]
    solution_bookmark_count = title_counts["Solusi yang disediakan oleh sumber"]
    add(blockers, not missing_bookmarks, f"missing or duplicated structural bookmarks: {missing_bookmarks}")
    add(blockers, solution_bookmark_count == 15, f"source-solution bookmark count is {solution_bookmark_count}, expected 15")
    add(blockers, len(records) == 80, f"bookmark count is {len(records)}, expected 80")

    units: dict[str, object] = {}
    total_exercises = 0
    total_solutions = 0
    for unit in range(1, 17):
        worksheet_page = bookmark_page(records, f"Lembar Kerja {unit}")
        end_page = (
            bookmark_page(records, f"{ROMAN[unit + 1]} Unit {unit + 1}")
            if unit < 16
            else bookmark_page(records, "Atribusi dan Hak Media")
        )
        block = ""
        if worksheet_page is not None and end_page is not None and worksheet_page < end_page:
            block = "\n".join(texts[worksheet_page - 1 : end_page - 1])
        marker = "Solusi yang disediakan oleh sumber"
        marker_index = block.find(marker)
        worksheet_text = block[:marker_index] if marker_index >= 0 else block
        solution_text = block[marker_index:] if marker_index >= 0 else ""
        exercise_numbers = [
            int(value) for value in re.findall(rf"(?m)^\s*Soal\s*{unit}\.(\d+)\.", worksheet_text)
        ]
        if unit == 1:
            solution_numbers = [
                int(value)
                for value in re.findall(r"(?m)^\s*Solusi\s+untuk\s+Soal\s+(\d+)\b", solution_text)
            ]
        else:
            solution_numbers = [
                int(value)
                for value in re.findall(rf"(?m)^\s*Solusi\s+Soal\s+{unit}\.(\d+)\b", solution_text)
            ]
        expected_exercises = EXPECTED_EXERCISE_NUMBERS[unit]
        expected_solutions = EXPECTED_SOLUTION_NUMBERS[unit]
        exercise_pass = exercise_numbers == expected_exercises
        solution_pass = solution_numbers == expected_solutions
        marker_pass = (marker_index >= 0) == bool(expected_solutions)
        add(blockers, exercise_pass, f"Unit {unit} exercise sequence mismatch: {exercise_numbers}")
        add(blockers, solution_pass, f"Unit {unit} source-solution sequence mismatch: {solution_numbers}")
        add(blockers, marker_pass, f"Unit {unit} source-solution section presence mismatch")
        total_exercises += len(exercise_numbers)
        total_solutions += len(solution_numbers)
        units[str(unit)] = {
            "worksheet_start_page": worksheet_page,
            "next_boundary_page": end_page,
            "exercise_numbers": exercise_numbers,
            "expected_exercise_numbers": expected_exercises,
            "exercise_count": len(exercise_numbers),
            "exercise_sequence_passed": exercise_pass,
            "source_solution_section_present": marker_index >= 0,
            "source_solution_numbers": solution_numbers,
            "expected_source_solution_numbers": expected_solutions,
            "source_solution_count": len(solution_numbers),
            "source_solution_sequence_passed": solution_pass,
        }
    add(blockers, total_exercises == EXPECTED_EXERCISE_TOTAL, f"exercise total is {total_exercises}, expected {EXPECTED_EXERCISE_TOTAL}")
    add(blockers, total_solutions == EXPECTED_SOLUTION_TOTAL, f"source-solution total is {total_solutions}, expected {EXPECTED_SOLUTION_TOTAL}")
    return {
        "required_prose_presence": {label: label not in missing_prose for label in REQUIRED_READER_PROSE},
        "missing_required_prose": missing_prose,
        "model_provenance": {"exact_text": EXPECTED_MODEL, "occurrences": model_count},
        "bookmark_title_counts": dict(sorted(title_counts.items())),
        "missing_or_duplicated_required_bookmarks": missing_bookmarks,
        "source_solution_bookmark_count": solution_bookmark_count,
        "units": units,
        "exercise_total": total_exercises,
        "expected_exercise_total": EXPECTED_EXERCISE_TOTAL,
        "source_solution_total": total_solutions,
        "expected_source_solution_total": EXPECTED_SOLUTION_TOTAL,
    }


def verify_media(
    normalized_text: str,
    uri_counts: Counter[str],
    build_inputs: list[dict[str, object]],
    blockers: list[str],
) -> dict[str, object]:
    input_map = {
        str(row.get("path")): (
            row.get("declared", {}) if isinstance(row.get("declared"), dict) else row
        )
        for row in build_inputs
    }
    config_path = PROJECT_ROOT / MEDIA_CONFIG_REL
    config_identity = identity(config_path)
    config_declared = input_map.get(MEDIA_CONFIG_REL, {})
    add(
        blockers,
        config_identity == {"bytes": config_declared.get("bytes"), "sha256": config_declared.get("sha256")},
        f"live media configuration is not bound to the build: {config_identity}",
    )
    data = load_json(config_path)
    units = data.get("units", {})
    rows = [row for unit in range(1, 17) for row in units.get(str(unit), {}).get("media", [])]
    filenames = sorted(str(row.get("filename")) for row in rows)
    add(blockers, data.get("schema_version") == 1, "wrong media configuration schema version")
    add(blockers, set(units) == {str(unit) for unit in range(1, 17)}, "media configuration does not cover exactly Units 1-16")
    add(blockers, filenames == EXPECTED_CONFIGURED_MEDIA, f"configured media filename closure mismatch: {filenames}")
    add(blockers, len(rows) == 23, f"configured media census is {len(rows)}, expected 23")

    text_occurrences = {filename: normalized_text.count(filename) for filename in filenames}
    missing_text = [filename for filename, count in text_occurrences.items() if count < 1]
    add(blockers, not missing_text, f"configured media absent from figure/attribution text: {missing_text}")

    allowed_uris = {
        f"https://commons.wikimedia.org/wiki/File:{filename.replace(' ', '_')}"
        for filename in _prefix.EXPECTED_STATIC_MEDIA
    }
    allowed_uris.update(_prefix.EXPECTED_GIF_URIS)
    allowed_uris.update(_prefix.EXPECTED_LICENSE_URIS)
    new_receipts: list[dict[str, object]] = []
    for unit, expected_names in NEW_MEDIA.items():
        rel = f"qa/unit-16/cumulative-media/unit-{unit:02d}_media.json"
        path = PROJECT_ROOT / rel
        receipt_identity = identity(path)
        declared = input_map.get(rel, {})
        add(
            blockers,
            receipt_identity == {"bytes": declared.get("bytes"), "sha256": declared.get("sha256")},
            f"Unit {unit} media receipt is not build-bound",
        )
        receipt = load_json(path)
        media_rows = receipt.get("media", [])
        add(blockers, receipt.get("unit_number") == unit, f"wrong Unit {unit} media receipt unit")
        add(
            blockers,
            [row.get("filename") for row in media_rows] == expected_names,
            f"Unit {unit} media receipt filename closure mismatch",
        )
        for row in media_rows:
            allowed_uris.add(str(row.get("commons_description_url")))
            if row.get("license_url"):
                allowed_uris.add(str(row["license_url"]))
        new_receipts.append({"unit": unit, "path": rel, **(receipt_identity or {}), "media": media_rows})
    allowed_uris.add(EXPECTED_INTERACTIVE_URI)
    actual_uris = set(uri_counts)
    missing_uris = sorted(allowed_uris - actual_uris)
    unexpected_uris = sorted(actual_uris - allowed_uris)
    add(blockers, not missing_uris, f"missing required media/license URIs: {missing_uris}")
    add(blockers, not unexpected_uris, f"unexpected external URIs: {unexpected_uris}")

    unit12 = next(row for row in new_receipts if row["unit"] == 12)
    gif_rows = [row for row in unit12["media"] if row.get("filename") == "Fiddler crab mobius strip.gif"]
    gif_row = gif_rows[0] if len(gif_rows) == 1 else {}
    derivative = gif_row.get("derivative") or {}
    derivative_rel = str(derivative.get("path", ""))
    derivative_actual = identity(PROJECT_ROOT / derivative_rel) if derivative_rel else None
    derivative_expected = {"bytes": derivative.get("bytes"), "sha256": derivative.get("sha256")}
    add(
        blockers,
        derivative_rel == EXPECTED_GIF_DERIVATIVE
        and derivative.get("source_kind") == "gif"
        and derivative.get("frame_index") == 0
        and derivative_actual == derivative_expected,
        f"Unit 12 GIF static frame-zero derivative mismatch: {derivative}",
    )
    animation_qa_rel = "qa/unit-12/ANIMATED_MEDIA_QA.json"
    animation_qa_path = PROJECT_ROOT / animation_qa_rel
    animation_qa = load_json(animation_qa_path)
    animation_declared = input_map.get(animation_qa_rel, {})
    add(
        blockers,
        identity(animation_qa_path)
        == {"bytes": animation_declared.get("bytes"), "sha256": animation_declared.get("sha256")}
        and animation_qa.get("status") == "pass"
        and animation_qa.get("static_pdf_fallback", {}).get("frame_index") == 0
        and animation_qa.get("static_pdf_fallback", {}).get("path") == EXPECTED_GIF_DERIVATIVE
        and animation_qa.get("static_pdf_fallback", {}).get("sha256") == derivative.get("sha256"),
        "Unit 12 passing animated-media QA/static fallback binding mismatch",
    )
    compat_text = (PROJECT_ROOT / COMPAT_REL).read_text(encoding="utf-8")
    prepared_text = (PROJECT_ROOT / "build/generated/lecture12.id.build.tex").read_text(encoding="utf-8")
    add(
        blockers,
        r"\newcommand{\bildeinlesunggif}[2]{generated/media/#1.png}" in compat_text
        and r"\bildeinlesunggif {Fiddler_crab_mobius_strip} {gif}" in prepared_text
        and EXPECTED_GIF_DESCRIPTION in prepared_text,
        "Unit 12 prepared lecture does not route the GIF through the disclosed static PNG fallback",
    )
    return {
        "configuration": {"path": MEDIA_CONFIG_REL, **(config_identity or {})},
        "configured_units": sorted(units, key=int),
        "configured_media_count": len(rows),
        "expected_configured_media_count": 23,
        "configured_media_filenames": filenames,
        "text_occurrences": text_occurrences,
        "missing_figure_or_attribution_text": missing_text,
        "new_unit_media_receipts": new_receipts,
        "unit12_static_pdf_fallback": {
            "path": derivative_rel,
            **(derivative_actual or {}),
            "source_kind": derivative.get("source_kind"),
            "frame_index": derivative.get("frame_index"),
            "animation_qa": animation_qa_rel,
        },
        "required_uri_count": len(allowed_uris),
        "missing_required_uris": missing_uris,
        "unexpected_uris": unexpected_uris,
    }


def prove_umbrella_hits_are_admitted_opaque_media(
    reader: PdfReader, pdf_path: Path
) -> dict[str, object]:
    """Prove that short-token raw hits occur only in admitted image bytes.

    A case-insensitive three-byte ``TTP`` scan can match entropy-coded JPEG or
    PNG data by chance.  We still scan extracted text, PDF metadata, and every
    non-image stream normally.  This routine permits exclusion only when every
    raw-byte and decoded-stream match lies inside a byte/hash-bound canonical
    image admitted by the milestone-local media receipts.
    """

    admitted: dict[str, dict[str, object]] = {}
    for unit in range(11, 17):
        receipt_path = (
            PROJECT_ROOT
            / f"qa/unit-16/cumulative-media/unit-{unit:02d}_media.json"
        )
        receipt = load_json(receipt_path)
        for row in receipt.get("media", []):
            path = safe_project_path(str(row.get("canonical_path", "")))
            declared = {
                "bytes": row.get("canonical_bytes"),
                "sha256": row.get("canonical_sha256"),
            }
            actual = identity(path) if path else None
            if actual != declared or path is None:
                continue
            data = path.read_bytes()
            if UMBRELLA_RAW.search(data):
                admitted[str(row["canonical_sha256"])] = {
                    "path": relative(path),
                    **declared,
                    "data": data,
                }

    raw = pdf_path.read_bytes()
    raw_matches = [match.start() for match in UMBRELLA_RAW.finditer(raw)]
    admitted_ranges: list[dict[str, object]] = []
    for row in admitted.values():
        blob = row["data"]
        start = raw.find(blob)
        while start >= 0:
            admitted_ranges.append(
                {
                    "start": start,
                    "end": start + len(blob),
                    "path": row["path"],
                    "sha256": row["sha256"],
                }
            )
            start = raw.find(blob, start + 1)
    raw_unexplained = [
        offset
        for offset in raw_matches
        if not any(int(row["start"]) <= offset < int(row["end"]) for row in admitted_ranges)
    ]

    stream_matches: list[dict[str, object]] = []
    stream_unexplained: list[dict[str, object]] = []
    for generation, entries in reader.xref.items():
        if generation == 65535:
            continue
        for object_number in entries:
            object_id = f"{object_number}:{generation}"
            try:
                obj = reader.get_object(
                    IndirectObject(object_number, generation, reader)
                )
                if not isinstance(obj, StreamObject):
                    continue
                data = obj.get_data()
            except Exception as exc:
                stream_unexplained.append(
                    {"object": object_id, "error": type(exc).__name__}
                )
                continue
            count = sum(1 for _ in UMBRELLA_RAW.finditer(data))
            if not count:
                continue
            digest = hashlib.sha256(data).hexdigest()
            row = {
                "object": object_id,
                "match_count": count,
                "subtype": str(obj.get("/Subtype", "")),
                "bytes": len(data),
                "sha256": digest,
            }
            stream_matches.append(row)
            if obj.get("/Subtype") != "/Image" or digest not in admitted:
                stream_unexplained.append(row)

    passed = bool(raw_matches or stream_matches) and not raw_unexplained and not stream_unexplained
    return {
        "status": "pass" if passed else "fail",
        "criterion": "all raw and decoded-stream umbrella-token hits are confined to exact hash-bound admitted opaque images",
        "raw_match_offsets": raw_matches,
        "admitted_raw_ranges": admitted_ranges,
        "unexplained_raw_match_offsets": raw_unexplained,
        "stream_matches": stream_matches,
        "unexplained_stream_matches": stream_unexplained,
    }


def validate_internal_links(reader: PdfReader) -> list[dict[str, object]]:
    named = set(str(key) for key in reader.named_destinations)
    failures: list[dict[str, object]] = []
    for page_number, page in enumerate(reader.pages, start=1):
        for annotation_ref in page.get("/Annots", []) or []:
            annotation = dereference(annotation_ref)
            action = dereference(annotation.get("/A")) if annotation.get("/A") else None
            if not action or str(action.get("/S", "")) != "/GoTo":
                continue
            destination = action.get("/D")
            if isinstance(destination, str):
                if str(destination) not in named:
                    failures.append({"page": page_number, "destination": str(destination), "reason": "missing named destination"})
            else:
                failures.append({"page": page_number, "destination": repr(destination), "reason": "unsupported destination representation"})
    return failures


def write_early_failure(output_path: Path, blockers: list[str]) -> int:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "workflow": "o011-through-unit16-pdf-structural-accessibility-qa-v1",
                "verdict": "FAIL",
                "passed": False,
                "blockers": blockers,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return 1


def main() -> int:
    blockers: list[str] = []
    warnings: list[str] = []
    limitations: list[str] = []
    script_path = Path(__file__).resolve()
    pdf_path = PROJECT_ROOT / PDF_REL
    output_path = PROJECT_ROOT / OUTPUT_REL
    if not pdf_path.is_file() or not (PROJECT_ROOT / BUILD_REL).is_file():
        if not pdf_path.is_file():
            blockers.append(f"missing target PDF: {PDF_REL}")
        if not (PROJECT_ROOT / BUILD_REL).is_file():
            blockers.append(f"missing build receipt: {BUILD_REL}")
        return write_early_failure(output_path, blockers)

    build_binding = verify_build(blockers)
    pdf_identity = identity(pdf_path)
    declared_output = build_binding.get("output", {})
    add(
        blockers,
        pdf_identity == {"bytes": declared_output.get("bytes"), "sha256": declared_output.get("sha256")},
        f"target PDF is not bound to the build receipt: {pdf_identity}",
    )

    reader = PdfReader(str(pdf_path))
    page_count = len(reader.pages)
    add(blockers, page_count > _prefix.EXPECTED_PAGES, f"Unit 16 cumulative PDF has only {page_count} pages")
    add(blockers, not reader.is_encrypted, "PDF is encrypted")
    catalog = dereference(reader.trailer.get("/Root", {})) or {}
    catalog_language = str(catalog.get("/Lang", ""))
    add(blockers, catalog_language == "id-ID", f"catalog language is {catalog_language!r}, expected 'id-ID'")

    metadata = {str(key): str(value) for key, value in (reader.metadata or {}).items() if value is not None}
    metadata_mismatches = {
        key: {"expected": expected, "actual": metadata.get(key)}
        for key, expected in EXPECTED_METADATA.items()
        if metadata.get(key) != expected
    }
    add(blockers, not metadata_mismatches, f"metadata mismatch: {metadata_mismatches}")
    volatile_metadata = sorted(key for key in ("/CreationDate", "/ModDate") if key in metadata)
    add(blockers, not volatile_metadata, f"volatile PDF metadata present: {volatile_metadata}")
    trailer_id_present = bool(reader.trailer.get("/ID"))
    add(blockers, not trailer_id_present, "non-deterministic trailer ID is present")

    media_boxes = [
        [round(float(page.mediabox.width), 3), round(float(page.mediabox.height), 3)]
        for page in reader.pages
    ]
    crop_boxes = [
        [round(float(page.cropbox.width), 3), round(float(page.cropbox.height), 3)]
        for page in reader.pages
    ]
    rotations = [int(page.get("/Rotate", 0) or 0) for page in reader.pages]
    add(blockers, all(box == EXPECTED_A4 for box in media_boxes), "not every MediaBox is A4")
    add(blockers, all(box == EXPECTED_A4 for box in crop_boxes), "not every CropBox is A4")
    add(blockers, not any(rotations), "one or more pages are rotated")
    expected_page_labels = ["1", "i", "ii", "iii", "iv", "v"] + [
        str(value) for value in range(1, page_count - 5)
    ]
    page_labels = list(reader.page_labels)
    add(blockers, page_labels == expected_page_labels, "page-label sequence mismatch")

    pypdf_text = [page.extract_text() or "" for page in reader.pages]
    pypdf_empty = [index + 1 for index, text in enumerate(pypdf_text) if not text.strip()]
    add(blockers, not pypdf_empty, f"pypdf empty-text pages: {pypdf_empty}")

    plumber_text: list[str] = []
    plumber_empty: list[int] = []
    outside_page: list[dict[str, object]] = []
    body_extents: list[dict[str, object]] = []
    with pdfplumber.open(pdf_path) as pdf:
        add(blockers, len(pdf.pages) == page_count, f"pdfplumber page count is {len(pdf.pages)}")
        for page_number, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            plumber_text.append(text)
            if not text.strip():
                plumber_empty.append(page_number)
            for char in page.chars:
                if (
                    float(char.get("x0", 0.0)) < -0.1
                    or float(char.get("x1", 0.0)) > float(page.width) + 0.1
                    or float(char.get("top", 0.0)) < -0.1
                    or float(char.get("bottom", 0.0)) > float(page.height) + 0.1
                ):
                    outside_page.append(
                        {
                            "page": page_number,
                            "text": str(char.get("text", "")),
                            "x0": round(float(char.get("x0", 0.0)), 3),
                            "x1": round(float(char.get("x1", 0.0)), 3),
                            "top": round(float(char.get("top", 0.0)), 3),
                            "bottom": round(float(char.get("bottom", 0.0)), 3),
                        }
                    )
            body_words = [
                word
                for word in (page.extract_words() or [])
                if float(word["top"]) >= 45.0 and float(word["bottom"]) <= 797.0
            ]
            if body_words:
                body_extents.append(
                    {
                        "page": page_number,
                        "left": round(min(float(word["x0"]) for word in body_words), 3),
                        "right": round(max(float(word["x1"]) for word in body_words), 3),
                    }
                )
    add(blockers, not plumber_empty, f"pdfplumber empty-text pages: {plumber_empty}")
    add(blockers, not outside_page, f"glyphs outside page bounds: {outside_page[:20]}")
    overall_left = min((float(row["left"]) for row in body_extents), default=None)
    overall_right = max((float(row["right"]) for row in body_extents), default=None)
    margin_pass = bool(
        overall_left is not None and overall_right is not None and overall_left >= 55.0 and overall_right <= 540.0
    )
    add(blockers, margin_pass, f"bounded centered-body extent failure: left={overall_left}, right={overall_right}")

    bookmarks, bookmark_errors = collect_bookmarks(reader)
    unresolved_bookmarks = [row for row in bookmarks if row.get("page") is None]
    out_of_range_bookmarks = [
        row for row in bookmarks if isinstance(row.get("page"), int) and not 1 <= int(row["page"]) <= page_count
    ]
    add(blockers, not bookmark_errors, f"bookmark extraction errors: {bookmark_errors}")
    add(blockers, not unresolved_bookmarks, f"unresolved bookmarks: {unresolved_bookmarks}")
    add(blockers, not out_of_range_bookmarks, f"out-of-range bookmarks: {out_of_range_bookmarks}")
    content_closure = verify_reader_content(pypdf_text, bookmarks, blockers)

    fonts = collect_fonts(reader)
    fonts_without_tounicode = sorted(key for key, row in fonts.items() if not row.get("to_unicode"))
    fonts_not_embedded = sorted(key for key, row in fonts.items() if not row.get("embedded"))
    add(blockers, not fonts_without_tounicode, f"fonts without ToUnicode: {fonts_without_tounicode}")
    add(blockers, not fonts_not_embedded, f"fonts not embedded: {fonts_not_embedded}")

    subtypes, uri_counts, internal_links, unsafe_actions, attachments = inspect_annotations(reader)
    unsafe_subtypes = sorted(subtype for subtype in subtypes if subtype in UNSAFE_ANNOTATION_SUBTYPES)
    internal_failures = validate_internal_links(reader)
    add(blockers, set(subtypes).issubset({"/Link"}), f"annotation subtype closure mismatch: {dict(subtypes)}")
    add(blockers, not unsafe_actions, f"unsafe annotation actions: {unsafe_actions}")
    add(blockers, not unsafe_subtypes, f"unsafe annotation subtypes: {unsafe_subtypes}")
    add(blockers, not attachments, f"annotation attachment markers: {attachments}")
    add(blockers, not internal_failures, f"unresolved internal links: {internal_failures}")

    names = dereference(catalog.get("/Names", {})) or {}
    has_javascript = bool(names.get("/JavaScript"))
    has_embedded_files = bool(names.get("/EmbeddedFiles"))
    has_acroform = bool(catalog.get("/AcroForm")) or bool(reader.get_fields() or {})
    has_associated_files = bool(catalog.get("/AF"))
    has_collection = bool(catalog.get("/Collection"))
    unsafe_active = bool(
        has_javascript
        or has_embedded_files
        or has_acroform
        or has_associated_files
        or has_collection
        or unsafe_actions
        or unsafe_subtypes
        or attachments
    )
    add(blockers, not unsafe_active, "PDF contains active, embedded, form, or portfolio content")

    normalized_full = normalize_text("\n".join(pypdf_text))
    media_closure = verify_media(normalized_full, uri_counts, build_binding["inputs"], blockers)

    extracted_hits = {
        label: sorted(set(match.group(0) for match in pattern.finditer("\n".join(pypdf_text))))
        for label, pattern in FORBIDDEN_TEXT.items()
        if pattern.search("\n".join(pypdf_text))
    }
    metadata_text = "\n".join(metadata.values())
    metadata_hits = {
        label: sorted(set(match.group(0) for match in pattern.finditer(metadata_text)))
        for label, pattern in FORBIDDEN_TEXT.items()
        if pattern.search(metadata_text)
    }
    sensitive_filename_hits = sorted(set(SENSITIVE_FILENAME.findall("\n".join(pypdf_text) + "\n" + metadata_text)))
    raw_hits, stream_count, decoded_bytes, stream_errors = scan_raw_objects(reader, pdf_path)
    raw_hits = {label: rows for label, rows in raw_hits.items() if rows}
    umbrella_binary_proof: dict[str, object] | None = None
    if "umbrella metadata residue" in raw_hits:
        umbrella_binary_proof = prove_umbrella_hits_are_admitted_opaque_media(
            reader, pdf_path
        )
        if umbrella_binary_proof.get("status") == "pass":
            del raw_hits["umbrella metadata residue"]
    add(
        blockers,
        not extracted_hits and not metadata_hits and not sensitive_filename_hits and not raw_hits and not stream_errors,
        (
            "privacy/residue scan failure: "
            f"text={extracted_hits}, metadata={metadata_hits}, sensitive_names={sensitive_filename_hits}, "
            f"raw={raw_hits}, stream_errors={stream_errors}"
        ),
    )

    mark_info = dereference(catalog.get("/MarkInfo", {})) or {}
    tagged = bool(catalog.get("/StructTreeRoot")) and bool(mark_info.get("/Marked"))
    if not tagged:
        limitations.append(
            f"The PDF is untagged. All {page_count} pages are text-extractable through pypdf and pdfplumber, "
            f"the catalog language is id-ID, and all {len(fonts)} embedded font objects have ToUnicode maps; "
            "the semantic HTML reader is the structured accessibility surface."
        )
    else:
        warnings.append("PDF unexpectedly reports a structure tree; inspect before freezing expectations.")

    named_destinations = list(reader.named_destinations)
    duplicate_named = len(named_destinations) != len(set(named_destinations))
    add(blockers, len(named_destinations) > _prefix.EXPECTED_PAGES, "named-destination census is implausibly small")
    add(blockers, not duplicate_named, "duplicate named destinations detected")

    passed = not blockers
    log_scan = build_binding.get("log_scan") or {}
    if log_scan.get("warning_hits"):
        warnings.append(
            f"The bound build logs contain {len(log_scan['warning_hits'])} TeX box diagnostics; "
            "independent page-bound, A4, centered-margin, text-extraction, and content-closure checks determine safety."
        )
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
        "workflow": "o011-through-unit16-pdf-structural-accessibility-qa-v1",
        "verdict": verdict,
        "passed": passed,
        "execution_binding": {
            "project_root": ".",
            "script": {"path": relative(script_path), **bytes_sha(script_path)},
            "pdf": {"path": PDF_REL, **(pdf_identity or {})},
            "output": OUTPUT_REL,
        },
        "build_binding": build_binding,
        "pdf": {
            "path": PDF_REL,
            **(pdf_identity or {}),
            "pages": page_count,
            "minimum_pages_exclusive": _prefix.EXPECTED_PAGES,
            "media_box_points": media_boxes[0] if media_boxes else None,
            "crop_box_points": crop_boxes[0] if crop_boxes else None,
            "all_media_boxes_a4": bool(media_boxes) and all(box == EXPECTED_A4 for box in media_boxes),
            "all_crop_boxes_a4": bool(crop_boxes) and all(box == EXPECTED_A4 for box in crop_boxes),
            "all_rotations_zero": not any(rotations),
            "page_labels": page_labels,
            "page_labels_match": page_labels == expected_page_labels,
            "encrypted": reader.is_encrypted,
            "catalog_language": catalog_language,
            "metadata": metadata,
            "metadata_mismatches": metadata_mismatches,
            "volatile_metadata_keys": volatile_metadata,
            "trailer_id_present": trailer_id_present,
            "tagged": tagged,
            "has_structure_tree": bool(catalog.get("/StructTreeRoot")),
            "mark_info_marked": bool(mark_info.get("/Marked")),
        },
        "layout": {
            "declared_geometry": {"paper": "A4", "margin": "22mm", "centered": True},
            "body_vertical_window_points": {"top": 45.0, "bottom": 797.0},
            "body_extent_pages_checked": len(body_extents),
            "minimum_body_left_points": overall_left,
            "maximum_body_right_points": overall_right,
            "accepted_horizontal_bounds_points": {"left_minimum": 55.0, "right_maximum": 540.0},
            "centered_body_bounds_passed": margin_pass,
            "glyphs_outside_page_bounds": outside_page,
        },
        "accessibility": {
            "pypdf_version": pypdf.__version__,
            "pdfplumber_version": pdfplumber.__version__,
            "pypdf_pages_with_extractable_text": page_count - len(pypdf_empty),
            "pypdf_empty_text_pages": pypdf_empty,
            "pdfplumber_pages_with_extractable_text": len(plumber_text) - len(plumber_empty),
            "pdfplumber_empty_text_pages": plumber_empty,
            "font_object_count": len(fonts),
            "fonts_with_tounicode": sum(1 for row in fonts.values() if row.get("to_unicode")),
            "fonts_without_tounicode": fonts_without_tounicode,
            "fonts_embedded": sum(1 for row in fonts.values() if row.get("embedded")),
            "fonts_not_embedded": fonts_not_embedded,
            "fonts": fonts,
        },
        "structure_and_content": {
            "bookmark_count": len(bookmarks),
            "bookmarks": bookmarks,
            "bookmark_errors": bookmark_errors,
            "unresolved_bookmarks": unresolved_bookmarks,
            "out_of_range_bookmarks": out_of_range_bookmarks,
            "named_destination_count": len(named_destinations),
            "duplicate_named_destinations": duplicate_named,
            **content_closure,
        },
        "media_closure": media_closure,
        "links_and_active_content": {
            "internal_link_count": internal_links,
            "internal_link_resolution_failures": internal_failures,
            "external_uri_count": sum(uri_counts.values()),
            "external_uri_counts": dict(sorted(uri_counts.items())),
            "annotation_subtype_counts": dict(sorted(subtypes.items())),
            "unsafe_actions": unsafe_actions,
            "unsafe_annotation_subtypes": unsafe_subtypes,
            "attachment_markers": attachments,
            "javascript_name_tree": has_javascript,
            "embedded_files_name_tree": has_embedded_files,
            "acroform_or_fields": has_acroform,
            "catalog_associated_files": has_associated_files,
            "collection": has_collection,
            "unsafe_active_content_present": unsafe_active,
        },
        "privacy_and_residue": {
            "extracted_text_hits": extracted_hits,
            "metadata_hits": metadata_hits,
            "sensitive_filename_hits": sensitive_filename_hits,
            "raw_or_decompressed_object_hits": raw_hits,
            "admitted_opaque_media_false_positive_proof": umbrella_binary_proof,
            "decoded_stream_count": stream_count,
            "decoded_stream_bytes_scanned": decoded_bytes,
            "stream_scan_errors": stream_errors,
        },
        "limitations": limitations,
        "warnings": warnings,
        "blockers": blockers,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    # Keep console output portable on Windows shells whose active code page is
    # not UTF-8.  The canonical receipt above remains UTF-8 with literal
    # Unicode; only the diagnostic stdout representation is ASCII-escaped.
    print(json.dumps(receipt, ensure_ascii=True, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
