#!/usr/bin/env python3
"""Strictly verify the cumulative O011 semantic HTML reader through Unit 13."""

from __future__ import annotations

import argparse
import re
import sys
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import unquote

import export_html_v13 as exporter


EXPECTED_MATHJAX_CONFIG = r'''window.MathJax={tex:{inlineMath:[["\\(","\\)"]],displayMath:[["\\[","\\]"]],packages:{"[+]":["ams"]}},options:{enableMenu:true}};'''
from verify_html_animated_media import FigureFragmentParser, figure_fragment
from verify_html_v10 import StrictReaderParser, source_topology


WORKFLOW = "o011-verify-html-v13"


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


class ReaderParser(StrictReaderParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = self._attrs(attrs)
        super().handle_starttag(tag, attrs)
        if tag == "figure" and self.figure_records:
            self.figure_records[-1]["attrs"] = values
        if tag == "a":
            self.links.append(values)


def load_json(path: Path) -> dict[str, Any]:
    return exporter.load_json_object(path)


def output_file_closure(output: Path, manifest: dict[str, Any], errors: list[str]) -> dict[str, dict[str, Any]]:
    declared = manifest.get("files")
    require(isinstance(declared, list), "manifest files inventory is not a list", errors)
    by_path: dict[str, dict[str, Any]] = {}
    if not isinstance(declared, list):
        return by_path
    for item in declared:
        if not isinstance(item, dict) or not isinstance(item.get("path"), str):
            errors.append("malformed file binding in manifest")
            continue
        relative = str(item["path"])
        require(relative not in by_path, f"duplicate manifest path: {relative}", errors)
        by_path[relative] = item
        try:
            path = exporter.safe_project_path(output, relative)
        except RuntimeError as exc:
            errors.append(str(exc))
            continue
        require(path.is_file(), f"manifested output missing: {relative}", errors)
        if path.is_file():
            require(exporter.file_binding(path, output) == item, f"stale output binding: {relative}", errors)
    actual = {
        path.relative_to(output).as_posix()
        for path in output.rglob("*")
        if path.is_file() and path.name != "manifest.json"
    }
    require(actual == set(by_path), "output inventory differs from manifest", errors)
    for required in ("index.html", "assets/reader.css", "README.txt"):
        require(required in by_path, f"manifest does not bind {required}", errors)
    return by_path


def verify_animated_surface(
    root: Path,
    output: Path,
    document: str,
    css: str,
    media: dict[str, dict[str, Any]],
    figures: list[dict[str, Any]],
    errors: list[str],
) -> None:
    animated = [item for item in figures if media.get(str(item.get("filename")), {}).get("animation")]
    require(len(animated) == 1, "reader must contain exactly the admitted Unit 12 embedded animation", errors)
    if len(animated) != 1:
        return
    declared = animated[0]
    figure_id = str(declared.get("id"))
    try:
        fragment = figure_fragment(document, figure_id)
    except RuntimeError as exc:
        errors.append(str(exc))
        return
    parser = FigureFragmentParser()
    parser.feed(fragment)
    parser.close()
    errors.extend(parser.errors)
    require('data-animation-state="stopped"' in fragment, "embedded animation does not start stopped", errors)
    require(len(parser.images) == 1, "embedded animation does not have exactly one image", errors)
    image = parser.images[0] if parser.images else {}
    expected_static = str(declared.get("static_filename"))
    expected_canonical = str(declared.get("filename"))
    require(unquote(image.get("src", "")) == f"assets/media/{expected_static}", "embedded animation initial source is not its static frame", errors)
    require(image.get("data-static-src") == image.get("src"), "embedded animation static source differs from its initial source", errors)
    require(unquote(image.get("data-animated-src", "")) == f"assets/media/{expected_canonical}", "embedded animation Play source is not the canonical GIF", errors)
    require(bool(image.get("alt", "").strip()), "embedded animation has empty alternative text", errors)
    require(image.get("aria-describedby", "") in parser.ids, "embedded animation description target is unresolved", errors)

    buttons = {item["attrs"].get("data-animation-action"): item for item in parser.buttons}
    require(set(buttons) == {"play", "stop"}, "native Play/Stop controls are not both present", errors)
    for action, label in (("play", "Putar animasi"), ("stop", "Hentikan animasi")):
        button = buttons.get(action, {"attrs": {}, "text": ""})
        require(button["attrs"].get("type") == "button", f"{action} control is not a native button", errors)
        require(button["attrs"].get("aria-controls") == image.get("id"), f"{action} control does not target the image", errors)
        require(button["text"] == label, f"{action} control label differs", errors)
        require("tabindex" not in button["attrs"], f"{action} control overrides native keyboard focus", errors)
    require("disabled" not in buttons.get("play", {}).get("attrs", {}), "Play is initially disabled", errors)
    require("disabled" in buttons.get("stop", {}).get("attrs", {}), "Stop is not initially disabled", errors)

    downloads = [item for item in parser.links if "animated-media-download" in item["attrs"].get("class", "").split()]
    require(len(downloads) == 1, "canonical embedded GIF download is absent or duplicated", errors)
    if downloads:
        require(unquote(downloads[0]["attrs"].get("href", "")) == f"assets/media/{expected_canonical}", "embedded GIF download target differs", errors)
        require(downloads[0]["attrs"].get("download") == expected_canonical, "embedded GIF download filename differs", errors)
    require(len(parser.statuses) == 1, "polite animation status is absent or duplicated", errors)
    if parser.statuses:
        require(parser.statuses[0]["attrs"].get("aria-live") == "polite", "animation status is not polite", errors)

    controller_checks = (
        'matchMedia("(prefers-reduced-motion: reduce)")',
        "image.src=playing?image.dataset.animatedSrc:image.dataset.staticSrc",
        "play.disabled=playing;stop.disabled=!playing",
        "if(preference.matches){stop",
        'preference.addEventListener("change",honorPreference)',
    )
    for snippet in controller_checks:
        require(snippet in document, f"animated-media controller contract missing: {snippet}", errors)
    require("prefers-reduced-motion:reduce" in css, "animated controls have no reduced-motion CSS surface", errors)
    require((output / "assets/media" / expected_static).is_file(), "verified static animation frame is missing from output", errors)
    require((output / "assets/media" / expected_canonical).is_file(), "canonical embedded GIF is missing from output", errors)


def verify(root: Path, output: Path, restage: bool = True) -> dict[str, Any]:
    root = root.resolve()
    output = exporter.assert_output_path(root, output)
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
    require(manifest.get("schema_version") == exporter.SCHEMA_VERSION, "unexpected manifest schema version", errors)
    require(manifest.get("workflow") == exporter.WORKFLOW, "unexpected manifest workflow", errors)
    require(manifest.get("status") == "partial_edition", "reader must truthfully remain partial", errors)
    require(manifest.get("language") == "id-ID", "manifest locale is not id-ID", errors)
    require(manifest.get("units") == list(range(1, 14)), "manifest unit sequence is not exactly 1--13", errors)
    require(manifest.get("model_identification") == exporter.MODEL_IDENTIFICATION, "model provenance is absent or changed", errors)
    require(manifest.get("text_license") == "CC BY-SA 4.0", "text license is absent or changed", errors)
    require(manifest.get("non_endorsement") is True, "non-endorsement flag is not true", errors)
    math_meta = manifest.get("math_rendering", {})
    require(math_meta.get("optional_network_dependency") == exporter.MATHJAX_URL, "MathJax dependency disclosure changed", errors)
    require(math_meta.get("offline_fallback") == "visible selectable TeX source", "offline math fallback is not disclosed", errors)

    output_file_closure(output, manifest, errors)
    expected_inputs = [exporter.file_binding(path, root) for path in exporter.source_files(root)]
    require(manifest.get("inputs") == expected_inputs, "reader input bindings are stale or incomplete", errors)
    expected_baseline = exporter.unit10_baseline(root)
    require(manifest.get("unit10_baseline") == expected_baseline, "exact public Unit 10 baseline binding changed", errors)
    expected_qa = exporter.load_live_qa_bindings(root)
    require(manifest.get("unit11_13_live_qa") == expected_qa, "live Unit 11--13 QA/translation bindings changed", errors)
    expected_generation_bindings = exporter.generation_bindings(root)
    require(manifest.get("generation_bindings") == expected_generation_bindings, "media/rights generation bindings changed", errors)
    require(manifest.get("exporter") == exporter.file_binding(Path(exporter.__file__).resolve(), root), "manifest exporter binding is stale", errors)

    html_bytes = entry_path.read_bytes()
    require(html_bytes.startswith(b'<!doctype html>\n<html lang="id-ID">'), "HTML preamble or locale changed", errors)
    require(b"\r" not in html_bytes, "HTML is not canonical LF text", errors)
    document = html_bytes.decode("utf-8")
    parser = ReaderParser()
    parser.feed(document)
    parser.close()
    errors.extend(parser.errors)
    require(parser.html_lang == "id-ID", "HTML root language is not id-ID", errors)
    require(parser.main_count == 1, "HTML must contain exactly one main landmark", errors)
    require(parser.nav_count >= 1, "HTML has no navigation landmark", errors)
    require(parser.heading_counts["h1"] == 1, "HTML must contain exactly one h1", errors)
    require(len(parser.ids) == len(set(parser.ids)), "HTML contains duplicate IDs", errors)
    ids = set(parser.ids)
    for href in parser.hrefs:
        if href.startswith("#"):
            require(href[1:] in ids, f"broken internal fragment: {href}", errors)
    for unit in range(1, 14):
        tag = f"{unit:02d}"
        for required in (f"o011-brenner-u{tag}", f"o011-brenner-u{tag}-l{tag}", f"o011-brenner-u{tag}-w{tag}"):
            require(required in ids, f"missing stable reader anchor: {required}", errors)

    require(len(parser.scripts) == 4, "HTML must contain only MathJax config/loader, deep-link stabilizer, and local animation controller", errors)
    script_srcs = [item.get("src", "") for item in parser.scripts if item.get("src")]
    require(script_srcs == [exporter.MATHJAX_URL], "unexpected or unpinned external script", errors)
    for script_id in ("mathjax-config", "deep-link-stabilizer", "animated-media-controller"):
        require(any(item.get("id") == script_id and not item.get("src") for item in parser.scripts), f"local script is absent: {script_id}", errors)
    require(exporter.MATHJAX_CONFIG == EXPECTED_MATHJAX_CONFIG, "exporter MathJax configuration differs from the independently pinned runtime contract", errors)
    require(
        f'<script id="mathjax-config">{EXPECTED_MATHJAX_CONFIG}</script>' in document,
        "MathJax configuration or JavaScript-escaped TeX delimiters differ",
        errors,
    )
    require('addEventListener("hashchange",settle)' in document and "setTimeout(align,3000)" in document, "deep-link stabilizer does not cover hash changes and delayed layout settlement", errors)

    require(parser.math_elements > 0, "HTML contains no marked mathematical content", errors)
    for value in parser.math_text:
        stripped = value.strip()
        if stripped:
            require(
                (stripped.startswith(r"\(") and stripped.endswith(r"\)"))
                or (stripped.startswith(r"\[") and stripped.endswith(r"\]")),
                "math element lacks compatible TeX delimiters",
                errors,
            )
    outside = "".join(parser.outside_math)
    prohibited = re.compile(r"__NOEDITSECTION__|\[\[|\\(?:input|definitions|zwischenueberschrift|mavergleich|vergleichskette|maabb|bild|aufzaehlung|fakt|mathl|mathbed|mathkor|zusatz)")
    require(prohibited.search(outside) is None, "unconverted source macro or MediaWiki residue leaked into reader prose", errors)
    require("---" not in outside, "raw TeX em-dash punctuation remains in reader prose", errors)
    require("Kategorie:Latexseite" not in outside and "Category:Latexseite" not in outside, "MediaWiki category metadata is visible", errors)
    require("Konstruktion der Objekte" not in outside and "Variation von S" not in outside, "German source-linked animation labels remain visible", errors)
    require(all("lang" not in link for link in parser.source_links), "source link applies a foreign language tag to its translated label", errors)
    require("TTP" not in document and "Translation and Transcription Project" not in document, "prohibited umbrella branding leaked into metadata", errors)
    require(exporter.MODEL_IDENTIFICATION in outside, "exact model provenance note missing", errors)
    require("CC BY-SA 4.0" in outside, "visible text-license statement missing", errors)
    require("bukan edisi resmi" in outside, "visible non-endorsement statement missing", errors)
    require("dependensi opsional" in outside and "sumber TeX" in outside, "offline/MathJax limitation disclosure missing", errors)

    topology = manifest.get("topology")
    require(isinstance(topology, dict), "manifest topology is absent", errors)
    expected_exercise_ids: set[str] = set()
    expected_solution_map: dict[str, str] = {}
    expected_source_sections = 0
    expected_figures = 0
    expected_semantic_blocks = 0
    for unit in range(1, 14):
        tag = f"{unit:02d}"
        lecture_path = root / f"source/units/unit-{tag}/lecture{tag}.id.tex"
        worksheet_path = root / f"source/units/unit-{tag}/worksheet{tag}.id.tex"
        lecture = source_topology(lecture_path, "lecture")
        worksheet = source_topology(worksheet_path, "worksheet")
        indices = exporter.solution_indices(root, unit)
        expected = topology.get(tag, {}) if isinstance(topology, dict) else {}
        require(expected.get("lecture", {}).get("source_sections") == lecture["source_sections"], f"Unit {unit} lecture section topology changed", errors)
        require(expected.get("lecture", {}).get("semantic_blocks") == lecture["semantic_blocks"], f"Unit {unit} lecture semantic topology changed", errors)
        require(expected.get("lecture", {}).get("figures") == lecture["figures"], f"Unit {unit} lecture figure topology changed", errors)
        require(expected.get("worksheet", {}).get("source_sections") == worksheet["source_sections"], f"Unit {unit} worksheet section topology changed", errors)
        require(expected.get("worksheet", {}).get("exercises") == worksheet["exercises"], f"Unit {unit} exercise topology changed", errors)
        require(expected.get("worksheet", {}).get("figures") == worksheet["figures"], f"Unit {unit} worksheet figure topology changed", errors)
        require(expected.get("source_supplied_solution_indices") == indices, f"Unit {unit} solution topology changed", errors)
        require(worksheet["source_solution_markers"] == indices, f"Unit {unit} source solution markers/files differ", errors)
        expected_source_sections += lecture["source_sections"] + worksheet["source_sections"]
        expected_figures += lecture["figures"] + worksheet["figures"]
        expected_semantic_blocks += lecture["semantic_blocks"]
        for index in range(1, worksheet["exercises"] + 1):
            expected_exercise_ids.add(f"o011-brenner-u{tag}-w{tag}-e{index:03d}")
        for index in indices:
            exercise_id = f"o011-brenner-u{tag}-w{tag}-e{index:03d}"
            solution_id = exercise_id + "-solution"
            expected_solution_map[solution_id] = exercise_id
            solution_path = root / f"source/units/unit-{tag}/worksheet{tag}_exercise{index:02d}_solution.id.tex"
            expected_source_sections += source_topology(solution_path, "lecture")["source_sections"]

    actual_exercise_ids = {
        item["id"] for item in parser.entity_attrs
        if item.get("data-entity") == "exercise" and item.get("id")
    }
    actual_solution_map = {
        item["id"]: item.get("data-solves", "") for item in parser.entity_attrs
        if item.get("data-entity") == "source-supplied-solution" and item.get("id")
    }
    require(actual_exercise_ids == expected_exercise_ids, "stable exercise-anchor closure failed", errors)
    require(actual_solution_map == expected_solution_map, "stable source-solution/data-solves closure failed", errors)
    require(parser.entities["source-section"] == expected_source_sections, "source-section count differs from TeX", errors)
    require(parser.entities["figure"] == expected_figures, "figure count differs from TeX", errors)
    actual_semantic_blocks = sum(parser.entities[name] for name in (
        "inputdefinition", "inputaxiom", "inputnotation", "inputbeispiel", "inputbemerkung",
        "inputverfahren", "inputkonstruktion", "inputfrage", "inputproblem", "inputsituation",
        "inputfakt", "inputfaktbeweis", "inputfaktbeweisnichtvorgefuehrt", "inputfaktbeweistrivial",
        "inputfaktuebergangbeweis",
    ))
    require(actual_semantic_blocks == expected_semantic_blocks, "lecture semantic-block count differs from TeX", errors)

    media_list = manifest.get("media")
    require(isinstance(media_list, list), "manifest media inventory is not a list", errors)
    media_by_name = {
        str(item.get("filename")): item for item in media_list or [] if isinstance(item, dict)
    }
    require(len(media_by_name) == len(media_list or []), "embedded media filenames are duplicated", errors)
    for filename, item in media_by_name.items():
        source_binding = item.get("source", {})
        try:
            source = exporter.safe_project_path(root, str(source_binding.get("path", "")))
        except RuntimeError as exc:
            errors.append(str(exc))
            continue
        require(source.is_file() and exporter.file_binding(source, root) == source_binding, f"embedded media source binding changed: {filename}", errors)
        target = output / "assets/media" / filename
        require(target.is_file(), f"embedded media output is missing: {filename}", errors)
        if target.is_file():
            require(target.read_bytes() == source.read_bytes(), f"embedded media output bytes differ: {filename}", errors)
        require(bool(str(item.get("creator") or "").strip()), f"embedded media creator is absent: {filename}", errors)
        require(bool(str(item.get("license") or "").strip()), f"embedded media license is absent: {filename}", errors)
        require(bool(item.get("unit_media_receipts")), f"unit media receipt binding is absent: {filename}", errors)

    figures = manifest.get("figures")
    require(isinstance(figures, list), "figure occurrence manifest is absent", errors)
    figure_list = figures if isinstance(figures, list) else []
    require(len(figure_list) == len(parser.figure_records), "figure occurrence manifest/HTML count differs", errors)
    require(parser.figure_count == len(parser.images) == len(figure_list), "each figure must contain exactly one image", errors)
    for declared, actual in zip(figure_list, parser.figure_records):
        filename = str(declared.get("filename"))
        media_item = media_by_name.get(filename, {})
        image = actual.get("image") or {}
        caption = " ".join("".join(actual.get("caption_parts", [])).split())
        require(actual.get("id") == declared.get("id"), f"figure stable ID changed: {declared.get('id')}", errors)
        require(image.get("alt") == declared.get("alt"), f"figure alt text changed: {declared.get('id')}", errors)
        animation = media_item.get("animation")
        expected_image = str(animation.get("static_filename")) if isinstance(animation, dict) else filename
        require(unquote(str(image.get("src", ""))) == f"assets/media/{expected_image}", f"figure image target changed: {declared.get('id')}", errors)
        if declared.get("caption_supplied"):
            expected_caption = " ".join(str(declared.get("caption_text") or "").split())
            require(bool(expected_caption) and expected_caption in caption, f"supplied figure caption is not visible: {declared.get('id')}", errors)
            require(image.get("alt") == expected_caption, f"supplied caption was not used as alt text: {declared.get('id')}", errors)
        for value, label in ((media_item.get("creator"), "creator"), (media_item.get("license"), "license")):
            require(str(value or "") in caption, f"figure {label} is not visible: {declared.get('id')}", errors)

    linked_list = manifest.get("source_linked_media")
    require(isinstance(linked_list, list), "source-linked media inventory is absent", errors)
    linked_by_name = {
        str(item.get("filename")): item for item in linked_list or [] if isinstance(item, dict)
    }
    expected_linked_names = {"Aufgabe75.22.1.gif", "Aufgabe75.22.2.gif", "Aufgabe79.27.gif"}
    require(set(linked_by_name) == expected_linked_names, "source-linked animation inventory differs", errors)
    linked_links = [item for item in parser.links if "source-linked-animation-download" in item.get("class", "").split()]
    require(len(linked_links) == len(expected_linked_names), "source-linked animation downloads are absent or duplicated", errors)
    link_by_filename = {unquote(str(item.get("href", ""))).removeprefix("assets/media/"): item for item in linked_links}
    require(set(link_by_filename) == expected_linked_names, "source-linked animation href closure differs", errors)
    for filename, item in linked_by_name.items():
        source = exporter.safe_project_path(root, str(item.get("source", {}).get("path", "")))
        require(source.is_file() and exporter.file_binding(source, root) == item.get("source"), f"source-linked media source changed: {filename}", errors)
        target = output / "assets/media" / filename
        require(target.is_file(), f"source-linked media output is missing: {filename}", errors)
        if source.is_file() and target.is_file():
            require(target.read_bytes() == source.read_bytes(), f"source-linked media output bytes differ: {filename}", errors)
        link = link_by_filename.get(filename, {})
        require(link.get("download") == filename, f"source-linked media download filename differs: {filename}", errors)
        require(str(item.get("description") or "") in str(link.get("aria-label") or ""), f"source-linked media accessible label differs: {filename}", errors)
        require(str(item.get("creator") or "") in outside and str(item.get("license") or "") in outside, f"source-linked media rights are not visible: {filename}", errors)
    linked_occurrences = manifest.get("source_linked_media_occurrences")
    require(isinstance(linked_occurrences, list) and len(linked_occurrences) == 3, "source-linked media occurrence closure differs", errors)
    if isinstance(linked_occurrences, list):
        for item in linked_occurrences:
            require(item.get("id") in ids, f"source-linked media stable ID is missing: {item.get('id')}", errors)
    require(parser.entities["source-linked-animation"] == 3, "source-linked animation entity count differs", errors)

    css = css_path.read_text(encoding="utf-8")
    require("--max:78rem" in css and "width:min(calc(100% - 2rem),var(--max))" in css, "centered max-width layout contract missing", errors)
    require("@media(max-width:46rem)" in css and "main{width:100%" in css, "responsive full-viewport layout contract missing", errors)
    require("overflow-x:auto" in css, "wide mathematics has no horizontal reflow fallback", errors)
    require("prefers-reduced-motion" in css, "reduced-motion accessibility rule missing", errors)
    require("source-linked-animation" in css, "source-linked media reflow styling missing", errors)
    readme = readme_path.read_text(encoding="utf-8")
    require("hingga Unit 13" in readme and "Putar animasi" in readme and "papan ketik" in readme, "README scope/animation accessibility disclosure missing", errors)

    verify_animated_surface(root, output, document, css, media_by_name, figure_list, errors)

    excluded = manifest.get("excluded_reader_metadata", {})
    category_count = sum(path.read_text(encoding="utf-8").count("[[Kategorie:Latexseite]]") for path in exporter.source_files(root))
    require(excluded.get("mediawiki_category_marker") == "[[Kategorie:Latexseite]]", "excluded category marker is undocumented", errors)
    require(excluded.get("occurrences") == category_count, "excluded category-marker count is stale", errors)
    require("source inputs" in str(excluded.get("preservation", "")), "category-marker provenance preservation is undocumented", errors)

    payload_inventory = [
        exporter.file_binding(path, output)
        for path in sorted(item for item in output.rglob("*") if item.is_file() and item.name != "manifest.json")
    ]
    reproducibility = manifest.get("reproducibility", {})
    require(reproducibility.get("staging_cycles") == 2, "manifest does not require exactly two staging cycles", errors)
    require(reproducibility.get("byte_identical_before_commit") is True, "manifest does not attest byte-identical pre-commit staging", errors)
    require(reproducibility.get("payload_inventory_sha256") == exporter.inventory_sha256(payload_inventory), "payload reproducibility digest differs", errors)

    restage_inventory: list[dict[str, Any]] | None = None
    if restage and not errors:
        contract = exporter.generation_contract(root)
        with tempfile.TemporaryDirectory(prefix=".verify-html-v13-a-", dir=output.parent) as first_tmp, tempfile.TemporaryDirectory(prefix=".verify-html-v13-b-", dir=output.parent) as second_tmp:
            first = Path(first_tmp) / "reader"
            second = Path(second_tmp) / "reader"
            exporter._stage_cycle(root, first, contract)
            exporter._stage_cycle(root, second, contract)
            first_inventory = exporter.tree_inventory(first)
            second_inventory = exporter.tree_inventory(second)
            committed_inventory = exporter.tree_inventory(output)
            require(first_inventory == second_inventory, "independent verifier staging cycles differ", errors)
            require(first_inventory == committed_inventory, "committed reader differs from independent deterministic staging", errors)
            restage_inventory = first_inventory

    if errors:
        raise RuntimeError("HTML v13 verification failed:\n- " + "\n- ".join(dict.fromkeys(errors)))

    output_inventory = [
        exporter.file_binding(path, root)
        for path in sorted(item for item in output.rglob("*") if item.is_file())
    ]
    return {
        "schema_version": 1,
        "workflow": WORKFLOW,
        "status": "pass",
        "scope": "Cumulative Indonesian semantic HTML reader through Unit 13",
        "entry": exporter.file_binding(entry_path, root),
        "manifest": exporter.file_binding(manifest_path, root),
        "checks": {
            "exact_published_unit10_baseline_unchanged": True,
            "live_unit11_13_post_qa_and_translation_receipts": True,
            "manifest_and_file_hash_closure": True,
            "strict_html_tag_balance": True,
            "unique_and_resolved_stable_deep_links": True,
            "unit_lecture_worksheet_topology": True,
            "exact_source_supplied_solution_topology": True,
            "semantic_block_topology": True,
            "mathjax_compatible_tex_and_honest_offline_fallback": True,
            "local_media_alt_caption_attribution_rights_closure": True,
            "static_first_keyboard_play_stop_download": True,
            "prefers_reduced_motion_prevents_and_stops_animation": True,
            "source_linked_animations_preserved_as_keyboard_downloads": True,
            "responsive_reflowable_reader_layout": True,
            "license_provenance_non_endorsement": True,
            "no_unconverted_source_macro_or_file_link_residue": True,
            "two_independent_staging_cycles_match_committed_tree": restage_inventory is not None,
        },
        "counts": {
            "units": 13,
            "input_files": len(expected_inputs),
            "output_files": len(output_inventory),
            "stable_ids": len(ids),
            "exercises": len(expected_exercise_ids),
            "source_supplied_solutions": len(expected_solution_map),
            "semantic_blocks": expected_semantic_blocks,
            "source_sections": expected_source_sections,
            "math_elements": parser.math_elements,
            "figures": expected_figures,
            "embedded_media_files": len(media_by_name),
            "source_linked_media_files": len(linked_by_name),
        },
        "reproducibility": {
            "cycles": 2,
            "complete_tree_inventory_sha256": exporter.inventory_sha256(exporter.tree_inventory(output)),
            "byte_identical_to_committed_output": restage_inventory is not None,
        },
        "unit10_baseline": {
            "status": expected_baseline["status"],
            "output_inventory_sha256": expected_baseline["output_inventory_sha256"],
            "published_html_zip": expected_baseline["published_html_zip"],
            "public_readback": expected_baseline["public_readback"],
        },
        "unit11_13_live_qa": expected_qa,
        "output_inventory": output_inventory,
        "verifier": exporter.file_binding(Path(__file__).resolve(), root),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--receipt", type=Path, default=None)
    parser.add_argument("--skip-restage", action="store_true", help="skip the independent two-cycle reconstruction (not suitable for final QA)")
    args = parser.parse_args()
    root = args.root.resolve()
    output = (args.output or (root / "output/html/unit-13")).resolve()
    receipt = (args.receipt or (root / "qa/unit-13/HTML_READER_QA.json")).resolve()
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
        "reproducibility": result["reproducibility"],
    }), end="")


if __name__ == "__main__":
    main()
