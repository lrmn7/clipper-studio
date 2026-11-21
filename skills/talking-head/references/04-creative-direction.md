# 04 — Autonomous Creative Direction & Blueprint System

AI Video Editor bertindak sebagai Creative Director mandiri. AI tidak boleh mengajukan pertanyaan teknis yang berulang kepada pengguna (seperti "ingin font apa?", "warna apa?", "efek apa?"), melainkan harus menyimpulkan konsep terbaik secara otonom berdasarkan materi footage dan audiens target.

---

## 1. Katalog 13 Signature Styles

| # | Signature Style | Engine Utama | Karakter Konten | Palet Visual | Motion & Sound |
|---|---|---|---|---|---|
| **1** | **High-Retention Creator** | `fx.py` | Edukasi finansial, tips bisnis, personal branding | Cyan (`#00F0FF`), Kuning Emas (`#FFD166`), Hitam | Zooms punchy, pop cards, UI clicks/pops |
| **2** | **Editorial Magazine / Vox Explainer** | `fx.py` | Isu sosial, ekonomi makro, jurnalisme investigasi | Krem Kertas (`#F4E9D8`), Merah Crimson (`#C83228`), Arang | Garis arsitektural, serif Playfair, tekstur kertas, minimal SFX |
| **3** | **Bold Documentary / Brutalist** | `fx.py` | Isu genting, krisis, pengungkapan bahaya | Hitam pekat, Merah menyala (`#E82434`), Putih | Kontras ekstrem, heavy condensed typography, film grain, dentuman sub-bass |
| **4** | **Apple Glass / Fintech Terminal** | `fx.py` | Teknologi tinggi, crypto, data korporat | Smoked Glass (`#1E293B`), Emerald Green (`#34D399`), Biru Langit | Kartu kaca frosted, live graph counters, soft UI ticks |
| **5** | **Kinetic Viral** | `fx.py` | Hiburan, tren media sosial, audiens muda | Kuning Neon, Ungu Violet, Cyan | Transisi cepat, camera shakes, emoji-free tactile stickers |
| **6** | **Soft Pastel / Wellness** | `fx.py` | Gaya hidup, psikologi, kecantikan, edukasi ramah | Lavender (`#E9D5FF`), Mint lembut, Peach | Pergerakan floating halus, rounded fonts, gentle chimes |
| **7** | **Cyberpunk Neon** | `fx.py` | Gaming, AI revolusi, hardware, crypto | Neon Magenta, Electric Cyan, Deep Space Navy | Rim glow menyala, scanlines, synth zaps |
| **8** | **Social Native / IG Collage** | `fx.py` | Cerita personal, vlog kasual, unboxing | Polaroids, Paper grid, Sticker tags | Stacking animation, playful pops |
| **9** | **Monochrome Film Noir** | `fx.py` | Narasi reflektif, filsafat, motivasi hidup | Skala abu-abu sinematik, Letterbox anamorfik | Kontras cahaya dramatis, minimal serif, atmospheric silence |
| **10** | **Pop Art / Zine Scrapbook** | `fx.py` | Industri kreatif, seni, musik indie | Halftone dots, masking tape kuning, spidol | Crayon sketch, marker doodle, tactile stop-motion |
| **11** | **Editorial Motion Typography** | `typo_fx.py` | Podcast, talkshow mendalam, wawancara tokoh | Space Mono (`#F4E9D8`), Emas (`#FFD166`), Hitam | **ZERO SFX (100% Suara Murni)**, kinetic display raksasa di belakang kepala |
| **12** | **Full Liquid Glass Spatial** | `liquid_glass_fx.py` | Brand premium, fintech masa depan, visual elit | Refraksi kaca optik 3D, Rim light pendar, Smoked bento | Kaca kristalin (`chime`, `drop`, `thud`), depth masking penuh |
| **13** | **Social Value / Contrast Critique** | `fx.py` | Perbandingan sosial (Guru vs Artis), kritik pasar | Biru Muda (`#60C4F8`), Emas (`#FFD166`), Merah (`#E82434`) | Kartu perbandingan kontras, stempel bantahan, lean-in tajam |

---

## 2. Struktur Internal Editing Blueprint

Setelah menganalisis konten, AI membuat **Editing Blueprint** terstruktur:

1. **Overall Visual Direction**: Nama gaya dan alasan pemilihan (misal: "Memilih Style 12 Liquid Glass karena membahas kebijakan suku bunga BI yang membutuhkan kredibilitas finansial tinggi").
2. **Color Palette Tokens**:
   - `primary`: Warna dominan judul / hook
   - `secondary`: Warna aksen data positif / highlight
   - `danger / contrast`: Warna peringatan / angka negatif
   - `surface`: Latar panel kartu grafis
3. **Typography System**:
   - Display/Hook: *Archivo Black* atau *Anton*
   - Editorial/Sub: *Playfair Display Italic* atau *Instrument Serif*
   - Meta/Label/Data: *Space Mono Bold*
   - Body/Caption: *Inter* atau *Poppins*
4. **Motion Language**:
   - Kurva animasi: Spring / Cubic ease-out (tidak linear kaku)
   - Frekuensi event: 1 perubahan visual setiap 2.5–4 detik
5. **Sound Design Direction**:
   - Pilihan: `Strict Clean Audio (Zero SFX)` vs `Subtle Contextual UI SFX (-3dB)`
6. **B-Roll & Infographics Strategy**:
   - Momen di mana kamera pembicara digantikan atau didampingi kartu data grafik.
