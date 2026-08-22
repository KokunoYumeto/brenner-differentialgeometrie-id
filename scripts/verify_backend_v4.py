#!/usr/bin/env python3
"""Verify the deterministic Unit 4 extension of the O011 modular backend."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from jsonschema import Draft202012Validator, FormatChecker


BASELINE_RECORD_COUNT = 591
BASELINE_JSONL_BYTES = 350_935
BASELINE_JSONL_SHA256 = "e2b1e159b1dff04273ddb0af82e85dc32adbb507f3936881f750867527d6800a"
BASELINE_CSV_BYTES = 125_961
BASELINE_CSV_SHA256 = "bdd4648d7e104da5f96a20ff85850a8782379f02609c3f29ed88117401032941"
WORKFLOW = "o011-export-backend-v4"
SOLUTION_INDICES = (7, 10)
ENTITY_TYPES = {
    "program", "course", "resource", "edition", "unit", "concept",
    "segment", "term", "asset", "relation", "rights", "qa_event",
    "artifact", "correction",
}
COMMON = (
    "schema", "schema_version", "id", "entity_type", "source_local_id",
    "parent_id", "order", "path", "resource_id", "edition_id",
    "source_locator", "source_sha256", "target_sha256", "language",
    "locale", "translation_state", "rights_component_id", "status",
    "timestamp", "workflow", "supersedes",
)
LECTURE_MARKER = re.compile(r"(?m)^\s*\\zwischenueberschrift\s*\{")
EXERCISE_MARKER = re.compile(r"(?m)^\s*\\(?:inputaufgabegibtloesung|inputaufgabe)\b")
WINDOWS_ABSOLUTE = re.compile(r"(?i)(?<![a-z0-9+.-])[a-z]:[\\/]")
PRIVATE_MARKERS = (
    "\\users\\", "/users/", "\\appdata\\", "/home/", "github_pat_",
    "ghp_", "gho_", "ghu_", "ghs_", "ghr_", "glpat-", "sk-proj-",
    "xoxb-", "bearer ", "access_token", "api_key", "zenodo token",
)

UNIT_ID = "o011-brenner-u04"
LECTURE_ID = "o011-brenner-u04-l04"
WORKSHEET_ID = "o011-brenner-u04-w04"
EXPECTED_UNITS = {
    UNIT_ID, LECTURE_ID, WORKSHEET_ID,
    *(f"{WORKSHEET_ID}-e{index:03d}" for index in range(1, 16)),
    *(f"{WORKSHEET_ID}-e{index:03d}-solution" for index in SOLUTION_INDICES),
}
EXPECTED_SEGMENTS = {f"{LECTURE_ID}-s01"}
EXPECTED_CONCEPTS = {
    "o011-concept-weingarten-map",
    "o011-concept-normal-acceleration",
    "o011-concept-shape-operator-self-adjoint",
    "o011-concept-shape-operator-diagonalization",
    "o011-concept-graph-shape-operator",
}
EXPECTED_TERMS = {f"o011-term-{index:04d}" for index in range(78, 96)}
EXPECTED_RIGHTS = {"o011-rights-u04-official-pdf-witness"}
EXPECTED_CORRECTIONS = {f"o011-corr-{index:04d}" for index in range(38, 46)}
EXPECTED_ARTIFACTS = {
    "o011-artifact-u04-l04-tex",
    "o011-artifact-u04-w04-tex",
    "o011-artifact-u04-w04-e007-solution-tex",
    "o011-artifact-u04-w04-e010-solution-tex",
    "o011-artifact-through-unit04-pdf",
    "o011-artifact-u04-official-pdf-witness",
}
QA_TARGETS = {
    "o011-qa-unit04-authority-preflight": UNIT_ID,
    "o011-qa-unit04-authority-verification": UNIT_ID,
    "o011-qa-unit04-current-revision": UNIT_ID,
    "o011-qa-unit04-solution-closure": WORKSHEET_ID,
    "o011-qa-unit04-media-authority-closure": UNIT_ID,
    "o011-qa-unit04-media-build-closure": UNIT_ID,
    "o011-qa-unit04-authority-anomalies": UNIT_ID,
    "o011-qa-unit04-official-pdf-witness": "o011-artifact-u04-official-pdf-witness",
    "o011-qa-unit04-official-pdf-structural-visual": "o011-artifact-u04-official-pdf-witness",
    "o011-qa-unit04-lecture-math-review": LECTURE_ID,
    "o011-qa-unit04-worksheet-math-review": WORKSHEET_ID,
    "o011-qa-unit04-final-math-audit": UNIT_ID,
    "o011-qa-through-unit04-pdf-reproducibility": "o011-artifact-through-unit04-pdf",
    "o011-qa-through-unit04-pdf-structural": "o011-artifact-through-unit04-pdf",
    "o011-qa-through-unit04-pdf-visual": "o011-artifact-through-unit04-pdf",
    "o011-qa-unit04-lecture-translation": LECTURE_ID,
    "o011-qa-unit04-worksheet-translation": WORKSHEET_ID,
    "o011-qa-unit04-solution07-translation": f"{WORKSHEET_ID}-e007-solution",
    "o011-qa-unit04-solution10-translation": f"{WORKSHEET_ID}-e010-solution",
}
ARTIFACT_TARGETS = {
    "o011-artifact-u04-l04-tex": LECTURE_ID,
    "o011-artifact-u04-w04-tex": WORKSHEET_ID,
    "o011-artifact-u04-w04-e007-solution-tex": f"{WORKSHEET_ID}-e007-solution",
    "o011-artifact-u04-w04-e010-solution-tex": f"{WORKSHEET_ID}-e010-solution",
}
CORRECTION_TARGETS = {
    "o011-corr-0038": f"{WORKSHEET_ID}-e002",
    "o011-corr-0039": f"{WORKSHEET_ID}-e007-solution",
    "o011-corr-0040": f"{WORKSHEET_ID}-e010-solution",
    "o011-corr-0041": LECTURE_ID,
    "o011-corr-0042": LECTURE_ID,
    "o011-corr-0043": LECTURE_ID,
    "o011-corr-0044": f"{WORKSHEET_ID}-e006",
    "o011-corr-0045": f"{WORKSHEET_ID}-e009",
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def repository_path(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def file_info(path: Path, root: Path) -> dict[str, object]:
    data = path.read_bytes()
    return {"path": repository_path(path, root), "bytes": len(data), "sha256": digest(data)}


def extract_prefix(data: bytes, line_count: int, label: str) -> bytes:
    lines = data.splitlines(keepends=True)
    if len(lines) < line_count:
        raise RuntimeError(f"{label} has fewer than {line_count} lines")
    prefix = b"".join(lines[:line_count])
    if not prefix.endswith(b"\n"):
        raise RuntimeError(f"{label} prefix is not LF terminated")
    return prefix


def slices(text: str, marker: re.Pattern[str]) -> list[str]:
    matches = list(marker.finditer(text))
    return [
        text[m.start() : (matches[i + 1].start() if i + 1 < len(matches) else len(text))]
        for i, m in enumerate(matches)
    ]


def require_hash(value: str, label: str) -> str:
    lowered = value.lower()
    if not re.fullmatch(r"[0-9a-f]{64}", lowered):
        raise RuntimeError(f"{label} is not a SHA-256 digest")
    return lowered


def assert_public_safe_bytes(label: str, data: bytes) -> None:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RuntimeError(f"{label} is not UTF-8") from exc
    folded = text.casefold()
    if WINDOWS_ABSOLUTE.search(text):
        raise RuntimeError(f"absolute Windows path leaked into {label}")
    found = [marker for marker in PRIVATE_MARKERS if marker in folded]
    if found:
        raise RuntimeError(f"private or credential marker leaked into {label}: {found}")


def walk_strings(value: object, key: str = "") -> Iterable[tuple[str, str]]:
    if isinstance(value, dict):
        for child_key, child in value.items():
            yield from walk_strings(child, str(child_key))
    elif isinstance(value, list):
        for child in value:
            yield from walk_strings(child, key)
    elif isinstance(value, str):
        yield key, value


def entity_ids(records: list[dict[str, Any]], entity_type: str) -> set[str]:
    return {str(record["id"]) for record in records if record.get("entity_type") == entity_type}


def live_binding(root: Path, binding: dict[str, Any], label: str) -> None:
    path_value = binding.get("path")
    if not isinstance(path_value, str) or not path_value:
        raise RuntimeError(f"{label} lacks a path")
    path = (root / path_value).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise RuntimeError(f"{label} escapes the project root") from exc
    data = path.read_bytes()
    if binding.get("bytes") != len(data) or binding.get("sha256") != digest(data):
        raise RuntimeError(f"stale live binding: {label}")


def validate_references(records: list[dict[str, Any]]) -> None:
    identifiers = {str(record["id"]) for record in records}
    if len(identifiers) != len(records):
        raise RuntimeError("duplicate stable IDs")
    for record in records:
        for field in (
            "parent_id", "resource_id", "edition_id", "rights_component_id",
            "target_id", "artifact_id",
        ):
            value = record.get(field)
            if value is not None and value not in identifiers:
                raise RuntimeError(f"unresolved {field}={value!r} in {record['id']}")
        for value in record.get("component_rights_ids") or []:
            if value not in identifiers:
                raise RuntimeError(f"unresolved component right {value!r} in {record['id']}")
        if record.get("entity_type") == "relation":
            if record.get("from_id") not in identifiers or record.get("to_id") not in identifiers:
                raise RuntimeError(f"unresolved relation endpoint in {record['id']}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--first-jsonl-sha256", required=True)
    parser.add_argument("--first-csv-sha256", required=True)
    parser.add_argument("--first-manifest-sha256", required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", args.checkpoint):
        raise RuntimeError("checkpoint must be explicit YYYY-MM-DDTHH:MM:SSZ")

    jsonl_path = root / "backend/records.jsonl"
    csv_path = root / "backend/records.csv"
    manifest_path = root / "backend/MANIFEST.json"
    schema_path = root / "backend/schema/o011-record-v1.schema.json"
    exporter_path = root / "scripts/export_backend_v4.py"
    jsonl_bytes = jsonl_path.read_bytes()
    csv_bytes = csv_path.read_bytes()
    manifest_bytes = manifest_path.read_bytes()
    for label, data in (
        ("records.jsonl", jsonl_bytes), ("records.csv", csv_bytes),
        ("MANIFEST.json", manifest_bytes),
    ):
        assert_public_safe_bytes(label, data)
    if digest(jsonl_bytes) != require_hash(args.first_jsonl_sha256, "first JSONL hash"):
        raise RuntimeError("JSONL differs from the first fixed-checkpoint export")
    if digest(csv_bytes) != require_hash(args.first_csv_sha256, "first CSV hash"):
        raise RuntimeError("CSV differs from the first fixed-checkpoint export")
    if digest(manifest_bytes) != require_hash(args.first_manifest_sha256, "first manifest hash"):
        raise RuntimeError("manifest differs from the first fixed-checkpoint export")

    baseline_jsonl = extract_prefix(jsonl_bytes, BASELINE_RECORD_COUNT, "records.jsonl")
    baseline_csv = extract_prefix(csv_bytes, BASELINE_RECORD_COUNT + 1, "records.csv")
    if len(baseline_jsonl) != BASELINE_JSONL_BYTES or digest(baseline_jsonl) != BASELINE_JSONL_SHA256:
        raise RuntimeError("immutable 591-record JSONL prefix changed")
    if len(baseline_csv) != BASELINE_CSV_BYTES or digest(baseline_csv) != BASELINE_CSV_SHA256:
        raise RuntimeError("immutable 591-row CSV prefix changed")

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(jsonl_bytes.splitlines(keepends=True), 1):
        if not line.endswith(b"\n"):
            raise RuntimeError(f"JSONL line {line_number} is not LF terminated")
        record = json.loads(line.decode("utf-8"))
        errors = sorted(validator.iter_errors(record), key=lambda error: list(error.path))
        if errors:
            raise RuntimeError(f"schema failure at line {line_number}: {errors[0].message}")
        if line_number > BASELINE_RECORD_COUNT and line != (canonical_json(record) + "\n").encode("utf-8"):
            raise RuntimeError(f"noncanonical Unit 4 JSONL row {line_number}")
        records.append(record)
    validate_references(records)
    baseline_records = records[:BASELINE_RECORD_COUNT]
    extension = records[BASELINE_RECORD_COUNT:]
    by_id = {str(record["id"]): record for record in records}
    extension_by_id = {str(record["id"]): record for record in extension}
    if list(extension_by_id) != sorted(extension_by_id):
        raise RuntimeError("Unit 4 JSONL suffix is not ID sorted")
    if any(record.get("workflow") != WORKFLOW or record.get("timestamp") != args.checkpoint for record in extension):
        raise RuntimeError("Unit 4 workflow/checkpoint binding changed")

    csv_reader = csv.DictReader(io.StringIO(csv_bytes.decode("utf-8")))
    csv_rows = list(csv_reader)
    if tuple(csv_reader.fieldnames or ()) != COMMON:
        raise RuntimeError("CSV header changed")
    if len(csv_rows) != len(records):
        raise RuntimeError("CSV and JSONL row counts differ")
    if [row["id"] for row in csv_rows] != [str(record["id"]) for record in records]:
        raise RuntimeError("CSV and JSONL stable-ID order differs")
    for row, record in zip(csv_rows[BASELINE_RECORD_COUNT:], extension):
        expected = {field: "" if record.get(field) is None else str(record.get(field)) for field in COMMON}
        if row != expected:
            raise RuntimeError(f"CSV/JSONL projection mismatch: {record['id']}")

    manifest = json.loads(manifest_bytes.decode("utf-8"))
    if manifest.get("schema_version") != 4 or manifest.get("generator") != "scripts/export_backend_v4.py":
        raise RuntimeError("manifest v4 identity changed")
    if manifest.get("generator_sha256") != digest(exporter_path.read_bytes()):
        raise RuntimeError("manifest exporter hash is stale")
    if manifest.get("timestamp") != args.checkpoint or manifest.get("record_count") != len(records):
        raise RuntimeError("manifest checkpoint or record count changed")
    cumulative_counts = {kind: sum(record.get("entity_type") == kind for record in records) for kind in sorted(ENTITY_TYPES)}
    extension_counts = {kind: sum(record.get("entity_type") == kind for record in extension) for kind in sorted(ENTITY_TYPES)}
    if manifest.get("entity_counts") != cumulative_counts:
        raise RuntimeError("manifest cumulative entity counts are stale")
    unit_manifest = manifest.get("unit04_extension") or {}
    if unit_manifest.get("record_count") != len(extension) or unit_manifest.get("entity_counts") != extension_counts:
        raise RuntimeError("manifest Unit 4 extension counts are stale")
    expected_preservation = {
        "path": "backend/records.jsonl", "record_count": BASELINE_RECORD_COUNT,
        "bytes": BASELINE_JSONL_BYTES, "sha256": BASELINE_JSONL_SHA256,
        "byte_identical_prefix": True,
        "csv_path": "backend/records.csv", "csv_bytes": BASELINE_CSV_BYTES,
        "csv_sha256": BASELINE_CSV_SHA256, "csv_byte_identical_prefix": True,
    }
    if manifest.get("unit123_baseline_preservation") != expected_preservation:
        raise RuntimeError("manifest 591-record preservation claim changed")
    if manifest.get("outputs") != {
        "records.jsonl": {"bytes": len(jsonl_bytes), "sha256": digest(jsonl_bytes)},
        "records.csv": {"bytes": len(csv_bytes), "sha256": digest(csv_bytes)},
    }:
        raise RuntimeError("manifest output hashes are stale")
    inputs = manifest.get("inputs") or {}
    if inputs.get("unit123_baseline_jsonl") != {
        "path": "backend/records.jsonl", "bytes": BASELINE_JSONL_BYTES,
        "sha256": BASELINE_JSONL_SHA256,
    } or inputs.get("unit123_baseline_csv") != {
        "path": "backend/records.csv", "bytes": BASELINE_CSV_BYTES,
        "sha256": BASELINE_CSV_SHA256,
    }:
        raise RuntimeError("manifest baseline input bindings changed")
    for key, binding in inputs.items():
        if key not in {"unit123_baseline_jsonl", "unit123_baseline_csv"}:
            if not isinstance(binding, dict):
                raise RuntimeError(f"malformed manifest input: {key}")
            live_binding(root, binding, f"manifest input {key}")

    expected_sets = {
        "unit": EXPECTED_UNITS,
        "segment": EXPECTED_SEGMENTS,
        "concept": EXPECTED_CONCEPTS,
        "term": EXPECTED_TERMS,
        "asset": set(),
        "rights": EXPECTED_RIGHTS,
        "artifact": EXPECTED_ARTIFACTS,
        "qa_event": set(QA_TARGETS),
        "correction": EXPECTED_CORRECTIONS,
    }
    for entity_type, expected in expected_sets.items():
        actual = entity_ids(extension, entity_type)
        if actual != expected:
            raise RuntimeError(f"Unit 4 {entity_type} closure changed: missing={sorted(expected-actual)} extra={sorted(actual-expected)}")
    if len(extension) != 222 or extension_counts.get("relation") != 144:
        raise RuntimeError("Unit 4 deterministic record/relation count changed")

    if extension_by_id[UNIT_ID].get("parent_id") != "o011-course-d50":
        raise RuntimeError("Unit 4 parent changed")
    if extension_by_id[LECTURE_ID].get("parent_id") != UNIT_ID or extension_by_id[WORKSHEET_ID].get("parent_id") != UNIT_ID:
        raise RuntimeError("Unit 4 lecture/worksheet parent changed")
    if extension_by_id[f"{LECTURE_ID}-s01"].get("parent_id") != LECTURE_ID:
        raise RuntimeError("Unit 4 segment parent changed")
    for index in range(1, 16):
        if extension_by_id[f"{WORKSHEET_ID}-e{index:03d}"].get("parent_id") != WORKSHEET_ID:
            raise RuntimeError(f"Unit 4 exercise parent changed: {index}")
    for index in SOLUTION_INDICES:
        if extension_by_id[f"{WORKSHEET_ID}-e{index:03d}-solution"].get("parent_id") != f"{WORKSHEET_ID}-e{index:03d}":
            raise RuntimeError(f"Unit 4 solution parent changed: {index}")

    def input_path(key: str) -> Path:
        return root / str(inputs[key]["path"])

    authority = json.loads(input_path("u04_authority").read_text(encoding="utf-8"))
    authority_verify = json.loads(input_path("u04_authority_verify").read_text(encoding="utf-8"))
    current_revision = json.loads(input_path("u04_current_revision").read_text(encoding="utf-8"))
    solution_closure = json.loads(input_path("u04_solution_closure").read_text(encoding="utf-8"))
    media_closure = json.loads(input_path("u04_media_closure").read_text(encoding="utf-8"))
    media_receipt = json.loads(input_path("u04_media_receipt").read_text(encoding="utf-8"))
    media_config = json.loads(input_path("u04_media_config").read_text(encoding="utf-8"))
    if authority.get("status") != "pass" or authority.get("unit") != 4:
        raise RuntimeError("Unit 4 authority preflight failed")
    structure = authority.get("structure") or {}
    if (
        structure.get("lecture_section_count") != 1
        or structure.get("worksheet_exercise_count") != 15
        or structure.get("worksheet_practice_count") != 11
        or structure.get("worksheet_graded_count") != 4
        or structure.get("worksheet_point_total") != 19
        or structure.get("all_hint_fields_blank") is not True
        or tuple(structure.get("worksheet_solution_bearing_indices") or []) != SOLUTION_INDICES
    ):
        raise RuntimeError("Unit 4 authority topology changed")
    if authority_verify.get("preflight") != inputs["u04_authority"] or authority_verify.get("status") != "pass":
        raise RuntimeError("Unit 4 authority verifier is stale")
    if (
        current_revision.get("status") != "pass"
        or not current_revision.get("all_four_frozen_revisions_remain_live_current")
        or current_revision.get("preflight_input", {}).get("sha256") != inputs["u04_authority"]["sha256"]
        or len(current_revision.get("surfaces") or []) != 4
    ):
        raise RuntimeError("Unit 4 current revision evidence changed")
    if authority.get("solutions") != solution_closure:
        raise RuntimeError("Unit 4 authority/solution receipts disagree")
    exercise_rows = solution_closure.get("exercises") or []
    if (
        len(exercise_rows) != 15
        or [row.get("exercise_index") for row in exercise_rows] != list(range(1, 16))
        or [row.get("point_value") for row in exercise_rows if row.get("point_value") is not None] != [4, 5, 4, 6]
        or any(row.get("hint_field") != "" for row in exercise_rows)
        or [row.get("exercise_index") for row in exercise_rows if row.get("exists")] != [7, 10]
    ):
        raise RuntimeError("Unit 4 exercise points/hints/solution markers changed")
    if (
        media_closure.get("status") != "pass"
        or media_closure.get("unique_media_assets") != 0
        or media_closure.get("displayed_media_occurrences") != 0
        or media_closure.get("assets") != []
        or media_receipt.get("source_count") != 0
        or media_receipt.get("derivative_count") != 0
        or media_receipt.get("media") != []
        or media_config.get("units", {}).get("4", {}).get("media") != []
    ):
        raise RuntimeError("Unit 4 zero-media closure changed")

    source_target_specs = {
        "lecture": ("u04_lecture_source", "u04_lecture_target", LECTURE_ID),
        "worksheet": ("u04_worksheet_source", "u04_worksheet_target", WORKSHEET_ID),
        "solution07": ("u04_solution07_source", "u04_solution07_target", f"{WORKSHEET_ID}-e007-solution"),
        "solution10": ("u04_solution10_source", "u04_solution10_target", f"{WORKSHEET_ID}-e010-solution"),
    }
    for name, (source_key, target_key, target_id) in source_target_specs.items():
        source_bytes = input_path(source_key).read_bytes()
        target_bytes = input_path(target_key).read_bytes()
        record = extension_by_id[target_id]
        if record.get("source_sha256") != digest(source_bytes) or record.get("target_sha256") != digest(target_bytes):
            raise RuntimeError(f"stale source/target unit binding: {name}")
        if unit_manifest.get("target_hashes", {}).get(name) != digest(target_bytes):
            raise RuntimeError(f"stale manifest target hash: {name}")
    lecture_source_parts = slices(input_path("u04_lecture_source").read_text(encoding="utf-8"), LECTURE_MARKER)
    lecture_target_parts = slices(input_path("u04_lecture_target").read_text(encoding="utf-8"), LECTURE_MARKER)
    worksheet_source_parts = slices(input_path("u04_worksheet_source").read_text(encoding="utf-8"), EXERCISE_MARKER)
    worksheet_target_parts = slices(input_path("u04_worksheet_target").read_text(encoding="utf-8"), EXERCISE_MARKER)
    if len(lecture_source_parts) != 1 or len(lecture_target_parts) != 1 or len(worksheet_source_parts) != 15 or len(worksheet_target_parts) != 15:
        raise RuntimeError("Unit 4 live TeX marker topology changed")
    segment = extension_by_id[f"{LECTURE_ID}-s01"]
    if segment.get("source_sha256") != digest(lecture_source_parts[0].encode("utf-8")) or segment.get("target_sha256") != digest(lecture_target_parts[0].encode("utf-8")):
        raise RuntimeError("Unit 4 lecture segment slice binding changed")
    for row, source_part, target_part in zip(exercise_rows, worksheet_source_parts, worksheet_target_parts):
        index = int(row["exercise_index"])
        record = extension_by_id[f"{WORKSHEET_ID}-e{index:03d}"]
        expected_point = row.get("point_value")
        if (
            record.get("source_sha256") != digest(source_part.encode("utf-8"))
            or record.get("target_sha256") != digest(target_part.encode("utf-8"))
            or record.get("source_display_id") != f"4.{index}"
            or record.get("point_value") != expected_point
            or record.get("graded") != (expected_point is not None)
            or record.get("hint_present") is not False
            or record.get("has_authority_solution") != bool(row.get("exists"))
        ):
            raise RuntimeError(f"Unit 4 exercise record drifted: {index}")

    terminology_rows = {
        row["id"].lower(): row
        for row in csv.DictReader(input_path("terminology").read_text(encoding="utf-8-sig").splitlines())
    }
    for term_id in EXPECTED_TERMS:
        term = extension_by_id[term_id]
        row = terminology_rows[term_id]
        if row.get("status") != "admitted" or term.get("labels") != {"de": row["source_de"], "id-ID": row["target_id"]} or term.get("terminology_ledger_sha256") != inputs["terminology"]["sha256"]:
            raise RuntimeError(f"Unit 4 terminology record drifted: {term_id}")

    pdf_artifact = extension_by_id["o011-artifact-through-unit04-pdf"]
    pdf_binding = unit_manifest.get("cumulative_pdf") or {}
    live_binding(root, pdf_binding, "Unit 4 cumulative PDF")
    if (
        pdf_artifact.get("path") != pdf_binding.get("path")
        or pdf_artifact.get("bytes") != pdf_binding.get("bytes")
        or pdf_artifact.get("target_sha256") != pdf_binding.get("sha256")
        or pdf_artifact.get("coverage_unit_ids") != ["o011-brenner-u01", "o011-brenner-u02", "o011-brenner-u03", UNIT_ID]
        or pdf_artifact.get("zero_unit04_media") is not True
    ):
        raise RuntimeError("Unit 4 cumulative PDF artifact record changed")
    if pdf_artifact.get("component_rights_ids") != by_id["o011-artifact-through-unit03-pdf"].get("component_rights_ids"):
        raise RuntimeError("zero-media Unit 4 unexpectedly changed cumulative reader rights components")
    for artifact_id, target_id in ARTIFACT_TARGETS.items():
        artifact = extension_by_id[artifact_id]
        live_binding(root, {"path": artifact["path"], "bytes": artifact["bytes"], "sha256": artifact["target_sha256"]}, artifact_id)
        if artifact.get("parent_id") != target_id or artifact.get("rights_component_id") != "o011-rights-brenner-text":
            raise RuntimeError(f"translated artifact ownership/rights changed: {artifact_id}")
    official_artifact = extension_by_id["o011-artifact-u04-official-pdf-witness"]
    official_rights = extension_by_id["o011-rights-u04-official-pdf-witness"]
    live_binding(root, {"path": official_artifact["path"], "bytes": official_artifact["bytes"], "sha256": official_artifact["target_sha256"]}, "official Unit 4 PDF witness")
    if (
        official_artifact.get("release_asset") is not False
        or official_artifact.get("production_master") is not False
        or official_artifact.get("rights_component_id") != official_rights["id"]
        or "withheld" not in str(official_artifact.get("redistribution_status"))
        or official_rights.get("redistribution_permitted") is not False
        or official_rights.get("license_signals") != {
            "commons_structured_metadata": "CC BY-SA 4.0",
            "internal_page_9": "CC BY-SA 3.0",
        }
    ):
        raise RuntimeError("official Unit 4 PDF witness rights disposition changed")

    admitted_results = {
        "o011-qa-unit04-authority-anomalies",
        "o011-qa-unit04-official-pdf-witness",
        "o011-qa-unit04-official-pdf-structural-visual",
    }
    for qa_id, target_id in QA_TARGETS.items():
        qa = extension_by_id[qa_id]
        if qa.get("target_id") != target_id:
            raise RuntimeError(f"Unit 4 QA target changed: {qa_id}")
        expected_result = "admitted_limitation" if qa_id in admitted_results else "pass"
        if qa.get("result") != expected_result:
            raise RuntimeError(f"Unit 4 QA result changed: {qa_id}")
        receipt_path = root / str(qa.get("receipt_path"))
        evidence = receipt_path.read_bytes()
        if qa.get("evidence_sha256") != digest(evidence):
            raise RuntimeError(f"stale Unit 4 QA evidence: {qa_id}")
    final_math = input_path("u04_final_math_audit").read_text(encoding="utf-8")
    if "**Verdict: PASS.**" not in final_math or any(correction.upper() not in final_math for correction in EXPECTED_CORRECTIONS):
        raise RuntimeError("Unit 4 final mathematical audit verdict/closure changed")
    if extension_by_id["o011-qa-unit04-final-math-audit"].get("evidence_sha256") != inputs["u04_final_math_audit"]["sha256"]:
        raise RuntimeError("Unit 4 final mathematical audit QA binding is stale")

    adverse_bytes = input_path("adverse").read_bytes()
    adverse_rows = {
        row["id"].lower(): row
        for row in csv.DictReader(io.StringIO(adverse_bytes.decode("utf-8-sig")))
        if row.get("id", "").lower() in EXPECTED_CORRECTIONS
    }
    if set(adverse_rows) != EXPECTED_CORRECTIONS:
        raise RuntimeError("Unit 4 adverse-ledger closure changed")
    manifest_owner_by_correction = {
        "o011-corr-0038": "u04_worksheet_corrections",
        "o011-corr-0039": "u04_solution07_corrections",
        "o011-corr-0040": "u04_solution10_corrections",
        "o011-corr-0041": "u04_lecture_corrections",
        "o011-corr-0042": "u04_lecture_corrections",
        "o011-corr-0043": "u04_lecture_corrections",
    }
    for correction_id in sorted(EXPECTED_CORRECTIONS):
        record = extension_by_id[correction_id]
        row = adverse_rows[correction_id]
        if (
            record.get("severity") != row["severity"]
            or record.get("description") != row["description"]
            or record.get("disposition") != row["disposition"]
            or record.get("correction_status") != row["status"]
            or record.get("source_local_id") != row["surface"]
            or record.get("ledger_sha256") != digest(adverse_bytes)
        ):
            raise RuntimeError(f"Unit 4 correction ledger binding changed: {correction_id}")
        target_binding = record.get("target_binding") or {}
        reader_binding = record.get("reader_binding") or {}
        live_binding(root, target_binding, f"correction target {correction_id}")
        receipt_bytes = (root / str(target_binding.get("receipt_path"))).read_bytes()
        if target_binding.get("receipt_sha256") != digest(receipt_bytes):
            raise RuntimeError(f"stale correction translation receipt: {correction_id}")
        live_binding(root, reader_binding, f"correction reader {correction_id}")
        for path_field in ("build_receipt_path", "structural_receipt_path", "visual_receipt_path", "math_audit_path"):
            evidence = (root / str(reader_binding.get(path_field))).read_bytes()
            hash_field = path_field.removesuffix("_path") + "_sha256"
            if reader_binding.get(hash_field) != digest(evidence):
                raise RuntimeError(f"stale correction reader evidence: {correction_id}/{path_field}")
        if reader_binding.get("math_audit_path") != "qa/unit-04/POST_REPAIR_MATH_AUDIT.md":
            raise RuntimeError(f"correction does not bind the final math audit: {correction_id}")
        owner_key = manifest_owner_by_correction.get(correction_id)
        deltas = record.get("protected_deltas") or []
        manifest_binding = record.get("correction_manifest")
        if owner_key:
            if manifest_binding != inputs[owner_key] or not deltas:
                raise RuntimeError(f"protected correction evidence changed: {correction_id}")
            live_binding(root, manifest_binding, f"correction manifest {correction_id}")
        elif manifest_binding is not None or deltas:
            raise RuntimeError(f"unprotected C1-to-C2 correction claims a manifest: {correction_id}")
    corr42 = extension_by_id["o011-corr-0042"]
    if not any(
        delta.get("evidence_class") == "evidence_only_delta"
        and delta.get("surface") == "command:mathl"
        and delta.get("occurrence_index") == 6
        for delta in corr42.get("protected_deltas") or []
    ):
        raise RuntimeError("O011-CORR-0042 exact occurrence-6 evidence binding changed")

    expected_relations: dict[str, tuple[str, str, str]] = {}
    def expect(relation_id: str, relation_type: str, from_id: str, to_id: str) -> None:
        if relation_id in expected_relations:
            raise RuntimeError(f"duplicate expected relation: {relation_id}")
        expected_relations[relation_id] = (relation_type, from_id, to_id)

    for concept_id in EXPECTED_CONCEPTS:
        expect(
            f"o011-rel-u04-l04-s01-covers-{concept_id.removeprefix('o011-concept-')}",
            "covers", f"{LECTURE_ID}-s01", concept_id,
        )
    for term_id in EXPECTED_TERMS:
        expect(f"o011-rel-u04-uses-{term_id.removeprefix('o011-')}", "uses_term", UNIT_ID, term_id)
    for index in range(2, 16):
        expect(
            f"o011-rel-u04-w04-e{index - 1:03d}-precedes-e{index:03d}",
            "precedes", f"{WORKSHEET_ID}-e{index - 1:03d}", f"{WORKSHEET_ID}-e{index:03d}",
        )
    for index in SOLUTION_INDICES:
        expect(
            f"o011-rel-u04-w04-e{index:03d}-solution-solves-e{index:03d}",
            "solves", f"{WORKSHEET_ID}-e{index:03d}-solution", f"{WORKSHEET_ID}-e{index:03d}",
        )
    for artifact_id, target_id in ARTIFACT_TARGETS.items():
        expect(
            f"o011-rel-{artifact_id.removeprefix('o011-')}-represents-{target_id.removeprefix('o011-')}",
            "represents", artifact_id, target_id,
        )
    for qa_id, target_id in QA_TARGETS.items():
        expect(
            f"o011-rel-{qa_id.removeprefix('o011-')}-verifies-{target_id.removeprefix('o011-')}",
            "verifies", qa_id, target_id,
        )
    expect("o011-rel-artifact-through-unit04-pdf-represents-u04-checkpoint", "represents", "o011-artifact-through-unit04-pdf", UNIT_ID)
    expect("o011-rel-artifact-through-unit04-pdf-extends-through-unit03-pdf", "extends", "o011-artifact-through-unit04-pdf", "o011-artifact-through-unit03-pdf")
    expect("o011-rel-artifact-u04-official-pdf-witness-witnesses-brenner-u04-l04", "witnesses", "o011-artifact-u04-official-pdf-witness", LECTURE_ID)
    expect("o011-rel-rights-u04-official-pdf-witness-governs-artifact-u04-official-pdf-witness", "governs", "o011-rights-u04-official-pdf-witness", "o011-artifact-u04-official-pdf-witness")
    expect("o011-rel-u03-precedes-u04", "precedes", "o011-brenner-u03", UNIT_ID)
    for correction_id, target_id in CORRECTION_TARGETS.items():
        expect(
            f"o011-rel-{correction_id.removeprefix('o011-')}-corrects-{target_id.removeprefix('o011-')}",
            "corrects", correction_id, target_id,
        )
    for child in extension:
        parent_id = child.get("parent_id")
        if parent_id and child.get("entity_type") not in {"relation", "rights", "correction"}:
            child_id = str(child["id"])
            expect(f"o011-rel-contains-{child_id.removeprefix('o011-')}", "contains", str(parent_id), child_id)
    actual_relation_ids = entity_ids(extension, "relation")
    if actual_relation_ids != set(expected_relations):
        raise RuntimeError(
            "Unit 4 relation closure changed: "
            f"missing={sorted(set(expected_relations)-actual_relation_ids)} "
            f"extra={sorted(actual_relation_ids-set(expected_relations))}"
        )
    for relation_id, expected in expected_relations.items():
        relation = extension_by_id[relation_id]
        actual = (relation.get("relation_type"), relation.get("from_id"), relation.get("to_id"))
        if actual != expected:
            raise RuntimeError(f"Unit 4 relation endpoint/type drift: {relation_id}")

    for label, value in (("records", records), ("manifest", manifest)):
        for key, string in walk_strings(value):
            folded = string.casefold()
            if (key == "path" or key.endswith("_path")) and (string.startswith(("/", "\\")) or WINDOWS_ABSOLUTE.search(string)):
                raise RuntimeError(f"absolute path in {label}:{key}")
            if any(marker in folded for marker in PRIVATE_MARKERS):
                raise RuntimeError(f"private/credential marker in {label}:{key}")
    for record in extension:
        source_display_id = record.get("source_display_id")
        if source_display_id and not re.fullmatch(r"4\.\d+", str(source_display_id)):
            raise RuntimeError(f"wrapper numbering leaked into Unit 4 source display ID: {record['id']}")

    receipt = {
        "schema_version": 1,
        "workflow": "o011-unit04-backend-qa-v1",
        "checkpoint_utc": args.checkpoint,
        "status": "pass",
        "validator": file_info(Path(__file__), root),
        "schema": {**file_info(schema_path, root), "draft": "2020-12", "rows_validated": len(records)},
        "outputs": {
            "records_jsonl": file_info(jsonl_path, root),
            "records_csv": file_info(csv_path, root),
            "manifest": file_info(manifest_path, root),
        },
        "deterministic_repeat": {
            "fixed_checkpoint": args.checkpoint, "runs_compared": 2,
            "jsonl_byte_identical": True, "csv_byte_identical": True,
            "manifest_byte_identical": True,
        },
        "unit123_preservation": {
            "record_count": len(baseline_records),
            "jsonl_bytes": len(baseline_jsonl), "jsonl_sha256": digest(baseline_jsonl),
            "csv_bytes": len(baseline_csv), "csv_sha256": digest(baseline_csv),
            "byte_identical_prefixes": True,
        },
        "unit04": {
            "record_count": len(extension), "entity_counts": extension_counts,
            "lecture_segment_count": 1, "worksheet_exercise_count": 15,
            "practice_exercise_count": 11, "graded_exercise_count": 4,
            "graded_point_values": [4, 5, 4, 6], "graded_point_total": 19,
            "all_hint_fields_blank": True,
            "supplied_solution_indices": list(SOLUTION_INDICES),
            "concept_count": len(EXPECTED_CONCEPTS), "term_count": len(EXPECTED_TERMS),
            "asset_count": 0, "zero_media": True,
            "rights_count": len(EXPECTED_RIGHTS),
            "correction_ids": sorted(EXPECTED_CORRECTIONS),
            "artifact_count": len(EXPECTED_ARTIFACTS),
            "qa_event_count": len(QA_TARGETS),
            "relation_count": len(expected_relations),
            "html_included": False,
            "authority_preflight": inputs["u04_authority"],
            "authority_verification": inputs["u04_authority_verify"],
            "final_math_audit": inputs["u04_final_math_audit"],
            "cumulative_pdf": pdf_binding,
            "official_pdf_witness": unit_manifest["official_pdf_witness"],
        },
        "checks": {
            "schema_valid": True,
            "unique_ids": True,
            "references_resolved": True,
            "unit123_jsonl_prefix_byte_identical": True,
            "unit123_csv_prefix_byte_identical": True,
            "csv_ids_and_row_count_match_jsonl": True,
            "manifest_counts_hashes_and_live_inputs_current": True,
            "authority_root_and_latex_revisions_current": True,
            "exercise_points_hints_and_solution_markers_exact": True,
            "exactly_solutions_7_and_10": True,
            "zero_media_authority_build_and_rights_closure": True,
            "artifacts_current": True,
            "qa_receipts_current": True,
            "final_math_audit_current": True,
            "correction_ledger_manifests_targets_and_reader_evidence_current": True,
            "corr0042_occurrence6_binding_current": True,
            "official_pdf_nonrelease_rights_disposition_preserved": True,
            "relations_exact": True,
            "source_numbering_preserved": True,
            "absolute_paths_absent": True,
            "private_and_credential_markers_absent": True,
        },
    }
    output_path = root / "qa/unit-04/backend_qa.json"
    receipt_bytes = (json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    assert_public_safe_bytes("qa/unit-04/backend_qa.json", receipt_bytes)
    output_path.write_bytes(receipt_bytes)


if __name__ == "__main__":
    main()
