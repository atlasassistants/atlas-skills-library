# Output Schema

**Schema version:** `schema_version: "1.0"`

## Purpose

`daily-reporting` produces:
1. a human-readable report
2. a structured state artifact for continuity

## Top-level shape

```text
daily_reporting_output
- mode
- report_date
- timezone
- status
- report_stage
- finalization_mode?
- human_readable_report
- structured_state
- delivery_meta?
- validation_meta?
```

Recommended values:
- `status` → `draft`, `final`, `partial`, or `blocked`
- `report_stage` → `generated`, `reviewed`, `locked`, or `sent` (stage within the review flow)
- `finalization_mode?` → `reviewed_locked`, `auto_locked`, or `send_only` (echoes `deployment_config.defaults.review_policy.finalization_mode`)

### `report_stage` vs `finalization_mode`

These two fields are orthogonal and must not be conflated:

| Field | Describes | Allowed values | Semantics |
|---|---|---|---|
| `report_stage` | Where the report is in the review flow | `generated`, `reviewed`, `locked`, `sent` | `generated`: draft produced, not yet reviewed. `reviewed`: reviewed (with or without edits) but not yet locked. `locked`: confirmed and locked for continuity. `sent`: locked final delivered to `delivery_meta.final_destination`. |
| `finalization_mode?` | Which finalization policy the deployment applied | `reviewed_locked`, `auto_locked`, `send_only` | Echo of `review_policy.finalization_mode` (see `../policies/review-and-locking.md`). Present once the report reaches `locked` or `sent`. |

A `reviewed_locked` report reaching `report_stage: locked` means a reviewed, human-confirmed report that was locked. An `auto_locked` report may reach `report_stage: locked` without a reviewer. A `send_only` report may reach `report_stage: sent` without ever passing through `reviewed` or `locked` (subject to `review_policy.send_only_reports_create_continuity`).

## Participants

Wherever `participants` appears inside this output (notably under `structured_state.participants`), it uses the canonical participant shape declared in `deployment-config-schema.md` ("Participants (canonical shape)"): `{ name, role, owner_type: "exec" | "ea" | "assistant" }`. Do not redeclare.

## Executive Scope Rule

See `../policies/review-and-locking.md` ("Executive Scope Rule") for the canonical rule. The output must remain executive-centered; scope enforcement happens at review and locking time.

## Structured state

The structured state should include, when available:
- `mode`
- `report_date`
- `timezone`
- `status`
- `report_stage`
- `finalization_mode?`
- `confirmed_by?`
- `confirmed_role?`
- `confirmed_at?`
- `locked_at?`
- `participants`
- `priorities`
- `carryovers`
- `dependencies`
- `risks`
- `unresolved_items`
- `completed_items?`
- `notes_for_next_cycle`

Use `mode` consistently for `sod` or `eod`. Do not introduce a second field like `report_type` for the same concept.

### Confirmation fields

`confirmed_by?` and `confirmed_role?` identify who confirmed the report and in which role they confirmed.

| Field | Type | Description |
|---|---|---|
| `confirmed_by?` | string | Must match one of `participants[].name` in the same structured_state. It identifies the specific person (by their display name), not the role. |
| `confirmed_role?` | enum string | The role under which the confirmation occurred. Uses the same vocabulary as `owner_type` (see `deployment-config-schema.md`, "Participants (canonical shape)"): `exec`, `ea`, `assistant`. Must match the `owner_type` of the participant whose `name` equals `confirmed_by`. |
| `confirmed_at?` | ISO-8601 timestamp | When the confirmation happened. |
| `locked_at?` | ISO-8601 timestamp | When the report transitioned to `report_stage: locked`. |

### Polish rule

`structured_state` and `human_readable_report` share the same executive-centered working set (`merged_context`) but they have different polish rules:

- **`structured_state` fields must be copied verbatim from `merged_context`.** This applies to every list-typed field in `structured_state` — `priorities`, `carryovers`, `dependencies`, `risks`, `unresolved_items`, `completed_items`, and `notes_for_next_cycle`. No re-wording, no new items, no synthesized narrative. If a reviewer changes a priority during locking, that change is a material edit to `merged_context` and the updated value then propagates verbatim.
- **`human_readable_report` may polish narrative slots.** Three narrative slots are explicitly permitted to be polished/synthesized at draft time from `merged_context`: `{{priority_context_summary}}` (SOD) and `{{proposed_focus_statement}}` (SOD — sourced from `merged_context.proposed_focus`) and `{{day_verdict_summary}}` (EOD). Every other slot in both templates must be rendered verbatim from the `merged_context` field named in the template's "Slot-to-field reference" table.

### Polish-slot verification

After the three polished slots are filled and before `structured_state` is locked (or `human_readable_report` is sent under `send_only`), a runtime SHOULD verify that each polished slot stays within its declared sources. This is a post-hoc anti-hallucination check on the three slots that the Polish rule above explicitly permits to be synthesized — it is not a replacement for that rule but a guardrail on it.

1. Each polished slot may only SYNTHESIZE from named `merged_context` fields (the slot's declared source). The declared sources are:
   - `{{priority_context_summary}}` (SOD) → `merged_context.priorities`, `merged_context.blockers`, `merged_context.dependencies`, and — when present as part of EOD-to-SOD continuity context — `merged_context.prior_locked_state.priorities`.
   - `{{proposed_focus_statement}}` (SOD) → `merged_context.proposed_focus[]`.
   - `{{day_verdict_summary}}` (EOD) → `merged_context.completed_items`, `merged_context.unresolved_items`, and `merged_context.carryovers`.
2. A polished slot must not introduce net-new facts. No dates, names, organizations, commitments, numbers, or claims may appear in a polished slot that do not appear somewhere in its declared source fields. Rewording and compression are permitted; novel content is not.
3. A runtime SHOULD verify each polished slot by checking that every noun phrase with a specific referent (a person name, a project name, an organization, a prioritized item) appears in the slot's declared source fields. Implementations may use substring matching, fuzzy matching, token overlap thresholds, or a second LLM pass as the verifier; the plugin does not prescribe a specific technique.
4. If verification fails, downgrade the slot to a verbatim fallback — emit the first item from the slot's primary source field instead of the polished synthesis. Concretely: `{{priority_context_summary}}` falls back to `merged_context.priorities[0]`, `{{proposed_focus_statement}}` falls back to `merged_context.proposed_focus[0]`, and `{{day_verdict_summary}}` falls back to `merged_context.completed_items[0]` (or `merged_context.unresolved_items[0]` if `completed_items` is empty). A verbatim fallback should also emit a `validation_meta.warnings` entry naming the slot that was downgraded.

This verification step catches the `auto_locked` path's lazy-polish risk — an unreviewed synthesis that drifts beyond `merged_context` would otherwise become continuity silently — and complements the "Auto-lock validation gate" in `../policies/review-and-locking.md`, which catches the composed-report-level failures (empty priorities, blocking warnings, unexpected `continuity_status: unavailable`).

### Field population mapping

`structured_state` fields map to `merged_context` as follows:

| `structured_state` field | `merged_context` source | Notes |
|---|---|---|
| `priorities` | `priorities` | Verbatim |
| `carryovers` | `carryovers` | Verbatim |
| `dependencies` | `dependencies` | Verbatim |
| `risks` | `risks` | Verbatim |
| `unresolved_items` | `unresolved_items` | Verbatim. `merged_context.unresolved_items` is itself derived per `./normalized-context-schema.md` ("Field derivation"), which unions `prior_state.prior_locked_state.unresolved_items`, still-relevant `email.inbox_flags.pending_decisions`/`unresolved_threads`, and still-open `tasks.task_snapshot.stalled_items`. |
| `completed_items` | `completed_items` | Verbatim. EOD-primary. |
| `notes_for_next_cycle` | `notes_for_next_cycle` | Verbatim. `merged_context.notes_for_next_cycle` is itself derived from `manual.freeform_operator_notes`, `manual.manual_overrides.notes_for_this_cycle`, and (EOD) still-relevant `prior_state.prior_locked_state.notes_for_next_cycle`. |

If `merged_context` does not contain content for a `structured_state` field, omit the field or emit an empty array — never synthesize new content directly into `structured_state`.

## Continuity rule

See `../policies/review-and-locking.md` ("Critical Rule") for the canonical gating rule that determines when a report becomes saved continuity.

## Delivery meta

`delivery_meta?`, when present, records the delivery destinations used for this run. Keys echo the deployment-config's `delivery_policy` with a naming adjustment: `delivery_policy.draft_destination` is recorded here as `review_destination` (the destination for in-review drafts and revisions).

| Field | Type | Description |
|---|---|---|
| `review_destination` | string | Destination identifier used for drafts and in-review revisions. Matches `deployment_config.defaults.delivery_policy.draft_destination` (renamed here to describe the runtime role of the surface — where review happens). |
| `final_destination` | string | Destination identifier used for locked finals. Matches `deployment_config.defaults.delivery_policy.final_destination`. |

## Validation meta

`validation_meta`, when present, should help a client or tool understand non-fatal issues.

Recommended fields:
- `schema_version`
- `warnings`
- `continuity_status?` (`available`, `unavailable`, `first_run`)
- `missing_sources?`

### `missing_sources[]`

`missing_sources?` is an array recording source families that did not return usable data for reasons other than being intentionally disabled. Each element has this shape:

| Field | Type | Description |
|---|---|---|
| `source_family` | enum string | The affected source key. Must be one of the canonical source keys declared in `deployment-config-schema.md` §Source keys. |
| `reason` | enum string | Why the source did not contribute. Allowed values: `error` (connector returned an error), `timeout` (connector exceeded its retrieval window), `auth_failure` (authentication or authorization failed), `invalid_payload` (connector returned data that failed schema validation, including a corrupted prior locked state per `../policies/continuity-model.md`), `required_but_absent` (source is marked required in the deployment config but was unreachable and no fallback exists). |

Populate `missing_sources[]` only for case (b) in `../../skills/daily-reporting/SKILL.md` ("If data is missing") — connector error, timeout, auth failure, or invalid payload. Do not populate it for case (a) (connector returned zero items successfully) or case (c) (connector intentionally disabled).

A populated `missing_sources[]` must be paired with a corresponding `warnings[]` entry and a downgraded `status` (`partial`, or `blocked` when a required source is absent).
