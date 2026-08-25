#!/usr/bin/env python3
"""Freeze one source-linked Commons animation outside static TeX media."""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
from pathlib import Path
from typing import Any


LINK_RE = re.compile(r"\[\[(?:File|Datei):([^|\]]+\.gif)", re.IGNORECASE)


def load_freeze_helpers(root: Path) -> Any:
    path = root / "scripts/freeze_unit_authority.py"
    spec = importlib.util.spec_from_file_location("o011_freeze_helpers", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load authority-freeze helpers")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def media_key(value: str) -> str:
    return re.sub(r"[_\s]+", " ", value.strip()).casefold()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--unit", type=int, required=True, choices=range(1, 30))
    parser.add_argument("--surface", required=True)
    parser.add_argument("--source-tex", type=Path, required=True)
    parser.add_argument("--filename", required=True)
    parser.add_argument("--alt-text-source", required=True)
    parser.add_argument("--alt-text-id", required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()

    root = args.root.resolve()
    helpers = load_freeze_helpers(root)
    source_path = (root / args.source_tex).resolve()
    source_path.relative_to(root)
    source_text = source_path.read_text(encoding="utf-8")
    linked = [name.strip() for name in LINK_RE.findall(source_text)]
    matches = [name for name in linked if media_key(name) == media_key(args.filename)]
    if len(matches) != 1:
        raise RuntimeError(
            f"expected one exact source-linked GIF occurrence for {args.filename!r}; found {matches!r}"
        )

    unit_tag = f"unit{args.unit:02d}"
    query_path = root / "authority/mediawiki" / f"{unit_tag}_interactive_media_imageinfo_current.json"
    parameters = {
        "action": "query",
        "format": "json",
        "formatversion": "2",
        "prop": "info|imageinfo",
        "iiprop": "timestamp|user|url|size|sha1|mime|extmetadata",
        "titles": "File:" + args.filename,
    }
    query_bytes, query_receipt = helpers.fetch_frozen_api(
        query_path, helpers.COMMONS_API, parameters
    )
    payload = json.loads(query_bytes.decode("utf-8"))
    pages = payload.get("query", {}).get("pages", [])
    if len(pages) != 1 or "missing" in pages[0]:
        raise RuntimeError("Commons did not return one existing interactive-media page")
    page = pages[0]
    canonical_filename = str(page.get("title", "")).removeprefix("File:")
    if media_key(canonical_filename) != media_key(args.filename):
        raise RuntimeError("Commons canonical title differs from the requested GIF")
    imageinfo = page.get("imageinfo") or []
    if len(imageinfo) != 1:
        raise RuntimeError("Commons did not return one current imageinfo row")
    info = imageinfo[0]
    if info.get("mime") != "image/gif":
        raise RuntimeError("interactive companion is not a GIF")

    license_name = helpers.ext_value(info, "LicenseShortName")
    license_url = helpers.ext_value(info, "LicenseUrl")
    artist_html = helpers.ext_value(info, "Artist")
    artist_text = helpers.plain_html(artist_html)
    attribution_required = helpers.ext_value(info, "AttributionRequired").lower() == "true"
    if not license_name or (license_name != "Public domain" and not license_url):
        raise RuntimeError("Commons interactive-media license closure is incomplete")
    if attribution_required and not artist_text:
        raise RuntimeError("Commons interactive-media creator closure is incomplete")

    original_url = str(info["url"]).split("?", 1)[0]
    binary_path = root / "authority/media" / canonical_filename
    binary, download_receipt = helpers.download_binary(binary_path, original_url)
    if len(binary) != int(info["size"]) or helpers.sha(binary, "sha1") != info["sha1"]:
        raise RuntimeError("downloaded interactive-media bytes differ from Commons imageinfo")

    asset = {
        "filename": canonical_filename,
        "source_page": info["descriptionurl"],
        "source_url": original_url,
        "creator": artist_text,
        "creator_html": artist_html,
        "license": license_name,
        "license_url": license_url or None,
        "attribution_required": attribution_required,
        "commons_pageid": int(page["pageid"]),
        "commons_lastrevid": int(page.get("lastrevid") or 0),
        "commons_touched": page.get("touched"),
        "image_timestamp": info.get("timestamp"),
        "image_user": info.get("user"),
        "mime": info["mime"],
        "width": int(info["width"]),
        "height": int(info["height"]),
        "bytes": len(binary),
        "sha1": helpers.sha(binary, "sha1"),
        "sha256": helpers.sha(binary),
        "alt_text_source": args.alt_text_source,
        "alt_text_id": args.alt_text_id,
        "role": "source-linked animation; retain as an interactive/downloadable surface",
    }
    manifest = {
        "schema_version": 1,
        "unit": args.unit,
        "surface": args.surface,
        "description": "Source-linked animation surface preserved separately from static TeX media attribution.",
        "source_surface": helpers.file_entry(source_path, root),
        "source_link_occurrences": 1,
        "query": helpers.file_entry(query_path, root),
        "query_request_receipt": helpers.file_entry(
            query_path.with_suffix(query_path.suffix + ".request.json"), root
        ),
        "query_retrieved_utc": query_receipt["retrieved_utc"],
        "download_receipt": download_receipt,
        "assets": [asset],
    }
    receipt = {
        "schema_version": 1,
        "workflow": f"o011-unit{args.unit:02d}-interactive-media-freeze-v1",
        "status": "pass",
        "scope": args.surface + " source-linked animation",
        "api_authority": helpers.COMMONS_API,
        "source_solution_binding": helpers.rel(source_path, root),
        "source_link_occurrences": 1,
        "assets": [
            {
                "filename": asset["filename"],
                "pageid": asset["commons_pageid"],
                "lastrevid": asset["commons_lastrevid"],
                "bytes": asset["bytes"],
                "sha1": asset["sha1"],
                "sha256": asset["sha256"],
                "creator": asset["creator"],
                "license": asset["license"],
                "license_url": asset["license_url"],
                "role": "interactive/downloadable source surface",
            }
        ],
        "preserved_locally": True,
        "translation_surface_requirement": "retain the source link and accessible Indonesian alt text; do not silently replace the animation with a static claim",
    }
    manifest_path = (root / args.manifest).resolve()
    receipt_path = (root / args.receipt).resolve()
    manifest_path.relative_to(root)
    receipt_path.relative_to(root)
    helpers.preserve_or_write(manifest_path, helpers.canonical_json(manifest))
    helpers.preserve_or_write(receipt_path, helpers.canonical_json(receipt))
    print(
        json.dumps(
            {
                "status": "pass",
                "manifest": helpers.file_entry(manifest_path, root),
                "receipt": helpers.file_entry(receipt_path, root),
                "asset": helpers.file_entry(binary_path, root),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
