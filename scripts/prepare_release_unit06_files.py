#!/usr/bin/env python3
"""Create and validate the six-file reader-first Unit 6 release inventory."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import zipfile
from pathlib import Path
from pathlib import PurePosixPath


PDF_RELATIVE = "output/pdf/geometri-diferensial-manifold-mulus-hingga-unit-06-id.pdf"
ZIP_RELATIVE = "output/zenodo/geometri-diferensial-manifold-mulus-brenner-id-unit06-20260822.zip"
LICENSE_RELATIVE = "qa/unit-06/LICENSE_RELEASE_UNIT06.md"
NOTES_RELATIVE = "qa/unit-06/RELEASE_NOTES_20260822.md"
MODEL_IDENTIFICATION = "OpenAI Codex gpt-5.6-sol, Ultra"
EXPECTED_CONTRIBUTORS = [
    {"name": "TTP", "type": "Other"},
    {"name": "Codex (OpenAI), at the user's direction", "type": "Other"},
]
LANE_CAP_BYTES = 500_000_000
PRIVATE_LOCATOR = re.compile(rb"[A-Za-z]:[\\/]+Users[\\/]+", re.IGNORECASE)
ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
SOURCE_PACKAGE_WORKFLOW = "o011-stage-zenodo-unit06-v1"


def digest(path: Path, algorithm: str) -> str:
    value = hashlib.new(algorithm)
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def verify_source_package(root: Path, zip_path: Path, receipt_path: Path) -> dict:
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    package = receipt.get("package") or {}
    privacy = receipt.get("privacy_scan") or {}
    if (
        receipt.get("schema_version") != 1
        or receipt.get("workflow") != SOURCE_PACKAGE_WORKFLOW
        or receipt.get("status") != "pass"
        or not package.get("reproducible_second_serialization")
        or privacy.get("private_locator_hits") != 0
        or privacy.get("personal_contributor_wording_hits") != 0
        or privacy.get("credential_like_content_hits") != 0
        or privacy.get("historical_publication_receipts_excluded") is not True
    ):
        raise SystemExit("source-package receipt is not a passing deterministic boundary")
    if (
        package.get("archive_bytes") != zip_path.stat().st_size
        or package.get("archive_sha256") != digest(zip_path, "sha256")
    ):
        raise SystemExit("source-package ZIP identity differs from its staging receipt")
    required = {
        "README.md",
        "LICENSE.md",
        "RELEASE_NOTES_20260822.md",
        "PACKAGE_MANIFEST.json",
        "PACKAGE_CHECKSUMS.sha256",
        "backend/records.jsonl",
        "backend/records.csv",
        "backend/MANIFEST.json",
        "authority/brenner_media_rights_manifest.csv",
        "source/units/unit-06/lecture06.id.tex",
        "qa/unit-06/POST_REPAIR_MATH_QA.json",
        "qa/unit-06/pdf_structural_qa.json",
    }
    forbidden_fragments = (
        ".git/",
        "tmp/",
        "authority/exports/",
        "authority/mediawiki/",
        "authority/pdf/",
        "__pycache__/",
    )
    with zipfile.ZipFile(zip_path, "r") as bundle:
        if bundle.testzip() is not None:
            raise SystemExit("source-package ZIP CRC verification failed")
        infos = bundle.infolist()
        names = [item.filename for item in infos]
        if names != sorted(names) or len(names) != len(set(names)):
            raise SystemExit("source-package ZIP order or uniqueness mismatch")
        if not required.issubset(names):
            raise SystemExit("source-package ZIP is missing required reader/backend/provenance files")
        for info in infos:
            parsed = PurePosixPath(info.filename)
            if (
                info.filename.startswith("/")
                or "\\" in info.filename
                or ":" in info.filename
                or ".." in parsed.parts
            ):
                raise SystemExit(f"unsafe source-package member: {info.filename}")
            if info.date_time != ZIP_TIMESTAMP:
                raise SystemExit(f"non-normalized source-package timestamp: {info.filename}")
            if any(fragment in info.filename for fragment in forbidden_fragments):
                raise SystemExit(f"forbidden raw/cache tree in source package: {info.filename}")
            if info.filename.lower().endswith(".pdf"):
                raise SystemExit(f"reader or witness PDF duplicated in source package: {info.filename}")
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--source-package-receipt", type=Path, required=True)
    parser.add_argument("--expected-pdf-bytes", type=int, required=True)
    parser.add_argument("--expected-pdf-sha256", required=True)
    args = parser.parse_args()

    root = args.root.resolve()
    output = (root / args.output_dir).resolve()
    receipt = (root / args.receipt).resolve()
    if output.exists():
        raise SystemExit(f"refusing to overwrite release inventory directory: {output}")
    if receipt.exists():
        raise SystemExit(f"refusing to overwrite release staging receipt: {receipt}")
    files = (
        (
            root / PDF_RELATIVE,
            "geometri-diferensial-manifold-mulus-hingga-unit-06-id.pdf",
            "primary reader; cumulative partial edition through Lecture/Worksheet 6",
            "CC BY-SA 4.0 text/adaptation; component media retain file-specific rights",
        ),
        (
            root / ZIP_RELATIVE,
            "geometri-diferensial-manifold-mulus-brenner-id-unit06-20260822.zip",
            "compact deterministic resumable source, stable-ID backend, rights ledgers, build scripts, and QA",
            "mixed open rights exactly as documented by LICENSE.md and the embedded media-rights ledger",
        ),
        (
            root / LICENSE_RELATIVE,
            "LICENSE.md",
            "rights, attribution, component-license, computational-provenance, and non-endorsement notice",
            "license notice; CC BY-SA 4.0 text/adaptation and file-specific media rights",
        ),
        (
            root / NOTES_RELATIVE,
            "RELEASE_NOTES_20260822.md",
            "coverage, QA, accessibility, provenance, byte identity, and incompleteness disclosure",
            "CC BY-SA 4.0",
        ),
    )
    for path, _, _, _ in files:
        if not path.is_file():
            raise SystemExit(f"required release file missing: {path}")
    source_package_receipt = verify_source_package(
        root,
        files[1][0],
        (root / args.source_package_receipt).resolve(),
    )
    pdf = files[0][0]
    if (
        pdf.stat().st_size != args.expected_pdf_bytes
        or digest(pdf, "sha256") != args.expected_pdf_sha256.lower()
    ):
        raise SystemExit("primary PDF identity does not match the settled release boundary")
    for path in (files[2][0], files[3][0]):
        data = path.read_bytes()
        if MODEL_IDENTIFICATION.encode("utf-8") not in data:
            raise SystemExit(f"exact model provenance missing: {path.name}")
        if PRIVATE_LOCATOR.search(data):
            raise SystemExit(f"private locator detected: {path.name}")
        if b"TTP" in data or b"Translation and Transcription Project" in data:
            raise SystemExit(f"umbrella label leaked into public descriptive file: {path.name}")
    license_text = files[2][0].read_text(encoding="utf-8")
    for phrase in (
        "Creative Commons Attribution-ShareAlike 4.0 International",
        "Media do not inherit a blanket repository license",
        "Parallel transport sphere2.svg",
        "CC BY-SA 3.0",
        MODEL_IDENTIFICATION,
    ):
        if phrase not in license_text:
            raise SystemExit(f"Unit 6 license disclosure missing: {phrase}")
    zenodo_metadata = json.loads((root / "qa/unit-06/ZENODO_METADATA.json").read_text(encoding="utf-8"))["metadata"]
    title_description = str(zenodo_metadata.get("title") or "") + str(zenodo_metadata.get("description") or "")
    if "TTP" in title_description or "Translation and Transcription Project" in title_description:
        raise SystemExit("organization label leaked into Zenodo title or description")
    if zenodo_metadata.get("contributors") != EXPECTED_CONTRIBUTORS:
        raise SystemExit("Zenodo contributor boundary mismatch")
    if MODEL_IDENTIFICATION not in title_description:
        raise SystemExit("exact model provenance missing from Zenodo description")
    if zenodo_metadata.get("license") != "other-open" or zenodo_metadata.get("access_right") != "open":
        raise SystemExit("Zenodo mixed-open-rights metadata mismatch")

    rows: list[dict[str, str | int]] = []
    for path, name, role, rights in files:
        rows.append(
            {
                "filename": name,
                "role": role,
                "bytes": path.stat().st_size,
                "sha256": digest(path, "sha256"),
                "md5": digest(path, "md5"),
                "rights_scope": rights,
            }
        )
    substantive_bytes = sum(int(row["bytes"]) for row in rows)
    if substantive_bytes >= LANE_CAP_BYTES:
        raise SystemExit("release payload is not below the 500 MB lane cap")

    output.mkdir(parents=True)
    manifest = output / "FILE_MANIFEST.csv"
    with manifest.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=("filename", "role", "bytes", "sha256", "md5", "rights_scope"),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)
    checksums = output / "CHECKSUMS.sha256"
    checksum_rows = [(str(row["sha256"]), str(row["filename"])) for row in rows]
    checksum_rows.append((digest(manifest, "sha256"), manifest.name))
    checksums.write_text(
        "".join(f"{value}  {name}\n" for value, name in checksum_rows),
        encoding="ascii",
        newline="\n",
    )

    public_rows = rows + [
        {
            "filename": manifest.name,
            "role": "public release file manifest",
            "bytes": manifest.stat().st_size,
            "sha256": digest(manifest, "sha256"),
            "md5": digest(manifest, "md5"),
            "rights_scope": "factual metadata",
        },
        {
            "filename": checksums.name,
            "role": "public SHA-256 checksum list",
            "bytes": checksums.stat().st_size,
            "sha256": digest(checksums, "sha256"),
            "md5": digest(checksums, "md5"),
            "rights_scope": "factual metadata",
        },
    ]
    public_payload_bytes = sum(int(row["bytes"]) for row in public_rows)
    if public_payload_bytes >= LANE_CAP_BYTES:
        raise SystemExit("complete six-file release payload is not below the 500 MB lane cap")
    result = {
        "schema_version": 1,
        "workflow": "o011-prepare-release-unit06-v1",
        "status": "pass",
        "coverage": "active_partial_through_unit_06",
        "reader_first": public_rows[0]["filename"].endswith(".pdf"),
        "public_file_count": len(public_rows),
        "substantive_payload_bytes": substantive_bytes,
        "public_payload_bytes": public_payload_bytes,
        "lane_cap_bytes": LANE_CAP_BYTES,
        "source_package": source_package_receipt["package"],
        "source_package_receipt": {
            "path": (root / args.source_package_receipt).resolve().relative_to(root).as_posix(),
            "bytes": (root / args.source_package_receipt).resolve().stat().st_size,
            "sha256": digest((root / args.source_package_receipt).resolve(), "sha256"),
            "workflow": source_package_receipt["workflow"],
        },
        "source_package_privacy": source_package_receipt["privacy_scan"],
        "files": public_rows,
        "remote_state_mutated": False,
    }
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
