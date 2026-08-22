# Unit 4 lecture translation and mathematical review

Reviewed: 2026-08-22 (Europe/Berlin)

Status: **PASS for translation, topology, and corrected mathematics.** Cumulative build and rendered-page QA remain separate gates.

## Exact surfaces

- Course root: `Kurs:Differentialgeometrie (Osnabrück 2023)/Vorlesung 4`, page/revision `142548/893683`.
- LaTeX surface: `Kurs:Differentialgeometrie (Osnabrück 2023)/Vorlesung 4/latex`, page/revision `142578/807138`.
- Frozen expanded source: `authority/expanded/lecture04_source.de.tex`, 26,932 bytes, SHA-256 `610c85e2cb9838a2ce1deb488ceca6cb7d2ee2ab47f1e657d5df7488796f8402`.
- Indonesian target: `source/units/unit-04/lecture04.id.tex`, 28,602 bytes, SHA-256 `60a7a2cbfc96a9a510bfff935f40722458c85031214eeaf8ccf4e8df2af2bc81`.
- Translation receipt: `qa/unit-04/lecture04_translation.json`, 1,314 bytes, SHA-256 `bac1e9f1577535848e1e7fc455f7a651952d8285050d56a45656e9dead6c78b2`, status `pass`.
- Correction manifest: `00_control/LECTURE04_PROTECTED_CORRECTIONS.json`, 1,933 bytes, SHA-256 `bbbefb6776c283045ee061fb2113f26d33de6789a54c3afcc08726c270208e3c`.

## Complete translation audit

- The full 1,420-line authority and full Indonesian target were compared, not sampled.
- The target preserves the section heading, one definition, six theorem/lemma/corollary proof blocks, two examples, semantic destinations, `NOEDITSECTION` markers, terminal category, and frozen live order.
- The manifest-aware verifier passes UTF-8, all 880 source command positions or declared deltas, 76 environment entries, all 62 inline-math payloads or declared deltas, all 73 protected calls or declared deltas, and brace topology.
- All eighteen semantic-link/category destinations remain byte-identical and in source order. Reader-facing labels are localized. Unit 4 has no media occurrence.
- The terminology proposals were reviewed and admitted to the shared ledger where they were genuinely new; duplicate source variants continue to use their existing admitted terms.

## Explicit target corrections

### O011-CORR-0041 — tangent-space point symbol

The source quantifies `P` but writes `T_pY`. The target uses `T_PY` and includes a reader-visible edition note. The exact inline-math source/target hashes are bound at occurrence 19 in the correction manifest.

### O011-CORR-0042 — missing normal vector in the acceleration component

The source prints an inner product with no second argument while describing normal acceleration. The immediately preceding proved identity uniquely determines `N(P)`, so the target restores `⟨gamma''(0),N(P)⟩` and discloses the correction. Because the generic profile previously did not protect `mathl`, the verifier now also validates an exact normalized `command:mathl` occurrence-6 binding; the receipt reports `evidence_only_deltas_verified: true` and a passing `O011-CORR-0042` result.

### O011-CORR-0043 — graph shape-operator matrix

For the graph immersion `F(x)=(x,f(x))`, let the column vector `g=grad f`, let `W=sqrt(1+||g||^2)`, and let the graph metric be `G=I+gg^T`. The source proof correctly establishes the second-fundamental-form identity

`<L dF(v),dF(w)> = v^T Hess(f) w / W`,

but the source statement incorrectly calls `Hess(f)/W` the coordinate matrix of `L`. If `A` is that operator matrix in the graph basis, the bilinear-form matrix is `GA`; hence `GA=Hess(f)/W` and

`A=G^{-1} Hess(f)/W`.

The target statement and proof conclusion now make this distinction explicit and tell the reader that the inverse metric factor was absent from the source. Command, protected `mathdisp`, and brace-profile deltas are bound to `O011-CORR-0043`.

## Order disposition

The target retains the frozen live order: self-adjointness Theorem 4.7, diagonalizability Corollary 4.8, then the graph Lemma 4.9. The historical official PDF reverses the last two items, but the live order is logically sound and all current references resolve. Decision `D015` records why the revisioned semantic graph, rather than the PDF witness, controls production order.

## Independent audit

An independent read-only audit found no P1 or material P3 issue. It verified the course sign convention `L=-DN`, the positive second-fundamental-form identity for the upward graph normal, the `GA` coordinate relation, the three corrections above, and all live-order references. Its one P2 evidence concern—the missing exact manifest binding for `O011-CORR-0042`—was repaired and now passes machine verification.
