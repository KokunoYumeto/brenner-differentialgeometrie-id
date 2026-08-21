#!/usr/bin/env python3
"""Deterministic structural QA for the published Unit 1 PDF.

The script deliberately treats the lack of a PDF structure tree as a recorded
accessibility limitation rather than hiding it. All other failed checks are
release blockers and produce a nonzero exit status.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from pypdf import PdfReader


EXPECTED_SHA256 = "eb7e78affacf8a559d0f52a1c44921633d2fa74a070faa64af58efc32d34a568"
EXPECTED_BYTES = 2_678_755
EXPECTED_PAGES = 25
EXPECTED_MEDIA_URIS = [
    "https://commons.wikimedia.org/wiki/File:3d-function-6.svg",
    "https://creativecommons.org/licenses/by/3.0",
    "https://commons.wikimedia.org/wiki/File:Great_circle_passing_through_two_points.svg",
    "https://creativecommons.org/licenses/by-sa/4.0",
    "https://commons.wikimedia.org/wiki/File:2019-07-Helix.jpg",
    "https://creativecommons.org/licenses/by-sa/4.0",
    "https://commons.wikimedia.org/wiki/File:Planned_flight_map_of_the_Oiseau_Blanc.svg",
    "https://creativecommons.org/licenses/by-sa/3.0",
]
REQUIRED_TEXT = [
    "MartinThoma",
    "HaEr48",
    "Episcophagus",
    "Polar angle to spherical side.svg",
    "Ag2gaeh",
    "Pethrus",
    "AMK1211",
    "BlankMap-World8.svg",
]
FORBIDDEN_TEXT = {
    "absolute Windows user path": re.compile(r"C:\\Users\\", re.IGNORECASE),
    "AppData path": re.compile(r"AppData", re.IGNORECASE),
    "project umbrella residue": re.compile(
        r"(?:\bTTP\b|Translation and Transcription Project)", re.IGNORECASE
    ),
    # Case-sensitive by design: pypdf may collapse "ke R^n" to "keRn",
    # which must not be mistaken for the lowercase German operator "kern".
    "German operators or internal lane jargon": re.compile(r"\b(?:bild|kern|lane)\b"),
    "stale cross-reference": re.compile(r"Catatan\s+1\.3\b"),
    "noncanonical license casing": re.compile(r"CC-by-sa", re.IGNORECASE),
    "replacement character": re.compile("\ufffd"),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def dereference(value):
    return value.get_object() if hasattr(value, "get_object") else value


def font_key(value) -> str:
    if hasattr(value, "idnum"):
        return f"{value.idnum}:{value.generation}"
    return repr(value)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument(
        "--pdf",
        type=Path,
        default=Path("output/pdf/geometri-diferensial-manifold-mulus-unit-01-id.pdf"),
    )
    parser.add_argument(
        "--output", type=Path, default=Path("qa/unit-01/pdf_structural_qa.json")
    )
    args = parser.parse_args()

    root = args.project_root.resolve()
    pdf_path = (root / args.pdf).resolve()
    output_path = (root / args.output).resolve()
    relative_pdf = pdf_path.relative_to(root).as_posix()

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
    page_sizes = []
    rotations = []
    page_text = []
    fonts: dict[str, bool] = {}
    uri_links: list[str] = []
    internal_links = 0
    unsafe_actions: list[str] = []

    for page in reader.pages:
        page_sizes.append(
            [round(float(page.mediabox.width), 3), round(float(page.mediabox.height), 3)]
        )
        rotations.append(int(page.get("/Rotate", 0)))
        page_text.append(page.extract_text() or "")

        resources = dereference(page.get("/Resources", {}))
        font_dict = dereference(resources.get("/Font", {})) if resources else {}
        for font_ref in font_dict.values():
            font = dereference(font_ref)
            fonts[font_key(font_ref)] = bool(font.get("/ToUnicode"))

        for annotation_ref in page.get("/Annots", []):
            annotation = dereference(annotation_ref)
            if annotation.get("/Subtype") != "/Link":
                continue
            action = dereference(annotation.get("/A", {}))
            if action:
                action_type = str(action.get("/S", ""))
                if action_type == "/URI":
                    uri_links.append(str(action.get("/URI", "")))
                elif action_type == "/GoTo":
                    internal_links += 1
                else:
                    unsafe_actions.append(action_type or "unknown")
            elif annotation.get("/Dest") is not None:
                internal_links += 1

    if len(reader.pages) != EXPECTED_PAGES:
        blockers.append(f"unexpected page count: {len(reader.pages)}")
    if any(size != [595.276, 841.89] for size in page_sizes):
        blockers.append("one or more pages are not A4 at the expected dimensions")
    if any(rotations):
        blockers.append("one or more pages have nonzero rotation")
    if reader.is_encrypted:
        blockers.append("PDF is encrypted")
    if str(catalog.get("/Lang", "")) != "id-ID":
        blockers.append(f"unexpected catalog language: {catalog.get('/Lang')!r}")

    tagged = bool(catalog.get("/StructTreeRoot")) and bool(catalog.get("/MarkInfo"))
    if not tagged:
        limitations.append(
            "PDF has no structure tree/tagging; all fonts retain ToUnicode and the planned HTML reader is the primary structured accessibility surface."
        )
    if not fonts or not all(fonts.values()):
        blockers.append("one or more embedded fonts lack a ToUnicode map")
    empty_text_pages = [index + 1 for index, text in enumerate(page_text) if not text.strip()]
    if empty_text_pages:
        blockers.append(f"pages with no extractable text: {empty_text_pages}")

    text = "\n".join(page_text)
    missing_text = [item for item in REQUIRED_TEXT if item not in text]
    if missing_text:
        blockers.append(f"missing required attribution text: {missing_text}")
    forbidden_hits = [label for label, pattern in FORBIDDEN_TEXT.items() if pattern.search(text)]
    if forbidden_hits:
        blockers.append(f"forbidden PDF-text residues: {forbidden_hits}")

    missing_uris = []
    remaining_uris = list(uri_links)
    for expected in EXPECTED_MEDIA_URIS:
        if expected in remaining_uris:
            remaining_uris.remove(expected)
        else:
            missing_uris.append(expected)
    if missing_uris:
        blockers.append(f"missing required external media links: {missing_uris}")
    if unsafe_actions:
        blockers.append(f"unexpected PDF action types: {unsafe_actions}")

    names = dereference(catalog.get("/Names", {}))
    has_embedded_files = bool(names and names.get("/EmbeddedFiles"))
    has_javascript = bool(names and names.get("/JavaScript"))
    has_form = bool(catalog.get("/AcroForm"))
    if has_embedded_files:
        blockers.append("PDF contains embedded files")
    if has_javascript:
        blockers.append("PDF contains JavaScript")
    if has_form:
        blockers.append("PDF contains an AcroForm")

    receipt = {
        "schema_version": 1,
        "workflow": "o011-unit01-pdf-structural-qa-v1",
        "pdf": {
            "path": relative_pdf,
            "bytes": actual_bytes,
            "sha256": actual_sha,
            "pages": len(reader.pages),
            "page_size_points": page_sizes[0] if page_sizes else None,
            "all_pages_same_size": len(set(map(tuple, page_sizes))) <= 1,
            "all_rotations_zero": not any(rotations),
            "encrypted": reader.is_encrypted,
            "catalog_language": str(catalog.get("/Lang", "")),
            "tagged": tagged,
        },
        "accessibility": {
            "unique_fonts": len(fonts),
            "fonts_with_tounicode": sum(fonts.values()),
            "pages_with_extractable_text": len(page_text) - len(empty_text_pages),
            "empty_text_pages": empty_text_pages,
        },
        "links": {
            "external_uri_count": len(uri_links),
            "external_uris": uri_links,
            "internal_link_count": internal_links,
            "unsafe_actions": unsafe_actions,
        },
        "active_content": {
            "javascript": has_javascript,
            "acroform": has_form,
            "embedded_files": has_embedded_files,
        },
        "required_attribution_text_present": not missing_text,
        "forbidden_text_residues": forbidden_hits,
        "limitations": limitations,
        "blockers": blockers,
        "passed": not blockers,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0 if not blockers else 1


if __name__ == "__main__":
    raise SystemExit(main())
