#!/usr/bin/env python3
"""Preview Engine for Reels AI Director.

Generates visual previews BEFORE final rendering:
1. Contact sheet & keyframe check stills at crucial editorial timestamps
   (Hook, Headline, Data Card, Spotlight, Climax, Outro) to inspect safe zones & face masking.
2. Fast proxy video preview (540x960, ultrafast, full audio & pacing) for client/user review.

Usage:
  python preview.py stills <video.mp4> --plan <plan.json> --out check_sheet.jpg
  python preview.py proxy <video.mp4> --plan <plan.json> --out preview.mp4 [--width 540]
"""
import argparse
import json
import math
import os
import subprocess
import sys
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))


def get_critical_timestamps(plan_path, duration):
    """Finds the most important editorial timestamps to sample for check stills."""
    try:
        data = json.load(open(plan_path, encoding='utf-8'))
        effects = data.get('effects', data) if isinstance(data, dict) else data
    except Exception:
        effects = []

    stills = []
    # Always check:
    # 1. Hook (midpoint of first effect or 1.5s)
    if effects:
        e0 = effects[0]
        stills.append(round((e0.get('start', 0) + min(e0.get('end', 3.0), 3.0)) / 2.0, 2))
    else:
        stills.append(1.5)

    # 2. Key visual moments (data, checklist, spotlight, headlines, pop-words)
    key_types = {'data-compare', 'liquid-glass-graph', 'checklist', 'headline-box', 'pop-word', 'spotlight', 'glass-hook', 'hook-card', 'tape-label', 'broll-split'}
    for e in effects:
        fx = e.get('fx', '')
        if fx in key_types:
            mid = round((e.get('start', 0) + e.get('end', 0)) / 2.0, 2)
            if not any(abs(mid - s) < 2.5 for s in stills) and mid < duration - 1.0:
                stills.append(mid)

    # 3. Outro / Climax
    if duration > 10:
        stills.append(round(duration - 2.5, 2))

    # Keep between 4 and 8 keyframes
    stills = sorted(list(set(stills)))
    if len(stills) > 6:
        # Sample down to 6 evenly
        indices = np.linspace(0, len(stills) - 1, 6, dtype=int)
        stills = [stills[i] for i in indices]
    return stills


def resolve_video_path(video_path):
    if os.path.isdir(video_path):
        valid_exts = ('.mp4', '.mov', '.mkv', '.webm', '.avi')
        found = [
            os.path.join(video_path, f)
            for f in sorted(os.listdir(video_path))
            if f.lower().endswith(valid_exts)
        ]
        if not found:
            sys.exit(f"No video files found in folder: {video_path}")
        return found[0]
    return video_path


def generate_stills(video_path, plan_path, out_sheet_path, timestamps=None):
    """Renders keyframes using fx.py engine and combines them into an annotated contact sheet."""
    video_path = resolve_video_path(video_path)
    import fx
    fr, fps, dur, sw, sh = fx.probe(video_path)
    if not timestamps:
        timestamps = get_critical_timestamps(plan_path, dur)

    print(f"--- [Preview Stage 1/2] Sampling {len(timestamps)} critical keyframes: {timestamps} ---", flush=True)
    temp_dir = os.path.join(os.path.dirname(os.path.abspath(out_sheet_path)), "_preview_tmp")
    os.makedirs(temp_dir, exist_ok=True)

    still_str = ",".join(str(t) for t in timestamps)
    temp_pattern = os.path.join(temp_dir, "frame.png")

    # Run fx.py with --still flag
    cmd = [
        sys.executable,
        os.path.join(ROOT, "scripts", "fx.py"),
        "--plan", plan_path,
        video_path,
        temp_pattern,
        "--still", still_str,
        "--width", "540"
    ]
    subprocess.run(cmd, check=True)

    # Collect rendered frames
    rendered_frames = []
    for t in timestamps:
        p = os.path.join(temp_dir, f"frame_{t:.2f}.png")
        if os.path.exists(p):
            im = cv2.imread(p)
            if im is not None:
                # Add timestamp badge
                cv2.rectangle(im, (12, 12), (180, 52), (15, 23, 42), -1)
                cv2.putText(im, f"T = {t:.1f}s", (24, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (56, 189, 248), 2)
                # Draw safe zone outline (light dotted overlay)
                h, w = im.shape[:2]
                top_y = int(0.135 * h)
                bot_y = int(0.772 * h)
                right_x = int(0.835 * w)
                cv2.line(im, (0, top_y), (w, top_y), (0, 240, 255), 1)
                cv2.line(im, (0, bot_y), (w, bot_y), (0, 240, 255), 1)
                cv2.line(im, (right_x, bot_y - 200), (right_x, bot_y), (0, 240, 255), 1)
                rendered_frames.append(im)

    if not rendered_frames:
        sys.exit("Error: No frames were rendered for preview sheet.")

    # Grid arrangement: 2 rows of 3 columns (or 1 row if <= 3)
    n = len(rendered_frames)
    cols = 3 if n >= 3 else n
    rows = math.ceil(n / cols)

    cell_h, cell_w = rendered_frames[0].shape[:2]
    sheet = np.zeros((rows * cell_h, cols * cell_w, 3), dtype=np.uint8)

    for idx, f_ in enumerate(rendered_frames):
        r = idx // cols
        c = idx % cols
        sheet[r * cell_h:(r + 1) * cell_h, c * cell_w:(c + 1) * cell_w] = f_

    # Clean up temp files
    for t in timestamps:
        p = os.path.join(temp_dir, f"frame_{t:.2f}.png")
        if os.path.exists(p):
            try: os.remove(p)
            except Exception: pass
    try: os.rmdir(temp_dir)
    except Exception: pass

    cv2.imwrite(out_sheet_path, sheet)
    print(f"Saved keyframe review sheet: {out_sheet_path} ({sheet.shape[1]}x{sheet.shape[0]})")
    return out_sheet_path


def generate_proxy(video_path, plan_path, out_proxy_path, width=540):
    """Renders a fast 540p proxy preview video for real-time motion and audio evaluation."""
    video_path = resolve_video_path(video_path)
    print(f"--- [Preview Stage 2/2] Encoding fast 540p proxy video ({width}p)... ---", flush=True)
    cmd = [
        sys.executable,
        os.path.join(ROOT, "scripts", "fx.py"),
        "--plan", plan_path,
        video_path,
        out_proxy_path,
        "--width", str(width)
    ]
    subprocess.run(cmd, check=True)
    print(f"Saved proxy preview video: {out_proxy_path}")
    return out_proxy_path


def main():
    ap = argparse.ArgumentParser(description="Preview-First Engine for Video Edits")
    sub = ap.add_subparsers(dest="cmd")

    p_stills = sub.add_parser("stills")
    p_stills.add_argument("video")
    p_stills.add_argument("--plan", required=True)
    p_stills.add_argument("--out", default="work/preview_sheet.jpg")
    p_stills.add_argument("--timestamps")

    p_proxy = sub.add_parser("proxy")
    p_proxy.add_argument("video")
    p_proxy.add_argument("--plan", required=True)
    p_proxy.add_argument("--out", default="work/preview_proxy.mp4")
    p_proxy.add_argument("--width", type=int, default=540)

    args = ap.parse_args()
    if args.cmd == "stills":
        ts = [float(x.strip()) for x in args.timestamps.split(",")] if args.timestamps else None
        generate_stills(args.video, args.plan, args.out, ts)
    elif args.cmd == "proxy":
        generate_proxy(args.video, args.plan, args.out, args.width)
    else:
        ap.print_help()


if __name__ == '__main__':
    main()
