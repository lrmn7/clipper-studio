# 11 — Cross-Platform Compatibility & Troubleshooting Guide

Sistem Intelligent Video Editing dirancang agar dapat berjalan secara konsisten di **Windows (PowerShell/CMD)**, **macOS (Terminal/zsh)**, dan **Linux (bash)** tanpa bergantung pada shell atau path spesifik OS.

---

## 1. Aturan Portabilitas Lintas Platform

### A. Path Handling dalam Python
- **JANGAN PERNAH MENGGUNAKAN HARDCODED SLASH TUNGGAL**:
  Gunakan `os.path.join()`, `os.path.abspath()`, atau `pathlib.Path` untuk semua konstruksi path file.
- Penanganan path virtual environment:
  - Windows: `.venv\Scripts\python.exe`
  - macOS / Linux: `.venv/bin/python`

### B. Eksekusi Command FFmpeg & Subprocess
- Selalu gunakan list argumen dalam `subprocess.run(["ffmpeg", ...])` daripada string shell mentah agar terhindar dari masalah escaping karakter di PowerShell vs Bash.
- Hindari filter shell seperti `2>/dev/null` di dalam kode Python. Gunakan parameter `capture_output=True` atau `stdout=subprocess.PIPE`.

### C. Resolusi Font Lintas Sistem Operasi
- Semua font utama (*ArchivoBlack*, *Inter*, *Montserrat*, *PlayfairDisplay*, *SpaceMono*, *PermanentMarker*) telah dibundel secara lokal di folder `SKILL/fonts/`.
- Engine secara otomatis memuat font dari direktori lokal tersebut tanpa bergantung pada font sistem OS Windows (`C:\Windows\Fonts`), macOS (`/Library/Fonts`), atau Linux (`/usr/share/fonts`).

---

## 2. Panduan Setup Satu Langkah (`setup.py`)

Gunakan script cross-platform `setup.py` yang kompatibel dengan semua sistem operasi:

```bash
# Di semua OS:
python scripts/setup.py
```

Script akan:
1. Memeriksa keberadaan `ffmpeg` dan `ffprobe` di sistem PATH.
2. Memverifikasi atau membuat environment virtual `.venv`.
3. Menginstal paket dependensi (`numpy`, `opencv-python`, `pillow`, `mediapipe`, `faster-whisper`).
4. Memvalidasi kemampuan inferensi model AI `yunet.onnx` dan `selfie_segmenter.tflite`.

---

## 3. Matriks Pemecahan Masalah (Troubleshooting)

| Gejala / Error | Akar Masalah | Solusi Cepat |
|---|---|---|
| `FileNotFoundError: presets/style-N.json` | Folder presets belum disinkronkan | Folder `SKILL/presets/` kini telah diisi lengkap dari template style 1–13. |
| `NEED_FFMPEG` / ffmpeg not found | FFmpeg belum terinstal di sistem PATH | Windows: `winget install ffmpeg`<br>macOS: `brew install ffmpeg`<br>Linux: `sudo apt install ffmpeg` |
| `OpenCV: FaceDetectorYN error` | Model YuNet tidak ditemukan pada path relatif | Pastikan path diakses via `os.path.join(ROOT, 'models', 'yunet.onnx')`. |
| Text tertutup tombol Like Instagram | Teks diletakkan di luar Safe Zone | Sesuaikan koordinat `y` agar berada di rentang 260px–1485px, dan `x <= 900px` di paruh bawah. |
| Audio video hasil render pecah / distorsi | Mixing SFX terlalu keras tanpa limiter | Gunakan flag `--sfx-volume -4.0` atau pastikan limiter `-alimiter=limit=0.97` aktif pada mixing filter. |
| Video sumber berukuran besar lambat di-render | Melakukan render 1080p langsung tanpa preview | Gunakan `preview.py proxy --width 540` untuk review cepat sebelum render master final. |
