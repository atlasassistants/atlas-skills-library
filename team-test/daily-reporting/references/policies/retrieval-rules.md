# Retrieval Rules

## Purpose

The plugin should gather enough context to produce an accurate executive report without pulling in unnecessary noise.

## Rules

- Prefer connectors or delegated retrieval for heavy source access.
- Consume normalized summaries rather than raw dumps.
- Use only approved sources.
- Keep retrieval windows narrow.
- Filter for executive relevance.
- Do not fabricate missing information.

Naming rule:
- use the canonical source keys declared in `../schemas/deployment-config-schema.md` §Source keys
- connector names stay outside the package

## Source Priority

This is the **canonical priority ladder** for the plugin. When sources disagree — whether about which items are priorities, which carryovers still matter, or how to reconcile conflicting signals — resolve in this order. Other documents in the plugin (the main skill, the normalized-context schema) reference this ladder rather than restating it.

Prefer, in order:
1. clear current-run human corrections and confirmed priorities (`manual.confirmed_priorities`, runtime `confirmed_priorities`, and in-run reviewer corrections)
2. prior locked state for continuity-heavy fields (`prior_state.prior_locked_state`)
3. connected executive source systems — primarily task-derived current priorities (`tasks.priority_context`), plus calendar and email evidence where they directly bear on the field being resolved
4. recent action-relevant meeting-note summaries (`meetings.meeting_note_summaries`)
5. manual fallback when connected sources are absent or intentionally overridden (`manual.freeform_operator_notes`, `manual.manual_overrides`)

Applied to priority selection specifically, this means: current-run human-confirmed priorities win; then task-derived current priorities; then still-relevant prior carryovers and carryover candidates; then meeting, email, and calendar signals as evidence for urgency, sequencing, blockers, and dependencies — or, when stronger sources are absent, as narrow fallback priorities. Email, meeting, and calendar signals still always influence blockers, dependencies, risks, timing, and readiness; they should not normally outrank valid human-confirmed priorities or clear task-derived priorities on their own.

If a source returns nothing relevant, leave it empty rather than inventing data.

## Required vs. optional sources

"Required source" is the taxonomy the main skill's "If data is missing" rule references when it decides between `status: partial` and `status: blocked`. The taxonomy is declared here so a runtime outage can be resolved deterministically rather than by implementer guess.

Required, per mode:

| Source | SOD | EOD | Rationale |
|---|---|---|---|
| `tasks` OR `manual` | required | required | Executive priority context must have at least one live signal — either a live `tasks` connector or a human-provided `manual` fallback. Mirrors the setup-time "Minimum valid deployment" rule in `../schemas/deployment-config-schema.md`. |
| `prior_state` | required on non-first-run | required on non-first-run | Continuity ordering depends on the prior locked cycle; when `continuity_status` would be `first_run`, prior_state is waived. |
| `calendar` | optional | optional | Evidence for urgency, sequencing, prep. Degrades the run gracefully if absent. |
| `email` | optional | optional | Evidence for unresolved threads, pending decisions. Degrades the run gracefully if absent. |
| `meetings` | optional | optional | Evidence for action items and follow-ups. Degrades the run gracefully if absent. |

Rules applied at workflow step 5 of `../../skills/daily-reporting/SKILL.md`:

- If every required source for the current mode is available (returned a successful, non-error payload — including the case where it returned zero items), the run proceeds normally. Outages among optional sources downgrade `status` to `partial` per the "If data is missing" case (b).
- If any required source is unavailable (connector error, timeout, auth failure, invalid payload, or not configured) **and** no reasonable fallback exists — specifically, `tasks` unavailable with no `manual` fallback provided, or `prior_state` unavailable on a non-first-run with no recoverable record in the continuity fallback chain — the run must return `status: blocked`. Populate `validation_meta.missing_sources[]` with `{ source_family, reason: "required_but_absent" }` (or the specific failure reason) using the shape declared in `../schemas/output-schema.md` ("`missing_sources[]`").
- A `manual` fallback counts as satisfying the `tasks`-or-`manual` requirement only when it actually provides current-run executive priorities (via `runtime_input.manual_overrides.priorities` or `runtime_input.confirmed_priorities`). An empty `manual` payload does not satisfy the requirement.
- Optional-source outages never trigger `status: blocked` on their own; they produce `status: partial` with the corresponding `validation_meta.warnings` and `validation_meta.missing_sources[]` entries.

The distinction between `partial` (some context missing but a meaningful report is still possible) and `blocked` (required context absent, the report would be misleading) depends entirely on this taxonomy. Changes to which sources are required for a meaningful run must be made here, not at individual call sites.
