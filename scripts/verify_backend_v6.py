#!/usr/bin/env python3
"""Independently verify the final deterministic Unit 6 O011 backend."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


BASELINE_RECORD_COUNT = 969
BASELINE_JSONL_BYTES = 576_960
BASELINE_JSONL_SHA256 = "bdd82d81cdac5cf30338d8fa0705189808ec4d746995127d02cbf4a248333227"
BASELINE_CSV_BYTES = 201_742
BASELINE_CSV_SHA256 = "ab7c40867434141e5f0a102db6b9a92a73677a3a946d96c3adbd925e77130592"
EXPORT_WORKFLOW = "o011-export-backend-v6"
VERIFY_WORKFLOW = "o011-verify-backend-v6"
MODEL_IDENTIFICATION = "OpenAI Codex gpt-5.6-sol, Ultra"
TRANSLATION_STATE = "visually_checked"
SOLUTION_INDICES = (2, 6, 9)
SOLUTION_ABSENT_INDICES = (1, 3, 4, 5, 7, 8, 10, 11, 12, 13, 14, 15, 16, 17, 18)
CORRECTION_NAMES = tuple(f"O011-CORR-{number:04d}" for number in range(54, 70))
CORRECTION_IDS = tuple(name.lower() for name in CORRECTION_NAMES)
TERM_IDS = tuple(f"o011-term-{number:04d}" for number in range(111, 135))
EXPECTED_RECORD_IDS_SHA256 = "13e0edb417965674706694e438013e09c69c53d1dba540c4ea32a09c0ce0b139"
EXPECTED_SEMANTIC_SHA256 = "e68ae3d0df8360078d9e3aed14dc001bb24607cdaec754f5029005c7d2ca7016"
EXPECTED_MATH_CHECKS = 262
EXPECTED_FINAL_BINDINGS = {
    "lecture_target": (32_034, "180c553eb556d91ba733e00f012bd0ece36c32e66704c992f0c64244ab6e05e8"),
    "final_math": (28_914, "b462de3f20b2a650d3f430660c993b598eba37f8acb0e4cc7187c0e171ee0cc7"),
    "terminology_propagation": (9_363, "c625cb3b97b1032dcec864c3ea06d7098f4a5ab7274078493f86e91c0e1de811"),
    "reader_pdf": (4_765_606, "40bf26d196ff04c38c6c99e8e9669a86bb5e6d31124b904b7ad154e7948cdec1"),
}
CSV_FIELDS = [
    "schema", "schema_version", "id", "entity_type", "source_local_id",
    "parent_id", "order", "path", "resource_id", "edition_id",
    "source_locator", "source_sha256", "target_sha256", "language",
    "locale", "translation_state", "rights_component_id", "status",
    "timestamp", "workflow", "supersedes",
]
ENTITY_TYPES = {
    "program", "course", "resource", "edition", "unit", "concept",
    "segment", "term", "asset", "relation", "rights", "qa_event",
    "artifact", "correction",
}
EXPECTED_ENTITY_COUNTS = {
    "artifact": 8,
    "asset": 1,
    "concept": 8,
    "correction": 16,
    "course": 0,
    "edition": 0,
    "program": 0,
    "qa_event": 14,
    "relation": 105,
    "resource": 0,
    "rights": 1,
    "segment": 3,
    "term": 24,
    "unit": 24,
}
EXPECTED_EXTENSION_COUNT = sum(EXPECTED_ENTITY_COUNTS.values())


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(record: dict[str, object]) -> bytes:
    return (
        json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def binding(path: Path, root: Path) -> dict[str, object]:
    data = path.read_bytes()
    return {
        "path": path.relative_to(root).as_posix(),
        "bytes": len(data),
        "sha256": sha256_bytes(data),
    }


def marker_slices(text: str, pattern: str) -> list[str]:
    starts = [match.start() for match in re.finditer(pattern, text)]
    return [
        text[start : starts[index + 1] if index + 1 < len(starts) else len(text)]
        for index, start in enumerate(starts)
    ]


def semantic_projection(value: object) -> object:
    if isinstance(value, dict):
        return {
            key: semantic_projection(item)
            for key, item in sorted(value.items())
            if key not in {"timestamp", "translation_state", "bytes", "checks_passed"}
            and key != "sha256"
            and not key.endswith("_sha256")
        }
    if isinstance(value, list):
        return [semantic_projection(item) for item in value]
    return value


def semantic_sha256(records: list[dict[str, object]]) -> str:
    data = (
        json.dumps(
            [semantic_projection(record) for record in records],
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")
    return sha256_bytes(data)


def assert_live_binding(root: Path, value: dict[str, object], label: str) -> None:
    path = root / str(value.get("path"))
    if not path.is_file():
        raise RuntimeError(f"{label} path missing: {path}")
    actual = binding(path, root)
    if any(actual[key] != value.get(key) for key in ("path", "bytes", "sha256")):
        raise RuntimeError(f"{label} binding is stale: {value} != {actual}")


def expected_csv(baseline: bytes, records: list[dict[str, object]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(
        buffer,
        fieldnames=CSV_FIELDS,
        extrasaction="ignore",
        lineterminator="\r\n",
    )
    for record in records:
        writer.writerow({field: record.get(field) for field in CSV_FIELDS})
    return baseline + buffer.getvalue().encode("utf-8")


def validate_current(root: Path) -> dict[str, object]:
    jsonl_path = root / "backend/records.jsonl"
    csv_path = root / "backend/records.csv"
    manifest_path = root / "backend/MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    jsonl = jsonl_path.read_bytes()
    csv_bytes = csv_path.read_bytes()
    lines = jsonl.splitlines(keepends=True)
    if len(lines) != BASELINE_RECORD_COUNT + EXPECTED_EXTENSION_COUNT:
        raise RuntimeError(f"unexpected combined record count: {len(lines)}")
    baseline_jsonl = b"".join(lines[:BASELINE_RECORD_COUNT])
    if len(baseline_jsonl) != BASELINE_JSONL_BYTES or sha256_bytes(baseline_jsonl) != BASELINE_JSONL_SHA256:
        raise RuntimeError("immutable 969-record JSONL prefix changed")
    records = [json.loads(line.decode("utf-8")) for line in lines]
    added = records[BASELINE_RECORD_COUNT:]
    for index, (line, record) in enumerate(zip(lines[BASELINE_RECORD_COUNT:], added), BASELINE_RECORD_COUNT + 1):
        if line != canonical_json(record):
            raise RuntimeError(f"noncanonical extension record: {index}")
    added_ids = [str(record["id"]) for record in added]
    if added_ids != sorted(added_ids) or len(set(added_ids)) != len(added_ids):
        raise RuntimeError("Unit 6 extension IDs are not unique and sorted")
    if sha256_bytes(("\n".join(added_ids) + "\n").encode("utf-8")) != EXPECTED_RECORD_IDS_SHA256:
        raise RuntimeError("Unit 6 extension IDs changed")
    if semantic_sha256(added) != EXPECTED_SEMANTIC_SHA256:
        raise RuntimeError("Unit 6 semantic extension changed")
    all_ids = [str(record["id"]) for record in records]
    if len(set(all_ids)) != len(all_ids):
        raise RuntimeError("combined backend IDs are not unique")
    by_id = {str(record["id"]): record for record in records}

    counts = Counter(str(record.get("entity_type")) for record in added)
    actual_counts = {kind: counts.get(kind, 0) for kind in sorted(ENTITY_TYPES)}
    if actual_counts != EXPECTED_ENTITY_COUNTS:
        raise RuntimeError(f"Unit 6 entity closure changed: {actual_counts}")
    schema = json.loads((root / "backend/schema/o011-record-v1.schema.json").read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors: list[str] = []
    for record in records:
        errors.extend(f"{record['id']}: {error.message}" for error in validator.iter_errors(record))
    if errors:
        raise RuntimeError("JSON Schema validation failed: " + "; ".join(errors[:10]))

    csv_lines = csv_bytes.splitlines(keepends=True)
    if len(csv_lines) != BASELINE_RECORD_COUNT + EXPECTED_EXTENSION_COUNT + 1:
        raise RuntimeError("unexpected combined CSV line count")
    baseline_csv = b"".join(csv_lines[: BASELINE_RECORD_COUNT + 1])
    if len(baseline_csv) != BASELINE_CSV_BYTES or sha256_bytes(baseline_csv) != BASELINE_CSV_SHA256:
        raise RuntimeError("immutable 969-row CSV prefix changed")
    if csv_bytes != expected_csv(baseline_csv, added):
        raise RuntimeError("CSV projection does not exactly match JSONL")

    checkpoint = str(manifest.get("checkpoint"))
    if manifest.get("workflow") != EXPORT_WORKFLOW:
        raise RuntimeError("manifest export workflow changed")
    if any(record.get("timestamp") != checkpoint or record.get("workflow") != EXPORT_WORKFLOW for record in added):
        raise RuntimeError("Unit 6 record checkpoint/workflow changed")
    if any(record.get("translation_state") != TRANSLATION_STATE for record in added if "translation_state" in record):
        raise RuntimeError("Unit 6 final translation state changed")
    baseline = manifest.get("baseline", {})
    if (
        baseline.get("record_count") != BASELINE_RECORD_COUNT
        or baseline.get("jsonl_bytes") != BASELINE_JSONL_BYTES
        or baseline.get("jsonl_sha256") != BASELINE_JSONL_SHA256
        or baseline.get("csv_bytes") != BASELINE_CSV_BYTES
        or baseline.get("csv_sha256") != BASELINE_CSV_SHA256
        or baseline.get("preserved_byte_identically") is not True
    ):
        raise RuntimeError("manifest baseline closure changed")
    extension = manifest.get("unit06_extension", {})
    if (
        extension.get("record_count") != EXPECTED_EXTENSION_COUNT
        or extension.get("entity_counts") != EXPECTED_ENTITY_COUNTS
        or extension.get("record_ids_sha256") != EXPECTED_RECORD_IDS_SHA256
        or extension.get("semantic_projection_sha256") != EXPECTED_SEMANTIC_SHA256
        or extension.get("lecture_segment_count") != 3
        or extension.get("exercise_count") != 18
        or extension.get("hint_indices") != []
        or extension.get("source_solution_indices") != list(SOLUTION_INDICES)
        or extension.get("source_solution_absent_indices") != list(SOLUTION_ABSENT_INDICES)
        or extension.get("terminology_ids") != [name.upper() for name in TERM_IDS]
        or extension.get("correction_ids") != list(CORRECTION_NAMES)
        or extension.get("model_identification") != MODEL_IDENTIFICATION
        or extension.get("translation_state") != TRANSLATION_STATE
        or extension.get("pdf_status") != "final_cumulative_reader_bound"
        or extension.get("html_status") != "absent_not_claimed"
    ):
        raise RuntimeError("manifest Unit 6 closure changed")
    if manifest.get("combined", {}).get("record_count") != len(records):
        raise RuntimeError("manifest combined record count is stale")
    claims = manifest.get("claims", {})
    required_claims = (
        "all_ids_unique", "all_references_resolve", "json_schema_valid",
        "unit06_translation_receipts_current", "unit06_authority_solution_media_closure_current",
        "unit06_correction_manifests_and_targets_current", "unit06_terminology_and_provenance_current",
        "unit06_pdf_build_structural_visual_receipts_current", "cumulative_pdf_present",
    )
    if any(claims.get(key) is not True for key in required_claims) or claims.get("cumulative_html_present") is not False:
        raise RuntimeError("manifest claims changed")
    if manifest.get("outputs", {}).get("records_jsonl") != binding(jsonl_path, root):
        raise RuntimeError("manifest JSONL output binding is stale")
    if manifest.get("outputs", {}).get("records_csv") != binding(csv_path, root):
        raise RuntimeError("manifest CSV output binding is stale")
    for key, value in manifest.get("inputs", {}).items():
        assert_live_binding(root, value, f"manifest input {key}")
    for key, expected in EXPECTED_FINAL_BINDINGS.items():
        value = manifest.get("inputs", {}).get(key, {})
        if (value.get("bytes"), value.get("sha256")) != expected:
            raise RuntimeError(f"final {key} manifest identity changed")
    if extension.get("pdf") != manifest.get("inputs", {}).get("reader_pdf"):
        raise RuntimeError("manifest final PDF binding changed")

    id_set = set(all_ids)
    for record in added:
        for key in ("parent_id", "resource_id", "edition_id", "rights_component_id", "target_id", "artifact_id"):
            value = record.get(key)
            if value is not None and str(value) not in id_set:
                raise RuntimeError(f"unresolved {key} on {record['id']}")
        for key in ("component_rights_ids", "target_ids"):
            for value in record.get(key) or []:
                if str(value) not in id_set:
                    raise RuntimeError(f"unresolved {key} on {record['id']}")
        if record.get("entity_type") == "relation":
            if str(record.get("from_id")) not in id_set or str(record.get("to_id")) not in id_set:
                raise RuntimeError(f"unresolved relation endpoint: {record['id']}")

    lecture_source = (root / manifest["inputs"]["lecture_source"]["path"]).read_text(encoding="utf-8")
    lecture_target = (root / manifest["inputs"]["lecture_target"]["path"]).read_text(encoding="utf-8")
    worksheet_source = (root / manifest["inputs"]["worksheet_source"]["path"]).read_text(encoding="utf-8")
    worksheet_target = (root / manifest["inputs"]["worksheet_target"]["path"]).read_text(encoding="utf-8")
    lecture_source_parts = marker_slices(lecture_source, r"\\zwischenueberschrift\{")
    lecture_target_parts = marker_slices(lecture_target, r"\\zwischenueberschrift\{")
    worksheet_source_parts = marker_slices(worksheet_source, r"\\inputaufgabe(?:gibtloesung)?")
    worksheet_target_parts = marker_slices(worksheet_target, r"\\inputaufgabe(?:gibtloesung)?")
    if len(lecture_source_parts) != 3 or len(lecture_target_parts) != 3:
        raise RuntimeError("Lecture 6 segment topology changed")
    if len(worksheet_source_parts) != 18 or len(worksheet_target_parts) != 18:
        raise RuntimeError("Worksheet 6 exercise topology changed")
    for index, (source_part, target_part) in enumerate(zip(lecture_source_parts, lecture_target_parts), 1):
        record = by_id[f"o011-brenner-u06-l06-s{index:02d}"]
        if (
            record.get("order") != index
            or record.get("source_sha256") != sha256_bytes(source_part.encode("utf-8"))
            or record.get("target_sha256") != sha256_bytes(target_part.encode("utf-8"))
        ):
            raise RuntimeError(f"Lecture 6 segment binding changed: {index}")
    graded_indices: list[int] = []
    for index, (source_part, target_part) in enumerate(zip(worksheet_source_parts, worksheet_target_parts), 1):
        record = by_id[f"o011-brenner-u06-w06-e{index:03d}"]
        expected_solution = index in SOLUTION_INDICES
        if (
            record.get("order") != index
            or record.get("source_sha256") != sha256_bytes(source_part.encode("utf-8"))
            or record.get("target_sha256") != sha256_bytes(target_part.encode("utf-8"))
            or record.get("hint_present") is not False
            or record.get("source_solution_checked") is not True
            or record.get("has_authority_solution") is not expected_solution
            or record.get("authority_solution_status") != ("source_supplied" if expected_solution else "source_absent")
        ):
            raise RuntimeError(f"Worksheet 6 exercise/source-solution binding changed: {index}")
        if record.get("graded"):
            graded_indices.append(index)
    if graded_indices != [15, 16, 17, 18]:
        raise RuntimeError("Worksheet 6 graded indices changed")
    if [by_id[f"o011-brenner-u06-w06-e{index:03d}"].get("point_value") for index in graded_indices] != [2, 4, 4, 4]:
        raise RuntimeError("Worksheet 6 graded markers changed")
    for index in SOLUTION_INDICES:
        solution_id = f"o011-brenner-u06-w06-e{index:03d}-solution"
        if by_id[solution_id].get("parent_id") != f"o011-brenner-u06-w06-e{index:03d}" or by_id[solution_id].get("unit_kind") != "source_supplied_solution":
            raise RuntimeError(f"Unit 6 supplied-solution record changed: {index}")

    if tuple(record["id"] for record in added if record.get("entity_type") == "term") != TERM_IDS:
        raise RuntimeError("Unit 6 terminology ID closure changed")
    for term_id in TERM_IDS:
        record = by_id[term_id]
        if (
            record.get("terminology_status") != "admitted"
            or record.get("terminology_ledger_sha256") != manifest["inputs"]["terminology"]["sha256"]
            or record.get("field_audit_sha256") != manifest["inputs"]["terminology_audit"]["sha256"]
        ):
            raise RuntimeError(f"stale or non-admitted Unit 6 term: {term_id}")
    if by_id["o011-brenner-u06"].get("translation_assistance", {}).get("model") != MODEL_IDENTIFICATION:
        raise RuntimeError("Unit 6 model provenance changed")
    provenance_artifact = by_id["o011-artifact-u06-reader-wrapper-provenance"]
    if provenance_artifact.get("model_identification") != MODEL_IDENTIFICATION:
        raise RuntimeError("Unit 6 model-provenance artifact changed")
    provenance_event = by_id["o011-qa-unit06-model-provenance"]
    if provenance_event.get("values", {}).get("model_identification") != MODEL_IDENTIFICATION:
        raise RuntimeError("Unit 6 model-provenance QA changed")

    asset = by_id["o011-asset-file-parallel-transport-sphere2-svg"]
    rights = by_id["o011-rights-media-u06-01"]
    if (
        asset.get("rights_component_id") != rights["id"]
        or asset.get("source_sha256") != manifest["inputs"]["asset_svg"]["sha256"]
        or asset.get("expected_bytes") != manifest["inputs"]["asset_svg"]["bytes"]
        or asset.get("creator") != "Silly rabbit"
        or rights.get("license") != "CC BY-SA 3.0"
        or rights.get("license_url") != "https://creativecommons.org/licenses/by-sa/3.0/"
        or rights.get("attribution") != "Silly rabbit at English Wikipedia (own work)"
        or rights.get("evidence_sha256") != manifest["inputs"]["authority"]["sha256"]
        or rights.get("media_rights_manifest_sha256") != manifest["inputs"]["media_manifest"]["sha256"]
    ):
        raise RuntimeError("Unit 6 component rights changed")

    artifact_records = [record for record in added if record.get("entity_type") == "artifact"]
    for record in artifact_records:
        path = root / str(record["path"])
        actual = binding(path, root)
        if record.get("bytes") != actual["bytes"] or record.get("target_sha256") != actual["sha256"]:
            raise RuntimeError(f"artifact binding changed: {record['id']}")

    target_map = {
        "o011-corr-0054": ["o011-brenner-u06-l06"],
        "o011-corr-0055": ["o011-brenner-u06-l06"],
        "o011-corr-0056": ["o011-brenner-u06-l06"],
        "o011-corr-0057": ["o011-brenner-u06-l06"],
        "o011-corr-0058": ["o011-brenner-u06-l06"],
        "o011-corr-0059": ["o011-brenner-u06-l06", "o011-brenner-u06-w06"],
        "o011-corr-0060": ["o011-brenner-u06-l06"],
        "o011-corr-0061": ["o011-brenner-u06-l06"],
        "o011-corr-0062": ["o011-brenner-u06-l06"],
        "o011-corr-0063": ["o011-brenner-u06-w06-e001"],
        "o011-corr-0064": ["o011-brenner-u06-w06-e004"],
        "o011-corr-0065": ["o011-brenner-u06-w06-e007"],
        "o011-corr-0066": ["o011-brenner-u06-w06-e017"],
        "o011-corr-0067": ["o011-brenner-u06-w06-e002-solution"],
        "o011-corr-0068": ["o011-brenner-u06-w06-e008"],
        "o011-corr-0069": ["o011-brenner-u06-l06"],
    }
    relations = {(record.get("relation_type"), record.get("from_id"), record.get("to_id")) for record in added if record.get("entity_type") == "relation"}
    for correction_id, targets in target_map.items():
        record = by_id[correction_id]
        if record.get("target_ids") != targets or record.get("correction_status") != "corrected_in_target":
            raise RuntimeError(f"correction targets changed: {correction_id}")
        if not record.get("correction_manifests"):
            raise RuntimeError(f"correction manifest missing: {correction_id}")
        for value in record["correction_manifests"]:
            assert_live_binding(root, value, f"correction manifest {correction_id}")
        for value in record["target_bindings"]:
            assert_live_binding(root, value, f"correction target {correction_id}")
        validation = record.get("validation_binding", {})
        assert_live_binding(root, validation, f"correction validation {correction_id}")
        if validation.get("checks_passed") != EXPECTED_MATH_CHECKS:
            raise RuntimeError(f"correction validation count changed: {correction_id}")
        for target in targets:
            if ("corrects", correction_id, target) not in relations:
                raise RuntimeError(f"corrects relation missing: {correction_id}/{target}")

    qa_events = [record for record in added if record.get("entity_type") == "qa_event"]
    if len(qa_events) != 14 or any(record.get("result") != "pass" for record in qa_events):
        raise RuntimeError("Unit 6 QA-event closure changed")
    for record in qa_events:
        path = root / str(record["receipt_path"])
        if record.get("evidence_sha256") != sha256_bytes(path.read_bytes()):
            raise RuntimeError(f"QA evidence changed: {record['id']}")
    closure_values = by_id["o011-qa-unit06-solution-closure"].get("values", {})
    if closure_values.get("supplied_solution_indices") != list(SOLUTION_INDICES) or closure_values.get("missing_solution_indices") != list(SOLUTION_ABSENT_INDICES):
        raise RuntimeError("Unit 6 solution-absence QA changed")
    math_values = by_id["o011-qa-unit06-final-math"].get("values", {})
    if math_values.get("checks_passed") != EXPECTED_MATH_CHECKS or math_values.get("correction_ids") != list(CORRECTION_NAMES):
        raise RuntimeError("Unit 6 final mathematical QA closure changed")
    for index in SOLUTION_INDICES:
        solution_id = f"o011-brenner-u06-w06-e{index:03d}-solution"
        exercise_id = f"o011-brenner-u06-w06-e{index:03d}"
        if ("solves", solution_id, exercise_id) not in relations:
            raise RuntimeError(f"solution relation missing: {index}")
    if ("governs", "o011-rights-media-u06-01", "o011-asset-file-parallel-transport-sphere2-svg") not in relations:
        raise RuntimeError("Unit 6 media-rights relation missing")

    build = json.loads((root / manifest["inputs"]["build"]["path"]).read_text(encoding="utf-8"))
    structural = json.loads((root / manifest["inputs"]["structural"]["path"]).read_text(encoding="utf-8"))
    pdf = manifest["inputs"]["reader_pdf"]
    if build.get("output") != pdf or any((cycle.get("bytes"), cycle.get("sha256")) != (pdf["bytes"], pdf["sha256"]) for cycle in build.get("cycles", [])):
        raise RuntimeError("Unit 6 deterministic PDF build binding changed")
    if structural.get("passed") is not True or any(structural.get("pdf", {}).get(key) != pdf[key] for key in ("path", "bytes", "sha256")):
        raise RuntimeError("Unit 6 structural PDF binding changed")

    return {
        "manifest": manifest,
        "records": records,
        "added": added,
        "entity_counts": actual_counts,
        "jsonl": binding(jsonl_path, root),
        "csv": binding(csv_path, root),
        "manifest_binding": binding(manifest_path, root),
        "pdf": pdf,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    root = args.root.resolve()

    first = validate_current(root)
    checkpoint = str(first["manifest"]["checkpoint"])
    command = [
        sys.executable,
        str(root / "scripts/export_backend_v6.py"),
        "--root", str(root),
        "--checkpoint", checkpoint,
        "--translation-state", TRANSLATION_STATE,
    ]
    completed = subprocess.run(command, cwd=root, capture_output=True, text=True, encoding="utf-8")
    if completed.returncode != 0:
        raise RuntimeError(f"repeat exporter failed: {completed.stderr.strip() or completed.stdout.strip()}")
    second = validate_current(root)
    for key in ("jsonl", "csv", "manifest_binding"):
        if first[key] != second[key]:
            raise RuntimeError(f"repeat export changed {key}: {first[key]} != {second[key]}")

    receipt = {
        "schema_version": 1,
        "workflow": VERIFY_WORKFLOW,
        "status": "pass",
        "checkpoint": checkpoint,
        "baseline": {
            "records": BASELINE_RECORD_COUNT,
            "jsonl_bytes": BASELINE_JSONL_BYTES,
            "jsonl_sha256": BASELINE_JSONL_SHA256,
            "csv_bytes": BASELINE_CSV_BYTES,
            "csv_sha256": BASELINE_CSV_SHA256,
            "preserved_byte_identically": True,
        },
        "unit06_extension": {
            "records": EXPECTED_EXTENSION_COUNT,
            "entity_counts": second["entity_counts"],
            "lecture_segments": 3,
            "exercises": 18,
            "source_solution_indices": list(SOLUTION_INDICES),
            "source_solution_absent_indices": list(SOLUTION_ABSENT_INDICES),
            "hint_indices": [],
            "graded_point_values": [2, 4, 4, 4],
            "graded_point_total": 14,
            "terminology_ids": list(TERM_IDS),
            "correction_ids": list(CORRECTION_IDS),
            "asset_id": "o011-asset-file-parallel-transport-sphere2-svg",
            "rights_id": "o011-rights-media-u06-01",
            "qa_events": 14,
            "model_identification": MODEL_IDENTIFICATION,
            "translation_state": TRANSLATION_STATE,
            "pdf_status": "final_cumulative_reader_bound",
            "html_status": "absent_not_claimed",
        },
        "combined_records": len(second["records"]),
        "final_pdf": second["pdf"],
        "outputs": {
            "records_jsonl": second["jsonl"],
            "records_csv": second["csv"],
            "manifest": second["manifest_binding"],
        },
        "determinism": {
            "first_jsonl_sha256": first["jsonl"]["sha256"],
            "first_csv_sha256": first["csv"]["sha256"],
            "first_manifest_sha256": first["manifest_binding"]["sha256"],
            "second_export_matches_first": True,
        },
        "checks": {
            "canonical_jsonl": True,
            "csv_projection_exact": True,
            "combined_json_schema_valid": True,
            "all_ids_unique": True,
            "all_references_resolve": True,
            "live_input_bindings_current": True,
            "live_artifact_bindings_current": True,
            "source_target_segment_hashes_current": True,
            "exact_solution_absence_truth": True,
            "authority_solution_hint_point_media_closure": True,
            "correction_manifest_target_validation_bindings_current": True,
            "component_rights_current": True,
            "terminology_and_model_provenance_current": True,
            "qa_receipts_current": True,
            "cumulative_pdf_build_structural_visual_current": True,
            "cumulative_html_not_falsely_claimed": True,
            "reconstructed_scripts_replace_nul_corruption": True,
        },
    }
    receipt_path = root / "qa/unit-06/backend.json"
    receipt_path.write_bytes(
        (json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    )
    print(json.dumps({
        "status": "pass",
        "records": len(second["records"]),
        "jsonl": second["jsonl"],
        "csv": second["csv"],
        "manifest": second["manifest_binding"],
        "receipt": binding(receipt_path, root),
        "pdf": second["pdf"],
    }, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
