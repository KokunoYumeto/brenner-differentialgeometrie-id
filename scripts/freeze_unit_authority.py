#!/usr/bin/env python3
"""Freeze one Brenner lecture/worksheet authority boundary before translation.

The script is intentionally narrow.  It reads the already-frozen recursive
exports and revision manifests, then performs only the official MediaWiki and
Commons API requests required to close one unit's expanded LaTeX, worksheet
solution candidates, and actually referenced media.  Existing frozen API
responses are never fetched over or replaced.
"""

from __future__ import annotations

import argparse
import base64
import csv
import difflib
import hashlib
import html
import io
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


COURSE = "Kurs:Differentialgeometrie (Osnabrück 2023)"
WIKIVERSITY_API = "https://de.wikiversity.org/w/api.php"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = (
    "Interlanguage-O011-authority-freeze/1.0 "
    "(bounded archival request for an attributed educational derivative)"
)
TASK_BLOCK_RE = re.compile(
    r"\{\{\s*inputaufgabe\s*\n(?P<body>.*?)\n\}\}", re.IGNORECASE | re.DOTALL
)
TASK_HEAD_RE = re.compile(r"^\|([^|\n]+)\|([^|\n]*)\|", re.DOTALL)
TASK_MACRO_RE = re.compile(
    r"(?m)^\\(inputaufgabegibtloesung|inputaufgabe)\s*\n\{([^{}\n]*)\}"
)
SECTION_MACRO_RE = re.compile(r"(?m)^\s*\\zwischenueberschrift\s*\{")
IMAGE_LICENSE_RE = re.compile(r"\\bildlizenz\s*\{\s*([^{}]+?)\s*\}")
INCLUDEGRAPHICS_RE = re.compile(r"\\includegraphics(?:\[[^\]]*\])?\s*\{")
IMAGE_INPUT_RE = re.compile(
    r"\\bildeinlesung(?:png|PNG|jpg|JPG|jpeg|svg|gif|GIF)?\s*"
    r"\{\s*([^{}]+?)\s*\}(?:\s*\{\s*([^{}]+?)\s*\})?"
)
HTML_TAG_RE = re.compile(
    r"</?[A-Za-z][A-Za-z0-9]*\s*/?>|"
    r"<[A-Za-z][A-Za-z0-9]*(?:\s+[A-Za-z_:][-A-Za-z0-9_:.]*\s*=\s*"
    r"(?:\"[^\"]*\"|'[^']*'|[^\s\"'=<>`]+))+\s*/?>",
    re.IGNORECASE,
)


def sha(data: bytes, algorithm: str = "sha256") -> str:
    return hashlib.new(algorithm, data).hexdigest()


def base36(number: int) -> str:
    alphabet = "0123456789abcdefghijklmnopqrstuvwxyz"
    if number == 0:
        return "0"
    output = ""
    while number:
        number, remainder = divmod(number, 36)
        output = alphabet[remainder] + output
    return output


def mediawiki_sha1_base36(data: bytes) -> str:
    # MediaWiki serializes SHA-1 values as a fixed-width 31-character base-36
    # string.  Preserve leading zeroes so low-leading-bit digests compare
    # byte-for-byte with export manifests (for example, Lecture 12).
    return base36(int(sha(data, "sha1"), 16)).rjust(31, "0")


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def rel(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def file_entry(path: Path, root: Path) -> dict[str, Any]:
    data = path.read_bytes()
    return {"path": rel(path, root), "bytes": len(data), "sha256": sha(data)}


def canonical_json(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    ).encode("utf-8")


def preserve_or_write(path: Path, data: bytes) -> None:
    if path.exists():
        existing = path.read_bytes()
        if existing != data:
            raise RuntimeError(f"refusing to overwrite differing frozen file: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def write_generated(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def request_api(endpoint: str, parameters: dict[str, str]) -> tuple[bytes, dict[str, str]]:
    body = urllib.parse.urlencode(parameters).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=body,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        },
        method="POST",
    )
    last_error: Exception | None = None
    for attempt in range(6):
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                data = response.read()
                headers = {
                    "date": response.headers.get("Date", ""),
                    "content_type": response.headers.get("Content-Type", ""),
                }
            payload = json.loads(data.decode("utf-8"))
            if payload.get("error"):
                raise RuntimeError(f"MediaWiki API error: {payload['error']}")
            return data, headers
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code != 429 or attempt == 5:
                break
            retry_after = exc.headers.get("Retry-After")
            try:
                delay = float(retry_after) if retry_after else 5.0 * (2**attempt)
            except ValueError:
                delay = 5.0 * (2**attempt)
            # A bounded backoff respects the public API without allowing one
            # request to leave this unit-level freeze dormant indefinitely.
            time.sleep(min(max(delay, 1.0), 45.0))
        except (urllib.error.URLError, TimeoutError) as exc:
            last_error = exc
            if attempt == 5:
                break
            time.sleep(min(2.0 * (attempt + 1), 12.0))
    raise RuntimeError(f"API request failed after retries: {last_error}")


def fetch_frozen_api(
    path: Path,
    endpoint: str,
    parameters: dict[str, str],
) -> tuple[bytes, dict[str, Any]]:
    sidecar = path.with_suffix(path.suffix + ".request.json")
    if path.exists():
        if not sidecar.exists():
            raise RuntimeError(f"frozen response lacks request receipt: {path}")
        data = path.read_bytes()
        receipt = json.loads(sidecar.read_text(encoding="utf-8"))
        if receipt.get("response_sha256") != sha(data):
            raise RuntimeError(f"stale request receipt: {sidecar}")
        if receipt.get("endpoint") != endpoint or receipt.get("parameters") != parameters:
            raise RuntimeError(f"request identity mismatch: {sidecar}")
        return data, receipt

    data, headers = request_api(endpoint, parameters)
    receipt = {
        "schema_version": 1,
        "retrieved_utc": utc_now(),
        "endpoint": endpoint,
        "method": "POST",
        "parameters": parameters,
        "http_date": headers["date"],
        "content_type": headers["content_type"],
        "response_path": str(path.name),
        "response_bytes": len(data),
        "response_sha256": sha(data),
    }
    preserve_or_write(path, data)
    preserve_or_write(sidecar, canonical_json(receipt))
    return data, receipt


def download_binary(path: Path, url: str) -> tuple[bytes, dict[str, Any]]:
    sidecar = path.with_suffix(path.suffix + ".download.json")
    if path.exists():
        data = path.read_bytes()
        if sidecar.exists():
            receipt = json.loads(sidecar.read_text(encoding="utf-8"))
            if receipt.get("sha256") != sha(data) or receipt.get("url") != url:
                raise RuntimeError(f"stale media download receipt: {sidecar}")
        else:
            receipt = {
                "schema_version": 1,
                "retrieved_utc": "pre-existing admitted binary",
                "url": url,
                "bytes": len(data),
                "sha1": sha(data, "sha1"),
                "sha256": sha(data),
            }
        return data, receipt

    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    last_error: Exception | None = None
    data: bytes | None = None
    final_url = ""
    http_date = ""
    content_type = ""
    for attempt in range(5):
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                data = response.read()
                final_url = response.geturl()
                http_date = response.headers.get("Date", "")
                content_type = response.headers.get("Content-Type", "")
            break
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code != 429 or attempt == 4:
                raise
            retry_after = exc.headers.get("Retry-After") if exc.headers else None
            delay = int(retry_after) if retry_after and retry_after.isdigit() else 5 * (attempt + 1)
            time.sleep(min(delay, 30))
        except (urllib.error.URLError, TimeoutError) as exc:
            last_error = exc
            if attempt == 4:
                raise
            time.sleep(2 * (attempt + 1))
    if data is None:
        raise RuntimeError(f"binary download failed after retries: {last_error}")
    receipt = {
        "schema_version": 1,
        "retrieved_utc": utc_now(),
        "url": url,
        "final_url": final_url,
        "http_date": http_date,
        "content_type": content_type,
        "bytes": len(data),
        "sha1": sha(data, "sha1"),
        "sha256": sha(data),
    }
    preserve_or_write(path, data)
    preserve_or_write(sidecar, canonical_json(receipt))
    return data, receipt


def csv_rows(path: Path) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(path.read_text(encoding="utf-8-sig"))))


def unique_row(rows: list[dict[str, str]], title: str) -> dict[str, str]:
    matches = [row for row in rows if row.get("title") == title]
    if len(matches) != 1:
        raise RuntimeError(f"expected one manifest row for {title!r}, found {len(matches)}")
    return matches[0]


def xml_page(xml_path: Path, title: str) -> dict[str, Any]:
    for _, element in ET.iterparse(xml_path, events=("end",)):
        if not element.tag.endswith("page"):
            continue
        page_title = next((child.text for child in element if child.tag.endswith("title")), "")
        if page_title == title:
            namespace = next(child.text for child in element if child.tag.endswith("ns"))
            pageid = next(child.text for child in element if child.tag.endswith("id"))
            revision = next(child for child in element if child.tag.endswith("revision"))
            values: dict[str, str] = {}
            for child in revision:
                key = child.tag.rsplit("}", 1)[-1]
                if key in {"id", "parentid", "timestamp", "model", "format", "sha1"}:
                    values[key] = child.text or ""
            text_element = next(child for child in revision if child.tag.endswith("text"))
            return {
                "title": title,
                "namespace": int(namespace),
                "pageid": int(pageid),
                "revid": int(values["id"]),
                "parentid": int(values.get("parentid") or 0),
                "timestamp": values["timestamp"],
                "model": values.get("model"),
                "format": values.get("format"),
                "mediawiki_sha1_base36": values["sha1"],
                "text": text_element.text or "",
            }
        element.clear()
    raise RuntimeError(f"page not found in frozen recursive export: {title}")


def freeze_xml_witness(
    root: Path,
    xml_path: Path,
    manifest_row: dict[str, str],
    stem: str,
) -> tuple[dict[str, Any], str]:
    page = xml_page(xml_path, manifest_row["title"])
    content = page.pop("text")
    content_bytes = content.encode("utf-8")
    if page["pageid"] != int(manifest_row["pageid"]) or page["revid"] != int(manifest_row["revid"]):
        raise RuntimeError(f"XML/CSV page identity mismatch for {manifest_row['title']}")
    if page["mediawiki_sha1_base36"] != manifest_row["mediawiki_sha1_base36"]:
        raise RuntimeError(f"XML/CSV MediaWiki SHA-1 mismatch for {manifest_row['title']}")
    if mediawiki_sha1_base36(content_bytes) != manifest_row["mediawiki_sha1_base36"]:
        raise RuntimeError(f"content MediaWiki SHA-1 mismatch for {manifest_row['title']}")
    if len(content_bytes) != int(manifest_row["text_utf8_bytes"]):
        raise RuntimeError(f"content byte mismatch for {manifest_row['title']}")

    exact_path = root / "authority/mediawiki" / f"{stem}.utf8.b64"
    readable_path = root / "authority/mediawiki" / f"{stem}.wiki"
    metadata_path = root / "authority/mediawiki" / f"{stem}.metadata.json"
    exact_bytes = (base64.b64encode(content_bytes).decode("ascii") + "\n").encode("ascii")
    readable_bytes = (content.replace("\r\n", "\n").replace("\r", "\n").rstrip() + "\n").encode("utf-8")
    metadata = {
        "schema_version": 1,
        "authority": "frozen recursive German Wikiversity Special:Export",
        "source_export": rel(xml_path, root),
        "source_export_sha256": sha(xml_path.read_bytes()),
        **page,
        "source_utf8_bytes": len(content_bytes),
        "source_utf8_sha1": sha(content_bytes, "sha1"),
        "source_utf8_sha256": sha(content_bytes),
        "exact_utf8_base64_witness": rel(exact_path, root),
        "exact_utf8_base64_sha256": sha(exact_bytes),
        "readable_normalized_witness": rel(readable_path, root),
        "readable_normalized_bytes": len(readable_bytes),
        "readable_normalized_sha256": sha(readable_bytes),
    }
    preserve_or_write(exact_path, exact_bytes)
    preserve_or_write(readable_path, readable_bytes)
    preserve_or_write(metadata_path, canonical_json(metadata))
    metadata["metadata"] = file_entry(metadata_path, root)
    return metadata, content


def freeze_api_revision_witness(
    root: Path,
    title: str,
    revid: int,
    stem: str,
) -> tuple[dict[str, Any], str]:
    """Freeze one explicitly selected root revision outside the course export.

    The whole-course recursive export remains the reproducibility baseline.  A
    later official root-page repair can nevertheless be adopted without
    silently mixing its current expansion with the older root witness.  This
    helper preserves the exact API response and request identity, then creates
    the same lossless source witnesses used for export-backed pages.
    """
    query_path = root / "authority/mediawiki" / f"{stem}.json"
    parameters = {
        "action": "query",
        "format": "json",
        "formatversion": "2",
        "prop": "revisions",
        "rvprop": "ids|timestamp|sha1|content",
        "rvslots": "main",
        "revids": str(revid),
    }
    response_bytes, _ = fetch_frozen_api(query_path, WIKIVERSITY_API, parameters)
    payload = json.loads(response_bytes.decode("utf-8"))
    pages = payload.get("query", {}).get("pages", [])
    if len(pages) != 1:
        raise RuntimeError(f"expected one API page for exact revision {revid}")
    page = pages[0]
    revisions = page.get("revisions") or []
    if page.get("title") != title or len(revisions) != 1:
        raise RuntimeError(f"exact revision {revid} resolved to an unexpected page")
    revision = revisions[0]
    if int(revision.get("revid", -1)) != revid:
        raise RuntimeError(f"API returned the wrong exact revision for {title}")
    slot = revision.get("slots", {}).get("main", {})
    content = slot.get("content")
    if not isinstance(content, str):
        raise RuntimeError(f"exact revision {revid} has no main-slot content")
    content_bytes = content.encode("utf-8")
    if sha(content_bytes, "sha1") != revision.get("sha1"):
        raise RuntimeError(f"MediaWiki SHA-1 mismatch for exact revision {revid}")

    exact_path = root / "authority/mediawiki" / f"{stem}.utf8.b64"
    readable_path = root / "authority/mediawiki" / f"{stem}.wiki"
    metadata_path = root / "authority/mediawiki" / f"{stem}.metadata.json"
    exact_bytes = (base64.b64encode(content_bytes).decode("ascii") + "\n").encode("ascii")
    readable_bytes = (
        content.replace("\r\n", "\n").replace("\r", "\n").rstrip() + "\n"
    ).encode("utf-8")
    metadata = {
        "schema_version": 1,
        "authority": "German Wikiversity MediaWiki API exact root-revision override",
        "source_api_response": file_entry(query_path, root),
        "source_api_request_receipt": file_entry(
            query_path.with_suffix(query_path.suffix + ".request.json"), root
        ),
        "pageid": int(page["pageid"]),
        "namespace": int(page["ns"]),
        "title": page["title"],
        "revid": int(revision["revid"]),
        "parentid": int(revision["parentid"]),
        "timestamp": revision["timestamp"],
        "mediawiki_sha1": revision["sha1"],
        "mediawiki_sha1_base36": mediawiki_sha1_base36(content_bytes),
        "model": slot.get("contentmodel"),
        "format": slot.get("contentformat"),
        "source_utf8_bytes": len(content_bytes),
        "source_utf8_sha1": sha(content_bytes, "sha1"),
        "source_utf8_sha256": sha(content_bytes),
        "exact_utf8_base64_witness": rel(exact_path, root),
        "exact_utf8_base64_sha256": sha(exact_bytes),
        "readable_normalized_witness": rel(readable_path, root),
        "readable_normalized_bytes": len(readable_bytes),
        "readable_normalized_sha256": sha(readable_bytes),
    }
    preserve_or_write(exact_path, exact_bytes)
    preserve_or_write(readable_path, readable_bytes)
    preserve_or_write(metadata_path, canonical_json(metadata))
    metadata["metadata"] = file_entry(metadata_path, root)
    return metadata, content


def freeze_revision_compare(
    root: Path,
    stem: str,
    fromrevid: int,
    torevid: int,
) -> dict[str, Any]:
    """Freeze the official diff that justifies an explicit root override."""
    path = root / "authority/mediawiki" / f"{stem}.json"
    parameters = {
        "action": "compare",
        "format": "json",
        "formatversion": "2",
        "fromrev": str(fromrevid),
        "torev": str(torevid),
        "prop": "ids|title|diff|user|comment|parsedcomment|size",
    }
    response_bytes, _ = fetch_frozen_api(path, WIKIVERSITY_API, parameters)
    payload = json.loads(response_bytes.decode("utf-8"))
    comparison = payload.get("compare", {})
    if (
        int(comparison.get("fromrevid", -1)) != fromrevid
        or int(comparison.get("torevid", -1)) != torevid
    ):
        raise RuntimeError("revision comparison returned unexpected identities")
    return {
        "response": file_entry(path, root),
        "request_receipt": file_entry(
            path.with_suffix(path.suffix + ".request.json"), root
        ),
        "fromsize": int(comparison["fromsize"]),
        "tosize": int(comparison["tosize"]),
    }


def source_delta_operations(baseline: str, adopted: str) -> list[dict[str, Any]]:
    operations: list[dict[str, Any]] = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(
        None, baseline, adopted, autojunk=False
    ).get_opcodes():
        if tag == "equal":
            continue
        operations.append(
            {
                "operation": tag,
                "baseline_span": [i1, i2],
                "adopted_span": [j1, j2],
                "baseline_text": baseline[i1:i2],
                "adopted_text": adopted[j1:j2],
            }
        )
    return operations


def freeze_root_override_transition(
    root: Path,
    unit: int,
    surface_key: str,
    root_title: str,
    latex_surface_title: str,
    baseline_page: dict[str, Any],
    baseline_text: str,
    adopted_page: dict[str, Any],
    adopted_text: str,
    live_expansion: dict[str, Any],
) -> dict[str, Any]:
    """Prove a root override does not silently change the frozen expansion."""
    if adopted_page["pageid"] != baseline_page["pageid"]:
        raise RuntimeError("root override changed page identity")
    if adopted_page["parentid"] != baseline_page["revid"]:
        raise RuntimeError("root override is not a direct child of the export baseline")

    sandbox_rows: dict[str, dict[str, Any]] = {}
    expanded_texts: dict[str, str] = {}
    for label, revision, source_text in (
        ("baseline", int(baseline_page["revid"]), baseline_text),
        ("adopted", int(adopted_page["revid"]), adopted_text),
    ):
        path = (
            root
            / "authority/exports"
            / f"{surface_key}{unit:02d}_latex_expand_root_revid{revision}_sandbox.json"
        )
        parameters = {
            "action": "expandtemplates",
            "format": "json",
            "formatversion": "2",
            "prop": "wikitext|categories|modules|jsconfigvars",
            "title": latex_surface_title,
            "text": "{{Latex}}",
            "templatesandboxtitle": root_title,
            "templatesandboxtext": source_text,
        }
        response_bytes, _ = fetch_frozen_api(path, WIKIVERSITY_API, parameters)
        payload = json.loads(response_bytes.decode("utf-8"))
        expanded = payload.get("expandtemplates", {}).get("wikitext")
        if not isinstance(expanded, str):
            raise RuntimeError("TemplateSandbox expansion lacks wikitext")
        expanded_texts[label] = expanded
        sandbox_rows[label] = {
            "root_revid": revision,
            "response": file_entry(path, root),
            "request_receipt": file_entry(
                path.with_suffix(path.suffix + ".request.json"), root
            ),
            "expanded_characters": len(expanded),
            "expanded_utf8_bytes": len(expanded.encode("utf-8")),
            "expanded_utf8_sha256": sha(expanded.encode("utf-8")),
        }

    live_response_path = root / live_expansion["response"]["path"]
    live_payload = json.loads(live_response_path.read_text(encoding="utf-8"))
    live_text = live_payload.get("expandtemplates", {}).get("wikitext")
    if not isinstance(live_text, str):
        raise RuntimeError("frozen live expansion lacks wikitext")
    all_equal = (
        expanded_texts["baseline"] == expanded_texts["adopted"] == live_text
    )
    if not all_equal:
        raise RuntimeError("root override changes the already-frozen official expansion")

    receipt = {
        "schema_version": 1,
        "workflow": "o011-root-revision-override-transition-v1",
        "unit": unit,
        "surface": surface_key,
        "root_title": root_title,
        "latex_surface_title": latex_surface_title,
        "baseline": {
            "pageid": baseline_page["pageid"],
            "revid": baseline_page["revid"],
            "source_utf8_bytes": baseline_page["source_utf8_bytes"],
            "source_utf8_sha256": baseline_page["source_utf8_sha256"],
        },
        "adopted": {
            "pageid": adopted_page["pageid"],
            "revid": adopted_page["revid"],
            "parentid": adopted_page["parentid"],
            "timestamp": adopted_page["timestamp"],
            "source_utf8_bytes": adopted_page["source_utf8_bytes"],
            "source_utf8_sha256": adopted_page["source_utf8_sha256"],
        },
        "adopted_is_direct_child": True,
        "source_utf8_byte_delta": len(adopted_text.encode("utf-8"))
        - len(baseline_text.encode("utf-8")),
        "source_delta_operations": source_delta_operations(
            baseline_text, adopted_text
        ),
        "template_sandbox": sandbox_rows,
        "existing_frozen_expansion": {
            "response": live_expansion["response"],
            "request_receipt": live_expansion["request_receipt"],
            "expanded_characters": len(live_text),
            "expanded_utf8_bytes": len(live_text.encode("utf-8")),
            "expanded_utf8_sha256": sha(live_text.encode("utf-8")),
        },
        "baseline_adopted_and_existing_expansions_byte_identical": all_equal,
        "status": "pass",
    }
    output_path = (
        root
        / f"qa/unit-{unit:02d}"
        / f"{surface_key.upper()}_ROOT_OVERRIDE_TRANSITION.json"
    )
    write_generated(output_path, canonical_json(receipt))
    return file_entry(output_path, root)


def run_sanitizer(root: Path, response: Path, output: Path, receipt: Path) -> None:
    if output.exists() or receipt.exists():
        if not output.exists() or not receipt.exists():
            raise RuntimeError(f"partial sanitizer state for {response}")
        saved = json.loads(receipt.read_text(encoding="utf-8"))
        if saved.get("input_sha256") != sha(response.read_bytes()):
            raise RuntimeError(f"stale sanitizer input receipt: {receipt}")
        if saved.get("output_sha256") != sha(output.read_bytes()):
            raise RuntimeError(f"stale sanitizer output receipt: {receipt}")
        return
    subprocess.run(
        [
            sys.executable,
            str(root / "scripts/sanitize_brenner_expand.py"),
            str(response),
            str(output),
            "--project-root",
            str(root),
            "--receipt",
            str(receipt),
        ],
        check=True,
    )


def freeze_expansion(
    root: Path,
    response_path: Path,
    output_path: Path,
    receipt_path: Path,
    context_title: str,
) -> dict[str, Any]:
    parameters = {
        "action": "expandtemplates",
        "format": "json",
        "formatversion": "2",
        "prop": "wikitext|categories|modules|jsconfigvars",
        "title": context_title,
        "text": "{{Latex}}",
    }
    response_bytes, request_receipt = fetch_frozen_api(
        response_path, WIKIVERSITY_API, parameters
    )
    payload = json.loads(response_bytes.decode("utf-8"))
    expanded = payload.get("expandtemplates", {}).get("wikitext")
    if not isinstance(expanded, str):
        raise RuntimeError(f"missing expandtemplates.wikitext in {response_path}")
    run_sanitizer(root, response_path, output_path, receipt_path)
    output_text = output_path.read_text(encoding="utf-8")
    if "\ufffd" in output_text or HTML_TAG_RE.search(output_text):
        raise RuntimeError(f"unsafe residue in sanitized source: {output_path}")
    return {
        "api_endpoint": WIKIVERSITY_API,
        "parameters": parameters,
        "retrieved_utc": request_receipt["retrieved_utc"],
        "http_date": request_receipt.get("http_date"),
        "response": file_entry(response_path, root),
        "request_receipt": file_entry(
            response_path.with_suffix(response_path.suffix + ".request.json"), root
        ),
        "expanded_characters": len(expanded),
        "sanitized_source": file_entry(output_path, root),
        "sanitizer_receipt": file_entry(receipt_path, root),
        "sanitizer": file_entry(root / "scripts/sanitize_brenner_expand.py", root),
        "valid_utf8": True,
        "residual_html_tags": False,
        "replacement_characters": False,
    }


def parse_tasks(root_wikitext: str, worksheet_tex: str) -> list[dict[str, Any]]:
    roots: list[dict[str, Any]] = []
    for block_match in TASK_BLOCK_RE.finditer(root_wikitext):
        body = block_match.group("body")
        head = TASK_HEAD_RE.match(body)
        if not head:
            raise RuntimeError("could not parse an inputaufgabe root block")
        hint_match = re.search(r"(?m)^\|tipp=(.*)$", body)
        roots.append(
            {
                "task_title": head.group(1).strip(),
                "root_point_marker": head.group(2).strip(),
                "hint_field": (hint_match.group(1).strip() if hint_match else None),
            }
        )
    macros = TASK_MACRO_RE.findall(worksheet_tex)
    if len(roots) != len(macros):
        raise RuntimeError(
            f"worksheet root/expanded exercise mismatch: {len(roots)} roots, {len(macros)} macros"
        )
    exercises: list[dict[str, Any]] = []
    for index, (root_task, macro) in enumerate(zip(roots, macros), 1):
        macro_name, points = macro
        points = points.strip()
        marker = root_task["root_point_marker"]
        if bool(marker) != bool(points):
            raise RuntimeError(
                f"graded marker/point-value mismatch at exercise {index}: {marker!r}/{points!r}"
            )
        exercises.append(
            {
                "exercise_index": index,
                **root_task,
                "point_value": int(points) if points.isdigit() else (points or None),
                "expanded_macro": macro_name,
                "solution_marker": macro_name == "inputaufgabegibtloesung",
                "solution_title": root_task["task_title"] + "/Lösung",
            }
        )
    return exercises


def graded_point_value(value: Any) -> int:
    """Return the total encoded by an integer or split-point worksheet label."""
    if isinstance(value, int):
        return value
    text = str(value).strip()
    if text.isdigit():
        return int(text)
    match = re.fullmatch(r"(\d+)\s*\((\d+(?:\+\d+)+)\)", text)
    if not match:
        raise RuntimeError(f"unsupported graded point label: {value!r}")
    total = int(match.group(1))
    parts = sum(int(part) for part in match.group(2).split("+"))
    if parts != total:
        raise RuntimeError(f"inconsistent split-point label: {value!r}")
    return total


def freeze_solution_closure(
    root: Path,
    unit: int,
    exercises: list[dict[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    unit_tag = f"unit{unit:02d}"
    query_path = root / "authority/mediawiki" / f"{unit_tag}_solution_pages_current.json"
    titles = "|".join(str(item["solution_title"]) for item in exercises)
    parameters = {
        "action": "query",
        "format": "json",
        "formatversion": "2",
        "prop": "revisions",
        "rvprop": "ids|timestamp|sha1|content",
        "rvslots": "main",
        "titles": titles,
    }
    query_bytes, query_receipt = fetch_frozen_api(query_path, WIKIVERSITY_API, parameters)
    payload = json.loads(query_bytes.decode("utf-8"))
    query = payload.get("query", {})
    pages = query.get("pages", [])
    pages_by_title = {page["title"]: page for page in pages}
    expected = {str(item["solution_title"]) for item in exercises}
    title_aliases: dict[str, str] = {}
    for key in ("normalized", "converted", "redirects"):
        for item in query.get(key, []):
            if isinstance(item, dict) and isinstance(item.get("from"), str) and isinstance(item.get("to"), str):
                title_aliases[item["from"]] = item["to"]

    def resolved_title(title: str) -> str:
        seen: set[str] = set()
        while title in title_aliases:
            if title in seen:
                raise RuntimeError(f"cyclic MediaWiki title normalization for {title!r}")
            seen.add(title)
            title = title_aliases[title]
        return title

    resolved_expected = {title: resolved_title(title) for title in expected}
    canonical_expected = set(resolved_expected.values())
    if set(pages_by_title) != canonical_expected:
        raise RuntimeError(
            "solution query title closure mismatch: "
            f"missing={sorted(canonical_expected - set(pages_by_title))}; "
            f"extra={sorted(set(pages_by_title) - canonical_expected)}"
        )

    supplied_expansions: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    api_existing_indices: set[int] = set()
    for exercise in exercises:
        index = int(exercise["exercise_index"])
        title = str(exercise["solution_title"])
        canonical_title = resolved_expected[title]
        page = pages_by_title[canonical_title]
        exists = "missing" not in page
        row = {
            **exercise,
            "resolved_solution_title": canonical_title,
            "title_normalized_by_mediawiki": canonical_title != title,
            "exists": exists,
        }
        if exists:
            api_existing_indices.add(index)
            revisions = page.get("revisions") or []
            if len(revisions) != 1:
                raise RuntimeError(f"expected one current revision for {title}")
            revision = revisions[0]
            slot = revision.get("slots", {}).get("main", {})
            content = slot.get("content")
            if not isinstance(content, str):
                raise RuntimeError(f"missing current main-slot content for {title}")
            content_bytes = content.encode("utf-8")
            if sha(content_bytes, "sha1") != revision["sha1"]:
                raise RuntimeError(f"MediaWiki SHA-1 mismatch for {title}")
            stem = f"worksheet{unit:02d}_exercise{index:02d}_solution_revid{revision['revid']}"
            exact_path = root / "authority/mediawiki" / f"{stem}.utf8.b64"
            readable_path = root / "authority/mediawiki" / f"{stem}.wiki"
            metadata_path = root / "authority/mediawiki" / f"{stem}.metadata.json"
            exact_bytes = (base64.b64encode(content_bytes).decode("ascii") + "\n").encode("ascii")
            readable_bytes = (
                content.replace("\r\n", "\n").replace("\r", "\n").rstrip() + "\n"
            ).encode("utf-8")
            metadata = {
                "schema_version": 1,
                "authority": "German Wikiversity MediaWiki API",
                "query_response": rel(query_path, root),
                "query_response_sha256": sha(query_bytes),
                "pageid": page["pageid"],
                "namespace": page["ns"],
                "requested_title": title,
                "title": canonical_title,
                "revid": revision["revid"],
                "parentid": revision["parentid"],
                "timestamp": revision["timestamp"],
                "mediawiki_sha1": revision["sha1"],
                "content_model": slot.get("contentmodel"),
                "content_format": slot.get("contentformat"),
                "source_characters": len(content),
                "source_utf8_bytes": len(content_bytes),
                "source_utf8_sha1": sha(content_bytes, "sha1"),
                "source_utf8_sha256": sha(content_bytes),
                "exact_utf8_base64_witness": rel(exact_path, root),
                "exact_utf8_base64_sha256": sha(exact_bytes),
                "readable_normalized_witness": rel(readable_path, root),
                "readable_normalized_bytes": len(readable_bytes),
                "readable_normalized_sha256": sha(readable_bytes),
            }
            preserve_or_write(exact_path, exact_bytes)
            preserve_or_write(readable_path, readable_bytes)
            preserve_or_write(metadata_path, canonical_json(metadata))

            response_path = root / "authority/exports" / f"worksheet{unit:02d}_exercise{index:02d}_solution_latex_expand.json"
            output_path = root / "authority/expanded" / f"worksheet{unit:02d}_exercise{index:02d}_solution_source.de.tex"
            sanitize_path = root / f"qa/unit-{unit:02d}" / f"worksheet{unit:02d}_exercise{index:02d}_solution_sanitize.json"
            expansion = freeze_expansion(
                root, response_path, output_path, sanitize_path, canonical_title + "/latex"
            )
            supplied_expansions.append(
                {
                    "exercise_index": index,
                    "solution_title": title,
                    "resolved_solution_title": canonical_title,
                    "expansion": expansion,
                }
            )
            row.update(
                {
                    "pageid": page["pageid"],
                    "revid": revision["revid"],
                    "parentid": revision["parentid"],
                    "timestamp": revision["timestamp"],
                    "mediawiki_sha1": revision["sha1"],
                    "source_utf8_bytes": len(content_bytes),
                    "source_utf8_sha256": sha(content_bytes),
                    "metadata": file_entry(metadata_path, root),
                    "exact_utf8_base64_witness": file_entry(exact_path, root),
                    "readable_normalized_witness": file_entry(readable_path, root),
                    "expanded_latex": expansion,
                }
            )
        rows.append(row)

    marked_indices = {
        int(item["exercise_index"]) for item in exercises if item["solution_marker"]
    }
    macro_api_agreement = marked_indices == api_existing_indices
    manifest = {
        "schema_version": 1,
        "workflow": f"o011-unit{unit:02d}-solution-freeze-v1",
        "worksheet_root_title": f"{COURSE}/Arbeitsblatt {unit}",
        "query": file_entry(query_path, root),
        "query_request_receipt": file_entry(
            query_path.with_suffix(query_path.suffix + ".request.json"), root
        ),
        "query_retrieved_utc": query_receipt["retrieved_utc"],
        "exercise_count": len(exercises),
        "graded_exercise_count": sum(bool(item["root_point_marker"]) for item in exercises),
        "practice_exercise_count": sum(not bool(item["root_point_marker"]) for item in exercises),
        "point_value_total": sum(
            graded_point_value(item["point_value"])
            for item in exercises
            if item["point_value"] is not None
        ),
        "supplied_solution_count": len(api_existing_indices),
        "supplied_solution_indices": sorted(api_existing_indices),
        "missing_solution_count": len(exercises) - len(api_existing_indices),
        "macro_api_agreement": macro_api_agreement,
        "exercises": rows,
    }
    manifest_path = root / f"qa/unit-{unit:02d}/solution_closure.json"
    write_generated(manifest_path, canonical_json(manifest))
    return manifest, supplied_expansions


def ext_value(info: dict[str, Any], name: str) -> str:
    value = info.get("extmetadata", {}).get(name, {}).get("value", "")
    return str(value)


def plain_html(value: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", value)).strip()


def artist_identity(value: str) -> dict[str, Any]:
    """Return locale-stable identity evidence from Commons Artist HTML.

    Commons localizes connective prose such as "at English Wikipedia" while
    retaining the creator link and label.  When anchors exist, bind identity
    to their ordered hrefs plus the first (creator) label; otherwise retain the
    stricter exact plain-text identity.
    """
    anchors = re.findall(
        r"<a\b[^>]*\bhref=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>",
        value,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if anchors:
        return {
            "anchor_hrefs": [html.unescape(href).strip() for href, _ in anchors],
            "creator_label": plain_html(anchors[0][1]),
        }
    # Commons' anonymous/unknown creator templates localize their visible
    # label but retain a hidden canonical label (for example,
    # ``Unbekannt ... Unknown`` versus ``Unknown ... Unknown``).  Bind that
    # stable hidden identity when it is present instead of treating interface
    # language as a creator change.
    hidden_labels = [
        plain_html(body)
        for attributes, body in re.findall(
            r"<span\b([^>]*)>(.*?)</span>",
            value,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if re.search(r"display\s*:\s*none", attributes, flags=re.IGNORECASE)
    ]
    if hidden_labels:
        return {"hidden_labels": hidden_labels}
    return {"plain_text": plain_html(value)}


def image_names(text: str) -> list[str]:
    return [match.strip() for match in IMAGE_LICENSE_RE.findall(text)]


def media_name_key(name: str) -> str:
    """Compare TeX macro stems and license filenames by a stable basename key.

    The Wikiversity TeX macro convention uses underscores for spaces in
    ``\u005cbildeinlesung...`` stems, while ``\u005cbildlizenz`` records the
    canonical Commons filename with spaces.  The rights lookup must retain the
    canonical licensed spelling, but the closure check should not reject this
    lossless TeX spelling difference.
    """
    return re.sub(r"[_\s]+", " ", name.strip()).casefold()


def freeze_media(
    root: Path,
    unit: int,
    surface_texts: list[tuple[str, str]],
) -> dict[str, Any]:
    occurrences: list[dict[str, Any]] = []
    for surface, text in surface_texts:
        licensed = image_names(text)
        include_count = len(INCLUDEGRAPHICS_RE.findall(text))
        input_names: list[str] = []
        for stem, extension in IMAGE_INPUT_RE.findall(text):
            stem = stem.strip()
            extension = extension.strip()
            input_names.append(f"{stem}.{extension}" if extension else stem)
        if include_count != len(input_names):
            raise RuntimeError(
                f"unclosed image-input syntax in {surface}: includegraphics={include_count}, inputs={len(input_names)}"
            )
        if [media_name_key(name) for name in input_names] != [media_name_key(name) for name in licensed]:
            raise RuntimeError(
                f"display/license image mismatch in {surface}: displayed={input_names}, licensed={licensed}"
            )
        for order, filename in enumerate(licensed, 1):
            occurrences.append(
                {"surface": surface, "surface_order": order, "filename": filename}
            )

    filenames = list(dict.fromkeys(item["filename"] for item in occurrences))
    rights_path = root / "authority/brenner_media_rights_manifest.csv"
    rights_rows = csv_rows(rights_path)
    if not filenames:
        return {
            "occurrence_count": 0,
            "unique_asset_count": 0,
            "surface_occurrences": [],
            "rights_manifest": file_entry(rights_path, root),
            "current_commons_query": None,
            "assets": [],
            "all_displayed_images_have_license_macros": True,
        }

    query_path = root / "authority/mediawiki" / f"unit{unit:02d}_media_imageinfo_current.json"
    parameters = {
        "action": "query",
        "format": "json",
        "formatversion": "2",
        "prop": "info|imageinfo",
        "iiprop": "timestamp|user|url|size|sha1|mime|extmetadata",
        "titles": "|".join("File:" + name for name in filenames),
    }
    query_bytes, query_receipt = fetch_frozen_api(query_path, COMMONS_API, parameters)
    payload = json.loads(query_bytes.decode("utf-8"))
    pages = payload.get("query", {}).get("pages", [])
    requested_by_key = {media_name_key(name): name for name in filenames}
    if len(requested_by_key) != len(filenames):
        raise RuntimeError("unit media contains duplicate underscore/space-equivalent filenames")
    pages_by_key: dict[str, dict[str, Any]] = {}
    for page in pages:
        canonical_filename = page["title"].removeprefix("File:")
        key = media_name_key(canonical_filename)
        if key in pages_by_key:
            raise RuntimeError("Commons returned duplicate underscore/space-equivalent image titles")
        pages_by_key[key] = page
    if set(pages_by_key) != set(requested_by_key):
        raise RuntimeError(
            "Commons image title closure mismatch: "
            f"missing={sorted(set(requested_by_key) - set(pages_by_key))}; "
            f"extra={sorted(set(pages_by_key) - set(requested_by_key))}"
        )

    rights_by_key = {
        media_name_key(row["title"].removeprefix("File:")): row
        for row in rights_rows
    }

    assets: list[dict[str, Any]] = []
    for occurrence_filename in filenames:
        key = media_name_key(occurrence_filename)
        page = pages_by_key[key]
        filename = page["title"].removeprefix("File:")
        imageinfo = page.get("imageinfo") or []
        if len(imageinfo) != 1:
            raise RuntimeError(f"expected one current Commons imageinfo row for {filename}")
        info = imageinfo[0]
        frozen = rights_by_key.get(key)
        if not frozen:
            raise RuntimeError(f"unit media absent from frozen whole-course rights manifest: {filename}")
        current_license = ext_value(info, "LicenseShortName")
        current_license_url = ext_value(info, "LicenseUrl")
        current_artist = ext_value(info, "Artist")
        current_credit = ext_value(info, "Credit")
        current_artist_identity = artist_identity(current_artist)
        frozen_artist_identity = artist_identity(frozen["artist_html"])
        current_attribution = ext_value(info, "AttributionRequired").lower()
        current_copyrighted = ext_value(info, "Copyrighted")
        comparisons = {
            "bytes": int(info["size"]) == int(frozen["bytes"]),
            "sha1": info["sha1"] == frozen["commons_sha1_hex"],
            "mime": info["mime"] == frozen["mime"],
            "license": current_license == frozen["license"],
            "license_url": current_license_url == frozen["license_url"],
            "artist_html": current_artist == frozen["artist_html"],
            "artist_identity": current_artist_identity == frozen_artist_identity,
            "credit_html": current_credit == frozen["credit_html"],
            "attribution_required": current_attribution == frozen["attribution_required"].lower(),
            "copyrighted": current_copyrighted == frozen["copyrighted"],
        }
        # ExtMetadata Artist and Credit contain localized connective prose
        # (for example, "in der Wikipedia auf Englisch" / "at English
        # Wikipedia" and "Eigenes Werk" / "Own work"). Preserve both exact
        # values, but bind the admission gate to rights-bearing fields and a
        # locale-stable creator identity rather than localized wrapper text.
        rights_critical_fields = (
            "bytes",
            "sha1",
            "mime",
            "license",
            "license_url",
            "artist_identity",
            "attribution_required",
            "copyrighted",
        )
        rights_critical_match = all(comparisons[key] for key in rights_critical_fields)
        if not rights_critical_match:
            raise RuntimeError(f"current Commons rights metadata differs from frozen row for {filename}: {comparisons}")

        binary_path = root / "authority/media" / filename
        binary, download_receipt = download_binary(binary_path, info["url"].split("?", 1)[0])
        if len(binary) != int(info["size"]) or sha(binary, "sha1") != info["sha1"]:
            raise RuntimeError(f"downloaded binary differs from current Commons imageinfo: {filename}")
        assets.append(
            {
                "filename": filename,
                "commons_pageid": page["pageid"],
                "commons_lastrevid": page.get("lastrevid"),
                "commons_touched": page.get("touched"),
                "image_timestamp": info.get("timestamp"),
                "image_user": info.get("user"),
                "description_url": info["descriptionurl"],
                "original_url": info["url"].split("?", 1)[0],
                "mime": info["mime"],
                "width": int(info["width"]),
                "height": int(info["height"]),
                "bytes": int(info["size"]),
                "commons_sha1": info["sha1"],
                "sha256": sha(binary),
                "license": current_license,
                "license_url": current_license_url or None,
                "usage_terms": ext_value(info, "UsageTerms") or None,
                "attribution_required": current_attribution == "true",
                "copyrighted_status": current_copyrighted,
                "artist_html": current_artist,
                "artist_text": plain_html(current_artist),
                "artist_identity": current_artist_identity,
                "frozen_artist_html": frozen["artist_html"],
                "frozen_artist_text": plain_html(frozen["artist_html"]),
                "frozen_artist_identity": frozen_artist_identity,
                "credit_html": current_credit,
                "credit_text": plain_html(current_credit),
                "frozen_credit_html": frozen["credit_html"],
                "frozen_credit_text": plain_html(frozen["credit_html"]),
                "binary": file_entry(binary_path, root),
                "download_receipt": download_receipt,
                "current_matches_frozen_rights_manifest": comparisons,
                "rights_critical_fields_match": rights_critical_match,
                "localized_artist_variance": not comparisons["artist_html"],
                "localized_credit_variance": not comparisons["credit_html"],
                "occurrences": [
                    item
                    for item in occurrences
                    if media_name_key(str(item["filename"])) == key
                ],
            }
        )
    return {
        "occurrence_count": len(occurrences),
        "unique_asset_count": len(assets),
        "surface_occurrences": occurrences,
        "rights_manifest": file_entry(rights_path, root),
        "current_commons_api": COMMONS_API,
        "current_commons_query": file_entry(query_path, root),
        "current_commons_query_request_receipt": file_entry(
            query_path.with_suffix(query_path.suffix + ".request.json"), root
        ),
        "query_retrieved_utc": query_receipt["retrieved_utc"],
        "assets": assets,
        "all_displayed_images_have_license_macros": True,
    }


def md_escape(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def render_markdown(manifest: dict[str, Any]) -> str:
    unit = manifest["unit"]
    authority = manifest["authority"]
    expansions = manifest["expansions"]
    solutions = manifest["solutions"]
    media = manifest["media"]
    lines = [
        f"# Unit {unit} authority preflight",
        "",
        f"Status: **{manifest['status'].upper()}**. This boundary freezes authority only; no Indonesian translation is present.",
        "",
        "## Exact root and `/latex` identities",
        "",
        "| Surface | Page ID | Revision | Timestamp | MediaWiki SHA-1 (base36) | UTF-8 bytes |",
        "|---|---:|---:|---|---|---:|",
    ]
    for key in ("lecture_root", "worksheet_root", "lecture_latex", "worksheet_latex"):
        item = authority["pages"][key]
        lines.append(
            f"| {md_escape(key)} | {item['pageid']} | {item['revid']} | "
            f"{item['timestamp']} | `{item['mediawiki_sha1_base36']}` | {item['source_utf8_bytes']} |"
        )
    if authority.get("root_revision_overrides"):
        root_identity_note = (
            "The recursive export remains the four-surface baseline, but each explicitly listed root override "
            "is an exact later official revision frozen through a request-bound MediaWiki API response. "
            "Both the superseded export witness and the adopted root witness remain hash-bound; the page table "
            "shows the revision actually admitted for this unit."
        )
    else:
        root_identity_note = (
            "The root identities come from the already-frozen recursive export and selected-revision manifests. "
            "Each of the four page bodies now also has an exact UTF-8 base64 witness, a readable normalized witness, and hash-bound metadata."
        )
    lines.extend(
        [
            "",
            root_identity_note,
            "",
            "## Official expanded LaTeX",
            "",
            "| Surface | Saved API response | Sanitized German TeX |",
            "|---|---|---|",
        ]
    )
    for key in ("lecture", "worksheet"):
        item = expansions[key]
        response = item["response"]
        source = item["sanitized_source"]
        lines.append(
            f"| {key.title()} {unit} | `{response['path']}`; {response['bytes']} B; `{response['sha256']}` | "
            f"`{source['path']}`; {source['bytes']} B; `{source['sha256']}` |"
        )
    lines.extend(
        [
            "",
            "The official `/latex` pages are nine-byte `{{Latex}}` invocations, so their page revisions alone do not freeze expanded mathematics. "
            "The byte-exact official API responses, request receipts, deterministic sanitation receipts, and UTF-8 German TeX witnesses are all retained.",
            "",
            "## Worksheet exercise and solution census",
            "",
            f"Exercise count: **{solutions['exercise_count']}**; graded: **{solutions['graded_exercise_count']}**; "
            f"practice: **{solutions['practice_exercise_count']}**; graded-point total: **{solutions['point_value_total']}**; "
            f"source-supplied solutions: **{solutions['supplied_solution_count']}**; missing candidates: **{solutions['missing_solution_count']}**.",
            "",
            "| # | Exact task title | Root marker | Points | Expanded solution marker | Current `/Lösung` | Revision |",
            "|---:|---|---|---:|---|---|---:|",
        ]
    )
    for exercise in solutions["exercises"]:
        lines.append(
            f"| {exercise['exercise_index']} | {md_escape(exercise['task_title'])} | "
            f"{md_escape(exercise['root_point_marker'] or '—')} | "
            f"{md_escape(exercise['point_value'] if exercise['point_value'] is not None else '—')} | "
            f"{'yes' if exercise['solution_marker'] else 'no'} | "
            f"{'exists' if exercise['exists'] else 'missing'} | "
            f"{exercise.get('revid', '—')} |"
        )
    lines.extend(
        [
            "",
            "All candidate solution titles were queried in one exact current-revision closure. "
            "Every existing solution has a lossless source witness, current revision metadata, official expanded LaTeX response, sanitized German TeX, and sanitation receipt. "
            f"Macro/API agreement: **{str(solutions['macro_api_agreement']).lower()}**. All worksheet hint fields blank: **{str(manifest['structure']['all_hint_fields_blank']).lower()}**.",
            "",
            "## Unit media closure",
            "",
            f"Displayed/licensed occurrences: **{media['occurrence_count']}**; unique admitted binaries: **{media['unique_asset_count']}**.",
            "",
        ]
    )
    if media["assets"]:
        lines.extend(
            [
                "| File | Surface(s) | Creator | License/status | License URL | Bytes | SHA-1 | SHA-256 | Commons revision |",
                "|---|---|---|---|---|---:|---|---|---:|",
            ]
        )
        for asset in media["assets"]:
            surfaces = ", ".join(item["surface"] for item in asset["occurrences"])
            license_url = asset["license_url"] or "—"
            lines.append(
                f"| {md_escape(asset['filename'])} | {md_escape(surfaces)} | {md_escape(asset['artist_text'])} | "
                f"{md_escape(asset['license'])}; copyrighted={md_escape(asset['copyrighted_status'])}; "
                f"attribution={str(asset['attribution_required']).lower()} | {md_escape(license_url)} | "
                f"{asset['bytes']} | `{asset['commons_sha1']}` | `{asset['sha256']}` | {asset['commons_lastrevid']} |"
            )
    else:
        lines.append("No `\\includegraphics`/`\\bildlizenz` occurrence exists in the lecture, worksheet, or supplied-solution expansion; the exact media set is empty.")
    lines.extend(
        [
            "",
            "Every displayed image is paired with the source `\\bildlizenz` macro. Current Commons rights-critical metadata and creator identity agree with the frozen whole-course row, and each admitted binary matches current size and SHA-1; SHA-256 is recorded locally. Exact localized credit HTML is preserved on both sides and may differ only by API interface language.",
            "",
            "## Gate",
            "",
            "- Root and surface revision/export bindings: pass.",
            "- Official expansion preservation and deterministic sanitation: pass.",
            "- Complete exercise, point, hint, marker, and candidate-solution census: pass.",
            "- Every actually supplied solution frozen at source/revision/expanded-TeX granularity: pass.",
            "- Exact lecture/worksheet/solution media and rights closure: pass.",
            "- Translation started by this workflow: no.",
            "",
            f"Production gate: **{manifest['status'].upper()}**. The next action is the complete Indonesian translation of Lecture {unit}, Worksheet {unit}, and exactly the frozen supplied solutions, preserving the admitted media and source indices.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--unit", type=int, required=True, choices=range(1, 30))
    parser.add_argument("--lecture-root-revid", type=int)
    parser.add_argument("--worksheet-root-revid", type=int)
    args = parser.parse_args()
    root = args.root.resolve()
    unit = args.unit
    unit_tag = f"unit{unit:02d}"
    qa_dir = root / f"qa/unit-{unit:02d}"
    qa_dir.mkdir(parents=True, exist_ok=True)

    recursive_xml = root / "authority/mediawiki/brenner_course_recursive_current.xml"
    latex_xml = root / "authority/mediawiki/brenner_latex_kontrolle_recursive_current.xml"
    root_manifest_path = root / "authority/brenner_selected_root_revisions.csv"
    surface_manifest_path = root / "authority/brenner_selected_surface_revisions.csv"
    roots = csv_rows(root_manifest_path)
    surfaces = csv_rows(surface_manifest_path)
    lecture_root_title = f"{COURSE}/Vorlesung {unit}"
    worksheet_root_title = f"{COURSE}/Arbeitsblatt {unit}"
    lecture_surface_title = lecture_root_title + "/latex"
    worksheet_surface_title = worksheet_root_title + "/latex"
    selected = {
        "lecture_root": unique_row(roots, lecture_root_title),
        "worksheet_root": unique_row(roots, worksheet_root_title),
        "lecture_latex": unique_row(surfaces, lecture_surface_title),
        "worksheet_latex": unique_row(surfaces, worksheet_surface_title),
    }
    expected_exports = {
        recursive_xml.name: sha(recursive_xml.read_bytes()),
        latex_xml.name: sha(latex_xml.read_bytes()),
    }
    for row in selected.values():
        if expected_exports.get(row["source_export_file"]) != row["source_export_sha256"]:
            raise RuntimeError(f"selected manifest/export hash mismatch for {row['title']}")

    page_records: dict[str, Any] = {}
    page_records["lecture_root"], lecture_root_text = freeze_xml_witness(
        root,
        recursive_xml,
        selected["lecture_root"],
        f"lecture{unit:02d}_root_revid{selected['lecture_root']['revid']}",
    )
    page_records["worksheet_root"], worksheet_root_text = freeze_xml_witness(
        root,
        recursive_xml,
        selected["worksheet_root"],
        f"worksheet{unit:02d}_root_revid{selected['worksheet_root']['revid']}",
    )
    page_records["lecture_latex"], _ = freeze_xml_witness(
        root,
        latex_xml,
        selected["lecture_latex"],
        f"lecture{unit:02d}_latex_surface_revid{selected['lecture_latex']['revid']}",
    )
    page_records["worksheet_latex"], _ = freeze_xml_witness(
        root,
        latex_xml,
        selected["worksheet_latex"],
        f"worksheet{unit:02d}_latex_surface_revid{selected['worksheet_latex']['revid']}",
    )

    lecture_root_baseline_text = lecture_root_text
    worksheet_root_baseline_text = worksheet_root_text

    root_revision_baselines: dict[str, Any] = {}
    root_revision_overrides: dict[str, Any] = {}
    if args.lecture_root_revid is not None:
        root_revision_baselines["lecture_root"] = page_records["lecture_root"]
        adopted, lecture_root_text = freeze_api_revision_witness(
            root,
            lecture_root_title,
            args.lecture_root_revid,
            f"lecture{unit:02d}_root_override_revid{args.lecture_root_revid}",
        )
        if adopted["pageid"] != page_records["lecture_root"]["pageid"]:
            raise RuntimeError("lecture root override changed the page identity")
        page_records["lecture_root"] = adopted
        root_revision_overrides["lecture_root"] = {
            "baseline_revid": int(selected["lecture_root"]["revid"]),
            "adopted_revid": args.lecture_root_revid,
            "basis": "explicit exact official revision newer than the recursive-export baseline",
            "api_response": adopted["source_api_response"],
            "api_request_receipt": adopted["source_api_request_receipt"],
            "official_revision_compare": freeze_revision_compare(
                root,
                f"lecture{unit:02d}_root_revid{selected['lecture_root']['revid']}_to_{args.lecture_root_revid}_compare",
                int(selected["lecture_root"]["revid"]),
                args.lecture_root_revid,
            ),
        }
    if args.worksheet_root_revid is not None:
        root_revision_baselines["worksheet_root"] = page_records["worksheet_root"]
        adopted, worksheet_root_text = freeze_api_revision_witness(
            root,
            worksheet_root_title,
            args.worksheet_root_revid,
            f"worksheet{unit:02d}_root_override_revid{args.worksheet_root_revid}",
        )
        if adopted["pageid"] != page_records["worksheet_root"]["pageid"]:
            raise RuntimeError("worksheet root override changed the page identity")
        page_records["worksheet_root"] = adopted
        root_revision_overrides["worksheet_root"] = {
            "baseline_revid": int(selected["worksheet_root"]["revid"]),
            "adopted_revid": args.worksheet_root_revid,
            "basis": "explicit exact official revision newer than the recursive-export baseline",
            "api_response": adopted["source_api_response"],
            "api_request_receipt": adopted["source_api_request_receipt"],
            "official_revision_compare": freeze_revision_compare(
                root,
                f"worksheet{unit:02d}_root_revid{selected['worksheet_root']['revid']}_to_{args.worksheet_root_revid}_compare",
                int(selected["worksheet_root"]["revid"]),
                args.worksheet_root_revid,
            ),
        }

    lecture_expansion = freeze_expansion(
        root,
        root / "authority/exports" / f"lecture{unit:02d}_latex_expand.json",
        root / "authority/expanded" / f"lecture{unit:02d}_source.de.tex",
        qa_dir / f"lecture{unit:02d}_sanitize.json",
        lecture_surface_title,
    )
    worksheet_expansion = freeze_expansion(
        root,
        root / "authority/exports" / f"worksheet{unit:02d}_latex_expand.json",
        root / "authority/expanded" / f"worksheet{unit:02d}_source.de.tex",
        qa_dir / f"worksheet{unit:02d}_sanitize.json",
        worksheet_surface_title,
    )
    if "lecture_root" in root_revision_overrides:
        root_revision_overrides["lecture_root"]["transition_receipt"] = (
            freeze_root_override_transition(
                root,
                unit,
                "lecture",
                lecture_root_title,
                lecture_surface_title,
                root_revision_baselines["lecture_root"],
                lecture_root_baseline_text,
                page_records["lecture_root"],
                lecture_root_text,
                lecture_expansion,
            )
        )
    if "worksheet_root" in root_revision_overrides:
        root_revision_overrides["worksheet_root"]["transition_receipt"] = (
            freeze_root_override_transition(
                root,
                unit,
                "worksheet",
                worksheet_root_title,
                worksheet_surface_title,
                root_revision_baselines["worksheet_root"],
                worksheet_root_baseline_text,
                page_records["worksheet_root"],
                worksheet_root_text,
                worksheet_expansion,
            )
        )
    lecture_text = (root / lecture_expansion["sanitized_source"]["path"]).read_text(encoding="utf-8")
    worksheet_text = (root / worksheet_expansion["sanitized_source"]["path"]).read_text(encoding="utf-8")
    exercises = parse_tasks(worksheet_root_text, worksheet_text)
    solution_manifest, supplied_expansions = freeze_solution_closure(root, unit, exercises)

    solution_surface_texts = []
    for item in supplied_expansions:
        source_path = root / item["expansion"]["sanitized_source"]["path"]
        solution_surface_texts.append(
            (f"worksheet{unit:02d}_solution{item['exercise_index']:02d}", source_path.read_text(encoding="utf-8"))
        )
    media = freeze_media(
        root,
        unit,
        [
            (f"lecture{unit:02d}", lecture_text),
            (f"worksheet{unit:02d}", worksheet_text),
            *solution_surface_texts,
        ],
    )
    all_hints_blank = all(item["hint_field"] == "" for item in exercises)
    checks = {
        "root_revision_bindings_unique": True,
        "surface_revision_bindings_unique": True,
        "revision_export_hashes_match": True,
        "root_witnesses_match_mediawiki_sha1": True,
        "lecture_expansion_sanitized": True,
        "worksheet_expansion_sanitized": True,
        "exercise_root_expansion_count_agreement": True,
        "all_point_markers_resolved": True,
        "all_candidate_solution_titles_queried": True,
        "solution_macro_api_agreement": solution_manifest["macro_api_agreement"],
        "all_supplied_solution_revisions_frozen": True,
        "all_supplied_solution_latex_snapshots_frozen": True,
        "all_displayed_images_have_license_macros": media["all_displayed_images_have_license_macros"],
        "unit_media_binary_and_rights_closure": True,
        "translation_started_by_workflow": False,
    }
    status = "pass" if all(value is True for key, value in checks.items() if key != "translation_started_by_workflow") else "fail"
    manifest = {
        "schema_version": 1,
        "workflow": f"o011-{unit_tag}-authority-preflight-v1",
        "unit": unit,
        "scope": f"Brenner Differentialgeometrie Unit {unit} authority preflight; no translation",
        "authority": {
            "course_recursive_export": file_entry(recursive_xml, root),
            "latex_surface_recursive_export": file_entry(latex_xml, root),
            "root_revision_manifest": file_entry(root_manifest_path, root),
            "surface_revision_manifest": file_entry(surface_manifest_path, root),
            "pages": page_records,
            "root_revision_baselines": root_revision_baselines,
            "root_revision_overrides": root_revision_overrides,
        },
        "expansions": {"lecture": lecture_expansion, "worksheet": worksheet_expansion},
        "structure": {
            "lecture_section_count": len(SECTION_MACRO_RE.findall(lecture_text)),
            "worksheet_section_count": len(SECTION_MACRO_RE.findall(worksheet_text)),
            "worksheet_exercise_count": len(exercises),
            "worksheet_graded_count": solution_manifest["graded_exercise_count"],
            "worksheet_practice_count": solution_manifest["practice_exercise_count"],
            "worksheet_point_total": solution_manifest["point_value_total"],
            "worksheet_solution_bearing_indices": solution_manifest["supplied_solution_indices"],
            "all_hint_fields_blank": all_hints_blank,
        },
        "solutions": solution_manifest,
        "media": media,
        "checks": checks,
        "status": status,
        "next_action": (
            f"Translate Lecture {unit}, Worksheet {unit}, and exactly the "
            f"{solution_manifest['supplied_solution_count']} supplied solutions in source order."
        ),
    }
    json_path = qa_dir / "AUTHORITY_PREFLIGHT.json"
    md_path = qa_dir / "AUTHORITY_PREFLIGHT.md"
    write_generated(json_path, canonical_json(manifest))
    write_generated(md_path, render_markdown(manifest).encode("utf-8"))
    print(
        json.dumps(
            {
                "status": status,
                "unit": unit,
                "exercises": len(exercises),
                "graded": solution_manifest["graded_exercise_count"],
                "points": solution_manifest["point_value_total"],
                "solutions": solution_manifest["supplied_solution_indices"],
                "media": [asset["filename"] for asset in media["assets"]],
                "preflight_json": file_entry(json_path, root),
                "preflight_md": file_entry(md_path, root),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
