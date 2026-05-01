---
name: daily-reporting
description: Generate a start-of-day or end-of-day report for an executive. Use when a tool or operator needs a structured daily report, continuity handoff between SOD and EOD cycles, or a reviewed/locked report drafted from approved source families.
when_to_use: User says "SOD", "EOD", "start of day", "end of day", "daily report", "let's start the day", "wrap up the day", "close the day", "close out the day", "end of day report", "daily brief". Also runs on scheduled triggers if configured. Do NOT use for ad-hoc status reports or non-daily summaries — those are out of scope.
atlas_methodology: opinionated
---

# Daily Reporting

This is the main file for the `daily-reporting` package.

A tool or agent using this package should start here.

`daily-reporting` is a platform-agnostic executive reporting skill.

Modes:
- `sod` — start-of-day planning and lock-in
- `eod` — end-of-day closeout and carryforward planning

## Scope

This plugin is intentionally narrow.

It should answer:
- what matters to the executive today
- what is blocking the executive
- what the executive is waiting on
- what the executive completed
- what must carry forward
- what support-layer work materially affects executive execution

It should not drift into whole-team reporting or broad workspace audits.

## How to use this file

Read this file first.

Then pull in the supporting files only when needed:
- `../daily-reporting-setup/` for saved defaults and config
- `../../references/schemas/` for the exact data shapes
- `../../references/policies/` for the core rules
- `../../references/templates/` and `../../references/examples/` for drafting and testing

## Write Contract

| Output | Target | When |
|--------|--------|------|
| Draft report | configured runtime or review destination | after required context is gathered |
| Revised draft | configured runtime or review destination | after review changes |
| Final sent report | configured delivery destination | according to saved review policy |
| Structured state | configured continuity store | whenever the selected finalization policy says it should become continuity |

**Continuity rule:** see `../../references/policies/review-and-locking.md` ("Critical Rule") for the canonical gating rule that determines when a report becomes saved continuity.

## Allowed input sources

This plugin uses a fixed set of six source keys. The canonical list lives in `../../references/schemas/deployment-config-schema.md` §Source keys — use those exact keys wherever this package refers to a source family.

Connector names can differ. The deployment config maps these source keys to the connector being used.

## Runtime model

Normal runtime input should stay small.

Required:
- `mode` — `sod` or `eod`

The skill should load saved defaults first, figure out the report date from the saved timezone, then apply any one-run overrides.

## How a tool should run this

Use this order:

1. load a valid `deployment_config`
2. load a valid `runtime_input`
3. gather inputs from the enabled connectors
4. combine those inputs into one clean working input (`normalized_context`)
5. run this skill to draft and finalize the report

If a client already has a valid `normalized_context` prepared ahead of time, it may skip straight to step 5. That is only a shortcut, not the normal flow.

## Grounding rule

Every slot in the SOD and EOD templates is traceable to a named `merged_context` field via the "Slot-to-field reference" table in each template (`../../references/templates/sod-template.md`, `../../references/templates/eod-template.md`). Every list-typed field in `structured_state` is a verbatim copy of the matching `merged_context` field — see `../../references/schemas/output-schema.md` ("Polish rule" and "Field population mapping"). Only a small, explicitly named set of narrative slots in `human_readable_report` may be polished/synthesized; the rest must be verbatim. Per-field derivation rules live in `../../references/schemas/normalized-context-schema.md` ("Field derivation").

## Workflow

1. Load saved deployment config.
   see: `../../references/schemas/deployment-config-schema.md`
2. Check that the requested `mode` is present and enabled.
   see: `../../references/schemas/deployment-config-schema.md`, `../../references/schemas/runtime-input-schema.md`
   Two mode-check failure paths must be explicit (both return `status: blocked` without proceeding further into the workflow):
   - **(a) Mode absent.** If `runtime_input.mode` is missing or empty, return `status: blocked`. Add a `validation_meta.warnings` entry naming the missing field (for example, "`runtime_input.mode` is required and was absent"). Do not default to either `sod` or `eod` silently.
   - **(b) Mode not enabled.** If `runtime_input.mode` is present but is not in `deployment_config.enabled_modes`, return `status: blocked`. Add a `validation_meta.warnings` entry naming both the requested mode and the configured `enabled_modes` (for example, "requested mode `eod` is not in configured `enabled_modes: [sod]`"). Do not silently substitute the only enabled mode and do not run a partial cycle.
3. Figure out the local report date from the saved timezone unless `report_date` is overridden.
   see: `../../references/schemas/runtime-input-schema.md`
4. Load prior continuity state if available.
   see: `../../references/policies/continuity-model.md`
5. Gather current-cycle inputs from the allowed sources.
   see: `../../references/policies/source-windows.md`, `../../references/policies/retrieval-budgets.md`, `../../references/policies/source-filtering.md`
6. Clean each input into its expected normalized shape.
   see: `../../references/schemas/normalized-context-schema.md`
7. Combine them into one executive-centered working input.
   see: `../../references/schemas/normalized-context-schema.md`
8. Draft the report.
   see: `../../references/templates/sod-template.md`, `../../references/templates/eod-template.md`
9. Apply the saved review and finalization rules.
   see: `../../references/policies/review-and-locking.md`
10. Emit the final output.
    see: `../../references/schemas/output-schema.md`
11. Save continuity only when the policy allows it.
    see: `../../references/policies/continuity-model.md`

### Mode-specific obligations

Steps 7 and 8 above are the same procedure in both modes, but the `merged_context` fields they must populate differ by `mode`. An SOD that skips the EOD-only fields is still valid, and an EOD that skips the SOD-only fields is still valid — but neither is valid if it skips its own mode's obligations.

#### SOD-specific obligations

When `mode = sod`, step 7 must populate (in addition to the always-on fields `priorities`, `blockers?`, `dependencies?`, `carryovers?`, `risks?`, `schedule_signals?`, `inbox_signals?`, `meeting_signals?`, `support_work?`, `unresolved_items?`, `notes_for_next_cycle?`):

- `prep_items[]` — from `calendar.calendar_summary.prep_items` (SOD-primary per `../../references/schemas/normalized-context-schema.md` "Field derivation").
- `proposed_focus[]` — a short synthesized recommendation for the day's focus. This is one of the three narrative slots that may be polished (see `../../references/schemas/output-schema.md` "Polish rule"). Template slot `{{proposed_focus_statement}}` reads from this field.

SOD should leave `completed_items`, `planned_priorities`, `stalled_items`, and `next_cycle_focus` empty or absent — those are EOD-only.

#### EOD-specific obligations

When `mode = eod`, step 7 must additionally populate the fields that make the handoff payload load-bearing for tomorrow's SOD:

- `completed_items[]` — from `tasks.task_snapshot.completed_today`. Verbatim.
- `unresolved_items[]` — union of `prior_state.prior_locked_state.unresolved_items`, still-relevant `email.inbox_flags.pending_decisions`/`unresolved_threads`, and still-open `tasks.task_snapshot.stalled_items`. Verbatim.
- `stalled_items[]` — copy verbatim from `tasks.task_snapshot.stalled_items` so the draft can explicitly surface items that did not move.
- `planned_priorities[]` — copy verbatim from `source_family_results.prior_state.prior_locked_state.priorities` (this cycle's SOD lock). Used to compare "what was planned" against "what moved."
- `next_cycle_focus[]` — forward-looking priorities for tomorrow's SOD. Normally a verbatim copy of the final `priorities[]` at EOD lock; a reviewer may trim it to a tighter subset.
- `notes_for_next_cycle[]` — forward-looking operator/reviewer notes. Sources: `manual.freeform_operator_notes`, `manual.manual_overrides.notes_for_this_cycle`, and still-relevant `prior_state.prior_locked_state.notes_for_next_cycle`.

At step 11, when an EOD run is locked, the `structured_state` it writes becomes tomorrow's `prior_locked_state`. Which `structured_state` fields of that payload are load-bearing for the next SOD — and which carryovers retire rather than persist — is defined in `../../references/policies/continuity-model.md` ("EOD → next-SOD handoff payload").

### Priority selection and source conflicts

See `../../references/policies/retrieval-rules.md` ("Source Priority") for the canonical priority ladder that covers both source-disagreement resolution and priority selection.

### If data is missing

- If no prior locked state exists, mark continuity as `first_run` or `unavailable` per the canonical rule in `../../references/policies/continuity-model.md` ("Continuity status vocabulary"): use `first_run` when no locked state has ever existed for this deployment, and `unavailable` when prior state was expected but could not be found or loaded.
- If a loaded prior locked state fails schema validation (malformed, truncated, or otherwise unreadable), treat it as `continuity_status: unavailable`, add a `validation_meta.warnings` entry naming the validation failure, and do not seed any `merged_context` field from the corrupted record. See `../../references/policies/continuity-model.md` ("Corrupted prior state rule").
- A connector returning zero items is not the same outcome as a connector that failed. Distinguish three cases:
  - **(a) connector returned successfully with zero items** — the source is genuinely empty. Continue with an empty result. No warning is required.
  - **(b) connector returned an error, timeout, or authentication failure** — the source outcome is unknown, not empty. Populate `validation_meta.missing_sources[]` with `{ source_family, reason }` for the affected source, add a `validation_meta.warnings` entry, and downgrade `status` to `partial`. If the source is a **required** source per the taxonomy in `../../references/policies/retrieval-rules.md` ("Required vs. optional sources") and no reasonable fallback exists, downgrade `status` to `blocked` instead. "Required" is defined by that taxonomy (for example, `tasks`-or-`manual` is always required; `prior_state` is required on non-first-run). Optional-source outages never downgrade past `partial` on their own.
  - **(c) connector was intentionally disabled** in `deployment_config.defaults.source_map` — treat the source as absent. No `missing_sources` entry, no warning.
- If context is thin, produce the narrowest honest draft possible and flag the gaps in `validation_meta.warnings`.

### Do not make things up

Do not invent:
- carryovers
- completed work
- blockers
- dependencies
- priorities

when the available context does not support them.

## Finalization Modes

See `../../references/policies/review-and-locking.md` for the three finalization modes (`reviewed_locked`, `auto_locked`, `send_only`), the `send_only`-does-not-create-continuity rule ("Critical Rule"), the `auto_locked` validation gate ("Auto-lock validation gate"), and the `reviewed_locked` non-confirm exits ("Non-confirm exits from `reviewed_locked`"). The deployment must choose one; the chosen mode is saved as `deployment_config.defaults.review_policy.finalization_mode`.

## What belongs in this plugin

This package owns:
- the executive reporting logic
- the SOD/EOD modes
- the allowed source keys
- the expected connector outputs
- the setup, runtime-input, normalized-context, and output schemas
- the continuity, retrieval, and finalization rules
- the templates and examples

A client implementation owns:
- auth and secrets
- exact data-source bindings
- storage locations
- delivery destinations
- scheduling
- approval surfaces
- logging and run IDs
- provider-specific retrieval wrappers
- client naming and org conventions

Simple rule:
- if it changes from one client deployment to another, it probably belongs outside this package

For the declarative list of capabilities the runtime must provide to host this plugin, see `../../references/policies/runtime-capabilities.md`.

## References

Schemas:
- `../../references/schemas/deployment-config-schema.md`
- `../../references/schemas/runtime-input-schema.md`
- `../../references/schemas/normalized-context-schema.md`
- `../../references/schemas/output-schema.md`

Policies:
- `../../references/policies/review-and-locking.md`
- `../../references/policies/continuity-model.md`
- `../../references/policies/retrieval-rules.md`
- `../../references/policies/source-windows.md`
- `../../references/policies/retrieval-budgets.md`
- `../../references/policies/source-filtering.md`
- `../../references/policies/runtime-capabilities.md`

Other references:
- `../../references/conformance.md`

Templates and examples:
- `../../references/templates/sod-template.md`
- `../../references/templates/eod-template.md`
- `../../references/examples/README.md`

## Companion components

- `../daily-reporting-setup/`
- `../google-calendar/`
- `../outlook-calendar/`
- `../gmail/`
- `../executive-workflow/`
- `../meeting-notes/`
- `../prior-state/`
- `../manual/`
