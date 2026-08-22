# Unit 4 post-repair mathematics and topology audit

**Verdict: PASS.** No unresolved mathematical, topological, formula, ordering, exercise, point-value, hint, or supplied-solution defect was found in the four current Indonesian Unit 4 targets bound below. All eight adverse-ledger determinations `O011-CORR-0038` through `O011-CORR-0045` are mathematically justified and are correctly realized in the current targets.

Audit date: 2026-08-22.

## Scope and boundaries

This audit compared only:

- the four frozen Unit 4 authority surfaces under `authority/expanded/`;
- the four current `source/units/unit-04/*.id.tex` targets;
- `00_control/ADVERSE_LEDGER.csv` rows `O011-CORR-0038` through `O011-CORR-0045`;
- the four Unit 4 protected-correction manifests; and
- the four current Unit 4 translation receipts.

The audit read every mathematical statement and formula in the lecture, every worksheet exercise in order, every point and hint slot, and both supplied solutions. It did not rebuild or edit the PDF, translations, authority bundle, backend, controls, receipts, or sibling units.

## Exact authority and target identities

| Surface | Bytes | SHA-256 |
|---|---:|---|
| `authority/expanded/lecture04_source.de.tex` | 26932 | `610c85e2cb9838a2ce1deb488ceca6cb7d2ee2ab47f1e657d5df7488796f8402` |
| `source/units/unit-04/lecture04.id.tex` | 28602 | `60a7a2cbfc96a9a510bfff935f40722458c85031214eeaf8ccf4e8df2af2bc81` |
| `authority/expanded/worksheet04_source.de.tex` | 11052 | `81f8d9667581e0e6507dd1684b136c23f3352d1cabf2e8c4013daeb0a312cd00` |
| `source/units/unit-04/worksheet04.id.tex` | 11797 | `f3721ced8fc5db02dd600ff81f02455ec724f34c7a085f4280d8f5c2d14873f8` |
| `authority/expanded/worksheet04_exercise07_solution_source.de.tex` | 2623 | `a0df2279b1dbae5bff1a4e50385349080bd8734e20d1a6edec83e528045dc63e` |
| `source/units/unit-04/worksheet04_exercise07_solution.id.tex` | 1983 | `6003193ccef4456ffcbe42e67068202567ceafe4897363aa4833b266aaf855d5` |
| `authority/expanded/worksheet04_exercise10_solution_source.de.tex` | 2633 | `76a2f5db7eb835b19b924418ae2c1b0cfbcd8cd2d5acc387f695f71cbb069a35` |
| `source/units/unit-04/worksheet04_exercise10_solution.id.tex` | 2661 | `a5d22c14d32b03265e532b34636da4d656d838cefe268c92d1ac3ec1ebd27de4` |

Each source and target byte count and hash exactly matches its current translation receipt.

## Evidence identities and reconciliation

| Evidence | Bytes | SHA-256 | Result |
|---|---:|---|---|
| `00_control/ADVERSE_LEDGER.csv` | 15319 | `c2d9b4bc6a5fd51e0f1b5ad5a314badff19f3bbfee04d6afc38f7005ebde47c5` | Rows 0038–0045 read and audited |
| `00_control/LECTURE04_PROTECTED_CORRECTIONS.json` | 1933 | `bbbefb6776c283045ee061fb2113f26d33de6789a54c3afcc08726c270208e3c` | 0041 and 0043 allowed deltas consumed; 0042 evidence-only binding verified |
| `00_control/WORKSHEET04_PROTECTED_CORRECTIONS.json` | 944 | `248901c4028c096195502727eeb1dadb2dea562394ec2de8d90b5252e9de5131` | 0038 allowed deltas consumed |
| `00_control/SOLUTION04_07_PROTECTED_CORRECTIONS.json` | 1797 | `f28d495a184a658a404a3ac039b4d812cbd30bd169f1c23d2984360d734dd1f2` | 0039 allowed deltas consumed |
| `00_control/SOLUTION04_10_PROTECTED_CORRECTIONS.json` | 1797 | `43e7ed9e660b52376e7c8ad5df9562d545011e86544f55c09f3100318c12a778` | 0040 allowed deltas consumed |
| `qa/unit-04/lecture04_translation.json` | 1314 | `bac1e9f1577535848e1e7fc455f7a651952d8285050d56a45656e9dead6c78b2` | `pass`, zero failures |
| `qa/unit-04/worksheet04_translation.json` | 1104 | `60e22fe368748abdad2b2153321723ba6f16479f1afd615697747f9b8912d0b3` | `pass`, zero failures |
| `qa/unit-04/worksheet04_exercise07_solution_translation.json` | 1205 | `add512ed7a75c29cc00e306d9f8fe3617b8b86d1443467bea1ec8ae7ecb02d2b` | `pass`, zero failures |
| `qa/unit-04/worksheet04_exercise10_solution_translation.json` | 1206 | `fd75703de97c3e53ea528a9bb862fce76645f6de31f2865cc54f99d0bf8d5297` | `pass`, zero failures |

The receipts report equality or an explicitly declared delta for command order, environment order, inline math, display math, protected macro calls, and brace profiles; all declared deltas were consumed. The lecture receipt also reports the 0042 evidence-only `mathl` occurrence as verified. Corrections 0044 and 0045 change ordinary statement text rather than a protected TeX surface, so they are not entries in the protected-correction manifest; their exact C² hypotheses were checked manually below.

## Lecture closure

The authority and target each contain one definition, six proved facts, and two examples in the same order.

| Surface | Mathematical audit |
|---|---|
| Introduction and Definition 4.1 | The directional derivative description, tangent-domain/codomain, and sign convention `L_P(v)=-D_vN(P)` are preserved. Dependence on the chosen unit normal is stated. |
| Lemma 4.2 | The normalized gradient is C¹ under the C² hypothesis. Differentiating `<N,N>=1` proves `D_vN(P)` is tangent, so `L_P` is a linear tangent-space endomorphism. |
| Lemma 4.3 | For a regular plane level curve, the shape operator is multiplication by the signed curvature; the orientation qualification is retained. |
| Sphere example 4.4 | With inward normal `N=-(x,y,z)/r`, `D_vN=-v/r`, hence `L_P(v)=v/r`. The displayed basis and reciprocal-radius conclusion agree. |
| One-sheeted hyperboloid example 4.5 | The Jacobian of `N=(x,y,-z)/sqrt(x²+y²+z²)`, both tangent bases, triangular matrix, and two eigenvectors/eigenvalues are algebraically correct. The use of `x²+y²-z²=1` in replacing `z²-x²-y²` by `-1` is consistent. |
| Lemma 4.6 | Differentiating `<gamma'(t),N(gamma(t))>=0` yields `<gamma''(0),N(P)>=<L_Pv,v>`; the corrected normal argument is present. |
| Theorem 4.7 | The normalized-gradient product rule reduces the bilinear form to the Hessian of `h`; Schwarz symmetry proves self-adjointness. Signs and normalization are correct. |
| Corollary 4.8 | Real diagonalizability and mutually orthogonal eigenspaces follow correctly from self-adjointness and the real spectral theorem. |
| Graph lemma 4.9 | For graph basis `X_i=e_i+f_i e_n`, the metric is `G=I+gg^T` and the second fundamental form is `B=Hess(f)/sqrt(1+||g||²)`. Since `GA=B`, the operator matrix is correctly repaired to `A=G^{-1}Hess(f)/sqrt(1+||g||²)`. |

No statement, proof step, displayed formula, sign, orientation dependency, or theorem/example order remains mathematically defective.

## Worksheet closure

The authority and target each contain 15 exercises in the same order. Exercises 1–11 are unpointed; exercises 12–15 carry exactly `4, 5, 4, 6` points. All 15 hint slots are empty in both surfaces. Supplied-solution markers occur exactly on exercises 7 and 10.

| Exercise | Surface checked | Result |
|---:|---|---|
| 4.1 | Nonzero linear form, affine level hyperplane, zero shape operator | PASS |
| 4.2 | Punctured standard cone, corrected rotational curve, normalized-gradient derivative limit | PASS |
| 4.3 | Standard cylinder at `(1,0,z)`, circular tangent curve, derivative limit | PASS |
| 4.4 | Cylinder shape operator is nonzero and non-bijective | PASS |
| 4.5 | A ruled surface can contain a line whose direction is not in the shape-operator kernel | PASS |
| 4.6 | Product hypersurface `Z=Y x R^m`, relation between `L_Q` and `L_P`, corrected C² regularity | PASS |
| 4.7 | Embedded torus with `0<r<R`, unit normal, two requested directional derivatives | PASS |
| 4.8 | Graph `f(x,y)=xy`, full shape operator and spectral data | PASS |
| 4.9 | Pullback by a linear isometry, tangent-space identification, corrected C² regularity | PASS |
| 4.10 | Ellipsoid `x²+y²+2z²=4` at `(1,1,1)`, diagonal shape-operator matrix | PASS |
| 4.11 | Reversal of orientation changes `L` to `-L` while preserving eigenspaces | PASS |
| 4.12 (4 points) | Hyperboloid at `(0,y,z)`, stated tangent basis, matrix and spectral data | PASS |
| 4.13 (5 points) | Ellipsoid `x²+2y²+5z²=11` at `(2,1,1)` | PASS; the point satisfies the equation |
| 4.14 (4 points) | Quadric hypersurface in `R^4` at `(1,1,1,1)` | PASS; the point satisfies the equation |
| 4.15 (6 points) | Graph `f=x³y⁵` at `(0,0,0)`, `(0,1,0)`, and `(2,1,8)` | PASS; all graph points and requested spectral outputs are preserved |

## Supplied-solution closure

### Exercise 4.7

Writing `rho=sqrt(x²+y²)` and `A=(x-xR/rho, y-yR/rho, z)` gives `grad(h)=2A` and `||A||=r` on the torus, so `N=A/r` is a unit normal there. At `P=(R-r,0,0)`:

- `A(P)=(-r,0,0)`;
- `D_vA(P)=(0,-r/(R-r),0)` and is orthogonal to `A(P)`;
- `D_wA(P)=(0,0,1)` and is orthogonal to `A(P)`.

The normalized-vector derivative therefore gives exactly `D_vN(P)=(0,-1/(R-r),0)` and `D_wN(P)=(0,0,1/r)`. All three requested parts are completed and the malformed/incomplete authority solution is not propagated.

### Exercise 4.10

For `Y: x²+y²+2z²=4`, the target's extension `M=(x,y,2z)/sqrt(4+2z²)` agrees with the normalized gradient on `Y`. Its displayed differential is correct. At `P=(1,1,1)`, the orthogonal tangent vectors `e1=(1,-1,0)` and `e2=(1,1,-1)` satisfy:

- `DM(e1)=e1/sqrt(6)`;
- `DM(e2)=4e2/(3sqrt(6))`.

Applying the defining minus sign gives the eigenvalues `-1/sqrt(6)` and `-4/(3sqrt(6))`, so the target's diagonal matrix is correct. The authority's non-eigen second basis vector and omitted Weingarten minus sign are not propagated.

## Adverse-ledger determinations

| ID | Independent mathematical determination | Target realization | Verdict |
|---|---|---|---|
| O011-CORR-0038 | `gamma(t)=(x cos t-y sin t, x sin t+y cos t,z)` has `gamma(0)=P` and preserves `x²+y²=z²`. The authority curve generally has neither property. | Standard xy-plane rotation plus disclosure | PASS |
| O011-CORR-0039 | The normalized-gradient calculation above uniquely gives the two requested derivatives and exposes the authority's malformed exponent/unfinished computation. | Complete three-part torus solution | PASS |
| O011-CORR-0040 | The orthogonal tangent eigenbasis above diagonalizes `DM`; `L=-DM` forces both eigenvalues to be negative for the chosen normal. | Correct basis, signs, eigenvalues, and diagonal matrix | PASS |
| O011-CORR-0041 | The lemma quantifies `P`; its tangent space must be `T_PY`, not `T_pY`. | Uppercase `P` plus disclosure | PASS |
| O011-CORR-0042 | The differentiated orthogonality identity fixes the missing argument as `N(P)`; no other vector gives the stated normal component. | Exact `<gamma''(0),N(P)>` binding; receipt evidence check passes | PASS |
| O011-CORR-0043 | In a non-orthonormal graph basis the scaled Hessian is the second fundamental-form matrix `B`, while the operator matrix satisfies `GA=B`. | `G^{-1}` inserted in statement and proof | PASS |
| O011-CORR-0044 | A C¹ defining function yields only a continuous normalized gradient in general; the lecture's shape operator needs a differentiable normal. C² is the correct sufficient hypothesis. | Exercise 4.6 explicitly assumes C² and discloses the repair | PASS |
| O011-CORR-0045 | The same regularity requirement applies before comparing shape operators under a linear isometry. | Exercise 4.9 explicitly assumes C² and discloses the repair | PASS |

## Final conclusion

The exact targets listed above are mathematically and topologically closed for Unit 4. Formula order and statement order match the authority except for the eight disclosed, justified repairs. Exercise order, point values, empty hints, supplied-solution availability, orientation behavior, tangent-space identifications, and all repaired computations pass. There are no remaining audit findings.
