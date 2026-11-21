# 08 — Visual Effects Encyclopedia (82+ Integrated Effects)

Dokumentasi lengkap sistem efek video hasil integrasi menyeluruh antara **Claude 65 Video Effects** dan **Adam Digital Reels FX System**. Setiap efek beroperasi secara non-destruktif, terintegrasi dengan pelacakan wajah YuNet dan segmentasi person MediaPipe.

---

## 1. Kamera, Zoom & Reframing
| Efek (`fx`) | Deskripsi Visual | Parameter Utama |
|---|---|---|
| `locked-on` | Corner brackets mengunci wajah subjek, kamera melacak pergerakan | `zoom` (def 1.35), `text` (tag label) |
| `lean-in` | Punch-in zoom cepat pada satu kata penekanan | `zoom` (1.15–1.45), `speed` |
| `slow-push` | Kamera mendekat perlahan ke wajah, latar belakang blur sinematik | `zoom` (1.2–1.6), `blur` |
| `dolly-zoom` | Efek vertigo: latar belakang mendekat cepat sementara ukuran subjek tetap | `zoom` (1.4), `plate` |
| `rack-focus` | Fokus berpindah ke latar belakang (subjek blur), lalu kembali ke subjek | `blur` |
| `over-the-shoulder-zoom` | Zoom ke sudut bahu kiri lalu kanan dengan grafik data melayang | `text`, `to`, `zoom` |

---

## 2. Tipografi Display & Titel di Belakang Kepala (`behind: true`)
| Efek (`fx`) | Deskripsi Visual | Parameter Utama |
|---|---|---|
| `pop-word` | Kata display raksasa meletup di belakang kepala dengan warna aksen | `text`, `color`, `size` (`big`/`med`) |
| `backdrop-word` | Kata raksasa jatuh dari atas dan tersangkut di belakang subjek | `text`, `color`, `font` (`bold`/`serif`) |
| `spotlight` | Ruangan meredup drastis, subjek tetap terang, teks berpendar di belakang | `text`, `color`, `push` |
| `huge-strike` | Kata serif raksasa di belakang kepala yang dicoret garis merah tegas | `text`, `at` |
| `crayon-write` | Krayon merah menulis kata kunci dan menggarisbawahinya di belakang kepala | `text`, `color` |
| `led-sign` | Lampu neon LED menyala berkedip mengetikkan kalimat penutup di belakang kepala | `text`, `color` |
| `orbit-ring` | Kalimat melingkari kepala subjek dalam cincin miring 3D | `text`, `color`, `speed`, `tilt` |

---

## 3. Kartu Data, Finansial & Infografis
| Efek (`fx`) | Deskripsi Visual | Parameter Utama |
|---|---|---|
| `data-compare` | Kartu perbandingan kondisi lama vs baru dengan pill delta persentase | `header`, `v1`, `sub1`, `v2`, `sub2`, `delta`, `color` |
| `liquid-glass-graph` | Kartu kaca refraktif dengan kurva grafik menanjak dan counter angka | `text`, `from`, `to`, `color`, `look` (`bento`) |
| `checklist` | Daftar tugas verifikasi dengan spinner loading yang tercentang hijau | `title`, `text` (`poin::meta\|...`), `color` |
| `apple-toggles` | Panel switch pengaturan iOS yang menyala ON bergantian di detik suara | `text` (baris), `ticks`, `color` |
| `the-bill` | Struk receipt tercetak keluar dari dinding di atas kepala pembicara | `text` (baris dipisah `\|`) |
| `banknote` | Frame berubah menjadi uang kertas resmi dengan wajah subjek di dalam oval | `text`, `title`, `serial`, `ink` |

---

## 4. B-Roll, Layout & Split Screen
| Efek (`fx`) | Deskripsi Visual | Parameter Utama |
|---|---|---|
| `hook-card` | Kartu hook kaca premium di sepertiga atas dengan judul pertanyaan | `tag`, `line1`, `line2`, `zoom`, `color` |
| `headline-box` | Punch-in dengan judul 2 baris, baris kedua di dalam kotak putih tegas | `text` (line1\|line2), `zoom` |
| `tape-label` | Pita perekat kuning bertekstur mendarat di dada subjek | `text`, `color` |
| `broll-split` | Layar terbelah 50:50: B-roll di atas dengan stiker harga, subjek di bawah | `images`, `text` (tag) |
| `halftone-paper` | Tekstur kertas koran krem, subjek terpotong di kanan bawah dengan bayangan halftone | `text`, `color` |
| `cover-star` | Menjadikan subjek sebagai sampul majalah mewah dengan masthead di belakang kepala | `text`, `lines`, `issue`, `look` (`editorial`) |
| `press-front` | Halaman depan surat kabar koran lengkap dengan foto halftone subjek | `text`, `sub`, `name`, `date` |
| `paper-tear` | Koran surat kabar sobek di tengah dan jatuh membuka video asli | `hold` |
| `card-drop` | Subjek bergeser turun dan kartu screenshot melayang masuk di atasnya | `images`, `text` |

---

## 5. UI Spasial & Interaksi Media Sosial
| Efek (`fx`) | Deskripsi Visual | Parameter Utama |
|---|---|---|
| `live-cursor` | Kursor mouse memilih subjek dalam kotak seleksi lalu menggesernya ke samping | `text` (nama kursor), `color`, `drag` |
| `comment-box` | Lembar komentar media sosial mengetikkan kata, memposting, dan mendapat like hati | `text`, `look` |
| `comment-drop` | Huruf jatuh ke bar komentar, memposting, dan membalas komentar | `text`, `user`, `line` |
| `messages` | Notifikasi iMessage kaca melayang bertumpuk rapi di zona aman | `text` (pesan dipisah `\|`), `title` |
| `predict-keys` | Keyboard smartphone muncul dan mengetikkan kata prediksi di atas layar | `text`, `next` |
| `tap` | Tombol Follow muncul lalu berubah menjadi Following dengan aksen centang | `at`, `x`, `y`, `color` |
| `reel-frame` | Video subjek mengecil ke dalam kartu tampilan Reels Instagram | `text` (handle) |
| `phone-fan` | Deretan cover video tersebar seperti kartu remi di bawah judul | `images`, `text` |
| `place-in-grid` | Subjek mengecil ke kotak tengah profil grid 3x3 dengan angka view counts | `images`, `views` |

---

## 6. Transisi Sinematik & Dimensional Art
| Efek (`fx`) | Deskripsi Visual | Parameter Utama |
|---|---|---|
| `layer-explode` | Frame video terbelah menjadi 4 lembaran kaca 3D terpisah di ruang spasial | `text`, `angle`, `gap` |
| `letter-dive` | Teks diketik di atas kertas, lalu kamera menyelam menembus lubang huruf | `text`, `into`, `zoom` |
| `blade-slice` | Potongan diagonal membelah frame, separuh gambar bergeser lalu mengunci kembali | `angle`, `slide`, `at` |
| `sketch-words` | Dinding menjadi kertas gambar dan kata diarsir dengan pensil sketsa | `text`, `color` |
| `dot-reveal` | Gambar terurai menjadi titik-titik partikel cahaya lalu kembali solid | `color`, `cell` |
| `code-body` | Tubuh subjek berubah menjadi barisan kode biner yang berjalan | `color`, `cell` |
| `blow-away` | Subjek terurai menjadi debu partikel dan tertiup angin meninggalkan ruangan kosong | `plate`, `speed`, `wind` |
| `reject-stamp` | Stempel merah besar menghantam frame dengan suara benturan tegas | `text`, `color`, `angle` |
| `uninstall` | Glitch bar uninstall meretakkan frame saat ada konsep yang ingin dibongkar | `text` |
| `swipe` | Garis sebelum-sesudah menyapu melintasi subjek memperlihatkan perbandingan | `grade` |

---

## 7. Sistem Subtitle & Overlay Lintas Layar
| Efek (`fx`) | Deskripsi Visual | Parameter Utama |
|---|---|---|
| `captions` | Subtitle per kata dengan highlight emas/kuning, sinkron Whisper | `style` (`clean`/`bold`/`pill`/`grey`), `y`, `hide` |
| `caption-pills` | Pill teks individual per baris dengan warna latar kontras | `text`, `ticks`, `bg`, `y` |
| `nameplate` | Kartu "Now Playing" di bagian bawah dengan nomor segmen dan progress bar | `text`, `ticks`, `color`, `y` |
| `tracklist` | Daftar urutan topik di sisi kanan yang menyorot babak aktif | `text`, `ticks`, `scale` |
