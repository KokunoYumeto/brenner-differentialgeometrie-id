# Catatan koreksi sumber Unit 26

Catatan ini tidak mengubah teks edisi. Rumus, latihan, dan solusi Bahasa Indonesia tetap mengikuti byte sumber Jerman yang dibekukan; butir di bawah disimpan untuk satu laporan hulu terdeduplikasi setelah korpus selesai.

1. **Solusi resmi Latihan 26.3 salah tanda.** Solusi terlebih dahulu menyatakan
   `\nabla_\partial(f)=f'+f g'/(2g)`. Syarat horizontal karena itu memberi
   `f'/f=-g'/(2g)`, bukan tanda positif yang tercetak. Solusi yang konsisten
   adalah `f=d/\sqrt g`, bukan `f=d\sqrt g`. Terjemahan mempertahankan rumus
   sumber yang tercetak dan tidak mengoreksinya diam-diam.
2. **Latihan 26.4 memerlukan asumsi komutativitas kerangka.** Trivialisasi
   terdiferensialkan sembarang dengan hasil kali skalar standar memang membuat
   koneksi trivial bersifat metrik, tetapi torsinya pada kerangka
   `V_i,V_j` adalah `-[V_i,V_j]`. Jadi koneksi itu merupakan koneksi
   Levi--Civita hanya jika kerangka trivialitas saling komutatif. Pernyataan
   sumber mengklaim hal itu untuk trivialisasi sembarang.
3. **Solusi resmi Latihan 26.6 mempunyai indeks bebas pada baris terakhir.**
   Suku `\sum_i f_i[V_i,g_jV_j]` masih mempunyai `j` bebas, dan
   `\sum_j g_j[f_iV_i,V_j]` masih mempunyai `i` bebas. Kedua suku tampaknya
   memerlukan penjumlahan ganda `\sum_{i,j}`. Terjemahan mempertahankan
   ekspresi sumber persis.
