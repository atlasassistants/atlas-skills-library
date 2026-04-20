"""Runtime path helpers for Atlas Inbox Zero.

Adds plugin-local dependency directories to ``sys.path`` before any third-party
imports happen. This lets the plugin keep its Python packages inside the repo
when the host machine does not provide a clean virtualenv workflow.
"""

from __future__ import annotations

import sys
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parent.parent.parent
LOCAL_PACKAGES_DIR = PLUGIN_ROOT / ".python-packages"


def ensure_runtime_paths() -> Path:
    """Add plugin-local package paths to ``sys.path`` if present."""
    local_path = str(LOCAL_PACKAGES_DIR)
    if LOCAL_PACKAGES_DIR.exists() and local_path not in sys.path:
        sys.path.insert(0, local_path)
    return LOCAL_PACKAGES_DIR
