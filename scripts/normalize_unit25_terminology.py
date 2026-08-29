#!/usr/bin/env python3
"""Apply the reviewed Unit 25 terminology normalization to the lecture."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "source/units/unit-25/lecture25.id.tex"

REPLACEMENTS = (
    ("fungsi-fungsi terdiferensiasi kontinu", "fungsi-fungsi yang terdiferensialkan secara kontinu"),
    ("penampang terdiferensiasi kontinu", "penampang yang terdiferensialkan secara kontinu"),
    ("bundel vektor terdiferensiasi", "bundel vektor diferensiabel"),
    ("manifold terdiferensiasi", "manifold diferensiabel"),
    ("penampang terdiferensiasi", "penampang diferensiabel"),
    ("fungsi terdiferensiasi", "fungsi diferensiabel"),
    ("peta terdiferensiasi", "pemetaan diferensiabel"),
    (
        "dengan suatu ruang vektor $\\R$ bernama $W$",
        "dengan suatu ruang vektor-$\\R$ yang dinotasikan $W$",
    ),
    ("berkas konstan-lokal", "berkas lokal konstan"),
)


def main() -> None:
    text = PATH.read_text(encoding="utf-8")
    for source, target in REPLACEMENTS:
        if source not in text:
            raise RuntimeError(f"expected Unit 25 wording not found: {source!r}")
        text = text.replace(source, target)
    PATH.write_text(text, encoding="utf-8", newline="\n")
    print(PATH.relative_to(ROOT), PATH.stat().st_size)


if __name__ == "__main__":
    main()
