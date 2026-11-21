# Reels AI Director & Intelligent Video Editing System

Sistem pengarah dan penyunting video vertikal (Instagram Reels, TikTok, YouTube Shorts) berbasis kecerdasan buatan. Menggabungkan 82+ efek video dari `claude-65-video-effects` dan `Adam Digital`, analisis semantik Whisper, pergerakan kamera face-tracking YuNet, tipografi kinetik editorial, serta alur kerja wajib **Preview-First**.

## Fitur Utama
- **Pemahaman Footage Mendalam**: Deteksi subjek, pelacakan wajah YuNet, dan analisis ruang spasial.
- **Transkripsi Semantik**: Timestamp per kata via Whisper dengan identifikasi otomatis hook, angka, kontras, dan klimaks.
- **Pengarahan Kreatif Mandiri**: 13 signature styles dengan pemilihan palet warna, tipografi, dan ritme tanpa menginterogasi pengguna.
- **Sistem Tipografi & Safe Zone**: Perlindungan wajah (*behind head depth masking*), anti-karaoke, dan batas aman antarmuka media sosial.
- **Infografis & B-Roll Kontekstual**: Generator lokal untuk papan data, grafik, dan kartu kutipan (`broll_gen.py`).
- **82+ Efek Terintegrasi**: Mencakup seluruh efek Claude 65 (3D layer explode, letter dive, paper tear, manga impact, dll.) dan efek kustom.
- **Desain Suara Kontekstual**: Sintesis audio prosedural tanpa royalti serta mode wajib **Clean Audio (Zero SFX)**.
- **Alur Kerja Preview-First (Wajib)**: Pembuatan lembar kontak keyframe dan video proxy cepat sebelum render final broadcast quality.

## Panduan Lengkap
Lihat [SKILL.md](SKILL.md) dan modul dokumentasi di folder [references/](references/).
