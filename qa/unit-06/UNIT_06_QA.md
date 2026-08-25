# Unit 6 verified-boundary QA

Verified boundary: 2026-08-23. This receipt covers the contiguous Indonesian
cumulative reader through Brenner Lecture 6 and Worksheet 6, including every
solution actually supplied by the frozen authority for this unit. It does not
claim that the 29-unit edition, ten-exam bank, Lie bridge, de Rham bridge, or
semantic HTML reader is complete. The release state is `active_partial`.

## Authority and exact source closure

The admitted authority is Holger Brenner, *Differentialgeometrie (Osnabrück
2023)* on German Wikiversity, recursively frozen at course pageid `142521`,
revision `889544`, timestamp `2023-03-07T11:39:09Z`, MediaWiki SHA-1
`e274ea4f0ae092736a5df23dfd3bb744184a9f2d`. Unit 6 is the exact source pair
`Vorlesung 6` / `Arbeitsblatt 6` (root pageids/revisions `142550/894447` and
`142640/894859`). The official expanded TeX witnesses are retained in
`authority/expanded/lecture06_source.de.tex` (29,148 bytes,
`7fde9eb970e13ecaeb9a6a4368a77f002c2b62d691dcc84139a6db50aef5d3e8`) and
`authority/expanded/worksheet06_source.de.tex` (14,690 bytes,
`886426135b7eeed2fc951670e897bbb8dd9f281e4500f1e71a084a1450aff57b`). The
unit authority preflight is `qa/unit-06/AUTHORITY_PREFLIGHT.json` (34,734 bytes,
SHA-256 `20e961850dccf9f31a1ad62e8d4aef1a8d43e642d23168863956427e7b28695d`)
and its Markdown summary records the complete revision, expansion, exercise,
solution, hint, and media census.

The worksheet has 18 exercises (4 graded, 14 practice; 14 graded points), no
source hint fields, and exactly three source-supplied solutions: Exercises 2,
6, and 9. The other 15 solution candidates remain absent and no solution is
attributed to the authority for them. One displayed asset is admitted:
`Parallel transport sphere2.svg`, 11,448 bytes, SHA-256
`4a6215c455dc248c97d1831e9af8b5d551a7cdb5da46976df2c1a77c959b88f8`, by Silly
rabbit, CC BY-SA 3.0, Commons revision `676576252`; its deterministic PNG
print derivative and attribution are bound in `qa/unit-06_media.json`.
Text and adaptation remain CC BY-SA 4.0; media retain file-specific rights.

## Translation and mathematical closure

Final source/target witnesses are:

- `source/units/unit-06/lecture06.id.tex`: 32,034 bytes,
  `180c553eb556d91ba733e00f012bd0ece36c32e66704c992f0c64244ab6e05e8`.
- `source/units/unit-06/worksheet06.id.tex`: 16,526 bytes,
  `b0cf54f892e2357bd6edaf1ed87df711cffcdf164c1454e7b7d2c987faa8bca5`.
- Supplied-solution targets for Exercises 2, 6, and 9:
  `772755e8e7d46abd63b2acf146fec3be01a23f57476cbea153ff14668a316ad5`,
  `e10704fec468e5ee582e72415ef85d92ad6182a3a4207359ad10ac41b9a581ac`, and
  `fd027471aa6655aaf6b2d07c60e7a96cb5d13df961adca1c38d2021cc19cf39b`.

The complete prose/meaning audit is `qa/unit-06/PROSE_QA.md`. Sixteen
source/translation corrections, `O011-CORR-0054` through `O011-CORR-0069`,
are explicit in the adverse ledger; the post-repair mathematical audit passes
all recorded checks (`qa/unit-06/POST_REPAIR_MATH_QA.json`, 28,914 bytes,
SHA-256 `b462de3f20b2a650d3f430660c993b598eba37f8acb0e4cc7187c0e171ee0cc7`).
The field-terminology audit and its fallback Indonesian academic comparison
are recorded in `qa/terminology/FIELD_TERMINOLOGY_AUDIT_20260822.md` (10,753
bytes, SHA-256 `a685d3e0f735df6498113d0a692cc95261a9fa0e5aa02010455d9650271c8559`
— the complete file hash is recorded in the companion ledger) and the
propagation receipt `qa/terminology/FIELD_TERMINOLOGY_PROPAGATION_U01_U06.json`
(SHA-256 `c625cb3b97b1032dcec864c3ea06d7098f4a5ab7274078493f86e91c0e1de811`).
No suitable Indonesian arXiv TeX source existed in the bounded search; the
fallback source and decision are named in that audit. The exact provenance
note is preserved in the reader and release notes as `OpenAI Codex gpt-5.6-sol,
Ultra`; source authors and media creators remain credited.

## Reader build and QA

The settled reader is `output/pdf/geometri-diferensial-manifold-mulus-hingga-unit-06-id.pdf`,
105 centered A4 pages, 4,765,606 bytes, SHA-256
`40bf26d196ff04c38c6c99e8e9669a86bb5e6d31124b904b7ad154e7948cdec1`. Two
independent clean three-pass pdfTeX cycles are byte-identical. The build
receipt is `qa/unit-06/build.json` (5,146 bytes, SHA-256
`fa3ff197c5dd03be1aff6766ac1a3e8db779ebf9557091cf1aac4f9fa836f466`). The
structural receipt is `qa/unit-06/pdf_structural_qa.json` (43,351 bytes,
SHA-256 `27af0539c1d5e130dd67a935975a2fed450d67b5e8b924e93a6752f34b6f049e`):
PASS_WITH_DOCUMENTED_LIMITATION, zero blockers/warnings, all pages
extractable, and 33/33 embedded fonts with ToUnicode. Full-page visual QA is
recorded in `qa/unit-06/VISUAL_QA.md` and passes. The prose and visual receipts
are `qa/unit-06/PROSE_QA.md` (4,414 bytes, SHA-256
`9b4f9ff339cb4e4eef94adafb928971175fce50861c2182e0a0a723c725710ad`) and
`qa/unit-06/VISUAL_QA.md` (2,875 bytes, SHA-256
`b5ec0160f897272b57c823ba2d5d2d483de42c7a0f8eeee918af3564e5118d68`). The
only disclosed limitation is structural: the PDF is not tagged. Semantic HTML
is not claimed at this boundary.

## Additive stable-ID backend

The backend verifier passes independently with system Python. There are 1,173
schema-valid records: the 969-record Units 1–5 prefix is byte-identical, and
Unit 6 adds 204 records (18 exercises, three supplied solutions, terms,
concepts, one media/right pair, corrections, artifacts, QA events, and
relations). Final artifacts are:

- `backend/records.jsonl`: 702,086 bytes, SHA-256
  `b09862d4b98c475d7e5a3bc92f1e3d72ca771d7f726350b76ab4bd68d6dde5a1`.
- `backend/records.csv`: 243,301 bytes, SHA-256
  `5831a7bf3ccc0c18c4246bf713ec6e4c93958465808e7027763e53e170683997`.
- `backend/MANIFEST.json`: 12,110 bytes, SHA-256
  `7e3efde35929a615384a104397d5c380b76d27b516b31f32919f907259cd5c44`.
- `qa/unit-06/backend.json`: 4,471 bytes, SHA-256
  `dc94366f185030611c8032d4a4e1a9fb7847cd6af13e1a2302627e0581573a2e`.

The backend is additive and never required to read the PDF.

## Rights, privacy, and release payload

The deterministic source/backend/provenance ZIP is 1,592,929 bytes, SHA-256
`660cda84e2cdc6c5b5723238165107e4f29678e12c8768d302923d885c65b524`, with
318 entries, normalized timestamps, and CRC verification. The six-file public
payload is 6,368,183 bytes, below the 500,000,000-byte lane cap. Staging and
release receipts prove that no credential-like value, private locator, cache,
or historical receipt entered the payload. The exact license notice, release
notes, manifest, and checksums are included; no blanket license is inferred
for component media.

## Public preservation

Zenodo publication succeeded as a new version of concept `22059977`: record
`22070425`, DOI `10.5281/zenodo.22070425`, URL
`https://zenodo.org/records/22070425`. The reader-first API order is PDF, ZIP,
LICENSE, release notes, manifest, checksums. `qa/unit-06/ZENODO_PUBLICATION_RECEIPT.json`
(4,970 bytes, SHA-256 `248014149accdc95ba7fcd4147451891ccb2c2cad1d61682ffb6bff9afe67073`)
and the independent anonymous readback
`qa/unit-06/ZENODO_PUBLIC_READBACK_RECEIPT.json` (3,781 bytes, SHA-256
`6bf800ca43aa598d83a7304812427eeaee5afebcf8534fbddde65575392efb8c`) prove
the public filenames, byte counts, hashes, latest-concept lineage, and
reader-first order. The work remains a partial checkpoint, not a completed
edition.

The authorized Figshare update was closed before mutation because article
`33314790` and its required project/collection memberships were absent from
the bounded API readback. The exact evidence is
`qa/unit-06/FIGSHARE_PREPUBLICATION_BLOCK_RECEIPT.md`; no duplicate article
or unsupported license claim was created. The prior Unit 5 Figshare receipt
is historical only. Retry only after predecessor visibility returns.

GitHub remains suspended under the existing support ticket and was not retried.
No upstream contact occurred.

## Cursor and terminal condition

This is a verified Unit 6 boundary, not completion of O011. The next
source-order action is to freeze and translate Lecture 7 plus Worksheet 7,
then continue through all 29 pairs, the exam closure, both bridges, original
solution-bearing items, HTML/PDF/backend QA, and final publication/readback.
