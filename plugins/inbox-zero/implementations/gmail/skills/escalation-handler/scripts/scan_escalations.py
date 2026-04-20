"""
Scan Inbox for Escalations
==========================
Scans the inbox for red flag / escalation triggers per the Atlas escalation
rules (see references/escalation-rules.md). Runs BEFORE normal triage so that
high-priority items are caught first.

Two tiers:
    - Tier 1 (immediate): board urgent, legal, media, client crisis, resignation,
      wire transfer, confidential, and security alerts. Agent surfaces these
      in-session.
    - Tier 2 (flag in report): large revenue, speaking/board invites, strategic
      partnerships, investor comms, key client feedback, and access requests.

VIP contacts (from client-profile/vip-contacts.md) are ALWAYS escalated.

Usage:
    python scan_escalations.py [--query "in:inbox"] [--max 200] [--apply-label]
                               [--vip-file PATH] [--dry-run]

Output:
    JSON to stdout:
        {
            "scanned": N,
            "tier1": [{id, threadId, subject, from, trigger, snippet}, ...],
            "tier2": [{id, threadId, subject, from, trigger, snippet}, ...],
            "labeled": M,
            "errors": [{id, error}]
        }
    Human-readable progress goes to stderr.

Exit codes:
    0 — scan completed (may still have zero hits)
    1 — auth failure or fatal error
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

# Import the shared Gmail client
_SHARED_SCRIPTS = Path(__file__).resolve().parents[2] / "shared" / "scripts"
if str(_SHARED_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SHARED_SCRIPTS))

from gmail_client import GmailClient
from atlas_labels import ACTION_REQUIRED
from profile_paths import profile_read_path
from state_store import StateStore


# ─────────────────────────────────────────────
# TRIGGER DEFINITIONS
# ─────────────────────────────────────────────

TIER_1_TRIGGERS: dict[str, list[str]] = {
    "legal": [
        "cease and desist", "lawsuit", "litigation", "subpoena", "deposition",
        "settlement agreement", "claim against", "legal notice", "attorney",
        "counsel", "privileged", "legal department", "legal team",
    ],
    "media": [
        "press inquiry", "media inquiry", "journalist", "reporter", "quote for",
        "interview request", "comment on", "for publication", "press release",
        "breaking story",
    ],
    # Strong solo triggers — explicit cancellation, formal complaint, or
    # unambiguous emotional escalation. Single hit is enough.
    "client_crisis": [
        "cancel my contract", "canceling our", "terminate our agreement",
        "terminating the contract", "ending our contract",
        "very disappointed", "escalate this", "losing confidence",
        "extremely unhappy", "file a complaint",
    ],
    "resignation": [
        "my resignation", "i am resigning", "two weeks notice", "my last day",
        "stepping down", "leaving the company", "my departure", "final day",
        "resign from my position",
    ],
    "wire_transfer": [
        "wire transfer", "wire instructions", "routing number", "account number",
        "swift code", "bank details", "payment instructions", "beneficiary account",
        "iban",
    ],
    "confidential": [
        "[confidential]", "confidential:", "attorney-client privileged",
        "highly confidential", "strictly confidential",
    ],
    "security_alert": [
        "password changed", "review this sign in", "please review this sign in",
        "security alert", "verify it's you", "unusual sign-in",
        "suspicious login", "login attempt",
    ],
    "urgent_board": [
        "board urgent", "urgent board", "emergency board", "board emergency",
    ],
}

TIER_2_TRIGGERS: dict[str, list[str]] = {
    "revenue_opportunity": [
        "$50,000", "$50k", "$75,000", "$75k", "$100,000", "$100k", "$250,000",
        "$250k", "$500,000", "$500k", "$1,000,000", "$1m", "$1 million",
        "enterprise deal", "enterprise agreement", "major account",
        "six-figure", "seven-figure", "multi-year contract",
    ],
    "speaking_invite": [
        "speaking engagement", "speaking invitation", "keynote", "panel invitation",
        "conference speaker", "fireside chat", "invited to speak",
    ],
    "board_invite": [
        "board seat", "advisory role", "advisory board", "board invitation",
        "invited to join the board", "join our board", "board appointment",
    ],
    "partnership": [
        "strategic partnership", "joint venture", "co-marketing", "white label",
        "licensing deal", "strategic alliance", "reseller agreement",
    ],
    "investor_comms": [
        "investor update", "cap table", "term sheet", "due diligence",
        "valuation", "funding round", "series a", "series b", "series c",
        "convertible note", "safe note",
    ],
    "key_client_feedback": [
        "case study request", "reference call", "nps", "customer story",
        "testimonial request",
    ],
    "access_request": [
        "share request", "requesting access", "access request",
        "accept invitation", "invited you to collaborate",
        "collaboration invite", "permission request",
        "will soon require 2fa", "require 2fa", "requires 2fa",
        "require two-factor", "requires two-factor",
        "require 2-factor", "requires 2-factor",
    ],
}

# For wire_transfer, require at least 2 signals (otherwise too many false positives
# from banking newsletters, Stripe receipts, etc.)
MULTI_SIGNAL_TRIGGERS = {"wire_transfer"}

# Client-crisis phrases that are too broad to escalate solo. They fire only
# when paired with a contract/service noun (signaling the email is actually
# *about* a client engagement) — otherwise they false-fire on contractor
# updates, support inquiries, etc. Keep this split deliberate; do not collapse
# back into the strong list without revisiting the false-positive analysis.
CLIENT_CRISIS_CONTEXT_TRIGGERS: list[str] = ["not working", "refund"]
_CLIENT_CONTEXT_NOUNS: list[str] = [
    "contract", "agreement", "service", "integration",
    "subscription", "engagement", "deliverable",
]

# Context patterns that disqualify a Tier 1 hit (±30 chars around match)
_CASUAL_MARKERS = ["lol", "haha", "jk", "joke", "kidding", "lmao", "metaphor", "😂", "🤣"]
_HYPOTHETICAL_MARKERS = [
    "would be", "waiting to happen", "like a", "feels like", "almost",
    "could be", "might be", "sounds like",
]
_RESOLVED_MARKERS = [
    "we settled", "we resolved", "dropped the", "dismissed", "closed the",
    "wrapped up", "all good", "sorted out",
]
_DISQUALIFYING_CONTEXT = _CASUAL_MARKERS + _HYPOTHETICAL_MARKERS + _RESOLVED_MARKERS

# Receipt/newsletter sender patterns that skip wire_transfer trigger
_RECEIPT_SENDER_PATTERNS = [
    r"noreply@", r"no-reply@", r"@stripe\.com", r"@paypal\.com",
    r"@square\.com", r"@venmo\.com", r"@wise\.com", r"@brex\.com",
    r"notifications@", r"receipts@",
]

_LEGAL_DOMAIN_PATTERNS = [
    r"law[.\-]", r"legal[.\-]", r"attorney", r"counsel",
    r"court[.\-]", r"lawfirm", r"solicitor",
]


# ─────────────────────────────────────────────
# VIP LOADING
# ─────────────────────────────────────────────

def load_vip_emails(vip_file: Path) -> set[str]:
    """
    Parse vip-contacts.md and return the set of lowercased VIP email addresses.
    Recognises markdown table rows with an email-like value in any cell.
    Returns an empty set if the file is missing or empty.
    """
    if not vip_file.exists():
        return set()

    email_pattern = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
    vips: set[str] = set()

    for line in vip_file.read_text(encoding="utf-8").splitlines():
        for match in email_pattern.findall(line):
            # Skip the placeholder example address from the template
            if match.lower() == "email@example.com":
                continue
            vips.add(match.lower())

    return vips


# ─────────────────────────────────────────────
# TRIGGER MATCHING
# ─────────────────────────────────────────────

def count_matches(text: str, phrases: list[str]) -> list[str]:
    """Return the list of phrases that appear in text (case-insensitive)."""
    lower = text.lower()
    return [p for p in phrases if p.lower() in lower]


def _has_disqualifying_context(text: str, match_phrase: str) -> bool:
    """
    Check if the ±30 character window around a match contains casual,
    hypothetical, or resolved language that disqualifies it.
    """
    lower = text.lower()
    idx = lower.find(match_phrase.lower())
    if idx == -1:
        return False
    window_start = max(0, idx - 30)
    window_end = min(len(lower), idx + len(match_phrase) + 30)
    window = lower[window_start:window_end]
    return any(marker in window for marker in _DISQUALIFYING_CONTEXT)


def _is_receipt_sender(sender: str) -> bool:
    """Check if sender matches known receipt/newsletter patterns."""
    sender_lower = sender.lower()
    return any(re.search(p, sender_lower) for p in _RECEIPT_SENDER_PATTERNS)


def classify_message(
    subject: str,
    body_snippet: str,
    sender: str,
    vip_emails: set[str],
) -> tuple[str | None, str | None]:
    """
    Classify a message as tier1, tier2, or None.

    Returns:
        (tier, trigger_label) where tier is "tier1", "tier2", or None.
    """
    combined = f"{subject}\n{body_snippet}"
    sender_lower = sender.lower()

    # VIP check (Pass 1)
    is_vip = any(vip in sender_lower for vip in vip_emails)

    # Tier 1 scan
    for category, phrases in TIER_1_TRIGGERS.items():
        hits = count_matches(combined, phrases)

        # Wire transfer: skip entirely if sender is a receipt/newsletter sender
        if category == "wire_transfer" and _is_receipt_sender(sender):
            continue

        if category in MULTI_SIGNAL_TRIGGERS:
            if len(hits) >= 2:
                return "tier1", category
        elif hits:
            # Context-aware check: look for disqualifying context around each hit
            genuine_hits = [h for h in hits if not _has_disqualifying_context(combined, h)]
            if genuine_hits:
                return "tier1", category
            # All hits had disqualifying context — downgrade to needs_ai_review
            # (handled by the ambiguity signal pass, not returned as tier1)

    # Client-crisis context-required triggers: phrase + contract/service noun.
    # ("the API is not working" from a contractor → no escalation;
    #  "your service is not working, we're considering canceling" → escalation.)
    context_hits = count_matches(combined, CLIENT_CRISIS_CONTEXT_TRIGGERS)
    if context_hits and any(noun in combined.lower() for noun in _CLIENT_CONTEXT_NOUNS):
        genuine = [h for h in context_hits if not _has_disqualifying_context(combined, h)]
        if genuine:
            return "tier1", "client_crisis"

    # Sender domain check: if domain looks legal, auto-flag
    if "@" in sender_lower:
        domain = sender_lower.split("@", 1)[1]
        if any(re.search(p, domain) for p in _LEGAL_DOMAIN_PATTERNS):
            return "tier2", "legal_domain"

    # VIP sender auto-escalates to at least tier2 (tier1 if combined with urgency word)
    if is_vip:
        urgency_hits = count_matches(combined, ["urgent", "asap", "emergency", "today"])
        if urgency_hits:
            return "tier1", "vip_urgent"
        return "tier2", "vip_contact"

    # Tier 2 scan
    for category, phrases in TIER_2_TRIGGERS.items():
        hits = count_matches(combined, phrases)
        if hits:
            return "tier2", category

    return None, None


# ─────────────────────────────────────────────
# AMBIGUITY SIGNALS — for AI second pass
# ─────────────────────────────────────────────

# Patterns that suggest the email might be important but didn't hit keywords
AMBIGUITY_SIGNALS: dict[str, list[str]] = {
    "tone_serious": [
        "please advise", "concerned about", "we need to discuss",
        "this is important", "time-sensitive", "require your attention",
        "at your earliest", "as soon as possible", "deadline",
        "matter of urgency", "please respond", "immediate attention",
    ],
    "authority_language": [
        "on behalf of", "authorized to", "representing",
        "instructed to", "formal notice", "for the record",
        "put on notice", "reserve the right", "all available options",
    ],
    "financial_concern": [
        "outstanding balance", "overdue", "past due", "collections",
        "final notice", "payment demand", "accounts receivable",
        "breach of contract", "material breach",
    ],
    "demand_language": [
        "hereby demand", "final opportunity", "reserves all rights",
        "failure to comply", "all available remedies", "pursuant to",
        "without prejudice", "we demand", "must comply", "legal remedies",
    ],
}


def detect_ambiguity_signals(
    subject: str,
    body_snippet: str,
) -> list[str]:
    """
    Detect signals that an email might need escalation but didn't
    match the hard keyword triggers. Returns a list of signal names.
    Used to flag items for AI second-pass review.
    """
    combined = f"{subject}\n{body_snippet}".lower()
    signals = []
    for category, phrases in AMBIGUITY_SIGNALS.items():
        hits = [p for p in phrases if p in combined]
        if len(hits) >= 2:  # require 2+ signals to flag for review
            signals.append(category)
    return signals


def detect_ambiguity_signals_v2(
    subject: str,
    body_snippet: str,
    sender: str = "",
    known_senders: set[str] | None = None,
) -> list[str]:
    """
    Enhanced ambiguity detection with sender awareness.

    Changes from v1:
    - 1 signal from authority_language or demand_language + unknown sender = flag
    - Original 2-signal threshold remains for tone_serious and financial_concern
    """
    combined = f"{subject}\n{body_snippet}".lower()
    signals = []
    sender_lower = sender.lower()
    is_unknown = True
    if known_senders:
        is_unknown = not any(k in sender_lower for k in known_senders)

    for category, phrases in AMBIGUITY_SIGNALS.items():
        hits = [p for p in phrases if p in combined]
        # Lowered threshold for authority + demand when sender is unknown
        if category in ("authority_language", "demand_language") and is_unknown:
            if len(hits) >= 1:
                signals.append(category)
        elif len(hits) >= 2:
            signals.append(category)
    return signals


# ─────────────────────────────────────────────
# MAIN SCAN
# ─────────────────────────────────────────────

def scan(
    client: GmailClient,
    query: str,
    max_messages: int,
    vip_emails: set[str],
    apply_label: bool,
    dry_run: bool,
) -> dict[str, Any]:
    """Run the escalation scan and return structured results."""
    print(f"Scanning up to {max_messages} messages matching: {query}", file=sys.stderr)

    raw_stubs = client.search_all_messages(query, max_results=max_messages)
    print(f"Found {len(raw_stubs)} matching messages before thread dedupe.", file=sys.stderr)

    # Escalation output should be conversation-level, not one line for every
    # message in a long thread. Keep only the newest message per thread.
    stubs: list[dict[str, Any]] = []
    seen_threads: set[str] = set()
    deduped_messages = 0
    for stub in raw_stubs:
        thread_id = stub.get("threadId") or stub["id"]
        if thread_id in seen_threads:
            deduped_messages += 1
            continue
        seen_threads.add(thread_id)
        stubs.append(stub)
    print(f"Scanning {len(stubs)} deduped threads.", file=sys.stderr)

    # Resolve the 1-Action Required label ID once if we'll be applying it
    action_label_id: str | None = None
    store: StateStore | None = None
    if apply_label and not dry_run and stubs:
        label = client.find_label_by_name(ACTION_REQUIRED)
        if not label:
            raise RuntimeError(
                f"Label '{ACTION_REQUIRED}' not found. Run inbox-onboarding first."
            )
        action_label_id = label["id"]
        try:
            store = StateStore()
        except Exception:
            store = None

    tier1: list[dict[str, Any]] = []
    tier2: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    labeled = 0
    archived = 0

    for i, stub in enumerate(stubs, start=1):
        if i % 25 == 0:
            print(f"  scanned {i}/{len(stubs)}...", file=sys.stderr)

        try:
            msg = client.read_message(stub["id"], format="full")
            headers = client.get_message_headers(msg)
            subject = headers.get("subject", "")
            sender = headers.get("from", "")
            body = client.get_message_body(msg)
            snippet = body[:500] if body else msg.get("snippet", "")
            current_label_ids = set(msg.get("labelIds", []))

            tier, trigger = classify_message(subject, snippet, sender, vip_emails)
            if tier is None:
                continue

            record = {
                "id": stub["id"],
                "threadId": stub.get("threadId"),
                "subject": subject,
                "from": sender,
                "trigger": trigger,
                "snippet": snippet[:200].replace("\n", " ").strip(),
            }

            if tier == "tier1":
                tier1.append(record)
            else:
                tier2.append(record)

            if apply_label and not dry_run and action_label_id:
                add_label_ids = [action_label_id] if action_label_id not in current_label_ids else None
                remove_label_ids = ["INBOX"] if "INBOX" in current_label_ids else None
            else:
                add_label_ids = None
                remove_label_ids = None

            if add_label_ids or remove_label_ids:
                try:
                    client.modify_message(
                        stub["id"],
                        add_label_ids=add_label_ids,
                        remove_label_ids=remove_label_ids,
                    )
                    if add_label_ids:
                        labeled += 1
                        if store is not None:
                            try:
                                store.record_label_applied(stub["id"], ACTION_REQUIRED)
                            except Exception:
                                pass
                    if remove_label_ids:
                        archived += 1
                except Exception as exc:  # noqa: BLE001
                    errors.append({"id": stub["id"], "error": f"label/archive apply: {exc}"})

        except Exception as exc:  # noqa: BLE001
            errors.append({"id": stub["id"], "error": str(exc)})

    # Second pass: flag ambiguous items for AI review
    needs_ai_review: list[dict[str, Any]] = []
    tier_ids = {r["id"] for r in tier1} | {r["id"] for r in tier2}
    for stub in stubs:
        msg_id = stub["id"]
        # Skip items already caught by tier1/tier2
        if msg_id in tier_ids:
            continue

        try:
            msg = client.read_message(msg_id, format="full")
            headers = client.get_message_headers(msg)
            subject = headers.get("subject", "")
            body = client.get_message_body(msg)
            snippet = body[:500] if body else msg.get("snippet", "")

            signals = detect_ambiguity_signals(subject, snippet)
            if signals:
                needs_ai_review.append({
                    "id": msg_id,
                    "threadId": stub.get("threadId"),
                    "subject": subject,
                    "from": headers.get("from", ""),
                    "signals": signals,
                    "snippet": snippet[:200].replace("\n", " ").strip(),
                })
        except Exception:  # noqa: BLE001
            pass  # ambiguity detection is best-effort

    return {
        "scanned": len(stubs),
        "raw_matches": len(raw_stubs),
        "deduped_messages": deduped_messages,
        "tier1": tier1,
        "tier2": tier2,
        "needs_ai_review": needs_ai_review,
        "labeled": labeled,
        "archived": archived,
        "errors": errors,
        "dry_run": dry_run,
        "vip_count": len(vip_emails),
    }


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────

def default_vip_file() -> Path:
    return profile_read_path("vip-contacts.md")


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan Gmail for escalation triggers.")
    parser.add_argument(
        "--query",
        default="newer_than:3d (in:inbox OR label:1-action-required OR label:2-read-only OR label:3-waiting-for OR label:4-delegated)",
        help="Gmail search query (default: inbox + recently labeled items)",
    )
    parser.add_argument(
        "--max",
        type=int,
        default=200,
        help="Max messages to scan (default: 200)",
    )
    parser.add_argument(
        "--apply-label",
        action="store_true",
        help="Apply 1-Action Required to escalated items",
    )
    parser.add_argument(
        "--vip-file",
        type=Path,
        default=None,
        help="Path to vip-contacts.md (default: client-profile/vip-contacts.md)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not apply labels, only report findings",
    )
    args = parser.parse_args()

    vip_file = args.vip_file or default_vip_file()
    vip_emails = load_vip_emails(vip_file)
    print(f"Loaded {len(vip_emails)} VIP addresses from {vip_file}", file=sys.stderr)

    try:
        client = GmailClient()
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: could not authenticate: {exc}", file=sys.stderr)
        return 1

    try:
        result = scan(
            client=client,
            query=args.query,
            max_messages=args.max,
            vip_emails=vip_emails,
            apply_label=args.apply_label,
            dry_run=args.dry_run,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR during scan: {exc}", file=sys.stderr)
        return 1

    # Human-readable summary to stderr
    print(
        f"\nDone. Tier 1: {len(result['tier1'])}, "
        f"Tier 2: {len(result['tier2'])}, "
        f"Labeled: {result['labeled']}, "
        f"Errors: {len(result['errors'])}",
        file=sys.stderr,
    )

    # JSON to stdout for the agent to consume
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
