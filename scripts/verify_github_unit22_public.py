#!/usr/bin/env python3
"""Anonymously verify the public GitHub Unit 22 tag, release, and assets."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import urllib.request
from pathlib import Path
from typing import Any


OWNER = "KokunoYumeto"
REPOSITORY = "brenner-differentialgeometrie-id"
TAG = "v0.22.0-unit-22"
VERSION = "2026.08.28-unit22"
RELEASE_TITLE = "Bahasa Indonesia checkpoint through Unit 22"
PREDECESSOR_COMMIT = "e470fa5897708f49596488083b442c494ca9ab0e"
PREDECESSOR_TAG = "v0.19.0-unit-19"
PREPARATION = Path("qa/unit-22/RELEASE_PREPARATION_RECEIPT.json")
DEFAULT_RECEIPT = Path("qa/unit-22/GITHUB_PUBLIC_READBACK_RECEIPT.json")


def fail(message: str) -> None:
    raise RuntimeError(message)


def api_json(url: str) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "O011-unit22-anonymous-github-verifier/1.0",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(request, timeout=180) as response:
        value = json.load(response)
    if not isinstance(value, dict):
        fail(f"non-object response from {url}")
    return value


def tag_commit(base: str, tag: str) -> str:
    ref = api_json(f"{base}/git/ref/tags/{tag}")
    target = ref.get("object") or {}
    if target.get("type") == "tag":
        target = api_json(f"{base}/git/tags/{target.get('sha')}").get("object") or {}
    sha = target.get("sha")
    if target.get("type") != "commit" or not isinstance(sha, str) or len(sha) != 40:
        fail(f"tag {tag} does not resolve to a commit")
    return sha.lower()


def stream_identity(url: str) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "O011-unit22-anonymous-github-verifier/1.0"},
    )
    sha256 = hashlib.sha256()
    md5 = hashlib.md5()
    size = 0
    with urllib.request.urlopen(request, timeout=300) as response:
        while True:
            block = response.read(1024 * 1024)
            if not block:
                break
            size += len(block)
            sha256.update(block)
            md5.update(block)
    return {"bytes": size, "sha256": sha256.hexdigest(), "md5": md5.hexdigest()}


def write_once(path: Path, value: dict[str, Any]) -> None:
    if path.exists():
        fail(f"refusing to overwrite {path}")
    serialized = json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n"
    lowered = serialized.lower()
    if any(marker in lowered for marker in ("access_token", "authorization: bearer", "github_pat_")):
        fail("receipt failed credential scan")
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(serialized, encoding="utf-8", newline="\n")
    os.replace(temporary, path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--receipt", type=Path, default=DEFAULT_RECEIPT)
    args = parser.parse_args()
    root = args.root.resolve()
    receipt_path = (root / args.receipt).resolve()
    receipt_path.relative_to(root)
    commit = args.commit.lower()
    if len(commit) != 40 or any(char not in "0123456789abcdef" for char in commit):
        fail("--commit must be one full SHA-1")

    stage_path = root / PREPARATION
    stage = json.loads(stage_path.read_text(encoding="utf-8"))
    if (
        stage.get("status") != "pass"
        or stage.get("workflow") != "o011-prepare-release-unit22-v1"
        or stage.get("version") != VERSION
        or stage.get("coverage") != "active_partial_through_unit_22"
    ):
        fail("Unit 22 release-preparation receipt is not exact")
    rows = stage.get("files")
    if not isinstance(rows, list) or len(rows) != 7:
        fail("Unit 22 stage must contain seven files")
    expected = {str(row["filename"]): row for row in rows}

    base = f"https://api.github.com/repos/{OWNER}/{REPOSITORY}"
    if tag_commit(base, TAG) != commit:
        fail("Unit 22 tag target differs")
    if tag_commit(base, PREDECESSOR_TAG) != PREDECESSOR_COMMIT:
        fail("Unit 19 predecessor tag changed")
    comparison = api_json(f"{base}/compare/{PREDECESSOR_COMMIT}...{commit}")
    if comparison.get("status") != "ahead" or comparison.get("behind_by") != 0:
        fail("Unit 22 commit is not a descendant of Unit 19")
    public_commit = api_json(f"{base}/commits/{commit}")
    if public_commit.get("sha") != commit or "Unit 22" not in str((public_commit.get("commit") or {}).get("message") or ""):
        fail("Unit 22 public commit identity differs")

    release = api_json(f"{base}/releases/tags/{TAG}")
    assets = release.get("assets")
    if (
        release.get("tag_name") != TAG
        or release.get("name") != RELEASE_TITLE
        or release.get("draft") is not False
        or release.get("prerelease") is not False
        or not isinstance(assets, list)
    ):
        fail("Unit 22 release metadata differs")
    asset_map = {str(row.get("name")): row for row in assets if isinstance(row, dict)}
    if set(asset_map) != set(expected) or len(asset_map) != 7:
        fail("Unit 22 release asset inventory differs")

    verified: list[dict[str, Any]] = []
    for name in stage.get("public_file_order", []):
        wanted = expected[name]
        asset = asset_map[name]
        if asset.get("state") != "uploaded" or asset.get("size") != wanted.get("bytes"):
            fail(f"GitHub inventory mismatch for {name}")
        url = str(asset.get("browser_download_url") or "")
        if not url.startswith(f"https://github.com/{OWNER}/{REPOSITORY}/releases/download/{TAG}/"):
            fail(f"unexpected asset URL for {name}")
        actual = stream_identity(url)
        wanted_identity = {key: wanted.get(key) for key in ("bytes", "sha256", "md5")}
        if actual != wanted_identity:
            fail(f"anonymous bytes differ for {name}")
        verified.append({"name": name, **actual, "download_url": url})

    latest = api_json(f"{base}/releases/latest")
    if latest.get("id") != release.get("id"):
        fail("Unit 22 is not the latest GitHub release")
    receipt = {
        "schema_version": 1,
        "workflow": "o011-independent-github-unit22-public-readback-v1",
        "status": "pass",
        "verified_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "authentication_used": False,
        "repository": f"https://github.com/{OWNER}/{REPOSITORY}",
        "commit": commit,
        "annotated_tag": TAG,
        "predecessor_commit": PREDECESSOR_COMMIT,
        "predecessor_tag": PREDECESSOR_TAG,
        "release_id": release.get("id"),
        "release_url": release.get("html_url"),
        "release_latest": True,
        "release_draft": False,
        "release_prerelease": False,
        "version": VERSION,
        "public_files": verified,
        "file_count": len(verified),
        "total_bytes": sum(int(row["bytes"]) for row in verified),
        "all_downloaded_bytes_sha256_md5_match": True,
        "reader_first_expected_order": stage.get("public_file_order"),
        "public_api_asset_order": [row.get("name") for row in assets],
        "preparation_receipt_sha256": hashlib.sha256(stage_path.read_bytes()).hexdigest(),
    }
    write_once(receipt_path, receipt)
    print(json.dumps({"status": "pass", "release_id": release.get("id"), "files": len(verified), "bytes": receipt["total_bytes"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
