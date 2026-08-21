#!/usr/bin/env python3
"""Convert a frozen MediaWiki expandtemplates JSON response to stable UTF-8 TeX.

This is intentionally an offline transform. It never fetches mutable wiki state.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
from pathlib import Path


BREAK_RE = re.compile(r"</?br\s*/?>", re.IGNORECASE)
WRAPPER_RE = re.compile(
    r"</?(?:div|pre|nowiki)(?:\s+[^>]*)?>", re.IGNORECASE
)
BLANKS_RE = re.compile(r"\n[ \t]*\n(?:[ \t]*\n)+")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def relative_path(path: Path, project_root: Path) -> str:
    return path.resolve().relative_to(project_root.resolve()).as_posix()


def sanitize(raw: str) -> str:
    text = raw.replace("\r\n", "\n").replace("\r", "\n")
    text = BREAK_RE.sub("\n", text)
    text = WRAPPER_RE.sub("", text)
    text = html.unescape(text)
    text = "\n".join(line.rstrip() for line in text.split("\n"))
    text = BLANKS_RE.sub("\n\n", text).strip() + "\n"
    if re.search(r"</?[A-Za-z][^>]*>", text):
        raise RuntimeError("unexpected HTML tag remains after sanitation")
    if "\ufffd" in text:
        raise RuntimeError("replacement character in sanitized text")
    return text


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()

    source_bytes = args.input.read_bytes()
    payload = json.loads(source_bytes.decode("utf-8"))
    try:
        expanded = payload["expandtemplates"]["wikitext"]
    except (KeyError, TypeError) as exc:
        raise RuntimeError("missing expandtemplates.wikitext") from exc
    if not isinstance(expanded, str):
        raise RuntimeError("expandtemplates.wikitext is not a string")

    output_bytes = sanitize(expanded).encode("utf-8")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(output_bytes)

    receipt = {
        "schema_version": 1,
        "input": relative_path(args.input, args.project_root),
        "input_bytes": len(source_bytes),
        "input_sha256": sha256(source_bytes),
        "expanded_chars": len(expanded),
        "output": relative_path(args.output, args.project_root),
        "output_bytes": len(output_bytes),
        "output_sha256": sha256(output_bytes),
        "transform": [
            "normalize CRLF/CR to LF",
            "replace br tags with LF",
            "remove div/pre/nowiki wrapper tags",
            "decode HTML entities",
            "strip trailing horizontal whitespace",
            "collapse runs of blank lines",
            "require no residual HTML tag or U+FFFD",
        ],
    }
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


if __name__ == "__main__":
    main()
