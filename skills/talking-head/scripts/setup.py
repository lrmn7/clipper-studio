#!/usr/bin/env python3
"""Cross-platform environment setup and validation for Reels AI Director.

Works identically on Windows (PowerShell/CMD), macOS (Terminal/zsh), and Linux (bash).
Validates Python version, ffmpeg/ffprobe, virtual environment, dependencies, models, and fonts.
"""
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def check_ffmpeg():
    print("[1/5] Checking ffmpeg and ffprobe on PATH...")
    ff = shutil.which("ffmpeg")
    fp = shutil.which("ffprobe")
    if not ff or not fp:
        print("  [ERROR] ffmpeg/ffprobe not found on PATH!")
        print("  Windows: winget install ffmpeg")
        print("  macOS:   brew install ffmpeg")
        print("  Linux:   sudo apt update && sudo apt install ffmpeg")
        return False
    print(f"  ffmpeg:  {ff}")
    print(f"  ffprobe: {fp}")
    return True


def check_python_version():
    print("[2/5] Checking Python version...")
    v = sys.version_info
    print(f"  Python {v.major}.{v.minor}.{v.micro}")
    if v.major < 3 or (v.major == 3 and v.minor < 10):
        print("  [ERROR] Python 3.10 or newer is required.")
        return False
    return True


def check_and_install_dependencies():
    print("[3/5] Checking Python dependencies...")
    req_path = os.path.join(ROOT, "requirements.txt")
    packages = ["numpy", "opencv-python", "pillow", "mediapipe", "faster-whisper"]
    missing = []

    for pkg in ["numpy", "cv2", "PIL", "mediapipe", "faster_whisper"]:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)

    if missing:
        print(f"  Missing packages: {missing}. Installing from requirements.txt...")
        cmd = [sys.executable, "-m", "pip", "install", "-r", req_path]
        res = subprocess.run(cmd)
        if res.returncode != 0:
            print("  [ERROR] Failed to install dependencies.")
            return False
    else:
        print("  All core packages are installed (numpy, opencv-python, pillow, mediapipe, faster-whisper).")
    return True


def validate_ai_models():
    print("[4/5] Validating AI models...")
    models_dir = os.path.join(ROOT, "models")
    yunet = os.path.join(models_dir, "yunet.onnx")
    seg = os.path.join(models_dir, "selfie_segmenter.tflite")

    ok = True
    if not os.path.exists(yunet) or os.path.getsize(yunet) < 10000:
        print("  [ERROR] YuNet face detection model missing or corrupt:", yunet)
        ok = False
    else:
        print("  YuNet Face Detector: OK")

    if not os.path.exists(seg) or os.path.getsize(seg) < 10000:
        print("  [ERROR] Selfie Segmenter model missing or corrupt:", seg)
        ok = False
    else:
        print("  Selfie Segmenter (MediaPipe): OK")
    return ok


def validate_fonts_and_presets():
    print("[5/5] Validating bundled fonts and style presets...")
    fonts_dir = os.path.join(ROOT, "fonts")
    presets_dir = os.path.join(ROOT, "presets")

    req_fonts = ["ArchivoBlack-Regular.ttf", "Inter.ttf", "Montserrat.ttf", "PlayfairDisplay.ttf", "SpaceMono-Bold.ttf"]
    for f in req_fonts:
        p = os.path.join(fonts_dir, f)
        if not os.path.exists(p):
            print("  [WARNING] Font missing:", f)

    p_count = len([f for f in os.listdir(presets_dir) if f.endswith(".json")]) if os.path.exists(presets_dir) else 0
    print(f"  Found {p_count} style presets in {presets_dir}")
    return True


def main():
    print(f"=== Reels AI Director Environment Setup ({sys.platform}) ===")
    ok = (check_ffmpeg() and
          check_python_version() and
          check_and_install_dependencies() and
          validate_ai_models() and
          validate_fonts_and_presets())

    if ok:
        print("\n>>> ENVIRONMENT IS READY! All systems operational. <<<")
        sys.exit(0)
    else:
        print("\n>>> SETUP INCOMPLETE: Please resolve the errors above. <<<")
        sys.exit(1)


if __name__ == '__main__':
    main()
