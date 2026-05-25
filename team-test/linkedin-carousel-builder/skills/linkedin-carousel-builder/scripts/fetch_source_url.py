#!/usr/bin/env python3
"""Fetch a URL and parse it into a brief structure."""
import json
import sys
from typing import Dict

import requests
from bs4 import BeautifulSoup


class FetchError(Exception):
    pass


def _fetch_html(url: str, timeout: int = 15) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; AtlasCarouselBuilder/0.1; +https://atlasassistants.com)"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
    except requests.exceptions.RequestException as exc:
        raise FetchError(str(exc)) from exc
    if resp.status_code != 200:
        raise FetchError(f"{resp.status_code} {resp.reason}")
    return resp.text


def _extract_text(html: str) -> Dict:
    soup = BeautifulSoup(html, "html.parser")
    title_tag = soup.find("h1") or soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else ""
    author_meta = soup.find("meta", attrs={"name": "author"})
    author = author_meta.get("content", "").strip() if author_meta else ""
    article = soup.find("article") or soup.find("main") or soup.body
    body = ""
    if article:
        paragraphs = [p.get_text(strip=True) for p in article.find_all(["p", "li"])]
        body = "\n\n".join(p for p in paragraphs if p)
    return {"title": title, "author": author, "body": body}


def fetch(url: str) -> Dict:
    try:
        html = _fetch_html(url)
    except FetchError as exc:
        return {"ok": False, "url": url, "error": str(exc)}
    parsed = _extract_text(html)
    if not parsed["body"].strip():
        return {"ok": False, "url": url, "error": "Body is empty after parsing (the page may be JS-rendered or content-blocked)."}
    return {"ok": True, "url": url, **parsed}


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"ok": False, "error": "Usage: fetch_source_url.py <url>"}))
        sys.exit(2)
    result = fetch(sys.argv[1])
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
