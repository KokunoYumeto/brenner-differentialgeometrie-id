# Geometri Diferensial dan Manifold Mulus — batas Unit 05

Revisi preservasi `r1` mengganti hanya arsip sumber agar dua locator jalur mesin lokal tidak ikut dipublikasikan. Byte PDF, cakupan matematika, terjemahan, backend, hak komponen, dan hasil QA tidak berubah. Revisi ini tetap berada dalam konsep Zenodo yang sama.

Rilis kumulatif Bahasa Indonesia ini mencakup Kuliah 1–5 dan Lembar Kerja 1–5 dari kursus Holger Brenner, Differentialgeometrie (Osnabrück 2023). Pembaca memuat 89 latihan dan seluruh sebelas solusi yang benar-benar disediakan sumber untuk lima unit tersebut. Unit 5 sendiri memuat 15 latihan, satu petunjuk sumber pada Latihan 5.13, dan satu solusi sumber untuk Latihan 5.1. Tidak ada solusi lain yang diklaim.

Unit 5 memperkenalkan kelengkungan utama dan arahnya, kelengkungan rata-rata, kelengkungan Gauss dan Gauss–Kronecker, kelengkungan normal, rumus Euler, dan irisan normal. Delapan koreksi sumber yang dapat ditentukan secara matematis dicatat terbuka sebagai O011-CORR-0046 sampai O011-CORR-0053; sumber Jerman yang dibekukan tidak diubah.

PDF kanonis terdiri atas 86 halaman A4 dengan bingkai teks terpusat dan margin horizontal 22 mm. Dua siklus pembangunan bersih menghasilkan berkas identik byte demi byte. Pemeriksaan matematika, struktur, visual seluruh halaman, hak media, tautan, privasi, dan backend stable-ID telah lulus. PDF belum bertag struktur; semua 29 font tersemat memiliki ToUnicode dan teks dapat diekstrak pada semua halaman. Pembaca HTML semantik belum termasuk dalam batas ini.

## Berkas publik

1. geometri-diferensial-manifold-mulus-hingga-unit-05-id.pdf  
   4,385,370 byte; SHA-256 44ef3bc7f4c9de8a9ffd3a747ea71c2102de6f26814718492bc63fd40e4af5ce.
2. geometri-diferensial-manifold-mulus-brenner-id-unit05-20260822.zip  
   Arsip deterministik sumber Indonesia, sumber/provenans Jerman, media yang diizinkan, ledger hak dan koreksi, backend, skrip pembangunan, dan bukti QA. PDF dipublikasikan terpisah dan tidak diduplikasi dalam ZIP. Berkas kredensial, render sementara, repositori Git, dan PDF saksi historis tidak disertakan.
3. RELEASE_NOTES_20260822.md  
   Catatan lingkup, hak, keterbatasan, identitas pembaca, dan instruksi pembangunan ini.

Identitas byte final ZIP dan ketiga unduhan publik dicatat dalam kuitansi publikasi Zenodo setelah pembacaan ulang anonim.

## Backend

Backend tambahan berisi 969 rekaman. Awalan 813 rekaman Unit 1–4 tetap identik byte demi byte; Unit 5 menambahkan 156 rekaman yang memetakan tiga segmen kuliah, 15 latihan, satu petunjuk, satu solusi sumber, konsep, istilah, media dan haknya, artefak, koreksi multi-target, QA, serta relasi.

- backend/records.jsonl: 576,960 byte; SHA-256 bdd82d81cdac5cf30338d8fa0705189808ec4d746995127d02cbf4a248333227
- backend/records.csv: 201,742 byte; SHA-256 ab7c40867434141e5f0a102db6b9a92a73677a3a946d96c3adbd925e77130592
- backend/MANIFEST.json: 9,439 byte; SHA-256 d2be7db771da7409da1cb085e06b609735b9b93916d090a7404a1e56f160a1ac

## Hak dan independensi

Teks sumber dan adaptasi Indonesia tersedia menurut CC BY-SA 4.0. Media tidak menerima lisensi menyeluruh. Gambar baru Unit 5, Minimal surface curvature planes-de.svg karya Eric Gaba (Sting), tetap berlisensi CC BY-SA 3.0; seluruh sepuluh gambar kumulatif mempertahankan pencipta, sumber, dan lisensinya sendiri dalam inventaris hak.

Ini adalah adaptasi independen. Rilis ini tidak menyiratkan dukungan Holger Brenner, Wikiversity, Wikimedia Commons, Wikimedia Foundation, atau pencipta media. Terjemahan, penataan ulang, backend, dan QA dibuat melalui alur kerja berbantuan Codex atas arahan pengguna; tidak ada tinjauan manusia independen yang diklaim.

## Membangun ulang

Dari akar arsip, dengan Python 3, PowerShell 7, MiKTeX/pdfTeX, dan ImageMagick:

    pwsh -NoProfile -File scripts/build_through_unit05.ps1
    python scripts/verify_through_unit05_pdf.py --project-root . --pdf output/pdf/geometri-diferensial-manifold-mulus-hingga-unit-05-id.pdf --expected-sha256 44ef3bc7f4c9de8a9ffd3a747ea71c2102de6f26814718492bc63fd40e4af5ce --expected-bytes 4385370 --expected-pages 86 --output qa/unit-05/pdf_structural_qa.json
    python scripts/export_backend_v5.py --root . --checkpoint 2026-08-22T17:30:00Z --translation-state visually_checked

Kuitansi terminal lokal berada di qa/unit-05/UNIT_05_QA.md. Edisi lengkap tetap memerlukan Unit 6–29, sepuluh ujian, jembatan Lie, jembatan de Rham, materi asli terencana, pembaca HTML semantik, QA akhir, dan versi Zenodo lanjutan dalam konsep yang sama.
