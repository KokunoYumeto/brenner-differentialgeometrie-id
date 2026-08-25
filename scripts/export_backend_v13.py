#!/usr/bin/env python3
"""Export the additive O011 Units 11--13 semantic backend extension.

The verified Units 1--10 JSONL and CSV are immutable byte prefixes.  This
generator appends deterministic records for Units 11--13 and admits the
cumulative Unit 13 HTML/PDF readers only when their complete QA closure is
present and current.  The v10 implementation is imported as an immutable
library for the already-tested per-unit record model; no v10 file is changed.
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


BASELINE_RECORD_COUNT = 1888
BASELINE_JSONL_BYTES = 1138347
BASELINE_JSONL_SHA256 = "ef614f1d6f74357b65644e06d5667870339f9ee6712bdde028e8b3923e16d132"
BASELINE_CSV_LINES = 1889
BASELINE_CSV_BYTES = 414039
BASELINE_CSV_SHA256 = "409c3d79d99ac17cbf4bf597763221681db00d4fd4c3f7a8cc84c6cd98c9a753"
EXPECTED_EXTENSION_RECORD_COUNT = 716
EXPECTED_COMBINED_RECORD_COUNT = 2604
EXPECTED_EXTENSION_ENTITY_COUNTS = {
    "artifact": 87,
    "asset": 4,
    "concept": 0,
    "correction": 44,
    "course": 0,
    "edition": 0,
    "program": 0,
    "qa_event": 36,
    "relation": 414,
    "resource": 0,
    "rights": 4,
    "segment": 14,
    "term": 0,
    "unit": 113,
}
EXPECTED_UNIT_CENSUS: dict[int, dict[str, Any]] = {
    11: {
        "lecture_sections": 2,
        "worksheet_sections": 2,
        "exercises": 39,
        "practice": 33,
        "graded": 6,
        "points": 22,
        "solutions": [10, 14],
        "assets": 1,
        "corrections": 10,
        "correction_manifests": 3,
    },
    12: {
        "lecture_sections": 2,
        "worksheet_sections": 1,
        "exercises": 29,
        "practice": 25,
        "graded": 4,
        "points": 15,
        "solutions": [11, 12],
        "assets": 2,
        "corrections": 22,
        "correction_manifests": 4,
    },
    13: {
        "lecture_sections": 5,
        "worksheet_sections": 2,
        "exercises": 24,
        "practice": 19,
        "graded": 5,
        "points": 20,
        "solutions": [1, 10, 11, 16, 18, 19, 21, 22],
        "assets": 1,
        "corrections": 12,
        "correction_manifests": 8,
    },
}

WORKFLOW = "o011-export-backend-v13"
MODEL_IDENTIFICATION = v10.MODEL_IDENTIFICATION
UNITS = (11, 12, 13)
DEFAULT_TRANSLATION_STATE = "mathematically_reviewed"
EDITION_ID = v10.EDITION_ID
RESOURCE_ID = v10.RESOURCE_ID
COURSE_ID = v10.COURSE_ID
TEXT_RIGHTS_ID = v10.TEXT_RIGHTS_ID
CSV_FIELDS = v10.CSV_FIELDS
ENTITY_TYPES = v10.ENTITY_TYPES
FINAL_PDF_PAGE_SIZE = "A4, 595.276 x 841.89 pt"
FINAL_READER_PATHS = {
    "html_entry": "output/html/unit-13/index.html",
    "html_manifest": "output/html/unit-13/manifest.json",
    "html_qa": "qa/unit-13/HTML_READER_QA.json",
    "pdf": "output/pdf/geometri-diferensial-manifold-mulus-hingga-unit-13-id.pdf",
    "pdf_structural_qa": "qa/unit-13/pdf_structural_qa.json",
    "pdf_visual_qa": "qa/unit-13/PDF_VISUAL_QA.json",
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


def assert_prefix(root: Path) -> tuple[bytes, bytes, list[dict[str, Any]]]:
    jsonl = (root / "backend/records.jsonl").read_bytes()
    jsonl_lines = jsonl.splitlines(keepends=True)
    if len(jsonl_lines) < BASELINE_RECORD_COUNT:
        raise RuntimeError("backend has fewer than the immutable 1,888-record Units 1--10 prefix")
    jsonl_prefix = b"".join(jsonl_lines[:BASELINE_RECORD_COUNT])
    if len(jsonl_prefix) != BASELINE_JSONL_BYTES or sha256_bytes(jsonl_prefix) != BASELINE_JSONL_SHA256:
        raise RuntimeError("immutable Units 1--10 JSONL prefix changed")

    csv_bytes = (root / "backend/records.csv").read_bytes()
    csv_lines = csv_bytes.splitlines(keepends=True)
    if len(csv_lines) < BASELINE_CSV_LINES:
        raise RuntimeError("backend CSV has fewer than the immutable Units 1--10 prefix")
    csv_prefix = b"".join(csv_lines[:BASELINE_CSV_LINES])
    if len(csv_prefix) != BASELINE_CSV_BYTES or sha256_bytes(csv_prefix) != BASELINE_CSV_SHA256:
        raise RuntimeError("immutable Units 1--10 CSV prefix changed")
    baseline = [json.loads(line.decode("utf-8")) for line in jsonl_lines[:BASELINE_RECORD_COUNT]]
    return jsonl_prefix, csv_prefix, baseline


def prepare_unit(root: Path, unit: int) -> dict[str, Any]:
    """Load a frozen unit while allowing its own QA directory as evidence scope."""
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
        "corrections": len(context["math_qa"].get("declared_corrections", [])),
        "correction_manifests": len(context["math_qa"].get("correction_manifests", [])),
    }
    if actual != expected:
        raise RuntimeError(f"frozen Unit {unit} semantic census changed: {actual!r}")


def prepare_reader_closure(root: Path) -> dict[str, Any]:
    paths = {key: root / relative for key, relative in FINAL_READER_PATHS.items()}
    missing = [relative for key, relative in FINAL_READER_PATHS.items() if not paths[key].is_file()]
    if missing:
        raise RuntimeError("cumulative Unit 13 reader closure is incomplete: " + ", ".join(missing))
    bindings = {key: binding(path, root) for key, path in paths.items()}

    html_manifest = load_json(paths["html_manifest"])
    html_qa = load_json(paths["html_qa"])
    if html_manifest.get("workflow") != "o011-export-html-v13" or html_manifest.get("status") != "partial_edition":
        raise RuntimeError("unexpected cumulative Unit 13 HTML manifest workflow/status")
    if html_manifest.get("language") != "id-ID" or html_manifest.get("units") != list(range(1, 14)):
        raise RuntimeError("cumulative HTML manifest does not cover exactly Units 1--13 in id-ID")
    if html_manifest.get("model_identification") != MODEL_IDENTIFICATION:
        raise RuntimeError("cumulative HTML manifest has the wrong model identification")
    if html_qa.get("workflow") != "o011-verify-html-v13" or html_qa.get("status") != "pass":
        raise RuntimeError("cumulative Unit 13 HTML QA is not passing")
    if not contains_binding(html_qa, bindings["html_entry"]) or not contains_binding(html_qa, bindings["html_manifest"]):
        raise RuntimeError("cumulative HTML QA does not bind the exact entry and manifest bytes")
    manifest_entry = {"path": "index.html", "bytes": bindings["html_entry"]["bytes"], "sha256": bindings["html_entry"]["sha256"]}
    if not any(isinstance(item, dict) and all(item.get(key) == value for key, value in manifest_entry.items()) for item in html_manifest.get("files", [])):
        raise RuntimeError("cumulative HTML manifest does not inventory the exact entry bytes")

    structural = load_json(paths["pdf_structural_qa"])
    if structural.get("workflow") != "o011-through-unit13-pdf-structural-accessibility-qa-v1":
        raise RuntimeError("unexpected cumulative Unit 13 PDF structural-QA workflow")
    if structural.get("passed") is not True or structural.get("blockers") not in (None, []):
        raise RuntimeError("cumulative Unit 13 PDF structural QA is not passing")
    structural_pdf = structural.get("pdf", {})
    if not isinstance(structural_pdf, dict) or not contains_binding(structural_pdf, bindings["pdf"]):
        raise RuntimeError("cumulative PDF structural QA does not bind the exact PDF bytes")
    if not contains_binding(structural.get("execution_binding", {}), bindings["pdf"]):
        raise RuntimeError("cumulative PDF execution binding does not bind the exact PDF bytes")
    pages = structural_pdf.get("pages")
    if not isinstance(pages, int) or pages <= 165:
        raise RuntimeError("cumulative Unit 13 PDF page count does not extend the 165-page Unit 10 boundary")
    if any(structural_pdf.get(key) is not True for key in ("all_media_boxes_a4", "all_crop_boxes_a4", "all_rotations_zero")):
        raise RuntimeError("cumulative Unit 13 PDF structural QA does not prove unrotated A4 pages")
    if structural.get("layout", {}).get("centered_body_bounds_passed") is not True:
        raise RuntimeError("cumulative Unit 13 PDF structural QA does not prove centered body bounds")

    visual = load_json(paths["pdf_visual_qa"])
    if visual.get("workflow") != "o011-pdf-visual-qa-v13" or visual.get("status") != "pass":
        raise RuntimeError("cumulative Unit 13 PDF visual QA is not passing")
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
        "pdf_structural_qa": structural,
        "pdf_visual_qa": visual,
        "pages": pages,
    }


def reader_closure_manifest(reader: dict[str, Any]) -> dict[str, Any]:
    bindings = reader["bindings"]
    return {
        "status": "cumulative_html_pdf_reader_bound",
        "through_unit": 13,
        "html": {"entry": bindings["html_entry"], "manifest": bindings["html_manifest"], "qa": bindings["html_qa"]},
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
        ("o011-artifact-u13-html-entry", "html_entry", "cumulative_semantic_html_reader_entry", "Indonesian", "id-ID", "represents"),
        ("o011-artifact-u13-html-manifest", "html_manifest", "cumulative_semantic_html_inventory", None, None, "evidences"),
        ("o011-artifact-u13-html-qa", "html_qa", "cumulative_semantic_html_qa_receipt", None, None, "evidences"),
        ("o011-artifact-u13-pdf", "pdf", "cumulative_a4_pdf_reader", "Indonesian", "id-ID", "represents"),
        ("o011-artifact-u13-pdf-structural-qa", "pdf_structural_qa", "cumulative_pdf_structural_accessibility_qa_receipt", None, None, "evidences"),
        ("o011-artifact-u13-pdf-visual-qa", "pdf_visual_qa", "cumulative_pdf_visual_qa_receipt", None, None, "evidences"),
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
        ("o011-qa-unit13-html-reader", "o011-artifact-u13-html-entry", "html_qa", "o011-artifact-u13-html-qa", "cumulative_semantic_html_reader"),
        ("o011-qa-unit13-pdf-structural", "o011-artifact-u13-pdf", "pdf_structural_qa", "o011-artifact-u13-pdf-structural-qa", "cumulative_pdf_structural_accessibility"),
        ("o011-qa-unit13-pdf-visual", "o011-artifact-u13-pdf", "pdf_visual_qa", "o011-artifact-u13-pdf-visual-qa", "cumulative_pdf_visual"),
    )
    for event_id, target_id, key, artifact_id, kind in qa_specs:
        value = bindings[key]
        records.append(base_record(event_id, "qa_event", checkpoint, parent_id="o011-brenner-u13", target_id=target_id, receipt_path=value["path"], evidence_sha256=value["sha256"], result="pass", qa_kind=kind, values=closure, artifact_id=artifact_id, translation_state=state))
        add_relation(records, checkpoint, f"o011-rel-{event_id}-evidences-target", "evidences", event_id, target_id)


def prepare_bundle(root: Path, checkpoint: str, state: str) -> dict[str, Any]:
    jsonl_prefix, csv_prefix, baseline = assert_prefix(root)
    contexts = [prepare_unit(root, unit) for unit in UNITS]
    reader = prepare_reader_closure(root)
    previous_workflow = v10.WORKFLOW
    v10.WORKFLOW = WORKFLOW
    try:
        suffix: list[dict[str, Any]] = []
        for context in contexts:
            unit_records = v10.make_unit_records(context, checkpoint, state)
            context["records"] = unit_records
            suffix.extend(unit_records)
        add_reader_records(suffix, baseline, reader, checkpoint, state)
    finally:
        v10.WORKFLOW = previous_workflow

    counts = v10.validate_records(baseline, suffix, load_json(root / "backend/schema/o011-record-v1.schema.json"))
    if len(suffix) != EXPECTED_EXTENSION_RECORD_COUNT or BASELINE_RECORD_COUNT + len(suffix) != EXPECTED_COMBINED_RECORD_COUNT:
        raise RuntimeError(f"frozen Units 11--13 semantic record census changed: {len(suffix)}")
    if counts != EXPECTED_EXTENSION_ENTITY_COUNTS:
        raise RuntimeError(f"frozen Units 11--13 entity census changed: {counts!r}")
    inputs: dict[str, dict[str, Any]] = {"schema": binding(root / "backend/schema/o011-record-v1.schema.json", root)}
    for context in contexts:
        for key, value in context["bindings"].items():
            inputs[f"u{context['tag']}:{key}"] = value
    for key, value in reader["bindings"].items():
        inputs[f"reader:{key}"] = value
    return {
        "jsonl_prefix": jsonl_prefix,
        "csv_prefix": csv_prefix,
        "baseline": baseline,
        "contexts": contexts,
        "reader": reader,
        "suffix": suffix,
        "counts": counts,
        "inputs": inputs,
    }


def unit_manifest(context: dict[str, Any], state: str, reader: dict[str, Any] | None = None) -> dict[str, Any]:
    manifest = v10.unit_manifest(context, state)
    if reader is not None and int(context["unit"]) == 13:
        bindings = reader["bindings"]
        manifest.update({
            "reader_status": "cumulative_html_pdf_reader_bound",
            "html_status": "cumulative_html_reader_bound",
            "pdf_status": "cumulative_pdf_reader_bound",
            "html_entry": bindings["html_entry"],
            "html_manifest": bindings["html_manifest"],
            "html_qa": bindings["html_qa"],
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
        raise RuntimeError("unsupported Units 11--13 translation state")
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
        "generator": binding(root / "scripts/export_backend_v13.py", root),
        "verifier": binding(root / "scripts/verify_backend_v13.py", root) if (root / "scripts/verify_backend_v13.py").is_file() else None,
        "baseline": {"record_count": BASELINE_RECORD_COUNT, "jsonl_bytes": BASELINE_JSONL_BYTES, "jsonl_sha256": BASELINE_JSONL_SHA256, "csv_lines_including_header": BASELINE_CSV_LINES, "csv_bytes": BASELINE_CSV_BYTES, "csv_sha256": BASELINE_CSV_SHA256, "preserved_byte_identically": True},
        "units11_13_extension": {"record_count": len(bundle["suffix"]), "entity_counts": bundle["counts"], "units": units, "model_identification": MODEL_IDENTIFICATION, "reader_status": "cumulative_html_pdf_reader_bound", "html_status": "cumulative_html_reader_bound", "pdf_status": "cumulative_pdf_reader_bound"},
        "inputs": bundle["inputs"],
        "outputs": outputs,
        "reader_closure": closure,
        "combined": {"record_count": BASELINE_RECORD_COUNT + len(bundle["suffix"]), "entity_counts": {kind: Counter(str(record.get("entity_type")) for record in bundle["baseline"] + bundle["suffix"]).get(kind, 0) for kind in sorted(ENTITY_TYPES)}},
        "claims": {"all_ids_unique": True, "all_references_resolve": True, "json_schema_valid": True, "units11_13_authority_solution_media_closure_current": True, "units11_13_translation_receipts_current": True, "units11_13_correction_manifests_current": True, "units11_13_post_correction_math_qa_current": True, "units1_10_prefix_byte_identical": True, "cumulative_reader_all_or_nothing": True, "cumulative_html_present": True, "cumulative_html_manifest_and_qa_current": True, "cumulative_pdf_present": True, "cumulative_pdf_structural_qa_current": True, "cumulative_pdf_visual_qa_current": True},
    }
    manifest_path = root / "backend/MANIFEST.json"
    manifest_path.write_bytes((json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    print(json.dumps({"status": "pass", "baseline_records": BASELINE_RECORD_COUNT, "added_records": len(bundle["suffix"]), "combined_records": BASELINE_RECORD_COUNT + len(bundle["suffix"]), "entity_counts": bundle["counts"], "jsonl": outputs["records_jsonl"], "csv": outputs["records_csv"], "manifest": binding(manifest_path, root)}, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
