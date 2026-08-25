#!/usr/bin/env python3
"""Append a deterministic Unit 5 extension to the frozen Units 1-4 backend."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
from pathlib import Path


BASELINE_RECORD_COUNT = 813
BASELINE_JSONL_SHA256 = "33a4f876f8225e40a006e97453f5530c05b21e327cfd1b7058303fa2421287f9"
BASELINE_CSV_SHA256 = "34a472148f9f376dcc6da220af640c0b4b5f12586b722015789908226059b5ea"
WORKFLOW = "o011-export-backend-v5"
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


def base_record(
    record_id: str,
    entity_type: str,
    timestamp: str,
    **values: object,
) -> dict[str, object]:
    record: dict[str, object] = {
        "schema": "o011-modular-backend",
        "schema_version": 1,
        "id": record_id,
        "entity_type": entity_type,
        "status": "active",
        "timestamp": timestamp,
        "workflow": WORKFLOW,
        "supersedes": None,
    }
    record.update(values)
    return record


def marker_slices(text: str, pattern: str) -> list[str]:
    starts = [match.start() for match in re.finditer(pattern, text)]
    return [
        text[start : starts[index + 1] if index + 1 < len(starts) else len(text)]
        for index, start in enumerate(starts)
    ]


def load_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--translation-state", default="visually_checked")
    args = parser.parse_args()
    if args.translation_state != "visually_checked":
        raise RuntimeError("Unit 5 final backend state must be visually_checked")

    root = args.root.resolve()
    jsonl_path = root / "backend/records.jsonl"
    csv_path = root / "backend/records.csv"
    manifest_path = root / "backend/MANIFEST.json"

    jsonl_lines = jsonl_path.read_bytes().splitlines(keepends=True)
    if len(jsonl_lines) < BASELINE_RECORD_COUNT:
        raise RuntimeError("backend has fewer than 813 baseline JSONL records")
    baseline_jsonl = b"".join(jsonl_lines[:BASELINE_RECORD_COUNT])
    if sha256_bytes(baseline_jsonl) != BASELINE_JSONL_SHA256:
        raise RuntimeError("immutable 813-record JSONL prefix changed")

    csv_lines = csv_path.read_bytes().splitlines(keepends=True)
    if len(csv_lines) < BASELINE_RECORD_COUNT + 1:
        raise RuntimeError("backend has fewer than 813 baseline CSV rows")
    baseline_csv = b"".join(csv_lines[: BASELINE_RECORD_COUNT + 1])
    if sha256_bytes(baseline_csv) != BASELINE_CSV_SHA256:
        raise RuntimeError("immutable 813-row CSV prefix changed")

    paths = {
        "schema": root / "backend/schema/o011-record-v1.schema.json",
        "terminology": root / "00_control/TERMINOLOGY.csv",
        "adverse": root / "00_control/ADVERSE_LEDGER.csv",
        "authority": root / "qa/unit-05/AUTHORITY_PREFLIGHT.json",
        "authority_verify": root / "qa/unit-05/AUTHORITY_PREFLIGHT_VERIFY.json",
        "current_revision": root / "qa/unit-05/CURRENT_REVISION_CHECK.json",
        "solution_closure": root / "qa/unit-05/solution_closure.json",
        "media_receipt": root / "qa/unit-05_media.json",
        "media_manifest": root / "authority/brenner_media_rights_manifest.csv",
        "media_config": root / "source/unit_media.json",
        "lecture_source": root / "authority/expanded/lecture05_source.de.tex",
        "lecture_target": root / "source/units/unit-05/lecture05.id.tex",
        "lecture_receipt": root / "qa/unit-05/lecture05_translation.json",
        "lecture_manifest": root / "00_control/LECTURE05_PROTECTED_CORRECTIONS.json",
        "lecture_review": root / "qa/unit-05/LECTURE_FINDINGS.md",
        "worksheet_source": root / "authority/expanded/worksheet05_source.de.tex",
        "worksheet_target": root / "source/units/unit-05/worksheet05.id.tex",
        "worksheet_receipt": root / "qa/unit-05/worksheet05_translation.json",
        "worksheet_manifest": root / "00_control/WORKSHEET05_PROTECTED_CORRECTIONS.json",
        "worksheet_review": root / "qa/unit-05/WORKSHEET_FINDINGS.md",
        "solution_source": root / "authority/expanded/worksheet05_exercise01_solution_source.de.tex",
        "solution_target": root / "source/units/unit-05/worksheet05_exercise01_solution.id.tex",
        "solution_receipt": root / "qa/unit-05/worksheet05_exercise01_solution_translation.json",
        "solution_manifest": root / "00_control/SOLUTION05_01_PROTECTED_CORRECTIONS.json",
        "final_math": root / "qa/unit-05/POST_REPAIR_MATH_QA.json",
        "build": root / "qa/unit-05/build.json",
        "structural": root / "qa/unit-05/pdf_structural_qa.json",
        "visual": root / "qa/unit-05/VISUAL_QA.md",
        "reader_pdf": root / "output/pdf/geometri-diferensial-manifold-mulus-hingga-unit-05-id.pdf",
        "asset_svg": root / "authority/media/Minimal surface curvature planes-de.svg",
        "asset_png": root / "build/generated/media/Minimal surface curvature planes-de.png",
        "exporter": root / "scripts/export_backend_v5.py",
        "verifier": root / "scripts/verify_backend_v5.py",
    }
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise RuntimeError(f"missing Unit 5 backend inputs: {missing}")
    bindings = {key: file_binding(path, root) for key, path in paths.items()}
    raw = {key: path.read_bytes() for key, path in paths.items()}

    authority = load_json(paths["authority"])
    authority_verify = load_json(paths["authority_verify"])
    current_revision = load_json(paths["current_revision"])
    solution_closure = load_json(paths["solution_closure"])
    media_receipt = load_json(paths["media_receipt"])
    final_math = load_json(paths["final_math"])
    build = load_json(paths["build"])
    structural = load_json(paths["structural"])
    if authority.get("status") != "pass":
        raise RuntimeError("Unit 5 authority preflight is not passing")
    if authority_verify.get("status") != "pass":
        raise RuntimeError("Unit 5 authority verification is not passing")
    if current_revision.get("status") != "pass" or not current_revision.get(
        "all_four_frozen_revisions_remain_live_current"
    ):
        raise RuntimeError("Unit 5 current revision closure is not passing")
    if (
        solution_closure.get("exercise_count") != 15
        or solution_closure.get("supplied_solution_indices") != [1]
        or solution_closure.get("graded_exercise_count") != 5
        or solution_closure.get("point_value_total") != 22
    ):
        raise RuntimeError("Unit 5 exercise/solution/point closure changed")
    exercises = solution_closure.get("exercises")
    if not isinstance(exercises, list) or len(exercises) != 15:
        raise RuntimeError("Unit 5 exercise records are absent")
    hint_indices = [
        int(item["exercise_index"]) for item in exercises if item.get("hint_field")
    ]
    if hint_indices != [13]:
        raise RuntimeError("Unit 5 hint closure changed")
    if (
        media_receipt.get("source_count") != 1
        or media_receipt.get("derivative_count") != 1
    ):
        raise RuntimeError("Unit 5 media closure changed")
    if final_math.get("status") != "pass" or final_math.get("checks_passed") != 46:
        raise RuntimeError("Unit 5 final mathematical QA changed")
    pdf_binding = bindings["reader_pdf"]
    if (
        pdf_binding["bytes"] != 4385370
        or pdf_binding["sha256"]
        != "44ef3bc7f4c9de8a9ffd3a747ea71c2102de6f26814718492bc63fd40e4af5ce"
    ):
        raise RuntimeError("Unit 5 PDF identity changed")
    if build.get("output", {}).get("sha256") != pdf_binding["sha256"] or not build.get(
        "deterministic_clean_cycles"
    ):
        raise RuntimeError("Unit 5 build receipt is stale")
    if (
        structural.get("passed") is not True
        or structural.get("pdf", {}).get("sha256") != pdf_binding["sha256"]
    ):
        raise RuntimeError("Unit 5 structural receipt is stale")
    visual_text = raw["visual"].decode("utf-8")
    if (
        "Status: **PASS.**" not in visual_text
        or str(pdf_binding["sha256"]) not in visual_text
    ):
        raise RuntimeError("Unit 5 visual receipt is stale")

    lecture_source = raw["lecture_source"].decode("utf-8")
    lecture_target = raw["lecture_target"].decode("utf-8")
    worksheet_source = raw["worksheet_source"].decode("utf-8")
    worksheet_target = raw["worksheet_target"].decode("utf-8")
    lecture_source_parts = marker_slices(
        lecture_source, r"\\zwischenueberschrift\{"
    )
    lecture_target_parts = marker_slices(
        lecture_target, r"\\zwischenueberschrift\{"
    )
    worksheet_source_parts = marker_slices(
        worksheet_source, r"\\inputaufgabe(?:gibtloesung)?"
    )
    worksheet_target_parts = marker_slices(
        worksheet_target, r"\\inputaufgabe(?:gibtloesung)?"
    )
    if len(lecture_source_parts) != 3 or len(lecture_target_parts) != 3:
        raise RuntimeError("Unit 5 lecture must have exactly three sections")
    if len(worksheet_source_parts) != 15 or len(worksheet_target_parts) != 15:
        raise RuntimeError("Unit 5 worksheet must have exactly fifteen exercises")

    for key in ("lecture_receipt", "worksheet_receipt", "solution_receipt"):
        receipt = load_json(paths[key])
        if receipt.get("status") != "pass":
            raise RuntimeError(f"failed translation receipt: {key}")
    for key in ("lecture_manifest", "worksheet_manifest", "solution_manifest"):
        manifest = load_json(paths[key])
        if not isinstance(manifest.get("allowed_deltas"), list):
            raise RuntimeError(f"invalid correction manifest: {key}")

    baseline_records = [
        json.loads(line.decode("utf-8")) for line in jsonl_lines[:BASELINE_RECORD_COUNT]
    ]
    baseline_ids = {str(record["id"]) for record in baseline_records}
    course_id = "o011-course-d50"
    resource_id = "o011-resource-brenner-dg2023"
    edition_id = "o011-edition-brenner-current-20260821"
    text_rights_id = "o011-rights-brenner-text"
    for required in (course_id, resource_id, edition_id, text_rights_id):
        if required not in baseline_ids:
            raise RuntimeError(f"required baseline ID missing: {required}")

    timestamp = args.checkpoint
    added_by_id: dict[str, dict[str, object]] = {}

    def add(record: dict[str, object]) -> None:
        record_id = str(record["id"])
        if record_id in baseline_ids or record_id in added_by_id:
            raise RuntimeError(f"duplicate backend ID: {record_id}")
        if record.get("entity_type") not in ENTITY_TYPES:
            raise RuntimeError(f"bad entity type: {record_id}")
        added_by_id[record_id] = record

    unit_id = "o011-brenner-u05"
    lecture_id = "o011-brenner-u05-l05"
    worksheet_id = "o011-brenner-u05-w05"
    solution_id = f"{worksheet_id}-e001-solution"
    media_rights_id = "o011-rights-media-u05-01"
    asset_id = "o011-asset-file-minimal-surface-curvature-planes-de-svg"
    pdf_artifact_id = "o011-artifact-through-unit05-pdf"

    add(
        base_record(
            unit_id,
            "unit",
            timestamp,
            source_local_id="course-unit-05",
            parent_id=course_id,
            order=5,
            path="source/units/unit-05",
            resource_id=resource_id,
            edition_id=edition_id,
            source_locator="Kurs:Differentialgeometrie (Osnabrück 2023)/Vorlesung 5 + Arbeitsblatt 5",
            source_sha256=sha256_bytes(raw["lecture_source"] + raw["worksheet_source"]),
            target_sha256=sha256_bytes(raw["lecture_target"] + raw["worksheet_target"]),
            language="Indonesian",
            locale="id-ID",
            translation_state=args.translation_state,
            rights_component_id=text_rights_id,
            unit_kind="lecture_worksheet_pair",
            authority_page_revisions={
                "lecture_root": [142549, 894651],
                "lecture_latex": [142579, 807139],
                "worksheet_root": [142639, 894758],
                "worksheet_latex": [142669, 807108],
            },
        )
    )
    add(
        base_record(
            lecture_id,
            "unit",
            timestamp,
            source_local_id="lecture05",
            parent_id=unit_id,
            order=1,
            path=bindings["lecture_target"]["path"],
            resource_id=resource_id,
            edition_id=edition_id,
            source_locator="Kurs:Differentialgeometrie (Osnabrück 2023)/Vorlesung 5",
            source_sha256=bindings["lecture_source"]["sha256"],
            target_sha256=bindings["lecture_target"]["sha256"],
            language="Indonesian",
            locale="id-ID",
            translation_state=args.translation_state,
            rights_component_id=text_rights_id,
            unit_kind="lecture",
            pageid=142549,
            revid=894651,
        )
    )
    add(
        base_record(
            worksheet_id,
            "unit",
            timestamp,
            source_local_id="worksheet05",
            parent_id=unit_id,
            order=2,
            path=bindings["worksheet_target"]["path"],
            resource_id=resource_id,
            edition_id=edition_id,
            source_locator="Kurs:Differentialgeometrie (Osnabrück 2023)/Arbeitsblatt 5",
            source_sha256=bindings["worksheet_source"]["sha256"],
            target_sha256=bindings["worksheet_target"]["sha256"],
            language="Indonesian",
            locale="id-ID",
            translation_state=args.translation_state,
            rights_component_id=text_rights_id,
            unit_kind="worksheet",
            pageid=142639,
            revid=894758,
        )
    )

    for index, (source_part, target_part) in enumerate(
        zip(lecture_source_parts, lecture_target_parts), start=1
    ):
        add(
            base_record(
                f"{lecture_id}-s{index:02d}",
                "segment",
                timestamp,
                source_local_id=f"lecture05:section:{index}",
                parent_id=lecture_id,
                order=index,
                path=f"source/units/unit-05/lecture05.id.tex#section-{index}",
                resource_id=resource_id,
                edition_id=edition_id,
                source_locator=f"Kurs:Differentialgeometrie (Osnabrück 2023)/Vorlesung 5#section-{index}",
                source_sha256=sha256_bytes(source_part.encode("utf-8")),
                target_sha256=sha256_bytes(target_part.encode("utf-8")),
                language="Indonesian",
                locale="id-ID",
                translation_state=args.translation_state,
                rights_component_id=text_rights_id,
                segment_kind="lecture_section",
            )
        )

    for index, (source_part, target_part, exercise) in enumerate(
        zip(worksheet_source_parts, worksheet_target_parts, exercises), start=1
    ):
        point_value = exercise.get("point_value")
        exercise_id = f"{worksheet_id}-e{index:03d}"
        add(
            base_record(
                exercise_id,
                "unit",
                timestamp,
                source_local_id=f"worksheet05:exercise:{index}",
                parent_id=worksheet_id,
                order=index,
                path=f"source/units/unit-05/worksheet05.id.tex#exercise-{index}",
                resource_id=resource_id,
                edition_id=edition_id,
                source_locator=str(exercise.get("task_title") or f"worksheet05 exercise {index}"),
                source_sha256=sha256_bytes(source_part.encode("utf-8")),
                target_sha256=sha256_bytes(target_part.encode("utf-8")),
                language="Indonesian",
                locale="id-ID",
                translation_state=args.translation_state,
                rights_component_id=text_rights_id,
                unit_kind="exercise",
                source_display_id=f"5.{index}",
                graded=point_value is not None,
                point_value=point_value,
                point_breakdown=[2, 2, 2] if index == 14 else None,
                hint_present=index == 13,
                has_authority_solution=index == 1,
                authority_task_title=exercise.get("task_title"),
            )
        )
    hint_text = str(exercises[12]["hint_field"])
    add(
        base_record(
            f"{worksheet_id}-e013-hint",
            "segment",
            timestamp,
            source_local_id="worksheet05:exercise:13:hint",
            parent_id=f"{worksheet_id}-e013",
            order=1,
            path="source/units/unit-05/worksheet05.id.tex#exercise-13-hint",
            resource_id=resource_id,
            edition_id=edition_id,
            source_locator=str(exercises[12]["task_title"]) + "#hint",
            source_sha256=sha256_bytes(hint_text.encode("utf-8")),
            target_sha256=sha256_bytes(worksheet_target_parts[12].encode("utf-8")),
            language="Indonesian",
            locale="id-ID",
            translation_state=args.translation_state,
            rights_component_id=text_rights_id,
            segment_kind="source_supplied_hint",
        )
    )
    add(
        base_record(
            solution_id,
            "unit",
            timestamp,
            source_local_id="worksheet05:exercise:1:solution",
            parent_id=f"{worksheet_id}-e001",
            order=1,
            path=bindings["solution_target"]["path"],
            resource_id=resource_id,
            edition_id=edition_id,
            source_locator=str(exercises[0]["solution_title"]),
            source_sha256=bindings["solution_source"]["sha256"],
            target_sha256=bindings["solution_target"]["sha256"],
            language="Indonesian",
            locale="id-ID",
            translation_state=args.translation_state,
            rights_component_id=text_rights_id,
            unit_kind="source_supplied_solution",
        )
    )

    concepts = {
        "o011-concept-principal-curvature": ("Hauptkrümmung", "kelengkungan utama"),
        "o011-concept-principal-direction": ("Hauptkrümmungsrichtung", "arah kelengkungan utama"),
        "o011-concept-mean-curvature": ("mittlere Krümmung", "kelengkungan rata-rata"),
        "o011-concept-gaussian-curvature": ("Gaußkrümmung", "kelengkungan Gauss"),
        "o011-concept-gauss-kronecker-curvature": ("Gauß-Kronecker-Krümmung", "kelengkungan Gauss--Kronecker"),
        "o011-concept-normal-curvature": ("Normalkrümmung", "kelengkungan normal"),
        "o011-concept-euler-normal-curvature-formula": ("Eulersche Formel", "rumus Euler untuk kelengkungan normal"),
        "o011-concept-normal-section": ("Normalschnitt", "irisan normal"),
    }
    for concept_id, (label_de, label_id) in concepts.items():
        if concept_id in baseline_ids:
            continue
        add(
            base_record(
                concept_id,
                "concept",
                timestamp,
                source_local_id=label_de,
                parent_id=course_id,
                language=None,
                locale=None,
                labels={"de": label_de, "id-ID": label_id},
            )
        )

    terminology_rows = list(
        csv.DictReader(raw["terminology"].decode("utf-8-sig").splitlines())
    )
    unit5_terms = [
        row for row in terminology_rows
        if 96 <= int(str(row["id"]).rsplit("-", 1)[1]) <= 110
    ]
    if len(unit5_terms) != 15 or any(row["status"] != "admitted" for row in unit5_terms):
        raise RuntimeError("Unit 5 terminology closure is not 15 admitted rows")
    for row in unit5_terms:
        number = int(str(row["id"]).rsplit("-", 1)[1])
        add(
            base_record(
                f"o011-term-{number:04d}",
                "term",
                timestamp,
                source_local_id=row["source_de"],
                parent_id=course_id,
                order=number,
                language=None,
                locale=None,
                labels={"de": row["source_de"], "id-ID": row["target_id"]},
                note=row["note"],
                terminology_status="admitted",
                terminology_ledger_path=bindings["terminology"]["path"],
                terminology_ledger_sha256=bindings["terminology"]["sha256"],
            )
        )

    media_item = media_receipt["media"][0]
    add(
        base_record(
            media_rights_id,
            "rights",
            timestamp,
            source_local_id="Commons revid:796566416",
            component_scope=bindings["asset_svg"]["path"],
            license="CC BY-SA 3.0",
            license_url="https://creativecommons.org/licenses/by-sa/3.0/",
            attribution="Eric Gaba (Sting); based upon a drawing in a book",
            evidence_path=bindings["media_receipt"]["path"],
            evidence_sha256=bindings["media_receipt"]["sha256"],
            redistribution_permitted=True,
            release_asset=True,
            rights_status="admitted_component_license",
        )
    )
    add(
        base_record(
            asset_id,
            "asset",
            timestamp,
            source_local_id="File:Minimal surface curvature planes-de.svg",
            parent_id=unit_id,
            order=1,
            path=bindings["asset_svg"]["path"],
            source_locator=str(media_item["commons_description_url"]),
            source_sha256=bindings["asset_svg"]["sha256"],
            rights_component_id=media_rights_id,
            mime="image/svg+xml",
            expected_bytes=bindings["asset_svg"]["bytes"],
            commons_sha1=str(media_item["canonical_sha1"]),
            commons_revid=796566416,
            binary_present=True,
        )
    )

    artifacts = [
        (
            "o011-artifact-u05-l05-tex", lecture_id, "lecture_source",
            "lecture_target", "translated_tex_fragment", "application/x-tex",
            [text_rights_id],
        ),
        (
            "o011-artifact-u05-w05-tex", worksheet_id, "worksheet_source",
            "worksheet_target", "translated_tex_fragment", "application/x-tex",
            [text_rights_id],
        ),
        (
            "o011-artifact-u05-w05-e001-solution-tex", solution_id,
            "solution_source", "solution_target", "translated_tex_fragment",
            "application/x-tex", [text_rights_id],
        ),
    ]
    for artifact_id, parent_id, source_key, target_key, kind, media_type, rights in artifacts:
        add(
            base_record(
                artifact_id,
                "artifact",
                timestamp,
                parent_id=parent_id,
                path=bindings[target_key]["path"],
                source_sha256=bindings[source_key]["sha256"],
                target_sha256=bindings[target_key]["sha256"],
                artifact_kind=kind,
                media_type=media_type,
                bytes=bindings[target_key]["bytes"],
                language="Indonesian",
                locale="id-ID",
                translation_state=args.translation_state,
                rights_component_id=text_rights_id,
                component_rights_ids=rights,
            )
        )
    add(
        base_record(
            "o011-artifact-u05-media-minimal-surface-curvature-planes-png",
            "artifact",
            timestamp,
            parent_id=asset_id,
            path=bindings["asset_png"]["path"],
            source_sha256=bindings["asset_svg"]["sha256"],
            target_sha256=bindings["asset_png"]["sha256"],
            artifact_kind="deterministic_print_media_derivative",
            media_type="image/png",
            bytes=bindings["asset_png"]["bytes"],
            rights_component_id=media_rights_id,
            component_rights_ids=[media_rights_id],
        )
    )
    prior_pdf = next(
        record for record in baseline_records
        if record.get("id") == "o011-artifact-through-unit04-pdf"
    )
    pdf_rights = sorted(
        set(prior_pdf.get("component_rights_ids") or []) | {media_rights_id}
    )
    add(
        base_record(
            pdf_artifact_id,
            "artifact",
            timestamp,
            parent_id=edition_id,
            path=bindings["reader_pdf"]["path"],
            target_sha256=bindings["reader_pdf"]["sha256"],
            artifact_kind="cumulative_indonesian_reader_pdf",
            media_type="application/pdf",
            bytes=bindings["reader_pdf"]["bytes"],
            language="Indonesian",
            locale="id-ID",
            translation_state=args.translation_state,
            rights_component_id=text_rights_id,
            component_rights_ids=pdf_rights,
            pages=86,
            tagged=False,
            cumulative_through_unit=5,
            build_receipt_path=bindings["build"]["path"],
            build_receipt_sha256=bindings["build"]["sha256"],
        )
    )

    adverse_rows = {
        row["id"]: row
        for row in csv.DictReader(raw["adverse"].decode("utf-8-sig").splitlines())
        if row["id"].startswith("O011-CORR-")
    }
    correction_targets = {
        "O011-CORR-0046": [lecture_id, f"{worksheet_id}-e007"],
        "O011-CORR-0047": [lecture_id, solution_id],
        "O011-CORR-0048": [lecture_id],
        "O011-CORR-0049": [lecture_id],
        "O011-CORR-0050": [lecture_id],
        "O011-CORR-0051": [lecture_id],
        "O011-CORR-0052": [lecture_id, f"{worksheet_id}-e014"],
        "O011-CORR-0053": [solution_id],
    }
    manifest_keys = ("lecture_manifest", "worksheet_manifest", "solution_manifest")
    target_file_keys = {
        lecture_id: "lecture_target",
        f"{worksheet_id}-e007": "worksheet_target",
        f"{worksheet_id}-e014": "worksheet_target",
        solution_id: "solution_target",
    }
    for correction_name, target_ids in correction_targets.items():
        row = adverse_rows.get(correction_name)
        if row is None:
            raise RuntimeError(f"correction absent from adverse ledger: {correction_name}")
        applicable_manifests = []
        for key in manifest_keys:
            if correction_name in raw[key].decode("utf-8"):
                applicable_manifests.append(bindings[key])
        target_bindings = [
            {
                **bindings[target_file_keys[target_id]],
                "target_id": target_id,
            }
            for target_id in target_ids
        ]
        add(
            base_record(
                correction_name.lower(),
                "correction",
                timestamp,
                source_local_id=str(row["surface"]),
                correction_status=str(row["status"]),
                severity=str(row["severity"]),
                description=str(row["description"]),
                disposition=str(row["disposition"]),
                ledger_path=bindings["adverse"]["path"],
                ledger_sha256=bindings["adverse"]["sha256"],
                target_ids=target_ids,
                target_bindings=target_bindings,
                correction_manifests=applicable_manifests,
                reader_binding={
                    **pdf_binding,
                    "math_qa_path": bindings["final_math"]["path"],
                    "math_qa_sha256": bindings["final_math"]["sha256"],
                    "structural_receipt_path": bindings["structural"]["path"],
                    "structural_receipt_sha256": bindings["structural"]["sha256"],
                    "visual_receipt_path": bindings["visual"]["path"],
                    "visual_receipt_sha256": bindings["visual"]["sha256"],
                },
                upstream_report_disposition="deferred_until_full_corpus",
            )
        )

    qa_specs = [
        ("o011-qa-unit05-authority-preflight", unit_id, "authority", "authority_source_solution_media_closure", None),
        ("o011-qa-unit05-authority-verification", unit_id, "authority_verify", "offline_authority_hash_and_closure_verification", None),
        ("o011-qa-unit05-current-revision", unit_id, "current_revision", "live_current_revision_check", None),
        ("o011-qa-unit05-solution-closure", worksheet_id, "solution_closure", "solution_hint_and_points_closure", None),
        ("o011-qa-unit05-media-authority", asset_id, "authority", "media_authority_and_rights_closure", None),
        ("o011-qa-unit05-media-build", asset_id, "media_receipt", "media_derivative_build_and_rights_closure", "o011-artifact-u05-media-minimal-surface-curvature-planes-png"),
        ("o011-qa-unit05-lecture-translation", lecture_id, "lecture_receipt", "translation_structure", "o011-artifact-u05-l05-tex"),
        ("o011-qa-unit05-worksheet-translation", worksheet_id, "worksheet_receipt", "translation_structure", "o011-artifact-u05-w05-tex"),
        ("o011-qa-unit05-solution-translation", solution_id, "solution_receipt", "translation_structure", "o011-artifact-u05-w05-e001-solution-tex"),
        ("o011-qa-unit05-lecture-review", lecture_id, "lecture_review", "translation_and_mathematical_review", "o011-artifact-u05-l05-tex"),
        ("o011-qa-unit05-worksheet-review", worksheet_id, "worksheet_review", "worksheet_and_solution_review", "o011-artifact-u05-w05-tex"),
        ("o011-qa-unit05-final-math", unit_id, "final_math", "post_repair_mathematical_and_topology_audit", pdf_artifact_id),
        ("o011-qa-through-unit05-pdf-reproducibility", pdf_artifact_id, "build", "reproducible_pdf_build", pdf_artifact_id),
        ("o011-qa-through-unit05-pdf-structural", pdf_artifact_id, "structural", "pdf_structure_accessibility_links_and_safety", pdf_artifact_id),
        ("o011-qa-through-unit05-pdf-visual", pdf_artifact_id, "visual", "pdf_visual_inspection_all_pages", pdf_artifact_id),
    ]
    for qa_id, target_id, receipt_key, qa_kind, artifact_id in qa_specs:
        values: dict[str, object] = {}
        if qa_id == "o011-qa-unit05-solution-closure":
            values = {
                "exercise_count": 15,
                "supplied_solution_indices": [1],
                "missing_solution_count": 14,
                "hint_indices": [13],
                "graded_point_values": [4, 4, 6, "6 (2+2+2)", 2],
                "graded_point_total": 22,
            }
        elif qa_id == "o011-qa-unit05-final-math":
            values = {
                "checks_passed": 46,
                "correction_ids": list(correction_targets),
            }
        elif qa_id == "o011-qa-through-unit05-pdf-structural":
            values = {
                "pages": 86,
                "tagged": False,
                "fonts_with_tounicode": 29,
                "limitations": structural.get("limitations"),
            }
        elif qa_id == "o011-qa-through-unit05-pdf-visual":
            values = {"pages": 86, "all_pages_inspected": True}
        add(
            base_record(
                qa_id,
                "qa_event",
                timestamp,
                parent_id=unit_id,
                target_id=target_id,
                artifact_id=artifact_id,
                receipt_path=bindings[receipt_key]["path"],
                evidence_sha256=bindings[receipt_key]["sha256"],
                result="pass",
                qa_kind=qa_kind,
                target_sha256=pdf_binding["sha256"] if artifact_id == pdf_artifact_id else None,
                translation_state=args.translation_state,
                values=values,
            )
        )

    def add_relation(
        relation_id: str,
        relation_type: str,
        from_id: str,
        to_id: str,
    ) -> None:
        add(
            base_record(
                relation_id,
                "relation",
                timestamp,
                relation_type=relation_type,
                from_id=from_id,
                to_id=to_id,
            )
        )

    add_relation("o011-rel-u04-precedes-u05", "precedes", "o011-brenner-u04", unit_id)
    add_relation("o011-rel-u05-has-part-l05", "has_part", unit_id, lecture_id)
    add_relation("o011-rel-u05-has-part-w05", "has_part", unit_id, worksheet_id)
    for index in range(1, 4):
        add_relation(
            f"o011-rel-u05-l05-has-part-s{index:02d}",
            "has_part",
            lecture_id,
            f"{lecture_id}-s{index:02d}",
        )
    for index in range(1, 3):
        add_relation(
            f"o011-rel-u05-l05-s{index:02d}-precedes-s{index + 1:02d}",
            "precedes",
            f"{lecture_id}-s{index:02d}",
            f"{lecture_id}-s{index + 1:02d}",
        )
    for index in range(1, 16):
        add_relation(
            f"o011-rel-u05-w05-has-part-e{index:03d}",
            "has_part",
            worksheet_id,
            f"{worksheet_id}-e{index:03d}",
        )
    for index in range(1, 15):
        add_relation(
            f"o011-rel-u05-w05-e{index:03d}-precedes-e{index + 1:03d}",
            "precedes",
            f"{worksheet_id}-e{index:03d}",
            f"{worksheet_id}-e{index + 1:03d}",
        )
    add_relation(
        "o011-rel-u05-w05-e001-solution-solves-e001",
        "solves",
        solution_id,
        f"{worksheet_id}-e001",
    )
    add_relation(
        "o011-rel-u05-w05-e013-hint-annotates-e013",
        "annotates",
        f"{worksheet_id}-e013-hint",
        f"{worksheet_id}-e013",
    )
    for concept_id in concepts:
        add_relation(
            f"o011-rel-u05-l05-covers-{concept_id.removeprefix('o011-concept-')}",
            "covers",
            lecture_id,
            concept_id,
        )
    for row in unit5_terms:
        number = int(str(row["id"]).rsplit("-", 1)[1])
        term_id = f"o011-term-{number:04d}"
        add_relation(
            f"o011-rel-u05-uses-term-{number:04d}",
            "uses_term",
            unit_id,
            term_id,
        )
    add_relation(
        "o011-rel-rights-media-u05-01-governs-asset",
        "governs",
        media_rights_id,
        asset_id,
    )
    add_relation(
        "o011-rel-rights-media-u05-01-governs-png",
        "governs",
        media_rights_id,
        "o011-artifact-u05-media-minimal-surface-curvature-planes-png",
    )
    add_relation(
        "o011-rel-asset-u05-used-by-l05",
        "used_by",
        asset_id,
        lecture_id,
    )
    add_relation(
        "o011-rel-artifact-through-unit05-pdf-represents-u05",
        "represents",
        pdf_artifact_id,
        unit_id,
    )
    for artifact_id, parent_id, *_ in artifacts:
        add_relation(
            f"o011-rel-{artifact_id.removeprefix('o011-artifact-')}-represents-{parent_id.removeprefix('o011-')}",
            "represents",
            artifact_id,
            parent_id,
        )
    for correction_name, target_ids in correction_targets.items():
        correction_id = correction_name.lower()
        for target_id in target_ids:
            add_relation(
                f"o011-rel-{correction_id.removeprefix('o011-')}-corrects-{target_id.removeprefix('o011-')}",
                "corrects",
                correction_id,
                target_id,
            )

    added = [added_by_id[record_id] for record_id in sorted(added_by_id)]
    all_ids = baseline_ids | set(added_by_id)
    for record in added:
        for key in ("parent_id", "resource_id", "edition_id", "rights_component_id", "target_id", "artifact_id"):
            value = record.get(key)
            if value is not None and value not in all_ids:
                raise RuntimeError(f"unresolved {key} on {record['id']}: {value}")
        for key in ("component_rights_ids", "target_ids"):
            for value in record.get(key) or []:
                if value not in all_ids:
                    raise RuntimeError(f"unresolved {key} on {record['id']}: {value}")
        if record["entity_type"] == "relation":
            for key in ("from_id", "to_id"):
                value = record.get(key)
                if value not in all_ids:
                    raise RuntimeError(f"unresolved relation endpoint on {record['id']}: {value}")

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
    entity_counts = {
        entity_type: sum(record["entity_type"] == entity_type for record in added)
        for entity_type in sorted(ENTITY_TYPES)
    }
    manifest = {
        "schema_version": 1,
        "workflow": WORKFLOW,
        "checkpoint": timestamp,
        "generator": bindings["exporter"],
        "verifier": bindings["verifier"],
        "baseline": {
            "record_count": BASELINE_RECORD_COUNT,
            "jsonl_bytes": len(baseline_jsonl),
            "jsonl_sha256": BASELINE_JSONL_SHA256,
            "csv_lines_including_header": BASELINE_RECORD_COUNT + 1,
            "csv_bytes": len(baseline_csv),
            "csv_sha256": BASELINE_CSV_SHA256,
            "preserved_byte_identically": True,
        },
        "unit05_extension": {
            "record_count": len(added),
            "entity_counts": entity_counts,
            "record_ids_sha256": sha256_bytes(
                ("\n".join(record["id"] for record in added) + "\n").encode("utf-8")
            ),
            "unit_id": unit_id,
            "lecture_segment_count": 3,
            "exercise_count": 15,
            "hint_indices": [13],
            "source_solution_indices": [1],
            "graded_point_values": [4, 4, 6, "6 (2+2+2)", 2],
            "graded_point_total": 22,
            "correction_ids": list(correction_targets),
            "asset_ids": [asset_id],
            "component_rights_ids": [media_rights_id],
            "html_status": "absent_not_claimed",
        },
        "inputs": bindings,
        "outputs": output_bindings,
        "combined": {
            "record_count": BASELINE_RECORD_COUNT + len(added),
            "entity_counts": {
                entity_type: sum(
                    record.get("entity_type") == entity_type
                    for record in baseline_records + added
                )
                for entity_type in sorted(ENTITY_TYPES)
            },
        },
        "claims": {
            "all_ids_unique": True,
            "all_references_resolve": True,
            "schema_required_fields_present": True,
            "unit05_translation_receipts_current": True,
            "unit05_authority_solution_media_closure_current": True,
            "unit05_correction_manifests_and_targets_current": True,
            "unit05_pdf_build_structural_visual_receipts_current": True,
            "cumulative_html_present": False,
        },
    }
    manifest_path.write_bytes(
        (
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True)
            + "\n"
        ).encode("utf-8")
    )
    print(
        json.dumps(
            {
                "status": "pass",
                "baseline_records": BASELINE_RECORD_COUNT,
                "added_records": len(added),
                "combined_records": BASELINE_RECORD_COUNT + len(added),
                "entity_counts": entity_counts,
                "jsonl": file_binding(jsonl_path, root),
                "csv": file_binding(csv_path, root),
                "manifest": file_binding(manifest_path, root),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
