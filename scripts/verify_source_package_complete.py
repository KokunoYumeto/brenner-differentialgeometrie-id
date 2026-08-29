#!/usr/bin/env python3
"""Verify the complete-edition source package with two clean offline restages.

The verifier checks the seven public files, safely extracts the compact source
archive twice, verifies its embedded manifest/checksums, rebuilds the complete
PDF/HTML/backend in network-blocked environments, and restages the complete
release.  Every rebuilt and restaged byte must equal the canonical release.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any

import stage_zenodo_complete as S
import verify_source_package_unit22 as U


WORKFLOW = "o011-verify-source-package-complete-v1"
MODEL = "OpenAI Codex gpt-5.6-sol, Ultra"
DEFAULT_RELEASE = Path(S.DEFAULT_OUTPUT_REL)
DEFAULT_SOURCE = DEFAULT_RELEASE / S.SOURCE_ZIP_NAME
DEFAULT_RECEIPT = Path("qa/complete/SOURCE_PACKAGE_INTEGRITY.json")
EMBEDDED_MANIFEST = "PACKAGE_MANIFEST.json"
EMBEDDED_CHECKSUMS = "PACKAGE_CHECKSUMS.sha256"
REQUIRED_MEMBERS = (
    "README.md",
    "LICENSE.md",
    "requirements-release.txt",
    "ZENODO_METADATA.json",
    "scripts/build_complete_reader.ps1",
    "scripts/verify_complete_reader.py",
    "scripts/export_html_complete.py",
    "scripts/verify_html_complete.py",
    "scripts/test_html_v19_pipeline.py",
    "scripts/export_backend_complete.py",
    "scripts/verify_backend_complete.py",
    "scripts/export_backend_v10.py",
    "scripts/verify_backend_v10.py",
    "scripts/export_backend_v19.py",
    "scripts/verify_backend_v19.py",
    "scripts/export_backend_v22.py",
    "scripts/verify_backend_v22.py",
    "scripts/stage_zenodo_unit19.py",
    "scripts/stage_zenodo_unit22.py",
    "scripts/stage_zenodo_complete.py",
    "scripts/verify_source_package_unit22.py",
    "scripts/verify_source_package_complete.py",
    "scripts/publish_zenodo_unit22.py",
    "scripts/publish_zenodo_complete.py",
    "scripts/verify_zenodo_complete_public.py",
    "backend/README.md",
    "backend/records.jsonl",
    "backend/records.csv",
    "backend/MANIFEST.json",
    "authority/brenner_media_rights_manifest.csv",
    "qa/complete/build.json",
    "qa/complete/pdf_structural_qa.json",
    "qa/complete/driver_derivation.json",
    "qa/complete/HTML_READER_QA.json",
    "qa/complete/HTML_BROWSER_QA.json",
    "qa/complete/backend.json",
    "qa/complete/LICENSE_RELEASE_COMPLETE.md",
    "qa/complete/PACKAGE_README.md",
    "qa/complete/RELEASE_NOTES_COMPLETE_20260828.md",
    "qa/complete/ZENODO_METADATA_COMPLETE.json",
    "qa/unit-10/HTML_READER_QA.json",
    "qa/unit-10/ZENODO_PUBLIC_READBACK_RECEIPT.json",
    "output/release-unit10/geometri-diferensial-manifold-mulus-brenner-id-unit10-html-20260823.zip",
    "qa/unit-13/HTML_READER_QA.json",
    "qa/unit-13/ZENODO_PUBLIC_READBACK_RECEIPT_R1.json",
    "qa/unit-13/GITHUB_PUBLIC_READBACK_RECEIPT_R1.json",
    "output/release-unit13-r1/geometri-diferensial-manifold-mulus-brenner-id-unit13-html-20260825.zip",
    "qa/unit-19/HTML_READER_QA.json",
    "qa/unit-14/lecture14_translation.json",
    "qa/unit-14/POST_CORRECTION_MATH_QA.json",
    "qa/unit-22/POST_CORRECTION_MATH_QA_VERIFY.json",
    "qa/unit-22/ZENODO_PUBLIC_READBACK_RECEIPT.json",
    EMBEDDED_MANIFEST,
    EMBEDDED_CHECKSUMS,
)


def extract_and_verify_source(source_zip: Path, destination: Path) -> dict[str, Any]:
    with zipfile.ZipFile(source_zip) as archive:
        bad_member = archive.testzip()
        if bad_member is not None:
            raise RuntimeError(f"source ZIP CRC verification failed: {bad_member}")
        infos = archive.infolist()
        names = [info.filename for info in infos]
        if len(names) != len(set(names)):
            raise RuntimeError("source ZIP contains duplicate member names")
        for info in infos:
            U.safe_member(info.filename)
            unix_type = (info.external_attr >> 16) & 0o170000
            if unix_type == 0o120000:
                raise RuntimeError(f"source ZIP contains a symbolic link: {info.filename}")
            target = destination.joinpath(*U.PurePosixPath(info.filename).parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(info))
    for name in REQUIRED_MEMBERS:
        if not (destination / name).is_file():
            raise RuntimeError(f"source package lacks required member: {name}")

    checksums = U.parse_checksums(destination / EMBEDDED_CHECKSUMS)
    actual_files = sorted(
        path.relative_to(destination).as_posix()
        for path in destination.rglob("*")
        if path.is_file() and path.name != EMBEDDED_CHECKSUMS
    )
    if set(checksums) != set(actual_files):
        missing = sorted(set(actual_files) - set(checksums))
        extra = sorted(set(checksums) - set(actual_files))
        raise RuntimeError(f"embedded checksum inventory differs: missing={missing!r} extra={extra!r}")
    for name in actual_files:
        if U.sha256_file(destination / name) != checksums[name]:
            raise RuntimeError(f"embedded checksum mismatch: {name}")

    manifest = U.load_json(destination / EMBEDDED_MANIFEST)
    if manifest.get("workflow") != "o011-complete-compact-source-backend-package-v1":
        raise RuntimeError("embedded complete-package manifest has the wrong workflow")
    if manifest.get("status") != "complete_edition" or manifest.get("model_identification") != MODEL:
        raise RuntimeError("embedded complete-package status/model differs")
    bindings = manifest.get("reader_and_backend_bindings")
    if not isinstance(bindings, dict) or bindings.get("coverage", {}).get("backend_records") != 6912:
        raise RuntimeError("embedded complete-package reader/backend binding differs")
    rows = manifest.get("files")
    if not isinstance(rows, list) or len(rows) != manifest.get("files_excluding_manifest_surfaces"):
        raise RuntimeError("embedded complete-package inventory is malformed")
    row_names: list[str] = []
    for row in rows:
        name = row.get("path") if isinstance(row, dict) else None
        if not isinstance(name, str) or not (destination / name).is_file():
            raise RuntimeError(f"embedded package manifest names an absent file: {name!r}")
        row_names.append(name)
        actual = U.identity(destination / name)
        if actual["bytes"] != row.get("bytes") or actual["sha256"] != row.get("sha256"):
            raise RuntimeError(f"embedded package manifest identity mismatch: {name}")
    if len(row_names) != len(set(row_names)) or set(row_names) != set(actual_files) - {EMBEDDED_MANIFEST}:
        raise RuntimeError("embedded package manifest file set differs from extracted content")
    return {
        "zip": U.identity(source_zip),
        "members": len(names),
        "uncompressed_bytes": sum(info.file_size for info in infos),
        "manifest": U.identity(destination / EMBEDDED_MANIFEST, EMBEDDED_MANIFEST),
        "checksums": U.identity(destination / EMBEDDED_CHECKSUMS, EMBEDDED_CHECKSUMS),
    }


def verify_outer_release(root: Path, release: Path) -> dict[str, Any]:
    expected_names = list(S.PUBLIC_FILE_ORDER)
    actual_names = sorted(path.name for path in release.iterdir() if path.is_file())
    if sorted(expected_names) != actual_names:
        raise RuntimeError("outer release does not contain exactly the seven declared complete-edition files")
    checksums = U.parse_checksums(release / S.CHECKSUMS_NAME)
    if list(checksums) != expected_names[:6]:
        raise RuntimeError("outer checksum order/content differs")
    for name, digest in checksums.items():
        if U.sha256_file(release / name) != digest:
            raise RuntimeError(f"outer checksum mismatch: {name}")
    manifest = U.load_json(release / S.MANIFEST_NAME)
    if (
        manifest.get("workflow") != "o011-complete-public-file-manifest-v1"
        or manifest.get("status") != "complete_edition"
        or manifest.get("version") != S.VERSION
        or manifest.get("title") != S.TITLE
        or manifest.get("model_identification") != MODEL
        or manifest.get("public_file_order") != expected_names
    ):
        raise RuntimeError("outer complete-edition manifest contract differs")
    rows = manifest.get("files")
    if not isinstance(rows, list) or [row.get("path") for row in rows] != expected_names[:5]:
        raise RuntimeError("outer manifest row order differs")
    for row in rows:
        actual = U.identity(release / row["path"])
        if actual["bytes"] != row.get("bytes") or actual["sha256"] != row.get("sha256"):
            raise RuntimeError(f"outer manifest identity mismatch: {row['path']}")
    if U.identity(release / S.PDF_NAME) != U.identity(root / S.PDF_REL):
        raise RuntimeError("staged PDF differs from the canonical complete PDF")
    html = U.verify_html_zip(release / S.HTML_ZIP_NAME, root / S.HTML_ROOT_REL)
    return {
        "files": [{"filename": name, **U.identity(release / name)} for name in expected_names],
        "total_bytes": sum((release / name).stat().st_size for name in expected_names),
        "html": html,
    }


def offline_environment() -> dict[str, str]:
    environment = os.environ.copy()
    blocked = "http://127.0.0.1:9"
    environment.update(
        {
            "HTTP_PROXY": blocked,
            "HTTPS_PROXY": blocked,
            "ALL_PROXY": blocked,
            "http_proxy": blocked,
            "https_proxy": blocked,
            "all_proxy": blocked,
            "NO_PROXY": "localhost,127.0.0.1",
            "no_proxy": "localhost,127.0.0.1",
            "PYTHONUTF8": "1",
        }
    )
    return environment


def run(command: list[str], cwd: Path) -> dict[str, Any]:
    completed = U.subprocess.run(
        command,
        cwd=cwd,
        env=offline_environment(),
        stdin=U.subprocess.DEVNULL,
        stdout=U.subprocess.PIPE,
        stderr=U.subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    output = completed.stdout or ""
    result = {
        "command": [Path(command[0]).name, *command[1:]],
        "exit_code": completed.returncode,
        "output_bytes": len(output.encode("utf-8")),
        "output_sha256": U.sha256_bytes(output.encode("utf-8")),
    }
    if completed.returncode != 0:
        raise RuntimeError(f"clean rebuild command failed ({completed.returncode}): {' '.join(command)}\n{output[-4000:]}")
    return result


def current_outputs(root: Path) -> dict[str, Any]:
    return {
        "pdf": U.identity(root / S.PDF_REL),
        "html_entry": U.identity(root / S.HTML_ENTRY_REL),
        "html_manifest": U.identity(root / S.HTML_MANIFEST_REL),
        "html_tree_sha256": U.inventory_digest(U.inventory(root / S.HTML_ROOT_REL)),
        "backend_jsonl": U.identity(root / "backend/records.jsonl"),
        "backend_csv": U.identity(root / "backend/records.csv"),
        "backend_manifest": U.identity(root / "backend/MANIFEST.json"),
    }


def rebuild_and_restage(extracted: Path, canonical_root: Path, canonical_release: Path) -> dict[str, Any]:
    manifest = U.load_json(extracted / "backend/MANIFEST.json")
    checkpoint = manifest.get("checkpoint")
    state = manifest.get("translation_state")
    if not isinstance(checkpoint, str) or not checkpoint or not isinstance(state, str) or not state:
        raise RuntimeError("embedded backend lacks one reproducible checkpoint/translation state")
    rebuilt_release = "output/release-complete-rebuilt"
    commands = [
        run([sys.executable, "scripts/export_html_complete.py", "--root", ".", "--output", S.HTML_ROOT_REL, "--replace"], extracted),
        run([sys.executable, "scripts/verify_html_complete.py", "--root", ".", "--output", S.HTML_ROOT_REL], extracted),
        run([sys.executable, "scripts/export_backend_complete.py", "--root", ".", "--checkpoint", checkpoint, "--translation-state", state], extracted),
        run([sys.executable, "scripts/verify_backend_complete.py", "--root", ".", "--check-only"], extracted),
        run([U.powershell(), "-NoProfile", "-File", "scripts/build_complete_reader.ps1"], extracted),
        run([sys.executable, "scripts/verify_complete_reader.py"], extracted),
        run(
            [
                sys.executable,
                "scripts/stage_zenodo_complete.py",
                "--root",
                ".",
                "--output-dir",
                rebuilt_release,
                "--receipt",
                "qa/complete/RELEASE_PREPARATION_REBUILT.json",
            ],
            extracted,
        ),
    ]
    outputs = current_outputs(extracted)
    expected = current_outputs(canonical_root)
    if outputs != expected:
        raise RuntimeError(f"clean complete-edition rebuild differs: actual={outputs!r} expected={expected!r}")
    rebuilt = extracted / rebuilt_release
    staged_files = {
        name: U.identity(rebuilt / name)
        for name in S.PUBLIC_FILE_ORDER
    }
    expected_files = {
        name: U.identity(canonical_release / name)
        for name in S.PUBLIC_FILE_ORDER
    }
    if staged_files != expected_files:
        raise RuntimeError(f"clean complete-edition restage differs: actual={staged_files!r} expected={expected_files!r}")
    return {
        "commands": commands,
        "outputs": outputs,
        "restaged_files": staged_files,
        "offline_proxy_blocking": True,
    }


def atomic_write(path: Path, payload: bytes) -> None:
    temporary = path.with_name(path.name + ".tmp")
    if path.exists() or temporary.exists():
        raise RuntimeError(f"refusing to overwrite receipt: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary.write_bytes(payload)
    os.replace(temporary, path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--release-dir", type=Path, default=DEFAULT_RELEASE)
    parser.add_argument("--source-zip", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--receipt", type=Path, default=DEFAULT_RECEIPT)
    args = parser.parse_args()
    root = args.root.resolve()
    release = (args.release_dir if args.release_dir.is_absolute() else root / args.release_dir).resolve()
    source_zip = (args.source_zip if args.source_zip.is_absolute() else root / args.source_zip).resolve()
    receipt_path = (args.receipt if args.receipt.is_absolute() else root / args.receipt).resolve()
    for path, label in ((release, "release directory"), (source_zip, "source ZIP"), (receipt_path.parent, "receipt parent")):
        if root != path and root not in path.parents:
            raise RuntimeError(f"{label} escapes the project root: {path}")
    if not release.is_dir() or not source_zip.is_file():
        raise RuntimeError("the staged complete release/source ZIP is absent")
    outer = verify_outer_release(root, release)
    cycle_results: list[dict[str, Any]] = []
    for cycle in (1, 2):
        temporary = Path(tempfile.mkdtemp(prefix=f"o011-complete-cycle{cycle}-"))
        try:
            extracted = temporary / "source"
            extracted.mkdir()
            extraction = extract_and_verify_source(source_zip, extracted)
            rebuilt = rebuild_and_restage(extracted, root, release)
            cycle_results.append({"cycle": cycle, "extraction": extraction, **rebuilt})
        finally:
            shutil.rmtree(temporary, ignore_errors=False)
    if cycle_results[0]["outputs"] != cycle_results[1]["outputs"]:
        raise RuntimeError("the two clean complete-edition rebuild cycles differ")
    if cycle_results[0]["restaged_files"] != cycle_results[1]["restaged_files"]:
        raise RuntimeError("the two clean complete-edition restages differ")
    receipt = {
        "schema_version": 1,
        "workflow": WORKFLOW,
        "status": "pass",
        "version": S.VERSION,
        "coverage": "complete_edition",
        "model_identification": MODEL,
        "source_zip": U.identity(source_zip, source_zip.relative_to(root).as_posix()),
        "outer_release": outer,
        "clean_rebuilds": cycle_results,
        "checks": {
            "source_zip_crc_paths_manifest_and_checksums_pass": True,
            "required_complete_resumable_source_closure_present": True,
            "two_independent_clean_extractions": True,
            "network_disabled_for_all_rebuild_and_restage_commands": True,
            "pdf_rebuilt_and_independently_verified_twice": True,
            "html_rebuilt_and_independently_verified_twice": True,
            "backend_rebuilt_and_independently_verified_twice": True,
            "all_rebuilt_artifacts_match_canonical_bytes": True,
            "all_seven_public_files_restaged_byte_identically_twice": True,
            "both_clean_cycles_match_each_other": True,
            "seven_file_outer_manifest_and_checksums_pass": True,
        },
        "remote_state_mutated": False,
    }
    payload = U.canonical_json(receipt)
    S.B.scan_bytes("complete source-package integrity receipt", payload)
    atomic_write(receipt_path, payload)
    print(
        json.dumps(
            {
                "status": "pass",
                "receipt": receipt_path.relative_to(root).as_posix(),
                "receipt_sha256": U.sha256_bytes(payload),
                "clean_rebuilds": 2,
                "clean_restages": 2,
                "remote_state_mutated": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
