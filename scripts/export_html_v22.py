#!/usr/bin/env python3
"""Build the deterministic Indonesian semantic HTML reader through Unit 22.

This boundary reuses the exact Unit 19 renderer, proves the committed Unit 19
reader before staging, adds only the admitted Unit 20--22 source surfaces, and
commits only after two complete staging trees are byte-identical.
"""

from __future__ import annotations

import argparse
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

import export_html_v10 as v10
import export_html_v19 as v19


SCHEMA_VERSION = 1
WORKFLOW = "o011-export-html-v22"
UNIT_COUNT = 22
MODEL_IDENTIFICATION = v19.MODEL_IDENTIFICATION
OFFICIAL_SOURCE = v19.OFFICIAL_SOURCE
MATHJAX_URL = v19.MATHJAX_URL
MATHJAX_CONFIG = v19.MATHJAX_CONFIG
UNIT_TITLES = {
    **v19.UNIT_TITLES,
    20: "Turunan Eksterior",
    21: "Manifold Berbatas",
    22: "Partisi Satuan",
}

EXPECTED_V19_OUTPUT_FILE_COUNT = 35
EXPECTED_V19_OUTPUT_INVENTORY_SHA256 = "c86631af6d21a495e0ec84bcc9eae59a5ad91b54fab7f9a4e968ef1e148529df"
EXPECTED_V19_BINDINGS = {
    "scripts/export_html_v19.py": (50646, "5735f5acb1f556ea67fa2b84f63c338ab66365ba479e4fb89d87f7453a99eb9a"),
    "scripts/verify_html_v19.py": (34814, "6421c5caa9ec7df5a570ebd58a01465411a363a397d34b6661d4cd8659576103"),
    "scripts/test_html_v19_pipeline.py": (8736, "530ad930abc7d2d58a45acea3aca752953da79756feb33654211f29e01ff3e46"),
    "output/html/unit-19/index.html": (1333528, "096393a5218d49dca913904bbf52a9bc0933a389d456db5d907db76872a3444a"),
    "output/html/unit-19/manifest.json": (110705, "78af3571a8ed75da6bdf421342bf601148c972dbb0f450f36fbeeddb97f74aac"),
    "output/html/unit-19/assets/reader.css": (7045, "b2af565e44ff10837308b0d1bc693ef8be350e2a80fa4d654ce2ecac3864e0b0"),
    "output/html/unit-19/README.txt": (1120, "289ab42fe4af3851d282c9a1fb0397e77be55d269fd098f019d7f61e69acd9c0"),
    "qa/unit-19/HTML_READER_QA.json": (33848, "f41ece1e459b6e9ce4df411855f3ab3fb4fa4a08213ff6d01408394f675ef078"),
}

canonical_json = v19.canonical_json
file_binding = v19.file_binding
inventory_sha256 = v19.inventory_sha256
load_json_object = v19.load_json_object
safe_project_path = v19.safe_project_path
tree_inventory = v19.tree_inventory
write_text = v19.write_text


class Renderer(v19.Renderer):
    """Exact v19 renderer with the admitted Unit 22 spacing macro."""

    def render_inline(self, text: str, state: v19.SurfaceState) -> str:
        return super().render_inline(text.replace(r"\leerzeichen", " "), state)


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def source_files(root: Path, maximum_unit: int = UNIT_COUNT) -> list[Path]:
    return v19.source_files(root, maximum_unit)


def unit_source_files(root: Path, unit: int) -> list[Path]:
    return v19.unit_source_files(root, unit)


def solution_indices(root: Path, unit: int) -> list[int]:
    return v19.solution_indices(root, unit)


def source_solution_marker_indices(path: Path) -> list[int]:
    return v19.source_solution_marker_indices(path)


def unit19_baseline(root: Path) -> dict[str, Any]:
    bindings: list[dict[str, Any]] = []
    for relative, (size, digest) in EXPECTED_V19_BINDINGS.items():
        path = safe_project_path(root, relative)
        expect(path.is_file(), f"missing exact Unit 19 baseline component: {relative}")
        actual = file_binding(path, root)
        expect(actual["bytes"] == size and actual["sha256"] == digest, f"exact Unit 19 baseline changed: {relative}")
        bindings.append(actual)
    directory = root / "output/html/unit-19"
    inventory = tree_inventory(directory)
    digest = inventory_sha256(inventory)
    expect(len(inventory) == EXPECTED_V19_OUTPUT_FILE_COUNT, "Unit 19 output file count changed")
    expect(digest == EXPECTED_V19_OUTPUT_INVENTORY_SHA256, "Unit 19 output inventory changed")
    manifest = load_json_object(directory / "manifest.json")
    expect(manifest.get("workflow") == v19.WORKFLOW, "Unit 19 manifest workflow changed")
    expect(manifest.get("units") == list(range(1, 20)), "Unit 19 manifest scope changed")
    expect(manifest.get("inputs") == [file_binding(path, root) for path in source_files(root, 19)], "live Unit 1--19 sources differ from the Unit 19 reader")
    return {
        "status": "exact_committed_baseline_preserved",
        "output_directory": "output/html/unit-19",
        "output_file_count": len(inventory),
        "output_inventory_sha256": digest,
        "output_inventory": inventory,
        "bindings": bindings,
        "lower_generation_contract": v19.generation_contract(root),
    }


def new_unit_admission_bindings(root: Path) -> dict[str, Any]:
    live_20_22 = v19.load_live_qa_bindings(root, range(20, 23))
    verify_path = root / "qa/unit-22/POST_CORRECTION_MATH_QA_VERIFY.json"
    expect(verify_path.is_file(), "missing independent Unit 22 POST QA verification")
    expect(load_json_object(verify_path).get("status") == "pass", "independent Unit 22 POST QA verification is not passing")
    return {
        "unit20_22_live_qa": live_20_22,
        "unit22_post_qa_verify": file_binding(verify_path, root),
    }


def generation_bindings(root: Path) -> list[dict[str, Any]]:
    bindings = v19.generation_bindings(root)
    for unit in range(20, 23):
        bindings.append(file_binding(root / f"qa/unit-{unit:02d}_media.json", root))
    return bindings


def generation_contract(root: Path) -> dict[str, Any]:
    return {
        "unit19_baseline": unit19_baseline(root),
        "unit20_22_admission": new_unit_admission_bindings(root),
        "generation_bindings": generation_bindings(root),
        "exporter": file_binding(Path(__file__).resolve(), root),
    }


def load_media_rights(root: Path) -> dict[str, dict[str, str]]:
    return v19.load_media_rights(root)


def render_reader(root: Path, renderer: Renderer) -> tuple[str, dict[str, Any]]:
    old_count, old_titles = v19.UNIT_COUNT, v19.UNIT_TITLES
    old_math_macro_value = v10.math_macro_value

    def math_macro_value(name: str, args: list[str]) -> str:
        if name != "mathbeddisp":
            return old_math_macro_value(name, args)
        value = args[0]
        for separator, term in ((args[1], args[2]), (args[3], args[4]), (args[5], args[6])):
            if term.strip():
                value += (separator if separator.strip() else r",\quad ") + term
        return value + args[7]

    try:
        v19.UNIT_COUNT = UNIT_COUNT
        v19.UNIT_TITLES = UNIT_TITLES
        v10.STRUCTURAL_ARITY["mathbeddisp"] = 8
        v10.MATH_WRAPPERS.add("mathbeddisp")
        v10.math_macro_value = math_macro_value
        document, topology = v19.render_reader(root, renderer)
    finally:
        v19.UNIT_COUNT = old_count
        v19.UNIT_TITLES = old_titles
        v10.STRUCTURAL_ARITY.pop("mathbeddisp", None)
        v10.MATH_WRAPPERS.discard("mathbeddisp")
        v10.math_macro_value = old_math_macro_value
    replacements = {
        "Kuliah dan Lembar Kerja 1–19": "Kuliah dan Lembar Kerja 1–22",
        "Pembaca hingga Unit 19": "Pembaca hingga Unit 22",
        "Pembaca kumulatif hingga Unit 19": "Pembaca kumulatif hingga Unit 22",
        "Kuliah 1–19 dan Lembar Kerja 1–19": "Kuliah 1–22 dan Lembar Kerja 1–22",
        "Bahasa Indonesia · Unit 1–19": "Bahasa Indonesia · Unit 1–22",
    }
    for old, new in replacements.items():
        expect(old in document, f"Unit 19 scope marker missing during v22 rendering: {old}")
        document = document.replace(old, new, 1)
    return document, topology


def reader_css(renderer: Renderer) -> str:
    return v19.reader_css(renderer)


def reader_readme(renderer: Renderer) -> str:
    value = v19.reader_readme(renderer)
    expect("hingga Unit 19" in value, "Unit 19 README scope marker missing")
    return value.replace("hingga Unit 19", "hingga Unit 22", 1)


def stage_media_assets(root: Path, staging: Path, renderer: Renderer) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    return v19.stage_media_assets(root, staging, renderer)


def _stage_cycle(root: Path, staging: Path, contract: dict[str, Any]) -> dict[str, Any]:
    staging.mkdir(parents=True, exist_ok=False)
    inputs = source_files(root)
    initial_bindings = [file_binding(path, root) for path in inputs]
    renderer = Renderer(root, load_media_rights(root))
    document, topology = render_reader(root, renderer)
    final_bindings = [file_binding(path, root) for path in inputs]
    expect(initial_bindings == final_bindings, "reader sources changed during a staging cycle")
    write_text(staging / "index.html", document)
    write_text(staging / "assets/reader.css", reader_css(renderer))
    write_text(staging / "README.txt", reader_readme(renderer))
    media_manifest, linked_media_manifest = stage_media_assets(root, staging, renderer)
    payload_files = tree_inventory(staging)
    payload_digest = inventory_sha256(payload_files)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "workflow": WORKFLOW,
        "scope": "O011 cumulative Indonesian semantic HTML reader through Unit 22",
        "status": "partial_edition",
        "language": "id-ID",
        "units": list(range(1, UNIT_COUNT + 1)),
        "model_identification": MODEL_IDENTIFICATION,
        "official_source": OFFICIAL_SOURCE,
        "text_license": "CC BY-SA 4.0",
        "non_endorsement": True,
        "math_rendering": {
            "format": "MathJax-compatible TeX retained in document text",
            "optional_network_dependency": MATHJAX_URL,
            "offline_fallback": "visible selectable TeX source",
        },
        "inputs": final_bindings,
        "unit19_baseline": contract["unit19_baseline"],
        "unit20_22_admission": contract["unit20_22_admission"],
        "generation_bindings": contract["generation_bindings"],
        "exporter": contract["exporter"],
        "topology": topology,
        "media": media_manifest,
        "source_linked_media": linked_media_manifest,
        "figures": renderer.figure_occurrences,
        "source_linked_media_occurrences": renderer.linked_media_occurrences,
        "reproducibility": {
            "staging_cycles": 2,
            "required_comparison": "complete relative-path/byte-count/SHA-256 inventory, including manifest",
            "payload_inventory_sha256": payload_digest,
            "byte_identical_before_commit": True,
        },
        "excluded_reader_metadata": {
            "mediawiki_category_marker": "[[Kategorie:Latexseite]]",
            "occurrences": sum(path.read_text(encoding="utf-8").count("[[Kategorie:Latexseite]]") for path in inputs),
            "preservation": "Retained byte-for-byte in the source inputs bound above; excluded only from reader-visible prose.",
        },
        "files": payload_files,
    }
    write_text(staging / "manifest.json", canonical_json(manifest))
    return manifest


def assert_output_path(root: Path, output: Path) -> Path:
    root, output = root.resolve(), output.resolve()
    html_root = (root / "output/html").resolve()
    try:
        relative = output.relative_to(html_root)
    except ValueError as exc:
        raise RuntimeError("v22 output must remain beneath output/html") from exc
    expect(bool(relative.parts), "v22 output may not replace output/html itself")
    immutable = {(html_root / f"unit-{unit}").resolve() for unit in (10, 13, 16, 19)}
    expect(output not in immutable, "published/committed Unit 10/13/16/19 outputs are immutable")
    return output


def build(root: Path, output: Path, replace: bool) -> dict[str, Any]:
    root, output = root.resolve(), assert_output_path(root, output)
    if output.exists():
        expect(output.is_dir(), f"output exists and is not a directory: {output}")
        expect(replace, f"output already exists (use --replace for this exact v22 directory): {output}")
    contract = generation_contract(root)
    output.parent.mkdir(parents=True, exist_ok=True)
    first = Path(tempfile.mkdtemp(prefix=".html-v22-cycle1-", dir=output.parent))
    second = Path(tempfile.mkdtemp(prefix=".html-v22-cycle2-", dir=output.parent))
    try:
        first_stage, second_stage = first / "reader", second / "reader"
        first_manifest = _stage_cycle(root, first_stage, contract)
        expect(generation_contract(root) == contract, "generation contract changed after staging cycle one")
        second_manifest = _stage_cycle(root, second_stage, contract)
        expect(generation_contract(root) == contract, "generation contract changed after staging cycle two")
        first_inventory, second_inventory = tree_inventory(first_stage), tree_inventory(second_stage)
        expect(first_inventory == second_inventory, "two complete Unit 22 staging trees are not byte-identical")
        expect(first_manifest == second_manifest, "two Unit 22 staging manifests differ")
        if output.exists():
            shutil.rmtree(output)
        os.replace(second_stage, output)
        return {"manifest": second_manifest, "tree_inventory_sha256": inventory_sha256(second_inventory), "tree_file_count": len(second_inventory)}
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
    output = (args.output or root / "output/html/unit-22").resolve()
    result = build(root, output, args.replace)
    manifest = result["manifest"]
    print(canonical_json({
        "status": "pass",
        "output": output.relative_to(root).as_posix(),
        "input_count": len(manifest["inputs"]),
        "file_count": result["tree_file_count"],
        "media_count": len(manifest["media"]),
        "source_linked_media_count": len(manifest["source_linked_media"]),
        "two_cycle_tree_inventory_sha256": result["tree_inventory_sha256"],
    }), end="")


if __name__ == "__main__":
    main()
