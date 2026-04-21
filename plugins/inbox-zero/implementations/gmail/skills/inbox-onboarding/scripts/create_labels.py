"""
Create Atlas Labels in Gmail
=============================
Creates the Atlas Inbox Zero label set in Gmail. By default uses the
standard 9 Atlas labels. If a label plan exists at
client-profile/label-plan.json (written by the agent after inbox-audit),
that plan is used instead — allowing sub-labels and adaptations based on
the exec's existing inbox structure.

Idempotent: rerunning creates missing labels and ensures Atlas colors are
applied to existing ones.

Usage:
    python create_labels.py
    python create_labels.py --plan /path/to/label-plan.json

label-plan.json format:
    {"labels": ["1-Action Required", "1-Action Required/Board", "8-Reference/Meetings", ...]}
"""

import json
import sys
from pathlib import Path

_IMPL_SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"
_SHARED_SCRIPTS = Path(__file__).resolve().parents[5] / "shared" / "scripts"
for _p in (_IMPL_SCRIPTS, _SHARED_SCRIPTS):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from atlas_labels import ALL_ATLAS_LABELS
from atlas_label_colors import color_for_label, label_has_color
from gmail_client import GmailClient
from profile_paths import CLIENT_PROFILE_DIR

DEFAULT_PLAN_PATH = CLIENT_PROFILE_DIR / "label-plan.json"


def load_label_plan(plan_path: Path | None = None) -> list[str]:
    path = plan_path or DEFAULT_PLAN_PATH
    if path and path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        labels = data.get("labels", [])
        if labels:
            print(f"Using label plan from: {path} ({len(labels)} labels)")
            return labels
    print(f"No label plan found — using standard 9 Atlas labels.")
    return list(ALL_ATLAS_LABELS)


ATLAS_LABELS: list[str] = []  # populated in main() after args parsed


def create_atlas_labels(
    client: GmailClient,
    labels: list[str],
) -> tuple[list[str], list[str], list[str], list[tuple[str, str]]]:
    created: list[str] = []
    recolored: list[str] = []
    already_correct: list[str] = []
    errors: list[tuple[str, str]] = []

    existing_by_name = {label["name"]: label for label in client.list_labels()}

    for name in labels:
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


def main(argv=None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Create Atlas labels in Gmail.")
    parser.add_argument("--plan", type=Path, default=None, help="Path to label-plan.json from inbox-audit.")
    args = parser.parse_args(argv)

    labels = load_label_plan(args.plan)

    print("Atlas Inbox Zero — Label Setup")
    print("=" * 40)
    print(f"Creating {len(labels)} labels...\n")

    try:
        client = GmailClient()
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: Could not authenticate with Gmail: {exc}")
        print("Run setup_credentials.py first to configure OAuth.")
        return 1

    profile = client.get_profile()
    print(f"Connected as: {profile.get('emailAddress', 'unknown')}\n")

    created, recolored, already_correct, errors = create_atlas_labels(client, labels)

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

    print(f"\nAll {len(labels)} labels are in place.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
