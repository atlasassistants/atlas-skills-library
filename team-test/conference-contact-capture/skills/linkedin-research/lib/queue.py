"""Queue persistence for multi-name batch scrapes."""

import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VALID_STATUSES = frozenset({"pending", "in_progress", "done", "failed"})


def _atomic_write_json(p: Path, data: Any) -> None:
    """Write JSON atomically: write to a sibling .tmp file, then rename.

    `os.replace` is atomic on both POSIX and Windows. Either the old file
    survives intact or the new file replaces it — never a half-written state.
    """
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(str(tmp), str(p))


def get_queue_path() -> Path:
    return Path.home() / ".linkedin-scraper-queue.json"


def get_history_dir() -> Path:
    return Path.home() / ".linkedin-scraper-queue-history"


def create_queue(items: list[dict[str, Any]], path: Path | None = None) -> None:
    """Create a fresh queue file from a list of {name, company} dicts."""
    p = path or get_queue_path()
    queue = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "items": [
            {"name": i["name"], "company": i.get("company"), "status": "pending"}
            for i in items
        ],
    }
    _atomic_write_json(p, queue)


def read_queue(path: Path | None = None) -> dict[str, Any] | None:
    p = path or get_queue_path()
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def update_item_status(index: int, status: str, path: Path | None = None) -> None:
    """Update the status of a queue item by index."""
    if status not in VALID_STATUSES:
        raise ValueError(
            f"Invalid status {status!r}. Must be one of: {sorted(VALID_STATUSES)}"
        )
    p = path or get_queue_path()
    queue = read_queue(path=p)
    if queue is None:
        raise FileNotFoundError(f"Queue file not found: {p}")
    if not 0 <= index < len(queue["items"]):
        raise IndexError(f"Item index {index} out of range")
    queue["items"][index]["status"] = status
    _atomic_write_json(p, queue)


def get_pending_items(path: Path | None = None) -> list[dict[str, Any]]:
    """Return list of items that still have status='pending'."""
    queue = read_queue(path=path)
    if queue is None:
        return []
    return [item for item in queue["items"] if item["status"] == "pending"]


def is_queue_complete(path: Path | None = None) -> bool:
    queue = read_queue(path=path)
    if queue is None:
        return False
    return all(item["status"] != "pending" for item in queue["items"])


def archive_completed_queue(path: Path | None = None,
                            history_dir: Path | None = None) -> Path:
    p = path or get_queue_path()
    h = history_dir or get_history_dir()
    h.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H%M%S-%f")
    target = h / f"{timestamp}.json"
    shutil.move(str(p), str(target))
    return target
