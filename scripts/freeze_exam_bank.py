#!/usr/bin/env python3
"""Freeze the official ten-form Brenner examination bank, once and exactly.

This is deliberately bounded to the official Differentialgeometrie exam index,
its ten learner roots, ten solution-form roots, their LaTeX contexts, and the
recursive template/transclusion closure returned by MediaWiki Special:Export.
It never rewrites an existing differing frozen response.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import freeze_unit_authority as fua


INDEX = "Kurs:Differentialgeometrie/Klausuren"
EXPORT_ENDPOINT = "https://de.wikiversity.org/wiki/Spezial:Exportieren"
NS = "{http://www.mediawiki.org/xml/export-0.11/}"
TASK_LINE_RE = re.compile(r"(?m)^\|([^|\n]+?/Aufgabe)\|([^|\n]*)\|")
TASK_MACRO_RE = re.compile(r"(?m)^\\(inputaufgabegibtloesung|inputaufgabe)\s*\n\{([^{}\n]*)\}")
EXAM_SANITIZER_PROFILE = "brenner-exam-presentational-em-v1"


def run_exam_sanitizer(
    root: Path, response: Path, output: Path, receipt: Path
) -> Path:
    """Run the strict generic sanitizer, falling back only to the exam profile.

    The fallback accepts exactly balanced, non-nested, attribute-free ``em``
    pairs and still rejects every other residual HTML tag.  Existing frozen
    output is validated rather than regenerated.
    """
    generic_script = root / "scripts/sanitize_brenner_expand.py"
    exam_script = root / "scripts/sanitize_brenner_exam_expand.py"
    if output.exists() or receipt.exists():
        if not output.exists() or not receipt.exists():
            raise RuntimeError(f"partial exam sanitizer state for {response}")
        saved = json.loads(receipt.read_text(encoding="utf-8"))
        if saved.get("input_sha256") != fua.sha(response.read_bytes()):
            raise RuntimeError(f"stale exam sanitizer input receipt: {receipt}")
        if saved.get("output_sha256") != fua.sha(output.read_bytes()):
            raise RuntimeError(f"stale exam sanitizer output receipt: {receipt}")
        profile = saved.get("sanitizer_profile")
        if profile is None:
            return generic_script
        if profile == EXAM_SANITIZER_PROFILE:
            return exam_script
        raise RuntimeError(f"unknown exam sanitizer profile in {receipt}: {profile!r}")

    base_command = [
        str(response),
        str(output),
        "--project-root",
        str(root),
        "--receipt",
        str(receipt),
    ]
    generic_result = subprocess.run(
        [sys.executable, str(generic_script), *base_command],
        check=False,
        capture_output=True,
        text=True,
    )
    if generic_result.returncode == 0:
        return generic_script
    if output.exists() or receipt.exists():
        raise RuntimeError(
            f"generic sanitizer left partial state for {response}; refusing fallback"
        )
    exam_result = subprocess.run(
        [sys.executable, str(exam_script), *base_command],
        check=False,
        capture_output=True,
        text=True,
    )
    if exam_result.returncode != 0:
        generic_detail = (generic_result.stderr or generic_result.stdout).strip().splitlines()
        exam_detail = (exam_result.stderr or exam_result.stdout).strip().splitlines()
        raise RuntimeError(
            "both strict exam sanitation paths failed: "
            f"generic={generic_detail[-1] if generic_detail else generic_result.returncode!r}; "
            f"exam={exam_detail[-1] if exam_detail else exam_result.returncode!r}"
        )
    return exam_script


def freeze_exam_expansion(
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
    response_bytes, request_receipt = fua.fetch_frozen_api(
        response_path, fua.WIKIVERSITY_API, parameters
    )
    payload = json.loads(response_bytes.decode("utf-8"))
    expanded = payload.get("expandtemplates", {}).get("wikitext")
    if not isinstance(expanded, str):
        raise RuntimeError(f"missing expandtemplates.wikitext in {response_path}")
    sanitizer_script = run_exam_sanitizer(
        root, response_path, output_path, receipt_path
    )
    output_text = output_path.read_text(encoding="utf-8")
    if "\ufffd" in output_text or fua.HTML_TAG_RE.search(output_text):
        raise RuntimeError(f"unsafe residue in sanitized exam source: {output_path}")
    return {
        "api_endpoint": fua.WIKIVERSITY_API,
        "parameters": parameters,
        "retrieved_utc": request_receipt["retrieved_utc"],
        "http_date": request_receipt.get("http_date"),
        "response": fua.file_entry(response_path, root),
        "request_receipt": fua.file_entry(
            response_path.with_suffix(response_path.suffix + ".request.json"), root
        ),
        "expanded_characters": len(expanded),
        "sanitized_source": fua.file_entry(output_path, root),
        "sanitizer_receipt": fua.file_entry(receipt_path, root),
        "sanitizer": fua.file_entry(sanitizer_script, root),
        "valid_utf8": True,
        "residual_html_tags": False,
        "replacement_characters": False,
    }


def rendered_task_slots(text: str) -> list[dict[str, Any]]:
    """Parse rendered learner slots from the frozen, sanitized LaTeX surface.

    Brenner's exam roots contain repeated relative template arguments that do
    not identify rendered problems by themselves.  The rendered learner form
    is authoritative for slot presence: a placeholder expands to an empty
    second argument of ``inputaufgabe``; an actual task has a non-empty second
    argument.  ``inputaufgabegibtloesung`` is the rendered solution-link
    signal used by the official template.
    """
    slots: list[dict[str, Any]] = []
    for slot_number, match in enumerate(TASK_MACRO_RE.finditer(text), 1):
        cursor = match.end()
        while cursor < len(text) and text[cursor].isspace():
            cursor += 1
        body, _ = fua.braced_argument(text, cursor)
        body_bytes = body.encode("utf-8")
        actual = bool(body.strip())
        macro = match.group(1)
        if not actual and (macro != "inputaufgabe" or match.group(2).strip() != "0"):
            raise RuntimeError(
                "unexpected nonstandard empty exam slot: "
                f"slot={slot_number}, macro={macro}, points={match.group(2)!r}"
            )
        slots.append(
            {
                "slot": slot_number,
                "macro": macro,
                "point_marker": match.group(2).strip(),
                "actual_problem": actual,
                "rendered_solution_link_present": (
                    actual and macro == "inputaufgabegibtloesung"
                ),
                "rendered_task_bytes": len(body_bytes),
                "rendered_task_sha256": fua.sha(body_bytes),
            }
        )
    return slots


def form_roots() -> list[dict[str, Any]]:
    return [
        {
            "form": number,
            "learner": f"Kurs:Differentialgeometrie/{number}/Klausur",
            "solutions": f"Kurs:Differentialgeometrie/{number}/Klausur mit Lösungen",
        }
        for number in range(1, 11)
    ]


def download_export(path: Path, titles: list[str]) -> dict[str, Any]:
    receipt_path = path.with_suffix(path.suffix + ".request.json")
    parameters = {"pages": "\n".join(titles), "templates": "1"}
    if path.exists():
        if not receipt_path.exists():
            raise RuntimeError(f"frozen export lacks request receipt: {path}")
        data = path.read_bytes()
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        if receipt.get("response_sha256") != fua.sha(data):
            raise RuntimeError(f"frozen export receipt mismatch: {path}")
        if receipt.get("parameters") != parameters:
            raise RuntimeError(f"frozen export request identity mismatch: {path}")
        return receipt

    body = urllib.parse.urlencode(parameters).encode("utf-8")
    request = urllib.request.Request(
        EXPORT_ENDPOINT,
        data=body,
        headers={
            "User-Agent": fua.USER_AGENT,
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Accept": "application/xml,text/xml",
        },
        method="POST",
    )
    last_error: Exception | None = None
    for attempt in range(6):
        try:
            with urllib.request.urlopen(request, timeout=240) as response:
                data = response.read()
                headers = {
                    "date": response.headers.get("Date", ""),
                    "content_type": response.headers.get("Content-Type", ""),
                }
            break
        except (urllib.error.URLError, TimeoutError) as exc:
            last_error = exc
            if attempt == 5:
                raise RuntimeError(f"recursive export failed: {last_error}") from exc
            time.sleep(min(3 * (attempt + 1), 20))
    else:
        raise RuntimeError(f"recursive export failed: {last_error}")
    if not data.startswith(b"<mediawiki"):
        raise RuntimeError("Special:Export did not return MediaWiki XML")
    receipt = {
        "schema_version": 1,
        "retrieved_utc": fua.utc_now(),
        "endpoint": EXPORT_ENDPOINT,
        "method": "POST",
        "parameters": parameters,
        "http_date": headers["date"],
        "content_type": headers["content_type"],
        "response_path": path.name,
        "response_bytes": len(data),
        "response_sha256": fua.sha(data),
    }
    fua.preserve_or_write(path, data)
    fua.preserve_or_write(receipt_path, fua.canonical_json(receipt))
    return receipt


def parse_export(path: Path) -> dict[str, dict[str, Any]]:
    root = ET.parse(path).getroot()
    pages: dict[str, dict[str, Any]] = {}
    for page in root.findall(f"{NS}page"):
        title = page.findtext(f"{NS}title") or ""
        pageid = int(page.findtext(f"{NS}id") or "0")
        revision = page.find(f"{NS}revision")
        if revision is None:
            raise RuntimeError(f"export page lacks revision: {title}")
        text_node = revision.find(f"{NS}text")
        text = text_node.text if text_node is not None and text_node.text else ""
        text_bytes = text.encode("utf-8")
        pages[title] = {
            "pageid": pageid,
            "revid": int(revision.findtext(f"{NS}id") or "0"),
            "timestamp": revision.findtext(f"{NS}timestamp") or "",
            "sha1": revision.findtext(f"{NS}sha1") or "",
            "text": text,
            "text_bytes": len(text_bytes),
            "text_sha256": fua.sha(text_bytes),
        }
    return pages


def root_revision_query(root: Path, titles: list[str]) -> dict[str, Any]:
    path = root / "authority/exams/mediawiki/exam_control_pages_current.json"
    parameters = {
        "action": "query",
        "format": "json",
        "formatversion": "2",
        "prop": "revisions",
        "rvprop": "ids|timestamp|sha1|content",
        "rvslots": "main",
        "titles": "|".join(titles),
    }
    data, receipt = fua.fetch_frozen_api(path, fua.WIKIVERSITY_API, parameters)
    payload = json.loads(data.decode("utf-8"))
    pages = payload.get("query", {}).get("pages", [])
    by_title: dict[str, Any] = {}
    for page in pages:
        revision = (page.get("revisions") or [{}])[0]
        by_title[page["title"]] = {
            "pageid": page.get("pageid"),
            "revid": revision.get("revid"),
            "timestamp": revision.get("timestamp"),
            "sha1": revision.get("sha1"),
            "missing": bool(page.get("missing")),
        }
    return {
        "response": fua.file_entry(path, root),
        "request_receipt": fua.file_entry(path.with_suffix(path.suffix + ".request.json"), root),
        "retrieved_utc": receipt["retrieved_utc"],
        "pages": by_title,
    }


def main() -> None:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd().resolve()
    forms = form_roots()
    solution_roots = [item["solutions"] for item in forms]
    export_path = root / "authority/exams/mediawiki/exam_bank_recursive_export.xml"
    export_receipt = download_export(export_path, solution_roots)
    pages = parse_export(export_path)

    control_titles = [INDEX]
    for item in forms:
        for key in ("learner", "solutions"):
            title = item[key]
            control_titles.extend([title, title + "/latex"])
    controls = root_revision_query(root, control_titles)

    expansion_entries: list[dict[str, Any]] = []
    occurrence_rows: list[dict[str, Any]] = []
    form_slot_census: list[dict[str, int]] = []
    for item in forms:
        number = item["form"]
        learner_page = pages.get(item["learner"])
        if learner_page is None:
            raise RuntimeError(f"recursive export misses learner root {item['learner']}")
        for kind in ("learner", "solutions"):
            title = item[kind]
            stem = f"exam{number:02d}_{kind}"
            response = root / f"authority/exams/mediawiki/{stem}_expandtemplates.json"
            output = root / f"authority/exams/expanded/{stem}_source.de.tex"
            sanitizer_receipt = root / f"qa/exams/{stem.upper()}_SANITIZE.json"
            entry = freeze_exam_expansion(
                root, response, output, sanitizer_receipt, title + "/latex"
            )
            text = output.read_text(encoding="utf-8")
            slots = rendered_task_slots(text) if kind == "learner" else []
            entry.update(
                {
                    "form": number,
                    "kind": kind,
                    "context_title": title + "/latex",
                    "task_macro_count": len(TASK_MACRO_RE.findall(text)),
                }
            )
            expansion_entries.append(entry)
            if kind == "learner":
                actual_slots = [slot for slot in slots if slot["actual_problem"]]
                solution_slots = [
                    slot for slot in actual_slots if slot["rendered_solution_link_present"]
                ]
                form_slot_census.append(
                    {
                        "form": number,
                        "nominal_slots": len(slots),
                        "actual_problem_occurrences": len(actual_slots),
                        "placeholder_slots": len(slots) - len(actual_slots),
                        "rendered_solution_link_occurrences": len(solution_slots),
                        "missing_solution_link_occurrences": (
                            len(actual_slots) - len(solution_slots)
                        ),
                    }
                )
                for occurrence, slot in enumerate(actual_slots, 1):
                    occurrence_rows.append(
                        {
                            "form": number,
                            "slot": slot["slot"],
                            "occurrence": occurrence,
                            "learner_macro": slot["macro"],
                            "point_marker": slot["point_marker"],
                            "rendered_task_bytes": slot["rendered_task_bytes"],
                            "rendered_task_sha256": slot["rendered_task_sha256"],
                            "source_solution_page_present": slot[
                                "rendered_solution_link_present"
                            ],
                            "solution_presence_evidence": (
                                "official rendered learner macro " + slot["macro"]
                            ),
                        }
                    )

    actual_occurrences = len(occurrence_rows)
    solution_occurrences = sum(
        1 for row in occurrence_rows if row["source_solution_page_present"]
    )
    unique_tasks = sorted({row["rendered_task_sha256"] for row in occurrence_rows})
    revision_rows = sorted(
        (title, item["pageid"], item["revid"], item["sha1"])
        for title, item in pages.items()
    )
    revision_digest = hashlib.sha256(
        json.dumps(revision_rows, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    occurrence_path = root / "authority/exams/EXAM_OCCURRENCE_MAP.json"
    fua.write_generated(occurrence_path, fua.canonical_json(occurrence_rows))
    manifest = {
        "schema_version": 1,
        "scope": "official ten-form Differentialgeometrie examination bank",
        "official_index": INDEX,
        "forms": 10,
        "recursive_export": fua.file_entry(export_path, root),
        "recursive_export_request": fua.file_entry(
            export_path.with_suffix(export_path.suffix + ".request.json"), root
        ),
        "recursive_page_count": len(pages),
        "revision_set_sha256": revision_digest,
        "control_pages": controls,
        "expansions": expansion_entries,
        "actual_problem_occurrences": actual_occurrences,
        "source_solution_occurrences": solution_occurrences,
        "missing_solution_occurrences": actual_occurrences - solution_occurrences,
        "unique_semantic_tasks": len(unique_tasks),
        "nominal_template_slots": sum(row["nominal_slots"] for row in form_slot_census),
        "placeholder_slots": sum(row["placeholder_slots"] for row in form_slot_census),
        "per_form_census": form_slot_census,
        "occurrence_map": fua.file_entry(occurrence_path, root),
        "expected_live_census_cross_check": {"actual": 123, "solutions": 117, "missing": 6},
        "census_matches_selection_evidence": (
            actual_occurrences == 123
            and solution_occurrences == 117
            and actual_occurrences - solution_occurrences == 6
        ),
        "export_request_retrieved_utc": export_receipt["retrieved_utc"],
    }
    manifest_path = root / "qa/exams/EXAM_BANK_AUTHORITY.json"
    fua.write_generated(manifest_path, fua.canonical_json(manifest))
    if not manifest["census_matches_selection_evidence"]:
        raise RuntimeError(
            "frozen exam census differs from the live selection evidence; inspect exact revisions"
        )
    print(json.dumps({
        "status": "pass",
        "manifest": fua.file_entry(manifest_path, root),
        "recursive_export": manifest["recursive_export"],
        "page_count": len(pages),
        "actual_occurrences": actual_occurrences,
        "solution_occurrences": solution_occurrences,
        "missing_solution_occurrences": actual_occurrences - solution_occurrences,
        "unique_semantic_tasks": len(unique_tasks),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
