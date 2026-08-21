# Unit 1 release QA

Verified boundary: 2026-08-21. This receipt applies only to the contiguous Indonesian reader unit comprising Brenner Lecture 1, Worksheet 1, and the one source-supplied solution attached to Exercise 1. It does not claim that the 29-unit edition is complete or that this corpus has separately been admitted to the 40-course curriculum.

## Final reader artifact

- PDF: `output/pdf/geometri-diferensial-manifold-mulus-unit-01-id.pdf`
- Bytes: 2,678,755
- SHA-256: `eb7e78affacf8a559d0f52a1c44921633d2fa74a070faa64af58efc32d34a568`
- Surface: 25 A4 pages, Bahasa Indonesia, four figures, 19 worksheet exercises, and one supplied solution.

## Translation and mathematical topology

The exact source/target verifier passed for the lecture, worksheet, and supplied solution. Command sequence, environment sequence, inline and displayed mathematics, protected macro calls, brace profile, order, and all declared deltas match. The target hashes are:

- Lecture: `428546cce566f1a93e237699f584ff6687275f555d295d584bc394d12e96cffa`
- Worksheet: `a4ec57c7c380c8a8f607019b660279a7f5ffd1cf5ee0e432154608ca1628965c`
- Supplied solution: `36f9b17c995afa4967c05fb119b15c18348dde5669a72140487c4d9ff33e12d5`

The strict final linguistic/mathematical audit found no remaining P1, P2, or P3 defect in the translated sources. Source defects and target-side corrections remain explicit in `00_control/ADVERSE_LEDGER.csv`; no correction is silent.

## Rights and build closure

All four Unit 1 media binaries are frozen with Commons revision metadata, creator, component license, byte size, SHA-1, and SHA-256. The reader exposes complete derivative-chain credit, including Episcophagus / `Polar angle to spherical side.svg` and AMK1211 / `BlankMap-World8.svg`, plus clickable Commons and license URLs.

Two clean three-pass build cycles produced byte-identical PDFs. The build receipt is `qa/unit-01/build.json`, SHA-256 `11550eedf5db17f867cad9123100d2367ccb9facd25c45c2ec27ff53419804aa`. All six console logs and the final TeX log contain no TeX error, warning, overfull or underfull box, undefined reference, or missing glyph.

## Structural, visual, privacy, and accessibility QA

`scripts/verify_unit01_pdf.py` passed and wrote `qa/unit-01/pdf_structural_qa.json`. All 25 pages are A4 with zero rotation; all 24 fonts have ToUnicode; every page has extractable text; `/Lang` is `id-ID`; 12 external URI annotations provide the four source and four license links; the PDF is unencrypted and contains no form, JavaScript, attachment, unsafe action, personal path, credential marker, project-umbrella residue, mojibake, or stale German operator/cross-reference residue.

All 25 pages were rendered at 120 dpi and visually inspected. Text, mathematics, page furniture, figures, captions, worksheet content, supplied solution, list of figures, detailed media attribution, and license page are legible with no clipping, overlap, corruption, or unexpected blank page. The manual receipt is `qa/unit-01/visual_qa.json`.

Known limitation: the PDF is not structurally tagged because the installed MiKTeX `latex-lab`/`tagpdf` stack failed before document compilation in the bounded tagging trial. This is disclosed rather than misrepresented. The PDF still has full ToUnicode coverage and extractable text; a semantic HTML reader remains the planned primary structured accessibility surface.

## Additive backend

The locale-neutral backend is bound to the final PDF and all current source, rights, build, structural, and visual receipts. Its deterministic export contains 174 schema-valid records across all 14 entity classes, including seven QA events and twenty correction records. JSONL SHA-256: `7b7cd4e77932d89920c921e886f3a689dcba4d0335325ec93593371552469533`; CSV SHA-256: `ade44164b71ea7306ae4d436dd4b7fbaafc759bc2ed2675335354303c1982469`.

## Disposition

Unit 1 passes its edition-production and bounded GitHub publication gate. The next production cursor is Lecture 2 plus Worksheet 2. Completion of this edition and selection of Brenner as the curriculum's O011 spine remain separate decisions.
