"""
Check Follow-Ups
================
Manages the 3-Waiting For queue per Atlas follow-up cadences (see
references/follow-up-cadences.md).

Responsibilities of THIS script (mechanical layer):
    - Fetch every item in 3-Waiting For
    - For each item, detect whether the waiter has already replied in thread
    - Classify the item as revenue / internal / vendors based on recipient
      domain + keywords + team delegation map
    - Compute label_age_days using the item's internalDate as proxy
    - Decide which cadence step is due now (or "none" if nothing is due)
    - Emit JSON so the agent can draft follow-ups in the exec's voice

Responsibilities of the AGENT (not this script):
    - Drafting the actual follow-up text in exec voice
    - Deciding what to do with replies (running the decision tree)
    - Reporting results to the user

Subcommands:

    scan            Full pass. Returns JSON with all 3-Waiting For items,
                    their category, cadence step, and reply status. Supports
                    filters: --replies-only, --only-message-id, --dry-run.
    clear-waiting   Remove 3-Waiting For from a single message. Used by
                    the agent when a reply arrives and it re-triages.
    escalate        Move a single message from 3-Waiting For to 5-Follow Up
                    when its cadence is exhausted.

Usage:
    python check_followups.py scan --exec-email alex@company.com
    python check_followups.py scan --exec-email alex@company.com --replies-only
    python check_followups.py scan --exec-email alex@company.com --dry-run
    python check_followups.py clear-waiting --message-id MSG_ID
    python check_followups.py escalate --message-id MSG_ID

Exit codes:
    0 — success
    1 — auth or fatal failure
"""

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Any

_SHARED_SCRIPTS = Path(__file__).resolve().parents[2] / "shared" / "scripts"
if str(_SHARED_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SHARED_SCRIPTS))

from gmail_client import GmailClient
from profile_paths import profile_read_path
from state_store import StateStore
from atlas_labels import LEADS, WAITING_FOR, FOLLOW_UP


# ─────────────────────────────────────────────
# CADENCE DEFINITIONS
# ─────────────────────────────────────────────

# Cadence step lists — day numbers at which a step fires.
# Last entry is the "escalate" step — moves item to 5-Follow Up.
CADENCES: dict[str, list[tuple[int, str]]] = {
    "revenue": [
        (1, "day_1"),
        (2, "day_2"),
        (4, "day_4"),
        (7, "day_7_final"),
        (8, "escalate"),
    ],
    "internal": [
        (1, "day_1"),
        (3, "day_3"),
        (5, "day_5_escalate"),
        (6, "escalate"),
    ],
    "vendors": [
        (3, "day_3"),
        (14, "week_2"),
        (21, "week_3_final"),
        (22, "escalate"),
    ],
}


REVENUE_KEYWORDS: list[str] = [
    "proposal", "pricing", "quote", "quotation",
    "renewal", "contract", "terms", "signed", "sign off", "sign-off",
    "close", "closing", "deal",
    "q1 terms", "q2 terms", "q3 terms", "q4 terms",
    "mrr", "arr", "acv", "revenue",
    "invoice approval", "po number", "po#",
]


EMAIL_REGEX = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


# ─────────────────────────────────────────────
# TEAM MAP — for internal classification
# ─────────────────────────────────────────────

def load_team_emails_and_domains(team_map_path: Path) -> tuple[set[str], set[str]]:
    """
    Parse team-delegation-map.md and return (emails, domains).

    Returns two sets:
        emails: lowercased exact email addresses
        domains: lowercased domain parts (after the @)

    Skips template placeholders like name@company.com / email@example.com.
    """
    if not team_map_path.exists():
        return set(), set()

    emails: set[str] = set()
    domains: set[str] = set()

    for line in team_map_path.read_text(encoding="utf-8").splitlines():
        for match in EMAIL_REGEX.findall(line):
            low = match.lower()
            if low in ("name@company.com", "email@example.com"):
                continue
            emails.add(low)
            if "@" in low:
                domains.add(low.split("@", 1)[1])

    return emails, domains


# ─────────────────────────────────────────────
# CATEGORY CLASSIFICATION
# ─────────────────────────────────────────────

def classify(
    to_header: str,
    subject: str,
    body: str,
    label_ids: list[str],
    team_emails: set[str],
    team_domains: set[str],
    leads_label_id: str | None,
    override: str | None = None,
) -> str:
    """
    Classify a thread as 'revenue', 'internal', or 'vendors'.

    Order:
      1. Override wins if provided.
      2. Internal: recipient email or domain appears in team map.
      3. Revenue: subject/body matches revenue keywords OR has 0-Leads label.
      4. Default: vendors.
    """
    if override in ("revenue", "internal", "vendors"):
        return override

    to_lower = (to_header or "").lower()

    # Extract the bare email from "Name <email>" format
    to_emails = EMAIL_REGEX.findall(to_lower)

    # Internal check
    for addr in to_emails:
        if addr in team_emails:
            return "internal"
        if "@" in addr and addr.split("@", 1)[1] in team_domains:
            return "internal"

    # Revenue check
    if leads_label_id and leads_label_id in label_ids:
        return "revenue"

    combined = f"{subject} {body[:500] if body else ''}".lower()
    for kw in REVENUE_KEYWORDS:
        if kw in combined:
            return "revenue"

    return "vendors"


# ─────────────────────────────────────────────
# CADENCE LOOKUP
# ─────────────────────────────────────────────

def cadence_step_for(category: str, age_days: int) -> str:
    """
    Return the cadence step that is due for a given category at given age.

    Rules:
    - If age_days < first step day → "none" (not yet due)
    - If age_days matches a step exactly or is between that step and the next,
      return that step (missed-step rule: fire only the most recent applicable
      step, never spam catch-up)
    - If age_days >= escalate threshold → "escalate"
    """
    if category not in CADENCES:
        return "none"

    steps = CADENCES[category]

    # Escalate threshold is the last tuple
    escalate_day = steps[-1][0]
    if age_days >= escalate_day:
        return "escalate"

    # Find the latest step whose day <= age_days
    applicable: str | None = None
    for day, name in steps[:-1]:
        if age_days >= day:
            applicable = name
        else:
            break

    return applicable if applicable else "none"


def _next_unexecuted_step(
    category: str, age_days: int, store: StateStore, message_id: str
) -> str:
    """Find the next cadence step that hasn't been executed yet."""
    if category not in CADENCES:
        return "none"

    steps = CADENCES[category]
    for day, step_name in steps:
        if age_days >= day and not store.is_step_executed(message_id, step_name):
            return step_name
    return "none"


# ─────────────────────────────────────────────
# REPLY DETECTION
# ─────────────────────────────────────────────

def waiting_thread_state(
    client: GmailClient,
    thread_id: str,
    exec_email: str,
    to_header: str,
) -> tuple[bool, bool]:
    """
    Return ``(is_valid_waiting_thread, waiter_replied)``.

    A valid waiting thread must contain at least one outgoing message from the
    exec. If a thread has no exec-sent message, it does not belong in
    ``3-Waiting For`` and should be surfaced as invalid queue state instead of
    quietly treated as "still waiting" forever.

    Heuristic:
      - Walk the thread messages in order.
      - Track the most recent message from the exec.
      - If there's any message AFTER that exec message FROM someone else
        (specifically, matching one of the emails in the original `to_header`
        — those are the people we were waiting on), return True.
      - Fallback: if `to_header` parsing yields no emails, return True if
        there's any non-exec message after the exec's last outgoing one.
    """
    if not thread_id:
        return False, False

    try:
        thread = client.read_thread(thread_id, format="metadata")
    except Exception:  # noqa: BLE001
        return False, False

    messages = thread.get("messages", [])
    if not messages:
        return False, False

    exec_low = (exec_email or "").lower()
    waiter_emails = {addr.lower() for addr in EMAIL_REGEX.findall(to_header or "")}

    # Sort by internalDate to be safe
    def _order_key(m: dict) -> int:
        return int(m.get("internalDate", 0))

    sorted_msgs = sorted(messages, key=_order_key)

    last_exec_idx = -1
    for idx, msg in enumerate(sorted_msgs):
        headers = client.get_message_headers(msg)
        from_value = (headers.get("from", "") or "").lower()
        if exec_low and exec_low in from_value:
            last_exec_idx = idx

    if last_exec_idx < 0:
        return False, False

    for msg in sorted_msgs[last_exec_idx + 1:]:
        headers = client.get_message_headers(msg)
        from_value = (headers.get("from", "") or "").lower()
        if exec_low and exec_low in from_value:
            continue  # still the exec
        sender_addrs = {a.lower() for a in EMAIL_REGEX.findall(from_value)}
        if waiter_emails and sender_addrs & waiter_emails:
            return True, True
        if not waiter_emails:
            # Fallback: any non-exec message counts as a reply
            return True, True

    return True, False


# ─────────────────────────────────────────────
# DRAFT DUPLICATE DETECTION
# ─────────────────────────────────────────────

def thread_has_pending_draft(client: GmailClient, thread_id: str) -> bool:
    """
    True if there's already a draft attached to this thread. Prevents
    duplicate follow-up drafts when the skill is re-run in the same session.
    """
    if not thread_id:
        return False
    try:
        drafts = client.list_drafts(max_results=100)
    except Exception:  # noqa: BLE001
        return False
    for draft in drafts:
        msg = draft.get("message", {})
        if msg.get("threadId") == thread_id:
            return True
    return False


# ─────────────────────────────────────────────
# SCAN
# ─────────────────────────────────────────────

def scan(
    client: GmailClient,
    exec_email: str,
    team_emails: set[str],
    team_domains: set[str],
    replies_only: bool,
    only_message_id: str | None,
    category_override: str | None,
    dry_run: bool,
) -> dict[str, Any]:
    """
    Scan 3-Waiting For and return a JSON-friendly structured report.
    """
    query = f'label:"{WAITING_FOR}"'
    if only_message_id:
        stubs = [{"id": only_message_id, "threadId": None}]
    else:
        stubs = client.search_all_messages(query, max_results=500)

    print(f"Scanning {len(stubs)} items in {WAITING_FOR}", file=sys.stderr)

    # Find 0-Leads label id for revenue classification
    leads_label = client.find_label_by_name(LEADS)
    leads_label_id = leads_label["id"] if leads_label else None

    now = time.time()
    now_ms = int(now * 1000)
    store = StateStore()
    records: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []

    # Aggregates for the agent-facing summary
    replied: list[dict[str, Any]] = []
    due_today: list[dict[str, Any]] = []
    escalations: list[dict[str, Any]] = []
    still_waiting: list[dict[str, Any]] = []
    invalid_waiting: list[dict[str, Any]] = []

    skipped = 0
    for i, stub in enumerate(stubs, start=1):
        if i % 25 == 0:
            print(f"  checked {i}/{len(stubs)}...", file=sys.stderr)

        try:
            msg = client.read_message(stub["id"], format="full")
        except Exception as exc:  # noqa: BLE001
            errors.append({"id": stub["id"], "error": f"read failed: {exc}"})
            continue

        thread_id = msg.get("threadId")
        headers = client.get_message_headers(msg)
        body = client.get_message_body(msg) or ""
        to_header = headers.get("to", "")
        subject = headers.get("subject", "")
        label_ids = msg.get("labelIds", [])

        # Prefer state store timestamp for label age
        label_ts = store.get_label_applied_at(msg["id"], WAITING_FOR)
        if label_ts is not None:
            age_seconds = max(0, now - label_ts)
            age_days = int(age_seconds // (24 * 3600))
        else:
            # Fallback: internalDate proxy (old behavior)
            internal_date = int(msg.get("internalDate", 0))
            age_ms = max(0, now_ms - internal_date)
            age_days = int(age_ms // (24 * 3600 * 1000))

        # Category
        category = classify(
            to_header=to_header,
            subject=subject,
            body=body,
            label_ids=label_ids,
            team_emails=team_emails,
            team_domains=team_domains,
            leads_label_id=leads_label_id,
            override=category_override,
        )

        # Reply detection
        valid_waiting_thread, replied_bool = waiting_thread_state(
            client=client,
            thread_id=thread_id,
            exec_email=exec_email,
            to_header=to_header,
        )

        # Cadence step
        cadence_step = "none"
        if not replied_bool:
            cadence_step = cadence_step_for(category, age_days)

        # Check if this step was already executed in a previous session
        if cadence_step != "none" and cadence_step != "escalate":
            if store.is_step_executed(msg["id"], cadence_step):
                # Already done — find the next unexecuted step
                cadence_step = _next_unexecuted_step(
                    category, age_days, store, msg["id"]
                )

        # Check for existing draft: state store first, then Gmail API fallback
        has_draft = store.is_step_executed(msg["id"], cadence_step) if cadence_step != "none" else False
        if not has_draft:
            has_draft = thread_has_pending_draft(client, thread_id)

        record = {
            "message_id": msg["id"],
            "thread_id": thread_id,
            "subject": subject,
            "to": to_header,
            "from": headers.get("from", ""),
            "label_age_days": age_days,
            "category": category,
            "cadence_step": cadence_step,
            "last_reply_from_waiter": replied_bool,
            "has_existing_draft": has_draft,
            "valid_waiting_thread": valid_waiting_thread,
        }

        if replies_only and not replied_bool:
            continue

        records.append(record)

        if not valid_waiting_thread:
            invalid_waiting.append(record)
        elif replied_bool:
            replied.append(record)
        elif cadence_step == "escalate":
            escalations.append(record)
        elif cadence_step != "none":
            due_today.append(record)
        else:
            still_waiting.append(record)

    summary = {
        "scanned_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "dry_run": dry_run,
        "scanned": len(records),
        "skipped": skipped,
        "replied": len(replied),
        "drafts_created": 0,  # agent increments this as it drafts
        "escalated_to_followup": 0,  # ditto
        "still_waiting": len(still_waiting),
        "invalid_waiting": [
            {
                "message_id": r["message_id"],
                "thread_id": r["thread_id"],
                "to": r["to"],
                "subject": r["subject"],
                "days_waiting": r["label_age_days"],
                "category": r["category"],
                "reason": "no_exec_outgoing_message",
            }
            for r in invalid_waiting
        ],
        "due_today": [
            {
                "message_id": r["message_id"],
                "thread_id": r["thread_id"],
                "to": r["to"],
                "subject": r["subject"],
                "days_waiting": r["label_age_days"],
                "category": r["category"],
                "cadence_step": r["cadence_step"],
                "has_existing_draft": r["has_existing_draft"],
            }
            for r in due_today
        ],
        "escalations": [
            {
                "message_id": r["message_id"],
                "thread_id": r["thread_id"],
                "to": r["to"],
                "subject": r["subject"],
                "days_waiting": r["label_age_days"],
                "category": r["category"],
            }
            for r in escalations
        ],
        "replies_to_retriage": [
            {
                "message_id": r["message_id"],
                "thread_id": r["thread_id"],
                "to": r["to"],
                "subject": r["subject"],
            }
            for r in replied
        ],
        "still_waiting_details": [
            {
                "message_id": r["message_id"],
                "to": r["to"],
                "subject": r["subject"],
                "days_waiting": r["label_age_days"],
                "category": r["category"],
            }
            for r in still_waiting
        ],
        "records": records,
        "errors": errors,
    }
    return summary


# ─────────────────────────────────────────────
# LABEL TRANSITIONS
# ─────────────────────────────────────────────

def clear_waiting(client: GmailClient, message_id: str) -> dict[str, Any]:
    """Remove 3-Waiting For and clean up state store."""
    label = client.find_label_by_name(WAITING_FOR)
    if not label:
        return {"ok": False, "error": f"Label '{WAITING_FOR}' not found"}
    client.remove_label(message_id, label["id"])

    # Clean up state
    store = StateStore()
    store.remove_label_record(message_id, WAITING_FOR)
    store.remove_label_record(message_id, f"{WAITING_FOR}:scanned")
    store.clear_cadence_history(message_id)

    return {"ok": True, "message_id": message_id, "removed_label": label["name"]}


def escalate_to_followup(client: GmailClient, message_id: str) -> dict[str, Any]:
    """Remove 3-Waiting For and apply 5-Follow Up."""
    waiting = client.find_label_by_name(WAITING_FOR)
    followup = client.find_label_by_name(FOLLOW_UP)
    if not waiting:
        return {"ok": False, "error": f"Label '{WAITING_FOR}' not found"}
    if not followup:
        return {"ok": False, "error": f"Label '{FOLLOW_UP}' not found"}

    client.modify_message(
        message_id,
        add_label_ids=[followup["id"]],
        remove_label_ids=[waiting["id"]],
    )

    store = StateStore()
    store.remove_label_record(message_id, WAITING_FOR)
    store.remove_label_record(message_id, f"{WAITING_FOR}:scanned")
    store.record_label_applied(message_id, FOLLOW_UP)
    store.clear_cadence_history(message_id)

    return {
        "ok": True,
        "message_id": message_id,
        "from_label": WAITING_FOR,
        "to_label": FOLLOW_UP,
    }


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────

def default_team_map() -> Path:
    return profile_read_path("team-delegation-map.md")


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage 3-Waiting For cadence.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_scan = sub.add_parser("scan", help="Scan 3-Waiting For and classify each item")
    p_scan.add_argument("--exec-email", required=True, help="Exec's email address")
    p_scan.add_argument(
        "--team-map",
        type=Path,
        default=None,
        help="Path to team-delegation-map.md",
    )
    p_scan.add_argument(
        "--replies-only",
        action="store_true",
        help="Only return items where the waiter has replied (cheap midday pass)",
    )
    p_scan.add_argument(
        "--only-message-id",
        default=None,
        help="Scan a single specific message ID instead of the whole queue",
    )
    p_scan.add_argument(
        "--category",
        choices=["revenue", "internal", "vendors"],
        default=None,
        help="Force category classification (useful with --only-message-id)",
    )
    p_scan.add_argument(
        "--dry-run",
        action="store_true",
        help="Read-only scan (default behaviour — no label changes happen in scan anyway)",
    )

    p_clear = sub.add_parser("clear-waiting", help="Remove 3-Waiting For from a single message")
    p_clear.add_argument("--message-id", required=True, help="Message ID")

    p_esc = sub.add_parser("escalate", help="Move a message from 3-Waiting For to 5-Follow Up")
    p_esc.add_argument("--message-id", required=True, help="Message ID")

    args = parser.parse_args()

    try:
        client = GmailClient()
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: could not authenticate: {exc}", file=sys.stderr)
        return 1

    if args.command == "scan":
        team_map_path = args.team_map or default_team_map()
        team_emails, team_domains = load_team_emails_and_domains(team_map_path)
        print(
            f"Team map loaded: {len(team_emails)} emails, {len(team_domains)} domains",
            file=sys.stderr,
        )

        try:
            result = scan(
                client=client,
                exec_email=args.exec_email,
                team_emails=team_emails,
                team_domains=team_domains,
                replies_only=args.replies_only,
                only_message_id=args.only_message_id,
                category_override=args.category,
                dry_run=args.dry_run,
            )
        except Exception as exc:  # noqa: BLE001
            print(f"ERROR during scan: {exc}", file=sys.stderr)
            return 1

        # Human summary to stderr
        print(
            f"Done. scanned={result['scanned']} "
            f"replied={result['replied']} "
            f"due_today={len(result['due_today'])} "
            f"escalations={len(result['escalations'])} "
            f"invalid_waiting={len(result['invalid_waiting'])} "
            f"still_waiting={result['still_waiting']}",
            file=sys.stderr,
        )
        print(json.dumps(result, indent=2))
        return 0

    if args.command == "clear-waiting":
        result = clear_waiting(client, args.message_id)
        print(json.dumps(result, indent=2))
        return 0 if result.get("ok") else 1

    if args.command == "escalate":
        result = escalate_to_followup(client, args.message_id)
        print(json.dumps(result, indent=2))
        return 0 if result.get("ok") else 1

    return 1


if __name__ == "__main__":
    sys.exit(main())
