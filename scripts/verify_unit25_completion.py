#!/usr/bin/env python3
"""Close the bounded Unit 25 authority/translation surface."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
QA = ROOT / "qa/unit-25"
UNIT = ROOT / "source/units/unit-25"
AUTHORITY = ROOT / "authority/expanded"

SURFACES = [
    ("lecture25_source.de.tex", "lecture25.id.tex", "lecture25_translation.json"),
    ("worksheet25_source.de.tex", "worksheet25.id.tex", "worksheet25_translation.json"),
    *[
        (
            f"worksheet25_exercise{index:02d}_solution_source.de.tex",
            f"worksheet25_exercise{index:02d}_solution.id.tex",
            f"worksheet25_exercise{index:02d}_solution_translation.json",
        )
        for index in (1, 7, 8, 11, 12, 14)
    ],
]

FORBIDDEN_MARKERS = (
    "PERLU_TERJEMAHAN",
    "ZXQ",
    "\ufffd",
    "manifold terdiferensiasi",
    "bundel vektor terdiferensiasi",
    "horizontal penampang",
    "Christoffele",
    "peta terdiferensiasi",
    "fungsi terdiferensiasi",
    "penampang terdiferensiasi",
)
GERMAN_PROSE = re.compile(
    r"\b(?:Es|sei|eine|einen|einer|einem|eines|Zeige|Bestimme|Beschreibe|"
    r"Wir|Dies|Diese|Daher|Somit|Nach|Folgt|Klar|gilt|ist|sind|wird|werden|"
    r"für|und|oder|wenn|genau|gegeben|liegt|Aufgabe|Bemerkung|Satz|Fakt|"
    r"Zusammenhang|Mannigfaltigkeit|Vektorbündel|Schnitt|Abbildung)\b"
)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def entry(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    return {"path": relative(path), "bytes": len(data), "sha256": sha(data)}


def prose_only(text: str) -> str:
    text = re.sub(r"\[\[.*?\]\]", "", text, flags=re.DOTALL)
    text = re.sub(r"\\inputfaktbeweis\s*\{[^{}]*\}", "", text)
    return text


def main() -> None:
    preflight_path = QA / "AUTHORITY_PREFLIGHT.json"
    preflight = json.loads(preflight_path.read_text(encoding="utf-8"))
    structure = preflight["structure"]
    solutions = preflight["solutions"]
    media = preflight["media"]
    required_authority = {
        "status": preflight["status"],
        "exercise_count": structure["worksheet_exercise_count"],
        "graded_count": structure["worksheet_graded_count"],
        "practice_count": structure["worksheet_practice_count"],
        "point_total": structure["worksheet_point_total"],
        "hint_count": structure["worksheet_hint_count"],
        "hint_indices": structure["worksheet_hint_bearing_indices"],
        "supplied_solution_count": solutions["supplied_solution_count"],
        "supplied_solution_indices": solutions["supplied_solution_indices"],
        "media_occurrence_count": media["occurrence_count"],
        "media_unique_asset_count": media["unique_asset_count"],
    }
    expected_authority = {
        "status": "pass",
        "exercise_count": 25,
        "graded_count": 4,
        "practice_count": 21,
        "point_total": 15,
        "hint_count": 0,
        "hint_indices": [],
        "supplied_solution_count": 6,
        "supplied_solution_indices": [1, 7, 8, 11, 12, 14],
        "media_occurrence_count": 0,
        "media_unique_asset_count": 0,
    }
    if required_authority != expected_authority:
        raise RuntimeError(f"Unit 25 authority census changed: {required_authority}")

    worksheet = (UNIT / "worksheet25.id.tex").read_text(encoding="utf-8")
    exercise_count = len(
        re.findall(r"\\inputaufgabe(?:gibtloesung)?\b", worksheet)
    )
    marker_count = len(re.findall(r"\\inputaufgabegibtloesung\b", worksheet))
    if (exercise_count, marker_count) != (25, 6):
        raise RuntimeError(
            f"translated worksheet census changed: {(exercise_count, marker_count)}"
        )

    files: list[dict[str, object]] = []
    receipts: list[dict[str, object]] = []
    residuals: list[dict[str, object]] = []
    link_destination_count = 0
    for source_name, target_name, receipt_name in SURFACES:
        source_path = AUTHORITY / source_name
        target_path = UNIT / target_name
        receipt_path = QA / receipt_name
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        target_bytes = target_path.read_bytes()
        source_bytes = source_path.read_bytes()
        if receipt.get("status") != "pass":
            raise RuntimeError(f"nonpassing translation receipt: {receipt_name}")
        if receipt.get("source_sha256") != sha(source_bytes):
            raise RuntimeError(f"stale source binding: {receipt_name}")
        if receipt.get("target_sha256") != sha(target_bytes):
            raise RuntimeError(f"stale target binding: {receipt_name}")
        text = target_bytes.decode("utf-8")
        source_text = source_bytes.decode("utf-8")
        source_link_destinations = re.findall(r"\[\[([^]|]+)", source_text)
        target_link_destinations = re.findall(r"\[\[([^]|]+)", text)
        if source_link_destinations != target_link_destinations:
            raise RuntimeError(f"link-destination sequence changed: {target_name}")
        link_destination_count += len(target_link_destinations)
        for marker in FORBIDDEN_MARKERS:
            if marker in text:
                residuals.append({"path": relative(target_path), "marker": marker})
        stripped = prose_only(text)
        if re.search(r"[ÄÖÜäöüß]", stripped):
            residuals.append(
                {"path": relative(target_path), "marker": "German umlaut in prose"}
            )
        match = GERMAN_PROSE.search(stripped)
        if match:
            residuals.append(
                {
                    "path": relative(target_path),
                    "marker": f"German prose token: {match.group(0)}",
                }
            )
        files.append(entry(target_path))
        receipts.append(entry(receipt_path))
    if residuals:
        raise RuntimeError(f"residual-language gate failed: {residuals}")

    pages = preflight["authority"]["pages"]
    payload = {
        "schema_version": 1,
        "workflow": "o011-unit25-bounded-translation-completion-v1",
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "unit": 25,
        "status": "pass",
        "authority_preflight": entry(preflight_path),
        "authority_roots": {
            "lecture": {
                "pageid": pages["lecture_root"]["pageid"],
                "revid": pages["lecture_root"]["revid"],
                "timestamp": pages["lecture_root"]["timestamp"],
                "mediawiki_sha1_base36": pages["lecture_root"][
                    "mediawiki_sha1_base36"
                ],
            },
            "worksheet": {
                "pageid": pages["worksheet_root"]["pageid"],
                "revid": pages["worksheet_root"]["revid"],
                "timestamp": pages["worksheet_root"]["timestamp"],
                "mediawiki_sha1_base36": pages["worksheet_root"][
                    "mediawiki_sha1_base36"
                ],
            },
        },
        "census": expected_authority,
        "translated_surface_count": len(SURFACES),
        "translated_exercise_count": exercise_count,
        "translated_solution_marker_count": marker_count,
        "preserved_link_destination_count": link_destination_count,
        "translated_files": files,
        "translation_receipts": receipts,
        "checks": {
            "all_translation_topology_math_receipts_pass_and_current": True,
            "worksheet_exercise_and_solution_marker_counts_match_authority": True,
            "all_source_supplied_solutions_translated": True,
            "all_source_hint_surfaces_translated": True,
            "source_hint_surface_count": 0,
            "link_destination_sequences_exact": True,
            "residual_draft_markers_absent": True,
            "known_bad_terminology_forms_absent": True,
            "german_prose_candidates_absent_after_locator_stripping": True,
            "utf8_without_replacement_character": True,
        },
    }
    output = QA / "TRANSLATION_COMPLETION.json"
    output.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(entry(output), ensure_ascii=False))


if __name__ == "__main__":
    main()
