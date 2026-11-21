# 01 — Core Workflow: The Intelligent Video Editing Pipeline

Panduan ini mendefinisikan standar operasional AI Video Editor & Director dari penerimaan raw footage hingga delivery akhir. Setiap langkah dirancang untuk memaksimalkan retensi penonton, kejernihan pesan, dan estetika visual tanpa ketergantungan pada template generik.

---

## The 10-Step Pipeline

```
Raw Footage ──► [1. Visual & Audio Probe] ──► [2. Pauses & Breath Trimming]
                     │                                   │
                     ▼                                   ▼
[4. Semantic Analysis & Beats] ◄── [3. Whisper Transcription & Correction]
         │
         ▼
[5. Autonomous Creative Direction & Blueprint Generation]
         │
         ▼
[6. Contextual B-Roll & Infographics Asset Creation]
         │
         ▼
[7. Scene-by-Scene Timeline Assembly & Effects Plan]
         │
         ▼
[8. MANDATORY PREVIEW GENERATION (Stills & Fast Proxy Video)]
         │
         ▼
[9. User Review & Iterative Revision Gate] ──► (Revisi Blueprint jika perlu)
         │ (Explicit Approval)
         ▼
[10. Master Quality Final Render (1080p / 4K)]
```

---

## Detailed Phase Execution

### Fase 1: Visual & Audio Probe (Pemeriksaan Awal)
Periksa metadata teknis video menggunakan `director.py` atau `ffprobe`:
- **Resolusi & Aspek Rasio**: Apakah video horizontal (16:9), vertikal native (9:16), atau square (1:1)?
- **Framerate & Durasi**: Cek sinkronisasi frame (24fps / 30fps / 60fps).
- **Keberadaan Audio**: Pastikan track dialog tersedia dan tidak rusak.
- **Deteksi Wajah & Framing**: Jalankan YuNet Face Detection untuk menghitung bounding box wajah, posisi mata, dan batas dagu.

```bash
python scripts/director.py analyze input.mp4 --out-plan work/plan.json
```

### Fase 2: Trimming Jeda Kosong (Dead-Air Optimization)
Pangkas jeda hening lebih dari 0.35s menggunakan `trim.py`:
- Pertahankan jeda napas mikro (0.15–0.25s) sebelum kalimat klimaks atau pengungkapan fakta besar agar ritme tetap terdengar alami.
- Pada video dialog/podcast 2 orang, gunakan threshold lebih toleran (`--gap 0.5`) agar tidak memotong reaksi lawan bicara.

```bash
python scripts/trim.py input.mp4 work/trim.mp4 --gap 0.4 --keep 0.16
```

### Fase 3: Auto-Reframe ke 9:16 (Jika Footage Horizontal)
Jika footage asli 16:9 atau bukan vertikal:
- Gunakan `reframe_reels.py` dengan smoothing Gaussian bilateral berbasis face-tracking YuNet.
- Pastikan subjek selalu berada di sepertiga atas frame dengan ruang gerak yang stabil.

```bash
python scripts/reframe_reels.py work/trim.mp4 work/reels.mp4 --tau 0.55
```

### Fase 4: Transkripsi Akurat & Pemahaman Semantik
Jalankan `words.py` untuk memperoleh timestamp per kata:
1. Periksa dan koreksi istilah teknis, nama institusi, persentase, dan angka (misal: "bang Indonesia" → "Bank Indonesia", "5,75%", "25 bps").
2. Identifikasi struktur retoris:
   - **Hook (0.0–3.5s)**: Klaim pemicu penasaran atau pertanyaan tajam.
   - **Problem / Question**: Masalah yang dihadapi audiens.
   - **Data / Core Metric**: Angka, persentase, perbandingan nilai.
   - **Breather / Transition**: Jeda logis untuk B-roll atau pergantian topik.
   - **Climax / Verdict**: Kesimpulan akhir.
   - **CTA**: Ajakan bertindak yang halus.

### Fase 5: Penentuan Creative Direction Mandiri
AI menentukan konsep visual secara otomatis berdasarkan topik bahasan (lihat `04-creative-direction.md`):
- **Topik Keuangan / Data / Finansial** → *Style 12: Full Liquid Glass* atau *Style 4: Fintech Terminal*.
- **Wawancara / Podcast / Diskusi Kritis** → *Style 11: Editorial Motion Typography* (Zero SFX).
- **Edukasi Cepat / Creator Viral** → *Style 1: High-Retention Creator*.
- **Dokumenter Serius / Investigasi** → *Style 3: Brutalist Crimson / Noir*.

### Fase 6: Pembuatan Aset Visual & B-Roll Kontekstual
Jika footage memerlukan visualisasi data atau demonstrasi konsep, buat aset resolusi tinggi menggunakan `broll_gen.py` atau engine grafis:
- Papan perbandingan data (`data-compare`)
- Kartu KPI angka besar (`kpi`)
- Kartu kutipan editorial (`quote`)

### Fase 7: Penyusunan Timeline & Rencana Efek (`effects.json`)
Rangkai timeline per detik dengan aturan:
- Perubahan visual setiap 2.5–4.5 detik (zoom punch, spotlight, kartu data, bento, sticker stack).
- Maksimal 2 efek simultan (jangan menumpuk terlalu banyak elemen visual yang membingungkan).
- Teks display raksasa wajib berada di belakang kepala (`behind: true`) atau di bawah dagu (`y=0.74`).
- Kunci elemen visual di dalam Safe Zone platform (lihat `05-typography-safezones.md`).

### Fase 8: WAJIB PREVIEW GENERATION (Stills & Proxy)
**DILARANG MELAKUKAN FINAL MASTER RENDER SEBELUM PREVIEW DITAMPILKAN KE PENGGUNA.**
1. Hasilkan lembar preview keyframe (`work/preview_sheet.jpg`) pada detik-detik penting (Hook, Data, Spotlight, Climax, Outro).
2. Hasilkan video proxy 540p (`work/preview_proxy.mp4`) untuk mengevaluasi ritme, audio, dan motion.

```bash
# 1. Keyframe Contact Sheet
python scripts/preview.py stills work/reels.mp4 --plan work/plan.json --out work/preview_sheet.jpg

# 2. Fast Proxy Video Preview
python scripts/preview.py proxy work/reels.mp4 --plan work/plan.json --out work/preview_proxy.mp4 --width 540
```

### Fase 9: Review & Revisi
Sampaikan hasil preview dan ringkasan arahan kreatif kepada pengguna:
- Jika pengguna meminta perubahan (misal: "ganti warna jadi emas", "ubah B-roll di detik 15", "hilangkan efek di detik 30"):
  Edit `work/plan.json`, lalu jalankan kembali `preview.py`.
- Lanjutkan ke render final HANYA setelah ada konfirmasi atau persetujuan pengguna.

### Fase 10: Master Final Render
Setelah disetujui, jalankan render resolusi penuh (1080×1920) dengan CRF 17 berkualitas broadcast:

```bash
python scripts/<engine>.py --plan work/plan.json work/reels.mp4 out_final.mp4
```
Simpan file output, catat ringkasan timeline, dan serahkan kepada pengguna.
