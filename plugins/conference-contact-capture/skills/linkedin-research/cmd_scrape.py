"""Scrape subcommand: search, crawl, save dossier."""

import json
import sys
import time
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright

from lib.browser import is_debug_port_open, ensure_chrome_running
from lib.config import load_config, save_config
from lib.pacing import (
    is_daily_cap_exceeded, seconds_until_next_scrape_allowed,
    append_history,
)
from lib.scrape import (
    is_logged_in, get_search_candidates,
    crawl_profile_subpages, build_dossier, slugify,
)
from lib.strip import strip_dossier_text


def cmd_scrape(args) -> int:
    cfg = load_config()
    if cfg is None:
        print(json.dumps({"ok": False, "reason": "no_config"}), file=sys.stderr)
        return 10
    if not cfg.get("chrome_path"):
        print(json.dumps({"ok": False, "reason": "no_chrome_path"}), file=sys.stderr)
        return 11

    pacing = cfg["pacing"]
    history = cfg.get("scrape_history", [])

    if is_daily_cap_exceeded(history, pacing["daily_cap"]):
        print(json.dumps({
            "ok": False, "reason": "daily_cap_exceeded",
            "cap": pacing["daily_cap"],
        }), file=sys.stderr)
        return 31

    wait = seconds_until_next_scrape_allowed(history, pacing)
    if wait > 0:
        print(json.dumps({"info": "pacing_wait", "seconds": round(wait, 1)}),
              file=sys.stderr)
        time.sleep(wait)

    try:
        ensure_chrome_running(
            chrome_path=cfg["chrome_path"],
            profile_dir=cfg["profile_dir"],
            port=cfg["debug_port"],
            visible=False,
        )
    except RuntimeError as e:
        print(json.dumps({"ok": False, "reason": "chrome_launch_failed", "detail": str(e)}),
              file=sys.stderr)
        return 12

    if not is_debug_port_open(cfg["debug_port"]):
        print(json.dumps({"ok": False, "reason": "chrome_unreachable"}), file=sys.stderr)
        return 13

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f"http://localhost:{cfg['debug_port']}", timeout=30000)
        if not browser.contexts:
            print(json.dumps({"ok": False, "reason": "no_browser_context"}), file=sys.stderr)
            return 13
        ctx = browser.contexts[0]
        page = ctx.new_page()
        try:
            if not is_logged_in(page):
                print(json.dumps({"ok": False, "reason": "linkedin_signed_out"}), file=sys.stderr)
                return 20

            candidates = get_search_candidates(page, args.name, args.company)
            if not candidates:
                dossier = build_dossier(args.name, args.company, [], None, {})
                ok = True
                profile_url = None
                sections = {}
            else:
                chosen = candidates[0]
                profile_url = chosen["url"]
                sections = crawl_profile_subpages(page, profile_url)

                if sections.get("__RATE_LIMITED__") == "true":
                    cfg["scrape_history"] = append_history(history, args.name, ok=False)
                    save_config(cfg)
                    print(json.dumps({"ok": False, "reason": "rate_limited"}), file=sys.stderr)
                    return 30
                if sections.get("__NOT_LOGGED_IN__") == "true":
                    print(json.dumps({"ok": False, "reason": "linkedin_signed_out"}), file=sys.stderr)
                    return 20
                sections.pop("__RATE_LIMITED__", None)
                sections.pop("__NOT_LOGGED_IN__", None)
                dossier = build_dossier(args.name, args.company, candidates, profile_url, sections)
                dossier = strip_dossier_text(dossier)  # second pass for section-aware rules
                ok = True
        finally:
            page.close()

    output_dir = Path(cfg["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d-%H%M")
    slug = slugify(args.name)
    out_path = output_dir / f"{slug}-{timestamp}-raw.md"
    out_path.write_text(dossier, encoding="utf-8")

    cfg["scrape_history"] = append_history(history, args.name, ok=ok)
    save_config(cfg)

    result = {
        "ok": True,
        "raw_dossier_path": str(out_path),
        "char_count": len(dossier),
        "profile_url": profile_url,
        "candidates_count": len(candidates),
        "name": args.name,
    }
    print(json.dumps(result))
    return 0
