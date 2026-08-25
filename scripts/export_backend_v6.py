#!/usr/bin/env python3
"""Finalize the deterministic Unit 6 extension of the O011 backend.

The first 969 JSONL records and first 970 CSV lines are immutable Units 1-5
bytes.  The already-admitted 204-record Unit 6 suffix is used as a semantic
template: its IDs and non-binding content are fingerprinted before live hashes,
QA counts, the checkpoint, and the final translation state are refreshed.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
from collections import Counter
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


BASELINE_RECORD_COUNT = 969
BASELINE_JSONL_BYTES = 576_960
BASELINE_JSONL_SHA256 = "bdd82d81cdac5cf30338d8fa0705189808ec4d746995127d02cbf4a248333227"
BASELINE_CSV_BYTES = 201_742
BASELINE_CSV_SHA256 = "ab7c40867434141e5f0a102db6b9a92a73677a3a946d96c3adbd925e77130592"
WORKFLOW = "o011-export-backend-v6"
MODEL_IDENTIFICATION = "OpenAI Codex gpt-5.6-sol, Ultra"
TRANSLATION_STATE = "visually_checked"
SOLUTION_INDICES = (2, 6, 9)
SOLUTION_ABSENT_INDICES = (1, 3, 4, 5, 7, 8, 10, 11, 12, 13, 14, 15, 16, 17, 18)
CORRECTION_NAMES = tuple(f"O011-CORR-{number:04d}" for number in range(54, 70))
TERM_NAMES = tuple(f"O011-TERM-{number:04d}" for number in range(111, 135))
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


def file_binding(path: Path, root: Path) -> dict[str, object]:
    data = path.read_bytes()
    return {
        "path": path.relative_to(root).as_posix(),
        "bytes": len(data),
        "sha256": sha256_bytes(data),
    }


def load_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def marker_slices(text: str, pattern: str) -> list[str]:
    starts = [match.start() for match in re.finditer(pattern, text)]
    return [
        text[start : starts[index + 1] if index + 1 < len(starts) else len(text)]
        for index, start in enumerate(starts)
    ]


def semantic_projection(value: object) -> object:
    """Remove only live binding/state fields from the admitted semantic graph."""
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


def paths_for(root: Path) -> dict[str, Path]:
    relative = {
        "schema": "backend/schema/o011-record-v1.schema.json",
        "terminology": "00_control/TERMINOLOGY.csv",
        "adverse": "00_control/ADVERSE_LEDGER.csv",
        "authority": "qa/unit-06/AUTHORITY_PREFLIGHT.json",
        "authority_verify": "qa/unit-06/AUTHORITY_PREFLIGHT_VERIFY.json",
        "current_revision": "qa/unit-06/CURRENT_REVISION_CHECK.json",
        "solution_closure": "qa/unit-06/solution_closure.json",
        "media_manifest": "authority/brenner_media_rights_manifest.csv",
        "media_config": "source/unit_media.json",
        "asset_svg": "authority/media/Parallel transport sphere2.svg",
        "lecture_source": "authority/expanded/lecture06_source.de.tex",
        "lecture_target": "source/units/unit-06/lecture06.id.tex",
        "lecture_receipt": "qa/unit-06/lecture06_translation.json",
        "lecture_manifest": "00_control/LECTURE06_PROTECTED_CORRECTIONS.json",
        "worksheet_source": "authority/expanded/worksheet06_source.de.tex",
        "worksheet_target": "source/units/unit-06/worksheet06.id.tex",
        "worksheet_receipt": "qa/unit-06/worksheet06_translation.json",
        "worksheet_manifest": "00_control/WORKSHEET06_PROTECTED_CORRECTIONS.json",
        "solution02_source": "authority/expanded/worksheet06_exercise02_solution_source.de.tex",
        "solution02_target": "source/units/unit-06/worksheet06_exercise02_solution.id.tex",
        "solution02_receipt": "qa/unit-06/worksheet06_exercise02_solution_translation.json",
        "solution02_manifest": "00_control/SOLUTION06_02_PROTECTED_CORRECTIONS.json",
        "solution06_source": "authority/expanded/worksheet06_exercise06_solution_source.de.tex",
        "solution06_target": "source/units/unit-06/worksheet06_exercise06_solution.id.tex",
        "solution06_receipt": "qa/unit-06/worksheet06_exercise06_solution_translation.json",
        "solution09_source": "authority/expanded/worksheet06_exercise09_solution_source.de.tex",
        "solution09_target": "source/units/unit-06/worksheet06_exercise09_solution.id.tex",
        "solution09_receipt": "qa/unit-06/worksheet06_exercise09_solution_translation.json",
        "final_math": "qa/unit-06/POST_REPAIR_MATH_QA.json",
        "terminology_audit": "qa/terminology/FIELD_TERMINOLOGY_AUDIT_20260822.md",
        "terminology_propagation": "qa/terminology/FIELD_TERMINOLOGY_PROPAGATION_U01_U06.json",
        "reader_wrapper": "build/through-unit-06.tex",
        "reader_pdf": "output/pdf/geometri-diferensial-manifold-mulus-hingga-unit-06-id.pdf",
        "build": "qa/unit-06/build.json",
        "structural": "qa/unit-06/pdf_structural_qa.json",
        "visual": "qa/unit-06/VISUAL_QA.md",
        "exporter": "scripts/export_backend_v6.py",
        "verifier": "scripts/verify_backend_v6.py",
    }
    return {key: root / value for key, value in relative.items()}


def validate_inputs(
    paths: dict[str, Path],
    bindings: dict[str, dict[str, object]],
    raw: dict[str, bytes],
) -> dict[str, object]:
    for key, expected in EXPECTED_FINAL_BINDINGS.items():
        actual = (bindings[key]["bytes"], bindings[key]["sha256"])
        if actual != expected:
            raise RuntimeError(f"final {key} identity changed: {actual} != {expected}")

    authority = load_json(paths["authority"])
    authority_verify = load_json(paths["authority_verify"])
    current_revision = load_json(paths["current_revision"])
    solution_closure = load_json(paths["solution_closure"])
    final_math = load_json(paths["final_math"])
    terminology_propagation = load_json(paths["terminology_propagation"])
    build = load_json(paths["build"])
    structural = load_json(paths["structural"])

    if authority.get("status") != "pass" or not authority.get("checks", {}).get(
        "unit_media_binary_and_rights_closure"
    ):
        raise RuntimeError("Unit 6 authority/media closure is not passing")
    if authority_verify.get("status") != "pass":
        raise RuntimeError("Unit 6 authority verification is not passing")
    if current_revision.get("status") != "pass" or not current_revision.get(
        "all_four_frozen_revisions_remain_live_current"
    ):
        raise RuntimeError("Unit 6 current-revision closure is not passing")

    exercises = solution_closure.get("exercises")
    if (
        solution_closure.get("exercise_count") != 18
        or solution_closure.get("supplied_solution_indices") != list(SOLUTION_INDICES)
        or solution_closure.get("supplied_solution_count") != 3
        or solution_closure.get("missing_solution_count") != 15
        or solution_closure.get("graded_exercise_count") != 4
        or solution_closure.get("practice_exercise_count") != 14
        or solution_closure.get("point_value_total") != 14
        or not isinstance(exercises, list)
        or len(exercises) != 18
    ):
        raise RuntimeError("Unit 6 exercise/solution/point closure changed")
    if [item.get("exercise_index") for item in exercises] != list(range(1, 19)):
        raise RuntimeError("Unit 6 exercise order changed")
    if any(item.get("hint_field") for item in exercises):
        raise RuntimeError("Unit 6 unexpectedly contains a source hint")
    point_values = [item.get("point_value") for item in exercises if item.get("point_value") is not None]
    if point_values != [2, 4, 4, 4]:
        raise RuntimeError("Unit 6 graded point markers changed")

    media = authority.get("media", {})
    assets = media.get("assets", []) if isinstance(media, dict) else []
    if media.get("unique_asset_count") != 1 or len(assets) != 1:
        raise RuntimeError("Unit 6 media asset count changed")
    media_item = assets[0]
    if (
        media_item.get("filename") != "Parallel transport sphere2.svg"
        or media_item.get("license") != "CC BY-SA 3.0"
        or media_item.get("artist_identity", {}).get("creator_label") != "Silly rabbit"
        or media_item.get("sha256") != bindings["asset_svg"]["sha256"]
        or media_item.get("bytes") != bindings["asset_svg"]["bytes"]
        or media_item.get("rights_critical_fields_match") is not True
    ):
        raise RuntimeError("Unit 6 media identity or rights changed")
    media_config = load_json(paths["media_config"])
    configured = media_config.get("units", {}).get("6", {}).get("media", [])
    if len(configured) != 1 or configured[0].get("filename") != "Parallel transport sphere2.svg":
        raise RuntimeError("Unit 6 reader media configuration changed")

    expected_targets = {
        "lecture": bindings["lecture_target"]["sha256"],
        "worksheet": bindings["worksheet_target"]["sha256"],
        "solution_02": bindings["solution02_target"]["sha256"],
        "solution_06": bindings["solution06_target"]["sha256"],
        "solution_09": bindings["solution09_target"]["sha256"],
    }
    if (
        final_math.get("status") != "pass"
        or final_math.get("checks_passed") != EXPECTED_MATH_CHECKS
        or final_math.get("correction_ids") != list(CORRECTION_NAMES)
        or final_math.get("exercise_topology", {}).get("solution_bearing_indices") != list(SOLUTION_INDICES)
        or final_math.get("target_sha256") != expected_targets
    ):
        raise RuntimeError("Unit 6 final mathematical QA changed")

    receipts = (
        ("lecture_receipt", "lecture_target", "lecture_source"),
        ("worksheet_receipt", "worksheet_target", "worksheet_source"),
        ("solution02_receipt", "solution02_target", "solution02_source"),
        ("solution06_receipt", "solution06_target", "solution06_source"),
        ("solution09_receipt", "solution09_target", "solution09_source"),
    )
    for receipt_key, target_key, source_key in receipts:
        receipt = load_json(paths[receipt_key])
        if (
            receipt.get("status") != "pass"
            or receipt.get("source_sha256") != bindings[source_key]["sha256"]
            or receipt.get("source_bytes") != bindings[source_key]["bytes"]
            or receipt.get("target_sha256") != bindings[target_key]["sha256"]
            or receipt.get("target_bytes") != bindings[target_key]["bytes"]
        ):
            raise RuntimeError(f"failed or stale translation receipt: {receipt_key}")
    for key in ("lecture_manifest", "worksheet_manifest", "solution02_manifest"):
        if not isinstance(load_json(paths[key]).get("allowed_deltas"), list):
            raise RuntimeError(f"invalid correction manifest: {key}")

    if (
        terminology_propagation.get("status") != "pass"
        or terminology_propagation.get("files_checked") != 26
        or terminology_propagation.get("files_changed") != 0
        or terminology_propagation.get("preserved_asset_identity") != "Parallel transport sphere2.svg"
        or any(value != 0 for value in terminology_propagation.get("post_checks", {}).values())
    ):
        raise RuntimeError("Unit 1-6 terminology propagation is not closed")
    if MODEL_IDENTIFICATION not in raw["terminology_audit"].decode("utf-8"):
        raise RuntimeError("terminology audit omits exact model identification")
    if raw["reader_wrapper"].decode("utf-8").count(MODEL_IDENTIFICATION) != 1:
        raise RuntimeError("reader wrapper must contain exact model identification once")

    pdf_binding = bindings["reader_pdf"]
    if (
        build.get("output", {}).get("path") != pdf_binding["path"]
        or build.get("output", {}).get("bytes") != pdf_binding["bytes"]
        or build.get("output", {}).get("sha256") != pdf_binding["sha256"]
        or build.get("deterministic_clean_cycles") is not True
        or len(build.get("cycles", [])) != 2
        or any(
            cycle.get("bytes") != pdf_binding["bytes"]
            or cycle.get("sha256") != pdf_binding["sha256"]
            for cycle in build.get("cycles", [])
        )
    ):
        raise RuntimeError("final Unit 6 PDF build receipt is stale")
    if (
        structural.get("passed") is not True
        or structural.get("pdf", {}).get("path") != pdf_binding["path"]
        or structural.get("pdf", {}).get("bytes") != pdf_binding["bytes"]
        or structural.get("pdf", {}).get("sha256") != pdf_binding["sha256"]
    ):
        raise RuntimeError("final Unit 6 PDF structural receipt is stale")
    visual_text = raw["visual"].decode("utf-8")
    if str(pdf_binding["sha256"]) not in visual_text or "Pass." not in visual_text:
        raise RuntimeError("final Unit 6 PDF visual receipt is stale")

    return {
        "authority": authority,
        "solution_closure": solution_closure,
        "final_math": final_math,
        "terminology_propagation": terminology_propagation,
        "media_item": media_item,
        "structural": structural,
    }


def refresh_records(
    records: list[dict[str, object]],
    checkpoint: str,
    paths: dict[str, Path],
    bindings: dict[str, dict[str, object]],
    raw: dict[str, bytes],
    evidence: dict[str, object],
) -> list[dict[str, object]]:
    if len(records) != EXPECTED_EXTENSION_COUNT:
        raise RuntimeError("Unit 6 semantic template record count changed")
    if [record.get("id") for record in records] != sorted(record.get("id") for record in records):
        raise RuntimeError("Unit 6 semantic template is not ID-sorted")
    ids_data = ("\n".join(str(record["id"]) for record in records) + "\n").encode("utf-8")
    if sha256_bytes(ids_data) != EXPECTED_RECORD_IDS_SHA256:
        raise RuntimeError("Unit 6 semantic template IDs changed")
    if semantic_sha256(records) != EXPECTED_SEMANTIC_SHA256:
        raise RuntimeError("Unit 6 semantic extension changed")

    by_id = {str(record["id"]): record for record in records}
    for record in records:
        record["timestamp"] = checkpoint
        record["workflow"] = WORKFLOW
        if "translation_state" in record:
            record["translation_state"] = TRANSLATION_STATE

    lecture_source = raw["lecture_source"].decode("utf-8")
    lecture_target = raw["lecture_target"].decode("utf-8")
    worksheet_source = raw["worksheet_source"].decode("utf-8")
    worksheet_target = raw["worksheet_target"].decode("utf-8")
    lecture_source_parts = marker_slices(lecture_source, r"\\zwischenueberschrift\{")
    lecture_target_parts = marker_slices(lecture_target, r"\\zwischenueberschrift\{")
    worksheet_source_parts = marker_slices(worksheet_source, r"\\inputaufgabe(?:gibtloesung)?")
    worksheet_target_parts = marker_slices(worksheet_target, r"\\inputaufgabe(?:gibtloesung)?")
    if len(lecture_source_parts) != 3 or len(lecture_target_parts) != 3:
        raise RuntimeError("Unit 6 lecture must have exactly three sections")
    if len(worksheet_source_parts) != 18 or len(worksheet_target_parts) != 18:
        raise RuntimeError("Unit 6 worksheet must have exactly eighteen exercises")

    unit = by_id["o011-brenner-u06"]
    unit["source_sha256"] = sha256_bytes(raw["lecture_source"] + raw["worksheet_source"])
    unit["target_sha256"] = sha256_bytes(raw["lecture_target"] + raw["worksheet_target"])
    unit["translation_assistance"]["model"] = MODEL_IDENTIFICATION

    direct_units = {
        "o011-brenner-u06-l06": ("lecture_source", "lecture_target"),
        "o011-brenner-u06-w06": ("worksheet_source", "worksheet_target"),
        "o011-brenner-u06-w06-e002-solution": ("solution02_source", "solution02_target"),
        "o011-brenner-u06-w06-e006-solution": ("solution06_source", "solution06_target"),
        "o011-brenner-u06-w06-e009-solution": ("solution09_source", "solution09_target"),
    }
    for record_id, (source_key, target_key) in direct_units.items():
        record = by_id[record_id]
        record["source_sha256"] = bindings[source_key]["sha256"]
        record["target_sha256"] = bindings[target_key]["sha256"]

    for index, (source_part, target_part) in enumerate(zip(lecture_source_parts, lecture_target_parts), 1):
        record = by_id[f"o011-brenner-u06-l06-s{index:02d}"]
        record["source_sha256"] = sha256_bytes(source_part.encode("utf-8"))
        record["target_sha256"] = sha256_bytes(target_part.encode("utf-8"))
    for index, (source_part, target_part) in enumerate(zip(worksheet_source_parts, worksheet_target_parts), 1):
        record = by_id[f"o011-brenner-u06-w06-e{index:03d}"]
        record["source_sha256"] = sha256_bytes(source_part.encode("utf-8"))
        record["target_sha256"] = sha256_bytes(target_part.encode("utf-8"))

    artifact_keys = {
        "o011-artifact-u06-l06-tex": ("lecture_target", "lecture_source"),
        "o011-artifact-u06-w06-tex": ("worksheet_target", "worksheet_source"),
        "o011-artifact-u06-w06-e002-solution-tex": ("solution02_target", "solution02_source"),
        "o011-artifact-u06-w06-e006-solution-tex": ("solution06_target", "solution06_source"),
        "o011-artifact-u06-w06-e009-solution-tex": ("solution09_target", "solution09_source"),
        "o011-artifact-u06-terminology-field-audit": ("terminology_audit", None),
        "o011-artifact-u06-terminology-propagation": ("terminology_propagation", None),
        "o011-artifact-u06-reader-wrapper-provenance": ("reader_wrapper", None),
    }
    for record_id, (target_key, source_key) in artifact_keys.items():
        record = by_id[record_id]
        record["path"] = bindings[target_key]["path"]
        record["bytes"] = bindings[target_key]["bytes"]
        record["target_sha256"] = bindings[target_key]["sha256"]
        if source_key is not None:
            record["source_sha256"] = bindings[source_key]["sha256"]
    by_id["o011-artifact-u06-reader-wrapper-provenance"]["model_identification"] = MODEL_IDENTIFICATION

    asset = by_id["o011-asset-file-parallel-transport-sphere2-svg"]
    asset["path"] = bindings["asset_svg"]["path"]
    asset["source_sha256"] = bindings["asset_svg"]["sha256"]
    asset["expected_bytes"] = bindings["asset_svg"]["bytes"]

    for record in records:
        if record.get("entity_type") == "correction":
            record["ledger_sha256"] = bindings["adverse"]["sha256"]
            record["target_bindings"] = [
                {**file_binding(paths[str(item["path_key"])] if "path_key" in item else paths_for_path(paths, str(item["path"])), paths["schema"].parents[2]), "target_id": item["target_id"]}
                if "path_key" in item else {**file_binding(paths_for_path(paths, str(item["path"])), paths["schema"].parents[2]), "target_id": item["target_id"]}
                for item in record.get("target_bindings", [])
            ]
            record["correction_manifests"] = [
                file_binding(paths_for_path(paths, str(item["path"])), paths["schema"].parents[2])
                for item in record.get("correction_manifests", [])
            ]
            record["validation_binding"] = {
                **bindings["final_math"],
                "checks_passed": evidence["final_math"]["checks_passed"],
            }

    for record in records:
        if record.get("entity_type") == "qa_event":
            receipt_path = paths_for_path(paths, str(record["receipt_path"]))
            record["evidence_sha256"] = sha256_bytes(receipt_path.read_bytes())
    final_math_event = by_id["o011-qa-unit06-final-math"]
    final_math_event["values"]["checks_passed"] = evidence["final_math"]["checks_passed"]
    final_math_event["values"]["correction_ids"] = list(CORRECTION_NAMES)
    propagation_event = by_id["o011-qa-unit06-terminology-propagation"]
    propagation_event["values"]["files_checked"] = evidence["terminology_propagation"]["files_checked"]
    propagation_event["values"]["files_changed_on_idempotence_rerun"] = evidence["terminology_propagation"]["files_changed"]

    terminology_hash = bindings["terminology"]["sha256"]
    audit_hash = bindings["terminology_audit"]["sha256"]
    for number in range(111, 135):
        term = by_id[f"o011-term-{number:04d}"]
        term["terminology_ledger_sha256"] = terminology_hash
        term["field_audit_sha256"] = audit_hash

    rights = by_id["o011-rights-media-u06-01"]
    rights["evidence_sha256"] = bindings["authority"]["sha256"]
    rights["media_rights_manifest_sha256"] = bindings["media_manifest"]["sha256"]

    if semantic_sha256(records) != EXPECTED_SEMANTIC_SHA256:
        raise RuntimeError("refresh changed the Unit 6 semantic extension")
    return sorted(records, key=lambda record: str(record["id"]))


def paths_for_path(paths: dict[str, Path], relative_path: str) -> Path:
    root = paths["schema"].parents[2]
    candidate = root / relative_path
    if not candidate.is_file():
        raise RuntimeError(f"bound file is missing: {relative_path}")
    return candidate


def validate_records(
    baseline_records: list[dict[str, object]],
    added: list[dict[str, object]],
    schema: dict[str, object],
) -> dict[str, int]:
    entity_counts = Counter(str(record.get("entity_type")) for record in added)
    actual_counts = {kind: entity_counts.get(kind, 0) for kind in sorted(ENTITY_TYPES)}
    if actual_counts != EXPECTED_ENTITY_COUNTS:
        raise RuntimeError(f"Unit 6 entity closure changed: {actual_counts}")
    all_records = baseline_records + added
    all_ids = {str(record["id"]) for record in all_records}
    if len(all_ids) != len(all_records):
        raise RuntimeError("combined backend IDs are not unique")
    for record in added:
        for key in ("parent_id", "resource_id", "edition_id", "rights_component_id", "target_id", "artifact_id"):
            value = record.get(key)
            if value is not None and str(value) not in all_ids:
                raise RuntimeError(f"unresolved {key} on {record['id']}: {value}")
        for key in ("component_rights_ids", "target_ids"):
            for value in record.get(key) or []:
                if str(value) not in all_ids:
                    raise RuntimeError(f"unresolved {key} on {record['id']}: {value}")
        if record.get("entity_type") == "relation":
            for key in ("from_id", "to_id"):
                if str(record.get(key)) not in all_ids:
                    raise RuntimeError(f"unresolved relation endpoint on {record['id']}")
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors: list[str] = []
    for record in all_records:
        errors.extend(f"{record['id']}: {error.message}" for error in validator.iter_errors(record))
    if errors:
        raise RuntimeError("JSON Schema validation failed: " + "; ".join(errors[:10]))
    return actual_counts


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--translation-state", default=TRANSLATION_STATE)
    args = parser.parse_args()
    if args.translation_state != TRANSLATION_STATE:
        raise RuntimeError(f"Unit 6 final backend state must be {TRANSLATION_STATE}")

    root = args.root.resolve()
    jsonl_path = root / "backend/records.jsonl"
    csv_path = root / "backend/records.csv"
    manifest_path = root / "backend/MANIFEST.json"
    jsonl_lines = jsonl_path.read_bytes().splitlines(keepends=True)
    if len(jsonl_lines) != BASELINE_RECORD_COUNT + EXPECTED_EXTENSION_COUNT:
        raise RuntimeError("backend does not contain the admitted 969+204 record topology")
    baseline_jsonl = b"".join(jsonl_lines[:BASELINE_RECORD_COUNT])
    if len(baseline_jsonl) != BASELINE_JSONL_BYTES or sha256_bytes(baseline_jsonl) != BASELINE_JSONL_SHA256:
        raise RuntimeError("immutable 969-record JSONL prefix changed")
    baseline_records = [json.loads(line.decode("utf-8")) for line in jsonl_lines[:BASELINE_RECORD_COUNT]]
    added = [json.loads(line.decode("utf-8")) for line in jsonl_lines[BASELINE_RECORD_COUNT:]]

    csv_lines = csv_path.read_bytes().splitlines(keepends=True)
    if len(csv_lines) != BASELINE_RECORD_COUNT + EXPECTED_EXTENSION_COUNT + 1:
        raise RuntimeError("backend CSV does not contain the admitted 969+204 row topology")
    baseline_csv = b"".join(csv_lines[: BASELINE_RECORD_COUNT + 1])
    if len(baseline_csv) != BASELINE_CSV_BYTES or sha256_bytes(baseline_csv) != BASELINE_CSV_SHA256:
        raise RuntimeError("immutable 969-row CSV prefix changed")

    paths = paths_for(root)
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise RuntimeError(f"missing Unit 6 backend inputs: {missing}")
    bindings = {key: file_binding(path, root) for key, path in paths.items()}
    raw = {key: path.read_bytes() for key, path in paths.items()}
    evidence = validate_inputs(paths, bindings, raw)
    added = refresh_records(added, args.checkpoint, paths, bindings, raw, evidence)
    entity_counts = validate_records(baseline_records, added, load_json(paths["schema"]))

    extension_jsonl = b"".join(canonical_json(record) for record in added)
    jsonl_path.write_bytes(baseline_jsonl + extension_jsonl)
    csv_buffer = io.StringIO(newline="")
    writer = csv.DictWriter(
        csv_buffer,
        fieldnames=CSV_FIELDS,
        extrasaction="ignore",
        lineterminator="\r\n",
    )
    for record in added:
        writer.writerow({field: record.get(field) for field in CSV_FIELDS})
    csv_path.write_bytes(baseline_csv + csv_buffer.getvalue().encode("utf-8"))

    output_bindings = {
        "records_jsonl": file_binding(jsonl_path, root),
        "records_csv": file_binding(csv_path, root),
    }
    combined_counts = Counter(str(record.get("entity_type")) for record in baseline_records + added)
    manifest = {
        "schema_version": 1,
        "workflow": WORKFLOW,
        "checkpoint": args.checkpoint,
        "generator": bindings["exporter"],
        "verifier": bindings["verifier"],
        "baseline": {
            "record_count": BASELINE_RECORD_COUNT,
            "jsonl_bytes": BASELINE_JSONL_BYTES,
            "jsonl_sha256": BASELINE_JSONL_SHA256,
            "csv_lines_including_header": BASELINE_RECORD_COUNT + 1,
            "csv_bytes": BASELINE_CSV_BYTES,
            "csv_sha256": BASELINE_CSV_SHA256,
            "preserved_byte_identically": True,
        },
        "unit06_extension": {
            "record_count": len(added),
            "entity_counts": entity_counts,
            "record_ids_sha256": EXPECTED_RECORD_IDS_SHA256,
            "semantic_projection_sha256": EXPECTED_SEMANTIC_SHA256,
            "unit_id": "o011-brenner-u06",
            "lecture_segment_count": 3,
            "exercise_count": 18,
            "hint_indices": [],
            "source_solution_indices": list(SOLUTION_INDICES),
            "source_solution_absent_indices": list(SOLUTION_ABSENT_INDICES),
            "graded_point_values": [2, 4, 4, 4],
            "graded_point_total": 14,
            "terminology_ids": list(TERM_NAMES),
            "correction_ids": list(CORRECTION_NAMES),
            "asset_ids": ["o011-asset-file-parallel-transport-sphere2-svg"],
            "component_rights_ids": ["o011-rights-media-u06-01"],
            "model_identification": MODEL_IDENTIFICATION,
            "translation_state": TRANSLATION_STATE,
            "pdf_status": "final_cumulative_reader_bound",
            "pdf": bindings["reader_pdf"],
            "html_status": "absent_not_claimed",
        },
        "inputs": bindings,
        "outputs": output_bindings,
        "combined": {
            "record_count": len(baseline_records) + len(added),
            "entity_counts": {kind: combined_counts.get(kind, 0) for kind in sorted(ENTITY_TYPES)},
        },
        "claims": {
            "all_ids_unique": True,
            "all_references_resolve": True,
            "json_schema_valid": True,
            "unit06_translation_receipts_current": True,
            "unit06_authority_solution_media_closure_current": True,
            "unit06_correction_manifests_and_targets_current": True,
            "unit06_terminology_and_provenance_current": True,
            "unit06_pdf_build_structural_visual_receipts_current": True,
            "cumulative_pdf_present": True,
            "cumulative_html_present": False,
        },
    }
    manifest_path.write_bytes(
        (json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    )
    print(json.dumps({
        "status": "pass",
        "baseline_records": BASELINE_RECORD_COUNT,
        "added_records": len(added),
        "combined_records": len(baseline_records) + len(added),
        "entity_counts": entity_counts,
        "jsonl": file_binding(jsonl_path, root),
        "csv": file_binding(csv_path, root),
        "manifest": file_binding(manifest_path, root),
    }, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
