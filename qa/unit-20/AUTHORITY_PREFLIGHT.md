# Unit 20 authority preflight

Status: **PASS**. This boundary freezes authority only; no Indonesian translation is present.

## Exact root and `/latex` identities

| Surface | Page ID | Revision | Timestamp | MediaWiki SHA-1 (base36) | UTF-8 bytes |
|---|---:|---:|---|---|---:|
| lecture_root | 142564 | 991598 | 2025-01-23T13:23:29Z | `6ogstejiqfvotc6ie4c6tsnz1uwm2ed` | 3695 |
| worksheet_root | 142654 | 906457 | 2023-07-15T11:14:19Z | `75wvq6lazl2xaebidh9t637nz7zsr40` | 3029 |
| lecture_latex | 142594 | 807126 | 2022-09-18T10:00:30Z | `3e3nqvm6nsvokcc33v86ivll7ce6lru` | 9 |
| worksheet_latex | 142684 | 807095 | 2022-09-18T09:55:20Z | `3e3nqvm6nsvokcc33v86ivll7ce6lru` | 9 |

The root identities come from the already-frozen recursive export and selected-revision manifests. Each of the four page bodies now also has an exact UTF-8 base64 witness, a readable normalized witness, and hash-bound metadata.

## Official expanded LaTeX

| Surface | Saved API response | Sanitized German TeX |
|---|---|---|
| Lecture 20 | `authority/exports/lecture20_latex_expand.json`; 30324 B; `2b55a9642d49806161b13a342f3966d8c8a419b1147330b45566662b99340ca0` | `authority/expanded/lecture20_source.de.tex`; 25013 B; `6af7e41e240899c1866ff6c6904984c6eb5d3b436b47f07068cb4d29e40e1768` |
| Worksheet 20 | `authority/exports/worksheet20_latex_expand.json`; 12975 B; `4d63c037a5548ca1fd9683b83dd449f3959edf65a3dbd0c1bc2e6c8a8b4c3410` | `authority/expanded/worksheet20_source.de.tex`; 9463 B; `31d0d7d85a81923ca09f039e6ad938c9849b21998e7f800a4d35586c523238c1` |

The official `/latex` pages are nine-byte `{{Latex}}` invocations, so their page revisions alone do not freeze expanded mathematics. The byte-exact official API responses, request receipts, deterministic sanitation receipts, and UTF-8 German TeX witnesses are all retained.

## Worksheet exercise and solution census

Exercise count: **24**; graded: **5**; practice: **19**; graded-point total: **22**; source-supplied solutions: **5**; missing candidates: **19**.

| # | Exact task title | Root marker | Points | Expanded solution marker | Current `/Lösung` | Revision |
|---:|---|---|---:|---|---|---:|
| 1 | Äußere Ableitung/(x^2-y^3)dx+x^3y^2dy/Bestimme/Aufgabe | — | — | no | missing | — |
| 2 | Äußere Ableitung/xy^2dx+yzdy+x^3dz/Bestimme/Aufgabe | — | — | no | missing | — |
| 3 | Äußere Ableitung/x^2 durch y dx- x durch y^2 dy/Aufgabe | — | — | yes | exists | 1096829 |
| 4 | Äußere Ableitung/e^(xz)dx wedge dy -xyz dx wedge dz + (sin (cos (xy))+y^(10)z^(100))/Aufgabe | — | — | yes | exists | 1113687 |
| 5 | Äußere Ableitung/sin^3(t^4) durch 1+t^2/Und dt/Aufgabe | — | — | yes | exists | 1095872 |
| 6 | Äußere Ableitung/xdxdy+xy^2zdydz+xe^ydxdz/Bestimme/Aufgabe | — | — | no | missing | — |
| 7 | (2x-siny)dx-xcosydy/Geschlossen und exakt/Aufgabe | — | — | yes | exists | 614920 |
| 8 | Offene Teilmenge/R^n/Differentialform ersten Grades/Geschlossen/Aufgabe | — | — | no | missing | — |
| 9 | 1-Form/Vektorfeld/Geschlossen gdw Integrabilitätsbedingung/Aufgabe | — | — | no | missing | — |
| 10 | 1-Form/Vektorfeld/Exakt gdw Gradientenfeld/Aufgabe | — | — | no | missing | — |
| 11 | Differentialform/Rückzug/Exakt und geschlossen/Aufgabe | — | — | no | missing | — |
| 12 | Vektorfeld/(x,y) nach (-y,x)/Nicht integrabel/Formversion/Aufgabe | — | — | no | missing | — |
| 13 | Vektorfeld/Punktierte Ebene/(x,y) nach (-y,x) durch x^2+y^2/Integrabel nicht exakt/Formversion/Aufgabe | — | — | no | missing | — |
| 14 | Offene Menge/R^n/n-Form/Exakt/Aufgabe | — | — | yes | exists | 1096454 |
| 15 | 1-Form/Mannigfaltigkeit/Exakt gdw Wegintegrale endpunktabhängig/Aufgabe | — | — | no | missing | — |
| 16 | Differenzierbare Mannigfaltigkeit/Differenzierbare Abbildung/Rückzug einer volldimensionalen Form/Geschlossen/Aufgabe | — | — | no | missing | — |
| 17 | R_+ definierte Funktionen/Differenzierbare Fortsetzung nach 0/Aufgabe | — | — | no | missing | — |
| 18 | Halbraum/In R^n offene Umgebung/Kein Randpunkt/Aufgabe | — | — | no | missing | — |
| 19 | Halbräume/Übertragung von Begriffen/Diffeomorphismus, Totales Differential, Höhere Ableitung/Aufgabe | — | — | no | missing | — |
| 20 | Äußere Ableitung/xy^2z^3dx+xyzdy+x^3yz^4dz/Bestimme/Aufgabe | p | 3 | no | missing | — |
| 21 | Äußere Ableitung/xy^2dxdy+(x^3-y^2z^4)dydz+sin(xy)dxdz/Bestimme/Aufgabe | p | 3 | no | missing | — |
| 22 | Differentialform/Äußere Ableitung/Mehrfaches Dachprodukt/Formel/Aufgabe | p | 5 | no | missing | — |
| 23 | (2xy+3x^2-ye^(xy))dx+(x^2-xe^(xy)+8y)dy/Geschlossen und exakt/Aufgabe | p | 5 | no | missing | — |
| 24 | Halbebene und Quadrant/Homöomorph/Aufgabe | p | 6 | no | missing | — |

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

Production gate: **PASS**. The next action is the complete Indonesian translation of Lecture 20, Worksheet 20, and exactly the frozen supplied solutions, preserving the admitted media and source indices.
