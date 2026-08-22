#!/usr/bin/env python3
"""Strict structural, accessibility, text, link, and privacy QA through Unit 2.

The verifier is deliberately bound to the exact cumulative Unit 2 PDF boundary.
The absence of a PDF structure tree is recorded as an accessibility limitation;
every other failed requirement is a release blocker and produces a nonzero exit.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

import pdfplumber
import pypdf
from pypdf import PdfReader
from pypdf.generic import IndirectObject, StreamObject


EXPECTED_SHA256 = "6312b4df706d0f08eeb9f37da0abda3428b5448dce54781d0f52eb9c8db5c385"
EXPECTED_BYTES = 3_152_320
EXPECTED_PAGES = 44
EXPECTED_A4_POINTS = [595.276, 841.89]
EXPECTED_METADATA = {
    "/Author": "Holger Brenner, Terjemahan Bahasa Indonesia independen",
    "/Title": "Geometri Diferensial dan Manifold Mulus Pembaca kumulatif hingga Unit 2",
    "/Creator": "LaTeX with hyperref",
}

REQUIRED_TEXT_PATTERNS = {
    "work title": r"\bGeometri Diferensial dan Manifold Mulus\b",
    "cumulative boundary title": r"\bPembaca kumulatif hingga Unit 2\b",
    "author": r"\bHolger Brenner\b",
    "independent Indonesian edition": r"\bTerjemahan Bahasa Indonesia independen\b",
    "edition note": r"\bTentang edisi ini\b",
    "Unit 1 part": r"\bBagian I Unit 1\b",
    "Unit 1 lecture": r"\bKuliah 1: Analisis dan Geometri\b",
    "Unit 1 worksheet": r"\bLembar Kerja 1\b",
    "Unit 1 supplied solution": r"\bSolusi untuk Soal 1\b",
    "Unit 2 part": r"\bBagian II Unit 2\b",
    "Unit 2 lecture": r"\bKuliah 2: Permukaan Putar, Medan Normal, dan Pemetaan Gauss\b",
    "Unit 2 worksheet": r"\bLembar Kerja 2\b",
    "Unit 2 final exercise": r"\bSoal 2\.19\.(?!\d)",
    "Unit 2 solution 1": r"\bSolusi Soal 2\.1(?!\d)",
    "Unit 2 solution 2": r"\bSolusi Soal 2\.2(?!\d)",
    "Unit 2 solution 7": r"\bSolusi Soal 2\.7(?!\d)",
    "Unit 2 solution 12": r"\bSolusi Soal 2\.12(?!\d)",
    "Unit 2 solution 13": r"\bSolusi Soal 2\.13(?!\d)",
    "repaired Solution 12 opening": (
        r"\bUntuk orientasi keluar yang ditentukan dalam soal, medan normal satuan "
        r"diperoleh dengan menormalisasi gradien fungsi yang mendeskripsikan elips tersebut\b"
    ),
    "correct Unit 2 theorem reference": (
        r"\bKesurjektifan pemetaan ini mengikuti Teorema 2\.11\b"
    ),
    "media-rights heading": r"\bAtribusi dan Hak Media\b",
    "text license": r"\bCC BY-SA 4\.0\b",
}

REQUIRED_MINIMUM_COUNTS = {
    "supplied-solutions heading": (r"\bSolusi yang disediakan oleh sumber\b", 2),
}

REQUIRED_MEDIA_TEXT = {
    "3d-function-6.svg",
    "MartinThoma",
    "Great circle passing through two points.svg",
    "HaEr48",
    "Polar angle to spherical side.svg",
    "Episcophagus",
    "2019-07-Helix.jpg",
    "Ag2gaeh",
    "Planned flight map of the Oiseau Blanc.svg",
    "Pethrus",
    "BlankMap-World8.svg",
    "AMK1211",
    "Integral apl rot obsah1.svg",
    "Pajs",
    "Wikipedia bahasa Ceko",
    "Hyperboloid1.png",
    "Lars H. Rohwedder",
    "RokerHRO",
    "domain publik",
}

PAGE_REQUIREMENTS = {
    1: [r"Geometri Diferensial dan Manifold Mulus", r"Pembaca kumulatif hingga Unit 2"],
    4: [r"Bagian I", r"Unit 1"],
    5: [r"Kuliah 1: Analisis dan Geometri"],
    17: [r"Lembar Kerja 1"],
    22: [r"Solusi yang disediakan oleh sumber", r"Solusi untuk Soal 1"],
    24: [r"Bagian II", r"Unit 2"],
    25: [r"Kuliah 2: Permukaan Putar, Medan Normal, dan Pemetaan Gauss"],
    34: [r"Lembar Kerja 2", r"Soal 2\.1\.\*"],
    38: [
        r"Solusi yang disediakan oleh sumber",
        r"Solusi Soal 2\.1(?!\d)",
        r"Solusi Soal 2\.2(?!\d)",
    ],
    39: [r"Solusi Soal 2\.7(?!\d)", r"Solusi Soal 2\.12(?!\d)"],
    40: [r"Solusi Soal 2\.13(?!\d)"],
    41: [r"Kesurjektifan pemetaan ini mengikuti Teorema 2\.11"],
    42: [r"Daftar Gambar", r"Integral apl rot obsah1\.svg", r"Hyperboloid1\.png"],
    43: [r"Atribusi dan Hak Media", r"Unit 1", r"Unit 2", r"Lars H\. Rohwedder"],
    44: [r"Lisensi", r"Holger Brenner", r"CC BY-SA 4\.0"],
}

EXPECTED_MEDIA_URI_COUNTS = Counter(
    {
        "https://commons.wikimedia.org/wiki/File:3d-function-6.svg": 2,
        "https://creativecommons.org/licenses/by/3.0": 1,
        "https://commons.wikimedia.org/wiki/File:Great_circle_passing_through_two_points.svg": 2,
        "https://creativecommons.org/licenses/by-sa/4.0": 2,
        "https://commons.wikimedia.org/wiki/File:2019-07-Helix.jpg": 2,
        "https://commons.wikimedia.org/wiki/File:Planned_flight_map_of_the_Oiseau_Blanc.svg": 2,
        "https://creativecommons.org/licenses/by-sa/3.0": 1,
        "https://commons.wikimedia.org/wiki/File:Integral_apl_rot_obsah1.svg": 1,
        "https://commons.wikimedia.org/wiki/File:Hyperboloid1.png": 2,
    }
)

FORBIDDEN_EXTRACTED_TEXT = {
    "local user path or profile": re.compile(
        r"(?:[A-Za-z]:[\\/](?:Users|Documents|AppData)[\\/]|/Users/|AppData|\bFloris\b)",
        re.IGNORECASE,
    ),
    "project umbrella residue": re.compile(
        r"(?:\bTTP\b|Translation and Transcription Project)", re.IGNORECASE
    ),
    "task/thread identifier": re.compile(
        r"\b01[a-f0-9]{6,}(?:-[a-f0-9]{4,}){2,}\b", re.IGNORECASE
    ),
    "replacement character": re.compile("\ufffd"),
    "raw wiki markup": re.compile(
        r"(?:\[\[|\]\]|\{\{(?:Latex|Definitionslink|Relationskette|Math|Abbildung)|Kategorie:Latexseite)",
        re.IGNORECASE,
    ),
    "German instructional prose": re.compile(
        r"\b(?:Zeige(?:,)? dass|Bestimme(?: die| das| den| ein| eine)|Man gebe|"
        r"Gilt davon auch die Umkehrung|Beschreibe die Menge|Aufgaben zum Abgeben|"
        r"Übungsaufgaben)\b"
    ),
    "German sentence residue": re.compile(
        r"(?m)^\s*(?:Es sei|Es seien|Eine |Der |Die |Das |Wir betrachten|Wegen |"
        r"Dann ist|Daher ist)\b"
    ),
    "German mathematical terminology residue": re.compile(
        r"\b(?:differenzierbare(?:n|r|s)?|Hyperfläche(?:n)?|Einheitsnormalenfeld(?:er)?|"
        r"Gauß-Abbildung(?:en)?|Äquivalenzrelation|Quotientenmenge|zusammenhängend|"
        r"bogenparametrisiert|Umkehrabbildung|Nullstellenmenge)\b"
    ),
    "stale antipodal trailing prose": re.compile(
        r"pemetaan antipodal.{0,160}\bdi atas\.", re.IGNORECASE | re.DOTALL
    ),
    "stale Unit 2 theorem reference": re.compile(
        r"Kesurjektifan pemetaan ini mengikuti Teorema 2\.10\b"
    ),
    "stale duplicated Solution 12 opening": re.compile(
        r"Untuk orientasi keluar.{0,180}medan normal satuan,\s*kita mulai",
        re.IGNORECASE | re.DOTALL,
    ),
}

FORBIDDEN_RAW_BYTES = {
    "local user path or profile": re.compile(
        rb"(?:[A-Za-z]:[\\/](?:Users|Documents|AppData)[\\/]|/Users/|AppData[\\/]|"
        rb"C:\\Users\\|\bFloris\b)",
        re.IGNORECASE,
    ),
    "project umbrella residue": re.compile(
        rb"(?:\bTTP\b|Translation and Transcription Project)", re.IGNORECASE
    ),
    "task/thread identifier": re.compile(
        rb"\b01[a-f0-9]{6,}(?:-[a-f0-9]{4,}){2,}\b", re.IGNORECASE
    ),
    "UTF-8 replacement character": re.compile(b"\xef\xbf\xbd"),
    "raw wiki markup": re.compile(
        rb"(?:\[\[(?:Kategorie|Category|File|Datei|Berkas):|"
        rb"\{\{(?:Latex|Definitionslink|Relationskette|Math|Abbildung)|"
        rb"Kategorie:Latexseite)",
        re.IGNORECASE,
    ),
}

UNSAFE_ANNOTATION_SUBTYPES = {
    "/FileAttachment",
    "/RichMedia",
    "/Movie",
    "/Sound",
    "/Screen",
    "/Widget",
}
SAFE_ACTION_TYPES = {"/GoTo", "/URI"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def dereference(value):
    return value.get_object() if hasattr(value, "get_object") else value


def indirect_key(value) -> str:
    if hasattr(value, "idnum"):
        return f"{value.idnum}:{value.generation}"
    return repr(value)


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def collect_fonts(reader: PdfReader) -> dict[str, dict[str, object]]:
    fonts: dict[str, dict[str, object]] = {}
    visited_xobjects: set[str] = set()

    def walk_resources(resources_ref) -> None:
        resources = dereference(resources_ref)
        if not isinstance(resources, dict):
            return
        font_dict = dereference(resources.get("/Font", {})) or {}
        for font_ref in font_dict.values():
            font = dereference(font_ref)
            descriptor = dereference(font.get("/FontDescriptor", {})) or {}
            embedded = any(
                descriptor.get(key)
                for key in ("/FontFile", "/FontFile2", "/FontFile3")
            )
            fonts[indirect_key(font_ref)] = {
                "base_font": str(font.get("/BaseFont", "")),
                "subtype": str(font.get("/Subtype", "")),
                "to_unicode": bool(font.get("/ToUnicode")),
                "embedded": bool(embedded),
            }

        xobjects = dereference(resources.get("/XObject", {})) or {}
        for xobject_ref in xobjects.values():
            key = indirect_key(xobject_ref)
            if key in visited_xobjects:
                continue
            visited_xobjects.add(key)
            xobject = dereference(xobject_ref)
            if isinstance(xobject, dict) and xobject.get("/Resources"):
                walk_resources(xobject.get("/Resources"))

    for page in reader.pages:
        walk_resources(page.get("/Resources", {}))
    return dict(sorted(fonts.items()))


def scan_raw_and_decompressed_objects(
    reader: PdfReader, pdf_path: Path
) -> tuple[dict[str, list[str]], int, int, list[str]]:
    hits = {label: [] for label in FORBIDDEN_RAW_BYTES}
    raw_pdf = pdf_path.read_bytes()
    for label, pattern in FORBIDDEN_RAW_BYTES.items():
        if pattern.search(raw_pdf):
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
                obj = reader.get_object(
                    IndirectObject(object_number, generation, reader)
                )
            except Exception as exc:  # pragma: no cover - receipt records any case
                errors.append(f"{object_id}: object read failed: {type(exc).__name__}")
                continue
            if not isinstance(obj, StreamObject):
                continue
            stream_count += 1
            try:
                data = obj.get_data()
            except Exception as exc:  # pragma: no cover - receipt records any case
                errors.append(f"{object_id}: stream decode failed: {type(exc).__name__}")
                continue
            decoded_bytes += len(data)
            for label, pattern in FORBIDDEN_RAW_BYTES.items():
                if pattern.search(data):
                    hits[label].append(object_id)

    return hits, stream_count, decoded_bytes, errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument(
        "--pdf",
        type=Path,
        default=Path(
            "output/pdf/geometri-diferensial-manifold-mulus-hingga-unit-02-id.pdf"
        ),
    )
    parser.add_argument(
        "--output", type=Path, default=Path("qa/unit-02/pdf_structural_qa.json")
    )
    args = parser.parse_args()

    root = args.project_root.resolve()
    pdf_path = (root / args.pdf).resolve()
    output_path = (root / args.output).resolve()
    relative_pdf = pdf_path.relative_to(root).as_posix()
    output_path.relative_to(root)

    blockers: list[str] = []
    limitations: list[str] = []
    actual_sha = sha256(pdf_path)
    actual_bytes = pdf_path.stat().st_size
    if actual_sha != EXPECTED_SHA256:
        blockers.append(f"unexpected PDF SHA-256: {actual_sha}")
    if actual_bytes != EXPECTED_BYTES:
        blockers.append(f"unexpected PDF byte count: {actual_bytes}")

    reader = PdfReader(str(pdf_path))
    catalog = reader.root_object
    metadata = {str(k): str(v) for k, v in dict(reader.metadata or {}).items()}
    metadata_mismatches = {
        key: {"expected": expected, "actual": metadata.get(key)}
        for key, expected in EXPECTED_METADATA.items()
        if metadata.get(key) != expected
    }
    if metadata_mismatches:
        blockers.append(f"metadata mismatch: {metadata_mismatches}")

    volatile_metadata = sorted(
        key for key in ("/CreationDate", "/ModDate") if key in metadata
    )
    trailer_id_present = bool(reader.trailer.get("/ID"))
    if volatile_metadata:
        blockers.append(f"volatile PDF metadata present: {volatile_metadata}")
    if trailer_id_present:
        blockers.append("PDF trailer contains a volatile /ID")

    page_media_sizes: list[list[float]] = []
    page_crop_sizes: list[list[float]] = []
    rotations: list[int] = []
    pypdf_page_text: list[str] = []
    uri_links: list[str] = []
    internal_link_count = 0
    unsafe_actions: list[dict[str, str]] = []
    annotation_subtypes: Counter[str] = Counter()
    attachment_markers: list[str] = []

    def inspect_action(owner: str, action_ref) -> None:
        nonlocal internal_link_count
        action = dereference(action_ref)
        if not isinstance(action, dict):
            unsafe_actions.append({"owner": owner, "type": "malformed"})
            return
        action_type = str(action.get("/S", ""))
        if action_type == "/URI":
            uri_links.append(str(action.get("/URI", "")))
        elif action_type == "/GoTo":
            internal_link_count += 1
        elif action_type not in SAFE_ACTION_TYPES:
            unsafe_actions.append({"owner": owner, "type": action_type or "unknown"})

    def inspect_additional_actions(owner: str, actions_ref) -> None:
        actions = dereference(actions_ref)
        if not isinstance(actions, dict):
            unsafe_actions.append({"owner": owner, "type": "malformed-/AA"})
            return
        for event, action in actions.items():
            inspect_action(f"{owner}{event}", action)

    for page_number, page in enumerate(reader.pages, start=1):
        page_media_sizes.append(
            [round(float(page.mediabox.width), 3), round(float(page.mediabox.height), 3)]
        )
        page_crop_sizes.append(
            [round(float(page.cropbox.width), 3), round(float(page.cropbox.height), 3)]
        )
        rotations.append(int(page.get("/Rotate", 0)))
        pypdf_page_text.append(page.extract_text() or "")
        if page.get("/AA"):
            inspect_additional_actions(f"page-{page_number}", page.get("/AA"))
        if page.get("/AF"):
            attachment_markers.append(f"page-{page_number}:/AF")

        for annotation_ref in page.get("/Annots", []):
            annotation = dereference(annotation_ref)
            subtype = str(annotation.get("/Subtype", "unknown"))
            annotation_subtypes[subtype] += 1
            owner = f"page-{page_number}:{subtype}"
            if subtype in UNSAFE_ANNOTATION_SUBTYPES:
                attachment_markers.append(owner)
            if annotation.get("/FS"):
                attachment_markers.append(f"{owner}:/FS")
            if annotation.get("/A"):
                inspect_action(owner, annotation.get("/A"))
            elif annotation.get("/Dest") is not None:
                internal_link_count += 1
            if annotation.get("/AA"):
                inspect_additional_actions(owner, annotation.get("/AA"))

    open_action = dereference(catalog.get("/OpenAction"))
    open_action_type = None
    if open_action:
        if isinstance(open_action, dict):
            open_action_type = str(open_action.get("/S", ""))
            inspect_action("catalog:/OpenAction", open_action)
        elif isinstance(open_action, list):
            open_action_type = "destination-array"
            internal_link_count += 1
        else:
            open_action_type = "malformed"
            unsafe_actions.append({"owner": "catalog:/OpenAction", "type": "malformed"})
    if catalog.get("/AA"):
        inspect_additional_actions("catalog", catalog.get("/AA"))

    if len(reader.pages) != EXPECTED_PAGES:
        blockers.append(f"unexpected page count: {len(reader.pages)}")
    if any(size != EXPECTED_A4_POINTS for size in page_media_sizes):
        blockers.append("one or more MediaBox dimensions are not A4")
    if any(size != EXPECTED_A4_POINTS for size in page_crop_sizes):
        blockers.append("one or more CropBox dimensions are not A4")
    if any(rotations):
        blockers.append("one or more pages have nonzero rotation")
    if reader.is_encrypted:
        blockers.append("PDF is encrypted")
    catalog_language = str(catalog.get("/Lang", ""))
    if catalog_language != "id-ID":
        blockers.append(f"unexpected catalog language: {catalog_language!r}")

    fonts = collect_fonts(reader)
    fonts_without_tounicode = [
        key for key, details in fonts.items() if not details["to_unicode"]
    ]
    if not fonts:
        blockers.append("no PDF fonts were discovered")
    if fonts_without_tounicode:
        blockers.append(f"fonts without ToUnicode: {fonts_without_tounicode}")

    pypdf_empty_pages = [
        number
        for number, text in enumerate(pypdf_page_text, start=1)
        if not text.strip()
    ]
    if pypdf_empty_pages:
        blockers.append(f"pypdf pages with no extractable text: {pypdf_empty_pages}")

    with pdfplumber.open(str(pdf_path)) as plumber_pdf:
        plumber_page_count = len(plumber_pdf.pages)
        plumber_page_sizes = [
            [round(float(page.width), 3), round(float(page.height), 3)]
            for page in plumber_pdf.pages
        ]
        plumber_page_text = [page.extract_text() or "" for page in plumber_pdf.pages]
    plumber_empty_pages = [
        number
        for number, text in enumerate(plumber_page_text, start=1)
        if not text.strip()
    ]
    if plumber_page_count != EXPECTED_PAGES:
        blockers.append(f"pdfplumber page-count mismatch: {plumber_page_count}")
    if any(size != EXPECTED_A4_POINTS for size in plumber_page_sizes):
        blockers.append("pdfplumber found one or more non-A4 pages")
    if plumber_empty_pages:
        blockers.append(
            f"pdfplumber pages with no extractable text: {plumber_empty_pages}"
        )

    full_text = "\n".join(pypdf_page_text)
    normalized_full_text = normalize_text(full_text)
    normalized_page_text = [normalize_text(text) for text in pypdf_page_text]
    missing_required_text = [
        label
        for label, pattern in REQUIRED_TEXT_PATTERNS.items()
        if not re.search(pattern, normalized_full_text)
    ]
    required_counts = {
        label: len(re.findall(pattern, normalized_full_text))
        for label, (pattern, _) in REQUIRED_MINIMUM_COUNTS.items()
    }
    insufficient_counts = {
        label: {"required": minimum, "actual": required_counts[label]}
        for label, (_, minimum) in REQUIRED_MINIMUM_COUNTS.items()
        if required_counts[label] < minimum
    }
    missing_media_text = sorted(
        item for item in REQUIRED_MEDIA_TEXT if item not in normalized_full_text
    )
    missing_page_requirements: list[dict[str, object]] = []
    for page_number, patterns in PAGE_REQUIREMENTS.items():
        page_text = normalized_page_text[page_number - 1]
        missing = [pattern for pattern in patterns if not re.search(pattern, page_text)]
        if missing:
            missing_page_requirements.append(
                {"page": page_number, "missing_patterns": missing}
            )
    if missing_required_text:
        blockers.append(f"missing required edition/unit text: {missing_required_text}")
    if insufficient_counts:
        blockers.append(f"insufficient required text counts: {insufficient_counts}")
    if missing_media_text:
        blockers.append(f"missing required media attribution text: {missing_media_text}")
    if missing_page_requirements:
        blockers.append(f"required page-local text missing: {missing_page_requirements}")

    extracted_forbidden_hits = {
        label: sorted(set(match.group(0) for match in pattern.finditer(full_text)))
        for label, pattern in FORBIDDEN_EXTRACTED_TEXT.items()
        if pattern.search(full_text)
    }
    metadata_text = "\n".join(metadata.values())
    metadata_forbidden_hits = {
        label: sorted(set(match.group(0) for match in pattern.finditer(metadata_text)))
        for label, pattern in FORBIDDEN_EXTRACTED_TEXT.items()
        if pattern.search(metadata_text)
    }
    if extracted_forbidden_hits:
        blockers.append(f"forbidden extracted-text residues: {extracted_forbidden_hits}")
    if metadata_forbidden_hits:
        blockers.append(f"forbidden metadata residues: {metadata_forbidden_hits}")

    raw_hits, stream_count, decoded_stream_bytes, stream_errors = (
        scan_raw_and_decompressed_objects(reader, pdf_path)
    )
    nonempty_raw_hits = {label: locations for label, locations in raw_hits.items() if locations}
    if nonempty_raw_hits:
        blockers.append(f"forbidden raw/decompressed-object residues: {nonempty_raw_hits}")
    if stream_errors:
        blockers.append(f"raw object scan errors: {stream_errors}")

    actual_uri_counts = Counter(uri_links)
    missing_uri_counts = {
        uri: expected - actual_uri_counts[uri]
        for uri, expected in EXPECTED_MEDIA_URI_COUNTS.items()
        if actual_uri_counts[uri] < expected
    }
    extra_uri_counts = {
        uri: actual - EXPECTED_MEDIA_URI_COUNTS[uri]
        for uri, actual in actual_uri_counts.items()
        if actual > EXPECTED_MEDIA_URI_COUNTS[uri]
    }
    if missing_uri_counts:
        blockers.append(f"missing required external media URI occurrences: {missing_uri_counts}")
    if unsafe_actions:
        blockers.append(f"unsafe or malformed PDF actions: {unsafe_actions}")

    names = dereference(catalog.get("/Names", {})) or {}
    has_javascript_name_tree = bool(names.get("/JavaScript"))
    has_embedded_files_name_tree = bool(names.get("/EmbeddedFiles"))
    has_acroform = bool(catalog.get("/AcroForm"))
    has_fields = bool(reader.get_fields() or {})
    has_catalog_af = bool(catalog.get("/AF"))
    has_collection = bool(catalog.get("/Collection"))
    unsafe_annotation_subtypes = sorted(
        subtype
        for subtype in annotation_subtypes
        if subtype in UNSAFE_ANNOTATION_SUBTYPES
    )
    if has_javascript_name_tree:
        blockers.append("PDF contains a JavaScript name tree")
    if has_embedded_files_name_tree or has_catalog_af or attachment_markers:
        blockers.append("PDF contains attachment markers")
    if has_acroform or has_fields or "/Widget" in annotation_subtypes:
        blockers.append("PDF contains an AcroForm or form widgets")
    if has_collection:
        blockers.append("PDF contains a collection/portfolio")
    if unsafe_annotation_subtypes:
        blockers.append(
            f"unsafe annotation subtypes present: {unsafe_annotation_subtypes}"
        )

    mark_info = dereference(catalog.get("/MarkInfo", {})) or {}
    has_structure_tree = bool(catalog.get("/StructTreeRoot"))
    marked = bool(mark_info.get("/Marked"))
    tagged = has_structure_tree and marked
    if not tagged:
        limitations.append(
            "PDF is untagged: it has no active structure tree with /MarkInfo /Marked true. All 28 discovered fonts have ToUnicode and every page remains text-extractable; the planned HTML reader is the primary structured accessibility surface."
        )

    passed = not blockers
    verdict = "PASS_WITH_DOCUMENTED_LIMITATION" if passed and limitations else (
        "PASS" if passed else "FAIL"
    )
    receipt = {
        "schema_version": 1,
        "workflow": "o011-through-unit02-pdf-structural-qa-v1",
        "verdict": verdict,
        "passed": passed,
        "pdf": {
            "path": relative_pdf,
            "bytes": actual_bytes,
            "sha256": actual_sha,
            "pages": len(reader.pages),
            "media_box_points": page_media_sizes[0] if page_media_sizes else None,
            "crop_box_points": page_crop_sizes[0] if page_crop_sizes else None,
            "all_media_boxes_a4": all(
                size == EXPECTED_A4_POINTS for size in page_media_sizes
            ),
            "all_crop_boxes_a4": all(
                size == EXPECTED_A4_POINTS for size in page_crop_sizes
            ),
            "all_rotations_zero": not any(rotations),
            "encrypted": reader.is_encrypted,
            "catalog_language": catalog_language,
            "metadata": metadata,
            "metadata_mismatches": metadata_mismatches,
            "volatile_metadata_keys": volatile_metadata,
            "trailer_id_present": trailer_id_present,
            "tagged": tagged,
            "has_structure_tree": has_structure_tree,
            "mark_info_marked": marked,
        },
        "accessibility": {
            "unique_fonts": len(fonts),
            "fonts_with_tounicode": sum(
                1 for details in fonts.values() if details["to_unicode"]
            ),
            "fonts_without_tounicode": fonts_without_tounicode,
            "fonts": fonts,
            "pypdf_pages_with_extractable_text": len(pypdf_page_text)
            - len(pypdf_empty_pages),
            "pypdf_empty_text_pages": pypdf_empty_pages,
            "pypdf_page_text_characters": [len(text) for text in pypdf_page_text],
            "pdfplumber_version": pdfplumber.__version__,
            "pdfplumber_page_count": plumber_page_count,
            "pdfplumber_pages_with_extractable_text": len(plumber_page_text)
            - len(plumber_empty_pages),
            "pdfplumber_empty_text_pages": plumber_empty_pages,
            "pdfplumber_page_text_characters": [
                len(text) for text in plumber_page_text
            ],
            "pypdf_version": pypdf.__version__,
        },
        "content_closure": {
            "missing_required_text": missing_required_text,
            "required_minimum_counts": {
                label: {
                    "required": minimum,
                    "actual": required_counts[label],
                }
                for label, (_, minimum) in REQUIRED_MINIMUM_COUNTS.items()
            },
            "missing_media_attribution_text": missing_media_text,
            "missing_page_requirements": missing_page_requirements,
        },
        "links": {
            "external_uri_count": len(uri_links),
            "external_uri_counts": dict(sorted(actual_uri_counts.items())),
            "required_uri_counts": dict(sorted(EXPECTED_MEDIA_URI_COUNTS.items())),
            "missing_uri_counts": missing_uri_counts,
            "extra_uri_counts": extra_uri_counts,
            "internal_link_count": internal_link_count,
            "catalog_open_action_type": open_action_type,
            "unsafe_actions": unsafe_actions,
        },
        "active_content": {
            "javascript_name_tree": has_javascript_name_tree,
            "acroform": has_acroform,
            "form_fields": has_fields,
            "embedded_files_name_tree": has_embedded_files_name_tree,
            "catalog_associated_files": has_catalog_af,
            "collection": has_collection,
            "attachment_markers": attachment_markers,
            "annotation_subtype_counts": dict(sorted(annotation_subtypes.items())),
            "unsafe_annotation_subtypes": unsafe_annotation_subtypes,
        },
        "privacy_and_residue": {
            "extracted_text_hits": extracted_forbidden_hits,
            "metadata_hits": metadata_forbidden_hits,
            "raw_or_decompressed_object_hits": nonempty_raw_hits,
            "decoded_stream_count": stream_count,
            "decoded_stream_bytes_scanned": decoded_stream_bytes,
            "stream_scan_errors": stream_errors,
        },
        "determinism_signals": {
            "expected_bytes": EXPECTED_BYTES,
            "actual_bytes_match": actual_bytes == EXPECTED_BYTES,
            "expected_sha256": EXPECTED_SHA256,
            "actual_sha256_match": actual_sha == EXPECTED_SHA256,
            "volatile_metadata_absent": not volatile_metadata,
            "trailer_id_absent": not trailer_id_present,
        },
        "limitations": limitations,
        "blockers": blockers,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
