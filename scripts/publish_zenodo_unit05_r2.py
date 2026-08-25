#!/usr/bin/env python3
"""Publish the reader-first Unit 5 preservation revision in its Zenodo concept."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import quote

import requests


CURRENT_RECORD = 22060146
CONCEPT = "22059977"
FILES = (
    ("output/pdf/geometri-diferensial-manifold-mulus-hingga-unit-05-id.pdf", "geometri-diferensial-manifold-mulus-hingga-unit-05-id.pdf"),
    ("output/zenodo/geometri-diferensial-manifold-mulus-brenner-id-unit05-20260822.zip", "geometri-diferensial-manifold-mulus-brenner-id-unit05-20260822.zip"),
    ("LICENSE.md", "LICENSE.md"),
    ("qa/unit-05/RELEASE_NOTES_20260822.md", "RELEASE_NOTES_20260822.md"),
    ("output/figshare/FILE_MANIFEST.csv", "FILE_MANIFEST.csv"),
    ("output/figshare/CHECKSUMS.sha256", "CHECKSUMS.sha256"),
)


def digest(path: Path, algorithm: str) -> str:
    value = hashlib.new(algorithm)
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def require(response: requests.Response, expected: tuple[int, ...]) -> dict:
    if response.status_code not in expected:
        try:
            error = response.json()
        except ValueError:
            error = {"message": response.text[:500]}
        raise SystemExit(
            json.dumps(
                {"status_code": response.status_code, "error": error},
                ensure_ascii=True,
                sort_keys=True,
            )
        )
    return response.json()


def file_identity(item: dict) -> tuple[str, int, str]:
    name = item.get("filename") or item.get("key") or item.get("name")
    size = item.get("filesize") or item.get("size")
    checksum = str(item.get("checksum") or "").removeprefix("md5:")
    return str(name), int(size), checksum


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--token-file", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    args = parser.parse_args()

    root = args.root.resolve()
    token = args.token_file.resolve().read_text(encoding="utf-8-sig").strip()
    if not token or any(character.isspace() for character in token):
        raise SystemExit("invalid token-file shape")
    payload = json.loads((root / args.metadata).read_text(encoding="utf-8"))
    local: dict[str, dict[str, object]] = {}
    for relative, public_name in FILES:
        path = (root / relative).resolve()
        local[public_name] = {
            "path": path,
            "bytes": path.stat().st_size,
            "sha256": digest(path, "sha256"),
            "md5": digest(path, "md5"),
        }

    session = requests.Session()
    session.trust_env = False
    headers = {"Authorization": f"Bearer {token}"}
    current_url = f"https://zenodo.org/api/deposit/depositions/{CURRENT_RECORD}"
    current = require(session.get(current_url, headers=headers, timeout=60), (200,))
    if str(current.get("conceptrecid")) != CONCEPT or not current.get("submitted"):
        raise SystemExit("unexpected current Zenodo record identity or state")

    created_response = session.post(
        f"{current_url}/actions/newversion", headers=headers, timeout=120
    )
    created = require(created_response, (200, 201, 202))
    if created.get("submitted"):
        latest_draft = (created.get("links") or {}).get("latest_draft")
        if not latest_draft:
            raise SystemExit("new-version response did not identify a draft")
        draft = require(session.get(latest_draft, headers=headers, timeout=60), (200,))
    else:
        draft = created
    if str(draft.get("conceptrecid")) != CONCEPT or draft.get("submitted"):
        raise SystemExit("unexpected new Zenodo draft identity or state")

    draft_id = int(draft["id"])
    draft_url = f"https://zenodo.org/api/deposit/depositions/{draft_id}"
    for item in draft.get("files", []):
        file_id = item.get("id")
        if not file_id:
            raise SystemExit("inherited Zenodo file lacks an id")
        deleted = session.delete(
            f"{draft_url}/files/{file_id}", headers=headers, timeout=60
        )
        if deleted.status_code not in (200, 202, 204):
            require(deleted, (200, 202, 204))

    draft = require(
        session.put(
            draft_url,
            headers={**headers, "Content-Type": "application/json"},
            json=payload,
            timeout=60,
        ),
        (200,),
    )
    bucket = (draft.get("links") or {}).get("bucket")
    if not bucket:
        raise SystemExit("new Zenodo draft has no upload bucket")

    for name, item in local.items():
        path = item["path"]
        assert isinstance(path, Path)
        with path.open("rb") as stream:
            uploaded = require(
                session.put(
                    f"{bucket.rstrip('/')}/{quote(name, safe='')}",
                    headers=headers,
                    data=stream,
                    timeout=300,
                ),
                (200, 201),
            )
        if file_identity(uploaded) != (name, int(item["bytes"]), str(item["md5"])):
            raise SystemExit(f"Zenodo upload identity mismatch: {name}")

    draft = require(session.get(draft_url, headers=headers, timeout=60), (200,))
    remote = {file_identity(item)[0]: file_identity(item) for item in draft.get("files", [])}
    if set(remote) != set(local):
        raise SystemExit("new Zenodo draft inventory mismatch")
    for name, item in local.items():
        if remote[name] != (name, int(item["bytes"]), str(item["md5"])):
            raise SystemExit(f"new Zenodo draft byte mismatch: {name}")

    metadata = draft.get("metadata") or {}
    expected = payload["metadata"]
    for field in (
        "title",
        "upload_type",
        "publication_type",
        "description",
        "access_right",
        "license",
        "publication_date",
        "version",
        "language",
        "keywords",
    ):
        if metadata.get(field) != expected.get(field):
            raise SystemExit(f"new Zenodo metadata mismatch: {field}")
    if [item.get("name") for item in metadata.get("creators", [])] != ["Brenner, Holger"]:
        raise SystemExit("new Zenodo creator mismatch")
    if [
        {"name": item.get("name"), "type": item.get("type")}
        for item in metadata.get("contributors", [])
    ] != expected["contributors"]:
        raise SystemExit("new Zenodo contributor mismatch")

    published = require(
        session.post(f"{draft_url}/actions/publish", headers=headers, timeout=120),
        (200, 201, 202),
    )
    result = {
        "status": "published",
        "record_id": published.get("record_id") or published.get("id"),
        "concept_record_id": published.get("conceptrecid"),
        "doi": published.get("doi"),
        "state": published.get("state"),
        "submitted": published.get("submitted"),
        "files": [
            {
                "name": name,
                "bytes": item["bytes"],
                "sha256": item["sha256"],
                "md5": item["md5"],
            }
            for name, item in local.items()
        ],
    }
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))


if __name__ == "__main__":
    main()
