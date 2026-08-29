# Geometri Diferensial dan Manifold Mulus — Edisi Bahasa Indonesia

Edisi independen Bahasa Indonesia dari kursus Holger Brenner,
*Differentialgeometrie (Osnabrück 2023)*. Edisi lengkap ini mempertahankan
urutan sumber, rumus, latihan, solusi yang benar-benar disediakan sumber,
identitas revisi, graf transklusi, serta hak setiap komponen media.

## Status edisi lengkap

Pembaca mencakup seluruh 29 kuliah dan 29 lembar kerja. Isinya mempertahankan
576 latihan inti dan seluruh 84 solusi lembar kerja yang disediakan sumber.
Bank penilaian resmi berisi sepuluh formulir ujian dengan 147 slot templat:
24 placeholder dikecualikan secara eksplisit, sehingga tersisa 123 kemunculan
soal aktual dan 117 kemunculan solusi resmi. Enam kemunculan yang tidak memiliki
solusi sumber dilengkapi dengan solusi asli yang diberi label dan provenans
terpisah.

Dua jembatan kurikuler asli melengkapi cakupan: grup/aljabar Lie serta
kohomologi de Rham/pengantar topologi diferensial. Kedua jembatan memuat 24
latihan dan delapan soal penguasaan, semuanya dengan petunjuk dan solusi
lengkap. Jadi terdapat tepat 32 butir jembatan asli yang memiliki solusi, atau
38 butir asli secara keseluruhan setelah enam perbaikan solusi ujian dihitung.

Artefak utama:

- [PDF lengkap](output/pdf/geometri-diferensial-manifold-mulus-edisi-lengkap-id.pdf) — 712 halaman A4 terpusat, 10.525.469 byte, SHA-256 `26f19153db2ca08851e182202900a8371f1816b428f8fe7321b35de60b9c84ef`.
- [Pembaca HTML semantik lengkap](output/html/complete/index.html) — reflowable dan responsif, 2.581.792 byte, SHA-256 `a7b26055e9be40fbd13116a2857114b27da2ae7cd93e84af5ca0f042a41f9c00`; [manifest HTML](output/html/complete/manifest.json) mengikat pohon pembaca dan media.
- [Backend JSONL](backend/records.jsonl) dan [CSV](backend/records.csv) — 6.912 record ber-ID stabil; [manifest backend](backend/MANIFEST.json) mencatat skema, hitungan, dan identitas artefak.
- [Sumber 29 unit](source/units), [sepuluh ujian](source/exams), dan [dua jembatan](source/bridges).
- [Kuitansi build PDF](qa/complete/build.json), [QA struktural PDF](qa/complete/pdf_structural_qa.json), [QA HTML](qa/complete/HTML_READER_QA.json), dan [validasi backend](qa/complete/backend.json).

Backend mempertahankan prefiks publik Unit 1–22 sebanyak 4.324 record secara
identik byte demi byte, lalu menambahkan 2.588 record untuk penutupan korpus.
Lapisan ini bersifat tambahan: PDF dan HTML tetap dapat digunakan tanpa
memproses JSONL atau CSV.

PDF mempunyai metadata bahasa `id-ID`, pemetaan ToUnicode pada seluruh font,
dan teks yang dapat diekstrak pada semua 712 halaman. PDF belum bertag;
pembaca HTML merupakan permukaan aksesibilitas terstruktur utama. Pemeriksaan
HTML mencakup 12.484 ekspresi matematika, 36 kemunculan gambar, tautan-dalam,
teks alternatif, media, navigasi papan ketik, serta reflow desktop dan seluler
tanpa galat MathJax atau luapan halaman global.

## Sumber, lisensi, dan independensi

Teks sumber, adaptasi Bahasa Indonesia, kedua jembatan asli, dan enam solusi
perbaikan tersedia di bawah CC BY-SA 4.0. Media tidak menerima lisensi payung:
setiap berkas mempertahankan pencipta, sumber, versi lisensi, dan ketentuannya
sendiri. Edisi ini tidak resmi dan tidak menyiratkan dukungan dari Holger
Brenner, Wikiversity, Wikimedia Commons, Wikimedia Foundation, ataupun
pencipta media.
Lihat [`LICENSE.md`](LICENSE.md) dan
[`authority/brenner_media_rights_manifest.csv`](authority/brenner_media_rights_manifest.csv).

Terjemahan, reflow, modul asli, backend, build, dan QA menggunakan
**OpenAI Codex gpt-5.6-sol, Ultra** atas arahan pengguna. Kredit penulis
sumber, kontributor halaman, dan pencipta media tetap dipertahankan.

## Membangun dan memverifikasi edisi lengkap

Prasyarat terbuka/offline: Python 3, PowerShell 7, MiKTeX/pdfTeX,
ImageMagick, serta paket Python yang dicatat oleh skrip verifikasi. Jalankan
dari akar repositori:

```text
pwsh -NoProfile -File scripts/build_complete_reader.ps1
python scripts/verify_complete_reader.py
python scripts/export_html_complete.py --root . --output output/html/complete --replace
python scripts/verify_html_complete.py --root . --output output/html/complete
python scripts/export_backend_complete.py --root . --checkpoint 2026-08-28T18:30:00Z --translation-state mathematically_reviewed
python scripts/verify_backend_complete.py --root .
```

Rangkaian ini membangun dan memeriksa PDF lengkap, mengekspor serta merestage
HTML dua kali untuk membuktikan determinisme, dan merekonstruksi backend
append-only sambil memverifikasi identitas, relasi, topologi soal/solusi,
provenans, matematika, serta hak media.

Status tahan-kompaksi berada di
[`00_control/GOAL_AND_WORKFLOW.md`](00_control/GOAL_AND_WORKFLOW.md),
[`00_control/CURRENT_STATE.md`](00_control/CURRENT_STATE.md), dan
[`00_control/CURSOR.json`](00_control/CURSOR.json), dan
[`00_control/DECISION_LOG.md`](00_control/DECISION_LOG.md).
