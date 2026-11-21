# 06 — Motion Graphics, Typeline & Infographics

Dalam video edukasi, finansial, dan storytelling modern, angka dan konsep abstrak tidak boleh dibiarkan hanya diucapkan secara lisan. Motion graphics dan infografis berfungsi menerjemahkan data mentah menjadi pemahaman visual instan (*cognitive ease*).

---

## 1. Modul Infografis Utama

### A. Data Comparison Board (`data-compare`)
Menampilkan perbandingan kondisi lama vs kondisi baru dengan badge delta:
- **Header**: Nama lembaga / parameter (misal: `BANK INDONESIA | BI-RATE`)
- **Kolom Kiri**: Data sebelumnya (`5,75%`, `SEBELUMNYA`)
- **Kolom Kanan**: Data baru dengan warna aksen hijau/biru (`6,00%`, `SUKU BUNGA BARU`)
- **Delta Badge**: Selisih eksplisit (`+25 BPS (KENAIKAN TIBA-TIBA)`)

### B. Liquid Glass Graph (`liquid-glass-graph`)
Panel kaca smoked transparan yang melayang di bawah dagu dengan:
- Label parameter
- Garis grafik yang menanjak dinamis dari nilai awal ke nilai akhir
- Angka counter yang berhitung secara halus mengikuti kurva easing

### C. Dashboard Bento Grid (`glass-bento`)
Tiga kartu analitik yang tersusun rapi:
1. Donut Chart (misal: `29% Portofolio`)
2. KPI Counter besar (misal: `Rp 672 Juta`)
3. Bar Chart historis 3 periode

### D. Audit Checklist & Toggles (`checklist`, `apple-toggles`, `todo`)
Untuk memecah penjelasan yang terdiri dari beberapa poin:
- **`checklist`**: Daftar tugas dengan indikator loading berputar yang kemudian tercentang hijau satu per satu saat pembicara menyebut poin tersebut.
- **`apple-toggles`**: Panel switch iOS di mana tombol switch berpindah ke posisi ON bersinar hijau saat kata kunci disebut.

---

## 2. Typeline & Kinetic Typography Animations (Style 11)

Modul khusus dari engine `typo_fx.py`:
- **`one-big-slam`**: Judul raksasa menghantam kanvas dari skala besar (1.8x) ke 1.0x dengan elastic rebound di belakang kepala.
- **`splits`**: Dua baris tipografi membelah bersih ke kiri dan kanan dari garis rambut aksen emas.
- **`heavy-landing`**: Tipografi angka/judul jatuh vertikal karena gravitasi, penyok elastis saat menyentuh dasar frame, lalu memantul tegak.
- **`rollout`**: Garis arsitektural vertikal di kiri dengan baris tipografi yang menggulung keluar satu per satu.
- **`dot-hop`**: Titik aksen emas melompat secara parabolik di antara pilar kata kunci utama.
- **`sticker-stack`**: Tiga kartu tag matte bertumpuk miring secara berurutan.
- **`slingshot`**: Teks ditarik ke belakang lalu melesat elastis melintasi frame.
- **`traced-outline`**: Garis outline huruf berongga digambar progresif lalu terisi warna solid dari bawah ke atas.
- **`plucked-string`**: Kawat horizontal bergetar teredam seperti senar bas saat kata kunci penting disebut.
- **`tumbling-letter`**: Huruf display jatuh berputar elastis ke tempatnya.

---

## 3. Aturan Editorial Infografis
1. **Fungsi Informasi Sebelum Estetika**: Jangan membuat grafik rumit jika data yang dibahas sangat sederhana.
2. **Durasi yang Cukup untuk Membaca**: Kartu data harus tampil di layar minimal selama 3.5 detik agar audiens sempat menyerap angka dan maknanya.
3. **Penyelarasan Warna Semantik**:
   - Hijau (`#34D399`): Pertumbuhan positif, kenaikan aman, status terverifikasi.
   - Merah (`#E82434`): Risiko, inflasi tinggi, pelemahan kurs, larangan.
   - Emas (`#FFD166`): Nilai tinggi, sorotan utama, kesimpulan.
   - Cyan (`#00F0FF`): Netral, teknologi, parameter resmi.
