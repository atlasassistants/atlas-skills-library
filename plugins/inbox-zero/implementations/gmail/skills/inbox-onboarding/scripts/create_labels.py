"""
Create the 9 Atlas Labels in Gmail
===================================
Creates every label the Atlas Inbox Zero system requires, with the EXACT names
specified in atlas-inbox-rules.md Section 1. Names must not be changed — the
entire plugin depends on these labels existing by these exact names.

Idempotent: rerunning the script creates missing labels and ensures Atlas label
colors are applied to existing ones.

Usage:
    python create_labels.py

Output:
    Prints one line per label (created or already exists) and a final summary.
    Exits 0 on success, 1 if any label failed to create.
"""

import sys
from pathlib import Path

# Import the shared Gmail client
_IMPL_SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"
_SHARED_SCRIPTS = Path(__file__).resolve().parents[5] / "shared" / "scripts"
for _p in (_IMPL_SCRIPTS, _SHARED_SCRIPTS):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from atlas_labels import ALL_ATLAS_LABELS
from atlas_label_colors import color_for_label, label_has_color
from gmail_client import GmailClient


ATLAS_LABELS: list[str] = list(ALL_ATLAS_LABELS)


def create_atlas_labels(
    client: GmailClient,
) -> tuple[list[str], list[str], list[str], list[tuple[str, str]]]:
    """
    Create every Atlas label in Gmail.

    Returns a tuple of (created, recolored, already_correct, errors) where:
        - created: names of labels newly created
        - recolored: names of labels updated to Atlas colors
        - already_correct: names of labels that already existed with the right colors
        - errors: list of (label_name, error_message) for any failures
    """
    created: list[str] = []
    recolored: list[str] = []
    already_correct: list[str] = []
    errors: list[tuple[str, str]] = []

    # Pre-fetch existing labels once so we don't re-list on every change
    existing_by_name = {label["name"]: label for label in client.list_labels()}

    for name in ATLAS_LABELS:
        try:
            desired_color = color_for_label(name)
            existing = existing_by_name.get(name)
            if existing:
                if label_has_color(existing, desired_color):
                    already_correct.append(name)
                    print(f"  [ok]      {name}  (already exists, color ok)")
                else:
                    client.update_label(existing["id"], color=desired_color)
                    recolored.append(name)
                    print(f"  [updated] {name}  (applied Atlas color)")
                continue

            client.create_label(
                name=name,
                label_list_visibility="labelShow",
                message_list_visibility="show",
                color=desired_color,
            )
            created.append(name)
            print(f"  [created] {name}")
        except Exception as exc:  # noqa: BLE001 — surface every failure
            errors.append((name, str(exc)))
            print(f"  [ERROR]   {name}: {exc}")

    return created, recolored, already_correct, errors


def main() -> int:
    print("Atlas Inbox Zero — Label Setup")
    print("=" * 40)
    print(f"Creating {len(ATLAS_LABELS)} labels...\n")

    try:
        client = GmailClient()
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: Could not authenticate with Gmail: {exc}")
        print("Run setup_credentials.py first to configure OAuth.")
        return 1

    profile = client.get_profile()
    print(f"Connected as: {profile.get('emailAddress', 'unknown')}\n")

    created, recolored, already_correct, errors = create_atlas_labels(client)

    print()
    print("=" * 40)
    print(
        "Summary: "
        f"{len(created)} created, "
        f"{len(recolored)} recolored, "
        f"{len(already_correct)} already correct, "
        f"{len(errors)} errors"
    )

    if errors:
        print("\nFailures:")
        for name, err in errors:
            print(f"  - {name}: {err}")
        return 1

    print("\nAll 9 Atlas labels are in place with Atlas colors applied.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
