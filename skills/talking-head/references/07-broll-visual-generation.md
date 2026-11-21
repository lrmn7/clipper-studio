# 07 — Contextual B-Roll & Visual Asset Generation

B-roll bukan sekadar selingan visual untuk menutupi potongan editing, melainkan instrumen penceritaan (*storytelling device*) yang memperkuat bukti dan mempertajam pemahaman audiens.

---

## 1. Matriks Kebutuhan B-Roll

| Pemicu dalam Transkrip | Jenis B-Roll Paling Tepat | Metode Eksekusi |
|---|---|---|
| **Penyebutan Lembaga / Brand** (Bank Indonesia, Wall Street, Apple) | Logo resmi, kartu identitas lembaga, atau gedung arsitektural | `broll_gen.py` data board atau `logo-link` |
| **Penyebutan Angka Statistik / Finansial** (5,75%, 25 BPS, 30 Juta) | Papan perbandingan data, grafik batang, kurva suku bunga | `broll_gen.py data-compare` / `liquid-glass-graph` |
| **Konsep Abstrak / Hukum Ekonomi** (Rem inflasi, Market gapunya hati) | Kartu kutipan editorial, diagram alur sebab-akibat | `broll_gen.py quote` / `glass-broll` |
| **Daftar Poin / Audit Langkah** (Pertama, Kedua, Ketiga) | Checklist visual bertingkat, stack notifikasi | `checklist` / `apple-toggles` |
| **Cerita Naratif / Tempat** | Foto sinematik lokasi atau peristiwanya | AI Image Generation atau crop footage sekunder |

---

## 2. Hirarki Sourcing Aset Visual

Jika AI Editor membutuhkan visual pendukung:
1. **Prioritas 1: Generator Grafis Lokal (`broll_gen.py`)**
   Gunakan script `broll_gen.py` untuk menghasilkan papan data, kartu KPI, dan kartu kutipan resolusi tinggi langsung di lingkungan lokal tanpa perlu koneksi API eksternal.
2. **Prioritas 2: Generative Image Tool (Jika Tersedia)**
   Jika workspace memiliki tool `generate_image`, buat gambar photorealistik atau ilustratif yang konsisten dengan palet dan tema warna video.
3. **Prioritas 3: Cropping & Reframing Footage yang Ada**
   Potong bagian spesifik dari raw footage (misal: gestur tangan, layar laptop pembicara, close-up ekspresi) lalu berikan efek *Ken Burns Zoom* dan border kaca berbayang.

---

## 3. Format Penempatan B-Roll pada Layar Vertikal

Jangan menimpa seluruh layar dengan video B-roll mentah resolusi rendah. Gunakan komposisi berkelas:
- **`glass-broll`**: Jendela B-roll melayang di sepertiga atas frame dengan border kaca melengkung dan zoom lambat, sementara pembicara tetap terlihat di latar belakang.
- **`broll-split`**: Layar terbelah 50:50 dengan B-roll di bagian atas (lengkap dengan tag stiker harga/topik) dan pembicara di bagian bawah.
- **`halftone-paper`**: Potongan subjek di kanan bawah dengan bayangan halftone, sementara visual B-roll dan teks editorial menempati sisi kiri dan atas.
