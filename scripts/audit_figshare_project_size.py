#!/usr/bin/env python3
"""Boundedly total every file in the authorized Figshare project."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import requests


BASE = "https://api.figshare.com/v2"
PROJECT_ID = 280296


def get_with_backoff(
    session: requests.Session,
    url: str,
    headers: dict[str, str],
    **kwargs,
) -> requests.Response:
    for attempt in range(5):
        response = session.get(url, headers=headers, timeout=60, **kwargs)
        if response.status_code == 200:
            return response
        if response.status_code not in (403, 429) or attempt == 4:
            return response
        time.sleep(10 * (attempt + 1))
    raise AssertionError("unreachable")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--token-file", type=Path, required=True)
    args = parser.parse_args()
    token = args.token_file.resolve().read_text(encoding="utf-8-sig").strip()
    headers = {"Authorization": f"token {token}"}
    session = requests.Session()
    session.trust_env = False
    response = get_with_backoff(
        session,
        f"{BASE}/account/projects/{PROJECT_ID}/articles",
        headers,
        params={"page_size": 1000},
    )
    if response.status_code != 200:
        raise SystemExit(f"project list failed: HTTP {response.status_code}")
    articles = response.json()
    rows = []
    for index, summary in enumerate(articles):
        if index:
            # Figshare's public cloud throttles bursts of otherwise tiny detail
            # reads.  Keep this audit intentionally slow and bounded rather
            # than retrying an aggressive request loop.
            time.sleep(6.5)
        detail_response = get_with_backoff(
            session,
            f"{BASE}/account/articles/{summary['id']}",
            headers,
        )
        if detail_response.status_code != 200:
            raise SystemExit(
                f"article detail failed: {summary['id']} HTTP {detail_response.status_code}"
            )
        detail = detail_response.json()
        files = detail.get("files", [])
        rows.append(
            {
                "article_id": detail["id"],
                "title": detail.get("title"),
                "published": bool(detail.get("published_date")),
                "files": len(files),
                "bytes": sum(int(item.get("size") or 0) for item in files),
            }
        )
    result = {
        "project_id": PROJECT_ID,
        "articles": len(rows),
        "files": sum(row["files"] for row in rows),
        "bytes": sum(row["bytes"] for row in rows),
        "limit_bytes": 20_000_000_000,
        "under_limit": sum(row["bytes"] for row in rows) < 20_000_000_000,
        "rows": rows,
    }
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))


if __name__ == "__main__":
    main()
