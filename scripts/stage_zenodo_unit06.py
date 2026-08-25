#!/usr/bin/env python3
"""Create and verify the compact deterministic Unit 6 source/backend archive."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import tempfile
import zipfile
from pathlib import Path


ROOT_FILE_MAP = {
    "qa/unit-06/PACKAGE_README.md": "README.md",
    "qa/unit-06/LICENSE_RELEASE_UNIT06.md": "LICENSE.md",
    "qa/unit-06/RELEASE_NOTES_20260822.md": "RELEASE_NOTES_20260822.md",
}
CONTROL_FILES = (
    "ADVERSE_LEDGER.csv",
    "TERMINOLOGY.csv",
)
AUTHORITY_FILES = (
    "brenner_94_link_classification.csv",
    "brenner_export_and_title_inventory_receipt.txt",
    "brenner_media_rights_manifest.csv",
    "brenner_selected_root_revisions.csv",
    "brenner_selected_surface_revisions.csv",
)
BUILD_FILES = (
    "brenner-compat.tex",
    "unit-01.tex",
    "through-unit-02.tex",
    "through-unit-03.tex",
    "through-unit-04.tex",
    "through-unit-05.tex",
    "through-unit-06.tex",
)
SCRIPT_FILES = (
    "build_unit01.ps1",
    "build_through_unit02.ps1",
    "build_through_unit03.ps1",
    "build_through_unit04.ps1",
    "build_through_unit05.ps1",
    "build_through_unit06.ps1",
    "make_portable_preamble.py",
    "prepare_unit_media.py",
    "prepare_unit_tex.py",
    "verify_unit_translation.py",
    "normalize_indonesian_field_terms_u01_u06.py",
    "export_backend_v6.py",
    "verify_backend_v6.py",
    "verify_unit06_post_repair.py",
    "verify_through_unit06_pdf.py",
)
TREE_DIRS = (
    "source",
    "backend",
    "authority/expanded",
    "authority/media",
)
QA_DIRS = (
    "qa/unit-01",
    "qa/unit-02",
    "qa/unit-03",
    "qa/unit-04",
    "qa/unit-05",
    "qa/unit-06",
    "qa/terminology",
)
QA_ROOT_FILES = (
    "lecture01_prepare.json",
    "lecture01_sanitize.json",
    "portable_preamble.json",
    "script_preamble_sanitize.json",
    "unit-01_media.json",
    "unit-02_media.json",
    "unit-03_media.json",
    "unit-04_media.json",
    "unit-05_media.json",
    "unit-06_media.json",
    "worksheet01_exercise01_solution_prepare.json",
    "worksheet01_prepare.json",
    "worksheet01_sanitize.json",
)
QA_EXCLUDED_FRAGMENTS = (
    "FIGSHARE_",
    "ZENODO_",
    "PUBLICATION_RECEIPT",
    "RELEASE_NOTES_",
    "LICENSE_RELEASE_",
    "PACKAGE_README",
)
TRANSIENT_NAMES = {"__pycache__", ".pytest_cache", ".mypy_cache"}
TRANSIENT_SUFFIXES = {
    ".aux",
    ".bbl",
    ".bcf",
    ".blg",
    ".fdb_latexmk",
    ".fls",
    ".idx",
    ".ilg",
    ".ind",
    ".lof",
    ".log",
    ".out",
    ".pyc",
    ".run.xml",
    ".synctex.gz",
    ".toc",
}
SENSITIVE_NAME_FRAGMENTS = ("token", "credential", "secret", "password", ".env")
TEXT_SUFFIXES = {
    "",
    ".csv",
    ".json",
    ".jsonl",
    ".md",
    ".ps1",
    ".py",
    ".svg",
    ".tex",
    ".txt",
    ".xml",
}
PRIVATE_LOCATOR_PATTERNS = (
    re.compile(rb"[A-Za-z]:[\\/]+Users[\\/]+", re.IGNORECASE),
    re.compile(rb"(?<!:)\/Users\/", re.IGNORECASE),
    re.compile(rb"(?<![:A-Za-z0-9_])\/(?:home|srv\/home)\/[A-Za-z0-9._-]+\/", re.IGNORECASE),
    re.compile(rb"\\\\[^\\\r\n]+\\Users\\", re.IGNORECASE),
)
SECRET_PATTERNS = (
    re.compile(rb"github_pat_[A-Za-z0-9_]{40,}"),
    re.compile(rb"gh[pousr]_[A-Za-z0-9]{36,}"),
    re.compile(rb"eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}"),
    re.compile(
        rb"(?:access[_-]?token|api[_-]?token|password|secret)\s*[:=]\s*[\"'][^\"'\r\n]{16,}[\"']",
        re.IGNORECASE,
    ),
    re.compile(
        rb"Authorization\s*[:=]\s*[\"']?(?:Bearer|token)\s+[A-Za-z0-9._-]{20,}",
        re.IGNORECASE,
    ),
)
PERSONAL_CONTRIBUTOR_PATTERNS = (
    re.compile(
        rb"Codex\s*\(OpenAI\)\s*,\s*acting\s+on\s+[^\r\n\"<]{1,120}(?:request|direction)",
        re.IGNORECASE,
    ),
    re.compile(
        rb"Codex\s*\(OpenAI\)\s*,\s*atas\s+arahan\s+(?!pengguna\b)[^\r\n\"<]{1,120}",
        re.IGNORECASE,
    ),
)
MODEL_IDENTIFICATION = "OpenAI Codex gpt-5.6-sol, Ultra"
ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
PDF_RELATIVE = "output/pdf/geometri-diferensial-manifold-mulus-hingga-unit-06-id.pdf"
LECTURE_RELATIVE = "source/units/unit-06/lecture06.id.tex"
MATH_QA_RELATIVE = "qa/unit-06/POST_REPAIR_MATH_QA.json"
BUILD_RECEIPT_RELATIVE = "qa/unit-06/build.json"
KNOWN_PRIVACY_SCANNER_FILE = "scripts/verify_through_unit06_pdf.py"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def identity(path: Path) -> dict[str, int | str]:
    return {"bytes": path.stat().st_size, "sha256": sha256(path)}


def project_relative(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.name


def verify_release_boundary(
    root: Path,
    expected_pdf_bytes: int,
    expected_pdf_sha256: str,
    expected_lecture_sha256: str,
    expected_build_receipt_sha256: str,
    expected_math_qa_sha256: str,
    expected_structural_qa_sha256: str,
    expected_backend_records: int,
    expected_backend_qa_sha256: str,
) -> dict[str, object]:
    expected_pdf = {
        "bytes": expected_pdf_bytes,
        "sha256": expected_pdf_sha256.lower(),
    }
    pdf = root / PDF_RELATIVE
    if identity(pdf) != expected_pdf:
        raise SystemExit("settled PDF identity mismatch at package boundary")

    lecture = root / LECTURE_RELATIVE
    if sha256(lecture) != expected_lecture_sha256.lower():
        raise SystemExit("final Lecture 6 source identity mismatch at package boundary")
    build_receipt_path = root / BUILD_RECEIPT_RELATIVE
    if sha256(build_receipt_path) != expected_build_receipt_sha256.lower():
        raise SystemExit("final build-receipt identity mismatch at package boundary")
    math_qa_path = root / MATH_QA_RELATIVE
    if sha256(math_qa_path) != expected_math_qa_sha256.lower():
        raise SystemExit("final math-QA identity mismatch at package boundary")
    math_qa = json.loads(math_qa_path.read_text(encoding="utf-8"))
    if math_qa.get("status") != "pass":
        raise SystemExit("final math QA is not passing")

    pdf_qa_path = root / "qa/unit-06/pdf_structural_qa.json"
    if sha256(pdf_qa_path) != expected_structural_qa_sha256.lower():
        raise SystemExit("final structural-QA identity mismatch at package boundary")
    pdf_qa = json.loads(pdf_qa_path.read_text(encoding="utf-8"))
    if not pdf_qa.get("passed") or {
        "bytes": pdf_qa.get("pdf", {}).get("bytes"),
        "sha256": pdf_qa.get("pdf", {}).get("sha256"),
    } != expected_pdf:
        raise SystemExit("structural QA is not bound to the settled PDF")

    manifest_path = root / "backend/MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("combined", {}).get("record_count") != expected_backend_records:
        raise SystemExit("backend manifest record-count mismatch")
    outputs = manifest.get("outputs", {})
    backend_files = {
        "records_jsonl": root / "backend/records.jsonl",
        "records_csv": root / "backend/records.csv",
    }
    for key, path in backend_files.items():
        if outputs.get(key) != {"path": path.relative_to(root).as_posix(), **identity(path)}:
            raise SystemExit(f"backend manifest output binding mismatch: {key}")
    backend_qa_path = root / "qa/unit-06/backend.json"
    if sha256(backend_qa_path) != expected_backend_qa_sha256.lower():
        raise SystemExit("final backend-QA identity mismatch at package boundary")
    backend_qa = json.loads(backend_qa_path.read_text(encoding="utf-8"))
    if (
        backend_qa.get("status") != "pass"
        or backend_qa.get("combined_records") != expected_backend_records
    ):
        raise SystemExit("backend QA is not passing at the expected record count")
    for key, path in backend_files.items():
        if backend_qa.get("outputs", {}).get(key) != {
            "path": path.relative_to(root).as_posix(),
            **identity(path),
        }:
            raise SystemExit(f"backend QA output binding mismatch: {key}")
    if backend_qa.get("outputs", {}).get("manifest") != {
        "path": "backend/MANIFEST.json",
        **identity(manifest_path),
    }:
        raise SystemExit("backend QA manifest binding mismatch")

    notes = (root / "qa/unit-06/RELEASE_NOTES_20260822.md").read_text(encoding="utf-8")
    for value in (
        expected_pdf_sha256.lower(),
        expected_lecture_sha256.lower(),
        expected_build_receipt_sha256.lower(),
        expected_math_qa_sha256.lower(),
        expected_structural_qa_sha256.lower(),
        sha256(root / "backend/records.jsonl"),
        sha256(root / "backend/records.csv"),
        sha256(manifest_path),
        expected_backend_qa_sha256.lower(),
        MODEL_IDENTIFICATION,
    ):
        if value not in notes:
            raise SystemExit(f"release notes do not bind required identity: {value}")

    return {
        "pdf": {"path": PDF_RELATIVE, **identity(pdf)},
        "lecture": {"path": LECTURE_RELATIVE, **identity(lecture)},
        "build_receipt": {"path": BUILD_RECEIPT_RELATIVE, **identity(build_receipt_path)},
        "math_qa": {"path": MATH_QA_RELATIVE, **identity(math_qa_path)},
        "structural_qa": {
            "path": "qa/unit-06/pdf_structural_qa.json",
            **identity(pdf_qa_path),
        },
        "backend_records": expected_backend_records,
        "backend": {
            "records_jsonl": identity(root / "backend/records.jsonl"),
            "records_csv": identity(root / "backend/records.csv"),
            "manifest": identity(manifest_path),
            "qa": identity(backend_qa_path),
        },
    }


def copy_file(root: Path, staging: Path, source_relative: str, target_relative: str | None = None) -> None:
    source = root / source_relative
    target = staging / (target_relative or source_relative)
    if not source.is_file():
        raise SystemExit(f"required package file missing: {source_relative}")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)


def include_qa(path: Path) -> bool:
    if any(fragment in path.name for fragment in QA_EXCLUDED_FRAGMENTS):
        return False
    return not any(part in TRANSIENT_NAMES for part in path.parts)


def copy_tree(root: Path, staging: Path, relative: str) -> None:
    source_root = root / relative
    if not source_root.is_dir():
        raise SystemExit(f"required package directory missing: {relative}")
    for source in sorted(path for path in source_root.rglob("*") if path.is_file()):
        local = source.relative_to(root).as_posix()
        if any(part in TRANSIENT_NAMES for part in source.parts):
            continue
        if any(source.name.lower().endswith(suffix) for suffix in TRANSIENT_SUFFIXES):
            continue
        if relative.startswith("qa/") and not include_qa(source):
            continue
        copy_file(root, staging, local)


def write_internal_manifests(staging: Path) -> None:
    files = sorted(
        (path for path in staging.rglob("*") if path.is_file()),
        key=lambda path: path.relative_to(staging).as_posix(),
    )
    manifest_rows = [
        {
            "path": path.relative_to(staging).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        }
        for path in files
    ]
    manifest = {
        "schema_version": 1,
        "workflow": "o011-unit06-compact-source-package-v1",
        "status": "active_partial",
        "coverage": "Kuliah 1-6 dan Lembar Kerja 1-6 dari 29 pasangan inti",
        "model_identification": MODEL_IDENTIFICATION,
        "files_excluding_manifest_surfaces": len(manifest_rows),
        "bytes_excluding_manifest_surfaces": sum(int(row["bytes"]) for row in manifest_rows),
        "tree_sha256": hashlib.sha256(
            "".join(
                f"{row['path']}\0{row['bytes']}\0{row['sha256']}\n"
                for row in manifest_rows
            ).encode("utf-8")
        ).hexdigest(),
        "files": manifest_rows,
        "deliberate_exclusions": [
            "PDF reader (published as the primary separate file)",
            "raw MediaWiki/XML export dumps and redundant export trees",
            "historical witness PDFs and duplicate generated build trees",
            "temporary renders, caches, TeX auxiliaries, and local Git data",
            "private locators, credentials, and remote-publication operation files",
        ],
    }
    manifest_path = staging / "PACKAGE_MANIFEST.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    checksum_files = sorted(
        (path for path in staging.rglob("*") if path.is_file()),
        key=lambda path: path.relative_to(staging).as_posix(),
    )
    (staging / "PACKAGE_CHECKSUMS.sha256").write_text(
        "".join(
            f"{sha256(path)}  {path.relative_to(staging).as_posix()}\n"
            for path in checksum_files
        ),
        encoding="ascii",
        newline="\n",
    )


def verify_staging(staging: Path) -> tuple[list[Path], dict[str, int | bool]]:
    files = sorted(
        (path for path in staging.rglob("*") if path.is_file()),
        key=lambda path: path.relative_to(staging).as_posix(),
    )
    if not files:
        raise SystemExit("staging tree is empty")
    sensitive_names = [
        path.relative_to(staging).as_posix()
        for path in files
        if any(fragment in path.name.lower() for fragment in SENSITIVE_NAME_FRAGMENTS)
    ]
    if sensitive_names:
        raise SystemExit("sensitive-looking package filenames: " + ", ".join(sensitive_names))
    private_locator_files: list[str] = []
    personal_contributor_files: list[str] = []
    credential_like_files: list[str] = []
    scanned_text_files = 0
    generic_scanner_pattern_literals = 0
    for path in files:
        if path.suffix.lower() in TEXT_SUFFIXES:
            scanned_text_files += 1
        payload = path.read_bytes()
        relative = path.relative_to(staging).as_posix()
        private_matches = [
            (index, match)
            for index, pattern in enumerate(PRIVATE_LOCATOR_PATTERNS)
            for match in pattern.finditer(payload)
        ]
        if private_matches:
            is_known_generic_scanner_literal = (
                relative == KNOWN_PRIVACY_SCANNER_FILE
                and all(index == 1 for index, _ in private_matches)
                and len(private_matches) == 2
                and payload.count(b"|/Users/|/home/)") == 2
            )
            if is_known_generic_scanner_literal:
                generic_scanner_pattern_literals += len(private_matches)
            else:
                private_locator_files.append(relative)
        if any(pattern.search(payload) for pattern in PERSONAL_CONTRIBUTOR_PATTERNS):
            personal_contributor_files.append(path.relative_to(staging).as_posix())
        if any(pattern.search(payload) for pattern in SECRET_PATTERNS):
            credential_like_files.append(path.relative_to(staging).as_posix())
    if private_locator_files:
        raise SystemExit("private local locators found in staged text files: " + ", ".join(private_locator_files))
    if personal_contributor_files:
        raise SystemExit(
            "personal-name contributor wording found in staged text files: "
            + ", ".join(personal_contributor_files)
        )
    if credential_like_files:
        raise SystemExit(
            "credential-like content found in staged files: "
            + ", ".join(credential_like_files)
        )
    release_text = (staging / "RELEASE_NOTES_20260822.md").read_text(encoding="utf-8")
    if MODEL_IDENTIFICATION not in release_text:
        raise SystemExit("exact model identification is absent from release notes")
    for forbidden in ("TTP", "Translation and Transcription Project"):
        if forbidden in release_text:
            raise SystemExit("umbrella label leaked into descriptive release prose")
    return files, {
        "all_files_raw_bytes_scanned": len(files),
        "text_files_scanned": scanned_text_files,
        "private_locator_hits": 0,
        "generic_privacy_scanner_pattern_literals": generic_scanner_pattern_literals,
        "personal_contributor_wording_hits": 0,
        "credential_like_content_hits": 0,
        "historical_publication_receipts_excluded": True,
    }


def create_zip(staging: Path, archive: Path, files: list[Path]) -> None:
    archive.parent.mkdir(parents=True, exist_ok=True)
    if archive.exists():
        raise SystemExit(f"refusing to overwrite archive: {archive}")
    with zipfile.ZipFile(
        archive,
        mode="x",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
        strict_timestamps=True,
    ) as bundle:
        for path in files:
            relative = path.relative_to(staging).as_posix()
            info = zipfile.ZipInfo(relative, date_time=ZIP_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.flag_bits |= 0x800
            bundle.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def verify_zip(staging: Path, archive: Path, files: list[Path]) -> dict[str, object]:
    expected = {
        path.relative_to(staging).as_posix(): (path.stat().st_size, sha256(path))
        for path in files
    }
    with zipfile.ZipFile(archive, "r") as bundle:
        infos = bundle.infolist()
        names = [item.filename for item in infos]
        if names != sorted(expected):
            raise SystemExit("ZIP entry order or inventory mismatch")
        if bundle.testzip() is not None:
            raise SystemExit("ZIP CRC verification failed")
        for item in infos:
            data = bundle.read(item.filename)
            actual = (len(data), hashlib.sha256(data).hexdigest())
            if actual != expected[item.filename]:
                raise SystemExit(f"ZIP entry identity mismatch: {item.filename}")
            if item.date_time != ZIP_TIMESTAMP:
                raise SystemExit(f"ZIP timestamp is not normalized: {item.filename}")
    return {
        "entries": len(expected),
        "uncompressed_bytes": sum(size for size, _ in expected.values()),
        "archive_bytes": archive.stat().st_size,
        "archive_sha256": sha256(archive),
        "crc_and_identity_verified": True,
        "timestamps_normalized": True,
    }


def verify_reproducible_zip(staging: Path, archive: Path, files: list[Path]) -> bool:
    with tempfile.TemporaryDirectory(prefix="unit06-zip-repro-", dir=archive.parent) as temporary:
        replica = Path(temporary) / archive.name
        create_zip(staging, replica, files)
        if identity(replica) != identity(archive):
            raise SystemExit("second deterministic ZIP serialization differs from the first")
    return True


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--staging", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--expected-pdf-bytes", type=int, required=True)
    parser.add_argument("--expected-pdf-sha256", required=True)
    parser.add_argument("--expected-lecture-sha256", required=True)
    parser.add_argument("--expected-build-receipt-sha256", required=True)
    parser.add_argument("--expected-math-qa-sha256", required=True)
    parser.add_argument("--expected-structural-qa-sha256", required=True)
    parser.add_argument("--expected-backend-records", type=int, required=True)
    parser.add_argument("--expected-backend-qa-sha256", required=True)
    args = parser.parse_args()

    root = args.root.resolve()
    staging = (root / args.staging).resolve()
    archive = (root / args.archive).resolve()
    receipt = (root / args.receipt).resolve()
    if staging.exists():
        raise SystemExit(f"refusing to overwrite staging directory: {staging}")
    if archive.exists():
        raise SystemExit(f"refusing to overwrite archive: {archive}")
    if receipt.exists():
        raise SystemExit(f"refusing to overwrite package receipt: {receipt}")
    if root == staging:
        raise SystemExit("staging cannot be the project root")
    if archive == root or archive == staging or staging in archive.parents:
        raise SystemExit("archive path is unsafe or inside the staging tree")
    if receipt == root or receipt == staging or staging in receipt.parents:
        raise SystemExit("receipt path is unsafe or inside the staging tree")

    release_boundary = verify_release_boundary(
        root,
        args.expected_pdf_bytes,
        args.expected_pdf_sha256,
        args.expected_lecture_sha256,
        args.expected_build_receipt_sha256,
        args.expected_math_qa_sha256,
        args.expected_structural_qa_sha256,
        args.expected_backend_records,
        args.expected_backend_qa_sha256,
    )

    staging.mkdir(parents=True)
    for source, target in ROOT_FILE_MAP.items():
        copy_file(root, staging, source, target)
    for name in CONTROL_FILES:
        copy_file(root, staging, f"00_control/{name}")
    for path in sorted((root / "00_control").glob("*_PROTECTED_CORRECTIONS.json")):
        copy_file(root, staging, path.relative_to(root).as_posix())
    for name in AUTHORITY_FILES:
        copy_file(root, staging, f"authority/{name}")
    for relative in TREE_DIRS:
        copy_tree(root, staging, relative)
    for name in BUILD_FILES:
        copy_file(root, staging, f"build/{name}")
    for name in SCRIPT_FILES:
        copy_file(root, staging, f"scripts/{name}")
    for relative in QA_DIRS:
        copy_tree(root, staging, relative)
    for name in QA_ROOT_FILES:
        copy_file(root, staging, f"qa/{name}")

    write_internal_manifests(staging)
    files, privacy_scan = verify_staging(staging)
    create_zip(staging, archive, files)
    package = verify_zip(staging, archive, files)
    package["archive_path"] = project_relative(root, archive)
    package["reproducible_second_serialization"] = verify_reproducible_zip(
        staging, archive, files
    )
    result = {
        "schema_version": 1,
        "status": "pass",
        "workflow": "o011-stage-zenodo-unit06-v1",
        "coverage": "active_partial_through_unit_06",
        "staging": project_relative(root, staging),
        "staged_files": len(files),
        "staged_bytes": sum(path.stat().st_size for path in files),
        "release_boundary": release_boundary,
        "privacy_scan": privacy_scan,
        "package": package,
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
