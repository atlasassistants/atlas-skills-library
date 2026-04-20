"""Cadence step tracking for StateStore.

Internal module — do not import from outside state_store.py.
"""

import time


def record_step(data, save, message_id, step, draft_id=None, session_id=None):
    """Record that a cadence step was executed for a message.

    Skips recording if the same step is already present (no overwrite).
    """
    if message_id not in data["cadence"]:
        data["cadence"][message_id] = []

    existing_steps = {s["step"] for s in data["cadence"][message_id]}
    if step in existing_steps:
        return

    data["cadence"][message_id].append({
        "step": step,
        "draft_id": draft_id,
        "ts": time.time(),
        "session_id": session_id,
    })
    save()


def was_fired_this_session(data, message_id, session_id):
    """Check if any cadence step was fired for this message in the given session."""
    steps = data["cadence"].get(message_id, [])
    return any(s.get("session_id") == session_id for s in steps)


def get_executed(data, message_id):
    """Get all executed cadence steps for a message."""
    return list(data["cadence"].get(message_id, []))


def is_executed(data, message_id, step):
    """Check if a specific cadence step has been executed."""
    steps = data["cadence"].get(message_id, [])
    return any(s["step"] == step for s in steps)


def clear_history(data, save, message_id):
    """Clear cadence history for a message (when it leaves 3-Waiting For)."""
    data["cadence"].pop(message_id, None)
    save()
