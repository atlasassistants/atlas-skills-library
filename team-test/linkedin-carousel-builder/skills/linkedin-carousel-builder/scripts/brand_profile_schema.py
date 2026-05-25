#!/usr/bin/env python3
"""Brand profile JSON schema + validator."""
import json
import re
import sys
from typing import Dict, List, Tuple

BUILTIN_ART_STYLES = {
    "clean-saas",
    "editorial-magazine",
    "pastel-diagram-marker",
    "hand-drawn-marker",
    "documentary-noir",
    "midnight-editorial",
    "bold-flat-corporate",
}

REQUIRED_FIELDS = {
    "brand_slug": str,
    "display_name": str,
    "audience": str,
    "voice": str,
    "colors": dict,
    "fonts": dict,
    "art_style": str,
    "footer_handle": str,
    "brand_mark": str,
    "hard_bans": list,
    "created_at": str,
    "last_used": str,
}

OPTIONAL_FIELDS = {
    "accent_name": str,
    "background_name": str,
    "headline_name": str,
    "body_name": str,
    "footer_brand_mark": str,
}

REQUIRED_COLORS = {"background", "headline", "body", "accent"}
REQUIRED_FONTS = {"headline", "body"}

HEX_COLOR = re.compile(r"^#[0-9A-Fa-f]{6}$")


def validate(profile: Dict) -> Tuple[bool, List[str]]:
    errors: List[str] = []
    # Backward-compat shim: if a legacy brand profile uses footer_brand_mark but
    # not the renamed brand_mark, treat it as brand_mark for this release.
    if "brand_mark" not in profile and "footer_brand_mark" in profile:
        profile = {**profile, "brand_mark": profile["footer_brand_mark"]}
    for field, expected_type in REQUIRED_FIELDS.items():
        if field not in profile:
            errors.append(f"missing required field: {field}")
            continue
        if not isinstance(profile[field], expected_type):
            errors.append(f"field {field}: expected {expected_type.__name__}, got {type(profile[field]).__name__}")

    for field, expected_type in OPTIONAL_FIELDS.items():
        if field in profile and not isinstance(profile[field], expected_type):
            errors.append(f"field {field}: expected {expected_type.__name__}, got {type(profile[field]).__name__}")

    colors = profile.get("colors", {})
    if isinstance(colors, dict):
        for key in REQUIRED_COLORS:
            if key not in colors:
                errors.append(f"missing color: {key}")
            elif not HEX_COLOR.match(str(colors[key])):
                errors.append(f"invalid hex color for {key}: {colors[key]!r}")

    fonts = profile.get("fonts", {})
    if isinstance(fonts, dict):
        for key in REQUIRED_FONTS:
            if key not in fonts or not str(fonts[key]).strip():
                errors.append(f"missing or empty font: {key}")

    art_style = profile.get("art_style")
    if art_style and art_style not in BUILTIN_ART_STYLES:
        if "art_style_prompt" not in profile or not str(profile["art_style_prompt"]).strip():
            errors.append(
                f"art_style {art_style!r} is not a built-in preset and no art_style_prompt provided."
            )

    return (len(errors) == 0, errors)


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"ok": False, "error": "Usage: brand_profile_schema.py <path-to-brand.json>"}))
        sys.exit(2)
    with open(sys.argv[1], encoding='utf-8-sig') as f:
        profile = json.loads(f.read())
    ok, errs = validate(profile)
    print(json.dumps({"ok": ok, "errors": errs}, indent=2))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
