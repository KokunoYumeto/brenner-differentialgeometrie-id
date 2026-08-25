# Unit 6 bilingual prose and meaning QA

Date: 2026-08-22
Scope: complete line-by-line comparison of the frozen German Lecture 6,
Worksheet 6, and all three source-supplied solutions against the Indonesian
reader targets. This review is separate from the protected-math verifier and
the post-repair mathematical audit.

## Final target witnesses

- `lecture06.id.tex`: 32,034 bytes; SHA-256
  `180c553eb556d91ba733e00f012bd0ece36c32e66704c992f0c64244ab6e05e8`.
- `worksheet06.id.tex`: 16,526 bytes; SHA-256
  `b0cf54f892e2357bd6edaf1ed87df711cffcdf164c1454e7b7d2c987faa8bca5`.
- `worksheet06_exercise02_solution.id.tex`: 2,588 bytes; SHA-256
  `772755e8e7d46abd63b2acf146fec3be01a23f57476cbea153ff14668a316ad5`.
- `worksheet06_exercise06_solution.id.tex`: 1,103 bytes; SHA-256
  `e10704fec468e5ee582e72415ef85d92ad6182a3a4207359ad10ac41b9a581ac`.
- `worksheet06_exercise09_solution.id.tex`: 595 bytes; SHA-256
  `fd027471aa6655aaf6b2d07c60e7a96cb5d13df961adca1c38d2021cc19cf39b`.

## Resolved findings

1. Eleven malformed renderings of the German indefinite article (`himpunan
   pertama suatu`) were replaced by explicit references to `$Y$` as the
   differentiable hypersurface. The later `$C^2$` qualifications remain.
2. The prose explaining a vector field along a curve was reordered so that
   `F(t) in T_{gamma(t)}Y` modifies the vector-valued curve rather than the
   subsequent differentiation operation.
3. Both closure statements in Lemma 6.7 were made grammatically complete:
   scalar multiples and sums of parallel fields remain parallel.
4. The proof of Theorem 6.9 now distinguishes the cited local
   Picard--Lindelof result from global continuation of a linear system with
   continuous coefficients. This source gap is ledgered as
   `O011-CORR-0069`.
5. Worksheet Exercise 8 no longer identifies an affine hyperplane directly
   with a vector space. All tangent spaces are canonically identified with its
   common linear direction space `V=Y-P`; the repair is disclosed and ledgered
   as `O011-CORR-0068`.
6. The supplied solution to Exercise 6 now states correctly that `F'(t)` is a
   scalar multiple of the normal, rather than saying that an ambiguously named
   vector “depends linearly” on it.
7. Missing copulas, two awkward sphere openers, the holonomy sentence, the
   cross-reference to Example 6.11, and `matriks Jacobi` terminology were
   normalized without changing mathematical content.
8. Edition notes for the pointwise Leibniz identity, the excess parenthesis in
   `A_ij`, and both corrected matrix columns were made exact and reader-facing.
9. A redundant pair of math delimiters around the existing `\mathl{aF}{}`
   macro in Worksheet Exercise 3 was removed after the first build exposed the
   nested-math error. This restored the source macro topology and changed no
   mathematical content.
10. The two longest right-hand sides in the corrected Leibniz derivation were
    reflowed across aligned continuation lines after the first rendered reader
    exposed right-margin clipping. Every term and equality is unchanged; the
    layout delta is bound to the already ledgered product-rule surface
    `O011-CORR-0055`.
11. Final rendered-text inspection found ten `\definitionsverweis` calls with
    a missing empty third argument. The macro had consequently consumed the
    next prose token, producing forms such as `geodesiktepat` and
    `paralelsepanjang`. Restoring the source macro arity repairs word spacing
    without changing the intended text or mathematics.
12. The final all-page render exposed eight punctuation marks
    following mapping or comparison macros. Their periods and commas were
    moved into the macros' terminal punctuation arguments so they remain
    attached to the corresponding display instead of becoming orphan lines.
    No mathematical token, statement order, or punctuation value changed;
    the normalization is recorded in
    `00_control/LECTURE06_PROTECTED_CORRECTIONS.json` and enforced by the
    post-repair verifier.

## Closure result

The audit found no unledgered omission of a German prose block, exercise part,
formula, or source-supplied solution step. The three source-supplied solution
surfaces remain exactly Exercises 2, 6, and 9. Exercise 9 required no repair.
Protected-structure verification, the independent post-repair mathematical
receipt, and the final PDF render remain separate required gates.
