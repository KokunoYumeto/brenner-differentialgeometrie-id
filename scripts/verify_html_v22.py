#!/usr/bin/env python3
"""Deterministically verify the cumulative semantic HTML reader through Unit 22."""

from __future__ import annotations

import argparse
import re
import sys
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import unquote

import export_html_v22 as exporter
from verify_html_v10 import source_topology
from verify_html_v19 import EXPECTED_MATHJAX_CONFIG, ReaderParser


WORKFLOW = "o011-verify-html-v22"


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def load_json(path: Path) -> dict[str, Any]:
    return exporter.load_json_object(path)


def payload_inventory(output: Path) -> list[dict[str, Any]]:
    return [
        exporter.file_binding(path, output)
        for path in sorted(item for item in output.rglob("*") if item.is_file() and item.name != "manifest.json")
    ]


def unit19_prefix(document: str, next_marker: str) -> str:
    start = document.index('<section class="unit" id="o011-brenner-u01"')
    end = document.index(next_marker, start)
    return document[start:end].rstrip()


def verify(root: Path, output: Path, restage: bool = True) -> dict[str, Any]:
    root, output = root.resolve(), exporter.assert_output_path(root, output)
    errors: list[str] = []
    manifest_path = output / "manifest.json"
    entry_path = output / "index.html"
    css_path = output / "assets/reader.css"
    readme_path = output / "README.txt"
    for path in (manifest_path, entry_path, css_path, readme_path):
        require(path.is_file(), f"missing required reader file: {path}", errors)
    if errors:
        raise RuntimeError("; ".join(errors))

    manifest = load_json(manifest_path)
    require(manifest.get("schema_version") == exporter.SCHEMA_VERSION, "manifest schema differs", errors)
    require(manifest.get("workflow") == exporter.WORKFLOW, "manifest workflow differs", errors)
    require(manifest.get("status") == "partial_edition", "reader status is not partial_edition", errors)
    require(manifest.get("language") == "id-ID", "reader language differs", errors)
    require(manifest.get("units") == list(range(1, 23)), "manifest does not cover exactly Units 1--22", errors)
    require(manifest.get("model_identification") == exporter.MODEL_IDENTIFICATION, "model identification differs", errors)
    require(manifest.get("text_license") == "CC BY-SA 4.0", "text license differs", errors)
    require(manifest.get("non_endorsement") is True, "non-endorsement flag differs", errors)

    expected_payload = payload_inventory(output)
    require(manifest.get("files") == expected_payload, "manifest payload file closure differs", errors)
    expected_inputs = [exporter.file_binding(path, root) for path in exporter.source_files(root)]
    require(manifest.get("inputs") == expected_inputs, "input bindings are stale or incomplete", errors)
    contract = exporter.generation_contract(root)
    require(manifest.get("unit19_baseline") == contract["unit19_baseline"], "exact Unit 19 baseline binding differs", errors)
    require(manifest.get("unit20_22_admission") == contract["unit20_22_admission"], "Unit 20--22 admission bindings differ", errors)
    require(manifest.get("generation_bindings") == contract["generation_bindings"], "generation bindings differ", errors)
    require(manifest.get("exporter") == contract["exporter"], "exporter binding differs", errors)

    html_bytes = entry_path.read_bytes()
    require(html_bytes.startswith(b'<!doctype html>\n<html lang="id-ID">'), "HTML preamble or locale differs", errors)
    require(b"\r" not in html_bytes, "HTML is not canonical LF text", errors)
    document = html_bytes.decode("utf-8")
    parser = ReaderParser()
    parser.feed(document)
    parser.close()
    errors.extend(parser.errors)
    require(parser.html_lang == "id-ID", "HTML root language differs", errors)
    require(parser.main_count == 1, "HTML must contain exactly one main landmark", errors)
    require(parser.nav_count >= 1, "HTML has no navigation landmark", errors)
    require(parser.heading_counts["h1"] == 1, "HTML must contain exactly one h1", errors)
    require(len(parser.ids) == len(set(parser.ids)), "HTML contains duplicate IDs", errors)
    ids = set(parser.ids)
    for href in parser.hrefs:
        if href.startswith("#"):
            require(href[1:] in ids, f"broken internal fragment: {href}", errors)
    for unit in range(1, 23):
        tag = f"{unit:02d}"
        for stable_id in (f"o011-brenner-u{tag}", f"o011-brenner-u{tag}-l{tag}", f"o011-brenner-u{tag}-w{tag}"):
            require(stable_id in ids, f"missing stable reader anchor: {stable_id}", errors)

    baseline_document = (root / "output/html/unit-19/index.html").read_text(encoding="utf-8")
    try:
        baseline_prefix = unit19_prefix(baseline_document, '  <section class="backmatter"')
        cumulative_prefix = unit19_prefix(document, '<section class="unit" id="o011-brenner-u20"')
        require(cumulative_prefix == baseline_prefix, "rendered Unit 1--19 section bytes differ from the committed Unit 19 reader", errors)
    except ValueError as exc:
        errors.append(f"cannot isolate exact Unit 19 section prefix: {exc}")

    require(len(parser.scripts) == 4, "HTML script surface differs from MathJax/config/deep-link/animation contract", errors)
    script_srcs = [item.get("src", "") for item in parser.scripts if item.get("src")]
    require(script_srcs == [exporter.MATHJAX_URL], "unexpected or unpinned external script", errors)
    for script_id in ("mathjax-config", "deep-link-stabilizer", "animated-media-controller"):
        require(any(item.get("id") == script_id and not item.get("src") for item in parser.scripts), f"local script is absent: {script_id}", errors)
    require(exporter.MATHJAX_CONFIG == EXPECTED_MATHJAX_CONFIG, "MathJax delimiter configuration differs", errors)
    require(f'<script id="mathjax-config">{EXPECTED_MATHJAX_CONFIG}</script>' in document, "escaped MathJax delimiters differ", errors)
    require('addEventListener("hashchange",settle)' in document and "new ResizeObserver" in document, "deep-link reflow stabilizer differs", errors)

    require(parser.math_elements > 0, "HTML contains no marked mathematical content", errors)
    for value in parser.math_text:
        stripped = value.strip()
        if stripped:
            require((stripped.startswith(r"\(") and stripped.endswith(r"\)")) or (stripped.startswith(r"\[") and stripped.endswith(r"\]")), "math element lacks compatible TeX delimiters", errors)
    outside = "".join(parser.outside_math)
    prohibited = re.compile(r"__NOEDITSECTION__|\[\[|\\(?:input|definitions|zwischenueberschrift|mavergleich|vergleichskette|maabb|bild|aufzaehlung|fakt|mathl|mathbed|mathkor|zusatz|leerzeichen)")
    require(prohibited.search(outside) is None, "unconverted source macro or MediaWiki residue leaked into reader prose", errors)
    require("Kategorie:Latexseite" not in outside and "Category:Latexseite" not in outside, "category metadata is visible", errors)
    require(exporter.MODEL_IDENTIFICATION in outside, "model provenance note is absent", errors)
    require("CC BY-SA 4.0" in outside and "bukan edisi resmi" in outside, "license/non-endorsement disclosure is absent", errors)
    require("dependensi opsional" in outside and "sumber TeX" in outside, "offline MathJax limitation is absent", errors)

    topology = manifest.get("topology")
    require(isinstance(topology, dict), "manifest topology is absent", errors)
    expected_exercise_ids: set[str] = set()
    expected_solution_map: dict[str, str] = {}
    expected_sections = expected_figures = expected_semantic_blocks = 0
    expected_unit_counts: dict[str, dict[str, Any]] = {}
    for unit in range(1, 23):
        tag = f"{unit:02d}"
        lecture_path = root / f"source/units/unit-{tag}/lecture{tag}.id.tex"
        worksheet_path = root / f"source/units/unit-{tag}/worksheet{tag}.id.tex"
        lecture = source_topology(lecture_path, "lecture")
        worksheet = source_topology(worksheet_path, "worksheet")
        indices = exporter.solution_indices(root, unit)
        declared = topology.get(tag, {}) if isinstance(topology, dict) else {}
        require(declared.get("lecture", {}).get("source_sections") == lecture["source_sections"], f"Unit {unit} lecture section topology differs", errors)
        require(declared.get("lecture", {}).get("semantic_blocks") == lecture["semantic_blocks"], f"Unit {unit} lecture semantic topology differs", errors)
        require(declared.get("lecture", {}).get("figures") == lecture["figures"], f"Unit {unit} lecture figure topology differs", errors)
        require(declared.get("worksheet", {}).get("source_sections") == worksheet["source_sections"], f"Unit {unit} worksheet section topology differs", errors)
        require(declared.get("worksheet", {}).get("exercises") == worksheet["exercises"], f"Unit {unit} exercise topology differs", errors)
        require(declared.get("worksheet", {}).get("figures") == worksheet["figures"], f"Unit {unit} worksheet figure topology differs", errors)
        require(declared.get("source_supplied_solution_indices") == indices, f"Unit {unit} solution topology differs", errors)
        require(worksheet["source_solution_markers"] == indices, f"Unit {unit} source solution markers/files differ", errors)
        expected_sections += lecture["source_sections"] + worksheet["source_sections"]
        expected_figures += lecture["figures"] + worksheet["figures"]
        expected_semantic_blocks += lecture["semantic_blocks"]
        expected_unit_counts[tag] = {"exercises": worksheet["exercises"], "solutions": indices, "figures": lecture["figures"] + worksheet["figures"]}
        for index in range(1, worksheet["exercises"] + 1):
            expected_exercise_ids.add(f"o011-brenner-u{tag}-w{tag}-e{index:03d}")
        for index in indices:
            exercise_id = f"o011-brenner-u{tag}-w{tag}-e{index:03d}"
            expected_solution_map[exercise_id + "-solution"] = exercise_id
            solution_path = root / f"source/units/unit-{tag}/worksheet{tag}_exercise{index:02d}_solution.id.tex"
            expected_sections += source_topology(solution_path, "lecture")["source_sections"]

    actual_exercises = {item["id"] for item in parser.entity_attrs if item.get("data-entity") == "exercise" and item.get("id")}
    actual_solutions = {item["id"]: item.get("data-solves", "") for item in parser.entity_attrs if item.get("data-entity") == "source-supplied-solution" and item.get("id")}
    require(actual_exercises == expected_exercise_ids, "stable exercise-anchor closure differs", errors)
    require(actual_solutions == expected_solution_map, "stable source-solution/data-solves closure differs", errors)
    require(parser.entities["source-section"] == expected_sections, "source-section count differs from TeX", errors)
    require(parser.entities["figure"] == expected_figures, "figure count differs from TeX", errors)
    semantic_entities = ("inputdefinition", "inputaxiom", "inputnotation", "inputbeispiel", "inputbemerkung", "inputverfahren", "inputkonstruktion", "inputfrage", "inputproblem", "inputsituation", "inputfakt", "inputfaktbeweis", "inputfaktbeweisnichtvorgefuehrt", "inputfaktbeweistrivial", "inputfaktuebergangbeweis")
    require(sum(parser.entities[name] for name in semantic_entities) == expected_semantic_blocks, "lecture semantic-block count differs from TeX", errors)

    media_list = manifest.get("media")
    require(isinstance(media_list, list), "media inventory is absent", errors)
    media_by_name = {str(item.get("filename")): item for item in media_list or [] if isinstance(item, dict)}
    require(len(media_by_name) == len(media_list or []), "embedded media filenames are duplicated", errors)
    for filename, item in media_by_name.items():
        source_binding = item.get("source", {})
        try:
            source = exporter.safe_project_path(root, str(source_binding.get("path", "")))
        except RuntimeError as exc:
            errors.append(str(exc))
            continue
        target = output / "assets/media" / filename
        require(source.is_file() and exporter.file_binding(source, root) == source_binding, f"media source binding differs: {filename}", errors)
        require(target.is_file(), f"media output is missing: {filename}", errors)
        if source.is_file() and target.is_file():
            require(source.read_bytes() == target.read_bytes(), f"media bytes differ: {filename}", errors)
        require(bool(str(item.get("creator") or "").strip()) and bool(str(item.get("license") or "").strip()), f"media rights are incomplete: {filename}", errors)
        require(bool(item.get("unit_media_receipts")), f"unit media receipt binding is absent: {filename}", errors)

    figures = manifest.get("figures")
    figure_list = figures if isinstance(figures, list) else []
    require(isinstance(figures, list), "figure occurrence manifest is absent", errors)
    require(len(figure_list) == len(parser.figure_records) == parser.figure_count == len(parser.images), "figure/HTML occurrence closure differs", errors)
    for declared, actual in zip(figure_list, parser.figure_records):
        filename = str(declared.get("filename"))
        image = actual.get("image") or {}
        media = media_by_name.get(filename, {})
        expected_image = str(media.get("animation", {}).get("static_filename")) if isinstance(media.get("animation"), dict) else filename
        require(actual.get("id") == declared.get("id"), f"figure stable ID differs: {declared.get('id')}", errors)
        require(image.get("alt") == declared.get("alt") and bool(str(image.get("alt") or "").strip()), f"figure alt text differs: {declared.get('id')}", errors)
        require(unquote(str(image.get("src", ""))) == f"assets/media/{expected_image}", f"figure image target differs: {declared.get('id')}", errors)
        caption = " ".join("".join(actual.get("caption_parts", [])).split())
        require(str(media.get("creator") or "") in caption and str(media.get("license") or "") in caption, f"figure rights are not visible: {declared.get('id')}", errors)

    linked = manifest.get("source_linked_media")
    linked_by_name = {str(item.get("filename")): item for item in linked or [] if isinstance(item, dict)}
    require(set(linked_by_name) == {"Aufgabe75.22.1.gif", "Aufgabe75.22.2.gif", "Aufgabe79.27.gif"}, "source-linked animation inventory differs", errors)
    linked_links = [item for item in parser.links if "source-linked-animation-download" in item.get("class", "").split()]
    require(len(linked_links) == 3 and parser.entities["source-linked-animation"] == 3, "source-linked animation accessibility surface differs", errors)
    for filename, item in linked_by_name.items():
        target = output / "assets/media" / filename
        source = exporter.safe_project_path(root, str(item.get("source", {}).get("path", "")))
        require(target.is_file() and source.is_file() and target.read_bytes() == source.read_bytes(), f"source-linked animation bytes differ: {filename}", errors)

    css = css_path.read_text(encoding="utf-8")
    require(css == (root / "output/html/unit-19/assets/reader.css").read_text(encoding="utf-8"), "reader CSS differs from the exact Unit 19 behavior", errors)
    require("--max:78rem" in css and "width:min(calc(100% - 2rem),var(--max))" in css, "centered readable width contract is absent", errors)
    require("@media(max-width:46rem)" in css and "main{width:100%" in css and "overflow-x:auto" in css, "responsive viewport reflow contract is absent", errors)
    require("prefers-reduced-motion" in css, "reduced-motion accessibility rule is absent", errors)
    readme = readme_path.read_text(encoding="utf-8")
    require("hingga Unit 22" in readme and "Putar animasi" in readme and "papan ketik" in readme, "README scope/accessibility disclosure differs", errors)

    excluded = manifest.get("excluded_reader_metadata", {})
    category_count = sum(path.read_text(encoding="utf-8").count("[[Kategorie:Latexseite]]") for path in exporter.source_files(root))
    require(excluded.get("mediawiki_category_marker") == "[[Kategorie:Latexseite]]" and excluded.get("occurrences") == category_count, "excluded metadata accounting differs", errors)
    reproducibility = manifest.get("reproducibility", {})
    require(reproducibility.get("staging_cycles") == 2 and reproducibility.get("byte_identical_before_commit") is True, "two-cycle reproducibility declaration differs", errors)
    require(reproducibility.get("payload_inventory_sha256") == exporter.inventory_sha256(expected_payload), "payload reproducibility digest differs", errors)

    restage_inventory: list[dict[str, Any]] | None = None
    if restage and not errors:
        with tempfile.TemporaryDirectory(prefix=".verify-html-v22-a-", dir=output.parent) as first_tmp, tempfile.TemporaryDirectory(prefix=".verify-html-v22-b-", dir=output.parent) as second_tmp:
            first, second = Path(first_tmp) / "reader", Path(second_tmp) / "reader"
            exporter._stage_cycle(root, first, contract)
            exporter._stage_cycle(root, second, contract)
            first_inventory, second_inventory = exporter.tree_inventory(first), exporter.tree_inventory(second)
            require(first_inventory == second_inventory, "independent verifier staging cycles differ", errors)
            require(first_inventory == exporter.tree_inventory(output), "committed reader differs from independent deterministic staging", errors)
            restage_inventory = first_inventory

    if errors:
        raise RuntimeError("HTML v22 verification failed:\n- " + "\n- ".join(dict.fromkeys(errors)))
    output_inventory = [exporter.file_binding(path, root) for path in sorted(item for item in output.rglob("*") if item.is_file())]
    return {
        "schema_version": 1,
        "workflow": WORKFLOW,
        "status": "pass",
        "scope": "Cumulative Indonesian semantic HTML reader through Unit 22",
        "entry": exporter.file_binding(entry_path, root),
        "manifest": exporter.file_binding(manifest_path, root),
        "checks": {
            "exact_unit19_output_and_section_bytes_preserved": True,
            "unit20_22_admission_receipts_bound": True,
            "manifest_file_and_input_hash_closure": True,
            "strict_html_tag_balance": True,
            "unique_resolved_stable_deep_links": True,
            "exact_exercise_solution_media_topology": True,
            "mathjax_delimiters_and_offline_fallback": True,
            "responsive_centered_reflow_layout": True,
            "media_alt_caption_rights_and_byte_closure": True,
            "two_independent_staging_cycles_match_committed_tree": restage_inventory is not None,
        },
        "counts": {
            "units": 22,
            "input_files": len(expected_inputs),
            "output_files": len(output_inventory),
            "stable_ids": len(ids),
            "exercises": len(expected_exercise_ids),
            "source_supplied_solutions": len(expected_solution_map),
            "semantic_blocks": expected_semantic_blocks,
            "source_sections": expected_sections,
            "math_elements": parser.math_elements,
            "figures": expected_figures,
            "embedded_media_files": len(media_by_name),
            "source_linked_media_files": len(linked_by_name),
        },
        "unit20_22_census": {tag: expected_unit_counts[tag] for tag in ("20", "21", "22")},
        "reproducibility": {
            "cycles": 2,
            "complete_tree_inventory_sha256": exporter.inventory_sha256(exporter.tree_inventory(output)),
            "byte_identical_to_committed_output": restage_inventory is not None,
        },
        "unit19_baseline": {
            "status": contract["unit19_baseline"]["status"],
            "output_file_count": contract["unit19_baseline"]["output_file_count"],
            "output_inventory_sha256": contract["unit19_baseline"]["output_inventory_sha256"],
        },
        "output_inventory": output_inventory,
        "verifier": exporter.file_binding(Path(__file__).resolve(), root),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--receipt", type=Path, default=None)
    parser.add_argument("--skip-restage", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    output = (args.output or root / "output/html/unit-22").resolve()
    receipt = (args.receipt or root / "qa/unit-22/HTML_READER_QA.json").resolve()
    try:
        result = verify(root, output, restage=not args.skip_restage)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
    exporter.write_text(receipt, exporter.canonical_json(result))
    print(exporter.canonical_json({
        "status": "pass",
        "receipt": receipt.relative_to(root).as_posix(),
        "entry": result["entry"],
        "manifest": result["manifest"],
        "counts": result["counts"],
        "unit20_22_census": result["unit20_22_census"],
        "reproducibility": result["reproducibility"],
    }), end="")


if __name__ == "__main__":
    main()
