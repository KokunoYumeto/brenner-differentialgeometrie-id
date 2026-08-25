#!/usr/bin/env python3
"""Apply the bounded 2026-08-22 Indonesian field-terminology decision.

This script touches only admitted Indonesian reader sources in Units 1--6.
German authority, stable link destinations, backend records, and other lanes are
outside its write set.  The replacements are deliberately locale-facing and
idempotent.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
UNIT_DIRS = [ROOT / "source" / "units" / f"unit-{number:02d}" for number in range(1, 7)]
RECEIPT = ROOT / "qa" / "terminology" / "FIELD_TERMINOLOGY_PROPAGATION_U01_U06.json"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def replace_count(text: str, old: str, new: str) -> tuple[str, int]:
    count = text.count(old)
    return text.replace(old, new), count


def main() -> None:
    files = [path for directory in UNIT_DIRS for path in sorted(directory.glob("*.id.tex"))]
    if not files:
        raise RuntimeError("no admitted Unit 1--6 Indonesian sources found")

    records: list[dict[str, object]] = []
    totals: dict[str, int] = {}
    for path in files:
        before_bytes = path.read_bytes()
        if before_bytes.startswith(b"\xef\xbb\xbf"):
            raise RuntimeError(f"unexpected UTF-8 BOM: {path}")
        text = before_bytes.decode("utf-8")
        changes: dict[str, int] = {}

        literal_replacements = [
            ("Transport Paralel", "Transpor Paralel"),
            ("transport-transport paralel", "transpor-transpor paralel"),
            ("transport paralel", "transpor paralel"),
            ("manifold terdiferensialkan", "manifold diferensiabel"),
            ("tangennya", "singgungnya"),
        ]
        for old, new in literal_replacements:
            text, count = replace_count(text, old, new)
            if count:
                changes[f"{old} -> {new}"] = count
                totals[f"{old} -> {new}"] = totals.get(f"{old} -> {new}", 0) + count

        # Preserve the admitted loan compound ``bundel tangen``.  The field
        # evidence supports the singgung family for tangent spaces/vectors/
        # lines, but it does not justify forcing the bundle term into a false
        # morphological symmetry.
        text, count = re.subn(r"(?<!bundel )\btangen\b", "singgung", text)
        if count:
            changes["standalone tangen -> singgung"] = count
            totals["standalone tangen -> singgung"] = totals.get("standalone tangen -> singgung", 0) + count

        # In these grammatical positions the Indonesian adjective is the
        # attested and natural form; nominal compounds retain "singgung".
        adjective_repairs = [
            ("medan-medan vektor singgung", "medan-medan vektor tangensial"),
            ("medan vektor singgung", "medan vektor tangensial"),
            ("medan singgung umum", "medan tangensial umum"),
            ("tetap singgung", "tetap tangensial"),
            ("bersifat singgung", "bersifat tangensial"),
            ("nilai singgung", "nilai tangensial"),
            ("sudah singgung pada", "sudah tangensial pada"),
            ("yang singgung pada", "yang tangensial pada"),
            ("$\\nabla_v F$ singgung pada", "$\\nabla_v F$ tangensial pada"),
        ]
        for old, new in adjective_repairs:
            text, count = replace_count(text, old, new)
            if count:
                changes[f"{old} -> {new}"] = count
                totals[f"{old} -> {new}"] = totals.get(f"{old} -> {new}", 0) + count

        after_bytes = text.encode("utf-8")
        if after_bytes != before_bytes:
            path.write_bytes(after_bytes)
        records.append(
            {
                "path": path.relative_to(ROOT).as_posix(),
                "before_bytes": len(before_bytes),
                "before_sha256": digest(before_bytes),
                "after_bytes": len(after_bytes),
                "after_sha256": digest(after_bytes),
                "changes": changes,
            }
        )

    joined = "\n".join(path.read_text(encoding="utf-8") for path in files)
    forbidden = {
        "disallowed_standalone_tangen": len(
            re.findall(r"(?<!bundel )\btangen(?:nya)?\b", joined)
        ),
        "indonesian_transport_paralel": joined.count("transport paralel")
        + joined.count("transport-transport paralel"),
        "manifold_terdiferensialkan": joined.count("manifold terdiferensialkan"),
        "unnatural_bersifat_singgung": joined.count("bersifat singgung"),
        "unnatural_tetap_singgung": joined.count("tetap singgung"),
        "unnatural_nilai_singgung": joined.count("nilai singgung"),
    }
    if any(forbidden.values()):
        raise RuntimeError(f"post-normalization forbidden forms remain: {forbidden}")

    receipt = {
        "schema_version": 1,
        "workflow": "o011-indonesian-field-terminology-u01-u06-v1",
        "decision_record": "qa/terminology/FIELD_TERMINOLOGY_AUDIT_20260822.md",
        "status": "pass",
        "files_checked": len(files),
        "files_changed": sum(bool(record["changes"]) for record in records),
        "totals": totals,
        "post_checks": forbidden,
        "allowed_bundel_tangen": len(re.findall(r"\bbundel tangen\b", joined)),
        "preserved_asset_identity": "Parallel transport sphere2.svg",
        "files": records,
    }
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(receipt, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
