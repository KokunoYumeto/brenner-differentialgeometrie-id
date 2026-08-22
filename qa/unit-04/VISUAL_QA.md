# Unit 4 cumulative PDF visual QA

Reviewed: 2026-08-22 (Europe/Berlin)

Status: **PASS.** No clipping, overlap, unreadable glyph, broken label, horizontal overflow, margin intrusion, or unintended asymmetric page frame was found.

## Exact artifact and render

- PDF: `output/pdf/geometri-diferensial-manifold-mulus-hingga-unit-04-id.pdf`
- Bytes: 3,666,928
- SHA-256: `04f84c2d7abdc721cb0ebafcd4e39c230a01faf60665f84d5e7124bf2574319b`
- Pages: 72, all A4 and rotation 0
- Render: all 72 pages at 120 dpi to `tmp/pdfs/unit04-final-visual-qa-04f84c2d/page-01.png` through `page-72.png`; eighteen four-page contact sheets were also inspected.

## Inspection result

All rendered pages were reviewed, with individual full-page inspection of the dense Unit 4 lecture and worksheet span. The title, edition statement, contents, unit dividers, headers, footers, page numbers, theorem/proof labels, matrices, fractions, vectors, exercise and point labels, edition notes, supplied solutions, figure list, media-rights statement, and license page render cleanly.

The two marker-scoped reflows in the Unit 4 hyperboloid calculation keep the long basis-action and eigenvector chains inside the text block while leaving every mathematical token unchanged. The graph shape-operator correction and both supplied solution repairs are legible at normal page scale. Unit 4's zero-media statement is visible and correctly separated from the cumulative rights inventory.

Sparse pages occur only at deliberate terminal or structural boundaries: centered title/unit dividers and the ends of lectures, worksheets, solution sections, the figure list, rights inventory, and license section. They are not remnants of the former narrow or off-center legacy frame. In particular, ordinary content pages use the full wrapper-owned text width and have symmetric horizontal placement.

## Programmatic margin cross-check

The 72 individual PNGs are uniformly 993 x 1,404 pixels. A grayscale ink-bounds pass at threshold 245 found:

- minimum left ink margin: 103 px;
- minimum right ink margin: 102 px;
- minimum top ink margin: 57 px;
- minimum bottom ink margin: 59 px;
- pages with ink within 20 px of an edge: 0;
- pages with left/right ink-margin difference greater than 80 px: 0.

This cross-check supports, but does not replace, the all-page visual inspection. The wrapper-owned centered A4 geometry with 22 mm horizontal margins passes.
