#!/usr/bin/env python3
"""Freeze exact current Unit 2 solution revisions from one saved API response."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path


COURSE_TITLE = "Kurs:Differentialgeometrie (Osnabrück 2023)"
WORKSHEET_TITLE = f"{COURSE_TITLE}/Arbeitsblatt 2"
TASK_RE = re.compile(r"\{\{\s*inputaufgabe\s*\n\|([^|\n]+)", re.IGNORECASE)
EXPANDED_MACRO_RE = re.compile(
    r"(?m)^\\(inputaufgabegibtloesung|inputaufgabe)\b"
)


def digest(data: bytes, algorithm: str = "sha256") -> str:
    return hashlib.new(algorithm, data).hexdigest()


def extract_page_text(xml_path: Path, title: str) -> str:
    for _, element in ET.iterparse(xml_path, events=("end",)):
        if not element.tag.endswith("page"):
            continue
        page_title = next(
            (child.text for child in element if child.tag.endswith("title")), None
        )
        if page_title == title:
            revision = next(child for child in element if child.tag.endswith("revision"))
            text_element = next(child for child in revision if child.tag.endswith("text"))
            return text_element.text or ""
        element.clear()
    raise RuntimeError(f"page not found in frozen XML: {title}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.root.resolve()
    xml_path = root / "authority/mediawiki/brenner_course_recursive_current.xml"
    query_path = root / "authority/mediawiki/unit02_solution_pages_current.json"
    worksheet_tex_path = root / "authority/expanded/worksheet02_source.de.tex"

    root_wikitext = extract_page_text(xml_path, WORKSHEET_TITLE)
    tasks = [match.group(1).strip() for match in TASK_RE.finditer(root_wikitext)]
    if len(tasks) != 19:
        raise RuntimeError(f"expected 19 Unit 2 tasks in frozen root, found {len(tasks)}")

    macro_types = EXPANDED_MACRO_RE.findall(worksheet_tex_path.read_text(encoding="utf-8"))
    if len(macro_types) != len(tasks):
        raise RuntimeError(
            f"expanded task/macro count mismatch: {len(tasks)} roots, {len(macro_types)} macros"
        )
    macro_solution_indices = {
        index for index, macro in enumerate(macro_types, 1)
        if macro == "inputaufgabegibtloesung"
    }

    query_bytes = query_path.read_bytes()
    payload = json.loads(query_bytes.decode("utf-8"))
    pages = payload.get("query", {}).get("pages", [])
    pages_by_title = {page["title"]: page for page in pages}
    expected_titles = {f"{task}/Lösung" for task in tasks}
    if set(pages_by_title) != expected_titles:
        missing = sorted(expected_titles - set(pages_by_title))
        extra = sorted(set(pages_by_title) - expected_titles)
        raise RuntimeError(f"solution query title closure mismatch: missing={missing}, extra={extra}")

    existing_indices: set[int] = set()
    solution_rows: list[dict[str, object]] = []
    output_dir = root / "authority/mediawiki"
    for index, task in enumerate(tasks, 1):
        title = f"{task}/Lösung"
        page = pages_by_title[title]
        exists = "missing" not in page
        row: dict[str, object] = {
            "exercise_index": index,
            "task_title": task,
            "solution_title": title,
            "macro": macro_types[index - 1],
            "exists": exists,
        }
        if exists:
            existing_indices.add(index)
            revisions = page.get("revisions") or []
            if len(revisions) != 1:
                raise RuntimeError(f"expected one current revision for {title}")
            revision = revisions[0]
            slot = revision.get("slots", {}).get("main", {})
            content = slot.get("content")
            if not isinstance(content, str):
                raise RuntimeError(f"missing current main-slot content for {title}")
            content_bytes = content.encode("utf-8")
            if digest(content_bytes, "sha1") != revision["sha1"]:
                raise RuntimeError(f"MediaWiki SHA-1 mismatch for {title}")
            stem = f"worksheet02_exercise{index:02d}_solution_revid{revision['revid']}"
            base64_name = stem + ".utf8.b64"
            wiki_name = stem + ".wiki"
            metadata_name = stem + ".metadata.json"
            exact_base64 = base64.b64encode(content_bytes).decode("ascii") + "\n"
            (output_dir / base64_name).write_text(exact_base64, encoding="ascii", newline="\n")
            readable_bytes = (content.replace("\r\n", "\n").replace("\r", "\n").rstrip() + "\n").encode("utf-8")
            (output_dir / wiki_name).write_bytes(readable_bytes)
            metadata = {
                "authority": "German Wikiversity MediaWiki API",
                "query_response": "authority/mediawiki/unit02_solution_pages_current.json",
                "query_response_sha256": digest(query_bytes),
                "pageid": page["pageid"],
                "namespace": page["ns"],
                "title": title,
                "revid": revision["revid"],
                "parentid": revision["parentid"],
                "timestamp": revision["timestamp"],
                "mediawiki_sha1": revision["sha1"],
                "content_model": slot.get("contentmodel"),
                "content_format": slot.get("contentformat"),
                "source_characters": len(content),
                "source_utf8_bytes": len(content_bytes),
                "source_utf8_sha1": digest(content_bytes, "sha1"),
                "source_utf8_sha256": digest(content_bytes),
                "exact_utf8_base64_witness": base64_name,
                "exact_utf8_base64_sha256": digest(exact_base64.encode("ascii")),
                "readable_normalized_witness": wiki_name,
                "readable_normalized_bytes": len(readable_bytes),
                "readable_normalized_sha256": digest(readable_bytes),
            }
            metadata_bytes = (
                json.dumps(metadata, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
            ).encode("utf-8")
            (output_dir / metadata_name).write_bytes(metadata_bytes)
            expanded_json_path = root / f"authority/exports/worksheet02_exercise{index:02d}_solution_latex_expand.json"
            expanded_tex_path = root / f"authority/expanded/worksheet02_exercise{index:02d}_solution_source.de.tex"
            sanitize_receipt_path = root / f"qa/unit-02/worksheet02_exercise{index:02d}_solution_sanitize.json"
            expanded_json_bytes = expanded_json_path.read_bytes()
            expanded_tex_bytes = expanded_tex_path.read_bytes()
            sanitize_receipt_bytes = sanitize_receipt_path.read_bytes()
            sanitize_receipt = json.loads(sanitize_receipt_bytes.decode("utf-8"))
            if sanitize_receipt.get("input_sha256") != digest(expanded_json_bytes):
                raise RuntimeError(f"stale solution expansion receipt input for exercise {index}")
            if sanitize_receipt.get("output_sha256") != digest(expanded_tex_bytes):
                raise RuntimeError(f"stale solution expansion receipt output for exercise {index}")
            row.update({
                "pageid": page["pageid"],
                "revid": revision["revid"],
                "timestamp": revision["timestamp"],
                "mediawiki_sha1": revision["sha1"],
                "source_utf8_bytes": len(content_bytes),
                "source_utf8_sha256": digest(content_bytes),
                "metadata_path": f"authority/mediawiki/{metadata_name}",
                "metadata_sha256": digest(metadata_bytes),
                "exact_utf8_base64_witness": f"authority/mediawiki/{base64_name}",
                "readable_normalized_witness": f"authority/mediawiki/{wiki_name}",
                "expanded_latex_response": f"authority/exports/{expanded_json_path.name}",
                "expanded_latex_response_bytes": len(expanded_json_bytes),
                "expanded_latex_response_sha256": digest(expanded_json_bytes),
                "expanded_latex_source": f"authority/expanded/{expanded_tex_path.name}",
                "expanded_latex_source_bytes": len(expanded_tex_bytes),
                "expanded_latex_source_sha256": digest(expanded_tex_bytes),
                "sanitize_receipt": f"qa/unit-02/{sanitize_receipt_path.name}",
                "sanitize_receipt_sha256": digest(sanitize_receipt_bytes),
            })
        solution_rows.append(row)

    if existing_indices != macro_solution_indices:
        raise RuntimeError(
            "solution existence disagrees with expanded inputaufgabegibtloesung markers: "
            f"API={sorted(existing_indices)}, macros={sorted(macro_solution_indices)}"
        )

    manifest = {
        "schema_version": 1,
        "workflow": "o011-unit02-solution-freeze-v1",
        "frozen_root": "authority/mediawiki/brenner_course_recursive_current.xml",
        "frozen_root_sha256": digest(xml_path.read_bytes()),
        "worksheet_root_title": WORKSHEET_TITLE,
        "query_response": "authority/mediawiki/unit02_solution_pages_current.json",
        "query_response_bytes": len(query_bytes),
        "query_response_sha256": digest(query_bytes),
        "exercise_count": len(tasks),
        "supplied_solution_count": len(existing_indices),
        "supplied_solution_indices": sorted(existing_indices),
        "missing_solution_count": len(tasks) - len(existing_indices),
        "macro_api_agreement": True,
        "solutions": solution_rows,
    }
    manifest_path = root / "qa/unit-02/solution_closure.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_bytes(
        (json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    )


if __name__ == "__main__":
    main()
