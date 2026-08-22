#!/usr/bin/env python3
"""Validate the combined Unit 1 + Unit 2 backend and write its QA receipt."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


UNIT01_BASELINE_SHA256 = "7b7cd4e77932d89920c921e886f3a689dcba4d0335325ec93593371552469533"
WINDOWS_ABSOLUTE = re.compile(r"(?i)(?<![a-z0-9+.-])[a-z]:[\\/]")
PRIVATE_MARKERS = (
    "\\users\\", "/users/", "\\appdata\\", "/home/", "github_pat_", "ghp_",
    "gho_", "ghu_", "ghs_", "ghr_", "glpat-", "sk-proj-", "xoxb-",
    "bearer ", "access_token", "api_key", "zenodo token",
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def file_info(path: Path, root: Path) -> dict[str, object]:
    data = path.read_bytes()
    return {
        "path": str(path.resolve().relative_to(root.resolve())).replace("\\", "/"),
        "bytes": len(data),
        "sha256": digest(data),
    }


def walk_strings(value: object, key: str = ""):
    if isinstance(value, dict):
        for child_key, child in value.items():
            yield from walk_strings(child, child_key)
    elif isinstance(value, list):
        for child in value:
            yield from walk_strings(child, key)
    elif isinstance(value, str):
        yield key, value


def assert_public_safe_bytes(label: str, data: bytes) -> None:
    text = data.decode("utf-8")
    folded = text.casefold()
    if WINDOWS_ABSOLUTE.search(text):
        raise RuntimeError(f"absolute Windows path leaked into {label}")
    found = [marker for marker in PRIVATE_MARKERS if marker in folded]
    if found:
        raise RuntimeError(f"private path or credential marker leaked into {label}: {found}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--first-jsonl-sha256", required=True)
    parser.add_argument("--first-csv-sha256", required=True)
    parser.add_argument("--first-manifest-sha256", required=True)
    args = parser.parse_args()
    root = args.root.resolve()

    jsonl_path = root / "backend/records.jsonl"
    csv_path = root / "backend/records.csv"
    manifest_path = root / "backend/MANIFEST.json"
    schema_path = root / "backend/schema/o011-record-v1.schema.json"
    baseline_path = root / "backend/unit01_records_frozen.jsonl"
    jsonl_bytes = jsonl_path.read_bytes()
    csv_bytes = csv_path.read_bytes()
    manifest_bytes = manifest_path.read_bytes()
    baseline_bytes = baseline_path.read_bytes()
    for label, data in (
        ("records.jsonl", jsonl_bytes),
        ("records.csv", csv_bytes),
        ("MANIFEST.json", manifest_bytes),
    ):
        assert_public_safe_bytes(label, data)
    if digest(baseline_bytes) != UNIT01_BASELINE_SHA256:
        raise RuntimeError("Unit 1 baseline hash changed")
    if digest(jsonl_bytes) != args.first_jsonl_sha256:
        raise RuntimeError("JSONL differs from the first fixed-checkpoint export")
    if digest(csv_bytes) != args.first_csv_sha256:
        raise RuntimeError("CSV differs from the first fixed-checkpoint export")
    if digest(manifest_bytes) != args.first_manifest_sha256:
        raise RuntimeError("manifest differs from the first fixed-checkpoint export")

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    records: list[dict[str, object]] = []
    for line_number, line in enumerate(jsonl_bytes.decode("utf-8").splitlines(), 1):
        record = json.loads(line)
        errors = sorted(validator.iter_errors(record), key=lambda error: list(error.path))
        if errors:
            raise RuntimeError(
                f"schema failure at row {line_number}, {record.get('id')}: {errors[0].message}"
            )
        records.append(record)
    ids = {record["id"] for record in records}
    if len(ids) != len(records):
        raise RuntimeError("duplicate stable IDs")
    for record in records:
        for field in (
            "parent_id", "resource_id", "edition_id", "rights_component_id",
            "target_id", "artifact_id",
        ):
            value = record.get(field)
            if value is not None and value not in ids:
                raise RuntimeError(f"unresolved {field} in {record['id']}")
        for value in record.get("component_rights_ids") or []:
            if value not in ids:
                raise RuntimeError(f"unresolved component right in {record['id']}")
        if record["entity_type"] == "relation":
            for field in ("from_id", "to_id"):
                if record.get(field) not in ids:
                    raise RuntimeError(f"unresolved relation endpoint in {record['id']}")

    baseline_records = [json.loads(line) for line in baseline_bytes.decode("utf-8").splitlines()]
    baseline_ids = {record["id"] for record in baseline_records}
    extracted = sorted(
        (record for record in records if record["id"] in baseline_ids),
        key=lambda record: str(record["id"]),
    )
    extracted_bytes = "".join(canonical_json(record) + "\n" for record in extracted).encode("utf-8")
    if extracted_bytes != baseline_bytes:
        raise RuntimeError("Unit 1 record objects are not byte-identical to the frozen baseline")

    unit02 = [record for record in records if record["id"] not in baseline_ids]
    unit02_ids = {record["id"] for record in unit02}
    expected_exercises = {f"o011-brenner-u02-w02-e{index:03d}" for index in range(1, 20)}
    expected_solutions = {
        f"o011-brenner-u02-w02-e{index:03d}-solution" for index in (1, 2, 7, 12, 13)
    }
    expected_segments = {f"o011-brenner-u02-l02-s{index:02d}" for index in range(1, 4)}
    expected_concepts = {
        "o011-concept-surface-of-revolution", "o011-concept-unit-normal-field",
        "o011-concept-orientation", "o011-concept-gauss-map",
    }
    ledger_path = root / "00_control/ADVERSE_LEDGER.csv"
    ledger_rows = list(csv.DictReader(io.StringIO(ledger_path.read_text(encoding="utf-8-sig"))))
    for row_number, row in enumerate(ledger_rows, 2):
        if None in row or any(row.get(field) is None for field in (
            "id", "severity", "surface", "status", "description", "disposition",
        )):
            raise RuntimeError(f"malformed adverse-ledger CSV row {row_number}")
    expected_corrections = {
        row["id"].lower() for row in ledger_rows if row["id"].lower() not in baseline_ids
    }
    for expected, label in (
        (expected_exercises, "exercises"), (expected_solutions, "solutions"),
        (expected_segments, "segments"), (expected_concepts, "concepts"),
        (expected_corrections, "corrections"),
    ):
        if not expected.issubset(unit02_ids):
            raise RuntimeError(f"Unit 2 {label} closure missing: {sorted(expected - unit02_ids)}")
    for index in range(1, 20):
        record = next(row for row in unit02 if row["id"] == f"o011-brenner-u02-w02-e{index:03d}")
        if record.get("source_display_id") != f"2.{index}":
            raise RuntimeError(f"source display ID drift at exercise {index}")
    for index in (1, 2, 7, 12, 13):
        record = next(row for row in unit02 if row["id"] == f"o011-brenner-u02-w02-e{index:03d}-solution")
        if record.get("source_display_id") != f"2.{index}":
            raise RuntimeError(f"source display ID drift at solution {index}")

    artifacts = [record for record in unit02 if record["entity_type"] == "artifact"]
    qa_events = [record for record in unit02 if record["entity_type"] == "qa_event"]
    assets = [record for record in unit02 if record["entity_type"] == "asset"]
    rights = [record for record in unit02 if record["entity_type"] == "rights"]
    corrections = [record for record in unit02 if record["entity_type"] == "correction"]
    if (
        len(artifacts) != 8 or len(qa_events) != 13 or len(assets) != 2
        or len(rights) != 2 or len(corrections) != len(expected_corrections)
    ):
        raise RuntimeError(
            f"Unit 2 artifact/QA/media closure failed: artifacts={len(artifacts)}, "
            f"qa={len(qa_events)}, assets={len(assets)}, rights={len(rights)}, "
            f"corrections={len(corrections)}"
        )
    for artifact in artifacts:
        artifact_path = root / str(artifact["path"])
        artifact_bytes = artifact_path.read_bytes()
        if len(artifact_bytes) != artifact["bytes"] or digest(artifact_bytes) != artifact["target_sha256"]:
            raise RuntimeError(f"stale artifact binding: {artifact['id']}")
    for qa_event in qa_events:
        receipt_path = root / str(qa_event["receipt_path"])
        if digest(receipt_path.read_bytes()) != qa_event["evidence_sha256"]:
            raise RuntimeError(f"stale QA evidence binding: {qa_event['id']}")
        admitted_structural_limitation = (
            qa_event["id"] == "o011-qa-through-unit02-pdf-structural"
            and qa_event["result"] == "admitted_limitation"
            and qa_event.get("limitations")
        )
        if qa_event["result"] != "pass" and not admitted_structural_limitation:
            raise RuntimeError(f"non-passing QA event: {qa_event['id']}")
    declared_correction_ids: set[str] = set()
    for qa_event in qa_events:
        for declaration in qa_event.get("declared_corrections") or []:
            if isinstance(declaration, str):
                declared_correction_ids.update(
                    item.lower() for item in declaration.split("+") if item
                )
    declared_correction_ids.add("o011-corr-0015")
    if not declared_correction_ids.issubset(expected_corrections):
        raise RuntimeError("Unit 2 receipt-declared corrections are missing from correction records")
    for correction in corrections:
        ledger_path = root / str(correction["ledger_path"])
        if digest(ledger_path.read_bytes()) != correction["ledger_sha256"]:
            raise RuntimeError(f"stale correction ledger binding: {correction['id']}")
        for delta in correction.get("protected_deltas") or []:
            manifest_path = root / str(delta["manifest_path"])
            if digest(manifest_path.read_bytes()) != delta["manifest_sha256"]:
                raise RuntimeError(f"stale protected-correction binding: {correction['id']}")

    pdf_artifact = next(
        record for record in artifacts if record["id"] == "o011-artifact-through-unit02-pdf"
    )
    if (
        pdf_artifact["translation_state"] != "visually_checked"
        or pdf_artifact["bytes"] <= 0
        or len(pdf_artifact.get("component_rights_ids") or []) != 7
    ):
        raise RuntimeError("cumulative Unit 2 PDF artifact binding is incomplete")
    expected_reader_qa = {
        "o011-qa-unit02-media-closure",
        "o011-qa-through-unit02-pdf-reproducibility",
        "o011-qa-through-unit02-pdf-structural",
        "o011-qa-through-unit02-pdf-visual",
        "o011-qa-unit02-final-math-audit",
    }
    if not expected_reader_qa.issubset({record["id"] for record in qa_events}):
        raise RuntimeError("cumulative Unit 2 reader QA closure is incomplete")

    manifest = json.loads(manifest_bytes.decode("utf-8"))
    if manifest.get("timestamp") != args.checkpoint:
        raise RuntimeError("manifest checkpoint differs from requested checkpoint")
    if manifest.get("record_count") != len(records):
        raise RuntimeError("manifest record count mismatch")
    expected_counts = {
        entity_type: sum(record["entity_type"] == entity_type for record in records)
        for entity_type in sorted({record["entity_type"] for record in records})
    }
    if manifest.get("entity_counts") != expected_counts:
        raise RuntimeError("manifest entity counts mismatch")
    if {
        value.lower() for value in manifest["unit02_extension"].get("correction_ids", [])
    } != expected_corrections:
        raise RuntimeError("manifest correction closure differs from the live adverse ledger")
    csv_rows = list(csv.DictReader(io.StringIO(csv_bytes.decode("utf-8"))))
    if len(csv_rows) != len(records):
        raise RuntimeError("CSV row count mismatch")

    for label, value in (("records", records), ("manifest", manifest)):
        for key, string in walk_strings(value):
            folded = string.casefold()
            if key in {"path", "receipt_path", "build_receipt_path"} and (
                string.startswith(("/", "\\")) or WINDOWS_ABSOLUTE.search(string)
            ):
                raise RuntimeError(f"absolute path in {label}:{key}")
            if any(marker in folded for marker in PRIVATE_MARKERS):
                raise RuntimeError(f"private or credential marker in {label}:{key}")
    for record in records:
        source_display_id = record.get("source_display_id")
        if source_display_id and re.fullmatch(r"(?:3|4)\.2\.\d+", str(source_display_id)):
            raise RuntimeError(f"wrapper chapter prefix leaked into source_display_id in {record['id']}")

    unit02_counts = {
        entity_type: sum(record["entity_type"] == entity_type for record in unit02)
        for entity_type in sorted({record["entity_type"] for record in unit02})
    }
    receipt = {
        "schema_version": 1,
        "workflow": "o011-unit02-backend-qa-v1",
        "checkpoint_utc": args.checkpoint,
        "status": "pass",
        "validator": file_info(Path(__file__), root),
        "schema": {
            **file_info(schema_path, root),
            "draft": "2020-12",
            "rows_validated": len(records),
        },
        "outputs": {
            "records_jsonl": file_info(jsonl_path, root),
            "records_csv": file_info(csv_path, root),
            "manifest": file_info(manifest_path, root),
        },
        "deterministic_repeat": {
            "fixed_checkpoint": args.checkpoint,
            "runs_compared": 2,
            "jsonl_byte_identical": True,
            "csv_byte_identical": True,
            "manifest_byte_identical": True,
        },
        "unit01_preservation": {
            "baseline": file_info(baseline_path, root),
            "baseline_record_count": len(baseline_records),
            "extracted_record_count": len(extracted),
            "extracted_sha256": digest(extracted_bytes),
            "byte_identical": True,
        },
        "unit02": {
            "record_count": len(unit02),
            "entity_counts": unit02_counts,
            "exercise_count": 19,
            "solution_count": 5,
            "solution_indices": [1, 2, 7, 12, 13],
            "segment_count": 3,
            "concept_count": 4,
            "artifact_count": len(artifacts),
            "qa_event_count": len(qa_events),
            "asset_count": len(assets),
            "rights_count": len(rights),
            "correction_count": len(corrections),
            "cumulative_pdf": {
                "path": pdf_artifact["path"],
                "bytes": pdf_artifact["bytes"],
                "sha256": pdf_artifact["target_sha256"],
                "qa_event_ids": sorted(expected_reader_qa),
            },
            "source_numbering_preserved": True,
            "target_hashes": manifest["unit02_extension"]["target_hashes"],
        },
        "checks": {
            "unique_ids": True,
            "references_resolved": True,
            "csv_row_count_matches": True,
            "manifest_counts_match": True,
            "artifact_hashes_current": True,
            "qa_receipt_hashes_current": True,
            "absolute_paths_absent": True,
            "private_and_credential_markers_absent": True,
            "wrapper_chapter_prefixes_absent_from_source_display_ids": True,
        },
    }
    output_path = root / "qa/unit-02/backend_qa.json"
    receipt_bytes = (
        json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    ).encode("utf-8")
    assert_public_safe_bytes("qa/unit-02/backend_qa.json", receipt_bytes)
    output_path.write_bytes(receipt_bytes)


if __name__ == "__main__":
    main()
