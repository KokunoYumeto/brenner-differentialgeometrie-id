#!/usr/bin/env python3
"""Independently verify the cumulative Unit 19 source package.

The staged archive is treated as untrusted input.  This verifier checks the
deterministic ZIP/container surfaces, privacy boundary, durable source and
rights closure, and the exact outer release inventory.  It then extracts the
archive into two independent empty temporary roots and executes the packaged
PDF, HTML, and backend build paths.  Both clean reconstructions must be byte
identical to each other and to the canonical staged Unit 19 artifacts.

No network or publication operation is performed.  Temporary extraction
roots are removed before a passing receipt is written.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Iterator


SCHEMA_VERSION = 1
WORKFLOW = "o011-verify-source-package-unit19-v1"
MODEL_IDENTIFICATION = "OpenAI Codex gpt-5.6-sol, Ultra"
ZIP_TIMESTAMP = (2026, 8, 26, 0, 0, 0)

DEFAULT_RELEASE_DIR = "output/release-unit19"
DEFAULT_SOURCE_ZIP = (
    "output/release-unit19/"
    "geometri-diferensial-manifold-mulus-unit19-source-20260826.zip"
)
DEFAULT_RECEIPT = "qa/unit-19/SOURCE_PACKAGE_INTEGRITY.json"
CANONICAL_PDF = (
    "output/pdf/geometri-diferensial-manifold-mulus-hingga-unit-19-id.pdf"
)
STAGED_PDF_NAME = "geometri-diferensial-manifold-mulus-hingga-unit-19-id.pdf"
STAGED_HTML_NAME = (
    "geometri-diferensial-manifold-mulus-unit19-html-20260826.zip"
)
STAGED_SOURCE_NAME = (
    "geometri-diferensial-manifold-mulus-unit19-source-20260826.zip"
)
OUTER_MANIFEST = "FILE_MANIFEST.json"
OUTER_CHECKSUMS = "SHA256SUMS.txt"
OUTER_LICENSE = "LICENSE.md"
OUTER_NOTES = "RELEASE_NOTES_UNIT19_20260826.md"
CANONICAL_HTML_ROOT = "output/html/unit-19"
CANONICAL_BACKEND = (
    "backend/records.jsonl",
    "backend/records.csv",
    "backend/MANIFEST.json",
)

MINIMUM_RECORD_COUNT = 3208
UNIT16_JSONL_PREFIX_BYTES = 1_966_474
UNIT16_JSONL_PREFIX_SHA256 = (
    "c42bac17822f949aa16ac0f87c7d0726526d020d46bab97f91d36e70f4b21983"
)
UNIT16_CSV_PREFIX_LINES = 3209
UNIT16_CSV_PREFIX_BYTES = 727_631
UNIT16_CSV_PREFIX_SHA256 = (
    "2ff324a750b01540fd3827684947877e807ac8402d09fc6ece1efdf14caeb312"
)
MINIMUM_CORRECTION_RECORD_COUNT = 193
MINIMUM_ADVERSE_ROWS = 193
MINIMUM_TERMINOLOGY_ROWS = 258
MINIMUM_ASSET_RECORD_COUNT = 25
MINIMUM_RIGHTS_RECORD_COUNT = 27
EXPECTED_MEDIA_RIGHTS_ROWS = 36
EXPECTED_EXERCISES = 394
EXPECTED_SOURCE_SOLUTIONS = 54
MINIMUM_PDF_PAGES = 261

REQUIRED_CONTROLS = (
    "00_control/GOAL_AND_WORKFLOW.md",
    "00_control/CURRENT_STATE.md",
    "00_control/CURSOR.json",
    "00_control/DECISION_LOG.md",
    "00_control/AUTHORITY_FREEZE.md",
    "00_control/SCOPE_AND_OVERLAP.md",
    "00_control/TERMINOLOGY.csv",
    "00_control/ADVERSE_LEDGER.csv",
)

REQUIRED_AUTHORITY = (
    "authority/brenner_export_and_title_inventory_receipt.txt",
    "authority/brenner_selected_root_revisions.csv",
    "authority/brenner_selected_surface_revisions.csv",
    "authority/brenner_media_rights_manifest.csv",
    "authority/brenner_94_link_classification.csv",
    "authority/expanded/script_preamble_source.de.tex",
)

REQUIRED_BUILD_PATHS = (
    "scripts/build_through_unit10.ps1",
    "scripts/build_through_unit19.ps1",
    "scripts/verify_through_unit10_pdf.py",
    "scripts/verify_through_unit13_pdf.py",
    "scripts/verify_through_unit19_pdf.py",
    "scripts/export_html_v10.py",
    "scripts/export_html_v13.py",
    "scripts/export_html_v19.py",
    "scripts/verify_html_v10.py",
    "scripts/verify_html_v13.py",
    "scripts/verify_html_v19.py",
    "scripts/test_html_v19_pipeline.py",
    "scripts/verify_html_animated_media.py",
    "scripts/export_backend_v10.py",
    "scripts/export_backend_v19.py",
    "scripts/verify_backend_v10.py",
    "scripts/verify_backend_v19.py",
    "scripts/verify_source_package_unit13_r1.py",
    "scripts/verify_source_package_unit19.py",
    "scripts/prepare_unit_tex.py",
    "scripts/prepare_unit_media.py",
    "scripts/stage_zenodo_unit19.py",
    "scripts/verify_unit_translation.py",
)

REQUIRED_PACKAGE_DOCUMENTS = (
    "PACKAGE_README.md",
    "README.md",
    "LICENSE.md",
    "RELEASE_NOTES_UNIT19_20260826.md",
)

REQUIRED_CURRENT_QA = (
    "qa/unit-18/ANIMATED_MEDIA_QA.json",
    "qa/unit-19/build.json",
    "qa/unit-19/pdf_structural_qa.json",
    "qa/unit-19/PDF_VISUAL_QA.json",
    "qa/unit-19/HTML_READER_QA.json",
    "qa/unit-19/HTML_BROWSER_QA.json",
    "qa/unit-19/backend.json",
    "qa/unit-19/UNIT10_PREFIX_PRESERVATION_RECEIPT.json",
    "qa/unit-19/WRAPPER_DERIVATION_RECEIPT.json",
    "qa/unit-19/MEDIA_ALIAS_RECEIPT.json",
)

REQUIRED_PREDECESSOR_SURFACES = (
    "output/release-unit10/geometri-diferensial-manifold-mulus-brenner-id-unit10-source-20260823.zip",
    "output/release-unit10/geometri-diferensial-manifold-mulus-brenner-id-unit10-html-20260823.zip",
    "output/release-unit10/geometri-diferensial-manifold-mulus-hingga-unit-10-id.pdf",
    "output/release-unit13-r1/geometri-diferensial-manifold-mulus-brenner-id-unit13-html-20260825.zip",
    "output/html/unit-13/index.html",
    "output/html/unit-13/manifest.json",
    "qa/unit-13/HTML_READER_QA.json",
    "qa/unit-13/HTML_BROWSER_QA.json",
    "qa/unit-13/PDF_VISUAL_QA.json",
)

EMBEDDED_MANIFEST = "PACKAGE_MANIFEST.json"
EMBEDDED_CHECKSUMS = "PACKAGE_CHECKSUMS.sha256"


def load_base_module() -> Any:
    """Load the hardened Unit 13 ZIP/privacy helpers from the same package."""
    path = Path(__file__).resolve().with_name("verify_source_package_unit13_r1.py")
    if not path.is_file():
        raise RuntimeError(
            "required hardened helper is missing: scripts/verify_source_package_unit13_r1.py"
        )
    spec = importlib.util.spec_from_file_location("o011_unit13_source_verifier", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load the Unit 13 source-package verifier helper")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.ZIP_TIMESTAMP = ZIP_TIMESTAMP
    module.EMBEDDED_MANIFEST = EMBEDDED_MANIFEST
    module.EMBEDDED_CHECKSUMS = EMBEDDED_CHECKSUMS
    return module


BASE = load_base_module()


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def file_binding(path: Path, root: Path | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }
    if root is not None:
        result = {
            "path": path.resolve().relative_to(root.resolve()).as_posix(),
            **result,
        }
    return result


def project_file(root: Path, relative: str) -> Path:
    return BASE.project_file(root, relative)


def load_json(path: Path) -> Any:
    return BASE.load_json(path)


def count_csv_rows(path: Path) -> int:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return sum(1 for _ in csv.DictReader(stream))


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def iter_bindings(value: Any) -> Iterator[dict[str, Any]]:
    yield from BASE.iter_bindings(value)


def validate_binding(root: Path, value: dict[str, Any], label: str) -> dict[str, Any]:
    relative = value.get("path")
    size = value.get("bytes")
    digest = value.get("sha256")
    if (
        not isinstance(relative, str)
        or not isinstance(size, int)
        or not isinstance(digest, str)
        or re.fullmatch(r"[0-9a-f]{64}", digest.lower()) is None
    ):
        raise RuntimeError(f"invalid {label} binding")
    actual = file_binding(project_file(root, relative), root)
    expected = {"path": relative, "bytes": size, "sha256": digest.lower()}
    if actual != expected:
        raise RuntimeError(f"stale {label} binding: {relative}")
    return actual


def validate_binding_collection(
    root: Path, value: Any, label: str, *, minimum: int = 1
) -> dict[str, Any]:
    count = 0
    unique: set[tuple[str, int, str]] = set()
    for record in iter_bindings(value):
        actual = validate_binding(root, record, label)
        unique.add((actual["path"], actual["bytes"], actual["sha256"]))
        count += 1
    if count < minimum:
        raise RuntimeError(f"{label} has only {count} identity bindings")
    return {"bindings": count, "unique_bindings": len(unique)}


def load_backend_records(root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for number, line in enumerate(
        project_file(root, "backend/records.jsonl")
        .read_text(encoding="utf-8")
        .splitlines(),
        1,
    ):
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"invalid backend JSONL row {number}") from exc
        if not isinstance(record, dict):
            raise RuntimeError(f"backend JSONL row {number} is not an object")
        records.append(record)
    return records


def verify_backend_and_ledgers(root: Path) -> dict[str, Any]:
    jsonl_path = project_file(root, "backend/records.jsonl")
    csv_path = project_file(root, "backend/records.csv")
    jsonl_bytes = jsonl_path.read_bytes()
    jsonl_lines = jsonl_bytes.splitlines(keepends=True)
    if len(jsonl_lines) < MINIMUM_RECORD_COUNT:
        raise RuntimeError("backend has fewer rows than the immutable Unit 16 JSONL prefix")
    jsonl_prefix = b"".join(jsonl_lines[:MINIMUM_RECORD_COUNT])
    if (
        len(jsonl_prefix) != UNIT16_JSONL_PREFIX_BYTES
        or sha256_bytes(jsonl_prefix) != UNIT16_JSONL_PREFIX_SHA256
    ):
        raise RuntimeError("immutable public Units 1--16 JSONL prefix changed")

    csv_bytes = csv_path.read_bytes()
    csv_lines = csv_bytes.splitlines(keepends=True)
    if len(csv_lines) < UNIT16_CSV_PREFIX_LINES:
        raise RuntimeError("backend has fewer rows than the immutable Unit 16 CSV prefix")
    csv_prefix = b"".join(csv_lines[:UNIT16_CSV_PREFIX_LINES])
    if (
        len(csv_prefix) != UNIT16_CSV_PREFIX_BYTES
        or sha256_bytes(csv_prefix) != UNIT16_CSV_PREFIX_SHA256
    ):
        raise RuntimeError("immutable public Units 1--16 CSV prefix changed")

    records = load_backend_records(root)
    identifiers = [str(record.get("id", "")) for record in records]
    if any(not identifier for identifier in identifiers) or len(set(identifiers)) != len(
        identifiers
    ):
        raise RuntimeError("backend identifiers are empty or duplicated")

    manifest = load_json(project_file(root, "backend/MANIFEST.json"))
    if not isinstance(manifest, dict) or manifest.get("workflow") != "o011-export-backend-v19":
        raise RuntimeError("backend manifest is absent or has the wrong Unit 19 workflow")
    combined = manifest.get("combined")
    if not isinstance(combined, dict):
        raise RuntimeError("backend manifest lacks its combined census")
    expected_record_count = combined.get("record_count")
    declared_counts = combined.get("entity_counts")
    if (
        not isinstance(expected_record_count, int)
        or expected_record_count <= MINIMUM_RECORD_COUNT
        or not isinstance(declared_counts, dict)
        or len(records) != expected_record_count
    ):
        raise RuntimeError("backend record count does not extend the Unit 16 prefix exactly")

    counts = Counter(str(record.get("entity_type", "")) for record in records)
    if any(declared_counts.get(kind) != count for kind, count in counts.items()):
        raise RuntimeError("backend manifest entity census differs from JSONL")
    if counts["correction"] <= MINIMUM_CORRECTION_RECORD_COUNT:
        raise RuntimeError("backend correction-record count does not extend Unit 16")
    if counts["asset"] < MINIMUM_ASSET_RECORD_COUNT:
        raise RuntimeError("backend asset-record count regressed")
    if counts["rights"] < MINIMUM_RIGHTS_RECORD_COUNT:
        raise RuntimeError("backend rights-record count regressed")
    if count_csv_rows(csv_path) != expected_record_count:
        raise RuntimeError("backend CSV row count differs from JSONL/manifest")

    adverse = csv_rows(project_file(root, "00_control/ADVERSE_LEDGER.csv"))
    terminology = csv_rows(project_file(root, "00_control/TERMINOLOGY.csv"))
    if len(adverse) != counts["correction"] or len(adverse) <= MINIMUM_ADVERSE_ROWS:
        raise RuntimeError("adverse-ledger/backend correction closure differs")
    if len(terminology) <= MINIMUM_TERMINOLOGY_ROWS:
        raise RuntimeError("terminology ledger does not extend the Unit 16 boundary")
    adverse_ids = [row.get("id", "") for row in adverse]
    term_ids = [row.get("id", "") for row in terminology]
    if (
        any(not value for value in adverse_ids)
        or len(set(adverse_ids)) != len(adverse_ids)
        or any(not value for value in term_ids)
        or len(set(term_ids)) != len(term_ids)
    ):
        raise RuntimeError("adverse/terminology ledger IDs are empty or duplicated")
    adverse_numbers = [
        int(match.group(1))
        for value in adverse_ids
        if (match := re.fullmatch(r"O011-[A-Z]+-(\d{4})", value))
    ]
    correction_numbers = [
        int(match.group(1))
        for record in records
        if record.get("entity_type") == "correction"
        and (match := re.fullmatch(r"o011-(?:adv|corr)-(\d{4})", str(record.get("id"))))
    ]
    if (
        len(adverse_numbers) != len(adverse)
        or len(correction_numbers) != counts["correction"]
        or Counter(adverse_numbers) != Counter(correction_numbers)
    ):
        raise RuntimeError("backend/adverse correction-number closure differs")

    receipt = load_json(project_file(root, "qa/unit-19/backend.json"))
    if (
        not isinstance(receipt, dict)
        or receipt.get("status") != "pass"
        or receipt.get("combined_records") != expected_record_count
    ):
        raise RuntimeError("Unit 19 backend verification receipt is not passing/current")

    rights = {str(record["id"]): record for record in records if record.get("entity_type") == "rights"}
    asset_bindings: list[dict[str, Any]] = []
    for asset in (record for record in records if record.get("entity_type") == "asset"):
        rights_id = str(asset.get("rights_component_id", ""))
        if rights_id not in rights:
            raise RuntimeError(f"asset has no resolved rights record: {asset.get('id')}")
        path = project_file(root, str(asset.get("path", "")))
        actual = file_binding(path, root)
        if (
            actual["bytes"] != asset.get("expected_bytes")
            or actual["sha256"] != asset.get("source_sha256")
        ):
            raise RuntimeError(f"asset identity is stale: {asset.get('id')}")
        right = rights[rights_id]
        if not right.get("license") or not right.get("component_scope"):
            raise RuntimeError(f"asset rights are incomplete: {rights_id}")
        asset_bindings.append(actual)

    return {
        "records": len(records),
        "entity_counts": dict(sorted(counts.items())),
        "correction_records": counts["correction"],
        "adverse_rows": len(adverse),
        "terminology_rows": len(terminology),
        "asset_records": counts["asset"],
        "rights_records": counts["rights"],
        "immutable_unit16_prefix": {
            "records": MINIMUM_RECORD_COUNT,
            "jsonl_bytes": UNIT16_JSONL_PREFIX_BYTES,
            "jsonl_sha256": UNIT16_JSONL_PREFIX_SHA256,
            "csv_lines": UNIT16_CSV_PREFIX_LINES,
            "csv_bytes": UNIT16_CSV_PREFIX_BYTES,
            "csv_sha256": UNIT16_CSV_PREFIX_SHA256,
            "preserved_byte_identically": True,
        },
        "asset_bindings": asset_bindings,
        "status": "pass",
    }

def verify_rights_surfaces(root: Path) -> dict[str, Any]:
    rights_path = project_file(root, "authority/brenner_media_rights_manifest.csv")
    rows = csv_rows(rights_path)
    if len(rows) != EXPECTED_MEDIA_RIGHTS_ROWS:
        raise RuntimeError("frozen media-rights ledger row count differs")
    required_fields = {
        "title",
        "bytes",
        "mime",
        "license",
        "original_url",
        "description_url",
    }
    if not rows or not required_fields.issubset(rows[0]):
        raise RuntimeError("media-rights ledger fields are incomplete")
    for number, row in enumerate(rows, 1):
        if not all(row.get(field, "").strip() for field in required_fields):
            raise RuntimeError(f"media-rights ledger row {number} is incomplete")
        if not (row.get("artist_html", "").strip() or row.get("credit_html", "").strip()):
            public_domain = "public domain" in row.get("license", "").lower()
            attribution_not_required = row.get("attribution_required", "").lower() == "false"
            if not (public_domain and attribution_not_required):
                raise RuntimeError(
                    f"media-rights ledger row {number} lacks creator/credit disclosure"
                )
        try:
            if int(row["bytes"]) <= 0:
                raise ValueError
        except ValueError as exc:
            raise RuntimeError(f"media-rights ledger row {number} has invalid bytes") from exc

    license_text = project_file(root, "LICENSE.md").read_text(encoding="utf-8")
    normalized_license_text = " ".join(license_text.split())
    required_phrases = (
        "Creative Commons Attribution-ShareAlike 4.0 International",
        "independent adaptation",
        "Media do not inherit a blanket repository license",
        "No CC BY-NC-SA source prose is incorporated",
        MODEL_IDENTIFICATION,
    )
    missing = [
        phrase for phrase in required_phrases if phrase not in normalized_license_text
    ]
    if missing:
        raise RuntimeError("LICENSE.md lacks required rights/provenance statements")
    return {
        "text_license": "CC BY-SA 4.0",
        "media_rows": len(rows),
        "per_component_media_licensing": True,
        "non_endorsement": True,
        "model_identification": MODEL_IDENTIFICATION,
        "status": "pass",
    }


def verify_source_unit_closure(root: Path) -> dict[str, Any]:
    solution_targets: list[str] = []
    source_surfaces = 0
    for unit in range(1, 20):
        tag = f"{unit:02d}"
        required = (
            f"authority/expanded/lecture{tag}_source.de.tex",
            f"authority/expanded/worksheet{tag}_source.de.tex",
            f"source/units/unit-{tag}/lecture{tag}.id.tex",
            f"source/units/unit-{tag}/worksheet{tag}.id.tex",
        )
        for relative in required:
            project_file(root, relative)
            source_surfaces += 1
        unit_dir = root / f"source/units/unit-{tag}"
        for target in sorted(unit_dir.glob(f"worksheet{tag}_exercise*_solution.id.tex")):
            match = re.fullmatch(
                rf"worksheet{tag}_exercise(\d{{2}})_solution\.id\.tex", target.name
            )
            if match is None:
                raise RuntimeError(f"noncanonical solution filename: {target.name}")
            index = match.group(1)
            authority = root / (
                f"authority/expanded/worksheet{tag}_exercise{index}_solution_source.de.tex"
            )
            if not authority.is_file():
                raise RuntimeError(
                    f"translated solution lacks frozen authority: {target.relative_to(root)}"
                )
            solution_targets.append(target.relative_to(root).as_posix())
    if len(solution_targets) != EXPECTED_SOURCE_SOLUTIONS:
        raise RuntimeError(
            f"source-supplied solution closure differs: {len(solution_targets)}"
        )
    return {
        "units": 19,
        "required_lecture_worksheet_and_qa_surfaces": source_surfaces,
        "source_supplied_solutions": len(solution_targets),
        "solution_targets": solution_targets,
        "status": "pass",
    }


def flatten_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [str(key) for key in value] + [
            string for item in value.values() for string in flatten_strings(item)
        ]
    if isinstance(value, list):
        return [string for item in value for string in flatten_strings(item)]
    return []


def verify_required_closure(
    root: Path,
    package_manifest: dict[str, Any],
    row_map: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    required_sets = {
        "durable_controls": REQUIRED_CONTROLS,
        "authority": REQUIRED_AUTHORITY,
        "build_paths": REQUIRED_BUILD_PATHS,
        "package_documents": REQUIRED_PACKAGE_DOCUMENTS,
        "current_qa": REQUIRED_CURRENT_QA,
        "predecessor_surfaces": REQUIRED_PREDECESSOR_SURFACES,
        "backend": CANONICAL_BACKEND,
    }
    for label, relatives in required_sets.items():
        missing = [relative for relative in relatives if relative not in row_map]
        if missing:
            raise RuntimeError(f"missing {label} closure: " + ", ".join(missing))
        for relative in relatives:
            project_file(root, relative)

    if project_file(root, "00_control/GOAL_AND_WORKFLOW.md").stat().st_size < 4000:
        raise RuntimeError("durable goal/workflow is not comprehensive")
    if project_file(root, "00_control/CURRENT_STATE.md").stat().st_size < 1000:
        raise RuntimeError("durable current state is unexpectedly small")
    cursor = load_json(project_file(root, "00_control/CURSOR.json"))
    if not isinstance(cursor, dict):
        raise RuntimeError("durable cursor is not a JSON object")

    build = load_json(project_file(root, "qa/unit-19/build.json"))
    if not isinstance(build, dict) or build.get("workflow") != "o011-through-unit19-pdf-build-v1":
        raise RuntimeError("Unit 19 build receipt is missing or has the wrong workflow")
    build_inputs = validate_binding_collection(
        root, build.get("inputs"), "Unit 19 PDF transitive input", minimum=300
    )
    build_output = build.get("output")
    if (
        not isinstance(build_output, dict)
        or build_output.get("path") != CANONICAL_PDF
        or not isinstance(build_output.get("bytes"), int)
        or build_output.get("bytes") <= 0
        or not isinstance(build_output.get("sha256"), str)
        or re.fullmatch(r"[0-9a-f]{64}", build_output["sha256"]) is None
    ):
        raise RuntimeError("Unit 19 build receipt has an invalid PDF identity")

    structural = load_json(project_file(root, "qa/unit-19/pdf_structural_qa.json"))
    pages = (structural.get("pdf") or {}).get("pages") if isinstance(structural, dict) else None
    if (
        not isinstance(pages, int)
        or pages <= MINIMUM_PDF_PAGES
        or not any(
            binding.get("bytes") == build_output["bytes"]
            and binding.get("sha256") == build_output["sha256"]
            for binding in iter_bindings(structural)
        )
    ):
        raise RuntimeError("Unit 19 structural receipt does not bind an extended cumulative PDF")

    backend_manifest = load_json(project_file(root, "backend/MANIFEST.json"))
    backend_count = (
        (backend_manifest.get("combined") or {}).get("record_count")
        if isinstance(backend_manifest, dict)
        else None
    )
    if not isinstance(backend_count, int) or backend_count <= MINIMUM_RECORD_COUNT:
        raise RuntimeError("Unit 19 backend manifest does not extend the Unit 16 prefix")

    control_text = "\n".join(
        (
            project_file(root, "00_control/CURRENT_STATE.md").read_text(encoding="utf-8"),
            project_file(root, "00_control/CURSOR.json").read_text(encoding="utf-8"),
            project_file(root, "00_control/DECISION_LOG.md").read_text(encoding="utf-8"),
        )
    )
    required_control_tokens = (
        build_output["sha256"],
        str(backend_count),
        "Unit 19",
        "SOURCE_PACKAGE_INTEGRITY.json",
    )
    missing_tokens = [token for token in required_control_tokens if token not in control_text]
    if missing_tokens:
        raise RuntimeError(
            "durable controls do not yet record the finalized Unit 19 checkpoint: "
            + ", ".join(missing_tokens)
        )

    documented = "\n".join(flatten_strings(package_manifest)).lower()
    command_names = (
        "build_through_unit19.ps1",
        "export_html_v19.py",
        "verify_html_v19.py",
        "test_html_v19_pipeline.py",
        "verify_backend_v19.py",
    )
    missing_commands = [name for name in command_names if name.lower() not in documented]
    if missing_commands:
        raise RuntimeError(
            "package manifest omits clean rebuild commands: " + ", ".join(missing_commands)
        )

    html_qa = load_json(project_file(root, "qa/unit-19/HTML_READER_QA.json"))
    counts = html_qa.get("counts") if isinstance(html_qa, dict) else None
    if (
        not isinstance(counts, dict)
        or counts.get("exercises") != EXPECTED_EXERCISES
        or counts.get("source_supplied_solutions") != EXPECTED_SOURCE_SOLUTIONS
    ):
        raise RuntimeError("Unit 19 reader exercise/solution census differs")

    source = verify_source_unit_closure(root)
    backend = verify_backend_and_ledgers(root)
    rights = verify_rights_surfaces(root)
    return {
        "required_sets": {label: len(values) for label, values in required_sets.items()},
        "source": source,
        "backend_and_ledgers": backend,
        "rights": rights,
        "transitive_pdf_build_inputs": build_inputs,
        "pdf_pages": pages,
        "documented_commands": list(command_names),
        "durable_controls_bind_finalized_checkpoint": True,
        "status": "pass",
    }

def parse_outer_checksums(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        if not line:
            continue
        match = re.fullmatch(r"([0-9a-fA-F]{64})  (.+)", line)
        if match is None:
            raise RuntimeError(f"invalid {OUTER_CHECKSUMS} row {number}")
        digest, name = match.groups()
        BASE.safe_relative_path(name)
        if name in result:
            raise RuntimeError(f"duplicate {OUTER_CHECKSUMS} path: {name}")
        result[name] = digest.lower()
    return result


def verify_outer_release(
    root: Path, release_dir: Path, source_zip: Path
) -> tuple[dict[str, Any], Path, Path]:
    manifest_path = project_file(
        root, f"{release_dir.relative_to(root).as_posix()}/{OUTER_MANIFEST}"
    )
    checksums_path = project_file(
        root, f"{release_dir.relative_to(root).as_posix()}/{OUTER_CHECKSUMS}"
    )
    manifest = load_json(manifest_path)
    if not isinstance(manifest, dict):
        raise RuntimeError("outer release manifest is not a JSON object")
    if manifest.get("schema_version") != 1:
        raise RuntimeError("outer release manifest schema version differs")
    rows = manifest.get("files")
    if not isinstance(rows, list) or len(rows) != 5:
        raise RuntimeError("outer release manifest must bind exactly five payload files")
    expected_first_five = (
        STAGED_PDF_NAME,
        STAGED_HTML_NAME,
        STAGED_SOURCE_NAME,
        OUTER_LICENSE,
        OUTER_NOTES,
    )
    if tuple(row.get("path") for row in rows if isinstance(row, dict)) != expected_first_five:
        raise RuntimeError("outer release manifest payload order differs")
    public_order = manifest.get("public_file_order")
    expected_order = list(expected_first_five) + [OUTER_MANIFEST, OUTER_CHECKSUMS]
    if public_order != expected_order:
        raise RuntimeError("outer release public-file order differs")

    release_relative = release_dir.relative_to(root).as_posix()
    verified: dict[str, Any] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise RuntimeError("invalid outer release manifest row")
        name = str(row.get("path", ""))
        actual = file_binding(project_file(root, f"{release_relative}/{name}"))
        if row.get("bytes") != actual["bytes"] or str(row.get("sha256", "")).lower() != actual["sha256"]:
            raise RuntimeError(f"outer release manifest identity mismatch: {name}")
        verified[name] = actual
    if file_binding(source_zip) != verified[STAGED_SOURCE_NAME]:
        raise RuntimeError("declared source ZIP differs from the outer release manifest")

    checksums = parse_outer_checksums(checksums_path)
    expected_checksum_names = set(expected_first_five) | {OUTER_MANIFEST}
    if set(checksums) != expected_checksum_names:
        raise RuntimeError("outer checksum inventory differs")
    for name, digest in checksums.items():
        actual_path = project_file(root, f"{release_relative}/{name}")
        if sha256_file(actual_path) != digest:
            raise RuntimeError(f"outer checksum identity mismatch: {name}")

    return (
        {
            "manifest": file_binding(manifest_path, root),
            "checksums": file_binding(checksums_path, root),
            "verified_artifacts": verified,
            "public_file_order": expected_order,
            "status": "pass",
        },
        release_dir / STAGED_PDF_NAME,
        release_dir / STAGED_HTML_NAME,
    )


def tree_inventory(directory: Path) -> list[dict[str, Any]]:
    return BASE.tree_inventory(directory)


def inventory_digest(inventory: list[dict[str, Any]]) -> str:
    return BASE.inventory_digest(inventory)


def serialize_html_tree(directory: Path, output: Path) -> None:
    BASE.serialize_html_tree(directory, output)


def verify_html_zip_against_inventory(
    html_zip: Path, inventory: list[dict[str, Any]]
) -> dict[str, Any]:
    return BASE.verify_html_zip_against_inventory(html_zip, inventory)


def compare_binding(actual: dict[str, Any], expected: dict[str, Any], label: str) -> None:
    if actual.get("bytes") != expected.get("bytes") or actual.get("sha256") != expected.get("sha256"):
        raise RuntimeError(f"{label} identity differs: actual={actual}, expected={expected}")


def command_environment() -> dict[str, str]:
    env = os.environ.copy()
    env.update(
        {
            "PYTHONHASHSEED": "0",
            "SOURCE_DATE_EPOCH": "1787702400",
            "NO_PROXY": "*",
            "no_proxy": "*",
            "HTTP_PROXY": "http://127.0.0.1:9",
            "HTTPS_PROXY": "http://127.0.0.1:9",
            "ALL_PROXY": "http://127.0.0.1:9",
        }
    )
    return env


def run_command(
    command: list[str], root: Path, label: str, timeout_seconds: int
) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        cwd=root,
        env=command_environment(),
        capture_output=True,
        text=False,
        timeout=timeout_seconds,
        check=False,
    )
    if completed.returncode != 0:
        tail = (completed.stderr or completed.stdout)[-5000:].decode(
            "utf-8", errors="replace"
        )
        tail = tail.replace(str(root), "<extraction-root>")
        raise RuntimeError(f"{label} failed with {completed.returncode}: {tail}")
    return {
        "label": label,
        "status": "pass",
        "returncode": 0,
        "stdout_bytes": len(completed.stdout),
        "stderr_bytes": len(completed.stderr),
    }


def choose_powershell() -> str:
    executable = shutil.which("pwsh") or shutil.which("powershell")
    if executable is None:
        raise RuntimeError("neither pwsh nor powershell is available")
    return executable


def build_canonical(root: Path, staged_pdf: Path, staged_html_zip: Path) -> dict[str, Any]:
    canonical_pdf = file_binding(project_file(root, CANONICAL_PDF))
    compare_binding(canonical_pdf, file_binding(staged_pdf), "canonical/staged PDF")
    html_root = BASE.project_directory(root, CANONICAL_HTML_ROOT)
    html_inventory = tree_inventory(html_root)
    html_zip = verify_html_zip_against_inventory(staged_html_zip, html_inventory)
    backend = {relative: file_binding(project_file(root, relative)) for relative in CANONICAL_BACKEND}
    qa = {
        relative: file_binding(project_file(root, relative))
        for relative in (
            "qa/unit-19/build.json",
            "qa/unit-19/pdf_structural_qa.json",
            "qa/unit-19/PDF_VISUAL_QA.json",
            "qa/unit-19/HTML_READER_QA.json",
            "qa/unit-19/HTML_BROWSER_QA.json",
            "qa/unit-19/backend.json",
        )
    }
    return {
        "pdf": canonical_pdf,
        "staged_pdf": file_binding(staged_pdf),
        "html_inventory": html_inventory,
        "html": {
            "files": len(html_inventory),
            "bytes": sum(item["bytes"] for item in html_inventory),
            "inventory_sha256": inventory_digest(html_inventory),
            "staged_zip": html_zip,
        },
        "backend": backend,
        "qa": qa,
    }


def rebuild_once(
    extracted_root: Path,
    cycle: int,
    canonical: dict[str, Any],
    staged_pdf: Path,
    staged_html_zip: Path,
    timeout_seconds: int,
) -> dict[str, Any]:
    commands: list[dict[str, Any]] = []
    powershell = choose_powershell()
    commands.append(
        run_command(
            [
                powershell,
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(extracted_root / "scripts/build_through_unit19.ps1"),
            ],
            extracted_root,
            "PDF build (two clean TeX cycles plus structural verifier)",
            timeout_seconds,
        )
    )

    html_output = extracted_root / CANONICAL_HTML_ROOT
    commands.append(
        run_command(
            [
                sys.executable,
                str(extracted_root / "scripts/export_html_v19.py"),
                "--root",
                str(extracted_root),
                "--output",
                str(html_output),
                "--replace",
            ],
            extracted_root,
            "HTML export (two deterministic staging cycles)",
            timeout_seconds,
        )
    )
    commands.append(
        run_command(
            [
                sys.executable,
                str(extracted_root / "scripts/verify_html_v19.py"),
                "--root",
                str(extracted_root),
                "--output",
                str(html_output),
                "--receipt",
                str(extracted_root / "qa/unit-19/HTML_READER_QA.json"),
            ],
            extracted_root,
            "HTML verifier (independent two-cycle reconstruction)",
            timeout_seconds,
        )
    )
    commands.append(
        run_command(
            [sys.executable, str(extracted_root / "scripts/test_html_v19_pipeline.py")],
            extracted_root,
            "bounded HTML pipeline regression",
            timeout_seconds,
        )
    )
    commands.append(
        run_command(
            [
                sys.executable,
                str(extracted_root / "scripts/verify_backend_v19.py"),
                "--root",
                str(extracted_root),
            ],
            extracted_root,
            "backend verifier (two deterministic exports)",
            timeout_seconds,
        )
    )

    pdf = file_binding(project_file(extracted_root, CANONICAL_PDF))
    compare_binding(pdf, canonical["pdf"], "rebuilt PDF/canonical PDF")
    compare_binding(pdf, file_binding(staged_pdf), "rebuilt PDF/staged PDF")

    rebuilt_html_root = BASE.project_directory(extracted_root, CANONICAL_HTML_ROOT)
    html_inventory = tree_inventory(rebuilt_html_root)
    if html_inventory != canonical["html_inventory"]:
        raise RuntimeError("rebuilt HTML tree differs from the canonical Unit 19 tree")
    html_zip_check = verify_html_zip_against_inventory(staged_html_zip, html_inventory)
    replica_zip = extracted_root / "tmp/unit19-html-rebuilt.zip"
    replica_zip.parent.mkdir(parents=True, exist_ok=True)
    serialize_html_tree(rebuilt_html_root, replica_zip)
    compare_binding(
        file_binding(replica_zip),
        file_binding(staged_html_zip),
        "deterministically serialized rebuilt HTML/staged HTML ZIP",
    )

    backend: dict[str, Any] = {}
    for relative in CANONICAL_BACKEND:
        rebuilt = file_binding(project_file(extracted_root, relative))
        compare_binding(rebuilt, canonical["backend"][relative], f"rebuilt {relative}")
        backend[relative] = rebuilt
    rebuilt_backend = verify_backend_and_ledgers(extracted_root)

    qa: dict[str, Any] = {}
    for relative in canonical["qa"]:
        rebuilt = file_binding(project_file(extracted_root, relative))
        compare_binding(rebuilt, canonical["qa"][relative], f"rebuilt/static {relative}")
        qa[relative] = rebuilt
    return {
        "cycle": cycle,
        "status": "pass",
        "commands": commands,
        "outputs": {
            "pdf": pdf,
            "html_tree": {
                "files": len(html_inventory),
                "bytes": sum(item["bytes"] for item in html_inventory),
                "inventory_sha256": inventory_digest(html_inventory),
            },
            "html_zip": html_zip_check,
            "backend": backend,
            "backend_census": rebuilt_backend,
            "qa": qa,
        },
    }


def clean_rebuild(
    source_zip: Path,
    cycle: int,
    canonical: dict[str, Any],
    staged_pdf: Path,
    staged_html_zip: Path,
    timeout_seconds: int,
) -> tuple[dict[str, Any], bool]:
    temporary_root = Path(tempfile.mkdtemp(prefix=f"o011-u19-{cycle}-"))
    extracted_root = temporary_root / "source"
    try:
        BASE.safe_extract(source_zip, extracted_root)
        result = rebuild_once(
            extracted_root,
            cycle,
            canonical,
            staged_pdf,
            staged_html_zip,
            timeout_seconds,
        )
    finally:
        shutil.rmtree(temporary_root, ignore_errors=False)
    return result, not temporary_root.exists()


def resolve_inside(root: Path, value: Path, label: str) -> Path:
    path = (value if value.is_absolute() else root / value).resolve()
    if path == root or root not in path.parents:
        raise RuntimeError(f"{label} must remain inside the project root")
    return path


def write_receipt(path: Path, value: dict[str, Any]) -> None:
    if path.exists():
        raise RuntimeError(f"refusing to overwrite source-package integrity receipt: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = canonical_json_bytes(value)
    temporary = path.with_name(path.name + ".tmp")
    if temporary.exists():
        raise RuntimeError(f"refusing to overwrite temporary source-package receipt: {temporary}")
    temporary.write_bytes(payload)
    os.replace(temporary, path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--source-zip", type=Path, default=Path(DEFAULT_SOURCE_ZIP))
    parser.add_argument("--release-dir", type=Path, default=Path(DEFAULT_RELEASE_DIR))
    parser.add_argument("--receipt", type=Path, default=Path(DEFAULT_RECEIPT))
    parser.add_argument(
        "--command-timeout-seconds",
        type=int,
        default=1800,
        help="per-command timeout; this does not weaken or skip any rebuild",
    )
    args = parser.parse_args()
    if args.command_timeout_seconds < 60:
        raise RuntimeError("command timeout must be at least 60 seconds")
    root = args.root.resolve()
    source_zip = resolve_inside(root, args.source_zip, "source ZIP")
    release_dir = resolve_inside(root, args.release_dir, "release directory")
    receipt_path = resolve_inside(root, args.receipt, "receipt")
    if not source_zip.is_file():
        raise RuntimeError(
            f"Unit 19 source ZIP is not staged yet at the expected path: {source_zip}"
        )
    if source_zip.name != STAGED_SOURCE_NAME:
        raise RuntimeError("Unit 19 source ZIP has the wrong filename")
    if not release_dir.is_dir() or source_zip.parent != release_dir:
        raise RuntimeError("Unit 19 source ZIP is not in the declared release directory")

    zip_validation, package_manifest, row_map = BASE.verify_zip_and_manifest(source_zip)
    privacy = BASE.verify_privacy(
        source_zip, sorted(row_map) + [EMBEDDED_MANIFEST, EMBEDDED_CHECKSUMS]
    )

    inspection_root = Path(tempfile.mkdtemp(prefix="o011-u19-inspect-"))
    extracted_inspection = inspection_root / "source"
    try:
        BASE.safe_extract(source_zip, extracted_inspection)
        required_closure = verify_required_closure(
            extracted_inspection, package_manifest, row_map
        )
    finally:
        shutil.rmtree(inspection_root, ignore_errors=False)
    if inspection_root.exists():
        raise RuntimeError("inspection extraction root was not removed")

    outer_release, staged_pdf, staged_html_zip = verify_outer_release(
        root, release_dir, source_zip
    )
    canonical = build_canonical(root, staged_pdf, staged_html_zip)
    canonical_receipt = {
        "pdf": canonical["pdf"],
        "staged_pdf": canonical["staged_pdf"],
        "html": canonical["html"],
        "backend": canonical["backend"],
        "qa": canonical["qa"],
    }

    clean_rebuilds: list[dict[str, Any]] = []
    cleanup_results: list[bool] = []
    for cycle in (1, 2):
        result, removed = clean_rebuild(
            source_zip,
            cycle,
            canonical,
            staged_pdf,
            staged_html_zip,
            args.command_timeout_seconds,
        )
        clean_rebuilds.append(result)
        cleanup_results.append(removed)
    if not all(cleanup_results):
        raise RuntimeError("one or more clean extraction roots were not removed")

    first = clean_rebuilds[0]["outputs"]
    second = clean_rebuilds[1]["outputs"]
    cross_cycle_identity = {
        "pdf": first["pdf"] == second["pdf"],
        "html_tree": first["html_tree"] == second["html_tree"],
        "html_zip": first["html_zip"] == second["html_zip"],
        "backend": first["backend"] == second["backend"],
        "backend_census": first["backend_census"] == second["backend_census"],
        "qa_receipts": first["qa"] == second["qa"],
    }
    if not all(cross_cycle_identity.values()):
        raise RuntimeError("the two independent clean reconstructions differ")

    checks = {
        "zip_crc_and_manifest_identity": True,
        "embedded_checksums_complete": True,
        "deterministic_member_order_and_timestamps": True,
        "safe_regular_members_only": True,
        "privacy_and_credentials_absent": True,
        "durable_controls_complete_and_current": True,
        "source_authority_translation_solution_closure_complete": True,
        "text_and_per_component_media_rights_complete": True,
        "immutable_unit16_backend_prefix_preserved": True,
        "backend_record_and_correction_closure": True,
        "adverse_and_terminology_ledger_closure": True,
        "two_independent_clean_extractions": True,
        "pdf_matches_staged_canonical": True,
        "html_tree_and_zip_match_staged_canonical": True,
        "backend_and_receipts_match_staged_canonical": True,
        "cross_cycle_identity": True,
        "temporary_directories_removed": True,
        "network_not_used": True,
    }
    if not all(checks.values()):
        raise RuntimeError("internal verifier check aggregation failed")

    receipt = {
        "schema_version": SCHEMA_VERSION,
        "workflow": WORKFLOW,
        "status": "pass",
        "verifier": file_binding(Path(__file__).resolve(), root),
        "source_zip": {
            "path": source_zip.relative_to(root).as_posix(),
            "filename": source_zip.name,
            **file_binding(source_zip),
        },
        "zip_validation": zip_validation,
        "privacy": privacy,
        "required_closure": required_closure,
        "outer_release": outer_release,
        "canonical": canonical_receipt,
        "clean_rebuilds": clean_rebuilds,
        "cross_cycle_identity": cross_cycle_identity,
        "checks": checks,
    }
    write_receipt(receipt_path, receipt)
    output = {
        "status": "pass",
        "receipt": file_binding(receipt_path, root),
        "source_zip": receipt["source_zip"],
        "clean_rebuilds": len(clean_rebuilds),
        "temporary_directories_removed": True,
    }
    print(json.dumps(output, ensure_ascii=True, sort_keys=True))


if __name__ == "__main__":
    main()
