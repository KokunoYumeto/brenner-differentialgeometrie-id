#!/usr/bin/env python3
"""Create a compact, deterministic, privacy-checked Unit 7 source package."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import tempfile
import zipfile
from pathlib import Path

ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
MODEL = "OpenAI Codex gpt-5.6-sol, Ultra"
PDF_REL = "output/pdf/geometri-diferensial-manifold-mulus-hingga-unit-07-id.pdf"
TRANSIENT_NAMES = {"__pycache__", ".pytest_cache", ".mypy_cache"}
TRANSIENT_SUFFIXES = {".aux", ".bbl", ".bcf", ".blg", ".fdb_latexmk", ".fls", ".idx", ".ilg", ".ind", ".lof", ".log", ".out", ".pyc", ".run.xml", ".synctex.gz", ".toc"}
QA_EXCLUDED = ("FIGSHARE_", "ZENODO_", "PUBLICATION_RECEIPT", "RELEASE_NOTES_", "LICENSE_RELEASE_", "PACKAGE_README", "_debug", "_latest", "_sanitize")
SENSITIVE = ("token", "credential", "secret", "password", ".env")
TEXT_SUFFIXES = {"", ".csv", ".json", ".jsonl", ".md", ".ps1", ".py", ".svg", ".tex", ".txt"}
PRIVATE_PATTERNS = (
    re.compile(rb"[A-Za-z]:[\\/]+Users[\\/]", re.I),
    re.compile(rb"(?<!:)\/Users\/", re.I),
    re.compile(rb"\\\\[^\\\r\n]+\\Users\\", re.I),
)
SECRET_PATTERNS = (
    re.compile(rb"github_pat_[A-Za-z0-9_]{40,}"),
    re.compile(rb"gh[pousr]_[A-Za-z0-9]{36,}"),
    re.compile(rb"(?:access[_-]?token|api[_-]?token|password|secret)\s*[:=]\s*[\"'][^\"'\r\n]{16,}[\"']", re.I),
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def identity(path: Path) -> dict[str, int | str]:
    return {"bytes": path.stat().st_size, "sha256": sha256(path)}


def rel(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def copy_one(root: Path, staging: Path, source: str, target: str | None = None) -> None:
    src = root / source
    if not src.is_file():
        raise RuntimeError(f"required package file is missing: {source}")
    dst = staging / (target or source)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)


def allowed_qa(path: Path) -> bool:
    name = path.name
    return not any(fragment.lower() in name.lower() for fragment in QA_EXCLUDED)


def copy_tree(root: Path, staging: Path, source_root: str, predicate=None) -> None:
    base = root / source_root
    if not base.is_dir():
        raise RuntimeError(f"required package directory is missing: {source_root}")
    for src in sorted(p for p in base.rglob("*") if p.is_file()):
        if any(part in TRANSIENT_NAMES for part in src.parts) or src.suffix.lower() in TRANSIENT_SUFFIXES:
            continue
        if predicate is not None and not predicate(src):
            continue
        copy_one(root, staging, rel(root, src))


def write_manifests(staging: Path) -> None:
    files = sorted((p for p in staging.rglob("*") if p.is_file()), key=lambda p: rel(staging, p))
    rows = [{"path": rel(staging, p), **identity(p)} for p in files]
    tree = hashlib.sha256("".join(f"{r['path']}\0{r['bytes']}\0{r['sha256']}\n" for r in rows).encode()).hexdigest()
    manifest = {
        "schema_version": 1,
        "workflow": "o011-unit07-compact-source-package-v1",
        "status": "active_partial",
        "coverage": "Kuliah 1-7 dan Lembar Kerja 1-7 dari 29 pasangan inti",
        "model_identification": MODEL,
        "files_excluding_manifest_surfaces": len(rows),
        "bytes_excluding_manifest_surfaces": sum(int(r["bytes"]) for r in rows),
        "tree_sha256": tree,
        "files": rows,
        "deliberate_exclusions": [
            "PDF reader (published as the primary separate file)",
            "raw MediaWiki/XML export dumps and redundant export trees",
            "historical witness PDFs and duplicate generated build trees",
            "temporary renders, caches, TeX auxiliaries, private locators, credentials, and remote-publication operation files",
        ],
    }
    (staging / "PACKAGE_MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    all_files = sorted((p for p in staging.rglob("*") if p.is_file()), key=lambda p: rel(staging, p))
    (staging / "PACKAGE_CHECKSUMS.sha256").write_text("".join(f"{sha256(p)}  {rel(staging,p)}\n" for p in all_files), encoding="ascii", newline="\n")


def verify_staging(staging: Path) -> dict[str, int]:
    files = sorted((p for p in staging.rglob("*") if p.is_file()), key=lambda p: rel(staging, p))
    if not files:
        raise RuntimeError("staging tree is empty")
    private_hits: list[str] = []
    secret_hits: list[str] = []
    scanned_text = 0
    for path in files:
        if path.suffix.lower() in TEXT_SUFFIXES:
            scanned_text += 1
            payload = path.read_bytes()
            if any(pattern.search(payload) for pattern in PRIVATE_PATTERNS):
                private_hits.append(rel(staging, path))
            if any(pattern.search(payload) for pattern in SECRET_PATTERNS):
                secret_hits.append(rel(staging, path))
    if private_hits:
        raise RuntimeError("private locator content found: " + ", ".join(private_hits))
    if secret_hits:
        raise RuntimeError("credential-like content found: " + ", ".join(secret_hits))
    sensitive_names = [rel(staging, p) for p in files if any(fragment in p.name.lower() for fragment in SENSITIVE)]
    if sensitive_names:
        raise RuntimeError("sensitive-looking filenames found: " + ", ".join(sensitive_names))
    notes = next((p for p in files if p.name == "RELEASE_NOTES_20260823.md"), None)
    if notes is None or MODEL not in notes.read_text(encoding="utf-8"):
        raise RuntimeError("release notes/model provenance missing")
    for forbidden in ("TTP", "Translation and Transcription Project"):
        if forbidden in notes.read_text(encoding="utf-8"):
            raise RuntimeError("umbrella label leaked into release prose")
    return {"all_files_raw_bytes_scanned": len(files), "text_files_scanned": scanned_text, "private_locator_hits": 0, "credential_like_content_hits": 0}


def create_zip(staging: Path, archive: Path, files: list[Path]) -> None:
    archive.parent.mkdir(parents=True, exist_ok=True)
    if archive.exists():
        raise RuntimeError(f"refusing to overwrite archive: {archive}")
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=9, strict_timestamps=True) as bundle:
        for path in files:
            info = zipfile.ZipInfo(rel(staging, path), date_time=ZIP_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.flag_bits |= 0x800
            bundle.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def verify_zip(staging: Path, archive: Path, files: list[Path]) -> dict[str, object]:
    expected = {rel(staging, p): (p.stat().st_size, sha256(p)) for p in files}
    with zipfile.ZipFile(archive, "r") as bundle:
        infos = bundle.infolist()
        if [i.filename for i in infos] != sorted(expected):
            raise RuntimeError("ZIP inventory/order mismatch")
        if bundle.testzip() is not None:
            raise RuntimeError("ZIP CRC failure")
        for info in infos:
            data = bundle.read(info.filename)
            if (len(data), hashlib.sha256(data).hexdigest()) != expected[info.filename]:
                raise RuntimeError(f"ZIP entry identity mismatch: {info.filename}")
            if info.date_time != ZIP_TIMESTAMP:
                raise RuntimeError("ZIP timestamp is not normalized")
    return {"entries": len(expected), "uncompressed_bytes": sum(v[0] for v in expected.values()), "archive_bytes": archive.stat().st_size, "archive_sha256": sha256(archive), "crc_and_identity_verified": True, "timestamps_normalized": True}


def reproducible(staging: Path, archive: Path, files: list[Path]) -> bool:
    with tempfile.TemporaryDirectory(prefix="unit07-zip-repro-", dir=archive.parent) as tmp:
        replica = Path(tmp) / archive.name
        create_zip(staging, replica, files)
        if identity(replica) != identity(archive):
            raise RuntimeError("second deterministic ZIP serialization differs")
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--staging", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve(); staging = (root / args.staging).resolve(); archive = (root / args.archive).resolve(); receipt = (root / args.receipt).resolve()
    if staging.exists() or archive.exists() or receipt.exists():
        raise RuntimeError("refusing to overwrite existing staging, archive, or receipt")
    pdf = root / PDF_REL
    if not pdf.is_file():
        raise RuntimeError("settled PDF is missing")
    staging.mkdir(parents=True)
    for source, target in {
        "qa/unit-07/PACKAGE_README.md": "README.md",
        "qa/unit-07/LICENSE_RELEASE_UNIT07.md": "LICENSE.md",
        "qa/unit-07/RELEASE_NOTES_20260823.md": "RELEASE_NOTES_20260823.md",
    }.items():
        copy_one(root, staging, source, target)
    for source in ("00_control/ADVERSE_LEDGER.csv", "00_control/TERMINOLOGY.csv", "00_control/LECTURE07_PROTECTED_CORRECTIONS.json", "00_control/WORKSHEET07_PROTECTED_CORRECTIONS.json"):
        copy_one(root, staging, source)
    for source in ("authority/brenner_94_link_classification.csv", "authority/brenner_export_and_title_inventory_receipt.txt", "authority/brenner_media_rights_manifest.csv", "authority/brenner_selected_root_revisions.csv", "authority/brenner_selected_surface_revisions.csv"):
        copy_one(root, staging, source)
    # The expanded closure is already bounded to the seven admitted units
    # (lectureXX/worksheetXX source fragments and supplied solutions), plus
    # the portable preamble witness; no raw XML dump is present here.
    copy_tree(root, staging, "authority/expanded")
    copy_tree(root, staging, "authority/media")
    copy_tree(root, staging, "source", lambda p: ("unit_media.json" in p.name or "unit07_interactive_media.json" in p.name or "source/units/unit-" in p.as_posix() and any(f"unit-{u:02d}" in p.as_posix() for u in range(1,8))))
    copy_tree(root, staging, "backend")
    for source in ("brenner-compat.tex", "unit-01.tex", "through-unit-02.tex", "through-unit-03.tex", "through-unit-04.tex", "through-unit-05.tex", "through-unit-06.tex", "through-unit-07.tex"):
        copy_one(root, staging, f"build/{source}")
    script_names = ("build_unit01.ps1", "build_through_unit02.ps1", "build_through_unit03.ps1", "build_through_unit04.ps1", "build_through_unit05.ps1", "build_through_unit06.ps1", "build_through_unit07.ps1", "prepare_unit_media.py", "prepare_unit_tex.py", "verify_unit_translation.py", "verify_unit07_pdf_boundary.py", "export_backend_v6.py", "verify_backend_v6.py", "export_backend_v7.py", "verify_backend_v7.py")
    for source in script_names:
        if (root / "scripts" / source).is_file():
            copy_one(root, staging, f"scripts/{source}")
    for source_root in [f"qa/unit-{u:02d}" for u in range(1,8)] + ["qa/terminology"]:
        copy_tree(root, staging, source_root, allowed_qa)
    for source in ("qa/unit-01_media.json", "qa/unit-02_media.json", "qa/unit-03_media.json", "qa/unit-04_media.json", "qa/unit-05_media.json", "qa/unit-06_media.json", "qa/unit-07_media.json"):
        if (root / source).is_file():
            copy_one(root, staging, source)
    write_manifests(staging)
    privacy = verify_staging(staging)
    files = sorted((p for p in staging.rglob("*") if p.is_file()), key=lambda p: rel(staging, p))
    create_zip(staging, archive, files)
    package = verify_zip(staging, archive, files)
    package["archive_path"] = rel(root, archive)
    package["reproducible_second_serialization"] = reproducible(staging, archive, files)
    result = {"schema_version": 1, "status": "pass", "workflow": "o011-stage-zenodo-unit07-v1", "coverage": "active_partial_through_unit_07", "staging": rel(root, staging), "staged_files": len(files), "staged_bytes": sum(p.stat().st_size for p in files), "pdf": {"path": PDF_REL, **identity(pdf)}, "privacy_scan": privacy, "package": package, "remote_state_mutated": False}
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
