# Unit 4 worksheet and supplied-solution review

Reviewed: 2026-08-22 (Europe/Berlin)

## Exact surfaces

- Frozen worksheet authority: `authority/expanded/worksheet04_source.de.tex`, 11,052 bytes, SHA-256 `81f8d9667581e0e6507dd1684b136c23f3352d1cabf2e8c4013daeb0a312cd00`.
- Indonesian worksheet: `source/units/unit-04/worksheet04.id.tex`, 11,797 bytes, SHA-256 `f3721ced8fc5db02dd600ff81f02455ec724f34c7a085f4280d8f5c2d14873f8`.
- Frozen Exercise 7 solution: 2,623 bytes, SHA-256 `a0df2279b1dbae5bff1a4e50385349080bd8734e20d1a6edec83e528045dc63e`.
- Indonesian Exercise 7 solution: 1,983 bytes, SHA-256 `6003193ccef4456ffcbe42e67068202567ceafe4897363aa4833b266aaf855d5`.
- Frozen Exercise 10 solution: 2,633 bytes, SHA-256 `76a2f5db7eb835b19b924418ae2c1b0cfbcd8cd2d5acc387f695f71cbb069a35`.
- Indonesian Exercise 10 solution: 2,661 bytes, SHA-256 `a5d22c14d32b03265e532b34636da4d656d838cefe268c92d1ac3ec1ebd27de4`.

The three manifest-aware topology receipts pass. The obsolete failing preflight receipts were removed after the final receipts superseded them.

## Closure and topology

- Fifteen exercises in the source order: eleven practice exercises and four graded exercises.
- Graded point values are exactly `4, 5, 4, 6`, totaling 19.
- Every source hint field is blank, and the target invents no hint layer.
- Exactly Exercises 7 and 10 carry source-supplied solutions. The other thirteen conventional solution candidates are absent.
- Unit 4 has no mathematical media assets.

## Explicit target corrections

- `O011-CORR-0038`: Exercise 2's source curve generally neither starts at the stated point nor remains on the cone. The Indonesian target uses the standard rotation `(x cos t - y sin t, x sin t + y cos t, z)` and tells the reader that the formula is corrected.
- `O011-CORR-0039`: the supplied torus solution is algebraically damaged and ends before evaluating the two requested derivatives. The target identifies that limitation and completes the normalized-gradient calculation, obtaining `D_vN(P)=(0,-1/(R-r),0)` and `D_wN(P)=(0,0,1/r)`.
- `O011-CORR-0040`: the supplied ellipsoid solution computes `DN` rather than the course's `L=-DN` and does not supply a valid eigenbasis. The target identifies the defect, uses the orthogonal tangent eigenbasis `(1,-1,0)` and `(1,1,-1)`, and obtains eigenvalues `-1/sqrt(6)` and `-4/(3sqrt(6))`.
- `O011-CORR-0044` and `O011-CORR-0045`: Exercises 6 and 9 assume only a `C1` defining function although the requested Weingarten map requires a differentiable normal field. Each target statement is explicitly strengthened to `C2`, with a reader-visible edition note.

## Independent review result

An independent read-only comparison confirmed the exercise count, order, point values, blank hints, supplied-solution closure, and the mathematics of corrections `0038`-`0040`. It also prompted a wording repair in Exercise 5 so the direction vector of the line, rather than the line itself, is regarded as a tangent vector. No unresolved P1, P2, or P3 finding remains on these three surfaces before cumulative-build QA.

