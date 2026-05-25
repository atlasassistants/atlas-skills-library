#!/usr/bin/env python3
"""Parse a design system file (W3C tokens JSON), folder (colors.json / typography.json / etc.),
or brand guidelines PDF into a brand-identity payload."""
import json
import re
import sys
from pathlib import Path
from typing import Dict, Optional

HEX_COLOR = re.compile(r"#[0-9A-Fa-f]{6}\b")
FONT_KEYWORD = re.compile(r"\b(font|typeface|family)[:\s]+([A-Z][A-Za-z\s]+)", re.IGNORECASE)
NAMED_COLOR_ROLES = ("background", "headline", "body", "accent", "primary")


def _parse_w3c_tokens(path: Path) -> Dict:
    data = json.loads(path.read_text())
    color = data.get("color", {})
    typography = data.get("typography", {})
    colors = {role: color[role]["$value"] for role in NAMED_COLOR_ROLES if role in color}
    fonts = {role: typography[role]["$value"] for role in ("headline", "body") if role in typography}
    if not colors or not fonts:
        return {"ok": False, "error": "W3C tokens file is missing required color or typography roles."}
    return {"ok": True, "colors": colors, "fonts": fonts}


def _parse_folder(path: Path) -> Dict:
    colors_path = path / "colors.json"
    typography_path = path / "typography.json"
    if not colors_path.exists() or not typography_path.exists():
        return {"ok": False, "error": "Design folder must contain colors.json and typography.json."}
    colors = json.loads(colors_path.read_text())
    fonts = json.loads(typography_path.read_text())
    missing_colors = {"background", "headline", "body", "accent"} - set(colors.keys())
    if missing_colors:
        return {"ok": False, "error": (
            f"{colors_path} must contain these role keys: background, headline, body, accent. "
            f"Missing: {sorted(missing_colors)}. Found: {sorted(colors.keys())}. "
            "If your brand source uses different naming (e.g., 'primary'/'secondary') or doesn't have all four roles, "
            "try a different brand-creation path: paste 1–3 brand screenshots, or point the skill at the folder/repo "
            "as a host-LLM extraction source (path 6 in the brand-creation menu)."
        )}
    missing_fonts = {"headline", "body"} - set(fonts.keys())
    if missing_fonts:
        return {"ok": False, "error": (
            f"{typography_path} must contain these role keys: headline, body. "
            f"Missing: {sorted(missing_fonts)}. Found: {sorted(fonts.keys())}. "
            "If your brand uses a single font for both, repeat its name under both 'headline' and 'body'. "
            "Or try a different brand-creation path (screenshots, or host-LLM folder/repo extraction)."
        )}
    # Optional style-guide.md surfaces as raw_notes
    style_guide = path / "style-guide.md"
    raw_notes = style_guide.read_text() if style_guide.exists() else ""
    # Naive hard-ban extraction: lines starting with "no " or containing "no <thing>"
    hard_bans = []
    for line in raw_notes.splitlines():
        m = re.search(r"\bno ([\w\s]+?)(?:[.,]|$)", line, re.IGNORECASE)
        if m:
            hard_bans.append(m.group(1).strip())
    return {"ok": True, "colors": colors, "fonts": fonts, "raw_notes": raw_notes, "hard_bans": hard_bans}


def _parse_pdf(path: Path) -> Dict:
    from pypdf import PdfReader
    reader = PdfReader(str(path))
    text = "\n".join((page.extract_text() or "") for page in reader.pages)
    hex_colors = list(dict.fromkeys(HEX_COLOR.findall(text)))
    fonts_found = {}
    for line in text.splitlines():
        if "headline font" in line.lower():
            m = re.search(r"headline font[:\s]+([A-Z][A-Za-z]+)", line, re.IGNORECASE)
            if m:
                fonts_found["headline"] = m.group(1)
        if "body font" in line.lower():
            m = re.search(r"body font[:\s]+([A-Z][A-Za-z]+)", line, re.IGNORECASE)
            if m:
                fonts_found["body"] = m.group(1)
    if not hex_colors or not fonts_found:
        return {"ok": False, "error": "PDF parsed but no clear colors or fonts found."}
    # Map hex_colors to roles by position (background first if light/white, accent next as most-saturated)
    colors = {
        "background": hex_colors[-1] if hex_colors[-1].upper() in ("#FFFFFF", "#FFF") else hex_colors[0],
        "headline": "#000000",
        "body": "#222222",
        "accent": hex_colors[0],
    }
    return {"ok": True, "colors": colors, "fonts": fonts_found}


def parse(path_str: str) -> Dict:
    path = Path(path_str)
    if not path.exists():
        return {"ok": False, "error": f"Path does not exist: {path}"}
    if path.is_dir():
        return _parse_folder(path)
    if path.suffix.lower() == ".json":
        return _parse_w3c_tokens(path)
    if path.suffix.lower() == ".pdf":
        return _parse_pdf(path)
    return {"ok": False, "error": f"Unsupported design-system input format: {path.suffix}. Use a .json file (W3C tokens), a folder with colors.json + typography.json, or a .pdf."}


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"ok": False, "error": "Usage: parse_design_system.py <path>"}))
        sys.exit(2)
    print(json.dumps(parse(sys.argv[1]), indent=2))


if __name__ == "__main__":
    main()
