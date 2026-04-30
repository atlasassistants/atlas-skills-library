"""Pacing rules: daily cap, burst cooldown, minimum interval between scrapes."""

import random
from datetime import datetime, timedelta, timezone
from typing import Any


DEFAULT_PACING = {
    "min_interval_seconds": 45,
    "interval_jitter_seconds": 15,
    "daily_cap": 25,
    "burst_cap": 8,
    "burst_window_minutes": 30,
    "burst_slow_interval_seconds": 90,
    "burst_slow_duration_minutes": 30,
}


def _parse_ts(s: str) -> datetime:
    dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def is_daily_cap_exceeded(history: list[dict], daily_cap: int) -> bool:
    cutoff = _now() - timedelta(hours=24)
    recent = [h for h in history if _parse_ts(h["timestamp"]) >= cutoff]
    return len(recent) >= daily_cap


def is_in_burst_slowdown(history: list[dict], burst_cap: int,
                         burst_window_minutes: int,
                         burst_slow_duration_minutes: int) -> bool:
    """Returns True if user has hit burst threshold and is still in slowdown."""
    burst_window_cutoff = _now() - timedelta(minutes=burst_window_minutes)
    in_burst_window = sorted(
        [h for h in history if _parse_ts(h["timestamp"]) >= burst_window_cutoff],
        key=lambda h: _parse_ts(h["timestamp"]),
    )
    if len(in_burst_window) < burst_cap:
        return False
    # Anchor to the moment the burst threshold was crossed (the burst_cap-th entry),
    # not the latest entry — otherwise slowdown extends every time a new scrape lands.
    burst_hit_at = _parse_ts(in_burst_window[burst_cap - 1]["timestamp"])
    slowdown_until = burst_hit_at + timedelta(minutes=burst_slow_duration_minutes)
    return _now() < slowdown_until


def seconds_until_next_scrape_allowed(history: list[dict],
                                      pacing: dict | None = None) -> float:
    pacing = pacing or DEFAULT_PACING
    if not history:
        return 0.0
    latest = max(_parse_ts(h["timestamp"]) for h in history)
    if is_in_burst_slowdown(
        history,
        pacing["burst_cap"],
        pacing["burst_window_minutes"],
        pacing["burst_slow_duration_minutes"],
    ):
        interval = pacing["burst_slow_interval_seconds"]
        jitter = 0  # no jitter during slowdown — keep predictable
    else:
        interval = pacing["min_interval_seconds"]
        jitter = random.uniform(-pacing["interval_jitter_seconds"],
                                pacing["interval_jitter_seconds"])
    target = latest + timedelta(seconds=interval + jitter)
    delta = (target - _now()).total_seconds()
    return max(0.0, delta)


def append_history(history: list[dict], name: str, ok: bool = True) -> list[dict]:
    """Append a new entry, prune entries older than 7 days, return new list."""
    new_entry = {
        "timestamp": _now().isoformat(),
        "name": name,
        "ok": ok,
    }
    cutoff = _now() - timedelta(days=7)
    pruned = [h for h in history if _parse_ts(h["timestamp"]) >= cutoff]
    pruned.append(new_entry)
    return pruned
