# Atlas inbox methodology

> Loaded by inbox-zero and inbox-triage before every session.

## The principle

An inbox is a decision queue, not a communications tool. Every message in an unmanaged inbox is an implicit demand on the exec's attention. The Atlas method converts the inbox from a pile to a queue: every message gets exactly one label, the queue is drained in bounded batches, and the exec only touches the inbox to review and act — never to sort.

**The exec's job:** review `1-Action Required` items, hit send on drafts, and make decisions on `5-Follow Up` items.
**The agent's job:** everything else.

## The 9 Atlas labels

Every email gets exactly one label. Never stacked. Never omitted.

| Label | Meaning | Who acts |
|---|---|---|
| `0-Leads` | Revenue opportunity — needs qualifying or routing | Agent surfaces; exec or sales decides |
| `1-Action Required` | Exec's personal decision or reply needed | Exec |
| `2-Read Only` | FYI — no action needed | Auto-archived after 48h |
| `3-Waiting For` | Exec sent something, waiting for a reply | Follow-up-tracker manages cadence |
| `4-Delegated` | EA or team member is handling it | Team member; agent monitors |
| `5-Follow Up` | Action needed — not today | Exec decides when |
| `6-Receipts/Invoices` | Financial records | Auto-archived |
| `7-Subscriptions` | Automated — newsletters, SaaS alerts, marketing | Auto-filtered at arrival |
| `8-Reference` | Calendar confirmations, recordings, booking refs | Auto-filtered at arrival |

**Rules:**
- One label per message. If it could be two things, pick the more urgent.
- Never create additional labels. The 9 are complete.
- Escalation detection runs before labeling — escalated items get `1-Action Required` directly.

## Session modes

Every session runs in one of three modes based on time of day (or explicit override):

| Mode | Time | What runs | Output |
|---|---|---|---|
| **Morning** | Before ~11am | Escalation + full triage + follow-ups | SOD report |
| **Midday** | ~11am–4pm | Escalation scan only | One-liner |
| **EOD** | After ~4pm | Escalation + full triage + sweep + follow-ups | EOD report |

## Chain order (non-negotiable)

1. Health pre-flight
2. Label reconciliation
3. Escalation-handler ← always before triage
4. Inbox-triage (morning/EOD only)
5. Follow-up-tracker (morning/EOD only)
6. Label sweep (EOD only, after triage)
7. Inbox-reporter ← always last

Any skill that runs out of this order produces unreliable output.

## Batching contract

Never fetch the entire inbox at once. Always fetch in bounded batches (default 100 messages). Apply decisions for each batch before fetching the next. If the inbox doesn't reach zero before the safety cap, report partial drain and continue next session.

This constraint exists to prevent context blowup, not because the inbox is too large to process — it's a disciplined pattern that keeps every session predictable regardless of inbox size.

## The client profile

The client profile is the persistent configuration that personalizes all skills for a specific exec. Lives in `client-profile/`:

| File | What it stores | Used by |
|---|---|---|
| `exec-voice-guide.md` | Writing voice patterns extracted from sent mail | inbox-triage, follow-up-tracker |
| `vip-contacts.md` | VIP sender list — always escalated | escalation-handler |
| `team-delegation-map.md` | Who handles what — internal routing | inbox-triage, follow-up-tracker |
| `label-sweep-rules.md` | Per-label archive timing defaults | inbox-triage (EOD sweep) |
| `sweep-schedule.json` | Processing schedule (if scheduled operation) | orchestrator |

## What good looks like

- Inbox reaches zero (or near-zero) every morning and EOD session
- Every `1-Action Required` item has a time estimate
- Drafts sound like the exec, not like AI
- Tier 1 escalations surface immediately, never buried in a batch
- Follow-ups go out before the exec has to ask "did anyone follow up on that?"
- The report is readable in under two minutes

## What bad looks like (avoid)

- Triage without escalation-handler running first
- Stacking multiple labels on one message
- Creating new labels outside the 9
- Drafting without a voice guide
- Fetching the entire inbox in one call
- Reporter running before all upstream skills complete
- Fabricating label counts or triage statistics
