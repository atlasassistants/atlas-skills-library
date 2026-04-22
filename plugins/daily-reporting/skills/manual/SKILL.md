---
name: manual
description: Accept manually supplied reporting inputs when connected sources are unavailable, incomplete, or intentionally bypassed. Use when an operator needs to provide direct context to daily-reporting.
when_to_use: Invoked by `daily-reporting` when the `manual` source family is enabled in `source_map` and the operator supplies direct input (priorities, overrides, freeform notes). Also invoked during backfill or recovery runs when connected sources are unavailable. Returns `freeform_operator_notes`, `confirmed_priorities`, and `manual_overrides` per the contract in this file. Operators may supply input via any surface the runtime exposes.
atlas_methodology: neutral
---

# Manual Connector

Use this connector when a human needs to supply or override reporting context directly.

## Write Contract

| Output | Target | When |
|--------|--------|------|
| Normalized manual notes | current `daily-reporting` run | whenever operator-supplied manual input is present |
| Confirmed manual priorities | current `daily-reporting` run | whenever the operator explicitly supplies them |
| Manual overrides | current `daily-reporting` run | whenever the operator intentionally overrides connected-source behavior |

**Naming:** contribute only `freeform_operator_notes`, `confirmed_priorities`, and `manual_overrides`.
**Skip write when:** if no manual input is supplied, return an empty result and do not create durable state.

This is the manual fallback and override connector.

## Default windows

Not applicable. Manual input is operator-supplied per run; retrieval-window policy in `../../references/policies/source-windows.md` does not bound this connector.

## Produce

Use for:
- operator notes
- manual priorities
- manual carryovers
- manual dependencies or risks
- backfill or recovery runs

## Rules

- do not mark manual input as verified unless the human explicitly provides it as authoritative
- keep manual input clearly separate from connected source truth
- return short structured summaries, not raw note dumps
- retrieval budget: unbounded by default; see `../../references/policies/retrieval-budgets.md`
- source filtering: none by default; operator input is authoritative. See `../../references/policies/source-filtering.md`.
