#!/usr/bin/env python3
"""Autonomous Creative Director & Editorial Intelligence Engine for Reels / Short-Form Video.

Understands raw footage (visual composition, YuNet face tracking, acoustic clarity),
transcribes speech with Whisper word-level timestamps, semantically analyzes hooks,
data points, questions, enumerations, contrasts, and climaxes, autonomously determines
creative direction across 13 signature styles, and builds an executable, production-ready
effects plan adhering strictly to platform safe zones, face protection, and editorial pacing.

Supports single footage, multi-footage probe, horizontal-to-vertical reframe guidance,
and strict Zero-SFX / clean audio enforcement.

Usage:
  python director.py analyze <video.mp4> [--words <words.json>] [--out-plan <plan.json>] [--style <style>] [--clean-audio]
  python director.py analyze video1.mp4 video2.mp4 ...
"""
import argparse
import json
import math
import os
import re
import subprocess
import sys
import numpy as np
import cv2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))


def probe_footage(path):
    """Deep visual probe: dimensions, fps, duration, aspect ratio, and face geometry."""
    if not os.path.exists(path):
        sys.exit(f"Footage not found: {path}")

    cmd = ['ffprobe', '-v', 'error', '-show_entries',
           'stream=width,height,r_frame_rate,codec_type:format=duration', '-of', 'json', path]
    try:
        raw = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
        info = json.loads(raw)
    except Exception as ex:
        sys.exit(f"Failed to probe footage {path}: {ex}")

    v_stream = next((s for s in info.get('streams', []) if s.get('codec_type') == 'video'), None)
    has_audio = any(s.get('codec_type') == 'audio' for s in info.get('streams', []))
    if not v_stream:
        sys.exit(f"No video stream found in {path}")

    num, den = v_stream.get('r_frame_rate', '30/1').split('/')
    fps = min(float(num) / float(den or 1), 30.0)
    dur = float(info.get('format', {}).get('duration', 0.0))
    sw, sh = int(v_stream.get('width', 1080)), int(v_stream.get('height', 1920))
    is_vertical = (sw * 16 <= sh * 9 + 40)

    # Face geometry sample with YuNet
    model_path = os.path.join(ROOT, 'models', 'yunet.onnx')
    dw, dh = 640, int(round(640 * sh / max(1, sw)))
    fd = cv2.FaceDetectorYN.create(model_path, '', (dw, dh), 0.55, 0.3, 10) if os.path.exists(model_path) else None

    cap = cv2.VideoCapture(path)
    faces = []
    sample_count = min(30, int(dur * 2)) if dur > 0 else 10
    sample_step = max(1, int((dur * fps) / max(1, sample_count))) if dur > 0 else 15

    frame_idx = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if frame_idx % sample_step == 0 and fd is not None:
            small = cv2.resize(frame, (dw, dh), interpolation=cv2.INTER_AREA)
            _, det = fd.detect(small)
            if det is not None and len(det):
                r = max(det, key=lambda f_: f_[2] * f_[3] * f_[-1])
                sc = sw / dw
                faces.append({
                    'x': float(r[0] * sc),
                    'y': float(r[1] * sc),
                    'w': float(r[2] * sc),
                    'h': float(r[3] * sc),
                    'cx': float((r[0] + r[2] * 0.5) * sc),
                    'cy': float((r[1] + r[3] * 0.5) * sc)
                })
        frame_idx += 1
    cap.release()

    med_face = None
    if faces:
        med_face = {
            'cx': float(np.median([f['cx'] for f in faces])),
            'cy': float(np.median([f['cy'] for f in faces])),
            'w': float(np.median([f['w'] for f in faces])),
            'h': float(np.median([f['h'] for f in faces]))
        }

    return {
        'path': path,
        'width': sw,
        'height': sh,
        'is_vertical': is_vertical,
        'fps': fps,
        'duration': dur,
        'has_audio': has_audio,
        'face': med_face
    }


def semantic_analysis(words, dur):
    """Analyzes word-level transcript to extract hooks, questions, data, and editorial beats."""
    if not words:
        return {
            'topic': 'general',
            'full_text': '',
            'phrases': [],
            'moments': []
        }

    # Group words into phrases/sentences based on natural pauses (>= 0.35s) or punctuation
    phrases = []
    curr = []
    for i, w in enumerate(words):
        curr.append(w)
        pause = (words[i + 1]['s'] - w['e']) if i + 1 < len(words) else 999.0
        word_str = w.get('w', '')
        if pause >= 0.35 or word_str.endswith(('.', '?', '!', ';')):
            text = " ".join(item['w'] for item in curr).strip()
            if text:
                phrases.append({
                    'start': curr[0]['s'],
                    'end': curr[-1]['e'],
                    'text': text,
                    'words': list(curr)
                })
            curr = []
    if curr:
        text = " ".join(item['w'] for item in curr).strip()
        if text:
            phrases.append({
                'start': curr[0]['s'],
                'end': curr[-1]['e'],
                'text': text,
                'words': list(curr)
            })

    full_text = " ".join(w['w'] for w in words).lower()

    # Broad topic classification based on semantic vocabulary
    topic_keywords = {
        'philosophy_religion': [
            'rasulullah', 'islam', 'nabi', 'hadits', 'allah', 'tuhan', 'agama', 'ibadah', 'moral',
            'keadilan', 'gender', 'equality', 'hak', 'akhlak', 'iman', 'filsafat', 'makna', 'hidup',
            'manusia', 'kebijaksanaan', 'sejarah', 'jaman', 'kebaikan', 'pahala', 'dosa', 'dakwah'
        ],
        'finance_economics': [
            'suku bunga', 'inflasi', 'rupiah', 'dolar', 'bi rate', 'ekonomi', 'kredit', 'pasar',
            'investasi', 'saham', 'profit', 'bank', 'uang', 'finansial', 'anggaran', 'persen', 'bps',
            'fintech', 'omset', 'modal', 'cuan', 'pajak', 'aset'
        ],
        'tech_developer': [
            'ai', 'koding', 'coding', 'software', 'tech', 'teknologi', 'komputer', 'prompt', 'model',
            'developer', 'programmer', 'python', 'sistem', 'cloud', 'data', 'digital', 'algoritma',
            'internet', 'robot', 'otomasi', 'machine learning'
        ],
        'social_investigative': [
            'guru', 'artis', 'viral', 'drama', 'keadilan', 'korupsi', 'pemerintah', 'politik',
            'kasus', 'skandal', 'masyarakat', 'kontroversi', 'gaji', 'biaya', 'rakyat', 'hukum',
            'kebijakan', 'aturan'
        ],
        'business_marketing': [
            'bisnis', 'penjualan', 'marketing', 'omset', 'strategi', 'customer', 'produk', 'jualan',
            'scale', 'brand', 'perusahaan', 'klien', 'closing', 'funnel', 'iklan', 'leads'
        ],
        'motivation_mindset': [
            'sukses', 'gagal', 'disiplin', 'kebiasaan', 'fokus', 'malas', 'kerja keras', 'masa depan',
            'konsisten', 'mental', 'motivasi', 'mindset', 'tujuan', 'impian', 'berkembang', 'rutinitas'
        ],
        'health_wellness': [
            'kesehatan', 'makan', 'tidur', 'olahraga', 'stres', 'workout', 'penyakit', 'dokter',
            'obat', 'gizi', 'nutrisi', 'diet', 'badan', 'otak', 'psikologi'
        ],
        'podcast_interview': [
            'podcast', 'interview', 'ngobrol', 'cerita', 'bintang tamu', 'obrolan', 'menurut kamu',
            'episode', 'pertanyaan', 'pengalaman', 'sharing'
        ]
    }

    topic_scores = {k: 0 for k in topic_keywords}
    for t_name, kws in topic_keywords.items():
        for kw in kws:
            if kw in full_text:
                topic_scores[t_name] += 1

    best_topic, best_score = max(topic_scores.items(), key=lambda it: it[1])
    topic = best_topic if best_score > 0 else 'general'

    # Identify narrative moments
    moments = []

    # 1. Opening Hook (0.0s to min(3.8s, dur))
    hook_words = [w for w in words if w['s'] <= min(3.8, dur)]
    if not hook_words and words:
        hook_words = words[:min(6, len(words))]
    hook_text = " ".join(w['w'] for w in hook_words).strip()
    moments.append({
        'type': 'hook',
        'start': 0.0,
        'end': min(2.8, hook_words[-1]['e'] if hook_words else 2.5),
        'text': hook_text or "PERTANYAAN KUNCI"
    })

    # 2. Number / Data / Statistics Extraction
    data_regex = re.compile(
        r'(\d+[\.,]?\d*\s*(?:%|persen|bps|x|kali|juta|jt|miliar|ribu|k|m|b)?)',
        re.IGNORECASE
    )
    for p in phrases:
        if p['start'] < 2.5 or p['start'] >= dur - 1.0:
            continue
        matches = [m.strip() for m in data_regex.findall(p['text']) if m.strip() and any(c.isdigit() for c in m)]
        if matches:
            # Check if this phrase represents a comparison between two metrics (e.g. from X to Y or X vs Y)
            comp_match = re.search(r'(?:dari|sebelumnya|antara)?\s*(\d+[\.,]?\d*[%]?)\s*(?:ke|menjadi|vs|sampai)?\s*(\d+[\.,]?\d*[%]?)', p['text'], re.IGNORECASE)
            v1, v2 = None, None
            if comp_match:
                v1, v2 = comp_match.group(1), comp_match.group(2)
            elif len(matches) >= 2:
                v1, v2 = matches[0], matches[1]

            moments.append({
                'type': 'data',
                'start': p['start'],
                'end': min(dur - 0.2, p['start'] + 4.0),
                'text': p['text'],
                'v1': v1,
                'v2': v2,
                'matches': matches
            })

    # 3. Question / Puzzle / Inquisitive Beat
    for p in phrases:
        if p['start'] < 2.5 or p['start'] >= dur - 1.0:
            continue
        txt_l = p['text'].lower()
        if any(q in txt_l for q in ['kenapa', 'mengapa', 'adakah', 'apa sih', 'benarkah', 'bagaimana', 'why', 'how', '?']):
            if not any(abs(m['start'] - p['start']) < 2.5 for m in moments):
                moments.append({
                    'type': 'question',
                    'start': p['start'],
                    'end': min(dur - 0.2, p['start'] + 3.8),
                    'text': p['text']
                })

    # 4. Enumeration / Key Steps / Checklist
    for p in phrases:
        if p['start'] < 3.0 or p['start'] >= dur - 2.0:
            continue
        txt_l = p['text'].lower()
        if any(step in txt_l for step in ['alasan', 'faktor', 'pertama', 'kedua', 'ketiga', 'langkah', 'poin penting']):
            if not any(abs(m['start'] - p['start']) < 3.0 for m in moments):
                moments.append({
                    'type': 'enumeration',
                    'start': p['start'],
                    'end': min(dur - 0.2, p['start'] + 5.0),
                    'text': p['text']
                })

    # 5. Emphasis / Contrast / Punchline
    for p in phrases:
        if p['start'] < 2.0 or p['start'] >= dur - 1.0:
            continue
        txt_l = p['text'].lower()
        if any(e in txt_l for e in ['bukan', 'tapi', 'justru', 'masalahnya', 'kuncinya', 'ingat', 'stop', 'kesimpulan', 'melemah', 'naik drastis']):
            if not any(abs(m['start'] - p['start']) < 2.5 for m in moments):
                # Pick 1-3 emphatic words
                words_in_p = p['words']
                emphasis_word = " ".join([w['w'] for w in words_in_p[:min(3, len(words_in_p))]]).upper()
                for w in words_in_p:
                    if w['w'].lower() in ['bukan', 'tapi', 'rem', 'melemah', 'ingat', 'stop']:
                        emphasis_word = w['w'].upper()
                        break
                moments.append({
                    'type': 'emphasis',
                    'start': p['start'],
                    'end': min(dur - 0.2, p['start'] + 2.8),
                    'text': p['text'],
                    'word': emphasis_word
                })

    return {
        'topic': topic,
        'full_text': full_text,
        'phrases': phrases,
        'moments': moments
    }


def smart_split_headline(text):
    """Splits headline text at natural linguistic boundaries, never breaking middle words."""
    clean = text.replace('|', ' ').strip()
    words = clean.split()
    if len(words) <= 3:
        return clean.upper(), ""
    mid = len(words) // 2
    best_idx = mid
    for i in range(1, len(words) - 1):
        prev_w = words[i - 1]
        w = words[i].lower().rstrip(',:;?')
        if prev_w.endswith((',', ':', ';', '?')):
            best_idx = i
            break
        if w in ('artinya', 'karena', 'bahwa', 'yaitu', 'seperti', 'adalah', 'sudah', 'tapi', 'yang', 'dari', 'sejak', 'untuk', 'dengan', 'itu', 'ini'):
            best_idx = i
            break
    ln1 = " ".join(words[:best_idx]).upper()
    ln2 = " ".join(words[best_idx:]).upper()
    return ln1, ln2


def determine_creative_direction(topic, user_style=None, clean_audio=False):
    """Determines optimal signature style, color palette, and audio treatment."""
    style_idx = 1
    if user_style:
        prompt_lower = str(user_style).lower()
        m = re.search(r'\d+', prompt_lower)
        if m:
            style_idx = int(m.group(0))
        elif any(k in prompt_lower for k in ['glass', 'spatial', '3d', 'refraction']):
            style_idx = 12
        elif any(k in prompt_lower for k in ['typo', 'podcast', 'clean', 'editorial', 'minimal']):
            style_idx = 11
        elif any(k in prompt_lower for k in ['doc', 'brutalist', 'crimson', 'investigative']):
            style_idx = 3
        elif any(k in prompt_lower for k in ['tech', 'fintech', 'terminal', 'cyber', 'code']):
            style_idx = 4
        elif any(k in prompt_lower for k in ['fast', 'hustle', 'hormozi', 'punchy', 'kinetic']):
            style_idx = 5
        elif any(k in prompt_lower for k in ['aesthetic', 'vlog', 'warm', 'lifestyle', 'wellness']):
            style_idx = 6
        elif any(k in prompt_lower for k in ['corporate', 'authority', 'linkedin', 'business']):
            style_idx = 7
        elif any(k in prompt_lower for k in ['saas', 'dark', 'software', 'app']):
            style_idx = 8
        elif any(k in prompt_lower for k in ['retro', 'vintage', 'grain', 'film', 'noir']):
            style_idx = 9
        elif any(k in prompt_lower for k in ['pop', 'zine', 'scrapbook']):
            style_idx = 10
        elif any(k in prompt_lower for k in ['social', 'contrast', 'viral', 'critique']):
            style_idx = 13
        else:
            style_idx = 1
    else:
        # Autonomous mapping from semantic topic
        if topic == 'philosophy_religion':
            style_idx = 2   # Editorial Magazine (Vox Explainer)
        elif topic == 'finance_economics':
            style_idx = 12  # Liquid Glass Spatial
        elif topic == 'tech_developer':
            style_idx = 4   # Apple Glass / Fintech Terminal
        elif topic == 'social_investigative':
            style_idx = 3   # Bold Documentary (Brutalist)
        elif topic == 'business_marketing':
            style_idx = 1   # High-Retention Creator
        elif topic == 'motivation_mindset':
            style_idx = 5   # Kinetic Viral
        elif topic == 'health_wellness':
            style_idx = 6   # Soft Pastel / Wellness
        elif topic == 'podcast_interview':
            style_idx = 11  # Editorial Motion Typography
        else:
            style_idx = 1   # High-Retention Creator

    palettes = {
        1: {'name': 'High-Retention Creator', 'pri': '#00F0FF', 'sec': '#FFD166', 'danger': '#E82434'},
        2: {'name': 'Editorial Magazine (Vox Style)', 'pri': '#F4E9D8', 'sec': '#FFD166', 'danger': '#C83228'},
        3: {'name': 'Bold Documentary (Brutalist)', 'pri': '#E82434', 'sec': '#FFFFFF', 'danger': '#E82434'},
        4: {'name': 'Apple Glass / Fintech Terminal', 'pri': '#38BDF8', 'sec': '#34D399', 'danger': '#EF4444'},
        5: {'name': 'Kinetic Viral (High Energy)', 'pri': '#FACC15', 'sec': '#00F0FF', 'danger': '#EF4444'},
        6: {'name': 'Soft Pastel / Minimalist Wellness', 'pri': '#38BDF8', 'sec': '#F4E9D8', 'danger': '#E82434'},
        7: {'name': 'Cyberpunk Neon Tech', 'pri': '#E024C3', 'sec': '#00F0FF', 'danger': '#FF3366'},
        8: {'name': 'Dark Mode SaaS Authority', 'pri': '#818CF8', 'sec': '#34D399', 'danger': '#F43F5E'},
        9: {'name': 'Monochrome Film Noir', 'pri': '#F8FAFC', 'sec': '#94A3B8', 'danger': '#E2E8F0'},
        10: {'name': 'Pop Art / Zine Scrapbook', 'pri': '#FDE047', 'sec': '#38BDF8', 'danger': '#F43F5E'},
        11: {'name': 'Editorial Motion Typography', 'pri': '#FFD166', 'sec': '#F4E9D8', 'danger': '#E82434'},
        12: {'name': 'Full Liquid Glass Spatial', 'pri': '#00F0FF', 'sec': '#34D399', 'danger': '#E82434'},
        13: {'name': 'Social Value / Contrast Critique', 'pri': '#60C4F8', 'sec': '#FFD166', 'danger': '#E82434'},
    }
    config = palettes.get(style_idx, palettes[1])

    # Audio rules: Clean Audio / Zero SFX
    sfx_allowed = not clean_audio and style_idx not in (9, 11)

    return {
        'style_index': style_idx,
        'style_name': config['name'],
        'palette': config,
        'sfx_allowed': sfx_allowed
    }


def build_blueprint(footage_meta, semantic_info, creative_dir, out_plan_path):
    """Assembles an intelligent, timestamped effects plan and editorial blueprint strictly clamped to footage duration."""
    dur = footage_meta['duration']
    moments = semantic_info.get('moments', [])
    style_idx = creative_dir['style_index']
    sfx_allowed = creative_dir['sfx_allowed']
    col_pri = creative_dir['palette']['pri']
    col_sec = creative_dir['palette']['sec']
    col_danger = creative_dir['palette']['danger']

    effects = []
    hide_captions_ranges = []
    last_card_end = 0.0

    # 1. Opening Hook (0.0 to min(2.8s, dur - 0.2s))
    if dur > 1.5:
        hook_m = next((m for m in moments if m['type'] == 'hook'), None)
        hook_raw = hook_m['text'] if hook_m else "PERTANYAAN KUNCI"
        line1, line2 = smart_split_headline(hook_raw)
        if not line2:
            line2 = "SIMAK PENJELASANNYA"

        hook_end = min(2.8, dur - 0.2)
        topic_tag = semantic_info.get('topic', 'PERSPEKTIF').replace('_', ' ').upper()
        effects.append({
            'fx': 'hook-card',
            'start': 0.0,
            'end': hook_end,
            'tag': f"GAGASAN UTAMA  |  {topic_tag}",
            'line1': line1,
            'line2': line2,
            'zoom': 1.10,
            'color': col_sec
        })
        hide_captions_ranges.append(f"0.0-{hook_end:.1f}")
        last_card_end = hook_end

    # 2. Iterate through detected moments and place contextual elements with editorial restraint
    for m in moments:
        if m['type'] == 'hook':
            continue

        m_start = m.get('start', 0.0)
        # Avoid clutter: enforce at least 2.5s gap between cards and ensure within duration
        if m_start < last_card_end + 2.2 or m_start >= dur - 1.2:
            continue

        if m['type'] == 'data':
            v1 = m.get('v1')
            v2 = m.get('v2')
            if v1 and v2:
                # Comparison card
                c_end = min(dur - 0.2, m_start + 3.8)
                effects.append({
                    'fx': 'data-compare',
                    'start': round(m_start, 2),
                    'end': round(c_end, 2),
                    'header': f"DATA ANALISIS  |  {semantic_info.get('topic', 'METRIK').replace('_', ' ').upper()}",
                    'v1': str(v1),
                    'sub1': 'KONDISI AWAL',
                    'v2': str(v2),
                    'sub2': 'PERUBAHAN TERBARU',
                    'delta': f"DELTA ({v1} -> {v2})",
                    'color': col_sec
                })
                hide_captions_ranges.append(f"{m_start:.1f}-{c_end:.1f}")
                last_card_end = c_end
            elif m.get('matches'):
                # Single metric pop
                val = m['matches'][0]
                p_end = min(dur - 0.2, m_start + 2.5)
                effects.append({
                    'fx': 'pop-word',
                    'start': round(m_start, 2),
                    'end': round(p_end, 2),
                    'text': val.upper(),
                    'color': col_sec,
                    'size': 'big',
                    'behind': True
                })
                last_card_end = p_end

        elif m['type'] == 'question':
            q_text = m.get('text', 'PERTANYAAN')
            ln1, ln2 = smart_split_headline(q_text)
            q_end = min(dur - 0.2, m_start + 3.5)
            effects.append({
                'fx': 'headline-box',
                'start': round(m_start, 2),
                'end': round(q_end, 2),
                'text': f"{ln1}|{ln2}" if ln2 else ln1,
                'zoom': 1.10
            })
            hide_captions_ranges.append(f"{m_start:.1f}-{q_end:.1f}")
            last_card_end = q_end

        elif m['type'] == 'enumeration':
            e_end = min(dur - 0.2, m_start + 4.5)
            effects.append({
                'fx': 'checklist',
                'start': round(m_start, 2),
                'end': round(e_end, 2),
                'title': 'Poin Penting',
                'color': col_pri,
                'text': '1. Analisis Situasi::Penting|2. Evaluasi Dampak::Kritis|3. Langkah Tindakan::Segera'
            })
            hide_captions_ranges.append(f"{m_start:.1f}-{e_end:.1f}")
            last_card_end = e_end

        elif m['type'] == 'emphasis':
            word = m.get('word', 'PENTING')
            e_end = min(dur - 0.2, m_start + 2.4)
            effects.append({
                'fx': 'lean-in',
                'start': round(m_start, 2),
                'end': round(e_end, 2),
                'zoom': 1.12
            })
            effects.append({
                'fx': 'pop-word',
                'start': round(m_start + 0.2, 2),
                'end': round(e_end, 2),
                'text': word,
                'color': col_danger if any(k in word.lower() for k in ['bukan', 'stop', 'salah', 'mitos']) else col_pri,
                'size': 'big',
                'behind': True
            })
            last_card_end = e_end

    # 3. Dynamic pacing fallback: If duration is long (> 12s) and space is wide, add subtle camera focus / push
    if dur > 12.0 and last_card_end < dur - 5.0:
        push_start = round(last_card_end + 1.5, 2)
        push_end = round(min(dur - 1.0, push_start + 4.0), 2)
        if push_end > push_start + 1.0:
            effects.append({
                'fx': 'slow-push',
                'start': push_start,
                'end': push_end,
                'push': 1.07
            })

    # 4. Captions with Safe Zone and dynamic overlay-aware hiding
    if footage_meta['has_audio']:
        effects.append({
            'fx': 'captions',
            'style': 'pill' if style_idx in (1, 5, 12, 13) else 'clean',
            'y': 0.74,
            'hide': "|".join(hide_captions_ranges)
        })

    # Ensure effects list is sorted by start timestamp
    effects = sorted(effects, key=lambda f_: f_.get('start') if f_.get('start') is not None else 0.0)

    plan = {
        'style': creative_dir['style_name'],
        'style_index': style_idx,
        'duration': round(dur, 2),
        'sfx': sfx_allowed,
        'sfx_volume': -4.0 if sfx_allowed else -99.0,
        'effects': effects
    }

    blueprint_meta = {
        'director': 'Antigravity Intelligent Video Director v2.1',
        'footage': {
            'file': os.path.basename(footage_meta['path']),
            'duration': dur,
            'resolution': f"{footage_meta['width']}x{footage_meta['height']}",
            'aspect_ratio': '9:16' if footage_meta['is_vertical'] else '16:9',
            'reframe_recommended': not footage_meta['is_vertical']
        },
        'creative_direction': {
            'concept': creative_dir['style_name'],
            'sound_design': 'Strict Clean Audio (Zero SFX)' if not sfx_allowed else 'Subtle Contextual UI SFX (-4dB)',
            'safe_zone': 'Strict Universal Social (Top >= 13.5%, Bottom <= 77.2%, Right <= 83.5%)',
            'face_protection': 'Depth masking & face tracking enabled'
        },
        'editorial_beats': len(effects),
        'preview_required': True
    }

    os.makedirs(os.path.dirname(os.path.abspath(out_plan_path)), exist_ok=True)
    with open(out_plan_path, 'w', encoding='utf-8') as f:
        json.dump(plan, f, indent=2)

    blueprint_path = out_plan_path.replace('.json', '_blueprint.json')
    with open(blueprint_path, 'w', encoding='utf-8') as f:
        json.dump({'meta': blueprint_meta, 'plan': plan}, f, indent=2)

    print(f"Generated Plan: {out_plan_path} ({len(effects)} effects, dur={dur:.1f}s)")
    print(f"Generated Blueprint: {blueprint_path}")
    return plan, blueprint_meta


def main():
    ap = argparse.ArgumentParser(description="Autonomous Creative Director for Video Editing")
    ap.add_argument("cmd", choices=["analyze", "blueprint"])
    ap.add_argument("videos", nargs="+", help="Input video path(s)")
    ap.add_argument("--words", help="Word-level timestamps JSON (will transcribe if omitted)")
    ap.add_argument("--out-plan", default="work/plan.json", help="Output effects plan JSON")
    ap.add_argument("--style", help="Force specific style name or number")
    ap.add_argument("--clean-audio", action="store_true", help="Force Zero SFX mode")
    args = ap.parse_args()

    # Handle folder input (multi-take or raw footage folder)
    if len(args.videos) == 1 and os.path.isdir(args.videos[0]):
        folder = args.videos[0]
        valid_exts = ('.mp4', '.mov', '.mkv', '.webm', '.avi')
        found_videos = [
            os.path.join(folder, f)
            for f in sorted(os.listdir(folder))
            if f.lower().endswith(valid_exts)
        ]
        if not found_videos:
            sys.exit(f"No video files found in folder: {folder}")
        args.videos = found_videos
        print(f"Loaded {len(found_videos)} take(s) from directory: {folder}")

    primary_video = args.videos[0]
    print(f"--- [Stage 1/4] Probing visual composition & face geometry: {os.path.basename(primary_video)} ---", flush=True)
    f_meta = probe_footage(primary_video)
    print(f"Dimensions: {f_meta['width']}x{f_meta['height']}, FPS: {f_meta['fps']:.2f}, Duration: {f_meta['duration']:.2f}s", flush=True)
    if not f_meta['is_vertical']:
        print("  [NOTE] Footage is horizontal (16:9). Reframe to 9:16 vertical safe zone recommended.", flush=True)
    if f_meta['face']:
        print(f"YuNet Face Tracked: center=({f_meta['face']['cx']:.1f}, {f_meta['face']['cy']:.1f}), size={f_meta['face']['w']:.1f}x{f_meta['face']['h']:.1f}", flush=True)

    if len(args.videos) > 1:
        print(f"\n--- Multicam / Multi-Footage Probe ({len(args.videos)} clips) ---", flush=True)
        for idx, extra_v in enumerate(args.videos[1:], start=2):
            extra_meta = probe_footage(extra_v)
            print(f"  Clip #{idx} ({os.path.basename(extra_v)}): {extra_meta['width']}x{extra_meta['height']}, {extra_meta['duration']:.2f}s", flush=True)

    words_data = []
    # Check cache paths: out_plan directory words.json or video directory words.json
    plan_words = os.path.join(os.path.dirname(os.path.abspath(args.out_plan)), 'words.json')
    video_words = os.path.splitext(primary_video)[0] + '.words.json'
    w_path = args.words or (plan_words if os.path.exists(plan_words) else video_words)

    if os.path.exists(w_path):
        with open(w_path, 'r', encoding='utf-8') as f:
            words_data = json.load(f)
        print(f"--- [Stage 2/4] Speech Transcription: Loaded {len(words_data)} cached words from {os.path.basename(w_path)} (Instant Resume) ---", flush=True)
    elif f_meta['has_audio']:
        print("--- [Stage 2/4] Transcribing speech with faster-whisper (word timestamps)... ---", flush=True)
        import words as words_mod
        words_data = words_mod.transcribe(primary_video)
        # Cache to out_plan directory so retry doesn't re-transcribe
        try:
            with open(plan_words, 'w', encoding='utf-8') as f:
                json.dump(words_data, f, indent=1)
        except Exception:
            pass
        try:
            with open(w_path, 'w', encoding='utf-8') as f:
                json.dump(words_data, f, indent=1)
        except Exception:
            pass
        print(f"Transcribed and cached {len(words_data)} words successfully.", flush=True)

    print("\n--- [Stage 3/4] Semantic Intelligence & Narrative Beat Analysis ---", flush=True)
    sem_info = semantic_analysis(words_data, f_meta['duration'])
    print(f"Detected Content Topic: {sem_info['topic'].upper()}", flush=True)
    print(f"Identified {len(sem_info['moments'])} key narrative beats (hooks, questions, data, punchlines)", flush=True)

    c_dir = determine_creative_direction(sem_info['topic'], args.style, args.clean_audio)
    print(f"Selected Signature Style: {c_dir['style_name']}", flush=True)
    print(f"Audio Design: {'Clean Audio (ZERO SFX Mode)' if not c_dir['sfx_allowed'] else 'Contextual Dynamic SFX'}", flush=True)

    print("\n--- [Stage 4/4] Building Production Blueprint & Execution Plan ---", flush=True)
    build_blueprint(f_meta, sem_info, c_dir, args.out_plan)


if __name__ == '__main__':
    main()
