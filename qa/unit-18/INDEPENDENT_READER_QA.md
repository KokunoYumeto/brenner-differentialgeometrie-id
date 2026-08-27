# Independent reader and source-math QA — Unit 18

Date: 2026-08-26  
Scope: frozen Lecture 18, Worksheet 18, and the four source-supplied solutions for Exercises 8, 11, 13, and 14. This review compared each German source fragment directly with its Indonesian target; it did not infer a solution layer where the source has none.

## Exact reviewed surfaces

| Surface | Frozen source SHA-256 | Final id-ID SHA-256 |
|---|---|---|
| Lecture 18 | `7fc98f4cdd977e4a5acb4dea5d61807251ac850fe102b8f0ecc1251f755d3c3e` | `7d7bc9d97d9719790d1cd37f78fae74f9cb318a4f29b8a7c295e24deb6aed298` |
| Worksheet 18 | `ee2744cd813459a644fb382e931ae1f9a0f3b9dd8889532dfd9d49acd30de738` | `6710aad75c6a8132d0d255548cf19ea6d184999386a81f786061b0f02546d759` |
| Supplied Solution 8 | `aa7c364802a08ecf65a15cf05b5c04a9cd91fb2f695f123cb531a867624aca9b` | `b33f25142ea1d417660de331a39252483fe081d456f3f32db19e4772a2cedf0f` |
| Supplied Solution 11 | `3a0fdd6356c37ddf28071138df7ba9cc9cac60af378cfeedc60d4b1c18198085` | `e602b8a63785e6bd356394d7e09d75a77203a3863efe5e6845f035e638dc409d` |
| Supplied Solution 13 | `7a0e047e2c6d90bb590a2f78e2198860f78917cfaa9019d0e68ba21aae1b4f10` | `2c618c487cbb8cccf300b3333c645f79519f39640dac00c664c25963e2935ec3` |
| Supplied Solution 14 | `91d82fb120103490b619000640f5fbb7a30d8d2f23cf5c5ffe28b98337763528` | `f1ee3d9a587a96a1315a31b45ee5483b494951018bd2082674bd0fed9468b307` |

## Closure and topology

- The frozen worksheet contains exactly 21 exercises: 16 practice and 5 graded exercises. The graded point values are `4, 3, 4, 4, 4`, totaling 19.
- Every one of the 21 hint fields is blank in the authority. The Indonesian edition therefore does not present a source-supplied hint layer.
- Exactly Exercises 8, 11, 13, and 14 have source-supplied solutions. All four and only those four are translated here; the other 17 solutions are absent and were not invented.
- Those four target files use the reader/exporter's canonical `worksheet18_exerciseNN_solution.id.tex` topology. Their earlier noncanonical filenames were removed after byte-identical renaming, so the cumulative solution census discovers exactly indices 8, 11, 13, and 14.
- All six canonical `verify_unit_translation.py` receipts pass. Command, environment, inline/display-math, protected-call, brace-profile, and declared-delta checks therefore agree with the frozen sources, except for the exact correction-manifest deltas below.
- All six `prepare_unit_tex.py` receipts bind the final target bytes to deterministic build fragments. Category markers were removed only in generated build copies; the semantic target files remain intact.

## Mathematical/source findings

1. `O011-CORR-0210`: the signless pullback integration formula needs an orientation condition. The target equips the domain with the pullback orientation and selects positive charts, so an orientation-reversing coordinate choice cannot silently flip the integral.
2. `O011-CORR-0212`: the source's ambient-linear-isometry example uses `phi(M)` without introducing `phi`. The target explicitly identifies that symbol with the ambient linear isometry under discussion.
3. `O011-CORR-0213`: the source twice writes `T_P(u_i)`, although the differential in the lemma is `T_P phi`. The target restores `T_P phi(u_i)` in both the displayed pullback identity and the following orthonormal-basis sentence.
4. `O011-CORR-0214`: the source defines only `mathbb H` but immediately uses `H` as the codomain of the disk map. The target defines `H = mathbb H` at first occurrence.
5. `O011-CORR-0215`: the frozen caption typo `Minkowsi-Form` is rendered as `bentuk Minkowski`.
6. `O011-CORR-0216`: the source's claimed vector `(x,-y,0)` is not generally tangent to `x^2+y^2-z^2=-1`. The target uses the valid tangent basis `(z,0,x),(0,z,y)` and checks
   `a^2 z^2+b^2 z^2-(ax+by)^2 = a^2+b^2+(ay-bx)^2`,
   which is strictly positive for a nonzero coefficient pair.
7. `O011-CORR-0217`: three source inner products on the hyperboloid carry the point subscript `(a,b)`, even though `(a,b)` is a disk point. The target suppresses that invalid point label; the ambient Minkowski form is constant.
8. `O011-CORR-0218`: Worksheet Exercise 5 asserts the impossible chain `I = gamma(I) subseteq R^n`. The target states the intended map `gamma: I -> gamma(I) subseteq R^n`.
9. `O011-CORR-0219`: Worksheet Exercise 7 now punctures the complex plane at the complex number `0`, while retaining `(0,0)` only in the identified real plane.
10. `O011-CORR-0220`: the frozen German spellings `Halbkreies` and `Kreies` were recorded and translated according to their unambiguous intended meanings.

The corrected hyperboloid basis was checked directly against the tangent equation `xu+yv-zw=0`; each basis vector satisfies it. The disk/half-plane formulas, the disk/hyperboloid derivative formulas, and the four supplied solution calculations were also traced term by term. No further high-confidence mathematical discrepancy was found.

## Reader-language findings

- `O011-TRANS-0211` removes a mechanical translation of German *bzw.* and improves the isometry and derivative prose without changing formulas.
- `O011-TRANS-0221` restores the established phrase `terdiferensialkan secara kontinu`, calls the requested object a circular arc, and uses `cakram` for the region whose area is requested.
- `O011-TRANS-0222` through `O011-TRANS-0225` bind the four supplied solutions' natural Indonesian renderings. Solution 11 was rearranged only enough to retain the source command order and its exact mathematical topology.
- `O011-ACC-0226` supplies the source's blank Poincaré-animation caption with a faithful Indonesian description of the conformal half-plane-to-disk transformation. It also tells readers that PDF uses the deterministic first frame while HTML and the download retain the canonical animation; the source GIF, creator credit, and CC BY-SA 3.0 rights are unchanged.
- `O011-ACC-0229` reflows the unchanged Hyperboloid2 caption into two centered lines at the clause boundary. This print-only line break keeps both lines inside the 22 mm-margin A4 text block without changing wording, mathematics, or media.
- No reader-facing German prose remains. German strings that remain are immutable MediaWiki targets, source-page identifiers, the terminal category marker removed during preparation, and the frozen source license token `gemeinfrei`; none is presented as Indonesian prose.

Result: **pass**. Unit 18's static-first animation closure is content-addressed in `ANIMATED_MEDIA_QA.json`; the unit is suitable for the parent task's cumulative reader/backend/build checks.
