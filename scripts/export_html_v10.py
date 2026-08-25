#!/usr/bin/env python3
"""Build the deterministic, reflowable O011 Indonesian reader through Unit 10.

The admitted source uses a MediaWiki-generated semantic TeX macro vocabulary,
not generic document LaTeX.  This exporter therefore parses the bounded macro
grammar actually used by Units 1--10 and refuses unknown text-mode commands
instead of silently dropping content.  Mathematical payloads remain TeX and
are emitted with MathJax-compatible delimiters.  If the optional network
renderer is unavailable, the TeX source remains visible and selectable.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import os
import re
import shutil
import tempfile
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import quote


SCHEMA_VERSION = 1
WORKFLOW = "o011-export-html-v10"
MODEL_IDENTIFICATION = "OpenAI Codex gpt-5.6-sol, Ultra"
OFFICIAL_SOURCE = "https://de.wikiversity.org/wiki/Kurs:Differentialgeometrie_(Osnabr%C3%BCck_2023)"
MATHJAX_URL = "https://cdn.jsdelivr.net/npm/mathjax@3.2.2/es5/tex-chtml.js"

UNIT_TITLES = {
    1: "Analisis dan Geometri",
    2: "Permukaan Putar, Medan Normal, dan Pemetaan Gauss",
    3: "Kelengkungan Kurva Berparameter Panjang Busur",
    4: "Pemetaan Weingarten",
    5: "Kelengkungan Utama",
    6: "Turunan Kovarian, Medan Vektor Paralel, dan Transpor Paralel",
    7: "Konsep sebuah Manifold",
    8: "Teorema Pemetaan Implisit dan Manifold",
    9: "Ruang Singgung Manifold Diferensiabel",
    10: "Submanifold Tertutup",
}

STRUCTURAL_ARITY = {
    "zwischenueberschrift": 1,
    "inputdefinition": 2,
    "inputaxiom": 2,
    "inputnotation": 2,
    "inputbeispiel": 2,
    "inputbemerkung": 2,
    "inputverfahren": 2,
    "inputkonstruktion": 2,
    "inputfrage": 2,
    "inputproblem": 2,
    "inputsituation": 2,
    "inputfakt": 4,
    "inputfaktbeweis": 5,
    "inputfaktbeweisnichtvorgefuehrt": 5,
    "inputfaktbeweistrivial": 4,
    "inputfaktuebergangbeweis": 6,
    "inputbeweis": 1,
    "inputaufgabe": 4,
    "inputaufgabegibtloesung": 4,
    "bild": 1,
    "bildlizenz": 6,
    "setcounter": 2,
    "faktsituation": 1,
    "faktvoraussetzung": 1,
    "faktvoraussetzungpos": 1,
    "faktvoraussetzungleer": 1,
    "faktuebergang": 1,
    "faktuebergangpos": 1,
    "faktuebergangleer": 1,
    "faktfolgerung": 1,
    "faktzusatz": 1,
    "teilbeweis": 5,
    "fallunterscheidung": 5,
    "fallunterscheidungzwei": 2,
    "fallunterscheidungdrei": 3,
    "fallunterscheidungvier": 4,
    "fallunterscheidungfuenf": 5,
    "mathdisp": 2,
    "mathdisplayteile": 3,
    "mavergleichskettedisp": 4,
    "mavergleichskettedisplang": 4,
    "mavergleichskettealign": 4,
    "mavergleichskettealigndrucklinks": 4,
    "mavergleichskettealignhandlinks": 4,
    "mavergleichskettedisphandlinks": 4,
    "mathlistdisp": 5,
    "alignier": 2,
    "maabbdisp": 4,
    "maabbnamedisp": 4,
    "maabbeledisp": 6,
    "maabbeledispvar": 6,
    "maabbelementzeiledisplay": 6,
    "maabbelementdoppelzeiledisplay": 6,
    "aufzaehlungeins": 1,
    "aufzaehlungzwei": 2,
    "aufzaehlungdrei": 3,
    "aufzaehlungvier": 4,
    "aufzaehlungfuenf": 5,
    "aufzaehlungsechs": 6,
    "aufzaehlungsieben": 7,
    "aufzaehlungacht": 8,
    "aufzaehlungneun": 9,
    "aufzaehlungeinsabc": 1,
    "aufzaehlungzweiabc": 2,
    "aufzaehlungdreiabc": 3,
    "aufzaehlungvierabc": 4,
    "aufzaehlungfuenfabc": 5,
    "aufzaehlungsechsabc": 6,
    "aufzaehlungsiebenabc": 7,
    "aufzaehlungachtabc": 8,
    "aufzaehlungneunabc": 9,
}

INLINE_ARITY = {
    "definitionsverweis": 3,
    "definitionsverweisanfuehrung": 3,
    "definitionswort": 2,
    "definitionswortteil": 2,
    "definitionswortenp": 2,
    "definitionswortpraemath": 3,
    "stichwort": 2,
    "stichwortpraemath": 3,
    "betonung": 2,
    "emph": 1,
    "textit": 1,
    "textbf": 1,
    "anfuehrung": 2,
    "anfuehrungenglisch": 2,
    "zusatz": 2,
    "zusatzklammer": 3,
    "zusatzgs": 3,
    "zusatzfussnote": 3,
    "faktsituation": 1,
    "faktvoraussetzung": 1,
    "faktvoraussetzungpos": 1,
    "faktvoraussetzungleer": 1,
    "faktuebergang": 1,
    "faktuebergangpos": 1,
    "faktuebergangleer": 1,
    "faktfolgerung": 1,
    "faktzusatz": 1,
    "teilbeweis": 5,
    "fallunterscheidung": 5,
    "fallunterscheidungzwei": 2,
    "fallunterscheidungdrei": 3,
    "fallunterscheidungvier": 4,
    "fallunterscheidungfuenf": 5,
    "mathl": 2,
    "mathlk": 2,
    "mathind": 3,
    "mathbed": 8,
    "mathkon": 4,
    "mathkor": 5,
    "mathkork": 5,
    "mathlist": 5,
    "mavergleichskette": 4,
    "mavergleichskettek": 4,
    "maabb": 4,
    "maabbele": 6,
    "punkte": 1,
    "footnote": 1,
}

MATH_WRAPPERS = {
    "mathdisp", "mavergleichskettedisp", "mavergleichskettedisplang",
    "mavergleichskettealign", "mavergleichskettealigndrucklinks",
    "mavergleichskettealignhandlinks", "mavergleichskettedisphandlinks",
}

ENTITY_LABELS = {
    "inputdefinition": "Definisi",
    "inputaxiom": "Aksioma",
    "inputnotation": "Notasi",
    "inputbeispiel": "Contoh",
    "inputbemerkung": "Catatan",
    "inputverfahren": "Prosedur",
    "inputkonstruktion": "Konstruksi",
    "inputfrage": "Pertanyaan",
    "inputproblem": "Masalah",
    "inputsituation": "Situasi",
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_binding(path: Path, root: Path) -> dict[str, Any]:
    data = path.read_bytes()
    return {
        "path": path.relative_to(root).as_posix(),
        "bytes": len(data),
        "sha256": sha256_bytes(data),
    }


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(value.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8"))


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def load_json_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def safe_project_path(root: Path, relative: str) -> Path:
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise RuntimeError(f"project-relative path escapes root: {relative}") from exc
    return candidate


def strip_tex_comments(text: str) -> str:
    output: list[str] = []
    for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        cut = len(line)
        for i, char in enumerate(line):
            if char != "%":
                continue
            slashes = 0
            j = i - 1
            while j >= 0 and line[j] == "\\":
                slashes += 1
                j -= 1
            if slashes % 2 == 0:
                cut = i
                break
        output.append(line[:cut])
    return "\n".join(output)


def split_top_level_paragraphs(text: str) -> list[str]:
    """Split blank-line paragraphs without cutting through macro arguments."""
    parts: list[str] = []
    start = 0
    depth = 0
    math_mode = False
    i = 0
    while i < len(text):
        char = text[i]
        escaped = i > 0 and text[i - 1] == "\\"
        if char == "$" and not escaped:
            math_mode = not math_mode
        elif not math_mode and not escaped:
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth < 0:
                    raise RuntimeError("unbalanced closing group in text flow")
        if char == "\n" and depth == 0 and not math_mode:
            match = re.match(r"\n[ \t]*\n+", text[i:])
            if match:
                parts.append(text[start:i])
                i += len(match.group(0))
                start = i
                continue
        i += 1
    if depth != 0 or math_mode:
        raise RuntimeError("unclosed group or math delimiter in text flow")
    parts.append(text[start:])
    return parts


def command_at(text: str, pos: int) -> tuple[str, int] | None:
    if pos >= len(text) or text[pos] != "\\":
        return None
    if pos + 1 >= len(text):
        return ("", pos + 1)
    if text[pos + 1].isalpha() or text[pos + 1] == "@":
        match = re.match(r"\\([A-Za-z@]+)", text[pos:])
        assert match
        return match.group(1), pos + len(match.group(0))
    return text[pos + 1], pos + 2


def skip_space(text: str, pos: int) -> int:
    while pos < len(text) and text[pos].isspace():
        pos += 1
    return pos


def read_group(text: str, pos: int) -> tuple[str, int]:
    pos = skip_space(text, pos)
    if pos >= len(text) or text[pos] != "{":
        raise RuntimeError(f"expected '{{' near source offset {pos}")
    depth = 1
    start = pos + 1
    i = start
    while i < len(text):
        char = text[i]
        if char in "{}":
            slashes = 0
            j = i - 1
            while j >= 0 and text[j] == "\\":
                slashes += 1
                j -= 1
            if slashes % 2 == 0:
                depth += 1 if char == "{" else -1
                if depth == 0:
                    return text[start:i], i + 1
        i += 1
    raise RuntimeError(f"unclosed group beginning near source offset {pos}")


def read_args(text: str, pos: int, count: int) -> tuple[list[str], int]:
    values: list[str] = []
    for _ in range(count):
        value, pos = read_group(text, pos)
        values.append(value)
    return values, pos


def normalized_media_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.casefold())


class VisibleText(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def html_to_text(value: str) -> str:
    parser = VisibleText()
    parser.feed(value or "")
    return html.unescape(" ".join(" ".join(parser.parts).split()))


def load_media_rights(root: Path) -> dict[str, dict[str, str]]:
    path = root / "authority/brenner_media_rights_manifest.csv"
    rows: dict[str, dict[str, str]] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            title = str(row.get("title", ""))
            filename = title[5:] if title.startswith("File:") else title
            if not filename:
                continue
            row = {str(k): str(v or "") for k, v in row.items()}
            row["filename"] = filename
            row["creator_text"] = html_to_text(row.get("artist_html", ""))
            rows[normalized_media_name(filename)] = row
    return rows


def wiki_link(value: str) -> str:
    target, sep, label = value.partition("|")
    shown = label if sep else target.rsplit("/", 1)[-1]
    url = "https://de.wikiversity.org/wiki/" + quote(target.strip().replace(" ", "_"), safe="/():")
    return f'<a class="source-link" href="{html.escape(url, quote=True)}">{html.escape(shown.strip())}</a>'


def expand_math(value: str) -> str:
    """Expand only source-specific math macros; retain standard TeX verbatim."""
    value = value.replace("[[", "\\text{").replace("]]", "}")
    output: list[str] = []
    pos = 0
    chain_macros = {
        "vergleichskette", "vergleichskettelang", "vergleichskettek",
        "vergleichskettedisphandlinks", "vergleichskettealign",
        "vergleichskettealigndrucklinks", "vergleichskettealignhandlinks",
        "vergleichskettefortsetzung", "vergleichskettefortsetzungk",
        "vergleichskettefortsetzungalign",
    }
    constants = {
        "R": r"\mathbb{R}", "N": r"\mathbb{N}", "Z": r"\mathbb{Z}",
        "Q": r"\mathbb{Q}", "C": r"\mathbb{C}", "Complex": r"\mathbb{C}",
        "defeq": ":=", "defeqr": "=:",
    }
    while pos < len(value):
        if value[pos] != "\\":
            output.append(value[pos])
            pos += 1
            continue
        parsed = command_at(value, pos)
        assert parsed
        name, after = parsed
        if name in constants:
            output.append(constants[name])
            pos = after
            continue
        if name == "f":
            # The frozen expansion occasionally emits ``\f`` for the variable f.
            output.append("f")
            pos = after
            continue
        if name in chain_macros:
            args: list[str] = []
            cursor = after
            maximum = 8 if name.startswith("vergleichskettefortsetzung") else 9
            while len(args) < maximum and skip_space(value, cursor) < len(value) and value[skip_space(value, cursor)] == "{":
                arg, cursor = read_group(value, cursor)
                args.append(arg)
            if len(args) < 3:
                excerpt = " ".join(value[max(0, pos - 60):min(len(value), pos + 220)].split())
                raise RuntimeError(f"cannot expand short math chain \\{name}: {excerpt}")
            pos = cursor
            args = [expand_math(arg) for arg in args]
            output.append(" ".join(arg for arg in args if arg.strip()))
            continue
        if name == "betrag":
            try:
                args, pos = read_args(value, after, 1)
            except RuntimeError as exc:
                excerpt = " ".join(value[max(0, pos - 60):min(len(value), pos + 220)].split())
                raise RuntimeError(f"cannot expand math macro \\{name}: {excerpt}") from exc
            args = [expand_math(arg) for arg in args]
            output.append(r"\left|" + args[0] + r"\right|")
            continue
        output.append(value[pos:after])
        pos = after
    return " ".join("".join(output).split())


def math_span(value: str, display: bool = False, nested: bool = False) -> str:
    tex = expand_math(value.strip())
    delimiters = (r"\[", r"\]") if display else (r"\(", r"\)")
    tag = "div" if display and not nested else "span"
    role = ' role="math" aria-label="Rumus matematika dalam notasi TeX"'
    return f'<{tag} class="math {"display" if display else "inline"}"{role}>{html.escape(delimiters[0] + tex + delimiters[1])}</{tag}>'


def math_macro_value(name: str, args: list[str]) -> str:
    if name == "mathdisp":
        return f"{args[0]} {args[1]}"
    if name == "mathdisplayteile":
        return f"{args[0]} \\qquad {args[1]} {args[2]}"
    if name.startswith("mavergleichskette"):
        return " ".join(args)
    if name == "mathlistdisp":
        parts = [args[0], args[1] or ",", args[2], args[3] or ",", args[4]]
        return " ".join(parts)
    if name == "alignier":
        return r"\begin{aligned}" + args[0] + " " + args[1] + r"\end{aligned}"
    if name in ("maabbdisp", "maabbnamedisp"):
        prefix = args[0] + r"\colon " if args[0].strip() else ""
        return prefix + args[1] + r"\longrightarrow " + args[2] + args[3]
    if name in ("maabbeledisp", "maabbeledispvar", "maabbelementzeiledisplay", "maabbelementdoppelzeiledisplay"):
        prefix = args[0] + r"\colon " if args[0].strip() else ""
        return prefix + args[1] + r"\longrightarrow " + args[2] + ", " + args[3] + r"\longmapsto " + args[4] + args[5]
    raise RuntimeError(f"unhandled display-math macro: {name}")


@dataclass
class SurfaceState:
    unit: int
    kind: str
    stable_id: str
    fact_counter: int = 0
    section_counter: int = 0
    exercise_counter: int = 0
    figure_counter: int = 0
    semantic_counts: dict[str, int] = field(default_factory=dict)


class Renderer:
    def __init__(self, root: Path, rights: dict[str, dict[str, str]]) -> None:
        self.root = root
        self.rights = rights
        self.media_used: dict[str, dict[str, Any]] = {}
        self.figure_occurrences: list[dict[str, Any]] = []
        self.unknown_text_commands: set[str] = set()

    @property
    def has_animated_media(self) -> bool:
        return any("animation" in item for item in self.media_used.values())

    def _animated_media_spec(
        self,
        filename: str,
        state: SurfaceState,
        description: str,
    ) -> dict[str, Any]:
        """Resolve and verify the deterministic static-first contract for a GIF.

        Animated reader media is admitted only when the unit media config, the
        deterministic derivative receipt, and the bounded animation QA receipt
        agree with the live canonical and frame-zero bytes.  The regular static
        image path never calls this method.
        """

        def expect(condition: bool, message: str) -> None:
            if not condition:
                raise RuntimeError(f"animated media closure failed for {filename}: {message}")

        config_path = self.root / "source/unit_media.json"
        media_receipt_path = self.root / f"qa/unit-{state.unit:02d}_media.json"
        animation_qa_path = self.root / f"qa/unit-{state.unit:02d}/ANIMATED_MEDIA_QA.json"
        for path in (config_path, media_receipt_path, animation_qa_path):
            expect(path.is_file(), f"missing required binding {path.relative_to(self.root)}")

        config = load_json_object(config_path)
        units = config.get("units")
        expect(isinstance(units, dict), "source/unit_media.json has no units object")
        unit_config = units.get(str(state.unit), {}) if isinstance(units, dict) else {}
        config_media = unit_config.get("media", []) if isinstance(unit_config, dict) else []
        config_matches = [
            item for item in config_media
            if isinstance(item, dict) and item.get("filename") == filename
        ] if isinstance(config_media, list) else []
        expect(len(config_matches) == 1, "unit media config does not contain exactly one matching GIF")
        config_item = config_matches[0]
        print_basename = str(config_item.get("print_basename", "")).strip()
        expect(bool(print_basename), "unit media config has no print_basename")

        media_receipt = load_json_object(media_receipt_path)
        expect(media_receipt.get("unit_number") == state.unit, "media receipt unit number differs")
        expect(media_receipt.get("media_config") == "source/unit_media.json", "media receipt config path differs")
        config_binding = file_binding(config_path, self.root)
        receipt_media = media_receipt.get("media", [])
        receipt_matches = [
            item for item in receipt_media
            if isinstance(item, dict) and item.get("filename") == filename
        ] if isinstance(receipt_media, list) else []
        expect(len(receipt_matches) == 1, "media receipt does not contain exactly one matching GIF")
        receipt_item = receipt_matches[0]

        canonical_relative = str(receipt_item.get("canonical_path", ""))
        canonical_path = safe_project_path(self.root, canonical_relative)
        expect(canonical_relative == f"authority/media/{filename}", "canonical path differs from rights media path")
        expect(canonical_path.is_file(), "canonical GIF bytes are missing")
        canonical_binding = file_binding(canonical_path, self.root)
        expect(receipt_item.get("canonical_bytes") == canonical_binding["bytes"], "canonical GIF byte count differs")
        expect(receipt_item.get("canonical_sha256") == canonical_binding["sha256"], "canonical GIF SHA-256 differs")

        derivative = receipt_item.get("derivative", {})
        expect(isinstance(derivative, dict), "static derivative record is absent")
        expect(derivative.get("source_kind") == "gif", "static derivative is not declared as GIF-derived")
        expect(derivative.get("frame_index") == 0, "static derivative is not frame zero")
        static_relative = str(derivative.get("path", ""))
        static_path = safe_project_path(self.root, static_relative)
        expect(static_relative == f"build/generated/media/{print_basename}.png", "static derivative path differs from configured print basename")
        expect(static_path.is_file(), "static frame bytes are missing")
        static_binding = file_binding(static_path, self.root)
        expect(derivative.get("bytes") == static_binding["bytes"], "static frame byte count differs")
        expect(derivative.get("sha256") == static_binding["sha256"], "static frame SHA-256 differs")

        animation_qa = load_json_object(animation_qa_path)
        expect(animation_qa.get("status") == "pass", "animation QA status is not pass")
        expect(animation_qa.get("unit_id") == f"o011-brenner-u{state.unit:02d}", "animation QA unit ID differs")
        canonical_qa = animation_qa.get("canonical_animation", {})
        fallback_qa = animation_qa.get("static_pdf_fallback", {})
        expect(isinstance(canonical_qa, dict), "canonical animation QA record is absent")
        expect(isinstance(fallback_qa, dict), "static fallback QA record is absent")
        expect(canonical_qa.get("filename") == filename, "animation QA filename differs")
        expect(canonical_qa.get("path") == canonical_relative, "animation QA canonical path differs")
        expect(canonical_qa.get("bytes") == canonical_binding["bytes"], "animation QA canonical byte count differs")
        expect(canonical_qa.get("sha256") == canonical_binding["sha256"], "animation QA canonical SHA-256 differs")
        expect(fallback_qa.get("frame_index") == 0, "animation QA fallback is not frame zero")
        expect(fallback_qa.get("path") == static_relative, "animation QA fallback path differs")
        expect(fallback_qa.get("bytes") == static_binding["bytes"], "animation QA fallback byte count differs")
        expect(fallback_qa.get("sha256") == static_binding["sha256"], "animation QA fallback SHA-256 differs")
        expect(fallback_qa.get("canonical_animation_unchanged") is True, "animation QA does not preserve canonical bytes")

        qa_description = " ".join(str(animation_qa.get("reader_description", "")).split())
        source_description = " ".join(description.split())
        expect(bool(qa_description), "Indonesian reader description is empty")
        expect(source_description == qa_description, "source caption differs from the admitted Indonesian reader description")

        return {
            "default_state": "static_frame",
            "canonical_filename": filename,
            "canonical_source": canonical_binding,
            "static_filename": static_path.name,
            "static_source": static_binding,
            "static_frame_index": 0,
            "description": qa_description,
            "prefers_reduced_motion": "animation remains stopped",
            "bindings": {
                "unit_media_config": config_binding,
                "unit_media_receipt": file_binding(media_receipt_path, self.root),
                "animated_media_qa": file_binding(animation_qa_path, self.root),
            },
        }

    def render_inline(self, text: str, state: SurfaceState) -> str:
        output: list[str] = []
        pos = 0
        while pos < len(text):
            if text.startswith("__NOEDITSECTION__", pos):
                pos += len("__NOEDITSECTION__")
                continue
            if text.startswith("[[", pos):
                end = text.find("]]", pos + 2)
                if end < 0:
                    raise RuntimeError("unclosed MediaWiki link in translated source")
                output.append(wiki_link(text[pos + 2:end]))
                pos = end + 2
                continue
            char = text[pos]
            if text.startswith("---", pos):
                output.append("—")
                pos += 3
                continue
            if text.startswith("--", pos):
                output.append("–")
                pos += 2
                continue
            if char == "$":
                end = pos + 1
                while True:
                    end = text.find("$", end)
                    if end < 0:
                        raise RuntimeError("unclosed inline math delimiter")
                    if end == 0 or text[end - 1] != "\\":
                        break
                    end += 1
                output.append(math_span(text[pos + 1:end]))
                pos = end + 1
                continue
            if char == "{":
                group, pos = read_group(text, pos)
                output.append(self.render_inline(group, state))
                continue
            if char == "}":
                raise RuntimeError("unexpected closing group in text flow")
            if char != "\\":
                if char == "~":
                    output.append("&nbsp;")
                else:
                    output.append(html.escape(char))
                pos += 1
                continue

            name, after = command_at(text, pos) or ("", pos + 1)
            if name == "(":
                end = text.find(r"\)", after)
                if end < 0:
                    raise RuntimeError("unclosed \\( inline math delimiter")
                output.append(math_span(text[after:end]))
                pos = end + 2
                continue
            if name in ("\\", "newline", "par"):
                output.append("<br>")
                pos = after
                continue
            nested_display_names = MATH_WRAPPERS | {
                "mathdisplayteile", "mathlistdisp", "alignier", "maabbdisp",
                "maabbnamedisp", "maabbeledisp", "maabbeledispvar",
                "maabbelementzeiledisplay", "maabbelementdoppelzeiledisplay",
            }
            if name in nested_display_names:
                args, pos = read_args(text, after, STRUCTURAL_ARITY[name])
                output.append(math_span(math_macro_value(name, args), display=True, nested=True))
                continue
            if name in (",", ";", ":", "!", " "):
                output.append(" ")
                pos = after
                continue
            if name in INLINE_ARITY:
                try:
                    args, pos = read_args(text, after, INLINE_ARITY[name])
                except RuntimeError as exc:
                    excerpt = " ".join(text[max(0, pos - 30):min(len(text), pos + 180)].split())
                    raise RuntimeError(
                        f"cannot parse \\{name} in Unit {state.unit} {state.kind}: {excerpt}"
                    ) from exc
                if name in ("mathl", "mathlk"):
                    output.append(math_span(args[0]) + self.render_inline(args[1], state))
                    continue
                if name == "mathind":
                    output.append(math_span(args[0]) + ", " + math_span(args[1]) + self.render_inline(args[2], state))
                    continue
                if name == "mathkon":
                    output.append(math_span(args[0]) + self.render_inline(args[1], state) + math_span(args[2]) + self.render_inline(args[3], state))
                    continue
                if name in ("mathkor", "mathkork"):
                    output.append(self.render_inline(args[0], state) + math_span(args[1]) + self.render_inline(args[2], state) + " " + math_span(args[3]) + self.render_inline(args[4], state))
                    continue
                if name == "mathlist":
                    output.append(math_span(args[0]) + (self.render_inline(args[1], state) or ",") + " " + math_span(args[2]) + (self.render_inline(args[3], state) or ",") + " " + math_span(args[4]))
                    continue
                if name == "mathbed":
                    output.append(math_span(args[0]))
                    output.append(self.render_inline(args[1], state) if args[1].strip() else ", ")
                    output.append(math_span(args[2]))
                    if args[4].strip():
                        output.append((self.render_inline(args[3], state) if args[3].strip() else ", ") + math_span(args[4]))
                    if args[6].strip():
                        output.append((self.render_inline(args[5], state) if args[5].strip() else ", ") + math_span(args[6]))
                    output.append(self.render_inline(args[7], state))
                    continue
                if name.startswith("mavergleichskette"):
                    output.append(math_span(" ".join(args)))
                    continue
                if name == "maabb":
                    value = (args[0] + r"\colon " if args[0].strip() else "") + args[1] + r"\longrightarrow " + args[2] + args[3]
                    output.append(math_span(value))
                    continue
                if name == "maabbele":
                    value = (args[0] + r"\colon " if args[0].strip() else "") + args[1] + r"\longrightarrow " + args[2] + ", " + args[3] + r"\longmapsto " + args[4] + args[5]
                    output.append(math_span(value))
                    continue
                rendered = [self.render_inline(arg, state) for arg in args]
                if name == "definitionsverweis":
                    output.append(rendered[0] + rendered[2])
                elif name == "definitionsverweisanfuehrung":
                    output.append("“" + rendered[0] + "”" + rendered[2])
                elif name in ("definitionswort", "definitionswortteil", "definitionswortenp", "stichwort", "betonung", "emph", "textit"):
                    output.append(f"<em>{rendered[0]}</em>" + (rendered[1] if len(rendered) > 1 else ""))
                elif name == "textbf":
                    output.append(f"<strong>{rendered[0]}</strong>")
                elif name in ("definitionswortpraemath", "stichwortpraemath"):
                    output.append(math_span(args[0]) + "-<em>" + rendered[1] + "</em>" + rendered[2])
                elif name in ("anfuehrung", "anfuehrungenglisch"):
                    output.append("“" + rendered[0] + "”" + rendered[1])
                elif name == "zusatz":
                    output.append("(" + rendered[0] + ")" + rendered[1])
                elif name == "zusatzklammer":
                    output.append("(" + rendered[0] + rendered[1] + ")" + rendered[2])
                elif name == "zusatzgs":
                    output.append("—" + rendered[0] + "—" + rendered[2])
                elif name in ("zusatzfussnote", "footnote"):
                    body = rendered[0] + (rendered[1] if len(rendered) > 1 else "")
                    tail = rendered[2] if len(rendered) > 2 else ""
                    output.append(f'<span class="footnote" role="note">Catatan: {body}</span>{tail}')
                elif name.startswith("fakt") or name.startswith("teilbeweis") or name.startswith("fallunterscheidung"):
                    output.append("".join(rendered))
                elif name == "punkte":
                    if args[0].strip():
                        output.append(f'<span class="points">{rendered[0]} poin</span>')
                else:
                    raise RuntimeError(f"unhandled inline macro: {name}")
                continue
            if name in ("smallskip", "medskip", "bigskip", "noindent", "quad", "qquad", "hfill"):
                output.append(" ")
                pos = after
                continue
            if name in ("hspace", "vspace"):
                _, pos = read_args(text, after, 1)
                output.append(" ")
                continue
            if name in ("%", "_", "&", "#", "{", "}"):
                output.append(html.escape(name))
                pos = after
                continue
            # Accent commands are retained as their visible argument.
            if name in ('"', "'", "`", "^", "~", "c", "v", "t"):
                try:
                    args, pos = read_args(text, after, 1)
                    output.append(self.render_inline(args[0], state))
                except RuntimeError:
                    pos = after
                continue
            self.unknown_text_commands.add(name)
            raise RuntimeError(f"unknown text-mode command \\{name} in Unit {state.unit} {state.kind}")
        return "".join(output)

    def _paragraph(self, value: str, state: SurfaceState) -> str:
        rendered = self.render_inline(value.strip(), state).strip()
        return f"<p>{rendered}</p>" if rendered else ""

    def _entity(self, name: str, args: list[str], state: SurfaceState) -> str:
        state.fact_counter += 1
        state.semantic_counts[name] = state.semantic_counts.get(name, 0) + 1
        label = ENTITY_LABELS[name]
        anchor = f"{state.stable_id}-fact-{state.fact_counter:03d}"
        subtitle = self.render_inline(args[0].strip(), state) if args[0].strip() else ""
        heading = f"{label} {state.unit}.{state.fact_counter}" + (f" ({subtitle})" if subtitle else "")
        return (
            f'<article class="semantic-block {html.escape(label.casefold())}" id="{anchor}" data-entity="{name}">'
            f'<h4>{heading}</h4>{self.render_flow(args[1], state)}</article>'
        )

    def _fact(self, name: str, args: list[str], state: SurfaceState) -> str:
        state.fact_counter += 1
        state.semantic_counts[name] = state.semantic_counts.get(name, 0) + 1
        anchor = f"{state.stable_id}-fact-{state.fact_counter:03d}"
        kind = self.render_inline(args[1].strip(), state) or "Teorema"
        subtitle = self.render_inline(args[2].strip(), state) if args[2].strip() else ""
        heading = f"{kind} {state.unit}.{state.fact_counter}" + (f" ({subtitle})" if subtitle else "")
        proof = ""
        if name == "inputfaktbeweis":
            proof = f'<section class="proof" aria-label="Bukti"><h5>Bukti</h5>{self.render_flow(args[4], state)}</section>'
        elif name == "inputfaktbeweisnichtvorgefuehrt":
            proof = '<section class="proof"><h5>Bukti</h5><p>Bukti ini tidak disampaikan dalam kuliah sumber.</p></section>'
        elif name == "inputfaktbeweistrivial":
            proof = '<section class="proof"><h5>Bukti</h5><p>Hal ini langsung.</p></section>'
        elif name == "inputfaktuebergangbeweis":
            proof = self.render_flow(args[4], state) + f'<section class="proof"><h5>Bukti</h5>{self.render_flow(args[5], state)}</section>'
        statement_index = 3
        return (
            f'<article class="semantic-block theorem" id="{anchor}" data-entity="{name}" '
            f'data-source-local-id="{html.escape(args[0].strip(), quote=True)}">'
            f'<h4>{heading}</h4>{self.render_flow(args[statement_index], state)}{proof}</article>'
        )

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
            badges.append('<span class="solution-marker">Solusi sumber tersedia</span>')
        body = self.render_flow(args[1], state)
        hint = self.render_flow(args[2], state) if args[2].strip() else ""
        if hint:
            body += f'<aside class="hint"><h5>Petunjuk sumber</h5>{hint}</aside>'
        return (
            f'<article class="exercise{" has-source-solution" if supplied else ""}" id="{anchor}" '
            f'data-entity="exercise" data-source-solution="{"true" if supplied else "false"}">'
            f'<h4>Soal {state.unit}.{number}</h4>{"".join(badges)}{body}</article>'
        )

    def _figure(self, body: str, state: SurfaceState) -> str:
        macro_match = re.search(r"\\bildeinlesung(?:svg|png|PNG|jpg|JPG|jpeg|gif|GIF|xcf)\s*\{([^{}]+)\}\s*\{([^{}]*)\}", body)
        if not macro_match:
            raise RuntimeError(f"cannot identify image in Unit {state.unit} {state.kind}")
        stem = macro_match.group(1).strip().replace("_", " ")
        extension = macro_match.group(2).strip().lower()
        if extension == "jpeg":
            extension = "jpg"
        wanted = normalized_media_name(stem + "." + extension)
        rights = self.rights.get(wanted)
        if rights is None:
            raise RuntimeError(f"media absent from frozen rights manifest: {stem}.{extension}")
        filename = rights["filename"]
        source_path = self.root / "authority/media" / filename
        if not source_path.is_file():
            raise RuntimeError(f"admitted media bytes missing: {source_path}")
        caption = ""
        caption_pos = body.find("\\bildtext")
        if caption_pos >= 0:
            _, after = command_at(body, caption_pos) or ("", caption_pos)
            caption_args, _ = read_args(body, after, 1)
            caption = self.render_inline(caption_args[0].strip(), state)
        state.figure_counter += 1
        state.semantic_counts["figure"] = state.semantic_counts.get("figure", 0) + 1
        anchor = f"{state.stable_id}-fig-{state.figure_counter:03d}"
        media_url = "assets/media/" + quote(filename)
        fallback_alt = "Ilustrasi sumber: " + Path(filename).stem.replace("_", " ")
        alt = re.sub(r"<[^>]+>", "", html.unescape(caption)).strip() or fallback_alt
        creator = rights.get("creator_text") or "Pembuat dicatat pada manifes hak media"
        license_name = rights.get("license") or "Lisensi per berkas"
        description_url = rights.get("description_url") or rights.get("original_url")
        license_url = rights.get("license_url")
        rights_parts = [html.escape(creator), html.escape(license_name)]
        if license_url:
            rights_parts[-1] = f'<a href="{html.escape(license_url, quote=True)}">{html.escape(license_name)}</a>'
        if description_url:
            rights_parts.append(f'<a href="{html.escape(description_url, quote=True)}">sumber media</a>')
        binding = file_binding(source_path, self.root)
        media_item: dict[str, Any] = {"source": binding, "rights": rights}
        occurrence: dict[str, Any] = {
            "id": anchor,
            "filename": filename,
            "caption_supplied": bool(caption),
            "caption_text": alt if caption else None,
            "alt": alt,
        }
        caption_html = f'<span class="figure-caption">{caption}</span>' if caption else ""
        if extension == "gif":
            if not caption:
                raise RuntimeError(f"animated media requires a meaningful Indonesian caption: {filename}")
            animation = self._animated_media_spec(filename, state, html_to_text(caption))
            media_item["animation"] = animation
            occurrence.update({
                "media_kind": "animated",
                "default_state": "static_frame",
                "static_filename": animation["static_filename"],
                "play_stop_controls": True,
                "canonical_download": True,
                "prefers_reduced_motion": True,
            })
            self.media_used[filename] = media_item
            self.figure_occurrences.append(occurrence)
            image_id = f"{anchor}-image"
            caption_id = f"{anchor}-caption"
            status_id = f"{anchor}-animation-status"
            static_url = "assets/media/" + quote(str(animation["static_filename"]))
            return (
                f'<figure id="{anchor}" class="animated-media" data-entity="figure" data-animation-state="stopped">'
                f'<div class="animated-media-stage"><img id="{image_id}" class="animated-media-image" '
                f'src="{html.escape(static_url, quote=True)}" data-static-src="{html.escape(static_url, quote=True)}" '
                f'data-animated-src="{html.escape(media_url, quote=True)}" alt="{html.escape(alt, quote=True)}" '
                f'aria-describedby="{caption_id}" loading="lazy"></div>'
                f'<div class="animated-media-controls" role="group" aria-label="Kontrol animasi">'
                f'<button type="button" data-animation-action="play" aria-controls="{image_id}">Putar animasi</button>'
                f'<button type="button" data-animation-action="stop" aria-controls="{image_id}" disabled>Hentikan animasi</button>'
                f'<a class="animated-media-download" href="{html.escape(media_url, quote=True)}" '
                f'download="{html.escape(filename, quote=True)}">Unduh GIF asli</a>'
                f'<span class="animated-media-status" id="{status_id}" role="status" aria-live="polite">'
                f'Animasi dihentikan; bingkai statis ditampilkan.</span></div>'
                f'<figcaption id="{caption_id}">{caption_html}'
                f'<span class="media-rights">{" · ".join(rights_parts)}</span></figcaption></figure>'
            )
        self.media_used[filename] = media_item
        self.figure_occurrences.append(occurrence)
        return (
            f'<figure id="{anchor}" data-entity="figure"><img src="{html.escape(media_url, quote=True)}" '
            f'alt="{html.escape(alt, quote=True)}" loading="lazy">'
            f'<figcaption>{caption_html}<span class="media-rights">{" · ".join(rights_parts)}</span></figcaption></figure>'
        )

    def render_flow(self, raw_text: str, state: SurfaceState) -> str:
        text = strip_tex_comments(raw_text).replace("__NOEDITSECTION__", "")
        text = re.sub(r"\[\[(?:Kategorie|Category):Latexseite(?:\|[^\]]*)?\]\]", "", text, flags=re.IGNORECASE)
        output: list[str] = []
        buffer: list[str] = []

        def flush() -> None:
            if not buffer:
                return
            value = "".join(buffer)
            buffer.clear()
            for paragraph in split_top_level_paragraphs(value):
                rendered = self._paragraph(paragraph, state)
                if rendered:
                    output.append(rendered)

        pos = 0
        depth = 0
        math_mode = False
        while pos < len(text):
            if text[pos] != "\\":
                escaped = pos > 0 and text[pos - 1] == "\\"
                if text[pos] == "$" and not escaped:
                    math_mode = not math_mode
                elif not math_mode and not escaped:
                    if text[pos] == "{":
                        depth += 1
                    elif text[pos] == "}":
                        depth -= 1
                buffer.append(text[pos])
                pos += 1
                continue
            parsed = command_at(text, pos)
            assert parsed
            name, after = parsed
            if depth == 0 and not math_mode and name == "[":
                end = text.find(r"\]", after)
                if end < 0:
                    raise RuntimeError(f"unclosed \\[ display in Unit {state.unit} {state.kind}")
                flush()
                output.append(math_span(text[after:end], display=True))
                pos = end + 2
                continue
            if depth != 0 or math_mode or name not in STRUCTURAL_ARITY:
                buffer.append(text[pos:after])
                pos = after
                continue
            args, new_pos = read_args(text, after, STRUCTURAL_ARITY[name])
            flush()
            pos = new_pos
            if name == "setcounter" or name == "bildlizenz":
                continue
            if name == "zwischenueberschrift":
                state.section_counter += 1
                state.semantic_counts[name] = state.semantic_counts.get(name, 0) + 1
                anchor = f"{state.stable_id}-s{state.section_counter:02d}"
                output.append(f'<h3 class="source-section" id="{anchor}" data-entity="source-section">{self.render_inline(args[0], state)}</h3>')
            elif name in ENTITY_LABELS:
                output.append(self._entity(name, args, state))
            elif name.startswith("inputfakt"):
                output.append(self._fact(name, args, state))
            elif name == "inputbeweis":
                output.append(f'<section class="proof" aria-label="Bukti"><h5>Bukti</h5>{self.render_flow(args[0], state)}</section>')
            elif name.startswith("fakt") or name.startswith("teilbeweis") or name.startswith("fallunterscheidung"):
                output.append("".join(self.render_flow(arg, state) for arg in args if arg.strip()))
            elif name in ("inputaufgabe", "inputaufgabegibtloesung"):
                output.append(self._exercise(name, args, state))
            elif name == "bild":
                output.append(self._figure(args[0], state))
            elif name in MATH_WRAPPERS or name in (
                "mathdisplayteile", "mathlistdisp", "alignier", "maabbdisp",
                "maabbnamedisp", "maabbeledisp", "maabbeledispvar",
                "maabbelementzeiledisplay", "maabbelementdoppelzeiledisplay",
            ):
                output.append(math_span(math_macro_value(name, args), display=True))
            elif name.startswith("aufzaehlung"):
                alpha = " abc" if name.endswith("abc") else ""
                items = "".join(f"<li>{self.render_flow(arg, state)}</li>" for arg in args)
                output.append(f'<ol class="source-list{alpha}">{items}</ol>')
            else:
                raise RuntimeError(f"unhandled structural macro: {name}")
        flush()
        return "\n".join(output)


def source_files(root: Path) -> list[Path]:
    paths: list[Path] = []
    for unit in range(1, 11):
        directory = root / f"source/units/unit-{unit:02d}"
        lecture = directory / f"lecture{unit:02d}.id.tex"
        worksheet = directory / f"worksheet{unit:02d}.id.tex"
        if not lecture.is_file() or not worksheet.is_file():
            raise RuntimeError(f"missing translated reader surface for Unit {unit}")
        paths.extend((lecture, worksheet))
        paths.extend(sorted(directory.glob(f"worksheet{unit:02d}_exercise*_solution.id.tex")))
    return paths


def reader_head_extension(renderer: Renderer) -> str:
    return (
        f'\n  <script id="animated-media-controller">{ANIMATED_MEDIA_JS}</script>'
        if renderer.has_animated_media else ""
    )


def render_reader(root: Path, renderer: Renderer) -> tuple[str, dict[str, Any]]:
    navigation: list[str] = []
    units_html: list[str] = []
    topology: dict[str, Any] = {}
    for unit in range(1, 11):
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

        solutions_html: list[str] = []
        solution_indices: list[int] = []
        for path in sorted((root / f"source/units/unit-{tag}").glob(f"worksheet{tag}_exercise*_solution.id.tex")):
            match = re.search(r"exercise(\d+)_solution", path.name)
            if not match:
                raise RuntimeError(f"unrecognized solution filename: {path}")
            index = int(match.group(1))
            solution_indices.append(index)
            stable_id = f"{worksheet_id}-e{index:03d}-solution"
            solution_state = SurfaceState(unit, f"solution-{index}", stable_id)
            body = renderer.render_flow(path.read_text(encoding="utf-8"), solution_state)
            solutions_html.append(
                f'<article class="source-solution" id="{stable_id}" data-entity="source-supplied-solution" '
                f'data-solves="{worksheet_id}-e{index:03d}"><h4>Solusi sumber untuk Soal {unit}.{index}</h4>{body}</article>'
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
            "source_supplied_solution_indices": solution_indices,
        }

    animated_media_head = reader_head_extension(renderer)
    document = f'''<!doctype html>
<html lang="id-ID">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="Pembaca reflowable Bahasa Indonesia untuk Kuliah dan Lembar Kerja 1–10 dari Differentialgeometrie (Osnabrück 2023).">
  <title>Geometri Diferensial dan Manifold Mulus — Pembaca hingga Unit 10</title>
  <link rel="stylesheet" href="assets/reader.css">
  <script id="mathjax-config">window.MathJax={{tex:{{inlineMath:[["\\\\(","\\\\)"]],displayMath:[["\\\\[","\\\\]"]],packages:{{"[+]":["ams"]}}}},options:{{enableMenu:true}}}};</script>
  <script defer src="{MATHJAX_URL}"></script>
  <script id="deep-link-stabilizer">(()=>{{const align=()=>{{if(!location.hash)return;const target=document.getElementById(decodeURIComponent(location.hash.slice(1)));if(!target)return;const root=document.documentElement;const previous=root.style.scrollBehavior;root.style.scrollBehavior="auto";target.scrollIntoView({{block:"start"}});root.style.scrollBehavior=previous;}};const settle=()=>{{align();requestAnimationFrame(align);setTimeout(align,250);setTimeout(align,1000);setTimeout(align,3000);}};addEventListener("load",settle,{{once:true}});addEventListener("hashchange",settle);if(document.fonts)document.fonts.ready.then(settle);}})();</script>{animated_media_head}
</head>
<body>
<a class="skip-link" href="#reader">Lewati ke isi utama</a>
<header class="masthead">
  <div class="masthead-inner">
    <p class="eyebrow">Edisi Bahasa Indonesia independen · cakupan parsial</p>
    <h1>Geometri Diferensial dan Manifold Mulus</h1>
    <p class="subtitle">Pembaca kumulatif hingga Unit 10</p>
    <p>Holger Brenner · <cite>Differentialgeometrie (Osnabrück 2023)</cite></p>
  </div>
</header>
<nav class="unit-nav" aria-label="Daftar unit"><ol>{''.join(navigation)}</ol></nav>
<main id="reader">
  <section class="frontmatter" id="tentang-edisi">
    <h2>Tentang edisi ini</h2>
    <p>Pembaca ini menerjemahkan Kuliah 1–10 dan Lembar Kerja 1–10 dari kursus Holger Brenner di Wikiversity berbahasa Jerman. Teks sumber digunakan berdasarkan <a href="https://creativecommons.org/licenses/by-sa/4.0/">CC BY-SA 4.0</a>. Terjemahan ini merupakan karya independen dan bukan edisi resmi atau dukungan dari penulis, Wikiversity, atau Wikimedia Foundation.</p>
    <p>Setiap gambar tetap mengikuti lisensi berkasnya sendiri; pembuat, lisensi, dan tautan sumber tercantum langsung pada keterangannya. Rumus, urutan materi, latihan, dan solusi yang disediakan sumber dipertahankan. ID yang stabil dan netral-lokal merupakan lapisan tambahan.</p>
    <p>Proses terjemahan dan produksi edisi dibantu oleh {MODEL_IDENTIFICATION}, di bawah arahan pengguna. Kredit penulis, sumber, dan kontributor manusia tetap dipertahankan.</p>
    <aside class="dependency-note" id="math-rendering"><h3>Tampilan matematika dan penggunaan offline</h3><p>Semua teks, navigasi, gaya, dan media berada di paket ini dan dapat dibaca offline. Perenderan tipografis rumus memakai MathJax dari CDN saat jaringan tersedia. Jika dependensi opsional itu tidak dapat dimuat, sumber TeX setiap rumus tetap terlihat, dapat dipilih, dan tidak menggantikan isi.</p><noscript><p>JavaScript tidak aktif; rumus ditampilkan sebagai sumber TeX.</p></noscript></aside>
    <p><a href="{OFFICIAL_SOURCE}">Sumber resmi kursus</a></p>
  </section>
  {''.join(units_html)}
  <section class="backmatter" id="lisensi-dan-provenans">
    <h2>Lisensi, provenans, dan independensi</h2>
    <p>Teks sumber dan adaptasi Bahasa Indonesia ini didistribusikan berdasarkan CC BY-SA 4.0. Media tidak menerima lisensi umum dari teks; setiap komponen mempertahankan lisensi berkasnya sendiri sebagaimana dicatat pada gambar dan manifes.</p>
    <p>Edisi ini tidak resmi dan tidak menyiratkan dukungan dari Holger Brenner, Wikiversity, para pembuat media, atau Wikimedia Foundation. Identitas sumber, perubahan, dan hash masukan tersedia pada <a href="manifest.json">manifes deterministik pembaca</a>.</p>
  </section>
</main>
<footer><p>Pembaca semantik reflowable · Bahasa Indonesia · Unit 1–10</p></footer>
</body>
</html>
'''
    return document, topology


CSS = r'''/* Deterministic reader stylesheet: O011 HTML v10 */
:root{color-scheme:light dark;--paper:#fffdf9;--ink:#1e293b;--muted:#52606d;--line:#cbd5e1;--accent:#315c8c;--soft:#eef4fa;--proof:#f5f3ff;--max:78rem}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:#e8edf2;color:var(--ink);font:clamp(1rem,.25vw + .95rem,1.15rem)/1.68 Georgia,"Times New Roman",serif}
a{color:#174f87;text-underline-offset:.16em}.skip-link{position:absolute;left:-9999px;top:0}.skip-link:focus{left:1rem;top:1rem;z-index:10;background:#fff;color:#000;padding:.7rem 1rem;border:2px solid #000}
.masthead{background:#18324c;color:#fff}.masthead-inner,main,.unit-nav ol,footer p{width:min(calc(100% - 2rem),var(--max));margin-inline:auto}.masthead-inner{padding:clamp(2rem,6vw,5rem) 0}.masthead h1{font-size:clamp(2.1rem,5vw,4.6rem);line-height:1.04;max-width:18ch;margin:.25rem 0}.subtitle{font-size:clamp(1.25rem,2.5vw,2rem);margin:.3rem 0}.eyebrow{text-transform:uppercase;letter-spacing:.1em;font:700 .76rem/1.4 system-ui,sans-serif}
.unit-nav{position:sticky;top:0;z-index:4;background:#fff;border-bottom:1px solid var(--line);box-shadow:0 2px 10px #0f172a18;overflow-x:auto}.unit-nav ol{display:flex;gap:.35rem;list-style:none;padding:.6rem 0}.unit-nav a{display:block;white-space:nowrap;padding:.4rem .7rem;border-radius:.35rem;text-decoration:none;font:650 .9rem/1.2 system-ui,sans-serif}.unit-nav a:hover,.unit-nav a:focus{background:var(--soft)}
main{background:var(--paper);padding:clamp(1rem,4vw,4rem);box-shadow:0 1rem 4rem #0f172a18}.frontmatter,.backmatter{border-left:.35rem solid var(--accent);padding:0 0 0 clamp(1rem,3vw,2rem);margin:0 0 5rem}.unit{margin:0 0 7rem;scroll-margin-top:5rem}.unit-header{border-bottom:.2rem solid var(--accent);padding-top:1rem}.unit h2{font-size:clamp(1.85rem,4vw,3.2rem);line-height:1.15;margin:.2rem 0 1rem}.lecture,.worksheet,.solutions{margin-top:3rem}.lecture>h3,.worksheet>h3,.solutions>h3{font-size:clamp(1.45rem,3vw,2.2rem);line-height:1.2;border-bottom:1px solid var(--line);padding-bottom:.45rem}.source-section{margin-top:2.5rem}.source-section h3{font:750 clamp(1.2rem,2.2vw,1.6rem)/1.25 system-ui,sans-serif;color:#234e75}
.semantic-block,.exercise,.source-solution{margin:1.5rem 0;padding:clamp(1rem,2.4vw,1.6rem);border:1px solid var(--line);border-radius:.55rem;background:#fff}.semantic-block h4,.exercise h4,.source-solution h4{font:750 1.08rem/1.3 system-ui,sans-serif;margin:0 0 .8rem;color:#234e75}.definition{border-left:.35rem solid #3b82a0}.theorem{border-left:.35rem solid #475569}.exercise{border-left:.35rem solid #7c3aed}.source-solution{border-left:.35rem solid #16856b;background:#f1fbf7}.scope-note,.dependency-note{color:var(--muted)}.solution-marker,.points{display:inline-block;font:650 .78rem/1 system-ui,sans-serif;padding:.32rem .48rem;margin:0 .5rem .5rem 0;border-radius:99rem;background:#e9d5ff;color:#4c1d95}.points{background:#dbeafe;color:#1e3a8a}
.proof,.hint{margin:1rem 0 0;padding:1rem;border-radius:.4rem;background:var(--proof)}.proof h5,.hint h5{font:750 .93rem/1.2 system-ui,sans-serif;margin:0 0 .5rem}.footnote{display:inline-block;border-bottom:1px dotted currentColor;color:var(--muted);font-size:.92em}.source-list{padding-left:1.8rem}.source-list.abc{list-style-type:lower-alpha}.source-list li>p:first-child{margin-top:0}.source-list li>p:last-child{margin-bottom:0}
.math.inline{font-family:"Cambria Math","STIX Two Math",serif;overflow-wrap:anywhere}.math.display{margin:1.25rem 0;padding:.8rem;overflow-x:auto;text-align:center;background:#f8fafc;border-radius:.35rem;color:#111827}
figure{margin:2rem auto;max-width:46rem;text-align:center}figure img{display:block;width:auto;max-width:100%;max-height:34rem;margin:auto;object-fit:contain}figcaption{margin:.65rem auto 0;color:var(--muted);font:.88rem/1.5 system-ui,sans-serif}.figure-caption{display:block;color:var(--ink);font-family:Georgia,"Times New Roman",serif;font-size:1rem}.media-rights{display:block;margin-top:.3rem}
p{max-width:74ch}.semantic-block p,.exercise p,.source-solution p{max-width:none}footer{background:#18324c;color:#fff;padding:1rem 0;margin-top:2rem}footer p{font:600 .85rem/1.4 system-ui,sans-serif}
@media(max-width:46rem){body{background:var(--paper)}main{width:100%;padding:1rem;box-shadow:none}.masthead-inner,.unit-nav ol,footer p{width:min(calc(100% - 1.4rem),var(--max))}.semantic-block,.exercise,.source-solution{padding:1rem}.unit-nav{position:static}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
@media(prefers-color-scheme:dark){:root{--paper:#111827;--ink:#e5e7eb;--muted:#bac5d1;--line:#475569;--soft:#26384d}.unit-nav{background:#111827}.semantic-block,.exercise{background:#172033}.source-solution{background:#102e29}.math.display{background:#f8fafc;color:#111827}.source-section h3,.semantic-block h4,.exercise h4,.source-solution h4,a{color:#8ec5ff}}
'''


ANIMATED_MEDIA_CSS = r'''
/* Static-first controls for admitted animated media. */
.animated-media-stage{display:grid;place-items:center;min-height:8rem}.animated-media-controls{display:flex;flex-wrap:wrap;align-items:center;justify-content:center;gap:.55rem;margin:.8rem auto 0;font:650 .88rem/1.25 system-ui,sans-serif}.animated-media-controls button,.animated-media-download{appearance:none;border:1px solid #315c8c;border-radius:.35rem;background:#fff;color:#174f87;padding:.55rem .75rem;text-decoration:none;cursor:pointer}.animated-media-controls button:hover,.animated-media-controls button:focus-visible,.animated-media-download:hover,.animated-media-download:focus-visible{outline:3px solid #93c5fd;outline-offset:2px}.animated-media-controls button:disabled{border-color:var(--line);color:var(--muted);cursor:not-allowed;opacity:.72}.animated-media-status{flex-basis:100%;color:var(--muted);font-weight:400}.animated-media-image{contain:layout paint}
@media(prefers-reduced-motion:reduce){.animated-media-controls [data-animation-action="play"]::after{content:" (gerak dikurangi)"}}
@media(prefers-color-scheme:dark){.animated-media-controls button,.animated-media-download{background:#172033;color:#8ec5ff;border-color:#8ec5ff}}
'''


ANIMATED_MEDIA_JS = r'''(()=>{const init=()=>{const preference=matchMedia("(prefers-reduced-motion: reduce)");const figures=()=>Array.from(document.querySelectorAll("figure.animated-media"));const setState=(figure,playing,message)=>{const image=figure.querySelector(".animated-media-image");const play=figure.querySelector('[data-animation-action="play"]');const stop=figure.querySelector('[data-animation-action="stop"]');const status=figure.querySelector(".animated-media-status");if(!image||!play||!stop||!status)return;image.src=playing?image.dataset.animatedSrc:image.dataset.staticSrc;figure.dataset.animationState=playing?"playing":"stopped";play.disabled=playing;stop.disabled=!playing;status.textContent=message;};const stop=(figure,message="Animasi dihentikan; bingkai statis ditampilkan.")=>setState(figure,false,message);const play=figure=>{if(preference.matches){stop(figure,"Animasi tetap dihentikan karena preferensi gerak dikurangi aktif.");return;}setState(figure,true,"Animasi sedang diputar.");};figures().forEach(figure=>stop(figure));document.addEventListener("click",event=>{if(!(event.target instanceof Element))return;const button=event.target.closest("button[data-animation-action]");if(!button)return;const figure=button.closest("figure.animated-media");if(!figure)return;if(button.dataset.animationAction==="play")play(figure);else if(button.dataset.animationAction==="stop")stop(figure);});const honorPreference=()=>{if(preference.matches)figures().forEach(figure=>stop(figure,"Animasi dihentikan karena preferensi gerak dikurangi aktif."));};if(preference.addEventListener)preference.addEventListener("change",honorPreference);else if(preference.addListener)preference.addListener(honorPreference);honorPreference();};if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",init,{once:true});else init();})();'''


README_TEXT = f'''Geometri Diferensial dan Manifold Mulus — pembaca HTML hingga Unit 10

Buka index.html pada peramban modern. Teks, navigasi, CSS, dan media tersedia
secara lokal. Rumus dipertahankan sebagai sumber TeX MathJax-compatible.
Perenderan tipografis rumus menggunakan dependensi opsional berikut ketika
jaringan tersedia:

{MATHJAX_URL}

Jika dependensi itu tidak dapat dimuat, sumber TeX rumus tetap terlihat dan
dapat dipilih. Tidak ada latihan atau interaktivitas yang diada-adakan.

Teks sumber dan adaptasi: CC BY-SA 4.0. Setiap media mempertahankan lisensi
per berkas yang dicatat pada keterangannya dan manifest.json. Ini merupakan
edisi independen, bukan edisi resmi dan bukan dukungan penulis/Wikiversity.
'''


ANIMATED_MEDIA_README = '''

Media animasi dimulai dari bingkai statis. Gunakan tombol “Putar animasi” dan
“Hentikan animasi” dengan tetikus atau papan ketik. Preferensi sistem untuk
mengurangi gerak membuat media tetap statis. GIF kanonis juga tersedia melalui
tautan “Unduh GIF asli” pada gambar.
'''


def reader_css(renderer: Renderer) -> str:
    return CSS + (ANIMATED_MEDIA_CSS if renderer.has_animated_media else "")


def reader_readme(renderer: Renderer) -> str:
    return README_TEXT + (ANIMATED_MEDIA_README if renderer.has_animated_media else "")


def stage_media_assets(root: Path, staging: Path, renderer: Renderer) -> list[dict[str, Any]]:
    media_manifest: list[dict[str, Any]] = []
    for filename, item in sorted(renderer.media_used.items()):
        source = safe_project_path(root, str(item["source"]["path"]))
        if file_binding(source, root) != item["source"]:
            raise RuntimeError(f"media bytes changed during export: {filename}")
        target = staging / "assets/media" / filename
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        rights_row = item["rights"]
        manifest_item: dict[str, Any] = {
            "filename": filename,
            "source": item["source"],
            "creator": rights_row.get("creator_text"),
            "license": rights_row.get("license"),
            "license_url": rights_row.get("license_url") or None,
            "description_url": rights_row.get("description_url") or None,
        }
        animation = item.get("animation")
        if isinstance(animation, dict):
            static_source = safe_project_path(root, str(animation["static_source"]["path"]))
            if file_binding(static_source, root) != animation["static_source"]:
                raise RuntimeError(f"static animation frame changed during export: {filename}")
            static_filename = str(animation["static_filename"])
            if Path(static_filename).name != static_filename:
                raise RuntimeError(f"invalid static animation filename: {static_filename}")
            static_target = staging / "assets/media" / static_filename
            if static_target.exists():
                raise RuntimeError(f"animated static-frame target collides with another media file: {static_filename}")
            static_target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(static_source, static_target)
            manifest_item["animation"] = animation
        media_manifest.append(manifest_item)
    return media_manifest


def build(root: Path, output: Path, replace: bool) -> dict[str, Any]:
    root = root.resolve()
    output = output.resolve()
    try:
        output.relative_to(root)
    except ValueError as exc:
        raise RuntimeError("output directory must remain inside the project root") from exc
    inputs = source_files(root)
    initial_bindings = [file_binding(path, root) for path in inputs]
    rights = load_media_rights(root)
    renderer = Renderer(root, rights)
    document, topology = render_reader(root, renderer)

    # Re-read every source after conversion: a concurrent Unit 10 edit must
    # fail the build rather than produce a mixed snapshot.
    final_bindings = [file_binding(path, root) for path in inputs]
    if initial_bindings != final_bindings:
        raise RuntimeError("reader inputs changed during export; rerun after the translation boundary is stable")

    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".html-v10-", dir=output.parent))
    try:
        write_text(staging / "index.html", document)
        write_text(staging / "assets/reader.css", reader_css(renderer))
        write_text(staging / "README.txt", reader_readme(renderer))
        media_manifest = stage_media_assets(root, staging, renderer)
        output_files: list[dict[str, Any]] = []
        for path in sorted(p for p in staging.rglob("*") if p.is_file()):
            output_files.append(file_binding(path, staging))
        manifest = {
            "schema_version": SCHEMA_VERSION,
            "workflow": WORKFLOW,
            "scope": "O011 cumulative Indonesian semantic HTML reader through Unit 10",
            "status": "partial_edition",
            "language": "id-ID",
            "units": list(range(1, 11)),
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
            "topology": topology,
            "media": media_manifest,
            "figures": renderer.figure_occurrences,
            "excluded_reader_metadata": {
                "mediawiki_category_marker": "[[Kategorie:Latexseite]]",
                "occurrences": sum(
                    path.read_text(encoding="utf-8").count("[[Kategorie:Latexseite]]")
                    for path in inputs
                ),
                "preservation": "Retained byte-for-byte in the source inputs bound above; excluded only from reader-visible prose.",
            },
            "files": output_files,
        }
        write_text(staging / "manifest.json", canonical_json(manifest))
        if output.exists():
            if not replace:
                raise RuntimeError(f"output already exists (use --replace for this exact directory): {output}")
            shutil.rmtree(output)
        os.replace(staging, output)
        return manifest
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--replace", action="store_true", help="replace only the exact declared output directory after a complete staged build")
    args = parser.parse_args()
    root = args.root.resolve()
    output = (args.output or (root / "output/html/unit-10")).resolve()
    manifest = build(root, output, args.replace)
    print(canonical_json({
        "status": "pass",
        "output": output.relative_to(root).as_posix(),
        "input_count": len(manifest["inputs"]),
        "file_count": len(manifest["files"]) + 1,
        "media_count": len(manifest["media"]),
    }), end="")


if __name__ == "__main__":
    main()
