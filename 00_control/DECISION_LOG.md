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

## D017 — Unit 4 GitHub publication externally blocked

**Decision:** retain exact local content commit `f04e23367a6b11dbe9cd375150f5333944061910` as the pending cumulative Unit 4 boundary and continue contiguous Unit 5 production. Retry once at the next substantial checkpoint; do not repeatedly push, create a duplicate repository, or claim absent Unit 3/4 tags or releases.

**Evidence:** at 2026-08-22T16:00:31Z both the ordinary HTTPS push and one explicit retry with the first supplied credential returned HTTP 403 and GitHub's exact `Your account is suspended` response. The second supplied credential returned HTTP 401 `Bad credentials` at `/user` and was not used for another push. Anonymous repository and historical Unit 2 release API reads returned HTTP 404 at 2026-08-22T16:00:46Z; GitHub's official status endpoint reported `All Systems Operational` at 2026-08-22T16:00:56Z. Sanitized receipt: `qa/unit-04/PUBLICATION_BLOCK_RECEIPT.md`.

**Boundary:** the block is external account state, not a defect in the verified edition. Unit 2 remains the latest historically published and byte-verified release, though the suspended account currently hides the entire repository lineage.

## D018 — Root-selected complete O011 architecture

**Decision:** retain the complete 29-lecture/29-worksheet Brenner course as the core and extend this same exclusive lane with (a) all ten separately frozen official example-exam forms, (b) one original CC BY-SA 4.0 Lie-group/Lie-algebra bridge, and (c) one original CC BY-SA 4.0 de Rham/differential-topology bridge. The finite original assessment closure is 38 solution-bearing items: 12 exercises per bridge, two four-problem mastery checks, and the currently estimated six missing-exam solutions.

**Authority:** curriculum-root decision file `37_O011_SELECTION_AND_EXISTING_TASK_HANDOFF_20260822.md`, 17,535 bytes, SHA-256 `e6dab7bd6246af82991eb510af1c526fe06dbb641584335b933229b168d51c0a`. The linked live exam census of 123 actual occurrences, 117 solution links, and six gaps is selection evidence only; the exact recursive freeze must recompute it. Marcello Seri 1.9.4 is CC BY-NC-SA comparison evidence, not a translation or prose donor.

**Reason:** this closes D50's Lie and de Rham gateways, self-study practice, and cumulative assessment without replacing the coherent admitted course, importing a heterogeneous second spine, or creating a ShareAlike license conflict.

**Terminal boundary:** O011 is complete only after all 29 pairs, the frozen ten-exam bank, both original bridges, all recomputed missing-exam solutions and 32 bridge/mastery items, exact rights and occurrence mappings, centered semantic HTML and A4 PDF, deterministic backend, full final QA, correct-lineage publication, and anonymous public-byte verification.

## D019 — Unit 5 verified and independently preserved through Zenodo

**Decision:** accept the cumulative Indonesian reader through Lecture 5 and Worksheet 5 as the fifth verified production boundary, advance the source cursor to Lecture 6 / Worksheet 6, and preserve Unit 5 immediately in the clean Zenodo concept lineage whose draft/record is `22059978`, concept record is `22059977`, and reserved DOI is `10.5281/zenodo.22059978`.

**Evidence:** the exact 86-page centered A4 PDF is 4,385,370 bytes with SHA-256 `44ef3bc7f4c9de8a9ffd3a747ea71c2102de6f26814718492bc63fd40e4af5ce`. Unit 5 contains 15 exercises, exactly one source hint at Exercise 13, exactly one source-supplied solution at Exercise 1, and one component-licensed figure. Corrections `O011-CORR-0046` through `O011-CORR-0053` are explicit. Two clean build cycles are byte-identical; all 86 pages pass visual inspection; mathematical, structural, link, privacy, rights, and backend gates pass with the disclosed untagged-PDF limitation. The additive backend contains 969 records, with the 813-record Units 1–4 prefix preserved byte-for-byte. Terminal receipt: `qa/unit-05/UNIT_05_QA.md`, 7,548 bytes, SHA-256 `ccab83c1b3c83db7cde8631d015db6fc2d43a44fcde518684780178cdbc731b9`.

**Publication boundary:** GitHub is externally unavailable because the account owner reports a VPN-triggered security suspension and an active support ticket. Do not retry GitHub while that ticket remains open. Zenodo is an independent preservation repository and is maintained at this incomplete but substantial boundary. The public deposit must contain the verified PDF, a deterministic source/backend/provenance ZIP, and release notes; use record-level `Other (Open)` for the mixed-license package while retaining exact component licenses, then prove every public byte anonymously in a sanitized receipt. This preserves Unit 5 without claiming that the 29-unit edition is complete.

## D020 — Same-concept corrective Zenodo version after portability audit

**Decision:** create one corrective version in Zenodo concept `10.5281/zenodo.22059977`, without changing the Unit 5 PDF or mathematical edition, because the first immutable version's source ZIP retained two non-secret machine-local path locators. Sanitize those public control references, keep the exact local locator in `00_control/PRIVATE_LOCAL_LOCATORS.md`, exclude that file from public staging, rebuild the deterministic ZIP, and anonymously verify the corrective version. This is complete at record `22060146`, DOI `10.5281/zenodo.22060146`; the concept DOI resolves to it.

**Reason:** a public preservation bundle should be portable and must not expose a machine-local user path even when it contains no credential. Zenodo's published version is immutable; a transparent new version in the same concept is the non-duplicative correction. The earlier DOI remains provenance history and must not be misrepresented as the clean latest version.

**Verified clean bytes:** PDF 4,385,370 bytes, SHA-256 `44ef3bc7f4c9de8a9ffd3a747ea71c2102de6f26814718492bc63fd40e4af5ce`; sanitized ZIP 5,819,316 bytes, SHA-256 `d2893bcc064ff1674084312ed97e79a44dfc50926275cc30a9333191233210be`; release notes 4,515 bytes, SHA-256 `36a55ac332878c6f2c460f58965a22363ba1b1e2cd54ef0311e0a97ad6423bcb`. Anonymous downloads match all three. The public ZIP has 465 members, an exact 464-row manifest, no machine-local path sequence, and no exact Zenodo or Figshare credential value. Receipt: `qa/unit-05/ZENODO_PUBLICATION_RECEIPT.md`.

## D021 — Figshare uses a CC0 zero-file link item, not a false byte mirror

**Decision:** publish Figshare article `33314790`, DOI `10.6084/m9.figshare.33314790.v1`, as a zero-file CC0 metadata item linking to Zenodo concept `10.5281/zenodo.22059977`. Keep Holger Brenner as the sole article author. Add it to project 280296 and append it to Indonesian collection 8668413 without replacing existing members.

**Reason:** the account offers CC BY 4.0, CC0, MIT, GPL variants, and Apache 2.0, but no CC BY-SA or mixed/Other article license. Figshare has one license per article and no per-file license field. Uploading the mixed-license edition bytes under any offered license would be false. CC0 therefore applies only to the metadata/link record; all work bytes and exact component rights remain on Zenodo.

**Public verification:** anonymous article readback proves the exact title, status `active_partial`, author, categories, description, CC0 license ID 2, four related-material links, and zero files. Anonymous project and collection reads include article 33314790. Concurrent authorized collection additions advanced the immutable version series; the final check found the item in version 17, DOI `10.6084/m9.figshare.c.8668413.v17`, with 18 members. Receipt: `qa/unit-05/FIGSHARE_PUBLICATION_RECEIPT.md`.

## D022 — Reader-first linked Figshare revision and six-file Zenodo surface

**Decision:** supersede D021's zero-file presentation without creating a second work. Keep article ID `33314790` and publish version 2, DOI `10.6084/m9.figshare.33314790.v2`, with the current Unit 5 PDF as its sole visible external linked file. Put exact links for the compact resumable source/backend ZIP, `LICENSE.md`, release notes, file manifest, and checksums in the public description. Preserve the source bytes in the existing Zenodo concept by publishing record `22060387`, DOI `10.5281/zenodo.22060387`, version `2026.08.22-unit05-r2`; do not upload or relicense them through Figshare.

**Platform and rights reason:** official Figshare OpenAPI proves `FileCreator.link` creates a visible remote file, but the article still has one catalog license and files have no license override. The live account still lacks CC BY-SA/mixed licensing. A bounded transaction additionally proved that Figshare accepts only one linked file per item: the second link returned HTTP 400, `Cannot add a linked file to an article that already has file(s).` The public description therefore scopes CC0 only to Figshare metadata/link arrangement, states that all linked edition bytes are not CC0, and identifies their actual CC BY-SA 4.0/file-specific rights. This yields the requested reader-first surface without a false license claim.

**Capacity evidence:** before publication, project 280296 contained 22 articles, 42 hosted files, and 133,963,919 bytes, which is below the 20,000,000,000-byte cap. The six linked targets total 10,212,844 bytes, below the 500,000,000-byte lane cap; Figshare counts the single external file as zero hosted bytes.

**Public verification:** anonymous article version-2 readback proves the canonical PDF filename and Zenodo URL, book type, Holger Brenner authorship, `active_partial` scope, and the rights disclaimer. Anonymous downloads of the PDF plus all five companion links match local byte counts, MD5, and SHA-256. Article 33314790 is present in project 280296 and was verified in Indonesian collection version 32, then again after a concurrent addition in version 33, DOI `10.6084/m9.figshare.c.8668413.v33`, with no other member removed. Receipts: `qa/unit-05/FIGSHARE_PUBLICATION_RECEIPT.md` and `qa/unit-05/ZENODO_PUBLICATION_RECEIPT.md`.

## D023 — Unit 6 verified local boundary

**Decision:** accept the cumulative Indonesian reader through Lecture 6 and
Worksheet 6 as the sixth verified production boundary and advance the source
cursor to Lecture 7 / Worksheet 7. The edition remains `active_partial`.

**Evidence:** the settled centered A4 PDF is 105 pages, 4,765,606 bytes, SHA-256
`40bf26d196ff04c38c6c99e8e9669a86bb5e6d31124b904b7ad154e7948cdec1`. Unit 6
contains 18 exercises, no source hints, and exactly three source-supplied
solutions (2, 6, and 9); the cumulative reader contains 107 exercises and 14
source-supplied solutions. The unit adds one CC BY-SA 3.0 media asset, and
corrections `O011-CORR-0054` through `O011-CORR-0069` are explicit. Two clean
three-pass builds are byte-identical; structural, mathematical, prose,
visual, rights, privacy, terminology, and backend gates pass with the known
untagged-PDF limitation. The additive backend contains 1,173 records; the
969-record Units 1–5 prefix remains byte-identical. Terminal receipt:
`qa/unit-06/UNIT_06_QA.md`.

**Boundary:** this completes Unit 6 only. The ten-exam freeze, both original
bridges, 29-unit spine, HTML surface, and final assessment closure remain open.

## D024 — Unit 6 Zenodo same-concept publication and anonymous readback

**Decision:** preserve the verified Unit 6 checkpoint immediately as the next
version of the existing Zenodo concept `10.5281/zenodo.22059977`, without
creating a competing work or claiming completion. The published record is
`22070425`, DOI `10.5281/zenodo.22070425`.

**Evidence:** the reader-first six-file payload is the 105-page PDF, the
deterministic 1,592,929-byte source/backend/provenance ZIP, exact license
notice, release notes, file manifest, and checksums. The payload totals
6,368,183 bytes and is below the 500 MB lane cap. Publication receipt
`qa/unit-06/ZENODO_PUBLICATION_RECEIPT.json` and independent anonymous
readback `qa/unit-06/ZENODO_PUBLIC_READBACK_RECEIPT.json` prove filenames,
byte counts, SHA-256 identity, API order, concept lineage, and the supported
organization contributor rendering. No credential or private locator entered
the public payload.

**Boundary:** Zenodo is current preservation for this partial checkpoint;
GitHub remains unavailable under the active account-suspension support ticket,
and no GitHub retry or upstream contact occurred.

## D025 — Figshare Unit 6 update stopped before mutation

**Decision:** do not create a duplicate Figshare item or assert a Unit 6
Figshare publication while the existing predecessor article cannot be seen by
the bounded API. The authorized update was closed before any remote mutation.

**Evidence:** article `33314790`, project `280296`, and collection `8668413`
were absent/empty in the bounded API reads; the exact DOI search returned no
item and the DOI page reached an AWS WAF challenge rather than a readable
record. The sanitized evidence is
`qa/unit-06/FIGSHARE_PREPUBLICATION_BLOCK_RECEIPT.md`. No token value is
recorded and no remote create/update/delete occurred.

**Boundary:** retain Unit 5 Figshare receipts as historical evidence only;
retry the same article lineage after predecessor visibility is restored. The
Zenodo publication remains the authoritative public Unit 6 checkpoint.

## D026 — Zenodo RDM publisher recovery path hardened

**Decision:** retain the current Zenodo publication unchanged, but harden the
bounded publisher used for future checkpoints. Canonical InvenioRDM responses
may encode record IDs as JSON strings; draft-file deletion may return 204 with
an empty body; and an authenticated draft listing may contain unrelated
unpublished records. The publisher now normalizes numeric string IDs, accepts
the documented empty DELETE response, filters to `new_version_draft` records
in the expected version range, and rechecks the organization-contributor
anchor when recovering an already exact release.

**Evidence:** `scripts/publish_zenodo_unit06_rdm.py` compiles after the bounded
patch (23,310 bytes, SHA-256
`9bf2059a754e06d235ac4aea9ace3f8d9df91b8552aee5a1250a2dba6703ac42`). The
published Unit 6 six-file bytes are unaffected; the publisher itself is not
part of the public release ZIP. No remote state was changed by this hardening.

## D027 — Unit 7 cursor and bounded source preflight

**Decision:** advance the local source cursor to Brenner Lecture 7 / Worksheet
7 while keeping the translation gate open until the missing expanded-source,
solution, and media closure is frozen. Do not claim Unit 7 admitted or
complete from the root-page identities alone.

**Evidence:** the exact frozen roots are Lecture 7 pageid/revision
`142551/1052941` (4,103 bytes, SHA-256
`d2f680f8365a71bf86be4b798797b5ac3e27e9bf8f4b087a6b810cd5603a99db`) and
Worksheet 7 pageid/revision `142641/905403` (2,624 bytes, SHA-256
`5a2af60e7ab1f920f454c15c1f9af96c1725116fc34e84911f420b5c268da6f8`). The
worksheet has 19 exercise targets (14 practice, 5 graded), all hint fields are
empty, and no Unit 7 solution closure is frozen. Lecture 7 names two figures
and Worksheet 7 names one animation surface; per-occurrence rights/rendering
proof remains open. The bounded preflight is
`qa/unit-07/AUTHORITY_PREFLIGHT.md`.

**Boundary:** next action is exact `/latex` expansion, solution-candidate
closure, and media/animation rights freeze, followed immediately by contiguous
Indonesian translation. No upstream contact or GitHub action occurred.

## D028 — Unit 7 authority closure passed

**Decision:** accept Unit 7's source/rights/solution boundary for translation and
begin the complete Indonesian Lecture 7 + Worksheet 7 pair in source order.
The unit remains unpublished and no target prose is yet claimed.

**Evidence:** `qa/unit-07/AUTHORITY_PREFLIGHT.json` is a PASS receipt (43,426
bytes, SHA-256
`1f7bf32f24c6962b8c8823918f3ed8c76d19fca44c2e03a3773ad52192fd52ec`) with
matching Markdown witness `qa/unit-07/AUTHORITY_PREFLIGHT.md` (6,625 bytes,
SHA-256 `172c80140e8da7b3e41aa9d9124fad2afccf0ced940683c071c292caab3c9ee7`).
The exact expanded TeX, root/surface revisions, all 19 exercise candidates,
three supplied solutions (Exercises 4, 7, and 13), sixteen missing solution
candidates, blank hint fields, and three displayed media assets are frozen.
The assets are `Stereographic projection in 3D.png` (public domain), `Manifold
zahyou3.png` (CC BY-SA 3.0), and `Circle - black simple.svg` (public domain),
each with current Commons bytes, revisions, creators, and rights evidence.

**Boundary:** translation starts now; no Unit 7 PDF/backend/publication is
claimed until the complete pair and its three supplied solutions pass the same
bounded production gates used through Unit 6.

## D029 — Unit 7 animation surfaces preserved separately

**Decision:** preserve the two GIFs embedded by the source solution for
Worksheet 7 Exercise 13 as explicit interactive/downloadable assets, separate
from the three static TeX figures handled by the ordinary media attribution
build. Do not silently turn the animations into static figures or claim that
the PDF alone represents the full source surface.

**Evidence:** `qa/unit-07/INTERACTIVE_MEDIA_QA.json` (1,428 bytes, SHA-256
`a6077a07a4ec03f1a33500781bf3256fa81da9d8efb091318fc6dd59dfdca193`) binds
Commons page/revision, creator, CC BY-SA 4.0 rights, exact bytes, SHA-1, and
SHA-256 for `Aufgabe75.22.1.gif` and `Aufgabe75.22.2.gif`. The compact source
manifest is `source/unit07_interactive_media.json` (1,823 bytes, SHA-256
`79a6509a87fa0da8f96527f798ca02b40d10c223300c439ee08dbdea1d2d3352`); both
binaries are retained under `authority/media`. Static Unit 7 media attribution
is now configured in `source/unit_media.json` (SHA-256
`cc9160ae95b4270e4f2dbb1f10fb9b45f25c8f568b92b866f42889df2ec6c11e`).

**Boundary:** the translated Exercise 13 solution must retain both source
links, captions/alt text, and license attribution; the final reader may expose
the GIFs as offline/downloadable interactive companions even if the PDF
surface cannot animate them.

## D030 — Zenodo Unit 6 lineage cleanliness rechecked

**Decision:** keep Zenodo as the current independent preservation surface for
this incomplete Indonesian edition, using the existing single concept
`22059977`; do not create a second Unit 6 concept or mutate the published
record merely because GitHub is suspended.

**Evidence:** a bounded anonymous check of the exact public API records
`22059978`, `22060146`, `22060387`, and `22070425`, plus the concept query,
found one public version lineage and the latest record `22070425` in state
`done`, version `2026.08.22-unit06`, with six reader-first files. The latest
title and description truthfully identify the partial Unit 6 boundary, contain
no repeated TTP prose, and expose the organization contributor anchor once;
the public readback receipt already proves every published file hash. No
duplicate Unit 6 concept was created and this check caused no remote mutation.

**Receipt:** `qa/unit-06/ZENODO_LINEAGE_HYGIENE_20260823.json`, 1,773 bytes,
SHA-256 `5d88701fc56ede90e4571d37579aed7128ef9acfd7f4214528997ede7b0ee34a`.

**Boundary:** continue the Unit 7 translation and publish its next coherent
checkpoint as the next version of this same concept only after the complete
Unit 7 build, rights, backend, and anonymous-readback gates pass.

## D031 — Authorized Figshare retry still blocked before mutation

**Decision:** retain the existing Figshare article lineage as pending and make
no duplicate or speculative update. The authorized Unit 6 retry stopped at the
public project-membership preflight because article `33314790` was not visible
as a member of project `280296`; no authenticated mutation was attempted.

**Evidence:** `qa/unit-06/FIGSHARE_RETRY_BLOCK_RECEIPT_20260823.md`, 1,105
bytes, SHA-256
`b37ad8c9fc8ec7559bbc2431610b5ba87d5adc61dd26acbf2f23fa61e17de5d3`.
The retry first proved the existing Zenodo record `22070425` and its six
public bytes, and the runtime-only token was not printed or persisted.

**Boundary:** Zenodo remains the authoritative public Unit 6 checkpoint;
retry Figshare only when the same public predecessor/project inventory is
readable. This is not a Zenodo failure and caused no remote Figshare change.

## D032 — Lecture 7 translation boundary passes topology with one declared language delta

**Decision:** accept the complete Indonesian Lecture 7 target as a verified
translation surface and keep Worksheet 7 as the active next cursor. The
reader translation preserves source-order mathematics, formulas, protected
macro argument topology, media locators, and balanced braces. One intentional
language-only delta translates the `\\mathbed` text argument `mit` to
`dengan`; it is not a mathematical or structural correction.

**Evidence:** `source/units/unit-07/lecture07.id.tex`, 20,270 bytes, SHA-256
`63345458babb8585a53241352c8c3818e694136cc4e3074c39ea56702e294b7f`; passing
receipt `qa/unit-07/lecture07_translation.json`, 1,056 bytes, SHA-256
`6d29e1e766a29a41f459ee366b4a0795db71798e7211d5769cc5be40f711d1e8`; and
the exact delta manifest `00_control/LECTURE07_PROTECTED_CORRECTIONS.json`,
667 bytes, SHA-256
`e4f2af5750074228b03dc7cd3ce5eaa0fccae03a1e2c3e5fc11d7efafe17fd70`.
The manifest binds source call hash
`a55617c35cd8ba6e2ba74ccf369b2967a4a2cadd01a748c060f96365c36c78df` to
target call hash
`7d2892ac41b0afef52aa7a593ffc2d3db3db91b10094ffebeb84ddf83a5f8233`.

**Boundary:** this is a translation checkpoint, not a Unit 7 publication or
completion claim. Continue with all 19 Worksheet 7 exercises and the three
source-supplied solutions before building the cumulative reader.

## D033 — Worksheet 7 and supplied-solution translation boundary passes

**Decision:** accept the complete Indonesian Worksheet 7 target and the three
source-supplied solution targets as translation-ready surfaces. The worksheet
retains all 19 exercise occurrences (14 practice, five graded), point markers,
blank source hint fields, source solution links for Exercises 4, 7, and 13,
and both raw animation wikilinks in Solution 13. One protected comparison
macro has a declared language-only delta (`für`/`sonst` → `untuk`/`selain
itu`); formulas, argument topology, and brace profile are unchanged.

**Evidence:** worksheet `source/units/unit-07/worksheet07.id.tex`, 8,029
bytes, SHA-256 `af223f98696a9353e7967d3ac150a8f2f5de3c49bef506c69fe0d452e7717658`;
passing receipt `qa/unit-07/worksheet07_translation.json`, 1,058 bytes,
SHA-256 `bf7e04ed1db79b14fad4f6666f8d6caedc4eae6b6a2bf17ff3cfab010ed65c35`;
delta manifest `00_control/WORKSHEET07_PROTECTED_CORRECTIONS.json`, 642
bytes, SHA-256 `a3fb4ee0fbed8ba0bd0e3a5ef05dd625468d7c16f30004e49815a50506b291c6`.
The three current source-supplied solution targets and passing receipts are:

- Exercise 4: 898 bytes, SHA-256 `fcae797a689655b486d9ffed1fdede2059b0f15f3842cc5f38e1ba21d4499822`;
- Exercise 7: 1,695 bytes, SHA-256 `b85aae3fecf5ff5c316fcd2f496134a2d60203b468d112b97ccda701bb77a49a`;
- Exercise 13: 332 bytes, SHA-256 `b23f0e52a315ac6d47d1849f06d426e5e1815a244cc39c1c6ce741435ba20f37`.

**Boundary:** Unit 7 now has a complete translated lecture/worksheet pair
and supplied-solution closure, but no PDF, backend, release, or publication
is claimed until the clean cumulative build and interactive/media QA pass.

## D034 — Preserve exact Unicode attribution while making the reader build TeX-safe

**Decision:** retain the exact creator string `１３２人目　` in the Unit 7
media manifest and rights metadata, but render the `\\bildlizenz` moving
argument as the ASCII transliteration `132ninme`. The original display caused
the cumulative build to fail when LaTeX wrote the list-of-figures file; this is
a reader-engine compatibility repair, not a change to attribution, source
identity, license, or asset bytes.

**Evidence:** `qa/unit-07/TEX_SAFE_ATTRIBUTION_DECISION.json` records the exact
source and target call hashes and the preserved Unicode value. The target
source remains in `source/units/unit-07/lecture07.id.tex`; the manifest keeps
the Unicode form and its TeX-safe display companion.

**Boundary:** rerun the clean cumulative Unit 7 build and continue only after
the deterministic two-cycle PDF and visual/structural QA gates pass.

## D035 — Unit 7 cumulative reader passes build, mathematics, and visual gates

**Decision:** accept the cumulative Indonesian reader through Lecture 7 and
Worksheet 7 as the next verified reader boundary. The build completed two
clean cycles with three pdfLaTeX passes per cycle; the reader preserves all 19
Unit 7 exercise occurrences, point values, the three supplied solutions, three
static media assets, and both downloadable GIF companion surfaces.

**Evidence:** `output/pdf/geometri-diferensial-manifold-mulus-hingga-unit-07-id.pdf`,
4,950,232 bytes, 117 A4 pages, SHA-256
`8c2cf76230b45d66a8236c0cd92a048809ff5ec0cce343132dd902684cb05ec6`;
`qa/unit-07/build.json`, 9,419 bytes, SHA-256
`bb3b6bc858948291b0fa6a000c57761aef3d055fceae43000b303b1aaaacf08d`;
`qa/unit-07/PDF_BOUNDARY_QA.json`, 8,777 bytes, SHA-256
`06b50304e1ac3f7873c054b6607f689db08f6e65fb583beffaaeb91e7bd39ef0`;
and independent `qa/unit-07/pdf_structural_qa.json`, 58,943 bytes, SHA-256
`b564eaf9b668c056092963158ff2f70aad1a29e254dfa98a1c0c9d43c5a6b649`.
Every page is A4 and text-extractable through two parsers; all embedded font
resources have ToUnicode; sampled title, transition, exercise, solution,
media, and final pages are centered and unclipped. The PDF remains untagged;
semantic HTML is still required and no accessibility overclaim is made.

**Boundary:** this proves the Unit 7 reader, not full O011 completion.

## D036 — Unit 7 additive backend is deterministic and prefix-preserving

**Decision:** accept the 1,363-record stable-ID backend as the machine-readable
companion to the Unit 7 reader. The 1,173-record Units 1–6 prefix remains
byte-identical; Unit 7 adds 190 records, including the three explicit Unit 7
correction identities and the final cumulative reader binding.

**Evidence:** `backend/records.jsonl`, 812,882 bytes, SHA-256
`d9d51a46b84368f50a211a31263bafe8f1588f8e62a5fa4b496b2ff45903b912`;
`backend/records.csv`, 288,506 bytes, SHA-256
`c301009770e1c523d046585c0c83947cab6f856b32b83890d361a919fed5a958`;
`backend/MANIFEST.json`, 11,297 bytes, SHA-256
`1a950183a66bbc837cff27f34cf2f1fc838ad181bc4fbf16e8bd758c1df2068d`;
and passing `qa/unit-07/backend.json`, SHA-256
`387afdb9eef916f34f3b7764bddf1de85dd23bcfef5b640ac7e1585a434588e1`.
The exporter repeated byte-identically with the frozen checkpoint timestamp,
and the verifier passed schema, ID/reference closure, prefix, source/target
binding, rights, media, exercise/solution, correction, and reader-artifact
checks.

**Boundary:** the backend remains additive and is not required to read the PDF.

## D037 — Unit 7 published in the existing Zenodo concept and anonymously verified

**Decision:** preserve Unit 7 as the next version of the existing concept
`22059977`, not as a duplicate concept. Record `22071323`, DOI
`10.5281/zenodo.22071323`, is public with a six-file, 8,349,784-byte payload.
The PDF is the default preview; the compact resumable source/backend archive
contains 317 entries and is 3,390,707 bytes with SHA-256
`80be8761faa2ac90130c5e806b34651dd2729fa49c7110db9979676b1620a73e`.

**Evidence:** publication receipt `qa/unit-07/ZENODO_PUBLICATION_RECEIPT.json`,
3,364 bytes, SHA-256
`092e7373fb9c37c919778b6dc57c03be06a37d0198974b015f57e99d1571ce75`;
independent unauthenticated readback
`qa/unit-07/ZENODO_PUBLIC_READBACK_RECEIPT.json`, 3,388 bytes, SHA-256
`2810f934b3018e2f70f0257fb32fe108c5a9e20177afeddc0b37d55f2522f723`.
All six public downloads match local byte counts, MD5, and SHA-256; the concept
version response contains exactly one `2026.08.23-unit07` version and there is
no matching open draft. Metadata states `active_partial`, preserves the mixed
component-rights boundary, contains the exact provenance identification
`OpenAI Codex gpt-5.6-sol, Ultra`, and keeps the organization anchor out of the
title and descriptive prose.

**Boundary:** GitHub remains suspended and Figshare state is unchanged. Do not
repeat Zenodo lineage hygiene or Figshare visibility/account checks until
external state changes or the next consolidated production milestone.

## D038 — Resume translation in a three-unit batch after terminology QA

**Decision:** before new bulk translation, perform one bounded comparison with
a representative Indonesian-language differential-geometry/manifold source
and propagate only mathematically justified terminology changes through Units
1–7. Then translate Units 8–10 contiguously with bounded per-unit source/math
receipts and defer the next cumulative backend/PDF/semantic-HTML/visual/publication
gate until all three pairs are translated.

**Reason:** this keeps reader production ahead of release ceremony while still
preserving exact per-unit authority and correction evidence. It also prevents
redundant rechecking of the already proved Units 1–7 and unchanged external
repository states.

**Boundary:** do not start Unit 8 reader translation until the terminology
comparison decision is durable; authority preflight may proceed in parallel.

## D039 — Unit 8 authority, exercise, solution, point, and media closure passes

**Decision:** admit the frozen Unit 8 source pair as the next translation
input, subject only to completion of the separate Indonesian terminology gate.
The authority closure contains 21 exercises (17 practice and four graded), 19
total points, blank hint fields, exactly two source-supplied solutions
(Exercises 11 and 13), nineteen solution absences, and zero media occurrences.

**Evidence:** `qa/unit-08/AUTHORITY_PREFLIGHT.json`, 28,269 bytes, SHA-256
`e07f98d81dfc4106d8af085a2d05f1e0c67aa1cff732e72cfc2020c7c32ea833`;
offline verification `qa/unit-08/AUTHORITY_PREFLIGHT_VERIFY.json`, SHA-256
`cd9044e29f821401c271dffb8930ba3985fee5abed4ab01d088e66b1b9ca6623`.
The frozen Lecture 8 TeX witness is 17,329 bytes, SHA-256
`91fef67aac0b5f0f539f73a672d3bb1c79b277986cc5561c0e27801a9973129a`;
the Worksheet 8 witness is 12,693 bytes, SHA-256
`1313fbf0d8d068f5089ee8381dafc811079a404dc0d7c847c3b3bab85afceb9a`;
the two supplied-solution witnesses have SHA-256
`6ae059c8bfa3ea5d0eb6ee3766647fa5b9a85a5592bff3597d3df185e04622a1`
and `31f2e73e81a59c36f23a4f2b35fb1a56399a77d7df3cc2d5b5f43babbc4f7b7d`.

**Repair:** the bounded authority freezer previously failed to count split
point labels such as `4 (1+1+2)`. `scripts/freeze_unit_authority.py`, SHA-256
`ee6ad87df084acfaff839420c590dda4387ae31d525461b14b9926bf69a7483f`,
now validates and sums the leading total consistently with the independent
offline verifier; the corrected Unit 8 total is 19 rather than the false 15.

**Boundary:** no Unit 8 translation, build, backend mutation, or publication is
claimed until the terminology decision is recorded and the translated pair is
verified.

## D040 — Correct stale backend README locally; do not create a ceremonial Unit 7.1

**Decision:** update `backend/README.md` to describe the actual Unit 7 backend,
1,363-record boundary, immutable Units 1–6 prefix, and v7 exporter/verifier.
Do not mint a near-duplicate Zenodo correction version solely for this
documentation file; carry the corrected README into the next consolidated
Unit 8–10 source package.

**Evidence:** the published Unit 7 ZIP has a correct top-level `README.md`,
correct `RELEASE_NOTES_20260823.md`, correct backend data and manifest, and the
v7 scripts, but its nested `backend/README.md` still described the Unit 6
boundary and v6 commands. That nested prose is not an authority, checksum,
reader, or backend-data defect, but its old regeneration command could mislead
a maintainer. The local file now names `scripts/export_backend_v7.py` and
`scripts/verify_backend_v7.py` and states the exact Unit 7 counts.

**Boundary:** retain record `22071323` as an immutable historical checkpoint;
do not obscure the correction or claim its archived nested README was already
updated. The next substantial Zenodo version must include the corrected file.

## D041 — Indonesian field-terminology gate passes without a reader rewrite

**Decision:** retain the existing natural Indonesian primary forms in Units
1–7. Add only field-attested retrieval aliases and the Unit 8 source-order
terms for topological manifolds and charts. Translation may now proceed from
the admitted Unit 8 authority.

**Evidence:** four bounded official-arXiv API probes found no qualifying
Indonesian smooth-manifold/differential-geometry source with public TeX. The
fallback is the official nine-page institutional PDF by Riri Alfakhriati,
Jenizon, and Haripamyu, DOI `10.25077/jmu.7.2.140-148.2018`, 432,411 bytes,
SHA-256
`be4039d4b589f37fe9ae4740269c98473d0d1dba96f3bd88fc8e3d6ce4e5998d`.
It directly confirms `ruang singgung` and `vektor singgung` and supplies
useful retrieval variants, while its mixed English/Indonesian construction and
spelling inconsistencies make it unsuitable as a normative style authority.
The durable decision is `qa/unit-07/TERMINOLOGY_QA_DECISION_20260823.md`,
2,847 bytes, SHA-256
`c2bbc255c2c95371f0c052b9d7a2d1dd2503ce7638c9e8fc4538faac78ee8c0b`.
The 140-row terminology ledger is 12,254 bytes, SHA-256
`c160ea6a34b8292b2f0809ca6103a693e28119f4b9809c05263704d7d1c343ba`.

**Propagation:** no Unit 1–7 reader source changed, so no ceremonial rebuild
or republication is warranted. `manifold smooth`, `manifold topologi`, `ruang
topologi`, `chart`, `koordinat lingkungan`, `reparameterisasi`, and
`Euclidean` remain search aliases rather than forced prose. Primary reader
forms remain `manifold mulus`, `manifold topologis`, `ruang topologis`,
`peta`, `koordinat lokal`, `reparametrisasi`, and `Euklides`.

## D042 — Sanitation must distinguish HTML markup from TeX inequalities

**Decision:** narrow the expansion sanitizer and offline preflight verifier's
residual-HTML test to actual tag syntax. Do not interpret a TeX inequality such
as `b<c`, followed later by `b>c`, as one enormous `<c ...>` HTML element.

**Evidence:** Unit 10 supplied Solution 10 contains the legitimate sets
`b>c` and `b<c`. The earlier regex `</?[A-Za-z][^>]*>` crossed intervening
TeX and falsely rejected the deterministic sanitized source. The official
API response, TeX meaning, and sanitized output were otherwise intact. After
the narrow repair, Unit 10 freezes and the independent offline verifier passes.

**Bindings:** `scripts/sanitize_brenner_expand.py`, 3,606 bytes, SHA-256
`849643e6af5445530ae01e4fccfd067aceba0a48e7bf598c649e6d2b638ed307`;
`scripts/freeze_unit_authority.py`, 49,745 bytes, SHA-256
`d25cef6780436bc9bbd93558acef173f30c5ddb33bdf3b0c73902e37883feaff`;
`scripts/verify_unit_authority_preflight.py`, 13,344 bytes, SHA-256
`62f9bb0139e0f8afe8222bccb450a42a833897a0fd29f10a1f6b91c632ef550a`.

## D043 — Units 9 and 10 authority closures pass before translation

**Decision:** admit the exact frozen Unit 9 and Unit 10 lecture/worksheet
pairs, supplied-solution surfaces, and media as the remaining inputs for the
current three-unit translation batch.

**Unit 9 evidence:** lecture root page/revision `142553/991592`; worksheet
root `142643/896662`; 17 exercises, 13 practice, four graded, 23 points, blank
hints, no source-supplied solutions, and one occurrence of the exact
public-domain `Tangentialvektor.svg`. `qa/unit-09/AUTHORITY_PREFLIGHT.json` is
27,017 bytes, SHA-256
`6425743defefc74dbe17d0870f6f6cfafe58c224474a001ace1c411950f1ba0a`;
offline receipt SHA-256
`ca1c133548a85ac087df3accf58f0e18ccdc9d7ecc3d09495940029d59e21e1a`.
The German lecture/worksheet translation witnesses have SHA-256
`88993b430407a58ad8db4b8006320a3b8ca190fbb02a04d52f3fc8731b55526a`
and `a852a6a793f860d387075bb38be9606cb2c3b26b4558e15323ba61bb127aaa3f`.

**Unit 10 evidence:** lecture root page/revision `142554/1069485`; worksheet
root `142644/906482`; 31 exercises, 26 practice, five graded, 31 points, blank
hints, supplied solutions 9, 10, 15, and 25, and two exact media assets.
`qa/unit-10/AUTHORITY_PREFLIGHT.json` is 46,969 bytes, SHA-256
`123828b49bc6f78bf2ea349f62f95b5a11911f9ac2743ca6b1cf09316f4b6ac4`;
offline receipt SHA-256
`cd1f406ac4786030fb5ca508874e6d79428de9cc0f381d3c074fbf6f788caeac`.
The German lecture/worksheet translation witnesses have SHA-256
`d9958463f904b6d4118203fc759307b1e97d758296ec1aec4b1e6747309bfa07`
and `0bb2340e60fd19551d420565bd9296e259eacf786a4262dc892395c1f2cbb786`.

**Boundary:** these are source-admission receipts, not translation or release
claims. Unit 8 remains the next reader cursor; Units 9 and 10 follow it without
another cumulative publication ceremony in between.

## D044 — Unit 8 translation and explicit mathematical-repair boundary passes

**Decision:** accept the complete Indonesian Lecture 8, Worksheet 8, and both
source-supplied solutions as the first finished reader pair in the Unit 8–10
batch. Advance the production cursor to Unit 9 without running an interim
cumulative build or publication ceremony.

**Evidence:** Lecture 8 is 18,099 bytes, SHA-256
`90574f5e2879e7bc07ee20e5a335d78bd1b84f5f94b52f257dcdd0f3abf6f8bf`;
Worksheet 8 is 13,094 bytes, SHA-256
`8cd886c6c2f9a7019f5e2319d9930a729572e016ee823346200228e3265b40bf`;
supplied Solutions 11 and 13 have SHA-256
`1a55e39744d436cf93afd514a638197019f2e9e139279abbb3576a1704757a2b`
and `73ee95e00976b81b69b5bee684d2f941c39ca413e4dd0f2696f29081456215ed`.
All four `verify_unit_translation.py` receipts pass command, environment,
inline/display math, protected-call, brace, UTF-8, and declared-delta checks.
The consolidated per-unit receipt is
`qa/unit-08/POST_CORRECTION_MATH_QA.json`, 5,279 bytes, SHA-256
`d09f92ff5de7cbacb37c5bd3a0ec61516877d473c3362cd0cdeeb18410af8974`.

**Corrections:** `O011-CORR-0073` through `O011-CORR-0078` disclose and bind
six mathematically necessary source repairs: arbitrary-fiber reduction,
projection-kernel identification, overlap-domain restriction, inverse
regularity in the maximal-atlas definition, the real-scaling condition for a
homogeneous fiber, and the radial factor in supplied Solution 13.
`O011-TRANS-0079` translates three protected German case labels without
altering their formulas. Residual German tokens occur only inside protected
MediaWiki link or input targets.

**Boundary:** Unit 8 has not been added to a claimed cumulative PDF, HTML,
backend, or public release yet. Those gates remain deferred until Units 9 and
10 are also translated and verified.

## D045 — Unit 9 translation and mathematical-repair boundary passes

**Decision:** accept the complete Indonesian Lecture 9 and Worksheet 9 as the
second finished pair in the Unit 8–10 batch and advance the cursor to Unit 10.
Do not interrupt the reader batch with an interim cumulative build or release.

**Evidence:** Lecture 9 is 26,132 bytes, SHA-256
`9e3b12f4168c4f7a8c246c4c9106d1154be237e9080e12e0a21bcd8942d61bba`;
Worksheet 9 is 10,331 bytes, SHA-256
`4079437947ab31c9216e3ee6059badc8cf7d780ead1df93cd5cfb6f1cd7d3e9d`.
Both exact translation receipts pass. The per-unit closure is
`qa/unit-09/POST_CORRECTION_MATH_QA.json`, 4,390 bytes, SHA-256
`57e90ee6c04fcecd5fbc31b23e25d8d3f30f7efaf322101a30ab8f9c867a27be`:
17 exercises, 23 points, blank hints, no source-supplied solutions, and one
exact public-domain `Tangentialvektor.svg` asset.

**Corrections:** `O011-CORR-0080` through `O011-TRANS-0087` bind the local
chart-domain repair, uppercase point notation, valid scalar-reparameterization
domain, the noncanonical higher-jet structure, the missing submersion
hypothesis for dimension `n-m`, the local domains of affine representatives,
the broken display label, and six reader-visible text fragments embedded in
protected math macros. The plural internal fact/exercise subtree was retained
and verified to exist in the frozen recursive export.

**Boundary:** Units 8–9 are not yet claimed in the cumulative PDF, semantic
HTML, backend, or public preservation record. Unit 10 and its four supplied
solutions must close before that consolidated gate begins.

## D046 — Unit 10 translation and mathematical-repair boundary passes

**Decision:** accept the complete Indonesian Lecture 10, Worksheet 10, and
exactly four source-supplied solutions as the final reader pair in the Unit
8–10 production batch. Start one consolidated Units 1–10 PDF, semantic-HTML,
backend, visual, accessibility, reproducibility, and Zenodo-publication gate.
Do not reopen Units 1–7 or run intermediate release ceremonies.

**Evidence:** Lecture 10 is 23,152 bytes, SHA-256
`bafd2d5f8d1307438c42f2b20a1914f143f097ddc7f37c2e1e9b99dccb340044`;
Worksheet 10 is 16,155 bytes, SHA-256
`3a386ddb1a7e29475d54ca052c518b9b7c7447cefb2c6158f1a288c9b816ac4a`.
Supplied Solutions 9, 10, 15, and 25 have SHA-256
`f4d86590a7244ce6006f2d7812700e4038391fe9808bf733b3c731e1d1cfe088`,
`4af0e5d19acc8555b0deb5fd7503008b86bb740f76ef8ce1482ff95d09cc7b22`,
`df54358b3ac368df7d552f21a38f09fbceb0c90055066e25944a11359c5ab2d1`,
and `18c69f5473ffea083ed655dd8542e2e466a0fee07175e355f3125447b26d21d5`.
All six exact translation receipts pass. The per-unit closure is
`qa/unit-10/POST_CORRECTION_MATH_QA.json`, 8,872 bytes, SHA-256
`c81d9c1459af5b32ca7b3e1af89c573c4f5881eec81dab2340d9a4ae39c497a6`:
31 exercises, 31 graded points, blank source hint fields, four supplied
solutions, and two exact file-specific media assets.

**Corrections:** `O011-CORR-0088` through `O011-CORR-0101` and
`O011-TRANS-0102` through `O011-TRANS-0103` disclose and bind the supplied
solution repairs, the required C2 hypothesis for the tangent-bundle level-set
exercise, the two coordinate-diagram repairs, tangent-bundle dimension and
coordinate-map typing, vector-field regularity clarification, equal-dimension
hypothesis for a disjoint union, the missing coordinate-vector-field arrow,
the tangent-bundle notation typo, and two protected visible-text
localizations. No new hints or solutions were invented.

**Boundary:** this decision closes Unit 10 as translated content only. The
Units 1–10 cumulative reader, backend, HTML, build, visual, publication, and
anonymous readback claims remain pending until their consolidated receipts
pass.

## D047 — Consolidated Units 1–10 local reader and backend gate passes

**Decision:** accept the deterministic cumulative Units 1–10 PDF, semantic
HTML, and stable-ID backend as one locally verified reader checkpoint. Proceed
directly to a single reader-first Zenodo version in the existing concept; do
not add an interim release or rerun Units 1–7 gates.

**PDF evidence:** the final PDF is 165 centered A4 pages, 5,733,895 bytes,
SHA-256
`4eaec807347feeab2b3334056d3109d5ce6e5eb30ed3649a507ae6124049856d`.
Two clean build cycles are byte-identical. It contains 195 exercises, all 23
source-supplied solutions, and 17 static media. Structural/accessibility
receipt `qa/unit-10/pdf_structural_qa.json` is 89,821 bytes, SHA-256
`81451a5e7f78f63935e758fa3d277db28b9db252c09c6930fc1cea597c9a47d7`;
visual receipt `qa/unit-10/PDF_VISUAL_QA.json` is 4,250 bytes, SHA-256
`8781c681152580035dca4552f5a3aa0d54c6003caf0a527ccbf4ca3ca4e6fc4b`.
All 165 pages rendered, all fonts are embedded with ToUnicode, all links
resolve or are allowlisted HTTPS, and no private path, secret, active content,
clipping, overlap, or unreadable glyph was found. The disclosed limitation is
that the PDF is untagged; HTML supplies the structured accessibility surface.

**Bounded visual repair:** the canonical legacy `Tangent bundle.svg` has an
oversized malformed viewport. Preserve its exact 23,116 source bytes and
SHA-256
`96e46d20e64c40985d7ddc517824a36ef6546261762c3cd8e277c9a4eab55623`.
Crop only the deterministic print derivative to its ink bounding box with a
fixed white border. The repaired derivative has SHA-256
`ec76e2061dcaf6b2e1bf577eb0c75e525bf89d5139ccf77b8aee25370b37bd7e`,
and the image plus its full caption remain together on physical page 144.

**HTML evidence:** the reflowable entry is 710,428 bytes, SHA-256
`125688aadaade39ded86fb42adc8bfa74005a7fca66623a4c419c79ab36d52d4`;
its 32,562-byte manifest has SHA-256
`c9d6b7ce87feeb7c1621d0ac25e8b4ef3639a2e95140ef4ffe6f330a40b62e8e`.
Deterministic structural receipt SHA-256 is
`b5af7e5e5192b2c19aaeb940907cce58c8340f294d694f130965545d2c1defb9`;
browser visual receipt SHA-256 is
`211ba0a6ad858974d68584c55ef84d9436d748d75433e6b9718cbc3e61e8c58d`.
Desktop/mobile reflow, deep links after math layout, scroll-contained wide
mathematics, captions, alt text, and component rights pass.

**Backend evidence:** preserve exactly 1,888 records: the immutable 1,363-
record Units 1–7 prefix plus 525 Units 8–10/reader-closure records. The six
HTML/PDF/QA surfaces are all-or-nothing without inflating semantic counts.
JSONL is 1,138,347 bytes, SHA-256
`ef614f1d6f74357b65644e06d5667870339f9ee6712bdde028e8b3923e16d132`;
CSV is 414,039 bytes, SHA-256
`409c3d79d99ac17cbf4bf597763221681db00d4fd4c3f7a8cc84c6cd98c9a753`;
manifest is 24,431 bytes, SHA-256
`2c4799664311ecfd5f5ca9bb119d08e356ee2fe1f021f0dbd56b833d5dcf0893`;
QA receipt is 6,667 bytes, SHA-256
`7220cfc60e9c896f67a49fd378c308265995d451c3b8adb95176e2821c9a56ea`.
An independent repeat verifier passes with byte-stable outputs.

**Boundary:** this is a complete local checkpoint, not yet a public release.
Stage exactly one compact seven-file payload, publish it as the next version of
Zenodo concept `22059977`, anonymously read back every file, and record a new
decision. GitHub and Figshare remain unchanged and must not be rechecked absent
an external-state change.

## D048 — Unit 10 existing-concept publication and two anonymous readbacks pass

**Decision:** accept record `22073928`, DOI `10.5281/zenodo.22073928`, as the
public cumulative Unit 10 checkpoint in existing concept `22059977`. It is the
single resumed Unit 10 version draft created from Unit 7 predecessor
`22071323`, not a competing concept or duplicate record. Close the consolidated
Units 1–10 milestone and resume source-order production at Unit 11. Do not
repeat Zenodo lineage hygiene, GitHub, or Figshare checks absent an external-
state change.

**Release evidence:** the exact seven-file payload totals 8,758,132 bytes.
The 165-page PDF remains 5,733,895 bytes, SHA-256
`4eaec807347feeab2b3334056d3109d5ce6e5eb30ed3649a507ae6124049856d`,
and is Zenodo's verified default preview. The reflowable HTML ZIP is 1,260,239
bytes, SHA-256
`6dbffc22f338eab537b42d907c2d6dae9bd2f00c045f7a690f5e96e652663b06`;
the compact resumable source/backend ZIP is 1,758,537 bytes, SHA-256
`0c160e741e02a711bdbbb984a788459ccb1e4ca94f0809f5add25ec50f8beb3a`.
Release-preparation receipt `qa/unit-10/RELEASE_PREPARATION_RECEIPT.json` is
9,513 bytes, SHA-256
`632f2d63476ceb552d729a0507d2a274e8c358909c35feb2a4f7f563db723cbf`.
Metadata preserves the exact title, active-partial Unit 10 scope, licenses,
source and non-endorsement. It carries exactly one `TTP` organization
contributor and no such title or description text; computational provenance is
exactly `OpenAI Codex gpt-5.6-sol, Ultra`.

**Publication and readback evidence:** publisher receipt
`qa/unit-10/ZENODO_PUBLICATION_RECEIPT.json` is 5,011 bytes, SHA-256
`51327022f3f3e28869e44191f1cf76b7784b7de5d164084193bba68c4d0ef3b8`.
Its unauthenticated readback streamed all seven public files and reproduced
every size, SHA-256, and MD5. A separate unauthenticated RDM read and complete
second download produced `qa/unit-10/ZENODO_PUBLIC_READBACK_RECEIPT.json`,
2,351 bytes, SHA-256
`575f2affc4bcdff66f2757da0551540c77c8a4c5a2cd4eb356bb5bb20c8c923c`;
it independently confirmed the record, concept, DOI, version, public status,
seven-file/8,758,132-byte inventory, and exact PDF default preview. Zenodo
normalizes the optional RDM inventory-order field to an empty list and does not
expose PUT sorting for this draft; the actual public order is recorded honestly
and is not used as an identity gate.

**Canonical-source disclosure:** the frozen 23,116-byte public-domain upstream
`Tangent bundle.svg`, SHA-256
`96e46d20e64c40985d7ddc517824a36ef6546261762c3cd8e277c9a4eab55623`,
contains a pre-existing authoring-machine `/home/.../diverse/wiki` string in
its public source bytes. It is not a task-local path or credential. Preserve
the canonical upstream identity rather than silently rewriting it; the
deterministic reader derivative remains separately repaired and hashed.

**Boundary:** Units 1–10 are now translated, cumulatively built, locally
verified, publicly preserved, and twice anonymously byte-verified. O011 is not
complete: Unit 11 is the active cursor, followed by Units 12–29, the official
exam closure, both original bridges, all planned solution-bearing items, final
course builds and QA, and final correct-lineage publication/readback.

## D049 — Unit 11 authority, solution, and media closure passes

**Decision:** admit the exact frozen Unit 11 lecture/worksheet pair for
immediate contiguous Indonesian translation. Include exactly the two supplied
solutions and the one admitted media asset; do not invent a hint or larger
solution layer. After bounded Unit 11 checks, continue to Unit 12 without a
cumulative build or publication ceremony.

**Authority evidence:** Lecture 11 root is page/revision `142555/896335`,
timestamp `2023-05-16T06:03:25Z`; Worksheet 11 is `142645/906316`, timestamp
`2023-07-14T06:57:07Z`. Their exact expanded German TeX witnesses are 16,043
bytes, SHA-256
`d5efb6e57e399693d36cec162df0a897ce898f188dc2b5eb30eb78c840e9c642`,
and 19,538 bytes, SHA-256
`5738bc01a606b4a6e1958e9698bbdc0d612afce9cddc793ce7ddf8d83eb128b6`.
Preflight `qa/unit-11/AUTHORITY_PREFLIGHT.json` is 39,646 bytes, SHA-256
`ebefb49d62801e3aaa41e3e4cc979d88a75940bf84e2cb68e621a7922665d963`;
its freshly repeated offline verifier is 519 bytes, SHA-256
`f519b5b07a348a6a928df663e392c70eac908430788c807c9c9e024b2a570e22`.

**Assessment closure:** Worksheet 11 has 39 exercises: 33 practice and six
graded Exercises 34–39 worth `5, 6, 3, 2, 2, 4 (1+1+1+1)` points, totaling
22. Every source hint field is blank. Current supplied Solutions 10 and 14
exist; their expanded TeX witnesses have SHA-256
`ee29d4737ab74b19dd54635c9429f9db3df2b77b191626e70ded1d3cd3293515`
and `88e97dcf61c9bb35387862134236635b54ef81fc9bd847e7623da0e5757b5af0`.
The other 37 conventional candidates are absent. Exact solution closure
`qa/unit-11/solution_closure.json` is 21,892 bytes, SHA-256
`46cd6d8fe08f3433f7514d1ca64ab1aebb7aec2eca84357d23a84152d0cbf329`.

**Media closure:** Unit 11 has one occurrence of one exact asset,
`Toroidal coord.png`, 151,522 bytes, SHA-256
`f09c9189157aedc9c9d516d24ffdf80c6e3d413101e2eb38e3c0cda996c5d618`.
Commons identifies DaveBurke as creator and CC BY 2.5 as the file license;
rights-critical current fields match the frozen whole-course manifest.

**Boundary:** authority admission is complete; reader translation of Lecture
11, Worksheet 11, Solutions 10 and 14, and the media attribution surface is
active. No Unit 11 reader, backend, or public-release claim exists yet.

## D050 — Unit 11 reader and bounded per-unit QA pass

**Decision:** accept the complete Indonesian Lecture 11, Worksheet 11, and
exactly source-supplied Solutions 10 and 14 as the next source-order reader
boundary. Continue directly to Unit 12; do not run a cumulative PDF, HTML,
backend, visual, or publication ceremony at this single-unit boundary.

**Reader evidence:** Lecture 11 is 16,590 bytes, SHA-256
`c6d5266be60eec3911d841213fb4333b51c6555266915e0b64438c3c2bf3d4fc`;
Worksheet 11 is 20,513 bytes, SHA-256
`b92ce3a51ad8b56acbd01f26673fb3512faee6b7bf17b8ccb6365c2091af6941`.
Supplied Solutions 10 and 14 are 1,351 and 795 bytes with SHA-256
`77e8efefffb8acded4a11f1e258134d8d26aef4e8cb517a67dd8a3d1565bf2e9`
and `d8cd8d24a7dba0865dda2bd83e10f1c96c0dc100c9e95de6fcaf723f8a714683`.
All four structural/protected-math translation receipts pass. The prepared
fragments have SHA-256 `a3f689e02a8c0aede0f924f2bfd1205957a14e0994268ebe641f346a1367148d`,
`0f286913dd79414679789a2b9ff27b8b877716365d2d523de9586bdcd9f33282`,
`b256cc638b0a72033c0b3a63659e38ea053803044712252f1fd863f73dbd5ed3`,
and `1dcb59a601f85acebe8da790e41d62143ac4115c36b1e20d2b15b8abced3f237`.

**Closure evidence:** all 39 exercises remain in order, with 33 practice and
six graded items totaling 22 points; all source hints remain blank and only
Solutions 10 and 14 are present. The exact CC BY 2.5 toroidal-coordinate PNG
and the exact CC BY-SA 4.0 downloadable animation link are preserved.
Corrections `O011-CORR-0104` through `O011-CORR-0113` are explicit. An
independent read found two low-severity Indonesian phrases, both refined and
reverified before closure. `qa/unit-11/POST_CORRECTION_MATH_QA.json` is 8,548
bytes, SHA-256
`e21ae4636c83f5dae3090a4f8cee5c6187e65546000f7b2b0fe67744e1e83d20`.

**Boundary:** Unit 11 is translated and bounded-QA complete. Units 1–10 remain
the latest cumulative public checkpoint; Unit 12 is active in the same local
production batch.

## D051 — Unit 12 authority and deterministic animated-media fallback pass

**Decision:** admit the exact frozen Unit 12 lecture/worksheet pair, exactly
supplied Solutions 11 and 12, and both source media assets for immediate
Indonesian translation. Preserve the canonical animated GIF for HTML/download
and derive its frame-zero PNG deterministically for static PDF rendering.

**Authority evidence:** Lecture 12 root is page/revision `142556/1020020` and
Worksheet 12 is `142646/906760`. Their exact German TeX witnesses are 20,823
bytes, SHA-256
`6f7ce6f22e12cc56f2de7874634f1a96cc65211264873c47ed485f2ea1e0cc32`,
and 19,055 bytes, SHA-256
`d88e5c3200b8ff324d1d720ee78a44a2c2c23d4ce69c29e7c999526b7226b1f9`.
Preflight `qa/unit-12/AUTHORITY_PREFLIGHT.json` is 39,355 bytes, SHA-256
`334789a72179046d0ef8bc741c256f953ab04e1f6728663ec4dd44ba0e01f6fa`;
the offline verifier is 519 bytes, SHA-256
`5f6bd731ef88456c7e7394ea13c6d05ec98c2129cd4c283f3b79876ecb3e7073`.
Worksheet 12 has 29 exercises: 25 practice and four graded items totaling 15
points. Every hint field is blank; exactly Solutions 11 and 12 exist.

**Media evidence:** canonical `Fiddler crab mobius strip.gif` is 1,557,242
bytes, SHA-256
`059c8643c42a0561e5ee5efe52cd5fc59de0879ddd3870fa200f4ae66a2fc69a`,
by Hamishtodd1 under CC BY-SA 4.0. It has 24 frames and 12.4 seconds of source
timing. Its deterministic frame-zero PNG is 145,058 bytes, SHA-256
`15f45aee985375fe99b19f30dc62268d286db4caf103cf4fc066a8951cc43790`.
Canonical `Inclusion-exclusion.svg` is 6,804 bytes, SHA-256
`d37d8453528fa90456c473f705741e6c50bc04ad2cd76e9d0f4199a9aa702df3`,
creator unknown and public domain; its deterministic PNG is 136,273 bytes,
SHA-256
`68825ea402cfdb1cd9831891815788b481ae16189f3f9d470aa07ab787256e19`.
Two independent media-preparation cycles were byte-identical. The media
receipt is 4,350 bytes, SHA-256
`b4ddde72b4d43261bb90a2f0f6fe360ed5e3d83b5c46c91a3bfd2e7737dd9fda`
after a deterministic rebind to the append-only media configuration through
Unit 13; Unit 12 media outputs themselves remain byte-identical.

**Boundary:** authority, solution, rights, and static-print fallback admission
passes. Complete Unit 12 reader translation and bounded QA next; no cumulative
build or release is due yet.

## D052 — Unit 12 reader and bounded per-unit QA pass

**Decision:** accept the complete Indonesian Lecture 12, Worksheet 12, and
exactly source-supplied Solutions 11 and 12 as the next source-order reader
boundary. Continue directly to Unit 13. Defer the cumulative PDF, semantic
HTML, backend, visual, accessibility, reproducibility, and publication gate
until Unit 13 closes the planned three-unit batch.

**Reader evidence:** Lecture 12 is 21,299 bytes, SHA-256
`993875dc8f085e0bddaaac813179dade7e5a2928d53c1e575c7c4f09bc6074f1`;
Worksheet 12 is 19,711 bytes, SHA-256
`23b1db1c6d7c38a64f62c83c704084ece00f78943165aa02007e5766bce12d37`.
Supplied Solutions 11 and 12 are 2,143 and 1,306 bytes with SHA-256
`fcee4e2a7cbf9c36b053c0831c5ac51aa99553870ddf7e9b10c7b04ac301a210`
and `3efe62a19d10bbf4f36301f6753f0f29f7480030dd2a1fe7a0ae914b1957d23f`.
All four final translation receipts pass, consume every declared delta, and
verify every evidence-only anchor. Prepared-fragment SHA-256 values are
`3dd57fbe38399ceff2118b7bffcf69b845b72e397ba212d7c56e0f417951554c`,
`1d9f57206794cbc4229d0435d79ea008003cfd49450f26c22c50d77c0d686daf`,
`be75ff34b04de199f5c6a7d1c65d949f2623fcfb56746813c85ec3b8c4a3aa4f`,
and `0b57624a796e6e528b7e1e0129b094ab1a50423bd223c34c150dd91c39492540`.

**Closure evidence:** all 29 exercises remain in source order, with 25
practice and four graded items worth `4, 4, 3, 4`, totaling 15 points. Every
source hint is blank; exactly Solutions 11 and 12 are present. The canonical
1,557,242-byte, 24-frame Möbius-strip GIF remains SHA-256
`059c8643c42a0561e5ee5efe52cd5fc59de0879ddd3870fa200f4ae66a2fc69a`,
Hamishtodd1 / CC BY-SA 4.0; its deterministic frame-zero PNG is SHA-256
`15f45aee985375fe99b19f30dc62268d286db4caf103cf4fc066a8951cc43790`.
The canonical public-domain inclusion-exclusion SVG remains SHA-256
`d37d8453528fa90456c473f705741e6c50bc04ad2cd76e9d0f4199a9aa702df3`;
its deterministic PNG is SHA-256
`68825ea402cfdb1cd9831891815788b481ae16189f3f9d470aa07ab787256e19`.
File-specific rights, nonempty Indonesian descriptions, and the static-PDF
animation disclosure are preserved.

**Correction and review evidence:** twenty-one uniquely assigned records,
`O011-CORR-0114` through `O011-TRANS-0134`, disclose all mathematical,
translation, accessibility, and rights repairs. They include the rank/index
repairs, kernel-subbundle dimension, malformed punctured space, reversed
quotient, ill-typed tangent map, transition-map directions in both supplied
solutions, rights correction, and terminology normalization. No correction is
silent. The final terminology audit also normalized three stale `real`
spellings to the admitted `riil`. The independent review is 2,764 bytes,
SHA-256
`c29deb53a599bc288661b0c86ce0c7a5f5c740a4306f22f1ad569e6d2686df29`.
The bounded semantic-HTML animation regression proves a static-first default,
keyboard Play/Stop, canonical GIF playback/download, and reduced-motion
handling without changing the public Unit 10 baseline; its receipt is 3,506
bytes, SHA-256
`0b84a482e4b5af062a87535eb80b23ca47dc13afd82d04546f4c84ac8907a32e`.
Final binding receipt `qa/unit-12/POST_CORRECTION_MATH_QA.json` is 11,392
bytes, SHA-256
`3f04301f4e26d64b9cd1adf240a8fd4b29265cb0265dca51bfa7bfe455ce1674`.

**Boundary:** Unit 12 is translated and bounded-QA complete. Units 1–10 remain
the latest cumulative public checkpoint; Unit 13 authority closure and reader
translation are active. No repository-service check or release ceremony is
repeated at this per-unit boundary.

## D053 — Unit 13 authority, solution, media, and anomaly closure pass

**Decision:** admit the exact frozen Unit 13 lecture/worksheet pair, exactly
the eight supplied solutions, and the one source media asset for immediate
Indonesian translation. Preserve the official raw responses and disclose all
three observed source/expansion anomalies. Correct the false antipodal-parity
sentence only in the target under the normal protected-correction convention.

**Authority evidence:** Lecture 13 root is page/revision `142557/897201` and
Worksheet 13 is `142647/905568`. Their exact expanded German TeX witnesses are
23,322 and 9,636 bytes with SHA-256
`3416c47b07bef5b03ca2d70e4dae74691342555a207663af61d908ee0fe05da5`
and `bf090474d14ea826ca31ceca8aae01b90c4600cd95f48ba74bd250fca254eb8d`.
Preflight `qa/unit-13/AUTHORITY_PREFLIGHT.json` is 51,347 bytes, SHA-256
`270d2670e7609ea33c54fdef4e0e00005740375ba85e4ad506d2cf826a26d559`;
offline verification is 567 bytes, SHA-256
`b6dd0288f66d7f05b048ff67848c78f86f168ef4c1279472f5f9687b58a6a751`.
A full repeat changed zero of 86 primary artifact paths. Its anomaly receipt is
5,469 bytes, SHA-256
`b400db1b5ee9dd6f799c6fc37a7c7a50c99a77b3c219c476ce1d9cb4da540053`.

**Assessment closure:** Worksheet 13 has 24 exercises: 19 practice and five
graded Exercises 20–24 worth four points each, totaling 20. Every source hint
is blank. Exactly Solutions 1, 10, 11, 16, 18, 19, 21, and 22 exist; all 16
other conventional candidates are absent. Exact solution closure is 33,249
bytes, SHA-256
`8255a56ca2496fa785189d5936e144c5ef3b05e553eca8fbfd4c27683b9800c9`.

**Media and anomaly closure:** the one admitted asset is `Möbius strip.jpg`,
82,042 bytes, SHA-256
`9c4323cfa3ce4f3ce043e4e2479dbf68658d165c46bd41394991361859ea9fad`,
by David Benbennick under CC BY-SA 3.0. The lecture response calls the display
stem `Mobius_strip.jpg` but the adjacent rights macro names `Möbius strip.jpg`;
the exact API response is retained and only the expanded witness uses the
admitted canonical asset name. Solution 21's expansion retained six balanced
raw `<math>` pairs; exact response bytes remain frozen and only those wrappers
were deterministically converted to TeX delimiters in the sanitized witness.
That supplied solution also contradicts itself about parity: the degree is
`(-1)^(n+1)`, hence the antipodal map reverses orientation when `n` is even,
including `S^2`; the target must disclose this mathematical repair.

**Boundary:** Unit 13 authority is admitted. Complete the lecture, worksheet,
eight supplied solutions, media/accessibility surface, and bounded independent
QA; then close the planned Units 11–13 cumulative gate.

## D054 — Unit 13 translation and bounded QA close; consolidated gate opens

**Decision:** accept the complete Indonesian Lecture 13, Worksheet 13, and
exactly eight source-supplied solutions after a bounded independent reader,
mathematics, structure, terminology, and media-rights review. Keep the Unit 13
per-unit closure separate from the cumulative PDF/HTML/backend/publication
claim. Run that larger gate once for Units 11–13.

**Reader evidence:** Lecture 13 is 23,437 bytes, SHA-256
`967551bab13674a72cd13fdde37bb9b1d0037adbc29d5a0059ec6f68258dc4db`;
Worksheet 13 is 9,779 bytes, SHA-256
`d44ad81ba46d80fcd1bc67aafa032943c085f3bc7899ea6266f9c94b846190d3`.
The reader preserves all 24 exercises, the five four-point graded exercises,
20-point total, blank hint layer, and exactly Solutions 1, 10, 11, 16, 18, 19,
21, and 22. All ten final translation and preparation chains pass against the
frozen German witnesses.

**Explicit repair evidence:** twelve records,
`O011-CORR-0135` through `O011-TRANS-0140` and `O011-CORR-0150`
through `O011-TRANS-0155`, disclose the media loader, protected payloads,
continuously differentiable terminology, antipodal parity, finite-subcover
equality, chart index, bounded-image inclusion, and final glossary
normalization. The independent first pass caught three stale renderings of
“finite subcover” in Solutions 10, 16, and 22. They were normalized to the
admitted `subtutupan hingga`, all three verifiers/preparers were rerun, and a
separate read-only pass confirmed current targets, receipts, and prepared
fragments. The adverse ledger now has 155 records, 46,178 bytes, SHA-256
`fe88f5b56bc492217b5a705c4c20b50826ac5617c00a02ab5d086f56d2ed1d48`.

**Rights and closure:** the exact David Benbennick Möbius image remains 82,042
bytes, SHA-256
`9c4323cfa3ce4f3ce043e4e2479dbf68658d165c46bd41394991361859ea9fad`,
under CC BY-SA 3.0. The independent review is 3,378 bytes, SHA-256
`7dc338b7b02556b2ac03019ded817d41b81fcc7434edadd74de8b7f0a3197be3`.
The final binding receipt `qa/unit-13/POST_CORRECTION_MATH_QA.json` is
17,280 bytes, SHA-256
`8adccbf52886be0fe7ecad158c18de0526ff9d1aebbdb37d79f7fee266be0504`.

**Boundary:** Units 11–13 are now translated and individually bounded-QA
complete. The active action is the single consolidated centered A4 PDF,
reflowable semantic HTML, stable-ID backend, visual/accessibility/
reproducibility gate, existing-concept Zenodo release, and anonymous byte
readback. After that milestone, resume source-order production at Unit 14.

## D055 — Consolidated Unit 13 reader/backend gate and existing-concept publication pass

**Decision:** accept Units 1–13 as the next cumulative public checkpoint after
closing the PDF, semantic HTML, real-browser, append-only backend, deterministic
package, mixed-rights, privacy, and reproducibility gates. Publish it only as
the next version of the existing Zenodo concept; do not create a competing
record. Resume source order at Unit 14 after one bounded GitHub lineage attempt.

**Reader and runtime evidence:** the centered A4 PDF is 213 pages and 6,396,207
bytes, SHA-256
`a4d7e55604de9bfb6556d78461db8255a6c584d36b8934a0993b2386ad5832a7`.
It contains all 287 exercises and exactly 35 source-supplied solutions. The
semantic HTML entry is 942,593 bytes, SHA-256
`994c6caf59d87638b3b78583cc9765c2dd8feba42a1ba2ab2c2a9e02d068ebc8`;
its manifest is 78,936 bytes, SHA-256
`8e4cd88db27d77eb4f764aa71816ef15bf758387ccb050e99f383eb741db87da`.
Real Chromium checks on desktop and mobile cover all 4,598 MathJax hosts, all
21 embedded images, long-math local scrolling, and the animation
Play/Stop/reduced-motion surface with zero MathJax or console errors. Browser
receipt `qa/unit-13/HTML_BROWSER_QA.json` is 3,451 bytes, SHA-256
`3f9944c9558d231db2ffb061050879481710782e46b3807269e90a6ec36d43c5`.

**Append-only backend evidence:** the complete backend has 2,604 records. The
published 1,888-record Unit 10 prefix is byte-identical; Unit 11–13 contribute
716 records. JSONL SHA-256 is
`15c4fd6b78a277be60d08016f4df4e5a3afe56bb26f5cb24df285256514186e9`;
CSV SHA-256 is
`e891d6f7c3cb9655f375e9309cd54d0840a09033722b794bd3d01fe73606c854`;
manifest SHA-256 is
`e5959dfd7347fbf53ac3210cd8e671c5dc84842fba99c940a68f062c0bb3dbc3`;
verifier receipt SHA-256 is
`cd5ffe0eac66c68be1705890d6f79225c9dfcc811225d13d9cbedbf656c50784`.

**Package and publication evidence:** the reproducible seven-file public
payload is 15,582,783 bytes. The HTML ZIP is 5,331,749 bytes, SHA-256
`22dacc34c9381c44aebeccf0c48e7cf107c991d7ff3c8c74ec4d950e77e77cf7`;
the compact resumable source ZIP is 3,848,742 bytes, SHA-256
`494fdecf09bec68bc45e04c2d9c7ff4a491bab471e14979a0e6039af7e03fbcb`.
Zenodo concept `22059977` now has exact Unit 13 record `22096736`, DOI
`10.5281/zenodo.22096736`, with Unit 10 record `22073928` as its predecessor.
The PDF is the default preview. Zenodo normalized optional file order to `[]`,
so no unsupported inventory-order claim is made. Publisher receipt
`qa/unit-13/ZENODO_PUBLICATION_RECEIPT.json` is 5,022 bytes, SHA-256
`9431051d25ab8617554d5cd2f8c673552dbb1ee940c38fc398536ebd3ec34463`.
The publisher and a separate urllib-based verifier each anonymously downloaded
all seven public files and reproduced every byte, SHA-256, and MD5. Independent
receipt `qa/unit-13/ZENODO_PUBLIC_READBACK_RECEIPT.json` is 2,556 bytes,
SHA-256
`5a535cb7c0a30412832343c4ecc48df29ccc7547348a3f7b259637053a2a9f01`.

**Boundary:** the Unit 13 cumulative checkpoint is public and closed. The
course goal remains active: make the bounded existing-lineage GitHub attempt,
then freeze and translate Unit 14 in source order.

## D056 — Correct the Unit 13 source package without changing reader content

**Decision:** retain record `22096736` as valid evidence for the exact PDF,
HTML, backend, and anonymous public-byte readbacks, but supersede it as the
source-package checkpoint. A post-publication clean-extraction audit proved
that its internally valid source ZIP omitted the public-safe durable controls
and frozen Unit 10 predecessor dependencies required by the incremental Unit
13 PDF and HTML builders. The existing description therefore overstated that
ZIP as resumable.

Create exactly one corrective next version in the same Zenodo concept
`22059977`. Preserve the PDF and HTML bytes exactly; replace the source ZIP,
README/release notes, manifest, and checksums. Include the public-safe goal,
state, cursor, decision, authority, scope, terminology, adverse/correction
ledgers, all transitive Unit 10 predecessor surfaces, and explicit executable
build commands. Exclude credentials, private locators, caches, and private
publication-operation receipts. Before publishing, extract the staged source
ZIP into two independent empty directories and require each to reproduce the
canonical Unit 13 PDF, HTML tree/package, JSONL, CSV, backend manifest, and QA
identities. This is a packaging correction only, not a mathematical or reader
revision. Unit 14 remains next after the corrective public readback and one
bounded GitHub attempt.

**Outcome:** passed. Corrective record `22097422`, DOI
`10.5281/zenodo.22097422`, is public in the same concept. Its PDF and HTML ZIP
are byte-identical to predecessor `22096736`; the replacement source ZIP is
25,923,641 bytes, SHA-256
`970221e6b7d9cb8cd9453dd3262647bcf9043eb639315bf87f15499ebbb56775`,
with 475 entries. Independent receipt
`qa/unit-13/SOURCE_PACKAGE_R1_INTEGRITY.json`, SHA-256
`1b5a4f5353066cf4b19db174185fdeb31923c69690fa2817c07eea1db84e8f13`,
binds two separate empty-root reproductions of the exact PDF, HTML tree/ZIP,
JSONL, CSV, backend manifest, and QA outputs. Publisher and independent
credential-free readbacks each reproduced all seven public files, totaling
37,657,635 bytes. Their receipt SHA-256 values are
`a817f1404898ea4dfce5654e7491d6be176f66fe872ac53c6400b0f6ab65c3ce`
and `81944e806274dffeae4513b64185db9b45f062296b45dd5658ca75d677ac8082`.
The visible Zenodo page independently shows the exact unmangled title, public
access, the Unit 13 r1 version, and the PDF preview. The corrective release
gate is closed; no duplicate concept or record was created.
