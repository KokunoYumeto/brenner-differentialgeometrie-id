# Unit 19 worksheet reader and mathematics QA

- Scope: `source/units/unit-19/worksheet19.id.tex`
- Frozen source: `authority/expanded/worksheet19_source.de.tex`
- Source SHA-256: `85fed2deb4f46ff8279383f9047a43fc8aee39b3cd7ddc35293b0686dc40ddad`
- Target SHA-256: `7fd09462ffe522d33330b4105b0cccbc04c9e7588e9bd7128e24c97dd2828c9c`
- Translation verifier: pass; all command, environment, inline-math, display-math, protected-call, and brace-profile checks pass.
- Census: 12 exercises, comprising nine practice exercises and three graded exercises worth 3, 4, and 5 points (12 points total).
- Source solution layer: no supplied solutions. No solutions were invented.
- Source hint layer: all 12 hint fields are blank and remain blank.
- Reader-language check: no German prose remains outside immutable MediaWiki targets and the removable source category marker.
- Encoding check: UTF-8 without BOM or replacement characters; LF line endings and a trailing LF.

## Mathematical determinations

1. `O011-CORR-0270`: Exercise 4 now limits the requested second-fundamental-matrix computation to the interior of the displayed parameter domain; the square-root chart is not differentiable at `v = plus or minus 1`.
2. `O011-CORR-0271`: Exercise 9 now assumes a three-times-differentiable parametrization, which makes the displayed second derivatives of the first fundamental coefficients available.
3. `O011-CORR-0272`: Exercise 12 now assumes a twice-differentiable generating curve, as required for its second fundamental matrix and curvature quantities.
4. `O011-CORR-0273`: Exercise 8 now specifies a unit normal field so its signed second fundamental matrix and curvature relation are determined.
5. `O011-CORR-0274`: Exercise 12 now requires a choice of unit normal field, removing the sign ambiguity in its second fundamental matrix and principal curvatures.

All five changes are explicit target clarifications recorded in `WORKSHEET19_PROTECTED_CORRECTIONS.json`; no mathematical formula or protected TeX structure was changed.
