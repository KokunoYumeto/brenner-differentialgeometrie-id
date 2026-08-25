#!/usr/bin/env python3
"""Offline verifier for a frozen Brenner unit authority preflight."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
from pathlib import Path
from typing import Any


HTML_TAG_RE = re.compile(
    r"</?[A-Za-z][A-Za-z0-9]*\s*/?>|"
    r"<[A-Za-z][A-Za-z0-9]*(?:\s+[A-Za-z_:][-A-Za-z0-9_:.]*\s*=\s*"
    r"(?:\"[^\"]*\"|'[^']*'|[^\s\"'=<>`]+))+\s*/?>",
    re.IGNORECASE,
)


def digest(data: bytes, algorithm: str = "sha256") -> str:
    return hashlib.new(algorithm, data).hexdigest()


def graded_point_value(value: Any) -> int:
    """Parse Brenner's integer or split-point labels without losing the rubric."""
    if isinstance(value, int):
        return value
    text = str(value).strip()
    if text.isdigit():
        return int(text)
    match = re.fullmatch(r"(\d+)\s*\((\d+(?:\+\d+)+)\)", text)
    if not match:
        raise RuntimeError(f"unsupported graded point label: {value!r}")
    total = int(match.group(1))
    parts = sum(int(part) for part in match.group(2).split("+"))
    if parts != total:
        raise RuntimeError(f"inconsistent split-point label: {value!r}")
    return total


def file_check(root: Path, entry: dict[str, Any]) -> dict[str, Any]:
    path = root / entry["path"]
    data = path.read_bytes()
    actual = {"path": entry["path"], "bytes": len(data), "sha256": digest(data)}
    if actual["bytes"] != entry["bytes"] or actual["sha256"] != entry["sha256"]:
        raise RuntimeError(f"file-entry mismatch: {entry['path']}")
    return actual


def verify_request(root: Path, response: dict[str, Any], receipt: dict[str, Any]) -> None:
    file_check(root, response)
    file_check(root, receipt)
    saved = json.loads((root / receipt["path"]).read_text(encoding="utf-8"))
    if saved["response_sha256"] != response["sha256"]:
        raise RuntimeError(f"request receipt does not bind response: {response['path']}")


def verify_expansion(root: Path, expansion: dict[str, Any]) -> None:
    verify_request(root, expansion["response"], expansion["request_receipt"])
    file_check(root, expansion["sanitized_source"])
    file_check(root, expansion["sanitizer_receipt"])
    file_check(root, expansion["sanitizer"])
    receipt = json.loads(
        (root / expansion["sanitizer_receipt"]["path"]).read_text(encoding="utf-8")
    )
    if receipt["input_sha256"] != expansion["response"]["sha256"]:
        raise RuntimeError("sanitizer receipt has stale input")
    if receipt["output_sha256"] != expansion["sanitized_source"]["sha256"]:
        raise RuntimeError("sanitizer receipt has stale output")
    text = (root / expansion["sanitized_source"]["path"]).read_text(encoding="utf-8")
    if "\ufffd" in text or HTML_TAG_RE.search(text):
        raise RuntimeError(f"unsafe sanitized source: {expansion['sanitized_source']['path']}")


def verify_page_witness(root: Path, page: dict[str, Any]) -> None:
    file_check(root, page["metadata"])
    exact_entry = {
        "path": page["exact_utf8_base64_witness"],
        "bytes": (root / page["exact_utf8_base64_witness"]).stat().st_size,
        "sha256": page["exact_utf8_base64_sha256"],
    }
    file_check(root, exact_entry)
    encoded = (root / page["exact_utf8_base64_witness"]).read_text(encoding="ascii")
    decoded = base64.b64decode(encoded)
    if len(decoded) != page["source_utf8_bytes"]:
        raise RuntimeError(f"page source-byte mismatch: {page['title']}")
    if digest(decoded) != page["source_utf8_sha256"]:
        raise RuntimeError(f"page source-hash mismatch: {page['title']}")
    readable = (root / page["readable_normalized_witness"]).read_bytes()
    if len(readable) != page["readable_normalized_bytes"]:
        raise RuntimeError(f"readable witness byte mismatch: {page['title']}")
    if digest(readable) != page["readable_normalized_sha256"]:
        raise RuntimeError(f"readable witness hash mismatch: {page['title']}")


def verify_solution(root: Path, exercise: dict[str, Any]) -> None:
    if not exercise["exists"]:
        forbidden = {"metadata", "expanded_latex", "revid", "source_utf8_sha256"}
        if forbidden.intersection(exercise):
            raise RuntimeError(f"missing solution carries frozen-content fields: {exercise['exercise_index']}")
        return
    file_check(root, exercise["metadata"])
    file_check(root, exercise["exact_utf8_base64_witness"])
    file_check(root, exercise["readable_normalized_witness"])
    decoded = base64.b64decode(
        (root / exercise["exact_utf8_base64_witness"]["path"]).read_text(encoding="ascii")
    )
    if len(decoded) != exercise["source_utf8_bytes"]:
        raise RuntimeError(f"solution source-byte mismatch: {exercise['exercise_index']}")
    if digest(decoded) != exercise["source_utf8_sha256"]:
        raise RuntimeError(f"solution source-hash mismatch: {exercise['exercise_index']}")
    if digest(decoded, "sha1") != exercise["mediawiki_sha1"]:
        raise RuntimeError(f"solution MediaWiki SHA-1 mismatch: {exercise['exercise_index']}")
    verify_expansion(root, exercise["expanded_latex"])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--unit", type=int, required=True, choices=range(1, 30))
    args = parser.parse_args()
    root = args.root.resolve()
    unit = args.unit
    manifest_path = root / f"qa/unit-{unit:02d}/AUTHORITY_PREFLIGHT.json"
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes.decode("utf-8"))
    if manifest["status"] != "pass" or manifest["unit"] != unit:
        raise RuntimeError("preflight is not a PASS receipt for the requested unit")

    authority = manifest["authority"]
    for key in (
        "course_recursive_export",
        "latex_surface_recursive_export",
        "root_revision_manifest",
        "surface_revision_manifest",
    ):
        file_check(root, authority[key])
    for page in authority["pages"].values():
        verify_page_witness(root, page)
    verify_expansion(root, manifest["expansions"]["lecture"])
    verify_expansion(root, manifest["expansions"]["worksheet"])

    solutions = manifest["solutions"]
    file_check(root, solutions["query"])
    file_check(root, solutions["query_request_receipt"])
    exercises = solutions["exercises"]
    if len(exercises) != solutions["exercise_count"]:
        raise RuntimeError("exercise census length mismatch")
    indices = [item["exercise_index"] for item in exercises]
    if indices != list(range(1, len(exercises) + 1)):
        raise RuntimeError("exercise indices are not contiguous")
    supplied = [item["exercise_index"] for item in exercises if item["exists"]]
    marked = [item["exercise_index"] for item in exercises if item["solution_marker"]]
    if supplied != solutions["supplied_solution_indices"] or supplied != marked:
        raise RuntimeError("solution existence/marker/index disagreement")
    if len(supplied) != solutions["supplied_solution_count"]:
        raise RuntimeError("supplied-solution count mismatch")
    if len(exercises) - len(supplied) != solutions["missing_solution_count"]:
        raise RuntimeError("missing-solution count mismatch")
    graded = [item for item in exercises if item["root_point_marker"]]
    if len(graded) != solutions["graded_exercise_count"]:
        raise RuntimeError("graded-exercise count mismatch")
    if sum(graded_point_value(item["point_value"]) for item in graded) != solutions["point_value_total"]:
        raise RuntimeError("graded-point total mismatch")
    for exercise in exercises:
        verify_solution(root, exercise)

    media = manifest["media"]
    file_check(root, media["rights_manifest"])
    if media["current_commons_query"]:
        verify_request(
            root,
            media["current_commons_query"],
            media["current_commons_query_request_receipt"],
        )
    occurrence_count = 0
    for asset in media["assets"]:
        binary = (root / asset["binary"]["path"]).read_bytes()
        file_check(root, asset["binary"])
        if len(binary) != asset["bytes"]:
            raise RuntimeError(f"media byte mismatch: {asset['filename']}")
        if digest(binary, "sha1") != asset["commons_sha1"]:
            raise RuntimeError(f"media Commons SHA-1 mismatch: {asset['filename']}")
        if digest(binary) != asset["sha256"]:
            raise RuntimeError(f"media SHA-256 mismatch: {asset['filename']}")
        if not asset["rights_critical_fields_match"]:
            raise RuntimeError(f"media rights gate is false: {asset['filename']}")
        if asset["attribution_required"] and not asset["artist_text"]:
            raise RuntimeError(f"attributed media lacks creator: {asset['filename']}")
        if asset["license"] != "Public domain" and not asset["license_url"]:
            raise RuntimeError(f"licensed media lacks license URL: {asset['filename']}")
        occurrence_count += len(asset["occurrences"])
    if len(media["assets"]) != media["unique_asset_count"]:
        raise RuntimeError("unique media count mismatch")
    if occurrence_count != media["occurrence_count"]:
        raise RuntimeError("media occurrence count mismatch")

    if "media_closure_receipt" in manifest:
        media_receipt_entry = file_check(root, manifest["media_closure_receipt"])
        media_receipt = json.loads(
            (root / media_receipt_entry["path"]).read_text(encoding="utf-8")
        )
        if media_receipt.get("status") != "pass":
            raise RuntimeError("exact media-closure receipt is not PASS")
        if media_receipt.get("displayed_media_occurrences") != media["occurrence_count"]:
            raise RuntimeError("media-closure occurrence count differs from preflight")
        if media_receipt.get("unique_media_assets") != media["unique_asset_count"]:
            raise RuntimeError("media-closure asset count differs from preflight")
        for surface in media_receipt.get("authority_surfaces", []):
            file_check(root, surface)

    if "official_pdf_witness" in manifest:
        witness_entry = file_check(root, manifest["official_pdf_witness"])
        witness = json.loads((root / witness_entry["path"]).read_text(encoding="utf-8"))
        if (
            witness.get("status") != "pass"
            or witness.get("production_master") is not False
            or witness.get("release_asset") is not False
            or not str(witness.get("redistribution_status", "")).startswith("withheld_")
        ):
            raise RuntimeError("official PDF witness role/status is invalid")
        file_check(root, witness["metadata"])
        pdf_entry = file_check(root, witness["binary"])
        if not (root / pdf_entry["path"]).read_bytes().startswith(b"%PDF-"):
            raise RuntimeError("official PDF witness lacks a PDF header")

    if "official_pdf_structural_visual_qa" in manifest:
        visual_entry = file_check(root, manifest["official_pdf_structural_visual_qa"])
        visual = json.loads((root / visual_entry["path"]).read_text(encoding="utf-8"))
        if visual.get("status") != "pass_with_documented_witness_limitations":
            raise RuntimeError("official PDF structural/visual receipt has unexpected status")
        file_check(root, visual["source"])
        visual_authority = file_check(root, visual["authority_receipt"])
        if visual_authority != manifest["official_pdf_witness"]:
            raise RuntimeError("official PDF structural/visual receipt binds a stale authority receipt")

    if not all(
        value is True
        for key, value in manifest["checks"].items()
        if key != "translation_started_by_workflow"
    ):
        raise RuntimeError("one or more positive gate checks is false")
    if manifest["checks"]["translation_started_by_workflow"] is not False:
        raise RuntimeError("authority workflow unexpectedly claims translation")

    receipt = {
        "schema_version": 1,
        "workflow": "o011-unit-authority-offline-verifier-v1",
        "unit": unit,
        "preflight": {
            "path": manifest_path.relative_to(root).as_posix(),
            "bytes": len(manifest_bytes),
            "sha256": digest(manifest_bytes),
        },
        "root_page_witnesses_verified": len(authority["pages"]),
        "expanded_surfaces_verified": 2 + len(supplied),
        "exercise_candidates_verified": len(exercises),
        "supplied_solution_indices": supplied,
        "media_assets_verified": len(media["assets"]),
        "media_occurrences_verified": occurrence_count,
        "status": "pass",
    }
    output_path = root / f"qa/unit-{unit:02d}/AUTHORITY_PREFLIGHT_VERIFY.json"
    output_path.write_bytes(
        (json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    )
    output_bytes = output_path.read_bytes()
    print(
        json.dumps(
            {
                **receipt,
                "verification_receipt": {
                    "path": output_path.relative_to(root).as_posix(),
                    "bytes": len(output_bytes),
                    "sha256": digest(output_bytes),
                },
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
