# Current state — O011 / D50

Updated: 2026-08-29 (Europe/Berlin)

## Current verified boundary — Unit 22 cumulative release public and anonymously byte-verified; Unit 23 production active

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

The matching GitHub boundary is also public: commit
`e470fa5897708f49596488083b442c494ca9ab0e`, annotated tag
`v0.19.0-unit-19`, and release
`https://github.com/KokunoYumeto/brenner-differentialgeometrie-id/releases/tag/v0.19.0-unit-19`.
The independent credential-free verifier resolved the exact ancestry and
release metadata, then downloaded all seven assets and matched all 54,614,325
bytes by SHA-256 and MD5. Its receipt is 5,047 bytes, SHA-256
`991b1a037df12edf288085403054861e44816e9cc2a93f5c0d35af4c340f79fb`.
GitHub's API exposes the assets in deterministic filename order even though
they were uploaded PDF-first; the release notes explicitly identify the PDF as
the primary reader.

Unit 20 is exactly frozen and independently offline-verified. Lecture 20 is
pageid/revision `142564 / 991598`, with sanitized expanded-source SHA-256
`6af7e41e240899c1866ff6c6904984c6eb5d3b436b47f07068cb4d29e40e1768`;
Worksheet 20 is `142654 / 906457`, SHA-256
`31d0d7d85a81923ca09f039e6ad938c9849b21998e7f800a4d35586c523238c1`.
The worksheet has 24 exercises: 19 practice and five graded, totaling 22
points; exactly Solutions 3, 4, 5, 7, and 14 are source-supplied; every hint
field is blank; and the media closure is empty. MediaWiki's normalization of
the Exercise 17 solution candidate from `R_+` to `R +` is explicitly recorded,
not treated as a missing or extra page. The preflight, offline verifier, and
live-current-revision receipt SHA-256 values are
`9a4c9d9e871406ce0629fad3ef7193df99aadb790b445fce961aac6654147324`,
`bbcde73c065cb6caf386a4053d26f90925443f3c44a9f3f3384bb35b553d32ee`,
and `73d67138cd2e0a59f688b07b83624dff5b4d8bb45cedd1c532eacb9698e11d02`.
The complete Indonesian Unit 20 target now passes its bounded translation,
mathematical, structural, terminology, media, deterministic-build, and visual
gates. The final lecture and worksheet are 25,211 and 9,695 bytes with SHA-256
`4f6b2af7f168bec59cb4c8a02bdb66ade520f7ab110098ed6b24ca4be9b98fb7`
and `ccbae6a87a2e11d6cbcb076f27d16bb97c520ba5806a477a2d4b12fa5d9c3b9a`.
All 24 exercises remain in source order with the exact 19/5 practice/graded
split and 22 points. The five source-supplied solution pages remain attached
only to Exercises 3, 4, 5, 7, and 14. Exercise 7's malformed ASCII solution is
transparently repaired; Exercise 14's source page is explicitly marked
unfinished and is preserved as a visibly disclosed fragment rather than
misrepresented as a complete proof.

The ten explicit Unit 20 records `O011-CORR-0275` through `O011-ACC-0284`
at their recorded noncontiguous IDs close the pullback regularity hypotheses,
inverse-chart pullback notation, positive-degree exactness domain,
zero-dimensional half-space convention, half-line interval, two defective
source solutions, terminology, and two A4 reflows. The 13,674-byte formal POST
QA has SHA-256
`4f75d385d8613d71173f00855bc9270870bb2ad5ac51842bb806bed931763acf`;
its independent binding receipt has SHA-256
`00eb96eea2afab16dedf6e021f25edb60c60183facd8299056ecd49b069ec73c`.

The bounded unit-only reader is 16 centered A4 pages and 363,565 bytes with
SHA-256
`a5eff2cb30b006d4642d6dd7fdb32e5bc434930e8c77700e3a1bb4434e7f0498`.
Two independent three-pass builds are byte-identical; the final log has no
overfull/underfull boxes, undefined commands, or LaTeX/package warnings. This
is QA evidence rather than a new cumulative public release. The complete
bounded Unit 20 source, controls, and QA evidence are public on `main` at commit
`a7a450118e88727d160f1fd76d2dff2d0e22f92e`, tree
`902a418351aec0ff8e8d881846ce694bf65fb13b`. An unauthenticated GitHub API
readback matched both identities, and seven representative raw files matched
their local byte counts and SHA-256 values exactly. The 3,396-byte receipt is
`qa/unit-20/GITHUB_COMMIT_PUBLIC_READBACK_RECEIPT.json`, SHA-256
`a38ccd463520daf0a8cfc64cfa93909e2610697fee5bf8f57c14b7202a5c7c13`.
Unit 21 has now joined Unit 20 at the complete bounded translation gate, and
both bounded source checkpoints are public. The next executable action is the
exact Unit 22 authority freeze and source-ordered translation; the next
consolidated PDF/HTML/backend/publication boundary remains Units 20–22. The
full O011 goal remains unfinished.

Unit 21 is now admitted through an exact, independently verified authority
closure. Lecture 21 remains pageid/revision `142565 / 897931`; Worksheet 21 is
pageid/revision `142655 / 1113692`. The latter intentionally supersedes the
recursive-export baseline revision `900559`: the official revision comparison
shows one source repair only, adding the missing trailing `|` to the
`Not-star-shaped.svg` image macro. Both baseline and adopted witnesses remain
preserved. The transition receipt additionally proves that the baseline,
adopted, and already-frozen worksheet expansions are byte-identical at 12,497
UTF-8 bytes, SHA-256
`cba043d0692525c5aafd43901eaa0437c92ba608b8241f1f3b8f01edf011d951`;
its own SHA-256 is
`ddcec3f3b05ccb47b188814cdf8f5711b860c056d49ca0ba0c187c0236fcbae8`.
The 52,253-byte preflight has SHA-256
`ef14f5ffa01482dd67596adff3ef4c29d931c3c234979f2cbbb41f7e5089f194`;
its independent offline verifier has SHA-256
`d9ca3fd9f6767c393f37c996aff5bc0a4f11be0dea98520af89cc3f305cba0b6`;
and the final live-current receipt `qa/unit-21/CURRENT_REVISION_CHECK_R2.json`
has SHA-256
`0cc4febad5958fca8432f7aed16867cb8a9d9215ac40b57945111a453d329bbd`.

The admitted Unit 21 expansion contains a 24,383-byte lecture (SHA-256
`3bd477b25e7061b022dab80c007fcdaef0c72c3674e6b61651e2bf598811e9d9`)
and a 10,004-byte worksheet (SHA-256
`07915c64bad243ef085524475108f94b38f2e4432c787466b752ff1dec48743e`).
Its 20 exercises comprise 15 practice and five graded items totaling 24
points; exactly Solutions 7, 10, 12, and 13 are source-supplied and all hint
fields are blank. Three exact media assets are admitted: two public-domain SVGs
and `Circle on sphere wireframe 10deg 6r.svg` under CC BY 3.0, with creator and
rights metadata retained.

The complete Indonesian Lecture 21 and Worksheet 21 pair now passes protected
topology, mathematical, terminology, media-rights, independent-reader,
deterministic-build, and visual gates. The final lecture and worksheet are
24,518 and 10,101 bytes with SHA-256
`207266db84e4ce06f17d7fa9dd82383597b1dc54afd989f8ae082e222826fff3`
and `8418192976181a42355d9349af05e4683333d5041f0fd996c77d366820a36946`.
All 20 exercises retain their exact order, 15/5 practice/graded split, and 24
points. Only source-supplied Solutions 7, 10, 12, and 13 are included, with
SHA-256 values
`a8dc37a46a7f3a63e35e6e6f2e449f2f9ea1e54e5dd8a787d657f7b7bcd9b847`,
`0bf50584af30cec1246553e5ed796b2f81ae9e00f634c19b2ebbe6120ff795a8`,
`5dcd64ff8208506ca60e1b0a730f92af3db3f838c465b296f2d5a69b4c6e56a4`,
and `ea2841a4d57af79e727edee65dbea21371c70cb4a2a13d2799a71ddfda6a6bc2`.

Fourteen explicit Unit 21 records, `O011-CORR-0285` through
`O011-TRANS-0298` at their recorded mixed prefixes, bind the two media-credit
repairs, three lecture mathematics repairs, three supplied-solution repairs,
one loader-alias repair, the complete Indonesian pass, and the four findings
from independent review. Nothing is silent. Formal POST QA is 13,696 bytes,
SHA-256
`f389f1ae59621f5d16a4e0917c0299f3d2bedf5c68aab684e4d75ab45268419a`;
its independent binding receipt is 6,968 bytes, SHA-256
`89977cefeffe9b7d38fb24571e693ebce864dbc05b1a39c488a7f44fb763c6bd`.

The bounded Unit 21 reader is 18 centered A4 pages and 1,486,293 bytes,
SHA-256
`d423260ff0bf8525e4aea9ff68ae3d4f435b12c66685dacebc5bdfda567a2840`.
Two independent three-pass builds are byte-identical. The final log contains
no overfull or underfull boxes, undefined commands, duplicate hyperlink
destinations, or LaTeX/package warnings. Every rendered page was visually
inspected; the three figures, repaired sign argument, media attribution, and
license page are centered, legible, and unclipped. The build/visual receipt is
2,905 bytes with SHA-256
`3aa629928e6ea9bd8e5cbc09c2bfccd1d200cd23683b128c03645d00cb200624`.
This PDF is bounded QA evidence rather than a cumulative release. The exact
bounded source checkpoint is public on `main` at commit
`79617dbc308605c82c4f66ccda445c8c3adf26c8`, tree
`068e1e73acb41c272b843133dbf4ac3346dfaa01`. A credential-free GitHub API
readback matched both identities, and nine representative raw files—including
one licensed media derivative—matched their local byte counts and SHA-256
values exactly. The 4,064-byte receipt is
`qa/unit-21/GITHUB_COMMIT_PUBLIC_READBACK_RECEIPT.json`, SHA-256
`85fd8cf7eb3aee6e4658a580dbad9ea1d30b69f2fb283be3f84f3b330b8174dc`.

Unit 22 is now exactly frozen and independently verified. Lecture 22 is
pageid/revision `142566 / 1052940`; its 23,522-byte sanitized expansion has
SHA-256
`73121723a31462a430a32fca8aca18fb94834c3fed936ec08a7bc11a9c301fc0`.
Worksheet 22 is pageid/revision `142656 / 905863`; its 7,553-byte expansion has
SHA-256
`c66138c90289ba525cb861835720a44f26369a7f59c00f76db7994abd20392ec`.
The worksheet has exactly 19 exercises: 15 practice and four graded items
totaling 16 points. All hint fields are blank and only Solution 6 is supplied;
its 605-byte sanitized authority has SHA-256
`b181ad81b16c367d2ff99012aa97ae2cc058474dda93b008536b5df91a4f2039`.
Two public-domain media assets are rights-closed: `Inner point.png` by
Zasdfgbnm and `Partition of unity illustration.svg` by Oleg Alexandrov. The
35,444-byte preflight, offline verifier, and live-current receipt have SHA-256
values
`9dbb43502dfcf2d5d7faa0ec2b5e65cb96b3374a200a3d2d825f733d648a92c2`,
`4cd821f3a80d64a72cd5dd38882581814f660106a67a6ed5c8143905a02f8a67`,
and `b8f37a4db40e5fafa2d9fe537d2864afb19fbb51f08088a3020c0e01f6f95cca`.
The complete Unit 22 translation, explicit correction closure, and cumulative
Units 1–22 PDF/HTML/backend build are now closed locally as described below.

The cumulative Unit 22 PDF is 345 centered A4 pages and 9,046,717 bytes,
SHA-256
`4e6c03dc8388a4c10c464d939d5a416ab035c52e3bd233212c78a40617e02cf7`.
It contains 457 exercises, exactly 64 source-supplied solutions, 109
bookmarks, and 31 admitted media assets. Two clean three-pass build cycles are
byte-identical. The build, structural QA, and complete 345-page visual QA
receipts have SHA-256 values
`68aacdf979f81c432a62dd9cebf2d4bab8e017cc03cde60d60532aaa99e6312d`,
`f5e9ae47e09bd6759b32b5ae14d623f25c0fbb5feb51f1d21d42559291915159`,
and `b266ff257fd1777a40b024f747ed10ba15436141dc1235168c260832194d6f27`.
All pages are centered inside the accepted A4 bounds and visually clean. The
PDF remains untagged, but all 345 pages are text-extractable; all 34 embedded
font objects carry ToUnicode maps and the catalog language is `id-ID`.

The final reflowable HTML entry is 1,525,348 bytes, SHA-256
`260d16445fabffa3f3225c6c97c9727e2215378a29d5ad8d9e352d8adc5d5cd5`;
its manifest SHA-256 is
`c1d7a977f75c03ba839a6b805b5d521525cceaa103fff27469482eea1e18d3d5`,
and the complete tree digest is
`8a27ef38e1a25d623d3dd9ab000aa8c5c4c5fdba2c6fe2ed4dbdc99f4389afab`.
Structural and real-browser QA have SHA-256 values
`4bf37f194b5ef4bd300c068b04bf49f374ff0822a21996ce454ef599e5366377`
and `57b9b785277df2873631b61f85de34a3ce12e0916dfb264bd404e9a9060fc212`.
Desktop and mobile surfaces reflow without page-level overflow, all 7,261
MathJax elements typeset without runtime errors, wide formulas remain locally
scrollable, both static-first animation controllers pass, and all internal
links and images resolve.

The append-only backend preserves the exact 3,747-record public Unit 19 prefix
and adds 577 records, yielding 4,324 records. JSONL, CSV, manifest, and
independent two-cycle verifier SHA-256 values are
`448982cccc2f7c21e275faae1314f3ef6731f6ba36c939035b295dcc7b3d195a`,
`8bc81cbe634cb94f71640d1f5fd5e4c7a7697647f3a21b4ea161cb18c031d34b`,
`43d190abeb2321fc06b10e882699ba8838488dbde4357cac586146c645b0886f`,
and `cac8c90df35816902c873aa73dfcfd24f077e93412c3ade526b119493a4d3330`.
Schema, reference, duplicate-ID, canonical serialization, exact CSV
projection, prefix, live-hash, exercise/solution, media-rights,
correction-ledger, and determinism checks all pass.

The next executable action is to finish the two-clean-reconstruction source
package gate, publish this exact checkpoint in the existing GitHub and Zenodo
lineages, anonymously read back every public byte, and then advance directly
to Unit 23. That package gate has now passed: the seven public files total
73,215,901 bytes; release-preparation receipt SHA-256 is
`a862a3cc9f158c3a895fb37dd1691d7276de97494974ff097ea4689f9bac6480`,
and two independent clean, network-blocked reconstructions have integrity
receipt SHA-256
`84c08713a057a5703e3efac048b7afa1c494d22118393065a318ceb72081f09f`.
The 56,860,936-byte source ZIP has SHA-256
`8f85344d1fd91d709534b15b960ddaac16aaddfc2f5d6fb62cba802a99898f83`.
Both reconstructions rebuilt and independently verified the exact canonical
PDF, HTML tree/ZIP, and backend. Publication and anonymous readback are now the
next executable actions. The full O011 goal remains unfinished.

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

## Unit 22 bounded translation closure — 2026-08-28

The public Unit 19 cumulative boundary and the public Unit 20 and Unit 21
source checkpoints remain intact. Unit 22 is now completely translated and
passes its bounded source, mathematics, language, rights, accessibility, and
correction gates. The final lecture is 24,495 bytes, SHA-256
`9d00d0a1072c30f35c677b02ec68d7f9908c24f0ef0084da20193fc44102b1e1`;
the worksheet is 7,650 bytes, SHA-256
`8f83748984c53a9ebecd44ba14d439fee9087d65f6466e71b61da2b4ced885b1`;
and source-supplied Solution 6 is 582 bytes, SHA-256
`f887cc5de32991876780565b2a6a7a6553c859d614ee1a024d6bc24a7e865e1b`.
All 19 exercises remain in order: 15 practice and four graded items totaling
16 points; every hint field remains blank and no solution other than the one
actually supplied by the source is claimed.

The content-addressed POST receipt is
`qa/unit-22/POST_CORRECTION_MATH_QA.json`, 9,577 bytes, SHA-256
`80002ae88b1d748929f251ea15e14a013b4077f427beba1709488aada2f27e72`.
Its independent verifier receipt is 4,809 bytes, SHA-256
`61be508d59d9b7ca89ac85d434c696244617c0e1cda5ba09c2350835007ad870`.
One semantically empty blank paragraph inside the first comparison macro was
removed after the TeX-context gate; it changed no reader text or mathematical
profile and prevents `\par` from entering math mode. Thirteen distinct ledger records disclose the mathematical, translation,
media-loader, and accessibility changes; the two displayed public-domain
assets retain exact creator and source rights. No bounded Unit 22 defect
remains open.

## Unit 22 public lineage closure — 2026-08-28

The cumulative Units 1–22 checkpoint is public in both existing lineages. The
GitHub content commit is
`c7f4928327b3be9bc28a42543acbc43d7009410e`; annotated tag
`v0.22.0-unit-22` and public release `378563046` resolve to it at
`https://github.com/KokunoYumeto/brenner-differentialgeometrie-id/releases/tag/v0.22.0-unit-22`.
An independent credential-free verifier downloaded all seven release assets
and matched all 73,215,901 bytes by SHA-256 and MD5. Its 4,334-byte receipt is
`qa/unit-22/GITHUB_PUBLIC_READBACK_RECEIPT.json`, SHA-256
`55ce476b8e09d5e6d55db871bc6f2fbe0091c49b9d56dd0c26229da3eb3f321b`.

Zenodo version `2026.08.28-unit22` is public in the existing concept
`22059977` as record `22146873`, DOI `10.5281/zenodo.22146873`, with record
and files both public and the 345-page PDF configured as the default preview.
Record `22134954` remains its direct predecessor; no competing concept was
created. The publisher and a separate credential-free verifier each
downloaded the exact same seven files and matched all 73,215,901 bytes by
SHA-256 and MD5. The sanitized publication receipt is 4,955 bytes, SHA-256
`7fcb3923280b129b9c4c1c028c8fa2fe2860883c753cdffe83e6c21537ec346f`;
the independent 4,068-byte readback receipt has SHA-256
`0d3b14210fee7552cce8dd1aa442ea3c0f85b4dbb5686f4ee6e9cf9aa759c7c9`.

The exact active action is contiguous source-ordered Unit 23 translation. No
additional Unit 22 rebuild or release ceremony is pending. The full O011 goal
remains unfinished because Units 23–29, the ten-form official exam bank, and
the two original bridges remain.

## Unit 23 translation closure and active core sprint — 2026-08-28

Unit 23 is completely translated and its bounded topology, mathematics,
hint/solution, and media-rights checks pass. Lecture root pageid/revision is
`142567/991600`; the final Indonesian lecture is 25,831 bytes, SHA-256
`72d6bd0aa4d0c3a77b46746d6641fd9d9e038812f1abeb0904d14e872cd42dde`.
Worksheet root pageid/revision is `142657/1020032`; the final Indonesian
worksheet is 14,950 bytes, SHA-256
`9af134008d058544d00b7f4217a89f7a0683d70f347fa2d1bce6776fcb8c00c0`.
All 30 exercises remain in source order: 23 practice and seven graded items
totaling 26 points. Source hints exist only at 4, 5, and 19; source solutions
exist only at 6, 13, 16, and 17. Three media assets have file-specific rights
closure. No Unit 23 translation remains.

Unit 24 authority is frozen at a 15-exercise, five-graded/18-point worksheet
with no supplied solution or media. Its worksheet has been manually rewritten
in Indonesian and matches the source command, brace, link, and exercise
topology; the lecture is undergoing a full human-language rewrite because the
first generated prose draft was rejected rather than admitted. Units 25 and 26
are translating independently. Exact authority for Units 27–29 is already
frozen: Unit 27 has 23 exercises, four graded/18 points, supplied solutions
4/5/9/13 and one media asset; Unit 28 has seven exercises, two graded/five
points and supplied solutions 2/5; Unit 29 has three practice exercises,
supplied Solution 2, and one media asset. The next action is complete Unit 24,
then continue Units 25–29 without waiting on a cumulative rebuild.

## Units 24 and 26 translation closure; Unit 27 active — 2026-08-28

Unit 24 is now completely translated. The rejected generated prose was not
admitted. Its independently rewritten 24,647-byte lecture has SHA-256
`1a30fa076a0535c188cb5aba9c71d557e094bcc6f322340f7d35998ec6697166`;
its 11,818-byte worksheet has SHA-256
`2454f1169e7e12b4124cb2942e20f3bb1b70ad68943e77ede58127dfc62e10ac`.
Both preserve the frozen command, formula, environment, link, and brace
topology, and the lecture has no residual German reader prose. Their bounded
receipt hashes are
`898ab635870f323cd359478dbfe99fc7de356750f7b46e4830a31bb6c92530fb`
and
`9ee747bc334ff777cf5be301a05494ae1382439753277bb4547db44318df6abb`.

Unit 26 is also completely translated: a 27,185-byte lecture
(`b9915fa7e2bcda998f396829548a6a272d4ea516d5155bbb5695db69fbd0fdda`),
an 11,725-byte worksheet
(`9ae7f9c964286053cd0b58bde0c11c90a44b1bcc757fa2dedaaaca185b63916e`),
and supplied Solutions 3/6/9 with hashes
`6d1e3218dc4add645605ec77e5a6abcf2561790b741a8d1bb9d3a0006ddec3eb`,
`5665146bc9b1c3ced56ab618caec2531dd301497d3734752646f86de76600367`,
and
`b013b58e0ffd2c0ab9e40075b205933a3dd446ca01b10eff4a55abf15d5a8bc3`.
All bounded translation checks pass; the receipt SHA-256 is
`5d71e66f10d84f67853790559fd508fe7b99211314a38f286317c3780a2291e0`.
Three source defects are preserved, not silently repaired, in
`qa/unit-26/SOURCE_ISSUES.md`.

Unit 27 source-supplied Solutions 4, 5, 9, and 13 are now translated and each
passes the exact topology verifier. Lecture 27 and Worksheet 27 remain the
root's active reader-production work. Unit 25 continues independently; Unit
28's rejected draft is being replaced by a full rewrite; Unit 29's lecture is
translating independently. No cumulative rebuild has been started.

Unit 25 has subsequently closed as a complete translation: its 21,074-byte
lecture and 20,360-byte worksheet have SHA-256 values
`076e00279e59e6d9c7c59e3f27f21eb3b47dc4016699c407420bad3ced179639`
and
`f9382254ef5dee139db6650b88262b250af5fd055eb3bddab3a5b4b569324f40`.
All 25 exercises remain in order (21 practice, four graded/15 points), with
exactly source Solutions 1/7/8/11/12/14 translated. The strengthened completion
receipt, including all 35 immutable wiki-link destinations, has SHA-256
`ea47645aa715c8d1ace85585aac8751ae0c8115645c8458078ca9127de4bbc9c`.
The contiguous complete core prefix is now Units 1–26. Worksheet 27 and its
four supplied solutions are complete, so the only remaining core surfaces are
Lectures 27, 28, and 29, each now translating independently.

Units 28 and 29 have now closed completely. Unit 28's rejected mixed-language
lecture was replaced by a 17,682-byte natural Indonesian translation with
SHA-256
`2ef59ce9e1230c34a50e8c098676f8286cbda627b2a888de08ab19f96802f37e`;
its worksheet and source Solutions 2/5 have hashes
`15c77fc77b9e93694627d4371ada815c958204942ef8554fdb48f8eb651fb4f5`,
`069d757ea1da7ee81ea7326588273b16da5582ebc587322639d22581987cad4a`,
and
`b9997de6fe7bf24fa0ecf2a55711c13d711b92b11f752193c85f22c89858cf67`.
Unit 29's lecture, worksheet, and source Solution 2 have hashes
`74e8a2befbded780466fc6d2ff0c913c2d3d387e019bb16daf0fa961c51c43b2`,
`00aa6620956475bde67bb608b711f12edf1e8fcbf91900d2bd026be0235f0b31`,
and
`f8e058dc363f032f4de39ab8eeade26658568cb5e45acb909ae7e95aefe2f884`.
All exact formula, macro, link, identifier, and residual-language checks pass.

Worksheet 27 and its four source solutions also pass bounded verification;
their hashes are `a5d6c58bb96b80e7b381935465a6d9a55e2a18f890684d263032d442eda4ce1c`,
`3961beca50c57223e144592d1ca2e97e48bdba4eee8eb5703756249fef3d145c`,
`4c1db25df8021f1db13580b505edf6e5201814b46b793a98431dc8e1593b378f`,
`5b6c999a3f8b6c55d08b2fb6c8eceaab127116782a7b851b7af6f37a0bec9f8c`,
and
`b440e32bb0acc0d3744c78cfd1c0c99fcdf9837d17bb13fe5b2ffcddc6639cae`.
Lecture 27 is therefore the only untranslated Brenner core surface. The
official ten-form exam-bank recursive export and Exam 1 learner source are
already frozen; Exam 1 translation and closure sanitation proceed in parallel.

## Complete 29-unit core and assessment-bank production — 2026-08-28

Lecture 27 is now complete: 25,369 bytes, SHA-256
`37623a58c537cf9e13e00b189eda77d880adb43bc09e60662691bb2d58bd60d2`.
Its exact topology/math/link/media gate passes; the main and residual receipt
hashes are
`8338d27c86f7acb65240aed0d08d60454df6d314b6cd5fb836f65ba88efc2462`
and
`bf5cee385efe0158e6d318d5ecc762e7f5a84fe28f4fcccd1bde2b728a1fdf6b`.
One explicit protected-formula delta translates reader-facing German prose in
the final distance formula without changing its mathematics. Therefore all 29
official lectures, all 29 worksheets, and every actually source-supplied core
solution are translated. The cumulative PDF/HTML/backend gate remains batched
and does not interrupt assessment translation.

Exam learner forms 1–3 are now translated. Exam 1 preserves all 14 actual
occurrences and has SHA-256
`a150e6cd95ea93422051f6a51e76b38acbce7beb48591ab12b34d0cac3ebd95a`;
Exam 2 has SHA-256
`aabea31036649f07272167bc1b353f0afa769e22937969d44f4bc19893675aa3`;
Exam 3 has SHA-256
`b8b90e5cb0517ea101fcedd6658ffa9916b03b8bc7618aa74b18e9c1f9e86084`.
All bounded topology checks pass. Exam 3 has one declared, hash-bound
reader-language delta for `ist nilpotent` inside a protected formula. Exam 4
and Exam 5 learner forms are translating independently, and the combined
recursive exam authority/solution closure is being completed in parallel.

The official assessment authority closure now passes. A single recursive
Special:Export freeze contains 1,024 exact-revision pages and 10,335,457 bytes,
SHA-256
`726c50ee9e0f851e35ad8f8acd60dc2387e34e3fa1df7b71950b7f3bcf83312c`;
the independently recomputed revision-set digest is
`ff552c754740bdd9c4436f4e31f7e5164341435f634a075866d72d027d1f1e00`.
All 20 learner/solution LaTeX surfaces are frozen and sanitized. The exact
rendered census is 147 nominal slots, 24 empty placeholders, 123 actual problem
occurrences, 117 source-solution occurrences, and six missing solutions, with
per-form occurrence mappings preserved. The 50,562-byte authority manifest has
SHA-256
`42a3784adc1e7e6423ac503685ba05eb6cda43a7bd213e401614acd631c5b226`;
the occurrence map hash is
`ba85735a613267d28301ad0f62eafec5b0d3f18e36f107759ca3c0231345a8ec`.
This proves rather than assumes the selection record's 123/117/six figures.

## Exam learner forms 1–9 and complete original Lie bridge — 2026-08-28

Official learner forms 1–9 are now complete translations. Forms 4–9 have
target SHA-256 values
`16e2a99d9b62bd082cde86a45377c50f50a11b690a3781d925b29d2ee407d83d`,
`973cbcc3d40bbfd1870b2a50ec9423c1a9b85eedfe1e4c76e377868d7438cede`,
`7d65cd6c3eb1b2095e0343cebaa53185ed5dc9eb6e344e1bb968d745bcf02d49`,
`59ed3a24b089bb1788574ad5e5de21fc4363d3d753575b2226737d54ae34b9da`,
`20a6e0195458a3e6254d8955b0c14147399df2924312f45ae71f0aa5689ab97c`,
and
`5586288e11541188186bd087a939383fb56b7643910899ac33146166a38f6951`.
Their exact command/environment/math/protected-call/brace, problem-occurrence,
score, link, and residual-language gates pass. Exam 10 is the sole learner form
still active. Source-supplied solution Forms 1 and 2 are translating in
parallel; none of the six missing source solutions has been silently authored
or attributed to the source.

The original CC BY-SA 4.0 Lie-group/Lie-algebra bridge is now substantive and
complete at its content boundary. It covers matrix Lie groups, translations
and invariant fields, the Lie algebra and bracket, one-parameter subgroups and
the exponential map, `Ad`/`ad`, smooth actions, orbit tangent spaces, and
stabilisers. It contains exactly 12 exercises with staged hints and complete
solutions plus four cumulative mastery problems, each with a complete
solution, point rubric, and alternate parameters: 16 original
solution-bearing items. Theory and assessment hashes are
`42ef0c9dedda792d0c04614d58159d5f798765d1bfcbc3e3054a6065d70b6b3f`
and
`6d3d5555ee2845756f01415798e64d06893552e62a52d398e5c647298f96c6f5`.
A two-pass A4 smoke build yields 13 pages with no errors, warnings, box
overflow, duplicate labels, or unresolved references; its SHA-256 is
`bfe9d8dc4fd6ef61a57ae2246a30aed0c5f239aefdb6fff9277773bb44c5e585`.
The 2,543-byte content receipt has SHA-256
`e0d041cfacc626c3b91f57eae8849946a76632f3e8e223063c709e813901e3ad`.
The next executable action is to finish Exam 10 and continue the ten official
solution forms in source order; cumulative reader/backend work remains off the
translation critical path.

The second original bridge is also complete at its content boundary. The
CC BY-SA 4.0 de Rham/differential-topology module covers the de Rham complex,
the cohomology ring and pullbacks, a proved star-shaped Poincaré lemma, the
chain-homotopy formula and homotopy invariance, Mayer--Vietoris, exact
computations of `H^0`, `H^*(S^1)`, and `H^*(S^n)`, a clearly bounded de Rham
theorem statement, and honest degree/transversality/Morse gateways. It contains
exactly 12 staged-hint exercises and four cumulative mastery problems, all with
complete original solutions; all four mastery items include rubrics and
alternate parameters. Theory and assessment SHA-256 values are
`50feb003989fe674e41e3dd16fec85ad5b6dcc20f9cf6f7f2b09bdbf620ccd0e`
and
`270a158c20c9733a394a3163fd0ee4229addfe09a866a5a04be64effe4b474fe`.
The clean two-pass A4 smoke reader is 11 pages, SHA-256
`bb430cf267a1483f71305d8684406fd36c652d2566be7d893d8f295d2feeb260`;
the 2,642-byte receipt is
`692934c74f3f295523c230b677971dde203c9cb753923d5a844eec1b9ed5f4a4`.
Together, the two bridges now close all 32 selected bridge/mastery
solution-bearing items. The six original exam-solution repairs remain separate
and pending, so the selected total of 38 is not yet falsely declared complete.

Exam 10 learner form is now complete, closing all ten official learner forms.
Its 9,540-byte target has SHA-256
`989b0d2f8f6cc963b5e91537e811dc28a9cdea709a636a7843d69d0b9f257791`;
the exact topology receipt has SHA-256
`735bad9cc5f4162b9e55d902f20057c4173eeef71baefcc215f8306006c10d32`.
It preserves 14 nominal slots, 11 actual problems, three zero-point
placeholders, ten source-solution markers, and the one frozen missing solution.
Two hash-bound `und`-to-`dan` reader-word changes inside protected math macros
are recorded without altering mathematical arguments.

The current Exam 1 solution-form file is explicitly **not admitted**. A failed
draft left German prose and rewrite markers and its verifier fails two protected
surfaces; its current SHA-256 is
`6b217ecb50651570ee945969fed46b26821c630c49adc638eded0f125de6cbb6`.
It must be completely repaired before it can count toward the 117 supplied
solution occurrences. Exam 2 generation and Forms 3–5 translation proceed in
parallel. No failed draft is counted as completed work.

All six original repairs for the frozen source-missing exam occurrences are
now complete and explicitly separate from source-supplied solutions. They bind
one-to-one to Forms 1/3/5/7/9/10 and their exact occurrence hashes, carry
CC BY-SA 4.0 provenance, and are never attributed to Brenner or Wikiversity.
The 7,208-byte solution source has SHA-256
`4964e0600fc2f0d68c96856e48d4c240022d2cf13aecfe79fb4de2911c69fb3d`.
Its clean two-pass, three-page A4 smoke reader has SHA-256
`4acc780442a6af61b832a259db2ab2161abef013d1be3209e6c865a1fda0f8c0`;
the 3,238-byte occurrence/provenance receipt has SHA-256
`3b91f57b7fc3239474b4eaad86db93656cb0270ac570576080b3ddc7c4b8d819`.
Together with 16 items in each bridge, this closes exactly all 38 selected
original solution-bearing items. This does not close the edition: translation
of all 117 source-supplied exam-solution occurrences remains active.

## Seven official solution forms complete; three remain active — 2026-08-28

The earlier rejected Exam 1 draft has now been completely replaced and is
admitted. Official solution Forms 1, 3, 4, 5, 7, 8, and 9 pass bounded
translation, exact learner-prompt, occurrence, score, solution-presence, link,
and residual-language checks. Their target SHA-256 values are, respectively,
`57249c1c3f744dcfa2b6c717f967e08df4a72eed5513c5051a22a428d58c61d6`,
`b669281a35aa1db2065866b1fde31ef41c5d298adae295d02dee775e496747bb`,
`df52cef44c3afec3887c9eebd8a1f7627f78a7e1f67eecd40038a3aa49b1ea90`,
`76f0980e9fc5f399ce993206caefb17b40e11588e63cb1ac2b31d5e39b0ba2f1`,
`ddf8bcebcf19c9fc21757d763e75c52fbbb044ec64450d5d2c8c247ab630cc82`,
`64ee153d746d737bca0af1b47a981e75e62b9000b44ea483bb1afc9f7c2c6a15`,
and
`b1ad5b0ca45852e6e85e1b1aaf7b0fe0acab07ed952b14005ba8b5c87af0b290`.

Exam 1 preserves 14 actual occurrences, 13 official solutions, the exact
source-empty occurrence 11, and 65 points. Its bounded receipt is 2,052 bytes,
SHA-256
`903e520114936379ac80a5ad282b529df22a688a5a72e5dd40138336fa844e34`.
It also records one high-confidence source correction: for the ellipsoid
`2x^2+3y^2+5z^2=10` at `P=(-1,-1,1)`, the displayed tangent equation is
corrected from `-4a+6b+10c=0` to `-4a-6b+10c=0`, agreeing with the source's
own displayed gradient `(-4,-6,10)`.

Forms 2, 6, and 10 are the only remaining official solution forms and are
actively translating in parallel. No cumulative backend/PDF/HTML work starts
until these final source-supplied solutions are translated. The next executable
action is to admit Forms 2, 6, and 10 after their bounded checks, then build the
single complete cumulative reader/backend boundary.

## All selected translation complete; final reader assembly active — 2026-08-28

Official solution Forms 2, 6, and 10 are now admitted, so all ten official
solution forms and all 117 source-supplied solution occurrences are translated.
Their target SHA-256 values are, respectively,
`b0a1db42aff2c940a7532064a7b1fecf185279df0807171b86bfcc6176eaf060`,
`295dae1737ee8e7a2a3d42c8c143314ca46541328e7eeb30cbc483c906bac7db`,
and
`32a61474c2bc1de6c9deab27b7887f30f1636b5b5b21fd3678560e9780fd7678`.
Their bounded-QA SHA-256 values are
`38cf0d4133e252457eda07a9e162bc134a24cc07f39a26e3d4540cfba0a89c50`,
`7a1d9dd474c99a08c7ddbf7ff124500507b9916996f6ad7bd1b7d28ee170ab9f`,
and
`43d5178ecfa6be6b64549724f8e220bce5638e5e913435e616f46efdf831c111`.
All three preserve exact occurrence topology, admitted learner prompts, scores,
immutable link targets, and the official solution-presence pattern, with zero
rewrite markers or residual German reader prose.

The selected reader text is therefore complete: all 29 Brenner lecture and
worksheet pairs, all source-supplied core solutions, all ten learner and
solution exam forms, both original bridges, all 32 bridge/mastery items, and
all six separately identified original repairs. The remaining work is finite
assembly: complete append-only backend, centered A4 PDF, reflowable semantic
HTML, deterministic consolidated gates, compact release package, publication
in the existing lineages, and anonymous byte-for-byte readback.

## Complete local reader gate passed; release packaging active — 2026-08-28

The finite assembly is now closed locally. The complete centered A4 PDF is 712
pages and 10,525,469 bytes, SHA-256
`26f19153db2ca08851e182202900a8371f1816b428f8fe7321b35de60b9c84ef`.
Its two clean build cycles are byte-identical. Build and structural-QA receipt
SHA-256 values are
`8ac9e827cc11ccf96cf3e69decf55c46309acfbbbc6f69b02a5e645d970ec5f0`
and
`00071db04a52dc9678590a208db36791ca3b26969cf437ddb1ef804b9fc25869`.

The complete semantic HTML entry is 2,581,857 bytes, SHA-256
`ebee44b421d841f4be2ff22c2007f58c3c63b5042a63dfd96dcd079fc4d17c66`;
its manifest SHA-256 is
`ce25122eb211b9feeec34eebbde8d547a08506bfdebbcb29dbd65341acb28d1d`.
The final browser pass exposed and repaired one real Unit 29 MathJax defect:
literal nested Lie brackets had been mistaken for MediaWiki-link delimiters by
the inherited exporter. The scoped deterministic repair preserves the Jacobi
identity and now yields 12,484/12,484 MathJax containers, zero MathJax errors,
zero console warnings/errors, zero broken internal fragments, and no global
desktop or mobile horizontal overflow. Browser-QA SHA-256 is
`5b9ee13df8d569b6c64c27c09cfcf1885fc78b29afff1baed106a9d6dd63fc94`.

The append-only backend contains 6,912 records while preserving the exact
4,324-record Unit 22 prefix. JSONL, CSV, manifest, and verifier SHA-256 values
are
`cf875638bbb7ffb657d5932c1663c063f6832495b2f755830d26121d1a631e26`,
`e97f94a5e221f7c5abdfb24a7795761f75a1c999f4da06500bb24e41c3c632db`,
`4bc497f5f26781ac0bb55b0db2ffa206774477a32790ec1890fd425b2861fb53`,
and
`33e99fd777ed327414073cc1ee3db95d735075dfd3650bfd44fe8bf2b9ec3116`.

The exact next action is release packaging, two clean offline source-package
reconstructions, publication in the existing Zenodo and GitHub lineages, and
anonymous byte-for-byte public readback. No translation, bridge, assessment,
or reader-build work remains open.

## Terminal complete edition published and independently read back — 2026-08-29

The complete selected O011 edition is finished. It contains all 29 Brenner
lecture/worksheet pairs, all 576 core exercises and 84 source-supplied core
solutions, all ten official learner and solution exam forms with 123 actual
problem occurrences and 117 source-supplied solution occurrences, the six
separately identified original missing-exam repairs, and both original bridges
with 32 further solution-bearing items. Thus all 38 selected original
solution-bearing items are present and no translation surface remains open.

The final centered A4 PDF remains 712 pages, 10,525,469 bytes, SHA-256
`26f19153db2ca08851e182202900a8371f1816b428f8fe7321b35de60b9c84ef`.
The semantic HTML entry remains 2,581,857 bytes, SHA-256
`ebee44b421d841f4be2ff22c2007f58c3c63b5042a63dfd96dcd079fc4d17c66`.
The append-only backend remains 6,912 records; JSONL SHA-256 is
`cf875638bbb7ffb657d5932c1663c063f6832495b2f755830d26121d1a631e26`.
The seven-file public payload is 87,434,229 bytes. Its source/backend ZIP is
69,147,984 bytes, SHA-256
`051324674c298cfb261dac7b8b98b0d316ea4bca948eb3f1224fc2162fb163c7`.
Two independent clean extraction/rebuild/restage cycles passed; integrity
receipt SHA-256 is
`5f6eecdae0542b42ee06745db0fbc8733f9e2e305017d976bd1b1622a9b35096`.

GitHub commit `d6f21e46c10a3562a42e1c7a3cc5c4ea1c0f855d`, annotated tag
`v1.0.0`, and release ID `378834384` are public at
`https://github.com/KokunoYumeto/brenner-differentialgeometrie-id/releases/tag/v1.0.0`.
The independent unauthenticated verifier downloaded all seven assets and
matched all 87,434,229 bytes. Publication and readback receipt SHA-256 values
are `c90be7067e772f67f69687f4cc41ca63dfea0ec59b2261ae9d142591f6000849`
and `a3ccd29212a0f858d8643d0820fe0c612c6985aff9debeea4ddd1b502409c650`.

The same exact seven files are public in the existing Zenodo concept at record
`22160677`, DOI `10.5281/zenodo.22160677`, with the PDF as the default preview.
The independent credential-free verifier matched all seven names, metadata,
licenses, relationships, 87,434,229 bytes, MD5 values, and SHA-256 values.
Publication and readback receipt SHA-256 values are
`b3c9fac14da08010379ecc1f52edf05dd5a6994062b6c8a0f0d37ed1d23b5f54`
and `421afcdcb2ce217cc8f53b672c0396d51b2c52ba424bb618a84538fa8777f909`.
The concept DOI remains `10.5281/zenodo.22059977`; no duplicate concept or
competing record was created.

The terminal condition is satisfied. No translation, build, backend, rights,
publication, or public-byte-verification action remains.

## Corrective r1 release staged; public successor pending — 2026-08-29

The terminal audit found one real release defect in the otherwise complete
edition: the derived complete PDF had inherited the Unit 22 checkpoint title
and scope prose. This affected the visible title page, the embedded `/Title`,
and the edition note; it did not affect the translated mathematics. The frozen
Unit 22 driver remains untouched. The complete-driver builder now applies
exactly three enumerated substitutions and proves that reversing them restores
every frozen prefix byte.

The corrected PDF remains 712 centered A4 pages. It is 10,524,618 bytes,
SHA-256
`e0b416d91dfa8de4d5fbf7d84add34cfb3b57adde4645f60c4bc0a0609f5bd2f`.
Its visible title is `Edisi Lengkap Bahasa Indonesia`, its embedded title is
`Geometri Diferensial dan Manifold Mulus Edisi Lengkap Bahasa Indonesia`, and
the frontmatter now states the complete 29-lecture/29-worksheet scope and the
separation of all 38 original solution-bearing items. Two clean PDF cycles are
byte-identical. Driver-derivation, build, and structural-QA receipt SHA-256
values are
`c63cae90487dde58115c2f41fa9d94bc65d01fcf6b2702364c829c4b1eebe501`,
`3ed6ecab0416a94213dbeb32ddea6e5eb0b9b0b9f427ef1e377403cabed7908e`,
and
`23f806804dd2591480764eb5a9415ef32fb233a4f4f151eace6eb534b8bdeb97`.

The corrective seven-file payload is staged at
`output/release-complete-r1`, totaling 87,438,798 bytes. Two independent
offline extraction/rebuild/restage cycles reproduced every byte. Release
preparation and source-package-integrity receipt SHA-256 values are
`31230e50c1fe2343d0306eb91ff9780e07fd0de130aff4cf0d849f10b535caab`
and
`1a943744f3a96786f88c61396f9a6102fc66c07eb697fdd3b7fa90b3bf011221`.
The old GitHub `v1.0.0` and Zenodo record `22160677` remain untouched as
historical witnesses. The exact next action is to commit and push this candidate,
publish GitHub `v1.0.1` and a successor in Zenodo concept `22059977`, then
anonymously download and hash all seven public files in each lineage.
