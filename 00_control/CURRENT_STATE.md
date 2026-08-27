# Current state — O011 / D50

Updated: 2026-08-27 (Europe/Berlin)

## Current verified boundary — cumulative Unit 19 local gate

Units 1–19 now pass the complete local reader and additive-backend gate. The
current centered A4 PDF is 302 pages and 7,740,452 bytes, SHA-256
`d96c7200271cd790b42bd4c584befd65c3aa669546e2b6935dbe44fc923b746e`.
It contains 394 exercises, exactly 54 source-supplied solutions, and 26 admitted
media assets. Two clean PDF build cycles are byte-identical. Structural QA has
SHA-256 `8d4e8e56f8990bfd6250b61f02501c4b08589e2fc8db4150716867e533a142b9`;
full 302-page visual QA has SHA-256
`b21130b6cabc7cad7b89cb4cba45c243af26d569d71ad504d1913afa251a6abb`.

The final reflowable HTML entry is 1,333,528 bytes, SHA-256
`096393a5218d49dca913904bbf52a9bc0933a389d456db5d907db76872a3444a`;
its manifest SHA-256 is
`78af3571a8ed75da6bdf421342bf601148c972dbb0f450f36fbeeddb97f74aac`.
The final responsive repair removes zero-width inline-math containment on small
screens and follows delayed MathJax layout changes when resolving deep links.
Structural HTML QA has SHA-256
`f41ece1e459b6e9ce4df411855f3ab3fb4fa4a08213ff6d01408394f675ef078`;
browser evidence has SHA-256
`3b5c2de61b61d5307e355d836540bfc08a0918c8d4f9020bc9c92a947bdedeee`.

The append-only backend preserves the exact 3,208-record public Unit 16 prefix
and adds 539 records for Units 17–19, the cumulative reader closure, and the
hash-bound Unit 18 static-media loader repair, for 3,747 records total. JSONL
SHA-256 is
`8045e59c84bc8c70fc3275bc65d023e46848276b184aca5978bd9b015060c193`;
CSV SHA-256 is
`b63d9d673b841869ab2d848e3a21b5b256a765c2b29f3e9982385e0ad3d75e1b`;
manifest SHA-256 is
`1bc181df4c931eb388dbd42cbc535ed88dd1ec37a475c26e820788d12c93c5eb`;
independent verifier receipt SHA-256 is
`feeab0a83c912d2f20f3bfa6c5bceb89f8cc4883a759166992579dc8b0ea60e2`.
All 245 adverse-ledger rows now correspond one-to-one with backend correction
records; `O011-ACC-0228` binds the persistent byte-identical loader alias, its
canonical public-domain raster, build script, alias receipt, and build receipt.

Unit 18's final lecture/worksheet hashes are
`7d7bc9d97d9719790d1cd37f78fae74f9cb318a4f29b8a7c295e24deb6aed298`
and `6710aad75c6a8132d0d255548cf19ea6d184999386a81f786061b0f02546d759`.
Unit 19's final lecture/worksheet hashes are
`ca3e199d2e80c45a8d87f43c2dae79538108ba04749ace112b88fc4d28000147`
and `338753c6889573ae0056d4975f14e6271722751f349a15ed0df9b3d044689df8`.
The previous D068/D069 values are superseded by this finalized reflow and QA
closure; their append-only historical entries remain unchanged.

The seven-file Unit 19 checkpoint is public in the existing Zenodo concept at
record `22134954`, DOI `10.5281/zenodo.22134954`. Its source package passed two
independent clean reconstructions; the anonymous public readback verified all
seven files, 54,614,325 bytes total, with the PDF as first file and default
preview. The publication and independent-readback receipt SHA-256 values are
`a778cb203fa7598dbacc3e396df497f86b1a5518af05b028a551c2f3d413a0ee`
and `7ff16486bbaa6867c5f85ff7761f03244b9bc683d57719f2fa26c8e0f88ca216`.
The next executable action is the matching existing-lineage GitHub commit,
tag, seven-asset release, and anonymous public readback, followed immediately
by the exact Unit 20 authority freeze and source-ordered translation. The full
O011 goal remains unfinished.

## Objective

Produce a complete, independent, natural id-ID reader for smooth manifolds and differential geometry. Preserve exact mathematics, source topology, exercises, solutions where the authority supplies them, media attribution, and per-component rights. Stable identifiers and machine-readable exports are additive; reader quality remains primary.

## Edition-production spine and admission gate

- Holger Brenner, *Differentialgeometrie (Osnabrück 2023)*, German Wikiversity, is admitted as the complete 29-lecture/29-worksheet production spine for this independent Indonesian edition. Units 1–10 have passed their portable-build, translation, mathematical, rights, visual, structural, privacy, backend, and public-preservation gates.
- This edition decision is not a decision to admit Brenner into the separate 40-course curriculum. The selection root must compare corpora independently and must not count completed work or sunk effort as evidence.
- Exact course page: pageid 142521, revision 889544, timestamp 2023-03-07T11:39:09Z, MediaWiki SHA-1 `e274ea4f0ae092736a5df23dfd3bb744184a9f2d`.
- Course structure: 29 lectures and 29 corresponding worksheets.
- Exact semantic freeze: 2,715 current-revision pages recursively exported with templates at 2026-08-21T09:52:04Z; 3,538,709 bytes; SHA-256 `6b96c90a8b1e52fac57c735f28d0babc56a95050ca015075b755179270d75d14`; revision-set digest `4810e9c13e352db58d7ceb5495c1cf86cb991d2193eaf6a344a48799e7ab0f71`.
- Text reuse path: CC BY-SA 4.0 with page-history attribution. Media rights are file-specific and must be carried row-by-row.

## Scope decision and comparison

Brenner is the strongest bounded candidate because it covers embedded geometry, abstract smooth manifolds, smooth maps, tangent/cotangent and vector bundles, orientation, differential forms, volume forms, Riemannian metrics, exterior differentiation, manifolds with boundary, partitions of unity, Stokes, general and linear connections, Levi-Civita connection, geodesics, curvature, and sectional curvature. It does not supply a self-contained de Rham-cohomology sequence or a Lie-group primer. If the build and rights gates pass, those become bounded original bridges rather than grounds for importing another book wholesale.

Petrunin–Zamora is optional visual supplementation only. Its curves-and-surfaces scope cannot replace the general-manifold spine. The lawful Dionne + Joyce + Petrunin–Zamora composite is much larger and more heterogeneous, retains a nonstandard Joyce adaptation-rights surface and component-media work, and still does not close advanced solved practice. It is not a cleaner edition design. No comparator is mixed silently into this edition.

## Root-selected completion architecture

The curriculum root formally selected O011 in the external coordinator artifact `37_O011_SELECTION_AND_EXISTING_TASK_HANDOFF_20260822.md`, 17,535 bytes, SHA-256 `e6dab7bd6246af82991eb510af1c526fe06dbb641584335b933229b168d51c0a`. Its machine-local locator is kept only in `PRIVATE_LOCAL_LOCATORS.md`, which is excluded from every public bundle. This retains the verified Brenner spine and adds three finite terminal components within this same exclusive lane:

- all ten official example-exam forms, separately frozen and occurrence-mapped; the live selection census is 123 actual problem occurrences, 117 rendered solution-link occurrences, and six missing-solution occurrences, but the recursive freeze must recompute and supersede those counts if needed;
- an original CC BY-SA 4.0 Lie-group/Lie-algebra bridge with 12 hinted solved exercises and one four-problem mastery check;
- an original CC BY-SA 4.0 de Rham/differential-topology bridge with the same 12-plus-four assessment structure.

The six recomputed missing-exam solutions plus 32 bridge/mastery items make 38 planned original solution-bearing items. Marcello Seri 1.9.4 is a CC BY-NC-SA 4.0 comparison reference only and contributes no translated or incorporated prose. Completion now requires the 29-unit spine, exact exam closure, both bridges, centered semantic HTML and A4 PDF, the expanded stable-ID backend, final QA, publication in the correct lineage, and anonymous public-byte verification.

## Upstream limitations admitted, not concealed

- The course pages are aggregators over live semantic pages; pinning 59 top pages is insufficient.
- Only one of the expected lecture/worksheet PDFs is present in the official Commons course category.
- `/latex` pages expand to body fragments using a custom macro vocabulary; the published preamble recipe is incomplete, legacy-encoded, and machine-specific.
- Therefore the reproducible baseline is rebuilt from the frozen recursive XML, frozen expanded fragments, exact media, and a small portable wrapper. The official Electron PDF is retained only as a rendering/accessibility witness.

## Production state

- Authority freeze: core semantic and LaTeX/control exports are complete. Unit 7 authority, all 19 exercises, zero source hints, exactly three supplied solutions (Exercises 4, 7, and 13), sixteen solution absences, three static-media assets, and two downloadable GIF surfaces are frozen at page/revision and byte/hash granularity. The cumulative reader now carries fourteen static media plus both exact GIF companion surfaces with component-specific rights.
- Verified reader boundary: cumulative through Lecture 7 plus Worksheet 7 and all seventeen source-supplied solutions across Units 1–7. The reader contains 126 worksheet exercises, seventeen supplied solutions, fourteen static media, and two linked GIF companions. The exact Unit 7 lecture target is 20,487 bytes, SHA-256 `5faec64b0b20a6999e61fc3fa6a32db812e324d1e8a272d1978c67bc76c3c7b0`; the worksheet target is 8,029 bytes, SHA-256 `af223f98696a9353e7967d3ac150a8f2f5de3c49bef506c69fe0d452e7717658`. Translation-only deltas and the TeX-safe attribution repair are explicit in the adverse ledger; no mathematical change is silent.
- Final cumulative PDF through Unit 7: 4,950,232 bytes; SHA-256 `8c2cf76230b45d66a8236c0cd92a048809ff5ec0cce343132dd902684cb05ec6`; 117 centered A4 pages with wrapper-owned 22 mm margins. Two clean build cycles passed. `qa/unit-07/PDF_BOUNDARY_QA.json` (SHA-256 `06b50304e1ac3f7873c054b6607f689db08f6e65fb583beffaaeb91e7bd39ef0`) and independent `qa/unit-07/pdf_structural_qa.json` (SHA-256 `b564eaf9b668c056092963158ff2f70aad1a29e254dfa98a1c0c9d43c5a6b649`) cover page boxes, extractability, fonts/ToUnicode, links, exercises/solutions, media surfaces, centering samples, and the disclosed untagged-PDF limitation.
- Cumulative backend: 1,363 schema-valid records. The 1,173-record Units 1–6 JSONL/CSV prefix remains byte-identical and Unit 7 adds 190 records. JSONL SHA-256 `d9d51a46b84368f50a211a31263bafe8f1588f8e62a5fa4b496b2ff45903b912`; CSV SHA-256 `c301009770e1c523d046585c0c83947cab6f856b32b83890d361a919fed5a958`; manifest SHA-256 `1a950183a66bbc837cff27f34cf2f1fc838ad181bc4fbf16e8bd758c1df2068d`.
- Publication/push: the cumulative Unit 13 checkpoint is now public as corrective version `2026.08.25-unit13-r1` in existing Zenodo concept `22059977`, record `22097422`, DOI `10.5281/zenodo.22097422`; record `22096736` is its exact predecessor. The 213-page PDF and 29-file HTML archive are byte-identical to that predecessor. The replacement source ZIP is 25,923,641 bytes, SHA-256 `970221e6b7d9cb8cd9453dd3262647bcf9043eb639315bf87f15499ebbb56775`, with 475 entries and every public-safe durable control, cumulative correction manifest, current Unit 13 build input, and consumed frozen Unit 10 predecessor dependency. Two independent empty-root extractions reproduced the PDF, HTML tree/ZIP, JSONL, CSV, backend manifest, and QA receipts byte-for-byte; integrity receipt SHA-256 is `1b5a4f5353066cf4b19db174185fdeb31923c69690fa2817c07eea1db84e8f13`. The publisher and a separate credential-free verifier each downloaded all seven public files and matched all 37,657,635 bytes by SHA-256 and MD5. Publisher receipt SHA-256 is `a817f1404898ea4dfce5654e7491d6be176f66fe872ac53c6400b0f6ab65c3ce`; independent public-readback receipt SHA-256 is `81944e806274dffeae4513b64185db9b45f062296b45dd5658ca75d677ac8082`. The human-facing Zenodo page shows the exact title and PDF preview. The frozen canonical upstream `Tangent bundle.svg` remains byte-identical; its public source bytes contain a pre-existing authoring-machine `/home/.../diverse/wiki` path. This is neither a task-local locator nor a credential, and rewriting it would break the frozen upstream identity, so it remains disclosed rather than silently changed.
- GitHub account access has recovered. The bounded atomic push succeeded: `main` now contains corrective commit `56f2b2b4d11592ecb311f7e317b92ae591f752ab`, annotated tag `v0.13.1-unit-13`, and public release `https://github.com/KokunoYumeto/brenner-differentialgeometrie-id/releases/tag/v0.13.1-unit-13`. A separate unauthenticated verifier resolved the tag to that exact commit, confirmed the release is latest/public/non-prerelease, downloaded all seven assets, and matched all 37,657,635 bytes by SHA-256 and MD5. Receipt `qa/unit-13/GITHUB_PUBLIC_READBACK_RECEIPT_R1.json` is 4,519 bytes, SHA-256 `0c1f7061114402df477ddcb7817b5746d8f22c82ef13f38a48eea373d28d0ad8`. Figshare remains at the previously recorded blocked Unit 6 state; do not repeat visibility/account checks until external state changes. No duplicate preservation record is authorized.
- Terminology gate: passed. A bounded official-arXiv search found no Indonesian smooth-manifold/differential-geometry source with public TeX, so the admitted fallback was the official nine-page institutional PDF by Alfakhriati, Jenizon, and Haripamyu, DOI `10.25077/jmu.7.2.140-148.2018`. `qa/unit-07/TERMINOLOGY_QA_DECISION_20260823.md`, 2,847 bytes, SHA-256 `c2bbc255c2c95371f0c052b9d7a2d1dd2503ce7638c9e8fc4538faac78ee8c0b`, records the page-level comparison. It directly confirms `ruang singgung` and `vektor singgung`; no Unit 1–7 reader rewrite is justified. Retrieval aliases and source-order terms through Unit 8 now form a 167-record terminology ledger, 14,288 bytes, SHA-256 `b6c50daa03ea47121586510b44cb7d2618c644ef3fd89d11332ce7ca9463a5ae`.
- Unit 8 reader boundary: complete and bounded-QA verified. Lecture 8 is 18,099 bytes, SHA-256 `90574f5e2879e7bc07ee20e5a335d78bd1b84f5f94b52f257dcdd0f3abf6f8bf`; Worksheet 8 is 13,094 bytes, SHA-256 `8cd886c6c2f9a7019f5e2319d9930a729572e016ee823346200228e3265b40bf`; supplied Solutions 11 and 13 have SHA-256 `1a55e39744d436cf93afd514a638197019f2e9e139279abbb3576a1704757a2b` and `73ee95e00976b81b69b5bee684d2f941c39ca413e4dd0f2696f29081456215ed`. All four structural/protected-math translation receipts pass. Seven explicit deltas, `O011-CORR-0073` through `O011-TRANS-0079`, disclose four lecture repairs, two worksheet/solution repairs, and one protected case-label translation; none is silent. `qa/unit-08/POST_CORRECTION_MATH_QA.json`, 5,279 bytes, SHA-256 `d09f92ff5de7cbacb37c5bd3a0ec61516877d473c3362cd0cdeeb18410af8974`, binds the complete 21-exercise/two-solution/no-media closure. No cumulative build or publication is claimed at this deliberately per-unit boundary.
- Unit 9 reader boundary: complete and bounded-QA verified. Lecture 9 is 26,132 bytes, SHA-256 `9e3b12f4168c4f7a8c246c4c9106d1154be237e9080e12e0a21bcd8942d61bba`; Worksheet 9 is 10,331 bytes, SHA-256 `4079437947ab31c9216e3ee6059badc8cf7d780ead1df93cd5cfb6f1cd7d3e9d`. Both structural/protected-math receipts pass. `O011-CORR-0080` through `O011-TRANS-0087` disclose the local-chart relation, point notation, scalar-reparameterization domain, higher-jet structure, submersive dimension hypothesis, affine-curve domains, broken display label, and protected formula text. `qa/unit-09/POST_CORRECTION_MATH_QA.json`, 4,390 bytes, SHA-256 `57e90ee6c04fcecd5fbc31b23e25d8d3f30f7efaf322101a30ab8f9c867a27be`, binds all 17 exercises, zero source-supplied solutions, and the exact public-domain SVG. No cumulative build or publication is claimed at this per-unit boundary.
- Unit 10 reader boundary: complete, bounded-QA verified, cumulatively built, and publicly preserved. Lecture 10 is 23,152 bytes, SHA-256 `bafd2d5f8d1307438c42f2b20a1914f143f097ddc7f37c2e1e9b99dccb340044`; Worksheet 10 is 16,155 bytes, SHA-256 `3a386ddb1a7e29475d54ca052c518b9b7c7447cefb2c6158f1a288c9b816ac4a`. Supplied Solutions 9, 10, 15, and 25 have SHA-256 `f4d86590a7244ce6006f2d7812700e4038391fe9808bf733b3c731e1d1cfe088`, `4af0e5d19acc8555b0deb5fd7503008b86bb740f76ef8ce1482ff95d09cc7b22`, `df54358b3ac368df7d552f21a38f09fbceb0c90055066e25944a11359c5ab2d1`, and `18c69f5473ffea083ed655dd8542e2e466a0fee07175e355f3125447b26d21d5`. All six translation receipts pass. `qa/unit-10/POST_CORRECTION_MATH_QA.json`, 8,872 bytes, SHA-256 `c81d9c1459af5b32ca7b3e1af89c573c4f5881eec81dab2340d9a4ae39c497a6`, binds the 31-exercise/four-solution/two-media closure and sixteen explicit Unit 10 deltas `O011-CORR-0088` through `O011-TRANS-0103`. The consolidated gate is closed; the active source-order cursor is Unit 11.
- Consolidated Units 1–10 gate: passed locally and publicly. The deterministic PDF is 165 centered A4 pages, 5,733,895 bytes, SHA-256 `4eaec807347feeab2b3334056d3109d5ce6e5eb30ed3649a507ae6124049856d`; two clean cycles are byte-identical. It contains 195 exercises, all 23 source-supplied solutions, and 17 static media, with exact per-file rights. Structural receipt `qa/unit-10/pdf_structural_qa.json` is 89,821 bytes, SHA-256 `81451a5e7f78f63935e758fa3d277db28b9db252c09c6930fc1cea597c9a47d7`; visual receipt `qa/unit-10/PDF_VISUAL_QA.json` is 4,250 bytes, SHA-256 `8781c681152580035dca4552f5a3aa0d54c6003caf0a527ccbf4ca3ca4e6fc4b`. Every page rendered; the malformed legacy tangent-bundle SVG viewport is corrected only in its deterministic print derivative, leaving canonical SVG bytes unchanged and keeping image plus caption together. The reflowable HTML entry is 710,428 bytes, SHA-256 `125688aadaade39ded86fb42adc8bfa74005a7fca66623a4c419c79ab36d52d4`; its manifest is 32,562 bytes, SHA-256 `c9d6b7ce87feeb7c1621d0ac25e8b4ef3639a2e95140ef4ffe6f330a40b62e8e`, and deterministic structural QA SHA-256 is `b5af7e5e5192b2c19aaeb940907cce58c8340f294d694f130965545d2c1defb9`. The additive backend remains exactly 1,888 schema-valid records with immutable 1,363-record Units 1–7 prefix and an all-or-nothing six-surface PDF/HTML closure: JSONL SHA-256 `ef614f1d6f74357b65644e06d5667870339f9ee6712bdde028e8b3923e16d132`, CSV SHA-256 `409c3d79d99ac17cbf4bf597763221681db00d4fd4c3f7a8cc84c6cd98c9a753`, manifest SHA-256 `2c4799664311ecfd5f5ca9bb119d08e356ee2fe1f021f0dbd56b833d5dcf0893`, and QA SHA-256 `7220cfc60e9c896f67a49fd378c308265995d451c3b8adb95176e2821c9a56ea`. Exact Zenodo publication and two anonymous public-byte verification passes close the milestone without another release ceremony.
- Units 9 and 10 are also fully authority-frozen and offline-verified, so the batch has no remaining source-admission dependency. Unit 9 has 17 exercises (13 practice, four graded, 23 points), no supplied solutions, blank hints, and one exact public-domain SVG; its preflight SHA-256 is `6425743defefc74dbe17d0870f6f6cfafe58c224474a001ace1c411950f1ba0a`. Unit 10 has 31 exercises (26 practice, five graded, 31 points), supplied solutions 9, 10, 15, and 25, blank hints, and two admitted media assets; its preflight SHA-256 is `123828b49bc6f78bf2ea349f62f95b5a11911f9ac2743ca6b1cf09316f4b6ac4`. The Unit 9 and 10 offline verification receipts have SHA-256 `ca1c133548a85ac087df3accf58f0e18ccdc9d7ecc3d09495940029d59e21e1a` and `cd1f406ac4786030fb5ca508874e6d79428de9cc0f381d3c074fbf6f788caeac` respectively.
- Unit 11 reader boundary: complete and bounded-QA verified. Lecture 11 is 16,590 bytes, SHA-256 `c6d5266be60eec3911d841213fb4333b51c6555266915e0b64438c3c2bf3d4fc`; Worksheet 11 is 20,513 bytes, SHA-256 `b92ce3a51ad8b56acbd01f26673fb3512faee6b7bf17b8ccb6365c2091af6941`. Supplied Solutions 10 and 14 have SHA-256 `77e8efefffb8acded4a11f1e258134d8d26aef4e8cb517a67dd8a3d1565bf2e9` and `d8cd8d24a7dba0865dda2bd83e10f1c96c0dc100c9e95de6fcaf723f8a714683`. All 39 exercises, six graded point values totaling 22, blank hints, exact solution presence, the CC BY 2.5 static image, and the CC BY-SA 4.0 downloadable animation are preserved. Ten explicit corrections `O011-CORR-0104` through `O011-CORR-0113` are disclosed. Independent language/math review passed after two prose refinements. `qa/unit-11/POST_CORRECTION_MATH_QA.json` is 8,548 bytes, SHA-256 `e21ae4636c83f5dae3090a4f8cee5c6187e65546000f7b2b0fe67744e1e83d20`. No cumulative build or publication is claimed at this per-unit boundary.
- Unit 12 reader boundary: complete and bounded-QA verified. Lecture 12 is 21,299 bytes, SHA-256 `993875dc8f085e0bddaaac813179dade7e5a2928d53c1e575c7c4f09bc6074f1`; Worksheet 12 is 19,723 bytes, SHA-256 `b773f00690f9d5128cf602ec8f96d816e58009113f9051f198966e98c1a76975`. Supplied Solutions 11 and 12 have SHA-256 `fcee4e2a7cbf9c36b053c0831c5ac51aa99553870ddf7e9b10c7b04ac301a210` and `3efe62a19d10bbf4f36301f6753f0f29f7480030dd2a1fe7a0ae914b1957d23f`. All four final translation receipts pass. All 29 exercises remain in order: 25 practice and four graded items totaling 15 points; every source hint remains blank and no solution layer beyond exact supplied Solutions 11 and 12 is implied. The exact 24-frame CC BY-SA 4.0 Möbius-strip GIF and public-domain inclusion-exclusion SVG retain their canonical bytes and file-specific rights; deterministic PNG derivatives serve the static PDF. Twenty-two explicit corrections/accessibility records `O011-CORR-0114` through `O011-TRANS-0134` plus `O011-TRANS-0156` are disclosed, including the final normalization of three stale `real` spellings to admitted `riil` and the lossless three-line reflow of two long bundle displays. Independent reader/math review passes. A bounded HTML regression also proves a static-first animation surface, keyboard Play/Stop, canonical GIF playback/download, and reduced-motion enforcement; its receipt SHA-256 is `0b84a482e4b5af062a87535eb80b23ca47dc13afd82d04546f4c84ac8907a32e`. `qa/unit-12/POST_CORRECTION_MATH_QA.json` is 11,525 bytes, SHA-256 `070d1da40e9bee5e1825259eee20600f7c26d5db3c01fe11c1680ffd2d3a85e7`.
- Unit 13 reader boundary: complete, bounded-QA verified, cumulatively built, and publicly preserved. Lecture 13 is 23,437 bytes, SHA-256 `967551bab13674a72cd13fdde37bb9b1d0037adbc29d5a0059ec6f68258dc4db`; Worksheet 13 is 9,779 bytes, SHA-256 `d44ad81ba46d80fcd1bc67aafa032943c085f3bc7899ea6266f9c94b846190d3`. All 24 exercises remain in source order: 19 practice and five graded items totaling 20 points; every hint is blank and exactly Solutions 1, 10, 11, 16, 18, 19, 21, and 22 are present. The exact 82,042-byte `Möbius strip.jpg`, SHA-256 `9c4323cfa3ce4f3ce043e4e2479dbf68658d165c46bd41394991361859ea9fad`, retains David Benbennick attribution and CC BY-SA 3.0. Twelve explicit Unit 13 deltas `O011-CORR-0135` through `O011-TRANS-0140` and `O011-CORR-0150` through `O011-TRANS-0155` disclose every mathematical, protected-text, media-loader, and terminology repair. Independent review first caught and then verified repair of three stale finite-subcover phrases; all ten live translation/preparation chains pass and agree with `subtutupan hingga`. `qa/unit-13/POST_CORRECTION_MATH_QA.json` is 17,280 bytes, SHA-256 `8adccbf52886be0fe7ecad158c18de0526ff9d1aebbdb37d79f7fee266be0504`.
- Consolidated Units 1–13 reader/backend/source-continuation gate: passed locally and publicly in both existing GitHub and Zenodo lineages. The deterministic PDF is 213 centered A4 pages, 6,396,207 bytes, SHA-256 `a4d7e55604de9bfb6556d78461db8255a6c584d36b8934a0993b2386ad5832a7`; it contains all 287 exercises and exactly 35 source-supplied solutions. The reflowable HTML entry is 942,593 bytes, SHA-256 `994c6caf59d87638b3b78583cc9765c2dd8feba42a1ba2ab2c2a9e02d068ebc8`; its 4,598 MathJax hosts pass real Chromium desktop/mobile testing with zero runtime or console errors, no page overflow, accessible media controls, and local scrolling for long mathematics. The additive backend has 2,604 schema-valid records; its 1,888-record public Unit 10 prefix is byte-identical and Unit 11–13 add 716 records. JSONL SHA-256 is `15c4fd6b78a277be60d08016f4df4e5a3afe56bb26f5cb24df285256514186e9`; CSV SHA-256 is `e891d6f7c3cb9655f375e9309cd54d0840a09033722b794bd3d01fe73606c854`; manifest SHA-256 is `e5959dfd7347fbf53ac3210cd8e671c5dc84842fba99c940a68f062c0bb3dbc3`; verifier receipt SHA-256 is `cd5ffe0eac66c68be1705890d6f79225c9dfcc811225d13d9cbedbf656c50784`. Unit 14 authority closure is now active.
- Unit 14 reader boundary: complete and bounded-QA verified. The authority freeze binds Lecture pageid/revid `142558/897331` and Worksheet `142648/1020024`; the exact expanded witnesses have SHA-256 `6c14208bd02871b44e60849c627c1e66928cdcabdb0306ad6fbe5407c311abbc` and `f6553d7398e700e915dc054527c5f079730bc79d2ebda63f094efb3c9c1d6942`. Lecture 14 is 27,295 bytes, SHA-256 `e1ab5149036b72be563774336fea35560e12039946952c5a19b52c612de0073c`; Worksheet 14 is 10,760 bytes, SHA-256 `98880cc5c0996175a6f3f60ac6c5098bb4076569f1050cc8136f13662e6cec79`. All 18 exercises remain in order: 14 practice and four graded items totaling 20 points; every hint is blank and exactly source-supplied Solutions 5, 6, 9, 11, 12, 13, and 14 are present. There is no media. Twelve explicit records `O011-CORR-0157` through `O011-TRANS-0168` disclose all mathematical and reader-language changes. Independent mathematical and language review passes with zero reader-facing residual German, and all nine translation plus preparation chains pass. `qa/unit-14/POST_CORRECTION_MATH_QA.json` is 8,498 bytes, SHA-256 `2b9c5474759e0bc298cb668e9b893ac477edb3e6a9db90ea1b00c19db81ed86e`. This is deliberately a per-unit boundary: no cumulative PDF, HTML, backend, package, publication, or public-readback claim is made. Unit 15 authority closure is next; Units 14–16 form the next planned cumulative batch.
- Unit 15 reader boundary: complete and bounded-QA verified. Lecture 15 is 34,034 bytes, SHA-256 `7d13af0d91107fda5d622ff80ef838338d1720ae397a74a8a6137112d30cc7ba`; Worksheet 15 is 8,381 bytes, SHA-256 `3c6e0d42eb20663d6c6eb6a33d2641b1afabc38b6e246a0ac9273bbeb5f6858c`. All 16 exercises remain in order: 13 practice and three graded items worth 4, 4, and 5 points; every hint is blank and exactly Solutions 1, 11, 12, and 13 are supplied. The four solution target hashes are `bff5036f08a6dfc8dded4043ab42ce201e313a9f2757f15275919888f663a42a`, `6902a8cd4421acd9d83ed501af4fbe7bc8e91fe1c6ab2ed6668827c8ed4ab749`, `fa070c1c433e17d201ae84e1ccfb7ea21c24f4255f28857016e323f0eb4fba49`, and `b29338f5cabe345e317c6848e8321ffea0e91d76910afa5ab86feccf5a5349d8`. There is no media. Twelve explicit records `O011-CORR-0169` through `O011-CORR-0180` disclose every source repair and reader-language refinement. Six translation and six preparation chains pass; independent language and mathematical review passes with zero reader-facing German. `qa/unit-15/POST_CORRECTION_MATH_QA.json` is 8,256 bytes, SHA-256 `90e0cee5ec3228ea3635e50ad6feaacd1f86092e93dea3c70b07ca020cff6a87`. This remains a per-unit boundary pending the cumulative Units 14–16 gate.
- Unit 16 reader boundary: complete and bounded-QA verified. Lecture pageid/revid is `142560/1052551` and Worksheet is `142650/1020028`. Lecture 16 is 24,994 bytes, SHA-256 `e40adb356c641b552e931bc7660094bacb5dbd10d351c2036e0a253021434614`; Worksheet 16 is 11,081 bytes, SHA-256 `1a7535fe6e1ee9bb40e0a508143aa57c5dfc19ef92415635e54ed9f5975290b2`. All 21 exercises remain in source order: 16 practice and five graded items worth 4, 3, 4, 6, and 6 points; all hints are blank and exactly Solutions 1 and 12 are supplied. Their target SHA-256 values are `df5f155101df65eb27bc1aeea5933526488471eea6b444cf7e8f5f04aa9c8779` and `84f08c2ac9fef0276b844e4c1ff06963f99a8115db4ff9422b5f833da4848cbf`. The exact public-domain Riemann portrait and three-handled-sphere image retain byte/hash and file-rights closure. Nine explicit records `O011-CORR-0181` through `O011-TRANS-0189` disclose three mathematical hypothesis/dimension repairs, authoritative creator spelling, one source typo, and reader-language refinements. Four translation and four preparation chains pass; independent language and mathematical review passes with zero reader-facing German. `qa/unit-16/POST_CORRECTION_MATH_QA.json` is 10,639 bytes, SHA-256 `13edee0684042a53beb4daa7b6dfe5c877ac7ed5c35ec03fa5fa63f11a710a4c`. Units 14–16 and their cumulative PDF/HTML/backend/package/publication gate are now closed in both existing public lineages.
- Unit 17 reader boundary: complete and bounded-QA verified. Lecture 17 is 24,372 bytes, SHA-256 `ef22cfb765131f1b8c0b52bd78545c66e36eedec777f84bb5e6cc04ecf04ad3e`; Worksheet 17 is 6,649 bytes, SHA-256 `0b1366792404b62fb2705f56995077f4d53bb9779e10c06f8a2c0b96a5241fdc`. All 19 exercises remain in source order: 13 practice and six graded items worth 5, 5, 4, 4, 6, and 6 points; every hint remains blank and exactly Solutions 2 and 4 are present, with target SHA-256 values `5fdd8ec67263580cd64065b4bd574581b8c55788b2351f278098781cb091b5ef` and `8de955a9a8910399b656e291a11ec70096d59444ba292b6a00fc8a7bfbfc6c3e`. The public-domain `Cilinderprojectie-constructie.jpg` remains byte-identical and credited to KoenB. Sixteen explicit records `O011-CORR-0194` through `O011-TRANS-0209` disclose orientation/sign hypotheses, malformed source notation, parameter-domain order, the Mercator relation, two worksheet idealizations, one source typo, and reader-language refinements. All four translation and four preparation chains pass. `qa/unit-17/POST_CORRECTION_MATH_QA.json` is 10,839 bytes, SHA-256 `90b5e890a3869d5187ec1e6bb6d66dba0842dbdab5e51414d1a05fe4fcb3eb0a`; its independent 28-path binding verifier is 5,656 bytes, SHA-256 `e37b86dadd0b0cfb9f3bf6188e788173dab45d6c45dc395d072fe7f0765f27a5`. Content commit `64d157d1622327ce7d7e0471284bad89573c2ef3` is public on `main`; anonymous raw readback matched both targets, both solutions, and the QA receipt. The 2,251-byte readback receipt has SHA-256 `f3890184be6dbe546cdc3c9ce0e7e18e3a423691ac60e20034233be29266323d`. This is a source checkpoint rather than a standalone release; the active source-order cursor is Unit 18 and the next cumulative reader/backend/publication milestone remains Unit 19.
- Upstream contact: prohibited during production and not used.

Known accessibility limitation: the cumulative PDF is not structurally tagged. It does carry `/Lang=id-ID`, all 33 embedded font objects have ToUnicode, and all 213 pages yield extractable text through both pypdf and pdfplumber. Semantic HTML is the primary structured accessibility surface.

## Completion gate for each unit

1. Exact source revisions and content hashes recorded.
2. Natural id-ID reader prose; formulas, identifiers, order, exercises, and supplied solutions preserved.
3. Media present with exact source, creator, license, and hash.
4. Portable build completes from a clean bounded directory.
5. Structural and mathematical comparison passes; no unexplained source correction.
6. PDF/HTML visual and link/accessibility checks pass where those surfaces exist; disclose surface-specific limitations rather than overstating them.
7. Backend IDs resolve to the same source segments and are not required to read the edition.

## Resume order

Read `GOAL_AND_WORKFLOW.md`, `AUTHORITY_FREEZE.md`, `DECISION_LOG.md`, `CURSOR.json`, `TERMINOLOGY.csv`, and `ADVERSE_LEDGER.csv`. Units 1–16 are complete through centered PDF, reflowable HTML, append-only backend, a clean-extraction-resumable source package, GitHub and existing-concept Zenodo publication, and anonymous public-byte readbacks. Do not repeat that release ceremony. Unit 17 is translated and bounded-QA complete but deliberately not released alone. The active executable action is the exact Unit 18 authority freeze and solution/media census followed by complete source-ordered translation. Continue through Unit 19 before running the next consolidated centered PDF, semantic HTML, immutable-prefix backend, reproducibility, existing-lineage publication, and anonymous public-readback gate.

## Verified cumulative Unit 16 boundary — 2026-08-26

The cumulative local reader and stable-ID backend gates through Unit 16 now pass. The final centered A4 PDF is `output/pdf/geometri-diferensial-manifold-mulus-hingga-unit-16-id.pdf`, 261 pages and 7,241,359 bytes, SHA-256 `58f98853ab8eeb1beb2aa4ade6bd3c746b62b4fa42c3c692a03c17076cdb06b8`; two clean build cycles are byte-identical. It contains 342 exercises, exactly 48 source-supplied solutions, and 23 configured media. Every page renders and was visually inspected; the final visual receipt is `qa/unit-16/PDF_VISUAL_QA.json`, SHA-256 `747b0eba681b317f1455b869e1cc5592fb147ffc5f32420eca338145eb6c8958`. The PDF remains deliberately disclosed as untagged; all fonts have ToUnicode, every page is extractable, `/Lang` is `id-ID`, and the semantic HTML is the primary structured accessibility surface.

The final reflowable HTML entry is `output/html/unit-16/index.html`, 1,163,644 bytes, SHA-256 `5612cf4218619425e5524fd72c46757fb30db63c185407e99c4d84d99fe3a2f9`; its manifest is 90,230 bytes, SHA-256 `e7c3c2c952b0880c938d07632faf313dd91b20c281295dbe7e3fb13b9af1d871`. Structural and real-Chromium desktop/mobile tests pass with 5,648 MathJax hosts, zero MathJax errors, zero console errors, zero broken internal links, working deep links and animation controls, local scrolling for wide mathematics, and no page-level horizontal overflow. The browser receipt is `qa/unit-16/HTML_BROWSER_QA.json`, SHA-256 `fe2a6cec0a93c7f9065bb60839a1f93a4c216f8933e4ccc79dad74b2df072a50`.

The additive backend now contains 3,208 schema-valid records. The published 2,604-record Unit 13 JSONL and CSV prefixes remain byte-identical; Units 14–16 append 604 records. `backend/records.jsonl` has SHA-256 `c42bac17822f949aa16ac0f87c7d0726526d020d46bab97f91d36e70f4b21983`, `backend/records.csv` has SHA-256 `2ff324a750b01540fd3827684947877e807ac8402d09fc6ece1efdf14caeb312`, and `backend/MANIFEST.json` has SHA-256 `5718751f625774d4b4ca6d019524646c56219731b513b3329f9ba022304845db`. The verifier receipt `qa/unit-16/backend.json` has SHA-256 `5e7e40f07033725db979fdb30b2a86e89c301555b10bb20f8a66447af8bfb22a`.

The Unit 16 checkpoint operations are closed: the reader-first seven-file release passed two clean-extraction rebuilds and is public and anonymously byte-verified in the existing GitHub and Zenodo lineages. Unit 17 has since passed its exact authority and bounded translation gate. The full O011 goal remains unfinished; Unit 18 authority closure is the next executable production action.

### Unit 16 reproducibility and Zenodo preservation closure

The reader-first seven-file release is now 51,241,328 bytes. Its compact source ZIP is 37,989,234 bytes, SHA-256 `080cc0c3902c3bda3a895646575ca2770cf20870ce16a740d6e3783cbc90a71c`. Two independent empty-root extractions rebuilt the exact 261-page PDF, HTML tree/archive, 3,208-record JSONL/CSV backend, manifests, and deterministic QA receipts byte-for-byte; the passing integrity receipt is `qa/unit-16/SOURCE_PACKAGE_INTEGRITY.json`, 35,272 bytes, SHA-256 `035277c316604ed69e6aac8d6632b6c8b927a02a2701f35e9ce7b35f4e475fa5`. Both temporary roots were removed. The closure includes all 25 backend-bound canonical assets, all file-specific rights records, the complete prepared-TeX build input tree, and the exporter/verifier generation bindings; it excludes diagnostic renders, caches, credentials, private controls, and bulk raw dumps.

Zenodo version `2026.08.26-unit16` is public in the existing concept as record `22104426`, DOI `10.5281/zenodo.22104426`. The publisher and an independent credential-free verifier each retrieved all seven files and matched all 51,241,328 bytes by SHA-256 and MD5. The PDF is the first effective file and the configured default preview. The sanitized publication receipt is 5,834 bytes, SHA-256 `0f35287a422263d48786ed45dee0e581c191cf1a0c6dce4f701535579a2a0c63`; the independent readback receipt is 4,023 bytes, SHA-256 `1c846dd93cf66c60822577b39e5b3ecf5a42a3c1f950ae56d30da0a493ddd063`. No duplicate concept or stray draft was created. The matching GitHub closure described below also passes; no Unit 16 publication work remains.

The matching GitHub checkpoint is now public. `main` contains content commit `a492e9d7c23991edd8cec7978533e80b44f86e6f`; annotated tag `v0.16.0-unit-16` and release `https://github.com/KokunoYumeto/brenner-differentialgeometrie-id/releases/tag/v0.16.0-unit-16` resolve to that commit. An unauthenticated verifier confirmed the public README contains the exact Zenodo version DOI, the release is latest/public/non-prerelease, and all seven assets match the same 51,241,328 local/Zenodo bytes by SHA-256 and MD5. Receipt `qa/unit-16/GITHUB_PUBLIC_READBACK_RECEIPT.json` is 4,555 bytes, SHA-256 `b2c8e160c13115a50cdd2f57484e7ce6172387b9cc713cd70d10bef640b3bea6`. Unit 16 is therefore closed in both existing public lineages. Unit 17 is now also translated and bounded-QA complete; the full corpus remains unfinished at the active Unit 18 authority cursor.

## Unit 17 authority boundary

Unit 17 authority freeze and preflight pass, including a second frozen-response reproduction and a live current-revision check. Lecture root pageid/revid is `142561/944389`; its sanitized expanded LaTeX is 24,138 bytes, SHA-256 `0ac2f20594df388ad6e6ddb3a38515af63ec74b6298eb7acc1d5c20851f2d1e0`. Worksheet root pageid/revid is `142651/886713`; its sanitized expanded LaTeX is 6,577 bytes, SHA-256 `fec773f1573930cba133de084287bd5cd91ea2302e99c2d5c0d96e65fe5cbd96`. The worksheet contains exactly 19 exercises: thirteen practice and six graded items totaling 30 points; all hint fields are blank and only Solutions 2 and 4 are source-supplied. One displayed public-domain media asset, `Cilinderprojectie-constructie.jpg` by KoenB, is frozen at 172,697 bytes with SHA-256 `7a3898760a53e679871e89e1a4382a4b5d8954c31f71d572bca6a3b3a160ef29`. The localized credit-text variance does not affect any rights-critical field. Preflight receipt SHA-256 is `0c7d19d122793874a8196386ba556cd4f80720602b08cf88e818dc1b8c59887a`; current-revision receipt SHA-256 is `788d919c67bb538639a0f65e8b78b3c47101c663a7c56dc9cf6767d643c97990`. The complete Unit 17 translation and bounded QA now pass as recorded above. The active action is exact Unit 18 authority closure and source-ordered translation.

## Units 18 and 19 bounded reader closure

Unit 18 now passes exact authority, translation, mathematical, media-rights,
accessibility, and content-addressed binding gates. Lecture root pageid/revid is
`142562/898474`; its 23,948-byte sanitized authority has SHA-256
`7fc98f4cdd977e4a5acb4dea5d61807251ac850fe102b8f0ecc1251f755d3c3e`.
Worksheet root pageid/revid is `142652/908317`; its 9,557-byte sanitized
authority has SHA-256
`ee2744cd813459a644fb382e931ae1f9a0f3b9dd8889532dfd9d49acd30de738`.
The final lecture target is 24,212 bytes with SHA-256
`61a0e9240fb83c0e553c37866e76efc5b38b7a27ade1789a8d32f014549d8193`;
the worksheet target is 9,504 bytes with SHA-256
`6710aad75c6a8132d0d255548cf19ea6d184999386a81f786061b0f02546d759`.
All 21 exercises remain in source order: 16 practice and five graded items
totaling 19 points; hints remain blank. Exactly Solutions 8, 11, 13, and 14
are present under the canonical cumulative filenames with SHA-256 values
`b33f25142ea1d417660de331a39252483fe081d456f3f32db19e4772a2cedf0f`,
`e602b8a63785e6bd356394d7e09d75a77203a3863efe5e6845f035e638dc409d`,
`2c618c487cbb8cccf300b3333c645f79519f39640dac00c664c25963e2935ec3`,
and `f1ee3d9a587a96a1315a31b45ee5483b494951018bd2082674bd0fed9468b307`.
The canonical 956,681-byte Poincare GIF remains CC BY-SA 3.0 and the
194,637-byte hyperboloid PNG remains public domain. The GIF has a faithful
Indonesian caption and a deterministic frame-zero static fallback; its
animation receipt is 5,919 bytes with SHA-256
`fd22692b6eeed7a4fe139a862b725fb932db780ab62a40de4a86d53583d16898`.
Seventeen disclosed Unit 18 records include `O011-ACC-0226`; no correction is
silent. The final POST QA is 13,965 bytes with SHA-256
`1ddc7b46878adaa9f8fe1419793a7f4453de768cb1607bf068de2ad712f5f6d1`;
its 7,339-byte independent binding receipt has SHA-256
`f1169ce3f04e9c69179e68423085f29999657ce9492c05bc2e1cb01a76299068`.

Unit 19 also passes its complete bounded gate. Lecture root pageid/revid is
`142563/905408`; the 29,051-byte sanitized authority has SHA-256
`bd47777c4d0fc68698db177e8937ab15824931ee86707148eb4ecb4bc9c548f2`.
Worksheet root pageid/revid is `142653/898594`; its 7,006-byte authority has
SHA-256
`85fed2deb4f46ff8279383f9047a43fc8aee39b3cd7ddc35293b0686dc40ddad`.
The final 29,383-byte lecture target has SHA-256
`b86102481c4997fb3f403d83809a5a4418ce9eae3c5d58b230693788afa7fbaa`;
the 7,175-byte worksheet target has SHA-256
`7fd09462ffe522d33330b4105b0cccbc04c9e7588e9bd7128e24c97dd2828c9c`.
All 12 exercises remain in source order: nine practice and three graded items
totaling 12 points; hints remain blank and no source solution exists. Thirteen
explicit corrections/refinements `O011-CORR-0250` through
`O011-CORR-0274` at their recorded noncontiguous IDs close the omitted map
label, malformed second derivatives, duplicated Christoffel equation,
regularity hypotheses, orientation-dependent curvature signs, and reader
language. The final POST QA is 7,491 bytes with SHA-256
`b5a35c91e7136592d80cc80d337d8667df1e6e125462ee7f2653d536ee9d4f55`;
its 3,976-byte independent binding receipt has SHA-256
`3d2ffa12b0ebd585a84ce8a4ef50eed1c26e7a8111eb7639d5d4c48339df841c`.

The active cursor is now the cumulative Unit 19 gate. The bounded dry audit
reconciles 92 source files, 50 Units 17-19 fragments, 394 cumulative exercises,
54 source-supplied solutions, 26 media assets, and two static-first animation
surfaces while preserving the published 3,208-record Units 1-16 backend
prefix. No cumulative PDF, HTML, backend, package, or publication is claimed
until the deterministic runtime and public-readback gates below pass.
