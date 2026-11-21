# 02 — Intelligent Footage Understanding

Fondasi video editing berkelas dunia adalah pemahaman mendalam terhadap materi mentah (*raw footage*). AI Editor tidak boleh memperlakukan footage hanya sebagai deretan piksel atau durasi waktu, melainkan harus menganalisis aspek visual, spasial, dan akustik secara menyeluruh.

---

## 1. Visual Analysis & Spatial Intelligence

### A. Geometri Wajah & Subjek Utama
Deteksi posisi wajah pembicara menggunakan YuNet Face Detector (`cv2.FaceDetectorYN`):
- **Titik Pusat Wajah (`cx, cy`)**: Menentukan titik jangkar kamera dan efek spotlight.
- **Lebar & Tinggi Wajah (`fw, fh`)**: Menentukan proporsi ukuran subjek terhadap frame (Close-up, Medium Close-up, Wide).
- **Ruang Negatif Atas (Negative Space)**:
  `top_margin = max(0, fy - fh * 0.8)`
  Jika `top_margin > 250px`, ruang di atas kepala ideal untuk penempatan *headline-box*, *apple-toggles*, atau *huge-strike*.
- **Ruang Bawah Dagu (Lower Safe Region)**:
  `chin_y = fy + fh * 0.8`
  Area di bawah dagu adalah zona aman paling tepat untuk kartu data (*data-compare*, *liquid-glass-graph*, *checklist*) dan subtitle.

### B. Face Protection & Depth Masking (MUTLAK)
- **TIDAK PERNAH MENUTUPI MATA ATAU WAJAH**:
  Setiap teks berukuran display/raksasa wajib diposisikan di belakang kepala pembicara menggunakan AI Person Segmentation (`selfie_segmenter.tflite` dengan guided filter edge refinement).
- Parameter `"behind": true` pada efek tipografi memastikan alpha mask subjek menutupi layer teks secara presisi.

### C. Analisis Komposisi & Reframing Cerdas
- **Horizontal (16:9) ke Vertikal (9:16)**:
  Jangan lakukan center crop statis jika pembicara bergerak. Gunakan `reframe_reels.py` dengan parameter filter temporal ganda (`tau=0.55`) untuk menghasilkan pergerakan kamera virtual yang mulus seperti dikendalikan kameramen profesional.
- **Shot Dynamics & Punch-In Editorial**:
  Punch-in kamera (`zoom=1.12–1.20`) hanya diterapkan pada:
  1. Detik awal Hook (0–3 detik) untuk memecah keheningan visual.
  2. Momen penekanan kata kunci / klimaks pernyataan.
  3. Pergantian babak atau transisi poin baru.
  *Jangan gunakan zoom acak tanpa alasan editorial.*

### D. Multi-Camera & Scene Continuity
Ketika menerima beberapa klip dari sudut berbeda:
- Analisis sinkronisasi audio track untuk mencocokkan timestamp.
- Potong ke sudut kamera kedua (Close-up atau Over-the-shoulder) pada pergantian ide atau penekanan poin penting, bukan di tengah-tengah kata.

---

## 2. Audio & Acoustic Intelligence

### A. Analisis Nada, Emosi & Intonasi
- **Delivery Berenergi Tinggi**: Memerlukan potongan visual cepat (2.0–3.0s), tipografi bold, dan aksen kinetik.
- **Delivery Reflektif / Serius**: Memerlukan ruang bernapas lebih luas (4.0–6.0s per perubahan visual), font serif mewah (*PlayfairDisplay*), pergerakan slow push, dan peredaman SFX.

### B. Pemetaan Jeda & Silence
- **Dead Air (Hening Kosong)**: Jeda tanpa suara > 0.35s dipangkas agar video padat dan tidak membosankan.
- **Dramatic Pause (Jeda Dramatis)**: Jeda pendek (0.2–0.3s) tepat sebelum pengungkapan angka penting atau kesimpulan **TIDAK BOLEH DIPOTONG**. Manfaatkan momen ini untuk memasukkan transisi visual, efek suara subtil, atau persiapan kartu data.

### C. Speaker Diarization
- Jika terdeteksi lebih dari satu pembicara (podcast/interview):
  Pastikan nama pembicara diperkenalkan via `nameplate` atau `tape-label` pada giliran bicara pertama mereka, dan jangan tumpuk teks pada wajah pembicara kedua.
