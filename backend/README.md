# O011 modular backend

This backend is additive to the Indonesian reader. It follows the coordinator's interoperability envelope without making the reader depend on a database or proprietary service.

- `schema/o011-record-v1.schema.json` defines the common record envelope.
- `records.jsonl` is the canonical deterministic UTF-8/LF stream.
- `records.csv` is a deliberately lossy exchange projection of common fields.
- `MANIFEST.json` binds the generated views, source/target inputs, and generator.

Stable IDs use source order and source-local identity, never translated titles or rendered page numbers. Corrections and component rights remain separate records. Regenerate only through `scripts/export_backend.py`; generated files must not be hand-edited.

Unit 1 also exposes one PDF `artifact` and receipt-backed `qa_event` records for the three structural translation checks, exact media closure, two-cycle reproducible PDF build, structural/accessibility inspection, and all-page visual inspection. Evidence paths are repository-relative; receipt hashes bind the records without copying machine-local or temporary-render paths from the receipts into the public views.

Use an explicit checkpoint timestamp so a repeat export is byte-identical:

```text
python scripts/export_backend.py --timestamp YYYY-MM-DDTHH:MM:SSZ --translation-state built
```

The generator rejects a failed or stale receipt, a mismatched PDF or media hash, unresolved stable-ID references, and generated output containing an absolute machine path or common credential marker.
