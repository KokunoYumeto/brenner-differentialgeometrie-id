# Independent reader and mathematics QA — Unit 13

Date: 2026-08-24

Status: **PASS after one bounded terminology repair**

## Scope

This review covered the complete Indonesian Lecture 13, Worksheet 13, the
eight source-supplied solutions to Exercises 1, 10, 11, 16, 18, 19, 21, and
22, the prepared TeX fragments, the exact worksheet census, the admitted
Möbius-strip image and its file-specific rights, and all declared Unit 13
mathematical or translation deltas.

## Independent findings

- The frozen authority closure and all live referenced bytes/hashes passed.
- The worksheet preserves 24 exercises: 19 practice exercises and five graded
  exercises (20–24), four points each, for 20 points total.
- All 24 hint fields remain blank. Exactly the eight source-supplied solutions
  listed above are present; no missing solution or hint layer is implied.
- The declared corrections O011-CORR/TRANS-0135 through 0140 and 0150 through
  0154 are mathematically and structurally justified. In particular, the
  target correctly repairs the supplied Solution 21 parity claim for the
  antipodal map, the finite-subcover equality in Solution 10, the uppercase
  chart-image index in Solution 19, and the ill-typed bounded-image relation in
  Solution 11.
- No reader-visible German prose, UTF-8 replacement character, or BOM remains.
  Residual German strings are frozen non-reader-visible source identifiers.
- The canonical 82,042-byte image `Möbius strip.jpg` remains byte-identical
  with SHA-256
  `9c4323cfa3ce4f3ce043e4e2479dbf68658d165c46bd41394991361859ea9fad`;
  its David Benbennick attribution and CC BY-SA 3.0 license are retained.

## Finding and repair

The first independent pass found three stale renderings of “finite subcover”
as `tutupan bagian berhingga`, inconsistent with glossary record
O011-TERM-0228 and the lecture's admitted `subtutupan hingga`. The three
reader-visible occurrences in Solutions 10, 16, and 22 were normalized and
recorded as O011-TRANS-0155. Their translation verifiers and TeX preparers were
rerun, followed by a separate read-only recheck.

Post-repair identities:

| Solution | Target SHA-256 | Translation receipt SHA-256 | Prepared SHA-256 |
|---|---|---|---|
| 10 | `522b280e4783ef70436f915492b36cc7cb6fc776ab42310d74e52e8605320a3e` | `17974357e6eff8e7d8fcffa64b9eae5b5d3882ce6affe37904ecc34d3e0b5a5c` | `bc6b663193a48174637eb4384682ee4b0357d13cc990cde063a47d56177b7098` |
| 16 | `802f85bf09bec093760930a4c179651c540c1b2b75b21943a12724a74f9d6fa3` | `11cb0edf9245033c3bae3b98087a876935fe098b3fcb49ac89ef2c0a33025e06` | `0931addc2f1a421dd6281b56c2a7df6d5fb451364a84a1fd4452d6f28ff031e2` |
| 22 | `8924d20cfd8305c389961d28bdbc9a5858927b49977924295997c94a0a1932bf` | `495909a1f2abccda269962ca2442265dbd1f845b8a5f98323775febc2306a4c8` | `ad94277318aa5181941b380ef51ae41645903fea13d295b6163b1348e46434b6` |

Each current receipt reports `status=pass`, all checks are true, and failures
are empty. `subtutupan hingga` occurs exactly once in each affected target and
prepared fragment; the stale phrase is absent.

## Boundary

Unit 13 passes its bounded source, translation, mathematics, structure,
terminology, media-rights, and prepared-fragment gate. This document does not
claim the cumulative PDF, HTML, backend, visual, release, or public-readback
gate; those follow once in the consolidated Units 11–13 milestone.
