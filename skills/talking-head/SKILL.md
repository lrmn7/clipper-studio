---
name: reels-editor
description: "Intelligent AI Video Editor, Creative Director, Motion Designer & Sound Designer for vertical videos (Instagram Reels, TikTok, YouTube Shorts). Understands raw footage visual framing and acoustics, transcribes speech with Whisper word-level timestamps, semantically analyzes hooks, data, questions and climaxes, autonomously directs scene-by-scene editing across 13 signature styles (82+ effects, kinetic typography, Liquid Glass), enforces strict safe zones and behind-head depth masking, and ALWAYS provides keyframe contact sheets and proxy video previews before final broadcast rendering. Trigger with /reels-editor."
---

# Reels AI Director & Intelligent Video Editing System

Bertindak sebagai **Professional Video Editor, Motion Designer, Creative Director, dan Sound Designer** otonom saat menerima raw footage. Tidak pernah mengedit secara generik atau menggunakan subtitle karaoke yang memusingkan.

Alur kerja inti yang wajib dipatuhi:
**Footage â”€â”€â–º Probe & Understand â”€â”€â–º Trim â”€â”€â–º Reframe â”€â”€â–º Transcribe & Semantics â”€â”€â–º Autonomous Blueprint â”€â”€â–º B-Roll/Infographics â”€â”€â–º PREVIEW (Stills & Proxy) â”€â”€â–º Final Render.**

Semua path relatif terhadap folder skill ini (`<SKILL>`). Script terletak di `<SKILL>/scripts/`.

---

## 0. Setup & Validasi Lingkungan (Lintas Platform)

Persyaratan: Python 3.10+, `ffmpeg` dan `ffprobe` terdaftar di PATH.
Gunakan Python environment aktif (`.venv\Scripts\python.exe` di Windows atau `.venv/bin/python` di macOS/Linux):

```bash
# Validasi dan instalasi dependensi otomatis (Windows/macOS/Linux)
python scripts/setup.py
```

---

## 1. Analisis Footage & Pemahaman Spasial

Jalankan probe visual dan pelacakan geometri wajah:

```bash
python scripts/director.py analyze input.mp4 --out-plan work/plan.json
```

- **Rasio Aspek**: Jika horizontal (16:9), siapkan reframe cerdas ke 1080Ã—1920.
- **Geometri Wajah**: AI mendeteksi koordinat tengah wajah (`cx, cy`) dan lebar wajah (`fw`) dengan YuNet.
- **Ruang Negatif**: Mengidentifikasi ruang kosong di atas kepala dan di bawah dagu untuk penempatan teks yang aman.
*(Detail lengkap baca: [02-footage-understanding.md](references/02-footage-understanding.md))*

---

## 2. Pangkas Jeda Kosong (Dead-Air Optimization)

Pangkas jeda hening tanpa suara > 0.35s menggunakan `trim.py`:

```bash
python scripts/trim.py input.mp4 work/trim.mp4 --gap 0.4 --keep 0.16
```
- Menjaga napas mikro (0.15â€“0.25s) sebelum kalimat penekanan penting agar terdengar alami.
*(Detail lengkap baca: [01-core-workflow.md](references/01-core-workflow.md))*

---

## 3. Auto-Reframe ke Vertikal 9:16 (Jika Footage Horizontal)

Jika footage asli horizontal (1920Ã—1080):

```bash
python scripts/reframe_reels.py work/trim.mp4 work/reels.mp4 --tau 0.55
```
- Menggunakan pelacakan wajah YuNet dengan filter temporal Gaussian bilateral sehingga subjek selalu berada di titik fokus frame.

---

## 4. Transkripsi & Analisis Semantik Kata demi Kata

Jalankan `words.py` untuk menghasilkan timestamp per kata:

```bash
python scripts/words.py work/reels.mp4
# Hasil tersimpan di work/reels.words.json
```

1. **Audit Istilah**: Koreksi salah dengar nama lembaga, brand, angka, dan persentase (misal: "Bank Indonesia", "5,75%", "25 bps").
2. **Ekstraksi Retorika Kalimat**:
   - **Hook (0.0â€“3.5s)**: Klaim pemicu rasa penasaran atau pertanyaan tajam.
   - **Pertanyaan / Masalah**: Bagian yang memerlukan spotlight dramatis.
   - **Data & Angka**: Memerlukan kartu data (`data-compare`) atau grafik cairan (`liquid-glass-graph`).
   - **Kontras & Bantahan**: Momen "bukan... tapi..." (`reject-stamp`, `huge-strike`, `pop-word`).
   - **Daftar Poin**: Memerlukan `checklist` atau `apple-toggles`.
   - **Kesimpulan / Climax**: Putusan akhir dan ajakan bertindak (`verdict`, `tape-label`, `tap`).
*(Detail lengkap baca: [03-transcription-semantics.md](references/03-transcription-semantics.md))*

---

## 5. Penentuan Creative Direction & Blueprint Otonom

AI menentukan gaya visual terbaik secara mandiri tanpa menginterogasi pengguna:

| Karakter Konten | Signature Style | Engine Utama | Karakter Visual & Audio |
|---|---|---|---|
| **Edukasi Finansial / Data / Perbankan** | **Style 12: Full Liquid Glass** | `liquid_glass_fx.py` | Refraksi kaca 3D, bento grid, audio kaca kristalin |
| **Podcast / Talkshow / Isu Mendalam** | **Style 11: Editorial Motion Typography** | `typo_fx.py` | Display kinetik mewah di belakang kepala, **ZERO SFX** |
| **Kreator Berenergi Tinggi / Bisnis** | **Style 1: High-Retention Creator** | `fx.py` | Punchy zooms, pop-word, kartu data, UI pops |
| **Kritik Sosial / Perbandingan Nilai** | **Style 13: Contrast Critique** | `fx.py` | Stempel bantahan, kartu perbandingan kontras |
| **Isu Krisis / Investigasi / Dokumen** | **Style 3: Bold Documentary** | `fx.py` | Hitam/merah pekat, heavy condensed type, dentuman sub-bass |

*(Detail 13 Signature Styles baca: [04-creative-direction.md](references/04-creative-direction.md))*

---

## 6. Pembuatan B-Roll & Infografis Kontekstual

Jika transkrip menyebut angka statistik, perbandingan, atau kutipan penting, buat aset visual beresolusi tinggi menggunakan `broll_gen.py`:

```bash
# Papan perbandingan data ekonomi
python scripts/broll_gen.py data-compare --title "BANK INDONESIA | BI RATE" --v1 "5.75%" --sub1 "Sebelumnya" --v2 "6.00%" --sub2 "Suku Bunga Baru" --delta "+25 BPS" --out assets/broll/bi_rate.png

# Kartu KPI Angka Besar
python scripts/broll_gen.py kpi --label "GAP PASAR" --val "10X" --sub "Artis vs Guru" --out assets/broll/kpi_gap.png
```
*(Detail strategi visual baca: [07-broll-visual-generation.md](references/07-broll-visual-generation.md))*

---

## 7. Perlindungan Wajah & Safe Zone Platform (MANDATORY)

- **Top Safe Line**: `y >= 13.5%` (260px pada 1080Ã—1920) â€” Bebas dari status bar dan tab feed.
- **Bottom Safe Line**: `y <= 77.2%` (1485px pada 1080Ã—1920) â€” Bebas dari username, caption, dan audio bar.
- **Right Rail**: Pada paruh bawah frame, `x <= 83.5%` (900px) â€” Bebas dari kolom tombol Like/Komentar/Share.
- **Face & Eye Protection**:
  Semua teks display besar diletakkan di belakang kepala (`behind: true`, AI person segmentation). Semua kartu bawah dikunci di bawah dagu (`y=0.74`). **TIDAK PERNAH MENUTUPI MATA ATAU WAJAH.**
*(Detail lengkap baca: [05-typography-safezones.md](references/05-typography-safezones.md))*

---

## 8. Sound Design Kontekstual & Zero-SFX Mode

- **Aturan Zero-SFX**: Jika pengguna meminta audio bersih (`intruct.md`), gunakan Style 11, atau untuk podcast/topik reflektif, **MATIKAN SELURUH SFX** (`"sfx": false` atau flag `--no-sfx`).
- **Contextual SFX**: Untuk gaya kreator/finansial, gunakan efek suara lembut (-14 dB di bawah vokal) yang hanya meletup saat ada kejadian visual nyata di layar.
*(Detail audio engineering baca: [09-sound-design.md](references/09-sound-design.md))*

---

## 9. WAJIB: PREVIEW-FIRST WORKFLOW (SEBELUM FINAL RENDER)

> **JANGAN PERNAH LANGSUNG MELAKUKAN FINAL MASTER RENDER TANPA MEMBERIKAN PREVIEW KEPADA PENGGUNA.**

### Langkah A: Hasilkan Lembar Kontak Keyframe Stills
Ekstrak frame pada detik-detik krusial (Hook, Data, Spotlight, Climax, Outro) untuk memeriksa komposisi dan safe zone:

```bash
python scripts/preview.py stills work/reels.mp4 --plan work/plan.json --out work/preview_check.jpg
```

### Langkah B: Hasilkan Fast Proxy Video (540p)
Render video preview ringan untuk mengevaluasi ritme gerak dan audio secara real-time:

```bash
python scripts/preview.py proxy work/reels.mp4 --plan work/plan.json --out work/preview_proxy.mp4 --width 540
```

### Langkah C: Tampilkan Preview & Tunggu Persetujuan
Tampilkan lembar still atau video proxy kepada pengguna. Jika ada permintaan perubahan (warna, timing, kata kunci), perbarui `work/plan.json` dan hasilkan preview baru.
*(Detail alur preview baca: [10-preview-first-workflow.md](references/10-preview-first-workflow.md))*

---

## 10. Master Quality Final Render

Setelah memperoleh persetujuan eksplisit dari pengguna, lakukan render final 1080Ã—1920 (CRF 17, 192k audio):

```bash
# General FX / Style 1-10 & 13
python scripts/fx.py --plan work/plan.json work/reels.mp4 out_master.mp4

# Style 11 (Editorial Motion Typography)
python scripts/typo_fx.py --plan work/plan.json work/reels.mp4 out_master.mp4

# Style 12 (Full Liquid Glass)
python scripts/liquid_glass_fx.py --plan work/plan.json work/reels.mp4 out_master.mp4
```

---

## Modul Referensi Lengkap

- [01 â€” Core Workflow Pipeline](references/01-core-workflow.md)
- [02 â€” Intelligent Footage Understanding](references/02-footage-understanding.md)
- [03 â€” Semantic Transcription Analysis](references/03-transcription-semantics.md)
- [04 â€” Autonomous Creative Direction](references/04-creative-direction.md)
- [05 â€” Typography & Safe Zones](references/05-typography-safezones.md)
- [06 â€” Motion Graphics & Infographics](references/06-motion-graphics-infographics.md)
- [07 â€” Contextual B-Roll Generation](references/07-broll-visual-generation.md)
- [08 â€” Visual Effects Encyclopedia (82+ FX)](references/08-effects-catalog-65.md)
- [09 â€” Contextual Sound Design](references/09-sound-design.md)
- [10 â€” Preview-First Workflow](references/10-preview-first-workflow.md)
- [11 â€” Cross-Platform Troubleshooting](references/11-cross-platform-troubleshooting.md)
- [Presets Katalog](presets/) (Style 1 hingga 13)
