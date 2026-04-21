"""
Scan Labels
===========
List all existing Gmail labels with message counts and last-active dates.
Used by inbox-audit to understand the exec's existing label structure.

Output JSON:
{
  "labels": [
    {
      "id": "Label_123",
      "name": "Board",
      "type": "user",           # user | system
      "total_messages": 47,
      "unread_messages": 3,
      "active_90d": true        # true if messages in last 90 days
    }
  ],
  "summary": {
    "total": 12,
    "user_labels": 8,
    "active": 5,
    "inactive": 3
  }
}

Usage:
    python scan_labels.py
    python scan_labels.py --days 60
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

_IMPL_SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"
_SHARED_SCRIPTS = Path(__file__).resolve().parents[5] / "shared" / "scripts"
for _p in (_IMPL_SCRIPTS, _SHARED_SCRIPTS):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from gmail_auth import get_credentials
from googleapiclient.discovery import build


def scan_labels(days: int = 90) -> dict:
    creds = get_credentials()
    service = build("gmail", "v1", credentials=creds)

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    cutoff_epoch = int(cutoff.timestamp())

    raw = service.users().labels().list(userId="me").execute()
    all_labels = raw.get("labels", [])

    results = []
    for label in all_labels:
        label_id = label["id"]
        name = label["name"]
        label_type = label.get("type", "user")

        detail = service.users().labels().get(userId="me", id=label_id).execute()
        total = detail.get("messagesTotal", 0)
        unread = detail.get("messagesUnread", 0)

        # Check for recent activity
        active = False
        if total > 0:
            query = f"label:{label_id} after:{cutoff_epoch}"
            result = service.users().messages().list(
                userId="me", q=query, maxResults=1
            ).execute()
            active = bool(result.get("messages"))

        results.append({
            "id": label_id,
            "name": name,
            "type": label_type,
            "total_messages": total,
            "unread_messages": unread,
            "active_90d": active,
        })

    user_labels = [r for r in results if r["type"] == "user"]
    active_count = sum(1 for r in user_labels if r["active_90d"])

    return {
        "labels": results,
        "summary": {
            "total": len(results),
            "user_labels": len(user_labels),
            "active": active_count,
            "inactive": len(user_labels) - active_count,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scan existing Gmail labels.")
    parser.add_argument("--days", type=int, default=90, help="Lookback window for active check.")
    args = parser.parse_args(argv)

    try:
        data = scan_labels(days=args.days)
        print(json.dumps(data, indent=2))
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
