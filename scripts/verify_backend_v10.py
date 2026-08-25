#!/usr/bin/env python3
"""Independent repeat-export verifier for the O011 Units 8--10 backend."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

sys.path.insert(0, str(Path(__file__).resolve().parent))
import export_backend_v10 as exporter  # noqa: E402


VERIFY_WORKFLOW = "o011-verify-backend-v10"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def binding(path: Path, root: Path) -> dict[str, Any]:
    data = path.read_bytes()
    return {"path": path.relative_to(root).as_posix(), "bytes": len(data), "sha256": sha256_bytes(data)}


def canonical_json(record: dict[str, Any]) -> bytes:
    return exporter.canonical_json(record)


def expected_csv(prefix: bytes, suffix: list[dict[str, Any]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=exporter.CSV_FIELDS, extrasaction="ignore", lineterminator="\r\n")
    for record in suffix:
        writer.writerow({field: record.get(field) for field in exporter.CSV_FIELDS})
    return prefix + buffer.getvalue().encode("utf-8")


def validate_references(records: list[dict[str, Any]]) -> None:
    all_ids = {str(record["id"]) for record in records}
    if len(all_ids) != len(records):
        raise RuntimeError("combined backend IDs are not unique")
    for record in records:
        for key in ("parent_id", "resource_id", "edition_id", "rights_component_id", "target_id", "artifact_id", "from_id", "to_id"):
            value = record.get(key)
            if value is not None and str(value) not in all_ids:
                raise RuntimeError(f"unresolved {key} on {record['id']}: {value}")
        for key in ("component_rights_ids", "target_ids"):
            for value in record.get(key, []) or []:
                if str(value) not in all_ids:
                    raise RuntimeError(f"unresolved {key} on {record['id']}: {value}")


def validate_state(root: Path) -> dict[str, Any]:
    manifest_path = root / "backend/MANIFEST.json"
    jsonl_path = root / "backend/records.jsonl"
    csv_path = root / "backend/records.csv"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("workflow") != exporter.WORKFLOW:
        raise RuntimeError("backend manifest is not the v10 workflow")
    extension = manifest.get("units08_10_extension", {})
    reader_bound = extension.get("reader_status") == "cumulative_html_pdf_reader_bound"
    expected_reader_status = "cumulative_html_pdf_reader_bound" if reader_bound else "not_bound_by_semantic_backend_export"
    expected_html_status = "cumulative_html_reader_bound" if reader_bound else "not_bound_by_semantic_backend_export"
    expected_pdf_status = "cumulative_pdf_reader_bound" if reader_bound else "not_bound_by_semantic_backend_export"
    if (
        extension.get("reader_status") != expected_reader_status
        or extension.get("html_status") != expected_html_status
        or extension.get("pdf_status") != expected_pdf_status
    ):
        raise RuntimeError("semantic exporter reader/HTML/PDF status is inconsistent")
    units_manifest = extension.get("units", {})
    if set(units_manifest) != {"08", "09", "10"}:
        raise RuntimeError("backend manifest does not contain exactly Units 8--10")
    states = {str(value.get("translation_state")) for value in units_manifest.values()}
    if len(states) != 1:
        raise RuntimeError("Units 8--10 manifest has inconsistent translation states")
    state = states.pop()
    checkpoint = str(manifest.get("checkpoint"))

    jsonl = jsonl_path.read_bytes()
    lines = jsonl.splitlines(keepends=True)
    if int(extension.get("record_count", -1)) != exporter.EXPECTED_EXTENSION_RECORD_COUNT:
        raise RuntimeError("frozen Units 8--10 extension record count changed")
    expected_count = exporter.BASELINE_RECORD_COUNT + int(extension.get("record_count", -1))
    if expected_count != exporter.EXPECTED_COMBINED_RECORD_COUNT:
        raise RuntimeError("frozen combined record count changed")
    if len(lines) != expected_count:
        raise RuntimeError("combined JSONL record count disagrees with manifest")
    prefix = b"".join(lines[: exporter.BASELINE_RECORD_COUNT])
    if len(prefix) != exporter.BASELINE_JSONL_BYTES or sha256_bytes(prefix) != exporter.BASELINE_JSONL_SHA256:
        raise RuntimeError("immutable Units 1--7 JSONL prefix changed")
    records = [json.loads(line.decode("utf-8")) for line in lines]
    suffix = records[exporter.BASELINE_RECORD_COUNT :]
    if any(line != canonical_json(record) for line, record in zip(lines[exporter.BASELINE_RECORD_COUNT :], suffix)):
        raise RuntimeError("noncanonical Units 8--10 JSONL record")
    if [str(record["id"]) for record in suffix] != sorted(str(record["id"]) for record in suffix):
        raise RuntimeError("Units 8--10 suffix IDs are not sorted")
    validate_references(records)

    schema = json.loads((root / "backend/schema/o011-record-v1.schema.json").read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors: list[str] = []
    for record in records:
        errors.extend(f"{record['id']}: {error.message}" for error in validator.iter_errors(record))
    if errors:
        raise RuntimeError("JSON Schema validation failed: " + "; ".join(errors[:10]))

    csv_bytes = csv_path.read_bytes()
    csv_lines = csv_bytes.splitlines(keepends=True)
    csv_prefix = b"".join(csv_lines[: exporter.BASELINE_CSV_LINES])
    if len(csv_lines) != exporter.BASELINE_CSV_LINES + len(suffix):
        raise RuntimeError("combined CSV line count disagrees with the JSONL suffix")
    if len(csv_prefix) != exporter.BASELINE_CSV_BYTES or sha256_bytes(csv_prefix) != exporter.BASELINE_CSV_SHA256:
        raise RuntimeError("immutable Units 1--7 CSV prefix changed")
    if csv_bytes != expected_csv(csv_prefix, suffix):
        raise RuntimeError("CSV is not the exact deterministic projection of the JSONL suffix")

    # Reconstruct the complete suffix from live authority, target, correction,
    # and QA evidence and require exact byte identity with the generated view.
    bundle = exporter.prepare_bundle(root, checkpoint, state)
    live_reader_bound = bool(bundle["contexts"][-1].get("reader_bound"))
    if live_reader_bound is not reader_bound:
        raise RuntimeError("manifest reader state disagrees with the live six-file closure")
    if not reader_bound:
        raise RuntimeError("final cumulative HTML/PDF reader closure is not bound")
    reconstructed_jsonl = b"".join(canonical_json(record) for record in bundle["suffix"])
    if b"".join(lines[exporter.BASELINE_RECORD_COUNT :]) != reconstructed_jsonl:
        raise RuntimeError("live reconstruction differs from the stored Units 8--10 JSONL suffix")
    if csv_bytes != expected_csv(csv_prefix, bundle["suffix"]):
        raise RuntimeError("live reconstruction differs from the stored CSV suffix")
    if manifest.get("inputs") != bundle["inputs"]:
        raise RuntimeError("manifest input bindings are stale")
    if extension.get("entity_counts") != bundle["counts"]:
        raise RuntimeError("manifest extension entity counts are stale")
    if extension.get("entity_counts") != exporter.EXPECTED_EXTENSION_ENTITY_COUNTS:
        raise RuntimeError("frozen Units 8--10 entity census changed")
    for context in bundle["contexts"]:
        tag = context["tag"]
        if units_manifest.get(tag) != exporter.unit_manifest(context, state):
            raise RuntimeError(f"manifest Unit {tag} census is stale")
    expected_reader_closure = exporter.reader_closure_manifest(bundle["contexts"][-1])
    if manifest.get("reader_closure") != expected_reader_closure:
        raise RuntimeError("manifest cumulative reader closure is stale")

    expected_baseline = {
        "record_count": exporter.BASELINE_RECORD_COUNT,
        "jsonl_bytes": exporter.BASELINE_JSONL_BYTES,
        "jsonl_sha256": exporter.BASELINE_JSONL_SHA256,
        "csv_lines_including_header": exporter.BASELINE_CSV_LINES,
        "csv_bytes": exporter.BASELINE_CSV_BYTES,
        "csv_sha256": exporter.BASELINE_CSV_SHA256,
        "preserved_byte_identically": True,
    }
    if manifest.get("baseline") != expected_baseline:
        raise RuntimeError("manifest immutable-prefix declaration is stale")
    if extension.get("model_identification") != exporter.MODEL_IDENTIFICATION:
        raise RuntimeError("model provenance changed")
    claims = manifest.get("claims", {})
    for key in (
        "cumulative_html_present",
        "cumulative_html_manifest_and_qa_current",
        "cumulative_pdf_present",
        "cumulative_pdf_structural_qa_current",
        "cumulative_pdf_visual_qa_current",
    ):
        if claims.get(key) is not reader_bound:
            raise RuntimeError(f"semantic backend reader claim disagrees with the all-or-nothing closure: {key}")
    for key in (
        "all_ids_unique", "all_references_resolve", "json_schema_valid",
        "units08_10_authority_solution_media_closure_current",
        "units08_10_translation_receipts_current",
        "units08_10_correction_manifests_current",
        "units08_10_post_correction_math_qa_current",
        "units1_7_prefix_byte_identical",
        "cumulative_reader_all_or_nothing",
    ):
        if claims.get(key) is not True:
            raise RuntimeError(f"required backend claim missing: {key}")

    if manifest.get("outputs", {}).get("records_jsonl") != binding(jsonl_path, root):
        raise RuntimeError("manifest JSONL output binding is stale")
    if manifest.get("outputs", {}).get("records_csv") != binding(csv_path, root):
        raise RuntimeError("manifest CSV output binding is stale")
    if manifest.get("generator") != binding(root / "scripts/export_backend_v10.py", root):
        raise RuntimeError("manifest exporter binding is stale")
    if manifest.get("verifier") != binding(root / "scripts/verify_backend_v10.py", root):
        raise RuntimeError("manifest verifier binding is stale")
    expected_combined_count = exporter.BASELINE_RECORD_COUNT + len(suffix)
    if manifest.get("combined", {}).get("record_count") != expected_combined_count:
        raise RuntimeError("manifest combined record count is stale")
    combined_counts = Counter(str(record.get("entity_type")) for record in records)
    expected_combined_counts = {kind: combined_counts.get(kind, 0) for kind in sorted(exporter.ENTITY_TYPES)}
    if manifest.get("combined", {}).get("entity_counts") != expected_combined_counts:
        raise RuntimeError("manifest combined entity counts are stale")

    by_id = {str(record["id"]): record for record in records}
    for context in bundle["contexts"]:
        unit = int(context["unit"]); tag = str(context["tag"])
        structure = context["preflight"]["structure"]
        solution_indices = tuple(context["solution_indices"])
        unit_id, lecture_id, worksheet_id = exporter.unit_ids(unit)
        unit_record = by_id[unit_id]
        aggregate_source = sha256_bytes(context["paths"]["lecture_source"].read_bytes() + context["paths"]["worksheet_source"].read_bytes())
        aggregate_target = sha256_bytes(context["paths"]["lecture_target"].read_bytes() + context["paths"]["worksheet_target"].read_bytes())
        if unit_record.get("source_sha256") != aggregate_source or unit_record.get("target_sha256") != aggregate_target:
            raise RuntimeError(f"Unit {tag} aggregate source/target binding changed")
        if unit_record.get("translation_assistance", {}).get("model") != exporter.MODEL_IDENTIFICATION or unit_record.get("translation_assistance", {}).get("human_and_source_credits_preserved") is not True:
            raise RuntimeError(f"Unit {tag} translation provenance changed")
        source_exercises = exporter.marker_slices(context["paths"]["worksheet_source"].read_text(encoding="utf-8"), r"\\inputaufgabe(?:gibtloesung)?")
        target_exercises = exporter.marker_slices(context["paths"]["worksheet_target"].read_text(encoding="utf-8"), r"\\inputaufgabe(?:gibtloesung)?")
        if len(source_exercises) != structure["worksheet_exercise_count"] or len(target_exercises) != structure["worksheet_exercise_count"]:
            raise RuntimeError(f"Unit {tag} exercise topology changed")
        solution_meta = {int(item["exercise_index"]): item for item in context["preflight"]["solutions"]["exercises"]}
        for index, (source_part, target_part) in enumerate(zip(source_exercises, target_exercises), 1):
            exercise = by_id[f"{worksheet_id}-e{index:03d}"]
            if exercise.get("source_sha256") != sha256_bytes(source_part.encode()) or exercise.get("target_sha256") != sha256_bytes(target_part.encode()):
                raise RuntimeError(f"Unit {tag} exercise {index} segment hash changed")
            if exercise.get("has_authority_solution") != (index in solution_indices) or exercise.get("hint_present") is not False or exercise.get("point_value") != solution_meta[index].get("point_value"):
                raise RuntimeError(f"Unit {tag} exercise {index} solution/hint/point closure changed")
        for index in solution_indices:
            solution_id = f"{worksheet_id}-e{index:03d}-solution"
            if by_id[solution_id].get("unit_kind") != "source_supplied_solution" or by_id[solution_id].get("parent_id") != f"{worksheet_id}-e{index:03d}":
                raise RuntimeError(f"Unit {tag} solution {index} identity changed")

        unit_assets = [record for record in suffix if record.get("entity_type") == "asset" and str(record.get("id", "")).startswith(f"o011-asset-file-u{tag}-")]
        unit_rights = [record for record in suffix if record.get("entity_type") == "rights" and str(record.get("id", "")).startswith(f"o011-rights-media-u{tag}-")]
        expected_assets = len(context["preflight"].get("media", {}).get("assets", []))
        if len(unit_assets) != expected_assets or len(unit_rights) != expected_assets:
            raise RuntimeError(f"Unit {tag} media/rights count changed")
        for asset in unit_assets:
            path = root / str(asset["path"])
            actual = binding(path, root)
            if asset.get("source_sha256") != actual["sha256"] or asset.get("expected_bytes") != actual["bytes"]:
                raise RuntimeError(f"Unit {tag} media binding changed: {asset['id']}")

        expected_corrections = set(context["math_qa"]["declared_corrections"])
        corrections = [record for record in suffix if record.get("entity_type") == "correction" and record.get("source_local_id") in expected_corrections]
        if {str(record["source_local_id"]) for record in corrections} != expected_corrections:
            raise RuntimeError(f"Unit {tag} correction closure changed")
        for correction in corrections:
            if correction.get("correction_status") != "corrected_in_target" or not correction.get("target_bindings") or not correction.get("correction_manifests") or not correction.get("validation_bindings"):
                raise RuntimeError(f"incomplete correction record: {correction['id']}")
            for value in correction["target_bindings"] + correction["correction_manifests"] + correction["validation_bindings"]:
                path = root / str(value["path"])
                if not path.is_file() or binding(path, root)["sha256"] != value.get("sha256"):
                    raise RuntimeError(f"stale correction evidence: {correction['id']}")

        qa_events = [record for record in suffix if record.get("entity_type") == "qa_event" and str(record.get("id", "")).startswith(f"o011-qa-unit{tag}-")]
        expected_qa_count = 7 + len(solution_indices) + (1 if tag == "10" and reader_bound else 0)
        if len(qa_events) != expected_qa_count or any(record.get("result") != "pass" for record in qa_events):
            raise RuntimeError(f"Unit {tag} QA-event closure changed")
        for event in qa_events:
            path = root / str(event["receipt_path"])
            if not path.is_file() or binding(path, root)["sha256"] != event.get("evidence_sha256"):
                raise RuntimeError(f"stale QA evidence: {event['id']}")

    if reader_bound:
        reader_context = bundle["contexts"][-1]
        if not reader_context.get("reader_bound"):
            raise RuntimeError("manifest claims readers but the live all-or-nothing closure is absent")
        for artifact_id, key in (
            ("o011-artifact-u10-html-entry", "html_entry"),
            ("o011-artifact-u10-html-manifest", "html_manifest"),
            ("o011-artifact-u10-html-qa", "html_qa"),
        ):
            artifact = by_id.get(artifact_id)
            if artifact is None or artifact.get("target_sha256") != reader_context["bindings"][key]["sha256"] or artifact.get("bytes") != reader_context["bindings"][key]["bytes"]:
                raise RuntimeError(f"cumulative HTML artifact binding changed: {artifact_id}")
        closure_artifact = by_id["o011-artifact-u10-html-qa"]
        if closure_artifact.get("reader_closure") != expected_reader_closure:
            raise RuntimeError("cumulative reader artifact metadata changed")
        closure_event = by_id.get("o011-qa-unit10-html-reader")
        if (
            closure_event is None
            or closure_event.get("qa_kind") != "cumulative_semantic_html_pdf_reader"
            or closure_event.get("values") != expected_reader_closure
            or closure_event.get("receipt_path") != reader_context["bindings"]["html_qa"]["path"]
            or closure_event.get("evidence_sha256") != reader_context["bindings"]["html_qa"]["sha256"]
        ):
            raise RuntimeError("cumulative reader QA-event binding changed")

    for artifact in (record for record in suffix if record.get("entity_type") == "artifact"):
        path = root / str(artifact["path"])
        if not path.is_file():
            raise RuntimeError(f"missing artifact file: {artifact['id']}")
        actual = binding(path, root)
        if artifact.get("bytes") != actual["bytes"]:
            raise RuntimeError(f"stale artifact byte count: {artifact['id']}")
        if artifact.get("language") == "German":
            if artifact.get("source_sha256") != actual["sha256"] or artifact.get("target_sha256") is not None:
                raise RuntimeError(f"stale frozen-source artifact: {artifact['id']}")
        elif artifact.get("target_sha256") != actual["sha256"]:
            raise RuntimeError(f"stale artifact target hash: {artifact['id']}")

    return {
        "manifest": manifest, "records": records, "suffix": suffix,
        "counts": bundle["counts"], "jsonl": binding(jsonl_path, root),
        "csv": binding(csv_path, root), "manifest_binding": binding(manifest_path, root),
        "contexts": bundle["contexts"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    root = args.root.resolve()
    current_manifest = json.loads((root / "backend/MANIFEST.json").read_text(encoding="utf-8"))
    checkpoint = str(current_manifest["checkpoint"])
    unit_states = {str(value["translation_state"]) for value in current_manifest["units08_10_extension"]["units"].values()}
    if len(unit_states) != 1:
        raise RuntimeError("cannot repeat export with inconsistent unit states")
    state = unit_states.pop()
    command = [sys.executable, str(root / "scripts/export_backend_v10.py"), "--root", str(root), "--checkpoint", checkpoint, "--translation-state", state]
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

    census: dict[str, Any] = {}
    for context in second["contexts"]:
        structure = context["preflight"]["structure"]
        census[context["tag"]] = {
            "lecture_sections": structure["lecture_section_count"],
            "worksheet_sections": structure["worksheet_section_count"],
            "exercises": structure["worksheet_exercise_count"],
            "source_solution_indices": list(context["solution_indices"]),
            "source_solution_absent_indices": [index for index in range(1, structure["worksheet_exercise_count"] + 1) if index not in context["solution_indices"]],
            "hint_indices": [], "graded_point_total": structure["worksheet_point_total"],
            "assets": len(context["preflight"].get("media", {}).get("assets", [])),
            "correction_ids": context["math_qa"]["declared_corrections"],
        }
    receipt = {
        "schema_version": 1, "workflow": VERIFY_WORKFLOW, "status": "pass", "checkpoint": checkpoint,
        "baseline": {"records": exporter.BASELINE_RECORD_COUNT, "jsonl_bytes": exporter.BASELINE_JSONL_BYTES, "jsonl_sha256": exporter.BASELINE_JSONL_SHA256, "csv_prefix_bytes": exporter.BASELINE_CSV_BYTES, "csv_prefix_sha256": exporter.BASELINE_CSV_SHA256, "preserved_byte_identically": True},
        "units08_10_extension": {"records": len(second["suffix"]), "entity_counts": second["counts"], "census": census, "model_identification": exporter.MODEL_IDENTIFICATION, "html_reader_bound": second["manifest"]["claims"]["cumulative_html_present"], "pdf_reader_bound": second["manifest"]["claims"]["cumulative_pdf_present"]},
        "reader_closure": second["manifest"]["reader_closure"],
        "combined_records": len(second["records"]),
        "outputs": {"records_jsonl": second["jsonl"], "records_csv": second["csv"], "manifest": second["manifest_binding"]},
        "determinism": {"first_jsonl_sha256": first["jsonl"]["sha256"], "first_csv_sha256": first["csv"]["sha256"], "first_manifest_sha256": first["manifest_binding"]["sha256"], "second_export_matches_first": True},
        "checks": {"immutable_units1_7_prefix": True, "canonical_jsonl": True, "csv_projection_exact": True, "combined_json_schema_valid": True, "all_ids_unique": True, "all_references_resolve": True, "live_input_bindings_current": True, "source_target_segment_hashes_current": True, "solution_hint_point_media_closure": True, "component_rights_current": True, "correction_manifest_target_bindings_current": True, "qa_receipts_current": True, "model_provenance_current": True, "html_pdf_reader_all_or_nothing": True, "pdf_structural_qa_current": True, "pdf_visual_qa_current": True},
    }
    receipt_path = root / "qa/unit-10/backend.json"
    receipt_path.write_bytes((json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    print(json.dumps({"status": "pass", "records": len(second["records"]), "jsonl": second["jsonl"], "csv": second["csv"], "manifest": second["manifest_binding"], "receipt": binding(receipt_path, root)}, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
