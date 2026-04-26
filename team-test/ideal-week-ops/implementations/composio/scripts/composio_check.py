#!/usr/bin/env python3
"""Pre-flight check for the Composio implementation of ideal-week-ops.

Verifies:
  1. The `composio` CLI is installed and on PATH
  2. The CLI is authenticated (logged in) to a Composio account
  3. A calendar app is connected (Google Calendar or Outlook Calendar)
  4. At least one notification app is connected (Slack, Gmail, Outlook, iMessage)
  5. The required tools are discoverable via Composio's search

Exits 0 on success; non-zero on any failure with an actionable message.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from typing import Optional

# Force UTF-8 on stdout/stderr so emoji and em-dashes render on Windows (cp1252 default).
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass

CALENDAR_APPS = {"googlecalendar", "outlook"}
NOTIFICATION_APPS = {"slack", "gmail", "outlook", "imessage"}


def check_cli_installed() -> Optional[str]:
    """Return the composio CLI version string, or None if missing."""
    if not shutil.which("composio"):
        return None
    try:
        result = subprocess.run(
            ["composio", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return result.stdout.strip() or "unknown version"
        return None
    except (subprocess.SubprocessError, FileNotFoundError):
        return None


def list_connections() -> Optional[list[dict]]:
    """Return the list of connected apps as dicts, or None if the call fails.

    The exact shape is whatever the CLI emits; we look for any field that
    looks like an app slug (e.g., 'googlecalendar', 'slack').
    """
    try:
        result = subprocess.run(
            ["composio", "connections", "list", "--json"],
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (subprocess.SubprocessError, FileNotFoundError):
        return None
    if result.returncode != 0:
        return None
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return None
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "connections" in data:
        return data["connections"]
    return None


def extract_app_slug(connection: dict) -> str:
    """Best-effort extraction of the app slug from a connection record."""
    for key in ("app", "appName", "appKey", "app_slug", "slug", "name"):
        value = connection.get(key)
        if isinstance(value, str) and value:
            return value.lower()
    return ""


def search_tool(query: str) -> bool:
    """Return True if `composio search` finds at least one tool for the query."""
    try:
        result = subprocess.run(
            ["composio", "search", query, "--json"],
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (subprocess.SubprocessError, FileNotFoundError):
        return False
    if result.returncode != 0:
        return False
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return result.stdout.strip() != ""
    if isinstance(data, list):
        return len(data) > 0
    if isinstance(data, dict):
        return bool(data.get("results") or data.get("tools"))
    return False


def main() -> int:
    failures: list[str] = []

    # 1. CLI installed
    version = check_cli_installed()
    if version is None:
        print("❌ Composio CLI not found on PATH")
        print("   Install: see the Install page in your Composio dashboard")
        print("           or https://docs.composio.dev/cli")
        return 1
    print(f"✅ Composio CLI installed ({version})")

    # 2. Connections list
    connections = list_connections()
    if connections is None:
        print("❌ Could not list Composio connections")
        print("   Try: composio login   (then re-run this script)")
        return 2

    connected_apps = {extract_app_slug(c) for c in connections}
    connected_apps.discard("")

    # 3. Calendar app connected
    calendar_match = connected_apps & CALENDAR_APPS
    if not calendar_match:
        failures.append(
            "❌ No calendar app connected (need one of: "
            f"{', '.join(sorted(CALENDAR_APPS))})\n"
            "   Open https://app.composio.dev/apps and connect Google Calendar or Outlook."
        )
    else:
        print(f"✅ Calendar connected: {', '.join(sorted(calendar_match))}")

    # 4. Notification app connected
    notification_match = connected_apps & NOTIFICATION_APPS
    if not notification_match:
        failures.append(
            "❌ No notification app connected (need at least one of: "
            f"{', '.join(sorted(NOTIFICATION_APPS))})\n"
            "   Open https://app.composio.dev/apps and connect Slack, Gmail, Outlook, or iMessage."
        )
    else:
        primary = sorted(notification_match)[0]
        alternates = sorted(notification_match - {primary})
        msg = f"✅ Notification channel connected: {primary}"
        if alternates:
            msg += f"\n   (alternates available: {', '.join(alternates)})"
        print(msg)

    # 5. Tool discovery
    if calendar_match and not search_tool("list calendar events"):
        failures.append(
            "❌ Composio search did not return a calendar tool\n"
            "   Run: composio search 'list calendar events'\n"
            "   If the result is empty, the calendar app may need a re-connect."
        )
    elif calendar_match:
        print("✅ Calendar tool discoverable via search")

    if notification_match and not search_tool("send message"):
        failures.append(
            "❌ Composio search did not return a notification tool\n"
            "   Run: composio search 'send message'"
        )
    elif notification_match:
        print("✅ Notification tool discoverable via search")

    if failures:
        print()
        for f in failures:
            print(f)
        return 3

    print()
    print("Ready to run scan-ideal-week.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
