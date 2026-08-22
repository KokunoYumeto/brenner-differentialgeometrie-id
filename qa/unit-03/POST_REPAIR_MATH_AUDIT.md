# Unit 3 Post-Repair Mathematical and Content Audit

## Verdict

PASS

Unit 3 is mathematically faithful to the frozen German authority after the ten declared target corrections. The lecture, worksheet, and both source-supplied solutions preserve their formulas, identifiers, order, and mathematical dependencies; the cumulative PDF renders every corrected clause intelligibly. Remaining findings: **P1 = 0, P2 = 0, P3 = 0**.

Audit date: 2026-08-22. This was an independent, read-only comparison of the four frozen German TeX witnesses against the four final Indonesian targets, followed by inspection of the centered 56-page PDF's extracted text and rendered pages. Existing translation, build, structural, and visual receipts were used as corroborating evidence rather than as substitutes for the comparison.

## Exact identity binding

| Surface | Bytes | SHA-256 |
|---|---:|---|
| `authority/expanded/lecture03_source.de.tex` | 28,482 | `c6fa222d45a2abaaa121fabbf68a76ab478d9ede7dd14f370d8e58d40887c25a` |
| `authority/expanded/worksheet03_source.de.tex` | 9,997 | `8dded699ee9337ebdc4cb76a9373fb8e2f6a5df94c6048c3deaaaeaccb88bac7` |
| `authority/expanded/worksheet03_exercise07_solution_source.de.tex` | 2,514 | `7e3437274bf4f79b6a3fa719876b09fdbcee4e10523a215e9e6f4ecb566cdb85` |
| `authority/expanded/worksheet03_exercise16_solution_source.de.tex` | 1,882 | `ed49f1889840b8352f634ef01400301849f8303ec27a2a38b334b744ae5e5951` |
| `source/units/unit-03/lecture03.id.tex` | 29,657 | `769ec3b7e72159509ede182469711ce4093027de27096d5d256b88a6e7f32c16` |
| `source/units/unit-03/worksheet03.id.tex` | 10,129 | `89b05cf8280045703c64e8a0d3540883196f6569f2c9e24f630a6b00ee703474` |
| `source/units/unit-03/worksheet03_exercise07_solution.id.tex` | 2,895 | `e1ec57974437f39f778c9eadc26f3cd565cfe69e3f88980d644b2df93552bb36` |
| `source/units/unit-03/worksheet03_exercise16_solution.id.tex` | 2,166 | `738506177ab79f47321e5e6e83b110bfae887161477abda8145dc7ff52c2ebf3` |
| `output/pdf/geometri-diferensial-manifold-mulus-hingga-unit-03-id.pdf` | 3,596,282 | `aee7f335c8d8110feb7b70448c70680a30700285131d5a1b4e4aeb2f2d04b46a` |

The final cumulative reader has 56 A4 pages in a centered wrapper-owned frame with 22 mm margins. Two clean three-pass build cycles produced identical bytes. The build receipt is `qa/unit-03/build.json`, SHA-256 `f4ef7e3989f65d6b8c15112a4ab14ab1c10e5325a050d9985936073a566eb8b7`; the structural receipt is `qa/unit-03/pdf_structural_qa.json`, SHA-256 `f7b5661749f631e30b8c14e50590751dc4b343e1092b72e2f9b874f89b44cc9e`, verdict `PASS_WITH_DOCUMENTED_LIMITATION`; and the centered-reflow visual receipt is `qa/unit-03/visual_qa.json`, SHA-256 `669c9bc22dc4374515c7f68daf94a507dcc376428113f67046e884ea8be33010`, status `pass`. The documented lack of a PDF structure tree is an accessibility limitation, not a mathematical/content defect.

Control bindings:

- `qa/unit-03/AUTHORITY_PREFLIGHT.json`: `654045743462e239dd8b10a5f755b3e0400d39cebeaf0fe20b0330e3b68cdf8c`.
- `00_control/ADVERSE_LEDGER.csv`: `c8568788a4cdaa54e54fcb1a1f5cf9a3dd19df78da3a2ec4dea4520e89272dcf`.
- `00_control/LECTURE03_PROTECTED_CORRECTIONS.json`: `8beff151d17c801044d88036cbc5a8b53045c0f154a5ffa8dbd5f3f90f86c2fa`.
- `00_control/WORKSHEET03_PROTECTED_CORRECTIONS.json`: `3361dae52fbe51f020692973548eb6510f4bc6ae070a00048e8e479a96754111`.

All four current translation receipts report `status: pass`, exact current source/target hashes, equality-or-declared-delta for command, environment, inline/display mathematics, protected macro calls, and brace profiles, and complete consumption of declared deltas.

## Mathematical and structural comparison

The lecture retains both source sections and the complete numbered chain: Definitions 3.1-3.3, Examples 3.4-3.5, Lemmas 3.6-3.8, Definition 3.9, and Lemmas 3.10-3.11. Formula-by-formula comparison found the following intact: the unit-speed condition; curvature-circle radius and center; signed curvature; both circle orientations; the unit-circle and parabola calculations; the second-order osculating-circle construction; realization of a prescribed curvature profile; the normal-vector characterization; arc-length reparametrization; the general signed-curvature quotient; and the implicit-curve identity `(DN)_P(v) = -kappa(P)v`. Internal source-link target identifiers occur in exactly the same sequence in authority and target.

Terminology is mathematically discriminating and consistent: `kelengkungan`, `jari-jari kelengkungan`, `lingkaran kelengkungan`, `lingkaran oskulasi`, `evolut`, `berparametrisasi panjang busur`, `reguler`, `medan normal satuan`, and the standard/opposite orientation clauses are not conflated.

The worksheet contains exactly 21 exercises in authority order: 16 practice exercises followed by 5 graded exercises. The graded point sequence is exactly `2, 2, 4, 4, 4`, totaling 16 points. All hint fields remain blank. Exactly Exercises 7 and 16 are marked as carrying source-supplied solutions; no solution was invented for the other 19 exercises. The rendered reader labels them consecutively as Soal 3.1-3.21 and preserves the same practice/graded boundary.

Exercise 7's solution preserves the value, first derivative, and second derivative at zero; the center/radius ansatz; the two matching equations; and the deductions `u = omega` and `x = 0`. Exercise 16's solution preserves the gradient and unit normal, the total derivative matrix, its action on `(y,-x)`, the orientation statement, and signed curvature `-1`. Both supplied solutions are present exactly once in the PDF under their correct exercise numbers.

## Declared correction audit

| ID | Mathematical/content check | Final reader check | Result |
|---|---|---|---|
| `O011-CORR-0028` | For the stated clothoid, speed is `sqrt(pi)` and the general curvature quotient gives `kappa(t) = sqrt(pi)t`; replacing the source's `t` is correct. | The corrected equation is legible on PDF page 48. | PASS |
| `O011-CORR-0029` | The curve `(cos f(t), sin f(t))` is regular exactly where `f'(t) != 0`; the restriction is required by Lemma 3.10 and makes the curvature-circle request well-defined. | The condition is visibly attached to Exercise 3.11 on PDF page 48. | PASS |
| `O011-CORR-0030` | The sign discussion now distinguishes positive, negative, and zero curvature; zero is no longer mislabeled negative. | The three-way statement renders as continuous prose on PDF page 42. | PASS |
| `O011-CORR-0031` | Since the curvature-circle center contains division by curvature, the evolute domain is correctly restricted to `{t in I | kappa(t) != 0}`. | The restricted domain is explicit on PDF page 42. | PASS |
| `O011-CORR-0032` | Signed curvature is preserved by increasing (orientation-preserving) reparametrization and reverses under decreasing reparametrization; the added hypothesis is mathematically necessary. | `reparametrisasi meningkat` appears immediately before the proof computation on PDF page 44; the long derivation remains inside both margins. | PASS |
| `O011-CORR-0033` | Pointwise signed curvature on an implicit curve requires a chosen orientation and an orientation-compatible arc-length parametrization; both are now explicit. | The orientation clause is complete and readable on PDF page 44. | PASS |
| `O011-CORR-0034` | Only nonzero `v` can determine an oriented basis with `N(P)`; the identity at `v = 0` follows separately from linearity. | `v in T_PY \ {0}` appears on PDF page 44 and the separate zero-vector sentence follows with the identity on PDF page 45. | PASS |
| `O011-CORR-0035` | Moving lecture display punctuation into the display macro changes no formula or mathematical assertion. | PDF page 38 has inline sentence punctuation and no isolated punctuation line. | PASS |
| `O011-CORR-0036` | Moving the three worksheet display stops into their punctuation arguments changes no exercise formula, order, or classification. | PDF pages 46-48 contain no isolated display punctuation; the clothoid equation ends normally. | PASS |
| `O011-CORR-0037` | Moving the Exercise 7 solution display stop into its punctuation argument changes no equation or deduction. | PDF page 50 carries the stop on the equation line and has no standalone dot before the following prose. | PASS |

## Closure

No formula, variable, theorem/exercise identifier, exercise, point value, supplied solution, or terminology-critical distinction is missing or displaced. No corrected clause introduces a new mathematical error. The final PDF hash matches both the build/structural evidence and the inspected rendered reader. There are no remaining P1, P2, or P3 mathematical/content findings for Unit 3.
