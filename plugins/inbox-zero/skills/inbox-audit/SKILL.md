---
name: inbox-audit
description: Pre-setup audit of the exec's inbox. Reads the existing label structure, filters, sent folder patterns, and inbox volume before touching anything. Produces a structured audit report that drives onboarding decisions — existing labels to keep or adapt, VIPs identified from reply history, voice patterns from sent folder, and red flags surfaced before any changes are made.
when_to_use: Run once before inbox-onboarding. Trigger phrases: "audit my inbox", "scan my inbox before setup", "run inbox audit", "what does my inbox look like", "check my inbox first". Also triggered automatically by inbox-onboarding if no audit report exists yet.
atlas_methodology: opinionated
---

# inbox-audit

Read the inbox before changing it. Build a system that fits, not one that fights.

## Purpose

Most execs already have a partial system — some labels, a few filters, habits around who they reply to. Forcing Atlas labels on top without understanding the existing structure creates friction, misses obvious wins, and ignores the exec's actual email behavior.

This skill audits the inbox first. It reads what's there, identifies patterns, surfaces red flags, and produces a report that drives every decision in onboarding. The result is a setup that adapts the Atlas system to fit the exec — not the other way around.

## Inputs

- **Email access** — read access to inbox, sent folder, labels, and filters
- **Lookback window** — default 90 days for sent analysis; configurable

## Required capabilities

- **Label list** — read all existing labels with message counts
- **Filter list** — read all existing email filters
- **Sent folder read** — fetch sent messages to analyze reply patterns, timing, and voice
- **Inbox read** — scan inbox for volume, sender distribution, and type breakdown

## Steps

### Step 0 — Credentials check

Before scanning anything, check whether Gmail credentials exist at `client-profile/credentials/credentials.json` and `client-profile/credentials/token.json`.

- **If missing:** run `implementations/gmail/scripts/setup_credentials.py` to walk the user through OAuth setup. Do not proceed until credentials are valid.
- **If present:** skip setup and go straight to scanning.

**Gmail implementation:** `implementations/gmail/skills/inbox-audit/scripts/run_audit.py` handles this check automatically — it calls setup if needed, then runs all scans and saves raw data to `client-profile/inbox-audit.json`.

### Phase 1 — Structural scan

1. **List all existing labels.** For each: name, message count, last active date. Flag labels with zero messages in 90 days as inactive. Flag labels that overlap with Atlas label purposes.

2. **List all existing filters.** For each: condition, action (label/archive/forward/delete), whether it appears to be working. Flag broken or outdated filters (e.g., referencing a domain the exec no longer uses).

3. **Inbox volume snapshot.** Count total inbox messages, unread count, and rough age distribution (today, this week, this month, older). Note if the inbox appears actively managed or backlogged.

### Phase 2 — Sent folder analysis

Sent folder patterns are more reliable than inbox volume — they show what the exec actually prioritizes, not just what arrives.

4. **Top reply-to contacts.** From the last 90 days of sent mail: rank contacts by reply frequency. These are VIP candidates. Note relationship context where inferable from email domain or thread subject.

5. **Reply timing.** Identify when the exec sends most replies (morning, midday, evening). Note whether replies appear batched or spread throughout the day.

6. **Topics that get responses.** From subject lines and thread context: what categories of email reliably get a reply? What gets ignored?

7. **Communication style sample.** Pull 10–15 sent messages across different recipients and contexts. Note: reply length (short/medium/long), tone (formal/semi-formal/casual), greeting and sign-off patterns, whether the exec forwards or delegates vs. replies directly.

### Phase 3 — Inbox pattern analysis

8. **Email type breakdown.** Scan inbox by sender domain, subject patterns, and existing labels. Estimate the proportion of each type: client/lead, internal team, calendar/scheduling, newsletters/subscriptions, invoices/receipts, notifications, personal, cold outreach, other.

9. **Top senders.** Rank by volume. Flag any high-volume sender that isn't filtered or labeled — especially if the exec never replies (noise candidate) or always replies (VIP candidate).

10. **Red flags.** Surface anything worth flagging before touching the inbox:
    - High-priority contacts with old unread messages
    - Mid-conversation threads where replies stopped
    - Sensitive content (legal, HR, board) with no organization
    - Obvious noise sources with no filter
    - Large backlogs by category

### Phase 4 — Setup recommendations

11. **Label system recommendation.** Based on existing labels and inbox patterns, propose which Atlas labels to create as-is, which to create as sub-labels under an existing structure, and which existing labels to keep or rename. The goal is to extend the exec's system, not replace it.

    Example adaptations:
    - Exec already has a "Meetings" folder → create `8-Reference/Meetings` instead of `8-Reference`
    - Top senders are all from one client → create `1-Action Required/[Client]` sub-label
    - Exec has 0 existing labels → standard Atlas 9-label setup applies

12. **VIP list draft.** Propose the initial VIP list from top reply-to contacts. Flag anyone who should clearly be included vs. needs exec confirmation.

13. **Voice guide draft.** From the sent folder sample, draft the initial exec voice profile (style, length, tone, formality, sign-off). Mark it as a first draft — exec confirms or adjusts during onboarding Phase B.

14. **Open questions.** List anything the audit couldn't determine: unclear relationships, ambiguous threads, decisions that need exec input before setup begins.

## Output

Two files written to `client-profile/`:

- **`inbox-audit.json`** — raw scan data (written by scripts, read by onboarding scripts)
- **`inbox-audit.md`** — human-readable report following `references/audit-template.md` (written by agent from JSON data)

After writing the report, also write **`client-profile/label-plan.json`** with the adapted label structure:

```json
{
  "labels": [
    "1-Action Required",
    "1-Action Required/Board",
    "2-Read Only",
    "3-Waiting For",
    "4-Delegated",
    "5-Follow Up",
    "6-Receipts/Invoices",
    "7-Subscriptions",
    "8-Reference",
    "8-Reference/Meetings",
    "0-Leads"
  ],
  "adapted_from": ["Board", "Meetings"],
  "notes": "Board sub-label added (exec has active Board label). Meetings sub-label added (top calendar volume)."
}
```

`inbox-onboarding` reads `label-plan.json` to create the right label structure. If no plan exists, it falls back to the standard 9 Atlas labels.

Brief inline summary to the user:

```
Inbox audit complete.

Structural findings:
- 6 existing labels (3 active, 3 unused)
- 4 filters (2 functional, 2 targeting defunct domains)
- Inbox: ~340 unread, mostly backlog older than 30 days

Sent folder (90 days):
- Top reply-to contacts identified → 7 VIP candidates
- Reply pattern: morning batch, 6–9am
- Voice: direct, 1–3 sentences, semi-formal

Recommended label adaptations:
- Keep existing "Board" label → map to 1-Action Required/Board
- Keep existing "Finance" label → map to 6-Receipts/Finance
- Standard Atlas labels for everything else

Red flags (3):
- 2 unread threads from board contacts (>60 days old)
- No filter for newsletters — ~35% inbox noise
- 1 legal thread with no label or follow-up

Full report: client-profile/inbox-audit.md
Ready to start onboarding? The audit findings will pre-fill VIPs, voice guide, and label structure.
```

## Customization

- **Lookback window.** Default 90 days for sent analysis. Extend to 180 days for execs with lower email volume.
- **VIP threshold.** Default: contacts with ≥5 replies in 90 days are flagged as VIP candidates. Adjust for high-volume senders.
- **Red flag sensitivity.** Default flags unread messages from high-frequency senders older than 30 days. Tighten or loosen per exec.

## Why opinionated

The audit approach encodes the Atlas conviction that setup quality depends on observation quality. Skipping this step and applying a generic label system is the single biggest reason inbox-zero setups fail in the first 30 days. The sent-folder-first heuristic (sent = actual priorities, inbox = noise) is Atlas doctrine and non-negotiable.

**Gmail implementation:** `implementations/gmail/skills/inbox-audit/scripts/`
