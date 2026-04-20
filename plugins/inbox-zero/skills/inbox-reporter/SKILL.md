---
name: inbox-reporter
description: Produces SOD, midday, and EOD inbox management reports from upstream skill output. Assembles triage counts, escalation items, follow-up actions, label sweep results, and health findings into a structured report the exec reads in under two minutes. Always the last skill in any chain.
when_to_use: Called automatically by inbox-zero at the end of every session. Also invoked directly to regenerate a report: "generate inbox report", "show me the SOD report", "produce EOD report". Never invoke before upstream skills have run for the session.
atlas_methodology: opinionated
---

# inbox-reporter

Stitch upstream skill output into a report the exec reads in under two minutes.

## Purpose

A raw JSON dump from triage and follow-up tracking is not a report. This skill transforms upstream outputs into a structured, prioritized, scannable report — decisions first, handled items second, follow-ups third, carryover last. The exec reads it in one pass and knows exactly what requires their attention.

## Inputs

- **Escalation JSON** (from `escalation-handler`) — tier1, tier2, labeled counts
- **Triage JSON** (from `inbox-triage`) — per-label counts, drafts created, confidence flags
- **Follow-up JSON** (from `follow-up-tracker`) — due today, escalations, replies received
- **Sweep JSON** (from label sweep, EOD only) — per-label archived/kept counts
- **Health findings** (from `health-check`) — drift findings if any
- **Live label counts** — current count of items in each Atlas label (fetched live, not from cached upstream data)
- **Session mode** — `morning`, `midday`, or `eod`

## Required capabilities

- **Email read** — fetch live label counts (one search per label for current queue depth)

## Steps

1. **Load references.** `skills/inbox-reporter/references/report-templates.md` — SOD, midday, and EOD templates; section rules; edge cases; what to omit.
2. **Collect all upstream JSON** from the session.
3. **Fetch live label counts** for each Atlas label — the upstream JSON shows what was processed this session; live counts show what's currently in the queue.
4. **Assemble report section-by-section** per the template:
   - **SOD:** Needs Your Decision → Revenue → Following Up Today → Handled For You → Today's Email-Driven Actions → Delegation Hints → Confidence Flags → Health → Quota
   - **EOD:** Today's Numbers → Still in Your Queue → Carryover → Label Sweep → Health → Quota → Alerts
   - **Midday:** Single paragraph, no sections, no emoji headers
5. **Apply section rules from the template:**
   - Omit empty sections entirely (no empty headers)
   - One line per item
   - Specific names and subjects — no generics
   - Time estimates on every `1-Action Required` item
   - Tier 1 escalations always first in Needs Your Decision
   - Each item in exactly one section
6. **Return the report** as markdown plus a one-line summary for the orchestrator log.

## Output

SOD example (abbreviated):

```
Inbox Management Update:

⚡ **Needs Your Decision** (14 min)
1. [Legal] counsel@lawfirm.com re: trademark — call legal today [10 min]
2. [Client] cto@bigclient.com re: contract — draft ready [2 min]
3. [Board] chair@board.com re: Q2 review — draft ready [2 min]

⏰ **Following Up Today**
- Acme (Day 4): Q2 proposal — draft ready
- Sam (Day 3 internal): product spec — flagged, needs exec check-in

✅ **Handled For You**
- 13 subscriptions auto-filtered and archived
- 7 receipts labeled and archived
- 4 delegated to team

📊 **Quota** — 1,240 / 30,000 API calls (4%)
```

## Customization

- **Section order.** The SOD and EOD section order is defined in `report-templates.md`. Adjust to match exec preference.
- **Omit sections.** Any section can be permanently disabled per mode.
- **Midday format.** Default is a single paragraph. Expand to a short list if exec prefers more detail at midday.

## Why opinionated

Report structure is where information gets lost. Decisions buried below handled items get missed. Items appearing in two sections create confusion. The template encodes the priority order and the omit rules so that every report has the same structure — readable in one pass, predictable every time.
