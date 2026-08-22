# Independent Unit 2 worksheet mathematics and translation audit

> **Historical pre-repair audit; superseded.** This receipt records defects in an earlier target state. Those defects were repaired, rebuilt, and independently re-audited. The terminal Unit 2 verdict and current hashes are in `POST_REPAIR_MATH_AUDIT.md` (PASS).

## Verdict

- **Translation fidelity: PASS.** The Indonesian worksheet and all five supplied solutions preserve the German tasks, solution-to-exercise mapping, quantifiers, signs, domains, mathematical notation, identifiers, and formula order. No target-originated mathematical mistranslation was found.
- **Reader mathematics/release gate: FAIL.** The package is not yet suitable for an unqualified mathematics-correct release because the frozen German authority contains one demonstrably false displayed derivation, one incomplete injectivity proof, and an orientation ambiguity that the Indonesian files faithfully reproduce. These are source defects, not translation defects, but they require correction or explicit editorial disclosure.
- **Untranslated residue: PASS.** No active German or English reader prose or placeholders remain. German occurs only inside preserved source identifiers/link targets and `[[Kategorie:Latexseite]]`; the English authority lines in the five solutions are TeX comments and do not render.

No source or target was edited during this audit.

## Exact audited inputs

| Role | Relative path | Bytes | SHA-256 |
|---|---|---:|---|
| German worksheet | `authority/expanded/worksheet02_source.de.tex` | 10,171 | `c645aacb16233d832b492315379b0251c33fa52db6b2e7ac24be4ecc9600d3ad` |
| Indonesian worksheet | `source/units/unit-02/worksheet02.id.tex` | 10,327 | `7a032c8f2ce6bd3bdf728f419c1d006e6fe0d02760f469e591bff7121df038a3` |
| German solution 1 | `authority/expanded/worksheet02_exercise01_solution_source.de.tex` | 647 | `6dcc38f066a8350fdba67145857c168e1b6ca532c07af0a8f34ee2b954ad9432` |
| Indonesian solution 1 | `source/units/unit-02/worksheet02_exercise01_solution.id.tex` | 951 | `bf0788c3f5cc77324bca5dfc1a899b5410fa5a8312da7594b85993c9245a45fe` |
| German solution 2 | `authority/expanded/worksheet02_exercise02_solution_source.de.tex` | 999 | `a92e556f50d2216192fc61703eea4bae3d233ab632c8eedb19bd35dec2ed89b0` |
| Indonesian solution 2 | `source/units/unit-02/worksheet02_exercise02_solution.id.tex` | 1,302 | `04da52a11f6ffd7ebc84ec1f70fc1ddef38d8bafc5cb4831cf13e4470849b34c` |
| German solution 7 | `authority/expanded/worksheet02_exercise07_solution_source.de.tex` | 1,131 | `90d9007e6a313dcbc4614045f0831b826f7a9af82897e17a36fbce08088ef92b` |
| Indonesian solution 7 | `source/units/unit-02/worksheet02_exercise07_solution.id.tex` | 1,440 | `91b527da12609ba9d53dc2126758a0a3b3f093cfd3f6e4f8de7a4af43894702a` |
| German solution 12 | `authority/expanded/worksheet02_exercise12_solution_source.de.tex` | 4,592 | `3191adb6fbfaf1be11c0e7a061468a4fd6fe9235cd0dea40771ec97bd10f970f` |
| Indonesian solution 12 | `source/units/unit-02/worksheet02_exercise12_solution.id.tex` | 4,950 | `00b8cc6b9fb19b3379662a9de94602db38a758254725657b1d0b0dfcbd25a1a1` |
| German solution 13 | `authority/expanded/worksheet02_exercise13_solution_source.de.tex` | 2,060 | `6896eb6a4a6f4c25bcfaab674847dcd78bc079cfd6c58b3b8542c5c220d85e7b` |
| Indonesian solution 13 | `source/units/unit-02/worksheet02_exercise13_solution.id.tex` | 2,408 | `5479516a09a8614a284bda99fa67fc412c17ef39d0c93dbe2a105c99b7e00ef9` |

## Structural and mapping checks

All six source/target pairs have identical TeX-command sequence, environment sequence, inline-math sequence, display-math sequence, and brace profile. Formula-bearing macro calls are byte-equivalent after whitespace normalization except for two legitimate reader-facing changes:

1. The worksheet translates `f \text{ differenzierbar}` to `f \text{ terdiferensialkan}` inside the definition of `M`.
2. Indonesian solution 1 adds a final period through the punctuation argument of the last `\mathdisp`; the mathematical expression is unchanged.

All other checked protected and extended formula calls are exact, including `\vergleichskette`, `\maabb*`, `\mathl`, `\mathdisp`, and both aligned-chain forms. Link targets, input identifiers, category markers, and the order of all exercise blocks are preserved.

The five supplied solutions map correctly:

| Solution | Worksheet task | Mapping result |
|---:|---|---|
| 1 | Derivative of `\langle f(t),g(t)\rangle` | Exact |
| 2 | Derivative of `\lVert h'(t)\rVert` for `h'(t)\ne0` | Exact |
| 7 | Unit normal field of the embedded torus | Exact |
| 12 | Gauss map of the ellipse and an explicit inverse | Exact |
| 13 | Bijectivity of the ellipse Gauss map | Exact |

## Release blockers inherited from the German authority

### B1 — P1 — Solution 2 contains a false derivative chain

German lines 17 and 29–31, faithfully reproduced at Indonesian lines 21 and 33–35, first extend `u_1=h'(t)` merely to an **orthogonal** basis and then treat the coordinate norm as Euclidean; that equality requires an orthonormal basis. More decisively,

`(\sqrt{h_1'(t)^2+\cdots+h_n'(t)^2})'`

is given a numerator `h_1(t)h_1'(t)+\cdots+h_n(t)h_n'(t)`. The numerator must instead be

`h_1'(t)h_1''(t)+\cdots+h_n'(t)h_n''(t)`.

The last displayed equality states the correct coordinate-free answer, but it does not follow from the preceding false lines. Recommended repair: replace the proof with

`\frac{d}{dt}\lVert h'(t)\rVert^2=2\langle h'(t),h''(t)\rangle`

and divide by `2\lVert h'(t)\rVert`, using the stated nonzero hypothesis.

### B2 — P2 — Exercise/solution 12 omits the required orientation

Worksheet lines 422–427 ask for “the” Gauss map of the ellipse and its inverse without fixing an orientation. A Gauss map is determined only after choosing one of the two unit normal fields. Solution 12 silently selects the normalized gradient of `\alpha x^2+\beta y^2`; the antipodal choice gives the other map and another inverse. Add to the task and solution that the orientation is the one induced by that gradient (or explicitly accept both choices).

### B3 — P2 — Solution 13 skips the step that proves the positive factor is one

German line 58, faithfully translated at Indonesian line 62, observes that the two unnormalized normal vectors differ by a positive factor `c`, then immediately declares the vectors equal. Equality of normalized vectors alone does not imply equality of the originals. The missing argument is short but essential: if `(x,y)=c(z,w)` and both points lie on `\alpha x^2+\beta y^2=1`, then `1=c^2`; since `c>0`, `c=1`. Add this step before concluding injectivity.

## Other upstream defects and omissions

### U1 — P2 — Wrong ambient dimension in the surface-of-revolution task

Worksheet German line 322 and Indonesian line 319 place the graph-derived rotational surface from Lemma 2.1 in `\mathbb R^n`. The cited construction is `I\times\mathbb R\times\mathbb R\subset\mathbb R^3`; without a separately defined higher-dimensional construction, this should be `\mathbb R^3`.

### U2 — P2 — Stray literal `m` in the antipodal-map display

The final punctuation argument of the antipodal map is `{m}` in German line 383 and Indonesian line 380. This is preserved exactly but will render as a stray `m`. Replace it with the appropriate empty or punctuation argument.

### U3 — P3 — Torus defining function needs an explicit domain

Solution 7 differentiates a function containing `\sqrt{x^2+y^2}` and divides by that radius. This is valid on an open neighborhood of the torus because `R>r>0` keeps the torus away from the `z`-axis, but the authority never states the domain restriction `x^2+y^2>0`. Adding it would make the normal-field construction fully explicit.

## Indonesian quality and terminology

Terminology is consistent with the Unit 1/Unit 2 reader conventions: `hasil kali dalam`, `berparametrisasi panjang busur`, `hipermuka terdiferensialkan`, `medan normal satuan`, `permukaan putar`, `orientasi`, `pemetaan Gauss`, `pemetaan antipodal`, `isometri linear`, and `isomorfisme linear` are used coherently. No sign, inequality, domain, point variable, or quantifier was mistranslated.

Non-blocking polish notes:

- Worksheet line 49 begins with a detached comma after a display; reflow as prose (`jika ... berlaku, maka ...`) or place punctuation through the display macro's punctuation argument.
- `pernyataan konversnya` at worksheet line 334 is understandable but less natural than `pernyataan sebaliknya`.
- `suatu dilatasi \mathbb R^n` at worksheet line 345 is smoother as `suatu dilatasi pada \mathbb R^n`.
- `beberapa titik ... dicapai sebanyak tak berhingga kali` at worksheet line 499 is clearer as `terdapat titik-titik ... yang dicapai tak berhingga kali`.
- `Kita klaim` in solution 12 line 43 is a direct calque; `Kita akan menunjukkan` is more idiomatic.
- The visible link label `Fakta` in solution 13 line 43 should use the reader's established theorem/lemma label if the referenced result is numbered as such.

## Terminal audit decision

**FAIL for mathematics-correct release; PASS for translation fidelity and exact solution mapping.** Resolve B1–B3 before treating the supplied solutions as complete. U1–U3 and the style notes are discrete, bounded follow-up edits rather than evidence of a systemic translation problem.
