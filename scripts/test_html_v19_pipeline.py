#!/usr/bin/env python3
"""Bounded non-cumulative tests for the Unit 19 HTML pipeline.

The final Unit 18/19 POST QA receipts are intentionally allowed to be absent here.
No cumulative reader is rendered or written by this test.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import export_html_v19 as exporter
from verify_html_animated_media import figure_body


def check(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    cumulative_output = root / "output/html/unit-19"
    output_before = exporter.tree_inventory(cumulative_output) if cumulative_output.is_dir() else None

    for immutable_unit in (10, 13, 16):
        try:
            exporter.assert_output_path(root, root / f"output/html/unit-{immutable_unit}")
        except RuntimeError as exc:
            check("immutable" in str(exc), f"Unit {immutable_unit} output refusal is not explicit")
        else:
            raise RuntimeError(f"published Unit {immutable_unit} output is not protected from replacement")

    check(r'inlineMath:[["\\(","\\)"]]' in exporter.MATHJAX_CONFIG, "MathJax inline delimiters are not JavaScript-escaped")
    check(r'displayMath:[["\\[","\\]"]]' in exporter.MATHJAX_CONFIG, "MathJax display delimiters are not JavaScript-escaped")

    baseline = exporter.unit13_baseline(root)
    check(baseline["output_inventory_sha256"] == exporter.EXPECTED_V13_OUTPUT_INVENTORY_SHA256, "Unit 13 baseline digest differs")
    check(baseline["exporter"] == exporter.EXPECTED_V13_EXPORTER, "v13 exporter changed")
    baseline_manifest = exporter.load_json_object(root / "output/html/unit-13/manifest.json")
    baseline_media = {item["filename"]: item for item in baseline_manifest["media"]}
    prefix_renderer = exporter.Renderer(root, exporter.load_media_rights(root))
    for figure in baseline_manifest["figures"]:
        unit = int(str(figure["id"]).split("-u", 1)[1][:2])
        prefix_renderer._verify_unit_media_receipt(
            str(figure["filename"]),
            unit,
            baseline_media[str(figure["filename"])]["source"],
        )

    sources = exporter.source_files(root)
    check(len(sources) == len(set(sources)), "cumulative source inventory contains duplicates")
    check({int(path.parent.name[-2:]) for path in sources} == set(range(1, 20)), "source inventory does not span exactly Units 1--19")
    for unit in range(1, 20):
        tag = f"{unit:02d}"
        worksheet = root / f"source/units/unit-{tag}/worksheet{tag}.id.tex"
        check(exporter.source_solution_marker_indices(worksheet) == exporter.solution_indices(root, unit), f"Unit {unit} supplied-solution closure differs")

    unit14_19_translations = {
        unit: exporter.unit_translation_bindings(root, unit) for unit in range(14, 20)
    }
    for unit, bindings in unit14_19_translations.items():
        check(len(bindings) == len(exporter.unit_source_files(root, unit)), f"Unit {unit} translation receipt closure differs")

    rights = exporter.load_media_rights(root)
    renderer = exporter.Renderer(root, rights)
    parse_files = [
        root / "source/units/unit-07/worksheet07_exercise13_solution.id.tex",
        *sorted((root / "source/units/unit-11").glob("*.id.tex")),
        *sorted((root / "source/units/unit-12").glob("*.id.tex")),
        *sorted((root / "source/units/unit-13").glob("*.id.tex")),
        *sorted((root / "source/units/unit-14").glob("*.id.tex")),
        *sorted((root / "source/units/unit-15").glob("*.id.tex")),
        *sorted((root / "source/units/unit-16").glob("*.id.tex")),
        *sorted((root / "source/units/unit-17").glob("*.id.tex")),
        *sorted((root / "source/units/unit-18").glob("*.id.tex")),
        *sorted((root / "source/units/unit-19").glob("*.id.tex")),
    ]
    rendered_fragments: list[str] = []
    for path in parse_files:
        unit = int(path.parent.name[-2:])
        rendered_fragments.append(
            renderer.render_flow(
                path.read_text(encoding="utf-8"),
                exporter.SurfaceState(unit, path.stem, f"bounded-{unit:02d}-{path.stem}"),
            )
        )
    rendered = "\n".join(rendered_fragments)
    check("[[File:" not in rendered and "[[Datei:" not in rendered, "source-linked file residue remains")
    check("Konstruktion der Objekte" not in rendered and "Variation von S" not in rendered, "German animation label remains visible")
    check(set(renderer.linked_media_used) == {"Aufgabe75.22.1.gif", "Aufgabe75.22.2.gif", "Aufgabe79.27.gif"}, "source-linked media set differs")
    check(len(renderer.linked_media_occurrences) == 3, "source-linked media occurrence count differs")
    check("Fiddler crab mobius strip.gif" in renderer.media_used, "Unit 12 embedded GIF was not admitted")
    check("Georg Friedrich Bernhard Riemann.jpeg" in renderer.media_used, "Unit 16 Riemann portrait was not admitted")
    check("Sphere with three handles.png" in renderer.media_used, "Unit 16 genus-three surface was not admitted")
    check("Cilinderprojectie-constructie.jpg" in renderer.media_used, "Unit 17 cylindrical-projection figure was not admitted")
    check("Poincarehalfplaneconform.gif" in renderer.media_used, "Unit 18 Poincare animation was not admitted")
    check("Hyperboloid2.png" in renderer.media_used, "Unit 18 hyperboloid figure was not admitted")
    check(rendered.count('data-animation-state="stopped"') == 2, "the two embedded GIFs are not both static-first")
    check('data-animation-action="play"' in rendered and 'data-animation-action="stop"' in rendered, "native Play/Stop controls are absent")
    check("Unduh GIF asli" in rendered, "canonical embedded GIF download is absent")

    with tempfile.TemporaryDirectory(prefix="o011-html-v19-bounded-") as temporary:
        stage = Path(temporary)
        embedded, linked = exporter.stage_media_assets(root, stage, renderer)
        check(len(linked) == 3, "bounded linked-media staging count differs")
        for filename in ("Aufgabe75.22.1.gif", "Aufgabe75.22.2.gif", "Aufgabe79.27.gif", "Fiddler crab mobius strip.gif", "Fiddler_crab_mobius_strip.png", "Georg Friedrich Bernhard Riemann.jpeg", "Sphere with three handles.png", "Cilinderprojectie-constructie.jpg", "Poincarehalfplaneconform.gif", "Poincarehalfplaneconform.png", "Hyperboloid2.png"):
            check((stage / "assets/media" / filename).is_file(), f"bounded staged asset missing: {filename}")
        animations = [item.get("animation") for item in embedded if isinstance(item.get("animation"), dict)]
        check(len(animations) == 2 and all(item.get("default_state") == "static_frame" for item in animations), "staged embedded animation contract differs")

    final_posts = [root / f"qa/unit-{unit:02d}/POST_CORRECTION_MATH_QA.json" for unit in range(14, 20)]
    final_gate_present = all(path.is_file() for path in final_posts)
    if final_gate_present:
        all_live = exporter.load_live_qa_bindings(root)
        check(set(all_live) == {"14", "15", "16", "17", "18", "19"}, "final live QA closure differs")
        contract = exporter.generation_contract(root)
        check(len(contract["generation_bindings"]) == 28, "generation media/rights binding count differs")
    else:
        try:
            exporter.load_live_qa_bindings(root)
        except RuntimeError as exc:
            check("POST_CORRECTION_MATH_QA.json" in str(exc), "missing final gate failure is not explicit")
        else:
            raise RuntimeError("full live QA closure unexpectedly passed without all Unit 14--19 POST QA receipts")

    output_after = exporter.tree_inventory(cumulative_output) if cumulative_output.is_dir() else None
    check(output_after == output_before, "bounded test changed the cumulative Unit 19 output")
    result = {
        "status": "pass",
        "scope": "bounded non-cumulative syntax/static/fragment tests",
        "unit13_inventory_sha256": baseline["output_inventory_sha256"],
        "unit13_figure_media_receipts_checked": len(baseline_manifest["figures"]),
        "source_files": len(sources),
        "new_unit_fragments_parsed": len(parse_files),
        "embedded_media_seen": len(renderer.media_used),
        "source_linked_media_seen": len(renderer.linked_media_used),
        "unit14_19_translation_receipts_bound": sum(len(value) for value in unit14_19_translations.values()),
        "unit14_19_final_post_qa_present": final_gate_present,
        "mathjax_delimiters_javascript_escaped": True,
        "cumulative_export_invoked": False,
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
