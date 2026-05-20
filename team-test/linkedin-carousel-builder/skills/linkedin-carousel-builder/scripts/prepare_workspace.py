#!/usr/bin/env python3
"""Scaffold the linkedin-carousel-builder workspace at <user CWD>."""
import json
import sys
from pathlib import Path

DEFAULT_CONFIG = {
    "companion_post_default": "yes",
    "last_used_brand": None,
    "default_art_style": "clean-saas",
    "openai_image_model_snapshot": "gpt-image-2-2026-04-21",
}


def prepare(workspace: Path) -> dict:
    workspace.mkdir(parents=True, exist_ok=True)
    plugin_dir = workspace / "linkedin-carousel-builder"
    (plugin_dir / "brands").mkdir(parents=True, exist_ok=True)
    (plugin_dir / "runs").mkdir(parents=True, exist_ok=True)

    config_path = workspace / "linkedin-carousel-builder.config.json"
    if not config_path.exists():
        config_path.write_text(json.dumps(DEFAULT_CONFIG, indent=2) + "\n")

    return {
        "ok": True,
        "workspace_root": str(workspace),
        "plugin_dir": str(plugin_dir),
        "config_path": str(config_path),
    }


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"ok": False, "error": "Usage: prepare_workspace.py <workspace-path>"}))
        sys.exit(2)
    workspace = Path(sys.argv[1]).resolve()
    try:
        result = prepare(workspace)
        print(json.dumps(result, indent=2))
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
