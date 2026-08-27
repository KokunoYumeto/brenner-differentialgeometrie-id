# Unit 19 independent reader QA

Status: **PASS**. The two findings from the first independent pass were corrected and the final lecture and worksheet targets are admitted.

## Scope and topology checked

- Frozen lecture: `authority/expanded/lecture19_source.de.tex`, 29,051 bytes, SHA-256 `bd47777c4d0fc68698db177e8937ab15824931ee86707148eb4ecb4bc9c548f2`.
- Frozen worksheet: `authority/expanded/worksheet19_source.de.tex`, 7,006 bytes, SHA-256 `85fed2deb4f46ff8279383f9047a43fc8aee39b3cd7ddc35293b0686dc40ddad`.
- Final lecture target: 29,383 bytes, SHA-256 `b86102481c4997fb3f403d83809a5a4418ce9eae3c5d58b230693788afa7fbaa`.
- Worksheet target reviewed at 7,175 bytes, SHA-256 `7fd09462ffe522d33330b4105b0cccbc04c9e7588e9bd7128e24c97dd2828c9c`.
- Lecture topology is complete: two definitions, five lemma/theorem/corollary proof blocks, one remark, all ten non-category internal links, and all formula/protected-macro surfaces are retained. The declared protected deltas are the only mathematical-token deltas.
- Worksheet topology is complete: 12 exercises, of which nine are practice and three carry 3, 4, and 5 points (12 total). All 12 hint fields remain blank. The frozen closure supplies no Unit 19 worksheet solutions, and none were invented.

## Findings closed in the final target

1. **Openness of the parameter domain `V`: closed.** The opening setup now attaches `terbuka` unambiguously to `V \subseteq \mathbb{R}^{n-1}` before identifying `\varphi` as a diffeomorphic parametrization of the open set `U`. This restores the explicit chart-domain hypothesis from the frozen source (`O011-TRANS-0256`).

2. **Orientation-dependent cylinder curvature: closed.** The intrinsic-curvature paragraph now gives the eigenvalues as `0` and `\pm 1/r` and states that the sign depends on the chosen unit normal. This is correct under the course convention `L=-DN`, while the ensuing conclusion `K=0` remains unchanged (`O011-CORR-0257`).

## Correction-manifest review

- `O011-CORR-0250` is justified: the map in Lemma 19.3 is `L_P`, as established by the surrounding sentence and proof.
- `O011-CORR-0251` is justified: the pure second derivatives require denominators `\partial u^2` and `\partial v^2`, not the malformed `\partial^2 u` and `\partial^2 v`.
- `O011-CORR-0252` is justified: substituting `i=j=2` into Lemma 19.5 gives the first component `2\partial_2g_{12}-\partial_1g_{22}` in the `\Gamma_{22}` system.
- `O011-CORR-0253` and `O011-CORR-0254` are justified: differentiating Christoffel symbols, or equivalently taking second derivatives of the metric coefficients, requires a continuously three-times differentiable parametrization.
- `O011-TRANS-0255` is reader-language normalization only and does not alter the mathematics or topology.
- `O011-TRANS-0256` faithfully restores the source's explicit openness hypothesis for `V`; it changes no mathematical token.
- `O011-CORR-0257` is justified: reversing the unit normal reverses the Weingarten map and hence the cylinder's nonzero principal curvature.
- `O011-CORR-0270` through `O011-CORR-0274` are all justified: interior restriction for the square-root sphere chart; `C^3` regularity for Brioschi; `C^2` regularity for the generating curve; and explicit normal choices for the signed second fundamental matrix/principal curvatures.

The final Indonesian prose is natural and mathematically faithful. The final lecture translation and preparation receipts pass and bind the final target hash above. No unresolved independent-reader finding remains.
