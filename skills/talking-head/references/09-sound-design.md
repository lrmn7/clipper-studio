# 09 — Contextual Sound Design & Audio Engineering

Sound design dalam video bukan tentang memasukkan sebanyak mungkin efek suara yang bising. Efek suara yang tidak relevan (seperti *whoosh* di setiap pergantian kata atau *pop* yang memekakkan telinga) akan menghancurkan kredibilitas konten profesional.

---

## 1. Hirarki Audio yang Disiplin

Setiap elemen audio harus memiliki tempat yang tepat dalam rantai suara (*gain staging*):

```
1. Spoken Dialogue (Track Utama)       ──► Target: -14 LUFS to -16 LUFS (0 dB Ref)
2. Contextual UI SFX (Ticks, Clicks)   ──► Target: -14 dB to -18 dB di bawah vokal
3. Visual Impacts (Stamps, Slams)      ──► Target: -8 dB to -12 dB di bawah vokal
4. Background Ambience / Tone          ──► Target: -20 dB to -26 dB di bawah vokal
```

---

## 2. Zero-SFX / Clean Audio Mode (MUTLAK UNTUK PODCAST & ISU SERIUS)

Jika salah satu kondisi berikut terpenuhi:
1. Pengguna secara eksplisit meminta audio bersih (*"ZERO SFX", "tanpa efek suara", "audio asli murni"* seperti pada `intruct.md`).
2. Konten diedit menggunakan **Style 11 (Editorial Motion Typography)**.
3. Topik bahasan bersifat reflektif, duka, atau investigasi hukum serius.

**Maka seluruh sound effect sintetis dinonaktifkan (`"sfx": false` atau flag `--no-sfx`).**
Biarkan suara rekaman asli berbicara dengan kejernihan maksimal tanpa gangguan buatan.

---

## 3. Sintesis Suara Prosedural Tanpa Royalti (`sfx.py`)

Seluruh SFX dihasilkan secara algoritmik menggunakan `numpy` (48.000 Hz, 16-bit PCM stereo):
- **`pop()`**: Transien frekuensi 240–1060 Hz (0.09s). Digunakan saat kata display atau kartu informasi muncul.
- **`tick()`**: Frekuensi ganda 2400 Hz & 4800 Hz (0.035s). Digunakan pada centang checklist, perpindahan toggle switch, dan hitungan counter.
- **`whoosh()`**: Band-limited noise dengan sapuan filter 300–4500 Hz (0.36s). Digunakan saat kartu B-roll bergeser atau transisi kamera menyapu layar.
- **`impact()`**: Sub-bass 46–120 Hz dengan kompresi eksponensial (0.50s). Digunakan pada stempel penolakan (`reject-stamp`), hook pembuka, dan hantaman judul raksasa.
- **`chime()`**: Tiga gelombang sinus harmonik (1760 Hz, 2640 Hz, 3520 Hz). Digunakan pada antarmuka Liquid Glass atau tema pastel.
- **`paper()`**: Gesekan tekstur kertas terfilter 1800 Hz. Digunakan pada robekan koran (`paper-tear`), surat kabar, dan etiket cetak.
- **`snap()`**: Impuls mekanis cepat (0.04s). Digunakan pada pisau pembelah diagonal (`blade-slice`).

---

## 4. Aturan Editorial Sound Design
1. **Tidak Ada SFX Tanpa Kejadian Visual Nyata**:
   Jika tidak ada elemen grafis yang bergerak di layar, jangan pernah memainkan suara *whoosh* semata-mata karena ada jeda bicara.
2. **Kekuatan Keheningan (Power of Silence)**:
   Momen paling intens dalam video sering kali adalah hening total tepat sebelum kalimat penentu diucapkan. Jangan penuhi hening tersebut dengan SFX pengisi.
3. **Pencegahan Distorsi & Clipping**:
   Sistem `sfx.py` dan `fx.py` dilengkapi limiter digital otomatis (`alimiter=limit=0.97`) pada tahap mixing ffmpeg agar audio gabungan tidak pernah mengalami distorsi digital (*hard clipping*).
