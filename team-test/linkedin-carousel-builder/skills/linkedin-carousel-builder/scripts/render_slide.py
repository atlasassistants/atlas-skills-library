#!/usr/bin/env python3
"""Render one slide HTML → PNG via Playwright/Chromium.

The slide template renders a smaller chrome headline + footer; the AI illustration
is the hero (passed in as a data URI to dodge file:// asset-loading quirks across
platforms). See the Phase 8 architectural note for the Option 3 rationale.
"""
import base64
import json
import mimetypes
import sys
from pathlib import Path
from typing import Dict, List, Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape
from playwright.sync_api import sync_playwright


SLIDE_WIDTH = 1080
SLIDE_HEIGHT = 1350


def _word_count(text: str) -> int:
    return len([w for w in (text or "").split() if w.strip()])


def _validate_slide(slide: Dict) -> List[str]:
    warnings = []
    head_count = _word_count(slide.get("headline", ""))
    if slide.get("slide_number") == 1:
        if not (6 <= head_count <= 10):
            warnings.append(f"cover headline word count {head_count} outside 6-10")
    else:
        if head_count > 8:
            warnings.append(f"body headline word count {head_count} exceeds 8")
    sup_count = _word_count(slide.get("supporting_line", ""))
    if sup_count > 15:
        warnings.append(f"supporting line word count {sup_count} exceeds 15")
    return warnings


def _illustration_to_data_uri(illustration_path: Optional[str]) -> Optional[str]:
    if not illustration_path:
        return None
    p = Path(illustration_path)
    mime, _ = mimetypes.guess_type(p.name)
    if not mime:
        mime = "image/png"
    encoded = base64.b64encode(p.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def render_slide(brand: Dict, slide: Dict, illustration_path: Optional[str], out_path: str, plugin_root: str) -> Dict:
    warnings = _validate_slide(slide)
    env = Environment(
        loader=FileSystemLoader(Path(plugin_root) / "templates"),
        autoescape=select_autoescape(["html"]),
    )
    template = env.get_template("slide.html.j2")
    html = template.render(
        brand=brand,
        slide_number=slide.get("slide_number"),
        total_slides=slide.get("total_slides"),
        headline=slide.get("headline", ""),
        supporting_line=slide.get("supporting_line", ""),
        illustration_data_uri=_illustration_to_data_uri(illustration_path),
        alt_text=slide.get("alt_text", ""),
    )
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            page = browser.new_page(
                viewport={"width": SLIDE_WIDTH, "height": SLIDE_HEIGHT},
                device_scale_factor=1,
            )
            page.set_content(html, wait_until="networkidle")
            page.screenshot(path=str(out), type="png", full_page=False)
        finally:
            browser.close()
    return {"ok": True, "out_path": str(out), "warnings": warnings}


def main():
    if len(sys.argv) < 4:
        print(json.dumps({"ok": False, "error": "Usage: render_slide.py <brand.json> <slide.json> <out.png> [illustration.png] [plugin_root]"}))
        sys.exit(2)
    brand = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    slide = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    out_path = sys.argv[3]
    illust = sys.argv[4] if len(sys.argv) > 4 and sys.argv[4] != "-" else None
    plugin_root = sys.argv[5] if len(sys.argv) > 5 else str(Path(__file__).parent.parent)
    result = render_slide(brand, slide, illust, out_path, plugin_root)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
