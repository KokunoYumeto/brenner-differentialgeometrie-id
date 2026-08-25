# Visual QA — cumulative reader through Unit 7

Status: PASS with the documented structural-tagging limitation.

The settled PDF is `output/pdf/geometri-diferensial-manifold-mulus-hingga-unit-07-id.pdf`,
117 pages, 4,950,232 bytes, SHA-256
`8c2cf76230b45d66a8236c0cd92a048809ff5ec0cce343132dd902684cb05ec6`.
Two clean three-pass build cycles produced that same byte identity. Every page
uses A4 media and the wrapper-owned centered layout; no clipping, overlap,
black-square glyph failures, or out-of-frame content was observed.

Sampled rendered pages (110 dpi) were inspected at the title, unit transition,
worksheet, Unit 7 lecture, Unit 7 worksheet, and final-license boundaries:
physical pages 1, 2, 50, 79, 98, 99, 105, 109, and 117. The sampled pages
show stable 22 mm wrapper margins, readable formulas, correctly placed figures,
and centered reader content. The Unit 7 solution-13 surface preserves both
clickable Commons GIF links.

Independent structural evidence is in `qa/unit-07/PDF_BOUNDARY_QA.json`:
all 117 pages yield extractable text through pypdf and pdfplumber, all 28
unique embedded fonts have ToUnicode maps, all page boxes are A4, rotations are
zero, and the PDF language is `id-ID`. The PDF is not structurally tagged;
semantic HTML remains the planned accessibility surface and is not claimed in
this partial checkpoint.

Model provenance is disclosed as **OpenAI Codex gpt-5.6-sol, Ultra** under user
direction. Source authors, page contributors, and media creators remain
credited in the reader and rights manifests.
