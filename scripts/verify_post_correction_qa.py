#!/usr/bin/env python3
"""Verify a bounded per-unit POST_CORRECTION_MATH_QA receipt.

The receipt is treated as a compact content-addressed manifest.  Every nested
``path``/``bytes``/``sha256`` triple must resolve inside the project root, all
declared correction IDs must occur exactly once in the adverse ledger and in
the listed correction manifests, and every referenced translation receipt
must report ``pass``.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any, Iterator


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def path_records(value: Any) -> Iterator[dict[str, Any]]:
    if isinstance(value, dict):
        if {"path", "bytes", "sha256"}.issubset(value):
            yield value
        for child in value.values():
            yield from path_records(child)
    elif isinstance(value, list):
        for child in value:
            yield from path_records(child)


def contained_path(root: Path, relative: str) -> Path:
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise RuntimeError(f"path escapes project root: {relative}") from exc
    return candidate


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("qa", type=Path)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--adverse-ledger", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()

    root = args.project_root.resolve()
    qa_path = args.qa.resolve()
    payload = json.loads(qa_path.read_text(encoding="utf-8"))
    failures: list[str] = []

    if payload.get("status") != "pass":
        failures.append("qa_status_not_pass")
    false_checks = sorted(
        key for key, value in payload.get("checks", {}).items() if value is not True
    )
    if false_checks:
        failures.append("false_checks:" + ",".join(false_checks))

    checked: dict[str, dict[str, Any]] = {}
    for record in path_records(payload):
        relative = record["path"]
        if not isinstance(relative, str):
            failures.append("non_string_path")
            continue
        path = contained_path(root, relative)
        if not path.is_file():
            failures.append(f"missing:{relative}")
            continue
        data = path.read_bytes()
        actual = {"path": relative, "bytes": len(data), "sha256": sha256(data)}
        if actual["bytes"] != record["bytes"] or actual["sha256"] != record["sha256"]:
            failures.append(f"identity_mismatch:{relative}")
        prior = checked.get(relative)
        if prior is not None and prior != actual:
            failures.append(f"inconsistent_duplicate:{relative}")
        checked[relative] = actual

    target_receipts: list[str] = []
    targets = payload.get("targets", {})
    for target in [targets.get("lecture"), targets.get("worksheet")]:
        if isinstance(target, dict) and isinstance(target.get("translation_receipt"), str):
            target_receipts.append(target["translation_receipt"])
    for target in targets.get("supplied_solutions", []):
        if isinstance(target, dict) and isinstance(target.get("translation_receipt"), str):
            target_receipts.append(target["translation_receipt"])
    for relative in target_receipts:
        receipt_payload = json.loads(contained_path(root, relative).read_text(encoding="utf-8"))
        if receipt_payload.get("status") != "pass" or receipt_payload.get("failures"):
            failures.append(f"translation_receipt_not_pass:{relative}")

    declared = payload.get("declared_corrections", [])
    if not isinstance(declared, list) or len(declared) != len(set(declared)):
        failures.append("declared_corrections_not_unique_list")
        declared = []
    manifest_ids: list[str] = []
    for record in payload.get("correction_manifests", []):
        manifest = json.loads(contained_path(root, record["path"]).read_text(encoding="utf-8"))
        manifest_ids.extend(
            item["correction_id"]
            for item in manifest.get("corrections", [])
            if isinstance(item, dict) and isinstance(item.get("correction_id"), str)
        )
    if set(manifest_ids) != set(declared) or len(manifest_ids) != len(set(manifest_ids)):
        failures.append("correction_manifest_closure")

    with args.adverse_ledger.open(encoding="utf-8", newline="") as handle:
        ledger_ids = [row["id"] for row in csv.DictReader(handle)]
    if len(ledger_ids) != len(set(ledger_ids)):
        failures.append("adverse_ledger_duplicate_ids")
    missing_ledger = sorted(set(declared) - set(ledger_ids))
    if missing_ledger:
        failures.append("missing_ledger_ids:" + ",".join(missing_ledger))

    topology_relative = payload.get("worksheet_topology", {}).get("path")
    if isinstance(topology_relative, str):
        topology = json.loads(contained_path(root, topology_relative).read_text(encoding="utf-8"))
        if topology.get("status") != "pass" or not all(topology.get("checks", {}).values()):
            failures.append("worksheet_topology_not_pass")

    qa_bytes = qa_path.read_bytes()
    result = {
        "schema_version": 1,
        "qa": qa_path.relative_to(root).as_posix(),
        "qa_bytes": len(qa_bytes),
        "qa_sha256": sha256(qa_bytes),
        "checked_unique_path_records": len(checked),
        "checked_paths": [checked[key] for key in sorted(checked)],
        "translation_receipts_checked": target_receipts,
        "declared_correction_count": len(declared),
        "manifest_correction_count": len(manifest_ids),
        "adverse_ledger_record_count": len(ledger_ids),
        "status": "pass" if not failures else "fail",
        "failures": failures,
    }
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    if failures:
        raise RuntimeError("post-correction QA verification failed: " + ", ".join(failures))


if __name__ == "__main__":
    main()
