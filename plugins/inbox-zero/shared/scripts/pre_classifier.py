"""
Deterministic Pre-Classifier
==============================
Classifies obvious email categories BEFORE the AI sees them.
~40% of inbox emails are receipts, subscriptions, calendar invites,
and meeting recordings — these don't need AI judgment.

The AI decision tree still handles everything this returns None for.

Usage:
    from pre_classifier import pre_classify

    result = pre_classify(from_header, subject, body, cc, label_ids)
    if result and not result.get("skip"):
        # Deterministic classification — apply the label
        label = result["label"]
    else:
        # Ambiguous — hand to AI decision tree
        pass
"""

import re
from typing import Any

from atlas_labels import RECEIPTS, REFERENCE, SUBSCRIPTIONS


# ── Pattern sets ──

_RECEIPT_PATTERNS = {
    "subject": [
        r"\breceipt\b", r"\binvoice\b", r"\bpayment\s+(confirm|receiv|process)",
        r"\bbilling\s+statement\b", r"\border\s+confirm", r"\bpurchase\s+confirm",
    ],
    "from": [
        r"receipt", r"billing", r"invoice", r"payment", r"noreply@.*\.stripe\.com",
        r"paypal", r"square",
    ],
}

_SUBSCRIPTION_PATTERNS = {
    "body": [r"\bunsubscribe\b"],
    "from": [
        r"^noreply@", r"^no-reply@", r"^notifications?@",
        r"^digest@", r"^updates?@", r"^alerts?@",
        r"@github\.com$", r"@gitlab\.com$", r"@jira\.atlassian",
        r"@slack\.com$", r"@asana\.com$", r"@notion\.so$",
        r"@linear\.app$", r"@figma\.com$",
    ],
}

_REFERENCE_PATTERNS = {
    "subject": [
        r"\binvitation:\s", r"\.ics\b", r"\bcalendar\s+event\b",
        r"\bmeeting\s+recording\b", r"\bcloud\s+recording\b",
        r"\bbooking\s+confirm",
    ],
    "from": [
        r"calendar-notification@google\.com", r"noreply@zoom\.us",
        r"@fathom\.video$", r"@calendly\.com$",
    ],
}

# Patterns that should NOT be pre-classified even if they match
# (these need human/AI judgment)
_EXCLUSION_PATTERNS = {
    "from": [
        # Personal contacts who happen to use receipt/billing language
        # will be caught by the "ambiguous" fallback
    ],
    "subject": [
        r"\burgent\b", r"\basap\b", r"\bconfidential\b",
        r"\blegal\b", r"\blitigation\b",
    ],
}


def _matches_any(text: str, patterns: list[str]) -> bool:
    """Check if text matches any pattern (case-insensitive)."""
    text_lower = text.lower()
    return any(re.search(p, text_lower) for p in patterns)


def _is_excluded(subject: str, from_header: str) -> bool:
    """Check if the email matches exclusion patterns (needs AI judgment)."""
    if _matches_any(subject, _EXCLUSION_PATTERNS.get("subject", [])):
        return True
    if _matches_any(from_header, _EXCLUSION_PATTERNS.get("from", [])):
        return True
    return False


def pre_classify(
    from_header: str,
    subject: str,
    body: str,
    cc: str,
    label_ids: list[str],
    atlas_label_ids: set[str] | None = None,
) -> dict[str, Any] | None:
    """
    Attempt deterministic classification of an email.

    Returns:
        None — if the email is ambiguous and needs AI judgment.
        {"label": "X", "confidence": "deterministic"} — if classified.
        {"skip": True, "reason": "already labeled"} — if already has an Atlas label.
    """
    # Skip if already labeled with an Atlas label
    if atlas_label_ids and label_ids:
        if set(label_ids) & atlas_label_ids:
            return {"skip": True, "reason": "already labeled"}

    # Check exclusions first — these need AI
    if _is_excluded(subject, from_header):
        return None

    # 6-Receipts/Invoices
    if (_matches_any(subject, _RECEIPT_PATTERNS["subject"]) or
            _matches_any(from_header, _RECEIPT_PATTERNS["from"])):
        return {"label": RECEIPTS, "confidence": "deterministic"}

    # 8-Reference (check before subscriptions — more specific from-patterns
    # like noreply@zoom.us should not be caught by generic ^noreply@)
    if (_matches_any(subject, _REFERENCE_PATTERNS["subject"]) or
            _matches_any(from_header, _REFERENCE_PATTERNS["from"])):
        return {"label": REFERENCE, "confidence": "deterministic"}

    # 7-Subscriptions
    if (_matches_any(body, _SUBSCRIPTION_PATTERNS["body"]) or
            _matches_any(from_header, _SUBSCRIPTION_PATTERNS["from"])):
        return {"label": SUBSCRIPTIONS, "confidence": "deterministic"}

    return None
