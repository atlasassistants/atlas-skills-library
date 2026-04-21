"""
Scan Filters
============
List all existing Gmail filters. Used by inbox-audit to document what
the exec has already automated and flag broken or outdated filters.

Output JSON:
{
  "filters": [
    {
      "id": "ANe1BmjX...",
      "criteria": {"from": "newsletter@domain.com"},
      "action": {"addLabelIds": ["Label_123"], "removeLabelIds": ["INBOX"]},
      "readable": "From newsletter@domain.com → label + skip inbox"
    }
  ],
  "summary": {"total": 4}
}

Usage:
    python scan_filters.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_IMPL_SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"
_SHARED_SCRIPTS = Path(__file__).resolve().parents[5] / "shared" / "scripts"
for _p in (_IMPL_SCRIPTS, _SHARED_SCRIPTS):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from gmail_auth import get_credentials
from googleapiclient.discovery import build


def _readable_filter(criteria: dict, action: dict) -> str:
    parts = []
    for key, val in criteria.items():
        parts.append(f"{key}: {val}")
    condition = ", ".join(parts) if parts else "(no condition)"

    actions = []
    if action.get("addLabelIds"):
        actions.append(f"add labels {action['addLabelIds']}")
    if action.get("removeLabelIds"):
        labels = action["removeLabelIds"]
        if "INBOX" in labels:
            actions.append("skip inbox")
        else:
            actions.append(f"remove labels {labels}")
    if action.get("forward"):
        actions.append(f"forward to {action['forward']}")
    if action.get("markAsRead"):
        actions.append("mark as read")
    if not actions:
        actions = ["(no action)"]

    return f"{condition} → {', '.join(actions)}"


def scan_filters() -> dict:
    creds = get_credentials()
    service = build("gmail", "v1", credentials=creds)

    raw = service.users().settings().filters().list(userId="me").execute()
    filters = raw.get("filter", [])

    results = []
    for f in filters:
        criteria = f.get("criteria", {})
        action = f.get("action", {})
        results.append({
            "id": f.get("id"),
            "criteria": criteria,
            "action": action,
            "readable": _readable_filter(criteria, action),
        })

    return {
        "filters": results,
        "summary": {"total": len(results)},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scan existing Gmail filters.")
    parser.parse_args(argv)

    try:
        data = scan_filters()
        print(json.dumps(data, indent=2))
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
