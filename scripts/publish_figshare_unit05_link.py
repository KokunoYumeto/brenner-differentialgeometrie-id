#!/usr/bin/env python3
"""Publish the CC0 Figshare metadata/link item for the mixed-license Unit 5 release."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import requests


BASE = "https://api.figshare.com/v2"
PROJECT_ID = 280296
COLLECTION_ID = 8668413
ZENODO_CONCEPT = "10.5281/zenodo.22059977"


def require(response: requests.Response, expected: tuple[int, ...]) -> dict | list:
    if response.status_code not in expected:
        try:
            body = response.json()
        except ValueError:
            body = {"message": response.text[:500]}
        raise SystemExit(json.dumps({"status_code": response.status_code, "error": body}, ensure_ascii=True, sort_keys=True))
    if not response.content:
        return {}
    return response.json()


def projection(article: dict) -> dict:
    return {
        "title": article.get("title"),
        "description": article.get("description"),
        "defined_type": article.get("defined_type_name") or article.get("defined_type"),
        "license": (article.get("license") or {}).get("value") if isinstance(article.get("license"), dict) else article.get("license"),
        "authors": [item.get("full_name") or item.get("name") for item in article.get("authors", [])],
        "categories": sorted(item.get("id") if isinstance(item, dict) else item for item in article.get("categories", [])),
        "tags": article.get("tags", []),
        "files": article.get("files", []),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--token-file", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    args = parser.parse_args()

    token = args.token_file.resolve().read_text(encoding="utf-8-sig").strip()
    if not token or any(character.isspace() for character in token):
        raise SystemExit("invalid token-file shape")
    metadata = json.loads(args.metadata.resolve().read_text(encoding="utf-8"))
    headers = {"Authorization": f"token {token}", "Accept": "application/json"}
    json_headers = {**headers, "Content-Type": "application/json"}
    session = requests.Session()
    # Ignore machine-level request configuration that incorrectly yields a
    # generic Figshare 403 even on public endpoints.
    session.trust_env = False

    licenses = require(session.get(f"{BASE}/account/licenses", headers=headers, timeout=60), (200,))
    available = {item["value"]: item["name"] for item in licenses}
    if available.get(2) != "CC0":
        raise SystemExit("account CC0 license id is not the verified value 2")
    if any("ShareAlike" in name or "BY-SA" in name for name in available.values()):
        raise SystemExit("account license surface changed; re-evaluate whether exact bytes may be mirrored")
    if metadata.get("license") != 2:
        raise SystemExit("Figshare link item must be CC0 metadata only")

    articles = require(
        session.get(
            f"{BASE}/account/projects/{PROJECT_ID}/articles",
            headers=headers,
            params={"page_size": 1000},
            timeout=60,
        ),
        (200,),
    )
    candidates = [
        item
        for item in articles
        if item.get("title", "").casefold() == metadata["title"].casefold()
        or (
            "geometri diferensial" in item.get("title", "").casefold()
            and "manifold mulus" in item.get("title", "").casefold()
        )
    ]
    if len(candidates) > 1:
        raise SystemExit("multiple candidate Figshare items; refusing to duplicate or guess")
    if candidates:
        article_id = int(candidates[0]["id"])
        detail = require(session.get(f"{BASE}/account/articles/{article_id}", headers=headers, timeout=60), (200,))
        related = [item.get("identifier") for item in detail.get("related_materials", [])]
        if ZENODO_CONCEPT not in related:
            raise SystemExit("similarly titled Figshare item is not bound to this Zenodo concept")
        if detail.get("published_date"):
            raise SystemExit("exact Figshare item already published; use public verifier instead")
        require(session.patch(f"{BASE}/account/articles/{article_id}", headers=json_headers, json=metadata, timeout=60), (200, 205,))
        creation = "updated_existing_draft"
    else:
        created = require(
            session.post(
                f"{BASE}/account/projects/{PROJECT_ID}/articles",
                headers=json_headers,
                json=metadata,
                timeout=60,
            ),
            (201,),
        )
        location = created.get("location") or ""
        match = re.search(r"/(\d+)$", location)
        if not match:
            raise SystemExit("Figshare create response did not return an article location")
        article_id = int(match.group(1))
        creation = "created"

    require(
        session.put(
            f"{BASE}/account/articles/{article_id}/authors",
            headers=json_headers,
            json={"authors": metadata["authors"]},
            timeout=60,
        ),
        (200, 205,),
    )
    detail = require(session.get(f"{BASE}/account/articles/{article_id}", headers=headers, timeout=60), (200,))
    view = projection(detail)
    if view["title"] != metadata["title"] or view["description"] != metadata["description"]:
        raise SystemExit("Figshare draft title/description mismatch")
    if view["license"] != 2 or view["defined_type"] != "online resource":
        raise SystemExit("Figshare draft type/license mismatch")
    if view["authors"] != ["Holger Brenner"]:
        raise SystemExit("Figshare draft author mismatch")
    if view["categories"] != sorted(metadata["categories"]):
        raise SystemExit("Figshare draft category mismatch")
    if view["tags"] != metadata["tags"] or view["files"]:
        raise SystemExit("Figshare draft tags or zero-file invariant mismatch")

    published = require(session.post(f"{BASE}/account/articles/{article_id}/publish", headers=headers, timeout=120), (201,))
    public = require(session.get(f"{BASE}/articles/{article_id}", timeout=60), (200,))
    public_view = projection(public)
    if public_view != view or public.get("id") != article_id or not public.get("published_date"):
        raise SystemExit("anonymous Figshare article verification mismatch")
    related = {item.get("identifier") for item in public.get("related_materials", [])}
    if ZENODO_CONCEPT not in related or public.get("files"):
        raise SystemExit("public Figshare link/zero-file invariant mismatch")

    members = require(
        session.get(
            f"{BASE}/account/collections/{COLLECTION_ID}/articles",
            headers=headers,
            params={"page_size": 1000},
            timeout=60,
        ),
        (200,),
    )
    if article_id not in {int(item["id"]) for item in members}:
        require(
            session.post(
                f"{BASE}/account/collections/{COLLECTION_ID}/articles",
                headers=json_headers,
                json={"articles": [article_id]},
                timeout=60,
            ),
            (200, 201,),
        )
    members = require(
        session.get(
            f"{BASE}/account/collections/{COLLECTION_ID}/articles",
            headers=headers,
            params={"page_size": 1000},
            timeout=60,
        ),
        (200,),
    )
    if article_id not in {int(item["id"]) for item in members}:
        raise SystemExit("article was not added to the Indonesian collection draft")

    collection_publish = require(
        session.post(f"{BASE}/account/collections/{COLLECTION_ID}/publish", headers=headers, timeout=120),
        (201,),
    )
    collection = require(session.get(f"{BASE}/collections/{COLLECTION_ID}", timeout=60), (200,))
    public_members = require(
        session.get(
            f"{BASE}/collections/{COLLECTION_ID}/articles",
            params={"page_size": 1000},
            timeout=60,
        ),
        (200,),
    )
    if article_id not in {int(item["id"]) for item in public_members}:
        raise SystemExit("anonymous collection membership verification failed")

    result = {
        "status": "pass",
        "creation": creation,
        "article_id": article_id,
        "article_doi": public.get("doi"),
        "article_url": public.get("url_public_html"),
        "article_version": public.get("version"),
        "article_files": 0,
        "article_license": public_view["license"],
        "zenodo_concept": ZENODO_CONCEPT,
        "collection_id": COLLECTION_ID,
        "collection_doi": collection.get("doi"),
        "collection_version": collection.get("version"),
        "collection_members": len(public_members),
        "authentication_used_for_public_readback": False,
        "publish_response": published,
        "collection_publish_response": collection_publish,
    }
    # Keep output sanitized: responses contain no account token, but retain only
    # primitive publication identifiers if the API returned larger objects.
    result["publish_response"] = {
        key: published.get(key) for key in ("location", "doi") if published.get(key)
    }
    result["collection_publish_response"] = {
        key: collection_publish.get(key) for key in ("location", "doi") if collection_publish.get(key)
    }
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))


if __name__ == "__main__":
    main()
