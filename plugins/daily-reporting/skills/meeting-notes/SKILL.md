---
name: meeting-notes
description: Retrieve recent action-relevant meeting note summaries for daily-reporting. Use when SOD or EOD needs decisions, follow-ups, blockers, dependencies, or unresolved actions from recent meetings.
when_to_use: Invoked by `daily-reporting` when SOD or EOD needs the `meetings` source family and the deployment's source_map points at a meeting-note backend (Granola, Fathom, Otter, Fireflies, etc.). Returns normalized `meeting_note_summaries` per the contract in this file. Do NOT use directly by an operator — invoke `daily-reporting` or `daily-reporting-setup` instead.
atlas_methodology: neutral
---

# Meeting Notes Connector

Use this connector when `daily-reporting` needs meeting-based decisions, follow-ups, blockers, or dependencies.

## Write Contract

| Output | Target | When |
|--------|--------|------|
| Normalized meeting note summaries | current `daily-reporting` run | whenever the `meetings` source family is enabled and selected |

**Naming:** return the result as `meeting_note_summaries`.
**Skip write when:** if the source is disabled, unavailable, or yields no action-relevant meeting context, return an empty result. Do not create durable state.

Only gather recent meeting context that matters for the report.

## Default windows

See `../../references/policies/source-windows.md`. Connector-specific caveat: at EOD, pull older notes only when an unresolved current-cycle item clearly depends on them.

## Produce

- decisions affecting the current cycle
- open follow-ups
- blockers and dependencies
- owner-specific actions

## Rules

- do not pass full transcripts or broad meeting history by default
- retrieval budget: see `../../references/policies/retrieval-budgets.md` ("Default budgets")
- source filtering: see `../../references/policies/source-filtering.md` (this connector's section)
