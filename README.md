# Geometri Diferensial dan Manifold Mulus — edisi Bahasa Indonesia

Edisi independen Bahasa Indonesia dari kursus Holger Brenner,
*Differentialgeometrie (Osnabrück 2023)*. Kursus sumber lengkap terdiri atas
29 kuliah dan 29 lembar kerja. Sumber Wikiversity dibekukan pada tingkat
revisi beserta graf transklusinya, bukan hanya halaman agregator.

## Status pembaca

Batas kumulatif yang telah diverifikasi mencakup Kuliah 1–22 dan Lembar Kerja
1–22. Edisi ini masih berstatus `active_partial`: 7 pasangan inti berikutnya,
sepuluh formulir ujian resmi, serta dua jembatan asli terbatas masih harus
diselesaikan.

- [PDF Unit 1–22](output/pdf/geometri-diferensial-manifold-mulus-hingga-unit-22-id.pdf) — 345 halaman A4 terpusat, 9.046.717 byte, SHA-256 `4e6c03dc8388a4c10c464d939d5a416ab035c52e3bd233212c78a40617e02cf7`
- [Pembaca HTML semantik Unit 1–22](output/html/unit-22/index.html) — reflowable, navigasi tautan-dalam stabil, matematika MathJax dengan fallback TeX, media berteks alternatif, dan kontrol animasi yang dapat dipakai dengan papan ketik
- [Checkpoint Unit 22 di Zenodo](https://doi.org/10.5281/zenodo.22059977) — versi `2026.08.28-unit22` dalam konsep tetap yang sama; [Unit 19](https://doi.org/10.5281/zenodo.22134954) ialah pendahulu langsungnya
- [Sumber terjemahan](source/units) dan [backend modular](backend/README.md)
- [Kuitansi build PDF](qa/unit-22/build.json), [inspeksi visual seluruh halaman](qa/unit-22/PDF_VISUAL_QA.json), [QA browser](qa/unit-22/HTML_BROWSER_QA.json), dan [validasi backend](qa/unit-22/backend.json)

Pembaca mempertahankan seluruh 457 soal dalam urutan sumber, tepat 64 solusi
yang memang disediakan sumber, dan 31 media beratribusi; tidak ada lapisan
petunjuk atau solusi lengkap yang diklaim. Backend JSONL/CSV memuat 4.324
record ber-ID stabil.
Prefiks publik Unit 1–19 sebanyak 3.747 record dipertahankan secara identik
byte demi byte; 577 record baru menutup Unit 20–22. Backend adalah lapisan
tambahan: buku tetap dapat digunakan tanpa membacanya.

PDF memiliki metadata bahasa `id-ID`, pemetaan ToUnicode pada seluruh font,
dan teks yang dapat diekstrak pada semua 345 halaman. PDF belum bertag;
pembaca HTML adalah permukaan aksesibilitas terstruktur utama. Pengujian
Chromium nyata pada desktop dan seluler mencakup 7.261 ekspresi matematika,
seluruh media, navigasi, luapan, serta kontrol Putar/Hentikan dengan nol galat
MathJax atau konsol.

Rilis GitHub `v0.22.0-unit-22` dan versi Zenodo Unit 22 memakai tujuh berkas
publik yang sama. Setiap berkas diunduh ulang tanpa autentikasi dan dicocokkan
berdasarkan ukuran serta SHA-256. Paket sumber juga membangun ulang PDF,
pohon/ZIP HTML, backend, dan kuitansi QA secara identik dari dua direktori
ekstraksi kosong yang terpisah.

## Sumber, lisensi, dan independensi

Teks sumber dan adaptasi Bahasa Indonesia tersedia di bawah CC BY-SA 4.0.
Setiap media mempertahankan pencipta, sumber, dan lisensi berkasnya sendiri;
komponen media mencakup domain publik, CC BY, dan CC BY-SA dari beberapa versi.
Edisi ini bukan edisi resmi dan tidak menyiratkan dukungan dari Holger Brenner,
Wikiversity, Wikimedia Commons, Wikimedia Foundation, ataupun pencipta media.
Lihat [`LICENSE.md`](LICENSE.md) dan
[`authority/brenner_media_rights_manifest.csv`](authority/brenner_media_rights_manifest.csv).

Terjemahan, reflow, backend, dan QA pada batas ini menggunakan **OpenAI Codex gpt-5.6-sol, Ultra**
atas arahan pengguna. Kredit penulis sumber, kontributor
halaman, dan pencipta media tetap dipertahankan.

## Membangun ulang batas Unit 22

Prasyarat terbuka/offline: Python 3, PowerShell 7, MiKTeX/pdfTeX,
ImageMagick, serta paket Python yang dicatat oleh skrip verifikasi. Jalankan
dari akar repositori:

```text
pwsh -NoProfile -File scripts/build_through_unit22.ps1
python scripts/verify_through_unit22_pdf.py
python scripts/export_html_v22.py --root . --output output/html/unit-22 --replace
python scripts/verify_html_v22.py --root . --output output/html/unit-22
python scripts/export_backend_v22.py --root . --checkpoint 2026-08-28T13:30:00Z --translation-state mathematically_reviewed
python scripts/verify_backend_v22.py --root .
```

Rangkaian ini membangun PDF dari sumber TeX portabel, merekonstruksi HTML dua
kali untuk membuktikan determinisme, memverifikasi topologi latihan/solusi dan
hak media, lalu mengekspor backend append-only.

## Melanjutkan produksi

Status tahan-kompaksi berada di
[`00_control/GOAL_AND_WORKFLOW.md`](00_control/GOAL_AND_WORKFLOW.md),
[`00_control/CURRENT_STATE.md`](00_control/CURRENT_STATE.md), dan
[`00_control/CURSOR.json`](00_control/CURSOR.json). Kursor berikutnya ialah
pembekuan otoritas, lalu terjemahan Kuliah 23 + Lembar Kerja 23.
