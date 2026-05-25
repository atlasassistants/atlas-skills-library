#!/usr/bin/env python3
"""ONE-SHOT — regenerate the art-styles contact sheet shipped with the plugin.

This is NOT part of the runtime pipeline. Run manually when art-style prompt
templates change. Requires OPENAI_API_KEY in the environment.

Usage:
    OPENAI_API_KEY=sk-... python3 generate_contact_sheet_assets.py
    OPENAI_API_KEY=sk-... python3 generate_contact_sheet_assets.py --preset pastel-diagram-marker

When --preset is given, only that preset's sample.png is regenerated; the
contact sheet is then re-stitched from all seven samples currently on disk (so
the other six must already exist).
"""
import argparse
import base64
import os
from pathlib import Path

from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent / "assets" / "art-styles"
PRESETS = [
    "clean-saas",
    "editorial-magazine",
    "pastel-diagram-marker",
    "hand-drawn-marker",
    "documentary-noir",
    "midnight-editorial",
    "bold-flat-corporate",
]

# Per-preset sample scenarios. Each entry shows the style in its native habitat
# rather than forcing a generic Input/Process/Output framework. Presets without
# an entry fall back to GENERIC_SAMPLE until they are tuned.
PER_PRESET_SAMPLE = {
    "clean-saas": {
        "visual_intent": (
            "An isometric side-by-side comparison of two customer-acquisition "
            "funnels. Left panel: a stylized funnel labeled 'Channel A' with "
            "'12%' shown at the bottom in soft grayscale. Right panel: a "
            "stylized funnel labeled 'Channel B' with '38%' shown at the "
            "bottom, the percentage filled in the brand accent color. A small "
            "connector with 'vs' between the two panels. Soft shadows ground "
            "both panels against a clean off-white background. One stylized "
            "cursor hovers near the '38%' badge."
        ),
        "embedded_message": "3.2× conversion",
    },
    "editorial-magazine": {
        "visual_intent": (
            "A single white chess king tipped on its side on a polished dark "
            "wood board, lit from above with theatrical chiaroscuro. The board's "
            "edge runs through the lower third of the composition. Above the "
            "board, an editorial display headline. To the right of the king, a "
            "small italicized pull-quote in two lines. A thin horizontal rule "
            "in the brand accent color separates the headline from the image."
        ),
        "embedded_message": "The cost of being right too early",
    },
    "pastel-diagram-marker": {
        "visual_intent": (
            "A horizontal bar chart comparing five customer-acquisition channels "
            "by conversion rate. Five bars labeled top-to-bottom: 'Referrals', "
            "'Partner lenders', 'Website SEO', 'Google search ads', 'Portal "
            "leads'. The top bar is much longer than the bottom. A curved arrow "
            "between the top and bottom bars highlights the gap. Soft pastel "
            "palette with one bar in the brand accent color."
        ),
        "embedded_message": "25× gap",
    },
    "hand-drawn-marker": {
        "visual_intent": (
            "A loose hand-drawn marker scene: a small stick figure stands at a "
            "fork in the road, looking up at three signposts pointing in "
            "different directions. Each signpost is labeled with a short word "
            "('Safer', 'Faster', 'Right?'). Above the figure's head, a thought "
            "bubble. Scribbled lines of motion show the figure's confusion. The "
            "brand accent color is used to fill the third signpost only."
        ),
        "embedded_message": "the real question",
    },
    "documentary-noir": {
        "visual_intent": (
            "A hand holding a quarterly earnings report under a harsh single "
            "overhead light. A printed line chart inside the report shows a "
            "sharp decline; one data point is circled in red ink. A red stamp "
            "at the top of the page reads 'DOWN 23%'. Visible film grain, deep "
            "black background, the hand and paper are the only lit elements. "
            "Strong negative space; the subject occupies only a small portion "
            "of the frame."
        ),
        "embedded_message": "DOWN 23%",
    },
    "midnight-editorial": {
        "visual_intent": (
            "An editorial vector composition showing a three-step decision "
            "framework. Three rectangular cards arranged horizontally with "
            "thin connector arrows between them. Left card is labeled "
            "'FRAME' in sans-serif caps at the top with a small list-icon "
            "below the label. Middle card is a circular gateway labeled "
            "'SELECT' in sans-serif caps with a thin merge-arrow icon. "
            "Right card is labeled 'COMMIT' in sans-serif caps with a "
            "single bright status pill in the accent color below the label. "
            "Clean vector linework in muted steel-grey on a solid deep-navy "
            "background. The accent color appears as the status pill on the "
            "right card and a thin underline beneath the middle card's "
            "label. No gradient, no glow, no atmospheric effects — just "
            "clean shapes, three short labels, and confident composition. "
            "Subject takes about 70% of the frame width, centered "
            "horizontally."
        ),
        "embedded_message": "Decide once",
    },
    "bold-flat-corporate": {
        "visual_intent": (
            "A 2x2 strategic matrix with horizontal axis labeled 'Market growth "
            "(low to high)' and vertical axis labeled 'Differentiation (low to "
            "high)'. The four cells are clearly delineated with thin grey "
            "rules. The upper-right cell is filled in the brand accent color "
            "and contains a label; the other three cells contain shorter cell "
            "labels in neutral grey. A single large percentage callout sits to "
            "the right of the matrix. Pure flat-vector treatment on a clean "
            "off-white background."
        ),
        "embedded_message": "Strategic position",
    },
}

GENERIC_SAMPLE = {
    "visual_intent": (
        "Show three stacked rectangles forming a stylized framework. Labels: "
        "'Input', 'Process', 'Output'. Use the brand accent color as the focal "
        "contrast."
    ),
    "embedded_message": "Input · Process · Output",
}


# Per-preset sample colors. Most presets use white bg + cool-blue accent; dark
# presets need a dark bg to render correctly because their prompts say the
# background must be {background_color} exactly. Documentary-noir is the
# exception — its prompt overrides via "deep black background" in vocabulary —
# but we use a dark bg for it too so the sample matches its real use case.
SAMPLE_COLORS = {
    "midnight-editorial": {"background": "#0A0E1F", "accent": "#5EEAD4", "accent_name": "teal"},
    "documentary-noir": {"background": "#0D0D0F", "accent": "#FF5A5F", "accent_name": "red"},
}
DEFAULT_COLORS = {"background": "#FFFFFF", "accent": "#3B82F6", "accent_name": "blue"}


def build_prompt(preset: str) -> str:
    template = (ROOT / preset / "prompt-template.txt").read_text(encoding="utf-8")
    sample = PER_PRESET_SAMPLE.get(preset, GENERIC_SAMPLE)
    colors = SAMPLE_COLORS.get(preset, DEFAULT_COLORS)
    return (
        template
        .replace("{accent_color}", colors["accent"])
        .replace("{accent_name}", colors["accent_name"])
        .replace("{background_color}", colors["background"])
        .replace("{visual_intent}", sample["visual_intent"])
        .replace("{embedded_message}", sample["embedded_message"])
    )


def render_one(client, preset: str) -> Path:
    prompt = build_prompt(preset)
    out_path = ROOT / preset / "sample.png"
    # Keep model + size in sync with MODEL_SNAPSHOT / IMAGE_SIZE in
    # generate_illustration.py so contact-sheet samples match runtime output.
    resp = client.images.generate(
        model="gpt-image-2-2026-04-21",
        prompt=prompt,
        size="1024x1024",
    )
    out_path.write_bytes(base64.b64decode(resp.data[0].b64_json))
    return out_path


def compose_grid(out_path: Path):
    tile = 512
    cols = 3
    rows = (len(PRESETS) + cols - 1) // cols  # ceil division — 7 presets → 3 rows
    header_h = 50  # dedicated label zone above each tile so labels don't bleed into adjacent images
    grid_w = tile * cols
    grid_h = (tile + header_h) * rows
    sheet = Image.new("RGB", (grid_w, grid_h), "white")
    draw = ImageDraw.Draw(sheet)
    # Design-specimen caption: regular-weight sans, all-caps, muted color.
    font = None
    for font_name in ("Arial", "arial.ttf", "Helvetica", "DejaVuSans.ttf"):
        try:
            font = ImageFont.truetype(font_name, 20)
            break
        except Exception:
            continue
    if font is None:
        font = ImageFont.load_default()
    for i, preset in enumerate(PRESETS):
        sample_path = ROOT / preset / "sample.png"
        if not sample_path.exists():
            raise SystemExit(f"Missing sample for {preset}: {sample_path}")
        img = Image.open(sample_path).resize((tile, tile))
        col, row = i % cols, i // cols
        row_y = row * (tile + header_h)
        sheet.paste(img, (col * tile, row_y + header_h))
        draw.text((col * tile + 16, row_y + 18), preset.upper(), fill="#444444", font=font)
    sheet.save(out_path, "JPEG", quality=85)


def main():
    parser = argparse.ArgumentParser(
        description="Regenerate art-style contact sheet assets."
    )
    parser.add_argument(
        "--preset",
        choices=PRESETS,
        help="Regenerate only this preset's sample.png; the contact sheet is "
             "then re-stitched from all seven samples on disk.",
    )
    args = parser.parse_args()

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("OPENAI_API_KEY required.")
    client = OpenAI(api_key=api_key)

    targets = [args.preset] if args.preset else list(PRESETS)
    for preset in targets:
        path = render_one(client, preset)
        print(f"Rendered {preset} -> {path}")

    out = ROOT / "contact-sheet.jpg"
    compose_grid(out)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
