# Geometri Diferensial dan Manifold Mulus — edisi Bahasa Indonesia

Edisi independen Bahasa Indonesia dari kursus Holger Brenner,
*Differentialgeometrie (Osnabrück 2023)*. Kursus sumber lengkap terdiri atas
29 kuliah dan 29 lembar kerja. Sumber Wikiversity dibekukan pada tingkat
revisi beserta graf transklusinya, bukan hanya halaman agregator.

## Status pembaca

Batas kumulatif yang telah diverifikasi mencakup Kuliah 1–13 dan Lembar Kerja
1–13. Edisi ini masih berstatus `active_partial`: 16 pasangan inti berikutnya,
sepuluh formulir ujian resmi, serta dua jembatan asli terbatas masih harus
diselesaikan.

- [PDF Unit 1–13](output/pdf/geometri-diferensial-manifold-mulus-hingga-unit-13-id.pdf) — 213 halaman A4 terpusat, 6.396.207 byte, SHA-256 `a4d7e55604de9bfb6556d78461db8255a6c584d36b8934a0993b2386ad5832a7`
- [Pembaca HTML semantik Unit 1–13](output/html/unit-13/index.html) — reflowable, navigasi tautan-dalam stabil, matematika MathJax dengan fallback TeX, media berteks alternatif, dan kontrol animasi yang dapat dipakai dengan papan ketik
- [Preservasi Zenodo Unit 13 r1](https://doi.org/10.5281/zenodo.22097422) — revisi paket sumber dalam konsep tetap [`10.5281/zenodo.22059977`](https://doi.org/10.5281/zenodo.22059977); byte PDF dan HTML tidak berubah
- [Sumber terjemahan](source/units) dan [backend modular](backend/README.md)
- [Kuitansi publikasi r1](qa/unit-13/ZENODO_PUBLICATION_RECEIPT_R1.json), [pembacaan ulang anonim independen](qa/unit-13/ZENODO_PUBLIC_READBACK_RECEIPT_R1.json), dan [bukti dua ekstraksi bersih](qa/unit-13/SOURCE_PACKAGE_R1_INTEGRITY.json)

Pembaca mempertahankan seluruh 287 soal dalam urutan sumber dan tepat 35
solusi yang memang disediakan sumber; tidak ada lapisan petunjuk atau solusi
lengkap yang diklaim. Backend JSONL/CSV berisi 2.604 record ber-ID stabil dan
mempertahankan prefiks publik Unit 1–10 sebanyak 1.888 record secara identik
byte demi byte. Backend adalah lapisan tambahan: buku tetap dapat digunakan
tanpa membacanya.

PDF memiliki metadata bahasa `id-ID`, ToUnicode pada seluruh 33 objek font,
dan teks yang dapat diekstrak pada semua 213 halaman. PDF belum bertag;
pembaca HTML adalah permukaan aksesibilitas terstruktur utama. Pengujian
Chromium nyata pada desktop dan seluler mencakup 4.598 ekspresi matematika,
seluruh media, navigasi, luapan, serta kontrol Putar/Hentikan dengan nol galat
MathJax atau konsol.

GitHub untuk sementara dapat mengembalikan 404 karena penangguhan keamanan
akun setelah pemakaian VPN; tiket dukungan telah diajukan. Keadaan itu bukan
kegagalan sumber atau pembaca. Zenodo di atas adalah preservasi publik terbaru.
Ketujuh berkas publiknya telah diunduh ulang tanpa autentikasi oleh penerbit
dan verifikator independen. Paket sumber 475-anggota juga telah membangun ulang
PDF, pohon/ZIP HTML, backend, dan kuitansi QA secara identik dari dua direktori
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

## Membangun ulang batas Unit 13

Prasyarat terbuka/offline: Python 3, PowerShell 7, MiKTeX/pdfTeX,
ImageMagick, serta paket Python yang dicatat oleh skrip verifikasi. Jalankan
dari akar repositori:

```text
pwsh -NoProfile -File scripts/build_through_unit13.ps1
python scripts/verify_through_unit13_pdf.py
python scripts/export_html_v13.py --root . --replace
python scripts/verify_html_v13.py --root .
python scripts/export_backend_v13.py --root . --checkpoint 2026-08-24T20:50:06Z --translation-state mathematically_reviewed
python scripts/verify_backend_v13.py --root .
python scripts/verify_source_package_unit13_r1.py --root .
```

Rangkaian ini membangun PDF dari sumber TeX portabel, merekonstruksi HTML dua
kali untuk membuktikan determinisme, memverifikasi topologi latihan/solusi dan
hak media, lalu mengekspor backend append-only.

## Melanjutkan produksi

Status tahan-kompaksi berada di
[`00_control/GOAL_AND_WORKFLOW.md`](00_control/GOAL_AND_WORKFLOW.md),
[`00_control/CURRENT_STATE.md`](00_control/CURRENT_STATE.md), dan
[`00_control/CURSOR.json`](00_control/CURSOR.json). Kursor berikutnya ialah
pembekuan otoritas, lalu terjemahan Kuliah 14 + Lembar Kerja 14.
