"""JSON-lines event logger with 10MB rotation.

Failure-soft: event() never raises. If the log file cannot be written the
logger disables itself for the rest of the session, printing a single
notice to stderr."""

from __future__ import annotations

import json
import logging
import os
import sys
import threading
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

from constants import LOG_ROTATE_BYTES, LOG_ROTATE_BACKUPS


class StructuredLogger:
    def __init__(
        self,
        log_path: Path,
        max_bytes: int = LOG_ROTATE_BYTES,
        backups: int = LOG_ROTATE_BACKUPS,
    ) -> None:
        self._path = Path(log_path)
        self._disabled = False
        self._lock = threading.Lock()
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            handler = RotatingFileHandler(
                str(self._path),
                maxBytes=max_bytes,
                backupCount=backups,
                encoding="utf-8",
                delay=True,
            )
            handler.setFormatter(logging.Formatter("%(message)s"))
            logger = logging.Logger(f"atlas.structured.{id(self)}")
            logger.setLevel(logging.INFO)
            logger.addHandler(handler)
            logger.propagate = False
            self._handler = handler
            self._logger = logger
        except OSError as e:
            self._notice(f"structured_logger disabled (init failure: {e})")
            self._disabled = True
            self._handler = None
            self._logger = None

    def event(self, name: str, **fields: Any) -> None:
        if self._disabled:
            return
        try:
            record: dict[str, Any] = {
                "ts": datetime.now(timezone.utc).isoformat(),
                "event": name,
                "pid": os.getpid(),
            }
            record.update(fields)
            line = json.dumps(record, default=str, ensure_ascii=False)
            with self._lock:
                self._logger.info(line)
        except Exception as e:  # never raise into caller
            self._notice(f"structured_logger disabled (write failure: {e})")
            self._disabled = True

    def close(self) -> None:
        if self._handler is not None:
            try:
                self._handler.close()
            except Exception:
                pass

    def _notice(self, msg: str) -> None:
        try:
            print(f"[structured_logger] {msg}", file=sys.stderr)
        except Exception:
            pass


_PLUGIN_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_DEFAULT_LOG_PATH = _PLUGIN_ROOT / "logs" / "inbox-zero.jsonl"

_singleton: StructuredLogger | None = None
_singleton_lock = threading.Lock()


def get_logger() -> StructuredLogger:
    global _singleton
    with _singleton_lock:
        if _singleton is None:
            log_dir_env = os.environ.get("ATLAS_LOG_DIR")
            if log_dir_env:
                path = Path(log_dir_env) / "inbox-zero.jsonl"
            else:
                path = _DEFAULT_LOG_PATH
            _singleton = StructuredLogger(path)
        return _singleton


def reset_logger() -> None:
    """Test-only: drop the singleton so a fresh path can be picked up."""
    global _singleton
    with _singleton_lock:
        if _singleton is not None:
            _singleton.close()
        _singleton = None
