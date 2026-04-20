"""
Initial Inbox Cleanup for Atlas Inbox Zero
============================================
One-time cleanup procedure the agent runs during onboarding (Section 11 of
atlas-inbox-rules.md). Designed as a small command-line tool so the agent
can invoke each phase separately and stay in control of the decisions.

Phases:

  1. mass-archive
     Archives every message older than N days (default 90). Archive only
     — never delete. Uses Gmail's batch modify for speed.

  2. scan-senders
     Scans the current inbox and prints JSON of senders with >= min_count
     messages. The agent reads this list, decides per sender whether to
     create a bulk filter, and (if yes) calls `create-filter`.

  3. create-filter
     Creates a filter for a single sender, labels them, and applies the
     label to existing messages. The agent calls this once per sender it
     wants to bulk-filter.

  4. count-remaining
     Prints how many messages are still in the inbox. The agent uses this
     to decide whether to keep batching bulk filters or move on to
     per-email triage.

Usage:
    python initial_cleanup.py mass-archive [--older-than-days 90] [--dry-run]
    python initial_cleanup.py mass-archive --older-than-days 90 --execute --approval-id <id>
    python initial_cleanup.py scan-senders [--min-count 5] [--max-scan 1000]
    python initial_cleanup.py create-filter --from SENDER --label LABEL_NAME [--apply-existing] [--dry-run]
    python initial_cleanup.py create-filter --from SENDER --label LABEL_NAME --execute --approval-id <id>
    python initial_cleanup.py count-remaining

JSON output: `scan-senders` and `count-remaining` print machine-readable JSON
to stdout, so the agent can parse it.
"""

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

from approval_policy import (
    ApprovalValidationError,
    approval_request_payload,
    create_approval_request,
    ensure_approved,
    render_approval_instructions,
)
from gmail_client import GmailClient


# ─────────────────────────────────────────────
# Phase 1: Mass archive old messages
# ─────────────────────────────────────────────


def mass_archive(
    client: GmailClient,
    older_than_days: int = 90,
    dry_run: bool = False,
    batch_size: int = 500,
) -> dict:
    """
    Archive every inbox message older than `older_than_days` days.
    Uses batch_modify_messages for efficiency.

    Returns a summary dict with counts.
    """
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=older_than_days)
    cutoff_str = cutoff_date.strftime("%Y/%m/%d")
    query = f"in:inbox before:{cutoff_str}"

    print(f"Searching: {query}", file=sys.stderr)

    # Pull all matching message IDs (capped at a sane upper limit — most
    # inboxes won't exceed this, and if they do the agent can re-run).
    messages = client.search_all_messages(query, max_results=10_000)
    total = len(messages)

    if total == 0:
        return {"matched": 0, "archived": 0, "dry_run": dry_run, "cutoff": cutoff_str}

    print(f"Found {total} messages older than {older_than_days} days.", file=sys.stderr)

    if dry_run:
        return {"matched": total, "archived": 0, "dry_run": True, "cutoff": cutoff_str}

    # Batch archive in chunks of `batch_size`
    archived = 0
    for i in range(0, total, batch_size):
        chunk = [m["id"] for m in messages[i : i + batch_size]]
        try:
            client.batch_modify_messages(
                message_ids=chunk,
                remove_label_ids=["INBOX"],
            )
            archived += len(chunk)
            print(f"  Archived {archived}/{total}...", file=sys.stderr)
        except Exception as exc:  # noqa: BLE001
            print(f"  ERROR on chunk {i}-{i+len(chunk)}: {exc}", file=sys.stderr)

    return {
        "matched": total,
        "archived": archived,
        "dry_run": False,
        "cutoff": cutoff_str,
    }


# ─────────────────────────────────────────────
# Phase 2: Scan bulk sender candidates
# ─────────────────────────────────────────────


def scan_bulk_senders(
    client: GmailClient,
    min_count: int = 5,
    max_scan: int = 1000,
) -> list[dict]:
    """
    Scan the current inbox and return senders with >= min_count messages.
    Uses GmailClient.get_senders_with_count under the hood.

    Returns a list of {email, count} dicts sorted by count descending.
    """
    print(
        f"Scanning up to {max_scan} inbox messages for senders with >= {min_count} emails...",
        file=sys.stderr,
    )
    pairs = client.get_senders_with_count(
        query="in:inbox",
        min_count=min_count,
        max_messages=max_scan,
    )
    return [{"email": email, "count": count} for email, count in pairs]


# ─────────────────────────────────────────────
# Phase 3: Create one bulk sender filter
# ─────────────────────────────────────────────


def create_bulk_sender_filter(
    client: GmailClient,
    sender: str,
    label_name: str,
    apply_existing: bool = True,
    should_archive: bool = True,
    dry_run: bool = False,
) -> dict:
    """
    Create a filter for one bulk sender and (optionally) apply the label
    to existing messages from that sender.

    Returns a summary dict: {sender, label, filter_created, existing_modified}.
    """
    sender = sender.strip().lower()

    # Find the label ID
    label = client.find_label_by_name(label_name)
    if label is None:
        raise KeyError(
            f"Label '{label_name}' doesn't exist. Run create_labels.py first "
            f"or pick a valid Atlas label name."
        )
    label_id = label["id"]

    existing = client.search_all_messages(f"from:{sender}", max_results=1000) if apply_existing else []
    ids_needing_label: list[str] = []
    for stub in existing:
        mid = stub["id"]
        try:
            msg = client.read_message(mid, format="minimal")
        except Exception as exc:  # noqa: BLE001
            print(
                f"Read failed for {mid}; including in batch anyway: {exc}",
                file=sys.stderr,
            )
            ids_needing_label.append(mid)
            continue
        if label_id not in msg.get("labelIds", []):
            ids_needing_label.append(mid)

    if dry_run:
        return {
            "sender": sender,
            "label": label_name,
            "filter_created": False,
            "filter_would_create": True,
            "existing_matched": len(existing),
            "existing_modified": 0,
            "existing_would_modify": len(ids_needing_label),
            "apply_existing": apply_existing,
            "should_archive": should_archive,
            "dry_run": True,
        }

    # Create the filter
    try:
        client.create_filter(
            criteria={"from": sender},
            add_label_ids=[label_id],
            should_archive=should_archive,
        )
        filter_created = True
    except Exception as exc:  # noqa: BLE001
        print(f"Filter creation failed for {sender}: {exc}", file=sys.stderr)
        filter_created = False

    # Apply the label to existing messages from this sender.
    # H1 idempotency: skip messages that already carry the target label so
    # re-running after a transient failure doesn't burn API quota on no-ops.
    existing_modified = 0
    if ids_needing_label:
        remove_ids = ["INBOX"] if should_archive else None
        for i in range(0, len(ids_needing_label), 500):
            chunk = ids_needing_label[i : i + 500]
            try:
                client.batch_modify_messages(
                    message_ids=chunk,
                    add_label_ids=[label_id],
                    remove_label_ids=remove_ids,
                )
                existing_modified += len(chunk)
            except Exception as exc:  # noqa: BLE001
                print(
                    f"Batch modify failed for chunk {i}: {exc}",
                    file=sys.stderr,
                )

    return {
        "sender": sender,
        "label": label_name,
        "filter_created": filter_created,
        "existing_matched": len(existing),
        "existing_modified": existing_modified,
        "apply_existing": apply_existing,
        "should_archive": should_archive,
        "dry_run": False,
    }


# ─────────────────────────────────────────────
# Phase 4: Count remaining inbox
# ─────────────────────────────────────────────


def count_remaining(client: GmailClient) -> dict:
    """Count how many messages are left in the inbox."""
    result = client.search_messages("in:inbox", max_results=1)
    return {"remaining": result.get("resultSizeEstimate", 0)}


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Initial inbox cleanup for Atlas Inbox Zero.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_archive = sub.add_parser(
        "mass-archive",
        help="Archive every inbox message older than N days.",
    )
    p_archive.add_argument("--older-than-days", type=int, default=90)
    p_archive.add_argument("--dry-run", action="store_true")
    p_archive.add_argument("--execute", action="store_true",
                           help="Actually archive after approval")
    p_archive.add_argument("--approval-id", default=None,
                           help="Approval id from a preview run")

    p_scan = sub.add_parser(
        "scan-senders",
        help="Return senders with >= min_count messages as JSON.",
    )
    p_scan.add_argument("--min-count", type=int, default=5)
    p_scan.add_argument("--max-scan", type=int, default=1000)

    p_filter = sub.add_parser(
        "create-filter",
        help="Create a filter for one sender and apply to existing messages.",
    )
    p_filter.add_argument("--from", dest="sender", required=True)
    p_filter.add_argument("--label", required=True)
    p_filter.add_argument(
        "--apply-existing",
        action="store_true",
        default=True,
        help="Apply the label to existing messages from this sender (default: true).",
    )
    p_filter.add_argument(
        "--no-apply-existing",
        dest="apply_existing",
        action="store_false",
    )
    p_filter.add_argument(
        "--no-archive",
        dest="should_archive",
        action="store_false",
        default=True,
        help="Do NOT skip the inbox — just apply the label.",
    )
    p_filter.add_argument("--dry-run", action="store_true",
                          help="Preview the filter creation and retroactive changes")
    p_filter.add_argument("--execute", action="store_true",
                          help="Actually create the filter after approval")
    p_filter.add_argument("--approval-id", default=None,
                          help="Approval id from a preview run")

    sub.add_parser("count-remaining", help="Print inbox message count as JSON.")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        client = GmailClient()
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: Could not authenticate: {exc}", file=sys.stderr)
        return 1

    if args.command == "mass-archive":
        preview = mass_archive(
            client,
            older_than_days=args.older_than_days,
            dry_run=True,
        )
        command_hint = (
            f"python initial_cleanup.py mass-archive --older-than-days {args.older_than_days} "
            f"--execute --approval-id <approval-id>"
        )
        if args.dry_run or not args.execute:
            request = create_approval_request("initial_cleanup.mass_archive", preview, command_hint=command_hint)
            preview["approval"] = approval_request_payload(request)
            print(render_approval_instructions(request), file=sys.stderr)
            print(json.dumps(preview, indent=2))
            return 0
        try:
            ensure_approved("initial_cleanup.mass_archive", preview, approval_id=args.approval_id)
        except ApprovalValidationError as exc:
            request = create_approval_request("initial_cleanup.mass_archive", preview, command_hint=command_hint)
            preview["approval"] = approval_request_payload(request)
            preview["error"] = str(exc)
            print(render_approval_instructions(request), file=sys.stderr)
            print(json.dumps(preview, indent=2))
            return 2
        result = mass_archive(
            client,
            older_than_days=args.older_than_days,
            dry_run=False,
        )
        print(json.dumps(result, indent=2))
        return 0

    if args.command == "scan-senders":
        result = scan_bulk_senders(
            client,
            min_count=args.min_count,
            max_scan=args.max_scan,
        )
        print(json.dumps(result, indent=2))
        return 0

    if args.command == "create-filter":
        preview = create_bulk_sender_filter(
            client,
            sender=args.sender,
            label_name=args.label,
            apply_existing=args.apply_existing,
            should_archive=args.should_archive,
            dry_run=True,
        )
        archive_flag = "" if args.should_archive else " --no-archive"
        apply_flag = "" if args.apply_existing else " --no-apply-existing"
        command_hint = (
            f"python initial_cleanup.py create-filter --from {args.sender} --label '{args.label}'"
            f"{apply_flag}{archive_flag} --execute --approval-id <approval-id>"
        )
        if args.dry_run or not args.execute:
            request = create_approval_request("initial_cleanup.create_filter", preview, command_hint=command_hint)
            preview["approval"] = approval_request_payload(request)
            print(render_approval_instructions(request), file=sys.stderr)
            print(json.dumps(preview, indent=2))
            return 0
        try:
            ensure_approved("initial_cleanup.create_filter", preview, approval_id=args.approval_id)
        except ApprovalValidationError as exc:
            request = create_approval_request("initial_cleanup.create_filter", preview, command_hint=command_hint)
            preview["approval"] = approval_request_payload(request)
            preview["error"] = str(exc)
            print(render_approval_instructions(request), file=sys.stderr)
            print(json.dumps(preview, indent=2))
            return 2
        result = create_bulk_sender_filter(
            client,
            sender=args.sender,
            label_name=args.label,
            apply_existing=args.apply_existing,
            should_archive=args.should_archive,
            dry_run=False,
        )
        print(json.dumps(result, indent=2))
        return 0

    if args.command == "count-remaining":
        result = count_remaining(client)
        print(json.dumps(result, indent=2))
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
