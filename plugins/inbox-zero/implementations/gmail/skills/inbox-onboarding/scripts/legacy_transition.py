"""
Legacy Transition Tool
======================
Concrete migration tool for mature executive inboxes that already have
labels and filters. Supports three decision modes:

  keep_both       — Atlas labels are added; existing labels stay untouched.
  migrate_labels  — Messages move from legacy labels to Atlas equivalents;
                    legacy labels are hidden (not deleted).
  clean_slate     — Atlas starts fresh; legacy labels are ignored.

All modes handle conflicting Gmail filters safely: back up to JSON
before removal, with a restore path.

Subcommands:
    plan              Dry-run: show what would happen (reads audit JSON or runs live audit)
    backup-filters    Export conflicting filters to a timestamped JSON backup
    remove-conflicts  Remove conflicting filters (requires prior backup)
    restore-filters   Recreate filters from a backup file
    migrate-labels    Batch-move messages from legacy labels to Atlas equivalents

Safety:
  - Every destructive subcommand defaults to --dry-run.
  - Filters are NEVER removed without a backup on disk.
  - No send or delete-email behavior.
  - Idempotent where possible.

Usage:
    python legacy_transition.py plan [--mode MODE] [--audit-json FILE] [--counts]
    python legacy_transition.py backup-filters [--output FILE]
    python legacy_transition.py remove-conflicts [--backup FILE] [--dry-run]
    python legacy_transition.py remove-conflicts [--backup FILE] --execute --approval-id <id>
    python legacy_transition.py restore-filters --backup FILE [--dry-run]
    python legacy_transition.py restore-filters --backup FILE --execute --approval-id <id>
    python legacy_transition.py migrate-labels --mode migrate_labels [--dry-run] [--batch-size N]
    python legacy_transition.py migrate-labels --mode migrate_labels --execute --approval-id <id>

Exit codes:
    0 — success
    1 — error (auth, missing backup, etc.)
    2 — dry-run completed or approval required (no changes made)
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_SHARED_SCRIPTS = Path(__file__).resolve().parents[2] / "shared" / "scripts"
if str(_SHARED_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SHARED_SCRIPTS))

from runtime_paths import ensure_runtime_paths

ensure_runtime_paths()

from approval_policy import (
    ApprovalValidationError,
    approval_request_payload,
    create_approval_request,
    ensure_approved,
    render_approval_instructions,
)
from gmail_client import GmailClient
from structured_logger import get_logger

# Paths
_PLUGIN_ROOT = Path(__file__).resolve().parents[2]
_BACKUPS_DIR = _PLUGIN_ROOT / "client-profile" / "backups"

# Re-use audit logic
_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from environment_audit import (
    find_conflicting_filters,
    find_similar_labels,
    fetch_label_message_counts,
    VALID_MODES,
)


# ─────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────

def _ensure_backups_dir() -> Path:
    """Create the backups directory if it doesn't exist."""
    _BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    return _BACKUPS_DIR


def _backup_path(prefix: str = "filters") -> Path:
    """Generate a timestamped backup filename."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return _ensure_backups_dir() / f"{prefix}-backup-{ts}.json"


def _load_backup(path: Path) -> list[dict]:
    """Load a filter backup file. Raises on missing/corrupt."""
    if not path.exists():
        raise FileNotFoundError(f"Backup not found: {path}")
    with open(path) as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"Expected a JSON array in backup file: {path}")
    return data


def _find_latest_backup(prefix: str = "filters") -> Path | None:
    """Find the most recent backup file matching prefix, or None."""
    if not _BACKUPS_DIR.exists():
        return None
    candidates = sorted(
        _BACKUPS_DIR.glob(f"{prefix}-backup-*.json"),
        reverse=True,
    )
    return candidates[0] if candidates else None


def _search_all_messages_by_label_id(
    client: "GmailClient",
    label_id: str,
    max_results: int = 10000,
) -> list[dict[str, Any]]:
    """Search messages by exact Gmail label id with pagination."""
    all_messages: list[dict[str, Any]] = []
    page_token = None

    while len(all_messages) < max_results:
        client._maybe_refresh_token()
        client._limiter.acquire()
        batch_size = min(500, max_results - len(all_messages))
        result = client._call_api(
            client.service.users().messages().list(
                userId=client.user_id,
                labelIds=[label_id],
                maxResults=batch_size,
                pageToken=page_token,
            )
        )
        all_messages.extend(result.get("messages", []))
        page_token = result.get("nextPageToken")
        if not page_token:
            break

    return all_messages[:max_results]


def _remove_conflicts_preview(
    current_filters: list[dict[str, Any]],
    backup_path: Path,
    backup_data: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build a stable preview summary for conflicting-filter removal."""
    backup_ids = {f.get("id") for f in backup_data if f.get("id")}
    current_ids = {f.get("id") for f in current_filters}
    to_remove = []
    for filt in current_filters:
        fid = filt.get("id")
        if fid not in backup_ids:
            continue
        criteria = filt.get("criteria", {})
        desc = criteria.get("from") or criteria.get("query") or criteria.get("subject") or str(criteria)
        to_remove.append({"filter_id": fid, "criteria": desc})
    already_gone = sorted(backup_ids - current_ids)
    return {
        "backup_path": str(backup_path),
        "to_remove_count": len(to_remove),
        "to_remove": to_remove,
        "already_gone_count": len(already_gone),
        "already_gone": already_gone,
    }


def _restore_filters_preview(
    current_filters: list[dict[str, Any]],
    backup_data: list[dict[str, Any]],
    backup_path: Path,
) -> dict[str, Any]:
    """Build a stable preview summary for filter restore."""
    current_filter_fingerprints = set()
    for f in current_filters:
        fingerprint = json.dumps(
            {
                "criteria": f.get("criteria", {}),
                "action": f.get("action", {}),
            },
            sort_keys=True,
        )
        current_filter_fingerprints.add(fingerprint)

    to_restore = []
    skipped = 0
    for bf in backup_data:
        fingerprint = json.dumps(
            {
                "criteria": bf.get("criteria", {}),
                "action": bf.get("action", {}),
            },
            sort_keys=True,
        )
        if fingerprint in current_filter_fingerprints:
            skipped += 1
        else:
            to_restore.append({
                "criteria": bf.get("criteria", {}),
                "action": bf.get("action", {}),
            })
    return {
        "backup_path": str(backup_path),
        "to_restore_count": len(to_restore),
        "to_restore": to_restore,
        "skipped_count": skipped,
    }


def _migration_preview(client: "GmailClient") -> dict[str, Any]:
    """Build a stable preview summary for legacy label migration."""
    all_labels = client.list_labels()
    user_labels = [l["name"] for l in all_labels if l.get("type") == "user"]
    label_by_name = {l["name"]: l for l in all_labels}
    similar = find_similar_labels(user_labels)
    to_migrate = [s for s in similar if s["status"] == "similar"]

    label_plans = []
    for entry in to_migrate:
        legacy_name = entry["existing"]
        atlas_name = entry["atlas_equivalent"]
        legacy_label = label_by_name.get(legacy_name)
        atlas_label = label_by_name.get(atlas_name)
        if not legacy_label or not atlas_label:
            label_plans.append({
                "legacy_label": legacy_name,
                "atlas_label": atlas_name,
                "message_count": 0,
                "ready": False,
            })
            continue
        messages = _search_all_messages_by_label_id(client, legacy_label["id"], max_results=10000)
        label_plans.append({
            "legacy_label": legacy_name,
            "atlas_label": atlas_name,
            "message_count": len(messages),
            "ready": True,
        })

    return {
        "mode": "migrate_labels",
        "label_plan_count": len(label_plans),
        "label_plans": label_plans,
        "total_messages": sum(item["message_count"] for item in label_plans),
    }


# ─────────────────────────────────────────────────────
# Subcommand: plan
# ─────────────────────────────────────────────────────

def cmd_plan(args) -> int:
    """Show a dry-run transition plan from audit data or a live audit."""
    log = get_logger()

    # Load or run audit
    if args.audit_json:
        audit_path = Path(args.audit_json)
        if not audit_path.exists():
            print(f"ERROR: Audit file not found: {audit_path}", file=sys.stderr)
            return 1
        with open(audit_path) as f:
            audit = json.load(f)
        atlas_labels_present = audit.get("atlas_labels_present", [])
        similar = audit.get("similar_labels", [])
        conflicting = audit.get("conflicting_filters", [])
    else:
        try:
            client = GmailClient()
        except Exception as exc:  # noqa: BLE001
            print(f"ERROR: Could not authenticate: {exc}", file=sys.stderr)
            return 1

        all_labels = client.list_labels()
        user_labels = [l["name"] for l in all_labels if l.get("type") == "user"]
        all_similar = find_similar_labels(user_labels)
        if args.counts and all_similar:
            all_similar = fetch_label_message_counts(client, all_similar)
        atlas_labels_present = [s for s in all_similar if s.get("status") == "exact_match"]
        similar = [s for s in all_similar if s.get("status") == "similar"]
        filters = client.list_filters()
        conflicting = find_conflicting_filters(filters)

    modes = [args.mode] if args.mode else list(VALID_MODES)

    # Import the recommendation builder from the enhanced audit
    from environment_audit import build_mode_recommendations

    plans = {}
    for mode in modes:
        plans[mode] = build_mode_recommendations(mode, similar, conflicting)

    if args.json:
        print(json.dumps({
            "atlas_labels_present": atlas_labels_present,
            "plans": plans,
        }, indent=2))
    else:
        if atlas_labels_present:
            print("\nAtlas labels already present:")
            for item in atlas_labels_present:
                print(f"  - {item['existing']}")
        for mode, plan in plans.items():
            print(f"\n{'=' * 50}")
            print(f"  MODE: {mode.upper()}")
            print(f"  {plan['description']}")
            print(f"{'=' * 50}")
            if plan["steps"]:
                print("\n  Steps:")
                for i, step in enumerate(plan["steps"], 1):
                    print(f"    {i}. {step}")
            if plan["label_actions"]:
                print("\n  Label actions:")
                for la in plan["label_actions"]:
                    print(f"    [{la['action'].upper()}] {la['existing_label']} -> {la['atlas_equivalent']}")
                    print(f"      {la['detail']}")
            if plan["filter_actions"]:
                print("\n  Filter actions:")
                for fa in plan["filter_actions"]:
                    print(f"    [{fa['action'].upper()}] {fa['criteria_readable']}")
                    print(f"      {fa['detail']}")
            print()

    log.event(
        "legacy_transition_plan",
        modes=modes,
        similar=len(similar),
        atlas_labels_present=len(atlas_labels_present),
        conflicts=len(conflicting),
    )
    return 0


# ─────────────────────────────────────────────────────
# Subcommand: backup-filters
# ─────────────────────────────────────────────────────

def cmd_backup_filters(args) -> int:
    """Export conflicting filters to a timestamped JSON backup."""
    log = get_logger()

    try:
        client = GmailClient()
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: Could not authenticate: {exc}", file=sys.stderr)
        return 1

    filters = client.list_filters()
    conflicting = find_conflicting_filters(filters)

    if not conflicting:
        print("No conflicting filters found — nothing to back up.")
        return 0

    # Build backup payload: full filter resources (not just the conflict metadata)
    conflict_ids = {c["filter_id"] for c in conflicting}
    backup_filters = [f for f in filters if f.get("id") in conflict_ids]

    out_path = Path(args.output) if args.output else _backup_path("filters")
    _ensure_backups_dir()
    with open(out_path, "w") as f:
        json.dump(backup_filters, f, indent=2)

    print(f"Backed up {len(backup_filters)} conflicting filter(s) to:")
    print(f"  {out_path}")
    for c in conflicting:
        print(f"  [{c['risk'].upper()}] {c['criteria_readable']}")

    log.event(
        "legacy_transition_backup",
        count=len(backup_filters),
        path=str(out_path),
    )
    return 0


# ─────────────────────────────────────────────────────
# Subcommand: remove-conflicts
# ─────────────────────────────────────────────────────

def cmd_remove_conflicts(args) -> int:
    """Remove conflicting filters. Requires a backup on disk first."""
    log = get_logger()

    # Resolve backup file
    if args.backup:
        backup_path = Path(args.backup)
    else:
        backup_path = _find_latest_backup("filters")

    if not backup_path or not backup_path.exists():
        print(
            "ERROR: No backup found. Run 'backup-filters' first.\n"
            "  Safety rule: filters are never removed without a backup on disk.",
            file=sys.stderr,
        )
        return 1

    backup_data = _load_backup(backup_path)
    backup_ids = {f.get("id") for f in backup_data if f.get("id")}

    if not backup_ids:
        print("ERROR: Backup file contains no filter IDs.", file=sys.stderr)
        return 1

    try:
        client = GmailClient()
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: Could not authenticate: {exc}", file=sys.stderr)
        return 1

    # Verify the backed-up filters still exist
    current_filters = client.list_filters()
    preview = _remove_conflicts_preview(current_filters, backup_path, backup_data)
    to_remove = {item["filter_id"] for item in preview["to_remove"]}

    if preview["already_gone_count"]:
        print(f"  Note: {preview['already_gone_count']} backed-up filter(s) already removed (idempotent).")

    if not to_remove:
        print("No conflicting filters to remove — all already gone.")
        return 0

    command_hint = (
        f"python legacy_transition.py remove-conflicts --backup {backup_path} "
        f"--execute --approval-id <approval-id>"
    )
    if args.dry_run:
        request = create_approval_request(
            "legacy_transition.remove_conflicts",
            preview,
            command_hint=command_hint,
        )
        print(f"DRY RUN: Would remove {preview['to_remove_count']} conflicting filter(s):")
        for item in preview["to_remove"]:
            print(f"  - {item['filter_id']}: {item['criteria']}")
        print(f"\nBackup verified at: {backup_path}")
        print(render_approval_instructions(request), file=sys.stderr)
        print(json.dumps({"preview": preview, "approval": approval_request_payload(request)}, indent=2))
        return 2

    try:
        ensure_approved(
            "legacy_transition.remove_conflicts",
            preview,
            approval_id=args.approval_id,
        )
    except ApprovalValidationError as exc:
        request = create_approval_request(
            "legacy_transition.remove_conflicts",
            preview,
            command_hint=command_hint,
        )
        print(render_approval_instructions(request), file=sys.stderr)
        print(json.dumps({
            "preview": preview,
            "approval": approval_request_payload(request),
            "error": str(exc),
        }, indent=2))
        return 2

    # Actually remove
    removed = 0
    errors = []
    for fid in to_remove:
        try:
            client.delete_filter(fid)
            removed += 1
        except Exception as exc:  # noqa: BLE001
            errors.append({"filter_id": fid, "error": str(exc)})

    print(f"Removed {removed}/{len(to_remove)} conflicting filter(s).")
    if errors:
        print(f"  {len(errors)} error(s):")
        for e in errors:
            print(f"    {e['filter_id']}: {e['error']}")

    print(f"Restore with: python legacy_transition.py restore-filters --backup {backup_path}")

    log.event(
        "legacy_transition_remove_conflicts",
        removed=removed,
        errors=len(errors),
        backup=str(backup_path),
    )
    return 1 if errors else 0


# ─────────────────────────────────────────────────────
# Subcommand: restore-filters
# ─────────────────────────────────────────────────────

def cmd_restore_filters(args) -> int:
    """Recreate filters from a backup file."""
    log = get_logger()

    backup_path = Path(args.backup)
    backup_data = _load_backup(backup_path)

    if not backup_data:
        print("Backup file is empty — nothing to restore.")
        return 0

    try:
        client = GmailClient()
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: Could not authenticate: {exc}", file=sys.stderr)
        return 1

    # Check which filters already exist (idempotency: skip duplicates by criteria)
    current_filters = client.list_filters()
    preview = _restore_filters_preview(current_filters, backup_data, backup_path)
    current_filter_fingerprints = set()
    for f in current_filters:
        fingerprint = json.dumps(
            {
                "criteria": f.get("criteria", {}),
                "action": f.get("action", {}),
            },
            sort_keys=True,
        )
        current_filter_fingerprints.add(fingerprint)

    command_hint = (
        f"python legacy_transition.py restore-filters --backup {backup_path} "
        f"--execute --approval-id <approval-id>"
    )
    if args.dry_run:
        request = create_approval_request(
            "legacy_transition.restore_filters",
            preview,
            command_hint=command_hint,
        )
        print(
            f"DRY RUN: Would restore {preview['to_restore_count']} filter(s), "
            f"skip {preview['skipped_count']} already-existing."
        )
        print(render_approval_instructions(request), file=sys.stderr)
        print(json.dumps({"preview": preview, "approval": approval_request_payload(request)}, indent=2))
        return 2

    try:
        ensure_approved(
            "legacy_transition.restore_filters",
            preview,
            approval_id=args.approval_id,
        )
    except ApprovalValidationError as exc:
        request = create_approval_request(
            "legacy_transition.restore_filters",
            preview,
            command_hint=command_hint,
        )
        print(render_approval_instructions(request), file=sys.stderr)
        print(json.dumps({
            "preview": preview,
            "approval": approval_request_payload(request),
            "error": str(exc),
        }, indent=2))
        return 2

    restored = 0
    skipped = 0
    errors = []
    for bf in backup_data:
        criteria = bf.get("criteria", {})
        action = bf.get("action", {})
        fingerprint = json.dumps(
            {
                "criteria": criteria,
                "action": action,
            },
            sort_keys=True,
        )

        if fingerprint in current_filter_fingerprints:
            skipped += 1
            continue

        try:
            client.create_filter(
                criteria=criteria,
                add_label_ids=action.get("addLabelIds"),
                remove_label_ids=action.get("removeLabelIds"),
            )
            restored += 1
            current_filter_fingerprints.add(fingerprint)
        except Exception as exc:  # noqa: BLE001
            errors.append({"criteria": criteria, "error": str(exc)})

    print(f"Restored {restored} filter(s), skipped {skipped} (already exist).")
    if errors:
        print(f"  {len(errors)} error(s):")
        for e in errors:
            print(f"    {e['criteria']}: {e['error']}")

    log.event(
        "legacy_transition_restore",
        restored=restored,
        skipped=skipped,
        errors=len(errors),
        backup=str(backup_path),
    )
    return 1 if errors else 0


# ─────────────────────────────────────────────────────
# Subcommand: migrate-labels
# ─────────────────────────────────────────────────────

def cmd_migrate_labels(args) -> int:
    """Batch-move messages from legacy labels to Atlas equivalents."""
    log = get_logger()

    if args.mode != "migrate_labels":
        print(
            "ERROR: migrate-labels only runs in migrate_labels mode.\n"
            "  Pass --mode migrate_labels explicitly.",
            file=sys.stderr,
        )
        return 1

    try:
        client = GmailClient()
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: Could not authenticate: {exc}", file=sys.stderr)
        return 1

    preview = _migration_preview(client)
    if not preview["label_plans"]:
        print("No similar labels found that need migration.")
        return 0

    command_hint = (
        "python legacy_transition.py migrate-labels --mode migrate_labels "
        "--execute --approval-id <approval-id>"
    )
    if args.dry_run:
        request = create_approval_request(
            "legacy_transition.migrate_labels",
            preview,
            command_hint=command_hint,
        )
        for item in preview["label_plans"]:
            print(
                f"  DRY RUN: '{item['legacy_label']}' -> '{item['atlas_label']}': "
                f"{item['message_count']} message(s) would be migrated"
            )
        print("\nDRY RUN complete. No changes made.")
        print(render_approval_instructions(request), file=sys.stderr)
        print(json.dumps({"preview": preview, "approval": approval_request_payload(request)}, indent=2))
        return 2

    try:
        ensure_approved(
            "legacy_transition.migrate_labels",
            preview,
            approval_id=args.approval_id,
        )
    except ApprovalValidationError as exc:
        request = create_approval_request(
            "legacy_transition.migrate_labels",
            preview,
            command_hint=command_hint,
        )
        print(render_approval_instructions(request), file=sys.stderr)
        print(json.dumps({
            "preview": preview,
            "approval": approval_request_payload(request),
            "error": str(exc),
        }, indent=2))
        return 2

    # Discover similar labels
    all_labels = client.list_labels()
    user_labels = [l["name"] for l in all_labels if l.get("type") == "user"]
    label_by_name = {l["name"]: l for l in all_labels}
    similar = find_similar_labels(user_labels)
    to_migrate = [s for s in similar if s["status"] == "similar"]

    batch_size = args.batch_size
    total_migrated = 0
    total_errors = 0

    for entry in to_migrate:
        legacy_name = entry["existing"]
        atlas_name = entry["atlas_equivalent"]

        legacy_label = label_by_name.get(legacy_name)
        atlas_label = label_by_name.get(atlas_name)

        if not legacy_label:
            print(f"  SKIP: Legacy label '{legacy_name}' not found.", file=sys.stderr)
            continue
        if not atlas_label:
            print(f"  SKIP: Atlas label '{atlas_name}' not found — create labels first.", file=sys.stderr)
            continue

        legacy_id = legacy_label["id"]
        atlas_id = atlas_label["id"]

        # Find messages with the legacy label via exact Gmail label id
        messages = _search_all_messages_by_label_id(client, legacy_id, max_results=10000)

        if not messages:
            print(f"  '{legacy_name}' -> '{atlas_name}': 0 messages (nothing to migrate)")
            continue

        # Batch-modify: add Atlas label, remove legacy label
        migrated = 0
        label_errors = 0
        for i in range(0, len(messages), batch_size):
            batch = [m["id"] for m in messages[i : i + batch_size]]
            try:
                client.batch_modify_messages(
                    batch,
                    add_label_ids=[atlas_id],
                    remove_label_ids=[legacy_id],
                )
                migrated += len(batch)
                print(f"    Migrated {migrated}/{len(messages)} from '{legacy_name}'...", file=sys.stderr)
            except Exception as exc:  # noqa: BLE001
                print(f"    ERROR migrating batch: {exc}", file=sys.stderr)
                total_errors += 1
                label_errors += 1

        total_migrated += migrated
        print(f"  '{legacy_name}' -> '{atlas_name}': {migrated}/{len(messages)} migrated")

        if label_errors or migrated != len(messages):
            print(
                f"    WARNING: Legacy label '{legacy_name}' not hidden because migration was partial.",
                file=sys.stderr,
            )
            continue

        # Hide the legacy label (labelHide) — don't delete
        try:
            client.hide_label(legacy_id)
            print(f"    Hidden legacy label '{legacy_name}' from label list.")
        except Exception as exc:  # noqa: BLE001
            print(f"    WARNING: Could not hide label '{legacy_name}': {exc}", file=sys.stderr)

    print(f"\nMigration complete: {total_migrated} message(s) migrated, {total_errors} error(s).")
    log.event(
        "legacy_transition_migrate",
        migrated=total_migrated,
        errors=total_errors,
    )
    return 1 if total_errors else 0


# ─────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────

def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Legacy inbox transition tool for Atlas Inbox Zero.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  # Show transition plan for all modes (dry-run, no changes)\n"
            "  python legacy_transition.py plan\n\n"
            "  # Show plan for migrate_labels mode with message counts\n"
            "  python legacy_transition.py plan --mode migrate_labels --counts\n\n"
            "  # Back up conflicting filters\n"
            "  python legacy_transition.py backup-filters\n\n"
            "  # Remove conflicts (preview first, then approve)\n"
            "  python legacy_transition.py remove-conflicts --dry-run\n"
            "  python legacy_transition.py remove-conflicts --execute --approval-id <id>\n\n"
            "  # Restore from backup if something goes wrong\n"
            "  python legacy_transition.py restore-filters --backup client-profile/backups/filters-backup-20260416T120000Z.json --dry-run\n"
            "  python legacy_transition.py restore-filters --backup client-profile/backups/filters-backup-20260416T120000Z.json --execute --approval-id <id>\n\n"
            "  # Migrate labels (preview first, then approve)\n"
            "  python legacy_transition.py migrate-labels --mode migrate_labels --dry-run\n"
            "  python legacy_transition.py migrate-labels --mode migrate_labels --execute --approval-id <id>\n"
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # plan
    p_plan = sub.add_parser("plan", help="Dry-run: show what would happen")
    p_plan.add_argument("--mode", choices=VALID_MODES, default=None)
    p_plan.add_argument("--audit-json", default=None, help="Path to a saved audit JSON file")
    p_plan.add_argument("--counts", action="store_true", help="Fetch per-label message counts")
    p_plan.add_argument("--json", action="store_true", help="Output raw JSON")

    # backup-filters
    p_backup = sub.add_parser("backup-filters", help="Export conflicting filters to JSON")
    p_backup.add_argument("--output", default=None, help="Custom output path (default: timestamped)")

    # remove-conflicts
    p_remove = sub.add_parser("remove-conflicts", help="Remove conflicting filters (backup required)")
    p_remove.add_argument("--backup", default=None, help="Path to backup file (default: latest)")
    p_remove.add_argument("--dry-run", action="store_true", default=True, help="Preview only (default)")
    p_remove.add_argument("--execute", action="store_true", help="Actually remove (overrides --dry-run)")
    p_remove.add_argument("--approval-id", default=None, help="Approval id from preview")

    # restore-filters
    p_restore = sub.add_parser("restore-filters", help="Recreate filters from backup")
    p_restore.add_argument("--backup", required=True, help="Path to backup file")
    p_restore.add_argument("--dry-run", action="store_true", default=True, help="Preview only (default)")
    p_restore.add_argument("--execute", action="store_true", help="Actually restore (overrides --dry-run)")
    p_restore.add_argument("--approval-id", default=None, help="Approval id from preview")

    # migrate-labels
    p_migrate = sub.add_parser("migrate-labels", help="Batch-move messages to Atlas labels")
    p_migrate.add_argument("--mode", choices=VALID_MODES, required=True)
    p_migrate.add_argument("--dry-run", action="store_true", default=True, help="Preview only (default)")
    p_migrate.add_argument("--execute", action="store_true", help="Actually migrate (overrides --dry-run)")
    p_migrate.add_argument("--approval-id", default=None, help="Approval id from preview")
    p_migrate.add_argument("--batch-size", type=int, default=100, help="Messages per batch (default: 100)")

    args = parser.parse_args()

    # --execute overrides --dry-run for destructive commands
    if hasattr(args, "execute") and args.execute:
        args.dry_run = False

    dispatch = {
        "plan": cmd_plan,
        "backup-filters": cmd_backup_filters,
        "remove-conflicts": cmd_remove_conflicts,
        "restore-filters": cmd_restore_filters,
        "migrate-labels": cmd_migrate_labels,
    }

    return dispatch[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
