# 05 — Professional Typography System & Platform Safe Zones

Typography adalah identitas visual utama dalam video pendek vertikal. Sistem tipografi yang buruk (terlalu kecil, menutupi wajah, tertutup tombol aplikasi, atau bergaya karaoke murahan) akan langsung menurunkan kualitas video.

---

## 1. Universal Social Safe Zone (Reels, TikTok, YouTube Shorts)

Pada canvas vertikal 1080×1920 (9:16), elemen antarmuka aplikasi (status bar, username, tombol like, disk audio) menutupi sebagian besar frame:

```
+--------------------------------------------------+ y = 0
|  TOP DANGER ZONE (Status Bar, Tab Navigation)    | (Tinggi 260px)
+==================================================+ y = 260px (13.5%)
|                                                  |
|              SAFE CANVAS AREA                    |
|                                                  |
|    - Display words behind head                   |
|    - Eye level / Face area (Protected)           |
|    - Cards / Bento under chin                    |
|                                   +--------------+
|    - Captions / Lower thirds      | RIGHT RAIL   | (Lebar 180px)
|      (Tinggi 1200px)              | Like/Comment |
|                                   +--------------+ x = 900px (83.5%)
+==================================================+ y = 1485px (77.2%)
|  BOTTOM DANGER ZONE (Caption, Audio, Navigation) | (Tinggi 435px)
+--------------------------------------------------+ y = 1920px
```

### Parameter Koordinat Safe Zone Wajib:
- **Batas Atas**: `y >= 0.135 * H` (260px pada 1080×1920).
  *Semua judul dan hook card diletakkan di bawah batas ini.*
- **Batas Bawah**: `y <= 0.772 * H` (1485px pada 1080×1920).
  *Semua caption, lower thirds, dan kartu bawah diletakkan di atas batas ini.*
- **Batas Kanan Bawah**: `x <= 0.835 * W` (900px pada 1080×1920 untuk paruh bawah frame).
  *Menghindari kolom vertikal tombol Like, Komentar, Share, dan Audio Disc.*
- **Batas Wajah & Mata (Face Protection)**:
  *Teks tidak boleh melintasi area antara alis dan mulut pembicara. Teks display wajib di belakang kepala (`behind: true`), dan kartu diletakkan di bawah dagu (`safe_lower_cy`).*

---

## 2. Tipografi Berjenjang (Editorial Typography Hierarchy)

| Level Hierarki | Peran & Fungsi | Font Family | Bobot & Ukuran | Posisi Frame |
|---|---|---|---|---|
| **Level 1: Display / Hook** | Judul pembuka, 1–3 kata kunci utama | *Archivo Black* / *Anton* | Huge (90–140px) | Belakang kepala (`behind: true`) |
| **Level 2: Eyebrow Tag** | Kategori topik, nama rubrik, metadata | *Space Mono Bold* | Small (24–32px), All-Caps | Di atas judul atau di dalam pill |
| **Level 3: Editorial Subtitle** | Penjelasan bernuansa, kutipan tajam | *Playfair Display Italic* | Medium (36–48px) | Di bawah dagu atau di samping subjek |
| **Level 4: Data & Stat Counter** | Angka persentase, nominal uang | *Archivo Black* / *Poppins* | Giant (80–120px) | Di dalam panel bento / kartu data |
| **Level 5: Standard Captions** | Dialog pembicaraan normal per frasa | *Inter SemiBold* / *Poppins* | Regular (44–52px) | Zona bawah aman (`y=0.74`) |
| **Level 6: Micro Typography** | Timecode, delta badge, label tombol | *Space Mono* / *Inter* | Micro (18–24px) | Di sudut kartu data atau badge |

---

## 3. Font Pairings yang Teruji

1. **Fintech / Data Elit**:
   *Display:* Inter ExtraBold + *Data:* Space Mono Bold + *Sub:* Playfair Display Italic
2. **Kreator Berenergi Tinggi**:
   *Display:* Archivo Black + *Data:* Montserrat Bold + *Caption:* Inter Bold
3. **Dokumenter / Vox Style**:
   *Display:* Anton + *Quotes:* Instrument Serif Italic + *Meta:* Space Mono
4. **Lifestyle / Reflektif**:
   *Display:* Playfair Display Bold + *Body:* Inter Regular
