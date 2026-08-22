#!/usr/bin/env python3
"""Append the deterministic Unit 4 extension to the frozen Units 1--3 backend.

The first 591 JSONL records and the corresponding 591 CSV data rows are an
immutable baseline.  A repeated run discards any existing Unit 4 suffix and
recreates it from the current, receipt-bound Unit 4 files.
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


SCHEMA = "o011-modular-backend"
SCHEMA_VERSION = 1
WORKFLOW = "o011-export-backend-v4"
BASELINE_RECORD_COUNT = 591
BASELINE_JSONL_BYTES = 350_935
BASELINE_JSONL_SHA256 = "e2b1e159b1dff04273ddb0af82e85dc32adbb507f3936881f750867527d6800a"
BASELINE_CSV_BYTES = 125_961
BASELINE_CSV_SHA256 = "bdd4648d7e104da5f96a20ff85850a8782379f02609c3f29ed88117401032941"
SOLUTION_INDICES = (7, 10)
TERM_NUMBERS = range(78, 96)
CORRECTION_NUMBERS = range(38, 46)
ENTITY_TYPES = {
    "program", "course", "resource", "edition", "unit", "concept",
    "segment", "term", "asset", "relation", "rights", "qa_event",
    "artifact", "correction",
}
COMMON = (
    "schema", "schema_version", "id", "entity_type", "source_local_id",
    "parent_id", "order", "path", "resource_id", "edition_id",
    "source_locator", "source_sha256", "target_sha256", "language",
    "locale", "translation_state", "rights_component_id", "status",
    "timestamp", "workflow", "supersedes",
)
LECTURE_MARKER = re.compile(r"(?m)^\s*\\zwischenueberschrift\s*\{")
EXERCISE_MARKER = re.compile(
    r"(?m)^\s*\\(?:inputaufgabegibtloesung|inputaufgabe)\b"
)
WINDOWS_ABSOLUTE = re.compile(r"(?i)(?<![a-z0-9+.-])[a-z]:[\\/]")
PRIVATE_MARKERS = (
    "\\users\\", "/users/", "\\appdata\\", "/home/", "github_pat_",
    "ghp_", "gho_", "ghu_", "ghs_", "ghr_", "glpat-", "sk-proj-",
    "xoxb-", "bearer ", "access_token", "api_key", "zenodo token",
)

CONCEPTS = (
    ("weingarten-map", "Weingartenabbildung", "pemetaan Weingarten"),
    ("normal-acceleration", "Normalbeschleunigung", "percepatan normal"),
    (
        "shape-operator-self-adjoint",
        "Selbstadjungiertheit der Weingartenabbildung",
        "sifat adjoin-diri pemetaan Weingarten",
    ),
    (
        "shape-operator-diagonalization",
        "Diagonalisierung der Weingartenabbildung",
        "diagonalisasi pemetaan Weingarten",
    ),
    (
        "graph-shape-operator",
        "Weingartenabbildung eines Graphen",
        "pemetaan Weingarten suatu grafik",
    ),
)

CORRECTION_TARGETS = {
    "O011-CORR-0038": ("worksheet", 2),
    "O011-CORR-0039": ("solution", 7),
    "O011-CORR-0040": ("solution", 10),
    "O011-CORR-0041": ("lecture", None),
    "O011-CORR-0042": ("lecture", None),
    "O011-CORR-0043": ("lecture", None),
    "O011-CORR-0044": ("worksheet", 6),
    "O011-CORR-0045": ("worksheet", 9),
}

CORRECTION_MANIFESTS = {
    "worksheet": "u04_worksheet_corrections",
    "solution07": "u04_solution07_corrections",
    "solution10": "u04_solution10_corrections",
    "lecture": "u04_lecture_corrections",
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def repository_path(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def file_binding(path: Path, root: Path) -> dict[str, object]:
    data = path.read_bytes()
    return {
        "path": repository_path(path, root),
        "bytes": len(data),
        "sha256": digest(data),
    }


def base(record_id: str, entity_type: str, timestamp: str, **values: object) -> dict[str, object]:
    record: dict[str, object] = {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
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
        text[m.start() : (matches[i + 1].start() if i + 1 < len(matches) else len(text))]
        for i, m in enumerate(matches)
    ]


def extract_prefix(data: bytes, line_count: int, label: str) -> bytes:
    lines = data.splitlines(keepends=True)
    if len(lines) < line_count:
        raise RuntimeError(f"{label} has fewer than {line_count} physical lines")
    prefix = b"".join(lines[:line_count])
    if not prefix.endswith(b"\n"):
        raise RuntimeError(f"{label} prefix is not LF terminated")
    return prefix


def assert_public_safe(label: str, data: bytes) -> None:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RuntimeError(f"{label} is not UTF-8") from exc
    folded = text.casefold()
    if WINDOWS_ABSOLUTE.search(text):
        raise RuntimeError(f"absolute Windows path leaked into {label}")
    found = [marker for marker in PRIVATE_MARKERS if marker in folded]
    if found:
        raise RuntimeError(f"private or credential marker leaked into {label}: {found}")


def load_json(raw: dict[str, bytes], key: str) -> dict[str, Any]:
    return json.loads(raw[key].decode("utf-8-sig"))


def validate(records: list[dict[str, object]], schema: dict[str, Any]) -> None:
    identifiers: set[str] = set()
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    for record in records:
        identifier = str(record.get("id"))
        if not re.fullmatch(r"o011-[a-z0-9][a-z0-9._-]*", identifier):
            raise RuntimeError(f"invalid stable ID: {identifier}")
        if identifier in identifiers:
            raise RuntimeError(f"duplicate stable ID: {identifier}")
        identifiers.add(identifier)
        if record.get("entity_type") not in ENTITY_TYPES:
            raise RuntimeError(f"invalid entity type in {identifier}")
        errors = sorted(validator.iter_errors(record), key=lambda e: list(e.path))
        if errors:
            raise RuntimeError(f"schema failure in {identifier}: {errors[0].message}")
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
        if record.get("entity_type") == "relation":
            for field in ("from_id", "to_id"):
                if record.get(field) not in identifiers:
                    raise RuntimeError(f"unresolved {field} in {record['id']}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--translation-state", default="visually_checked")
    args = parser.parse_args()
    root = args.root.resolve()
    timestamp = args.checkpoint
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", timestamp):
        raise RuntimeError("checkpoint must be explicit YYYY-MM-DDTHH:MM:SSZ")
    if args.translation_state != "visually_checked":
        raise RuntimeError("final Unit 4 backend state must be visually_checked")

    jsonl_path = root / "backend/records.jsonl"
    csv_path = root / "backend/records.csv"
    baseline_jsonl = extract_prefix(jsonl_path.read_bytes(), BASELINE_RECORD_COUNT, "records.jsonl")
    baseline_csv = extract_prefix(csv_path.read_bytes(), BASELINE_RECORD_COUNT + 1, "records.csv")
    if len(baseline_jsonl) != BASELINE_JSONL_BYTES or digest(baseline_jsonl) != BASELINE_JSONL_SHA256:
        raise RuntimeError("immutable 591-record JSONL baseline changed")
    if len(baseline_csv) != BASELINE_CSV_BYTES or digest(baseline_csv) != BASELINE_CSV_SHA256:
        raise RuntimeError("immutable 591-row CSV baseline changed")
    baseline_records = [json.loads(line) for line in baseline_jsonl.decode("utf-8").splitlines()]
    if len(baseline_records) != BASELINE_RECORD_COUNT:
        raise RuntimeError("baseline JSONL record count changed")
    baseline_ids = {str(record["id"]) for record in baseline_records}

    paths: dict[str, Path] = {
        "schema": root / "backend/schema/o011-record-v1.schema.json",
        "root_revisions": root / "authority/brenner_selected_root_revisions.csv",
        "surface_revisions": root / "authority/brenner_selected_surface_revisions.csv",
        "media_rights": root / "authority/brenner_media_rights_manifest.csv",
        "terminology": root / "00_control/TERMINOLOGY.csv",
        "adverse": root / "00_control/ADVERSE_LEDGER.csv",
        "u04_authority": root / "qa/unit-04/AUTHORITY_PREFLIGHT.json",
        "u04_authority_verify": root / "qa/unit-04/AUTHORITY_PREFLIGHT_VERIFY.json",
        "u04_current_revision": root / "qa/unit-04/CURRENT_REVISION_CHECK.json",
        "u04_solution_closure": root / "qa/unit-04/solution_closure.json",
        "u04_media_closure": root / "qa/unit-04/media_closure.json",
        "u04_media_receipt": root / "qa/unit-04_media.json",
        "u04_media_config": root / "source/unit_media.json",
        "u04_media_attribution": root / "build/generated/unit04-media-attribution-cumulative.tex",
        "u04_official_pdf_witness": root / "qa/unit-04/OFFICIAL_PDF_WITNESS.json",
        "u04_official_pdf_qa": root / "qa/unit-04/OFFICIAL_PDF_STRUCTURAL_VISUAL_QA.json",
        "u04_official_pdf": root / "authority/pdf/lecture04_commons_revid1003382720.pdf",
        "u04_authority_anomalies": root / "qa/unit-04/AUTHORITY_ANOMALIES.md",
        "u04_lecture_source": root / "authority/expanded/lecture04_source.de.tex",
        "u04_lecture_target": root / "source/units/unit-04/lecture04.id.tex",
        "u04_lecture_receipt": root / "qa/unit-04/lecture04_translation.json",
        "u04_worksheet_source": root / "authority/expanded/worksheet04_source.de.tex",
        "u04_worksheet_target": root / "source/units/unit-04/worksheet04.id.tex",
        "u04_worksheet_receipt": root / "qa/unit-04/worksheet04_translation.json",
        "u04_solution07_source": root / "authority/expanded/worksheet04_exercise07_solution_source.de.tex",
        "u04_solution07_target": root / "source/units/unit-04/worksheet04_exercise07_solution.id.tex",
        "u04_solution07_receipt": root / "qa/unit-04/worksheet04_exercise07_solution_translation.json",
        "u04_solution10_source": root / "authority/expanded/worksheet04_exercise10_solution_source.de.tex",
        "u04_solution10_target": root / "source/units/unit-04/worksheet04_exercise10_solution.id.tex",
        "u04_solution10_receipt": root / "qa/unit-04/worksheet04_exercise10_solution_translation.json",
        "u04_lecture_corrections": root / "00_control/LECTURE04_PROTECTED_CORRECTIONS.json",
        "u04_worksheet_corrections": root / "00_control/WORKSHEET04_PROTECTED_CORRECTIONS.json",
        "u04_solution07_corrections": root / "00_control/SOLUTION04_07_PROTECTED_CORRECTIONS.json",
        "u04_solution10_corrections": root / "00_control/SOLUTION04_10_PROTECTED_CORRECTIONS.json",
        "u04_build_receipt": root / "qa/unit-04/build.json",
        "u04_structural_receipt": root / "qa/unit-04/STRUCTURAL_QA.json",
        "u04_visual_receipt": root / "qa/unit-04/VISUAL_QA.md",
        "u04_lecture_math_review": root / "qa/unit-04/LECTURE_FINDINGS.md",
        "u04_worksheet_math_review": root / "qa/unit-04/WORKSHEET_FINDINGS.md",
        "u04_final_math_audit": root / "qa/unit-04/POST_REPAIR_MATH_AUDIT.md",
        "u04_reader_pdf": root / "output/pdf/geometri-diferensial-manifold-mulus-hingga-unit-04-id.pdf",
    }
    raw = {name: path.read_bytes() for name, path in paths.items()}
    schema = json.loads(raw["schema"].decode("utf-8"))
    Draft202012Validator.check_schema(schema)
    validate(baseline_records, schema)

    for key in (
        "u04_lecture_target", "u04_worksheet_target", "u04_solution07_target",
        "u04_solution10_target",
    ):
        assert_public_safe(repository_path(paths[key], root), raw[key])

    authority = load_json(raw, "u04_authority")
    authority_verify = load_json(raw, "u04_authority_verify")
    current_revision = load_json(raw, "u04_current_revision")
    solution_closure = load_json(raw, "u04_solution_closure")
    media_closure = load_json(raw, "u04_media_closure")
    media_receipt = load_json(raw, "u04_media_receipt")
    media_config = load_json(raw, "u04_media_config")
    official_witness = load_json(raw, "u04_official_pdf_witness")
    official_qa = load_json(raw, "u04_official_pdf_qa")
    build_receipt = load_json(raw, "u04_build_receipt")
    structural_receipt = load_json(raw, "u04_structural_receipt")

    expected_structure = {
        "all_hint_fields_blank": True,
        "lecture_section_count": 1,
        "worksheet_exercise_count": 15,
        "worksheet_graded_count": 4,
        "worksheet_point_total": 19,
        "worksheet_practice_count": 11,
        "worksheet_section_count": 2,
        "worksheet_solution_bearing_indices": [7, 10],
    }
    if authority.get("status") != "pass" or authority.get("unit") != 4:
        raise RuntimeError("Unit 4 authority preflight is not a pass")
    if authority.get("structure") != expected_structure:
        raise RuntimeError("Unit 4 topology in the authority receipt changed")
    if authority.get("solutions") != solution_closure:
        raise RuntimeError("Unit 4 solution closure drifted from the authority receipt")
    if (
        authority_verify.get("status") != "pass"
        or authority_verify.get("unit") != 4
        or authority_verify.get("preflight")
        != {
            "path": repository_path(paths["u04_authority"], root),
            "bytes": len(raw["u04_authority"]),
            "sha256": digest(raw["u04_authority"]),
        }
    ):
        raise RuntimeError("Unit 4 offline authority verification is stale")
    if (
        current_revision.get("status") != "pass"
        or current_revision.get("unit") != 4
        or not current_revision.get("all_four_frozen_revisions_remain_live_current")
        or current_revision.get("preflight_input", {}).get("sha256") != digest(raw["u04_authority"])
        or len(current_revision.get("surfaces") or []) != 4
        or not all(
            row.get("pageid_match") and row.get("revid_match")
            and row.get("lastrevid_match") and row.get("timestamp_match")
            for row in current_revision.get("surfaces") or []
        )
    ):
        raise RuntimeError("Unit 4 current-revision evidence is incomplete or stale")

    if (
        solution_closure.get("exercise_count") != 15
        or solution_closure.get("practice_exercise_count") != 11
        or solution_closure.get("graded_exercise_count") != 4
        or solution_closure.get("point_value_total") != 19
        or tuple(solution_closure.get("supplied_solution_indices") or []) != SOLUTION_INDICES
        or solution_closure.get("supplied_solution_count") != 2
        or solution_closure.get("missing_solution_count") != 13
    ):
        raise RuntimeError("Unit 4 exercise/solution census changed")
    exercises = solution_closure.get("exercises") or []
    if len(exercises) != 15 or [row.get("exercise_index") for row in exercises] != list(range(1, 16)):
        raise RuntimeError("Unit 4 exercise order changed")
    if [row.get("point_value") for row in exercises if row.get("point_value") is not None] != [4, 5, 4, 6]:
        raise RuntimeError("Unit 4 graded point structure changed")
    if any(row.get("hint_field") != "" for row in exercises):
        raise RuntimeError("Unit 4 authority unexpectedly contains a hint")
    if [row["exercise_index"] for row in exercises if row.get("exists")] != list(SOLUTION_INDICES):
        raise RuntimeError("Unit 4 supplied-solution closure changed")

    if (
        media_closure.get("status") != "pass"
        or media_closure.get("unit") != 4
        or media_closure.get("displayed_media_occurrences") != 0
        or media_closure.get("unique_media_assets") != 0
        or media_closure.get("assets") != []
        or media_config.get("units", {}).get("4", {}).get("media") != []
        or media_receipt.get("unit_number") != 4
        or media_receipt.get("source_count") != 0
        or media_receipt.get("derivative_count") != 0
        or media_receipt.get("media") != []
        or media_receipt.get("media_config_sha256") != digest(raw["u04_media_config"])
    ):
        raise RuntimeError("Unit 4 zero-media closure changed")
    attribution_binding = media_receipt.get("attribution_tex") or {}
    if attribution_binding != file_binding(paths["u04_media_attribution"], root):
        raise RuntimeError("Unit 4 zero-media attribution derivative is stale")

    if (
        official_witness.get("status") != "pass"
        or official_witness.get("binary") != file_binding(paths["u04_official_pdf"], root)
        or official_witness.get("release_asset") is not False
        or official_witness.get("production_master") is not False
        or "withheld" not in str(official_witness.get("redistribution_status"))
        or official_qa.get("source") != file_binding(paths["u04_official_pdf"], root)
        or official_qa.get("release_asset") is not False
        or "withheld" not in str(official_qa.get("redistribution_status"))
    ):
        raise RuntimeError("official Unit 4 PDF witness disposition changed")

    pages = authority["authority"]["pages"]
    page_expectations = {
        "lecture_root": (142548, 893683),
        "lecture_latex": (142578, 807138),
        "worksheet_root": (142638, 1010985),
        "worksheet_latex": (142668, 807107),
    }
    for name, (pageid, revid) in page_expectations.items():
        if pages[name].get("pageid") != pageid or pages[name].get("revid") != revid:
            raise RuntimeError(f"Unit 4 authority identity changed: {name}")
    for owner, source_key in (("lecture", "u04_lecture_source"), ("worksheet", "u04_worksheet_source")):
        if authority["expansions"][owner]["sanitized_source"] != file_binding(paths[source_key], root):
            raise RuntimeError(f"Unit 4 {owner} source drifted from authority")

    translation_specs = [
        ("lecture", "o011-brenner-u04-l04", "u04_lecture_source", "u04_lecture_target", "u04_lecture_receipt", "o011-artifact-u04-l04-tex"),
        ("worksheet", "o011-brenner-u04-w04", "u04_worksheet_source", "u04_worksheet_target", "u04_worksheet_receipt", "o011-artifact-u04-w04-tex"),
        ("solution07", "o011-brenner-u04-w04-e007-solution", "u04_solution07_source", "u04_solution07_target", "u04_solution07_receipt", "o011-artifact-u04-w04-e007-solution-tex"),
        ("solution10", "o011-brenner-u04-w04-e010-solution", "u04_solution10_source", "u04_solution10_target", "u04_solution10_receipt", "o011-artifact-u04-w04-e010-solution-tex"),
    ]
    receipts: dict[str, dict[str, Any]] = {}
    for name, _target_id, source_key, target_key, receipt_key, _artifact_id in translation_specs:
        receipt = load_json(raw, receipt_key)
        receipts[name] = receipt
        expected_source = repository_path(paths[source_key], root)
        expected_target = repository_path(paths[target_key], root)
        if (
            receipt.get("status") != "pass"
            or receipt.get("source") != expected_source
            or receipt.get("source_bytes") != len(raw[source_key])
            or receipt.get("source_sha256") != digest(raw[source_key])
            or receipt.get("target") != expected_target
            or receipt.get("target_bytes") != len(raw[target_key])
            or receipt.get("target_sha256") != digest(raw[target_key])
            or not all(receipt.get("checks", {}).values())
        ):
            raise RuntimeError(f"stale or failed Unit 4 translation receipt: {name}")

    lecture_source = raw["u04_lecture_source"].decode("utf-8")
    lecture_target = raw["u04_lecture_target"].decode("utf-8")
    worksheet_source = raw["u04_worksheet_source"].decode("utf-8")
    worksheet_target = raw["u04_worksheet_target"].decode("utf-8")
    lecture_source_parts = slices(lecture_source, LECTURE_MARKER)
    lecture_target_parts = slices(lecture_target, LECTURE_MARKER)
    worksheet_source_parts = slices(worksheet_source, EXERCISE_MARKER)
    worksheet_target_parts = slices(worksheet_target, EXERCISE_MARKER)
    if len(lecture_source_parts) != 1 or len(lecture_target_parts) != 1:
        raise RuntimeError("Unit 4 lecture must have exactly one section")
    if len(worksheet_source_parts) != 15 or len(worksheet_target_parts) != 15:
        raise RuntimeError("Unit 4 worksheet must have exactly fifteen exercises")
    title_match = re.search(r"\\zwischenueberschrift\s*\{([^{}]+)\}", lecture_target)
    if not title_match:
        raise RuntimeError("Unit 4 Indonesian lecture title is missing")
    unit_title = title_match.group(1).strip()

    correction_names = tuple(f"O011-CORR-{number:04d}" for number in CORRECTION_NUMBERS)
    adverse_rows = {
        row["id"]: row
        for row in csv.DictReader(io.StringIO(raw["adverse"].decode("utf-8-sig")))
        if row.get("id") in correction_names
    }
    if set(adverse_rows) != set(correction_names):
        raise RuntimeError("Unit 4 correction ledger closure changed")

    correction_manifests: dict[str, dict[str, object]] = {}
    protected_by_id: dict[str, list[dict[str, object]]] = {name: [] for name in correction_names}
    for owner, key in CORRECTION_MANIFESTS.items():
        manifest = load_json(raw, key)
        expected_scope = {
            "lecture": "source/units/unit-04/lecture04.id.tex",
            "worksheet": "source/units/unit-04/worksheet04.id.tex",
            "solution07": "source/units/unit-04/worksheet04_exercise07_solution.id.tex",
            "solution10": "source/units/unit-04/worksheet04_exercise10_solution.id.tex",
        }[owner]
        if manifest.get("scope") != expected_scope:
            raise RuntimeError(f"wrong Unit 4 correction-manifest scope: {owner}")
        binding = file_binding(paths[key], root)
        correction_manifests[owner] = binding
        for evidence_class, field in (("protected_delta", "allowed_deltas"), ("evidence_only_delta", "evidence_only_deltas")):
            for delta in manifest.get(field) or []:
                names = [item for item in str(delta.get("correction_id", "")).split("+") if item]
                if not names or any(name not in protected_by_id for name in names):
                    raise RuntimeError(f"unknown correction in Unit 4 {owner} manifest")
                for name in names:
                    protected_by_id[name].append({
                        "evidence_class": evidence_class,
                        "manifest_path": binding["path"],
                        "manifest_sha256": binding["sha256"],
                        **delta,
                    })
    if not protected_by_id["O011-CORR-0042"] or not any(
        delta.get("evidence_class") == "evidence_only_delta"
        and delta.get("surface") == "command:mathl"
        and delta.get("occurrence_index") == 6
        for delta in protected_by_id["O011-CORR-0042"]
    ):
        raise RuntimeError("O011-CORR-0042 exact evidence-only binding is absent")
    if not receipts["lecture"].get("checks", {}).get("evidence_only_deltas_verified"):
        raise RuntimeError("lecture receipt does not verify evidence-only deltas")
    if protected_by_id["O011-CORR-0044"] or protected_by_id["O011-CORR-0045"]:
        raise RuntimeError("C1-to-C2 prose corrections unexpectedly claim protected deltas")

    lecture_review = raw["u04_lecture_math_review"].decode("utf-8")
    worksheet_review = raw["u04_worksheet_math_review"].decode("utf-8")
    final_math_audit = raw["u04_final_math_audit"].decode("utf-8")
    visual_review = raw["u04_visual_receipt"].decode("utf-8")
    if "Status: **PASS" not in lecture_review or any(name not in lecture_review for name in correction_names[3:6]):
        raise RuntimeError("Unit 4 lecture mathematical review is incomplete")
    if "No unresolved P1, P2, or P3" not in worksheet_review or any(
        name not in worksheet_review for name in (
            "O011-CORR-0038", "O011-CORR-0039", "O011-CORR-0040",
            "O011-CORR-0044", "O011-CORR-0045",
        )
    ):
        raise RuntimeError("Unit 4 worksheet mathematical review is incomplete")
    if "Status: **PASS" not in visual_review:
        raise RuntimeError("Unit 4 visual review lacks a PASS verdict")
    if "**Verdict: PASS.**" not in final_math_audit or any(
        name not in final_math_audit for name in correction_names
    ):
        raise RuntimeError("Unit 4 final mathematical audit is incomplete")
    for key in (
        "u04_lecture_source", "u04_lecture_target", "u04_worksheet_source",
        "u04_worksheet_target", "u04_solution07_source", "u04_solution07_target",
        "u04_solution10_source", "u04_solution10_target", "adverse",
        "u04_lecture_corrections", "u04_worksheet_corrections",
        "u04_solution07_corrections", "u04_solution10_corrections",
    ):
        if digest(raw[key]) not in final_math_audit:
            raise RuntimeError(f"Unit 4 final mathematical audit lacks current hash: {key}")

    pdf_binding = file_binding(paths["u04_reader_pdf"], root)
    if build_receipt.get("output") != pdf_binding:
        raise RuntimeError("Unit 4 build receipt does not bind the cumulative PDF")
    cycles = build_receipt.get("cycles") or []
    if len(cycles) != 2 or any(
        cycle.get("bytes") != pdf_binding["bytes"] or cycle.get("sha256") != pdf_binding["sha256"]
        for cycle in cycles
    ):
        raise RuntimeError("Unit 4 build is not two-cycle byte reproducible")
    if (
        structural_receipt.get("passed") is not True
        or structural_receipt.get("pdf") != {
            **structural_receipt.get("pdf", {}),
            "path": pdf_binding["path"],
            "bytes": pdf_binding["bytes"],
            "sha256": pdf_binding["sha256"],
        }
        or structural_receipt.get("pdf", {}).get("pages") != 72
    ):
        raise RuntimeError("Unit 4 structural PDF receipt is stale or failed")
    if str(pdf_binding["sha256"]) not in visual_review or str(pdf_binding["bytes"]) not in visual_review.replace(",", ""):
        raise RuntimeError("Unit 4 visual receipt is not bound to the cumulative PDF")

    terminology_rows = {
        row["id"].lower(): row
        for row in csv.DictReader(io.StringIO(raw["terminology"].decode("utf-8-sig")))
    }
    term_ids = [f"o011-term-{number:04d}" for number in TERM_NUMBERS]
    if any(term_id not in terminology_rows or terminology_rows[term_id].get("status") != "admitted" for term_id in term_ids):
        raise RuntimeError("Unit 4 terminology closure is not admitted")

    unit_id = "o011-brenner-u04"
    lecture_id = "o011-brenner-u04-l04"
    worksheet_id = "o011-brenner-u04-w04"
    resource_id = "o011-resource-brenner-dg2023"
    edition_id = "o011-edition-brenner-current-20260821"
    text_rights_id = "o011-rights-brenner-text"
    official_rights_id = "o011-rights-u04-official-pdf-witness"
    if not {resource_id, edition_id, text_rights_id, "o011-course-d50"}.issubset(baseline_ids):
        raise RuntimeError("Unit 4 parent/resource/rights baseline IDs are absent")

    added: list[dict[str, object]] = []
    added.append(base(
        unit_id, "unit", timestamp,
        parent_id="o011-course-d50", order=4, path="source/units/unit-04",
        resource_id=resource_id, edition_id=edition_id,
        source_local_id="Vorlesung 4 + Arbeitsblatt 4",
        title=unit_title, unit_kind="lecture_worksheet_pair",
        authority_receipt="qa/unit-04/AUTHORITY_PREFLIGHT.json",
        authority_receipt_sha256=digest(raw["u04_authority"]),
        authority_verification_sha256=digest(raw["u04_authority_verify"]),
        current_revision_receipt_sha256=digest(raw["u04_current_revision"]),
        language="Indonesian", locale="id-ID",
        translation_state=args.translation_state,
        rights_component_id=text_rights_id,
    ))
    added.append(base(
        lecture_id, "unit", timestamp,
        parent_id=unit_id, order=1,
        path=repository_path(paths["u04_lecture_target"], root),
        resource_id=resource_id, edition_id=edition_id,
        source_local_id="pageid:142548/revid:893683",
        source_locator=pages["lecture_root"]["title"],
        root_pageid=142548, root_revid=893683,
        latex_pageid=142578, latex_revid=807138,
        source_sha256=digest(raw["u04_lecture_source"]),
        target_sha256=digest(raw["u04_lecture_target"]),
        language="Indonesian", locale="id-ID",
        translation_state=args.translation_state,
        rights_component_id=text_rights_id, unit_kind="lecture",
    ))
    added.append(base(
        worksheet_id, "unit", timestamp,
        parent_id=unit_id, order=2,
        path=repository_path(paths["u04_worksheet_target"], root),
        resource_id=resource_id, edition_id=edition_id,
        source_local_id="pageid:142638/revid:1010985",
        source_locator=pages["worksheet_root"]["title"],
        root_pageid=142638, root_revid=1010985,
        latex_pageid=142668, latex_revid=807107,
        source_sha256=digest(raw["u04_worksheet_source"]),
        target_sha256=digest(raw["u04_worksheet_target"]),
        language="Indonesian", locale="id-ID",
        translation_state=args.translation_state,
        rights_component_id=text_rights_id, unit_kind="worksheet",
        exercise_count=15, supplied_solution_indices=list(SOLUTION_INDICES),
        all_hint_fields_blank=True, graded_point_values=[4, 5, 4, 6],
        graded_point_total=19,
    ))
    added.append(base(
        f"{lecture_id}-s01", "segment", timestamp,
        parent_id=lecture_id, order=1,
        path="source/units/unit-04/lecture04.id.tex#section-1",
        resource_id=resource_id, edition_id=edition_id,
        source_local_id="lecture04:section:1",
        source_locator=f"{pages['lecture_root']['title']}#section-1",
        source_sha256=digest(lecture_source_parts[0].encode("utf-8")),
        target_sha256=digest(lecture_target_parts[0].encode("utf-8")),
        language="Indonesian", locale="id-ID",
        translation_state=args.translation_state,
        rights_component_id=text_rights_id, segment_kind="lecture_section",
    ))

    for row, source_part, target_part in zip(exercises, worksheet_source_parts, worksheet_target_parts):
        index = int(row["exercise_index"])
        exercise_id = f"{worksheet_id}-e{index:03d}"
        added.append(base(
            exercise_id, "unit", timestamp,
            parent_id=worksheet_id, order=index,
            path=f"source/units/unit-04/worksheet04.id.tex#exercise-{index}",
            resource_id=resource_id, edition_id=edition_id,
            source_local_id=f"worksheet04:exercise:{index}",
            source_locator=f"{pages['worksheet_root']['title']}#exercise-{index}",
            authority_task_title=row["task_title"],
            source_display_id=f"4.{index}",
            source_sha256=digest(source_part.encode("utf-8")),
            target_sha256=digest(target_part.encode("utf-8")),
            language="Indonesian", locale="id-ID",
            translation_state=args.translation_state,
            rights_component_id=text_rights_id, unit_kind="exercise",
            graded=row.get("point_value") is not None,
            point_value=row.get("point_value"), hint_present=False,
            has_authority_solution=bool(row.get("exists")),
        ))

    solution_rows = {int(row["exercise_index"]): row for row in exercises if row.get("exists")}
    for index in SOLUTION_INDICES:
        row = solution_rows[index]
        source_key = f"u04_solution{index:02d}_source"
        target_key = f"u04_solution{index:02d}_target"
        added.append(base(
            f"{worksheet_id}-e{index:03d}-solution", "unit", timestamp,
            parent_id=f"{worksheet_id}-e{index:03d}", order=1,
            path=repository_path(paths[target_key], root),
            resource_id=resource_id, edition_id=edition_id,
            source_local_id=f"pageid:{row['pageid']}/revid:{row['revid']}",
            source_locator=row["solution_title"], source_display_id=f"4.{index}",
            authority_wikitext_sha256=row["source_utf8_sha256"],
            source_revision_timestamp=row["timestamp"],
            source_sha256=digest(raw[source_key]), target_sha256=digest(raw[target_key]),
            language="Indonesian", locale="id-ID",
            translation_state=args.translation_state,
            rights_component_id=text_rights_id, unit_kind="solution",
        ))

    concept_ids: list[str] = []
    for slug, source_label, target_label in CONCEPTS:
        concept_id = f"o011-concept-{slug}"
        concept_ids.append(concept_id)
        added.append(base(
            concept_id, "concept", timestamp,
            parent_id="o011-course-d50", source_local_id=source_label,
            labels={"de": source_label, "id-ID": target_label},
            language=None, locale=None,
        ))

    for term_id in term_ids:
        row = terminology_rows[term_id]
        added.append(base(
            term_id, "term", timestamp,
            parent_id="o011-course-d50", order=int(term_id.rsplit("-", 1)[1]),
            source_local_id=row["source_de"],
            labels={"de": row["source_de"], "id-ID": row["target_id"]},
            terminology_status=row["status"], note=row.get("note") or "",
            terminology_ledger_path="00_control/TERMINOLOGY.csv",
            terminology_ledger_sha256=digest(raw["terminology"]),
            language=None, locale=None,
        ))

    added.append(base(
        official_rights_id, "rights", timestamp,
        source_local_id="Commons pageid:130922930/revid:1003382720",
        component_scope="authority/pdf/lecture04_commons_revid1003382720.pdf",
        attribution="Holger Brenner alias Bocardodarapti; Commons artist User:Bocardodarapti",
        license="unresolved file-specific version signal",
        license_url=None,
        license_signals={
            "commons_structured_metadata": "CC BY-SA 4.0",
            "internal_page_9": "CC BY-SA 3.0",
        },
        rights_status="withheld_pending_resolution",
        redistribution_permitted=False, release_asset=False,
        evidence_path="qa/unit-04/OFFICIAL_PDF_WITNESS.json",
        evidence_sha256=digest(raw["u04_official_pdf_witness"]),
    ))

    artifact_ids: list[str] = []
    for _name, target_id, source_key, target_key, _receipt_key, artifact_id in translation_specs:
        artifact_ids.append(artifact_id)
        added.append(base(
            artifact_id, "artifact", timestamp,
            parent_id=target_id, path=repository_path(paths[target_key], root),
            source_sha256=digest(raw[source_key]), target_sha256=digest(raw[target_key]),
            language="Indonesian", locale="id-ID",
            translation_state=args.translation_state,
            rights_component_id=text_rights_id,
            component_rights_ids=[text_rights_id],
            artifact_kind="translated_tex_fragment", media_type="application/x-tex",
            bytes=len(raw[target_key]),
        ))

    baseline_by_id = {str(record["id"]): record for record in baseline_records}
    cumulative_rights = list(baseline_by_id["o011-artifact-through-unit03-pdf"]["component_rights_ids"])
    pdf_artifact_id = "o011-artifact-through-unit04-pdf"
    artifact_ids.append(pdf_artifact_id)
    added.append(base(
        pdf_artifact_id, "artifact", timestamp,
        parent_id=unit_id, path=str(pdf_binding["path"]),
        target_sha256=str(pdf_binding["sha256"]), bytes=int(pdf_binding["bytes"]),
        language="Indonesian", locale="id-ID", translation_state="visually_checked",
        component_rights_ids=cumulative_rights,
        artifact_kind="cumulative_reader_pdf", media_type="application/pdf",
        build_receipt_path="qa/unit-04/build.json",
        build_receipt_sha256=digest(raw["u04_build_receipt"]),
        clean_cycle_count=2, deterministic_clean_cycles=True,
        coverage_unit_ids=["o011-brenner-u01", "o011-brenner-u02", "o011-brenner-u03", unit_id],
        zero_unit04_media=True,
    ))
    official_artifact_id = "o011-artifact-u04-official-pdf-witness"
    artifact_ids.append(official_artifact_id)
    added.append(base(
        official_artifact_id, "artifact", timestamp,
        parent_id=lecture_id, path=repository_path(paths["u04_official_pdf"], root),
        target_sha256=digest(raw["u04_official_pdf"]), bytes=len(raw["u04_official_pdf"]),
        language="German", locale="de-DE", translation_state="source_frozen",
        rights_component_id=official_rights_id,
        component_rights_ids=[official_rights_id],
        artifact_kind="authority_render_witness_pdf", media_type="application/pdf",
        production_master=False, release_asset=False,
        redistribution_status=official_witness["redistribution_status"],
        witness_receipt_path="qa/unit-04/OFFICIAL_PDF_WITNESS.json",
        witness_receipt_sha256=digest(raw["u04_official_pdf_witness"]),
    ))

    qa_specs: list[dict[str, object]] = [
        {"id": "o011-qa-unit04-authority-preflight", "target_id": unit_id, "receipt_key": "u04_authority", "qa_kind": "authority_source_solution_media_closure", "result": "pass", "state": "source_frozen", "values": {"lecture_section_count": 1, "worksheet_exercise_count": 15, "supplied_solution_indices": [7, 10], "asset_ids": [], "component_rights_ids": []}},
        {"id": "o011-qa-unit04-authority-verification", "target_id": unit_id, "receipt_key": "u04_authority_verify", "qa_kind": "offline_authority_hash_and_closure_verification", "result": "pass", "state": "source_frozen"},
        {"id": "o011-qa-unit04-current-revision", "target_id": unit_id, "receipt_key": "u04_current_revision", "qa_kind": "live_current_revision_check", "result": "pass", "state": "source_frozen", "values": {"surface_count": 4}},
        {"id": "o011-qa-unit04-solution-closure", "target_id": worksheet_id, "receipt_key": "u04_solution_closure", "qa_kind": "solution_hint_and_points_closure", "result": "pass", "state": "source_frozen", "values": {"exercise_count": 15, "supplied_solution_indices": [7, 10], "missing_solution_count": 13, "all_hint_fields_blank": True, "graded_point_values": [4, 5, 4, 6], "graded_point_total": 19}},
        {"id": "o011-qa-unit04-media-authority-closure", "target_id": unit_id, "receipt_key": "u04_media_closure", "qa_kind": "zero_media_authority_closure", "result": "pass", "state": "source_frozen", "values": {"asset_ids": [], "source_count": 0, "derivative_count": 0}},
        {"id": "o011-qa-unit04-media-build-closure", "target_id": unit_id, "receipt_key": "u04_media_receipt", "qa_kind": "zero_media_build_and_rights_closure", "result": "pass", "state": "structurally_verified", "values": {"asset_ids": [], "source_count": 0, "derivative_count": 0}},
        {"id": "o011-qa-unit04-authority-anomalies", "target_id": unit_id, "receipt_key": "u04_authority_anomalies", "qa_kind": "authority_anomaly_census", "result": "admitted_limitation", "state": "source_frozen", "values": {"anomaly_group_count": 6, "correction_ids": list(correction_names)}},
        {"id": "o011-qa-unit04-official-pdf-witness", "target_id": official_artifact_id, "artifact_id": official_artifact_id, "receipt_key": "u04_official_pdf_witness", "qa_kind": "official_pdf_identity_and_rights_disposition", "result": "admitted_limitation", "state": "source_frozen", "target_sha256": digest(raw["u04_official_pdf"]), "values": {"release_asset": False, "production_master": False, "redistribution_status": official_witness["redistribution_status"]}},
        {"id": "o011-qa-unit04-official-pdf-structural-visual", "target_id": official_artifact_id, "artifact_id": official_artifact_id, "receipt_key": "u04_official_pdf_qa", "qa_kind": "official_pdf_structural_visual_witness", "result": "admitted_limitation", "state": "source_frozen", "target_sha256": digest(raw["u04_official_pdf"]), "values": {"pages": 9, "blank_pages": [8], "rights_index_pages": [9], "release_asset": False}},
        {"id": "o011-qa-unit04-lecture-math-review", "target_id": lecture_id, "artifact_id": "o011-artifact-u04-l04-tex", "receipt_key": "u04_lecture_math_review", "qa_kind": "independent_translation_and_mathematical_review", "result": "pass", "state": "mathematically_reviewed", "target_sha256": digest(raw["u04_lecture_target"]), "values": {"correction_ids": ["O011-CORR-0041", "O011-CORR-0042", "O011-CORR-0043"], "remaining_p1_p2_p3_findings": 0}},
        {"id": "o011-qa-unit04-worksheet-math-review", "target_id": worksheet_id, "artifact_id": "o011-artifact-u04-w04-tex", "receipt_key": "u04_worksheet_math_review", "qa_kind": "independent_worksheet_and_solution_mathematical_review", "result": "pass", "state": "mathematically_reviewed", "target_sha256": digest(raw["u04_worksheet_target"]), "values": {"artifact_ids": ["o011-artifact-u04-w04-tex", "o011-artifact-u04-w04-e007-solution-tex", "o011-artifact-u04-w04-e010-solution-tex"], "correction_ids": ["O011-CORR-0038", "O011-CORR-0039", "O011-CORR-0040", "O011-CORR-0044", "O011-CORR-0045"], "remaining_p1_p2_p3_findings": 0}},
        {"id": "o011-qa-unit04-final-math-audit", "target_id": unit_id, "artifact_id": pdf_artifact_id, "receipt_key": "u04_final_math_audit", "qa_kind": "independent_post_repair_mathematical_and_topology_audit", "result": "pass", "state": "mathematically_reviewed", "target_sha256": str(pdf_binding["sha256"]), "values": {"audited_artifact_ids": ["o011-artifact-u04-l04-tex", "o011-artifact-u04-w04-tex", "o011-artifact-u04-w04-e007-solution-tex", "o011-artifact-u04-w04-e010-solution-tex"], "correction_ids": list(correction_names), "remaining_p1_p2_p3_findings": 0}},
        {"id": "o011-qa-through-unit04-pdf-reproducibility", "target_id": pdf_artifact_id, "artifact_id": pdf_artifact_id, "receipt_key": "u04_build_receipt", "qa_kind": "reproducible_pdf_build", "result": "pass", "state": "built", "target_sha256": str(pdf_binding["sha256"]), "values": {"engine": build_receipt["engine"], "clean_cycle_count": 2, "pass_count_per_cycle": 3, "deterministic_clean_cycles": True, "artifact_bytes": int(pdf_binding["bytes"])}},
        {"id": "o011-qa-through-unit04-pdf-structural", "target_id": pdf_artifact_id, "artifact_id": pdf_artifact_id, "receipt_key": "u04_structural_receipt", "qa_kind": "pdf_structure_accessibility_links_and_safety", "result": "pass", "state": "visually_checked", "target_sha256": str(pdf_binding["sha256"]), "values": {"page_count": 72, "catalog_language": "id-ID", "tagged": False, "fonts_with_tounicode": 29, "limitations": structural_receipt.get("limitations")}},
        {"id": "o011-qa-through-unit04-pdf-visual", "target_id": pdf_artifact_id, "artifact_id": pdf_artifact_id, "receipt_key": "u04_visual_receipt", "qa_kind": "pdf_visual_inspection", "result": "pass", "state": "visually_checked", "target_sha256": str(pdf_binding["sha256"]), "values": {"page_count": 72, "all_pages_inspected": True, "new_unit_pages_inspected": [58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69]}},
    ]
    for name, target_id, source_key, target_key, receipt_key, artifact_id in translation_specs:
        receipt = receipts[name]
        qa_specs.append({
            "id": f"o011-qa-unit04-{name}-translation",
            "target_id": target_id, "artifact_id": artifact_id,
            "receipt_key": receipt_key, "qa_kind": "translation_structure",
            "result": "pass", "state": args.translation_state,
            "source_sha256": digest(raw[source_key]),
            "target_sha256": digest(raw[target_key]),
            "values": {
                "checks": receipt["checks"], "counts": receipt["counts"],
                "declared_corrections": receipt.get("declared_corrections") or [],
            },
        })

    qa_ids: list[str] = []
    for spec in qa_specs:
        qa_id = str(spec["id"])
        qa_ids.append(qa_id)
        receipt_key = str(spec["receipt_key"])
        state = str(spec["state"])
        values: dict[str, object] = {
            "parent_id": unit_id,
            "target_id": spec["target_id"],
            "receipt_path": repository_path(paths[receipt_key], root),
            "evidence_sha256": digest(raw[receipt_key]),
            "language": "Indonesian" if state not in {"source_frozen"} else None,
            "locale": "id-ID" if state not in {"source_frozen"} else None,
            "translation_state": state,
            "qa_kind": spec["qa_kind"],
            "result": spec["result"],
            **dict(spec.get("values") or {}),
        }
        for optional in ("artifact_id", "source_sha256", "target_sha256"):
            if spec.get(optional) is not None:
                values[optional] = spec[optional]
        added.append(base(qa_id, "qa_event", timestamp, **values))

    for correction_name in correction_names:
        row = adverse_rows[correction_name]
        owner, index = CORRECTION_TARGETS[correction_name]
        if owner == "lecture":
            target_id = lecture_id
            target_key = "u04_lecture_target"
            receipt_key = "u04_lecture_receipt"
            math_key = "u04_final_math_audit"
            manifest_owner = "lecture"
        elif owner == "solution":
            assert index in SOLUTION_INDICES
            target_id = f"{worksheet_id}-e{index:03d}-solution"
            target_key = f"u04_solution{index:02d}_target"
            receipt_key = f"u04_solution{index:02d}_receipt"
            math_key = "u04_final_math_audit"
            manifest_owner = f"solution{index:02d}"
        else:
            assert index is not None
            target_id = f"{worksheet_id}-e{index:03d}"
            target_key = "u04_worksheet_target"
            receipt_key = "u04_worksheet_receipt"
            math_key = "u04_final_math_audit"
            manifest_owner = "worksheet" if correction_name == "O011-CORR-0038" else None
        deltas = protected_by_id[correction_name]
        manifest_binding = correction_manifests[manifest_owner] if manifest_owner else None
        if bool(deltas) != bool(manifest_binding):
            raise RuntimeError(f"correction-manifest binding mismatch: {correction_name}")
        correction_id = correction_name.lower()
        added.append(base(
            correction_id, "correction", timestamp,
            source_local_id=row["surface"], severity=row["severity"],
            correction_status=row["status"], description=row["description"],
            disposition=row["disposition"],
            upstream_report_disposition="deferred_until_full_corpus",
            ledger_path="00_control/ADVERSE_LEDGER.csv",
            ledger_sha256=digest(raw["adverse"]),
            protected_deltas=deltas, correction_manifest=manifest_binding,
            target_binding={
                "path": repository_path(paths[target_key], root),
                "bytes": len(raw[target_key]), "sha256": digest(raw[target_key]),
                "receipt_path": repository_path(paths[receipt_key], root),
                "receipt_sha256": digest(raw[receipt_key]),
            },
            reader_binding={
                **pdf_binding,
                "build_receipt_path": "qa/unit-04/build.json",
                "build_receipt_sha256": digest(raw["u04_build_receipt"]),
                "structural_receipt_path": "qa/unit-04/STRUCTURAL_QA.json",
                "structural_receipt_sha256": digest(raw["u04_structural_receipt"]),
                "visual_receipt_path": "qa/unit-04/VISUAL_QA.md",
                "visual_receipt_sha256": digest(raw["u04_visual_receipt"]),
                "math_audit_path": repository_path(paths[math_key], root),
                "math_audit_sha256": digest(raw[math_key]),
            },
        ))

    def add_relation(relation_id: str, relation_type: str, from_id: str, to_id: str) -> None:
        added.append(base(
            relation_id, "relation", timestamp,
            relation_type=relation_type, from_id=from_id, to_id=to_id,
        ))

    for concept_id in concept_ids:
        add_relation(
            f"o011-rel-u04-l04-s01-covers-{concept_id.removeprefix('o011-concept-')}",
            "covers", f"{lecture_id}-s01", concept_id,
        )
    for term_id in term_ids:
        add_relation(
            f"o011-rel-u04-uses-{term_id.removeprefix('o011-')}",
            "uses_term", unit_id, term_id,
        )
    for index in range(2, 16):
        add_relation(
            f"o011-rel-u04-w04-e{index - 1:03d}-precedes-e{index:03d}",
            "precedes", f"{worksheet_id}-e{index - 1:03d}", f"{worksheet_id}-e{index:03d}",
        )
    for index in SOLUTION_INDICES:
        add_relation(
            f"o011-rel-u04-w04-e{index:03d}-solution-solves-e{index:03d}",
            "solves", f"{worksheet_id}-e{index:03d}-solution", f"{worksheet_id}-e{index:03d}",
        )
    for _name, target_id, _source_key, _target_key, _receipt_key, artifact_id in translation_specs:
        add_relation(
            f"o011-rel-{artifact_id.removeprefix('o011-')}-represents-{target_id.removeprefix('o011-')}",
            "represents", artifact_id, target_id,
        )
    for spec in qa_specs:
        qa_id = str(spec["id"])
        target_id = str(spec["target_id"])
        add_relation(
            f"o011-rel-{qa_id.removeprefix('o011-')}-verifies-{target_id.removeprefix('o011-')}",
            "verifies", qa_id, target_id,
        )
    add_relation(
        "o011-rel-artifact-through-unit04-pdf-represents-u04-checkpoint",
        "represents", pdf_artifact_id, unit_id,
    )
    add_relation(
        "o011-rel-artifact-through-unit04-pdf-extends-through-unit03-pdf",
        "extends", pdf_artifact_id, "o011-artifact-through-unit03-pdf",
    )
    add_relation(
        "o011-rel-artifact-u04-official-pdf-witness-witnesses-brenner-u04-l04",
        "witnesses", official_artifact_id, lecture_id,
    )
    add_relation(
        "o011-rel-rights-u04-official-pdf-witness-governs-artifact-u04-official-pdf-witness",
        "governs", official_rights_id, official_artifact_id,
    )
    add_relation("o011-rel-u03-precedes-u04", "precedes", "o011-brenner-u03", unit_id)
    for correction_name, (owner, index) in CORRECTION_TARGETS.items():
        correction_id = correction_name.lower()
        if owner == "lecture":
            target_id = lecture_id
        elif owner == "solution":
            assert index is not None
            target_id = f"{worksheet_id}-e{index:03d}-solution"
        else:
            assert index is not None
            target_id = f"{worksheet_id}-e{index:03d}"
        add_relation(
            f"o011-rel-{correction_id.removeprefix('o011-')}-corrects-{target_id.removeprefix('o011-')}",
            "corrects", correction_id, target_id,
        )

    for child in list(added):
        parent_id = child.get("parent_id")
        if parent_id and child.get("entity_type") not in {"relation", "rights", "correction"}:
            child_id = str(child["id"])
            add_relation(
                f"o011-rel-contains-{child_id.removeprefix('o011-')}",
                "contains", str(parent_id), child_id,
            )

    collisions = sorted(str(record["id"]) for record in added if str(record["id"]) in baseline_ids)
    if collisions:
        raise RuntimeError(f"Unit 4 stable IDs collide with the 591-record baseline: {collisions}")
    added.sort(key=lambda record: str(record["id"]))
    records = [*baseline_records, *added]
    validate(records, schema)

    jsonl_suffix = "".join(canonical_json(record) + "\n" for record in added).encode("utf-8")
    jsonl_bytes = baseline_jsonl + jsonl_suffix
    if jsonl_bytes[:BASELINE_JSONL_BYTES] != baseline_jsonl:
        raise RuntimeError("591-record JSONL prefix changed")
    assert_public_safe("records.jsonl", jsonl_bytes)

    csv_buffer = io.StringIO(newline="")
    writer = csv.DictWriter(csv_buffer, fieldnames=COMMON, lineterminator="\n")
    for record in added:
        writer.writerow({field: record.get(field) for field in COMMON})
    csv_bytes = baseline_csv + csv_buffer.getvalue().encode("utf-8")
    if csv_bytes[:BASELINE_CSV_BYTES] != baseline_csv:
        raise RuntimeError("591-row CSV prefix changed")
    csv_rows = list(csv.DictReader(io.StringIO(csv_bytes.decode("utf-8"))))
    if len(csv_rows) != len(records):
        raise RuntimeError("CSV and JSONL row counts differ")
    assert_public_safe("records.csv", csv_bytes)

    extension_counts = {kind: sum(record["entity_type"] == kind for record in added) for kind in sorted(ENTITY_TYPES)}
    cumulative_counts = {kind: sum(record["entity_type"] == kind for record in records) for kind in sorted(ENTITY_TYPES)}
    manifest = {
        "schema_version": 4,
        "generator": "scripts/export_backend_v4.py",
        "generator_sha256": digest(Path(__file__).read_bytes()),
        "timestamp": timestamp,
        "record_count": len(records),
        "entity_counts": cumulative_counts,
        "unit123_baseline_preservation": {
            "path": "backend/records.jsonl", "record_count": BASELINE_RECORD_COUNT,
            "bytes": len(baseline_jsonl), "sha256": digest(baseline_jsonl),
            "byte_identical_prefix": True,
            "csv_path": "backend/records.csv", "csv_bytes": len(baseline_csv),
            "csv_sha256": digest(baseline_csv), "csv_byte_identical_prefix": True,
        },
        "unit04_extension": {
            "record_count": len(added), "entity_counts": extension_counts,
            "translation_state": args.translation_state,
            "authority_receipt_sha256": digest(raw["u04_authority"]),
            "authority_verification_sha256": digest(raw["u04_authority_verify"]),
            "current_revision_receipt_sha256": digest(raw["u04_current_revision"]),
            "root_revision_ids": {"lecture": 893683, "worksheet": 1010985},
            "latex_revision_ids": {"lecture": 807138, "worksheet": 807107},
            "lecture_segment_count": 1, "exercise_count": 15,
            "practice_exercise_count": 11, "graded_exercise_count": 4,
            "graded_point_values": [4, 5, 4, 6], "graded_point_total": 19,
            "all_hint_fields_blank": True, "solution_indices": list(SOLUTION_INDICES),
            "zero_media": True, "asset_ids": [],
            "concept_ids": concept_ids, "term_ids": term_ids,
            "rights_ids": [official_rights_id],
            "correction_ids": list(correction_names),
            "artifact_ids": sorted(artifact_ids), "qa_event_ids": sorted(qa_ids),
            "target_hashes": {
                name: digest(raw[target_key])
                for name, _target_id, _source_key, target_key, _receipt_key, _artifact_id in translation_specs
            },
            "cumulative_pdf": pdf_binding,
            "cumulative_html": {"included": False, "path": None, "bytes": None, "sha256": None},
            "official_pdf_witness": {
                **file_binding(paths["u04_official_pdf"], root),
                "release_asset": False,
                "redistribution_status": official_witness["redistribution_status"],
            },
        },
        "inputs": {
            "unit123_baseline_jsonl": {"path": "backend/records.jsonl", "bytes": len(baseline_jsonl), "sha256": digest(baseline_jsonl)},
            "unit123_baseline_csv": {"path": "backend/records.csv", "bytes": len(baseline_csv), "sha256": digest(baseline_csv)},
            **{
                name: {"path": repository_path(paths[name], root), "bytes": len(raw[name]), "sha256": digest(raw[name])}
                for name in sorted(paths)
            },
        },
        "outputs": {
            "records.jsonl": {"bytes": len(jsonl_bytes), "sha256": digest(jsonl_bytes)},
            "records.csv": {"bytes": len(csv_bytes), "sha256": digest(csv_bytes)},
        },
        "safety_checks": {
            "unit123_jsonl_prefix_byte_identical": True,
            "unit123_csv_prefix_byte_identical": True,
            "absolute_machine_paths_absent": True,
            "common_credential_markers_absent": True,
            "unit04_authority_and_receipts_current": True,
            "unit04_correction_evidence_current": True,
            "unit04_zero_media_closed": True,
            "unit04_terms_admitted": True,
            "official_pdf_withheld_disposition_preserved": True,
            "html_included_only_if_present_and_verified": True,
        },
    }
    manifest_bytes = (json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    assert_public_safe("MANIFEST.json", manifest_bytes)

    jsonl_path.write_bytes(jsonl_bytes)
    csv_path.write_bytes(csv_bytes)
    (root / "backend/MANIFEST.json").write_bytes(manifest_bytes)


if __name__ == "__main__":
    main()
