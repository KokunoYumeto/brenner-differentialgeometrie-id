# Geometri Diferensial dan Manifold Mulus — batas Unit 07

Rilis kumulatif Bahasa Indonesia ini berstatus `active_partial` dan mencakup
Kuliah 1–7 serta Lembar Kerja 1–7 dari kursus Holger Brenner,
*Differentialgeometrie (Osnabrück 2023)*. Pembaca memuat 126 latihan dan
seluruh 17 solusi yang benar-benar disediakan sumber untuk tujuh unit tersebut.
Unit 7 sendiri memuat 19 latihan (14 latihan dan lima bertanda nilai), tidak
memiliki petunjuk sumber, dan memuat tiga solusi sumber untuk Latihan 7.4, 7.7,
dan 7.13. Tidak ada solusi lain yang diklaim.

Unit 7 memperkenalkan proyeksi stereografis, transisi peta, manifold topologis,
manifold diferensiabel, atlas, dan pemetaan diferensiabel. Tiga media statis
baru dan dua permukaan GIF interaktif Commons dipertahankan dengan lisensi,
pencipta, revisi, URL, dan hash masing-masing. Perubahan bahasa yang terikat
topologi dicatat sebagai `O011-TRANS-0070` dan `O011-TRANS-0071`; perbaikan
kompatibilitas TeX untuk nama pencipta Unicode dicatat sebagai
`O011-TEX-0072`. Sumber Jerman yang dibekukan tidak diubah.

Sumber terjemahan final Kuliah 7 memiliki SHA-256
`5faec64b0b20a6999e61fc3fa6a32db812e324d1e8a272d1978c67bc76c3c7b0`;
Worksheet 7 memiliki SHA-256
`af223f98696a9353e7967d3ac150a8f2f5de3c49bef506c69fe0d452e7717658`.
Kuitansi pembangunan final memiliki SHA-256
`bb3b6bc858948291b0fa6a000c57761aef3d055fceae43000b303b1aaaacf08d`.
Kuitansi QA PDF independen memiliki SHA-256
`06b50304e1ac3f7873c054b6607f689db08f6e65fb583beffaaeb91e7bd39ef0`.
Kuitansi QA struktural lengkap memiliki SHA-256
`b564eaf9b668c056092963158ff2f70aad1a29e254dfa98a1c0c9d43c5a6b649`.
Kuitansi QA matematika memiliki SHA-256
`66639b0c5a90bd4eba34078ee6f5229ca0fab1aad4c05f641d2c3dc7912e6345`.

PDF kanonis terdiri atas 117 halaman A4 dengan bingkai teks terpusat dan margin
horizontal 22 mm. Dua siklus pembangunan bersih menghasilkan berkas identik
byte demi byte. Pemeriksaan matematika, struktur, visual berbatas, hak media,
tautan, privasi, interaktif, dan backend stable-ID telah lulus. PDF belum
bertag struktur; seluruh 33 font resource tersemat (28 nama unik) memiliki
ToUnicode dan teks dapat diekstrak pada semua 117 halaman melalui dua parser
independen. Pembaca HTML
semantik belum termasuk dalam batas ini.

## Berkas publik

1. `geometri-diferensial-manifold-mulus-hingga-unit-07-id.pdf` — pembaca utama;
   4,950,232 byte; SHA-256
   `8c2cf76230b45d66a8236c0cd92a048809ff5ec0cce343132dd902684cb05ec6`.
2. `geometri-diferensial-manifold-mulus-brenner-id-unit07-20260823.zip` —
   arsip deterministik dan ringkas yang memuat sumber Indonesia, sumber Jerman
   terurai yang benar-benar dipakai untuk Unit 1–7, media yang diizinkan,
   ledger hak dan koreksi, backend, skrip pembangunan, dan bukti QA. PDF
   dipublikasikan terpisah dan tidak diduplikasi dalam ZIP.
3. `LICENSE.md` — pernyataan hak, atribusi, lisensi komponen, dan
   non-endorsement.
4. `RELEASE_NOTES_20260823.md` — catatan cakupan, QA, aksesibilitas,
   provenans, dan ketidaklengkapan.
5. `FILE_MANIFEST.csv` dan `CHECKSUMS.sha256` — identitas byte dan ruang
   lingkup hak semua berkas publik.

## Backend and reproducibility

The final reader-bound backend contains **1,363 records**: the Unit 1–6 prefix
of 1,173 records remains byte-identical, and Unit 7 adds 190 records (25 unit,
4 segment, 5 asset, 5 rights, 29 artifact, 16 QA-event, 3 correction, and 103
relation records). The final JSONL is 812,882 bytes, SHA-256
`d9d51a46b84368f50a211a31263bafe8f1588f8e62a5fa4b496b2ff45903b912`; the CSV
is 288,506 bytes, SHA-256
`c301009770e1c523d046585c0c83947cab6f856b32b83890d361a919fed5a958`; the
manifest is 11,297 bytes, SHA-256
`1a950183a66bbc837cff27f34cf2f1fc838ad181bc4fbf16e8bd758c1df2068d`; and the
independent backend QA receipt is 3,113 bytes, SHA-256
`387afdb9eef916f34f3b7764bddf1de85dd23bcfef5b640ac7e1585a434588e1`.
Rebuild with PowerShell 7,
Python 3, MiKTeX/pdfTeX, and ImageMagick:

```text
pwsh -NoProfile -File scripts/build_through_unit07.ps1
python scripts/verify_unit07_pdf_boundary.py --root . --pdf output/pdf/geometri-diferensial-manifold-mulus-hingga-unit-07-id.pdf --output qa/unit-07/PDF_BOUNDARY_QA.json
python scripts/export_backend_v7.py --root . --checkpoint 2026-08-23T18:00:00Z
python scripts/verify_backend_v7.py --root .
```

The complete edition still requires Units 8–29, the ten official example-exam
forms, the Lie and de Rham bridges, 38 original solution-bearing items, the
semantic HTML reader, final QA, and later versions in this same preservation
lineage.

Translation, reflow, backend, and QA at this boundary used **OpenAI Codex gpt-5.6-sol, Ultra** under user direction. This is an independent adaptation;
it does not imply endorsement by Holger Brenner, Wikiversity, Wikimedia
Commons, the Wikimedia Foundation, or media creators. All source and human
contributor credits remain intact.
