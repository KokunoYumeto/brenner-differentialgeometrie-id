# Unit 7 Indonesian field-terminology QA research

Date: 2026-08-23  
Scope: bounded comparison only; no translation or glossary mutation in this
research pass.

## Selection result

No genuinely Indonesian-language differential-geometry or smooth-manifold
source with public TeX was found on arXiv. Four exact official API probes were
persisted under `authority/terminology/arxiv-probe/`; each reports
`opensearch:totalResults = 0`. The query URLs, response hashes, and response
timestamps are recorded in
`authority/terminology/TERMINOLOGY_SOURCE_RECEIPT_20260823.json`.

The bounded fallback is:

- Riri Alfakhriati, Jenizon, and Haripamyu, *Sifat-Sifat Fungsi Jarak pada
  Manifold Riemannian*, Jurnal Matematika UNAND 7(2), 2018, pp. 140-148,
  DOI `10.25077/jmu.7.2.140-148.2018`.
- Official landing page:
  <https://jmua.fmipa.unand.ac.id/index.php/jmua/article/view/320>
- Official PDF:
  <https://jmua.fmipa.unand.ac.id/index.php/jmua/article/download/320/311>
- Local PDF: 432,411 bytes, nine A4 pages, SHA-256
  `be4039d4b589f37fe9ae4740269c98473d0d1dba96f3bd88fc8e3d6ce4e5998d`.
- The PDF identifies `TeX` as creator and `MiKTeX pdfTeX-1.40.14` as
  producer. The public article surface exposes the PDF but no source/TeX
  package. The body is plainly Indonesian; the landing page's
  `citation_language=en` value is incorrect and was not used as language
  evidence.

## Direct page evidence

- Physical page 1 / journal page 140 uses **manifold smooth**, **metrik
  Riemannian**, **ruang singgung**, **ruang topologi**, and **Euclidean**.
- Physical page 4 / journal page 143 uses **manifold topologi**, **smooth**,
  **diffeomorfisma**, **chart**, **koordinat lokal**, **koordinat lingkungan**,
  **pemetaan transisi**, **atlas smooth**, and **struktur smooth**.
- Physical page 5 / journal page 144 uses **ruang singgung**, **vektor
  singgung**, **kurva smooth**, **vektor laju**, and **reparameterisasi**.
- Physical page 6 / journal page 145 repeatedly uses **metrik Riemannian** and
  **ruang singgung**, and uses a mixed phrase corresponding to a smooth
  partition of unity.

All nine PDF pages were extracted and visually inspected. The text extraction
is 22,668 bytes with SHA-256
`79501bb9604f3ad02c193a7d8957c53ff7ddb1b5515b831f95b6bc43208e730f`.

## Comparison against the Unit 1-7 edition

The comparison baseline was `00_control/TERMINOLOGY.csv`, 11,474 bytes,
SHA-256
`9f556b553ce9f10453ffa8033c413855acb39253baab00ded1973c9f1a9be1dd`,
plus the lecture and worksheet sources for Units 1-7.

| Concept | Institutional PDF | Current edition | Decision |
|---|---|---|---|
| tangent space | `ruang singgung` | `ruang singgung` | Exact confirmation; keep. |
| tangent vector | `vektor singgung` | `vektor singgung` | Exact confirmation; keep. |
| transition map | `pemetaan transisi` | `pemetaan transisi` | Exact confirmation; keep. |
| local coordinates | `koordinat lokal` / `koordinat lingkungan` | `sistem koordinat lokal` / `koordinat lokal` | Strong confirmation; keep current primary form and record the second as an alias if useful. |
| smooth manifold | `manifold smooth` | `manifold mulus` | Keep natural id-ID `manifold mulus`; record `manifold smooth` only as a field-attested retrieval alias. |
| topological manifold | `manifold topologi` | `manifold topologis` | Keep the grammatically integrated adjectival form `manifold topologis`; record the source form as an alias. |
| chart | `chart` | `peta` | Keep source-faithful Indonesian `peta`, but add `chart` as a retrieval alias and consider `peta (chart)` at the first pedagogical occurrence. Do not replace every occurrence. |
| smooth/differentiable structure | `struktur smooth` | `struktur diferensiabel` | Keep the edition's degree-sensitive distinction; use `mulus` only for smooth/C-infinity. Add the mixed loan form as an alias, not prose. |
| reparametrization | `reparameterisasi` | `reparametrisasi` | Both are intelligible; keep the edition's compact, consistent form and record the other as an alias. |
| Euclidean | `Euclidean` | `Euklides` | Keep the Indonesian exonym `Euklides`; retain `Euclidean` as a search alias. |
| inner product | `hasilkali dalam` | `hasil kali dalam` | Keep the edition's standard separated spelling. |
| second countable | English loan | `basis topologi terhitung` | Keep the translated, explanatory form. |
| velocity vector | `vektor laju` | `kecepatan` / `medan kecepatan` | Keep `kecepatan`; it preserves the speed/velocity distinction more accurately. |
| Riemannian metric/manifold | `metrik Riemannian`; `manifold Riemannian` | not yet present in Units 1-7 or the current terminology ledger | Admit these two attested forms before their first source-order occurrence. |

The paper also contains visibly mixed English-Indonesian constructions and
spelling inconsistencies (`smooth`, `diffeomorfisma`, `terdeferensial`,
`hasilkali`, and `subordinate kesatuan`). It is therefore good evidence of
actual field usage, but it is not a normative spelling authority.

## Recommendation

No bulk correction or propagation through Units 1-7 is justified. The most
important contested choices, `ruang singgung` and `vektor singgung`, receive
direct institutional confirmation. Add field-attested aliases for search and
interoperability, admit `metrik Riemannian` and `manifold Riemannian` before
they first occur, and optionally gloss the first pedagogical occurrence of
`peta` as `peta (chart)`. Preserve the edition's natural Indonesian forms and
degree-sensitive distinction between `diferensiabel` and `mulus`.
