# Unit 5 lecture translation and source findings

Reviewed: 2026-08-22 (Europe/Berlin)

Status: **PASS — complete Indonesian translation with explicit ledgered repairs.**

## Exact surfaces

- Course root: `Kurs:Differentialgeometrie (Osnabrück 2023)/Vorlesung 5`, page/revision `142549/894651`.
- LaTeX surface: `Kurs:Differentialgeometrie (Osnabrück 2023)/Vorlesung 5/latex`, page/revision `142579/807139`.
- Frozen expanded source: `authority/expanded/lecture05_source.de.tex`, 23,357 bytes, SHA-256 `d4d3549c402338aa7f65973fc3a6cb57822e9a75277d48ce1177672d73bc01be`.
- Corrected Indonesian target: `source/units/unit-05/lecture05.id.tex`, 25,557 bytes, SHA-256 `5e3e89d1cf6a0fc2575b7790bd0dbce824ae0ecdc1bde1e32364aa642289d27b`.
- Translation receipt: `qa/unit-05/lecture05_translation.json`, 1,188 bytes, SHA-256 `9976bc55644714e1a8401c81aba12c3ba5aabd4adc7de0c56a5301c628c5a1af`, status `pass`.
- Exact correction manifest: `00_control/LECTURE05_PROTECTED_CORRECTIONS.json`, 1,825 bytes, SHA-256 `e71ab3bc9d53563e99c022273f179cfd22a1327e0c629a0498461f85082565da`.

## Complete translation audit

- The complete authority and target were compared rather than sampled.
- All three headings, definitions, examples, proofs, semantic destinations, `NOEDITSECTION` markers, the terminal category, and source order remain present.
- The manifest-aware verifier passes UTF-8, command and environment profiles, inline/display mathematics, protected macro calls, brace topology, and full consumption of the declared correction profile.
- The one admitted media occurrence remains `Minimal surface curvature planes-de.svg`. Its source credit macro is preserved and its formerly empty caption now gives an Indonesian semantic description of every German label.

## Correction disposition

The independent mathematical audit confirmed eight source defects across the Unit 5 surfaces. Lecture corrections are bound as follows:

- `O011-CORR-0046`: strengthen the three opening Weingarten/principal-curvature hypotheses and the rotational example from `C1`/differentiable to `C2`.
- `O011-CORR-0047`: restore the inverse graph metric, so `A=G^{-1}H/omega`, principal directions solve `Hu=kappa omega Gu`, and `K=det(H)/omega^4`.
- `O011-CORR-0048`: remove the unrelated sphere-example cross-reference while retaining graph Lemma 4.9.
- `O011-CORR-0049`: repair the rotational graph domain to `z^2<f(x)^2`, equivalently `|z|<f(x)`.
- `O011-CORR-0050`: repair the meridional, parallel, and Gaussian curvatures by their exact metric powers.
- `O011-CORR-0051`: require a unit direction and an orthonormal principal basis in Euler's formula and state the scaled identity for nonunit vectors.
- `O011-CORR-0052`: fix a compatible orientation for signed normal-section curvature and disclose the orientation-free absolute-value statement.

Every repair carries a reader-visible `Catatan edisi`; the frozen authority remains unchanged. `qa/unit-05/POST_REPAIR_MATH_QA.json` independently binds all eight Unit 5 correction IDs and passes 46 exact checks.
