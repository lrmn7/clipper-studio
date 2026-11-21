# 03 — Semantic Transcription & Word-Level Analysis

Transkripsi bukan sekadar membuat teks subtitle yang berjalan secara mekanis. AI Video Editor harus memahami isi pembicaraan secara semantik, mengenali bobot retorika kalimat, dan menghubungkan kata demi kata dengan keputusan visual yang tepat.

---

## 1. Word-Level Timestamps & Koreksi Konteks

Menggunakan Whisper (`faster-whisper` atau `mlx-whisper`), audio dipecah menjadi timestamp per kata (`.words.json`):

```json
[
  {"w": "Kenapa", "s": 0.00, "e": 0.38},
  {"w": "Bank", "s": 0.40, "e": 0.88},
  {"w": "Indonesia", "s": 0.90, "e": 1.22},
  {"w": "menaikkan", "s": 1.24, "e": 1.84},
  {"w": "suku", "s": 1.88, "e": 2.02},
  {"w": "bunga?", "s": 2.04, "e": 2.60}
]
```

### Koreksi Otomatis Istilah Teknis
Sebelum menyusun editing, transkrip mentah wajib diaudit terhadap:
- **Nama Lembaga & Brand**: "bang Indonesia" → "Bank Indonesia", "BCA", "OJK", "The Fed", "Apple".
- **Angka & Persentase**: "lima koma tujuh lima persen" → "5,75%", "enam persen" → "6,00%".
- **Istilah Finansial / Teknis**: "dua puluh lima BPS" → "25 bps", "yield", "depresiasi", "inflasi".

---

## 2. Pemetaan Struktur Retorika Kalimat

AI Editor mengelompokkan kata-kata ke dalam 7 kategori editorial:

| Kategori | Pola Semantik | Keputusan Visual / Editorial |
|---|---|---|
| **1. Hook (0–3.5s)** | Pertanyaan pemicu, pernyataan kontroversial, klaim mengejutkan | Judul display raksasa di belakang kepala (`one-big-slam`, `hook-card`, `glass-hook`) + zoom punch-in |
| **2. Problem / Question** | "Kenapa...", "Mengapa...", "Adakah masalah...", "Bagaimana jika..." | Spotlight meredupkan studio + kartu pertanyaan beraksen warna |
| **3. Data & Metrics** | Persentase (`%`), nominal uang (`Rp`, `Juta`, `USD`), angka rasio | Kartu perbandingan data (`data-compare`), grafik cairan (`liquid-glass-graph`), angka raksasa |
| **4. Contrast & Comparison** | "Bukan... tapi...", "Naik vs Turun", "Sebelumnya vs Baru", "Guru vs Artis" | Split visual, highlight kontras warna (Merah vs Hijau), stempel bantahan (`reject-stamp`) |
| **5. Core Emphasis / Punchline** | "Jadi rem", "Market gak punya hati", "Dolar jangan kabur", "Bukan inflasi" | `pop-word` di belakang kepala (warna merah/emas) + kamera lean-in cepat |
| **6. Enumeration / Lists** | "Pertama... kedua...", "Ada tiga alasan...", "Satu... dua..." | Checklist bertingkat (`checklist`, `apple-toggles`, `rollout`) |
| **7. Climax & Conclusion** | "Bisa kita simpulkan...", "Artinya...", "Pelajaran pentingnya..." | Kartu kesimpulan (`verdict`, `tape-label`) + outro kartu ajakan |

---

## 3. Prinsip Anti-Karaoke

> **HINDARI GAYA KARAOKE / LIRIK LAGU BERJALAN YANG MEMUSINGKAN.**

1. **Bukan Setiap Kata Dianimasikan**:
   Menyorot atau membesarkan setiap kata yang diucapkan justru merusak konsentrasi audiens dan menurunkan persepsi profesionalitas konten.
2. **Chunking Kalimat yang Nyaman Dibaca**:
   Kelompokkan caption dalam frasa 2–4 kata yang selaras dengan ritme pernapasan pembicara.
3. **Penyembunyian Otomatis Saat Ada Kartu Grafis**:
   Ketika kartu data besar, bento, atau B-roll tampil di layar, **matikan subtitle sementara** (`hide` parameter pada `captions`) agar layar tidak penuh sesak (*visual clutter*).
