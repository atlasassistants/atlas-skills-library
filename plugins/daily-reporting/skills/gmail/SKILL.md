---
name: gmail
description: Retrieve email-based attention flags and unresolved message context for daily-reporting. Use when SOD or EOD needs executive-relevant inbox signals, pending decisions, important follow-ups, or email-derived risks from Gmail.
when_to_use: Invoked by `daily-reporting` when SOD or EOD needs the `email` source family and the deployment's source_map points at Gmail. Returns normalized `inbox_flags` per the contract in this file. Do NOT use directly by an operator — invoke `daily-reporting` or `daily-reporting-setup` instead.
atlas_methodology: neutral
---

# Gmail Connector

Use this connector when `daily-reporting` needs email-based attention flags from Gmail.

## Write Contract

| Output | Target | When |
|--------|--------|------|
| Normalized inbox flags | current `daily-reporting` run | whenever the `email` source family is enabled and selected |

**Naming:** return the result as `inbox_flags`.
**Skip write when:** if the source is disabled, unavailable, or has no reporting-relevant unresolved messages, return an empty result. Do not create durable state.

Only gather inbox context that matters for the report.

## Default windows

See `../../references/policies/source-windows.md`.

## Produce

- `unresolved_threads` (unresolved important emails)
- `pending_decisions` (pending responses or decisions)
- `urgent_followups` (urgent follow-ups)
- `executive_risks` (external commitments or risks affecting the executive's cycle)

## Rules

- do not pull the entire inbox or pass long raw threads by default
- retrieval budget: see `../../references/policies/retrieval-budgets.md` ("Default budgets")
- source filtering: see `../../references/policies/source-filtering.md` (this connector's section)
