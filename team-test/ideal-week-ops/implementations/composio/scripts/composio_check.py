#!/usr/bin/env python3
"""Pre-flight check for the Composio implementation of ideal-week-ops.

Verifies:
  1. Composio is reachable — via CLI (if installed) or REST API fallback
     (uses COMPOSIO_API_KEY env var; find it at app.composio.dev → Install)
  2. A calendar app is connected (Google Calendar or Outlook Calendar)
  3. At least one notification app is connected (Slack, Gmail, Outlook, iMessage)
  4. The required tools are discoverable via Composio's search (CLI path only)

Exits 0 on success; non-zero on any failure with an actionable message.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from typing import Optional

# Force UTF-8 on stdout/stderr so emoji and em-dashes render on Windows (cp1252 default).
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass

CALENDAR_APPS = {"googlecalendar", "outlook"}
NOTIFICATION_APPS = {"slack", "gmail", "outlook", "imessage"}
COMPOSIO_API_BASE = "https://backend.composio.dev/api/v1"


# ── CLI path ──────────────────────────────────────────────────────────────────

def check_cli_installed() -> Optional[str]:
    """Return the composio CLI version string, or None if missing."""
    if not shutil.which("composio"):
        return None
    try:
        result = subprocess.run(
            ["composio", "--version"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            return result.stdout.strip() or "unknown version"
        return None
    except (subprocess.SubprocessError, FileNotFoundError):
        return None


def list_connections_cli() -> Optional[list[dict]]:
    """Return connected apps via CLI, or None if the call fails."""
    try:
        result = subprocess.run(
            ["composio", "connections", "list", "--json"],
            capture_output=True, text=True, timeout=15,
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


def search_tool(query: str) -> bool:
    """Return True if `composio search` finds at least one tool for the query."""
    try:
        result = subprocess.run(
            ["composio", "search", query, "--json"],
            capture_output=True, text=True, timeout=15,
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


# ── REST API fallback path ────────────────────────────────────────────────────

def list_connections_api(api_key: str) -> Optional[list[dict]]:
    """Return connected apps via Composio REST API, or None if the call fails.

    Uses the X-CONSUMER-API-KEY shown in app.composio.dev → Install → MCP section.
    """
    url = f"{COMPOSIO_API_BASE}/connectedAccounts"
    req = urllib.request.Request(url, headers={"x-api-key": api_key})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
    except (urllib.error.URLError, json.JSONDecodeError, OSError):
        return None
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("items", "connections", "data", "connectedAccounts"):
            if isinstance(data.get(key), list):
                return data[key]
    return None


# ── Shared ────────────────────────────────────────────────────────────────────

def extract_app_slug(connection: dict) -> str:
    """Best-effort extraction of the app slug from a connection record."""
    for key in ("app", "appName", "appKey", "app_slug", "slug", "name", "toolkit"):
        value = connection.get(key)
        if isinstance(value, str) and value:
            return value.lower()
    return ""


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    failures: list[str] = []
    cli_available = False

    # 1. Composio reachable — CLI preferred, REST API fallback
    version = check_cli_installed()
    if version:
        cli_available = True
        print(f"✅ Composio CLI installed ({version})")
        connections = list_connections_cli()
        if connections is None:
            print("❌ Could not list Composio connections via CLI")
            print("   Try: composio login   (then re-run this script)")
            return 2
    else:
        print("ℹ️  Composio CLI not on PATH — trying REST API fallback")
        print("   (If you installed via the Composio dashboard, this is expected.)")
        api_key = os.environ.get("COMPOSIO_API_KEY", "")
        if not api_key:
            print("❌ COMPOSIO_API_KEY env var not set")
            print("   Find your key: app.composio.dev → Install → MCP section → X-CONSUMER-API-KEY")
            print("   Then: set COMPOSIO_API_KEY=<your-key>   and re-run")
            return 1
        connections = list_connections_api(api_key)
        if connections is None:
            print("❌ Could not reach Composio API with the provided key")
            print("   Check COMPOSIO_API_KEY is correct and your network is online.")
            return 2
        print("✅ Composio reachable via REST API")

    connected_apps = {extract_app_slug(c) for c in connections}
    connected_apps.discard("")

    # 2. Calendar app connected
    calendar_match = connected_apps & CALENDAR_APPS
    if not calendar_match:
        failures.append(
            "❌ No calendar app connected (need one of: "
            f"{', '.join(sorted(CALENDAR_APPS))})\n"
            "   Open https://app.composio.dev/apps and connect Google Calendar or Outlook."
        )
    else:
        print(f"✅ Calendar connected: {', '.join(sorted(calendar_match))}")

    # 3. Notification app connected
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

    # 4. Tool discovery (CLI only — MCP handles this automatically in non-CLI path)
    if cli_available:
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
    else:
        print("ℹ️  Tool discovery skipped (CLI not available — MCP handles routing automatically)")

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
