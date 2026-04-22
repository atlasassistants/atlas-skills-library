# Runtime Input Schema

**Schema version:** `schema_version: "1.0"`

## Purpose

Runtime input should stay small. The skill should use saved config first, then apply one-run changes.

## Minimum required runtime input

```text
runtime_input
- mode
```

Allowed values:
- `sod`
- `eod`

Mode-check failure paths (enforced at workflow step 2 in `../../skills/daily-reporting/SKILL.md`):
- If `runtime_input.mode` is missing or empty, the skill must return `status: blocked` with a `validation_meta.warnings` entry naming the missing field. The skill must not default to either `sod` or `eod` silently.
- If `runtime_input.mode` is present but is not in `deployment_config.enabled_modes`, the skill must return `status: blocked` with a `validation_meta.warnings` entry naming both the requested mode and the configured `enabled_modes`. The skill must not silently substitute the only enabled mode and must not run a partial cycle.

## Optional runtime overrides

```text
runtime_input
- mode
- report_date?
- timezone?
- participants?
- source_overrides?
- operator_notes?
- confirmed_priorities?
- manual_overrides?
```

Field notes:
- `participants` uses the canonical participant shape declared in `deployment-config-schema.md` ("Participants (canonical shape)"): `{ name, role, owner_type: "exec" | "ea" | "assistant" }`. Do not redeclare.
- `source_overrides` should be an override object keyed by source family (see "Rules" below for the canonical source keys)
- `operator_notes` should be an ordered list of short human notes for the current run
- `confirmed_priorities` should be an ordered list of explicitly human-confirmed priorities
- `manual_overrides` should be a targeted manual override object for fields the human wants to set directly

Recommended `source_overrides` shape:

```text
source_overrides
- <source_family>
  - enabled?
  - retrieval_window?
  - use_manual_fallback?
  - replace_with_manual?
```

`source_overrides.<family>.retrieval_window` uses the canonical per-family vocabulary declared in `deployment-config-schema.md` ("Retrieval windows"). An override replaces the deployment default for the single run it applies to. Allowed values by family:

| Source | Allowed values |
|---|---|
| `calendar` | `today`, `today_plus_tomorrow_preview` |
| `email` | `since_last_locked_eod`, `today_unresolved_only` |
| `tasks` | `active_executive_items_only`, `today_plus_executive_carryforward_candidates` |
| `meetings` | `last_3_business_days_unresolved_only`, `today_only` |
| `prior_state` | `most_recent_locked_eod`, `current_day_locked_sod` |

See `deployment-config-schema.md` "Retrieval windows" for the semantic of each value and `../policies/source-windows.md` for prose defaults.

`manual_overrides` uses the shape defined canonically in `normalized-context-schema.md` §`manual`. Do not redeclare the sub-shape here.

Override rules:
- `source_overrides` changes how a source is used for the current run only
- `manual_overrides` changes only the fields it explicitly provides
- blank or omitted fields must not erase unrelated connected-source results by default

## Rules

- If `report_date` is missing, resolve the cycle date from the current runtime time using the saved timezone.
- Do not ask for timezone or participants every run unless setup is incomplete or an override is intended.
- Runtime overrides must stay inside the approved source model.
- `source_overrides` should use these source keys: `calendar`, `email`, `tasks`, `meetings`, `prior_state`, `manual`.
- `tasks` overrides must not widen into a whole-team audit.
- `manual_overrides` must stay executive-centered and must not broaden the run into an org-wide summary.
- Avoid adding deployment-specific transport, routing, or logging fields to runtime input.

### `report_date` constraints

`report_date?` is an optional override. When provided, these constraints apply. The monotonicity assumption they enforce is stated canonically in `../policies/continuity-model.md` ("Report date monotonicity").

- **Future dates.** `report_date` must not be later than the current local date resolved from `deployment_config.defaults.timezone`. If it is, and the deployment does not set `allow_future_report_date = true`, the skill must return `status: blocked` with a `validation_meta.warnings` entry naming the requested date and the resolved local date. Generating a future cycle preemptively (for example, drafting Thursday's SOD on Tuesday) is not a default-supported path.
- **Existing lock (overwrite).** If a locked report already exists for the tuple `(mode, report_date, deployment)` in `deployment_config.defaults.continuity_store`, the skill must refuse to re-run by default — return `status: blocked` with a `validation_meta.warnings` entry naming the existing lock. Re-running over an existing lock requires an explicit deployment-configured override flag (for example, `allow_overwrite_locked_report = true`); without it, a silent overwrite under `auto_locked` is forbidden.
- **Non-monotonic date (continuity inversion).** If `report_date` is earlier than the `report_date` of the most recent locked continuity record for this deployment, the run may still proceed but must surface a `validation_meta.warnings` entry naming both dates (for example, "`report_date` 2026-04-18 precedes most recent locked continuity 2026-04-20"). Non-monotonic input does not by itself seed `merged_context` from the newer locked record — prior-state loading follows the normal continuity fallback chain for the requested `report_date`.

Outcomes from these constraints wire into `validation_meta` per `../schemas/output-schema.md` ("Validation meta"). When a required source would also be affected (for example, `prior_state` cannot be loaded for a non-monotonic `report_date`), pair the `validation_meta.warnings` entry with a `validation_meta.missing_sources[]` entry using the shape defined in that section.

### Timezone edge cases

`report_date` is tied to a timezone, and timezones are not always stable across a deployment's lifetime (DST transitions, executive travel, one-run overrides). The following cases are the canonical handling.

1. **Saved timezone resolution.** `report_date` is a calendar date computed in the deployment's saved `defaults.timezone` at the moment the run is initiated. The plugin treats a day as a calendar day in that timezone; 23-hour and 25-hour wall-clock days (DST transitions) count as 1 day of `report_date` advancement each, not fractional. A DST transition does not by itself cause `report_date` to skip or repeat.
2. **One-run timezone override.** If the runtime input supplies `timezone` as a one-run override, it takes precedence over the saved default for that run's `report_date` computation. The run's output (`structured_state.metadata` or an equivalent output field) SHOULD record both the saved timezone and the effective-at-runtime timezone so continuity across timezone shifts is traceable. If the override differs from the saved default, emit a `validation_meta.warnings` entry naming both values — informational, not blocking — so reviewers can see the run ran under a non-default timezone.
3. **DST ambiguous moments.** If the run is initiated during a DST fall-back hour (the same wall-clock time occurs twice) or a spring-forward gap (a wall-clock time that does not exist), resolve the date via the underlying UTC instant, not the wall-clock representation. The plugin relies on the runtime's timezone library (IANA tzdata or equivalent) to perform this resolution; it does not itself arbitrate DST. A correctly-implemented runtime will never produce an ambiguous `report_date` from a valid UTC instant.
4. **Executive travel.** An executive travelling across timezones is a runtime-override case (#2 above). The plugin does not detect travel, and it does not infer intent from a runtime-input `timezone` that happens to differ from the saved default; the runtime decides whether to apply an override per-run. If no override is supplied, `report_date` follows the saved default, which may lag or lead the executive's local day by up to ~24 hours. Deployments that expect frequent travel SHOULD surface an override mechanism to their runtime (for example, a setup toggle that prompts for timezone at SOD initiation) rather than relying on the executive to hand-edit runtime input.
