# Unit 2 worksheet and supplied-solution translation findings

> **Historical initial-translation handoff; superseded.** The source defects and target hashes below describe the first translated draft before the authorized mathematical repairs. The current targets contain the explicit corrections recorded as O011-CORR-0016 through O011-CORR-0027, and the terminal evidence is `POST_REPAIR_MATH_AUDIT.md`, whose verdict is PASS. Do not use this file as the current release verdict or hash inventory.

Status: **complete source translation**. The Indonesian worksheet and all five source-supplied solutions are present. No suspected source defect was silently repaired. Build integration and rendered QA are outside this bounded handoff.

## Frozen authority and closure

The worksheet is the German Wikiversity surface `.../Arbeitsblatt 2`, page ID `142636`, revision `907117`, timestamp `2023-07-18T12:00:58Z`. Its sanitized expanded TeX witness is `authority/expanded/worksheet02_source.de.tex`, 10,171 bytes, SHA-256 `c645aacb16233d832b492315379b0251c33fa52db6b2e7ac24be4ecc9600d3ad`.

The worksheet contains 19 exercises: 15 practice exercises followed by four submission exercises worth `3, 4, 5, 3` points. Exactly five practice exercises use `\inputaufgabegibtloesung`: exercises 1, 2, 7, 12, and 13. The current official solution query found exactly those five pages and marked the other 14 candidate solution pages missing.

| Exercise | Page ID / revision | Revision time (UTC) | Exact wikitext SHA-256 | Expanded German TeX SHA-256 |
|---:|---|---|---|---|
| 1 | `139491 / 1090802` | `2026-05-31T14:13:03Z` | `f6787c5b9547ac189e011cb8b1f50ecad82247095e086138bd45e0a4f06647bb` | `6dcc38f066a8350fdba67145857c168e1b6ca532c07af0a8f34ee2b954ad9432` |
| 2 | `120435 / 1089268` | `2026-05-31T10:02:12Z` | `0bdd1cde6d1d0dc74757aa824634d10b6b4bf413efb4431538b7d9bac2b6f06c` | `a92e556f50d2216192fc61703eea4bae3d233ab632c8eedb19bd35dec2ed89b0` |
| 7 | `152882 / 1094222` | `2026-06-14T15:20:09Z` | `dbe0990deca042c24dda79891b6ccc66b57723be69023687cacd7ffa206f6988` | `90d9007e6a313dcbc4614045f0831b826f7a9af82897e17a36fbce08088ef92b` |
| 12 | `152865 / 1095926` | `2026-06-15T07:27:34Z` | `78284fe9d10f41f0503cba0d3295c761d5d168d8de06505226909c7242d4993a` | `3191adb6fbfaf1be11c0e7a061468a4fd6fe9235cd0dea40771ec97bd10f970f` |
| 13 | `152873 / 1094182` | `2026-06-14T15:10:42Z` | `1050f074ecb58b7a8211d756b7fcd6fe4a0a4db6a024083c31ca3c5469e9fd50` | `6896eb6a4a6f4c25bcfaab674847dcd78bc079cfd6c58b3b8542c5c220d85e7b` |

Each translated solution is a separate file and begins with comments binding it to the exact page identity, wikitext witness, and expanded German TeX witness.

## Preservation QA

- Worksheet: source and target both contain 271 TeX commands in the same sequence, 28 identical inline-math spans, balanced braces `744/744` with maximum depth 6, the same environment sequence, the same 19 exercise macros in source order, and the same point arguments. The inserted arc-length definition remains between exercises 2 and 3.
- Supplied solutions 1/2/7/12/13 respectively preserve command counts `21/40/39/262/79`, inline-math counts `2/2/1/2/1`, balanced-brace counts `28/56/90/358/131`, command sequence, environment sequence, and every protected mathematical macro argument.
- One intentional reader-visible localization occurs inside mathematics at worksheet source/target line 154: `f\text{ differenzierbar}` became `f\text{ terdiferensialkan}`. The surrounding set-builder expression is byte-identical. This is a protected localization, not a mathematical change.
- Reader-facing scans found no residual German or English prose after excluding immutable German internal-link destinations, authority comments, and the preserved `[[Kategorie:Latexseite]]` structural marker. All six targets contain zero U+FFFD characters, tested mojibake signatures, local paths, task/thread IDs, umbrella-project strings, or secret-like strings.

## Source defects and ambiguities preserved for review

1. **P2 — Exercise 2 supplied solution has an invalid derivative derivation.** In `authority/expanded/worksheet02_exercise02_solution_source.de.tex:17`, `u_1=h'(t)` is extended only to an orthogonal basis, but lines 25–31 use the unweighted Euclidean coordinate-norm formula as though the basis were fixed and orthonormal. More decisively, differentiating `\sqrt{\sum_i h_i'(t)^2}` should introduce `h_i'(t)h_i''(t)`, whereas the source numerator at lines 29–31 is `h_i(t)h_i'(t)`. The final invariant formula is correct, but the displayed intermediate equalities do not prove it.
2. **P2 — Exercise 13 supplied solution omits a needed injectivity step.** In `authority/expanded/worksheet02_exercise13_solution_source.de.tex:56`, equality of normalized Gauss vectors yields positive scalar dependence of the two unnormalized vectors. The source then asserts equality at lines 60–73 without proving the scalar is one. Applying the common ellipse equation to the two points supplies the missing argument; the translation does not add it.
3. **P3 — Exercise 8 has an ambient-dimension inconsistency.** `authority/expanded/worksheet02_source.de.tex:322` places the surface of revolution generated by `f:I\to\mathbb R_+` in `\mathbb R^n`, while the associated Lecture 2 construction is a surface in `\mathbb R^3`. The translation preserves `\mathbb R^n`.
4. **P3 — Exercise 11 contains a stray source character.** The antipodal-map macro has the final argument `{m}` at `authority/expanded/worksheet02_source.de.tex:383`, which produces a visible `m` after `P\mapsto-P`. The same `{m}` remains at `source/units/unit-02/worksheet02.id.tex:380`.
5. **P3 — Exercise 10 leaves the sphere orientation unstated.** The Gauss map changes sign when the orientation is reversed, although either choice is still induced by a scalar linear map. The translation preserves the source's wording and does not choose an orientation.

## Target inventory

| Target | Bytes | SHA-256 |
|---|---:|---|
| `source/units/unit-02/worksheet02.id.tex` | 10,327 | `7a032c8f2ce6bd3bdf728f419c1d006e6fe0d02760f469e591bff7121df038a3` |
| `source/units/unit-02/worksheet02_exercise01_solution.id.tex` | 951 | `bf0788c3f5cc77324bca5dfc1a899b5410fa5a8312da7594b85993c9245a45fe` |
| `source/units/unit-02/worksheet02_exercise02_solution.id.tex` | 1,302 | `04da52a11f6ffd7ebc84ec1f70fc1ddef38d8bafc5cb4831cf13e4470849b34c` |
| `source/units/unit-02/worksheet02_exercise07_solution.id.tex` | 1,440 | `91b527da12609ba9d53dc2126758a0a3b3f093cfd3f6e4f8de7a4af43894702a` |
| `source/units/unit-02/worksheet02_exercise12_solution.id.tex` | 4,950 | `00b8cc6b9fb19b3379662a9de94602db38a758254725657b1d0b0dfcbd25a1a1` |
| `source/units/unit-02/worksheet02_exercise13_solution.id.tex` | 2,408 | `5479516a09a8614a284bda99fa67fc412c17ef39d0c93dbe2a105c99b7e00ef9` |
| `qa/unit-02/WORKSHEET_TERMS_PROPOSED.csv` | 2,471 | `95e9e1b28cb3a694e7822006374787f210c3cdf9de5d08b46eb8b9d290469e6c` |

The terminology file proposes 24 worksheet terms and explicitly marks the entries already aligned with the Unit 2 lecture. No shared terminology file, ledger, build file, backend, Unit 1 file, or authority witness was edited.
