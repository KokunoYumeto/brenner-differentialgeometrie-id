# Unit 15 authority preflight

Status: **PASS**. This boundary freezes authority only; no Indonesian translation is present.

## Exact root and `/latex` identities

| Surface | Page ID | Revision | Timestamp | MediaWiki SHA-1 (base36) | UTF-8 bytes |
|---|---:|---:|---|---|---:|
| lecture_root | 142559 | 991595 | 2025-01-23T13:23:09Z | `eyal6k850lvp9r5k7a5wtxissy8z1lh` | 3158 |
| worksheet_root | 142649 | 899070 | 2023-06-21T09:48:22Z | `qi7v542hf1tgxf9n6ho1rdmg0qp1dyn` | 1799 |
| lecture_latex | 142589 | 807120 | 2022-09-18T09:59:30Z | `3e3nqvm6nsvokcc33v86ivll7ce6lru` | 9 |
| worksheet_latex | 142679 | 807089 | 2022-09-18T09:54:19Z | `3e3nqvm6nsvokcc33v86ivll7ce6lru` | 9 |

The root identities come from the already-frozen recursive export and selected-revision manifests. Each of the four page bodies now also has an exact UTF-8 base64 witness, a readable normalized witness, and hash-bound metadata.

## Official expanded LaTeX

| Surface | Saved API response | Sanitized German TeX |
|---|---|---|
| Lecture 15 | `authority/exports/lecture15_latex_expand.json`; 40211 B; `13e0b1c80a33f51c7378b7584476b20064ad28f02047bdf35cbdb9b4abd20fd1` | `authority/expanded/lecture15_source.de.tex`; 33156 B; `5645c84aed54603af32dda35ae73008c964b0a850b5a9bedffa27f2c62b38bc8` |
| Worksheet 15 | `authority/exports/worksheet15_latex_expand.json`; 10957 B; `c09668fb40eeacd7cb23790f4275e6a904df87bffe3e4edf22d6c5cf2db3a5b9` | `authority/expanded/worksheet15_source.de.tex`; 8200 B; `e425eede128eefd7d8eae134076caed6f0782e40e148b73eeaf843e1c740a621` |

The official `/latex` pages are nine-byte `{{Latex}}` invocations, so their page revisions alone do not freeze expanded mathematics. The byte-exact official API responses, request receipts, deterministic sanitation receipts, and UTF-8 German TeX witnesses are all retained.

## Worksheet exercise and solution census

Exercise count: **16**; graded: **3**; practice: **13**; graded-point total: **13**; source-supplied solutions: **4**; missing candidates: **12**.

| # | Exact task title | Root marker | Points | Expanded solution marker | Current `/Lösung` | Revision |
|---:|---|---|---:|---|---|---:|
| 1 | Kompakte Mannigfaltigkeit/Positive Volumenform/Endlich/Fakt/Beweis/Aufgabe | — | — | yes | exists | 1021853 |
| 2 | Positive Volumenform/Volumenmaß/Ist Maß/Aufgabe | — | — | no | missing | — |
| 3 | R^n/Standardform/Integration über Teilmenge/Aufgabe | — | — | no | missing | — |
| 4 | Integration auf Mannigfaltigkeiten/Nullmengen/Ignorierbar/Aufgabe | — | — | no | missing | — |
| 5 | Volumenform/Integration/Eigenschaften/Fakt/Beweis/Aufgabe | — | — | no | missing | — |
| 6 | Mannigfaltigkeit/Abzählbare Topologie/Nullmengen/Unabhängig von Volumenform/Aufgabe | — | — | no | missing | — |
| 7 | S^1/Faser/Gradient/Längenform/Aufgabe | — | — | no | missing | — |
| 8 | S^2/Faser/Gradient/Flächenform/Aufgabe | — | — | no | missing | — |
| 9 | Wegintegral/Mannigfaltigkeit/Differenzierbare Abbildung/Aufgabe | — | — | no | missing | — |
| 10 | Wegintegral/Trigonometrischer Kreis/xdx+ydy etc/Aufgabe | — | — | no | missing | — |
| 11 | Wegintegral/x^3dx-yzdy+xz^2dz/(-t^2,t^3-1,t+2)/-1 bis 0/Aufgabe | — | — | yes | exists | 1096774 |
| 12 | Wegintegrale/t nach (t,t^(-1))/(u,v) nach (u^2,uv,-u+v^2)/xdx-zdy+dz/Aufgabe | — | — | yes | exists | 1096775 |
| 13 | Wegintegrale/t nach (t,t^3)/(u,v) nach (u^3,u^2+v^2,u^-1+v^-1)/(x-y)dx-z^2dy+dz/Aufgabe | — | — | yes | exists | 1096776 |
| 14 | Abgeschlossene Untermannigfaltigkeit/Volumenform/Kleinere Dimension/Nullmenge/Aufgabe | p | 4 | no | missing | — |
| 15 | Wegintegral/R^2/Monomiale Daten/Aufgabe | p | 4 | no | missing | — |
| 16 | Wegintegral/Trigonometrische Helix/(y-z^3)dx+x^2dy-xzdz/Aufgabe | p | 5 | no | missing | — |

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

Production gate: **PASS**. The next action is the complete Indonesian translation of Lecture 15, Worksheet 15, and exactly the frozen supplied solutions, preserving the admitted media and source indices.
