# Unit 2 Lecture: mathematical source findings

Authority: `authority/expanded/lecture02_source.de.tex`, 22,206 bytes, SHA-256 `f488d809e7d9490c40099d90c2abed2cc8bea39f11923a8d525e6302f3be470a`.

Corrected translation: `source/units/unit-02/lecture02.id.tex`, 22,694 bytes, SHA-256 `3dec5f7c1ec47b2ea965481f78db8334ab4046b001c53dd58bde0b9d0bb4cc49`.

The issues below are source-level findings. Corrections 1--3 are explicit reader corrections recorded as `O011-CORR-0012` through `O011-CORR-0014` in the adverse ledger and hash-bound in `00_control/LECTURE02_PROTECTED_CORRECTIONS.json`; none was applied silently. Finding 4 is a prose normalization. Finding 5 remains a disclosed source wording issue.

## O011-U02-L02-FIND-0001 — P2 — curve-domain mismatch

The opening defines `\gamma` on the open interval `]a,b[` but defines the associated surface using `t \in [a,b]`. Unless `\gamma` is additionally assumed to extend to the endpoints, the displayed set evaluates `\gamma` outside its declared domain. The target uses `t \in ]a,b[` in the surface, matching the declared domain of `\gamma`.

## O011-U02-L02-FIND-0002 — P2 — normal-field symbol mismatch

The definition introduces the normal field as `F:U\to\mathbb R^n` and imposes `F(P)\in N_PY`, but the following unit-length condition is written `\lVert N(P)\rVert=1`. No field `N` has yet been introduced. The target replaces `N(P)` by `F(P)`.

## O011-U02-L02-FIND-0003 — P1 — invalid proof step in the constant-Gauss-map lemma

The forward proof says that one may replace the real-valued defining function `h` by `h/\lVert h\rVert` without changing `Y`, then infers `\operatorname{Grad}h(P)=\pm v` and finally that `h` is linear. For scalar `h`, this normalization is undefined on a zero fiber, generally does not preserve an arbitrary fiber, and does not justify either derivative conclusion. The theorem itself is salvageable without this step: if the Gauss map is the constant unit vector `v`, then the differential on `Y` of `P\mapsto\langle v,P\rangle` vanishes; connectedness (and local path connectedness of the hypersurface) makes that function constant, so `Y` lies in one affine hyperplane orthogonal to `v`; equal dimension and the local manifold charts then show that `Y` is open in that hyperplane. The target gives that valid replacement proof and explicitly tells the reader why it replaces the source step.

## O011-U02-L02-FIND-0004 — P3 — contradictory affine-subspace wording

The same proof ends with the German phrase `affin-linearer Untervektorraum`, although an affine subspace need not be a vector subspace. The Indonesian reader text uses the mathematically coherent `subruang afin-linear`, matching the lemma statement; no formula or identifier changed. A corrected German wording would be `affin-linearer Unterraum` or, here, `affine Hyperebene`.

## O011-U02-L02-FIND-0005 — P3 — continuity/differentiability wording mismatch

The normal-field definition requires only a continuous vector field on an open neighborhood, but the explanatory sentence says the open neighborhood is needed so that one can speak of differentiability. Either the intended field regularity should be stated as differentiable, or the explanation should distinguish the present continuity requirement from later ambient differentiability. The translation preserves this distinction as written.
