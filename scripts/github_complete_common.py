#!/usr/bin/env python3
"""Shared fail-closed validation for the complete GitHub release workflow."""

from __future__ import annotations

import hashlib
import json
import os
import re
import ssl
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


OWNER = "KokunoYumeto"
REPOSITORY = "brenner-differentialgeometrie-id"
REPOSITORY_URL = f"https://github.com/{OWNER}/{REPOSITORY}"
TAG = "v1.0.0"
PREDECESSOR_TAG = "v0.22.0-unit-22"
RELEASE_TITLE = "Geometri Diferensial dan Manifold Mulus — Edisi Lengkap Bahasa Indonesia"
RELEASE_VERSION = "2026.08.28-complete"
WORKFLOW = "o011-github-complete-release-v1"
DEFAULT_METADATA = Path("qa/complete/GITHUB_RELEASE_METADATA.json")
DEFAULT_PUBLICATION_RECEIPT = Path("qa/complete/GITHUB_PUBLICATION_RECEIPT.json")
DEFAULT_READBACK_RECEIPT = Path("qa/complete/GITHUB_PUBLIC_READBACK_RECEIPT.json")
EXPECTED_ORDER = [
    "geometri-diferensial-manifold-mulus-edisi-lengkap-id.pdf",
    "geometri-diferensial-manifold-mulus-edisi-lengkap-html-20260828.zip",
    "geometri-diferensial-manifold-mulus-edisi-lengkap-source-backend-20260828.zip",
    "LICENSE.md",
    "RELEASE_NOTES_COMPLETE_20260828.md",
    "FILE_MANIFEST.json",
    "SHA256SUMS.txt",
]
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
PRIVATE_RE = re.compile(
    r"(?i)(?:[A-Z]:[\\/]+Users[\\/]|/Users/|/home/|file://|AppData[\\/]|"
    r"[\\/](?:Downloads|Documents)[\\/]|\\\\[^\\\s]+\\)"
)
SECRET_RE = re.compile(
    r"(?i)(?:access[_-]?token\s*[=:]|authorization\s*:\s*(?:bearer|token)|"
    r"github_pat_[A-Za-z0-9_]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|"
    r"(?:api[_-]?)?key\s*[=:])"
)


class ReleaseError(RuntimeError):
    """A deliberately sanitized release-workflow failure."""


def fail(message: str) -> None:
    raise ReleaseError(message)


class _RejectRedirects(urllib.request.HTTPRedirectHandler):
    """Keep authenticated API headers on api.github.com only."""

    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> None:
        return None


def digest(path: Path) -> str:
    value = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                value.update(block)
    except OSError:
        fail(f"unable to hash required release file {path.name}")
    return value.hexdigest()


def inside(root: Path, path: Path, label: str) -> Path:
    resolved = path.resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        fail(f"{label} must resolve inside the repository root")
    return resolved


def load_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        fail(f"unable to read valid {label} JSON")
    if not isinstance(value, dict):
        fail(f"{label} must be a JSON object")
    return value


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


def sanitized(value: Any) -> bool:
    if isinstance(value, dict):
        for key, item in value.items():
            lowered = str(key).lower()
            if any(term in lowered for term in ("password", "credential", "authorization")):
                return False
            if lowered in {"token", "access_token", "github_token"}:
                return False
            if not sanitized(item):
                return False
        return True
    if isinstance(value, list):
        return all(sanitized(item) for item in value)
    if isinstance(value, str):
        return (
            not PRIVATE_RE.search(value)
            and not SECRET_RE.search(value)
            and "access_token=" not in value.lower()
            and not local_profile_name_present(value)
        )
    return True


def write_once(path: Path, value: dict[str, Any], label: str) -> None:
    if path.exists():
        fail(f"refusing to overwrite {label}")
    if not sanitized(value):
        fail(f"{label} failed its credential/private-locator scan")
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n"
    try:
        with path.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(encoded)
    except FileExistsError:
        fail(f"refusing to overwrite {label}")
    except OSError:
        fail(f"unable to write {label}")


@dataclass(frozen=True)
class ReleasePlan:
    metadata: dict[str, Any]
    metadata_path: Path
    release_dir: Path
    release_notes: str
    assets: tuple[dict[str, Any], ...]
    expected: dict[str, dict[str, Any]]


def _metadata_relative(root: Path, value: Any, label: str) -> Path:
    if not isinstance(value, str) or not value or Path(value).is_absolute():
        fail(f"GitHub metadata {label} must be a nonempty repository-relative path")
    return inside(root, root / value, f"GitHub metadata {label}")


def _checksum_map(path: Path) -> dict[str, str]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError):
        fail("unable to read SHA256SUMS.txt")
    result: dict[str, str] = {}
    for line in lines:
        match = re.fullmatch(r"([0-9a-f]{64})  ([^/\\]+)", line)
        if match is None or match.group(2) in result:
            fail("SHA256SUMS.txt is malformed or contains duplicate names")
        result[match.group(2)] = match.group(1)
    return result


def load_release_plan(root: Path, metadata_path: Path) -> ReleasePlan:
    metadata_path = inside(root, metadata_path, "GitHub release metadata")
    metadata = load_object(metadata_path, "GitHub release metadata")
    repository = metadata.get("repository")
    if (
        metadata.get("schema_version") != 1
        or metadata.get("workflow") != WORKFLOW
        or metadata.get("status") != "ready"
        or metadata.get("tag") != TAG
        or metadata.get("predecessor_tag") != PREDECESSOR_TAG
        or metadata.get("release_title") != RELEASE_TITLE
        or metadata.get("release_version") != RELEASE_VERSION
        or metadata.get("target_commit") != "required_runtime_argument"
        or metadata.get("annotated_tag") is not True
        or metadata.get("draft") is not False
        or metadata.get("prerelease") is not False
        or metadata.get("make_latest") is not True
        or not isinstance(repository, dict)
        or repository.get("owner") != OWNER
        or repository.get("name") != REPOSITORY
        or repository.get("url") != REPOSITORY_URL
    ):
        fail("GitHub release metadata identity or publication state differs")
    if not sanitized(metadata):
        fail("GitHub release metadata contains a credential or private locator")

    order = metadata.get("public_file_order")
    if order != EXPECTED_ORDER or len(set(order)) != 7:
        fail("GitHub release metadata does not bind the exact seven-file order")
    release_dir = _metadata_relative(root, metadata.get("asset_directory"), "asset_directory")
    manifest_path = _metadata_relative(root, metadata.get("manifest"), "manifest")
    sums_path = _metadata_relative(root, metadata.get("checksums"), "checksums")
    notes_path = _metadata_relative(root, metadata.get("release_notes"), "release_notes")
    if (
        manifest_path.parent != release_dir
        or sums_path.parent != release_dir
        or notes_path.parent != release_dir
        or manifest_path.name != "FILE_MANIFEST.json"
        or sums_path.name != "SHA256SUMS.txt"
        or notes_path.name != "RELEASE_NOTES_COMPLETE_20260828.md"
    ):
        fail("GitHub release metadata points outside the exact release directory")
    if not release_dir.is_dir():
        fail("complete release asset directory is missing")

    raw_assets = metadata.get("assets")
    if not isinstance(raw_assets, list) or len(raw_assets) != 7:
        fail("GitHub release metadata must contain exactly seven asset identities")
    assets: list[dict[str, Any]] = []
    expected: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(raw_assets):
        if not isinstance(item, dict) or set(item) != {"name", "bytes", "sha256"}:
            fail("GitHub asset identity has an unexpected shape")
        name = item.get("name")
        size = item.get("bytes")
        sha256 = item.get("sha256")
        if (
            name != EXPECTED_ORDER[index]
            or Path(str(name)).name != name
            or not isinstance(size, int)
            or size <= 0
            or not isinstance(sha256, str)
            or SHA256_RE.fullmatch(sha256) is None
            or name in expected
        ):
            fail("GitHub asset identity differs from the exact public order")
        row = {"name": name, "bytes": size, "sha256": sha256}
        assets.append(row)
        expected[name] = row

    actual_names = sorted(path.name for path in release_dir.iterdir() if path.is_file())
    if actual_names != sorted(EXPECTED_ORDER):
        fail("release directory is not the exact seven-file inventory")
    for item in assets:
        path = release_dir / str(item["name"])
        if path.stat().st_size != item["bytes"] or digest(path) != item["sha256"]:
            fail(f"local release identity differs for {item['name']}")

    manifest = load_object(manifest_path, "complete file manifest")
    if (
        manifest.get("schema_version") != 1
        or manifest.get("status") != "complete_edition"
        or manifest.get("version") != RELEASE_VERSION
        or manifest.get("public_file_order") != EXPECTED_ORDER
    ):
        fail("complete file manifest differs from the GitHub release contract")
    manifest_files = manifest.get("files")
    if not isinstance(manifest_files, list) or len(manifest_files) != 5:
        fail("complete file manifest payload inventory differs")
    manifest_map: dict[str, dict[str, Any]] = {}
    for item in manifest_files:
        if not isinstance(item, dict) or set(item) != {"path", "bytes", "sha256"}:
            fail("complete file manifest contains an unexpected payload identity")
        name = item.get("path")
        if not isinstance(name, str) or name in manifest_map:
            fail("complete file manifest contains a duplicate payload name")
        manifest_map[name] = item
    if list(manifest_map) != EXPECTED_ORDER[:5]:
        fail("complete file manifest payload order differs")
    for name in EXPECTED_ORDER[:5]:
        wanted = expected[name]
        item = manifest_map[name]
        if item.get("bytes") != wanted["bytes"] or item.get("sha256") != wanted["sha256"]:
            fail(f"complete file manifest identity differs for {name}")
    if manifest.get("bytes_bound") != sum(expected[name]["bytes"] for name in EXPECTED_ORDER[:5]):
        fail("complete file manifest bytes_bound differs")

    sums = _checksum_map(sums_path)
    if list(sums) != EXPECTED_ORDER[:6]:
        fail("SHA256SUMS.txt does not bind the expected first six assets in order")
    for name in EXPECTED_ORDER[:6]:
        if sums[name] != expected[name]["sha256"]:
            fail(f"SHA256SUMS.txt identity differs for {name}")

    try:
        notes = notes_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        fail("unable to read complete release notes")
    if RELEASE_VERSION not in notes or not notes.strip() or not sanitized(notes):
        fail("complete release notes are missing their version or fail sanitization")

    publication_receipt = _metadata_relative(
        root, metadata.get("publication_receipt"), "publication_receipt"
    )
    readback_receipt = _metadata_relative(
        root, metadata.get("public_readback_receipt"), "public_readback_receipt"
    )
    if publication_receipt != inside(
        root, root / DEFAULT_PUBLICATION_RECEIPT, "default publication receipt"
    ) or readback_receipt != inside(
        root, root / DEFAULT_READBACK_RECEIPT, "default public-readback receipt"
    ):
        fail("GitHub receipt locations differ from the complete-edition contract")

    return ReleasePlan(
        metadata=metadata,
        metadata_path=metadata_path,
        release_dir=release_dir,
        release_notes=notes,
        assets=tuple(assets),
        expected=expected,
    )


def _decode_json(raw: bytes) -> Any:
    if not raw:
        return None
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError):
        return None


class GitHubClient:
    """Small GitHub API client that never places credentials in URLs."""

    def __init__(self, *, token: str | None, user_agent: str) -> None:
        self._token = token
        self._user_agent = user_agent
        self._opener = urllib.request.build_opener(
            urllib.request.ProxyHandler({}),
            urllib.request.HTTPSHandler(context=ssl.create_default_context()),
            _RejectRedirects(),
        )

    def request_json(
        self,
        method: str,
        path: str,
        expected_statuses: tuple[int, ...],
        label: str,
        body: dict[str, Any] | None = None,
    ) -> tuple[int, Any]:
        if not path.startswith("/") or "?access_token=" in path.lower():
            fail("invalid GitHub API path")
        url = f"https://api.github.com{path}"
        data = None if body is None else json.dumps(body, ensure_ascii=True).encode("utf-8")
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": self._user_agent,
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if data is not None:
            headers["Content-Type"] = "application/json"
        if self._token is not None:
            headers["Authorization"] = f"Bearer {self._token}"
        request = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with self._opener.open(request, timeout=180) as response:
                status = response.status
                raw = response.read()
        except urllib.error.HTTPError as exc:
            status = exc.code
            try:
                raw = exc.read(1024 * 1024)
            except OSError:
                raw = b""
        except (urllib.error.URLError, TimeoutError, OSError):
            fail(f"{label} failed")
        value = _decode_json(raw)
        if status not in expected_statuses:
            message = value.get("message") if isinstance(value, dict) else None
            suffix = f": {message}" if isinstance(message, str) and sanitized(message) else ""
            fail(f"{label} returned HTTP {status}{suffix}")
        return status, value


def api_path(suffix: str = "") -> str:
    return f"/repos/{OWNER}/{REPOSITORY}{suffix}"


def require_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        fail(f"{label} returned a non-object")
    return value


def resolve_tag(client: GitHubClient, tag: str) -> tuple[str, bool, str]:
    encoded = urllib.parse.quote(tag, safe="")
    _, raw_ref = client.request_json(
        "GET", api_path(f"/git/ref/tags/{encoded}"), (200,), f"tag read for {tag}"
    )
    ref = require_object(raw_ref, f"tag read for {tag}")
    target = ref.get("object")
    if not isinstance(target, dict):
        fail(f"tag {tag} has no target object")
    ref_target_sha = target.get("sha")
    if not isinstance(ref_target_sha, str) or COMMIT_RE.fullmatch(ref_target_sha.lower()) is None:
        fail(f"tag {tag} has an invalid ref-target identity")
    ref_target_sha = ref_target_sha.lower()
    annotated = target.get("type") == "tag"
    seen: set[str] = set()
    for _ in range(4):
        kind = target.get("type")
        sha = target.get("sha")
        if not isinstance(sha, str) or COMMIT_RE.fullmatch(sha.lower()) is None:
            fail(f"tag {tag} has an invalid target identity")
        sha = sha.lower()
        if kind == "commit":
            return sha, annotated, ref_target_sha
        if kind != "tag" or sha in seen:
            fail(f"tag {tag} does not resolve unambiguously to a commit")
        seen.add(sha)
        _, raw_tag = client.request_json(
            "GET", api_path(f"/git/tags/{sha}"), (200,), f"annotated tag read for {tag}"
        )
        tag_object = require_object(raw_tag, f"annotated tag read for {tag}")
        target = tag_object.get("object")
        if not isinstance(target, dict):
            fail(f"annotated tag {tag} has no target object")
    fail(f"tag {tag} nesting is unexpectedly deep")


def stream_identity(url: str, name: str, expected_bytes: int) -> dict[str, Any]:
    expected_url = (
        f"{REPOSITORY_URL}/releases/download/{urllib.parse.quote(TAG, safe='')}/"
        f"{urllib.parse.quote(name, safe='')}"
    )
    if url != expected_url or expected_bytes <= 0:
        fail(f"unexpected public download URL for {name}")
    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler({}),
        urllib.request.HTTPSHandler(context=ssl.create_default_context()),
    )
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/octet-stream", "User-Agent": "O011-complete-github-public-readback/1.0"},
        method="GET",
    )
    sha256 = hashlib.sha256()
    size = 0
    try:
        with opener.open(request, timeout=300) as response:
            if response.status != 200:
                fail(f"anonymous download returned HTTP {response.status} for {name}")
            for block in iter(lambda: response.read(1024 * 1024), b""):
                size += len(block)
                if size > expected_bytes:
                    fail(f"anonymous download length differs for {name}")
                sha256.update(block)
    except (urllib.error.URLError, TimeoutError, OSError):
        fail(f"anonymous download failed for {name}")
    return {"bytes": size, "sha256": sha256.hexdigest()}
