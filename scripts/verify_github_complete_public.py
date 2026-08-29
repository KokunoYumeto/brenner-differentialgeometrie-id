#!/usr/bin/env python3
"""Anonymously verify the complete-edition GitHub tag, release, and bytes."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html
import json
import os
import ssl
import subprocess
import urllib.parse
import urllib.request
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


def public_web_get(url: str, label: str) -> tuple[str, bytes]:
    if not url.startswith(f"{REPOSITORY_URL}/") or "access_token=" in url.lower():
        fail(f"unsafe public GitHub web URL for {label}")
    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler({}),
        urllib.request.HTTPSHandler(context=ssl.create_default_context()),
    )
    request = urllib.request.Request(
        url,
        headers={"Accept": "text/html", "User-Agent": "O011-complete-github-web-readback/1.0"},
        method="GET",
    )
    try:
        with opener.open(request, timeout=180) as response:
            if response.status != 200:
                fail(f"public GitHub web read returned HTTP {response.status} for {label}")
            return response.geturl(), response.read()
    except (urllib.error.URLError, TimeoutError, OSError):
        fail(f"public GitHub web read failed for {label}")


def anonymous_tag_refs(expected_commit: str, publication: dict[str, Any]) -> dict[str, str]:
    environment = os.environ.copy()
    environment["GIT_TERMINAL_PROMPT"] = "0"
    command = [
        "git",
        "-c",
        "credential.helper=",
        "ls-remote",
        "--tags",
        f"{REPOSITORY_URL}.git",
        f"refs/tags/{TAG}",
        f"refs/tags/{TAG}^{{}}",
    ]
    try:
        completed = subprocess.run(
            command,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=180,
            check=False,
            shell=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        fail("anonymous Git tag read failed")
    if completed.returncode != 0:
        fail("anonymous Git tag read returned a nonzero status")
    refs: dict[str, str] = {}
    for line in completed.stdout.splitlines():
        fields = line.split("\t", 1)
        if len(fields) == 2:
            refs[fields[1]] = fields[0].lower()
    expected_refs = {
        f"refs/tags/{TAG}": str(publication.get("tag_object_sha", "")).lower(),
        f"refs/tags/{TAG}^{{}}": expected_commit,
    }
    if refs != expected_refs:
        fail("anonymous Git tag and dereferenced commit differ from the publication proof")
    return refs


def direct_web_release(
    expected_commit: str,
    plan: ReleasePlan,
    publication: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    refs = anonymous_tag_refs(expected_commit, publication)
    release_url = f"{REPOSITORY_URL}/releases/tag/{TAG}"
    resolved_release_url, release_bytes = public_web_get(release_url, "release page")
    release_text = html.unescape(release_bytes.decode("utf-8", errors="replace"))
    if resolved_release_url != release_url or RELEASE_TITLE not in release_text or TAG not in release_text:
        fail("public GitHub release page title or tag differs")

    expanded_url = f"{REPOSITORY_URL}/releases/expanded_assets/{TAG}"
    resolved_expanded_url, expanded_bytes = public_web_get(expanded_url, "expanded asset inventory")
    expanded_text = html.unescape(expanded_bytes.decode("utf-8", errors="replace"))
    if resolved_expanded_url != expanded_url:
        fail("public GitHub expanded-asset URL redirected unexpectedly")
    for name in EXPECTED_ORDER:
        download_path = (
            f"/{OWNER}/{REPOSITORY}/releases/download/{urllib.parse.quote(TAG, safe='')}/"
            f"{urllib.parse.quote(name, safe='')}"
        )
        if expanded_text.count(download_path) != 1 or expanded_text.count(name) < 1:
            fail(f"public GitHub expanded inventory differs for {name}")

    latest_url = f"{REPOSITORY_URL}/releases/latest"
    resolved_latest_url, _ = public_web_get(latest_url, "latest release redirect")
    if resolved_latest_url != release_url:
        fail(f"{TAG} is not the latest public GitHub release")

    publication_assets = publication.get("assets")
    if not isinstance(publication_assets, list):
        fail("publication receipt lacks the exact asset proof")
    by_name = {
        str(item.get("name")): item
        for item in publication_assets
        if isinstance(item, dict) and isinstance(item.get("name"), str)
    }
    if set(by_name) != set(EXPECTED_ORDER):
        fail("publication receipt asset set differs before direct readback")
    verified: list[dict[str, Any]] = []
    for name in EXPECTED_ORDER:
        wanted = plan.expected[name]
        actual = stream_identity(
            f"{REPOSITORY_URL}/releases/download/{urllib.parse.quote(TAG, safe='')}/{urllib.parse.quote(name, safe='')}",
            name,
            int(wanted["bytes"]),
        )
        if actual != {"bytes": wanted["bytes"], "sha256": wanted["sha256"]}:
            fail(f"anonymous direct GitHub bytes differ for {name}")
        item = by_name[name]
        verified.append(
            {
                "name": name,
                "asset_id": item.get("asset_id"),
                "bytes": actual["bytes"],
                "sha256": actual["sha256"],
                "github_digest": item.get("github_digest"),
                "download_url": f"{REPOSITORY_URL}/releases/download/{TAG}/{name}",
                "matches_local_release_contract": True,
            }
        )
    return {
        "tag_object_sha": refs[f"refs/tags/{TAG}"],
        "tag_commit": refs[f"refs/tags/{TAG}^{{}}"],
        "release_url": release_url,
        "release_id": publication.get("release_id"),
        "release_page_bytes": len(release_bytes),
        "expanded_asset_page_bytes": len(expanded_bytes),
        "latest_release_redirect_verified": True,
    }, verified


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
        fail("public v1.0.1 tag is not the exact annotated expected-commit tag")

    encoded_base = urllib.parse.quote(predecessor_commit, safe="")
    _, raw_comparison = client.request_json(
        "GET",
        api_path(f"/compare/{encoded_base}...{expected_commit}"),
        (200,),
        "anonymous release ancestry check",
    )
    comparison = require_object(raw_comparison, "anonymous release ancestry check")
    base_commit = comparison.get("base_commit")
    merge_base_commit = comparison.get("merge_base_commit")
    commits = comparison.get("commits")
    last_compared_commit = commits[-1] if isinstance(commits, list) and commits else None
    if (
        comparison.get("status") != "ahead"
        or comparison.get("behind_by") != 0
        or not isinstance(comparison.get("ahead_by"), int)
        or comparison.get("ahead_by") < 1
        or not isinstance(base_commit, dict)
        or str(base_commit.get("sha", "")).lower() != predecessor_commit
        or not isinstance(commits, list)
        or len(commits) != comparison.get("ahead_by")
        or not isinstance(last_compared_commit, dict)
        or str(last_compared_commit.get("sha", "")).lower() != expected_commit
        or not isinstance(merge_base_commit, dict)
        or str(merge_base_commit.get("sha", "")).lower() != predecessor_commit
    ):
        fail("public v1.0.1 commit is not strictly ahead of the predecessor tag")
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
) -> tuple[dict[str, Any], list[dict[str, Any]], list[str]]:
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
    observed_order = [str(item.get("name")) for item in assets if isinstance(item, dict)]
    by_name = {
        str(item.get("name")): item
        for item in assets
        if isinstance(item, dict) and isinstance(item.get("name"), str)
    }
    if len(by_name) != 7 or set(by_name) != set(EXPECTED_ORDER):
        fail("anonymous GitHub release asset names differ from the public manifest")

    verified: list[dict[str, Any]] = []
    for name in EXPECTED_ORDER:
        item = by_name[name]
        wanted = plan.expected.get(name)
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
        actual = stream_identity(url, name, int(wanted["bytes"]))
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
        fail("v1.0.1 is not the latest GitHub release")
    return release, verified, observed_order


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

    if args.direct_web:
        web, files = direct_web_release(expected_commit, plan, publication)
        repository = {
            "tag_object_sha": web["tag_object_sha"],
            "predecessor_commit": publication["predecessor_commit"],
            "default_branch": publication["remote_default_branch"],
        }
        release = {"id": web["release_id"], "html_url": web["release_url"]}
        observed_order = EXPECTED_ORDER.copy()
        verification_route = "credential_free_git_refs_public_web_pages_and_direct_asset_downloads"
        route_proof: dict[str, Any] = web
    else:
        client = GitHubClient(token=None, user_agent="O011-complete-github-public-readback/1.0")
        repository = public_repository_state(
            client,
            expected_commit,
            str(publication["predecessor_commit"]),
            str(publication["tag_object_sha"]),
        )
        if repository["default_branch"] != publication["remote_default_branch"]:
            fail("public default branch differs from the publication proof")
        release, files, observed_order = public_release(client, expected_commit, plan, publication)
        verification_route = "credential_free_github_rest_api_and_direct_asset_downloads"
        route_proof = {"anonymous_rest_api_used": True}

    receipt = {
        "schema_version": 1,
        "workflow": "o011-independent-github-complete-public-readback-v1",
        "status": "pass",
        "verified_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "authentication_used": False,
        "verification_route": verification_route,
        "anonymous_rest_api_used": not args.direct_web,
        "route_proof": route_proof,
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
        "public_api_asset_order": observed_order,
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
    parser.add_argument(
        "--direct-web",
        action="store_true",
        help="avoid the shared anonymous REST quota; verify public Git refs, web pages, and direct bytes",
    )
    args = parser.parse_args()
    try:
        return run(args)
    except ReleaseError as exc:
        raise SystemExit(f"error: {exc}") from None


if __name__ == "__main__":
    raise SystemExit(main())
