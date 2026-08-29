# Unit 24 authority preflight

Status: **PASS**. This boundary freezes authority only; no Indonesian translation is present.

## Exact root and `/latex` identities

| Surface | Page ID | Revision | Timestamp | MediaWiki SHA-1 (base36) | UTF-8 bytes |
|---|---:|---:|---|---|---:|
| lecture_root | 142568 | 901310 | 2023-07-04T16:00:52Z | `86n9yaalneq1uerb9rrxt0x35dt49f9` | 923 |
| worksheet_root | 142658 | 906309 | 2023-07-14T06:45:43Z | `85a7ruezww2d5nxtg6b1ayyppiy3wpg` | 1886 |
| lecture_latex | 142598 | 807130 | 2022-09-18T10:01:10Z | `3e3nqvm6nsvokcc33v86ivll7ce6lru` | 9 |
| worksheet_latex | 142688 | 807099 | 2022-09-18T09:56:00Z | `3e3nqvm6nsvokcc33v86ivll7ce6lru` | 9 |

The root identities come from the already-frozen recursive export and selected-revision manifests. Each of the four page bodies now also has an exact UTF-8 base64 witness, a readable normalized witness, and hash-bound metadata.

## Official expanded LaTeX

| Surface | Saved API response | Sanitized German TeX |
|---|---|---|
| Lecture 24 | `authority/exports/lecture24_latex_expand.json`; 30070 B; `6230db0ba8d73d539c72b703ddc244be86fc745cb9b978fc817ed0888396a0b3` | `authority/expanded/lecture24_source.de.tex`; 25046 B; `1eb16ffb8bbc5571341e32f7181f33c191ac3fbf770936c4d38b2b5b77ee7d0b` |
| Worksheet 24 | `authority/exports/worksheet24_latex_expand.json`; 15182 B; `bda4b44e8a5f271dfcb3b5d6921b82c4ec4b565addc5c4acbf43e476c19d46b9` | `authority/expanded/worksheet24_source.de.tex`; 11879 B; `c4c82a5a98a1091c49533665a04db9f35b3e541e5558a1c9c0b29d68e043e3e6` |

The official `/latex` pages are nine-byte `{{Latex}}` invocations, so their page revisions alone do not freeze expanded mathematics. The byte-exact official API responses, request receipts, deterministic sanitation receipts, and UTF-8 German TeX witnesses are all retained.

## Worksheet exercise and solution census

Exercise count: **15**; graded: **5**; practice: **10**; graded-point total: **18**; source-supplied solutions: **0**; missing candidates: **15**.

| # | Exact task title | Root marker | Points | Expanded solution marker | Current `/Lösung` | Revision |
|---:|---|---|---:|---|---|---:|
| 1 | Differenzierbare Mannigfaltigkeit/Vektorbündel/Kurze exakte Sequenz/Spaltung/Aufgabe | — | — | no | missing | — |
| 2 | Differenzierbare Hyperfläche/Tangentialbündel/Differenzierbarer Weg/Zweites Tangentialbündel/Aufgabe | — | — | no | missing | — |
| 3 | Kreis/Erstes und zweites Tangentialbündel/Implizit/Aufgabe | — | — | no | missing | — |
| 4 | Differenzierbare Faser/Erstes und zweites Tangentialbündel/Beschreibung/Aufgabe | — | — | no | missing | — |
| 5 | Differenzierbare Mannigfaltigkeit/Quader/Abbildung/Zweites Tangentialbündel/Aufgabe | — | — | no | missing | — |
| 6 | Differenzierbare Mannigfaltigkeit/Quader/Abbildung/Zweites Tangentialbündel/Kurze exakte Sequenz/Aufgabe | — | — | no | missing | — |
| 7 | Mannigfaltigkeit/Vektorbündel/R/Zusammenhang/Ränge/Aufgabe | — | — | no | missing | — |
| 8 | Mannigfaltigkeit/Nullbündel/Zusammenhang/Aufgabe | — | — | no | missing | — |
| 9 | Punkt/Vektorbündel/Zusammenhang/Aufgabe | — | — | no | missing | — |
| 10 | Mannigfaltigkeit/Vektorbündel/R/Zusammenhang/Vertikale Ableitung längs Abbildung/Aufgabe | — | — | no | missing | — |
| 11 | Topologischer Raum/Vektorbündel/Kurze exakte Sequenz/Rückzug/Aufgabe | p | 3 | no | missing | — |
| 12 | Offenes Intervall/Zusammenhang/Kurze exakte Sequenz/Aufgabe | p | 3 (1+2) | no | missing | — |
| 13 | Ebene Gleichung/Erstes und zweites Tangentialbündel/Implizit/1/Aufgabe | p | 4 | no | missing | — |
| 14 | Flächengleichung/Quadrik/Erstes und zweites Tangentialbündel/Implizit/1/Aufgabe | p | 5 (3+2) | no | missing | — |
| 15 | Offene Menge/Rang 1/Trivialer Zusammenhang/Funktion/Vertikale Ableitung/Aufgabe | p | 3 | no | missing | — |

All candidate solution titles were queried in one exact current-revision closure. Every existing solution has a lossless source witness, current revision metadata, official expanded LaTeX response, sanitized German TeX, and sanitation receipt. Macro/API agreement: **true**. All worksheet hint fields blank: **true**.

## Unit media closure

Displayed/licensed occurrences: **0**; unique admitted binaries: **0**.

No `\includegraphics`/`\bildlizenz` occurrence exists in the lecture, worksheet, or supplied-solution expansion; the exact media set is empty.

Every displayed image is paired with the source `\bildlizenz` macro. Current Commons rights-critical metadata and creator identity agree with the frozen whole-course row, and each admitted binary matches current size and SHA-1; SHA-256 is recorded locally. Exact localized credit HTML is preserved on both sides and may differ only by API interface language.

## Gate

- Root and surface revision/export bindings: pass.
- Official expansion preservation and deterministic sanitation: pass.
- Complete exercise, point, hint, marker, and candidate-solution census: pass.
- Every actually supplied solution frozen at source/revision/expanded-TeX granularity: pass.
- Exact lecture/worksheet/solution media and rights closure: pass.
- Translation started by this workflow: no.

Production gate: **PASS**. The next action is the complete Indonesian translation of Lecture 24, Worksheet 24, and exactly the frozen supplied solutions, preserving the admitted media and source indices.
