"""
Inbox Triage Helper
===================
Fetches inbox messages in a form the agent can consume, and applies the
agent's labeling decisions back to Gmail. The decision tree itself is run
by the AGENT (Claude), not this script — judgment calls like
"is this a lead?" or "does this need the exec's input?" belong to the model.

This script is the mechanical layer: fetch, decode, and apply.

Important: ``fetch`` is intentionally one batch at a time. For live Morning
and EOD full triage, the agent should repeat the fetch -> classify ->
apply-batch cycle until the untriaged inbox is clear or the safety cap is hit.

Subcommands:

    fetch        Fetch inbox messages as JSON (for the agent to read and
                 classify). Includes headers, snippet, plain-text body,
                 CC list, and internalDate.

    apply-batch  Apply labels / archive per a JSON decision file written
                 by the agent. Idempotent — safe to re-run.

    count        Quick count of messages matching a query. No bodies.

Usage:

    # Fetch the next batch of up to 100 inbox messages, oldest-first
    python triage_inbox.py fetch --query "in:inbox" --max 100 --order oldest

    # Apply a batch of decisions the agent prepared
    python triage_inbox.py apply-batch --file decisions.json

    # Example decisions.json:
    # [
    #   {"message_id": "abc123", "label": "4-Delegated", "archive": false},
    #   {"message_id": "def456", "label": "2-Read Only", "archive": false},
    #   {"message_id": "ghi789", "label": null, "archive": true}
    # ]

Exit codes:
    0 — success
    1 — auth or fatal failure
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

_SHARED_SCRIPTS = Path(__file__).resolve().parents[2] / "shared" / "scripts"
if str(_SHARED_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SHARED_SCRIPTS))

from atlas_labels import ALL_ATLAS_LABELS, is_atlas_label
from gmail_client import GmailClient
from pre_classifier import pre_classify
from state_store import StateStore
from structured_logger import get_logger


# Phase 5 Fix B — retry config. Module-level so tests can patch to 0.
_REMOVE_LABEL_BACKOFF_SEC = 1.0


def _remove_label_with_retry(
    client: GmailClient, msg_id: str, label_id: str
) -> tuple[bool, str | None]:
    """Try to remove ``label_id`` from ``msg_id``; retry once after a short
    backoff. Returns ``(True, None)`` on success or ``(False, error_str)`` when
    both attempts fail. Never raises — the caller uses the return value to
    decide whether to clear the local ``labelIds`` copy."""
    try:
        client.remove_label(msg_id, label_id)
        return True, None
    except Exception as first_exc:  # noqa: BLE001
        if _REMOVE_LABEL_BACKOFF_SEC > 0:
            time.sleep(_REMOVE_LABEL_BACKOFF_SEC)
        try:
            client.remove_label(msg_id, label_id)
            return True, None
        except Exception as second_exc:  # noqa: BLE001
            return False, f"{type(second_exc).__name__}: {second_exc}"


# ─────────────────────────────────────────────
# FETCH
# ─────────────────────────────────────────────

def fetch_messages(
    client: GmailClient,
    query: str,
    max_messages: int,
    order: str = "newest",
    body_chars: int = 2000,
) -> list[dict[str, Any]]:
    """
    Fetch messages matching query and return a list of JSON-serializable dicts.

    Each record contains everything the agent needs to apply the decision tree:
        id, threadId, internalDate (ms), labelIds, subject, from, to, cc,
        snippet, body_plain (up to body_chars), isUnread.

    Args:
        order: "newest" or "oldest" — determines sort order of the result.
    """
    stubs = client.search_all_messages(query, max_results=max_messages)
    records: list[dict[str, Any]] = []

    # Build a set of Gmail label IDs that correspond to Atlas labels,
    # used for re-triage-on-reply detection below.
    try:
        all_gmail_labels = client.list_labels()
        atlas_label_ids: set[str] = {
            lbl["id"]
            for lbl in all_gmail_labels
            if is_atlas_label(lbl.get("name", ""))
        }
    except Exception:  # noqa: BLE001
        atlas_label_ids = set()

    for stub in stubs:
        try:
            msg = client.read_message(stub["id"], format="full")
        except Exception as exc:  # noqa: BLE001
            records.append({
                "id": stub["id"],
                "threadId": stub.get("threadId"),
                "error": f"read failed: {exc}",
            })
            continue

        headers = client.get_message_headers(msg)
        body = client.get_message_body(msg) or ""
        thread_id = msg.get("threadId")

        # Re-triage on reply: if this message belongs to a thread that already
        # carries an Atlas label, remove the old label so the thread gets
        # re-evaluated through the full decision tree.
        if atlas_label_ids:
            current_msg_labels = set(msg.get("labelIds", []))
            existing_atlas = current_msg_labels & atlas_label_ids
            if existing_atlas and thread_id:
                try:
                    thread = client.read_thread(thread_id, format="minimal")
                    thread_msgs = thread.get("messages", [])
                except Exception:  # noqa: BLE001
                    thread_msgs = []  # can't classify thread — skip re-triage
                if len(thread_msgs) > 1:
                    # Thread has multiple messages — a reply arrived; remove
                    # the old Atlas label so triage can re-evaluate. Retry
                    # once on transient failure; on the second failure keep
                    # the local label so pre_classify skips re-triage this run.
                    log = get_logger()
                    successfully_removed: set[str] = set()
                    for label_id in existing_atlas:
                        ok, err = _remove_label_with_retry(
                            client, msg["id"], label_id
                        )
                        if ok:
                            successfully_removed.add(label_id)
                        else:
                            log.event(
                                "label_remove_failed",
                                msg_id=msg["id"],
                                label=label_id,
                                error=err,
                            )
                    if successfully_removed:
                        msg["labelIds"] = [
                            lid for lid in msg.get("labelIds", [])
                            if lid not in successfully_removed
                        ]

        # Run deterministic pre-classification
        pre_result = pre_classify(
            from_header=headers.get("from", ""),
            subject=headers.get("subject", ""),
            body=body[:2000],
            cc=headers.get("cc", ""),
            label_ids=msg.get("labelIds", []),
        )

        records.append({
            "id": msg["id"],
            "threadId": msg.get("threadId"),
            "internalDate": int(msg.get("internalDate", 0)),
            "labelIds": msg.get("labelIds", []),
            "isUnread": "UNREAD" in msg.get("labelIds", []),
            "subject": headers.get("subject", ""),
            "from": headers.get("from", ""),
            "to": headers.get("to", ""),
            "cc": headers.get("cc", ""),
            "date": headers.get("date", ""),
            "snippet": msg.get("snippet", ""),
            "body_plain": body[:body_chars],
            "body_truncated": len(body) > body_chars,
            "pre_classification": pre_result,
        })

        # M3: emit progress to stderr every 25 records so operators
        # tailing a live run see forward progress, and the orchestrator's
        # captured stderr buffer carries a last-known-position signal even
        # if the 5-minute subprocess timeout fires mid-read.
        if len(records) % 25 == 0:
            try:
                print(
                    f"[triage_inbox] progress: read {len(records)}/{len(stubs)} messages",
                    file=sys.stderr,
                    flush=True,
                )
            except Exception:
                pass

    # Sort by internalDate
    records_with_date = [r for r in records if "internalDate" in r]
    records_without = [r for r in records if "internalDate" not in r]

    if order == "oldest":
        records_with_date.sort(key=lambda r: r["internalDate"])
    else:
        records_with_date.sort(key=lambda r: r["internalDate"], reverse=True)

    return records_with_date + records_without


# ─────────────────────────────────────────────
# APPLY DECISIONS
# ─────────────────────────────────────────────

def apply_decisions(
    client: GmailClient,
    decisions: list[dict[str, Any]],
    store: "StateStore | None" = None,
    mode: str | None = None,
) -> dict[str, Any]:
    """
    Apply a batch of triage decisions.

    Each decision is:
        {
            "message_id": str,
            "label": str | null,      # Atlas label name to apply, or null
            "archive": bool,          # Remove INBOX label
            "remove_labels": [str]    # Optional — label names to remove
        }

    Args:
        store: Optional StateStore for snapshot recording (issue #3).
        mode:  Triage mode label (e.g. "morning") stored with the snapshot.

    Returns a summary with per-label counts and any errors.
    """
    # Pre-resolve label names to IDs so we don't hit list_labels per decision
    label_lookup: dict[str, str] = {}
    for label in client.list_labels():
        label_lookup[label["name"]] = label["id"]
    # Reverse lookup: Gmail label ID → Atlas label name
    id_to_atlas_name: dict[str, str] = {
        lid: name for name, lid in label_lookup.items() if is_atlas_label(name)
    }

    # Read each target message once: needed for both snapshot recording and
    # manual-label protection. Messages that can't be read are tracked so
    # we can skip them consistently downstream.
    current_labels_by_msg: dict[str, list[str]] = {}
    for decision in decisions:
        msg_id = decision.get("message_id")
        if not msg_id or msg_id in current_labels_by_msg:
            continue
        try:
            msg = client.read_message(msg_id, format="minimal")
            current_labels_by_msg[msg_id] = msg.get("labelIds", [])
        except Exception:  # noqa: BLE001
            current_labels_by_msg[msg_id] = []

    # Explicit manual-label protection: preserve Atlas labels only when the
    # state store marks their provenance as source="manual". Labels whose
    # provenance is missing or unknown are eligible for reclassification.
    skipped_manual: list[dict[str, str]] = []
    protected_msg_ids: set[str] = set()
    if store is not None:
        for msg_id, gmail_label_ids in current_labels_by_msg.items():
            for gmail_lid in gmail_label_ids:
                atlas_name = id_to_atlas_name.get(gmail_lid)
                if not atlas_name:
                    continue
                if store.get_label_source(msg_id, atlas_name) == "manual":
                    skipped_manual.append({
                        "message_id": msg_id,
                        "label": atlas_name,
                        "reason": "manual_label_preserved",
                    })
                    protected_msg_ids.add(msg_id)
                    break

    # Record snapshot before modifying any labels (issue #3)
    snapshot_actions = []
    for decision in decisions:
        msg_id = decision.get("message_id")
        new_label = decision.get("label")
        if msg_id in protected_msg_ids:
            continue
        if msg_id and new_label:
            snapshot_actions.append({
                "message_id": msg_id,
                "old_labels": current_labels_by_msg.get(msg_id, []),
                "new_label": new_label,
            })

    session_id = None
    if snapshot_actions and store:
        session_id = store.record_snapshot(mode or "unknown", snapshot_actions)

    counts_by_label: dict[str, int] = {}
    archived = 0
    errors: list[dict[str, str]] = []

    for decision in decisions:
        mid = decision.get("message_id")
        if not mid:
            errors.append({"decision": json.dumps(decision), "error": "missing message_id"})
            continue
        if mid in protected_msg_ids:
            continue

        add_ids: list[str] = []
        remove_ids: list[str] = []

        label_name = decision.get("label")
        if label_name:
            label_id = label_lookup.get(label_name)
            if not label_id:
                errors.append({
                    "message_id": mid,
                    "error": f"unknown label '{label_name}' — run inbox-onboarding first",
                })
                continue
            add_ids.append(label_id)

        for rm_name in decision.get("remove_labels", []) or []:
            rm_id = label_lookup.get(rm_name)
            if rm_id:
                remove_ids.append(rm_id)

        if decision.get("archive"):
            remove_ids.append("INBOX")

        if not add_ids and not remove_ids:
            continue  # no-op decision

        try:
            client.modify_message(mid, add_label_ids=add_ids or None, remove_label_ids=remove_ids or None)
            if label_name:
                counts_by_label[label_name] = counts_by_label.get(label_name, 0) + 1
            if decision.get("archive"):
                archived += 1
            # Record label timestamp in state store
            try:
                _label_store = store if store is not None else StateStore()
                if label_name:
                    _label_store.record_label_applied(mid, label_name)
            except Exception:  # noqa: BLE001
                pass  # state store failure is non-fatal
        except Exception as exc:  # noqa: BLE001
            errors.append({"message_id": mid, "error": str(exc)})

    return {
        "labeled": counts_by_label,
        "archived": archived,
        "errors": errors,
        "processed": len(decisions),
        "session_id": session_id,
        "skipped_manual": skipped_manual,
    }


# ─────────────────────────────────────────────
# COUNT
# ─────────────────────────────────────────────

def count_matching(client: GmailClient, query: str) -> int:
    """Return the count of messages matching a query (capped at 500 for speed)."""
    result = client.search_messages(query, max_results=500)
    # resultSizeEstimate is approximate but good enough for a count
    return result.get("resultSizeEstimate", len(result.get("messages", [])))


# ─────────────────────────────────────────────
# ROLLBACK
# ─────────────────────────────────────────────

def rollback_session(
    client: GmailClient,
    session_id: str,
    store: StateStore,
    force: bool = False,
    max_age_days: int = 7,
) -> dict[str, Any]:
    """
    Reverse all label changes from a triage session.

    For each action recorded in the snapshot:
    - Remove the new label that was applied
    - Re-apply the old labels that were present before triage
    - Clear the corresponding state-store entries

    Returns a summary dict with keys: session_id, reversed, errors.
    """
    snap = store.get_snapshot(session_id)
    if snap and snap.get("rolled_back"):
        return {"session_id": session_id, "reversed": 0, "error": "already rolled back"}

    # M6: refuse to roll back snapshots older than max_age_days. P3's
    # auto-prune normally removes them at session end, but a crashed
    # previous session can leave stale snapshots; restoring labels on
    # messages that may no longer exist is worse than refusing. Operator
    # can pass force=True (CLI: --force) to bypass when they know what
    # they're doing.
    if not force and snap and snap.get("ts") is not None:
        import time as _t
        age_seconds = _t.time() - snap["ts"]
        max_age_seconds = max_age_days * 86400
        if age_seconds > max_age_seconds:
            try:
                get_logger().event(
                    "rollback_rejected_stale_snapshot",
                    session_id=session_id,
                    age_days=round(age_seconds / 86400, 1),
                    max_age_days=max_age_days,
                )
            except Exception:
                pass  # logger failure must not mask the rejection
            return {
                "session_id": session_id,
                "reversed": 0,
                "error": (
                    f"snapshot too old ({round(age_seconds / 86400, 1)} days, "
                    f"max {max_age_days}); pass --force to override"
                ),
            }

    actions = store.get_rollback_actions(session_id)
    if not actions:
        return {"error": f"No snapshot found for session {session_id}", "reversed": 0}

    reversed_count = 0
    errors: list[dict[str, Any]] = []

    for action in actions:
        msg_id = action["message_id"]
        try:
            # Remove the Atlas label that was applied during triage
            new_label = client.find_label_by_name(action["remove_label"])
            if new_label:
                client.remove_label(msg_id, new_label["id"])
                store.remove_label_record(msg_id, action["remove_label"])

            # Re-apply old labels (these were the Gmail label IDs before triage)
            for old_label_id in action["restore_labels"]:
                client.apply_label(msg_id, old_label_id)

            reversed_count += 1
        except Exception as exc:  # noqa: BLE001
            errors.append({"message_id": msg_id, "error": str(exc)})

    store.mark_rolled_back(session_id)
    return {"session_id": session_id, "reversed": reversed_count, "errors": errors}


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description="Inbox triage helper.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_fetch = sub.add_parser("fetch", help="Fetch messages as JSON")
    p_fetch.add_argument("--query", default="in:inbox", help="Gmail search query")
    p_fetch.add_argument("--max", type=int, default=100, help="Max messages")
    p_fetch.add_argument(
        "--order",
        choices=["newest", "oldest"],
        default="newest",
        help="Sort order of returned messages",
    )
    p_fetch.add_argument(
        "--body-chars",
        type=int,
        default=2000,
        help="Max characters of body to include per message",
    )

    p_apply = sub.add_parser("apply-batch", help="Apply a decision batch")
    p_apply.add_argument(
        "--file",
        type=Path,
        required=True,
        help="Path to JSON file with decisions (list of {message_id, label, archive})",
    )

    p_count = sub.add_parser("count", help="Count messages matching a query")
    p_count.add_argument("--query", default="in:inbox", help="Gmail search query")

    p_rollback = sub.add_parser("rollback", help="Reverse a triage session")
    p_rollback.add_argument(
        "--session",
        required=True,
        help="Session ID to rollback (returned by apply-batch)",
    )
    p_rollback.add_argument(
        "--force",
        action="store_true",
        help="Bypass the 7-day max-age guard (M6). Use only when you know "
             "the snapshot is still applicable.",
    )

    args = parser.parse_args()

    try:
        client = GmailClient()
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: could not authenticate: {exc}", file=sys.stderr)
        return 1

    if args.command == "fetch":
        records = fetch_messages(
            client,
            query=args.query,
            max_messages=args.max,
            order=args.order,
            body_chars=args.body_chars,
        )
        print(f"Fetched {len(records)} messages from query: {args.query}", file=sys.stderr)
        print(json.dumps(records, indent=2))
        return 0

    if args.command == "apply-batch":
        if not args.file.exists():
            print(f"ERROR: decisions file not found: {args.file}", file=sys.stderr)
            return 1
        decisions = json.loads(args.file.read_text(encoding="utf-8"))
        if not isinstance(decisions, list):
            print("ERROR: decisions file must contain a JSON list", file=sys.stderr)
            return 1

        result = apply_decisions(client, decisions, store=StateStore(), mode="batch")
        print(
            f"Applied {result['processed']} decisions — "
            f"archived: {result['archived']}, errors: {len(result['errors'])}",
            file=sys.stderr,
        )
        print(json.dumps(result, indent=2))
        return 0

    if args.command == "count":
        count = count_matching(client, args.query)
        print(json.dumps({"query": args.query, "count": count}))
        return 0

    if args.command == "rollback":
        store = StateStore()
        result = rollback_session(client, args.session, store, force=args.force)
        print(json.dumps(result, indent=2))
        return 1 if result.get("error") else 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
