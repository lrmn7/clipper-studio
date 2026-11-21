#!/usr/bin/env python3
"""Auto face-tracked reframe: any aspect (16:9 etc.) -> 1080x1920 (9:16) for Reels/TikTok/Shorts.
Usage: python reframe_reels.py input.mp4 output.mp4 [--tau 0.55]
"""
import argparse, math, os, subprocess, sys
import numpy as np
import cv2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ap = argparse.ArgumentParser()
ap.add_argument("src"); ap.add_argument("dst")
ap.add_argument("--tau", type=float, default=0.55, help="smoothing seconds (higher = calmer camera)")
a_ = ap.parse_args()
SRC, DST = a_.src, a_.dst

cap = cv2.VideoCapture(SRC)
fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
sw = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)); sh = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
if sw * 16 <= sh * 9 + 2:
    sys.exit("Input is already vertical; just scale to 1080x1920 with ffmpeg.")
dw, dh = 640, int(round(640 * sh / sw))
fd = cv2.FaceDetectorYN.create(os.path.join(ROOT, "models", "yunet.onnx"), "", (dw, dh), 0.55, 0.3, 10)

xs, idx = [], 0
while True:
    ok, frame = cap.read()
    if not ok: break
    v = np.nan
    if idx % 2 == 0:
        _, faces = fd.detect(cv2.resize(frame, (dw, dh), interpolation=cv2.INTER_AREA))
        if faces is not None and len(faces):
            r = max(faces, key=lambda f: f[2] * f[3] * f[-1])
            v = (r[0] + r[2] * 0.5) * (sw / dw)
    xs.append(v); idx += 1
cap.release()

arr = np.array(xs, dtype=np.float64); good = ~np.isnan(arr)
if good.any(): arr[~good] = np.interp(np.where(~good)[0], np.where(good)[0], arr[good])
else: arr[:] = sw / 2.0
a = 1.0 - math.exp(-1.0 / (fps * a_.tau))
for i in range(1, len(arr)): arr[i] = arr[i-1] + a * (arr[i] - arr[i-1])
for i in range(len(arr) - 2, -1, -1): arr[i] = arr[i+1] + a * (arr[i] - arr[i+1])

crop_w = int(round(sh * 9 / 16)); W, H = 1080, 1920
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24",
    "-s", f"{W}x{H}", "-r", f"{fps:.6f}", "-i", "-", "-i", SRC, "-map", "0:v", "-map", "1:a:0?",
    "-c:v", "libx264", "-crf", "16", "-preset", "fast", "-pix_fmt", "yuv420p",
    "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", DST], stdin=subprocess.PIPE)
cap = cv2.VideoCapture(SRC); i = 0
while True:
    ok, frame = cap.read()
    if not ok: break
    x0 = max(0, min(sw - crop_w, int(round(arr[min(i, len(arr)-1)] - crop_w / 2))))
    enc.stdin.write(cv2.resize(frame[:, x0:x0+crop_w], (W, H), interpolation=cv2.INTER_LANCZOS4).tobytes())
    i += 1
cap.release(); enc.stdin.close()
if enc.wait() != 0: sys.exit("ffmpeg failed")
print(f"Done: {i} frames -> {DST}")
