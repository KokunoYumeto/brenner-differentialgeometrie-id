#!/usr/bin/env python3
"""Append a deterministic Unit 3 extension to the immutable Unit 1-2 backend.

This exporter is deliberately receipt-gated.  It refuses to alter generated
backend views until the complete Unit 3 authority, translation, media, build,
structural, visual, and mathematical evidence exists and binds the live files.
The first 357 JSONL records and first 357 CSV data rows are preserved byte for
byte.  Re-running with the same checkpoint discards any previous Unit 3 suffix
and recreates that suffix deterministically.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


SCHEMA = "o011-modular-backend"
SCHEMA_VERSION = 1
WORKFLOW = "o011-export-backend-v3"
BASELINE_RECORD_COUNT = 357
BASELINE_JSONL_BYTES = 215_317
BASELINE_JSONL_SHA256 = "a393d3ff6c8aed203e7d3690eb6391e22ea25436cd06e85aa40e1adc23adb122"
BASELINE_CSV_BYTES = 79_611
BASELINE_CSV_SHA256 = "5880fa9dee8bc0a73ed0e903d931fad38978bc2c9ef65cc58b62b48a7f26b7ba"
ENTITY_TYPES = {
    "program",
    "course",
    "resource",
    "edition",
    "unit",
    "concept",
    "segment",
    "term",
    "asset",
    "relation",
    "rights",
    "qa_event",
    "artifact",
    "correction",
}
COMMON = (
    "schema",
    "schema_version",
    "id",
    "entity_type",
    "source_local_id",
    "parent_id",
    "order",
    "path",
    "resource_id",
    "edition_id",
    "source_locator",
    "source_sha256",
    "target_sha256",
    "language",
    "locale",
    "translation_state",
    "rights_component_id",
    "status",
    "timestamp",
    "workflow",
    "supersedes",
)
LECTURE_MARKER = re.compile(r"(?m)^\s*\\zwischenueberschrift\s*\{")
EXERCISE_MARKER = re.compile(
    r"(?m)^\s*\\(?:inputaufgabegibtloesung|inputaufgabe)\b"
)
WINDOWS_ABSOLUTE = re.compile(r"(?i)(?<![a-z0-9+.-])[a-z]:[\\/]")
PUBLIC_SAFETY_MARKERS = (
    "\\users\\",
    "/users/",
    "\\appdata\\",
    "/home/",
    "github_pat_",
    "ghp_",
    "gho_",
    "ghu_",
    "ghs_",
    "ghr_",
    "glpat-",
    "sk-proj-",
    "xoxb-",
    "bearer ",
    "access_token",
    "api_key",
    "zenodo token",
)
SOLUTION_INDICES = (7, 16)
UNIT3_CORRECTION_RANGE = range(28, 38)
CORRECTION_MANIFEST_SPECS = (
    (
        "u03_worksheet_corrections",
        "source/units/unit-03/worksheet03.id.tex",
        "worksheet",
    ),
    (
        "u03_lecture_corrections",
        "source/units/unit-03/lecture03.id.tex",
        "lecture",
    ),
)

# The worksheet proposal is the explicit terminology intake surface.  The two
# arc-length terms already admitted in the durable ledger are also essential
# to the Unit 3 lecture.  Every row must be admitted in TERMINOLOGY.csv before
# export; proposed vocabulary never leaks into the public backend as settled.
UNIT3_TERMS = {
    "Bogenparametrisierung": "parametrisasi panjang busur",
    "bogenparametrisiert": "berparametrisasi panjang busur",
    "Krümmung": "kelengkungan",
    "Drehung": "rotasi",
    "Krümmungskreis": "lingkaran kelengkungan",
    "Kreisbewegung": "gerak melingkar",
    "uniforme Kreisbewegung": "gerak melingkar beraturan",
    "Geschwindigkeitsnorm": "norma kecepatan",
    "Beschleunigung": "percepatan",
    "Klothoide": "klotoid",
    "logarithmische Spirale": "spiral logaritmik",
    "archimedische Spirale": "spiral Archimedes",
    "analytisch": "analitik",
    "Potenzreihe": "deret pangkat",
    "Evolute": "evolut",
    "Gradientenfeld": "medan gradien",
    "totales Differential": "diferensial total",
    "tangentialer Vektor": "vektor tangen",
    "regulär": "reguler",
    "Tangente": "garis tangen",
}

CONCEPTS = (
    (
        "arc-length-parametrization",
        "Bogenparametrisierung",
        "parametrisasi panjang busur",
    ),
    ("planar-signed-curvature", "Krümmung", "kelengkungan bertanda"),
    ("curvature-circle", "Krümmungskreis", "lingkaran kelengkungan"),
    ("evolute", "Evolute", "evolut"),
    (
        "general-curve-curvature",
        "Krümmung allgemeiner Kurven",
        "kelengkungan kurva umum",
    ),
)

MEDIA_SPECS = (
    (1, "Parabola circle.svg", "u03_media_parabola", "parabola-circle-svg", "lecture"),
    (2, "Euler spiral.svg", "u03_media_euler", "euler-spiral-svg", "worksheet"),
    (3, "Evolute-parab.svg", "u03_media_evolute", "evolute-parab-svg", "worksheet"),
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def repository_path(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def base(
    record_id: str, entity_type: str, timestamp: str, **values: object
) -> dict[str, object]:
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
        text[
            match.start() : (
                matches[index + 1].start() if index + 1 < len(matches) else len(text)
            )
        ]
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
            field
            for field in (
                "schema",
                "schema_version",
                "id",
                "entity_type",
                "status",
                "timestamp",
                "workflow",
                "supersedes",
            )
            if field not in record
        ]
        if missing:
            raise RuntimeError(f"missing common fields in {record.get('id')}: {missing}")
        if record["schema"] != SCHEMA or record["schema_version"] != SCHEMA_VERSION:
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
            "parent_id",
            "resource_id",
            "edition_id",
            "rights_component_id",
            "target_id",
            "artifact_id",
        ):
            value = record.get(field)
            if value is not None and value not in identifiers:
                raise RuntimeError(f"unresolved {field}={value!r} in {record['id']}")
        for value in record.get("component_rights_ids") or []:
            if value not in identifiers:
                raise RuntimeError(
                    f"unresolved component right {value!r} in {record['id']}"
                )
        if record["entity_type"] == "relation":
            for field in ("from_id", "to_id"):
                if record.get(field) not in identifiers:
                    raise RuntimeError(f"unresolved {field} in {record['id']}")
        for field in ("path", "receipt_path", "build_receipt_path", "ledger_path"):
            value = record.get(field)
            if value is not None and (
                str(value).startswith(("/", "\\")) or WINDOWS_ABSOLUTE.search(str(value))
            ):
                raise RuntimeError(f"absolute {field} in {record['id']}")


def load_json(raw: dict[str, bytes], key: str) -> dict[str, Any]:
    return json.loads(raw[key].decode("utf-8-sig"))


def extract_line_prefix(data: bytes, line_count: int, label: str) -> bytes:
    lines = data.splitlines(keepends=True)
    if len(lines) < line_count:
        raise RuntimeError(f"{label} has fewer than {line_count} physical lines")
    prefix = b"".join(lines[:line_count])
    if not prefix.endswith(b"\n"):
        raise RuntimeError(f"{label} baseline prefix is not LF-terminated")
    return prefix


def extract_baselines(root: Path) -> tuple[bytes, bytes, list[dict[str, Any]]]:
    jsonl_path = root / "backend/records.jsonl"
    csv_path = root / "backend/records.csv"
    current_jsonl = jsonl_path.read_bytes()
    current_csv = csv_path.read_bytes()
    baseline_jsonl = extract_line_prefix(
        current_jsonl, BASELINE_RECORD_COUNT, "records.jsonl"
    )
    baseline_csv = extract_line_prefix(
        current_csv, BASELINE_RECORD_COUNT + 1, "records.csv"
    )
    if len(baseline_jsonl) != BASELINE_JSONL_BYTES or digest(baseline_jsonl) != BASELINE_JSONL_SHA256:
        raise RuntimeError("immutable 357-record JSONL baseline changed")
    if len(baseline_csv) != BASELINE_CSV_BYTES or digest(baseline_csv) != BASELINE_CSV_SHA256:
        raise RuntimeError("immutable 357-record CSV baseline changed")
    records = [
        json.loads(line)
        for line in baseline_jsonl.decode("utf-8").splitlines()
    ]
    if len(records) != BASELINE_RECORD_COUNT:
        raise RuntimeError("baseline JSONL must contain exactly 357 records")
    validate(records)
    csv_rows = list(csv.DictReader(io.StringIO(baseline_csv.decode("utf-8"))))
    if len(csv_rows) != BASELINE_RECORD_COUNT:
        raise RuntimeError("baseline CSV must contain exactly 357 data rows")
    return baseline_jsonl, baseline_csv, records


def receipt_binds_file(
    receipt: Any, expected_path: str, expected_bytes: int, expected_sha256: str
) -> bool:
    if isinstance(receipt, dict):
        path = receipt.get("path")
        size = receipt.get("bytes")
        checksum = receipt.get("sha256") or receipt.get("target_sha256")
        if (
            path == expected_path
            and size == expected_bytes
            and checksum == expected_sha256
        ):
            return True
        return any(
            receipt_binds_file(value, expected_path, expected_bytes, expected_sha256)
            for value in receipt.values()
        )
    if isinstance(receipt, list):
        return any(
            receipt_binds_file(value, expected_path, expected_bytes, expected_sha256)
            for value in receipt
        )
    return False


def declared_corrections(receipts: dict[str, dict[str, Any]]) -> set[str]:
    found: set[str] = set()
    for receipt in receipts.values():
        for declaration in receipt.get("declared_corrections") or []:
            if isinstance(declaration, str):
                found.update(item for item in declaration.split("+") if item)
    return found


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
        raise RuntimeError("final Unit 3 backend state must be visually_checked")

    baseline_jsonl, baseline_csv, baseline_records = extract_baselines(root)
    baseline_ids = {str(record["id"]) for record in baseline_records}

    paths: dict[str, Path] = {
        "schema": root / "backend/schema/o011-record-v1.schema.json",
        "revisions": root / "authority/brenner_selected_root_revisions.csv",
        "media_rights": root / "authority/brenner_media_rights_manifest.csv",
        "terminology": root / "00_control/TERMINOLOGY.csv",
        "unit03_terms_proposed": root / "qa/unit-03/WORKSHEET_TERMS_PROPOSED.csv",
        "adverse": root / "00_control/ADVERSE_LEDGER.csv",
        "u03_worksheet_corrections": root
        / "00_control/WORKSHEET03_PROTECTED_CORRECTIONS.json",
        "u03_lecture_corrections": root
        / "00_control/LECTURE03_PROTECTED_CORRECTIONS.json",
        "unit03_authority": root / "qa/unit-03/AUTHORITY_PREFLIGHT.json",
        "unit03_authority_verify": root / "qa/unit-03/AUTHORITY_PREFLIGHT_VERIFY.json",
        "unit03_solution_closure": root / "qa/unit-03/solution_closure.json",
        "u03_lecture_source": root / "authority/expanded/lecture03_source.de.tex",
        "u03_lecture_target": root / "source/units/unit-03/lecture03.id.tex",
        "u03_lecture_receipt": root / "qa/unit-03/lecture_translation.json",
        "u03_worksheet_source": root / "authority/expanded/worksheet03_source.de.tex",
        "u03_worksheet_target": root / "source/units/unit-03/worksheet03.id.tex",
        "u03_worksheet_receipt": root / "qa/unit-03/worksheet03_translation.json",
        "u03_media_parabola": root / "authority/media/Parabola circle.svg",
        "u03_media_euler": root / "authority/media/Euler spiral.svg",
        "u03_media_evolute": root / "authority/media/Evolute-parab.svg",
        "u03_reader_pdf": root
        / "output/pdf/geometri-diferensial-manifold-mulus-hingga-unit-03-id.pdf",
        "u03_build_receipt": root / "qa/unit-03/build.json",
        "u03_media_receipt": root / "qa/unit-03_media.json",
        "u03_structural_receipt": root / "qa/unit-03/pdf_structural_qa.json",
        "u03_visual_receipt": root / "qa/unit-03/visual_qa.json",
        "u03_math_audit": root / "qa/unit-03/POST_REPAIR_MATH_AUDIT.md",
    }
    for index in SOLUTION_INDICES:
        paths[f"u03_solution{index:02d}_source"] = root / (
            f"authority/expanded/worksheet03_exercise{index:02d}_solution_source.de.tex"
        )
        paths[f"u03_solution{index:02d}_target"] = root / (
            f"source/units/unit-03/worksheet03_exercise{index:02d}_solution.id.tex"
        )
        paths[f"u03_solution{index:02d}_receipt"] = root / (
            f"qa/unit-03/worksheet03_exercise{index:02d}_solution_translation.json"
        )

    html_path = (
        root
        / "output/html/geometri-diferensial-manifold-mulus-hingga-unit-03-id.html"
    ).resolve()
    html_receipt_path = (root / "qa/unit-03/html_structural_qa.json").resolve()
    html_present = html_path.is_file()
    if html_present:
        html_path.relative_to(root)
        html_receipt_path.relative_to(root)
        paths["u03_reader_html"] = html_path
        paths["u03_html_receipt"] = html_receipt_path

    raw = {name: path.read_bytes() for name, path in paths.items()}
    for key in (
        "u03_lecture_target",
        "u03_worksheet_target",
        "u03_solution07_target",
        "u03_solution16_target",
    ):
        assert_public_safe(repository_path(paths[key], root), raw[key])
    if html_present:
        assert_public_safe(repository_path(html_path, root), raw["u03_reader_html"])

    authority = load_json(raw, "unit03_authority")
    authority_verify = load_json(raw, "unit03_authority_verify")
    solution_closure = load_json(raw, "unit03_solution_closure")
    if authority.get("status") != "pass" or authority.get("unit") != 3:
        raise RuntimeError("Unit 3 authority preflight is not a pass")
    structure = authority.get("structure", {})
    if structure.get("lecture_section_count") != 2:
        raise RuntimeError("Unit 3 authority does not bind two lecture segments")
    if structure.get("worksheet_exercise_count") != 21:
        raise RuntimeError("Unit 3 authority does not bind 21 exercises")
    if tuple(structure.get("worksheet_solution_bearing_indices", [])) != SOLUTION_INDICES:
        raise RuntimeError("Unit 3 authority supplied-solution indices changed")
    if tuple(solution_closure.get("supplied_solution_indices", [])) != SOLUTION_INDICES:
        raise RuntimeError("Unit 3 solution closure changed")
    if (
        authority_verify.get("status") != "pass"
        or authority_verify.get("unit") != 3
        or authority_verify.get("preflight", {}).get("sha256")
        != digest(raw["unit03_authority"])
    ):
        raise RuntimeError("Unit 3 authority verification receipt is stale")

    authority_expansions = authority.get("expansions", {})
    for owner, source_key in (
        ("lecture", "u03_lecture_source"),
        ("worksheet", "u03_worksheet_source"),
    ):
        frozen = authority_expansions.get(owner, {}).get("sanitized_source", {})
        if (
            frozen.get("path") != repository_path(paths[source_key], root)
            or frozen.get("bytes") != len(raw[source_key])
            or frozen.get("sha256") != digest(raw[source_key])
        ):
            raise RuntimeError(f"Unit 3 {owner} source drifted from authority preflight")
    if authority.get("solutions") != solution_closure:
        raise RuntimeError("live Unit 3 solution closure drifted from authority preflight")
    authority_solutions = {
        int(row["exercise_index"]): row
        for row in authority["solutions"]["exercises"]
        if row.get("exists")
    }
    if set(authority_solutions) != set(SOLUTION_INDICES):
        raise RuntimeError("Unit 3 authority solution-source closure changed")
    for index in SOLUTION_INDICES:
        source_key = f"u03_solution{index:02d}_source"
        frozen = authority_solutions[index]["expanded_latex"]["sanitized_source"]
        if (
            frozen.get("path") != repository_path(paths[source_key], root)
            or frozen.get("bytes") != len(raw[source_key])
            or frozen.get("sha256") != digest(raw[source_key])
        ):
            raise RuntimeError(
                f"Unit 3 solution {index} source drifted from authority preflight"
            )

    lecture_source = raw["u03_lecture_source"].decode("utf-8")
    lecture_target = raw["u03_lecture_target"].decode("utf-8")
    worksheet_source = raw["u03_worksheet_source"].decode("utf-8")
    worksheet_target = raw["u03_worksheet_target"].decode("utf-8")
    lecture_source_parts = slices(lecture_source, LECTURE_MARKER)
    lecture_target_parts = slices(lecture_target, LECTURE_MARKER)
    worksheet_source_parts = slices(worksheet_source, EXERCISE_MARKER)
    worksheet_target_parts = slices(worksheet_target, EXERCISE_MARKER)
    if len(lecture_source_parts) != 2 or len(lecture_target_parts) != 2:
        raise RuntimeError("Unit 3 lecture must contain exactly two section markers")
    if len(worksheet_source_parts) != 21 or len(worksheet_target_parts) != 21:
        raise RuntimeError("Unit 3 worksheet must contain exactly 21 exercise markers")

    translation_specs: list[dict[str, str]] = [
        {
            "name": "lecture",
            "unit_id": "o011-brenner-u03-l03",
            "source_key": "u03_lecture_source",
            "target_key": "u03_lecture_target",
            "receipt_key": "u03_lecture_receipt",
            "artifact_id": "o011-artifact-u03-l03-tex",
            "qa_id": "o011-qa-unit03-lecture-translation",
        },
        {
            "name": "worksheet",
            "unit_id": "o011-brenner-u03-w03",
            "source_key": "u03_worksheet_source",
            "target_key": "u03_worksheet_target",
            "receipt_key": "u03_worksheet_receipt",
            "artifact_id": "o011-artifact-u03-w03-tex",
            "qa_id": "o011-qa-unit03-worksheet-translation",
        },
    ]
    for index in SOLUTION_INDICES:
        translation_specs.append(
            {
                "name": f"solution{index:02d}",
                "unit_id": f"o011-brenner-u03-w03-e{index:03d}-solution",
                "source_key": f"u03_solution{index:02d}_source",
                "target_key": f"u03_solution{index:02d}_target",
                "receipt_key": f"u03_solution{index:02d}_receipt",
                "artifact_id": f"o011-artifact-u03-w03-e{index:03d}-solution-tex",
                "qa_id": f"o011-qa-unit03-solution{index:02d}-translation",
            }
        )
    receipts: dict[str, dict[str, Any]] = {}
    for spec in translation_specs:
        receipt = load_json(raw, spec["receipt_key"])
        receipts[spec["name"]] = receipt
        if receipt.get("status") != "pass" or receipt.get("failures"):
            raise RuntimeError(f"Unit 3 {spec['name']} receipt is not a clean pass")
        if (
            receipt.get("source_sha256") != digest(raw[spec["source_key"]])
            or receipt.get("source_bytes") != len(raw[spec["source_key"]])
        ):
            raise RuntimeError(f"Unit 3 {spec['name']} receipt is stale against source")
        if (
            receipt.get("target_sha256") != digest(raw[spec["target_key"]])
            or receipt.get("target_bytes") != len(raw[spec["target_key"]])
        ):
            raise RuntimeError(f"Unit 3 {spec['name']} receipt is stale against target")

    adverse_rows = list(
        csv.DictReader(io.StringIO(raw["adverse"].decode("utf-8-sig")))
    )
    for row_number, row in enumerate(adverse_rows, 2):
        if None in row or any(
            row.get(field) is None
            for field in (
                "id",
                "severity",
                "surface",
                "status",
                "description",
                "disposition",
            )
        ):
            raise RuntimeError(f"malformed adverse-ledger CSV row {row_number}")
    if len({row["id"] for row in adverse_rows}) != len(adverse_rows):
        raise RuntimeError("duplicate IDs in adverse ledger")
    correction_rows = {
        row["id"]: row
        for row in adverse_rows
        if row["surface"].startswith(("lecture03:", "worksheet03:"))
        and row["status"] == "corrected_in_target"
    }
    expected_unit3_corrections = {
        f"O011-CORR-{index:04d}" for index in UNIT3_CORRECTION_RANGE
    }
    correction_names = tuple(sorted(correction_rows))
    if set(correction_names) != expected_unit3_corrections:
        raise RuntimeError(
            "Unit 3 adverse-ledger correction closure changed: "
            f"{sorted(correction_rows)}"
        )
    receipt_corrections = declared_corrections(receipts)

    correction_manifests: dict[str, dict[str, Any]] = {}
    protected_deltas_by_id: dict[str, list[dict[str, Any]]] = {
        correction_name: [] for correction_name in correction_names
    }
    protected_ids: set[str] = set()
    for manifest_key, expected_scope, owner in CORRECTION_MANIFEST_SPECS:
        manifest = load_json(raw, manifest_key)
        if manifest.get("schema_version") != 1 or manifest.get("scope") != expected_scope:
            raise RuntimeError(f"Unit 3 {owner} protected-correction manifest drift")
        deltas = manifest.get("allowed_deltas")
        if not isinstance(deltas, list) or not deltas:
            raise RuntimeError(f"Unit 3 {owner} protected-correction manifest is empty")
        manifest_path = repository_path(paths[manifest_key], root)
        manifest_sha256 = digest(raw[manifest_key])
        correction_manifests[owner] = {
            "path": manifest_path,
            "bytes": len(raw[manifest_key]),
            "sha256": manifest_sha256,
        }
        for delta in deltas:
            delta_ids = {
                item
                for item in str(delta.get("correction_id", "")).split("+")
                if item
            }
            if not delta_ids or not delta_ids.issubset(correction_rows):
                raise RuntimeError(
                    f"Unit 3 {owner} protected delta has unknown correction IDs: "
                    f"{sorted(delta_ids)}"
                )
            if any(
                not correction_rows[correction_name]["surface"].startswith(
                    f"{owner}03:"
                )
                for correction_name in delta_ids
            ):
                raise RuntimeError(
                    f"Unit 3 {owner} manifest names a correction owned by another surface"
                )
            protected_ids.update(delta_ids)
            for correction_name in delta_ids:
                protected_deltas_by_id[correction_name].append(
                    {
                        "manifest_path": manifest_path,
                        "manifest_sha256": manifest_sha256,
                        **delta,
                    }
                )
    if not protected_ids or not protected_ids.issubset(correction_rows):
        raise RuntimeError("Unit 3 protected correction closure is invalid")
    if receipt_corrections != protected_ids:
        raise RuntimeError(
            "Unit 3 topology-receipt declarations differ from the protected-delta "
            f"closure: {sorted(receipt_corrections)}"
        )

    proposal_rows = list(
        csv.DictReader(io.StringIO(raw["unit03_terms_proposed"].decode("utf-8-sig")))
    )
    proposal_map = {row["source_de"]: row["target_id"] for row in proposal_rows}
    for source, target in UNIT3_TERMS.items():
        if source in {"Bogenparametrisierung", "bogenparametrisiert"}:
            continue
        if proposal_map.get(source) != target:
            raise RuntimeError(f"Unit 3 terminology proposal drift for {source}")
    terminology_rows = list(
        csv.DictReader(io.StringIO(raw["terminology"].decode("utf-8-sig")))
    )
    admitted_by_pair = {
        (row["source_de"], row["target_id"]): row
        for row in terminology_rows
        if row.get("status") == "admitted"
    }
    term_rows: list[dict[str, str]] = []
    for source, target in UNIT3_TERMS.items():
        row = admitted_by_pair.get((source, target))
        if not row:
            raise RuntimeError(
                f"Unit 3 term is not yet admitted in TERMINOLOGY.csv: {source} -> {target}"
            )
        term_rows.append(row)
    term_rows.sort(key=lambda row: row["id"])
    term_ids = [row["id"].lower() for row in term_rows]
    if len(term_ids) != len(set(term_ids)) or any(term_id in baseline_ids for term_id in term_ids):
        raise RuntimeError("Unit 3 terminology IDs collide with the immutable baseline")

    reader_pdf = raw["u03_reader_pdf"]
    reader_pdf_sha256 = digest(reader_pdf)
    reader_pdf_bytes = len(reader_pdf)
    reader_pdf_path = repository_path(paths["u03_reader_pdf"], root)
    build_receipt = load_json(raw, "u03_build_receipt")
    media_receipt = load_json(raw, "u03_media_receipt")
    structural_receipt = load_json(raw, "u03_structural_receipt")
    visual_receipt = load_json(raw, "u03_visual_receipt")
    math_audit_text = raw["u03_math_audit"].decode("utf-8")
    build_output = build_receipt.get("output", {})
    build_cycles = build_receipt.get("cycles", [])
    build_status = str(build_receipt.get("status", "pass")).casefold()
    if (
        build_status != "pass"
        or build_receipt.get("failures")
        or build_receipt.get("blockers")
        or build_output.get("path") != reader_pdf_path
        or build_output.get("bytes") != reader_pdf_bytes
        or build_output.get("sha256") != reader_pdf_sha256
        or build_receipt.get("deterministic_clean_cycles") is not True
        or len(build_cycles) != 2
        or any(
            cycle.get("cycle") != index
            or cycle.get("bytes") != reader_pdf_bytes
            or cycle.get("sha256") != reader_pdf_sha256
            or len(cycle.get("logs", [])) != 3
            for index, cycle in enumerate(build_cycles, 1)
        )
    ):
        raise RuntimeError("Unit 3 cumulative PDF build receipt is stale or non-reproducible")
    media_status = str(media_receipt.get("status", "pass")).casefold()
    if (
        media_status != "pass"
        or media_receipt.get("failures")
        or media_receipt.get("blockers")
        or media_receipt.get("manifest_sha256") != digest(raw["media_rights"])
        or media_receipt.get("source_count") != 3
        or media_receipt.get("derivative_count") != 3
    ):
        raise RuntimeError("Unit 3 media receipt is stale or incomplete")
    media_receipt_by_filename = {
        item["filename"]: item for item in media_receipt.get("media", [])
    }
    authority_media_by_filename = {
        item["filename"]: item for item in authority.get("media", {}).get("assets", [])
    }
    expected_media_filenames = {spec[1] for spec in MEDIA_SPECS}
    if (
        set(media_receipt_by_filename) != expected_media_filenames
        or set(authority_media_by_filename) != expected_media_filenames
    ):
        raise RuntimeError("Unit 3 media filename closure changed")
    media_derivative_bindings: list[dict[str, Any]] = []
    for _, filename, binary_key, _, _ in MEDIA_SPECS:
        binary = raw[binary_key]
        media_item = media_receipt_by_filename.get(filename, {})
        authority_item = authority_media_by_filename.get(filename, {})
        if (
            media_item.get("canonical_bytes") != len(binary)
            or media_item.get("canonical_sha256") != digest(binary)
            or authority_item.get("bytes") != len(binary)
            or authority_item.get("sha256") != digest(binary)
        ):
            raise RuntimeError(f"Unit 3 media receipt is stale for {filename}")
        derivative = media_item.get("derivative")
        if not isinstance(derivative, dict):
            raise RuntimeError(f"Unit 3 media derivative is absent for {filename}")
        derivative_path = (root / str(derivative.get("path", ""))).resolve()
        try:
            derivative_path.relative_to(root)
        except ValueError as exc:
            raise RuntimeError(f"Unit 3 media derivative path escapes root: {filename}") from exc
        derivative_bytes = derivative_path.read_bytes()
        if (
            derivative.get("bytes") != len(derivative_bytes)
            or derivative.get("sha256") != digest(derivative_bytes)
        ):
            raise RuntimeError(f"Unit 3 media derivative is stale for {filename}")
        media_derivative_bindings.append(
            {
                "filename": filename,
                "path": repository_path(derivative_path, root),
                "bytes": len(derivative_bytes),
                "sha256": digest(derivative_bytes),
            }
        )
    structural_pdf = structural_receipt.get("pdf", {})
    if (
        structural_receipt.get("passed") is not True
        or structural_receipt.get("blockers")
        or structural_pdf.get("path") != reader_pdf_path
        or structural_pdf.get("bytes") != reader_pdf_bytes
        or structural_pdf.get("sha256") != reader_pdf_sha256
        or structural_pdf.get("catalog_language") != "id-ID"
        or structural_receipt.get("bookmarks", {}).get("missing_required")
        or structural_receipt.get("content_closure", {}).get(
            "failed_unit3_media_surfaces"
        )
    ):
        raise RuntimeError("Unit 3 PDF structural receipt is not a clean pass")
    visual_pdf = visual_receipt.get("pdf", {})
    visual_status = visual_receipt.get("status")
    visual_verdict = visual_receipt.get("verdict")
    visual_passed = visual_receipt.get("passed")
    visual_checks = visual_receipt.get("inspection", {}).get("checks", {})
    negative_visual_prefixes = (
        "clipped_",
        "broken_",
        "missing_",
        "unexpected_",
        "unreadable_",
        "footer_",
    )
    visual_checks_pass = bool(visual_checks) and all(
        isinstance(value, bool)
        and (
            value is False
            if key.startswith(negative_visual_prefixes)
            else value is True
        )
        for key, value in visual_checks.items()
    )
    visual_pass = (
        (visual_status is None or str(visual_status).casefold() == "pass")
        and (visual_verdict is None or visual_verdict == "PASS")
        and (visual_passed is None or visual_passed is True)
        and any(
            (
                visual_status is not None,
                visual_verdict is not None,
                visual_passed is not None,
            )
        )
        and not visual_receipt.get("failures")
        and not visual_receipt.get("blockers")
        and visual_receipt.get("inspection", {}).get("all_pages_inspected") is True
        and visual_checks_pass
    )
    visual_render = visual_receipt.get("render", {})
    visual_render_page_count = visual_render.get(
        "page_count", visual_render.get("page_png_count")
    )
    visual_render_inventory_sha256 = visual_render.get(
        "inventory_sha256", visual_render.get("ordered_page_sha256_aggregate")
    )
    if (
        not visual_pass
        or visual_pdf.get("path") != reader_pdf_path
        or visual_pdf.get("bytes") != reader_pdf_bytes
        or visual_pdf.get("sha256") != reader_pdf_sha256
        or visual_render_page_count != visual_pdf.get("pages")
        or not re.fullmatch(r"[0-9a-f]{64}", str(visual_render_inventory_sha256))
    ):
        raise RuntimeError("Unit 3 PDF visual receipt is stale or non-passing")
    audit_bound_hashes = [
        reader_pdf_sha256,
        *(digest(raw[spec["target_key"]]) for spec in translation_specs),
    ]
    if not re.search(
        r"(?mi)^\s*(?:\*\*)?PASS(?:\s+[—–-][^\r\n]*)?(?:\*\*)?\s*$",
        math_audit_text,
    ):
        raise RuntimeError("Unit 3 final mathematical audit is not a pass")
    if any(checksum not in math_audit_text for checksum in audit_bound_hashes):
        raise RuntimeError("Unit 3 mathematical audit does not bind every final target")
    if not re.search(
        r"no remaining P1, P2, or P3|tidak ada temuan P1, P2, atau P3",
        math_audit_text,
        re.IGNORECASE,
    ):
        raise RuntimeError("Unit 3 mathematical audit does not close P1/P2/P3 findings")
    required_audit_evidence = {
        *correction_names,
        digest(raw["adverse"]),
        *(binding["sha256"] for binding in correction_manifests.values()),
    }
    if any(value not in math_audit_text for value in required_audit_evidence):
        raise RuntimeError(
            "Unit 3 mathematical audit does not bind correction IDs, ledger, and manifests"
        )

    html_receipt: dict[str, Any] | None = None
    html_sha256: str | None = None
    html_bytes: int | None = None
    html_repository_path: str | None = None
    html_result = "pass"
    html_limitations: list[Any] = []
    if html_present:
        html_receipt = load_json(raw, "u03_html_receipt")
        html_sha256 = digest(raw["u03_reader_html"])
        html_bytes = len(raw["u03_reader_html"])
        html_repository_path = repository_path(html_path, root)
        status_signal = html_receipt.get("status")
        verdict_signal = html_receipt.get("verdict")
        passed_signal = html_receipt.get("passed")
        html_limitations = list(html_receipt.get("limitations") or [])
        html_pass = (
            not html_receipt.get("failures")
            and not html_receipt.get("blockers")
            and (status_signal is None or str(status_signal).casefold() == "pass")
            and (
                verdict_signal is None
                or verdict_signal in {"PASS", "PASS_WITH_DOCUMENTED_LIMITATION"}
            )
            and (passed_signal is None or passed_signal is True)
            and any(
                (
                    status_signal is not None,
                    verdict_signal is not None,
                    passed_signal is not None,
                )
            )
            and (
                verdict_signal != "PASS_WITH_DOCUMENTED_LIMITATION"
                or bool(html_limitations)
            )
        )
        if not html_pass or not receipt_binds_file(
            html_receipt, html_repository_path, html_bytes, html_sha256
        ):
            raise RuntimeError("present cumulative HTML lacks a passing hash-bound receipt")
        html_result = "admitted_limitation" if html_limitations else "pass"

    pages = authority["authority"]["pages"]
    lecture_revision = pages["lecture_root"]
    worksheet_revision = pages["worksheet_root"]
    supplied_by_index = {
        int(row["exercise_index"]): row
        for row in solution_closure["exercises"]
        if row.get("exists")
    }
    rights_rows = list(
        csv.DictReader(io.StringIO(raw["media_rights"].decode("utf-8-sig")))
    )
    rights_by_filename = {
        row["title"].removeprefix("File:"): row for row in rights_rows
    }

    resource_id = "o011-resource-brenner-dg2023"
    edition_id = "o011-edition-brenner-current-20260821"
    text_rights_id = "o011-rights-brenner-text"
    unit_id = "o011-brenner-u03"
    lecture_id = unit_id + "-l03"
    worksheet_id = unit_id + "-w03"
    added: list[dict[str, object]] = []
    added.extend(
        [
            base(
                unit_id,
                "unit",
                timestamp,
                parent_id="o011-course-d50",
                order=3,
                path="source/units/unit-03",
                resource_id=resource_id,
                edition_id=edition_id,
                source_local_id="Vorlesung 3 + Arbeitsblatt 3",
                language="Indonesian",
                locale="id-ID",
                translation_state=args.translation_state,
                rights_component_id=text_rights_id,
                unit_kind="lecture_worksheet_pair",
                title="Kelengkungan Kurva Berparameter Panjang Busur",
                authority_receipt="qa/unit-03/AUTHORITY_PREFLIGHT.json",
                authority_receipt_sha256=digest(raw["unit03_authority"]),
            ),
            base(
                lecture_id,
                "unit",
                timestamp,
                parent_id=unit_id,
                order=1,
                path="source/units/unit-03/lecture03.id.tex",
                resource_id=resource_id,
                edition_id=edition_id,
                source_local_id=(
                    f"pageid:{lecture_revision['pageid']}/revid:{lecture_revision['revid']}"
                ),
                source_locator=lecture_revision["title"],
                source_sha256=digest(raw["u03_lecture_source"]),
                target_sha256=digest(raw["u03_lecture_target"]),
                language="Indonesian",
                locale="id-ID",
                translation_state=args.translation_state,
                rights_component_id=text_rights_id,
                unit_kind="lecture",
            ),
            base(
                worksheet_id,
                "unit",
                timestamp,
                parent_id=unit_id,
                order=2,
                path="source/units/unit-03/worksheet03.id.tex",
                resource_id=resource_id,
                edition_id=edition_id,
                source_local_id=(
                    f"pageid:{worksheet_revision['pageid']}/revid:{worksheet_revision['revid']}"
                ),
                source_locator=worksheet_revision["title"],
                source_sha256=digest(raw["u03_worksheet_source"]),
                target_sha256=digest(raw["u03_worksheet_target"]),
                language="Indonesian",
                locale="id-ID",
                translation_state=args.translation_state,
                rights_component_id=text_rights_id,
                unit_kind="worksheet",
            ),
        ]
    )

    for index, (source_part, target_part) in enumerate(
        zip(lecture_source_parts, lecture_target_parts), 1
    ):
        added.append(
            base(
                f"{lecture_id}-s{index:02d}",
                "segment",
                timestamp,
                parent_id=lecture_id,
                order=index,
                path=f"source/units/unit-03/lecture03.id.tex#section-{index}",
                resource_id=resource_id,
                edition_id=edition_id,
                source_local_id=f"lecture03:section:{index}",
                source_locator=f"{lecture_revision['title']}#section-{index}",
                source_sha256=digest(source_part.encode("utf-8")),
                target_sha256=digest(target_part.encode("utf-8")),
                language="Indonesian",
                locale="id-ID",
                translation_state=args.translation_state,
                rights_component_id=text_rights_id,
                segment_kind="lecture_section",
            )
        )

    concept_ids: list[str] = []
    for slug, source_label, target_label in CONCEPTS:
        concept_id = f"o011-concept-{slug}"
        concept_ids.append(concept_id)
        added.append(
            base(
                concept_id,
                "concept",
                timestamp,
                parent_id="o011-course-d50",
                source_local_id=source_label,
                language=None,
                locale=None,
                labels={"de": source_label, "id-ID": target_label},
            )
        )
    section_concepts = {
        1: (
            "arc-length-parametrization",
            "planar-signed-curvature",
            "curvature-circle",
            "evolute",
        ),
        2: ("general-curve-curvature",),
    }
    for section, slugs in section_concepts.items():
        for order, slug in enumerate(slugs, 1):
            added.append(
                base(
                    f"o011-rel-u03-l03-s{section:02d}-covers-{slug}",
                    "relation",
                    timestamp,
                    order=order,
                    relation_type="covers",
                    from_id=f"{lecture_id}-s{section:02d}",
                    to_id=f"o011-concept-{slug}",
                    evidence="Direct section content in the frozen Lecture 3 source",
                )
            )

    for row in term_rows:
        term_id = row["id"].lower()
        added.append(
            base(
                term_id,
                "term",
                timestamp,
                parent_id="o011-course-d50",
                order=int(row["id"].rsplit("-", 1)[-1]),
                source_local_id=row["source_de"],
                language=None,
                locale=None,
                labels={"de": row["source_de"], "id-ID": row["target_id"]},
                terminology_status=row["status"],
                note=row["note"],
                terminology_ledger_path="00_control/TERMINOLOGY.csv",
                terminology_ledger_sha256=digest(raw["terminology"]),
            )
        )
        added.append(
            base(
                f"o011-rel-u03-uses-{term_id.removeprefix('o011-')}",
                "relation",
                timestamp,
                relation_type="uses_term",
                from_id=unit_id,
                to_id=term_id,
            )
        )

    previous_exercise: str | None = None
    for index, (source_part, target_part) in enumerate(
        zip(worksheet_source_parts, worksheet_target_parts), 1
    ):
        exercise_id = f"{worksheet_id}-e{index:03d}"
        closure_row = solution_closure["exercises"][index - 1]
        added.append(
            base(
                exercise_id,
                "unit",
                timestamp,
                parent_id=worksheet_id,
                order=index,
                path=f"source/units/unit-03/worksheet03.id.tex#exercise-{index}",
                resource_id=resource_id,
                edition_id=edition_id,
                source_local_id=f"worksheet03:exercise:{index}",
                source_locator=f"{worksheet_revision['title']}#exercise-{index}",
                source_sha256=digest(source_part.encode("utf-8")),
                target_sha256=digest(target_part.encode("utf-8")),
                language="Indonesian",
                locale="id-ID",
                translation_state=args.translation_state,
                rights_component_id=text_rights_id,
                unit_kind="exercise",
                has_authority_solution=index in SOLUTION_INDICES,
                source_display_id=f"3.{index}",
                graded=bool(closure_row["root_point_marker"]),
                point_value=closure_row["point_value"],
                hint_present=bool(closure_row["hint_field"]),
            )
        )
        if previous_exercise:
            added.append(
                base(
                    f"o011-rel-u03-w03-e{index - 1:03d}-precedes-e{index:03d}",
                    "relation",
                    timestamp,
                    relation_type="precedes",
                    from_id=previous_exercise,
                    to_id=exercise_id,
                )
            )
        previous_exercise = exercise_id

    for index in SOLUTION_INDICES:
        authority_row = supplied_by_index[index]
        solution_id = f"{worksheet_id}-e{index:03d}-solution"
        source_key = f"u03_solution{index:02d}_source"
        target_key = f"u03_solution{index:02d}_target"
        added.append(
            base(
                solution_id,
                "unit",
                timestamp,
                parent_id=f"{worksheet_id}-e{index:03d}",
                order=1,
                path=(
                    f"source/units/unit-03/worksheet03_exercise{index:02d}_solution.id.tex"
                ),
                resource_id=resource_id,
                edition_id=edition_id,
                source_local_id=(
                    f"pageid:{authority_row['pageid']}/revid:{authority_row['revid']}"
                ),
                source_locator=authority_row["solution_title"],
                source_sha256=digest(raw[source_key]),
                target_sha256=digest(raw[target_key]),
                language="Indonesian",
                locale="id-ID",
                translation_state=args.translation_state,
                rights_component_id=text_rights_id,
                unit_kind="solution",
                source_display_id=f"3.{index}",
                authority_wikitext_sha256=authority_row["source_utf8_sha256"],
            )
        )
        added.append(
            base(
                f"o011-rel-u03-w03-e{index:03d}-solution-solves-e{index:03d}",
                "relation",
                timestamp,
                relation_type="solves",
                from_id=solution_id,
                to_id=f"{worksheet_id}-e{index:03d}",
            )
        )

    asset_ids: list[str] = []
    media_rights_ids: list[str] = []
    for order, filename, binary_key, slug, owner in MEDIA_SPECS:
        row = rights_by_filename[filename]
        binary = raw[binary_key]
        authority_item = authority_media_by_filename[filename]
        if (
            len(binary) != int(row["bytes"])
            or digest(binary) != authority_item["sha256"]
            or authority_item["commons_sha1"] != row["commons_sha1_hex"]
        ):
            raise RuntimeError(f"Unit 3 media authority mismatch for {filename}")
        rights_id = f"o011-rights-media-u03-{order:02d}"
        asset_id = f"o011-asset-file-{slug}"
        added.append(
            base(
                rights_id,
                "rights",
                timestamp,
                source_local_id=f"File:{filename}",
                license=row["license"],
                license_url=row["license_url"] or None,
                attribution=row["artist_html"],
                credit=row["credit_html"],
                component_scope=f"File:{filename}",
                attribution_required=row["attribution_required"].lower() == "true",
                copyrighted=row["copyrighted"],
                commons_lastrevid=authority_item["commons_lastrevid"],
                commons_image_timestamp=authority_item["image_timestamp"],
            )
        )
        added.append(
            base(
                asset_id,
                "asset",
                timestamp,
                parent_id=unit_id,
                order=order,
                path=f"authority/media/{filename}",
                source_local_id=f"File:{filename}",
                source_locator=row["description_url"],
                source_sha256=digest(binary),
                rights_component_id=rights_id,
                mime=row["mime"],
                expected_bytes=int(row["bytes"]),
                commons_sha1=row["commons_sha1_hex"],
                binary_present=True,
            )
        )
        asset_ids.append(asset_id)
        media_rights_ids.append(rights_id)
        owner_id = lecture_id if owner == "lecture" else worksheet_id
        added.append(
            base(
                f"o011-rel-u03-{owner}-uses-{slug}",
                "relation",
                timestamp,
                relation_type="uses",
                from_id=owner_id,
                to_id=asset_id,
            )
        )

    previous_pdf = next(
        record
        for record in baseline_records
        if record["id"] == "o011-artifact-through-unit02-pdf"
    )
    prior_rights_ids = list(previous_pdf.get("component_rights_ids") or [])
    cumulative_rights_ids = [*prior_rights_ids, *media_rights_ids]
    if len(cumulative_rights_ids) != len(set(cumulative_rights_ids)):
        raise RuntimeError("cumulative reader component-rights IDs are not unique")
    pdf_artifact_id = "o011-artifact-through-unit03-pdf"
    added.append(
        base(
            pdf_artifact_id,
            "artifact",
            timestamp,
            parent_id=unit_id,
            path=reader_pdf_path,
            target_sha256=reader_pdf_sha256,
            language="Indonesian",
            locale="id-ID",
            translation_state="visually_checked",
            artifact_kind="cumulative_reader_pdf",
            media_type="application/pdf",
            bytes=reader_pdf_bytes,
            component_rights_ids=cumulative_rights_ids,
            build_receipt_path=repository_path(paths["u03_build_receipt"], root),
            build_receipt_sha256=digest(raw["u03_build_receipt"]),
            deterministic_clean_cycles=True,
            clean_cycle_count=2,
            coverage_unit_ids=[
                "o011-brenner-u01",
                "o011-brenner-u02",
                unit_id,
            ],
        )
    )

    artifact_ids = [
        *(spec["artifact_id"] for spec in translation_specs),
        pdf_artifact_id,
    ]
    html_artifact_id: str | None = None
    if html_present:
        assert html_sha256 is not None
        assert html_bytes is not None
        assert html_repository_path is not None
        html_artifact_id = "o011-artifact-through-unit03-html"
        artifact_ids.append(html_artifact_id)
        added.append(
            base(
                html_artifact_id,
                "artifact",
                timestamp,
                parent_id=unit_id,
                path=html_repository_path,
                target_sha256=html_sha256,
                language="Indonesian",
                locale="id-ID",
                translation_state="visually_checked",
                artifact_kind="cumulative_reader_html",
                media_type="text/html",
                bytes=html_bytes,
                component_rights_ids=cumulative_rights_ids,
                coverage_unit_ids=[
                    "o011-brenner-u01",
                    "o011-brenner-u02",
                    unit_id,
                ],
                offline_capable=True,
            )
        )

    qa_specs: list[dict[str, Any]] = [
        {
            "id": "o011-qa-unit03-authority-preflight",
            "target_id": unit_id,
            "receipt_key": "unit03_authority",
            "qa_kind": "authority_source_media_solution_closure",
            "result": "pass",
            "translation_state": "source_frozen",
            "values": {
                "lecture_section_count": 2,
                "worksheet_exercise_count": 21,
                "supplied_solution_indices": list(SOLUTION_INDICES),
                "asset_ids": asset_ids,
                "component_rights_ids": media_rights_ids,
            },
        },
        {
            "id": "o011-qa-unit03-authority-verification",
            "target_id": unit_id,
            "receipt_key": "unit03_authority_verify",
            "qa_kind": "offline_authority_closure_verification",
            "result": "pass",
            "translation_state": "source_frozen",
            "values": {
                "root_page_witnesses_verified": authority_verify[
                    "root_page_witnesses_verified"
                ],
                "exercise_candidates_verified": authority_verify[
                    "exercise_candidates_verified"
                ],
            },
        },
        {
            "id": "o011-qa-unit03-media-closure",
            "target_id": unit_id,
            "receipt_key": "u03_media_receipt",
            "qa_kind": "media_rights_and_binary_closure",
            "result": "pass",
            "translation_state": "structurally_verified",
            "values": {
                "source_count": 3,
                "derivative_count": 3,
                "asset_ids": asset_ids,
                "component_rights_ids": media_rights_ids,
            },
        },
        {
            "id": "o011-qa-through-unit03-pdf-reproducibility",
            "target_id": pdf_artifact_id,
            "artifact_id": pdf_artifact_id,
            "receipt_key": "u03_build_receipt",
            "qa_kind": "reproducible_pdf_build",
            "result": "pass",
            "translation_state": "built",
            "target_sha256": reader_pdf_sha256,
            "values": {
                "engine": build_receipt["engine"],
                "deterministic_clean_cycles": True,
                "clean_cycle_count": 2,
                "pass_count_per_cycle": 3,
                "artifact_bytes": reader_pdf_bytes,
            },
        },
        {
            "id": "o011-qa-through-unit03-pdf-structural",
            "target_id": pdf_artifact_id,
            "artifact_id": pdf_artifact_id,
            "receipt_key": "u03_structural_receipt",
            "qa_kind": "pdf_structure_accessibility_and_safety",
            "result": (
                "admitted_limitation"
                if structural_receipt.get("limitations")
                else "pass"
            ),
            "translation_state": "visually_checked",
            "target_sha256": reader_pdf_sha256,
            "values": {
                "page_count": structural_pdf["pages"],
                "page_size_points": structural_pdf["media_box_points"],
                "catalog_language": structural_pdf["catalog_language"],
                "tagged": structural_pdf["tagged"],
                "limitations": structural_receipt["limitations"],
                "bookmark_count": structural_receipt["bookmarks"]["count"],
                "accessibility": {
                    "unique_fonts": structural_receipt["accessibility"][
                        "unique_fonts"
                    ],
                    "fonts_with_tounicode": structural_receipt["accessibility"][
                        "fonts_with_tounicode"
                    ],
                    "pages_with_extractable_text": structural_receipt[
                        "accessibility"
                    ]["pdfplumber_pages_with_extractable_text"],
                    "empty_text_pages": structural_receipt["accessibility"][
                        "pdfplumber_empty_text_pages"
                    ],
                },
                "active_content": structural_receipt["active_content"],
                "external_uri_count": structural_receipt["links"][
                    "external_uri_count"
                ],
                "internal_link_count": structural_receipt["links"][
                    "internal_link_count"
                ],
            },
        },
        {
            "id": "o011-qa-through-unit03-pdf-visual",
            "target_id": pdf_artifact_id,
            "artifact_id": pdf_artifact_id,
            "receipt_key": "u03_visual_receipt",
            "qa_kind": "pdf_visual_inspection",
            "result": "pass",
            "translation_state": "visually_checked",
            "target_sha256": reader_pdf_sha256,
            "values": {
                "page_count": visual_pdf["pages"],
                "all_pages_inspected": visual_receipt["inspection"][
                    "all_pages_inspected"
                ],
                "page_dimensions_pixels": visual_render.get("pixel_dimensions_each"),
                "render_inventory_sha256": visual_render_inventory_sha256,
                "inspection": visual_receipt["inspection"],
            },
        },
        {
            "id": "o011-qa-unit03-final-math-audit",
            "target_id": unit_id,
            "artifact_id": pdf_artifact_id,
            "receipt_key": "u03_math_audit",
            "qa_kind": "independent_post_repair_mathematical_audit",
            "result": "pass",
            "translation_state": "visually_checked",
            "target_sha256": reader_pdf_sha256,
            "values": {
                "scope": "four Unit 3 reader sources, correction closure, and cumulative PDF",
                "audited_target_hashes": {
                    spec["name"]: digest(raw[spec["target_key"]])
                    for spec in translation_specs
                },
                "audited_pdf_sha256": reader_pdf_sha256,
                "remaining_p1_p2_p3_findings": 0,
                "correction_ids": list(correction_names),
                "adverse_ledger_sha256": digest(raw["adverse"]),
                "correction_manifest_sha256s": {
                    owner: binding["sha256"]
                    for owner, binding in sorted(correction_manifests.items())
                },
            },
        },
    ]

    for spec in translation_specs:
        receipt = receipts[spec["name"]]
        qa_specs.append(
            {
                "id": spec["qa_id"],
                "target_id": spec["unit_id"],
                "artifact_id": spec["artifact_id"],
                "receipt_key": spec["receipt_key"],
                "qa_kind": "translation_structure",
                "result": "pass",
                "translation_state": args.translation_state,
                "source_sha256": digest(raw[spec["source_key"]]),
                "target_sha256": digest(raw[spec["target_key"]]),
                "values": {
                    "checks": receipt["checks"],
                    "counts": receipt["counts"],
                    "declared_corrections": sorted(
                        {
                            value
                            for value in receipt.get("declared_corrections") or []
                            if isinstance(value, str) and value
                        }
                    ),
                },
            }
        )

    if html_present:
        assert html_artifact_id is not None
        assert html_sha256 is not None
        qa_specs.append(
            {
                "id": "o011-qa-through-unit03-html-structural",
                "target_id": html_artifact_id,
                "artifact_id": html_artifact_id,
                "receipt_key": "u03_html_receipt",
                "qa_kind": "html_structure_accessibility_links_and_safety",
                "result": html_result,
                "translation_state": "visually_checked",
                "target_sha256": html_sha256,
                "values": {
                    "offline_capable": True,
                    "limitations": html_limitations,
                },
            }
        )

    for spec in translation_specs:
        source_key = spec["source_key"]
        target_key = spec["target_key"]
        artifact_id = spec["artifact_id"]
        target_id = spec["unit_id"]
        added.append(
            base(
                artifact_id,
                "artifact",
                timestamp,
                parent_id=target_id,
                path=repository_path(paths[target_key], root),
                source_sha256=digest(raw[source_key]),
                target_sha256=digest(raw[target_key]),
                language="Indonesian",
                locale="id-ID",
                translation_state=args.translation_state,
                rights_component_id=text_rights_id,
                artifact_kind="translated_tex_fragment",
                media_type="application/x-tex",
                bytes=len(raw[target_key]),
                component_rights_ids=[text_rights_id],
            )
        )
        added.append(
            base(
                f"o011-rel-{artifact_id.removeprefix('o011-')}-represents-{target_id.removeprefix('o011-')}",
                "relation",
                timestamp,
                relation_type="represents",
                from_id=artifact_id,
                to_id=target_id,
            )
        )

    qa_ids: list[str] = []
    for spec in qa_specs:
        qa_id = spec["id"]
        qa_ids.append(qa_id)
        receipt_key = spec["receipt_key"]
        values = {
            "parent_id": unit_id,
            "target_id": spec["target_id"],
            "receipt_path": repository_path(paths[receipt_key], root),
            "evidence_sha256": digest(raw[receipt_key]),
            "language": (
                "Indonesian"
                if spec.get("translation_state") not in {"source_frozen"}
                else None
            ),
            "locale": (
                "id-ID"
                if spec.get("translation_state") not in {"source_frozen"}
                else None
            ),
            "translation_state": spec["translation_state"],
            "qa_kind": spec["qa_kind"],
            "result": spec["result"],
            **spec.get("values", {}),
        }
        for optional in ("artifact_id", "source_sha256", "target_sha256"):
            if spec.get(optional) is not None:
                values[optional] = spec[optional]
        added.append(base(qa_id, "qa_event", timestamp, **values))
        added.append(
            base(
                f"o011-rel-{qa_id.removeprefix('o011-')}-verifies-{str(spec['target_id']).removeprefix('o011-')}",
                "relation",
                timestamp,
                relation_type="verifies",
                from_id=qa_id,
                to_id=spec["target_id"],
            )
        )

    added.append(
        base(
            "o011-rel-artifact-through-unit03-pdf-represents-u03-checkpoint",
            "relation",
            timestamp,
            relation_type="represents",
            from_id=pdf_artifact_id,
            to_id=unit_id,
        )
    )
    if html_artifact_id:
        added.append(
            base(
                "o011-rel-artifact-through-unit03-html-represents-u03-checkpoint",
                "relation",
                timestamp,
                relation_type="represents",
                from_id=html_artifact_id,
                to_id=unit_id,
            )
        )
    added.append(
        base(
            "o011-rel-u02-precedes-u03",
            "relation",
            timestamp,
            relation_type="precedes",
            from_id="o011-brenner-u02",
            to_id=unit_id,
        )
    )

    for correction_name in correction_names:
        row = correction_rows[correction_name]
        solution_match = re.fullmatch(
            r"worksheet03:exercise(\d{2})-solution-.*", row["surface"]
        )
        worksheet_match = re.fullmatch(r"worksheet03:exercise(\d{2})-.*", row["surface"])
        if solution_match:
            exercise_index = int(solution_match.group(1))
            if exercise_index not in SOLUTION_INDICES:
                raise RuntimeError(
                    f"Unit 3 correction names a non-supplied solution: {correction_name}"
                )
            correction_target = f"{worksheet_id}-e{exercise_index:03d}-solution"
            receipt_key = f"u03_solution{exercise_index:02d}_receipt"
            target_key = f"u03_solution{exercise_index:02d}_target"
            manifest_owner = None
        elif worksheet_match:
            exercise_index = int(worksheet_match.group(1))
            if not 1 <= exercise_index <= 21:
                raise RuntimeError(
                    f"Unit 3 correction has invalid worksheet target: {correction_name}"
                )
            correction_target = f"{worksheet_id}-e{exercise_index:03d}"
            receipt_key = "u03_worksheet_receipt"
            target_key = "u03_worksheet_target"
            manifest_owner = "worksheet"
        elif row["surface"].startswith("worksheet03:"):
            correction_target = worksheet_id
            receipt_key = "u03_worksheet_receipt"
            target_key = "u03_worksheet_target"
            manifest_owner = "worksheet"
        elif row["surface"].startswith("lecture03:"):
            correction_target = lecture_id
            receipt_key = "u03_lecture_receipt"
            target_key = "u03_lecture_target"
            manifest_owner = "lecture"
        else:
            raise RuntimeError(f"Unit 3 correction has unknown target: {correction_name}")
        protected_deltas = protected_deltas_by_id[correction_name]
        if protected_deltas and manifest_owner is None:
            raise RuntimeError(
                f"Unit 3 correction has protected deltas without an owner manifest: {correction_name}"
            )
        correction_manifest_binding = (
            correction_manifests[manifest_owner] if protected_deltas else None
        )
        correction_id = correction_name.lower()
        added.append(
            base(
                correction_id,
                "correction",
                timestamp,
                source_local_id=row["surface"],
                severity=row["severity"],
                correction_status=row["status"],
                description=row["description"],
                disposition=row["disposition"],
                upstream_report_disposition="deferred_until_full_corpus",
                ledger_path=repository_path(paths["adverse"], root),
                ledger_sha256=digest(raw["adverse"]),
                protected_deltas=protected_deltas,
                correction_manifest=correction_manifest_binding,
                target_binding={
                    "path": repository_path(paths[target_key], root),
                    "bytes": len(raw[target_key]),
                    "sha256": digest(raw[target_key]),
                    "receipt_path": repository_path(paths[receipt_key], root),
                    "receipt_sha256": digest(raw[receipt_key]),
                },
                reader_binding={
                    "path": reader_pdf_path,
                    "bytes": reader_pdf_bytes,
                    "sha256": reader_pdf_sha256,
                    "build_receipt_path": repository_path(
                        paths["u03_build_receipt"], root
                    ),
                    "build_receipt_sha256": digest(raw["u03_build_receipt"]),
                    "structural_receipt_path": repository_path(
                        paths["u03_structural_receipt"], root
                    ),
                    "structural_receipt_sha256": digest(raw["u03_structural_receipt"]),
                    "visual_receipt_path": repository_path(
                        paths["u03_visual_receipt"], root
                    ),
                    "visual_receipt_sha256": digest(raw["u03_visual_receipt"]),
                    "math_audit_path": repository_path(paths["u03_math_audit"], root),
                    "math_audit_sha256": digest(raw["u03_math_audit"]),
                },
            )
        )
        added.append(
            base(
                f"o011-rel-{correction_id.removeprefix('o011-')}-corrects-{correction_target.removeprefix('o011-')}",
                "relation",
                timestamp,
                relation_type="corrects",
                from_id=correction_id,
                to_id=correction_target,
            )
        )

    for child in list(added):
        parent_id = child.get("parent_id")
        if parent_id and child["entity_type"] not in {"relation", "rights", "correction"}:
            child_slug = str(child["id"]).removeprefix("o011-")
            added.append(
                base(
                    f"o011-rel-contains-{child_slug}",
                    "relation",
                    timestamp,
                    relation_type="contains",
                    from_id=parent_id,
                    to_id=child["id"],
                )
            )

    collisions = sorted(
        str(record["id"]) for record in added if str(record["id"]) in baseline_ids
    )
    if collisions:
        raise RuntimeError(f"Unit 3 stable IDs collide with Unit 1-2 baseline: {collisions}")
    added.sort(key=lambda record: str(record["id"]))
    records = [*baseline_records, *added]
    validate(records)
    schema = json.loads(raw["schema"].decode("utf-8"))
    Draft202012Validator.check_schema(schema)
    schema_validator = Draft202012Validator(schema, format_checker=FormatChecker())
    for record in records:
        errors = sorted(
            schema_validator.iter_errors(record), key=lambda error: list(error.path)
        )
        if errors:
            raise RuntimeError(
                f"schema failure in {record['id']}: {errors[0].message}"
            )

    new_jsonl = "".join(canonical_json(record) + "\n" for record in added).encode(
        "utf-8"
    )
    jsonl = baseline_jsonl + new_jsonl
    if jsonl[: len(baseline_jsonl)] != baseline_jsonl:
        raise RuntimeError("JSONL baseline prefix changed during Unit 3 extension")
    assert_public_safe("records.jsonl", jsonl)

    csv_buffer = io.StringIO(newline="")
    writer = csv.DictWriter(csv_buffer, fieldnames=COMMON, lineterminator="\n")
    for record in added:
        writer.writerow({field: record.get(field) for field in COMMON})
    csv_suffix = csv_buffer.getvalue().encode("utf-8")
    csv_bytes = baseline_csv + csv_suffix
    if csv_bytes[: len(baseline_csv)] != baseline_csv:
        raise RuntimeError("CSV baseline prefix changed during Unit 3 extension")
    if len(list(csv.DictReader(io.StringIO(csv_bytes.decode("utf-8"))))) != len(records):
        raise RuntimeError("combined CSV row count differs from JSONL")
    assert_public_safe("records.csv", csv_bytes)

    unit03_counts = {
        name: sum(record["entity_type"] == name for record in added)
        for name in sorted(ENTITY_TYPES)
    }
    generated = {
        "schema_version": 3,
        "generator": "scripts/export_backend_v3.py",
        "generator_sha256": digest(Path(__file__).read_bytes()),
        "timestamp": timestamp,
        "record_count": len(records),
        "entity_counts": {
            name: sum(record["entity_type"] == name for record in records)
            for name in sorted(ENTITY_TYPES)
        },
        "unit12_baseline_preservation": {
            "path": "backend/records.jsonl",
            "record_count": BASELINE_RECORD_COUNT,
            "bytes": len(baseline_jsonl),
            "sha256": digest(baseline_jsonl),
            "byte_identical_prefix": True,
            "csv_path": "backend/records.csv",
            "csv_bytes": len(baseline_csv),
            "csv_sha256": digest(baseline_csv),
            "csv_byte_identical_prefix": True,
        },
        "unit03_extension": {
            "record_count": len(added),
            "entity_counts": unit03_counts,
            "translation_state": args.translation_state,
            "authority_receipt_sha256": digest(raw["unit03_authority"]),
            "correction_ids": list(correction_names),
            "target_hashes": {
                spec["name"]: digest(raw[spec["target_key"]])
                for spec in translation_specs
            },
            "exercise_count": 21,
            "solution_indices": list(SOLUTION_INDICES),
            "segment_count": 2,
            "concept_ids": concept_ids,
            "term_ids": term_ids,
            "asset_ids": asset_ids,
            "rights_ids": media_rights_ids,
            "media_derivatives": media_derivative_bindings,
            "artifact_ids": artifact_ids,
            "qa_event_ids": sorted(qa_ids),
            "cumulative_pdf": {
                "path": reader_pdf_path,
                "bytes": reader_pdf_bytes,
                "sha256": reader_pdf_sha256,
            },
            "cumulative_html": {
                "included": html_present,
                "path": html_repository_path,
                "bytes": html_bytes,
                "sha256": html_sha256,
            },
        },
        "inputs": {
            "unit12_baseline_jsonl": {
                "path": "backend/records.jsonl",
                "bytes": len(baseline_jsonl),
                "sha256": digest(baseline_jsonl),
            },
            "unit12_baseline_csv": {
                "path": "backend/records.csv",
                "bytes": len(baseline_csv),
                "sha256": digest(baseline_csv),
            },
            **{
                name: {
                    "path": repository_path(paths[name], root),
                    "bytes": len(raw[name]),
                    "sha256": digest(raw[name]),
                }
                for name in sorted(paths)
            },
        },
        "outputs": {
            "records.jsonl": {"bytes": len(jsonl), "sha256": digest(jsonl)},
            "records.csv": {"bytes": len(csv_bytes), "sha256": digest(csv_bytes)},
        },
        "safety_checks": {
            "unit12_jsonl_prefix_byte_identical": True,
            "unit12_csv_prefix_byte_identical": True,
            "absolute_machine_paths_absent": True,
            "common_credential_markers_absent": True,
            "unit03_receipts_current": True,
            "unit03_terms_admitted": True,
            "html_included_only_if_present_and_verified": True,
        },
    }
    manifest_bytes = (
        json.dumps(generated, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    ).encode("utf-8")
    assert_public_safe("MANIFEST.json", manifest_bytes)

    (root / "backend/records.jsonl").write_bytes(jsonl)
    (root / "backend/records.csv").write_bytes(csv_bytes)
    (root / "backend/MANIFEST.json").write_bytes(manifest_bytes)


if __name__ == "__main__":
    main()
