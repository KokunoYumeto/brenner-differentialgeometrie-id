#!/usr/bin/env python3
"""Prepare the six-file reader-first Unit 7 public payload and receipt."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from pathlib import Path


PDF_NAME = "geometri-diferensial-manifold-mulus-hingga-unit-07-id.pdf"
ZIP_NAME = "geometri-diferensial-manifold-mulus-brenner-id-unit07-20260823.zip"
LICENSE_NAME = "LICENSE.md"
NOTES_NAME = "RELEASE_NOTES_20260823.md"


def digest(path: Path, algorithm: str = "sha256") -> str:
    h = hashlib.new(algorithm)
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def identity(path: Path) -> dict[str, int | str]:
    return {"bytes": path.stat().st_size, "sha256": digest(path), "md5": digest(path, "md5")}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--staging-receipt", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve(); staging = (root / args.staging_receipt).resolve(); out = (root / args.output_dir).resolve(); receipt = (root / args.receipt).resolve()
    existing_release_files = [p for p in out.iterdir()] if out.exists() else []
    if any(p.name != "STAGING_RECEIPT.json" for p in existing_release_files):
        raise RuntimeError("refusing to overwrite non-empty release output")
    if receipt.exists():
        raise RuntimeError("refusing to overwrite release receipt")
    stage = json.loads(staging.read_text(encoding="utf-8"))
    if stage.get("status") != "pass" or stage.get("remote_state_mutated") is not False:
        raise RuntimeError("source staging receipt is not a local passing boundary")
    pdf = root / "output/pdf" / PDF_NAME
    archive = root / "output/zenodo" / ZIP_NAME
    license_src = root / "qa/unit-07/LICENSE_RELEASE_UNIT07.md"
    notes_src = root / "qa/unit-07/RELEASE_NOTES_20260823.md"
    for path in (pdf, archive, license_src, notes_src):
        if not path.is_file():
            raise RuntimeError(f"missing release input: {path}")
    out.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(pdf, out / PDF_NAME)
    shutil.copyfile(archive, out / ZIP_NAME)
    shutil.copyfile(license_src, out / LICENSE_NAME)
    shutil.copyfile(notes_src, out / NOTES_NAME)
    payload = [
        (PDF_NAME, "primary reader; cumulative partial edition through Lecture/Worksheet 7", "CC BY-SA 4.0 text/adaptation; component media retain file-specific rights"),
        (ZIP_NAME, "compact deterministic resumable source, stable-ID backend, rights ledgers, build scripts, and QA", "mixed open rights exactly as documented by LICENSE.md and embedded rights ledgers"),
        (LICENSE_NAME, "rights, attribution, component-license, computational-provenance, and non-endorsement notice", "license notice; CC BY-SA 4.0 text/adaptation and file-specific media rights"),
        (NOTES_NAME, "coverage, QA, accessibility, provenance, byte identity, and incompleteness disclosure", "CC BY-SA 4.0"),
    ]
    rows = []
    for name, role, rights in payload:
        path = out / name
        value = identity(path)
        rows.append({"filename": name, **value, "role": role, "rights_scope": rights})
    manifest = out / "FILE_MANIFEST.csv"
    with manifest.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["filename", "bytes", "sha256", "md5", "role", "rights_scope"], lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)
    checksums = out / "CHECKSUMS.sha256"
    checksums.write_text("".join(f"{row['sha256']}  {row['filename']}\n" for row in rows) + f"{digest(manifest)}  FILE_MANIFEST.csv\n", encoding="ascii", newline="\n")
    public_files = [out / row["filename"] for row in rows] + [manifest, checksums]
    public_payload = sum(path.stat().st_size for path in public_files)
    if public_payload > 500_000_000:
        raise RuntimeError("public payload exceeds 500 MB lane cap")
    result = {
        "schema_version": 1,
        "status": "pass",
        "workflow": "o011-prepare-release-unit07-v1",
        "coverage": "active_partial_through_unit_07",
        "reader_first": True,
        "lane_cap_bytes": 500_000_000,
        "public_file_count": len(public_files),
        "public_payload_bytes": public_payload,
        "substantive_payload_bytes": sum((out / row["filename"]).stat().st_size for row in rows),
        "files": [{"filename": row["filename"], "role": row["role"], "rights_scope": row["rights_scope"], **identity(out / row["filename"])} for row in rows] + [{"filename": "FILE_MANIFEST.csv", "role": "public release file manifest", "rights_scope": "factual metadata", **identity(manifest)}, {"filename": "CHECKSUMS.sha256", "role": "public SHA-256 checksum list", "rights_scope": "factual metadata", **identity(checksums)}],
        "source_package": {"archive_path": "output/zenodo/" + ZIP_NAME, **identity(archive), "staged_files": stage.get("staged_files"), "staged_bytes": stage.get("staged_bytes"), "crc_and_identity_verified": stage.get("package", {}).get("crc_and_identity_verified"), "reproducible_second_serialization": stage.get("package", {}).get("reproducible_second_serialization")},
        "source_package_receipt": {"path": args.staging_receipt.as_posix(), "sha256": digest(staging), "workflow": stage.get("workflow")},
        "remote_state_mutated": False,
    }
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
