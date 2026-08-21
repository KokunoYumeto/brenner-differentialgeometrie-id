#!/usr/bin/env python3
"""Verify topology and protected mathematics for one Brenner translation unit.

The check deliberately does not judge Indonesian prose quality.  It proves that
translation did not change the TeX command topology, formula-bearing macro
calls, inline/display math, environments, or media locators.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


COMMAND_RE = re.compile(r"\\[A-Za-z@]+")
ENV_RE = re.compile(r"\\(begin|end)\s*\{([^{}]+)\}")
INLINE_MATH_RE = re.compile(r"(?<!\\)\$(?!\$)(.*?)(?<!\\)\$", re.DOTALL)
DISPLAY_MATH_RE = re.compile(r"\\\[(.*?)\\\]", re.DOTALL)

PROTECTED_COMMANDS = (
    "vergleichskette",
    "vergleichskettek",
    "maabb",
    "maabbdisp",
    "maabbeledisp",
    "mathbed",
    "includegraphics",
    "bildeinlesung",
    "bildeinlesungpng",
    "bildeinlesungPNG",
    "bildeinlesungjpg",
    "bildeinlesungJPG",
    "bildeinlesungjpeg",
    "bildeinlesungsvg",
    "bildeinlesunggif",
    "bildeinlesungGIF",
    "bildeinlesungxcf",
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def relative_path(path: Path, project_root: Path) -> str:
    return path.resolve().relative_to(project_root.resolve()).as_posix()


def normalized(value: str) -> str:
    return re.sub(r"\s+", "", value)


def braced(text: str, start: int) -> tuple[str, int]:
    if start >= len(text) or text[start] != "{":
        raise ValueError("expected opening brace")
    depth = 0
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1], index + 1
    raise ValueError("unclosed brace")


def command_calls(text: str, command: str) -> list[str]:
    marker = "\\" + command
    calls: list[str] = []
    cursor = 0
    while True:
        found = text.find(marker, cursor)
        if found < 0:
            break
        after_name = found + len(marker)
        if after_name < len(text) and text[after_name].isalpha():
            cursor = after_name
            continue
        end = after_name
        while end < len(text) and text[end].isspace():
            end += 1
        if end < len(text) and text[end] == "[":
            close = text.find("]", end + 1)
            if close < 0:
                raise ValueError(f"unclosed option for {marker}")
            end = close + 1
        argument_count = 0
        while True:
            while end < len(text) and text[end].isspace():
                end += 1
            if end >= len(text) or text[end] != "{":
                break
            _, end = braced(text, end)
            argument_count += 1
        if not argument_count:
            raise ValueError(f"protected command has no braced argument: {marker}")
        calls.append(normalized(text[found:end]))
        cursor = end
    return calls


def brace_profile(text: str) -> dict[str, int]:
    depth = 0
    maximum = 0
    left = 0
    right = 0
    escaped = False
    for char in text:
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
        elif char == "{":
            left += 1
            depth += 1
            maximum = max(maximum, depth)
        elif char == "}":
            right += 1
            depth -= 1
            if depth < 0:
                raise RuntimeError("closing brace before opening brace")
    if depth:
        raise RuntimeError(f"unbalanced braces: final depth {depth}")
    return {"opening": left, "closing": right, "maximum_depth": maximum}


def extract(text: str) -> dict[str, object]:
    protected = {name: command_calls(text, name) for name in PROTECTED_COMMANDS}
    return {
        "commands": COMMAND_RE.findall(text),
        "environments": ENV_RE.findall(text),
        "inline_math": [normalized(item) for item in INLINE_MATH_RE.findall(text)],
        "display_math": [normalized(item) for item in DISPLAY_MATH_RE.findall(text)],
        "protected_calls": protected,
        "brace_profile": brace_profile(text),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("target", type=Path)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--corrections", type=Path)
    args = parser.parse_args()

    source_bytes = args.source.read_bytes()
    target_bytes = args.target.read_bytes()
    source = source_bytes.decode("utf-8")
    target = target_bytes.decode("utf-8")
    if "\ufffd" in target:
        raise RuntimeError("target contains U+FFFD")
    source_profile = extract(source)
    target_profile = extract(target)
    allowed: list[dict[str, object]] = []
    if args.corrections:
        correction_payload = json.loads(args.corrections.read_text(encoding="utf-8"))
        if correction_payload.get("schema_version") != 1:
            raise RuntimeError("unsupported correction-manifest schema")
        allowed = correction_payload.get("allowed_deltas", [])
        if not isinstance(allowed, list):
            raise RuntimeError("allowed_deltas must be a list")
    consumed: set[int] = set()

    def profile_hash(value: object) -> str:
        payload = json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        return sha256(payload)

    def profile_equal_or_allowed(surface: str, source_value: object, target_value: object) -> bool:
        if source_value == target_value:
            return True
        source_hash = profile_hash(source_value)
        target_hash = profile_hash(target_value)
        matches = [
            allowed_index
            for allowed_index, item in enumerate(allowed)
            if allowed_index not in consumed
            and item.get("surface") == f"profile:{surface}"
            and item.get("source_sha256") == source_hash
            and item.get("target_sha256") == target_hash
        ]
        if len(matches) != 1:
            return False
        consumed.add(matches[0])
        return True

    def sequence_equal(surface: str, source_values: list[str], target_values: list[str]) -> bool:
        if len(source_values) != len(target_values):
            return False
        equal = True
        for index, (source_value, target_value) in enumerate(zip(source_values, target_values)):
            if source_value == target_value:
                continue
            source_hash = sha256(source_value.encode("utf-8"))
            target_hash = sha256(target_value.encode("utf-8"))
            matches = [
                allowed_index
                for allowed_index, item in enumerate(allowed)
                if allowed_index not in consumed
                and item.get("surface") == surface
                and item.get("index") == index
                and item.get("source_sha256") == source_hash
                and item.get("target_sha256") == target_hash
            ]
            if len(matches) != 1:
                equal = False
            else:
                consumed.add(matches[0])
        return equal

    failures: list[str] = []
    for field in ("commands", "environments"):
        if not profile_equal_or_allowed(field, source_profile[field], target_profile[field]):
            failures.append(field)
    if not sequence_equal("inline_math", source_profile["inline_math"], target_profile["inline_math"]):
        failures.append("inline_math")
    if not sequence_equal("display_math", source_profile["display_math"], target_profile["display_math"]):
        failures.append("display_math")
    for command in PROTECTED_COMMANDS:
        if not sequence_equal(
            f"protected:{command}",
            source_profile["protected_calls"][command],
            target_profile["protected_calls"][command],
        ):
            failures.append(f"protected:{command}")
    source_braces = source_profile["brace_profile"]
    target_braces = target_profile["brace_profile"]
    if not profile_equal_or_allowed("brace_profile", source_braces, target_braces):
        failures.append("brace_profile")
    unused = sorted(set(range(len(allowed))) - consumed)
    if unused:
        failures.append("unused_allowed_deltas")

    receipt = {
        "schema_version": 1,
        "source": relative_path(args.source, args.project_root),
        "source_bytes": len(source_bytes),
        "source_sha256": sha256(source_bytes),
        "target": relative_path(args.target, args.project_root),
        "target_bytes": len(target_bytes),
        "target_sha256": sha256(target_bytes),
        "checks": {
            "utf8_without_replacement_character": "\ufffd" not in target,
            "command_sequence_equal_or_declared": "commands" not in failures,
            "environment_sequence_equal_or_declared": "environments" not in failures,
            "inline_math_equal_or_declared": "inline_math" not in failures,
            "display_math_equal_or_declared": "display_math" not in failures,
            "protected_macro_calls_equal_or_declared": not any(item.startswith("protected:") for item in failures),
            "brace_profile_equal_or_declared": "brace_profile" not in failures,
            "all_declared_deltas_consumed": not unused,
        },
        "counts": {
            "commands": len(source_profile["commands"]),
            "environments": len(source_profile["environments"]),
            "inline_math": len(source_profile["inline_math"]),
            "display_math": len(source_profile["display_math"]),
            "protected_calls": sum(len(value) for value in source_profile["protected_calls"].values()),
        },
        "status": "pass" if not failures else "fail",
        "failures": failures,
        "declared_corrections": [allowed[index].get("correction_id") for index in sorted(consumed)],
    }
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    if failures:
        raise RuntimeError("translation verification failed: " + ", ".join(failures))


if __name__ == "__main__":
    main()
