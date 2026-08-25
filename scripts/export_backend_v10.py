#!/usr/bin/env python3
"""Export the additive O011 Units 8--10 semantic backend extension.

The current 1,363-record Units 1--7 JSONL and 1,364-line CSV are an
immutable byte prefix.  This generator appends deterministic records for the
three admitted lecture/worksheet pairs, their exact exercise/solution closure,
file-specific media rights, correction manifests, QA evidence, and artifact
relations.  The cumulative Unit 10 HTML and PDF readers are admitted as one
all-or-nothing closure: the HTML entry/inventory/QA receipt and the PDF plus
its structural and visual QA receipts must all be present and mutually current.
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
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


BASELINE_RECORD_COUNT = 1363
BASELINE_JSONL_BYTES = 812882
BASELINE_JSONL_SHA256 = "d9d51a46b84368f50a211a31263bafe8f1588f8e62a5fa4b496b2ff45903b912"
BASELINE_CSV_LINES = 1364
BASELINE_CSV_BYTES = 288506
BASELINE_CSV_SHA256 = "c301009770e1c523d046585c0c83947cab6f856b32b83890d361a919fed5a958"
EXPECTED_EXTENSION_RECORD_COUNT = 525
EXPECTED_COMBINED_RECORD_COUNT = 1888
WORKFLOW = "o011-export-backend-v10"
MODEL_IDENTIFICATION = "OpenAI Codex gpt-5.6-sol, Ultra"
UNITS = (8, 9, 10)
DEFAULT_TRANSLATION_STATE = "mathematically_reviewed"
EDITION_ID = "o011-edition-brenner-current-20260821"
RESOURCE_ID = "o011-resource-brenner-dg2023"
COURSE_ID = "o011-course-d50"
TEXT_RIGHTS_ID = "o011-rights-brenner-text"
FINAL_PDF_PAGES = 165
FINAL_PDF_PAGE_SIZE = "A4, 595.276 x 841.89 pt"
FINAL_READER_BINDINGS: dict[str, dict[str, Any]] = {
    "html_entry": {
        "path": "output/html/unit-10/index.html",
        "bytes": 710428,
        "sha256": "125688aadaade39ded86fb42adc8bfa74005a7fca66623a4c419c79ab36d52d4",
    },
    "html_manifest": {
        "path": "output/html/unit-10/manifest.json",
        "bytes": 32562,
        "sha256": "c9d6b7ce87feeb7c1621d0ac25e8b4ef3639a2e95140ef4ffe6f330a40b62e8e",
    },
    "html_qa": {
        "path": "qa/unit-10/HTML_READER_QA.json",
        "bytes": 5830,
        "sha256": "b5af7e5e5192b2c19aaeb940907cce58c8340f294d694f130965545d2c1defb9",
    },
    "pdf": {
        "path": "output/pdf/geometri-diferensial-manifold-mulus-hingga-unit-10-id.pdf",
        "bytes": 5733895,
        "sha256": "4eaec807347feeab2b3334056d3109d5ce6e5eb30ed3649a507ae6124049856d",
    },
    "pdf_structural_qa": {
        "path": "qa/unit-10/pdf_structural_qa.json",
        "bytes": 89821,
        "sha256": "81451a5e7f78f63935e758fa3d277db28b9db252c09c6930fc1cea597c9a47d7",
    },
    "pdf_visual_qa": {
        "path": "qa/unit-10/PDF_VISUAL_QA.json",
        "bytes": 4250,
        "sha256": "8781c681152580035dca4552f5a3aa0d54c6003caf0a527ccbf4ca3ca4e6fc4b",
    },
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
EXPECTED_EXTENSION_ENTITY_COUNTS = {
    "artifact": 62,
    "asset": 3,
    "concept": 0,
    "correction": 31,
    "course": 0,
    "edition": 0,
    "program": 0,
    "qa_event": 28,
    "relation": 302,
    "resource": 0,
    "rights": 3,
    "segment": 12,
    "term": 0,
    "unit": 84,
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(record: dict[str, Any]) -> bytes:
    return (json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def binding(path: Path, root: Path) -> dict[str, Any]:
    data = path.read_bytes()
    return {"path": path.relative_to(root).as_posix(), "bytes": len(data), "sha256": sha256_bytes(data)}


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def safe_repo_path(root: Path, relative: str) -> Path:
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise RuntimeError(f"path escapes repository: {relative}") from exc
    return candidate


def marker_slices(text: str, pattern: str) -> list[str]:
    starts = [match.start() for match in re.finditer(pattern, text)]
    return [text[start:starts[i + 1] if i + 1 < len(starts) else len(text)] for i, start in enumerate(starts)]


def slug(value: str) -> str:
    value = value.lower().replace(".", "-")
    return re.sub(r"[^a-z0-9]+", "-", value).strip("-")


def base_record(record_id: str, entity_type: str, checkpoint: str, **fields: Any) -> dict[str, Any]:
    value: dict[str, Any] = {
        "schema": "o011-modular-backend",
        "schema_version": 1,
        "id": record_id,
        "entity_type": entity_type,
        "status": "active",
        "timestamp": checkpoint,
        "workflow": WORKFLOW,
        "supersedes": None,
    }
    value.update(fields)
    return value


def unit_ids(unit: int) -> tuple[str, str, str]:
    tag = f"{unit:02d}"
    unit_id = f"o011-brenner-u{tag}"
    return unit_id, f"{unit_id}-l{tag}", f"{unit_id}-w{tag}"


def extract_correction_ids(value: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "correction_id" and isinstance(item, str):
                found.add(item)
            elif key == "correction_ids" and isinstance(item, list):
                found.update(str(part) for part in item)
            else:
                found.update(extract_correction_ids(item))
    elif isinstance(value, list):
        for item in value:
            found.update(extract_correction_ids(item))
    return found


def contains_binding(value: Any, expected: dict[str, Any]) -> bool:
    """Return true when a nested JSON value contains the exact file binding."""
    if isinstance(value, dict):
        if all(value.get(key) == expected.get(key) for key in ("path", "bytes", "sha256")):
            return True
        return any(contains_binding(item, expected) for item in value.values())
    if isinstance(value, list):
        return any(contains_binding(item, expected) for item in value)
    return False


def correction_record_id(correction_id: str) -> str:
    match = re.search(r"(\d{4})$", correction_id)
    if not match:
        raise RuntimeError(f"correction ID has no four-digit suffix: {correction_id}")
    return f"o011-corr-{match.group(1)}"


def assert_prefix(root: Path) -> tuple[bytes, bytes, list[dict[str, Any]]]:
    jsonl_path = root / "backend/records.jsonl"
    csv_path = root / "backend/records.csv"
    jsonl = jsonl_path.read_bytes()
    lines = jsonl.splitlines(keepends=True)
    if len(lines) < BASELINE_RECORD_COUNT:
        raise RuntimeError("backend has fewer than the immutable 1,363-record prefix")
    jsonl_prefix = b"".join(lines[:BASELINE_RECORD_COUNT])
    if len(jsonl_prefix) != BASELINE_JSONL_BYTES or sha256_bytes(jsonl_prefix) != BASELINE_JSONL_SHA256:
        raise RuntimeError("immutable Units 1--7 JSONL prefix changed")
    csv_bytes = csv_path.read_bytes()
    csv_lines = csv_bytes.splitlines(keepends=True)
    if len(csv_lines) < BASELINE_CSV_LINES:
        raise RuntimeError("backend CSV has fewer than the immutable Units 1--7 prefix")
    csv_prefix = b"".join(csv_lines[:BASELINE_CSV_LINES])
    if len(csv_prefix) != BASELINE_CSV_BYTES or sha256_bytes(csv_prefix) != BASELINE_CSV_SHA256:
        raise RuntimeError("immutable Units 1--7 CSV prefix changed")
    baseline = [json.loads(line.decode("utf-8")) for line in lines[:BASELINE_RECORD_COUNT]]
    return jsonl_prefix, csv_prefix, baseline


def declared_entry_path(entry: dict[str, Any], label: str) -> str:
    path = entry.get("path")
    if not isinstance(path, str) or not path:
        raise RuntimeError(f"missing declared path for {label}")
    return path


def prepare_unit(root: Path, unit: int) -> dict[str, Any]:
    tag = f"{unit:02d}"
    qa_dir = root / f"qa/unit-{tag}"
    preflight_path = qa_dir / "AUTHORITY_PREFLIGHT.json"
    math_path = qa_dir / "POST_CORRECTION_MATH_QA.json"
    if not math_path.is_file():
        raise RuntimeError(f"Unit {unit} is not frozen: missing {math_path.relative_to(root).as_posix()}")
    preflight = load_json(preflight_path)
    math_qa = load_json(math_path)
    if preflight.get("status") != "pass" or preflight.get("unit") != unit:
        raise RuntimeError(f"Unit {unit} authority preflight is not passing")
    if math_qa.get("status") != "pass" or math_qa.get("unit_id") != f"o011-brenner-u{tag}":
        raise RuntimeError(f"Unit {unit} post-correction mathematical QA is not passing/current")

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
    for index, entry in enumerate(manifest_entries, 1):
        relative = declared_entry_path(entry, f"Unit {unit} correction manifest {index}")
        if not relative.startswith("00_control/"):
            raise RuntimeError(f"Unit {unit} correction manifest is outside 00_control: {relative}")
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
        "unit": unit, "tag": tag, "preflight": preflight, "math_qa": math_qa,
        "paths": paths, "bindings": bindings, "solution_indices": solution_indices,
    }
    validate_unit_inputs(root, context)
    return context


def assert_declared_binding(entry: dict[str, Any], actual: dict[str, Any], label: str) -> None:
    for key in ("path", "bytes", "sha256"):
        if entry.get(key) != actual.get(key):
            raise RuntimeError(f"stale {label} binding: {key}")


def validate_unit_inputs(root: Path, context: dict[str, Any]) -> None:
    unit = int(context["unit"])
    tag = str(context["tag"])
    preflight = context["preflight"]
    math_qa = context["math_qa"]
    paths = context["paths"]
    bindings = context["bindings"]
    solution_indices = context["solution_indices"]
    verify = load_json(paths["preflight_verify"])
    if verify.get("status") != "pass" or verify.get("unit") != unit:
        raise RuntimeError(f"Unit {unit} offline authority verification is not passing")
    closure = load_json(paths["solution_closure"])
    structure = preflight.get("structure", {})
    expected = {
        "exercise_count": structure.get("worksheet_exercise_count"),
        "practice_exercise_count": structure.get("worksheet_practice_count"),
        "graded_exercise_count": structure.get("worksheet_graded_count"),
        "point_value_total": structure.get("worksheet_point_total"),
        "supplied_solution_indices": list(solution_indices),
    }
    for key, value in expected.items():
        if closure.get(key) != value:
            raise RuntimeError(f"Unit {unit} solution closure changed: {key}")
    if closure.get("macro_api_agreement") is not True or structure.get("all_hint_fields_blank") is not True:
        raise RuntimeError(f"Unit {unit} solution/hint closure is not admitted")
    qa_closure = math_qa.get("source_closure", {})
    checks = {
        "exercise_count": structure.get("worksheet_exercise_count"),
        "practice_exercise_count": structure.get("worksheet_practice_count"),
        "graded_exercise_count": structure.get("worksheet_graded_count"),
        "point_total": structure.get("worksheet_point_total"),
        "hint_fields_blank": True,
        "supplied_solution_indices": list(solution_indices),
        "media_occurrence_count": preflight.get("media", {}).get("occurrence_count", 0),
    }
    for key, value in checks.items():
        if qa_closure.get(key) != value:
            raise RuntimeError(f"Unit {unit} post-correction source closure changed: {key}")

    authority = math_qa["authority"]
    targets = math_qa["targets"]
    assert_declared_binding(authority["lecture"], bindings["lecture_source"], f"Unit {unit} lecture authority")
    assert_declared_binding(authority["worksheet"], bindings["worksheet_source"], f"Unit {unit} worksheet authority")
    assert_declared_binding(targets["lecture"], bindings["lecture_target"], f"Unit {unit} lecture target")
    assert_declared_binding(targets["worksheet"], bindings["worksheet_target"], f"Unit {unit} worksheet target")
    for label, target_entry, receipt_key in (
        ("lecture", targets["lecture"], "lecture_receipt"),
        ("worksheet", targets["worksheet"], "worksheet_receipt"),
    ):
        declared_receipt_hash = target_entry.get("translation_receipt_sha256")
        if declared_receipt_hash is not None and declared_receipt_hash != bindings[receipt_key]["sha256"]:
            raise RuntimeError(f"Unit {unit} stale {label} translation-receipt binding in mathematical QA")
    authority_solutions = {int(item["exercise"]): item for item in authority.get("supplied_solutions", [])}
    target_solutions = {int(item["exercise"]): item for item in targets.get("supplied_solutions", [])}
    for index in solution_indices:
        assert_declared_binding(authority_solutions[index], bindings[f"solution{index}_source"], f"Unit {unit} solution {index} authority")
        assert_declared_binding(target_solutions[index], bindings[f"solution{index}_target"], f"Unit {unit} solution {index} target")
        declared_receipt_hash = target_solutions[index].get("translation_receipt_sha256")
        if declared_receipt_hash is not None and declared_receipt_hash != bindings[f"solution{index}_receipt"]["sha256"]:
            raise RuntimeError(f"Unit {unit} stale solution {index} translation-receipt binding in mathematical QA")

    receipt_pairs = [("lecture_receipt", "lecture_source", "lecture_target"), ("worksheet_receipt", "worksheet_source", "worksheet_target")]
    receipt_pairs.extend((f"solution{i}_receipt", f"solution{i}_source", f"solution{i}_target") for i in solution_indices)
    for receipt_key, source_key, target_key in receipt_pairs:
        receipt = load_json(paths[receipt_key])
        if receipt.get("status") != "pass":
            raise RuntimeError(f"Unit {unit} failed translation receipt: {receipt_key}")
        if receipt.get("source_sha256") != bindings[source_key]["sha256"] or receipt.get("source_bytes") != bindings[source_key]["bytes"]:
            raise RuntimeError(f"Unit {unit} stale source in {receipt_key}")
        if receipt.get("target_sha256") != bindings[target_key]["sha256"] or receipt.get("target_bytes") != bindings[target_key]["bytes"]:
            raise RuntimeError(f"Unit {unit} stale target in {receipt_key}")

    declared_manifest_bindings = math_qa.get("correction_manifests", [])
    manifests: list[dict[str, Any]] = []
    for index, entry in enumerate(declared_manifest_bindings, 1):
        key = f"correction_manifest:{index:02d}"
        assert_declared_binding(entry, bindings[key], f"Unit {unit} correction manifest {index}")
        manifests.append(load_json(paths[key]))
    manifest_ids: set[str] = set()
    for manifest in manifests:
        scope = manifest.get("scope")
        allowed_scopes = {bindings["lecture_target"]["path"], bindings["worksheet_target"]["path"]}
        allowed_scopes.update(bindings[f"solution{i}_target"]["path"] for i in solution_indices)
        if scope not in allowed_scopes:
            raise RuntimeError(f"Unit {unit} correction manifest has an unknown scope: {scope}")
        manifest_ids.update(extract_correction_ids(manifest))
    declared_ids = {str(value) for value in math_qa.get("declared_corrections", [])}
    if manifest_ids != declared_ids:
        raise RuntimeError(f"Unit {unit} correction-ID closure differs between manifests and mathematical QA")
    if any(int(re.search(r"(\d{4})$", value).group(1)) <= 72 for value in declared_ids):
        raise RuntimeError(f"Unit {unit} correction IDs collide with the Units 1--7 prefix")

    for asset in preflight.get("media", {}).get("assets", []):
        actual = bindings[f"media:{asset['filename']}"]
        if actual["bytes"] != asset.get("bytes") or actual["sha256"] != asset.get("sha256"):
            raise RuntimeError(f"Unit {unit} media binding changed: {asset['filename']}")
        if asset.get("rights_critical_fields_match") is not True:
            raise RuntimeError(f"Unit {unit} media rights are not admitted: {asset['filename']}")

    lecture_source = paths["lecture_source"].read_text(encoding="utf-8")
    lecture_target = paths["lecture_target"].read_text(encoding="utf-8")
    worksheet_source = paths["worksheet_source"].read_text(encoding="utf-8")
    worksheet_target = paths["worksheet_target"].read_text(encoding="utf-8")
    actual_counts = {
        "lecture_section_count": (len(marker_slices(lecture_source, r"\\zwischenueberschrift\{")), len(marker_slices(lecture_target, r"\\zwischenueberschrift\{"))),
        "worksheet_section_count": (len(marker_slices(worksheet_source, r"\\zwischenueberschrift\{")), len(marker_slices(worksheet_target, r"\\zwischenueberschrift\{"))),
        "worksheet_exercise_count": (len(marker_slices(worksheet_source, r"\\inputaufgabe(?:gibtloesung)?")), len(marker_slices(worksheet_target, r"\\inputaufgabe(?:gibtloesung)?"))),
    }
    for key, pair in actual_counts.items():
        if pair[0] != pair[1] or pair[0] != structure.get(key):
            raise RuntimeError(f"Unit {unit} source/target topology changed: {key}={pair}")


def reader_closure_manifest(context: dict[str, Any]) -> dict[str, Any]:
    """Return the exact cumulative-reader closure represented by this export."""
    if not context.get("reader_bound"):
        return {"status": "not_bound_by_semantic_backend_export"}
    bindings = context["bindings"]
    return {
        "status": "cumulative_html_pdf_reader_bound",
        "html": {
            "entry": bindings["html_entry"],
            "manifest": bindings["html_manifest"],
            "qa": bindings["html_qa"],
        },
        "pdf": {
            "artifact": bindings["pdf"],
            "pages": FINAL_PDF_PAGES,
            "page_size": FINAL_PDF_PAGE_SIZE,
            "structural_qa": bindings["pdf_structural_qa"],
            "visual_qa": bindings["pdf_visual_qa"],
        },
    }


def prepare_reader_closure(root: Path, context: dict[str, Any]) -> None:
    """Bind the cumulative HTML/PDF surfaces only when all six files pass."""
    candidates = {key: root / value["path"] for key, value in FINAL_READER_BINDINGS.items()}
    present = {key: path.is_file() for key, path in candidates.items()}
    if any(present.values()) and not all(present.values()):
        missing = [key for key, value in present.items() if not value]
        raise RuntimeError("incomplete cumulative HTML/PDF reader closure: " + ", ".join(missing))
    context["reader_bound"] = all(present.values())
    context["html_bound"] = context["reader_bound"]
    context["pdf_bound"] = context["reader_bound"]
    if not context["reader_bound"]:
        return
    reader_bindings = {key: binding(path, root) for key, path in candidates.items()}
    for key, expected in FINAL_READER_BINDINGS.items():
        if reader_bindings[key] != expected:
            raise RuntimeError(f"frozen cumulative reader binding changed: {key}")

    html_manifest = load_json(candidates["html_manifest"])
    html_qa = load_json(candidates["html_qa"])
    if html_manifest.get("workflow") != "o011-export-html-v10":
        raise RuntimeError("unexpected cumulative HTML manifest workflow")
    if html_manifest.get("status") != "partial_edition":
        raise RuntimeError("cumulative HTML manifest does not declare the partial-edition state")
    if html_manifest.get("units") != list(range(1, 11)):
        raise RuntimeError("cumulative HTML manifest does not cover exactly Units 1--10")
    if html_manifest.get("model_identification") != MODEL_IDENTIFICATION:
        raise RuntimeError("cumulative HTML manifest has the wrong model identification")
    if html_qa.get("status") != "pass":
        raise RuntimeError("cumulative HTML reader QA is not passing")
    if not contains_binding(html_qa, reader_bindings["html_entry"]) or not contains_binding(html_qa, reader_bindings["html_manifest"]):
        raise RuntimeError("cumulative HTML QA does not bind the exact entry and manifest bytes")
    manifest_entry = {
        "path": "index.html",
        "bytes": reader_bindings["html_entry"]["bytes"],
        "sha256": reader_bindings["html_entry"]["sha256"],
    }
    if not any(
        isinstance(item, dict) and all(item.get(key) == value for key, value in manifest_entry.items())
        for item in html_manifest.get("files", [])
    ):
        raise RuntimeError("cumulative HTML manifest does not inventory the exact entry bytes")

    structural_qa = load_json(candidates["pdf_structural_qa"])
    if structural_qa.get("workflow") != "o011-through-unit10-pdf-structural-accessibility-qa-v1":
        raise RuntimeError("unexpected cumulative PDF structural-QA workflow")
    if (
        structural_qa.get("passed") is not True
        or structural_qa.get("blockers") not in (None, [])
        or structural_qa.get("verdict") != "PASS_WITH_WARNINGS_AND_DOCUMENTED_LIMITATION"
    ):
        raise RuntimeError("cumulative PDF structural QA is not passing")
    structural_pdf = structural_qa.get("pdf", {})
    if not isinstance(structural_pdf, dict) or not contains_binding(structural_pdf, reader_bindings["pdf"]):
        raise RuntimeError("cumulative PDF structural QA does not bind the exact PDF bytes")
    if not contains_binding(structural_qa.get("execution_binding", {}), reader_bindings["pdf"]):
        raise RuntimeError("cumulative PDF execution binding does not bind the exact PDF bytes")
    if (
        structural_pdf.get("pages") != FINAL_PDF_PAGES
        or structural_pdf.get("all_media_boxes_a4") is not True
        or structural_pdf.get("all_crop_boxes_a4") is not True
        or structural_pdf.get("all_rotations_zero") is not True
    ):
        raise RuntimeError("cumulative PDF structural QA does not prove 165 unrotated A4 pages")

    visual_qa = load_json(candidates["pdf_visual_qa"])
    if visual_qa.get("workflow") != "o011-pdf-visual-qa-v10" or visual_qa.get("status") != "pass":
        raise RuntimeError("cumulative PDF visual QA is not passing")
    visual_surface = visual_qa.get("surface", {})
    if not isinstance(visual_surface, dict) or not contains_binding(visual_surface, reader_bindings["pdf"]):
        raise RuntimeError("cumulative PDF visual QA does not bind the exact PDF bytes")
    if visual_surface.get("pages") != FINAL_PDF_PAGES or visual_surface.get("page_size") != FINAL_PDF_PAGE_SIZE:
        raise RuntimeError("cumulative PDF visual QA does not cover the exact 165-page A4 surface")
    visual_checks = visual_qa.get("checks", {})
    if not isinstance(visual_checks, dict) or not visual_checks or any(value is not True for value in visual_checks.values()):
        raise RuntimeError("cumulative PDF visual QA does not pass every declared check")

    context["paths"].update(candidates)
    context["bindings"].update(reader_bindings)
    context["html_manifest"] = html_manifest
    context["html_qa"] = html_qa
    context["pdf_structural_qa"] = structural_qa
    context["pdf_visual_qa"] = visual_qa


def add_relation(records: list[dict[str, Any]], checkpoint: str, relation_id: str, relation_type: str, from_id: str, to_id: str) -> None:
    records.append(base_record(relation_id, "relation", checkpoint, relation_type=relation_type, from_id=from_id, to_id=to_id))


def media_type(path: str) -> str:
    suffix = Path(path).suffix.lower()
    return {
        ".json": "application/json", ".md": "text/markdown", ".csv": "text/csv", ".html": "text/html",
        ".svg": "image/svg+xml", ".png": "image/png", ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg", ".gif": "image/gif", ".pdf": "application/pdf",
    }.get(suffix, "application/x-tex")


def make_unit_records(context: dict[str, Any], checkpoint: str, state: str) -> list[dict[str, Any]]:
    unit = int(context["unit"])
    tag = str(context["tag"])
    preflight = context["preflight"]
    math_qa = context["math_qa"]
    paths = context["paths"]
    bindings = context["bindings"]
    solution_indices = tuple(context["solution_indices"])
    unit_id, lecture_id, worksheet_id = unit_ids(unit)
    root_authority = preflight["authority"]["pages"]
    solution_meta = {int(item["exercise_index"]): item for item in preflight["solutions"]["exercises"]}
    structure = preflight["structure"]
    records: list[dict[str, Any]] = []
    common = {
        "edition_id": EDITION_ID, "resource_id": RESOURCE_ID,
        "language": "Indonesian", "locale": "id-ID",
        "rights_component_id": TEXT_RIGHTS_ID,
    }
    records.append(base_record(
        unit_id, "unit", checkpoint, **common, order=unit, parent_id=COURSE_ID,
        path=f"source/units/unit-{tag}", source_local_id=f"course-unit-{tag}",
        source_locator=f"Kurs:Differentialgeometrie (Osnabrück 2023)/Vorlesung {unit} + Arbeitsblatt {unit}",
        source_sha256=sha256_bytes(paths["lecture_source"].read_bytes() + paths["worksheet_source"].read_bytes()),
        target_sha256=sha256_bytes(paths["lecture_target"].read_bytes() + paths["worksheet_target"].read_bytes()),
        translation_assistance={"human_and_source_credits_preserved": True, "model": MODEL_IDENTIFICATION, "role": "translation and production assistance under user direction"},
        translation_state=state, unit_kind="lecture_worksheet_pair",
        authority_page_revisions={
            "lecture_root": [root_authority["lecture_root"]["pageid"], root_authority["lecture_root"]["revid"]],
            "lecture_latex": [root_authority["lecture_latex"]["pageid"], root_authority["lecture_latex"]["revid"]],
            "worksheet_root": [root_authority["worksheet_root"]["pageid"], root_authority["worksheet_root"]["revid"]],
            "worksheet_latex": [root_authority["worksheet_latex"]["pageid"], root_authority["worksheet_latex"]["revid"]],
        },
    ))
    records.append(base_record(lecture_id, "unit", checkpoint, **common, order=1, parent_id=unit_id, path=bindings["lecture_target"]["path"], source_local_id=f"lecture{tag}", source_locator=root_authority["lecture_root"]["title"], source_sha256=bindings["lecture_source"]["sha256"], target_sha256=bindings["lecture_target"]["sha256"], revid=root_authority["lecture_root"]["revid"], pageid=root_authority["lecture_root"]["pageid"], unit_kind="lecture", translation_state=state))
    records.append(base_record(worksheet_id, "unit", checkpoint, **common, order=2, parent_id=unit_id, path=bindings["worksheet_target"]["path"], source_local_id=f"worksheet{tag}", source_locator=root_authority["worksheet_root"]["title"], source_sha256=bindings["worksheet_source"]["sha256"], target_sha256=bindings["worksheet_target"]["sha256"], revid=root_authority["worksheet_root"]["revid"], pageid=root_authority["worksheet_root"]["pageid"], unit_kind="worksheet", translation_state=state))

    lecture_source_sections = marker_slices(paths["lecture_source"].read_text(encoding="utf-8"), r"\\zwischenueberschrift\{")
    lecture_target_sections = marker_slices(paths["lecture_target"].read_text(encoding="utf-8"), r"\\zwischenueberschrift\{")
    worksheet_source_sections = marker_slices(paths["worksheet_source"].read_text(encoding="utf-8"), r"\\zwischenueberschrift\{")
    worksheet_target_sections = marker_slices(paths["worksheet_target"].read_text(encoding="utf-8"), r"\\zwischenueberschrift\{")
    for index, (source_part, target_part) in enumerate(zip(lecture_source_sections, lecture_target_sections), 1):
        records.append(base_record(f"{lecture_id}-s{index:02d}", "segment", checkpoint, **common, order=index, parent_id=lecture_id, path=f"{bindings['lecture_target']['path']}#section-{index}", source_local_id=f"lecture{tag}:section:{index}", source_locator=f"{root_authority['lecture_root']['title']}#section-{index}", source_sha256=sha256_bytes(source_part.encode()), target_sha256=sha256_bytes(target_part.encode()), segment_kind="lecture_section", translation_state=state))
    for index, (source_part, target_part) in enumerate(zip(worksheet_source_sections, worksheet_target_sections), 1):
        records.append(base_record(f"{worksheet_id}-s{index:02d}", "segment", checkpoint, **common, order=index, parent_id=worksheet_id, path=f"{bindings['worksheet_target']['path']}#section-{index}", source_local_id=f"worksheet{tag}:section:{index}", source_locator=f"{root_authority['worksheet_root']['title']}#section-{index}", source_sha256=sha256_bytes(source_part.encode()), target_sha256=sha256_bytes(target_part.encode()), segment_kind="worksheet_section", translation_state=state))

    exercise_source_parts = marker_slices(paths["worksheet_source"].read_text(encoding="utf-8"), r"\\inputaufgabe(?:gibtloesung)?")
    exercise_target_parts = marker_slices(paths["worksheet_target"].read_text(encoding="utf-8"), r"\\inputaufgabe(?:gibtloesung)?")
    for index, (source_part, target_part) in enumerate(zip(exercise_source_parts, exercise_target_parts), 1):
        meta = solution_meta[index]
        point = meta.get("point_value")
        records.append(base_record(f"{worksheet_id}-e{index:03d}", "unit", checkpoint, **common, order=index, parent_id=worksheet_id, path=f"{bindings['worksheet_target']['path']}#exercise-{index}", source_local_id=f"worksheet{tag}:exercise:{index}", source_locator=meta.get("task_title"), source_display_id=f"{unit}.{index}", source_sha256=sha256_bytes(source_part.encode()), target_sha256=sha256_bytes(target_part.encode()), authority_task_title=meta.get("task_title"), candidate_solution_title=meta.get("solution_title"), authority_solution_status="source_supplied" if index in solution_indices else "source_absent", has_authority_solution=index in solution_indices, source_solution_checked=True, hint_present=bool(meta.get("hint_field")), graded=point is not None, point_value=point, unit_kind="exercise", translation_state=state))
    for index in solution_indices:
        meta = solution_meta[index]
        exercise_id = f"{worksheet_id}-e{index:03d}"
        records.append(base_record(f"{exercise_id}-solution", "unit", checkpoint, **common, order=1, parent_id=exercise_id, path=bindings[f"solution{index}_target"]["path"], source_local_id=f"worksheet{tag}:exercise:{index}:solution", source_locator=meta.get("solution_title"), source_sha256=bindings[f"solution{index}_source"]["sha256"], target_sha256=bindings[f"solution{index}_target"]["sha256"], pageid=meta.get("pageid"), revid=meta.get("revid"), unit_kind="source_supplied_solution", translation_state=state))

    asset_ids: list[str] = []
    rights_ids: list[str] = []
    for index, asset in enumerate(preflight.get("media", {}).get("assets", []), 1):
        asset_id = f"o011-asset-file-u{tag}-{slug(asset['filename'])}"
        rights_id = f"o011-rights-media-u{tag}-{index:02d}"
        occurrence_surfaces = [str(item.get("surface", "")) for item in asset.get("occurrences", [])]
        parent = lecture_id if any(value.startswith("lecture") for value in occurrence_surfaces) else worksheet_id
        asset_ids.append(asset_id); rights_ids.append(rights_id)
        records.append(base_record(rights_id, "rights", checkpoint, source_local_id=f"Commons pageid:{asset['commons_pageid']}/revid:{asset['commons_lastrevid']}", component_scope=bindings[f"media:{asset['filename']}"]["path"], evidence_path=bindings["preflight"]["path"], evidence_sha256=bindings["preflight"]["sha256"], attribution=asset.get("artist_text"), credit=asset.get("credit_text"), license=asset.get("license"), license_url=asset.get("license_url"), redistribution_permitted=True, release_asset=True, rights_status="admitted_component_license"))
        records.append(base_record(asset_id, "asset", checkpoint, parent_id=parent, order=index, path=bindings[f"media:{asset['filename']}"]["path"], source_local_id=f"File:{asset['filename']}", source_locator=asset.get("description_url"), source_sha256=bindings[f"media:{asset['filename']}"]["sha256"], expected_bytes=bindings[f"media:{asset['filename']}"]["bytes"], binary_present=True, mime=asset.get("mime"), commons_pageid=asset.get("commons_pageid"), commons_lastrevid=asset.get("commons_lastrevid"), commons_sha1=asset.get("commons_sha1"), rights_component_id=rights_id, occurrence_surfaces=occurrence_surfaces))

    artifact_ids: list[tuple[str, str, str]] = []
    def add_artifact(artifact_id: str, path_key: str, parent_id: str, kind: str, language: str | None = None, locale: str | None = None, source_key: str | None = None, extra_fields: dict[str, Any] | None = None) -> None:
        target = bindings[path_key]
        fields: dict[str, Any] = {"artifact_kind": kind, "bytes": target["bytes"], "path": target["path"], "media_type": media_type(target["path"]), "parent_id": parent_id, "rights_component_id": TEXT_RIGHTS_ID, "component_rights_ids": [TEXT_RIGHTS_ID], "target_sha256": target["sha256"], "language": language, "locale": locale}
        if source_key:
            fields["source_sha256"] = bindings[source_key]["sha256"]
        elif language == "German":
            fields["source_sha256"] = target["sha256"]
            fields["target_sha256"] = None
        if extra_fields:
            fields.update(extra_fields)
        records.append(base_record(artifact_id, "artifact", checkpoint, **fields, translation_state=state if language == "Indonesian" else "source_frozen" if language == "German" else state))
        artifact_ids.append((artifact_id, parent_id, "represents" if language == "Indonesian" else "evidences"))

    add_artifact(f"o011-artifact-u{tag}-l{tag}-source-tex", "lecture_source", lecture_id, "frozen_authority_tex_fragment", "German", "de-DE")
    add_artifact(f"o011-artifact-u{tag}-l{tag}-tex", "lecture_target", lecture_id, "translated_tex_fragment", "Indonesian", "id-ID", "lecture_source")
    add_artifact(f"o011-artifact-u{tag}-w{tag}-source-tex", "worksheet_source", worksheet_id, "frozen_authority_tex_fragment", "German", "de-DE")
    add_artifact(f"o011-artifact-u{tag}-w{tag}-tex", "worksheet_target", worksheet_id, "translated_tex_fragment", "Indonesian", "id-ID", "worksheet_source")
    for index in solution_indices:
        solution_id = f"{worksheet_id}-e{index:03d}-solution"
        add_artifact(f"o011-artifact-u{tag}-w{tag}-e{index:03d}-solution-source-tex", f"solution{index}_source", solution_id, "frozen_authority_tex_fragment", "German", "de-DE")
        add_artifact(f"o011-artifact-u{tag}-w{tag}-e{index:03d}-solution-tex", f"solution{index}_target", solution_id, "translated_tex_fragment", "Indonesian", "id-ID", f"solution{index}_source")
    evidence_artifacts = [
        (f"o011-artifact-u{tag}-authority-preflight", "preflight", "authority_source_solution_media_closure"),
        (f"o011-artifact-u{tag}-authority-preflight-verify", "preflight_verify", "offline_authority_verification_receipt"),
        (f"o011-artifact-u{tag}-solution-closure", "solution_closure", "source_solution_hint_point_closure"),
        (f"o011-artifact-u{tag}-math-qa", "math_qa", "post_correction_mathematical_qa_receipt"),
        (f"o011-artifact-u{tag}-lecture-translation-receipt", "lecture_receipt", "translation_structure_receipt"),
        (f"o011-artifact-u{tag}-worksheet-translation-receipt", "worksheet_receipt", "translation_structure_receipt"),
    ]
    for index in solution_indices:
        evidence_artifacts.append((f"o011-artifact-u{tag}-solution{index}-translation-receipt", f"solution{index}_receipt", "translation_structure_receipt"))
    for index in range(1, len(math_qa["correction_manifests"]) + 1):
        key = f"correction_manifest:{index:02d}"
        evidence_artifacts.append((f"o011-artifact-u{tag}-correction-manifest-{index:02d}", key, "translation_correction_manifest"))
    for artifact_id, key, kind in evidence_artifacts:
        add_artifact(artifact_id, key, unit_id, kind)
    if context.get("reader_bound"):
        add_artifact("o011-artifact-u10-html-entry", "html_entry", EDITION_ID, "cumulative_semantic_html_reader_entry", "Indonesian", "id-ID")
        add_artifact("o011-artifact-u10-html-manifest", "html_manifest", EDITION_ID, "cumulative_semantic_html_inventory")
        add_artifact(
            "o011-artifact-u10-html-qa",
            "html_qa",
            unit_id,
            "cumulative_semantic_html_qa_receipt",
            extra_fields={"reader_closure": reader_closure_manifest(context)},
        )

    qa_events: list[dict[str, Any]] = []
    def qa(qid: str, target_id: str, receipt_key: str, kind: str, artifact_id: str, values: dict[str, Any] | None = None) -> None:
        event = base_record(qid, "qa_event", checkpoint, parent_id=unit_id, target_id=target_id, receipt_path=bindings[receipt_key]["path"], evidence_sha256=bindings[receipt_key]["sha256"], result="pass", qa_kind=kind, values=values or {}, artifact_id=artifact_id, translation_state=state)
        records.append(event); qa_events.append(event)
    qa(f"o011-qa-unit{tag}-authority-preflight", unit_id, "preflight", "authority_source_solution_media_closure", f"o011-artifact-u{tag}-authority-preflight")
    qa(f"o011-qa-unit{tag}-authority-preflight-verify", unit_id, "preflight_verify", "offline_authority_verification", f"o011-artifact-u{tag}-authority-preflight-verify")
    qa(f"o011-qa-unit{tag}-solution-closure", worksheet_id, "solution_closure", "solution_hint_point_closure", f"o011-artifact-u{tag}-solution-closure", {"exercise_count": structure["worksheet_exercise_count"], "graded_point_total": structure["worksheet_point_total"], "hint_indices": [], "supplied_solution_indices": list(solution_indices), "missing_solution_indices": [i for i in range(1, structure["worksheet_exercise_count"] + 1) if i not in solution_indices]})
    qa(f"o011-qa-unit{tag}-lecture-translation", lecture_id, "lecture_receipt", "translation_structure", f"o011-artifact-u{tag}-lecture-translation-receipt")
    qa(f"o011-qa-unit{tag}-worksheet-translation", worksheet_id, "worksheet_receipt", "translation_structure", f"o011-artifact-u{tag}-worksheet-translation-receipt")
    for index in solution_indices:
        qa(f"o011-qa-unit{tag}-solution{index}-translation", f"{worksheet_id}-e{index:03d}-solution", f"solution{index}_receipt", "translation_structure", f"o011-artifact-u{tag}-solution{index}-translation-receipt")
    qa(f"o011-qa-unit{tag}-post-correction-math", unit_id, "math_qa", "post_correction_mathematical_and_topology_audit", f"o011-artifact-u{tag}-math-qa")
    qa(f"o011-qa-unit{tag}-correction-closure", unit_id, "math_qa", "declared_correction_closure", f"o011-artifact-u{tag}-math-qa", {"correction_ids": math_qa["declared_corrections"]})
    if context.get("reader_bound"):
        qa(
            "o011-qa-unit10-html-reader",
            EDITION_ID,
            "html_qa",
            "cumulative_semantic_html_pdf_reader",
            "o011-artifact-u10-html-entry",
            reader_closure_manifest(context),
        )

    scope_targets = {bindings["lecture_target"]["path"]: lecture_id, bindings["worksheet_target"]["path"]: worksheet_id}
    target_receipts = {lecture_id: bindings["lecture_receipt"], worksheet_id: bindings["worksheet_receipt"]}
    for index in solution_indices:
        solution_id = f"{worksheet_id}-e{index:03d}-solution"
        scope_targets[bindings[f"solution{index}_target"]["path"]] = solution_id
        target_receipts[solution_id] = bindings[f"solution{index}_receipt"]
    manifests: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for index in range(1, len(math_qa["correction_manifests"]) + 1):
        key = f"correction_manifest:{index:02d}"
        manifests.append((load_json(paths[key]), bindings[key]))
    for correction_id in sorted(math_qa["declared_corrections"]):
        involved = [(manifest, manifest_binding) for manifest, manifest_binding in manifests if correction_id in extract_correction_ids(manifest)]
        target_ids = sorted({scope_targets[str(manifest["scope"])] for manifest, _ in involved})
        descriptions: list[str] = []
        for manifest, _ in involved:
            for item in manifest.get("prose_only_corrections", []):
                ids = {str(item.get("correction_id"))} | {str(value) for value in item.get("correction_ids", [])}
                if correction_id in ids and item.get("change"):
                    descriptions.append(str(item["change"]))
            if correction_id in extract_correction_ids(manifest) and manifest.get("translation_only_deltas"):
                descriptions.extend(str(value) for value in manifest["translation_only_deltas"])
        if not descriptions:
            surfaces = sorted({
                str(delta.get("surface"))
                for manifest, _ in involved
                for group in ("allowed_deltas", "evidence_only_deltas")
                for delta in manifest.get(group, [])
                if correction_id in extract_correction_ids(delta)
            })
            descriptions.append("Declared and verified target correction on protected surfaces: " + ", ".join(surfaces))
        records.append(base_record(correction_record_id(correction_id), "correction", checkpoint, source_local_id=correction_id, severity="P2", description=" ".join(dict.fromkeys(descriptions)), disposition="Corrected in the Indonesian target and verified against the frozen authority", correction_status="corrected_in_target", upstream_report_disposition="deferred_until_full_corpus", target_ids=target_ids, target_bindings=[{**binding_value_for_target(target_id, target_receipts, bindings, lecture_id, worksheet_id, solution_indices), "target_id": target_id} for target_id in target_ids], correction_manifests=[manifest_binding for _, manifest_binding in involved], validation_bindings=[target_receipts[target_id] for target_id in target_ids], post_correction_qa_binding=bindings["math_qa"]))

    previous_id = "o011-brenner-u07" if unit == 8 else f"o011-brenner-u{unit - 1:02d}"
    add_relation(records, checkpoint, f"o011-rel-u{unit - 1:02d}-precedes-u{tag}", "precedes", previous_id, unit_id)
    add_relation(records, checkpoint, f"o011-rel-u{tag}-has-part-l{tag}", "has_part", unit_id, lecture_id)
    add_relation(records, checkpoint, f"o011-rel-u{tag}-has-part-w{tag}", "has_part", unit_id, worksheet_id)
    for prefix, parent, count in [(f"l{tag}-s", lecture_id, structure["lecture_section_count"]), (f"w{tag}-s", worksheet_id, structure["worksheet_section_count"])]:
        for index in range(1, count + 1):
            section_id = f"{unit_id}-{prefix}{index:02d}"
            add_relation(records, checkpoint, f"o011-rel-u{tag}-{prefix}{index:02d}-has-part", "has_part", parent, section_id)
            if index > 1:
                add_relation(records, checkpoint, f"o011-rel-u{tag}-{prefix}{index - 1:02d}-precedes-{index:02d}", "precedes", f"{unit_id}-{prefix}{index - 1:02d}", section_id)
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
    for artifact_id, target_id, relation_type in artifact_ids:
        add_relation(records, checkpoint, f"o011-rel-{artifact_id}-{relation_type}-target", relation_type, artifact_id, target_id)
    for correction_id in math_qa["declared_corrections"]:
        correction_record = next(record for record in records if record["id"] == correction_record_id(correction_id))
        for position, target_id in enumerate(correction_record["target_ids"], 1):
            add_relation(records, checkpoint, f"o011-rel-{correction_record['id']}-corrects-{position:02d}", "corrects", str(correction_record["id"]), str(target_id))
    for event in qa_events:
        add_relation(records, checkpoint, f"o011-rel-{event['id']}-evidences-target", "evidences", str(event["id"]), str(event["target_id"]))
    return records


def binding_value_for_target(target_id: str, receipts: dict[str, dict[str, Any]], bindings: dict[str, dict[str, Any]], lecture_id: str, worksheet_id: str, solution_indices: tuple[int, ...]) -> dict[str, Any]:
    if target_id == lecture_id:
        return dict(bindings["lecture_target"])
    if target_id == worksheet_id:
        return dict(bindings["worksheet_target"])
    for index in solution_indices:
        if target_id.endswith(f"-e{index:03d}-solution"):
            return dict(bindings[f"solution{index}_target"])
    raise RuntimeError(f"unknown correction target: {target_id}")


def validate_records(baseline: list[dict[str, Any]], added: list[dict[str, Any]], schema: dict[str, Any]) -> dict[str, int]:
    added.sort(key=lambda item: str(item["id"]))
    all_records = baseline + added
    if len({str(record["id"]) for record in all_records}) != len(all_records):
        raise RuntimeError("combined backend IDs are not unique")
    all_ids = {str(record["id"]) for record in all_records}
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors: list[str] = []
    for record in all_records:
        errors.extend(f"{record['id']}: {error.message}" for error in validator.iter_errors(record))
    if errors:
        raise RuntimeError("JSON Schema validation failed: " + "; ".join(errors[:10]))
    for record in added:
        for key in ("parent_id", "resource_id", "edition_id", "rights_component_id", "target_id", "artifact_id", "from_id", "to_id"):
            value = record.get(key)
            if value is not None and str(value) not in all_ids:
                raise RuntimeError(f"unresolved {key} on {record['id']}: {value}")
        for key in ("component_rights_ids", "target_ids"):
            for value in record.get(key, []) or []:
                if str(value) not in all_ids:
                    raise RuntimeError(f"unresolved {key} on {record['id']}: {value}")
    counts = Counter(str(record.get("entity_type")) for record in added)
    return {kind: counts.get(kind, 0) for kind in sorted(ENTITY_TYPES)}


def prepare_bundle(root: Path, checkpoint: str, state: str) -> dict[str, Any]:
    jsonl_prefix, csv_prefix, baseline = assert_prefix(root)
    contexts = [prepare_unit(root, unit) for unit in UNITS]
    prepare_reader_closure(root, contexts[-1])
    suffix: list[dict[str, Any]] = []
    for context in contexts:
        unit_records = make_unit_records(context, checkpoint, state)
        context["records"] = unit_records
        suffix.extend(unit_records)
    counts = validate_records(baseline, suffix, load_json(root / "backend/schema/o011-record-v1.schema.json"))
    if len(suffix) != EXPECTED_EXTENSION_RECORD_COUNT or BASELINE_RECORD_COUNT + len(suffix) != EXPECTED_COMBINED_RECORD_COUNT:
        raise RuntimeError("frozen Units 8--10 semantic record census changed")
    if counts != EXPECTED_EXTENSION_ENTITY_COUNTS:
        raise RuntimeError("frozen Units 8--10 entity census changed")
    inputs: dict[str, dict[str, Any]] = {"schema": binding(root / "backend/schema/o011-record-v1.schema.json", root)}
    for context in contexts:
        for key, value in context["bindings"].items():
            inputs[f"u{context['tag']}:{key}"] = value
    return {"jsonl_prefix": jsonl_prefix, "csv_prefix": csv_prefix, "baseline": baseline, "contexts": contexts, "suffix": suffix, "counts": counts, "inputs": inputs}


def unit_manifest(context: dict[str, Any], state: str) -> dict[str, Any]:
    unit = int(context["unit"]); tag = str(context["tag"])
    structure = context["preflight"]["structure"]
    solutions = list(context["solution_indices"])
    unit_records = context["records"]
    counts = Counter(str(record.get("entity_type")) for record in unit_records)
    return {
        "unit_id": unit_ids(unit)[0], "lecture_sections": structure["lecture_section_count"],
        "worksheet_sections": structure["worksheet_section_count"], "exercise_count": structure["worksheet_exercise_count"],
        "practice_exercise_count": structure["worksheet_practice_count"], "graded_exercise_count": structure["worksheet_graded_count"],
        "graded_point_total": structure["worksheet_point_total"], "hint_indices": [],
        "source_solution_indices": solutions, "source_solution_absent_indices": [i for i in range(1, structure["worksheet_exercise_count"] + 1) if i not in solutions],
        "asset_count": len(context["preflight"].get("media", {}).get("assets", [])),
        "correction_ids": list(context["math_qa"]["declared_corrections"]), "translation_state": state,
        "entity_counts": {kind: counts.get(kind, 0) for kind in sorted(ENTITY_TYPES)},
        "reader_status": "cumulative_html_pdf_reader_bound" if context.get("reader_bound") else "not_bound",
        "html_status": "cumulative_html_reader_bound" if context.get("reader_bound") else "not_bound",
        "pdf_status": "cumulative_pdf_reader_bound" if context.get("reader_bound") else "not_bound",
        **(
            {
                "html_entry": context["bindings"]["html_entry"],
                "html_manifest": context["bindings"]["html_manifest"],
                "html_qa": context["bindings"]["html_qa"],
                "pdf": context["bindings"]["pdf"],
                "pdf_structural_qa": context["bindings"]["pdf_structural_qa"],
                "pdf_visual_qa": context["bindings"]["pdf_visual_qa"],
            }
            if context.get("reader_bound")
            else {}
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--translation-state", default=DEFAULT_TRANSLATION_STATE)
    parser.add_argument("--check-only", action="store_true", help="validate and census live inputs without changing backend outputs")
    args = parser.parse_args()
    if args.translation_state not in {"translated", "structurally_verified", "mathematically_reviewed", "language_reviewed", "built", "visually_checked"}:
        raise RuntimeError("unsupported Units 8--10 translation state")
    root = args.root.resolve()
    bundle = prepare_bundle(root, args.checkpoint, args.translation_state)
    reader_bound = bool(bundle["contexts"][-1].get("reader_bound"))
    if args.check_only:
        print(json.dumps({"status": "pass", "check_only": True, "baseline_records": BASELINE_RECORD_COUNT, "prospective_added_records": len(bundle["suffix"]), "prospective_combined_records": BASELINE_RECORD_COUNT + len(bundle["suffix"]), "entity_counts": bundle["counts"], "units": {context["tag"]: unit_manifest(context, args.translation_state) for context in bundle["contexts"]}}, ensure_ascii=False, sort_keys=True))
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
        "schema_version": 1, "workflow": WORKFLOW, "checkpoint": args.checkpoint,
        "generator": binding(root / "scripts/export_backend_v10.py", root),
        "verifier": binding(root / "scripts/verify_backend_v10.py", root) if (root / "scripts/verify_backend_v10.py").is_file() else None,
        "baseline": {"record_count": BASELINE_RECORD_COUNT, "jsonl_bytes": BASELINE_JSONL_BYTES, "jsonl_sha256": BASELINE_JSONL_SHA256, "csv_lines_including_header": BASELINE_CSV_LINES, "csv_bytes": BASELINE_CSV_BYTES, "csv_sha256": BASELINE_CSV_SHA256, "preserved_byte_identically": True},
        "units08_10_extension": {
            "record_count": len(bundle["suffix"]), "entity_counts": bundle["counts"],
            "units": {context["tag"]: unit_manifest(context, args.translation_state) for context in bundle["contexts"]},
            "model_identification": MODEL_IDENTIFICATION,
            "reader_status": "cumulative_html_pdf_reader_bound" if reader_bound else "not_bound_by_semantic_backend_export",
            "html_status": "cumulative_html_reader_bound" if reader_bound else "not_bound_by_semantic_backend_export",
            "pdf_status": "cumulative_pdf_reader_bound" if reader_bound else "not_bound_by_semantic_backend_export",
        },
        "inputs": bundle["inputs"], "outputs": outputs,
        "reader_closure": reader_closure_manifest(bundle["contexts"][-1]),
        "combined": {"record_count": BASELINE_RECORD_COUNT + len(bundle["suffix"]), "entity_counts": {kind: Counter(str(record.get("entity_type")) for record in bundle["baseline"] + bundle["suffix"]).get(kind, 0) for kind in sorted(ENTITY_TYPES)}},
        "claims": {"all_ids_unique": True, "all_references_resolve": True, "json_schema_valid": True, "units08_10_authority_solution_media_closure_current": True, "units08_10_translation_receipts_current": True, "units08_10_correction_manifests_current": True, "units08_10_post_correction_math_qa_current": True, "units1_7_prefix_byte_identical": True, "cumulative_reader_all_or_nothing": True, "cumulative_html_present": reader_bound, "cumulative_html_manifest_and_qa_current": reader_bound, "cumulative_pdf_present": reader_bound, "cumulative_pdf_structural_qa_current": reader_bound, "cumulative_pdf_visual_qa_current": reader_bound},
    }
    manifest_path = root / "backend/MANIFEST.json"
    manifest_path.write_bytes((json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    print(json.dumps({"status": "pass", "baseline_records": BASELINE_RECORD_COUNT, "added_records": len(bundle["suffix"]), "combined_records": BASELINE_RECORD_COUNT + len(bundle["suffix"]), "entity_counts": bundle["counts"], "jsonl": outputs["records_jsonl"], "csv": outputs["records_csv"], "manifest": binding(manifest_path, root)}, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
