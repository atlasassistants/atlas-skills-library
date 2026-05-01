---
name: google-calendar
description: Retrieve current calendar context for daily-reporting. Use when SOD or EOD needs schedule shape, meeting load, prep needs, collisions, or next-day preview from Google Calendar.
when_to_use: Invoked by `daily-reporting` when SOD or EOD needs the `calendar` source family and the deployment's source_map points at Google Calendar. Returns normalized `calendar_summary` per the contract in this file. Do NOT use directly by an operator — invoke `daily-reporting` or `daily-reporting-setup` instead.
atlas_methodology: neutral
---

# Google Calendar Connector

Use this connector when `daily-reporting` needs schedule context from Google Calendar.

See also `../outlook-calendar/SKILL.md` — the shared calendar-connector contract (frontmatter, H1, Write Contract, Default windows, Produce, Rules) is near-identical across both provider connectors; only the provider name and the Write Contract `When` column (Outlook adds "and mapped to Outlook") differ. Apply shared-behavior edits to both files.

## Write Contract

| Output | Target | When |
|--------|--------|------|
| Normalized calendar summary | current `daily-reporting` run | whenever the `calendar` source family is enabled and selected |

**Naming:** return the result as `calendar_summary`.
**Skip write when:** if the source is disabled, unavailable, or has no reporting-relevant events, return an empty result. Do not create durable state.

Only gather schedule context that matters for the report.

## Default windows

See `../../references/policies/source-windows.md`.

## Produce

- `key_events` (key meetings)
- `prep_items` (prep-relevant meetings)
- `collisions`
- `focus_windows` (open focus windows when inferable)
- `tomorrow_preview` (next-day preview events; EOD-relevant)

## Rules

- do not pass raw calendar dumps by default
- retrieval budget: see `../../references/policies/retrieval-budgets.md` ("Default budgets")
- source filtering: see `../../references/policies/source-filtering.md` (this connector's section)
