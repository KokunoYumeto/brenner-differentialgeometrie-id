# Unit 4 verified-boundary QA

Verified boundary: 2026-08-22. This receipt covers the contiguous Indonesian cumulative reader through Brenner Lecture 4 and Worksheet 4, including both and only the source-supplied Unit 4 solutions, for Exercises 7 and 10. It does not claim that the 29-unit edition is complete or that this corpus has been admitted to the separate curriculum.

## Final reader artifact

- PDF: `output/pdf/geometri-diferensial-manifold-mulus-hingga-unit-04-id.pdf`
- Bytes: 3,666,928
- SHA-256: `04f84c2d7abdc721cb0ebafcd4e39c230a01faf60665f84d5e7124bf2574319b`
- Surface: 72 centered A4 pages containing Units 1-4, nine figures, 74 worksheet exercises, and all ten solutions actually supplied by the source across those units.
- Page frame: wrapper-owned A4 geometry with centered 22 mm margins. No Unit 4 translation, formula, identifier, exercise, solution, or rights surface depends on the legacy offset page-frame assignments.

## Authority, exercise, solution, and media closure

Lecture 4 is pageid/revision `142548 / 893683`; Worksheet 4 is `142638 / 1010985`. Their `/latex` surfaces are pageid/revision `142578 / 807138` and `142668 / 807107`. Exact expanded German TeX identities are:

- Lecture 4: 26,932 bytes; `610c85e2cb9838a2ce1deb488ceca6cb7d2ee2ab47f1e657d5df7488796f8402`
- Worksheet 4: 11,052 bytes; `81f8d9667581e0e6507dd1684b136c23f3352d1cabf2e8c4013daeb0a312cd00`
- Exercise 7 solution: 2,623 bytes; `a0df2279b1dbae5bff1a4e50385349080bd8734e20d1a6edec83e528045dc63e`
- Exercise 10 solution: 2,633 bytes; `76a2f5db7eb835b19b924418ae2c1b0cfbcd8cd2d5acc387f695f71cbb069a35`

The exact revision/API/sanitation, solution-presence and absence-query, media, and current-revision evidence passes in `qa/unit-04/AUTHORITY_PREFLIGHT.json`, 26,771 bytes, SHA-256 `0a2f455c500cad070fe8d5970786189840fd90cbb856101c7cd177de0bdefa36`; its independent consistency receipt is 517 bytes, SHA-256 `3dbcb88246dff59e786257882e671072588bd50a4fd98bfb0ba7a2b374700893`. Worksheet 4 contains 15 exercises: 11 practice and four graded exercises worth `4, 5, 4, 6` points, or 19 points total. All hint fields are blank. Exactly two conventional solution pages exist; the other 13 queried candidates are absent, and the reader invents none.

Unit 4 has exactly zero displayed-media occurrences and zero admitted media files. The cumulative nine figures are all inherited from Units 1-3 under their component-specific rights records. A historical official Unit 4 PDF witness is retained locally only: 210,221 bytes, SHA-256 `65ee310d19704bdbbb7f981f821901f96b166ceac416ad7cc063ae737894571d`. Because its internal CC BY-SA 3.0 declaration conflicts with Commons structured CC BY-SA 4.0 metadata, it is not a translation master, derivative input, tracked public file, or release asset.

## Translation and mathematical review

The final Indonesian targets are:

- Lecture 4: 28,602 bytes; `60a7a2cbfc96a9a510bfff935f40722458c85031214eeaf8ccf4e8df2af2bc81`
- Worksheet 4: 11,797 bytes; `f3721ced8fc5db02dd600ff81f02455ec724f34c7a085f4280d8f5c2d14873f8`
- Exercise 7 solution: 1,983 bytes; `6003193ccef4456ffcbe42e67068202567ceafe4897363aa4833b266aaf855d5`
- Exercise 10 solution: 2,661 bytes; `a5d22c14d32b03265e532b34636da4d656d838cefe268c92d1ac3ec1ebd27de4`

All four manifest-aware comparison receipts pass the final source/target hashes, command and environment sequences, inline/display mathematics, protected macro calls, brace profiles, source order, exercise classification, point values, empty hints, and solution mapping. Corrections `O011-CORR-0038` through `O011-CORR-0045` are explicit and hash-bound in `00_control/ADVERSE_LEDGER.csv`, 15,319 bytes, SHA-256 `c2d9b4bc6a5fd51e0f1b5ad5a314badff19f3bbfee04d6afc38f7005ebde47c5`; none is silent.

The independent post-repair mathematical/content audit re-read all four German witnesses against all four final Indonesian targets. It verifies the cone rotation, the complete torus solution, the ellipsoid sign and eigenbasis, `T_PY`, the restored normal argument, the graph operator `A=G^{-1}H/\sqrt{1+\lVert\nabla f\rVert^2}`, and both corrected `C^2` hypotheses. It passes with no remaining mathematical, topology, formula-order, exercise-order, point, hint, or solution finding. `qa/unit-04/POST_REPAIR_MATH_AUDIT.md` is 11,563 bytes with SHA-256 `814052c6ae88232593ed9cb9d1980612c8fd2e027ead853c2babae3fe0bb1f4f`.

## Reproducible build, structural, and visual QA

Two independent clean cycles, each with three pdfTeX passes, produced the same 3,666,928-byte PDF and SHA-256. All six final console logs contain zero matches for TeX warnings, errors, overfull or underfull boxes, badness, missing glyphs, or undefined references. The build receipt is `qa/unit-04/build.json`, 7,520 bytes, SHA-256 `f68276cf509a33e596397e4e41edd0eba0f0762c5671239f1af900d7bb85a8eb`.

The structural verifier passes with the documented tagging limitation. All 72 pages are A4 with zero rotation; `/Lang` is `id-ID`; all 29 unique embedded fonts have ToUnicode; both pypdf and pdfplumber extract nonempty text from every page. Required bookmarks, solution headings, media-rights statements, and source/license links are present. The PDF is unencrypted and contains no form, JavaScript, attachment, unsafe action, personal path, credential marker, or project-umbrella residue. `qa/unit-04/STRUCTURAL_QA.json` is 15,506 bytes with SHA-256 `ad26e5f7bd9f525376b77cba0880da31730369a516a656b8d17d2f72e1503896`.

All 72 pages were rendered at 120 dpi and inspected in 18 ordered four-page contact sheets, with direct full-page inspection of the dense Unit 4 lecture, worksheet, both supplied solutions, rights inventory, and license close. The centered frame fills the page consistently; equations remain within the text block; labels, correction notes, matrices, fractions, vectors, and links are legible; and no clipping, overlap, corrupt glyph, broken transition, or visual blocker remains. The programmatic cross-check found minimum ink margins of 103 px left, 102 px right, 57 px top, and 59 px bottom, with zero pages entering a 20 px edge zone. `qa/unit-04/VISUAL_QA.md` is 2,418 bytes with SHA-256 `261b98fe10e34a34fe66461a7a87072b9b666dd78ec9516702454c4eb9d6b90a`.

Known limitation: the PDF remains structurally untagged. This is disclosed rather than overstated; language metadata, ToUnicode coverage, and page-complete extraction pass. The planned semantic reflowable HTML reader remains the primary future structured-accessibility surface and is not claimed at this boundary.

## Additive backend

The deterministic backend contains 813 schema-valid records; Unit 4 contributes 222 records while the frozen 591-record Units 1-3 prefix remains byte-identical. Two fixed-checkpoint exports are byte-identical, all references resolve, every manifest input rehashes current, and the backend binds the final PDF and all current authority, translation, mathematical, build, structural, visual, rights, and withheld-witness evidence. HTML is honestly recorded as absent at this boundary.

- `backend/records.jsonl`: 482,841 bytes; `33a4f876f8225e40a006e97453f5530c05b21e327cfd1b7058303fa2421287f9`
- `backend/records.csv`: 168,680 bytes; `34a472148f9f376dcc6da220af640c0b4b5f12586b722015789908226059b5ea`
- `backend/MANIFEST.json`: 14,840 bytes; `d33f6c72c4be0a73cd3c9d4205422682e36aacb9f8303b63b75d25a1fb5c5a11`
- `qa/unit-04/backend_qa.json`: 4,881 bytes; `706a2794d57b00673cecd07688277fcdcb65233fc82c6f047ec37e60197cc720`

## Disposition

Unit 4 passes its bounded edition-production and publication gates. The edition remains incomplete; after preservation of this verified boundary, the next production cursor is Lecture 5 plus Worksheet 5. Curriculum admission remains a separate comparison and must not count completed translation or sunk effort as evidence. No upstream contact occurred.
