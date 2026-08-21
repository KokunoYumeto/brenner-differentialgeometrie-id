# Authority freeze

## Primary authority

- Author-controlled teaching index: <https://de.wikiversity.org/wiki/Benutzer:Holger_Brenner/Lehre>
- Course: <https://de.wikiversity.org/wiki/Kurs:Differentialgeometrie_(Osnabr%C3%BCck_2023)>
- Course pageid/revision: 142521 / 889544.
- Course revision timestamp: 2023-03-07T11:39:09Z.
- Course MediaWiki SHA-1: `e274ea4f0ae092736a5df23dfd3bb744184a9f2d`.

The course page and its 58 numbered teaching pages are composition layers. Their mathematical content is transcluded from shared semantic pages. The frozen authority is therefore the recursive current-revision export, not only the course prefix.

## Frozen files

| File | Purpose | Bytes | SHA-256 |
|---|---|---:|---|
| `authority/mediawiki/brenner_course_recursive_current.xml` | 2,715-page current-revision Special:Export closure | 3,538,709 | `6b96c90a8b1e52fac57c735f28d0babc56a95050ca015075b755179270d75d14` |
| `authority/mediawiki/brenner_latex_kontrolle_recursive_current.xml` | 2,866-page recursive closure for all `/latex` and `/kontrolle` surfaces plus the official preamble | 3,722,387 | `4c489c44a3d856304a8724e04c1007aa8b18d0e7099257aaf711a084eab0de7c` |
| `authority/brenner_selected_root_revisions.csv` | Exact 59-row course/lecture/worksheet revision cursor | 15,237 | `64cf91594907db45355e64fb512fb14092e15218c74847a8f60fe884a5284fc8` |
| `authority/brenner_selected_surface_revisions.csv` | Exact 117-row `/latex`, `/kontrolle`, and preamble revision cursor | 31,799 | `9a3a6b7dc08cc022803dad24e959365d67810d4da87a8bc4385c601db9d4bd52` |
| `authority/brenner_media_rights_manifest.csv` | Whole-course 36-row Commons media rights inventory | 25,588 | `fc3cc283b23c9027b181c0e3822cf0f26eb58037fe3cbd23e4c7eaae1d05ec57` |
| `authority/brenner_94_link_classification.csv` | Classification of 36 real images and 58 per-unit PDF links | 27,170 | `039a5ec757bde1179de78d7b27c398d5fe06c622859630ffc0ea9e9f16d7919b` |
| `authority/brenner_export_and_title_inventory_receipt.txt` | Exact export/API recipes, title inventory, and closure counts | 15,286 | `6ac0a458c9b674a8b84c86f75dd68a5a52b4b733c394bd03aff1270af269a289` |
| `authority/exports/lecture01_latex_expand.json` | Official expanded LaTeX response for Lecture 1 | 34,557 | `d14726deb0a402e35135e956281940bcfe23b019d38b94fca2087b75c3016801` |
| `authority/exports/worksheet01_latex_expand.json` | Official expanded LaTeX response for Worksheet 1 | 17,573 | `825fb50db84653307ae7b904988a51254b8f195be1685a2a68c1a4431e222410` |
| `authority/mediawiki/worksheet01_exercise01_solution_revid1111802.utf8.b64` | Lossless UTF-8 source bytes for the one supplied Unit 1 solution, base64-wrapped for transport | 3,521 | `b85f6e5009e304baf4d7a3948428494e984d0129160230d03b95a5438268947d` |
| `authority/expanded/worksheet01_exercise01_solution_source.de.tex` | Deterministically derived German LaTeX witness for that solution | 2,539 | `620804c6a0464a748f9e6923c779d55a4fd5108cfd1236e6d3ac383a3eaff407` |
| `authority/pdf/lecture01_electron_current.pdf` | Official Electron render witness, not production master | 865,064 | `87208550af86a83004c95d9d4b004d2d8ac4973da7962f5ed7b26bde933f0ee3` |

Export timestamp: 2026-08-21T09:52:04Z. Namespace counts: main 2,151; template 197; course 367. All 59 requested root pages are present; every exported page has revision text. The canonical internal revision-set digest is `4810e9c13e352db58d7ceb5495c1cf86cb991d2193eaf6a344a48799e7ab0f71`.

The second recursive export has revision-set digest `e274c45e0496b3e842d7aa2a4f7c68005f7a6b58c6bcb3ce1c6763cdefb0da28`. The supplied Worksheet 1 solution is pageid 131353, revision 1111802, timestamp 2026-08-15T16:41:12Z. Decoding the frozen base64 witness yields 2,638 bytes, SHA-256 `b07aac01b6f803481fab9b5331e19480fb9bf0058597159b6152c65c7bc955ce`, and SHA-1 `09f1f40080836e9c7f41b5851209d9dff07ad8cb`.

## Rights boundary

Wikiversity text is reused through the current CC BY-SA 4.0 path, with source URL, permanent revision, and page-history attribution retained. Wikimedia media do not inherit that blanket text license: each image must be admitted from its file-description metadata and carry creator, source, exact license, revision, size, and hash. No ambiguous or unavailable media may be silently copied.

The exact Unit 1 media closure is local under `authority/media/`: four canonical files with their Wikimedia SHA-1, byte count, SHA-256, creator, license, and derivative hashes recorded in `qa/unit-01_media.json`. The four source licenses are CC BY 3.0, CC BY-SA 4.0 (two files), and CC BY-SA 3.0. No whole-course blanket media license is asserted.

## Build boundary

The official `/latex` surface is an expanded body fragment, not a self-contained TeX project. It contains HTML line-break artifacts and course-specific macros. The published preamble recipe has personal paths and legacy assumptions. Production therefore uses:

1. the exact JSON expansion as evidence;
2. deterministic sanitation (`<br>` to LF, wrapper-tag removal, UTF-8/LF normalization);
3. a versioned local macro compatibility layer;
4. exact local media assets;
5. an explicitly recorded TeX engine and command.

The official Electron lecture render is a ten-page A4 tagged PDF and is legible, but it contains edit-URL headings, navigation/footer material, and an almost empty final page. It is not the layout target.

## Known upstream PDF incompleteness

The official Commons category contains only `Differentialgeometrie (Osnabrück 2023)Vorlesung4.pdf`. The other expected lecture and worksheet links are absent. A release must not claim a complete official PDF set.
