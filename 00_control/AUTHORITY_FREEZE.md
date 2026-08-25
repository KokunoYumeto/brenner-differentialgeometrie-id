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

## Unit 4 exact closure

The Unit 4 roots are Lecture 4 pageid/revision `142548 / 893683` and Worksheet 4 `142638 / 1010985`; their `/latex` surfaces are `142578 / 807138` and `142668 / 807107`. A bounded live official-API check at `2026-08-22T07:25:23Z` confirms that all four frozen page IDs, revision IDs, `lastrevid` values, and timestamps remain current. The exact result is `qa/unit-04/CURRENT_REVISION_CHECK.json`, 3,063 bytes, SHA-256 `357a36764e1f2b397b3130c482c85ddd592cf874cbb3db5028053d1e354066ab`.

The frozen official expansion responses yield a 26,932-byte lecture witness with SHA-256 `610c85e2cb9838a2ce1deb488ceca6cb7d2ee2ab47f1e657d5df7488796f8402` and an 11,052-byte worksheet witness with SHA-256 `81f8d9667581e0e6507dd1684b136c23f3352d1cabf2e8c4013daeb0a312cd00`. Root and `/latex` wikitext are retained as exact UTF-8 base64, normalized readable witnesses, and revision metadata. Exact response, request, and sanitation identities are in `qa/unit-04/AUTHORITY_PREFLIGHT.json` (26,771 bytes; SHA-256 `0a2f455c500cad070fe8d5970786189840fd90cbb856101c7cd177de0bdefa36`) and its freshly recomputed offline verification receipt (517 bytes; SHA-256 `3dbcb88246dff59e786257882e671072588bd50a4fd98bfb0ba7a2b374700893`).

Worksheet 4 contains 15 exercises: 11 practice and four graded exercises worth `4, 5, 4, 6` points, for 19 points total. Every hint field is blank. Exactly two current source-supplied solutions exist, for Exercises 7 and 10. Their pageid/revision identities are `152876 / 1094221` and `151124 / 1094288`; their expanded German TeX witnesses are respectively 2,623 bytes with SHA-256 `a0df2279b1dbae5bff1a4e50385349080bd8734e20d1a6edec83e528045dc63e` and 2,633 bytes with SHA-256 `76a2f5db7eb835b19b924418ae2c1b0cfbcd8cd2d5acc387f695f71cbb069a35`. The other 13 conventional `/Lösung` candidates were queried and are absent. The full closure is `qa/unit-04/solution_closure.json`, 13,097 bytes, SHA-256 `cbb81ccdd6115044d52b4dc61013b61bc61a38ee5565cb81f58674555548d5f7`.

The lecture, worksheet, and both supplied solutions contain no `\includegraphics` or `\bildlizenz` occurrence, so Unit 4's mathematical-media set is exactly empty. This zero-asset closure is explicit in `qa/unit-04/media_closure.json`, 1,827 bytes, SHA-256 `acf2a10f7daab6d4d4b62e6a9735041d3b1e519b9139f93ee815324e4a9ee289`.

The one existing official course PDF is retained only as a local, unredistributed numbering/order witness, never as editable authority, production master, derivative input, publication file, or release asset: Commons pageid/revision `130922930 / 1003382720`, file timestamp `2023-04-20T19:44:46Z`, 210,221 bytes, Commons SHA-1 `610c2216778a3121aee356f992560cd55ed90690`, and SHA-256 `65ee310d19704bdbbb7f981f821901f96b166ceac416ad7cc063ae737894571d`. Current Commons structured metadata says CC BY-SA 4.0 and artist `User:Bocardodarapti`; the PDF's internal page 9 says Holger Brenner alias Bocardodarapti and CC-by-sa 3.0. These unresolved file-specific rights signals are preserved without merging them into a license claim. The PDF must not be redistributed. Exact restrictions are in `qa/unit-04/OFFICIAL_PDF_WITNESS.json` (947 bytes; SHA-256 `87422827230c2ce2faac3f957999b56c72cc1ea1cc11094652c800a44efbf05b`) and `qa/unit-04/OFFICIAL_PDF_STRUCTURAL_VISUAL_QA.json` (2,310 bytes; SHA-256 `b5395fd883a60fc6bb99f4c2e1050131ad59a18475c3626163b1dfa87a0f5cc5`). The PDF has nine untagged US Letter pages; pages 1-7 carry the lecture, page 8 is blank, and page 9 is the rights index.

The frozen source also exposes six anomaly groups that must not be silently normalized: the malformed cone curve in Exercise 2; the graph shape-operator/second-fundamental-form conflation in Lecture Lemma 4.8; insufficient `C^1` hypotheses in Exercises 6 and 9; the unfinished and algebraically damaged supplied Exercise 7 solution; the omitted `L=-DN` sign and incomplete eigenbasis in the supplied Exercise 10 solution; and two literal lecture defects. Exact mathematical evidence is in `qa/unit-04/AUTHORITY_ANOMALIES.md`, 4,615 bytes, SHA-256 `dab36b02cc0f1ab9cf2177a1d615709851f2a869c35cc01e5f8e127ef36f7bd1`. Authority closure passes; target correction and any original completion remain separate adverse-ledger decisions.

## Unit 5 exact closure

The Unit 5 roots are Lecture 5 pageid/revision `142549 / 894651` and Worksheet 5 `142639 / 894758`; their `/latex` surfaces are `142579 / 807139` and `142669 / 807108`. A bounded official-API check at `2026-08-22T15:14:07Z` confirms that all four frozen page IDs, revision IDs, `lastrevid` values, timestamps, and MediaWiki SHA-1 values remain current. The exact result is `qa/unit-05/CURRENT_REVISION_CHECK.json`, 3,060 bytes, SHA-256 `75cec505bb1fbdee2d40295e6ec85a8181dba18c99993134dd5064308086d562`.

The frozen official expansion responses yield a 23,357-byte lecture witness with SHA-256 `d4d3549c402338aa7f65973fc3a6cb57822e9a75277d48ce1177672d73bc01be` and a 10,542-byte worksheet witness with SHA-256 `88223af26d835e5be221b05a34fee7b374729af095ff7e053119761c6d09ed13`. Root and `/latex` witnesses, request receipts, expansion responses, exact UTF-8 bytes, and sanitation evidence are bound by `qa/unit-05/AUTHORITY_PREFLIGHT.json`, 26,812 bytes, SHA-256 `3cd23e9c6ef0a74309a680c5f754817c607f533ed935b960e0def949fd12184c`, and its offline verifier receipt, 509 bytes, SHA-256 `576c8500fd27dac80d6163b194a7c772fdd4f297b0f6c9c5753dc1f068690ef6`.

Worksheet 5 contains 15 exercises: ten practice and five graded exercises worth `4`, `4`, `6`, `6 (2+2+2)`, and `2` points, for 22 points total. Exercise 13 alone carries a nonblank source hint. Exactly one current source-supplied solution exists, for Exercise 1, pageid/revision `151137 / 1095881`; its expanded German TeX witness is 2,033 bytes with SHA-256 `c2ae2ee20c93daf8bd13b6491e2a8180adb2f07fcb934b968ac384e11ec46790`. The other 14 conventional solution candidates were queried and are absent. The full closure is `qa/unit-05/solution_closure.json`, 10,393 bytes, SHA-256 `3e25d0f61e01cb1e73f562ade62770eab45112dcc5baac4dd415de5b8b41b032`.

Unit 5 has exactly one mathematical-media occurrence: `Minimal surface curvature planes-de.svg`, 50,805 bytes, SHA-256 `c3048459dcf36445b38c5b734eee1febd21215bb08aeba9675cd1e5745cde873`, Commons page/revision `122989228 / 796566416`, credited to Eric Gaba (Sting) and licensed CC BY-SA 3.0. The deterministic print derivative is 666,377 bytes with SHA-256 `fbf3bcf3d6cd43563e765fddf8657b8174034447e70033a06f2dd0df128f0533`. Exact rights, source URLs, attribution, current Commons metadata, derivative command, bytes, and hashes pass in `qa/unit-05_media.json`, 2,667 bytes, SHA-256 `b91aa704e8088727de25b3ecb537be693d36aa307d3de766ece20d47907584e8`.
