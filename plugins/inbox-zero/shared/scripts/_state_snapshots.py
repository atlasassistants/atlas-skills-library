"""Snapshot / rollback tracking for StateStore.

Internal module — do not import from outside state_store.py.
"""

import time
from datetime import datetime, timezone


def record(data, save, mode, actions):
    """Record a triage session snapshot before labels are modified.

    Args:
        data: StateStore._data dict
        save: StateStore.save callable
        mode: Triage mode (morning/midday/eod)
        actions: List of {message_id, old_labels, new_label}

    Returns:
        session_id (ISO timestamp string)
    """
    now = datetime.now(timezone.utc)
    session_id = now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond:06d}Z"
    data["snapshots"][session_id] = {
        "session_id": session_id,
        "mode": mode,
        "actions": actions,
        "ts": time.time(),
        "rolled_back": False,
    }
    save()
    return session_id


def get(data, session_id):
    """Get a snapshot by session ID."""
    return data["snapshots"].get(session_id)


def list_all(data):
    """List all snapshots, newest first."""
    snaps = list(data["snapshots"].values())
    snaps.sort(key=lambda s: s.get("ts", 0), reverse=True)
    return snaps


def get_rollback_actions(data, session_id):
    """Get the list of actions needed to reverse a snapshot.

    Returns list of {message_id, restore_labels, remove_label}.
    Empty list if snapshot not found.
    """
    snap = get(data, session_id)
    if not snap:
        return []
    rollback = []
    for action in snap.get("actions", []):
        rollback.append({
            "message_id": action["message_id"],
            "restore_labels": action["old_labels"],
            "remove_label": action["new_label"],
        })
    return rollback


def mark_rolled_back(data, save, session_id):
    """Mark a snapshot as rolled back. Returns True if marked, False if not found."""
    snap = data["snapshots"].get(session_id)
    if snap:
        snap["rolled_back"] = True
        save()
        return True
    return False


def prune(data, save, max_age_days=7):
    """Remove snapshots older than max_age_days."""
    cutoff = time.time() - (max_age_days * 24 * 3600)
    to_remove = [
        sid for sid, snap in data["snapshots"].items()
        if snap.get("ts", 0) < cutoff
    ]
    for sid in to_remove:
        del data["snapshots"][sid]
    if to_remove:
        save()
