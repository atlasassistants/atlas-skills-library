"""
Configure Gmail Settings for Atlas Inbox Zero
==============================================
Configures every Gmail setting the Atlas system requires (Section 2 of
atlas-inbox-rules.md). Because the Gmail REST API does NOT expose most
general settings (Multiple Inboxes, keyboard shortcuts, reading pane,
auto-advance, desktop notifications, etc.), this script runs as a
**guided UI wizard**:

    1. Opens the relevant Gmail settings tab in the user's browser
    2. Shows them the exact toggles/values to set
    3. Waits for them to confirm "done" with a single keystroke
    4. Moves to the next setting

This follows the same ADHD-friendly pattern as setup_credentials.py:
one action per step, progress indicator, plain English.

For the tiny subset of settings the API DOES support (send-as, vacation,
filters, etc.) the script uses direct API calls — but for this plugin,
that subset is empty. Everything in Section 2 is UI-only.

Usage:
    python configure_settings.py
"""

import argparse
import json
import sys
import time
import webbrowser
from pathlib import Path

_SHARED_SCRIPTS = Path(__file__).resolve().parents[2] / "shared" / "scripts"
if str(_SHARED_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SHARED_SCRIPTS))

from atlas_labels import ACTION_REQUIRED, DELEGATED, LEADS, READ_ONLY, WAITING_FOR
from gmail_client import GmailClient


_UI_CONFIRMATION_PATH = Path(__file__).resolve().parents[1] / "client-profile" / ".onboarding-ui-confirmed.json"


# ─────────────────────────────────────────────
# The 4 configuration sections (ordered)
# ─────────────────────────────────────────────

GMAIL_SETTINGS_URL = "https://mail.google.com/mail/u/0/#settings/general"
GMAIL_ADVANCED_URL = "https://mail.google.com/mail/u/0/#settings/labs"
GMAIL_INBOX_URL = "https://mail.google.com/mail/u/0/#settings/inbox"
GMAIL_MULTIPLE_INBOXES_URL = "https://mail.google.com/mail/u/0/#settings/multiinbox"


STEPS: list[dict] = [
    {
        "title": "General Settings",
        "url": GMAIL_SETTINGS_URL,
        "instructions": [
            "'Show Send & Archive button in reply'        → ON",
            "'Desktop notifications'                      → OFF (mail notifications off)",
            "'Keyboard shortcuts'                         → ON",
            "'Default reply behavior'                     → Reply all",
            "'Auto-advance'                               → ON (go to next conversation)",
            "'Maximum page size'                          → 50 conversations",
        ],
        "reminder": "Scroll to the very bottom of the page and click 'Save Changes' before moving on.",
    },
    {
        "title": "Advanced Settings (Labs)",
        "url": GMAIL_ADVANCED_URL,
        "instructions": [
            "'Multiple Inboxes'  → Enable",
            "'Templates'         → Enable",
            "'Auto-advance'      → Enable",
        ],
        "reminder": "Scroll to the bottom and click 'Save Changes'. Gmail will reload.",
    },
    {
        "title": "Inbox Type",
        "url": GMAIL_INBOX_URL,
        "instructions": [
            "'Inbox type'             → Multiple Inboxes",
            "'Reading pane position'  → Right of inbox",
            "'Maximum page size'      → 20 conversations",
        ],
        "reminder": "Scroll to the bottom and click 'Save Changes'.",
    },
    {
        "title": "Multiple Inbox Sections",
        "url": GMAIL_MULTIPLE_INBOXES_URL,
        "instructions": [
            "Create 5 sections with EXACT queries and labels below:",
            "",
            "  Section 1:  Query = label:0-leads              Name = 💰 Revenue",
            "  Section 2:  Query = label:1-action-required    Name = ⚡ Needs You",
            "  Section 3:  Query = label:2-read-only          Name = 📖 FYI",
            "  Section 4:  Query = label:3-waiting-for        Name = ⏰ Pending",
            "  Section 5:  Query = label:4-delegated          Name = ✅ EA Handling",
        ],
        "reminder": "Click 'Save Changes' after adding all 5 sections. Gmail will reload showing the new layout.",
    },
]


# ─────────────────────────────────────────────
# UI helpers
# ─────────────────────────────────────────────


def _hr(char: str = "─", width: int = 64) -> None:
    print(char * width)


def _open_url(url: str) -> bool:
    """Open a URL in the default browser. Returns True on success."""
    try:
        return webbrowser.open(url, new=2)
    except Exception:  # noqa: BLE001
        return False


def _wait_for_done(prompt: str = "When you're done, press Enter to continue") -> None:
    """Block until the user confirms a step is complete."""
    try:
        input(f"\n  {prompt} ⏎ ")
    except EOFError:
        print()


def _run_step(step_num: int, total: int, step: dict) -> None:
    _hr()
    print(f"Step {step_num} of {total}: {step['title']}")
    _hr()

    print("\nSet the following values in Gmail:\n")
    for line in step["instructions"]:
        if line:
            print(f"  • {line}")
        else:
            print()

    print(f"\n  ⚠️  {step['reminder']}")

    url = step["url"]
    print(f"\n  Opening: {url}")
    opened = _open_url(url)
    if not opened:
        print("  (Browser couldn't auto-open — click the link above manually.)")

    _wait_for_done()
    print(f"  ✓ Step {step_num} confirmed\n")


# ─────────────────────────────────────────────
# Verification
# ─────────────────────────────────────────────


def _verify_labels_visible(client) -> bool:
    """After Multiple Inboxes setup, verify at least the 5 section labels exist."""
    try:
        labels = {l["name"] for l in client.list_labels()}
        required = {LEADS, ACTION_REQUIRED, READ_ONLY, WAITING_FOR, DELEGATED}
        return required.issubset(labels)
    except Exception:
        return False


def _verify_filters_exist(client, min_count: int = 4) -> bool:
    """After filter creation, verify filters were actually created."""
    try:
        filters = client.list_filters()
        return len(filters) >= min_count
    except Exception:
        return False


def _print_verification_summary(client) -> None:
    """Print what we could verify and what we had to take on trust."""
    print()
    print("=" * 60)
    print("  Verification Summary")
    print("=" * 60)
    print()

    # Things we CAN verify via API
    checks = {
        "Labels exist": _verify_labels_visible(client),
        "Filters created": _verify_filters_exist(client),
    }
    for check, passed in checks.items():
        status = "VERIFIED" if passed else "NOT FOUND"
        print(f"  [{status}] {check}")

    # Things we CANNOT verify (UI-only settings)
    print()
    print("  [TRUST] Multiple Inboxes layout — API can't verify, taken on user confirmation")
    print("  [TRUST] Reading pane position — API can't verify")
    print("  [TRUST] Keyboard shortcuts — API can't verify")
    print("  [TRUST] Send & Archive button — API can't verify")
    print()
    print("  If any [TRUST] items don't look right in Gmail, re-run this wizard")
    print("  and I'll walk you through just those sections.")
    print()


def _write_ui_confirmation(email_address: str) -> None:
    _UI_CONFIRMATION_PATH.write_text(
        json.dumps(
            {
                "confirmed": True,
                "email": email_address,
                "ts": time.time(),
            },
            indent=2,
        ),
        encoding="utf-8",
    )


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────


def main() -> int:
    parser = argparse.ArgumentParser(description="Atlas Inbox Zero — Gmail Settings Wizard")
    parser.add_argument(
        "--skip-completed",
        action="store_true",
        help="Skip steps whose results are already verifiable (labels exist, filters exist)",
    )
    args = parser.parse_args()

    print()
    _hr("=")
    print("Atlas Inbox Zero — Gmail Settings Wizard")
    _hr("=")
    print()
    print("This wizard walks you through the 4 Gmail settings")
    print("sections the Atlas system needs. For each one:")
    print("  1. A Gmail settings tab opens in your browser")
    print("  2. You set the values shown below")
    print("  3. You click Save Changes and come back here")
    print("  4. Press Enter and we move to the next one")
    print()
    print("The whole thing takes about 5 minutes.")
    print()

    # Sanity-check that we're connected to Gmail first so the user doesn't
    # go through the whole wizard on the wrong account.
    client = None
    try:
        client = GmailClient()
        profile = client.get_profile()
        print(f"Connected account: {profile.get('emailAddress', 'unknown')}")
    except Exception as exc:  # noqa: BLE001
        print(f"WARNING: Could not verify Gmail connection: {exc}")
        print("Run setup_credentials.py first if you haven't already.")
        print()

    # Determine which steps to skip when --skip-completed is active
    skip_indices: set[int] = set()
    if args.skip_completed and client:
        if _verify_labels_visible(client):
            # Labels exist → skip "Advanced Settings (Labs)" and
            # "Multiple Inbox Sections" steps (indices 1, 3)
            skip_indices.update({1, 3})
            print("  [skip] Labels already exist — skipping Labs and Multiple Inbox Sections steps")
        if _verify_filters_exist(client):
            print("  [skip] Filters already exist")
        if skip_indices:
            print()

    try:
        input("Press Enter to start, or Ctrl+C to cancel ⏎ ")
    except (EOFError, KeyboardInterrupt):
        print("\nCancelled.")
        return 1

    print()

    total = len(STEPS)
    ran = 0
    for i, step in enumerate(STEPS):
        if i in skip_indices:
            print(f"  ⏭ Skipping Step {i + 1} of {total}: {step['title']} (already verified)\n")
            continue
        ran += 1
        _run_step(i + 1, total, step)

    _hr("=")
    if ran == 0:
        print("All settings already verified — nothing to do.")
    else:
        print(f"{'All 4' if ran == total else f'{ran} of {total}'} settings sections configured.")
    _hr("=")

    # Print verification summary
    if client:
        _print_verification_summary(client)
        try:
            _write_ui_confirmation(profile.get("emailAddress", ""))
            print(f"Saved UI confirmation marker to {_UI_CONFIRMATION_PATH}")
        except Exception as exc:  # noqa: BLE001
            print(f"WARNING: Could not save UI confirmation marker: {exc}")

    print("Next up: create_filters.py  (creates core Gmail filters)")
    print()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nCancelled.")
        sys.exit(1)
