#!/usr/bin/env python3
"""Style 12 â€” Full Apple Liquid Glass Engine (Reels / TikTok / YouTube Shorts Safe-Zone Edition).

Every visual element is rendered as real-time optical Liquid Glass:
  - Rounded-rect SDF edge refraction bending the live video behind each panel
  - Subtle RGB chromatic dispersion fringe & top-left specular caustic rim
  - Strict Universal 9:16 Social Safe Zone (Instagram Reels + TikTok + YouTube Shorts):
      * Top safe margin    >= 13.5% (clears status bar, camera & Following/For You tabs)
      * Bottom safe margin <= 77.5% (clears username, captions & bottom navigation bar)
      * Right UI rail safe <= 83.5% in lower half (clears Like/Comment/Share/Save buttons)
      * Hard face/eye protection via AI face tracking & person segmentation mask
  - Bespoke crystalline Liquid Glass audio effects (synthesized 48kHz stereo, zero sample licenses)

Usage:
  python liquid_glass_fx.py --plan effects.json input.mp4 output.mp4 [--words file.words.json] [--cache track.npz] [--still 1.5,5.0]
"""
import argparse, json, math, os, re, subprocess, sys, wave
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FX_SCRIPTS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, FX_SCRIPTS)
import fx

# Universal 9:16 Social Safe Zone (Instagram Reels + TikTok + YouTube Shorts)
SAFE_TOP = 0.135
SAFE_BOT = 0.772
SAFE_LEFT = 0.055
SAFE_RIGHT_LOWER = 0.835  # clears right-side Like/Comment/Share/Save rail!
SAFE_CX_LOWER = (SAFE_LEFT + SAFE_RIGHT_LOWER) * 0.5  # 0.445 -> subtly left of right-rail icons
SAFE_W_LOWER = (SAFE_RIGHT_LOWER - SAFE_LEFT)         # 0.780 -> max 842px on 1080w

# Liquid Glass Palette
WHITE = (255, 255, 255)
ICE = (232, 244, 255)
INK = (16, 18, 24)
MINT = (56, 224, 136)
CYAN = (90, 200, 255)
GOLD = (255, 214, 102)
CRIMSON = (255, 76, 88)


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease_out(x):
    x = clamp(x)
    return 1.0 - (1.0 - x) ** 3


def ease_inout(x):
    x = clamp(x)
    return 3.0 * x * x - 2.0 * x * x * x


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


def cached(seg, key, fn):
    st = seg.setdefault("_cache", {})
    if key not in st:
        st[key] = fn()
    return st[key]


def head_top_y(seg, c):
    return seg["_top"] if seg.get("_top") is not None else (c.fy - c.fw * 0.92)


def safe_lower_cy(c, card_h, pref_y=0.68):
    """Place a lower-third card strictly below chin AND strictly above Reels/TikTok/Shorts bottom UI."""
    chin = c.fy + c.fw * 1.02
    lo = max(c.H * 0.50, chin + card_h * 0.5 + c.H * 0.025)
    hi = c.H * SAFE_BOT - card_h * 0.5
    if lo > hi:
        return hi
    return clamp(c.H * pref_y, lo, hi)


def safe_lower_cx(c, card_w):
    """Keep card centered nicely while NEVER entering the right-side Reels/TikTok/Shorts icon rail."""
    # Prefer visual center (0.50) if card fits inside SAFE_RIGHT_LOWER, otherwise nudge subtly left
    right_lim = c.W * SAFE_RIGHT_LOWER
    left_lim = c.W * SAFE_LEFT
    cx = c.W * 0.50
    if cx + card_w * 0.5 > right_lim:
        cx = right_lim - card_w * 0.5
    if cx - card_w * 0.5 < left_lim:
        cx = (left_lim + right_lim) * 0.5
    return cx


def glass_slab(c, w, h, r, cx, cy, tint=(240, 248, 255), tint_amt=0.14, dark=0.28, blur=None, alpha=245):
    """True optical Liquid Glass slab with SDF edge refraction, RGB dispersion, frosted depth & top-left specular rim."""
    im = fx.glass(c, max(16, int(w)), max(16, int(h)), max(6, int(r)), cx, cy,
                  amt=tint_amt, tint=tint, blur=blur or max(10, c.W // 34), alpha=alpha, dark=dark, liquid=True)
    # Crisp inner specular highlight rim (Apple iOS 26 liquid-glass bevel)
    d = ImageDraw.Draw(im)
    W_, H_ = im.size
    d.rounded_rectangle([1, 1, W_ - 2, H_ - 2], max(4, int(r)), outline=(255, 255, 255, 135), width=max(2, c.W // 540))
    return im


def glass_display_word(text, max_w, start_sz, kind="pop", tint=ICE, glow_col=CYAN):
    """Luminous frosted-glass display typography with translucent sheen & soft chromatic glow."""
    sz = start_sz
    while sz > 28 and fx.font(kind, sz).getlength(text) > max_w:
        sz = int(sz * 0.93)
    f = fx.font(kind, sz)
    bb = f.getbbox(text)
    pad = int(sz * 0.28) + 12
    w, h = (bb[2] - bb[0]) + 2 * pad, (bb[3] - bb[1]) + 2 * pad
    ox, oy = pad - bb[0], pad - bb[1]
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).text((ox, oy), text, font=f, fill=255)
    # Vertical glass-sheen gradient inside letters (bright pearl top -> cool frosted tint bottom)
    g = np.linspace(0.0, 1.0, h, dtype=np.float32)[:, None, None]
    top_c = np.float32((255, 255, 255))
    bot_c = np.float32(tint)
    col = top_c * (1.0 - g * 0.72) + bot_c * (g * 0.72)
    alpha_m = (np.asarray(m, dtype=np.float32) * 0.92).astype(np.uint8)
    body = Image.fromarray(np.dstack([np.broadcast_to(col, (h, w, 3)).astype(np.uint8), alpha_m]), "RGBA")
    # Specular crisp white rim stroke
    rim = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(rim).text((ox, oy), text, font=f, fill=(255, 255, 255, 0), stroke_width=max(2, int(sz * 0.014)), stroke_fill=(255, 255, 255, 210))
    # Soft luminous halo
    gl = Image.new("RGBA", (w, h), tuple(glow_col) + (0,))
    gl.putalpha(m.filter(ImageFilter.GaussianBlur(max(4, int(sz * 0.07)))).point(lambda v: int(v * 0.55)))
    out = Image.alpha_composite(gl, body)
    out = Image.alpha_composite(out, rim)
    return fx.shadowed(out, blur=max(8, int(sz * 0.06)), dy=int(sz * 0.03), alpha=110), sz


def apply_glass_spotlight(c, seg, lt, dur):
    """Cinematic cool-pearl/tinted studio spotlight keeping speaker sharp while room dims smoothly."""
    if not seg.get("spotlight"):
        return
    k = clamp(lt / 0.28) * clamp((dur - lt) / 0.26)
    if k <= 0.01:
        return
    push = float(seg.get("push", 1.07))
    if push > 1.005:
        fx.face_cam(c, 1.0 + (push - 1.0) * ease_inout(lt / dur), 0.42)
    tint = np.float32(rgb(seg.get("spot_color") or seg.get("color"), CYAN)) / 255.0
    strength = float(seg.get("spot_strength", 0.62))
    xx, yy = fx.grid(c)
    d = ((xx - c.fx) / (c.W * 0.56)) ** 2 + ((yy - (c.fy + c.H * 0.14)) / (c.H * 0.50)) ** 2
    pool = np.clip(1.0 - d, 0.0, 1.0) ** 1.5
    bg_b = 1.0 - k * strength * (1.0 - 0.40 * pool)
    m = c.m[..., None]
    c.img = c.img * (bg_b[..., None] * (1.0 - m) + (1.0 + 0.05 * k) * m)
    halo = np.clip(cv2.GaussianBlur(c.m, (0, 0), c.W * 0.018) * 1.45 - c.m, 0.0, 1.0)
    c.img = np.clip(c.img + (halo * 0.34 * k)[..., None] * tint * (1.0 - m), 0.0, 1.0)


# ==============================================================================
# LIQUID GLASS EFFECTS SUITE
# ==============================================================================

def fx_glass_hook(c, seg, lt, dur):
    """Spatial Liquid Glass Hook: luminous glass display word behind head + refractive hero capsule in safe zone."""
    u = c.W / 1080.0
    col = rgb(seg.get("color"), CYAN)
    al = env_alpha(lt, dur, 0.10, 0.24)
    if al <= 0:
        return
    word = str(seg.get("text", "BI RATE")).upper()
    eyebrow = str(seg.get("eyebrow", "RDG BANK INDONESIA Â· NOV 2026")).upper()
    sub = str(seg.get("sub", "Naik 6,00% â€” ada apa sih?"))

    im, sz = cached(seg, "hw", lambda: glass_display_word(word, 920 * u, 240 * u, kind="pop", tint=ICE, glow_col=col))
    p = ease_back(lt / 0.30, s=1.4)
    cy_w = max(head_top_y(seg, c) - sz * 0.24, c.H * 0.11 + sz * 0.30)
    fx.place(c, im, c.W * 0.5, cy_w, 1.18 - 0.18 * p, 0, al, behind=True)

    # Refractive Liquid Glass Hero Capsule in lower safe zone (clears right UI rail + bottom caption area)
    if lt > 0.14:
        q = ease_back((lt - 0.14) / 0.30, s=1.35)
        cw = int(min(c.W * SAFE_W_LOWER, 810 * u))
        ch = int(172 * u)
        cx = safe_lower_cx(c, cw)
        cy = safe_lower_cy(c, ch, pref_y=0.69) + (1.0 - q) * 34 * u
        slab = glass_slab(c, cw, ch, 38 * u, cx, cy, tint=col, tint_amt=0.14, dark=0.38)
        d = ImageDraw.Draw(slab)
        # Luminous status dot + mono eyebrow
        dr = 7 * u
        d.ellipse([36 * u - dr, 48 * u - dr, 36 * u + dr, 48 * u + dr], fill=col + (255,))
        d.text((56 * u, 48 * u), eyebrow, font=fx.font("mono", 22 * u), fill=ICE + (225,), anchor="lm")
        # Editorial serif sub-hook inside glass slab
        fsz = 48 * u
        while fsz > 26 * u and fx.font("didoneib", fsz).getlength(sub) > cw - 72 * u:
            fsz *= 0.93
        d.text((36 * u, 114 * u), sub, font=fx.font("didoneib", fsz), fill=WHITE + (255,), anchor="lm")
        fx.place(c, fx.shadowed(slab, int(18 * u), int(10 * u), 110), cx, cy, 0.90 + 0.10 * q, 0, al * clamp((lt - 0.14) / 0.10))


def fx_glass_broll(c, seg, lt, dur):
    """Spatial Liquid Glass B-Roll Window: speaker slides gently down, beveled glass B-roll frame floats in top safe zone."""
    u = c.W / 1080.0
    col = rgb(seg.get("color"), CYAN)
    k = min(ease_inout(lt / 0.34), ease_inout((dur - lt) / 0.30))
    al = clamp(lt / 0.12) * clamp((dur - lt) / 0.22)
    if al <= 0:
        return

    # Safe top B-roll window: strictly below SAFE_TOP (13.5% = 260px) and centered within 840px width
    bw, bh = int(840 * u), int(520 * u)
    top_y = int(c.H * SAFE_TOP + 18 * u)
    want_dy = clamp((top_y + bh + 36 * u) - head_top_y(seg, c), c.H * 0.18, c.H * 0.34)
    dy = want_dy * k
    if dy > 1.0:
        small = cv2.resize(c.img, (c.W // 8, c.H // 8), interpolation=cv2.INTER_AREA)
        bg = cv2.resize(cv2.GaussianBlur(small, (0, 0), 7), (c.W, c.H), interpolation=cv2.INTER_LINEAR) * 0.52
        M = np.float32([[1, 0, 0], [0, 1, dy]])
        c.img = cv2.warpAffine(c.img, M, (c.W, c.H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
        c.m = cv2.warpAffine(c.m, M, (c.W, c.H), flags=cv2.INTER_LINEAR)
        n = int(math.ceil(dy))
        c.img[:n] = bg[:n]
        c.fy += dy

    cx, cy = c.W * 0.5, top_y + bh * 0.5 + (1.0 - ease_back(lt / 0.36, s=1.3)) * 38 * u
    # Outer refractive Liquid Glass bezel frame
    pad = int(18 * u)
    bezel = glass_slab(c, bw + 2 * pad, bh + 2 * pad, 42 * u, cx, cy, tint=ICE, tint_amt=0.16, dark=0.26)

    # Inner B-roll media with slow Ken Burns push-in
    img_path = seg.get("image")
    src_im = cached(seg, "src", lambda: Image.open(img_path).convert("RGB") if (img_path and os.path.exists(img_path)) else None)
    if src_im is not None:
        z = 1.0 + 0.08 * clamp(lt / dur)
        s = max(bw * z / src_im.width, bh * z / src_im.height)
        rw, rh = max(bw, int(src_im.width * s)), max(bh, int(src_im.height * s))
        res = src_im.resize((rw, rh), Image.LANCZOS)
        l, tp = (rw - bw) // 2, (rh - bh) // 2
        inner = res.crop((l, tp, l + bw, tp + bh)).convert("RGBA")
    else:
        inner = Image.new("RGBA", (bw, bh), (20, 26, 36, 255))
        t_im = fx.fit_text(str(seg.get("text", "B-ROLL")), bw * 0.82, "popb", int(64 * u), fill=WHITE)
        inner.alpha_composite(t_im, ((bw - t_im.width) // 2, (bh - t_im.height) // 2))

    # Subtle dark glass sheen gradient over bottom of B-roll for badge contrast
    mk = Image.new("L", (bw, bh), 0)
    ImageDraw.Draw(mk).rounded_rectangle([0, 0, bw - 1, bh - 1], int(28 * u), fill=255)
    inner.putalpha(mk)
    ImageDraw.Draw(inner).rounded_rectangle([1, 1, bw - 2, bh - 2], int(28 * u), outline=(255, 255, 255, 110), width=2)
    bezel.alpha_composite(inner, (pad, pad))
    fx.place(c, fx.shadowed(bezel, int(28 * u), int(14 * u), 130), cx, cy, 0.90 + 0.10 * ease_out(lt / 0.30), 0, al)

    # Floating Liquid Glass metric tag pill anchored at bottom-left of B-roll frame
    tag = seg.get("tag", "")
    if tag and lt > 0.22:
        tp = ease_back((lt - 0.22) / 0.28, s=1.4)
        f = fx.font("uib", 30 * u)
        tw = f.getlength(tag)
        pw, ph = int(tw + 52 * u), int(64 * u)
        px = cx - bw * 0.5 + pw * 0.5 + 18 * u
        py = cy + bh * 0.5 - ph * 0.5 - 12 * u
        pill = glass_slab(c, pw, ph, ph / 2.0, px, py, tint=col, tint_amt=0.26, dark=0.45)
        pd = ImageDraw.Draw(pill)
        pd.ellipse([20 * u - 6 * u, ph / 2 - 6 * u, 20 * u + 6 * u, ph / 2 + 6 * u], fill=col + (255,))
        pd.text((38 * u, ph / 2), tag, font=f, fill=WHITE + (255,), anchor="lm")
        fx.place(c, fx.shadowed(pill, int(10 * u), int(5 * u), 95), px, py, 0.72 + 0.28 * tp, 0, al * clamp((lt - 0.22) / 0.08))


def fx_glass_bento(c, seg, lt, dur):
    """Safe-Zone Liquid Glass Bento Dashboard: smoked glass chart behind head + 2 lower tiles avoiding right UI rail."""
    u = c.W / 1080.0
    col = rgb(seg.get("color"), MINT)
    al = env_alpha(lt, dur, 0.12, 0.22)
    if al <= 0:
        return
    q = ease_out(lt / 0.38)
    # 1. Smoked Liquid Glass graph panel behind head (starts cleanly below SAFE_TOP 13.5%)
    pw, ph = int(880 * u), int(440 * u)
    pcx, pcy = c.W * 0.5, c.H * SAFE_TOP + ph * 0.5 + 10 * u + (1.0 - q) * 28 * u
    pan = glass_slab(c, pw, ph, 38 * u, pcx, pcy, tint=ICE, tint_amt=0.08, dark=0.55)
    d = ImageDraw.Draw(pan)
    pad = 42 * u
    g = ease_inout((lt - 0.18) / max(0.3, dur * 0.68))
    d.text((pad, pad * 0.78), str(seg.get("text", "BI RATE 2026")).upper(), font=fx.font("mono", 24 * u), fill=ICE + (210,))
    a0, _, _ = fx.num_parts(seg.get("from", "5.75%"))
    b0, suf, dp = fx.num_parts(seg.get("to", "6.00%"))
    val_s = f"{a0 + (b0 - a0) * g:.{dp}f}{suf}"
    fv = fx.font("uib", 68 * u)
    d.text((pw - pad - fv.getlength(val_s), pad * 0.45), val_s, font=fv, fill=WHITE + (255,))
    x0, x1, y0, y1 = pad, pw - pad, ph - pad * 0.85, ph * 0.34
    for j in range(1, 4):
        yy = y0 - (y0 - y1) * j / 3.2
        d.line([(x0, yy), (x1, yy)], fill=(255, 255, 255, 36), width=2)
    n = 70
    pts = [(x0 + (x1 - x0) * j / n, y0 - (y0 - y1) * ((j / n) ** 1.65) + math.sin(j / n * 14) * ph * 0.018 * (1 - j / n)) for j in range(int(n * g) + 1)]
    if len(pts) > 1:
        area = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
        ImageDraw.Draw(area).polygon(pts + [(pts[-1][0], y0), (x0, y0)], fill=col + (65,))
        pan.alpha_composite(area)
        gl = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
        ImageDraw.Draw(gl).line(pts, fill=col + (255,), width=int(18 * u), joint="curve")
        pan.alpha_composite(gl.filter(ImageFilter.GaussianBlur(10 * u)))
        ImageDraw.Draw(pan).line(pts, fill=col + (255,), width=int(7 * u), joint="curve")
        hx, hy = pts[-1]
        ImageDraw.Draw(pan).ellipse([hx - 12 * u, hy - 12 * u, hx + 12 * u, hy + 12 * u], fill=WHITE + (255,), outline=col + (255,), width=3)
    fx.place(c, pan, pcx, pcy, alpha=al * q, behind=True)

    # 2. Lower Safe-Zone Glass Bento Row (strictly inside x: [60..890], y <= 1480 -> ZERO Reels/TikTok UI overlap!)
    row_w = int(810 * u)
    gap = int(24 * u)
    tw_l = int(340 * u)
    tw_r = row_w - tw_l - gap
    th = int(280 * u)
    row_cx = safe_lower_cx(c, row_w)
    row_cy = safe_lower_cy(c, th, pref_y=0.69)

    # Left KPI + Progress Ring Tile
    if lt > 0.16:
        k1 = ease_back((lt - 0.16) / 0.34)
        lx = row_cx - row_w * 0.5 + tw_l * 0.5
        t1 = glass_slab(c, tw_l, th, 34 * u, lx, row_cy, tint=col, tint_amt=0.10, dark=0.45)
        d1 = ImageDraw.Draw(t1)
        d1.text((28 * u, 28 * u), str(seg.get("kpi_label", "KENAIKAN")).upper(), font=fx.font("mono", 20 * u), fill=ICE + (190,))
        d1.text((28 * u, 68 * u), str(seg.get("kpi", "+25 bps")), font=fx.font("uib", 62 * u), fill=WHITE + (255,))
        # Glowing pill badge at bottom of KPI tile
        pill_txt = str(seg.get("kpi_sub", "BI Rate Â· 6,00%"))
        d1.rounded_rectangle([26 * u, th - 78 * u, tw_l - 26 * u, th - 26 * u], 18 * u, fill=col + (55,), outline=col + (180,), width=2)
        d1.text((tw_l * 0.5, th - 52 * u), pill_txt, font=fx.font("uim", 24 * u), fill=WHITE + (240,), anchor="mm")
        fx.place(c, fx.shadowed(t1, int(14 * u), int(8 * u), 100), lx, row_cy, 0.78 + 0.22 * k1, 0, al * clamp((lt - 0.16) / 0.10))

    # Right Mini Bar Chart Tile
    if lt > 0.26:
        k2 = ease_back((lt - 0.26) / 0.34)
        rx = row_cx + row_w * 0.5 - tw_r * 0.5
        t2 = glass_slab(c, tw_r, th, 34 * u, rx, row_cy, tint=ICE, tint_amt=0.08, dark=0.45)
        d2 = ImageDraw.Draw(t2)
        bv, bl = (str(seg.get("bars", "5.25|5.50|5.75|6.00::JEJAK BI RATE 2026")).split("::") + [""])[:2]
        vals = [fx.num_parts(v)[0] for v in bv.split("|")]
        d2.text((28 * u, 26 * u), bl.upper(), font=fx.font("mono", 20 * u), fill=ICE + (195,))
        nb = len(vals)
        bw_ = (tw_r - 56 * u) / max(1, nb)
        top_b, bot_b = 94 * u, th - 28 * u
        mx = max(vals) if vals else 1.0
        for j, v in enumerate(vals):
            kk = ease_out((lt - 0.34 - 0.08 * j) / 0.42)
            # Emphasize differences neatly
            norm = 0.38 + 0.62 * ((v - min(vals) * 0.92) / max(1e-3, mx - min(vals) * 0.92))
            bh_ = (bot_b - top_b) * norm * kk
            bx = 28 * u + j * bw_
            is_last = (j == nb - 1)
            fill_b = col + (235,) if is_last else (255, 255, 255, 130)
            d2.rounded_rectangle([bx + bw_ * 0.14, bot_b - bh_, bx + bw_ * 0.86, bot_b], int(10 * u), fill=fill_b)
            if kk > 0.55:
                d2.text((bx + bw_ * 0.5, bot_b - bh_ - 8 * u), f"{v:.2f}", font=fx.font("uib", 20 * u), fill=WHITE + (235,), anchor="md")
        fx.place(c, fx.shadowed(t2, int(14 * u), int(8 * u), 100), rx, row_cy, 0.78 + 0.22 * k2, 0, al * clamp((lt - 0.26) / 0.10))


def fx_glass_track(c, seg, lt, dur):
    """Liquid Glass Camera Tracking: smooth AI face-tracking zoom + glass reticle brackets + floating glass HUD pill."""
    u = c.W / 1080.0
    col = rgb(seg.get("color"), CYAN)
    al = env_alpha(lt, dur, 0.12, 0.22)
    z = float(seg.get("zoom", 1.28))
    fx.face_cam(c, 1.0 + (z - 1.0) * ease_out(lt / 0.55), 0.41)
    if al <= 0:
        return
    # Refractive glass viewfinder corners around face
    snap = ease_out(lt / 0.24)
    s = c.fw * 0.88 * (1.0 + 0.45 * (1.0 - snap))
    sz_w, sz_h = int(2 * s + 44), int(2.45 * s + 44)
    im = Image.new("RGBA", (sz_w, sz_h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = 22, 22, sz_w - 22, sz_h - 22
    L = int(s * 0.30)
    wd = max(4, int(5 * u))
    for (px, py, dx, dy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
        d.line([(px, py + dy * L), (px, py), (px + dx * L, py)], fill=col + (180,), width=wd + 4, joint="curve")
        d.line([(px, py + dy * L), (px, py), (px + dx * L, py)], fill=WHITE + (245,), width=wd, joint="curve")
    fx.place(c, fx.shadowed(im, int(8 * u), int(3 * u), 95), c.fx, c.fy, alpha=al)

    # Floating Liquid Glass Tracking Pill cleanly in lower safe zone
    tag = str(seg.get("text", "TRACKING FOCUS")).upper()
    if lt > 0.16:
        q = ease_back((lt - 0.16) / 0.28)
        f = fx.font("mono", 25 * u)
        pw = int(min(c.W * SAFE_W_LOWER, f.getlength(tag) + 84 * u))
        ph = int(68 * u)
        px = safe_lower_cx(c, pw)
        py = safe_lower_cy(c, ph, pref_y=0.71)
        pill = glass_slab(c, pw, ph, ph / 2.0, px, py, tint=col, tint_amt=0.18, dark=0.40)
        pd = ImageDraw.Draw(pill)
        # Blinking live lens dot
        da = 255 if int(lt * 3.0) % 2 == 0 else 110
        pd.ellipse([24 * u, ph / 2 - 7 * u, 38 * u, ph / 2 + 7 * u], fill=col + (da,))
        pd.text((52 * u, ph / 2), tag, font=f, fill=WHITE + (245,), anchor="lm")
        fx.place(c, fx.shadowed(pill, int(12 * u), int(6 * u), 95), px, py, 0.80 + 0.20 * q, 0, al * clamp((lt - 0.16) / 0.10))


def fx_glass_type(c, seg, lt, dur):
    """Editorial Liquid Glass Callout Slab: mixed Sans + Playfair Italic inside a sleek specular glass lens."""
    u = c.W / 1080.0
    col = rgb(seg.get("color"), GOLD)
    al = env_alpha(lt, dur, 0.12, 0.22)
    if al <= 0:
        return
    parts = [p.strip() for p in str(seg.get("text", "SIMPEL|dua alasan utama")).split("|")]
    top_s = parts[0].upper()
    bot_s = parts[1] if len(parts) > 1 else ""
    q = ease_back(lt / 0.32, s=1.35)
    cw = int(min(c.W * SAFE_W_LOWER, 780 * u))
    ch = int(196 * u)
    cx = safe_lower_cx(c, cw)
    cy = safe_lower_cy(c, ch, pref_y=0.69) + (1.0 - q) * 32 * u
    slab = glass_slab(c, cw, ch, 40 * u, cx, cy, tint=col, tint_amt=0.12, dark=0.38)
    d = ImageDraw.Draw(slab)
    d.text((cw * 0.5, 56 * u), top_s, font=fx.font("mono", 25 * u), fill=col + (245,), anchor="mm")
    d.line([(56 * u, 88 * u), (cw - 56 * u, 88 * u)], fill=(255, 255, 255, 55), width=2)
    fsz = 56 * u
    while fsz > 28 * u and fx.font("didoneib", fsz).getlength(bot_s) > cw - 76 * u:
        fsz *= 0.93
    d.text((cw * 0.5, 138 * u), bot_s, font=fx.font("didoneib", fsz), fill=WHITE + (255,), anchor="mm")
    fx.place(c, fx.shadowed(slab, int(18 * u), int(10 * u), 115), cx, cy, 0.88 + 0.12 * q, 0, al)


def fx_glass_toggles(c, seg, lt, dur):
    """Full Liquid Glass iOS Switches (translucent refractive card, NOT opaque white) in lower safe zone."""
    u = c.W / 1080.0
    col = rgb(seg.get("color"), MINT)
    al = env_alpha(lt, dur, 0.10, 0.22)
    if al <= 0:
        return
    rows = [r.strip() for r in str(seg.get("text", "01 Â· Inflasi|02 Â· Mata Uang")).split("|") if r.strip()]
    ticks = [float(x) for x in str(seg["ticks"]).split("|")] if seg.get("ticks") else [0.45 + 0.45 * i for i in range(len(rows))]
    q = ease_back(lt / 0.34, s=1.35)
    cw = int(min(c.W * SAFE_W_LOWER, 760 * u))
    rh = int(116 * u)
    ch = rh * len(rows)
    cx = safe_lower_cx(c, cw)
    cy = safe_lower_cy(c, ch, pref_y=0.69) + (1.0 - q) * 32 * u

    slab = glass_slab(c, cw, ch, 38 * u, cx, cy, tint=ICE, tint_amt=0.14, dark=0.40)
    d = ImageDraw.Draw(slab)
    tw, th = int(126 * u), int(72 * u)
    tx = cw - int(44 * u) - tw
    off_c, on_c = np.float32((110, 118, 130)), np.float32(col)
    f = fx.font("uib", 44 * u)
    for i, label in enumerate(rows):
        yc_r = i * rh + rh * 0.5
        if i > 0:
            d.line([(36 * u, i * rh), (cw - 36 * u, i * rh)], fill=(255, 255, 255, 48), width=2)
        u_sw = ease_out((lt - ticks[i]) / 0.22) if i < len(ticks) else 0.0
        sw_col = tuple(int(v) for v in off_c * (1.0 - u_sw) + on_c * u_sw)
        d.text((42 * u, yc_r), label, font=f, fill=WHITE + (250 if u_sw > 0.2 else 185,), anchor="lm")
        x0, y0 = tx, yc_r - th * 0.5
        d.rounded_rectangle([x0, y0, x0 + tw, y0 + th], th // 2, fill=sw_col + (225,), outline=(255, 255, 255, 110), width=2)
        kr = th * 0.5 - 6 * u
        kx = x0 + th * 0.5 + (tw - th) * u_sw
        d.ellipse([kx - kr, yc_r - kr, kx + kr, yc_r + kr], fill=WHITE + (255,))
    fx.place(c, fx.shadowed(slab, int(18 * u), int(10 * u), 110), cx, cy, 0.88 + 0.12 * q, 0, al)


def fx_glass_spotlight_word(c, seg, lt, dur):
    """Spotlight + Luminous Glass Display Word behind head + translucent glass pill in lower safe zone."""
    u = c.W / 1080.0
    col = rgb(seg.get("color"), MINT)
    al = env_alpha(lt, dur, 0.10, 0.22)
    if al <= 0:
        return
    word = str(seg.get("text", "AMAN")).upper()
    sub = str(seg.get("sub", ""))
    im, sz = cached(seg, "w", lambda: glass_display_word(word, 920 * u, 235 * u, kind="pop", tint=col, glow_col=col))
    p = ease_back(lt / 0.28, s=1.4)
    cy_w = max(head_top_y(seg, c) - sz * 0.14, c.H * SAFE_TOP + sz * 0.36)
    fx.place(c, im, c.W * 0.5, cy_w, 1.15 - 0.15 * p, 0, al, behind=True)

    if sub and lt > 0.18:
        q = ease_back((lt - 0.18) / 0.28)
        f = fx.font("uib", 30 * u)
        pw = int(min(c.W * SAFE_W_LOWER, f.getlength(sub) + 84 * u))
        ph = int(74 * u)
        px = safe_lower_cx(c, pw)
        py = safe_lower_cy(c, ph, pref_y=0.71)
        pill = glass_slab(c, pw, ph, ph / 2.0, px, py, tint=col, tint_amt=0.18, dark=0.40)
        pd = ImageDraw.Draw(pill)
        pd.ellipse([24 * u, ph / 2 - 7 * u, 38 * u, ph / 2 + 7 * u], fill=col + (255,))
        pd.text((52 * u, ph / 2), sub, font=f, fill=WHITE + (250,), anchor="lm")
        fx.place(c, fx.shadowed(pill, int(12 * u), int(6 * u), 95), px, py, 0.82 + 0.18 * q, 0, al * clamp((lt - 0.18) / 0.08))


def fx_glass_ots(c, seg, lt, dur):
    """Over-the-Shoulder Dual Liquid Glass Graphs (reuses fx.py's optical liquid_glass engine, speaker stays in front)."""
    # Wrap segment into a lightweight Fx object so fx.fx_over_the_shoulder_zoom runs natively!
    e = cached(seg, "fxe", lambda: fx.Fx(seg, c.fps))
    c.lt = lt
    fx.fx_over_the_shoulder_zoom(c, e)


def fx_glass_stack(c, seg, lt, dur):
    """Spatial Liquid Glass Alert Cards stacking smoothly inside lower safe zone (clears right UI rail)."""
    u = c.W / 1080.0
    col = rgb(seg.get("color"), CYAN)
    al = env_alpha(lt, dur, 0.10, 0.22)
    if al <= 0:
        return
    items = [x.strip() for x in str(seg.get("text", "Currency Watch::Jaga Dolar tetap di RI|BI Policy::Daya tarik +25 bps")).split("|") if x.strip()]
    cw = int(min(c.W * SAFE_W_LOWER, 800 * u))
    ch = int(128 * u)
    gap = int(18 * u)
    tot_h = len(items) * ch + max(0, len(items) - 1) * gap
    cx = safe_lower_cx(c, cw)
    cy_mid = safe_lower_cy(c, tot_h, pref_y=0.69)
    y_start = cy_mid - tot_h * 0.5 + ch * 0.5

    for i, raw in enumerate(items):
        t0 = 0.10 + i * 0.42
        if lt < t0:
            continue
        title, body = (raw.split("::") + [""])[:2]
        q = ease_back((lt - t0) / 0.28, s=1.4)
        cy = y_start + i * (ch + gap) + (1.0 - q) * 28 * u
        slab = glass_slab(c, cw, ch, 32 * u, cx, cy, tint=col if i == 0 else MINT, tint_amt=0.14, dark=0.42)
        d = ImageDraw.Draw(slab)
        # Translucent circular glass icon badge
        ir = 30 * u
        ix, iy = 54 * u, ch * 0.5
        ic_c = col if i == 0 else MINT
        d.ellipse([ix - ir, iy - ir, ix + ir, iy + ir], fill=ic_c + (75,), outline=ic_c + (220,), width=2)
        d.ellipse([ix - 9 * u, iy - 9 * u, ix + 9 * u, iy + 9 * u], fill=WHITE + (245,))
        d.text((104 * u, 42 * u), title.upper(), font=fx.font("mono", 20 * u), fill=ic_c + (245,), anchor="lm")
        fsz = 32 * u
        while fsz > 20 * u and fx.font("uib", fsz).getlength(body) > cw - 134 * u:
            fsz *= 0.93
        d.text((104 * u, 84 * u), body, font=fx.font("uib", fsz), fill=WHITE + (250,), anchor="lm")
        fx.place(c, fx.shadowed(slab, int(14 * u), int(8 * u), 100), cx, cy, 0.86 + 0.14 * q, 0, al * clamp((lt - t0) / 0.08))


def fx_glass_checklist(c, seg, lt, dur):
    """Smoked Liquid Glass Audit Checklist strictly inside lower safe zone (clears right UI rail & bottom UI)."""
    u = c.W / 1080.0
    col = rgb(seg.get("color"), MINT)
    al = env_alpha(lt, dur, 0.12, 0.22)
    if al <= 0:
        return
    rows = [x.split("::") for x in str(seg.get("text", "Cek Inflasi::2026|Cek Mata Uang::IDR/USD|Faktor Lain::Makro")).split("|")]
    n = len(rows)
    cw = int(min(c.W * SAFE_W_LOWER, 810 * u))
    hh = int(94 * u)
    rh = int(90 * u)
    ch = hh + rh * n + int(22 * u)
    cx = safe_lower_cx(c, cw)
    q = ease_out(lt / 0.34)
    cy = safe_lower_cy(c, ch, pref_y=0.66) + (1.0 - q) * 34 * u

    ticks = [float(x) for x in str(seg["ticks"]).split("|")] if seg.get("ticks") else [0.3 + (dur - 0.6) * (i + 1) / n for i in range(n)]
    slab = glass_slab(c, cw, ch, 36 * u, cx, cy, tint=ICE, tint_amt=0.10, dark=0.56)
    d = ImageDraw.Draw(slab)
    d.ellipse([30 * u, hh * 0.5 - 9 * u, 48 * u, hh * 0.5 + 9 * u], fill=col + (255,))
    d.text((64 * u, hh * 0.5), str(seg.get("title", "AUDIT DATA 2026")).upper(), font=fx.font("uib", 34 * u), fill=WHITE + (255,), anchor="lm")
    nd = sum(lt >= t_ for t_ in ticks)
    d.text((cw - 32 * u, hh * 0.5), f"{nd} / {n}", font=fx.font("mono", 24 * u), fill=ICE + (200,), anchor="rm")
    d.line([(28 * u, hh), (cw - 28 * u, hh)], fill=(255, 255, 255, 42), width=2)

    for i, r_item in enumerate(rows):
        txt, meta = (r_item + [""])[:2]
        yr = hh + 10 * u + rh * i + rh * 0.5
        xr = 52 * u
        rr = 20 * u
        t_start = ticks[i - 1] if i > 0 else 0.25
        if lt >= ticks[i]:
            qq = ease_back((lt - ticks[i]) / 0.24)
            r2 = rr * (0.65 + 0.35 * qq)
            d.ellipse([xr - r2, yr - r2, xr + r2, yr + r2], fill=col + (255,))
            fx.tick(d, xr - r2 * 0.48, yr - r2 * 0.45, r2 * 0.96, w=max(3, int(4 * u)))
            fc, mc = WHITE + (255,), col + (255,)
        elif lt >= t_start:
            a0 = (lt * 520) % 360
            d.ellipse([xr - rr, yr - rr, xr + rr, yr + rr], outline=(255, 255, 255, 60), width=4)
            d.arc([xr - rr, yr - rr, xr + rr, yr + rr], a0, a0 + 105, fill=CYAN + (255,), width=4)
            fc, mc = WHITE + (245,), ICE + (190,)
        else:
            d.ellipse([xr - rr, yr - rr, xr + rr, yr + rr], outline=(255, 255, 255, 65), width=3)
            fc, mc = WHITE + (130,), ICE + (110,)
        d.text((xr + 42 * u, yr), txt, font=fx.font("uib", 34 * u), fill=fc, anchor="lm")
        d.text((cw - 32 * u, yr), meta, font=fx.font("mono", 24 * u), fill=mc, anchor="rm")
    fx.place(c, fx.shadowed(slab, int(20 * u), int(10 * u), 120), cx, cy, 1.0, 0, al)


def fx_glass_verdict(c, seg, lt, dur):
    """Tinted Liquid Glass Verdict Stamp slamming into lower safe zone with micro-shake."""
    u = c.W / 1080.0
    col = rgb(seg.get("color"), CRIMSON)
    al = env_alpha(lt, dur, 0.06, 0.22)
    if al <= 0:
        return
    if 0.12 <= lt < 0.28:
        mag = (0.28 - lt) / 0.16 * 7.0 * u
        rnd = np.random.default_rng(int(c.t * 60))
        M = np.float32([[1, 0, rnd.uniform(-mag, mag)], [0, 1, rnd.uniform(-mag, mag)]])
        c.img = cv2.warpAffine(c.img, M, (c.W, c.H), borderMode=cv2.BORDER_REFLECT)

    word = str(seg.get("text", "BUKAN INFLASI")).upper()
    eyebrow = str(seg.get("eyebrow", "KESIMPULAN")).upper()
    cw = int(min(c.W * SAFE_W_LOWER, 780 * u))
    ch = int(156 * u)
    cx = safe_lower_cx(c, cw)
    cy = safe_lower_cy(c, ch, pref_y=0.70)

    k = clamp(lt / 0.14)
    sc = 1.65 - 0.65 * (k * k) if lt < 0.14 else (1.0 + 0.06 * math.sin(math.pi * clamp((lt - 0.14) / 0.18)))
    slab = glass_slab(c, cw, ch, 34 * u, cx, cy, tint=col, tint_amt=0.28, dark=0.45)
    d = ImageDraw.Draw(slab)
    d.rounded_rectangle([4, 4, cw - 5, ch - 5], 32 * u, outline=col + (210,), width=3)
    d.text((cw * 0.5, 42 * u), eyebrow, font=fx.font("mono", 22 * u), fill=col + (255,), anchor="mm")
    fsz = 58 * u
    while fsz > 28 * u and fx.font("pop", fsz).getlength(word) > cw - 68 * u:
        fsz *= 0.93
    d.text((cw * 0.5, 102 * u), word, font=fx.font("pop", fsz), fill=WHITE + (255,), anchor="mm")
    fx.place(c, fx.shadowed(slab, int(18 * u), int(10 * u), 120), cx, cy, sc, float(seg.get("angle", -3.0)), al)


def fx_glass_outro(c, seg, lt, dur):
    """Spatial Liquid Glass Outro: glass word behind head + summary card + interactive Follow glass pill."""
    u = c.W / 1080.0
    col = rgb(seg.get("color"), CYAN)
    al = env_alpha(lt, dur, 0.12, 0.20)
    if al <= 0:
        return
    word = str(seg.get("text", "RUPIAH")).upper()
    sub = str(seg.get("sub", "Problem sebenarnya."))
    cta = str(seg.get("cta", "Part 2 Â· Mata Uang"))

    im, sz = cached(seg, "ow", lambda: glass_display_word(word, 920 * u, 235 * u, kind="pop", tint=ICE, glow_col=col))
    p = ease_out(lt / 0.34)
    cy_w = max(head_top_y(seg, c) - sz * 0.14, c.H * SAFE_TOP + sz * 0.36)
    fx.place(c, im, c.W * 0.5, cy_w + (1.0 - p) * 24 * u, 1.0, 0, al * p, behind=True)

    # Refractive Glass Outro Card + Glass Follow Toggle inside safe zone
    q = ease_back((lt - 0.14) / 0.32) if lt > 0.14 else 0.0
    if q > 0.01:
        cw, ch = int(min(c.W * SAFE_W_LOWER, 790 * u)), int(184 * u)
        cx = safe_lower_cx(c, cw)
        cy = safe_lower_cy(c, ch, pref_y=0.69) + (1.0 - q) * 32 * u
        slab = glass_slab(c, cw, ch, 38 * u, cx, cy, tint=col, tint_amt=0.14, dark=0.45)
        d = ImageDraw.Draw(slab)
        d.text((38 * u, 46 * u), cta.upper(), font=fx.font("mono", 22 * u), fill=col + (245,), anchor="lm")
        d.text((38 * u, 114 * u), sub, font=fx.font("didoneib", 52 * u), fill=WHITE + (255,), anchor="lm")

        # Glass Follow button inside card (flips to Following at 58% of outro)
        on = lt >= dur * 0.56
        bw, bh = int(206 * u), int(64 * u)
        bx0, by0 = cw - bw - 30 * u, ch * 0.5 - bh * 0.5
        b_col = MINT if on else col
        d.rounded_rectangle([bx0, by0, bx0 + bw, by0 + bh], bh // 2, fill=b_col + (225,), outline=WHITE + (180,), width=2)
        d.text((bx0 + bw * 0.5, by0 + bh * 0.5), "Following" if on else "+ Follow", font=fx.font("uib", 26 * u), fill=INK + (255,) if on else WHITE + (255,), anchor="mm")
        fx.place(c, fx.shadowed(slab, int(20 * u), int(10 * u), 120), cx, cy, 0.88 + 0.12 * q, 0, al * clamp((lt - 0.14) / 0.10))


LOWER_UI_FX = {
    "glass-hook", "glass-broll", "glass-bento", "glass-track", "glass-type", "glass-toggles",
    "glass-spotlight-word", "glass-ots", "glass-stack", "glass-checklist",
    "glass-verdict", "glass-outro"
}


def fx_glass_captions(c, seg, t, active_names):
    """Minimal Safe-Zone Liquid Glass Pill Subtitles (auto-hides whenever any lower glass card is visible)."""
    if active_names & LOWER_UI_FX:
        return
    u = c.W / 1080.0
    blocks = seg["_blocks"]
    cur = None
    for b, s, e in blocks:
        if s <= t < e:
            cur = (b, s, e)
            break
    if cur is None:
        return
    b, bs, be = cur
    txt = " ".join(w["w"] for w in b).rstrip(",;:")
    f = fx.font("uib", 38 * u)
    max_tw = c.W * SAFE_W_LOWER - 72 * u
    while f.getlength(txt) > max_tw and f.size > 20:
        f = fx.font("uib", int(f.size * 0.92))
    pw = int(f.getlength(txt) + 64 * u)
    ph = int(76 * u)
    cx = safe_lower_cx(c, pw)
    cy = safe_lower_cy(c, ph, pref_y=0.72)
    al = clamp((t - bs) / 0.08) * clamp((be - t) / 0.10)
    sc = 0.93 + 0.07 * ease_out((t - bs) / 0.12)
    pill = glass_slab(c, pw, ph, ph / 2.0, cx, cy, tint=ICE, tint_amt=0.12, dark=0.46)
    ImageDraw.Draw(pill).text((pw * 0.5, ph * 0.5), txt, font=f, fill=WHITE + (250,), anchor="mm")
    fx.place(c, fx.shadowed(pill, int(10 * u), int(5 * u), 85), cx, cy, sc, 0, al)


EFFECTS = {
    "glass-hook": fx_glass_hook,
    "glass-broll": fx_glass_broll,
    "glass-bento": fx_glass_bento,
    "glass-track": fx_glass_track,
    "glass-type": fx_glass_type,
    "glass-toggles": fx_glass_toggles,
    "glass-spotlight-word": fx_glass_spotlight_word,
    "glass-ots": fx_glass_ots,
    "glass-stack": fx_glass_stack,
    "glass-checklist": fx_glass_checklist,
    "glass-verdict": fx_glass_verdict,
    "glass-outro": fx_glass_outro,
}


# ==============================================================================
# BESPOKE CRYSTALLINE LIQUID GLASS AUDIO SYNTHESIS (48kHz STEREO)
# ==============================================================================
SR = 48000


def _env(n, atk, dec):
    t = np.arange(n) / SR
    return np.minimum(1.0, t / max(atk, 1e-4)) * np.exp(-t / dec)


def sfx_glass_chime():
    """Crystalline bell-like harmonic shimmer for glass hooks & reveals."""
    n = int(0.45 * SR)
    t = np.arange(n) / SR
    s = (
        0.50 * np.sin(2 * np.pi * 1046.5 * t) * _env(n, 0.004, 0.14)
        + 0.30 * np.sin(2 * np.pi * 1568.0 * t) * _env(n, 0.003, 0.10)
        + 0.20 * np.sin(2 * np.pi * 2093.0 * t) * _env(n, 0.002, 0.07)
    )
    return s * 0.36


def sfx_glass_drop():
    """Soft refractive water-drop pop for glass cards & toggles."""
    n = int(0.14 * SR)
    t = np.arange(n) / SR
    f = 420.0 + 780.0 * (1.0 - np.exp(-t / 0.025))
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(n, 0.002, 0.036)
    return s * 0.42


def sfx_glass_tick():
    """Crisp crystalline glass click for checklists & follow button."""
    n = int(0.06 * SR)
    t = np.arange(n) / SR
    s = (
        np.sin(2 * np.pi * 2637.0 * t) * _env(n, 0.0008, 0.012)
        + 0.4 * np.sin(2 * np.pi * 3951.0 * t) * _env(n, 0.0005, 0.007)
    )
    return s * 0.34


def sfx_glass_whoosh():
    """Airy filtered spatial glide for B-roll & over-the-shoulder zoom."""
    n = int(0.38 * SR)
    t = np.linspace(0, 1, n)
    rng = np.random.default_rng(12)
    x = rng.standard_normal(n)
    # Simple resonant lowpass sweep
    y = np.empty_like(x)
    p = 0.0
    cut = 350.0 + 3200.0 * (np.sin(np.pi * t) ** 2)
    a = np.exp(-2 * np.pi * cut / SR)
    for i in range(n):
        p = (1.0 - a[i]) * x[i] + a[i] * p
        y[i] = p
    y /= (np.abs(y).max() + 1e-9)
    return y * (np.sin(np.pi * t) ** 1.5) * 0.28


def sfx_glass_thud():
    """Warm muffled sub-glass impact for verdicts & slams."""
    n = int(0.36 * SR)
    t = np.arange(n) / SR
    f = 58.0 + 82.0 * np.exp(-t / 0.035)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(n, 0.002, 0.11) + 0.18 * np.sin(2 * np.pi * 1318.0 * t) * _env(n, 0.001, 0.03)
    return s * 0.52


GLASS_SFX = {
    "chime": sfx_glass_chime,
    "drop": sfx_glass_drop,
    "tick": sfx_glass_tick,
    "whoosh": sfx_glass_whoosh,
    "thud": sfx_glass_thud,
}


def collect_glass_sfx(segments):
    evs = []
    for seg in segments:
        k, s0, d = seg["fx"], seg["start"], max(0.1, seg["end"] - seg["start"])
        if k == "glass-hook":
            evs += [(s0 + 0.04, "chime", 0.85), (s0 + 0.16, "drop", 0.65)]
        elif k == "glass-broll":
            evs += [(s0, "whoosh", 0.75), (s0 + 0.22, "drop", 0.65)]
        elif k == "glass-bento":
            evs += [(s0 + 0.04, "chime", 0.70), (s0 + 0.18, "drop", 0.65), (s0 + 0.28, "drop", 0.60)]
        elif k == "glass-track":
            evs += [(s0, "tick", 0.75), (s0 + 0.16, "drop", 0.55)]
        elif k == "glass-type":
            evs += [(s0 + 0.04, "drop", 0.70)]
        elif k == "glass-toggles":
            evs.append((s0, "drop", 0.55))
            ticks = [float(x) for x in str(seg["ticks"]).split("|")] if seg.get("ticks") else [0.45, 0.90]
            for tk in ticks:
                evs.append((s0 + tk, "tick", 0.90))
        elif k == "glass-spotlight-word":
            evs += [(s0 + 0.04, "chime", 0.78)]
        elif k == "glass-ots":
            evs += [(s0 + d * 0.42, "whoosh", 0.65), (s0 + d * 0.84, "drop", 0.70)]
        elif k == "glass-stack":
            n = len(str(seg.get("text", "a|b")).split("|"))
            for i in range(n):
                evs.append((s0 + 0.10 + i * 0.42, "drop", 0.75))
        elif k == "glass-checklist":
            evs.append((s0, "drop", 0.55))
            ticks = [float(x) for x in str(seg["ticks"]).split("|")] if seg.get("ticks") else [0.3 + (d - 0.6) * (i + 1) / 3 for i in range(3)]
            for tk in ticks:
                evs.append((s0 + tk, "tick", 0.88))
        elif k == "glass-verdict":
            evs += [(s0 + 0.06, "thud", 0.90)]
        elif k == "glass-outro":
            evs += [(s0 + 0.04, "chime", 0.80), (s0 + d * 0.56, "tick", 0.95)]
    return evs


def write_glass_sfx_wav(path, evs, dur, gain_db=-4.0):
    out = np.zeros(int(dur * SR) + SR, np.float64)
    g0 = 10.0 ** (gain_db / 20.0)
    cache = {}
    for t, name, g in evs:
        if name not in cache:
            cache[name] = GLASS_SFX[name]()
        s = cache[name]
        i = int(t * SR)
        if i < 0 or i >= len(out):
            continue
        j = min(len(out), i + len(s))
        out[i:j] += s[:j - i] * g * g0
    out = np.clip(out[:int(dur * SR)], -0.97, 0.97)
    pcm = (np.repeat(out[:, None], 2, axis=1) * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def load_tracking(src, cache_path, fps, fr, W, H):
    aw = 540 if W <= H else int(round(540 * W / H / 2)) * 2
    ah = int(round(aw * H / W / 2)) * 2
    if cache_path and os.path.exists(cache_path):
        d = np.load(cache_path)
        return d["masks"], d["sm"], aw, ah
    print("Tracking speaker face & person mask...", flush=True)
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
    return np.stack(masks, axis=0), sm, aw, ah


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--plan", required=True)
    ap.add_argument("--words")
    ap.add_argument("--cache", help="Optional .npz tracking cache")
    ap.add_argument("--still", help="Comma-separated seconds to save preview PNGs")
    ap.add_argument("--no-sfx", action="store_true")
    ap.add_argument("--sfx-volume", type=float, default=-4.0)
    a = ap.parse_args()

    fr, fps, dur, sw, sh = fx.probe(a.src)
    W, H = (1080, int(round(1080 * sh / sw / 2)) * 2) if sw <= sh else (int(round(1080 * sw / sh / 2)) * 2, 1080)
    plan = json.load(open(a.plan, encoding="utf-8"))
    raw_list = plan.get("effects", []) if isinstance(plan, dict) else plan
    sfx_on = (not a.no_sfx) and (plan.get("sfx", True) is not False if isinstance(plan, dict) else True)
    sfx_db = float(plan.get("sfx_volume", a.sfx_volume)) if isinstance(plan, dict) else a.sfx_volume

    words_path = a.words or (os.path.splitext(a.src)[0] + ".words.json")
    allw = json.load(open(words_path, encoding="utf-8")) if os.path.exists(words_path) else []

    masks_arr, sm, aw, ah = load_tracking(a.src, a.cache, fps, fr, W, H)
    sc = W / aw
    n_m = len(masks_arr)

    segments = []
    cap_seg = None
    for raw in raw_list:
        name = raw["fx"].lower().strip()
        seg = dict(raw)
        seg["fx"] = name
        seg["start"] = max(0.0, float(seg.get("start", 0.0)))
        seg["end"] = min(dur, float(seg.get("end", dur)))
        if name == "glass-captions":
            seg["_blocks"] = fx.cap_blocks(allw, "pill", None, 0) if allw else []
            cap_seg = seg
            continue
        if name not in EFFECTS:
            sys.exit(f"Unknown Liquid Glass effect '{name}'. Available: {', '.join(EFFECTS)}")
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
    sfx_path = None
    if stills is None:
        os.makedirs(os.path.dirname(os.path.abspath(a.dst)), exist_ok=True)
        cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(fr), "-i", "-", "-i", a.src]
        evs = collect_glass_sfx(segments) if sfx_on else []
        if evs:
            sfx_path = os.path.splitext(a.dst)[0] + ".sfx.wav"
            write_glass_sfx_wav(sfx_path, evs, dur, sfx_db)
            cmd += ["-i", sfx_path]
            print(f"[style-12] Adding {len(evs)} crystalline Liquid Glass sound effects.", flush=True)
            cmd += [
                "-filter_complex",
                "[1:a:0]aresample=48000,aformat=channel_layouts=stereo[v0];[v0][2:a]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.97:level=disabled[a]",
                "-map", "0:v", "-map", "[a]"
            ]
        else:
            cmd += ["-map", "0:v", "-map", "1:a:0?"]
        enc = subprocess.Popen(
            cmd + ["-c:v", "libx264", "-crf", "17", "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", a.dst],
            stdin=subprocess.PIPE
        )

    print(f"[style-12] Rendering {'stills' if stills else 'video'} ({len(segments)} Liquid Glass modules)...", flush=True)
    for i, frame in enumerate(fx.read_frames(a.src, W, H, fr)):
        t = i / fps
        if stills is not None and i not in stills:
            if i > stills[-1]:
                break
            continue
        act = [seg for seg in segments if seg["start"] <= t < seg["end"]]
        if act or cap_seg is not None:
            c = fx.Ctx()
            c.W, c.H, c.t, c.fps = W, H, t, fps
            c.img = frame.astype(np.float32) / 255.0
            m = masks_arr[i] if i < n_m else None
            c.m = cv2.resize(m, (W, H), interpolation=cv2.INTER_LINEAR).astype(np.float32) / 255.0 if m is not None else np.zeros((H, W), np.float32)
            fx_, fy_, fw_ = sm[min(i, len(sm) - 1)]
            c.fx, c.fy, c.fw = fx_ * sc, fy_ * sc, max(fw_ * sc, W * 0.05)
            # 1. Spotlight lighting pass first
            for seg in act:
                apply_glass_spotlight(c, seg, t - seg["start"], max(0.05, seg["end"] - seg["start"]))
            # 2. Liquid Glass visual modules
            active_names = {seg["fx"] for seg in act}
            for seg in act:
                EFFECTS[seg["fx"]](c, seg, t - seg["start"], max(0.05, seg["end"] - seg["start"]))
            # 3. Safe-Zone Glass Pill Micro-Subtitles ONLY during breathing gaps
            if cap_seg is not None:
                fx_glass_captions(c, cap_seg, t, active_names)
            frame = (np.clip(c.img, 0, 1) * 255 + 0.5).astype(np.uint8)
        if stills is not None:
            out = a.dst.replace(".png", f"_{t:.2f}.png") if len(stills) > 1 else a.dst
            cv2.imwrite(out, cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
            print("saved", out, flush=True)
        else:
            enc.stdin.write(frame.tobytes())
            if i % int(fps * 15) == 0:
                print(f"  [style-12] {t:5.1f}s / {dur:.1f}s", flush=True)

    if enc:
        enc.stdin.close()
        rc = enc.wait()
        if sfx_path and os.path.exists(sfx_path):
            os.remove(sfx_path)
        if rc != 0:
            sys.exit(f"ffmpeg exited with code {rc}")
        print(f"[style-12] Done: {a.dst}", flush=True)


if __name__ == "__main__":
    main()

