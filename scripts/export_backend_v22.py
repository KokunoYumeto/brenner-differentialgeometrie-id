#!/usr/bin/env python3
"""Append the deterministic O011 Units 20--22 backend to the public Unit 19 prefix."""

from __future__ import annotations

import argparse
import copy
import csv
import io
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import export_backend_v19 as v19  # noqa: E402


WORKFLOW = "o011-export-backend-v22"
VERIFY_WORKFLOW = "o011-verify-backend-v22"
UNITS = (20, 21, 22)
BASELINE_RECORD_COUNT = 3747
BASELINE_JSONL_BYTES = 2316959
BASELINE_JSONL_SHA256 = "8045e59c84bc8c70fc3275bc65d023e46848276b184aca5978bd9b015060c193"
BASELINE_CSV_LINES = 3748
BASELINE_CSV_BYTES = 850266
BASELINE_CSV_SHA256 = "b63d9d673b841869ab2d848e3a21b5b256a765c2b29f3e9982385e0ad3d75e1b"
BASELINE_EXERCISE_COUNT = 394
BASELINE_SOURCE_SOLUTION_COUNT = 54
EXPECTED_UNIT_CENSUS: dict[int, dict[str, Any]] = {
    20: {"lecture_sections": 2, "worksheet_sections": 2, "exercises": 24, "practice": 19, "graded": 5, "points": 22, "solutions": [3, 4, 5, 7, 14], "assets": 0},
    21: {"lecture_sections": 2, "worksheet_sections": 2, "exercises": 20, "practice": 15, "graded": 5, "points": 24, "solutions": [7, 10, 12, 13], "assets": 3},
    22: {"lecture_sections": 3, "worksheet_sections": 2, "exercises": 19, "practice": 15, "graded": 4, "points": 16, "solutions": [6], "assets": 2},
}
EXTENSION_EXERCISE_COUNT = sum(int(value["exercises"]) for value in EXPECTED_UNIT_CENSUS.values())
EXTENSION_SOURCE_SOLUTION_COUNT = sum(len(value["solutions"]) for value in EXPECTED_UNIT_CENSUS.values())
FINAL_EXERCISE_COUNT = BASELINE_EXERCISE_COUNT + EXTENSION_EXERCISE_COUNT
FINAL_SOURCE_SOLUTION_COUNT = BASELINE_SOURCE_SOLUTION_COUNT + EXTENSION_SOURCE_SOLUTION_COUNT
DEFAULT_TRANSLATION_STATE = "mathematically_reviewed"

v10 = v19.v10
sha256_bytes = v19.sha256_bytes
canonical_json = v19.canonical_json
binding = v19.binding
load_json = v19.load_json
CSV_FIELDS = v19.CSV_FIELDS
ENTITY_TYPES = v19.ENTITY_TYPES
unit_ids = v19.unit_ids
base_record = v19.base_record
add_relation = v19.add_relation
correction_record_id = v19.correction_record_id

MEDIA_CORRECTION_ID = "O011-ACC-0310"
MEDIA_MANIFEST_NAME = "MEDIA22_PROTECTED_CORRECTIONS.json"
MEDIA_ALIAS_PATHS = {
    "adverse_ledger": "00_control/ADVERSE_LEDGER.csv",
    "alias_receipt": "qa/unit-22/MEDIA_ALIAS_RECEIPT.json",
    "inner_source": "authority/media/Inner point.png",
    "inner_alias": "build/generated/media/Inner_point.png",
    "partition_source": "build/generated/media/Partition of unity illustration.png",
    "partition_alias": "build/generated/media/Partition_of_unity_illustration.png",
}
MEDIA_ALIAS_SPECS = (
    ("o011-artifact-u22-inner-point-loader-alias", "o011-asset-file-u22-inner-point-png", "inner_source", "inner_alias"),
    ("o011-artifact-u22-partition-of-unity-loader-alias", "o011-asset-file-u22-partition-of-unity-illustration-svg", "partition_source", "partition_alias"),
)
UNIT21_ALIAS_PATHS = {
    "adverse_ledger": "00_control/ADVERSE_LEDGER.csv",
    "independent_review": "qa/unit-21/INDEPENDENT_READER_QA.md",
    "alias_receipt": "qa/unit-21/MEDIA_ALIAS_RECEIPT.json",
    "runge_source": "build/generated/media/Runge theorem.png",
    "runge_alias": "build/generated/media/Runge_theorem.png",
    "circle_source": "build/generated/media/Circle on sphere wireframe 10deg 6r.png",
    "circle_alias": "build/generated/media/Circle_on_sphere_wireframe_10deg_6r.png",
}
UNIT21_ALIAS_SPECS = (
    ("o011-artifact-u21-runge-theorem-loader-alias", "o011-asset-file-u21-runge-theorem-svg", "runge_source", "runge_alias"),
    ("o011-artifact-u21-circle-on-sphere-loader-alias", "o011-asset-file-u21-circle-on-sphere-wireframe-10deg-6r-svg", "circle_source", "circle_alias"),
)
UNIT21_LATE_CORRECTIONS = {
    "O011-CORR-0295": ("solution10", "Clarify that the boundary coordinate is nonpositive while the path parameter is negative, giving the required quotient sign."),
    "O011-TRANS-0296": ("lecture", "Use the admitted Indonesian terms for Hausdorff space and open cover."),
    "O011-TRANS-0297": ("lecture", "Use Indonesian noun-adjective order for closed box."),
    "O011-TRANS-0298": ("worksheet", "Use the admitted Indonesian term for unit sphere."),
}


def all_correction_ids(context: dict[str, Any]) -> list[str]:
    values = list(context["math_qa"]["all_declared_corrections"])
    if int(context["unit"]) == 21:
        values.extend(["O011-ACC-0294", *UNIT21_LATE_CORRECTIONS])
    return values


def assert_prefix(root: Path) -> tuple[bytes, bytes, list[dict[str, Any]]]:
    jsonl = (root / "backend/records.jsonl").read_bytes()
    lines = jsonl.splitlines(keepends=True)
    if len(lines) < BASELINE_RECORD_COUNT:
        raise RuntimeError("backend has fewer than the immutable 3,747-record Unit 19 prefix")
    jsonl_prefix = b"".join(lines[:BASELINE_RECORD_COUNT])
    if len(jsonl_prefix) != BASELINE_JSONL_BYTES or sha256_bytes(jsonl_prefix) != BASELINE_JSONL_SHA256:
        raise RuntimeError("immutable public Unit 19 JSONL prefix changed")
    csv_bytes = (root / "backend/records.csv").read_bytes()
    csv_lines = csv_bytes.splitlines(keepends=True)
    if len(csv_lines) < BASELINE_CSV_LINES:
        raise RuntimeError("backend CSV has fewer than the immutable Unit 19 prefix")
    csv_prefix = b"".join(csv_lines[:BASELINE_CSV_LINES])
    if len(csv_prefix) != BASELINE_CSV_BYTES or sha256_bytes(csv_prefix) != BASELINE_CSV_SHA256:
        raise RuntimeError("immutable public Unit 19 CSV prefix changed")
    baseline = [json.loads(line.decode("utf-8")) for line in lines[:BASELINE_RECORD_COUNT]]
    return jsonl_prefix, csv_prefix, baseline


def surface_only_context(context: dict[str, Any]) -> dict[str, Any]:
    """Return the ordinary translated-surface view, excluding Unit 22's build-alias correction."""
    if int(context["unit"]) != 22:
        return context
    result = copy.deepcopy(context)
    manifests = list(context["math_qa"]["correction_manifests"])
    surface_positions = [index for index, value in enumerate(manifests, 1) if Path(str(value["path"])).name != MEDIA_MANIFEST_NAME]
    result["math_qa"]["correction_manifests"] = [manifests[index - 1] for index in surface_positions]
    result["math_qa"]["declared_corrections"] = [value for value in context["math_qa"]["declared_corrections"] if value != MEDIA_CORRECTION_ID]
    result["math_qa"]["all_declared_corrections"] = list(result["math_qa"]["declared_corrections"])
    for new_index, old_index in enumerate(surface_positions, 1):
        result["paths"][f"correction_manifest:{new_index:02d}"] = context["paths"][f"correction_manifest:{old_index:02d}"]
        result["bindings"][f"correction_manifest:{new_index:02d}"] = context["bindings"][f"correction_manifest:{old_index:02d}"]
    return result


def prepare_unit(root: Path, unit: int) -> dict[str, Any]:
    previous = v19.EXPECTED_UNIT_CENSUS
    previous_validator = v10.validate_unit_inputs
    v19.EXPECTED_UNIT_CENSUS = EXPECTED_UNIT_CENSUS
    v10.validate_unit_inputs = lambda candidate_root, context: previous_validator(candidate_root, surface_only_context(context))
    try:
        context = v19.prepare_unit(root, unit)
    finally:
        v19.EXPECTED_UNIT_CENSUS = previous
        v10.validate_unit_inputs = previous_validator
    if unit == 22:
        manifest_positions = [index for index, value in enumerate(context["math_qa"]["correction_manifests"], 1) if Path(str(value["path"])).name == MEDIA_MANIFEST_NAME]
        if manifest_positions != [2] or MEDIA_CORRECTION_ID not in context["math_qa"]["all_declared_corrections"]:
            raise RuntimeError("Unit 22 media-alias correction identity/order changed")
        context["media_manifest_binding"] = context["bindings"]["correction_manifest:02"]
        for key, relative in MEDIA_ALIAS_PATHS.items():
            path = root / relative
            if not path.is_file():
                raise RuntimeError(f"Unit 22 media-alias evidence is missing: {relative}")
            context["paths"][f"media_alias:{key}"] = path
            context["bindings"][f"media_alias:{key}"] = binding(path, root)
        receipt = load_json(context["paths"]["media_alias:alias_receipt"])
        receipt_by_target = {str(value["target"]): value for value in receipt.get("aliases", []) if value.get("transient") is False}
        for _, _, source_key, alias_key in MEDIA_ALIAS_SPECS:
            source = context["bindings"][f"media_alias:{source_key}"]
            alias = context["bindings"][f"media_alias:{alias_key}"]
            declared = receipt_by_target.get(alias["path"])
            if declared is None or declared.get("source") != source["path"] or declared.get("bytes") != alias["bytes"] or declared.get("sha256") != alias["sha256"] or source["sha256"] != alias["sha256"]:
                raise RuntimeError(f"Unit 22 media-alias receipt is stale: {alias['path']}")
    if unit == 21:
        for key, relative in UNIT21_ALIAS_PATHS.items():
            path = root / relative
            if not path.is_file():
                raise RuntimeError(f"Unit 21 late-correction evidence is missing: {relative}")
            context["paths"][f"unit21_late:{key}"] = path
            context["bindings"][f"unit21_late:{key}"] = binding(path, root)
        receipt = load_json(context["paths"]["unit21_late:alias_receipt"])
        receipt_by_target = {str(value["target"]): value for value in receipt.get("aliases", []) if value.get("transient") is False}
        for _, _, source_key, alias_key in UNIT21_ALIAS_SPECS:
            source = context["bindings"][f"unit21_late:{source_key}"]
            alias = context["bindings"][f"unit21_late:{alias_key}"]
            declared = receipt_by_target.get(alias["path"])
            if declared is None or declared.get("source") != source["path"] or declared.get("bytes") != alias["bytes"] or declared.get("sha256") != alias["sha256"] or source["sha256"] != alias["sha256"]:
                raise RuntimeError(f"Unit 21 media-alias receipt is stale: {alias['path']}")
    return context


def add_unit21_late_records(context: dict[str, Any], records: list[dict[str, Any]], checkpoint: str, state: str) -> None:
    unit_id, lecture_id, worksheet_id = unit_ids(21)
    bindings = context["bindings"]
    receipt = bindings["unit21_late:alias_receipt"]
    evidence = [bindings["unit21_late:adverse_ledger"], bindings["unit21_late:independent_review"]]
    receipt_artifact = "o011-artifact-u21-media-alias-receipt"
    records.append(base_record(receipt_artifact, "artifact", checkpoint, artifact_kind="deterministic_media_loader_alias_receipt", bytes=receipt["bytes"], path=receipt["path"], media_type="application/json", parent_id=unit_id, rights_component_id=v19.TEXT_RIGHTS_ID, component_rights_ids=[v19.TEXT_RIGHTS_ID], target_sha256=receipt["sha256"], translation_state=state))
    add_relation(records, checkpoint, f"o011-rel-{receipt_artifact}-evidences-target", "evidences", receipt_artifact, unit_id)
    alias_ids: list[str] = []
    alias_bindings: list[dict[str, Any]] = []
    alias_validation: list[dict[str, Any]] = [receipt]
    for artifact_id, parent_id, source_key, alias_key in UNIT21_ALIAS_SPECS:
        source = bindings[f"unit21_late:{source_key}"]
        alias = bindings[f"unit21_late:{alias_key}"]
        alias_ids.append(artifact_id)
        alias_bindings.append({**alias, "target_id": artifact_id})
        alias_validation.extend([source, alias])
        records.append(base_record(artifact_id, "artifact", checkpoint, artifact_kind="deterministic_media_loader_alias", bytes=alias["bytes"], path=alias["path"], media_type="image/png", parent_id=parent_id, source_sha256=source["sha256"], target_sha256=alias["sha256"], rights_component_id=v19.TEXT_RIGHTS_ID, component_rights_ids=[v19.TEXT_RIGHTS_ID], translation_state=state))
        add_relation(records, checkpoint, f"o011-rel-{artifact_id}-represents-target", "represents", artifact_id, parent_id)
    alias_record_id = correction_record_id("O011-ACC-0294")
    records.append(base_record(alias_record_id, "correction", checkpoint, source_local_id="O011-ACC-0294", severity="P1", description="Create exact hash-identical persistent loader aliases for the Unit 21 SVG print derivatives.", disposition="Persistent aliases repair MediaWiki loader-name normalization without changing derivative bytes or component rights", correction_status="build_structure_repaired", upstream_report_disposition="not_upstream_source_issue", target_ids=sorted(alias_ids), target_bindings=sorted(alias_bindings, key=lambda value: str(value["target_id"])), correction_manifests=[], legacy_correction_evidence=evidence + [receipt], validation_bindings=alias_validation, post_correction_qa_binding=bindings["math_qa"]))
    for position, target_id in enumerate(sorted(alias_ids), 1):
        add_relation(records, checkpoint, f"o011-rel-{alias_record_id}-corrects-{position:02d}", "corrects", alias_record_id, target_id)

    target_map = {
        "lecture": (lecture_id, bindings["lecture_target"], bindings["lecture_receipt"]),
        "worksheet": (worksheet_id, bindings["worksheet_target"], bindings["worksheet_receipt"]),
        "solution10": (f"{worksheet_id}-e010-solution", bindings["solution10_target"], bindings["solution10_receipt"]),
    }
    for correction_id, (scope, description) in UNIT21_LATE_CORRECTIONS.items():
        target_id, target_binding, target_receipt = target_map[scope]
        record_id = correction_record_id(correction_id)
        records.append(base_record(record_id, "correction", checkpoint, source_local_id=correction_id, severity="P1" if correction_id == "O011-CORR-0295" else "P2", description=description, disposition="Corrected in the Indonesian target and independently verified", correction_status="corrected_in_target", upstream_report_disposition="deferred_until_full_corpus", target_ids=[target_id], target_bindings=[{**target_binding, "target_id": target_id}], correction_manifests=[], legacy_correction_evidence=evidence, validation_bindings=[target_receipt], post_correction_qa_binding=bindings["math_qa"]))
        add_relation(records, checkpoint, f"o011-rel-{record_id}-corrects-01", "corrects", record_id, target_id)
    closure = next(record for record in records if record.get("id") == "o011-qa-unit21-correction-closure")
    closure["values"] = {"correction_ids": all_correction_ids(context)}


def add_media_alias_records(context: dict[str, Any], records: list[dict[str, Any]], checkpoint: str, state: str) -> None:
    tag = str(context["tag"])
    unit_id, _, _ = unit_ids(22)
    bindings = context["bindings"]
    # The surface-only generator numbered the worksheet manifest as 02. Restore
    # the declared Unit 22 order: lecture=01, media=02, worksheet=03.
    old_artifact = f"o011-artifact-u{tag}-correction-manifest-02"
    new_artifact = f"o011-artifact-u{tag}-correction-manifest-03"
    old_relation = f"o011-rel-{old_artifact}-evidences-target"
    new_relation = f"o011-rel-{new_artifact}-evidences-target"
    for record in records:
        if record.get("id") == old_artifact:
            record["id"] = new_artifact
        elif record.get("id") == old_relation:
            record["id"] = new_relation
            record["from_id"] = new_artifact

    media_manifest = context["media_manifest_binding"]
    records.append(base_record(
        old_artifact,
        "artifact",
        checkpoint,
        artifact_kind="build_media_alias_correction_manifest",
        bytes=media_manifest["bytes"],
        path=media_manifest["path"],
        media_type="application/json",
        parent_id=unit_id,
        rights_component_id=v19.TEXT_RIGHTS_ID,
        component_rights_ids=[v19.TEXT_RIGHTS_ID],
        target_sha256=media_manifest["sha256"],
        translation_state=state,
    ))
    add_relation(records, checkpoint, old_relation, "evidences", old_artifact, unit_id)

    receipt = bindings["media_alias:alias_receipt"]
    receipt_artifact = "o011-artifact-u22-media-alias-receipt"
    records.append(base_record(
        receipt_artifact,
        "artifact",
        checkpoint,
        artifact_kind="deterministic_media_loader_alias_receipt",
        bytes=receipt["bytes"],
        path=receipt["path"],
        media_type="application/json",
        parent_id=unit_id,
        rights_component_id=v19.TEXT_RIGHTS_ID,
        component_rights_ids=[v19.TEXT_RIGHTS_ID],
        target_sha256=receipt["sha256"],
        translation_state=state,
    ))
    add_relation(records, checkpoint, f"o011-rel-{receipt_artifact}-evidences-target", "evidences", receipt_artifact, unit_id)

    target_ids: list[str] = []
    target_bindings: list[dict[str, Any]] = []
    validation_bindings: list[dict[str, Any]] = [receipt]
    for artifact_id, parent_id, source_key, alias_key in MEDIA_ALIAS_SPECS:
        source = bindings[f"media_alias:{source_key}"]
        alias = bindings[f"media_alias:{alias_key}"]
        target_ids.append(artifact_id)
        target_bindings.append({**alias, "target_id": artifact_id})
        validation_bindings.extend([source, alias])
        records.append(base_record(
            artifact_id,
            "artifact",
            checkpoint,
            artifact_kind="deterministic_media_loader_alias",
            bytes=alias["bytes"],
            path=alias["path"],
            media_type="image/png",
            parent_id=parent_id,
            source_sha256=source["sha256"],
            target_sha256=alias["sha256"],
            rights_component_id=v19.TEXT_RIGHTS_ID,
            component_rights_ids=[v19.TEXT_RIGHTS_ID],
            translation_state=state,
        ))
        add_relation(records, checkpoint, f"o011-rel-{artifact_id}-represents-target", "represents", artifact_id, parent_id)

    record_id = correction_record_id(MEDIA_CORRECTION_ID)
    records.append(base_record(
        record_id,
        "correction",
        checkpoint,
        source_local_id=MEDIA_CORRECTION_ID,
        severity="P1",
        description="Create deterministic hash-bound loader aliases for the exact rights-closed Unit 22 media assets.",
        disposition="Persistent aliases repair MediaWiki loader-name normalization without changing canonical media bytes or attribution",
        correction_status="build_structure_repaired",
        upstream_report_disposition="not_upstream_source_issue",
        target_ids=sorted(target_ids),
        target_bindings=sorted(target_bindings, key=lambda value: str(value["target_id"])),
        correction_manifests=[media_manifest],
        legacy_correction_evidence=[bindings["media_alias:adverse_ledger"], receipt],
        validation_bindings=validation_bindings,
        post_correction_qa_binding=bindings["math_qa"],
    ))
    for position, target_id in enumerate(sorted(target_ids), 1):
        add_relation(records, checkpoint, f"o011-rel-{record_id}-corrects-{position:02d}", "corrects", record_id, target_id)
    closure = next(record for record in records if record.get("id") == "o011-qa-unit22-correction-closure")
    closure["values"] = {"correction_ids": context["math_qa"]["all_declared_corrections"]}


def prepare_bundle(root: Path, checkpoint: str, state: str) -> dict[str, Any]:
    jsonl_prefix, csv_prefix, baseline = assert_prefix(root)
    contexts = [prepare_unit(root, unit) for unit in UNITS]
    previous_workflow = v10.WORKFLOW
    v10.WORKFLOW = WORKFLOW
    try:
        suffix: list[dict[str, Any]] = []
        for context in contexts:
            unit_records = v10.make_unit_records(surface_only_context(context), checkpoint, state)
            if int(context["unit"]) == 21:
                add_unit21_late_records(context, unit_records, checkpoint, state)
            if int(context["unit"]) == 22:
                add_media_alias_records(context, unit_records, checkpoint, state)
            context["records"] = unit_records
            suffix.extend(unit_records)
    finally:
        v10.WORKFLOW = previous_workflow
    counts = v10.validate_records(baseline, suffix, load_json(root / "backend/schema/o011-record-v1.schema.json"))
    exercises = sum(int(context["preflight"]["structure"]["worksheet_exercise_count"]) for context in contexts)
    solutions = sum(len(context["solution_indices"]) for context in contexts)
    if exercises != EXTENSION_EXERCISE_COUNT or BASELINE_EXERCISE_COUNT + exercises != FINAL_EXERCISE_COUNT:
        raise RuntimeError("cumulative exercise census changed")
    if solutions != EXTENSION_SOURCE_SOLUTION_COUNT or BASELINE_SOURCE_SOLUTION_COUNT + solutions != FINAL_SOURCE_SOLUTION_COUNT:
        raise RuntimeError("cumulative source-supplied-solution census changed")
    inputs: dict[str, dict[str, Any]] = {"schema": binding(root / "backend/schema/o011-record-v1.schema.json", root)}
    for context in contexts:
        for key, value in context["bindings"].items():
            inputs[f"u{context['tag']}:{key}"] = value
    return {"jsonl_prefix": jsonl_prefix, "csv_prefix": csv_prefix, "baseline": baseline, "contexts": contexts, "suffix": suffix, "counts": counts, "inputs": inputs}


def unit_manifest(context: dict[str, Any], state: str) -> dict[str, Any]:
    result = v10.unit_manifest(context, state)
    result["correction_ids"] = all_correction_ids(context)
    supplemental = ["O011-ACC-0294", *UNIT21_LATE_CORRECTIONS] if int(context["unit"]) == 21 else []
    result["legacy_unmanifested_correction_ids"] = supplemental
    result["supplemental_compatibility_correction_ids"] = supplemental
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--translation-state", default=DEFAULT_TRANSLATION_STATE)
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    if args.translation_state not in {"translated", "structurally_verified", "mathematically_reviewed", "language_reviewed", "built", "visually_checked"}:
        raise RuntimeError("unsupported Units 20--22 translation state")
    root = args.root.resolve()
    bundle = prepare_bundle(root, args.checkpoint, args.translation_state)
    units = {context["tag"]: unit_manifest(context, args.translation_state) for context in bundle["contexts"]}
    summary = {"status": "pass", "baseline_records": BASELINE_RECORD_COUNT, "added_records": len(bundle["suffix"]), "combined_records": BASELINE_RECORD_COUNT + len(bundle["suffix"]), "entity_counts": bundle["counts"], "units": units}
    if args.check_only:
        summary["check_only"] = True
        print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
        return

    jsonl_path = root / "backend/records.jsonl"
    csv_path = root / "backend/records.csv"
    jsonl_path.write_bytes(bundle["jsonl_prefix"] + b"".join(canonical_json(record) for record in bundle["suffix"]))
    csv_buffer = io.StringIO(newline="")
    writer = csv.DictWriter(csv_buffer, fieldnames=CSV_FIELDS, extrasaction="ignore", lineterminator="\r\n")
    for record in bundle["suffix"]:
        writer.writerow({field: record.get(field) for field in CSV_FIELDS})
    csv_path.write_bytes(bundle["csv_prefix"] + csv_buffer.getvalue().encode("utf-8"))
    outputs = {"records_jsonl": binding(jsonl_path, root), "records_csv": binding(csv_path, root)}
    manifest = {
        "schema_version": 1,
        "workflow": WORKFLOW,
        "checkpoint": args.checkpoint,
        "generator": binding(root / "scripts/export_backend_v22.py", root),
        "verifier": binding(root / "scripts/verify_backend_v22.py", root),
        "baseline": {"record_count": BASELINE_RECORD_COUNT, "jsonl_bytes": BASELINE_JSONL_BYTES, "jsonl_sha256": BASELINE_JSONL_SHA256, "csv_lines_including_header": BASELINE_CSV_LINES, "csv_bytes": BASELINE_CSV_BYTES, "csv_sha256": BASELINE_CSV_SHA256, "preserved_byte_identically": True},
        "units20_22_extension": {"record_count": len(bundle["suffix"]), "entity_counts": bundle["counts"], "units": units, "model_identification": v19.MODEL_IDENTIFICATION, "exercise_count": EXTENSION_EXERCISE_COUNT, "source_supplied_solution_count": EXTENSION_SOURCE_SOLUTION_COUNT},
        "inputs": bundle["inputs"],
        "outputs": outputs,
        "combined": {"record_count": BASELINE_RECORD_COUNT + len(bundle["suffix"]), "entity_counts": {kind: Counter(str(record.get("entity_type")) for record in bundle["baseline"] + bundle["suffix"]).get(kind, 0) for kind in sorted(ENTITY_TYPES)}},
        "claims": {"all_ids_unique": True, "all_references_resolve": True, "json_schema_valid": True, "unit19_public_prefix_byte_identical": True, "units20_22_authority_solution_media_closure_current": True, "units20_22_translation_receipts_current": True, "units20_22_correction_manifests_current": True, "units20_22_post_correction_math_qa_current": True, "cumulative_exercises_457": True, "cumulative_source_supplied_solutions_64": True},
    }
    manifest_path = root / "backend/MANIFEST.json"
    manifest_path.write_bytes((json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    summary.update({"jsonl": outputs["records_jsonl"], "csv": outputs["records_csv"], "manifest": binding(manifest_path, root)})
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
