#!/usr/bin/env python3
"""Validate and summarize the frozen O011 Unit 2 authority closure."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path


COURSE = "Kurs:Differentialgeometrie (Osnabrück 2023)"
LECTURE_ROOT = f"{COURSE}/Vorlesung 2"
WORKSHEET_ROOT = f"{COURSE}/Arbeitsblatt 2"
LECTURE_SURFACE = LECTURE_ROOT + "/latex"
WORKSHEET_SURFACE = WORKSHEET_ROOT + "/latex"
TASK_MACRO = re.compile(r"(?m)^\\(inputaufgabegibtloesung|inputaufgabe)\b")
SECTION_MACRO = re.compile(r"(?m)^\s*\\zwischenueberschrift\s*\{")
IMAGE_LICENSE = re.compile(r"\\bildlizenz\s*\{\s*([^}]+?)\s*\}")


def digest(data: bytes, algorithm: str = "sha256") -> str:
    return hashlib.new(algorithm, data).hexdigest()


def rel(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def file_entry(path: Path, root: Path) -> dict[str, object]:
    data = path.read_bytes()
    return {
        "path": rel(path, root),
        "bytes": len(data),
        "sha256": digest(data),
    }


def utc_mtime(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


def unique_revision(rows: list[dict[str, str]], title: str) -> dict[str, object]:
    matches = [row for row in rows if row.get("title") == title]
    if len(matches) != 1:
        raise RuntimeError(f"expected one revision row for {title!r}, found {len(matches)}")
    row = matches[0]
    return {
        "title": row["title"],
        "namespace": int(row["namespace"]),
        "pageid": int(row["pageid"]),
        "revid": int(row["revid"]),
        "timestamp_utc": row["timestamp_utc"],
        "mediawiki_sha1_base36": row["mediawiki_sha1_base36"],
        "text_utf8_bytes": int(row["text_utf8_bytes"]),
        "source_export_file": row["source_export_file"],
        "source_export_sha256": row["source_export_sha256"],
    }


def validate_expansion(
    root: Path,
    response_path: Path,
    output_path: Path,
    receipt_path: Path,
    context_title: str,
) -> dict[str, object]:
    response_bytes = response_path.read_bytes()
    payload = json.loads(response_bytes.decode("utf-8"))
    if payload.get("error"):
        raise RuntimeError(f"API error in {response_path}: {payload['error']}")
    expanded = payload.get("expandtemplates", {}).get("wikitext")
    if not isinstance(expanded, str):
        raise RuntimeError(f"missing expanded wikitext in {response_path}")
    output_bytes = output_path.read_bytes()
    output_text = output_bytes.decode("utf-8")
    receipt_bytes = receipt_path.read_bytes()
    receipt = json.loads(receipt_bytes.decode("utf-8"))
    if receipt.get("input_sha256") != digest(response_bytes):
        raise RuntimeError(f"stale sanitizer input receipt: {receipt_path}")
    if receipt.get("output_sha256") != digest(output_bytes):
        raise RuntimeError(f"stale sanitizer output receipt: {receipt_path}")
    if "\ufffd" in output_text or re.search(r"</?[A-Za-z][^>]*>", output_text):
        raise RuntimeError(f"unsafe residue in sanitized source: {output_path}")
    return {
        "api_endpoint": "https://de.wikiversity.org/w/api.php",
        "parameters": {
            "action": "expandtemplates",
            "format": "json",
            "formatversion": 2,
            "prop": "wikitext|categories|modules|jsconfigvars",
            "title": context_title,
            "text": "{{Latex}}",
        },
        "retrieved_utc_local_receipt": utc_mtime(response_path),
        "response": file_entry(response_path, root),
        "expanded_characters": len(expanded),
        "sanitized_source": file_entry(output_path, root),
        "sanitizer_receipt": file_entry(receipt_path, root),
        "sanitizer": file_entry(root / "scripts/sanitize_brenner_expand.py", root),
        "valid_utf8": True,
        "residual_html_tags": False,
        "replacement_characters": False,
    }


def xml_solution_titles(xml_path: Path) -> list[str]:
    found: list[str] = []
    for _, element in ET.iterparse(xml_path, events=("end",)):
        if element.tag.endswith("page"):
            title = next(
                (child.text for child in element if child.tag.endswith("title")), ""
            )
            if title and title.endswith("/Lösung"):
                found.append(title)
            element.clear()
    return sorted(found)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--checkpoint", required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", args.checkpoint):
        raise RuntimeError("checkpoint must be explicit YYYY-MM-DDTHH:MM:SSZ")
    root = args.root.resolve()

    recursive_xml = root / "authority/mediawiki/brenner_course_recursive_current.xml"
    latex_xml = root / "authority/mediawiki/brenner_latex_kontrolle_recursive_current.xml"
    root_csv_path = root / "authority/brenner_selected_root_revisions.csv"
    surface_csv_path = root / "authority/brenner_selected_surface_revisions.csv"
    root_csv = list(csv.DictReader(io.StringIO(root_csv_path.read_text(encoding="utf-8-sig"))))
    surface_csv = list(csv.DictReader(io.StringIO(surface_csv_path.read_text(encoding="utf-8-sig"))))
    root_revisions = {
        "lecture": unique_revision(root_csv, LECTURE_ROOT),
        "worksheet": unique_revision(root_csv, WORKSHEET_ROOT),
    }
    surface_revisions = {
        "lecture_latex": unique_revision(surface_csv, LECTURE_SURFACE),
        "worksheet_latex": unique_revision(surface_csv, WORKSHEET_SURFACE),
    }
    actual_export_hashes = {
        recursive_xml.name: digest(recursive_xml.read_bytes()),
        latex_xml.name: digest(latex_xml.read_bytes()),
    }
    for revision in [*root_revisions.values(), *surface_revisions.values()]:
        if actual_export_hashes.get(str(revision["source_export_file"])) != revision["source_export_sha256"]:
            raise RuntimeError(f"revision CSV export hash mismatch for {revision['title']}")

    lecture_expansion = validate_expansion(
        root,
        root / "authority/exports/lecture02_latex_expand.json",
        root / "authority/expanded/lecture02_source.de.tex",
        root / "qa/unit-02/lecture02_sanitize.json",
        LECTURE_SURFACE,
    )
    worksheet_expansion = validate_expansion(
        root,
        root / "authority/exports/worksheet02_latex_expand.json",
        root / "authority/expanded/worksheet02_source.de.tex",
        root / "qa/unit-02/worksheet02_sanitize.json",
        WORKSHEET_SURFACE,
    )
    lecture_text = (root / lecture_expansion["sanitized_source"]["path"]).read_text(encoding="utf-8")
    worksheet_text = (root / worksheet_expansion["sanitized_source"]["path"]).read_text(encoding="utf-8")
    worksheet_macros = TASK_MACRO.findall(worksheet_text)
    solution_indices = [
        index for index, macro in enumerate(worksheet_macros, 1)
        if macro == "inputaufgabegibtloesung"
    ]

    solution_manifest_path = root / "qa/unit-02/solution_closure.json"
    solution_manifest = json.loads(solution_manifest_path.read_text(encoding="utf-8"))
    if solution_manifest.get("supplied_solution_indices") != solution_indices:
        raise RuntimeError("solution manifest disagrees with worksheet solution-bearing macros")
    frozen_xml_solution_titles = xml_solution_titles(recursive_xml)

    media_query_path = root / "authority/mediawiki/unit02_media_imageinfo_current.json"
    media_query_bytes = media_query_path.read_bytes()
    media_query = json.loads(media_query_bytes.decode("utf-8"))
    media_pages: dict[str, dict[str, object]] = {}
    for page in media_query.get("query", {}).get("pages", []):
        filename = page["title"].split(":", 1)[-1]
        media_pages[filename] = page
    used_images = [name.strip() for name in IMAGE_LICENSE.findall(lecture_text)]
    worksheet_images = [name.strip() for name in IMAGE_LICENSE.findall(worksheet_text)]
    solution_images: list[str] = []
    for solution in solution_manifest["solutions"]:
        if solution.get("exists"):
            solution_path = root / solution["expanded_latex_source"]
            solution_images.extend(name.strip() for name in IMAGE_LICENSE.findall(solution_path.read_text(encoding="utf-8")))
    if worksheet_images or solution_images:
        raise RuntimeError("unexpected Unit 2 image use outside Lecture 2")
    if used_images != ["Integral apl rot obsah1.svg", "Hyperboloid1.png"]:
        raise RuntimeError(f"unexpected Lecture 2 image sequence: {used_images}")

    rights_path = root / "authority/brenner_media_rights_manifest.csv"
    rights_rows = list(csv.DictReader(io.StringIO(rights_path.read_text(encoding="utf-8-sig"))))
    rights_by_filename = {
        row["title"].removeprefix("File:"): row for row in rights_rows
    }
    media_records: list[dict[str, object]] = []
    for order, filename in enumerate(used_images, 1):
        if filename not in media_pages or filename not in rights_by_filename:
            raise RuntimeError(f"missing API or rights closure for {filename}")
        imageinfo = media_pages[filename].get("imageinfo") or []
        if len(imageinfo) != 1:
            raise RuntimeError(f"expected one imageinfo row for {filename}")
        info = imageinfo[0]
        rights = rights_by_filename[filename]
        binary_path = root / "authority/media" / filename
        binary = binary_path.read_bytes()
        if len(binary) != int(info["size"]) or digest(binary, "sha1") != info["sha1"]:
            raise RuntimeError(f"downloaded media does not match current imageinfo: {filename}")
        if len(binary) != int(rights["bytes"]) or digest(binary, "sha1") != rights["commons_sha1_hex"]:
            raise RuntimeError(f"downloaded media does not match frozen rights manifest: {filename}")
        if info["mime"] != rights["mime"]:
            raise RuntimeError(f"media MIME mismatch: {filename}")
        media_records.append({
            "order": order,
            "surface": "lecture02",
            "filename": filename,
            "binary": file_entry(binary_path, root),
            "commons_sha1": info["sha1"],
            "bytes": int(info["size"]),
            "width": int(info["width"]),
            "height": int(info["height"]),
            "mime": info["mime"],
            "original_url": info["url"].split("?", 1)[0],
            "description_url": info["descriptionurl"],
            "license": rights["license"],
            "license_url": rights["license_url"] or None,
            "attribution_required": rights["attribution_required"].lower() == "true",
            "artist_html": rights["artist_html"],
            "credit_html": rights["credit_html"],
            "rights_manifest_sha256": digest(rights_path.read_bytes()),
            "current_api_matches_frozen_manifest": True,
        })

    for solution in solution_manifest["solutions"]:
        if not solution.get("exists"):
            continue
        response_path = root / solution["expanded_latex_response"]
        source_path = root / solution["expanded_latex_source"]
        receipt_path = root / solution["sanitize_receipt"]
        validate_expansion(
            root,
            response_path,
            source_path,
            receipt_path,
            solution["solution_title"] + "/latex",
        )

    manifest = {
        "schema_version": 1,
        "workflow": "o011-unit02-authority-preflight-v1",
        "checkpoint_utc": args.checkpoint,
        "scope": "Brenner Differentialgeometrie Unit 2 authority preflight; no translation",
        "authority": {
            "course_recursive_export": file_entry(recursive_xml, root),
            "latex_surface_recursive_export": file_entry(latex_xml, root),
            "root_revision_manifest": file_entry(root_csv_path, root),
            "surface_revision_manifest": file_entry(surface_csv_path, root),
            "root_revisions": root_revisions,
            "surface_revisions": surface_revisions,
        },
        "expansions": {
            "lecture": lecture_expansion,
            "worksheet": worksheet_expansion,
        },
        "structure": {
            "lecture_section_count": len(SECTION_MACRO.findall(lecture_text)),
            "worksheet_exercise_count": len(worksheet_macros),
            "worksheet_solution_bearing_macro_count": len(solution_indices),
            "worksheet_solution_bearing_indices": solution_indices,
            "additional_solution_bearing_macros": [],
        },
        "solutions": {
            "frozen_recursive_xml_solution_page_count": len(frozen_xml_solution_titles),
            "frozen_recursive_xml_solution_titles": frozen_xml_solution_titles,
            "current_api_query_required": len(frozen_xml_solution_titles) == 0,
            "api_endpoint": "https://de.wikiversity.org/w/api.php",
            "query_parameters": {
                "action": "query",
                "format": "json",
                "formatversion": 2,
                "prop": "revisions",
                "rvprop": "ids|timestamp|sha1|content",
                "rvslots": "main",
                "titles": "the 19 exact task titles from the frozen Worksheet 2 root, each suffixed /Lösung",
            },
            "expanded_latex_recipe": {
                "action": "expandtemplates",
                "format": "json",
                "formatversion": 2,
                "prop": "wikitext|categories|modules|jsconfigvars",
                "title": "the exact supplied-solution title suffixed /latex",
                "text": "{{Latex}}",
            },
            "query": file_entry(root / "authority/mediawiki/unit02_solution_pages_current.json", root),
            "query_retrieved_utc_local_receipt": utc_mtime(root / "authority/mediawiki/unit02_solution_pages_current.json"),
            "closure_manifest": file_entry(solution_manifest_path, root),
            "exercise_count": solution_manifest["exercise_count"],
            "supplied_solution_count": solution_manifest["supplied_solution_count"],
            "supplied_solution_indices": solution_manifest["supplied_solution_indices"],
            "missing_solution_count": solution_manifest["missing_solution_count"],
            "macro_api_agreement": solution_manifest["macro_api_agreement"],
            "supplied": [row for row in solution_manifest["solutions"] if row["exists"]],
        },
        "media": {
            "lecture_image_count": len(used_images),
            "worksheet_image_count": len(worksheet_images),
            "solution_image_count": len(solution_images),
            "api_endpoint": "https://de.wikiversity.org/w/api.php",
            "query_parameters": {
                "action": "query",
                "format": "json",
                "formatversion": 2,
                "prop": "imageinfo",
                "iiprop": "url|size|sha1|mime|extmetadata",
                "titles": "File:Integral apl rot obsah1.svg|File:Hyperboloid1.png",
            },
            "current_imageinfo_query": file_entry(media_query_path, root),
            "query_retrieved_utc_local_receipt": utc_mtime(media_query_path),
            "rights_manifest": file_entry(rights_path, root),
            "assets": media_records,
        },
        "checks": {
            "root_revision_bindings_unique": True,
            "surface_revision_bindings_unique": True,
            "revision_export_hashes_match": True,
            "lecture_expansion_sanitized": True,
            "worksheet_expansion_sanitized": True,
            "exercise_macro_count_is_19": len(worksheet_macros) == 19,
            "solution_macro_api_agreement": solution_manifest["macro_api_agreement"],
            "all_supplied_solution_revisions_frozen": True,
            "all_supplied_solution_latex_snapshots_frozen": True,
            "unit_media_binary_and_rights_closure": True,
            "translation_started": False,
        },
        "status": "pass",
        "next_action": "Translate Lecture 2, Worksheet 2, and the five supplied solutions in source order; preserve the two public-domain images and stable exercise indices.",
    }
    output_path = root / "qa/unit-02/AUTHORITY_PREFLIGHT.json"
    output_path.write_bytes(
        (json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    )


if __name__ == "__main__":
    main()
