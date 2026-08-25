#!/usr/bin/env python3
"""Fail-closed verification of the ledgered mathematical repairs in O011 Unit 6."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "qa/unit-06/POST_REPAIR_MATH_QA.json"

CORRECTION_IDS = tuple(f"O011-CORR-{number:04d}" for number in range(54, 70))

AUTHORITY_FILES = {
    "lecture": (
        "authority/expanded/lecture06_source.de.tex",
        "7fde9eb970e13ecaeb9a6a4368a77f002c2b62d691dcc84139a6db50aef5d3e8",
    ),
    "worksheet": (
        "authority/expanded/worksheet06_source.de.tex",
        "886426135b7eeed2fc951670e897bbb8dd9f281e4500f1e71a084a1450aff57b",
    ),
    "solution_02": (
        "authority/expanded/worksheet06_exercise02_solution_source.de.tex",
        "97b063b6f25eadad6dd7fd6eaae1fce4a61c979f513d6139cac846114a6f6025",
    ),
    "solution_06": (
        "authority/expanded/worksheet06_exercise06_solution_source.de.tex",
        "f986bce024056c1979de52dc33b5afff08e889559dd2a9ebee39c826d452a59a",
    ),
    "solution_09": (
        "authority/expanded/worksheet06_exercise09_solution_source.de.tex",
        "9eefeeabb0e4769e28c4340d4ce2fa33172773862fdcbb791f21e583ea8e1b61",
    ),
    "authority_preflight": (
        "qa/unit-06/AUTHORITY_PREFLIGHT.json",
        "20e961850dccf9f31a1ad62e8d4aef1a8d43e642d23168863956427e7b28695d",
    ),
    "solution_closure": (
        "qa/unit-06/solution_closure.json",
        "8d0588494f1ee1cb2736eae20cb97507e734ec5b6ba5d2b286c492f2d8ee2c98",
    ),
    "media": (
        "authority/media/Parallel transport sphere2.svg",
        "4a6215c455dc248c97d1831e9af8b5d551a7cdb5da46976df2c1a77c959b88f8",
    ),
}

# These whole-file hashes deliberately make a later target edit invalidate the receipt.
TARGET_FILES = {
    "lecture": (
        "source/units/unit-06/lecture06.id.tex",
        "180c553eb556d91ba733e00f012bd0ece36c32e66704c992f0c64244ab6e05e8",
    ),
    "worksheet": (
        "source/units/unit-06/worksheet06.id.tex",
        "b0cf54f892e2357bd6edaf1ed87df711cffcdf164c1454e7b7d2c987faa8bca5",
    ),
    "solution_02": (
        "source/units/unit-06/worksheet06_exercise02_solution.id.tex",
        "772755e8e7d46abd63b2acf146fec3be01a23f57476cbea153ff14668a316ad5",
    ),
    "solution_06": (
        "source/units/unit-06/worksheet06_exercise06_solution.id.tex",
        "e10704fec468e5ee582e72415ef85d92ad6182a3a4207359ad10ac41b9a581ac",
    ),
    "solution_09": (
        "source/units/unit-06/worksheet06_exercise09_solution.id.tex",
        "fd027471aa6655aaf6b2d07c60e7a96cb5d13df961adca1c38d2021cc19cf39b",
    ),
}

EXPECTED_RECEIPTS = {
    "lecture06_translation.json": {
        "source": AUTHORITY_FILES["lecture"][0],
        "target": TARGET_FILES["lecture"][0],
        "corrections": {f"O011-CORR-{number:04d}" for number in range(54, 63)}
        | {"O011-CORR-0069"},
    },
    "worksheet06_translation.json": {
        "source": AUTHORITY_FILES["worksheet"][0],
        "target": TARGET_FILES["worksheet"][0],
        "corrections": {
            "O011-CORR-0059",
            "O011-CORR-0063",
            "O011-CORR-0064",
            "O011-CORR-0065",
            "O011-CORR-0066",
            "O011-CORR-0068",
        },
    },
    "worksheet06_exercise02_solution_translation.json": {
        "source": AUTHORITY_FILES["solution_02"][0],
        "target": TARGET_FILES["solution_02"][0],
        "corrections": {"O011-CORR-0067"},
    },
    "worksheet06_exercise06_solution_translation.json": {
        "source": AUTHORITY_FILES["solution_06"][0],
        "target": TARGET_FILES["solution_06"][0],
        "corrections": set(),
    },
    "worksheet06_exercise09_solution_translation.json": {
        "source": AUTHORITY_FILES["solution_09"][0],
        "target": TARGET_FILES["solution_09"][0],
        "corrections": set(),
    },
}

EXPECTED_MANIFESTS = {
    "LECTURE06_PROTECTED_CORRECTIONS.json": {
        "scope": TARGET_FILES["lecture"][0],
        "corrections": {f"O011-CORR-{number:04d}" for number in range(54, 63)}
        | {"O011-CORR-0069"},
    },
    "WORKSHEET06_PROTECTED_CORRECTIONS.json": {
        "scope": TARGET_FILES["worksheet"][0],
        "corrections": {
            "O011-CORR-0059",
            "O011-CORR-0063",
            "O011-CORR-0064",
            "O011-CORR-0065",
            "O011-CORR-0066",
            "O011-CORR-0068",
        },
    },
    "SOLUTION06_02_PROTECTED_CORRECTIONS.json": {
        "scope": TARGET_FILES["solution_02"][0],
        "corrections": {"O011-CORR-0067"},
    },
}

EXPECTED_LEDGER_ROWS = {
    "O011-CORR-0054": {
        "severity": "P2",
        "surface": "lecture06:opening-hypersurface-relation",
        "status": "corrected_in_target",
        "description": "The opening display calls Y a hypersurface but states Y equals the ambient space R n",
        "disposition": "Replace equality by the required subset relation and disclose the correction",
    },
    "O011-CORR-0055": {
        "severity": "P2",
        "surface": "lecture06:lemma06-03-product-rule",
        "status": "corrected_in_target",
        "description": "The product rule applies a point evaluation to nabla sub v F even though v in T P Y already makes it a vector at P and the proof writes D g F ambiguously",
        "disposition": "Remove the stray point evaluation and write D of the product g F in the proof",
    },
    "O011-CORR-0056": {
        "severity": "P2",
        "surface": "lecture06:lemma06-04-product-rule",
        "status": "corrected_in_target",
        "description": "The displayed Leibniz rule equates a field-valued left side with a pointwise right side containing a free point P",
        "disposition": "Evaluate the left side at P so both sides are pointwise vectors",
    },
    "O011-CORR-0057": {
        "severity": "P2",
        "surface": "lecture06:definition06-05-domain",
        "status": "corrected_in_target",
        "description": "The definition gives gamma domain a b but gives F the undefined domain I and calls F a field along I",
        "disposition": "Use the common interval I for gamma and F and call F a field along gamma",
    },
    "O011-CORR-0058": {
        "severity": "P2",
        "surface": "lecture06:definition06-05-generalization-type",
        "status": "corrected_in_target",
        "description": "The footnote declares F as a tangent-bundle-valued map but applies an ambient derivative D F directly to the orthogonal projection on R n",
        "disposition": "Declare F as an R n valued map whose values lie in the appropriate tangent spaces",
    },
    "O011-CORR-0059": {
        "severity": "P1",
        "surface": "lecture06-and-worksheet06:parallel-transport-regularity-and-existence",
        "status": "corrected_in_target",
        "description": "The existence proof differentiates an unintroduced normal and assumes only C1 data and it never proves the ODE solution stays tangent while later transport and holonomy claims inherit the same gap",
        "disposition": "Require a C2 hypersurface where existence transport or holonomy depends on a differentiable normal and add the missing invariant tangency calculation",
    },
    "O011-CORR-0060": {
        "severity": "P3",
        "surface": "lecture06:remark06-10-ode-coefficient",
        "status": "corrected_in_target",
        "description": "The coordinate coefficient A i j contains an unmatched closing parenthesis in the derivative of the normal component",
        "disposition": "Write A i j equals N i times N prime j with balanced parentheses",
    },
    "O011-CORR-0061": {
        "severity": "P2",
        "surface": "lecture06:parallel-transport-linearity-proof",
        "status": "corrected_in_target",
        "description": "The proof claims the initial value of r F plus s G is v plus w while the next line and linearity require r v plus s w",
        "disposition": "Restore the scalar factors in the initial value",
    },
    "O011-CORR-0062": {
        "severity": "P2",
        "surface": "lecture06:parallel-transport-inner-product-proof",
        "status": "corrected_in_target",
        "description": "The constant inner-product chain changes its second initial field from G to F and therefore no longer proves the claimed mixed inner product",
        "disposition": "Replace the second F at the initial point by G",
    },
    "O011-CORR-0063": {
        "severity": "P3",
        "surface": "worksheet06:exercise01-tangent-membership",
        "status": "corrected_in_target",
        "description": "The exercise equates a vector v with the tangent space T P Y",
        "disposition": "Replace equality by membership",
    },
    "O011-CORR-0064": {
        "severity": "P1",
        "surface": "worksheet06:exercise04-hyperplane-parallel-field",
        "status": "corrected_in_target",
        "description": "The exercise falsely claims every tangent vector field on a hyperplane is parallel although its ordinary derivative can be nonzero",
        "disposition": "Restrict the claim to constant tangent vector fields",
    },
    "O011-CORR-0065": {
        "severity": "P2",
        "surface": "worksheet06:exercise07-path-domain",
        "status": "corrected_in_target",
        "description": "The cube-root component is not differentiable at t equals negative 3 to the power negative one fifth although the path domain is all real numbers",
        "disposition": "Restrict the path to an interval avoiding the singular parameter",
    },
    "O011-CORR-0066": {
        "severity": "P1",
        "surface": "worksheet06:exercise17-sphere-holonomy",
        "status": "corrected_in_target",
        "description": "The exercise identifies sphere holonomy with the full orthogonal isometry group although parallel transport preserves orientation",
        "disposition": "Ask for the orientation-preserving group SO 2 at each tangent plane",
    },
    "O011-CORR-0067": {
        "severity": "P1",
        "surface": "worksheet06:exercise02-supplied-solution",
        "status": "corrected_in_target",
        "description": "The supplied matrix is the negative of the matrix determined by its own two displayed basis images",
        "disposition": "Use columns negative e two and e one to obtain the corrected matrix",
    },
    "O011-CORR-0068": {
        "severity": "P2",
        "surface": "worksheet06:exercise08-affine-hyperplane-identification",
        "status": "corrected_in_target",
        "description": "The exercise identifies every tangent vector space of an affine hyperplane directly with the affine set Y although only its linear direction space is canonically a vector space",
        "disposition": "Identify each tangent space with the common direction space V equals Y minus P and disclose the clarification",
    },
    "O011-CORR-0069": {
        "severity": "P2",
        "surface": "lecture06:theorem06-09-global-ode-existence",
        "status": "corrected_in_target",
        "description": "The proof invokes a theorem that states only local existence and uniqueness as if it directly yielded a solution on the full interval I",
        "disposition": "State local existence first and justify unique continuation across I from linearity and continuity of the coefficients",
    },
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compact(value: str) -> str:
    return re.sub(r"\s+", "", value)


def require(condition: bool, message: str, checks: list[str]) -> None:
    if not condition:
        raise RuntimeError(message)
    checks.append(message)


def load_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON root must be an object: {path}")
    return value


def main() -> None:
    OUTPUT.unlink(missing_ok=True)
    checks: list[str] = []

    authority_hashes: dict[str, str] = {}
    for label, (relative, expected_hash) in AUTHORITY_FILES.items():
        path = ROOT / relative
        require(path.is_file(), f"authority file exists: {relative}", checks)
        actual_hash = sha256(path)
        require(actual_hash == expected_hash, f"frozen authority hash matches: {label}", checks)
        authority_hashes[label] = actual_hash

    target_hashes: dict[str, str] = {}
    target_by_relative: dict[str, str] = {}
    for label, (relative, expected_hash) in TARGET_FILES.items():
        path = ROOT / relative
        require(path.is_file(), f"target file exists: {relative}", checks)
        actual_hash = sha256(path)
        require(actual_hash == expected_hash, f"frozen target hash matches: {label}", checks)
        target_hashes[label] = actual_hash
        target_by_relative[relative] = actual_hash

    lecture_source = (ROOT / AUTHORITY_FILES["lecture"][0]).read_text(encoding="utf-8")
    worksheet_source = (ROOT / AUTHORITY_FILES["worksheet"][0]).read_text(encoding="utf-8")
    solution02_source = (ROOT / AUTHORITY_FILES["solution_02"][0]).read_text(encoding="utf-8")
    lecture = (ROOT / TARGET_FILES["lecture"][0]).read_text(encoding="utf-8")
    worksheet = (ROOT / TARGET_FILES["worksheet"][0]).read_text(encoding="utf-8")
    solution02 = (ROOT / TARGET_FILES["solution_02"][0]).read_text(encoding="utf-8")
    solution06 = (ROOT / TARGET_FILES["solution_06"][0]).read_text(encoding="utf-8")
    solution09 = (ROOT / TARGET_FILES["solution_09"][0]).read_text(encoding="utf-8")
    require(
        re.search(r"(?m)^[.,;:]\}?$", lecture) is None,
        "lecture has no punctuation-only lines, including punctuation before a closing macro brace",
        checks,
    )
    ls, ws, ss = compact(lecture_source), compact(worksheet_source), compact(solution02_source)
    lt, wt, st = compact(lecture), compact(worksheet), compact(solution02)

    # Bind the independently frozen authority census before testing the translation.
    preflight = load_json(ROOT / AUTHORITY_FILES["authority_preflight"][0])
    structure = preflight.get("structure")
    media = preflight.get("media")
    require(preflight.get("status") == "pass" and preflight.get("unit") == 6, "Unit 6 authority preflight passes", checks)
    require(isinstance(structure, dict), "authority structure object is present", checks)
    assert isinstance(structure, dict)
    expected_structure = {
        "worksheet_exercise_count": 18,
        "worksheet_practice_count": 14,
        "worksheet_graded_count": 4,
        "worksheet_point_total": 14,
        "worksheet_solution_bearing_indices": [2, 6, 9],
        "all_hint_fields_blank": True,
    }
    for field, expected in expected_structure.items():
        require(structure.get(field) == expected, f"authority topology matches: {field}", checks)
    require(isinstance(media, dict), "authority media object is present", checks)
    assert isinstance(media, dict)
    require(media.get("occurrence_count") == 1, "authority has one media occurrence", checks)
    require(media.get("unique_asset_count") == 1, "authority has one unique media asset", checks)
    require(
        media.get("surface_occurrences")
        == [{"filename": "Parallel transport sphere2.svg", "surface": "lecture06", "surface_order": 1}],
        "authority media occurrence identity matches",
        checks,
    )

    closure = load_json(ROOT / AUTHORITY_FILES["solution_closure"][0])
    exercises = closure.get("exercises")
    require(isinstance(exercises, list) and len(exercises) == 18, "solution closure has eighteen exercise rows", checks)
    assert isinstance(exercises, list)
    require([item.get("exercise_index") for item in exercises] == list(range(1, 19)), "solution closure indices are contiguous", checks)
    require(all(item.get("hint_field") == "" for item in exercises), "all eighteen frozen hint fields are blank", checks)
    require([item.get("exercise_index") for item in exercises if item.get("solution_marker")] == [2, 6, 9], "frozen solution markers are exactly 2, 6, and 9", checks)
    require([item.get("exercise_index") for item in exercises if item.get("exists")] == [2, 6, 9], "frozen supplied solution pages are exactly 2, 6, and 9", checks)
    require([item.get("point_value") for item in exercises] == [None] * 14 + [2, 4, 4, 4], "frozen point sequence is blank times fourteen then 2, 4, 4, 4", checks)
    require(closure.get("practice_exercise_count") == 14 and closure.get("graded_exercise_count") == 4, "frozen practice and graded counts are 14 and 4", checks)
    require(closure.get("point_value_total") == 14, "frozen graded point total is 14", checks)

    # Bind the target exercise macros independently of the source receipt.
    macro_matches = list(
        re.finditer(
            r"(?m)^\\inputaufgabe(?P<solution>gibtloesung)?\s*\n\{(?P<points>[^{}]*)\}",
            worksheet,
        )
    )
    require(len(macro_matches) == 18, "target contains exactly eighteen exercise macros", checks)
    solution_positions = [index for index, match in enumerate(macro_matches, 1) if match.group("solution")]
    require(solution_positions == [2, 6, 9], "target solution-bearing macro positions are exactly 2, 6, and 9", checks)
    target_points = [match.group("points").strip() or None for match in macro_matches]
    require(target_points == [None] * 14 + ["2", "4", "4", "4"], "target point-marker sequence is exact", checks)
    require(sum(int(value) for value in target_points if value is not None) == 14, "target graded point total is 14", checks)
    require("Petunjuk:" not in worksheet and "Hinweis:" not in worksheet, "target introduces no hints", checks)

    solution_directory = ROOT / "source/units/unit-06"
    found_solution_files = {path.name for path in solution_directory.glob("worksheet06_exercise*_solution.id.tex")}
    expected_solution_files = {
        "worksheet06_exercise02_solution.id.tex",
        "worksheet06_exercise06_solution.id.tex",
        "worksheet06_exercise09_solution.id.tex",
    }
    require(found_solution_files == expected_solution_files, "target supplied-solution files are exactly 02, 06, and 09", checks)
    all_targets = (lecture, worksheet, solution02, solution06, solution09)
    require(sum(value.count("\\includegraphics") for value in all_targets) == 1, "target contains exactly one displayed media occurrence", checks)
    require(lecture.count("Parallel transport sphere2") == 2, "lecture has one media call and one matching license call", checks)
    require(lecture.count("\\bildlizenz") == 1, "target contains exactly one media-license call", checks)
    require("{Sillyrabbit}{enWikipedia}{CC-by-sa3.0}" in compact(lecture), "target preserves the media creator and CC BY-SA 3.0 credit", checks)

    # Exact authority/repair witness pairs. These checks intentionally retain evidence of the source defects.
    lecture_opening_source = ls[: ls.index("\\inputdefinition")]
    lecture_opening_target = lt[: lt.index("\\inputdefinition")]
    require("{Y}{=}{\\R^n}" in lecture_opening_source, "authority retains the opening Y equals R n defect", checks)
    require("{Y}{\\subseteq}{\\R^n}" in lecture_opening_target, "opening relation is Y subset R n", checks)
    require("{Y}{=}{\\R^n}" not in lecture_opening_target, "opening ambient-space equality is absent from target", checks)

    source_pointwise_v = "{\\nabla_v(gF)}{=}{g(P)(\\nabla_vF)(P)+\\left(D_{v}g\\right)\\left(P\\right)F(P)"
    target_pointwise_v = "{\\nabla_v(gF)}{=}{g(P)\\nabla_vF+\\left(D_{v}g\\right)\\left(P\\right)F(P)"
    require(source_pointwise_v in ls, "authority retains the over-evaluated v-Leibniz formula", checks)
    require(target_pointwise_v in lt, "pointwise v-Leibniz formula is correctly typed", checks)
    require("\\left(D(gF)\\right)_{P}" in lt, "v-Leibniz proof differentiates the product gF unambiguously", checks)

    source_pointwise_g = "{\\nabla_G(gF)}{=}{g(P)(\\nabla_GF)(P)+(\\nabla_Gg)(P)F(P)"
    target_pointwise_g = "{(\\nabla_G(gF))(P)}{=}{g(P)(\\nabla_GF)(P)+(\\nabla_Gg)(P)F(P)"
    require(source_pointwise_g in ls, "authority retains the field-versus-point mismatch in the G-Leibniz formula", checks)
    require(target_pointwise_g in lt, "pointwise G-Leibniz formula is correctly typed", checks)

    gamma_pattern = re.compile(r"\\maabbdisp\s*\{\\gamma\}\s*\{([^{}]*)\}")
    f_domain_pattern = re.compile(r"\\maabbdisp\s*\{F\}\s*\{([^{}]*)\}\s*\{\s*\\R\^n")
    source_gamma_match = gamma_pattern.search(lecture_source)
    target_gamma_match = gamma_pattern.search(lecture)
    require(source_gamma_match is not None and target_gamma_match is not None, "covariant-along-curve gamma maps are present", checks)
    assert source_gamma_match is not None and target_gamma_match is not None
    source_f_match = f_domain_pattern.search(lecture_source, source_gamma_match.end())
    target_f_match = f_domain_pattern.search(lecture, target_gamma_match.end())
    require(source_f_match is not None and target_f_match is not None, "covariant-along-curve F maps are present", checks)
    assert source_f_match is not None and target_f_match is not None
    require(source_gamma_match.group(1).strip() == "[a,b]" and source_f_match.group(1).strip() == "I", "authority retains the mismatched gamma and F domains", checks)
    require(target_gamma_match.group(1).strip() == "I" and target_f_match.group(1).strip() == "I", "gamma and its vector field share the common interval I", checks)
    require("\\maabbdisp{F}{Z}{TY=\\biguplus_{P\\inY}T_PY}" in ls, "authority retains the tangent-bundle-valued F declaration", checks)
    require("\\maabbdisp{F}{Z}{\\R^n}{}" in lt and "F(Q)\\inT_{\\varphi(Q)}Y" in lt, "generalized F map is ambient-valued with tangent values", checks)

    require(ls.count("C^2") == 0, "authority lecture contains no C2 repair text", checks)
    require(lt.count("kelas$C^2$") == 3, "existence, transport, and transport-isometry hypotheses are C2", checks)
    require(ws.count("stetigdifferenzierbareFunktion") == 3, "authority worksheet retains three C1 holonomy hypotheses", checks)
    require(wt.count("fungsiyangduakaliterdiferensialkansecarakontinu") == 3, "three worksheet transport and holonomy hypotheses are C2", checks)
    tangency_invariant = (
        "\\frac{d}{dt}\\left\\langleF(t),N(\\gamma(t))\\right\\rangle"
        "=-\\left\\langleF(t),(N\\circ\\gamma)'(t)\\right\\rangle"
        "+\\left\\langleF(t),(N\\circ\\gamma)'(t)\\right\\rangle=0."
    )
    require(tangency_invariant in lt, "parallel-field existence proof contains the tangency invariant", checks)
    require("Jadi$F(t)$tetaptangensial" in lt, "parallel-field existence proof closes tangency", checks)
    require(
        "eineeindeutigeLösungbesitzt.EskannalsohöchstenseineLösungderAusgangsgleichunggeben" in ls,
        "authority relies on an undifferentiated unique-solution claim",
        checks,
    )
    require("memilikisolusilokaltunggal" in lt, "Theorem 6.9 states local ODE existence first", checks)
    require(
        "Karenapersamaaninilineardengankoefisienkontinupada$I$,solusitersebutdapatdilanjutkansecaraunikkeseluruhinterval$I$"
        in lt,
        "Theorem 6.9 justifies unique continuation across I from linear continuous coefficients",
        checks,
    )

    require("{A_{ij}(t)}{=}{N(\\gamma(t))_iN(\\gamma(t)))'_j}" in ls, "authority retains the unbalanced Aij coefficient", checks)
    require("{A_{ij}(t)}{=}{N(\\gamma(t))_i(N(\\gamma(t)))'_j}" in lt, "Aij equals Ni times N-prime-j with balanced parentheses", checks)
    require("{(rF+sG)(a)}{=}{v+w}" in ls, "authority retains the missing scalar factors", checks)
    require("{(rF+sG)(a)}{=}{rv+sw}" in lt, "parallel-transport linearity proof has rv plus sw", checks)
    require("{=}{\\left\\langleF(a),F(a)\\right\\rangle}{=}{\\left\\langlev,w\\right\\rangle}" in ls, "authority retains the repeated F in the mixed inner product", checks)
    require("{=}{\\left\\langleF(a),G(a)\\right\\rangle}{=}{\\left\\langlev,w\\right\\rangle}" in lt, "parallel transport preserves the mixed inner product F(a), G(a)", checks)

    vector = "\\begin{pmatrix}2\\\\1\\\\2\\end{pmatrix}"
    require(f"{{v}}{{=}}{{{vector}}}{{=}}{{T_PY}}" in ws, "authority retains v equals T_PY", checks)
    require(f"{{v}}{{=}}{{{vector}}}{{\\in}}{{T_PY}}" in wt, "Exercise 1 states v is in T_PY", checks)
    require("Buktikanbahwasetiap\\definitionsverweis{medanvektortangensial}{}{}$F$yangkonstan" in wt, "Exercise 4 is restricted to constant tangent vector fields", checks)
    require("$F$yangkonstan" not in ws, "authority Exercise 4 has no constant-field restriction", checks)
    require("\\maabbeledisp{\\gamma}{\\R}{Y}" in ws, "authority Exercise 7 uses all real parameters", checks)
    require("\\maabbeledisp{\\gamma}{(-3^{-1/5},\\infty)}{Y}" in wt, "Exercise 7 uses an interval excluding the singular parameter", checks)
    require("$T_PY$mit$Y$identifiziert" in ws, "authority Exercise 8 identifies tangent spaces with the affine set Y", checks)
    require(
        "$T_PY$diidentifikasisecarakanonisdenganruangarahlinear$V=Y-P$" in wt,
        "Exercise 8 identifies tangent spaces with the affine hyperplane direction space",
        checks,
    )
    require("\\operatorname{SO}(T_PY)\\cong\\operatorname{SO}(2)" in wt, "Exercise 17 asks for the orientation-preserving SO(2) holonomy", checks)
    require("gleichder\\definitionsverweis{Isometriegruppe}{}{}ist" in ws, "authority Exercise 17 asks for the full isometry group", checks)

    wrong_matrix = "\\mathdisp{\\begin{pmatrix}0&-1\\\\1&0\\end{pmatrix}}{.}"
    corrected_matrix = "\\mathdisp{\\begin{pmatrix}0&1\\\\-1&0\\end{pmatrix}}{.}"
    require(wrong_matrix in ss, "authority supplied solution retains the sign-reversed matrix", checks)
    require(corrected_matrix in st, "Exercise 2 supplied solution contains the corrected matrix", checks)
    require(wrong_matrix not in st, "sign-reversed 2 by 2 matrix is absent from the target solution", checks)

    # Translation receipts bind whole source/target files to the protected-delta verifier.
    receipt_hashes: dict[str, str] = {}
    receipt_correction_union: set[str] = set()
    for name, expected in EXPECTED_RECEIPTS.items():
        path = ROOT / "qa/unit-06" / name
        require(path.is_file(), f"translation receipt exists: {name}", checks)
        receipt = load_json(path)
        require(receipt.get("status") == "pass" and receipt.get("failures") == [], f"translation receipt passes: {name}", checks)
        require(receipt.get("source") == expected["source"], f"translation receipt source matches: {name}", checks)
        require(receipt.get("target") == expected["target"], f"translation receipt target matches: {name}", checks)
        require(receipt.get("source_sha256") == sha256(ROOT / str(expected["source"])), f"translation receipt source hash matches: {name}", checks)
        require(receipt.get("target_sha256") == target_by_relative[str(expected["target"])], f"translation receipt target hash matches: {name}", checks)
        declared = set(receipt.get("declared_corrections") or [])
        expected_corrections = set(expected["corrections"])
        require(declared == expected_corrections, f"translation receipt correction set is exact: {name}", checks)
        receipt_checks = receipt.get("checks")
        require(isinstance(receipt_checks, dict) and receipt_checks and all(receipt_checks.values()), f"all translation receipt checks pass: {name}", checks)
        receipt_correction_union.update(declared)
        receipt_hashes[name] = sha256(path)
    require(receipt_correction_union == set(CORRECTION_IDS), "translation receipts cover exactly corrections 0054 through 0069", checks)

    manifest_hashes: dict[str, str] = {}
    manifest_correction_union: set[str] = set()
    found_manifest_names = {path.name for path in (ROOT / "00_control").glob("*06*_PROTECTED_CORRECTIONS.json")}
    require(found_manifest_names == set(EXPECTED_MANIFESTS), "Unit 6 protected-correction manifest inventory is exact", checks)
    for name, expected in EXPECTED_MANIFESTS.items():
        path = ROOT / "00_control" / name
        manifest = load_json(path)
        require(manifest.get("schema_version") == 1, f"manifest schema is version 1: {name}", checks)
        require(manifest.get("scope") == expected["scope"], f"manifest scope matches: {name}", checks)
        deltas = manifest.get("allowed_deltas")
        require(isinstance(deltas, list) and deltas, f"manifest has allowed deltas: {name}", checks)
        assert isinstance(deltas, list)
        declared: set[str] = set()
        for delta in deltas:
            require(isinstance(delta, dict), f"manifest delta is an object: {name}", checks)
            assert isinstance(delta, dict)
            ids = delta.get("correction_ids")
            require(isinstance(ids, list) and ids, f"manifest delta declares correction IDs: {name}", checks)
            assert isinstance(ids, list)
            declared.update(str(value) for value in ids)
            require(str(delta.get("surface", "")).startswith("profile:"), f"manifest delta surface is protected: {name}", checks)
            require(bool(re.fullmatch(r"[0-9a-f]{64}", str(delta.get("source_sha256", "")))), f"manifest source profile hash is valid: {name}", checks)
            require(bool(re.fullmatch(r"[0-9a-f]{64}", str(delta.get("target_sha256", "")))), f"manifest target profile hash is valid: {name}", checks)
        require(declared == set(expected["corrections"]), f"manifest correction set is exact: {name}", checks)
        manifest_correction_union.update(declared)
        manifest_hashes[name] = sha256(path)
    require(manifest_correction_union == set(CORRECTION_IDS), "protected manifests cover exactly corrections 0054 through 0069", checks)

    # Every relevant adverse-ledger row is checked field for field, not merely by ID.
    ledger_path = ROOT / "00_control/ADVERSE_LEDGER.csv"
    with ledger_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    ids = [row.get("id", "") for row in rows]
    require(len(ids) == len(set(ids)), "all adverse-ledger IDs are unique", checks)
    relevant_rows: dict[str, dict[str, str]] = {}
    for correction_id in CORRECTION_IDS:
        matching = [row for row in rows if row.get("id") == correction_id]
        require(len(matching) == 1, f"adverse ledger contains exactly one row for {correction_id}", checks)
        row = matching[0]
        expected_row = {"id": correction_id, **EXPECTED_LEDGER_ROWS[correction_id]}
        require(row == expected_row, f"adverse ledger row matches exactly: {correction_id}", checks)
        relevant_rows[correction_id] = row

    payload = {
        "schema_version": 1,
        "unit_id": "o011-brenner-u06",
        "status": "pass",
        "correction_ids": list(CORRECTION_IDS),
        "checks_passed": len(checks),
        "checks": checks,
        "authority_sha256": authority_hashes,
        "target_sha256": target_hashes,
        "translation_receipt_sha256": receipt_hashes,
        "protected_manifest_sha256": manifest_hashes,
        "adverse_ledger_sha256": sha256(ledger_path),
        "adverse_ledger_rows": relevant_rows,
        "exercise_topology": {
            "exercise_count": 18,
            "practice_count": 14,
            "graded_count": 4,
            "graded_point_markers": [2, 4, 4, 4],
            "graded_point_total": 14,
            "solution_bearing_indices": [2, 6, 9],
            "hint_fields_blank": True,
        },
        "media": {
            "occurrence_count": 1,
            "filename": "Parallel transport sphere2.svg",
            "sha256": authority_hashes["media"],
        },
    }
    OUTPUT.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps({"status": "pass", "checks": len(checks)}, separators=(",", ":"), sort_keys=True))


if __name__ == "__main__":
    main()
