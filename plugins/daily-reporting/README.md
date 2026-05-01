# daily-reporting

> Executive daily reporting — start-of-day planning and end-of-day closeout with continuity handoff, review/locking, and connector-agnostic source handling.
> v0.1.0

## What it does

Runs a structured daily reporting cycle for an executive, end to end, for either start-of-day (SOD) or end-of-day (EOD) mode:

- **Gathers executive-relevant context** from up to six source families — calendar, email, tasks, meetings, prior locked state, and manually supplied input. Each source has a bounded retrieval window and signal-first filtering policy.
- **Combines everything into one working input** (`normalized_context`) shaped by a strict per-field derivation contract. Every output slot traces back to a named input field — no hallucinated priorities, carryovers, blockers, or completed work.
- **Drafts the report** from opinionated SOD or EOD templates. The draft carries verbatim data from `merged_context`; only a small set of narrative slots is synthesized.
- **Handles review and finalization** via one of three configurable modes (`reviewed_locked`, `auto_locked`, `send_only`), with a material-edit tie-breaker and explicit non-confirm exits.
- **Writes durable continuity** — the locked `structured_state` from today's EOD becomes tomorrow's SOD anchor, carrying forward only the fields that are load-bearing for the next cycle.

The result: a reviewable daily report and a structured continuity record, produced to an exact contract, runnable on any runtime that satisfies the declared capability set.

## Who it's for

Executives and their EAs / AI tools who need a repeatable daily cadence: a SOD that names today's priorities and a paired EOD that closes them, with explicit continuity between the two cycles. Atlas built this for the way our human EAs run daily reporting — structured slots, no invented content, locked handoffs that survive across days. If "what matters today, what's blocking, what carried forward" is the question the exec wants answered every morning and evening, this plugin delivers it.

## Required capabilities

The plugin's skills depend on these eight runtime capabilities. Each is named abstractly — wire it up to whatever tool the host agent has access to. Full per-capability proof items are in [`references/conformance.md`](references/conformance.md).

- **Persistence** — write and read `structured_state` records keyed by `(deployment_id, mode, report_date)`.
- **Scheduling** — trigger runs at schedulable times (daily minimum); support on-demand invocation and timezone-aware `report_date` computation.
- **Connector invocation** — call each enabled connector with the appropriate retrieval window, apply retrieval budgets, apply source filtering.
- **Review surface** — present drafted reports to a named reviewer; accept confirm / decline / edit with material-edit classification.
- **Delivery** — send final reports to configured destinations; handle retries; record delivery metadata.
- **Warning surface** — surface `validation_meta.warnings` to operators.
- **Run-history tracking** — track successful `reviewed_locked` run counts and corrupted-prior-state incidents (7-day rolling window) for guardrail enforcement.
- **Safe-posture surfacing** — honor customer configuration but surface advisories when a config falls into a safe-posture case.

Persistence, Connector invocation, and Delivery are hard-required. The other five are graceful-degradation — see [`references/policies/runtime-capabilities.md`](references/policies/runtime-capabilities.md) for the full tier breakdown.

## Suggested tool wiring

| Capability | Common options |
|---|---|
| Calendar | Google Calendar MCP, Outlook MCP, Composio Calendar |
| Email | Gmail MCP, Outlook MCP, Composio Gmail |
| Tasks / Executive workflow | Airtable, Notion, Linear, HubSpot, Things, a markdown todo file |
| Meeting notes | Granola, Fathom, Otter, Fireflies, Google Drive meeting docs |
| Persistence / Continuity store | Filesystem MCP, Postgres, any durable key-value store |
| Review surface | Email inbox, Slack DM, web form, any chat surface |
| Delivery | Slack, email, filesystem, webhook |

These are examples, not requirements. For operators without connectors wired at all, see the [`connect-sources`](skills/connect-sources/) skill for a guided Composio-first onboarding path.

## Installation

```
/plugin marketplace add colin-atlas/atlas-skills-library
/plugin install daily-reporting@atlas
```

After installing, complete the first-run setup below before running the main reporting skill.

## First-run setup

The setup is two steps, each guided by its own skill:

**Step 1 — Make sure connections exist.** Run [`connect-sources`](skills/connect-sources/). This skill's precondition handling routes operators who have no connectors wired to a guided Composio-first onboarding path. Skip if your runtime already has native connectors for the source families you plan to enable.

**Step 2 — Configure the deployment.** Run [`daily-reporting-setup`](skills/daily-reporting-setup/). This wizard saves the defaults the reporting skill reuses each run: default timezone, default participants, continuity store, delivery policy, review policy, retrieval policy, retrieval windows, source map, and validation status. See the setup skill's workflow for the canonical 11-step sequence, including a minimum-viable test cycle.

Once setup is complete and the test cycle passes, [`daily-reporting`](skills/daily-reporting/) is ready to run in either `sod` or `eod` mode.

## Skills included

- **`daily-reporting`** — *opinionated.* Main reporting skill. Loads saved config, loads prior state, gathers from enabled connectors, combines into `normalized_context`, drafts from the SOD or EOD template, applies the saved review/finalization policy, emits the final output, and writes continuity when policy permits.
- **`daily-reporting-setup`** — *neutral.* Setup wizard. Saves the deployment's reusable defaults and validates the config. Includes a lightweight test cycle as step 11 to confirm the wiring is runnable.
- **`connect-sources`** — *neutral.* Connection onboarding router. For operators with no connectors wired, walks them through a Composio-first path (signup, MCP install, per-app authorization, verification) before they return to setup. Also accepts native runtime connectors, direct OAuth, or other aggregators.
- **`gmail`** — *neutral.* Connector contract for the `email` source family backed by Gmail. Returns normalized `inbox_flags`.
- **`google-calendar`** — *neutral.* Connector contract for the `calendar` source family backed by Google Calendar. Returns normalized `calendar_summary`.
- **`outlook-calendar`** — *neutral.* Connector contract for the `calendar` source family backed by Outlook. Returns normalized `calendar_summary`.
- **`executive-workflow`** — *neutral.* Connector contract for the `tasks` source family backed by the executive's workflow system (Airtable, Linear, Notion, HubSpot, etc.). Returns `priority_context` and `task_snapshot`.
- **`meeting-notes`** — *neutral.* Connector contract for the `meetings` source family backed by any meeting-notes provider. Returns `meeting_note_summaries`.
- **`prior-state`** — *neutral.* Internal connector for the continuity source. Loads the most recent locked state per the continuity-model policy. Returns `prior_locked_state` + `continuity_status`.
- **`manual`** — *neutral.* Internal connector for operator-supplied input. Returns `freeform_operator_notes`, `confirmed_priorities`, `manual_overrides`.

## Customization notes

This plugin is opinionated about the reporting contract itself (what SOD/EOD means, what continuity means, how review and locking work), but every policy is editable. Common things clients change:

- **Source map.** Which source key maps to which connector. Edit `source_map` in the saved `deployment_config`. Minimum is `tasks` or `manual`.
- **Retrieval windows.** How far back each source scans. Defaults in [`references/policies/source-windows.md`](references/policies/source-windows.md); override per deployment in `runtime_input.overrides.windows`.
- **Retrieval budgets.** How many items a source can contribute. Defaults in [`references/policies/retrieval-budgets.md`](references/policies/retrieval-budgets.md).
- **Source filtering.** What noise to exclude and what signal to prioritize per source. Defaults in [`references/policies/source-filtering.md`](references/policies/source-filtering.md).
- **Review policy.** Choose `reviewed_locked` (human confirms), `auto_locked` (runs green-lit by run-history), or `send_only` (no continuity written). See [`references/policies/review-and-locking.md`](references/policies/review-and-locking.md).
- **Templates.** The SOD and EOD template shapes are in [`references/templates/`](references/templates/). Edit to match your report style, but respect the slot-to-field mapping.

The schemas in [`references/schemas/`](references/schemas/) define the contract shape — edit those only if you're extending the plugin.

## Atlas methodology

This plugin encodes Atlas's daily reporting discipline as a strict contract:

- **Slot-to-field grounding.** Every template slot maps to a named `merged_context` field per each template's slot-to-field reference table. The skill never invents content; only a small, explicitly named set of narrative slots may be polished/synthesized, and the rest are verbatim copies.
- **SOD → EOD continuity.** An EOD lock becomes the next SOD's `prior_locked_state`. Which fields are load-bearing for the handoff is defined in [`references/policies/continuity-model.md`](references/policies/continuity-model.md) ("EOD → next-SOD handoff payload").
- **Review-and-lock as a gate on continuity.** `send_only` runs explicitly do NOT write continuity (the "Critical Rule" in [`references/policies/review-and-locking.md`](references/policies/review-and-locking.md)); corrupted prior state triggers a 7-day cooldown; `auto_locked` requires a run-history gate before it's permitted.
- **Eight-capability runtime contract.** The plugin is portable to any runtime that demonstrates the eight capabilities in [`references/policies/runtime-capabilities.md`](references/policies/runtime-capabilities.md) per the proof items in [`references/conformance.md`](references/conformance.md). No vendor lock-in; no built-in tool assumption.

## Troubleshooting

**Report status is `blocked`.** Check `validation_meta.warnings` for the reason. Common causes: `runtime_input.mode` missing or not in `enabled_modes`, required source (`tasks`-or-`manual`) unavailable, corrupted prior-state record. See [`references/policies/review-and-locking.md`](references/policies/review-and-locking.md) "Auto-lock validation gate" for the full blocking-class enumeration.

**Report status is `partial`.** A connector returned an error, timeout, or auth failure for a non-required source. Check `validation_meta.missing_sources[]`. The report still produces with available sources; the missing ones are named.

**SOD reports "first_run" continuity status but should have prior state.** Either the EOD was run under `send_only` (which does NOT create continuity) or the persistence layer did not find the record. Check the continuity store and the `review_policy.finalization_mode` of yesterday's EOD.

**`auto_locked` configuration rejected on the first run.** Per the day-0 rule in [`references/policies/review-and-locking.md`](references/policies/review-and-locking.md) "Deployment posture," `auto_locked` requires at least one prior successful `reviewed_locked` run to build the run-history gate. Configure `reviewed_locked` for the first few cycles, then switch.

**A reviewer edited the draft and the output went `blocked` instead of `reviewed_locked`.** The material-edit tie-breaker in [`references/policies/review-and-locking.md`](references/policies/review-and-locking.md) ("Material vs. non-material edits") classifies some edits as material; material edits require re-review. Check `review_meta` on the output.

**Connector returned zero items but operator says there should be data.** Distinguish between `connector_returned_successfully_with_zero_items` (genuinely empty source, no warning) and `connector_errored` (source outcome unknown, surfaces in `validation_meta.missing_sources`). See the `daily-reporting/SKILL.md` "If data is missing" section.
