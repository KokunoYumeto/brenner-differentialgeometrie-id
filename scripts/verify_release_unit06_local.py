#!/usr/bin/env python3
"""Verify and receipt the complete local Unit 6 reader-first release boundary."""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import re
from pathlib import Path


MODEL_IDENTIFICATION = "OpenAI Codex gpt-5.6-sol, Ultra"
LANE_CAP_BYTES = 500_000_000
SOURCE_PACKAGE_WORKFLOW = "o011-stage-zenodo-unit06-v1"
STAGING_WORKFLOW = "o011-prepare-release-unit06-v1"
EXPECTED_CONTRIBUTORS = [
    {"name": "TTP", "type": "Other"},
    {"name": "Codex (OpenAI), at the user's direction", "type": "Other"},
]
PDF_RELATIVE = "output/pdf/geometri-diferensial-manifold-mulus-hingga-unit-06-id.pdf"
ZIP_RELATIVE = "output/zenodo/geometri-diferensial-manifold-mulus-brenner-id-unit06-20260822.zip"
PUBLIC_FILES = {
    "geometri-diferensial-manifold-mulus-hingga-unit-06-id.pdf": PDF_RELATIVE,
    "geometri-diferensial-manifold-mulus-brenner-id-unit06-20260822.zip": ZIP_RELATIVE,
    "LICENSE.md": "qa/unit-06/LICENSE_RELEASE_UNIT06.md",
    "RELEASE_NOTES_20260822.md": "qa/unit-06/RELEASE_NOTES_20260822.md",
    "FILE_MANIFEST.csv": "output/release-unit06/FILE_MANIFEST.csv",
    "CHECKSUMS.sha256": "output/release-unit06/CHECKSUMS.sha256",
}
SCRIPTS = (
    "scripts/render_release_unit06_notes.py",
    "scripts/stage_zenodo_unit06.py",
    "scripts/prepare_release_unit06_files.py",
    "scripts/verify_release_unit06_local.py",
    "scripts/publish_zenodo_unit06.py",
    "scripts/verify_zenodo_public_unit06.py",
    "scripts/render_figshare_unit06_metadata.py",
    "scripts/publish_figshare_unit06_linked_reader.py",
    "scripts/verify_figshare_public_unit06_linked_reader.py",
)
PRIVATE_LOCATOR = re.compile(
    rb"[A-Za-z]:[\\/]+Users[\\/]+|(?<!:)\/Users\/|(?<![:A-Za-z0-9_])\/(?:home|srv\/home)\/[A-Za-z0-9._-]+\/|\\\\[^\\\r\n]+\\Users\\",
    re.IGNORECASE,
)
PERSONAL_CONTRIBUTOR_PATTERNS = (
    re.compile(
        rb"Codex\s*\(OpenAI\)\s*,\s*acting\s+on\s+[^\r\n]{1,120}(?:request|direction)",
        re.IGNORECASE,
    ),
    re.compile(
        rb"Codex\s*\(OpenAI\)\s*,\s*atas\s+arahan\s+(?!pengguna\b)[^\r\n]{1,120}",
        re.IGNORECASE,
    ),
)


def digest(path: Path, algorithm: str = "sha256") -> str:
    value = hashlib.new(algorithm)
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def identity(path: Path) -> dict[str, int | str]:
    return {
        "bytes": path.stat().st_size,
        "sha256": digest(path, "sha256"),
        "md5": digest(path, "md5"),
    }


def require_identity(path: Path, size: int, sha256: str, label: str) -> None:
    if path.stat().st_size != size or digest(path) != sha256.lower():
        raise SystemExit(f"{label} identity mismatch")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--source-package-receipt", type=Path, required=True)
    parser.add_argument("--release-staging-receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected-pdf-bytes", type=int, required=True)
    parser.add_argument("--expected-pdf-sha256", required=True)
    parser.add_argument("--expected-pages", type=int, required=True)
    parser.add_argument("--expected-lecture-sha256", required=True)
    parser.add_argument("--expected-build-receipt-sha256", required=True)
    parser.add_argument("--expected-math-qa-sha256", required=True)
    parser.add_argument("--expected-structural-qa-sha256", required=True)
    parser.add_argument("--expected-backend-records", type=int, required=True)
    parser.add_argument("--expected-backend-jsonl-bytes", type=int, required=True)
    parser.add_argument("--expected-backend-jsonl-sha256", required=True)
    parser.add_argument("--expected-backend-csv-bytes", type=int, required=True)
    parser.add_argument("--expected-backend-csv-sha256", required=True)
    parser.add_argument("--expected-backend-manifest-bytes", type=int, required=True)
    parser.add_argument("--expected-backend-manifest-sha256", required=True)
    parser.add_argument("--expected-backend-qa-sha256", required=True)
    args = parser.parse_args()

    root = args.root.resolve()
    output = (root / args.output).resolve()
    if output.exists():
        raise SystemExit(f"refusing to overwrite local release receipt: {output}")

    pdf = root / PDF_RELATIVE
    lecture = root / "source/units/unit-06/lecture06.id.tex"
    build_receipt = root / "qa/unit-06/build.json"
    math_qa_path = root / "qa/unit-06/POST_REPAIR_MATH_QA.json"
    structural_qa_path = root / "qa/unit-06/pdf_structural_qa.json"
    require_identity(pdf, args.expected_pdf_bytes, args.expected_pdf_sha256, "settled PDF")
    if digest(lecture) != args.expected_lecture_sha256.lower():
        raise SystemExit("final Lecture 6 source identity mismatch")
    if digest(build_receipt) != args.expected_build_receipt_sha256.lower():
        raise SystemExit("final build-receipt identity mismatch")
    if digest(math_qa_path) != args.expected_math_qa_sha256.lower():
        raise SystemExit("final math-QA identity mismatch")
    if digest(structural_qa_path) != args.expected_structural_qa_sha256.lower():
        raise SystemExit("final structural-QA identity mismatch")
    if json.loads(math_qa_path.read_text(encoding="utf-8")).get("status") != "pass":
        raise SystemExit("final math QA is not passing")
    structural_qa = json.loads(structural_qa_path.read_text(encoding="utf-8"))
    if (
        not structural_qa.get("passed")
        or structural_qa.get("pdf", {}).get("pages") != args.expected_pages
        or structural_qa.get("pdf", {}).get("bytes") != args.expected_pdf_bytes
        or structural_qa.get("pdf", {}).get("sha256") != args.expected_pdf_sha256.lower()
    ):
        raise SystemExit("final structural QA is not bound to the settled reader")

    backend_paths = {
        "records_jsonl": root / "backend/records.jsonl",
        "records_csv": root / "backend/records.csv",
        "manifest": root / "backend/MANIFEST.json",
        "qa": root / "qa/unit-06/backend.json",
    }
    require_identity(
        backend_paths["records_jsonl"],
        args.expected_backend_jsonl_bytes,
        args.expected_backend_jsonl_sha256,
        "backend JSONL",
    )
    require_identity(
        backend_paths["records_csv"],
        args.expected_backend_csv_bytes,
        args.expected_backend_csv_sha256,
        "backend CSV",
    )
    require_identity(
        backend_paths["manifest"],
        args.expected_backend_manifest_bytes,
        args.expected_backend_manifest_sha256,
        "backend manifest",
    )
    if digest(backend_paths["qa"]) != args.expected_backend_qa_sha256.lower():
        raise SystemExit("backend QA identity mismatch")
    backend_manifest = json.loads(backend_paths["manifest"].read_text(encoding="utf-8"))
    backend_qa = json.loads(backend_paths["qa"].read_text(encoding="utf-8"))
    if (
        backend_manifest.get("combined", {}).get("record_count") != args.expected_backend_records
        or backend_qa.get("status") != "pass"
        or backend_qa.get("combined_records") != args.expected_backend_records
    ):
        raise SystemExit("backend record-count or QA boundary mismatch")

    source_receipt_path = (root / args.source_package_receipt).resolve()
    source_receipt = json.loads(source_receipt_path.read_text(encoding="utf-8"))
    source_package = source_receipt.get("package") or {}
    privacy_scan = source_receipt.get("privacy_scan") or {}
    archive = root / ZIP_RELATIVE
    if (
        source_receipt.get("schema_version") != 1
        or source_receipt.get("workflow") != SOURCE_PACKAGE_WORKFLOW
        or source_receipt.get("status") != "pass"
        or not source_package.get("reproducible_second_serialization")
        or source_package.get("archive_bytes") != archive.stat().st_size
        or source_package.get("archive_sha256") != digest(archive)
        or privacy_scan.get("private_locator_hits") != 0
        or privacy_scan.get("personal_contributor_wording_hits") != 0
        or privacy_scan.get("credential_like_content_hits") != 0
        or privacy_scan.get("historical_publication_receipts_excluded") is not True
    ):
        raise SystemExit("deterministic source-package or privacy receipt mismatch")

    release_receipt_path = (root / args.release_staging_receipt).resolve()
    release_receipt = json.loads(release_receipt_path.read_text(encoding="utf-8"))
    expected_receipt_files = {
        item["filename"]: (int(item["bytes"]), str(item["sha256"]), str(item["md5"]))
        for item in release_receipt.get("files", [])
    }
    if (
        release_receipt.get("schema_version") != 1
        or release_receipt.get("workflow") != STAGING_WORKFLOW
        or release_receipt.get("status") != "pass"
        or release_receipt.get("public_file_count") != 6
        or not release_receipt.get("reader_first")
        or release_receipt.get("lane_cap_bytes") != LANE_CAP_BYTES
        or set(expected_receipt_files) != set(PUBLIC_FILES)
    ):
        raise SystemExit("public release staging receipt mismatch")
    public_identities = {}
    for name, relative in PUBLIC_FILES.items():
        path = root / relative
        actual = identity(path)
        if expected_receipt_files[name] != (
            int(actual["bytes"]),
            str(actual["sha256"]),
            str(actual["md5"]),
        ):
            raise SystemExit(f"public release identity mismatch: {name}")
        public_identities[name] = actual
    public_payload_bytes = sum(int(value["bytes"]) for value in public_identities.values())
    if (
        public_payload_bytes != int(release_receipt.get("public_payload_bytes") or -1)
        or public_payload_bytes >= LANE_CAP_BYTES
    ):
        raise SystemExit("public payload-byte total or 500 MB cap mismatch")

    manifest_path = root / PUBLIC_FILES["FILE_MANIFEST.csv"]
    with manifest_path.open("r", encoding="utf-8", newline="") as stream:
        manifest_rows = list(csv.DictReader(stream))
    if [row["filename"] for row in manifest_rows] != list(PUBLIC_FILES)[:4]:
        raise SystemExit("public manifest is not reader-first or has an unexpected inventory")
    for row in manifest_rows:
        actual = public_identities[row["filename"]]
        if (
            int(row["bytes"]) != actual["bytes"]
            or row["sha256"] != actual["sha256"]
            or row["md5"] != actual["md5"]
        ):
            raise SystemExit(f"public manifest row mismatch: {row['filename']}")
    checksums_path = root / PUBLIC_FILES["CHECKSUMS.sha256"]
    checksum_rows = {}
    for line in checksums_path.read_text(encoding="ascii").splitlines():
        value, name = line.split("  ", 1)
        checksum_rows[name] = value
    expected_checksum_rows = {
        name: str(public_identities[name]["sha256"])
        for name in list(PUBLIC_FILES)[:5]
    }
    if checksum_rows != expected_checksum_rows:
        raise SystemExit("public checksum surface mismatch")

    notes = (root / "qa/unit-06/RELEASE_NOTES_20260822.md").read_text(encoding="utf-8")
    license_text = (root / "qa/unit-06/LICENSE_RELEASE_UNIT06.md").read_text(encoding="utf-8")
    required_note_values = (
        args.expected_pdf_sha256.lower(),
        args.expected_lecture_sha256.lower(),
        args.expected_build_receipt_sha256.lower(),
        args.expected_math_qa_sha256.lower(),
        args.expected_structural_qa_sha256.lower(),
        args.expected_backend_jsonl_sha256.lower(),
        args.expected_backend_csv_sha256.lower(),
        args.expected_backend_manifest_sha256.lower(),
        args.expected_backend_qa_sha256.lower(),
        MODEL_IDENTIFICATION,
    )
    if any(value not in notes for value in required_note_values):
        raise SystemExit("release notes omit a required final identity or provenance string")
    for text, label in ((notes, "release notes"), (license_text, "license")):
        payload = text.encode("utf-8")
        if PRIVATE_LOCATOR.search(payload):
            raise SystemExit(f"private locator detected in {label}")
        if "TTP" in text or "Translation and Transcription Project" in text:
            raise SystemExit(f"organization label leaked into {label}")
    for phrase in (
        "Creative Commons Attribution-ShareAlike 4.0 International",
        "Media do not inherit a blanket repository license",
        "Parallel transport sphere2.svg",
        "CC BY-SA 3.0",
        MODEL_IDENTIFICATION,
    ):
        if phrase not in license_text:
            raise SystemExit(f"license disclosure missing: {phrase}")

    zenodo_path = root / "qa/unit-06/ZENODO_METADATA.json"
    zenodo = json.loads(zenodo_path.read_text(encoding="utf-8"))["metadata"]
    title_description = str(zenodo.get("title") or "") + str(zenodo.get("description") or "")
    if zenodo.get("contributors") != EXPECTED_CONTRIBUTORS:
        raise SystemExit("Zenodo contributor boundary mismatch")
    if (
        "TTP" in title_description
        or "Translation and Transcription Project" in title_description
        or MODEL_IDENTIFICATION not in title_description
    ):
        raise SystemExit("Zenodo title/description organization or provenance mismatch")
    figshare_template_path = root / "qa/unit-06/FIGSHARE_METADATA_TEMPLATE_20260822.json"
    figshare_template = figshare_template_path.read_text(encoding="utf-8")
    if (
        "TTP" in figshare_template
        or "Translation and Transcription Project" in figshare_template
        or MODEL_IDENTIFICATION not in figshare_template
        or any(marker not in figshare_template for marker in ("{{ZENODO_RECORD}}", "{{ZENODO_DOI}}", "{{PUBLIC_PAYLOAD_BYTES_ID}}"))
    ):
        raise SystemExit("Figshare template organization, provenance, or marker mismatch")

    public_privacy_paths = (
        pdf,
        root / "qa/unit-06/LICENSE_RELEASE_UNIT06.md",
        root / "qa/unit-06/RELEASE_NOTES_20260822.md",
        manifest_path,
        checksums_path,
        zenodo_path,
        figshare_template_path,
    )
    private_locator_hits = 0
    personal_contributor_wording_hits = 0
    for path in public_privacy_paths:
        payload = path.read_bytes()
        private_locator_hits += len(PRIVATE_LOCATOR.findall(payload))
        personal_contributor_wording_hits += sum(
            1 for pattern in PERSONAL_CONTRIBUTOR_PATTERNS for _ in pattern.finditer(payload)
        )
    if private_locator_hits or personal_contributor_wording_hits:
        raise SystemExit("public payload/metadata privacy scan failed")

    script_identities = {}
    for relative in SCRIPTS:
        path = root / relative
        ast.parse(path.read_text(encoding="utf-8"), filename=relative)
        script_identities[relative] = identity(path)

    result = {
        "schema_version": 1,
        "workflow": "o011-verify-release-unit06-local-v1",
        "status": "pass",
        "coverage": "active_partial_through_unit_06",
        "reader_first": True,
        "remote_state_mutated": False,
        "credentials_accessed": False,
        "settled_reader": {"path": PDF_RELATIVE, **identity(pdf), "pages": args.expected_pages},
        "final_bindings": {
            "lecture": {"path": "source/units/unit-06/lecture06.id.tex", **identity(lecture)},
            "build_receipt": {"path": "qa/unit-06/build.json", **identity(build_receipt)},
            "math_qa": {"path": "qa/unit-06/POST_REPAIR_MATH_QA.json", **identity(math_qa_path)},
            "structural_qa": {"path": "qa/unit-06/pdf_structural_qa.json", **identity(structural_qa_path)},
            "backend_records": args.expected_backend_records,
            "backend": {key: identity(path) for key, path in backend_paths.items()},
        },
        "source_package": source_package,
        "public_file_count": 6,
        "public_payload_bytes": public_payload_bytes,
        "lane_cap_bytes": LANE_CAP_BYTES,
        "public_files": public_identities,
        "metadata": {
            "zenodo": identity(zenodo_path),
            "figshare_template": identity(figshare_template_path),
            "zenodo_concept_record_id": 22059977,
            "figshare_article_id": 33314790,
        },
        "privacy_scan": {
            "public_payload_and_metadata_files_scanned": len(public_privacy_paths),
            "public_private_locator_hits": private_locator_hits,
            "public_personal_contributor_wording_hits": personal_contributor_wording_hits,
            "source_package": privacy_scan,
        },
        "scripts": script_identities,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
