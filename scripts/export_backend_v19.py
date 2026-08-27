#!/usr/bin/env python3
"""Export the additive O011 Units 17--19 semantic backend extension.

The verified public Units 1--16 JSONL and CSV are immutable byte prefixes.
This generator appends deterministic records for Units 17--19 and admits the
cumulative Unit 19 HTML/PDF readers only when their complete QA closure is
present and current.  The v10 implementation is imported as an immutable
library for the already-tested per-unit record model; no earlier file is changed.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import export_backend_v10 as v10  # noqa: E402


BASELINE_RECORD_COUNT = 3208
BASELINE_JSONL_BYTES = 1966474
BASELINE_JSONL_SHA256 = "c42bac17822f949aa16ac0f87c7d0726526d020d46bab97f91d36e70f4b21983"
BASELINE_CSV_LINES = 3209
BASELINE_CSV_BYTES = 727631
BASELINE_CSV_SHA256 = "2ff324a750b01540fd3827684947877e807ac8402d09fc6ece1efdf14caeb312"
BASELINE_EXERCISE_COUNT = 342
BASELINE_SOURCE_SOLUTION_COUNT = 48
FINAL_EXERCISE_COUNT = 394
FINAL_SOURCE_SOLUTION_COUNT = 54
EXPECTED_UNIT_CENSUS: dict[int, dict[str, Any]] = {
    17: {
        "lecture_sections": 3,
        "worksheet_sections": 2,
        "exercises": 19,
        "practice": 13,
        "graded": 6,
        "points": 30,
        "solutions": [2, 4],
        "assets": 1,
    },
    18: {
        "lecture_sections": 3,
        "worksheet_sections": 2,
        "exercises": 21,
        "practice": 16,
        "graded": 5,
        "points": 19,
        "solutions": [8, 11, 13, 14],
        "assets": 2,
    },
    19: {
        "lecture_sections": 2,
        "worksheet_sections": 2,
        "exercises": 12,
        "practice": 9,
        "graded": 3,
        "points": 12,
        "solutions": [],
        "assets": 0,
    },
}
EXTENSION_EXERCISE_COUNT = sum(int(value["exercises"]) for value in EXPECTED_UNIT_CENSUS.values())
EXTENSION_SOURCE_SOLUTION_COUNT = sum(len(value["solutions"]) for value in EXPECTED_UNIT_CENSUS.values())

# Two list-era receipts predate the rule that every post-review correction ID
# must occur inside a protected-surface JSON manifest.  Preserve those IDs as
# explicit, separately evidenced backend records instead of silently dropping
# them or rewriting immutable QA receipts.
LEGACY_UNMANIFESTED_CORRECTIONS: dict[str, dict[str, Any]] = {
    "O011-TRANS-0168": {
        "unit": 14,
        "target_scope": ("lecture", "worksheet", "solution5", "solution9", "solution14"),
        "description": "Post-review Indonesian reader refinements recorded by the Unit 14 independent review and adverse ledger.",
        "evidence_keys": ("post_review_correction_closure", "independent_review", "adverse_ledger", "math_qa"),
    },
    "O011-CORR-0180": {
        "unit": 15,
        "target_scope": "lecture",
        "description": "The frozen German countable-atlas phrase has inconsistent article/adjective agreement; the Indonesian lecture preserves the intended mathematical reading.",
        "evidence_keys": ("countable_atlas_correction_closure", "repeat_and_anomalies", "adverse_ledger", "math_qa"),
    },
}

SUPPLEMENTAL_CORRECTION_MANIFESTS: dict[int, tuple[str, ...]] = {
    14: ("qa/unit-14/UNIT14_INTERNAL_ENVIRONMENT_CORRECTION.json",),
    15: ("qa/unit-15/UNIT15_INTERNAL_ENVIRONMENT_CORRECTION.json",),
}

WORKFLOW = "o011-export-backend-v19"
MODEL_IDENTIFICATION = v10.MODEL_IDENTIFICATION
UNITS = (17, 18, 19)
DEFAULT_TRANSLATION_STATE = "mathematically_reviewed"
EDITION_ID = v10.EDITION_ID
RESOURCE_ID = v10.RESOURCE_ID
COURSE_ID = v10.COURSE_ID
TEXT_RIGHTS_ID = v10.TEXT_RIGHTS_ID
CSV_FIELDS = v10.CSV_FIELDS
ENTITY_TYPES = v10.ENTITY_TYPES
FINAL_PDF_PAGE_SIZE = "A4, 595.276 x 841.89 pt"
FINAL_READER_PATHS = {
    "html_entry": "output/html/unit-19/index.html",
    "html_manifest": "output/html/unit-19/manifest.json",
    "html_qa": "qa/unit-19/HTML_READER_QA.json",
    "html_browser_qa": "qa/unit-19/HTML_BROWSER_QA.json",
    "pdf": "output/pdf/geometri-diferensial-manifold-mulus-hingga-unit-19-id.pdf",
    "pdf_structural_qa": "qa/unit-19/pdf_structural_qa.json",
    "pdf_visual_qa": "qa/unit-19/PDF_VISUAL_QA.json",
}
BUILD_CORRECTION_ID = "O011-ACC-0228"
BUILD_CORRECTION_ARTIFACT_ID = "o011-artifact-u18-hyperboloid2-loader-alias"
BUILD_CORRECTION_TARGET_ID = "o011-asset-file-u18-hyperboloid2-png"
BUILD_CORRECTION_PATHS = {
    "adverse_ledger": "00_control/ADVERSE_LEDGER.csv",
    "build_script": "scripts/build_through_unit19.ps1",
    "build_qa": "qa/unit-19/build.json",
    "alias_qa": "qa/unit-19/MEDIA_ALIAS_RECEIPT.json",
    "canonical_media": "authority/media/Hyperboloid2.png",
    "loader_alias": "build/generated/media/Hyperboloid2.png",
}


sha256_bytes = v10.sha256_bytes
canonical_json = v10.canonical_json
binding = v10.binding
load_json = v10.load_json
safe_repo_path = v10.safe_repo_path
declared_entry_path = v10.declared_entry_path
contains_binding = v10.contains_binding
base_record = v10.base_record
add_relation = v10.add_relation
media_type = v10.media_type
unit_ids = v10.unit_ids
correction_record_id = v10.correction_record_id


def assert_prefix(root: Path) -> tuple[bytes, bytes, list[dict[str, Any]]]:
    jsonl = (root / "backend/records.jsonl").read_bytes()
    jsonl_lines = jsonl.splitlines(keepends=True)
    if len(jsonl_lines) < BASELINE_RECORD_COUNT:
        raise RuntimeError("backend has fewer than the immutable 3,208-record Units 1--16 prefix")
    jsonl_prefix = b"".join(jsonl_lines[:BASELINE_RECORD_COUNT])
    if len(jsonl_prefix) != BASELINE_JSONL_BYTES or sha256_bytes(jsonl_prefix) != BASELINE_JSONL_SHA256:
        raise RuntimeError("immutable public Units 1--16 JSONL prefix changed")

    csv_bytes = (root / "backend/records.csv").read_bytes()
    csv_lines = csv_bytes.splitlines(keepends=True)
    if len(csv_lines) < BASELINE_CSV_LINES:
        raise RuntimeError("backend CSV has fewer than the immutable Units 1--16 prefix")
    csv_prefix = b"".join(csv_lines[:BASELINE_CSV_LINES])
    if len(csv_prefix) != BASELINE_CSV_BYTES or sha256_bytes(csv_prefix) != BASELINE_CSV_SHA256:
        raise RuntimeError("immutable public Units 1--16 CSV prefix changed")
    baseline = [json.loads(line.decode("utf-8")) for line in jsonl_lines[:BASELINE_RECORD_COUNT]]
    return jsonl_prefix, csv_prefix, baseline


def translation_receipt_relative(unit: int, target_relative: str) -> str:
    """Return the deterministic receipt path used by every translated TeX surface."""
    tag = f"{unit:02d}"
    target = Path(target_relative)
    if target.parent.as_posix() != f"source/units/unit-{tag}" or not target.name.endswith(".id.tex"):
        raise RuntimeError(f"Unit {unit} translation target is outside its admitted source directory: {target_relative}")
    return f"qa/unit-{tag}/{target.name.removesuffix('.id.tex')}_translation.json"


def _normalize_target_entry(root: Path, unit: int, entry: dict[str, Any], label: str) -> dict[str, Any]:
    normalized = dict(entry)
    target_relative = declared_entry_path(normalized, label)
    expected_receipt = translation_receipt_relative(unit, target_relative)
    declared_receipt = str(normalized.get("translation_receipt") or expected_receipt)
    if declared_receipt != expected_receipt:
        raise RuntimeError(f"{label} declares a noncanonical translation receipt: {declared_receipt}")
    receipt_path = safe_repo_path(root, declared_receipt)
    if not receipt_path.is_file():
        raise RuntimeError(f"{label} translation receipt is missing: {declared_receipt}")
    receipt_binding = binding(receipt_path, root)
    declared_sha = normalized.get("translation_receipt_sha256")
    if declared_sha is not None and declared_sha != receipt_binding["sha256"]:
        raise RuntimeError(f"{label} translation-receipt SHA-256 is stale: {declared_receipt}")
    normalized["translation_receipt"] = declared_receipt
    normalized["translation_receipt_sha256"] = receipt_binding["sha256"]
    return normalized


def _derived_authority_solutions(preflight: dict[str, Any], unit: int) -> list[dict[str, Any]]:
    derived: list[dict[str, Any]] = []
    for item in preflight.get("solutions", {}).get("exercises", []):
        if not isinstance(item, dict) or item.get("exists") is not True:
            continue
        exercise = int(item["exercise_index"])
        source = item.get("expanded_latex", {}).get("sanitized_source", {})
        if not isinstance(source, dict) or not source.get("path"):
            raise RuntimeError(f"Unit {unit} solution {exercise} lacks its frozen sanitized authority source")
        derived.append({"exercise": exercise, **source})
    return sorted(derived, key=lambda value: int(value["exercise"]))


def _derived_correction_manifests(root: Path, unit: int) -> list[dict[str, Any]]:
    qa_dir = root / f"qa/unit-{unit:02d}"
    paths = sorted(qa_dir.glob("*_PROTECTED_CORRECTIONS.json"), key=lambda value: value.name)
    if not paths:
        raise RuntimeError(f"Unit {unit} has no protected-correction manifests to normalize")
    return [binding(path, root) for path in paths]


def _manifest_correction_ids(root: Path, unit: int, manifests: list[dict[str, Any]]) -> set[str]:
    result: set[str] = set()
    for index, entry in enumerate(manifests, 1):
        relative = declared_entry_path(entry, f"Unit {unit} correction manifest {index}")
        result.update(v10.extract_correction_ids(load_json(safe_repo_path(root, relative))))
    return result


def normalize_post_qa(root: Path, unit: int, preflight: dict[str, Any], raw: dict[str, Any]) -> dict[str, Any]:
    """Losslessly normalize the admitted list-era and dict-era POST-QA schemas.

    Units 14 and 15 were frozen before the structured ``targets`` and
    ``authority.supplied_solutions`` fields were introduced.  Their receipts
    remain immutable evidence; this compatibility view is constructed only in
    memory from those receipts, their exact preflights, and convention-bound
    translation/correction receipts.  The structured Units 17--19 forms pass
    through the same validations without being downgraded.
    """
    math_qa = dict(raw)
    declared = math_qa.get("declared_corrections", math_qa.get("corrections", []))
    if not isinstance(declared, list) or not declared or any(not isinstance(value, str) or not value for value in declared):
        raise RuntimeError(f"Unit {unit} has no valid declared-correction closure")
    if len(declared) != len(set(declared)):
        raise RuntimeError(f"Unit {unit} declares duplicate correction IDs")
    math_qa["all_declared_corrections"] = list(declared)

    authority_raw = math_qa.get("authority", {})
    if not isinstance(authority_raw, dict):
        raise RuntimeError(f"Unit {unit} POST-QA authority is not an object")
    authority = dict(authority_raw)
    supplied_authority = authority.get("supplied_solutions")
    if supplied_authority is None:
        supplied_authority = _derived_authority_solutions(preflight, unit)
    if not isinstance(supplied_authority, list):
        raise RuntimeError(f"Unit {unit} authority supplied-solution closure is not a list")
    authority["supplied_solutions"] = [dict(value) for value in supplied_authority]
    math_qa["authority"] = authority

    targets_raw = math_qa.get("targets", {})
    if isinstance(targets_raw, list):
        surface_entries = [dict(value) for value in targets_raw if isinstance(value, dict) and "exercise" not in value]
        solution_entries = [dict(value) for value in targets_raw if isinstance(value, dict) and "exercise" in value]
        lecture_matches = [value for value in surface_entries if Path(str(value.get("path", ""))).name == f"lecture{unit:02d}.id.tex"]
        worksheet_matches = [value for value in surface_entries if Path(str(value.get("path", ""))).name == f"worksheet{unit:02d}.id.tex"]
        if len(lecture_matches) != 1 or len(worksheet_matches) != 1 or len(surface_entries) != 2:
            raise RuntimeError(f"Unit {unit} list-era target receipt does not uniquely identify lecture and worksheet")
        targets: dict[str, Any] = {
            "lecture": lecture_matches[0],
            "worksheet": worksheet_matches[0],
            "supplied_solutions": solution_entries,
        }
    elif isinstance(targets_raw, dict):
        targets = dict(targets_raw)
    else:
        raise RuntimeError(f"Unit {unit} POST-QA targets are neither a list nor an object")

    for key in ("lecture", "worksheet"):
        entry = targets.get(key)
        if not isinstance(entry, dict):
            raise RuntimeError(f"Unit {unit} POST-QA lacks a structured {key} target")
        targets[key] = _normalize_target_entry(root, unit, entry, f"Unit {unit} {key} target")
    solutions_raw = targets.get("supplied_solutions", [])
    if not isinstance(solutions_raw, list):
        raise RuntimeError(f"Unit {unit} target supplied-solution closure is not a list")
    normalized_solutions: list[dict[str, Any]] = []
    for value in solutions_raw:
        if not isinstance(value, dict) or "exercise" not in value:
            raise RuntimeError(f"Unit {unit} contains a malformed supplied-solution target")
        exercise = int(value["exercise"])
        normalized_solutions.append(_normalize_target_entry(root, unit, value, f"Unit {unit} solution {exercise} target"))
    targets["supplied_solutions"] = sorted(normalized_solutions, key=lambda value: int(value["exercise"]))
    math_qa["targets"] = targets

    manifests = math_qa.get("correction_manifests")
    if manifests is None:
        manifests = _derived_correction_manifests(root, unit)
    if not isinstance(manifests, list) or not manifests:
        raise RuntimeError(f"Unit {unit} has no admitted correction-manifest closure")
    normalized_manifests = [dict(value) for value in manifests]
    declared_manifest_paths = {declared_entry_path(value, f"Unit {unit} correction manifest") for value in normalized_manifests}
    for relative in SUPPLEMENTAL_CORRECTION_MANIFESTS.get(unit, ()):
        if relative not in declared_manifest_paths:
            path = safe_repo_path(root, relative)
            if not path.is_file():
                raise RuntimeError(f"Unit {unit} supplemental correction manifest is missing: {relative}")
            normalized_manifests.append(binding(path, root))
            declared_manifest_paths.add(relative)
    math_qa["correction_manifests"] = normalized_manifests
    manifest_ids = _manifest_correction_ids(root, unit, math_qa["correction_manifests"])
    declared_ids = set(declared)
    unexpected = sorted(manifest_ids - declared_ids)
    if unexpected:
        raise RuntimeError(f"Unit {unit} correction manifests contain undeclared IDs: {unexpected}")
    unmanifested = [value for value in declared if value not in manifest_ids]
    for correction_id in unmanifested:
        spec = LEGACY_UNMANIFESTED_CORRECTIONS.get(correction_id)
        if spec is None or int(spec["unit"]) != unit:
            raise RuntimeError(f"Unit {unit} has an unmanifested correction without an admitted compatibility rule: {correction_id}")
    math_qa["declared_corrections"] = [value for value in declared if value in manifest_ids]
    math_qa["legacy_unmanifested_corrections"] = unmanifested

    source_closure_raw = math_qa.get("source_closure", {})
    if not isinstance(source_closure_raw, dict):
        raise RuntimeError(f"Unit {unit} source closure is not an object")
    source_closure = dict(source_closure_raw)
    aliases = {
        "point_total": "graded_points_total",
        "media_occurrence_count": "media_occurrences",
        "unique_media_asset_count": "media_assets",
    }
    for current, legacy in aliases.items():
        if current not in source_closure and legacy in source_closure:
            source_closure[current] = source_closure[legacy]
    if "hint_fields_blank" not in source_closure and "blank_hint_count" in source_closure:
        source_closure["hint_fields_blank"] = source_closure.get("blank_hint_count") == source_closure.get("exercise_count")
    solution_rows = [value for value in preflight.get("solutions", {}).get("exercises", []) if isinstance(value, dict)]
    if "graded_exercise_indices" not in source_closure:
        source_closure["graded_exercise_indices"] = [int(value["exercise_index"]) for value in solution_rows if value.get("point_value") is not None]
    if "graded_point_values" not in source_closure:
        source_closure["graded_point_values"] = [int(value["point_value"]) for value in solution_rows if value.get("point_value") is not None]
    if "supplied_solution_indices" not in source_closure:
        source_closure["supplied_solution_indices"] = [int(value) for value in preflight.get("solutions", {}).get("supplied_solution_indices", [])]
    math_qa["source_closure"] = source_closure
    return math_qa


def prepare_unit(root: Path, unit: int) -> dict[str, Any]:
    """Load a frozen unit while allowing its own QA directory as evidence scope."""
    tag = f"{unit:02d}"
    qa_dir = root / f"qa/unit-{tag}"
    preflight_path = qa_dir / "AUTHORITY_PREFLIGHT.json"
    math_path = qa_dir / "POST_CORRECTION_MATH_QA.json"
    if not math_path.is_file():
        raise RuntimeError(f"Unit {unit} is not frozen: missing {math_path.relative_to(root).as_posix()}")
    preflight = load_json(preflight_path)
    math_qa = normalize_post_qa(root, unit, preflight, load_json(math_path))
    if preflight.get("status") != "pass" or preflight.get("unit") != unit:
        raise RuntimeError(f"Unit {unit} authority preflight is not passing")
    if math_qa.get("status") != "pass" or math_qa.get("unit_id") != f"o011-brenner-u{tag}":
        raise RuntimeError(f"Unit {unit} post-correction mathematical QA is not passing/current")

    # Unit 11 records the source animation and its reader static fallback as
    # separate named counts.  The v10 validator expects the older aggregate
    # source-media key; supply that lossless compatibility view in memory only.
    source_closure = math_qa.get("source_closure", {})
    if "media_occurrence_count" not in source_closure:
        if "static_media_occurrence_count" not in source_closure:
            raise RuntimeError(f"Unit {unit} post-correction QA has no source-media occurrence census")
        source_closure["media_occurrence_count"] = preflight.get("media", {}).get("occurrence_count", 0)

    authority = math_qa.get("authority", {})
    targets = math_qa.get("targets", {})
    paths: dict[str, Path] = {
        "preflight": preflight_path,
        "preflight_verify": qa_dir / "AUTHORITY_PREFLIGHT_VERIFY.json",
        "solution_closure": qa_dir / "solution_closure.json",
        "math_qa": math_path,
        "lecture_source": safe_repo_path(root, declared_entry_path(authority.get("lecture", {}), f"Unit {unit} lecture authority")),
        "worksheet_source": safe_repo_path(root, declared_entry_path(authority.get("worksheet", {}), f"Unit {unit} worksheet authority")),
        "lecture_target": safe_repo_path(root, declared_entry_path(targets.get("lecture", {}), f"Unit {unit} lecture target")),
        "worksheet_target": safe_repo_path(root, declared_entry_path(targets.get("worksheet", {}), f"Unit {unit} worksheet target")),
        "lecture_receipt": safe_repo_path(root, str(targets.get("lecture", {}).get("translation_receipt", ""))),
        "worksheet_receipt": safe_repo_path(root, str(targets.get("worksheet", {}).get("translation_receipt", ""))),
    }
    if math_qa.get("legacy_unmanifested_corrections"):
        evidence_entries = {
            "repeat_and_anomalies": authority.get("repeat_and_anomalies"),
            "independent_review": math_qa.get("independent_review"),
            "adverse_ledger": math_qa.get("ledgers", {}).get("adverse"),
        }
        for key, entry in evidence_entries.items():
            if not isinstance(entry, dict):
                raise RuntimeError(f"Unit {unit} legacy correction evidence is missing: {key}")
            paths[key] = safe_repo_path(root, declared_entry_path(entry, f"Unit {unit} legacy correction evidence {key}"))
        if unit == 14:
            paths["post_review_correction_closure"] = root / "qa/unit-14/UNIT14_POST_REVIEW_CORRECTION_CLOSURE.json"
        if unit == 15:
            paths["countable_atlas_correction_closure"] = root / "qa/unit-15/UNIT15_COUNTABLE_ATLAS_CORRECTION_CLOSURE.json"
    authority_solutions = {int(item["exercise"]): item for item in authority.get("supplied_solutions", [])}
    target_solutions = {int(item["exercise"]): item for item in targets.get("supplied_solutions", [])}
    solution_indices = tuple(int(value) for value in preflight.get("solutions", {}).get("supplied_solution_indices", []))
    if set(authority_solutions) != set(solution_indices) or set(target_solutions) != set(solution_indices):
        raise RuntimeError(f"Unit {unit} post-correction QA does not bind the exact supplied-solution set")
    for index in solution_indices:
        source_entry = authority_solutions[index]
        target_entry = target_solutions[index]
        paths[f"solution{index}_source"] = safe_repo_path(root, declared_entry_path(source_entry, f"Unit {unit} solution {index} authority"))
        paths[f"solution{index}_target"] = safe_repo_path(root, declared_entry_path(target_entry, f"Unit {unit} solution {index} target"))
        paths[f"solution{index}_receipt"] = safe_repo_path(root, str(target_entry.get("translation_receipt", "")))

    manifest_entries = math_qa.get("correction_manifests", [])
    if not isinstance(manifest_entries, list) or not manifest_entries:
        raise RuntimeError(f"Unit {unit} has no admitted correction-manifest closure")
    allowed_prefixes = ("00_control/", f"qa/unit-{tag}/")
    for index, entry in enumerate(manifest_entries, 1):
        relative = declared_entry_path(entry, f"Unit {unit} correction manifest {index}")
        if not relative.startswith(allowed_prefixes):
            raise RuntimeError(f"Unit {unit} correction manifest is outside its admitted evidence scopes: {relative}")
        paths[f"correction_manifest:{index:02d}"] = safe_repo_path(root, relative)
    for asset in preflight.get("media", {}).get("assets", []):
        binary = asset.get("binary", {})
        relative = binary.get("path") or f"authority/media/{asset['filename']}"
        paths[f"media:{asset['filename']}"] = safe_repo_path(root, str(relative))

    missing = [f"{key}: {path.relative_to(root).as_posix()}" for key, path in paths.items() if not path.is_file()]
    if missing:
        raise RuntimeError(f"Unit {unit} is not frozen; missing inputs: " + "; ".join(missing))
    bindings = {key: binding(path, root) for key, path in sorted(paths.items())}
    context: dict[str, Any] = {
        "unit": unit,
        "tag": tag,
        "preflight": preflight,
        "math_qa": math_qa,
        "paths": paths,
        "bindings": bindings,
        "solution_indices": solution_indices,
        "reader_bound": False,
        "html_bound": False,
        "pdf_bound": False,
    }
    v10.validate_unit_inputs(root, context)
    validate_unit_census(context)
    return context


def validate_unit_census(context: dict[str, Any]) -> None:
    unit = int(context["unit"])
    expected = EXPECTED_UNIT_CENSUS[unit]
    structure = context["preflight"]["structure"]
    actual = {
        "lecture_sections": structure.get("lecture_section_count"),
        "worksheet_sections": structure.get("worksheet_section_count"),
        "exercises": structure.get("worksheet_exercise_count"),
        "practice": structure.get("worksheet_practice_count"),
        "graded": structure.get("worksheet_graded_count"),
        "points": structure.get("worksheet_point_total"),
        "solutions": list(context["solution_indices"]),
        "assets": len(context["preflight"].get("media", {}).get("assets", [])),
    }
    if actual != expected:
        raise RuntimeError(f"frozen Unit {unit} semantic census changed: {actual!r}")
    if not context["math_qa"].get("all_declared_corrections"):
        raise RuntimeError(f"Unit {unit} has no declared source/translation correction closure")
    if not context["math_qa"].get("correction_manifests"):
        raise RuntimeError(f"Unit {unit} has no correction-manifest closure")


def add_legacy_correction_records(context: dict[str, Any], records: list[dict[str, Any]], checkpoint: str) -> None:
    correction_ids = list(context["math_qa"].get("legacy_unmanifested_corrections", []))
    if not correction_ids:
        return
    unit = int(context["unit"])
    tag = str(context["tag"])
    _, lecture_id, worksheet_id = unit_ids(unit)
    solution_indices = tuple(context["solution_indices"])
    bindings = context["bindings"]
    target_map: dict[str, tuple[str, dict[str, Any], dict[str, Any]]] = {
        "lecture": (lecture_id, bindings["lecture_target"], bindings["lecture_receipt"]),
        "worksheet": (worksheet_id, bindings["worksheet_target"], bindings["worksheet_receipt"]),
    }
    for index in solution_indices:
        target_map[f"solution{index}"] = (
            f"{worksheet_id}-e{index:03d}-solution",
            bindings[f"solution{index}_target"],
            bindings[f"solution{index}_receipt"],
        )
    for correction_id in correction_ids:
        spec = LEGACY_UNMANIFESTED_CORRECTIONS[correction_id]
        raw_scope = spec["target_scope"]
        if raw_scope == "all_translated_surfaces":
            selected = list(target_map)
        elif isinstance(raw_scope, (list, tuple)):
            selected = [str(value) for value in raw_scope]
        else:
            selected = [str(raw_scope)]
        targets = [target_map[key] for key in selected]
        target_ids = sorted(value[0] for value in targets)
        target_bindings = [{**value[1], "target_id": value[0]} for value in targets]
        validation_bindings = [value[2] for value in targets]
        evidence = [bindings[str(key)] for key in spec["evidence_keys"]]
        record_id = v10.correction_record_id(correction_id)
        records.append(base_record(
            record_id,
            "correction",
            checkpoint,
            source_local_id=correction_id,
            severity="P3",
            description=str(spec["description"]),
            disposition="Corrected in the Indonesian target and verified against the frozen authority",
            correction_status="corrected_in_target",
            upstream_report_disposition="deferred_until_full_corpus",
            target_ids=target_ids,
            target_bindings=target_bindings,
            correction_manifests=[],
            legacy_correction_evidence=evidence,
            validation_bindings=validation_bindings,
            post_correction_qa_binding=bindings["math_qa"],
        ))
        for position, target_id in enumerate(target_ids, 1):
            add_relation(records, checkpoint, f"o011-rel-{record_id}-corrects-{position:02d}", "corrects", record_id, target_id)

    closure_id = f"o011-qa-unit{tag}-correction-closure"
    closure_events = [record for record in records if record.get("id") == closure_id]
    if len(closure_events) != 1:
        raise RuntimeError(f"Unit {unit} correction-closure QA event is absent or duplicated")
    closure_events[0]["values"] = {"correction_ids": context["math_qa"]["all_declared_corrections"]}


def prepare_reader_closure(root: Path) -> dict[str, Any]:
    paths = {key: root / relative for key, relative in FINAL_READER_PATHS.items()}
    missing = [relative for key, relative in FINAL_READER_PATHS.items() if not paths[key].is_file()]
    if missing:
        raise RuntimeError("cumulative Unit 19 reader closure is incomplete: " + ", ".join(missing))
    bindings = {key: binding(path, root) for key, path in paths.items()}

    html_manifest = load_json(paths["html_manifest"])
    html_qa = load_json(paths["html_qa"])
    if html_manifest.get("workflow") != "o011-export-html-v19" or html_manifest.get("status") != "partial_edition":
        raise RuntimeError("unexpected cumulative Unit 19 HTML manifest workflow/status")
    if html_manifest.get("language") != "id-ID" or html_manifest.get("units") != list(range(1, 20)):
        raise RuntimeError("cumulative HTML manifest does not cover exactly Units 1--19 in id-ID")
    if html_manifest.get("model_identification") != MODEL_IDENTIFICATION:
        raise RuntimeError("cumulative HTML manifest has the wrong model identification")
    if html_qa.get("workflow") != "o011-verify-html-v19" or html_qa.get("status") != "pass":
        raise RuntimeError("cumulative Unit 19 HTML QA is not passing")
    if not contains_binding(html_qa, bindings["html_entry"]) or not contains_binding(html_qa, bindings["html_manifest"]):
        raise RuntimeError("cumulative HTML QA does not bind the exact entry and manifest bytes")
    manifest_entry = {"path": "index.html", "bytes": bindings["html_entry"]["bytes"], "sha256": bindings["html_entry"]["sha256"]}
    if not any(isinstance(item, dict) and all(item.get(key) == value for key, value in manifest_entry.items()) for item in html_manifest.get("files", [])):
        raise RuntimeError("cumulative HTML manifest does not inventory the exact entry bytes")

    browser = load_json(paths["html_browser_qa"])
    if browser.get("workflow") != "o011-html-browser-qa-v19" or browser.get("status") != "pass":
        raise RuntimeError("cumulative Unit 19 HTML browser QA is not passing")
    if not contains_binding(browser.get("surface", {}), bindings["html_entry"]) or not contains_binding(browser.get("surface", {}), bindings["html_manifest"]):
        raise RuntimeError("cumulative HTML browser QA does not bind the exact entry and manifest bytes")
    if not contains_binding(browser.get("surface", {}), bindings["html_qa"]):
        raise RuntimeError("cumulative HTML browser QA does not bind the structural HTML QA receipt")
    browser_checks = browser.get("checks", {})
    if not isinstance(browser_checks, dict) or not browser_checks or any(value is not True for value in browser_checks.values()):
        raise RuntimeError("cumulative HTML browser QA does not pass every declared runtime/responsive check")
    for profile in ("desktop", "mobile"):
        viewport = browser.get(profile, {}).get("viewport", {})
        if viewport.get("page_has_horizontal_overflow") is not False:
            raise RuntimeError(f"cumulative HTML browser QA reports {profile} page overflow")
    runtime = browser.get("runtime", {})
    if runtime.get("mathjax_errors") != 0 or runtime.get("console_errors") != 0 or not isinstance(runtime.get("mathjax_containers"), int) or runtime.get("mathjax_containers", 0) <= 0:
        raise RuntimeError("cumulative HTML browser QA runtime/MathJax census is not clean")

    structural = load_json(paths["pdf_structural_qa"])
    if structural.get("workflow") != "o011-through-unit19-pdf-structural-accessibility-qa-v1":
        raise RuntimeError("unexpected cumulative Unit 19 PDF structural-QA workflow")
    if structural.get("passed") is not True or structural.get("blockers") not in (None, []):
        raise RuntimeError("cumulative Unit 19 PDF structural QA is not passing")
    structural_pdf = structural.get("pdf", {})
    if not isinstance(structural_pdf, dict) or not contains_binding(structural_pdf, bindings["pdf"]):
        raise RuntimeError("cumulative PDF structural QA does not bind the exact PDF bytes")
    if not contains_binding(structural.get("execution_binding", {}), bindings["pdf"]):
        raise RuntimeError("cumulative PDF execution binding does not bind the exact PDF bytes")
    pages = structural_pdf.get("pages")
    if not isinstance(pages, int) or pages <= 261:
        raise RuntimeError("cumulative Unit 19 PDF page count does not extend the 261-page Unit 16 boundary")
    if any(structural_pdf.get(key) is not True for key in ("all_media_boxes_a4", "all_crop_boxes_a4", "all_rotations_zero")):
        raise RuntimeError("cumulative Unit 19 PDF structural QA does not prove unrotated A4 pages")
    if structural.get("layout", {}).get("centered_body_bounds_passed") is not True:
        raise RuntimeError("cumulative Unit 19 PDF structural QA does not prove centered body bounds")

    visual = load_json(paths["pdf_visual_qa"])
    if visual.get("workflow") != "o011-pdf-visual-qa-v19" or visual.get("status") != "pass":
        raise RuntimeError("cumulative Unit 19 PDF visual QA is not passing")
    surface = visual.get("surface", {})
    if not isinstance(surface, dict) or not contains_binding(surface, bindings["pdf"]):
        raise RuntimeError("cumulative PDF visual QA does not bind the exact PDF bytes")
    if surface.get("pages") != pages or surface.get("page_size") != FINAL_PDF_PAGE_SIZE:
        raise RuntimeError("cumulative PDF visual QA does not cover the exact A4 surface")
    checks = visual.get("checks", {})
    if not isinstance(checks, dict) or not checks or any(value is not True for value in checks.values()):
        raise RuntimeError("cumulative PDF visual QA does not pass every declared check")
    return {
        "paths": paths,
        "bindings": bindings,
        "html_manifest": html_manifest,
        "html_qa": html_qa,
        "html_browser_qa": browser,
        "pdf_structural_qa": structural,
        "pdf_visual_qa": visual,
        "pages": pages,
    }


def prepare_build_correction(root: Path) -> dict[str, Any]:
    """Bind the one cumulative build-surface repair outside per-unit math QA."""
    paths = {key: safe_repo_path(root, relative) for key, relative in BUILD_CORRECTION_PATHS.items()}
    missing = [BUILD_CORRECTION_PATHS[key] for key, path in paths.items() if not path.is_file()]
    if missing:
        raise RuntimeError("Unit 18 loader-alias correction closure is incomplete: " + ", ".join(missing))
    bindings = {key: binding(path, root) for key, path in sorted(paths.items())}

    with paths["adverse_ledger"].open("r", encoding="utf-8-sig", newline="") as handle:
        matching = [row for row in csv.DictReader(handle) if row.get("id") == BUILD_CORRECTION_ID]
    if len(matching) != 1:
        raise RuntimeError(f"{BUILD_CORRECTION_ID} is absent or duplicated in the adverse ledger")
    row = matching[0]
    expected = {
        "severity": "P1",
        "surface": "unit18:hyperboloid-static-media-loader",
        "status": "build_structure_repaired",
    }
    if any(row.get(key) != value for key, value in expected.items()):
        raise RuntimeError(f"{BUILD_CORRECTION_ID} adverse-ledger semantics changed")

    alias_receipt = load_json(paths["alias_qa"])
    aliases = alias_receipt.get("aliases", [])
    matching_aliases = [
        value for value in aliases
        if isinstance(value, dict)
        and value.get("source") == bindings["canonical_media"]["path"]
        and value.get("target") == bindings["loader_alias"]["path"]
    ]
    if len(matching_aliases) != 1:
        raise RuntimeError("Unit 18 Hyperboloid2 loader alias is absent or duplicated in its receipt")
    alias = matching_aliases[0]
    if (
        alias.get("transient") is not False
        or alias.get("bytes") != bindings["loader_alias"]["bytes"]
        or alias.get("sha256") != bindings["loader_alias"]["sha256"]
        or bindings["canonical_media"]["bytes"] != bindings["loader_alias"]["bytes"]
        or bindings["canonical_media"]["sha256"] != bindings["loader_alias"]["sha256"]
    ):
        raise RuntimeError("Unit 18 Hyperboloid2 loader alias is not an exact persistent copy")
    build_qa = load_json(paths["build_qa"])
    if build_qa.get("workflow") != "o011-through-unit19-pdf-build-v1" or not contains_binding(build_qa, bindings["loader_alias"]):
        raise RuntimeError("Unit 19 build receipt does not bind the exact Unit 18 loader alias")
    return {"row": row, "paths": paths, "bindings": bindings}


def reader_closure_manifest(reader: dict[str, Any]) -> dict[str, Any]:
    bindings = reader["bindings"]
    return {
        "status": "cumulative_html_pdf_reader_bound",
        "through_unit": 19,
        "html": {"entry": bindings["html_entry"], "manifest": bindings["html_manifest"], "qa": bindings["html_qa"], "browser_qa": bindings["html_browser_qa"]},
        "pdf": {
            "artifact": bindings["pdf"],
            "pages": reader["pages"],
            "page_size": FINAL_PDF_PAGE_SIZE,
            "structural_qa": bindings["pdf_structural_qa"],
            "visual_qa": bindings["pdf_visual_qa"],
        },
    }


def add_reader_records(records: list[dict[str, Any]], baseline: list[dict[str, Any]], reader: dict[str, Any], checkpoint: str, state: str) -> None:
    bindings = reader["bindings"]
    closure = reader_closure_manifest(reader)
    rights_ids = sorted({str(record["id"]) for record in baseline + records if record.get("entity_type") == "rights"})
    artifact_specs = (
        ("o011-artifact-u19-html-entry", "html_entry", "cumulative_semantic_html_reader_entry", "Indonesian", "id-ID", "represents"),
        ("o011-artifact-u19-html-manifest", "html_manifest", "cumulative_semantic_html_inventory", None, None, "evidences"),
        ("o011-artifact-u19-html-qa", "html_qa", "cumulative_semantic_html_qa_receipt", None, None, "evidences"),
        ("o011-artifact-u19-html-browser-qa", "html_browser_qa", "cumulative_semantic_html_browser_runtime_qa_receipt", None, None, "evidences"),
        ("o011-artifact-u19-pdf", "pdf", "cumulative_a4_pdf_reader", "Indonesian", "id-ID", "represents"),
        ("o011-artifact-u19-pdf-structural-qa", "pdf_structural_qa", "cumulative_pdf_structural_accessibility_qa_receipt", None, None, "evidences"),
        ("o011-artifact-u19-pdf-visual-qa", "pdf_visual_qa", "cumulative_pdf_visual_qa_receipt", None, None, "evidences"),
    )
    for artifact_id, key, kind, language, locale, relation_type in artifact_specs:
        value = bindings[key]
        records.append(base_record(
            artifact_id,
            "artifact",
            checkpoint,
            parent_id=EDITION_ID,
            path=value["path"],
            bytes=value["bytes"],
            target_sha256=value["sha256"],
            artifact_kind=kind,
            media_type=media_type(value["path"]),
            language=language,
            locale=locale,
            translation_state=state,
            rights_component_id=TEXT_RIGHTS_ID,
            component_rights_ids=rights_ids,
            reader_closure=closure if key.endswith("qa") else None,
        ))
        add_relation(records, checkpoint, f"o011-rel-{artifact_id}-{relation_type}-edition", relation_type, artifact_id, EDITION_ID)

    qa_specs = (
        ("o011-qa-unit19-html-reader", "o011-artifact-u19-html-entry", "html_qa", "o011-artifact-u19-html-qa", "cumulative_semantic_html_reader"),
        ("o011-qa-unit19-html-browser", "o011-artifact-u19-html-entry", "html_browser_qa", "o011-artifact-u19-html-browser-qa", "cumulative_semantic_html_browser_runtime"),
        ("o011-qa-unit19-pdf-structural", "o011-artifact-u19-pdf", "pdf_structural_qa", "o011-artifact-u19-pdf-structural-qa", "cumulative_pdf_structural_accessibility"),
        ("o011-qa-unit19-pdf-visual", "o011-artifact-u19-pdf", "pdf_visual_qa", "o011-artifact-u19-pdf-visual-qa", "cumulative_pdf_visual"),
    )
    for event_id, target_id, key, artifact_id, kind in qa_specs:
        value = bindings[key]
        records.append(base_record(event_id, "qa_event", checkpoint, parent_id="o011-brenner-u19", target_id=target_id, receipt_path=value["path"], evidence_sha256=value["sha256"], result="pass", qa_kind=kind, values=closure, artifact_id=artifact_id, translation_state=state))
        add_relation(records, checkpoint, f"o011-rel-{event_id}-evidences-target", "evidences", event_id, target_id)


def add_build_correction_records(records: list[dict[str, Any]], correction: dict[str, Any], checkpoint: str) -> None:
    row = correction["row"]
    bindings = correction["bindings"]
    records.append(base_record(
        BUILD_CORRECTION_ARTIFACT_ID,
        "artifact",
        checkpoint,
        parent_id=BUILD_CORRECTION_TARGET_ID,
        path=bindings["loader_alias"]["path"],
        bytes=bindings["loader_alias"]["bytes"],
        source_sha256=bindings["canonical_media"]["sha256"],
        target_sha256=bindings["loader_alias"]["sha256"],
        artifact_kind="mediawiki_static_png_loader_alias",
        media_type="image/png",
        translation_state="built",
        rights_component_id="o011-rights-media-u18-02",
        component_rights_ids=["o011-rights-media-u18-02"],
        canonical_source_binding=bindings["canonical_media"],
        alias_receipt_binding=bindings["alias_qa"],
    ))
    record_id = correction_record_id(BUILD_CORRECTION_ID)
    records.append(base_record(
        record_id,
        "correction",
        checkpoint,
        source_local_id=BUILD_CORRECTION_ID,
        severity=row["severity"],
        source_surface=row["surface"],
        description=row["description"],
        disposition=row["disposition"],
        correction_status=row["status"],
        upstream_report_disposition="not_an_upstream_source_error_local_build_surface",
        target_ids=[BUILD_CORRECTION_ARTIFACT_ID],
        target_bindings=[{**bindings["loader_alias"], "target_id": BUILD_CORRECTION_ARTIFACT_ID}],
        correction_manifests=[],
        legacy_correction_evidence=[
            bindings["adverse_ledger"],
            bindings["build_script"],
            bindings["alias_qa"],
            bindings["build_qa"],
        ],
        validation_bindings=[
            bindings["canonical_media"],
            bindings["loader_alias"],
            bindings["alias_qa"],
            bindings["build_qa"],
        ],
        post_correction_qa_binding=bindings["build_qa"],
    ))
    add_relation(
        records,
        checkpoint,
        f"o011-rel-{record_id}-corrects-loader-alias",
        "corrects",
        record_id,
        BUILD_CORRECTION_ARTIFACT_ID,
    )


def prepare_bundle(root: Path, checkpoint: str, state: str) -> dict[str, Any]:
    jsonl_prefix, csv_prefix, baseline = assert_prefix(root)
    contexts = [prepare_unit(root, unit) for unit in UNITS]
    reader = prepare_reader_closure(root)
    build_correction = prepare_build_correction(root)
    previous_workflow = v10.WORKFLOW
    v10.WORKFLOW = WORKFLOW
    try:
        suffix: list[dict[str, Any]] = []
        for context in contexts:
            unit_records = v10.make_unit_records(context, checkpoint, state)
            add_legacy_correction_records(context, unit_records, checkpoint)
            context["records"] = unit_records
            suffix.extend(unit_records)
        add_reader_records(suffix, baseline, reader, checkpoint, state)
        add_build_correction_records(suffix, build_correction, checkpoint)
    finally:
        v10.WORKFLOW = previous_workflow

    counts = v10.validate_records(baseline, suffix, load_json(root / "backend/schema/o011-record-v1.schema.json"))
    extension_exercises = sum(int(context["preflight"]["structure"]["worksheet_exercise_count"]) for context in contexts)
    extension_solutions = sum(len(context["solution_indices"]) for context in contexts)
    if BASELINE_EXERCISE_COUNT + extension_exercises != FINAL_EXERCISE_COUNT:
        raise RuntimeError(f"cumulative exercise census changed: {BASELINE_EXERCISE_COUNT}+{extension_exercises}")
    if BASELINE_SOURCE_SOLUTION_COUNT + extension_solutions != FINAL_SOURCE_SOLUTION_COUNT:
        raise RuntimeError(f"cumulative source-supplied-solution census changed: {BASELINE_SOURCE_SOLUTION_COUNT}+{extension_solutions}")
    inputs: dict[str, dict[str, Any]] = {"schema": binding(root / "backend/schema/o011-record-v1.schema.json", root)}
    for context in contexts:
        for key, value in context["bindings"].items():
            inputs[f"u{context['tag']}:{key}"] = value
    for key, value in reader["bindings"].items():
        inputs[f"reader:{key}"] = value
    for key, value in build_correction["bindings"].items():
        inputs[f"build-correction:{key}"] = value
    return {
        "jsonl_prefix": jsonl_prefix,
        "csv_prefix": csv_prefix,
        "baseline": baseline,
        "contexts": contexts,
        "reader": reader,
        "build_correction": build_correction,
        "suffix": suffix,
        "counts": counts,
        "inputs": inputs,
    }


def unit_manifest(context: dict[str, Any], state: str, reader: dict[str, Any] | None = None) -> dict[str, Any]:
    manifest = v10.unit_manifest(context, state)
    manifest["correction_ids"] = list(context["math_qa"]["all_declared_corrections"])
    manifest["legacy_unmanifested_correction_ids"] = list(context["math_qa"].get("legacy_unmanifested_corrections", []))
    if reader is not None and int(context["unit"]) == 19:
        bindings = reader["bindings"]
        manifest.update({
            "reader_status": "cumulative_html_pdf_reader_bound",
            "html_status": "cumulative_html_reader_bound",
            "pdf_status": "cumulative_pdf_reader_bound",
            "html_entry": bindings["html_entry"],
            "html_manifest": bindings["html_manifest"],
            "html_qa": bindings["html_qa"],
            "html_browser_qa": bindings["html_browser_qa"],
            "pdf": bindings["pdf"],
            "pdf_structural_qa": bindings["pdf_structural_qa"],
            "pdf_visual_qa": bindings["pdf_visual_qa"],
        })
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--translation-state", default=DEFAULT_TRANSLATION_STATE)
    parser.add_argument("--check-only", action="store_true", help="validate and census all live inputs without changing backend outputs")
    args = parser.parse_args()
    if args.translation_state not in {"translated", "structurally_verified", "mathematically_reviewed", "language_reviewed", "built", "visually_checked"}:
        raise RuntimeError("unsupported Units 17--19 translation state")
    root = args.root.resolve()
    bundle = prepare_bundle(root, args.checkpoint, args.translation_state)
    units = {context["tag"]: unit_manifest(context, args.translation_state, bundle["reader"]) for context in bundle["contexts"]}
    if args.check_only:
        print(json.dumps({"status": "pass", "check_only": True, "baseline_records": BASELINE_RECORD_COUNT, "prospective_added_records": len(bundle["suffix"]), "prospective_combined_records": BASELINE_RECORD_COUNT + len(bundle["suffix"]), "entity_counts": bundle["counts"], "units": units, "reader_closure": reader_closure_manifest(bundle["reader"])}, ensure_ascii=False, sort_keys=True))
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
    closure = reader_closure_manifest(bundle["reader"])
    manifest = {
        "schema_version": 1,
        "workflow": WORKFLOW,
        "checkpoint": args.checkpoint,
        "generator": binding(root / "scripts/export_backend_v19.py", root),
        "verifier": binding(root / "scripts/verify_backend_v19.py", root) if (root / "scripts/verify_backend_v19.py").is_file() else None,
        "baseline": {"record_count": BASELINE_RECORD_COUNT, "jsonl_bytes": BASELINE_JSONL_BYTES, "jsonl_sha256": BASELINE_JSONL_SHA256, "csv_lines_including_header": BASELINE_CSV_LINES, "csv_bytes": BASELINE_CSV_BYTES, "csv_sha256": BASELINE_CSV_SHA256, "preserved_byte_identically": True},
        "units17_19_extension": {"record_count": len(bundle["suffix"]), "entity_counts": bundle["counts"], "units": units, "model_identification": MODEL_IDENTIFICATION, "reader_status": "cumulative_html_pdf_reader_bound", "html_status": "cumulative_html_reader_bound", "pdf_status": "cumulative_pdf_reader_bound", "exercise_count": EXTENSION_EXERCISE_COUNT, "source_supplied_solution_count": EXTENSION_SOURCE_SOLUTION_COUNT},
        "inputs": bundle["inputs"],
        "outputs": outputs,
        "reader_closure": closure,
        "combined": {"record_count": BASELINE_RECORD_COUNT + len(bundle["suffix"]), "entity_counts": {kind: Counter(str(record.get("entity_type")) for record in bundle["baseline"] + bundle["suffix"]).get(kind, 0) for kind in sorted(ENTITY_TYPES)}},
        "claims": {"all_ids_unique": True, "all_references_resolve": True, "json_schema_valid": True, "units17_19_authority_solution_media_closure_current": True, "units17_19_translation_receipts_current": True, "units17_19_correction_manifests_current": True, "units17_19_post_correction_math_qa_current": True, "adverse_ledger_backend_correction_closure_current": True, "unit18_loader_alias_build_correction_current": True, "units1_16_public_prefix_byte_identical": True, "cumulative_exercises_394": True, "cumulative_source_supplied_solutions_54": True, "cumulative_reader_all_or_nothing": True, "cumulative_html_present": True, "cumulative_html_manifest_and_qa_current": True, "cumulative_html_browser_runtime_qa_current": True, "cumulative_pdf_present": True, "cumulative_pdf_structural_qa_current": True, "cumulative_pdf_visual_qa_current": True},
    }
    manifest_path = root / "backend/MANIFEST.json"
    manifest_path.write_bytes((json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    print(json.dumps({"status": "pass", "baseline_records": BASELINE_RECORD_COUNT, "added_records": len(bundle["suffix"]), "combined_records": BASELINE_RECORD_COUNT + len(bundle["suffix"]), "entity_counts": bundle["counts"], "jsonl": outputs["records_jsonl"], "csv": outputs["records_csv"], "manifest": binding(manifest_path, root)}, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
