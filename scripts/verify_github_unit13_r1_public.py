#!/usr/bin/env python3
"""Verify the public GitHub Unit 13 r1 commit, tag, release, and assets."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


OWNER = "KokunoYumeto"
REPOSITORY = "brenner-differentialgeometrie-id"
TAG = "v0.13.1-unit-13"
COMMIT = "56f2b2b4d11592ecb311f7e317b92ae591f752ab"
TITLE = "Geometri Diferensial dan Manifold Mulus — Batas Unit 13 r1"
VERSION = "2026.08.25-unit13-r1"
ZENODO_DOI = "10.5281/zenodo.22097422"
MODEL = "OpenAI Codex gpt-5.6-sol, Ultra"
PREPARATION = "qa/unit-13/RELEASE_PREPARATION_RECEIPT_R1.json"
DEFAULT_RECEIPT = "qa/unit-13/GITHUB_PUBLIC_READBACK_RECEIPT_R1.json"


def fail(message: str) -> None:
    raise RuntimeError(message)


def load_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        fail(f"cannot read {label}: {exc}")
    if not isinstance(value, dict):
        fail(f"{label} is not a JSON object")
    return value


def api_json(url: str, label: str) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "O011-unit13-r1-anonymous-github-verifier/1.0",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            if response.status != 200:
                fail(f"{label} returned HTTP {response.status}")
            value = json.load(response)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        fail(f"cannot read {label}: {exc}")
    if not isinstance(value, dict):
        fail(f"{label} returned a non-object")
    return value


def stream_identity(url: str, label: str) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={"Accept": "*/*", "User-Agent": "O011-unit13-r1-anonymous-github-verifier/1.0"},
        method="GET",
    )
    sha = hashlib.sha256()
    md5 = hashlib.md5()
    size = 0
    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            if response.status != 200:
                fail(f"{label} returned HTTP {response.status}")
            while True:
                block = response.read(1024 * 1024)
                if not block:
                    break
                size += len(block)
                sha.update(block)
                md5.update(block)
    except (urllib.error.URLError, TimeoutError) as exc:
        fail(f"cannot download {label}: {exc}")
    return {"bytes": size, "sha256": sha.hexdigest(), "md5": md5.hexdigest()}


def inside(root: Path, value: Path, label: str) -> Path:
    path = (value if value.is_absolute() else root / value).resolve()
    if path == root or root not in path.parents:
        fail(f"{label} must remain inside the project root")
    return path


def write_once(path: Path, value: dict[str, Any]) -> None:
    if path.exists():
        fail(f"refusing to overwrite receipt: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    temporary = path.with_name(path.name + ".tmp")
    if temporary.exists():
        temporary.unlink()
    temporary.write_bytes(payload)
    os.replace(temporary, path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--receipt", type=Path, default=Path(DEFAULT_RECEIPT))
    args = parser.parse_args()
    root = args.root.resolve()
    receipt_path = inside(root, args.receipt, "receipt")
    preparation_path = root / PREPARATION
    preparation = load_object(preparation_path, "release-preparation receipt")
    rows = preparation.get("files")
    if (
        preparation.get("status") != "pass"
        or preparation.get("workflow") != "o011-prepare-release-unit13-source-r1-v1"
        or not isinstance(rows, list)
        or len(rows) != 7
    ):
        fail("release-preparation receipt is not the exact passing r1 stage")
    expected = {str(row["filename"]): row for row in rows if isinstance(row, dict)}
    if len(expected) != 7:
        fail("staged file inventory is malformed")

    base = f"https://api.github.com/repos/{OWNER}/{REPOSITORY}"
    ref = api_json(f"{base}/git/ref/tags/{TAG}", "public tag ref")
    ref_object = ref.get("object") or {}
    if ref.get("ref") != f"refs/tags/{TAG}" or ref_object.get("type") != "tag":
        fail("public ref is not the expected annotated tag")
    tag_object = api_json(f"{base}/git/tags/{ref_object.get('sha')}", "public annotated tag")
    target = tag_object.get("object") or {}
    if target.get("type") != "commit" or target.get("sha") != COMMIT:
        fail("public annotated tag does not target the exact corrective commit")
    commit = api_json(f"{base}/commits/{COMMIT}", "public corrective commit")
    if commit.get("sha") != COMMIT or (commit.get("commit") or {}).get("message") != "Correct Unit 13 resumable source package":
        fail("public corrective commit identity/message differs")

    release = api_json(f"{base}/releases/tags/{TAG}", "public release")
    assets = release.get("assets")
    if (
        release.get("tag_name") != TAG
        or release.get("name") != TITLE
        or release.get("draft") is not False
        or release.get("prerelease") is not False
        or not isinstance(assets, list)
    ):
        fail("public release metadata/status differs")
    body = str(release.get("body") or "")
    for phrase in (VERSION, MODEL, "Unit 13"):
        if phrase not in body:
            fail(f"public release notes omit {phrase!r}")
    asset_map = {str(asset.get("name")): asset for asset in assets if isinstance(asset, dict)}
    if set(asset_map) != set(expected) or len(asset_map) != len(expected):
        fail("public release asset inventory differs from the exact seven-file stage")

    verified: list[dict[str, Any]] = []
    for name in preparation.get("public_file_order", []):
        if name not in expected or name not in asset_map:
            fail(f"missing expected public asset: {name}")
        wanted = expected[name]
        asset = asset_map[name]
        if asset.get("size") != wanted.get("bytes") or asset.get("state") != "uploaded":
            fail(f"public asset inventory identity differs: {name}")
        url = asset.get("browser_download_url")
        if not isinstance(url, str) or not url.startswith(f"https://github.com/{OWNER}/{REPOSITORY}/releases/download/{TAG}/"):
            fail(f"unsafe or unexpected public asset URL: {name}")
        actual = stream_identity(url, name)
        if actual != {key: wanted.get(key) for key in ("bytes", "sha256", "md5")}:
            fail(f"anonymous public asset bytes differ: {name}")
        verified.append({"name": name, **actual, "download_url": url})

    latest = api_json(f"{base}/releases/latest", "latest public release")
    if latest.get("id") != release.get("id"):
        fail("Unit 13 r1 is not the repository's latest release")
    raw_readme = stream_identity(
        f"https://raw.githubusercontent.com/{OWNER}/{REPOSITORY}/{COMMIT}/README.md",
        "public README at corrective commit",
    )
    local_readme = root / "README.md"
    local_readme_identity = {
        "bytes": local_readme.stat().st_size,
        "sha256": hashlib.sha256(local_readme.read_bytes()).hexdigest(),
        "md5": hashlib.md5(local_readme.read_bytes()).hexdigest(),
    }
    if raw_readme != local_readme_identity or ZENODO_DOI not in local_readme.read_text(encoding="utf-8"):
        fail("public corrective README differs or omits the current Zenodo DOI")

    receipt = {
        "schema_version": 1,
        "workflow": "o011-independent-github-unit13-r1-public-readback-v1",
        "status": "pass",
        "verified_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "authentication_used": False,
        "repository": f"https://github.com/{OWNER}/{REPOSITORY}",
        "commit": COMMIT,
        "annotated_tag": TAG,
        "release_id": release.get("id"),
        "release_url": release.get("html_url"),
        "release_latest": True,
        "release_draft": False,
        "release_prerelease": False,
        "version": VERSION,
        "zenodo_doi": ZENODO_DOI,
        "public_files": verified,
        "file_count": len(verified),
        "total_bytes": sum(int(row["bytes"]) for row in verified),
        "all_downloaded_bytes_sha256_md5_match": True,
        "reader_first_expected_order": preparation.get("public_file_order"),
        "public_api_asset_order": [asset.get("name") for asset in assets],
        "public_readme": raw_readme,
        "preparation_receipt_sha256": hashlib.sha256(preparation_path.read_bytes()).hexdigest(),
    }
    write_once(receipt_path, receipt)
    print(json.dumps({"status": "pass", "commit": COMMIT, "tag": TAG, "files": len(verified), "bytes": receipt["total_bytes"], "receipt": receipt_path.relative_to(root).as_posix()}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
