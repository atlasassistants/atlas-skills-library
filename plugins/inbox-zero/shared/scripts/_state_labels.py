"""Label timestamp tracking for StateStore.

Internal module — do not import from outside state_store.py.
Free functions take `data: dict` (the StateStore._data dict) and
`save: Callable[[], None]` (the StateStore.save method).
"""

import time


VALID_SOURCES = {"plugin", "manual", "unknown"}


def record_applied(data, save, message_id, label_name, timestamp=None, source="plugin"):
    """Record when a label was applied to a message."""
    if source not in VALID_SOURCES:
        raise ValueError(f"invalid label source: {source}")
    ts = timestamp or time.time()
    key = f"{message_id}:{label_name}"
    data["labels"][key] = {
        "ts": ts, "message_id": message_id,
        "label": label_name, "source": source,
    }
    save()


def set_source(data, save, message_id, label_name, source, timestamp=None):
    """Set or replace the provenance source for a currently-labeled message."""
    record_applied(data, save, message_id, label_name, timestamp=timestamp, source=source)


def get_applied_at(data, message_id, label_name):
    """Get the timestamp when a label was applied. Returns None if unknown."""
    key = f"{message_id}:{label_name}"
    entry = data["labels"].get(key)
    return entry["ts"] if entry else None


def get_age_days(data, message_id, label_name):
    """Get how many days since the label was applied. Returns None if unknown."""
    ts = get_applied_at(data, message_id, label_name)
    if ts is None:
        return None
    age_seconds = max(0, time.time() - ts)
    return int(age_seconds // (24 * 3600))


def get_source(data, message_id, label_name):
    """Get the source that applied a label ('plugin', 'manual', or 'unknown'). None if missing."""
    key = f"{message_id}:{label_name}"
    entry = data["labels"].get(key)
    return entry.get("source") if entry else None


def remove(data, save, message_id, label_name):
    """Remove a label timestamp record (when label is removed)."""
    key = f"{message_id}:{label_name}"
    data["labels"].pop(key, None)
    save()


def reconcile(data, save, client):
    """
    Sync state store with Gmail's actual label state.

    1. For each Atlas label, fetch messages with that label from Gmail.
    2. Any message with a label not in the state store = provenance unknown.
    3. Any state store entry whose label is no longer in Gmail = stale, clear it.

    Args:
        data: StateStore._data dict
        save: StateStore.save callable
        client: GmailClient instance

    Returns:
        {"new_unknown": N, "new_manual": 0, "cleared_stale": M}
    """
    # Local import preserved from original — atlas_labels is on sys.path
    # via the same path manipulation StateStore callers rely on.
    from atlas_labels import ALL_ATLAS_LABELS, is_atlas_label

    new_unknown = 0
    cleared_stale = 0
    failed_labels: list[str] = []

    gmail_state: set[tuple[str, str]] = set()

    for label_name in ALL_ATLAS_LABELS:
        slug = label_name.lower().replace(" ", "-").replace("/", "-")
        query = f"label:{slug}"
        try:
            stubs = client.search_all_messages(query, max_results=500)
        except Exception as exc:
            failed_labels.append(label_name)
            _log_reconcile_search_failure(label_name, exc)
            continue
        for stub in stubs:
            msg_id = stub["id"]
            gmail_state.add((msg_id, label_name))
            if get_applied_at(data, msg_id, label_name) is None:
                key = f"{msg_id}:{label_name}"
                data["labels"][key] = {
                    "ts": time.time(), "message_id": msg_id,
                    "label": label_name, "source": "unknown",
                }
                new_unknown += 1

    if new_unknown > 0:
        save()

    keys_to_remove = []
    failed_set = set(failed_labels)
    for key, entry in data["labels"].items():
        msg_id = entry["message_id"]
        label_name = entry["label"]
        if label_name in failed_set:
            continue  # can't classify as stale without a successful search
        if is_atlas_label(label_name) and (msg_id, label_name) not in gmail_state:
            keys_to_remove.append(key)

    for key in keys_to_remove:
        del data["labels"][key]
        cleared_stale += 1

    if keys_to_remove:
        save()

    return {
        "new_unknown": new_unknown,
        "new_manual": 0,
        "cleared_stale": cleared_stale,
        "failed_labels": failed_labels,
    }


def _log_reconcile_search_failure(label_name: str, exc: Exception) -> None:
    """Emit a reconcile_label_search_failed event. Never raises."""
    try:
        from structured_logger import get_logger
        get_logger().event(
            "reconcile_label_search_failed",
            label=label_name,
            message=str(exc)[:500],
            error_type=type(exc).__name__,
        )
    except Exception:
        pass
