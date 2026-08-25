#!/usr/bin/env python3
"""Bounded structural verification for the Unit 12 static-first GIF surface.

This verifier renders only the two figure fragments needed for the regression
contract.  It does not invoke the cumulative reader build.
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import unquote

from export_html_v10 import (
    ANIMATED_MEDIA_CSS,
    ANIMATED_MEDIA_JS,
    CSS,
    README_TEXT,
    Renderer,
    SurfaceState,
    canonical_json,
    command_at,
    file_binding,
    load_json_object,
    load_media_rights,
    read_args,
    reader_css,
    reader_head_extension,
    reader_readme,
    stage_media_assets,
    write_text,
)


class FigureFragmentParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[str] = []
        self.errors: list[str] = []
        self.ids: list[str] = []
        self.images: list[dict[str, str]] = []
        self.buttons: list[dict[str, Any]] = []
        self.links: list[dict[str, Any]] = []
        self.statuses: list[dict[str, Any]] = []
        self.captions: list[str] = []
        self._active_button: dict[str, Any] | None = None
        self._active_link: dict[str, Any] | None = None
        self._active_status: dict[str, Any] | None = None
        self._caption_parts: list[str] | None = None

    @staticmethod
    def attrs(values: list[tuple[str, str | None]]) -> dict[str, str]:
        return {str(key): str(value or "") for key, value in values}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = self.attrs(attrs)
        if "id" in values:
            self.ids.append(values["id"])
        if tag == "img":
            self.images.append(values)
            return
        if tag == "button":
            self._active_button = {"attrs": values, "text": []}
            self.buttons.append(self._active_button)
        elif tag == "a":
            self._active_link = {"attrs": values, "text": []}
            self.links.append(self._active_link)
        elif tag == "span" and values.get("role") == "status":
            self._active_status = {"attrs": values, "text": []}
            self.statuses.append(self._active_status)
        elif tag == "figcaption":
            self._caption_parts = []
        self.stack.append(tag)

    def handle_endtag(self, tag: str) -> None:
        if not self.stack or self.stack[-1] != tag:
            self.errors.append(f"misnested closing tag: {tag}")
            return
        self.stack.pop()
        if tag == "button":
            self._active_button = None
        elif tag == "a":
            self._active_link = None
        elif tag == "span" and self._active_status is not None:
            self._active_status = None
        elif tag == "figcaption" and self._caption_parts is not None:
            self.captions.append(" ".join("".join(self._caption_parts).split()))
            self._caption_parts = None

    def handle_data(self, data: str) -> None:
        if self._active_button is not None:
            self._active_button["text"].append(data)
        if self._active_link is not None:
            self._active_link["text"].append(data)
        if self._active_status is not None:
            self._active_status["text"].append(data)
        if self._caption_parts is not None:
            self._caption_parts.append(data)

    def close(self) -> None:
        super().close()
        if self.stack:
            self.errors.append("unclosed fragment tags: " + ", ".join(self.stack))
        for collection in (self.buttons, self.links, self.statuses):
            for item in collection:
                item["text"] = " ".join("".join(item["text"]).split())


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def figure_body(path: Path, marker: str) -> str:
    text = path.read_text(encoding="utf-8")
    marker_pos = text.find(marker)
    if marker_pos < 0:
        raise RuntimeError(f"fixture marker is absent from {path}: {marker}")
    figure_pos = text.rfind(r"\bild{", 0, marker_pos)
    if figure_pos < 0:
        raise RuntimeError(f"fixture marker is not enclosed by \\bild: {marker}")
    name, after = command_at(text, figure_pos) or ("", figure_pos)
    if name != "bild":
        raise RuntimeError(f"fixture did not resolve to \\bild: {marker}")
    args, _ = read_args(text, after, 1)
    return args[0]


def figure_fragment(document: str, figure_id: str) -> str:
    start = document.find(f'<figure id="{figure_id}"')
    if start < 0:
        raise RuntimeError(f"baseline reader has no figure {figure_id}")
    end = document.find("</figure>", start)
    if end < 0:
        raise RuntimeError(f"baseline reader figure is unclosed: {figure_id}")
    return document[start:end + len("</figure>")]


def verify(root: Path) -> dict[str, Any]:
    root = root.resolve()
    errors: list[str] = []
    rights = load_media_rights(root)

    animated_source = root / "source/units/unit-12/lecture12.id.tex"
    animated_body = figure_body(animated_source, "Fiddler_crab_mobius_strip")
    animated_renderer = Renderer(root, rights)
    animated_fragment = animated_renderer._figure(
        animated_body,
        SurfaceState(12, "lecture", "o011-brenner-u12-l12"),
    )
    parser = FigureFragmentParser()
    parser.feed(animated_fragment)
    parser.close()
    errors.extend(parser.errors)

    require(animated_renderer.has_animated_media, "GIF did not activate the animated-media path", errors)
    require('data-animation-state="stopped"' in animated_fragment, "default animation state is not stopped", errors)
    require(len(parser.images) == 1, "animated figure does not have exactly one image", errors)
    image = parser.images[0] if parser.images else {}
    require(image.get("src") == "assets/media/Fiddler_crab_mobius_strip.png", "initial image is not the verified static frame", errors)
    require(image.get("data-static-src") == image.get("src"), "static source does not match initial image", errors)
    require(unquote(image.get("data-animated-src", "")) == "assets/media/Fiddler crab mobius strip.gif", "Play source is not the canonical GIF", errors)
    require(bool(image.get("alt", "").strip()), "animated image has no alternative text", errors)
    require(image.get("aria-describedby", "") in parser.ids, "animated image description target is unresolved", errors)
    require('<div class="animated-media-controls" role="group" aria-label="Kontrol animasi">' in animated_fragment, "Play/Stop controls have no labelled group", errors)
    require("onclick=" not in animated_fragment and "onkeydown=" not in animated_fragment, "animated figure uses prohibited inline event handlers", errors)

    buttons = {item["attrs"].get("data-animation-action"): item for item in parser.buttons}
    require(set(buttons) == {"play", "stop"}, "native Play/Stop buttons are not both present", errors)
    for action, label in (("play", "Putar animasi"), ("stop", "Hentikan animasi")):
        button = buttons.get(action, {"attrs": {}, "text": ""})
        require(button["attrs"].get("type") == "button", f"{action} control is not a native button", errors)
        require(button["attrs"].get("aria-controls") == image.get("id"), f"{action} control does not target the image", errors)
        require(button["text"] == label, f"{action} control has the wrong Indonesian label", errors)
        require("tabindex" not in button["attrs"], f"{action} control overrides native keyboard focus", errors)
    require("disabled" not in buttons.get("play", {}).get("attrs", {}), "Play is not initially keyboard-operable", errors)
    require("disabled" in buttons.get("stop", {}).get("attrs", {}), "Stop is not initially disabled for the static state", errors)

    downloads = [item for item in parser.links if "animated-media-download" in item["attrs"].get("class", "").split()]
    require(len(downloads) == 1, "canonical GIF download link is absent or duplicated", errors)
    download = downloads[0] if downloads else {"attrs": {}, "text": ""}
    require(unquote(download["attrs"].get("href", "")) == "assets/media/Fiddler crab mobius strip.gif", "download link does not target the canonical GIF", errors)
    require(download["attrs"].get("download") == "Fiddler crab mobius strip.gif", "download filename differs from the canonical GIF", errors)
    require(download["text"] == "Unduh GIF asli", "download link has the wrong Indonesian label", errors)

    description = (
        "Animasi seekor kepiting biola yang mengelilingi pita Möbius dan kembali "
        "dengan orientasi tercermin. Edisi PDF menampilkan bingkai pertama yang "
        "statis; animasi asli dipertahankan untuk edisi HTML dan unduhan."
    )
    require(any(description in caption for caption in parser.captions), "meaningful Indonesian animation caption is not visible", errors)
    require(len(parser.statuses) == 1, "polite animation status is absent or duplicated", errors)
    if parser.statuses:
        require(parser.statuses[0]["attrs"].get("aria-live") == "polite", "animation status is not polite", errors)
        require("bingkai statis" in parser.statuses[0]["text"], "initial status does not disclose the static frame", errors)

    require('matchMedia("(prefers-reduced-motion: reduce)")' in ANIMATED_MEDIA_JS, "controller does not query reduced-motion preference", errors)
    require("image.src=playing?image.dataset.animatedSrc:image.dataset.staticSrc" in ANIMATED_MEDIA_JS, "controller does not swap between canonical GIF and static frame", errors)
    require("play.disabled=playing;stop.disabled=!playing" in ANIMATED_MEDIA_JS, "controller does not expose mutually valid Play/Stop states", errors)
    require("if(preference.matches){stop" in ANIMATED_MEDIA_JS, "controller does not prevent Play under reduced motion", errors)
    require('preference.addEventListener("change",honorPreference)' in ANIMATED_MEDIA_JS, "controller does not respond to preference changes", errors)
    require("prefers-reduced-motion:reduce" in ANIMATED_MEDIA_CSS, "animated controls have no reduced-motion CSS surface", errors)
    require("animated-media-controller" in reader_head_extension(animated_renderer), "animated controller is not admitted into an animated reader head", errors)
    require(ANIMATED_MEDIA_CSS in reader_css(animated_renderer), "animated control styles are not admitted into an animated reader", errors)

    second_renderer = Renderer(root, rights)
    second_fragment = second_renderer._figure(
        animated_body,
        SurfaceState(12, "lecture", "o011-brenner-u12-l12"),
    )
    require(second_fragment == animated_fragment, "two Unit 12 fragment renders differ", errors)
    require(canonical_json(second_renderer.media_used) == canonical_json(animated_renderer.media_used), "two animated media manifests differ", errors)

    with tempfile.TemporaryDirectory(prefix="o011-html-animation-test-") as first_tmp, tempfile.TemporaryDirectory(prefix="o011-html-animation-test-") as second_tmp:
        first_stage = Path(first_tmp)
        second_stage = Path(second_tmp)
        first_manifest = stage_media_assets(root, first_stage, animated_renderer)
        second_manifest = stage_media_assets(root, second_stage, second_renderer)
        require(canonical_json(first_manifest) == canonical_json(second_manifest), "two staged animated media manifests differ", errors)
        for name, expected_sha in (
            ("Fiddler crab mobius strip.gif", "059c8643c42a0561e5ee5efe52cd5fc59de0879ddd3870fa200f4ae66a2fc69a"),
            ("Fiddler_crab_mobius_strip.png", "15f45aee985375fe99b19f30dc62268d286db4caf103cf4fc066a8951cc43790"),
        ):
            first = first_stage / "assets/media" / name
            second = second_stage / "assets/media" / name
            require(first.is_file() and second.is_file(), f"staged media is missing: {name}", errors)
            if first.is_file() and second.is_file():
                first_binding = file_binding(first, first_stage)
                second_binding = file_binding(second, second_stage)
                require(first_binding == second_binding, f"two staged copies differ: {name}", errors)
                require(first_binding["sha256"] == expected_sha, f"staged bytes differ from admitted hash: {name}", errors)

    static_source = root / "source/units/unit-10/lecture10.id.tex"
    static_body = figure_body(static_source, "Tangent_bundle")
    static_renderer = Renderer(root, rights)
    static_fragment = static_renderer._figure(
        static_body,
        SurfaceState(10, "lecture", "o011-brenner-u10-l10"),
    )
    baseline_entry = root / "output/html/unit-10/index.html"
    baseline_css = root / "output/html/unit-10/assets/reader.css"
    baseline_readme = root / "output/html/unit-10/README.txt"
    baseline_manifest = root / "output/html/unit-10/manifest.json"
    for path in (baseline_entry, baseline_css, baseline_readme, baseline_manifest):
        require(path.is_file(), f"established Unit 10 baseline is missing: {path.relative_to(root)}", errors)
    if baseline_entry.is_file():
        expected_fragment = figure_fragment(
            baseline_entry.read_text(encoding="utf-8"),
            "o011-brenner-u10-l10-fig-001",
        )
        require(static_fragment == expected_fragment, "existing static figure HTML bytes changed", errors)
    require(not static_renderer.has_animated_media, "static figure activated animated-media behavior", errors)
    require(reader_head_extension(static_renderer) == "", "static reader would gain an extra controller script", errors)
    require(reader_css(static_renderer) == CSS, "static reader would gain animated CSS", errors)
    require(reader_readme(static_renderer) == README_TEXT, "static reader would gain animated README prose", errors)
    if baseline_css.is_file():
        require(reader_css(static_renderer).encode("utf-8") == baseline_css.read_bytes(), "base CSS bytes differ from the established Unit 10 output", errors)
    if baseline_readme.is_file():
        require(reader_readme(static_renderer).encode("utf-8") == baseline_readme.read_bytes(), "base README bytes differ from the established Unit 10 output", errors)
    if baseline_manifest.is_file():
        baseline_manifest_value = load_json_object(baseline_manifest)
        expected_static_media = [
            item for item in baseline_manifest_value.get("media", [])
            if isinstance(item, dict) and item.get("filename") == "Tangent bundle.svg"
        ]
        require(len(expected_static_media) == 1, "Unit 10 baseline has no unique Tangent bundle.svg manifest entry", errors)
        with tempfile.TemporaryDirectory(prefix="o011-html-static-test-") as static_tmp:
            static_stage = Path(static_tmp)
            actual_static_media = stage_media_assets(root, static_stage, static_renderer)
            if len(expected_static_media) == 1:
                require(actual_static_media == expected_static_media, "existing static media manifest schema or values changed", errors)
            staged_static = static_stage / "assets/media/Tangent bundle.svg"
            baseline_static = root / "output/html/unit-10/assets/media/Tangent bundle.svg"
            require(staged_static.is_file(), "static media staging omitted Tangent bundle.svg", errors)
            if staged_static.is_file() and baseline_static.is_file():
                require(staged_static.read_bytes() == baseline_static.read_bytes(), "staged static media bytes differ from the Unit 10 baseline", errors)

    if errors:
        raise RuntimeError("animated-media HTML verification failed:\n- " + "\n- ".join(dict.fromkeys(errors)))

    animation = animated_renderer.media_used["Fiddler crab mobius strip.gif"]["animation"]
    return {
        "schema_version": 1,
        "workflow": "o011-verify-html-animated-media-v1",
        "status": "pass",
        "scope": "Bounded Unit 12 static-first animated-media HTML fragment and unchanged static-media regression; no cumulative build",
        "checks": {
            "default_surface_is_verified_static_frame": True,
            "native_keyboard_play_stop_controls": True,
            "canonical_gif_used_for_play_and_download": True,
            "meaningful_indonesian_caption_and_live_status": True,
            "prefers_reduced_motion_prevents_and_stops_animation": True,
            "canonical_and_static_assets_staged_byte_identically": True,
            "two_fragment_renders_and_manifests_identical": True,
            "existing_static_figure_html_unchanged": True,
            "existing_static_asset_and_manifest_entry_unchanged": True,
            "existing_static_css_readme_and_head_extensions_unchanged": True,
            "cumulative_build_not_invoked": True,
        },
        "animated_figure": {
            "id": "o011-brenner-u12-l12-fig-001",
            "canonical": animation["canonical_source"],
            "static_frame": animation["static_source"],
            "static_frame_index": animation["static_frame_index"],
            "description": animation["description"],
        },
        "bindings": {
            "exporter": file_binding(root / "scripts/export_html_v10.py", root),
            "verifier": file_binding(Path(__file__).resolve(), root),
            "unit_media_config": file_binding(root / "source/unit_media.json", root),
            "unit_12_media_receipt": file_binding(root / "qa/unit-12_media.json", root),
            "unit_12_animation_qa": file_binding(root / "qa/unit-12/ANIMATED_MEDIA_QA.json", root),
            "unit_12_lecture": file_binding(animated_source, root),
            "unit_10_baseline_entry": file_binding(baseline_entry, root),
            "unit_10_baseline_css": file_binding(baseline_css, root),
            "unit_10_baseline_readme": file_binding(baseline_readme, root),
            "unit_10_baseline_manifest": file_binding(baseline_manifest, root),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--receipt", type=Path, default=None)
    args = parser.parse_args()
    root = args.root.resolve()
    receipt = (args.receipt or (root / "qa/unit-12/HTML_ANIMATED_MEDIA_QA.json")).resolve()
    try:
        result = verify(root)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
    write_text(receipt, canonical_json(result))
    print(canonical_json({
        "status": "pass",
        "receipt": receipt.relative_to(root).as_posix(),
        "animated_figure": result["animated_figure"],
        "checks": result["checks"],
    }), end="")


if __name__ == "__main__":
    main()
