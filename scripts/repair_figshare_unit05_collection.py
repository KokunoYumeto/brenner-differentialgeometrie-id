#!/usr/bin/env python3
"""Add the existing public O011 item to the Indonesian collection and publish."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import requests


BASE = "https://api.figshare.com/v2"
ARTICLE_ID = 33314790
COLLECTION_ID = 8668413


def require(response: requests.Response, expected: tuple[int, ...]) -> dict | list:
    if response.status_code not in expected:
        try:
            body = response.json()
        except ValueError:
            body = {"message": response.text[:500]}
        raise SystemExit(json.dumps({"status_code": response.status_code, "error": body}, ensure_ascii=True, sort_keys=True))
    return response.json() if response.content else {}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--token-file", type=Path, required=True)
    args = parser.parse_args()
    token = args.token_file.resolve().read_text(encoding="utf-8-sig").strip()
    if not token or any(character.isspace() for character in token):
        raise SystemExit("invalid token-file shape")

    session = requests.Session()
    session.trust_env = False
    headers = {"Authorization": f"token {token}"}
    json_headers = {**headers, "Content-Type": "application/json"}
    member_url = f"{BASE}/account/collections/{COLLECTION_ID}/articles"
    before = require(
        session.get(member_url, headers=headers, params={"page_size": 1000}, timeout=60),
        (200,),
    )
    added = ARTICLE_ID not in {int(item["id"]) for item in before}
    publish: dict | list = {}
    if added:
        require(
            session.post(
                member_url,
                headers=json_headers,
                json={"articles": [ARTICLE_ID]},
                timeout=60,
            ),
            (200, 201),
        )
        after_private = require(
            session.get(member_url, headers=headers, params={"page_size": 1000}, timeout=60),
            (200,),
        )
        if ARTICLE_ID not in {int(item["id"]) for item in after_private}:
            raise SystemExit("collection membership did not persist privately")
        publish = require(
            session.post(
                f"{BASE}/account/collections/{COLLECTION_ID}/publish",
                headers=headers,
                timeout=120,
            ),
            (201,),
        )

    public_session = requests.Session()
    public_session.trust_env = False
    public_collection = require(
        public_session.get(f"{BASE}/collections/{COLLECTION_ID}", timeout=60),
        (200,),
    )
    public_members = require(
        public_session.get(
            f"{BASE}/collections/{COLLECTION_ID}/articles",
            params={"page_size": 1000},
            timeout=60,
        ),
        (200,),
    )
    if ARTICLE_ID not in {int(item["id"]) for item in public_members}:
        raise SystemExit("anonymous collection membership verification failed")
    print(
        json.dumps(
            {
                "status": "pass",
                "article_id": ARTICLE_ID,
                "collection_id": COLLECTION_ID,
                "added": added,
                "collection_doi": public_collection.get("doi"),
                "collection_version": public_collection.get("version"),
                "collection_members": len(public_members),
                "authentication_used_for_public_readback": False,
                "publish_response": {
                    key: publish.get(key)
                    for key in ("location", "doi")
                    if isinstance(publish, dict) and publish.get(key)
                },
            },
            ensure_ascii=True,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
