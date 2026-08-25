# Geometri Diferensial dan Manifold Mulus — paket sumber hingga Unit 7

Paket ini mendampingi PDF pembaca kumulatif Bahasa Indonesia untuk Kuliah 1–7
dan Lembar Kerja 1–7 dari kursus Holger Brenner, *Differentialgeometrie
(Osnabrück 2023)*. Statusnya `active_partial`: kursus inti memiliki 29 pasangan
kuliah/lembar kerja, lalu masih memerlukan bank ujian dan dua jembatan asli yang
telah ditetapkan.

Mulailah dengan `RELEASE_NOTES_20260823.md` untuk cakupan, identitas byte,
keterbatasan aksesibilitas, dan perintah pembangunan. `LICENSE.md` menjelaskan
CC BY-SA 4.0 untuk teks/adaptasi dan lisensi per komponen untuk media.
`PACKAGE_MANIFEST.json` serta `PACKAGE_CHECKSUMS.sha256` mengikat seluruh isi
arsip.

Isi utama:

- `source/`: sumber terjemahan Indonesia yang dapat diedit;
- `authority/expanded/`: sumber Jerman terurai yang benar-benar dipakai untuk
  unit yang diterjemahkan;
- `authority/media/` dan ledger hak: media yang dipakai beserta identitas haknya;
- `build/` dan `scripts/`: jalur pembangunan PDF kumulatif dan verifikasi;
- `backend/`: ekspor JSONL/CSV stable-ID, skema, dan manifes;
- `qa/` serta `00_control/`: kuitansi terikat-hash, glosarium, ledger koreksi,
  dan bukti QA.

Dump MediaWiki/XML mentah, PDF saksi historis, build turunan yang dapat dibuat
ulang, kredensial, locator privat, render sementara, cache, dan data Git sengaja
tidak disertakan. PDF pembaca tersedia sebagai berkas publik utama yang
terpisah sehingga tidak diduplikasi di dalam ZIP. Dua GIF Unit 7 dipertahankan
sebagai sumber interaktif yang dapat diunduh; PDF menyediakan tautan Commons
yang dapat diklik.

Terjemahan, reflow, backend, dan QA pada batas ini menggunakan **OpenAI Codex
gpt-5.6-sol, Ultra** atas arahan pengguna. Model bukan pengarang karya. Kredit
Holger Brenner, kontributor halaman, dan setiap pencipta media tetap
dipertahankan.
