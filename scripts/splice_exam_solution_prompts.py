#!/usr/bin/env python3
"""Replace solution-form prompts with already-admitted learner-form prompts.

The operation is occurrence-ordered and refuses any count or point mismatch.
Only the prompt argument is replaced; official solution arguments remain intact.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


def braced_argument(text: str, start: int) -> tuple[int, int, str]:
    while start < len(text) and text[start].isspace():
        start += 1
    if start >= len(text) or text[start] != "{":
        raise RuntimeError(f"expected braced argument at byte {start}")
    depth = 0
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return start, index + 1, text[start + 1 : index]
    raise RuntimeError("unterminated braced argument")


def calls(text: str, command: str, argument_count: int) -> list[list[tuple[int, int, str]]]:
    pattern = re.compile(rf"\\{re.escape(command)}(?![A-Za-z@])")
    result: list[list[tuple[int, int, str]]] = []
    for match in pattern.finditer(text):
        cursor = match.end()
        arguments: list[tuple[int, int, str]] = []
        for _ in range(argument_count):
            argument = braced_argument(text, cursor)
            arguments.append(argument)
            cursor = argument[1]
        result.append(arguments)
    return result


def normalized(value: str) -> str:
    return re.sub(r"\s+", "", value)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("solution_target", type=Path)
    parser.add_argument("learner_target", type=Path)
    args = parser.parse_args()

    solution = args.solution_target.read_text(encoding="utf-8")
    learner = args.learner_target.read_text(encoding="utf-8")
    solution_calls = calls(solution, "inputaufgabeklausurloesung", 3)
    learner_calls = sorted(
        calls(learner, "inputaufgabegibtloesung", 2)
        + calls(learner, "inputaufgabe", 2),
        key=lambda call: call[0][0],
    )
    if len(solution_calls) != len(learner_calls):
        raise RuntimeError(
            f"occurrence mismatch: solution={len(solution_calls)}, learner={len(learner_calls)}"
        )
    replacements: list[tuple[int, int, str]] = []
    for index, (solution_call, learner_call) in enumerate(
        zip(solution_calls, learner_calls), start=1
    ):
        if normalized(solution_call[0][2]) != normalized(learner_call[0][2]):
            raise RuntimeError(f"point mismatch at actual occurrence {index}")
        start, end, _ = solution_call[1]
        replacements.append((start, end, "{" + learner_call[1][2] + "}"))
    for start, end, replacement in reversed(replacements):
        solution = solution[:start] + replacement + solution[end:]
    args.solution_target.write_text(solution, encoding="utf-8", newline="\n")
    print(f"spliced {len(replacements)} learner prompts")


if __name__ == "__main__":
    main()
