"""Config loading, saving, and platform-aware Chrome detection."""

import json
import sys
from pathlib import Path
from typing import Any


def get_config_path() -> Path:
    """Path to the user's config file in their home directory."""
    return Path.home() / ".linkedin-scraper-config.json"


def get_profile_dir() -> Path:
    """Default Chrome user-data-dir for the scraper profile."""
    return Path.home() / ".linkedin-scraper-profile"


def get_default_output_dir() -> Path:
    """Default folder for saved dossier files."""
    return Path.home() / "Documents" / "linkedin-research"


def default_config() -> dict[str, Any]:
    return {
        "version": 1,
        "platform": sys.platform,
        "chrome_path": None,
        "profile_dir": str(get_profile_dir()),
        "debug_port": 9222,
        "output_dir": str(get_default_output_dir()),
        "linkedin_verified_at": None,
        "pacing": {
            "min_interval_seconds": 45,
            "interval_jitter_seconds": 15,
            "daily_cap": 25,
            "burst_cap": 8,
            "burst_window_minutes": 30,
            "burst_slow_interval_seconds": 90,
            "burst_slow_duration_minutes": 30,
        },
        "scrape_history": [],
    }


def load_config(path: Path | None = None) -> dict[str, Any] | None:
    p = path or get_config_path()
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"Config file at {p} is corrupted: {e}. "
            f"Re-run `python linkedin_scraper.py setup` to regenerate."
        ) from e


def save_config(cfg: dict[str, Any], path: Path | None = None) -> None:
    p = path or get_config_path()
    p.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")


def detect_chrome_path() -> Path | None:
    """Try known Chrome install paths for the current OS. Return first that exists."""
    candidates: list[Path] = []
    if sys.platform == "win32":
        candidates = [
            Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
            Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
            Path.home() / "AppData" / "Local" / "Google" / "Chrome" / "Application" / "chrome.exe",
        ]
    elif sys.platform == "darwin":
        candidates = [
            Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
            Path.home() / "Applications" / "Google Chrome.app" / "Contents" / "MacOS" / "Google Chrome",
        ]
    else:
        return None  # Linux not in v1 scope

    for c in candidates:
        if c.exists():
            return c
    return None
