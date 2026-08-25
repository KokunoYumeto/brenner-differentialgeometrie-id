# Unit 5 worksheet and supplied-solution review

Reviewed: 2026-08-22 (Europe/Berlin)

Status: **PASS — complete Indonesian translation with explicit ledgered repairs.**

## Exact surfaces

- Frozen worksheet authority: `authority/expanded/worksheet05_source.de.tex`, 10,542 bytes, SHA-256 `88223af26d835e5be221b05a34fee7b374729af095ff7e053119761c6d09ed13`.
- Corrected Indonesian worksheet: `source/units/unit-05/worksheet05.id.tex`, 11,365 bytes, SHA-256 `134823a7aabab103eb198922abdf2a73ef6aee3b4e8644a2e33d488648f322b5`.
- Frozen Exercise 1 solution: `authority/expanded/worksheet05_exercise01_solution_source.de.tex`, 2,033 bytes, SHA-256 `c2ae2ee20c93daf8bd13b6491e2a8180adb2f07fcb934b968ac384e11ec46790`.
- Corrected Indonesian Exercise 1 solution: `source/units/unit-05/worksheet05_exercise01_solution.id.tex`, 2,895 bytes, SHA-256 `aad6ab0d0729988c26b41cc6d6a82c95338b388f79212005a86b0f5c90b3bc4f`.
- Worksheet receipt: `qa/unit-05/worksheet05_translation.json`, 1,081 bytes, SHA-256 `a82cdd0a8a791e39fc342ac89aabfa4a3817053f82629ac523ed613b410cf7d8`, status `pass`.
- Solution receipt: `qa/unit-05/worksheet05_exercise01_solution_translation.json`, 1,117 bytes, SHA-256 `d8ee4f9a9981433698bdaaa3d7f472035c5a86ad82fa86261ab1acdbdbdf4983`, status `pass`.

## Closure preserved

- Exactly 15 exercises remain in source order: ten practice and five graded.
- The graded markers are exactly `4`, `4`, `6`, `6 (2+2+2)`, and `2`, totaling 22 points. The preflight parser was fixed so the split-valued marker is no longer omitted.
- Exercise 13 alone has a nonblank translated hint.
- Exercise 1 alone retains `\inputaufgabegibtloesung`, and exactly its one frozen source-supplied solution is translated. No hint or solution was invented for the other 14 exercises.
- Worksheet 5 has no media occurrence; Unit 5's sole media occurrence is in Lecture 5.

## Correction disposition

- `O011-CORR-0046`: Exercise 7 now assumes `C2`, with a visible note explaining why its requested Weingarten data are otherwise undefined.
- `O011-CORR-0052`: Exercise 14(3) now inherits the compatible normal-plane orientation required by the corrected signed normal-section theorem.
- `O011-CORR-0053`: the supplied Exercise 1 solution now states `Grad f(0)=0`, `omega=1`, and `G=I`; excludes the zero vector in the scalar case; handles both diagonal eigenvalue orderings explicitly; and uses the generic formulas only for `c` nonzero.

The exact manifests are `00_control/WORKSHEET05_PROTECTED_CORRECTIONS.json` and `00_control/SOLUTION05_01_PROTECTED_CORRECTIONS.json`. Both manifest-aware translation receipts pass. The combined post-repair audit `qa/unit-05/POST_REPAIR_MATH_QA.json` passes all 46 correction, topology, point, hint, solution, receipt, and adverse-ledger checks.
