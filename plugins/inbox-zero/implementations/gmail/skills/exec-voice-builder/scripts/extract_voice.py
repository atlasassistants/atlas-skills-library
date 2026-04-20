"""
Extract Voice
=============
Fetches the last N messages from the exec's Gmail Sent folder and returns
them as cleaned JSON so the agent can extract writing patterns.

Responsibilities of THIS script (mechanical layer):
    - Fetch N messages from the Sent folder (via client.get_sent_messages)
    - Strip quoted replies, forwarded blocks, signatures, and auto-reply
      boilerplate from each body
    - Emit JSON with one record per message

Responsibilities of the AGENT:
    - Reading the JSON and extracting tone, openings, closings, signature
      phrases, situational patterns, and anti-patterns
    - Writing the resulting profile to client-profile/exec-voice-guide.md
      in the format defined in references/voice-guide-template.md

Subcommands:

    fetch   Pull N sent messages and return cleaned JSON. Default.

Flags:

    --count N            Number of sent messages to fetch (default 30)
    --include-raw        Also include body_full (raw plain text) alongside
                         the cleaned body_plain, for the agent to compare

Usage:

    python extract_voice.py fetch --count 30
    python extract_voice.py fetch --count 20 --include-raw

Exit codes:
    0 — success (possibly with count_available < count_requested)
    1 — auth or fatal failure
    2 — fewer than 3 sent messages available (not usable at all)
"""

import argparse
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_IMPL_SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"
_SHARED_SCRIPTS = Path(__file__).resolve().parents[5] / "shared" / "scripts"
for _p in (_IMPL_SCRIPTS, _SHARED_SCRIPTS):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from gmail_client import GmailClient


# ─────────────────────────────────────────────
# BODY CLEANING
# ─────────────────────────────────────────────

# Markers that start a quoted or forwarded block. Everything from the marker
# onward (including the marker line) is removed.
QUOTE_BLOCK_MARKERS: list[re.Pattern] = [
    # "On Mon, Apr 10, 2026 at 3:42 PM, Name <email> wrote:"
    re.compile(r"^On\s+.+?wrote:\s*$", re.MULTILINE | re.IGNORECASE),
    # "On [date] [person] wrote:" variant without comma
    re.compile(r"^On\s+.+?,.+?wrote:\s*$", re.MULTILINE | re.IGNORECASE),
    # Gmail mobile: "On [day], [date] [person] <email> wrote:"
    re.compile(r"^On\s+\w+,\s+\w+\s+\d+,\s+\d{4}.+?wrote:\s*$", re.MULTILINE | re.IGNORECASE),
    # Outlook-style forwarded marker
    re.compile(r"^-{2,}\s*Forwarded message\s*-{2,}\s*$", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^-{2,}\s*Original Message\s*-{2,}\s*$", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^Begin forwarded message:\s*$", re.MULTILINE | re.IGNORECASE),
    # Outlook reply marker: "From: ..." on its own line followed by Sent/To/Subject
    re.compile(
        r"^From:\s.+?\n(?:Sent|Date):\s.+?\nTo:\s.+?\nSubject:\s.+?$",
        re.MULTILINE | re.IGNORECASE | re.DOTALL,
    ),
]

# Signature separators — everything after the first one is dropped
SIGNATURE_MARKERS: list[re.Pattern] = [
    re.compile(r"^--\s*$", re.MULTILINE),  # Standard sig delimiter
    re.compile(r"^__+\s*$", re.MULTILINE),  # Underscore divider
    re.compile(r"^Sent from my iPhone\s*$", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^Sent from my iPad\s*$", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^Sent from my Android\s*$", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^Sent from my (Galaxy|Pixel|BlackBerry).*$", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^Get Outlook for iOS\s*$", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^Get Outlook for Android\s*$", re.MULTILINE | re.IGNORECASE),
]

# Lines starting with ">" are quoted — strip them
QUOTED_LINE_REGEX = re.compile(r"^>.*$", re.MULTILINE)

# Runs of blank lines
BLANK_LINE_RUN = re.compile(r"\n{3,}")


def clean_body(raw_body: str) -> str:
    """
    Remove quoted content, forwarded blocks, signatures, and common auto-reply
    boilerplate from a sent-message body. Returns the cleaned plain-text.

    The goal is to isolate the actual outgoing text the exec wrote, which is
    what we analyze for tone and phrasing.
    """
    if not raw_body:
        return ""

    text = raw_body.replace("\r\n", "\n").replace("\r", "\n")

    # 1. Cut at first quote-block marker
    earliest_cut = len(text)
    for pattern in QUOTE_BLOCK_MARKERS:
        match = pattern.search(text)
        if match and match.start() < earliest_cut:
            earliest_cut = match.start()
    text = text[:earliest_cut]

    # 2. Cut at first signature marker
    earliest_sig = len(text)
    for pattern in SIGNATURE_MARKERS:
        match = pattern.search(text)
        if match and match.start() < earliest_sig:
            earliest_sig = match.start()
    text = text[:earliest_sig]

    # 3. Strip individual quoted lines (just in case)
    text = QUOTED_LINE_REGEX.sub("", text)

    # 4. Collapse runs of blank lines
    text = BLANK_LINE_RUN.sub("\n\n", text)

    return text.strip()


# ─────────────────────────────────────────────
# FETCH
# ─────────────────────────────────────────────

def fetch_sent(
    client: GmailClient,
    count: int,
    include_raw: bool,
) -> dict[str, Any]:
    """
    Fetch up to `count` sent messages and return a JSON-friendly dict.
    """
    print(f"Fetching up to {count} sent messages...", file=sys.stderr)

    try:
        messages = client.get_sent_messages(max_results=count)
    except Exception as exc:  # noqa: BLE001
        return {"error": f"fetch failed: {exc}"}

    records: list[dict[str, Any]] = []
    for msg in messages:
        try:
            headers = client.get_message_headers(msg)
            raw_body = client.get_message_body(msg) or ""
            cleaned = clean_body(raw_body)

            record = {
                "id": msg.get("id"),
                "thread_id": msg.get("threadId"),
                "date": headers.get("date", ""),
                "to": headers.get("to", ""),
                "cc": headers.get("cc", ""),
                "subject": headers.get("subject", ""),
                "body_plain": cleaned,
            }

            if include_raw:
                record["body_full"] = raw_body

            records.append(record)
        except Exception as exc:  # noqa: BLE001
            records.append({"id": msg.get("id"), "error": str(exc)})

    # Sort newest first by date header where possible, else by id (stable)
    # The Gmail API already returns them in sent order (newest first) since
    # the underlying search_messages is sorted by date. No re-sort needed.

    result: dict[str, Any] = {
        "count_requested": count,
        "count_available": len(records),
        "messages": records,
    }
    return result


def write_voice_timestamp(voice_guide_path: Path) -> None:
    """
    Write or update the voice-guide-built timestamp at the top of
    exec-voice-guide.md. Called after the voice guide is generated/refreshed.
    """
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    marker = f"<!-- voice-guide-built: {ts} -->"

    if not voice_guide_path.exists():
        return

    content = voice_guide_path.read_text(encoding="utf-8")
    # Replace existing marker or prepend
    if "<!-- voice-guide-built:" in content:
        content = re.sub(
            r"<!-- voice-guide-built: .+? -->",
            marker,
            content,
        )
    else:
        content = marker + "\n" + content

    voice_guide_path.write_text(content, encoding="utf-8")


def get_voice_guide_age_days(voice_guide_path: Path) -> int | None:
    """
    Return the voice guide age in days. Tries the built-marker first; falls
    back to file mtime when the marker is missing or malformed. Emits one
    ``voice_guide_age_check`` structured event recording which branch fired
    (``source="marker"`` or ``source="mtime"``). Returns None only when the
    file does not exist (no event emitted in that case).
    """
    if not voice_guide_path.exists():
        return None

    from structured_logger import get_logger
    log = get_logger()

    content = voice_guide_path.read_text(encoding="utf-8")
    match = re.search(r"<!-- voice-guide-built: (.+?) -->", content)
    if match:
        try:
            built_dt = datetime.fromisoformat(match.group(1).replace("Z", "+00:00"))
            age = (datetime.now(timezone.utc) - built_dt).days
            log.event("voice_guide_age_check", source="marker", age_days=age)
            return age
        except (ValueError, TypeError):
            pass  # Fall through to mtime.

    mtime = voice_guide_path.stat().st_mtime
    age = int((time.time() - mtime) // (24 * 3600))
    log.event("voice_guide_age_check", source="mtime", age_days=age)
    return age


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fetch and clean the exec's sent messages for voice extraction."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_fetch = sub.add_parser("fetch", help="Fetch N sent messages as cleaned JSON")
    p_fetch.add_argument(
        "--count",
        type=int,
        default=30,
        help="Number of sent messages to pull (default 30)",
    )
    p_fetch.add_argument(
        "--include-raw",
        action="store_true",
        help="Include raw plain-text body alongside the cleaned body",
    )

    args = parser.parse_args()

    try:
        client = GmailClient()
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: could not authenticate: {exc}", file=sys.stderr)
        return 1

    if args.command == "fetch":
        result = fetch_sent(client, args.count, args.include_raw)
        if "error" in result:
            print(f"ERROR: {result['error']}", file=sys.stderr)
            print(json.dumps(result, indent=2))
            return 1

        available = result["count_available"]
        print(
            f"Fetched {available}/{args.count} sent messages.",
            file=sys.stderr,
        )

        if available < 3:
            print(
                "WARNING: fewer than 3 sent messages available — not enough for any profile.",
                file=sys.stderr,
            )
            print(json.dumps(result, indent=2))
            return 2

        if available < 10:
            print(
                f"WARNING: only {available} sent messages available — signal is weak. "
                "Voice guide should note 'limited signal' until more messages are sent.",
                file=sys.stderr,
            )

        print(json.dumps(result, indent=2))
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
