#!/usr/bin/env python3
"""Independent deterministic verifier for the Unit 7 backend boundary."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

sys.path.insert(0, str(Path(__file__).resolve().parent))
import export_backend_v7 as exporter  # noqa: E402


VERIFY_WORKFLOW = "o011-verify-backend-v7"
MODEL_IDENTIFICATION = exporter.MODEL_IDENTIFICATION
SOLUTION_INDICES = exporter.SOLUTION_INDICES


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def binding(path: Path, root: Path) -> dict[str, object]:
    data = path.read_bytes()
    return {"path": path.relative_to(root).as_posix(), "bytes": len(data), "sha256": sha256_bytes(data)}


def canonical_json(record: dict[str, object]) -> bytes:
    return (json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def marker_slices(text: str, pattern: str) -> list[str]:
    return exporter.marker_slices(text, pattern)


def expected_csv(prefix: bytes, suffix: list[dict[str, object]]) -> bytes:
    buf = io.StringIO(newline="")
    writer = csv.DictWriter(buf, fieldnames=exporter.CSV_FIELDS, extrasaction="ignore", lineterminator="\r\n")
    for record in suffix:
        writer.writerow({field: record.get(field) for field in exporter.CSV_FIELDS})
    return prefix + buf.getvalue().encode("utf-8")


def validate_state(root: Path) -> dict[str, object]:
    jsonl_path = root / "backend/records.jsonl"
    csv_path = root / "backend/records.csv"
    manifest_path = root / "backend/MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("workflow") != exporter.WORKFLOW:
        raise RuntimeError("backend manifest is not the v7 workflow")
    jsonl = jsonl_path.read_bytes()
    lines = jsonl.splitlines(keepends=True)
    if len(lines) != exporter.BASELINE_RECORD_COUNT + int(manifest["unit07_extension"]["record_count"]):
        raise RuntimeError("combined JSONL record count disagrees with manifest")
    prefix = b"".join(lines[: exporter.BASELINE_RECORD_COUNT])
    if len(prefix) != exporter.BASELINE_JSONL_BYTES or sha256_bytes(prefix) != exporter.BASELINE_JSONL_SHA256:
        raise RuntimeError("immutable 1,173-record JSONL prefix changed")
    records = [json.loads(line.decode("utf-8")) for line in lines]
    suffix = records[exporter.BASELINE_RECORD_COUNT :]
    if any(line != canonical_json(record) for line, record in zip(lines[exporter.BASELINE_RECORD_COUNT :], suffix)):
        raise RuntimeError("noncanonical Unit 7 JSONL record")
    if [str(record["id"]) for record in suffix] != sorted(str(record["id"]) for record in suffix):
        raise RuntimeError("Unit 7 suffix IDs are not sorted")
    if len({str(record["id"]) for record in records}) != len(records):
        raise RuntimeError("combined backend IDs are not unique")

    schema = json.loads((root / "backend/schema/o011-record-v1.schema.json").read_text(encoding="utf-8"))
    errors: list[str] = []
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    for record in records:
        errors.extend(f"{record['id']}: {error.message}" for error in validator.iter_errors(record))
    if errors:
        raise RuntimeError("JSON Schema validation failed: " + "; ".join(errors[:10]))
    all_ids = {str(record["id"]) for record in records}
    for record in suffix:
        for key in ("parent_id", "resource_id", "edition_id", "rights_component_id", "target_id", "artifact_id", "from_id", "to_id"):
            value = record.get(key)
            if value is not None and str(value) not in all_ids:
                raise RuntimeError(f"unresolved {key} on {record['id']}: {value}")

    csv_bytes = csv_path.read_bytes()
    csv_lines = csv_bytes.splitlines(keepends=True)
    csv_prefix = b"".join(csv_lines[: exporter.BASELINE_CSV_LINES])
    if len(csv_lines) != exporter.BASELINE_CSV_LINES + len(suffix) or len(csv_prefix) != exporter.BASELINE_CSV_BYTES or sha256_bytes(csv_prefix) != exporter.BASELINE_CSV_SHA256:
        raise RuntimeError("CSV immutable prefix or line count changed")
    if csv_bytes != expected_csv(csv_prefix, suffix):
        raise RuntimeError("CSV projection is not exactly the v7 JSONL suffix")

    ext = manifest.get("unit07_extension", {})
    reader_bound = ext.get("reader_status") == "final_cumulative_reader_bound"
    expected = {
        "record_count": len(suffix), "unit_id": exporter.UNIT_ID, "lecture_sections": 2,
        "worksheet_sections": 2, "exercise_count": 19, "hint_indices": [],
        "source_solution_indices": list(SOLUTION_INDICES), "graded_point_values": [3, 5, 8, 6, 4],
        "graded_point_total": 26, "static_asset_count": 3, "interactive_asset_count": 2,
        "correction_ids": list(exporter.CORRECTION_IDS), "model_identification": MODEL_IDENTIFICATION,
        "reader_status": "final_cumulative_reader_bound" if reader_bound else "not_yet_bound",
        "html_status": "absent_not_claimed",
    }
    for key, value in expected.items():
        if ext.get(key) != value:
            raise RuntimeError(f"manifest Unit 7 closure changed: {key}={ext.get(key)!r}")
    if ext.get("translation_state") not in {"translated", "visually_checked"}:
        raise RuntimeError("invalid Unit 7 translation state")
    if reader_bound and ext.get("translation_state") != "visually_checked":
        raise RuntimeError("reader-bound Unit 7 closure is not visually_checked")
    counts = Counter(str(record.get("entity_type")) for record in suffix)
    manifest_counts = ext.get("entity_counts")
    if manifest_counts != {kind: counts.get(kind, 0) for kind in sorted(exporter.ENTITY_TYPES)}:
        raise RuntimeError("manifest entity counts are stale")

    # Every manifest input is a live, cryptographically current file binding.
    for key, value in manifest.get("inputs", {}).items():
        if not isinstance(value, dict):
            raise RuntimeError(f"invalid input binding: {key}")
        path = root / str(value["path"])
        if not path.is_file() or binding(path, root) != value:
            raise RuntimeError(f"stale input binding: {key}")
    if manifest.get("outputs", {}).get("records_jsonl") != binding(jsonl_path, root) or manifest.get("outputs", {}).get("records_csv") != binding(csv_path, root):
        raise RuntimeError("manifest output binding is stale")

    by_id = {str(record["id"]): record for record in records}
    unit = by_id[exporter.UNIT_ID]
    if unit.get("translation_assistance", {}).get("model") != MODEL_IDENTIFICATION or unit.get("translation_assistance", {}).get("human_and_source_credits_preserved") is not True:
        raise RuntimeError("model/source-credit provenance changed")
    lecture = by_id[exporter.LECTURE_ID]
    worksheet = by_id[exporter.WORKSHEET_ID]
    if lecture.get("target_sha256") != manifest["inputs"]["lecture_target"]["sha256"] or worksheet.get("target_sha256") != manifest["inputs"]["worksheet_target"]["sha256"]:
        raise RuntimeError("lecture/worksheet target bindings changed")

    preflight = json.loads((root / "qa/unit-07/AUTHORITY_PREFLIGHT.json").read_text(encoding="utf-8"))
    solution_meta = {int(item["exercise_index"]): item for item in preflight["solutions"]["exercises"]}
    lecture_source = (root / "authority/expanded/lecture07_source.de.tex").read_text(encoding="utf-8")
    lecture_target = (root / "source/units/unit-07/lecture07.id.tex").read_text(encoding="utf-8")
    worksheet_source = (root / "authority/expanded/worksheet07_source.de.tex").read_text(encoding="utf-8")
    worksheet_target = (root / "source/units/unit-07/worksheet07.id.tex").read_text(encoding="utf-8")
    if unit.get("source_sha256") != sha256_bytes((root / "authority/expanded/lecture07_source.de.tex").read_bytes() + (root / "authority/expanded/worksheet07_source.de.tex").read_bytes()) or unit.get("target_sha256") != sha256_bytes((root / "source/units/unit-07/lecture07.id.tex").read_bytes() + (root / "source/units/unit-07/worksheet07.id.tex").read_bytes()):
        raise RuntimeError("Unit 7 pair source/target aggregate binding changed")
    for index, (source_part, target_part) in enumerate(zip(marker_slices(lecture_source, r"\\zwischenueberschrift\{"), marker_slices(lecture_target, r"\\zwischenueberschrift\{")), 1):
        record = by_id[f"o011-brenner-u07-l07-s{index:02d}"]
        if record.get("source_sha256") != sha256_bytes(source_part.encode()) or record.get("target_sha256") != sha256_bytes(target_part.encode()):
            raise RuntimeError(f"lecture section {index} binding changed")
    source_exercises = marker_slices(worksheet_source, r"\\inputaufgabe(?:gibtloesung)?")
    target_exercises = marker_slices(worksheet_target, r"\\inputaufgabe(?:gibtloesung)?")
    if len(source_exercises) != 19 or len(target_exercises) != 19:
        raise RuntimeError("worksheet exercise topology changed")
    for index, (source_part, target_part) in enumerate(zip(source_exercises, target_exercises), 1):
        record = by_id[f"o011-brenner-u07-w07-e{index:03d}"]
        meta = solution_meta[index]
        if record.get("source_sha256") != sha256_bytes(source_part.encode()) or record.get("target_sha256") != sha256_bytes(target_part.encode()) or record.get("has_authority_solution") != (index in SOLUTION_INDICES) or record.get("hint_present") is not False:
            raise RuntimeError(f"worksheet exercise {index} closure changed")
        if record.get("point_value") != meta.get("point_value"):
            raise RuntimeError(f"worksheet exercise {index} point marker changed")
    for index in SOLUTION_INDICES:
        sid = f"o011-brenner-u07-w07-e{index:03d}-solution"
        if by_id[sid].get("unit_kind") != "source_supplied_solution" or by_id[sid].get("parent_id") != f"o011-brenner-u07-w07-e{index:03d}":
            raise RuntimeError(f"solution {index} identity changed")

    assets = [r for r in suffix if r.get("entity_type") == "asset"]
    rights = [r for r in suffix if r.get("entity_type") == "rights"]
    if len(assets) != 5 or len(rights) != 5:
        raise RuntimeError("Unit 7 media/rights count changed")
    for asset in assets:
        path = root / str(asset["path"])
        actual = binding(path, root)
        if actual["sha256"] != asset.get("source_sha256") or actual["bytes"] != asset.get("expected_bytes"):
            raise RuntimeError(f"media binding changed: {asset['id']}")
    corrections = [r for r in suffix if r.get("entity_type") == "correction"]
    if {r["source_local_id"] for r in corrections} != set(exporter.CORRECTION_IDS):
        raise RuntimeError("Unit 7 correction closure changed")
    for correction in corrections:
        if correction.get("correction_status") != "corrected_in_target" or not correction.get("correction_manifests") or not correction.get("target_bindings"):
            raise RuntimeError(f"incomplete correction: {correction['id']}")
        values = correction["correction_manifests"] + correction["target_bindings"]
        if correction.get("validation_binding"):
            values.append(correction["validation_binding"])
        for value in values:
            path = root / str(value["path"])
            if not path.is_file() or binding(path, root)["sha256"] != value.get("sha256"):
                raise RuntimeError(f"stale correction binding: {correction['id']}")

    qa_events = [r for r in suffix if r.get("entity_type") == "qa_event"]
    expected_qa_count = 16 if reader_bound else 10
    if len(qa_events) != expected_qa_count or any(r.get("result") != "pass" for r in qa_events):
        raise RuntimeError("Unit 7 QA-event closure changed")
    for event in qa_events:
        path = root / str(event["receipt_path"])
        if not path.is_file() or sha256_bytes(path.read_bytes()) != event.get("evidence_sha256"):
            raise RuntimeError(f"stale QA evidence: {event['id']}")

    # Every artifact is a live, current file binding.  Source-frozen artifacts
    # intentionally carry target_sha256=null; translated/reader artifacts must
    # bind their target hash to the current bytes.
    for artifact in (r for r in suffix if r.get("entity_type") == "artifact"):
        path = root / str(artifact["path"])
        if not path.is_file():
            raise RuntimeError(f"missing artifact file: {artifact['id']}")
        actual = binding(path, root)
        if artifact.get("bytes") != actual["bytes"]:
            raise RuntimeError(f"stale artifact byte count: {artifact['id']}")
        target_hash = artifact.get("target_sha256")
        if target_hash is not None and target_hash != actual["sha256"]:
            raise RuntimeError(f"stale artifact target binding: {artifact['id']}")
        if artifact.get("language") == "German" and artifact.get("source_sha256") != actual["sha256"]:
            raise RuntimeError(f"stale frozen source artifact binding: {artifact['id']}")

    claims = manifest.get("claims", {})
    if claims.get("cumulative_html_present") is not False:
        raise RuntimeError("unavailable cumulative HTML surface was claimed")
    if reader_bound:
        optional_paths = exporter.optional_reader_paths(root)
        if not all(path.is_file() for path in optional_paths.values()):
            raise RuntimeError("manifest claims a reader but the final reader closure is incomplete")
        optional_bindings = {key: binding(path, root) for key, path in optional_paths.items()}
        exporter.validate_reader_inputs(root, optional_paths, optional_bindings)
        if ext.get("reader_pdf") != optional_bindings["reader_pdf"]:
            raise RuntimeError("manifest reader PDF binding is stale")
        boundary = json.loads(optional_paths["boundary_receipt"].read_text(encoding="utf-8"))
        if ext.get("reader_pages") != boundary.get("pdf", {}).get("pages"):
            raise RuntimeError("manifest reader page count is stale")
        final_artifacts = {
            "o011-artifact-u07-reader-pdf": "reader_pdf",
            "o011-artifact-u07-reader-wrapper": "reader_wrapper",
            "o011-artifact-u07-build-receipt": "build_receipt",
            "o011-artifact-u07-structural-receipt": "structural_receipt",
            "o011-artifact-u07-boundary-receipt": "boundary_receipt",
            "o011-artifact-u07-visual-receipt": "visual_receipt",
            "o011-artifact-u07-math-receipt": "math_receipt",
        }
        for artifact_id, key in final_artifacts.items():
            artifact = by_id.get(artifact_id)
            if artifact is None:
                raise RuntimeError(f"missing final reader artifact: {artifact_id}")
            if artifact.get("target_sha256") != optional_bindings[key]["sha256"] or artifact.get("bytes") != optional_bindings[key]["bytes"]:
                raise RuntimeError(f"final reader artifact binding changed: {artifact_id}")
        for key in ("reader_pdf_bound", "cumulative_pdf_present", "build_structural_visual_math_current", "model_provenance_current"):
            if claims.get(key) is not True:
                raise RuntimeError(f"reader-bound claim missing: {key}")
    else:
        for key in ("reader_pdf_bound", "cumulative_pdf_present", "build_structural_visual_math_current", "model_provenance_current"):
            if claims.get(key) is not False:
                raise RuntimeError(f"unverified reader surface was claimed: {key}")

    return {"manifest": manifest, "records": records, "suffix": suffix, "counts": {kind: counts.get(kind, 0) for kind in sorted(exporter.ENTITY_TYPES)}, "jsonl": binding(jsonl_path, root), "csv": binding(csv_path, root), "manifest_binding": binding(manifest_path, root)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    root = args.root.resolve()
    current_manifest = json.loads((root / "backend/MANIFEST.json").read_text(encoding="utf-8"))
    checkpoint = str(current_manifest["checkpoint"])
    state = str(current_manifest["unit07_extension"].get("translation_state", exporter.DEFAULT_TRANSLATION_STATE))
    command = [sys.executable, str(root / "scripts/export_backend_v7.py"), "--root", str(root), "--checkpoint", checkpoint, "--translation-state", state]
    completed = subprocess.run(command, cwd=root, capture_output=True, text=True, encoding="utf-8")
    if completed.returncode != 0:
        raise RuntimeError(f"repeat exporter failed: {completed.stderr.strip() or completed.stdout.strip()}")
    first = validate_state(root)
    completed = subprocess.run(command, cwd=root, capture_output=True, text=True, encoding="utf-8")
    if completed.returncode != 0:
        raise RuntimeError(f"second exporter failed: {completed.stderr.strip() or completed.stdout.strip()}")
    second = validate_state(root)
    for key in ("jsonl", "csv", "manifest_binding"):
        if first[key] != second[key]:
            raise RuntimeError(f"repeat export changed {key}")
    final_reader_bound = second["manifest"].get("unit07_extension", {}).get("reader_status") == "final_cumulative_reader_bound"
    effective_state = str(second["manifest"].get("unit07_extension", {}).get("translation_state", state))
    receipt = {
        "schema_version": 1,
        "workflow": VERIFY_WORKFLOW,
        "status": "pass",
        "checkpoint": checkpoint,
        "baseline": {"records": exporter.BASELINE_RECORD_COUNT, "jsonl_bytes": exporter.BASELINE_JSONL_BYTES, "jsonl_sha256": exporter.BASELINE_JSONL_SHA256, "csv_prefix_bytes": exporter.BASELINE_CSV_BYTES, "csv_prefix_sha256": exporter.BASELINE_CSV_SHA256, "preserved_byte_identically": True},
        "unit07_extension": {"records": len(second["suffix"]), "entity_counts": second["counts"], "lecture_sections": 2, "worksheet_sections": 2, "exercises": 19, "source_solution_indices": list(SOLUTION_INDICES), "source_solution_absent_indices": [i for i in range(1, 20) if i not in SOLUTION_INDICES], "hint_indices": [], "graded_point_values": [3, 5, 8, 6, 4], "graded_point_total": 26, "static_assets": 3, "interactive_assets": 2, "correction_ids": [x.lower() for x in exporter.CORRECTION_IDS], "model_identification": MODEL_IDENTIFICATION, "translation_state": effective_state, "reader_status": "final_cumulative_reader_bound" if final_reader_bound else "not_yet_bound", "html_status": "absent_not_claimed"},
        "combined_records": len(second["records"]),
        "outputs": {"records_jsonl": second["jsonl"], "records_csv": second["csv"], "manifest": second["manifest_binding"]},
        "determinism": {"first_jsonl_sha256": first["jsonl"]["sha256"], "first_csv_sha256": first["csv"]["sha256"], "first_manifest_sha256": first["manifest_binding"]["sha256"], "second_export_matches_first": True},
        "checks": {"immutable_prefix": True, "canonical_jsonl": True, "csv_projection_exact": True, "combined_json_schema_valid": True, "all_ids_unique": True, "all_references_resolve": True, "live_input_bindings_current": True, "source_target_segment_hashes_current": True, "solution_hint_point_media_closure": True, "interactive_surfaces_preserved": True, "correction_manifest_target_bindings_current": True, "qa_receipts_current": True, "reader_bound_current": final_reader_bound, "reader_not_falsely_claimed": not final_reader_bound},
    }
    receipt_path = root / "qa/unit-07/backend.json"
    receipt_path.write_bytes((json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    print(json.dumps({"status": "pass", "records": len(second["records"]), "jsonl": second["jsonl"], "csv": second["csv"], "manifest": second["manifest_binding"], "receipt": binding(receipt_path, root)}, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
