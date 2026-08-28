# Geometri Diferensial dan Manifold Mulus — batas Unit 22

Versi `2026.08.28-unit22` adalah rilis `active_partial` kumulatif yang memuat
Kuliah 1–22 dan Lembar Kerja 1–22 dari 29 pasangan inti sumber. Batas ini
memperluas Unit 19 tanpa mengubah atau menghilangkan materi publik yang telah
diterima. Tujuh pasangan inti, sepuluh formulir ujian resmi, dan dua jembatan
asli terbatas masih berada di luar cakupan checkpoint ini.

Artefak pembaca utama adalah PDF A4 terpusat 345 halaman dan HTML semantik yang
dapat menyesuaikan lebar desktop maupun seluler. Keduanya mempertahankan seluruh
457 soal dalam urutan sumber, tepat 64 solusi yang benar-benar disediakan
sumber, dan 31 media beratribusi. Tidak ada lapisan petunjuk umum atau solusi
lengkap yang disiratkan. Unit 20–22 menambahkan 63 soal, 10 solusi sumber, dan
5 media terhadap batas Unit 19.

Backend kumulatif memuat 4.324 record stable-ID. Prefiks publik Unit 1–19
sebanyak 3.747 record dipertahankan identik byte demi byte; 577 record baru
menutup Unit 20–22 beserta relasi sumber, pembaca, hak, koreksi, dan QA.
Ekspor JSONL/CSV lulus validasi skema, resolusi referensi, keunikan ID,
proyeksi CSV, preservasi prefiks, serta pengulangan deterministik.

PDF dibuktikan oleh dua siklus build bersih yang identik byte demi byte dan
inspeksi visual seluruh 345 halaman. Gate struktural mencatat 42 diagnostik
kotak TeX yang tidak menghalangi; pemeriksaan batas badan halaman dan inspeksi
render penuh menemukan nol kliping atau tumbukan. PDF memiliki bahasa `id-ID`,
pemetaan ToUnicode, dan teks yang dapat diekstrak pada setiap halaman, tetapi
belum bertag. HTML semantik merupakan permukaan aksesibel/reflowable utama.
Pengujian Chromium nyata pada desktop dan seluler memeriksa 7.261 ekspresi
MathJax, navigasi tautan-dalam, media, luapan rumus lokal, serta kontrol
Putar/Hentikan tanpa galat MathJax atau konsol.

Rilis disusun reader-first: PDF tampil sebagai aset utama, diikuti HTML ZIP,
paket sumber ringkas yang dapat dipakai untuk melanjutkan pekerjaan, lisensi,
catatan rilis, manifes, dan checksum. Kredensial, cache, render sementara,
duplikasi build, dan dump sumber mentah besar tidak termasuk.

Teks sumber dan adaptasi Indonesia tetap CC BY-SA 4.0. Media mempertahankan hak
per komponennya; tidak ada lisensi media menyeluruh yang diwariskan. Adaptasi
ini independen dan bukan edisi resmi atau dukungan dari penulis, Wikiversity,
Wikimedia Commons, Wikimedia Foundation, maupun pencipta media. Pekerjaan
komputasional pada batas ini menggunakan **OpenAI Codex gpt-5.6-sol, Ultra**
atas arahan pengguna; seluruh kredit sumber tetap berlaku.
