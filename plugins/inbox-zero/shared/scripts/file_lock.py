"""Cross-platform file lock for the plugin's session-level exclusivity.

Uses os.open(..., O_CREAT | O_EXCL | O_WRONLY) which is atomic on both
POSIX and Windows — if another process holds the lockfile the call fails
with FileExistsError and we retry until timeout.

Stale recovery is by lockfile mtime, not PID probing, to stay dependency-free
across OSes. A lockfile older than stale_after_hours is assumed dead and
removed before the next acquire attempt."""

from __future__ import annotations

import errno
import os
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator


def _write_lockfile(path: Path) -> None:
    """Atomically create the lockfile. Raises FileExistsError if it already exists."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = f"{os.getpid()}|{datetime.now(timezone.utc).isoformat()}".encode("utf-8")
    fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    try:
        os.write(fd, payload)
    finally:
        os.close(fd)


def _read_holder(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8").strip()
    except OSError:
        return "<unreadable>"


def _pid_is_alive(pid: int) -> bool | None:
    """Return True if pid corresponds to a live process, False if provably
    dead, None if we couldn't determine (treat as 'unknown' — caller should
    fall back to the age check).

    POSIX: os.kill(pid, 0) — ProcessLookupError ⇒ dead, PermissionError ⇒
    alive (process exists, owned by another user). Other OSError ⇒ unknown.

    Windows: ctypes.windll.kernel32.OpenProcess(0x1000, False, pid).
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000. NULL handle with
    GetLastError == 5 (ACCESS_DENIED) ⇒ alive; other NULL ⇒ dead."""
    if pid <= 0:
        return None
    if os.name == "nt":
        try:
            import ctypes
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.OpenProcess(
                PROCESS_QUERY_LIMITED_INFORMATION, False, int(pid)
            )
            if handle == 0:
                err = kernel32.GetLastError()
                if err == 5:  # ERROR_ACCESS_DENIED — process exists
                    return True
                return False
            kernel32.CloseHandle(handle)
            return True
        except Exception:
            return None
    else:
        try:
            os.kill(pid, 0)
            return True
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        except OSError:
            return None


def _parse_pid_from_lockfile(path: Path) -> int | None:
    """Lockfile payload is `{pid}|{iso-ts}`. Return int pid or None if
    missing/unreadable/malformed."""
    try:
        payload = path.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    head, _, _ = payload.partition("|")
    try:
        return int(head)
    except ValueError:
        return None


def _reap_if_stale(path: Path, stale_after_hours: float) -> bool:
    """Delete the lockfile if its PID is provably dead OR if it is older
    than stale_after_hours. Returns True if reaped.

    The PID-alive check makes lock recovery immediate after a crash: a
    holder process that exited without unlinking the lockfile is detected
    on the next acquire, not after the stale timer elapses."""
    try:
        mtime = path.stat().st_mtime
    except FileNotFoundError:
        return False
    except OSError:
        return False

    pid = _parse_pid_from_lockfile(path)
    if pid is not None:
        alive = _pid_is_alive(pid)
        if alive is False:
            try:
                path.unlink()
                return True
            except FileNotFoundError:
                return False
            except OSError:
                return False
        if alive is True:
            return False

    age_hours = (time.time() - mtime) / 3600.0
    if age_hours >= stale_after_hours:
        try:
            path.unlink()
            return True
        except FileNotFoundError:
            return False
        except OSError:
            return False
    return False


@contextmanager
def session_lock(
    lock_path: Path,
    timeout: float = 30.0,
    stale_after_hours: float = 1.0,
    poll_interval: float = 0.1,
) -> Iterator[None]:
    lock_path = Path(lock_path)
    deadline = time.monotonic() + timeout
    owned = False
    while True:
        _reap_if_stale(lock_path, stale_after_hours)
        try:
            _write_lockfile(lock_path)
            owned = True
            break
        except FileExistsError:
            pass
        except OSError as e:
            # EEXIST on some platforms surfaces differently; treat as contention
            if e.errno == errno.EEXIST:
                pass
            else:
                raise
        if time.monotonic() >= deadline:
            holder = _read_holder(lock_path)
            raise TimeoutError(
                f"Could not acquire {lock_path} within {timeout:.1f}s "
                f"(held by {holder})"
            )
        time.sleep(poll_interval)

    try:
        yield
    finally:
        if owned:
            try:
                lock_path.unlink()
            except FileNotFoundError:
                pass
            except OSError:
                # Leave lockfile — stale-by-age reap will clean up later
                pass
