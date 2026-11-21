# 10 — Mandatory Preview-First Workflow & Approval Gate

Kebijakan utama Intelligent Video Editing System adalah:

> **JANGAN PERNAH LANGSUNG MELAKUKAN FINAL RENDER SEBELUM MEMBERIKAN PREVIEW KEPADA PENGGUNA.**

Merender video penuh pada resolusi 1080×1920 (atau 4K) membutuhkan waktu komputasi yang signifikan. Jika terdapat kesalahan penempatan teks di atas wajah, kata salah eja, atau durasi efek yang tidak pas, melakukan render ulang dari nol adalah pemborosan waktu.

---

## 1. Alur Kerja Dua Tahap (Two-Stage Gate)

```
[Tahap A: Perancangan Timeline]
  └─► Jalankan `director.py` untuk menghasilkan `work/plan.json` & `work/blueprint.json`
        │
        ▼
[Tahap B: PREVIEW GENERATION (Wajib)]
  ├─► Jalankan `preview.py stills`  ──► Lembar Kontak Keyframe (Cek Safe Zone & Wajah)
  └─► Jalankan `preview.py proxy`   ──► Video Preview Cepat 540p (Cek Ritme & Audio)
        │
        ▼
[Tahap C: Presentasi ke Pengguna]
  └─► Tampilkan gambar preview & sampaikan ringkasan keputusan kreatif kepada pengguna.
        │
        ▼
[Tahap D: Gate Persetujuan]
  ├─► Ada Revisi?  ──► Edit `work/plan.json` ──► Render Ulang Preview
  └─► Disetujui?   ──► Lanjutkan ke Tahap E (Final Render)
        │
        ▼
[Tahap E: Final Master Render]
  └─► Jalankan render penuh resolusi 1080p broadcast quality dengan CRF 17.
```

---

## 2. Pengecekan Kualitas pada Lembar Stills (`preview.py stills`)

Sebelum menyajikan hasil ke pengguna, AI Editor memeriksa sendiri gambar still frame:
1. **Perlindungan Wajah & Mata**: Apakah ada huruf atau kartu grafis yang melintasi area mata, kacamata, atau hidung pembicara? Jika ya, aktifkan `"behind": true` atau geser `y` ke bawah dagu.
2. **Kesesuaian Safe Zone**: Apakah ada teks yang berada di atas garis kuning atas (y < 13.5%) atau di bawah garis bawah (y > 77.2%)?
3. **Keterbacaan & Kontras**: Apakah kontras teks terhadap latar belakang video memenuhi rasio minimal 4.5:1? Jika latar belakang terang, tambahkan bayangan lembut atau panel kaca frosted.
4. **Ejaan Istilah & Angka**: Apakah angka persentase ("5,75%"), nominal ("6%"), dan istilah ("BI-Rate") sudah tertulis akurat?

---

## 3. Evaluasi Ritme pada Video Proxy (`preview.py proxy`)

Video proxy 540p (540×960) selesai dirender dalam hitungan detik:
- **Pacing**: Apakah pergantian efek terjadi setiap 2.5–4.5 detik tanpa jeda membosankan?
- **Sinkronisasi Kata**: Apakah efek meletup tepat pada suku kata yang relevan?
- **Keseimbangan Suara**: Apakah dialog terdengar jernih dan vokal tidak tenggelam oleh efek suara?

---

## 4. Penanganan Siklus Revisi Pengguna

Pengguna dapat memberikan feedback seperti:
- *"Ganti warna hook jadi kuning emas"*
- *"Teks 'JADI REM' di detik 21 jangan terlalu besar"*
- *"Hapus sound effect di bagian data"*

AI Editor memperbarui file `work/plan.json` sesuai instruksi, membuat preview baru, dan hanya merender master video akhir setelah pengguna memberikan lampu hijau (*explicit approval*).
