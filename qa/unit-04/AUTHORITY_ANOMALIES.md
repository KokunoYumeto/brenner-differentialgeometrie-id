# Unit 4 authority anomalies before translation

This is a source-evidence ledger, not a target correction file. The frozen German witnesses remain unchanged. Each item must be resolved explicitly in the Unit 4 mathematical/adverse-correction review; none may be silently normalized.

## A1 - Worksheet Exercise 2 does not define the claimed curve on the cone

At `authority/expanded/worksheet04_source.de.tex:90`, the source sets

\[
\gamma(t)=(x\cos t,\;y\sin t,\;z)
\]

for an arbitrary stated point \(P=(x,y,z)\) on \(x^2+y^2=z^2\). In general \(\gamma(0)=(x,0,z)\ne P\), and \(x^2\cos^2t+y^2\sin^2t\) is not constantly \(z^2\). Thus the curve generally neither starts at \(P\) nor lies on the cone. The mathematically natural intended rotation is plausibly \((x\cos t-y\sin t,\;x\sin t+y\cos t,\;z)\), but that intent must be logged rather than assumed silently.

## A2 - Lecture Lemma 4.8 conflates the second fundamental form with the shape-operator matrix

At `authority/expanded/lecture04_source.de.tex:1312`, the source states that, under the graph-coordinate identification from Lecture 1, the Weingarten map is

\[
\frac{1}{\sqrt{1+\lVert\nabla f\rVert^2}}\operatorname{Hess}f.
\]

The proof at line 1403 establishes instead the bilinear-form identity

\[
\langle L_P(dF(v)),dF(w)\rangle
=\frac{1}{W}v^{\mathsf T}(\operatorname{Hess}f)w,
\qquad W=\sqrt{1+\lVert\nabla f\rVert^2}.
\]

Because the graph-coordinate metric is \(G=I+\nabla f\,\nabla f^{\mathsf T}\), the operator matrix relative to the graph basis is \(G^{-1}(\operatorname{Hess}f)/W\), not merely \((\operatorname{Hess}f)/W\), except in special cases such as \(\nabla f=0\). This affects the method for Worksheet Exercises 8 and 15.

## A3 - Exercises 6 and 9 assume insufficient regularity

At `authority/expanded/worksheet04_source.de.tex:302` and `:552`, the source assumes only a continuously differentiable defining function \(h\), then asks about Weingarten maps. The lecture definition requires a differentiable unit normal, and its stated sufficient hypothesis is twice continuously differentiable \(h\). A merely \(C^1\) function does not ensure that the normalized gradient is differentiable. Both exercises need an explicit \(C^2\) hypothesis or another differentiability assumption on the chosen normal field.

## A4 - The supplied Exercise 7 solution is unfinished and algebraically damaged

`authority/expanded/worksheet04_exercise07_solution_source.de.tex` ends at line 84 with “Im angegeben Punkt ist dies”, followed by an empty second-item conclusion and an entirely empty third list item. It therefore supplies no final value for the requested \(D_vN\) and no response at all for \(D_wN\). Its displayed derivative also changes the normalization denominator, uses a positive correction term where differentiating \(F/\lVert F\rVert\) contributes a negative projection term, and contains \((x^2+y^2)^{+3/2}\) where the surrounding derivative pattern requires a negative exponent. Preserve the frozen source as an incomplete supplied solution; any completed solution must be separately identified and mathematically audited.

## A5 - The supplied Exercise 10 solution computes \(DN\), not the defined Weingarten map \(-DN\)

The source defines \(L_P(v)=-(D_vN)(P)\). `authority/expanded/worksheet04_exercise10_solution_source.de.tex` computes the differential of the outward normal extension \(M=N\) and then reports its positive eigenvalues \(1/\sqrt6\) and \(4/(3\sqrt6)\) as those of the Weingarten map. With the stated orientation and convention, the corresponding \(L_P\) eigenvalues are their negatives. Moreover, the displayed working gives a triangular matrix in the chosen non-eigenbasis and then states a diagonal matrix without supplying the changed eigenbasis. A corrected target solution must show the sign and basis explicitly.

## A6 - Two literal lecture defects

- `authority/expanded/lecture04_source.de.tex:271` says \(T_pY\) where the quantified point is \(P\); the intended symbol is \(T_PY\).
- At line 931, the source writes \(\langle\gamma'',\,\rangle(0)\) while describing the normal acceleration component. The preceding proved identity shows the missing second argument is \(N(P)\), i.e. \(\langle\gamma''(0),N(P)\rangle\).

## Disposition

Authority admission remains **PASS** because every defect is frozen exactly and the closure is complete. Translation is not a mechanical copy gate: Unit 4 must use explicit adverse-ledger entries for mathematically determined corrections, and the incomplete Exercise 7 solution must not be presented as though the source supplied a complete solution.
