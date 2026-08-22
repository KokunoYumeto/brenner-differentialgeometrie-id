# Unit 3 lecture translation findings

Status: **PASS after complete translation review, five mathematically determined target corrections, and one reader-layout correction.**

## Frozen authority and target

- Course root: `Kurs:Differentialgeometrie (Osnabrück 2023)/Vorlesung 3`, page/revision `142547/1020016`.
- LaTeX surface: `Kurs:Differentialgeometrie (Osnabrück 2023)/Vorlesung 3/latex`, page/revision `142577/807136`.
- Frozen expanded source: `authority/expanded/lecture03_source.de.tex`, 28,482 bytes, SHA-256 `c6fa222d45a2abaaa121fabbf68a76ab478d9ede7dd14f370d8e58d40887c25a`.
- Indonesian target: `source/units/unit-03/lecture03.id.tex`, 29,657 bytes, SHA-256 `769ec3b7e72159509ede182469711ce4093027de27096d5d256b88a6e7f32c16`.
- Canonical receipt: `qa/unit-03/lecture_translation.json`, status `pass`, with every hash-bound delta consumed.
- Protected correction manifest: `00_control/LECTURE03_PROTECTED_CORRECTIONS.json`, 966 bytes, SHA-256 `8beff151d17c801044d88036cb5a8b53045c0f154a5ffa8dbd5f3f90f86c2fa`.

## Complete translation audit

- Read and compared the entire 1,554-line German authority against the entire Indonesian target; this was not a sample review.
- Preserved the two section headings, four definitions, two examples, five lemma/proof blocks, their order and boundaries, five `__NOEDITSECTION__` markers, the terminal category, and the single displayed media/license occurrence.
- The canonical verifier reports source-equivalent TeX command order (1,198 commands), environment order (106 entries), 58 inline-math payloads, and 97 protected macro calls after consuming exactly the declared deltas for O011-CORR-0031 and O011-CORR-0034; UTF-8, brace topology, display mathematics, formulas, identifiers, and image locators pass.
- All seven reader-content semantic-link destinations remain byte-for-byte identical and in source order; only visible link labels were translated. The terminal category destination is also unchanged.
- A complete residue scan found no reader-facing German. German remains only inside immutable semantic destinations, plus the proper name `Osnabrück`; the Commons filename and license metadata are unchanged.
- Terminology follows the admitted shared ledger and the Unit 3 worksheet mapping (`Krümmungskreis` → `lingkaran kelengkungan`, `Schmiegkreis` → `lingkaran oskulasi`). The reviewed Unit 3 terminology set has been merged into `00_control/TERMINOLOGY.csv`.

## Authority defects and applied target corrections

These observations concern the unchanged German authority. Each correction is recorded in `00_control/ADVERSE_LEDGER.csv`; topology-changing corrections are additionally bound by `00_control/LECTURE03_PROTECTED_CORRECTIONS.json`.

### O011-CORR-0030 — zero-curvature sign case omitted (minor; corrected)

- Authority: line 929; corrected target: line 932.
- The prose says the sign is positive for positive curvature and negative “otherwise.” At a point with `\kappa(t)=0`, neither sign is negative, although `+0=-0` makes the displayed norm identity harmless.
- Applied correction: the target now says that the plus sign applies for positive curvature, the minus sign for negative curvature, and the distinction is immaterial at zero.

### O011-CORR-0031 — evolute is not defined at zero curvature (material; corrected)

- Authority: lines 937–980; corrected target: lines 940–984, especially line 975.
- The definition assumes only `\gamma'(t)\neq0` and then declares a map `M:I\to\mathbb R^2` sending every `t` to the center of the osculating circle. Earlier, that center exists only where the signed curvature is nonzero; at an inflection or straight segment its radius is infinite and there is no center in `\mathbb R^2`.
- Applied correction: the evolute domain is `\{t\in I\mid\kappa(t)\neq0\}`.

### O011-CORR-0032 — orientation-preserving reparameterization is unstated (material; corrected)

- Authority: lines 1207–1245, especially line 1223; corrected target: lines 1209–1247, especially line 1225.
- The proof writes `\alpha(t)=\gamma(\beta(t))` for “a reparameterization” and cancels powers of `\beta'(t)` as if `\beta'(t)>0`. Signed curvature changes sign under an orientation-reversing reparameterization; the displayed conclusion is valid for the increasing arc-length reparameterization constructed immediately before it, but not for an arbitrary decreasing one.
- Applied correction: the target explicitly requires an increasing reparameterization.

### O011-CORR-0033 — pointwise signed curvature lacks an orientation (material; corrected)

- Authority: lines 1249–1297; corrected target: lines 1251–1299.
- The notation `\kappa(P)` is introduced from the existence of an arc-length parametrization through `P`, but no orientation is fixed. Reversing that parametrization negates signed curvature, as the lecture itself states earlier.
- Applied correction: the target requires an oriented implicit curve and an orientation-compatible arc-length parametrization.

### O011-CORR-0034 — the zero tangent vector does not determine an orientation (minor; corrected)

- Authority: lines 1401–1434; corrected target: lines 1403–1441, especially line 1409.
- The final lemma quantifies over every `v\in T_PY` while defining `\kappa(P)` using the orientation represented by `v,N(P)`. That ordered pair defines an orientation only when `v\neq0`; the equation for `v=0` is nevertheless trivially true by linearity.
- Applied correction: the orientation-bearing quantifier is restricted to `T_PY\setminus\{0\}`, followed by the zero-vector case from linearity.

### O011-CORR-0035 — display punctuation rendered on an isolated line (minor; corrected)

- The first Indonesian draft placed one full stop after, rather than inside, a multiline equation macro. The initial PDF rendered that character alone on a separate line.
- Applied correction: the full stop now occupies the macro punctuation argument. The equation is unchanged, the translation/topology receipt passes, and the final rendered page has no isolated mark.

## Disposition

No formula, identifier, hypothesis, conclusion, or semantic destination was silently repaired. O011-CORR-0030 through O011-CORR-0035 are explicit in the adverse ledger; topology-changing deltas are hash-bound and verifier-consumed. An independent audit’s translation and semantic-link findings were repaired: primary/synonym terminology matches the worksheet, concept-bearing macro occurrences follow their source referents, and the cited Indonesian prose/layout issues are resolved. The target is incorporated in the deterministic cumulative Unit 3 build.
