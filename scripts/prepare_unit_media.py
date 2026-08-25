#!/usr/bin/env python3
"""Verify one unit's Commons sources and create deterministic TeX derivatives."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import subprocess
from pathlib import Path


def digest(path: Path, algorithm: str) -> str:
    hasher = hashlib.new(algorithm)
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def run_checked(command: list[str]) -> str:
    completed = subprocess.run(
        command,
        check=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    return completed.stdout.strip()


def relative_path(path: Path, project_root: Path) -> str:
    return path.resolve().relative_to(project_root.resolve()).as_posix()


def tex_escape(value: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(character, character) for character in value)


def tex_breakable_filename(value: str) -> str:
    """Escape a display filename while permitting line breaks at spaces."""
    return " ".join(rf"\texttt{{{tex_escape(part)}}}" for part in value.split(" "))


def write_attribution_tex(
    rows: list[dict[str, object]],
    destination: Path,
    unit_number: int,
    heading_level: str,
) -> None:
    count_word = {
        1: "Satu",
        2: "Dua",
        3: "Tiga",
        4: "Empat",
        5: "Lima",
        6: "Enam",
    }.get(len(rows), str(len(rows)))
    rights_sentence = (
        "mengikuti lisensinya sendiri; tautan sumber dan lisensi dapat diklik."
        if unit_number == 1
        else (
            "mengikuti status hak atau lisensinya sendiri; tautan sumber dapat "
            "diklik dan tautan lisensi dicantumkan jika tersedia."
        )
    )
    if heading_level == "chapter":
        heading = r"\chapter*{Atribusi dan Hak Media}"
        toc = r"\addcontentsline{toc}{chapter}{Atribusi dan Hak Media}"
    else:
        heading = rf"\section*{{Unit {unit_number}}}"
        toc = rf"\addcontentsline{{toc}}{{section}}{{Unit {unit_number}}}"
    if not rows:
        lines = [
            heading,
            toc,
            (
                f"Unit {unit_number} tidak menggunakan berkas media. "
                "Penutupan nol-aset ini diverifikasi terhadap kuliah, lembar kerja, "
                "dan semua solusi yang disediakan oleh sumber."
            ),
            "",
        ]
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text("\n".join(lines), encoding="utf-8", newline="\n")
        return
    lines = [
        heading,
        toc,
        (
            f"{count_word} berkas berikut digunakan dalam Unit {unit_number}. "
            f"Setiap berkas tetap {rights_sentence}"
        ),
        r"\begin{description}",
    ]
    for row in rows:
        filename = str(row["filename"])
        license_name = str(row["rights_label_id"])
        source_link = (
            rf"\href{{{row['commons_description_url']}}}"
            r"{Halaman sumber di Wikimedia Commons}"
        )
        if row["license_url"]:
            rights_text = (
                rf"lisensi \href{{{row['license_url']}}}"
                rf"{{{tex_escape(license_name)}}}"
            )
        else:
            rights_text = rf"status hak: {tex_escape(license_name)}"
        lines.extend(
            [
                rf"\item[]{tex_breakable_filename(filename)}",
                tex_escape(str(row.get("attribution_id_tex") or row["attribution_id"])),
                f"{source_link}; {rights_text}.",
            ]
        )
    lines.extend(
        [
            r"\end{description}",
            (
                "Identitas revisi, ukuran, SHA-1 Wikimedia, SHA-256, URL berkas asli, "
                "dan hash turunan cetak tercatat dalam manifest media yang disertakan."
            ),
            "",
        ]
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--attribution-tex", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--media-config", type=Path, required=True)
    parser.add_argument("--unit-number", type=int, required=True)
    parser.add_argument(
        "--heading-level", choices=("chapter", "section"), default="chapter"
    )
    args = parser.parse_args()

    config = json.loads(args.media_config.read_text(encoding="utf-8"))
    try:
        unit_config = config["units"][str(args.unit_number)]
        media_config = unit_config["media"]
    except (KeyError, TypeError) as exc:
        raise RuntimeError(
            f"missing Unit {args.unit_number} media configuration"
        ) from exc
    if not isinstance(media_config, list):
        raise RuntimeError("unit media configuration must be a list")

    with args.manifest.open(encoding="utf-8", newline="") as stream:
        by_title = {row["title"]: row for row in csv.DictReader(stream)}

    magick = shutil.which("magick") if media_config else None
    if media_config and not magick:
        raise RuntimeError("ImageMagick 'magick' executable not found")
    version = (
        run_checked([magick, "-version"]).splitlines()[0]
        if magick
        else "not required (verified zero-asset unit)"
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, object]] = []
    for media_item in media_config:
        filename = media_item["filename"]
        title = f"File:{filename}"
        if title not in by_title:
            raise RuntimeError(f"missing rights-manifest row: {title}")
        metadata = by_title[title]
        source = args.source_dir / filename
        if not source.is_file():
            raise RuntimeError(f"missing canonical binary: {source}")
        source_bytes = source.stat().st_size
        source_sha1 = digest(source, "sha1")
        source_sha256 = digest(source, "sha256")
        if source_bytes != int(metadata["bytes"]):
            raise RuntimeError(f"byte-count mismatch for {filename}")
        if source_sha1 != metadata["commons_sha1_hex"].lower():
            raise RuntimeError(f"Commons SHA-1 mismatch for {filename}")

        derivative: dict[str, object] | None = None
        if source.suffix.lower() in {".svg", ".gif"}:
            print_basename = media_item.get("print_basename", source.stem)
            output = args.output_dir / f"{print_basename}.png"
            # Fixed density, bounding box, colour treatment, and metadata stripping make
            # this a stable print fallback while preserving the canonical SVG or GIF.
            # Animated GIFs use frame zero only; the canonical animation remains the
            # HTML/download surface and the derivative is explicitly recorded below.
            source_argument = (
                f"{source}[0]" if source.suffix.lower() == ".gif" else str(source)
            )
            command = [magick, "-background", "white"]
            if source.suffix.lower() == ".svg":
                command.extend(["-density", "300"])
            command.extend(
                [
                    source_argument,
                    "-alpha",
                    "remove",
                    "-alpha",
                    "off",
                ]
            )
            if media_item.get("trim_whitespace", False):
                # Some legacy Commons SVGs carry a malformed/oversized viewport.
                # Crop only the deterministic print derivative, retaining a small
                # white quiet zone; the canonical SVG bytes remain untouched.
                command.extend(
                    [
                        "-fuzz",
                        "1%",
                        "-trim",
                        "+repage",
                        "-bordercolor",
                        "white",
                        "-border",
                        "12x12",
                    ]
                )
            command.extend(
                [
                    "-resize",
                    "1800x1800>",
                    "-strip",
                    "-define",
                    "png:exclude-chunk=date,time",
                    f"PNG24:{output}",
                ]
            )
            run_checked(command)
            identify = run_checked(
                [magick, "identify", "-format", "%m %w %h %[colorspace]", str(output)]
            )
            derivative = {
                "path": relative_path(output, args.project_root),
                "bytes": output.stat().st_size,
                "sha256": digest(output, "sha256"),
                "identify": identify,
                "source_kind": source.suffix.lower().lstrip("."),
                "frame_index": 0 if source.suffix.lower() == ".gif" else None,
                "command": [
                    "magick" if part == magick else relative_path(output, args.project_root)
                    if part == f"PNG24:{output}"
                    else relative_path(source, args.project_root) + "[0]"
                    if part == f"{source}[0]"
                    else relative_path(source, args.project_root)
                    if part == str(source)
                    else part
                    for part in command
                ],
            }

        source_license_url = metadata["license_url"]
        reader_license_url = media_item.get("license_url_id", source_license_url)
        row: dict[str, object] = {
                "filename": filename,
                "canonical_path": relative_path(source, args.project_root),
                "canonical_bytes": source_bytes,
                "canonical_sha1": source_sha1,
                "canonical_sha256": source_sha256,
                "commons_description_url": metadata["description_url"],
                "commons_original_url": metadata["original_url"],
                "license": metadata["license"],
                "rights_label_id": media_item.get(
                    "rights_label_id", metadata["license"]
                ),
                "license_url": reader_license_url,
                "artist_html": metadata["artist_html"],
                "credit_html": metadata["credit_html"],
                "attribution_required": metadata["attribution_required"],
                "attribution_id": media_item["attribution_id"],
                "derivative": derivative,
            }
        if media_item.get("attribution_id_tex"):
            row["attribution_id_tex"] = media_item["attribution_id_tex"]
        if reader_license_url != source_license_url:
            row["source_license_url"] = source_license_url
        rows.append(row)

    write_attribution_tex(
        rows, args.attribution_tex, args.unit_number, args.heading_level
    )

    receipt = {
        "schema_version": 1,
        "scope": (
            f"O011 Brenner Unit {args.unit_number} exact media closure "
            "and TeX print derivatives"
        ),
        "unit_number": args.unit_number,
        "heading_level": args.heading_level,
        "media_config": relative_path(args.media_config, args.project_root),
        "media_config_sha256": digest(args.media_config, "sha256"),
        "manifest": relative_path(args.manifest, args.project_root),
        "manifest_sha256": digest(args.manifest, "sha256"),
        "image_engine": version,
        "source_count": len(rows),
        "derivative_count": sum(row["derivative"] is not None for row in rows),
        "attribution_tex": {
            "path": relative_path(args.attribution_tex, args.project_root),
            "bytes": args.attribution_tex.stat().st_size,
            "sha256": digest(args.attribution_tex, "sha256"),
        },
        "media": rows,
    }
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


if __name__ == "__main__":
    main()
