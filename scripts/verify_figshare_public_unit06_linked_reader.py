#!/usr/bin/env python3
"""Anonymously verify the exact public Unit 6 Figshare metadata/link version."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

import requests

import publish_figshare_unit06_linked_reader as core


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Anonymously verify full Unit 6 Figshare metadata, lineage, membership, and linked bytes."
    )
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--staging-receipt", type=Path, required=True)
    parser.add_argument("--zenodo-record", type=int, required=True)
    parser.add_argument("--article-version", type=int, required=True)
    parser.add_argument(
        "--expected-predecessor-version",
        type=int,
        default=core.DEFAULT_PREDECESSOR_VERSION,
        help="version immediately before --article-version (default: 2)",
    )
    args = parser.parse_args()
    if args.zenodo_record <= 0 or args.zenodo_record == core.PREVIOUS_ZENODO_RECORD:
        raise SystemExit("a new Unit 6 Zenodo record id is required")
    if args.expected_predecessor_version <= 0 or args.article_version != args.expected_predecessor_version + 1:
        raise SystemExit("article version must be exactly expected predecessor version plus one")

    root = args.root.resolve()
    metadata = json.loads((root / args.metadata).resolve().read_text(encoding="utf-8"))
    if not isinstance(metadata, dict):
        raise SystemExit("Figshare metadata root must be an object")
    expected_projection = core.validate_metadata(metadata, args.zenodo_record)
    local, lane_bytes = core.load_local_boundary(root, (root / args.staging_receipt).resolve())

    session = requests.Session()
    session.trust_env = False
    session.headers.update({"User-Agent": core.USER_AGENT})
    zenodo_record, zenodo_preflight = core.verify_zenodo_boundary(
        session,
        args.zenodo_record,
        local,
    )
    project_members, collection_members, collection = core.public_membership_preflight(session)
    article = core.request_json(
        session,
        "GET",
        f"{core.FIGSHARE_BASE}/articles/{core.ARTICLE_ID}",
        (200,),
        "anonymous Figshare Unit 6 article read",
        timeout=60,
    )
    if not isinstance(article, dict):
        raise SystemExit("anonymous Figshare Unit 6 article read returned an unexpected shape")
    pdf_url = core.zenodo_url(args.zenodo_record, core.PDF_NAME)
    core.require_target(article, args.article_version, expected_projection, pdf_url)
    size_proof = core.project_size_proof(session, lane_bytes, None)
    linked_readback = core.verify_public_links(session, article, args.zenodo_record, local)

    actual_projection = core.metadata_projection(article)
    if actual_projection != expected_projection:
        raise SystemExit("anonymous Figshare full metadata projection mismatch")
    if actual_projection["related_materials"] != core.normalized_related(metadata["related_materials"]):
        raise SystemExit("anonymous Figshare related-material object parity mismatch")

    print(
        json.dumps(
            {
                "schema_version": 2,
                "workflow": "o011-verify-figshare-public-unit06-linked-reader-v2",
                "status": "pass",
                "authentication_used": False,
                "verified_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                "article_id": core.ARTICLE_ID,
                "article_doi": article.get("doi"),
                "article_url": article.get("url_public_html"),
                "article_version": args.article_version,
                "expected_predecessor_version": args.expected_predecessor_version,
                "article_license": {"value": core.CC0_LICENSE_ID, "name": "CC0"},
                "article_defined_type_request": "metadata",
                "article_defined_type_name": article.get("defined_type_name"),
                "is_metadata_record": False,
                "authors": actual_projection["authors"],
                "categories": actual_projection["categories"],
                "tags": actual_projection["tags"],
                "related_materials": actual_projection["related_materials"],
                "figshare_visible_files": 1,
                "description_companion_links": len(local) - 1,
                "linked_payload_bytes": lane_bytes,
                "zenodo_record": args.zenodo_record,
                "zenodo_doi": zenodo_record.get("doi"),
                "zenodo_concept_record_id": core.ZENODO_CONCEPT_ID,
                "zenodo_concept_doi": core.ZENODO_CONCEPT_DOI,
                "zenodo_anonymous_preflight_files": zenodo_preflight,
                "project_id": core.PROJECT_ID,
                "project_members": len(project_members),
                "project_size_proof": size_proof,
                "collection_id": core.COLLECTION_ID,
                "collection_doi": collection.get("doi"),
                "collection_version": collection.get("version"),
                "collection_members": len(collection_members),
                "files": linked_readback,
            },
            ensure_ascii=True,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
