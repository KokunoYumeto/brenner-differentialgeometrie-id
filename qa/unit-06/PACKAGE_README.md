# Geometri Diferensial dan Manifold Mulus — paket sumber hingga Unit 6

Paket ini mendampingi PDF pembaca kumulatif Bahasa Indonesia untuk Kuliah 1–6 dan Lembar Kerja 1–6 dari kursus Holger Brenner, *Differentialgeometrie (Osnabrück 2023)*. Statusnya `active_partial`: kursus inti memiliki 29 pasangan kuliah/lembar kerja, lalu masih memerlukan bank ujian dan dua jembatan asli yang telah ditetapkan.

Mulailah dengan `RELEASE_NOTES_20260822.md` untuk cakupan, identitas byte, keterbatasan aksesibilitas, dan perintah pembangunan. `LICENSE.md` menjelaskan CC BY-SA 4.0 untuk teks/adaptasi dan lisensi per komponen untuk media. `PACKAGE_MANIFEST.json` serta `PACKAGE_CHECKSUMS.sha256` mengikat seluruh isi arsip.

Isi utama:

- `source/`: sumber terjemahan Indonesia yang dapat diedit;
- `authority/expanded/`: sumber Jerman terurai yang benar-benar dipakai untuk enam unit;
- `authority/media/` dan ledger hak: media yang dipakai beserta identitas haknya;
- `build/` dan `scripts/`: jalur pembangunan PDF kumulatif dan verifikasi yang diperlukan;
- `backend/`: ekspor JSONL/CSV stable-ID, skema, dan manifes;
- `qa/` serta `00_control/`: kuitansi terikat-hash, glosarium, ledger koreksi, dan bukti QA.

Dump MediaWiki/XML mentah, PDF saksi historis, build turunan yang dapat dibuat ulang, cache, render sementara, locator privat, kredensial, dan data Git sengaja tidak disertakan. PDF pembaca tersedia sebagai berkas publik utama yang terpisah sehingga tidak diduplikasi di dalam ZIP.

Terjemahan, reflow, backend, dan QA pada batas ini menggunakan **OpenAI Codex gpt-5.6-sol, Ultra** atas arahan pengguna. Model bukan pengarang karya. Kredit Holger Brenner, kontributor halaman, dan setiap pencipta media tetap dipertahankan.
