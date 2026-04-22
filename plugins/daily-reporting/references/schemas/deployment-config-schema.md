# Deployment Config Schema

**Schema version:** `schema_version: "1.0"`

This schema defines the saved setup config for `daily-reporting`.

## Purpose

The reporting skill should load this config first so normal runs do not need the same setup questions every time.

## Source keys

This is the **canonical list** of the six source keys used throughout the plugin. Other documents (README, main skill, setup skill, normalized-context schema, retrieval-rules) reference this section rather than restating the list.

Use these source keys in `source_map`, retrieval windows, and wherever the plugin refers to a source family:

Approved external source families:
- `calendar`
- `email`
- `tasks` (executive workflow only)
- `meetings`

Internal support families:
- `prior_state`
- `manual`

Connector names can vary by client or tool, for example:
- `google-calendar`
- `outlook-calendar`
- `gmail`
- `executive-workflow`
- `meeting-notes`
- `prior-state`

Terminology note: where the plugin speaks of the "executive workflow" (for example, the `executive_workflow_only` scope rule or the "tasks (executive workflow only)" annotation above), it means the executive's task and priority context — the abstract concept. The connector named `executive-workflow` is one provider of that context; the two are not synonymous.

## Top-level shape

```text
deployment_config
- version
- plugin_name
- deployment_name
- deployment_mode
- enabled_modes
- defaults
- source_map
- connector_settings
- validation_status
```

## Deployment mode

`deployment_mode` declares whether the deployment uses live connectors or runs without them.

Allowed values:
- `connected` — all enabled sources are served by live connectors
- `manual_only` — no connectors are wired; the deployment runs from operator input and prior state only
- `disconnected` — connectors are wired but temporarily not used (degrade to manual fallbacks for the current deployment)

`enabled_modes` is an ordered list of which reporting modes are active for this deployment; each entry must be one of `sod` or `eod` (see `runtime-input-schema.md` for the `mode` enum).

## Required defaults

`defaults` should include:
- `timezone`
- `participants`
- `continuity_store`
- `delivery_policy`
- `review_policy`
- `retrieval_policy`
- `retrieval_windows`

## Participants (canonical shape)

`defaults.participants` is the canonical declaration of the participant object shape. Other schemas (`runtime-input-schema.md`, `normalized-context-schema.md`, `output-schema.md`) reference this shape by pointer rather than restating it.

Each `participants[]` entry is an object with:

| Field | Type | Description |
|---|---|---|
| `name` | string | Human-readable label used in reports and `structured_state.confirmed_by` matches. |
| `role` | string | Free-text role label (e.g. `Executive`, `EA / Operator`, `Assistant / CoS`). |
| `owner_type` | enum string | Role identifier used for permission checks and the `confirmed_role` vocabulary. Allowed values: `exec`, `ea`, `assistant`. |

Vocabulary rule: wherever a role is referenced by identifier (not by participant name) — including `review_policy.can_review`, `review_policy.can_confirm`, and `structured_state.confirmed_role` — use the `owner_type` vocabulary (`exec` | `ea` | `assistant`). Do not use `"executive"` as a role identifier; use `"exec"`.

## Continuity store

`defaults.continuity_store` declares where prior locked reports and structured state live so the next cycle can seed from them.

| Field | Type | Description |
|---|---|---|
| `type` | string | Continuity backend identifier. Current canonical value: `file_archive`. |
| `human_readable_reports_path` | string | Relative or absolute path where locked human-readable reports are written. |
| `structured_state_path` | string | Relative or absolute path where locked structured-state artifacts are written. |
| `allow_draft_continuity` | boolean | When `true`, draft (unlocked) reports may seed continuity; when `false`, only locked reports do. See `../policies/continuity-model.md`. |

## Delivery policy

`defaults.delivery_policy` declares where drafts and locked finals are sent.

| Field | Type | Description |
|---|---|---|
| `draft_destination` | string | Identifier of the surface that receives generated drafts and revisions awaiting review. |
| `final_destination` | string | Identifier of the surface that receives locked finals. |
| `send_revisions_to_review_surface` | boolean | When `true`, in-review revisions are re-sent to the draft/review surface. |
| `send_only_locked_finals_to_final_destination` | boolean | When `true`, only locked reports reach `final_destination`. |

## Retrieval policy

`defaults.retrieval_policy` declares the default behavior connectors should assume when the deployment runs.

| Field | Type | Description |
|---|---|---|
| `use_delegated_retrieval_when_available` | boolean | When `true`, connector families may fan out work via the host runtime's delegated-retrieval primitive (see `../policies/retrieval-rules.md`, "delegated retrieval"). Named tool-agnostically so the package does not assume a specific host primitive. |
| `prefer_normalized_summaries` | boolean | When `true`, connectors must return normalized per-family summaries (the shapes in `normalized-context-schema.md`) rather than raw payloads. |
| `allow_raw_transcripts_by_default` | boolean | When `true`, meeting and email connectors may include raw transcript text; normally `false`. |
| `executive_scope_only` | boolean | When `true`, connectors must exclude non-executive-owned items from retrieval by default. |

## Retrieval windows

`defaults.retrieval_windows` declares the default retrieval window for each source family, keyed by mode. The canonical prose form lives in `../policies/source-windows.md`; this schema enumerates the canonical string values below. A runtime override may replace any single entry for a single run (see `runtime-input-schema.md`, `source_overrides.<family>.retrieval_window`).

Shape:

```text
retrieval_windows
- sod
  - calendar
  - email
  - tasks
  - meetings
  - prior_state
- eod
  - calendar
  - email
  - tasks
  - meetings
  - prior_state
```

Canonical values per source family (same vocabulary used by runtime `source_overrides.<family>.retrieval_window`):

| Source | Allowed values | Intended behavior |
|---|---|---|
| `calendar` | `today`, `today_plus_tomorrow_preview` | `today`: current-cycle events only. `today_plus_tomorrow_preview`: today plus an optional lookahead for the next cycle. |
| `email` | `since_last_locked_eod`, `today_unresolved_only` | `since_last_locked_eod`: everything since the prior locked EOD. `today_unresolved_only`: today's messages filtered to unresolved items. |
| `tasks` | `active_executive_items_only`, `today_plus_executive_carryforward_candidates` | `active_executive_items_only`: open executive-scoped items. `today_plus_executive_carryforward_candidates`: today's changes plus items likely to carry forward. |
| `meetings` | `last_3_business_days_unresolved_only`, `today_only` | `last_3_business_days_unresolved_only`: recent meetings filtered to unresolved/action-relevant. `today_only`: meetings from the current cycle date only. |
| `prior_state` | `most_recent_locked_eod`, `current_day_locked_sod` | `most_recent_locked_eod`: seed SOD from the prior EOD's locked state. `current_day_locked_sod`: seed EOD from the same day's locked SOD. |

## Review policy

`defaults.review_policy` is required and must include:
- `finalization_mode`
- `review_required`
- `confirmation_required`
- `can_review`
- `can_confirm`
- `same_person_may_review_and_confirm`
- `material_edits_require_reconfirmation` — see `../policies/review-and-locking.md` ("Material vs. non-material edits") for the canonical definition of which edits count as material
- `non_material_edits_require_reconfirmation` — see `../policies/review-and-locking.md` ("Material vs. non-material edits") for the canonical definition of which edits count as non-material
- `correction_from_authorized_confirmer_implies_confirmation`
- `auto_send_after_generation`
- `auto_lock_after_generation`
- `send_only_reports_create_continuity`

Role-valued fields (`can_review`, `can_confirm`) must use the `owner_type` vocabulary declared under "Participants (canonical shape)" — `exec`, `ea`, `assistant`. Do not use `"executive"` as a role identifier. Every entry in `can_review` and `can_confirm` must additionally correspond to the `owner_type` of at least one entry in `defaults.participants` (see `../policies/review-and-locking.md`, "Reviewer authority resolution" for the canonical resolution contract and referential-integrity rule); this is enforced by the "Minimum valid deployment" checklist below.

`review_policy` may also include the optional per-mode override block:

- `mode_overrides?` — per-mode override of any subset of the 12 review_policy fields above. Shape:

```text
mode_overrides
- sod?
  - <any review_policy field above>: <override value>
- eod?
  - <any review_policy field above>: <override value>
```

Both `mode_overrides.sod` and `mode_overrides.eod` are optional objects; each may contain any subset of the twelve review_policy fields listed above. An empty object (`{}`) means "no per-mode override for this mode"; the base `review_policy` value applies. `mode_overrides` is **out of scope for v1**: the starter template (`../../skills/daily-reporting-setup/assets/config-template.json`) and the connected example (`../examples/deployment-config.connected.json`) do not ship this block, and the v1 plugin does not define merge semantics between base policy and per-mode overrides. The shape is declared here for forward compatibility only — deployments should not populate `mode_overrides` until a future version documents the merge behavior.

## Source map

Expected keys: the six canonical source keys declared in "Source keys" above.

Each enabled source entry should declare, when relevant:
- `enabled`
- `provider`
- `input_domains` (always an array of strings; use a one-element array when the family contributes a single domain)
- `authority`
- `scope_rule` when the family requires one

### `authority` (enum)

`source_map.<family>.authority` declares the family's weight when the merge rules in `normalized-context-schema.md` combine sources.

Allowed values:
- `authoritative` — the family is the primary source for its input domain. Merge rules prefer authoritative values and only fall back to other sources when the authoritative source is absent or explicitly empty.
- `supporting` — the family enriches merged context (adds signal) but does not override authoritative values on its own.
- `fallback` — the family is consulted only when no authoritative or supporting source produces a value for the relevant field. `manual` is the canonical fallback.

Ordering: `authoritative` > `supporting` > `fallback`.

### `scope_rule` (enum, per family)

`source_map.<family>.scope_rule` narrows which items a connector may return.

Supported families: `tasks` is the only family for which a `scope_rule` is required in v1. Other families may accept a `scope_rule` in the future but have no defined values today; implementers should treat unrecognized `scope_rule` values as a validation error.

Allowed values for `tasks`:
- `executive_workflow_only` — the connector must exclude non-executive-owned items from retrieval, even if the underlying system contains them. An item's owner is determined by the connector's executive-workflow provider; items whose owner is not the executive (or executive's delegated surface) must not appear in the returned `priority_context` or `task_snapshot`.

Important rule:
- `tasks` must remain explicitly executive-scoped, for example `scope_rule: executive_workflow_only`.

If a connector setting for the same provider also accepts a `scope_rule` (see `connector_settings.executive-workflow`), the two values must agree — the source-map entry is the canonical declaration and the connector setting is a per-connector echo for implementation clarity.

## Connector settings

`connector_settings` is an optional top-level object keyed by connector name. Each entry configures one connector for this deployment. Connector names vary by provider (see "Connector names" above).

Every connector entry may declare:

| Field | Type | Description |
|---|---|---|
| `enabled` | boolean | When `false`, the connector is skipped even if its source family is enabled in `source_map`. |

Additionally, every connector entry may declare the following optional sub-fields:

- `budget?: integer` — per-run retrieval budget override for this connector. See `../policies/retrieval-budgets.md` ("Override mechanism") for defaults and behavior.
- `filtering_overrides?: object` — per-connector override of default noise-exclusion or signal-prioritization rules. See `../policies/source-filtering.md` ("Override mechanism") for shape and behavior.

Per-connector additional fields (only keys that appear in the starter template and example are declared below; unknown keys are reserved):

**`executive-workflow`** (connector for the `tasks` source family):

| Field | Type | Description |
|---|---|---|
| `scope_rule` | enum string | Echoes `source_map.tasks.scope_rule`; must agree. See `scope_rule (enum, per family)` above. |
| `include_support_work_only_if_exec_relevant` | boolean | When `true`, support-layer items surface only when they materially affect executive execution. |

**`meeting-notes`** (connector for the `meetings` source family):

| Field | Type | Description |
|---|---|---|
| `unresolved_only` | boolean | When `true`, the connector returns only unresolved items from the configured retrieval window. |
| `action_relevant_only` | boolean | When `true`, the connector filters to action/followup-bearing items. |

**`prior-state`** (connector for the `prior_state` source family):

| Field | Type | Description |
|---|---|---|
| `prefer_structured_state` | boolean | When `true`, the connector reads `structured_state_path` in preference to human-readable reports. |
| `allow_draft_continuity` | boolean | When `true`, draft (unlocked) prior state may seed this cycle; mirror of `continuity_store.allow_draft_continuity`. |

For `connector_settings.gmail` specifically:
- `high_signal_labels?: string[]` — gmail labels treated as high-signal for prioritization (e.g., `["Needs Action", "Urgent", "Important", "VIP"]`). See `../policies/source-filtering.md` (email signal prioritization).
- `vip_senders?: string[]` — email addresses or domains treated as VIP for prioritization. See `../policies/source-filtering.md`.

`google-calendar`, `outlook-calendar`, `gmail`, and `manual` in the starter template use only `enabled` today.

## Validation status

`validation_status` should include:
- `configured`
- `last_validated_at`
- `blocking_issues`

## Minimum valid deployment

This is the canonical validation checklist for a deployment of `daily-reporting`. The setup skill (`skills/daily-reporting-setup/SKILL.md`) references this list rather than restating it.

A deployment is minimally valid when:
- at least one mode is enabled
- timezone exists
- participants exist
- continuity store exists
- delivery policy exists
- review policy exists
- every entry in `review_policy.can_review` and `review_policy.can_confirm` corresponds to the `owner_type` of at least one participant (see `../policies/review-and-locking.md`, "Reviewer authority resolution")
- executive priority context has a valid source path through `tasks` or manual fallback
- approved source mappings are connected or explicitly manual
- validation has no unresolved blocking issue
