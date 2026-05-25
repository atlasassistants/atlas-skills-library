#!/usr/bin/env python3
"""Combine rendered slide PNGs into a single PDF at LinkedIn document-post spec (1080x1350)."""
import json
import sys
from pathlib import Path
from typing import Dict

from PIL import Image


def build(slides_dir: str, out_path: str) -> Dict:
    sdir = Path(slides_dir)
    slides = sorted(sdir.glob("slide-*.png"))
    if not slides:
        return {"ok": False, "error": "No slide PNGs found."}
    images = []
    for sp in slides:
        img = Image.open(sp)
        if img.size != (1080, 1350):
            img = img.resize((1080, 1350))
        if img.mode != "RGB":
            img = img.convert("RGB")
        images.append(img)
    first, rest = images[0], images[1:]
    first.save(out_path, "PDF", save_all=True, append_images=rest, resolution=72.0)
    return {"ok": True, "out_path": out_path, "page_count": len(images)}


def main():
    if len(sys.argv) < 3:
        print(json.dumps({"ok": False, "error": "Usage: build_pdf.py <slides_dir> <out.pdf>"}))
        sys.exit(2)
    print(json.dumps(build(sys.argv[1], sys.argv[2]), indent=2))


if __name__ == "__main__":
    main()
