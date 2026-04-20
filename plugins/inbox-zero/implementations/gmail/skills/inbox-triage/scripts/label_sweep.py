"""
Label Sweep
===========
Runs the EOD label sweep per Atlas rules (see references/decision-tree.md
Label Sweep Rules section). For each label, checks the sweep rule and
archives items that meet it.

Rules summary (defaults — can be overridden per client):
    1-Action Required: archive if exec has replied in thread. Older than 48h
                       and no reply → keep, flag for re-flag in next SOD.
    2-Read Only:       archive after 48h in the label.
    3-Waiting For:     SKIP — handled by follow-up-tracker.
    4-Delegated:       archive if routed team member has replied. Older than
                       72h and no activity → keep, flag for EA. If no team map
                       is loaded, fail safe: do not auto-archive delegated mail.
    5-Follow Up:       SKIP — manual exec decision.
    0-Leads:           archive if thread has a reply or calendar event.
    6-Receipts/Invoices: safety-net clear of INBOX only, keep the label.

Rules are soft-configurable via --rules-file (a JSON file with overrides).
If the file doesn't exist, the defaults above are used.

The script needs:
    --exec-email    Email address of the executive (for thread reply checks
                    on 1-Action Required). Required.
    --team-map      Path to team-delegation-map.md (for parsing team member
                    emails used in 4-Delegated reply checks). Optional —
                    if missing, 4-Delegated items are kept for EA review and
                    only age-based flagging is applied.

Output: JSON report to stdout, human summary to stderr.

Usage:
    python label_sweep.py --exec-email alex@company.com
    python label_sweep.py --exec-email alex@company.com --dry-run
"""

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Any

_IMPL_SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"
_SHARED_SCRIPTS = Path(__file__).resolve().parents[5] / "shared" / "scripts"
for _p in (_IMPL_SCRIPTS, _SHARED_SCRIPTS):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from gmail_client import GmailClient
from profile_paths import profile_read_path
from state_store import StateStore
from atlas_labels import (
    LEADS, ACTION_REQUIRED, READ_ONLY, WAITING_FOR, DELEGATED,
    FOLLOW_UP, RECEIPTS, SUBSCRIPTIONS, REFERENCE,
)


EMAIL_REGEX = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


# Default sweep thresholds in hours
DEFAULT_RULES = {
    ACTION_REQUIRED: {
        "mode": "reply_from_exec",
        "reflag_after_hours": 48,
    },
    READ_ONLY: {
        "mode": "age_based",
        "archive_after_hours": 48,
    },
    WAITING_FOR: {"mode": "skip"},
    DELEGATED: {
        "mode": "reply_from_team",
        "flag_ea_after_hours": 72,
    },
    FOLLOW_UP: {"mode": "skip"},
    LEADS: {"mode": "reply_in_thread"},
    RECEIPTS: {"mode": "clear_inbox_only"},
    SUBSCRIPTIONS: {"mode": "skip"},
    REFERENCE: {"mode": "skip"},
}


# ─────────────────────────────────────────────
# Helper: load team emails from team-delegation-map.md
# ─────────────────────────────────────────────

def load_team_emails(team_map_path: Path) -> set[str]:
    """Extract all email addresses from team-delegation-map.md."""
    if not team_map_path.exists():
        return set()
    emails = set()
    for line in team_map_path.read_text(encoding="utf-8").splitlines():
        for match in EMAIL_REGEX.findall(line):
            if match.lower() in ("name@company.com", "email@example.com"):
                continue
            emails.add(match.lower())
    return emails


def _extract_emails(value: str) -> set[str]:
    return {match.lower() for match in EMAIL_REGEX.findall(value or "")}


def _resolve_label_id(client: GmailClient, label_name: str) -> str | None:
    label = client.find_label_by_name(label_name)
    return label["id"] if label else None


def _sweep_candidates(
    client: GmailClient,
    label_name: str,
    only_message_id: str | None,
) -> tuple[list[dict[str, Any]], str | None]:
    label_id = _resolve_label_id(client, label_name)
    if only_message_id:
        if not label_id:
            return [], None
        msg = client.read_message(only_message_id, format="metadata")
        if label_id not in set(msg.get("labelIds", [])):
            return [], label_id
        return [{"id": only_message_id, "threadId": msg.get("threadId")}], label_id
    query = f'label:"{label_name}"'
    return client.search_all_messages(query, max_results=500), label_id


def _clear_queue_item(
    client: GmailClient,
    store: StateStore,
    message_id: str,
    label_name: str,
    label_id: str | None,
) -> None:
    remove_ids = ["INBOX"]
    if label_id:
        remove_ids.insert(0, label_id)
    client.modify_message(message_id, remove_label_ids=remove_ids)
    store.remove_label_record(message_id, label_name)


def _thread_has_reply_from_non_original_sender_since(
    client: GmailClient,
    message: dict[str, Any],
    since_ts: float,
) -> bool:
    thread_id = message.get("threadId")
    if not thread_id:
        return False
    try:
        thread = client.read_thread(thread_id, format="metadata")
    except Exception:
        return False

    original_headers = client.get_message_headers(message)
    original_emails = _extract_emails(original_headers.get("from", ""))
    original_from = (original_headers.get("from", "") or "").strip().lower()

    for item in thread.get("messages", []):
        internal_date = int(item.get("internalDate", 0)) / 1000
        if internal_date <= since_ts:
            continue
        headers = client.get_message_headers(item)
        from_value = (headers.get("from", "") or "").strip().lower()
        sender_emails = _extract_emails(from_value)
        if original_emails:
            if sender_emails and sender_emails <= original_emails:
                continue
        elif from_value == original_from:
            continue
        return True
    return False


# ─────────────────────────────────────────────
# Thread activity helper
# ─────────────────────────────────────────────

def _has_new_thread_activity(
    client: GmailClient,
    thread_id: str,
    since_ts: float,
) -> bool:
    """
    Check if a thread has messages newer than `since_ts`.
    Used before archiving to avoid archiving threads with new activity.
    """
    try:
        thread = client.read_thread(thread_id, format="metadata")
        for msg in thread.get("messages", []):
            internal_date = int(msg.get("internalDate", 0)) / 1000  # ms to seconds
            if internal_date > since_ts:
                return True
    except Exception:
        pass  # If we can't check, err on side of not archiving
    return False


def _thread_has_reply_from_since(
    client: GmailClient,
    thread_id: str,
    sender_email: str,
    since_ts: float,
) -> bool:
    """True if ``sender_email`` replied in the thread after ``since_ts``."""
    try:
        thread = client.read_thread(thread_id, format="metadata")
        needle = (sender_email or "").lower()
        for msg in thread.get("messages", []):
            internal_date = int(msg.get("internalDate", 0)) / 1000
            if internal_date <= since_ts:
                continue
            headers = client.get_message_headers(msg)
            from_value = (headers.get("from", "") or "").lower()
            if needle and needle in from_value:
                return True
    except Exception:
        pass
    return False


# ─────────────────────────────────────────────
# Sweep implementations
# ─────────────────────────────────────────────

def sweep_reply_from_exec(
    client: GmailClient,
    exec_email: str,
    reflag_hours: int,
    dry_run: bool,
    only_message_id: str | None = None,
) -> dict[str, Any]:
    """
    1-Action Required sweep: clear the queue item once exec replied in thread.
    Older than N hours with no reply → keep and mark for reflag.
    Uses state store for actual label timestamp when available.
    """
    label_name = ACTION_REQUIRED
    messages, label_id = _sweep_candidates(client, label_name, only_message_id)
    now = time.time()
    cutoff_seconds = reflag_hours * 3600

    store = StateStore()
    archived = 0
    reflag: list[dict[str, str]] = []
    kept = 0

    for stub in messages:
        msg_id = stub["id"]
        try:
            msg = client.read_message(msg_id, format="metadata")
            label_ts = store.get_label_applied_at(msg_id, label_name)
            if label_ts is None:
                if not dry_run:
                    store.record_label_applied(msg_id, label_name)
                label_ts = int(msg.get("internalDate", 0)) / 1000
            age_seconds = max(0, now - label_ts)

            thread_id = msg.get("threadId")
            if thread_id and _thread_has_reply_from_since(client, thread_id, exec_email, label_ts):
                if not dry_run:
                    _clear_queue_item(client, store, msg_id, label_name, label_id)
                archived += 1
                continue

            if age_seconds >= cutoff_seconds:
                headers = client.get_message_headers(msg)
                reflag.append({
                    "id": msg_id,
                    "subject": headers.get("subject", ""),
                    "from": headers.get("from", ""),
                })
            kept += 1
        except Exception as exc:  # noqa: BLE001
            return {"error": str(exc), "label": label_name}

    return {
        "checked": len(messages),
        "archived": archived,
        "kept": kept,
        "skipped": 0,
        "reflag": reflag,
    }


def sweep_age_based(
    client: GmailClient,
    label_name: str,
    archive_after_hours: int,
    dry_run: bool,
    only_message_id: str | None = None,
) -> dict[str, Any]:
    """
    2-Read Only sweep: clear anything labeled more than N hours ago.
    Uses the state store for the label timestamp. If no record exists,
    lazy-init the timestamp on this pass so the next run has an accurate age.
    """
    messages, label_id = _sweep_candidates(client, label_name, only_message_id)
    now = time.time()
    cutoff_seconds = archive_after_hours * 3600

    store = StateStore()
    archived = 0
    kept = 0

    for stub in messages:
        msg_id = stub["id"]
        try:
            msg = client.read_message(msg_id, format="metadata")

            label_ts = store.get_label_applied_at(msg_id, label_name)
            if label_ts is None:
                if not dry_run:
                    store.record_label_applied(msg_id, label_name)
                label_ts = now
            age_seconds = max(0, now - label_ts)

            if age_seconds >= cutoff_seconds:
                thread_id = msg.get("threadId")
                if thread_id and _has_new_thread_activity(client, thread_id, label_ts):
                    kept += 1
                    continue
                if not dry_run:
                    _clear_queue_item(client, store, msg_id, label_name, label_id)
                archived += 1
            else:
                kept += 1
        except Exception as exc:  # noqa: BLE001
            return {"error": str(exc), "label": label_name}

    return {"checked": len(messages), "archived": archived, "kept": kept, "skipped": 0}


def sweep_reply_from_team(
    client: GmailClient,
    team_emails: set[str],
    flag_after_hours: int,
    dry_run: bool,
    only_message_id: str | None = None,
) -> dict[str, Any]:
    """
    4-Delegated sweep: clear the queue item if a routed team member replied.
    Items older than N hours with no team reply → flag for EA.
    If no team map is available, fail safe by never auto-clearing.
    """
    label_name = DELEGATED
    messages, label_id = _sweep_candidates(client, label_name, only_message_id)
    now = time.time()
    cutoff_seconds = flag_after_hours * 3600

    store = StateStore()
    archived = 0
    flagged_ea: list[dict[str, str]] = []
    kept = 0
    auto_archive_disabled = not bool(team_emails)

    for stub in messages:
        msg_id = stub["id"]
        try:
            msg = client.read_message(msg_id, format="metadata")
            thread_id = msg.get("threadId")
            replied = False

            label_ts = store.get_label_applied_at(msg_id, label_name)
            if label_ts is None:
                if not dry_run:
                    store.record_label_applied(msg_id, label_name)
                label_ts = int(msg.get("internalDate", 0)) / 1000
            age_seconds = max(0, now - label_ts)

            if thread_id and team_emails:
                for team_email in team_emails:
                    if _thread_has_reply_from_since(client, thread_id, team_email, label_ts):
                        replied = True
                        break

            if replied:
                if not dry_run:
                    _clear_queue_item(client, store, msg_id, label_name, label_id)
                archived += 1
                continue

            if age_seconds >= cutoff_seconds:
                headers = client.get_message_headers(msg)
                flagged_ea.append({
                    "id": msg_id,
                    "subject": headers.get("subject", ""),
                    "from": headers.get("from", ""),
                })
            kept += 1
        except Exception as exc:  # noqa: BLE001
            return {"error": str(exc), "label": label_name}

    return {
        "checked": len(messages),
        "archived": archived,
        "kept": kept,
        "skipped": 0,
        "flagged_ea": flagged_ea,
        "auto_archive_disabled": auto_archive_disabled,
    }


def sweep_reply_in_thread(
    client: GmailClient,
    label_name: str,
    dry_run: bool,
    only_message_id: str | None = None,
) -> dict[str, Any]:
    """
    0-Leads sweep: clear the queue item once another participant replied.
    """
    messages, label_id = _sweep_candidates(client, label_name, only_message_id)

    store = StateStore()
    archived = 0
    kept = 0

    for stub in messages:
        msg_id = stub["id"]
        try:
            msg = client.read_message(msg_id, format="metadata")
            since_ts = int(msg.get("internalDate", 0)) / 1000
            if _thread_has_reply_from_non_original_sender_since(client, msg, since_ts):
                if not dry_run:
                    _clear_queue_item(client, store, msg_id, label_name, label_id)
                archived += 1
            else:
                kept += 1
        except Exception as exc:  # noqa: BLE001
            return {"error": str(exc), "label": label_name}

    return {
        "checked": len(messages),
        "archived": archived,
        "kept": kept,
        "skipped": 0,
    }


def sweep_clear_inbox_only(
    client: GmailClient,
    label_name: str,
    dry_run: bool,
    only_message_id: str | None = None,
) -> dict[str, Any]:
    """
    Safety-net sweep for labels that should stay searchable but never sit in Inbox.
    Removes only INBOX and preserves the queue label.
    """
    messages, _label_id = _sweep_candidates(client, label_name, only_message_id)

    archived = 0
    kept = 0

    for stub in messages:
        msg_id = stub["id"]
        try:
            msg = client.read_message(msg_id, format="metadata")
            current_label_ids = set(msg.get("labelIds", []))
            if "INBOX" in current_label_ids:
                if not dry_run:
                    client.modify_message(msg_id, remove_label_ids=["INBOX"])
                archived += 1
            else:
                kept += 1
        except Exception as exc:  # noqa: BLE001
            return {"error": str(exc), "label": label_name}

    return {
        "checked": len(messages),
        "archived": archived,
        "kept": kept,
        "skipped": 0,
    }


# ─────────────────────────────────────────────
# Main sweep runner
# ─────────────────────────────────────────────

def run_sweep(
    client: GmailClient,
    exec_email: str,
    team_emails: set[str],
    rules: dict[str, dict],
    dry_run: bool,
    only_message_id: str | None = None,
) -> dict[str, Any]:
    results: dict[str, Any] = {}

    for label_name, rule in rules.items():
        mode = rule.get("mode", "skip")

        if mode == "skip":
            continue

        if mode == "reply_from_exec":
            results[label_name] = sweep_reply_from_exec(
                client,
                exec_email=exec_email,
                reflag_hours=rule.get("reflag_after_hours", 48),
                dry_run=dry_run,
                only_message_id=only_message_id,
            )
        elif mode == "age_based":
            results[label_name] = sweep_age_based(
                client,
                label_name=label_name,
                archive_after_hours=rule.get("archive_after_hours", 48),
                dry_run=dry_run,
                only_message_id=only_message_id,
            )
        elif mode == "reply_from_team":
            results[label_name] = sweep_reply_from_team(
                client,
                team_emails=team_emails,
                flag_after_hours=rule.get("flag_ea_after_hours", 72),
                dry_run=dry_run,
                only_message_id=only_message_id,
            )
        elif mode == "reply_in_thread":
            results[label_name] = sweep_reply_in_thread(
                client,
                label_name=label_name,
                dry_run=dry_run,
                only_message_id=only_message_id,
            )
        elif mode == "clear_inbox_only":
            results[label_name] = sweep_clear_inbox_only(
                client,
                label_name=label_name,
                dry_run=dry_run,
                only_message_id=only_message_id,
            )
        else:
            results[label_name] = {"error": f"unknown mode '{mode}'"}

    return results


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description="Run the EOD label sweep.")
    parser.add_argument("--exec-email", required=True, help="Exec's email address")
    parser.add_argument(
        "--team-map",
        type=Path,
        default=None,
        help="Path to team-delegation-map.md (for team reply checks)",
    )
    parser.add_argument(
        "--rules-file",
        type=Path,
        default=None,
        help="JSON file with sweep rule overrides",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't archive anything — only report what would be done",
    )
    parser.add_argument(
        "--only-message-id",
        default=None,
        help="Limit the sweep to a single message for safe sandbox testing",
    )
    args = parser.parse_args()

    # Resolve defaults
    team_map_path = args.team_map or profile_read_path("team-delegation-map.md")
    team_emails = load_team_emails(team_map_path)

    rules = dict(DEFAULT_RULES)
    if args.rules_file and args.rules_file.exists():
        overrides = json.loads(args.rules_file.read_text(encoding="utf-8"))
        for label, rule in overrides.items():
            rules[label] = rule

    try:
        client = GmailClient()
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: could not authenticate: {exc}", file=sys.stderr)
        return 1

    print(f"Running label sweep (dry_run={args.dry_run})", file=sys.stderr)
    print(f"Team emails loaded: {len(team_emails)}", file=sys.stderr)

    results = run_sweep(
        client=client,
        exec_email=args.exec_email,
        team_emails=team_emails,
        rules=rules,
        dry_run=args.dry_run,
        only_message_id=args.only_message_id,
    )

    # Summary to stderr
    for label, result in results.items():
        if "error" in result:
            print(f"  {label}: ERROR {result['error']}", file=sys.stderr)
        else:
            parts = [f"checked={result['checked']}", f"archived={result['archived']}", f"kept={result['kept']}"]
            if "reflag" in result:
                parts.append(f"reflag={len(result['reflag'])}")
            if "flagged_ea" in result:
                parts.append(f"flagged_ea={len(result['flagged_ea'])}")
            print(f"  {label}: " + ", ".join(parts), file=sys.stderr)

    output = {
        "sweep_run_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "dry_run": args.dry_run,
        "results": results,
    }
    print(json.dumps(output, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
