# Current state — O011 / D50

Updated: 2026-08-22 (Europe/Berlin)

## Objective

Produce a complete, independent, natural id-ID reader for smooth manifolds and differential geometry. Preserve exact mathematics, source topology, exercises, solutions where the authority supplies them, media attribution, and per-component rights. Stable identifiers and machine-readable exports are additive; reader quality remains primary.

## Edition-production spine and admission gate

- Holger Brenner, *Differentialgeometrie (Osnabrück 2023)*, German Wikiversity, is admitted as the complete 29-lecture/29-worksheet production spine for this independent Indonesian edition. Units 1–2 have passed their portable-build, translation, mathematical, rights, visual, structural, privacy, and backend gates.
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

- Authority freeze: core semantic and LaTeX/control exports are complete; Unit 1 has exact four-file binary-media closure and Unit 2 has exact two-file binary-media closure. Unit 2 authority, all 19 exercise candidates, and the five actually supplied solutions are frozen at page/revision and byte/hash granularity.
- Verified reader boundary: cumulative through Lecture 2, *Permukaan Putar, Medan Normal, dan Pemetaan Gauss*, plus Worksheet 2 and its five source-supplied solutions. Across Units 1–2 the reader contains 38 worksheet exercises and six supplied solutions.
- Final cumulative PDF through Unit 2: 3,152,320 bytes; SHA-256 `6312b4df706d0f08eeb9f37da0abda3428b5448dce54781d0f52eb9c8db5c385`; 44 A4 pages. Terminal QA receipt: `qa/unit-02/UNIT_02_QA.md`, 6,326 bytes, SHA-256 `ef1d89de134f4f9bca59513e8bc3790c9121e6b92d0dae5e67aa0fc882803e4f`.
- Cumulative backend: 357 schema-valid records across all 14 entity classes. The 174-record Unit 1 slice remains byte-identical; Unit 2 adds 183 records. JSONL SHA-256 `a393d3ff6c8aed203e7d3690eb6391e22ea25436cd06e85aa40e1adc23adb122`; CSV SHA-256 `5880fa9dee8bc0a73ed0e903d931fad38978bc2c9ef65cc58b62b48a7f26b7ba`.
- Current cursor: `unit-03`, source pair `Vorlesung 3` / `Arbeitsblatt 3`.
- Publication/push: the cumulative Unit 2 boundary is public in the dedicated repository `KokunoYumeto/brenner-differentialgeometrie-id`. Its bounded content commit is `500b2ce2cbc4eef0f1c443a2e5a22ab36ee9313a`; release tag `v0.2.0-unit-02` points to publication commit `2a1a0fa75462e70278a2b9d4aaaf759bfc5788ee`. Anonymous API, raw-file, manifest, and release-asset readback reproduced the exact 3,152,320-byte PDF and its SHA-256. Unit 1 remains available as the historical `v0.1.0-unit-01` release. Sanitized evidence is in `qa/unit-02/PUBLICATION_RECEIPT.md`.
- Upstream contact: prohibited during production and not used.

Known accessibility limitation: the cumulative PDF is not structurally tagged. It does carry `/Lang=id-ID`, all 28 unique embedded fonts have ToUnicode, and all 44 pages yield extractable text through both pypdf and pdfplumber. Semantic HTML remains the planned primary structured accessibility surface.

## Completion gate for each unit

1. Exact source revisions and content hashes recorded.
2. Natural id-ID reader prose; formulas, identifiers, order, exercises, and supplied solutions preserved.
3. Media present with exact source, creator, license, and hash.
4. Portable build completes from a clean bounded directory.
5. Structural and mathematical comparison passes; no unexplained source correction.
6. PDF/HTML visual and link/accessibility checks pass where those surfaces exist; disclose surface-specific limitations rather than overstating them.
7. Backend IDs resolve to the same source segments and are not required to read the edition.

## Resume order

Read `GOAL_AND_WORKFLOW.md`, `AUTHORITY_FREEZE.md`, `DECISION_LOG.md`, `CURSOR.json`, `TERMINOLOGY.csv`, and `ADVERSE_LEDGER.csv`; then continue only Unit 3. Freeze Lecture 3, Worksheet 3, every source-supplied solution, and its actual media closure before translation. Do not infer admission or completion from a generated file without the unit QA receipt.
