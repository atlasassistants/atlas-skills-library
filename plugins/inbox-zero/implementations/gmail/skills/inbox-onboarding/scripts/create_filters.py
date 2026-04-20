"""
Create Core Gmail Filters for Atlas Inbox Zero
================================================
Creates every Gmail filter that the Atlas system requires (Section 3 of
atlas-inbox-rules.md). Core filters handle automatic routing of subscriptions,
receipts, calendar invites, and VIP mail.

This script handles the FIXED core filters. Two other filter sources are
handled separately:
    - VIP contacts: add via vip-contacts.md, then call `create_vip_filters`
    - Bulk sender filters: created during initial_cleanup.py

Core filters created:
    1. "unsubscribe" keyword    → 7-Subscriptions (skip inbox)
    2. receipt/invoice/payment  → 6-Receipts/Invoices (skip inbox)
    3. .ics / calendar / invite → 8-Reference
    4. zoom/fathom/recordings   → 8-Reference (skip inbox)

Idempotent: scans existing filters by criteria + action and skips anything
already present.

Usage:
    python create_filters.py
"""

import sys
from pathlib import Path

_SHARED_SCRIPTS = Path(__file__).resolve().parents[2] / "shared" / "scripts"
if str(_SHARED_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SHARED_SCRIPTS))

from atlas_labels import ACTION_REQUIRED, RECEIPTS, REFERENCE, SUBSCRIPTIONS
from gmail_client import GmailClient


# ─────────────────────────────────────────────
# Filter definitions
# ─────────────────────────────────────────────
#
# Each core filter is a dict the script converts into a
# gmail_client.create_filter() call. The `label_name` field names
# the Atlas label to apply — the script resolves it to a label_id.


CORE_FILTERS: list[dict] = [
    {
        "nickname": "Subscriptions (unsubscribe keyword)",
        "criteria": {"query": '"unsubscribe"'},
        "label_name": SUBSCRIPTIONS,
        "should_archive": True,
        "should_mark_read": False,
    },
    {
        "nickname": "Receipts / Invoices / Payments",
        "criteria": {"query": 'receipt OR invoice OR payment OR billing'},
        "label_name": RECEIPTS,
        "should_archive": True,
        "should_mark_read": False,
    },
    {
        "nickname": "Calendar Invites (.ics / calendar / invitation)",
        "criteria": {"query": 'filename:ics OR "calendar invitation" OR subject:invitation'},
        "label_name": REFERENCE,
        "should_archive": False,
        "should_mark_read": False,
    },
    {
        "nickname": "Meeting Recordings (Zoom / Fathom)",
        "criteria": {"query": 'from:(noreply@zoom.us OR recordings@ OR @fathom.video)'},
        "label_name": REFERENCE,
        "should_archive": True,
        "should_mark_read": False,
    },
]


def _criteria_matches(existing: dict, wanted: dict) -> bool:
    """Check if an existing filter criteria dict matches a wanted one."""
    for key, value in wanted.items():
        if existing.get(key) != value:
            return False
    return True


def _build_label_lookup(client: GmailClient) -> dict[str, str]:
    """Return a {label_name: label_id} map of all labels in the account."""
    return {label["name"]: label["id"] for label in client.list_labels()}


def _resolve_label_id(label_lookup: dict[str, str], name: str) -> str:
    """Find a label ID by name. Raises KeyError if the label doesn't exist yet."""
    if name not in label_lookup:
        raise KeyError(
            f"Label '{name}' does not exist in Gmail. "
            f"Run create_labels.py before create_filters.py."
        )
    return label_lookup[name]


def create_core_filters(client: GmailClient) -> tuple[list[str], list[str], list[tuple[str, str]]]:
    """
    Create all core filters. Returns (created, skipped, errors).
    """
    created: list[str] = []
    skipped: list[str] = []
    errors: list[tuple[str, str]] = []

    label_lookup = _build_label_lookup(client)
    existing_filters = client.list_filters()

    for spec in CORE_FILTERS:
        nickname = spec["nickname"]
        try:
            label_id = _resolve_label_id(label_lookup, spec["label_name"])

            # Check if a filter with the same criteria already exists
            already = any(
                _criteria_matches(f.get("criteria", {}), spec["criteria"])
                for f in existing_filters
            )
            if already:
                skipped.append(nickname)
                print(f"  [skip]    {nickname}  (filter already exists)")
                continue

            client.create_filter(
                criteria=spec["criteria"],
                add_label_ids=[label_id],
                should_archive=spec["should_archive"],
                should_mark_read=spec["should_mark_read"],
            )
            created.append(nickname)
            print(f"  [created] {nickname}")
        except Exception as exc:  # noqa: BLE001
            errors.append((nickname, str(exc)))
            print(f"  [ERROR]   {nickname}: {exc}")

    return created, skipped, errors


def _vip_filter_state(
    existing_filters: list[dict],
    email_addr: str,
    action_required_id: str,
) -> tuple[bool, bool]:
    """Return ``(already_covered, has_overlap)`` for a VIP sender.

    ``already_covered`` means an existing filter for this sender already applies
    the Action Required label. ``has_overlap`` means a sender-specific filter
    exists, but it does *not* already enforce the Atlas VIP behavior.
    """
    overlaps = [
        f for f in existing_filters
        if f.get("criteria", {}).get("from", "").lower() == email_addr
    ]
    if not overlaps:
        return False, False

    for filt in overlaps:
        add_ids = filt.get("action", {}).get("addLabelIds", [])
        if action_required_id in add_ids:
            return True, True
    return False, True


def create_vip_filters(
    client: GmailClient,
    vip_emails: list[str],
) -> tuple[list[str], list[str], list[tuple[str, str]]]:
    """
    Create a filter for each VIP contact:
      From: <email>  →  apply 1-Action Required, never spam

    Called after onboarding collects vip-contacts.md. Can also be called
    later to add new VIPs incrementally.
    """
    created: list[str] = []
    skipped: list[str] = []
    errors: list[tuple[str, str]] = []

    label_lookup = _build_label_lookup(client)
    action_required_id = _resolve_label_id(label_lookup, ACTION_REQUIRED)
    existing_filters = client.list_filters()

    for email_addr in vip_emails:
        email_addr = email_addr.strip().lower()
        if not email_addr:
            continue

        criteria = {"from": email_addr}
        try:
            already_covered, has_overlap = _vip_filter_state(
                existing_filters,
                email_addr,
                action_required_id,
            )
            if already_covered:
                skipped.append(email_addr)
                print(f"  [skip]    VIP {email_addr}  (already covered by existing filter)")
                continue

            client.create_filter(
                criteria=criteria,
                add_label_ids=[action_required_id],
                should_never_spam=True,
            )
            created.append(email_addr)
            if has_overlap:
                print(f"  [created] VIP {email_addr}  (overlapping sender filter detected)")
            else:
                print(f"  [created] VIP {email_addr}")
            existing_filters = client.list_filters()
        except Exception as exc:  # noqa: BLE001
            errors.append((email_addr, str(exc)))
            print(f"  [ERROR]   VIP {email_addr}: {exc}")

    return created, skipped, errors


def main() -> int:
    print("Atlas Inbox Zero — Core Filter Setup")
    print("=" * 40)

    try:
        client = GmailClient()
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: Could not authenticate: {exc}")
        return 1

    profile = client.get_profile()
    print(f"Connected as: {profile.get('emailAddress', 'unknown')}\n")

    print(f"Creating {len(CORE_FILTERS)} core filters...\n")
    created, skipped, errors = create_core_filters(client)

    print()
    print("=" * 40)
    print(f"Summary: {len(created)} created, {len(skipped)} already existed, {len(errors)} errors")

    if errors:
        print("\nFailures:")
        for name, err in errors:
            print(f"  - {name}: {err}")
        return 1

    print("\nCore filters are in place.")
    print("Note: VIP contact filters are created separately once vip-contacts.md is populated.")
    print("Note: Bulk sender filters are created during initial_cleanup.py.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
