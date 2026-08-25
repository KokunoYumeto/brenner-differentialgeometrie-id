#!/usr/bin/env python3
"""Prepare a translated semantic TeX fragment for compilation without mutation."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


CATEGORY_RE = re.compile(r"\s*\[\[Kategori(?:e|):[^\]]+\]\]\s*", re.IGNORECASE)
WIKILINK_RE = re.compile(r"\[\[([^\[\]|]+)(?:\|([^\[\]]+))?\]\]")
# MediaWiki animation links are a reader surface, not ordinary prose links.
# Preserve them as clickable Commons links before the generic wiki-link pass
# strips the source target.  The pattern is intentionally limited to the two
# file namespaces and GIF assets; ordinary internal links retain the existing
# label-only behavior.
INTERACTIVE_GIF_WIKILINK_RE = re.compile(
    r"\[\[(?:Datei|File):([^\[\]|]+\.gif)(?:\|([^\[\]]*))?\]\]",
    re.IGNORECASE,
)
IMAGE_LOADER_RE = re.compile(
    r"(\\bildeinlesung(?:png|PNG|jpg|JPG|jpeg|svg|gif|GIF|xcf)?\s*\{)"
    r"\s*([^{}]*?)\s*(\})"
)

LAYOUT_REFLOWS = {
    "O011-LAYOUT-U04-HYPERBOLOID-BASIS-ACTION": [
        (
            r"\mavergleichskettedisphandlinks",
            r"\mavergleichskettealigndrucklinks",
        ),
        (
            r"\vergleichskettedisphandlinks",
            r"\vergleichskettealigndrucklinks",
        ),
    ],
    "O011-LAYOUT-U04-HYPERBOLOID-EIGENVECTOR": [
        (
            r"\mavergleichskettealignhandlinks",
            r"\mavergleichskettealigndrucklinks",
        ),
        (
            r"\vergleichskettealignhandlinks",
            r"\vergleichskettealigndrucklinks",
        ),
    ],
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def relative_path(path: Path, project_root: Path) -> str:
    return path.resolve().relative_to(project_root.resolve()).as_posix()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()

    source_bytes = args.input.read_bytes()
    text = source_bytes.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
    category_count = len(CATEGORY_RE.findall(text))
    text = CATEGORY_RE.sub("\n", text)
    noedit_count = text.count("__NOEDITSECTION__")
    text = text.replace("__NOEDITSECTION__", "")
    links: list[dict[str, str]] = []
    interactive_links: list[dict[str, str]] = []

    def replace_interactive_gif(match: re.Match[str]) -> str:
        filename = match.group(1).strip()
        fields = [field.strip() for field in (match.group(2) or "").split("|") if field.strip()]
        # MediaWiki's thumb marker is presentation metadata; the final field
        # is the human-readable caption/accessible label.
        caption = next((field for field in fields if field.lower() != "thumb"), filename)
        url = "https://commons.wikimedia.org/wiki/File:" + filename.replace(" ", "_")
        interactive_links.append({"filename": filename, "label": caption, "url": url})
        return r"\href{" + url + "}{" + caption + "}"

    text = INTERACTIVE_GIF_WIKILINK_RE.sub(replace_interactive_gif, text)

    def replace_link(match: re.Match[str]) -> str:
        target = match.group(1).strip()
        label = (match.group(2) or target).strip()
        links.append({"target": target, "label": label})
        return label

    text = WIKILINK_RE.sub(replace_link, text)
    if "[[" in text or "]]" in text:
        raise RuntimeError("unresolved wiki-link delimiter")

    operator_localizations = {
        "operatorname_kern_to_ker": text.count(r"\operatorname{kern}"),
        "operatorname_bild_to_im": text.count(r"\operatorname{bild}"),
    }
    text = text.replace(r"\operatorname{kern}", r"\ker")
    text = text.replace(r"\operatorname{bild}", r"\operatorname{im}")

    layout_reflows: list[dict[str, str]] = []
    for layout_id, replacements in LAYOUT_REFLOWS.items():
        begin_marker = f"% {layout_id}-BEGIN"
        end_marker = f"% {layout_id}-END"
        begin_count = text.count(begin_marker)
        end_count = text.count(end_marker)
        if begin_count != end_count:
            raise RuntimeError(f"unpaired layout marker: {layout_id}")
        if begin_count > 1:
            raise RuntimeError(f"layout marker occurs more than once: {layout_id}")
        if begin_count == 1:
            before, marked = text.split(begin_marker, 1)
            segment, after = marked.split(end_marker, 1)
            applied: list[dict[str, str]] = []
            for old, new in replacements:
                if segment.count(old) != 1:
                    raise RuntimeError(
                        f"layout reflow expected one {old} in {layout_id}"
                    )
                segment = segment.replace(old, new, 1)
                applied.append({"source_command": old, "target_command": new})
            text = before + segment + after
            layout_reflows.append(
                {"layout_id": layout_id, "command_replacements": applied}
            )

    trimmed_media_arguments = 0

    def trim_media_argument(match: re.Match[str]) -> str:
        nonlocal trimmed_media_arguments
        original = match.group(2)
        trimmed = original.strip()
        if original != trimmed:
            trimmed_media_arguments += 1
        return f"{match.group(1)}{trimmed}{match.group(3)}"

    text = IMAGE_LOADER_RE.sub(trim_media_argument, text)
    text = "\n".join(line.rstrip() for line in text.split("\n")).strip() + "\n"
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
        "removed_category_links": category_count,
        "removed_noedit_markers": noedit_count,
        "trimmed_media_arguments": trimmed_media_arguments,
        "localized_math_operators": operator_localizations,
        "layout_reflows": layout_reflows,
        "rendered_internal_links": links,
        "rendered_interactive_gif_links": interactive_links,
    }
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


if __name__ == "__main__":
    main()
