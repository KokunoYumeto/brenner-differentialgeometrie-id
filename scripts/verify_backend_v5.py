#!/usr/bin/env python3
"""Verify the deterministic Unit 5 extension of the O011 modular backend."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path


BASELINE_RECORD_COUNT = 813
BASELINE_JSONL_SHA256 = "33a4f876f8225e40a006e97453f5530c05b21e327cfd1b7058303fa2421287f9"
BASELINE_CSV_SHA256 = "34a472148f9f376dcc6da220af640c0b4b5f12586b722015789908226059b5ea"
WORKFLOW = "o011-export-backend-v5"
CSV_FIELDS = [
    "schema", "schema_version", "id", "entity_type", "source_local_id",
    "parent_id", "order", "path", "resource_id", "edition_id",
    "source_locator", "source_sha256", "target_sha256", "language",
    "locale", "translation_state", "rights_component_id", "status",
    "timestamp", "workflow", "supersedes",
]
EXPECTED_ENTITY_COUNTS = {
    "artifact": 5,
    "asset": 1,
    "concept": 8,
    "correction": 8,
    "course": 0,
    "edition": 0,
    "program": 0,
    "qa_event": 15,
    "relation": 80,
    "resource": 0,
    "rights": 1,
    "segment": 4,
    "term": 15,
    "unit": 19,
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


def live_binding(root: Path, value: dict[str, object], label: str) -> None:
    path = root / str(value["path"])
    if not path.is_file():
        raise RuntimeError(f"{label} path missing: {path}")
    current = binding(path, root)
    if current != {
        "path": value["path"],
        "bytes": value["bytes"],
        "sha256": value["sha256"],
    }:
        raise RuntimeError(f"{label} binding is stale")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--first-jsonl-sha256", required=True)
    parser.add_argument("--first-csv-sha256", required=True)
    parser.add_argument("--first-manifest-sha256", required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    jsonl_path = root / "backend/records.jsonl"
    csv_path = root / "backend/records.csv"
    manifest_path = root / "backend/MANIFEST.json"

    jsonl_bytes = jsonl_path.read_bytes()
    csv_bytes = csv_path.read_bytes()
    manifest_bytes = manifest_path.read_bytes()
    if sha256_bytes(jsonl_bytes) != args.first_jsonl_sha256:
        raise RuntimeError("JSONL changed between fixed-checkpoint exports")
    if sha256_bytes(csv_bytes) != args.first_csv_sha256:
        raise RuntimeError("CSV changed between fixed-checkpoint exports")
    if sha256_bytes(manifest_bytes) != args.first_manifest_sha256:
        raise RuntimeError("manifest changed between fixed-checkpoint exports")

    lines = jsonl_bytes.splitlines(keepends=True)
    if len(lines) != BASELINE_RECORD_COUNT + EXPECTED_EXTENSION_COUNT:
        raise RuntimeError(f"unexpected combined record count: {len(lines)}")
    prefix = b"".join(lines[:BASELINE_RECORD_COUNT])
    if sha256_bytes(prefix) != BASELINE_JSONL_SHA256:
        raise RuntimeError("immutable 813-record JSONL prefix changed")
    records = [json.loads(line.decode("utf-8")) for line in lines]
    extension = records[BASELINE_RECORD_COUNT:]
    for line, record in zip(lines[BASELINE_RECORD_COUNT:], extension):
        if line != canonical_json(record):
            raise RuntimeError(f"noncanonical extension record: {record.get('id')}")
    extension_ids = [str(record["id"]) for record in extension]
    if extension_ids != sorted(extension_ids):
        raise RuntimeError("Unit 5 extension is not ID sorted")
    if len(extension_ids) != len(set(extension_ids)):
        raise RuntimeError("duplicate Unit 5 ID")
    all_ids = {str(record["id"]) for record in records}
    if len(all_ids) != len(records):
        raise RuntimeError("combined backend IDs are not unique")

    required_fields = {
        "schema", "schema_version", "id", "entity_type", "status",
        "timestamp", "workflow", "supersedes",
    }
    for record in extension:
        missing = required_fields - set(record)
        if missing:
            raise RuntimeError(f"required fields missing on {record['id']}: {sorted(missing)}")
        if (
            record["schema"] != "o011-modular-backend"
            or record["schema_version"] != 1
            or record["workflow"] != WORKFLOW
            or record["timestamp"] != args.checkpoint
        ):
            raise RuntimeError(f"schema/workflow/checkpoint drift: {record['id']}")
        if record["entity_type"] == "artifact":
            for key in ("path", "target_sha256", "artifact_kind", "media_type", "bytes"):
                if key not in record:
                    raise RuntimeError(f"artifact field missing on {record['id']}: {key}")
        if record["entity_type"] == "qa_event":
            for key in ("target_id", "receipt_path", "evidence_sha256", "result"):
                if key not in record:
                    raise RuntimeError(f"QA field missing on {record['id']}: {key}")

    entity_counts = {
        kind: sum(record["entity_type"] == kind for record in extension)
        for kind in EXPECTED_ENTITY_COUNTS
    }
    if entity_counts != EXPECTED_ENTITY_COUNTS:
        raise RuntimeError(f"Unit 5 entity closure changed: {entity_counts}")
    by_id = {str(record["id"]): record for record in records}
    ext_by_id = {str(record["id"]): record for record in extension}

    csv_lines = csv_bytes.splitlines(keepends=True)
    if len(csv_lines) != BASELINE_RECORD_COUNT + EXPECTED_EXTENSION_COUNT + 1:
        raise RuntimeError("unexpected combined CSV line count")
    csv_prefix = b"".join(csv_lines[: BASELINE_RECORD_COUNT + 1])
    if sha256_bytes(csv_prefix) != BASELINE_CSV_SHA256:
        raise RuntimeError("immutable 813-row CSV prefix changed")
    csv_rows = list(csv.DictReader(csv_bytes.decode("utf-8-sig").splitlines()))
    if len(csv_rows) != len(records):
        raise RuntimeError("CSV/JSONL record counts disagree")
    for row, record in zip(csv_rows[BASELINE_RECORD_COUNT:], extension):
        for field in CSV_FIELDS:
            expected = "" if record.get(field) is None else str(record.get(field))
            if row[field] != expected:
                raise RuntimeError(f"CSV projection mismatch: {record['id']} / {field}")

    manifest = json.loads(manifest_bytes.decode("utf-8"))
    if manifest.get("workflow") != WORKFLOW or manifest.get("checkpoint") != args.checkpoint:
        raise RuntimeError("manifest workflow/checkpoint changed")
    if manifest.get("baseline", {}).get("record_count") != BASELINE_RECORD_COUNT:
        raise RuntimeError("manifest baseline count changed")
    if not manifest.get("baseline", {}).get("preserved_byte_identically"):
        raise RuntimeError("manifest does not claim byte-identical prefix preservation")
    unit_manifest = manifest.get("unit05_extension") or {}
    if (
        unit_manifest.get("record_count") != EXPECTED_EXTENSION_COUNT
        or unit_manifest.get("entity_counts") != EXPECTED_ENTITY_COUNTS
        or unit_manifest.get("lecture_segment_count") != 3
        or unit_manifest.get("exercise_count") != 15
        or unit_manifest.get("hint_indices") != [13]
        or unit_manifest.get("source_solution_indices") != [1]
        or unit_manifest.get("graded_point_total") != 22
        or unit_manifest.get("html_status") != "absent_not_claimed"
    ):
        raise RuntimeError("manifest Unit 5 closure changed")
    if manifest.get("combined", {}).get("record_count") != len(records):
        raise RuntimeError("manifest combined count is stale")
    if manifest.get("outputs", {}).get("records_jsonl") != binding(jsonl_path, root):
        raise RuntimeError("manifest JSONL output binding is stale")
    if manifest.get("outputs", {}).get("records_csv") != binding(csv_path, root):
        raise RuntimeError("manifest CSV output binding is stale")
    for key, value in (manifest.get("inputs") or {}).items():
        live_binding(root, value, f"manifest input {key}")

    for record in extension:
        for key in (
            "parent_id", "resource_id", "edition_id", "rights_component_id",
            "target_id", "artifact_id",
        ):
            value = record.get(key)
            if value is not None and value not in all_ids:
                raise RuntimeError(f"unresolved {key} on {record['id']}: {value}")
        for key in ("component_rights_ids", "target_ids"):
            for value in record.get(key) or []:
                if value not in all_ids:
                    raise RuntimeError(f"unresolved {key} on {record['id']}: {value}")
        if record["entity_type"] == "relation":
            if record.get("from_id") not in all_ids or record.get("to_id") not in all_ids:
                raise RuntimeError(f"unresolved relation endpoint: {record['id']}")

    unit_id = "o011-brenner-u05"
    lecture_id = "o011-brenner-u05-l05"
    worksheet_id = "o011-brenner-u05-w05"
    if ext_by_id[unit_id].get("parent_id") != "o011-course-d50":
        raise RuntimeError("Unit 5 parent changed")
    if ext_by_id[lecture_id].get("parent_id") != unit_id:
        raise RuntimeError("Lecture 5 parent changed")
    if ext_by_id[worksheet_id].get("parent_id") != unit_id:
        raise RuntimeError("Worksheet 5 parent changed")
    segments = [
        record for record in extension
        if record.get("parent_id") == lecture_id and record["entity_type"] == "segment"
    ]
    if [record["order"] for record in sorted(segments, key=lambda item: item["order"])] != [1, 2, 3]:
        raise RuntimeError("Lecture 5 segment closure changed")
    exercises = [
        ext_by_id[f"{worksheet_id}-e{index:03d}"] for index in range(1, 16)
    ]
    if [record["order"] for record in exercises] != list(range(1, 16)):
        raise RuntimeError("Worksheet 5 exercise order changed")
    if [record["point_value"] for record in exercises if record["graded"]] != [
        4, 4, 6, "6 (2+2+2)", 2
    ]:
        raise RuntimeError("Worksheet 5 graded markers changed")
    if [record["order"] for record in exercises if record["hint_present"]] != [13]:
        raise RuntimeError("Worksheet 5 hint index changed")
    if [record["order"] for record in exercises if record["has_authority_solution"]] != [1]:
        raise RuntimeError("Worksheet 5 source-solution index changed")
    if ext_by_id[f"{worksheet_id}-e013-hint"].get("parent_id") != f"{worksheet_id}-e013":
        raise RuntimeError("Unit 5 hint parent changed")
    if ext_by_id[f"{worksheet_id}-e001-solution"].get("parent_id") != f"{worksheet_id}-e001":
        raise RuntimeError("Unit 5 solution parent changed")

    required_concepts = {
        "o011-concept-principal-curvature",
        "o011-concept-principal-direction",
        "o011-concept-mean-curvature",
        "o011-concept-gaussian-curvature",
        "o011-concept-gauss-kronecker-curvature",
        "o011-concept-normal-curvature",
        "o011-concept-euler-normal-curvature-formula",
        "o011-concept-normal-section",
    }
    if not required_concepts <= all_ids:
        raise RuntimeError("Unit 5 concept closure changed")
    expected_terms = {f"o011-term-{number:04d}" for number in range(96, 111)}
    if {record["id"] for record in extension if record["entity_type"] == "term"} != expected_terms:
        raise RuntimeError("Unit 5 terminology closure changed")
    for term_id in expected_terms:
        term = ext_by_id[term_id]
        if term.get("terminology_status") != "admitted":
            raise RuntimeError(f"non-admitted Unit 5 term: {term_id}")

    asset_id = "o011-asset-file-minimal-surface-curvature-planes-de-svg"
    rights_id = "o011-rights-media-u05-01"
    pdf_id = "o011-artifact-through-unit05-pdf"
    if ext_by_id[asset_id].get("rights_component_id") != rights_id:
        raise RuntimeError("Unit 5 asset rights binding changed")
    if (
        ext_by_id[rights_id].get("license") != "CC BY-SA 3.0"
        or ext_by_id[rights_id].get("attribution")
        != "Eric Gaba (Sting); based upon a drawing in a book"
    ):
        raise RuntimeError("Unit 5 media rights changed")
    pdf = ext_by_id[pdf_id]
    if (
        pdf.get("bytes") != 4385370
        or pdf.get("target_sha256")
        != "44ef3bc7f4c9de8a9ffd3a747ea71c2102de6f26814718492bc63fd40e4af5ce"
        or pdf.get("pages") != 86
        or rights_id not in (pdf.get("component_rights_ids") or [])
    ):
        raise RuntimeError("Unit 5 PDF artifact changed")
    for record in extension:
        if record["entity_type"] == "artifact":
            live_binding(
                root,
                {
                    "path": record["path"],
                    "bytes": record["bytes"],
                    "sha256": record["target_sha256"],
                },
                f"artifact {record['id']}",
            )

    correction_targets = {
        "o011-corr-0046": [lecture_id, f"{worksheet_id}-e007"],
        "o011-corr-0047": [lecture_id, f"{worksheet_id}-e001-solution"],
        "o011-corr-0048": [lecture_id],
        "o011-corr-0049": [lecture_id],
        "o011-corr-0050": [lecture_id],
        "o011-corr-0051": [lecture_id],
        "o011-corr-0052": [lecture_id, f"{worksheet_id}-e014"],
        "o011-corr-0053": [f"{worksheet_id}-e001-solution"],
    }
    actual_corrections = {
        record["id"] for record in extension if record["entity_type"] == "correction"
    }
    if actual_corrections != set(correction_targets):
        raise RuntimeError("Unit 5 correction closure changed")
    relation_index = {
        (record.get("relation_type"), record.get("from_id"), record.get("to_id"))
        for record in extension if record["entity_type"] == "relation"
    }
    for correction_id, target_ids in correction_targets.items():
        correction = ext_by_id[correction_id]
        if correction.get("target_ids") != target_ids:
            raise RuntimeError(f"correction targets changed: {correction_id}")
        if not correction.get("correction_manifests"):
            raise RuntimeError(f"correction manifest missing: {correction_id}")
        for value in correction.get("target_bindings") or []:
            live_binding(root, value, f"correction target {correction_id}")
        for value in correction.get("correction_manifests") or []:
            live_binding(root, value, f"correction manifest {correction_id}")
        reader = correction.get("reader_binding") or {}
        live_binding(root, reader, f"correction reader {correction_id}")
        for target_id in target_ids:
            if ("corrects", correction_id, target_id) not in relation_index:
                raise RuntimeError(f"corrects relation missing: {correction_id}/{target_id}")

    qa_records = [
        record for record in extension if record["entity_type"] == "qa_event"
    ]
    if len(qa_records) != 15 or any(record.get("result") != "pass" for record in qa_records):
        raise RuntimeError("Unit 5 QA-event closure changed")
    for record in qa_records:
        live_binding(
            root,
            {
                "path": record["receipt_path"],
                "bytes": (root / record["receipt_path"]).stat().st_size,
                "sha256": record["evidence_sha256"],
            },
            f"QA evidence {record['id']}",
        )
    final_math = ext_by_id["o011-qa-unit05-final-math"]
    if (
        final_math.get("values", {}).get("checks_passed") != 46
        or final_math.get("values", {}).get("correction_ids")
        != [f"O011-CORR-{number:04d}" for number in range(46, 54)]
    ):
        raise RuntimeError("Unit 5 final mathematical QA closure changed")

    receipt = {
        "schema_version": 1,
        "workflow": "o011-verify-backend-v5",
        "status": "pass",
        "checkpoint": args.checkpoint,
        "baseline": {
            "records": BASELINE_RECORD_COUNT,
            "jsonl_sha256": BASELINE_JSONL_SHA256,
            "csv_sha256": BASELINE_CSV_SHA256,
            "preserved_byte_identically": True,
        },
        "unit05_extension": {
            "records": EXPECTED_EXTENSION_COUNT,
            "entity_counts": EXPECTED_ENTITY_COUNTS,
            "lecture_segments": 3,
            "exercises": 15,
            "hint_indices": [13],
            "source_solution_indices": [1],
            "graded_point_values": [4, 4, 6, "6 (2+2+2)", 2],
            "graded_point_total": 22,
            "correction_ids": list(correction_targets),
            "qa_events": 15,
            "html_status": "absent_not_claimed",
        },
        "combined_records": len(records),
        "outputs": {
            "records_jsonl": binding(jsonl_path, root),
            "records_csv": binding(csv_path, root),
            "manifest": binding(manifest_path, root),
        },
        "determinism": {
            "first_jsonl_sha256": args.first_jsonl_sha256,
            "first_csv_sha256": args.first_csv_sha256,
            "first_manifest_sha256": args.first_manifest_sha256,
            "second_export_matches_first": True,
        },
        "checks": {
            "canonical_jsonl": True,
            "csv_projection_exact": True,
            "all_ids_unique": True,
            "all_references_resolve": True,
            "required_schema_fields_present": True,
            "live_input_bindings_current": True,
            "live_artifact_bindings_current": True,
            "authority_solution_hint_point_media_closure": True,
            "correction_manifest_target_reader_bindings_current": True,
            "component_rights_current": True,
            "qa_receipts_current": True,
            "cumulative_html_not_falsely_claimed": True,
        },
    }
    output_path = root / "qa/unit-05/backend_qa.json"
    output_path.write_bytes(
        (
            json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True)
            + "\n"
        ).encode("utf-8")
    )
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
