---
name: executive-workflow
description: Retrieve executive-centered work context for daily-reporting. Use when SOD or EOD needs the executive's active priorities, blockers, dependencies, carryovers, and delegated support work that materially affects the executive's day.
when_to_use: Invoked by `daily-reporting` when SOD or EOD needs the `tasks` source family and the deployment's source_map points at an executive-workflow backend (Airtable, Linear, Notion, HubSpot, etc.). Returns normalized `priority_context` and `task_snapshot` per the contract in this file. Do NOT use directly by an operator — invoke `daily-reporting` or `daily-reporting-setup` instead.
atlas_methodology: neutral
---

# Executive Workflow Connector

Use this connector when `daily-reporting` needs executive-scoped task and priority context.

## Write Contract

| Output | Target | When |
|--------|--------|------|
| Normalized executive priority context | current `daily-reporting` run | whenever the `tasks` source family is enabled and selected |
| Normalized task snapshot | current `daily-reporting` run | whenever the `tasks` source family is enabled and selected |

**Naming:** contribute only `priority_context` and `task_snapshot`.

**Populates these fields** (per `../../references/schemas/normalized-context-schema.md` §`tasks`):

| Container | Sub-fields |
|-----------|------------|
| `priority_context` | `current_priorities[]`, `blockers[]?`, `dependencies[]?`, `carryover_candidates[]?`, `exec_relevant_support_work[]?` |
| `task_snapshot` | `active_items[]?`, `completed_today[]?`, `stalled_items[]?` |

**Skip write when:** if no executive-relevant task context is available, return an empty result. Do not create durable state.

This connector is intentionally narrow.

## Default windows

See `../../references/policies/source-windows.md` (`tasks` row).

## Produce

Include only items that are:
- owned by the executive
- explicitly marked as executive priorities
- blockers of executive priorities
- delegated support work that materially affects executive execution
- carryovers from the executive’s prior locked report

Do not include by default:
- full team backlog
- unrelated team tasks
- broad PM audits
- general workspace hygiene review

## Rules

- contribute to `priority_context` and `task_snapshot`
- never widen into a whole-team scan by default
- keep summaries short and executive-centered
- retrieval budget: see `../../references/policies/retrieval-budgets.md` ("Default budgets")
- source filtering: see `../../references/policies/source-filtering.md` (this connector's section)
