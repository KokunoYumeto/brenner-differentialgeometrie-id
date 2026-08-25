# Geometri Diferensial dan Manifold Mulus — batas Unit 13

Rilis `active_partial` ini menyediakan pembaca kumulatif Bahasa Indonesia untuk
Kuliah 1–13 dan Lembar Kerja 1–13 dari kursus Holger Brenner,
*Differentialgeometrie (Osnabrück 2023)*. Berkas publik disusun dengan urutan
pembaca terlebih dahulu: PDF A4, pembaca HTML semantik yang dapat di-reflow,
lalu paket sumber/backend/QA ringkas yang dapat dipakai untuk melanjutkan
pekerjaan. Manifes CSV dan daftar checksum mengikat byte publik yang disiapkan.

PDF berisi 213 halaman A4 yang terpusat dan dapat diekstrak sebagai teks. PDF
belum bertag; pembaca HTML adalah permukaan aksesibilitas terstruktur dan
pendamping, bukan pengganti sumber yang dapat diedit. HTML memuat seluruh 287
soal dalam urutan sumber, tepat 35 solusi yang memang disediakan sumber, 21
media tertanam, tiga animasi sumber yang dapat diunduh, serta 4.598 ekspresi
matematika. Pemeriksaan Chromium nyata pada desktop dan seluler menemukan nol
galat MathJax, nol galat konsol, dan tidak ada luapan halaman; matematika lebar
dapat digulir secara lokal. Kontrol Putar/Hentikan animasi, keadaan statis awal,
dan preferensi pengurangan gerak telah diverifikasi.

Backend locale-neutral mengekspor 2.604 record JSONL/CSV yang valid terhadap
skema. Prefiks publik Unit 1–10 sebanyak 1.888 record dipertahankan identik
byte demi byte; Unit 11–13 menambahkan 716 record dan mengikat PDF, HTML,
manifes, QA, hak komponen, koreksi, latihan, serta solusi secara all-or-nothing.

Teks kursus dan adaptasi Indonesia tersedia di bawah CC BY-SA 4.0. Media tidak
mewarisi satu lisensi menyeluruh: setiap komponen mempertahankan pencipta,
sumber, dan lisensinya sendiri, termasuk komponen domain publik, CC BY, dan CC
BY-SA dari beberapa versi. Adaptasi ini independen, bukan edisi resmi, dan
tidak didukung oleh penulis sumber, Wikiversity, Wikimedia Commons, Wikimedia
Foundation, ataupun pencipta media. Rincian lengkap ada di `LICENSE.md` dan
ledger hak dalam paket sumber.

Terjemahan, reflow, backend, dan QA pada batas ini menggunakan **OpenAI Codex
gpt-5.6-sol, Ultra** atas arahan pengguna. Model bukan pengarang karya; kredit
penulis sumber, kontributor halaman, dan pencipta media tetap dipertahankan.

Paket sumber sengaja tidak memuat dump MediaWiki/XML mentah, PDF saksi
historis, render sementara, cache, locator privat, kredensial, kuitansi
publikasi jarak jauh, atau build turunan duplikat. `PACKAGE_MANIFEST.json` dan
`PACKAGE_CHECKSUMS.sha256` di dalam arsip mengikat inventaris ringkas tersebut.
