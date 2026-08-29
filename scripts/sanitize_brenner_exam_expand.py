#!/usr/bin/env python3
"""Sanitize a frozen Brenner exam expansion without weakening the core policy.

The exam solution views contain a small amount of MediaWiki-generated ``em``
markup used only for italic presentation.  The ordinary Brenner sanitizer
rightly rejects every residual HTML tag.  This exam-only profile applies the
same transformations, permits only balanced, non-nested, attribute-free
``<em>...</em>`` pairs, removes just those tags, and then enforces the same
zero-residual-HTML and zero-replacement-character checks.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
from pathlib import Path

import sanitize_brenner_expand as generic


PROFILE = "brenner-exam-presentational-em-v1"
ALLOWED_OPEN = "<em>"
ALLOWED_CLOSE = "</em>"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def relative_path(path: Path, project_root: Path) -> str:
    return path.resolve().relative_to(project_root.resolve()).as_posix()


def sanitize(raw: str) -> tuple[str, dict[str, object]]:
    text = raw.replace("\r\n", "\n").replace("\r", "\n")
    text = generic.BREAK_RE.sub("\n", text)
    text = generic.WRAPPER_RE.sub("", text)
    text = html.unescape(text)

    residual_tags = [match.group(0) for match in generic.HTML_TAG_RE.finditer(text)]
    depth = 0
    open_count = 0
    close_count = 0
    for tag in residual_tags:
        normalized = tag.casefold()
        if normalized == ALLOWED_OPEN:
            if depth:
                raise RuntimeError("nested em markup is outside the exam sanitation policy")
            depth = 1
            open_count += 1
        elif normalized == ALLOWED_CLOSE:
            if depth != 1:
                raise RuntimeError("unbalanced closing em tag in exam expansion")
            depth = 0
            close_count += 1
        else:
            raise RuntimeError(
                f"unexpected HTML tag outside the exam sanitation policy: {tag!r}"
            )
    if depth or open_count != close_count:
        raise RuntimeError("unbalanced em markup in exam expansion")

    before_unwrap = text.encode("utf-8")
    # The inventory above proves every matched tag has exact, attribute-free
    # ``em`` syntax.  Replace the inventoried syntax only; inner text is left
    # byte-for-byte intact at this stage.
    text = generic.HTML_TAG_RE.sub("", text)
    after_unwrap = text.encode("utf-8")
    text = "\n".join(line.rstrip() for line in text.split("\n"))
    text = generic.BLANKS_RE.sub("\n\n", text).strip() + "\n"
    if generic.HTML_TAG_RE.search(text):
        raise RuntimeError("unexpected HTML tag remains after exam sanitation")
    if "\ufffd" in text:
        raise RuntimeError("replacement character in sanitized exam text")

    evidence: dict[str, object] = {
        "profile": PROFILE,
        "allowed_presentational_syntax": [ALLOWED_OPEN, ALLOWED_CLOSE],
        "residual_html_tags_before_unwrap": len(residual_tags),
        "em_open_tags_removed": open_count,
        "em_close_tags_removed": close_count,
        "pre_unwrap_utf8_sha256": sha256(before_unwrap),
        "post_unwrap_utf8_sha256": sha256(after_unwrap),
        "removed_utf8_bytes": len(before_unwrap) - len(after_unwrap),
        "balanced_non_nested_pairs": True,
    }
    return text, evidence


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

    sanitized, evidence = sanitize(expanded)
    output_bytes = sanitized.encode("utf-8")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(output_bytes)

    receipt = {
        "schema_version": 1,
        "sanitizer_profile": PROFILE,
        "input": relative_path(args.input, args.project_root),
        "input_bytes": len(source_bytes),
        "input_sha256": sha256(source_bytes),
        "expanded_chars": len(expanded),
        "output": relative_path(args.output, args.project_root),
        "output_bytes": len(output_bytes),
        "output_sha256": sha256(output_bytes),
        "presentational_html_evidence": evidence,
        "transform": [
            "normalize CRLF/CR to LF",
            "replace br tags with LF",
            "remove div/pre/nowiki wrapper tags",
            "decode HTML entities",
            "inventory and require only balanced non-nested attribute-free em pairs",
            "remove only the em opening and closing tags while preserving inner text",
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
