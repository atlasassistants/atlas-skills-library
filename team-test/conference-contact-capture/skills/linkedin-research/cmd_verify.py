"""Health check: config + Chrome + LinkedIn session."""

import json
import sys

from playwright.sync_api import sync_playwright

from lib.browser import is_debug_port_open, ensure_chrome_running
from lib.config import load_config
from lib.scrape import is_logged_in


def cmd_verify(args) -> int:
    cfg = load_config()
    if cfg is None:
        print(json.dumps({"ok": False, "reason": "no_config"}))
        return 10

    if not cfg.get("chrome_path"):
        print(json.dumps({"ok": False, "reason": "no_chrome_path"}))
        return 11

    # Chrome must be reachable. If not, launch it.
    try:
        ensure_chrome_running(
            chrome_path=cfg["chrome_path"],
            profile_dir=cfg["profile_dir"],
            port=cfg["debug_port"],
            visible=False,
        )
    except RuntimeError as e:
        print(json.dumps({"ok": False, "reason": "chrome_launch_failed", "detail": str(e)}))
        return 12

    if not is_debug_port_open(cfg["debug_port"]):
        print(json.dumps({"ok": False, "reason": "chrome_unreachable"}))
        return 13

    # Check LinkedIn session
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f"http://localhost:{cfg['debug_port']}", timeout=30000)
        if not browser.contexts:
            print(json.dumps({"ok": False, "reason": "no_browser_context"}))
            return 13
        ctx = browser.contexts[0]
        page = ctx.new_page()
        try:
            if not is_logged_in(page):
                print(json.dumps({"ok": False, "reason": "linkedin_signed_out"}))
                return 20
        finally:
            page.close()

    print(json.dumps({
        "ok": True,
        "chrome_ok": True,
        "linkedin_ok": True,
        "config_loaded_at": cfg.get("linkedin_verified_at"),
    }))
    return 0
