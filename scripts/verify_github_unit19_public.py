#!/usr/bin/env python3
"""Verify the public GitHub Unit 19 commit, tag, release, and seven assets."""

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
TAG = "v0.19.0-unit-19"
TITLE = "Geometri Diferensial dan Manifold Mulus — Batas Unit 19"
VERSION = "2026.08.26-unit19"
MODEL = "OpenAI Codex gpt-5.6-sol, Ultra"
UNIT16_TAG = "v0.16.0-unit-16"
UNIT16_COMMIT = "a492e9d7c23991edd8cec7978533e80b44f86e6f"
UNIT16_READBACK = "qa/unit-16/GITHUB_PUBLIC_READBACK_RECEIPT.json"
UNIT16_READBACK_SHA256 = (
    "b2c8e160c13115a50cdd2f57484e7ce6172387b9cc713cd70d10bef640b3bea6"
)
ZENODO_CONCEPT_ID = 22059977
ZENODO_PREDECESSOR_ID = 22104426
ZENODO_TITLE = "Geometri Diferensial dan Manifold Mulus — Edisi Bahasa Indonesia (Batas Unit 19)"
PREPARATION = "qa/unit-19/RELEASE_PREPARATION_RECEIPT.json"
INTEGRITY = "qa/unit-19/SOURCE_PACKAGE_INTEGRITY.json"
DEFAULT_RECEIPT = "qa/unit-19/GITHUB_PUBLIC_READBACK_RECEIPT.json"
EXPECTED_ORDER = [
    "geometri-diferensial-manifold-mulus-hingga-unit-19-id.pdf",
    "geometri-diferensial-manifold-mulus-unit19-html-20260826.zip",
    "geometri-diferensial-manifold-mulus-unit19-source-20260826.zip",
    "LICENSE.md",
    "RELEASE_NOTES_UNIT19_20260826.md",
    "FILE_MANIFEST.json",
    "SHA256SUMS.txt",
]
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
DOI_RE = re.compile(r"^10\.5281/zenodo\.[1-9][0-9]*$")
TTP_RE = re.compile(r"(?i)(?:\bTTP\b|Translation\s+and\s+Transcription\s+Project)")


def fail(message: str) -> None:
    raise RuntimeError(message)


def local_profile_name_present(value: str) -> bool:
    if os.name != "nt":
        return False
    profile_name = Path.home().name.strip()
    if len(profile_name) < 4:
        return False
    return re.search(
        r"(?i)(?<![A-Za-z])" + re.escape(profile_name) + r"(?![A-Za-z])",
        value,
    ) is not None


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
            "User-Agent": "O011-unit19-anonymous-github-verifier/1.0",
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


def tag_commit(base: str, tag: str, label: str) -> str:
    ref = api_json(f"{base}/git/ref/tags/{tag}", f"{label} tag ref")
    ref_object = ref.get("object") or {}
    if ref.get("ref") != f"refs/tags/{tag}":
        fail(f"{label} ref is not the expected tag")
    if ref_object.get("type") == "tag":
        tag_object = api_json(
            f"{base}/git/tags/{ref_object.get('sha')}", f"{label} annotated tag"
        )
        target = tag_object.get("object") or {}
    elif ref_object.get("type") == "commit":
        target = ref_object
    else:
        fail(f"{label} tag points to neither an annotated tag nor a commit")
    sha = target.get("sha")
    if target.get("type") != "commit" or not isinstance(sha, str) or not COMMIT_RE.fullmatch(sha):
        fail(f"{label} tag does not resolve to one exact commit")
    return sha


def verify_zenodo_version(doi: str) -> dict[str, Any]:
    record_id = int(doi.rsplit(".", 1)[1])
    if record_id in (ZENODO_CONCEPT_ID, ZENODO_PREDECESSOR_ID):
        fail("--zenodo-doi must be the exact new Unit 19 version DOI, not a concept or predecessor DOI")
    url = f"https://zenodo.org/api/records/{record_id}"
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.inveniordm.v1+json",
            "User-Agent": "O011-unit19-anonymous-github-verifier/1.0",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            if response.status != 200:
                fail(f"public Zenodo Unit 19 record returned HTTP {response.status}")
            record = json.load(response)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        fail(f"cannot read public Zenodo Unit 19 record: {exc}")
    if not isinstance(record, dict):
        fail("public Zenodo Unit 19 record returned a non-object")
    metadata = record.get("metadata") or {}
    concept_id = str(record.get("conceptrecid") or (record.get("parent") or {}).get("id") or "")
    public_doi = str(
        record.get("doi")
        or (((record.get("pids") or {}).get("doi") or {}).get("identifier"))
        or ""
    )
    if (
        record.get("id") != record_id
        or concept_id != str(ZENODO_CONCEPT_ID)
        or public_doi != doi
        or record.get("status") != "published"
        or (record.get("access") or {}).get("record") != "public"
        or metadata.get("version") != VERSION
        or metadata.get("title") != ZENODO_TITLE
    ):
        fail("--zenodo-doi does not resolve to the exact public Unit 19 record in the existing concept")
    return {"record_id": record_id, "doi": doi, "concept_record_id": ZENODO_CONCEPT_ID}


def stream_identity(url: str, label: str) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={"Accept": "*/*", "User-Agent": "O011-unit19-anonymous-github-verifier/1.0"},
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
    parser.add_argument("--zenodo-doi", required=True, help="exact published Unit 19 version DOI")
    args = parser.parse_args()
    root = args.root.resolve()
    receipt_path = inside(root, args.receipt, "receipt")
    commit_sha = args.commit.lower()
    zenodo_doi = args.zenodo_doi
    if not COMMIT_RE.fullmatch(commit_sha):
        fail("--commit must be one exact lowercase-compatible 40-character SHA")
    if not DOI_RE.fullmatch(zenodo_doi):
        fail("--zenodo-doi is not an exact Zenodo version DOI")
    zenodo = verify_zenodo_version(zenodo_doi)
    preparation_path = root / PREPARATION
    integrity_path = root / INTEGRITY
    unit16_readback_path = root / UNIT16_READBACK
    preparation = load_object(preparation_path, "release-preparation receipt")
    integrity = load_object(integrity_path, "source-package integrity receipt")
    unit16_readback = load_object(unit16_readback_path, "Unit 16 GitHub public-readback receipt")
    if (
        hashlib.sha256(unit16_readback_path.read_bytes()).hexdigest()
        != UNIT16_READBACK_SHA256
        or unit16_readback.get("schema_version") != 1
        or unit16_readback.get("workflow")
        != "o011-independent-github-unit16-public-readback-v1"
        or unit16_readback.get("status") != "pass"
        or unit16_readback.get("authentication_used") is not False
        or unit16_readback.get("repository")
        != f"https://github.com/{OWNER}/{REPOSITORY}"
        or unit16_readback.get("commit") != UNIT16_COMMIT
        or unit16_readback.get("annotated_tag") != UNIT16_TAG
        or unit16_readback.get("version") != "2026.08.26-unit16"
    ):
        fail("exact Unit 16 GitHub public-readback proof is absent or changed")
    rows = preparation.get("files")
    if (
        preparation.get("schema_version") != 1
        or preparation.get("status") != "pass"
        or preparation.get("workflow") != "o011-prepare-release-unit19-v1"
        or preparation.get("version") != VERSION
        or preparation.get("coverage") != "active_partial_through_unit_19"
        or preparation.get("remote_state_mutated") is not False
        or not isinstance(rows, list)
        or [row.get("filename") for row in rows if isinstance(row, dict)] != EXPECTED_ORDER
    ):
        fail("release-preparation receipt is not the exact passing Unit 19 stage")
    expected = {str(row["filename"]): row for row in rows if isinstance(row, dict)}
    if set(expected) != set(EXPECTED_ORDER) or len(expected) != 7:
        fail("staged file inventory is malformed")
    if preparation.get("public_file_order") != EXPECTED_ORDER:
        fail("staged reader-first order is not exact")
    lineage = preparation.get("lineage")
    privacy = preparation.get("privacy_scan")
    if any(not isinstance(row.get("bytes"), int) or row["bytes"] < 0 for row in rows):
        fail("staged Unit 19 file sizes are malformed")
    total_public_bytes = sum(row["bytes"] for row in rows)
    if (
        lineage
        != {
            "concept_record_id": ZENODO_CONCEPT_ID,
            "predecessor_record_id": ZENODO_PREDECESSOR_ID,
            "new_concept_created": False,
        }
        or preparation.get("public_file_count") != len(EXPECTED_ORDER)
        or preparation.get("public_bytes") != total_public_bytes
        or preparation.get("total_public_bytes") != total_public_bytes
        or total_public_bytes > 500_000_000
        or not isinstance(privacy, dict)
        or privacy.get("status") != "pass"
        or privacy.get("private_locator_hits") != 0
        or privacy.get("credential_like_content_hits") != 0
        or privacy.get("local_profile_name_hits") != 0
    ):
        fail("staged Unit 19 lineage, size, or privacy contract is not exact")
    source_identity = {
        key: expected[EXPECTED_ORDER[2]].get(key) for key in ("bytes", "sha256")
    }
    html_identity = {
        key: expected[EXPECTED_ORDER[1]].get(key) for key in ("bytes", "sha256")
    }
    pdf_identity = {
        key: expected[EXPECTED_ORDER[0]].get(key) for key in ("bytes", "sha256")
    }
    if not identity_occurs(preparation.get("input_bindings"), pdf_identity):
        fail("release preparation does not bind its PDF to the validated reader gate")
    clean = integrity.get("clean_rebuilds")
    if (
        integrity.get("schema_version") != 1
        or integrity.get("workflow") != "o011-verify-source-package-unit19-v1"
        or integrity.get("status") != "pass"
        or not identity_occurs(integrity.get("source_zip"), source_identity)
        or not isinstance(clean, list)
        or len(clean) != 2
        or any(not isinstance(item, dict) or item.get("status") != "pass" for item in clean)
        or any(not identity_occurs(item, pdf_identity) for item in clean)
        or any(not identity_occurs(item, html_identity) for item in clean)
        or not all_boolean_leaves_true(integrity.get("cross_cycle_identity"))
        or not all_boolean_leaves_true(integrity.get("checks"))
    ):
        fail("source-package integrity receipt lacks the exact passing two-cycle Unit 19 gate")

    base = f"https://api.github.com/repos/{OWNER}/{REPOSITORY}"
    if tag_commit(base, TAG, "public Unit 19") != commit_sha:
        fail("public Unit 19 tag does not target the exact supplied commit")
    if tag_commit(base, UNIT16_TAG, "public Unit 16 predecessor") != UNIT16_COMMIT:
        fail("public Unit 16 predecessor tag changed")
    comparison = api_json(
        f"{base}/compare/{UNIT16_COMMIT}...{commit_sha}",
        "public Unit 16-to-Unit 19 ancestry comparison",
    )
    ahead_by = comparison.get("ahead_by")
    behind_by = comparison.get("behind_by")
    if (
        comparison.get("status") != "ahead"
        or not isinstance(ahead_by, int)
        or ahead_by <= 0
        or behind_by != 0
        or (comparison.get("base_commit") or {}).get("sha") != UNIT16_COMMIT
        or (comparison.get("merge_base_commit") or {}).get("sha") != UNIT16_COMMIT
    ):
        fail("public Unit 19 commit does not descend from the exact Unit 16 boundary")
    commit = api_json(f"{base}/commits/{commit_sha}", "public Unit 19 commit")
    commit_message = str((commit.get("commit") or {}).get("message") or "")
    if commit.get("sha") != commit_sha or "Unit 19" not in commit_message:
        fail("public Unit 19 commit identity/message differs")

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
    if TTP_RE.search(TITLE) or TTP_RE.search(body):
        fail("umbrella organization label leaked into the GitHub release title or notes")
    if local_profile_name_present(TITLE + "\n" + body):
        fail("local profile name leaked into the GitHub release title or notes")
    for phrase in (VERSION, MODEL, "Unit 19", zenodo_doi):
        if phrase not in body:
            fail(f"public release notes omit {phrase!r}")
    asset_map = {str(asset.get("name")): asset for asset in assets if isinstance(asset, dict)}
    if set(asset_map) != set(expected) or len(asset_map) != len(expected):
        fail("public release asset inventory differs from the exact seven-file stage")
    if [asset.get("name") for asset in assets] != EXPECTED_ORDER:
        fail("public GitHub asset order is not the exact reader-first order")

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
        fail("Unit 19 is not the repository's latest release")
    raw_readme = stream_identity(
        f"https://raw.githubusercontent.com/{OWNER}/{REPOSITORY}/{commit_sha}/README.md",
        "public README at Unit 19 commit",
    )
    local_readme = root / "README.md"
    local_readme_identity = {
        "bytes": local_readme.stat().st_size,
        "sha256": hashlib.sha256(local_readme.read_bytes()).hexdigest(),
        "md5": hashlib.md5(local_readme.read_bytes()).hexdigest(),
    }
    local_readme_text = local_readme.read_text(encoding="utf-8")
    if (
        raw_readme != local_readme_identity
        or zenodo_doi not in local_readme_text
        or TTP_RE.search(local_readme_text)
        or local_profile_name_present(local_readme_text)
    ):
        fail("public Unit 19 README differs or omits the current Zenodo DOI")

    receipt = {
        "schema_version": 1,
        "workflow": "o011-independent-github-unit19-public-readback-v1",
        "status": "pass",
        "verified_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "authentication_used": False,
        "repository": f"https://github.com/{OWNER}/{REPOSITORY}",
        "commit": commit_sha,
        "annotated_tag": TAG,
        "predecessor_commit": UNIT16_COMMIT,
        "predecessor_tag": UNIT16_TAG,
        "unit16_to_unit19_ahead_by": ahead_by,
        "unit16_predecessor_readback_sha256": UNIT16_READBACK_SHA256,
        "release_id": release.get("id"),
        "release_url": release.get("html_url"),
        "release_latest": True,
        "release_draft": False,
        "release_prerelease": False,
        "version": VERSION,
        "zenodo_doi": zenodo_doi,
        "zenodo_version": zenodo,
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
