# Unit 3 verified-boundary QA

Verified boundary: 2026-08-22. This receipt covers the contiguous Indonesian cumulative reader through Brenner Lecture 3 and Worksheet 3, including both and only the source-supplied Unit 3 solutions, for Exercises 7 and 16. It does not claim that the 29-unit edition is complete or that this corpus has been admitted to the separate 40-course curriculum.

## Final reader artifact

- PDF: `output/pdf/geometri-diferensial-manifold-mulus-hingga-unit-03-id.pdf`
- Bytes: 3,596,282
- SHA-256: `aee7f335c8d8110feb7b70448c70680a30700285131d5a1b4e4aeb2f2d04b46a`
- Surface: 56 centered A4 pages containing Units 1-3, nine figures, 59 worksheet exercises, and all eight solutions actually supplied by the source across those units.
- Page frame: wrapper-owned A4 geometry with centered 22 mm margins. The six historical preamble assignments that previously narrowed and offset the text column are retained only as commented provenance and no longer override the reader wrapper.

## Authority, exercise, solution, and media closure

Lecture 3 is pageid/revision `142547 / 1020016`; Worksheet 3 is `142637 / 894109`. Their `/latex` surfaces are pageid/revision `142577 / 807136` and `142667 / 807105`. Exact expanded German TeX identities are:

- Lecture 3: 28,482 bytes; `c6fa222d45a2abaaa121fabbf68a76ab478d9ede7dd14f370d8e58d40887c25a`
- Worksheet 3: 9,997 bytes; `8dded699ee9337ebdc4cb76a9373fb8e2f6a5df94c6048c3deaaaeaccb88bac7`
- Exercise 7 solution: 2,514 bytes; `7e3437274bf4f79b6a3fa719876b09fdbcee4e10523a215e9e6f4ecb566cdb85`
- Exercise 16 solution: 1,882 bytes; `ed49f1889840b8352f634ef01400301849f8303ec27a2a38b334b744ae5e5951`

The exact revision/API/sanitation and absence-query evidence passes in `qa/unit-03/AUTHORITY_PREFLIGHT.json`, 36,951 bytes, SHA-256 `654045743462e239dd8b10a5f755b3e0400d39cebeaf0fe20b0330e3b68cdf8c`. Worksheet 3 contains 21 exercises: 16 practice and five graded exercises worth `2, 2, 4, 4, 4` points, or 16 points total. All hint fields are blank. Exactly two conventional solution pages exist; the other 19 queried candidates are absent, and the reader invents none.

Unit 3 uses exactly three admitted media files: `Parabola circle.svg` (IkamusumeFan, CC BY-SA 4.0), `Euler spiral.svg` (AdiJapan, CC BY-SA 3.0), and `Evolute-parab.svg` (Ag2gaeh, CC BY-SA 4.0). Exact Commons identities, bytes, hashes, derivative identities, creators, source URLs, and licenses pass in `qa/unit-03_media.json`, 5,698 bytes, SHA-256 `a6af5b76a899633f366a024edd59181186846a045821aa74d8e6a2b51ab74936`. No blanket media license is claimed.

## Translation and mathematical review

The final Indonesian targets are:

- Lecture 3: 29,657 bytes; `769ec3b7e72159509ede182469711ce4093027de27096d5d256b88a6e7f32c16`
- Worksheet 3: 10,129 bytes; `89b05cf8280045703c64e8a0d3540883196f6569f2c9e24f630a6b00ee703474`
- Exercise 7 solution: 2,895 bytes; `e1ec57974437f39f778c9eadc26f3cd565cfe69e3f88980d644b2df93552bb36`
- Exercise 16 solution: 2,166 bytes; `738506177ab79f47321e5e6e83b110bfae887161477abda8145dc7ff52c2ebf3`

All four manifest-aware comparison receipts pass the final source/target hashes, command and environment sequences, inline/display mathematics, protected macro calls, brace profiles, source order, exercise classification, point values, and solution mapping. Corrections `O011-CORR-0028` through `O011-CORR-0037` are explicit and hash-bound in `00_control/ADVERSE_LEDGER.csv`, SHA-256 `c8568788a4cdaa54e54fcb1a1f5cf9a3dd19df78da3a2ec4dea4520e89272dcf`; none is silent.

The independent post-repair mathematical/content audit re-read all four German witnesses against all four final Indonesian targets and inspected the reflowed PDF's extracted and rendered correction sites. It passes with no remaining P1, P2, or P3 finding. `qa/unit-03/POST_REPAIR_MATH_AUDIT.md` is 8,652 bytes with SHA-256 `8c82fb8a7b4ec324f7284676bdffbbe9a5b323d15c3dfcf10977a287c9c56086`.

## Reproducible build, structural, and visual QA

Two independent clean cycles, each with three pdfTeX passes, produced the same 3,596,282-byte PDF and SHA-256. All six final console logs contain zero matches for TeX warnings, errors, overfull/underfull boxes, missing glyphs, or undefined references. The build receipt is `qa/unit-03/build.json`, 6,406 bytes, SHA-256 `f4ef7e3989f65d6b8c15112a4ab14ab1c10e5325a050d9985936073a566eb8b7`.

The structural verifier passes with the documented tagging limitation. All 56 pages are A4 with zero rotation; `/Lang` is `id-ID`; all 28 unique embedded fonts have ToUnicode; both pypdf and pdfplumber extract nonempty text from every page. Required bookmarks, solution headings, media credits, and source/license links are present. The PDF is unencrypted and contains no form, JavaScript, attachment, unsafe action, personal path, credential marker, or project-umbrella residue. `qa/unit-03/pdf_structural_qa.json` is 14,420 bytes with SHA-256 `f7b5661749f631e30b8c14e50590751dc4b343e1092b72e2f9b874f89b44cc9e`.

All 56 pages were rendered at 120 dpi and inspected in four ordered contact sheets, with direct full-page inspection of the title/contents, Unit 3 opening, the long reparametrization derivation, worksheet corrections, both supplied-solution transitions, media attribution, and license close. The centered frame fills the page consistently; equations stay within the margins; media filenames wrap; figures are sharp; and no clipping, overlap, corrupt glyph, isolated display punctuation, broken transition, or visual blocker remains. `qa/unit-03/visual_qa.json` is 3,921 bytes with SHA-256 `669c9bc22dc4374515c7f68daf94a507dcc376428113f67046e884ea8be33010`.

Known limitation: the PDF remains structurally untagged. This is disclosed rather than overstated; language metadata, ToUnicode coverage, and page-complete extraction pass. The planned semantic reflowable HTML reader remains the primary future structured-accessibility surface and is not claimed at this boundary.

## Additive backend

The deterministic backend contains 591 schema-valid records; Unit 3 contributes 234 records while the frozen 357-record Unit 1-2 prefix remains byte-identical. Two fixed-checkpoint exports are byte-identical, all references resolve, every manifest input rehashes current, and the backend binds the final centered PDF and all current build/structural/visual/mathematical evidence. HTML is honestly recorded as absent at this boundary.

- `backend/records.jsonl`: 350,935 bytes; `e2b1e159b1dff04273ddb0af82e85dc32adbb507f3936881f750867527d6800a`
- `backend/records.csv`: 125,961 bytes; `bdd4648d7e104da5f96a20ff85850a8782379f02609c3f29ed88117401032941`
- `backend/MANIFEST.json`: 12,404 bytes; `8810518777d9f08ba4a833784835f669c2b9b592b14f928fd0c895f712abd122`
- `qa/unit-03/backend_qa.json`: 3,460 bytes; `616df624197490ec322bdb488df56a233d426ddd06ac2dc64e2de46b1c70f6ca`

## Disposition

Unit 3 passes its bounded edition-production and publication gates. The edition remains incomplete; after preservation of this verified boundary, the next production cursor is Lecture 4 plus Worksheet 4. Curriculum admission remains a separate comparison and must not count completed translation or sunk effort as evidence. No upstream contact occurred.
