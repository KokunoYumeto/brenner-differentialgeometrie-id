# Independent reader and mathematics QA — Unit 15

Status: **pass**  
Date: 2026-08-25  
Scope: Lecture 15, Worksheet 15, and the exact source-supplied Solutions 1, 11, 12, and 13.

## Reader review

The complete Indonesian unit was compared directly with the frozen German expanded sources. The final reader uses natural field language for positive volume forms, volume measures, null sets, integration on manifolds, orientation induced by a nonvanishing top form, volume forms on regular fibers, graph hypersurfaces, pullback, and path integrals. Dimension phrases now read as `manifold diferensiabel berdimensi n`; continuously differentiable maps and curves use the explicit natural form `yang terdiferensialkan secara kontinu`. Mechanical reduplication and German-order chart sentences were removed without altering identifiers or mathematics.

No reader-facing German remains outside deliberately preserved source locators, semantic identifiers, and category identities. All four headings, three definitions, five fact/proof blocks, three remarks, three examples, three partial-proof parts, five no-edit markers, 26 wiki targets, 120 inline-math spans, 135 math-bearing macro invocations, and five hidden fact identifiers remain accounted for.

## Mathematical review

The independent comparison confirmed and bound the following high-confidence corrections:

1. The source's sigma-finiteness conclusion is true in the stated measurable setting but lacked its countable bounded-density argument; the target supplies that argument and keeps Exercise 15.2 as the continuous special case.
2. The local top form in the orientation proof has degree `m`, not `1`.
3. The graph-defining map has domain `V × R`, because `h` is defined on `V`; its determinant components follow the declared column convention for the tangent vectors.
4. Chart independence requires `T ⊆ U_1 ∩ U_2`, not the source's comma notation.
5. A measurable pulled-back coefficient need not be integrable. The definition and coordinate computation now make existence of the path integral conditional on integrability.
6. Supplied Solution 1 separates the finite-subcover cardinality from the dimension and takes the bound on the compact coordinate-ball closure.
7. Supplied Solution 12 parenthesizes `d(u^2)`, `d(uv)`, and `d(t^2)`.
8. The Exercise 13 body and supplied solution consistently use the product `u^{-1}v^{-1}`; that coherent mathematics is preserved while the contradictory title metadata is disclosed.

The four supplied-solution computations were independently recomputed: the finite-volume comparison in Solution 1, the exact line integral in Solution 11, the two pullback calculations in Solution 12, and the two-parameter pullback in Solution 13 agree with the final target. No other high-confidence mathematical defect remains.

## Closure

- 16 exercises in exact source order: 13 practice and three graded.
- Graded point values: `4, 4, 5`, totaling 13.
- All 16 source hint fields remain blank.
- Exactly four supplied solutions: 1, 11, 12, and 13.
- No solution is invented for the remaining twelve exercises.
- Zero media occurrences and zero admitted binaries.
- Six translation receipts and six preparation receipts pass.
- Every target correction is explicit in `00_control/ADVERSE_LEDGER.csv` and the exact final targets are hash-bound by the Unit 15 manifests and final receipt.

No cumulative PDF, HTML, backend, publication, or public-readback gate is claimed at this per-unit boundary.
