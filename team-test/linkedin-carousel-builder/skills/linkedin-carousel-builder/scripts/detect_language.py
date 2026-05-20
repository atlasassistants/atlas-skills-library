#!/usr/bin/env python3
"""Detect source language and gate against non-Latin-script content (v1)."""
import json
import sys
from typing import Dict

from langdetect import detect as _langdetect_detect, DetectorFactory, LangDetectException
DetectorFactory.seed = 42  # deterministic

LATIN_SCRIPT_SUPPORTED = {"en", "es", "fr", "de", "pt", "it", "nl"}


def detect_language(text: str) -> Dict:
    sample = text[:2000].strip()
    if not sample:
        return {"status": "block", "language": None, "error": "Empty source body — nothing to detect."}
    try:
        lang = _langdetect_detect(sample)
    except LangDetectException as exc:
        return {"status": "block", "language": None, "error": f"Language detection failed: {exc}"}
    if lang == "en":
        return {"status": "proceed", "language": lang}
    if lang in LATIN_SCRIPT_SUPPORTED:
        return {
            "status": "proceed_with_warning",
            "language": lang,
            "warning": (
                f"Source detected as {lang}. The methodology rules (e.g., 6–10 word cover headline, "
                f"100–150 char per slide) are tuned for English. They generally transfer to other "
                f"Latin-script languages but may need light manual editing in compound-heavy "
                f"languages like German. Proceeding."
            ),
        }
    return {
        "status": "block",
        "language": lang,
        "error": (
            f"Source detected as {lang}. v1 supports English plus other Latin-script languages "
            f"(Spanish, French, German, Portuguese, Italian, Dutch). Non-Latin scripts need typography "
            f"and layout work scheduled for v2. Cancel this run or provide a Latin-script source."
        ),
    }


# Alias for test import convenience
detect = detect_language


def main():
    if len(sys.argv) < 2:
        text = sys.stdin.read()
    else:
        text = sys.argv[1]
    print(json.dumps(detect_language(text), indent=2))


if __name__ == "__main__":
    main()
