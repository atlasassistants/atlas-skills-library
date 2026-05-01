"""LinkedIn search, profile crawl, and dossier assembly."""

import re
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote

from playwright.sync_api import TimeoutError as PWTimeout

from lib.browser import dismiss_cookie_banner
from lib.strip import strip_dossier_text


RATE_LIMIT_MARKERS = (
    "you've reached the weekly",
    "you've been viewing too many",
    "we've restricted",
    "unusual activity",
    "temporarily restricted",
)


def slugify(text: str) -> str:
    text = re.sub(r"[^\w\s-]", "", text).strip().lower()
    return re.sub(r"[\s_-]+", "-", text) or "result"


def is_logged_in(page) -> bool:
    """Returns True if LinkedIn shows a logged-in feed; False otherwise.

    Includes a brief retry to handle the transient false-negative observed when
    checking immediately after a fresh sign-in (page still rendering).
    """
    try:
        page.goto("https://www.linkedin.com/feed/",
                  wait_until="domcontentloaded", timeout=15000)
    except PWTimeout:
        return False

    # Quick check first — if it's clearly logged in or clearly not, return immediately
    if any(seg in page.url for seg in ("/login", "/checkpoint", "/authwall", "/uas/login")):
        return False

    # Give the page a brief moment to finish hydrating before the title check.
    # Without this, a fresh sign-in can leave page.title() as bare "LinkedIn" momentarily.
    page.wait_for_timeout(2000)

    if page.title().strip().lower() == "linkedin":
        # Try once more — might still be hydrating
        page.wait_for_timeout(2000)
        if page.title().strip().lower() == "linkedin":
            return False
    return True


def detect_block(page) -> str | None:
    """Returns 'rate_limited', 'not_logged_in', or None based on body text markers."""
    try:
        body = page.evaluate("() => (document.body.innerText || '').toLowerCase()")
    except Exception:
        return None
    if any(m in body for m in RATE_LIMIT_MARKERS):
        return "rate_limited"
    if "page not found" in body and "uh oh" in body:
        return "not_logged_in"
    return None


def get_main_text(page) -> str:
    """Get the rendered text of the <main> element. Falls back to body if no main."""
    text = page.evaluate("""() => {
        const main = document.querySelector('main');
        return (main || document.body).innerText || '';
    }""")
    text = re.sub(r"\n{3,}", "\n\n", text or "")
    return text.strip()


def get_search_candidates(page, name: str, company: str | None,
                          max_results: int = 10) -> list[dict[str, Any]]:
    """Search LinkedIn for `name` (+ optional `company`). Return up to `max_results` candidates."""
    query = f"{name} {company}" if company else name
    url = f"https://www.linkedin.com/search/results/people/?keywords={quote(query)}"

    try:
        page.goto(url, wait_until="domcontentloaded", timeout=20000)
    except PWTimeout:
        return []

    if detect_block(page) == "not_logged_in":
        return []

    try:
        page.wait_for_selector("main a[href*='/in/']", timeout=10000)
    except PWTimeout:
        return []

    page.wait_for_timeout(1500)

    candidates = page.evaluate(f"""() => {{
        const cards = [];
        const seen = new Set();
        const links = document.querySelectorAll('main a[href*="/in/"]');
        for (const a of links) {{
            const href = a.href.split('?')[0].split('#')[0];
            const m = href.match(/\\/in\\/([^/]+)\\/?$/);
            if (!m) continue;
            const slug = m[1];
            if (seen.has(slug)) continue;
            seen.add(slug);

            let el = a;
            for (let i = 0; i < 6; i++) {{
                if (!el.parentElement) break;
                el = el.parentElement;
                if ((el.innerText || '').trim().length > 60) break;
            }}
            const preview = (el.innerText || '').trim()
                .split('\\n')
                .map(s => s.trim())
                .filter(s => s && !/^\\d+(st|nd|rd|th)\\b/i.test(s))
                .slice(0, 4)
                .join(' • ')
                .slice(0, 250);

            cards.push({{ slug, url: 'https://www.linkedin.com/in/' + slug + '/', preview }});
            if (cards.length >= {max_results}) break;
        }}
        return cards;
    }}""")
    return candidates


def crawl_profile_subpages(page, profile_url: str) -> dict[str, str]:
    """Visit /in/<slug>/, /details/experience/, /details/education/, /recent-activity/all/.

    For each page: navigate, dismiss cookie banner, wait for render, scroll to load more
    (activity feed only), capture main text, strip via strip_dossier_text.

    Returns a dict keyed by section label. Special keys '__RATE_LIMITED__' or
    '__NOT_LOGGED_IN__' are set if a block is detected mid-crawl.
    """
    base = profile_url.rstrip("/").split("?")[0].split("#")[0]
    subpages = [
        ("Profile main", base + "/", 2500),
        ("Experience", base + "/details/experience/", 2500),
        ("Education", base + "/details/education/", 2500),
        ("Recent activity", base + "/recent-activity/all/", 4500),
    ]
    sections: dict[str, str] = {}
    for label, url, render_wait_ms in subpages:
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=20000)
        except PWTimeout:
            sections[label] = f"_(navigation timeout for {url})_"
            continue

        dismiss_cookie_banner(page)
        page.wait_for_timeout(render_wait_ms)

        # Scroll to trigger lazy-loading of below-fold sections (About text,
        # Experience details, posts further down the activity feed).
        try:
            for _ in range(3):
                page.evaluate("() => window.scrollBy(0, 1500)")
                page.wait_for_timeout(800)
            page.evaluate("() => window.scrollTo(0, 0)")
            page.wait_for_timeout(500)
        except Exception:
            pass

        # Click any visible "see more" / "...more" buttons to expand truncated
        # content (About paragraph, Experience descriptions, post bodies).
        # Inner try/except keeps non-clickable matches harmless.
        try:
            see_more_buttons = (page.get_by_text("…more", exact=False).all() +
                                page.get_by_text("see more", exact=False).all())
            for btn in see_more_buttons:
                try:
                    btn.click(timeout=1500)
                    page.wait_for_timeout(200)
                except Exception:
                    pass
        except Exception:
            pass

        block = detect_block(page)
        if block == "rate_limited":
            sections["__RATE_LIMITED__"] = "true"
            sections[label] = "_(rate limited — stopping)_"
            return sections
        if block == "not_logged_in":
            sections["__NOT_LOGGED_IN__"] = "true"
            sections[label] = "_(auth wall — session expired)_"
            return sections

        raw_text = get_main_text(page)
        sections[label] = strip_dossier_text(raw_text)
    return sections


def build_dossier(searched_name: str, company: str | None,
                  candidates: list[dict], selected_url: str | None,
                  sections: dict[str, str]) -> str:
    """Assemble the markdown dossier from the components."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    md: list[str] = [
        f"# LinkedIn Dossier: {searched_name}",
        "",
        f"**Searched:** {timestamp}  ",
    ]
    query_line = f"**Query:** `{searched_name}`"
    if company:
        query_line += f" + company `{company}`"
    md.append(query_line + "  ")
    if selected_url:
        md.append(f"**Selected profile:** {selected_url}")
    md.append("")
    md.append(f"## Search candidates ({len(candidates)} found)")
    md.append("")
    if not candidates:
        md.append("_No candidates returned by LinkedIn search._")
    else:
        for i, c in enumerate(candidates, 1):
            preview = c.get("preview") or c["slug"]
            md.append(f"{i}. [{preview}]({c['url']})")
    md.append("")

    if selected_url is None:
        return "\n".join(md)

    for label in ("Profile main", "Experience", "Education", "Recent activity"):
        md.append(f"## {label}")
        md.append("")
        md.append(sections.get(label, "_(not crawled)_"))
        md.append("")
    return "\n".join(md)
