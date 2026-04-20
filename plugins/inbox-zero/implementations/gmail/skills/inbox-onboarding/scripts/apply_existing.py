"""
Apply Core Filters to Existing Inbox Messages
===============================================
Gmail filters created via the API only apply to FUTURE messages. This
script retroactively applies the same filter logic to messages already
in the inbox — the equivalent of checking "Also apply filter to matching
conversations" in the Gmail UI.

Run this AFTER create_filters.py during onboarding. It typically clears
40-70% of the inbox on the first run.

Usage:
    python apply_existing.py [--dry-run]
    python apply_existing.py --execute --approval-id <id>

Exit codes:
    0 — success
    1 — auth or fatal failure
    2 — approval required before execute
"""

import json
import sys
from pathlib import Path
from typing import Any

_IMPL_SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"
_SHARED_SCRIPTS = Path(__file__).resolve().parents[5] / "shared" / "scripts"
for _p in (_IMPL_SCRIPTS, _SHARED_SCRIPTS):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from atlas_labels import RECEIPTS, REFERENCE, SUBSCRIPTIONS
from approval_policy import (
    ApprovalValidationError,
    approval_request_payload,
    create_approval_request,
    ensure_approved,
    render_approval_instructions,
)
from gmail_client import GmailClient


# These mirror the core filters from create_filters.py but are scoped
# to "in:inbox" so they only touch messages sitting in the inbox now.
RETROACTIVE_FILTERS: list[dict[str, Any]] = [
    {
        "nickname": "Subscriptions (unsubscribe keyword)",
        "query": 'in:inbox "unsubscribe"',
        "label": SUBSCRIPTIONS,
        "archive": True,
    },
    {
        "nickname": "Receipts / Invoices / Payments",
        "query": "in:inbox (receipt OR invoice OR payment OR billing)",
        "label": RECEIPTS,
        "archive": True,
    },
    {
        "nickname": "Calendar Invites",
        "query": 'in:inbox (filename:ics OR "calendar invitation" OR subject:invitation)',
        "label": REFERENCE,
        "archive": False,  # calendar invites stay visible
    },
    {
        "nickname": "Meeting Recordings (Zoom / Fathom)",
        "query": "in:inbox from:(noreply@zoom.us OR recordings@ OR @fathom.video)",
        "label": REFERENCE,
        "archive": True,
    },
]


def apply_one_filter(
    client: GmailClient,
    query: str,
    label_name: str,
    archive: bool,
    dry_run: bool,
    batch_size: int = 500,
) -> dict[str, Any]:
    """
    Search for messages matching query, apply label, optionally archive.
    Returns a summary dict.
    """
    label = client.find_label_by_name(label_name)
    if not label:
        return {"error": f"Label '{label_name}' not found", "matched": 0, "applied": 0}

    label_id = label["id"]
    messages = client.search_all_messages(query, max_results=5000)
    matched = len(messages)

    if matched == 0 or dry_run:
        return {"matched": matched, "applied": 0, "dry_run": dry_run}

    applied = 0
    for i in range(0, matched, batch_size):
        chunk_ids = [m["id"] for m in messages[i : i + batch_size]]
        try:
            add_ids = [label_id]
            remove_ids = ["INBOX"] if archive else None
            client.batch_modify_messages(
                message_ids=chunk_ids,
                add_label_ids=add_ids,
                remove_label_ids=remove_ids,
            )
            applied += len(chunk_ids)
        except Exception as exc:
            print(f"  ERROR on chunk {i}: {exc}", file=sys.stderr)

    return {"matched": matched, "applied": applied, "dry_run": False}


def apply_all(client: GmailClient, dry_run: bool = False) -> dict[str, Any]:
    """Apply all retroactive filters and return a combined report."""
    results = {}
    total_matched = 0
    total_applied = 0

    for spec in RETROACTIVE_FILTERS:
        nickname = spec["nickname"]
        print(f"  Applying: {nickname}...", file=sys.stderr)

        result = apply_one_filter(
            client,
            query=spec["query"],
            label_name=spec["label"],
            archive=spec["archive"],
            dry_run=dry_run,
        )

        results[nickname] = result
        total_matched += result.get("matched", 0)
        total_applied += result.get("applied", 0)

        status = f"matched {result['matched']}"
        if not dry_run:
            status += f", applied {result.get('applied', 0)}"
        print(f"    {status}", file=sys.stderr)

    return {
        "total_matched": total_matched,
        "total_applied": total_applied,
        "dry_run": dry_run,
        "per_filter": results,
    }


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(
        description="Apply core filter logic to existing inbox messages."
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be filtered without modifying anything")
    parser.add_argument("--execute", action="store_true",
                        help="Actually apply the retroactive changes after approval")
    parser.add_argument("--approval-id", default=None,
                        help="Approval id from a preview run")
    args = parser.parse_args()

    try:
        client = GmailClient()
    except Exception as exc:
        print(f"ERROR: Could not authenticate: {exc}", file=sys.stderr)
        return 1

    profile = client.get_profile()
    print(f"Connected as: {profile.get('emailAddress', 'unknown')}", file=sys.stderr)

    preview = apply_all(client, dry_run=True)
    command_hint = (
        f"python apply_existing.py --execute --approval-id "
        f"<approval-id>"
    )

    if args.dry_run or not args.execute:
        print("\n  DRY RUN — no changes will be made\n", file=sys.stderr)
        request = create_approval_request(
            "apply_existing",
            preview,
            command_hint=command_hint,
        )
        preview["approval"] = approval_request_payload(request)
        print(render_approval_instructions(request), file=sys.stderr)
        print(f"\n  Total: {preview['total_matched']} matched, "
              f"{preview['total_applied']} applied", file=sys.stderr)
        print(json.dumps(preview, indent=2))
        return 0

    try:
        ensure_approved("apply_existing", preview, approval_id=args.approval_id)
    except ApprovalValidationError as exc:
        request = create_approval_request(
            "apply_existing",
            preview,
            command_hint=command_hint,
        )
        preview["approval"] = approval_request_payload(request)
        preview["error"] = str(exc)
        print(render_approval_instructions(request), file=sys.stderr)
        print(json.dumps(preview, indent=2))
        return 2

    result = apply_all(client, dry_run=False)

    print(f"\n  Total: {result['total_matched']} matched, "
          f"{result['total_applied']} applied", file=sys.stderr)

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
