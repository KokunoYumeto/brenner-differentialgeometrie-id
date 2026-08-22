# Unit 2 final post-repair mathematical audit

Audit date: 2026-08-22 (Europe/Berlin)  
Mode: independent read-only audit of the seven final Unit 2 reader sources against the exact frozen German authorities, correction manifests, translation receipts, adverse ledger, and rebuilt through-Unit-2 PDF. This receipt is the audit's only write.

## Release verdict

**PASS — no remaining P1, P2, or P3 finding in the audited Unit 2 scope.**

All requested mathematical repairs are correct, the three defects found in the preceding audit are resolved, every final target is bound to its current authority and correction manifest, the ledger is valid machine-readable CSV, and the corrected passages render cleanly in the deterministic PDF.

## Mathematical and reader-layer verification

- **O011-CORR-0012 — rotation-surface domain: PASS.** The curve and surface now consistently use the open interval `]a,b[`.
- **O011-CORR-0013 — normal-field symbol: PASS.** The unit condition uses the defined field `F`, not undefined `N`.
- **O011-CORR-0014 — constant Gauss-map proof: PASS.** For `\ell(x)=\langle v,x\rangle`, the restriction has zero differential on `Y`; connectedness makes it constant, so `Y` lies in the affine hyperplane `H`. Since `T_PY=T_PH=v^\perp`, the equal-dimensional inclusion `Y\to H` is a local diffeomorphism and `Y` is open in `H`. The reader-visible edition note accurately discloses replacement of the invalid source proof.
- **O011-CORR-0015 — source-item numbering: PASS.** Lecture statements and worksheet exercises render with the source's `2.x` identifiers, including Teorema 2.10 and Teorema 2.11, while the cumulative-reader anchors remain distinct.
- **O011-CORR-0016/O011-CORR-0024 — display punctuation: PASS.** The corrected comma and sentence-ending full stop are attached to their displays without changing the mathematics.
- **O011-CORR-0017 — ambient dimension: PASS.** The rotation-surface task correctly uses `\mathbb R^3`, as does Lecture 2, Lemma 2.1.
- **O011-CORR-0018/O011-CORR-0020 — orientation: PASS.** The sphere task handles both orientations and signs; the ellipse task fixes the outward-gradient orientation, and Solution 12 uses that same normal.
- **O011-CORR-0019/O011-CORR-0025 — antipodal map: PASS.** The stray source `m` is replaced by a full stop and the detached Indonesian continuation is gone. The sentence ends cleanly at the map.
- **O011-CORR-0021 — Solution 2 proof: PASS.** Differentiating `\Vert h'\Vert^2` and dividing by nonzero `2\Vert h'\Vert` proves exactly the required identity without the source's orthogonal/orthonormal error.
- **O011-CORR-0022 — Solution 7 domain: PASS.** `U=\{x^2+y^2>0\}` is the correct open domain for the radial square root and divisions; `R>r>0` ensures the torus lies in `U`.
- **O011-CORR-0023 — Solution 13 injectivity: PASS.** Equality of normalized positive-gradient vectors gives `(x,y)=c(z,w)` with `c>0`; the ellipse equation gives `1=c^2`, hence `c=1`.
- **O011-CORR-0026 — Solution 13 reference: PASS.** The Gauss-surjectivity result is now correctly displayed as **Teorema 2.11**, matching the numbered lecture result.
- **O011-CORR-0027 — Solution 12 prose: PASS.** The opening now states grammatically and directly that the outward unit normal is obtained by normalizing the ellipse gradient.

No correction introduced a new quantifier, sign, domain, notation, formula, identifier, exercise-order, solution-mapping, or Indonesian reader-prose defect.

## Topology, ledger, build, and visible-PDF evidence

The current `scripts/verify_unit_translation.py` logic (SHA-256 `176d5e184540a7bc397ec639e980b968b913bcbc796e7838ddf22e10bb8025de`) was re-run in memory, without writing receipts. All seven comparisons pass: command and environment sequences, inline/display mathematics, protected macro calls, and brace profiles are exact or covered by one declared hash-bound correction; every declared delta is consumed and no undeclared delta remains. The seven persisted translation receipts also report `pass` and bind the final target hashes below.

`00_control/ADVERSE_LEDGER.csv` is 9,604 bytes, SHA-256 `8e19247c807b90890718f4ce845e7ba6a990a7e3d67e639f2cd2f92f54ab84e2`. A standards-based CSV parse returns 37 rows including the header, exactly six fields in every row, no duplicate IDs, and complete unique entries O011-CORR-0012 through O011-CORR-0027. The formerly malformed O011-CORR-0012 fields are now quoted correctly.

The rebuilt 44-page PDF was produced identically in both recorded clean build cycles. Each cycle and the final output are 3,152,320 bytes with SHA-256 `6312b4df706d0f08eeb9f37da0abda3428b5448dce54781d0f52eb9c8db5c385`; the final third-pass logs contain no TeX warning, overfull/underfull box, undefined-reference, or error diagnostic. Text readback and 180-dpi visual inspection confirm:

- page 36: the antipodal map ends cleanly as `P \mapsto -P.` with no detached phrase or stray character;
- page 39: the revised Solution 12 opening is readable, well spaced, unclipped, and collision-free;
- page 41: “Kesurjektifan pemetaan ini mengikuti Teorema 2.11.” is correct and cleanly rendered.

A bounded scan of all seven sources and the PDF found no placeholder, replacement character, local filesystem path, credential/token pattern, raw URL, or active German/English reader residue. Remaining German strings in sources are non-reader semantic link/category locators or authority comments and do not leak into the PDF.

## Final audited target identities

| Target | Bytes | SHA-256 |
|---|---:|---|
| `lecture02.id.tex` | 22,694 | `3dec5f7c1ec47b2ea965481f78db8334ab4046b001c53dd58bde0b9d0bb4cc49` |
| `worksheet02.id.tex` | 10,576 | `677d9b244a2c30561f497e602e29081ca12f668d5a5ec3d116900c49a5bd5954` |
| `worksheet02_exercise01_solution.id.tex` | 951 | `bf0788c3f5cc77324bca5dfc1a899b5410fa5a8312da7594b85993c9245a45fe` |
| `worksheet02_exercise02_solution.id.tex` | 965 | `66ac0a6b86de21eee86a898fe7122644c932c4dff44bbc51845967a86b73e2fc` |
| `worksheet02_exercise07_solution.id.tex` | 1,499 | `405e59e8569d9ba8d8dd35ebe6b2ce693cb931d8ed42824d790baeba31fdd8d3` |
| `worksheet02_exercise12_solution.id.tex` | 5,009 | `1c04a8fd29888aa47633cffceb25104c6533e6c2b9e512ad663fd3742c581832` |
| `worksheet02_exercise13_solution.id.tex` | 2,532 | `a4a230b45de82885027722450d3a7f12fc63fe06187abab481788f7b37352ac0` |
| `geometri-diferensial-manifold-mulus-hingga-unit-02-id.pdf` | 3,152,320 | `6312b4df706d0f08eeb9f37da0abda3428b5448dce54781d0f52eb9c8db5c385` |

Frozen German authority hashes used: lecture `f488d809e7d9490c40099d90c2abed2cc8bea39f11923a8d525e6302f3be470a`; worksheet `c645aacb16233d832b492315379b0251c33fa52db6b2e7ac24be4ecc9600d3ad`; Solutions 1/2/7/12/13 respectively `6dcc38f066a8350fdba67145857c168e1b6ca532c07af0a8f34ee2b954ad9432`, `a92e556f50d2216192fc61703eea4bae3d233ab632c8eedb19bd35dec2ed89b0`, `90d9007e6a313dcbc4614045f0831b826f7a9af82897e17a36fbce08088ef92b`, `3191adb6fbfaf1be11c0e7a061468a4fd6fe9235cd0dea40771ec97bd10f970f`, and `6896eb6a4a6f4c25bcfaab674847dcd78bc079cfd6c58b3b8542c5c220d85e7b`.
