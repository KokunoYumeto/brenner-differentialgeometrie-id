# Indonesian field-terminology QA decision

Date: 2026-08-23  
Gate: passed  
Propagation scope: glossary notes and forward Unit 8 terminology only; no bulk
reader-text rewrite

## Evidence boundary

The official arXiv API returned zero results for four bounded searches for an
Indonesian-language smooth-manifold or differential-geometry source with TeX.
The admitted fallback is Riri Alfakhriati, Jenizon, and Haripamyu,
*Sifat-Sifat Fungsi Jarak pada Manifold Riemannian*, Jurnal Matematika UNAND
7(2), 2018, pp. 140--148, DOI `10.25077/jmu.7.2.140-148.2018`.

- source receipt: `authority/terminology/TERMINOLOGY_SOURCE_RECEIPT_20260823.json`,
  4,237 bytes, SHA-256
  `b4f429e8cf2c0ec27541953c0b2822d5d970468e6e4ad8e77c215a4d18a42ff0`;
- official PDF witness: 432,411 bytes, nine A4 pages, SHA-256
  `be4039d4b589f37fe9ae4740269c98473d0d1dba96f3bd88fc8e3d6ce4e5998d`;
- extracted text witness: 22,668 bytes, SHA-256
  `79501bb9604f3ad02c193a7d8957c53ff7ddb1b5515b831f95b6bc43208e730f`;
- research report: `qa/unit-07/TERMINOLOGY_QA_RESEARCH_20260823.md`,
  5,547 bytes, SHA-256
  `e18f20c5174b776fd52683375823a5709c7f44f4f1f7907f71f45be5f76e45e6`.

The fallback is evidence of actual Indonesian mathematical usage, not a
normative spelling authority: its prose mixes English loans and Indonesian
forms and contains visible spelling inconsistencies.

## Decision and propagation

No reader-facing correction is required in Units 1--7. Their primary forms
`ruang singgung`, `vektor singgung`, `pemetaan transisi`, `koordinat lokal`,
`manifold mulus`, `manifold topologis`, `struktur diferensiabel`,
`reparametrisasi`, `Euklides`, and `hasil kali dalam` are mathematically sound
and internally consistent. In particular, the institutional source directly
confirms `ruang singgung` and `vektor singgung`.

The terminology ledger was extended without changing admitted reader prose:

- field-attested retrieval aliases were recorded for `manifold smooth`,
  `Euclidean`, and `reparameterisasi`;
- Unit 8 source-order entries were admitted for `manifold topologis`, `ruang
  topologis`, `peta`, `citra peta`, `domain peta`, and `koordinat lokal`;
- `manifold topologi`, `ruang topologi`, `chart`, and `koordinat lingkungan`
  are retrieval aliases, not replacements for the primary reader forms;
- `metrik Riemannian` and `manifold Riemannian` are accepted future forms but
  will be entered only immediately before their first actual source-order
  occurrence.

The resulting `00_control/TERMINOLOGY.csv` has 140 admitted terms, 12,254
bytes, SHA-256
`c160ea6a34b8292b2f0809ca6103a693e28119f4b9809c05263704d7d1c343ba`.
Because the propagation changes only retrieval notes and newly needed Unit 8
terms, rebuilding or republishing the unchanged Unit 1--7 reader would add no
value. Translation may proceed from the already frozen Unit 8 authority.
