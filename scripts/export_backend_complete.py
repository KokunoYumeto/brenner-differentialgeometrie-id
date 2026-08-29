#!/usr/bin/env python3
"""Append the complete O011 edition to the immutable published Unit 22 backend.

The suffix covers Brenner Units 23--29, the ten occurrence-mapped official
exam forms and their source-supplied solutions, the six separately provenanced
original exam repairs, and both original 16-item bridges.  The existing Unit 22
JSONL and CSV bytes are an immutable prefix; generated views are never edited by
hand.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from jsonschema import Draft202012Validator, FormatChecker

sys.path.insert(0, str(Path(__file__).resolve().parent))
import export_backend_v22 as v22  # noqa: E402


WORKFLOW = "o011-export-backend-complete"
VERIFY_WORKFLOW = "o011-verify-backend-complete"
BASELINE_RECORD_COUNT = 4324
BASELINE_JSONL_BYTES = 2672207
BASELINE_JSONL_SHA256 = "448982cccc2f7c21e275faae1314f3ef6731f6ba36c939035b295dcc7b3d195a"
BASELINE_CSV_LINES = 4325
BASELINE_CSV_BYTES = 987360
BASELINE_CSV_SHA256 = "8bc81cbe634cb94f71640d1f5fd5e4c7a7697647f3a21b4ea161cb18c031d34b"
BASELINE_CORE_EXERCISES = 457
BASELINE_CORE_SOURCE_SOLUTIONS = 64
FINAL_CORE_EXERCISES = 576
FINAL_CORE_SOURCE_SOLUTIONS = 84

UNITS = tuple(range(23, 30))
EXPECTED_UNIT_CENSUS: dict[int, dict[str, Any]] = {
    23: {"lecture_sections": 3, "worksheet_sections": 2, "exercises": 30, "practice": 23, "graded": 7, "points": 26, "solutions": [6, 13, 16, 17], "hints": [4, 5, 19], "assets": 3},
    24: {"lecture_sections": 2, "worksheet_sections": 2, "exercises": 15, "practice": 10, "graded": 5, "points": 18, "solutions": [], "hints": [], "assets": 0},
    25: {"lecture_sections": 4, "worksheet_sections": 2, "exercises": 25, "practice": 21, "graded": 4, "points": 15, "solutions": [1, 7, 8, 11, 12, 14], "hints": [], "assets": 0},
    26: {"lecture_sections": 2, "worksheet_sections": 2, "exercises": 16, "practice": 12, "graded": 4, "points": 9, "solutions": [3, 6, 9], "hints": [], "assets": 0},
    27: {"lecture_sections": 3, "worksheet_sections": 2, "exercises": 23, "practice": 19, "graded": 4, "points": 18, "solutions": [4, 5, 9, 13], "hints": [], "assets": 1},
    28: {"lecture_sections": 2, "worksheet_sections": 2, "exercises": 7, "practice": 5, "graded": 2, "points": 5, "solutions": [2, 5], "hints": [], "assets": 0},
    29: {"lecture_sections": 2, "worksheet_sections": 2, "exercises": 3, "practice": 3, "graded": 0, "points": 0, "solutions": [2], "hints": [], "assets": 1},
}
EXPECTED_EXAM_CENSUS = {
    "forms": 10,
    "nominal_slots": 147,
    "actual_occurrences": 123,
    "placeholder_slots": 24,
    "unique_semantic_tasks": 119,
    "source_supplied_solutions": 117,
    "source_missing_solutions": 6,
}
EXPECTED_ORIGINAL_REPAIRS = 6
EXPECTED_BRIDGES = 2
EXPECTED_BRIDGE_EXERCISES = 24
EXPECTED_BRIDGE_MASTERY = 8
EXPECTED_BRIDGE_ITEMS = 32
DEFAULT_TRANSLATION_STATE = "mathematically_reviewed"

CSV_FIELDS = v22.CSV_FIELDS
ENTITY_TYPES = v22.ENTITY_TYPES
COURSE_ID = v22.v19.COURSE_ID
EDITION_ID = v22.v19.EDITION_ID
RESOURCE_ID = v22.v19.RESOURCE_ID
TEXT_RIGHTS_ID = v22.v19.TEXT_RIGHTS_ID
MODEL_IDENTIFICATION = v22.v19.MODEL_IDENTIFICATION

CORE_MATH_CHECKS = {
    "command_sequence_equal_or_declared",
    "environment_sequence_equal_or_declared",
    "inline_math_equal_or_declared",
    "display_math_equal_or_declared",
    "protected_macro_calls_equal_or_declared",
    "brace_profile_equal_or_declared",
    "all_declared_deltas_consumed",
    "evidence_only_deltas_verified",
}
REFERENCE_KEYS = {
    "parent_id", "resource_id", "edition_id", "rights_component_id",
    "target_id", "artifact_id", "from_id", "to_id",
    "semantic_problem_id", "occurrence_id",
}
REFERENCE_LIST_KEYS = {"component_rights_ids", "target_ids", "internal_prerequisite_ids"}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(record: dict[str, Any]) -> bytes:
    return (json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def binding(path: Path, root: Path) -> dict[str, Any]:
    data = path.read_bytes()
    return {"path": path.relative_to(root).as_posix(), "bytes": len(data), "sha256": sha256_bytes(data)}


def media_type(path: str) -> str:
    return {
        ".json": "application/json", ".md": "text/markdown", ".csv": "text/csv",
        ".html": "text/html", ".svg": "image/svg+xml", ".png": "image/png",
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif",
        ".pdf": "application/pdf",
    }.get(Path(path).suffix.lower(), "application/x-tex")


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def base_record(record_id: str, entity_type: str, checkpoint: str, **fields: Any) -> dict[str, Any]:
    record: dict[str, Any] = {
        "schema": "o011-modular-backend",
        "schema_version": 1,
        "id": record_id,
        "entity_type": entity_type,
        "status": "active",
        "timestamp": checkpoint,
        "workflow": WORKFLOW,
        "supersedes": None,
    }
    record.update(fields)
    return record


def add_relation(records: list[dict[str, Any]], checkpoint: str, relation_id: str, relation_type: str, from_id: str, to_id: str) -> None:
    records.append(base_record(relation_id, "relation", checkpoint, relation_type=relation_type, from_id=from_id, to_id=to_id))


def add_artifact(
    records: list[dict[str, Any]], checkpoint: str, artifact_id: str,
    bound: dict[str, Any], parent_id: str, kind: str,
    *, language: str | None = None, locale: str | None = None,
    source_sha256: str | None = None, rights_id: str = TEXT_RIGHTS_ID,
    translation_state: str | None = None,
) -> None:
    records.append(base_record(
        artifact_id, "artifact", checkpoint, artifact_kind=kind,
        bytes=bound["bytes"], path=bound["path"], media_type=media_type(bound["path"]),
        parent_id=parent_id, rights_component_id=rights_id,
        component_rights_ids=[rights_id], target_sha256=bound["sha256"],
        source_sha256=source_sha256, language=language, locale=locale,
        translation_state=translation_state,
    ))


def assert_prefix(root: Path) -> tuple[bytes, bytes, list[dict[str, Any]]]:
    jsonl = (root / "backend/records.jsonl").read_bytes()
    lines = jsonl.splitlines(keepends=True)
    if len(lines) < BASELINE_RECORD_COUNT:
        raise RuntimeError("backend has fewer than the immutable 4,324-record Unit 22 prefix")
    jsonl_prefix = b"".join(lines[:BASELINE_RECORD_COUNT])
    if len(jsonl_prefix) != BASELINE_JSONL_BYTES or sha256_bytes(jsonl_prefix) != BASELINE_JSONL_SHA256:
        raise RuntimeError("immutable published Unit 22 JSONL prefix changed")
    csv_data = (root / "backend/records.csv").read_bytes()
    csv_lines = csv_data.splitlines(keepends=True)
    if len(csv_lines) < BASELINE_CSV_LINES:
        raise RuntimeError("backend CSV has fewer than the immutable Unit 22 prefix")
    csv_prefix = b"".join(csv_lines[:BASELINE_CSV_LINES])
    if len(csv_prefix) != BASELINE_CSV_BYTES or sha256_bytes(csv_prefix) != BASELINE_CSV_SHA256:
        raise RuntimeError("immutable published Unit 22 CSV prefix changed")
    baseline = [json.loads(line.decode("utf-8")) for line in lines[:BASELINE_RECORD_COUNT]]
    return jsonl_prefix, csv_prefix, baseline


def assert_file(path: Path, label: str) -> None:
    if not path.is_file():
        raise RuntimeError(f"missing {label}: {path.as_posix()}")


def iter_declared_bindings(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        if isinstance(value.get("path"), str) and isinstance(value.get("bytes"), int) and isinstance(value.get("sha256"), str):
            yield {"path": value["path"], "bytes": value["bytes"], "sha256": value["sha256"]}
        for prefix in ("source", "target", "learner"):
            if isinstance(value.get(prefix), str) and isinstance(value.get(f"{prefix}_bytes"), int) and isinstance(value.get(f"{prefix}_sha256"), str):
                yield {"path": value[prefix], "bytes": value[f"{prefix}_bytes"], "sha256": value[f"{prefix}_sha256"]}
        for child in value.values():
            yield from iter_declared_bindings(child)
    elif isinstance(value, list):
        for child in value:
            yield from iter_declared_bindings(child)


def assert_json_binds(receipt: Any, expected: dict[str, Any], label: str) -> None:
    if not any(all(candidate.get(key) == expected.get(key) for key in ("path", "bytes", "sha256")) for candidate in iter_declared_bindings(receipt)):
        raise RuntimeError(f"stale or absent file binding in {label}: {expected['path']}")


def assert_passing_math_receipt(receipt: dict[str, Any], label: str) -> None:
    if receipt.get("status") != "pass":
        raise RuntimeError(f"non-passing translation receipt: {label}")
    if receipt.get("failures") not in (None, []):
        raise RuntimeError(f"translation receipt has failures: {label}")
    checks = receipt.get("checks")
    if isinstance(checks, dict):
        false_checks = sorted(key for key, value in checks.items() if value is False)
        if false_checks:
            raise RuntimeError(f"failed checks in {label}: {', '.join(false_checks)}")
        present_math = CORE_MATH_CHECKS.intersection(checks)
        if present_math and any(checks[key] is not True for key in present_math):
            raise RuntimeError(f"non-true protected-math checks in {label}")


def balanced_braces(text: str) -> bool:
    depth = 0
    index = 0
    while index < len(text):
        char = text[index]
        if char == "\\":
            index += 2
            continue
        if char == "%":
            newline = text.find("\n", index)
            if newline < 0:
                break
            index = newline + 1
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth < 0:
                return False
        index += 1
    return depth == 0


def braced_argument(text: str, cursor: int) -> tuple[str, int]:
    while cursor < len(text) and text[cursor].isspace():
        cursor += 1
    if cursor >= len(text) or text[cursor] != "{":
        raise RuntimeError(f"expected braced argument near offset {cursor}")
    start = cursor + 1
    depth = 1
    cursor += 1
    while cursor < len(text):
        if text[cursor] == "\\":
            cursor += 2
            continue
        if text[cursor] == "{":
            depth += 1
        elif text[cursor] == "}":
            depth -= 1
            if depth == 0:
                return text[start:cursor], cursor + 1
        cursor += 1
    raise RuntimeError("unterminated TeX braced argument")


def macro_calls(text: str, names: tuple[str, ...], argument_count: int) -> list[dict[str, Any]]:
    pattern = re.compile(r"\\(" + "|".join(sorted((re.escape(name) for name in names), key=len, reverse=True)) + r")(?=\s*\{)")
    calls: list[dict[str, Any]] = []
    for match in pattern.finditer(text):
        cursor = match.end()
        args: list[str] = []
        for _ in range(argument_count):
            argument, cursor = braced_argument(text, cursor)
            args.append(argument)
        calls.append({"macro": match.group(1), "args": args, "start": match.start(), "end": cursor})
    return calls


def marker_slices(text: str, pattern: str) -> list[str]:
    starts = [match.start() for match in re.finditer(pattern, text)]
    return [text[start:starts[index + 1] if index + 1 < len(starts) else len(text)] for index, start in enumerate(starts)]


def unit_ids(unit: int) -> tuple[str, str, str]:
    tag = f"{unit:02d}"
    unit_id = f"o011-brenner-u{tag}"
    return unit_id, f"{unit_id}-l{tag}", f"{unit_id}-w{tag}"


def select_unit_receipt(qa_dir: Path, surface: str, index: int | None = None) -> Path:
    candidates: list[Path] = []
    for path in sorted(qa_dir.glob("*.json"), key=lambda item: item.name.lower()):
        name = path.name.lower()
        if "translation" not in name or any(token in name for token in ("prepare", "sanitize", "pre_manifest", "+.json", "protected")):
            continue
        if surface == "lecture" and "lecture" in name:
            candidates.append(path)
        elif surface == "worksheet" and "worksheet" in name and "exercise" not in name and "solution" not in name:
            candidates.append(path)
        elif surface == "solution" and index is not None:
            if f"exercise{index:02d}" in name or f"solution{index:02d}" in name:
                candidates.append(path)
    passing = []
    for path in candidates:
        value = load_json(path)
        if isinstance(value, dict) and value.get("status") == "pass":
            passing.append(path)
    if len(passing) != 1:
        raise RuntimeError(f"expected one passing Unit {qa_dir.name} {surface} translation receipt, found {[path.name for path in passing]}")
    return passing[0]


def prepare_unit(root: Path, unit: int, inputs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    tag = f"{unit:02d}"
    qa_dir = root / f"qa/unit-{tag}"
    preflight_path = qa_dir / "AUTHORITY_PREFLIGHT.json"
    closure_path = qa_dir / "solution_closure.json"
    source_lecture = root / f"authority/expanded/lecture{tag}_source.de.tex"
    source_worksheet = root / f"authority/expanded/worksheet{tag}_source.de.tex"
    target_lecture = root / f"source/units/unit-{tag}/lecture{tag}.id.tex"
    target_worksheet = root / f"source/units/unit-{tag}/worksheet{tag}.id.tex"
    for path, label in ((preflight_path, "unit preflight"), (closure_path, "unit solution closure"), (source_lecture, "lecture source"), (source_worksheet, "worksheet source"), (target_lecture, "lecture target"), (target_worksheet, "worksheet target")):
        assert_file(path, label)
    preflight = load_json(preflight_path)
    closure = load_json(closure_path)
    if preflight.get("status") != "pass" or int(preflight.get("unit", -1)) != unit:
        raise RuntimeError(f"Unit {unit} authority preflight is not passing")
    structure = preflight.get("structure", {})
    expected = EXPECTED_UNIT_CENSUS[unit]
    actual = {
        "lecture_sections": structure.get("lecture_section_count"),
        "worksheet_sections": structure.get("worksheet_section_count"),
        "exercises": structure.get("worksheet_exercise_count"),
        "practice": structure.get("worksheet_practice_count"),
        "graded": structure.get("worksheet_graded_count"),
        "points": structure.get("worksheet_point_total"),
        "solutions": list(preflight.get("solutions", {}).get("supplied_solution_indices", [])),
        "hints": [int(item["exercise_index"]) for item in preflight.get("solutions", {}).get("exercises", []) if str(item.get("hint_field") or "").strip()],
        "assets": len(preflight.get("media", {}).get("assets", [])),
    }
    if actual != expected:
        raise RuntimeError(f"Unit {unit} semantic census changed: {actual!r}")
    closure_expected = {
        "exercise_count": expected["exercises"], "practice_exercise_count": expected["practice"],
        "graded_exercise_count": expected["graded"], "point_value_total": expected["points"],
        "supplied_solution_indices": expected["solutions"],
    }
    for key, value in closure_expected.items():
        if closure.get(key) != value:
            raise RuntimeError(f"Unit {unit} solution closure changed: {key}")
    if closure.get("macro_api_agreement") is not True:
        raise RuntimeError(f"Unit {unit} solution macro/API agreement is not passing")

    paths: dict[str, Path] = {
        "preflight": preflight_path, "solution_closure": closure_path,
        "lecture_source": source_lecture, "worksheet_source": source_worksheet,
        "lecture_target": target_lecture, "worksheet_target": target_worksheet,
        "lecture_receipt": select_unit_receipt(qa_dir, "lecture"),
        "worksheet_receipt": select_unit_receipt(qa_dir, "worksheet"),
    }
    for index in expected["solutions"]:
        paths[f"solution{index}_source"] = root / f"authority/expanded/worksheet{tag}_exercise{index:02d}_solution_source.de.tex"
        paths[f"solution{index}_target"] = root / f"source/units/unit-{tag}/worksheet{tag}_exercise{index:02d}_solution.id.tex"
        paths[f"solution{index}_receipt"] = select_unit_receipt(qa_dir, "solution", index)
    correction_paths = sorted(qa_dir.glob("*CORRECTIONS.json"), key=lambda item: item.name)
    for index, path in enumerate(correction_paths, 1):
        paths[f"correction_manifest:{index:02d}"] = path
    media_receipt = root / f"qa/complete/cumulative-media/unit-{tag}_media.json"
    assert_file(media_receipt, f"Unit {unit} cumulative media receipt")
    paths["media_receipt"] = media_receipt
    for asset in preflight.get("media", {}).get("assets", []):
        paths[f"media:{asset['filename']}"] = root / str(asset.get("binary", {}).get("path") or f"authority/media/{asset['filename']}")
    for key, path in paths.items():
        assert_file(path, f"Unit {unit} input {key}")
    bindings = {key: binding(path, root) for key, path in sorted(paths.items())}
    assert_json_binds(preflight, bindings["lecture_source"], f"Unit {unit} preflight")
    assert_json_binds(preflight, bindings["worksheet_source"], f"Unit {unit} preflight")
    for surface in ("lecture", "worksheet"):
        receipt = load_json(paths[f"{surface}_receipt"])
        assert_passing_math_receipt(receipt, bindings[f"{surface}_receipt"]["path"])
        assert_json_binds(receipt, bindings[f"{surface}_source"], f"Unit {unit} {surface} translation receipt")
        assert_json_binds(receipt, bindings[f"{surface}_target"], f"Unit {unit} {surface} translation receipt")
    for index in expected["solutions"]:
        assert_json_binds(closure, bindings[f"solution{index}_source"], f"Unit {unit} solution closure")
        receipt = load_json(paths[f"solution{index}_receipt"])
        assert_passing_math_receipt(receipt, bindings[f"solution{index}_receipt"]["path"])
        assert_json_binds(receipt, bindings[f"solution{index}_source"], f"Unit {unit} solution {index} receipt")
        assert_json_binds(receipt, bindings[f"solution{index}_target"], f"Unit {unit} solution {index} receipt")
    media_data = load_json(media_receipt)
    if int(media_data.get("source_count", -1)) != expected["assets"]:
        raise RuntimeError(f"Unit {unit} complete-reader media census changed")
    media_by_name = {str(item.get("filename")): item for item in media_data.get("media", [])}
    for asset in preflight.get("media", {}).get("assets", []):
        bound = bindings[f"media:{asset['filename']}"]
        declared = media_by_name.get(str(asset["filename"]), {})
        if declared.get("canonical_path") != bound["path"] or declared.get("canonical_bytes") != bound["bytes"] or declared.get("canonical_sha256") != bound["sha256"]:
            raise RuntimeError(f"Unit {unit} stale complete-reader media binding: {asset['filename']}")
    for key, bound in bindings.items():
        inputs[f"u{tag}:{key}"] = bound
    return {"unit": unit, "tag": tag, "preflight": preflight, "closure": closure, "paths": paths, "bindings": bindings, "census": actual}


def make_unit_records(context: dict[str, Any], checkpoint: str, state: str) -> list[dict[str, Any]]:
    unit = int(context["unit"])
    tag = str(context["tag"])
    preflight = context["preflight"]
    structure = preflight["structure"]
    paths = context["paths"]
    bindings = context["bindings"]
    solution_indices = tuple(EXPECTED_UNIT_CENSUS[unit]["solutions"])
    unit_id, lecture_id, worksheet_id = unit_ids(unit)
    root_authority = preflight["authority"]["pages"]
    exercise_meta = {int(item["exercise_index"]): item for item in preflight["solutions"]["exercises"]}
    common = {"edition_id": EDITION_ID, "resource_id": RESOURCE_ID, "language": "Indonesian", "locale": "id-ID", "rights_component_id": TEXT_RIGHTS_ID}
    records: list[dict[str, Any]] = []
    records.append(base_record(
        unit_id, "unit", checkpoint, **common, order=unit, parent_id=COURSE_ID,
        path=f"source/units/unit-{tag}", reader_anchor=f"unit-{tag}",
        source_local_id=f"course-unit-{tag}", unit_kind="lecture_worksheet_pair",
        source_locator=f"Kurs:Differentialgeometrie (Osnabrück 2023)/Vorlesung {unit} + Arbeitsblatt {unit}",
        source_sha256=sha256_bytes(paths["lecture_source"].read_bytes() + paths["worksheet_source"].read_bytes()),
        target_sha256=sha256_bytes(paths["lecture_target"].read_bytes() + paths["worksheet_target"].read_bytes()),
        authority_page_revisions={
            "lecture_root": [root_authority["lecture_root"]["pageid"], root_authority["lecture_root"]["revid"]],
            "lecture_latex": [root_authority["lecture_latex"]["pageid"], root_authority["lecture_latex"]["revid"]],
            "worksheet_root": [root_authority["worksheet_root"]["pageid"], root_authority["worksheet_root"]["revid"]],
            "worksheet_latex": [root_authority["worksheet_latex"]["pageid"], root_authority["worksheet_latex"]["revid"]],
        },
        translation_assistance={"model": MODEL_IDENTIFICATION, "role": "translation and production assistance under user direction", "human_and_source_credits_preserved": True},
        translation_state=state,
    ))
    records.append(base_record(lecture_id, "unit", checkpoint, **common, order=1, parent_id=unit_id, path=bindings["lecture_target"]["path"], reader_anchor=f"unit-{tag}-lecture", source_local_id=f"lecture{tag}", source_locator=root_authority["lecture_root"]["title"], source_sha256=bindings["lecture_source"]["sha256"], target_sha256=bindings["lecture_target"]["sha256"], pageid=root_authority["lecture_root"]["pageid"], revid=root_authority["lecture_root"]["revid"], unit_kind="lecture", translation_state=state))
    records.append(base_record(worksheet_id, "unit", checkpoint, **common, order=2, parent_id=unit_id, path=bindings["worksheet_target"]["path"], reader_anchor=f"unit-{tag}-worksheet", source_local_id=f"worksheet{tag}", source_locator=root_authority["worksheet_root"]["title"], source_sha256=bindings["worksheet_source"]["sha256"], target_sha256=bindings["worksheet_target"]["sha256"], pageid=root_authority["worksheet_root"]["pageid"], revid=root_authority["worksheet_root"]["revid"], unit_kind="worksheet", translation_state=state))

    lecture_source_sections = marker_slices(paths["lecture_source"].read_text(encoding="utf-8"), r"\\zwischenueberschrift\{")
    lecture_target_sections = marker_slices(paths["lecture_target"].read_text(encoding="utf-8"), r"\\zwischenueberschrift\{")
    worksheet_source_sections = marker_slices(paths["worksheet_source"].read_text(encoding="utf-8"), r"\\zwischenueberschrift\{")
    worksheet_target_sections = marker_slices(paths["worksheet_target"].read_text(encoding="utf-8"), r"\\zwischenueberschrift\{")
    for values, expected, label in ((lecture_source_sections, structure["lecture_section_count"], "lecture source"), (lecture_target_sections, structure["lecture_section_count"], "lecture target"), (worksheet_source_sections, structure["worksheet_section_count"], "worksheet source"), (worksheet_target_sections, structure["worksheet_section_count"], "worksheet target")):
        if len(values) != expected:
            raise RuntimeError(f"Unit {unit} {label} section count changed")
    for index, (source_part, target_part) in enumerate(zip(lecture_source_sections, lecture_target_sections), 1):
        records.append(base_record(f"{lecture_id}-s{index:02d}", "segment", checkpoint, **common, order=index, parent_id=lecture_id, path=f"{bindings['lecture_target']['path']}#section-{index}", reader_anchor=f"unit-{tag}-lecture-section-{index}", source_local_id=f"lecture{tag}:section:{index}", source_locator=f"{root_authority['lecture_root']['title']}#section-{index}", source_sha256=sha256_bytes(source_part.encode()), target_sha256=sha256_bytes(target_part.encode()), segment_kind="lecture_section", translation_state=state))
    for index, (source_part, target_part) in enumerate(zip(worksheet_source_sections, worksheet_target_sections), 1):
        records.append(base_record(f"{worksheet_id}-s{index:02d}", "segment", checkpoint, **common, order=index, parent_id=worksheet_id, path=f"{bindings['worksheet_target']['path']}#section-{index}", reader_anchor=f"unit-{tag}-worksheet-section-{index}", source_local_id=f"worksheet{tag}:section:{index}", source_locator=f"{root_authority['worksheet_root']['title']}#section-{index}", source_sha256=sha256_bytes(source_part.encode()), target_sha256=sha256_bytes(target_part.encode()), segment_kind="worksheet_section", translation_state=state))

    source_exercises = marker_slices(paths["worksheet_source"].read_text(encoding="utf-8"), r"\\inputaufgabe(?:gibtloesung)?")
    target_exercises = marker_slices(paths["worksheet_target"].read_text(encoding="utf-8"), r"\\inputaufgabe(?:gibtloesung)?")
    if len(source_exercises) != structure["worksheet_exercise_count"] or len(target_exercises) != structure["worksheet_exercise_count"]:
        raise RuntimeError(f"Unit {unit} exercise occurrence topology changed")
    for index, (source_part, target_part) in enumerate(zip(source_exercises, target_exercises), 1):
        meta = exercise_meta[index]
        point = meta.get("point_value")
        exercise_id = f"{worksheet_id}-e{index:03d}"
        records.append(base_record(
            exercise_id, "unit", checkpoint, **common, order=index, parent_id=worksheet_id,
            path=f"{bindings['worksheet_target']['path']}#exercise-{index}", reader_anchor=f"unit-{tag}-exercise-{index:03d}",
            source_local_id=f"worksheet{tag}:exercise:{index}", source_display_id=f"{unit}.{index}",
            source_locator=meta.get("task_title"), authority_task_title=meta.get("task_title"),
            candidate_solution_title=meta.get("solution_title"), source_sha256=sha256_bytes(source_part.encode()),
            target_sha256=sha256_bytes(target_part.encode()), authority_solution_status="source_supplied" if index in solution_indices else "source_absent",
            has_authority_solution=index in solution_indices, source_solution_checked=True,
            hint_present=bool(str(meta.get("hint_field") or "").strip()), hint_source_sha256=meta.get("expanded_hint_sha256"),
            graded=point is not None, point_value=point, unit_kind="exercise", translation_state=state,
        ))
    for index in solution_indices:
        meta = exercise_meta[index]
        exercise_id = f"{worksheet_id}-e{index:03d}"
        records.append(base_record(f"{exercise_id}-solution", "unit", checkpoint, **common, order=1, parent_id=exercise_id, path=bindings[f"solution{index}_target"]["path"], reader_anchor=f"unit-{tag}-exercise-{index:03d}-solution", source_local_id=f"worksheet{tag}:exercise:{index}:solution", source_locator=meta.get("solution_title"), source_sha256=bindings[f"solution{index}_source"]["sha256"], target_sha256=bindings[f"solution{index}_target"]["sha256"], pageid=meta.get("pageid"), revid=meta.get("revid"), unit_kind="source_supplied_solution", solution_provenance="official_source_supplied", translation_state=state))

    asset_ids: list[str] = []
    rights_ids: list[str] = []
    for index, asset in enumerate(preflight.get("media", {}).get("assets", []), 1):
        asset_id = f"o011-asset-file-u{tag}-{slug(asset['filename'])}"
        rights_id = f"o011-rights-media-u{tag}-{index:02d}"
        bound = bindings[f"media:{asset['filename']}"]
        occurrence_surfaces = [str(item.get("surface", "")) for item in asset.get("occurrences", [])]
        parent_id = lecture_id if any(value.startswith("lecture") for value in occurrence_surfaces) else worksheet_id
        rights_ids.append(rights_id); asset_ids.append(asset_id)
        records.append(base_record(rights_id, "rights", checkpoint, source_local_id=f"Commons pageid:{asset.get('commons_pageid')}/revid:{asset.get('commons_lastrevid')}", component_scope=bound["path"], evidence_path=bindings["media_receipt"]["path"], evidence_sha256=bindings["media_receipt"]["sha256"], attribution=asset.get("artist_text"), credit=asset.get("credit_text"), license=asset.get("license"), license_url=asset.get("license_url"), redistribution_permitted=True, release_asset=True, rights_status="admitted_component_license"))
        records.append(base_record(asset_id, "asset", checkpoint, parent_id=parent_id, order=index, path=bound["path"], source_local_id=f"File:{asset['filename']}", source_locator=asset.get("description_url"), source_sha256=bound["sha256"], expected_bytes=bound["bytes"], binary_present=True, mime=asset.get("mime"), commons_pageid=asset.get("commons_pageid"), commons_lastrevid=asset.get("commons_lastrevid"), rights_component_id=rights_id, occurrence_surfaces=occurrence_surfaces))

    artifact_specs = [
        (f"o011-artifact-u{tag}-l{tag}-source-tex", "lecture_source", lecture_id, "frozen_authority_tex_fragment", "German", "de-DE", None),
        (f"o011-artifact-u{tag}-l{tag}-tex", "lecture_target", lecture_id, "translated_tex_fragment", "Indonesian", "id-ID", bindings["lecture_source"]["sha256"]),
        (f"o011-artifact-u{tag}-w{tag}-source-tex", "worksheet_source", worksheet_id, "frozen_authority_tex_fragment", "German", "de-DE", None),
        (f"o011-artifact-u{tag}-w{tag}-tex", "worksheet_target", worksheet_id, "translated_tex_fragment", "Indonesian", "id-ID", bindings["worksheet_source"]["sha256"]),
    ]
    for index in solution_indices:
        solution_id = f"{worksheet_id}-e{index:03d}-solution"
        artifact_specs.extend([
            (f"o011-artifact-u{tag}-w{tag}-e{index:03d}-solution-source-tex", f"solution{index}_source", solution_id, "frozen_authority_tex_fragment", "German", "de-DE", None),
            (f"o011-artifact-u{tag}-w{tag}-e{index:03d}-solution-tex", f"solution{index}_target", solution_id, "translated_tex_fragment", "Indonesian", "id-ID", bindings[f"solution{index}_source"]["sha256"]),
        ])
    for artifact_id, key, parent_id, kind, language, locale, source_hash in artifact_specs:
        add_artifact(records, checkpoint, artifact_id, bindings[key], parent_id, kind, language=language, locale=locale, source_sha256=source_hash, translation_state="source_frozen" if language == "German" else state)
        add_relation(records, checkpoint, f"o011-rel-{artifact_id}-represents-target", "represents" if language == "Indonesian" else "evidences", artifact_id, parent_id)

    evidence_keys = ["preflight", "solution_closure", "lecture_receipt", "worksheet_receipt", "media_receipt"] + [f"solution{index}_receipt" for index in solution_indices] + [key for key in bindings if key.startswith("correction_manifest:")]
    for position, key in enumerate(evidence_keys, 1):
        artifact_id = f"o011-artifact-u{tag}-evidence-{position:02d}"
        add_artifact(records, checkpoint, artifact_id, bindings[key], unit_id, "bounded_qa_or_correction_receipt", translation_state=state)
        qa_id = f"o011-qa-unit{tag}-evidence-{position:02d}"
        records.append(base_record(qa_id, "qa_event", checkpoint, parent_id=unit_id, target_id=unit_id, receipt_path=bindings[key]["path"], evidence_sha256=bindings[key]["sha256"], result="pass", qa_kind="bounded_source_translation_math_media_evidence", artifact_id=artifact_id, translation_state=state))
        add_relation(records, checkpoint, f"o011-rel-{artifact_id}-evidences-target", "evidences", artifact_id, unit_id)
        add_relation(records, checkpoint, f"o011-rel-{qa_id}-evidences-target", "evidences", qa_id, unit_id)

    previous_id = f"o011-brenner-u{unit - 1:02d}"
    add_relation(records, checkpoint, f"o011-rel-u{unit - 1:02d}-precedes-u{tag}", "precedes", previous_id, unit_id)
    add_relation(records, checkpoint, f"o011-rel-u{tag}-has-part-l{tag}", "has_part", unit_id, lecture_id)
    add_relation(records, checkpoint, f"o011-rel-u{tag}-has-part-w{tag}", "has_part", unit_id, worksheet_id)
    for prefix, parent_id, count in ((f"l{tag}-s", lecture_id, structure["lecture_section_count"]), (f"w{tag}-s", worksheet_id, structure["worksheet_section_count"])):
        for index in range(1, count + 1):
            child_id = f"{unit_id}-{prefix}{index:02d}"
            add_relation(records, checkpoint, f"o011-rel-u{tag}-{prefix}{index:02d}-has-part", "has_part", parent_id, child_id)
            if index > 1:
                add_relation(records, checkpoint, f"o011-rel-u{tag}-{prefix}{index - 1:02d}-precedes-{index:02d}", "precedes", f"{unit_id}-{prefix}{index - 1:02d}", child_id)
    for index in range(1, structure["worksheet_exercise_count"] + 1):
        exercise_id = f"{worksheet_id}-e{index:03d}"
        add_relation(records, checkpoint, f"o011-rel-u{tag}-w{tag}-has-part-e{index:03d}", "has_part", worksheet_id, exercise_id)
        if index > 1:
            add_relation(records, checkpoint, f"o011-rel-u{tag}-w{tag}-e{index - 1:03d}-precedes-e{index:03d}", "precedes", f"{worksheet_id}-e{index - 1:03d}", exercise_id)
        if index in solution_indices:
            solution_id = f"{exercise_id}-solution"
            add_relation(records, checkpoint, f"o011-rel-u{tag}-w{tag}-e{index:03d}-has-solution", "has_part", exercise_id, solution_id)
            add_relation(records, checkpoint, f"o011-rel-u{tag}-w{tag}-e{index:03d}-solution-solves", "solves", solution_id, exercise_id)
    for rights_id, asset_id in zip(rights_ids, asset_ids):
        add_relation(records, checkpoint, f"o011-rel-{rights_id}-governs-asset", "governs", rights_id, asset_id)
        asset = next(record for record in records if record["id"] == asset_id)
        add_relation(records, checkpoint, f"o011-rel-{asset_id}-used-by-parent", "used_by", asset_id, str(asset["parent_id"]))
    return records


def exam_translation_receipt(root: Path, form: int, kind: str) -> Path:
    tag = f"{form:02d}"
    primary = root / f"qa/exams/EXAM{tag}_{kind.upper()}_TRANSLATION_QA.json"
    if primary.is_file():
        return primary
    if kind == "learner":
        fallback = root / f"qa/exam-{tag}/LEARNER_TRANSLATION_QA.json"
        if fallback.is_file():
            return fallback
    raise RuntimeError(f"missing Exam {form} {kind} translation QA")


def prepare_exams(root: Path, inputs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    authority_path = root / "qa/exams/EXAM_BANK_AUTHORITY.json"
    occurrence_path = root / "authority/exams/EXAM_OCCURRENCE_MAP.json"
    assert_file(authority_path, "exam authority receipt")
    assert_file(occurrence_path, "exam occurrence map")
    authority = load_json(authority_path)
    occurrence_rows = load_json(occurrence_path)
    if not isinstance(occurrence_rows, list):
        raise RuntimeError("exam occurrence map is not a JSON array")
    census = {
        "forms": authority.get("forms"), "nominal_slots": authority.get("nominal_template_slots"),
        "actual_occurrences": authority.get("actual_problem_occurrences"), "placeholder_slots": authority.get("placeholder_slots"),
        "unique_semantic_tasks": authority.get("unique_semantic_tasks"), "source_supplied_solutions": authority.get("source_solution_occurrences"),
        "source_missing_solutions": authority.get("missing_solution_occurrences"),
    }
    if census != EXPECTED_EXAM_CENSUS or len(occurrence_rows) != EXPECTED_EXAM_CENSUS["actual_occurrences"]:
        raise RuntimeError(f"exam authority census changed: {census!r}")
    occurrence_binding = binding(occurrence_path, root)
    if authority.get("occurrence_map") != occurrence_binding:
        raise RuntimeError("exam authority receipt has a stale occurrence-map binding")
    inputs["exam:authority"] = binding(authority_path, root)
    inputs["exam:occurrence_map"] = occurrence_binding
    rows_by_form: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in occurrence_rows:
        rows_by_form[int(row["form"])].append(row)
    expansion_by_pair = {(int(item["form"]), str(item["kind"])): item for item in authority.get("expansions", [])}
    form_contexts: list[dict[str, Any]] = []
    recomputed_rows: list[dict[str, Any]] = []
    for form in range(1, 11):
        tag = f"{form:02d}"
        paths = {
            "learner_source": root / f"authority/exams/expanded/exam{tag}_learner_source.de.tex",
            "solutions_source": root / f"authority/exams/expanded/exam{tag}_solutions_source.de.tex",
            "learner_target": root / f"source/exams/exam-{tag}/exam{tag}_learner.id.tex",
            "solutions_target": root / f"source/exams/exam-{tag}/exam{tag}_solutions.id.tex",
            "learner_receipt": exam_translation_receipt(root, form, "learner"),
            "solutions_receipt": exam_translation_receipt(root, form, "solutions"),
            "solutions_bounded": root / f"qa/exams/EXAM{tag}_SOLUTIONS_BOUNDED_QA.json",
            "learner_sanitize": root / f"qa/exams/EXAM{tag}_LEARNER_SANITIZE.json",
            "solutions_sanitize": root / f"qa/exams/EXAM{tag}_SOLUTIONS_SANITIZE.json",
        }
        for key, path in paths.items():
            assert_file(path, f"Exam {form} {key}")
        bindings = {key: binding(path, root) for key, path in sorted(paths.items())}
        for kind in ("learner", "solutions"):
            expansion = expansion_by_pair.get((form, kind))
            if not isinstance(expansion, dict) or expansion.get("sanitized_source") != bindings[f"{kind}_source"]:
                raise RuntimeError(f"Exam {form} frozen {kind} source identity changed")
            receipt = load_json(paths[f"{kind}_receipt"])
            assert_passing_math_receipt(receipt, bindings[f"{kind}_receipt"]["path"])
            assert_json_binds(receipt, bindings[f"{kind}_source"], f"Exam {form} {kind} translation QA")
            assert_json_binds(receipt, bindings[f"{kind}_target"], f"Exam {form} {kind} translation QA")
        bounded = load_json(paths["solutions_bounded"])
        if bounded.get("status") != "pass":
            raise RuntimeError(f"Exam {form} bounded solution QA is not passing")
        for key in ("solutions_source", "solutions_target"):
            assert_json_binds(bounded, bindings[key], f"Exam {form} bounded solution QA")

        learner_source_text = paths["learner_source"].read_text(encoding="utf-8")
        learner_target_text = paths["learner_target"].read_text(encoding="utf-8")
        solutions_source_text = paths["solutions_source"].read_text(encoding="utf-8")
        solutions_target_text = paths["solutions_target"].read_text(encoding="utf-8")
        for text, label in ((learner_source_text, "learner source"), (learner_target_text, "learner target"), (solutions_source_text, "solutions source"), (solutions_target_text, "solutions target")):
            if not balanced_braces(text) or "\ufffd" in text:
                raise RuntimeError(f"Exam {form} invalid TeX/UTF-8 surface: {label}")
        source_learner_calls = macro_calls(learner_source_text, ("inputaufgabegibtloesung", "inputaufgabe"), 2)
        target_learner_calls = macro_calls(learner_target_text, ("inputaufgabegibtloesung", "inputaufgabe"), 2)
        source_solution_calls = macro_calls(solutions_source_text, ("inputaufgabeklausurloesung",), 3)
        target_solution_calls = macro_calls(solutions_target_text, ("inputaufgabeklausurloesung",), 3)
        nominal = int(next(item["nominal_slots"] for item in authority["per_form_census"] if int(item["form"]) == form))
        if not all(len(values) == nominal for values in (source_learner_calls, target_learner_calls, source_solution_calls, target_solution_calls)):
            raise RuntimeError(f"Exam {form} nominal slot topology changed")
        map_rows = sorted(rows_by_form[form], key=lambda row: int(row["slot"]))
        actual_index = 0
        slot_rows: list[dict[str, Any]] = []
        for slot, (sl, tl, ss, ts) in enumerate(zip(source_learner_calls, target_learner_calls, source_solution_calls, target_solution_calls), 1):
            source_points, source_prompt = sl["args"]
            target_points, target_prompt = tl["args"]
            ss_points, ss_prompt, ss_solution = ss["args"]
            ts_points, ts_prompt, ts_solution = ts["args"]
            # The official Exam 9 solution form uses the literal continuation
            # marker ``weiter`` at one slot while its learner form carries the
            # numeric point decomposition.  Preserve both official surfaces;
            # only source-to-target equality is required within each form.
            if source_points.strip() != target_points.strip() or ss_points.strip() != ts_points.strip():
                raise RuntimeError(f"Exam {form} slot {slot} point sequence changed")
            if ss_prompt != source_prompt or ts_prompt != target_prompt:
                raise RuntimeError(f"Exam {form} slot {slot} solution-form prompt is not exact learner wording")
            actual = bool(source_prompt.strip())
            if actual != bool(target_prompt.strip()):
                raise RuntimeError(f"Exam {form} slot {slot} learner occurrence topology changed")
            if actual:
                row = map_rows[actual_index]
                actual_index += 1
                expected_row = {
                    "form": form, "slot": slot, "occurrence": actual_index,
                    "learner_macro": sl["macro"], "point_marker": source_points.strip(),
                    "rendered_task_bytes": len(source_prompt.encode("utf-8")),
                    "rendered_task_sha256": sha256_bytes(source_prompt.encode("utf-8")),
                    "source_solution_page_present": sl["macro"] == "inputaufgabegibtloesung",
                    "solution_presence_evidence": "official rendered learner macro " + sl["macro"],
                }
                if row != expected_row:
                    raise RuntimeError(f"Exam {form} slot {slot} occurrence-map source identity changed")
                supplied = bool(row["source_solution_page_present"])
                if bool(ss_solution.strip()) != supplied or bool(ts_solution.strip()) != supplied:
                    raise RuntimeError(f"Exam {form} slot {slot} source-solution presence topology changed")
                recomputed_rows.append(expected_row)
                slot_rows.append({"slot": slot, "actual": True, "occurrence": actual_index, "map": row, "source_prompt": source_prompt, "target_prompt": target_prompt, "source_solution": ss_solution, "target_solution": ts_solution})
            else:
                if any(value.strip() for value in (ss_prompt, ts_prompt, ss_solution, ts_solution)):
                    raise RuntimeError(f"Exam {form} slot {slot} placeholder topology changed")
                slot_rows.append({"slot": slot, "actual": False, "points": source_points.strip()})
        if actual_index != len(map_rows):
            raise RuntimeError(f"Exam {form} actual occurrence count changed")
        for key, bound in bindings.items():
            inputs[f"exam{tag}:{key}"] = bound
        form_contexts.append({"form": form, "tag": tag, "paths": paths, "bindings": bindings, "slots": slot_rows, "nominal": nominal})
    if recomputed_rows != occurrence_rows:
        raise RuntimeError("recomputed exam occurrence map differs from frozen canonical map")
    if len({row["rendered_task_sha256"] for row in recomputed_rows}) != EXPECTED_EXAM_CENSUS["unique_semantic_tasks"]:
        raise RuntimeError("exam semantic-task hash census changed")
    return {"authority": authority, "occurrence_rows": occurrence_rows, "forms": form_contexts, "census": census, "bindings": {"authority": inputs["exam:authority"], "occurrence_map": inputs["exam:occurrence_map"]}}


def make_exam_records(context: dict[str, Any], checkpoint: str, state: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    bank_id = "o011-brenner-exam-bank"
    authority = context["authority"]
    records.append(base_record(bank_id, "unit", checkpoint, order=30, parent_id=COURSE_ID, edition_id=EDITION_ID, resource_id=RESOURCE_ID, rights_component_id=TEXT_RIGHTS_ID, language="Indonesian", locale="id-ID", path="source/exams", reader_anchor="official-exam-bank", source_local_id=authority["official_index"], source_locator=authority["official_index"], source_sha256=authority["revision_set_sha256"], target_sha256=sha256_bytes(b"".join(form["paths"]["learner_target"].read_bytes() + form["paths"]["solutions_target"].read_bytes() for form in context["forms"])), unit_kind="official_exam_bank", actual_problem_occurrences=123, nominal_slots=147, placeholder_slots=24, source_supplied_solution_occurrences=117, source_missing_solution_occurrences=6, unique_semantic_tasks=119, translation_state=state))
    add_relation(records, checkpoint, "o011-rel-u29-precedes-exam-bank", "precedes", "o011-brenner-u29", bank_id)
    semantic_first: dict[str, tuple[int, int, int, str, str]] = {}
    for form in context["forms"]:
        for slot in form["slots"]:
            if slot["actual"]:
                row = slot["map"]
                semantic_first.setdefault(str(row["rendered_task_sha256"]), (form["form"], slot["slot"], slot["occurrence"], slot["source_prompt"], slot["target_prompt"]))
    for digest in sorted(semantic_first):
        form, slot, occurrence, source_prompt, target_prompt = semantic_first[digest]
        semantic_id = f"o011-exam-semantic-{digest}"
        records.append(base_record(semantic_id, "unit", checkpoint, order=None, parent_id=bank_id, edition_id=EDITION_ID, resource_id=RESOURCE_ID, rights_component_id=TEXT_RIGHTS_ID, language="Indonesian", locale="id-ID", source_local_id=f"rendered-task-sha256:{digest}", source_sha256=digest, target_sha256=sha256_bytes(target_prompt.encode("utf-8")), first_occurrence={"form": form, "slot": slot, "occurrence": occurrence}, unit_kind="semantic_exam_problem", occurrence_count=sum(1 for row in context["occurrence_rows"] if row["rendered_task_sha256"] == digest), translation_state=state))
    previous_form_id: str | None = None
    for form in context["forms"]:
        number = int(form["form"]); tag = str(form["tag"]); bindings = form["bindings"]
        form_id = f"o011-exam-f{tag}"
        learner_id = f"{form_id}-learner"
        solutions_id = f"{form_id}-solutions"
        form_source_hash = sha256_bytes(form["paths"]["learner_source"].read_bytes() + form["paths"]["solutions_source"].read_bytes())
        form_target_hash = sha256_bytes(form["paths"]["learner_target"].read_bytes() + form["paths"]["solutions_target"].read_bytes())
        actual_count = sum(1 for slot in form["slots"] if slot["actual"])
        supplied_count = sum(1 for slot in form["slots"] if slot["actual"] and slot["map"]["source_solution_page_present"])
        records.append(base_record(form_id, "unit", checkpoint, order=number, parent_id=bank_id, edition_id=EDITION_ID, resource_id=RESOURCE_ID, rights_component_id=TEXT_RIGHTS_ID, language="Indonesian", locale="id-ID", path=f"source/exams/exam-{tag}", reader_anchor=f"exam-{tag}", source_local_id=f"official-exam-form-{number}", source_locator=f"Kurs:Differentialgeometrie/{number}/Klausur", source_sha256=form_source_hash, target_sha256=form_target_hash, unit_kind="official_exam_form", nominal_slots=form["nominal"], actual_occurrences=actual_count, placeholder_slots=form["nominal"] - actual_count, source_supplied_solutions=supplied_count, source_missing_solutions=actual_count - supplied_count, translation_state=state))
        records.append(base_record(learner_id, "unit", checkpoint, order=1, parent_id=form_id, edition_id=EDITION_ID, resource_id=RESOURCE_ID, rights_component_id=TEXT_RIGHTS_ID, language="Indonesian", locale="id-ID", path=bindings["learner_target"]["path"], reader_anchor=f"exam-{tag}-learner", source_local_id=f"exam{tag}:learner", source_sha256=bindings["learner_source"]["sha256"], target_sha256=bindings["learner_target"]["sha256"], unit_kind="official_exam_learner_form", translation_state=state))
        records.append(base_record(solutions_id, "unit", checkpoint, order=2, parent_id=form_id, edition_id=EDITION_ID, resource_id=RESOURCE_ID, rights_component_id=TEXT_RIGHTS_ID, language="Indonesian", locale="id-ID", path=bindings["solutions_target"]["path"], reader_anchor=f"exam-{tag}-official-solutions", source_local_id=f"exam{tag}:solutions", source_sha256=bindings["solutions_source"]["sha256"], target_sha256=bindings["solutions_target"]["sha256"], unit_kind="official_exam_solution_form", solution_provenance="official_source_supplied_only_with_source_missing_occurrences_preserved", translation_state=state))
        add_relation(records, checkpoint, f"o011-rel-exam-f{tag}-has-learner", "has_part", form_id, learner_id)
        add_relation(records, checkpoint, f"o011-rel-exam-f{tag}-has-solutions", "has_part", form_id, solutions_id)
        if previous_form_id:
            add_relation(records, checkpoint, f"o011-rel-{previous_form_id.removeprefix('o011-')}-precedes-f{tag}", "precedes", previous_form_id, form_id)
        previous_form_id = form_id
        for slot in form["slots"]:
            slot_number = int(slot["slot"])
            slot_id = f"{form_id}-slot-{slot_number:03d}"
            if not slot["actual"]:
                records.append(base_record(slot_id, "unit", checkpoint, order=slot_number, parent_id=learner_id, edition_id=EDITION_ID, resource_id=RESOURCE_ID, rights_component_id=TEXT_RIGHTS_ID, language="Indonesian", locale="id-ID", path=f"{bindings['learner_target']['path']}#slot-{slot_number}", reader_anchor=f"exam-{tag}-slot-{slot_number:03d}", source_local_id=f"exam{tag}:slot:{slot_number}", unit_kind="exam_placeholder_slot", point_marker=slot["points"], actual_problem=False, authority_solution_status="not_applicable", translation_state=state))
                add_relation(records, checkpoint, f"o011-rel-exam-f{tag}-learner-has-slot-{slot_number:03d}", "has_part", learner_id, slot_id)
                continue
            row = slot["map"]
            digest = str(row["rendered_task_sha256"])
            semantic_id = f"o011-exam-semantic-{digest}"
            supplied = bool(row["source_solution_page_present"])
            records.append(base_record(slot_id, "unit", checkpoint, order=slot_number, parent_id=learner_id, edition_id=EDITION_ID, resource_id=RESOURCE_ID, rights_component_id=TEXT_RIGHTS_ID, language="Indonesian", locale="id-ID", path=f"{bindings['learner_target']['path']}#slot-{slot_number}", reader_anchor=f"exam-{tag}-problem-{slot['occurrence']:03d}", source_local_id=f"exam{tag}:slot:{slot_number}:occurrence:{slot['occurrence']}", source_display_id=f"exam-{number}.{slot['occurrence']}", source_sha256=digest, target_sha256=sha256_bytes(slot["target_prompt"].encode("utf-8")), semantic_problem_id=semantic_id, occurrence_index=slot["occurrence"], point_marker=row["point_marker"], actual_problem=True, learner_macro=row["learner_macro"], authority_solution_status="source_supplied" if supplied else "source_missing", has_authority_solution=supplied, source_solution_checked=True, unit_kind="exam_problem_occurrence", translation_state=state))
            add_relation(records, checkpoint, f"o011-rel-exam-f{tag}-learner-has-slot-{slot_number:03d}", "has_part", learner_id, slot_id)
            add_relation(records, checkpoint, f"o011-rel-exam-f{tag}-slot-{slot_number:03d}-occurrence-of", "occurrence_of", slot_id, semantic_id)
            if supplied:
                solution_id = f"{slot_id}-source-solution"
                records.append(base_record(solution_id, "unit", checkpoint, order=slot_number, parent_id=solutions_id, edition_id=EDITION_ID, resource_id=RESOURCE_ID, rights_component_id=TEXT_RIGHTS_ID, language="Indonesian", locale="id-ID", path=f"{bindings['solutions_target']['path']}#slot-{slot_number}", reader_anchor=f"exam-{tag}-official-solution-{slot['occurrence']:03d}", source_local_id=f"exam{tag}:slot:{slot_number}:official-solution", source_sha256=sha256_bytes(slot["source_solution"].encode("utf-8")), target_sha256=sha256_bytes(slot["target_solution"].encode("utf-8")), semantic_problem_id=semantic_id, occurrence_id=slot_id, unit_kind="source_supplied_exam_solution", solution_provenance="official_source_supplied", translation_state=state))
                add_relation(records, checkpoint, f"o011-rel-exam-f{tag}-solutions-has-slot-{slot_number:03d}", "has_part", solutions_id, solution_id)
                add_relation(records, checkpoint, f"o011-rel-exam-f{tag}-slot-{slot_number:03d}-source-solution-solves", "solves", solution_id, slot_id)
                add_relation(records, checkpoint, f"o011-rel-exam-f{tag}-slot-{slot_number:03d}-source-solution-semantic", "solves", solution_id, semantic_id)

        artifact_specs = [
            (f"o011-artifact-exam-f{tag}-learner-source", "learner_source", learner_id, "frozen_official_exam_learner_tex", "German", "de-DE", None),
            (f"o011-artifact-exam-f{tag}-learner-target", "learner_target", learner_id, "translated_official_exam_learner_tex", "Indonesian", "id-ID", bindings["learner_source"]["sha256"]),
            (f"o011-artifact-exam-f{tag}-solutions-source", "solutions_source", solutions_id, "frozen_official_exam_solution_tex", "German", "de-DE", None),
            (f"o011-artifact-exam-f{tag}-solutions-target", "solutions_target", solutions_id, "translated_official_exam_solution_tex", "Indonesian", "id-ID", bindings["solutions_source"]["sha256"]),
        ]
        for artifact_id, key, parent_id, kind, language, locale, source_hash in artifact_specs:
            add_artifact(records, checkpoint, artifact_id, bindings[key], parent_id, kind, language=language, locale=locale, source_sha256=source_hash, translation_state="source_frozen" if language == "German" else state)
            add_relation(records, checkpoint, f"o011-rel-{artifact_id}-represents-target", "represents" if language == "Indonesian" else "evidences", artifact_id, parent_id)
        for position, key in enumerate(("learner_receipt", "solutions_receipt", "solutions_bounded", "learner_sanitize", "solutions_sanitize"), 1):
            artifact_id = f"o011-artifact-exam-f{tag}-evidence-{position:02d}"
            add_artifact(records, checkpoint, artifact_id, bindings[key], form_id, "exam_translation_topology_or_authority_receipt", translation_state=state)
            qa_id = f"o011-qa-exam-f{tag}-evidence-{position:02d}"
            records.append(base_record(qa_id, "qa_event", checkpoint, parent_id=form_id, target_id=form_id, receipt_path=bindings[key]["path"], evidence_sha256=bindings[key]["sha256"], result="pass", qa_kind="exam_source_translation_math_prompt_solution_topology", artifact_id=artifact_id, translation_state=state))
            add_relation(records, checkpoint, f"o011-rel-{artifact_id}-evidences-target", "evidences", artifact_id, form_id)
            add_relation(records, checkpoint, f"o011-rel-{qa_id}-evidences-target", "evidences", qa_id, form_id)
    authority_bound = context["bindings"]["authority"]
    map_bound = context["bindings"]["occurrence_map"]
    for artifact_id, bound, kind in (("o011-artifact-exam-bank-authority", authority_bound, "frozen_exam_authority_receipt"), ("o011-artifact-exam-occurrence-map", map_bound, "canonical_exam_occurrence_map")):
        add_artifact(records, checkpoint, artifact_id, bound, bank_id, kind, translation_state="source_frozen")
        add_relation(records, checkpoint, f"o011-rel-{artifact_id}-evidences-target", "evidences", artifact_id, bank_id)
    return records


def prepare_original_repairs(root: Path, exam_context: dict[str, Any], inputs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    qa_path = root / "qa/exams/ORIGINAL_MISSING_SOLUTIONS_QA.json"
    target_path = root / "source/exams/original-repairs/missing-exam-solutions.id.tex"
    license_path = root / "source/exams/original-repairs/LICENSE.md"
    for path, label in ((qa_path, "original exam-repair QA"), (target_path, "original exam-repair solutions"), (license_path, "original exam-repair license")):
        assert_file(path, label)
    qa = load_json(qa_path)
    bindings = {"qa": binding(qa_path, root), "target": binding(target_path, root), "license": binding(license_path, root)}
    if qa.get("status") != "six_original_missing_solution_repairs_complete_and_smoke_build_passed" or qa.get("license") != "CC BY-SA 4.0":
        raise RuntimeError("original missing-exam repair QA is not admitted")
    assert_json_binds(qa, bindings["target"], "original repair QA")
    assert_json_binds(qa, bindings["license"], "original repair QA")
    rows = list(qa.get("occurrence_bindings", []))
    missing = [row for row in exam_context["occurrence_rows"] if not row["source_solution_page_present"]]
    if len(rows) != EXPECTED_ORIGINAL_REPAIRS or len(missing) != EXPECTED_ORIGINAL_REPAIRS:
        raise RuntimeError("original missing-exam repair census changed")
    missing_by_key = {(int(row["form"]), int(row["slot"]), int(row["occurrence"])): row for row in missing}
    text = target_path.read_text(encoding="utf-8")
    labels = re.findall(r"\\label\{(o011-exam\d\d-orig-sol-\d\d)\}", text)
    if len(labels) != EXPECTED_ORIGINAL_REPAIRS or len(set(labels)) != EXPECTED_ORIGINAL_REPAIRS:
        raise RuntimeError("original exam-repair label topology changed")
    starts = [match.start() for match in re.finditer(r"\\subsection\*\{Ujian ", text)]
    blocks = [text[start:starts[index + 1] if index + 1 < len(starts) else len(text)] for index, start in enumerate(starts)]
    block_by_label: dict[str, str] = {}
    for block in blocks:
        match = re.search(r"\\label\{([^}]+)\}", block)
        if match:
            block_by_label[match.group(1)] = block
    for row in rows:
        key = (int(row["form"]), int(row["slot"]), int(row["actual_occurrence"]))
        occurrence = missing_by_key.get(key)
        if occurrence is None or occurrence["rendered_task_sha256"] != row["source_rendered_task_sha256"] or str(occurrence["point_marker"]) != str(row["points"]):
            raise RuntimeError(f"stale original repair occurrence binding: {row.get('stable_id')}")
        label = str(row["stable_id"]).lower()
        if label not in block_by_label:
            raise RuntimeError(f"missing original repair reader anchor: {label}")
    for key, bound in bindings.items():
        inputs[f"original_repairs:{key}"] = bound
    return {"qa": qa, "bindings": bindings, "rows": rows, "blocks": block_by_label}


def make_original_repair_records(context: dict[str, Any], checkpoint: str, state: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    component_id = "o011-exam-original-missing-solutions"
    rights_id = "o011-rights-original-exam-repairs"
    bindings = context["bindings"]
    records.append(base_record(rights_id, "rights", checkpoint, source_local_id="CC-BY-SA-4.0-original-exam-repairs", component_scope=bindings["target"]["path"], evidence_path=bindings["license"]["path"], evidence_sha256=bindings["license"]["sha256"], attribution=MODEL_IDENTIFICATION + ", at the user's direction", license="CC BY-SA 4.0", license_url="https://creativecommons.org/licenses/by-sa/4.0/", redistribution_permitted=True, release_asset=True, rights_status="original_component_license"))
    records.append(base_record(component_id, "unit", checkpoint, order=1, parent_id="o011-brenner-exam-bank", language="Indonesian", locale="id-ID", rights_component_id=rights_id, path=bindings["target"]["path"], reader_anchor="o011-exam-original-repairs", source_local_id="six-frozen-source-missing-exam-occurrences", target_sha256=bindings["target"]["sha256"], source_sha256=None, unit_kind="separately_provenanced_original_exam_solution_repairs", solution_provenance="original_not_source_supplied", original_solution_count=6, translation_state=state))
    add_relation(records, checkpoint, "o011-rel-original-exam-repairs-follows-official-bank", "supplements", component_id, "o011-brenner-exam-bank")
    add_relation(records, checkpoint, "o011-rel-original-exam-repairs-rights-governs", "governs", rights_id, component_id)
    for order, row in enumerate(context["rows"], 1):
        record_id = str(row["stable_id"]).lower()
        form = int(row["form"]); slot = int(row["slot"]); occurrence = int(row["actual_occurrence"])
        occurrence_id = f"o011-exam-f{form:02d}-slot-{slot:03d}"
        semantic_id = f"o011-exam-semantic-{row['source_rendered_task_sha256']}"
        records.append(base_record(record_id, "unit", checkpoint, order=order, parent_id=component_id, language="Indonesian", locale="id-ID", rights_component_id=rights_id, path=f"{bindings['target']['path']}#{record_id}", reader_anchor=record_id, source_local_id=str(row["stable_id"]), source_sha256=None, target_sha256=sha256_bytes(context["blocks"][record_id].encode("utf-8")), occurrence_id=occurrence_id, semantic_problem_id=semantic_id, form=form, slot=slot, occurrence_index=occurrence, point_marker=str(row["points"]), authority_solution_status="source_missing", unit_kind="original_exam_solution_repair", solution_provenance="original_not_source_supplied", translation_state=state))
        add_relation(records, checkpoint, f"o011-rel-{record_id}-solves-occurrence", "solves", record_id, occurrence_id)
        add_relation(records, checkpoint, f"o011-rel-{record_id}-solves-semantic", "solves", record_id, semantic_id)
        add_relation(records, checkpoint, f"o011-rel-original-exam-repairs-has-{order:02d}", "has_part", component_id, record_id)
    for artifact_id, key, kind in (("o011-artifact-original-exam-repairs-tex", "target", "original_exam_solution_repairs_tex"), ("o011-artifact-original-exam-repairs-license", "license", "original_component_license"), ("o011-artifact-original-exam-repairs-qa", "qa", "original_solution_occurrence_and_smoke_qa")):
        add_artifact(records, checkpoint, artifact_id, bindings[key], component_id, kind, language="Indonesian" if key == "target" else None, locale="id-ID" if key == "target" else None, rights_id=rights_id, translation_state=state)
        add_relation(records, checkpoint, f"o011-rel-{artifact_id}-evidences-target", "evidences", artifact_id, component_id)
    records.append(base_record("o011-qa-original-exam-repairs", "qa_event", checkpoint, parent_id=component_id, target_id=component_id, receipt_path=bindings["qa"]["path"], evidence_sha256=bindings["qa"]["sha256"], result="pass", qa_kind="six_original_source_missing_exam_solution_repairs", artifact_id="o011-artifact-original-exam-repairs-qa", translation_state=state))
    add_relation(records, checkpoint, "o011-rel-qa-original-exam-repairs-evidences-target", "evidences", "o011-qa-original-exam-repairs", component_id)
    return records


def prepare_bridges(root: Path, inputs: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    specs = [
        ("lie", "lie-groups", "qa/bridges/lie-groups/BRIDGE_LIE_CONTENT_SMOKE_QA.json", "o011-bridge-lie", "o011-bl-"),
        ("de-rham", "de-rham", "qa/bridges/de-rham/BRIDGE_DE_RHAM_CONTENT_SMOKE_QA.json", "o011-bridge-de-rham", "o011-br-"),
    ]
    contexts: list[dict[str, Any]] = []
    for short, directory, qa_relative, component_id, prefix in specs:
        qa_path = root / qa_relative
        theory_path = root / f"source/bridges/{directory}/bridge-{'lie' if short == 'lie' else 'de-rham'}-theory.id.tex"
        assessment_path = root / f"source/bridges/{directory}/bridge-{'lie' if short == 'lie' else 'de-rham'}-assessment.id.tex"
        license_path = root / f"source/bridges/{directory}/LICENSE.md"
        for path, label in ((qa_path, "bridge QA"), (theory_path, "bridge theory"), (assessment_path, "bridge assessment"), (license_path, "bridge license")):
            assert_file(path, f"{short} {label}")
        qa = load_json(qa_path)
        bindings = {"qa": binding(qa_path, root), "theory": binding(theory_path, root), "assessment": binding(assessment_path, root), "license": binding(license_path, root)}
        if qa.get("component_id") != component_id or qa.get("status") != "complete_original_reader_content_and_smoke_build_passed" or qa.get("license") != "CC BY-SA 4.0":
            raise RuntimeError(f"{short} bridge QA is not admitted")
        for key in ("theory", "assessment", "license"):
            assert_json_binds(qa, bindings[key], f"{short} bridge QA")
        census = qa.get("census", {})
        expected = {"exercise_ids": 12, "exercise_hints": 12, "exercise_complete_solutions": 12, "mastery_problem_ids": 4, "mastery_complete_solutions": 4, "mastery_rubrics": 4, "mastery_alternate_parameter_sets": 4, "solution_bearing_items": 16}
        if any(census.get(key) != value for key, value in expected.items()):
            raise RuntimeError(f"{short} bridge item census changed")
        theory_text = theory_path.read_text(encoding="utf-8")
        assessment_text = assessment_path.read_text(encoding="utf-8")
        if not balanced_braces(theory_text) or not balanced_braces(assessment_text):
            raise RuntimeError(f"{short} bridge brace topology changed")
        item_pattern = re.compile(r"\\label\{(" + re.escape(prefix) + r"[em]\d\d)\}")
        item_matches = list(item_pattern.finditer(assessment_text))
        if len(item_matches) != 16 or len({match.group(1) for match in item_matches}) != 16:
            raise RuntimeError(f"{short} bridge stable item labels changed")
        blocks: dict[str, str] = {}
        for index, match in enumerate(item_matches):
            start = assessment_text.rfind("\\subsubsection", 0, match.start())
            end = assessment_text.rfind("\\subsubsection", 0, item_matches[index + 1].start()) if index + 1 < len(item_matches) else len(assessment_text)
            if index + 1 < len(item_matches):
                end = assessment_text.rfind("\\subsubsection", 0, item_matches[index + 1].start())
            blocks[match.group(1)] = assessment_text[start:end]
        labels = re.findall(r"\\label\{(o011-[a-z0-9-]+)\}", theory_text)
        if component_id not in labels or len(labels) != len(set(labels)):
            raise RuntimeError(f"{short} bridge theory reader anchors changed")
        for key, bound in bindings.items():
            inputs[f"bridge:{short}:{key}"] = bound
        contexts.append({"short": short, "directory": directory, "component_id": component_id, "prefix": prefix, "qa": qa, "bindings": bindings, "paths": {"qa": qa_path, "theory": theory_path, "assessment": assessment_path, "license": license_path}, "blocks": blocks, "theory_labels": labels})
    return contexts


def make_bridge_records(contexts: list[dict[str, Any]], checkpoint: str, state: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for order, context in enumerate(contexts, 1):
        short = context["short"]; component_id = context["component_id"]; qa = context["qa"]; bindings = context["bindings"]
        rights_id = f"o011-rights-original-bridge-{short}"
        theory_id = f"{component_id}-theory"
        assessment_id = f"{component_id}-assessment"
        records.append(base_record(rights_id, "rights", checkpoint, source_local_id=f"CC-BY-SA-4.0-original-bridge-{short}", component_scope=f"source/bridges/{context['directory']}", evidence_path=bindings["license"]["path"], evidence_sha256=bindings["license"]["sha256"], attribution=MODEL_IDENTIFICATION + ", at the user's direction", license="CC BY-SA 4.0", license_url="https://creativecommons.org/licenses/by-sa/4.0/", redistribution_permitted=True, release_asset=True, rights_status="original_component_license"))
        records.append(base_record(component_id, "unit", checkpoint, order=order + 31, parent_id=COURSE_ID, language="Indonesian", locale="id-ID", rights_component_id=rights_id, path=f"source/bridges/{context['directory']}", reader_anchor=component_id, source_local_id=component_id.upper(), source_sha256=None, target_sha256=sha256_bytes(context["paths"]["theory"].read_bytes() + context["paths"]["assessment"].read_bytes()), unit_kind="original_cc_by_sa_bridge", solution_provenance="original_not_source_supplied", provenance=qa["provenance"], internal_prerequisite_ids=list(qa["internal_prerequisites"]), exercise_count=12, mastery_problem_count=4, solution_bearing_item_count=16, translation_state=state))
        records.append(base_record(theory_id, "unit", checkpoint, order=1, parent_id=component_id, language="Indonesian", locale="id-ID", rights_component_id=rights_id, path=bindings["theory"]["path"], reader_anchor=component_id, source_local_id=f"{component_id}:theory", source_sha256=None, target_sha256=bindings["theory"]["sha256"], unit_kind="original_bridge_theory", provenance=qa["provenance"], translation_state=state))
        records.append(base_record(assessment_id, "unit", checkpoint, order=2, parent_id=component_id, language="Indonesian", locale="id-ID", rights_component_id=rights_id, path=bindings["assessment"]["path"], reader_anchor=f"{component_id}-assessment", source_local_id=f"{component_id}:assessment", source_sha256=None, target_sha256=bindings["assessment"]["sha256"], unit_kind="original_bridge_assessment", provenance=qa["provenance"], translation_state=state))
        add_relation(records, checkpoint, f"o011-rel-{component_id}-has-theory", "has_part", component_id, theory_id)
        add_relation(records, checkpoint, f"o011-rel-{component_id}-has-assessment", "has_part", component_id, assessment_id)
        add_relation(records, checkpoint, f"o011-rel-{rights_id}-governs-bridge", "governs", rights_id, component_id)
        for position, prerequisite in enumerate(qa["internal_prerequisites"], 1):
            add_relation(records, checkpoint, f"o011-rel-{component_id}-prerequisite-{position:02d}", "requires", component_id, prerequisite)
        item_ids = sorted(context["blocks"], key=lambda value: ("-m" in value, value))
        for item_order, item_id in enumerate(item_ids, 1):
            mastery = "-m" in item_id
            block = context["blocks"][item_id]
            has_hint = "\\paragraph{Petunjuk" in block
            has_solution = "\\paragraph{Solusi.}" in block
            has_rubric = "\\paragraph{Rubrik" in block
            has_alternate = "\\paragraph{Parameter alternatif.}" in block
            if not has_hint or not has_solution or (mastery and (not has_rubric or not has_alternate)):
                raise RuntimeError(f"incomplete original bridge item: {item_id}")
            records.append(base_record(item_id, "unit", checkpoint, order=item_order, parent_id=assessment_id, language="Indonesian", locale="id-ID", rights_component_id=rights_id, path=f"{bindings['assessment']['path']}#{item_id}", reader_anchor=item_id, source_local_id=item_id.upper(), source_sha256=None, target_sha256=sha256_bytes(block.encode("utf-8")), unit_kind="original_bridge_mastery_problem" if mastery else "original_bridge_exercise", solution_provenance="original_not_source_supplied", hint_present=True, complete_solution_present=True, rubric_present=has_rubric, alternate_parameters_present=has_alternate, translation_state=state))
            add_relation(records, checkpoint, f"o011-rel-{assessment_id}-has-{item_id.removeprefix('o011-')}", "has_part", assessment_id, item_id)
        theory_text = context["paths"]["theory"].read_text(encoding="utf-8")
        label_matches = list(re.finditer(r"\\label\{(o011-[a-z0-9-]+)\}", theory_text))
        for label_order, match in enumerate(label_matches, 1):
            label = match.group(1)
            if label == component_id:
                continue
            end = label_matches[label_order].start() if label_order < len(label_matches) else len(theory_text)
            part = theory_text[match.start():end]
            records.append(base_record(label, "segment", checkpoint, order=label_order, parent_id=theory_id, path=f"{bindings['theory']['path']}#{label}", reader_anchor=label, source_local_id=label.upper(), source_sha256=None, target_sha256=sha256_bytes(part.encode("utf-8")), segment_kind="original_bridge_reader_anchor", language="Indonesian", locale="id-ID", rights_component_id=rights_id, translation_state=state))
            add_relation(records, checkpoint, f"o011-rel-{theory_id}-has-{label.removeprefix('o011-')}", "has_part", theory_id, label)
        for artifact_id, key, kind in ((f"o011-artifact-bridge-{short}-theory", "theory", "original_bridge_theory_tex"), (f"o011-artifact-bridge-{short}-assessment", "assessment", "original_bridge_assessment_tex"), (f"o011-artifact-bridge-{short}-license", "license", "original_component_license"), (f"o011-artifact-bridge-{short}-qa", "qa", "bridge_content_and_smoke_qa")):
            add_artifact(records, checkpoint, artifact_id, bindings[key], component_id, kind, language="Indonesian" if key in ("theory", "assessment") else None, locale="id-ID" if key in ("theory", "assessment") else None, rights_id=rights_id, translation_state=state)
            add_relation(records, checkpoint, f"o011-rel-{artifact_id}-evidences-target", "evidences", artifact_id, component_id)
        qa_id = f"o011-qa-bridge-{short}"
        records.append(base_record(qa_id, "qa_event", checkpoint, parent_id=component_id, target_id=component_id, receipt_path=bindings["qa"]["path"], evidence_sha256=bindings["qa"]["sha256"], result="pass", qa_kind="original_bridge_content_solution_license_and_smoke_closure", artifact_id=f"o011-artifact-bridge-{short}-qa", translation_state=state))
        add_relation(records, checkpoint, f"o011-rel-{qa_id}-evidences-target", "evidences", qa_id, component_id)
    return records


def correction_record_id(correction_id: str) -> str:
    if re.fullmatch(r"O011-(?:CORR|TRANS|ACC)-\d{4}", correction_id):
        return "o011-corr-" + correction_id[-4:]
    return "o011-corr-declared-" + slug(correction_id)


def add_declared_corrections(root: Path, unit_contexts: list[dict[str, Any]], exam_context: dict[str, Any], records: list[dict[str, Any]], inputs: dict[str, dict[str, Any]], checkpoint: str, state: str) -> dict[str, int]:
    scope_targets: dict[str, tuple[str, dict[str, Any]]] = {}
    for context in unit_contexts:
        unit = context["unit"]; tag = context["tag"]; bindings = context["bindings"]
        _, lecture_id, worksheet_id = unit_ids(unit)
        scope_targets[bindings["lecture_target"]["path"]] = (lecture_id, bindings["lecture_target"])
        scope_targets[bindings["worksheet_target"]["path"]] = (worksheet_id, bindings["worksheet_target"])
        for index in EXPECTED_UNIT_CENSUS[unit]["solutions"]:
            solution_id = f"{worksheet_id}-e{index:03d}-solution"
            scope_targets[bindings[f"solution{index}_target"]["path"]] = (solution_id, bindings[f"solution{index}_target"])
    for context in exam_context["forms"]:
        tag = context["tag"]; bindings = context["bindings"]
        scope_targets[bindings["learner_target"]["path"]] = (f"o011-exam-f{tag}-learner", bindings["learner_target"])
        scope_targets[bindings["solutions_target"]["path"]] = (f"o011-exam-f{tag}-solutions", bindings["solutions_target"])

    manifest_paths = [path for context in unit_contexts for key, path in context["paths"].items() if key.startswith("correction_manifest:")]
    manifest_paths.extend(sorted((root / "qa/exams").glob("*TRANSLATION_DELTAS.json"), key=lambda item: item.name))
    seen: set[str] = set()
    source_corrections = 0
    for manifest_position, path in enumerate(sorted(set(manifest_paths), key=lambda item: item.as_posix()), 1):
        manifest = load_json(path)
        bound = binding(path, root)
        input_key = f"corrections:{manifest_position:02d}"
        inputs[input_key] = bound
        scope = manifest.get("scope")
        if not isinstance(scope, str) or scope not in scope_targets:
            if not manifest.get("corrections"):
                continue
            raise RuntimeError(f"unknown declared-correction scope: {scope!r}")
        target_id, target_binding = scope_targets[scope]
        artifact_id = f"o011-artifact-correction-manifest-{manifest_position:02d}"
        parent_id = target_id
        add_artifact(records, checkpoint, artifact_id, bound, parent_id, "declared_translation_or_source_correction_manifest", translation_state=state)
        add_relation(records, checkpoint, f"o011-rel-{artifact_id}-evidences-target", "evidences", artifact_id, target_id)
        for correction in manifest.get("corrections", []):
            correction_id = str(correction["correction_id"])
            if correction_id in seen:
                raise RuntimeError(f"duplicate declared correction identity: {correction_id}")
            seen.add(correction_id)
            record_id = correction_record_id(correction_id)
            change = str(correction.get("change", "Declared target delta"))
            source_correction = correction_id == "O011-CORR-0312" or correction_id == "O011-EXAM01-SOL-0002"
            if source_correction:
                source_corrections += 1
            kind = "source_correction" if source_correction else "accessibility_delta" if "-ACC-" in correction_id else "translation_only_delta"
            records.append(base_record(record_id, "correction", checkpoint, source_local_id=correction_id, severity="P1" if source_correction else "P2", description=change, anchor=correction.get("anchor"), disposition="Corrected or translated in the Indonesian target and verified against the frozen authority", correction_status="corrected_in_target", correction_kind=kind, source_correction=source_correction, upstream_report_disposition="deferred_until_full_corpus", target_ids=[target_id], target_bindings=[{**target_binding, "target_id": target_id}], correction_manifests=[bound], translation_state=state))
            add_relation(records, checkpoint, f"o011-rel-{record_id}-corrects-01", "corrects", record_id, target_id)
    return {"declared_corrections": len(seen), "source_corrections": source_corrections, "manifests": len(manifest_paths)}


def validate_records(baseline: list[dict[str, Any]], suffix: list[dict[str, Any]], schema: dict[str, Any]) -> dict[str, int]:
    suffix.sort(key=lambda item: str(item["id"]))
    all_records = baseline + suffix
    ids = [str(record["id"]) for record in all_records]
    duplicates = sorted(record_id for record_id, count in Counter(ids).items() if count > 1)
    if duplicates:
        raise RuntimeError("duplicate backend IDs: " + ", ".join(duplicates[:20]))
    all_ids = set(ids)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors: list[str] = []
    for record in all_records:
        errors.extend(f"{record['id']}: {error.message}" for error in validator.iter_errors(record))
    if errors:
        raise RuntimeError("JSON Schema validation failed: " + "; ".join(errors[:20]))
    for record in suffix:
        for key in REFERENCE_KEYS:
            value = record.get(key)
            if value is not None and str(value) not in all_ids:
                raise RuntimeError(f"unresolved {key} on {record['id']}: {value}")
        for key in REFERENCE_LIST_KEYS:
            for value in record.get(key, []) or []:
                if str(value) not in all_ids:
                    raise RuntimeError(f"unresolved {key} on {record['id']}: {value}")
    counts = Counter(str(record.get("entity_type")) for record in suffix)
    return {kind: counts.get(kind, 0) for kind in sorted(ENTITY_TYPES)}


def semantic_census(suffix: list[dict[str, Any]]) -> dict[str, int]:
    def count(kind: str) -> int:
        return sum(1 for record in suffix if record.get("unit_kind") == kind)
    return {
        "core_units_added": sum(1 for record in suffix if record.get("unit_kind") == "lecture_worksheet_pair"),
        "core_exercises_added": count("exercise"),
        "core_source_solutions_added": count("source_supplied_solution"),
        "exam_forms": count("official_exam_form"),
        "exam_nominal_slots": count("exam_problem_occurrence") + count("exam_placeholder_slot"),
        "exam_actual_occurrences": count("exam_problem_occurrence"),
        "exam_placeholder_slots": count("exam_placeholder_slot"),
        "exam_semantic_tasks": count("semantic_exam_problem"),
        "exam_source_supplied_solutions": count("source_supplied_exam_solution"),
        "original_exam_repairs": count("original_exam_solution_repair"),
        "bridges": count("original_cc_by_sa_bridge"),
        "bridge_exercises": count("original_bridge_exercise"),
        "bridge_mastery": count("original_bridge_mastery_problem"),
        "bridge_items": count("original_bridge_exercise") + count("original_bridge_mastery_problem"),
    }


def prepare_bundle(root: Path, checkpoint: str, state: str) -> dict[str, Any]:
    jsonl_prefix, csv_prefix, baseline = assert_prefix(root)
    inputs: dict[str, dict[str, Any]] = {"schema": binding(root / "backend/schema/o011-record-v1.schema.json", root)}
    unit_contexts = [prepare_unit(root, unit, inputs) for unit in UNITS]
    exam_context = prepare_exams(root, inputs)
    repair_context = prepare_original_repairs(root, exam_context, inputs)
    bridge_contexts = prepare_bridges(root, inputs)
    suffix: list[dict[str, Any]] = []
    for context in unit_contexts:
        suffix.extend(make_unit_records(context, checkpoint, state))
    suffix.extend(make_exam_records(exam_context, checkpoint, state))
    suffix.extend(make_original_repair_records(repair_context, checkpoint, state))
    suffix.extend(make_bridge_records(bridge_contexts, checkpoint, state))
    correction_census = add_declared_corrections(root, unit_contexts, exam_context, suffix, inputs, checkpoint, state)
    entity_counts = validate_records(baseline, suffix, load_json(root / "backend/schema/o011-record-v1.schema.json"))
    census = semantic_census(suffix)
    expected = {
        "core_units_added": 7, "core_exercises_added": 119, "core_source_solutions_added": 20,
        "exam_forms": 10, "exam_nominal_slots": 147, "exam_actual_occurrences": 123,
        "exam_placeholder_slots": 24, "exam_semantic_tasks": 119,
        "exam_source_supplied_solutions": 117, "original_exam_repairs": 6,
        "bridges": 2, "bridge_exercises": 24, "bridge_mastery": 8, "bridge_items": 32,
    }
    if census != expected:
        raise RuntimeError(f"complete-edition semantic census changed: {census!r}")
    if BASELINE_CORE_EXERCISES + census["core_exercises_added"] != FINAL_CORE_EXERCISES or BASELINE_CORE_SOURCE_SOLUTIONS + census["core_source_solutions_added"] != FINAL_CORE_SOURCE_SOLUTIONS:
        raise RuntimeError("complete Brenner core exercise/solution census changed")
    return {"jsonl_prefix": jsonl_prefix, "csv_prefix": csv_prefix, "baseline": baseline, "suffix": suffix, "inputs": dict(sorted(inputs.items())), "entity_counts": entity_counts, "semantic_census": census, "correction_census": correction_census, "unit_contexts": unit_contexts, "exam_context": exam_context}


def render_csv_suffix(suffix: list[dict[str, Any]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS, extrasaction="ignore", lineterminator="\r\n")
    for record in suffix:
        writer.writerow({field: record.get(field) for field in CSV_FIELDS})
    return stream.getvalue().encode("utf-8")


def make_manifest(root: Path, checkpoint: str, state: str, bundle: dict[str, Any], outputs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    combined_counts = Counter(str(record.get("entity_type")) for record in bundle["baseline"] + bundle["suffix"])
    return {
        "schema_version": 1,
        "workflow": WORKFLOW,
        "checkpoint": checkpoint,
        "translation_state": state,
        "generator": binding(root / "scripts/export_backend_complete.py", root),
        "verifier": binding(root / "scripts/verify_backend_complete.py", root),
        "documentation": binding(root / "backend/README.md", root),
        "baseline": {"record_count": BASELINE_RECORD_COUNT, "jsonl_bytes": BASELINE_JSONL_BYTES, "jsonl_sha256": BASELINE_JSONL_SHA256, "csv_lines_including_header": BASELINE_CSV_LINES, "csv_bytes": BASELINE_CSV_BYTES, "csv_sha256": BASELINE_CSV_SHA256, "published_unit22_prefix_preserved_byte_identically": True},
        "extension": {"record_count": len(bundle["suffix"]), "entity_counts": bundle["entity_counts"], "semantic_census": bundle["semantic_census"], "correction_census": bundle["correction_census"], "core_final": {"exercises": FINAL_CORE_EXERCISES, "source_supplied_solutions": FINAL_CORE_SOURCE_SOLUTIONS}, "exam_authority": EXPECTED_EXAM_CENSUS, "original_solution_bearing_items": {"exam_repairs": 6, "bridge_and_mastery": 32, "total": 38}, "solution_provenance_separated": True, "reader_anchor_fields_present": True},
        "combined": {"record_count": BASELINE_RECORD_COUNT + len(bundle["suffix"]), "entity_counts": {kind: combined_counts.get(kind, 0) for kind in sorted(ENTITY_TYPES)}},
        "inputs": bundle["inputs"],
        "outputs": outputs,
        "claims": {"all_ids_unique": True, "all_references_resolve": True, "json_schema_valid": True, "unit22_public_prefix_byte_identical": True, "csv_projection_exact": True, "source_identity_bindings_current": True, "hash_bound_translation_math_receipts_pass": True, "exam_occurrence_map_recomputed_exactly": True, "exam_learner_prompts_exact_in_solution_forms": True, "exam_source_solution_topology_exact": True, "original_solution_provenance_distinct": True, "component_media_and_rights_closed": True, "reader_anchors_stable": True},
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--translation-state", default=DEFAULT_TRANSLATION_STATE)
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    if args.translation_state not in {"translated", "structurally_verified", "mathematically_reviewed", "language_reviewed", "built", "visually_checked"}:
        raise RuntimeError("unsupported complete-edition translation state")
    root = args.root.resolve()
    bundle = prepare_bundle(root, args.checkpoint, args.translation_state)
    summary = {"status": "pass", "baseline_records": BASELINE_RECORD_COUNT, "added_records": len(bundle["suffix"]), "combined_records": BASELINE_RECORD_COUNT + len(bundle["suffix"]), "entity_counts": bundle["entity_counts"], "semantic_census": bundle["semantic_census"], "correction_census": bundle["correction_census"]}
    if args.check_only:
        summary["check_only"] = True
        print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
        return
    jsonl_path = root / "backend/records.jsonl"
    csv_path = root / "backend/records.csv"
    jsonl_path.write_bytes(bundle["jsonl_prefix"] + b"".join(canonical_json(record) for record in bundle["suffix"]))
    csv_path.write_bytes(bundle["csv_prefix"] + render_csv_suffix(bundle["suffix"]))
    outputs = {"records_jsonl": binding(jsonl_path, root), "records_csv": binding(csv_path, root)}
    manifest = make_manifest(root, args.checkpoint, args.translation_state, bundle, outputs)
    manifest_path = root / "backend/MANIFEST.json"
    manifest_path.write_bytes((json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    summary.update({"jsonl": outputs["records_jsonl"], "csv": outputs["records_csv"], "manifest": binding(manifest_path, root)})
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
