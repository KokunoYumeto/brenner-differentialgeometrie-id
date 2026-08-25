#!/usr/bin/env python3
"""Render and validate Unit 6 Figshare metadata after Zenodo assigns a record."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


MODEL_IDENTIFICATION = "OpenAI Codex gpt-5.6-sol, Ultra"
ZENODO_CONCEPT_DOI = "10.5281/zenodo.22059977"
LANE_CAP_BYTES = 500_000_000
TITLE = "Geometri Diferensial dan Manifold Mulus — Edisi Bahasa Indonesia (batas Unit 06; rilis kerja parsial)"
PDF_NAME = "geometri-diferensial-manifold-mulus-hingga-unit-06-id.pdf"
PUBLIC_FILES = (
    PDF_NAME,
    "geometri-diferensial-manifold-mulus-brenner-id-unit06-20260822.zip",
    "LICENSE.md",
    "RELEASE_NOTES_20260822.md",
    "FILE_MANIFEST.csv",
    "CHECKSUMS.sha256",
)
AUTHORS = [{"name": "Holger Brenner"}]
CATEGORIES = [29830, 26095]
TAGS = [
    "Bahasa Indonesia",
    "differential geometry",
    "smooth manifolds",
    "parallel transport",
    "open educational resources",
    "translation",
    "active_partial",
    "D50",
    "O011",
    "CC BY-SA 4.0",
    "mixed component licenses",
    "linked reader",
]
MARKERS = (
    "{{ZENODO_RECORD}}",
    "{{ZENODO_DOI}}",
    "{{PUBLIC_PAYLOAD_BYTES_ID}}",
)
PRIVATE_LOCATOR = re.compile(
    r"[A-Za-z]:[\\/]+Users[\\/]+|(?<!:)/Users/|(?<![:A-Za-z0-9_])/(?:home|srv/home)/[A-Za-z0-9._-]+/",
    re.IGNORECASE,
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def expected_related_materials(zenodo_doi: str) -> list[dict[str, object]]:
    return [
        {
            "identifier": ZENODO_CONCEPT_DOI,
            "identifier_type": "DOI",
            "relation": "References",
            "is_linkout": True,
            "title": "Zenodo concept — latest preservation version",
        },
        {
            "identifier": zenodo_doi,
            "identifier_type": "DOI",
            "relation": "References",
            "is_linkout": False,
            "title": "Zenodo Unit 06 reader-first preservation version",
        },
        {
            "identifier": "https://de.wikiversity.org/wiki/Kurs:Differentialgeometrie_(Osnabr%C3%BCck_2023)",
            "identifier_type": "URL",
            "relation": "IsDerivedFrom",
            "is_linkout": False,
            "title": "Official source course",
        },
        {
            "identifier": "10.6084/m9.figshare.33314676.v1",
            "identifier_type": "DOI",
            "relation": "IsPartOf",
            "is_linkout": False,
            "title": "Indonesian Open Mathematics Editions inventory baseline",
        },
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--template", type=Path, required=True)
    parser.add_argument("--staging-receipt", type=Path, required=True)
    parser.add_argument("--zenodo-record", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    root = args.root.resolve()
    template = (root / args.template).resolve()
    staging_receipt = (root / args.staging_receipt).resolve()
    output = (root / args.output).resolve()
    if args.zenodo_record <= 0:
        raise SystemExit("Zenodo record id must be positive")
    if output.exists():
        raise SystemExit(f"refusing to overwrite rendered Figshare metadata: {output}")

    receipt = json.loads(staging_receipt.read_text(encoding="utf-8"))
    if receipt.get("status") != "pass" or receipt.get("public_file_count") != 6:
        raise SystemExit("release staging receipt is not a passing six-file boundary")
    files = receipt.get("files", [])
    filenames = [str(item.get("filename")) for item in files]
    if len(filenames) != len(set(filenames)) or set(filenames) != set(PUBLIC_FILES):
        raise SystemExit("release staging receipt has an unexpected public inventory")
    for item in files:
        if int(item.get("bytes") or 0) <= 0:
            raise SystemExit("release staging receipt contains a non-positive byte count")
        if not re.fullmatch(r"[0-9a-f]{64}", str(item.get("sha256") or "")):
            raise SystemExit("release staging receipt contains an invalid SHA-256")
        if not re.fullmatch(r"[0-9a-f]{32}", str(item.get("md5") or "")):
            raise SystemExit("release staging receipt contains an invalid MD5")
    public_payload_bytes = sum(int(item["bytes"]) for item in files)
    if int(receipt.get("public_payload_bytes") or -1) != public_payload_bytes:
        raise SystemExit("release staging receipt total-byte declaration mismatch")
    if public_payload_bytes >= LANE_CAP_BYTES:
        raise SystemExit("linked payload is not below the 500 MB lane cap")

    zenodo_doi = f"10.5281/zenodo.{args.zenodo_record}"
    replacements = {
        "{{ZENODO_RECORD}}": str(args.zenodo_record),
        "{{ZENODO_DOI}}": zenodo_doi,
        "{{PUBLIC_PAYLOAD_BYTES_ID}}": f"{public_payload_bytes:,}".replace(",", "."),
    }
    text = template.read_text(encoding="utf-8")
    for marker in MARKERS:
        if marker not in text:
            raise SystemExit(f"Figshare metadata marker missing: {marker}")
        text = text.replace(marker, replacements[marker])
    if any(marker in text for marker in MARKERS) or "{{" in text or "}}" in text:
        raise SystemExit("unresolved Figshare metadata markers remain")
    if PRIVATE_LOCATOR.search(text):
        raise SystemExit("private locator detected in rendered Figshare metadata")

    payload = json.loads(text)
    title = str(payload.get("title") or "")
    description = str(payload.get("description") or "")
    pdf_url = f"https://zenodo.org/records/{args.zenodo_record}/files/{PDF_NAME}"
    if "TTP" in title + description or "Translation and Transcription Project" in title + description:
        raise SystemExit("organization label leaked into Figshare title or description")
    if MODEL_IDENTIFICATION not in description:
        raise SystemExit("exact model provenance is absent from Figshare description")
    required_phrases = (
        "active_partial",
        "CC0 pada Figshare berlaku hanya untuk metadata/katalog",
        "bukan</strong> berlisensi CC0",
        "CC BY-SA 4.0",
        "Parallel transport sphere2.svg",
        "CC BY-SA 3.0",
        "tidak diunggah atau dilisensikan ulang oleh Figshare",
        "tidak melisensikan ulang satu byte pun",
        "Figshare tidak menyimpan salinan byte PDF tersebut",
        pdf_url,
        zenodo_doi,
        ZENODO_CONCEPT_DOI,
    )
    if any(phrase not in description for phrase in required_phrases):
        raise SystemExit("Figshare rights, scope, provenance, or lineage disclosure is incomplete")
    expected_keys = {
        "title",
        "description",
        "authors",
        "categories",
        "tags",
        "defined_type",
        "license",
        "is_metadata_record",
        "related_materials",
    }
    if set(payload) != expected_keys:
        raise SystemExit("Figshare metadata contains an unexpected or missing top-level field")
    if payload.get("title") != TITLE:
        raise SystemExit("Figshare title mismatch")
    if payload.get("authors") != AUTHORS:
        raise SystemExit("Figshare source-author metadata mismatch")
    if payload.get("categories") != CATEGORIES or payload.get("tags") != TAGS:
        raise SystemExit("Figshare category or tag metadata mismatch")
    if payload.get("license") != 2 or payload.get("defined_type") != "metadata" or payload.get("is_metadata_record") is not False:
        raise SystemExit("Figshare CC0 metadata/link-record license/type boundary mismatch")
    if payload.get("related_materials") != expected_related_materials(zenodo_doi):
        raise SystemExit("Figshare related-material object parity mismatch")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    try:
        output_label = output.relative_to(root).as_posix()
    except ValueError:
        output_label = output.name
    print(
        json.dumps(
            {
                "status": "pass",
                "workflow": "o011-render-figshare-unit06-metadata-v1",
                "output": output_label,
                "bytes": output.stat().st_size,
                "sha256": sha256(output),
                "zenodo_record": args.zenodo_record,
                "zenodo_doi": zenodo_doi,
                "zenodo_concept_doi": ZENODO_CONCEPT_DOI,
                "public_file_count": 6,
                "public_payload_bytes": public_payload_bytes,
                "remote_state_mutated": False,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
