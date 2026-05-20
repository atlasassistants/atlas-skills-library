#!/usr/bin/env python3
"""Generate a single slide illustration via gpt-image-2."""
import base64
import json
import sys
from pathlib import Path
from typing import Dict

# If you bump these, also update the duplicated values in
# generate_contact_sheet_assets.py (model + size at the images.generate call)
# so regenerated contact-sheet samples match runtime output.
MODEL_SNAPSHOT = "gpt-image-2-2026-04-21"
IMAGE_SIZE = "1024x1024"


class IllustrationError(Exception):
    pass


def _load_art_style_prompt(brand: Dict, plugin_root: Path) -> str:
    art_style = brand.get("art_style", "clean-saas")
    custom = brand.get("art_style_prompt")
    if custom:
        return custom
    template_path = plugin_root / "assets" / "art-styles" / art_style / "prompt-template.txt"
    if not template_path.exists():
        raise IllustrationError(f"Art style not found: {art_style}")
    return template_path.read_text(encoding="utf-8")


def _build_prompt(brand: Dict, visual_intent: str, embedded_message: str, plugin_root: Path) -> str:
    template = _load_art_style_prompt(brand, plugin_root)
    try:
        accent = brand["colors"]["accent"]
        background = brand["colors"]["background"]
    except (KeyError, TypeError) as exc:
        raise IllustrationError(
            f"Brand profile is missing required color key {exc}. "
            "Re-run brand creation, or run brand_profile_schema.py against the brand "
            "JSON to see all schema errors at once."
        ) from exc
    return (
        template
        .replace("{accent_color}", accent)
        .replace("{background_color}", background)
        .replace("{accent_name}", brand.get("accent_name") or "the brand accent")
        .replace("{visual_intent}", visual_intent)
        .replace("{embedded_message}", embedded_message or "")
    )


def _call_openai(api_key: str, prompt: str) -> bytes:
    try:
        from openai import OpenAI, APIError
    except ImportError as exc:
        raise IllustrationError(f"openai SDK not installed: {exc}")
    client = OpenAI(api_key=api_key)
    try:
        resp = client.images.generate(
            model=MODEL_SNAPSHOT, prompt=prompt, size=IMAGE_SIZE,
        )
    except APIError as exc:
        raise IllustrationError(f"OpenAI image API error: {exc}") from exc
    if not resp.data:
        raise IllustrationError("OpenAI returned no image data.")
    return base64.b64decode(resp.data[0].b64_json)


def generate(api_key: str, brand: Dict, visual_intent: str, embedded_message: str, out_path: str, plugin_root: str) -> Dict:
    # Defensive contract: when visual_intent is non-empty, embedded_message must
    # be non-empty too. If embedded_message is empty, the art-style prompt
    # template still asks the model for an in-image annotation, and the model
    # substitutes literal text from the visual_intent as that annotation.
    # Result is metadata-as-art, never editorial.
    if (visual_intent or "").strip() and not (embedded_message or "").strip():
        return {
            "ok": False,
            "error": (
                "embedded_message is required when visual_intent is non-empty. "
                "Empty embedded_message causes the model to render literal visual_intent "
                "text as the in-image annotation. Either provide an embedded_message "
                "(1-5 short labels, <=30 chars) or pass an empty visual_intent for a "
                "typography-only slide."
            ),
        }
    try:
        prompt = _build_prompt(brand, visual_intent, embedded_message, Path(plugin_root))
        image_bytes = _call_openai(api_key=api_key, prompt=prompt)
    except IllustrationError as exc:
        return {"ok": False, "error": str(exc)}
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(image_bytes)
    return {"ok": True, "out_path": str(out), "model": MODEL_SNAPSHOT}


def main():
    if len(sys.argv) < 6:
        print(json.dumps({
            "ok": False,
            "error": "Usage: generate_illustration.py <api_key> <brand_json_path> <visual_intent> <embedded_message> <out_png_path> [plugin_root]",
        }))
        sys.exit(2)
    api_key, brand_path, intent, embedded_message, out_path = sys.argv[1:6]
    plugin_root = sys.argv[6] if len(sys.argv) > 6 else str(Path(__file__).parent.parent)
    brand = json.loads(Path(brand_path).read_text(encoding="utf-8"))
    result = generate(
        api_key=api_key,
        brand=brand,
        visual_intent=intent,
        embedded_message=embedded_message,
        out_path=out_path,
        plugin_root=plugin_root,
    )
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
