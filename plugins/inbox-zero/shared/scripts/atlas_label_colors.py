"""Atlas Gmail label color mapping."""

from __future__ import annotations

from atlas_labels import (
    ACTION_REQUIRED,
    DELEGATED,
    FOLLOW_UP,
    LEADS,
    READ_ONLY,
    RECEIPTS,
    REFERENCE,
    SUBSCRIPTIONS,
    WAITING_FOR,
)


ATLAS_LABEL_COLORS: dict[str, dict[str, str]] = {
    LEADS: {"backgroundColor": "#ffad47", "textColor": "#594c05"},
    ACTION_REQUIRED: {"backgroundColor": "#fb4c2f", "textColor": "#ffffff"},
    READ_ONLY: {"backgroundColor": "#4a86e8", "textColor": "#ffffff"},
    WAITING_FOR: {"backgroundColor": "#fad165", "textColor": "#594c05"},
    DELEGATED: {"backgroundColor": "#16a766", "textColor": "#ffffff"},
    FOLLOW_UP: {"backgroundColor": "#a479e2", "textColor": "#ffffff"},
    RECEIPTS: {"backgroundColor": "#f6c5be", "textColor": "#7a2e0b"},
    SUBSCRIPTIONS: {"backgroundColor": "#c2c2c2", "textColor": "#434343"},
    REFERENCE: {"backgroundColor": "#aa8831", "textColor": "#ffffff"},
}


def color_for_label(name: str) -> dict[str, str] | None:
    color = ATLAS_LABEL_COLORS.get(name)
    return dict(color) if color else None


def label_has_color(label: dict, desired: dict[str, str] | None) -> bool:
    if desired is None:
        return True
    current = label.get("color") or {}
    return (
        str(current.get("backgroundColor", "")).lower() == desired["backgroundColor"].lower()
        and str(current.get("textColor", "")).lower() == desired["textColor"].lower()
    )
