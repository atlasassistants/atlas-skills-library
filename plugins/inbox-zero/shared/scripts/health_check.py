"""Drift checks against the client-profile.

Phase 1 ships three checks: voice guide age, empty VIP list, basic template
placeholders. Phase 5 extends the template check to the full marker set
(placeholder email domains, empty required sections).

Every check is isolated: if one raises, run_checks records the check name
in errored_checks and continues. run_checks itself never raises."""

from __future__ import annotations

import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path

from constants import VOICE_GUIDE_STALE_DAYS
from profile_paths import profile_read_path


@dataclass(frozen=True)
class HealthFinding:
    check: str
    severity: str           # "info" | "warn" | "error"
    detail: str
    file: str | None = None


@dataclass
class HealthReport:
    findings: list[HealthFinding] = field(default_factory=list)
    errored_checks: list[str] = field(default_factory=list)


_REQUIRED_FILES = (
    "exec-voice-guide.md",
    "vip-contacts.md",
    "team-delegation-map.md",
)

# Literal placeholder markers scanned across all client-profile files.
_BASIC_MARKERS = (
    "TODO",
    "TBD",
    "[Name]",
    "[Role]",
    "[Company]",
    "[email@example.com]",
)

# Domains that appear only in templates; matched inside email addresses.
_TEMPLATE_DOMAINS = ("example.com", "company.com", "acme.com")

# An H2/H3 header followed by nothing but blank lines (and another header
# or EOF) indicates an unfilled required section. Match header + up to two
# whitespace-only lines + (next header | EOF). H1 is skipped — it's almost
# always the document title, not a required-content section.
_EMPTY_SECTION_RE = re.compile(
    r"^(#{2,3})\s+(?P<header>.+?)\s*$\n(?:\s*\n){0,2}(?=#{1,3}\s|\Z)",
    re.MULTILINE,
)

_EMAIL_IN_LINE_RE = re.compile(r"[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+\.[A-Za-z]{2,})")


def _check_voice_guide_age(client_profile: Path) -> list[HealthFinding]:
    path = profile_read_path("exec-voice-guide.md", client_profile_dir=client_profile)
    if not path.exists():
        return [HealthFinding(
            check="voice_guide_age",
            severity="error",
            detail="exec-voice-guide.md not found",
            file=str(path),
        )]
    age_days = int((time.time() - path.stat().st_mtime) // (24 * 3600))
    if age_days >= VOICE_GUIDE_STALE_DAYS:
        return [HealthFinding(
            check="voice_guide_age",
            severity="warn",
            detail=f"voice guide is {age_days} days old (threshold {VOICE_GUIDE_STALE_DAYS})",
            file=str(path),
        )]
    return []


_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def _check_empty_vip_list(client_profile: Path) -> list[HealthFinding]:
    path = profile_read_path("vip-contacts.md", client_profile_dir=client_profile)
    if not path.exists():
        return [HealthFinding(
            check="empty_vip_list",
            severity="error",
            detail="vip-contacts.md not found",
            file=str(path),
        )]
    return []


def _detect_template_domains(text: str) -> list[str]:
    """Return the sorted unique set of template domains found inside email
    addresses in ``text`` (e.g. 'example.com', 'acme.com'). Plain occurrences
    of the word 'example.com' outside an email address are ignored."""
    hits: set[str] = set()
    for match in _EMAIL_IN_LINE_RE.finditer(text):
        domain = match.group(1).lower()
        if domain in _TEMPLATE_DOMAINS:
            hits.add(domain)
    return sorted(hits)


def _detect_empty_sections(text: str) -> list[str]:
    """Return headers of required sections whose body is blank."""
    return [m.group("header").strip() for m in _EMPTY_SECTION_RE.finditer(text)]


def _check_config_templates(client_profile: Path) -> list[HealthFinding]:
    findings: list[HealthFinding] = []
    for name in _REQUIRED_FILES:
        path = profile_read_path(name, client_profile_dir=client_profile)
        if not path.exists():
            continue  # file-missing is caught by other checks where relevant
        text = path.read_text(encoding="utf-8", errors="replace")

        reasons: list[str] = []
        marker_hits = [m for m in _BASIC_MARKERS if m in text]
        if marker_hits:
            reasons.append(f"placeholders: {', '.join(marker_hits)}")

        domain_hits = _detect_template_domains(text)
        if domain_hits:
            reasons.append(f"template domains: {', '.join(domain_hits)}")

        empty_hits = _detect_empty_sections(text)
        if empty_hits:
            reasons.append(f"empty sections: {', '.join(empty_hits)}")

        if reasons:
            findings.append(HealthFinding(
                check="config_template",
                severity="warn",
                detail="; ".join(reasons),
                file=str(path),
            ))
    return findings


_CHECKS = (
    _check_voice_guide_age,
    _check_empty_vip_list,
    _check_config_templates,
)


def run_checks(client_profile: Path) -> HealthReport:
    client_profile = Path(client_profile)
    report = HealthReport()
    # Re-resolve from the module namespace so tests can monkeypatch individual checks
    import health_check as _self
    for fn_ref in _CHECKS:
        name = fn_ref.__name__
        fn = getattr(_self, name, fn_ref)
        try:
            report.findings.extend(fn(client_profile))
        except Exception:
            report.errored_checks.append(name)
    return report
