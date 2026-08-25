#!/usr/bin/env python3
"""Strict cumulative PDF QA for the Indonesian O011 reader through Unit 6.

The verifier is deliberately bound to the exact admitted build, its two clean
cycle witnesses, and the exact cumulative Unit 5 prefix.  It emits no time or
machine-specific fields, so two executions over the same evidence must produce
byte-identical JSON.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import pdfplumber
import pypdf
from pypdf import PdfReader
from pypdf.generic import IndirectObject, StreamObject


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PDF_REL = "output/pdf/geometri-diferensial-manifold-mulus-hingga-unit-06-id.pdf"
OUTPUT_REL = "qa/unit-06/pdf_structural_qa.json"
BUILD_REL = "qa/unit-06/build.json"
PREFIX_BUILD_REL = "qa/unit-05/build.json"
PREFIX_PDF_REL = "output/pdf/geometri-diferensial-manifold-mulus-hingga-unit-05-id.pdf"
LECTURE_SOURCE_REL = "source/units/unit-06/lecture06.id.tex"
MATH_QA_REL = "qa/unit-06/POST_REPAIR_MATH_QA.json"
TERMINOLOGY_QA_REL = "qa/terminology/FIELD_TERMINOLOGY_PROPAGATION_U01_U06.json"

EXPECTED_PDF_BYTES = 4_765_606
EXPECTED_PDF_SHA256 = "40bf26d196ff04c38c6c99e8e9669a86bb5e6d31124b904b7ad154e7948cdec1"
EXPECTED_PAGES = 105
EXPECTED_BUILD_BYTES = 5_146
EXPECTED_BUILD_SHA256 = "fa3ff197c5dd03be1aff6766ac1a3e8db779ebf9557091cf1aac4f9fa836f466"
EXPECTED_PREFIX_BUILD_BYTES = 8_435
EXPECTED_PREFIX_BUILD_SHA256 = "1e925aa7108f8e2c4d8394a8f90c8fa5c1cbd24725dc53517936082c58e7326f"
EXPECTED_PREFIX_PDF_BYTES = 4_385_195
EXPECTED_PREFIX_PDF_SHA256 = "7aca79b4cfc937760463fe193a21373d5ad0acf18c79086faaf2a09189e08628"
EXPECTED_LECTURE_SOURCE_BYTES = 32_034
EXPECTED_LECTURE_SOURCE_SHA256 = "180c553eb556d91ba733e00f012bd0ece36c32e66704c992f0c64244ab6e05e8"
EXPECTED_MATH_QA_BYTES = 28_914
EXPECTED_MATH_QA_SHA256 = "b462de3f20b2a650d3f430660c993b598eba37f8acb0e4cc7187c0e171ee0cc7"
EXPECTED_TERMINOLOGY_QA_BYTES = 9_363
EXPECTED_TERMINOLOGY_QA_SHA256 = "c625cb3b97b1032dcec864c3ea06d7098f4a5ab7274078493f86e91c0e1de811"
EXPECTED_A4_POINTS = [595.276, 841.89]
EXPECTED_MARGIN_MM = 22.0
EXPECTED_MARGIN_POINTS = EXPECTED_MARGIN_MM * 72.0 / 25.4
EXPECTED_METADATA = {
    "/Author": "Holger Brenner, Terjemahan Bahasa Indonesia independen",
    "/Title": "Geometri Diferensial dan Manifold Mulus Pembaca kumulatif hingga Unit 6",
    "/Creator": "LaTeX with hyperref",
}
EXPECTED_PAGE_LABELS = ["1", "i", "ii", "iii"] + [str(i) for i in range(1, 102)]
EXPECTED_EXERCISES = Counter({str(i): 1 for i in range(1, 19)})
EXPECTED_SOLUTIONS = Counter({"2": 1, "6": 1, "9": 1})
EXPECTED_GRADED = {
    "6.15": r"Soal 6\.15\.\s*\(2 poin\)",
    "6.16": r"Soal 6\.16\.\s*\(4 poin\)",
    "6.17": r"Soal 6\.17\.\s*\(4 poin\)",
    "6.18": r"Soal 6\.18\.\s*\(4 poin\)",
}

REQUIRED_TEXT = {
    "work title": r"\bGeometri Diferensial dan Manifold Mulus\b",
    "cumulative boundary": r"\bPembaca kumulatif hingga Unit 6\b",
    "Unit 6 part": r"\bBagian VI Unit 6\b",
    "Unit 6 lecture": (
        r"\bKuliah 6: Turunan Kovarian, Medan Vektor Paralel, dan Transpor Paralel\b"
    ),
    "Unit 6 worksheet": r"\bLembar Kerja 6\b",
    "source-supplied solutions": r"\bSolusi yang disediakan oleh sumber\b",
    "text license": r"\bCC BY-SA 4\.0\b",
    "media rights": r"\bAtribusi dan Hak Media\b",
}

# Each adverse-ledger item 0054--0069 must have a reader-visible disclosure.
# Patterns intentionally match the stable Indonesian prose around mathematical
# glyphs whose extracted spacing can vary by PDF library.
CORRECTION_PATTERNS = {
    "O011-CORR-0054": r"Relasi pembuka diperbaiki.*?hipermuka tidak sama dengan seluruh ruang sekitarnya",
    "O011-CORR-0055": r"Evaluasi berlebih.*?setelah.*?dihapus karena.*?sudah menentukan titiknya",
    "O011-CORR-0056": r"Ruas kiri dievaluasi di.*?agar identitas ini konsisten dengan ruas kanan",
    "O011-CORR-0057": r"Domain.*?dan.*?diseragamkan menjadi interval.*?sumber memakai",
    "O011-CORR-0058": r"Kodomain.*?diperbaiki menjadi.*?dengan syarat nilai tangensial",
    "O011-CORR-0059": r"tidak membuktikan bahwa solusi persamaan diferensial tetap tangensial",
    "O011-CORR-0060": r"Satu tanda kurung tutup berlebih pada faktor.*?dihapus",
    "O011-CORR-0061": r"Nilai awal kombinasi linear diperbaiki dari.*?menjadi",
    "O011-CORR-0062": r"Faktor kedua pada hasil kali dalam di titik awal diperbaiki dari.*?menjadi",
    "O011-CORR-0063": r"Tanda sama dengan pada sumber diperbaiki menjadi tanda keanggotaan",
    "O011-CORR-0064": r"Syarat [“\"]konstan[”\"] ditambahkan",
    "O011-CORR-0065": r"Domain sumber.*?dibatasi pada interval di atas",
    "O011-CORR-0066": r"Sumber menyatakan grup isometri penuh.*?transpor paralel mempertahankan orientasi",
    "O011-CORR-0067": r"Tanda pada kedua kolom diperbaiki agar matriks ini sesuai",
    "O011-CORR-0068": r"Sumber mengidentifikasi ruang singgung hiperbidang afin langsung dengan",
    "O011-CORR-0069": r"menerapkan teorema eksistensi lokal langsung pada seluruh interval",
}

EXPECTED_MODEL_PROVENANCE = "OpenAI Codex gpt-5.6-sol, Ultra"
UNIT6_MEDIA = {
    "filename": "Parallel transport sphere2.svg",
    "creator": "Silly rabbit",
    "source_context": "Wikipedia bahasa Inggris",
    "creation": "karya sendiri",
    "license": "CC BY-SA 3.0",
    "source_uri": "https://commons.wikimedia.org/wiki/File:Parallel_transport_sphere2.svg",
    "license_uri": "https://creativecommons.org/licenses/by-sa/3.0/",
}

REQUIRED_BOOKMARKS = {
    "Unit 6 part": r"^VI Unit 6$",
    "Unit 6 lecture": r"^Kuliah 6$",
    "Unit 6 worksheet": r"^Lembar Kerja 6$",
    "source solutions": r"^Solusi yang disediakan oleh sumber$",
    "media rights": r"^Atribusi dan Hak Media$",
    "Unit 6 media": r"^Unit 6$",
}

FORBIDDEN_TEXT = {
    "local filesystem path": re.compile(
        r"(?:[A-Za-z]:[\\/](?:Users|Documents|AppData)[\\/]|/Users/|/home/)",
        re.IGNORECASE,
    ),
    "credential or token": re.compile(
        r"(?:ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|"
        r"authorization\s*:\s*bearer|access[_ -]?token|api[_ -]?token)",
        re.IGNORECASE,
    ),
    "task/thread identifier": re.compile(
        r"\b01[a-f0-9]{6,}(?:-[a-f0-9]{4,}){2,}\b", re.IGNORECASE
    ),
    "umbrella metadata residue": re.compile(
        r"(?:\bTTP\b|Translation and Transcription Project)", re.IGNORECASE
    ),
    "replacement character": re.compile("\ufffd"),
    "raw wiki markup": re.compile(
        r"(?:\[\[|\]\]|\{\{(?:Latex|Definitionslink|Relationskette|Math|Abbildung)|"
        r"Kategorie:Latexseite)",
        re.IGNORECASE,
    ),
}

FORBIDDEN_RAW = {
    "local filesystem path": re.compile(
        rb"(?:[A-Za-z]:[\\/](?:Users|Documents|AppData)[\\/]|/Users/|/home/)",
        re.IGNORECASE,
    ),
    "credential or token": re.compile(
        rb"(?:ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|"
        rb"authorization\s*:\s*bearer|access[_ -]?token|api[_ -]?token)",
        re.IGNORECASE,
    ),
    "task/thread identifier": re.compile(
        rb"\b01[a-f0-9]{6,}(?:-[a-f0-9]{4,}){2,}\b", re.IGNORECASE
    ),
    "umbrella metadata residue": re.compile(
        rb"(?:\bTTP\b|Translation and Transcription Project)", re.IGNORECASE
    ),
    "UTF-8 replacement character": re.compile(b"\xef\xbf\xbd"),
}

FATAL_LOG_PATTERNS = {
    "fatal error": re.compile(r"Fatal error", re.IGNORECASE),
    "emergency stop": re.compile(r"Emergency stop", re.IGNORECASE),
    "TeX/LaTeX error": re.compile(r"(?:^! |LaTeX Error|Package\s+\S+\s+Error)", re.IGNORECASE),
    "undefined control": re.compile(r"Undefined control sequence", re.IGNORECASE),
    "undefined references": re.compile(
        r"(?:undefined references|Reference .+ undefined)", re.IGNORECASE
    ),
    "undefined citations": re.compile(
        r"(?:undefined citations|Citation .+ undefined)", re.IGNORECASE
    ),
    "duplicate destination": re.compile(
        r"(?:destination with the same identifier|duplicate destination)", re.IGNORECASE
    ),
}
WARNING_LOG_PATTERNS = {
    "overfull box": re.compile(r"Overfull \\[hv]box", re.IGNORECASE),
    "underfull box": re.compile(r"Underfull \\[hv]box", re.IGNORECASE),
    "LaTeX/package warning": re.compile(r"(?:LaTeX|Package\s+\S+) Warning", re.IGNORECASE),
}

UNSAFE_ANNOTATION_SUBTYPES = {
    "/FileAttachment",
    "/RichMedia",
    "/Movie",
    "/Sound",
    "/Screen",
    "/Widget",
}
SAFE_ACTIONS = {"/GoTo", "/URI"}
SOURCE_ORPHAN_PUNCTUATION = re.compile(r"^[.,;:!?…]+\}*$")
EXTRACTED_PUNCTUATION_ONLY = re.compile(r"^[.,;:!?…]+$")
VISUAL_PUNCTUATION = {".", ",", ";", ":"}
SENTENCE_TERMINATORS = {".", "!", "?"}
PUNCTUATION_NEIGHBOR_RADIUS_POINTS = 12.0
CONCATENATION_GAP_POINTS = 1.0


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def bytes_sha(path: Path) -> dict[str, object]:
    return {"bytes": path.stat().st_size, "sha256": sha256(path)}


def normalize_text(value: str) -> str:
    value = re.sub(r"(?<=\w)-[ \t]*\r?\n[ \t]*(?=\w)", "", value)
    return re.sub(r"\s+", " ", value).strip()


def dereference(value: Any) -> Any:
    return value.get_object() if hasattr(value, "get_object") else value


def indirect_key(value: Any) -> str:
    if hasattr(value, "idnum"):
        return f"{value.idnum}:{value.generation}"
    return repr(value)


def relative(path: Path) -> str:
    return path.resolve().relative_to(PROJECT_ROOT).as_posix()


def add_blocker(blockers: list[str], condition: bool, message: str) -> None:
    if not condition:
        blockers.append(message)


def punctuation_only_lines(
    page_text: list[str], first_physical_page: int
) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    for offset, text in enumerate(page_text):
        for line_number, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if stripped and EXTRACTED_PUNCTUATION_ONLY.fullmatch(stripped):
                findings.append(
                    {
                        "page": first_physical_page + offset,
                        "line": line_number,
                        "text": stripped,
                    }
                )
    return findings


def box_distance(left: dict[str, object], right: dict[str, object]) -> float:
    horizontal = max(
        float(left["x0"]) - float(right["x1"]),
        float(right["x0"]) - float(left["x1"]),
        0.0,
    )
    vertical = max(
        float(left["top"]) - float(right["bottom"]),
        float(right["top"]) - float(left["bottom"]),
        0.0,
    )
    return (horizontal * horizontal + vertical * vertical) ** 0.5


def inspect_unit6_punctuation_geometry(
    plumber_pages: list[Any],
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    visual_orphans: list[dict[str, object]] = []
    sentence_concatenations: list[dict[str, object]] = []
    for page_number in range(83, 102):
        chars = plumber_pages[page_number - 1].chars
        for index, char in enumerate(chars):
            text = str(char.get("text", ""))
            if text in VISUAL_PUNCTUATION:
                nearest = min(
                    (
                        box_distance(char, other)
                        for other_index, other in enumerate(chars)
                        if other_index != index and str(other.get("text", "")).strip()
                    ),
                    default=float("inf"),
                )
                if nearest > PUNCTUATION_NEIGHBOR_RADIUS_POINTS:
                    visual_orphans.append(
                        {
                            "page": page_number,
                            "text": text,
                            "x0": round(float(char["x0"]), 3),
                            "top": round(float(char["top"]), 3),
                            "nearest_glyph_distance_points": round(nearest, 3),
                        }
                    )
            if text not in SENTENCE_TERMINATORS:
                continue
            for other_index, other in enumerate(chars):
                if other_index == index:
                    continue
                other_text = str(other.get("text", ""))
                if not other_text or not other_text[0].isupper():
                    continue
                vertical_separation = max(
                    float(char["top"]), float(other["top"])
                ) - min(float(char["bottom"]), float(other["bottom"]))
                gap = float(other["x0"]) - float(char["x1"])
                if vertical_separation <= 1.5 and 0.0 <= gap <= CONCATENATION_GAP_POINTS:
                    sentence_concatenations.append(
                        {
                            "page": page_number,
                            "punctuation": text,
                            "next_character": other_text,
                            "gap_points": round(gap, 3),
                            "top": round(float(char["top"]), 3),
                        }
                    )
    return visual_orphans, sentence_concatenations


def collect_fonts(reader: PdfReader) -> dict[str, dict[str, object]]:
    fonts: dict[str, dict[str, object]] = {}
    visited_xobjects: set[str] = set()

    def walk(resources_ref: Any) -> None:
        resources = dereference(resources_ref)
        if not isinstance(resources, dict):
            return
        for font_ref in (dereference(resources.get("/Font", {})) or {}).values():
            font = dereference(font_ref)
            descriptor = dereference(font.get("/FontDescriptor", {})) or {}
            fonts[indirect_key(font_ref)] = {
                "base_font": str(font.get("/BaseFont", "")),
                "subtype": str(font.get("/Subtype", "")),
                "to_unicode": bool(font.get("/ToUnicode")),
                "embedded": any(
                    bool(descriptor.get(key))
                    for key in ("/FontFile", "/FontFile2", "/FontFile3")
                ),
            }
        for object_ref in (dereference(resources.get("/XObject", {})) or {}).values():
            key = indirect_key(object_ref)
            if key in visited_xobjects:
                continue
            visited_xobjects.add(key)
            obj = dereference(object_ref)
            if isinstance(obj, dict) and obj.get("/Resources"):
                walk(obj.get("/Resources"))

    for page in reader.pages:
        walk(page.get("/Resources", {}))
    return dict(sorted(fonts.items()))


def scan_raw_objects(
    reader: PdfReader, path: Path
) -> tuple[dict[str, list[str]], int, int, list[str]]:
    hits = {label: [] for label in FORBIDDEN_RAW}
    raw = path.read_bytes()
    for label, pattern in FORBIDDEN_RAW.items():
        if pattern.search(raw):
            hits[label].append("raw-pdf")
    stream_count = 0
    decoded_bytes = 0
    errors: list[str] = []
    for generation, entries in reader.xref.items():
        if generation == 65535:
            continue
        for object_number in entries:
            object_id = f"{object_number}:{generation}"
            try:
                obj = reader.get_object(IndirectObject(object_number, generation, reader))
            except Exception as exc:  # recorded, never hidden
                errors.append(f"{object_id}: object read failed: {type(exc).__name__}")
                continue
            if not isinstance(obj, StreamObject):
                continue
            stream_count += 1
            try:
                data = obj.get_data()
            except Exception as exc:  # recorded, never hidden
                errors.append(f"{object_id}: stream decode failed: {type(exc).__name__}")
                continue
            decoded_bytes += len(data)
            for label, pattern in FORBIDDEN_RAW.items():
                if pattern.search(data):
                    hits[label].append(object_id)
    return hits, stream_count, decoded_bytes, errors


def collect_bookmarks(reader: PdfReader) -> tuple[list[dict[str, object]], list[str]]:
    records: list[dict[str, object]] = []
    errors: list[str] = []

    def walk(items: list[Any], depth: int) -> None:
        for item in items:
            if isinstance(item, list):
                walk(item, depth + 1)
                continue
            title = normalize_text(str(getattr(item, "title", "") or ""))
            try:
                page = reader.get_destination_page_number(item) + 1
            except Exception as exc:
                page = None
                errors.append(f"{title or '<empty>'}: {type(exc).__name__}")
            records.append({"title": title, "depth": depth, "page": page})

    outline = reader.outline
    if isinstance(outline, list):
        walk(outline, 0)
    else:
        errors.append("outline is not a list")
    return records, errors


def inspect_annotations(
    reader: PdfReader,
) -> tuple[Counter[str], Counter[str], int, list[dict[str, str]], list[str]]:
    subtypes: Counter[str] = Counter()
    uris: Counter[str] = Counter()
    internal_links = 0
    unsafe_actions: list[dict[str, str]] = []
    attachment_markers: list[str] = []
    for page_number, page in enumerate(reader.pages, start=1):
        for annotation_ref in page.get("/Annots", []) or []:
            annotation = dereference(annotation_ref)
            subtype = str(annotation.get("/Subtype", ""))
            subtypes[subtype] += 1
            if annotation.get("/FS") or annotation.get("/EF"):
                attachment_markers.append(f"page-{page_number}")
            action = dereference(annotation.get("/A")) if annotation.get("/A") else None
            if action:
                action_type = str(action.get("/S", ""))
                if action_type == "/URI":
                    uri = str(action.get("/URI", ""))
                    uris[uri] += 1
                    parsed = urlparse(uri)
                    if parsed.scheme != "https" or not parsed.netloc:
                        unsafe_actions.append(
                            {"owner": f"page-{page_number}", "type": action_type, "uri": uri}
                        )
                elif action_type == "/GoTo":
                    internal_links += 1
                elif action_type not in SAFE_ACTIONS:
                    unsafe_actions.append(
                        {"owner": f"page-{page_number}", "type": action_type}
                    )
            elif annotation.get("/Dest"):
                internal_links += 1
            if annotation.get("/AA"):
                unsafe_actions.append(
                    {"owner": f"page-{page_number}", "type": "/AA"}
                )
    return subtypes, uris, internal_links, unsafe_actions, sorted(set(attachment_markers))


def scan_logs(build: dict[str, Any], blockers: list[str]) -> dict[str, object]:
    fatal_hits: list[dict[str, object]] = []
    warning_hits: list[dict[str, object]] = []
    verified: list[dict[str, object]] = []
    for cycle in build.get("cycles", []):
        for declared in cycle.get("logs", []):
            path = PROJECT_ROOT / declared["path"]
            actual = bytes_sha(path) if path.is_file() else None
            matches = bool(
                actual
                and actual["bytes"] == declared["bytes"]
                and actual["sha256"] == declared["sha256"]
            )
            verified.append(
                {
                    "path": declared["path"],
                    "declared": {"bytes": declared["bytes"], "sha256": declared["sha256"]},
                    "actual": actual,
                    "matches": matches,
                }
            )
            if not matches:
                blockers.append(f"build-log identity mismatch: {declared['path']}")
                continue
            for number, line in enumerate(
                path.read_text(encoding="utf-8-sig", errors="replace").splitlines(), start=1
            ):
                for label, pattern in FATAL_LOG_PATTERNS.items():
                    if pattern.search(line):
                        fatal_hits.append(
                            {"path": declared["path"], "line": number, "kind": label, "text": line.strip()}
                        )
                for label, pattern in WARNING_LOG_PATTERNS.items():
                    if pattern.search(line):
                        warning_hits.append(
                            {"path": declared["path"], "line": number, "kind": label, "text": line.strip()}
                        )
    if fatal_hits:
        blockers.append(f"fatal/undefined/duplicate-destination log findings: {len(fatal_hits)}")
    if warning_hits:
        blockers.append(f"build warning diagnostics: {len(warning_hits)}")
    return {
        "verified_logs": verified,
        "fatal_hits": fatal_hits,
        "warning_hits": warning_hits,
        "overfull_hits": [hit for hit in warning_hits if hit["kind"] == "overfull box"],
        "underfull_hits": [hit for hit in warning_hits if hit["kind"] == "underfull box"],
        "diagnostic_count": len(fatal_hits) + len(warning_hits),
        "zero_diagnostics": not fatal_hits and not warning_hits,
    }


def verify_final_source_and_math_qa(blockers: list[str]) -> dict[str, object]:
    source_path = PROJECT_ROOT / LECTURE_SOURCE_REL
    source_identity = bytes_sha(source_path)
    expected_source_identity = {
        "bytes": EXPECTED_LECTURE_SOURCE_BYTES,
        "sha256": EXPECTED_LECTURE_SOURCE_SHA256,
    }
    add_blocker(
        blockers,
        source_identity == expected_source_identity,
        f"final lecture source identity mismatch: {source_identity}",
    )
    source_orphan_lines = [
        {"line": line_number, "text": line.strip()}
        for line_number, line in enumerate(
            source_path.read_text(encoding="utf-8").splitlines(), start=1
        )
        if SOURCE_ORPHAN_PUNCTUATION.fullmatch(line.strip())
    ]
    add_blocker(
        blockers,
        not source_orphan_lines,
        f"final lecture source retains punctuation-only logical lines: {source_orphan_lines}",
    )

    math_qa_path = PROJECT_ROOT / MATH_QA_REL
    math_qa_identity = bytes_sha(math_qa_path)
    expected_math_qa_identity = {
        "bytes": EXPECTED_MATH_QA_BYTES,
        "sha256": EXPECTED_MATH_QA_SHA256,
    }
    add_blocker(
        blockers,
        math_qa_identity == expected_math_qa_identity,
        f"post-repair math QA identity mismatch: {math_qa_identity}",
    )
    math_qa = json.loads(math_qa_path.read_text(encoding="utf-8"))
    target_lecture_sha = (math_qa.get("target_sha256") or {}).get("lecture")
    punctuation_check = (
        "lecture has no punctuation-only lines, including punctuation before a closing macro brace"
    )
    math_checks = math_qa.get("checks", [])
    add_blocker(blockers, math_qa.get("status") == "pass", "post-repair math QA does not pass")
    add_blocker(
        blockers,
        target_lecture_sha == EXPECTED_LECTURE_SOURCE_SHA256,
        f"post-repair math QA binds the wrong lecture source: {target_lecture_sha}",
    )
    add_blocker(
        blockers,
        punctuation_check in math_checks,
        "post-repair math QA lacks the punctuation-orphan closure check",
    )

    terminology_path = PROJECT_ROOT / TERMINOLOGY_QA_REL
    terminology_identity = bytes_sha(terminology_path)
    expected_terminology_identity = {
        "bytes": EXPECTED_TERMINOLOGY_QA_BYTES,
        "sha256": EXPECTED_TERMINOLOGY_QA_SHA256,
    }
    add_blocker(
        blockers,
        terminology_identity == expected_terminology_identity,
        f"terminology QA identity mismatch: {terminology_identity}",
    )
    terminology = json.loads(terminology_path.read_text(encoding="utf-8"))
    terminology_lecture_rows = [
        row
        for row in terminology.get("files", [])
        if row.get("path") == LECTURE_SOURCE_REL
    ]
    terminology_post_checks = terminology.get("post_checks", {})
    add_blocker(
        blockers,
        terminology.get("workflow") == "o011-indonesian-field-terminology-u01-u06-v1"
        and terminology.get("status") == "pass",
        "terminology QA workflow/status mismatch",
    )
    add_blocker(
        blockers,
        len(terminology_lecture_rows) == 1
        and terminology_lecture_rows[0].get("after_bytes")
        == EXPECTED_LECTURE_SOURCE_BYTES
        and terminology_lecture_rows[0].get("after_sha256")
        == EXPECTED_LECTURE_SOURCE_SHA256,
        f"terminology QA binds the wrong final lecture row: {terminology_lecture_rows}",
    )
    add_blocker(
        blockers,
        bool(terminology_post_checks)
        and all(value == 0 for value in terminology_post_checks.values()),
        f"terminology QA post-checks are not all zero: {terminology_post_checks}",
    )
    return {
        "lecture_source": {
            "path": LECTURE_SOURCE_REL,
            **source_identity,
            "punctuation_only_logical_lines": source_orphan_lines,
        },
        "post_repair_math_qa": {
            "path": MATH_QA_REL,
            **math_qa_identity,
            "status": math_qa.get("status"),
            "checks_passed": math_qa.get("checks_passed"),
            "target_lecture_sha256": target_lecture_sha,
            "punctuation_orphan_check_present": punctuation_check in math_checks,
        },
        "terminology_qa": {
            "path": TERMINOLOGY_QA_REL,
            **terminology_identity,
            "status": terminology.get("status"),
            "post_checks": terminology_post_checks,
            "final_lecture_row": (
                terminology_lecture_rows[0]
                if len(terminology_lecture_rows) == 1
                else None
            ),
        },
    }


def verify_build_binding(blockers: list[str]) -> tuple[dict[str, Any], dict[str, object]]:
    build_path = PROJECT_ROOT / BUILD_REL
    identity = bytes_sha(build_path)
    add_blocker(
        blockers,
        identity == {"bytes": EXPECTED_BUILD_BYTES, "sha256": EXPECTED_BUILD_SHA256},
        f"Unit 6 build receipt identity mismatch: {identity}",
    )
    build = json.loads(build_path.read_text(encoding="utf-8"))
    add_blocker(blockers, build.get("workflow") == "o011-through-unit06-pdf-build-v1", "wrong build workflow")
    add_blocker(blockers, build.get("deterministic_clean_cycles") is True, "build does not assert deterministic clean cycles")
    add_blocker(blockers, build.get("cumulative_prefix_receipt") == PREFIX_BUILD_REL, "wrong cumulative prefix receipt")
    expected_output = {"path": PDF_REL, "bytes": EXPECTED_PDF_BYTES, "sha256": EXPECTED_PDF_SHA256}
    add_blocker(blockers, build.get("output") == expected_output, f"build output binding mismatch: {build.get('output')}")

    cycles = build.get("cycles", [])
    add_blocker(blockers, len(cycles) == 2, f"expected exactly two clean cycles, found {len(cycles)}")
    cycle_checks: list[dict[str, object]] = []
    for expected_number, cycle in enumerate(cycles, start=1):
        path = PROJECT_ROOT / cycle.get("pdf", "")
        actual = bytes_sha(path) if path.is_file() else None
        passed = bool(
            cycle.get("cycle") == expected_number
            and cycle.get("bytes") == EXPECTED_PDF_BYTES
            and cycle.get("sha256") == EXPECTED_PDF_SHA256
            and actual == {"bytes": EXPECTED_PDF_BYTES, "sha256": EXPECTED_PDF_SHA256}
        )
        cycle_checks.append(
            {"cycle": expected_number, "path": cycle.get("pdf"), "actual": actual, "passed": passed}
        )
        if not passed:
            blockers.append(f"clean cycle {expected_number} is not bound to the exact PDF")
    if len(cycle_checks) == 2:
        add_blocker(
            blockers,
            cycle_checks[0]["actual"] == cycle_checks[1]["actual"],
            "two clean-cycle PDF identities differ",
        )

    input_checks: list[dict[str, object]] = []
    for declared in build.get("inputs", []):
        rel_path = str(declared.get("path", ""))
        candidate = (PROJECT_ROOT / rel_path).resolve()
        within_root = PROJECT_ROOT == candidate or PROJECT_ROOT in candidate.parents
        actual = bytes_sha(candidate) if within_root and candidate.is_file() else None
        passed = bool(
            within_root
            and actual
            and actual["bytes"] == declared.get("bytes")
            and actual["sha256"] == declared.get("sha256")
        )
        input_checks.append(
            {"path": rel_path, "declared": {"bytes": declared.get("bytes"), "sha256": declared.get("sha256")}, "actual": actual, "passed": passed}
        )
        if not passed:
            blockers.append(f"build input identity mismatch: {rel_path}")

    log_scan = scan_logs(build, blockers)
    return build, {
        "receipt": {"path": BUILD_REL, **identity},
        "cycles": cycle_checks,
        "inputs": input_checks,
        "log_scan": log_scan,
    }


def verify_prefix(
    reader: PdfReader, plumber_pages: list[Any], blockers: list[str]
) -> dict[str, object]:
    prefix_build_path = PROJECT_ROOT / PREFIX_BUILD_REL
    prefix_build_identity = bytes_sha(prefix_build_path)
    add_blocker(
        blockers,
        prefix_build_identity
        == {"bytes": EXPECTED_PREFIX_BUILD_BYTES, "sha256": EXPECTED_PREFIX_BUILD_SHA256},
        f"Unit 5 prefix receipt identity mismatch: {prefix_build_identity}",
    )
    prefix_build = json.loads(prefix_build_path.read_text(encoding="utf-8"))
    expected_prefix_output = {
        "path": PREFIX_PDF_REL,
        "bytes": EXPECTED_PREFIX_PDF_BYTES,
        "sha256": EXPECTED_PREFIX_PDF_SHA256,
    }
    add_blocker(
        blockers,
        prefix_build.get("output") == expected_prefix_output,
        f"Unit 5 prefix output binding mismatch: {prefix_build.get('output')}",
    )
    prefix_path = PROJECT_ROOT / PREFIX_PDF_REL
    prefix_pdf_identity = bytes_sha(prefix_path)
    add_blocker(
        blockers,
        prefix_pdf_identity
        == {"bytes": EXPECTED_PREFIX_PDF_BYTES, "sha256": EXPECTED_PREFIX_PDF_SHA256},
        f"Unit 5 prefix PDF identity mismatch: {prefix_pdf_identity}",
    )

    prefix_reader = PdfReader(str(prefix_path))
    add_blocker(blockers, len(prefix_reader.pages) == 86, f"Unit 5 prefix page count is {len(prefix_reader.pages)}, expected 86")
    # Physical pages 5--82 are the complete Unit 1--5 body.  Unit 6 begins on
    # physical page 83 in the cumulative reader; the Unit 5 stand-alone reader
    # begins its back matter there.  Compare the body page content streams and
    # a second extractor's text, not only headings or a few sample pages.
    start, stop = 4, 82
    stream_mismatches: list[int] = []
    stream_left: list[str] = []
    stream_right: list[str] = []
    for index in range(start, stop):
        left = prefix_reader.pages[index].get_contents().get_data()
        right = reader.pages[index].get_contents().get_data()
        left_hash = hashlib.sha256(left).hexdigest()
        right_hash = hashlib.sha256(right).hexdigest()
        stream_left.append(left_hash)
        stream_right.append(right_hash)
        if left != right:
            stream_mismatches.append(index + 1)

    with pdfplumber.open(prefix_path) as prefix_plumber:
        plumber_mismatches = [
            index + 1
            for index in range(start, stop)
            if (prefix_plumber.pages[index].extract_text() or "")
            != (plumber_pages[index].extract_text() or "")
        ]
        prefix_sizes = [
            [round(float(page.width), 3), round(float(page.height), 3)]
            for page in prefix_plumber.pages[start:stop]
        ]
    cumulative_sizes = [
        [round(float(page.width), 3), round(float(page.height), 3)]
        for page in plumber_pages[start:stop]
    ]
    add_blocker(blockers, not stream_mismatches, f"Unit 1--5 PDF content-stream prefix mismatches: {stream_mismatches}")
    add_blocker(blockers, not plumber_mismatches, f"Unit 1--5 pdfplumber text prefix mismatches: {plumber_mismatches}")
    add_blocker(blockers, prefix_sizes == cumulative_sizes, "Unit 1--5 page-size prefix mismatch")
    aggregate_left = hashlib.sha256("\n".join(stream_left).encode("ascii")).hexdigest()
    aggregate_right = hashlib.sha256("\n".join(stream_right).encode("ascii")).hexdigest()
    return {
        "prefix_receipt": {"path": PREFIX_BUILD_REL, **prefix_build_identity},
        "prefix_pdf": {"path": PREFIX_PDF_REL, **prefix_pdf_identity, "pages": len(prefix_reader.pages)},
        "compared_physical_pages": {"first": 5, "last": 82, "count": stop - start},
        "content_stream_aggregate_sha256_prefix": aggregate_left,
        "content_stream_aggregate_sha256_cumulative": aggregate_right,
        "content_stream_mismatch_pages": stream_mismatches,
        "pdfplumber_text_mismatch_pages": plumber_mismatches,
        "page_sizes_equal": prefix_sizes == cumulative_sizes,
        "passed": not stream_mismatches and not plumber_mismatches and prefix_sizes == cumulative_sizes,
    }


def main() -> int:
    blockers: list[str] = []
    warnings: list[str] = []
    limitations: list[str] = []
    pdf_path = PROJECT_ROOT / PDF_REL
    output_path = PROJECT_ROOT / OUTPUT_REL
    script_path = Path(__file__).resolve()

    source_and_math_qa_binding = verify_final_source_and_math_qa(blockers)
    build, build_binding = verify_build_binding(blockers)
    pdf_identity = bytes_sha(pdf_path)
    add_blocker(
        blockers,
        pdf_identity == {"bytes": EXPECTED_PDF_BYTES, "sha256": EXPECTED_PDF_SHA256},
        f"target PDF identity mismatch: {pdf_identity}",
    )

    reader = PdfReader(str(pdf_path))
    catalog = reader.root_object
    actual_pages = len(reader.pages)
    add_blocker(blockers, actual_pages == EXPECTED_PAGES, f"page count is {actual_pages}, expected {EXPECTED_PAGES}")
    add_blocker(blockers, not reader.is_encrypted, "PDF is encrypted")

    media_sizes = [
        [round(float(page.mediabox.width), 3), round(float(page.mediabox.height), 3)]
        for page in reader.pages
    ]
    crop_sizes = [
        [round(float(page.cropbox.width), 3), round(float(page.cropbox.height), 3)]
        for page in reader.pages
    ]
    rotations = [int(page.get("/Rotate", 0) or 0) % 360 for page in reader.pages]
    add_blocker(blockers, all(size == EXPECTED_A4_POINTS for size in media_sizes), "one or more MediaBox dimensions are not A4")
    add_blocker(blockers, all(size == EXPECTED_A4_POINTS for size in crop_sizes), "one or more CropBox dimensions are not A4")
    add_blocker(blockers, not any(rotations), "one or more pages are rotated")

    page_labels = [str(item) for item in reader.page_labels]
    add_blocker(blockers, page_labels == EXPECTED_PAGE_LABELS, "page-label sequence does not match title/roman/frontmatter plus 1--101 body numbering")
    catalog_language = str(catalog.get("/Lang", ""))
    add_blocker(blockers, catalog_language == "id-ID", f"catalog /Lang is {catalog_language!r}")

    metadata = {str(key): str(value) for key, value in (reader.metadata or {}).items()}
    metadata_mismatches = {
        key: {"expected": expected, "actual": metadata.get(key)}
        for key, expected in EXPECTED_METADATA.items()
        if metadata.get(key) != expected
    }
    volatile_metadata = sorted(key for key in ("/CreationDate", "/ModDate") if key in metadata)
    trailer_id_present = bool(reader.trailer.get("/ID"))
    if metadata_mismatches:
        blockers.append(f"metadata mismatch: {metadata_mismatches}")
    if volatile_metadata:
        blockers.append(f"volatile metadata present: {volatile_metadata}")
    if trailer_id_present:
        blockers.append("volatile trailer /ID is present")

    pypdf_text = [page.extract_text() or "" for page in reader.pages]
    pypdf_empty = [i + 1 for i, text in enumerate(pypdf_text) if not text.strip()]
    with pdfplumber.open(pdf_path) as plumber:
        plumber_pages = list(plumber.pages)
        plumber_text = [page.extract_text() or "" for page in plumber_pages]
        plumber_layout_unit6_text = [
            page.extract_text(layout=True) or "" for page in plumber_pages[82:101]
        ]
        plumber_empty = [i + 1 for i, text in enumerate(plumber_text) if not text.strip()]
        plumber_sizes = [
            [round(float(page.width), 3), round(float(page.height), 3)]
            for page in plumber_pages
        ]

        # Centered 22 mm wrapper: the exact geometry declaration is hash-bound
        # by the build receipt, while independent word coordinates confirm the
        # body starts and repeatedly ends at the expected symmetric anchors.
        geometry_source = PROJECT_ROOT / "build/through-unit-06.tex"
        geometry_line = r"\usepackage[a4paper,margin=22mm,headheight=15pt]{geometry}"
        geometry_present = geometry_line in geometry_source.read_text(encoding="utf-8")
        part_pages = {21, 37, 54, 70}
        content_page_numbers = [
            page
            for page in list(range(6, 83)) + list(range(84, 102))
            if page not in part_pages
        ]
        page_layout: list[dict[str, object]] = []
        left_anchor_pages: list[int] = []
        right_anchor_pages: list[int] = []
        nominal_margin_overruns: list[dict[str, object]] = []
        outside_media_box: list[dict[str, object]] = []
        expected_right = EXPECTED_A4_POINTS[0] - EXPECTED_MARGIN_POINTS
        for page_number in content_page_numbers:
            page = plumber_pages[page_number - 1]
            words = [
                word
                for word in page.extract_words()
                if float(word["top"]) >= 50.0 and float(word["bottom"]) <= 790.0
            ]
            min_x = min((float(word["x0"]) for word in words), default=None)
            max_x = max((float(word["x1"]) for word in words), default=None)
            if min_x is not None and EXPECTED_MARGIN_POINTS - 3.0 <= min_x <= EXPECTED_MARGIN_POINTS + 1.0:
                left_anchor_pages.append(page_number)
            if any(abs(float(word["x1"]) - expected_right) <= 3.0 for word in words):
                right_anchor_pages.append(page_number)
            overruns = [
                word
                for word in words
                if float(word["x0"]) < EXPECTED_MARGIN_POINTS - 4.0
                or float(word["x1"]) > expected_right + 4.0
            ]
            outside = [
                word
                for word in words
                if float(word["x0"]) < -0.5
                or float(word["x1"]) > float(page.width) + 0.5
                or float(word["top"]) < -0.5
                or float(word["bottom"]) > float(page.height) + 0.5
            ]
            if overruns:
                nominal_margin_overruns.append(
                    {
                        "page": page_number,
                        "count": len(overruns),
                        "max_right": round(max(float(word["x1"]) for word in overruns), 3),
                        "samples": [str(word.get("text", "")) for word in overruns[:8]],
                    }
                )
            if outside:
                outside_media_box.append(
                    {
                        "page": page_number,
                        "count": len(outside),
                        "max_right": round(max(float(word["x1"]) for word in outside), 3),
                        "samples": [str(word.get("text", "")) for word in outside[:8]],
                    }
                )
            page_layout.append(
                {
                    "page": page_number,
                    "body_min_x": None if min_x is None else round(min_x, 3),
                    "body_max_x": None if max_x is None else round(max_x, 3),
                }
            )

        required_left_anchors = int(len(content_page_numbers) * 0.95)
        required_right_anchors = int(len(content_page_numbers) * 0.60)
        centered_wrapper_passed = bool(
            geometry_present
            and len(left_anchor_pages) >= required_left_anchors
            and len(right_anchor_pages) >= required_right_anchors
        )
        add_blocker(blockers, geometry_present, "hash-bound wrapper source does not declare geometry margin=22mm")
        add_blocker(blockers, len(left_anchor_pages) >= required_left_anchors, "too few body pages exhibit the 22 mm left anchor")
        add_blocker(blockers, len(right_anchor_pages) >= required_right_anchors, "too few body pages reach the symmetric 22 mm right anchor")

        prefix_integrity = verify_prefix(reader, plumber_pages, blockers)
        visual_punctuation_orphans, sentence_punctuation_concatenations = (
            inspect_unit6_punctuation_geometry(plumber_pages)
        )

    add_blocker(blockers, len(plumber_text) == actual_pages, "pdfplumber page count differs from pypdf")
    add_blocker(blockers, all(size == EXPECTED_A4_POINTS for size in plumber_sizes), "pdfplumber found non-A4 pages")
    add_blocker(blockers, not pypdf_empty, f"pypdf empty-text pages: {pypdf_empty}")
    add_blocker(blockers, not plumber_empty, f"pdfplumber empty-text pages: {plumber_empty}")
    pypdf_punctuation_only = punctuation_only_lines(pypdf_text[82:101], 83)
    pdfplumber_punctuation_only = punctuation_only_lines(plumber_text[82:101], 83)
    pdfplumber_layout_punctuation_only = punctuation_only_lines(
        plumber_layout_unit6_text, 83
    )
    add_blocker(
        blockers,
        not visual_punctuation_orphans,
        f"visually isolated Unit 6 punctuation glyphs: {visual_punctuation_orphans}",
    )
    add_blocker(
        blockers,
        not sentence_punctuation_concatenations,
        "sentence-terminal punctuation is geometrically concatenated with following text: "
        f"{sentence_punctuation_concatenations}",
    )
    if nominal_margin_overruns:
        warnings.append(
            f"content exceeds the nominal 22 mm body box on physical pages {[item['page'] for item in nominal_margin_overruns]}"
        )
    if outside_media_box:
        warnings.append(
            f"extracted word geometry extends beyond the A4 MediaBox on physical pages {[item['page'] for item in outside_media_box]}"
        )

    full_text = "\n".join(pypdf_text)
    normalized_full = normalize_text(full_text)
    normalized_pages = [normalize_text(text) for text in pypdf_text]
    unit6_text = normalize_text("\n".join(pypdf_text[82:101]))
    worksheet_text = normalize_text("\n".join(pypdf_text[93:99]))
    # The 6.2 solution heading begins at the foot of physical page 99 while
    # its body continues on page 100, so the exact solution span is 99--101.
    solution_text = normalize_text("\n".join(pypdf_text[98:101]))

    missing_required = [
        label for label, pattern in REQUIRED_TEXT.items() if not re.search(pattern, normalized_full)
    ]
    if missing_required:
        blockers.append(f"missing required reader text: {missing_required}")
    unit6_part_pages = [i + 1 for i, text in enumerate(normalized_pages) if re.search(REQUIRED_TEXT["Unit 6 part"], text)]
    add_blocker(blockers, unit6_part_pages == [83], f"Unit 6 part boundary is not exactly physical page 83: {unit6_part_pages}")

    exercise_counts = Counter(re.findall(r"(?<!Solusi )\bSoal 6\.(\d+)\.(?!\d)", worksheet_text))
    solution_counts = Counter(re.findall(r"\bSolusi Soal 6\.(\d+)(?!\d)", solution_text))
    add_blocker(blockers, exercise_counts == EXPECTED_EXERCISES, f"Unit 6 exercise headings mismatch: {dict(sorted(exercise_counts.items()))}")
    add_blocker(blockers, solution_counts == EXPECTED_SOLUTIONS, f"Unit 6 solution headings mismatch: {dict(sorted(solution_counts.items()))}")
    missing_graded = [label for label, pattern in EXPECTED_GRADED.items() if not re.search(pattern, worksheet_text)]
    if missing_graded:
        blockers.append(f"missing Unit 6 graded point markers: {missing_graded}")

    correction_presence = {
        correction_id: bool(re.search(pattern, unit6_text, re.IGNORECASE))
        for correction_id, pattern in CORRECTION_PATTERNS.items()
    }
    missing_corrections = [key for key, present in correction_presence.items() if not present]
    if missing_corrections:
        blockers.append(f"missing reader-visible Unit 6 correction disclosures: {missing_corrections}")

    model_count = normalized_full.count(EXPECTED_MODEL_PROVENANCE)
    add_blocker(blockers, model_count == 1, f"exact model provenance occurs {model_count} times, expected once")

    media_text_presence = {
        key: value in normalized_full
        for key, value in UNIT6_MEDIA.items()
        if key not in {"source_uri", "license_uri"}
    }
    missing_media_text = [key for key, present in media_text_presence.items() if not present]
    if missing_media_text:
        blockers.append(f"missing Unit 6 media/credit text: {missing_media_text}")

    bookmarks, bookmark_errors = collect_bookmarks(reader)
    bookmark_titles = [str(item["title"]) for item in bookmarks]
    missing_bookmarks = [
        label
        for label, pattern in REQUIRED_BOOKMARKS.items()
        if not any(re.search(pattern, title) for title in bookmark_titles)
    ]
    unresolved_bookmarks = [item for item in bookmarks if item["page"] is None]
    out_of_range_bookmarks = [
        item for item in bookmarks if isinstance(item["page"], int) and not 1 <= int(item["page"]) <= actual_pages
    ]
    if bookmark_errors or unresolved_bookmarks or out_of_range_bookmarks or missing_bookmarks:
        blockers.append(
            "bookmark closure failure: "
            f"errors={bookmark_errors}, unresolved={unresolved_bookmarks}, "
            f"out_of_range={out_of_range_bookmarks}, missing={missing_bookmarks}"
        )

    fonts = collect_fonts(reader)
    fonts_without_tounicode = sorted(key for key, value in fonts.items() if not value["to_unicode"])
    fonts_not_embedded = sorted(key for key, value in fonts.items() if not value["embedded"])
    if fonts_without_tounicode:
        blockers.append(f"fonts without ToUnicode: {fonts_without_tounicode}")
    if fonts_not_embedded:
        blockers.append(f"fonts not embedded: {fonts_not_embedded}")

    subtypes, uris, internal_links, unsafe_actions, attachment_markers = inspect_annotations(reader)
    source_uri_count = uris[UNIT6_MEDIA["source_uri"]]
    license_uri_count = uris[UNIT6_MEDIA["license_uri"]]
    add_blocker(blockers, source_uri_count >= 1, "Unit 6 media source URI is absent")
    add_blocker(blockers, license_uri_count >= 1, "Unit 6 media license URI is absent")
    if unsafe_actions:
        blockers.append(f"unsafe annotation actions: {unsafe_actions}")
    unsafe_subtypes = sorted(kind for kind in subtypes if kind in UNSAFE_ANNOTATION_SUBTYPES)

    names = dereference(catalog.get("/Names", {})) or {}
    has_javascript = bool(names.get("/JavaScript"))
    has_embedded_files = bool(names.get("/EmbeddedFiles"))
    has_acroform = bool(catalog.get("/AcroForm")) or bool(reader.get_fields() or {})
    has_associated_files = bool(catalog.get("/AF"))
    has_collection = bool(catalog.get("/Collection"))
    unsafe_active_content_present = bool(
        has_javascript
        or has_embedded_files
        or has_acroform
        or has_associated_files
        or has_collection
        or attachment_markers
        or unsafe_subtypes
        or unsafe_actions
    )
    if unsafe_active_content_present:
        blockers.append("PDF contains active, embedded, form, portfolio, or unsafe annotation content")

    extracted_hits = {
        label: sorted(set(match.group(0) for match in pattern.finditer(full_text)))
        for label, pattern in FORBIDDEN_TEXT.items()
        if pattern.search(full_text)
    }
    metadata_text = "\n".join(metadata.values())
    metadata_hits = {
        label: sorted(set(match.group(0) for match in pattern.finditer(metadata_text)))
        for label, pattern in FORBIDDEN_TEXT.items()
        if pattern.search(metadata_text)
    }
    raw_hits, stream_count, decoded_bytes, stream_errors = scan_raw_objects(reader, pdf_path)
    raw_hits = {key: value for key, value in raw_hits.items() if value}
    if extracted_hits or metadata_hits or raw_hits or stream_errors:
        blockers.append(
            "privacy/residue scan failure: "
            f"text={extracted_hits}, metadata={metadata_hits}, raw={raw_hits}, stream_errors={stream_errors}"
        )

    mark_info = dereference(catalog.get("/MarkInfo", {})) or {}
    has_structure_tree = bool(catalog.get("/StructTreeRoot"))
    marked = bool(mark_info.get("/Marked"))
    tagged = has_structure_tree and marked
    if not tagged:
        limitations.append(
            "PDF is untagged: no active structure tree with /MarkInfo /Marked true. "
            f"All {len(fonts)} discovered fonts have ToUnicode and all {actual_pages} pages "
            "remain text-extractable through both pypdf and pdfplumber; the semantic HTML "
            "reader remains the primary structured accessibility surface."
        )

    log_scan = build_binding["log_scan"]
    if log_scan["overfull_hits"]:
        unique_overfull = sorted(set(str(hit["text"]) for hit in log_scan["overfull_hits"]))
        warnings.append(
            f"all six bound build logs record overfull boxes: {unique_overfull}"
        )
    if log_scan["underfull_hits"]:
        warnings.append(
            f"bound build logs record {len(log_scan['underfull_hits'])} underfull-box warnings"
        )

    named_destinations = reader.named_destinations
    named_destination_names = list(named_destinations.keys())
    duplicate_named_destinations = len(named_destination_names) != len(set(named_destination_names))
    if duplicate_named_destinations:
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
        "workflow": "o011-through-unit06-pdf-structural-qa-v1",
        "verdict": verdict,
        "passed": passed,
        "execution_binding": {
            "project_root": ".",
            "script": {"path": relative(script_path), **bytes_sha(script_path)},
            "pdf": {"path": PDF_REL, "expected_bytes": EXPECTED_PDF_BYTES, "expected_sha256": EXPECTED_PDF_SHA256},
            "output": OUTPUT_REL,
        },
        "build_binding": build_binding,
        "source_and_math_qa_binding": source_and_math_qa_binding,
        "prefix_integrity": prefix_integrity,
        "pdf": {
            "path": PDF_REL,
            **pdf_identity,
            "pages": actual_pages,
            "media_box_points": media_sizes[0] if media_sizes else None,
            "crop_box_points": crop_sizes[0] if crop_sizes else None,
            "all_media_boxes_a4": bool(media_sizes) and all(size == EXPECTED_A4_POINTS for size in media_sizes),
            "all_crop_boxes_a4": bool(crop_sizes) and all(size == EXPECTED_A4_POINTS for size in crop_sizes),
            "all_rotations_zero": not any(rotations),
            "page_labels": page_labels,
            "page_labels_match": page_labels == EXPECTED_PAGE_LABELS,
            "catalog_language": catalog_language,
            "encrypted": reader.is_encrypted,
            "metadata": metadata,
            "metadata_mismatches": metadata_mismatches,
            "volatile_metadata_keys": volatile_metadata,
            "trailer_id_present": trailer_id_present,
            "tagged": tagged,
            "has_structure_tree": has_structure_tree,
            "mark_info_marked": marked,
        },
        "layout": {
            "expected_wrapper_margin_mm": EXPECTED_MARGIN_MM,
            "expected_wrapper_margin_points": round(EXPECTED_MARGIN_POINTS, 6),
            "expected_right_anchor_points": round(EXPECTED_A4_POINTS[0] - EXPECTED_MARGIN_POINTS, 6),
            "hash_bound_geometry_declaration_present": geometry_present,
            "content_pages_checked": content_page_numbers,
            "left_anchor_pages": left_anchor_pages,
            "minimum_required_left_anchor_pages": required_left_anchors,
            "right_anchor_pages": right_anchor_pages,
            "minimum_required_right_anchor_pages": required_right_anchors,
            "centered_wrapper_passed": centered_wrapper_passed,
            "page_body_extents": page_layout,
            "nominal_margin_overruns": nominal_margin_overruns,
            "outside_media_box": outside_media_box,
        },
        "accessibility": {
            "pypdf_version": pypdf.__version__,
            "pdfplumber_version": pdfplumber.__version__,
            "pypdf_pages_with_extractable_text": actual_pages - len(pypdf_empty),
            "pypdf_empty_text_pages": pypdf_empty,
            "pypdf_page_text_characters": [len(text) for text in pypdf_text],
            "pdfplumber_pages_with_extractable_text": len(plumber_text) - len(plumber_empty),
            "pdfplumber_empty_text_pages": plumber_empty,
            "pdfplumber_page_text_characters": [len(text) for text in plumber_text],
            "unique_fonts": len(fonts),
            "fonts_with_tounicode": sum(1 for value in fonts.values() if value["to_unicode"]),
            "fonts_without_tounicode": fonts_without_tounicode,
            "fonts_not_embedded": fonts_not_embedded,
            "fonts": fonts,
        },
        "content_closure": {
            "missing_required_text": missing_required,
            "unit6_part_physical_pages": unit6_part_pages,
            "worksheet_physical_pages_checked": [94, 95, 96, 97, 98, 99],
            "exercise_heading_counts": dict(sorted(exercise_counts.items(), key=lambda item: int(item[0]))),
            "expected_exercise_heading_counts": dict(sorted(EXPECTED_EXERCISES.items(), key=lambda item: int(item[0]))),
            "solution_heading_counts": dict(sorted(solution_counts.items(), key=lambda item: int(item[0]))),
            "expected_solution_heading_counts": dict(sorted(EXPECTED_SOLUTIONS.items(), key=lambda item: int(item[0]))),
            "missing_graded_markers": missing_graded,
            "correction_disclosures": correction_presence,
            "missing_correction_disclosures": missing_corrections,
            "model_provenance": {"exact_text": EXPECTED_MODEL_PROVENANCE, "occurrences": model_count},
            "unit6_media_text_presence": media_text_presence,
            "missing_unit6_media_text": missing_media_text,
        },
        "punctuation_regression": {
            "source_punctuation_only_logical_lines": source_and_math_qa_binding[
                "lecture_source"
            ]["punctuation_only_logical_lines"],
            "pypdf_punctuation_only_line_candidates": pypdf_punctuation_only,
            "pdfplumber_punctuation_only_line_candidates": pdfplumber_punctuation_only,
            "pdfplumber_layout_punctuation_only_line_candidates": pdfplumber_layout_punctuation_only,
            "visually_isolated_punctuation_glyphs": visual_punctuation_orphans,
            "sentence_punctuation_concatenations": sentence_punctuation_concatenations,
            "neighbor_radius_points": PUNCTUATION_NEIGHBOR_RADIUS_POINTS,
            "concatenation_gap_points": CONCATENATION_GAP_POINTS,
            "passed": not visual_punctuation_orphans
            and not sentence_punctuation_concatenations
            and not source_and_math_qa_binding["lecture_source"][
                "punctuation_only_logical_lines"
            ],
        },
        "bookmarks": {
            "count": len(bookmarks),
            "records": bookmarks,
            "errors": bookmark_errors,
            "unresolved": unresolved_bookmarks,
            "out_of_range": out_of_range_bookmarks,
            "missing_required": missing_bookmarks,
            "named_destination_count": len(named_destination_names),
            "duplicate_named_destinations": duplicate_named_destinations,
        },
        "links_and_active_content": {
            "external_uri_count": sum(uris.values()),
            "external_uri_counts": dict(sorted(uris.items())),
            "unit6_media_source_uri_count": source_uri_count,
            "unit6_media_license_uri_count": license_uri_count,
            "internal_link_count": internal_links,
            "annotation_subtype_counts": dict(sorted(subtypes.items())),
            "unsafe_actions": unsafe_actions,
            "unsafe_annotation_subtypes": unsafe_subtypes,
            "attachment_markers": attachment_markers,
            "javascript_name_tree": has_javascript,
            "embedded_files_name_tree": has_embedded_files,
            "acroform_or_fields": has_acroform,
            "catalog_associated_files": has_associated_files,
            "collection": has_collection,
            "unsafe_active_content_present": unsafe_active_content_present,
        },
        "privacy_and_residue": {
            "extracted_text_hits": extracted_hits,
            "metadata_hits": metadata_hits,
            "raw_or_decompressed_object_hits": raw_hits,
            "decoded_stream_count": stream_count,
            "decoded_stream_bytes_scanned": decoded_bytes,
            "stream_scan_errors": stream_errors,
        },
        "warnings": warnings,
        "limitations": limitations,
        "blockers": blockers,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
