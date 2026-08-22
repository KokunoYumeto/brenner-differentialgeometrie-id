#!/usr/bin/env python3
"""Verify the deterministic Unit 3 extension of the O011 modular backend.

Run this only after two exports made with the same explicit checkpoint.  The
three ``--first-*`` hashes must be captured from the first export; this second
pass proves byte-for-byte repeatability while also validating the schema,
immutable Unit 1-2 prefixes, live artifacts and receipts, Unit 3 closure, and
public-data safety.  A successful run writes ``qa/unit-03/backend_qa.json``.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
from pathlib import Path
from typing import Any, Iterable

from jsonschema import Draft202012Validator, FormatChecker


BASELINE_RECORD_COUNT = 357
BASELINE_JSONL_BYTES = 215_317
BASELINE_JSONL_SHA256 = "a393d3ff6c8aed203e7d3690eb6391e22ea25436cd06e85aa40e1adc23adb122"
BASELINE_CSV_BYTES = 79_611
BASELINE_CSV_SHA256 = "5880fa9dee8bc0a73ed0e903d931fad38978bc2c9ef65cc58b62b48a7f26b7ba"
WORKFLOW = "o011-export-backend-v3"
SOLUTION_INDICES = (7, 16)
EXPECTED_CORRECTION_IDS = {
    f"o011-corr-{index:04d}" for index in range(28, 38)
}
EXPECTED_CONCEPT_IDS = {
    "o011-concept-arc-length-parametrization",
    "o011-concept-planar-signed-curvature",
    "o011-concept-curvature-circle",
    "o011-concept-evolute",
    "o011-concept-general-curve-curvature",
}
EXPECTED_ASSET_IDS = {
    "o011-asset-file-parabola-circle-svg",
    "o011-asset-file-euler-spiral-svg",
    "o011-asset-file-evolute-parab-svg",
}
EXPECTED_RIGHTS_IDS = {
    "o011-rights-media-u03-01",
    "o011-rights-media-u03-02",
    "o011-rights-media-u03-03",
}
EXPECTED_FRAGMENT_ARTIFACT_IDS = {
    "o011-artifact-u03-l03-tex",
    "o011-artifact-u03-w03-tex",
    "o011-artifact-u03-w03-e007-solution-tex",
    "o011-artifact-u03-w03-e016-solution-tex",
}
EXPECTED_BASE_QA_IDS = {
    "o011-qa-unit03-authority-preflight",
    "o011-qa-unit03-authority-verification",
    "o011-qa-unit03-media-closure",
    "o011-qa-through-unit03-pdf-reproducibility",
    "o011-qa-through-unit03-pdf-structural",
    "o011-qa-through-unit03-pdf-visual",
    "o011-qa-unit03-final-math-audit",
    "o011-qa-unit03-lecture-translation",
    "o011-qa-unit03-worksheet-translation",
    "o011-qa-unit03-solution07-translation",
    "o011-qa-unit03-solution16-translation",
}
ENTITY_TYPES = {
    "program",
    "course",
    "resource",
    "edition",
    "unit",
    "concept",
    "segment",
    "term",
    "asset",
    "relation",
    "rights",
    "qa_event",
    "artifact",
    "correction",
}
COMMON = (
    "schema",
    "schema_version",
    "id",
    "entity_type",
    "source_local_id",
    "parent_id",
    "order",
    "path",
    "resource_id",
    "edition_id",
    "source_locator",
    "source_sha256",
    "target_sha256",
    "language",
    "locale",
    "translation_state",
    "rights_component_id",
    "status",
    "timestamp",
    "workflow",
    "supersedes",
)
WINDOWS_ABSOLUTE = re.compile(r"(?i)(?<![a-z0-9+.-])[a-z]:[\\/]")
LECTURE_MARKER = re.compile(r"(?m)^\s*\\zwischenueberschrift\s*\{")
EXERCISE_MARKER = re.compile(
    r"(?m)^\s*\\(?:inputaufgabegibtloesung|inputaufgabe)\b"
)
PRIVATE_MARKERS = (
    "\\users\\",
    "/users/",
    "\\appdata\\",
    "/home/",
    "github_pat_",
    "ghp_",
    "gho_",
    "ghu_",
    "ghs_",
    "ghr_",
    "glpat-",
    "sk-proj-",
    "xoxb-",
    "bearer ",
    "access_token",
    "api_key",
    "zenodo token",
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def slices(text: str, marker: re.Pattern[str]) -> list[str]:
    matches = list(marker.finditer(text))
    return [
        text[
            match.start() : (
                matches[index + 1].start() if index + 1 < len(matches) else len(text)
            )
        ]
        for index, match in enumerate(matches)
    ]


def repository_path(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def file_info(path: Path, root: Path) -> dict[str, object]:
    data = path.read_bytes()
    return {
        "path": repository_path(path, root),
        "bytes": len(data),
        "sha256": digest(data),
    }


def walk_strings(value: object, key: str = "") -> Iterable[tuple[str, str]]:
    if isinstance(value, dict):
        for child_key, child in value.items():
            yield from walk_strings(child, str(child_key))
    elif isinstance(value, list):
        for child in value:
            yield from walk_strings(child, key)
    elif isinstance(value, str):
        yield key, value


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
        raise RuntimeError(f"private path or credential marker leaked into {label}: {found}")


def extract_line_prefix(data: bytes, line_count: int, label: str) -> bytes:
    lines = data.splitlines(keepends=True)
    if len(lines) < line_count:
        raise RuntimeError(f"{label} has fewer than {line_count} physical lines")
    prefix = b"".join(lines[:line_count])
    if not prefix.endswith(b"\n"):
        raise RuntimeError(f"{label} baseline prefix is not LF-terminated")
    return prefix


def require_hash(value: str, label: str) -> str:
    lowered = value.lower()
    if not re.fullmatch(r"[0-9a-f]{64}", lowered):
        raise RuntimeError(f"{label} must be a SHA-256 hex digest")
    return lowered


def record_map(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    mapped = {str(record["id"]): record for record in records}
    if len(mapped) != len(records):
        raise RuntimeError("duplicate stable IDs")
    return mapped


def entity_ids(records: list[dict[str, Any]], entity_type: str) -> set[str]:
    return {
        str(record["id"])
        for record in records
        if record.get("entity_type") == entity_type
    }


def validate_references(records: list[dict[str, Any]]) -> None:
    identifiers = {str(record["id"]) for record in records}
    for record in records:
        for field in (
            "parent_id",
            "resource_id",
            "edition_id",
            "rights_component_id",
            "target_id",
            "artifact_id",
        ):
            value = record.get(field)
            if value is not None and value not in identifiers:
                raise RuntimeError(f"unresolved {field}={value!r} in {record['id']}")
        for value in record.get("component_rights_ids") or []:
            if value not in identifiers:
                raise RuntimeError(
                    f"unresolved component right {value!r} in {record['id']}"
                )
        if record.get("entity_type") == "relation":
            for field in ("from_id", "to_id"):
                if record.get(field) not in identifiers:
                    raise RuntimeError(f"unresolved {field} in {record['id']}")


def live_binding(root: Path, binding: dict[str, Any], label: str) -> None:
    relative = binding.get("path")
    if not isinstance(relative, str) or not relative:
        raise RuntimeError(f"{label} lacks a repository-relative path")
    path = (root / relative).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise RuntimeError(f"{label} escapes the project root") from exc
    data = path.read_bytes()
    if binding.get("bytes") != len(data) or binding.get("sha256") != digest(data):
        raise RuntimeError(f"stale live binding: {label}")


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
    exporter_path = root / "scripts/export_backend_v3.py"
    jsonl_bytes = jsonl_path.read_bytes()
    csv_bytes = csv_path.read_bytes()
    manifest_bytes = manifest_path.read_bytes()
    for label, data in (
        ("records.jsonl", jsonl_bytes),
        ("records.csv", csv_bytes),
        ("MANIFEST.json", manifest_bytes),
    ):
        assert_public_safe_bytes(label, data)
    if digest(jsonl_bytes) != require_hash(args.first_jsonl_sha256, "first JSONL hash"):
        raise RuntimeError("JSONL differs from the first fixed-checkpoint export")
    if digest(csv_bytes) != require_hash(args.first_csv_sha256, "first CSV hash"):
        raise RuntimeError("CSV differs from the first fixed-checkpoint export")
    if digest(manifest_bytes) != require_hash(
        args.first_manifest_sha256, "first manifest hash"
    ):
        raise RuntimeError("manifest differs from the first fixed-checkpoint export")

    baseline_jsonl = extract_line_prefix(
        jsonl_bytes, BASELINE_RECORD_COUNT, "records.jsonl"
    )
    baseline_csv = extract_line_prefix(
        csv_bytes, BASELINE_RECORD_COUNT + 1, "records.csv"
    )
    if (
        len(baseline_jsonl) != BASELINE_JSONL_BYTES
        or digest(baseline_jsonl) != BASELINE_JSONL_SHA256
    ):
        raise RuntimeError("immutable 357-record JSONL prefix changed")
    if len(baseline_csv) != BASELINE_CSV_BYTES or digest(baseline_csv) != BASELINE_CSV_SHA256:
        raise RuntimeError("immutable 357-row CSV prefix changed")

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    records: list[dict[str, Any]] = []
    jsonl_lines = jsonl_bytes.splitlines(keepends=True)
    for line_number, line in enumerate(jsonl_lines, 1):
        if not line.endswith(b"\n"):
            raise RuntimeError(f"JSONL line {line_number} is not LF-terminated")
        record = json.loads(line.decode("utf-8"))
        errors = sorted(validator.iter_errors(record), key=lambda error: list(error.path))
        if errors:
            raise RuntimeError(
                f"schema failure at row {line_number}, {record.get('id')}: "
                f"{errors[0].message}"
            )
        if line_number > BASELINE_RECORD_COUNT:
            expected_line = (canonical_json(record) + "\n").encode("utf-8")
            if line != expected_line:
                raise RuntimeError(f"non-canonical Unit 3 JSONL row {line_number}")
        records.append(record)
    if len(records) <= BASELINE_RECORD_COUNT:
        raise RuntimeError("Unit 3 extension is absent")
    by_id = record_map(records)
    validate_references(records)
    baseline_records = records[:BASELINE_RECORD_COUNT]
    extension = records[BASELINE_RECORD_COUNT:]
    extension_by_id = record_map(extension)
    extension_ids = list(extension_by_id)
    if extension_ids != sorted(extension_ids):
        raise RuntimeError("Unit 3 JSONL suffix is not deterministically ID-sorted")
    if any(
        record.get("workflow") != WORKFLOW or record.get("timestamp") != args.checkpoint
        for record in extension
    ):
        raise RuntimeError("Unit 3 workflow/checkpoint binding changed")

    csv_reader = csv.DictReader(io.StringIO(csv_bytes.decode("utf-8")))
    csv_rows = list(csv_reader)
    if tuple(csv_reader.fieldnames or ()) != COMMON:
        raise RuntimeError("CSV header differs from the canonical common-field projection")
    if len(csv_rows) != len(records):
        raise RuntimeError("CSV row count differs from JSONL")
    if [row.get("id") for row in csv_rows] != [record["id"] for record in records]:
        raise RuntimeError("CSV stable-ID ordering differs from JSONL")
    for offset, (row, record) in enumerate(
        zip(csv_rows[BASELINE_RECORD_COUNT:], extension), BASELINE_RECORD_COUNT + 2
    ):
        expected_row = {
            field: "" if record.get(field) is None else str(record.get(field))
            for field in COMMON
        }
        if row != expected_row:
            raise RuntimeError(f"CSV/JSONL common-field mismatch at CSV row {offset}")

    manifest = json.loads(manifest_bytes.decode("utf-8"))
    if manifest.get("schema_version") != 3:
        raise RuntimeError("manifest schema version is not 3")
    if manifest.get("generator") != "scripts/export_backend_v3.py":
        raise RuntimeError("manifest generator path changed")
    if manifest.get("generator_sha256") != digest(exporter_path.read_bytes()):
        raise RuntimeError("manifest generator hash is stale")
    if manifest.get("timestamp") != args.checkpoint:
        raise RuntimeError("manifest checkpoint differs from the requested checkpoint")
    if manifest.get("record_count") != len(records):
        raise RuntimeError("manifest record count mismatch")
    entity_counts = {
        kind: sum(record.get("entity_type") == kind for record in records)
        for kind in sorted(ENTITY_TYPES)
    }
    extension_counts = {
        kind: sum(record.get("entity_type") == kind for record in extension)
        for kind in sorted(ENTITY_TYPES)
    }
    if manifest.get("entity_counts") != entity_counts:
        raise RuntimeError("manifest cumulative entity counts mismatch")
    unit3_manifest = manifest.get("unit03_extension", {})
    if (
        unit3_manifest.get("record_count") != len(extension)
        or unit3_manifest.get("entity_counts") != extension_counts
    ):
        raise RuntimeError("manifest Unit 3 entity counts mismatch")
    preservation = manifest.get("unit12_baseline_preservation", {})
    if preservation != {
        "path": "backend/records.jsonl",
        "record_count": BASELINE_RECORD_COUNT,
        "bytes": BASELINE_JSONL_BYTES,
        "sha256": BASELINE_JSONL_SHA256,
        "byte_identical_prefix": True,
        "csv_path": "backend/records.csv",
        "csv_bytes": BASELINE_CSV_BYTES,
        "csv_sha256": BASELINE_CSV_SHA256,
        "csv_byte_identical_prefix": True,
    }:
        raise RuntimeError("manifest Unit 1-2 preservation claim is incomplete")
    outputs = manifest.get("outputs", {})
    if outputs.get("records.jsonl") != {
        "bytes": len(jsonl_bytes),
        "sha256": digest(jsonl_bytes),
    } or outputs.get("records.csv") != {
        "bytes": len(csv_bytes),
        "sha256": digest(csv_bytes),
    }:
        raise RuntimeError("manifest output hashes are stale")
    inputs = manifest.get("inputs", {})
    for special_key, expected in (
        (
            "unit12_baseline_jsonl",
            {
                "path": "backend/records.jsonl",
                "bytes": BASELINE_JSONL_BYTES,
                "sha256": BASELINE_JSONL_SHA256,
            },
        ),
        (
            "unit12_baseline_csv",
            {
                "path": "backend/records.csv",
                "bytes": BASELINE_CSV_BYTES,
                "sha256": BASELINE_CSV_SHA256,
            },
        ),
    ):
        if inputs.get(special_key) != expected:
            raise RuntimeError(f"manifest {special_key} binding changed")
    for key, binding in inputs.items():
        if key not in {"unit12_baseline_jsonl", "unit12_baseline_csv"}:
            if not isinstance(binding, dict):
                raise RuntimeError(f"malformed manifest input: {key}")
            live_binding(root, binding, f"manifest input {key}")

    unit_id = "o011-brenner-u03"
    lecture_id = "o011-brenner-u03-l03"
    worksheet_id = "o011-brenner-u03-w03"
    expected_exercises = {
        f"{worksheet_id}-e{index:03d}" for index in range(1, 22)
    }
    expected_solutions = {
        f"{worksheet_id}-e{index:03d}-solution" for index in SOLUTION_INDICES
    }
    expected_units = {
        unit_id,
        lecture_id,
        worksheet_id,
        *expected_exercises,
        *expected_solutions,
    }
    expected_segments = {f"{lecture_id}-s{index:02d}" for index in range(1, 3)}
    if entity_ids(extension, "unit") != expected_units:
        raise RuntimeError("Unit 3 lecture/worksheet/exercise/solution closure changed")
    if entity_ids(extension, "segment") != expected_segments:
        raise RuntimeError("Unit 3 two-segment lecture closure changed")
    if entity_ids(extension, "concept") != EXPECTED_CONCEPT_IDS:
        raise RuntimeError("Unit 3 concept closure changed")
    term_ids = set(unit3_manifest.get("term_ids") or [])
    if len(term_ids) != 20 or entity_ids(extension, "term") != term_ids:
        raise RuntimeError("Unit 3 twenty-term closure changed")
    if entity_ids(extension, "asset") != EXPECTED_ASSET_IDS:
        raise RuntimeError("Unit 3 three-asset closure changed")
    if entity_ids(extension, "rights") != EXPECTED_RIGHTS_IDS:
        raise RuntimeError("Unit 3 per-file rights closure changed")
    if entity_ids(extension, "correction") != EXPECTED_CORRECTION_IDS:
        raise RuntimeError("Unit 3 correction-record closure changed")
    if extension_by_id[unit_id].get("parent_id") != "o011-course-d50":
        raise RuntimeError("Unit 3 parent changed")
    if extension_by_id[lecture_id].get("parent_id") != unit_id:
        raise RuntimeError("Unit 3 lecture parent changed")
    if extension_by_id[worksheet_id].get("parent_id") != unit_id:
        raise RuntimeError("Unit 3 worksheet parent changed")
    for segment_id in expected_segments:
        if extension_by_id[segment_id].get("parent_id") != lecture_id:
            raise RuntimeError(f"Unit 3 segment parent changed: {segment_id}")
    for exercise_id in expected_exercises:
        if extension_by_id[exercise_id].get("parent_id") != worksheet_id:
            raise RuntimeError(f"Unit 3 exercise parent changed: {exercise_id}")
    for index in SOLUTION_INDICES:
        solution_id = f"{worksheet_id}-e{index:03d}-solution"
        if extension_by_id[solution_id].get("parent_id") != f"{worksheet_id}-e{index:03d}":
            raise RuntimeError(f"Unit 3 solution parent changed: {solution_id}")

    lecture_source_path = root / "authority/expanded/lecture03_source.de.tex"
    lecture_target_path = root / "source/units/unit-03/lecture03.id.tex"
    worksheet_source_path = root / "authority/expanded/worksheet03_source.de.tex"
    worksheet_target_path = root / "source/units/unit-03/worksheet03.id.tex"
    lecture_source_bytes = lecture_source_path.read_bytes()
    lecture_target_bytes = lecture_target_path.read_bytes()
    worksheet_source_bytes = worksheet_source_path.read_bytes()
    worksheet_target_bytes = worksheet_target_path.read_bytes()
    lecture_record = extension_by_id[lecture_id]
    worksheet_record = extension_by_id[worksheet_id]
    if (
        lecture_record.get("source_sha256") != digest(lecture_source_bytes)
        or lecture_record.get("target_sha256") != digest(lecture_target_bytes)
        or worksheet_record.get("source_sha256") != digest(worksheet_source_bytes)
        or worksheet_record.get("target_sha256") != digest(worksheet_target_bytes)
    ):
        raise RuntimeError("Unit 3 lecture/worksheet whole-file hash binding is stale")
    lecture_source_parts = slices(lecture_source_bytes.decode("utf-8"), LECTURE_MARKER)
    lecture_target_parts = slices(lecture_target_bytes.decode("utf-8"), LECTURE_MARKER)
    worksheet_source_parts = slices(worksheet_source_bytes.decode("utf-8"), EXERCISE_MARKER)
    worksheet_target_parts = slices(worksheet_target_bytes.decode("utf-8"), EXERCISE_MARKER)
    if len(lecture_source_parts) != 2 or len(lecture_target_parts) != 2:
        raise RuntimeError("live Unit 3 lecture no longer has exactly two segments")
    if len(worksheet_source_parts) != 21 or len(worksheet_target_parts) != 21:
        raise RuntimeError("live Unit 3 worksheet no longer has exactly 21 exercises")
    for index, (source_part, target_part) in enumerate(
        zip(lecture_source_parts, lecture_target_parts), 1
    ):
        segment = extension_by_id[f"{lecture_id}-s{index:02d}"]
        if (
            segment.get("source_sha256") != digest(source_part.encode("utf-8"))
            or segment.get("target_sha256") != digest(target_part.encode("utf-8"))
        ):
            raise RuntimeError(f"stale Unit 3 lecture segment binding: {index}")

    solution_closure = json.loads(
        (root / "qa/unit-03/solution_closure.json").read_text(encoding="utf-8")
    )
    closure_rows = solution_closure.get("exercises") or []
    if (
        solution_closure.get("exercise_count") != 21
        or len(closure_rows) != 21
        or tuple(solution_closure.get("supplied_solution_indices") or [])
        != SOLUTION_INDICES
    ):
        raise RuntimeError("live Unit 3 worksheet/solution census changed")

    for index in range(1, 22):
        exercise = extension_by_id[f"{worksheet_id}-e{index:03d}"]
        closure_row = closure_rows[index - 1]
        if closure_row.get("exercise_index") != index:
            raise RuntimeError(f"solution census ordering drift at Unit 3 exercise {index}")
        if exercise.get("source_display_id") != f"3.{index}":
            raise RuntimeError(f"source display ID drift at Unit 3 exercise {index}")
        if bool(exercise.get("has_authority_solution")) != (index in SOLUTION_INDICES):
            raise RuntimeError(f"solution marker drift at Unit 3 exercise {index}")
        if (
            exercise.get("source_sha256")
            != digest(worksheet_source_parts[index - 1].encode("utf-8"))
            or exercise.get("target_sha256")
            != digest(worksheet_target_parts[index - 1].encode("utf-8"))
        ):
            raise RuntimeError(f"stale Unit 3 exercise slice binding: {index}")
        if exercise.get("graded") is not bool(closure_row.get("root_point_marker")):
            raise RuntimeError(f"graded marker drift at Unit 3 exercise {index}")
        if exercise.get("hint_present") is not bool(closure_row.get("hint_field")):
            raise RuntimeError(f"hint marker drift at Unit 3 exercise {index}")
        if exercise.get("point_value") != closure_row.get("point_value"):
            raise RuntimeError(f"point value drift at Unit 3 exercise {index}")
        point_value = exercise.get("point_value")
        if point_value is not None and (
            not isinstance(point_value, int) or isinstance(point_value, bool) or point_value < 0
        ):
            raise RuntimeError(f"point value is invalid at Unit 3 exercise {index}")
    for index in SOLUTION_INDICES:
        solution = extension_by_id[f"{worksheet_id}-e{index:03d}-solution"]
        if solution.get("source_display_id") != f"3.{index}":
            raise RuntimeError(f"source display ID drift at Unit 3 solution {index}")
        solution_source = (
            root
            / f"authority/expanded/worksheet03_exercise{index:02d}_solution_source.de.tex"
        ).read_bytes()
        solution_target = (
            root
            / f"source/units/unit-03/worksheet03_exercise{index:02d}_solution.id.tex"
        ).read_bytes()
        if (
            solution.get("source_sha256") != digest(solution_source)
            or solution.get("target_sha256") != digest(solution_target)
        ):
            raise RuntimeError(f"stale Unit 3 supplied-solution binding: {index}")

    proposed_terms_path = root / "qa/unit-03/WORKSHEET_TERMS_PROPOSED.csv"
    terminology_path = root / "00_control/TERMINOLOGY.csv"
    terminology_rows = list(
        csv.DictReader(io.StringIO(terminology_path.read_text(encoding="utf-8-sig")))
    )
    admitted_terms = {
        row["id"].lower(): row for row in terminology_rows if row.get("status") == "admitted"
    }
    for term_id in term_ids:
        term = extension_by_id[term_id]
        ledger_row = admitted_terms.get(term_id)
        if not ledger_row or term.get("source_local_id") != ledger_row.get("source_de"):
            raise RuntimeError(f"term is not current against TERMINOLOGY.csv: {term_id}")
        if (term.get("labels") or {}).get("id-ID") != ledger_row.get("target_id"):
            raise RuntimeError(f"term target drift against TERMINOLOGY.csv: {term_id}")
    if not proposed_terms_path.is_file():
        raise RuntimeError("Unit 3 terminology proposal witness is missing")

    asset_owner = {
        "o011-asset-file-parabola-circle-svg": lecture_id,
        "o011-asset-file-euler-spiral-svg": worksheet_id,
        "o011-asset-file-evolute-parab-svg": worksheet_id,
    }
    asset_rights = {
        "o011-asset-file-parabola-circle-svg": "o011-rights-media-u03-01",
        "o011-asset-file-euler-spiral-svg": "o011-rights-media-u03-02",
        "o011-asset-file-evolute-parab-svg": "o011-rights-media-u03-03",
    }
    media_rights_path = root / "authority/brenner_media_rights_manifest.csv"
    media_rights_rows = list(
        csv.DictReader(io.StringIO(media_rights_path.read_text(encoding="utf-8-sig")))
    )
    media_rights_by_filename = {
        row["title"].removeprefix("File:"): row for row in media_rights_rows
    }
    authority_preflight = json.loads(
        (root / "qa/unit-03/AUTHORITY_PREFLIGHT.json").read_text(encoding="utf-8")
    )
    authority_media_by_filename = {
        item["filename"]: item
        for item in authority_preflight.get("media", {}).get("assets", [])
    }
    for asset_id in sorted(EXPECTED_ASSET_IDS):
        asset = extension_by_id[asset_id]
        filename = str(asset.get("source_local_id", "")).removeprefix("File:")
        rights_row = media_rights_by_filename.get(filename)
        authority_item = authority_media_by_filename.get(filename)
        if rights_row is None or authority_item is None:
            raise RuntimeError(f"missing live rights/authority row for {asset_id}")
        if asset.get("rights_component_id") != asset_rights[asset_id]:
            raise RuntimeError(f"wrong per-file rights component for {asset_id}")
        asset_path = (root / str(asset.get("path"))).resolve()
        asset_path.relative_to(root)
        asset_bytes = asset_path.read_bytes()
        if (
            asset.get("path") != f"authority/media/{filename}"
            or len(asset_bytes) != asset.get("expected_bytes")
            or digest(asset_bytes) != asset.get("source_sha256")
            or asset.get("binary_present") is not True
            or asset.get("source_locator") != rights_row.get("description_url")
            or asset.get("mime") != rights_row.get("mime")
            or asset.get("expected_bytes") != int(rights_row["bytes"])
            or asset.get("commons_sha1") != rights_row.get("commons_sha1_hex")
            or authority_item.get("bytes") != len(asset_bytes)
            or authority_item.get("sha256") != digest(asset_bytes)
            or authority_item.get("commons_sha1") != rights_row.get("commons_sha1_hex")
        ):
            raise RuntimeError(f"stale Unit 3 media asset binding: {asset_id}")
        rights = extension_by_id[str(asset.get("rights_component_id"))]
        if (
            rights.get("status") != "active"
            or rights.get("license") != rights_row.get("license")
            or rights.get("license_url") != (rights_row.get("license_url") or None)
            or rights.get("attribution") != rights_row.get("artist_html")
            or rights.get("credit") != rights_row.get("credit_html")
            or rights.get("component_scope") != asset.get("source_local_id")
            or rights.get("attribution_required")
            is not (rights_row.get("attribution_required", "").lower() == "true")
            or rights.get("copyrighted") != rights_row.get("copyrighted")
            or rights.get("commons_lastrevid") != authority_item.get("commons_lastrevid")
            or rights.get("commons_image_timestamp") != authority_item.get("image_timestamp")
        ):
            raise RuntimeError(f"incomplete per-file rights record for {asset_id}")
    media_receipt_path = root / "qa/unit-03_media.json"
    media_receipt = json.loads(media_receipt_path.read_text(encoding="utf-8"))
    media_status = str(media_receipt.get("status", "pass")).casefold()
    if (
        media_status != "pass"
        or media_receipt.get("failures")
        or media_receipt.get("blockers")
        or media_receipt.get("source_count") != 3
        or media_receipt.get("derivative_count") != 3
    ):
        raise RuntimeError("live Unit 3 media receipt is not a clean closure")
    media_receipt_by_filename = {
        item["filename"]: item for item in media_receipt.get("media", [])
    }
    unit3_filenames = {
        str(extension_by_id[asset_id]["source_local_id"]).removeprefix("File:")
        for asset_id in EXPECTED_ASSET_IDS
    }
    if set(media_receipt_by_filename) != unit3_filenames:
        raise RuntimeError("Unit 3 media receipt filename closure changed")
    derivative_bindings = unit3_manifest.get("media_derivatives") or []
    if len(derivative_bindings) != 3 or {
        binding.get("filename") for binding in derivative_bindings
    } != unit3_filenames:
        raise RuntimeError("manifest Unit 3 derivative closure changed")
    for binding in derivative_bindings:
        filename = str(binding["filename"])
        derivative = media_receipt_by_filename[filename].get("derivative")
        if not isinstance(derivative, dict):
            raise RuntimeError(f"media derivative receipt is absent: {filename}")
        derivative_path = (root / str(derivative.get("path", ""))).resolve()
        expected_binding = {
            "filename": filename,
            "path": repository_path(derivative_path, root),
            "bytes": derivative.get("bytes"),
            "sha256": derivative.get("sha256"),
        }
        if binding != expected_binding:
            raise RuntimeError(f"manifest/media-receipt derivative drift: {filename}")
        live_binding(root, binding, f"Unit 3 media derivative {filename}")

    html_info = unit3_manifest.get("cumulative_html", {})
    html_included = html_info.get("included") is True
    canonical_html = root / "output/html/geometri-diferensial-manifold-mulus-hingga-unit-03-id.html"
    if canonical_html.is_file() != html_included:
        raise RuntimeError("canonical cumulative HTML presence differs from manifest inclusion")
    fragment_targets = {
        "o011-artifact-u03-l03-tex": lecture_id,
        "o011-artifact-u03-w03-tex": worksheet_id,
        "o011-artifact-u03-w03-e007-solution-tex": f"{worksheet_id}-e007-solution",
        "o011-artifact-u03-w03-e016-solution-tex": f"{worksheet_id}-e016-solution",
    }
    expected_artifacts = {
        *EXPECTED_FRAGMENT_ARTIFACT_IDS,
        "o011-artifact-through-unit03-pdf",
    }
    expected_qa = set(EXPECTED_BASE_QA_IDS)
    if html_included:
        expected_artifacts.add("o011-artifact-through-unit03-html")
        expected_qa.add("o011-qa-through-unit03-html-structural")
    if entity_ids(extension, "artifact") != expected_artifacts:
        raise RuntimeError("Unit 3 artifact closure changed")
    if entity_ids(extension, "qa_event") != expected_qa:
        raise RuntimeError("Unit 3 QA-event closure changed")
    if set(unit3_manifest.get("artifact_ids") or []) != expected_artifacts:
        raise RuntimeError("manifest Unit 3 artifact IDs changed")
    if set(unit3_manifest.get("qa_event_ids") or []) != expected_qa:
        raise RuntimeError("manifest Unit 3 QA-event IDs changed")
    if set(unit3_manifest.get("asset_ids") or []) != EXPECTED_ASSET_IDS:
        raise RuntimeError("manifest Unit 3 asset IDs changed")
    if set(unit3_manifest.get("rights_ids") or []) != EXPECTED_RIGHTS_IDS:
        raise RuntimeError("manifest Unit 3 rights IDs changed")
    if set(unit3_manifest.get("concept_ids") or []) != EXPECTED_CONCEPT_IDS:
        raise RuntimeError("manifest Unit 3 concept IDs changed")
    if {value.lower() for value in unit3_manifest.get("correction_ids") or []} != EXPECTED_CORRECTION_IDS:
        raise RuntimeError("manifest Unit 3 correction IDs changed")
    if unit3_manifest.get("exercise_count") != 21 or unit3_manifest.get("segment_count") != 2:
        raise RuntimeError("manifest Unit 3 structure counts changed")
    if tuple(unit3_manifest.get("solution_indices") or []) != SOLUTION_INDICES:
        raise RuntimeError("manifest Unit 3 solution indices changed")
    expected_target_hashes = {
        "lecture": digest(lecture_target_bytes),
        "worksheet": digest(worksheet_target_bytes),
        **{
            f"solution{index:02d}": extension_by_id[
                f"{worksheet_id}-e{index:03d}-solution"
            ]["target_sha256"]
            for index in SOLUTION_INDICES
        },
    }
    if unit3_manifest.get("target_hashes") != expected_target_hashes:
        raise RuntimeError("manifest Unit 3 translated-target hashes changed")

    for artifact_id in sorted(expected_artifacts):
        artifact = extension_by_id[artifact_id]
        expected_parent = fragment_targets.get(artifact_id, unit_id)
        if artifact.get("parent_id") != expected_parent:
            raise RuntimeError(f"Unit 3 artifact parent changed: {artifact_id}")
        artifact_path = (root / str(artifact.get("path"))).resolve()
        artifact_path.relative_to(root)
        artifact_bytes = artifact_path.read_bytes()
        if (
            len(artifact_bytes) != artifact.get("bytes")
            or digest(artifact_bytes) != artifact.get("target_sha256")
        ):
            raise RuntimeError(f"stale Unit 3 artifact binding: {artifact_id}")
    pdf_artifact = extension_by_id["o011-artifact-through-unit03-pdf"]
    if unit3_manifest.get("cumulative_pdf") != {
        "path": pdf_artifact["path"],
        "bytes": pdf_artifact["bytes"],
        "sha256": pdf_artifact["target_sha256"],
    }:
        raise RuntimeError("manifest cumulative PDF binding differs from artifact")
    if html_included:
        html_artifact_for_manifest = extension_by_id["o011-artifact-through-unit03-html"]
        if html_info != {
            "included": True,
            "path": html_artifact_for_manifest["path"],
            "bytes": html_artifact_for_manifest["bytes"],
            "sha256": html_artifact_for_manifest["target_sha256"],
        }:
            raise RuntimeError("manifest cumulative HTML binding differs from artifact")
    elif html_info != {"included": False, "path": None, "bytes": None, "sha256": None}:
        raise RuntimeError("manifest absent-HTML declaration is not canonical")
    prior_pdf = by_id["o011-artifact-through-unit02-pdf"]
    expected_cumulative_rights = [
        *(prior_pdf.get("component_rights_ids") or []),
        *sorted(EXPECTED_RIGHTS_IDS),
    ]
    if pdf_artifact.get("component_rights_ids") != expected_cumulative_rights:
        raise RuntimeError("cumulative Unit 3 PDF component-rights closure changed")
    if pdf_artifact.get("coverage_unit_ids") != [
        "o011-brenner-u01",
        "o011-brenner-u02",
        unit_id,
    ]:
        raise RuntimeError("cumulative Unit 3 PDF coverage declaration changed")
    if html_included:
        html_artifact = extension_by_id["o011-artifact-through-unit03-html"]
        if html_artifact.get("component_rights_ids") != expected_cumulative_rights:
            raise RuntimeError("cumulative Unit 3 HTML component-rights closure changed")

    expected_qa_artifacts = {
        "o011-qa-through-unit03-pdf-reproducibility": "o011-artifact-through-unit03-pdf",
        "o011-qa-through-unit03-pdf-structural": "o011-artifact-through-unit03-pdf",
        "o011-qa-through-unit03-pdf-visual": "o011-artifact-through-unit03-pdf",
        "o011-qa-unit03-final-math-audit": "o011-artifact-through-unit03-pdf",
        "o011-qa-unit03-lecture-translation": "o011-artifact-u03-l03-tex",
        "o011-qa-unit03-worksheet-translation": "o011-artifact-u03-w03-tex",
        "o011-qa-unit03-solution07-translation": (
            "o011-artifact-u03-w03-e007-solution-tex"
        ),
        "o011-qa-unit03-solution16-translation": (
            "o011-artifact-u03-w03-e016-solution-tex"
        ),
    }
    if html_included:
        expected_qa_artifacts["o011-qa-through-unit03-html-structural"] = (
            "o011-artifact-through-unit03-html"
        )
    declared_corrections: set[str] = set()
    for qa_id in sorted(expected_qa):
        qa_event = extension_by_id[qa_id]
        if qa_event.get("parent_id") != unit_id:
            raise RuntimeError(f"Unit 3 QA parent changed: {qa_id}")
        if qa_event.get("artifact_id") != expected_qa_artifacts.get(qa_id):
            raise RuntimeError(f"Unit 3 QA artifact binding changed: {qa_id}")
        receipt_path = (root / str(qa_event.get("receipt_path"))).resolve()
        receipt_path.relative_to(root)
        receipt_bytes = receipt_path.read_bytes()
        if digest(receipt_bytes) != qa_event.get("evidence_sha256"):
            raise RuntimeError(f"stale Unit 3 QA evidence binding: {qa_id}")
        admitted_document_limitation = (
            qa_id
            in {
                "o011-qa-through-unit03-pdf-structural",
                "o011-qa-through-unit03-html-structural",
            }
            and qa_event.get("result") == "admitted_limitation"
            and bool(qa_event.get("limitations"))
        )
        if qa_event.get("result") != "pass" and not admitted_document_limitation:
            raise RuntimeError(f"non-passing Unit 3 QA event: {qa_id}")
        for declaration in qa_event.get("declared_corrections") or []:
            if isinstance(declaration, str):
                declared_corrections.update(
                    item.lower() for item in declaration.split("+") if item
                )
    adverse_path = root / "00_control/ADVERSE_LEDGER.csv"
    adverse_bytes = adverse_path.read_bytes()
    adverse_rows = list(
        csv.DictReader(io.StringIO(adverse_bytes.decode("utf-8-sig")))
    )
    for row_number, row in enumerate(adverse_rows, 2):
        if None in row or any(
            row.get(field) is None
            for field in (
                "id",
                "severity",
                "surface",
                "status",
                "description",
                "disposition",
            )
        ):
            raise RuntimeError(f"malformed adverse-ledger CSV row {row_number}")
    if len({row["id"] for row in adverse_rows}) != len(adverse_rows):
        raise RuntimeError("duplicate IDs in adverse ledger")
    adverse_by_id = {row["id"].lower(): row for row in adverse_rows}
    live_unit3_corrections = {
        row["id"].lower()
        for row in adverse_rows
        if row.get("surface", "").startswith(("lecture03:", "worksheet03:"))
        and row.get("status") == "corrected_in_target"
    }
    if live_unit3_corrections != EXPECTED_CORRECTION_IDS:
        raise RuntimeError("live adverse-ledger Unit 3 correction closure changed")
    manifest_specs = {
        "lecture": (
            root / "00_control/LECTURE03_PROTECTED_CORRECTIONS.json",
            "source/units/unit-03/lecture03.id.tex",
        ),
        "worksheet": (
            root / "00_control/WORKSHEET03_PROTECTED_CORRECTIONS.json",
            "source/units/unit-03/worksheet03.id.tex",
        ),
    }
    correction_manifest_bindings: dict[str, dict[str, Any]] = {}
    expected_deltas_by_id: dict[str, list[dict[str, Any]]] = {
        correction_id: [] for correction_id in EXPECTED_CORRECTION_IDS
    }
    for owner, (path, expected_scope) in manifest_specs.items():
        data = path.read_bytes()
        manifest_data = json.loads(data.decode("utf-8"))
        if (
            manifest_data.get("schema_version") != 1
            or manifest_data.get("scope") != expected_scope
            or not isinstance(manifest_data.get("allowed_deltas"), list)
            or not manifest_data["allowed_deltas"]
        ):
            raise RuntimeError(f"live Unit 3 {owner} correction manifest changed")
        binding = {
            "path": repository_path(path, root),
            "bytes": len(data),
            "sha256": digest(data),
        }
        correction_manifest_bindings[owner] = binding
        for delta in manifest_data["allowed_deltas"]:
            delta_ids = {
                item.lower()
                for item in str(delta.get("correction_id", "")).split("+")
                if item
            }
            if not delta_ids or not delta_ids.issubset(EXPECTED_CORRECTION_IDS):
                raise RuntimeError(
                    f"unknown correction ID in live Unit 3 {owner} correction manifest"
                )
            if any(
                not adverse_by_id[correction_id]["surface"].startswith(f"{owner}03:")
                for correction_id in delta_ids
            ):
                raise RuntimeError(
                    f"live Unit 3 {owner} manifest names another surface's correction"
                )
            for correction_id in delta_ids:
                expected_deltas_by_id[correction_id].append(
                    {
                        "manifest_path": binding["path"],
                        "manifest_sha256": binding["sha256"],
                        **delta,
                    }
                )
    protected_correction_ids = {
        correction_id
        for correction_id, deltas in expected_deltas_by_id.items()
        if deltas
    }
    if declared_corrections != protected_correction_ids:
        raise RuntimeError(
            "translation QA declarations differ from the protected-delta closure"
        )
    math_qa = extension_by_id["o011-qa-unit03-final-math-audit"]
    expected_manifest_hashes = {
        owner: binding["sha256"]
        for owner, binding in sorted(correction_manifest_bindings.items())
    }
    if (
        {value.lower() for value in math_qa.get("correction_ids") or []}
        != EXPECTED_CORRECTION_IDS
        or math_qa.get("adverse_ledger_sha256") != digest(adverse_bytes)
        or math_qa.get("correction_manifest_sha256s") != expected_manifest_hashes
    ):
        raise RuntimeError("final mathematical QA correction evidence changed")
    math_audit_text = (
        root / "qa/unit-03/POST_REPAIR_MATH_AUDIT.md"
    ).read_text(encoding="utf-8")
    if not re.search(
        r"(?mi)^\s*(?:\*\*)?PASS(?:\s+[—–-][^\r\n]*)?(?:\*\*)?\s*$",
        math_audit_text,
    ):
        raise RuntimeError("final mathematical audit lacks an explicit PASS verdict line")
    required_audit_evidence = {
        *(correction_id.upper() for correction_id in EXPECTED_CORRECTION_IDS),
        digest(adverse_bytes),
        *expected_manifest_hashes.values(),
        str(pdf_artifact["target_sha256"]),
        *(str(value) for value in unit3_manifest["target_hashes"].values()),
    }
    if any(value not in math_audit_text for value in required_audit_evidence):
        raise RuntimeError("final mathematical audit evidence closure is incomplete")
    correction_targets: dict[str, str] = {}
    for correction_id in sorted(EXPECTED_CORRECTION_IDS):
        correction = extension_by_id[correction_id]
        ledger_row = adverse_by_id[correction_id]
        for field in ("severity", "description", "disposition"):
            if correction.get(field) != ledger_row.get(field):
                raise RuntimeError(f"correction ledger field drift in {correction_id}: {field}")
        if (
            correction.get("correction_status") != ledger_row.get("status")
            or correction.get("source_local_id") != ledger_row.get("surface")
            or correction.get("ledger_sha256") != digest(adverse_bytes)
            or correction.get("ledger_path") != "00_control/ADVERSE_LEDGER.csv"
        ):
            raise RuntimeError(f"stale correction ledger binding: {correction_id}")
        target_binding = correction.get("target_binding")
        if not isinstance(target_binding, dict):
            raise RuntimeError(f"missing target binding: {correction_id}")
        surface = ledger_row["surface"]
        solution_match = re.fullmatch(r"worksheet03:exercise(\d{2})-solution-.*", surface)
        worksheet_match = re.fullmatch(r"worksheet03:exercise(\d{2})-.*", surface)
        if solution_match:
            solution_index = int(solution_match.group(1))
            if solution_index not in SOLUTION_INDICES:
                raise RuntimeError(f"correction names a non-supplied solution: {correction_id}")
            owner = f"solution{solution_index:02d}"
            expected_target_path = (
                f"source/units/unit-03/worksheet03_exercise{solution_index:02d}_solution.id.tex"
            )
            expected_receipt_path = (
                f"qa/unit-03/worksheet03_exercise{solution_index:02d}_solution_translation.json"
            )
        elif worksheet_match:
            owner = "worksheet"
            expected_target_path = "source/units/unit-03/worksheet03.id.tex"
            expected_receipt_path = "qa/unit-03/worksheet03_translation.json"
        elif surface.startswith("worksheet03:"):
            owner = "worksheet"
            expected_target_path = "source/units/unit-03/worksheet03.id.tex"
            expected_receipt_path = "qa/unit-03/worksheet03_translation.json"
        elif surface.startswith("lecture03:"):
            owner = "lecture"
            expected_target_path = "source/units/unit-03/lecture03.id.tex"
            expected_receipt_path = "qa/unit-03/lecture_translation.json"
        else:
            raise RuntimeError(f"unknown Unit 3 correction target: {correction_id}")
        if (
            target_binding.get("path") != expected_target_path
            or target_binding.get("receipt_path") != expected_receipt_path
        ):
            raise RuntimeError(f"correction is bound to the wrong owner target: {correction_id}")
        live_binding(root, target_binding, f"correction target {correction_id}")
        receipt_path = (root / str(target_binding.get("receipt_path"))).resolve()
        receipt_path.relative_to(root)
        if digest(receipt_path.read_bytes()) != target_binding.get("receipt_sha256"):
            raise RuntimeError(f"stale correction receipt binding: {correction_id}")
        correction_manifest = correction.get("correction_manifest")
        expected_deltas = expected_deltas_by_id[correction_id]
        if expected_deltas:
            if owner not in correction_manifest_bindings:
                raise RuntimeError(
                    f"protected correction has no owner manifest: {correction_id}"
                )
            if correction_manifest != correction_manifest_bindings[owner]:
                raise RuntimeError(f"wrong correction-manifest binding: {correction_id}")
            live_binding(root, correction_manifest, f"correction manifest {correction_id}")
        elif correction_manifest is not None:
            raise RuntimeError(f"unneeded correction manifest claimed: {correction_id}")
        if (correction.get("protected_deltas") or []) != expected_deltas:
            raise RuntimeError(f"protected-delta closure changed: {correction_id}")
        for delta in expected_deltas:
            manifest_binding = {
                "path": delta.get("manifest_path"),
                "sha256": delta.get("manifest_sha256"),
            }
            protected_manifest_path = root / str(manifest_binding["path"])
            manifest_binding["bytes"] = len(protected_manifest_path.read_bytes())
            live_binding(root, manifest_binding, f"protected delta {correction_id}")
            declared = {
                item.lower()
                for item in str(delta.get("correction_id", "")).split("+")
                if item
            }
            if correction_id not in declared:
                raise RuntimeError(f"misassigned protected delta in {correction_id}")
        reader_binding = correction.get("reader_binding")
        if not isinstance(reader_binding, dict):
            raise RuntimeError(f"missing cumulative-reader binding: {correction_id}")
        expected_reader_receipts = {
            "build_receipt_path": "qa/unit-03/build.json",
            "structural_receipt_path": "qa/unit-03/pdf_structural_qa.json",
            "visual_receipt_path": "qa/unit-03/visual_qa.json",
            "math_audit_path": "qa/unit-03/POST_REPAIR_MATH_AUDIT.md",
        }
        if (
            reader_binding.get("path") != pdf_artifact.get("path")
            or reader_binding.get("bytes") != pdf_artifact.get("bytes")
            or reader_binding.get("sha256") != pdf_artifact.get("target_sha256")
        ):
            raise RuntimeError(f"wrong cumulative-reader binding: {correction_id}")
        live_binding(root, reader_binding, f"correction reader {correction_id}")
        for path_field, expected_path in expected_reader_receipts.items():
            hash_field = path_field.removesuffix("_path") + "_sha256"
            if reader_binding.get(path_field) != expected_path:
                raise RuntimeError(
                    f"wrong cumulative-reader receipt path in {correction_id}: {path_field}"
                )
            evidence = (root / expected_path).read_bytes()
            if reader_binding.get(hash_field) != digest(evidence):
                raise RuntimeError(
                    f"stale cumulative-reader receipt in {correction_id}: {path_field}"
                )
        if solution_match:
            correction_targets[correction_id] = (
                f"{worksheet_id}-e{int(solution_match.group(1)):03d}-solution"
            )
        elif worksheet_match:
            correction_targets[correction_id] = (
                f"{worksheet_id}-e{int(worksheet_match.group(1)):03d}"
            )
        elif surface.startswith("worksheet03:"):
            correction_targets[correction_id] = worksheet_id
        elif surface.startswith("lecture03:"):
            correction_targets[correction_id] = lecture_id
        else:
            raise RuntimeError(f"unknown Unit 3 correction target: {correction_id}")

    expected_relations: dict[str, tuple[str, str, str]] = {}

    def expect_relation(
        relation_id: str, relation_type: str, from_id: str, to_id: str
    ) -> None:
        if relation_id in expected_relations:
            raise RuntimeError(f"duplicate expected relation ID: {relation_id}")
        expected_relations[relation_id] = (relation_type, from_id, to_id)

    concept_sections = {
        "o011-concept-arc-length-parametrization": 1,
        "o011-concept-planar-signed-curvature": 1,
        "o011-concept-curvature-circle": 1,
        "o011-concept-evolute": 1,
        "o011-concept-general-curve-curvature": 2,
    }
    for concept_id, section in concept_sections.items():
        slug = concept_id.removeprefix("o011-concept-")
        expect_relation(
            f"o011-rel-u03-l03-s{section:02d}-covers-{slug}",
            "covers",
            f"{lecture_id}-s{section:02d}",
            concept_id,
        )
    for term_id in term_ids:
        expect_relation(
            f"o011-rel-u03-uses-{term_id.removeprefix('o011-')}",
            "uses_term",
            unit_id,
            term_id,
        )
    for index in range(2, 22):
        expect_relation(
            f"o011-rel-u03-w03-e{index - 1:03d}-precedes-e{index:03d}",
            "precedes",
            f"{worksheet_id}-e{index - 1:03d}",
            f"{worksheet_id}-e{index:03d}",
        )
    for index in SOLUTION_INDICES:
        solution_id = f"{worksheet_id}-e{index:03d}-solution"
        expect_relation(
            f"o011-rel-u03-w03-e{index:03d}-solution-solves-e{index:03d}",
            "solves",
            solution_id,
            f"{worksheet_id}-e{index:03d}",
        )
    for asset_id, owner_id in asset_owner.items():
        owner = "lecture" if owner_id == lecture_id else "worksheet"
        slug = asset_id.removeprefix("o011-asset-file-")
        expect_relation(
            f"o011-rel-u03-{owner}-uses-{slug}", "uses", owner_id, asset_id
        )
    for artifact_id, target_id in fragment_targets.items():
        expect_relation(
            f"o011-rel-{artifact_id.removeprefix('o011-')}-represents-{target_id.removeprefix('o011-')}",
            "represents",
            artifact_id,
            target_id,
        )
    qa_targets = {
        "o011-qa-unit03-authority-preflight": unit_id,
        "o011-qa-unit03-authority-verification": unit_id,
        "o011-qa-unit03-media-closure": unit_id,
        "o011-qa-through-unit03-pdf-reproducibility": "o011-artifact-through-unit03-pdf",
        "o011-qa-through-unit03-pdf-structural": "o011-artifact-through-unit03-pdf",
        "o011-qa-through-unit03-pdf-visual": "o011-artifact-through-unit03-pdf",
        "o011-qa-unit03-final-math-audit": unit_id,
        "o011-qa-unit03-lecture-translation": lecture_id,
        "o011-qa-unit03-worksheet-translation": worksheet_id,
        "o011-qa-unit03-solution07-translation": f"{worksheet_id}-e007-solution",
        "o011-qa-unit03-solution16-translation": f"{worksheet_id}-e016-solution",
    }
    if html_included:
        qa_targets["o011-qa-through-unit03-html-structural"] = (
            "o011-artifact-through-unit03-html"
        )
    if set(qa_targets) != expected_qa:
        raise RuntimeError("internal expected QA target map is incomplete")
    for qa_id, target_id in qa_targets.items():
        if extension_by_id[qa_id].get("target_id") != target_id:
            raise RuntimeError(f"Unit 3 QA target changed: {qa_id}")
        expect_relation(
            f"o011-rel-{qa_id.removeprefix('o011-')}-verifies-{target_id.removeprefix('o011-')}",
            "verifies",
            qa_id,
            target_id,
        )
    expect_relation(
        "o011-rel-artifact-through-unit03-pdf-represents-u03-checkpoint",
        "represents",
        "o011-artifact-through-unit03-pdf",
        unit_id,
    )
    if html_included:
        expect_relation(
            "o011-rel-artifact-through-unit03-html-represents-u03-checkpoint",
            "represents",
            "o011-artifact-through-unit03-html",
            unit_id,
        )
    expect_relation(
        "o011-rel-u02-precedes-u03",
        "precedes",
        "o011-brenner-u02",
        unit_id,
    )
    for correction_id, target_id in correction_targets.items():
        expect_relation(
            f"o011-rel-{correction_id.removeprefix('o011-')}-corrects-{target_id.removeprefix('o011-')}",
            "corrects",
            correction_id,
            target_id,
        )
    for child in extension:
        parent_id = child.get("parent_id")
        if parent_id and child.get("entity_type") not in {"relation", "rights", "correction"}:
            child_id = str(child["id"])
            expect_relation(
                f"o011-rel-contains-{child_id.removeprefix('o011-')}",
                "contains",
                str(parent_id),
                child_id,
            )
    actual_relation_ids = entity_ids(extension, "relation")
    if actual_relation_ids != set(expected_relations):
        raise RuntimeError(
            "Unit 3 relation closure changed: "
            f"missing={sorted(set(expected_relations) - actual_relation_ids)}, "
            f"extra={sorted(actual_relation_ids - set(expected_relations))}"
        )
    for relation_id, expected in expected_relations.items():
        relation = extension_by_id[relation_id]
        actual = (
            relation.get("relation_type"),
            relation.get("from_id"),
            relation.get("to_id"),
        )
        if actual != expected:
            raise RuntimeError(f"relation endpoint/type drift: {relation_id}")

    for label, value in (("records", records), ("manifest", manifest)):
        for key, string in walk_strings(value):
            folded = string.casefold()
            if (key == "path" or key.endswith("_path")) and (
                string.startswith(("/", "\\")) or WINDOWS_ABSOLUTE.search(string)
            ):
                raise RuntimeError(f"absolute path in {label}:{key}")
            if any(marker in folded for marker in PRIVATE_MARKERS):
                raise RuntimeError(f"private or credential marker in {label}:{key}")
    for record in records:
        source_display_id = record.get("source_display_id")
        if source_display_id and re.fullmatch(r"(?:3|4)\.2\.\d+", str(source_display_id)):
            raise RuntimeError(
                f"wrapper chapter prefix leaked into source_display_id in {record['id']}"
            )

    receipt = {
        "schema_version": 1,
        "workflow": "o011-unit03-backend-qa-v1",
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
        "unit12_preservation": {
            "record_count": len(baseline_records),
            "jsonl_bytes": len(baseline_jsonl),
            "jsonl_sha256": digest(baseline_jsonl),
            "csv_bytes": len(baseline_csv),
            "csv_sha256": digest(baseline_csv),
            "byte_identical_prefixes": True,
        },
        "unit03": {
            "record_count": len(extension),
            "entity_counts": extension_counts,
            "lecture_segment_count": 2,
            "worksheet_exercise_count": 21,
            "supplied_solution_indices": list(SOLUTION_INDICES),
            "concept_count": len(EXPECTED_CONCEPT_IDS),
            "term_count": len(term_ids),
            "asset_count": len(EXPECTED_ASSET_IDS),
            "per_file_rights_count": len(EXPECTED_RIGHTS_IDS),
            "correction_ids": sorted(EXPECTED_CORRECTION_IDS),
            "artifact_count": len(expected_artifacts),
            "qa_event_count": len(expected_qa),
            "relation_count": len(expected_relations),
            "html_included": html_included,
            "cumulative_pdf": {
                "path": pdf_artifact["path"],
                "bytes": pdf_artifact["bytes"],
                "sha256": pdf_artifact["target_sha256"],
            },
        },
        "checks": {
            "schema_valid": True,
            "unique_ids": True,
            "references_resolved": True,
            "unit12_jsonl_prefix_byte_identical": True,
            "unit12_csv_prefix_byte_identical": True,
            "csv_ids_and_row_count_match_jsonl": True,
            "manifest_counts_and_hashes_current": True,
            "artifacts_and_media_current": True,
            "qa_receipts_current": True,
            "exercise_points_hints_and_solution_markers_present": True,
            "per_file_rights_complete": True,
            "correction_ledger_manifests_targets_and_receipts_current": True,
            "relations_exact": True,
            "source_numbering_preserved": True,
            "absolute_paths_absent": True,
            "private_and_credential_markers_absent": True,
        },
    }
    output_path = root / "qa/unit-03/backend_qa.json"
    receipt_bytes = (
        json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    ).encode("utf-8")
    assert_public_safe_bytes("qa/unit-03/backend_qa.json", receipt_bytes)
    output_path.write_bytes(receipt_bytes)


if __name__ == "__main__":
    main()
