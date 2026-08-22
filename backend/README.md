# O011 modular backend

This backend is additive to the Indonesian reader. It follows the coordinator's interoperability envelope without making the reader depend on a database or proprietary service.

- `schema/o011-record-v1.schema.json` defines the common record envelope.
- `records.jsonl` is the canonical deterministic UTF-8/LF stream for Units 1–3.
- `records.csv` is a deliberately lossy exchange projection of common fields.
- `MANIFEST.json` binds the generated views, source/target inputs, and generator.
- `unit01_records_frozen.jsonl` is the immutable 174-record Unit 1 baseline. The full 357-record Units 1–2 prefix is also preserved byte-for-byte in every Unit 3 export.

Stable IDs use source order and source-local identity, never translated titles or rendered page numbers. Display identifiers retain Brenner's source numbering (`1.x`, `2.x`, `3.x`) rather than the standalone book wrapper's chapter prefixes. Corrections and component rights remain separate records. Regenerate the combined backend only through `scripts/export_backend_v3.py`; generated files must not be hand-edited.

Unit 1 exposes one PDF `artifact` and receipt-backed `qa_event` records for structural translation checks, exact media closure, two-cycle reproducible PDF build, structural/accessibility inspection, and all-page visual inspection. Evidence paths are repository-relative; receipt hashes bind the records without copying machine-local or temporary-render paths into the public views.

Unit 2 adds the lecture/worksheet pair, three lecture segments, nineteen exercises, five supplied solutions, four concepts, two Commons assets with separate rights records, seven translated-TeX artifacts, and the sixteen documented corrections `O011-CORR-0012`–`0027`.

Unit 3 adds its lecture/worksheet pair, two lecture segments, twenty-one exercises, exactly two supplied solutions, five concepts, twenty admitted term records, three Commons assets with separate rights records, five artifacts, eleven QA events, and the ten documented corrections `O011-CORR-0028`–`0037`. It binds the cumulative through-Unit-3 PDF, exact media closure, two-cycle reproducible build, structural/accessibility inspection, all-page visual inspection, and independent mathematical audit. The cumulative backend contains 591 records; the validation receipt is `qa/unit-03/backend_qa.json`. No HTML artifact is claimed at this boundary.

Use an explicit checkpoint timestamp so a repeat export is byte-identical:

```text
python scripts/export_backend_v3.py --root . --checkpoint YYYY-MM-DDTHH:MM:SSZ --translation-state structurally_verified
```

The generator rejects a changed Units 1–2 prefix, a failed or stale Unit 3 receipt, incomplete exercise/solution/correction closure, a mismatched media hash, unresolved stable-ID references, and generated output containing an absolute machine path or common credential marker. Run `scripts/verify_backend_v3.py` after two exports with the same checkpoint to validate every JSONL row against the Draft 2020-12 schema, verify references and live evidence hashes, prove byte-identical repeat output, and regenerate the deterministic Unit 3 backend QA receipt.
