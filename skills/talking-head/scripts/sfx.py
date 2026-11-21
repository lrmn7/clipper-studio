"""Soft, original sound effects made with numpy: no sample files and no licences to worry about.

Each effect gets a small sound when it lands (a pop, tick, whoosh, impact, chime, paper or snap).
They are kept quiet and restrained on purpose: a pop on big words and cards, ticks on checks,
one low hit on stamps and drops, and no whoosh on every cut.

Supports 82+ effects across general FX, typographic moments, and glass interfaces.
Includes strict zero-SFX / clean-audio mode for serious topics, editorial styles, and podcasts.
"""
import wave
import numpy as np

SR = 48000


def _env(n, attack, decay):
    t = np.arange(n) / SR
    return np.minimum(1.0, t / max(attack, 1e-4)) * np.exp(-t / decay)


def _lowpass(x, cutoff):
    """One-pole low-pass with a per-sample cutoff (Hz)."""
    a = np.exp(-2 * np.pi * np.broadcast_to(cutoff, x.shape) / SR)
    y = np.empty_like(x); p = 0.0
    for i in range(len(x)):
        p = (1 - a[i]) * x[i] + a[i] * p
        y[i] = p
    return y


def pop():
    n = int(0.09 * SR); t = np.arange(n) / SR
    f = 240 + 820 * np.exp(-t / 0.012)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(n, 0.0015, 0.028)
    s += np.random.default_rng(1).standard_normal(n) * _env(n, 0.0004, 0.003) * 0.12
    return s * 0.5


def tick():
    n = int(0.035 * SR); t = np.arange(n) / SR
    s = np.sin(2 * np.pi * 2400 * t) * _env(n, 0.0004, 0.006) + np.sin(2 * np.pi * 4800 * t) * _env(n, 0.0003, 0.003) * 0.35
    return s * 0.32


def whoosh(dur=0.36):
    n = int(dur * SR); t = np.linspace(0, 1, n)
    y = _lowpass(np.random.default_rng(2).standard_normal(n), 300 + 4200 * np.sin(np.pi * t) ** 2)
    y = y / (np.abs(y).max() + 1e-9)
    return y * np.sin(np.pi * t) ** 1.6 * 0.32


def impact():
    n = int(0.5 * SR); t = np.arange(n) / SR
    f = 46 + 75 * np.exp(-t / 0.045)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(n, 0.002, 0.15)
    nz = _lowpass(np.random.default_rng(3).standard_normal(n), 900.0) * _env(n, 0.001, 0.03)
    s = s + nz / (np.abs(nz).max() + 1e-9) * 0.25
    return s / (np.abs(s).max() + 1e-9) * 0.62


def chime():
    n = int(0.4 * SR); t = np.arange(n) / SR
    s = (np.sin(2 * np.pi * 1760 * t) * 0.5 +
         np.sin(2 * np.pi * 2640 * t) * 0.3 +
         np.sin(2 * np.pi * 3520 * t) * 0.2) * _env(n, 0.002, 0.08)
    return s * 0.45


def paper():
    n = int(0.18 * SR); t = np.linspace(0, 1, n)
    nz = np.random.default_rng(4).standard_normal(n)
    s = _lowpass(nz, 1800 + 1200 * np.sin(np.pi * t)) * _env(n, 0.01, 0.05)
    return s / (np.abs(s).max() + 1e-9) * 0.28


def snap():
    n = int(0.04 * SR); t = np.arange(n) / SR
    s = np.sin(2 * np.pi * 3200 * t) * _env(n, 0.0002, 0.008)
    nz = np.random.default_rng(5).standard_normal(n) * _env(n, 0.0001, 0.004) * 0.4
    return (s + nz) * 0.4


SOUNDS = {
    'pop': pop, 'tick': tick, 'whoosh': whoosh, 'impact': impact,
    'chime': chime, 'paper': paper, 'snap': snap
}

DEFAULT = [(0.0, 'pop', 0.8)]
SILENT = ('captions', 'lean-in', 'slow-push', 'moody', 'wave-trim', 'rabbit-hole', 'clean', 'none')

MAP = {
    # Impacts / Punches
    'reject-stamp': [(0.06, 'impact', 0.9)],
    'backdrop-word': [(0.3, 'impact', 0.6)],
    'spotlight': [(0.0, 'impact', 0.65)],
    'led-sign': [(0.0, 'impact', 0.55)],
    'pop-word': [(0.0, 'pop', 0.8), (0.02, 'impact', 0.45)],
    'red-collage': [(0.0, 'impact', 0.6)],
    'match-cut': [(0.0, 'impact', 0.5)],
    'huge-strike': [(0.0, 'pop', 0.6)],
    'impact-frame': [(0.0, 'impact', 0.9)],
    'uninstall': [(0.0, 'impact', 0.45)],

    # UI / Ticks
    'locked-on': [(0.0, 'tick', 0.9), (0.16, 'tick', 0.7)],
    'over-the-shoulder-zoom': [(0.0, 'pop', 0.6)],
    'messages': [(0.0, 'pop', 0.5), (0.15, 'tick', 0.6)],
    'predict-keys': [(0.0, 'pop', 0.5), (0.12, 'tick', 0.7), (0.24, 'tick', 0.7)],
    'live-cursor': [(0.0, 'tick', 0.8), (0.15, 'pop', 0.5)],
    'voice-note': [(0.0, 'pop', 0.6), (0.2, 'tick', 0.7)],
    'head-stack': [(0.0, 'pop', 0.6), (0.2, 'tick', 0.7)],
    'tracklist': [(0.0, 'tick', 0.5)],
    'caption-pills': [(0.0, 'pop', 0.4)],
    'nameplate': [(0.0, 'pop', 0.5), (0.1, 'tick', 0.6)],

    # Motion / Whooshes
    'swipe': [(0.0, 'whoosh', 0.7)],
    'card-drop': [(0.0, 'whoosh', 0.55), (0.12, 'pop', 0.75)],
    'split-headline': [(0.0, 'whoosh', 0.55)],
    'reel-frame': [(0.0, 'whoosh', 0.5)],
    'halftone-paper': [(0.0, 'paper', 0.6), (0.05, 'whoosh', 0.45)],
    'dot-reveal': [(0.0, 'whoosh', 0.5)],
    'clone-row': [(0.0, 'whoosh', 0.6)],
    'day-dial': [(0.0, 'whoosh', 0.5), (0.2, 'tick', 0.8)],
    'orbit-ring': [(0.0, 'whoosh', 0.5)],
    'post-wall': [(0.0, 'whoosh', 0.5), (0.1, 'tick', 0.8)],
    'letter-dive': [(0.0, 'impact', 0.6), (0.35, 'whoosh', 0.7)],
    'layer-explode': [(0.0, 'whoosh', 0.6), (0.1, 'impact', 0.7)],
    'dolly-zoom': [(0.0, 'whoosh', 0.5)],
    'blow-away': [(0.0, 'whoosh', 0.8)],
    'rack-focus': [(0.0, 'whoosh', 0.4)],

    # Tactile / Paper & Blade
    'blade-slice': [(0.0, 'snap', 0.7), (0.08, 'whoosh', 0.55)],
    'sketch-words': [(0.0, 'paper', 0.6)],
    'banknote': [(0.0, 'paper', 0.6), (0.15, 'impact', 0.5)],
    'press-front': [(0.0, 'impact', 0.65), (0.04, 'paper', 0.7)],
    'paper-tear': [(0.0, 'paper', 0.8), (0.12, 'whoosh', 0.5)],
    'comment-drop': [(0.0, 'pop', 0.7), (0.25, 'tick', 0.8)],
    'code-body': [(0.0, 'impact', 0.5)],

    # Cards & Data
    'hook-card': [(0.0, 'whoosh', 0.55), (0.1, 'impact', 0.5)],
    'data-compare': [(0.0, 'whoosh', 0.5), (0.12, 'tick', 0.7)],
    'liquid-glass-graph': [(0.0, 'chime', 0.6), (0.15, 'tick', 0.7)],
}


def events(fx, start, end, opts):
    """Sound events for one effect as (time, sound, loudness)."""
    if fx in SILENT:
        return []
    d = end - start
    ev = list(MAP.get(fx, DEFAULT))
    if fx in ('todo', 'apple-toggles') and opts.get('ticks'):
        ev = [(float(t) - start, 'tick', 0.9) for t in str(opts['ticks']).split('|') if t.strip()]
    elif fx in ('checklist', 'todo', 'apple-toggles'):
        n = max(1, len(str(opts.get('text', 'a|b|c')).split('|')))
        ev = [(0.0, 'pop', 0.6)] + [((i + 1) * d / (n + 1), 'tick', 0.85) for i in range(n)]
    elif fx == 'countdown-flip':
        ev = [(float(i) * d / 3, 'tick', 1.0) for i in range(3)]
    elif fx == 'tap':
        ev = [(0.0, 'pop', 0.6), (float(opts['at']) - start if opts.get('at') else d * 0.5, 'tick', 1.0)]
    elif fx == 'huge-strike':
        ev = [(0.0, 'pop', 0.6), (float(opts.get('at', 0.6)), 'tick', 0.9)]
    elif fx == 'logo-link':
        ev = [(0.0, 'pop', 0.8), (min(0.35, d * 0.3), 'pop', 0.8)]
    return [(start + t, s, g) for t, s, g in ev if 0 <= t <= d]


def track(evs, duration, gain_db=0.0):
    """Mix events into a stereo int16 track of `duration` seconds."""
    out = np.zeros(int(duration * SR) + SR, np.float64); g0 = 10 ** (gain_db / 20); cache = {}
    for t, name, g in evs:
        if name not in cache:
            cache[name] = SOUNDS.get(name, pop)()
        s = cache[name]; i = int(t * SR)
        if i < 0 or i >= len(out):
            continue
        j = min(len(out), i + len(s)); out[i:j] += s[:j - i] * g * g0
    out = np.clip(out[:int(duration * SR)], -0.98, 0.98)
    return (np.repeat(out[:, None], 2, axis=1) * 32767).astype(np.int16)


def write(path, pcm):
    with wave.open(path, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
