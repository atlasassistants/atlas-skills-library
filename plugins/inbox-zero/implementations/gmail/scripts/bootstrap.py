"""Shared sys.path bootstrap for atlas-inbox-zero skills (M2).

Skills launched as subprocesses by the orchestrator inherit the
``ATLAS_SHARED_SCRIPTS`` environment variable pointing at this directory.
By importing this module at the top of a skill, the skill picks up the
shared scripts path without having to compute the relative location itself:

    import bootstrap  # noqa: F401  -- inserts ATLAS_SHARED_SCRIPTS on sys.path
    from gmail_client import GmailClient

Existing skills retain their defensive ``sys.path.insert`` boilerplate as
belts-and-suspenders. New skills should prefer this module - fewer moving
parts, one source of truth for the path.

If ``ATLAS_SHARED_SCRIPTS`` is unset (e.g., the skill is being run
manually without the orchestrator), this module is a no-op so direct
invocation still works as long as the caller's ``sys.path`` already
includes the shared scripts dir.
"""

from __future__ import annotations

import os
import sys

_SHARED = os.environ.get("ATLAS_SHARED_SCRIPTS")
if _SHARED and _SHARED not in sys.path:
    sys.path.insert(0, _SHARED)
