# Geometri Diferensial dan Manifold Mulus — edisi Bahasa Indonesia

Edisi independen Bahasa Indonesia dari kursus Holger Brenner, *Differentialgeometrie (Osnabrück 2023)*. Cakupan sumber lengkapnya ialah 29 kuliah dan 29 lembar kerja. Sumber Wikiversity dibekukan pada tingkat revisi beserta graf transklusinya, bukan hanya halaman agregator.

## Status dan unduhan

Unit 1—Kuliah 1, Lembar Kerja 1, dan satu solusi yang memang disediakan sumber—telah lulus pemeriksaan terjemahan, matematika, hak media, pembangunan ulang, visual, struktur PDF, privasi, dan reproduktibilitas. Edisi 29 unit belum selesai.

- [PDF Unit 1](output/pdf/geometri-diferensial-manifold-mulus-unit-01-id.pdf) — 25 halaman A4, 2.678.755 byte, SHA-256 `eb7e78affacf8a559d0f52a1c44921633d2fa74a070faa64af58efc32d34a568`
- [Sumber terjemahan Unit 1](source/units/unit-01)
- [Bukti QA Unit 1](qa/unit-01/UNIT_01_QA.md)
- [Backend modular](backend/README.md) — 174 rekaman ber-ID stabil; lapisan tambahan, bukan syarat untuk membaca buku

PDF memiliki metadata bahasa `id-ID`, pemetaan ToUnicode pada seluruh font, dan teks yang dapat diekstrak pada semua halaman. PDF belum memiliki penandaan struktur; pembaca HTML semantik akan menjadi permukaan aksesibilitas terstruktur utama.

## Sumber, lisensi, dan independensi

Teks sumber digunakan dan diadaptasi berdasarkan CC BY-SA 4.0; atribusi dan riwayat halaman sumber dipertahankan. Setiap media tetap mengikuti lisensi berkasnya sendiri. Edisi ini bukan edisi resmi dan tidak menyiratkan dukungan dari Holger Brenner, Wikiversity, atau para pembuat media.

Rincian hak, atribusi, perubahan, dan batas lisensi media tersedia dalam [`LICENSE.md`](LICENSE.md). Identitas sumber dan proses pembangunan ulang ada dalam [`00_control/AUTHORITY_FREEZE.md`](00_control/AUTHORITY_FREEZE.md) dan [`qa/unit-01/build.json`](qa/unit-01/build.json).

## Membangun ulang Unit 1

Prasyarat terbuka/offline: Python 3, PowerShell 7 (`pwsh`), MiKTeX/pdfTeX, dan ImageMagick. Setelah dependensi tersedia, jalankan dari akar repositori:

```text
pwsh -NoProfile -File scripts/build_unit01.ps1
python scripts/verify_unit01_pdf.py --project-root .
python scripts/export_backend.py --timestamp 2026-08-21T17:24:54Z --translation-state visually_checked
```

Skrip pembangunan menyegarkan terlebih dahulu ketiga bukti kesetaraan topologi sumber/terjemahan, kemudian menyiapkan media dan TeX portabel, menjalankan dua siklus bersih yang masing-masing terdiri atas tiga lintasan pdfTeX, dan menolak hasil yang tidak identik byte demi byte.

## Melanjutkan produksi

Status tahan-kompaksi berada di [`00_control/GOAL_AND_WORKFLOW.md`](00_control/GOAL_AND_WORKFLOW.md), [`00_control/CURRENT_STATE.md`](00_control/CURRENT_STATE.md), dan [`00_control/CURSOR.json`](00_control/CURSOR.json). Kursor berikutnya ialah Kuliah 2 + Lembar Kerja 2.
