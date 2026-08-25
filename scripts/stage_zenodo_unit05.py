#!/usr/bin/env python3
"""Stage the explicit, redistributable Unit 5 source/backend preservation tree."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path


ROOT_FILES = (".gitattributes", ".gitignore", "README.md", "LICENSE.md")
ROOT_DIRS = ("00_control", "backend", "build", "qa", "scripts", "source")
AUTHORITY_ROOT_FILES = (
    "brenner_94_link_classification.csv",
    "brenner_export_and_title_inventory_receipt.txt",
    "brenner_media_rights_manifest.csv",
    "brenner_selected_root_revisions.csv",
    "brenner_selected_surface_revisions.csv",
)
AUTHORITY_DIRS = ("expanded", "exports", "media", "mediawiki")
TRANSIENT_NAMES = {"__pycache__"}
TRANSIENT_SUFFIXES = {
    ".aux",
    ".bbl",
    ".bcf",
    ".blg",
    ".idx",
    ".ilg",
    ".ind",
    ".log",
    ".lof",
    ".out",
    ".pyc",
    ".run.xml",
    ".toc",
    ".fls",
    ".fdb_latexmk",
    ".synctex.gz",
}
SENSITIVE_NAME_FRAGMENTS = ("token", "credential", "secret", "password")
LOCAL_ONLY_PATHS = {
    "00_control/PRIVATE_LOCAL_LOCATORS.md",
    "scripts/publish_zenodo_unit05.py",
    "scripts/publish_zenodo_unit05_revision.py",
    "scripts/publish_figshare_unit05_link.py",
    "scripts/audit_figshare_project_size.py",
    "scripts/verify_figshare_unit05_link.py",
    "scripts/verify_zenodo_public_unit05.py",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--staging", type=Path, required=True)
    args = parser.parse_args()

    root = args.root.resolve()
    staging = args.staging.resolve()
    if staging.exists():
        raise SystemExit(f"refusing to overwrite staging directory: {staging}")
    if root == staging or staging in root.parents:
        raise SystemExit("staging must be inside or beside the project, not its parent")
    staging.mkdir(parents=True)

    for relative in ROOT_FILES:
        source = root / relative
        if not source.is_file():
            raise SystemExit(f"required file missing: {source}")
        shutil.copy2(source, staging / relative)
    for relative in ROOT_DIRS:
        source = root / relative
        if not source.is_dir():
            raise SystemExit(f"required directory missing: {source}")
        shutil.copytree(source, staging / relative)

    authority_target = staging / "authority"
    authority_target.mkdir()
    for relative in AUTHORITY_ROOT_FILES:
        source = root / "authority" / relative
        if not source.is_file():
            raise SystemExit(f"required authority file missing: {source}")
        shutil.copy2(source, authority_target / relative)
    for relative in AUTHORITY_DIRS:
        source = root / "authority" / relative
        if not source.is_dir():
            raise SystemExit(f"required authority directory missing: {source}")
        shutil.copytree(source, authority_target / relative)

    for path in sorted(staging.rglob("*"), reverse=True):
        if path.is_dir() and path.name in TRANSIENT_NAMES:
            shutil.rmtree(path)
        elif path.is_file() and any(path.name.lower().endswith(suffix) for suffix in TRANSIENT_SUFFIXES):
            path.unlink()

    for relative in sorted(LOCAL_ONLY_PATHS):
        local_only = staging / relative
        if local_only.is_file():
            local_only.unlink()

    files = sorted(path for path in staging.rglob("*") if path.is_file())
    sensitive_names = [
        path.relative_to(staging).as_posix()
        for path in files
        if path.name.lower() == ".env"
        or path.name.lower().startswith(".env.")
        or any(fragment in path.name.lower() for fragment in SENSITIVE_NAME_FRAGMENTS)
    ]
    if sensitive_names:
        raise SystemExit(
            "refusing to stage sensitive-looking filenames: "
            + ", ".join(sensitive_names)
        )
    result = {
        "status": "staged",
        "path": str(staging),
        "files": len(files),
        "bytes": sum(path.stat().st_size for path in files),
        "tree_sha256": hashlib.sha256(
            "".join(
                f"{path.relative_to(staging).as_posix()}\0{path.stat().st_size}\0{sha256(path)}\n"
                for path in files
            ).encode("utf-8")
        ).hexdigest(),
        "excluded": [
            ".git/",
            "tmp/",
            "output/ (PDF is uploaded separately)",
            "authority/pdf/ (historical witnesses are not redistribution assets)",
            "texput.log",
            "credentials",
            "private local locators and publication-operation scripts",
            "transient TeX/Python build files",
        ],
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
