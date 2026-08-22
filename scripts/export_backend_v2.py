#!/usr/bin/env python3
"""Extend the immutable O011 Unit 1 backend with deterministic Unit 2 records."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
from pathlib import Path


SCHEMA = "o011-modular-backend"
VERSION = 1
WORKFLOW = "o011-export-backend-v2"
UNIT01_BASELINE_SHA256 = "7b7cd4e77932d89920c921e886f3a689dcba4d0335325ec93593371552469533"
ENTITY_TYPES = {
    "program", "course", "resource", "edition", "unit", "concept", "segment",
    "term", "asset", "relation", "rights", "qa_event", "artifact", "correction",
}
COMMON = (
    "schema", "schema_version", "id", "entity_type", "source_local_id", "parent_id",
    "order", "path", "resource_id", "edition_id", "source_locator", "source_sha256",
    "target_sha256", "language", "locale", "translation_state", "rights_component_id",
    "status", "timestamp", "workflow", "supersedes",
)
LECTURE_MARKER = re.compile(r"(?m)^\s*\\zwischenueberschrift\s*\{")
EXERCISE_MARKER = re.compile(r"(?m)^\s*\\(?:inputaufgabegibtloesung|inputaufgabe)\b")
WINDOWS_ABSOLUTE = re.compile(r"(?i)(?<![a-z0-9+.-])[a-z]:[\\/]")
PUBLIC_SAFETY_MARKERS = (
    "\\users\\", "/users/", "\\appdata\\", "/home/", "github_pat_", "ghp_",
    "gho_", "ghu_", "ghs_", "ghr_", "glpat-", "sk-proj-", "xoxb-",
    "bearer ", "access_token", "api_key", "zenodo token",
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def repository_path(path: Path, root: Path) -> str:
    return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")


def base(record_id: str, entity_type: str, timestamp: str, **values: object) -> dict[str, object]:
    record: dict[str, object] = {
        "schema": SCHEMA,
        "schema_version": VERSION,
        "id": record_id,
        "entity_type": entity_type,
        "status": "active",
        "timestamp": timestamp,
        "workflow": WORKFLOW,
        "supersedes": None,
    }
    record.update(values)
    return record


def slices(text: str, marker: re.Pattern[str]) -> list[str]:
    matches = list(marker.finditer(text))
    return [
        text[match.start() : matches[index + 1].start() if index + 1 < len(matches) else len(text)]
        for index, match in enumerate(matches)
    ]


def assert_public_safe(label: str, data: bytes) -> None:
    text = data.decode("utf-8")
    folded = text.casefold()
    if WINDOWS_ABSOLUTE.search(text):
        raise RuntimeError(f"absolute Windows path leaked into {label}")
    found = [marker for marker in PUBLIC_SAFETY_MARKERS if marker in folded]
    if found:
        raise RuntimeError(f"private path or credential marker leaked into {label}: {found}")


def validate(records: list[dict[str, object]]) -> None:
    identifiers: set[str] = set()
    for record in records:
        missing = [
            field for field in (
                "schema", "schema_version", "id", "entity_type", "status",
                "timestamp", "workflow", "supersedes",
            ) if field not in record
        ]
        if missing:
            raise RuntimeError(f"missing common fields in {record.get('id')}: {missing}")
        if record["schema"] != SCHEMA or record["schema_version"] != VERSION:
            raise RuntimeError(f"schema mismatch in {record.get('id')}")
        if record["entity_type"] not in ENTITY_TYPES:
            raise RuntimeError(f"unknown entity type in {record.get('id')}")
        identifier = str(record["id"])
        if not re.fullmatch(r"o011-[a-z0-9][a-z0-9._-]*", identifier):
            raise RuntimeError(f"invalid stable ID: {identifier}")
        if identifier in identifiers:
            raise RuntimeError(f"duplicate stable ID: {identifier}")
        identifiers.add(identifier)
        for field in ("source_sha256", "target_sha256", "evidence_sha256"):
            value = record.get(field)
            if value is not None and not re.fullmatch(r"[0-9a-f]{64}", str(value)):
                raise RuntimeError(f"invalid {field} in {identifier}")
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
        if record["entity_type"] == "relation":
            for field in ("from_id", "to_id"):
                if record.get(field) not in identifiers:
                    raise RuntimeError(f"unresolved {field} in {record['id']}")
        for field in ("path", "receipt_path", "build_receipt_path"):
            value = record.get(field)
            if value is not None and (
                str(value).startswith(("/", "\\")) or WINDOWS_ABSOLUTE.search(str(value))
            ):
                raise RuntimeError(f"absolute {field} in {record['id']}")


def load_json(raw: dict[str, bytes], key: str) -> dict[str, object]:
    return json.loads(raw[key].decode("utf-8-sig"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--timestamp", required=True)
    parser.add_argument("--translation-state", default="structurally_verified")
    args = parser.parse_args()
    root = args.root.resolve()
    timestamp = args.timestamp
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", timestamp):
        raise RuntimeError("timestamp must be explicit YYYY-MM-DDTHH:MM:SSZ")

    paths: dict[str, Path] = {
        "schema": root / "backend/schema/o011-record-v1.schema.json",
        "unit01_frozen_records": root / "backend/unit01_records_frozen.jsonl",
        "revisions": root / "authority/brenner_selected_root_revisions.csv",
        "media_rights": root / "authority/brenner_media_rights_manifest.csv",
        "unit02_authority": root / "qa/unit-02/AUTHORITY_PREFLIGHT.json",
        "unit02_solution_closure": root / "qa/unit-02/solution_closure.json",
        "adverse": root / "00_control/ADVERSE_LEDGER.csv",
        "u02_lecture_corrections": root / "00_control/LECTURE02_PROTECTED_CORRECTIONS.json",
        "u02_worksheet_corrections": root / "00_control/WORKSHEET02_PROTECTED_CORRECTIONS.json",
        "u02_solution01_corrections": root / "00_control/SOLUTION01_PROTECTED_CORRECTIONS.json",
        "u02_solution02_corrections": root / "00_control/SOLUTION02_PROTECTED_CORRECTIONS.json",
        "u02_solution07_corrections": root / "00_control/SOLUTION07_PROTECTED_CORRECTIONS.json",
        "u02_solution13_corrections": root / "00_control/SOLUTION13_PROTECTED_CORRECTIONS.json",
        "u02_lecture_source": root / "authority/expanded/lecture02_source.de.tex",
        "u02_lecture_target": root / "source/units/unit-02/lecture02.id.tex",
        "u02_lecture_receipt": root / "qa/unit-02/lecture_translation.json",
        "u02_worksheet_source": root / "authority/expanded/worksheet02_source.de.tex",
        "u02_worksheet_target": root / "source/units/unit-02/worksheet02.id.tex",
        "u02_worksheet_receipt": root / "qa/unit-02/worksheet_translation.json",
        "u02_media_integral": root / "authority/media/Integral apl rot obsah1.svg",
        "u02_media_hyperboloid": root / "authority/media/Hyperboloid1.png",
        "u02_reader_pdf": root / "output/pdf/geometri-diferensial-manifold-mulus-hingga-unit-02-id.pdf",
        "u02_build_receipt": root / "qa/unit-02/build.json",
        "u02_media_receipt": root / "qa/unit-02_media.json",
        "u02_structural_receipt": root / "qa/unit-02/pdf_structural_qa.json",
        "u02_visual_receipt": root / "qa/unit-02/visual_qa.json",
        "u02_math_audit": root / "qa/unit-02/POST_REPAIR_MATH_AUDIT.md",
    }
    solution_indices = (1, 2, 7, 12, 13)
    for index in solution_indices:
        paths[f"u02_solution{index:02d}_source"] = root / f"authority/expanded/worksheet02_exercise{index:02d}_solution_source.de.tex"
        paths[f"u02_solution{index:02d}_target"] = root / f"source/units/unit-02/worksheet02_exercise{index:02d}_solution.id.tex"
        paths[f"u02_solution{index:02d}_receipt"] = root / f"qa/unit-02/worksheet02_exercise{index:02d}_solution_translation.json"
    raw = {name: path.read_bytes() for name, path in paths.items()}

    baseline_bytes = raw["unit01_frozen_records"]
    if digest(baseline_bytes) != UNIT01_BASELINE_SHA256:
        raise RuntimeError("Unit 1 frozen record baseline hash changed")
    baseline_records = [json.loads(line) for line in baseline_bytes.decode("utf-8").splitlines()]
    if len(baseline_records) != 174:
        raise RuntimeError("Unit 1 frozen record baseline must contain exactly 174 rows")
    validate(baseline_records)
    baseline_ids = {record["id"] for record in baseline_records}

    authority = load_json(raw, "unit02_authority")
    solution_closure = load_json(raw, "unit02_solution_closure")
    if authority.get("status") != "pass":
        raise RuntimeError("Unit 2 authority preflight is not a pass")
    if authority.get("structure", {}).get("worksheet_exercise_count") != 19:
        raise RuntimeError("Unit 2 authority preflight does not bind 19 exercises")
    if tuple(authority.get("solutions", {}).get("supplied_solution_indices", [])) != solution_indices:
        raise RuntimeError("Unit 2 authority preflight solution closure changed")
    if tuple(solution_closure.get("supplied_solution_indices", [])) != solution_indices:
        raise RuntimeError("Unit 2 solution manifest closure changed")

    lecture_source = raw["u02_lecture_source"].decode("utf-8")
    lecture_target = raw["u02_lecture_target"].decode("utf-8")
    worksheet_source = raw["u02_worksheet_source"].decode("utf-8")
    worksheet_target = raw["u02_worksheet_target"].decode("utf-8")
    lecture_source_parts = slices(lecture_source, LECTURE_MARKER)
    lecture_target_parts = slices(lecture_target, LECTURE_MARKER)
    worksheet_source_parts = slices(worksheet_source, EXERCISE_MARKER)
    worksheet_target_parts = slices(worksheet_target, EXERCISE_MARKER)
    if len(lecture_source_parts) != 3 or len(lecture_target_parts) != 3:
        raise RuntimeError("Unit 2 Lecture must contain exactly three section markers")
    if len(worksheet_source_parts) != 19 or len(worksheet_target_parts) != 19:
        raise RuntimeError("Unit 2 Worksheet must contain exactly nineteen exercise markers")

    translation_specs: list[dict[str, object]] = [
        {
            "name": "lecture",
            "unit_id": "o011-brenner-u02-l02",
            "source_key": "u02_lecture_source",
            "target_key": "u02_lecture_target",
            "receipt_key": "u02_lecture_receipt",
            "artifact_id": "o011-artifact-u02-l02-tex",
            "qa_id": "o011-qa-unit02-lecture-translation",
        },
        {
            "name": "worksheet",
            "unit_id": "o011-brenner-u02-w02",
            "source_key": "u02_worksheet_source",
            "target_key": "u02_worksheet_target",
            "receipt_key": "u02_worksheet_receipt",
            "artifact_id": "o011-artifact-u02-w02-tex",
            "qa_id": "o011-qa-unit02-worksheet-translation",
        },
    ]
    for index in solution_indices:
        translation_specs.append({
            "name": f"solution{index:02d}",
            "unit_id": f"o011-brenner-u02-w02-e{index:03d}-solution",
            "source_key": f"u02_solution{index:02d}_source",
            "target_key": f"u02_solution{index:02d}_target",
            "receipt_key": f"u02_solution{index:02d}_receipt",
            "artifact_id": f"o011-artifact-u02-w02-e{index:03d}-solution-tex",
            "qa_id": f"o011-qa-unit02-solution{index:02d}-translation",
        })
    receipts: dict[str, dict[str, object]] = {}
    for spec in translation_specs:
        receipt_key = str(spec["receipt_key"])
        receipt = load_json(raw, receipt_key)
        receipts[str(spec["name"])] = receipt
        source_key = str(spec["source_key"])
        target_key = str(spec["target_key"])
        if receipt.get("status") != "pass" or receipt.get("failures"):
            raise RuntimeError(f"Unit 2 {spec['name']} receipt is not a clean pass")
        if receipt.get("source_sha256") != digest(raw[source_key]) or receipt.get("source_bytes") != len(raw[source_key]):
            raise RuntimeError(f"Unit 2 {spec['name']} receipt is stale against its source")
        if receipt.get("target_sha256") != digest(raw[target_key]) or receipt.get("target_bytes") != len(raw[target_key]):
            raise RuntimeError(f"Unit 2 {spec['name']} receipt is stale against its target")

    fragment_correction_ids: set[str] = set()
    for receipt in receipts.values():
        for declaration in receipt.get("declared_corrections") or []:
            if isinstance(declaration, str):
                fragment_correction_ids.update(
                    correction_id for correction_id in declaration.split("+") if correction_id
                )
    adverse_rows = list(csv.DictReader(io.StringIO(raw["adverse"].decode("utf-8-sig"))))
    for row_number, row in enumerate(adverse_rows, 2):
        if None in row or any(row.get(field) is None for field in (
            "id", "severity", "surface", "status", "description", "disposition",
        )):
            raise RuntimeError(f"malformed adverse-ledger CSV row {row_number}")
    adverse_by_id = {row["id"]: row for row in adverse_rows}
    # The Unit 1 record objects are immutable. Any ledger record not already in
    # that baseline belongs to the current Unit 2/checkpoint extension, including
    # reader-level fixes that are not declared by an individual TeX receipt.
    expected_correction_ids = {
        row["id"] for row in adverse_rows if row["id"].lower() not in baseline_ids
    }
    missing_corrections = fragment_correction_ids - expected_correction_ids
    if missing_corrections:
        raise RuntimeError(
            f"Unit 2 receipt-declared corrections missing from adverse ledger: {sorted(missing_corrections)}"
        )
    if "O011-CORR-0015" not in expected_correction_ids:
        raise RuntimeError("Unit 2 reader-numbering correction is missing from the adverse ledger")
    correction_manifest_keys = (
        "u02_lecture_corrections", "u02_worksheet_corrections",
        "u02_solution01_corrections", "u02_solution02_corrections",
        "u02_solution07_corrections", "u02_solution13_corrections",
    )
    protected_corrections = [
        (
            repository_path(paths[key], root),
            digest(raw[key]),
            load_json(raw, key),
        )
        for key in correction_manifest_keys
    ]

    reader_pdf_sha256 = digest(raw["u02_reader_pdf"])
    reader_pdf_bytes = len(raw["u02_reader_pdf"])
    build_receipt = load_json(raw, "u02_build_receipt")
    media_receipt = load_json(raw, "u02_media_receipt")
    structural_receipt = load_json(raw, "u02_structural_receipt")
    visual_receipt = load_json(raw, "u02_visual_receipt")
    math_audit_text = raw["u02_math_audit"].decode("utf-8")
    build_output = build_receipt.get("output", {})
    if (
        build_output.get("path") != repository_path(paths["u02_reader_pdf"], root)
        or build_output.get("bytes") != reader_pdf_bytes
        or build_output.get("sha256") != reader_pdf_sha256
        or build_receipt.get("deterministic_clean_cycles") is not True
        or len(build_receipt.get("cycles", [])) != 2
        or any(cycle.get("sha256") != reader_pdf_sha256 for cycle in build_receipt.get("cycles", []))
    ):
        raise RuntimeError("Unit 2 cumulative PDF build receipt is stale or non-reproducible")
    if (
        media_receipt.get("manifest_sha256") != digest(raw["media_rights"])
        or media_receipt.get("source_count") != 2
        or media_receipt.get("derivative_count") != 1
    ):
        raise RuntimeError("Unit 2 media receipt is stale or incomplete")
    media_receipt_by_filename = {
        item["filename"]: item for item in media_receipt.get("media", [])
    }
    for filename, binary_key in (
        ("Integral apl rot obsah1.svg", "u02_media_integral"),
        ("Hyperboloid1.png", "u02_media_hyperboloid"),
    ):
        item = media_receipt_by_filename.get(filename, {})
        if (
            item.get("canonical_bytes") != len(raw[binary_key])
            or item.get("canonical_sha256") != digest(raw[binary_key])
        ):
            raise RuntimeError(f"Unit 2 media receipt is stale for {filename}")
    structural_pdf = structural_receipt.get("pdf", {})
    if (
        structural_receipt.get("passed") is not True
        or structural_receipt.get("blockers")
        or structural_pdf.get("bytes") != reader_pdf_bytes
        or structural_pdf.get("sha256") != reader_pdf_sha256
        or structural_pdf.get("catalog_language") != "id-ID"
    ):
        raise RuntimeError("Unit 2 cumulative PDF structural receipt is not a clean pass")
    visual_pdf = visual_receipt.get("pdf", {})
    if (
        visual_receipt.get("verdict") != "PASS"
        or visual_pdf.get("bytes") != reader_pdf_bytes
        or visual_pdf.get("sha256") != reader_pdf_sha256
        or visual_receipt.get("render", {}).get("page_count") != visual_pdf.get("pages")
    ):
        raise RuntimeError("Unit 2 cumulative PDF visual receipt is stale or non-passing")
    if "**PASS — no remaining P1, P2, or P3 finding" not in math_audit_text:
        raise RuntimeError("Unit 2 final independent mathematical audit is not a pass")
    audit_bound_hashes = [
        reader_pdf_sha256,
        *(digest(raw[str(spec["target_key"])]) for spec in translation_specs),
    ]
    if any(bound_hash not in math_audit_text for bound_hash in audit_bound_hashes):
        raise RuntimeError("Unit 2 final mathematical audit does not bind every current target")

    revision_rows = list(csv.DictReader(io.StringIO(raw["revisions"].decode("utf-8-sig"))))
    lecture_revision = next(row for row in revision_rows if row["title"].endswith("/Vorlesung 2"))
    worksheet_revision = next(row for row in revision_rows if row["title"].endswith("/Arbeitsblatt 2"))
    supplied_by_index = {
        int(row["exercise_index"]): row
        for row in solution_closure["solutions"] if row.get("exists")
    }

    resource_id = "o011-resource-brenner-dg2023"
    edition_id = "o011-edition-brenner-current-20260821"
    text_rights_id = "o011-rights-brenner-text"
    unit_id = "o011-brenner-u02"
    lecture_id = unit_id + "-l02"
    worksheet_id = unit_id + "-w02"
    added: list[dict[str, object]] = []
    added.extend([
        base(
            unit_id, "unit", timestamp, parent_id="o011-course-d50", order=2,
            path="source/units/unit-02", resource_id=resource_id, edition_id=edition_id,
            source_local_id="Vorlesung 2 + Arbeitsblatt 2", language="Indonesian",
            locale="id-ID", translation_state=args.translation_state,
            rights_component_id=text_rights_id, unit_kind="lecture_worksheet_pair",
            title="Permukaan Putar, Medan Normal, dan Pemetaan Gauss",
            authority_receipt="qa/unit-02/AUTHORITY_PREFLIGHT.json",
            authority_receipt_sha256=digest(raw["unit02_authority"]),
        ),
        base(
            lecture_id, "unit", timestamp, parent_id=unit_id, order=1,
            path="source/units/unit-02/lecture02.id.tex", resource_id=resource_id,
            edition_id=edition_id,
            source_local_id=f"pageid:{lecture_revision['pageid']}/revid:{lecture_revision['revid']}",
            source_locator=lecture_revision["title"], source_sha256=digest(raw["u02_lecture_source"]),
            target_sha256=digest(raw["u02_lecture_target"]), language="Indonesian",
            locale="id-ID", translation_state=args.translation_state,
            rights_component_id=text_rights_id, unit_kind="lecture",
        ),
        base(
            worksheet_id, "unit", timestamp, parent_id=unit_id, order=2,
            path="source/units/unit-02/worksheet02.id.tex", resource_id=resource_id,
            edition_id=edition_id,
            source_local_id=f"pageid:{worksheet_revision['pageid']}/revid:{worksheet_revision['revid']}",
            source_locator=worksheet_revision["title"], source_sha256=digest(raw["u02_worksheet_source"]),
            target_sha256=digest(raw["u02_worksheet_target"]), language="Indonesian",
            locale="id-ID", translation_state=args.translation_state,
            rights_component_id=text_rights_id, unit_kind="worksheet",
        ),
    ])

    for index, (source_part, target_part) in enumerate(zip(lecture_source_parts, lecture_target_parts), 1):
        added.append(base(
            f"{lecture_id}-s{index:02d}", "segment", timestamp, parent_id=lecture_id,
            order=index, path=f"source/units/unit-02/lecture02.id.tex#section-{index}",
            resource_id=resource_id, edition_id=edition_id,
            source_local_id=f"lecture02:section:{index}",
            source_locator=f"{lecture_revision['title']}#section-{index}",
            source_sha256=digest(source_part.encode("utf-8")),
            target_sha256=digest(target_part.encode("utf-8")), language="Indonesian",
            locale="id-ID", translation_state=args.translation_state,
            rights_component_id=text_rights_id, segment_kind="lecture_section",
        ))

    concepts = [
        ("surface-of-revolution", "Rotationsfläche", "permukaan putar"),
        ("unit-normal-field", "Einheitsnormalenfeld", "medan normal satuan"),
        ("orientation", "Orientierung", "orientasi"),
        ("gauss-map", "Gauß-Abbildung", "pemetaan Gauss"),
    ]
    for slug, source_label, target_label in concepts:
        added.append(base(
            f"o011-concept-{slug}", "concept", timestamp, parent_id="o011-course-d50",
            source_local_id=source_label, language=None, locale=None,
            labels={"de": source_label, "id-ID": target_label},
        ))
    section_concepts = {
        1: ("surface-of-revolution",),
        2: ("unit-normal-field", "orientation"),
        3: ("gauss-map",),
    }
    for section, slugs in section_concepts.items():
        for order, slug in enumerate(slugs, 1):
            added.append(base(
                f"o011-rel-u02-l02-s{section:02d}-covers-{slug}", "relation", timestamp,
                order=order, relation_type="covers", from_id=f"{lecture_id}-s{section:02d}",
                to_id=f"o011-concept-{slug}",
                evidence="Direct section content in the frozen Lecture 2 source",
            ))

    previous_exercise: str | None = None
    for index, (source_part, target_part) in enumerate(zip(worksheet_source_parts, worksheet_target_parts), 1):
        exercise_id = f"{worksheet_id}-e{index:03d}"
        added.append(base(
            exercise_id, "unit", timestamp, parent_id=worksheet_id, order=index,
            path=f"source/units/unit-02/worksheet02.id.tex#exercise-{index}",
            resource_id=resource_id, edition_id=edition_id,
            source_local_id=f"worksheet02:exercise:{index}",
            source_locator=f"{worksheet_revision['title']}#exercise-{index}",
            source_sha256=digest(source_part.encode("utf-8")),
            target_sha256=digest(target_part.encode("utf-8")), language="Indonesian",
            locale="id-ID", translation_state=args.translation_state,
            rights_component_id=text_rights_id, unit_kind="exercise",
            has_authority_solution=index in solution_indices,
            source_display_id=f"2.{index}",
        ))
        if previous_exercise:
            added.append(base(
                f"o011-rel-u02-w02-e{index - 1:03d}-precedes-e{index:03d}",
                "relation", timestamp, relation_type="precedes",
                from_id=previous_exercise, to_id=exercise_id,
            ))
        previous_exercise = exercise_id

    for index in solution_indices:
        authority_row = supplied_by_index[index]
        solution_id = f"{worksheet_id}-e{index:03d}-solution"
        source_key = f"u02_solution{index:02d}_source"
        target_key = f"u02_solution{index:02d}_target"
        added.append(base(
            solution_id, "unit", timestamp, parent_id=f"{worksheet_id}-e{index:03d}",
            order=1, path=f"source/units/unit-02/worksheet02_exercise{index:02d}_solution.id.tex",
            resource_id=resource_id, edition_id=edition_id,
            source_local_id=f"pageid:{authority_row['pageid']}/revid:{authority_row['revid']}",
            source_locator=authority_row["solution_title"], source_sha256=digest(raw[source_key]),
            target_sha256=digest(raw[target_key]), language="Indonesian", locale="id-ID",
            translation_state=args.translation_state, rights_component_id=text_rights_id,
            unit_kind="solution", source_display_id=f"2.{index}",
            authority_wikitext_sha256=authority_row["source_utf8_sha256"],
        ))
        added.append(base(
            f"o011-rel-u02-w02-e{index:03d}-solution-solves-e{index:03d}",
            "relation", timestamp, relation_type="solves", from_id=solution_id,
            to_id=f"{worksheet_id}-e{index:03d}",
        ))

    rights_rows = list(csv.DictReader(io.StringIO(raw["media_rights"].decode("utf-8-sig"))))
    rights_by_filename = {row["title"].removeprefix("File:"): row for row in rights_rows}
    media_specs = [
        (1, "Integral apl rot obsah1.svg", "u02_media_integral", "integral-apl-rot-obsah1-svg"),
        (2, "Hyperboloid1.png", "u02_media_hyperboloid", "hyperboloid1-png"),
    ]
    asset_ids: list[str] = []
    media_rights_ids: list[str] = []
    for order, filename, binary_key, slug in media_specs:
        row = rights_by_filename[filename]
        binary = raw[binary_key]
        if len(binary) != int(row["bytes"]):
            raise RuntimeError(f"Unit 2 media byte mismatch for {filename}")
        rights_id = f"o011-rights-media-u02-{order:02d}"
        asset_id = f"o011-asset-file-{slug}"
        rights_id_list_value = row["attribution_required"].lower() == "true"
        added.append(base(
            rights_id, "rights", timestamp, source_local_id=f"File:{filename}",
            license=row["license"], license_url=row["license_url"] or None,
            attribution=row["artist_html"], credit=row["credit_html"],
            component_scope=f"File:{filename}", attribution_required=rights_id_list_value,
        ))
        added.append(base(
            asset_id, "asset", timestamp, parent_id=unit_id, order=order,
            path=f"authority/media/{filename}", source_local_id=f"File:{filename}",
            source_locator=row["description_url"], source_sha256=digest(binary),
            rights_component_id=rights_id, mime=row["mime"], expected_bytes=int(row["bytes"]),
            commons_sha1=row["commons_sha1_hex"], binary_present=True,
        ))
        asset_ids.append(asset_id)
        media_rights_ids.append(rights_id)
        added.append(base(
            f"o011-rel-u02-l02-uses-{slug}", "relation", timestamp,
            relation_type="uses", from_id=lecture_id, to_id=asset_id,
        ))

    pdf_artifact_id = "o011-artifact-through-unit02-pdf"
    unit01_media_rights_ids = [f"o011-rights-media-{index:02d}" for index in range(1, 5)]
    cumulative_rights_ids = [text_rights_id, *unit01_media_rights_ids, *media_rights_ids]
    if any(rights_id not in baseline_ids and rights_id not in media_rights_ids for rights_id in cumulative_rights_ids):
        raise RuntimeError("cumulative reader references a missing component-rights record")
    added.append(base(
        pdf_artifact_id, "artifact", timestamp, parent_id=unit_id,
        path=repository_path(paths["u02_reader_pdf"], root),
        target_sha256=reader_pdf_sha256, language="Indonesian", locale="id-ID",
        translation_state="visually_checked", artifact_kind="cumulative_reader_pdf",
        media_type="application/pdf", bytes=reader_pdf_bytes,
        component_rights_ids=cumulative_rights_ids,
        build_receipt_path=repository_path(paths["u02_build_receipt"], root),
        build_receipt_sha256=digest(raw["u02_build_receipt"]),
        deterministic_clean_cycles=True, clean_cycle_count=2,
        coverage_unit_ids=["o011-brenner-u01", unit_id],
    ))
    added.extend([
        base(
            "o011-qa-unit02-media-closure", "qa_event", timestamp,
            parent_id=unit_id, target_id=unit_id,
            receipt_path=repository_path(paths["u02_media_receipt"], root),
            evidence_sha256=digest(raw["u02_media_receipt"]),
            source_sha256=digest(raw["media_rights"]), language=None, locale=None,
            translation_state="structurally_verified",
            qa_kind="media_rights_and_binary_closure", result="pass",
            source_count=media_receipt["source_count"],
            derivative_count=media_receipt["derivative_count"],
            asset_ids=asset_ids, component_rights_ids=media_rights_ids,
        ),
        base(
            "o011-qa-through-unit02-pdf-reproducibility", "qa_event", timestamp,
            parent_id=unit_id, target_id=pdf_artifact_id, artifact_id=pdf_artifact_id,
            receipt_path=repository_path(paths["u02_build_receipt"], root),
            evidence_sha256=digest(raw["u02_build_receipt"]),
            target_sha256=reader_pdf_sha256, language="Indonesian", locale="id-ID",
            translation_state="built", qa_kind="reproducible_pdf_build", result="pass",
            engine=build_receipt["engine"], deterministic_clean_cycles=True,
            clean_cycle_count=2, pass_count_per_cycle=3, artifact_bytes=reader_pdf_bytes,
        ),
        base(
            "o011-qa-through-unit02-pdf-structural", "qa_event", timestamp,
            parent_id=unit_id, target_id=pdf_artifact_id, artifact_id=pdf_artifact_id,
            receipt_path=repository_path(paths["u02_structural_receipt"], root),
            evidence_sha256=digest(raw["u02_structural_receipt"]),
            target_sha256=reader_pdf_sha256, language="Indonesian", locale="id-ID",
            translation_state="visually_checked",
            qa_kind="pdf_structure_accessibility_and_safety",
            result="admitted_limitation", page_count=structural_pdf["pages"],
            page_size_points=structural_pdf["media_box_points"],
            catalog_language=structural_pdf["catalog_language"],
            tagged=structural_pdf["tagged"], limitations=structural_receipt["limitations"],
            accessibility={
                "unique_fonts": structural_receipt["accessibility"]["unique_fonts"],
                "fonts_with_tounicode": structural_receipt["accessibility"]["fonts_with_tounicode"],
                "pages_with_extractable_text": structural_receipt["accessibility"]["pdfplumber_pages_with_extractable_text"],
                "empty_text_pages": structural_receipt["accessibility"]["pdfplumber_empty_text_pages"],
            },
            active_content=structural_receipt["active_content"],
            external_uri_count=structural_receipt["links"]["external_uri_count"],
            internal_link_count=structural_receipt["links"]["internal_link_count"],
            exact_required_uri_inventory=(
                not structural_receipt["links"]["missing_uri_counts"]
                and not structural_receipt["links"]["extra_uri_counts"]
            ),
        ),
        base(
            "o011-qa-through-unit02-pdf-visual", "qa_event", timestamp,
            parent_id=unit_id, target_id=pdf_artifact_id, artifact_id=pdf_artifact_id,
            receipt_path=repository_path(paths["u02_visual_receipt"], root),
            evidence_sha256=digest(raw["u02_visual_receipt"]),
            target_sha256=reader_pdf_sha256, language="Indonesian", locale="id-ID",
            translation_state="visually_checked", qa_kind="pdf_visual_inspection",
            result="pass", page_count=visual_pdf["pages"], all_pages_inspected=True,
            page_dimensions_pixels=visual_receipt["render"]["pixel_dimensions_each"],
            render_inventory_sha256=visual_receipt["render"]["inventory_sha256"],
            inspection=visual_receipt["inspection"],
        ),
    ])
    added.append(base(
        "o011-rel-artifact-through-unit02-pdf-represents-u02-checkpoint",
        "relation", timestamp, relation_type="represents", from_id=pdf_artifact_id,
        to_id=unit_id,
    ))
    for qa_id in (
        "o011-qa-through-unit02-pdf-reproducibility",
        "o011-qa-through-unit02-pdf-structural",
        "o011-qa-through-unit02-pdf-visual",
    ):
        added.append(base(
            f"o011-rel-{qa_id.removeprefix('o011-')}-verifies-through-unit02-pdf",
            "relation", timestamp, relation_type="verifies", from_id=qa_id,
            to_id=pdf_artifact_id,
        ))
    added.append(base(
        "o011-rel-qa-unit02-media-closure-verifies-u02", "relation", timestamp,
        relation_type="verifies", from_id="o011-qa-unit02-media-closure", to_id=unit_id,
    ))
    added.append(base(
        "o011-qa-unit02-final-math-audit", "qa_event", timestamp,
        parent_id=unit_id, target_id=unit_id, artifact_id=pdf_artifact_id,
        receipt_path=repository_path(paths["u02_math_audit"], root),
        evidence_sha256=digest(raw["u02_math_audit"]), target_sha256=reader_pdf_sha256,
        language="Indonesian", locale="id-ID", translation_state="visually_checked",
        qa_kind="independent_post_repair_mathematical_audit", result="pass",
        scope="seven Unit 2 reader sources, correction closure, and cumulative PDF",
        audited_target_hashes={
            str(spec["name"]): digest(raw[str(spec["target_key"])])
            for spec in translation_specs
        },
        audited_pdf_sha256=reader_pdf_sha256,
        remaining_p1_p2_p3_findings=0,
    ))
    added.append(base(
        "o011-rel-qa-unit02-final-math-audit-verifies-u02", "relation", timestamp,
        relation_type="verifies", from_id="o011-qa-unit02-final-math-audit", to_id=unit_id,
    ))

    for spec in translation_specs:
        name = str(spec["name"])
        source_key = str(spec["source_key"])
        target_key = str(spec["target_key"])
        receipt_key = str(spec["receipt_key"])
        artifact_id = str(spec["artifact_id"])
        target_id = str(spec["unit_id"])
        receipt = receipts[name]
        added.append(base(
            artifact_id, "artifact", timestamp, parent_id=target_id,
            path=repository_path(paths[target_key], root), source_sha256=digest(raw[source_key]),
            target_sha256=digest(raw[target_key]), language="Indonesian", locale="id-ID",
            translation_state=args.translation_state, rights_component_id=text_rights_id,
            artifact_kind="translated_tex_fragment", media_type="application/x-tex",
            bytes=len(raw[target_key]), component_rights_ids=[text_rights_id],
        ))
        qa_values: dict[str, object] = {
            "parent_id": unit_id,
            "target_id": target_id,
            "artifact_id": artifact_id,
            "receipt_path": repository_path(paths[receipt_key], root),
            "evidence_sha256": digest(raw[receipt_key]),
            "source_sha256": digest(raw[source_key]),
            "target_sha256": digest(raw[target_key]),
            "language": "Indonesian",
            "locale": "id-ID",
            "translation_state": args.translation_state,
            "qa_kind": "translation_structure",
            "result": "pass",
            "checks": receipt["checks"],
            "counts": receipt["counts"],
            "declared_corrections": sorted({
                value for value in (receipt.get("declared_corrections") or [])
                if isinstance(value, str) and value
            }),
        }
        added.append(base(str(spec["qa_id"]), "qa_event", timestamp, **qa_values))
        added.append(base(
            f"o011-rel-{artifact_id.removeprefix('o011-')}-represents-{target_id.removeprefix('o011-')}",
            "relation", timestamp, relation_type="represents", from_id=artifact_id,
            to_id=target_id,
        ))
        added.append(base(
            f"o011-rel-{str(spec['qa_id']).removeprefix('o011-')}-verifies-{artifact_id.removeprefix('o011-')}",
            "relation", timestamp, relation_type="verifies", from_id=str(spec["qa_id"]),
            to_id=artifact_id,
        ))

    authority_qa_id = "o011-qa-unit02-authority-preflight"
    added.append(base(
        authority_qa_id, "qa_event", timestamp, parent_id=unit_id, target_id=unit_id,
        receipt_path=repository_path(paths["unit02_authority"], root),
        evidence_sha256=digest(raw["unit02_authority"]), language=None, locale=None,
        translation_state="source_frozen", qa_kind="authority_source_media_solution_closure",
        result="pass", lecture_section_count=3, worksheet_exercise_count=19,
        supplied_solution_indices=list(solution_indices), asset_ids=asset_ids,
        component_rights_ids=media_rights_ids,
    ))
    added.append(base(
        "o011-rel-qa-unit02-authority-preflight-verifies-u02", "relation", timestamp,
        relation_type="verifies", from_id=authority_qa_id, to_id=unit_id,
    ))
    added.append(base(
        "o011-rel-u01-precedes-u02", "relation", timestamp, relation_type="precedes",
        from_id="o011-brenner-u01", to_id=unit_id,
    ))

    for correction_name in sorted(expected_correction_ids):
        row = adverse_by_id[correction_name]
        protected_deltas: list[dict[str, object]] = []
        for manifest_path, manifest_sha256, document in protected_corrections:
            for delta in document.get("allowed_deltas", []):
                correction_ids = str(delta.get("correction_id", "")).split("+")
                if correction_name in correction_ids:
                    protected_deltas.append({
                        "manifest_path": manifest_path,
                        "manifest_sha256": manifest_sha256,
                        **delta,
                    })
        added.append(base(
            correction_name.lower(), "correction", timestamp,
            source_local_id=row["surface"], severity=row["severity"],
            correction_status=row["status"], description=row["description"],
            disposition=row["disposition"],
            upstream_report_disposition="deferred_until_full_corpus",
            ledger_path=repository_path(paths["adverse"], root),
            ledger_sha256=digest(raw["adverse"]),
            protected_deltas=protected_deltas,
        ))

    for child in list(added):
        parent_id = child.get("parent_id")
        if parent_id and child["entity_type"] not in {"relation", "rights", "correction"}:
            child_slug = str(child["id"]).removeprefix("o011-")
            added.append(base(
                f"o011-rel-contains-{child_slug}", "relation", timestamp,
                relation_type="contains", from_id=parent_id, to_id=child["id"],
            ))

    if any(record["id"] in baseline_ids for record in added):
        collisions = sorted(record["id"] for record in added if record["id"] in baseline_ids)
        raise RuntimeError(f"Unit 2 stable IDs collide with Unit 1: {collisions}")
    records = [*baseline_records, *added]
    records.sort(key=lambda record: str(record["id"]))
    validate(records)

    extracted_unit01 = [record for record in records if record["id"] in baseline_ids]
    extracted_unit01.sort(key=lambda record: str(record["id"]))
    extracted_unit01_bytes = "".join(canonical_json(record) + "\n" for record in extracted_unit01).encode("utf-8")
    if extracted_unit01_bytes != baseline_bytes:
        raise RuntimeError("Unit 1 records changed during Unit 2 extension")

    output = root / "backend/records.jsonl"
    jsonl = "".join(canonical_json(record) + "\n" for record in records).encode("utf-8")
    assert_public_safe("records.jsonl", jsonl)
    output.write_bytes(jsonl)

    csv_buffer = io.StringIO(newline="")
    writer = csv.DictWriter(csv_buffer, fieldnames=COMMON, lineterminator="\n")
    writer.writeheader()
    for record in records:
        writer.writerow({field: record.get(field) for field in COMMON})
    csv_bytes = csv_buffer.getvalue().encode("utf-8")
    assert_public_safe("records.csv", csv_bytes)
    (root / "backend/records.csv").write_bytes(csv_bytes)

    unit02_counts = {
        name: sum(record["entity_type"] == name for record in added)
        for name in sorted(ENTITY_TYPES)
    }
    generated = {
        "schema_version": 2,
        "generator": "scripts/export_backend_v2.py",
        "generator_sha256": digest(Path(__file__).read_bytes()),
        "timestamp": timestamp,
        "record_count": len(records),
        "entity_counts": {
            name: sum(record["entity_type"] == name for record in records)
            for name in sorted(ENTITY_TYPES)
        },
        "unit01_preservation": {
            "baseline_path": repository_path(paths["unit01_frozen_records"], root),
            "baseline_bytes": len(baseline_bytes),
            "baseline_sha256": digest(baseline_bytes),
            "baseline_record_count": len(baseline_records),
            "extracted_record_count": len(extracted_unit01),
            "extracted_sha256": digest(extracted_unit01_bytes),
            "byte_identical": True,
        },
        "unit02_extension": {
            "record_count": len(added),
            "entity_counts": unit02_counts,
            "translation_state": args.translation_state,
            "authority_receipt_sha256": digest(raw["unit02_authority"]),
            "correction_ids": sorted(expected_correction_ids),
            "target_hashes": {
                str(spec["name"]): digest(raw[str(spec["target_key"])])
                for spec in translation_specs
            },
        },
        "inputs": {
            name: {
                "path": repository_path(paths[name], root),
                "bytes": len(raw[name]),
                "sha256": digest(raw[name]),
            }
            for name in sorted(paths)
        },
        "outputs": {
            "records.jsonl": {"bytes": len(jsonl), "sha256": digest(jsonl)},
            "records.csv": {"bytes": len(csv_bytes), "sha256": digest(csv_bytes)},
        },
        "safety_checks": {
            "unit01_records_byte_identical": True,
            "absolute_machine_paths_absent": True,
            "common_credential_markers_absent": True,
            "unit02_receipts_current": True,
        },
    }
    manifest_bytes = (
        json.dumps(generated, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    ).encode("utf-8")
    assert_public_safe("MANIFEST.json", manifest_bytes)
    (root / "backend/MANIFEST.json").write_bytes(manifest_bytes)


if __name__ == "__main__":
    main()
