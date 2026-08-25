# Unit 6 cumulative PDF visual QA

Date: 2026-08-22

## Settled reader

- Artifact: `output/pdf/geometri-diferensial-manifold-mulus-hingga-unit-06-id.pdf`
- Size: 4,765,606 bytes
- SHA-256: `40bf26d196ff04c38c6c99e8e9669a86bb5e6d31124b904b7ad154e7948cdec1`
- Extent: 105 A4 pages, wrapper-owned 22 mm margins, centered text block.
- Determinism: two clean three-pass build cycles are byte-identical; the final
  pass reports no overfull or underfull boxes, warnings, undefined references,
  duplicate destinations, fatal errors, or build errors.

## Render and inspection

The settled PDF was rendered in full with Poppler at 110 dpi. All 105 final
page PNGs were inspected through seven regenerated 4-by-4 contact sheets;
Unit 6 pages and every page touched by a repair were also inspected at original
render resolution. The UTF-8 sorted page-name/byte-count/SHA-256 manifest
serialization is 8,898 bytes with SHA-256
`b803726d8c2f45b57054ac682d081f9c2e0fc79e80459706edc64db4a0fcc304`.

The review covered title and provenance pages, contents and page labels,
chapter/worksheet transitions, all figures, dense formula pages, long proofs,
exercise and solution transitions, figure list, media-rights pages, and the
terminal license page. Page 105 is intentionally sparse: it is the terminal
license page rather than missing content.

## Defects caught and closed

1. The first Unit 6 render exposed a long corrected Leibniz derivation beyond
   the right margin. Its two longest right-hand sides were reflowed onto
   aligned continuation lines without changing any term or equality. The
   final page 86 render is fully inside the text block.
2. Extracted-text and rendered-page review found ten definition-reference
   macros consuming the next prose token because their empty third argument
   was absent. Restoring the source macro arity removed concatenations such as
   `geodesiktepat` and `paralelsepanjang`.
3. The final all-page pass found eight periods or commas held outside the
   terminal arguments of mapping/comparison macros. They were moved into the
   macros' terminal punctuation arguments. Final pages 85, 88, 89, and 91
   confirm that the punctuation remains attached to its display and no orphan
   punctuation line remains.
4. The bottom of page 103 was checked independently: the page number does not
   collide with the media-attribution text. Figures and captions remain sharp,
   centered, and within the margins.

## Verdict

Pass. The settled render has no clipping, overlap, broken glyph, unreadable
formula, miscentered content block, or unexplained blank page. The known
accessibility limitation is structural rather than visual: the PDF is not
tagged. It does carry `id-ID`, embedded fonts with ToUnicode maps, and
extractable text on every page; semantic HTML remains the required structured
accessibility surface for the complete edition.
