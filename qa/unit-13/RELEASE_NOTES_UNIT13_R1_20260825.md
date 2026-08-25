# Geometri Diferensial dan Manifold Mulus — batas Unit 13, revisi paket sumber

Versi `2026.08.25-unit13-r1` adalah revisi korektif paket sumber untuk rilis
`active_partial` Kuliah 1–13 dan Lembar Kerja 1–13. Konten pembaca dan byte PDF
serta HTML yang telah divalidasi tidak berubah dari record Zenodo 22096736.
PDF tetap 213 halaman A4 terpusat; HTML tetap memuat 287 soal, tepat 35 solusi
yang tersedia pada sumber, 21 media tertanam, tiga animasi sumber yang dapat
diunduh, dan 4.598 ekspresi matematika. Backend tetap memuat 2.604 record,
dengan prefiks publik 1.888 record Unit 1–10 yang identik byte demi byte dan
ekstensi 716 record untuk Unit 11–13.

Perubahan r1 terbatas pada paket sumber, dokumentasi paket, manifes/checksum,
dan metadata rilis. Paket sumber pendahulu tidak memuat seluruh kontrol tahan
kompaksi dan beberapa dependensi inkremental Unit 10 yang dibutuhkan oleh
skrip Unit 13. r1 menambahkan delapan kontrol publik, seluruh 48 manifes
koreksi terlindungi kumulatif, semua masukan transitif kuitansi build Unit 10
dan Unit 13, pohon output HTML Unit 10, PDF Unit 10, seluruh rilis tujuh berkas
Unit 10, backend/skema, QA yang diperlukan, serta skrip dan aset yang dipakai.

Paket r1 menolak locator privat, kredensial, cache, render sementara, dump
besar yang tidak diperlukan, dan `qa/unit-05/ZENODO_PUBLICATION_RECEIPT.md`.
Setiap ZIP bersifat deterministik, diuji CRC, diinventarisasi, dipindai untuk
locator/kredensial pada teks termasuk anggota ZIP bersarang, dan diikat SHA-256.

Setelah mengekstrak source ZIP ke direktori kosong, jalankan dari akarnya:

```powershell
pwsh -NoProfile -File scripts/build_through_unit13.ps1
python scripts/verify_through_unit13_pdf.py
python scripts/export_html_v13.py --root . --output output/html/unit-13 --replace
python scripts/verify_html_v13.py --root . --output output/html/unit-13
python scripts/export_backend_v13.py --root . --checkpoint 2026-08-24T20:50:06Z --translation-state mathematically_reviewed
python scripts/verify_backend_v13.py --root .
```

Teks sumber dan adaptasi Indonesia tetap CC BY-SA 4.0. Media mempertahankan
hak per komponennya; tidak ada lisensi media menyeluruh yang diwariskan.
Adaptasi ini independen dan bukan edisi resmi atau dukungan dari penulis,
Wikiversity, Wikimedia Commons, Wikimedia Foundation, maupun pencipta media.
Pekerjaan komputasional pada revisi ini menggunakan **OpenAI Codex gpt-5.6-sol, Ultra**
atas arahan pengguna; semua kredit sumber tetap berlaku.
