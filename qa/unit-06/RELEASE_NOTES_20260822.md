# Geometri Diferensial dan Manifold Mulus — batas Unit 06

Rilis kumulatif Bahasa Indonesia ini berstatus `active_partial` dan mencakup Kuliah 1–6 serta Lembar Kerja 1–6 dari kursus Holger Brenner, *Differentialgeometrie (Osnabrück 2023)*. Pembaca memuat 107 latihan dan seluruh 14 solusi yang benar-benar disediakan sumber untuk enam unit tersebut. Unit 6 sendiri memuat 18 latihan, tidak memiliki petunjuk sumber, dan memuat tiga solusi sumber untuk Latihan 6.2, 6.6, dan 6.9. Tidak ada solusi lain yang diklaim.

Unit 6 memperkenalkan derivatif kovarian sepanjang kurva, medan vektor paralel, transpor paralel, isometri transpor, serta holonomi. Enam belas koreksi sumber yang dapat ditentukan secara matematis atau tipografis dicatat terbuka sebagai O011-CORR-0054 sampai O011-CORR-0069; sumber Jerman yang dibekukan tidak diubah. Audit terminologi bidang juga membandingkan penggunaan teknis Bahasa Indonesia dengan dua sumber akademik Indonesia yang terdokumentasi dan mempertahankan keputusan istilah dalam glosarium serta bukti propagasi.

Sumber terjemahan final Kuliah 6 memiliki SHA-256 `180c553eb556d91ba733e00f012bd0ece36c32e66704c992f0c64244ab6e05e8`; kuitansi pembangunan final memiliki SHA-256 `fa3ff197c5dd03be1aff6766ac1a3e8db779ebf9557091cf1aac4f9fa836f466`; bukti QA matematika pascaperbaikan memiliki SHA-256 `b462de3f20b2a650d3f430660c993b598eba37f8acb0e4cc7187c0e171ee0cc7`. Ketiganya diikat ulang sebelum paket rilis dibuat.

PDF kanonis terdiri atas 105 halaman A4 dengan bingkai teks terpusat dan margin horizontal 22 mm. Dua siklus pembangunan bersih menghasilkan berkas identik byte demi byte. Pemeriksaan matematika, struktur, visual seluruh halaman, hak media, tautan, privasi, dan backend stable-ID telah lulus; kuitansi QA struktural final memiliki SHA-256 `27af0539c1d5e130dd67a935975a2fed450d67b5e8b924e93a6752f34b6f049e`. PDF belum bertag struktur; seluruh 33 font tersemat memiliki ToUnicode dan teks dapat diekstrak pada semua 105 halaman melalui dua parser independen. Pembaca HTML semantik belum termasuk dalam batas ini.

## Berkas publik

1. `geometri-diferensial-manifold-mulus-hingga-unit-06-id.pdf`  
   4765606 byte; SHA-256 `40bf26d196ff04c38c6c99e8e9669a86bb5e6d31124b904b7ad154e7948cdec1`.
2. `geometri-diferensial-manifold-mulus-brenner-id-unit06-20260822.zip`  
   Arsip deterministik dan ringkas yang memuat sumber Indonesia, sumber Jerman terurai yang benar-benar dipakai untuk Unit 1–6, media yang diizinkan, ledger hak dan koreksi, backend, skrip pembangunan, dan bukti QA. PDF dipublikasikan terpisah dan tidak diduplikasi dalam ZIP. Dump MediaWiki/XML mentah, PDF saksi historis, build turunan yang dapat dibuat ulang, kredensial, locator privat, render sementara, cache, dan data Git tidak disertakan.
3. `LICENSE.md`  
   Pernyataan hak, atribusi, lisensi komponen, dan non-endorsement untuk batas Unit 6.
4. `RELEASE_NOTES_20260822.md`  
   Catatan cakupan, QA, aksesibilitas, provenans, dan ketidaklengkapan ini.
5. `FILE_MANIFEST.csv` dan `CHECKSUMS.sha256`  
   Identitas byte dan ruang lingkup hak semua berkas publik.

Identitas byte ZIP dan seluruh unduhan publik dicatat setelah pembacaan ulang anonim pada tiap layanan publikasi.

## Backend

Backend tambahan berisi 1173 rekaman stable-ID. Awalan 969 rekaman Unit 1–5 dipertahankan identik byte demi byte; Unit 6 menambahkan 204 rekaman untuk tiga segmen kuliah, 18 latihan, tiga solusi sumber, konsep, istilah, media dan haknya, artefak, koreksi, QA, serta relasi.

Kuitansi verifikasi backend final memiliki SHA-256 `dc94366f185030611c8032d4a4e1a9fb7847cd6af13e1a2302627e0581573a2e`.

- `backend/records.jsonl`: 702086 byte; SHA-256 `b09862d4b98c475d7e5a3bc92f1e3d72ca771d7f726350b76ab4bd68d6dde5a1`
- `backend/records.csv`: 243301 byte; SHA-256 `5831a7bf3ccc0c18c4246bf713ec6e4c93958465808e7027763e53e170683997`
- `backend/MANIFEST.json`: 12110 byte; SHA-256 `7e3efde35929a615384a104397d5c380b76d27b516b31f32919f907259cd5c44`

## Hak dan independensi

Teks sumber dan adaptasi Indonesia tersedia menurut CC BY-SA 4.0. Media tidak menerima lisensi menyeluruh. Gambar baru Unit 6, `Parallel transport sphere2.svg` karya Silly rabbit, tetap berlisensi CC BY-SA 3.0; seluruh sebelas gambar kumulatif mempertahankan pencipta, sumber, revisi, dan lisensinya sendiri dalam inventaris hak.

Ini adalah adaptasi independen. Rilis ini tidak menyiratkan dukungan Holger Brenner, Wikiversity, Wikimedia Commons, Wikimedia Foundation, atau pencipta media. Terjemahan, penataan ulang, backend, dan QA dibuat melalui alur kerja berbantuan **OpenAI Codex gpt-5.6-sol, Ultra** atas arahan pengguna. Model bukan pengarang karya dan tidak ada tinjauan manusia independen yang diklaim. Seluruh kredit pengarang sumber dan pencipta media tetap dipertahankan.

## Membangun ulang

Dari akar arsip, dengan Python 3, PowerShell 7, MiKTeX/pdfTeX, dan ImageMagick:

```text
pwsh -NoProfile -File scripts/build_through_unit06.ps1
python scripts/verify_through_unit06_pdf.py --project-root . --pdf output/pdf/geometri-diferensial-manifold-mulus-hingga-unit-06-id.pdf --expected-sha256 40bf26d196ff04c38c6c99e8e9669a86bb5e6d31124b904b7ad154e7948cdec1 --expected-bytes 4765606 --output qa/unit-06/pdf_structural_qa.json
python scripts/export_backend_v6.py --root . --checkpoint 2026-08-22T20:55:00Z --translation-state visually_checked
python scripts/verify_backend_v6.py --root .
```

Edisi lengkap tetap memerlukan Unit 7–29, sepuluh ujian, jembatan Lie, jembatan de Rham, 38 item asli ber-solusi yang telah ditetapkan, pembaca HTML semantik, QA akhir, dan versi preservasi lanjutan dalam konsep yang sama.
