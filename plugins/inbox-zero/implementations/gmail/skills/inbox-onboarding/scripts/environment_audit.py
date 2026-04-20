"""
Environment Audit
=================
Read-only scan of the exec's Gmail environment BEFORE onboarding makes
any changes. Detects:
  - Existing user labels (non-system)
  - Labels that are similar in purpose to Atlas labels (potential merge candidates)
  - Per-similar-label message counts (when --counts is used)
  - Existing filters that could conflict with Atlas (auto-archive, auto-delete)
  - Multiple Inboxes configuration (if detectable)
  - Current inbox size
  - Migration recommendations for three decision modes:
      keep_both, migrate_labels, clean_slate

This script does NOT modify anything. It produces a JSON report that the
onboarding skill presents to the user so they can make informed decisions
before the plugin starts creating labels and filters.

Usage:
    python environment_audit.py [--json] [--verbose] [--counts] [--mode MODE]

Options:
    --json      Output raw JSON only
    --verbose   Include filter details
    --counts    Fetch per-similar-label message counts (extra API calls)
    --mode      Migration mode: keep_both | migrate_labels | clean_slate
                (default: all three shown in recommendations)

Exit codes:
    0 — audit complete
    1 — auth failure
"""

import json
import re
import sys
from pathlib import Path
from typing import Any

_SHARED_SCRIPTS = Path(__file__).resolve().parents[2] / "shared" / "scripts"
if str(_SHARED_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SHARED_SCRIPTS))

from atlas_labels import (
    ACTION_REQUIRED, DELEGATED, FOLLOW_UP, LEADS, READ_ONLY,
    RECEIPTS, REFERENCE, SUBSCRIPTIONS, WAITING_FOR,
)
from gmail_client import GmailClient


# Gmail system labels that we ignore in the audit
SYSTEM_LABELS = {
    "INBOX", "SENT", "DRAFT", "SPAM", "TRASH", "STARRED", "IMPORTANT",
    "UNREAD", "CATEGORY_PERSONAL", "CATEGORY_SOCIAL", "CATEGORY_PROMOTIONS",
    "CATEGORY_UPDATES", "CATEGORY_FORUMS", "CHAT",
}

# Atlas labels and the user-label concepts they map to
ATLAS_LABEL_SYNONYMS: dict[str, list[str]] = {
    ACTION_REQUIRED: [
        "action", "to do", "todo", "to-do", "urgent", "priority",
        "action items", "action required", "needs action", "do",
    ],
    READ_ONLY: [
        "read", "fyi", "info", "informational", "read only", "read-only",
        "newsletters", "news",
    ],
    WAITING_FOR: [
        "waiting", "pending", "waiting on", "waiting for", "awaiting",
        "follow up", "followup",
    ],
    DELEGATED: [
        "delegated", "assigned", "handed off", "team",
    ],
    FOLLOW_UP: [
        "follow up", "followup", "follow-up", "later", "someday",
        "snooze", "remind",
    ],
    RECEIPTS: [
        "receipts", "invoices", "billing", "payments", "financial",
    ],
    SUBSCRIPTIONS: [
        "subscriptions", "newsletters", "marketing", "promotions",
    ],
    REFERENCE: [
        "reference", "archive", "filed", "records", "documents",
    ],
    LEADS: [
        "leads", "prospects", "sales", "opportunities", "pipeline",
    ],
}

# Valid migration modes
VALID_MODES = ("keep_both", "migrate_labels", "clean_slate")


def find_similar_labels(
    existing_names: list[str],
    atlas_labels: list[str] | None = None,
) -> list[dict[str, str]]:
    """
    Find existing labels that are similar in purpose to Atlas labels.
    Returns a list of {existing, atlas_equivalent, status} dicts.
    """
    if atlas_labels is None:
        atlas_labels = list(ATLAS_LABEL_SYNONYMS.keys())

    atlas_set = set(atlas_labels)
    results = []

    for name in existing_names:
        # Skip system labels
        if name in SYSTEM_LABELS:
            continue
        # Skip labels that start with system prefixes
        if name.startswith(("CATEGORY_", "[Imap]/")):
            continue

        # Check for exact Atlas label match
        if name in atlas_set:
            results.append({
                "existing": name,
                "atlas_equivalent": name,
                "status": "exact_match",
            })
            continue

        # Check for synonym match (only against requested atlas_labels)
        name_lower = name.lower().strip()
        for atlas_label in atlas_labels:
            synonyms = ATLAS_LABEL_SYNONYMS.get(atlas_label, [])
            for synonym in synonyms:
                if synonym in name_lower or name_lower in synonym:
                    results.append({
                        "existing": name,
                        "atlas_equivalent": atlas_label,
                        "status": "similar",
                    })
                    break
            else:
                continue
            break

    return results


def _count_messages_for_label(
    client: "GmailClient",
    label_name: str,
    max_results: int = 10000,
) -> int | None:
    """Return an exact count for a label by paginating Gmail results.

    Gmail's `resultSizeEstimate` is not reliable for user-label scoped queries,
    so we page through message ids and count them directly. Counts are capped at
    ``max_results`` to keep audit cost bounded on very large inboxes.
    """
    try:
        label = client.find_label_by_name(label_name)
        if not label:
            return None

        total = 0
        page_token = None
        while total < max_results:
            client._maybe_refresh_token()
            client._limiter.acquire()
            batch_size = min(500, max_results - total)
            result = client._call_api(
                client.service.users().messages().list(
                    userId=client.user_id,
                    labelIds=[label["id"]],
                    maxResults=batch_size,
                    pageToken=page_token,
                )
            )
            messages = result.get("messages", [])
            total += len(messages)
            page_token = result.get("nextPageToken")
            if not page_token or not messages:
                break
        return total
    except Exception:  # noqa: BLE001
        return None


def fetch_label_message_counts(
    client: "GmailClient",
    similar_labels: list[dict[str, str]],
) -> list[dict[str, Any]]:
    """
    Enrich similar_labels entries with message counts.

    For each similar label, queries Gmail for the count of messages
    bearing that label. Returns a new list with an added "message_count"
    field on each entry.

    This makes extra API calls (one per label) — only call when the user
    opts in via --counts.
    """
    enriched = []
    for entry in similar_labels:
        count = _count_messages_for_label(client, entry["existing"])
        enriched.append({**entry, "message_count": count})
    return enriched


def find_conflicting_filters(filters: list[dict]) -> list[dict[str, Any]]:
    """
    Identify filters that could interfere with Atlas triage.

    Risky patterns:
    - Auto-archive (removes INBOX label) — Atlas won't see the email
    - Auto-delete (adds TRASH label) — email is gone
    - Mark as read — Atlas triage checks unread status for midday scans
    - Send to spam — blocks the sender entirely
    """
    conflicts = []

    for f in filters:
        filter_id = f.get("id", "unknown")
        criteria = f.get("criteria", {})
        action = f.get("action", {})

        remove_labels = action.get("removeLabelIds", [])
        add_labels = action.get("addLabelIds", [])

        risk = None
        reason = ""

        if "INBOX" in remove_labels:
            risk = "auto_archive"
            reason = "Removes from inbox — Atlas triage will never see matching emails"
        elif "TRASH" in add_labels:
            risk = "auto_delete"
            reason = "Sends to trash — emails are deleted before Atlas can process them"
        elif "UNREAD" in remove_labels:
            risk = "auto_read"
            reason = "Marks as read — Atlas midday scan uses is:unread and may miss these"

        if risk:
            # Build a human-readable description of what the filter matches
            criteria_desc = []
            if criteria.get("from"):
                criteria_desc.append(f"from: {criteria['from']}")
            if criteria.get("to"):
                criteria_desc.append(f"to: {criteria['to']}")
            if criteria.get("query"):
                criteria_desc.append(f"query: {criteria['query']}")
            if criteria.get("subject"):
                criteria_desc.append(f"subject: {criteria['subject']}")

            conflicts.append({
                "filter_id": filter_id,
                "criteria": criteria,
                "criteria_readable": ", ".join(criteria_desc) if criteria_desc else "unknown",
                "risk": risk,
                "reason": reason,
            })

    return conflicts


def build_mode_recommendations(
    mode: str,
    similar_labels: list[dict[str, Any]],
    conflicting_filters: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Build migration-mode-specific recommendations and action summaries.

    Args:
        mode: One of keep_both, migrate_labels, clean_slate.
        similar_labels: Output of find_similar_labels (optionally enriched with counts).
        conflicting_filters: Output of find_conflicting_filters.

    Returns:
        Dict with "mode", "description", "label_actions", "filter_actions",
        and human-readable "steps".
    """
    label_actions: list[dict[str, str]] = []
    filter_actions: list[dict[str, str]] = []
    steps: list[str] = []

    if mode == "keep_both":
        steps.append("Create all 9 Atlas labels alongside existing labels.")
        steps.append("No label migration — existing labels are untouched.")
        for entry in similar_labels:
            label_actions.append({
                "existing_label": entry["existing"],
                "atlas_equivalent": entry["atlas_equivalent"],
                "action": "keep",
                "detail": "Existing label kept as-is; Atlas equivalent created separately.",
            })
        for cf in conflicting_filters:
            filter_actions.append({
                "filter_id": cf["filter_id"],
                "criteria_readable": cf["criteria_readable"],
                "risk": cf["risk"],
                "action": "backup_and_remove",
                "detail": (
                    "Back up filter to JSON, then remove it. Even in keep-both "
                    "mode, conflicting filters can hide mail from Atlas triage."
                ),
            })
        if conflicting_filters:
            steps.append(
                f"Back up and remove {len(conflicting_filters)} conflicting filter(s)."
            )

    elif mode == "migrate_labels":
        steps.append("Create all 9 Atlas labels.")
        for entry in similar_labels:
            if entry["status"] == "exact_match":
                label_actions.append({
                    "existing_label": entry["existing"],
                    "atlas_equivalent": entry["atlas_equivalent"],
                    "action": "skip",
                    "detail": "Label already matches Atlas name — no migration needed.",
                })
            else:
                count_note = ""
                if entry.get("message_count") is not None:
                    count_note = f" (~{entry['message_count']} messages)"
                label_actions.append({
                    "existing_label": entry["existing"],
                    "atlas_equivalent": entry["atlas_equivalent"],
                    "action": "migrate",
                    "detail": (
                        f"Batch-move messages from '{entry['existing']}' to "
                        f"'{entry['atlas_equivalent']}'{count_note}, then hide "
                        "the old label."
                    ),
                })
        migrate_count = sum(1 for a in label_actions if a["action"] == "migrate")
        if migrate_count:
            steps.append(
                f"Migrate messages from {migrate_count} legacy label(s) to Atlas equivalents."
            )
            steps.append("Hide (not delete) migrated legacy labels.")
        for cf in conflicting_filters:
            filter_actions.append({
                "filter_id": cf["filter_id"],
                "criteria_readable": cf["criteria_readable"],
                "risk": cf["risk"],
                "action": "backup_and_remove",
                "detail": (
                    "Back up filter to JSON, then remove it so Atlas triage "
                    "can see matching emails."
                ),
            })
        if conflicting_filters:
            steps.append(
                f"Back up and remove {len(conflicting_filters)} conflicting filter(s)."
            )

    elif mode == "clean_slate":
        steps.append("Create all 9 Atlas labels.")
        steps.append("Existing labels are left in place but ignored by Atlas.")
        for entry in similar_labels:
            label_actions.append({
                "existing_label": entry["existing"],
                "atlas_equivalent": entry["atlas_equivalent"],
                "action": "ignore",
                "detail": "Existing label left as-is — Atlas starts fresh.",
            })
        for cf in conflicting_filters:
            filter_actions.append({
                "filter_id": cf["filter_id"],
                "criteria_readable": cf["criteria_readable"],
                "risk": cf["risk"],
                "action": "backup_and_remove",
                "detail": (
                    "Back up filter to JSON, then remove it — even in clean-slate "
                    "mode, conflicting filters block Atlas triage."
                ),
            })
        if conflicting_filters:
            steps.append(
                f"Back up and remove {len(conflicting_filters)} conflicting filter(s)."
            )

    return {
        "mode": mode,
        "description": {
            "keep_both": "Keep existing labels untouched. Atlas labels are added alongside.",
            "migrate_labels": "Move messages from legacy labels to Atlas equivalents, then hide legacy labels.",
            "clean_slate": "Start fresh with Atlas labels. Legacy labels are left alone but ignored.",
        }[mode],
        "label_actions": label_actions,
        "filter_actions": filter_actions,
        "steps": steps,
    }


def build_report(
    user_labels: list[str],
    system_labels: list[str],
    filters: list[dict],
    similar_labels: list[dict],
    conflicting_filters: list[dict],
    inbox_count: int,
    mode: str | None = None,
) -> dict[str, Any]:
    """Build the full audit report.

    Args:
        mode: If set, include migration_plan for that mode only.
              If None, include migration_plan for all three modes.
    """
    atlas_labels_present = [s for s in similar_labels if s["status"] == "exact_match"]
    legacy_similar_labels = [s for s in similar_labels if s["status"] == "similar"]

    recommendations = []

    if legacy_similar_labels:
        recommendations.append(
            f"Found {len(legacy_similar_labels)} pre-existing label(s) similar to Atlas labels. "
            "Consider migrating emails from these labels to the Atlas equivalents "
            "during onboarding, or keep both systems side by side."
        )

    if atlas_labels_present:
        recommendations.append(
            f"Detected {len(atlas_labels_present)} Atlas label(s) already present. "
            "Treat these as existing system state, not migration candidates."
        )

    if conflicting_filters:
        recommendations.append(
            f"Found {len(conflicting_filters)} filter(s) that could interfere with Atlas. "
            "Review each one — auto-archive filters can prevent Atlas from seeing emails. "
            "Consider disabling or adjusting them."
        )

    if inbox_count > 1000:
        recommendations.append(
            f"Large inbox ({inbox_count} messages). The initial cleanup will take longer. "
            "Consider a more aggressive archive cutoff (60 days instead of 90)."
        )

    if not recommendations:
        recommendations.append("Clean environment — no conflicts detected. Ready for onboarding.")

    # Build migration plans from true legacy labels only
    if mode:
        migration_plan = build_mode_recommendations(mode, legacy_similar_labels, conflicting_filters)
    else:
        migration_plan = {
            m: build_mode_recommendations(m, legacy_similar_labels, conflicting_filters)
            for m in VALID_MODES
        }

    # Machine-readable action summary
    action_summary = {
        "atlas_label_count": len(atlas_labels_present),
        "legacy_similar_label_count": len(legacy_similar_labels),
        "similar_label_count": len(legacy_similar_labels),
        "conflicting_filter_count": len(conflicting_filters),
        "has_atlas_labels_present": bool(atlas_labels_present),
        "has_legacy_similar_labels": bool(legacy_similar_labels),
        "has_exact_matches": bool(atlas_labels_present),
        "has_similar_matches": bool(legacy_similar_labels),
        "risk_categories": sorted({c["risk"] for c in conflicting_filters}),
        "inbox_size_category": (
            "small" if inbox_count <= 100
            else "medium" if inbox_count <= 1000
            else "large" if inbox_count <= 10000
            else "very_large"
        ),
    }

    return {
        "existing_labels": user_labels,
        "system_labels_found": len(system_labels),
        "user_labels_found": len(user_labels),
        "atlas_labels_present": atlas_labels_present,
        "similar_labels": legacy_similar_labels,
        "conflicting_filters": conflicting_filters,
        "total_filters": len(filters),
        "inbox_count": inbox_count,
        "recommendations": recommendations,
        "migration_plan": migration_plan,
        "action_summary": action_summary,
    }


def run_audit(
    client: "GmailClient",
    fetch_counts: bool = False,
    mode: str | None = None,
) -> dict[str, Any]:
    """Run the full environment audit.

    Args:
        client: Authenticated GmailClient.
        fetch_counts: If True, query message counts per similar label.
        mode: If set, restrict migration_plan to this mode only.
    """
    # 1. Get all labels
    all_labels = client.list_labels()
    system_labels = [l["name"] for l in all_labels if l.get("type") == "system"]
    user_labels = [l["name"] for l in all_labels if l.get("type") == "user"]

    # 2. Find similar labels
    similar = find_similar_labels(user_labels)

    # 2b. Optionally enrich with message counts
    if fetch_counts and similar:
        similar = fetch_label_message_counts(client, similar)

    # 3. Get all filters
    filters = client.list_filters()
    conflicting = find_conflicting_filters(filters)

    # 4. Inbox count
    result = client.search_messages("in:inbox", max_results=1)
    inbox_count = result.get("resultSizeEstimate", 0)

    return build_report(
        user_labels=user_labels,
        system_labels=system_labels,
        filters=filters,
        similar_labels=similar,
        conflicting_filters=conflicting,
        inbox_count=inbox_count,
        mode=mode,
    )


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Audit Gmail environment before onboarding.")
    parser.add_argument("--json", action="store_true", help="Output raw JSON only")
    parser.add_argument("--verbose", action="store_true", help="Include filter details")
    parser.add_argument(
        "--counts", action="store_true",
        help="Fetch per-similar-label message counts (extra API calls)",
    )
    parser.add_argument(
        "--mode", choices=VALID_MODES, default=None,
        help="Show migration plan for a specific mode only (default: all three)",
    )
    args = parser.parse_args()

    try:
        client = GmailClient()
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: Could not authenticate: {exc}", file=sys.stderr)
        return 1

    report = run_audit(client, fetch_counts=args.counts, mode=args.mode)

    if args.json:
        print(json.dumps(report, indent=2))
        return 0

    # Human-readable output
    print("=" * 60)
    print("  Atlas Inbox Zero — Environment Audit")
    print("=" * 60)
    print()
    print(f"  Inbox size: ~{report['inbox_count']} messages")
    print(f"  Existing user labels: {report['user_labels_found']}")
    print(f"  Existing filters: {report['total_filters']}")
    print()

    if report["atlas_labels_present"]:
        print("  ATLAS LABELS ALREADY PRESENT:")
        for s in report["atlas_labels_present"]:
            print(f"    [ATLAS] \"{s['existing']}\"")
        print()

    if report["similar_labels"]:
        print("  LEGACY LABELS SIMILAR TO ATLAS:")
        for s in report["similar_labels"]:
            count_str = ""
            if s.get("message_count") is not None:
                count_str = f" ({s['message_count']} messages)"
            print(f"    [SIMILAR] \"{s['existing']}\" -> Atlas: \"{s['atlas_equivalent']}\"{count_str}")
        print()

    if report["conflicting_filters"]:
        print("  CONFLICTING FILTERS FOUND:")
        for c in report["conflicting_filters"]:
            print(f"    [{c['risk'].upper()}] {c['criteria_readable']}")
            print(f"      {c['reason']}")
        print()

    # Show migration plan(s)
    plan = report["migration_plan"]
    if isinstance(plan, dict) and "mode" in plan:
        # Single mode
        _print_mode_plan(plan)
    elif isinstance(plan, dict):
        # All three modes
        print("  MIGRATION OPTIONS:")
        print()
        for mode_key in VALID_MODES:
            if mode_key in plan:
                _print_mode_plan(plan[mode_key], indent=4)

    print("  RECOMMENDATIONS:")
    for r in report["recommendations"]:
        print(f"    - {r}")
    print()

    return 0


def _print_mode_plan(plan: dict, indent: int = 4) -> None:
    """Print a single migration-mode plan block."""
    pad = " " * indent
    print(f"{pad}[{plan['mode'].upper()}] {plan['description']}")
    for step in plan["steps"]:
        print(f"{pad}  - {step}")
    print()


if __name__ == "__main__":
    sys.exit(main())
