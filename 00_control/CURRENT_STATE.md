# Current state — O011 / D50

Updated: 2026-08-22 (Europe/Berlin)

## Objective

Produce a complete, independent, natural id-ID reader for smooth manifolds and differential geometry. Preserve exact mathematics, source topology, exercises, solutions where the authority supplies them, media attribution, and per-component rights. Stable identifiers and machine-readable exports are additive; reader quality remains primary.

## Edition-production spine and admission gate

- Holger Brenner, *Differentialgeometrie (Osnabrück 2023)*, German Wikiversity, is admitted as the complete 29-lecture/29-worksheet production spine for this independent Indonesian edition. Units 1–3 have passed their portable-build, translation, mathematical, rights, visual, structural, privacy, and backend gates.
- This edition decision is not a decision to admit Brenner into the separate 40-course curriculum. The selection root must compare corpora independently and must not count completed work or sunk effort as evidence.
- Exact course page: pageid 142521, revision 889544, timestamp 2023-03-07T11:39:09Z, MediaWiki SHA-1 `e274ea4f0ae092736a5df23dfd3bb744184a9f2d`.
- Course structure: 29 lectures and 29 corresponding worksheets.
- Exact semantic freeze: 2,715 current-revision pages recursively exported with templates at 2026-08-21T09:52:04Z; 3,538,709 bytes; SHA-256 `6b96c90a8b1e52fac57c735f28d0babc56a95050ca015075b755179270d75d14`; revision-set digest `4810e9c13e352db58d7ceb5495c1cf86cb991d2193eaf6a344a48799e7ab0f71`.
- Text reuse path: CC BY-SA 4.0 with page-history attribution. Media rights are file-specific and must be carried row-by-row.

## Scope decision and comparison

Brenner is the strongest bounded candidate because it covers embedded geometry, abstract smooth manifolds, smooth maps, tangent/cotangent and vector bundles, orientation, differential forms, volume forms, Riemannian metrics, exterior differentiation, manifolds with boundary, partitions of unity, Stokes, general and linear connections, Levi-Civita connection, geodesics, curvature, and sectional curvature. It does not supply a self-contained de Rham-cohomology sequence or a Lie-group primer. If the build and rights gates pass, those become bounded original bridges rather than grounds for importing another book wholesale.

Petrunin–Zamora is optional visual supplementation only. Its curves-and-surfaces scope cannot replace the general-manifold spine. The lawful Dionne + Joyce + Petrunin–Zamora composite is much larger and more heterogeneous, retains a nonstandard Joyce adaptation-rights surface and component-media work, and still does not close advanced solved practice. It is not a cleaner edition design. No comparator is mixed silently into this edition.

## Upstream limitations admitted, not concealed

- The course pages are aggregators over live semantic pages; pinning 59 top pages is insufficient.
- Only one of the expected lecture/worksheet PDFs is present in the official Commons course category.
- `/latex` pages expand to body fragments using a custom macro vocabulary; the published preamble recipe is incomplete, legacy-encoded, and machine-specific.
- Therefore the reproducible baseline is rebuilt from the frozen recursive XML, frozen expanded fragments, exact media, and a small portable wrapper. The official Electron PDF is retained only as a rendering/accessibility witness.

## Production state

- Authority freeze: core semantic and LaTeX/control exports are complete. Unit 3 authority, all 21 exercise candidates, exactly two supplied solutions, and its exact three-file media closure are frozen at page/revision and byte/hash granularity. The cumulative reader now carries four Unit 1 media files, two Unit 2 media files, and three Unit 3 media files with component-specific rights.
- Verified reader boundary: cumulative through Lecture 3, *Kelengkungan Kurva Berparameter Panjang Busur*, plus Worksheet 3 and its two source-supplied solutions. Across Units 1–3 the reader contains 59 worksheet exercises, eight supplied solutions, and nine figures.
- Final cumulative PDF through Unit 3: 3,596,282 bytes; SHA-256 `aee7f335c8d8110feb7b70448c70680a30700285131d5a1b4e4aeb2f2d04b46a`; 56 centered A4 pages with wrapper-owned 22 mm margins. Terminal QA receipt: `qa/unit-03/UNIT_03_QA.md`, 7,211 bytes, SHA-256 `7781e297f7fb1688e271c8b7cc507d8efeac2d25b9ea8f84b046e3b68e3d9943`.
- Cumulative backend: 591 schema-valid records. The 357-record Unit 1–2 prefix remains byte-identical and Unit 3 adds 234 records. JSONL SHA-256 `e2b1e159b1dff04273ddb0af82e85dc32adbb507f3936881f750867527d6800a`; CSV SHA-256 `bdd4648d7e104da5f96a20ff85850a8782379f02609c3f29ed88117401032941`.
- Current cursor: `unit-04`, source pair `Vorlesung 4` / `Arbeitsblatt 4`.
- Publication/push: Unit 3 has passed its local publication gate and is being preserved as cumulative release `v0.3.0-unit-03` under the standing authorization. Until that transaction and anonymous public-byte readback complete, the cumulative Unit 2 boundary remains the latest publicly verified release. Unit 1 remains available as the historical `v0.1.0-unit-01` release.
- Upstream contact: prohibited during production and not used.

Known accessibility limitation: the cumulative PDF is not structurally tagged. It does carry `/Lang=id-ID`, all 28 unique embedded fonts have ToUnicode, and all 56 pages yield extractable text through both pypdf and pdfplumber. Semantic HTML remains the planned primary structured accessibility surface.

## Completion gate for each unit

1. Exact source revisions and content hashes recorded.
2. Natural id-ID reader prose; formulas, identifiers, order, exercises, and supplied solutions preserved.
3. Media present with exact source, creator, license, and hash.
4. Portable build completes from a clean bounded directory.
5. Structural and mathematical comparison passes; no unexplained source correction.
6. PDF/HTML visual and link/accessibility checks pass where those surfaces exist; disclose surface-specific limitations rather than overstating them.
7. Backend IDs resolve to the same source segments and are not required to read the edition.

## Resume order

Read `GOAL_AND_WORKFLOW.md`, `AUTHORITY_FREEZE.md`, `DECISION_LOG.md`, `CURSOR.json`, `TERMINOLOGY.csv`, and `ADVERSE_LEDGER.csv`; then continue only Unit 4. Freeze Lecture 4, Worksheet 4, every source-supplied solution, and its actual media closure before translation. Do not infer admission or completion from a generated file without the unit QA receipt.
