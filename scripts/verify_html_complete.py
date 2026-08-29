#!/usr/bin/env python3
"""Deterministically verify the complete O011 Indonesian semantic HTML reader."""

from __future__ import annotations

import argparse
import re
import sys
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import unquote

import export_html_complete as exporter
from verify_html_v10 import source_topology
from verify_html_v19 import EXPECTED_MATHJAX_CONFIG, ReaderParser, verify_animated_surface


WORKFLOW = "o011-verify-html-complete-v1"
EXPECTED_ACTUAL = [14, 11, 12, 12, 14, 11, 11, 14, 13, 11]
EXPECTED_SUPPLIED = [13, 11, 11, 12, 13, 11, 10, 14, 12, 10]
EXPECTED_MISSING = [[11], [], [10], [], [5], [], [10], [], [9], [4]]
EXPECTED_PLACEHOLDERS = [[], [], [3, 4, 7, 15], [3, 4, 8, 16], [], [5, 6, 7, 11, 14], [3, 8, 11, 14, 15], [4, 6, 9], [], [6, 10, 13]]


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def load_json(path: Path) -> dict[str, Any]:
    return exporter.load_json_object(path)


def assert_output_path(root: Path, output: Path) -> Path:
    output = output.resolve()
    expected_root = (root / "output/html").resolve()
    try:
        output.relative_to(expected_root)
    except ValueError as exc:
        raise RuntimeError("complete HTML output must remain beneath output/html") from exc
    if output == expected_root:
        raise RuntimeError("complete HTML output may not be output/html itself")
    return output


def safe_path(root: Path, relative: str) -> Path:
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise RuntimeError(f"path escapes declared root: {relative}") from exc
    return candidate


def payload_inventory(output: Path) -> list[dict[str, Any]]:
    return [
        exporter.file_binding(path, output)
        for path in sorted(
            item for item in output.rglob("*")
            if item.is_file() and item.name != "manifest.json"
        )
    ]


def section_bytes(document: str, start_marker: str, end_marker: str) -> str:
    start = document.index(start_marker)
    end = document.index(end_marker, start)
    return document[start:end].rstrip()


def verify(root: Path, output: Path, restage: bool = True) -> dict[str, Any]:
    root = root.resolve()
    output = assert_output_path(root, output)
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
    require(manifest.get("status") == "complete_edition", "reader status is not complete_edition", errors)
    require(manifest.get("scope") == "complete O011 Indonesian reader: 29 core units, two original bridges, and ten-form assessment bank", "manifest scope differs", errors)
    require(manifest.get("language") == "id-ID", "reader language differs", errors)
    require(manifest.get("units") == list(range(1, 30)), "manifest does not cover exactly Units 1--29", errors)
    require(manifest.get("bridges") == ["Lie groups and Lie algebras", "de Rham cohomology and differential-topology gateway"], "bridge inventory differs", errors)
    require(manifest.get("exam_forms") == list(range(1, 11)), "exam-form inventory differs", errors)
    require(manifest.get("model_identification") == exporter.MODEL_IDENTIFICATION, "model identification differs", errors)
    require(manifest.get("official_source") == exporter.OFFICIAL_SOURCE, "official source differs", errors)
    require(manifest.get("text_license") == "CC BY-SA 4.0", "text license differs", errors)
    require(manifest.get("component_media_licenses_remain_file_specific") is True, "file-specific media-rights flag differs", errors)
    require(manifest.get("non_endorsement") is True, "non-endorsement flag differs", errors)

    expected_payload = payload_inventory(output)
    require(manifest.get("files") == expected_payload, "manifest payload file closure differs", errors)
    expected_inputs = [exporter.file_binding(path, root) for path in exporter.all_inputs(root)]
    require(manifest.get("inputs") == expected_inputs, "manifest input bindings are stale or incomplete", errors)
    contract = exporter.generation_contract(root)
    require(manifest.get("generation_contract") == contract, "generation contract differs", errors)
    reproducibility = manifest.get("reproducibility", {})
    require(reproducibility.get("staging_cycles") == 2, "manifest does not declare two staging cycles", errors)
    require(reproducibility.get("byte_identical_complete_trees_required") is True, "byte-identical complete-tree requirement differs", errors)
    require(reproducibility.get("payload_inventory_sha256") == exporter.inventory_sha256(expected_payload), "payload inventory digest differs", errors)

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
    require(parser.nav_count >= 2, "HTML lacks its core or supplement navigation", errors)
    require(parser.heading_counts["h1"] >= 1, "HTML has no level-one heading", errors)
    require(len(parser.ids) == len(set(parser.ids)), "HTML contains duplicate IDs", errors)
    ids = set(parser.ids)
    for href in parser.hrefs:
        if href.startswith("#"):
            target = unquote(href[1:])
            require(bool(target) and target in ids, f"broken internal fragment: {href}", errors)

    for unit in range(1, 30):
        tag = f"{unit:02d}"
        for stable_id in (f"o011-brenner-u{tag}", f"o011-brenner-u{tag}-l{tag}", f"o011-brenner-u{tag}-w{tag}"):
            require(stable_id in ids, f"missing core stable anchor: {stable_id}", errors)
    require(parser.entities["unit"] == 29 and parser.entities["lecture"] == 29 and parser.entities["worksheet"] == 29, "core unit/lecture/worksheet entity counts differ", errors)

    unit22_contract = contract.get("unit22_public_reader_baseline", {})
    require(isinstance(unit22_contract, dict) and bool(unit22_contract), "Unit 22 public-reader baseline is not bound into the complete generation contract", errors)

    require(len(parser.scripts) == 4, "HTML script surface differs from the MathJax/deep-link/animation contract", errors)
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

    topology = manifest.get("core_topology")
    require(isinstance(topology, dict), "core topology is absent", errors)
    expected_exercise_ids: set[str] = set()
    expected_solution_map: dict[str, str] = {}
    expected_sections = expected_figures = expected_semantic_blocks = 0
    unit_census: dict[str, dict[str, Any]] = {}
    for unit in range(1, 30):
        tag = f"{unit:02d}"
        lecture_path = root / f"source/units/unit-{tag}/lecture{tag}.id.tex"
        worksheet_path = root / f"source/units/unit-{tag}/worksheet{tag}.id.tex"
        lecture = source_topology(lecture_path, "lecture")
        worksheet = source_topology(worksheet_path, "worksheet")
        indices = exporter.v22.solution_indices(root, unit)
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
        unit_census[tag] = {"exercises": worksheet["exercises"], "solutions": indices, "figures": lecture["figures"] + worksheet["figures"]}
        for index in range(1, worksheet["exercises"] + 1):
            expected_exercise_ids.add(f"o011-brenner-u{tag}-w{tag}-e{index:03d}")
        for index in indices:
            exercise_id = f"o011-brenner-u{tag}-w{tag}-e{index:03d}"
            expected_solution_map[exercise_id + "-solution"] = exercise_id
            solution_path = root / f"source/units/unit-{tag}/worksheet{tag}_exercise{index:02d}_solution.id.tex"
            expected_sections += source_topology(solution_path, "lecture")["source_sections"]

    actual_exercises = {item["id"] for item in parser.entity_attrs if item.get("data-entity") == "exercise" and item.get("id")}
    actual_solutions = {item["id"]: item.get("data-solves", "") for item in parser.entity_attrs if item.get("data-entity") == "source-supplied-solution" and item.get("id")}
    require(actual_exercises == expected_exercise_ids, "core stable exercise-anchor closure differs", errors)
    require(actual_solutions == expected_solution_map, "core source-solution/data-solves closure differs", errors)
    require(parser.entities["source-section"] == expected_sections, "core source-section count differs from TeX", errors)
    require(parser.entities["figure"] == expected_figures, "core figure count differs from TeX", errors)
    semantic_entities = ("inputdefinition", "inputaxiom", "inputnotation", "inputbeispiel", "inputbemerkung", "inputverfahren", "inputkonstruktion", "inputfrage", "inputproblem", "inputsituation", "inputfakt", "inputfaktbeweis", "inputfaktbeweisnichtvorgefuehrt", "inputfaktbeweistrivial", "inputfaktuebergangbeweis")
    require(sum(parser.entities[name] for name in semantic_entities) == expected_semantic_blocks, "core semantic-block count differs from TeX", errors)

    exam_topology = manifest.get("exam_topology")
    require(isinstance(exam_topology, dict) and set(exam_topology) == {f"{exam:02d}" for exam in range(1, 11)}, "exam topology keys differ", errors)
    expected_exam_problem_ids: set[str] = set()
    expected_exam_solution_map: dict[str, str] = {}
    missing_pairs: set[tuple[int, int]] = set()
    nominal_total = actual_total = supplied_total = missing_total = placeholder_total = 0
    for exam in range(1, 11):
        tag = f"{exam:02d}"
        declared = exam_topology.get(tag, {}) if isinstance(exam_topology, dict) else {}
        placeholders = EXPECTED_PLACEHOLDERS[exam - 1]
        nominal = EXPECTED_ACTUAL[exam - 1] + len(placeholders)
        actual_slots = [slot for slot in range(1, nominal + 1) if slot not in placeholders]
        missing = EXPECTED_MISSING[exam - 1]
        require(declared.get("nominal_slots") == nominal, f"Exam {exam} nominal-slot count differs", errors)
        require(declared.get("actual_occurrences") == EXPECTED_ACTUAL[exam - 1], f"Exam {exam} actual occurrence count differs", errors)
        require(declared.get("actual_occurrence_slots") == actual_slots, f"Exam {exam} actual occurrence slots differ", errors)
        require(declared.get("zero_point_placeholder_slots") == placeholders, f"Exam {exam} placeholder slots differ", errors)
        require(declared.get("source_supplied_solution_occurrences") == EXPECTED_SUPPLIED[exam - 1], f"Exam {exam} source-solution count differs", errors)
        require(declared.get("source_missing_nonzero_solution_occurrences") == missing, f"Exam {exam} missing-solution slots differ", errors)
        require(len(declared.get("point_labels", [])) == EXPECTED_ACTUAL[exam - 1], f"Exam {exam} actual point-label census differs", errors)
        require(f"ujian-{tag}" in ids, f"Exam {exam} form anchor is absent", errors)
        for slot in actual_slots:
            problem_id = f"o011-exam-{tag}-p{slot:03d}"
            expected_exam_problem_ids.add(problem_id)
            if slot not in missing:
                expected_exam_solution_map[problem_id + "-source-solution"] = problem_id
        missing_pairs.update((exam, slot) for slot in missing)
        nominal_total += nominal
        actual_total += EXPECTED_ACTUAL[exam - 1]
        supplied_total += EXPECTED_SUPPLIED[exam - 1]
        missing_total += len(missing)
        placeholder_total += len(placeholders)
    actual_exam_problem_ids = {item["id"] for item in parser.entity_attrs if item.get("data-entity") == "exam-problem" and item.get("id")}
    actual_exam_solution_map = {item["id"]: item.get("data-solves", "") for item in parser.entity_attrs if item.get("data-entity") == "source-supplied-exam-solution" and item.get("id")}
    require(actual_exam_problem_ids == expected_exam_problem_ids, "exam-problem stable-ID closure differs", errors)
    require(actual_exam_solution_map == expected_exam_solution_map, "source-supplied exam solution/data-solves closure differs", errors)
    require(parser.entities["exam-form"] == 10 and parser.entities["exam-problem"] == 123 and parser.entities["source-supplied-exam-solution"] == 117, "rendered exam entity census differs", errors)
    require((nominal_total, actual_total, supplied_total, missing_total, placeholder_total) == (147, 123, 117, 6, 24), "aggregate exam census differs", errors)

    repair_qa = load_json(root / "qa/exams/ORIGINAL_MISSING_SOLUTIONS_QA.json")
    bindings = repair_qa.get("occurrence_bindings", [])
    repair_pairs = {(int(item["form"]), int(item["slot"])) for item in bindings if isinstance(item, dict)}
    repair_ids = {str(item["stable_id"]).casefold() for item in bindings if isinstance(item, dict)}
    require(repair_pairs == missing_pairs, "six original repairs do not bind exactly the six missing exam occurrences", errors)
    require(len(repair_ids) == 6 and repair_ids <= ids, "original repair stable-ID surface differs", errors)
    require(repair_qa.get("census", {}).get("source_supplied_solutions_misattributed") == 0, "original repairs are misattributed", errors)
    require("o011-exam-original-repairs" in ids and "solusi-perbaikan-asli" in ids, "original repair section anchors are absent", errors)
    require(parser.entities["original-exam-solution-repairs"] == 1, "original repair section is absent or duplicated", errors)

    bridge_specs = {
        "lie": {
            "surface": "jembatan-lie",
            "root_id": "o011-bridge-lie",
            "assessment": root / "source/bridges/lie-groups/bridge-lie-assessment.id.tex",
            "qa": root / "qa/bridges/lie-groups/BRIDGE_LIE_CONTENT_SMOKE_QA.json",
            "item_ids": [*(f"o011-bl-e{i:02d}" for i in range(1, 13)), *(f"o011-bl-m{i:02d}" for i in range(1, 5))],
            "solution_prefix": "lie-assessment-solusi",
            "end": '<section class="supplement bridge" id="jembatan-de-rham"',
        },
        "de-rham": {
            "surface": "jembatan-de-rham",
            "root_id": "o011-bridge-de-rham",
            "assessment": root / "source/bridges/de-rham/bridge-de-rham-assessment.id.tex",
            "qa": root / "qa/bridges/de-rham/BRIDGE_DE_RHAM_CONTENT_SMOKE_QA.json",
            "item_ids": [*(f"o011-br-e{i:02d}" for i in range(1, 13)), *(f"o011-br-m{i:02d}" for i in range(1, 5))],
            "solution_prefix": "de-rham-assessment-solusi",
            "end": '<section class="supplement assessment-bank" id="bank-ujian"',
        },
    }
    bridge_solution_items = 0
    for name, spec in bridge_specs.items():
        start = f'<section class="supplement bridge" id="{spec["surface"]}"'
        try:
            fragment = section_bytes(document, start, str(spec["end"]))
        except ValueError as exc:
            errors.append(f"cannot isolate {name} bridge: {exc}")
            fragment = ""
        require(spec["surface"] in ids and spec["root_id"] in ids, f"{name} bridge surface anchors are absent", errors)
        item_ids = set(spec["item_ids"])
        require(item_ids <= ids and all(f'id="{item_id}"' in fragment for item_id in item_ids), f"{name} bridge stable item IDs differ", errors)
        assessment_text = Path(spec["assessment"]).read_text(encoding="utf-8")
        require(len(re.findall(r"\\paragraph\{Solusi\.\}", assessment_text)) == 16, f"{name} bridge source does not contain exactly 16 solutions", errors)
        rendered_solutions = re.findall(rf'id="{re.escape(str(spec["solution_prefix"]))}[^\"]*"[^>]*>Solusi\.</h4>', fragment)
        require(len(rendered_solutions) == 16, f"{name} bridge HTML does not expose exactly 16 complete solutions", errors)
        bridge_qa = load_json(Path(spec["qa"]))
        census = bridge_qa.get("census", {})
        require(census.get("exercise_ids") == 12 and census.get("mastery_problem_ids") == 4 and census.get("solution_bearing_items") == 16, f"{name} bridge QA census differs", errors)
        require(bridge_qa.get("license") == "CC BY-SA 4.0" and exporter.MODEL_IDENTIFICATION in str(bridge_qa.get("provenance", "")), f"{name} bridge rights/provenance differ", errors)
        bridge_solution_items += len(rendered_solutions)
    require(parser.entities["original-bridge"] == 2 and bridge_solution_items == 32, "two bridge surfaces or 32 solution-bearing items differ", errors)
    require("bank-ujian" in ids and parser.entities["assessment-bank"] == 1, "assessment-bank surface is absent or duplicated", errors)

    media_list = manifest.get("media")
    require(isinstance(media_list, list), "media inventory is absent", errors)
    media_by_name = {str(item.get("filename")): item for item in media_list or [] if isinstance(item, dict)}
    require(len(media_by_name) == len(media_list or []), "embedded media filenames are duplicated", errors)
    for filename, item in media_by_name.items():
        source_binding = item.get("source", {})
        try:
            source = safe_path(root, str(source_binding.get("path", "")))
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
        animation = media.get("animation") if isinstance(media.get("animation"), dict) else None
        expected_image = str(animation.get("static_filename")) if animation else filename
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
        source = safe_path(root, str(item.get("source", {}).get("path", "")))
        require(target.is_file() and source.is_file() and target.read_bytes() == source.read_bytes(), f"source-linked animation bytes differ: {filename}", errors)

    css = css_path.read_text(encoding="utf-8")
    css_renderer = exporter.Renderer(root, exporter.v22.load_media_rights(root))
    exporter.render_core(root, css_renderer)
    expected_css = exporter.extended_css(css_renderer)
    require(css == expected_css, "reader CSS differs from the deterministic exporter", errors)
    require("--max:78rem" in css and "width:min(calc(100% - 2rem),var(--max));margin-inline:auto" in css, "centered readable-width contract is absent", errors)
    require("@media(max-width:46rem)" in css and "main{width:100%" in css and "overflow-x:auto" in css, "responsive viewport reflow contract is absent", errors)
    require(".supplement,.assessment-bank{margin:3rem auto" in css and "max-width:88rem" in css, "supplement/assessment centering contract is absent", errors)
    require("prefers-reduced-motion" in css, "reduced-motion accessibility rule is absent", errors)
    verify_animated_surface(root, output, document, css, media_by_name, figure_list, errors)
    readme = readme_path.read_text(encoding="utf-8")
    require("29 unit Brenner" in readme and "dua jembatan asli" in readme and "sepuluh formulir ujian" in readme, "README complete-edition scope differs", errors)

    restage_inventory: list[dict[str, Any]] | None = None
    if restage and not errors:
        with tempfile.TemporaryDirectory(prefix=".verify-html-complete-a-", dir=output.parent) as first_tmp, tempfile.TemporaryDirectory(prefix=".verify-html-complete-b-", dir=output.parent) as second_tmp:
            first, second = Path(first_tmp) / "reader", Path(second_tmp) / "reader"
            first_manifest = exporter.stage_cycle(root, first, contract)
            second_manifest = exporter.stage_cycle(root, second, contract)
            first_inventory, second_inventory = exporter.tree_inventory(first), exporter.tree_inventory(second)
            require(first_manifest == second_manifest, "independent verifier staging manifests differ", errors)
            require(first_inventory == second_inventory, "independent verifier staging trees differ", errors)
            require(first_inventory == exporter.tree_inventory(output), "committed complete reader differs from independent deterministic staging", errors)
            restage_inventory = first_inventory

    if errors:
        raise RuntimeError("complete HTML verification failed:\n- " + "\n- ".join(dict.fromkeys(errors)))
    output_inventory = [exporter.file_binding(path, root) for path in sorted(item for item in output.rglob("*") if item.is_file())]
    return {
        "schema_version": 1,
        "workflow": WORKFLOW,
        "status": "pass",
        "scope": "Complete O011 Indonesian semantic HTML reader",
        "entry": exporter.file_binding(entry_path, root),
        "manifest": exporter.file_binding(manifest_path, root),
        "checks": {
            "exact_29_unit_core_topology": True,
            "unit22_public_reader_baseline_bound": True,
            "ten_exam_forms_147_nominal_123_actual": True,
            "117_source_solutions_and_six_original_repairs": True,
            "two_original_bridges_and_32_solution_bearing_items": True,
            "manifest_input_output_hash_closure": True,
            "strict_balanced_html_and_unique_resolved_fragments": True,
            "mathjax_provenance_license_non_endorsement": True,
            "responsive_centered_reflow_layout": True,
            "media_alt_caption_rights_and_byte_closure": True,
            "two_independent_staging_cycles_match_committed_tree": restage_inventory is not None,
        },
        "counts": {
            "units": 29,
            "input_files": len(expected_inputs),
            "output_files": len(output_inventory),
            "stable_ids": len(ids),
            "core_exercises": len(expected_exercise_ids),
            "core_source_supplied_solutions": len(expected_solution_map),
            "semantic_blocks": expected_semantic_blocks,
            "source_sections": expected_sections,
            "math_elements": parser.math_elements,
            "figures": expected_figures,
            "embedded_media_files": len(media_by_name),
            "source_linked_media_files": len(linked_by_name),
            "exam_forms": 10,
            "exam_nominal_slots": nominal_total,
            "exam_actual_occurrences": actual_total,
            "exam_zero_point_placeholders": placeholder_total,
            "exam_source_supplied_solutions": supplied_total,
            "exam_original_missing_solution_repairs": missing_total,
            "original_bridges": 2,
            "bridge_solution_bearing_items": bridge_solution_items,
        },
        "unit23_29_census": {tag: unit_census[tag] for tag in ("23", "24", "25", "26", "27", "28", "29")},
        "exam_census": {
            "nominal_slots": nominal_total,
            "actual_occurrences": actual_total,
            "zero_point_placeholders": placeholder_total,
            "source_supplied_solutions": supplied_total,
            "original_repairs": missing_total,
        },
        "reproducibility": {
            "cycles": 2,
            "complete_tree_inventory_sha256": exporter.inventory_sha256(exporter.tree_inventory(output)),
            "byte_identical_to_committed_output": restage_inventory is not None,
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
    output = (args.output or root / "output/html/complete").resolve()
    receipt = (args.receipt or root / "qa/complete/HTML_READER_QA.json").resolve()
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
        "exam_census": result["exam_census"],
        "reproducibility": result["reproducibility"],
    }), end="")


if __name__ == "__main__":
    main()
