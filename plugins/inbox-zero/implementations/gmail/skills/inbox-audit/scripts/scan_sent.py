"""
Scan Sent Folder
================
Analyze the exec's sent folder to identify VIP candidates, reply timing,
and communication style. Sent patterns are the most reliable signal for
who the exec actually prioritizes.

Output JSON:
{
  "top_recipients": [
    {"email": "name@domain.com", "reply_count": 23, "domain": "domain.com"}
  ],
  "reply_timing": {
    "by_hour": {"6": 12, "7": 34, ...},
    "peak_hours": [7, 8, 9],
    "pattern": "morning-batch"   # morning-batch | spread | evening
  },
  "sent_sample": [
    {"to": "name@domain.com", "subject": "Re: ...", "snippet": "...", "word_count": 12}
  ],
  "summary": {
    "total_sent_scanned": 300,
    "lookback_days": 90,
    "unique_recipients": 47
  }
}

Usage:
    python scan_sent.py
    python scan_sent.py --days 180 --max 500 --sample 20
"""

from __future__ import annotations

import argparse
import base64
import json
import re
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

_IMPL_SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"
_SHARED_SCRIPTS = Path(__file__).resolve().parents[5] / "shared" / "scripts"
for _p in (_IMPL_SCRIPTS, _SHARED_SCRIPTS):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from gmail_auth import get_credentials
from googleapiclient.discovery import build

_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def _extract_emails(header_val: str) -> list[str]:
    return [m.lower() for m in _EMAIL_RE.findall(header_val or "")]


def _header(headers: list[dict], name: str) -> str:
    for h in headers:
        if h["name"].lower() == name.lower():
            return h["value"]
    return ""


def _word_count(snippet: str) -> int:
    return len((snippet or "").split())


def _classify_timing(by_hour: dict[str, int]) -> str:
    morning = sum(by_hour.get(str(h), 0) for h in range(5, 12))
    midday = sum(by_hour.get(str(h), 0) for h in range(12, 17))
    evening = sum(by_hour.get(str(h), 0) for h in range(17, 24))
    total = morning + midday + evening or 1
    if morning / total > 0.5:
        return "morning-batch"
    if evening / total > 0.4:
        return "evening"
    return "spread"


def scan_sent(days: int = 90, max_messages: int = 300, sample_size: int = 15) -> dict:
    creds = get_credentials()
    service = build("gmail", "v1", credentials=creds)

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    query = f"in:sent after:{int(cutoff.timestamp())}"

    messages = []
    page_token = None
    while len(messages) < max_messages:
        kwargs = {"userId": "me", "q": query, "maxResults": min(100, max_messages - len(messages))}
        if page_token:
            kwargs["pageToken"] = page_token
        result = service.users().messages().list(**kwargs).execute()
        messages.extend(result.get("messages", []))
        page_token = result.get("nextPageToken")
        if not page_token:
            break

    recipient_counter: Counter = Counter()
    hour_counter: Counter = Counter()
    sample: list[dict] = []

    for msg_ref in messages:
        msg = service.users().messages().get(
            userId="me", id=msg_ref["id"], format="metadata",
            metadataHeaders=["To", "Cc", "Subject", "Date"]
        ).execute()

        headers = msg.get("payload", {}).get("headers", [])
        to = _extract_emails(_header(headers, "To"))
        cc = _extract_emails(_header(headers, "Cc"))
        subject = _header(headers, "Subject")
        snippet = msg.get("snippet", "")

        for email in to + cc:
            recipient_counter[email] += 1

        internal_date = int(msg.get("internalDate", 0)) / 1000
        sent_dt = datetime.fromtimestamp(internal_date, tz=timezone.utc)
        hour_counter[str(sent_dt.hour)] += 1

        if len(sample) < sample_size and to:
            sample.append({
                "to": to[0],
                "subject": subject,
                "snippet": snippet,
                "word_count": _word_count(snippet),
            })

    top_recipients = [
        {"email": email, "reply_count": count, "domain": email.split("@")[-1]}
        for email, count in recipient_counter.most_common(20)
    ]

    by_hour = dict(hour_counter)
    peak_hours = [int(h) for h, _ in hour_counter.most_common(3)]

    return {
        "top_recipients": top_recipients,
        "reply_timing": {
            "by_hour": by_hour,
            "peak_hours": sorted(peak_hours),
            "pattern": _classify_timing(by_hour),
        },
        "sent_sample": sample,
        "summary": {
            "total_sent_scanned": len(messages),
            "lookback_days": days,
            "unique_recipients": len(recipient_counter),
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scan sent folder for VIP and voice signals.")
    parser.add_argument("--days", type=int, default=90)
    parser.add_argument("--max", type=int, default=300, dest="max_messages")
    parser.add_argument("--sample", type=int, default=15, dest="sample_size")
    args = parser.parse_args(argv)

    try:
        data = scan_sent(days=args.days, max_messages=args.max_messages, sample_size=args.sample_size)
        print(json.dumps(data, indent=2))
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
