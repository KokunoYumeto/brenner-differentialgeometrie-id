# Decision log

## D001 — Complete edition-production spine

**Decision:** admit Holger Brenner's complete 29-lecture/29-worksheet Wikiversity course as the production spine of this independent Indonesian edition. The first-unit exact media closure, portable build, structural comparison, visual QA, and reproducibility gate passed on 2026-08-21.

**Reason:** it provides a coherent lawful sequence from embedded geometry through general manifolds, forms and Stokes to connections, geodesics, and curvature. Its semantic source is publicly editable and revisioned, and the Unit 1 proof now establishes a reproducible reader path rather than merely assuming one.

**Boundary:** this admits a source for edition production only. It does not admit Brenner to the separate 40-course curriculum, and completion or sunk work must not be used as curricular evidence.

## D002 — Authority granularity

**Decision:** freeze the recursive transclusion closure, not only the 59 course pages.

**Reason:** lecture and worksheet pages are aggregators. A top-page pin would leave their mathematical body mutable through shared transclusions.

## D003 — Local rebuild

**Decision:** rebuild from frozen semantic/expanded source with a small portable compatibility layer.

**Reason:** the official static PDF set is incomplete and the historical LaTeX recipe is not a self-contained portable project. These facts are source limitations, not permission to lower the reproducibility gate.

## D004 — Bounded missing bridge

**Decision:** add an independently authored bridge after the Brenner spine for (a) de Rham complex/cohomology, Poincaré lemma and homotopy invariance, with the de Rham theorem clearly scoped; and (b) a short Lie-group/Lie-algebra primer if the final role map still requires it. Do not splice another textbook's prose.

**Reason:** Brenner covers differential forms, exterior derivative, partitions of unity and Stokes, but not the required explicit de Rham-cohomology progression; it also lacks a coherent Lie-group unit. The gaps are bounded and conceptually downstream of the spine.

## D005 — Optional visual supplement

**Decision:** Petrunin–Zamora is excluded from the O011 core. Any later separately attributed optional visual supplement requires a fresh overlap check with the geometry lanes.

## D006 — First production boundary

**Decision:** translate Lecture 1 and Worksheet 1 as one contiguous unit and set the next cursor to Lecture 2 / Worksheet 2 only after structural, build, and visual QA passes.

## D007 — Unit 1 verified boundary

**Decision:** Unit 1 passes its bounded edition and GitHub publication gate. The exact PDF is 2,678,755 bytes, SHA-256 `eb7e78affacf8a559d0f52a1c44921633d2fa74a070faa64af58efc32d34a568`, with 25 A4 pages. Translation topology, four-file media rights, two-cycle byte reproducibility, all-page visual inspection, links, privacy, and the 174-record additive backend pass.

**Limitation:** the PDF is untagged; `/Lang=id-ID`, ToUnicode for all fonts, and full-page text extraction pass. Semantic HTML is therefore the planned primary structured accessibility surface.

## D008 — Bounded corpus-choice rationale

**Decision:** keep the exact full boundary at Brenner's 29 lectures plus their 29 matched worksheets. Add no second wholesale spine. After the source sequence, author a separately identified de Rham-cohomology bridge; add a short Lie-group/Lie-algebra primer only if the final role specification still requires it. Petrunin–Zamora remains outside the core and is not currently included.

**Comparison:** Petrunin–Zamora's 214-page book is excellent for curves and surfaces but cannot supply the abstract-manifold/forms/Stokes/connections half. The 919-page Dionne + Joyce + Petrunin–Zamora composite is broader in selected places but imposes three source and license surfaces, nonstandard downstream permission wording for Joyce, more component-rights and connective work, and still lacks a solved advanced practice sequence. Brenner is the most coherent buildable single-course edition design; its de Rham and possible Lie gaps are bounded and honest.

**Self-study gap:** the frozen Brenner corpus has 576 unique exercises, 84 public solution pages, 492 exercises without a public solution, and no populated worksheet hint fields. This edition must preserve that census and may later add a separately provenanced mastery layer; it must never imply that the source supplies complete hints or solutions.

## D009 — Unit 2 verified local boundary

**Decision:** accept the cumulative Indonesian reader through Lecture 2 and Worksheet 2 as the second verified production boundary and advance the cursor to Lecture 3 / Worksheet 3.

**Evidence:** the exact 44-page A4 PDF is 3,152,320 bytes with SHA-256 `6312b4df706d0f08eeb9f37da0abda3428b5448dce54781d0f52eb9c8db5c385`. All seven Unit 2 translation surfaces pass manifest-aware topology checks and the independent final mathematical audit has no remaining P1, P2, or P3 finding. Two clean three-pass build cycles are byte-identical. All 44 pages pass visual inspection; the structural verifier passes A4, language, ToUnicode, extraction, link, active-content, and privacy checks. The PDF remains honestly disclosed as untagged.

**Closure:** Unit 2 contains 19 exercises, exactly five source-supplied solutions (1, 2, 7, 12, 13), and two public-domain media files. Corrections O011-CORR-0012 through O011-CORR-0027 are explicit. The additive backend contains 357 schema-valid records; Unit 1's frozen 174-record slice remains byte-identical and Unit 2 adds 183 records. Terminal receipt: `qa/unit-02/UNIT_02_QA.md`, SHA-256 `ef1d89de134f4f9bca59513e8bc3790c9121e6b92d0dae5e67aa0fc882803e4f`.

**Publication boundary:** the verified Unit 2 source/backend/reader tree was pushed as bounded content commit `500b2ce2cbc4eef0f1c443a2e5a22ab36ee9313a` and prepared for release tag `v0.2.0-unit-02`. Anonymous public-byte verification is recorded separately in the publication receipt after the release transaction.

## D010 — Bounded overlap recheck

**Decision:** retain sole ownership of O011 in this task and continue with Brenner Unit 3. A 2026-08-22 narrow read of the exact coordinator registry, dispatch, and execution-log files still assigns O011 only to task `01a01f48-83f5-7862-80ca-35729193814e`.

**Boundary:** O004's Petrunin geometry corpus, O012 algebraic topology, and O016 Brenner *Algebraische Kurven* remain separate lanes. The coordinator's status prose for O011 is an older Unit 1 snapshot, but its ownership row is unambiguous; no duplicate corpus or write-path owner was found.

## D011 — Unit 2 public preservation

**Decision:** preserve the verified cumulative Unit 2 boundary as GitHub release `v0.2.0-unit-02` in the existing edition lineage.

**Evidence:** the release is public, not a draft or prerelease; its tag points to commit `2a1a0fa75462e70278a2b9d4aaaf759bfc5788ee`. Anonymous download returned one PDF asset of 3,152,320 bytes with SHA-256 `6312b4df706d0f08eeb9f37da0abda3428b5448dce54781d0f52eb9c8db5c385`, exactly matching the verified local artifact. Anonymous tag-raw readback reproduced `README.md`, `UNIT_02_QA.md`, and the 202-row staged-blob release manifest; its PDF and QA rows match the public bytes. See `qa/unit-02/PUBLICATION_RECEIPT.md`.

## D012 — Wrapper-owned centered reader geometry

**Decision:** the portable cumulative reader owns an A4 page frame with centered 22 mm margins. The historical Brenner preamble's explicit `oddsidemargin`, `evensidemargin`, `textwidth`, `textheight`, `topmargin`, and `footskip` assignments are retained only as commented provenance and no longer override the wrapper geometry.

**Reason:** those legacy assignments narrowed and offset the reader column after the wrapper had configured the page, producing the visibly under-filled, inconsistently centered pages reported by the user. Neutralizing only those page-frame assignments is additive: it changes no frozen authority, translation, formula, identifier, media, or rights surface. The final cumulative Unit 3 reader is 56 centered A4 pages; two clean build cycles are byte-identical, all build logs are free of layout warnings, and all pages pass fresh visual and structural inspection.

## D013 — Unit 3 verified local boundary

**Decision:** accept the cumulative Indonesian reader through Lecture 3 and Worksheet 3 as the third verified production boundary and advance the source cursor to Lecture 4 / Worksheet 4.

**Evidence:** the exact 56-page centered A4 PDF is 3,596,282 bytes with SHA-256 `aee7f335c8d8110feb7b70448c70680a30700285131d5a1b4e4aeb2f2d04b46a`. All four Unit 3 translation surfaces pass manifest-aware topology checks; the independent post-repair mathematics audit has no remaining P1, P2, or P3 finding. Two clean three-pass build cycles are byte-identical and have no warning/error/layout-warning matches. All 56 pages pass visual inspection; the structural verifier passes A4, language, ToUnicode, extraction, bookmark, link, active-content, and privacy checks. The PDF remains honestly disclosed as untagged.

**Closure:** Unit 3 contains 21 exercises, exactly two source-supplied solutions (7 and 16), and three component-licensed media files. Corrections `O011-CORR-0028` through `O011-CORR-0037` are explicit. The additive backend contains 591 schema-valid records; the 357-record Unit 1–2 prefix remains byte-identical and Unit 3 adds 234 records. Terminal receipt: `qa/unit-03/UNIT_03_QA.md`, SHA-256 `7781e297f7fb1688e271c8b7cc507d8efeac2d25b9ea8f84b046e3b68e3d9943`.

**Boundary:** this completes one edition-production unit, not the 29-unit edition and not the separate curriculum-selection decision. The verified tree is authorized for preservation as `v0.3.0-unit-03`; anonymous public-byte evidence follows in the publication receipt.

## D014 — Unit 3 GitHub publication temporarily blocked

**Decision:** retain exact local content commit `5fb8d2716f0f4b0a1596178f0ab69a5cb22bbd93` as the pending `v0.3.0-unit-03` boundary and continue contiguous Unit 4 production. Retry publication at the next substantial checkpoint; do not repeatedly hammer GitHub or falsely claim a public tag/release.

**Evidence:** at 2026-08-22T07:13:00Z the push to the existing official edition repository returned HTTP 403 with GitHub's explicit response that the account is suspended. A bounded authenticated `/user` check using the separately supplied credentials returned the same 403 suspension response for the valid token and HTTP 401 `Bad credentials` for the second candidate. No credential value was emitted or retained. Unit 2 therefore remains the latest anonymously verified public boundary.

**Boundary:** this is external publication friction, not a defect in the verified Unit 3 files and not a reason to stop translation. No alternate repository, duplicate release, or upstream contact is authorized or created.

## D015 — Unit 4 live semantic order retained

**Decision:** retain the exact frozen live Unit 4 order: self-adjointness Theorem 4.7, diagonalizability Corollary 4.8, then the graph-coordinate Lemma 4.9. Do not reorder the derivative to match the sole historical 2023 PDF witness.

**Reason:** the revisioned semantic/transclusion graph is the admitted editable authority. In the live order, Corollary 4.8 depends only on Theorem 4.7, the graph lemma depends only on Lemma 4.6 and Theorem 4.7, and the earlier forward reference to Corollary 4.8 resolves correctly. The official PDF's alternative Lemma 4.8 / Corollary 4.9 order is useful historical evidence but is not the production master.

**Boundary:** this decision preserves current topology only. The graph lemma's false operator formula is independently corrected under `O011-CORR-0043`; retaining the live order is not evidence that the live mathematics is error-free.

## D016 — Unit 4 verified local boundary

**Decision:** accept the cumulative Indonesian reader through Lecture 4 and Worksheet 4 as the fourth verified production boundary and advance the source cursor to Lecture 5 / Worksheet 5.

**Evidence:** the exact 72-page centered A4 PDF is 3,666,928 bytes with SHA-256 `04f84c2d7abdc721cb0ebafcd4e39c230a01faf60665f84d5e7124bf2574319b`. All four Unit 4 translation surfaces pass manifest-aware topology checks; the independent post-repair mathematics audit has no remaining finding. Two clean three-pass build cycles are byte-identical and have no warning, error, layout-warning, missing-glyph, or undefined-reference match. All 72 pages pass visual inspection; the structural verifier passes A4, language, ToUnicode, extraction, bookmarks, links, active-content, and privacy checks. The PDF remains honestly disclosed as untagged.

**Closure:** Unit 4 contains 15 exercises, exactly two source-supplied solutions (7 and 10), and zero media files. Corrections `O011-CORR-0038` through `O011-CORR-0045` are explicit. The historical official PDF witness remains local-only and excluded from release because its internal and Commons license signals disagree. The additive backend contains 813 schema-valid records; the 591-record Units 1-3 prefix remains byte-identical and Unit 4 adds 222 records. Terminal receipt: `qa/unit-04/UNIT_04_QA.md`, 7,843 bytes, SHA-256 `81ae622d1d299a79e4ccaae150176ebc9eafe8b0f502be9852bcf729c21ae037`.

**Boundary:** this completes one edition-production unit, not the 29-unit edition and not the separate curriculum-selection decision. The verified tree is authorized for bounded GitHub preservation; public release is claimed only after successful push and anonymous byte readback.
