"""Rolling 24h Gmail API call counter.

Failure-soft: any exception raised by the underlying store is logged once
to stderr and then swallowed. usage_24h / usage_pct return None after a
failure so callers can render 'quota: unknown'."""

from __future__ import annotations

import os
import sys
import threading
import time
from pathlib import Path
from typing import Any

from constants import QUOTA_SOFT_BUDGET, QUOTA_WARN_PCT
from state_store import StateStore


# M4: process-wide emit-once flag for the disable notice. Both the init
# path (StateStore construction failure in get_quota_tracker) and the
# runtime path (_notice_once after a record/usage exception) consult this
# so we never double-log.
_disabled_emitted: bool = False


def _emit_disabled_once(reason: str) -> None:
    """Print one stderr line and emit one quota_tracker_disabled structured
    event — exactly once per process. Idempotent across all callers.

    The structured-event lazy-import follows the pattern Phase 2 introduced
    in gmail_auth._log_token_refresh_failure: a broken structured_logger
    must never mask the underlying disable signal."""
    global _disabled_emitted
    if _disabled_emitted:
        return
    _disabled_emitted = True
    try:
        print(f"[quota_tracker] disabled: {reason}", file=sys.stderr)
    except Exception:
        pass
    try:
        from structured_logger import get_logger
        get_logger().event("quota_tracker_disabled", reason=str(reason)[:500])
    except Exception:
        pass


class QuotaTracker:
    def __init__(self, store: Any, budget: int = QUOTA_SOFT_BUDGET) -> None:
        self._store = store
        self._budget = max(1, int(budget))
        self._disabled = False

    def _notice_once(self, msg: str) -> None:
        if self._disabled:
            return
        self._disabled = True
        # M4: route through the shared helper so the structured event
        # fires too, and the emit-once invariant holds across both the
        # init and runtime disable paths.
        _emit_disabled_once(msg)

    def record(self, n: int = 1) -> None:
        if self._disabled or n <= 0:
            return
        try:
            self._store.record_api_call(count=int(n), ts=time.time())
        except Exception as e:
            self._notice_once(str(e))

    def usage_24h(self) -> int | None:
        if self._disabled:
            return None
        try:
            return int(self._store.get_api_calls_last_24h(now=time.time()))
        except Exception as e:
            self._notice_once(str(e))
            return None

    def usage_pct(self) -> float | None:
        used = self.usage_24h()
        if used is None:
            return None
        return (used / self._budget) * 100.0

    def over_warn_threshold(self) -> bool:
        pct = self.usage_pct()
        if pct is None:
            return False
        return pct >= QUOTA_WARN_PCT


class _DisabledTracker(QuotaTracker):
    """Drop-in tracker used when StateStore construction fails. All writes
    are no-ops; all reads return None. Keeps callers free of None-checks
    on the tracker itself."""

    def __init__(self) -> None:  # noqa: D401
        self._store = None
        self._budget = max(1, int(QUOTA_SOFT_BUDGET))
        self._disabled = True


_singleton: QuotaTracker | None = None
_singleton_lock = threading.Lock()


def get_quota_tracker() -> QuotaTracker:
    """Module-level singleton. First call constructs a StateStore at
    ATLAS_STATE_PATH (if set) or the default plugin state path, wraps it
    in a QuotaTracker, and caches the result. If StateStore construction
    raises, returns a _DisabledTracker so callers never see an exception."""
    global _singleton
    with _singleton_lock:
        if _singleton is None:
            path_env = os.environ.get("ATLAS_STATE_PATH")
            try:
                store = StateStore(path=Path(path_env)) if path_env else StateStore()
                _singleton = QuotaTracker(store)
            except Exception as e:
                _emit_disabled_once(str(e))
                _singleton = _DisabledTracker()
        return _singleton


def set_quota_tracker(tracker: QuotaTracker) -> None:
    """Test-only: inject a QuotaTracker so get_quota_tracker() returns it
    until the next reset."""
    global _singleton
    with _singleton_lock:
        _singleton = tracker


def reset_quota_tracker() -> None:
    """Test-only: drop the cached singleton AND reset the disable-emit
    flag so the next disable in the test process re-emits."""
    global _singleton, _disabled_emitted
    with _singleton_lock:
        _singleton = None
        _disabled_emitted = False
