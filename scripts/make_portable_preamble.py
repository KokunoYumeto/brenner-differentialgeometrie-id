#!/usr/bin/env python3
"""Derive the portable unit-build compatibility preamble from frozen authority."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


CATEGORY_RE = re.compile(r"\s*\[\[(?:Kategorie|Category):[^\]]+\]\]\s*", re.IGNORECASE)

PORTABLE_APPENDIX = r"""

% Indonesian aliases used by the independent translated reader.
\newtheorem{Teorema}[fakt]{Teorema}
\renewcommand{\proofname}{Bukti}
"""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def relative_path(path: Path, project_root: Path) -> str:
    return path.resolve().relative_to(project_root.resolve()).as_posix()


def replace_once(text: str, old: str, new: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"expected one occurrence, found {count}: {old!r}")
    return text.replace(old, new)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()

    source_bytes = args.input.read_bytes()
    text = source_bytes.decode("utf-8")
    replacements = [
        (r"\usepackage{german}", "% language package supplied by unit wrapper"),
        (r"\usepackage[latin1]{inputenc}", "% UTF-8 input supplied by unit wrapper"),
        (
            r"\newcommand{\bildeinlesung}[1]{../../../brenner/bilderundgraphiken/#1}",
            r"\newcommand{\bildeinlesung}[1]{../authority/media/#1}",
        ),
        (
            r"\renewcommand{\bildeinlesung}[2]{../../Marianne/bilderundgraphiken/#1.#2}",
            r"\renewcommand{\bildeinlesung}[2]{../authority/media/#1.#2}",
        ),
        (
            r"\newcommand{\bildeinlesungpng}[2]{    ../../Marianne/bilderundgraphiken/#1.png}",
            r"\newcommand{\bildeinlesungpng}[2]{../authority/media/#1.png}",
        ),
        (
            r"\newcommand{\bildeinlesungPNG}[2]{    ../../Marianne/bilderundgraphiken/#1.png}",
            r"\newcommand{\bildeinlesungPNG}[2]{../authority/media/#1.png}",
        ),
        (
            r"\newcommand{\bildeinlesungjpg}[2]{    ../../Marianne/bilderundgraphiken/#1.jpg}",
            r"\newcommand{\bildeinlesungjpg}[2]{../authority/media/#1.jpg}",
        ),
        (
            r"\newcommand{\bildeinlesungJPG}[2]{    ../../Marianne/bilderundgraphiken/#1.jpg}",
            r"\newcommand{\bildeinlesungJPG}[2]{../authority/media/#1.jpg}",
        ),
        (
            r"\newcommand{\bildeinlesungjpeg}[2]{    ../../Marianne/bilderundgraphiken/#1.png}",
            r"\newcommand{\bildeinlesungjpeg}[2]{../authority/media/#1.jpg}",
        ),
        (
            r"\newcommand{\bildeinlesungsvg}[2]{    ../../Marianne/bilderundgraphiken/#1.png}",
            r"\newcommand{\bildeinlesungsvg}[2]{generated/media/#1.png}",
        ),
        (
            r"\newcommand{\bildeinlesunggif}[2]{    ../../Marianne/bilderundgraphiken/#1.png}",
            r"\newcommand{\bildeinlesunggif}[2]{../authority/media/#1.png}",
        ),
        (
            r"\newcommand{\bildeinlesungGIF}[2]{    ../../Marianne/bilderundgraphiken/#1.png}",
            r"\newcommand{\bildeinlesungGIF}[2]{../authority/media/#1.png}",
        ),
        (
            r"\newcommand{\bildeinlesungxcf}[2]{    ../../Marianne/bilderundgraphiken/#1.png}",
            r"\newcommand{\bildeinlesungxcf}[2]{../authority/media/#1.png}",
        ),
        (
            r"\newcommand{\Lizenztext}{Lizenzerkl\"arung: Diese Seite wurde von Holger Brenner alias Bocardodarapti auf der deutschsprachigen Wikiversity erstellt und unter die Lizenz CC-by-sa 3.0 gestellt.}",
            r"\newcommand{\Lizenztext}{Teks sumber dibuat oleh Holger Brenner di Wikiversity berbahasa Jerman dan digunakan di sini berdasarkan CC BY-SA 4.0. Media mengikuti lisensi per berkas.}",
        ),
        (r"\newtheorem{fakt}{fakt}[section]", r"\newtheorem{fakt}{Fakta}[section]"),
        (r"\newtheorem{aufgabe}[fakt]{Aufgabe}", r"\newtheorem{aufgabe}[fakt]{Soal}"),
        (r"\newtheorem{Aufgabe}[fakt]{Aufgabe}", r"\newtheorem{Aufgabe}[fakt]{Soal}"),
        (r"\newtheorem{beispiel}[fakt]{Beispiel}", r"\newtheorem{beispiel}[fakt]{Contoh}"),
        (r"\newtheorem{Beispiel}[fakt]{Beispiel}", r"\newtheorem{Beispiel}[fakt]{Contoh}"),
        (r"\newtheorem{bemerkung}[fakt]{Bemerkung}", r"\newtheorem{bemerkung}[fakt]{Catatan}"),
        (r"\newtheorem{Bemerkung}[fakt]{Bemerkung}", r"\newtheorem{Bemerkung}[fakt]{Catatan}"),
        (r"\newtheorem{definition}[fakt]{Definition}", r"\newtheorem{definition}[fakt]{Definisi}"),
        (r"\newtheorem{Definition}[fakt]{Definition}", r"\newtheorem{Definition}[fakt]{Definisi}"),
        (r"\newtheorem{Lemma}[fakt]{Lemma}", r"\newtheorem{Lemma}[fakt]{Lema}"),
        (
            r"\newcommand{\punkte}[1]{\ifthenelse {\equal {#1}{}}{} {\ifthenelse {\equal {#1}{1}} {(1 Punkt)} {(#1 Punkte)}}}",
            r"\newcommand{\punkte}[1]{\ifthenelse {\equal {#1}{}}{} {\ifthenelse {\equal {#1}{1}} {(1 poin)} {(#1 poin)}}}",
        ),
        (
            r"{\addcontentsline{lof}{figure}{Quelle = #1, Autor = Benutzer #3 auf #4, Lizenz = #5 \bildlizenzskip  }}",
            r"{\addcontentsline{lof}{figure}{Sumber = #1, Kreator = Pengguna #3 di #4, Lisensi = #5 \bildlizenzskip  }}",
        ),
        (
            r"{ \addcontentsline{lof}{figure}{ Quelle = #1, Autor = #2, Lizenz = #5 \bildlizenzskip }}",
            r"{ \addcontentsline{lof}{figure}{ Sumber = #1, Kreator = #2, Lisensi = #5 \bildlizenzskip }}",
        ),
        (
            r"{ \addcontentsline{lof}{figure}{ Quelle = #1, Autor = #2 (hochgeladen von Benutzer #3 auf #4), Lizenz = #5 \bildlizenzskip }} } }",
            r"{ \addcontentsline{lof}{figure}{ Sumber = #1, Kreator = #2 (diunggah oleh Pengguna #3 di #4), Lisensi = #5 \bildlizenzskip }} } }",
        ),
        (r"\setlength{\oddsidemargin}{1.5cm}", "% page geometry supplied by reader wrapper"),
        (r"\setlength{\evensidemargin}{1.5cm}", "% page geometry supplied by reader wrapper"),
        (r"\setlength{\textwidth}{13.7cm}", "% page geometry supplied by reader wrapper"),
        (r"\setlength{\textheight}{22cm}", "% page geometry supplied by reader wrapper"),
        (r"\setlength{\topmargin}{1cm}", "% page geometry supplied by reader wrapper"),
        (r"\setlength{\footskip}{1cm}", "% page geometry supplied by reader wrapper"),
    ]
    for old, new in replacements:
        text = replace_once(text, old, new)

    category_count = len(CATEGORY_RE.findall(text))
    text = CATEGORY_RE.sub("\n", text)
    text = text.rstrip() + PORTABLE_APPENDIX

    output_bytes = text.encode("utf-8")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(output_bytes)
    receipt = {
        "schema_version": 1,
        "input": relative_path(args.input, args.project_root),
        "input_bytes": len(source_bytes),
        "input_sha256": sha256(source_bytes),
        "output": relative_path(args.output, args.project_root),
        "output_bytes": len(output_bytes),
        "output_sha256": sha256(output_bytes),
        "replacement_count": len(replacements),
        "removed_category_links": category_count,
        "portable_appendix": ["Teorema environment sharing fakt counter", "Indonesian proof label"],
        "scope": "language/input ownership, local media paths, current text-license notice, Indonesian reader labels, wrapper-owned centered A4 page geometry",
    }
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


if __name__ == "__main__":
    main()
