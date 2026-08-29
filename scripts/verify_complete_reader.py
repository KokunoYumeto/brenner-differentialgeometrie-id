#!/usr/bin/env python3
"""Bounded deterministic structural QA for the O011 complete Indonesian reader."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any

import pypdf
from pypdf import PdfReader
from pypdf.generic import IndirectObject


ROOT = Path(__file__).resolve().parent.parent
PDF_REL = "output/pdf/geometri-diferensial-manifold-mulus-edisi-lengkap-id.pdf"
BUILD_REL = "qa/complete/build.json"
OUTPUT_REL = "qa/complete/pdf_structural_qa.json"
DRIVER_REL = "build/generated/complete-reader-driver.tex"
PREFIX_DRIVER_REL = "build/generated/through-unit-22-driver.tex"
MACRO_REL = "build/complete-exam-macros.id.tex"

PREFIX_FROZEN = {
    "driver": {
        "path": PREFIX_DRIVER_REL,
        "bytes": 17_431,
        "sha256": "7d04f2c5906c1ddf5e82a0e80dcaafa7a7d62f99f915f3b8643e5be1d8181716",
    },
    "pdf": {
        "path": "output/pdf/geometri-diferensial-manifold-mulus-hingga-unit-22-id.pdf",
        "bytes": 9_046_717,
        "sha256": "4e6c03dc8388a4c10c464d939d5a416ab035c52e3bd233212c78a40617e02cf7",
    },
    "build_receipt": {
        "path": "qa/unit-22/build.json",
        "bytes": 233_556,
        "sha256": "68aacdf979f81c432a62dd9cebf2d4bab8e017cc03cde60d60532aaa99e6312d",
    },
    "structural_qa": {
        "path": "qa/unit-22/pdf_structural_qa.json",
        "bytes": 478_620,
        "sha256": "f5e9ae47e09bd6759b32b5ae14d623f25c0fbb5feb51f1d21d42559291915159",
    },
}

CORE_SOLUTIONS = {
    23: [6, 13, 16, 17],
    24: [],
    25: [1, 7, 8, 11, 12, 14],
    26: [3, 6, 9],
    27: [4, 5, 9, 13],
    28: [2, 5],
    29: [2],
}
CORE_EXERCISE_COUNTS = {23: 30, 24: 15, 25: 25, 26: 16, 27: 23, 28: 7, 29: 3}
EXAM_OCCURRENCES = {1: 14, 2: 11, 3: 16, 4: 16, 5: 14, 6: 16, 7: 16, 8: 17, 9: 13, 10: 14}
REPAIR_EXAMS = [1, 3, 5, 7, 9, 10]
EXPECTED_A4 = (595.276, 841.89)
PREFIX_PAGE_COUNT = 345
EXPECTED_PDF_TITLE = "Geometri Diferensial dan Manifold Mulus Edisi Lengkap Bahasa Indonesia"
SCAFFOLDING_REPLACEMENTS = [
    (
        r"\title{Geometri Diferensial dan Manifold Mulus\\\large Pembaca kumulatif hingga Unit 22}",
        r"\title{Geometri Diferensial dan Manifold Mulus\\\large Edisi Lengkap Bahasa Indonesia}",
    ),
    (
        "Pembaca kumulatif ini menerjemahkan Kuliah 1--22 dan Lembar Kerja 1--22 dari kursus Holger Brenner di Wikiversity berbahasa Jerman. Teks sumber digunakan berdasarkan CC BY-SA 4.0. Terjemahan ini merupakan karya independen dan bukan edisi resmi atau dukungan dari penulis maupun Wikiversity. Setiap gambar mengikuti status hak atau lisensi berkasnya sendiri, yang dicatat pada daftar gambar dan manifest media.",
        "Pembaca lengkap ini menerjemahkan seluruh 29 Kuliah dan 29 Lembar Kerja dari kursus Holger Brenner di Wikiversity berbahasa Jerman. Selain inti terjemahan, edisi ini memuat sepuluh formulir ujian resmi beserta solusi sumber yang tersedia, serta dua jembatan dan enam perbaikan solusi yang ditulis khusus untuk edisi ini dan diberi label terpisah. Teks sumber digunakan berdasarkan CC BY-SA 4.0. Terjemahan ini merupakan karya independen dan bukan edisi resmi atau dukungan dari penulis maupun Wikiversity. Setiap gambar mengikuti status hak atau lisensi berkasnya sendiri, yang dicatat pada daftar gambar dan manifest media.",
    ),
    (
        "Sumber permanen dan hash revisi dicatat dalam berkas kontrol edisi ini. Rumus, urutan, latihan, penanda solusi, dan atribusi media dipertahankan; ID mesin hanya merupakan lapisan tambahan. Bagian solusi hanya memuat solusi yang benar-benar disediakan oleh sumber.",
        "Sumber permanen dan hash revisi dicatat dalam berkas kontrol edisi ini. Rumus, urutan, latihan, penanda solusi, dan atribusi media dipertahankan; ID mesin hanya merupakan lapisan tambahan. Solusi yang disediakan sumber dipisahkan secara eksplisit dari 38 butir solusi asli edisi ini.",
    ),
]


def identity(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    data = path.read_bytes()
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def add(blockers: list[str], condition: bool, message: str) -> None:
    if not condition:
        blockers.append(message)


def normalized(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    without_marks = "".join(char for char in decomposed if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", without_marks).strip()


def dereference(value: Any) -> Any:
    return value.get_object() if isinstance(value, IndirectObject) else value


def flatten_outline(items: list[Any]) -> list[str]:
    result: list[str] = []
    for item in items:
        if isinstance(item, list):
            result.extend(flatten_outline(item))
        else:
            title = getattr(item, "title", None)
            if title is not None:
                result.append(str(title))
    return result


def source_target_hash(receipt: dict[str, Any]) -> str | None:
    direct = receipt.get("target_sha256")
    if direct:
        return str(direct).lower()
    target = receipt.get("target")
    if isinstance(target, dict) and target.get("sha256"):
        return str(target["sha256"]).lower()
    return None


def verify_prefix_and_driver(blockers: list[str]) -> dict[str, Any]:
    frozen_checks: list[dict[str, Any]] = []
    for label, expected in PREFIX_FROZEN.items():
        actual = identity(ROOT / expected["path"])
        passed = actual == {"bytes": expected["bytes"], "sha256": expected["sha256"]}
        frozen_checks.append(
            {"label": label, "path": expected["path"], "expected": expected, "actual": actual, "passed": passed}
        )
        add(blockers, passed, f"frozen Unit 22 public-prefix artifact changed: {label}")

    prefix_path = ROOT / PREFIX_DRIVER_REL
    driver_path = ROOT / DRIVER_REL
    prefix_bytes = prefix_path.read_bytes() if prefix_path.is_file() else b""
    driver_bytes = driver_path.read_bytes() if driver_path.is_file() else b""
    marker = b"\\backmatter"
    add(blockers, prefix_bytes.count(marker) == 1, "frozen Unit 22 driver lacks a unique backmatter marker")
    marker_index = prefix_bytes.find(marker)
    prefix_head = prefix_bytes[:marker_index] if marker_index >= 0 else b""
    prefix_head_text = prefix_head.decode("utf-8", errors="strict") if prefix_head else ""
    expected_prefix_text = prefix_head_text
    replacement_rows: list[dict[str, Any]] = []
    for old, new in SCAFFOLDING_REPLACEMENTS:
        count = expected_prefix_text.count(old)
        add(blockers, count == 1, f"frozen prefix scaffolding occurrence mismatch ({count}): {old[:48]}")
        expected_prefix_text = expected_prefix_text.replace(old, new, 1)
        replacement_rows.append({"source_occurrences": count, "source": old, "target": new})
    expected_prefix = expected_prefix_text.encode("utf-8")
    controlled_prefix_equal = bool(expected_prefix and driver_bytes.startswith(expected_prefix))
    add(
        blockers,
        controlled_prefix_equal,
        "complete driver differs outside the three exact complete-edition scaffolding substitutions",
    )
    restored_prefix_text = expected_prefix_text
    for old, new in SCAFFOLDING_REPLACEMENTS:
        restored_prefix_text = restored_prefix_text.replace(new, old, 1)
    exactly_reversible = restored_prefix_text == prefix_head_text
    add(blockers, exactly_reversible, "complete-edition prefix substitutions are not exactly reversible")

    driver = driver_bytes.decode("utf-8", errors="replace")
    add(blockers, "\ufffd" not in driver, "complete driver is not valid UTF-8")
    add(
        blockers,
        driver.count(r"\usepackage[a4paper,margin=22mm,headheight=15pt]{geometry}") == 1,
        "complete driver lost the unique centered A4/22mm geometry declaration",
    )
    add(blockers, driver.count("% O011-COMPLETE-EXTENSION-BEGIN") == 1, "missing/duplicate extension begin marker")
    add(blockers, driver.count("% O011-COMPLETE-EXTENSION-END") == 1, "missing/duplicate extension end marker")

    expected_inputs: list[str] = []
    for unit in range(23, 30):
        expected_inputs.extend(
            [
                f"generated/lecture{unit:02d}.id.build.tex",
                f"generated/worksheet{unit:02d}.id.build.tex",
            ]
        )
        expected_inputs.extend(
            f"generated/worksheet{unit:02d}_exercise{exercise:02d}_solution.id.build.tex"
            for exercise in CORE_SOLUTIONS[unit]
        )
    expected_inputs.extend(
        [
            "generated/bridges/bridge-lie-theory.build.tex",
            "generated/bridges/bridge-lie-assessment.build.tex",
            "generated/bridges/bridge-de-rham-theory.build.tex",
            "generated/bridges/bridge-de-rham-assessment.build.tex",
            "complete-exam-macros.id.tex",
        ]
    )
    expected_inputs.extend(f"generated/exams/exam{exam:02d}_learner.id.build.tex" for exam in range(1, 11))
    expected_inputs.extend(f"generated/exams/exam{exam:02d}_solutions.id.build.tex" for exam in range(1, 11))
    expected_inputs.append("generated/bridges/missing-exam-solutions.build.tex")
    positions: list[int] = []
    for rel in expected_inputs:
        token = rf"\input{{{rel}}}"
        count = driver.count(token)
        add(blockers, count == 1, f"complete driver input occurrence mismatch ({count}): {rel}")
        positions.append(driver.find(token))
    ordered_inputs = all(left < right for left, right in zip(positions, positions[1:]))
    add(blockers, ordered_inputs, "complete driver surfaces are not in the required order")

    attribution_positions: list[int] = []
    for unit in range(22, 30):
        suffix = "cumulative" if unit == 22 else "complete"
        token = rf"\input{{generated/unit{unit:02d}-media-attribution-{suffix}.tex}}"
        add(blockers, driver.count(token) == 1, f"Unit {unit} media attribution input mismatch")
        attribution_positions.append(driver.find(token))
    attribution_ordered = all(left < right for left, right in zip(attribution_positions, attribution_positions[1:]))
    add(blockers, attribution_ordered, "Unit 22--29 media attributions are not ordered")

    provenance_phrases = [
        "Catatan provenans bagian tambahan",
        "Jembatan Asli",
        "Formulir Peserta Ujian 1",
        "Formulir Solusi Resmi Ujian 1",
        "Perbaikan Asli yang Terpisah",
        "bukan bagian dari sumber Brenner/Wikiversity",
    ]
    provenance = {phrase: driver.count(phrase) for phrase in provenance_phrases}
    for phrase, count in provenance.items():
        add(blockers, count >= 1, f"missing driver provenance label: {phrase}")

    prepare_script = (ROOT / "scripts/prepare_unit_tex.py").read_text(encoding="utf-8")
    lie_delimiter_fix = (
        "Do not reject raw ``[[``/``]]`` unconditionally" in prepare_script
        and "RESIDUAL_MEDIAWIKI_LINK_RE.search(text)" in prepare_script
    )
    add(blockers, lie_delimiter_fix, "prepare_unit_tex Lie-bracket delimiter fix is absent")

    macro_path = ROOT / MACRO_REL
    macro = macro_path.read_text(encoding="utf-8") if macro_path.is_file() else ""
    required_macro_prose = ["Bidang studi", "Nomor mahasiswa", "Solusi:", "poin", "Diperoleh", "Tanda tangan"]
    macro_localization = {phrase: phrase in macro for phrase in required_macro_prose}
    for phrase, present in macro_localization.items():
        add(blockers, present, f"exam reader macro lacks Indonesian text: {phrase}")
    german_macro_literals = ["Lösung", "Punkte", "Aufgabe", "mögliche Pkt.", "Name, Vorname", "Matrikelnummer", "Unterschrift"]
    german_hits = [token for token in german_macro_literals if token in macro]
    add(blockers, not german_hits, f"German reader literals remain in exam macro overlay: {german_hits}")

    return {
        "frozen_artifacts": frozen_checks,
        "preserved_prefix": {
            "frozen": {
                "bytes": len(prefix_head),
                "sha256": hashlib.sha256(prefix_head).hexdigest() if prefix_head else None,
            },
            "derived": {
                "bytes": len(expected_prefix),
                "sha256": hashlib.sha256(expected_prefix).hexdigest() if expected_prefix else None,
            },
            "byte_identical": False,
            "controlled_replacement_count": len(SCAFFOLDING_REPLACEMENTS),
            "replacements": replacement_rows,
            "exactly_reversible": exactly_reversible,
            "controlled_prefix_equal": controlled_prefix_equal,
            "boundary": "before unique backmatter command, except exact complete-edition scaffolding substitutions",
        },
        "driver": identity(driver_path),
        "required_extension_input_count": len(expected_inputs),
        "required_extension_inputs_ordered": ordered_inputs,
        "media_attribution_ordered": attribution_ordered,
        "provenance_phrase_counts": provenance,
        "prepare_unit_tex_lie_delimiter_fix_present": lie_delimiter_fix,
        "exam_macro_localization": macro_localization,
        "exam_macro_german_literal_hits": german_hits,
    }


def verify_source_closure(blockers: list[str]) -> dict[str, Any]:
    core_rows: list[dict[str, Any]] = []
    exercise_pattern = re.compile(r"\\inputaufgabe(?:gibtloesung)?\s*\{")
    for unit in range(23, 30):
        unit_dir = ROOT / f"source/units/unit-{unit:02d}"
        worksheet = unit_dir / f"worksheet{unit:02d}.id.tex"
        text = worksheet.read_text(encoding="utf-8")
        exercise_count = len(exercise_pattern.findall(text))
        solution_files = sorted(unit_dir.glob(f"worksheet{unit:02d}_exercise*_solution.id.tex"))
        actual_solutions = [
            int(re.search(r"exercise(\d+)_solution", path.name).group(1))  # type: ignore[union-attr]
            for path in solution_files
        ]
        passed = exercise_count == CORE_EXERCISE_COUNTS[unit] and actual_solutions == CORE_SOLUTIONS[unit]
        add(blockers, passed, f"Unit {unit} exercise/source-solution closure mismatch")
        core_rows.append(
            {
                "unit": unit,
                "exercise_count": exercise_count,
                "expected_exercise_count": CORE_EXERCISE_COUNTS[unit],
                "source_supplied_solution_numbers": actual_solutions,
                "expected_solution_numbers": CORE_SOLUTIONS[unit],
                "passed": passed,
            }
        )

    exam_rows: list[dict[str, Any]] = []
    learner_pattern = re.compile(r"\\inputaufgabe(?:gibtloesung)?\s*\{")
    official_pattern = re.compile(r"\\inputaufgabeklausurloesung\s*\{")
    for exam in range(1, 11):
        digits = f"{exam:02d}"
        learner_path = ROOT / f"source/exams/exam-{digits}/exam{digits}_learner.id.tex"
        official_path = ROOT / f"source/exams/exam-{digits}/exam{digits}_solutions.id.tex"
        learner_count = len(learner_pattern.findall(learner_path.read_text(encoding="utf-8")))
        official_count = len(official_pattern.findall(official_path.read_text(encoding="utf-8")))
        source_id = identity(official_path)
        translation_path = ROOT / f"qa/exams/EXAM{digits}_SOLUTIONS_TRANSLATION_QA.json"
        bounded_path = ROOT / f"qa/exams/EXAM{digits}_SOLUTIONS_BOUNDED_QA.json"
        translation = load_json(translation_path) if translation_path.is_file() else {}
        bounded = load_json(bounded_path) if bounded_path.is_file() else {}
        translation_pass = translation.get("status") == "pass" or translation.get("passed") is True
        bounded_pass = bounded.get("status") == "pass" or bounded.get("passed") is True
        translation_bound = bool(source_id and translation.get("target_sha256") == source_id["sha256"])
        bounded_hash = source_target_hash(bounded)
        bounded_bound = bounded_hash is None or bool(source_id and bounded_hash == source_id["sha256"])
        passed = bool(
            learner_count == EXAM_OCCURRENCES[exam]
            and official_count == EXAM_OCCURRENCES[exam]
            and translation_pass
            and bounded_pass
            and translation_bound
            and bounded_bound
        )
        add(blockers, passed, f"Exam {exam} form/QA closure mismatch")
        exam_rows.append(
            {
                "exam": exam,
                "learner_occurrences": learner_count,
                "official_solution_form_occurrences": official_count,
                "expected_occurrences": EXAM_OCCURRENCES[exam],
                "exact_translation_qa_passed_and_bound": translation_pass and translation_bound,
                "bounded_qa_passed_and_bound": bounded_pass and bounded_bound,
                "official_solution_identity": source_id,
                "passed": passed,
            }
        )

    repairs_path = ROOT / "source/exams/original-repairs/missing-exam-solutions.id.tex"
    repairs = repairs_path.read_text(encoding="utf-8")
    repair_ids = [int(value) for value in re.findall(r"O011-EXAM(\d{2})-ORIG-SOL-01", repairs)]
    unique_repairs = sorted(set(repair_ids))
    repair_subsections = len(re.findall(r"\\subsection\*\{Ujian \d+, soal tanpa solusi sumber", repairs))
    repair_pass = unique_repairs == REPAIR_EXAMS and repair_subsections == 6
    add(blockers, repair_pass, "original missing-exam repair closure is not exactly six labelled solutions")

    return {
        "core_units": core_rows,
        "exam_forms": exam_rows,
        "original_repairs": {
            "expected_exams": REPAIR_EXAMS,
            "observed_unique_exam_ids": unique_repairs,
            "subsection_count": repair_subsections,
            "passed": repair_pass,
        },
    }


def verify_build_receipt(blockers: list[str]) -> dict[str, Any]:
    build_path = ROOT / BUILD_REL
    if not build_path.is_file():
        blockers.append(f"missing build receipt: {BUILD_REL}")
        return {"receipt": None}
    data = load_json(build_path)
    add(blockers, data.get("workflow") == "o011-complete-reader-pdf-build-v1", "wrong complete-reader build workflow")
    add(blockers, data.get("deterministic_clean_cycles") is True, "build does not assert deterministic clean cycles")
    add(
        blockers,
        data.get("geometry") == {"paper": "A4", "margin": "22mm", "centered": True, "class_option": "oneside"},
        "build receipt geometry contract mismatch",
    )
    output = data.get("output", {})
    actual_pdf = identity(ROOT / PDF_REL)
    output_bound = bool(
        output.get("path") == PDF_REL
        and actual_pdf == {"bytes": output.get("bytes"), "sha256": output.get("sha256")}
    )
    add(blockers, output_bound, "build output receipt is not bound to the installed PDF")

    cycles = data.get("cycles", [])
    cycle_rows: list[dict[str, Any]] = []
    add(blockers, len(cycles) == 2, f"expected two build cycles, found {len(cycles)}")
    for expected_number, row in enumerate(cycles, start=1):
        declared = row.get("identity", {})
        actual = identity(ROOT / str(row.get("pdf", "")))
        passed = bool(
            row.get("cycle") == expected_number
            and declared == actual
            and actual == actual_pdf
        )
        add(blockers, passed, f"clean cycle {expected_number} is not byte-identical to installed output")
        cycle_rows.append(
            {"cycle": expected_number, "path": row.get("pdf"), "declared": declared, "actual": actual, "passed": passed}
        )

    input_rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in data.get("inputs", []):
        rel = str(row.get("path", ""))
        candidate = (ROOT / rel).resolve()
        within = candidate != ROOT and ROOT in candidate.parents
        actual = identity(candidate) if within else None
        declared = {"bytes": row.get("bytes"), "sha256": row.get("sha256")}
        unique = rel not in seen
        passed = within and unique and actual == declared
        add(blockers, passed, f"declared build input changed or is unsafe/duplicated: {rel}")
        input_rows.append({"path": rel, "declared": declared, "actual": actual, "unique": unique, "passed": passed})
        seen.add(rel)

    required_inputs = {
        "scripts/build_complete_reader.ps1",
        "scripts/verify_complete_reader.py",
        "scripts/prepare_unit_tex.py",
        DRIVER_REL,
        PREFIX_DRIVER_REL,
        MACRO_REL,
        "build/brenner-compat.tex",
        "source/exams/original-repairs/missing-exam-solutions.id.tex",
        "build/generated/bridges/missing-exam-solutions.build.tex",
    }
    for exam in range(1, 11):
        digits = f"{exam:02d}"
        required_inputs.update(
            {
                f"source/exams/exam-{digits}/exam{digits}_learner.id.tex",
                f"source/exams/exam-{digits}/exam{digits}_solutions.id.tex",
                f"build/generated/exams/exam{digits}_learner.id.build.tex",
                f"build/generated/exams/exam{digits}_solutions.id.build.tex",
                f"qa/exams/EXAM{digits}_SOLUTIONS_TRANSLATION_QA.json",
                f"qa/exams/EXAM{digits}_SOLUTIONS_BOUNDED_QA.json",
            }
        )
    for unit in range(23, 30):
        required_inputs.update(
            {
                f"source/units/unit-{unit:02d}/lecture{unit:02d}.id.tex",
                f"source/units/unit-{unit:02d}/worksheet{unit:02d}.id.tex",
                f"build/generated/lecture{unit:02d}.id.build.tex",
                f"build/generated/worksheet{unit:02d}.id.build.tex",
                f"build/generated/unit{unit:02d}-media-attribution-complete.tex",
                f"qa/complete/cumulative-media/unit-{unit:02d}_media.json",
            }
        )
        for exercise in CORE_SOLUTIONS[unit]:
            required_inputs.update(
                {
                    f"source/units/unit-{unit:02d}/worksheet{unit:02d}_exercise{exercise:02d}_solution.id.tex",
                    f"build/generated/worksheet{unit:02d}_exercise{exercise:02d}_solution.id.build.tex",
                }
            )
    missing_declared = sorted(required_inputs - seen)
    add(blockers, not missing_declared, f"required build inputs are undeclared: {missing_declared}")

    return {
        "receipt": identity(build_path),
        "output": {"declared": output, "actual": actual_pdf, "passed": output_bound},
        "cycles": cycle_rows,
        "declared_input_count": len(input_rows),
        "inputs": input_rows,
        "required_inputs_missing": missing_declared,
    }


def verify_pdf(blockers: list[str]) -> dict[str, Any]:
    pdf_path = ROOT / PDF_REL
    if not pdf_path.is_file():
        blockers.append(f"missing complete PDF: {PDF_REL}")
        return {"identity": None}

    reader = PdfReader(str(pdf_path), strict=False)
    page_count = len(reader.pages)
    add(blockers, page_count > PREFIX_PAGE_COUNT, f"complete PDF has only {page_count} pages; it does not extend Unit 22")

    geometry_failures: list[dict[str, Any]] = []
    rotations: Counter[int] = Counter()
    for index, page in enumerate(reader.pages, start=1):
        media = page.mediabox
        crop = page.cropbox
        media_width = float(media.right) - float(media.left)
        media_height = float(media.top) - float(media.bottom)
        crop_width = float(crop.right) - float(crop.left)
        crop_height = float(crop.top) - float(crop.bottom)
        rotation = int(page.get("/Rotate", 0) or 0) % 360
        rotations[rotation] += 1
        passed = bool(
            abs(media_width - EXPECTED_A4[0]) <= 0.15
            and abs(media_height - EXPECTED_A4[1]) <= 0.15
            and abs(crop_width - media_width) <= 0.15
            and abs(crop_height - media_height) <= 0.15
            and rotation == 0
        )
        if not passed:
            geometry_failures.append(
                {
                    "page": index,
                    "media": [media_width, media_height],
                    "crop": [crop_width, crop_height],
                    "rotation": rotation,
                }
            )
    add(blockers, not geometry_failures, f"non-centered-A4 page geometry found on {len(geometry_failures)} pages")

    page_texts: list[str] = []
    extraction_errors: list[dict[str, Any]] = []
    for index, page in enumerate(reader.pages, start=1):
        try:
            page_texts.append(page.extract_text() or "")
        except Exception as exc:  # pragma: no cover - evidence path
            page_texts.append("")
            extraction_errors.append({"page": index, "error": str(exc)})
    add(blockers, not extraction_errors, f"text extraction failed on {len(extraction_errors)} pages")
    text = "\n".join(page_texts)
    normalized_text = normalized(text)

    visible_complete_scope = {
        "complete title": normalized("Edisi Lengkap Bahasa Indonesia") in normalized(page_texts[0]),
        "29-lecture and 29-worksheet scope": normalized("seluruh 29 Kuliah dan 29 Lembar Kerja") in normalized("\n".join(page_texts[:2])),
        "38 original solution items distinguished": normalized("38 butir solusi asli edisi ini") in normalized("\n".join(page_texts[:2])),
    }
    for label, present in visible_complete_scope.items():
        add(blockers, present, f"complete-edition frontmatter is missing: {label}")
    stale_complete_scaffolding = [
        phrase
        for phrase in ("Pembaca kumulatif hingga Unit 22", "Pembaca kumulatif ini menerjemahkan Kuliah 1")
        if normalized(phrase) in normalized("\n".join(page_texts[:2]))
    ]
    add(blockers, not stale_complete_scaffolding, f"stale Unit 22 scaffolding remains: {stale_complete_scaffolding}")

    sentinels = ["Solusi Soal 22.6", "Kelanjutan Edisi Lengkap"]
    sentinels.extend(f"Unit {unit}" for unit in range(23, 30))
    sentinels.extend(
        [
            "Jembatan Asli",
            "Jembatan Grup Lie dan Aljabar Lie",
            "Jembatan Kohomologi de Rham dan Topologi Diferensial",
            "Formulir Ujian",
        ]
    )
    sentinels.extend(f"Formulir Peserta Ujian {exam}" for exam in range(1, 11))
    sentinels.append("Formulir Solusi Resmi")
    sentinels.extend(f"Formulir Solusi Resmi Ujian {exam}" for exam in range(1, 11))
    sentinels.extend(
        [
            "Perbaikan Asli yang Terpisah",
            "Enam solusi asli untuk kekosongan sumber",
            "Atribusi dan Hak Media",
            "Lisensi",
        ]
    )
    cursor = 0
    sentinel_rows: list[dict[str, Any]] = []
    for sentinel in sentinels:
        needle = normalized(sentinel)
        position = normalized_text.find(needle, cursor)
        passed = position >= cursor
        sentinel_rows.append({"text": sentinel, "position": position, "passed": passed})
        add(blockers, passed, f"missing/out-of-order PDF sentinel: {sentinel}")
        if passed:
            cursor = position + len(needle)

    required_reader_prose = [
        "Materi asli edisi ini",
        "kekosongan sumber dipertahankan",
        "bukan bagian dari sumber Brenner/Wikiversity",
        "Nomor mahasiswa",
        "Diperoleh",
        "Solusi:",
    ]
    reader_prose = {phrase: normalized(phrase) in normalized_text for phrase in required_reader_prose}
    for phrase, present in reader_prose.items():
        add(blockers, present, f"required Indonesian reader-facing prose absent from PDF: {phrase}")

    german_exam_patterns = {
        "German solution heading": re.compile(r"\bL.sung\s*:", re.IGNORECASE),
        "German points header": re.compile(r"m.gliche\s+Pkt", re.IGNORECASE),
        "German received-points header": re.compile(r"erhaltene\s+Pkt", re.IGNORECASE),
        "German student-number label": re.compile(r"Matrikelnummer\s*:", re.IGNORECASE),
        "German grade label": re.compile(r"\bNote\s*:", re.IGNORECASE),
    }
    german_hits = {
        label: pattern.findall(normalized_text)[:10]
        for label, pattern in german_exam_patterns.items()
        if pattern.search(normalized_text)
    }
    add(blockers, not german_hits, f"German exam reader-surface residue remains in PDF: {sorted(german_hits)}")

    bookmarks = flatten_outline(reader.outline)
    normalized_bookmarks = [normalized(title) for title in bookmarks]
    expected_bookmarks = [
        "Kelanjutan Edisi Lengkap",
        "Unit 23",
        "Unit 29",
        "Jembatan Asli",
        "Formulir Ujian",
        "Formulir Solusi Resmi",
        "Perbaikan Asli yang Terpisah",
        "Atribusi dan Hak Media",
    ]
    bookmark_presence = {
        title: any(normalized(title) in bookmark for bookmark in normalized_bookmarks)
        for title in expected_bookmarks
    }
    for title, present in bookmark_presence.items():
        add(blockers, present, f"required PDF bookmark absent: {title}")

    subtype_counts: Counter[str] = Counter()
    uri_counts: Counter[str] = Counter()
    unsafe_actions: list[dict[str, Any]] = []
    unsafe_action_types = {"/Launch", "/JavaScript", "/SubmitForm", "/ImportData", "/GoToR"}
    unsafe_subtypes = {"/FileAttachment", "/Movie", "/Sound", "/RichMedia", "/Screen"}
    for page_number, page in enumerate(reader.pages, start=1):
        annotations = dereference(page.get("/Annots", [])) or []
        for annotation_ref in annotations:
            annotation = dereference(annotation_ref)
            subtype = str(annotation.get("/Subtype", ""))
            subtype_counts[subtype] += 1
            if subtype in unsafe_subtypes:
                unsafe_actions.append({"page": page_number, "subtype": subtype})
            action = dereference(annotation.get("/A")) if annotation.get("/A") is not None else None
            if action is not None:
                action_type = str(action.get("/S", ""))
                if action_type == "/URI":
                    uri_counts[str(action.get("/URI", ""))] += 1
                if action_type in unsafe_action_types:
                    unsafe_actions.append({"page": page_number, "subtype": subtype, "action": action_type})
    root = dereference(reader.trailer.get("/Root"))
    names = dereference(root.get("/Names")) if root is not None and root.get("/Names") is not None else None
    embedded_files = bool(names and names.get("/EmbeddedFiles"))
    javascript_tree = bool(names and names.get("/JavaScript"))
    acroform = bool(root and root.get("/AcroForm"))
    add(blockers, not unsafe_actions, f"unsafe PDF annotation/action present: {unsafe_actions[:5]}")
    add(blockers, not embedded_files, "PDF contains an embedded-files name tree")
    add(blockers, not javascript_tree, "PDF contains a JavaScript name tree")
    add(blockers, not acroform, "PDF contains an AcroForm")

    metadata = {str(key): str(value) for key, value in (reader.metadata or {}).items()}
    metadata_title = normalized(metadata.get("/Title", ""))
    expected_metadata_title = normalized(EXPECTED_PDF_TITLE)
    add(
        blockers,
        metadata_title == expected_metadata_title,
        f"PDF /Title mismatch: {metadata.get('/Title')!r}",
    )
    sensitive = re.compile(r"(?:New zenodo token|Github Tokens|Zenodo token|Figshare Token)", re.IGNORECASE)
    sensitive_hits = [value for value in [text, *metadata.values()] if sensitive.search(value)]
    add(blockers, not sensitive_hits, "sensitive credential filename leaked into PDF")

    log_path = ROOT / "build/complete-work/complete-reader.log"
    log_text = log_path.read_text(encoding="utf-8", errors="replace") if log_path.is_file() else ""
    fatal_log_hits = [
        token for token in ("! LaTeX Error", "Emergency stop", "Fatal error occurred") if token in log_text
    ]
    add(blockers, not fatal_log_hits, f"fatal TeX diagnostics remain in final log: {fatal_log_hits}")
    overfull = [float(value) for value in re.findall(r"Overfull \\hbox \(([0-9.]+)pt too wide\)", log_text)]

    return {
        "identity": identity(pdf_path),
        "pypdf_version": pypdf.__version__,
        "page_count": page_count,
        "prefix_page_count": PREFIX_PAGE_COUNT,
        "all_pages_a4_centered_boxes": not geometry_failures,
        "geometry_failures": geometry_failures,
        "rotations": dict(sorted(rotations.items())),
        "pages_with_extractable_text": sum(bool(text.strip()) for text in page_texts),
        "text_extraction_errors": extraction_errors,
        "ordered_sentinels": sentinel_rows,
        "required_reader_prose": reader_prose,
        "german_exam_surface_hits": german_hits,
        "bookmark_count": len(bookmarks),
        "required_bookmark_presence": bookmark_presence,
        "annotation_subtype_counts": dict(sorted(subtype_counts.items())),
        "external_uri_count": sum(uri_counts.values()),
        "external_uri_counts": dict(sorted(uri_counts.items())),
        "unsafe_actions": unsafe_actions,
        "embedded_files_name_tree": embedded_files,
        "javascript_name_tree": javascript_tree,
        "acroform": acroform,
        "metadata": metadata,
        "metadata_title_expected": EXPECTED_PDF_TITLE,
        "metadata_title_passed": metadata_title == expected_metadata_title,
        "visible_complete_scope": visible_complete_scope,
        "stale_complete_scaffolding": stale_complete_scaffolding,
        "fatal_log_hits": fatal_log_hits,
        "overfull_hbox_count": len(overfull),
        "maximum_overfull_hbox_points": max(overfull, default=0.0),
    }


def main() -> int:
    blockers: list[str] = []
    prefix_driver = verify_prefix_and_driver(blockers)
    source_closure = verify_source_closure(blockers)
    build = verify_build_receipt(blockers)
    pdf = verify_pdf(blockers)
    status = "pass" if not blockers else "fail"
    receipt = {
        "schema_version": 1,
        "workflow": "o011-complete-reader-structural-qa-v1",
        "status": status,
        "scope": "exact Unit 22 public-prefix preservation, complete-surface ordering and provenance, source closure, deterministic PDF identity, centered A4 geometry, reader-facing Indonesian exam labels, links, and active-content safety",
        "prefix_and_driver": prefix_driver,
        "source_closure": source_closure,
        "build": build,
        "pdf": pdf,
        "blockers": blockers,
    }
    output = ROOT / OUTPUT_REL
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(receipt, ensure_ascii=True, indent=2, sort_keys=True))
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
