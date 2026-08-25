#!/usr/bin/env python3
"""Safely publish or recover the Unit 6 Figshare metadata/link revision."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import time
from pathlib import Path
from urllib.parse import quote, unquote, urljoin

import requests


FIGSHARE_BASE = "https://api.figshare.com/v2"
ZENODO_API = "https://zenodo.org/api/records"
ZENODO_WEB = "https://zenodo.org/records"
ARTICLE_ID = 33314790
PROJECT_ID = 280296
COLLECTION_ID = 8668413
PREVIOUS_ZENODO_RECORD = 22060387
ZENODO_CONCEPT_ID = 22059977
ZENODO_CONCEPT_DOI = "10.5281/zenodo.22059977"
DEFAULT_PREDECESSOR_VERSION = 2
CC0_LICENSE_ID = 2
PROJECT_CAP_BYTES = 20_000_000_000
LANE_CAP_BYTES = 500_000_000
PAGE_SIZE = 100
USER_AGENT = "O011-release-verifier/2.0"
MODEL_IDENTIFICATION = "OpenAI Codex gpt-5.6-sol, Ultra"
SOURCE_PACKAGE_WORKFLOW = "o011-stage-zenodo-unit06-v1"
STAGING_WORKFLOW = "o011-prepare-release-unit06-v1"
ZENODO_VERSION = "2026.08.22-unit06"
ZENODO_LICENSE = "other-open"
ZENODO_CREATORS = ["Brenner, Holger"]
ZENODO_CONTRIBUTORS = [
    {"name": "TTP", "type": "Other"},
    {"name": "Codex (OpenAI), at the user's direction", "type": "Other"},
]
TITLE = "Geometri Diferensial dan Manifold Mulus — Edisi Bahasa Indonesia (batas Unit 06; rilis kerja parsial)"
PDF_NAME = "geometri-diferensial-manifold-mulus-hingga-unit-06-id.pdf"
PREVIOUS_PDF_NAME = "geometri-diferensial-manifold-mulus-hingga-unit-05-id.pdf"
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
LOCAL_FILES = {
    PDF_NAME: "output/pdf/geometri-diferensial-manifold-mulus-hingga-unit-06-id.pdf",
    "geometri-diferensial-manifold-mulus-brenner-id-unit06-20260822.zip":
        "output/zenodo/geometri-diferensial-manifold-mulus-brenner-id-unit06-20260822.zip",
    "LICENSE.md": "qa/unit-06/LICENSE_RELEASE_UNIT06.md",
    "RELEASE_NOTES_20260822.md": "qa/unit-06/RELEASE_NOTES_20260822.md",
    "FILE_MANIFEST.csv": "output/release-unit06/FILE_MANIFEST.csv",
    "CHECKSUMS.sha256": "output/release-unit06/CHECKSUMS.sha256",
}
METADATA_KEYS = {
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
PRIVATE_LOCATOR = re.compile(
    r"[A-Za-z]:[\\/]+Users[\\/]+|(?<!:)/Users/|(?<![:A-Za-z0-9_])/(?:home|srv/home)/[A-Za-z0-9._-]+/",
    re.IGNORECASE,
)


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def request_json(
    session: requests.Session,
    method: str,
    url: str,
    expected: tuple[int, ...],
    operation: str,
    **kwargs: object,
) -> dict | list:
    """Issue an API request without reproducing headers or response bodies."""
    try:
        response = session.request(method, url, **kwargs)
    except requests.RequestException as exc:
        raise SystemExit(f"{operation} failed: {exc.__class__.__name__}") from None
    if response.status_code not in expected:
        raise SystemExit(f"{operation} failed: HTTP {response.status_code}")
    if not response.content:
        return {}
    try:
        payload = response.json()
    except ValueError:
        raise SystemExit(f"{operation} returned non-JSON content") from None
    if not isinstance(payload, (dict, list)):
        raise SystemExit(f"{operation} returned an unexpected JSON shape")
    return payload


def paginated(
    session: requests.Session,
    url: str,
    operation: str,
    headers: dict[str, str] | None = None,
) -> list[dict]:
    rows: list[dict] = []
    for page in range(1, 10_001):
        payload = request_json(
            session,
            "GET",
            url,
            (200,),
            operation,
            headers=headers,
            params={"page": page, "page_size": PAGE_SIZE},
            timeout=60,
        )
        if not isinstance(payload, list) or any(not isinstance(item, dict) for item in payload):
            raise SystemExit(f"{operation} returned an unexpected page shape")
        rows.extend(payload)
        if len(payload) < PAGE_SIZE:
            return rows
    raise SystemExit(f"{operation} exceeded the pagination safety bound")


def digest_path(path: Path) -> tuple[int, str, str]:
    sha256 = hashlib.sha256()
    md5 = hashlib.md5()
    size = 0
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            size += len(block)
            sha256.update(block)
            md5.update(block)
    return size, sha256.hexdigest(), md5.hexdigest()


def sha256_path(path: Path) -> str:
    return digest_path(path)[1]


def remote_identity(session: requests.Session, url: str, label: str) -> tuple[int, str, str]:
    try:
        response = session.get(url, stream=True, timeout=300)
    except requests.RequestException as exc:
        raise SystemExit(f"anonymous linked download failed for {label}: {exc.__class__.__name__}") from None
    if response.status_code != 200:
        raise SystemExit(f"anonymous linked download failed for {label}: HTTP {response.status_code}")
    sha256 = hashlib.sha256()
    md5 = hashlib.md5()
    size = 0
    for block in response.iter_content(1024 * 1024):
        if block:
            size += len(block)
            sha256.update(block)
            md5.update(block)
    return size, sha256.hexdigest(), md5.hexdigest()


def zenodo_url(record_id: int, name: str) -> str:
    return f"{ZENODO_WEB}/{record_id}/files/{quote(name, safe='')}"


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


def scalar(value: object) -> object:
    if isinstance(value, dict):
        for key in ("name", "value", "id"):
            if value.get(key) is not None:
                return value[key]
    return value


def canonical_description(value: object) -> str:
    return re.sub(r"href='([^']*)'", r'href="\1"', str(value or ""))


def canonical_defined_type(value: object) -> str:
    name = str(value or "").strip().lower()
    return "metadata" if name == "online resource" else name


def normalized_related(items: object) -> list[dict[str, object]]:
    if not isinstance(items, list):
        raise SystemExit("Figshare related-material metadata has an unexpected shape")
    normalized: list[dict[str, object]] = []
    for item in items:
        if not isinstance(item, dict):
            raise SystemExit("Figshare related-material metadata has an unexpected entry")
        normalized.append(
            {
                "identifier": unquote(str(item.get("identifier") or "")),
                "identifier_type": str(scalar(item.get("identifier_type")) or ""),
                "relation": str(scalar(item.get("relation")) or ""),
                "is_linkout": bool(item.get("is_linkout")),
                "title": str(item.get("title") or ""),
            }
        )
    return sorted(normalized, key=lambda item: json.dumps(item, ensure_ascii=False, sort_keys=True))


def metadata_projection(value: dict) -> dict:
    defined_type = value.get("defined_type_name") or scalar(value.get("defined_type"))
    license_raw = value.get("license")
    license_value = license_raw.get("value") if isinstance(license_raw, dict) else license_raw
    authors = value.get("authors") or []
    categories = value.get("categories") or []
    tags = value.get("tags") or []
    return {
        "title": value.get("title"),
        "description": canonical_description(value.get("description")),
        "defined_type": canonical_defined_type(defined_type),
        "license": int(license_value or 0),
        "is_metadata_record": (
            value.get("is_metadata_record")
            if isinstance(value.get("is_metadata_record"), bool)
            else None
        ),
        "authors": [
            {"name": str(item.get("full_name") or item.get("name") or "")}
            for item in authors
            if isinstance(item, dict)
        ],
        "categories": sorted(
            int(item.get("id") if isinstance(item, dict) else item)
            for item in categories
        ),
        "tags": sorted(str(item) for item in tags),
        "related_materials": normalized_related(value.get("related_materials") or []),
    }


def validate_metadata(metadata: dict, zenodo_record: int) -> dict:
    if set(metadata) != METADATA_KEYS:
        raise SystemExit("Figshare metadata has an unexpected or missing top-level field")
    zenodo_doi = f"10.5281/zenodo.{zenodo_record}"
    pdf_url = zenodo_url(zenodo_record, PDF_NAME)
    title_description = str(metadata.get("title") or "") + str(metadata.get("description") or "")
    if any(label in title_description for label in ("TTP", "Translation and Transcription Project")):
        raise SystemExit("organization label leaked into Figshare title or description")
    required_phrases = (
        "active_partial",
        "CC0 pada Figshare berlaku hanya untuk metadata/katalog",
        "bukan</strong> berlisensi CC0",
        "tidak melisensikan ulang satu byte pun",
        "Figshare tidak menyimpan salinan byte PDF tersebut",
        "CC BY-SA 4.0",
        "Parallel transport sphere2.svg",
        "CC BY-SA 3.0",
        "tidak diunggah atau dilisensikan ulang oleh Figshare",
        MODEL_IDENTIFICATION,
        pdf_url,
        zenodo_doi,
        ZENODO_CONCEPT_DOI,
    )
    if any(phrase not in title_description for phrase in required_phrases):
        raise SystemExit("Figshare scope, rights, provenance, external-PDF, or lineage disclosure is incomplete")
    if PRIVATE_LOCATOR.search(json.dumps(metadata, ensure_ascii=False)):
        raise SystemExit("private locator detected in Figshare metadata")
    if "{{" in title_description or "}}" in title_description:
        raise SystemExit("unresolved Figshare metadata marker")
    if metadata.get("title") != TITLE or metadata.get("authors") != AUTHORS:
        raise SystemExit("Figshare title or source-author metadata mismatch")
    if metadata.get("categories") != CATEGORIES or metadata.get("tags") != TAGS:
        raise SystemExit("Figshare category or tag metadata mismatch")
    if (
        metadata.get("license") != CC0_LICENSE_ID
        or metadata.get("defined_type") != "metadata"
        or metadata.get("is_metadata_record") is not False
    ):
        raise SystemExit("Figshare CC0 metadata/link-record license/type boundary mismatch")
    if metadata.get("related_materials") != expected_related_materials(zenodo_doi):
        raise SystemExit("Figshare related-material object parity mismatch")
    return metadata_projection(metadata)


def require_staging_provenance(root: Path, staging: dict) -> None:
    binding = staging.get("source_package_receipt") or {}
    privacy = staging.get("source_package_privacy") or {}
    package = staging.get("source_package") or {}
    if (
        staging.get("schema_version") != 1
        or staging.get("workflow") != STAGING_WORKFLOW
        or not isinstance(binding, dict)
        or binding.get("workflow") != SOURCE_PACKAGE_WORKFLOW
        or not isinstance(privacy, dict)
        or privacy.get("private_locator_hits") != 0
        or privacy.get("personal_contributor_wording_hits") != 0
        or privacy.get("credential_like_content_hits") != 0
        or privacy.get("historical_publication_receipts_excluded") is not True
        or not isinstance(package, dict)
        or package.get("reproducible_second_serialization") is not True
    ):
        raise SystemExit("staging receipt lacks the required source-package and zero-hit privacy gates")
    relative = str(binding.get("path") or "")
    bound_path = (root / relative).resolve()
    try:
        bound_path.relative_to(root)
    except ValueError:
        raise SystemExit("source-package receipt binding escapes the release root") from None
    if (
        not bound_path.is_file()
        or int(binding.get("bytes") or -1) != bound_path.stat().st_size
        or not re.fullmatch(r"[0-9a-f]{64}", str(binding.get("sha256") or ""))
        or binding.get("sha256") != sha256_path(bound_path)
    ):
        raise SystemExit("staging source-package receipt binding mismatch")
    try:
        bound = json.loads(bound_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise SystemExit("bound source-package receipt is unreadable") from None
    if (
        not isinstance(bound, dict)
        or bound.get("schema_version") != 1
        or bound.get("workflow") != SOURCE_PACKAGE_WORKFLOW
        or bound.get("status") != "pass"
        or bound.get("privacy_scan") != privacy
        or bound.get("package") != package
    ):
        raise SystemExit("embedded staging provenance differs from its bound source-package receipt")


def load_local_boundary(root: Path, staging_path: Path) -> tuple[dict[str, dict[str, object]], int]:
    staging = json.loads(staging_path.read_text(encoding="utf-8"))
    if not isinstance(staging, dict):
        raise SystemExit("release staging receipt root must be an object")
    require_staging_provenance(root, staging)
    if staging.get("status") != "pass" or staging.get("public_file_count") != len(LOCAL_FILES):
        raise SystemExit("release staging receipt is not a passing six-file boundary")
    rows = staging.get("files") or []
    if not isinstance(rows, list) or any(not isinstance(item, dict) for item in rows):
        raise SystemExit("release staging receipt file inventory has an unexpected shape")
    if len(rows) != len(LOCAL_FILES):
        raise SystemExit("release staging receipt file count mismatch")
    expected: dict[str, tuple[int, str, str]] = {}
    for item in rows:
        name = str(item.get("filename") or "")
        identity = (int(item.get("bytes") or 0), str(item.get("sha256") or ""), str(item.get("md5") or ""))
        if name in expected or identity[0] <= 0:
            raise SystemExit("release staging receipt contains a duplicate file or non-positive byte count")
        if not re.fullmatch(r"[0-9a-f]{64}", identity[1]) or not re.fullmatch(r"[0-9a-f]{32}", identity[2]):
            raise SystemExit("release staging receipt contains an invalid digest")
        expected[name] = identity
    if set(expected) != set(LOCAL_FILES):
        raise SystemExit("release staging receipt inventory mismatch")
    local: dict[str, dict[str, object]] = {}
    for name, relative in LOCAL_FILES.items():
        path = (root / relative).resolve()
        if not path.is_file():
            raise SystemExit(f"release file missing: {relative}")
        identity = digest_path(path)
        if expected[name] != identity:
            raise SystemExit(f"release staging identity mismatch: {name}")
        local[name] = {"bytes": identity[0], "sha256": identity[1], "md5": identity[2], "url": ""}
    lane_bytes = sum(int(item["bytes"]) for item in local.values())
    if int(staging.get("public_payload_bytes") or -1) != lane_bytes:
        raise SystemExit("release staging total-byte declaration mismatch")
    if lane_bytes >= LANE_CAP_BYTES:
        raise SystemExit("bounded linked payload is not below the 500 MB lane cap")
    return local, lane_bytes


def verify_zenodo_boundary(
    session: requests.Session,
    record_id: int,
    local: dict[str, dict[str, object]],
) -> tuple[dict, list[dict[str, object]]]:
    payload = request_json(
        session,
        "GET",
        f"{ZENODO_API}/{record_id}",
        (200,),
        "anonymous Zenodo record preflight",
        timeout=60,
    )
    if not isinstance(payload, dict):
        raise SystemExit("anonymous Zenodo record preflight returned an unexpected shape")
    doi = f"10.5281/zenodo.{record_id}"
    metadata = payload.get("metadata") or {}
    if (
        int(payload.get("id") or 0) != record_id
        or str(payload.get("conceptrecid")) != str(ZENODO_CONCEPT_ID)
        or payload.get("doi") != doi
        or payload.get("conceptdoi") != ZENODO_CONCEPT_DOI
        or not isinstance(metadata, dict)
        or metadata.get("access_right") != "open"
    ):
        raise SystemExit("anonymous Zenodo record/concept/DOI/open-access preflight failed")
    zenodo_title_description = str(metadata.get("title") or "") + str(metadata.get("description") or "")
    creators = [str(item.get("name") or "") for item in metadata.get("creators") or [] if isinstance(item, dict)]
    contributors = [
        {"name": str(item.get("name") or ""), "type": str(item.get("type") or "")}
        for item in metadata.get("contributors") or []
        if isinstance(item, dict)
    ]
    license_value = metadata.get("license") or {}
    if (
        metadata.get("version") != ZENODO_VERSION
        or not isinstance(license_value, dict)
        or license_value.get("id") != ZENODO_LICENSE
        or creators != ZENODO_CREATORS
        or contributors != ZENODO_CONTRIBUTORS
        or MODEL_IDENTIFICATION not in zenodo_title_description
        or "TTP" in zenodo_title_description
        or "Translation and Transcription Project" in zenodo_title_description
    ):
        raise SystemExit("anonymous Zenodo Unit 6 metadata/provenance boundary mismatch")
    files = payload.get("files") or []
    if not isinstance(files, list) or any(not isinstance(item, dict) for item in files):
        raise SystemExit("anonymous Zenodo file inventory has an unexpected shape")
    remote_by_name = {str(item.get("key") or ""): item for item in files}
    if len(remote_by_name) != len(files) or set(remote_by_name) != set(local):
        raise SystemExit("anonymous Zenodo six-file inventory mismatch")
    readback: list[dict[str, object]] = []
    for name, expected in local.items():
        remote = remote_by_name[name]
        checksum = str(remote.get("checksum") or "").lower().removeprefix("md5:")
        if int(remote.get("size") or -1) != int(expected["bytes"]) or checksum != expected["md5"]:
            raise SystemExit(f"anonymous Zenodo API size/MD5 mismatch: {name}")
        url = zenodo_url(record_id, name)
        identity = remote_identity(session, url, name)
        expected_identity = (int(expected["bytes"]), str(expected["sha256"]), str(expected["md5"]))
        if identity != expected_identity:
            raise SystemExit(f"anonymous Zenodo byte/MD5/SHA-256 mismatch: {name}")
        expected["url"] = url
        readback.append({
            "name": name,
            "bytes": identity[0],
            "sha256": identity[1],
            "md5": identity[2],
            "url": url,
            "matches_local_receipt": True,
        })
    return payload, readback


def member_ids(rows: list[dict], label: str) -> set[int]:
    identifiers = [int(item.get("id") or 0) for item in rows]
    if 0 in identifiers or len(identifiers) != len(set(identifiers)):
        raise SystemExit(f"{label} contains an invalid or duplicate article id")
    return set(identifiers)


def public_membership_preflight(session: requests.Session) -> tuple[list[dict], list[dict], dict]:
    project_rows = paginated(
        session,
        f"{FIGSHARE_BASE}/projects/{PROJECT_ID}/articles",
        "anonymous Figshare project-membership preflight",
    )
    collection_rows = paginated(
        session,
        f"{FIGSHARE_BASE}/collections/{COLLECTION_ID}/articles",
        "anonymous Figshare collection-membership preflight",
    )
    if ARTICLE_ID not in member_ids(project_rows, "Figshare project preflight"):
        raise SystemExit("article is not a public member of required Figshare project 280296")
    if ARTICLE_ID not in member_ids(collection_rows, "Figshare collection preflight"):
        raise SystemExit("article is not a public member of required Figshare collection 8668413")
    collection = request_json(
        session,
        "GET",
        f"{FIGSHARE_BASE}/collections/{COLLECTION_ID}",
        (200,),
        "anonymous Figshare collection preflight",
        timeout=60,
    )
    if not isinstance(collection, dict) or int(collection.get("id") or 0) != COLLECTION_ID:
        raise SystemExit("unexpected Figshare collection identity")
    return project_rows, collection_rows, collection


def project_size_proof(
    session: requests.Session,
    lane_bytes: int,
    headers: dict[str, str] | None,
) -> dict[str, object]:
    authenticated = headers is not None
    prefix = "/account" if authenticated else ""
    rows = paginated(
        session,
        f"{FIGSHARE_BASE}{prefix}/projects/{PROJECT_ID}/articles",
        "live Figshare project-size membership read",
        headers,
    )
    ids = member_ids(rows, "live Figshare project-size membership")
    if ARTICLE_ID not in ids:
        raise SystemExit("required article is absent from live Figshare project-size scope")
    total = 0
    file_count = 0
    for article_id in sorted(ids):
        detail = request_json(
            session,
            "GET",
            f"{FIGSHARE_BASE}{prefix}/articles/{article_id}",
            (200,),
            "live Figshare project article-size read",
            headers=headers,
            timeout=60,
        )
        if not isinstance(detail, dict) or int(detail.get("id") or 0) != article_id:
            raise SystemExit("live Figshare project article identity mismatch")
        files = detail.get("files") or []
        if not isinstance(files, list) or any(not isinstance(item, dict) for item in files):
            raise SystemExit("live Figshare project article has an unexpected file shape")
        for item in files:
            raw_size = item.get("size")
            if isinstance(raw_size, bool) or not isinstance(raw_size, int) or raw_size < 0:
                raise SystemExit("live Figshare project file lacks a non-negative integer size")
            total += raw_size
            file_count += 1
    upper_bound = total + lane_bytes
    if upper_bound >= PROJECT_CAP_BYTES:
        raise SystemExit("live bounded Figshare project size is not below 20 GB")
    return {
        "observed_at_utc": utc_now(),
        "scope": "authenticated account project" if authenticated else "anonymous public project",
        "project_id": PROJECT_ID,
        "article_count": len(ids),
        "file_count": file_count,
        "reported_current_file_bytes": total,
        "conservative_unit06_linked_payload_allowance_bytes": lane_bytes,
        "upper_bound_bytes": upper_bound,
        "cap_bytes": PROJECT_CAP_BYTES,
        "below_cap": True,
    }


def exact_file(item: dict, name: str, url: str) -> bool:
    return (
        item.get("name") == name
        and item.get("download_url") == url
        and item.get("is_link_only") is True
        and int(item.get("id") or 0) > 0
    )


def require_predecessor(article: dict, version: int) -> None:
    previous_url = zenodo_url(PREVIOUS_ZENODO_RECORD, PREVIOUS_PDF_NAME)
    related = {str(item.get("identifier") or "") for item in article.get("related_materials") or [] if isinstance(item, dict)}
    files = article.get("files") or []
    expected_doi = f"10.6084/m9.figshare.{ARTICLE_ID}.v{version}"
    if (
        int(article.get("id") or 0) != ARTICLE_ID
        or int(article.get("version") or 0) != version
        or article.get("doi") != expected_doi
        or not article.get("published_date")
        or ZENODO_CONCEPT_DOI not in related
        or len(files) != 1
        or not isinstance(files[0], dict)
        or not exact_file(files[0], PREVIOUS_PDF_NAME, previous_url)
    ):
        raise SystemExit(f"public Figshare article is not the exact version-{version} Unit 5 predecessor")


def target_matches(article: dict, target_version: int, expected_projection: dict, pdf_url: str) -> bool:
    expected_doi = f"10.6084/m9.figshare.{ARTICLE_ID}.v{target_version}"
    files = article.get("files") or []
    try:
        return (
            int(article.get("id") or 0) == ARTICLE_ID
            and int(article.get("version") or 0) == target_version
            and article.get("doi") == expected_doi
            and bool(article.get("published_date"))
            and metadata_projection(article) == expected_projection
            and len(files) == 1
            and isinstance(files[0], dict)
            and exact_file(files[0], PDF_NAME, pdf_url)
        )
    except (SystemExit, TypeError, ValueError):
        return False


def require_target(article: dict, target_version: int, expected_projection: dict, pdf_url: str) -> None:
    if not target_matches(article, target_version, expected_projection, pdf_url):
        raise SystemExit(f"public Figshare article is not the exact Unit 6 version {target_version}")


def account_file_state(article: dict, previous_url: str, pdf_url: str) -> tuple[dict | None, dict | None]:
    files = article.get("files") or []
    if not isinstance(files, list) or any(not isinstance(item, dict) for item in files):
        raise SystemExit("Figshare account article has an unexpected file shape")
    previous: list[dict] = []
    desired: list[dict] = []
    for item in files:
        if exact_file(item, PREVIOUS_PDF_NAME, previous_url):
            previous.append(item)
        elif exact_file(item, PDF_NAME, pdf_url):
            desired.append(item)
        else:
            raise SystemExit("Figshare draft contains an unexpected or inexact file")
    if len(previous) > 1 or len(desired) > 1:
        raise SystemExit("Figshare draft contains a duplicate predecessor or Unit 6 link")
    if not previous and not desired:
        raise SystemExit("Figshare draft contains neither the predecessor nor Unit 6 link")
    return previous[0] if previous else None, desired[0] if desired else None


def resolve_location(location: str) -> str:
    if location.startswith("https://"):
        return location
    if location.startswith("/v2/"):
        return urljoin("https://api.figshare.com", location)
    if location.startswith("/account/"):
        return FIGSHARE_BASE + location
    return urljoin(FIGSHARE_BASE + "/", location)


def verify_public_links(
    session: requests.Session,
    article: dict,
    record_id: int,
    local: dict[str, dict[str, object]],
) -> list[dict[str, object]]:
    public_files = article.get("files") or []
    pdf_url = zenodo_url(record_id, PDF_NAME)
    if len(public_files) != 1 or not isinstance(public_files[0], dict) or not exact_file(public_files[0], PDF_NAME, pdf_url):
        raise SystemExit("anonymous Figshare primary link is not the exact external Zenodo PDF")
    description = str(article.get("description") or "")
    readback: list[dict[str, object]] = []
    for name, expected in local.items():
        url = pdf_url if name == PDF_NAME else zenodo_url(record_id, name)
        if url not in description:
            raise SystemExit(f"exact external Zenodo link missing from public Figshare description: {name}")
        identity = remote_identity(session, public_files[0]["download_url"] if name == PDF_NAME else url, name)
        expected_identity = (int(expected["bytes"]), str(expected["sha256"]), str(expected["md5"]))
        if identity != expected_identity:
            raise SystemExit(f"anonymous Figshare-linked byte/MD5/SHA-256 mismatch: {name}")
        readback.append({
            "name": name,
            "bytes": identity[0],
            "sha256": identity[1],
            "md5": identity[2],
            "download_url": url,
            "figshare_visible_file": name == PDF_NAME,
            "is_external_zenodo_link": True,
            "matches_local_receipt": True,
        })
    return readback


def receipt_identity(value: dict) -> dict:
    return {
        "schema_version": value.get("schema_version"),
        "workflow": value.get("workflow"),
        "status": value.get("status"),
        "article_id": value.get("article_id"),
        "article_doi": value.get("article_doi"),
        "article_version": value.get("article_version"),
        "expected_predecessor_version": value.get("expected_predecessor_version"),
        "article_license": value.get("article_license"),
        "article_defined_type": value.get("article_defined_type"),
        "is_metadata_record": value.get("is_metadata_record"),
        "zenodo_record": value.get("zenodo_record"),
        "zenodo_doi": value.get("zenodo_doi"),
        "zenodo_concept_record_id": value.get("zenodo_concept_record_id"),
        "zenodo_concept_doi": value.get("zenodo_concept_doi"),
        "project_id": value.get("project_id"),
        "collection_id": value.get("collection_id"),
        "lane_linked_bytes": value.get("lane_linked_bytes"),
        "files": [
            {key: item.get(key) for key in ("name", "bytes", "sha256", "md5", "download_url")}
            for item in value.get("files") or []
            if isinstance(item, dict)
        ],
    }


def persist_receipt(path: Path, result: dict) -> str:
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            raise SystemExit("existing Figshare receipt is unreadable; refusing to overwrite it") from None
        if not isinstance(existing, dict) or receipt_identity(existing) != receipt_identity(result):
            raise SystemExit("existing Figshare receipt has a different release identity; refusing to overwrite it")
        return "retained_verified_existing"
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(result, stream, ensure_ascii=True, indent=2, sort_keys=True)
            stream.write("\n")
    except FileExistsError:
        raise SystemExit("Figshare receipt appeared concurrently; rerun to verify it") from None
    return "created"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Publish Unit 6 as exact Figshare metadata/link version 3, or verify an existing exact version without republishing."
    )
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--token-file", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--staging-receipt", type=Path, required=True)
    parser.add_argument("--zenodo-record", type=int, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument(
        "--expected-predecessor-version",
        type=int,
        default=DEFAULT_PREDECESSOR_VERSION,
        help="exact currently public predecessor version (target is this value plus one; default: 2)",
    )
    args = parser.parse_args()
    if args.zenodo_record <= 0 or args.zenodo_record == PREVIOUS_ZENODO_RECORD:
        raise SystemExit("a new Unit 6 Zenodo record id is required")
    if args.expected_predecessor_version <= 0:
        raise SystemExit("expected predecessor version must be positive")
    target_version = args.expected_predecessor_version + 1
    root = args.root.resolve()
    receipt_path = (root / args.receipt).resolve()
    metadata = json.loads((root / args.metadata).resolve().read_text(encoding="utf-8"))
    if not isinstance(metadata, dict):
        raise SystemExit("Figshare metadata root must be an object")
    expected_projection = validate_metadata(metadata, args.zenodo_record)
    local, lane_bytes = load_local_boundary(root, (root / args.staging_receipt).resolve())

    public_session = requests.Session()
    public_session.trust_env = False
    public_session.headers.update({"User-Agent": USER_AGENT})
    # Before any Figshare mutation, prove the Zenodo concept and all six bytes.
    zenodo_record, zenodo_preflight = verify_zenodo_boundary(public_session, args.zenodo_record, local)
    # Also before mutation, prove both required public memberships.
    project_before, collection_before, collection = public_membership_preflight(public_session)
    public_before = request_json(
        public_session,
        "GET",
        f"{FIGSHARE_BASE}/articles/{ARTICLE_ID}",
        (200,),
        "anonymous Figshare article preflight",
        timeout=60,
    )
    if not isinstance(public_before, dict):
        raise SystemExit("anonymous Figshare article preflight returned an unexpected shape")
    pdf_url = zenodo_url(args.zenodo_record, PDF_NAME)
    public_version = int(public_before.get("version") or 0)
    publish_performed = False
    publish_response: dict = {}
    account_size_before: dict[str, object] | None = None

    if public_version == target_version:
        # Exact public target: verify/recover only, never republish.
        require_target(public_before, target_version, expected_projection, pdf_url)
        public_size_after = project_size_proof(public_session, lane_bytes, None)
        final_article = public_before
        mode = "verified_existing_exact_target"
    else:
        if public_version != args.expected_predecessor_version:
            raise SystemExit(
                f"public Figshare version is {public_version}; expected exact predecessor "
                f"{args.expected_predecessor_version} or exact target {target_version}"
            )
        require_predecessor(public_before, args.expected_predecessor_version)
        try:
            token = args.token_file.resolve().read_text(encoding="utf-8-sig").strip()
        except OSError:
            raise SystemExit("unable to read Figshare token file") from None
        if not token or any(character.isspace() for character in token):
            raise SystemExit("invalid token-file shape")
        headers = {"Authorization": f"token {token}", "Accept": "application/json"}
        json_headers = {**headers, "Content-Type": "application/json"}
        account_session = requests.Session()
        account_session.trust_env = False
        account_session.headers.update({"User-Agent": USER_AGENT})
        licenses = request_json(
            account_session,
            "GET",
            f"{FIGSHARE_BASE}/account/licenses",
            (200,),
            "Figshare CC0 license preflight",
            headers=headers,
            timeout=60,
        )
        if not isinstance(licenses, list):
            raise SystemExit("Figshare license preflight returned an unexpected shape")
        available = {int(item.get("value") or 0): str(item.get("name") or "") for item in licenses if isinstance(item, dict)}
        if available.get(CC0_LICENSE_ID) != "CC0":
            raise SystemExit("account CC0 license id is not the verified value 2")
        account_project_rows = paginated(
            account_session,
            f"{FIGSHARE_BASE}/account/projects/{PROJECT_ID}/articles",
            "authenticated Figshare project-membership preflight",
            headers,
        )
        if ARTICLE_ID not in member_ids(account_project_rows, "authenticated Figshare project preflight"):
            raise SystemExit("article is not an account member of required Figshare project 280296")
        account_size_before = project_size_proof(account_session, lane_bytes, headers)
        article_url = f"{FIGSHARE_BASE}/account/articles/{ARTICLE_ID}"
        account_article = request_json(
            account_session,
            "GET",
            article_url,
            (200,),
            "Figshare account article preflight",
            headers=headers,
            timeout=60,
        )
        if not isinstance(account_article, dict) or int(account_article.get("id") or 0) != ARTICLE_ID:
            raise SystemExit("unexpected Figshare account article identity")
        if int(account_article.get("version") or 0) not in {args.expected_predecessor_version, target_version}:
            raise SystemExit("Figshare account draft has an unexpected version")
        related = {
            str(item.get("identifier") or "")
            for item in account_article.get("related_materials") or []
            if isinstance(item, dict)
        }
        if ZENODO_CONCEPT_DOI not in related:
            raise SystemExit("Figshare account article is not bound to the required Zenodo concept")
        account_projection = metadata_projection(account_article)
        predecessor_projection = metadata_projection(public_before)
        if account_projection not in (predecessor_projection, expected_projection):
            raise SystemExit("Figshare account draft metadata is neither the exact predecessor nor exact Unit 6 target")
        # Close the small read race before the first mutating request.
        public_recheck = request_json(
            public_session,
            "GET",
            f"{FIGSHARE_BASE}/articles/{ARTICLE_ID}",
            (200,),
            "anonymous Figshare version recheck",
            timeout=60,
        )
        if not isinstance(public_recheck, dict):
            raise SystemExit("anonymous Figshare version recheck returned an unexpected shape")
        if int(public_recheck.get("version") or 0) == target_version:
            require_target(public_recheck, target_version, expected_projection, pdf_url)
            final_article = public_recheck
            mode = "verified_concurrently_published_exact_target"
            public_size_after = project_size_proof(public_session, lane_bytes, None)
        else:
            require_predecessor(public_recheck, args.expected_predecessor_version)
            previous_url = zenodo_url(PREVIOUS_ZENODO_RECORD, PREVIOUS_PDF_NAME)
            predecessor_file, target_file = account_file_state(account_article, previous_url, pdf_url)
            # Prove the new link alongside the old link before any deletion.
            if target_file is None:
                if predecessor_file is None:
                    raise SystemExit("safe link swap cannot start without the exact predecessor")
                created = request_json(
                    account_session,
                    "POST",
                    f"{article_url}/files",
                    (201,),
                    "Figshare Unit 6 link creation",
                    headers=json_headers,
                    json={"link": pdf_url},
                    timeout=120,
                )
                if not isinstance(created, dict) or not str(created.get("location") or ""):
                    raise SystemExit("Figshare Unit 6 link creation omitted its location")
                linked = {}
                for _ in range(10):
                    candidate = request_json(
                        account_session,
                        "GET",
                        resolve_location(str(created["location"])),
                        (200,),
                        "Figshare Unit 6 created-link readback",
                        headers=headers,
                        timeout=60,
                    )
                    if isinstance(candidate, dict) and exact_file(candidate, PDF_NAME, pdf_url):
                        linked = candidate
                        break
                    time.sleep(1)
                if not linked:
                    raise SystemExit("Figshare did not create the exact Unit 6 external link")
                account_article = request_json(
                    account_session,
                    "GET",
                    article_url,
                    (200,),
                    "Figshare dual-link safety readback",
                    headers=headers,
                    timeout=60,
                )
                if not isinstance(account_article, dict):
                    raise SystemExit("Figshare dual-link safety readback returned an unexpected shape")
                predecessor_file, target_file = account_file_state(account_article, previous_url, pdf_url)
                if predecessor_file is None or target_file is None:
                    raise SystemExit("Unit 6 link was not proven alongside the predecessor; refusing deletion")
            if predecessor_file is not None:
                request_json(
                    account_session,
                    "DELETE",
                    f"{article_url}/files/{int(predecessor_file['id'])}",
                    (200, 202, 204),
                    "Figshare predecessor-link removal",
                    headers=headers,
                    timeout=60,
                )
            account_article = request_json(
                account_session,
                "GET",
                article_url,
                (200,),
                "Figshare post-swap file readback",
                headers=headers,
                timeout=60,
            )
            if not isinstance(account_article, dict):
                raise SystemExit("Figshare post-swap file readback returned an unexpected shape")
            predecessor_file, target_file = account_file_state(account_article, previous_url, pdf_url)
            if predecessor_file is not None or target_file is None:
                raise SystemExit("Figshare safe link swap did not converge to one exact Unit 6 link")
            request_json(
                account_session,
                "PUT",
                article_url,
                (200, 205),
                "Figshare Unit 6 metadata update",
                headers=json_headers,
                json=metadata,
                timeout=60,
            )
            request_json(
                account_session,
                "PUT",
                f"{article_url}/authors",
                (200, 205),
                "Figshare Unit 6 author update",
                headers=json_headers,
                json={"authors": metadata["authors"]},
                timeout=60,
            )
            private_detail = request_json(
                account_session,
                "GET",
                article_url,
                (200,),
                "Figshare private Unit 6 parity readback",
                headers=headers,
                timeout=60,
            )
            if not isinstance(private_detail, dict) or metadata_projection(private_detail) != expected_projection:
                raise SystemExit("Figshare private Unit 6 full metadata parity mismatch")
            private_previous, private_target = account_file_state(private_detail, previous_url, pdf_url)
            if private_previous is not None or private_target is None:
                raise SystemExit("Figshare private Unit 6 link parity mismatch")
            public_last_check = request_json(
                public_session,
                "GET",
                f"{FIGSHARE_BASE}/articles/{ARTICLE_ID}",
                (200,),
                "anonymous Figshare last predecessor check",
                timeout=60,
            )
            if not isinstance(public_last_check, dict):
                raise SystemExit("anonymous Figshare last predecessor check returned an unexpected shape")
            require_predecessor(public_last_check, args.expected_predecessor_version)
            published = request_json(
                account_session,
                "POST",
                f"{article_url}/publish",
                (201,),
                "Figshare Unit 6 version publication",
                headers=headers,
                timeout=120,
            )
            publish_response = {
                key: published.get(key)
                for key in ("location", "doi")
                if isinstance(published, dict) and published.get(key)
            }
            publish_performed = True
            final_article = {}
            for _ in range(15):
                candidate = request_json(
                    public_session,
                    "GET",
                    f"{FIGSHARE_BASE}/articles/{ARTICLE_ID}",
                    (200,),
                    "anonymous Figshare Unit 6 convergence read",
                    timeout=60,
                )
                if isinstance(candidate, dict) and int(candidate.get("version") or 0) > target_version:
                    raise SystemExit("Figshare public version advanced beyond the exact Unit 6 target")
                if isinstance(candidate, dict) and target_matches(candidate, target_version, expected_projection, pdf_url):
                    final_article = candidate
                    break
                time.sleep(2)
            if not final_article:
                raise SystemExit(f"anonymous Figshare version {target_version} readback did not converge")
            mode = "published_exact_next_version"
            public_size_after = project_size_proof(public_session, lane_bytes, None)

    # Final anonymous gates cover every linked byte, not only the panel PDF.
    project_after, collection_after, collection_after_detail = public_membership_preflight(public_session)
    require_target(final_article, target_version, expected_projection, pdf_url)
    readback = verify_public_links(public_session, final_article, args.zenodo_record, local)
    result = {
        "schema_version": 2,
        "workflow": "o011-publish-figshare-unit06-linked-reader-v2",
        "status": "pass",
        "verified_at_utc": utc_now(),
        "mode": mode,
        "figshare_mutation_performed": publish_performed,
        "publish_endpoint_called": publish_performed,
        "article_id": ARTICLE_ID,
        "article_doi": final_article.get("doi"),
        "article_url": final_article.get("url_public_html"),
        "article_version": target_version,
        "expected_predecessor_version": args.expected_predecessor_version,
        "article_license": {"value": CC0_LICENSE_ID, "name": "CC0"},
        "article_defined_type": "metadata",
        "is_metadata_record": False,
        "figshare_visible_files": 1,
        "description_companion_links": len(local) - 1,
        "lane_linked_bytes": lane_bytes,
        "lane_cap_bytes": LANE_CAP_BYTES,
        "zenodo_record": args.zenodo_record,
        "zenodo_doi": zenodo_record.get("doi"),
        "zenodo_concept_record_id": ZENODO_CONCEPT_ID,
        "zenodo_concept_doi": ZENODO_CONCEPT_DOI,
        "zenodo_anonymous_preflight_files": zenodo_preflight,
        "project_id": PROJECT_ID,
        "project_members_preflight": len(project_before),
        "project_members_post_publication": len(project_after),
        "project_size_pre_mutation": account_size_before,
        "project_size_post_publication": public_size_after,
        "collection_id": COLLECTION_ID,
        "collection_doi": collection_after_detail.get("doi") or collection.get("doi"),
        "collection_version": collection_after_detail.get("version"),
        "collection_members_preflight": len(collection_before),
        "collection_members_post_publication": len(collection_after),
        "authentication_used_for_public_readback": False,
        "files": readback,
        "publish_response": publish_response,
    }
    result["receipt_action"] = persist_receipt(receipt_path, result)
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))


if __name__ == "__main__":
    main()
