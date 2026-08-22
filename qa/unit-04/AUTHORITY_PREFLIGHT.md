# Unit 4 authority preflight

Status: **PASS**. This boundary freezes authority only; no Indonesian translation is present.

## Exact root and `/latex` identities

| Surface | Page ID | Revision | Timestamp | MediaWiki SHA-1 (base36) | UTF-8 bytes |
|---|---:|---:|---|---|---:|
| lecture_root | 142548 | 893683 | 2023-04-14T08:21:27Z | `m5bw869ocdnu96zkj86a49xd947srbm` | 189 |
| worksheet_root | 142638 | 1010985 | 2025-07-25T06:39:21Z | `d8r1ixhwrj3eok7ot4yn0c9epk2633j` | 1903 |
| lecture_latex | 142578 | 807138 | 2022-09-18T10:02:30Z | `3e3nqvm6nsvokcc33v86ivll7ce6lru` | 9 |
| worksheet_latex | 142668 | 807107 | 2022-09-18T09:57:20Z | `3e3nqvm6nsvokcc33v86ivll7ce6lru` | 9 |

The root identities come from the already-frozen recursive export and selected-revision manifests. Each of the four page bodies now also has an exact UTF-8 base64 witness, a readable normalized witness, and hash-bound metadata.

A separate official API query at `2026-08-22T07:25:23Z` confirms that all four frozen page IDs, revision IDs, `lastrevid` values, and timestamps remain live-current. The response and request identity are frozen in `authority/mediawiki/unit04_root_surfaces_current.json` and its receipt; the verified result is `qa/unit-04/CURRENT_REVISION_CHECK.json` (3,063 bytes; SHA-256 `357a36764e1f2b397b3130c482c85ddd592cf874cbb3db5028053d1e354066ab`).

## Official expanded LaTeX

| Surface | Saved API response | Sanitized German TeX |
|---|---|---|
| Lecture 4 | `authority/exports/lecture04_latex_expand.json`; 33018 B; `03cf5fee20d7a52a9e7bd820b30c23ebf0ebfa4bc3bf4f8b75160c5a4754a6fa` | `authority/expanded/lecture04_source.de.tex`; 26932 B; `610c85e2cb9838a2ce1deb488ceca6cb7d2ee2ab47f1e657d5df7488796f8402` |
| Worksheet 4 | `authority/exports/worksheet04_latex_expand.json`; 15342 B; `f3718aaf6e79ed1a74202abceb76da4ebcbeea65bd291f02110136744be7134a` | `authority/expanded/worksheet04_source.de.tex`; 11052 B; `81f8d9667581e0e6507dd1684b136c23f3352d1cabf2e8c4013daeb0a312cd00` |

The official `/latex` pages are nine-byte `{{Latex}}` invocations, so their page revisions alone do not freeze expanded mathematics. The byte-exact official API responses, request receipts, deterministic sanitation receipts, and UTF-8 German TeX witnesses are all retained.

## Worksheet exercise and solution census

Exercise count: **15**; graded: **4**; practice: **11**; graded-point total: **19**; source-supplied solutions: **2**; missing candidates: **13**.

| # | Exact task title | Root marker | Points | Expanded solution marker | Current `/Lösung` | Revision |
|---:|---|---|---:|---|---|---:|
| 1 | Linearform/Hyperebene/Weingartenabbildung/Aufgabe | — | — | no | missing | — |
| 2 | Differenzierbare Fläche/Standardkegel/Kreisbewegung/Aufgabe | — | — | no | missing | — |
| 3 | Differenzierbare Fläche/Standardzylinder/Kreisbewegung/Aufgabe | — | — | no | missing | — |
| 4 | Differenzierbare Fläche/Standardzylinder/Weingartenabbildung/Nicht bijektiv/Aufgabe | — | — | no | missing | — |
| 5 | Differenzierbare Fläche/Gerade/Weingartenabbildung/Aufgabe | — | — | no | missing | — |
| 6 | Differenzierbare Hyperfläche/Allgemeiner Zylinder/Weingartenabbildung/Aufgabe | — | — | no | missing | — |
| 7 | Eingebetteter Torus/Einheitsnormalenfeld/Weingartenabbildung/1/Aufgabe | — | — | yes | exists | 1094221 |
| 8 | Differenzierbare Fläche/Graph/Z ist xy/Weingartenabbildung/Jeder Punkt/Diagonalmatrix/Aufgabe | — | — | no | missing | — |
| 9 | Differenzierbare Hyperfläche/Weingartenabbildung/Isometrie/Aufgabe | — | — | no | missing | — |
| 10 | Differenzierbare Fläche/Ellipsoidoberfläche/Weingartenabbildung/Diagonalmatrix/Aufgabe | — | — | yes | exists | 1094288 |
| 11 | Differenzierbare Hyperfläche/Änderung der Orientierung/Eigenräume der Weingartenabbildung/Aufgabe | — | — | no | missing | — |
| 12 | Einschaliges Hyperboloid/Weingartenabbildung/x ist 0/Aufgabe | p | 4 | no | missing | — |
| 13 | Differenzierbare Fläche/Ellipsoidoberfläche/Weingartenabbildung/Diagonalmatrix/2/Aufgabe | p | 5 | no | missing | — |
| 14 | Differenzierbare Hyperfläche/Quadrik in 4 Variablen/Weingartenabbildung/Basis/Aufgabe | p | 4 | no | missing | — |
| 15 | Differenzierbare Fläche/Graph/Z ist x^3y^5/Weingartenabbildung/Diagonalmatrix/Aufgabe | p | 6 | no | missing | — |

All candidate solution titles were queried in one exact current-revision closure. Every existing solution has a lossless source witness, current revision metadata, official expanded LaTeX response, sanitized German TeX, and sanitation receipt. Macro/API agreement: **true**. All worksheet hint fields blank: **true**.

## Unit media closure

Displayed/licensed occurrences: **0**; unique admitted binaries: **0**.

No `\includegraphics`/`\bildlizenz` occurrence exists in the lecture, worksheet, or supplied-solution expansion; the exact media set is empty.

Every displayed image is paired with the source `\bildlizenz` macro. Current Commons rights-critical metadata and creator identity agree with the frozen whole-course row, and each admitted binary matches current size and SHA-1; SHA-256 is recorded locally. Exact localized credit HTML is preserved on both sides and may differ only by API interface language.

The standalone official Commons PDF is deliberately outside this zero-asset mathematical-media set. The exact empty closure is recorded in `qa/unit-04/media_closure.json` (1,827 bytes; SHA-256 `acf2a10f7daab6d4d4b62e6a9735041d3b1e519b9139f93ee815324e4a9ee289`).

## Official Unit 4 PDF witness

The sole existing course PDF, `File:Differentialgeometrie (Osnabrück 2023)Vorlesung4.pdf`, is frozen only as a local, unredistributed historical numbering/order witness. It is not editable authority, a production master, or a release asset. Its current Commons page is pageid `130922930`, revision `1003382720`; the file revision timestamp is `2023-04-20T19:44:46Z`. The exact 210,221-byte PDF has Commons SHA-1 `610c2216778a3121aee356f992560cd55ed90690` and SHA-256 `65ee310d19704bdbbb7f981f821901f96b166ceac416ad7cc063ae737894571d`. Current Commons metadata records artist `User:Bocardodarapti`, uploader `LavenderLina42`, and CC BY-SA 4.0.

Read-only structural and all-page visual inspection confirms a nine-page, untagged, unencrypted US Letter PDF produced by pdfTeX. Pages 1-7 contain the lecture, page 8 is blank, and page 9 is the image/license index. Page 9 internally attributes the page to Holger Brenner alias Bocardodarapti under CC-by-sa 3.0, while current Commons structured metadata says CC BY-SA 4.0. These are unresolved file-specific rights signals, not a merged or blanket license claim. The binary stays local and must not be redistributed or published. Exact evidence is `qa/unit-04/OFFICIAL_PDF_WITNESS.json` (947 bytes; SHA-256 `87422827230c2ce2faac3f957999b56c72cc1ea1cc11094652c800a44efbf05b`) and `qa/unit-04/OFFICIAL_PDF_STRUCTURAL_VISUAL_QA.json` (2,310 bytes; SHA-256 `b5395fd883a60fc6bb99f4c2e1050131ad59a18475c3626163b1dfa87a0f5cc5`).

## Authority anomalies requiring explicit translation review

The exact source contains six documented anomaly groups: a cone exercise whose stated curve generally is not on the cone; a graph-shape-operator lemma that states the second-fundamental-form matrix as the operator matrix; insufficient `C^1` hypotheses in two Weingarten-map exercises; an unfinished and algebraically damaged supplied Exercise 7 solution; a supplied Exercise 10 solution that omits the defining minus sign in `L=-DN`; and two literal lecture defects. The frozen witnesses remain unchanged. Exact evidence and mathematically checked disposition are in `qa/unit-04/AUTHORITY_ANOMALIES.md` (4,615 bytes; SHA-256 `dab36b02cc0f1ab9cf2177a1d615709851f2a869c35cc01e5f8e127ef36f7bd1`). These findings do not invalidate the authority closure, but every target correction or original completion requires explicit adverse-ledger provenance.

## Gate

- Root and surface revision/export bindings: pass.
- Official expansion preservation and deterministic sanitation: pass.
- Complete exercise, point, hint, marker, and candidate-solution census: pass.
- Every actually supplied solution frozen at source/revision/expanded-TeX granularity: pass.
- Exact lecture/worksheet/solution media and rights closure: pass.
- Official Commons PDF retained locally only and explicitly excluded from derivative authority, media, publication, and release roles: pass with unresolved file-specific CC BY-SA 3.0/4.0 signals disclosed.
- Authority anomalies frozen without silent repair and routed to the mathematical/adverse-correction gate: pass.
- Translation started by this workflow: no.

Production gate: **PASS**. The next action is the complete Indonesian translation of Lecture 4, Worksheet 4, and exactly the frozen supplied solutions, preserving the admitted media and source indices.
