# atlas-inbox-zero/shared/scripts/atlas_labels.py
"""
Atlas Label Constants
=====================
Single source of truth for all Atlas Inbox Zero label names.
All Python scripts import from here. SKILL.md files still use display names.
"""

LEADS = "0-Leads"
ACTION_REQUIRED = "1-Action Required"
READ_ONLY = "2-Read Only"
WAITING_FOR = "3-Waiting For"
DELEGATED = "4-Delegated"
FOLLOW_UP = "5-Follow Up"
RECEIPTS = "6-Receipts/Invoices"
SUBSCRIPTIONS = "7-Subscriptions"
REFERENCE = "8-Reference"

ALL_ATLAS_LABELS: list[str] = [
    LEADS, ACTION_REQUIRED, READ_ONLY, WAITING_FOR,
    DELEGATED, FOLLOW_UP, RECEIPTS, SUBSCRIPTIONS, REFERENCE,
]

_ATLAS_SET: set[str] = set(ALL_ATLAS_LABELS)


def is_atlas_label(name: str) -> bool:
    """Check if a label name is an Atlas label."""
    return name in _ATLAS_SET
