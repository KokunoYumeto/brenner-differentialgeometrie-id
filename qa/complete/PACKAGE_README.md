# Complete Indonesian edition — reproducible source/backend package

This package accompanies version `2026.08.28-complete` of *Geometri
Diferensial dan Manifold Mulus — Edisi Bahasa Indonesia*. The complete PDF and
HTML reader are separate leading release files; this ZIP contains the compact
source, stable-ID backend, rights evidence, essential QA, and scripts needed to
reconstruct and verify them.

Primary rebuild commands from the extracted package root are recorded verbatim
in `PACKAGE_MANIFEST.json`. They build and verify the complete PDF, semantic
HTML, and backend without network access. `PACKAGE_CHECKSUMS.sha256` binds every
package member other than itself.

The optional Zenodo publication helper uses Python 3.10 or newer and the pinned
dependency in `requirements-release.txt` (`httpx==0.27.2`). Install that file in
an isolated environment before invoking the publisher. The reader rebuild and
the two clean offline reconstruction cycles do not use this dependency, a
credential, or the network.

The package deliberately excludes credentials, private machine locators, raw
bulk provenance dumps, caches, temporary renders, TeX auxiliaries, and duplicate
build trees. Source text and the Indonesian adaptation are CC BY-SA 4.0; media
retain their file-specific rights. See `LICENSE.md` and the rights/backend
records for exact component treatment.

Computational provenance: **OpenAI Codex gpt-5.6-sol, Ultra**.
