#!/usr/bin/env python3
"""Bounded non-cumulative tests for the Unit 13 HTML pipeline.

The final Unit 13 POST QA receipt is intentionally allowed to be absent here.
No cumulative reader is rendered or written by this test.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import export_html_v13 as exporter
from verify_html_animated_media import figure_body


def check(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    cumulative_output = root / "output/html/unit-13"
    output_before = exporter.tree_inventory(cumulative_output) if cumulative_output.is_dir() else None

    check(r'inlineMath:[["\\(","\\)"]]' in exporter.MATHJAX_CONFIG, "MathJax inline delimiters are not JavaScript-escaped")
    check(r'displayMath:[["\\[","\\]"]]' in exporter.MATHJAX_CONFIG, "MathJax display delimiters are not JavaScript-escaped")

    baseline = exporter.unit10_baseline(root)
    check(baseline["output_inventory_sha256"] == exporter.EXPECTED_V10_OUTPUT_INVENTORY_SHA256, "Unit 10 baseline digest differs")
    check(baseline["exporter"] == exporter.EXPECTED_V10_EXPORTER, "v10 exporter changed")
    baseline_manifest = exporter.load_json_object(root / "output/html/unit-10/manifest.json")
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
    check({int(path.parent.name[-2:]) for path in sources} == set(range(1, 14)), "source inventory does not span exactly Units 1--13")
    for unit in range(1, 14):
        tag = f"{unit:02d}"
        worksheet = root / f"source/units/unit-{tag}/worksheet{tag}.id.tex"
        check(exporter.source_solution_marker_indices(worksheet) == exporter.solution_indices(root, unit), f"Unit {unit} supplied-solution closure differs")

    qa_11_12 = exporter.load_live_qa_bindings(root, (11, 12))
    check(set(qa_11_12) == {"11", "12"}, "live Unit 11--12 QA binding closure differs")
    unit13_translations = exporter.unit_translation_bindings(root, 13)
    check(len(unit13_translations) == len(exporter.unit_source_files(root, 13)), "Unit 13 translation receipt closure differs")

    rights = exporter.load_media_rights(root)
    renderer = exporter.Renderer(root, rights)
    parse_files = [
        root / "source/units/unit-07/worksheet07_exercise13_solution.id.tex",
        *sorted((root / "source/units/unit-11").glob("*.id.tex")),
        *sorted((root / "source/units/unit-12").glob("*.id.tex")),
        *sorted((root / "source/units/unit-13").glob("*.id.tex")),
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
    check('data-animation-state="stopped"' in rendered, "Unit 12 embedded GIF is not static-first")
    check('data-animation-action="play"' in rendered and 'data-animation-action="stop"' in rendered, "native Play/Stop controls are absent")
    check("Unduh GIF asli" in rendered, "canonical embedded GIF download is absent")

    with tempfile.TemporaryDirectory(prefix="o011-html-v13-bounded-") as temporary:
        stage = Path(temporary)
        embedded, linked = exporter.stage_media_assets(root, stage, renderer)
        check(len(linked) == 3, "bounded linked-media staging count differs")
        for filename in ("Aufgabe75.22.1.gif", "Aufgabe75.22.2.gif", "Aufgabe79.27.gif", "Fiddler crab mobius strip.gif", "Fiddler_crab_mobius_strip.png"):
            check((stage / "assets/media" / filename).is_file(), f"bounded staged asset missing: {filename}")
        check(any(item.get("animation", {}).get("default_state") == "static_frame" for item in embedded), "staged embedded animation contract differs")

    final_post = root / "qa/unit-13/POST_CORRECTION_MATH_QA.json"
    final_gate_present = final_post.is_file()
    if final_gate_present:
        all_live = exporter.load_live_qa_bindings(root)
        check(set(all_live) == {"11", "12", "13"}, "final live QA closure differs")
        contract = exporter.generation_contract(root)
        check(len(contract["generation_bindings"]) == 21, "generation media/rights binding count differs")
    else:
        try:
            exporter.load_live_qa_bindings(root)
        except RuntimeError as exc:
            check(final_post.relative_to(root).as_posix() in str(exc), "missing final gate failure is not explicit")
        else:
            raise RuntimeError("full live QA closure unexpectedly passed without Unit 13 POST QA")

    output_after = exporter.tree_inventory(cumulative_output) if cumulative_output.is_dir() else None
    check(output_after == output_before, "bounded test changed the cumulative Unit 13 output")
    result = {
        "status": "pass",
        "scope": "bounded non-cumulative syntax/static/fragment tests",
        "unit10_inventory_sha256": baseline["output_inventory_sha256"],
        "unit10_figure_media_receipts_checked": len(baseline_manifest["figures"]),
        "source_files": len(sources),
        "new_unit_fragments_parsed": len(parse_files),
        "embedded_media_seen": len(renderer.media_used),
        "source_linked_media_seen": len(renderer.linked_media_used),
        "unit13_translation_receipts_bound": len(unit13_translations),
        "unit13_final_post_qa_present": final_gate_present,
        "mathjax_delimiters_javascript_escaped": True,
        "cumulative_export_invoked": False,
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
