# Unit 5 authority preflight

Status: **PASS**. This boundary freezes authority only; no Indonesian translation is present.

## Exact root and `/latex` identities

| Surface | Page ID | Revision | Timestamp | MediaWiki SHA-1 (base36) | UTF-8 bytes |
|---|---:|---:|---|---|---:|
| lecture_root | 142549 | 894651 | 2023-04-26T06:22:24Z | `aqei7hjs39ik210llvxlfogh4b8std7` | 547 |
| worksheet_root | 142639 | 894758 | 2023-04-26T17:41:28Z | `751pjv3ozqjvb9duqyh48qmvo8y8xte` | 2228 |
| lecture_latex | 142579 | 807139 | 2022-09-18T10:02:40Z | `3e3nqvm6nsvokcc33v86ivll7ce6lru` | 9 |
| worksheet_latex | 142669 | 807108 | 2022-09-18T09:57:30Z | `3e3nqvm6nsvokcc33v86ivll7ce6lru` | 9 |

The root identities come from the already-frozen recursive export and selected-revision manifests. Each of the four page bodies now also has an exact UTF-8 base64 witness, a readable normalized witness, and hash-bound metadata.

## Official expanded LaTeX

| Surface | Saved API response | Sanitized German TeX |
|---|---|---|
| Lecture 5 | `authority/exports/lecture05_latex_expand.json`; 29271 B; `a4e676350283ae17a92b674fa72e6a3d95960e56522373ec94c844be01a0f713` | `authority/expanded/lecture05_source.de.tex`; 23357 B; `d4d3549c402338aa7f65973fc3a6cb57822e9a75277d48ce1177672d73bc01be` |
| Worksheet 5 | `authority/exports/worksheet05_latex_expand.json`; 14631 B; `12f5d0ce34dd23eee1d27a6f651b2b114aa10bd4c1430db98b80d48f6da81465` | `authority/expanded/worksheet05_source.de.tex`; 10542 B; `88223af26d835e5be221b05a34fee7b374729af095ff7e053119761c6d09ed13` |

The official `/latex` pages are nine-byte `{{Latex}}` invocations, so their page revisions alone do not freeze expanded mathematics. The byte-exact official API responses, request receipts, deterministic sanitation receipts, and UTF-8 German TeX witnesses are all retained.

## Worksheet exercise and solution census

Exercise count: **15**; graded: **5**; practice: **10**; graded-point total: **22**; source-supplied solutions: **1**; missing candidates: **14**.

The first generated receipt draft reported 16 points because it omitted the split label `6 (2+2+2)` from the arithmetic while still counting that exercise as graded. The offline verifier rejected the inconsistency; the corrected total `4+4+6+6+2=22` is bound here and preserves the source label exactly.

| # | Exact task title | Root marker | Points | Expanded solution marker | Current `/Lösung` | Revision |
|---:|---|---|---:|---|---|---:|
| 1 | Quadratische Funktion/Zwei Variablen/Nullpunkt/Hauptkrümmungsrichtungen/Aufgabe | — | — | yes | exists | 1095881 |
| 2 | Rein-quadratische Funktion/Hauptkrümmungsrichtungen/Aufgabe | — | — | no | missing | — |
| 3 | Quadratische Funktion/Drei Variablen/Krümmungsverhalten/2/Aufgabe | — | — | no | missing | — |
| 4 | Quadratische Funktion/Drei Variablen/Charakteristisches Polynom/Aufgabe | — | — | no | missing | — |
| 5 | Graph/Z ist x^2+y^3/Krümmungseigenschaften/Aufgabe | — | — | no | missing | — |
| 6 | Funktion/Taylor-Entwicklung/Krümmungsverhalten/Aufgabe | — | — | no | missing | — |
| 7 | Differenzierbare Hyperfläche/Allgemeiner Zylinder/Hauptkrümmungen/Aufgabe | — | — | no | missing | — |
| 8 | Differenzierbare Hyperfläche/Gauß-Kronecker-Krümmung/Produkt der Hauptkrümmungen/Aufgabe | — | — | no | missing | — |
| 9 | Differenzierbare Hyperfläche/Dreidimensional/Weingartenabbildung/Charakteristisches Polynom/Gauß-Kronecker-Krümmung/1/Aufgabe | — | — | no | missing | — |
| 10 | Normalkrümmung/Differenzierbare Fläche/Tangentiale Richtung/Aufgabe | — | — | no | missing | — |
| 11 | Graph/Z ist Funktion in zwei Variablen/Krümmungseigenschaften/2/Aufgabe | p | 4 | no | missing | — |
| 12 | Quadratische Funktion/Drei Variablen/Krümmungsverhalten/3/Aufgabe | p | 4 | no | missing | — |
| 13 | Differenzierbare Hyperfläche/Dreidimensional/Weingartenabbildung/Charakteristisches Polynom/Gauß-Kronecker-Krümmung/2/Aufgabe | p | 6 | no | missing | — |
| 14 | Normalkrümmung/Differenzierbare Fläche/Tangentiale Richtung/2/Aufgabe | p | 6 (2+2+2) | no | missing | — |
| 15 | Normalkrümmung/Differenzierbare Fläche/Schnitt nicht regulär/Skizze/Aufgabe | p | 2 | no | missing | — |

All candidate solution titles were queried in one exact current-revision closure. Every existing solution has a lossless source witness, current revision metadata, official expanded LaTeX response, sanitized German TeX, and sanitation receipt. Macro/API agreement: **true**. All worksheet hint fields blank: **false**.

## Unit media closure

Displayed/licensed occurrences: **1**; unique admitted binaries: **1**.

| File | Surface(s) | Creator | License/status | License URL | Bytes | SHA-1 | SHA-256 | Commons revision |
|---|---|---|---|---|---:|---|---|---:|
| Minimal surface curvature planes-de.svg | lecture05 | Eric Gaba (Sting) | CC BY-SA 3.0; copyrighted=True; attribution=true | http://creativecommons.org/licenses/by-sa/3.0/ | 50805 | `4e9aca15c254ee07e01a99af4c7d0ea4f44b0ce7` | `c3048459dcf36445b38c5b734eee1febd21215bb08aeba9675cd1e5745cde873` | 796566416 |

Every displayed image is paired with the source `\bildlizenz` macro. Current Commons rights-critical metadata and creator identity agree with the frozen whole-course row, and each admitted binary matches current size and SHA-1; SHA-256 is recorded locally. Exact localized credit HTML is preserved on both sides and may differ only by API interface language.

## Gate

- Root and surface revision/export bindings: pass.
- Official expansion preservation and deterministic sanitation: pass.
- Complete exercise, point, hint, marker, and candidate-solution census: pass.
- Every actually supplied solution frozen at source/revision/expanded-TeX granularity: pass.
- Exact lecture/worksheet/solution media and rights closure: pass.
- Translation started by this workflow: no.

Production gate: **PASS**. The next action is the complete Indonesian translation of Lecture 5, Worksheet 5, and exactly the frozen supplied solutions, preserving the admitted media and source indices.
