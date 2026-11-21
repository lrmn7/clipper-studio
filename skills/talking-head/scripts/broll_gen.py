#!/usr/bin/env python3
"""Contextual B-Roll & Infographic Generator for Reels / Short-Form Video.

Generates high-resolution graphic B-roll assets (data comparison boards, KPI cards,
editorial quotes, process checklists, and conceptual boards) locally using Pillow.
Can be used as standalone overlays, full-screen cutaways, or within glass/split-screen effects.

Usage:
  python broll_gen.py data-compare --title "BI-RATE HIKE" --v1 "5.75%" --v2 "6.00%" --delta "+25 BPS" --out broll/bi_rate.png
  python broll_gen.py kpi --label "MARKET GAP" --val "10x" --sub "Artis vs Guru" --out broll/kpi.png
  python broll_gen.py quote --quote "Market tidak punya hati" --author "Prinsip Ekonomi" --out broll/quote.png
  python broll_gen.py process --title "HUKUM PASAR" --steps "1. Permintaan|2. Penawaran|3. Kelangkaan" --out broll/steps.png
"""
import argparse
import os
import sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_DIR = os.path.join(ROOT, 'fonts')


def get_font(name, size):
    font_files = {
        'bold': 'ArchivoBlack-Regular.ttf',
        'serif': 'InstrumentSerif-Italic.ttf',
        'serif_bold': 'PlayfairDisplay-Italic.ttf',
        'mono': 'SpaceMono-Bold.ttf',
        'ui': 'Inter.ttf',
        'mont': 'Montserrat.ttf',
        'pop': 'Poppins-Bold.ttf'
    }
    path = os.path.join(FONT_DIR, font_files.get(name, 'Inter.ttf'))
    if os.path.exists(path):
        try:
            return ImageFont.truetype(path, int(size))
        except Exception:
            pass
    return ImageFont.load_default()


def rrect(draw, bbox, r, fill, outline=None, width=1):
    x0, y0, x1, y1 = bbox
    draw.rounded_rectangle([x0, y0, x1, y1], radius=r, fill=fill, outline=outline, width=width)


def make_data_compare(title, v1, sub1, v2, sub2, delta, out_path, w=1000, h=640, theme='dark'):
    """Generates a high-end data comparison board (e.g. BI Rate 5.75% vs 6.00%)."""
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)

    bg_col = (18, 24, 38, 240) if theme == 'dark' else (248, 249, 252, 245)
    border_col = (56, 189, 248, 120) if theme == 'dark' else (203, 213, 225, 200)
    text_pri = (255, 255, 255, 255) if theme == 'dark' else (15, 23, 42, 255)
    text_sec = (148, 163, 184, 255) if theme == 'dark' else (100, 116, 139, 255)

    # Outer rounded container
    rrect(d, (20, 20, w - 20, h - 20), 32, bg_col, border_col, 3)

    # Header pill
    f_mono = get_font('mono', 22)
    f_bold = get_font('bold', 44)
    f_val = get_font('bold', 82)
    f_sub = get_font('ui', 20)
    f_delta = get_font('mono', 28)

    # Title header
    rrect(d, (50, 45, w - 50, 95), 14, (30, 41, 59, 180), border_col, 1)
    d.text((70, 58), title.upper(), font=f_mono, fill=(56, 189, 248, 255))

    # Two column panels
    col_w = (w - 140) // 2
    # Left column (Old / Previous)
    rrect(d, (50, 120, 50 + col_w, h - 160), 24, (24, 32, 50, 200), (71, 85, 105, 100), 2)
    d.text((75, 140), (sub1 or "PREVIOUS").upper(), font=f_sub, fill=text_sec)
    d.text((75, 190), v1, font=f_val, fill=(226, 232, 240, 240))

    # Right column (New / Current)
    rrect(d, (70 + col_w, 120, w - 50, h - 160), 24, (16, 36, 48, 220), (52, 211, 153, 160), 2)
    d.text((95 + col_w, 140), (sub2 or "NEW RATE").upper(), font=f_sub, fill=(52, 211, 153, 255))
    d.text((95 + col_w, 190), v2, font=f_val, fill=(52, 211, 153, 255))

    # Delta badge at bottom
    if delta:
        rrect(d, (50, h - 130, w - 50, h - 50), 20, (15, 23, 42, 240), (52, 211, 153, 200), 2)
        d.text((75, h - 105), f"DELTA: {delta}", font=f_delta, fill=(52, 211, 153, 255))

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    im.save(out_path, "PNG")
    print(f"Generated B-Roll data-compare -> {out_path}")


def make_kpi(label, val, sub, out_path, w=800, h=480, theme='glass'):
    """Generates a high-impact KPI / stat callout card."""
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)

    bg_col = (15, 23, 42, 230)
    border_col = (232, 36, 52, 180) if "gap" in label.lower() or "artis" in sub.lower() else (56, 189, 248, 160)
    val_col = (255, 214, 10, 255) if "gap" in label.lower() else (255, 255, 255, 255)

    rrect(d, (20, 20, w - 20, h - 20), 28, bg_col, border_col, 3)

    f_label = get_font('mono', 24)
    f_val = get_font('bold', 110)
    f_sub = get_font('serif_bold', 34)

    # Pill
    rrect(d, (45, 45, 45 + int(f_label.getlength(label)) + 30, 90), 12, (30, 41, 59, 200))
    d.text((60, 56), label.upper(), font=f_label, fill=(244, 233, 216, 255))

    d.text((45, 130), val, font=f_val, fill=val_col)
    if sub:
        d.text((48, 320), sub, font=f_sub, fill=(226, 232, 240, 230))

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    im.save(out_path, "PNG")
    print(f"Generated B-Roll KPI -> {out_path}")


def make_quote(quote, author, out_path, w=960, h=540):
    """Generates an editorial quotation or verdict board."""
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)

    rrect(d, (20, 20, w - 20, h - 20), 30, (22, 22, 24, 240), (255, 214, 10, 160), 2)

    f_quote = get_font('serif_bold', 52)
    f_auth = get_font('mono', 24)

    # Large quotation marks
    d.text((50, 40), "“", font=get_font('bold', 90), fill=(255, 214, 10, 180))

    # Multi-line quote text
    words = quote.split()
    lines = []
    cur = []
    for w_ in words:
        cur.append(w_)
        if f_quote.getlength(" ".join(cur)) > w - 160:
            cur.pop()
            lines.append(" ".join(cur))
            cur = [w_]
    if cur:
        lines.append(" ".join(cur))

    y = 140
    for l in lines:
        d.text((70, y), l, font=f_quote, fill=(255, 255, 255, 255))
        y += 66

    if author:
        d.text((75, y + 30), f"— {author.upper()}", font=f_auth, fill=(255, 214, 10, 240))

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    im.save(out_path, "PNG")
    print(f"Generated B-Roll Quote -> {out_path}")


def make_process(title, steps, out_path, w=1000, h=640, theme='dark'):
    """Generates an editorial process card / checklist board."""
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)

    bg_col = (18, 24, 38, 245) if theme == 'dark' else (248, 249, 252, 245)
    border_col = (56, 189, 248, 140) if theme == 'dark' else (203, 213, 225, 200)
    rrect(d, (20, 20, w - 20, h - 20), 32, bg_col, border_col, 3)

    f_title = get_font('bold', 34)
    f_step = get_font('ui', 26)
    f_num = get_font('mono', 24)

    # Title pill
    pill_w = int(f_title.getlength(title.upper()) + 60)
    rrect(d, (50, 45, 50 + pill_w, 95), 16, (56, 189, 248, 40), (56, 189, 248, 180), 2)
    d.text((75, 58), title.upper(), font=f_title, fill=(56, 189, 248, 255))

    items = [s.strip() for s in steps.split('|') if s.strip()]
    y = 135
    row_h = min(95, int((h - 170) / max(1, len(items))))

    for i, it in enumerate(items):
        rrect(d, (50, y, w - 50, y + row_h - 12), 16, (30, 41, 59, 180), (71, 85, 105, 140), 1)
        # Indicator badge
        badge_w = 40
        rrect(d, (68, y + (row_h - 12 - badge_w) // 2, 68 + badge_w, y + (row_h - 12 + badge_w) // 2), 10,
              (14, 165, 233, 220), None)
        d.text((80, y + (row_h - 12) // 2 - 13), str(i + 1), font=f_num, fill=(255, 255, 255, 255))
        # Text
        d.text((128, y + (row_h - 12) // 2 - 14), it, font=f_step, fill=(241, 245, 249, 255))
        y += row_h

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    im.save(out_path, "PNG")
    print(f"Generated B-Roll Process -> {out_path}")


def main():
    ap = argparse.ArgumentParser(description="Generate contextual graphic B-Roll assets")
    sub = ap.add_subparsers(dest="cmd")

    p_comp = sub.add_parser("data-compare")
    p_comp.add_argument("--title", default="ECONOMIC DATA AUDIT")
    p_comp.add_argument("--v1", required=True)
    p_comp.add_argument("--sub1", default="PREVIOUS")
    p_comp.add_argument("--v2", required=True)
    p_comp.add_argument("--sub2", default="NEW")
    p_comp.add_argument("--delta", default="")
    p_comp.add_argument("--out", required=True)

    p_kpi = sub.add_parser("kpi")
    p_kpi.add_argument("--label", required=True)
    p_kpi.add_argument("--val", required=True)
    p_kpi.add_argument("--sub", default="")
    p_kpi.add_argument("--out", required=True)

    p_quote = sub.add_parser("quote")
    p_quote.add_argument("--quote", required=True)
    p_quote.add_argument("--author", default="")
    p_quote.add_argument("--out", required=True)

    p_proc = sub.add_parser("process")
    p_proc.add_argument("--title", default="KEY STEPS")
    p_proc.add_argument("--steps", required=True, help="Pipe-separated steps: 'Step 1|Step 2|Step 3'")
    p_proc.add_argument("--out", required=True)

    args = ap.parse_args()
    if args.cmd == "data-compare":
        make_data_compare(args.title, args.v1, args.sub1, args.v2, args.sub2, args.delta, args.out)
    elif args.cmd == "kpi":
        make_kpi(args.label, args.val, args.sub, args.out)
    elif args.cmd == "quote":
        make_quote(args.quote, args.author, args.out)
    elif args.cmd == "process":
        make_process(args.title, args.steps, args.out)
    else:
        ap.print_help()


if __name__ == '__main__':
    main()
