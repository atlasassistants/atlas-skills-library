# Templates: replacement mini-spec + audit summary

## Replacement mini-spec template

One file per replace-candidate at `<finance_docs_root>/audits/replacement-ideas/<tool-slug>.md`. `<tool-slug>` is the kebab-case vendor or tool name.

```markdown
---
title: Replace <Tool Name> with <Short Replacement Description>
type: knowledge
subtype: comparison
tags:
  - finances
  - ai-replacement
  - <tool-category>
created: YYYY-MM-DD
updated: YYYY-MM-DD
sources:
  - [[subscriptions]]
  - [[audits/YYYY-MM-DD-subscription-audit]]
related:
  - [[subscriptions]]
---

# Replace <Tool Name> with <replacement description>

**Current cost:** $XX/mo ($XXX/year)
**Category:** <ai-tools | infra | etc.>
**Usage notes (from audit):** <1-2 sentence paraphrase of Colin's answer>

## Problem

What does <Tool Name> actually do for Atlas? What workflow would we need to preserve if we cancelled it?

## Proposed replacement

Design the replacement concretely. Pick one of:

- **Claude skill** — a new skill in your skills library that does the core job interactively
- **Composio workflow** — a scripted automation chaining Composio toolkits (Gmail, Slack, etc.) triggered manually or on a schedule
- **Custom micro-app** — a small web app or CLI you build and self-host
- **Hybrid** — combination of the above

Describe the flow: trigger → steps → output. Be specific.

## Tools / APIs needed

- Composio toolkits: <list>
- External APIs: <list>
- Infra: <e.g., Vercel function, local cron, knowledge base vault>

## Rough complexity

| Dimension | Estimate |
|-----------|----------|
| Build effort | X-Y hours OR X days |
| Complexity (1-5) | N |
| Maintenance burden | low / medium / high |

## Estimated savings

| Line item | Amount |
|-----------|--------|
| Current annual cost | $XXX |
| Replacement infra cost (if any) | -$XX |
| Claude API cost estimate | -$XX |
| **Net annual savings** | **$XXX** |

## Risks / tradeoffs

- Where the SaaS tool does something the replacement can't
- Hidden costs (maintenance, debugging, onboarding)
- Switching cost (data migration, muscle memory)

## Recommendation

One of: **build now**, **build later (low priority)**, **do not replace — keep paying**. Include the reason.

## Next steps if greenlit

1. ...
2. ...
```

---

## Audit summary template

One file per audit run at `areas/finances/audits/YYYY-MM-DD-subscription-audit.md`.

```markdown
---
title: Subscription Audit — YYYY-MM-DD
type: report
subtype: subscription-audit
tags:
  - finances
  - subscriptions
  - audit
created: YYYY-MM-DD
updated: YYYY-MM-DD
---

# Subscription Audit — Month DD, YYYY

**Scope:** <all active subs | category X only | subs ≥ $N/mo>
**Subs reviewed:** N
**Combined monthly cost reviewed:** $X,XXX ($YY,YYY annual)

## Results at a glance

| Classification | Count | Monthly | Annual |
|----------------|-------|---------|--------|
| Keep | N | $X,XXX | $XX,XXX |
| Cancel candidate | N | $XXX | $X,XXX |
| Replace candidate | N | $XXX | $X,XXX |
| **Total potential annual savings** | — | — | **$X,XXX** |

## Keep

Subs the user confirmed as core. No action.

- **Tool A** — $XX/mo — reason
- **Tool B** — $XX/mo — reason

## Cancel candidates

Subs to cancel outright (not used or not needed).

- **Tool C** — $XX/mo — last used date / reason
- **Tool D** — $XX/mo — reason

**Next step:** Log into vendor portal(s) and cancel. Update `subscriptions.md` with `status: cancelled` and `cancelled_date`.

## Replace candidates

Subs where a custom AI build could plausibly replace the paid tool. Each has a mini-spec:

- **Tool E** — $XX/mo — [[replacement-ideas/tool-e]] — complexity X, savings $XXX/yr
- **Tool F** — $XX/mo — [[replacement-ideas/tool-f]] — complexity Y, savings $XXX/yr

## Recommended next builds (top 3)

1. **<Tool>** — <one-sentence why>
2. **<Tool>** — <one-sentence why>
3. **<Tool>** — <one-sentence why>

## Follow-ups

- Confirm `needs-review` subs (flagged but not yet classified)
- Schedule a build session for the top recommendation
- Re-run audit in N months
```
