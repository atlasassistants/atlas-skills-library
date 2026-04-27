#!/usr/bin/env python3
"""Send a scan-ideal-week notification via the Composio CLI.

Usage:
  notify_send.py --channel slack --target "@sam.reyes" --body-file <path>
  notify_send.py --channel gmail --target "sam@example.com" --subject "Ideal week scan" --body-file <path>
  notify_send.py --channel file  --target "./scan-output.md" --body-file <path>
  notify_send.py --dry-run --body-file <path>   # print to stdout, do not send

Channel routing — picks the right Composio tool based on --channel:
  slack    → search "send slack message" → execute
  gmail    → search "send gmail email"   → execute
  outlook  → search "send outlook email" → execute
  imessage → search "send imessage"      → execute
  file     → write to local file (no Composio call)
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

# Force UTF-8 on stdout/stderr so em-dashes and emoji in notification bodies render on Windows.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass


CHANNEL_QUERIES = {
    "slack": "send slack message",
    "gmail": "send gmail email",
    "outlook": "send outlook email",
    "imessage": "send imessage",
}


def discover_tool(query: str) -> str:
    """Return the first tool id matching the query, or raise."""
    result = subprocess.run(
        ["composio", "search", query, "--json"],
        capture_output=True,
        text=True,
        timeout=15,
        check=True,
    )
    candidates = json.loads(result.stdout)
    if isinstance(candidates, dict):
        candidates = candidates.get("results") or candidates.get("tools") or []
    if not candidates:
        raise RuntimeError(f"No tool found for query: {query}")
    first = candidates[0]
    tool_id = first.get("id") or first.get("tool_id") or first.get("name")
    if not tool_id:
        raise RuntimeError(f"Could not extract tool id from: {first}")
    return tool_id


def execute_tool(tool_id: str, payload: dict[str, Any]) -> dict:
    """Execute a Composio tool and return the parsed response."""
    result = subprocess.run(
        ["composio", "execute", tool_id, "-d", json.dumps(payload)],
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"raw": result.stdout}


def send_via_channel(channel: str, target: str, subject: str | None, body: str) -> dict:
    """Route to the right Composio tool based on channel."""
    if channel == "file":
        path = Path(target)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
        return {"channel": "file", "target": str(path), "bytes_written": len(body.encode("utf-8"))}

    if channel not in CHANNEL_QUERIES:
        raise ValueError(f"Unsupported channel: {channel}")

    tool_id = discover_tool(CHANNEL_QUERIES[channel])

    # Build the payload. Field names vary by provider; pass conservative
    # multi-key shapes so most tools accept it without translation.
    payload: dict[str, Any] = {
        "text": body,
        "body": body,
        "message": body,
        "content": body,
    }
    if channel == "slack":
        payload["channel"] = target
        payload["recipient"] = target
    elif channel in {"gmail", "outlook"}:
        payload["to"] = target
        payload["recipient"] = target
        payload["subject"] = subject or "Ideal-week scan"
    elif channel == "imessage":
        payload["recipient"] = target
        payload["to"] = target

    return execute_tool(tool_id, payload)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--channel", choices=["slack", "gmail", "outlook", "imessage", "file"], required=False)
    parser.add_argument("--target", help="Slack handle, email address, file path, etc.")
    parser.add_argument("--subject", help="Subject line for email channels")
    parser.add_argument("--body-file", required=True, help="path to file containing the notification body")
    parser.add_argument("--dry-run", action="store_true", help="print body to stdout instead of sending")
    args = parser.parse_args()

    body = Path(args.body_file).read_text(encoding="utf-8")

    if args.dry_run:
        sys.stdout.write("--- DRY RUN — would send ---\n")
        sys.stdout.write(body)
        if not body.endswith("\n"):
            sys.stdout.write("\n")
        sys.stdout.write("--- end dry run ---\n")
        return 0

    if not args.channel or not args.target:
        parser.error("--channel and --target are required unless --dry-run is set")

    try:
        result = send_via_channel(args.channel, args.target, args.subject, body)
    except subprocess.CalledProcessError as exc:
        sys.stderr.write(f"composio CLI error: {exc.stderr}\n")
        return 2
    except (RuntimeError, ValueError) as exc:
        sys.stderr.write(f"send failed: {exc}\n")
        return 3

    sys.stdout.write(f"Sent via {args.channel} to {args.target}\n")
    sys.stdout.write(json.dumps(result, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
