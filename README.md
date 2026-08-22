# Geometri Diferensial dan Manifold Mulus — edisi Bahasa Indonesia

Edisi independen Bahasa Indonesia dari kursus Holger Brenner, *Differentialgeometrie (Osnabrück 2023)*. Cakupan sumber lengkapnya ialah 29 kuliah dan 29 lembar kerja. Sumber Wikiversity dibekukan pada tingkat revisi beserta graf transklusinya, bukan hanya halaman agregator.

## Status dan unduhan

Pembaca kumulatif hingga Unit 2—Kuliah 1–2, Lembar Kerja 1–2, dan keenam solusi yang memang disediakan sumber—telah lulus pemeriksaan terjemahan, matematika, hak media, pembangunan ulang, visual, struktur PDF, privasi, dan reproduktibilitas. Edisi 29 unit belum selesai. Unit 2 telah diverifikasi secara lokal; Unit 1 tetap merupakan rilis publik terbaru karena giliran kerja ini secara khusus tidak melakukan Git atau publikasi.

- [PDF kumulatif hingga Unit 2](output/pdf/geometri-diferensial-manifold-mulus-hingga-unit-02-id.pdf) — 44 halaman A4, 3.152.320 byte, SHA-256 `6312b4df706d0f08eeb9f37da0abda3428b5448dce54781d0f52eb9c8db5c385`
- [PDF Unit 1](output/pdf/geometri-diferensial-manifold-mulus-unit-01-id.pdf) — 25 halaman A4, 2.678.755 byte, SHA-256 `eb7e78affacf8a559d0f52a1c44921633d2fa74a070faa64af58efc32d34a568`
- [Rilis GitHub Unit 1](https://github.com/KokunoYumeto/brenner-differentialgeometrie-id/releases/tag/v0.1.0-unit-01) — aset PDF yang sama, dibaca ulang secara publik dan cocok byte demi byte
- [Sumber terjemahan](source/units)
- [Bukti QA Unit 2](qa/unit-02/UNIT_02_QA.md)
- [Backend modular](backend/README.md) — 357 rekaman ber-ID stabil untuk Unit 1–2; lapisan tambahan, bukan syarat untuk membaca buku

PDF memiliki metadata bahasa `id-ID`, pemetaan ToUnicode pada seluruh font, dan teks yang dapat diekstrak pada semua halaman. PDF belum memiliki penandaan struktur; pembaca HTML semantik akan menjadi permukaan aksesibilitas terstruktur utama.

## Sumber, lisensi, dan independensi

Teks sumber digunakan dan diadaptasi berdasarkan CC BY-SA 4.0; atribusi dan riwayat halaman sumber dipertahankan. Setiap media tetap mengikuti lisensi berkasnya sendiri. Edisi ini bukan edisi resmi dan tidak menyiratkan dukungan dari Holger Brenner, Wikiversity, atau para pembuat media.

Rincian hak, atribusi, perubahan, dan batas lisensi media tersedia dalam [`LICENSE.md`](LICENSE.md). Identitas sumber dan proses pembangunan ulang ada dalam [`00_control/AUTHORITY_FREEZE.md`](00_control/AUTHORITY_FREEZE.md), [`qa/unit-01/build.json`](qa/unit-01/build.json), dan [`qa/unit-02/build.json`](qa/unit-02/build.json).

## Membangun ulang pembaca hingga Unit 2

Prasyarat terbuka/offline: Python 3, PowerShell 7 (`pwsh`), MiKTeX/pdfTeX, dan ImageMagick. Setelah dependensi tersedia, jalankan dari akar repositori:

```text
pwsh -NoProfile -File scripts/build_through_unit02.ps1
python scripts/verify_through_unit02_pdf.py --project-root .
python scripts/export_backend_v2.py --timestamp 2026-08-22T04:29:34Z --translation-state structurally_verified
python scripts/verify_backend_v2.py --root . --checkpoint 2026-08-22T04:29:34Z --first-jsonl-sha256 a393d3ff6c8aed203e7d3690eb6391e22ea25436cd06e85aa40e1adc23adb122 --first-csv-sha256 5880fa9dee8bc0a73ed0e903d931fad38978bc2c9ef65cc58b62b48a7f26b7ba --first-manifest-sha256 2b34e24c0efbce3b6cc847ddc1232b4f2b881126f7b6d5ac39ba469b22b7f789
```

Skrip pembangunan menyegarkan seluruh bukti kesetaraan topologi sumber/terjemahan untuk kedua unit, kemudian menyiapkan media dan TeX portabel, menjalankan dua siklus bersih yang masing-masing terdiri atas tiga lintasan pdfTeX, dan menolak hasil yang tidak identik byte demi byte.

## Melanjutkan produksi

Status tahan-kompaksi berada di [`00_control/GOAL_AND_WORKFLOW.md`](00_control/GOAL_AND_WORKFLOW.md), [`00_control/CURRENT_STATE.md`](00_control/CURRENT_STATE.md), dan [`00_control/CURSOR.json`](00_control/CURSOR.json). Kursor berikutnya ialah Kuliah 3 + Lembar Kerja 3.
