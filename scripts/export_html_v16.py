#!/usr/bin/env python3
"""Build the deterministic O011 Indonesian semantic HTML reader through Unit 16.

This is a new publication boundary.  It deliberately imports the established
Unit 10 renderer instead of modifying it, refuses drift in the exact published
Unit 13 HTML baseline, binds the live Unit 14--16 translation and post-
correction QA receipts, and commits only after two independently staged trees
are byte-identical.
"""

from __future__ import annotations

import argparse
import html
import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import quote

import export_html_v10 as v10


SCHEMA_VERSION = 1
WORKFLOW = "o011-export-html-v16"
UNIT_COUNT = 16
MODEL_IDENTIFICATION = v10.MODEL_IDENTIFICATION
OFFICIAL_SOURCE = v10.OFFICIAL_SOURCE
MATHJAX_URL = v10.MATHJAX_URL
MATHJAX_CONFIG = r'''window.MathJax={tex:{inlineMath:[["\\(","\\)"]],displayMath:[["\\[","\\]"]],packages:{"[+]":["ams"]}},options:{enableMenu:true}};'''

UNIT_TITLES = {
    **v10.UNIT_TITLES,
    11: "Produk Manifold",
    12: "Bundel Vektor",
    13: "Konstruksi Bundel Vektor",
    14: "Bentuk Diferensial pada Manifold",
    15: "Integrasi pada Manifold",
    16: "Manifold Riemann",
}

EXPECTED_V13_EXPORTER = {
    "path": "scripts/export_html_v13.py",
    "bytes": 40497,
    "sha256": "d8052e5905ca1c40c1db8ae267341ebf488eb2004dd5c4e95bb1f3a04c0fd2a7",
}
EXPECTED_V13_VERIFIER = {
    "path": "scripts/verify_html_v13.py",
    "bytes": 31925,
    "sha256": "80ea80fb4c3fe5e2af0862342dcdbd824d1b11da10356c1bc3ce72fd0a1f444a",
}
EXPECTED_V13_READER_QA = {
    "path": "qa/unit-13/HTML_READER_QA.json",
    "bytes": 22249,
    "sha256": "8790767d395fc994779d4e349c38d3d99e8828c782ebf69ab32fa020d4d869d2",
}
EXPECTED_V13_ZENODO_READBACK = {
    "path": "qa/unit-13/ZENODO_PUBLIC_READBACK_RECEIPT_R1.json",
    "bytes": 4054,
    "sha256": "81944e806274dffeae4513b64185db9b45f062296b45dd5658ca75d677ac8082",
}
EXPECTED_V13_GITHUB_READBACK = {
    "path": "qa/unit-13/GITHUB_PUBLIC_READBACK_RECEIPT_R1.json",
    "bytes": 4519,
    "sha256": "0c1f7061114402df477ddcb7817b5746d8f22c82ef13f38a48eea373d28d0ad8",
}
EXPECTED_V13_PUBLIC_HTML_ZIP = {
    "path": "output/release-unit13-r1/geometri-diferensial-manifold-mulus-brenner-id-unit13-html-20260825.zip",
    "bytes": 5331749,
    "sha256": "22dacc34c9381c44aebeccf0c48e7cf107c991d7ff3c8c74ec4d950e77e77cf7",
}
EXPECTED_V13_OUTPUT_FILE_COUNT = 29
EXPECTED_V13_OUTPUT_INVENTORY_SHA256 = "583a7f904c6742c8afb00e4322f22720f36a366eb39c1308a6717d15c0d6ee0f"
EXPECTED_V13_ENTRY_SHA256 = "994c6caf59d87638b3b78583cc9765c2dd8feba42a1ba2ab2c2a9e02d068ebc8"
EXPECTED_V13_MANIFEST_SHA256 = "8e4cd88db27d77eb4f764aa71816ef15bf758387ccb050e99f383eb741db87da"
EXPECTED_V13_ZENODO_RECORD_ID = 22097422
EXPECTED_V13_GITHUB_COMMIT = "56f2b2b4d11592ecb311f7e317b92ae591f752ab"

EXPECTED_V10_EXPORTER = {
    "path": "scripts/export_html_v10.py",
    "bytes": 69665,
    "sha256": "c6d817de1af44236a826f954630bc5004b22b19c952d2b9c853c844164d61df1",
}
EXPECTED_V10_VERIFIER = {
    "path": "scripts/verify_html_v10.py",
    "bytes": 24862,
    "sha256": "00951165f42221f0dd7feeb14778e4dc6098cf6631efed8a5514c5821a660e43",
}
EXPECTED_V10_READER_QA = {
    "path": "qa/unit-10/HTML_READER_QA.json",
    "bytes": 5830,
    "sha256": "b5af7e5e5192b2c19aaeb940907cce58c8340f294d694f130965545d2c1defb9",
}
EXPECTED_V10_PUBLIC_READBACK = {
    "path": "qa/unit-10/ZENODO_PUBLIC_READBACK_RECEIPT.json",
    "bytes": 2351,
    "sha256": "575f2affc4bcdff66f2757da0551540c77c8a4c5a2cd4eb356bb5bb20c8c923c",
}
EXPECTED_V10_PUBLIC_HTML_ZIP = {
    "path": "output/release-unit10/geometri-diferensial-manifold-mulus-brenner-id-unit10-html-20260823.zip",
    "bytes": 1260239,
    "sha256": "6dbffc22f338eab537b42d907c2d6dae9bd2f00c045f7a690f5e96e652663b06",
}
EXPECTED_V10_OUTPUT_FILE_COUNT = 21
EXPECTED_V10_OUTPUT_INVENTORY_SHA256 = "7f676e5da89c377d2893c818447f65ff75a7fc970a91a3c8ffc4d961b059039b"
EXPECTED_V10_PUBLIC_RECORD_ID = 22073928

LINKED_ANIMATION_LABELS = {
    "Aufgabe75.22.1.gif": "Konstruksi objek-objek pada Soal 7.13.",
    "Aufgabe75.22.2.gif": "Variasi S dan perubahan panjang lintasan pada Soal 7.13.",
}
FILE_LINK_RE = re.compile(
    r"\[\[(?:File|Datei):([^\]|\r\n]+)\|(?:thumb\|)?([^\]\r\n]+)\]\]"
)

canonical_json = v10.canonical_json
file_binding = v10.file_binding
load_json_object = v10.load_json_object
safe_project_path = v10.safe_project_path
sha256_bytes = v10.sha256_bytes
write_text = v10.write_text
SurfaceState = v10.SurfaceState


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def tree_inventory(directory: Path) -> list[dict[str, Any]]:
    return [
        file_binding(path, directory)
        for path in sorted(item for item in directory.rglob("*") if item.is_file())
    ]


def inventory_sha256(inventory: list[dict[str, Any]]) -> str:
    return sha256_bytes(canonical_json(inventory).encode("utf-8"))


def source_files(root: Path, maximum_unit: int = UNIT_COUNT) -> list[Path]:
    paths: list[Path] = []
    for unit in range(1, maximum_unit + 1):
        tag = f"{unit:02d}"
        directory = root / f"source/units/unit-{tag}"
        lecture = directory / f"lecture{tag}.id.tex"
        worksheet = directory / f"worksheet{tag}.id.tex"
        expect(lecture.is_file() and worksheet.is_file(), f"missing translated reader surface for Unit {unit}")
        paths.extend((lecture, worksheet))
        paths.extend(sorted(directory.glob(f"worksheet{tag}_exercise*_solution.id.tex")))
    return paths


def unit_source_files(root: Path, unit: int) -> list[Path]:
    tag = f"{unit:02d}"
    directory = root / f"source/units/unit-{tag}"
    return [
        directory / f"lecture{tag}.id.tex",
        directory / f"worksheet{tag}.id.tex",
        *sorted(directory.glob(f"worksheet{tag}_exercise*_solution.id.tex")),
    ]


def solution_indices(root: Path, unit: int) -> list[int]:
    tag = f"{unit:02d}"
    result: list[int] = []
    for path in sorted((root / f"source/units/unit-{tag}").glob(f"worksheet{tag}_exercise*_solution.id.tex")):
        match = re.search(r"exercise(\d+)_solution", path.name)
        expect(match is not None, f"unrecognized solution filename: {path}")
        result.append(int(match.group(1)))
    expect(len(result) == len(set(result)), f"duplicate supplied-solution index in Unit {unit}")
    return result


def source_solution_marker_indices(path: Path) -> list[int]:
    exercises = list(re.finditer(r"\\(inputaufgabe(?:gibtloesung)?)\b", path.read_text(encoding="utf-8")))
    return [index for index, match in enumerate(exercises, 1) if match.group(1) == "inputaufgabegibtloesung"]


def translation_receipt_path(root: Path, target: Path) -> Path:
    unit_match = re.fullmatch(r"unit-(\d{2})", target.parent.name)
    expect(unit_match is not None, f"translation target is outside a unit directory: {target}")
    basename = target.name.removesuffix(".id.tex")
    return root / f"qa/unit-{unit_match.group(1)}/{basename}_translation.json"


def _strings(value: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(value, str):
        found.add(value)
    elif isinstance(value, dict):
        for key, item in value.items():
            found.add(str(key))
            found.update(_strings(item))
    elif isinstance(value, list):
        for item in value:
            found.update(_strings(item))
    return found


def unit_translation_bindings(root: Path, unit: int) -> list[dict[str, Any]]:
    bindings: list[dict[str, Any]] = []
    for target in unit_source_files(root, unit):
        expect(target.is_file(), f"missing translated source: {target.relative_to(root)}")
        receipt_path = translation_receipt_path(root, target)
        expect(receipt_path.is_file(), f"missing translation receipt: {receipt_path.relative_to(root)}")
        receipt = load_json_object(receipt_path)
        target_binding = file_binding(target, root)
        target_relative = target.relative_to(root).as_posix()
        expect(receipt.get("status") == "pass", f"translation receipt is not passing: {receipt_path.relative_to(root)}")
        expect(receipt.get("target") == target_relative, f"translation receipt targets a different file: {receipt_path.relative_to(root)}")
        expect(receipt.get("target_bytes") == target_binding["bytes"], f"translation target byte count is stale: {target_relative}")
        expect(receipt.get("target_sha256") == target_binding["sha256"], f"translation target SHA-256 is stale: {target_relative}")
        expect(receipt.get("failures") in (None, []), f"translation receipt retains failures: {receipt_path.relative_to(root)}")

        authority_relative = str(receipt.get("source", ""))
        authority_path = safe_project_path(root, authority_relative)
        expect(authority_path.is_file(), f"translation authority source is missing: {authority_relative}")
        authority_binding = file_binding(authority_path, root)
        expect(receipt.get("source_bytes") == authority_binding["bytes"], f"translation authority byte count is stale: {authority_relative}")
        expect(receipt.get("source_sha256") == authority_binding["sha256"], f"translation authority SHA-256 is stale: {authority_relative}")
        bindings.append({
            "target": target_binding,
            "authority_source": authority_binding,
            "translation_receipt": file_binding(receipt_path, root),
        })
    return bindings


def load_live_qa_bindings(root: Path, units: Iterable[int] = range(14, 17)) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for unit in units:
        tag = f"{unit:02d}"
        translations = unit_translation_bindings(root, unit)
        post_path = root / f"qa/unit-{tag}/POST_CORRECTION_MATH_QA.json"
        expect(post_path.is_file(), f"missing final Unit {unit} POST QA gate: {post_path.relative_to(root)}")
        post = load_json_object(post_path)
        expect(post.get("status") == "pass", f"Unit {unit} POST QA gate is not passing")
        expect(post.get("unit_id") == f"o011-brenner-u{tag}", f"Unit {unit} POST QA unit ID differs")
        evidence_strings = _strings(post)
        for item in translations:
            target = item["target"]
            receipt = item["translation_receipt"]
            expect(target["path"] in evidence_strings, f"Unit {unit} POST QA does not name {target['path']}")
            expect(target["sha256"] in evidence_strings, f"Unit {unit} POST QA does not bind {target['path']}")
            expect(receipt["sha256"] in evidence_strings, f"Unit {unit} POST QA does not bind {receipt['path']}")
            if receipt["path"] not in evidence_strings:
                # The immutable list-era Unit 14/15 receipts record a
                # solution translation-receipt SHA but omit its path.  Admit
                # that older representation only when the target entry is
                # unique and the deterministic target-to-receipt convention
                # resolves to the exact live receipt bytes.
                legacy_targets = post.get("targets")
                matches = [
                    value for value in legacy_targets or []
                    if isinstance(value, dict)
                    and value.get("path") == target["path"]
                    and value.get("translation_receipt_sha256") == receipt["sha256"]
                ] if isinstance(legacy_targets, list) else []
                expected_receipt = translation_receipt_path(root, safe_project_path(root, target["path"]))
                expect(len(matches) == 1 and expected_receipt.relative_to(root).as_posix() == receipt["path"], f"Unit {unit} POST QA does not name {receipt['path']}")
        result[tag] = {
            "post_correction_math_qa": file_binding(post_path, root),
            "translation_surfaces": translations,
        }
    return result


def _assert_binding(root: Path, expected: dict[str, Any], label: str) -> dict[str, Any]:
    path = safe_project_path(root, str(expected["path"]))
    expect(path.is_file(), f"missing {label}: {expected['path']}")
    actual = file_binding(path, root)
    expect(actual == expected, f"exact {label} changed: {expected['path']}")
    return actual


def unit10_baseline(root: Path) -> dict[str, Any]:
    exporter = _assert_binding(root, EXPECTED_V10_EXPORTER, "Unit 10 exporter")
    verifier = _assert_binding(root, EXPECTED_V10_VERIFIER, "Unit 10 verifier")
    reader_qa_binding = _assert_binding(root, EXPECTED_V10_READER_QA, "Unit 10 HTML QA receipt")
    public_binding = _assert_binding(root, EXPECTED_V10_PUBLIC_READBACK, "Unit 10 public readback receipt")
    public_zip = _assert_binding(root, EXPECTED_V10_PUBLIC_HTML_ZIP, "published Unit 10 HTML ZIP")

    baseline_directory = root / "output/html/unit-10"
    expect(baseline_directory.is_dir(), "exact Unit 10 HTML output directory is missing")
    inventory = tree_inventory(baseline_directory)
    digest = inventory_sha256(inventory)
    expect(len(inventory) == EXPECTED_V10_OUTPUT_FILE_COUNT, "Unit 10 HTML output file count changed")
    expect(digest == EXPECTED_V10_OUTPUT_INVENTORY_SHA256, "exact Unit 10 HTML output inventory changed")

    manifest = load_json_object(baseline_directory / "manifest.json")
    expect(manifest.get("workflow") == v10.WORKFLOW, "Unit 10 baseline manifest workflow changed")
    live_prefix_inputs = [file_binding(path, root) for path in source_files(root, 10)]
    expect(manifest.get("inputs") == live_prefix_inputs, "live Units 1--10 sources differ from the published HTML baseline")

    reader_qa = load_json_object(root / EXPECTED_V10_READER_QA["path"])
    expect(reader_qa.get("status") == "pass", "Unit 10 HTML QA receipt is not passing")
    expect(reader_qa.get("entry", {}).get("sha256") == "125688aadaade39ded86fb42adc8bfa74005a7fca66623a4c419c79ab36d52d4", "Unit 10 entry receipt changed")
    expect(reader_qa.get("manifest", {}).get("sha256") == "c9d6b7ce87feeb7c1621d0ac25e8b4ef3639a2e95140ef4ffe6f330a40b62e8e", "Unit 10 manifest receipt changed")

    public = load_json_object(root / EXPECTED_V10_PUBLIC_READBACK["path"])
    expect(public.get("status") == "pass" and public.get("record_status") == "published", "Unit 10 public readback is not a passing published receipt")
    expect(public.get("record_id") == EXPECTED_V10_PUBLIC_RECORD_ID, "Unit 10 public record identity changed")
    public_files = [item for item in public.get("files", []) if isinstance(item, dict)]
    zip_matches = [item for item in public_files if item.get("name") == Path(EXPECTED_V10_PUBLIC_HTML_ZIP["path"]).name]
    expect(len(zip_matches) == 1, "Unit 10 public readback does not contain exactly one HTML ZIP")
    expect(zip_matches[0].get("bytes") == public_zip["bytes"] and zip_matches[0].get("sha256") == public_zip["sha256"], "Unit 10 public HTML ZIP/readback identity differs")
    return {
        "status": "exact_published_baseline_preserved",
        "output_directory": "output/html/unit-10",
        "output_file_count": len(inventory),
        "output_inventory_sha256": digest,
        "output_inventory": inventory,
        "exporter": exporter,
        "verifier": verifier,
        "reader_qa": reader_qa_binding,
        "published_html_zip": public_zip,
        "public_readback": public_binding,
        "zenodo_record_id": EXPECTED_V10_PUBLIC_RECORD_ID,
    }


def unit13_baseline(root: Path) -> dict[str, Any]:
    """Prove the exact public cumulative Unit 13 HTML boundary is untouched."""
    exporter = _assert_binding(root, EXPECTED_V13_EXPORTER, "Unit 13 exporter")
    verifier = _assert_binding(root, EXPECTED_V13_VERIFIER, "Unit 13 verifier")
    reader_qa_binding = _assert_binding(root, EXPECTED_V13_READER_QA, "Unit 13 HTML QA receipt")
    zenodo_binding = _assert_binding(root, EXPECTED_V13_ZENODO_READBACK, "Unit 13 Zenodo readback")
    github_binding = _assert_binding(root, EXPECTED_V13_GITHUB_READBACK, "Unit 13 GitHub readback")
    public_zip = _assert_binding(root, EXPECTED_V13_PUBLIC_HTML_ZIP, "published Unit 13 HTML ZIP")

    baseline_directory = root / "output/html/unit-13"
    expect(baseline_directory.is_dir(), "exact Unit 13 HTML output directory is missing")
    inventory = tree_inventory(baseline_directory)
    digest = inventory_sha256(inventory)
    expect(len(inventory) == EXPECTED_V13_OUTPUT_FILE_COUNT, "Unit 13 HTML output file count changed")
    expect(digest == EXPECTED_V13_OUTPUT_INVENTORY_SHA256, "exact Unit 13 HTML output inventory changed")

    manifest_path = baseline_directory / "manifest.json"
    entry_path = baseline_directory / "index.html"
    expect(file_binding(entry_path, root)["sha256"] == EXPECTED_V13_ENTRY_SHA256, "Unit 13 HTML entry changed")
    expect(file_binding(manifest_path, root)["sha256"] == EXPECTED_V13_MANIFEST_SHA256, "Unit 13 HTML manifest changed")
    manifest = load_json_object(manifest_path)
    expect(manifest.get("workflow") == "o011-export-html-v13", "Unit 13 baseline manifest workflow changed")
    expect(manifest.get("units") == list(range(1, 14)), "Unit 13 baseline no longer covers exactly Units 1--13")
    live_prefix_inputs = [file_binding(path, root) for path in source_files(root, 13)]
    expect(manifest.get("inputs") == live_prefix_inputs, "live Units 1--13 sources differ from the published HTML baseline")

    reader_qa = load_json_object(root / EXPECTED_V13_READER_QA["path"])
    expect(reader_qa.get("status") == "pass" and reader_qa.get("workflow") == "o011-verify-html-v13", "Unit 13 HTML QA receipt is not passing")
    expect(reader_qa.get("entry", {}).get("sha256") == EXPECTED_V13_ENTRY_SHA256, "Unit 13 QA entry binding changed")
    expect(reader_qa.get("manifest", {}).get("sha256") == EXPECTED_V13_MANIFEST_SHA256, "Unit 13 QA manifest binding changed")

    zenodo = load_json_object(root / EXPECTED_V13_ZENODO_READBACK["path"])
    github = load_json_object(root / EXPECTED_V13_GITHUB_READBACK["path"])
    expect(zenodo.get("status") == "pass" and zenodo.get("record_status") == "published", "Unit 13 Zenodo readback is not passing/published")
    expect(zenodo.get("record_id") == EXPECTED_V13_ZENODO_RECORD_ID, "Unit 13 Zenodo record identity changed")
    expect(github.get("status") == "pass" and github.get("commit") == EXPECTED_V13_GITHUB_COMMIT, "Unit 13 GitHub readback identity changed")
    for receipt, key in ((zenodo, "files"), (github, "public_files")):
        matches = [item for item in receipt.get(key, []) if isinstance(item, dict) and item.get("name") == Path(EXPECTED_V13_PUBLIC_HTML_ZIP["path"]).name]
        expect(len(matches) == 1, f"Unit 13 public readback lacks the exact HTML ZIP ({key})")
        expect(matches[0].get("bytes") == public_zip["bytes"] and matches[0].get("sha256") == public_zip["sha256"], f"Unit 13 public HTML ZIP identity differs ({key})")
    return {
        "status": "exact_published_baseline_preserved",
        "output_directory": "output/html/unit-13",
        "output_file_count": len(inventory),
        "output_inventory_sha256": digest,
        "output_inventory": inventory,
        "exporter": exporter,
        "verifier": verifier,
        "reader_qa": reader_qa_binding,
        "published_html_zip": public_zip,
        "zenodo_public_readback": zenodo_binding,
        "github_public_readback": github_binding,
        "zenodo_record_id": EXPECTED_V13_ZENODO_RECORD_ID,
        "github_commit": EXPECTED_V13_GITHUB_COMMIT,
    }


def generation_bindings(root: Path) -> list[dict[str, Any]]:
    relatives = [
        "authority/brenner_media_rights_manifest.csv",
        "source/unit_media.json",
        *[f"qa/unit-{unit:02d}_media.json" for unit in range(1, UNIT_COUNT + 1)],
        "source/unit07_interactive_media.json",
        "qa/unit-07/INTERACTIVE_MEDIA_QA.json",
        "source/unit11_interactive_media.json",
        "qa/unit-11/INTERACTIVE_MEDIA_QA.json",
        "qa/unit-12/ANIMATED_MEDIA_QA.json",
        "qa/unit-12/HTML_ANIMATED_MEDIA_QA.json",
    ]
    bindings: list[dict[str, Any]] = []
    for relative in relatives:
        path = safe_project_path(root, relative)
        expect(path.is_file(), f"missing generation binding: {relative}")
        bindings.append(file_binding(path, root))
    return bindings


def generation_contract(root: Path) -> dict[str, Any]:
    return {
        "unit13_baseline": unit13_baseline(root),
        "unit14_16_live_qa": load_live_qa_bindings(root),
        "generation_bindings": generation_bindings(root),
        "exporter": file_binding(Path(__file__).resolve(), root),
    }


class Renderer(v10.Renderer):
    """The v10 semantic renderer plus receipt-backed source-linked GIFs."""

    def __init__(self, root: Path, rights: dict[str, dict[str, str]]) -> None:
        # The inherited Brenner macro parser normalizes ``bildeinlesungjpeg``
        # to a ``.jpg`` lookup key.  Commons and the frozen rights ledger keep
        # the canonical filename extension ``.jpeg`` for the Unit 16 Riemann
        # portrait.  Admit a lookup-only alias while retaining the canonical
        # filename, source binding, output name, and receipt identity carried
        # by the rights record itself.
        rights_with_aliases: dict[str, dict[str, str]] = {}
        for key, value in rights.items():
            normalized = dict(value)
            if not str(normalized.get("creator_text") or "").strip():
                # Do not turn missing Commons creator metadata into a false
                # attribution.  A visible, honest unknown-creator label keeps
                # the component-rights surface complete and matches the
                # Unit 16 media receipt's disclosed attribution state.
                normalized["creator_text"] = "Pembuat tidak dicantumkan dalam metadata Commons"
            rights_with_aliases[key] = normalized
            if key.endswith("jpeg"):
                alias = key[:-4] + "jpg"
                existing = rights_with_aliases.get(alias)
                expect(existing in (None, normalized), f"conflicting JPEG/JPG rights entries: {key}")
                rights_with_aliases[alias] = normalized
        super().__init__(root, rights_with_aliases)
        self.linked_media_used: dict[str, dict[str, Any]] = {}
        self.linked_media_occurrences: list[dict[str, Any]] = []

    def _verify_unit_media_receipt(self, filename: str, unit: int, binding: dict[str, Any]) -> dict[str, Any]:
        receipt_path = self.root / f"qa/unit-{unit:02d}_media.json"
        receipt = load_json_object(receipt_path)
        expect(receipt.get("unit_number") == unit, f"media receipt unit differs for {filename}")
        matches = [
            item for item in receipt.get("media", [])
            if isinstance(item, dict) and item.get("filename") == filename
        ]
        expect(len(matches) == 1, f"Unit {unit} media receipt does not uniquely bind {filename}")
        item = matches[0]
        expect(item.get("canonical_path") == binding["path"], f"Unit {unit} media path differs for {filename}")
        expect(item.get("canonical_bytes") == binding["bytes"], f"Unit {unit} media byte count differs for {filename}")
        expect(item.get("canonical_sha256") == binding["sha256"], f"Unit {unit} media SHA-256 differs for {filename}")
        return file_binding(receipt_path, self.root)

    def _figure(self, body: str, state: SurfaceState) -> str:
        previous = {name: dict(item) for name, item in self.media_used.items()}
        rendered = super()._figure(body, state)
        occurrence = self.figure_occurrences[-1]
        filename = str(occurrence["filename"])
        current = self.media_used[filename]
        old = previous.get(filename, {})
        units = sorted(set([*old.get("units", []), state.unit]))
        receipts = {str(item["unit"]): item["binding"] for item in old.get("unit_media_receipts", [])}
        receipts[str(state.unit)] = self._verify_unit_media_receipt(filename, state.unit, current["source"])
        current["units"] = units
        current["unit_media_receipts"] = [
            {"unit": int(unit), "binding": receipts[unit]} for unit in sorted(receipts, key=int)
        ]
        occurrence["unit"] = state.unit
        return rendered

    def _source_linked_animation(self, filename: str, raw_label: str, state: SurfaceState) -> str:
        expect(state.unit in (7, 11), f"unadmitted source-linked animation in Unit {state.unit}: {filename}")
        manifest_path = self.root / f"source/unit{state.unit:02d}_interactive_media.json"
        qa_path = self.root / f"qa/unit-{state.unit:02d}/INTERACTIVE_MEDIA_QA.json"
        manifest = load_json_object(manifest_path)
        qa = load_json_object(qa_path)
        expect(manifest.get("unit") == state.unit, f"interactive-media manifest unit differs for {filename}")
        expect(qa.get("status") == "pass", f"interactive-media QA is not passing for Unit {state.unit}")
        manifest_matches = [item for item in manifest.get("assets", []) if isinstance(item, dict) and item.get("filename") == filename]
        qa_matches = [item for item in qa.get("assets", []) if isinstance(item, dict) and item.get("filename") == filename]
        expect(len(manifest_matches) == 1 and len(qa_matches) == 1, f"interactive-media receipts do not uniquely bind {filename}")
        asset = manifest_matches[0]
        qa_asset = qa_matches[0]
        source = self.root / "authority/media" / filename
        expect(source.is_file(), f"source-linked animation bytes are missing: {filename}")
        binding = file_binding(source, self.root)
        for record, label in ((asset, "manifest"), (qa_asset, "QA")):
            expect(record.get("bytes") == binding["bytes"], f"interactive {label} byte count differs for {filename}")
            expect(record.get("sha256") == binding["sha256"], f"interactive {label} SHA-256 differs for {filename}")
            expect(record.get("creator") and record.get("license"), f"interactive {label} rights are incomplete for {filename}")

        visible_label = str(asset.get("alt_text_id") or LINKED_ANIMATION_LABELS.get(filename, "")).strip()
        expect(bool(visible_label), f"no admitted Indonesian label for {filename}")
        if state.unit == 11:
            expect(" ".join(raw_label.split()) == " ".join(visible_label.split()), f"Unit 11 source-linked animation label differs for {filename}")
        occurrence_number = 1 + sum(item["filename"] == filename for item in self.linked_media_occurrences)
        expect(occurrence_number == 1, f"source-linked animation is duplicated: {filename}")
        state_count = int(getattr(state, "linked_animation_counter", 0)) + 1
        setattr(state, "linked_animation_counter", state_count)
        anchor = f"{state.stable_id}-linked-animation-{state_count:02d}"
        item = {
            "filename": filename,
            "source": binding,
            "creator": str(asset["creator"]),
            "license": str(asset["license"]),
            "license_url": str(asset.get("license_url") or qa_asset.get("license_url") or "") or None,
            "description_url": str(asset.get("source_page") or "") or None,
            "description": visible_label,
            "role": "source-linked animation; local keyboard-accessible download",
            "bindings": {
                "interactive_media_manifest": file_binding(manifest_path, self.root),
                "interactive_media_qa": file_binding(qa_path, self.root),
            },
        }
        self.linked_media_used[filename] = item
        self.linked_media_occurrences.append({
            "id": anchor,
            "unit": state.unit,
            "filename": filename,
            "description": visible_label,
        })
        media_url = "assets/media/" + quote(filename)
        rights_parts = [html.escape(item["creator"]), html.escape(item["license"])]
        if item["license_url"]:
            rights_parts[-1] = f'<a href="{html.escape(str(item["license_url"]), quote=True)}">{html.escape(item["license"])}</a>'
        if item["description_url"]:
            rights_parts.append(f'<a href="{html.escape(str(item["description_url"]), quote=True)}">sumber media</a>')
        return (
            f'<span class="source-linked-animation" id="{anchor}" data-entity="source-linked-animation">'
            f'<a class="source-linked-animation-download" href="{html.escape(media_url, quote=True)}" '
            f'download="{html.escape(filename, quote=True)}" aria-label="Unduh animasi sumber: {html.escape(visible_label, quote=True)}">'
            f'{html.escape(visible_label)}</a>'
            f'<span class="media-rights">{" · ".join(rights_parts)}</span></span>'
        )

    def render_inline(self, text: str, state: SurfaceState) -> str:
        matches = list(FILE_LINK_RE.finditer(text))
        if not matches:
            return super().render_inline(text, state)
        output: list[str] = []
        position = 0
        for match in matches:
            output.append(super().render_inline(text[position:match.start()], state))
            output.append(self._source_linked_animation(match.group(1).strip(), match.group(2).strip(), state))
            position = match.end()
        output.append(super().render_inline(text[position:], state))
        return "".join(output)

    def _exercise(self, name: str, args: list[str], state: SurfaceState) -> str:
        state.exercise_counter += 1
        state.semantic_counts[name] = state.semantic_counts.get(name, 0) + 1
        number = state.exercise_counter
        anchor = f"o011-brenner-u{state.unit:02d}-w{state.unit:02d}-e{number:03d}"
        points = self.render_inline(args[0].strip(), state) if args[0].strip() else ""
        supplied = name == "inputaufgabegibtloesung"
        badges: list[str] = []
        if points:
            badges.append(f'<span class="points">{points} poin</span>')
        if supplied:
            badges.append(f'<a class="solution-marker" href="#{anchor}-solution">Solusi sumber tersedia</a>')
        body = self.render_flow(args[1], state)
        hint = self.render_flow(args[2], state) if args[2].strip() else ""
        if hint:
            body += f'<aside class="hint"><h5>Petunjuk sumber</h5>{hint}</aside>'
        return (
            f'<article class="exercise{" has-source-solution" if supplied else ""}" id="{anchor}" '
            f'data-entity="exercise" data-source-solution="{"true" if supplied else "false"}">'
            f'<h4>Soal {state.unit}.{number}</h4>{"".join(badges)}{body}</article>'
        )


def load_media_rights(root: Path) -> dict[str, dict[str, str]]:
    return v10.load_media_rights(root)


def reader_head_extension(renderer: Renderer) -> str:
    return v10.reader_head_extension(renderer)


LINKED_MEDIA_CSS = r'''
/* Receipt-backed source-linked animations remain explicit local downloads. */
.source-linked-animation{display:block;margin:1rem 0;padding:.8rem 1rem;border-left:.3rem solid #16856b;background:#f1fbf7;border-radius:.35rem}.source-linked-animation-download{display:inline-block;font:700 .95rem/1.35 system-ui,sans-serif}.source-linked-animation .media-rights{font:.82rem/1.45 system-ui,sans-serif;color:var(--muted);margin-top:.35rem}.solution-backlink{font:650 .88rem/1.3 system-ui,sans-serif}
@media(prefers-color-scheme:dark){.source-linked-animation{background:#102e29}}
'''

V16_REFLOW_CSS = r'''
/* Keep MathJax's intrinsic width inside the reader-owned scrolling region. */
.math.display{max-width:100%;min-width:0;contain:inline-size}
@media(max-width:46rem){.unit,.lecture,.worksheet,.semantic-block,.exercise,.source-solution,.proof{min-width:0;max-width:100%}.math.inline{display:inline-block;max-width:100%;overflow-x:auto;overflow-y:hidden;vertical-align:middle;contain:inline-size}}
'''


def reader_css(renderer: Renderer) -> str:
    value = v10.CSS + V16_REFLOW_CSS
    if renderer.has_animated_media:
        value += v10.ANIMATED_MEDIA_CSS
    if renderer.linked_media_used:
        value += LINKED_MEDIA_CSS
    return value.replace("O011 HTML v10", "O011 HTML v16", 1)


README_TEXT = f'''Geometri Diferensial dan Manifold Mulus — pembaca HTML hingga Unit 16

Buka index.html pada peramban modern. Teks, navigasi, CSS, media, dan semua
solusi yang benar-benar disediakan oleh sumber tersedia secara lokal. Rumus
dipertahankan sebagai sumber TeX MathJax-compatible. Perenderan tipografis
rumus menggunakan dependensi opsional berikut ketika jaringan tersedia:

{MATHJAX_URL}

Jika dependensi itu tidak dapat dimuat, sumber TeX rumus tetap terlihat dan
dapat dipilih. Media animasi tertanam dimulai dari bingkai statis. Tombol
“Putar animasi” dan “Hentikan animasi” bekerja dengan tetikus atau papan ketik;
preferensi sistem untuk mengurangi gerak mempertahankan keadaan statis. GIF
kanonis dapat diunduh. Animasi sumber yang tidak tertanam juga dipertahankan
sebagai unduhan lokal yang dapat dioperasikan dengan papan ketik.

Teks sumber dan adaptasi: CC BY-SA 4.0. Setiap media mempertahankan lisensi
per berkas yang dicatat pada keterangannya dan manifest.json. Ini merupakan
edisi independen, bukan edisi resmi dan bukan dukungan penulis/Wikiversity.
'''


def reader_readme(renderer: Renderer) -> str:
    return README_TEXT


def stage_media_assets(root: Path, staging: Path, renderer: Renderer) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    media_manifest = v10.stage_media_assets(root, staging, renderer)
    for item in media_manifest:
        used = renderer.media_used[str(item["filename"])]
        item["units"] = used.get("units", [])
        item["unit_media_receipts"] = used.get("unit_media_receipts", [])

    linked_manifest: list[dict[str, Any]] = []
    for filename, item in sorted(renderer.linked_media_used.items()):
        expect(filename not in renderer.media_used, f"linked/embedded media target collision: {filename}")
        source = safe_project_path(root, str(item["source"]["path"]))
        expect(file_binding(source, root) == item["source"], f"source-linked animation changed during export: {filename}")
        target = staging / "assets/media" / filename
        expect(not target.exists(), f"source-linked animation target collision: {filename}")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        linked_manifest.append(dict(item))
    return media_manifest, linked_manifest


def render_reader(root: Path, renderer: Renderer) -> tuple[str, dict[str, Any]]:
    navigation: list[str] = []
    units_html: list[str] = []
    topology: dict[str, Any] = {}
    for unit in range(1, UNIT_COUNT + 1):
        tag = f"{unit:02d}"
        unit_id = f"o011-brenner-u{tag}"
        lecture_id = f"{unit_id}-l{tag}"
        worksheet_id = f"{unit_id}-w{tag}"
        navigation.append(f'<li><a href="#{unit_id}">Unit {unit}</a></li>')
        lecture_path = root / f"source/units/unit-{tag}/lecture{tag}.id.tex"
        worksheet_path = root / f"source/units/unit-{tag}/worksheet{tag}.id.tex"
        lecture_state = SurfaceState(unit, "lecture", lecture_id)
        worksheet_state = SurfaceState(unit, "worksheet", worksheet_id)
        lecture_html = renderer.render_flow(lecture_path.read_text(encoding="utf-8"), lecture_state)
        worksheet_html = renderer.render_flow(worksheet_path.read_text(encoding="utf-8"), worksheet_state)

        supplied_indices = solution_indices(root, unit)
        marker_indices = source_solution_marker_indices(worksheet_path)
        expect(marker_indices == supplied_indices, f"Unit {unit} source solution markers/files differ")
        solutions_html: list[str] = []
        for index in supplied_indices:
            path = root / f"source/units/unit-{tag}/worksheet{tag}_exercise{index:02d}_solution.id.tex"
            stable_id = f"{worksheet_id}-e{index:03d}-solution"
            exercise_id = f"{worksheet_id}-e{index:03d}"
            solution_state = SurfaceState(unit, f"solution-{index}", stable_id)
            body = renderer.render_flow(path.read_text(encoding="utf-8"), solution_state)
            solutions_html.append(
                f'<article class="source-solution" id="{stable_id}" data-entity="source-supplied-solution" '
                f'data-solves="{exercise_id}"><h4>Solusi sumber untuk Soal {unit}.{index}</h4>{body}'
                f'<p class="solution-backlink"><a href="#{exercise_id}">Kembali ke Soal {unit}.{index}</a></p></article>'
            )
        solution_section = ""
        if solutions_html:
            solution_section = (
                f'<section class="solutions" id="{worksheet_id}-solutions" aria-labelledby="{worksheet_id}-solutions-heading">'
                f'<h3 id="{worksheet_id}-solutions-heading">Solusi yang disediakan oleh sumber</h3>'
                '<p class="scope-note">Bagian ini hanya memuat solusi yang benar-benar tersedia pada sumber. '
                'Tidak adanya solusi di sini bukan pernyataan bahwa sebuah soal tidak dapat diselesaikan.</p>'
                + "".join(solutions_html) + "</section>"
            )
        units_html.append(
            f'<section class="unit" id="{unit_id}" data-entity="unit"><header class="unit-header">'
            f'<p class="eyebrow">Unit {unit}</p><h2>{html.escape(UNIT_TITLES[unit])}</h2></header>'
            f'<section class="lecture" id="{lecture_id}" data-entity="lecture"><h3>Kuliah {unit}</h3>{lecture_html}</section>'
            f'<section class="worksheet" id="{worksheet_id}" data-entity="worksheet"><h3>Lembar Kerja {unit}</h3>{worksheet_html}</section>'
            f'{solution_section}</section>'
        )
        topology[tag] = {
            "lecture": {
                "source_sections": lecture_state.section_counter,
                "semantic_blocks": lecture_state.fact_counter,
                "figures": lecture_state.figure_counter,
                "counts": lecture_state.semantic_counts,
            },
            "worksheet": {
                "source_sections": worksheet_state.section_counter,
                "exercises": worksheet_state.exercise_counter,
                "figures": worksheet_state.figure_counter,
                "counts": worksheet_state.semantic_counts,
            },
            "source_supplied_solution_indices": supplied_indices,
        }

    expected_linked = sorted([
        *[str(item["filename"]) for item in load_json_object(root / "source/unit07_interactive_media.json").get("assets", [])],
        *[str(item["filename"]) for item in load_json_object(root / "source/unit11_interactive_media.json").get("assets", [])],
    ])
    actual_linked = sorted(item["filename"] for item in renderer.linked_media_occurrences)
    expect(actual_linked == expected_linked, "source-linked animation occurrence/authority closure differs")

    animated_media_head = reader_head_extension(renderer)
    document = f'''<!doctype html>
<html lang="id-ID">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="Pembaca reflowable Bahasa Indonesia untuk Kuliah dan Lembar Kerja 1–16 dari Differentialgeometrie (Osnabrück 2023).">
  <title>Geometri Diferensial dan Manifold Mulus — Pembaca hingga Unit 16</title>
  <link rel="stylesheet" href="assets/reader.css">
  <script id="mathjax-config">{MATHJAX_CONFIG}</script>
  <script defer src="{MATHJAX_URL}"></script>
  <script id="deep-link-stabilizer">(()=>{{const align=()=>{{if(!location.hash)return;const target=document.getElementById(decodeURIComponent(location.hash.slice(1)));if(!target)return;const root=document.documentElement;const previous=root.style.scrollBehavior;root.style.scrollBehavior="auto";target.scrollIntoView({{block:"start"}});root.style.scrollBehavior=previous;}};const settle=()=>{{align();requestAnimationFrame(align);setTimeout(align,250);setTimeout(align,1000);setTimeout(align,3000);}};addEventListener("load",settle,{{once:true}});addEventListener("hashchange",settle);if(document.fonts)document.fonts.ready.then(settle);}})();</script>{animated_media_head}
</head>
<body>
<a class="skip-link" href="#reader">Lewati ke isi utama</a>
<header class="masthead">
  <div class="masthead-inner">
    <p class="eyebrow">Edisi Bahasa Indonesia independen · cakupan parsial</p>
    <h1>Geometri Diferensial dan Manifold Mulus</h1>
    <p class="subtitle">Pembaca kumulatif hingga Unit 16</p>
    <p>Holger Brenner · <cite>Differentialgeometrie (Osnabrück 2023)</cite></p>
  </div>
</header>
<nav class="unit-nav" aria-label="Daftar unit"><ol>{''.join(navigation)}</ol></nav>
<main id="reader">
  <section class="frontmatter" id="tentang-edisi">
    <h2>Tentang edisi ini</h2>
    <p>Pembaca ini menerjemahkan Kuliah 1–16 dan Lembar Kerja 1–16 dari kursus Holger Brenner di Wikiversity berbahasa Jerman. Teks sumber digunakan berdasarkan <a href="https://creativecommons.org/licenses/by-sa/4.0/">CC BY-SA 4.0</a>. Terjemahan ini merupakan karya independen dan bukan edisi resmi atau dukungan dari penulis, Wikiversity, atau Wikimedia Foundation.</p>
    <p>Setiap gambar dan animasi tetap mengikuti lisensi berkasnya sendiri; pembuat, lisensi, dan tautan sumber tercantum langsung pada keterangannya atau tautan unduhnya. Rumus, urutan materi, latihan, dan tepat semua solusi yang disediakan sumber dipertahankan. ID yang stabil dan netral-lokal merupakan lapisan tambahan.</p>
    <p>Proses terjemahan dan produksi edisi dibantu oleh {MODEL_IDENTIFICATION}, di bawah arahan pengguna. Kredit penulis, sumber, dan kontributor manusia tetap dipertahankan.</p>
    <aside class="dependency-note" id="math-rendering"><h3>Tampilan matematika dan penggunaan offline</h3><p>Semua teks, navigasi, gaya, dan media berada di paket ini dan dapat dibaca offline. Perenderan tipografis rumus memakai MathJax dari CDN saat jaringan tersedia. Jika dependensi opsional itu tidak dapat dimuat, sumber TeX setiap rumus tetap terlihat, dapat dipilih, dan tidak menggantikan isi.</p><noscript><p>JavaScript tidak aktif; rumus dan bingkai statis animasi tetap ditampilkan.</p></noscript></aside>
    <p><a href="{OFFICIAL_SOURCE}">Sumber resmi kursus</a></p>
  </section>
  {''.join(units_html)}
  <section class="backmatter" id="lisensi-dan-provenans">
    <h2>Lisensi, provenans, dan independensi</h2>
    <p>Teks sumber dan adaptasi Bahasa Indonesia ini didistribusikan berdasarkan CC BY-SA 4.0. Media tidak menerima lisensi umum dari teks; setiap komponen mempertahankan lisensi berkasnya sendiri sebagaimana dicatat pada gambar, tautan unduh, dan manifes.</p>
    <p>Edisi ini tidak resmi dan tidak menyiratkan dukungan dari Holger Brenner, Wikiversity, para pembuat media, atau Wikimedia Foundation. Identitas sumber, perubahan, QA langsung, batas publik Unit 13, dan hash masukan tersedia pada <a href="manifest.json">manifes deterministik pembaca</a>.</p>
  </section>
</main>
<footer><p>Pembaca semantik reflowable · Bahasa Indonesia · Unit 1–16</p></footer>
</body>
</html>
'''
    return document, topology


def _stage_cycle(root: Path, staging: Path, contract: dict[str, Any]) -> dict[str, Any]:
    staging.mkdir(parents=True, exist_ok=False)
    inputs = source_files(root)
    initial_bindings = [file_binding(path, root) for path in inputs]
    renderer = Renderer(root, load_media_rights(root))
    document, topology = render_reader(root, renderer)
    final_bindings = [file_binding(path, root) for path in inputs]
    expect(initial_bindings == final_bindings, "reader sources changed during a staging cycle")

    write_text(staging / "index.html", document)
    write_text(staging / "assets/reader.css", reader_css(renderer))
    write_text(staging / "README.txt", reader_readme(renderer))
    media_manifest, linked_media_manifest = stage_media_assets(root, staging, renderer)
    payload_files = tree_inventory(staging)
    payload_digest = inventory_sha256(payload_files)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "workflow": WORKFLOW,
        "scope": "O011 cumulative Indonesian semantic HTML reader through Unit 16",
        "status": "partial_edition",
        "language": "id-ID",
        "units": list(range(1, UNIT_COUNT + 1)),
        "model_identification": MODEL_IDENTIFICATION,
        "official_source": OFFICIAL_SOURCE,
        "text_license": "CC BY-SA 4.0",
        "non_endorsement": True,
        "math_rendering": {
            "format": "MathJax-compatible TeX retained in document text",
            "optional_network_dependency": MATHJAX_URL,
            "offline_fallback": "visible selectable TeX source",
        },
        "inputs": final_bindings,
        "unit13_baseline": contract["unit13_baseline"],
        "unit14_16_live_qa": contract["unit14_16_live_qa"],
        "generation_bindings": contract["generation_bindings"],
        "exporter": contract["exporter"],
        "topology": topology,
        "media": media_manifest,
        "source_linked_media": linked_media_manifest,
        "figures": renderer.figure_occurrences,
        "source_linked_media_occurrences": renderer.linked_media_occurrences,
        "reproducibility": {
            "staging_cycles": 2,
            "required_comparison": "complete relative-path/byte-count/SHA-256 inventory, including manifest",
            "payload_inventory_sha256": payload_digest,
            "byte_identical_before_commit": True,
        },
        "excluded_reader_metadata": {
            "mediawiki_category_marker": "[[Kategorie:Latexseite]]",
            "occurrences": sum(path.read_text(encoding="utf-8").count("[[Kategorie:Latexseite]]") for path in inputs),
            "preservation": "Retained byte-for-byte in the source inputs bound above; excluded only from reader-visible prose.",
        },
        "files": payload_files,
    }
    write_text(staging / "manifest.json", canonical_json(manifest))
    return manifest


def assert_output_path(root: Path, output: Path) -> Path:
    root = root.resolve()
    output = output.resolve()
    html_root = (root / "output/html").resolve()
    try:
        relative = output.relative_to(html_root)
    except ValueError as exc:
        raise RuntimeError("v16 output must remain beneath output/html") from exc
    expect(bool(relative.parts), "v16 output may not replace output/html itself")
    expect(output not in {(html_root / "unit-10").resolve(), (html_root / "unit-13").resolve()}, "published Unit 10/13 outputs are immutable")
    return output


def build(root: Path, output: Path, replace: bool) -> dict[str, Any]:
    root = root.resolve()
    output = assert_output_path(root, output)
    if output.exists():
        expect(output.is_dir(), f"output exists and is not a directory: {output}")
        expect(replace, f"output already exists (use --replace for this exact v16 directory): {output}")

    contract = generation_contract(root)
    output.parent.mkdir(parents=True, exist_ok=True)
    first = Path(tempfile.mkdtemp(prefix=".html-v16-cycle1-", dir=output.parent))
    second = Path(tempfile.mkdtemp(prefix=".html-v16-cycle2-", dir=output.parent))
    # mkdtemp creates the directory; _stage_cycle requires a fresh child.
    first_stage = first / "reader"
    second_stage = second / "reader"
    try:
        first_manifest = _stage_cycle(root, first_stage, contract)
        expect(generation_contract(root) == contract, "generation contract changed after staging cycle one")
        second_manifest = _stage_cycle(root, second_stage, contract)
        expect(generation_contract(root) == contract, "generation contract changed after staging cycle two")
        first_inventory = tree_inventory(first_stage)
        second_inventory = tree_inventory(second_stage)
        expect(first_inventory == second_inventory, "two complete Unit 16 staging trees are not byte-identical")
        expect(first_manifest == second_manifest, "two Unit 16 staging manifests differ")
        if output.exists():
            shutil.rmtree(output)
        os.replace(second_stage, output)
        return {
            "manifest": second_manifest,
            "tree_inventory_sha256": inventory_sha256(second_inventory),
            "tree_file_count": len(second_inventory),
        }
    finally:
        shutil.rmtree(first, ignore_errors=True)
        shutil.rmtree(second, ignore_errors=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--replace", action="store_true", help="replace only the exact declared v16 output after two complete identical staging cycles")
    args = parser.parse_args()
    root = args.root.resolve()
    output = (args.output or (root / "output/html/unit-16")).resolve()
    result = build(root, output, args.replace)
    manifest = result["manifest"]
    print(canonical_json({
        "status": "pass",
        "output": output.relative_to(root).as_posix(),
        "input_count": len(manifest["inputs"]),
        "file_count": result["tree_file_count"],
        "media_count": len(manifest["media"]),
        "source_linked_media_count": len(manifest["source_linked_media"]),
        "two_cycle_tree_inventory_sha256": result["tree_inventory_sha256"],
    }), end="")


if __name__ == "__main__":
    main()
