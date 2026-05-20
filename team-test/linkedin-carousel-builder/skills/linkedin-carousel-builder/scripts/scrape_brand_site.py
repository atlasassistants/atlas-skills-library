#!/usr/bin/env python3
"""Scrape a brand site for dominant colors and fonts. Reports confidence."""
import json
import re
import sys
from typing import Dict, List

import requests
from bs4 import BeautifulSoup


class ScrapeError(Exception):
    pass


HEX_COLOR = re.compile(r"#[0-9A-Fa-f]{6}\b")
FONT_FAMILY = re.compile(r"font-family\s*:\s*['\"]?([^,;'\"]+)", re.IGNORECASE)
GRAYSCALE = {"#FFFFFF", "#000000", "#FFF", "#000"}


def _fetch_html(url: str) -> str:
    headers = {"User-Agent": "Mozilla/5.0 (compatible; AtlasCarouselBuilder/0.1)"}
    try:
        resp = requests.get(url, headers=headers, timeout=15)
    except requests.exceptions.RequestException as exc:
        raise ScrapeError(str(exc)) from exc
    if resp.status_code != 200:
        raise ScrapeError(f"{resp.status_code} {resp.reason}")
    return resp.text


def _extract_signals(html: str) -> Dict[str, List[str]]:
    soup = BeautifulSoup(html, "html.parser")
    style_text = " ".join(s.get_text() for s in soup.find_all("style"))
    inline_styles = " ".join(t.get("style", "") for t in soup.find_all(style=True))
    combined = style_text + " " + inline_styles
    colors = list(dict.fromkeys(HEX_COLOR.findall(combined)))
    fonts = list(dict.fromkeys(m.strip() for m in FONT_FAMILY.findall(combined)))
    return {"colors": colors, "fonts": fonts}


def _assess_confidence(signals: Dict[str, List[str]]) -> str:
    colors = signals["colors"]
    fonts = signals["fonts"]
    non_grayscale = [c for c in colors if c.upper() not in GRAYSCALE]
    if not non_grayscale or not fonts:
        return "low"
    if len(non_grayscale) < 2:
        return "low"
    return "high"


def scrape(url: str) -> Dict:
    try:
        html = _fetch_html(url)
    except ScrapeError as exc:
        return {"ok": False, "error": str(exc), "confidence": "fetch_failed"}
    signals = _extract_signals(html)
    confidence = _assess_confidence(signals)
    if confidence == "low":
        return {
            "ok": False,
            "confidence": "low",
            "colors": signals["colors"],
            "fonts": signals["fonts"],
            "error": "Too few colors / fonts detected to build a brand reliably.",
        }
    return {
        "ok": True,
        "confidence": confidence,
        "colors": signals["colors"],
        "fonts": signals["fonts"],
        "url": url,
    }


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"ok": False, "error": "Usage: scrape_brand_site.py <url>"}))
        sys.exit(2)
    print(json.dumps(scrape(sys.argv[1]), indent=2))


if __name__ == "__main__":
    main()
