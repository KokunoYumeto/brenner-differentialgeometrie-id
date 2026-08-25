#!/usr/bin/env python3
"""Verify the exact, ledgered mathematical repairs in O011 Unit 5."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LECTURE_SOURCE = ROOT / "authority/expanded/lecture05_source.de.tex"
WORKSHEET_SOURCE = ROOT / "authority/expanded/worksheet05_source.de.tex"
SOLUTION_SOURCE = ROOT / "authority/expanded/worksheet05_exercise01_solution_source.de.tex"
LECTURE_TARGET = ROOT / "source/units/unit-05/lecture05.id.tex"
WORKSHEET_TARGET = ROOT / "source/units/unit-05/worksheet05.id.tex"
SOLUTION_TARGET = ROOT / "source/units/unit-05/worksheet05_exercise01_solution.id.tex"
LEDGER = ROOT / "00_control/ADVERSE_LEDGER.csv"
OUTPUT = ROOT / "qa/unit-05/POST_REPAIR_MATH_QA.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compact(value: str) -> str:
    return re.sub(r"\s+", "", value)


def require(condition: bool, message: str, checks: list[str]) -> None:
    if not condition:
        raise RuntimeError(message)
    checks.append(message)


def load_receipt(name: str) -> dict[str, object]:
    return json.loads((ROOT / "qa/unit-05" / name).read_text(encoding="utf-8"))


def main() -> None:
    lecture_source = LECTURE_SOURCE.read_text(encoding="utf-8")
    worksheet_source = WORKSHEET_SOURCE.read_text(encoding="utf-8")
    solution_source = SOLUTION_SOURCE.read_text(encoding="utf-8")
    lecture = LECTURE_TARGET.read_text(encoding="utf-8")
    worksheet = WORKSHEET_TARGET.read_text(encoding="utf-8")
    solution = SOLUTION_TARGET.read_text(encoding="utf-8")
    ls = compact(lecture_source)
    ws = compact(worksheet_source)
    ss = compact(solution_source)
    lt = compact(lecture)
    wt = compact(worksheet)
    st = compact(solution)
    checks: list[str] = []

    require("stetigdifferenzierbareFunktion" in ls, "source C1 witness retained", checks)
    require("differenzierbareFunktion" in ls, "source rotational differentiability witness retained", checks)
    require("fungsiyangterdiferensialkansecarakontinu" not in lt, "lecture affected C1 hypotheses removed", checks)
    require("fungsiterdiferensialkan" not in lt, "rotational C1 hypothesis removed", checks)
    require("fungsiyangterdiferensialkansecarakontinu" not in wt, "worksheet Exercise 7 C1 hypothesis removed", checks)

    require("Kugel/Radius/Weingartenabbildung/Beispiel|Beispiel4.4" in ls, "wrong graph cross-reference retained in authority", checks)
    graph_target = lt[lt.index("g=\\operatorname{Grad}f(Q)") : lt.index("Catatanedisi:sumbermenunjukcontohbola")]
    require("Kugel/Radius/Weingartenabbildung/Beispiel" not in graph_target, "wrong graph cross-reference removed from target example", checks)
    require("A=G^{-1}{\\frac{1}{\\omega}}H" in graph_target, "graph operator contains inverse metric", checks)
    require("Hu=\\kappa\\,\\omegaGu" in graph_target, "generalized principal-direction eigenproblem present", checks)
    require("K={\\frac{\\detH}{\\omega^4}}" in graph_target, "graph Gaussian curvature has omega fourth power", checks)

    require("z^2<f(x_0)" in ls, "wrong rotational domain retained in authority", checks)
    require("z^2<f(x)^2" in lt and "|z|<f(x)" in lt, "rotational graph domain repaired", checks)
    require("f^{\\prime\\prime}(x_0)}{\\omega^3" in lt, "meridional curvature has omega cubed", checks)
    require("f(x_0)\\omega" in lt, "parallel curvature has f omega denominator", checks)
    require("\\left(1+f'(x_0)^2\\right)^2" in lt, "rotational Gaussian curvature has squared metric factor", checks)

    require("basisortonormal" in lt, "Euler formula uses orthonormal principal basis", checks)
    require("\\lVertv\\rVert=1" in lt, "Euler formula requires a unit direction", checks)
    require("\\lVertv\\rVert^2\\kappa" in lt, "Euler formula states nonunit scaling identity", checks)

    require("\\gamma'(0)=v" in lt, "normal-section realization fixes tangent direction", checks)
    require("normalsatuankurvairisandidalambidang" in lt, "normal-section in-plane curve normal fixed", checks)
    require("$(v,N(P))$sebagaibasisberorientasipositif" in lt, "normal-section plane orientation fixed", checks)
    require("hanyanilaimutlak" in lt and "hanyamenentukankesamaannilaimutlak" in wt, "orientation-free absolute-value limitation disclosed", checks)

    require("\\operatorname{Grad}f(0)=0" in st and "G=I" in st, "supplied solution justifies Hessian reduction by graph metric", checks)
    require("c\\neq0" in st, "supplied solution isolates generic nonzero-c branch", checks)
    require("setiapvektortaknol" in st, "scalar-map eigendirections exclude the zero vector", checks)
    require(st.count("\\mathkor") == 2, "both diagonal orderings are explicit", checks)
    require("jederVektor" in ss, "incomplete scalar-case wording retained in authority", checks)

    require(worksheet.count("\\inputaufgabe\n") == 14, "fourteen ordinary exercise macros retained", checks)
    require(worksheet.count("\\inputaufgabegibtloesung") == 1, "exactly one solution-bearing exercise retained", checks)
    require(worksheet.count("Petunjuk:") == 1, "exactly one Indonesian hint retained", checks)
    point_markers = [
        value.strip()
        for value in re.findall(r"\\inputaufgabe\s*\{([^{}]*)\}", worksheet)
        if value.strip()
    ]
    require(point_markers == ["4", "4", "6", "6 (2+2+2)", "2"], "graded point-marker sequence retained", checks)
    require(sum(int(re.match(r"\d+", value).group()) for value in point_markers) == 22, "graded point total is 22", checks)

    expected_receipts = {
        "lecture05_translation.json": {f"O011-CORR-{number:04d}" for number in range(46, 53)},
        "worksheet05_translation.json": {"O011-CORR-0046", "O011-CORR-0052"},
        "worksheet05_exercise01_solution_translation.json": {"O011-CORR-0047", "O011-CORR-0053"},
    }
    receipt_hashes: dict[str, str] = {}
    for name, expected in expected_receipts.items():
        receipt = load_receipt(name)
        require(receipt.get("status") == "pass", f"translation receipt passes: {name}", checks)
        declared = set(receipt.get("declared_corrections") or [])
        require(expected <= declared, f"translation receipt declares correction closure: {name}", checks)
        receipt_hashes[name] = sha256(ROOT / "qa/unit-05" / name)

    ledger = LEDGER.read_text(encoding="utf-8")
    for number in range(46, 54):
        correction_id = f"O011-CORR-{number:04d}"
        require(f"\n{correction_id}," in ledger, f"adverse ledger contains {correction_id}", checks)

    payload = {
        "schema_version": 1,
        "unit_id": "o011-brenner-u05",
        "status": "pass",
        "correction_ids": [f"O011-CORR-{number:04d}" for number in range(46, 54)],
        "checks_passed": len(checks),
        "checks": checks,
        "authority_sha256": {
            "lecture": sha256(LECTURE_SOURCE),
            "worksheet": sha256(WORKSHEET_SOURCE),
            "solution_01": sha256(SOLUTION_SOURCE),
        },
        "target_sha256": {
            "lecture": sha256(LECTURE_TARGET),
            "worksheet": sha256(WORKSHEET_TARGET),
            "solution_01": sha256(SOLUTION_TARGET),
        },
        "translation_receipt_sha256": receipt_hashes,
    }
    OUTPUT.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps({"status": "pass", "checks": len(checks)}, separators=(",", ":")))


if __name__ == "__main__":
    main()
