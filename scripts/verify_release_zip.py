#!/usr/bin/env python3
"""Verify a deterministic release ZIP against its embedded manifest."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import zipfile
from pathlib import PurePosixPath, Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", dest="zip_path", type=Path, required=True)
    parser.add_argument("--manifest", default="BUNDLE_MANIFEST.csv")
    args = parser.parse_args()

    zip_path = args.zip_path.resolve()
    with zipfile.ZipFile(zip_path, "r") as archive:
        bad_member = archive.testzip()
        if bad_member is not None:
            raise SystemExit(f"CRC failure: {bad_member}")
        infos = [info for info in archive.infolist() if not info.is_dir()]
        names = [info.filename for info in infos]
        if len(names) != len(set(names)):
            raise SystemExit("duplicate ZIP member name")
        for name in names:
            parsed = PurePosixPath(name)
            if (
                name.startswith("/")
                or "\\" in name
                or ":" in name
                or ".." in parsed.parts
            ):
                raise SystemExit(f"unsafe ZIP member: {name}")
        if args.manifest not in names:
            raise SystemExit(f"missing embedded manifest: {args.manifest}")

        manifest_text = archive.read(args.manifest).decode("utf-8-sig")
        rows = list(csv.DictReader(io.StringIO(manifest_text)))
        manifest_paths = [row["path"] for row in rows]
        if len(manifest_paths) != len(set(manifest_paths)):
            raise SystemExit("duplicate embedded-manifest path")
        expected = {row["path"] for row in rows} | {args.manifest}
        actual = set(names)
        if expected != actual:
            raise SystemExit(
                json.dumps(
                    {
                        "missing": sorted(expected - actual),
                        "unexpected": sorted(actual - expected),
                    },
                    ensure_ascii=False,
                )
            )

        info_by_name = {info.filename: info for info in infos}
        for row in rows:
            data = archive.read(row["path"])
            if len(data) != int(row["bytes"]):
                raise SystemExit(f"byte mismatch: {row['path']}")
            if hashlib.sha256(data).hexdigest() != row["sha256"]:
                raise SystemExit(f"SHA-256 mismatch: {row['path']}")
            if info_by_name[row["path"]].file_size != int(row["bytes"]):
                raise SystemExit(f"ZIP metadata size mismatch: {row['path']}")

        result = {
            "status": "pass",
            "zip": str(zip_path),
            "members": len(infos),
            "manifest_rows": len(rows),
            "uncompressed_bytes": sum(info.file_size for info in infos),
            "zip_bytes": zip_path.stat().st_size,
            "zip_sha256": hashlib.sha256(zip_path.read_bytes()).hexdigest(),
            "encrypted_members": sum(bool(info.flag_bits & 0x1) for info in infos),
        }
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
