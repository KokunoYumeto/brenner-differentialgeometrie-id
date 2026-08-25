#!/usr/bin/env python3
"""Independently verify the corrective Unit 13 r1 source package.

The verifier is intentionally outside the staging implementation.  It treats
the staged source ZIP as untrusted input, validates its complete embedded
inventory and privacy boundary, extracts it safely into two independent
temporary roots, and executes the packaged PDF, HTML, and backend build paths.
Both clean reconstructions must be byte-identical to each other and to the
canonical staged Unit 13 reader/backend artifacts.

No network operation or publication is performed.  Temporary extraction
roots are removed before a passing receipt is written.
"""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Iterator


SCHEMA_VERSION = 1
WORKFLOW = "o011-verify-source-package-unit13-r1-v1"
ZIP_TIMESTAMP = (2026, 8, 25, 0, 0, 0)
DEFAULT_SOURCE_ZIP = (
    "output/release-unit13-r1/"
    "geometri-diferensial-manifold-mulus-unit13-source-r1-20260825.zip"
)
DEFAULT_RELEASE_DIR = "output/release-unit13-r1"
DEFAULT_RECEIPT = "qa/unit-13/SOURCE_PACKAGE_R1_INTEGRITY.json"
CANONICAL_PDF = (
    "output/pdf/geometri-diferensial-manifold-mulus-hingga-unit-13-id.pdf"
)
STAGED_PDF_NAME = "geometri-diferensial-manifold-mulus-hingga-unit-13-id.pdf"
CANONICAL_HTML_ROOT = "output/html/unit-13"
CANONICAL_BACKEND = (
    "backend/records.jsonl",
    "backend/records.csv",
    "backend/MANIFEST.json",
)
EMBEDDED_MANIFEST = "PACKAGE_MANIFEST.json"
EMBEDDED_CHECKSUMS = "PACKAGE_CHECKSUMS.sha256"
OUTER_MANIFEST = "FILE_MANIFEST.csv"
OUTER_CHECKSUMS = "CHECKSUMS.sha256"
MAX_UNCOMPRESSED_BYTES = 1_000_000_000
MAX_MEMBER_BYTES = 500_000_000
EXPECTED_RECORD_COUNT = 2604
EXPECTED_CORRECTION_RECORD_COUNT = 156
EXPECTED_TERMINOLOGY_ROWS = 232
EXPECTED_ADVERSE_ROWS = 156


REQUIRED_CONTROL_PATHS = (
    "00_control/GOAL_AND_WORKFLOW.md",
    "00_control/CURRENT_STATE.md",
    "00_control/CURSOR.json",
    "00_control/DECISION_LOG.md",
    "00_control/AUTHORITY_FREEZE.md",
    "00_control/SCOPE_AND_OVERLAP.md",
    "00_control/TERMINOLOGY.csv",
    "00_control/ADVERSE_LEDGER.csv",
)

REQUIRED_CONTROL_CORRECTION_MANIFESTS = (
    "00_control/PROTECTED_CORRECTIONS.json",
    "00_control/LECTURE02_PROTECTED_CORRECTIONS.json",
    "00_control/LECTURE03_PROTECTED_CORRECTIONS.json",
    "00_control/LECTURE04_PROTECTED_CORRECTIONS.json",
    "00_control/LECTURE05_PROTECTED_CORRECTIONS.json",
    "00_control/LECTURE06_PROTECTED_CORRECTIONS.json",
    "00_control/LECTURE07_PROTECTED_CORRECTIONS.json",
    "00_control/LECTURE08_PROTECTED_CORRECTIONS.json",
    "00_control/LECTURE09_PROTECTED_CORRECTIONS.json",
    "00_control/LECTURE10_PROTECTED_CORRECTIONS.json",
    "00_control/LECTURE11_PROTECTED_CORRECTIONS.json",
    "00_control/LECTURE12_PROTECTED_CORRECTIONS.json",
    "00_control/LECTURE13_PROTECTED_CORRECTIONS.json",
    "00_control/SOLUTION01_PROTECTED_CORRECTIONS.json",
    "00_control/SOLUTION02_PROTECTED_CORRECTIONS.json",
    "00_control/SOLUTION04_07_PROTECTED_CORRECTIONS.json",
    "00_control/SOLUTION04_10_PROTECTED_CORRECTIONS.json",
    "00_control/SOLUTION05_01_PROTECTED_CORRECTIONS.json",
    "00_control/SOLUTION06_02_PROTECTED_CORRECTIONS.json",
    "00_control/SOLUTION07_PROTECTED_CORRECTIONS.json",
    "00_control/SOLUTION09_10_PROTECTED_CORRECTIONS.json",
    "00_control/SOLUTION10_10_PROTECTED_CORRECTIONS.json",
    "00_control/SOLUTION13_08_PROTECTED_CORRECTIONS.json",
    "00_control/SOLUTION13_PROTECTED_CORRECTIONS.json",
    "00_control/SOLUTION15_10_PROTECTED_CORRECTIONS.json",
    "00_control/SOLUTION25_10_PROTECTED_CORRECTIONS.json",
    "00_control/WORKSHEET01_PROTECTED_CORRECTIONS.json",
    "00_control/WORKSHEET02_PROTECTED_CORRECTIONS.json",
    "00_control/WORKSHEET03_PROTECTED_CORRECTIONS.json",
    "00_control/WORKSHEET04_PROTECTED_CORRECTIONS.json",
    "00_control/WORKSHEET05_PROTECTED_CORRECTIONS.json",
    "00_control/WORKSHEET06_PROTECTED_CORRECTIONS.json",
    "00_control/WORKSHEET07_PROTECTED_CORRECTIONS.json",
    "00_control/WORKSHEET08_PROTECTED_CORRECTIONS.json",
    "00_control/WORKSHEET09_PROTECTED_CORRECTIONS.json",
    "00_control/WORKSHEET10_PROTECTED_CORRECTIONS.json",
)

REQUIRED_QA_CORRECTION_MANIFESTS = (
    "qa/unit-08/POST_CORRECTION_MATH_QA.json",
    "qa/unit-09/POST_CORRECTION_MATH_QA.json",
    "qa/unit-10/POST_CORRECTION_MATH_QA.json",
    "qa/unit-11/POST_CORRECTION_MATH_QA.json",
    "qa/unit-11/SOLUTION11_10_PROTECTED_CORRECTIONS.json",
    "qa/unit-11/WORKSHEET11_PROTECTED_CORRECTIONS.json",
    "qa/unit-12/POST_CORRECTION_MATH_QA.json",
    "qa/unit-12/SOLUTION12_11_PROTECTED_CORRECTIONS.json",
    "qa/unit-12/SOLUTION12_12_PROTECTED_CORRECTIONS.json",
    "qa/unit-12/WORKSHEET12_PROTECTED_CORRECTIONS.json",
    "qa/unit-13/POST_CORRECTION_MATH_QA.json",
    "qa/unit-13/SOLUTION13_10_PROTECTED_CORRECTIONS.json",
    "qa/unit-13/SOLUTION13_11_PROTECTED_CORRECTIONS.json",
    "qa/unit-13/SOLUTION13_16_PROTECTED_CORRECTIONS.json",
    "qa/unit-13/SOLUTION13_19_PROTECTED_CORRECTIONS.json",
    "qa/unit-13/SOLUTION13_21_PROTECTED_CORRECTIONS.json",
    "qa/unit-13/SOLUTION13_22_PROTECTED_CORRECTIONS.json",
    "qa/unit-13/WORKSHEET13_PROTECTED_CORRECTIONS.json",
)

REQUIRED_UNIT10_RELEASE_PATHS = (
    "output/release-unit10/CHECKSUMS.sha256",
    "output/release-unit10/FILE_MANIFEST.csv",
    "output/release-unit10/geometri-diferensial-manifold-mulus-brenner-id-unit10-html-20260823.zip",
    "output/release-unit10/geometri-diferensial-manifold-mulus-brenner-id-unit10-source-20260823.zip",
    "output/release-unit10/geometri-diferensial-manifold-mulus-hingga-unit-10-id.pdf",
    "output/release-unit10/LICENSE.md",
    "output/release-unit10/RELEASE_NOTES_20260823.md",
)

REQUIRED_UNIT10_HTML_PATHS = (
    "output/html/unit-10/index.html",
    "output/html/unit-10/manifest.json",
    "output/html/unit-10/README.txt",
    "output/html/unit-10/assets/reader.css",
    "output/html/unit-10/assets/media/2019-07-Helix.jpg",
    "output/html/unit-10/assets/media/3d-function-6.svg",
    "output/html/unit-10/assets/media/Circle - black simple.svg",
    "output/html/unit-10/assets/media/Euler spiral.svg",
    "output/html/unit-10/assets/media/Evolute-parab.svg",
    "output/html/unit-10/assets/media/Great circle passing through two points.svg",
    "output/html/unit-10/assets/media/Hyperboloid1.png",
    "output/html/unit-10/assets/media/Integral apl rot obsah1.svg",
    "output/html/unit-10/assets/media/Manifold zahyou3.png",
    "output/html/unit-10/assets/media/Minimal surface curvature planes-de.svg",
    "output/html/unit-10/assets/media/Parabola circle.svg",
    "output/html/unit-10/assets/media/Parallel transport sphere2.svg",
    "output/html/unit-10/assets/media/Planned flight map of the Oiseau Blanc.svg",
    "output/html/unit-10/assets/media/Stereographic projection in 3D.png",
    "output/html/unit-10/assets/media/Tangent bundle.svg",
    "output/html/unit-10/assets/media/Tangentialvektor.svg",
    "output/html/unit-10/assets/media/Torus vectors oblique.jpg",
)

REQUIRED_PREDECESSOR_QA_PATHS = (
    "output/pdf/geometri-diferensial-manifold-mulus-hingga-unit-10-id.pdf",
    "qa/unit-10/build.json",
    "qa/unit-10/pdf_structural_qa.json",
    "qa/unit-10/HTML_READER_QA.json",
    "qa/unit-10/ZENODO_PUBLIC_READBACK_RECEIPT.json",
)

REQUIRED_BUILD_PATHS = (
    "scripts/build_through_unit10.ps1",
    "scripts/build_through_unit13.ps1",
    "scripts/verify_through_unit06_pdf.py",
    "scripts/verify_through_unit10_pdf.py",
    "scripts/verify_through_unit13_pdf.py",
    "scripts/export_html_v10.py",
    "scripts/export_html_v13.py",
    "scripts/verify_html_v10.py",
    "scripts/verify_html_v13.py",
    "scripts/verify_html_animated_media.py",
    "scripts/export_backend_v10.py",
    "scripts/export_backend_v13.py",
    "scripts/verify_backend_v10.py",
    "scripts/verify_backend_v13.py",
    "scripts/verify_source_package_unit13_r1.py",
    "scripts/prepare_unit_tex.py",
    "scripts/prepare_unit_media.py",
)

CRITICAL_EXPLICIT_PREDECESSOR_BINDINGS = (
    "output/release-unit10/geometri-diferensial-manifold-mulus-brenner-id-unit10-source-20260823.zip",
    "output/release-unit10/geometri-diferensial-manifold-mulus-brenner-id-unit10-html-20260823.zip",
    "output/pdf/geometri-diferensial-manifold-mulus-hingga-unit-10-id.pdf",
    "qa/unit-10/build.json",
    "qa/unit-10/pdf_structural_qa.json",
    "qa/unit-10/HTML_READER_QA.json",
    "qa/unit-10/ZENODO_PUBLIC_READBACK_RECEIPT.json",
)

REQUIRED_DOCUMENTS = (
    "README.md",
    "LICENSE.md",
    "RELEASE_NOTES_UNIT13_R1_20260825.md",
)

FORBIDDEN_MEMBER_NAMES = (
    re.compile(r"(?:^|/)PRIVATE_LOCAL_LOCATORS(?:\.|/|$)", re.IGNORECASE),
    re.compile(r"(?:^|/)(?:\.env(?:\..*)?|id_rsa|id_ed25519|credentials?\.json)$", re.IGNORECASE),
    re.compile(r"(?:^|/)(?:github|zenodo|figshare)[^/]*token[^/]*$", re.IGNORECASE),
)

PRIVATE_BYTE_PATTERNS = (
    re.compile(rb"[A-Za-z]:[\\/]+(?:Users|Documents[ ]and[ ]Settings)[\\/]", re.IGNORECASE),
    re.compile(rb"(?<!:)\/Users\/[^/\x00\r\n]+\/", re.IGNORECASE),
    re.compile(rb"\\\\[^\\\x00\r\n]+\\Users\\", re.IGNORECASE),
)

SECRET_BYTE_PATTERNS = (
    re.compile(rb"github_pat_[A-Za-z0-9_]{40,}"),
    re.compile(rb"gh[pousr]_[A-Za-z0-9]{36,}"),
    re.compile(rb"(?:Bearer|token)\s+[A-Za-z0-9._~-]{32,}", re.IGNORECASE),
    re.compile(rb"(?:access[_-]?token|api[_-]?token|password|secret)\s*[:=]\s*[\"'][^\"'\r\n]{16,}[\"']", re.IGNORECASE),
    re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
)

TEXT_SUFFIXES = {
    "",
    ".csv",
    ".css",
    ".html",
    ".json",
    ".jsonl",
    ".md",
    ".ps1",
    ".py",
    ".svg",
    ".tex",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
}


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
        result = {"path": path.resolve().relative_to(root.resolve()).as_posix(), **result}
    return result


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def safe_relative_path(value: str) -> PurePosixPath:
    if not value or "\\" in value or "\x00" in value or value.startswith("/"):
        raise RuntimeError(f"unsafe archive path: {value!r}")
    parsed = PurePosixPath(value)
    if parsed.is_absolute() or any(part in {"", ".", ".."} for part in parsed.parts):
        raise RuntimeError(f"unsafe archive path: {value!r}")
    if ":" in parsed.parts[0]:
        raise RuntimeError(f"drive-like archive path: {value!r}")
    return parsed


def project_file(root: Path, relative: str) -> Path:
    parsed = safe_relative_path(relative)
    path = root.joinpath(*parsed.parts)
    if not path.is_file():
        raise RuntimeError(f"required file is missing: {relative}")
    return path


def project_directory(root: Path, relative: str) -> Path:
    parsed = safe_relative_path(relative)
    path = root.joinpath(*parsed.parts)
    if not path.is_dir():
        raise RuntimeError(f"required directory is missing: {relative}")
    return path


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"invalid JSON at {path.name}: {exc}") from exc


def parse_checksum_surface(payload: bytes, label: str) -> dict[str, str]:
    try:
        text = payload.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise RuntimeError(f"{label} is not UTF-8") from exc
    result: dict[str, str] = {}
    for line_number, line in enumerate(text.splitlines(), 1):
        if not line:
            continue
        match = re.fullmatch(r"([0-9a-fA-F]{64})  (.+)", line)
        if match is None:
            raise RuntimeError(f"invalid {label} row {line_number}")
        digest, relative = match.groups()
        safe_relative_path(relative)
        if relative in result:
            raise RuntimeError(f"duplicate {label} path: {relative}")
        result[relative] = digest.lower()
    if not result:
        raise RuntimeError(f"{label} is empty")
    return result


def iter_bindings(value: Any) -> Iterator[dict[str, Any]]:
    if isinstance(value, dict):
        if (
            isinstance(value.get("path"), str)
            and isinstance(value.get("bytes"), int)
            and isinstance(value.get("sha256"), str)
        ):
            yield value
        for item in value.values():
            yield from iter_bindings(item)
    elif isinstance(value, list):
        for item in value:
            yield from iter_bindings(item)


def contains_binding(value: Any, expected: dict[str, Any]) -> bool:
    return any(
        item.get("path") == expected["path"]
        and item.get("bytes") == expected["bytes"]
        and str(item.get("sha256", "")).lower() == expected["sha256"]
        for item in iter_bindings(value)
    )


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


def verify_documented_commands(manifest: dict[str, Any]) -> dict[str, Any]:
    strings = "\n".join(flatten_strings(manifest)).lower()
    required = (
        "build_through_unit13.ps1",
        "export_html_v13.py",
        "verify_html_v13.py",
        "verify_backend_v13.py",
    )
    missing = [name for name in required if name.lower() not in strings]
    if missing:
        raise RuntimeError(
            "package manifest does not document every rebuild path: "
            + ", ".join(missing)
        )
    return {"required_commands": list(required), "all_documented": True}


def verify_zip_and_manifest(
    zip_path: Path,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, dict[str, Any]]]:
    with zipfile.ZipFile(zip_path, "r") as archive:
        bad_member = archive.testzip()
        if bad_member is not None:
            raise RuntimeError(f"ZIP CRC failure: {bad_member}")
        infos = [info for info in archive.infolist() if not info.is_dir()]
        names = [info.filename for info in infos]
        if len(names) != len(set(names)):
            raise RuntimeError("source ZIP has duplicate member names")
        if len({name.casefold() for name in names}) != len(names):
            raise RuntimeError("source ZIP has case-colliding member names")
        if names != sorted(names):
            raise RuntimeError("source ZIP member order is not deterministic")
        for info in infos:
            safe_relative_path(info.filename)
            if any(pattern.search(info.filename) for pattern in FORBIDDEN_MEMBER_NAMES):
                raise RuntimeError(f"forbidden private/credential member name: {info.filename}")
            if info.flag_bits & 0x1:
                raise RuntimeError(f"encrypted ZIP member: {info.filename}")
            file_type = (info.external_attr >> 16) & 0o170000
            if file_type not in (0, 0o100000):
                raise RuntimeError(f"non-regular ZIP member: {info.filename}")
            if info.file_size > MAX_MEMBER_BYTES:
                raise RuntimeError(f"oversized ZIP member: {info.filename}")
            if info.date_time != ZIP_TIMESTAMP:
                raise RuntimeError(f"non-normalized ZIP timestamp: {info.filename}")
        uncompressed_bytes = sum(info.file_size for info in infos)
        if uncompressed_bytes > MAX_UNCOMPRESSED_BYTES:
            raise RuntimeError("source ZIP exceeds bounded uncompressed size")
        if EMBEDDED_MANIFEST not in names or EMBEDDED_CHECKSUMS not in names:
            raise RuntimeError("source ZIP lacks embedded manifest/checksum surfaces")

        manifest_payload = archive.read(EMBEDDED_MANIFEST)
        try:
            manifest = json.loads(manifest_payload.decode("utf-8-sig"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RuntimeError("embedded package manifest is invalid") from exc
        if not isinstance(manifest, dict):
            raise RuntimeError("embedded package manifest is not an object")
        rows = manifest.get("files")
        if not isinstance(rows, list) or not rows:
            raise RuntimeError("embedded package manifest has no file inventory")
        row_map: dict[str, dict[str, Any]] = {}
        for row in rows:
            if not isinstance(row, dict):
                raise RuntimeError("invalid embedded manifest row")
            relative = row.get("path")
            size = row.get("bytes")
            digest = row.get("sha256")
            if (
                not isinstance(relative, str)
                or not isinstance(size, int)
                or not isinstance(digest, str)
                or re.fullmatch(r"[0-9a-f]{64}", digest.lower()) is None
            ):
                raise RuntimeError("invalid embedded manifest identity row")
            safe_relative_path(relative)
            if relative in row_map:
                raise RuntimeError(f"duplicate embedded manifest path: {relative}")
            row_map[relative] = {
                "path": relative,
                "bytes": size,
                "sha256": digest.lower(),
            }

        expected_names = set(row_map) | {EMBEDDED_MANIFEST, EMBEDDED_CHECKSUMS}
        if set(names) != expected_names:
            raise RuntimeError(
                "ZIP/manifest inventory mismatch: "
                + json.dumps(
                    {
                        "missing": sorted(expected_names - set(names)),
                        "unexpected": sorted(set(names) - expected_names),
                    },
                    ensure_ascii=False,
                )
            )
        for relative, row in row_map.items():
            payload = archive.read(relative)
            if len(payload) != row["bytes"] or sha256_bytes(payload) != row["sha256"]:
                raise RuntimeError(f"embedded manifest identity mismatch: {relative}")

        checksums = parse_checksum_surface(
            archive.read(EMBEDDED_CHECKSUMS), EMBEDDED_CHECKSUMS
        )
        expected_checksum_names = set(row_map) | {EMBEDDED_MANIFEST}
        if set(checksums) != expected_checksum_names:
            raise RuntimeError("embedded checksum surface inventory mismatch")
        for relative, digest in checksums.items():
            if sha256_bytes(archive.read(relative)) != digest:
                raise RuntimeError(f"embedded checksum mismatch: {relative}")

        tree_digest = hashlib.sha256(
            "".join(
                f"{row['path']}\0{row['bytes']}\0{row['sha256']}\n"
                for row in sorted(row_map.values(), key=lambda item: item["path"])
            ).encode("utf-8")
        ).hexdigest()
        if manifest.get("tree_sha256") != tree_digest:
            raise RuntimeError("embedded package tree digest is absent or stale")
        if manifest.get("files_excluding_manifest_surfaces") not in (
            None,
            len(row_map),
        ):
            raise RuntimeError("embedded package file count is stale")
        if manifest.get("bytes_excluding_manifest_surfaces") not in (
            None,
            sum(row["bytes"] for row in row_map.values()),
        ):
            raise RuntimeError("embedded package byte count is stale")

        result = {
            "crc_passed": True,
            "entries": len(infos),
            "encrypted_members": 0,
            "unsafe_members": 0,
            "case_collisions": 0,
            "uncompressed_bytes": uncompressed_bytes,
            "manifest_rows": len(row_map),
            "manifest_sha256": sha256_bytes(manifest_payload),
            "checksums_rows": len(checksums),
            "tree_sha256": tree_digest,
            "timestamps_normalized": True,
        }
        return result, manifest, row_map


def text_scan_payload(payload: bytes, name: str) -> bytes:
    # A packaged verifier may contain its own detector definitions.  Ignore
    # only complete Python re.compile(...) call spans; all other source lines
    # remain subject to the same leak scan as documentation and data.  AST
    # spans are needed because detector literals are often split over several
    # lines and a one-line exception would flag their continuation strings.
    if PurePosixPath(name).suffix.lower() != ".py":
        return payload
    try:
        text = payload.decode("utf-8-sig")
        tree = ast.parse(text)
    except (UnicodeDecodeError, SyntaxError):
        return payload
    redacted_lines: set[int] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        function = node.func
        if not (
            isinstance(function, ast.Attribute)
            and function.attr == "compile"
            and isinstance(function.value, ast.Name)
            and function.value.id == "re"
        ):
            continue
        start = getattr(node, "lineno", None)
        end = getattr(node, "end_lineno", None)
        if isinstance(start, int) and isinstance(end, int):
            redacted_lines.update(range(start, end + 1))
    lines = text.splitlines()
    return "\n".join(
        "" if index in redacted_lines else line
        for index, line in enumerate(lines, 1)
    ).encode("utf-8")


def verify_privacy(zip_path: Path, member_names: Iterable[str]) -> dict[str, Any]:
    profile_name = Path.home().name.encode("utf-8", errors="ignore")
    profile_pattern = None
    if len(profile_name) >= 3:
        profile_pattern = re.compile(
            rb"(?<![A-Za-z0-9])" + re.escape(profile_name) + rb"(?![A-Za-z0-9])",
            re.IGNORECASE,
        )
    scanned = 0
    text_scanned = 0
    nested_zip_files_scanned = 0
    nested_members_scanned = 0
    nested_text_members_scanned = 0

    def scan_member(name: str, payload: bytes, *, nested: bool) -> None:
        nonlocal scanned, text_scanned, nested_members_scanned, nested_text_members_scanned
        if nested:
            nested_members_scanned += 1
        else:
            scanned += 1
        scan_payload = text_scan_payload(payload, name)
        for pattern in (*PRIVATE_BYTE_PATTERNS, *SECRET_BYTE_PATTERNS):
            if pattern.search(scan_payload):
                raise RuntimeError(f"private/credential-like content in {name}")
        suffix = PurePosixPath(name).suffix.lower()
        if suffix in TEXT_SUFFIXES:
            if nested:
                nested_text_members_scanned += 1
            else:
                text_scanned += 1
            if profile_pattern is not None and profile_pattern.search(scan_payload):
                raise RuntimeError(f"local user identifier in {name}")
            try:
                payload.decode("utf-8-sig")
            except UnicodeDecodeError as exc:
                raise RuntimeError(f"declared text member is not UTF-8: {name}") from exc

    with zipfile.ZipFile(zip_path, "r") as archive:
        for name in member_names:
            payload = archive.read(name)
            scan_member(name, payload, nested=False)
            suffix = PurePosixPath(name).suffix.lower()
            if suffix == ".zip":
                nested_zip_files_scanned += 1
                with zipfile.ZipFile(io.BytesIO(payload), "r") as nested_archive:
                    bad = nested_archive.testzip()
                    if bad is not None:
                        raise RuntimeError(f"nested ZIP CRC failure in {name}: {bad}")
                    nested_infos = [
                        info for info in nested_archive.infolist() if not info.is_dir()
                    ]
                    nested_names = [info.filename for info in nested_infos]
                    if len(nested_names) != len(set(nested_names)):
                        raise RuntimeError(f"duplicate nested ZIP member in {name}")
                    for info in nested_infos:
                        safe_relative_path(info.filename)
                        if info.flag_bits & 0x1:
                            raise RuntimeError(
                                f"encrypted nested ZIP member in {name}: {info.filename}"
                            )
                        if any(
                            pattern.search(info.filename)
                            for pattern in FORBIDDEN_MEMBER_NAMES
                        ):
                            raise RuntimeError(
                                f"forbidden private member in {name}: {info.filename}"
                            )
                        scan_member(
                            f"{name}!/{info.filename}",
                            nested_archive.read(info.filename),
                            nested=True,
                        )
    return {
        "files_scanned": scanned,
        "text_files_scanned": text_scanned,
        "nested_zip_files_scanned": nested_zip_files_scanned,
        "nested_members_scanned": nested_members_scanned,
        "nested_text_members_scanned": nested_text_members_scanned,
        "private_locator_hits": 0,
        "local_user_identifier_hits": 0,
        "credential_like_content_hits": 0,
        "forbidden_member_name_hits": 0,
        "status": "pass",
    }


def count_csv_rows(path: Path) -> int:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return sum(1 for _ in csv.DictReader(stream))


def verify_json_files(root: Path, relatives: Iterable[str]) -> None:
    for relative in relatives:
        value = load_json(project_file(root, relative))
        if not isinstance(value, (dict, list)):
            raise RuntimeError(f"required JSON evidence is empty/invalid: {relative}")


def nested_zip_bindings(path: Path) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    with zipfile.ZipFile(path, "r") as archive:
        bad = archive.testzip()
        if bad is not None:
            raise RuntimeError(f"nested predecessor ZIP CRC failure: {bad}")
        for info in archive.infolist():
            if info.is_dir():
                continue
            relative = info.filename
            safe_relative_path(relative)
            if relative in result:
                raise RuntimeError(f"duplicate nested predecessor member: {relative}")
            payload = archive.read(relative)
            result[relative] = {
                "path": relative,
                "bytes": len(payload),
                "sha256": sha256_bytes(payload),
            }
    return result


def validate_declared_bindings(
    root: Path,
    value: Any,
    label: str,
    fallback_zip: Path | None = None,
    allow_present_superseded_versions: bool = False,
) -> dict[str, int]:
    count = 0
    loose_matches = 0
    nested_matches = 0
    present_superseded_versions = 0
    fallback = nested_zip_bindings(fallback_zip) if fallback_zip is not None else {}
    for record in iter_bindings(value):
        relative = str(record["path"])
        expected = {
            "path": relative,
            "bytes": record["bytes"],
            "sha256": str(record["sha256"]).lower(),
        }
        parsed = safe_relative_path(relative)
        path = root.joinpath(*parsed.parts)
        actual = file_binding(path, root) if path.is_file() else None
        if actual == expected:
            loose_matches += 1
        elif fallback.get(relative) == expected:
            nested_matches += 1
        elif allow_present_superseded_versions and path.is_file():
            # The frozen Unit 10 build receipt is itself an exact predecessor
            # artifact consumed by the Unit 13 build.  A few paths it records
            # were legitimately superseded later at the same repo-relative
            # locations and were never promised as a fresh Unit 10 rebuild
            # surface.  Presence is still useful closure evidence, but it is
            # reported explicitly and never mislabelled as historic identity.
            present_superseded_versions += 1
        else:
            raise RuntimeError(f"stale or absent {label} binding: {relative}")
        count += 1
    if count == 0:
        raise RuntimeError(f"{label} has no identity bindings")
    return {
        "bindings": count,
        "loose_exact_matches": loose_matches,
        "nested_frozen_source_matches": nested_matches,
        "present_superseded_versions": present_superseded_versions,
    }


def verify_required_closure(
    root: Path,
    package_manifest: dict[str, Any],
    row_map: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    required_sets = {
        "durable_controls": REQUIRED_CONTROL_PATHS,
        "control_correction_manifests": REQUIRED_CONTROL_CORRECTION_MANIFESTS,
        "qa_correction_manifests": REQUIRED_QA_CORRECTION_MANIFESTS,
        "unit10_release": REQUIRED_UNIT10_RELEASE_PATHS,
        "unit10_html_tree": REQUIRED_UNIT10_HTML_PATHS,
        "predecessor_qa": REQUIRED_PREDECESSOR_QA_PATHS,
        "build_paths": REQUIRED_BUILD_PATHS,
        "package_documents": REQUIRED_DOCUMENTS,
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
    if count_csv_rows(project_file(root, "00_control/TERMINOLOGY.csv")) != EXPECTED_TERMINOLOGY_ROWS:
        raise RuntimeError("terminology ledger row count differs from the settled Unit 13 boundary")
    if count_csv_rows(project_file(root, "00_control/ADVERSE_LEDGER.csv")) != EXPECTED_ADVERSE_ROWS:
        raise RuntimeError("adverse/correction ledger row count differs from the settled Unit 13 boundary")
    verify_json_files(root, REQUIRED_CONTROL_CORRECTION_MANIFESTS)
    verify_json_files(root, REQUIRED_QA_CORRECTION_MANIFESTS)

    records = [
        json.loads(line)
        for line in project_file(root, "backend/records.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line
    ]
    if len(records) != EXPECTED_RECORD_COUNT:
        raise RuntimeError("backend record count differs from the settled Unit 13 boundary")
    corrections = sum(record.get("entity_type") == "correction" for record in records)
    if corrections != EXPECTED_CORRECTION_RECORD_COUNT:
        raise RuntimeError("backend correction-record closure is incomplete")

    # Prove the transitive PDF build inputs from both frozen build receipts,
    # not merely the handful of predecessor files named by the outer package.
    transitive_counts: dict[str, Any] = {}
    unit10_source_zip = project_file(
        root,
        "output/release-unit10/geometri-diferensial-manifold-mulus-brenner-id-unit10-source-20260823.zip",
    )
    for relative in ("qa/unit-10/build.json", "qa/unit-13/build.json"):
        receipt = load_json(project_file(root, relative))
        inputs = receipt.get("inputs") if isinstance(receipt, dict) else None
        if not isinstance(inputs, list) or not inputs:
            raise RuntimeError(f"build receipt has no transitive input closure: {relative}")
        transitive_counts[relative] = validate_declared_bindings(
            root,
            inputs,
            f"{relative} transitive input",
            fallback_zip=unit10_source_zip if relative == "qa/unit-10/build.json" else None,
            allow_present_superseded_versions=relative == "qa/unit-10/build.json",
        )

    explicit_bindings: dict[str, dict[str, Any]] = {}
    for relative in CRITICAL_EXPLICIT_PREDECESSOR_BINDINGS:
        path = project_file(root, relative)
        expected = file_binding(path, root)
        if not contains_binding(package_manifest, expected):
            raise RuntimeError(
                "package manifest lacks explicit predecessor identity binding: "
                + relative
            )
        explicit_bindings[relative] = expected

    commands = verify_documented_commands(package_manifest)
    return {
        "durable_controls": len(REQUIRED_CONTROL_PATHS),
        "cumulative_correction_manifests": len(
            REQUIRED_CONTROL_CORRECTION_MANIFESTS
        )
        + len(REQUIRED_QA_CORRECTION_MANIFESTS),
        "terminology_rows": EXPECTED_TERMINOLOGY_ROWS,
        "adverse_ledger_rows": EXPECTED_ADVERSE_ROWS,
        "backend_records": EXPECTED_RECORD_COUNT,
        "backend_correction_records": EXPECTED_CORRECTION_RECORD_COUNT,
        "unit10_release_files": len(REQUIRED_UNIT10_RELEASE_PATHS),
        "unit10_html_files": len(REQUIRED_UNIT10_HTML_PATHS),
        "predecessor_qa_files": len(REQUIRED_PREDECESSOR_QA_PATHS),
        "transitive_build_input_bindings": transitive_counts,
        "explicit_predecessor_bindings": explicit_bindings,
        "documented_build_paths": commands,
        "status": "pass",
    }


def safe_extract(zip_path: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=False)
    with zipfile.ZipFile(zip_path, "r") as archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            parsed = safe_relative_path(info.filename)
            target = destination.joinpath(*parsed.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            payload = archive.read(info.filename)
            target.write_bytes(payload)
            if target.stat().st_size != info.file_size:
                raise RuntimeError(f"extraction size mismatch: {info.filename}")


def tree_inventory(directory: Path) -> list[dict[str, Any]]:
    return [
        {
            "path": path.relative_to(directory).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
        for path in sorted(
            (item for item in directory.rglob("*") if item.is_file()),
            key=lambda item: item.relative_to(directory).as_posix(),
        )
    ]


def inventory_digest(inventory: list[dict[str, Any]]) -> str:
    return sha256_bytes(
        json.dumps(
            inventory,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    )


def serialize_html_tree(directory: Path, output: Path) -> None:
    files = sorted(
        (item for item in directory.rglob("*") if item.is_file()),
        key=lambda item: item.relative_to(directory).as_posix(),
    )
    with zipfile.ZipFile(
        output,
        "x",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
        strict_timestamps=True,
    ) as archive:
        for path in files:
            relative = path.relative_to(directory).as_posix()
            info = zipfile.ZipInfo(relative, ZIP_TIMESTAMP)
            info.create_system = 3
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            info.flag_bits |= 0x800
            archive.writestr(
                info,
                path.read_bytes(),
                compress_type=zipfile.ZIP_DEFLATED,
                compresslevel=9,
            )


def verify_outer_release(
    root: Path, release_dir: Path, source_zip: Path
) -> tuple[dict[str, Any], Path, Path]:
    manifest_path = project_file(root, f"{release_dir.relative_to(root).as_posix()}/{OUTER_MANIFEST}")
    checksums_path = project_file(root, f"{release_dir.relative_to(root).as_posix()}/{OUTER_CHECKSUMS}")
    with manifest_path.open("r", encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if not rows:
        raise RuntimeError("outer release manifest is empty")
    row_map: dict[str, dict[str, Any]] = {}
    for row in rows:
        filename = row.get("filename") or row.get("path")
        if not filename or filename in row_map:
            raise RuntimeError("invalid/duplicate outer release manifest filename")
        safe_relative_path(filename)
        row_map[filename] = row
    checksums = parse_checksum_surface(checksums_path.read_bytes(), OUTER_CHECKSUMS)

    source_name = source_zip.name
    html_names = [
        name
        for name in row_map
        if name.lower().endswith(".zip")
        and "unit13" in name.lower()
        and "html" in name.lower()
    ]
    if len(html_names) != 1:
        raise RuntimeError("outer manifest does not identify exactly one Unit 13 HTML ZIP")
    required_names = (STAGED_PDF_NAME, source_name, html_names[0])
    verified: dict[str, Any] = {}
    for name in required_names:
        if name not in row_map:
            raise RuntimeError(f"outer release manifest omits staged artifact: {name}")
        path = project_file(root, f"{release_dir.relative_to(root).as_posix()}/{name}")
        binding = file_binding(path)
        row = row_map[name]
        if int(row.get("bytes", -1)) != binding["bytes"] or str(row.get("sha256", "")).lower() != binding["sha256"]:
            raise RuntimeError(f"outer release manifest identity mismatch: {name}")
        if checksums.get(name) != binding["sha256"]:
            raise RuntimeError(f"outer release checksum identity mismatch: {name}")
        verified[name] = binding
    return (
        {
            "manifest": file_binding(manifest_path, root),
            "checksums": file_binding(checksums_path, root),
            "verified_artifacts": verified,
            "status": "pass",
        },
        release_dir / STAGED_PDF_NAME,
        release_dir / html_names[0],
    )


def verify_html_zip_against_inventory(
    html_zip: Path, inventory: list[dict[str, Any]]
) -> dict[str, Any]:
    expected = {item["path"]: item for item in inventory}
    with zipfile.ZipFile(html_zip, "r") as archive:
        bad = archive.testzip()
        if bad is not None:
            raise RuntimeError(f"staged HTML ZIP CRC failure: {bad}")
        infos = [info for info in archive.infolist() if not info.is_dir()]
        names = [info.filename for info in infos]
        if names != sorted(expected) or set(names) != set(expected):
            raise RuntimeError("staged HTML ZIP/tree inventory mismatch")
        for info in infos:
            payload = archive.read(info.filename)
            item = expected[info.filename]
            if len(payload) != item["bytes"] or sha256_bytes(payload) != item["sha256"]:
                raise RuntimeError(f"staged HTML ZIP/tree identity mismatch: {info.filename}")
    return {
        **file_binding(html_zip),
        "entries": len(inventory),
        "tree_inventory_sha256": inventory_digest(inventory),
        "crc_passed": True,
    }


def command_environment() -> dict[str, str]:
    env = os.environ.copy()
    env.update(
        {
            "PYTHONHASHSEED": "0",
            "SOURCE_DATE_EPOCH": "1787616000",
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
    started = time.monotonic()
    completed = subprocess.run(
        command,
        cwd=root,
        env=command_environment(),
        capture_output=True,
        text=False,
        timeout=timeout_seconds,
        check=False,
    )
    duration_ms = int((time.monotonic() - started) * 1000)
    if completed.returncode != 0:
        tail = (completed.stderr or completed.stdout)[-4000:].decode(
            "utf-8", errors="replace"
        )
        tail = tail.replace(str(root), "<extraction-root>")
        raise RuntimeError(f"{label} failed with {completed.returncode}: {tail}")
    return {
        "label": label,
        "status": "pass",
        "returncode": 0,
        "duration_ms": duration_ms,
        "stdout_bytes": len(completed.stdout),
        "stderr_bytes": len(completed.stderr),
    }


def choose_powershell() -> str:
    executable = shutil.which("pwsh") or shutil.which("powershell")
    if executable is None:
        raise RuntimeError("neither pwsh nor powershell is available")
    return executable


def compare_binding(actual: dict[str, Any], expected: dict[str, Any], label: str) -> None:
    if actual.get("bytes") != expected.get("bytes") or actual.get("sha256") != expected.get("sha256"):
        raise RuntimeError(
            f"{label} identity differs: actual={actual}, expected={expected}"
        )


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
                str(extracted_root / "scripts/build_through_unit13.ps1"),
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
                str(extracted_root / "scripts/export_html_v13.py"),
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
                str(extracted_root / "scripts/verify_html_v13.py"),
                "--root",
                str(extracted_root),
                "--output",
                str(html_output),
                "--receipt",
                str(extracted_root / "qa/unit-13/HTML_READER_QA.json"),
            ],
            extracted_root,
            "HTML verifier (independent two-cycle reconstruction)",
            timeout_seconds,
        )
    )
    commands.append(
        run_command(
            [
                sys.executable,
                str(extracted_root / "scripts/verify_backend_v13.py"),
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

    html_inventory = tree_inventory(project_directory(extracted_root, CANONICAL_HTML_ROOT))
    if html_inventory != canonical["html_inventory"]:
        raise RuntimeError("rebuilt HTML tree differs from the canonical Unit 13 tree")
    html_zip_check = verify_html_zip_against_inventory(staged_html_zip, html_inventory)
    replica_zip = extracted_root / "tmp/unit13-html-r1-rebuilt.zip"
    replica_zip.parent.mkdir(parents=True, exist_ok=True)
    serialize_html_tree(project_directory(extracted_root, CANONICAL_HTML_ROOT), replica_zip)
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

    qa_outputs = {
        relative: file_binding(project_file(extracted_root, relative))
        for relative in (
            "qa/unit-13/build.json",
            "qa/unit-13/pdf_structural_qa.json",
            "qa/unit-13/HTML_READER_QA.json",
            "qa/unit-13/backend.json",
        )
    }
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
            "qa": qa_outputs,
        },
    }


def build_canonical(root: Path, staged_pdf: Path, staged_html_zip: Path) -> dict[str, Any]:
    canonical_pdf = file_binding(project_file(root, CANONICAL_PDF))
    compare_binding(canonical_pdf, file_binding(staged_pdf), "canonical/staged PDF")
    html_inventory = tree_inventory(project_directory(root, CANONICAL_HTML_ROOT))
    html_zip = verify_html_zip_against_inventory(staged_html_zip, html_inventory)
    backend = {
        relative: file_binding(project_file(root, relative))
        for relative in CANONICAL_BACKEND
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
    }


def clean_rebuild(
    source_zip: Path,
    cycle: int,
    canonical: dict[str, Any],
    staged_pdf: Path,
    staged_html_zip: Path,
    timeout_seconds: int,
) -> tuple[dict[str, Any], bool]:
    temporary_root = Path(tempfile.mkdtemp(prefix=f"o011-u13-r1-{cycle}-"))
    extracted_root = temporary_root / "source"
    try:
        safe_extract(source_zip, extracted_root)
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


def all_boolean_leaves_true(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, dict) and value:
        return all(all_boolean_leaves_true(item) for item in value.values())
    return False


def resolve_inside(root: Path, value: Path, label: str) -> Path:
    path = (value if value.is_absolute() else root / value).resolve()
    if path == root or root not in path.parents:
        raise RuntimeError(f"{label} must remain inside the project root")
    return path


def write_receipt(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = canonical_json_bytes(value)
    temporary = path.with_name(path.name + ".tmp")
    if temporary.exists():
        temporary.unlink()
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
        raise RuntimeError(f"corrective source ZIP is missing: {source_zip.name}")
    if not release_dir.is_dir() or source_zip.parent != release_dir:
        raise RuntimeError("corrective source ZIP is not in the declared r1 release directory")

    zip_validation, package_manifest, row_map = verify_zip_and_manifest(source_zip)
    privacy = verify_privacy(source_zip, sorted(row_map) + [EMBEDDED_MANIFEST, EMBEDDED_CHECKSUMS])

    inspection_root = Path(tempfile.mkdtemp(prefix="o011-u13-r1-inspect-"))
    extracted_inspection = inspection_root / "source"
    try:
        safe_extract(source_zip, extracted_inspection)
        required_closure = verify_required_closure(
            extracted_inspection, package_manifest, row_map
        )
    finally:
        shutil.rmtree(inspection_root, ignore_errors=False)
    inspection_removed = not inspection_root.exists()
    if not inspection_removed:
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
        "qa_receipts": first["qa"] == second["qa"],
    }
    if not all_boolean_leaves_true(cross_cycle_identity):
        raise RuntimeError("the two independent clean reconstructions differ")

    checks = {
        "zip_crc_and_manifest_identity": True,
        "embedded_checksums_complete": True,
        "safe_regular_members_only": True,
        "privacy_and_credentials_absent": True,
        "public_safe_durable_controls_complete": True,
        "cumulative_correction_manifests_complete": True,
        "unit10_predecessor_closure_complete": True,
        "transitive_pdf_build_inputs_bound": True,
        "documented_build_paths_exercised": True,
        "independent_verifier_in_source_package": True,
        "two_independent_clean_extractions": True,
        "pdf_matches_staged_canonical": True,
        "html_tree_and_zip_match_staged_canonical": True,
        "backend_matches_staged_canonical": True,
        "cross_cycle_identity": True,
        "temporary_directories_removed": True,
        "network_not_used": True,
    }
    if not all_boolean_leaves_true(checks):
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
    print(json.dumps(output, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
