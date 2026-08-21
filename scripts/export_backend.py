#!/usr/bin/env python3
"""Build deterministic first-unit O011 JSONL and CSV exchange views."""

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
WORKFLOW = "o011-export-backend-v1"
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
    return str(path.relative_to(root)).replace("\\", "/")


def assert_public_safe(label: str, data: bytes) -> None:
    text = data.decode("utf-8")
    folded = text.casefold()
    if WINDOWS_ABSOLUTE.search(text):
        raise RuntimeError(f"absolute Windows path leaked into {label}")
    found = [marker for marker in PUBLIC_SAFETY_MARKERS if marker in folded]
    if found:
        raise RuntimeError(f"private path or credential marker leaked into {label}: {found}")


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


def slices(text: str, marker: re.Pattern[str]) -> list[tuple[int, int, str]]:
    matches = list(marker.finditer(text))
    result: list[tuple[int, int, str]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        result.append((match.start(), end, text[match.start():end]))
    return result


def revision(rows: list[dict[str, str]], suffix: str) -> dict[str, str]:
    found = [row for row in rows if row.get("title", "").endswith(suffix)]
    if len(found) != 1:
        raise RuntimeError(f"expected one revision row ending {suffix!r}, found {len(found)}")
    return found[0]


def validate(records: list[dict[str, object]]) -> None:
    identifiers: set[str] = set()
    for record in records:
        missing = [field for field in ("schema", "schema_version", "id", "entity_type", "status", "timestamp", "workflow", "supersedes") if field not in record]
        if missing:
            raise RuntimeError(f"missing common fields in {record.get('id')}: {missing}")
        if record["schema"] != SCHEMA or record["schema_version"] != VERSION:
            raise RuntimeError("schema mismatch")
        if record["entity_type"] not in ENTITY_TYPES:
            raise RuntimeError(f"unknown entity type: {record['entity_type']}")
        identifier = str(record["id"])
        if not re.fullmatch(r"o011-[a-z0-9][a-z0-9._-]*", identifier):
            raise RuntimeError(f"invalid stable ID: {identifier}")
        if identifier in identifiers:
            raise RuntimeError(f"duplicate stable ID: {identifier}")
        identifiers.add(identifier)
        for field in ("source_sha256", "target_sha256"):
            value = record.get(field)
            if value is not None and not re.fullmatch(r"[0-9a-f]{64}", str(value)):
                raise RuntimeError(f"invalid {field} in {identifier}")
    for record in records:
        for field in ("parent_id", "resource_id", "edition_id", "rights_component_id", "target_id", "artifact_id"):
            value = record.get(field)
            if value is not None and value not in identifiers:
                raise RuntimeError(f"unresolved {field}={value!r} in {record['id']}")
        for value in record.get("component_rights_ids") or []:
            if value not in identifiers:
                raise RuntimeError(f"unresolved component_rights_ids value={value!r} in {record['id']}")
        if record["entity_type"] == "relation":
            for field in ("from_id", "to_id"):
                if record.get(field) not in identifiers:
                    raise RuntimeError(f"unresolved {field} in {record['id']}")
        for field in ("path", "receipt_path", "build_receipt_path"):
            value = record.get(field)
            if value is not None and (str(value).startswith(("/", "\\")) or WINDOWS_ABSOLUTE.search(str(value))):
                raise RuntimeError(f"absolute {field} in {record['id']}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--timestamp", required=True, help="Explicit checkpoint timestamp in ISO-8601 Z form")
    parser.add_argument("--translation-state", default="translated")
    args = parser.parse_args()
    root = args.root.resolve()
    timestamp = args.timestamp
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", timestamp):
        raise RuntimeError("timestamp must be explicit YYYY-MM-DDTHH:MM:SSZ")

    paths = {
        "schema": root / "backend/schema/o011-record-v1.schema.json",
        "lecture_source": root / "authority/expanded/lecture01_source.de.tex",
        "worksheet_source": root / "authority/expanded/worksheet01_source.de.tex",
        "lecture_target": root / "source/units/unit-01/lecture01.id.tex",
        "worksheet_target": root / "source/units/unit-01/worksheet01.id.tex",
        "solution_source": root / "authority/expanded/worksheet01_exercise01_solution_source.de.tex",
        "solution_target": root / "source/units/unit-01/worksheet01_exercise01_solution.id.tex",
        "solution_metadata": root / "authority/mediawiki/worksheet01_exercise01_solution_revid1111802.metadata.json",
        "revisions": root / "authority/brenner_selected_root_revisions.csv",
        "media": root / "authority/brenner_media_rights_manifest.csv",
        "terms": root / "00_control/TERMINOLOGY.csv",
        "adverse": root / "00_control/ADVERSE_LEDGER.csv",
        "lecture_corrections": root / "00_control/PROTECTED_CORRECTIONS.json",
        "worksheet_corrections": root / "00_control/WORKSHEET01_PROTECTED_CORRECTIONS.json",
        "media_qa": root / "qa/unit-01_media.json",
        "build_receipt": root / "qa/unit-01/build.json",
        "pdf_structural_qa": root / "qa/unit-01/pdf_structural_qa.json",
        "visual_qa": root / "qa/unit-01/visual_qa.json",
        "lecture_translation_receipt": root / "qa/unit-01/lecture_translation.json",
        "worksheet_translation_receipt": root / "qa/unit-01/worksheet_translation.json",
        "solution_translation_receipt": root / "qa/unit-01/worksheet_exercise01_solution_translation.json",
    }
    raw = {name: path.read_bytes() for name, path in paths.items()}
    text = {name: value.decode("utf-8-sig") for name, value in raw.items()}
    revision_rows = list(csv.DictReader(io.StringIO(text["revisions"])))
    media_rows = list(csv.DictReader(io.StringIO(text["media"])))
    term_rows = list(csv.DictReader(io.StringIO(text["terms"])))
    adverse_rows = list(csv.DictReader(io.StringIO(text["adverse"])))
    solution_metadata = json.loads(text["solution_metadata"])
    protected_corrections = [
        ("00_control/PROTECTED_CORRECTIONS.json", digest(raw["lecture_corrections"]), json.loads(text["lecture_corrections"])),
        ("00_control/WORKSHEET01_PROTECTED_CORRECTIONS.json", digest(raw["worksheet_corrections"]), json.loads(text["worksheet_corrections"])),
    ]
    translation_receipts = {
        "lecture": json.loads(text["lecture_translation_receipt"]),
        "worksheet": json.loads(text["worksheet_translation_receipt"]),
        "solution": json.loads(text["solution_translation_receipt"]),
    }
    media_qa = json.loads(text["media_qa"])
    build_receipt = json.loads(text["build_receipt"])
    pdf_structural_qa = json.loads(text["pdf_structural_qa"])
    visual_qa = json.loads(text["visual_qa"])
    pdf_path = root / "output/pdf/geometri-diferensial-manifold-mulus-unit-01-id.pdf"
    pdf_bytes = pdf_path.read_bytes()
    pdf_sha256 = digest(pdf_bytes)
    lecture_revision = revision(revision_rows, "/Vorlesung 1")
    worksheet_revision = revision(revision_rows, "/Arbeitsblatt 1")

    records: list[dict[str, object]] = []
    records.extend([
        base("o011-program-id", "program", timestamp, source_local_id="O011", language="Indonesian", locale="id-ID", name="Kurikulum matematika Bahasa Indonesia"),
        base("o011-course-d50", "course", timestamp, parent_id="o011-program-id", source_local_id="D50", order=50, name="Manifold mulus dan geometri diferensial", language="Indonesian", locale="id-ID"),
        base("o011-resource-brenner-dg2023", "resource", timestamp, parent_id="o011-course-d50", source_local_id="pageid:142521", source_locator="https://de.wikiversity.org/wiki/Kurs:Differentialgeometrie_(Osnabr%C3%BCck_2023)", name="Differentialgeometrie (Osnabrück 2023)", creator="Holger Brenner", rights_component_id="o011-rights-brenner-text"),
        base("o011-edition-brenner-current-20260821", "edition", timestamp, parent_id="o011-resource-brenner-dg2023", resource_id="o011-resource-brenner-dg2023", source_local_id="pageid:142521/revid:889544", source_locator="authority/mediawiki/brenner_course_recursive_current.xml", source_sha256=digest((root / "authority/mediawiki/brenner_course_recursive_current.xml").read_bytes()), rights_component_id="o011-rights-brenner-text", revision_set_sha256="4810e9c13e352db58d7ceb5495c1cf86cb991d2193eaf6a344a48799e7ab0f71", translation_state="source_frozen"),
        base("o011-rights-brenner-text", "rights", timestamp, source_local_id="CC-BY-SA-4.0", license="CC BY-SA 4.0", license_url="https://creativecommons.org/licenses/by-sa/4.0/", attribution="Holger Brenner; German Wikiversity page histories", change_notice_required=True, share_alike=True, component_scope="Wikiversity text only; media excluded"),
    ])

    unit_id = "o011-brenner-u01"
    lecture_id = unit_id + "-l01"
    worksheet_id = unit_id + "-w01"
    records.extend([
        base(unit_id, "unit", timestamp, parent_id="o011-course-d50", order=1, path="source/units/unit-01", resource_id="o011-resource-brenner-dg2023", edition_id="o011-edition-brenner-current-20260821", source_local_id="Vorlesung 1 + Arbeitsblatt 1", language="Indonesian", locale="id-ID", translation_state=args.translation_state, rights_component_id="o011-rights-brenner-text", unit_kind="lecture_worksheet_pair", title="Analisis dan Geometri"),
        base(lecture_id, "unit", timestamp, parent_id=unit_id, order=1, path="source/units/unit-01/lecture01.id.tex", resource_id="o011-resource-brenner-dg2023", edition_id="o011-edition-brenner-current-20260821", source_local_id=f"pageid:{lecture_revision['pageid']}/revid:{lecture_revision['revid']}", source_locator=lecture_revision["title"], source_sha256=digest(raw["lecture_source"]), target_sha256=digest(raw["lecture_target"]), language="Indonesian", locale="id-ID", translation_state=args.translation_state, rights_component_id="o011-rights-brenner-text", unit_kind="lecture"),
        base(worksheet_id, "unit", timestamp, parent_id=unit_id, order=2, path="source/units/unit-01/worksheet01.id.tex", resource_id="o011-resource-brenner-dg2023", edition_id="o011-edition-brenner-current-20260821", source_local_id=f"pageid:{worksheet_revision['pageid']}/revid:{worksheet_revision['revid']}", source_locator=worksheet_revision["title"], source_sha256=digest(raw["worksheet_source"]), target_sha256=digest(raw["worksheet_target"]), language="Indonesian", locale="id-ID", translation_state=args.translation_state, rights_component_id="o011-rights-brenner-text", unit_kind="worksheet"),
    ])

    lecture_source_slices = slices(text["lecture_source"], LECTURE_MARKER)
    lecture_target_slices = slices(text["lecture_target"], LECTURE_MARKER)
    if len(lecture_source_slices) != 4 or len(lecture_target_slices) != 4:
        raise RuntimeError("Lecture 1 must contain exactly four section markers")
    for index, (source_part, target_part) in enumerate(zip(lecture_source_slices, lecture_target_slices), 1):
        _, _, source_value = source_part
        _, _, target_value = target_part
        segment_id = f"{lecture_id}-s{index:02d}"
        records.append(base(segment_id, "segment", timestamp, parent_id=lecture_id, order=index, path=f"source/units/unit-01/lecture01.id.tex#section-{index}", resource_id="o011-resource-brenner-dg2023", edition_id="o011-edition-brenner-current-20260821", source_local_id=f"lecture01:section:{index}", source_locator=f"{lecture_revision['title']}#section-{index}", source_sha256=digest(source_value.encode("utf-8")), target_sha256=digest(target_value.encode("utf-8")), language="Indonesian", locale="id-ID", translation_state=args.translation_state, rights_component_id="o011-rights-brenner-text", segment_kind="lecture_section"))

    concepts = [
        ("regular-level-set", "reguläre Faser", "serat reguler"),
        ("hypersurface", "Hyperfläche", "hipermuka"),
        ("tangent-space", "Tangentialraum", "ruang tangen"),
        ("tangent-vector-field", "tangentiales Vektorfeld", "medan vektor tangensial"),
        ("constrained-extremum", "Extremum unter Nebenbedingungen", "ekstremum dengan kendala"),
        ("normal-tangent-decomposition", "Tangential- und Normalkomponente", "penguraian komponen tangen dan normal"),
        ("tangential-acceleration", "Tangentialbeschleunigung", "percepatan tangensial"),
        ("geodesic", "geodätische Kurve", "kurva geodesik"),
        ("great-circle", "Großkreis", "lingkaran besar"),
    ]
    for slug, source_label, target_label in concepts:
        records.append(base(
            f"o011-concept-{slug}",
            "concept",
            timestamp,
            parent_id="o011-course-d50",
            source_local_id=source_label,
            language=None,
            locale=None,
            labels={"de": source_label, "id-ID": target_label},
        ))
    section_concepts = {
        1: ("regular-level-set", "hypersurface", "tangent-space"),
        2: ("tangent-vector-field", "constrained-extremum"),
        3: ("normal-tangent-decomposition", "tangential-acceleration"),
        4: ("geodesic", "great-circle"),
    }
    for section_order, concept_slugs in section_concepts.items():
        for relation_order, slug in enumerate(concept_slugs, 1):
            records.append(base(
                f"o011-rel-l01-s{section_order:02d}-covers-{slug}",
                "relation",
                timestamp,
                order=relation_order,
                relation_type="covers",
                from_id=f"{lecture_id}-s{section_order:02d}",
                to_id=f"o011-concept-{slug}",
                evidence="Direct section content in the frozen Lecture 1 source",
            ))

    worksheet_source_slices = slices(text["worksheet_source"], EXERCISE_MARKER)
    worksheet_target_slices = slices(text["worksheet_target"], EXERCISE_MARKER)
    if len(worksheet_source_slices) != 19 or len(worksheet_target_slices) != 19:
        raise RuntimeError("Worksheet 1 must contain exactly 19 exercise markers")
    previous: str | None = None
    for index, (source_part, target_part) in enumerate(zip(worksheet_source_slices, worksheet_target_slices), 1):
        _, _, source_value = source_part
        _, _, target_value = target_part
        exercise_id = f"{worksheet_id}-e{index:03d}"
        records.append(base(exercise_id, "unit", timestamp, parent_id=worksheet_id, order=index, path=f"source/units/unit-01/worksheet01.id.tex#exercise-{index}", resource_id="o011-resource-brenner-dg2023", edition_id="o011-edition-brenner-current-20260821", source_local_id=f"worksheet01:exercise:{index}", source_locator=f"{worksheet_revision['title']}#exercise-{index}", source_sha256=digest(source_value.encode("utf-8")), target_sha256=digest(target_value.encode("utf-8")), language="Indonesian", locale="id-ID", translation_state=args.translation_state, rights_component_id="o011-rights-brenner-text", unit_kind="exercise", has_authority_solution=index == 1))
        if previous:
            records.append(base(f"o011-rel-w01-e{index-1:03d}-precedes-e{index:03d}", "relation", timestamp, relation_type="precedes", from_id=previous, to_id=exercise_id))
        previous = exercise_id

    solution_id = worksheet_id + "-e001-solution"
    records.append(base(
        solution_id,
        "unit",
        timestamp,
        parent_id=worksheet_id + "-e001",
        order=1,
        path="source/units/unit-01/worksheet01_exercise01_solution.id.tex",
        resource_id="o011-resource-brenner-dg2023",
        edition_id="o011-edition-brenner-current-20260821",
        source_local_id=f"pageid:{solution_metadata['pageid']}/revid:{solution_metadata['revid']}",
        source_locator=solution_metadata["title"],
        source_sha256=digest(raw["solution_source"]),
        target_sha256=digest(raw["solution_target"]),
        language="Indonesian",
        locale="id-ID",
        translation_state=args.translation_state,
        rights_component_id="o011-rights-brenner-text",
        unit_kind="solution",
    ))
    records.append(base(
        "o011-rel-w01-e001-solution-solves-e001",
        "relation",
        timestamp,
        relation_type="solves",
        from_id=solution_id,
        to_id=worksheet_id + "-e001",
    ))

    chosen_assets = {"File:3d-function-6.svg", "File:Great circle passing through two points.svg", "File:2019-07-Helix.jpg", "File:Planned flight map of the Oiseau Blanc.svg"}
    selected_media = [row for row in media_rows if row.get("title") in chosen_assets]
    if {row["title"] for row in selected_media} != chosen_assets:
        raise RuntimeError("Unit 1 media manifest closure is incomplete")
    asset_ids: list[str] = []
    media_rights_ids: list[str] = []
    for index, row in enumerate(sorted(selected_media, key=lambda value: value["title"].casefold()), 1):
        slug = re.sub(r"[^a-z0-9]+", "-", row["title"].lower()).strip("-")
        rights_id = f"o011-rights-media-{index:02d}"
        asset_id = f"o011-asset-{slug}"
        asset_ids.append(asset_id)
        media_rights_ids.append(rights_id)
        records.append(base(rights_id, "rights", timestamp, source_local_id=row["title"], license=row["license"], license_url=row["license_url"] or None, attribution=row["artist_html"], credit=row["credit_html"], component_scope=row["title"], attribution_required=row["attribution_required"].lower() == "true"))
        local_name = row["title"].removeprefix("File:")
        local_path = root / "authority/media" / local_name
        records.append(base(asset_id, "asset", timestamp, parent_id=unit_id, order=index, path=f"authority/media/{local_name}", source_local_id=row["title"], source_locator=row["description_url"], source_sha256=digest(local_path.read_bytes()) if local_path.is_file() else None, rights_component_id=rights_id, mime=row["mime"], expected_bytes=int(row["bytes"]), commons_sha1=row["commons_sha1_hex"], binary_present=local_path.is_file()))

    translation_specs = {
        "lecture": {
            "qa_id": "o011-qa-unit01-lecture-translation",
            "target_id": lecture_id,
            "source_key": "lecture_source",
            "target_key": "lecture_target",
            "receipt_key": "lecture_translation_receipt",
        },
        "worksheet": {
            "qa_id": "o011-qa-unit01-worksheet-translation",
            "target_id": worksheet_id,
            "source_key": "worksheet_source",
            "target_key": "worksheet_target",
            "receipt_key": "worksheet_translation_receipt",
        },
        "solution": {
            "qa_id": "o011-qa-unit01-solution-translation",
            "target_id": solution_id,
            "source_key": "solution_source",
            "target_key": "solution_target",
            "receipt_key": "solution_translation_receipt",
        },
    }
    for name, spec in translation_specs.items():
        receipt = translation_receipts[name]
        if receipt.get("status") != "pass" or receipt.get("failures"):
            raise RuntimeError(f"{name} translation receipt is not a clean pass")
        if receipt.get("source_sha256") != digest(raw[str(spec["source_key"])]) or receipt.get("target_sha256") != digest(raw[str(spec["target_key"]) ]):
            raise RuntimeError(f"{name} translation receipt is stale")
        receipt_key = str(spec["receipt_key"])
        records.append(base(
            str(spec["qa_id"]),
            "qa_event",
            timestamp,
            parent_id=unit_id,
            target_id=str(spec["target_id"]),
            receipt_path=repository_path(paths[receipt_key], root),
            evidence_sha256=digest(raw[receipt_key]),
            source_sha256=receipt["source_sha256"],
            target_sha256=receipt["target_sha256"],
            language="Indonesian",
            locale="id-ID",
            translation_state="structurally_verified",
            qa_kind="translation_structure",
            result="pass",
            checks=receipt["checks"],
            counts=receipt["counts"],
            declared_corrections=sorted(set(receipt.get("declared_corrections") or [])),
        ))

    media_by_filename = {item["filename"]: item for item in media_qa.get("media", [])}
    if media_qa.get("source_count") != 4 or set(media_by_filename) != {title.removeprefix("File:") for title in chosen_assets}:
        raise RuntimeError("Unit 1 media QA receipt does not describe the exact four-file closure")
    if media_qa.get("manifest_sha256") != digest(raw["media"]):
        raise RuntimeError("Unit 1 media QA receipt is stale relative to the rights manifest")
    for row in selected_media:
        filename = row["title"].removeprefix("File:")
        media_path = root / "authority/media" / filename
        if media_by_filename[filename].get("canonical_sha256") != digest(media_path.read_bytes()):
            raise RuntimeError(f"Unit 1 media QA receipt is stale for {filename}")
    records.append(base(
        "o011-qa-unit01-media-closure",
        "qa_event",
        timestamp,
        parent_id=unit_id,
        target_id=unit_id,
        receipt_path=repository_path(paths["media_qa"], root),
        evidence_sha256=digest(raw["media_qa"]),
        source_sha256=digest(raw["media"]),
        language=None,
        locale=None,
        translation_state="structurally_verified",
        qa_kind="media_rights_and_binary_closure",
        result="pass",
        source_count=media_qa["source_count"],
        derivative_count=media_qa["derivative_count"],
        asset_ids=sorted(asset_ids),
        component_rights_ids=sorted(media_rights_ids),
    ))

    expected_pdf_relative = repository_path(pdf_path, root)
    build_output = build_receipt.get("output") or {}
    cycles = build_receipt.get("cycles") or []
    cycle_hashes = {cycle.get("sha256") for cycle in cycles}
    cycle_bytes = {cycle.get("bytes") for cycle in cycles}
    if not build_receipt.get("deterministic_clean_cycles") or len(cycles) < 2 or cycle_hashes != {pdf_sha256} or cycle_bytes != {len(pdf_bytes)}:
        raise RuntimeError("PDF build receipt does not prove two matching clean cycles")
    if build_output.get("path") != expected_pdf_relative or build_output.get("sha256") != pdf_sha256 or build_output.get("bytes") != len(pdf_bytes):
        raise RuntimeError("PDF build receipt is stale relative to the final artifact")
    structural_pdf = pdf_structural_qa.get("pdf") or {}
    if structural_pdf.get("path") != expected_pdf_relative or structural_pdf.get("sha256") != pdf_sha256 or structural_pdf.get("bytes") != len(pdf_bytes):
        raise RuntimeError("PDF structural QA receipt is stale relative to the final artifact")
    if not pdf_structural_qa.get("passed") or pdf_structural_qa.get("blockers"):
        raise RuntimeError("PDF structural QA receipt is not a clean pass")
    if structural_pdf.get("pages", 0) < 1 or not structural_pdf.get("all_pages_same_size") or not structural_pdf.get("all_rotations_zero") or structural_pdf.get("encrypted"):
        raise RuntimeError("PDF structural QA receipt fails page-structure checks")
    if structural_pdf.get("catalog_language") != "id-ID" or (pdf_structural_qa.get("accessibility") or {}).get("pages_with_extractable_text") != structural_pdf.get("pages"):
        raise RuntimeError("PDF structural QA receipt fails language or text-extraction checks")
    if (pdf_structural_qa.get("links") or {}).get("unsafe_actions") or any((pdf_structural_qa.get("active_content") or {}).values()):
        raise RuntimeError("PDF structural QA receipt reports unsafe actions or active content")
    if not pdf_structural_qa.get("required_attribution_text_present") or pdf_structural_qa.get("forbidden_text_residues"):
        raise RuntimeError("PDF structural QA receipt fails attribution or residue checks")
    visual_pdf = visual_qa.get("pdf") or {}
    visual_render = visual_qa.get("render") or {}
    visual_inspection = visual_qa.get("inspection") or {}
    if visual_pdf.get("path") != expected_pdf_relative or visual_pdf.get("sha256") != pdf_sha256 or visual_pdf.get("bytes") != len(pdf_bytes):
        raise RuntimeError("PDF visual QA receipt is stale relative to the final artifact")
    if visual_qa.get("status") != "pass" or not visual_inspection.get("all_pages_inspected") or visual_render.get("page_count") != structural_pdf.get("pages"):
        raise RuntimeError("PDF visual QA receipt is not a complete pass")
    expected_visual_results = {
        "title_and_front_matter": "pass",
        "body_text_and_mathematics": "pass",
        "figures_and_captions": "pass",
        "worksheet_and_supplied_solution": "pass",
        "list_of_figures": "pass",
        "media_attribution_and_license_pages": "pass",
        "clipping_or_overlap": "none",
        "missing_or_corrupt_glyphs": "none",
        "unexpected_blank_pages": "none",
    }
    if any(visual_inspection.get(key) != expected for key, expected in expected_visual_results.items()):
        raise RuntimeError("PDF visual QA receipt contains a failed inspection category")
    pdf_artifact_id = "o011-artifact-unit01-pdf"
    records.append(base(
        pdf_artifact_id,
        "artifact",
        timestamp,
        parent_id=unit_id,
        path=expected_pdf_relative,
        target_sha256=pdf_sha256,
        language="Indonesian",
        locale="id-ID",
        translation_state="visually_checked",
        artifact_kind="reader_pdf",
        media_type="application/pdf",
        bytes=len(pdf_bytes),
        build_receipt_path=repository_path(paths["build_receipt"], root),
        build_receipt_sha256=digest(raw["build_receipt"]),
        deterministic_clean_cycles=True,
        clean_cycle_count=len(cycles),
        component_rights_ids=["o011-rights-brenner-text", *sorted(media_rights_ids)],
    ))
    records.append(base(
        "o011-qa-unit01-pdf-reproducibility",
        "qa_event",
        timestamp,
        parent_id=unit_id,
        target_id=pdf_artifact_id,
        artifact_id=pdf_artifact_id,
        receipt_path=repository_path(paths["build_receipt"], root),
        evidence_sha256=digest(raw["build_receipt"]),
        target_sha256=pdf_sha256,
        language="Indonesian",
        locale="id-ID",
        translation_state="built",
        qa_kind="reproducible_pdf_build",
        result="pass",
        engine=build_receipt.get("engine"),
        clean_cycle_count=len(cycles),
        pass_count_per_cycle=3,
        deterministic_clean_cycles=True,
        artifact_bytes=len(pdf_bytes),
    ))
    records.append(base(
        "o011-qa-unit01-pdf-structural",
        "qa_event",
        timestamp,
        parent_id=unit_id,
        target_id=pdf_artifact_id,
        artifact_id=pdf_artifact_id,
        receipt_path=repository_path(paths["pdf_structural_qa"], root),
        evidence_sha256=digest(raw["pdf_structural_qa"]),
        target_sha256=pdf_sha256,
        language="Indonesian",
        locale="id-ID",
        translation_state="visually_checked",
        qa_kind="pdf_structure_accessibility_and_safety",
        result="pass",
        page_count=structural_pdf["pages"],
        page_size_points=structural_pdf["page_size_points"],
        catalog_language=structural_pdf["catalog_language"],
        tagged=structural_pdf["tagged"],
        accessibility=pdf_structural_qa["accessibility"],
        external_uri_count=pdf_structural_qa["links"]["external_uri_count"],
        internal_link_count=pdf_structural_qa["links"]["internal_link_count"],
        active_content=pdf_structural_qa["active_content"],
        required_attribution_text_present=True,
        limitations=pdf_structural_qa.get("limitations") or [],
    ))
    records.append(base(
        "o011-qa-unit01-pdf-visual",
        "qa_event",
        timestamp,
        parent_id=unit_id,
        target_id=pdf_artifact_id,
        artifact_id=pdf_artifact_id,
        receipt_path=repository_path(paths["visual_qa"], root),
        evidence_sha256=digest(raw["visual_qa"]),
        target_sha256=pdf_sha256,
        language="Indonesian",
        locale="id-ID",
        translation_state="visually_checked",
        qa_kind="pdf_visual_inspection",
        result="pass",
        render_engine=visual_render["engine"],
        page_count=visual_render["page_count"],
        page_dimensions_pixels=visual_render["page_dimensions_pixels"],
        all_pages_inspected=True,
        inspection=visual_inspection,
    ))

    for row in term_rows:
        records.append(base(row["id"].lower(), "term", timestamp, source_local_id=row["source_de"], language="Indonesian", locale="id-ID", translation_state="translated", source_expression=row["source_de"], target_expression=row["target_id"], term_status=row["status"], note=row["note"] or None))
    for row in adverse_rows:
        correction_id = row["id"].lower()
        protected_deltas: list[dict[str, object]] = []
        for manifest_path, manifest_sha256, document in protected_corrections:
            for delta in document.get("allowed_deltas", []):
                correction_ids = str(delta.get("correction_id", "")).split("+")
                if row["id"] in correction_ids:
                    protected_deltas.append({
                        "manifest_path": manifest_path,
                        "manifest_sha256": manifest_sha256,
                        **delta,
                    })
        values: dict[str, object] = {
            "source_local_id": row["surface"],
            "severity": row["severity"],
            "correction_status": row["status"],
            "description": row["description"],
            "disposition": row["disposition"],
            "upstream_report_disposition": "deferred_until_full_corpus",
            "ledger_sha256": digest(raw["adverse"]),
            "protected_deltas": protected_deltas,
        }
        if row["id"] == "O011-CORR-0003":
            values["rights_manifest_sha256"] = digest(raw["media"])
            values["media_qa_sha256"] = digest(raw["media_qa"])
        records.append(base(correction_id, "correction", timestamp, **values))

    for child in list(records):
        parent_id = child.get("parent_id")
        if parent_id and child["entity_type"] not in {"relation", "rights", "correction"}:
            child_slug = str(child["id"]).removeprefix("o011-")
            records.append(base(
                f"o011-rel-contains-{child_slug}",
                "relation",
                timestamp,
                relation_type="contains",
                from_id=parent_id,
                to_id=child["id"],
            ))

    records.sort(key=lambda record: str(record["id"]))
    validate(records)
    output = root / "backend/records.jsonl"
    output.parent.mkdir(parents=True, exist_ok=True)
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

    generated = {
        "schema_version": 1,
        "generator": "scripts/export_backend.py",
        "generator_sha256": digest(Path(__file__).read_bytes()),
        "timestamp": timestamp,
        "record_count": len(records),
        "entity_counts": {name: sum(record["entity_type"] == name for record in records) for name in sorted(ENTITY_TYPES)},
        "inputs": {name: {"path": str(paths[name].relative_to(root)).replace("\\", "/"), "bytes": len(raw[name]), "sha256": digest(raw[name])} for name in sorted(paths)},
        "outputs": {
            "records.jsonl": {"bytes": len(jsonl), "sha256": digest(jsonl)},
            "records.csv": {"bytes": len(csv_bytes), "sha256": digest(csv_bytes)},
        },
        "safety_checks": {
            "absolute_machine_paths_absent": True,
            "common_credential_markers_absent": True,
        },
    }
    manifest_bytes = (json.dumps(generated, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    assert_public_safe("MANIFEST.json", manifest_bytes)
    (root / "backend/MANIFEST.json").write_bytes(manifest_bytes)


if __name__ == "__main__":
    main()
