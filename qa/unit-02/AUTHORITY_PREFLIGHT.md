# Unit 2 authority preflight

Status: **PASS** at `2026-08-22T03:49:56Z`. This checkpoint freezes authority and source closure only; no Unit 2 translation or build has started.

## Authority chain

The root identities come from `authority/brenner_selected_root_revisions.csv`, bound to `authority/mediawiki/brenner_course_recursive_current.xml` (3,538,709 bytes; SHA-256 `6b96c90a8b1e52fac57c735f28d0babc56a95050ca015075b755179270d75d14`). The `/latex` surface identities come from `authority/brenner_selected_surface_revisions.csv`, bound to `authority/mediawiki/brenner_latex_kontrolle_recursive_current.xml` (3,722,387 bytes; SHA-256 `4c489c44a3d856304a8724e04c1007aa8b18d0e7099257aaf711a084eab0de7c`).

| Surface | Page ID | Revision | Revision time (UTC) | MediaWiki SHA-1 (base 36) | UTF-8 bytes |
|---|---:|---:|---|---|---:|
| `.../Vorlesung 2` | 142546 | 893641 | 2023-04-13T16:07:37Z | `p58d9syrhxwk61sqiu43xxqt99rmgua` | 709 |
| `.../Arbeitsblatt 2` | 142636 | 907117 | 2023-07-18T12:00:58Z | `rsw82cuta1d9miyozhkf0ds94jdwc5q` | 2,097 |
| `.../Vorlesung 2/latex` | 142576 | 807125 | 2022-09-18T10:00:20Z | `3e3nqvm6nsvokcc33v86ivll7ce6lru` | 9 |
| `.../Arbeitsblatt 2/latex` | 142666 | 807094 | 2022-09-18T09:55:09Z | `3e3nqvm6nsvokcc33v86ivll7ce6lru` | 9 |

The two nine-byte `/latex` pages are only `{{Latex}}` surfaces; their revision IDs do not by themselves freeze transcluded mathematics. Therefore the authoritative expanded responses are also preserved byte-for-byte from the official German Wikiversity API with `action=expandtemplates`, `format=json`, `formatversion=2`, `prop=wikitext|categories|modules|jsconfigvars`, the exact surface title, and `text={{Latex}}`.

| Source | Frozen API response | Sanitized German TeX |
|---|---|---|
| Lecture 2 | `authority/exports/lecture02_latex_expand.json`: 27,945 bytes; SHA-256 `08a21182f04117a8839ccdea429b986a21aff4763b6a3fabcb2ab5faa3d0d21e` | `authority/expanded/lecture02_source.de.tex`: 22,206 bytes; SHA-256 `f488d809e7d9490c40099d90c2abed2cc8bea39f11923a8d525e6302f3be470a` |
| Worksheet 2 | `authority/exports/worksheet02_latex_expand.json`: 14,036 bytes; SHA-256 `81f0f3d88687a255fbe828ff70f78c15aa7686520b39728598518bc03a724ed2` | `authority/expanded/worksheet02_source.de.tex`: 10,171 bytes; SHA-256 `c645aacb16233d832b492315379b0251c33fa52db6b2e7ac24be4ecc9600d3ad` |

Both were transformed only by the existing deterministic `scripts/sanitize_brenner_expand.py`. The receipts are `lecture02_sanitize.json` (SHA-256 `cf5e8040c223c9f981548b795aff52c19116a6d5c2cd77dbc975c57e4ae702e7`) and `worksheet02_sanitize.json` (SHA-256 `b6437a7d46a411f7dba7099caab707db4196bdc9034a59105068b844ef5cbace`). UTF-8, residual-HTML, replacement-character, input-hash, and output-hash checks pass.

## Exercise and solution closure

Worksheet 2 contains 19 exercises. Its expanded source contains five and only five `\inputaufgabegibtloesung` macros: exercises **1, 2, 7, 12, and 13**. The frozen recursive XML contains no `/Lösung` pages, so all 19 exact candidate titles were queried through the current official revisions API. The result is 5 existing pages and 14 missing pages, exactly matching the five solution-bearing macros.

| Exercise | Solution page ID / revision | Revision time (UTC) | MediaWiki SHA-1 | Exact source SHA-256 | Expanded TeX SHA-256 |
|---:|---|---|---|---|---|
| 1 | 139491 / 1090802 | 2026-05-31T14:13:03Z | `b186a92ddf2deeee8de0a49f21e1acae5e9da1c6` | `f6787c5b9547ac189e011cb8b1f50ecad82247095e086138bd45e0a4f06647bb` | `6dcc38f066a8350fdba67145857c168e1b6ca532c07af0a8f34ee2b954ad9432` |
| 2 | 120435 / 1089268 | 2026-05-31T10:02:12Z | `d684028bf2c688772acfeb0f37a42bd274ff6e70` | `0bdd1cde6d1d0dc74757aa824634d10b6b4bf413efb4431538b7d9bac2b6f06c` | `a92e556f50d2216192fc61703eea4bae3d233ab632c8eedb19bd35dec2ed89b0` |
| 7 | 152882 / 1094222 | 2026-06-14T15:20:09Z | `763b0e249dc4092c784d70c9547217f198a3c370` | `dbe0990deca042c24dda79891b6ccc66b57723be69023687cacd7ffa206f6988` | `90d9007e6a313dcbc4614045f0831b826f7a9af82897e17a36fbce08088ef92b` |
| 12 | 152865 / 1095926 | 2026-06-15T07:27:34Z | `c7039038dd076b610eac80b920127b8502dc6dad` | `78284fe9d10f41f0503cba0d3295c761d5d168d8de06505226909c7242d4993a` | `3191adb6fbfaf1be11c0e7a061468a4fd6fe9235cd0dea40771ec97bd10f970f` |
| 13 | 152873 / 1094182 | 2026-06-14T15:10:42Z | `fde8f63ad5da4cb7f0e6f0e1a788f2e3102a076e` | `1050f074ecb58b7a8211d756b7fcd6fe4a0a4db6a024083c31ca3c5469e9fd50` | `6896eb6a4a6f4c25bcfaab674847dcd78bc079cfd6c58b3b8542c5c220d85e7b` |

For each supplied solution, `authority/mediawiki/` contains revision metadata, an exact UTF-8 base64 witness, and a readable `.wiki` witness. `authority/exports/` contains the frozen `/Lösung/latex` expansion response; `authority/expanded/` contains its sanitized German TeX; `qa/unit-02/` contains the individual sanitation receipt. `solution_closure.json` inventories all 19 exercises and binds every file. No additional solution-bearing macro exists.

## Media closure

Lecture 2 uses exactly two images; Worksheet 2 and all five supplied solutions use none. Current official imageinfo agrees with the existing per-file rights manifest, and the exact binaries are now frozen under `authority/media/`.

| File | Bytes | Commons SHA-1 | SHA-256 | License |
|---|---:|---|---|---|
| `Integral apl rot obsah1.svg` | 8,098 | `6acbfaacc41c1fb9c8500bbd1aef86d7fd230208` | `3dc950fd001c3a2e3ef095dcceac915f4701e990ecf513cf314eaef8a8f86dd1` | Public domain |
| `Hyperboloid1.png` | 278,393 | `8dd605e11b3b6cb2597dbdfaaac4857e979ceaaa` | `4c813998156ef1961fa557d3a7c356d737c47291d36159baa955f170e500979b` | Public domain |

The saved imageinfo response is `authority/mediawiki/unit02_media_imageinfo_current.json`; the saved solution-query response is `authority/mediawiki/unit02_solution_pages_current.json`.

## Admission and next action

Unit 2 authority preflight is complete: three lecture sections, 19 exercises, five supplied solutions, and two media assets have exact closure. The next production action is to translate Lecture 2, Worksheet 2, and solutions 1/2/7/12/13 in source order, preserving exercise indices and both public-domain assets. This document does not claim that translation, build, semantic review, or visual QA has occurred.

The canonical machine-readable receipt is `qa/unit-02/AUTHORITY_PREFLIGHT.json`.
