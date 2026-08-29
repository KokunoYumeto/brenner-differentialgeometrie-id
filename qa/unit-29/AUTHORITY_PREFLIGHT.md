# Unit 29 authority preflight

Status: **PASS**. This boundary freezes authority only; no Indonesian translation is present.

## Exact root and `/latex` identities

| Surface | Page ID | Revision | Timestamp | MediaWiki SHA-1 (base36) | UTF-8 bytes |
|---|---:|---:|---|---|---:|
| lecture_root | 142573 | 906540 | 2023-07-15T18:45:21Z | `r8qudj7a5berxllr6r08ecygthzrxhk` | 604 |
| worksheet_root | 142663 | 907143 | 2023-07-18T17:21:55Z | `skvxnklukpdn23aatk4pvymi8n1ejm1` | 544 |
| lecture_latex | 142603 | 807135 | 2022-09-18T10:02:00Z | `3e3nqvm6nsvokcc33v86ivll7ce6lru` | 9 |
| worksheet_latex | 142693 | 807104 | 2022-09-18T09:56:50Z | `3e3nqvm6nsvokcc33v86ivll7ce6lru` | 9 |

The root identities come from the already-frozen recursive export and selected-revision manifests. Each of the four page bodies now also has an exact UTF-8 base64 witness, a readable normalized witness, and hash-bound metadata.

## Official expanded LaTeX

| Surface | Saved API response | Sanitized German TeX |
|---|---|---|
| Lecture 29 | `authority/exports/lecture29_latex_expand.json`; 28741 B; `9b38da14fbcc681e3ed245fe43e8955ff23c3930285f3f850c7827dbe170eb35` | `authority/expanded/lecture29_source.de.tex`; 23633 B; `9340f97d02677f67a496875c3b972350b94b7340b0d694923bc124d07b038c92` |
| Worksheet 29 | `authority/exports/worksheet29_latex_expand.json`; 2743 B; `6bea9e78f37b58bd0e34f4abe1814747dfc2b7f665f9dd6a6a2121aace2e36f3` | `authority/expanded/worksheet29_source.de.tex`; 2078 B; `422070f786b7d7ac19f6358e55c5c492a598cfa0f31d492cd9822ce9a8892e2e` |

The official `/latex` pages are nine-byte `{{Latex}}` invocations, so their page revisions alone do not freeze expanded mathematics. The byte-exact official API responses, request receipts, deterministic sanitation receipts, and UTF-8 German TeX witnesses are all retained.

## Worksheet exercise and solution census

Exercise count: **3**; graded: **0**; practice: **3**; graded-point total: **0**; source-supplied solutions: **1**; missing candidates: **2**.

| # | Exact task title | Root marker | Points | Expanded solution marker | Current `/Lösung` | Revision |
|---:|---|---|---:|---|---|---:|
| 1 | Mannigfaltigkeit/Tangentialbündel trivial/Triviale riemannsche Struktur/Krümmung/Aufgabe | — | — | no | missing | — |
| 2 | R^2/Offene Menge/Riemannsche Metrik/Levi-Civita-Zusammenhang/Krümmungsoperator/Berechnung/Aufgabe | — | — | yes | exists | 991186 |
| 3 | Torus/Riemannsche Struktur/Eingebettete Realisierung/Krümmung/Aufgabe | — | — | no | missing | — |

All candidate solution titles were queried in one exact current-revision closure. Every existing solution has a lossless source witness, current revision metadata, official expanded LaTeX response, sanitized German TeX, and sanitation receipt. Macro/API agreement: **true**. Source-supplied hints: **0** (exercise indices []); all worksheet hint fields blank: **true**.

## Unit media closure

Displayed/licensed occurrences: **1**; unique admitted binaries: **1**.

| File | Surface(s) | Creator | License/status | License URL | Bytes | SHA-1 | SHA-256 | Commons revision |
|---|---|---|---|---|---:|---|---|---:|
| Parallel lines in Poincare's model of hyperbolic geometry.svg | lecture29 | Januszkaja | CC BY-SA 3.0; copyrighted=True; attribution=true | https://creativecommons.org/licenses/by-sa/3.0 | 32238 | `ee99cc2a5eedddffa02a0d8ff313fd478ad35b5c` | `0be24daaf98af7e8f2758031765f16ece41e1e987cc5165871e3f2eb4f0675d8` | 449345728 |

Every displayed image is paired with the source `\bildlizenz` macro. Current Commons rights-critical metadata and creator identity agree with the frozen whole-course row, and each admitted binary matches current size and SHA-1; SHA-256 is recorded locally. Exact localized credit HTML is preserved on both sides and may differ only by API interface language.

## Gate

- Root and surface revision/export bindings: pass.
- Official expansion preservation and deterministic sanitation: pass.
- Complete exercise, point, hint, marker, and candidate-solution census: pass.
- Every actually supplied solution frozen at source/revision/expanded-TeX granularity: pass.
- Exact lecture/worksheet/solution media and rights closure: pass.
- Translation started by this workflow: no.

Production gate: **PASS**. The next action is the complete Indonesian translation of Lecture 29, Worksheet 29, and exactly the frozen supplied solutions, preserving the admitted media and source indices.
