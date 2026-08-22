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

## Unit 2 exact closure

The Unit 2 roots are Lecture 2 pageid/revision `142546 / 893641` and Worksheet 2 `142636 / 907117`; their `/latex` surfaces are `142576 / 807125` and `142666 / 807094`. Because those `/latex` pages contain only the `{{Latex}}` invocation, the frozen official `expandtemplates` responses and sanitized German TeX witnesses are also part of authority. The lecture witness is 22,206 bytes, SHA-256 `f488d809e7d9490c40099d90c2abed2cc8bea39f11923a8d525e6302f3be470a`; the worksheet witness is 10,171 bytes, SHA-256 `c645aacb16233d832b492315379b0251c33fa52db6b2e7ac24be4ecc9600d3ad`. Exact API identities, response hashes, and sanitation receipts are in `qa/unit-02/AUTHORITY_PREFLIGHT.json` and `.md`.

Worksheet 2 contains 19 exercises and exactly five source-supplied solutions, for exercises 1, 2, 7, 12, and 13. Their expanded German TeX SHA-256 values are respectively `6dcc38f066a8350fdba67145857c168e1b6ca532c07af0a8f34ee2b954ad9432`, `a92e556f50d2216192fc61703eea4bae3d233ab632c8eedb19bd35dec2ed89b0`, `90d9007e6a313dcbc4614045f0831b826f7a9af82897e17a36fbce08088ef92b`, `3191adb6fbfaf1be11c0e7a061468a4fd6fe9235cd0dea40771ec97bd10f970f`, and `6896eb6a4a6f4c25bcfaab674847dcd78bc079cfd6c58b3b8542c5c220d85e7b`. The official current-revision query records the other 14 candidate solution pages as missing; the edition does not imply a larger solution layer.

Lecture 2 uses exactly two media files, while its worksheet and five solutions use none. `Integral apl rot obsah1.svg` is 8,098 bytes, SHA-256 `3dc950fd001c3a2e3ef095dcceac915f4701e990ecf513cf314eaef8a8f86dd1`; `Hyperboloid1.png` is 278,393 bytes, SHA-256 `4c813998156ef1961fa557d3a7c356d737c47291d36159baa955f170e500979b`. Both are public-domain components and retain their Commons source pages and creator credit in `qa/unit-02_media.json` and the reader.

## Build boundary

The official `/latex` surface is an expanded body fragment, not a self-contained TeX project. It contains HTML line-break artifacts and course-specific macros. The published preamble recipe has personal paths and legacy assumptions. Production therefore uses:

1. the exact JSON expansion as evidence;
2. deterministic sanitation (`<br>` to LF, wrapper-tag removal, UTF-8/LF normalization);
3. a versioned local macro compatibility layer;
4. exact local media assets;
5. an explicitly recorded TeX engine and command.

The official Electron lecture render is a ten-page A4 tagged PDF and is legible, but it contains edit-URL headings, navigation/footer material, and an almost empty final page. It is not the layout target.

## Unit 3 exact closure

The Unit 3 roots are Lecture 3 pageid/revision `142547 / 1020016` and Worksheet 3 `142637 / 894109`; their `/latex` surfaces are `142577 / 807136` and `142667 / 807105`. The frozen official expansion responses yield a 28,482-byte lecture witness with SHA-256 `c6fa222d45a2abaaa121fabbf68a76ab478d9ede7dd14f370d8e58d40887c25a` and a 9,997-byte worksheet witness with SHA-256 `8dded699ee9337ebdc4cb76a9373fb8e2f6a5df94c6048c3deaaaeaccb88bac7`. Exact API identities, response hashes, sanitation receipts, root witnesses, and verification results are in `qa/unit-03/AUTHORITY_PREFLIGHT.json`, `.md`, and `AUTHORITY_PREFLIGHT_VERIFY.json`.

Worksheet 3 contains 21 exercises: 16 practice exercises and five graded exercises worth `2, 2, 4, 4, 4` points, for 16 points total. Every hint field is blank. Exactly two source-supplied solutions exist, for Exercises 7 and 16. Their pageid/revision identities are `151168 / 1095913` and `151178 / 1095920`; their expanded German TeX SHA-256 values are `7e3437274bf4f79b6a3fa719876b09fdbcee4e10523a215e9e6f4ecb566cdb85` and `ed49f1889840b8352f634ef01400301849f8303ec27a2a38b334b744ae5e5951`. The other 19 candidate solution pages were queried and are absent; no larger solution layer is implied.

Unit 3 uses exactly three admitted Commons files. `Parabola circle.svg` is 19,469 bytes, SHA-256 `186a981781924575a5e517d83d8ab5bfb829125d0a86edc664a41a589bcfca83`, credited to IkamusumeFan under CC BY-SA 4.0. `Euler spiral.svg` is 31,848 bytes, SHA-256 `886d55edfa0fa21ac992ede928cfec4f816742a16b29709ea093113b29e410b9`, credited to AdiJapan under CC BY-SA 3.0. `Evolute-parab.svg` is 44,890 bytes, SHA-256 `851a909594c64be31477e391ea9b45e890305ea62e32e29a1d04bc66cf497db1`, credited to Ag2gaeh under CC BY-SA 4.0. Exact source/derivative identities and license URLs pass in `qa/unit-03_media.json`.

## Known upstream PDF incompleteness

The official Commons category contains only `Differentialgeometrie (Osnabrück 2023)Vorlesung4.pdf`. The other expected lecture and worksheet links are absent. A release must not claim a complete official PDF set.
