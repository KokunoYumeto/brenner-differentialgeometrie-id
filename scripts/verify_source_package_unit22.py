#!/usr/bin/env python3
"""Verify the Unit 22 source package with two clean offline rebuilds.

The verifier checks the seven-file release, embedded package manifest and
checksums, then extracts the source archive into two unrelated temporary
directories.  Each extraction rebuilds and independently verifies the PDF,
HTML, and append-only backend without network access.  Rebuilt artifacts must
match the canonical and staged bytes exactly.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

import stage_zenodo_unit22 as S


WORKFLOW = "o011-verify-source-package-unit22-v1"
MODEL = "OpenAI Codex gpt-5.6-sol, Ultra"
DEFAULT_RELEASE = Path("output/release-unit22")
DEFAULT_SOURCE = DEFAULT_RELEASE / S.SOURCE_ZIP_NAME
DEFAULT_RECEIPT = Path("qa/unit-22/SOURCE_PACKAGE_INTEGRITY.json")
EMBEDDED_MANIFEST = "PACKAGE_MANIFEST.json"
EMBEDDED_CHECKSUMS = "PACKAGE_CHECKSUMS.sha256"
REQUIRED_MEMBERS = (
    "00_control/GOAL_AND_WORKFLOW.md",
    "00_control/CURRENT_STATE.md",
    "00_control/CURSOR.json",
    "00_control/DECISION_LOG.md",
    "00_control/ADVERSE_LEDGER.csv",
    "00_control/TERMINOLOGY.csv",
    "authority/brenner_media_rights_manifest.csv",
    "source/units/unit-22/lecture22.id.tex",
    "source/units/unit-22/worksheet22.id.tex",
    "source/units/unit-22/worksheet22_exercise06_solution.id.tex",
    "scripts/build_through_unit22.ps1",
    "scripts/verify_through_unit22_pdf.py",
    "scripts/export_html_v22.py",
    "scripts/verify_html_v22.py",
    "scripts/export_backend_v22.py",
    "scripts/verify_backend_v22.py",
    "scripts/verify_source_package_unit22.py",
    "backend/records.jsonl",
    "backend/records.csv",
    "backend/MANIFEST.json",
    "qa/unit-22/build.json",
    "qa/unit-22/pdf_structural_qa.json",
    "qa/unit-22/PDF_VISUAL_QA.json",
    "qa/unit-22/HTML_READER_QA.json",
    "qa/unit-22/HTML_BROWSER_QA.json",
    "qa/unit-22/backend.json",
    EMBEDDED_MANIFEST,
    EMBEDDED_CHECKSUMS,
)


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def identity(path: Path, relative: str | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {"bytes": path.stat().st_size, "sha256": sha256_file(path)}
    if relative is not None:
        result["path"] = relative
    return result


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_checksums(path: Path) -> dict[str, str]:
    rows: dict[str, str] = {}
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line:
            continue
        if "  " not in line:
            raise RuntimeError(f"malformed checksum row {number}: {line!r}")
        digest, name = line.split("  ", 1)
        if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
            raise RuntimeError(f"invalid SHA-256 in checksum row {number}")
        if name in rows:
            raise RuntimeError(f"duplicate checksum member: {name}")
        rows[name] = digest
    return rows


def safe_member(name: str) -> PurePosixPath:
    path = PurePosixPath(name)
    if not name or path.is_absolute() or "\\" in name or any(part in ("", ".", "..") for part in path.parts):
        raise RuntimeError(f"unsafe ZIP member path: {name!r}")
    return path


def extract_and_verify_source(source_zip: Path, destination: Path) -> dict[str, Any]:
    with zipfile.ZipFile(source_zip) as archive:
        if archive.testzip() is not None:
            raise RuntimeError("source ZIP CRC verification failed")
        infos = archive.infolist()
        names = [info.filename for info in infos]
        if len(names) != len(set(names)):
            raise RuntimeError("source ZIP contains duplicate member names")
        for info in infos:
            safe_member(info.filename)
            unix_type = (info.external_attr >> 16) & 0o170000
            if unix_type == 0o120000:
                raise RuntimeError(f"source ZIP contains a symbolic link: {info.filename}")
            target = destination.joinpath(*PurePosixPath(info.filename).parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(info))
    for name in REQUIRED_MEMBERS:
        if not (destination / name).is_file():
            raise RuntimeError(f"source package lacks required member: {name}")
    checksums = parse_checksums(destination / EMBEDDED_CHECKSUMS)
    actual_files = sorted(
        path.relative_to(destination).as_posix()
        for path in destination.rglob("*")
        if path.is_file() and path.name != EMBEDDED_CHECKSUMS
    )
    if set(checksums) != set(actual_files):
        raise RuntimeError("embedded checksum inventory does not equal the extracted file inventory")
    for name in actual_files:
        if sha256_file(destination / name) != checksums[name]:
            raise RuntimeError(f"embedded checksum mismatch: {name}")
    manifest = load_json(destination / EMBEDDED_MANIFEST)
    if manifest.get("workflow") != "o011-unit22-compact-source-package-v1":
        raise RuntimeError("embedded package manifest has the wrong workflow")
    if manifest.get("status") != "active_partial" or manifest.get("model_identification") != MODEL:
        raise RuntimeError("embedded package status/model differs")
    rows = manifest.get("files")
    if not isinstance(rows, list) or len(rows) != manifest.get("files_excluding_manifest_surfaces"):
        raise RuntimeError("embedded package manifest inventory is malformed")
    for row in rows:
        name = row.get("path") if isinstance(row, dict) else None
        if not isinstance(name, str) or not (destination / name).is_file():
            raise RuntimeError(f"embedded package manifest names an absent file: {name!r}")
        actual = identity(destination / name)
        if actual["bytes"] != row.get("bytes") or actual["sha256"] != row.get("sha256"):
            raise RuntimeError(f"embedded package manifest identity mismatch: {name}")
    return {
        "zip": identity(source_zip),
        "members": len(names),
        "uncompressed_bytes": sum(info.file_size for info in infos),
        "manifest": identity(destination / EMBEDDED_MANIFEST, EMBEDDED_MANIFEST),
        "checksums": identity(destination / EMBEDDED_CHECKSUMS, EMBEDDED_CHECKSUMS),
    }


def inventory(directory: Path) -> list[dict[str, Any]]:
    return [
        {"path": path.relative_to(directory).as_posix(), **identity(path)}
        for path in sorted((item for item in directory.rglob("*") if item.is_file()), key=lambda item: item.relative_to(directory).as_posix())
    ]


def inventory_digest(rows: list[dict[str, Any]]) -> str:
    return sha256_bytes("".join(f"{row['path']}\0{row['bytes']}\0{row['sha256']}\n" for row in rows).encode("utf-8"))


def verify_html_zip(zip_path: Path, canonical_root: Path) -> dict[str, Any]:
    expected = inventory(canonical_root)
    expected_map = {row["path"]: row for row in expected}
    with zipfile.ZipFile(zip_path) as archive:
        if archive.testzip() is not None:
            raise RuntimeError("HTML ZIP CRC verification failed")
        names = [info.filename for info in archive.infolist()]
        if len(names) != len(set(names)) or set(names) != set(expected_map):
            raise RuntimeError("HTML ZIP inventory differs from the canonical HTML tree")
        for info in archive.infolist():
            safe_member(info.filename)
            payload = archive.read(info)
            expected_row = expected_map[info.filename]
            if len(payload) != expected_row["bytes"] or sha256_bytes(payload) != expected_row["sha256"]:
                raise RuntimeError(f"HTML ZIP member differs: {info.filename}")
    return {"zip": identity(zip_path), "files": len(expected), "tree_sha256": inventory_digest(expected)}


def verify_outer_release(root: Path, release: Path) -> dict[str, Any]:
    expected_names = list(S.PUBLIC_FILE_ORDER)
    actual_names = sorted(path.name for path in release.iterdir() if path.is_file())
    if sorted(expected_names) != actual_names:
        raise RuntimeError("outer release does not contain exactly the seven declared files")
    checksums = parse_checksums(release / S.CHECKSUMS_NAME)
    if list(checksums) != expected_names[:6]:
        raise RuntimeError("outer checksum order/content differs")
    for name, digest in checksums.items():
        if sha256_file(release / name) != digest:
            raise RuntimeError(f"outer checksum mismatch: {name}")
    manifest = load_json(release / S.MANIFEST_NAME)
    if manifest.get("workflow") != "o011-unit22-public-file-manifest-v1":
        raise RuntimeError("outer manifest workflow differs")
    if manifest.get("public_file_order") != expected_names:
        raise RuntimeError("outer public-file order differs")
    rows = manifest.get("files")
    if not isinstance(rows, list) or [row.get("path") for row in rows] != expected_names[:5]:
        raise RuntimeError("outer manifest row order differs")
    for row in rows:
        actual = identity(release / row["path"])
        if actual["bytes"] != row.get("bytes") or actual["sha256"] != row.get("sha256"):
            raise RuntimeError(f"outer manifest identity mismatch: {row['path']}")
    staged_pdf = release / S.PDF_NAME
    canonical_pdf = root / S.PDF_REL
    if identity(staged_pdf) != identity(canonical_pdf):
        raise RuntimeError("staged PDF differs from the canonical Unit 22 PDF")
    html = verify_html_zip(release / S.HTML_ZIP_NAME, root / S.HTML_ROOT_REL)
    return {
        "files": [{"filename": name, **identity(release / name)} for name in expected_names],
        "total_bytes": sum((release / name).stat().st_size for name in expected_names),
        "html": html,
    }


def offline_environment() -> dict[str, str]:
    environment = os.environ.copy()
    blocked = "http://127.0.0.1:9"
    environment.update({
        "HTTP_PROXY": blocked,
        "HTTPS_PROXY": blocked,
        "ALL_PROXY": blocked,
        "http_proxy": blocked,
        "https_proxy": blocked,
        "all_proxy": blocked,
        "NO_PROXY": "localhost,127.0.0.1",
        "no_proxy": "localhost,127.0.0.1",
        "PYTHONUTF8": "1",
    })
    return environment


def run(command: list[str], cwd: Path) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=offline_environment(),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
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
        "output_sha256": sha256_bytes(output.encode("utf-8")),
    }
    if completed.returncode != 0:
        raise RuntimeError(f"clean rebuild command failed ({completed.returncode}): {' '.join(command)}\n{output[-4000:]}")
    return result


def powershell() -> str:
    executable = shutil.which("pwsh") or shutil.which("powershell")
    if not executable:
        raise RuntimeError("PowerShell is required for the clean PDF rebuild")
    return executable


def rebuild_once(extracted: Path, canonical_root: Path, staged_html: Path) -> dict[str, Any]:
    manifest = load_json(extracted / "backend/MANIFEST.json")
    checkpoint = manifest.get("checkpoint")
    units = (manifest.get("units20_22_extension") or {}).get("units")
    states = {value.get("translation_state") for value in units.values() if isinstance(value, dict)} if isinstance(units, dict) else set()
    if not isinstance(checkpoint, str) or len(states) != 1:
        raise RuntimeError("embedded backend does not expose one reproducible checkpoint/state")
    state = str(states.pop())
    commands = [
        run([powershell(), "-NoProfile", "-File", "scripts/build_through_unit22.ps1"], extracted),
        run([sys.executable, "scripts/verify_through_unit22_pdf.py"], extracted),
        run([sys.executable, "scripts/export_html_v22.py", "--root", ".", "--output", "output/html/unit-22", "--replace"], extracted),
        run([sys.executable, "scripts/verify_html_v22.py", "--root", ".", "--output", "output/html/unit-22"], extracted),
        run([sys.executable, "scripts/export_backend_v22.py", "--root", ".", "--checkpoint", checkpoint, "--translation-state", state], extracted),
        run([sys.executable, "scripts/verify_backend_v22.py", "--root", "."], extracted),
    ]
    outputs = {
        "pdf": identity(extracted / S.PDF_REL),
        "html_entry": identity(extracted / S.HTML_ENTRY_REL),
        "html_manifest": identity(extracted / S.HTML_MANIFEST_REL),
        "html_tree_sha256": inventory_digest(inventory(extracted / S.HTML_ROOT_REL)),
        "backend_jsonl": identity(extracted / "backend/records.jsonl"),
        "backend_csv": identity(extracted / "backend/records.csv"),
        "backend_manifest": identity(extracted / "backend/MANIFEST.json"),
    }
    expected = {
        "pdf": identity(canonical_root / S.PDF_REL),
        "html_entry": identity(canonical_root / S.HTML_ENTRY_REL),
        "html_manifest": identity(canonical_root / S.HTML_MANIFEST_REL),
        "html_tree_sha256": inventory_digest(inventory(canonical_root / S.HTML_ROOT_REL)),
        "backend_jsonl": identity(canonical_root / "backend/records.jsonl"),
        "backend_csv": identity(canonical_root / "backend/records.csv"),
        "backend_manifest": identity(canonical_root / "backend/MANIFEST.json"),
    }
    if outputs != expected:
        raise RuntimeError(f"clean rebuild outputs differ from canonical bytes: actual={outputs!r} expected={expected!r}")
    verify_html_zip(staged_html, extracted / S.HTML_ROOT_REL)
    return {"commands": commands, "outputs": outputs, "offline_proxy_blocking": True}


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
        raise RuntimeError("the staged Unit 22 release/source ZIP is absent")
    outer = verify_outer_release(root, release)
    cycle_results: list[dict[str, Any]] = []
    for cycle in (1, 2):
        temporary = Path(tempfile.mkdtemp(prefix=f"o011-u22-cycle{cycle}-"))
        try:
            extracted = temporary / "source"
            extracted.mkdir()
            extraction = extract_and_verify_source(source_zip, extracted)
            rebuilt = rebuild_once(extracted, root, release / S.HTML_ZIP_NAME)
            cycle_results.append({"cycle": cycle, "extraction": extraction, **rebuilt})
        finally:
            shutil.rmtree(temporary, ignore_errors=False)
    if cycle_results[0]["outputs"] != cycle_results[1]["outputs"]:
        raise RuntimeError("the two clean rebuild cycles differ")
    receipt = {
        "schema_version": 1,
        "workflow": WORKFLOW,
        "status": "pass",
        "version": S.VERSION,
        "coverage": "active_partial_through_unit_22",
        "model_identification": MODEL,
        "source_zip": identity(source_zip, source_zip.relative_to(root).as_posix()),
        "outer_release": outer,
        "clean_rebuilds": cycle_results,
        "checks": {
            "source_zip_crc_paths_manifest_and_checksums_pass": True,
            "required_resumable_source_closure_present": True,
            "two_independent_clean_extractions": True,
            "network_disabled_for_all_rebuild_commands": True,
            "pdf_rebuilt_and_independently_verified_twice": True,
            "html_rebuilt_verified_and_zip_matched_twice": True,
            "backend_rebuilt_and_independently_verified_twice": True,
            "all_rebuilt_artifacts_match_canonical_bytes": True,
            "both_clean_cycles_match_each_other": True,
            "seven_file_outer_manifest_and_checksums_pass": True,
        },
        "remote_state_mutated": False,
    }
    payload = canonical_json(receipt)
    S.B.scan_bytes("Unit 22 source-package integrity receipt", payload)
    atomic_write(receipt_path, payload)
    print(json.dumps({"status": "pass", "receipt": receipt_path.relative_to(root).as_posix(), "receipt_sha256": sha256_bytes(payload), "clean_rebuilds": 2}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
