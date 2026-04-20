"""
Orchestrator
============
The real executable orchestrator for inbox-zero. Chains skills in the
correct order, manages context between them, handles failures, and
produces a consolidated report.

Replaces the pseudocode in inbox-zero/SKILL.md with actual executable
logic. The SKILL.md still describes the orchestrator's behavior for
Claude Code's skill system — this script is what it calls.

Usage:
    python orchestrator.py --mode auto
    python orchestrator.py --mode morning
    python orchestrator.py --mode eod --dry-run

Exit codes:
    0 — chain completed (possibly with warnings)
    1 — chain halted on a fatal error (partial report still emitted)
    2 — prerequisites not met (credentials, labels, etc.)
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

_PLUGIN_ROOT = Path(__file__).resolve().parent.parent.parent
_SHARED_SCRIPTS = _PLUGIN_ROOT / "shared" / "scripts"

if str(_SHARED_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SHARED_SCRIPTS))

from file_lock import session_lock  # noqa: E402  (path inserted just above)
from structured_logger import get_logger  # noqa: E402
from health_check import run_checks  # noqa: E402
from profile_paths import CLIENT_PROFILE_DIR, profile_read_path  # noqa: E402


_CLIENT_PROFILE = CLIENT_PROFILE_DIR


def _session_id() -> str:
    """ISO 8601 UTC timestamp with seconds precision. Used as the correlation id
    across all events emitted within a single _run_session invocation."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _quota_snapshot() -> dict[str, Any]:
    """Build the quota snapshot dict. Never raises; returns a fully-typed
    dict with None fields when the tracker is disabled."""
    try:
        from quota_tracker import get_quota_tracker
        from constants import QUOTA_SOFT_BUDGET
        tracker = get_quota_tracker()
        calls = tracker.usage_24h()
        pct = tracker.usage_pct()
        over = tracker.over_warn_threshold()
        return {
            "calls_24h": calls,
            "budget": int(QUOTA_SOFT_BUDGET),
            "pct": pct,
            "over_warn": bool(over),
        }
    except Exception:
        # Import-time failure or anything else: return a disabled snapshot.
        return {"calls_24h": None, "budget": 0, "pct": None, "over_warn": False}


def _prune_quota_state() -> None:
    """Prune api_calls older than 24h. Failure-soft."""
    try:
        from quota_tracker import get_quota_tracker
        import time as _t
        tracker = get_quota_tracker()
        store = getattr(tracker, "_store", None)
        if store is None:
            return
        store.prune_api_calls(cutoff_ts=_t.time() - (24 * 3600))
    except Exception:
        pass


def _run_health_preflight(session_id: str) -> dict[str, Any]:
    """
    Run ``health_check.run_checks()`` as a session pre-flight.

    Emits ``health_check_start``, one ``health_finding`` event per finding,
    one ``health_check_errored`` event per check that raised, and a
    ``health_check_end`` summary. Renders each finding as a one-line stderr
    notice so operators see drift inline when watching a run.

    MUST NEVER raise into the caller. ``run_checks`` has its own per-check
    isolation, and this wrapper adds a belt-and-suspenders try/except in
    case the shared module itself explodes. On wrapper failure we return
    an empty-but-well-typed report so ``result["health"]`` is still
    attachable downstream.

    Returns the serialized report shape::

        {
            "findings": [{"check","severity","detail","file"}, ...],
            "errored_checks": ["_check_name", ...]
        }
    """
    from dataclasses import asdict

    log = get_logger()
    log.event("health_check_start", session_id=session_id)

    try:
        report = run_checks(_CLIENT_PROFILE)
    except Exception as exc:
        log.event(
            "health_check_end",
            session_id=session_id,
            findings=0,
            errored_checks=0,
            wrapper_error=str(exc),
        )
        return {
            "findings": [],
            "errored_checks": [],
            "wrapper_error": str(exc)[:500],
        }

    for f in report.findings:
        log.event(
            "health_finding",
            session_id=session_id,
            check=f.check,
            severity=f.severity,
            detail=f.detail,
            file=f.file,
        )
        print(
            f"Health {f.severity.upper()}: {f.check} - {f.detail}",
            file=sys.stderr,
        )

    for name in report.errored_checks:
        log.event("health_check_errored", session_id=session_id, check=name)

    log.event(
        "health_check_end",
        session_id=session_id,
        findings=len(report.findings),
        errored_checks=len(report.errored_checks),
    )

    return {
        "findings": [asdict(f) for f in report.findings],
        "errored_checks": list(report.errored_checks),
    }


# ─── Session Rate Guard ───

SESSION_RATE_GUARD_MINUTES = 20


# ─── Session Lock ───

SESSION_LOCK_FILENAME = ".plugin-session.lock"
SESSION_LOCK_TIMEOUT = 30.0
SESSION_LOCK_STALE_HOURS = 1.0
EXIT_LOCK_CONTENTION = 73
UI_CONFIRMATION_PATH = _CLIENT_PROFILE / ".onboarding-ui-confirmed.json"


def check_session_rate_limit(mode: str, force: bool) -> tuple[bool, str]:
    """
    Refuse to run if the last session was the same mode and fired
    less than SESSION_RATE_GUARD_MINUTES ago, unless --force was passed.

    Returns (should_run, message). Failures here are non-fatal — if the
    state store can't be read, we let the run proceed.
    """
    if force:
        return True, ""
    try:
        from state_store import StateStore
        store = StateStore()
        last = store.get_last_session()
    except Exception:
        return True, ""
    if not last or last.get("mode") != mode:
        return True, ""
    age_minutes = (time.time() - last.get("ts", 0)) / 60
    if age_minutes >= SESSION_RATE_GUARD_MINUTES:
        return True, ""
    return False, (
        f"Last {mode} session ran {age_minutes:.1f} minutes ago "
        f"(< {SESSION_RATE_GUARD_MINUTES}m). Pass --force to override."
    )


# ─── Mode Detection ───

def detect_mode(hour: int | None = None, override: str | None = None) -> str:
    """Determine triage mode from time of day or explicit override."""
    if override and override in ("morning", "midday", "eod"):
        return override
    if hour is None:
        hour = datetime.now().hour
    if hour < 11:
        return "morning"
    elif hour >= 16:
        return "eod"
    else:
        return "midday"


# ─── Prerequisites ───

def validate_prerequisites() -> list[str]:
    """
    Check that the plugin can run. Returns a list of error messages.
    Empty list = all good.
    """
    errors = []

    creds = _CLIENT_PROFILE / "credentials" / "credentials.json"
    if not creds.exists():
        errors.append(
            "No credentials.json found. Run `inbox-onboarding` first."
        )

    token = _CLIENT_PROFILE / "credentials" / "token.json"
    if not token.exists():
        errors.append(
            "Not authenticated. Run `inbox-onboarding` or "
            "`python shared/scripts/setup_credentials.py`."
        )

    if not errors:
        # Only check labels if we can authenticate
        try:
            from atlas_labels import ALL_ATLAS_LABELS
            from gmail_client import GmailClient
            client = GmailClient()
            labels = {l["name"] for l in client.list_labels()}
            required = set(ALL_ATLAS_LABELS)
            missing = required - labels
            if missing:
                errors.append(
                    f"Missing Atlas labels: {sorted(missing)}. "
                    "Run `inbox-onboarding` to create them."
                )

            filters = client.list_filters()
            if len(filters) < 4:
                errors.append(
                    f"Core Gmail filters are incomplete ({len(filters)}/4 found). "
                    "Run `python inbox-onboarding/scripts/create_filters.py`."
                )

            cutoff = (datetime.now() - timedelta(days=90)).strftime("%Y/%m/%d")
            old_inbox = client.search_messages(
                f"in:inbox before:{cutoff}",
                max_results=1,
            ).get("resultSizeEstimate", 0)
            if int(old_inbox or 0) > 0:
                errors.append(
                    "Initial cleanup incomplete: inbox still contains mail older than 90 days. "
                    "Run `python inbox-onboarding/scripts/initial_cleanup.py mass-archive --older-than-days 90 --dry-run`, then execute with the approval id."
                )

            if _file_has_any_marker(
                profile_read_path("exec-voice-guide.md"),
                ["[Exec name]", "[phrase]", "[e.g.", "[Name]"],
            ):
                errors.append(
                    "Executive voice guide is still template text. Run exec-voice-builder or complete the voice profile."
                )

        except Exception as exc:
            errors.append(f"Could not authenticate: {exc}")

    return errors


def _file_has_any_marker(path: Path, markers: list[str]) -> bool:
    if not path.exists():
        return True
    try:
        text = path.read_text(encoding="utf-8").lower()
    except Exception:
        return True
    return any(marker.lower() in text for marker in markers)


# ─── Skill Result ───

@dataclass
class SkillResult:
    """Standardized result from a skill execution."""
    skill: str
    mode: str
    status: str = "ok"  # "ok", "warning", "fatal"
    summary: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    duration_seconds: float = 0.0

    @property
    def is_fatal(self) -> bool:
        return self.status == "fatal"

    def to_dict(self) -> dict[str, Any]:
        return {
            "skill": self.skill,
            "mode": self.mode,
            "status": self.status,
            "fatal": self.is_fatal,
            "summary": self.summary,
            "errors": self.errors,
            "warnings": self.warnings,
            "duration_seconds": self.duration_seconds,
        }


# ─── Skill Runner ───

def run_script(
    script_path: str,
    args: list[str],
    timeout: int = 300,
) -> tuple[str, str, int]:
    """
    Run a Python script and capture stdout (JSON), stderr (progress), exit code.

    M2: injects ATLAS_SHARED_SCRIPTS into the subprocess environment so
    skills that ``import bootstrap`` pick up the shared-scripts path
    without having to recompute it themselves.
    """
    cmd = [sys.executable, str(_PLUGIN_ROOT / script_path)] + args
    env = os.environ.copy()
    env["ATLAS_SHARED_SCRIPTS"] = str(_SHARED_SCRIPTS)
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(_PLUGIN_ROOT),
            env=env,
        )
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "", "Script timed out", 1
    except Exception as exc:
        return "", str(exc), 1


def _normalize_skill_summary(name: str, raw_summary: Any) -> dict[str, Any]:
    """Coerce non-envelope script output into the dict shape SkillResult expects."""
    if isinstance(raw_summary, dict):
        return raw_summary
    if isinstance(raw_summary, list):
        return {
            "items": raw_summary,
            "count": len(raw_summary),
            # inbox-triage fetch returns a bare list of message records.
            # processed keeps downstream session accounting from treating the
            # run as zero-work while still preserving the original payload.
            "processed": len(raw_summary) if name == "inbox-triage" else 0,
        }
    return {"value": raw_summary}


def run_skill(
    name: str,
    script: str,
    args: list[str],
    mode: str = "default",
) -> SkillResult:
    """Execute a skill's script and return a standardized result."""
    start = time.time()
    stdout, stderr, exit_code = run_script(script, args)
    duration = time.time() - start

    if exit_code != 0:
        return SkillResult(
            skill=name, mode=mode, status="fatal",
            errors=[f"Exit code {exit_code}: {stderr.strip()[:500]}"],
            duration_seconds=duration,
        )

    parse_error: str | None = None
    try:
        parsed = json.loads(stdout) if stdout.strip() else {}
        summary = _normalize_skill_summary(name, parsed)
    except json.JSONDecodeError as exc:
        # H5: a skill that exits 0 but emits non-JSON stdout must NOT be
        # reported as ok. Surface the parse failure in the summary and
        # downgrade status. If stderr is also non-empty the skill almost
        # certainly crashed mid-write - treat as fatal.
        parse_error = f"{type(exc).__name__}: {exc}"[:500]
        summary = {"raw_output": stdout[:1000], "parse_error": parse_error}

    errors = summary.get("errors", [])
    status = "ok"
    if errors:
        status = "warning"
    if summary.get("fatal"):
        status = "fatal"
    if parse_error is not None:
        status = "fatal" if stderr.strip() else "warning"

    return SkillResult(
        skill=name, mode=mode, status=status,
        summary=summary,
        errors=[str(e) for e in errors],
        warnings=summary.get("warnings", []),
        duration_seconds=duration,
    )


_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_PLACEHOLDER_EMAILS = {"email@example.com", "name@company.com"}
_REVENUE_KEYWORDS = [
    "proposal", "pricing", "quote", "quotation", "renewal", "contract",
    "terms", "deal", "partnership", "revenue", "mrr",
    "arr", "acv", "po number", "po#",
]
_ACCOUNT_MANAGEMENT_PATTERNS = [
    "our subscription", "your subscription", "pause our subscription",
    "pause your subscription", "reactivate", "reactivation",
    "your account", "our account", "grandfathered", "membership active",
    "billing portal", "customer support", "support ticket",
]
_EXEC_DECISION_KEYWORDS = [
    "needs your approval", "awaiting your approval", "please approve",
    "need your decision", "decision needed", "your decision",
    "sign off", "sign-off", "please sign", "signature requested",
    "sign document", "final approval",
]
_SECURITY_ACTION_KEYWORDS = [
    "share request", "requesting access", "accept invitation",
    "invited you to collaborate", "password changed",
    "review this sign in", "security alert", "verify it's you",
    "verification code", "two-factor", "2fa", "reset your password",
]
_PROMO_PATTERNS = [
    "gift card", "signup offer", "ends today", "special offer", "limited time",
    "unsubscribe", "manage preferences", "view in browser", "you've been approved",
]
_MEETING_RECAP_PATTERNS = [
    "recap for", "meeting summary", "internal meetings", "view meeting",
    "action items", "recording", "transcript",
]
_CALENDAR_UPDATE_PATTERNS = [
    "updated invitation", "accepted:", "declined:", "tentative:",
    "new event:", "canceled:", "canceled event:", "rescheduled:", "add to calendar",
]


def _extract_emails(text: str) -> set[str]:
    emails = {m.lower() for m in _EMAIL_RE.findall(text or "")}
    return {e for e in emails if e not in _PLACEHOLDER_EMAILS}


def _domains_from_emails(emails: set[str]) -> set[str]:
    return {email.split("@", 1)[1] for email in emails if "@" in email}


def _email_domain(email: str) -> str:
    low = (email or "").strip().lower()
    return low.split("@", 1)[1] if "@" in low else ""


def _get_exec_domain(client: Any) -> str:
    try:
        profile = client.get_profile() or {}
        return _email_domain(profile.get("emailAddress", ""))
    except Exception:
        return ""


def _is_internal_thread(
    *,
    sender_emails: set[str],
    to_emails: set[str],
    cc_emails: set[str],
    team_emails: set[str],
    team_domains: set[str],
    exec_domain: str,
) -> bool:
    participant_emails = sender_emails | to_emails | cc_emails
    non_primary_recipient_emails = sender_emails | cc_emails
    participant_domains = _domains_from_emails(participant_emails)
    non_primary_recipient_domains = _domains_from_emails(non_primary_recipient_emails)
    if participant_emails & team_emails:
        return True
    if participant_domains & team_domains:
        return True
    return bool(exec_domain and exec_domain in non_primary_recipient_domains)


def _load_team_context() -> tuple[set[str], set[str]]:
    path = profile_read_path("team-delegation-map.md")
    emails = _extract_emails(path.read_text(encoding="utf-8")) if path.exists() else set()
    domains = {email.split("@", 1)[1] for email in emails if "@" in email}
    return emails, domains


def _load_vip_emails() -> set[str]:
    path = profile_read_path("vip-contacts.md")
    return _extract_emails(path.read_text(encoding="utf-8")) if path.exists() else set()


def _voice_guide_ready() -> bool:
    path = profile_read_path("exec-voice-guide.md")
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    placeholders = ["[Exec name]", "[Name]", "[phrase]", "[e.g.", "[Answer]"]
    return not any(p in text for p in placeholders)


def _contains_any(text: str, phrases: list[str]) -> bool:
    lower = (text or "").lower()
    return any(p in lower for p in phrases)


def _looks_automated(sender: str, combined: str, label_ids: set[str]) -> bool:
    sender_lower = (sender or "").lower()
    automated_sender = sender_lower.startswith(("noreply@", "no-reply@", "notifications@"))
    category_markers = {"CATEGORY_PROMOTIONS", "CATEGORY_UPDATES", "CATEGORY_FORUMS"}
    return automated_sender or _contains_any(combined, ["unsubscribe", "manage preferences", "view in browser"]) or bool(label_ids & category_markers)


def _looks_promotional(subject: str, sender: str, combined: str, label_ids: set[str]) -> bool:
    return _looks_automated(sender, combined, label_ids) or _contains_any(subject, _PROMO_PATTERNS) or _contains_any(combined, _PROMO_PATTERNS)


def _looks_meeting_recap(subject: str, sender: str, combined: str) -> bool:
    sender_lower = (sender or "").lower()
    return "fathom.video" in sender_lower or _contains_any(subject, _MEETING_RECAP_PATTERNS) or _contains_any(combined, _MEETING_RECAP_PATTERNS)


def _looks_calendar_update(subject: str, sender: str, combined: str) -> bool:
    sender_lower = (sender or "").lower()
    return "calendar" in sender_lower or _contains_any(subject, _CALENDAR_UPDATE_PATTERNS) or _contains_any(combined, _CALENDAR_UPDATE_PATTERNS)


def _looks_account_management_thread(combined: str) -> bool:
    return _contains_any(combined, _ACCOUNT_MANAGEMENT_PATTERNS)


def _needs_exec_action(subject: str, sender: str, combined: str) -> tuple[str, str] | None:
    if _contains_any(combined, _SECURITY_ACTION_KEYWORDS):
        return "high", "security / access intervention"
    if _contains_any(combined, _EXEC_DECISION_KEYWORDS):
        return "high", "explicit exec approval / decision"
    return None


def _format_item_preview(record: dict[str, Any], confidence: str, reason: str) -> dict[str, Any]:
    return {
        "message_id": record.get("id", ""),
        "thread_id": record.get("threadId", ""),
        "subject": record.get("subject", ""),
        "from": record.get("from", ""),
        "snippet": record.get("snippet", ""),
        "confidence": confidence,
        "reason": reason,
    }


def _dedupe_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str, str]] = set()
    out: list[dict[str, Any]] = []
    for item in items:
        key = (
            item.get("thread_id", "") or item.get("message_id", ""),
            item.get("subject", ""),
            item.get("from", ""),
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


_REPORT_REASON_LABELS = {
    "security_alert": "security / access review",
    "access_request": "access request",
    "legal_domain": "legal sender",
    "vip_contact": "VIP contact",
    "vip_urgent": "VIP urgent",
    "client_crisis": "client risk",
    "wire_transfer": "payment / wire review",
    "confidential": "confidential",
    "urgent_board": "board urgency",
}


def _report_reason(item: dict[str, Any]) -> str:
    raw = item.get("trigger") or item.get("reason") or "review needed"
    if raw in _REPORT_REASON_LABELS:
        return _REPORT_REASON_LABELS[raw]
    return raw.replace("_", " ")


def _compact_report_text(text: str, *, limit: int = 90) -> str:
    compact = " ".join((text or "").replace("\n", " ").split())
    if not compact:
        return ""
    if len(compact) <= limit:
        return compact
    trimmed = compact[: limit - 1].rstrip(" ,;:-")
    return f"{trimmed}…"


def _action_item_context(item: dict[str, Any]) -> str:
    subject = str(item.get("subject", "") or "")
    snippet = str(item.get("snippet", "") or "")
    reason = _report_reason(item)
    combined = f"{subject} {snippet}".lower()

    if any(token in combined for token in ["accept invitation", "invited to join", "organization", "share request", "requesting access"]):
        return "access invitation or permission change"
    if any(token in combined for token in ["verification code", "verify it", "sign in", "sign-in", "security alert", "1password", "2fa", "two-factor"]):
        return "security verification or sign-in alert"
    if "board" in combined:
        return "board-related request"
    if "legal" in combined:
        return "legal or compliance thread"

    snippet_summary = _compact_report_text(snippet, limit=80)
    if snippet_summary:
        return snippet_summary
    return reason


def _action_item_instruction(item: dict[str, Any]) -> str:
    trigger = str(item.get("trigger", "") or "")
    reason = str(item.get("reason", "") or "").lower()
    subject = str(item.get("subject", "") or "").lower()
    snippet = str(item.get("snippet", "") or "").lower()
    combined = " ".join([trigger, reason, subject, snippet])

    if any(token in combined for token in ["approval", "approve", "decision"]):
        return "approve, decline, or give direction"
    if any(token in combined for token in ["share request", "requesting access", "accept invitation", "invited to join", "access request"]):
        return "confirm whether this access should be granted"
    if any(token in combined for token in ["verification code", "verify it", "sign in", "sign-in", "security alert", "1password", "2fa", "two-factor"]):
        return "confirm whether this was expected"
    if any(token in combined for token in ["board", "vip", "legal", "client risk", "confidential", "wire"]):
        return "review and decide next step"
    return "review and decide next step"


_NO_DRAFT_TRIGGER_LABELS = {
    "security_alert",
    "access_request",
    "wire_transfer",
    "confidential",
    "urgent_board",
}


def _action_item_needs_reply_draft(item: dict[str, Any]) -> bool:
    trigger = (item.get("trigger") or "").strip()
    reason = (item.get("reason") or "").strip().lower()
    sender = item.get("from", "")
    combined = " ".join(
        str(item.get(key, ""))
        for key in ("subject", "snippet", "body_plain", "reason", "trigger")
    )

    if trigger in _NO_DRAFT_TRIGGER_LABELS:
        return False
    if "security / access" in reason or "access request" in reason:
        return False
    if _looks_automated(sender, combined, set()):
        return False
    return True


def _action_item_suffix(item: dict[str, Any], draft_message_ids: set[str]) -> str:
    if not _action_item_needs_reply_draft(item):
        return "review directly"
    if item.get("message_id") in draft_message_ids:
        return "draft ready"
    if not _voice_guide_ready():
        return "draft pending"
    return "review"


def _build_triage_summary(
    fetch_summary: dict[str, Any],
    *,
    mode: str,
    dry_run: bool,
) -> dict[str, Any]:
    from atlas_labels import (
        ACTION_REQUIRED,
        DELEGATED,
        LEADS,
        READ_ONLY,
        RECEIPTS,
        REFERENCE,
        SUBSCRIPTIONS,
        WAITING_FOR,
        is_atlas_label,
    )
    from gmail_client import GmailClient
    from state_store import StateStore

    triage_scripts = _PLUGIN_ROOT / "inbox-triage" / "scripts"
    if str(triage_scripts) not in sys.path:
        sys.path.insert(0, str(triage_scripts))
    from triage_inbox import apply_decisions

    items = list(fetch_summary.get("items", []))
    client = GmailClient()
    labels = client.list_labels()
    atlas_label_ids = {
        label["id"]
        for label in labels
        if is_atlas_label(label.get("name", ""))
    }
    vip_emails = _load_vip_emails()
    team_emails, team_domains = _load_team_context()
    exec_domain = _get_exec_domain(client)
    voice_ready = _voice_guide_ready()

    decisions: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    classifier_errors: list[dict[str, str]] = []
    confidence_flags: list[dict[str, Any]] = []
    item_groups: dict[str, list[dict[str, Any]]] = {
        ACTION_REQUIRED: [],
        LEADS: [],
        DELEGATED: [],
        READ_ONLY: [],
        WAITING_FOR: [],
    }

    for record in items:
        msg_id = record.get("id")
        if not msg_id:
            classifier_errors.append({"message_id": "", "error": "missing id in fetch output"})
            continue
        if record.get("error"):
            classifier_errors.append({"message_id": msg_id, "error": str(record["error"])})
            continue

        label_ids = set(record.get("labelIds", []))
        if label_ids & atlas_label_ids:
            skipped.append({"message_id": msg_id, "reason": "already labeled"})
            continue

        pre = record.get("pre_classification") or {}
        subject = record.get("subject", "")
        sender = record.get("from", "")
        to = record.get("to", "")
        cc = record.get("cc", "")
        body = record.get("body_plain", "")
        snippet = record.get("snippet", "")
        combined = "\n".join([subject, sender, to, cc, snippet, body])
        sender_emails = _extract_emails(sender)
        to_emails = _extract_emails(to)
        cc_emails = _extract_emails(cc)
        looks_internal = _is_internal_thread(
            sender_emails=sender_emails,
            to_emails=to_emails,
            cc_emails=cc_emails,
            team_emails=team_emails,
            team_domains=team_domains,
            exec_domain=exec_domain,
        )
        looks_account_management = _looks_account_management_thread(combined)
        looks_automated = _looks_automated(sender, combined, label_ids)
        looks_promotional = _looks_promotional(subject, sender, combined, label_ids)
        looks_meeting_recap = _looks_meeting_recap(subject, sender, combined)
        looks_calendar_update = _looks_calendar_update(subject, sender, combined)
        exec_action = _needs_exec_action(subject, sender, combined)

        label_name: str | None = None
        confidence = "low"
        reason = ""
        archive = False

        if pre.get("label"):
            label_name = str(pre["label"])
            confidence = str(pre.get("confidence") or "deterministic")
            reason = "deterministic pre-classification"
        elif sender_emails & vip_emails:
            label_name = ACTION_REQUIRED
            confidence = "high"
            reason = "VIP sender"
        elif exec_action:
            label_name = ACTION_REQUIRED
            confidence, reason = exec_action
        elif looks_meeting_recap:
            label_name = REFERENCE
            confidence = "high"
            reason = "meeting recap / transcript pattern"
        elif looks_calendar_update:
            label_name = REFERENCE
            confidence = "high"
            reason = "calendar update / invitation pattern"
        elif looks_promotional:
            label_name = SUBSCRIPTIONS
            confidence = "high"
            reason = "promotional / automated pattern"
        elif looks_automated:
            label_name = SUBSCRIPTIONS
            confidence = "high"
            reason = "automated/newsletter pattern"
        elif looks_internal:
            label_name = DELEGATED
            confidence = "high"
            reason = "internal/team participant detected"
        elif looks_account_management:
            label_name = DELEGATED
            confidence = "medium"
            reason = "existing account / vendor-management thread"
        elif _contains_any(combined, _REVENUE_KEYWORDS):
            label_name = LEADS
            confidence = "medium"
            reason = "revenue-related keywords"
        else:
            label_name = DELEGATED
            confidence = "low"
            reason = "ambiguous, defaulting to EA review"

        if label_name:
            archive = True

        decisions.append({
            "message_id": msg_id,
            "label": label_name,
            "archive": archive,
        })

        if label_name in item_groups:
            item_groups[label_name].append(_format_item_preview(record, confidence, reason))
        if confidence == "medium":
            confidence_flags.append(_format_item_preview(record, confidence, reason))
        if label_name == ACTION_REQUIRED and not voice_ready:
            skipped.append({"message_id": msg_id, "reason": "voice profile missing"})

    if dry_run:
        labeled_counts: dict[str, int] = {}
        archived_count = 0
        for decision in decisions:
            label_name = decision.get("label")
            if label_name:
                labeled_counts[label_name] = labeled_counts.get(label_name, 0) + 1
            if decision.get("archive"):
                archived_count += 1
        apply_result = {
            "labeled": labeled_counts,
            "archived": archived_count,
            "errors": [],
            "processed": len(decisions),
            "session_id": None,
            "skipped_manual": [],
        }
    else:
        apply_result = apply_decisions(client, decisions, store=StateStore(), mode=mode)

    return {
        "mode": mode,
        "scanned": len(items),
        "processed": apply_result.get("processed", len(decisions)),
        "labeled": apply_result.get("labeled", {}),
        "archived": apply_result.get("archived", 0),
        "drafts_created": [],
        "skipped": skipped + apply_result.get("skipped_manual", []),
        "confidence_flags": confidence_flags,
        "action_required_items": item_groups[ACTION_REQUIRED],
        "lead_items": item_groups[LEADS],
        "delegated_items": item_groups[DELEGATED],
        "errors": classifier_errors + apply_result.get("errors", []),
        "session_id": apply_result.get("session_id"),
    }


def _render_report(
    *,
    mode: str,
    results: dict[str, Any],
    health: dict[str, Any],
    quota: dict[str, Any],
) -> dict[str, Any]:
    triage = (results.get("inbox-triage") or {}).get("summary", {})
    escalation = (results.get("escalation-handler") or {}).get("summary", {})
    follow_up = (results.get("follow-up-tracker") or {}).get("summary", {})
    sweep = (results.get("label-sweep") or {}).get("summary", {})

    if mode == "midday":
        handled = int(triage.get("processed", 0) or 0)
        urgent = len(escalation.get("tier1", []) or []) + len(triage.get("action_required_items", []) or [])
        untouched = max(int(triage.get("scanned", 0) or 0) - handled, 0)
        markdown = (
            f"Midday inbox check: {triage.get('scanned', 0)} scanned, {handled} processed, "
            f"{urgent} urgent/action items, {untouched} routine items left for later."
        )
        return {
            "mode": "midday",
            "markdown": markdown,
            "sections_included": ["midday"],
            "item_counts": {"processed": handled, "urgent": urgent},
            "word_count": len(markdown.split()),
        }

    lines: list[str] = []
    sections: list[str] = []
    counts: dict[str, int] = {}

    title = "# Inbox Management Update" if mode == "morning" else "# Inbox EOD Summary"
    lines.append(title)
    lines.append("")

    action_items = _dedupe_items(
        list(escalation.get("tier1", []) or [])
        + list(escalation.get("tier2", []) or [])
        + list(triage.get("action_required_items", []) or [])
    )
    if action_items:
        sections.append("needs_decision")
        counts["needs_decision"] = len(action_items)
        lines.append("## ⚡ Needs Your Decision")
        draft_message_ids = {
            str(item.get("message_id", ""))
            for item in (triage.get("drafts_created", []) or [])
            if item.get("message_id")
        }
        for item in action_items[:7]:
            subject = item.get("subject", "(no subject)")
            sender = item.get("from", "Unknown sender")
            context = _action_item_context(item)
            instruction = _action_item_instruction(item)
            suffix = _action_item_suffix(item, draft_message_ids)
            lines.append(f"- {subject} — {sender} — {context}; {instruction} ({suffix}, ~2m)")
        lines.append("")

    lead_items = _dedupe_items(triage.get("lead_items", []) or [])
    if lead_items:
        sections.append("revenue")
        counts["revenue"] = len(lead_items)
        lines.append("## 💰 Revenue")
        for item in lead_items[:5]:
            lines.append(f"- {item.get('subject', '(no subject)')} — {item.get('from', 'Unknown sender')} — {item.get('reason', 'revenue signal')}")
        lines.append("")

    due_today = follow_up.get("due_today", []) or []
    if due_today:
        sections.append("follow_up")
        counts["follow_up"] = len(due_today)
        lines.append("## ⏰ Following Up Today")
        for item in due_today[:5]:
            lines.append(f"- {item.get('subject', '(no subject)')} — {item.get('category', 'follow-up')} — {item.get('cadence_step', 'due now')}")
        lines.append("")

    from atlas_labels import DELEGATED, READ_ONLY, RECEIPTS, REFERENCE, SUBSCRIPTIONS, WAITING_FOR

    labeled_counts = triage.get("labeled", {}) or {}
    handled_labels = {READ_ONLY, WAITING_FOR, RECEIPTS, REFERENCE, SUBSCRIPTIONS}
    handled_count = sum(int(labeled_counts.get(label, 0) or 0) for label in handled_labels)
    delegated_count = int(labeled_counts.get(DELEGATED, 0) or len(triage.get("delegated_items", []) or []))
    if handled_count or delegated_count:
        sections.append("handled")
        counts["handled"] = handled_count + delegated_count
        lines.append("## ✅ Handled For You")
        if handled_count:
            lines.append(f"- {handled_count} routine items labeled and moved out of Inbox automatically")
        if delegated_count:
            lines.append(f"- {delegated_count} items routed to 4-Delegated for EA review")
        lines.append("")

    flags = _dedupe_items(triage.get("confidence_flags", []) or [])
    if flags:
        sections.append("confidence")
        counts["confidence"] = len(flags)
        lines.append("## ⚠ Confidence Flags")
        for item in flags[:7]:
            lines.append(f"- {item.get('subject', '(no subject)')} — {item.get('reason', 'EA verify')} ({item.get('confidence', 'medium')})")
        lines.append("")

    if mode == "eod" and sweep:
        sweep_results = sweep.get("results", {}) or {}
        if sweep_results:
            sections.append("sweep")
            counts["sweep"] = len(sweep_results)
            lines.append("## 🧹 Label Sweep")
            for label, data in sweep_results.items():
                if not any(data.values()):
                    continue
                flagged = data.get("reflag")
                if isinstance(flagged, list):
                    flagged = len(flagged)
                elif flagged is None:
                    flagged = data.get("flagged_ea", 0)
                    if isinstance(flagged, list):
                        flagged = len(flagged)
                lines.append(
                    f"- {label}: archived {data.get('archived', 0)}, kept {data.get('kept', 0)}, flagged {flagged}"
                )
            lines.append("")

    findings = health.get("findings", []) or []
    errored_checks = health.get("errored_checks", []) or []
    if findings or errored_checks:
        sections.append("health")
        counts["health"] = len(findings) + len(errored_checks)
        lines.append("## 📋 Health")
        for finding in findings:
            prefix = "⚠" if finding.get("severity") == "warn" else "❗"
            lines.append(f"- {prefix} {finding.get('check')}: {finding.get('detail')}")
        for check in errored_checks:
            lines.append(f"- ✖ check errored: {check}")
        lines.append("")

    if quota.get("calls_24h") is not None:
        sections.append("quota")
        counts["quota"] = int(quota.get("calls_24h") or 0)
        prefix = "⚠ " if quota.get("over_warn") else ""
        pct = quota.get("pct")
        pct_text = f"{pct:.1f}%" if isinstance(pct, (int, float)) else "unknown"
        lines.append("## 📊 Quota")
        lines.append(f"- {prefix}{quota.get('calls_24h', 0)} API calls in last 24h ({pct_text} of daily budget)")
        lines.append("")

    markdown = "\n".join(lines).strip()
    return {
        "mode": "sod" if mode == "morning" else mode,
        "markdown": markdown,
        "sections_included": sections,
        "item_counts": counts,
        "word_count": len(markdown.split()),
    }


def run_label_reconciliation(mode: str = "default", dry_run: bool = False) -> SkillResult:
    """Run label reconciliation inline (not via subprocess)."""
    start = time.time()
    if dry_run:
        return SkillResult(
            skill="label-reconciliation", mode=mode, status="ok",
            summary={"dry_run": True, "note": "skipped in dry-run mode"},
            duration_seconds=time.time() - start,
        )
    try:
        from state_store import StateStore
        from gmail_client import GmailClient
        client = GmailClient()
        store = StateStore()
        result = store.reconcile_labels(client)
        return SkillResult(
            skill="label-reconciliation", mode=mode, status="ok",
            summary=result, duration_seconds=time.time() - start,
        )
    except Exception as exc:
        return SkillResult(
            skill="label-reconciliation", mode=mode, status="warning",
            errors=[str(exc)], duration_seconds=time.time() - start,
        )


# ─── Chain Definition ───

UNTRIAGED_INBOX_QUERY = (
    'in:inbox '
    '-label:"0-Leads" '
    '-label:"1-Action Required" '
    '-label:"2-Read Only" '
    '-label:"3-Waiting For" '
    '-label:"4-Delegated" '
    '-label:"5-Follow Up" '
    '-label:"6-Receipts/Invoices" '
    '-label:"7-Subscriptions" '
    '-label:"8-Reference"'
)

UNTRIAGED_MIDDAY_QUERY = UNTRIAGED_INBOX_QUERY + ' is:unread newer_than:6h'
TRIAGE_DRAIN_MODES = {"morning", "eod"}
TRIAGE_MAX_BATCHES = 10


def _run_triage_batches(
    *,
    mode: str,
    dry_run: bool,
    session_id: str,
    batch_size: int,
    run_batch: Callable[[int], "SkillResult"],
) -> "SkillResult":
    """Run triage batch-by-batch until the session should stop.

    This centralizes the drain-to-zero loop so orchestrated and future
    standalone/full-triage entry points can share one implementation.
    """
    log = get_logger()
    max_batches = 1 if dry_run or mode not in TRIAGE_DRAIN_MODES else TRIAGE_MAX_BATCHES

    combined_summary: dict[str, Any] = {
        "mode": mode,
        "scanned": 0,
        "processed": 0,
        "labeled": {},
        "archived": 0,
        "drafts_created": [],
        "skipped": [],
        "confidence_flags": [],
        "action_required_items": [],
        "lead_items": [],
        "delegated_items": [],
        "errors": [],
        "session_id": None,
        "batch_count": 0,
        "batch_size": batch_size,
        "drained_to_zero": False,
    }
    total_duration = 0.0
    warnings: list[str] = []

    for batch_num in range(1, max_batches + 1):
        if max_batches > 1:
            print(
                f"  inbox-triage batch {batch_num}/{max_batches}...",
                file=sys.stderr,
            )
        log.event(
            "triage_batch_start",
            session_id=session_id,
            mode=mode,
            batch=batch_num,
            batch_size=batch_size,
        )

        result = run_batch(batch_num)
        total_duration += result.duration_seconds
        if result.is_fatal:
            result.duration_seconds = total_duration
            return result

        summary = result.summary or {}
        last_batch_count = int(summary.get("scanned", 0) or 0)
        combined_summary["scanned"] += last_batch_count
        combined_summary["processed"] += int(summary.get("processed", 0) or 0)
        combined_summary["archived"] += int(summary.get("archived", 0) or 0)
        combined_summary["drafts_created"].extend(summary.get("drafts_created", []) or [])
        combined_summary["skipped"].extend(summary.get("skipped", []) or [])
        combined_summary["confidence_flags"].extend(summary.get("confidence_flags", []) or [])
        combined_summary["action_required_items"].extend(summary.get("action_required_items", []) or [])
        combined_summary["lead_items"].extend(summary.get("lead_items", []) or [])
        combined_summary["delegated_items"].extend(summary.get("delegated_items", []) or [])
        combined_summary["errors"].extend(summary.get("errors", []) or [])
        combined_summary["session_id"] = summary.get("session_id") or combined_summary["session_id"]
        combined_summary["batch_count"] = batch_num
        for label_name, count in (summary.get("labeled", {}) or {}).items():
            combined_summary["labeled"][label_name] = combined_summary["labeled"].get(label_name, 0) + int(count or 0)

        log.event(
            "triage_batch_end",
            session_id=session_id,
            mode=mode,
            batch=batch_num,
            scanned=last_batch_count,
            processed=int(summary.get("processed", 0) or 0),
            archived=int(summary.get("archived", 0) or 0),
            error_count=len(result.errors),
        )

        if dry_run or mode not in TRIAGE_DRAIN_MODES:
            break
        if last_batch_count == 0 or last_batch_count < batch_size:
            combined_summary["drained_to_zero"] = True
            break

    combined_summary["confidence_flags"] = _dedupe_items(combined_summary["confidence_flags"])
    combined_summary["action_required_items"] = _dedupe_items(combined_summary["action_required_items"])
    combined_summary["lead_items"] = _dedupe_items(combined_summary["lead_items"])
    combined_summary["delegated_items"] = _dedupe_items(combined_summary["delegated_items"])

    if not dry_run and mode in TRIAGE_DRAIN_MODES and not combined_summary["drained_to_zero"]:
        warnings.append(
            f"Stopped after {combined_summary['batch_count']} triage batches ({batch_size} per batch) before reaching zero."
        )
    if dry_run and mode in TRIAGE_DRAIN_MODES:
        warnings.append("Dry run previewed one triage batch only. Live runs continue batching until the untriaged inbox is clear or the safety cap is hit.")

    return SkillResult(
        skill="inbox-triage",
        mode=mode,
        status="warning" if combined_summary["errors"] or warnings else "ok",
        summary=combined_summary,
        errors=[str(e) for e in combined_summary["errors"]],
        warnings=warnings,
        duration_seconds=total_duration,
    )

# Each step: name, script path, args builder function
CHAINS: dict[str, list[dict[str, Any]]] = {
    "morning": [
        {"name": "label-reconciliation",
         "script": None,  # runs inline via run_label_reconciliation
         "args": [],
         "fatal_on_error": False},
        {"name": "escalation-handler",
         "script": "escalation-handler/scripts/scan_escalations.py",
         "args": ["--max", "200", "--apply-label"],
         "fatal_on_error": True},
        {"name": "inbox-triage",
         "script": "inbox-triage/scripts/triage_inbox.py",
         "args": ["fetch", "--query", UNTRIAGED_INBOX_QUERY, "--max", "100", "--order", "oldest"],
         "fatal_on_error": True},
        {"name": "follow-up-tracker",
         "script": "follow-up-tracker/scripts/check_followups.py",
         "args": ["scan"],
         "fatal_on_error": False},
        {"name": "inbox-reporter",
         "script": None,
         "args": [],
         "fatal_on_error": False},
    ],
    "midday": [
        {"name": "label-reconciliation",
         "script": None,  # runs inline
         "args": [],
         "fatal_on_error": False},
        {"name": "escalation-handler",
         "script": "escalation-handler/scripts/scan_escalations.py",
         "args": ["--query", "in:inbox is:unread newer_than:6h", "--max", "50",
                  "--apply-label"],
         "fatal_on_error": True},
        {"name": "inbox-triage",
         "script": "inbox-triage/scripts/triage_inbox.py",
         "args": ["fetch", "--query", UNTRIAGED_MIDDAY_QUERY,
                  "--max", "50", "--order", "newest"],
         "fatal_on_error": False},
        {"name": "inbox-reporter",
         "script": None,
         "args": [],
         "fatal_on_error": False},
    ],
    "eod": [
        {"name": "label-reconciliation",
         "script": None,  # runs inline
         "args": [],
         "fatal_on_error": False},
        {"name": "escalation-handler",
         "script": "escalation-handler/scripts/scan_escalations.py",
         "args": ["--max", "200", "--apply-label"],
         "fatal_on_error": True},
        {"name": "inbox-triage",
         "script": "inbox-triage/scripts/triage_inbox.py",
         "args": ["fetch", "--query", UNTRIAGED_INBOX_QUERY, "--max", "100", "--order", "newest"],
         "fatal_on_error": True},
        {"name": "follow-up-tracker",
         "script": "follow-up-tracker/scripts/check_followups.py",
         "args": ["scan"],
         "fatal_on_error": False},
        {"name": "label-sweep",
         "script": "inbox-triage/scripts/label_sweep.py",
         "args": [],
         "fatal_on_error": False},
        {"name": "inbox-reporter",
         "script": None,
         "args": [],
         "fatal_on_error": False},
    ],
}


class OrchestratorChain:
    """Represents a chain of skills to execute for a given mode."""

    def __init__(self, mode: str, session_id: str = ""):
        self.mode = mode
        self.session_id = session_id
        self.steps = CHAINS.get(mode, CHAINS["morning"])
        self.results: dict[str, SkillResult] = {}

    @staticmethod
    def _triage_batch_size(args: list[str]) -> int:
        try:
            idx = args.index("--max")
            return int(args[idx + 1])
        except (ValueError, IndexError, TypeError):
            return 100

    def _run_triage_step(self, step: dict[str, Any], dry_run: bool) -> SkillResult:
        args = list(step["args"])
        batch_size = self._triage_batch_size(args)
        def _run_one_batch(_: int) -> SkillResult:
            result = run_skill("inbox-triage", step["script"], args, mode=self.mode)
            if not result.is_fatal:
                try:
                    result.summary = _build_triage_summary(
                        result.summary,
                        mode=self.mode,
                        dry_run=dry_run,
                    )
                    result.errors = [str(e) for e in result.summary.get("errors", [])]
                    result.warnings = list(result.summary.get("warnings", []))
                    result.status = "warning" if result.errors else "ok"
                except Exception as exc:
                    result = SkillResult(
                        skill="inbox-triage",
                        mode=self.mode,
                        status="fatal",
                        errors=[f"triage post-process failed: {exc}"],
                        duration_seconds=result.duration_seconds,
                    )
            return result

        return _run_triage_batches(
            mode=self.mode,
            dry_run=dry_run,
            session_id=self.session_id,
            batch_size=batch_size,
            run_batch=_run_one_batch,
        )

    def run(self, dry_run: bool = False, exec_email: str = "") -> dict[str, Any]:
        """Execute the full chain, collecting results."""
        log = get_logger()
        halted = False
        halt_reason = ""

        for step in self.steps:
            name = step["name"]
            log.event(
                "skill_start",
                session_id=self.session_id,
                skill=name,
                mode=self.mode,
            )

            if name == "label-reconciliation":
                result = run_label_reconciliation(mode=self.mode, dry_run=dry_run)
                self.results[name] = result
                print(f"  {name}: {result.status} ({result.duration_seconds:.1f}s)", file=sys.stderr)
            elif step["script"] is None:
                result = SkillResult(
                    skill=name, mode=self.mode, status="ok",
                    summary={"note": "Agent-driven skill, no script execution"},
                )
                self.results[name] = result
            elif name == "inbox-triage":
                result = self._run_triage_step(step, dry_run=dry_run)
                self.results[name] = result
                print(
                    f"  {name}: {result.status} "
                    f"({result.duration_seconds:.1f}s, "
                    f"{len(result.errors)} errors, "
                    f"{result.summary.get('batch_count', 1)} batches)",
                    file=sys.stderr,
                )
            else:
                args = list(step["args"])
                if name in ("follow-up-tracker", "label-sweep") and exec_email:
                    args.extend(["--exec-email", exec_email])
                if dry_run and name != "inbox-triage":
                    args.append("--dry-run")

                result = run_skill(name, step["script"], args, mode=self.mode)
                self.results[name] = result
                print(
                    f"  {name}: {result.status} "
                    f"({result.duration_seconds:.1f}s, "
                    f"{len(result.errors)} errors)",
                    file=sys.stderr,
                )

            log.event(
                "skill_end",
                session_id=self.session_id,
                skill=name,
                mode=self.mode,
                status=result.status,
                duration_seconds=round(result.duration_seconds, 3),
                error_count=len(result.errors),
            )

            if result.is_fatal and step["fatal_on_error"]:
                halted = True
                halt_reason = f"{name} failed: {'; '.join(result.errors[:3])}"
                log.event(
                    "skill_fatal",
                    session_id=self.session_id,
                    skill=name,
                    mode=self.mode,
                    reason=halt_reason,
                )
                break

        return {
            "mode": self.mode,
            "halted": halted,
            "halt_reason": halt_reason,
            "results": {k: v.to_dict() for k, v in self.results.items()},
            "total_duration": sum(
                r.duration_seconds for r in self.results.values()
            ),
        }


# ─── CLI ───

def _run_session(args: argparse.Namespace) -> int:
    """Body of a single orchestrator session. Extracted so main() can wrap it in a session lock."""
    log = get_logger()
    session_id = _session_id()
    mode = detect_mode(override=args.mode if args.mode != "auto" else None)
    start_ts = time.monotonic()

    log.event(
        "session_start",
        session_id=session_id,
        mode=mode,
        dry_run=bool(args.dry_run),
    )

    # C4: prune the quota log at session start too (not just in _finish()).
    # A crashed previous run where _finish() never executed would otherwise
    # leave stale 24h+ entries in api_calls until the next clean exit.
    # _prune_quota_state() is failure-soft; logger / quota failures cannot
    # break a working run (observability-failure invariant).
    _prune_quota_state()

    def _finish(exit_code: int, halted: bool = False, halt_reason: str = "") -> int:
        snap = _quota_snapshot()
        log.event(
            "quota_snapshot",
            session_id=session_id,
            calls_24h=snap["calls_24h"],
            budget=snap["budget"],
            pct=snap["pct"],
            over_warn=snap["over_warn"],
        )
        log.event(
            "session_end",
            session_id=session_id,
            mode=mode,
            exit_code=exit_code,
            duration_seconds=round(time.monotonic() - start_ts, 3),
            halted=halted,
            halt_reason=halt_reason,
        )
        _prune_quota_state()
        return exit_code

    should_run, guard_msg = check_session_rate_limit(mode, force=args.force)
    if not should_run:
        print(f"Skipping run: {guard_msg}", file=sys.stderr)
        return _finish(0)

    print(f"Running {mode} inbox zero...", file=sys.stderr)

    health_report = _run_health_preflight(session_id)

    # M1: Preflight is gating, not advisory. If any check raised, or the
    # health module itself blew up, halt the session before launching any
    # skill. This is the deliberate exception to the observability-failure
    # invariant — silently masking a missing-creds/config-drift signal is
    # exactly the failure mode the spec calls out.
    errored = health_report.get("errored_checks") or []
    wrapper_err = health_report.get("wrapper_error")
    if errored or wrapper_err:
        try:
            log.event(
                "health_check_aborted_session",
                session_id=session_id,
                errored_checks=list(errored),
                wrapper_error=wrapper_err or "",
            )
        except Exception:
            pass
        msg = (
            f"Preflight health check failed — aborting session. "
            f"Errored checks: {list(errored) or 'none'}. "
            f"Wrapper error: {wrapper_err or 'none'}."
        )
        print(f"ERROR: {msg}", file=sys.stderr)
        return _finish(2)

    prereq_errors = validate_prerequisites()
    if prereq_errors:
        for err in prereq_errors:
            print(f"ERROR: {err}", file=sys.stderr)
        return _finish(2)

    try:
        from gmail_client import GmailClient
        client = GmailClient()
        exec_email = client.get_profile().get("emailAddress", "")
    except Exception:
        exec_email = ""

    try:
        voice_guide = profile_read_path("exec-voice-guide.md")
        if voice_guide.exists():
            sys.path.insert(0, str(_PLUGIN_ROOT / "exec-voice-builder" / "scripts"))
            from extract_voice import get_voice_guide_age_days
            age = get_voice_guide_age_days(voice_guide)
            if age is not None and age > 30:
                print(
                    f"Warning: Voice guide is {age} days old - "
                    "consider refreshing with exec-voice-builder",
                    file=sys.stderr,
                )
    except Exception:
        pass

    chain = OrchestratorChain(mode, session_id=session_id)
    result = chain.run(dry_run=args.dry_run, exec_email=exec_email)

    if not args.dry_run:
        try:
            from state_store import StateStore
            store = StateStore()
            triage = result["results"].get("inbox-triage", {}).get("summary", {})
            if isinstance(triage, dict):
                processed = int(
                    triage.get("processed", 0)
                    or triage.get("triaged", 0)
                    or triage.get("count", 0)
                    or 0
                )
            elif isinstance(triage, list):
                processed = len(triage)
            else:
                processed = 0
            errors = sum(len(r.get("errors", [])) for r in result["results"].values())
            store.record_session(mode=mode, processed=processed, errors=errors)
            store.prune(max_age_days=30)
            # M6: drop rollback snapshots older than 7 days so the state file
            # stays bounded and stale-session rollbacks don't try to restore
            # labels on messages that may no longer exist.
            store.prune_snapshots(max_age_days=7)
        except Exception:
            pass

    result["quota"] = _quota_snapshot()
    result["health"] = health_report
    result["results"]["inbox-reporter"] = {
        "skill": "inbox-reporter",
        "mode": mode,
        "status": "ok",
        "fatal": False,
        "summary": _render_report(
            mode=mode,
            results=result["results"],
            health=health_report,
            quota=result["quota"],
        ),
        "errors": [],
        "warnings": [],
        "duration_seconds": result["results"].get("inbox-reporter", {}).get("duration_seconds", 0.0),
    }
    print(json.dumps(result, indent=2))
    if result["halted"]:
        print(f"\nChain HALTED: {result['halt_reason']}", file=sys.stderr)
        return _finish(1, halted=True, halt_reason=result["halt_reason"])

    total = result["total_duration"]
    print(f"\n{mode.upper()} inbox zero complete in {total:.0f}s.", file=sys.stderr)
    return _finish(0)


def main() -> int:
    parser = argparse.ArgumentParser(description="Atlas Inbox Zero Orchestrator")
    parser.add_argument(
        "--mode",
        choices=["auto", "morning", "midday", "eod"],
        default="auto",
        help="Triage mode (default: auto-detect from time of day)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run all skills in dry-run mode (no changes to Gmail)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help=(
            f"Override the {SESSION_RATE_GUARD_MINUTES}-minute same-mode "
            "rate guard (use sparingly — repeated runs waste API quota)."
        ),
    )
    args = parser.parse_args()
    lock_path = _CLIENT_PROFILE / SESSION_LOCK_FILENAME
    try:
        with session_lock(
            lock_path,
            timeout=SESSION_LOCK_TIMEOUT,
            stale_after_hours=SESSION_LOCK_STALE_HOURS,
        ):
            return _run_session(args)
    except TimeoutError as exc:
        print(
            f"Another inbox-zero session is already running. "
            f"Waited {SESSION_LOCK_TIMEOUT:.0f}s and giving up. "
            f"Details: {exc}",
            file=sys.stderr,
        )
        return EXIT_LOCK_CONTENTION


if __name__ == "__main__":
    sys.exit(main())
