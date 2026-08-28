# Independent reader and mathematical QA — Unit 21

Date: 2026-08-28

Status: **PASS for the bounded Unit 21 translation boundary.** This is not a
cumulative Units 1–21 release gate.

## Scope and method

The review compared the exact frozen German Lecture 21 and Worksheet 21
expansions with the complete Indonesian targets and all four source-supplied
solution pages. It checked the 20-exercise source order, fifteen practice and
five graded items, the 24-point total, blank hint fields, four supplied
solutions, formulas and hypotheses, terminology, three media identities and
rights, reader prose, and every page of the unit-only A4 render. Internal
German MediaWiki link targets and LaTeX dispatch keys remain control identities
and are intentionally not localized.

## Findings closed in the target

1. `O011-CORR-0285` and `O011-CORR-0286`: the sphere-circle figure now carries
   its exact CC BY 3.0 license, and `Not-star-shaped.svg` credits its actual
   creator, WillT.Net, rather than the copied creator from another figure.
2. `O011-CORR-0287`: the closed-ball example applies the regular-level theorem
   to the smooth squared norm at regular value `r^2`, with `r>0`, rather than
   to the Euclidean norm at the origin.
3. `O011-CORR-0288` and `O011-CORR-0289`: the boundary-orientation proof places
   the comparison basis in ambient `R^n`, and the boundary chart transition
   uses the declared coordinate domains `V_1` and `V_2`.
4. `O011-CORR-0290`, `O011-CORR-0291`, and `O011-CORR-0292`: supplied Solution
   21.7 uses the boundary symbol `\partial H`; supplied Solution 21.10 uses the
   actual difference quotient and the chart-coordinate vector
   `T_P(\alpha)(v)`.
5. `O011-CORR-0295`: Solution 21.10 now states the exact sign information:
   `t` is negative and the first coordinate is nonpositive, so the first
   quotient coordinate is nonnegative. Equality at a boundary-tangent path is
   no longer excluded.
6. `O011-TRANS-0293`, `O011-TRANS-0296`, `O011-TRANS-0297`, and
   `O011-TRANS-0298`: the complete reader-language pass is idiomatic and uses
   the admitted forms `ruang topologis Hausdorff`, `tutupan terbuka`, `balok
   tertutup`, and `permukaan bola satuan`.
7. `O011-ACC-0294`: exact hash-identical underscore-normalized aliases make the
   two space-bearing SVG print derivatives resolvable without changing their
   canonical Commons filenames or rights records.

## Deterministic and visual evidence

- Lecture target: 24,518 bytes; SHA-256
  `207266db84e4ce06f17d7fa9dd82383597b1dc54afd989f8ae082e222826fff3`.
- Worksheet target: 10,101 bytes; SHA-256
  `8418192976181a42355d9349af05e4683333d5041f0fd996c77d366820a36946`.
- Supplied Solutions 21.7, 21.10, 21.12, and 21.13 have SHA-256 values
  `a8dc37a46a7f3a63e35e6e6f2e449f2f9ea1e54e5dd8a787d657f7b7bcd9b847`,
  `0bf50584af30cec1246553e5ed796b2f81ae9e00f634c19b2ebbe6120ff795a8`,
  `5dcd64ff8208506ca60e1b0a730f92af3db3f838c465b296f2d5a69b4c6e56a4`,
  and `ea2841a4d57af79e727edee65dbea21371c70cb4a2a13d2799a71ddfda6a6bc2`.
- The unit-only A4 QA reader is 18 pages and 1,486,293 bytes, SHA-256
  `d423260ff0bf8525e4aea9ff68ae3d4f435b12c66685dacebc5bdfda567a2840`.
  Two independent three-pass builds are byte-identical. The final log contains
  no overfull or underfull boxes, undefined commands, duplicate hyperlink
  destinations, or LaTeX/package warnings.
- Visual inspection covered all 18 rendered pages, with full-resolution checks
  of the opening definition and figure, the corrected closed-box example, the
  graded worksheet and unit-sphere wording, the two solution pages around the
  repaired sign argument, media attribution, and license page. The 22 mm A4
  text block is centered; figures are sharp; no clipping, overflow, or orphaned
  conclusion remains.

The next executable action is to generate and independently verify the formal
post-correction receipt, persist exact Unit 21 hashes and the source cursor,
publish the bounded source checkpoint, and then freeze Unit 22 in source order.
