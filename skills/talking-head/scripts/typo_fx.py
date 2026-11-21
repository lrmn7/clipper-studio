#!/usr/bin/env python3
"""Style 11 â€” Editorial Motion Typography Engine (Podcast Edition, Zero Karaoke, Zero SFX).

Curated editorial typography compositions with AI depth-masking (behind head),
cinematic spotlight lighting, strict face/eye-safe placement, and 10 elevated
kinetic motion styles:

  1. one-big-slam     Monumental display headline slams in with micro-shake & shockwave
  2. splits           Two editorial lines split cleanly from a drawing hairline rule
  3. heavy-landing    Weighted typography drops under gravity, squashes on baseline & rebounds
  4. rollout          Stacked typography unrolls cleanly out of an architectural accent rule
  5. dot-hop          Refined glowing editorial dot arcs gracefully between key headline anchors
  6. sticker-stack    High-fashion matte editorial tags slam in at subtle alternating angles
  7. slingshot        Kinetic tension pull-back then elastic snap with subtle motion echo
  8. traced-outline   Monumental hollow stroked display type traces in then flood-fills solid
  9. plucked-string   Minimalist baseline tension string bends & vibrates with damped physics
 10. tumbling-letter  Staggered individual letters tumble in with crisp spring rotation

Every composition protects the speaker's eyes & face (either behind the head via AI person
segmentation, or strictly clamped below the chin via face_safe_y). No karaoke subtitles.
No synthetic sound effects by default (preserves clean studio podcast audio).
"""
import argparse, json, math, os, subprocess, sys
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FX_SCRIPTS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, FX_SCRIPTS)
import fx

# Editorial Podcast Palette
WHITE = (255, 255, 255)
CREAM = (245, 236, 222)
INK = (16, 16, 20)
CHARCOAL = (26, 26, 32)
GOLD = (242, 198, 92)
CRIMSON = (232, 64, 76)
MINT = (62, 212, 128)
CYAN = (96, 196, 248)


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease_out(x):
    x = clamp(x)
    return 1.0 - (1.0 - x) ** 3


def ease_inout(x):
    x = clamp(x)
    return 3.0 * x * x - 2.0 * x * x * x


def ease_in(x):
    x = clamp(x)
    return x * x


def ease_back(x, s=1.55):
    x = clamp(x)
    x -= 1.0
    return x * x * ((s + 1.0) * x + s) + 1.0


def rgb(v, default):
    if v is None:
        return default
    if isinstance(v, (list, tuple)):
        return tuple(int(x) for x in v[:3])
    v = str(v).lstrip("#")
    return tuple(int(v[i:i + 2], 16) for i in (0, 2, 4))


def env_alpha(lt, dur, t_in=0.14, t_out=0.22):
    return clamp(lt / max(0.01, t_in)) * clamp((dur - lt) / max(0.01, t_out))


def face_safe_y(c, pref_y=0.71, half_h=90):
    """Hard guarantee: foreground typography stays cleanly below chin & eyes, above Reels UI."""
    chin = c.fy + c.fw * 1.08
    lo = chin + half_h + c.H * 0.03
    hi = c.H * 0.80
    return clamp(max(c.H * pref_y, lo), c.H * 0.60, hi)


def head_top_y(seg, c):
    return seg["_top"] if seg.get("_top") is not None else (c.fy - c.fw * 0.92)


def tracked_rgba(text, size, kind="mono", fill=CREAM, spacing=0.0, shadow=8, stroke=0, stroke_fill=INK, alpha_fill=255):
    f = fx.font(kind, size)
    chars = list(text)
    if not chars:
        return Image.new("RGBA", (4, 4), (0, 0, 0, 0))
    total_w = sum(f.getlength(ch) for ch in chars) + spacing * max(0, len(chars) - 1)
    bb = f.getbbox("AgÃ„y", stroke_width=stroke)
    gh = bb[3] - bb[1]
    pad = int(size * 0.22 + shadow * 2.2 + stroke * 2) + 8
    w = max(8, int(math.ceil(total_w)) + 2 * pad)
    h = max(8, int(math.ceil(gh)) + 2 * pad)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))

    def draw_chars(target, dx, dy, col_fill, col_stroke=None):
        d = ImageDraw.Draw(target)
        x = pad + dx
        y = pad - bb[1] + dy
        for ch in chars:
            if stroke > 0 and col_stroke is not None:
                d.text((x, y), ch, font=f, fill=col_fill, stroke_width=stroke, stroke_fill=col_stroke)
            else:
                d.text((x, y), ch, font=f, fill=col_fill)
            x += f.getlength(ch) + spacing

    if shadow > 0:
        sh = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw_chars(sh, 0, int(shadow * 0.4), (0, 0, 0, 175), (0, 0, 0, 175) if stroke > 0 else None)
        im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(shadow)))
    draw_chars(im, 0, 0, tuple(fill) + (alpha_fill,), tuple(stroke_fill) + (255,) if stroke > 0 else None)
    return im


def fit_tracked(text, max_w, start_sz, kind="anton", spacing_ratio=0.0, **kw):
    sz = start_sz
    while sz > 18:
        f = fx.font(kind, sz)
        sp = sz * spacing_ratio
        tw = sum(f.getlength(ch) for ch in text) + sp * max(0, len(text) - 1)
        if tw <= max_w:
            break
        sz *= 0.93
    return tracked_rgba(text, sz, kind=kind, spacing=sz * spacing_ratio, **kw), sz


def comp_pil(c, im, cx, cy, sx=1.0, sy=1.0, rot=0.0, alpha=1.0, behind=False, anchor="center"):
    if alpha <= 0.01 or sx <= 0.02 or sy <= 0.02:
        return
    nw = max(1, int(round(im.width * sx)))
    nh = max(1, int(round(im.height * sy)))
    if nw != im.width or nh != im.height:
        im = im.resize((nw, nh), Image.BILINEAR)
    if abs(rot) > 0.1:
        im = im.rotate(rot, Image.BICUBIC, expand=True)
    x = cx - im.width / 2.0
    y = (cy - im.height) if anchor == "bottom" else (cy - im.height / 2.0)
    fx.comp(c, im, x, y, alpha=alpha, behind=behind)


def apply_editorial_spotlight(c, seg, lt, dur):
    """Optional cinematic studio spotlight: dims room behind speaker, adds subtle warm rim glow & gentle push."""
    sp = seg.get("spotlight")
    if not sp:
        return
    k = clamp(lt / 0.28) * clamp((dur - lt) / 0.28)
    if k <= 0.01:
        return
    # Gentle studio push-in (never jarring)
    push = float(seg.get("push", 1.07))
    if push > 1.005:
        fx.face_cam(c, 1.0 + (push - 1.0) * ease_inout(lt / dur), 0.42)
    tint = np.float32(rgb(seg.get("spot_color") or seg.get("color"), GOLD)) / 255.0
    strength = float(seg.get("spot_strength", 0.68))
    xx, yy = fx.grid(c)
    d = ((xx - c.fx) / (c.W * 0.54)) ** 2 + ((yy - (c.fy + c.H * 0.14)) / (c.H * 0.48)) ** 2
    pool = np.clip(1.0 - d, 0.0, 1.0) ** 1.6
    bg_bright = 1.0 - k * strength * (1.0 - 0.38 * pool)
    fg_boost = 1.0 + 0.05 * k
    m = c.m[..., None]
    c.img = c.img * (bg_bright[..., None] * (1.0 - m) + fg_boost * m)
    # Soft studio rim glow behind shoulders/head
    halo = np.clip(cv2.GaussianBlur(c.m, (0, 0), c.W * 0.018) * 1.45 - c.m, 0.0, 1.0)
    c.img = np.clip(c.img + (halo * 0.32 * k)[..., None] * tint * (1.0 - m), 0.0, 1.0)


def draw_eyebrow(c, text, cx, cy, u, accent=GOLD, alpha=1.0, behind=False):
    if not text or alpha <= 0.01:
        return
    lbl, _ = fit_tracked(text.upper(), 780 * u, 24 * u, kind="mono", fill=accent, spacing_ratio=0.14, shadow=6 * u)
    comp_pil(c, lbl, cx, cy, 1.0, 1.0, 0.0, alpha, behind=behind)


def draw_sub_serif(c, text, cx, cy, u, fill=CREAM, alpha=1.0, max_w=860):
    if not text or alpha <= 0.01:
        return
    sub, _ = fit_tracked(text, max_w * u, 54 * u, kind="didoneib", fill=fill, spacing_ratio=0.0, shadow=12 * u)
    comp_pil(c, sub, cx, cy, 1.0, 1.0, 0.0, alpha)


def draw_pill_tag(c, text, cx, cy, u, bg=GOLD, fg=INK, alpha=1.0, scale=1.0):
    if not text or alpha <= 0.01:
        return
    lbl, _ = fit_tracked(text.upper(), 680 * u, 23 * u, kind="mono", fill=fg, spacing_ratio=0.10, shadow=0)
    pw, ph = int(lbl.width + 26 * u), int(lbl.height + 6 * u)
    pill = fx.rrect(pw, ph, ph / 2.0, tuple(bg) + (245,))
    pill.alpha_composite(lbl, ((pw - lbl.width) // 2, (ph - lbl.height) // 2))
    pill = fx.shadowed(pill, blur=int(10 * u), dy=int(5 * u), alpha=110)
    comp_pil(c, pill, cx, cy, scale, scale, 0.0, alpha)


def cached(seg, key, fn):
    st = seg.setdefault("_cache", {})
    if key not in st:
        st[key] = fn()
    return st[key]


# ==============================================================================
# 10 ELEVATED EDITORIAL KINETIC TYPOGRAPHY EFFECTS (ZERO KARAOKE)
# ==============================================================================

def fx_one_big_slam(c, seg, lt, dur):
    """1. one-big-slam: Monumental display title slams in (behind head or face-safe chest) with shockwave & sub-hook."""
    u = c.W / 1080.0
    col = rgb(seg.get("color"), GOLD)
    al = env_alpha(lt, dur, 0.06, 0.24)
    if al <= 0:
        return
    behind = bool(seg.get("behind", False))
    word = str(seg.get("text", "BI RATE")).upper()
    eyebrow = seg.get("eyebrow", "")
    sub = seg.get("sub", "")

    # Micro camera jolt on impact
    if 0.11 <= lt < 0.25:
        mag = (0.25 - lt) / 0.14 * 7.5 * u
        rnd = np.random.default_rng(int(c.t * 60))
        M = np.float32([[1, 0, rnd.uniform(-mag, mag)], [0, 1, rnd.uniform(-mag, mag)]])
        c.img = cv2.warpAffine(c.img, M, (c.W, c.H), borderMode=cv2.BORDER_REFLECT)

    if behind:
        room = max(c.H * 0.12, head_top_y(seg, c) - c.H * 0.03)
        im, sz = cached(seg, "w", lambda: fit_tracked(word, 940 * u, 250 * u, kind="pop", fill=col, spacing_ratio=-0.02, shadow=22 * u))
        def_cy = max(head_top_y(seg, c) - sz * 0.22, c.H * 0.05 + im.height * 0.35)
        cy = float(seg["y"]) * c.H if seg.get("y") is not None else def_cy
    else:
        im, sz = cached(seg, "w", lambda: fit_tracked(word, 880 * u, 138 * u, kind="pop", fill=col, stroke=int(3 * u), stroke_fill=INK, shadow=18 * u))
        cy = face_safe_y(c, float(seg.get("y", 0.72)), im.height * 0.45)

    # Slam physics: 1.72x -> 1.0x in 0.12s + crisp squash bounce
    if lt < 0.12:
        p = ease_in(lt / 0.12)
        sx = sy = 1.72 - 0.72 * p
    else:
        q = clamp((lt - 0.12) / 0.18)
        b = 0.08 * math.sin(math.pi * q) * (1.0 - q)
        sx, sy = 1.0 + b, 1.0 - b

    # Horizontal shockwave line on impact
    if 0.11 <= lt < 0.36:
        rp = ease_out((lt - 0.11) / 0.25)
        lw = int(860 * u * rp)
        lh = max(3, int(5 * u * (1.0 - rp * 0.6)))
        bar = Image.new("RGBA", (max(8, lw), lh + 12), (0, 0, 0, 0))
        ImageDraw.Draw(bar).rectangle([0, 6, lw, 6 + lh], fill=col + (int(210 * (1.0 - rp)),))
        comp_pil(c, bar, c.W / 2.0, cy + sz * 0.52, 1.0, 1.0, 0.0, al, behind=behind)

    comp_pil(c, im, c.W / 2.0, cy, sx, sy, 0.0, al, behind=behind)

    # Editorial eyebrow pill + serif sub-hook cleanly separated
    if eyebrow or sub:
        if behind:
            yc_sub = face_safe_y(c, float(seg.get("sub_y", 0.74)), 110 * u)
            if eyebrow and lt > 0.18:
                ep = ease_back((lt - 0.18) / 0.24)
                draw_pill_tag(c, eyebrow, c.W / 2.0, yc_sub - 64 * u, u, bg=col, fg=INK, alpha=al * clamp((lt - 0.18) / 0.08), scale=0.75 + 0.25 * ep)
            if sub and lt > 0.28:
                sp = ease_out((lt - 0.28) / 0.28)
                draw_sub_serif(c, sub, c.W / 2.0, yc_sub + 14 * u + (1.0 - sp) * 26 * u, u, fill=CREAM, alpha=al * sp)
        else:
            if eyebrow and lt > 0.18:
                ep = ease_back((lt - 0.18) / 0.24)
                draw_pill_tag(c, eyebrow, c.W / 2.0, cy - sz * 0.96, u, bg=CREAM, fg=INK, alpha=al * clamp((lt - 0.18) / 0.08), scale=0.75 + 0.25 * ep)
            if sub and lt > 0.28:
                sp = ease_out((lt - 0.28) / 0.28)
                draw_sub_serif(c, sub, c.W / 2.0, cy + sz * 0.88 + (1.0 - sp) * 20 * u, u, fill=CREAM, alpha=al * sp)


def fx_splits(c, seg, lt, dur):
    """2. splits: Editorial two-line split opening vertically/horizontally from a glowing center hairline rule."""
    u = c.W / 1080.0
    col = rgb(seg.get("color"), GOLD)
    al = env_alpha(lt, dur, 0.10, 0.22)
    if al <= 0:
        return
    parts = [p.strip() for p in str(seg.get("text", "KENAPA BI|naikkan bunga?")).split("|")]
    top_txt = parts[0]
    bot_txt = parts[1] if len(parts) > 1 else ""
    eyebrow = seg.get("eyebrow", "")
    behind_word = seg.get("behind_text", "")

    if behind_word:
        bw, bsz = cached(seg, "bw", lambda: fit_tracked(behind_word.upper(), 940 * u, 240 * u, kind="pop", fill=col, spacing_ratio=-0.02, shadow=20 * u))
        bp = ease_out(lt / 0.34)
        bcy = max(head_top_y(seg, c) - bsz * 0.20, c.H * 0.05 + bw.height * 0.34)
        comp_pil(c, bw, c.W / 2.0, bcy + (1.0 - bp) * 28 * u, 1.0, 1.0, 0.0, al * bp, behind=True)

    yc = face_safe_y(c, float(seg.get("y", 0.72)), 140 * u)
    im_t, szt = cached(seg, "t", lambda: fit_tracked(top_txt.upper(), 860 * u, 76 * u, kind="montb", fill=WHITE, spacing_ratio=0.04, shadow=14 * u))
    im_b, szb = cached(seg, "b", lambda: fit_tracked(bot_txt, 880 * u, 96 * u, kind="didoneib", fill=col, spacing_ratio=0.0, shadow=16 * u)) if bot_txt else (None, 0)

    # Center hairline rule draws outward from center
    rp = ease_out(lt / 0.26)
    rw = max(8, int(min(840 * u, max(im_t.width, im_b.width if im_b else 0) * 0.88) * rp))
    rule = Image.new("RGBA", (rw, 10), (0, 0, 0, 0))
    ImageDraw.Draw(rule).rounded_rectangle([0, 3, rw - 1, 7], 2, fill=col + (235,))
    comp_pil(c, rule, c.W / 2.0, yc, 1.0, 1.0, 0.0, al)

    # Split outward: top rises slightly left-to-center, bottom drops slightly right-to-center from behind the rule
    p1 = ease_back((lt - 0.10) / 0.34, s=1.2)
    p2 = ease_back((lt - 0.22) / 0.36, s=1.2)
    if lt > 0.10:
        comp_pil(c, im_t, c.W / 2.0 - (1.0 - p1) * 48 * u, yc - szt * 0.68 + (1.0 - p1) * 34 * u, 1.0, 1.0, 0.0, al * clamp((lt - 0.10) / 0.12))
    if im_b is not None and lt > 0.22:
        comp_pil(c, im_b, c.W / 2.0 + (1.0 - p2) * 48 * u, yc + szb * 0.62 - (1.0 - p2) * 34 * u, 1.0, 1.0, 0.0, al * clamp((lt - 0.22) / 0.12))
    if eyebrow and lt > 0.32:
        draw_eyebrow(c, eyebrow, c.W / 2.0, yc - szt * 1.48, u, accent=CREAM, alpha=al * ease_out((lt - 0.32) / 0.22))


def fx_heavy_landing(c, seg, lt, dur):
    """3. heavy-landing: Big sculptural stat/headline drops under gravity, squashes flat on baseline, rebounds."""
    u = c.W / 1080.0
    col = rgb(seg.get("color"), GOLD)
    al = env_alpha(lt, dur, 0.06, 0.22)
    if al <= 0:
        return
    behind = bool(seg.get("behind", False))
    main_txt = str(seg.get("text", "6,00%")).upper()
    sub = seg.get("sub", "")
    eyebrow = seg.get("eyebrow", "")

    if behind:
        im, sz = cached(seg, "m", lambda: fit_tracked(main_txt, 940 * u, 235 * u, kind="pop", fill=col, spacing_ratio=-0.02, shadow=22 * u))
        y_base = max(head_top_y(seg, c) + sz * 0.26, c.H * 0.06 + im.height * 0.80)
    else:
        im, sz = cached(seg, "m", lambda: fit_tracked(main_txt, 880 * u, 134 * u, kind="bold", fill=col, stroke=int(3 * u), stroke_fill=INK, shadow=16 * u))
        y_base = face_safe_y(c, float(seg.get("y", 0.72)), 110 * u) + sz * 0.42

    t_drop = 0.18
    if lt < t_drop:
        p = ease_in(lt / t_drop)
        dy = -(1.0 - p) * 210 * u
        sx = 0.88 + 0.12 * p
        sy = 1.20 - 0.20 * p
        sh_sc = 0.25 + 0.75 * p
    else:
        q = lt - t_drop
        dy = 0.0
        sq = 0.30 * math.exp(-9.0 * q) * math.cos(22.0 * q)
        sx = 1.0 + sq
        sy = 1.0 - sq * 0.82
        sh_sc = 1.0 + sq * 0.85

    # Ground contact shadow
    if not behind:
        sw = max(20, int(im.width * 0.72 * sh_sc))
        sh = max(8, int(22 * u))
        gsh = Image.new("RGBA", (sw + 32, sh + 32), (0, 0, 0, 0))
        ImageDraw.Draw(gsh).ellipse([16, 16, 16 + sw, 16 + sh], fill=(0, 0, 0, 150))
        gsh = gsh.filter(ImageFilter.GaussianBlur(8 * u))
        comp_pil(c, gsh, c.W / 2.0, y_base - 8 * u, 1.0, 1.0, 0.0, al)

    comp_pil(c, im, c.W / 2.0, y_base + dy, sx, sy, 0.0, al, behind=behind, anchor="bottom")

    # Supporting mono/serif editorial context cleanly below chin
    yc_ctx = face_safe_y(c, float(seg.get("sub_y", 0.74)), 90 * u) if behind else (y_base + 40 * u)
    if eyebrow and lt > 0.22:
        draw_eyebrow(c, eyebrow, c.W / 2.0, yc_ctx - (34 * u if sub else 0), u, accent=CREAM, alpha=al * ease_out((lt - 0.22) / 0.20))
    if sub and lt > 0.30:
        draw_sub_serif(c, sub, c.W / 2.0, yc_ctx + (22 * u if eyebrow else 0), u, fill=WHITE, alpha=al * ease_out((lt - 0.30) / 0.24))


def fx_rollout(c, seg, lt, dur):
    """4. rollout: Architectural stacked editorial lines smoothly mask-roll out from a vertical accent bar."""
    u = c.W / 1080.0
    col = rgb(seg.get("color"), CYAN)
    al = env_alpha(lt, dur, 0.10, 0.22)
    if al <= 0:
        return
    lines = [ln.strip() for ln in str(seg.get("text", "KENAPA PEMERINTAH|naikkan suku bunga?")).split("|") if ln.strip()]
    delays = [float(x) for x in str(seg["delays"]).split("|")] if seg.get("delays") else [0.10 + 0.22 * i for i in range(len(lines))]
    eyebrow = seg.get("eyebrow", "")

    n = len(lines)
    yc = face_safe_y(c, float(seg.get("y", 0.72)), (55 * n + 40) * u)
    # Build line images (alternating crisp sans & italic serif for editorial luxury, or clean numbered audit rows)
    is_list = n >= 3
    ims = cached(seg, "ims", lambda: [
        fit_tracked(
            ln.upper() if (is_list or i == 0) else ln,
            800 * u,
            (54 if is_list else (62 if i == 0 else 86)) * u,
            kind=("uib" if (is_list or i == 0) else "didoneib"),
            fill=(WHITE if (is_list and i != n - 1) or i == 0 else col),
            spacing_ratio=(0.03 if (is_list or i == 0) else 0.0),
            shadow=12 * u
        )[0]
        for i, ln in enumerate(lines)
    ])

    row_h = (82 if is_list else 98) * u
    block_h = row_h * n
    x_bar = c.W * 0.12
    y_top = yc - block_h / 2.0

    # Vertical architectural accent bar
    bp = ease_out(lt / 0.28)
    bh = max(12, int(block_h * bp))
    bar = Image.new("RGBA", (int(18 * u), bh + 16), (0, 0, 0, 0))
    ImageDraw.Draw(bar).rounded_rectangle([6, 8, int(12 * u), 8 + bh], 3, fill=col + (255,))
    bar = Image.alpha_composite(bar.filter(ImageFilter.GaussianBlur(3 * u)), bar)
    fx.comp(c, bar, x_bar - 6, y_top - 8, alpha=al)

    if eyebrow and lt > 0.06:
        eb, _ = fit_tracked(eyebrow.upper(), 720 * u, 22 * u, kind="mono", fill=col, spacing_ratio=0.14, shadow=6 * u)
        fx.comp(c, eb, x_bar + 28 * u, y_top - eb.height - 6 * u, alpha=al * ease_out(lt / 0.22))

    # Each line rolls smoothly out to the right from behind the vertical bar
    for i, im in enumerate(ims):
        t0 = delays[i] if i < len(delays) else (0.10 + 0.22 * i)
        if lt < t0:
            continue
        p = ease_out((lt - t0) / 0.34)
        vis_w = max(2, int(im.width * p))
        crop = im.crop((0, 0, vis_w, im.height))
        slide = (1.0 - p) * 28 * u
        fx.comp(c, crop, x_bar + 24 * u - slide, y_top + i * row_h + (row_h - im.height) / 2.0, alpha=al * clamp((lt - t0) / 0.08))


def fx_dot_hop(c, seg, lt, dur):
    """5. dot-hop: Refined editorial anchor points with a glowing accent dot arcing between headline pillars (NOT karaoke)."""
    u = c.W / 1080.0
    col = rgb(seg.get("color"), GOLD)
    al = env_alpha(lt, dur, 0.10, 0.22)
    if al <= 0:
        return
    anchors = [a.strip() for a in str(seg.get("text", "SIMPEL|DUA ALASAN")).split("|") if a.strip()]
    hops = [float(x) for x in str(seg["hops"]).split("|")] if seg.get("hops") else [0.15 + i * (dur * 0.62 / max(1, len(anchors))) for i in range(len(anchors))]
    eyebrow = seg.get("eyebrow", "")

    yc = face_safe_y(c, float(seg.get("y", 0.72)), 110 * u)
    # Fit all anchor pillars nicely across the width
    ims = cached(seg, "anc", lambda: [
        fit_tracked(a.upper(), (820 / max(1, len(anchors))) * u, 74 * u, kind="montb", fill=WHITE, spacing_ratio=0.03, shadow=14 * u)[0]
        for a in anchors
    ])
    ims_hi = cached(seg, "anchi", lambda: [
        fit_tracked(a.upper(), (820 / max(1, len(anchors))) * u, 74 * u, kind="montb", fill=col, spacing_ratio=0.03, shadow=16 * u)[0]
        for a in anchors
    ])

    gap = 64 * u
    tot_w = sum(im.width for im in ims) + gap * max(0, len(ims) - 1)
    x = c.W / 2.0 - tot_w / 2.0
    cxs = []
    for im in ims:
        cxs.append(x + im.width / 2.0)
        x += im.width + gap

    # Active anchor index
    cur = 0
    for idx, ht in enumerate(hops):
        if lt >= ht:
            cur = idx

    if eyebrow:
        draw_eyebrow(c, eyebrow, c.W / 2.0, yc - 172 * u, u, accent=CREAM, alpha=al * ease_out(lt / 0.25))

    # Draw delicate dotted arc connector between anchors
    if len(cxs) >= 2:
        arc_im = Image.new("RGBA", (c.W, int(220 * u)), (0, 0, 0, 0))
        ad = ImageDraw.Draw(arc_im)
        for idx in range(len(cxs) - 1):
            x0, x1 = cxs[idx], cxs[idx + 1]
            for s_i in range(1, 14):
                f = s_i / 14.0
                px = x0 + (x1 - x0) * f
                py = 145 * u - 4.0 * f * (1.0 - f) * 84 * u
                ad.ellipse([px - 2.5 * u, py - 2.5 * u, px + 2.5 * u, py + 2.5 * u], fill=col + (95,))
        fx.comp(c, arc_im, 0, yc - 210 * u, alpha=al * 0.85)

    # Draw anchor words
    for idx, (im_w, im_h, cx) in enumerate(zip(ims, ims_hi, cxs)):
        active = idx == cur
        reached = idx <= cur
        dt = max(0.0, lt - hops[idx])
        sc = 1.0 + 0.08 * math.sin(math.pi * clamp(dt / 0.24)) if active else 1.0
        comp_pil(c, im_h if active else im_w, cx, yc, sc, sc, 0.0, al * (1.0 if reached else 0.42))

    # Glowing editorial dot hopping on smooth parabolic arc
    if cur == 0:
        p = ease_out(clamp((lt - hops[0]) / 0.24))
        dx, dy = cxs[0], -76 * u - (1.0 - p) * 50 * u
        sq = 1.0
    else:
        p = clamp((lt - hops[cur]) / 0.30)
        x0, x1 = cxs[cur - 1], cxs[cur]
        dx = x0 + (x1 - x0) * ease_inout(p)
        dy = -76 * u - 4.0 * p * (1.0 - p) * 86 * u
        sq = 1.25 if (0.85 < p < 1.0) else 1.0

    r = int(14 * u)
    pad = int(26 * u)
    dot = Image.new("RGBA", (2 * (r + pad), 2 * (r + pad)), (0, 0, 0, 0))
    c0 = r + pad
    gl = Image.new("RGBA", dot.size, (0, 0, 0, 0))
    ImageDraw.Draw(gl).ellipse([c0 - r * 1.6, c0 - r * 1.6, c0 + r * 1.6, c0 + r * 1.6], fill=col + (210,))
    dot = Image.alpha_composite(dot, gl.filter(ImageFilter.GaussianBlur(10 * u)))
    ImageDraw.Draw(dot).ellipse([c0 - r, c0 - r, c0 + r, c0 + r], fill=col + (255,))
    comp_pil(c, dot, dx, yc + dy, sq, 1.0 / sq, 0.0, al)


def fx_sticker_stack(c, seg, lt, dur):
    """6. sticker-stack: High-fashion matte editorial cards (cream, charcoal, crimson) slam in tilted."""
    u = c.W / 1080.0
    al = env_alpha(lt, dur, 0.08, 0.22)
    if al <= 0:
        return
    items = [x.strip() for x in str(seg.get("text", "01 Â· INFLASI|02 Â· MATA UANG")).split("|") if x.strip()]
    delays = [float(x) for x in str(seg["delays"]).split("|")] if seg.get("delays") else [0.10 + 0.45 * i for i in range(len(items))]
    yc = face_safe_y(c, float(seg.get("y", 0.72)), 140 * u)

    styles = [
        (CREAM, INK, GOLD),
        (CHARCOAL, CREAM, CRIMSON),
        (CRIMSON, WHITE, CREAM),
    ]
    angles = (-2.6, 2.2, -1.8)

    def mk_card(i, txt):
        bg, fg, dot_c = styles[i % len(styles)]
        sz = 52 * u
        f = fx.font("popb", sz)
        tw = f.getlength(txt.upper())
        asc, desc = f.getmetrics()
        px, py = int(42 * u), int(24 * u)
        bw, bh = int(tw + 2 * px + 26 * u), int(asc + desc + 2 * py)
        r = int(bh * 0.24)
        brd = max(3, int(4 * u))
        im = Image.new("RGBA", (bw + 2 * brd, bh + 2 * brd), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle([0, 0, im.width - 1, im.height - 1], r + brd, fill=CREAM + (220,))
        d.rounded_rectangle([brd, brd, brd + bw - 1, brd + bh - 1], r, fill=bg + (255,))
        # Editorial accent dot on left of badge
        dr = 9 * u
        d.ellipse([brd + 26 * u - dr, brd + bh / 2.0 - dr, brd + 26 * u + dr, brd + bh / 2.0 + dr], fill=dot_c + (255,))
        d.text((brd + 52 * u, brd + bh / 2.0 - 2 * u), txt.upper(), font=f, fill=fg + (255,), anchor="lm")
        return fx.shadowed(im, blur=int(18 * u), dy=int(10 * u), alpha=145)

    cards = cached(seg, "cards", lambda: [mk_card(i, t) for i, t in enumerate(items)])
    step_y = 114 * u
    y0 = yc - (len(cards) - 1) * step_y / 2.0
    for i, card_im in enumerate(cards):
        t0 = delays[i] if i < len(delays) else 0.10 + 0.45 * i
        if lt < t0:
            continue
        q = ease_back((lt - t0) / 0.26, s=2.0)
        sc = 0.65 + 0.35 * q
        ox = (-18 * u if i % 2 == 0 else 18 * u)
        comp_pil(c, card_im, c.W / 2.0 + ox, y0 + i * step_y, sc, sc, angles[i % len(angles)], al * clamp((lt - t0) / 0.06))


def fx_slingshot(c, seg, lt, dur):
    """7. slingshot: Bold headline pulls back with kinetic tension then snaps into place behind head or below chin."""
    u = c.W / 1080.0
    col = rgb(seg.get("color"), CRIMSON)
    al = env_alpha(lt, dur, 0.08, 0.22)
    if al <= 0:
        return
    behind = bool(seg.get("behind", True))
    word = str(seg.get("text", "REM INFLASI")).upper()
    sub = seg.get("sub", "")

    if behind:
        im, sz = cached(seg, "w", lambda: fit_tracked(word, 940 * u, 210 * u, kind="pop", fill=col, spacing_ratio=-0.02, shadow=20 * u))
        cy = max(head_top_y(seg, c) - sz * 0.20, c.H * 0.05 + im.height * 0.35)
    else:
        im, sz = cached(seg, "w", lambda: fit_tracked(word, 880 * u, 118 * u, kind="pop", fill=col, stroke=int(3 * u), stroke_fill=INK, shadow=16 * u))
        cy = face_safe_y(c, float(seg.get("y", 0.72)), 100 * u)

    # Pull back right (0..0.14s) with horizontal stretch, then slingshot left into center with elastic overshoot
    if lt < 0.14:
        q = ease_out(lt / 0.14)
        dx = 140 * u + 85 * u * q
        sx, sy = 1.0 + 0.22 * q, 1.0 - 0.12 * q
    else:
        q = clamp((lt - 0.14) / 0.30)
        eb = ease_back(q, s=2.4)
        dx = 225 * u * (1.0 - eb)
        vel = math.sin(math.pi * q) * (1.0 - q * 0.5)
        sx, sy = 1.0 + 0.20 * vel, 1.0 - 0.11 * vel
        if q < 0.55:
            comp_pil(c, im, c.W / 2.0 + dx + 45 * u * (1.0 - q), cy, sx * 1.06, sy, 0.0, al * 0.24 * (1.0 - q), behind=behind)

    comp_pil(c, im, c.W / 2.0 + dx, cy, sx, sy, 0.0, al, behind=behind)

    if sub and lt > 0.28:
        yc_sub = face_safe_y(c, float(seg.get("sub_y", 0.74)), 80 * u) if behind else (cy + sz * 0.72)
        sp = ease_out((lt - 0.28) / 0.26)
        draw_pill_tag(c, sub, c.W / 2.0 + (1.0 - sp) * 60 * u, yc_sub, u, bg=CREAM, fg=INK, alpha=al * sp)


def fx_traced_outline(c, seg, lt, dur):
    """8. traced-outline: Monumental hollow stroked display typography traces in behind head then flood-fills solid."""
    u = c.W / 1080.0
    col = rgb(seg.get("color"), GOLD)
    al = env_alpha(lt, dur, 0.08, 0.26)
    if al <= 0:
        return
    behind = bool(seg.get("behind", True))
    word = str(seg.get("text", "RUPIAH")).upper()
    sub = seg.get("sub", "")
    eyebrow = seg.get("eyebrow", "")

    sw = max(3, int(4.5 * u))
    if behind:
        out_im, sz = cached(seg, "out", lambda: fit_tracked(word, 950 * u, 250 * u, kind="pop", fill=(0, 0, 0), stroke=sw, stroke_fill=CREAM, shadow=14 * u, alpha_fill=0))
        sol_im, _ = cached(seg, "sol", lambda: fit_tracked(word, 950 * u, 250 * u, kind="pop", fill=col, stroke=sw, stroke_fill=col, shadow=22 * u, alpha_fill=255))
        cy = max(head_top_y(seg, c) - sz * 0.22, c.H * 0.05 + out_im.height * 0.35)
    else:
        out_im, sz = cached(seg, "out", lambda: fit_tracked(word, 880 * u, 130 * u, kind="pop", fill=(0, 0, 0), stroke=sw, stroke_fill=CREAM, shadow=12 * u, alpha_fill=0))
        sol_im, _ = cached(seg, "sol", lambda: fit_tracked(word, 880 * u, 130 * u, kind="pop", fill=col, stroke=sw, stroke_fill=col, shadow=18 * u, alpha_fill=255))
        cy = face_safe_y(c, float(seg.get("y", 0.72)), 110 * u)

    trace_p = ease_out(lt / 0.55)
    fill_p = ease_inout((lt - 0.50) / 0.55)
    x0 = c.W / 2.0 - out_im.width / 2.0
    y0 = cy - out_im.height / 2.0

    # Progressive left-to-right hollow outline trace
    vis_w = max(4, int(out_im.width * trace_p))
    fx.comp(c, out_im.crop((0, 0, vis_w, out_im.height)), x0, y0, alpha=al, behind=behind)

    # Smooth bottom-to-top liquid gold ink fill
    if fill_p > 0.01:
        vis_h = max(4, int(sol_im.height * fill_p))
        y_cut = sol_im.height - vis_h
        fx.comp(c, sol_im.crop((0, y_cut, sol_im.width, sol_im.height)), x0, y0 + y_cut, alpha=al, behind=behind)

    if eyebrow or sub:
        yc_sub = face_safe_y(c, float(seg.get("sub_y", 0.74)), 100 * u) if behind else (cy + sz * 0.75)
        if eyebrow and lt > 0.35:
            draw_eyebrow(c, eyebrow, c.W / 2.0, yc_sub - 44 * u, u, accent=col, alpha=al * ease_out((lt - 0.35) / 0.25))
        if sub and lt > 0.55:
            draw_sub_serif(c, sub, c.W / 2.0, yc_sub + 14 * u, u, fill=CREAM, alpha=al * ease_out((lt - 0.55) / 0.28))


def fx_plucked_string(c, seg, lt, dur):
    """9. plucked-string: Minimalist horizontal tension wire plucks & oscillates underneath an editorial headline."""
    u = c.W / 1080.0
    col = rgb(seg.get("color"), CYAN)
    al = env_alpha(lt, dur, 0.10, 0.22)
    if al <= 0:
        return
    word = str(seg.get("text", "JAGA DOLAR")).upper()
    sub = seg.get("sub", "")
    yc = face_safe_y(c, float(seg.get("y", 0.72)), 115 * u)

    im, sz = cached(seg, "w", lambda: fit_tracked(word, 840 * u, 92 * u, kind="montb", fill=WHITE, spacing_ratio=0.04, shadow=14 * u))
    pluck_t = float(seg.get("pluck_at", 0.20))
    if lt >= pluck_t:
        dt = lt - pluck_t
        amp = 42 * u * math.exp(-5.8 * dt) * math.sin(26.0 * dt + 0.3)
    else:
        amp = 0.0

    # Tension wire across chest safe zone
    sw = int(min(900 * u, im.width + 140 * u))
    sh = int(130 * u)
    wire = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
    wd = ImageDraw.Draw(wire)
    ym = sh / 2.0
    pts = [(f * sw, ym + amp * 1.15 * math.sin(math.pi * f)) for f in np.linspace(0, 1, 45)]
    wd.line(pts, fill=col + (235,), width=max(3, int(4 * u)), joint="curve")
    for ex in (8 * u, sw - 8 * u):
        wd.ellipse([ex - 6 * u, ym - 6 * u, ex + 6 * u, ym + 6 * u], fill=col + (255,))
    fx.comp(c, wire, c.W / 2.0 - sw / 2.0, yc + sz * 0.52 - ym, alpha=al)

    comp_pil(c, im, c.W / 2.0, yc + amp * 0.85, 1.0, 1.0, -amp * 0.08, al * ease_out(lt / 0.18))
    if sub and lt > 0.28:
        draw_eyebrow(c, sub, c.W / 2.0, yc + sz * 0.52 + 46 * u, u, accent=CREAM, alpha=al * ease_out((lt - 0.28) / 0.25))


def fx_tumbling_letter(c, seg, lt, dur):
    """10. tumbling-letter: Staggered editorial display letters tumble in with crisp spring rotation + serif subline."""
    u = c.W / 1080.0
    col = rgb(seg.get("color"), GOLD)
    al = env_alpha(lt, dur, 0.06, 0.22)
    if al <= 0:
        return
    word = str(seg.get("text", "BREAKDOWN")).upper()
    sub = seg.get("sub", "")
    yc = face_safe_y(c, float(seg.get("y", 0.71)), 125 * u)

    sz = 104 * u
    while sz > 44 * u and fx.font("pop", sz).getlength(word) > 840 * u:
        sz *= 0.92
    f = fx.font("pop", sz)
    tot_w = sum(f.getlength(ch) for ch in word)
    x = c.W / 2.0 - tot_w / 2.0

    for ci, ch in enumerate(word):
        cw = f.getlength(ch)
        dt = lt - (0.04 + ci * 0.036)
        if dt >= 0:
            p = ease_back(dt / 0.34, s=1.8)
            dy = -(1.0 - p) * 115 * u
            rot = (-38.0 if ci % 2 == 0 else 38.0) * (1.0 - clamp(p, 0.0, 1.12))
            sc = 0.55 + 0.45 * clamp(p, 0.0, 1.12)
            ch_im = cached(seg, ("ch", ci), lambda ch=ch: tracked_rgba(ch, sz, kind="pop", fill=col if ci < len(word) else WHITE, stroke=int(2.5 * u), stroke_fill=INK, shadow=14 * u))
            comp_pil(c, ch_im, x + cw / 2.0, yc + dy, sc, sc, rot, al * clamp(dt / 0.07))
        x += cw

    if sub and lt > 0.42:
        sp = ease_out((lt - 0.42) / 0.26)
        draw_sub_serif(c, sub, c.W / 2.0, yc + sz * 0.80 + (1.0 - sp) * 20 * u, u, fill=CREAM, alpha=al * sp)


EFFECTS = {
    "one-big-slam": fx_one_big_slam,
    "splits": fx_splits,
    "heavy-landing": fx_heavy_landing,
    "rollout": fx_rollout,
    "dot-hop": fx_dot_hop,
    "sticker-stack": fx_sticker_stack,
    "slingshot": fx_slingshot,
    "traced-outline": fx_traced_outline,
    "plucked-string": fx_plucked_string,
    "tumbling-letter": fx_tumbling_letter,
}


def load_tracking(src, cache_path, fps, fr, W, H):
    aw = 540 if W <= H else int(round(540 * W / H / 2)) * 2
    ah = int(round(aw * H / W / 2)) * 2
    cache_file = cache_path or (os.path.splitext(src)[0] + ".tracking.npz")
    if os.path.exists(cache_file):
        print(f"Loading tracking cache from {cache_file}...", flush=True)
        d = np.load(cache_file)
        return d["masks"], d["sm"], aw, ah
    print("Tracking speaker face & person mask (for depth & face-safe typography)...", flush=True)
    trk = fx.Tracker(aw, ah)
    masks, faces = [], []
    for i, fr_ in enumerate(fx.read_frames(src, aw, ah, fr)):
        m, f = trk(fr_, int(i / fps * 1000))
        masks.append(m)
        faces.append(f)
    try:
        trk.seg.close()
    except Exception:
        pass
    sm = fx.smooth(faces, fps)
    if sm is None:
        sm = np.tile([aw / 2, ah * 0.33, aw * 0.15], (len(faces), 1))
    masks_arr = np.stack(masks, axis=0)
    try:
        np.savez_compressed(cache_file, masks=masks_arr, sm=sm)
        print(f"Saved tracking cache to {cache_file}", flush=True)
    except Exception as ex:
        print(f"Notice: could not save cache: {ex}", flush=True)
    return masks_arr, sm, aw, ah


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--plan", required=True)
    ap.add_argument("--cache", help="Optional .npz tracking cache")
    ap.add_argument("--still", help="Comma-separated seconds to save preview PNGs")
    a = ap.parse_args()

    fr, fps, dur, sw, sh = fx.probe(a.src)
    W, H = (1080, int(round(1080 * sh / sw / 2)) * 2) if sw <= sh else (int(round(1080 * sw / sh / 2)) * 2, 1080)
    plan = json.load(open(a.plan, encoding="utf-8"))
    raw_list = plan.get("effects", []) if isinstance(plan, dict) else plan

    masks_arr, sm, aw, ah = load_tracking(a.src, a.cache, fps, fr, W, H)
    sc = W / aw
    n_m = len(masks_arr)

    segments = []
    for raw in raw_list:
        name = raw["fx"].lower().strip()
        if name not in EFFECTS:
            sys.exit(f"Unknown typography effect '{name}'. Available: {', '.join(EFFECTS)}")
        seg = dict(raw)
        seg["fx"] = name
        seg["start"] = max(0.0, float(seg.get("start", 0.0)))
        seg["end"] = min(dur, float(seg.get("end", dur)))
        # Compute median top-of-head for behind-head placement
        i0, i1 = max(0, int(seg["start"] * fps)), min(n_m, int(seg["end"] * fps) + 1)
        tops = []
        for ii in range(i0, i1, 3):
            m = masks_arr[ii]
            fx_, fy_, fw_ = sm[min(ii, len(sm) - 1)]
            band = m[:, max(0, int(fx_ - fw_ * 0.35)):int(fx_ + fw_ * 0.35) + 1]
            r = np.nonzero((band > 128).mean(1) > 0.25)[0]
            if len(r) and r[0] < fy_:
                tops.append(r[0])
        seg["_top"] = float(np.median(tops)) * sc if tops else None
        segments.append(seg)

    stills = sorted({int(round(float(s) * fps)) for s in a.still.split(",")}) if a.still else None
    enc = None
    if stills is None:
        os.makedirs(os.path.dirname(os.path.abspath(a.dst)), exist_ok=True)
        # Pure original podcast audio (NO synthetic sound effects)
        cmd = [
            "ffmpeg", "-v", "error", "-y",
            "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(fr), "-i", "-",
            "-i", a.src,
            "-map", "0:v", "-map", "1:a:0?",
            "-c:v", "libx264", "-crf", "17", "-preset", "medium", "-pix_fmt", "yuv420p",
            "-c:a", "copy", "-shortest", "-movflags", "+faststart", a.dst
        ]
        enc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    print(f"[style-11] Rendering {'stills' if stills else 'video (clean audio, zero SFX)'} ({len(segments)} editorial beats)...", flush=True)
    for i, frame in enumerate(fx.read_frames(a.src, W, H, fr)):
        t = i / fps
        if stills is not None and i not in stills:
            if i > stills[-1]:
                break
            continue
        act = [seg for seg in segments if seg["start"] <= t < seg["end"]]
        if act:
            c = fx.Ctx()
            c.W, c.H, c.t, c.fps = W, H, t, fps
            c.img = frame.astype(np.float32) / 255.0
            m = masks_arr[i] if i < n_m else None
            c.m = cv2.resize(m, (W, H), interpolation=cv2.INTER_LINEAR).astype(np.float32) / 255.0 if m is not None else np.zeros((H, W), np.float32)
            fx_, fy_, fw_ = sm[min(i, len(sm) - 1)]
            c.fx, c.fy, c.fw = fx_ * sc, fy_ * sc, max(fw_ * sc, W * 0.05)
            # Apply spotlight first (if active), then editorial typography
            for seg in act:
                apply_editorial_spotlight(c, seg, t - seg["start"], max(0.05, seg["end"] - seg["start"]))
            # Soft readability gradient ONLY on bottom third (never dims face)
            yy = np.linspace(0.0, 1.0, H, dtype=np.float32)[:, None, None]
            c.img *= (1.0 - np.clip((yy - 0.58) / 0.34, 0.0, 1.0) * 0.30)
            for seg in act:
                EFFECTS[seg["fx"]](c, seg, t - seg["start"], max(0.05, seg["end"] - seg["start"]))
            frame = (np.clip(c.img, 0, 1) * 255 + 0.5).astype(np.uint8)
        if stills is not None:
            out = a.dst.replace(".png", f"_{t:.2f}.png") if len(stills) > 1 else a.dst
            cv2.imwrite(out, cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
            print("saved", out, flush=True)
        else:
            enc.stdin.write(frame.tobytes())
            if i % int(fps * 15) == 0:
                print(f"  [style-11] {t:5.1f}s / {dur:.1f}s", flush=True)

    if enc:
        enc.stdin.close()
        rc = enc.wait()
        if rc != 0:
            sys.exit(f"ffmpeg exited with code {rc}")
        print(f"[style-11] Done: {a.dst}", flush=True)


if __name__ == "__main__":
    main()

