# O011 Indonesian field-terminology check

Date: 2026-08-22
Scope: read-only comparison against `00_control/TERMINOLOGY.csv` and all `*.id.tex` files in Units 1-6. No production or control file was changed.

## arXiv result and fallback

No suitable Indonesian-language arXiv record with downloadable TeX source was found in the bounded check. On 2026-08-22, the official arXiv search returned zero records for each exact all-field phrase:

- `"geometri diferensial"`
- `"ruang singgung"`
- `"manifold diferensiabel"`
- `"turunan kovarian"`

Official query pattern: `https://arxiv.org/search/?query=...&searchtype=all&abstracts=show&order=-announced_date_first&size=50`. General web searches restricted to arXiv also returned no suitable Indonesian TeX source. This does not prove that no Indonesian prose exists inside any arXiv source package; it establishes that the bounded, reproducible metadata/web search did not identify one. The requested fallback was therefore used honestly.

## Main representative fallback

Hari Taqwan Santoso, *Aspek Topologis dan Struktur Kausal Ruangwaktu dalam Teori Relativitas Einstein*, Skripsi S-1 Fisika, UIN Sunan Kalijaga Yogyakarta, 2016.

- Official item: https://digilib.uin-suka.ac.id/id/eprint/22593/
- Official public PDF: https://digilib.uin-suka.ac.id/id/eprint/22593/1/11620017_BAB-I_IV-atau-V_DAFTAR-PUSTAKA.pdf
- Repository status: Published Version; deposited 2016-11-03. The separate middle-chapters file is restricted to registered users. The public file still contains the title/authority pages, contents naming the complete mathematical sequence, and substantive appendices on tangent projection, covariant differentiation, metric connection, second fundamental form, and curvature.
- Local PDF: `santoso-2016-aspek-topologis-struktur-kausal.pdf`
- PDF: 6,690,702 bytes; SHA-256 `fefc426be169a1acf84869ddcaf0fb8825428c88fa0bd1587f30c590ad976fdf`; 51 A4 pages.
- Extracted text: `santoso-2016-aspek-topologis-struktur-kausal.layout.txt`; 75,334 bytes; SHA-256 `70e52dce20b9e794e27e26a7b60f58f5decb04f656b7eeca65435fa863486a8c`.
- Visual witnesses: `render-p1-01.png`, `render-p9-09.png`, `render-p44-44.png`, `render-p45-45.png`.

Short direct term evidence in the extracted text:

- lines 172, 176, 178, 182: `Sekatan Kesatuan`, `Keragaman Diferensiabel`, `Ruang Singgung`, `Forma Diferensial`.
- lines 186-188, 193: `Koneksi`, `Geodesik`, `Kelengkungan`, `Koneksi Levi-Civita`.
- lines 1429, 1436-1443: `ruang singgung`, `medan vektor singgung`, `turunan kovarian`, and adjectival `tangensial` occur together in mathematical prose.
- lines 1466-1469: `koneksi metrik`, `turunan kovarian`, and `forma asasi kedua`.
- lines 1478-1483: `Tensor Kelengkungan` and `komponen singgung`.

## Secondary primary-source corroborator

Salman Farishi, *Solusi Schwarzschild untuk Perhitungan Presisi Orbit Planet-Planet di Dalam Tata Surya dan Pergeseran Merah Gravitasi*, Skripsi S-1 Fisika, Universitas Indonesia, April 2010 (defended 2010-05-11).

- Official PDF: https://lib.ui.ac.id/file?file=digital%2Fold23%2F20181580-S29377-Salman+Farishi.pdf
- Local PDF: `farishi-2010-solusi-schwarzschild.pdf`
- PDF: 3,451,904 bytes; SHA-256 `e23e09a95ea2245aeb891205db173334b4eb1093fb4922b5c64238fc1fa3c042`; 91 letter pages.
- Extracted text: `farishi-2010-solusi-schwarzschild.layout.txt`; 132,277 bytes; SHA-256 `e5992c7a7479dc660fe22983ab661ee48a87e40607eeca3e85d057e5fc52c2a9`.

Short direct term evidence:

- lines 764-768 and 900-903: `manifold` and `manifold diferensiabel`.
- lines 1020-1041: `tensor kelengkungan Riemann`, `pergeseran sejajar`, `panjang busur`, and `garis geodesik`.
- lines 1256-1283: `geodesik`, `transpor paralel`, adjectival `tangen`/`tangensial`, and `turunan kovarian`.

## Lane snapshot compared

- `00_control/TERMINOLOGY.csv`: 8,656 bytes; SHA-256 `b91163237a0bedb048aa2c254db84a2a911bbc55a37c2cbf680d7d7368edda31`.
- Unit 1-6 snapshot: 26 Indonesian TeX files, 269,189 bytes. SHA-256 of the UTF-8 sorted `relative-path<TAB>bytes<TAB>sha256` manifest serialization: `bbf9ae96ce9680dc4368386ad74ec122353d5b7921e2f8e729fa2125ba68d240`.
- Point-in-time occurrences: `ruang tangen` 66 vs `ruang singgung` 0; `vektor tangen` 47 vs `vektor singgung` 0; `garis tangen` 2 vs `garis singgung` 0; `transport paralel` 7 vs `transpor paralel` 12; `manifold` 4 vs `keragaman` 0; `koneksi` 2; `geodesik` 22; `kelengkungan` 147. Unit 6 was active, so re-count before propagation.

## Decisions

1. **Refine nominal tangent terms to native field usage.** Change reader-facing `ruang tangen` to `ruang singgung`, `vektor tangen` to `vektor singgung`, and `garis tangen` to `garis singgung`. The UIN witness uses the singgung family consistently, and official Indonesian curricula from ITB and UGM independently do the same. Retain adjectival `tangensial`: the UIN witness itself uses `komponen tangensial`, and this avoids awkward compounds.
2. **Keep `manifold` as the primary noun.** Indonesian usage is genuinely mixed: Santoso uses `keragaman`, while Farishi and current ITB mathematics usage use `manifold`. The edition title and established glossary already use `manifold`; changing it would reduce international discoverability without improving mathematical precision. Add `keragaman` as a search/glossary alias, not a prose-wide replacement.
3. **Keep `terdiferensialkan` for functions/curves and `diferensiabel` for manifold noun phrases.** Both constructions are attested in Indonesian academic mathematics. A wholesale replacement of the current 176 `terdiferensialkan` occurrences is not supported as a correction. However, normalize the isolated Unit 6 phrase `manifold terdiferensialkan` to the admitted `manifold diferensiabel`.
4. **Standardize Unit 6 to `transpor paralel`.** The worksheet/solutions already use `transpor paralel`, the lecture currently uses `transport paralel`, and the UI witness explicitly uses `transpor paralel`. Replace the lecture's seven `transport paralel` occurrences and admit one canonical glossary row for German `Paralleltransport` -> `transpor paralel`.
5. **Keep `bentuk diferensial` and `partisi satuan` as reader-facing primaries, but record aliases.** Santoso's `forma diferensial` and `sekatan kesatuan` are valid field variants; they do not make the current natural Indonesian choices erroneous. Add the variants to glossary notes/search aliases. Likewise, retain `bentuk fundamental kedua`; record `forma asasi kedua` as an alias only.
6. **Keep the aligned core terms unchanged:** `koneksi`, `koneksi Levi-Civita`, `turunan kovarian`, `geodesik`, `kelengkungan`, `panjang busur`, and `tensor kelengkungan Riemann`.
7. **Do not force cotangent/bundle terminology into a false morphological symmetry.** Keep `ruang kotangen` and `bundel tangen` as admitted/attested loans for now; add `ruang singgung pendamping`, `ruang kosinggung`, and `untingan singgung` as retrieval aliases where the backend supports aliases.

## Exact propagation targets

- Glossary rows O011-TERM-0006, O011-TERM-0064, O011-TERM-0066, and O011-TERM-0077: change canonical nominal targets to `ruang singgung`, `vektor singgung`, `garis singgung`, and `vektor singgung` respectively; preserve prior terms as aliases/decision history.
- Add canonical `Paralleltransport` -> `transpor paralel`.
- Re-run a bounded replacement only over admitted Unit 1-6 Indonesian reader sources; do not alter German source text, source identifiers, URLs, hashes, or prose where `tangensial` is the correct adjective.
- Normalize Unit 6 lecture `transport paralel` -> `transpor paralel` and `manifold terdiferensialkan` -> `manifold diferensiabel`.
- Record this as terminology normalization, not as a Brenner source correction; then re-run structural/math preservation checks and PDF/HTML visual QA because the replacements can reflow lines.

## Independent verification and applied result

The main production lane independently reopened the official arXiv result page and confirmed the explicit zero-result response for `"geometri diferensial"`. It also reopened the UIN repository record and visually inspected the public title page, contents page, and the two mathematical appendix pages cited above. The inspection directly confirmed `Ruang Singgung`, `medan vektor singgung`, `tangensial`, `turunan kovarian`, `Koneksi`, `Geodesik`, and `Kelengkungan`. The Universitas Indonesia PDF was independently rendered at PDF pages 21 and 33; its printed pages 12 and 24 directly confirm `manifold diferensiabel`, `transpor paralel`, `tangen`/`tangensial`, and `turunan kovarian`.

The bounded propagation was then applied only to the 26 admitted `*.id.tex` files in Units 1--6. The immediate pre-pass lexical census contained 112 standalone lowercase `tangen` tokens, three suffixed `tangennya` tokens, one `Transport Paralel` heading, one `transport-transport paralel` phrase, six remaining lowercase `transport paralel` phrases, and one `manifold terdiferensialkan` phrase. Nominal tangent-space/vector/line uses became the `singgung` family; field adjectives remained or became `tangensial`; the admitted compound `bundel tangen` remains unchanged; all Indonesian transport prose became `transpor paralel`; the exact media identity `Parallel transport sphere2.svg` and every German link destination remained unchanged.

The first deterministic pass made the intended edits and then stopped at a validator false positive because the protected English media filename legitimately contains lowercase `transport`. The validator was narrowed to the Indonesian phrase rather than weakening source protection. A second review also caught that the mechanical nominal pass had overreached once by changing the expressly retained compound `bundel tangen`; the source and validator were corrected to preserve that exception. The final idempotence pass checks all 26 files and reports zero forbidden forms in `FIELD_TERMINOLOGY_PROPAGATION_U01_U06.json`. These incidents changed no authority identity or media locator and are retained here rather than concealed.

Glossary rows `O011-TERM-0002`, `0003`, `0006`, `0007`, `0009`, `0016`, `0064`, `0066`, `0077`, and `0094` now preserve the chosen primary terms and attested aliases. Unit 6 terms `O011-TERM-0111` through `O011-TERM-0134` were admitted, including the expressly retained `Tangentialbündel` -> `bundel tangen`. The exact production helper is `scripts/normalize_indonesian_field_terms_u01_u06.py`.

The Unit 6 reader wrapper now states the model provenance exactly as `OpenAI Codex gpt-5.6-sol, Ultra` while preserving Holger Brenner's authorship and all human and media credits. The next translation and build verifiers must bind the new target hashes and reflow before this terminology checkpoint can be considered fully closed.
