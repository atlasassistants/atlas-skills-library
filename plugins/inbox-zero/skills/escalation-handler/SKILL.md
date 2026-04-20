---
name: escalation-handler
description: Red flag detection — runs first in every inbox session, before normal triage. Scans for legal threats, board urgencies, client crises, wire transfer requests, press inquiries, resignations, security alerts, and VIP messages. Tier 1 items surface immediately; Tier 2 items appear in the session report.
when_to_use: Called automatically by inbox-zero before every triage run. Also invoked directly: "check for escalations", "scan for red flags", "any urgent emails", "check escalations". Always runs FIRST — never after triage.
atlas_methodology: opinionated
---

# escalation-handler

Scan for red flags before anything else touches the inbox.

## Purpose

Normal triage is a decision queue. Escalations are a different category: time-sensitive, high-stakes, or high-authority items that must surface immediately regardless of where they fall in the inbox sort order. Running escalation detection after triage risks a legal notice getting archived or a board message getting labeled `2-Read Only`. This skill prevents that by always running first.

## Inputs

- **Scan scope** (optional) — default: inbox + `1-Action Required` from the last 2 days. Adjustable per session.

## Required capabilities

- **Email read** — search messages by sender, subject keywords, and body content across inbox and recent labeled items
- **Label apply** — apply `1-Action Required` to detected escalation items

## Steps

1. **Load references.** `skills/escalation-handler/references/escalation-rules.md` — Tier 1 and Tier 2 trigger definitions, VIP contact matching rules, demand language signals, context-aware downgrade markers.
2. **Read the VIP contact list** fresh from `client-profile/vip-contacts.md`. VIP list is read every scan — not cached.
3. **Run the scan** in three passes:
   - Pass 1: Sender match against VIP list (fastest)
   - Pass 2: Subject scan for trigger keywords
   - Pass 3: Body scan (first ~500 chars) for trigger phrases (slower, only when needed)
4. **Apply context-aware judgment** — casual markers (lol, haha, jk), hypothetical markers (would be, feels like), resolved markers (we settled, resolved) downgrade a hit to `needs_ai_review`. Agent reviews those manually.
5. **Apply `1-Action Required`** to all confirmed escalation items.
6. **Surface Tier 1 items immediately** — do not wait for the report. Alert the user in-session with: trigger type, sender, subject, snippet.
7. **Return summary JSON** — tier1 list, tier2 list, needs_ai_review list, scan counts, any errors.

**Gmail implementation:** `implementations/gmail/skills/escalation-handler/scan_escalations.py`

## Output

Tier 1 items surface in-session immediately:

```
🚨 Escalation detected — action required now

1. [Legal threat] From: counsel@lawfirm.com — "Cease and desist re: trademark use"
   → Labeled 1-Action Required. Do not delegate. Review and call legal.

2. [Client crisis] From: cto@bigclient.com — "Terminating contract if not resolved today"
   → Labeled 1-Action Required. Needs exec response within the hour.
```

JSON summary returned to orchestrator:

```json
{
  "skill": "escalation-handler",
  "status": "ok",
  "summary": {
    "scanned": 134,
    "tier1": [{"id": "...", "from": "...", "subject": "...", "trigger": "legal"}],
    "tier2": [{"id": "...", "trigger": "revenue_opportunity"}],
    "needs_ai_review": [],
    "labeled": 3
  }
}
```

## Customization

- **Escalation rules.** All trigger keywords, domain patterns, and VIP matching logic live in `skills/escalation-handler/references/escalation-rules.md`. Fully editable.
- **Scan scope.** Default searches inbox + recent labeled items. Expand or narrow per deployment.
- **Tier 1 delivery.** Default surfaces in-session as text. Wire to a messaging capability for push notifications if the exec isn't in session.

## Why opinionated

The "always first" rule is non-negotiable. Any architecture that runs escalation detection after triage, or makes it optional, risks missing a time-sensitive item. When in doubt, escalate — the cost of a false positive is a 10-second dismissal; the cost of a false negative is a missed legal notice.
