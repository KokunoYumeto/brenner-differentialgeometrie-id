#!/usr/bin/env python3
"""Publish the exact verified Unit 5 checkpoint to its reserved Zenodo record."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import quote

import requests


EXPECTED_DEPOSITION = 22059978
EXPECTED_CONCEPT = "22059977"
EXPECTED_DOI = "10.5281/zenodo.22059978"
UPLOADS = (
    (
        "output/pdf/geometri-diferensial-manifold-mulus-hingga-unit-05-id.pdf",
        "geometri-diferensial-manifold-mulus-hingga-unit-05-id.pdf",
    ),
    (
        "output/zenodo/geometri-diferensial-manifold-mulus-brenner-id-unit05-20260822.zip",
        "geometri-diferensial-manifold-mulus-brenner-id-unit05-20260822.zip",
    ),
    ("qa/unit-05/RELEASE_NOTES_20260822.md", "RELEASE_NOTES_20260822.md"),
)


def digest(path: Path, algorithm: str) -> str:
    value = hashlib.new(algorithm)
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def require_response(response: requests.Response, expected: tuple[int, ...]) -> dict:
    if response.status_code not in expected:
        try:
            body = response.json()
        except ValueError:
            body = {"message": response.text[:500]}
        raise SystemExit(
            json.dumps(
                {"status_code": response.status_code, "error": body},
                ensure_ascii=True,
                sort_keys=True,
            )
        )
    return response.json()


def normalized_checksum(value: str | None) -> str:
    if not value:
        return ""
    return value.removeprefix("md5:")


def file_view(item: dict) -> tuple[str, int, str]:
    name = item.get("filename") or item.get("name") or item.get("key")
    size = item.get("filesize") or item.get("size")
    return str(name), int(size), normalized_checksum(item.get("checksum"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--token-file", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--deposition", type=int, default=EXPECTED_DEPOSITION)
    args = parser.parse_args()

    if args.deposition != EXPECTED_DEPOSITION:
        raise SystemExit("refusing unexpected Zenodo deposition id")
    root = args.root.resolve()
    token_file = args.token_file.resolve()
    metadata_path = (root / args.metadata).resolve()
    token = token_file.read_text(encoding="utf-8-sig").strip()
    if not token or any(character.isspace() for character in token):
        raise SystemExit("invalid token-file shape")
    payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    expected_metadata = payload["metadata"]

    local_files: dict[str, dict] = {}
    for relative, public_name in UPLOADS:
        path = (root / relative).resolve()
        if not path.is_file():
            raise SystemExit(f"required upload missing: {relative}")
        local_files[public_name] = {
            "path": path,
            "bytes": path.stat().st_size,
            "sha256": digest(path, "sha256"),
            "md5": digest(path, "md5"),
        }

    headers = {"Authorization": f"Bearer {token}"}
    json_headers = {**headers, "Content-Type": "application/json"}
    deposition_url = f"https://zenodo.org/api/deposit/depositions/{args.deposition}"

    draft = require_response(requests.get(deposition_url, headers=headers, timeout=60), (200,))
    if str(draft.get("conceptrecid")) != EXPECTED_CONCEPT:
        raise SystemExit("unexpected Zenodo concept record")
    if draft.get("submitted") or draft.get("state") == "done":
        raise SystemExit("record is already published; use anonymous verifier")
    reserved = (draft.get("metadata") or {}).get("prereserve_doi") or {}
    if reserved.get("doi") != EXPECTED_DOI:
        raise SystemExit("unexpected reserved DOI")

    draft = require_response(
        requests.put(
            deposition_url,
            headers=json_headers,
            json=payload,
            timeout=60,
        ),
        (200,),
    )
    bucket = (draft.get("links") or {}).get("bucket")
    if not bucket:
        raise SystemExit("Zenodo draft has no upload bucket")

    remote_existing = {file_view(item)[0]: file_view(item) for item in draft.get("files", [])}
    unexpected = sorted(set(remote_existing) - set(local_files))
    if unexpected:
        raise SystemExit("unexpected files already in draft: " + ", ".join(unexpected))

    upload_results = []
    for public_name, local in local_files.items():
        existing = remote_existing.get(public_name)
        if existing:
            if existing[1] != local["bytes"] or existing[2] != local["md5"]:
                raise SystemExit(f"existing draft file differs: {public_name}")
            upload_results.append({"name": public_name, "status": "already_exact"})
            continue
        with local["path"].open("rb") as stream:
            uploaded = require_response(
                requests.put(
                    f"{bucket.rstrip('/')}/{quote(public_name, safe='')}",
                    headers=headers,
                    data=stream,
                    timeout=300,
                ),
                (200, 201),
            )
        view = file_view(uploaded)
        if view[0] != public_name or view[1] != local["bytes"] or view[2] != local["md5"]:
            raise SystemExit(f"upload response mismatch: {public_name}")
        upload_results.append({"name": public_name, "status": "uploaded"})

    draft = require_response(requests.get(deposition_url, headers=headers, timeout=60), (200,))
    remote_files = {file_view(item)[0]: file_view(item) for item in draft.get("files", [])}
    if set(remote_files) != set(local_files):
        raise SystemExit("draft file inventory does not match the three-file release")
    for name, local in local_files.items():
        remote = remote_files[name]
        if remote[1] != local["bytes"] or remote[2] != local["md5"]:
            raise SystemExit(f"draft file identity mismatch: {name}")

    metadata = draft.get("metadata") or {}
    exact_fields = (
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
    )
    for field in exact_fields:
        if metadata.get(field) != expected_metadata.get(field):
            raise SystemExit(f"Zenodo normalized an exact metadata field unexpectedly: {field}")
    creator_projection = [
        {key: item[key] for key in ("name", "affiliation", "orcid", "gnd") if item.get(key)}
        for item in metadata.get("creators", [])
    ]
    if creator_projection != expected_metadata.get("creators"):
        raise SystemExit("Zenodo creator metadata mismatch")
    contributor_projection = [
        {key: item[key] for key in ("name", "type", "affiliation", "orcid", "gnd") if item.get(key)}
        for item in metadata.get("contributors", [])
    ]
    if contributor_projection != expected_metadata.get("contributors"):
        raise SystemExit("Zenodo contributor metadata mismatch")
    related_projection = [
        {
            key: item[key]
            for key in ("identifier", "relation", "resource_type", "scheme")
            if item.get(key)
        }
        for item in metadata.get("related_identifiers", [])
    ]
    if related_projection != expected_metadata.get("related_identifiers"):
        raise SystemExit("Zenodo related-identifier metadata mismatch")

    published = require_response(
        requests.post(
            f"{deposition_url}/actions/publish",
            headers=headers,
            timeout=120,
        ),
        (200, 201, 202),
    )
    result = {
        "status": "published",
        "record_id": published.get("record_id") or published.get("id"),
        "concept_record_id": published.get("conceptrecid"),
        "doi": published.get("doi"),
        "doi_url": published.get("doi_url"),
        "state": published.get("state"),
        "submitted": published.get("submitted"),
        "metadata_license": (published.get("metadata") or {}).get("license"),
        "uploads": upload_results,
        "files": [
            {
                "name": name,
                "bytes": local["bytes"],
                "sha256": local["sha256"],
                "md5": local["md5"],
            }
            for name, local in local_files.items()
        ],
    }
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))


if __name__ == "__main__":
    main()
