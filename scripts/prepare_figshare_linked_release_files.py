#!/usr/bin/env python3
"""Create the compact manifest and checksum surfaces for the Unit 5 links."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "figshare"
FILES = (
    (
        ROOT / "output" / "pdf" / "geometri-diferensial-manifold-mulus-hingga-unit-05-id.pdf",
        "geometri-diferensial-manifold-mulus-hingga-unit-05-id.pdf",
        "primary reader; cumulative partial edition through Lecture/Worksheet 5",
        "CC BY-SA 4.0 text/adaptation; component media retain file-specific rights",
    ),
    (
        ROOT / "output" / "zenodo" / "geometri-diferensial-manifold-mulus-brenner-id-unit05-20260822.zip",
        "geometri-diferensial-manifold-mulus-brenner-id-unit05-20260822.zip",
        "compact resumable source, stable-ID backend, rights ledgers, build scripts, and QA",
        "mixed open rights exactly as documented by LICENSE.md and embedded media ledger",
    ),
    (
        ROOT / "LICENSE.md",
        "LICENSE.md",
        "rights, attribution, component-license, and non-endorsement notice",
        "license notice; describes CC BY-SA 4.0 text/adaptation and file-specific media rights",
    ),
    (
        ROOT / "qa" / "unit-05" / "RELEASE_NOTES_20260822.md",
        "RELEASE_NOTES_20260822.md",
        "coverage, QA, accessibility, provenance, and incompleteness disclosure",
        "CC BY-SA 4.0",
    ),
)


def digest(path: Path, algorithm: str) -> str:
    value = hashlib.new(algorithm)
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, str | int]] = []
    for path, name, role, rights in FILES:
        if not path.is_file():
            raise SystemExit(f"required release file missing: {path}")
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

    manifest = OUTPUT / "FILE_MANIFEST.csv"
    with manifest.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=("filename", "role", "bytes", "sha256", "md5", "rights_scope"),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)

    checksum_rows = [(str(row["sha256"]), str(row["filename"])) for row in rows]
    checksum_rows.append((digest(manifest, "sha256"), manifest.name))
    checksums = OUTPUT / "CHECKSUMS.sha256"
    checksums.write_text(
        "".join(f"{sha256}  {name}\n" for sha256, name in checksum_rows),
        encoding="ascii",
        newline="\n",
    )

    print(f"manifest={manifest} bytes={manifest.stat().st_size} sha256={digest(manifest, 'sha256')}")
    print(f"checksums={checksums} bytes={checksums.stat().st_size} sha256={digest(checksums, 'sha256')}")
    print(f"substantive_bytes={sum(int(row['bytes']) for row in rows)}")


if __name__ == "__main__":
    main()
