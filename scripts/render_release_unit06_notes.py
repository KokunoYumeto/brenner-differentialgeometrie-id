#!/usr/bin/env python3
"""Bind the Unit 6 release notes to the settled PDF and backend identities."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


TOKENS = (
    "PDF_BYTES",
    "PDF_SHA256",
    "PDF_PAGES",
    "LECTURE_SHA256",
    "BUILD_RECEIPT_SHA256",
    "MATH_QA_SHA256",
    "STRUCTURAL_QA_SHA256",
    "BACKEND_RECORDS",
    "BACKEND_JSONL_BYTES",
    "BACKEND_JSONL_SHA256",
    "BACKEND_CSV_BYTES",
    "BACKEND_CSV_SHA256",
    "BACKEND_MANIFEST_BYTES",
    "BACKEND_MANIFEST_SHA256",
    "BACKEND_QA_SHA256",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def identity(path: Path) -> dict[str, int | str]:
    return {"bytes": path.stat().st_size, "sha256": sha256(path)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--expected-pdf-bytes", type=int, required=True)
    parser.add_argument("--expected-pdf-sha256", required=True)
    parser.add_argument("--expected-pages", type=int, required=True)
    parser.add_argument("--expected-lecture-sha256", required=True)
    parser.add_argument("--expected-build-receipt-sha256", required=True)
    parser.add_argument("--expected-math-qa-sha256", required=True)
    parser.add_argument("--expected-structural-qa-sha256", required=True)
    parser.add_argument("--expected-backend-records", type=int, required=True)
    parser.add_argument("--expected-backend-qa-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    root = args.root.resolve()
    output = (root / args.output).resolve()
    if output.exists():
        raise SystemExit(f"refusing to overwrite rendered release notes: {output}")
    template_path = root / "qa/unit-06/RELEASE_NOTES_TEMPLATE_20260822.md"
    pdf = root / "output/pdf/geometri-diferensial-manifold-mulus-hingga-unit-06-id.pdf"
    pdf_identity = identity(pdf)
    expected_pdf = {
        "bytes": args.expected_pdf_bytes,
        "sha256": args.expected_pdf_sha256.lower(),
    }
    if pdf_identity != expected_pdf:
        raise SystemExit(f"settled PDF identity mismatch: {pdf_identity}")

    pdf_qa = json.loads((root / "qa/unit-06/pdf_structural_qa.json").read_text(encoding="utf-8"))
    structural_qa_path = root / "qa/unit-06/pdf_structural_qa.json"
    structural_qa_sha256 = sha256(structural_qa_path)
    if structural_qa_sha256 != args.expected_structural_qa_sha256.lower():
        raise SystemExit("final structural-QA identity mismatch")
    if not pdf_qa.get("passed") or pdf_qa.get("pdf", {}).get("pages") != args.expected_pages:
        raise SystemExit("settled PDF QA/page binding mismatch")
    if {
        "bytes": pdf_qa["pdf"]["bytes"],
        "sha256": pdf_qa["pdf"]["sha256"],
    } != expected_pdf:
        raise SystemExit("settled PDF QA identity mismatch")

    lecture = root / "source/units/unit-06/lecture06.id.tex"
    build_receipt_path = root / "qa/unit-06/build.json"
    math_qa_path = root / "qa/unit-06/POST_REPAIR_MATH_QA.json"
    lecture_sha256 = sha256(lecture)
    build_receipt_sha256 = sha256(build_receipt_path)
    math_qa_sha256 = sha256(math_qa_path)
    if lecture_sha256 != args.expected_lecture_sha256.lower():
        raise SystemExit("final Lecture 6 source identity mismatch")
    if build_receipt_sha256 != args.expected_build_receipt_sha256.lower():
        raise SystemExit("final build-receipt identity mismatch")
    if math_qa_sha256 != args.expected_math_qa_sha256.lower():
        raise SystemExit("final post-repair math-QA identity mismatch")
    math_qa = json.loads(math_qa_path.read_text(encoding="utf-8"))
    if math_qa.get("status") != "pass":
        raise SystemExit("final post-repair math QA is not passing")

    backend_manifest_path = root / "backend/MANIFEST.json"
    backend_manifest = json.loads(backend_manifest_path.read_text(encoding="utf-8"))
    if backend_manifest.get("combined", {}).get("record_count") != args.expected_backend_records:
        raise SystemExit("backend record-count binding mismatch")
    backend_qa = json.loads((root / "qa/unit-06/backend.json").read_text(encoding="utf-8"))
    backend_qa_path = root / "qa/unit-06/backend.json"
    backend_qa_sha256 = sha256(backend_qa_path)
    if backend_qa_sha256 != args.expected_backend_qa_sha256.lower():
        raise SystemExit("final backend-QA identity mismatch")
    if backend_qa.get("status") != "pass" or backend_qa.get("combined_records") != args.expected_backend_records:
        raise SystemExit("backend QA binding mismatch")

    jsonl = identity(root / "backend/records.jsonl")
    csv = identity(root / "backend/records.csv")
    manifest_identity = identity(backend_manifest_path)
    declared = backend_manifest.get("outputs", {})
    if declared.get("records_jsonl") != {
        "path": "backend/records.jsonl",
        **jsonl,
    }:
        raise SystemExit("backend JSONL manifest binding mismatch")
    if declared.get("records_csv") != {
        "path": "backend/records.csv",
        **csv,
    }:
        raise SystemExit("backend CSV manifest binding mismatch")

    replacements = {
        "PDF_BYTES": str(pdf_identity["bytes"]),
        "PDF_SHA256": str(pdf_identity["sha256"]),
        "PDF_PAGES": str(args.expected_pages),
        "LECTURE_SHA256": lecture_sha256,
        "BUILD_RECEIPT_SHA256": build_receipt_sha256,
        "MATH_QA_SHA256": math_qa_sha256,
        "STRUCTURAL_QA_SHA256": structural_qa_sha256,
        "BACKEND_RECORDS": str(args.expected_backend_records),
        "BACKEND_JSONL_BYTES": str(jsonl["bytes"]),
        "BACKEND_JSONL_SHA256": str(jsonl["sha256"]),
        "BACKEND_CSV_BYTES": str(csv["bytes"]),
        "BACKEND_CSV_SHA256": str(csv["sha256"]),
        "BACKEND_MANIFEST_BYTES": str(manifest_identity["bytes"]),
        "BACKEND_MANIFEST_SHA256": str(manifest_identity["sha256"]),
        "BACKEND_QA_SHA256": backend_qa_sha256,
    }
    text = template_path.read_text(encoding="utf-8")
    for name, value in replacements.items():
        marker = "{{" + name + "}}"
        if text.count(marker) == 0:
            raise SystemExit(f"release-note template marker missing: {marker}")
        text = text.replace(marker, value)
    unresolved = [name for name in TOKENS if "{{" + name + "}}" in text]
    if unresolved or "{{" in text or "}}" in text:
        raise SystemExit(f"unresolved release-note template markers: {unresolved}")
    if "OpenAI Codex gpt-5.6-sol, Ultra" not in text:
        raise SystemExit("exact model identification missing from rendered release notes")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8", newline="\n")
    try:
        output_label = output.relative_to(root).as_posix()
    except ValueError:
        output_label = output.name
    print(
        json.dumps(
            {
                "status": "pass",
                "output": output_label,
                "bytes": output.stat().st_size,
                "sha256": sha256(output),
                "pdf": pdf_identity,
                "pages": args.expected_pages,
                "lecture_sha256": lecture_sha256,
                "build_receipt_sha256": build_receipt_sha256,
                "math_qa_sha256": math_qa_sha256,
                "structural_qa_sha256": structural_qa_sha256,
                "backend_records": args.expected_backend_records,
                "backend_qa_sha256": backend_qa_sha256,
                "remote_state_mutated": False,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
