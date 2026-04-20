# inbox-zero

> Daily inbox management — triage, escalation detection, follow-up cadences, voice-matched drafts, SOD/EOD reports.
> v0.1.0 — `heavyweight` tier.

## What it does

Runs the full inbox management lifecycle for an executive, end to end:

- **Triages every email** through a fixed 9-label decision tree. Every message gets exactly one label. No judgment calls left to chance.
- **Detects escalations first** — before normal triage runs, scans for legal threats, board urgencies, client crises, wire transfers, VIP messages, and surfaces Tier 1 items immediately.
- **Tracks follow-ups automatically** — maintains cadences for every thread where the exec sent something and is waiting. Revenue threads get chased at Day 1/2/4/7. Internal at Day 1/3/5. Vendors at Day 3/Week 2/Week 3.
- **Drafts replies in the exec's voice** — extracts writing patterns from the exec's last 30 sent messages. Every draft sounds like the exec wrote it. The human only hits send.
- **Reports in under two minutes** — structured SOD and EOD reports: what needs a decision, what was handled, what's following up today, what's carryover.

The result: inbox zero every day without the exec touching their inbox.

## Who it's for

Executive assistants and agents managing a high-volume executive inbox. Atlas built this for founder and C-suite workflows where the inbox is a decision queue, not a communications tool — and where the EA's job is to drain that queue, not just read it.

## Required capabilities

The plugin's skills depend on these capabilities. Each is named abstractly — wire it up to whatever tool the host agent has access to.

- **Email read** — search and read messages with filters, queries, and date ranges
- **Label apply** — apply classification labels to messages in the inbox
- **Draft create** — create draft replies (write to drafts folder; never send)
- **Filter create** — set up automated routing rules that fire at message arrival
- **Label create** — create the label taxonomy in the email system (once, during onboarding)
- **State storage** — persist follow-up cadence state between sessions

## Suggested tool wiring

| Capability | Common options |
|---|---|
| Email read | Gmail MCP, Outlook MCP, any email search tool |
| Label apply | Gmail MCP, IMAP label/folder tools |
| Draft create | Gmail MCP, Outlook MCP |
| Filter create | Gmail MCP, email API |
| State storage | Filesystem MCP, any key-value store |

These are examples, not requirements. The **Gmail implementation** (`implementations/gmail/`) ships with production-ready Python scripts for every capability — see below.

## Installation

```
/plugin install inbox-zero@atlas
```

After installing, complete the first-run setup before running any skill.

## First-run setup

> See [`instructions.md`](instructions.md) for the full setup walkthrough.

**Gmail (recommended):** The Gmail implementation ships with a guided onboarding wizard. Run `inbox-onboarding` — it handles credentials, label creation, filter setup, Gmail UI configuration, and initial inbox cleanup in two phases.

**Other providers:** Wire up the capabilities above to your email provider. The skills are provider-agnostic; the Gmail scripts in `implementations/gmail/` are one implementation path.

## Skills included

- **`inbox-zero`** — *opinionated.* The orchestrator. Sequences all other skills in the right order based on time of day. Three modes: morning (full triage + follow-ups → SOD report), midday (quick escalation scan only), EOD (full triage + sweep + follow-ups → EOD report).
- **`inbox-triage`** — *opinionated.* Core daily workflow. Processes every inbox email through the Atlas decision tree in bounded batches, applies exactly one label per message, drafts replies for Action Required items.
- **`escalation-handler`** — *opinionated.* Runs first in every session. Detects legal threats, board urgencies, client crises, wire transfer requests, VIP messages. Tier 1 items surface immediately; Tier 2 in the report.
- **`follow-up-tracker`** — *opinionated.* Manages the `3-Waiting For` queue. Applies cadences by category (revenue/internal/vendors), drafts follow-up messages in exec voice, escalates exhausted threads.
- **`exec-voice-builder`** — *opinionated.* Extracts the exec's writing voice from their last 30 sent emails. Required before any drafting skill runs.
- **`inbox-reporter`** — *opinionated.* Produces SOD and EOD reports from upstream skill output. Last skill in every chain.
- **`inbox-onboarding`** — *neutral.* Two-phase setup wizard. Phase A: credentials, labels, filters, Gmail UI, initial cleanup. Phase B: VIP contacts, team routing, sweep rules.
- **`health-check`** — *neutral.* Audits the client profile for drift — stale voice guide, template placeholders, empty VIP list. Runs as a pre-flight inside every orchestrator session.

## The 9 Atlas labels

Every email gets **exactly one** of these — never stacked:

| Label | Use |
|---|---|
| `0-Leads` | Revenue opportunities |
| `1-Action Required` | Exec's personal decision or reply needed |
| `2-Read Only` | FYI — newsletters, industry news |
| `3-Waiting For` | Exec sent it, waiting for a reply |
| `4-Delegated` | EA or team is handling it |
| `5-Follow Up` | Action needed later, not today |
| `6-Receipts/Invoices` | Financial records |
| `7-Subscriptions` | Automated, newsletters, SaaS alerts |
| `8-Reference` | Calendar confirmations, recordings, bookings |

## Gmail implementation

The Gmail implementation ships in `implementations/gmail/`. It contains production Python scripts for every capability — auth, label management, message fetching, draft creation, filter setup, quota tracking, state persistence, and safety guards.

Key safety properties:
- **No send capability.** The send API is blocked at the library level. Only drafts.
- **Approval gates.** Destructive operations (mass archive, filter removal, label migration) require a `--dry-run` preview and an explicit approval ID before executing.
- **Quota tracking.** Monitors API call volume against the 30k/day Gmail budget; warns at 80%.

See [`implementations/gmail/README.md`](implementations/gmail/README.md) for setup.

## Customization notes

Common things clients change:

- **VIP contact list.** Populated during onboarding Phase B. Kept in `client-profile/vip-contacts.md`. Update whenever the exec's key relationships change.
- **Team delegation map.** Who handles what. Used by triage (4-Delegated) and follow-up-tracker (internal cadence). Kept in `client-profile/team-delegation-map.md`.
- **Label sweep rules.** Default sweep timing per label. Kept in `client-profile/label-sweep-rules.md`. Adjust for exec's archive preferences.
- **Follow-up cadences.** The timing and template logic lives in `skills/follow-up-tracker/references/follow-up-cadences.md`. Revenue, internal, and vendor cadences are independently adjustable.
- **Escalation triggers.** The keyword lists and domain patterns for Tier 1 and Tier 2 detection live in `skills/escalation-handler/references/escalation-rules.md`.
- **Exec voice guide.** Extracted by `exec-voice-builder`. Lives in `client-profile/exec-voice-guide.md`. Re-run quarterly or when drafts feel off.

## Troubleshooting

**Escalation-handler not detecting a known red flag.** Check `escalation-rules.md` — add the sender to `vip-contacts.md` or add the keyword to the relevant tier. The rules are fully editable.

**Drafts don't sound like the exec.** Re-run `exec-voice-builder`. Voice drift happens over ~90 days. If the guide is >30 days old, `health-check` will flag it.

**Triage is leaving items in the inbox.** Normal if the inbox is large — batching is by design. The safety cap prevents context blowup. Run again; it picks up where it left off.

**Follow-up drafts aren't threading correctly.** The Gmail implementation uses `create_reply_draft` which requires the original message ID. If the thread structure is non-standard, check that `check_followups.py` is returning the correct `in_reply_to` field.

**Onboarding fails mid-way.** Onboarding is resumable. Re-run `inbox-onboarding` — it detects which steps completed and picks up from the right phase.
