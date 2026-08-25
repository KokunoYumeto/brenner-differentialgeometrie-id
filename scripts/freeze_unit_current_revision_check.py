#!/usr/bin/env python3
"""Freeze a bounded live-current revision check for one admitted Brenner unit."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from freeze_unit_authority import (
    WIKIVERSITY_API,
    canonical_json,
    fetch_frozen_api,
    file_entry,
    preserve_or_write,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--unit", type=int, required=True, choices=range(1, 30))
    args = parser.parse_args()
    root = args.root.resolve()
    unit = args.unit
    manifest_path = root / f"qa/unit-{unit:02d}/AUTHORITY_PREFLIGHT.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    pages = manifest["authority"]["pages"]
    expected = {
        item["title"]: {
            "surface": key,
            "pageid": int(item["pageid"]),
            "revid": int(item["revid"]),
            "timestamp": item["timestamp"],
        }
        for key, item in pages.items()
    }
    query_path = root / f"authority/mediawiki/unit{unit:02d}_root_surfaces_current.json"
    parameters = {
        "action": "query",
        "format": "json",
        "formatversion": "2",
        "prop": "info|revisions",
        "rvprop": "ids|timestamp|sha1",
        "titles": "|".join(expected),
    }
    response_bytes, request_receipt = fetch_frozen_api(
        query_path, WIKIVERSITY_API, parameters
    )
    payload = json.loads(response_bytes.decode("utf-8"))
    current_pages = payload.get("query", {}).get("pages", [])
    current_by_title = {page["title"]: page for page in current_pages}
    if set(current_by_title) != set(expected):
        raise RuntimeError("live-current title closure differs from the four frozen surfaces")
    comparisons = []
    for title, frozen in expected.items():
        page = current_by_title[title]
        revisions = page.get("revisions") or []
        if len(revisions) != 1 or "missing" in page:
            raise RuntimeError(f"missing or ambiguous live-current revision: {title}")
        revision = revisions[0]
        row = {
            **frozen,
            "title": title,
            "current_pageid": int(page["pageid"]),
            "current_lastrevid": int(page["lastrevid"]),
            "current_revid": int(revision["revid"]),
            "current_timestamp": revision["timestamp"],
            "current_revision_sha1": revision["sha1"],
        }
        row["pageid_match"] = row["current_pageid"] == row["pageid"]
        row["revid_match"] = row["current_revid"] == row["revid"]
        row["lastrevid_match"] = row["current_lastrevid"] == row["revid"]
        row["timestamp_match"] = row["current_timestamp"] == row["timestamp"]
        comparisons.append(row)
    matches = all(
        row[key]
        for row in comparisons
        for key in ("pageid_match", "revid_match", "lastrevid_match", "timestamp_match")
    )
    if not matches:
        raise RuntimeError("one or more frozen Unit surfaces are no longer live-current")
    receipt = {
        "schema_version": 1,
        "workflow": "o011-brenner-unit-live-current-revision-check-v1",
        "unit": unit,
        "retrieved_utc": request_receipt["retrieved_utc"],
        "api_response": file_entry(query_path, root),
        "api_request_receipt": file_entry(query_path.with_suffix(".json.request.json"), root),
        "preflight_input": file_entry(manifest_path, root),
        "surfaces": comparisons,
        "all_four_frozen_revisions_remain_live_current": matches,
        "status": "pass",
    }
    output_path = root / f"qa/unit-{unit:02d}/CURRENT_REVISION_CHECK.json"
    preserve_or_write(output_path, canonical_json(receipt))
    print(json.dumps({**receipt, "receipt": file_entry(output_path, root)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
