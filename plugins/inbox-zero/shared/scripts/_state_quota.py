"""API-call quota tracking for StateStore.

Internal module — do not import from outside state_store.py.

Data shape: data["api_calls"] is a list of two-element lists [ts, count].
JSON has no tuple, so list-of-list is what round-trips cleanly.
"""


def record_call(data, save, count, ts):
    """Append a single (ts, count) entry. O(1). Called by QuotaTracker on
    every Gmail API hit."""
    data["api_calls"].append([float(ts), int(count)])
    save()


def get_calls_last_24h(data, now):
    """Sum counts of entries whose ts is >= now - 24h."""
    cutoff = now - (24 * 3600)
    return sum(count for ts, count in data["api_calls"] if ts >= cutoff)


def prune(data, save, cutoff_ts):
    """Drop entries older than cutoff_ts. Called by orchestrator at session
    end with cutoff_ts = now - 24h."""
    before = len(data["api_calls"])
    data["api_calls"] = [
        [ts, count] for ts, count in data["api_calls"] if ts >= cutoff_ts
    ]
    if len(data["api_calls"]) != before:
        save()
