# Schemas: subscriptions.md and monthly report

## `subscriptions.md` schema

This file is the living registry of every recurring paid subscription tracked by the plugin. It lives at `<finance_docs_root>/subscriptions.md` — the path resolves from the client config (`client-profile/templates/expense-config.template.md`).

### Frontmatter

```yaml
---
title: <Org Name> Subscriptions
type: area
tags:
  - finances
  - subscriptions
created: YYYY-MM-DD
updated: YYYY-MM-DD
---
```

`<Org Name>` is the user's organization name. The skill should ask the user for it on first registry creation and reuse it from then on.

### Body structure

The body is a set of subscriptions, each rendered as a level-3 heading with a YAML frontmatter-like block underneath. This keeps it greppable and editable by both agents and humans.

```markdown
# <Org Name> Subscriptions

Living registry of recurring tool and service subscriptions. Updated monthly by the `monthly-expense-report` skill.

**Totals**
- Active monthly cost: $X,XXX.XX
- Active annual cost: $XX,XXX.XX
- Total subscriptions: N (active) / M (under review)

## Active

### Claude Pro
- vendor: Anthropic
- category: ai-tools
- cost_monthly: 20.00
- cost_annual: 240.00
- billing_cycle: monthly
- status: active
- first_charged: 2025-08-15
- last_charged: 2026-04-15
- last_amount: 20.00
- owner: colin
- notes: Primary Claude subscription.

### AWS
- vendor: Amazon Web Services
- category: infra
- cost_monthly: 247.50
- billing_cycle: usage-based
- status: active
- first_charged: 2025-04-01
- last_charged: 2026-04-28
- last_amount: 247.50
- last_charge_count: 4
- notes: Multi-charge vendor; cost varies by usage. last_amount is the month total across all 4 charges.

### Figma
- vendor: Figma Inc
- category: design
- cost_monthly: 15.00
- billing_cycle: monthly
- status: active
- ...

## Under review

### ExampleTool
- vendor: ExampleCo
- cost_monthly: 49.00
- status: needs-review
- notes: Detected in April 2026 expense pull, not previously registered.

## Archived

### OldTool
- vendor: SomeCo
- cost_monthly: 29.00
- status: cancelled
- cancelled_date: 2026-02-10
- notes: Replaced by internal workflow.
```

### Field reference

| Field | Required | Values / format |
|-------|----------|-----------------|
| `vendor` | yes | Merchant-name as it appears on bookkeeping statements |
| `category` | yes | One of: `ai-tools`, `infra`, `dev-tools`, `productivity`, `design`, `analytics`, `marketing`, `ops`, `other` |
| `cost_monthly` | yes | Number (USD). For annual subs, monthly equivalent (annual/12) |
| `cost_annual` | optional | Number (USD). Only for annual billing |
| `billing_cycle` | yes | `monthly`, `annual`, `quarterly`, `usage-based` |
| `status` | yes | `active`, `needs-review`, `cancel-candidate`, `replace-candidate`, `cancelled` |
| `first_charged` | optional | YYYY-MM-DD |
| `last_charged` | yes (if active) | YYYY-MM-DD — the latest date in the most recent month with activity |
| `last_amount` | yes (if active) | Number (USD) — **total** charged in the most recent month with activity (sum across all charges if there were multiple) |
| `last_charge_count` | optional | Integer ≥ 2 — emit only when the vendor charged more than once last month. Omit for single-charge vendors |
| `owner` | optional | Team member who owns it |
| `notes` | optional | Free text |

### Sort order

Inside each section, sort subscriptions by `cost_monthly` descending.

### Parse recipe

Both `monthly-expense-report` and `subscription-audit` read this file. Use the same parse routine in each:

1. Read the file into memory.
2. Strip the YAML frontmatter (between the first two `---` lines).
3. Find the `## Active`, `## Under review`, and `## Archived` section headers. Everything between two H2s belongs to the preceding section.
4. Within a section, each subscription is a `### <Tool Name>` heading followed by bulleted lines of the form `- <field>: <value>`.
5. Parse each subscription into a dict: `{tool_name, vendor, category, cost_monthly (float), billing_cycle, status, first_charged, last_charged, last_amount (float), owner, notes, section}` — the `section` field records which section it was under.
6. Ignore blank lines and free-text paragraphs between subscriptions.

When writing back, preserve the order of fields shown in the Field Reference table above. Keep human-added free-text between subscriptions intact if possible (re-emit it under the same subscription it preceded).

If a subscription heading exists but has no bulleted fields, treat it as parse-failed and surface it to the user — do not silently drop it.

---

## Normalized transaction shape

The skill consumes a list of transactions for the target month, regardless of bookkeeping system. Each `implementations/<system>/procedure.md` is responsible for producing this shape:

```json
{
  "date":   "YYYY-MM-DD",
  "vendor": "Anthropic",
  "amount": 20.00,
  "currency": "USD",
  "memo":   "Claude Pro — monthly",
  "raw":    { ... }      // optional — system-native record for the appendix
}
```

After the implementation returns this list, the universal reconcile + write-report logic in the skill takes over. The list must already be filtered to the configured bookkeeping bucket — bucket filtering is a per-system concern.

---

## Monthly report schema

The monthly report lives at `<finance_docs_root>/monthly-reports/YYYY-MM-report.md`.

### Frontmatter

```yaml
---
title: YYYY-MM Expense Report
type: report
subtype: monthly-expense-report
tags:
  - finances
  - expenses
  - monthly
month: YYYY-MM
created: YYYY-MM-DD
updated: YYYY-MM-DD
---
```

### Body structure

```markdown
# Expense Report — <Month YYYY>

Source: <bookkeeping.system> (via Composio) — pulled YYYY-MM-DD
Related: [[subscriptions]]

## Summary

| Metric | This month | Last month | Δ |
|--------|------------|------------|---|
| Total expenses | $X,XXX | $X,XXX | ±$XXX (±X%) |
| Transaction count | N | N | ±N |

**Top 5 vendors:**
1. Vendor A — $XXX
2. Vendor B — $XXX
...

## Subscriptions this month

Every vendor matched to an entry in `subscriptions.md`. The "Amount" column shows the **total** charges this month for vendors with multiple charges; the price-change check still uses the latest single charge.

| Tool | Vendor | Amount | Charges | Status | Change vs last month |
|------|--------|--------|---------|--------|----------------------|
| Claude Pro | Anthropic | $20.00 | 1 | active | — |
| Figma | Figma Inc | $15.00 | 1 | active | — |
| ... | | | | | |

### New subscriptions detected

Charges from vendors not currently in `subscriptions.md`. Added to `## Under review` with `status: needs-review`.

- **VendorX** — $49.00 on 2026-04-12 — confirm + categorize at next audit

### Subscriptions that did not charge this month

Active registered subs with no matching transaction — may indicate cancellation, annual billing, or a sync gap. Excludes subs in `## Under review`, `## Archived`, or with `status: cancelled`.

- **Tool Y** — last charged 2026-03-15, expected ~$20/mo. Verify status.

### Price changes this month

Subs whose latest charge changed >10% vs prior `last_amount`.

- **Tool Z** — was $19.00, now $24.00 (+26%). [[replacement-ideas/tool-z]]

## Appendix — full transactions

Every transaction pulled for this month, sorted by date descending.

| Date | Vendor | Amount | Memo |
|------|--------|--------|------|
| 2026-04-28 | Anthropic | $20.00 | Claude Pro — monthly |
| 2026-04-15 | Figma Inc | $15.00 | Figma Professional |
| ... | | | |
```

The appendix is intentionally a flat list rather than grouped by category — new (`needs-review`) vendors don't have a category yet, and grouping mid-month would scatter them under "uncategorized." Date-sorted is more useful for tracing a specific charge.

### Wikilink conventions

- Always wikilink `[[subscriptions]]` in the body so the report backlinks to the registry.
- When a replacement-idea page exists for a tool, wikilink to `[[replacement-ideas/<tool-slug>]]` in the subscriptions table row.
