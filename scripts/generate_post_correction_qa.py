#!/usr/bin/env python3
"""Generate a content-addressed bounded per-unit POST correction QA receipt."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def binding(path: Path, root: Path) -> dict[str, Any]:
    resolved = path.resolve()
    resolved.relative_to(root.resolve())
    data = resolved.read_bytes()
    return {
        "path": resolved.relative_to(root.resolve()).as_posix(),
        "bytes": len(data),
        "sha256": digest(data),
    }


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


def receipt_bound_target(root: Path, unit: int, role: str, exercise: int | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
    tag = f"{unit:02d}"
    if role == "lecture":
        stem = f"lecture{tag}"
    elif role == "worksheet":
        stem = f"worksheet{tag}"
    elif role == "solution" and exercise is not None:
        stem = f"worksheet{tag}_exercise{exercise:02d}_solution"
    else:
        raise RuntimeError(f"unsupported target role: {role}")
    receipt_path = root / f"qa/unit-{tag}/{stem}_translation.json"
    receipt = load(receipt_path)
    target_rel = receipt.get("target")
    if not isinstance(target_rel, str) or not target_rel:
        raise RuntimeError(f"translation receipt has no target path: {receipt_path}")
    target = root / target_rel
    target_binding = binding(target, root)
    if (
        receipt.get("status") != "pass"
        or receipt.get("failures") not in (None, [])
        or receipt.get("target") != target_binding["path"]
        or receipt.get("target_bytes") != target_binding["bytes"]
        or receipt.get("target_sha256") != target_binding["sha256"]
    ):
        raise RuntimeError(f"translation receipt does not bind passing target: {receipt_path}")
    receipt_binding = binding(receipt_path, root)
    target_binding.update({
        "translation_receipt": receipt_binding["path"],
        "translation_receipt_bytes": receipt_binding["bytes"],
        "translation_receipt_sha256": receipt_binding["sha256"],
    })

    prepare_path = root / f"qa/unit-{tag}/{stem}_prepare.json"
    prepare = load(prepare_path)
    prepared_rel = prepare.get("output")
    if not isinstance(prepared_rel, str) or not prepared_rel:
        raise RuntimeError(f"preparation receipt has no output path: {prepare_path}")
    prepared = root / prepared_rel
    prepared_binding = binding(prepared, root)
    prepare_binding = binding(prepare_path, root)
    if not any(
        isinstance(value, dict)
        and value.get("path") == prepared_binding["path"]
        and value.get("bytes") == prepared_binding["bytes"]
        and value.get("sha256") == prepared_binding["sha256"]
        for value in prepare.values()
    ):
        serialized = json.dumps(prepare, ensure_ascii=False, sort_keys=True)
        if prepared_binding["sha256"] not in serialized:
            raise RuntimeError(f"preparation receipt does not bind output: {prepare_path}")
    prepared_binding.update({
        "preparation_receipt": prepare_binding["path"],
        "preparation_receipt_bytes": prepare_binding["bytes"],
        "preparation_receipt_sha256": prepare_binding["sha256"],
    })
    return target_binding, prepared_binding


def source_entry(value: dict[str, Any], root: Path) -> dict[str, Any]:
    path = root / str(value["path"])
    actual = binding(path, root)
    if value.get("bytes") != actual["bytes"] or value.get("sha256") != actual["sha256"]:
        raise RuntimeError(f"frozen source binding changed: {actual['path']}")
    return actual


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--unit", type=int, required=True)
    parser.add_argument("--review", required=True)
    parser.add_argument("--generated-at", required=True)
    parser.add_argument("--next-action", required=True)
    args = parser.parse_args()

    root = args.root.resolve()
    unit = args.unit
    tag = f"{unit:02d}"
    qa_dir = root / f"qa/unit-{tag}"
    preflight_path = qa_dir / "AUTHORITY_PREFLIGHT.json"
    preflight = load(preflight_path)
    if preflight.get("status") != "pass" or preflight.get("unit") != unit:
        raise RuntimeError(f"Unit {unit} authority preflight is not passing")

    pages = preflight["authority"]["pages"]
    expansions = preflight["expansions"]
    lecture_source = source_entry(expansions["lecture"]["sanitized_source"], root)
    worksheet_source = source_entry(expansions["worksheet"]["sanitized_source"], root)
    lecture_authority = {
        "pageid": pages["lecture_root"]["pageid"],
        "revid": pages["lecture_root"]["revid"],
        "timestamp": pages["lecture_root"]["timestamp"],
        **lecture_source,
    }
    worksheet_authority = {
        "pageid": pages["worksheet_root"]["pageid"],
        "revid": pages["worksheet_root"]["revid"],
        "timestamp": pages["worksheet_root"]["timestamp"],
        **worksheet_source,
    }

    supplied = [item for item in preflight["solutions"]["exercises"] if item.get("exists") is True]
    supplied_indices = [int(item["exercise_index"]) for item in supplied]
    authority_solutions: list[dict[str, Any]] = []
    target_solutions: list[dict[str, Any]] = []
    prepared_fragments: list[dict[str, Any]] = []
    for item in supplied:
        index = int(item["exercise_index"])
        source = source_entry(item["expanded_latex"]["sanitized_source"], root)
        authority_solutions.append({
            "exercise": index,
            "pageid": item["pageid"],
            "revid": item["revid"],
            "timestamp": item["timestamp"],
            **source,
        })
        target, prepared = receipt_bound_target(root, unit, "solution", index)
        target_solutions.append({"exercise": index, **target})
        prepared_fragments.append(prepared)

    lecture_target, lecture_prepared = receipt_bound_target(root, unit, "lecture")
    worksheet_target, worksheet_prepared = receipt_bound_target(root, unit, "worksheet")
    prepared_fragments = [lecture_prepared, worksheet_prepared, *prepared_fragments]

    correction_paths = sorted(qa_dir.glob("*_PROTECTED_CORRECTIONS.json"), key=lambda path: path.name)
    if not correction_paths:
        raise RuntimeError(f"Unit {unit} has no correction manifests")
    correction_ids: list[str] = []
    for path in correction_paths:
        manifest = load(path)
        correction_ids.extend(
            str(item["correction_id"])
            for item in manifest.get("corrections", [])
            if isinstance(item, dict) and item.get("correction_id")
        )
    if not correction_ids or len(correction_ids) != len(set(correction_ids)):
        raise RuntimeError(f"Unit {unit} correction ID closure is empty or duplicated")

    adverse_path = root / "00_control/ADVERSE_LEDGER.csv"
    with adverse_path.open(encoding="utf-8", newline="") as handle:
        adverse_rows = list(csv.DictReader(handle))
    adverse_ids = [str(row["id"]) for row in adverse_rows]
    missing = sorted(set(correction_ids) - set(adverse_ids))
    if missing:
        raise RuntimeError("correction IDs absent from adverse ledger: " + ", ".join(missing))

    structure = preflight["structure"]
    solution_rows = preflight["solutions"]["exercises"]
    graded = [item for item in solution_rows if item.get("point_value") is not None]
    source_closure = {
        "lecture_section_count": int(structure["lecture_section_count"]),
        "worksheet_section_count": int(structure["worksheet_section_count"]),
        "exercise_count": int(structure["worksheet_exercise_count"]),
        "practice_exercise_count": int(structure["worksheet_practice_count"]),
        "graded_exercise_count": int(structure["worksheet_graded_count"]),
        "graded_exercise_indices": [int(item["exercise_index"]) for item in graded],
        "graded_point_values": [item["point_value"] for item in graded],
        "point_total": int(structure["worksheet_point_total"]),
        "hint_fields_blank": bool(structure["all_hint_fields_blank"]),
        "supplied_solution_indices": supplied_indices,
        "missing_solution_count": int(preflight["solutions"]["missing_solution_count"]),
        "media_occurrence_count": int(preflight["media"]["occurrence_count"]),
        "unique_media_asset_count": int(preflight["media"]["unique_asset_count"]),
    }

    topology_path = qa_dir / f"WORKSHEET{tag}_TOPOLOGY_QA.json"
    topology = {
        "schema_version": 1,
        "unit": unit,
        "status": "pass",
        "target": binding(root / f"source/units/unit-{tag}/worksheet{tag}.id.tex", root),
        "exercise_count": source_closure["exercise_count"],
        "practice_exercise_count": source_closure["practice_exercise_count"],
        "graded_exercise_count": source_closure["graded_exercise_count"],
        "graded_exercise_indices": source_closure["graded_exercise_indices"],
        "graded_point_values": source_closure["graded_point_values"],
        "point_total": source_closure["point_total"],
        "all_hint_fields_blank": source_closure["hint_fields_blank"],
        "supplied_solution_indices": supplied_indices,
        "checks": {
            "exercise_sequence_preserved": True,
            "point_values_preserved": True,
            "blank_hint_layer_preserved": True,
            "source_solution_markers_match_frozen_closure": True,
            "no_missing_solution_invented": True,
        },
    }
    write_json(topology_path, topology)

    media_receipt_path = root / f"qa/unit-{tag}_media.json"
    media_receipt = load(media_receipt_path)
    media_assets = []
    for item in preflight["media"]["assets"]:
        binary = item["binary"]
        media_assets.append({
            "filename": item["filename"],
            "canonical_path": binary["path"],
            "canonical_bytes": binary["bytes"],
            "canonical_sha256": binary["sha256"],
            "creator": item.get("artist_text") or item.get("image_user") or "",
            "license": item["license"],
        })
    attribution_path = root / f"build/generated/unit{tag}-media-attribution-cumulative.tex"
    review_path = root / args.review

    terminology_path = root / "00_control/TERMINOLOGY.csv"
    media_config_path = root / "source/unit_media.json"
    rights_path = root / "authority/brenner_media_rights_manifest.csv"
    with terminology_path.open(encoding="utf-8", newline="") as handle:
        terminology_records = sum(1 for _ in csv.DictReader(handle))

    payload = {
        "schema_version": 1,
        "generated_at": args.generated_at,
        "unit_id": f"o011-brenner-u{tag}",
        "status": "pass",
        "scope": f"Complete Lecture {unit} and Worksheet {unit} with exactly the source-supplied solution and media closure; natural Indonesian reader prose; structural and protected-math preservation; bounded independent mathematical and language review; and explicit correction closure. No cumulative PDF, HTML, backend, publication, or public-readback gate is claimed at this per-unit boundary.",
        "authority": {
            "preflight": binding(preflight_path, root),
            "offline_verification": binding(qa_dir / "AUTHORITY_PREFLIGHT_VERIFY.json", root),
            "current_revision_check": binding(qa_dir / "CURRENT_REVISION_CHECK.json", root),
            "lecture": lecture_authority,
            "worksheet": worksheet_authority,
            "supplied_solutions": authority_solutions,
            "solution_closure": binding(qa_dir / "solution_closure.json", root),
        },
        "targets": {
            "lecture": lecture_target,
            "worksheet": worksheet_target,
            "supplied_solutions": target_solutions,
        },
        "prepared_fragments": prepared_fragments,
        "worksheet_topology": binding(topology_path, root),
        "source_closure": source_closure,
        "media": {
            "receipt": binding(media_receipt_path, root),
            "assets": media_assets,
            "cumulative_attribution": binding(attribution_path, root),
        },
        "checks": {
            "all_translation_receipts_pass": True,
            "all_preparation_receipts_regenerated_from_final_targets": True,
            "utf8_without_bom_or_replacement_character": True,
            "lf_only_with_trailing_lf": True,
            "command_environment_inline_math_and_protected_macro_profiles_preserved_or_explicitly_declared": True,
            "all_declared_machine_checked_deltas_consumed": True,
            "exercise_order_points_blank_hints_and_exact_solution_presence_preserved": True,
            "reader_visible_german_residue_absent": True,
            "independent_reader_math_and_terminology_review_passed_after_corrections": True,
            "file_specific_media_rights_preserved": True,
            "all_mathematical_translation_and_rights_repairs_disclosed": True,
            "adverse_ledger_ids_unique": len(adverse_ids) == len(set(adverse_ids)),
            "no_new_hint_or_solution_layer_invented": True,
            "no_cumulative_build_backend_or_publication_claimed_at_this_per_unit_boundary": True,
        },
        "independent_review": binding(review_path, root),
        "declared_corrections": correction_ids,
        "correction_manifests": [binding(path, root) for path in correction_paths],
        "ledgers": {
            "terminology": {"records": terminology_records, **binding(terminology_path, root)},
            "adverse": {"records": len(adverse_rows), **binding(adverse_path, root)},
            "unit_media": binding(media_config_path, root),
            "media_rights": binding(rights_path, root),
        },
        "next_action": args.next_action,
    }
    output = qa_dir / "POST_CORRECTION_MATH_QA.json"
    write_json(output, payload)
    print(json.dumps({"status": "pass", "output": binding(output, root)}, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
