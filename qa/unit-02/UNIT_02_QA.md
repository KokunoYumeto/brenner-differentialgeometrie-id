# Unit 2 verified-boundary QA

Verified boundary: 2026-08-22. This receipt covers the contiguous Indonesian cumulative reader through Brenner Lecture 2 and Worksheet 2, including every source-supplied solution for Unit 2: exercises 1, 2, 7, 12, and 13. It does not claim that the 29-unit edition is complete or that this corpus has been admitted to the separate 40-course curriculum.

## Final reader artifact

- PDF: `output/pdf/geometri-diferensial-manifold-mulus-hingga-unit-02-id.pdf`
- Bytes: 3,152,320
- SHA-256: `6312b4df706d0f08eeb9f37da0abda3428b5448dce54781d0f52eb9c8db5c385`
- Surface: 44 A4 pages containing Units 1-2, six figures, 38 worksheet exercises, and six source-supplied solutions in total.

## Authority and solution/media closure

Lecture 2 is pageid/revision `142546 / 893641`; Worksheet 2 is `142636 / 907117`. The sanitized expanded German TeX witnesses are 22,206 bytes with SHA-256 `f488d809e7d9490c40099d90c2abed2cc8bea39f11923a8d525e6302f3be470a`, and 10,171 bytes with SHA-256 `c645aacb16233d832b492315379b0251c33fa52db6b2e7ac24be4ecc9600d3ad`. The exact API responses, revision metadata, sanitation receipts, and 19-exercise solution query are bound in `AUTHORITY_PREFLIGHT.json` and `.md`.

Worksheet 2 has exactly five source-supplied solutions, for exercises 1, 2, 7, 12, and 13; the other 14 queried candidate solution pages are absent. Lecture 2 has two media files and the worksheet/solutions have none. `Integral apl rot obsah1.svg` and `Hyperboloid1.png` are frozen with exact bytes, Commons metadata, creators, source URLs, and SHA-256 hashes in `qa/unit-02_media.json`; both are public-domain components. No blanket media license is claimed.

## Translation and mathematical review

All seven exact source/target comparisons pass. Command and environment sequences, inline/display mathematics, protected macro calls, brace profiles, exercise order, point values, and solution mappings are exact or covered by a consumed hash-bound correction manifest. Final target identities are:

- Lecture 2: 22,694 bytes; `3dec5f7c1ec47b2ea965481f78db8334ab4046b001c53dd58bde0b9d0bb4cc49`
- Worksheet 2: 10,576 bytes; `677d9b244a2c30561f497e602e29081ca12f668d5a5ec3d116900c49a5bd5954`
- Solution 1: 951 bytes; `bf0788c3f5cc77324bca5dfc1a899b5410fa5a8312da7594b85993c9245a45fe`
- Solution 2: 965 bytes; `66ac0a6b86de21eee86a898fe7122644c932c4dff44bbc51845967a86b73e2fc`
- Solution 7: 1,499 bytes; `405e59e8569d9ba8d8dd35ebe6b2ce693cb931d8ed42824d790baeba31fdd8d3`
- Solution 12: 5,009 bytes; `1c04a8fd29888aa47633cffceb25104c6533e6c2b9e512ad663fd3742c581832`
- Solution 13: 2,532 bytes; `a4a230b45de82885027722450d3a7f12fc63fe06187abab481788f7b37352ac0`

The final independent audit, `POST_REPAIR_MATH_AUDIT.md`, passes with no remaining P1, P2, or P3 finding; SHA-256 `7ca1e3e61f7e7d86cf22e8dc4bd2669607ea68520a36dc77e09a413cc3794734`. Corrections O011-CORR-0012 through O011-CORR-0027 are explicit and machine-readable in the adverse ledger. They include source-level mathematical repairs, source-number preservation, punctuation/orientation/domain corrections, and three final target-prose/reference repairs. None is silent.

## Reproducible build, structural, and visual QA

Two independent clean cycles, each with three pdfTeX passes, produced the same 3,152,320-byte PDF and SHA-256. `qa/unit-02/build.json` has SHA-256 `3eb91e7c7f02bbca7ef1400ec10461e7b2584e06611920c7f29163d786f0ab00`; all final logs contain no TeX warning, error, overfull/underfull box, undefined reference, or missing glyph.

`scripts/verify_through_unit02_pdf.py` passes. All 44 pages are A4 with zero rotation; `/Lang` is `id-ID`; all 28 unique embedded fonts have ToUnicode; both pypdf and pdfplumber extract nonempty text from every page. The PDF is unencrypted and contains no form, JavaScript, attachment, unsafe action, personal path, credential marker, project-umbrella residue, replacement character, raw wiki syntax, or active German prose. All required headings, solutions, credits, and 15 exact Commons/license URI annotations are present. Structural receipt: `qa/unit-02/pdf_structural_qa.json`, SHA-256 `3aa3bda7a35e0870fd25249cd81c3c193f2ab1f3e49998ad6bd618d1fb6bbf56`.

All 44 pages were rendered at 120 dpi and visually inspected. The title matter, contents, source numbering, formulas, both lecture/worksheet pairs, all supplied solutions, figures, list of figures, attribution, and license page are legible with no clipping, overlap, corrupt glyph, missing image, broken transition, or unexpected blank page. The repaired antipodal-map sentence, Solution 12 opening, Solution 13 cross-reference, and Unit 2 media-rights wording were inspected directly. Visual receipt: `qa/unit-02/visual_qa.json`, SHA-256 `41971a564ca4ad80b070e084a5661087eed7c780fab0b6057109d447011004ee`.

Known limitation: the PDF remains structurally untagged. This is disclosed rather than overstated; language metadata, ToUnicode coverage, and text extraction pass. A semantic reflowable HTML reader remains the planned primary structured accessibility surface.

## Additive backend

The deterministic backend now contains 357 schema-valid records across all 14 entity classes. The frozen Unit 1 slice remains byte-identical at 174 records; Unit 2 contributes 183 records, including 27 unit records, 3 segments, 4 concepts, 2 assets, 2 rights records, 8 artifacts, 13 QA events, 16 corrections, and 108 relations. Two fixed-checkpoint exports are byte-identical, all references resolve, and all 42 manifest inputs rehash current.

- `backend/records.jsonl`: 215,317 bytes; `a393d3ff6c8aed203e7d3690eb6391e22ea25436cd06e85aa40e1adc23adb122`
- `backend/records.csv`: 79,611 bytes; `5880fa9dee8bc0a73ed0e903d931fad38978bc2c9ef65cc58b62b48a7f26b7ba`
- `backend/MANIFEST.json`: 11,614 bytes; `2b34e24c0efbce3b6cc847ddc1232b4f2b881126f7b6d5ac39ba469b22b7f789`
- `qa/unit-02/backend_qa.json`: 3,798 bytes; `304ee9d7455a169f3b8cdccce1a27d653446fdcb7a582f1bbc5c20ce07fc39c8`

## Disposition

Unit 2 passes its local edition-production boundary. The next cursor is Lecture 3 plus Worksheet 3. No Git operation, upstream contact, or publication was performed in this turn, as required by the current task instruction. Unit 1 remains the latest public release; completion of this edition and curriculum admission remain separate decisions.
