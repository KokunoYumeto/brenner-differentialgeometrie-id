# Independent reader and mathematical QA — Unit 20

Date: 2026-08-28

Status: **PASS for the bounded Unit 20 translation boundary.** This is not a
cumulative Units 1–20 release gate.

## Scope and method

The review compared the frozen German Lecture 20 and Worksheet 20 expansions
with the complete Indonesian targets and all five source-supplied solution
pages. It checked the 24-exercise occurrence order, the 19 practice and five
graded items, the 22-point total, blank hint fields, five solution links,
mathematical formulas, finite-regularity hypotheses, terminology, reader prose,
and visible A4 output. Internal German MediaWiki link targets and LaTeX dispatch
keys are control identities and are intentionally not localized.

## Findings closed in the target

1. `O011-CORR-0275`: naturality of the exterior derivative under pullback now
   requires a twice continuously differentiable map. A merely `C^1` map does
   not make the pullback of a positive-degree `C^1` form differentiable, and
   the source proof uses `d(d\psi_i)=0`.
2. `O011-CORR-0276`: the malformed `\beta^{-1^*}` in the chart-independence
   display is now the pullback by the inverse chart, `\beta^{-1*}`.
3. `O011-CORR-0277`: exact forms and the corresponding Euclidean exercise are
   restricted to positive degree; degree zero would invoke an undefined
   degree-minus-one form.
4. `O011-CORR-0278` and `O011-CORR-0279`: the half-space formula is explicitly
   positive-dimensional, the zero-dimensional case is the one-point
   convention, and the real half-line is `[0,\infty)` rather than an interval
   closed at infinity.
5. `O011-CORR-0280`: the malformed ASCII solution to Exercise 20.7 is replaced
   by a valid calculation of `d\omega=0` and the explicit primitive
   `x^2-x\sin y`.
6. `O011-CORR-0281`: the Exercise 20.14 source page is explicitly marked
   unfinished. The Indonesian reader preserves its meaningful fragment but
   visibly states that the candidate differentiates to `-n\omega` under its
   own assumptions and that the required global construction on arbitrary
   open sets is absent. The empty source equation is not presented as content.
7. `O011-TRANS-0282`, `O011-ACC-0283`, and `O011-ACC-0284`: terminology follows
   the admitted ledger; coordinate-image and coordinate-neighborhood prose is
   unambiguous; the long fixed-coordinate tuple is reflowed; and the opening
   map's punctuation no longer renders on an isolated line.

## Deterministic and visual evidence

- Lecture target: 25,211 bytes; SHA-256
  `4f6b2af7f168bec59cb4c8a02bdb66ade520f7ab110098ed6b24ca4be9b98fb7`.
- Worksheet target: 9,695 bytes; SHA-256
  `ccbae6a87a2e11d6cbcb076f27d16bb97c520ba5806a477a2d4b12fa5d9c3b9a`.
- Corrected Exercise 20.7 solution: 672 bytes; SHA-256
  `2fc6ac77b0c44e4f25eb59497a0d58df5e073591b1b3a900b1b53b03601358af`.
- Disclosed Exercise 20.14 fragment: 1,700 bytes; SHA-256
  `efcb047ffdae25fd7d0a89dd92fa2b32424d87595ca46df19f1411fb36325c79`.
- Unit-only A4 QA reader: 16 pages; 363,565 bytes; SHA-256
  `a5eff2cb30b006d4642d6dd7fdb32e5bc434930e8c77700e3a1bb4434e7f0498`.
  Two independent three-pass builds are byte-identical. The final log contains
  no overfull or underfull boxes, undefined commands, or LaTeX/package warnings.
  Visual inspection covered the opening, theorem and chart-independence pages,
  half-space definition, worksheet body, corrected Exercise 20.7 solution, and
  disclosed Exercise 20.14 fragment. Content is centered within the 22 mm A4
  text block and no clipping or orphan punctuation remains.

The next executable action is to generate and independently verify the formal
post-correction receipt, persist the Unit 20 cursor and hashes, and then freeze
Unit 21 in source order.
