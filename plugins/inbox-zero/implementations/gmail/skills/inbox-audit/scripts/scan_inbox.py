"""
Scan Inbox
==========
Analyze inbox volume, top senders, and email type distribution.
Used by inbox-audit to understand what's coming in before touching anything.

Output JSON:
{
  "volume": {
    "total_inbox": 340,
    "unread": 89,
    "age_buckets": {"today": 12, "this_week": 34, "this_month": 67, "older": 227}
  },
  "top_senders": [
    {"email": "sender@domain.com", "count": 45, "domain": "domain.com", "exec_replies": false}
  ],
  "type_estimates": {
    "calendar_scheduling": 18,
    "newsletters_subscriptions": 112,
    "receipts_invoices": 23,
    "notifications": 67,
    "direct_correspondence": 54,
    "other": 66
  },
  "summary": {"scanned": 340, "lookback_days": 90}
}

Usage:
    python scan_inbox.py
    python scan_inbox.py --max 500
"""

from __future__ import annotations

import argparse
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
from pre_classifier import pre_classify
from atlas_labels import REFERENCE, SUBSCRIPTIONS, RECEIPTS

_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def _header(headers: list[dict], name: str) -> str:
    for h in headers:
        if h["name"].lower() == name.lower():
            return h["value"]
    return ""


def _extract_from_email(from_header: str) -> str:
    match = _EMAIL_RE.search(from_header or "")
    return match.group(0).lower() if match else from_header.lower()


def _age_bucket(internal_date_ms: int) -> str:
    now = datetime.now(timezone.utc)
    sent_dt = datetime.fromtimestamp(internal_date_ms / 1000, tz=timezone.utc)
    delta = now - sent_dt
    if delta.days == 0:
        return "today"
    if delta.days <= 7:
        return "this_week"
    if delta.days <= 30:
        return "this_month"
    return "older"


def scan_inbox(max_messages: int = 400) -> dict:
    creds = get_credentials()
    service = build("gmail", "v1", credentials=creds)

    # Total inbox count
    profile = service.users().getProfile(userId="me").execute()
    total_inbox_estimate = profile.get("messagesTotal", 0)

    # Fetch inbox messages
    messages = []
    page_token = None
    while len(messages) < max_messages:
        kwargs = {"userId": "me", "labelIds": ["INBOX"], "maxResults": min(100, max_messages - len(messages))}
        if page_token:
            kwargs["pageToken"] = page_token
        result = service.users().messages().list(**kwargs).execute()
        messages.extend(result.get("messages", []))
        page_token = result.get("nextPageToken")
        if not page_token:
            break

    sender_counter: Counter = Counter()
    age_buckets: Counter = Counter()
    type_counter: Counter = Counter()
    unread_count = 0

    for msg_ref in messages:
        msg = service.users().messages().get(
            userId="me", id=msg_ref["id"], format="metadata",
            metadataHeaders=["From", "Subject"]
        ).execute()

        headers = msg.get("payload", {}).get("headers", [])
        from_header = _header(headers, "From")
        subject = _header(headers, "Subject")
        label_ids = msg.get("labelIds", [])

        sender_email = _extract_from_email(from_header)
        sender_counter[sender_email] += 1

        if "UNREAD" in label_ids:
            unread_count += 1

        age_buckets[_age_bucket(int(msg.get("internalDate", 0)))] += 1

        # Use pre_classifier to estimate type
        classification = pre_classify(from_header=from_header, subject=subject, body="")
        if classification:
            label = classification.get("label", "other")
            if label == REFERENCE:
                type_counter["calendar_scheduling"] += 1
            elif label == SUBSCRIPTIONS:
                type_counter["newsletters_subscriptions"] += 1
            elif label == RECEIPTS:
                type_counter["receipts_invoices"] += 1
            else:
                type_counter["notifications"] += 1
        else:
            type_counter["direct_correspondence"] += 1

    top_senders = [
        {"email": email, "count": count, "domain": email.split("@")[-1] if "@" in email else email}
        for email, count in sender_counter.most_common(20)
    ]

    return {
        "volume": {
            "total_inbox": total_inbox_estimate,
            "scanned": len(messages),
            "unread": unread_count,
            "age_buckets": dict(age_buckets),
        },
        "top_senders": top_senders,
        "type_estimates": dict(type_counter),
        "summary": {
            "scanned": len(messages),
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scan inbox for volume and sender patterns.")
    parser.add_argument("--max", type=int, default=400, dest="max_messages")
    args = parser.parse_args(argv)

    try:
        data = scan_inbox(max_messages=args.max_messages)
        print(json.dumps(data, indent=2))
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
