"""Publish Unit 6 through Zenodo's current InvenioRDM version API.

The older ``deposit/depositions`` endpoint is still visible on Zenodo, but its
new-version action now rejects this lineage.  This bounded publisher uses the
documented ``records/{id}/versions`` and draft-file endpoints, and refuses to
create a second concept or to publish a non-exact payload.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import time
from pathlib import Path
from urllib.parse import quote

import requests

from verify_zenodo_public_unit06 import (
    CONCEPT_DOI,
    CONCEPT_ID,
    CURRENT_RECORD,
    EXPECTED_CREATORS,
    EXPECTED_KEYWORDS,
    EXPECTED_SOURCE_RELATION,
    PUBLIC_NAMES,
    file_view,
    get_json,
    inventory,
    latest_public_record,
    plain_int,
    record_matches,
    validate_boundary,
    verify_public_record,
    versions,
    zenodo_url,
)


CURRENT_DOI = "10.5281/zenodo.22060387"
CURRENT_TITLE = (
    "Geometri Diferensial dan Manifold Mulus — Edisi Bahasa Indonesia "
    "(Batas Unit 05)"
)
CURRENT_VERSION = "2026.08.22-unit05-r2"
TARGET_VERSION = "2026.08.22-unit06"
TARGET_TITLE = (
    "Geometri Diferensial dan Manifold Mulus — Edisi Bahasa Indonesia "
    "(Batas Unit 06)"
)
HUB_URL = "https://doi.org/10.5281/zenodo.22059999"
API_MEDIA = "application/vnd.inveniordm.v1+json"
WORKFLOW = "o011-publish-zenodo-unit06-rdm-v1"
PDF_NAME = PUBLIC_NAMES[0]


def fail(message: str) -> None:
    raise SystemExit(message)


def auth_json(
    session: requests.Session,
    method: str,
    url: str,
    statuses: tuple[int, ...],
    label: str,
    timeout: int,
    **kwargs: object,
) -> dict | list:
    zenodo_url(url, "/api/")
    try:
        response = session.request(method, url, timeout=timeout, **kwargs)
    except requests.RequestException:
        fail(f"{label} failed before a response was received")
    if response.status_code not in statuses:
        fail(f"{label} failed: HTTP {response.status_code}")
    try:
        value = response.json()
    except ValueError:
        fail(f"{label} returned malformed JSON")
    if not isinstance(value, (dict, list)):
        fail(f"{label} returned an invalid JSON value")
    return value


def auth_status(
    session: requests.Session,
    method: str,
    url: str,
    statuses: tuple[int, ...],
    label: str,
    timeout: int,
    **kwargs: object,
) -> int:
    """Run an authenticated request whose successful response may be empty.

    Invenio's draft-file DELETE endpoint is documented to return 204 No
    Content.  Do not force that successful response through ``response.json``.
    """
    zenodo_url(url, "/api/")
    try:
        response = session.request(method, url, timeout=timeout, **kwargs)
    except requests.RequestException:
        fail(f"{label} failed before a response was received")
    if response.status_code not in statuses:
        fail(f"{label} failed: HTTP {response.status_code}")
    return response.status_code


def record_id_int(value: object) -> int | None:
    """Normalize canonical API IDs, which may be JSON numbers or strings."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return None


def expected_legacy_predecessor(record: dict) -> None:
    metadata = record.get("metadata")
    if (
        record.get("id") != CURRENT_RECORD
        or str(record.get("conceptrecid")) != CONCEPT_ID
        or record.get("doi") != CURRENT_DOI
        or record.get("conceptdoi") != CONCEPT_DOI
        or not isinstance(metadata, dict)
        or metadata.get("title") != CURRENT_TITLE
        or metadata.get("version") != CURRENT_VERSION
    ):
        fail("the exact Unit 5 predecessor is not the current Zenodo record")


def inspect_public_lineage(
    session: requests.Session, expected: dict, local: dict
) -> tuple[str, dict, dict]:
    current = get_json(
        session, f"https://zenodo.org/api/records/{CURRENT_RECORD}",
        "anonymous CURRENT_RECORD read",
    )
    expected_legacy_predecessor(current)
    latest, latest_url = latest_public_record(session, current)
    proof = {
        "predecessor_record_id": CURRENT_RECORD,
        "authoritative_latest_record_id": latest["id"],
        "latest_link": latest_url,
        "current_record_was_concept_latest": latest["id"] == CURRENT_RECORD,
    }
    if latest["id"] == CURRENT_RECORD:
        return "predecessor_latest", current, proof
    if record_matches(latest, expected, local):
        proof["exact_release_is_latest"] = True
        return "exact_release", latest, proof
    matches = {
        item["id"]: item
        for item in versions(session, current)
        if record_matches(item, expected, local)
    }
    if len(matches) == 1:
        found = next(iter(matches.values()))
        proof["exact_release_record_id"] = found["id"]
        proof["exact_release_is_latest"] = found["id"] == latest["id"]
        return "exact_release", found, proof
    if len(matches) > 1:
        fail("multiple exact Unit 6 public versions exist; refusing duplication")
    fail("predecessor is no longer concept-latest and no exact Unit 6 exists")


def modern_metadata(expected: dict) -> dict:
    source = expected["related_identifiers"][0]
    return {
        "resource_type": {"id": "publication-book"},
        "title": expected["title"],
        "publisher": "Zenodo",
        "publication_date": expected["publication_date"],
        "description": expected["description"],
        "creators": [{
            "person_or_org": {
                "type": "personal", "name": "Brenner, Holger",
                "given_name": "Holger", "family_name": "Brenner",
            },
        }],
        "contributors": [
            {
                "person_or_org": {"type": "organizational", "name": "TTP"},
                "role": {"id": "other"},
            },
            {
                "person_or_org": {
                    "type": "organizational",
                    "name": "Codex (OpenAI), at the user's direction",
                },
                "role": {"id": "other"},
            },
        ],
        "subjects": [{"subject": item} for item in expected["keywords"]],
        "languages": [{"id": expected["language"]}],
        "rights": [{"id": expected["license"]}],
        "related_identifiers": [{
            "identifier": source["identifier"],
            "scheme": "url",
            "relation_type": {"id": "isderivedfrom"},
            "resource_type": {"id": "publication-book"},
        }],
        "version": expected["version"],
    }


def canonical_entries(value: object) -> dict[str, dict]:
    if not isinstance(value, dict):
        fail("draft files representation is malformed")
    entries = value.get("entries")
    if not isinstance(entries, dict) or any(not isinstance(v, dict) for v in entries.values()):
        fail("draft file entries are malformed")
    return entries


def md5(path: Path) -> str:
    h = hashlib.md5()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def validate_canonical_draft(
    draft: dict, modern: dict, local: dict
) -> dict[str, dict]:
    if (
        draft.get("is_draft") is not True
        or draft.get("is_published") is not False
        or draft.get("status") != "new_version_draft"
    ):
        fail("selected Zenodo object is not an unpublished new-version draft")
    parent = draft.get("parent")
    if not isinstance(parent, dict) or str(parent.get("id")) != CONCEPT_ID:
        fail("selected draft is not in the expected concept")
    if draft.get("errors"):
        fail("Zenodo draft contains validation errors")
    metadata = draft.get("metadata")
    if not isinstance(metadata, dict):
        fail("Zenodo draft omitted canonical metadata")
    # Compare only fields which the API promises to echo; vocabulary labels are
    # server-generated and are deliberately not copied into the local payload.
    if (
        metadata.get("title") != modern["title"]
        or metadata.get("publisher") != "Zenodo"
        or metadata.get("publication_date") != modern["publication_date"]
        or metadata.get("description") != modern["description"]
        or metadata.get("version") != modern["version"]
        or metadata.get("resource_type", {}).get("id") != "publication-book"
        or metadata.get("languages", [{}])[0].get("id") != "ind"
        or metadata.get("rights", [{}])[0].get("id") != "other-open"
    ):
        fail("Zenodo draft metadata does not match the exact Unit 6 target")
    creators = metadata.get("creators")
    if not isinstance(creators, list) or len(creators) != 1:
        fail("Zenodo draft creator closure is malformed")
    creator_name = (creators[0].get("person_or_org") or {}).get("name")
    if creator_name != "Brenner, Holger":
        fail("Zenodo draft creator identity mismatch")
    contributors = metadata.get("contributors")
    if not isinstance(contributors, list) or len(contributors) != 2:
        fail("Zenodo draft contributor closure is malformed")
    names = [((item.get("person_or_org") or {}).get("name")) for item in contributors]
    if names != ["TTP", "Codex (OpenAI), at the user's direction"]:
        fail("Zenodo draft contributor identity mismatch")
    ttp = contributors[0]
    if (ttp.get("person_or_org") or {}).get("type") != "organizational":
        fail("TTP is not represented as an organization")
    if "TTP" in json.dumps({k: v for k, v in metadata.items() if k != "contributors"}, ensure_ascii=False):
        fail("TTP leaked outside the contributor field")
    entries = canonical_entries(draft.get("files"))
    target = {
        name: (name, local[name]["bytes"], local[name]["md5"])
        for name in PUBLIC_NAMES
    }
    for name, item in entries.items():
        size = item.get("size")
        checksum = str(item.get("checksum") or "")
        if name in target and (name, size, checksum.removeprefix("md5:")) != target[name]:
            fail(f"Zenodo draft file identity mismatch: {name}")
    return entries


def draft_listing(session: requests.Session) -> list[dict]:
    value = auth_json(
        session, "GET",
        "https://zenodo.org/api/user/records?q=is_published:false&size=100&page=1",
        (200,), "authenticated draft listing", 60,
    )
    hits = value.get("hits", {}).get("hits") if isinstance(value, dict) else None
    if not isinstance(hits, list):
        fail("authenticated draft listing schema mismatch")
    result = []
    for item in hits:
        if not isinstance(item, dict) or item.get("is_published") is not False:
            continue
        if item.get("status") != "new_version_draft":
            continue
        versions_info = item.get("versions")
        if isinstance(versions_info, dict) and versions_info.get("index") is not None:
            try:
                if int(versions_info["index"]) <= 1:
                    continue
            except (TypeError, ValueError):
                continue
        parent = item.get("parent")
        if isinstance(parent, dict) and str(parent.get("id")) == CONCEPT_ID:
            result.append(item)
    return result


def upload_exact(
    session: requests.Session, draft_id: int, root: Path, local: dict[str, dict]
) -> list[dict]:
    base = f"https://zenodo.org/api/records/{draft_id}/draft/files"
    # Zenodo's file-list endpoint still emits the legacy array serializer even
    # when the draft endpoint is requested with the canonical media type.  Read
    # the canonical ``files.entries`` from the draft resource itself.
    draft = auth_json(
        session, "GET", f"https://zenodo.org/api/records/{draft_id}/draft",
        (200,), "draft file list", 60,
    )
    if not isinstance(draft, dict):
        fail("draft file list returned malformed JSON")
    entries = canonical_entries(draft.get("files"))
    target = {
        name: (local[name]["bytes"], local[name]["md5"]) for name in PUBLIC_NAMES
    }
    exact = len(entries) == 6 and all(
        name in entries
        and entries[name].get("size") == target[name][0]
        and str(entries[name].get("checksum", "")).removeprefix("md5:") == target[name][1]
        for name in PUBLIC_NAMES
    )
    if exact:
        return [{"name": name, "status": "already_exact"} for name in PUBLIC_NAMES]
    for name in list(entries):
        url = f"{base}/{quote(name, safe='')}"
        auth_status(session, "DELETE", url, (200, 204), f"delete old draft file {name}", 60)
    initialized = auth_json(
        session, "POST", base, (200, 201), "draft file initialization", 120,
        json=[{"key": name} for name in PUBLIC_NAMES],
        headers={"Content-Type": "application/json", "Accept": API_MEDIA},
    )
    del initialized
    uploads = []
    for name in PUBLIC_NAMES:
        content = f"{base}/{quote(name, safe='')}/content"
        try:
            with local[name]["path"].open("rb") as stream:
                response = session.put(
                    content, data=stream, timeout=300,
                    headers={"Content-Type": "application/octet-stream", "Accept": API_MEDIA},
                )
        except (OSError, requests.RequestException):
            fail(f"upload failed before a response was received: {name}")
        if response.status_code not in (200, 201):
            fail(f"upload failed: HTTP {response.status_code}")
        committed = auth_json(
            session, "POST", f"{base}/{quote(name, safe='')}/commit",
            (200, 201), f"commit {name}", 120,
        )
        if not isinstance(committed, dict):
            fail(f"commit response malformed: {name}")
        if (
            committed.get("key") != name
            or committed.get("size") != local[name]["bytes"]
            or str(committed.get("checksum", "")).removeprefix("md5:") != local[name]["md5"]
        ):
            fail(f"commit identity mismatch: {name}")
        uploads.append({"name": name, "status": "uploaded_exact"})
    return uploads


def ttp_html_proof(session: requests.Session, record_id: int) -> dict:
    url = f"https://zenodo.org/records/{record_id}"
    zenodo_url(url, "/")
    try:
        response = session.get(url, timeout=60)
    except requests.RequestException:
        return {"landing_page_read": False}
    if response.status_code != 200:
        return {"landing_page_read": False, "http_status": response.status_code}
    text = response.text
    anchor = 'metadata.contributors.person_or_org.name:%22TTP%22'
    return {
        "landing_page_read": True,
        "ttp_contributor_search_anchor": anchor in text,
        "ttp_anchor_is_clickable": anchor in text,
        "ttp_organization_group_icon": bool(
            re.search(r"TTP.{0,500}group icon|group icon.{0,500}TTP", text, re.I | re.S)
        ),
        "cross_record_hub_reference": HUB_URL,
    }


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(value, stream, ensure_ascii=True, indent=2, sort_keys=True)
            stream.write("\n")
    except FileExistsError:
        fail(f"refusing to overwrite publication transaction receipt: {path}")
    except OSError:
        fail("unable to write publication transaction receipt")


def main() -> None:
    parser = argparse.ArgumentParser(description="Publish Unit 6 via current Zenodo RDM API")
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--token-file", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--staging-receipt", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--draft-id", type=int)
    args = parser.parse_args()
    root = args.root.resolve()
    receipt = (root / args.receipt).resolve()
    if receipt.exists():
        fail(f"refusing to overwrite publication transaction receipt: {receipt}")
    expected, local, evidence = validate_boundary(
        root, (root / args.metadata).resolve(), (root / args.staging_receipt).resolve()
    )
    public = requests.Session(); public.trust_env = False
    state, record, lineage = inspect_public_lineage(public, expected, local)
    if state == "exact_release":
        files, order_proof = verify_public_record(public, record, expected, local, evidence)
        ttp = ttp_html_proof(public, record["id"])
        if not ttp.get("ttp_anchor_is_clickable"):
            fail("public Zenodo organization contributor anchor was not verified")
        write_json(receipt, {
            "schema_version": 1, "workflow": WORKFLOW, "status": "pass",
            "publication_action": "recovered_existing_exact_publication",
            "authentication_used_for_publication_path": False,
            "authentication_used_for_public_readback": False,
            "verified_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "record_id": record["id"], "concept_record_id": int(CONCEPT_ID),
            "doi": record.get("doi"), "concept_doi": CONCEPT_DOI,
            "record_url": f"https://zenodo.org/records/{record['id']}",
            "lineage_proof": lineage, "reader_first_proof": order_proof,
            "ttp_proof": ttp, "files": files,
        })
        return
    if state != "predecessor_latest":
        fail("unexpected public lineage state")
    try:
        token = args.token_file.resolve().read_text(encoding="utf-8-sig").strip()
    except (OSError, UnicodeError):
        fail("unable to read the Zenodo token file")
    if not token or any(character.isspace() for character in token):
        fail("invalid token-file shape")
    auth = requests.Session(); auth.trust_env = False
    auth.headers.update({"Authorization": f"Bearer {token}", "Accept": API_MEDIA,
                         "User-Agent": "O011-unit06-publisher/1.0"})
    del token
    drafts = draft_listing(auth)
    if args.draft_id:
        drafts = [
            item for item in drafts
            if record_id_int(item.get("id")) == args.draft_id
        ]
        if not drafts:
            # A draft may not appear in the first listing after creation; direct
            # read is safe and still bounded to the explicitly supplied ID.
            drafts = [{"id": args.draft_id}]
    if len(drafts) > 1:
        fail("multiple unpublished drafts exist in the O011 concept")
    if drafts:
        draft_id = int(drafts[0]["id"])
        origin = "resumed_existing_new_api_draft"
    else:
        created = auth_json(
            auth, "POST", f"https://zenodo.org/api/records/{CURRENT_RECORD}/versions",
            (201,), "new-version creation", 120,
        )
        if not isinstance(created, dict) or record_id_int(created.get("id")) is None:
            fail("new-version response omitted a draft ID")
        draft_id = record_id_int(created["id"]); origin = "created_new_api_version_draft"
    modern = modern_metadata(expected)
    draft_url = f"https://zenodo.org/api/records/{draft_id}/draft"
    body = {
        "metadata": modern,
        "access": {"record": "public", "files": "public"},
        # The first draft update can run before any files exist.  Zenodo
        # rejects a default preview that does not yet name an uploaded file.
        "files": {"enabled": True},
    }
    updated = auth_json(
        auth, "PUT", draft_url, (200,), "Unit 6 canonical metadata update", 120,
        json=body, headers={"Content-Type": "application/json", "Accept": API_MEDIA},
    )
    if not isinstance(updated, dict):
        fail("canonical metadata update returned malformed JSON")
    uploads = upload_exact(auth, draft_id, root, local)
    final_body = {
        "metadata": modern,
        "access": {"record": "public", "files": "public"},
        "files": {
            "enabled": True,
            "default_preview": PDF_NAME,
            "order": list(PUBLIC_NAMES),
        },
    }
    updated = auth_json(
        auth, "PUT", draft_url, (200,), "Unit 6 final metadata update", 120,
        json=final_body, headers={"Content-Type": "application/json", "Accept": API_MEDIA},
    )
    if not isinstance(updated, dict):
        fail("final metadata update returned malformed JSON")
    draft = auth_json(
        auth, "GET", draft_url, (200,), "Unit 6 draft verification", 60,
    )
    if not isinstance(draft, dict):
        fail("draft verification returned malformed JSON")
    validate_canonical_draft(draft, modern, local)
    # Recheck anonymous lineage immediately before publication.
    pre_state, pre_record, pre_lineage = inspect_public_lineage(public, expected, local)
    if pre_state == "exact_release":
        fail("an exact Unit 6 publication appeared concurrently; refusing duplicate")
    if pre_state != "predecessor_latest":
        fail("predecessor ceased to be concept-latest before publication")
    publish = auth_json(
        auth, "POST", f"{draft_url}/actions/publish", (201, 202),
        "Unit 6 draft publication", 180,
    )
    published_id = record_id_int(publish.get("id")) if isinstance(publish, dict) else None
    if published_id is None:
        published_id = draft_id
    recovered = None
    final_lineage = {}
    for _ in range(20):
        try:
            candidate = get_json(
                public, f"https://zenodo.org/api/records/{published_id}",
                "anonymous post-publication read",
            )
            if record_matches(candidate, expected, local):
                recovered = candidate
                _, _, final_lineage = inspect_public_lineage(public, expected, local)
                break
        except SystemExit:
            pass
        time.sleep(3)
    if recovered is None:
        fail("publication returned but exact public Unit 6 bytes were not visible")
    files, order_proof = verify_public_record(public, recovered, expected, local, evidence)
    ttp = ttp_html_proof(public, recovered["id"])
    if not ttp.get("ttp_anchor_is_clickable"):
        fail("public Zenodo TTP contributor anchor was not verified")
    write_json(receipt, {
        "schema_version": 1, "workflow": WORKFLOW, "status": "pass",
        "publication_action": "published_new_version",
        "authentication_used_for_publication_path": True,
        "authentication_used_for_public_readback": False,
        "verified_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "record_id": recovered["id"], "concept_record_id": int(CONCEPT_ID),
        "doi": recovered.get("doi"), "concept_doi": CONCEPT_DOI,
        "record_url": f"https://zenodo.org/records/{recovered['id']}",
        "api_url": f"https://zenodo.org/api/records/{recovered['id']}",
        "lineage_proof": final_lineage or pre_lineage,
        "draft": {"id": draft_id, "origin": origin, "uploads": uploads},
        "reader_first_proof": order_proof, "ttp_proof": ttp, "files": files,
    })
    print(json.dumps({"status": "pass", "record_id": recovered["id"], "doi": recovered.get("doi")}, sort_keys=True))


if __name__ == "__main__":
    main()
