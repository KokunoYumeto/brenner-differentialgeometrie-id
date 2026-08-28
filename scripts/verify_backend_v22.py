#!/usr/bin/env python3
"""Verify the cumulative O011 backend through Unit 22 and repeat-export determinism."""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import export_backend_v22 as exporter  # noqa: E402


def expected_csv(prefix: bytes, suffix: list[dict[str, Any]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=exporter.CSV_FIELDS, extrasaction="ignore", lineterminator="\r\n")
    for record in suffix:
        writer.writerow({field: record.get(field) for field in exporter.CSV_FIELDS})
    return prefix + buffer.getvalue().encode("utf-8")


def validate_references(records: list[dict[str, Any]]) -> None:
    ids = {str(record["id"]) for record in records}
    for record in records:
        for key in ("parent_id", "resource_id", "edition_id", "rights_component_id", "target_id", "artifact_id", "from_id", "to_id"):
            value = record.get(key)
            if value is not None and value not in ids:
                raise RuntimeError(f"unresolved {key}={value!r} in {record['id']}")
        for key in ("component_rights_ids", "target_ids"):
            for value in record.get(key) or []:
                if value not in ids:
                    raise RuntimeError(f"unresolved {key} member {value!r} in {record['id']}")


def validate_state(root: Path) -> dict[str, Any]:
    manifest_path = root / "backend/MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    extension = manifest.get("units20_22_extension", {})
    checkpoint = str(manifest["checkpoint"])
    states = {str(value["translation_state"]) for value in extension.get("units", {}).values()}
    if len(states) != 1:
        raise RuntimeError("manifest has inconsistent Units 20--22 translation states")
    bundle = exporter.prepare_bundle(root, checkpoint, states.pop())
    jsonl_path = root / "backend/records.jsonl"
    csv_path = root / "backend/records.csv"
    lines = jsonl_path.read_bytes().splitlines(keepends=True)
    records = [json.loads(line.decode("utf-8")) for line in lines]
    if len(records) != exporter.BASELINE_RECORD_COUNT + len(bundle["suffix"]):
        raise RuntimeError("combined JSONL record count changed")
    prefix = b"".join(lines[: exporter.BASELINE_RECORD_COUNT])
    if len(prefix) != exporter.BASELINE_JSONL_BYTES or exporter.sha256_bytes(prefix) != exporter.BASELINE_JSONL_SHA256:
        raise RuntimeError("Unit 19 JSONL prefix changed")
    suffix = records[exporter.BASELINE_RECORD_COUNT :]
    if suffix != bundle["suffix"] or any(line != exporter.canonical_json(record) for line, record in zip(lines[exporter.BASELINE_RECORD_COUNT :], suffix)):
        raise RuntimeError("JSONL suffix is not the canonical reconstructed extension")
    if len({str(record["id"]) for record in records}) != len(records):
        raise RuntimeError("duplicate stable IDs")
    validate_references(records)
    exporter.v10.validate_records(bundle["baseline"], suffix, exporter.load_json(root / "backend/schema/o011-record-v1.schema.json"))
    csv_bytes = csv_path.read_bytes()
    csv_lines = csv_bytes.splitlines(keepends=True)
    csv_prefix = b"".join(csv_lines[: exporter.BASELINE_CSV_LINES])
    if len(csv_prefix) != exporter.BASELINE_CSV_BYTES or exporter.sha256_bytes(csv_prefix) != exporter.BASELINE_CSV_SHA256:
        raise RuntimeError("Unit 19 CSV prefix changed")
    if csv_bytes != expected_csv(csv_prefix, suffix):
        raise RuntimeError("CSV is not the exact projection of JSONL")

    if manifest.get("workflow") != exporter.WORKFLOW or manifest.get("generator") != exporter.binding(root / "scripts/export_backend_v22.py", root) or manifest.get("verifier") != exporter.binding(root / "scripts/verify_backend_v22.py", root):
        raise RuntimeError("manifest workflow/script binding changed")
    if manifest.get("inputs") != bundle["inputs"] or manifest.get("outputs", {}).get("records_jsonl") != exporter.binding(jsonl_path, root) or manifest.get("outputs", {}).get("records_csv") != exporter.binding(csv_path, root):
        raise RuntimeError("manifest input/output binding changed")
    if manifest.get("combined", {}).get("record_count") != len(records):
        raise RuntimeError("manifest combined census changed")
    expected_counts = Counter(str(record.get("entity_type")) for record in records)
    if manifest.get("combined", {}).get("entity_counts") != {kind: expected_counts.get(kind, 0) for kind in sorted(exporter.ENTITY_TYPES)}:
        raise RuntimeError("manifest combined entity counts changed")

    by_id = {str(record["id"]): record for record in records}
    for context in bundle["contexts"]:
        unit = int(context["unit"])
        tag = str(context["tag"])
        structure = context["preflight"]["structure"]
        solution_indices = tuple(context["solution_indices"])
        unit_id, _, worksheet_id = exporter.unit_ids(unit)
        unit_record = by_id[unit_id]
        source_hash = exporter.sha256_bytes(context["paths"]["lecture_source"].read_bytes() + context["paths"]["worksheet_source"].read_bytes())
        target_hash = exporter.sha256_bytes(context["paths"]["lecture_target"].read_bytes() + context["paths"]["worksheet_target"].read_bytes())
        if unit_record.get("source_sha256") != source_hash or unit_record.get("target_sha256") != target_hash:
            raise RuntimeError(f"Unit {tag} aggregate source/target hash changed")
        source_exercises = exporter.v10.marker_slices(context["paths"]["worksheet_source"].read_text(encoding="utf-8"), r"\\inputaufgabe(?:gibtloesung)?")
        target_exercises = exporter.v10.marker_slices(context["paths"]["worksheet_target"].read_text(encoding="utf-8"), r"\\inputaufgabe(?:gibtloesung)?")
        if len(source_exercises) != structure["worksheet_exercise_count"] or len(target_exercises) != structure["worksheet_exercise_count"]:
            raise RuntimeError(f"Unit {tag} exercise topology changed")
        solution_meta = {int(item["exercise_index"]): item for item in context["preflight"]["solutions"]["exercises"]}
        for index, (source_part, target_part) in enumerate(zip(source_exercises, target_exercises), 1):
            exercise = by_id[f"{worksheet_id}-e{index:03d}"]
            if exercise.get("source_sha256") != exporter.sha256_bytes(source_part.encode()) or exercise.get("target_sha256") != exporter.sha256_bytes(target_part.encode()):
                raise RuntimeError(f"Unit {tag} exercise {index} segment hash changed")
            if exercise.get("has_authority_solution") != (index in solution_indices) or exercise.get("hint_present") is not False or exercise.get("point_value") != solution_meta[index].get("point_value"):
                raise RuntimeError(f"Unit {tag} exercise {index} solution/hint/point identity changed")
        for index in solution_indices:
            solution = by_id[f"{worksheet_id}-e{index:03d}-solution"]
            if solution.get("unit_kind") != "source_supplied_solution" or solution.get("parent_id") != f"{worksheet_id}-e{index:03d}":
                raise RuntimeError(f"Unit {tag} solution {index} identity changed")
        unit_assets = [record for record in suffix if record.get("entity_type") == "asset" and str(record.get("id", "")).startswith(f"o011-asset-file-u{tag}-")]
        unit_rights = [record for record in suffix if record.get("entity_type") == "rights" and str(record.get("id", "")).startswith(f"o011-rights-media-u{tag}-")]
        expected_assets = len(context["preflight"].get("media", {}).get("assets", []))
        if len(unit_assets) != expected_assets or len(unit_rights) != expected_assets:
            raise RuntimeError(f"Unit {tag} media/rights identity count changed")
        for asset in unit_assets:
            actual = exporter.binding(root / str(asset["path"]), root)
            if asset.get("source_sha256") != actual["sha256"] or asset.get("expected_bytes") != actual["bytes"]:
                raise RuntimeError(f"Unit {tag} media binding changed: {asset['id']}")
        expected_corrections = set(context["math_qa"]["all_declared_corrections"])
        corrections = [record for record in suffix if record.get("entity_type") == "correction" and record.get("source_local_id") in expected_corrections]
        if {str(record["source_local_id"]) for record in corrections} != expected_corrections:
            raise RuntimeError(f"Unit {tag} correction identity closure changed")
        for record in corrections:
            if not record.get("target_bindings") or not record.get("correction_manifests") or not record.get("validation_bindings"):
                raise RuntimeError(f"incomplete correction record: {record['id']}")
            for value in record["target_bindings"] + record["correction_manifests"] + record["validation_bindings"]:
                path = root / str(value["path"])
                if not path.is_file() or exporter.binding(path, root)["sha256"] != value.get("sha256"):
                    raise RuntimeError(f"stale correction evidence: {record['id']}")

    with (root / "00_control/ADVERSE_LEDGER.csv").open("r", encoding="utf-8-sig", newline="") as handle:
        adverse = list(csv.DictReader(handle))
    adverse_numbers = [int(match.group(1)) for row in adverse if (match := re.fullmatch(r"O011-[A-Z]+-(\d{4})", str(row.get("id", ""))))]
    correction_records = [record for record in records if record.get("entity_type") == "correction"]
    correction_numbers = [int(match.group(1)) for record in correction_records if (match := re.fullmatch(r"o011-(?:adv|corr)-(\d{4})", str(record.get("id", ""))))]
    if len(adverse_numbers) != len(adverse) or len(correction_numbers) != len(correction_records) or Counter(adverse_numbers) != Counter(correction_numbers):
        raise RuntimeError("backend/adverse correction-number closure differs")

    return {"manifest": manifest, "records": records, "suffix": suffix, "bundle": bundle, "jsonl": exporter.binding(jsonl_path, root), "csv": exporter.binding(csv_path, root), "manifest_binding": exporter.binding(manifest_path, root)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    root = args.root.resolve()
    manifest = json.loads((root / "backend/MANIFEST.json").read_text(encoding="utf-8"))
    checkpoint = str(manifest["checkpoint"])
    states = {str(value["translation_state"]) for value in manifest["units20_22_extension"]["units"].values()}
    if len(states) != 1:
        raise RuntimeError("cannot repeat export with inconsistent unit states")
    state = states.pop()
    command = [sys.executable, str(root / "scripts/export_backend_v22.py"), "--root", str(root), "--checkpoint", checkpoint, "--translation-state", state]
    completed = subprocess.run(command, cwd=root, capture_output=True, text=True, encoding="utf-8")
    if completed.returncode != 0:
        raise RuntimeError(f"first repeat exporter failed: {completed.stderr.strip() or completed.stdout.strip()}")
    first = validate_state(root)
    completed = subprocess.run(command, cwd=root, capture_output=True, text=True, encoding="utf-8")
    if completed.returncode != 0:
        raise RuntimeError(f"second repeat exporter failed: {completed.stderr.strip() or completed.stdout.strip()}")
    second = validate_state(root)
    for key in ("jsonl", "csv", "manifest_binding"):
        if first[key] != second[key]:
            raise RuntimeError(f"repeat export changed {key}")
    census = {}
    for context in second["bundle"]["contexts"]:
        structure = context["preflight"]["structure"]
        census[context["tag"]] = {"lecture_sections": structure["lecture_section_count"], "worksheet_sections": structure["worksheet_section_count"], "exercises": structure["worksheet_exercise_count"], "practice_exercises": structure["worksheet_practice_count"], "graded_exercises": structure["worksheet_graded_count"], "graded_point_total": structure["worksheet_point_total"], "source_solution_indices": list(context["solution_indices"]), "assets": len(context["preflight"].get("media", {}).get("assets", [])), "correction_ids": context["math_qa"]["all_declared_corrections"]}
    receipt = {
        "schema_version": 1, "workflow": exporter.VERIFY_WORKFLOW, "status": "pass", "checkpoint": checkpoint,
        "baseline": {"records": exporter.BASELINE_RECORD_COUNT, "jsonl_bytes": exporter.BASELINE_JSONL_BYTES, "jsonl_sha256": exporter.BASELINE_JSONL_SHA256, "csv_prefix_bytes": exporter.BASELINE_CSV_BYTES, "csv_prefix_sha256": exporter.BASELINE_CSV_SHA256, "preserved_byte_identically": True},
        "units20_22_extension": {"records": len(second["suffix"]), "entity_counts": second["bundle"]["counts"], "census": census, "exercise_count": exporter.EXTENSION_EXERCISE_COUNT, "source_supplied_solution_count": exporter.EXTENSION_SOURCE_SOLUTION_COUNT},
        "cumulative_census": {"exercises": exporter.FINAL_EXERCISE_COUNT, "source_supplied_solutions": exporter.FINAL_SOURCE_SOLUTION_COUNT},
        "combined_records": len(second["records"]),
        "outputs": {"records_jsonl": second["jsonl"], "records_csv": second["csv"], "manifest": second["manifest_binding"]},
        "determinism": {"first_jsonl_sha256": first["jsonl"]["sha256"], "first_csv_sha256": first["csv"]["sha256"], "first_manifest_sha256": first["manifest_binding"]["sha256"], "second_export_matches_first": True},
        "checks": {"immutable_public_unit19_prefix": True, "canonical_jsonl": True, "csv_projection_exact": True, "combined_json_schema_valid": True, "all_ids_unique": True, "all_references_resolve": True, "live_input_hash_bindings_current": True, "source_target_segment_hashes_current": True, "exercise_solution_hint_point_closure": True, "media_rights_closure_current": True, "correction_manifest_target_bindings_current": True, "adverse_ledger_backend_correction_closure_current": True, "repeat_export_deterministic": True},
    }
    receipt_path = root / "qa/unit-22/backend.json"
    receipt_path.write_bytes((json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    print(json.dumps({"status": "pass", "records": len(second["records"]), "jsonl": second["jsonl"], "csv": second["csv"], "manifest": second["manifest_binding"], "receipt": exporter.binding(receipt_path, root)}, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
