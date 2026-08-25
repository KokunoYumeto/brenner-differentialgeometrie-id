#!/usr/bin/env python3
"""Anonymously verify the public Figshare Unit 5 metadata/link item."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import time
from pathlib import Path
from urllib.parse import unquote

import requests


BASE = "https://api.figshare.com/v2"
ARTICLE_ID = 33314790
PROJECT_ID = 280296
COLLECTION_ID = 8668413
ARTICLE_DOI = "10.6084/m9.figshare.33314790.v1"
ZENODO_CONCEPT = "10.5281/zenodo.22059977"


def get_json(session: requests.Session, url: str, **kwargs) -> dict | list:
    for attempt in range(3):
        response = session.get(url, timeout=60, **kwargs)
        if response.status_code == 200:
            data = response.json()
            time.sleep(1.1)
            return data
        if response.status_code not in (403, 429) or attempt == 2:
            raise SystemExit(f"anonymous Figshare GET failed: HTTP {response.status_code} {url}")
        time.sleep(5 * (attempt + 1))
    raise AssertionError("unreachable")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--metadata", type=Path, required=True)
    args = parser.parse_args()
    expected = json.loads(args.metadata.resolve().read_text(encoding="utf-8"))

    session = requests.Session()
    session.trust_env = False
    article = get_json(session, f"{BASE}/articles/{ARTICLE_ID}")
    if article.get("id") != ARTICLE_ID or article.get("doi") != ARTICLE_DOI or article.get("version") != 1:
        raise SystemExit("public Figshare article identity mismatch")
    for field in ("title", "description", "tags"):
        if article.get(field) != expected.get(field):
            raise SystemExit(f"public Figshare metadata mismatch: {field}")
    if article.get("defined_type_name") != expected["defined_type"]:
        raise SystemExit("public Figshare defined type mismatch")
    if (article.get("license") or {}).get("value") != 2 or (article.get("license") or {}).get("name") != "CC0":
        raise SystemExit("public Figshare metadata license mismatch")
    if [item.get("full_name") for item in article.get("authors", [])] != ["Holger Brenner"]:
        raise SystemExit("public Figshare author mismatch")
    if sorted(item.get("id") for item in article.get("categories", [])) != sorted(expected["categories"]):
        raise SystemExit("public Figshare categories mismatch")
    if article.get("files"):
        raise SystemExit("Figshare link item unexpectedly contains files")
    related = {unquote(item.get("identifier", "")) for item in article.get("related_materials", [])}
    if related != {unquote(item["identifier"]) for item in expected["related_materials"]}:
        raise SystemExit("public Figshare related-material set mismatch")
    if ZENODO_CONCEPT not in related:
        raise SystemExit("public Figshare item lacks Zenodo concept link")

    project_articles = get_json(
        session,
        f"{BASE}/projects/{PROJECT_ID}/articles",
        params={"page_size": 1000},
    )
    if ARTICLE_ID not in {int(item["id"]) for item in project_articles}:
        raise SystemExit("public Figshare project membership mismatch")
    collection = get_json(session, f"{BASE}/collections/{COLLECTION_ID}")
    collection_articles = get_json(
        session,
        f"{BASE}/collections/{COLLECTION_ID}/articles",
        params={"page_size": 1000},
    )
    if ARTICLE_ID not in {int(item["id"]) for item in collection_articles}:
        raise SystemExit("public Indonesian collection membership mismatch")

    result = {
        "status": "pass",
        "authentication_used": False,
        "verified_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "article_id": ARTICLE_ID,
        "article_doi": ARTICLE_DOI,
        "article_url": article.get("url_public_html"),
        "files": 0,
        "license": article.get("license"),
        "project_id": PROJECT_ID,
        "project_url": "https://figshare.com/projects/Open_and_Share-Alike_Educational_Materials_Translations/280296",
        "collection_id": COLLECTION_ID,
        "collection_doi": collection.get("doi"),
        "collection_version": collection.get("version"),
        "collection_members": len(collection_articles),
        "zenodo_concept": ZENODO_CONCEPT,
    }
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))


if __name__ == "__main__":
    main()
