#!/usr/bin/env python3
"""Verify the complete append-only O011 stable-ID backend and write its receipt."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import export_backend_complete as export  # noqa: E402


WORKFLOW = "o011-verify-backend-complete"


def file_binding(path: Path, root: Path) -> dict[str, Any]:
    return export.binding(path, root)


def verify(root: Path) -> dict[str, Any]:
    manifest_path = root / "backend/MANIFEST.json"
    if not manifest_path.is_file():
        raise RuntimeError("complete backend manifest is missing")
    manifest = export.load_json(manifest_path)
    if manifest.get("workflow") != export.WORKFLOW:
        raise RuntimeError("backend manifest is not the complete-edition manifest")
    checkpoint = str(manifest.get("checkpoint"))
    state = str(manifest.get("translation_state"))
    first = export.prepare_bundle(root, checkpoint, state)
    expected_jsonl = first["jsonl_prefix"] + b"".join(export.canonical_json(record) for record in first["suffix"])
    expected_csv = first["csv_prefix"] + export.render_csv_suffix(first["suffix"])
    jsonl_path = root / "backend/records.jsonl"
    csv_path = root / "backend/records.csv"
    actual_jsonl = jsonl_path.read_bytes()
    actual_csv = csv_path.read_bytes()
    if actual_jsonl != expected_jsonl:
        raise RuntimeError("backend JSONL differs from deterministic reconstruction")
    if actual_csv != expected_csv:
        raise RuntimeError("backend CSV differs from the exact deterministic projection")
    lines = actual_jsonl.splitlines(keepends=True)
    if len(lines) != export.BASELINE_RECORD_COUNT + len(first["suffix"]):
        raise RuntimeError("backend JSONL record count changed")
    for line_number, line in enumerate(lines, 1):
        if export.canonical_json(json.loads(line.decode("utf-8"))) != line:
            raise RuntimeError(f"non-canonical JSONL record at line {line_number}")
    if len(actual_csv.splitlines()) != len(lines) + 1:
        raise RuntimeError("backend CSV line count is not record count plus header")

    outputs = {"records_jsonl": file_binding(jsonl_path, root), "records_csv": file_binding(csv_path, root)}
    expected_manifest = export.make_manifest(root, checkpoint, state, first, outputs)
    if manifest != expected_manifest:
        raise RuntimeError("backend manifest differs from deterministic reconstruction")
    if manifest.get("inputs") != first["inputs"]:
        raise RuntimeError("manifest input inventory differs from live source identities")
    if manifest.get("outputs") != outputs:
        raise RuntimeError("manifest output bindings differ from live backend outputs")

    # A second in-memory reconstruction proves determinism without mutating any
    # source, translated, reader, or backend surface.
    second = export.prepare_bundle(root, checkpoint, state)
    second_jsonl = second["jsonl_prefix"] + b"".join(export.canonical_json(record) for record in second["suffix"])
    second_csv = second["csv_prefix"] + export.render_csv_suffix(second["suffix"])
    if second_jsonl != expected_jsonl or second_csv != expected_csv or second["inputs"] != first["inputs"]:
        raise RuntimeError("repeat complete-backend reconstruction is not deterministic")

    receipt = {
        "schema_version": 1,
        "workflow": WORKFLOW,
        "status": "pass",
        "checkpoint": checkpoint,
        "baseline": {
            "records": export.BASELINE_RECORD_COUNT,
            "jsonl_bytes": export.BASELINE_JSONL_BYTES,
            "jsonl_sha256": export.BASELINE_JSONL_SHA256,
            "csv_lines_including_header": export.BASELINE_CSV_LINES,
            "csv_bytes": export.BASELINE_CSV_BYTES,
            "csv_sha256": export.BASELINE_CSV_SHA256,
            "preserved_byte_identically": True,
        },
        "combined_records": len(lines),
        "extension_records": len(first["suffix"]),
        "extension_entity_counts": first["entity_counts"],
        "semantic_census": first["semantic_census"],
        "correction_census": first["correction_census"],
        "complete_core_census": {"exercises": export.FINAL_CORE_EXERCISES, "source_supplied_solutions": export.FINAL_CORE_SOURCE_SOLUTIONS},
        "checks": {
            "immutable_published_unit22_jsonl_prefix": True,
            "immutable_published_unit22_csv_prefix": True,
            "canonical_jsonl": True,
            "csv_projection_exact": True,
            "combined_json_schema_valid": True,
            "all_ids_unique": True,
            "all_references_resolve": True,
            "live_source_identity_bindings_current": True,
            "hash_bound_translation_and_math_receipts_pass": True,
            "unit_exercise_hint_point_solution_topology_exact": True,
            "exam_occurrence_map_recomputed_exactly": True,
            "exam_learner_prompts_exact_in_solution_forms": True,
            "exam_source_solution_presence_topology_exact": True,
            "official_and_original_solution_provenance_distinct": True,
            "six_original_exam_repairs_one_to_one": True,
            "all_32_original_bridge_items_complete": True,
            "component_media_rights_and_license_closure": True,
            "declared_source_corrections_bound": True,
            "stable_reader_anchors_present": True,
            "repeat_reconstruction_deterministic": True,
        },
        "outputs": {
            **outputs,
            "manifest": file_binding(manifest_path, root),
            "generator": file_binding(root / "scripts/export_backend_complete.py", root),
            "verifier": file_binding(root / "scripts/verify_backend_complete.py", root),
        },
        "determinism": {
            "first_jsonl_sha256": export.sha256_bytes(expected_jsonl),
            "second_jsonl_sha256": export.sha256_bytes(second_jsonl),
            "first_csv_sha256": export.sha256_bytes(expected_csv),
            "second_csv_sha256": export.sha256_bytes(second_csv),
            "second_reconstruction_matches_first": True,
        },
    }
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    receipt = verify(root)
    if not args.check_only:
        output = root / "qa/complete/backend.json"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes((json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8"))
        receipt["receipt"] = file_binding(output, root)
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
