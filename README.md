# Geometri Diferensial dan Manifold Mulus — edisi Bahasa Indonesia

Edisi independen Bahasa Indonesia dari kursus Holger Brenner, *Differentialgeometrie (Osnabrück 2023)*. Cakupan sumber lengkapnya ialah 29 kuliah dan 29 lembar kerja. Sumber Wikiversity dibekukan pada tingkat revisi beserta graf transklusinya, bukan hanya halaman agregator.

## Status dan unduhan

Pembaca kumulatif hingga Unit 3—Kuliah 1–3, Lembar Kerja 1–3, dan seluruh delapan solusi yang memang disediakan sumber—telah lulus pemeriksaan terjemahan, matematika, hak media, pembangunan ulang, visual, struktur PDF, privasi, dan reproduktibilitas. Edisi 29 unit belum selesai.

- [PDF kumulatif hingga Unit 3](output/pdf/geometri-diferensial-manifold-mulus-hingga-unit-03-id.pdf) — 56 halaman A4, 3.596.282 byte, SHA-256 `aee7f335c8d8110feb7b70448c70680a30700285131d5a1b4e4aeb2f2d04b46a`
- Rilis GitHub Unit 3 sedang dipublikasikan sebagai `v0.3.0-unit-03`; tautan publik akan dicatat setelah pembacaan ulang anonim selesai.
- [PDF kumulatif hingga Unit 2](output/pdf/geometri-diferensial-manifold-mulus-hingga-unit-02-id.pdf) — 44 halaman A4, 3.152.320 byte, SHA-256 `6312b4df706d0f08eeb9f37da0abda3428b5448dce54781d0f52eb9c8db5c385`
- [Rilis GitHub Unit 2](https://github.com/KokunoYumeto/brenner-differentialgeometrie-id/releases/tag/v0.2.0-unit-02) — pembaca kumulatif dan sumber terverifikasi hingga Unit 2
- [PDF Unit 1](output/pdf/geometri-diferensial-manifold-mulus-unit-01-id.pdf) — 25 halaman A4, 2.678.755 byte, SHA-256 `eb7e78affacf8a559d0f52a1c44921633d2fa74a070faa64af58efc32d34a568`
- [Rilis GitHub Unit 1](https://github.com/KokunoYumeto/brenner-differentialgeometrie-id/releases/tag/v0.1.0-unit-01) — aset PDF yang sama, dibaca ulang secara publik dan cocok byte demi byte
- [Sumber terjemahan](source/units)
- [Bukti QA Unit 3](qa/unit-03/UNIT_03_QA.md)
- [Backend modular](backend/README.md) — 591 rekaman ber-ID stabil untuk Unit 1–3; lapisan tambahan, bukan syarat untuk membaca buku

PDF memiliki metadata bahasa `id-ID`, pemetaan ToUnicode pada seluruh font, dan teks yang dapat diekstrak pada semua halaman. PDF belum memiliki penandaan struktur; pembaca HTML semantik akan menjadi permukaan aksesibilitas terstruktur utama.

## Sumber, lisensi, dan independensi

Teks sumber digunakan dan diadaptasi berdasarkan CC BY-SA 4.0; atribusi dan riwayat halaman sumber dipertahankan. Setiap media tetap mengikuti lisensi berkasnya sendiri. Edisi ini bukan edisi resmi dan tidak menyiratkan dukungan dari Holger Brenner, Wikiversity, atau para pembuat media.

Rincian hak, atribusi, perubahan, dan batas lisensi media tersedia dalam [`LICENSE.md`](LICENSE.md). Identitas sumber dan proses pembangunan ulang ada dalam [`00_control/AUTHORITY_FREEZE.md`](00_control/AUTHORITY_FREEZE.md), [`qa/unit-01/build.json`](qa/unit-01/build.json), [`qa/unit-02/build.json`](qa/unit-02/build.json), dan [`qa/unit-03/build.json`](qa/unit-03/build.json).

## Membangun ulang pembaca hingga Unit 3

Prasyarat terbuka/offline: Python 3, PowerShell 7 (`pwsh`), MiKTeX/pdfTeX, dan ImageMagick. Setelah dependensi tersedia, jalankan dari akar repositori:

```text
pwsh -NoProfile -File scripts/build_through_unit03.ps1
python scripts/verify_through_unit03_pdf.py --project-root . --pdf output/pdf/geometri-diferensial-manifold-mulus-hingga-unit-03-id.pdf --expected-sha256 aee7f335c8d8110feb7b70448c70680a30700285131d5a1b4e4aeb2f2d04b46a --expected-bytes 3596282 --expected-pages 56 --output qa/unit-03/pdf_structural_qa.json
python scripts/export_backend_v3.py --root . --checkpoint 2026-08-22T06:03:04Z --translation-state visually_checked
python scripts/verify_backend_v3.py --root . --checkpoint 2026-08-22T06:03:04Z --first-jsonl-sha256 e2b1e159b1dff04273ddb0af82e85dc32adbb507f3936881f750867527d6800a --first-csv-sha256 bdd4648d7e104da5f96a20ff85850a8782379f02609c3f29ed88117401032941 --first-manifest-sha256 8810518777d9f08ba4a833784835f669c2b9b592b14f928fd0c895f712abd122
```

Skrip pembangunan menyegarkan seluruh bukti kesetaraan topologi sumber/terjemahan untuk ketiga unit, kemudian menyiapkan media dan TeX portabel, menjalankan dua siklus bersih yang masing-masing terdiri atas tiga lintasan pdfTeX, dan menolak hasil yang tidak identik byte demi byte.

## Melanjutkan produksi

Status tahan-kompaksi berada di [`00_control/GOAL_AND_WORKFLOW.md`](00_control/GOAL_AND_WORKFLOW.md), [`00_control/CURRENT_STATE.md`](00_control/CURRENT_STATE.md), dan [`00_control/CURSOR.json`](00_control/CURSOR.json). Kursor berikutnya ialah Kuliah 4 + Lembar Kerja 4.
