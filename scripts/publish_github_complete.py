#!/usr/bin/env python3
"""Publish the exact complete-edition seven-asset GitHub release.

The transaction is fail-closed.  It proves a clean exact local commit, the
existing checkpoint ancestry, the remote default-branch commit, absence of the
new tag/release and duplicate title, and all local bytes before reading a
credential.  It uploads assets to a draft in manifest order and makes the
release public only after the authenticated inventory is exact.  Anonymous
public-byte verification is intentionally performed by the companion verifier.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import http.client
import json
import os
import re
import ssl
import subprocess
import urllib.parse
from pathlib import Path
from typing import Any

from github_complete_common import (
    COMMIT_RE,
    DEFAULT_METADATA,
    DEFAULT_PUBLICATION_RECEIPT,
    EXPECTED_ORDER,
    OWNER,
    PREDECESSOR_TAG,
    RELEASE_TITLE,
    RELEASE_VERSION,
    REPOSITORY,
    REPOSITORY_URL,
    TAG,
    WORKFLOW,
    GitHubClient,
    ReleaseError,
    ReleasePlan,
    api_path,
    digest,
    fail,
    inside,
    load_release_plan,
    require_object,
    resolve_tag,
    sanitized,
    write_once,
)


TOKEN_RE = re.compile(
    r"(?<![A-Za-z0-9_])(?:github_pat_[A-Za-z0-9_]{20,}|gh[pousr]_[A-Za-z0-9]{20,})(?![A-Za-z0-9_])"
)
TRACKED_RELEASE_CONTROLS = [
    "scripts/github_complete_common.py",
    "scripts/publish_github_complete.py",
    "scripts/verify_github_complete_public.py",
    "qa/complete/GITHUB_RELEASE_METADATA.json",
]


def git_command(
    root: Path,
    arguments: list[str],
    label: str,
    allowed_statuses: tuple[int, ...] = (0,),
) -> tuple[int, str]:
    environment = os.environ.copy()
    environment["GIT_OPTIONAL_LOCKS"] = "0"
    try:
        completed = subprocess.run(
            ["git", *arguments],
            cwd=root,
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
        fail(f"{label} failed")
    if completed.returncode not in allowed_statuses:
        fail(f"{label} failed with Git exit status {completed.returncode}")
    return completed.returncode, completed.stdout.strip()


def valid_origin(value: str) -> bool:
    candidates = {
        f"https://github.com/{OWNER}/{REPOSITORY}",
        f"https://github.com/{OWNER}/{REPOSITORY}.git",
        f"git@github.com:{OWNER}/{REPOSITORY}.git",
        f"git@github.com:{OWNER}/{REPOSITORY}",
        f"ssh://git@github.com/{OWNER}/{REPOSITORY}.git",
        f"ssh://git@github.com/{OWNER}/{REPOSITORY}",
    }
    return value.rstrip("/") in candidates


def local_git_preflight(root: Path, expected_commit: str) -> dict[str, Any]:
    _, top = git_command(root, ["rev-parse", "--show-toplevel"], "repository-root check")
    try:
        top_path = Path(top).resolve()
    except OSError:
        fail("Git returned an invalid repository root")
    if top_path != root:
        fail("--root is not the exact Git repository root")

    _, head = git_command(root, ["rev-parse", "--verify", "HEAD"], "HEAD identity check")
    if head.lower() != expected_commit:
        fail("HEAD is not the caller-supplied expected commit")

    _, status = git_command(
        root,
        ["status", "--porcelain=v1", "--untracked-files=all", "--ignore-submodules=none"],
        "clean-worktree check",
    )
    if status:
        fail("working tree or index is not clean; refusing publication")

    code, _ = git_command(
        root,
        ["show-ref", "--verify", "--quiet", f"refs/tags/{TAG}"],
        "new local tag absence check",
        (0, 1),
    )
    if code == 0:
        fail(f"local tag {TAG} already exists; refusing overwrite or duplicate publication")

    _, predecessor_commit = git_command(
        root,
        ["rev-parse", "--verify", f"{PREDECESSOR_TAG}^{{commit}}"],
        "local predecessor-tag resolution",
    )
    predecessor_commit = predecessor_commit.lower()
    if COMMIT_RE.fullmatch(predecessor_commit) is None or predecessor_commit == expected_commit:
        fail("local predecessor tag has an invalid or non-predecessor commit")
    code, _ = git_command(
        root,
        ["merge-base", "--is-ancestor", predecessor_commit, expected_commit],
        "local predecessor ancestry check",
        (0, 1),
    )
    if code != 0:
        fail("expected commit is not a descendant of the local Unit 22 tag")

    _, origin = git_command(root, ["remote", "get-url", "origin"], "origin identity check")
    if not valid_origin(origin):
        fail("origin does not identify the authorized existing GitHub repository")

    git_command(
        root,
        ["ls-files", "--error-unmatch", "--", *TRACKED_RELEASE_CONTROLS],
        "tracked release-control check",
    )
    return {
        "head": expected_commit,
        "predecessor_commit": predecessor_commit,
        "origin": REPOSITORY_URL,
        "working_tree_clean": True,
        "release_controls_tracked": True,
        "new_local_tag_absent": True,
    }


def absent_new_remote_state(client: GitHubClient) -> None:
    encoded_tag = urllib.parse.quote(TAG, safe="")
    tag_status, _ = client.request_json(
        "GET",
        api_path(f"/git/ref/tags/{encoded_tag}"),
        (200, 404),
        "new remote tag absence check",
    )
    if tag_status != 404:
        fail(f"remote tag {TAG} already exists; refusing overwrite or duplicate publication")
    release_status, _ = client.request_json(
        "GET",
        api_path(f"/releases/tags/{encoded_tag}"),
        (200, 404),
        "new remote release absence check",
    )
    if release_status != 404:
        fail(f"release {TAG} already exists; refusing overwrite or duplicate publication")


def remote_commit_preflight(client: GitHubClient, expected_commit: str) -> dict[str, Any]:
    _, raw_repository = client.request_json(
        "GET", api_path(), (200,), "public repository identity check"
    )
    repository = require_object(raw_repository, "public repository identity check")
    default_branch = repository.get("default_branch")
    if (
        repository.get("full_name") != f"{OWNER}/{REPOSITORY}"
        or repository.get("private") is not False
        or not isinstance(default_branch, str)
        or not default_branch
    ):
        fail("public repository identity or access state differs")

    encoded_branch = urllib.parse.quote(default_branch, safe="")
    _, raw_branch = client.request_json(
        "GET", api_path(f"/branches/{encoded_branch}"), (200,), "default-branch identity check"
    )
    branch = require_object(raw_branch, "default-branch identity check")
    branch_commit = branch.get("commit")
    if not isinstance(branch_commit, dict) or str(branch_commit.get("sha", "")).lower() != expected_commit:
        fail("remote default branch is not the exact expected commit")

    _, raw_commit = client.request_json(
        "GET", api_path(f"/commits/{expected_commit}"), (200,), "expected remote commit check"
    )
    commit = require_object(raw_commit, "expected remote commit check")
    if str(commit.get("sha", "")).lower() != expected_commit:
        fail("remote expected commit identity differs")

    predecessor_commit, _, _ = resolve_tag(client, PREDECESSOR_TAG)
    encoded_base = urllib.parse.quote(predecessor_commit, safe="")
    _, raw_comparison = client.request_json(
        "GET",
        api_path(f"/compare/{encoded_base}...{expected_commit}"),
        (200,),
        "remote predecessor ancestry check",
    )
    comparison = require_object(raw_comparison, "remote predecessor ancestry check")
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
        fail("remote expected commit is not strictly ahead of the Unit 22 tag")

    absent_new_remote_state(client)
    return {
        "default_branch": default_branch,
        "expected_commit": expected_commit,
        "predecessor_commit": predecessor_commit,
        "predecessor_tag": PREDECESSOR_TAG,
        "strict_descendant": True,
        "new_tag_absent": True,
        "new_release_absent": True,
    }


def read_token(path: Path) -> str:
    if not path.is_file():
        fail("GitHub token file is missing")
    try:
        raw = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError):
        fail("unable to read the GitHub token file")
    candidates = list(dict.fromkeys(match.group(0) for match in TOKEN_RE.finditer(raw)))
    fine_grained = [token for token in candidates if token.startswith("github_pat_")]
    if len(fine_grained) == 1:
        return fine_grained[0]
    if len(candidates) == 1:
        return candidates[0]
    fail("GitHub token file does not contain one unambiguous usable GitHub credential")


def authenticated_preflight(client: GitHubClient, expected_commit: str) -> dict[str, Any]:
    _, raw_user = client.request_json("GET", "/user", (200,), "authenticated GitHub identity check")
    user = require_object(raw_user, "authenticated GitHub identity check")
    if not isinstance(user.get("id"), int) or user.get("id") <= 0:
        fail("authenticated GitHub identity is malformed")

    _, raw_repository = client.request_json(
        "GET", api_path(), (200,), "authenticated repository permission check"
    )
    repository = require_object(raw_repository, "authenticated repository permission check")
    permissions = repository.get("permissions")
    if (
        repository.get("full_name") != f"{OWNER}/{REPOSITORY}"
        or not isinstance(permissions, dict)
        or permissions.get("push") is not True
    ):
        fail("credential does not prove push permission to the authorized repository")

    remote = remote_commit_preflight(client, expected_commit)
    for page in range(1, 11):
        _, raw_releases = client.request_json(
            "GET",
            api_path(f"/releases?per_page=100&page={page}"),
            (200,),
            "authenticated release duplicate scan",
        )
        if not isinstance(raw_releases, list):
            fail("authenticated release duplicate scan returned a non-list")
        for release in raw_releases:
            if not isinstance(release, dict):
                fail("authenticated release duplicate scan contains a non-object")
            if release.get("tag_name") == TAG or release.get("name") == RELEASE_TITLE:
                fail("matching release tag or title already exists; refusing duplicate publication")
        if len(raw_releases) < 100:
            return remote
    fail("release history exceeds the bounded duplicate scan")


def content_type(name: str) -> str:
    suffix = Path(name).suffix.lower()
    return {
        ".pdf": "application/pdf",
        ".zip": "application/zip",
        ".md": "text/markdown; charset=utf-8",
        ".json": "application/json",
        ".txt": "text/plain; charset=utf-8",
    }.get(suffix, "application/octet-stream")


def upload_asset(
    token: str,
    release_id: int,
    path: Path,
    expected: dict[str, Any],
) -> dict[str, Any]:
    name = str(expected["name"])
    expected_bytes = int(expected["bytes"])
    expected_sha256 = str(expected["sha256"])
    try:
        if path.stat().st_size != expected_bytes:
            fail(f"local asset length changed before upload for {name}")
    except OSError:
        fail(f"unable to inspect local asset before upload for {name}")
    request_path = (
        f"/repos/{urllib.parse.quote(OWNER, safe='')}/{urllib.parse.quote(REPOSITORY, safe='')}"
        f"/releases/{release_id}/assets?name={urllib.parse.quote(name, safe='')}"
    )
    connection = http.client.HTTPSConnection(
        "uploads.github.com", timeout=300, context=ssl.create_default_context()
    )
    try:
        connection.putrequest("POST", request_path)
        connection.putheader("Accept", "application/vnd.github+json")
        connection.putheader("Authorization", f"Bearer {token}")
        connection.putheader("Content-Type", content_type(name))
        connection.putheader("Content-Length", str(expected_bytes))
        connection.putheader("User-Agent", "O011-complete-github-publisher/1.0")
        connection.putheader("X-GitHub-Api-Version", "2022-11-28")
        connection.endheaders()
        streamed_sha256 = hashlib.sha256()
        streamed_bytes = 0
        with path.open("rb") as stream:
            while streamed_bytes < expected_bytes:
                block = stream.read(min(1024 * 1024, expected_bytes - streamed_bytes))
                if not block:
                    fail(f"local asset ended during upload for {name}")
                connection.send(block)
                streamed_bytes += len(block)
                streamed_sha256.update(block)
            if stream.read(1):
                fail(f"local asset grew during upload for {name}")
        if streamed_sha256.hexdigest() != expected_sha256:
            fail(f"local asset bytes changed during upload for {name}")
        response = connection.getresponse()
        raw = response.read()
        status = response.status
    except (OSError, TimeoutError, http.client.HTTPException):
        fail(f"asset upload failed for {name}")
    finally:
        connection.close()
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError):
        value = None
    if status != 201 or not isinstance(value, dict):
        fail(f"asset upload returned HTTP {status} for {name}")
    api_digest = value.get("digest")
    if (
        value.get("name") != name
        or value.get("state") != "uploaded"
        or value.get("size") != expected["bytes"]
        or not isinstance(value.get("id"), int)
        or (api_digest is not None and api_digest != f"sha256:{expected['sha256']}")
    ):
        fail(f"uploaded asset identity differs for {name}")
    return {
        "name": name,
        "asset_id": value["id"],
        "bytes": expected["bytes"],
        "sha256": expected["sha256"],
        "github_digest": api_digest,
        "state": "uploaded",
    }


def release_asset_inventory(release: dict[str, Any], plan: ReleasePlan) -> list[dict[str, Any]]:
    raw_assets = release.get("assets")
    if not isinstance(raw_assets, list) or len(raw_assets) != 7:
        fail("authenticated draft does not have exactly seven assets")
    by_name = {
        str(item.get("name")): item
        for item in raw_assets
        if isinstance(item, dict) and isinstance(item.get("name"), str)
    }
    if len(by_name) != 7 or set(by_name) != set(EXPECTED_ORDER):
        fail("authenticated draft asset names differ from the public manifest")
    result: list[dict[str, Any]] = []
    # GitHub returns release assets in its own stable name order, not upload
    # order.  Normalize to the manifest order before comparing identities.
    for name in EXPECTED_ORDER:
        item = by_name[name]
        wanted = plan.expected.get(name)
        api_digest = item.get("digest")
        if (
            wanted is None
            or item.get("state") != "uploaded"
            or item.get("size") != wanted["bytes"]
            or not isinstance(item.get("id"), int)
            or (api_digest is not None and api_digest != f"sha256:{wanted['sha256']}")
        ):
            fail(f"authenticated draft asset identity differs for {name}")
        result.append(
            {
                "name": name,
                "asset_id": item["id"],
                "bytes": wanted["bytes"],
                "sha256": wanted["sha256"],
                "github_digest": api_digest,
                "state": "uploaded",
            }
        )
    return result


def publish(
    client: GitHubClient,
    token: str,
    expected_commit: str,
    plan: ReleasePlan,
) -> dict[str, Any]:
    tag_message = f"{RELEASE_TITLE} ({TAG})"
    _, raw_tag = client.request_json(
        "POST",
        api_path("/git/tags"),
        (201,),
        "annotated-tag creation",
        {
            "tag": TAG,
            "message": tag_message,
            "object": expected_commit,
            "type": "commit",
        },
    )
    tag_object = require_object(raw_tag, "annotated-tag creation")
    tag_sha = str(tag_object.get("sha", "")).lower()
    target = tag_object.get("object")
    if (
        tag_object.get("tag") != TAG
        or COMMIT_RE.fullmatch(tag_sha) is None
        or not isinstance(target, dict)
        or target.get("type") != "commit"
        or str(target.get("sha", "")).lower() != expected_commit
    ):
        fail("created annotated-tag object differs")

    _, raw_ref = client.request_json(
        "POST",
        api_path("/git/refs"),
        (201,),
        "tag-ref creation",
        {"ref": f"refs/tags/{TAG}", "sha": tag_sha},
    )
    ref = require_object(raw_ref, "tag-ref creation")
    ref_object = ref.get("object")
    if (
        ref.get("ref") != f"refs/tags/{TAG}"
        or not isinstance(ref_object, dict)
        or ref_object.get("type") != "tag"
        or str(ref_object.get("sha", "")).lower() != tag_sha
    ):
        fail("created tag ref differs")

    _, raw_release = client.request_json(
        "POST",
        api_path("/releases"),
        (201,),
        "draft-release creation",
        {
            "tag_name": TAG,
            "target_commitish": expected_commit,
            "name": RELEASE_TITLE,
            "body": plan.release_notes,
            "draft": True,
            "prerelease": False,
            "generate_release_notes": False,
            "make_latest": "true",
        },
    )
    release = require_object(raw_release, "draft-release creation")
    release_id = release.get("id")
    if (
        not isinstance(release_id, int)
        or release.get("tag_name") != TAG
        or release.get("target_commitish") != expected_commit
        or release.get("name") != RELEASE_TITLE
        or release.get("draft") is not True
        or release.get("prerelease") is not False
        or release.get("assets") != []
    ):
        fail("new draft-release metadata differs")

    uploaded: list[dict[str, Any]] = []
    for item in plan.assets:
        uploaded.append(upload_asset(token, release_id, plan.release_dir / item["name"], item))

    _, raw_draft = client.request_json(
        "GET", api_path(f"/releases/{release_id}"), (200,), "uploaded draft inventory check"
    )
    draft = require_object(raw_draft, "uploaded draft inventory check")
    inventory = release_asset_inventory(draft, plan)
    if draft.get("draft") is not True or inventory != uploaded:
        fail("uploaded draft state differs before publication")

    _, raw_public = client.request_json(
        "PATCH",
        api_path(f"/releases/{release_id}"),
        (200,),
        "final release publication",
        {
            "tag_name": TAG,
            "target_commitish": expected_commit,
            "name": RELEASE_TITLE,
            "body": plan.release_notes,
            "draft": False,
            "prerelease": False,
            "make_latest": "true",
        },
    )
    public_release = require_object(raw_public, "final release publication")
    if (
        public_release.get("id") != release_id
        or public_release.get("tag_name") != TAG
        or public_release.get("target_commitish") != expected_commit
        or public_release.get("name") != RELEASE_TITLE
        or public_release.get("body") != plan.release_notes
        or public_release.get("draft") is not False
        or public_release.get("prerelease") is not False
        or public_release.get("html_url") != f"{REPOSITORY_URL}/releases/tag/{TAG}"
    ):
        fail("published release metadata differs")
    public_inventory = release_asset_inventory(public_release, plan)
    if public_inventory != inventory:
        fail("published release asset inventory differs from the checked draft")

    resolved_commit, annotated, resolved_tag_object = resolve_tag(client, TAG)
    if resolved_commit != expected_commit or not annotated or resolved_tag_object != tag_sha:
        fail("published tag does not resolve as the expected annotated tag")
    encoded_tag = urllib.parse.quote(TAG, safe="")
    _, raw_by_tag = client.request_json(
        "GET", api_path(f"/releases/tags/{encoded_tag}"), (200,), "published release tag lookup"
    )
    by_tag = require_object(raw_by_tag, "published release tag lookup")
    if by_tag.get("id") != release_id:
        fail("published release tag lookup differs")
    return {
        "release_id": release_id,
        "release_url": public_release["html_url"],
        "tag_object_sha": tag_sha,
        "tag_commit": resolved_commit,
        "assets": public_inventory,
    }


def run(args: argparse.Namespace) -> int:
    root = args.root.resolve()
    if not root.is_dir():
        fail("--root must be an existing directory")
    expected_commit = args.expected_commit.lower()
    if COMMIT_RE.fullmatch(expected_commit) is None:
        fail("--expected-commit must be exactly 40 lowercase hexadecimal characters")
    metadata_path = inside(root, root / args.metadata, "GitHub release metadata")
    receipt_path = inside(root, root / args.receipt, "GitHub publication receipt")
    expected_receipt_path = inside(
        root, root / DEFAULT_PUBLICATION_RECEIPT, "default GitHub publication receipt"
    )
    if receipt_path != expected_receipt_path:
        fail("publication receipt must use the sanitized qa/complete path")
    if receipt_path.exists():
        fail("refusing to overwrite the GitHub publication receipt")

    plan = load_release_plan(root, metadata_path)
    local = local_git_preflight(root, expected_commit)

    # GitHub's anonymous REST quota is shared by the public egress address and
    # can be exhausted by unrelated work.  Complete every local fail-closed
    # check before reading the credential, then use the authenticated quota for
    # the read-only remote preflight.  The companion verifier still performs
    # the required credential-free public-byte readback after publication.
    token = read_token(args.token_file.resolve())
    authenticated = GitHubClient(token=token, user_agent="O011-complete-github-publisher/1.0")
    remote = remote_commit_preflight(authenticated, expected_commit)
    if remote["predecessor_commit"] != local["predecessor_commit"]:
        fail("local and public predecessor-tag commits differ")

    authenticated_remote = authenticated_preflight(authenticated, expected_commit)
    if authenticated_remote != remote:
        fail("authenticated and anonymous remote preflight proofs differ")
    published = publish(authenticated, token, expected_commit, plan)
    del token, authenticated

    receipt = {
        "schema_version": 1,
        "workflow": "o011-publish-github-complete-v1",
        "status": "pass",
        "published_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "authentication_used_for_publication": True,
        "runtime_secret_recorded": False,
        "remote_state_mutated": True,
        "repository": REPOSITORY_URL,
        "tag": TAG,
        "tag_kind": "annotated",
        "release_title": RELEASE_TITLE,
        "version": RELEASE_VERSION,
        "draft": False,
        "prerelease": False,
        "latest_requested": True,
        "commit": expected_commit,
        "predecessor_tag": PREDECESSOR_TAG,
        "predecessor_commit": remote["predecessor_commit"],
        "strict_descendant_of_predecessor": True,
        "remote_default_branch": remote["default_branch"],
        "local_preflight": {
            "head_matches_expected_commit": True,
            "working_tree_clean": True,
            "release_controls_tracked": True,
            "origin_matches_repository": True,
            "new_local_tag_was_absent": True,
        },
        "remote_preflight": {
            "default_branch_matches_expected_commit": True,
            "new_tag_was_absent": True,
            "new_release_was_absent": True,
            "duplicate_tag_or_title_was_absent": True,
        },
        "release_id": published["release_id"],
        "release_url": published["release_url"],
        "tag_object_sha": published["tag_object_sha"],
        "tag_commit": published["tag_commit"],
        "public_file_order": EXPECTED_ORDER,
        "assets": published["assets"],
        "file_count": 7,
        "total_bytes": sum(item["bytes"] for item in plan.assets),
        "release_metadata_sha256": digest(plan.metadata_path),
        "release_notes_sha256": hashlib.sha256(plan.release_notes.encode("utf-8")).hexdigest(),
        "anonymous_public_readback_pending": True,
    }
    if not sanitized(receipt):
        fail("GitHub publication receipt failed final sanitization")
    write_once(receipt_path, receipt, "GitHub publication receipt")
    print(
        json.dumps(
            {
                "status": "published",
                "repository": f"{OWNER}/{REPOSITORY}",
                "tag": TAG,
                "release_id": published["release_id"],
                "assets": 7,
            },
            sort_keys=True,
        )
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--expected-commit", required=True)
    parser.add_argument("--token-file", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--receipt", type=Path, default=DEFAULT_PUBLICATION_RECEIPT)
    args = parser.parse_args()
    try:
        return run(args)
    except ReleaseError as exc:
        raise SystemExit(f"error: {exc}") from None


if __name__ == "__main__":
    raise SystemExit(main())
