#!/usr/bin/env python3
"""Build the complete deterministic reflowable O011 Indonesian reader."""

from __future__ import annotations

import argparse
import html
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import export_html_v19 as v19
import export_html_v22 as v22


SCHEMA_VERSION = 1
WORKFLOW = "o011-export-html-complete-v1"
UNIT_COUNT = 29
UNIT_TITLES = {
    **v22.UNIT_TITLES,
    23: "Teorema Stokes dan Teorema Titik Tetap Brouwer",
    24: "Koneksi dan Turunan Vertikal",
    25: "Koneksi Linear dan Penampang Horizontal",
    26: "Koneksi Levi--Civita",
    27: "Kurva Geodesik",
    28: "Kelengkungan dan Teorema Frobenius",
    29: "Kelengkungan Seksional",
}
MODEL_IDENTIFICATION = v22.MODEL_IDENTIFICATION
OFFICIAL_SOURCE = v22.OFFICIAL_SOURCE
MATHJAX_URL = v22.MATHJAX_URL
MATHJAX_CONFIG = v22.MATHJAX_CONFIG

canonical_json = v22.canonical_json
file_binding = v22.file_binding
inventory_sha256 = v22.inventory_sha256
load_json_object = v22.load_json_object
tree_inventory = v22.tree_inventory
write_text = v22.write_text


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def normalized(value: str) -> str:
    return re.sub(r"\s+", "", value)


def braced_argument(text: str, start: int) -> tuple[int, int, str]:
    while start < len(text) and text[start].isspace():
        start += 1
    if start >= len(text) or text[start] != "{":
        raise RuntimeError(f"expected braced argument at character {start}")
    depth = 0
    escaped = False
    for index in range(start, len(text)):
        character = text[index]
        if escaped:
            escaped = False
        elif character == "\\":
            escaped = True
        elif character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
            if depth == 0:
                return start, index + 1, text[start + 1:index]
    raise RuntimeError("unterminated braced argument")


def command_calls(text: str, names: tuple[str, ...], argument_count: int) -> list[tuple[str, list[str], int]]:
    pattern = re.compile(r"\\(" + "|".join(re.escape(name) for name in names) + r")(?![A-Za-z@])")
    result: list[tuple[str, list[str], int]] = []
    for match in pattern.finditer(text):
        cursor = match.end()
        values: list[str] = []
        for _ in range(argument_count):
            _, cursor, value = braced_argument(text, cursor)
            values.append(value)
        result.append((match.group(1), values, match.start()))
    return result


def complete_short_inline_chains(text: str) -> str:
    """Supply the inert fourth wrapper argument omitted by a few source calls."""
    pattern = re.compile(r"\\mavergleichskette(?:k)?(?![A-Za-z@])")
    insertions: list[int] = []
    for match in pattern.finditer(text):
        cursor = match.end()
        parsed = 0
        try:
            for _ in range(4):
                _, cursor, _ = braced_argument(text, cursor)
                parsed += 1
        except RuntimeError:
            if parsed == 3:
                insertions.append(cursor)
            else:
                raise
    for cursor in reversed(insertions):
        text = text[:cursor] + "{}" + text[cursor:]
    return text


def split_inline_chain_suffixes(text: str) -> str:
    """Keep wrapper suffixes/footnotes outside the mathematical TeX span."""
    pattern = re.compile(r"\\mavergleichskette(?:k)?(?![A-Za-z@])")
    replacements = 0
    while True:
        match = pattern.search(text)
        if match is None:
            return text
        cursor = match.end()
        arguments: list[str] = []
        for _ in range(4):
            _, cursor, argument = braced_argument(text, cursor)
            arguments.append(argument)
        replacement = r"\mathl{" + arguments[0] + "}{" + "".join(arguments[1:]) + "}"
        text = text[:match.start()] + replacement + text[cursor:]
        replacements += 1
        if replacements > 256:
            raise RuntimeError("inline comparison-chain rewrite did not converge")


def protect_jacobi_lie_brackets(text: str) -> str:
    """Disambiguate mathematical nested brackets from MediaWiki links.

    The inherited math expander interprets literal ``[[...]]`` as a wiki-link
    label.  Unit 29's Jacobi identity instead uses those bytes for nested Lie
    brackets, so spell the same TeX with explicit scalable delimiters before
    the inherited expander sees it.
    """
    source = "[V, [W,Z]] + [W, [Z,V]] + [Z, [V,W]]"
    replacement = (
        r"\left[V,\left[W,Z\right]\right]"
        r" + \left[W,\left[Z,V\right]\right]"
        r" + \left[Z,\left[V,W\right]\right]"
    )
    return text.replace(source, replacement)


class Renderer(v22.Renderer):
    """Unit 22 renderer extended only for newly admitted media receipts."""

    def __init__(self, root: Path, rights: dict[str, dict[str, str]]) -> None:
        super().__init__(root, rights)
        canonical = self.rights.get("théorème-de-brouwer-(cond-1).jpg")
        if canonical is not None:
            self.rights["theoreme-de-brouwer-(cond-1).jpg"] = canonical

    def render_inline(self, text: str, state: v19.SurfaceState) -> str:
        # MediaWiki's LaTeX export legally permits whitespace between a macro
        # name and its first braced argument.  The inherited deterministic
        # reader parser expects the equivalent compact spelling.
        text = re.sub(r"\\([A-Za-z@]+)\s+(?=\{)", r"\\\1", text)
        text = protect_jacobi_lie_brackets(text)
        text = complete_short_inline_chains(text)
        text = split_inline_chain_suffixes(text)
        return super().render_inline(text, state)

    def render_flow(self, raw_text: str, state: v19.SurfaceState) -> str:
        # Structural display-math macros are consumed by the inherited flow
        # parser before ``render_inline`` is reached, so protect the one nested
        # Lie-bracket identity at this boundary as well.
        return super().render_flow(protect_jacobi_lie_brackets(raw_text), state)

    def _verify_unit_media_receipt(self, filename: str, unit: int, binding: dict[str, Any]) -> dict[str, Any]:
        if unit <= 22:
            return super()._verify_unit_media_receipt(filename, unit, binding)
        receipt_path = self.root / f"qa/complete/cumulative-media/unit-{unit:02d}_media.json"
        receipt = load_json_object(receipt_path)
        expect(receipt.get("unit_number") == unit, f"complete media receipt unit differs for {filename}")
        matches = [
            item for item in receipt.get("media", [])
            if isinstance(item, dict) and item.get("filename") == filename
        ]
        expect(len(matches) == 1, f"Unit {unit} complete media receipt does not uniquely bind {filename}")
        item = matches[0]
        expect(item.get("canonical_path") == binding["path"], f"Unit {unit} media path differs for {filename}")
        expect(item.get("canonical_bytes") == binding["bytes"], f"Unit {unit} media byte count differs for {filename}")
        expect(item.get("canonical_sha256") == binding["sha256"], f"Unit {unit} media SHA-256 differs for {filename}")
        return file_binding(receipt_path, self.root)


def core_source_files(root: Path) -> list[Path]:
    return v19.source_files(root, UNIT_COUNT)


def exam_source_files(root: Path) -> list[Path]:
    paths: list[Path] = []
    for exam in range(1, 11):
        tag = f"{exam:02d}"
        paths.extend([
            root / f"source/exams/exam-{tag}/exam{tag}_learner.id.tex",
            root / f"source/exams/exam-{tag}/exam{tag}_solutions.id.tex",
            root / f"build/generated/exams/exam{tag}_learner.id.build.tex",
            root / f"build/generated/exams/exam{tag}_solutions.id.build.tex",
            root / f"qa/complete/preparation/exam{tag}_learner_prepare.json",
            root / f"qa/complete/preparation/exam{tag}_solutions_prepare.json",
            root / f"qa/exams/EXAM{tag}_SOLUTIONS_TRANSLATION_QA.json",
            root / f"qa/exams/EXAM{tag}_SOLUTIONS_BOUNDED_QA.json",
        ])
    return paths


def supplement_source_files(root: Path) -> list[Path]:
    return [
        root / "source/bridges/lie-groups/bridge-lie-theory.id.tex",
        root / "source/bridges/lie-groups/bridge-lie-assessment.id.tex",
        root / "source/bridges/de-rham/bridge-de-rham-theory.id.tex",
        root / "source/bridges/de-rham/bridge-de-rham-assessment.id.tex",
        root / "source/exams/original-repairs/missing-exam-solutions.id.tex",
        root / "qa/bridges/lie-groups/BRIDGE_LIE_CONTENT_SMOKE_QA.json",
        root / "qa/bridges/de-rham/BRIDGE_DE_RHAM_CONTENT_SMOKE_QA.json",
        root / "qa/exams/ORIGINAL_MISSING_SOLUTIONS_QA.json",
    ]


def all_inputs(root: Path) -> list[Path]:
    paths = [*core_source_files(root), *exam_source_files(root), *supplement_source_files(root)]
    paths.extend(root / f"qa/complete/cumulative-media/unit-{unit:02d}_media.json" for unit in range(23, 30))
    unique = sorted(set(path.resolve() for path in paths), key=lambda path: path.as_posix())
    for path in unique:
        expect(path.is_file(), f"missing complete HTML input: {path.relative_to(root)}")
    return unique


def render_core(root: Path, renderer: Renderer) -> tuple[str, dict[str, Any]]:
    old_count, old_titles = v22.UNIT_COUNT, v22.UNIT_TITLES
    try:
        v22.UNIT_COUNT = UNIT_COUNT
        v22.UNIT_TITLES = UNIT_TITLES
        document, topology = v22.render_reader(root, renderer)
    finally:
        v22.UNIT_COUNT = old_count
        v22.UNIT_TITLES = old_titles
    replacements = {
        "Kuliah dan Lembar Kerja 1–22": "Kuliah dan Lembar Kerja 1–29",
        "Pembaca hingga Unit 22": "Pembaca lengkap",
        "Pembaca kumulatif hingga Unit 22": "Pembaca lengkap: 29 unit, jembatan, dan asesmen",
        "Kuliah 1–22 dan Lembar Kerja 1–22": "Kuliah 1–29 dan Lembar Kerja 1–29",
        "Bahasa Indonesia · Unit 1–22": "Bahasa Indonesia · Edisi lengkap",
        "Edisi Bahasa Indonesia independen · cakupan parsial": "Edisi Bahasa Indonesia independen · lengkap",
    }
    for old, new in replacements.items():
        expect(old in document, f"complete-reader scope marker missing: {old}")
        document = document.replace(old, new, 1)
    return document, topology


def pandoc_version() -> str:
    process = subprocess.run(["pandoc", "--version"], check=True, text=True, encoding="utf-8", stdout=subprocess.PIPE)
    return process.stdout.splitlines()[0]


def pandoc_fragment(path: Path) -> str:
    process = subprocess.run(
        ["pandoc", "--from=latex", "--to=html5", "--mathjax", "--wrap=none", str(path)],
        check=True,
        text=True,
        encoding="utf-8",
        stdout=subprocess.PIPE,
    )
    return process.stdout.strip()


def namespace_pandoc_ids(fragment: str, namespace: str) -> str:
    """Namespace Pandoc's local auto-IDs while preserving project stable IDs."""
    identifiers = re.findall(r'\bid="([^"]+)"', fragment)
    expect(len(identifiers) == len(set(identifiers)), f"duplicate Pandoc ID inside {namespace} fragment")
    replacements = {
        identifier: f"{namespace}-{identifier}"
        for identifier in identifiers
        if not identifier.startswith("o011-")
    }
    for old, new in replacements.items():
        fragment = fragment.replace(f'id="{old}"', f'id="{new}"')
        fragment = fragment.replace(f'href="#{old}"', f'href="#{new}"')
    return fragment


def render_bridge(root: Path, bridge: str) -> str:
    if bridge == "lie":
        paths = [
            root / "source/bridges/lie-groups/bridge-lie-theory.id.tex",
            root / "source/bridges/lie-groups/bridge-lie-assessment.id.tex",
        ]
        namespaces = ["lie-theory", "lie-assessment"]
        title, anchor = "Jembatan Grup Lie dan Aljabar Lie", "jembatan-lie"
    else:
        paths = [
            root / "source/bridges/de-rham/bridge-de-rham-theory.id.tex",
            root / "source/bridges/de-rham/bridge-de-rham-assessment.id.tex",
        ]
        namespaces = ["de-rham-theory", "de-rham-assessment"]
        title, anchor = "Jembatan Kohomologi de Rham", "jembatan-de-rham"
    body = "\n".join(
        namespace_pandoc_ids(pandoc_fragment(path), namespace)
        for path, namespace in zip(paths, namespaces, strict=True)
    )
    return (
        f'<section class="supplement bridge" id="{anchor}" data-entity="original-bridge">'
        f'<header class="unit-header"><p class="eyebrow">Modul asli · CC BY-SA 4.0</p><h2>{html.escape(title)}</h2></header>'
        '<p class="scope-note">Modul ini disusun secara independen untuk menutup cakupan kurikuler; '
        'modul ini bukan teks atau solusi yang dinisbahkan kepada sumber Brenner.</p>'
        f'{body}</section>'
    )


def render_exam_bank(root: Path, renderer: Renderer) -> tuple[str, dict[str, Any]]:
    forms: list[str] = []
    topology: dict[str, Any] = {}
    for exam in range(1, 11):
        tag = f"{exam:02d}"
        learner_path = root / f"build/generated/exams/exam{tag}_learner.id.build.tex"
        solution_path = root / f"build/generated/exams/exam{tag}_solutions.id.build.tex"
        learner_calls = sorted(
            command_calls(learner_path.read_text(encoding="utf-8"), ("inputaufgabe", "inputaufgabegibtloesung"), 4),
            key=lambda item: item[2],
        )
        solution_calls = command_calls(
            solution_path.read_text(encoding="utf-8"), ("inputaufgabeklausurloesung",), 3
        )
        expect(len(learner_calls) == len(solution_calls), f"Exam {exam} learner/solution occurrence mismatch")
        learner_articles: list[str] = []
        solution_articles: list[str] = []
        supplied_count = 0
        missing: list[int] = []
        point_labels: list[str] = []
        actual_slots: list[int] = []
        placeholder_slots: list[int] = []
        for occurrence, (learner_call, solution_call) in enumerate(zip(learner_calls, solution_calls), 1):
            learner_name, learner_args, _ = learner_call
            _, solution_args, _ = solution_call
            point_match = normalized(learner_args[0]) == normalized(solution_args[0])
            frozen_exam09_placeholder = (
                exam == 9
                and occurrence == 7
                and normalized(solution_args[0]) == "weiter"
                and normalized(learner_args[0]) == "13(2+3+2+2+2+2)"
            )
            expect(point_match or frozen_exam09_placeholder, f"Exam {exam} point mismatch at {occurrence}")
            expect(normalized(learner_args[1]) == normalized(solution_args[1]), f"Exam {exam} prompt mismatch at {occurrence}")
            if normalized(learner_args[0]) == "0":
                expect(
                    not learner_args[1].strip() and not learner_args[2].strip() and not solution_args[2].strip(),
                    f"Exam {exam} placeholder slot {occurrence} unexpectedly carries content",
                )
                placeholder_slots.append(occurrence)
                continue
            actual_slots.append(occurrence)
            problem_id = f"o011-exam-{tag}-p{occurrence:03d}"
            points = renderer.render_inline(learner_args[0].strip(), v19.SurfaceState(100 + exam, "exam-points", problem_id))
            point_labels.append(learner_args[0].strip())
            prompt_state = v19.SurfaceState(100 + exam, "exam-learner", problem_id)
            prompt = renderer.render_flow(learner_args[1], prompt_state)
            hint = renderer.render_flow(learner_args[2], prompt_state) if learner_args[2].strip() else ""
            badges = [f'<span class="points">{points} poin</span>'] if points else []
            if learner_name == "inputaufgabegibtloesung":
                badges.append('<span class="solution-marker">Solusi sumber tersedia</span>')
            learner_articles.append(
                f'<article class="exercise exam-problem" id="{problem_id}" data-entity="exam-problem">'
                f'<h4>Soal {exam}.{occurrence}</h4>{"".join(badges)}{prompt}'
                + (f'<aside class="hint"><h5>Petunjuk sumber</h5>{hint}</aside>' if hint else "")
                + '</article>'
            )
            if solution_args[2].strip():
                supplied_count += 1
                solution_id = f"{problem_id}-source-solution"
                solution_state = v19.SurfaceState(200 + exam, "exam-source-solution", solution_id)
                solution_body = renderer.render_flow(solution_args[2], solution_state)
                solution_articles.append(
                    f'<article class="source-solution exam-solution" id="{solution_id}" '
                    f'data-entity="source-supplied-exam-solution" data-solves="{problem_id}">'
                    f'<h4>Solusi sumber untuk Soal {exam}.{occurrence}</h4>{solution_body}'
                    f'<p class="solution-backlink"><a href="#{problem_id}">Kembali ke Soal {exam}.{occurrence}</a></p></article>'
                )
            elif points.strip() and points.strip() != "0":
                missing.append(occurrence)
        forms.append(
            f'<section class="exam-form" id="ujian-{tag}" data-entity="exam-form">'
            f'<header class="unit-header"><p class="eyebrow">Formulir {exam}</p><h3>Ujian {exam}</h3></header>'
            f'<section class="exam-learner" aria-label="Formulir peserta Ujian {exam}">{"".join(learner_articles)}</section>'
            f'<section class="solutions exam-solutions" aria-label="Solusi resmi Ujian {exam}">'
            '<h3>Solusi yang disediakan oleh sumber</h3>'
            '<p class="scope-note">Solusi dalam bagian ini hanya yang benar-benar tersedia pada sumber.</p>'
            f'{"".join(solution_articles)}</section></section>'
        )
        topology[tag] = {
            "nominal_slots": len(learner_calls),
            "actual_occurrences": len(actual_slots),
            "actual_occurrence_slots": actual_slots,
            "zero_point_placeholder_slots": placeholder_slots,
            "source_supplied_solution_occurrences": supplied_count,
            "source_missing_nonzero_solution_occurrences": missing,
            "point_labels": point_labels,
        }
    repairs = pandoc_fragment(root / "source/exams/original-repairs/missing-exam-solutions.id.tex")
    return (
        '<section class="supplement assessment-bank" id="bank-ujian" data-entity="assessment-bank">'
        '<header class="unit-header"><p class="eyebrow">Asesmen kumulatif resmi</p><h2>Sepuluh formulir ujian dan solusi</h2></header>'
        '<p class="scope-note">Pemetaan kemunculan dipertahankan. Solusi resmi dipisahkan dari enam solusi perbaikan asli.</p>'
        + "".join(forms)
        + '<section class="original-repairs" id="solusi-perbaikan-asli" data-entity="original-exam-solution-repairs">'
        '<h2>Enam solusi perbaikan asli</h2><p class="scope-note">Bagian ini berlisensi CC BY-SA 4.0 dan tidak '
        'dinisbahkan kepada Brenner atau Wikiversity.</p>' + repairs + '</section></section>',
        topology,
    )


def extended_css(renderer: Renderer) -> str:
    return v22.reader_css(renderer) + """

.supplement,.assessment-bank{margin:3rem auto;max-width:88rem;padding:1.5rem;border-top:4px solid var(--accent)}
.supplement-nav{max-width:88rem;margin:0 auto;padding:1rem}.supplement-nav ul{display:flex;flex-wrap:wrap;gap:.8rem;list-style:none;padding:0}
.exam-form{margin:2rem 0;padding:1rem;border:1px solid var(--line);border-radius:.5rem}.exam-problem,.exam-solution{scroll-margin-top:5rem}
.exam-learner{display:grid;gap:1rem}.exam-solutions{margin-top:2rem}.original-repairs{margin-top:3rem;padding-top:1rem;border-top:2px solid var(--line)}
.bridge .definition,.bridge .beispiel{padding:1rem;margin:1rem 0;border-left:4px solid var(--accent);background:var(--surface)}
.supplement .math.inline,.assessment-bank .math.inline{display:inline-block;max-width:100%;overflow-x:auto;overflow-y:hidden;vertical-align:middle}
.supplement .math.display,.assessment-bank .math.display{display:block;max-width:100%;overflow-x:auto;overflow-y:hidden}
"""


def generation_contract(root: Path) -> dict[str, Any]:
    inputs = all_inputs(root)
    return {
        "unit22_public_reader_baseline": v22.generation_contract(root),
        "complete_inputs": [file_binding(path, root) for path in inputs],
        "exporter": file_binding(Path(__file__).resolve(), root),
        "pandoc": pandoc_version(),
    }


def stage_cycle(root: Path, staging: Path, contract: dict[str, Any]) -> dict[str, Any]:
    staging.mkdir(parents=True, exist_ok=False)
    inputs = all_inputs(root)
    before = [file_binding(path, root) for path in inputs]
    renderer = Renderer(root, v22.load_media_rights(root))
    document, core_topology = render_core(root, renderer)
    lie = render_bridge(root, "lie")
    de_rham = render_bridge(root, "de-rham")
    exams, exam_topology = render_exam_bank(root, renderer)
    insertion = (
        '<nav class="supplement-nav" aria-label="Materi tambahan"><ul>'
        '<li><a href="#jembatan-lie">Jembatan Lie</a></li>'
        '<li><a href="#jembatan-de-rham">Jembatan de Rham</a></li>'
        '<li><a href="#bank-ujian">Bank ujian</a></li></ul></nav>'
        + lie + de_rham + exams
    )
    marker = '<section class="backmatter" id="lisensi-dan-provenans">'
    expect(document.count(marker) == 1, "complete-reader backmatter insertion marker is not unique")
    document = document.replace(marker, insertion + marker, 1)
    after = [file_binding(path, root) for path in inputs]
    expect(before == after, "complete HTML inputs changed during staging")
    write_text(staging / "index.html", document)
    write_text(staging / "assets/reader.css", extended_css(renderer))
    write_text(
        staging / "README.txt",
        "Pembaca HTML lengkap Bahasa Indonesia: 29 unit Brenner, dua jembatan asli, sepuluh formulir ujian, solusi sumber, dan enam perbaikan asli.\n",
    )
    media, linked_media = v22.stage_media_assets(root, staging, renderer)
    payload = tree_inventory(staging)
    payload_digest = inventory_sha256(payload)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "workflow": WORKFLOW,
        "scope": "complete O011 Indonesian reader: 29 core units, two original bridges, and ten-form assessment bank",
        "status": "complete_edition",
        "language": "id-ID",
        "model_identification": MODEL_IDENTIFICATION,
        "official_source": OFFICIAL_SOURCE,
        "text_license": "CC BY-SA 4.0",
        "component_media_licenses_remain_file_specific": True,
        "non_endorsement": True,
        "units": list(range(1, 30)),
        "bridges": ["Lie groups and Lie algebras", "de Rham cohomology and differential-topology gateway"],
        "exam_forms": list(range(1, 11)),
        "core_topology": core_topology,
        "exam_topology": exam_topology,
        "media": media,
        "source_linked_media": linked_media,
        "figures": renderer.figure_occurrences,
        "source_linked_media_occurrences": renderer.linked_media_occurrences,
        "inputs": after,
        "generation_contract": contract,
        "reproducibility": {
            "staging_cycles": 2,
            "byte_identical_complete_trees_required": True,
            "payload_inventory_sha256": payload_digest,
        },
        "files": payload,
    }
    write_text(staging / "manifest.json", canonical_json(manifest))
    return manifest


def build(root: Path, output: Path, replace: bool) -> dict[str, Any]:
    root, output = root.resolve(), output.resolve()
    html_root = (root / "output/html").resolve()
    try:
        output.relative_to(html_root)
    except ValueError as exc:
        raise RuntimeError("complete HTML output must remain beneath output/html") from exc
    expect(output != html_root, "complete HTML output may not replace output/html")
    if output.exists():
        expect(output.is_dir(), f"output exists and is not a directory: {output}")
        expect(replace, "complete HTML output exists; use --replace for this exact directory")
    contract = generation_contract(root)
    output.parent.mkdir(parents=True, exist_ok=True)
    first = Path(tempfile.mkdtemp(prefix=".html-complete-cycle1-", dir=output.parent))
    second = Path(tempfile.mkdtemp(prefix=".html-complete-cycle2-", dir=output.parent))
    try:
        first_stage, second_stage = first / "reader", second / "reader"
        first_manifest = stage_cycle(root, first_stage, contract)
        expect(generation_contract(root) == contract, "generation contract changed after complete cycle one")
        second_manifest = stage_cycle(root, second_stage, contract)
        expect(generation_contract(root) == contract, "generation contract changed after complete cycle two")
        first_inventory, second_inventory = tree_inventory(first_stage), tree_inventory(second_stage)
        expect(first_inventory == second_inventory, "complete HTML staging trees are not byte-identical")
        expect(first_manifest == second_manifest, "complete HTML manifests differ")
        if output.exists():
            shutil.rmtree(output)
        os.replace(second_stage, output)
        return {
            "manifest": second_manifest,
            "tree_inventory_sha256": inventory_sha256(second_inventory),
            "tree_file_count": len(second_inventory),
        }
    finally:
        shutil.rmtree(first, ignore_errors=True)
        shutil.rmtree(second, ignore_errors=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    output = (args.output or root / "output/html/complete").resolve()
    result = build(root, output, args.replace)
    print(canonical_json({
        "status": "pass",
        "output": output.relative_to(root).as_posix(),
        "file_count": result["tree_file_count"],
        "tree_inventory_sha256": result["tree_inventory_sha256"],
        "input_count": len(result["manifest"]["inputs"]),
        "media_count": len(result["manifest"]["media"]),
    }), end="")


if __name__ == "__main__":
    main()
