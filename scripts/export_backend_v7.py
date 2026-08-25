#!/usr/bin/env python3
"""Export the additive Unit 7 O011 backend extension.

The existing 1,173 JSONL records (Units 1--6) are a byte-immutable prefix.
This exporter reconstructs a deterministic Unit 7 suffix from the frozen
authority, translation receipts, corrections, and file-specific media rights.
The reader closure is all-or-nothing: while the PDF/build/QA receipts are
absent it remains explicitly unbound; once every final receipt is present and
cryptographically current, the export records a visually-checked cumulative
reader and binds each receipt as an additive artifact.
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


BASELINE_RECORD_COUNT = 1173
BASELINE_JSONL_BYTES = 702086
BASELINE_JSONL_SHA256 = "b09862d4b98c475d7e5a3bc92f1e3d72ca771d7f726350b76ab4bd68d6dde5a1"
BASELINE_CSV_LINES = 1174
BASELINE_CSV_BYTES = 243301
BASELINE_CSV_SHA256 = "5831a7bf3ccc0c18c4246bf713ec6e4c93958465808e7027763e53e170683997"
WORKFLOW = "o011-export-backend-v7"
MODEL_IDENTIFICATION = "OpenAI Codex gpt-5.6-sol, Ultra"
DEFAULT_TRANSLATION_STATE = "translated"
SOLUTION_INDICES = (4, 7, 13)
CORRECTION_IDS = ("O011-TRANS-0070", "O011-TRANS-0071", "O011-TEX-0072")
UNIT_ID = "o011-brenner-u07"
LECTURE_ID = "o011-brenner-u07-l07"
WORKSHEET_ID = "o011-brenner-u07-w07"
EDITION_ID = "o011-edition-brenner-current-20260821"
RESOURCE_ID = "o011-resource-brenner-dg2023"
COURSE_ID = "o011-course-d50"
TEXT_RIGHTS_ID = "o011-rights-brenner-text"

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


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(record: dict[str, object]) -> bytes:
    return (json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def binding(path: Path, root: Path) -> dict[str, object]:
    data = path.read_bytes()
    return {"path": path.relative_to(root).as_posix(), "bytes": len(data), "sha256": sha256_bytes(data)}


def load_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def marker_slices(text: str, pattern: str) -> list[str]:
    starts = [m.start() for m in re.finditer(pattern, text)]
    return [text[start:starts[i + 1] if i + 1 < len(starts) else len(text)] for i, start in enumerate(starts)]


def slug(value: str) -> str:
    value = value.lower().replace(".", "-")
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value


def base_record(record_id: str, entity_type: str, checkpoint: str, **fields: object) -> dict[str, object]:
    value: dict[str, object] = {
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


def paths_for(root: Path, preflight: dict[str, object]) -> dict[str, Path]:
    paths: dict[str, Path] = {
        "schema": root / "backend/schema/o011-record-v1.schema.json",
        "preflight": root / "qa/unit-07/AUTHORITY_PREFLIGHT.json",
        "interactive_manifest": root / "source/unit07_interactive_media.json",
        "interactive_qa": root / "qa/unit-07/INTERACTIVE_MEDIA_QA.json",
        "media_config": root / "source/unit_media.json",
        "media_rights_manifest": root / "authority/brenner_media_rights_manifest.csv",
        "adverse": root / "00_control/ADVERSE_LEDGER.csv",
        "terminology": root / "00_control/TERMINOLOGY.csv",
        "terminology_audit": root / "qa/terminology/FIELD_TERMINOLOGY_AUDIT_20260822.md",
        "lecture_source": root / "authority/expanded/lecture07_source.de.tex",
        "lecture_target": root / "source/units/unit-07/lecture07.id.tex",
        "lecture_receipt": root / "qa/unit-07/lecture07_translation.json",
        "lecture_manifest": root / "00_control/LECTURE07_PROTECTED_CORRECTIONS.json",
        "worksheet_source": root / "authority/expanded/worksheet07_source.de.tex",
        "worksheet_target": root / "source/units/unit-07/worksheet07.id.tex",
        "worksheet_receipt": root / "qa/unit-07/worksheet07_translation.json",
        "worksheet_manifest": root / "00_control/WORKSHEET07_PROTECTED_CORRECTIONS.json",
        "tex_safe_decision": root / "qa/unit-07/TEX_SAFE_ATTRIBUTION_DECISION.json",
    }
    for index in SOLUTION_INDICES:
        paths[f"solution{index}_source"] = root / f"authority/expanded/worksheet07_exercise{index:02d}_solution_source.de.tex"
        paths[f"solution{index}_target"] = root / f"source/units/unit-07/worksheet07_exercise{index:02d}_solution.id.tex"
        paths[f"solution{index}_receipt"] = root / f"qa/unit-07/worksheet07_exercise{index:02d}_solution_translation.json"
    for asset in preflight.get("media", {}).get("assets", []):
        paths[f"media:{asset['filename']}"] = root / "authority/media" / str(asset["filename"])
    for asset in load_json(paths["interactive_manifest"]).get("assets", []):
        paths[f"media:{asset['filename']}"] = root / "authority/media" / str(asset["filename"])
    return paths


def optional_reader_paths(root: Path) -> dict[str, Path]:
    """Final reader inputs are admitted as one all-or-nothing closure."""
    return {
        "reader_pdf": root / "output/pdf/geometri-diferensial-manifold-mulus-hingga-unit-07-id.pdf",
        "reader_wrapper": root / "build/through-unit-07.tex",
        "build_receipt": root / "qa/unit-07/build.json",
        "structural_receipt": root / "qa/unit-07/pdf_structural_qa.json",
        "boundary_receipt": root / "qa/unit-07/PDF_BOUNDARY_QA.json",
        "visual_receipt": root / "qa/unit-07/VISUAL_QA.md",
        "math_receipt": root / "qa/unit-07/POST_REPAIR_MATH_QA.json",
    }


def assert_prefix(root: Path) -> tuple[bytes, bytes, list[dict[str, object]]]:
    jsonl = (root / "backend/records.jsonl").read_bytes()
    lines = jsonl.splitlines(keepends=True)
    if len(lines) < BASELINE_RECORD_COUNT:
        raise RuntimeError("backend has fewer than the immutable 1,173-record prefix")
    prefix = b"".join(lines[:BASELINE_RECORD_COUNT])
    if len(prefix) != BASELINE_JSONL_BYTES or sha256_bytes(prefix) != BASELINE_JSONL_SHA256:
        raise RuntimeError("immutable 1,173-record JSONL prefix changed")
    csv_bytes = (root / "backend/records.csv").read_bytes()
    csv_lines = csv_bytes.splitlines(keepends=True)
    if len(csv_lines) < BASELINE_CSV_LINES:
        raise RuntimeError("backend CSV has fewer than the immutable prefix")
    csv_prefix = b"".join(csv_lines[:BASELINE_CSV_LINES])
    if len(csv_prefix) != BASELINE_CSV_BYTES or sha256_bytes(csv_prefix) != BASELINE_CSV_SHA256:
        raise RuntimeError("immutable 1,173-row CSV prefix changed")
    baseline = [json.loads(line.decode("utf-8")) for line in lines[:BASELINE_RECORD_COUNT]]
    return prefix, csv_prefix, baseline


def file_bindings(paths: dict[str, Path]) -> dict[str, dict[str, object]]:
    missing = [f"{key}: {path}" for key, path in paths.items() if not path.is_file()]
    if missing:
        raise RuntimeError("missing Unit 7 inputs: " + "; ".join(missing))
    root = paths["schema"].parents[2]
    return {key: binding(path, root) for key, path in sorted(paths.items())}


def validate_inputs(root: Path, paths: dict[str, Path], bindings: dict[str, dict[str, object]]) -> tuple[dict[str, object], dict[str, object], list[dict[str, object]]]:
    preflight = load_json(paths["preflight"])
    if preflight.get("status") != "pass" or preflight.get("unit") != 7:
        raise RuntimeError("Unit 7 authority preflight is not passing")
    structure = preflight.get("structure", {})
    expected_structure = {
        "lecture_section_count": 2,
        "worksheet_section_count": 2,
        "worksheet_exercise_count": 19,
        "worksheet_graded_count": 5,
        "worksheet_practice_count": 14,
        "worksheet_point_total": 26,
        "worksheet_solution_bearing_indices": list(SOLUTION_INDICES),
        "all_hint_fields_blank": True,
    }
    if any(structure.get(k) != v for k, v in expected_structure.items()):
        raise RuntimeError(f"Unit 7 authority structure changed: {structure}")
    for key in ["lecture_receipt", "worksheet_receipt", *[f"solution{i}_receipt" for i in SOLUTION_INDICES]]:
        receipt = load_json(paths[key])
        if receipt.get("status") != "pass":
            raise RuntimeError(f"translation receipt failed: {key}")
        source_key = key.replace("_receipt", "_source")
        target_key = key.replace("_receipt", "_target")
        if receipt.get("source_sha256") != bindings[source_key]["sha256"] or receipt.get("source_bytes") != bindings[source_key]["bytes"]:
            raise RuntimeError(f"stale source binding in {key}")
        if receipt.get("target_sha256") != bindings[target_key]["sha256"] or receipt.get("target_bytes") != bindings[target_key]["bytes"]:
            raise RuntimeError(f"stale target binding in {key}")
    for key in ("lecture_manifest", "worksheet_manifest"):
        manifest = load_json(paths[key])
        if not isinstance(manifest.get("allowed_deltas"), list) or len(manifest["allowed_deltas"]) != 1:
            raise RuntimeError(f"invalid correction manifest: {key}")
        if manifest["allowed_deltas"][0].get("correction_id") not in CORRECTION_IDS:
            raise RuntimeError(f"unexpected correction ID in {key}")
    tex_decision = load_json(paths["tex_safe_decision"])
    if tex_decision.get("status") != "applied-before-unit-07-build" or tex_decision.get("tex_display_creator") != "132ninme":
        raise RuntimeError("TeX-safe attribution decision is not admitted")
    interactive = load_json(paths["interactive_qa"])
    if interactive.get("status") != "pass" or interactive.get("preserved_locally") is not True:
        raise RuntimeError("interactive media QA is not passing")
    interactive_manifest = load_json(paths["interactive_manifest"])
    if len(interactive_manifest.get("assets", [])) != 2:
        raise RuntimeError("interactive media manifest changed")
    media_assets = preflight.get("media", {}).get("assets", [])
    if len(media_assets) != 3:
        raise RuntimeError("static Unit 7 media closure changed")
    for asset in media_assets:
        path = paths[f"media:{asset['filename']}"]
        actual = binding(path, root)
        if actual["bytes"] != asset.get("bytes") or actual["sha256"] != asset.get("sha256"):
            raise RuntimeError(f"static media binding changed: {asset['filename']}")
        if not asset.get("rights_critical_fields_match"):
            raise RuntimeError(f"static media rights closure changed: {asset['filename']}")
    for asset in interactive_manifest["assets"]:
        actual = binding(paths[f"media:{asset['filename']}"], root)
        if actual["bytes"] != asset.get("bytes") or actual["sha256"] != asset.get("sha256"):
            raise RuntimeError(f"interactive media binding changed: {asset['filename']}")
    return preflight, interactive_manifest, [load_json(paths[f"solution{i}_receipt"]) for i in SOLUTION_INDICES]


def validate_reader_inputs(root: Path, paths: dict[str, Path], bindings: dict[str, dict[str, object]]) -> dict[str, object]:
    """Validate the all-or-nothing final PDF/build/QA closure."""
    pdf = binding(paths["reader_pdf"], root)
    build = load_json(paths["build_receipt"])
    structural = load_json(paths["structural_receipt"])
    boundary = load_json(paths["boundary_receipt"])
    math = load_json(paths["math_receipt"])
    if build.get("deterministic_clean_cycles") is not True or len(build.get("cycles", [])) != 2:
        raise RuntimeError("Unit 7 deterministic PDF build is not closed")
    if build.get("output") != pdf or any(cycle.get("bytes") != pdf["bytes"] or cycle.get("sha256") != pdf["sha256"] for cycle in build.get("cycles", [])):
        raise RuntimeError("Unit 7 build receipt does not bind the final PDF")
    if structural.get("passed") is not True or structural.get("pdf", {}).get("path") != pdf["path"] or structural.get("pdf", {}).get("bytes") != pdf["bytes"] or structural.get("pdf", {}).get("sha256") != pdf["sha256"]:
        raise RuntimeError("Unit 7 structural PDF receipt is not passing/current")
    if boundary.get("status") != "pass" or boundary.get("passed") is not True or boundary.get("pdf", {}).get("path") != pdf["path"] or boundary.get("pdf", {}).get("bytes") != pdf["bytes"] or boundary.get("pdf", {}).get("sha256") != pdf["sha256"]:
        raise RuntimeError("Unit 7 independent PDF boundary QA is not passing/current")
    if math.get("status") != "pass" or math.get("checks", {}).get("cumulative_pdf_build_pass") is not True or math.get("artifact_bindings", {}).get("reader_pdf") != pdf:
        raise RuntimeError("Unit 7 post-repair mathematical QA is not passing/current")
    visual = paths["visual_receipt"].read_text(encoding="utf-8")
    if pdf["sha256"] not in visual or "Status: PASS" not in visual:
        raise RuntimeError("Unit 7 visual QA does not bind the final PDF")
    wrapper = paths["reader_wrapper"].read_text(encoding="utf-8")
    if wrapper.count(MODEL_IDENTIFICATION) != 1:
        raise RuntimeError("Unit 7 reader wrapper model provenance is not exact-once")
    return {"pdf": pdf, "build": build, "structural": structural, "boundary": boundary, "math": math}


def add_relation(records: list[dict[str, object]], checkpoint: str, relation_id: str, relation_type: str, from_id: str, to_id: str) -> None:
    records.append(base_record(relation_id, "relation", checkpoint, relation_type=relation_type, from_id=from_id, to_id=to_id))


def make_suffix(root: Path, checkpoint: str, state: str, paths: dict[str, Path], bindings: dict[str, dict[str, object]], preflight: dict[str, object], interactive_manifest: dict[str, object]) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    root_authority = preflight["authority"]["pages"]
    solution_meta = {int(item["exercise_index"]): item for item in preflight["solutions"]["exercises"]}
    lecture_source = paths["lecture_source"].read_text(encoding="utf-8")
    lecture_target = paths["lecture_target"].read_text(encoding="utf-8")
    worksheet_source = paths["worksheet_source"].read_text(encoding="utf-8")
    worksheet_target = paths["worksheet_target"].read_text(encoding="utf-8")
    lecture_source_sections = marker_slices(lecture_source, r"\\zwischenueberschrift\{")
    lecture_target_sections = marker_slices(lecture_target, r"\\zwischenueberschrift\{")
    worksheet_source_sections = marker_slices(worksheet_source, r"\\zwischenueberschrift\{")
    worksheet_target_sections = marker_slices(worksheet_target, r"\\zwischenueberschrift\{")
    exercise_source_parts = marker_slices(worksheet_source, r"\\inputaufgabe(?:gibtloesung)?")
    exercise_target_parts = marker_slices(worksheet_target, r"\\inputaufgabe(?:gibtloesung)?")
    if not (len(lecture_source_sections) == len(lecture_target_sections) == 2 and len(worksheet_source_sections) == len(worksheet_target_sections) == 2 and len(exercise_source_parts) == len(exercise_target_parts) == 19):
        raise RuntimeError("Unit 7 source/target topology changed")

    common = {
        "edition_id": EDITION_ID,
        "resource_id": RESOURCE_ID,
        "language": "Indonesian",
        "locale": "id-ID",
        "rights_component_id": TEXT_RIGHTS_ID,
    }
    records.append(base_record(
        UNIT_ID, "unit", checkpoint,
        **common,
        order=7,
        parent_id=COURSE_ID,
        path="source/units/unit-07",
        source_local_id="course-unit-07",
        source_locator="Kurs:Differentialgeometrie (Osnabrück 2023)/Vorlesung 7 + Arbeitsblatt 7",
        source_sha256=sha256_bytes(paths["lecture_source"].read_bytes() + paths["worksheet_source"].read_bytes()),
        target_sha256=sha256_bytes(paths["lecture_target"].read_bytes() + paths["worksheet_target"].read_bytes()),
        translation_assistance={"human_and_source_credits_preserved": True, "model": MODEL_IDENTIFICATION, "role": "translation and production assistance under user direction"},
        translation_state=state,
        unit_kind="lecture_worksheet_pair",
        authority_page_revisions={
            "lecture_root": [root_authority["lecture_root"]["pageid"], root_authority["lecture_root"]["revid"]],
            "lecture_latex": [root_authority["lecture_latex"]["pageid"], root_authority["lecture_latex"]["revid"]],
            "worksheet_root": [root_authority["worksheet_root"]["pageid"], root_authority["worksheet_root"]["revid"]],
            "worksheet_latex": [root_authority["worksheet_latex"]["pageid"], root_authority["worksheet_latex"]["revid"]],
        },
    ))
    records.append(base_record(LECTURE_ID, "unit", checkpoint, **common, order=1, parent_id=UNIT_ID, path="source/units/unit-07/lecture07.id.tex", source_local_id="lecture07", source_locator=root_authority["lecture_root"]["title"], source_sha256=bindings["lecture_source"]["sha256"], target_sha256=bindings["lecture_target"]["sha256"], revid=root_authority["lecture_root"]["revid"], pageid=root_authority["lecture_root"]["pageid"], unit_kind="lecture", translation_state=state))
    records.append(base_record(WORKSHEET_ID, "unit", checkpoint, **common, order=2, parent_id=UNIT_ID, path="source/units/unit-07/worksheet07.id.tex", source_local_id="worksheet07", source_locator=root_authority["worksheet_root"]["title"], source_sha256=bindings["worksheet_source"]["sha256"], target_sha256=bindings["worksheet_target"]["sha256"], revid=root_authority["worksheet_root"]["revid"], pageid=root_authority["worksheet_root"]["pageid"], unit_kind="worksheet", translation_state=state))

    for index, (source_part, target_part) in enumerate(zip(lecture_source_sections, lecture_target_sections), 1):
        records.append(base_record(f"o011-brenner-u07-l07-s{index:02d}", "segment", checkpoint, **common, order=index, parent_id=LECTURE_ID, path=f"source/units/unit-07/lecture07.id.tex#section-{index}", source_local_id=f"lecture07:section:{index}", source_locator=f"{root_authority['lecture_root']['title']}#section-{index}", source_sha256=sha256_bytes(source_part.encode()), target_sha256=sha256_bytes(target_part.encode()), segment_kind="lecture_section", translation_state=state))
    for index, (source_part, target_part) in enumerate(zip(worksheet_source_sections, worksheet_target_sections), 1):
        records.append(base_record(f"o011-brenner-u07-w07-s{index:02d}", "segment", checkpoint, **common, order=index, parent_id=WORKSHEET_ID, path=f"source/units/unit-07/worksheet07.id.tex#section-{index}", source_local_id=f"worksheet07:section:{index}", source_locator=f"{root_authority['worksheet_root']['title']}#section-{index}", source_sha256=sha256_bytes(source_part.encode()), target_sha256=sha256_bytes(target_part.encode()), segment_kind="worksheet_section", translation_state=state))

    for index, (source_part, target_part) in enumerate(zip(exercise_source_parts, exercise_target_parts), 1):
        meta = solution_meta[index]
        point = meta.get("point_value")
        records.append(base_record(f"o011-brenner-u07-w07-e{index:03d}", "unit", checkpoint, **common, order=index, parent_id=WORKSHEET_ID, path=f"source/units/unit-07/worksheet07.id.tex#exercise-{index}", source_local_id=f"worksheet07:exercise:{index}", source_locator=meta.get("task_title"), source_display_id=f"7.{index}", source_sha256=sha256_bytes(source_part.encode()), target_sha256=sha256_bytes(target_part.encode()), authority_task_title=meta.get("task_title"), candidate_solution_title=meta.get("solution_title"), authority_solution_status="source_supplied" if index in SOLUTION_INDICES else "source_absent", has_authority_solution=index in SOLUTION_INDICES, source_solution_checked=True, hint_present=bool(meta.get("hint_field")), graded=point is not None, point_value=point, unit_kind="exercise", translation_state=state))

    for index in SOLUTION_INDICES:
        meta = solution_meta[index]
        source_key = f"solution{index}_source"
        target_key = f"solution{index}_target"
        exercise_id = f"o011-brenner-u07-w07-e{index:03d}"
        records.append(base_record(f"{exercise_id}-solution", "unit", checkpoint, **common, order=1, parent_id=exercise_id, path=f"source/units/unit-07/worksheet07_exercise{index:02d}_solution.id.tex", source_local_id=f"worksheet07:exercise:{index}:solution", source_locator=meta.get("solution_title"), source_sha256=bindings[source_key]["sha256"], target_sha256=bindings[target_key]["sha256"], pageid=meta.get("pageid"), revid=meta.get("revid"), unit_kind="source_supplied_solution", translation_state=state))

    static_assets = preflight["media"]["assets"]
    rights_ids: list[str] = []
    asset_ids: list[str] = []
    for index, asset in enumerate(static_assets, 1):
        asset_id = f"o011-asset-file-u07-{slug(asset['filename'])}"
        rights_id = f"o011-rights-media-u07-{index:02d}"
        asset_ids.append(asset_id); rights_ids.append(rights_id)
        records.append(base_record(rights_id, "rights", checkpoint, source_local_id=f"Commons pageid:{asset['commons_pageid']}/revid:{asset['commons_lastrevid']}", component_scope=f"authority/media/{asset['filename']}", evidence_path="qa/unit-07/AUTHORITY_PREFLIGHT.json", evidence_sha256=bindings["preflight"]["sha256"], media_rights_manifest_path=bindings["media_rights_manifest"]["path"], media_rights_manifest_sha256=bindings["media_rights_manifest"]["sha256"], attribution=asset.get("artist_text"), license=asset.get("license"), license_url=asset.get("license_url"), redistribution_permitted=True, release_asset=True, rights_status="admitted_component_license"))
        records.append(base_record(asset_id, "asset", checkpoint, parent_id=LECTURE_ID, order=index, path=f"authority/media/{asset['filename']}", source_local_id=f"File:{asset['filename']}", source_locator=asset["description_url"], source_sha256=bindings[f"media:{asset['filename']}"]["sha256"], expected_bytes=bindings[f"media:{asset['filename']}"]["bytes"], binary_present=True, mime=asset["mime"], commons_pageid=asset["commons_pageid"], commons_lastrevid=asset["commons_lastrevid"], commons_sha1=asset["commons_sha1"], rights_component_id=rights_id))
    interactive_qa = load_json(paths["interactive_qa"])
    for offset, asset in enumerate(interactive_manifest["assets"], len(static_assets) + 1):
        asset_id = f"o011-asset-file-u07-{slug(asset['filename'])}"
        rights_id = f"o011-rights-media-u07-{offset:02d}"
        asset_ids.append(asset_id); rights_ids.append(rights_id)
        qa_asset = next(item for item in interactive_qa["assets"] if item["filename"] == asset["filename"])
        records.append(base_record(rights_id, "rights", checkpoint, source_local_id=f"Commons pageid:{asset['commons_pageid']}/revid:{asset['commons_lastrevid']}", component_scope=f"authority/media/{asset['filename']}", evidence_path="qa/unit-07/INTERACTIVE_MEDIA_QA.json", evidence_sha256=bindings["interactive_qa"]["sha256"], attribution=asset.get("creator"), license=asset.get("license"), license_url=asset.get("license_url"), redistribution_permitted=True, release_asset=True, rights_status="admitted_component_license"))
        records.append(base_record(asset_id, "asset", checkpoint, parent_id=f"o011-brenner-u07-w07-e013-solution", order=offset, path=f"authority/media/{asset['filename']}", source_local_id=f"File:{asset['filename']}", source_locator=asset["source_page"], source_sha256=bindings[f"media:{asset['filename']}"]["sha256"], expected_bytes=bindings[f"media:{asset['filename']}"]["bytes"], binary_present=True, mime="image/gif", commons_pageid=asset["commons_pageid"], commons_lastrevid=asset["commons_lastrevid"], commons_sha1=asset["sha1"], creator=asset["creator"], rights_component_id=rights_id, interactive=True, alt_text_source=asset.get("alt_text_source")))

    def add_artifact(artifact_id: str, path_key: str, parent_id: str, kind: str, language: str | None, locale: str | None, source_key: str | None = None) -> None:
        target = bindings[path_key]
        fields: dict[str, object] = {"artifact_kind": kind, "bytes": target["bytes"], "path": target["path"], "media_type": "application/pdf" if target["path"].endswith(".pdf") else ("application/json" if target["path"].endswith(".json") else ("text/markdown" if target["path"].endswith(".md") else ("text/csv" if target["path"].endswith(".csv") else ("image/gif" if target["path"].endswith(".gif") else ("image/png" if target["path"].endswith(".png") else ("image/svg+xml" if target["path"].endswith(".svg") else "application/x-tex")))))), "parent_id": parent_id, "rights_component_id": TEXT_RIGHTS_ID, "component_rights_ids": [TEXT_RIGHTS_ID], "target_sha256": target["sha256"], "language": language, "locale": locale}
        if source_key:
            fields["source_sha256"] = bindings[source_key]["sha256"]
        elif language == "German":
            # A frozen source artifact is not itself a translation target.
            fields["source_sha256"] = target["sha256"]
            fields["target_sha256"] = None
        records.append(base_record(artifact_id, "artifact", checkpoint, **fields, translation_state=state if language == "Indonesian" else "source_frozen"))

    # Frozen authority and translated TeX artifacts are kept as paired, explicit provenance.
    add_artifact("o011-artifact-u07-l07-source-tex", "lecture_source", LECTURE_ID, "frozen_authority_tex_fragment", "German", "de-DE")
    add_artifact("o011-artifact-u07-l07-tex", "lecture_target", LECTURE_ID, "translated_tex_fragment", "Indonesian", "id-ID", "lecture_source")
    add_artifact("o011-artifact-u07-w07-source-tex", "worksheet_source", WORKSHEET_ID, "frozen_authority_tex_fragment", "German", "de-DE")
    add_artifact("o011-artifact-u07-w07-tex", "worksheet_target", WORKSHEET_ID, "translated_tex_fragment", "Indonesian", "id-ID", "worksheet_source")
    for index in SOLUTION_INDICES:
        exercise_id = f"o011-brenner-u07-w07-e{index:03d}"
        add_artifact(f"o011-artifact-u07-w07-e{index:03d}-solution-source-tex", f"solution{index}_source", exercise_id + "-solution", "frozen_authority_tex_fragment", "German", "de-DE")
        add_artifact(f"o011-artifact-u07-w07-e{index:03d}-solution-tex", f"solution{index}_target", exercise_id + "-solution", "translated_tex_fragment", "Indonesian", "id-ID", f"solution{index}_source")
    add_artifact("o011-artifact-u07-authority-preflight", "preflight", UNIT_ID, "authority_source_solution_media_closure", None, None)
    add_artifact("o011-artifact-u07-interactive-manifest", "interactive_manifest", UNIT_ID, "interactive_media_manifest", None, None)
    add_artifact("o011-artifact-u07-interactive-qa", "interactive_qa", UNIT_ID, "interactive_media_qa_receipt", None, None)
    add_artifact("o011-artifact-u07-media-config", "media_config", UNIT_ID, "reader_media_configuration", "Indonesian", "id-ID")
    add_artifact("o011-artifact-u07-lecture-correction-manifest", "lecture_manifest", LECTURE_ID, "translation_correction_manifest", None, None)
    add_artifact("o011-artifact-u07-worksheet-correction-manifest", "worksheet_manifest", WORKSHEET_ID, "translation_correction_manifest", None, None)
    add_artifact("o011-artifact-u07-tex-safe-attribution-decision", "tex_safe_decision", LECTURE_ID, "reader_compatibility_correction_decision", None, None)
    for key, target_id, label in [("lecture_receipt", LECTURE_ID, "lecture"), ("worksheet_receipt", WORKSHEET_ID, "worksheet")]:
        add_artifact(f"o011-artifact-u07-{label}-translation-receipt", key, target_id, "translation_structure_receipt", None, None)
    for index in SOLUTION_INDICES:
        add_artifact(f"o011-artifact-u07-solution{index}-translation-receipt", f"solution{index}_receipt", f"o011-brenner-u07-w07-e{index:03d}-solution", "translation_structure_receipt", None, None)

    reader_bound = all(key in bindings for key in ("reader_pdf", "reader_wrapper", "build_receipt", "structural_receipt", "boundary_receipt", "visual_receipt", "math_receipt"))
    reader_evidence: dict[str, object] | None = None
    if reader_bound:
        reader_evidence = validate_reader_inputs(root, paths, bindings)
        add_artifact("o011-artifact-u07-reader-pdf", "reader_pdf", EDITION_ID, "cumulative_pdf_reader", "Indonesian", "id-ID")
        add_artifact("o011-artifact-u07-reader-wrapper", "reader_wrapper", EDITION_ID, "reader_wrapper_with_model_provenance", None, None)
        add_artifact("o011-artifact-u07-build-receipt", "build_receipt", UNIT_ID, "deterministic_pdf_build_receipt", None, None)
        add_artifact("o011-artifact-u07-structural-receipt", "structural_receipt", UNIT_ID, "pdf_structural_qa_receipt", None, None)
        add_artifact("o011-artifact-u07-boundary-receipt", "boundary_receipt", UNIT_ID, "pdf_boundary_qa_receipt", None, None)
        add_artifact("o011-artifact-u07-visual-receipt", "visual_receipt", UNIT_ID, "pdf_visual_qa_receipt", None, None)
        add_artifact("o011-artifact-u07-math-receipt", "math_receipt", UNIT_ID, "post_repair_math_qa_receipt", None, None)

    # QA events bind every current authority/translation/interactive receipt.
    def qa(qid: str, target_id: str, receipt_key: str, kind: str, artifact_id: str | None = None, values: dict[str, object] | None = None) -> None:
        fields: dict[str, object] = {"parent_id": UNIT_ID, "target_id": target_id, "receipt_path": bindings[receipt_key]["path"], "evidence_sha256": bindings[receipt_key]["sha256"], "result": "pass", "qa_kind": kind, "values": values or {}, "translation_state": state}
        if artifact_id is not None:
            fields["artifact_id"] = artifact_id
        records.append(base_record(qid, "qa_event", checkpoint, **fields))
    qa("o011-qa-unit07-authority-preflight", UNIT_ID, "preflight", "authority_source_solution_media_closure", "o011-artifact-u07-authority-preflight")
    qa("o011-qa-unit07-lecture-translation", LECTURE_ID, "lecture_receipt", "translation_structure", "o011-artifact-u07-lecture-translation-receipt")
    qa("o011-qa-unit07-worksheet-translation", WORKSHEET_ID, "worksheet_receipt", "translation_structure", "o011-artifact-u07-worksheet-translation-receipt")
    for index in SOLUTION_INDICES:
        solution_id = f"o011-brenner-u07-w07-e{index:03d}-solution"
        qa(f"o011-qa-unit07-solution{index}-translation", solution_id, f"solution{index}_receipt", "translation_structure", f"o011-artifact-u07-solution{index}-translation-receipt")
    qa("o011-qa-unit07-solution-closure", WORKSHEET_ID, "preflight", "solution_hint_point_closure", "o011-artifact-u07-authority-preflight", {"exercise_count": 19, "graded_point_total": 26, "graded_point_values": [3, 5, 8, 6, 4], "hint_indices": [], "missing_solution_indices": [i for i in range(1, 20) if i not in SOLUTION_INDICES], "supplied_solution_indices": list(SOLUTION_INDICES)})
    qa("o011-qa-unit07-interactive-media", "o011-brenner-u07-w07-e013-solution", "interactive_qa", "interactive_media_rights_and_surface_closure", "o011-artifact-u07-interactive-qa", {"asset_count": 2, "source_links_preserved": True})
    qa("o011-qa-unit07-media-config", UNIT_ID, "media_config", "reader_media_configuration", "o011-artifact-u07-media-config", {"static_asset_count": 3, "interactive_asset_count": 2})
    qa("o011-qa-unit07-correction-closure", UNIT_ID, "tex_safe_decision", "translation_and_reader_correction_closure", "o011-artifact-u07-tex-safe-attribution-decision", {"correction_ids": list(CORRECTION_IDS)})
    if reader_bound:
        qa("o011-qa-unit07-pdf-build", UNIT_ID, "build_receipt", "deterministic_pdf_build", "o011-artifact-u07-build-receipt", {"cycles": 2})
        qa("o011-qa-unit07-pdf-structural", UNIT_ID, "structural_receipt", "pdf_structural_accessibility_and_content", "o011-artifact-u07-structural-receipt", {"passed": True})
        qa("o011-qa-unit07-pdf-boundary", EDITION_ID, "boundary_receipt", "independent_pdf_boundary", "o011-artifact-u07-boundary-receipt", {"passed": True})
        qa("o011-qa-unit07-pdf-visual", EDITION_ID, "visual_receipt", "pdf_visual_layout_qa", "o011-artifact-u07-visual-receipt", {"passed": True})
        qa("o011-qa-unit07-pdf-math", UNIT_ID, "math_receipt", "post_repair_mathematical_and_topology_audit", "o011-artifact-u07-math-receipt", {"passed": True})
        qa("o011-qa-unit07-model-provenance", EDITION_ID, "reader_wrapper", "model_provenance_presence", "o011-artifact-u07-reader-wrapper", {"model_identification": MODEL_IDENTIFICATION, "exact_occurrences": 1, "source_and_human_credits_preserved": True})

    # Two explicit translation-only corrections; upstream reporting remains deferred.
    correction_targets = [("lecture_manifest", "lecture_receipt", "o011-brenner-u07-l07", "O011-TRANS-0070"), ("worksheet_manifest", "worksheet_receipt", WORKSHEET_ID, "O011-TRANS-0071"), ("tex_safe_decision", "math_receipt", "o011-brenner-u07-l07", "O011-TEX-0072")]
    for number, (manifest_key, receipt_key, target_id, correction_id) in enumerate(correction_targets, 70):
        manifest = load_json(paths[manifest_key])
        if manifest_key == "tex_safe_decision":
            description = str(manifest.get("reason", ""))
            disposition = str(manifest.get("decision", ""))
        else:
            description = str(manifest.get("translation_only_deltas", [""])[0])
            disposition = "Declared translation-only delta; protected topology and mathematical tokens preserved"
        target_binding = {**bindings["lecture_target" if target_id == LECTURE_ID else "worksheet_target"], "target_id": target_id}
        validation_key = receipt_key if receipt_key in paths else manifest_key
        validation = dict(bindings[validation_key])
        validation["checks_passed"] = len(load_json(paths[validation_key]).get("checks", {})) if paths[validation_key].suffix == ".json" else None
        records.append(base_record(f"o011-corr-{number:04d}", "correction", checkpoint, source_local_id=correction_id, severity="P2", description=description, disposition=disposition, correction_status="corrected_in_target", upstream_report_disposition="deferred_until_full_corpus", ledger_path=bindings["adverse"]["path"], ledger_sha256=bindings["adverse"]["sha256"], target_ids=[target_id], target_bindings=[target_binding], correction_manifests=[bindings[manifest_key]], validation_binding=validation))

    # Structural, provenance, rights, correction, QA, and source-solution relations.
    add_relation(records, checkpoint, "o011-rel-u06-precedes-u07", "precedes", "o011-brenner-u06", UNIT_ID)
    add_relation(records, checkpoint, "o011-rel-u07-has-part-l07", "has_part", UNIT_ID, LECTURE_ID)
    add_relation(records, checkpoint, "o011-rel-u07-has-part-w07", "has_part", UNIT_ID, WORKSHEET_ID)
    for prefix, parent, count in [("l07-s", LECTURE_ID, 2), ("w07-s", WORKSHEET_ID, 2)]:
        for i in range(1, count + 1):
            sid = f"o011-brenner-u07-{prefix}{i:02d}"
            add_relation(records, checkpoint, f"o011-rel-{prefix}{i:02d}-has-part", "has_part", parent, sid)
            if i > 1:
                add_relation(records, checkpoint, f"o011-rel-{prefix}{i-1:02d}-precedes-{i:02d}", "precedes", f"o011-brenner-u07-{prefix}{i-1:02d}", sid)
    for i in range(1, 20):
        eid = f"o011-brenner-u07-w07-e{i:03d}"
        add_relation(records, checkpoint, f"o011-rel-u07-w07-has-part-e{i:03d}", "has_part", WORKSHEET_ID, eid)
        if i > 1:
            add_relation(records, checkpoint, f"o011-rel-u07-w07-e{i-1:03d}-precedes-e{i:03d}", "precedes", f"o011-brenner-u07-w07-e{i-1:03d}", eid)
        if i in SOLUTION_INDICES:
            sid = f"{eid}-solution"
            add_relation(records, checkpoint, f"o011-rel-u07-w07-e{i:03d}-has-solution", "has_part", eid, sid)
            add_relation(records, checkpoint, f"o011-rel-u07-w07-e{i:03d}-solution-solves", "solves", sid, eid)
    artifact_targets = [("o011-artifact-u07-l07-tex", LECTURE_ID), ("o011-artifact-u07-w07-tex", WORKSHEET_ID)] + [(f"o011-artifact-u07-w07-e{i:03d}-solution-tex", f"o011-brenner-u07-w07-e{i:03d}-solution") for i in SOLUTION_INDICES]
    artifact_targets.append(("o011-artifact-u07-tex-safe-attribution-decision", LECTURE_ID))
    if reader_bound:
        artifact_targets.extend([
            ("o011-artifact-u07-reader-pdf", EDITION_ID),
            ("o011-artifact-u07-reader-wrapper", EDITION_ID),
        ])
    for aid, target in artifact_targets:
        add_relation(records, checkpoint, f"o011-rel-{aid}-represents", "represents", aid, target)
    for aid in ["o011-artifact-u07-authority-preflight", "o011-artifact-u07-interactive-manifest", "o011-artifact-u07-interactive-qa", "o011-artifact-u07-media-config"]:
        add_relation(records, checkpoint, f"o011-rel-{aid}-evidences-unit", "evidences", aid, UNIT_ID)
    for rid, aid in zip(rights_ids, asset_ids):
        add_relation(records, checkpoint, f"o011-rel-{rid}-governs-asset", "governs", rid, aid)
    for aid in asset_ids[:3]:
        add_relation(records, checkpoint, f"o011-rel-{aid}-used-by-lecture", "used_by", aid, LECTURE_ID)
    for aid in asset_ids[3:]:
        add_relation(records, checkpoint, f"o011-rel-{aid}-used-by-solution13", "used_by", aid, "o011-brenner-u07-w07-e013-solution")
    for number, target in ((70, LECTURE_ID), (71, WORKSHEET_ID), (72, LECTURE_ID)):
        add_relation(records, checkpoint, f"o011-rel-corr-{number:04d}-corrects", "corrects", f"o011-corr-{number:04d}", target)
    for q in [r for r in records if r["entity_type"] == "qa_event"]:
        add_relation(records, checkpoint, f"o011-rel-{q['id']}-evidences-target", "evidences", q["id"], q["target_id"])

    # Add explicit source artifact relations for all frozen authority fragments.
    for aid, target in [("o011-artifact-u07-l07-source-tex", LECTURE_ID), ("o011-artifact-u07-w07-source-tex", WORKSHEET_ID)] + [(f"o011-artifact-u07-w07-e{i:03d}-solution-source-tex", f"o011-brenner-u07-w07-e{i:03d}-solution") for i in SOLUTION_INDICES]:
        add_relation(records, checkpoint, f"o011-rel-{aid}-evidences-source", "evidences", aid, target)
    if reader_bound:
        for aid in ("o011-artifact-u07-build-receipt", "o011-artifact-u07-structural-receipt", "o011-artifact-u07-boundary-receipt", "o011-artifact-u07-visual-receipt", "o011-artifact-u07-math-receipt"):
            add_relation(records, checkpoint, f"o011-rel-{aid}-evidences-reader", "evidences", aid, EDITION_ID)
    return sorted(records, key=lambda item: str(item["id"]))


def validate_records(baseline: list[dict[str, object]], added: list[dict[str, object]], schema: dict[str, object]) -> dict[str, int]:
    counts = Counter(str(record.get("entity_type")) for record in added)
    actual = {kind: counts.get(kind, 0) for kind in sorted(ENTITY_TYPES)}
    if len({str(record["id"]) for record in baseline + added}) != len(baseline) + len(added):
        raise RuntimeError("combined backend IDs are not unique")
    if [record["id"] for record in added] != sorted(record["id"] for record in added):
        raise RuntimeError("Unit 7 suffix IDs are not sorted")
    all_ids = {str(record["id"]) for record in baseline + added}
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors: list[str] = []
    for record in baseline + added:
        errors.extend(f"{record['id']}: {error.message}" for error in validator.iter_errors(record))
    if errors:
        raise RuntimeError("JSON Schema validation failed: " + "; ".join(errors[:10]))
    for record in added:
        for key in ("parent_id", "resource_id", "edition_id", "rights_component_id", "target_id", "artifact_id", "from_id", "to_id"):
            value = record.get(key)
            if value is not None and str(value) not in all_ids:
                raise RuntimeError(f"unresolved {key} on {record['id']}: {value}")
    return actual


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--translation-state", default=DEFAULT_TRANSLATION_STATE)
    args = parser.parse_args()
    if args.translation_state not in {"translated", "visually_checked"}:
        raise RuntimeError("Unit 7 translation state must be translated or visually_checked")
    root = args.root.resolve()
    jsonl_prefix, csv_prefix, baseline = assert_prefix(root)
    preflight = load_json(root / "qa/unit-07/AUTHORITY_PREFLIGHT.json")
    paths = paths_for(root, preflight)
    candidate_reader_paths = optional_reader_paths(root)
    reader_bound = all(path.is_file() for path in candidate_reader_paths.values())
    if reader_bound:
        paths.update(candidate_reader_paths)
    effective_state = "visually_checked" if reader_bound else args.translation_state
    bindings = file_bindings(paths)
    preflight, interactive_manifest, _ = validate_inputs(root, paths, bindings)
    suffix = make_suffix(root, args.checkpoint, effective_state, paths, bindings, preflight, interactive_manifest)
    counts = validate_records(baseline, suffix, load_json(paths["schema"]))
    jsonl_path = root / "backend/records.jsonl"
    csv_path = root / "backend/records.csv"
    extension_jsonl = b"".join(canonical_json(record) for record in suffix)
    jsonl_path.write_bytes(jsonl_prefix + extension_jsonl)
    csv_buffer = io.StringIO(newline="")
    writer = csv.DictWriter(csv_buffer, fieldnames=CSV_FIELDS, extrasaction="ignore", lineterminator="\r\n")
    for record in suffix:
        writer.writerow({field: record.get(field) for field in CSV_FIELDS})
    csv_path.write_bytes(csv_prefix + csv_buffer.getvalue().encode("utf-8"))
    outputs = {"records_jsonl": binding(jsonl_path, root), "records_csv": binding(csv_path, root)}
    manifest = {
        "schema_version": 1,
        "workflow": WORKFLOW,
        "checkpoint": args.checkpoint,
        "generator": binding(root / "scripts/export_backend_v7.py", root),
        "verifier": binding(root / "scripts/verify_backend_v7.py", root) if (root / "scripts/verify_backend_v7.py").is_file() else None,
        "baseline": {"record_count": BASELINE_RECORD_COUNT, "jsonl_bytes": BASELINE_JSONL_BYTES, "jsonl_sha256": BASELINE_JSONL_SHA256, "csv_lines_including_header": BASELINE_CSV_LINES, "csv_bytes": BASELINE_CSV_BYTES, "csv_sha256": BASELINE_CSV_SHA256, "preserved_byte_identically": True},
        "unit07_extension": {
            "record_count": len(suffix), "entity_counts": counts, "unit_id": UNIT_ID, "lecture_sections": 2, "worksheet_sections": 2, "exercise_count": 19, "hint_indices": [], "source_solution_indices": list(SOLUTION_INDICES), "source_solution_absent_indices": [i for i in range(1, 20) if i not in SOLUTION_INDICES], "graded_point_values": [3, 5, 8, 6, 4], "graded_point_total": 26, "static_asset_count": 3, "interactive_asset_count": 2, "correction_ids": list(CORRECTION_IDS), "model_identification": MODEL_IDENTIFICATION, "translation_state": effective_state, "reader_status": "final_cumulative_reader_bound" if reader_bound else "not_yet_bound", "html_status": "absent_not_claimed",
            **({"reader_pdf": bindings["reader_pdf"], "reader_pages": load_json(paths["boundary_receipt"]).get("pdf", {}).get("pages")} if reader_bound else {}),
        },
        "inputs": bindings,
        "outputs": outputs,
        "combined": {"record_count": BASELINE_RECORD_COUNT + len(suffix), "entity_counts": {kind: Counter(str(record.get("entity_type")) for record in baseline + suffix).get(kind, 0) for kind in sorted(ENTITY_TYPES)}},
        "claims": {"all_ids_unique": True, "all_references_resolve": True, "json_schema_valid": True, "unit07_authority_solution_media_closure_current": True, "unit07_translation_receipts_current": True, "unit07_correction_manifests_current": True, "interactive_surfaces_preserved": True, "reader_pdf_bound": reader_bound, "cumulative_pdf_present": reader_bound, "build_structural_visual_math_current": reader_bound, "model_provenance_current": reader_bound, "cumulative_html_present": False},
    }
    manifest_path = root / "backend/MANIFEST.json"
    manifest_path.write_bytes((json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    print(json.dumps({"status": "pass", "baseline_records": BASELINE_RECORD_COUNT, "added_records": len(suffix), "combined_records": BASELINE_RECORD_COUNT + len(suffix), "entity_counts": counts, "jsonl": outputs["records_jsonl"], "csv": outputs["records_csv"], "manifest": binding(manifest_path, root)}, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
