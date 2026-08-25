# Geometri Diferensial dan Manifold Mulus — paket sumber Unit 13 r1

Ini adalah revisi korektif paket sumber untuk batas `active_partial` Kuliah
1–13 dan Lembar Kerja 1–13. Isi pembaca, PDF A4 213 halaman, dan arsip HTML
yang telah divalidasi tidak berubah dari record Zenodo 22096736. Revisi ini
memperbaiki paket sumber agar pemulihan alur kerja dan pembangunan ulang tidak
bergantung pada berkas lokal yang tidak ikut diterbitkan.

Paket sekarang memuat:

- kontrol publik yang tahan kehilangan konteks: `GOAL_AND_WORKFLOW`,
  `CURRENT_STATE`, `CURSOR`, `DECISION_LOG`, pembekuan otoritas, batas lingkup,
  terminologi, dan ledger adverse;
- seluruh 48 manifes koreksi terlindungi kumulatif sampai Unit 13;
- sumber Indonesia yang dapat diedit, sumber Jerman terurai yang dipakai,
  media, ledger hak, kuitansi QA, backend stable-ID, skema, dan skrip pembangun;
- seluruh masukan transitif yang diikat kuitansi pembangunan Unit 13;
- PDF Unit 10, pohon HTML Unit 10, tujuh berkas rilis Unit 10, source ZIP dan
  HTML ZIP Unit 10, serta kuitansi build, struktur, HTML, dan readback publik
  Unit 10 dengan byte dan lokasi relatif aslinya.

`00_control/PRIVATE_LOCAL_LOCATORS.md`, kredensial, cache, render sementara,
dump MediaWiki/XML mentah, dan kuitansi privat yang dikenal
`qa/unit-05/ZENODO_PUBLICATION_RECEIPT.md` sengaja tidak disertakan. PDF dan
HTML Unit 13 tersedia sebagai dua berkas publik pembaca tersendiri; paket
sumber ini tidak menduplikasi keduanya.

## Pembangunan ulang dari ekstraksi bersih

Ekstrak ZIP ini ke direktori kosong dan jalankan perintah berikut dari akar
hasil ekstraksi. Jangan memindahkan subdirektori karena kuitansi memakai path
relatif yang disengaja.

```powershell
pwsh -NoProfile -File scripts/build_through_unit13.ps1
python scripts/verify_through_unit13_pdf.py
python scripts/export_html_v13.py --root . --output output/html/unit-13 --replace
python scripts/verify_html_v13.py --root . --output output/html/unit-13
python scripts/export_backend_v13.py --root . --checkpoint 2026-08-24T20:50:06Z --translation-state mathematically_reviewed
python scripts/verify_backend_v13.py --root .
```

Jalur PDF memerlukan PowerShell, `pdflatex`, Python, `pypdf`, dan
`pdfplumber`; verifikator/backend juga memerlukan `jsonschema`. Jalur HTML dan
backend bekerja offline kecuali MathJax CDN opsional pada tampilan rumus di
browser. Skrip menolak identitas Unit 10, sumber, media, QA, atau koreksi yang
berubah. `PACKAGE_MANIFEST.json` mencatat kontrak closure dan
`PACKAGE_CHECKSUMS.sha256` mengikat setiap anggota arsip.

Teks dan adaptasi Indonesia berlisensi CC BY-SA 4.0. Media mempertahankan
lisensi per berkas; tidak ada lisensi media menyeluruh yang disimpulkan.
Terjemahan, reflow, backend, pengemasan korektif, dan QA pada batas ini
menggunakan **OpenAI Codex gpt-5.6-sol, Ultra** atas arahan pengguna. Kredit
Holger Brenner, kontributor halaman, dan pencipta media tetap dipertahankan.
