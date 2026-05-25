#!/usr/bin/env python3
"""Build a contact sheet from rendered slide PNGs."""
import json
import math
import sys
from pathlib import Path
from typing import Dict

from PIL import Image, ImageDraw, ImageFont


TILE = 540  # half-size of 1080x1350 with proportion preserved
TILE_W, TILE_H = TILE, int(TILE * 1350 / 1080)


def build(slides_dir: str, out_path: str) -> Dict:
    sdir = Path(slides_dir)
    slides = sorted(sdir.glob("slide-*.png"))
    if not slides:
        return {"ok": False, "error": "No slides found in directory."}
    cols = 4
    rows = math.ceil(len(slides) / cols)
    sheet = Image.new("RGB", (TILE_W * cols + 20 * (cols + 1), TILE_H * rows + 20 * (rows + 1)), "white")
    try:
        font = ImageFont.truetype("Arial", 20)
    except Exception:
        font = ImageFont.load_default()
    draw = ImageDraw.Draw(sheet)
    for idx, sp in enumerate(slides):
        col, row = idx % cols, idx // cols
        x = 20 + col * (TILE_W + 20)
        y = 20 + row * (TILE_H + 20)
        img = Image.open(sp).resize((TILE_W, TILE_H))
        sheet.paste(img, (x, y))
        draw.text((x + 8, y + 8), sp.stem, fill="black", font=font, stroke_width=2, stroke_fill="white")
    sheet.save(out_path, "JPEG", quality=85)
    return {"ok": True, "out_path": out_path, "count": len(slides)}


def main():
    if len(sys.argv) < 3:
        print(json.dumps({"ok": False, "error": "Usage: create_contact_sheet.py <slides_dir> <out.jpg>"}))
        sys.exit(2)
    print(json.dumps(build(sys.argv[1], sys.argv[2]), indent=2))


if __name__ == "__main__":
    main()
