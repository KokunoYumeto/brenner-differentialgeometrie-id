#!/usr/bin/env python3
"""Bounded structural/layout QA for the cumulative Indonesian reader through Unit 7.

This verifier is intentionally independent of the build script.  It binds the
settled PDF bytes, checks every page's A4 geometry and extractability, audits
embedded font maps and active links, and verifies the Unit 7 exercise/solution
and interactive-media closure.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from collections import Counter

import pdfplumber
from pypdf import PdfReader


EXPECTED_BYTES = 4_950_232
EXPECTED_SHA256 = "8c2cf76230b45d66a8236c0cd92a048809ff5ec0cce343132dd902684cb05ec6"
EXPECTED_PAGES = 117
EXPECTED_A4 = (595.276, 841.89)
MODEL = "OpenAI Codex gpt-5.6-sol, Ultra"


def digest(path: Path) -> tuple[int, str]:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return path.stat().st_size, h.hexdigest()


def close(a: float, b: float, tol: float = 0.01) -> bool:
    return abs(a - b) <= tol


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--pdf", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    pdf_path = (root / args.pdf).resolve()
    output_path = (root / args.output).resolve()
    size, sha = digest(pdf_path)
    reader = PdfReader(str(pdf_path))
    pages = len(reader.pages)
    boxes = [(round(float(p.mediabox.width), 3), round(float(p.mediabox.height), 3)) for p in reader.pages]
    rotations = [int(p.get("/Rotate", 0) or 0) for p in reader.pages]
    texts = [p.extract_text() or "" for p in reader.pages]
    empty_pages = [i + 1 for i, text in enumerate(texts) if not text.strip()]
    metadata = {str(k): str(v) for k, v in (reader.metadata or {}).items() if v is not None}
    fonts: dict[str, dict[str, bool]] = {}
    uri_links: list[str] = []
    subtype_counts: Counter[str] = Counter()
    unsafe_actions: list[str] = []
    for page in reader.pages:
        for annotation in page.get("/Annots", []) or []:
            obj = annotation.get_object()
            subtype = str(obj.get("/Subtype"))
            subtype_counts[subtype] += 1
            action = obj.get("/A")
            if action:
                action_type = str(action.get("/S"))
                if action_type in {"/JavaScript", "/Launch", "/SubmitForm", "/GoToR"}:
                    unsafe_actions.append(action_type)
                if action_type == "/URI":
                    uri_links.append(str(action.get("/URI")))
        resources = page.get("/Resources")
        if resources and "/Font" in resources:
            for _, font_ref in resources["/Font"].items():
                font = font_ref.get_object()
                name = str(font.get("/BaseFont", "unknown"))
                entry = fonts.setdefault(name, {"to_unicode": False, "embedded": False})
                entry["to_unicode"] |= "/ToUnicode" in font
                descriptor = font.get("/FontDescriptor")
                if descriptor:
                    desc = descriptor.get_object()
                    entry["embedded"] |= any(key in desc for key in ("/FontFile", "/FontFile2", "/FontFile3"))
                descendants = font.get("/DescendantFonts")
                if descendants:
                    descendant = descendants[0].get_object()
                    entry["to_unicode"] |= "/ToUnicode" in descendant
                    descriptor = descendant.get("/FontDescriptor")
                    if descriptor:
                        desc = descriptor.get_object()
                        entry["embedded"] |= any(key in desc for key in ("/FontFile", "/FontFile2", "/FontFile3"))

    required_text = {
        "title": r"Geometri Diferensial dan Manifold Mulus",
        "boundary": r"Pembaca kumulatif hingga Unit 7",
        "unit_7": r"Unit 7",
        "lecture_7": r"Kuliah 7",
        "worksheet_7": r"Lembar Kerja 7",
        "source_solutions": r"Solusi yang disediakan oleh sumber",
        "model": re.escape(MODEL),
    }
    full_text = "\n".join(texts)
    missing_text = [name for name, pattern in required_text.items() if not re.search(pattern, full_text)]
    exercise_counts = Counter(re.findall(r"Soal 7\.(\d+)\.", full_text))
    solution_counts = Counter(re.findall(r"Solusi Soal 7\.(\d+)", full_text))
    gif_links = sorted(url for url in uri_links if "Aufgabe75.22" in url)

    # pdfplumber gives a second, layout-aware extraction path and bounded body
    # extents.  The 22 mm wrapper margins correspond to roughly 62.36 points.
    layout_empty: list[int] = []
    left_extents: list[float] = []
    right_extents: list[float] = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for index, page in enumerate(pdf.pages, 1):
            words = page.extract_words() or []
            if not words:
                layout_empty.append(index)
                continue
            left_extents.append(min(float(w["x0"]) for w in words))
            right_extents.append(max(float(w["x1"]) for w in words))

    root_catalog = reader.trailer["/Root"]
    passed = all(
        [
            size == EXPECTED_BYTES,
            sha == EXPECTED_SHA256,
            pages == EXPECTED_PAGES,
            all(close(w, EXPECTED_A4[0]) and close(h, EXPECTED_A4[1]) for w, h in boxes),
            not any(rotations),
            not empty_pages,
            not layout_empty,
            not missing_text,
            exercise_counts == Counter({str(i): 1 for i in range(1, 20)}),
            solution_counts == Counter({"4": 1, "7": 1, "13": 1}),
            gif_links == [
                "https://commons.wikimedia.org/wiki/File:Aufgabe75.22.1.gif",
                "https://commons.wikimedia.org/wiki/File:Aufgabe75.22.2.gif",
            ],
            not unsafe_actions,
            all(value["to_unicode"] for value in fonts.values()),
            bool(left_extents) and min(left_extents) >= 55.0,
            bool(right_extents) and max(right_extents) <= 550.0,
            not reader.is_encrypted,
        ]
    )
    receipt = {
        "schema_version": 1,
        "workflow": "o011-unit07-independent-pdf-boundary-qa-v1",
        "status": "pass" if passed else "fail",
        "passed": passed,
        "pdf": {"path": args.pdf.as_posix(), "bytes": size, "sha256": sha, "pages": pages,
                "media_boxes": boxes, "rotations": rotations, "encrypted": reader.is_encrypted,
                "metadata": metadata, "tagged": "/StructTreeRoot" in root_catalog,
                "lang": str(root_catalog.get("/Lang", ""))},
        "accessibility": {"pypdf_empty_pages": empty_pages, "pdfplumber_empty_pages": layout_empty,
                          "font_count": len(fonts), "fonts_without_tounicode": sorted(k for k,v in fonts.items() if not v["to_unicode"]),
                          "fonts_not_embedded": sorted(k for k,v in fonts.items() if not v["embedded"])},
        "layout": {"expected_a4_points": EXPECTED_A4, "left_min_points": min(left_extents) if left_extents else None,
                   "right_max_points": max(right_extents) if right_extents else None,
                   "body_margin_bounds_pass": bool(left_extents) and min(left_extents) >= 55.0 and max(right_extents) <= 550.0},
        "content": {"missing_required_text": missing_text, "exercise_counts": dict(sorted(exercise_counts.items())),
                    "solution_counts": dict(sorted(solution_counts.items())), "interactive_gif_links": gif_links,
                    "uri_count": len(uri_links), "annotation_subtypes": dict(sorted(subtype_counts.items()))},
        "limitations": ["PDF is not structurally tagged; semantic HTML remains the planned accessibility surface."],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
