"""Approval policy helpers for high-impact Atlas Inbox Zero actions.

The goal is to keep routine, low-risk setup automatic while forcing a human
check-in before destructive, retroactive, or existing-system-changing actions
run against a real inbox.
"""

from __future__ import annotations

import hashlib
import json
import secrets
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


_PLUGIN_ROOT = Path(__file__).resolve().parents[2]
_APPROVALS_DIR = _PLUGIN_ROOT / "client-profile" / "approvals"
_PENDING_DIR = _APPROVALS_DIR / "pending"


class ApprovalRequiredError(RuntimeError):
    """Raised when a risky action needs explicit human approval first."""


class ApprovalValidationError(RuntimeError):
    """Raised when an approval id is missing, expired, or mismatched."""


@dataclass
class ApprovalRequest:
    approval_id: str
    action: str
    fingerprint: str
    summary: dict[str, Any]
    command_hint: str | None
    created_ts: float
    expires_ts: float
    path: Path

    def to_dict(self) -> dict[str, Any]:
        return {
            "approval_id": self.approval_id,
            "action": self.action,
            "fingerprint": self.fingerprint,
            "summary": self.summary,
            "command_hint": self.command_hint,
            "created_ts": self.created_ts,
            "expires_ts": self.expires_ts,
        }


def _ensure_dirs() -> None:
    _PENDING_DIR.mkdir(parents=True, exist_ok=True)


def _canonical_fingerprint(action: str, summary: dict[str, Any]) -> str:
    payload = json.dumps({"action": action, "summary": summary}, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def create_approval_request(
    action: str,
    summary: dict[str, Any],
    *,
    command_hint: str | None = None,
    expires_hours: int = 24,
) -> ApprovalRequest:
    """Persist a pending approval request and return its metadata."""
    _ensure_dirs()
    now = time.time()
    approval_id = f"apr_{int(now)}_{secrets.token_hex(4)}"
    fingerprint = _canonical_fingerprint(action, summary)
    path = _PENDING_DIR / f"{approval_id}.json"
    request = ApprovalRequest(
        approval_id=approval_id,
        action=action,
        fingerprint=fingerprint,
        summary=summary,
        command_hint=command_hint,
        created_ts=now,
        expires_ts=now + (expires_hours * 3600),
        path=path,
    )
    path.write_text(json.dumps(request.to_dict(), indent=2), encoding="utf-8")
    return request


def load_approval_request(approval_id: str) -> ApprovalRequest:
    """Load a pending approval request by id."""
    path = _PENDING_DIR / f"{approval_id}.json"
    if not path.exists():
        raise ApprovalValidationError(
            f"Approval id '{approval_id}' was not found. Run the preview step again."
        )
    payload = json.loads(path.read_text(encoding="utf-8"))
    return ApprovalRequest(
        approval_id=payload["approval_id"],
        action=payload["action"],
        fingerprint=payload["fingerprint"],
        summary=payload["summary"],
        command_hint=payload.get("command_hint"),
        created_ts=payload["created_ts"],
        expires_ts=payload["expires_ts"],
        path=path,
    )


def ensure_approved(
    action: str,
    summary: dict[str, Any],
    *,
    approval_id: str | None,
) -> ApprovalRequest:
    """Validate that a pending approval matches the current action scope."""
    if not approval_id:
        raise ApprovalValidationError(
            "This action requires explicit approval. Run the preview step first, "
            "then re-run with --approval-id <id>."
        )

    request = load_approval_request(approval_id)
    if request.action != action:
        raise ApprovalValidationError(
            f"Approval id '{approval_id}' is for '{request.action}', not '{action}'."
        )
    if request.expires_ts < time.time():
        raise ApprovalValidationError(
            f"Approval id '{approval_id}' expired. Run the preview step again."
        )

    current = _canonical_fingerprint(action, summary)
    if request.fingerprint != current:
        raise ApprovalValidationError(
            "The current action scope no longer matches the approved preview. "
            "Run the preview step again before executing."
        )
    return request


def approval_request_payload(request: ApprovalRequest) -> dict[str, Any]:
    """JSON-friendly approval metadata for script output."""
    return {
        "required": True,
        "approval_id": request.approval_id,
        "expires_ts": request.expires_ts,
        "path": str(request.path),
        "command_hint": request.command_hint,
    }


def render_approval_instructions(request: ApprovalRequest) -> str:
    """Human-readable approval instructions for stderr output."""
    base = (
        f"APPROVAL REQUIRED for {request.action}. "
        f"Review the preview, then re-run with --approval-id {request.approval_id}."
    )
    if request.command_hint:
        return f"{base}\nCommand: {request.command_hint}"
    return base
