---
title: Replace Zapier with Composio + Claude skill
type: knowledge
subtype: comparison
tags:
  - finances
  - ai-replacement
  - ops
created: 2026-04-22
updated: 2026-04-22
sources:
  - [[subscriptions]]
  - [[audits/2026-04-22-subscription-audit]]
related:
  - [[subscriptions]]
---

# Replace Zapier with Composio + Claude skill

**Current cost:** $49/mo ($588/year)
**Category:** ops
**Colin's usage notes (from audit):** Uses Zapier mainly for three things — (1) new Gmail labels → Slack notifications, (2) Typeform submissions → Notion rows, (3) calendar events → Slack reminders. Rated 3/5: useful but not irreplaceable.

## Problem

Zapier routes events between Gmail, Slack, Typeform, Notion, and Google Calendar. Value comes from its pre-built connectors and polling infrastructure, not from any unique business logic. If we cancelled, we'd lose roughly 3 live automations.

## Proposed replacement

**Composio workflow + scheduled Claude skills**, triggered via cron or Composio trigger events:

1. **Gmail → Slack notifier** — Composio `GMAIL_LIST_THREADS` + `SLACK_SEND_MESSAGE` on a 5-minute cron. Local CLI script, ~40 lines.
2. **Typeform → Notion** — Replace Typeform with a Google Form (free); new rows land in Google Sheets; Composio `GOOGLESHEETS_GET_ROWS` + `NOTION_CREATE_PAGE` on poll. OR keep Typeform and call its webhook from a Vercel serverless function that then calls Composio.
3. **Calendar → Slack reminders** — Composio `GOOGLECALENDAR_FIND_EVENTS` scheduled twice daily, post summary to Slack. Could be folded into the existing chief-of-staff agent.

All three live in a new `atlas-automations` skill or plugin, triggered via `composio run` for scheduled ones.

## Tools / APIs needed

- Composio toolkits: gmail, slack, googlecalendar, googlesheets, notion (would need to add notion)
- External APIs: none new
- Infra: cron (local launchd on the Mac mini) OR Vercel cron; colin-brain to log run outcomes

## Rough complexity

| Dimension | Estimate |
|-----------|----------|
| Build effort | 4-6 hours |
| Complexity (1-5) | 2 |
| Maintenance burden | low — 3 scripts, infrequent changes |

## Estimated savings

| Line item | Amount |
|-----------|--------|
| Current Zapier annual cost | $588 |
| Composio incremental cost (already paying) | $0 |
| Cron / Vercel infra cost | -$0 (covered by existing plans) |
| **Net annual savings** | **$588** |

## Risks / tradeoffs

- **Debuggability** — Zapier has nice run history UIs; our scripts need to log to colin-brain or Slack to replace that
- **Onboarding cost** — If another team member wanted to add a Zap, the path is harder than clicking buttons in Zapier
- **Reliability** — Zapier retries failures; need to add basic retry + alert logic to the cron scripts
- **Trigger latency** — 5-min poll vs Zapier's near-realtime (acceptable for these 3 flows)

## Recommendation

**Build now.** Low complexity, clear savings, and the capability unlocks more automations Atlas would build anyway. The scripts become a library we'll reuse.

## Next steps if greenlit

1. Connect `notion` via Composio if not already connected (`composio link notion`)
2. Write the three scripts in `atlas-automations/` skill
3. Run in parallel with Zapier for 1 week, verify outputs match
4. Cancel Zapier, update `subscriptions.md` with `status: cancelled`
