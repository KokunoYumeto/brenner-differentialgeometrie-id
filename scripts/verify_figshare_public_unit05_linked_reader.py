#!/usr/bin/env python3
"""Anonymously verify the public reader-first Unit 5 Figshare item and links."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path

import requests


BASE = "https://api.figshare.com/v2"
ARTICLE_ID = 33314790
PROJECT_ID = 280296
COLLECTION_ID = 8668413
ARTICLE_DOI = "10.6084/m9.figshare.33314790.v2"
ZENODO_RECORD = 22060387
FILES = (
    ("output/pdf/geometri-diferensial-manifold-mulus-hingga-unit-05-id.pdf", "geometri-diferensial-manifold-mulus-hingga-unit-05-id.pdf"),
    ("output/zenodo/geometri-diferensial-manifold-mulus-brenner-id-unit05-20260822.zip", "geometri-diferensial-manifold-mulus-brenner-id-unit05-20260822.zip"),
    ("LICENSE.md", "LICENSE.md"),
    ("qa/unit-05/RELEASE_NOTES_20260822.md", "RELEASE_NOTES_20260822.md"),
    ("output/figshare/FILE_MANIFEST.csv", "FILE_MANIFEST.csv"),
    ("output/figshare/CHECKSUMS.sha256", "CHECKSUMS.sha256"),
)


def require(response: requests.Response, expected: tuple[int, ...]) -> dict | list:
    if response.status_code not in expected:
        try:
            body = response.json()
        except ValueError:
            body = {"message": response.text[:500]}
        raise SystemExit(json.dumps({"status_code": response.status_code, "error": body}, ensure_ascii=True, sort_keys=True))
    return response.json() if response.content else {}


def local_identity(path: Path) -> tuple[int, str, str]:
    sha256 = hashlib.sha256()
    md5 = hashlib.md5()
    size = 0
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            size += len(block)
            sha256.update(block)
            md5.update(block)
    return size, sha256.hexdigest(), md5.hexdigest()


def remote_identity(session: requests.Session, url: str) -> tuple[int, str, str]:
    response = session.get(url, stream=True, timeout=300)
    if response.status_code != 200:
        raise SystemExit(f"anonymous linked download failed: HTTP {response.status_code} {url}")
    sha256 = hashlib.sha256()
    md5 = hashlib.md5()
    size = 0
    for block in response.iter_content(1024 * 1024):
        if block:
            size += len(block)
            sha256.update(block)
            md5.update(block)
    return size, sha256.hexdigest(), md5.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    expected = json.loads((root / args.metadata).read_text(encoding="utf-8"))
    canonical_description = expected["description"].replace("href='", 'href="').replace("'>", '">')

    session = requests.Session()
    session.trust_env = False
    article = require(session.get(f"{BASE}/articles/{ARTICLE_ID}", timeout=60), (200,))
    license_value = article.get("license") or {}
    if not isinstance(license_value, dict):
        raise SystemExit("public Figshare license shape mismatch")
    checks = {
        "id": int(article.get("id") or 0) == ARTICLE_ID,
        "doi": article.get("doi") == ARTICLE_DOI,
        "version": int(article.get("version") or 0) == 2,
        "title": article.get("title") == expected["title"],
        "description": article.get("description") == canonical_description,
        "license": int(license_value.get("value") or 0) == 2,
        "type": article.get("defined_type_name") == "book",
        "status": "active_partial" in article.get("description", ""),
        "rights_scope": all(
            phrase in article.get("description", "")
            for phrase in (
                "CC0 pada Figshare berlaku hanya untuk metadata/katalog",
                "bukan</strong> berlisensi CC0",
                "CC BY-SA 4.0",
                "tidak diunggah atau dilisensikan ulang oleh Figshare",
            )
        ),
        "no_umbrella_label": all(
            label not in (article.get("title", "") + article.get("description", ""))
            for label in ("TTP", "Translation and Transcription Project")
        ),
        "author": [item.get("full_name") for item in article.get("authors", [])] == ["Holger Brenner"],
    }
    if not all(checks.values()):
        raise SystemExit(f"anonymous Figshare metadata mismatch: {checks}")

    public_files = article.get("files", [])
    pdf_name = FILES[0][1]
    pdf_url = f"https://zenodo.org/records/{ZENODO_RECORD}/files/{pdf_name}"
    if len(public_files) != 1:
        raise SystemExit("public Figshare item does not expose exactly one primary reader")
    primary = public_files[0]
    if not primary.get("is_link_only") or primary.get("name") != pdf_name or primary.get("download_url") != pdf_url:
        raise SystemExit("public Figshare primary file is not the canonical linked PDF")

    readback = []
    for relative, name in FILES:
        local = (root / relative).resolve()
        url = pdf_url if name == pdf_name else f"https://zenodo.org/records/{ZENODO_RECORD}/files/{name}"
        if name != pdf_name and url not in article.get("description", ""):
            raise SystemExit(f"companion link missing from public description: {name}")
        local_value = local_identity(local)
        remote_value = remote_identity(session, url)
        if remote_value != local_value:
            raise SystemExit(f"anonymous linked-byte mismatch: {name}")
        readback.append(
            {
                "name": name,
                "bytes": remote_value[0],
                "sha256": remote_value[1],
                "md5": remote_value[2],
                "url": url,
                "figshare_primary_file": name == pdf_name,
                "matches_local": True,
            }
        )

    project_members = require(
        session.get(f"{BASE}/projects/{PROJECT_ID}/articles", params={"page_size": 1000}, timeout=60),
        (200,),
    )
    if ARTICLE_ID not in {int(item["id"]) for item in project_members}:
        raise SystemExit("public project membership mismatch")
    collection = require(session.get(f"{BASE}/collections/{COLLECTION_ID}", timeout=60), (200,))
    collection_members = require(
        session.get(f"{BASE}/collections/{COLLECTION_ID}/articles", params={"page_size": 1000}, timeout=60),
        (200,),
    )
    if ARTICLE_ID not in {int(item["id"]) for item in collection_members}:
        raise SystemExit("public Indonesian collection membership mismatch")

    print(
        json.dumps(
            {
                "status": "pass",
                "authentication_used": False,
                "verified_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                "article_id": ARTICLE_ID,
                "article_doi": ARTICLE_DOI,
                "article_url": article.get("url_public_html"),
                "article_version": 2,
                "article_license": {"value": 2, "name": license_value.get("name")},
                "figshare_visible_files": 1,
                "description_companion_links": 5,
                "linked_payload_bytes": sum(item["bytes"] for item in readback),
                "project_id": PROJECT_ID,
                "project_members": len(project_members),
                "collection_id": COLLECTION_ID,
                "collection_doi": collection.get("doi"),
                "collection_version": collection.get("version"),
                "collection_members": len(collection_members),
                "files": readback,
            },
            ensure_ascii=True,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
