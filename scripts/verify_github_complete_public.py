#!/usr/bin/env python3
"""Anonymously verify the complete-edition GitHub tag, release, and bytes."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import urllib.parse
from pathlib import Path
from typing import Any

from github_complete_common import (
    COMMIT_RE,
    DEFAULT_METADATA,
    DEFAULT_PUBLICATION_RECEIPT,
    DEFAULT_READBACK_RECEIPT,
    EXPECTED_ORDER,
    OWNER,
    PREDECESSOR_TAG,
    RELEASE_TITLE,
    RELEASE_VERSION,
    REPOSITORY,
    REPOSITORY_URL,
    TAG,
    GitHubClient,
    ReleaseError,
    ReleasePlan,
    api_path,
    digest,
    fail,
    inside,
    load_object,
    load_release_plan,
    require_object,
    resolve_tag,
    sanitized,
    stream_identity,
    write_once,
)


def publication_receipt_ok(
    path: Path,
    expected_commit: str,
    plan: ReleasePlan,
) -> dict[str, Any]:
    receipt = load_object(path, "GitHub publication receipt")
    assets = receipt.get("assets")
    expected_local_preflight = {
        "head_matches_expected_commit": True,
        "working_tree_clean": True,
        "release_controls_tracked": True,
        "origin_matches_repository": True,
        "new_local_tag_was_absent": True,
    }
    expected_remote_preflight = {
        "default_branch_matches_expected_commit": True,
        "new_tag_was_absent": True,
        "new_release_was_absent": True,
        "duplicate_tag_or_title_was_absent": True,
    }
    if (
        receipt.get("schema_version") != 1
        or receipt.get("workflow") != "o011-publish-github-complete-v1"
        or receipt.get("status") != "pass"
        or receipt.get("authentication_used_for_publication") is not True
        or receipt.get("runtime_secret_recorded") is not False
        or receipt.get("remote_state_mutated") is not True
        or receipt.get("repository") != REPOSITORY_URL
        or receipt.get("tag") != TAG
        or receipt.get("tag_kind") != "annotated"
        or receipt.get("release_title") != RELEASE_TITLE
        or receipt.get("version") != RELEASE_VERSION
        or receipt.get("draft") is not False
        or receipt.get("prerelease") is not False
        or receipt.get("latest_requested") is not True
        or receipt.get("commit") != expected_commit
        or receipt.get("tag_commit") != expected_commit
        or receipt.get("predecessor_tag") != PREDECESSOR_TAG
        or receipt.get("strict_descendant_of_predecessor") is not True
        or not isinstance(receipt.get("remote_default_branch"), str)
        or not receipt.get("remote_default_branch")
        or receipt.get("local_preflight") != expected_local_preflight
        or receipt.get("remote_preflight") != expected_remote_preflight
        or receipt.get("public_file_order") != EXPECTED_ORDER
        or receipt.get("file_count") != 7
        or receipt.get("total_bytes") != sum(item["bytes"] for item in plan.assets)
        or receipt.get("release_metadata_sha256") != digest(plan.metadata_path)
        or receipt.get("release_notes_sha256")
        != hashlib.sha256(plan.release_notes.encode("utf-8")).hexdigest()
        or receipt.get("anonymous_public_readback_pending") is not True
        or not isinstance(receipt.get("release_id"), int)
        or receipt.get("release_url") != f"{REPOSITORY_URL}/releases/tag/{TAG}"
        or not isinstance(receipt.get("tag_object_sha"), str)
        or COMMIT_RE.fullmatch(receipt.get("tag_object_sha")) is None
        or not isinstance(receipt.get("predecessor_commit"), str)
        or COMMIT_RE.fullmatch(receipt.get("predecessor_commit")) is None
        or not isinstance(assets, list)
        or len(assets) != 7
        or not sanitized(receipt)
    ):
        fail("GitHub publication receipt is not the exact sanitized passing proof")
    for index, item in enumerate(assets):
        if not isinstance(item, dict):
            fail("GitHub publication receipt contains a non-object asset")
        name = EXPECTED_ORDER[index]
        wanted = plan.expected[name]
        if (
            item.get("name") != name
            or item.get("bytes") != wanted["bytes"]
            or item.get("sha256") != wanted["sha256"]
            or item.get("state") != "uploaded"
            or not isinstance(item.get("asset_id"), int)
        ):
            fail(f"GitHub publication receipt asset identity differs for {name}")
        api_digest = item.get("github_digest")
        if api_digest is not None and api_digest != f"sha256:{wanted['sha256']}":
            fail(f"GitHub publication receipt digest differs for {name}")
    return receipt


def public_repository_state(
    client: GitHubClient,
    expected_commit: str,
    expected_predecessor: str,
    expected_tag_object: str,
) -> dict[str, Any]:
    _, raw_repository = client.request_json(
        "GET", api_path(), (200,), "anonymous repository identity check"
    )
    repository = require_object(raw_repository, "anonymous repository identity check")
    default_branch = repository.get("default_branch")
    if (
        repository.get("full_name") != f"{OWNER}/{REPOSITORY}"
        or repository.get("private") is not False
        or not isinstance(default_branch, str)
        or not default_branch
    ):
        fail("anonymous repository identity or public state differs")

    encoded_branch = urllib.parse.quote(default_branch, safe="")
    _, raw_branch = client.request_json(
        "GET", api_path(f"/branches/{encoded_branch}"), (200,), "anonymous default-branch check"
    )
    branch = require_object(raw_branch, "anonymous default-branch check")
    branch_commit = branch.get("commit")
    if not isinstance(branch_commit, dict) or str(branch_commit.get("sha", "")).lower() != expected_commit:
        fail("anonymous default branch is not the exact released commit")

    _, raw_commit = client.request_json(
        "GET", api_path(f"/commits/{expected_commit}"), (200,), "anonymous release-commit check"
    )
    commit = require_object(raw_commit, "anonymous release-commit check")
    if str(commit.get("sha", "")).lower() != expected_commit:
        fail("anonymous release commit identity differs")

    predecessor_commit, _, _ = resolve_tag(client, PREDECESSOR_TAG)
    if predecessor_commit != expected_predecessor:
        fail("public predecessor tag differs from the publication proof")
    release_commit, annotated, tag_object_sha = resolve_tag(client, TAG)
    if (
        release_commit != expected_commit
        or not annotated
        or tag_object_sha != expected_tag_object
    ):
        fail("public v1.0.0 tag is not the exact annotated expected-commit tag")

    encoded_base = urllib.parse.quote(predecessor_commit, safe="")
    _, raw_comparison = client.request_json(
        "GET",
        api_path(f"/compare/{encoded_base}...{expected_commit}"),
        (200,),
        "anonymous release ancestry check",
    )
    comparison = require_object(raw_comparison, "anonymous release ancestry check")
    base_commit = comparison.get("base_commit")
    head_commit = comparison.get("head_commit")
    merge_base_commit = comparison.get("merge_base_commit")
    if (
        comparison.get("status") != "ahead"
        or comparison.get("behind_by") != 0
        or not isinstance(comparison.get("ahead_by"), int)
        or comparison.get("ahead_by") < 1
        or not isinstance(base_commit, dict)
        or str(base_commit.get("sha", "")).lower() != predecessor_commit
        or not isinstance(head_commit, dict)
        or str(head_commit.get("sha", "")).lower() != expected_commit
        or not isinstance(merge_base_commit, dict)
        or str(merge_base_commit.get("sha", "")).lower() != predecessor_commit
    ):
        fail("public v1.0.0 commit is not strictly ahead of the Unit 22 tag")
    return {
        "default_branch": default_branch,
        "predecessor_commit": predecessor_commit,
        "release_commit": release_commit,
        "tag_object_sha": tag_object_sha,
        "annotated_tag": True,
        "strict_descendant": True,
    }


def public_release(
    client: GitHubClient,
    expected_commit: str,
    plan: ReleasePlan,
    publication: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    encoded_tag = urllib.parse.quote(TAG, safe="")
    _, raw_release = client.request_json(
        "GET", api_path(f"/releases/tags/{encoded_tag}"), (200,), "anonymous release lookup"
    )
    release = require_object(raw_release, "anonymous release lookup")
    assets = release.get("assets")
    expected_url = f"{REPOSITORY_URL}/releases/tag/{TAG}"
    if (
        release.get("id") != publication.get("release_id")
        or release.get("tag_name") != TAG
        or release.get("target_commitish") != expected_commit
        or release.get("name") != RELEASE_TITLE
        or release.get("html_url") != expected_url
        or release.get("body") != plan.release_notes
        or release.get("draft") is not False
        or release.get("prerelease") is not False
        or not isinstance(assets, list)
        or len(assets) != 7
    ):
        fail("anonymous GitHub release metadata differs")
    if [item.get("name") for item in assets if isinstance(item, dict)] != EXPECTED_ORDER:
        fail("anonymous GitHub release asset order differs from the public manifest")

    verified: list[dict[str, Any]] = []
    for item in assets:
        if not isinstance(item, dict):
            fail("anonymous GitHub release inventory contains a non-object")
        name = item.get("name")
        wanted = plan.expected.get(str(name))
        url = item.get("browser_download_url")
        api_digest = item.get("digest")
        if (
            wanted is None
            or item.get("state") != "uploaded"
            or item.get("size") != wanted["bytes"]
            or not isinstance(item.get("id"), int)
            or not isinstance(url, str)
            or (api_digest is not None and api_digest != f"sha256:{wanted['sha256']}")
        ):
            fail(f"anonymous GitHub inventory differs for {name}")
        actual = stream_identity(url, str(name), int(wanted["bytes"]))
        if actual != {"bytes": wanted["bytes"], "sha256": wanted["sha256"]}:
            fail(f"anonymous public bytes differ for {name}")
        verified.append(
            {
                "name": name,
                "asset_id": item["id"],
                "bytes": actual["bytes"],
                "sha256": actual["sha256"],
                "github_digest": api_digest,
                "download_url": url,
                "matches_local_release_contract": True,
            }
        )

    _, raw_latest = client.request_json(
        "GET", api_path("/releases/latest"), (200,), "latest-release check"
    )
    latest = require_object(raw_latest, "latest-release check")
    if latest.get("id") != release.get("id") or latest.get("tag_name") != TAG:
        fail("v1.0.0 is not the latest GitHub release")
    return release, verified


def run(args: argparse.Namespace) -> int:
    root = args.root.resolve()
    if not root.is_dir():
        fail("--root must be an existing directory")
    expected_commit = args.expected_commit.lower()
    if COMMIT_RE.fullmatch(expected_commit) is None:
        fail("--expected-commit must be exactly 40 lowercase hexadecimal characters")
    metadata_path = inside(root, root / args.metadata, "GitHub release metadata")
    receipt_path = inside(root, root / args.receipt, "GitHub public-readback receipt")
    expected_receipt_path = inside(
        root, root / DEFAULT_READBACK_RECEIPT, "default GitHub public-readback receipt"
    )
    if receipt_path != expected_receipt_path:
        fail("public-readback receipt must use the sanitized qa/complete path")
    if receipt_path.exists():
        fail("refusing to overwrite the GitHub public-readback receipt")

    plan = load_release_plan(root, metadata_path)
    publication_path = inside(
        root, root / DEFAULT_PUBLICATION_RECEIPT, "GitHub publication receipt"
    )
    publication = publication_receipt_ok(publication_path, expected_commit, plan)

    client = GitHubClient(token=None, user_agent="O011-complete-github-public-readback/1.0")
    repository = public_repository_state(
        client,
        expected_commit,
        str(publication["predecessor_commit"]),
        str(publication["tag_object_sha"]),
    )
    if repository["default_branch"] != publication["remote_default_branch"]:
        fail("public default branch differs from the publication proof")
    release, files = public_release(client, expected_commit, plan, publication)

    receipt = {
        "schema_version": 1,
        "workflow": "o011-independent-github-complete-public-readback-v1",
        "status": "pass",
        "verified_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "authentication_used": False,
        "repository": REPOSITORY_URL,
        "repository_public": True,
        "tag": TAG,
        "tag_kind": "annotated",
        "tag_object_sha": repository["tag_object_sha"],
        "release_title": RELEASE_TITLE,
        "version": RELEASE_VERSION,
        "commit": expected_commit,
        "remote_default_branch": repository["default_branch"],
        "predecessor_tag": PREDECESSOR_TAG,
        "predecessor_commit": repository["predecessor_commit"],
        "strict_descendant_of_predecessor": True,
        "release_id": release["id"],
        "release_url": release["html_url"],
        "release_latest": True,
        "release_draft": False,
        "release_prerelease": False,
        "expected_public_file_order": EXPECTED_ORDER,
        "public_api_asset_order": [item["name"] for item in files],
        "public_files": files,
        "file_count": 7,
        "total_bytes": sum(item["bytes"] for item in files),
        "all_anonymous_downloaded_bytes_sha256_match": True,
        "release_metadata_sha256": digest(plan.metadata_path),
        "publication_receipt_sha256": digest(publication_path),
    }
    if not sanitized(receipt):
        fail("GitHub public-readback receipt failed final sanitization")
    write_once(receipt_path, receipt, "GitHub public-readback receipt")
    print(
        json.dumps(
            {
                "status": "pass",
                "repository": f"{OWNER}/{REPOSITORY}",
                "tag": TAG,
                "release_id": release["id"],
                "files": 7,
                "bytes": receipt["total_bytes"],
            },
            sort_keys=True,
        )
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--expected-commit", required=True)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--receipt", type=Path, default=DEFAULT_READBACK_RECEIPT)
    args = parser.parse_args()
    try:
        return run(args)
    except ReleaseError as exc:
        raise SystemExit(f"error: {exc}") from None


if __name__ == "__main__":
    raise SystemExit(main())
