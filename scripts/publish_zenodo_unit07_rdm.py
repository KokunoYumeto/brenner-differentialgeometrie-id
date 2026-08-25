#!/usr/bin/env python3
"""Publish the verified Unit 7 checkpoint as the next version of one Zenodo concept.

The transaction is fail-closed: it never creates a second concept, refuses a
changed predecessor or duplicate exact release, reads the token only at
runtime, uploads the six staged files in reader-first order, and anonymously
re-reads every public byte before writing its sanitized receipt.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import time
from pathlib import Path
from urllib.parse import quote

import httpx


CONCEPT_ID = "22059977"
CONCEPT_DOI = "10.5281/zenodo.22059977"
PREDECESSOR_ID = 22070425
PREDECESSOR_DOI = "10.5281/zenodo.22070425"
API_MEDIA = "application/vnd.inveniordm.v1+json"
MODEL = "OpenAI Codex gpt-5.6-sol, Ultra"
PDF_NAME = "geometri-diferensial-manifold-mulus-hingga-unit-07-id.pdf"


def fail(message: str) -> None:
    raise SystemExit(message)


def digest(path: Path, algorithm: str = "sha256") -> str:
    h = hashlib.new(algorithm)
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def api_json(session: httpx.Client, method: str, url: str, statuses: tuple[int, ...], label: str, **kwargs: object) -> object:
    try:
        response = session.request(method, url, timeout=180, **kwargs)
    except httpx.HTTPError:
        fail(f"{label} failed before a response")
    if response.status_code not in statuses:
        fail(f"{label} failed: HTTP {response.status_code}")
    try:
        return response.json()
    except ValueError:
        fail(f"{label} returned malformed JSON")


def api_status(session: httpx.Client, method: str, url: str, statuses: tuple[int, ...], label: str, **kwargs: object) -> int:
    try:
        response = session.request(method, url, timeout=180, **kwargs)
    except httpx.HTTPError:
        fail(f"{label} failed before a response")
    if response.status_code not in statuses:
        fail(f"{label} failed: HTTP {response.status_code}")
    return response.status_code


def local_payload(root: Path, staging: Path) -> tuple[dict, dict[str, dict], list[str]]:
    stage = json.loads(staging.read_text(encoding="utf-8"))
    if stage.get("status") != "pass":
        fail("release preparation receipt is not passing")
    files = stage.get("files")
    if not isinstance(files, list) or len(files) != 6:
        fail("release preparation does not describe exactly six public files")
    local: dict[str, dict] = {}
    order: list[str] = []
    for item in files:
        if not isinstance(item, dict) or not isinstance(item.get("filename"), str):
            fail("malformed public file entry")
        name = item["filename"]
        path = root / "output/release-unit07" / name
        if not path.is_file():
            fail(f"public file is missing: {name}")
        actual = {"path": path, "bytes": path.stat().st_size, "sha256": digest(path), "md5": digest(path, "md5")}
        if actual["bytes"] != item.get("bytes") or actual["sha256"] != item.get("sha256") or actual["md5"] != item.get("md5"):
            fail(f"local public file identity changed: {name}")
        local[name] = actual; order.append(name)
    if order[0] != PDF_NAME:
        fail("primary reader is not first")
    return stage, local, order


def expected_metadata(metadata_path: Path) -> tuple[dict, dict]:
    payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("metadata"), dict):
        fail("metadata file must contain a metadata object")
    m = payload["metadata"]
    required = {"title", "description", "creators", "contributors", "license", "publication_date", "version", "language", "keywords", "related_identifiers"}
    if set(m) != required:
        fail("Unit 7 metadata schema is not exact")
    if not isinstance(m["description"], str) or MODEL not in m["description"] or "active_partial" not in m["description"]:
        fail("metadata description lacks truthful scope/model disclosure")
    if "TTP" in m["title"] or "TTP" in m["description"] or "Translation and Transcription Project" in json.dumps({k:v for k,v in m.items() if k != "contributors"}, ensure_ascii=False):
        fail("umbrella label leaked outside the contributor field")
    contributors = m["contributors"]
    if not isinstance(contributors, list) or len(contributors) != 2 or sum(1 for x in contributors if x.get("name") == "TTP") != 1:
        fail("metadata must contain exactly one organizational TTP contributor")
    modern = {
        "resource_type": {"id": "publication-book"},
        "title": m["title"], "publisher": "Zenodo", "publication_date": m["publication_date"],
        "description": m["description"], "version": m["version"],
        "creators": [{"person_or_org": {"type": "personal", "name": "Brenner, Holger", "given_name": "Holger", "family_name": "Brenner"}}],
        "contributors": [
            {"person_or_org": {"type": "organizational", "name": "TTP"}, "role": {"id": "other"}},
            {"person_or_org": {"type": "organizational", "name": "Codex (OpenAI), at the user's direction"}, "role": {"id": "other"}},
        ],
        "subjects": [{"subject": str(x)} for x in m["keywords"]],
        "languages": [{"id": m["language"]}], "rights": [{"id": m["license"]}],
        "related_identifiers": [{"identifier": m["related_identifiers"][0]["identifier"], "scheme": "url", "relation_type": {"id": "isderivedfrom"}, "resource_type": {"id": "publication-book"}}],
    }
    if modern["rights"] != [{"id": "other-open"}]:
        fail("mixed component rights must use Other (Open)")
    return m, modern


def projection(record: dict) -> dict:
    metadata = record.get("metadata") or {}
    def people(key: str) -> list[dict]:
        result = []
        for x in metadata.get(key, []) or []:
            person = x.get("person_or_org") or x
            kind = person.get("type")
            if key == "creators" and kind is None: kind = "personal"
            if isinstance(kind, str) and kind.lower() in {"other", "organization", "organizational"}: kind = "organizational"
            result.append({"name": person.get("name"), "type": kind})
        return result
    def ids(key: str, legacy_key: str | None = None) -> list[dict]:
        values = metadata.get(key)
        if values is None and legacy_key:
            values = metadata.get(legacy_key)
        if isinstance(values, (str, dict)):
            values = [values]
        result = []
        for x in values or []:
            if isinstance(x, str): result.append({"id": x})
            else: result.append({"id": x.get("id")})
        return result
    related = []
    for x in metadata.get("related_identifiers", []) or []:
        relation = x.get("relation_type") or x.get("relation") or {}
        resource = x.get("resource_type") or {}
        relation_id = relation if isinstance(relation, str) else relation.get("id")
        resource_id = resource if isinstance(resource, str) else resource.get("id")
        if isinstance(relation_id, str): relation_id = relation_id.lower()
        related.append({"identifier": x.get("identifier"), "scheme": x.get("scheme"), "relation_type": {"id": relation_id}, "resource_type": {"id": resource_id}})
    return {
        "title": metadata.get("title"), "description": metadata.get("description"),
        "publication_date": metadata.get("publication_date"), "version": metadata.get("version"),
        "creators": people("creators"), "contributors": people("contributors"),
        "subjects": metadata.get("subjects") if metadata.get("subjects") is not None else ([{"subject": x} for x in metadata.get("keywords", [])]),
        "languages": ids("languages", "language"),
        "rights": ids("rights", "license"), "related_identifiers": related,
    }


def draft_files(value: object) -> dict[str, dict]:
    if not isinstance(value, dict) or not isinstance(value.get("files"), dict) or not isinstance(value["files"].get("entries"), dict):
        fail("Zenodo files representation is malformed")
    return value["files"]["entries"]


def public_inventory(record: dict) -> tuple[list[str], dict[str, dict]]:
    files = record.get("files")
    if not isinstance(files, list):
        fail("public Zenodo file inventory is malformed")
    order: list[str] = []; found: dict[str, dict] = {}
    for item in files:
        if not isinstance(item, dict) or not isinstance(item.get("key"), str):
            fail("public file entry is malformed")
        name = item["key"]; order.append(name); found[name] = item
    return order, found


def exact_public(record: dict, modern: dict, local: dict[str, dict], order: list[str]) -> bool:
    if record.get("id") is None or str(record.get("conceptrecid")) != CONCEPT_ID or record.get("conceptdoi") != CONCEPT_DOI:
        return False
    if projection(record) != projection({"metadata": modern}):
        return False
    try:
        public_order, files = public_inventory(record)
    except SystemExit:
        return False
    # Zenodo may canonicalize the public file-list order after publication;
    # reader-first is enforced by the PDF being present as the default preview
    # (thumbnail key) and by the release payload/manifest order, not by the
    # server's returned list order.
    thumbnails = ((record.get("links") or {}).get("thumbnails") or {})
    pdf_preview = any(PDF_NAME in str(url) for url in thumbnails.values())
    return set(public_order) == set(order) and len(files) == len(order) and pdf_preview and all(files[n].get("size") == local[n]["bytes"] and str(files[n].get("checksum", "")).removeprefix("md5:") == local[n]["md5"] for n in order)


def predecessor_ok(record: dict) -> None:
    metadata = record.get("metadata") or {}
    if record.get("id") != PREDECESSOR_ID or str(record.get("conceptrecid")) != CONCEPT_ID or record.get("doi") != PREDECESSOR_DOI or record.get("conceptdoi") != CONCEPT_DOI:
        fail("Zenodo predecessor is not the expected concept record")
    if "Batas Unit 06" not in str(metadata.get("title")) or str(metadata.get("version")) != "2026.08.22-unit06":
        fail("Zenodo predecessor metadata is not the published Unit 6 boundary")


def latest(session: httpx.Client, seed: dict) -> dict:
    url = ((seed.get("links") or {}).get("latest"))
    if not url:
        fail("Zenodo predecessor omitted latest-version link")
    value = api_json(session, "GET", url, (200,), "anonymous latest-version read")
    if not isinstance(value, dict) or str(value.get("conceptrecid")) != CONCEPT_ID:
        fail("latest link escaped the expected concept")
    return value


def anonymous_readback(session: httpx.Client, record: dict, modern: dict, local: dict[str, dict], order: list[str]) -> list[dict]:
    if not exact_public(record, modern, local, order):
        fail("public Unit 7 record is not an exact metadata/file match")
    _, files = public_inventory(record); results = []
    for name in order:
        url = ((files[name].get("links") or {}).get("self"))
        if not url:
            fail(f"public file lacks download URL: {name}")
        try:
            response = session.get(url, timeout=300)
        except httpx.HTTPError:
            fail(f"anonymous download failed before response: {name}")
        if response.status_code != 200:
            fail(f"anonymous download failed HTTP {response.status_code}: {name}")
        h = hashlib.sha256(); md = hashlib.md5(); size = 0
        for block in response.iter_bytes(1024 * 1024):
            if block: size += len(block); h.update(block); md.update(block)
        if (size, h.hexdigest(), md.hexdigest()) != (local[name]["bytes"], local[name]["sha256"], local[name]["md5"]):
            fail(f"anonymous byte mismatch: {name}")
        results.append({"name": name, "bytes": size, "sha256": h.hexdigest(), "md5": md.hexdigest(), "matches_local": True, "download_url": url})
    return results


def write_once(path: Path, value: dict) -> None:
    if path.exists():
        fail(f"refusing to overwrite receipt: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--token-file", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--staging-receipt", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--draft-id", type=int)
    args = parser.parse_args()
    root = args.root.resolve(); token_path = args.token_file.resolve(); metadata_path = (root / args.metadata).resolve(); staging_path = (root / args.staging_receipt).resolve(); receipt = (root / args.receipt).resolve()
    m, modern = expected_metadata(metadata_path)
    stage, local, order = local_payload(root, staging_path)
    public = httpx.Client(trust_env=False, follow_redirects=True, timeout=180)
    predecessor = api_json(public, "GET", f"https://zenodo.org/api/records/{PREDECESSOR_ID}", (200,), "anonymous predecessor read")
    if not isinstance(predecessor, dict): fail("predecessor response malformed")
    predecessor_ok(predecessor)
    current = latest(public, predecessor)
    if exact_public(current, modern, local, order):
        files = anonymous_readback(public, current, modern, local, order)
        public_order, _ = public_inventory(current)
        write_once(receipt, {"schema_version": 1, "workflow": "o011-publish-zenodo-unit07-rdm-v1", "status": "pass", "publication_action": "recovered_existing_exact_publication", "authentication_used_for_publication_path": False, "authentication_used_for_public_readback": False, "verified_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "record_id": current["id"], "concept_record_id": int(CONCEPT_ID), "doi": current.get("doi"), "concept_doi": CONCEPT_DOI, "record_url": f"https://zenodo.org/records/{current['id']}", "reader_first_order": order, "public_file_order": public_order, "pdf_default_preview_verified": True, "files": files, "metadata_title": m["title"]})
        return 0
    if current.get("id") != PREDECESSOR_ID:
        fail("a different public version is already latest and is not the exact Unit 7 release; refusing duplicate")
    try:
        token = token_path.read_text(encoding="utf-8-sig").strip()
    except (OSError, UnicodeError):
        fail("unable to read Zenodo token file")
    if not token or any(c.isspace() for c in token): fail("invalid token-file shape")
    auth = httpx.Client(trust_env=False, follow_redirects=True, timeout=180, headers={"Authorization": f"Bearer {token}", "Accept": API_MEDIA, "User-Agent": "O011-unit07-publisher/1.0"}); del token
    drafts_value = api_json(auth, "GET", "https://zenodo.org/api/user/records?q=is_published:false&size=100&page=1", (200,), "authenticated draft listing")
    hits = (drafts_value.get("hits", {}).get("hits") if isinstance(drafts_value, dict) else None) or []
    drafts = [x for x in hits if isinstance(x, dict) and x.get("status") == "new_version_draft" and str((x.get("parent") or {}).get("id")) == CONCEPT_ID and int((x.get("versions") or {}).get("index", 2)) > 1]
    if args.draft_id:
        drafts = [{"id": args.draft_id}] if not any(int(x.get("id", -1)) == args.draft_id for x in drafts) else [x for x in drafts if int(x.get("id")) == args.draft_id]
    if len(drafts) > 1: fail("multiple Unit 7 drafts exist; refusing ambiguity")
    if drafts:
        draft_id = int(drafts[0]["id"]); origin = "resumed_existing_new_api_draft"
    else:
        created = api_json(auth, "POST", f"https://zenodo.org/api/records/{PREDECESSOR_ID}/versions", (201,), "new-version creation")
        if not isinstance(created, dict) or not str(created.get("id", "")).isdigit(): fail("new-version response omitted draft ID")
        draft_id = int(created["id"]); origin = "created_new_api_version_draft"
    draft_url = f"https://zenodo.org/api/records/{draft_id}/draft"
    initial = {"metadata": modern, "access": {"record": "public", "files": "public"}, "files": {"enabled": True}}
    api_json(auth, "PUT", draft_url, (200,), "initial Unit 7 metadata update", json=initial, headers={"Content-Type": "application/json", "Accept": API_MEDIA})
    current_draft = api_json(auth, "GET", draft_url, (200,), "draft file read")
    entries = draft_files(current_draft)
    exact = len(entries) == len(order) and all(name in entries and entries[name].get("size") == local[name]["bytes"] and str(entries[name].get("checksum", "")).removeprefix("md5:") == local[name]["md5"] for name in order)
    base = f"https://zenodo.org/api/records/{draft_id}/draft/files"
    uploads = []
    if not exact:
        for name in list(entries): api_status(auth, "DELETE", f"{base}/{quote(name, safe='')}", (200, 204), f"delete old draft file {name}")
        api_json(auth, "POST", base, (200, 201), "draft file initialization", json=[{"key": name} for name in order], headers={"Content-Type": "application/json", "Accept": API_MEDIA})
        for name in order:
            with local[name]["path"].open("rb") as stream:
                try: response = auth.put(f"{base}/{quote(name, safe='')}/content", content=stream, timeout=300, headers={"Content-Type": "application/octet-stream", "Accept": API_MEDIA})
                except httpx.HTTPError: fail(f"upload failed before response: {name}")
            if response.status_code not in (200, 201): fail(f"upload failed HTTP {response.status_code}: {name}")
            committed = api_json(auth, "POST", f"{base}/{quote(name, safe='')}/commit", (200, 201), f"commit {name}")
            if not isinstance(committed, dict) or committed.get("size") != local[name]["bytes"] or str(committed.get("checksum", "")).removeprefix("md5:") != local[name]["md5"]: fail(f"commit identity mismatch: {name}")
            uploads.append({"name": name, "status": "uploaded_exact"})
    final = {"metadata": modern, "access": {"record": "public", "files": "public"}, "files": {"enabled": True, "default_preview": PDF_NAME, "order": order}}
    api_json(auth, "PUT", draft_url, (200,), "final Unit 7 metadata update", json=final, headers={"Content-Type": "application/json", "Accept": API_MEDIA})
    verified_draft = api_json(auth, "GET", draft_url, (200,), "final draft verification")
    if projection({"metadata": (verified_draft.get("metadata") if isinstance(verified_draft, dict) else {})}) != projection({"metadata": modern}): fail("draft metadata mismatch")
    if not isinstance(verified_draft, dict) or len(draft_files(verified_draft)) != len(order): fail("draft file closure mismatch")
    latest_before = latest(public, predecessor)
    if latest_before.get("id") != PREDECESSOR_ID: fail("predecessor ceased to be latest before publish")
    published = api_json(auth, "POST", f"{draft_url}/actions/publish", (201, 202), "Unit 7 draft publication")
    published_id = int(published.get("id", draft_id)) if isinstance(published, dict) and str(published.get("id", draft_id)).isdigit() else draft_id
    recovered = None
    for _ in range(30):
        candidate = api_json(public, "GET", f"https://zenodo.org/api/records/{published_id}", (200,), "anonymous post-publication read")
        if isinstance(candidate, dict) and exact_public(candidate, modern, local, order): recovered = candidate; break
        time.sleep(3)
    if recovered is None: fail("published Unit 7 bytes were not visible anonymously")
    files = anonymous_readback(public, recovered, modern, local, order)
    public_order, _ = public_inventory(recovered)
    write_once(receipt, {"schema_version": 1, "workflow": "o011-publish-zenodo-unit07-rdm-v1", "status": "pass", "publication_action": "published_new_version", "authentication_used_for_publication_path": True, "authentication_used_for_public_readback": False, "verified_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "record_id": recovered["id"], "concept_record_id": int(CONCEPT_ID), "doi": recovered.get("doi"), "concept_doi": CONCEPT_DOI, "record_url": f"https://zenodo.org/records/{recovered['id']}", "draft": {"id": draft_id, "origin": origin, "uploads": uploads}, "reader_first_order": order, "public_file_order": public_order, "pdf_default_preview_verified": True, "files": files, "metadata_title": m["title"]})
    print(json.dumps({"status": "pass", "record_id": recovered["id"], "doi": recovered.get("doi")}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
