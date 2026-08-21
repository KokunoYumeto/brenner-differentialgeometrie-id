#!/usr/bin/env python3
"""Generate the deterministic manifest for the narrow public edition tree."""

from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path


SKIP_DIRS = {".git", "tmp", "__pycache__"}
SKIP_SUFFIXES = {
    ".aux",
    ".bbl",
    ".bcf",
    ".blg",
    ".fdb_latexmk",
    ".fls",
    ".idx",
    ".ilg",
    ".ind",
    ".log",
    ".lof",
    ".out",
    ".pyc",
    ".run.xml",
    ".synctex.gz",
    ".toc",
}


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def skipped(relative: Path, output_relative: Path) -> bool:
    if relative == output_relative:
        return True
    if any(part in SKIP_DIRS for part in relative.parts):
        return True
    name = relative.name.lower()
    return any(name.endswith(suffix) for suffix in SKIP_SUFFIXES)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("qa/unit-01/RELEASE_MANIFEST.csv"),
    )
    args = parser.parse_args()

    root = args.project_root.resolve()
    output = (root / args.output).resolve()
    output_relative = output.relative_to(root)
    rows = []
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if skipped(relative, output_relative):
            continue
        rows.append(
            {
                "path": relative.as_posix(),
                "bytes": path.stat().st_size,
                "sha256": digest(path),
            }
        )

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["path", "bytes", "sha256"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"{len(rows)} files; {sum(row['bytes'] for row in rows)} bytes")


if __name__ == "__main__":
    main()
