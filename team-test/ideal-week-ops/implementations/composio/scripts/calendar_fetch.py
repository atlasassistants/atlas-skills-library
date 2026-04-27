#!/usr/bin/env python3
"""Fetch calendar events for a date range via the Composio CLI.

Usage:
  calendar_fetch.py --start YYYY-MM-DD --end YYYY-MM-DD [--account <slug>]
  calendar_fetch.py --fixture <path>    # use local sample data instead of live fetch

Outputs a JSON list of normalized events to stdout:
  [
    {
      "title": str,
      "start": "YYYY-MM-DDTHH:MM",   # local time, no timezone offset
      "end":   "YYYY-MM-DDTHH:MM",
      "attendees": [str, ...],       # email addresses
      "organizer": str,              # email address
      "is_recurring": bool,
      "account": str                 # composio app slug
    },
    ...
  ]

Designed to be called from `scan-ideal-week`. The skill body parses the JSON
and runs the rule engine against the events.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from typing import Any

# Force UTF-8 on stdout/stderr so the JSON output renders cleanly on Windows.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass


def fetch_via_composio(start: str, end: str, account: str | None) -> list[dict]:
    """Discover and execute the calendar list-events tool via Composio CLI."""
    # Discover the tool. Calendar list tools across providers (Google, Outlook)
    # consistently match this query.
    search = subprocess.run(
        ["composio", "search", "list calendar events", "--json"],
        capture_output=True,
        text=True,
        timeout=15,
        check=True,
    )
    candidates = json.loads(search.stdout)
    if isinstance(candidates, dict):
        candidates = candidates.get("results") or candidates.get("tools") or []
    if not candidates:
        raise RuntimeError(
            "No calendar list tool found via Composio search. "
            "Run `composio search 'list calendar events'` to debug."
        )

    # Pick the first calendar list tool. If the user has both Google and
    # Outlook, this picks the first one returned — the multi-account flow
    # is in the higher-level scan-ideal-week skill, which calls this script
    # once per account.
    tool_id = candidates[0].get("id") or candidates[0].get("tool_id") or candidates[0].get("name")
    if not tool_id:
        raise RuntimeError(f"Could not extract tool id from search result: {candidates[0]}")

    # Build the execute payload. Field names are kept conservative — most
    # calendar list tools accept `start_time` / `end_time` or `time_min` / `time_max`.
    # We pass both shapes; the tool ignores unknown fields.
    payload: dict[str, Any] = {
        "start_time": f"{start}T00:00:00Z",
        "end_time": f"{end}T23:59:59Z",
        "time_min": f"{start}T00:00:00Z",
        "time_max": f"{end}T23:59:59Z",
        "max_results": 250,
    }
    if account:
        payload["account"] = account

    execute = subprocess.run(
        ["composio", "execute", tool_id, "-d", json.dumps(payload)],
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    )
    raw = json.loads(execute.stdout)
    return normalize_events(raw, account or tool_id)


def normalize_events(raw: Any, account_label: str) -> list[dict]:
    """Convert a provider-specific event list into the plugin's normalized shape."""
    # Composio responses vary by provider. Look for common shapes.
    items: list[dict] = []
    if isinstance(raw, dict):
        items = raw.get("items") or raw.get("events") or raw.get("data") or []
    elif isinstance(raw, list):
        items = raw

    normalized = []
    for item in items:
        if not isinstance(item, dict):
            continue
        title = item.get("summary") or item.get("subject") or item.get("title") or "(untitled)"
        start = _extract_datetime(item.get("start"))
        end = _extract_datetime(item.get("end"))
        if not start or not end:
            continue
        attendees = _extract_attendees(item.get("attendees"))
        organizer = _extract_email(item.get("organizer"))
        is_recurring = bool(item.get("recurringEventId") or item.get("recurrence") or item.get("is_recurring"))
        normalized.append({
            "title": title,
            "start": start,
            "end": end,
            "attendees": attendees,
            "organizer": organizer,
            "is_recurring": is_recurring,
            "account": account_label,
        })
    return normalized


def _extract_datetime(field: Any) -> str:
    """Extract a YYYY-MM-DDTHH:MM string from various provider shapes."""
    if isinstance(field, str):
        return field[:16]
    if isinstance(field, dict):
        for key in ("dateTime", "date_time", "datetime", "date"):
            value = field.get(key)
            if isinstance(value, str):
                return value[:16]
    return ""


def _extract_attendees(field: Any) -> list[str]:
    if not isinstance(field, list):
        return []
    out: list[str] = []
    for item in field:
        email = _extract_email(item)
        if email:
            out.append(email)
    return out


def _extract_email(field: Any) -> str:
    if isinstance(field, str):
        return field
    if isinstance(field, dict):
        for key in ("email", "address", "emailAddress"):
            value = field.get(key)
            if isinstance(value, str) and value:
                return value
    return ""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", help="start date YYYY-MM-DD")
    parser.add_argument("--end", help="end date YYYY-MM-DD")
    parser.add_argument("--account", help="composio app slug for a specific account", default=None)
    parser.add_argument("--fixture", help="path to a local fixture JSON file (skips live fetch)", default=None)
    args = parser.parse_args()

    if args.fixture:
        with open(args.fixture, "r", encoding="utf-8") as f:
            fixture_data = json.load(f)
        json.dump(fixture_data, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0

    if not args.start or not args.end:
        parser.error("--start and --end are required unless --fixture is given")

    try:
        events = fetch_via_composio(args.start, args.end, args.account)
    except subprocess.CalledProcessError as exc:
        sys.stderr.write(f"composio CLI error: {exc.stderr}\n")
        return 2
    except (RuntimeError, json.JSONDecodeError) as exc:
        sys.stderr.write(f"fetch failed: {exc}\n")
        return 3

    json.dump(events, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
