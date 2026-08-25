# Unit 5 cumulative PDF visual QA

Reviewed: 2026-08-22 (Europe/Berlin)

Status: **PASS.** No clipping, overlap, unreadable glyph, broken label, horizontal overflow, margin intrusion, or unintended asymmetric page frame was found.

## Exact artifact and render

- PDF: `output/pdf/geometri-diferensial-manifold-mulus-hingga-unit-05-id.pdf`
- Bytes: 4,385,370
- SHA-256: `44ef3bc7f4c9de8a9ffd3a747ea71c2102de6f26814718492bc63fd40e4af5ce`
- Pages: 86, all A4 and rotation 0
- Render: all 86 pages at 120 dpi to `tmp/pdfs/unit05-render/page-01.png` through `page-86.png`; six ordered contact sheets covering every page were also inspected.

## Inspection result

All rendered pages were reviewed. Pages 73--86, which contain the densest new Unit 5 mathematics, the full worksheet, the sole source-supplied Unit 5 solution, figure list, component-rights inventory, and license close, were additionally inspected at individual full-page scale.

The title, edition statement, contents, unit dividers, headers, footers, page numbers, theorem/proof labels, matrices, fractions, vectors, exercise and point labels, edition notes, supplied solutions, figure list, media-rights statement, and license page render cleanly. The long rotational-surface Hessian on physical page 74 was reflowed by introducing the local abbreviation `s=f(x)^2-z^2>0`; its mathematical value is unchanged, and the rebuilt document has no overfull box. The German labels retained in the canonical Unit 5 source figure remain legible, and the Indonesian caption describes the principal-curvature planes, normal vector, and tangent plane.

Sparse pages occur only at deliberate terminal or structural boundaries: centered title/unit dividers and the ends of lectures, worksheets, solution sections, the figure list, rights inventory, and license section. They are not remnants of the former narrow or off-center legacy frame. Ordinary content pages use the full wrapper-owned text width and have symmetric horizontal placement.

## Programmatic margin cross-check

The 86 individual PNGs are uniformly 993 x 1,404 pixels. A grayscale ink-bounds pass at threshold 245 found:

- minimum left ink margin: 103 px;
- minimum right ink margin: 102 px;
- minimum top ink margin: 57 px;
- minimum bottom ink margin: 59 px;
- pages with ink within 20 px of an edge: 0;
- pages with left/right ink-margin difference greater than 80 px: 0.

This cross-check supports, but does not replace, the all-page visual inspection. The wrapper-owned centered A4 geometry with 22 mm horizontal margins passes.
