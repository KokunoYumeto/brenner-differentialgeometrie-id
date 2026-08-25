#!/usr/bin/env python3
"""Idempotently publish or recover the exact Unit 6 Zenodo version."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import time
from pathlib import Path
from urllib.parse import quote

import requests

from verify_zenodo_public_unit06 import (
    CONCEPT_DOI,
    CONCEPT_ID,
    CURRENT_RECORD,
    EXPECTED_CREATORS,
    EXPECTED_SOURCE_RELATION,
    PUBLIC_NAMES,
    file_view,
    get_json,
    inventory,
    latest_public_record,
    metadata_projection,
    plain_int,
    project_people,
    project_related,
    record_matches,
    validate_boundary,
    validate_remote_metadata,
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
PUBLICATION_WORKFLOW = "o011-publish-zenodo-unit06-v1"
PREDECESSOR_FILES = {
    "geometri-diferensial-manifold-mulus-hingga-unit-05-id.pdf": (
        4_385_370, "933833841aa30699b788ca4725be863e"
    ),
    "geometri-diferensial-manifold-mulus-brenner-id-unit05-20260822.zip": (
        5_819_316, "dec99c3c1093959eaa2da16e30b75070"
    ),
    "LICENSE.md": (1_958, "c8d442c8a144bd09a8136706b73892a8"),
    "RELEASE_NOTES_20260822.md": (4_515, "88f9602185d94e2a18e6987363531eb1"),
    "FILE_MANIFEST.csv": (1_175, "b47dda952d05e7ceb5263086f32ff9b6"),
    "CHECKSUMS.sha256": (510, "9e0cd472b1ca5dcf120a3d3c07e9d96e"),
}


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
) -> dict:
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
    if not isinstance(value, dict):
        fail(f"{label} returned a non-object JSON body")
    return value


def validate_predecessor(record: dict) -> None:
    metadata = record.get("metadata")
    if (
        record.get("id") != CURRENT_RECORD
        or str(record.get("conceptrecid")) != CONCEPT_ID
        or record.get("doi") != CURRENT_DOI
        or record.get("conceptdoi") != CONCEPT_DOI
        or not isinstance(metadata, dict)
        or metadata.get("title") != CURRENT_TITLE
        or metadata.get("version") != CURRENT_VERSION
        or metadata.get("publication_date") != "2026-08-22"
        or metadata.get("language") != "ind"
        or metadata.get("access_right") != "open"
        or not isinstance(metadata.get("license"), dict)
        or metadata["license"].get("id") != "other-open"
        or project_people(
            metadata.get("creators"), ("name", "affiliation", "orcid", "gnd")
        ) != EXPECTED_CREATORS
        or project_related(metadata.get("related_identifiers")) != EXPECTED_SOURCE_RELATION
    ):
        fail("CURRENT_RECORD is not the exact expected Unit 5 predecessor")
    _, files, _ = inventory(record.get("files"))
    if {name: (item[1], item[2]) for name, item in files.items()} != PREDECESSOR_FILES:
        fail("CURRENT_RECORD files do not match the exact expected predecessor")


def inspect_lineage(
    session: requests.Session, expected: dict, local: dict
) -> tuple[str, dict, dict]:
    current = get_json(
        session, f"https://zenodo.org/api/records/{CURRENT_RECORD}",
        "anonymous CURRENT_RECORD read",
    )
    validate_predecessor(current)
    latest, latest_url = latest_public_record(session, current)
    proof = {
        "predecessor_record_id": CURRENT_RECORD,
        "authoritative_latest_record_id": latest["id"],
        "latest_link": latest_url,
        "current_record_was_concept_latest": latest["id"] == CURRENT_RECORD,
    }
    if latest["id"] == CURRENT_RECORD:
        if latest.get("doi") != CURRENT_DOI:
            fail("CURRENT_RECORD latest proof returned the wrong DOI")
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
        fail("multiple exact Unit 6 public versions exist; refusing a duplicate")
    fail("CURRENT_RECORD is not concept latest and no exact Unit 6 version exists")


def validate_auth_predecessor(deposition: dict) -> None:
    metadata = deposition.get("metadata")
    if (
        deposition.get("id") != CURRENT_RECORD
        or str(deposition.get("conceptrecid")) != CONCEPT_ID
        or deposition.get("submitted") is not True
        or deposition.get("state") != "done"
        or not isinstance(metadata, dict)
        or metadata.get("title") != CURRENT_TITLE
        or metadata.get("version") != CURRENT_VERSION
    ):
        fail("authenticated CURRENT_RECORD is not the exact published predecessor")
    _, files, _ = inventory(deposition.get("files"))
    if {name: (item[1], item[2]) for name, item in files.items()} != PREDECESSOR_FILES:
        fail("authenticated CURRENT_RECORD file identity mismatch")


def latest_draft(
    session: requests.Session, current: dict
) -> tuple[dict, str] | None:
    links = current.get("links")
    if not isinstance(links, dict) or not links.get("latest_draft"):
        return None
    url = zenodo_url(links["latest_draft"], "/api/deposit/depositions/")
    try:
        response = session.get(url, timeout=60)
    except requests.RequestException:
        fail("latest_draft lookup failed before a response was received")
    if response.status_code == 404:
        return None
    if response.status_code != 200:
        fail(f"latest_draft lookup failed: HTTP {response.status_code}")
    try:
        draft = response.json()
    except ValueError:
        fail("latest_draft lookup returned malformed JSON")
    if not isinstance(draft, dict):
        fail("latest_draft lookup returned a non-object JSON body")
    # Zenodo's published-deposition representation can expose a `latest_draft`
    # link that resolves back to the submitted record itself.  That is not an
    # unpublished draft; treat it as no draft so the exact predecessor path
    # can create the next version instead of failing closed on a false draft.
    if (
        draft.get("submitted") is True
        or draft.get("state") == "done"
        or draft.get("id") == CURRENT_RECORD
    ):
        return None
    return draft, url


def validate_draft(draft: dict, current: dict, expected: dict, local: dict) -> str:
    draft_id = draft.get("id")
    if (
        not plain_int(draft_id) or draft_id <= 0 or draft_id == CURRENT_RECORD
        or str(draft.get("conceptrecid")) != CONCEPT_ID
        or draft.get("submitted") is not False or draft.get("state") == "done"
    ):
        fail("latest_draft is not an unpublished draft in the expected concept")
    order, files, _ = inventory(draft.get("files"))
    draft_metadata = metadata_projection(draft.get("metadata"), public=False)
    current_metadata = metadata_projection(current.get("metadata"), public=False)
    target_metadata = metadata_projection(expected, public=False)
    predecessor = {
        name: (name, value[0], value[1]) for name, value in PREDECESSOR_FILES.items()
    }
    target = {
        name: (name, local[name]["bytes"], local[name]["md5"]) for name in PUBLIC_NAMES
    }
    if draft_metadata == current_metadata:
        if files != predecessor:
            fail("inherited latest_draft is not a pristine CURRENT_RECORD clone")
        return "pristine_predecessor_clone"
    if draft_metadata != target_metadata:
        fail("latest_draft metadata matches neither CURRENT_RECORD nor exact Unit 6")
    for name, item in files.items():
        if item != predecessor.get(name) and item != target.get(name):
            fail(f"latest_draft contains an unrelated or changed file: {name}")
    return "matching_unit06_draft"


def bind_latest_draft(
    session: requests.Session, current_url: str, draft_id: int
) -> dict:
    current = auth_json(
        session, "GET", current_url, (200,), "CURRENT_RECORD refresh", 60
    )
    selected = latest_draft(session, current)
    if selected is None or selected[0].get("id") != draft_id:
        fail("selected draft is no longer CURRENT_RECORD's latest_draft")
    return selected[0]


def prepare_draft(
    session: requests.Session, draft_url: str, payload: dict, expected: dict, local: dict
) -> tuple[dict, dict]:
    draft = auth_json(
        session, "PUT", draft_url, (200,), "Unit 6 metadata update", 60,
        headers={"Content-Type": "application/json"}, json=payload,
    )
    validate_remote_metadata(draft.get("metadata"), expected, public=False, label="Unit 6 draft")
    links = draft.get("links")
    if not isinstance(links, dict) or not links.get("bucket"):
        fail("Unit 6 draft omitted its upload bucket")
    bucket = zenodo_url(links["bucket"], "/api/files/")
    raw_files = draft.get("files")
    inventory(raw_files)
    assert isinstance(raw_files, list)
    for item in raw_files:
        file_id = item.get("id")
        if not file_id:
            fail("draft file selected for exact replacement has no id")
        delete_url = zenodo_url(
            f"{draft_url}/files/{quote(str(file_id), safe='')}",
            "/api/deposit/depositions/",
        )
        try:
            response = session.delete(delete_url, timeout=60)
        except requests.RequestException:
            fail("draft file replacement failed before a response was received")
        if response.status_code not in (200, 202, 204):
            fail(f"draft file replacement failed: HTTP {response.status_code}")
    uploads = []
    for name in PUBLIC_NAMES:
        upload_url = zenodo_url(
            f"{bucket.rstrip('/')}/{quote(name, safe='')}", "/api/files/"
        )
        try:
            with local[name]["path"].open("rb") as stream:
                uploaded = auth_json(
                    session, "PUT", upload_url, (200, 201), f"upload {name}", 300,
                    data=stream,
                )
        except OSError:
            fail(f"unable to reopen local upload file: {name}")
        if file_view(uploaded) != (name, local[name]["bytes"], local[name]["md5"]):
            fail(f"upload response identity mismatch: {name}")
        uploads.append({"name": name, "status": "uploaded_exact"})
    draft = auth_json(
        session, "GET", draft_url, (200,), "Unit 6 draft verification", 60
    )
    validate_remote_metadata(draft.get("metadata"), expected, public=False, label="Unit 6 draft")
    order, files, _ = inventory(draft.get("files"))
    if len(order) != 6 or set(files) != set(PUBLIC_NAMES) or any(
        files[name] != (name, local[name]["bytes"], local[name]["md5"])
        for name in PUBLIC_NAMES
    ):
        fail("Unit 6 draft six-file identity mismatch")
    return draft, {
        "uploads": uploads, "draft_api_file_order": order,
        "draft_api_preserved_intended_order": order == list(PUBLIC_NAMES),
    }


def write_result(path: Path, result: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(result, stream, ensure_ascii=True, indent=2, sort_keys=True)
            stream.write("\n")
    except FileExistsError:
        fail(f"refusing to overwrite Zenodo publication receipt: {path}")
    except OSError:
        fail("unable to write Zenodo publication receipt")


def finalize(
    receipt: Path,
    session: requests.Session,
    record: dict,
    expected: dict,
    local: dict,
    evidence: dict,
    proof: dict,
    action: str,
    authentication_used: bool,
    draft: dict | None = None,
) -> None:
    files, order_proof = verify_public_record(session, record, expected, local, evidence)
    record_id = record["id"]
    result = {
        "schema_version": 1, "workflow": PUBLICATION_WORKFLOW, "status": "pass",
        "publication_action": action,
        "verified_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "record_id": record_id, "concept_record_id": int(CONCEPT_ID),
        "doi": record.get("doi"), "concept_doi": record.get("conceptdoi"),
        "record_url": f"https://zenodo.org/records/{record_id}",
        "api_url": f"https://zenodo.org/api/records/{record_id}",
        "authentication_used_for_publication_path": authentication_used,
        "authentication_used_for_public_readback": False,
        "lineage_proof": proof, "reader_first_proof": order_proof, "files": files,
    }
    if draft is not None:
        result["draft"] = draft
    write_result(receipt, result)
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))


def poll_exact(
    session: requests.Session, record_id: int | None, expected: dict, local: dict
) -> tuple[dict, dict] | None:
    for _ in range(12):
        if record_id is not None:
            try:
                candidate = get_json(
                    session, f"https://zenodo.org/api/records/{record_id}",
                    "anonymous post-publication read",
                )
            except SystemExit:
                candidate = {}
            if candidate and record_matches(candidate, expected, local):
                _, _, proof = inspect_lineage(session, expected, local)
                return candidate, proof
        try:
            state, candidate, proof = inspect_lineage(session, expected, local)
        except SystemExit:
            state, candidate, proof = "pending", {}, {}
        if state == "exact_release":
            return candidate, proof
        time.sleep(2)
    return None


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Publish Unit 6 only from exact concept-latest CURRENT_RECORD, resuming a "
            "matching latest_draft or recovering an exact existing publication."
        )
    )
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--token-file", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--staging-receipt", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    receipt = (root / args.receipt).resolve()
    if receipt.exists():
        fail(f"refusing to overwrite Zenodo publication receipt: {receipt}")
    expected, local, evidence = validate_boundary(
        root, (root / args.metadata).resolve(), (root / args.staging_receipt).resolve()
    )
    public = requests.Session(); public.trust_env = False
    state, record, proof = inspect_lineage(public, expected, local)
    if state == "exact_release":
        finalize(
            receipt, public, record, expected, local, evidence, proof,
            "recovered_existing_exact_publication", False,
        )
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
    auth.headers.update({"Authorization": f"Bearer {token}"})
    del token
    current_url = f"https://zenodo.org/api/deposit/depositions/{CURRENT_RECORD}"
    current = auth_json(auth, "GET", current_url, (200,), "CURRENT_RECORD read", 60)
    validate_auth_predecessor(current)

    race_state, race_record, race_proof = inspect_lineage(public, expected, local)
    if race_state == "exact_release":
        finalize(
            receipt, public, race_record, expected, local, evidence, race_proof,
            "recovered_existing_exact_publication", True,
        )
        return
    if race_state != "predecessor_latest":
        fail("CURRENT_RECORD lost concept-latest status before draft selection")

    selected = latest_draft(auth, current)
    if selected is None:
        created = auth_json(
            auth, "POST", f"{current_url}/actions/newversion", (200, 201, 202),
            "new-version creation", 120,
        )
        if created.get("submitted") is False:
            draft = created
            draft_url = zenodo_url(
                (draft.get("links") or {}).get("self"), "/api/deposit/depositions/"
            )
        else:
            draft_url = zenodo_url(
                (created.get("links") or {}).get("latest_draft"),
                "/api/deposit/depositions/",
            )
            draft = auth_json(auth, "GET", draft_url, (200,), "new draft read", 60)
        origin = "created_from_exact_predecessor"
    else:
        draft, draft_url = selected
        origin = "resumed_existing_latest_draft"
    mode = validate_draft(draft, current, expected, local)
    draft_id = draft["id"]
    bind_latest_draft(auth, current_url, draft_id)
    draft, upload_details = prepare_draft(
        auth, draft_url, {"metadata": expected}, expected, local
    )
    bind_latest_draft(auth, current_url, draft_id)
    draft_receipt = {
        "id": draft_id, "origin": origin, "resume_mode": mode, **upload_details,
    }

    pre_state, pre_record, pre_proof = inspect_lineage(public, expected, local)
    if pre_state == "exact_release":
        finalize(
            receipt, public, pre_record, expected, local, evidence, pre_proof,
            "recovered_concurrent_exact_publication", True, draft_receipt,
        )
        return
    if pre_state != "predecessor_latest":
        fail("CURRENT_RECORD lost concept-latest status before publication")

    publish_url = zenodo_url(f"{draft_url}/actions/publish", "/api/deposit/depositions/")
    try:
        response = auth.post(publish_url, timeout=120)
    except requests.RequestException:
        response = None
    record_id = None
    if response is not None and response.status_code in (200, 201, 202):
        try:
            body = response.json()
        except ValueError:
            body = {}
        if isinstance(body, dict):
            candidate = body.get("record_id") or body.get("id")
            if plain_int(candidate) and candidate > 0:
                record_id = candidate
    recovered = poll_exact(public, record_id, expected, local)
    if recovered is None:
        status = "no response" if response is None else f"HTTP {response.status_code}"
        fail(
            f"publish outcome was {status}, and no exact public Unit 6 version was "
            "visible; rerun this script to recover before any further publication"
        )
    published, final_proof = recovered
    finalize(
        receipt, public, published, expected, local, evidence, final_proof,
        "published_new_version", True, draft_receipt,
    )


if __name__ == "__main__":
    main()
