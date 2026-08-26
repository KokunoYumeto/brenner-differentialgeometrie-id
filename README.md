# Geometri Diferensial dan Manifold Mulus — edisi Bahasa Indonesia

Edisi independen Bahasa Indonesia dari kursus Holger Brenner,
*Differentialgeometrie (Osnabrück 2023)*. Kursus sumber lengkap terdiri atas
29 kuliah dan 29 lembar kerja. Sumber Wikiversity dibekukan pada tingkat
revisi beserta graf transklusinya, bukan hanya halaman agregator.

## Status pembaca

Batas kumulatif yang telah diverifikasi mencakup Kuliah 1–16 dan Lembar Kerja
1–16. Edisi ini masih berstatus `active_partial`: 13 pasangan inti berikutnya,
sepuluh formulir ujian resmi, serta dua jembatan asli terbatas masih harus
diselesaikan.

- [PDF Unit 1–16](output/pdf/geometri-diferensial-manifold-mulus-hingga-unit-16-id.pdf) — 261 halaman A4 terpusat, 7.241.359 byte, SHA-256 `58f98853ab8eeb1beb2aa4ade6bd3c746b62b4fa42c3c692a03c17076cdb06b8`
- [Pembaca HTML semantik Unit 1–16](output/html/unit-16/index.html) — reflowable, navigasi tautan-dalam stabil, matematika MathJax dengan fallback TeX, media berteks alternatif, dan kontrol animasi yang dapat dipakai dengan papan ketik
- [Checkpoint Unit 16 di Zenodo](https://doi.org/10.5281/zenodo.22104426) — versi `2026.08.26-unit16` dalam [konsep tetap yang sama](https://doi.org/10.5281/zenodo.22059977); Unit 13 r1 ialah pendahulu langsungnya
- [Sumber terjemahan](source/units) dan [backend modular](backend/README.md)
- [Kuitansi publikasi](qa/unit-16/ZENODO_PUBLICATION_RECEIPT.json), [pembacaan ulang anonim independen](qa/unit-16/ZENODO_PUBLIC_READBACK_RECEIPT.json), dan [bukti dua ekstraksi bersih](qa/unit-16/SOURCE_PACKAGE_INTEGRITY.json)

Pembaca mempertahankan seluruh 342 soal dalam urutan sumber dan tepat 48
solusi yang memang disediakan sumber; tidak ada lapisan petunjuk atau solusi
lengkap yang diklaim. Backend JSONL/CSV berisi 2.604 record ber-ID stabil dan
memuat 3.208 record ber-ID stabil. Prefiks publik Unit 1–13 sebanyak 2.604
record dipertahankan secara identik byte demi byte. Backend adalah lapisan
tambahan: buku tetap dapat digunakan tanpa membacanya.

PDF memiliki metadata bahasa `id-ID`, ToUnicode pada seluruh 34 objek font,
dan teks yang dapat diekstrak pada semua 261 halaman. PDF belum bertag;
pembaca HTML adalah permukaan aksesibilitas terstruktur utama. Pengujian
Chromium nyata pada desktop dan seluler mencakup 5.648 ekspresi matematika,
seluruh media, navigasi, luapan, serta kontrol Putar/Hentikan dengan nol galat
MathJax atau konsol.

Rilis GitHub `v0.16.0-unit-16` dan versi Zenodo Unit 16 memakai tujuh berkas
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

Terjemahan, reflow, backend, dan QA pada batas ini menggunakan **OpenAI Codex
gpt-5.6-sol, Ultra** atas arahan pengguna. Kredit penulis sumber, kontributor
halaman, dan pencipta media tetap dipertahankan.

## Membangun ulang batas Unit 16

Prasyarat terbuka/offline: Python 3, PowerShell 7, MiKTeX/pdfTeX,
ImageMagick, serta paket Python yang dicatat oleh skrip verifikasi. Jalankan
dari akar repositori:

```text
pwsh -NoProfile -File scripts/build_through_unit16.ps1
python scripts/verify_through_unit16_pdf.py
python scripts/export_html_v16.py --root . --output output/html/unit-16 --replace
python scripts/verify_html_v16.py --root . --output output/html/unit-16
python scripts/export_backend_v16.py --root . --checkpoint 2026-08-26T00:50:00Z --translation-state mathematically_reviewed
python scripts/verify_backend_v16.py --root .
python scripts/verify_source_package_unit16.py --root . --release-dir output/release-unit16
```

Rangkaian ini membangun PDF dari sumber TeX portabel, merekonstruksi HTML dua
kali untuk membuktikan determinisme, memverifikasi topologi latihan/solusi dan
hak media, lalu mengekspor backend append-only.

## Melanjutkan produksi

Status tahan-kompaksi berada di
[`00_control/GOAL_AND_WORKFLOW.md`](00_control/GOAL_AND_WORKFLOW.md),
[`00_control/CURRENT_STATE.md`](00_control/CURRENT_STATE.md), dan
[`00_control/CURSOR.json`](00_control/CURSOR.json). Kursor berikutnya ialah
pembekuan otoritas, lalu terjemahan Kuliah 17 + Lembar Kerja 17.
