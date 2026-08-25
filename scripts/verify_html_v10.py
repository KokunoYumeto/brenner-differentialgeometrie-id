#!/usr/bin/env python3
"""Strictly verify the cumulative O011 semantic HTML reader through Unit 10."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import unquote

from export_html_v10 import (
    MATHJAX_URL,
    MODEL_IDENTIFICATION,
    WORKFLOW,
    canonical_json,
    file_binding,
    sha256_bytes,
    source_files,
    write_text,
)


VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}


class StrictReaderParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[tuple[str, set[str]]] = []
        self.errors: list[str] = []
        self.ids: list[str] = []
        self.hrefs: list[str] = []
        self.images: list[dict[str, str]] = []
        self.source_links: list[dict[str, str]] = []
        self.figure_records: list[dict[str, Any]] = []
        self.active_figure: dict[str, Any] | None = None
        self.in_figcaption = False
        self.scripts: list[dict[str, str]] = []
        self.entities: Counter[str] = Counter()
        self.entity_attrs: list[dict[str, str]] = []
        self.outside_math: list[str] = []
        self.math_text: list[str] = []
        self.math_elements = 0
        self.html_lang: str | None = None
        self.main_count = 0
        self.nav_count = 0
        self.figure_count = 0
        self.figcaption_count = 0
        self.heading_counts: Counter[str] = Counter()

    def _attrs(self, attrs: list[tuple[str, str | None]]) -> dict[str, str]:
        return {str(k): str(v or "") for k, v in attrs}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = self._attrs(attrs)
        classes = set(values.get("class", "").split())
        if tag == "html":
            self.html_lang = values.get("lang")
        if tag == "main":
            self.main_count += 1
        if tag == "nav":
            self.nav_count += 1
        if tag == "figure":
            self.figure_count += 1
            self.active_figure = {"id": values.get("id"), "image": None, "caption_parts": []}
            self.figure_records.append(self.active_figure)
        if tag == "figcaption":
            self.figcaption_count += 1
            self.in_figcaption = True
        if re.fullmatch(r"h[1-6]", tag):
            self.heading_counts[tag] += 1
        if "id" in values:
            self.ids.append(values["id"])
        if "href" in values:
            self.hrefs.append(values["href"])
        if tag == "img":
            self.images.append(values)
            if self.active_figure is not None:
                self.active_figure["image"] = values
        if tag == "a" and "source-link" in classes:
            self.source_links.append(values)
        if tag == "script":
            self.scripts.append(values)
        if "data-entity" in values:
            self.entities[values["data-entity"]] += 1
            self.entity_attrs.append(values)
        if "math" in classes:
            self.math_elements += 1
        for key, value in values.items():
            if key.casefold().startswith("on"):
                self.errors.append(f"inline event handler is prohibited: {key}")
            if value.casefold().strip().startswith("javascript:"):
                self.errors.append(f"javascript URL is prohibited: {key}")
        if tag not in VOID_TAGS:
            self.stack.append((tag, classes))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        if tag not in VOID_TAGS:
            self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        if tag == "figcaption":
            self.in_figcaption = False
        if tag == "figure":
            self.active_figure = None
        if not self.stack:
            self.errors.append(f"unexpected closing tag: {tag}")
            return
        open_tag, _ = self.stack[-1]
        if open_tag != tag:
            self.errors.append(f"misnested tag: expected </{open_tag}>, found </{tag}>")
            for i in range(len(self.stack) - 1, -1, -1):
                if self.stack[i][0] == tag:
                    del self.stack[i:]
                    return
            return
        self.stack.pop()

    def handle_data(self, data: str) -> None:
        if any(tag in ("script", "style") for tag, _ in self.stack):
            return
        if self.in_figcaption and self.active_figure is not None:
            self.active_figure["caption_parts"].append(data)
        in_math = any("math" in classes for _, classes in self.stack)
        (self.math_text if in_math else self.outside_math).append(data)

    def close(self) -> None:
        super().close()
        if self.stack:
            self.errors.append("unclosed tags: " + ", ".join(tag for tag, _ in self.stack[-10:]))


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def safe_path(root: Path, relative: str) -> Path:
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise RuntimeError(f"path escapes root: {relative}") from exc
    return candidate


def source_topology(path: Path, surface: str) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    value: dict[str, Any] = {
        "source_sections": len(re.findall(r"\\zwischenueberschrift\s*\{", text)),
        "figures": len(re.findall(r"\\bild\s*\{", text)),
    }
    if surface == "lecture":
        value["semantic_blocks"] = len(re.findall(
            r"\\(?:inputdefinition|inputaxiom|inputnotation|inputbeispiel|inputbemerkung|inputverfahren|inputkonstruktion|inputfrage|inputproblem|inputsituation|inputfakt(?:beweis|beweisnichtvorgefuehrt|beweistrivial|uebergangbeweis)?)\b",
            text,
        ))
    else:
        exercises = list(re.finditer(r"\\(inputaufgabe(?:gibtloesung)?)\b", text))
        value["exercises"] = len(exercises)
        value["source_solution_markers"] = [i for i, match in enumerate(exercises, 1) if match.group(1) == "inputaufgabegibtloesung"]
    return value


def verify(root: Path, output: Path) -> dict[str, Any]:
    root = root.resolve()
    output = output.resolve()
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
    require(manifest.get("schema_version") == 1, "unexpected manifest schema version", errors)
    require(manifest.get("workflow") == WORKFLOW, "unexpected manifest workflow", errors)
    require(manifest.get("status") == "partial_edition", "reader must truthfully remain partial", errors)
    require(manifest.get("language") == "id-ID", "manifest locale is not id-ID", errors)
    require(manifest.get("units") == list(range(1, 11)), "manifest unit sequence is not exactly 1--10", errors)
    require(manifest.get("model_identification") == MODEL_IDENTIFICATION, "model provenance is absent or changed", errors)
    require(manifest.get("text_license") == "CC BY-SA 4.0", "text license is absent or changed", errors)
    require(manifest.get("non_endorsement") is True, "non-endorsement flag is not true", errors)
    math_meta = manifest.get("math_rendering", {})
    require(math_meta.get("optional_network_dependency") == MATHJAX_URL, "MathJax dependency disclosure changed", errors)
    require(math_meta.get("offline_fallback") == "visible selectable TeX source", "offline math fallback is not disclosed", errors)

    declared_files = manifest.get("files")
    require(isinstance(declared_files, list), "manifest files inventory is not a list", errors)
    declared_by_path: dict[str, dict[str, Any]] = {}
    if isinstance(declared_files, list):
        for item in declared_files:
            if not isinstance(item, dict) or not isinstance(item.get("path"), str):
                errors.append("malformed file binding in manifest")
                continue
            relative = item["path"]
            require(relative not in declared_by_path, f"duplicate manifest path: {relative}", errors)
            declared_by_path[relative] = item
            path = safe_path(output, relative)
            require(path.is_file(), f"manifested output missing: {relative}", errors)
            if path.is_file():
                actual = file_binding(path, output)
                require(actual == item, f"stale output binding: {relative}", errors)
    actual_files = {
        path.relative_to(output).as_posix()
        for path in output.rglob("*") if path.is_file() and path.name != "manifest.json"
    }
    require(actual_files == set(declared_by_path), "output inventory differs from manifest", errors)
    require("index.html" in declared_by_path, "manifest does not bind index.html", errors)

    expected_inputs = [file_binding(path, root) for path in source_files(root)]
    require(manifest.get("inputs") == expected_inputs, "reader input bindings are stale or incomplete", errors)

    html_bytes = entry_path.read_bytes()
    require(html_bytes.startswith(b"<!doctype html>\n<html lang=\"id-ID\">"), "HTML preamble or locale changed", errors)
    require(b"\r" not in html_bytes, "HTML is not canonical LF text", errors)
    document = html_bytes.decode("utf-8")
    parser = StrictReaderParser()
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
    for unit in range(1, 11):
        tag = f"{unit:02d}"
        for required in (
            f"o011-brenner-u{tag}",
            f"o011-brenner-u{tag}-l{tag}",
            f"o011-brenner-u{tag}-w{tag}",
        ):
            require(required in ids, f"missing stable reader anchor: {required}", errors)

    require(len(parser.scripts) == 3, "HTML must contain only MathJax configuration, its pinned loader, and the local deep-link stabilizer", errors)
    script_srcs = [item.get("src", "") for item in parser.scripts if item.get("src")]
    require(script_srcs == [MATHJAX_URL], "unexpected or unpinned external script", errors)
    require(any(item.get("id") == "mathjax-config" and not item.get("src") for item in parser.scripts), "MathJax configuration is absent", errors)
    require(any(item.get("id") == "deep-link-stabilizer" and not item.get("src") for item in parser.scripts), "local deep-link stabilizer is absent", errors)
    require('addEventListener("hashchange",settle)' in document and "setTimeout(align,3000)" in document, "deep-link stabilizer does not cover hash changes and delayed layout settlement", errors)
    require(parser.math_elements > 0, "HTML contains no marked mathematical content", errors)
    for value in parser.math_text:
        stripped = value.strip()
        if stripped:
            require((stripped.startswith(r"\(") and stripped.endswith(r"\)")) or (stripped.startswith(r"\[") and stripped.endswith(r"\]")), "math element lacks compatible TeX delimiters", errors)

    outside = "".join(parser.outside_math)
    prohibited_residue = re.compile(r"__NOEDITSECTION__|\[\[|\\(?:input|definitions|zwischenueberschrift|mavergleich|vergleichskette|maabb|bild|aufzaehlung|fakt|mathl|mathbed|mathkor|zusatz)")
    require(prohibited_residue.search(outside) is None, "unconverted source macro or MediaWiki residue leaked into reader prose", errors)
    require("---" not in outside, "raw TeX em-dash punctuation remains in reader prose", errors)
    require("Kategorie:Latexseite" not in outside and "Category:Latexseite" not in outside, "MediaWiki category metadata is visible in reader prose", errors)
    require(all("lang" not in link for link in parser.source_links), "source link applies a foreign language tag to its translated visible label", errors)
    require("TTP" not in document and "Translation and Transcription Project" not in document, "prohibited umbrella branding leaked into work metadata", errors)
    require(MODEL_IDENTIFICATION in outside, "exact model provenance note missing from visible reader", errors)
    require("CC BY-SA 4.0" in outside, "visible text-license statement missing", errors)
    require("bukan edisi resmi" in outside, "visible non-endorsement statement missing", errors)
    require("dependensi opsional" in outside and "sumber TeX" in outside, "offline/MathJax limitation disclosure missing", errors)

    media = manifest.get("media")
    require(isinstance(media, list), "manifest media inventory is not a list", errors)
    media_names = {str(item.get("filename")) for item in media} if isinstance(media, list) else set()
    require(len(parser.images) == len(media_names), "image occurrence/unique-media closure changed", errors)
    require(parser.figure_count == len(parser.images), "each image must be enclosed by exactly one figure", errors)
    require(parser.figcaption_count == len(parser.images), "each image must have a figcaption", errors)
    image_names: set[str] = set()
    for image in parser.images:
        source = image.get("src", "")
        require(source.startswith("assets/media/"), f"image is not local/offline: {source}", errors)
        require(bool(image.get("alt", "").strip()), f"image has empty alt text: {source}", errors)
        filename = unquote(source.removeprefix("assets/media/"))
        image_names.add(filename)
        require(filename in media_names, f"image absent from rights manifest: {filename}", errors)
        require((output / "assets/media" / filename).is_file(), f"local image bytes missing: {filename}", errors)
    require(image_names == media_names, "HTML/media manifest filenames differ", errors)
    figure_manifest = manifest.get("figures")
    require(isinstance(figure_manifest, list), "figure occurrence manifest is absent", errors)
    if isinstance(figure_manifest, list):
        require(len(figure_manifest) == len(parser.figure_records), "figure occurrence manifest/HTML count differs", errors)
        for declared, actual in zip(figure_manifest, parser.figure_records):
            actual_image = actual.get("image") or {}
            actual_caption = " ".join("".join(actual.get("caption_parts", [])).split())
            require(actual.get("id") == declared.get("id"), f"figure stable ID changed: {declared.get('id')}", errors)
            require(unquote(str(actual_image.get("src", ""))).endswith(str(declared.get("filename", ""))), f"figure media changed: {declared.get('id')}", errors)
            require(actual_image.get("alt") == declared.get("alt"), f"figure alt text changed: {declared.get('id')}", errors)
            if declared.get("caption_supplied"):
                expected_caption = " ".join(str(declared.get("caption_text", "")).split())
                require(bool(expected_caption), f"supplied figure caption became empty: {declared.get('id')}", errors)
                require(expected_caption in actual_caption, f"supplied figure caption is not visible: {declared.get('id')}", errors)
                require(actual_image.get("alt") == expected_caption, f"supplied figure caption was not used as alt text: {declared.get('id')}", errors)

    excluded = manifest.get("excluded_reader_metadata", {})
    actual_category_count = sum(
        path.read_text(encoding="utf-8").count("[[Kategorie:Latexseite]]")
        for path in source_files(root)
    )
    require(excluded.get("mediawiki_category_marker") == "[[Kategorie:Latexseite]]", "excluded category marker is undocumented", errors)
    require(excluded.get("occurrences") == actual_category_count, "excluded category-marker count is stale", errors)
    require("source inputs" in str(excluded.get("preservation", "")), "category-marker provenance preservation is undocumented", errors)

    topology = manifest.get("topology")
    require(isinstance(topology, dict), "manifest topology is absent", errors)
    expected_exercise_ids: set[str] = set()
    expected_solution_ids: set[str] = set()
    expected_source_sections = 0
    expected_figures = 0
    expected_semantic_blocks = 0
    for unit in range(1, 11):
        tag = f"{unit:02d}"
        lecture_path = root / f"source/units/unit-{tag}/lecture{tag}.id.tex"
        worksheet_path = root / f"source/units/unit-{tag}/worksheet{tag}.id.tex"
        lecture = source_topology(lecture_path, "lecture")
        worksheet = source_topology(worksheet_path, "worksheet")
        solution_indices = sorted(
            int(match.group(1))
            for path in (root / f"source/units/unit-{tag}").glob(f"worksheet{tag}_exercise*_solution.id.tex")
            if (match := re.search(r"exercise(\d+)_solution", path.name))
        )
        expected = topology.get(tag, {}) if isinstance(topology, dict) else {}
        require(expected.get("lecture", {}).get("source_sections") == lecture["source_sections"], f"Unit {unit} lecture section topology changed", errors)
        require(expected.get("lecture", {}).get("semantic_blocks") == lecture["semantic_blocks"], f"Unit {unit} lecture semantic-block topology changed", errors)
        require(expected.get("lecture", {}).get("figures") == lecture["figures"], f"Unit {unit} lecture figure topology changed", errors)
        require(expected.get("worksheet", {}).get("source_sections") == worksheet["source_sections"], f"Unit {unit} worksheet section topology changed", errors)
        require(expected.get("worksheet", {}).get("exercises") == worksheet["exercises"], f"Unit {unit} exercise topology changed", errors)
        require(expected.get("worksheet", {}).get("figures") == worksheet["figures"], f"Unit {unit} worksheet figure topology changed", errors)
        require(expected.get("source_supplied_solution_indices") == solution_indices, f"Unit {unit} solution-file topology changed", errors)
        require(worksheet["source_solution_markers"] == solution_indices, f"Unit {unit} source solution markers do not match translated solution files", errors)
        expected_source_sections += lecture["source_sections"] + worksheet["source_sections"]
        expected_figures += lecture["figures"] + worksheet["figures"]
        expected_semantic_blocks += lecture["semantic_blocks"]
        for index in range(1, worksheet["exercises"] + 1):
            expected_exercise_ids.add(f"o011-brenner-u{tag}-w{tag}-e{index:03d}")
        for index in solution_indices:
            expected_solution_ids.add(f"o011-brenner-u{tag}-w{tag}-e{index:03d}-solution")
            solution_path = root / f"source/units/unit-{tag}/worksheet{tag}_exercise{index:02d}_solution.id.tex"
            expected_source_sections += source_topology(solution_path, "lecture")["source_sections"]
    actual_exercise_ids = {
        item["id"] for item in parser.entity_attrs
        if item.get("data-entity") == "exercise" and item.get("id")
    }
    actual_solution_ids = {
        item["id"] for item in parser.entity_attrs
        if item.get("data-entity") == "source-supplied-solution" and item.get("id")
    }
    require(actual_exercise_ids == expected_exercise_ids, "stable exercise-anchor closure failed", errors)
    require(actual_solution_ids == expected_solution_ids, "stable source-solution-anchor closure failed", errors)
    require(parser.entities["source-section"] == expected_source_sections, "source-section count differs from TeX", errors)
    require(parser.entities["figure"] == expected_figures, "figure count differs from TeX", errors)
    actual_semantic_blocks = sum(parser.entities[name] for name in (
        "inputdefinition", "inputaxiom", "inputnotation", "inputbeispiel", "inputbemerkung",
        "inputverfahren", "inputkonstruktion", "inputfrage", "inputproblem", "inputsituation",
        "inputfakt", "inputfaktbeweis", "inputfaktbeweisnichtvorgefuehrt", "inputfaktbeweistrivial",
        "inputfaktuebergangbeweis",
    ))
    require(actual_semantic_blocks == expected_semantic_blocks, "lecture semantic-block count differs from TeX", errors)

    css = css_path.read_text(encoding="utf-8")
    require("--max:78rem" in css and "width:min(calc(100% - 2rem),var(--max))" in css, "centered max-width layout contract missing", errors)
    require("@media(max-width:46rem)" in css and "main{width:100%" in css, "responsive full-viewport layout contract missing", errors)
    require("prefers-reduced-motion" in css, "reduced-motion accessibility rule missing", errors)

    if errors:
        raise RuntimeError("HTML verification failed:\n- " + "\n- ".join(dict.fromkeys(errors)))

    entry_binding = file_binding(entry_path, root)
    manifest_binding = file_binding(manifest_path, root)
    output_inventory = [
        file_binding(path, root)
        for path in sorted(p for p in output.rglob("*") if p.is_file())
    ]
    return {
        "schema_version": 1,
        "workflow": "o011-verify-html-v10",
        "status": "pass",
        "scope": "Cumulative Indonesian semantic HTML reader through Unit 10",
        "entry": entry_binding,
        "manifest": manifest_binding,
        "checks": {
            "manifest_and_file_hash_closure": True,
            "current_input_hash_closure": True,
            "strict_html_tag_balance": True,
            "unique_and_resolved_stable_anchors": True,
            "unit_lecture_worksheet_topology": True,
            "exercise_and_source_solution_topology": True,
            "semantic_block_topology": True,
            "mathjax_compatible_tex_and_honest_offline_fallback": True,
            "local_media_alt_caption_rights_closure": True,
            "responsive_centered_reader_layout": True,
            "license_provenance_non_endorsement": True,
            "no_unconverted_source_macro_residue": True,
            "no_invented_interactivity": True,
        },
        "counts": {
            "units": 10,
            "input_files": len(expected_inputs),
            "output_files": len(output_inventory),
            "stable_ids": len(ids),
            "exercises": len(expected_exercise_ids),
            "source_supplied_solutions": len(expected_solution_ids),
            "semantic_blocks": expected_semantic_blocks,
            "source_sections": expected_source_sections,
            "math_elements": parser.math_elements,
            "figures": expected_figures,
            "media_files": len(media_names),
        },
        "math_rendering_limitation": {
            "optional_dependency": MATHJAX_URL,
            "offline_behavior": "TeX source remains visible/selectable; typographic rendering requires the disclosed optional network dependency.",
        },
        "output_inventory": output_inventory,
        "verifier": file_binding(Path(__file__).resolve(), root),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--receipt", type=Path, default=None)
    args = parser.parse_args()
    root = args.root.resolve()
    output = (args.output or (root / "output/html/unit-10")).resolve()
    receipt = (args.receipt or (root / "qa/unit-10/HTML_READER_QA.json")).resolve()
    try:
        result = verify(root, output)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
    write_text(receipt, canonical_json(result))
    print(canonical_json({
        "status": "pass",
        "receipt": receipt.relative_to(root).as_posix(),
        "entry": result["entry"],
        "manifest": result["manifest"],
        "counts": result["counts"],
    }), end="")


if __name__ == "__main__":
    main()
