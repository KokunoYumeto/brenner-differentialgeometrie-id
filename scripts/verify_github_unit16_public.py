#!/usr/bin/env python3
"""Verify the public GitHub Unit 16 commit, tag, release, and seven assets."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


OWNER = "KokunoYumeto"
REPOSITORY = "brenner-differentialgeometrie-id"
TAG = "v0.16.0-unit-16"
TITLE = "Geometri Diferensial dan Manifold Mulus — Batas Unit 16"
VERSION = "2026.08.26-unit16"
MODEL = "OpenAI Codex gpt-5.6-sol, Ultra"
PREPARATION = "qa/unit-16/RELEASE_PREPARATION_RECEIPT.json"
INTEGRITY = "qa/unit-16/SOURCE_PACKAGE_INTEGRITY.json"
DEFAULT_RECEIPT = "qa/unit-16/GITHUB_PUBLIC_READBACK_RECEIPT.json"
EXPECTED_ORDER = [
    "geometri-diferensial-manifold-mulus-hingga-unit-16-id.pdf",
    "geometri-diferensial-manifold-mulus-unit16-html-20260826.zip",
    "geometri-diferensial-manifold-mulus-unit16-source-20260826.zip",
    "LICENSE.md",
    "RELEASE_NOTES_UNIT16_20260826.md",
    "FILE_MANIFEST.json",
    "SHA256SUMS.txt",
]
PDF_IDENTITY = {
    "bytes": 7_241_359,
    "sha256": "58f98853ab8eeb1beb2aa4ade6bd3c746b62b4fa42c3c692a03c17076cdb06b8",
}
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
DOI_RE = re.compile(r"^10\.5281/zenodo\.[1-9][0-9]*$")


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


def all_boolean_leaves_true(value: Any) -> bool:
    leaves: list[bool] = []

    def walk(item: Any) -> None:
        if isinstance(item, bool):
            leaves.append(item)
        elif isinstance(item, dict):
            for child in item.values():
                walk(child)
        elif isinstance(item, list):
            for child in item:
                walk(child)

    walk(value)
    return bool(leaves) and all(leaves)


def identity_occurs(value: Any, wanted: dict[str, Any]) -> bool:
    if isinstance(value, dict):
        if value.get("bytes") == wanted["bytes"] and value.get("sha256") == wanted["sha256"]:
            return True
        return any(identity_occurs(child, wanted) for child in value.values())
    if isinstance(value, list):
        return any(identity_occurs(child, wanted) for child in value)
    return False


def api_json(url: str, label: str) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "O011-unit16-anonymous-github-verifier/1.0",
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
        headers={"Accept": "*/*", "User-Agent": "O011-unit16-anonymous-github-verifier/1.0"},
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
    parser.add_argument("--commit", required=True, help="exact 40-character public commit SHA")
    parser.add_argument("--zenodo-doi", required=True, help="exact published Unit 16 version DOI")
    args = parser.parse_args()
    root = args.root.resolve()
    receipt_path = inside(root, args.receipt, "receipt")
    commit_sha = args.commit.lower()
    zenodo_doi = args.zenodo_doi
    if not COMMIT_RE.fullmatch(commit_sha):
        fail("--commit must be one exact lowercase-compatible 40-character SHA")
    if not DOI_RE.fullmatch(zenodo_doi):
        fail("--zenodo-doi is not an exact Zenodo version DOI")
    preparation_path = root / PREPARATION
    integrity_path = root / INTEGRITY
    preparation = load_object(preparation_path, "release-preparation receipt")
    integrity = load_object(integrity_path, "source-package integrity receipt")
    rows = preparation.get("files")
    if (
        preparation.get("status") != "pass"
        or preparation.get("workflow") != "o011-prepare-release-unit16-v1"
        or not isinstance(rows, list)
        or [row.get("filename") for row in rows if isinstance(row, dict)] != EXPECTED_ORDER
    ):
        fail("release-preparation receipt is not the exact passing Unit 16 stage")
    expected = {str(row["filename"]): row for row in rows if isinstance(row, dict)}
    if set(expected) != set(EXPECTED_ORDER) or len(expected) != 7:
        fail("staged file inventory is malformed")
    if preparation.get("public_file_order") != EXPECTED_ORDER:
        fail("staged reader-first order is not exact")
    source_identity = {
        key: expected[EXPECTED_ORDER[2]].get(key) for key in ("bytes", "sha256")
    }
    html_identity = {
        key: expected[EXPECTED_ORDER[1]].get(key) for key in ("bytes", "sha256")
    }
    clean = integrity.get("clean_rebuilds")
    if (
        integrity.get("schema_version") != 1
        or integrity.get("workflow") != "o011-verify-source-package-unit16-v1"
        or integrity.get("status") != "pass"
        or not identity_occurs(integrity.get("source_zip"), source_identity)
        or not isinstance(clean, list)
        or len(clean) != 2
        or any(not isinstance(item, dict) or item.get("status") != "pass" for item in clean)
        or any(not identity_occurs(item, PDF_IDENTITY) for item in clean)
        or any(not identity_occurs(item, html_identity) for item in clean)
        or not all_boolean_leaves_true(integrity.get("cross_cycle_identity"))
        or not all_boolean_leaves_true(integrity.get("checks"))
    ):
        fail("source-package integrity receipt lacks the exact passing two-cycle Unit 16 gate")

    base = f"https://api.github.com/repos/{OWNER}/{REPOSITORY}"
    ref = api_json(f"{base}/git/ref/tags/{TAG}", "public tag ref")
    ref_object = ref.get("object") or {}
    if ref.get("ref") != f"refs/tags/{TAG}":
        fail("public ref is not the expected Unit 16 tag")
    if ref_object.get("type") == "tag":
        tag_object = api_json(f"{base}/git/tags/{ref_object.get('sha')}", "public annotated tag")
        target = tag_object.get("object") or {}
    elif ref_object.get("type") == "commit":
        target = ref_object
    else:
        fail("public Unit 16 tag points to neither an annotated tag nor a commit")
    if target.get("type") != "commit" or target.get("sha") != commit_sha:
        fail("public Unit 16 tag does not target the exact supplied commit")
    commit = api_json(f"{base}/commits/{commit_sha}", "public Unit 16 commit")
    commit_message = str((commit.get("commit") or {}).get("message") or "")
    if commit.get("sha") != commit_sha or "Unit 16" not in commit_message:
        fail("public Unit 16 commit identity/message differs")

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
    for phrase in (VERSION, MODEL, "Unit 16", zenodo_doi):
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
        fail("Unit 16 is not the repository's latest release")
    raw_readme = stream_identity(
        f"https://raw.githubusercontent.com/{OWNER}/{REPOSITORY}/{commit_sha}/README.md",
        "public README at Unit 16 commit",
    )
    local_readme = root / "README.md"
    local_readme_identity = {
        "bytes": local_readme.stat().st_size,
        "sha256": hashlib.sha256(local_readme.read_bytes()).hexdigest(),
        "md5": hashlib.md5(local_readme.read_bytes()).hexdigest(),
    }
    if raw_readme != local_readme_identity or zenodo_doi not in local_readme.read_text(encoding="utf-8"):
        fail("public Unit 16 README differs or omits the current Zenodo DOI")

    receipt = {
        "schema_version": 1,
        "workflow": "o011-independent-github-unit16-public-readback-v1",
        "status": "pass",
        "verified_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "authentication_used": False,
        "repository": f"https://github.com/{OWNER}/{REPOSITORY}",
        "commit": commit_sha,
        "annotated_tag": TAG,
        "release_id": release.get("id"),
        "release_url": release.get("html_url"),
        "release_latest": True,
        "release_draft": False,
        "release_prerelease": False,
        "version": VERSION,
        "zenodo_doi": zenodo_doi,
        "public_files": verified,
        "file_count": len(verified),
        "total_bytes": sum(int(row["bytes"]) for row in verified),
        "all_downloaded_bytes_sha256_md5_match": True,
        "reader_first_expected_order": preparation.get("public_file_order"),
        "public_api_asset_order": [asset.get("name") for asset in assets],
        "public_readme": raw_readme,
        "preparation_receipt_sha256": hashlib.sha256(preparation_path.read_bytes()).hexdigest(),
        "source_package_integrity_receipt_sha256": hashlib.sha256(integrity_path.read_bytes()).hexdigest(),
    }
    write_once(receipt_path, receipt)
    print(json.dumps({"status": "pass", "commit": commit_sha, "tag": TAG, "files": len(verified), "bytes": receipt["total_bytes"], "receipt": receipt_path.relative_to(root).as_posix()}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
