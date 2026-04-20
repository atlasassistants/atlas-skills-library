"""
Persistent State Store
======================
Lightweight JSON-backed state that tracks:
  - When labels were applied (actual timestamp, not internalDate)
  - Which cadence steps have been executed per message
  - Session history markers

Solves three reliability problems:
  - Follow-up cadence firing prematurely (Problem 2)
  - Read-Only auto-archiving items that were just labeled (Problem 5)
  - Duplicate follow-up drafts across sessions (Problem 7)

The state file lives at client-profile/.plugin-state.json by default.
Every write is atomic (write to temp, rename) to avoid corruption.

Usage:
    from state_store import StateStore
    store = StateStore()  # uses default path
    store.record_label_applied("msg_001", "3-Waiting For")
    age = store.get_label_age_days("msg_001", "3-Waiting For")
"""

import json
import os
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import _state_cadence
import _state_labels
import _state_quota
import _state_snapshots
from profile_paths import CLIENT_PROFILE_DIR

_DEFAULT_STATE_PATH = CLIENT_PROFILE_DIR / ".plugin-state.json"


class StateStore:
    """JSON-backed persistent state for the Atlas Inbox Zero plugin."""

    def __init__(self, path: str | Path | None = None):
        self.path = Path(path or _DEFAULT_STATE_PATH)
        self._data: dict[str, Any] = {
            "labels": {}, "cadence": {}, "sessions": [],
            "snapshots": {}, "api_calls": [],
        }
        self._load()

    # ─── Persistence ───

    def _load(self) -> None:
        if self.path.exists():
            try:
                self._data = json.loads(self.path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError) as exc:
                self._data = self._recover_from_corrupt_main(exc)
        # Ensure keys exist even on corrupt/empty load
        self._data.setdefault("labels", {})
        self._data.setdefault("cadence", {})
        self._data.setdefault("sessions", [])
        self._data.setdefault("snapshots", {})
        self._data.setdefault("api_calls", [])

    def _recover_from_corrupt_main(self, exc: Exception) -> dict:
        """H4: main file failed to parse. Quarantine it, try restoring from
        .bak, fall back to empty default if .bak is also corrupt or missing.
        Emit a loud structured log event for the operator either way.

        Returns the recovered _data dict. Never raises — load recovery must
        not itself be a failure path.
        """
        quarantine_path = self._quarantine_corrupt_main()

        # Attempt restore from .bak.
        bak_path = self._bak_path()
        if bak_path.exists():
            try:
                recovered = json.loads(bak_path.read_text(encoding="utf-8"))
                self._log_corrupt_load(
                    recovered_from="bak",
                    quarantine_path=str(quarantine_path) if quarantine_path else "",
                    error=str(exc)[:500],
                )
                return recovered
            except (json.JSONDecodeError, OSError):
                pass  # .bak is also bad — fall through to empty.

        self._log_corrupt_load(
            recovered_from="empty",
            quarantine_path=str(quarantine_path) if quarantine_path else "",
            error=str(exc)[:500],
        )
        return {
            "labels": {}, "cadence": {}, "sessions": [],
            "snapshots": {}, "api_calls": [],
        }

    def _quarantine_corrupt_main(self):
        """Rename the corrupt main file to <path>.corrupt.<iso-ts>. Returns
        the new path, or None if the rename itself failed (in which case
        the corrupt file just remains at its original name — the caller
        still proceeds with recovery)."""
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        quarantine = self.path.parent / (self.path.name + f".corrupt.{ts}")
        try:
            os.replace(str(self.path), str(quarantine))
            try:
                os.chmod(quarantine, 0o600)
            except OSError:
                pass
            return quarantine
        except OSError:
            return None

    def _log_corrupt_load(
        self, *, recovered_from: str, quarantine_path: str, error: str,
    ) -> None:
        """Emit state_store_corrupt_load event. Lazy-import the logger so
        a broken structured_logger cannot break load recovery — we match
        the pattern Phase 2 used in gmail_auth._log_token_refresh_failure."""
        try:
            from structured_logger import get_logger
            get_logger().event(
                "state_store_corrupt_load",
                recovered_from=recovered_from,
                quarantine_path=quarantine_path,
                error=error,
            )
        except Exception:
            pass  # logger failure must never mask recovery

    def save(self) -> None:
        """Atomic write: write to temp file, then rename. Before replacing
        the main file, rotate the previous payload to <path>.bak so H4
        corrupt-load recovery has something to restore from.
        """
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp_fd, tmp_path = tempfile.mkstemp(
            dir=str(self.path.parent), suffix=".tmp"
        )
        try:
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2)

            # H4: rotate previous payload to .bak BEFORE we overwrite main.
            # os.replace is atomic and overwrites an existing .bak on both
            # POSIX and Windows. Failure here is non-fatal — durability
            # forward-progress (the new main write) matters more than the
            # belt-and-suspenders backup.
            bak_path = self._bak_path()
            if self.path.exists():
                try:
                    os.replace(str(self.path), str(bak_path))
                    try:
                        os.chmod(bak_path, 0o600)
                    except OSError:
                        pass
                except OSError:
                    pass  # .bak rotation failed; proceed to main write anyway.

            # On Windows, os.replace is atomic if same filesystem
            os.replace(tmp_path, str(self.path))
            # M5: lock to owner-only on POSIX. mkstemp(2) already creates
            # the temp file with mode 0o600, so there's no window where
            # the final path is world-readable; this chmod locks the
            # destination path in case it previously had looser perms.
            # On Windows os.chmod is a no-op for these bits — harmless.
            try:
                os.chmod(self.path, 0o600)
            except OSError:
                # Don't let a chmod failure break a successful write
                # (e.g., filesystem that doesn't support chmod). The
                # atomic rename already succeeded.
                pass
        except Exception:
            # Clean up temp file on failure
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise

    def _bak_path(self) -> Path:
        """Path to the .bak rotation file next to the main state file."""
        return self.path.parent / (self.path.name + ".bak")

    # ─── Label Timestamps (Problems 2 & 5) ───

    def record_label_applied(
        self,
        message_id: str,
        label_name: str,
        timestamp: float | None = None,
        source: str = "plugin",
    ) -> None:
        """Record when a label was applied to a message."""
        _state_labels.record_applied(
            self._data, self.save, message_id, label_name, timestamp, source,
        )

    def get_label_applied_at(self, message_id: str, label_name: str) -> float | None:
        """Get the timestamp when a label was applied. Returns None if unknown."""
        return _state_labels.get_applied_at(self._data, message_id, label_name)

    def get_label_age_days(self, message_id: str, label_name: str) -> int | None:
        """Get how many days since the label was applied. Returns None if unknown."""
        return _state_labels.get_age_days(self._data, message_id, label_name)

    def get_label_source(self, message_id: str, label_name: str) -> str | None:
        """Get the source that applied a label ('plugin', 'manual', or 'unknown'). None if missing."""
        return _state_labels.get_source(self._data, message_id, label_name)

    def set_label_source(
        self,
        message_id: str,
        label_name: str,
        source: str,
        timestamp: float | None = None,
    ) -> None:
        """Explicitly set provenance for a currently-labeled message."""
        _state_labels.set_source(
            self._data, self.save, message_id, label_name, source, timestamp,
        )

    def remove_label_record(self, message_id: str, label_name: str) -> None:
        """Remove a label timestamp record (when label is removed)."""
        _state_labels.remove(self._data, self.save, message_id, label_name)

    def reconcile_labels(self, client) -> dict[str, object]:
        """
        Sync state store with Gmail's actual label state.

        1. For each Atlas label, fetch messages with that label from Gmail.
        2. Any message with a label not in the state store = provenance unknown.
        3. Any state store entry whose label is no longer in Gmail = stale, clear it.
        4. Labels whose search raised are recorded in failed_labels and skipped
           for stale-classification (we can't know ground truth).

        Args:
            client: GmailClient instance

        Returns:
            {
                "new_unknown": int,
                "new_manual": int,
                "cleared_stale": int,
                "failed_labels": list[str],  # labels whose search_all_messages raised
            }
        """
        return _state_labels.reconcile(self._data, self.save, client)

    # ─── Cadence Step Tracking (Problem 7) ───

    def record_cadence_step(
        self,
        message_id: str,
        step: str,
        draft_id: str | None = None,
        session_id: str | None = None,
    ) -> None:
        """Record that a cadence step was executed for a message."""
        _state_cadence.record_step(self._data, self.save, message_id, step, draft_id, session_id)

    def was_step_fired_this_session(self, message_id: str, session_id: str) -> bool:
        """Check if any cadence step was fired for this message in the given session."""
        return _state_cadence.was_fired_this_session(self._data, message_id, session_id)

    def get_executed_steps(self, message_id: str) -> list[dict[str, Any]]:
        """Get all executed cadence steps for a message."""
        return _state_cadence.get_executed(self._data, message_id)

    def is_step_executed(self, message_id: str, step: str) -> bool:
        """Check if a specific cadence step has been executed."""
        return _state_cadence.is_executed(self._data, message_id, step)

    def clear_cadence_history(self, message_id: str) -> None:
        """Clear cadence history for a message (when it leaves 3-Waiting For)."""
        _state_cadence.clear_history(self._data, self.save, message_id)

    # ─── Session Markers ───

    def record_session(self, mode: str, processed: int, errors: int) -> None:
        """Record a completed triage session."""
        self._data["sessions"].append({
            "mode": mode,
            "processed": processed,
            "errors": errors,
            "ts": time.time(),
        })
        # Keep only last 50 sessions
        self._data["sessions"] = self._data["sessions"][-50:]
        self.save()

    def get_last_session(self) -> dict[str, Any] | None:
        """Get the most recent session marker."""
        sessions = self._data["sessions"]
        return sessions[-1] if sessions else None

    # ─── Snapshots & Rollback (Issue #3) ───

    def record_snapshot(
        self,
        mode: str,
        actions: list[dict],
    ) -> str:
        """
        Record a triage session snapshot before labels are modified.

        Args:
            mode: Triage mode (morning/midday/eod)
            actions: List of {message_id, old_labels, new_label}

        Returns:
            session_id (ISO timestamp string)
        """
        return _state_snapshots.record(self._data, self.save, mode, actions)

    def get_snapshot(self, session_id: str) -> dict | None:
        """Get a snapshot by session ID."""
        return _state_snapshots.get(self._data, session_id)

    def list_snapshots(self) -> list[dict]:
        """List all snapshots, newest first."""
        return _state_snapshots.list_all(self._data)

    def get_rollback_actions(self, session_id: str) -> list[dict]:
        """
        Get the list of actions needed to reverse a snapshot.

        Returns list of {message_id, restore_labels, remove_label}.
        Empty list if snapshot not found.
        """
        return _state_snapshots.get_rollback_actions(self._data, session_id)

    def mark_rolled_back(self, session_id: str) -> bool:
        """Mark a snapshot as rolled back. Returns True if marked, False if not found."""
        return _state_snapshots.mark_rolled_back(self._data, self.save, session_id)

    def prune_snapshots(self, max_age_days: int = 7) -> None:
        """Remove snapshots older than max_age_days."""
        _state_snapshots.prune(self._data, self.save, max_age_days)

    # ─── API-Call Quota Tracking ───

    def record_api_call(self, count: int, ts: float) -> None:
        """Append a single (ts, count) entry. O(1). Called by QuotaTracker
        on every Gmail API hit. Data is a list of two-element lists because
        JSON has no tuple; list-of-list round-trips cleanly."""
        _state_quota.record_call(self._data, self.save, count, ts)

    def get_api_calls_last_24h(self, now: float) -> int:
        """Sum counts of entries whose ts is >= now - 24h."""
        return _state_quota.get_calls_last_24h(self._data, now)

    def prune_api_calls(self, cutoff_ts: float) -> None:
        """Drop entries older than cutoff_ts. Called by orchestrator at
        session end with cutoff_ts = now - 24h."""
        _state_quota.prune(self._data, self.save, cutoff_ts)

    # ─── Cleanup ───

    def prune(self, max_age_days: int = 30) -> None:
        """Remove entries older than max_age_days to prevent unbounded growth."""
        cutoff = time.time() - (max_age_days * 24 * 3600)

        # Prune labels
        to_remove = [
            key for key, entry in self._data["labels"].items()
            if entry["ts"] < cutoff
        ]
        for key in to_remove:
            del self._data["labels"][key]

        # Prune cadence entries with no recent steps
        to_remove_cadence = []
        for msg_id, steps in self._data["cadence"].items():
            if not steps or max(s["ts"] for s in steps) < cutoff:
                to_remove_cadence.append(msg_id)
        for msg_id in to_remove_cadence:
            del self._data["cadence"][msg_id]

        self.save()
