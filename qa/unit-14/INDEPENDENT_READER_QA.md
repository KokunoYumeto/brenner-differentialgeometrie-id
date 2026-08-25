# Independent reader and mathematics QA — Unit 14

Status: **pass**  
Date: 2026-08-25  
Scope: Lecture 14, Worksheet 14, and exact source-supplied Solutions 5, 6, 9, 11, 12, 13, and 14.

## Reader review

The Indonesian lecture and worksheet were compared directly with the frozen German expanded sources. The final reader uses natural field language for differential forms, exterior products, cotangent bundles, Pfaff forms, pullback, local coordinate expressions, Jacobian minors, and top forms. Reader-visible German remains only inside deliberately preserved internal source locators and category identifiers.

The review repaired an unbound point phrase, replaced literal `ruang sekitar` with `ruang ambien`, rewrote the pullback definition so its alternating-map syntax is unambiguous, standardized the result term as `bentuk diferensial tarik balik`, removed awkward manifold reduplication, made the chart-domain reference explicit, restored one missing display stop and one omitted `juga`, and preserved the established continuously-differentiable terminology.

## Mathematical review

Seven high-confidence source defects were independently checked and corrected only in the Indonesian target:

1. Pullback is restriction only when the map is the inclusion.
2. The coordinate exterior-basis proof requires `j_1 < ... < j_k`, not equality.
3. A target component of a map into `R^m` is indexed through `m`, not `n`.
4. Top forms transform like oriented densities; positive measure densities require the absolute Jacobian determinant.
5. Exercise 2's differentiability-class form space is on `M`, not undefined `U`.
6. Supplied Solution 5 requires `D(f \circ \alpha^{-1})`, not `Df \circ \alpha^{-1}`.
7. Supplied Solution 12 places `\cos(r^2st)` only in the third intermediate wedge summand; its final collected coefficient was already correct.

The Jacobian-minor computation in Solution 9, the normalized-circle pullback in Solution 11, the scalar-product pullback in Solution 13, and the chain-rule proof in Solution 14 were recomputed and agree with the final target. No additional high-confidence mathematical defect was found.

## Closure

- 18 exercises in exact source order: 14 practice and four graded.
- Graded point values: `6, 4, 4, 6`, totaling 20.
- All 18 source hint fields remain blank.
- Exactly seven supplied solutions: 5, 6, 9, 11, 12, 13, and 14.
- No solution is invented for the remaining eleven exercises.
- Zero media occurrences and zero admitted binaries.
- Nine translation receipts pass command, environment, inline/display math, protected-call, and brace-profile checks.
- All corrections and protected reader-text translations are explicit in `00_control/ADVERSE_LEDGER.csv` and hash-bound by the Unit 14 correction manifests.

No cumulative PDF, HTML, backend, publication, or public-readback gate is claimed at this per-unit boundary.
