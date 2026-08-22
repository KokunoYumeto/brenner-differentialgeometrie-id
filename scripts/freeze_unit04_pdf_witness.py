#!/usr/bin/env python3
"""Freeze the sole official Commons PDF linked from Brenner Unit 4.

This is an authority/render witness only.  It is not a production master and
is deliberately kept outside the mathematical media closure because the
expanded Unit 4 lecture, worksheet, and supplied solutions display no media.
"""

from __future__ import annotations

import base64
import csv
import html
import io
import json
import re
from pathlib import Path
from typing import Any

from freeze_unit_authority import (
    COMMONS_API,
    canonical_json,
    download_binary,
    fetch_frozen_api,
    file_entry,
    preserve_or_write,
    sha,
)


TITLE = "File:Differentialgeometrie (Osnabrück 2023)Vorlesung4.pdf"


def plain_html(value: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", value)).strip()


def ext_value(info: dict[str, Any], name: str) -> str:
    return str(info.get("extmetadata", {}).get(name, {}).get("value", ""))


def one_row(path: Path) -> dict[str, str]:
    rows = list(csv.DictReader(io.StringIO(path.read_text(encoding="utf-8-sig"))))
    matches = [row for row in rows if row.get("title") == TITLE]
    if len(matches) != 1:
        raise RuntimeError(f"expected one frozen link-classification row, found {len(matches)}")
    return matches[0]


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    api_path = root / "authority/mediawiki/unit04_official_lecture_pdf_current.json"
    parameters = {
        "action": "query",
        "format": "json",
        "formatversion": "2",
        "prop": "info|revisions|imageinfo",
        "rvprop": "ids|timestamp|user|userid|comment|sha1|content",
        "rvslots": "main",
        "iiprop": "timestamp|user|url|size|sha1|mime|mediatype|extmetadata",
        "titles": TITLE,
    }
    response_bytes, request_receipt = fetch_frozen_api(api_path, COMMONS_API, parameters)
    payload = json.loads(response_bytes.decode("utf-8"))
    pages = payload.get("query", {}).get("pages", [])
    if len(pages) != 1 or pages[0].get("title") != TITLE or "missing" in pages[0]:
        raise RuntimeError("official Unit 4 lecture PDF is absent or query closure differs")
    page = pages[0]
    revisions = page.get("revisions") or []
    infos = page.get("imageinfo") or []
    if len(revisions) != 1 or len(infos) != 1:
        raise RuntimeError("expected one current page revision and one current file revision")
    revision = revisions[0]
    info = infos[0]
    source = revision.get("slots", {}).get("main", {}).get("content")
    if not isinstance(source, str):
        raise RuntimeError("current Commons description-page source is missing")
    source_bytes = source.encode("utf-8")
    classification_path = root / "authority/brenner_94_link_classification.csv"
    frozen = one_row(classification_path)
    checks = {
        "frozen_row_exists": True,
        "frozen_row_class": frozen["class"] == "per_unit_pdf_link",
        "frozen_row_status": frozen["status"] == "commons_file_verified",
        "frozen_row_exists_flag": frozen["exists"].lower() == "true",
        "frozen_bytes_match": int(frozen["bytes"]) == int(info["size"]),
        "frozen_sha1_match": frozen["commons_sha1_hex"] == info["sha1"],
        "frozen_license_match": frozen["license"] == ext_value(info, "LicenseShortName"),
        "frozen_original_url_match": frozen["source_url"] == info["url"].split("?", 1)[0],
        "mime_is_pdf": info["mime"] == "application/pdf",
        "media_type_is_office": info.get("mediatype") == "OFFICE",
    }
    if not all(checks.values()):
        raise RuntimeError(f"current Commons PDF differs from frozen classification: {checks}")

    stem = f"lecture04_commons_revid{revision['revid']}"
    exact_path = root / f"authority/mediawiki/{stem}.utf8.b64"
    readable_path = root / f"authority/mediawiki/{stem}.wiki"
    exact_bytes = (base64.b64encode(source_bytes).decode("ascii") + "\n").encode("ascii")
    readable_bytes = (source.replace("\r\n", "\n").replace("\r", "\n").rstrip() + "\n").encode("utf-8")
    preserve_or_write(exact_path, exact_bytes)
    preserve_or_write(readable_path, readable_bytes)

    pdf_path = root / f"authority/pdf/{stem}.pdf"
    binary, download_receipt = download_binary(pdf_path, info["url"].split("?", 1)[0])
    if len(binary) != int(info["size"]) or sha(binary, "sha1") != info["sha1"]:
        raise RuntimeError("downloaded official PDF bytes differ from current Commons imageinfo")

    metadata_path = root / f"authority/mediawiki/{stem}.metadata.json"
    metadata = {
        "schema_version": 1,
        "role": "local unredistributed Unit 4 numbering/order witness; never a production master",
        "release_asset": False,
        "redistribution_status": (
            "withheld_pending_resolution_of_internal_cc-by-sa-3.0_and_"
            "commons_structured_metadata_cc-by-sa-4.0_signals"
        ),
        "title": TITLE,
        "commons_pageid": page["pageid"],
        "commons_lastrevid": page.get("lastrevid"),
        "commons_touched": page.get("touched"),
        "description_revision": {
            "revid": revision["revid"],
            "parentid": revision.get("parentid"),
            "timestamp": revision["timestamp"],
            "user": revision.get("user"),
            "userid": revision.get("userid"),
            "comment": revision.get("comment"),
            "mediawiki_revision_sha1": revision["sha1"],
            "mediawiki_revision_sha1_scope": (
                "revision aggregate; the current revision is a structured-data edit, "
                "so this is not asserted as the unchanged main-slot wikitext SHA-1"
            ),
            "source_utf8_bytes": len(source_bytes),
            "source_utf8_sha1": sha(source_bytes, "sha1"),
            "source_utf8_sha256": sha(source_bytes),
            "exact_utf8_base64_witness": file_entry(exact_path, root),
            "readable_normalized_witness": file_entry(readable_path, root),
        },
        "file_revision": {
            "timestamp": info.get("timestamp"),
            "user": info.get("user"),
            "description_url": info["descriptionurl"],
            "original_url": info["url"].split("?", 1)[0],
            "mime": info["mime"],
            "media_type": info.get("mediatype"),
            "width": int(info["width"]),
            "height": int(info["height"]),
            "bytes": int(info["size"]),
            "commons_sha1": info["sha1"],
            "sha256": sha(binary),
            "license": ext_value(info, "LicenseShortName"),
            "license_url": ext_value(info, "LicenseUrl") or None,
            "usage_terms": ext_value(info, "UsageTerms") or None,
            "attribution_required": ext_value(info, "AttributionRequired").lower() == "true",
            "copyrighted": ext_value(info, "Copyrighted"),
            "artist_html": ext_value(info, "Artist"),
            "artist_text": plain_html(ext_value(info, "Artist")),
            "credit_html": ext_value(info, "Credit"),
            "credit_text": plain_html(ext_value(info, "Credit")),
            "binary": file_entry(pdf_path, root),
            "download_receipt": file_entry(pdf_path.with_suffix(".pdf.download.json"), root),
        },
        "api_response": file_entry(api_path, root),
        "api_request_receipt": file_entry(api_path.with_suffix(".json.request.json"), root),
        "api_retrieved_utc": request_receipt["retrieved_utc"],
        "frozen_link_classification": file_entry(classification_path, root),
        "checks": checks,
        "status": "pass",
    }
    preserve_or_write(metadata_path, canonical_json(metadata))

    receipt_path = root / "qa/unit-04/OFFICIAL_PDF_WITNESS.json"
    receipt = {
        "schema_version": 1,
        "scope": "Brenner Unit 4 local unredistributed numbering/order PDF witness only",
        "metadata": file_entry(metadata_path, root),
        "binary": file_entry(pdf_path, root),
        "commons_sha1": info["sha1"],
        "page_revision": revision["revid"],
        "file_timestamp": info.get("timestamp"),
        "license": ext_value(info, "LicenseShortName"),
        "license_url": ext_value(info, "LicenseUrl") or None,
        "production_master": False,
        "release_asset": False,
        "redistribution_status": (
            "withheld_pending_resolution_of_internal_cc-by-sa-3.0_and_"
            "commons_structured_metadata_cc-by-sa-4.0_signals"
        ),
        "status": "pass",
    }
    preserve_or_write(receipt_path, canonical_json(receipt))
    print(json.dumps({**receipt, "receipt": file_entry(receipt_path, root)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
