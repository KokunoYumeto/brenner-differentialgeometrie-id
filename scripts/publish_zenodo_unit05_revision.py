#!/usr/bin/env python3
"""Publish the sanitized Unit 5 repair in the existing Zenodo concept."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import quote

import requests


DEPOSITION = 22060146
CONCEPT = "22059977"
DOI = "10.5281/zenodo.22060146"
FILES = (
    ("output/pdf/geometri-diferensial-manifold-mulus-hingga-unit-05-id.pdf", "geometri-diferensial-manifold-mulus-hingga-unit-05-id.pdf"),
    ("output/zenodo/geometri-diferensial-manifold-mulus-brenner-id-unit05-20260822.zip", "geometri-diferensial-manifold-mulus-brenner-id-unit05-20260822.zip"),
    ("qa/unit-05/RELEASE_NOTES_20260822.md", "RELEASE_NOTES_20260822.md"),
)


def digest(path: Path, algorithm: str) -> str:
    value = hashlib.new(algorithm)
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def response_json(response: requests.Response, expected: tuple[int, ...]) -> dict:
    if response.status_code not in expected:
        try:
            error = response.json()
        except ValueError:
            error = {"message": response.text[:500]}
        raise SystemExit(json.dumps({"status_code": response.status_code, "error": error}, ensure_ascii=True, sort_keys=True))
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
    local = {}
    for relative, public_name in FILES:
        path = (root / relative).resolve()
        local[public_name] = {
            "path": path,
            "bytes": path.stat().st_size,
            "sha256": digest(path, "sha256"),
            "md5": digest(path, "md5"),
        }

    headers = {"Authorization": f"Bearer {token}"}
    url = f"https://zenodo.org/api/deposit/depositions/{DEPOSITION}"
    draft = response_json(requests.get(url, headers=headers, timeout=60), (200,))
    if str(draft.get("conceptrecid")) != CONCEPT or draft.get("submitted"):
        raise SystemExit("unexpected corrective-draft identity or state")
    if ((draft.get("metadata") or {}).get("prereserve_doi") or {}).get("doi") != DOI:
        raise SystemExit("unexpected corrective reserved DOI")

    draft = response_json(
        requests.put(url, headers={**headers, "Content-Type": "application/json"}, json=payload, timeout=60),
        (200,),
    )
    bucket = (draft.get("links") or {}).get("bucket")
    if not bucket:
        raise SystemExit("corrective draft has no bucket")
    for name, item in local.items():
        with item["path"].open("rb") as stream:
            uploaded = response_json(
                requests.put(
                    f"{bucket.rstrip('/')}/{quote(name, safe='')}",
                    headers=headers,
                    data=stream,
                    timeout=300,
                ),
                (200, 201),
            )
        if file_identity(uploaded) != (name, item["bytes"], item["md5"]):
            raise SystemExit(f"corrective upload mismatch: {name}")

    draft = response_json(requests.get(url, headers=headers, timeout=60), (200,))
    remote = {file_identity(item)[0]: file_identity(item) for item in draft.get("files", [])}
    if set(remote) != set(local):
        raise SystemExit("corrective draft file inventory mismatch")
    for name, item in local.items():
        if remote[name] != (name, item["bytes"], item["md5"]):
            raise SystemExit(f"corrective draft bytes mismatch: {name}")
    metadata = draft.get("metadata") or {}
    expected = payload["metadata"]
    for field in ("title", "upload_type", "publication_type", "description", "access_right", "license", "publication_date", "version", "language", "keywords"):
        if metadata.get(field) != expected.get(field):
            raise SystemExit(f"corrective metadata mismatch: {field}")
    if [item.get("name") for item in metadata.get("creators", [])] != ["Brenner, Holger"]:
        raise SystemExit("corrective creator mismatch")
    if [{"name": item.get("name"), "type": item.get("type")} for item in metadata.get("contributors", [])] != expected["contributors"]:
        raise SystemExit("corrective contributor mismatch")

    published = response_json(requests.post(f"{url}/actions/publish", headers=headers, timeout=120), (200, 201, 202))
    result = {
        "status": "published",
        "record_id": published.get("record_id") or published.get("id"),
        "concept_record_id": published.get("conceptrecid"),
        "doi": published.get("doi"),
        "state": published.get("state"),
        "submitted": published.get("submitted"),
        "files": [
            {"name": name, "bytes": item["bytes"], "sha256": item["sha256"], "md5": item["md5"]}
            for name, item in local.items()
        ],
    }
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))


if __name__ == "__main__":
    main()
