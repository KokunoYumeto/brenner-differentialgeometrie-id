# Geometri Diferensial dan Manifold Mulus — paket sumber Unit 22

Paket ini memulihkan batas `active_partial` Kuliah 1–22 dan Lembar Kerja 1–22
dari 29 pasangan inti. Pembaca utama diterbitkan terpisah sebagai PDF A4
terpusat 345 halaman dan arsip HTML semantik yang dapat menyesuaikan lebar
layar. Paket sumber memuat bahan minimum yang diperlukan untuk memeriksa,
melanjutkan, dan membangun ulang batas yang sama tanpa bergantung pada lokasi
pribadi atau layanan daring yang dapat berubah.

Paket memuat:

- kontrol publik yang tahan kehilangan konteks: tujuan/alur kerja, status,
  kursor, keputusan, pembekuan otoritas, batas lingkup, terminologi, serta
  ledger koreksi/adverse;
- sumber Indonesia Unit 1–22, sumber Jerman terurai yang benar-benar dipakai,
  media yang diakui, ledger hak, dan manifes koreksi terlindungi;
- pembungkus dan input build portabel, backend stable-ID JSONL/CSV beserta
  skema, kuitansi QA esensial, serta skrip build/verifikasi;
- artefak pendahulu yang diperlukan untuk membuktikan prefiks append-only,
  tanpa menduplikasi pembaca Unit 22 di dalam ZIP sumber;
- `PACKAGE_MANIFEST.json` dan `PACKAGE_CHECKSUMS.sha256` yang mengikat seluruh
  anggota paket.

Kredensial, locator lokal privat, cache, render halaman/contact sheet,
diagnostik gambar sementara, dump MediaWiki/XML mentah, keluaran TeX bantu,
duplikasi pembaca, dan kuitansi publikasi jarak jauh tidak disertakan.

## Pembangunan ulang dari ekstraksi bersih

Ekstrak ZIP ke direktori kosong, pertahankan struktur relatifnya, lalu jalankan
dari akar hasil ekstraksi:

```powershell
pwsh -NoProfile -File scripts/build_through_unit22.ps1
python scripts/verify_through_unit22_pdf.py
python scripts/export_html_v22.py --root . --output output/html/unit-22 --replace
python scripts/verify_html_v22.py --root . --output output/html/unit-22
python scripts/export_backend_v22.py --root . --checkpoint 2026-08-28T13:30:00Z --translation-state mathematically_reviewed
python scripts/verify_backend_v22.py --root .
```

Jalur PDF memerlukan PowerShell, `pdflatex`, Python, `pypdf`, dan
`pdfplumber`; verifikator/backend juga memerlukan `jsonschema`. HTML dan backend
dapat dibangun tanpa jaringan. MathJax CDN hanya merupakan peningkatan opsional
pada saat penayangan; rumus dan sumber semantiknya tetap berada dalam pembaca.

Teks dan adaptasi Indonesia berlisensi CC BY-SA 4.0. Media mempertahankan
lisensi per berkas; tidak ada lisensi media menyeluruh yang disimpulkan.
Terjemahan, reflow, backend, pengemasan, dan QA pada batas ini menggunakan
**OpenAI Codex gpt-5.6-sol, Ultra** atas arahan pengguna. Kredit Holger Brenner,
kontributor halaman, dan pencipta media tetap dipertahankan.
