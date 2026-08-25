#!/usr/bin/env python3
"""Publish the reader-first linked-file revision of the Unit 5 Figshare item."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import time
from pathlib import Path
from urllib.parse import quote, urljoin

import requests


BASE = "https://api.figshare.com/v2"
ARTICLE_ID = 33314790
PROJECT_ID = 280296
COLLECTION_ID = 8668413
ZENODO_RECORD = 22060387
ZENODO_CONCEPT = "10.5281/zenodo.22059977"
PROJECT_AUDIT_BYTES = 133_963_919
PROJECT_CAP_BYTES = 20_000_000_000
LANE_CAP_BYTES = 500_000_000
FILES = (
    (
        "output/pdf/geometri-diferensial-manifold-mulus-hingga-unit-05-id.pdf",
        "geometri-diferensial-manifold-mulus-hingga-unit-05-id.pdf",
    ),
    (
        "output/zenodo/geometri-diferensial-manifold-mulus-brenner-id-unit05-20260822.zip",
        "geometri-diferensial-manifold-mulus-brenner-id-unit05-20260822.zip",
    ),
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
        raise SystemExit(
            json.dumps(
                {"status_code": response.status_code, "error": body},
                ensure_ascii=True,
                sort_keys=True,
            )
        )
    if not response.content:
        return {}
    return response.json()


def digest_bytes(path: Path) -> tuple[int, str, str]:
    sha256 = hashlib.sha256()
    md5 = hashlib.md5()
    size = 0
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            size += len(block)
            sha256.update(block)
            md5.update(block)
    return size, sha256.hexdigest(), md5.hexdigest()


def projection(article: dict) -> dict:
    license_value = article.get("license")
    if isinstance(license_value, dict):
        license_value = license_value.get("value")
    return {
        "title": article.get("title"),
        "description": article.get("description"),
        "defined_type": article.get("defined_type_name") or article.get("defined_type"),
        "license": license_value,
        "authors": [item.get("full_name") or item.get("name") for item in article.get("authors", [])],
        "categories": sorted(
            item.get("id") if isinstance(item, dict) else item
            for item in article.get("categories", [])
        ),
        "tags": article.get("tags", []),
        "is_metadata_record": bool(article.get("is_metadata_record")),
    }


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
    metadata = json.loads((root / args.metadata).read_text(encoding="utf-8"))

    local: dict[str, dict[str, object]] = {}
    for relative, name in FILES:
        path = (root / relative).resolve()
        size, sha256, md5 = digest_bytes(path)
        local[name] = {
            "path": path,
            "bytes": size,
            "sha256": sha256,
            "md5": md5,
            "link": (
                f"https://zenodo.org/records/{ZENODO_RECORD}/files/"
                f"{quote(name, safe='')}"
            ),
        }
    lane_bytes = sum(int(item["bytes"]) for item in local.values())
    if lane_bytes >= LANE_CAP_BYTES:
        raise SystemExit("bounded linked payload is not below the 500 MB lane cap")
    if PROJECT_AUDIT_BYTES + lane_bytes >= PROJECT_CAP_BYTES:
        raise SystemExit("bounded project size proof is not below the 20 GB cap")

    headers = {"Authorization": f"token {token}", "Accept": "application/json"}
    json_headers = {**headers, "Content-Type": "application/json"}
    session = requests.Session()
    session.trust_env = False

    licenses = require(
        session.get(f"{BASE}/account/licenses", headers=headers, timeout=60),
        (200,),
    )
    available = {int(item["value"]): item["name"] for item in licenses}
    if available.get(2) != "CC0":
        raise SystemExit("account CC0 license id is not the verified value 2")
    if any("ShareAlike" in name or "BY-SA" in name for name in available.values()):
        raise SystemExit("Figshare license surface changed; exact-hosting route must be re-evaluated")
    if metadata.get("license") != 2 or metadata.get("is_metadata_record") is not False:
        raise SystemExit("linked item must explicitly scope CC0 to non-metadata-only link metadata")
    description = metadata.get("description", "")
    required_phrases = (
        "CC0 pada Figshare berlaku hanya untuk metadata/katalog",
        "bukan</strong> berlisensi CC0",
        "CC BY-SA 4.0",
        "tidak diunggah atau dilisensikan ulang oleh Figshare",
        "active_partial",
    )
    if any(phrase not in description for phrase in required_phrases):
        raise SystemExit("Figshare rights/status disclosure is incomplete")

    article_url = f"{BASE}/account/articles/{ARTICLE_ID}"
    before = require(session.get(article_url, headers=headers, timeout=60), (200,))
    if int(before.get("id")) != ARTICLE_ID or not before.get("published_date"):
        raise SystemExit("unexpected existing Figshare item identity or publication state")
    related_before = {item.get("identifier") for item in before.get("related_materials", [])}
    if ZENODO_CONCEPT not in related_before:
        raise SystemExit("existing Figshare item is not bound to this Zenodo concept")
    existing_files = before.get("files", [])
    expected_pdf_name = FILES[0][1]
    expected_pdf_url = str(local[expected_pdf_name]["link"])
    if existing_files:
        if len(existing_files) != 1 or not existing_files[0].get("is_link_only"):
            raise SystemExit("existing Figshare private revision has an ambiguous file inventory")
        existing = existing_files[0]
        # A first attempt exposed the correct PDF but included ?download=1 in
        # the visible filename.  Delete only that exact private linked-file
        # record, then recreate it with the canonical URL whose path ends in
        # the real PDF filename.  The already-public v1 remains immutable.
        if (
            existing.get("name") == expected_pdf_name + "?download=1"
            and existing.get("download_url") == expected_pdf_url + "?download=1"
        ):
            require(
                session.delete(
                    f"{article_url}/files/{int(existing['id'])}",
                    headers=headers,
                    timeout=60,
                ),
                (200, 202, 204),
            )
            existing_files = []
        elif not (
            existing.get("name") == expected_pdf_name
            and existing.get("download_url") == expected_pdf_url
        ):
            raise SystemExit("existing linked file is not the exact expected reader PDF")

    require(
        session.put(
            article_url,
            headers=json_headers,
            json=metadata,
            timeout=60,
        ),
        (200, 205),
    )
    require(
        session.put(
            f"{article_url}/authors",
            headers=json_headers,
            json={"authors": metadata["authors"]},
            timeout=60,
        ),
        (200, 205),
    )

    if not existing_files:
        name = expected_pdf_name
        item = local[name]
        created = require(
            session.post(
                f"{article_url}/files",
                headers=json_headers,
                json={"link": item["link"]},
                timeout=120,
            ),
            (201,),
        )
        location = created.get("location") or ""
        if not location:
            raise SystemExit(f"Figshare linked-file creation omitted location: {name}")
        linked = require(
            session.get(urljoin(BASE + "/", location), headers=headers, timeout=60),
            (200,),
        )
        if not linked.get("is_link_only"):
            raise SystemExit(f"Figshare did not mark remote file as link-only: {name}")
        time.sleep(1.5)

    detail = require(session.get(article_url, headers=headers, timeout=60), (200,))
    view = projection(detail)
    # Figshare's HTML sanitizer normalizes single-quoted href attributes to
    # double quotes without changing the links or visible prose.
    canonical_description = metadata["description"].replace("href='", 'href="').replace("'>", '">')
    if view != {
        "title": metadata["title"],
        "description": canonical_description,
        "defined_type": "book",
        "license": 2,
        "authors": ["Holger Brenner"],
        "categories": sorted(metadata["categories"]),
        "tags": metadata["tags"],
        "is_metadata_record": False,
    }:
        raise SystemExit("Figshare private revision metadata mismatch")
    private_files = detail.get("files", [])
    if len(private_files) != 1 or not private_files[0].get("is_link_only"):
        raise SystemExit("Figshare private linked-file inventory mismatch")
    if private_files[0].get("name") != expected_pdf_name:
        raise SystemExit("Figshare private file order is not reader-first")
    if private_files[0].get("download_url") != expected_pdf_url:
        raise SystemExit("Figshare private linked-file URL mismatch")

    published = require(
        session.post(f"{article_url}/publish", headers=headers, timeout=120),
        (201,),
    )

    public_session = requests.Session()
    public_session.trust_env = False
    public = require(public_session.get(f"{BASE}/articles/{ARTICLE_ID}", timeout=60), (200,))
    public_view = projection(public)
    if public_view != view or int(public.get("version") or 0) < 2:
        raise SystemExit("anonymous Figshare metadata/version readback mismatch")
    public_files = public.get("files", [])
    if len(public_files) != 1 or not public_files[0].get("is_link_only"):
        raise SystemExit("anonymous Figshare linked-file inventory mismatch")
    if (
        public_files[0].get("name") != expected_pdf_name
        or public_files[0].get("download_url") != expected_pdf_url
    ):
        raise SystemExit("anonymous Figshare file is not the canonical reader-first PDF")

    readback = []
    for name, item in local.items():
        download_url = (
            public_files[0]["download_url"]
            if name == expected_pdf_name
            else str(item["link"])
        )
        response = public_session.get(download_url, stream=True, timeout=300)
        if response.status_code != 200:
            raise SystemExit(f"anonymous Figshare-linked download failed: {name}")
        sha256 = hashlib.sha256()
        md5 = hashlib.md5()
        size = 0
        for block in response.iter_content(1024 * 1024):
            if block:
                size += len(block)
                sha256.update(block)
                md5.update(block)
        identity = (size, sha256.hexdigest(), md5.hexdigest())
        expected = (int(item["bytes"]), str(item["sha256"]), str(item["md5"]))
        if identity != expected:
            raise SystemExit(f"anonymous Figshare-linked byte mismatch: {name}")
        readback.append(
            {
                "name": name,
                "bytes": size,
                "sha256": identity[1],
                "md5": identity[2],
                "download_url": download_url,
                "figshare_visible_file": name == expected_pdf_name,
                "is_external_zenodo_link": True,
                "matches_local": True,
            }
        )

    project_articles = require(
        public_session.get(
            f"{BASE}/projects/{PROJECT_ID}/articles",
            params={"page_size": 1000},
            timeout=60,
        ),
        (200,),
    )
    if ARTICLE_ID not in {int(item["id"]) for item in project_articles}:
        raise SystemExit("anonymous Figshare project membership verification failed")

    account_collection_articles = require(
        session.get(
            f"{BASE}/account/collections/{COLLECTION_ID}/articles",
            headers=headers,
            params={"page_size": 1000},
            timeout=60,
        ),
        (200,),
    )
    collection_publish: dict | list = {}
    if ARTICLE_ID not in {int(item["id"]) for item in account_collection_articles}:
        require(
            session.post(
                f"{BASE}/account/collections/{COLLECTION_ID}/articles",
                headers=json_headers,
                json={"articles": [ARTICLE_ID]},
                timeout=60,
            ),
            (200, 201),
        )
        account_collection_articles = require(
            session.get(
                f"{BASE}/account/collections/{COLLECTION_ID}/articles",
                headers=headers,
                params={"page_size": 1000},
                timeout=60,
            ),
            (200,),
        )
        if ARTICLE_ID not in {int(item["id"]) for item in account_collection_articles}:
            raise SystemExit("Figshare collection membership add did not persist")
        collection_publish = require(
            session.post(
                f"{BASE}/account/collections/{COLLECTION_ID}/publish",
                headers=headers,
                timeout=120,
            ),
            (201,),
        )

    collection_articles = require(
        public_session.get(
            f"{BASE}/collections/{COLLECTION_ID}/articles",
            params={"page_size": 1000},
            timeout=60,
        ),
        (200,),
    )
    member = next(
        (item for item in collection_articles if int(item["id"]) == ARTICLE_ID),
        None,
    )
    if member is None:
        raise SystemExit("anonymous Indonesian collection membership verification failed")
    collection = require(
        public_session.get(f"{BASE}/collections/{COLLECTION_ID}", timeout=60),
        (200,),
    )

    result = {
        "status": "pass",
        "verified_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "article_id": ARTICLE_ID,
        "article_doi": public.get("doi"),
        "article_url": public.get("url_public_html"),
        "article_version": public.get("version"),
        "article_license": public_view["license"],
        "article_files": len(public_files),
        "description_linked_companion_files": len(local) - len(public_files),
        "lane_linked_bytes": lane_bytes,
        "lane_cap_bytes": LANE_CAP_BYTES,
        "project_audit_bytes_before_links": PROJECT_AUDIT_BYTES,
        "project_cap_bytes": PROJECT_CAP_BYTES,
        "project_upper_bound_after_links": PROJECT_AUDIT_BYTES + lane_bytes,
        "collection_id": COLLECTION_ID,
        "collection_doi": collection.get("doi"),
        "collection_version": collection.get("version"),
        "collection_members": len(collection_articles),
        "collection_member_doi": member.get("doi"),
        "authentication_used_for_public_readback": False,
        "files": readback,
        "publish_response": {
            key: published.get(key)
            for key in ("location", "doi")
            if published.get(key)
        },
        "collection_publish_response": {
            key: collection_publish.get(key)
            for key in ("location", "doi")
            if isinstance(collection_publish, dict) and collection_publish.get(key)
        },
    }
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))


if __name__ == "__main__":
    main()
