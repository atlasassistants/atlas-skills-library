"""Interactive onboarding wizard. Multi-stage protocol with the skill.

Usage patterns from the skill:
  python linkedin_scraper.py setup --stage detect
    -> prints JSON {chrome_path: "..." or null, output_dir_default: "..."}
       exit 0 if Chrome found, 11 if not (needs path from user)

  python linkedin_scraper.py setup --stage save-paths --chrome-path X --output-dir Y
    -> writes config; prints JSON {ok: true}; exit 0

  python linkedin_scraper.py setup --stage launch-for-login
    -> launches Chrome (visible) navigated to linkedin.com/login
       exit 0 once Chrome is up

  python linkedin_scraper.py setup --stage verify-login
    -> checks if LinkedIn is logged in; updates config if so
       exit 0 if verified, 20 if still signed out

  python linkedin_scraper.py setup --reauth-only
    -> skips path setup; runs launch-for-login (skill calls verify-login next)
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright

from lib.browser import ensure_chrome_running
from lib.config import (
    default_config, load_config, save_config,
    detect_chrome_path, get_profile_dir, get_default_output_dir,
)
from lib.scrape import is_logged_in


def cmd_setup(args) -> int:
    if args.reauth_only:
        return _do_launch_for_login(args)

    stage = getattr(args, "stage", None)

    if stage == "detect" or stage is None:
        return _do_detect(args)
    elif stage == "save-paths":
        return _do_save_paths(args)
    elif stage == "launch-for-login":
        return _do_launch_for_login(args)
    elif stage == "verify-login":
        return _do_verify_login(args)
    else:
        print(json.dumps({"ok": False, "reason": "unknown_stage"}), file=sys.stderr)
        return 1


def _do_detect(args) -> int:
    chrome = detect_chrome_path()
    out = {
        "chrome_path": str(chrome) if chrome else None,
        "output_dir_default": str(get_default_output_dir()),
        "profile_dir": str(get_profile_dir()),
        "platform": sys.platform,
    }
    print(json.dumps(out))
    return 0 if chrome else 11


def _do_save_paths(args) -> int:
    chrome_path = args.chrome_path
    output_dir = args.output_dir or str(get_default_output_dir())

    cfg = load_config() or default_config()
    cfg["chrome_path"] = chrome_path
    cfg["output_dir"] = output_dir
    cfg["profile_dir"] = str(get_profile_dir())
    cfg["platform"] = sys.platform

    Path(cfg["profile_dir"]).mkdir(parents=True, exist_ok=True)
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    save_config(cfg)
    print(json.dumps({"ok": True, "chrome_path": chrome_path, "output_dir": output_dir}))
    return 0


def _do_launch_for_login(args) -> int:
    cfg = load_config()
    if cfg is None or not cfg.get("chrome_path"):
        print(json.dumps({"ok": False, "reason": "no_config"}), file=sys.stderr)
        return 10

    try:
        # Visible launch — user needs to see it for sign-in
        ensure_chrome_running(
            chrome_path=cfg["chrome_path"],
            profile_dir=cfg["profile_dir"],
            port=cfg["debug_port"],
            visible=True,
        )
    except RuntimeError as e:
        print(json.dumps({"ok": False, "reason": "chrome_launch_failed", "detail": str(e)}),
              file=sys.stderr)
        return 12

    # Navigate to LinkedIn login on a new page
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f"http://localhost:{cfg['debug_port']}", timeout=30000)
        ctx = browser.contexts[0]
        page = ctx.new_page()
        try:
            page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded", timeout=15000)
        except Exception:
            pass  # don't fail if navigation is slow — Chrome window is up, that's enough
        # Don't close the page — leave it open for the user to sign in

    print(json.dumps({"ok": True, "message": "chrome_open_at_login_page"}))
    return 0


def _do_verify_login(args) -> int:
    cfg = load_config()
    if cfg is None:
        print(json.dumps({"ok": False, "reason": "no_config"}), file=sys.stderr)
        return 10

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f"http://localhost:{cfg['debug_port']}", timeout=30000)
        if not browser.contexts:
            print(json.dumps({"ok": False, "reason": "no_browser_context"}), file=sys.stderr)
            return 13
        ctx = browser.contexts[0]
        page = ctx.new_page()
        try:
            if is_logged_in(page):
                cfg["linkedin_verified_at"] = datetime.now(timezone.utc).isoformat()
                save_config(cfg)
                print(json.dumps({"ok": True, "verified_at": cfg["linkedin_verified_at"]}))
                return 0
            else:
                print(json.dumps({"ok": False, "reason": "still_signed_out"}), file=sys.stderr)
                return 20
        finally:
            page.close()
