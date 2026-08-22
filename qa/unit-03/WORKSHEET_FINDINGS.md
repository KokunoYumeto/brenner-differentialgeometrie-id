# Unit 3 worksheet and supplied-solution translation findings

Status: **PASS after complete translation review, two explicit mathematical corrections, and two reader-layout corrections.**

## Frozen authority and closure

The worksheet is the German Wikiversity surface `.../Arbeitsblatt 3`, page ID `142637`, revision `894109`, timestamp `2023-04-19T14:26:37Z`. Its sanitized expanded TeX witness is `authority/expanded/worksheet03_source.de.tex`, 9,997 bytes, SHA-256 `8dded699ee9337ebdc4cb76a9373fb8e2f6a5df94c6048c3deaaaeaccb88bac7`.

The worksheet contains 21 exercises: 16 practice exercises followed by five submission exercises worth `2, 2, 4, 4, 4` points, for 16 points total. All 21 hint fields are empty. Exactly Exercises 7 and 16 use `\inputaufgabegibtloesung`, and the frozen solution-page query proves that exactly those two source solutions exist.

| Exercise | Page ID / revision | Revision time (UTC) | Exact UTF-8 wikitext SHA-256 | Expanded German TeX SHA-256 |
|---:|---|---|---|---|
| 7 | `151168 / 1095913` | `2026-06-15T07:25:24Z` | `c771b7c1ed173ddc05c8c4219c3c34e7e8099fe42079740b292d991b2ce3fb25` | `7e3437274bf4f79b6a3fa719876b09fdbcee4e10523a215e9e6f4ecb566cdb85` |
| 16 | `151178 / 1095920` | `2026-06-15T07:26:34Z` | `237b3b08df28c060d3c5c2fb6efdf22ea7ae5df6c1fbfad68d64380fe7b4f852` | `ed49f1889840b8352f634ef01400301849f8303ec27a2a38b334b744ae5e5951` |

Worksheet media topology is preserved exactly: `Euler spiral.svg` is attributed to AdiJapan under CC BY-SA 3.0 and `Evolute-parab.svg` to Ag2gaeh under CC BY-SA 4.0. Exact binaries, derivative hashes, source pages, creators, and licenses pass in `qa/unit-03_media.json`.

## Preservation and language QA

- `verify_unit_translation.py` passes independently for the worksheet and both solutions; every declared topology delta is consumed.
- The worksheet preserves 323 TeX commands, 22 environment markers, 16 inline-math spans, 54 protected mathematical/media calls, and the full exercise topology. Internal-link destinations remain unchanged while visible labels are localized.
- The exercise-macro sequence is exactly 21 entries long and source-equivalent: Exercises 7 and 16 are the only solution-bearing entries; the final five point arguments are `2, 2, 4, 4, 4`; every hint and trailing metadata field remains empty.
- The two `\bildlizenz` calls, media filenames, creators, source label, and license strings are preserved.
- Complete prose and residue review found no reader-facing German apart from immutable semantic destinations and proper names. All targets are valid UTF-8 and contain no replacement characters, tested mojibake, personal paths, task IDs, umbrella-project strings, or secret-like metadata.

## Explicit target corrections

### O011-CORR-0028 — inconsistent clothoid scale (P2; corrected)

The stated curve has speed `\sqrt{\pi}` and tangent-angle derivative `\pi t`, hence signed curvature `\sqrt{\pi}t`, not `t`. The Indonesian task retains the stated curve and changes only the requested conclusion to `\kappa(t)=\sqrt{\pi}t`.

### O011-CORR-0029 — missing regularity condition (P2; corrected)

For `\alpha(t)=(\cos f(t),\sin f(t))`, one has `\alpha'(t)=f'(t)(-\sin f(t),\cos f(t))`. The curvature and curvature-circle formulas therefore apply only where `f'(t)\ne0`. The Indonesian task states that pointwise restriction.

### O011-CORR-0036 and O011-CORR-0037 — isolated display punctuation (P3; corrected)

Three worksheet full stops and one Exercise 7 solution full stop were initially placed after multiline equation macros, so the PDF rendered them on separate lines. Each now occupies the macro punctuation argument; no equation changed. The final translation receipts pass and direct inspection of the final PDF confirms that the isolated marks are gone.

No further mathematical defect was found in the 21 tasks. The Exercise 7 solution correctly forces the center and angular speed from the common two-jet. The Exercise 16 solution correctly evaluates the differential of the outward radial unit normal on the unit circle; its denominator disappears in the displayed multiplication because `x^2+y^2=1` at the stated point.

## Target and receipt inventory

| Target | Bytes | SHA-256 | Receipt SHA-256 |
|---|---:|---|---|
| `source/units/unit-03/worksheet03.id.tex` | 10,129 | `89b05cf8280045703c64e8a0d3540883196f6569f2c9e24f630a6b00ee703474` | `bf1decadfc0aaa53428e46c3ec590514bf78466b24088e60c043cc9ba1d42765` |
| `source/units/unit-03/worksheet03_exercise07_solution.id.tex` | 2,895 | `e1ec57974437f39f778c9eadc26f3cd565cfe69e3f88980d644b2df93552bb36` | `b0a310d469e4a421cfb70942a0df922447946b900470aeab481ee999dd748694` |
| `source/units/unit-03/worksheet03_exercise16_solution.id.tex` | 2,166 | `738506177ab79f47321e5e6e83b110bfae887161477abda8145dc7ff52c2ebf3` | `1aa1c1feac878b9871bfc415e38015a0d929ebc7775b42cc1515fa3b568cfbad` |

The Unit 3 terminology entries are merged into `00_control/TERMINOLOGY.csv`; all source corrections remain explicit in `00_control/ADVERSE_LEDGER.csv`.
