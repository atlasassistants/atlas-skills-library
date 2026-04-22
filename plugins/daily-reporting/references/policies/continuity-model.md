# Continuity Model

## Purpose

SOD and EOD (see `../../skills/daily-reporting/SKILL.md` §Modes for the canonical mode definitions) should not behave like isolated drafts. Each setup should define how continuity is saved and reused.

## Continuity outputs

See `../schemas/output-schema.md` §Purpose for the two output artifacts (the human-readable report and the structured state record for continuity).

The structured state is the primary continuity source. The human-readable report remains useful for review and auditing.

## Report date monotonicity

The SOD ↔ EOD alternation below assumes `report_date` advances monotonically across locked cycles for a given deployment. This is an explicit assumption, not a free-floating convention: continuity ordering cannot invert without producing the "today's prior state precedes a newer locked state" corruption described in `../schemas/runtime-input-schema.md` ("`report_date` constraints").

Enforcement lives in `../schemas/runtime-input-schema.md` ("`report_date` constraints"); that section is canonical. In summary, for this policy's purposes:
- a `report_date` in the future (relative to the deployment timezone) is rejected by default,
- re-running a locked `(mode, report_date, deployment)` tuple is rejected by default,
- a `report_date` earlier than the most recent locked continuity record is allowed to proceed but must be flagged in `validation_meta.warnings`, and prior-state loading still follows the normal fallback chain for the requested date rather than the newer locked record.

The fallback chains below read "most recent locked EOD" and "current-day locked SOD" under this monotonicity assumption — if monotonicity is violated, the warning is the signal to the reviewer; the chains themselves do not try to self-correct.

## Default Continuity Flow

- SOD should prefer the most recent locked EOD
- EOD should prefer the current day locked SOD

### SOD fallback chain (`send_only` ↔ continuity)

If yesterday's EOD ran under `send_only` (or any finalization mode that did not lock), no locked EOD exists for the prior day. In that case, SOD must resolve prior state in this order:

1. the most recent locked EOD for the prior day (the default preference above)
2. if absent, the most recent locked EOD within a bounded look-back window configured per deployment (recommended default: 7 days) — this preserves some continuity rather than losing it silently
3. if still absent, surface `continuity_status: unavailable` and add a `validation_meta.warnings` entry naming the gap; do not silently reach further back

Step 2's bounded window must be treated as explicit stale state: the run still proceeds, but implementers should consider also emitting a warning so reviewers know continuity is older than one cycle.

### EOD fallback chain (`send_only` ↔ continuity)

The symmetric case: if today's SOD ran under `send_only` (or any finalization mode that did not lock), no current-day locked SOD exists for EOD to anchor on. EOD must resolve prior state in this order:

1. the current-day locked SOD (the default preference above)
2. if absent, the most recent locked EOD for the prior day — this gives EOD some continuity anchor rather than running with no prior state at all
3. if still absent, surface `continuity_status: unavailable` and add a `validation_meta.warnings` entry naming the gap; do not silently run without prior state

Both fallback chains interact with `review-and-locking.md` ("Critical Rule" for `send_only`): when `send_only_reports_create_continuity = false`, the fallback chain is the only path that preserves continuity across a `send_only` cycle.

## EOD → next-SOD handoff payload

A locked EOD's `structured_state` is the sole continuity input that tomorrow's SOD reads as `source_family_results.prior_state.prior_locked_state`. To keep that handoff load-bearing rather than ornamental, a locked EOD must populate the following `structured_state` fields (omitted or empty fields are treated as "nothing to hand off," not as a missing obligation, but a locked EOD that omits all of them is substantively broken even if formally valid):

| `structured_state` field | Must populate at EOD lock | Purpose in next SOD |
|---|---|---|
| `priorities` | yes | Read by next SOD as `prior_locked_state.priorities`; seeds next SOD's `merged_context.planned_priorities` (the "what was planned" baseline — note: for the current EOD run, `planned_priorities` reflects *this* day's SOD lock, not yesterday's). |
| `carryovers` | yes if any carry | Surviving work items to be re-evaluated next SOD. Subject to the retire-vs-carry rule below. |
| `dependencies` | yes if any open | Seeds `merged_context.dependencies` in the next SOD. |
| `risks` | yes if any open | Seeds `merged_context.risks` in the next SOD. |
| `unresolved_items` | yes | Open decisions, unresolved threads, stalled items not closed during the day. Seeds `merged_context.unresolved_items` in the next SOD via the union derivation in `../schemas/normalized-context-schema.md` ("Field derivation"). |
| `notes_for_next_cycle` | yes if any forward-looking notes | Seeds `merged_context.notes_for_next_cycle` in the next SOD (see the same "Field derivation" entry). |
| `completed_items` | yes if anything completed | Not re-seeded into next SOD's `merged_context` — this is a historical record, useful for audit and EOD-to-EOD comparison only. |

`structured_state.completed_items` is deliberately EOD-only and does not carry forward. It records what moved during the day that just ended; it is not a candidate for next-cycle priorities.

See `../schemas/output-schema.md` ("Structured state" and "Field population mapping") for the full `structured_state` shape and the verbatim-copy rule from `merged_context`.

### Retire-vs-carry rule for carryovers

Not every item in `structured_state.carryovers` should survive forward indefinitely. Applied when the next SOD runs and considers the just-loaded `prior_locked_state.carryovers`:

A carryover **carries** into the next cycle's `merged_context.carryovers` when at least one of the following holds:
1. The executive or reviewer explicitly confirmed the carryover during this cycle's review (it was added via `manual.manual_overrides.carryovers` or survived an explicit reviewer edit).
2. A current-cycle source still references the item — for example, a matching open task in `tasks.priority_context.carryover_candidates`, an unresolved email thread, or a meeting follow-up owned by the executive.
3. The carryover has a declared due date or dependency that has not yet passed.

A carryover **retires** (is not copied into next cycle's `merged_context.carryovers`) when all of the following hold:
1. No current-cycle source references it.
2. It has been present in `prior_locked_state.carryovers` across more than three consecutive locked cycles without any current-cycle source corroboration — this bounded age prevents stale carryovers from persisting forever on their own momentum.
3. No reviewer has explicitly confirmed it this cycle.

Retirement is silent by default; if a deployment wants retired carryovers surfaced, the retirement can be recorded as an informational `validation_meta.warnings` entry. A retired carryover does not appear in the next cycle's `merged_context.carryovers` and therefore does not appear in the next cycle's `structured_state.carryovers`.

This rule is the concrete form of `../policies/retrieval-rules.md` ("Source Priority"), which states that older carryovers should survive only if current-cycle context still suggests they matter.

## First-Run Rule

If no prior locked state exists, the skill may still run, but it must mark continuity as `unavailable` or `first_run` (per the vocabulary below) and avoid inventing carryovers.

## Corrupted prior state rule

A prior locked state record may exist on disk but be malformed, truncated, schema-invalid, or otherwise unreadable (for example, from an interrupted write, a version skew, or a storage corruption). This is not the same as "no prior locked state exists" and must not be silently treated as authoritative.

When the `prior-state` connector (or any other continuity loader) reads a candidate record, it must validate the record against the `prior_locked_state` shape in `../schemas/normalized-context-schema.md` before use. On validation failure:

1. treat the record as if it were not loaded — do not seed any field of `merged_context` from it, not even partially
2. set `continuity_status: unavailable` (per the vocabulary below)
3. populate `validation_meta.warnings` with an entry that names the specific validation failure (for example, "prior locked state for 2025-01-14 failed schema validation: missing `priorities`")
4. populate `validation_meta.missing_sources[]` with `{ source_family: "prior_state", reason: "invalid_payload" }` per `../schemas/output-schema.md` ("`missing_sources[]`")

The run should then proceed as if prior state were genuinely unavailable. Corrupted prior state is intentionally mapped onto the existing `unavailable` value rather than a distinct `corrupted` / `invalid` vocabulary entry — downstream behavior is the same (do not seed from it, warn the reviewer, do not lock silently), and the specific validation failure is surfaced in `validation_meta.warnings` where it is actionable.

### Validation checklist for loaded prior state

Before declaring a loaded prior-state record valid (and therefore eligible to seed `merged_context`), a runtime must run the following checks in order. Any failure on checks 1–3 is a hard invalidation: treat the record as if it were not loaded, per the rule above, and map to `continuity_status: unavailable`. Checks 4 and 5 are warning-class: the record may still be used, but the failure must be surfaced in `validation_meta.warnings`.

1. **Required-field presence.** `mode`, `report_date`, `priorities`, `locked_at`, `confirmed_by`, and `confirmed_role` must all be present on the record. A record that cannot identify its mode, date, executive content, or confirming principal cannot be authoritative continuity.
2. **Type correctness.** `mode` is a string, `report_date` is an ISO 8601 date, `locked_at` is an ISO 8601 datetime, `priorities` is an array of strings, and — when present — `carryovers`, `dependencies`, `risks`, `unresolved_items`, `notes_for_next_cycle`, and `completed_items` are each arrays of strings.
3. **Enum correctness.** `mode ∈ {sod, eod}` and `confirmed_role ∈ {exec, ea, assistant}` (the `owner_type` vocabulary declared in `../schemas/deployment-config-schema.md` "Participants (canonical shape)").
4. **Referential check (loose).** `confirmed_by` should correspond to a known participant name in the current deployment's `defaults.participants`. If the deployment's participants list has changed since the record was written (e.g., a name was replaced), this check is advisory — warn but do not fail. A hard failure here would invalidate historically-legitimate continuity every time the participant list evolves.
5. **Temporal sanity.** `locked_at` must not be in the future relative to the current runtime clock, and `report_date` must not be after today's run date (in the deployment's saved timezone). A mild violation — for example, a `locked_at` a few seconds ahead due to clock skew — is warning-class; any implementer adding a stricter clock-skew threshold should do so above this floor.

This checklist is the minimum a runtime must implement when loading prior state. Clients may add stricter checks (cryptographic signatures, checksums, version-skew detection, schema-version pinning) but must not skip any of the checks above.

## Continuity status vocabulary

The normalized-context schema's `continuity_status` field has three allowed values. Pick between them using this rule:

- `available` — prior locked state was located and loaded successfully.
- `first_run` — no locked state has ever existed for this deployment (brand-new deployment that has never locked a prior cycle).
- `unavailable` — prior locked state was expected to exist for this deployment but could not be found, could not be loaded, or was loaded but failed schema validation (see "Corrupted prior state rule" above). The SOD and EOD fallback chains above also resolve to `unavailable` if no lock can be found within the bounded look-back window.

Implementers (including the `prior-state` connector and the main `daily-reporting` skill) should reference this definition rather than choosing between `first_run` and `unavailable` by guesswork. The vocabulary is intentionally kept to three values: corrupted prior state, a failed fallback chain, and a straightforwardly-missing lock all map to `unavailable`, and the specific cause is carried in `validation_meta.warnings` where it is actionable for reviewers.

## Safe-posture defaults

The starter configuration template defaults to the safe posture:
- `finalization_mode: "reviewed_locked"`
- `allow_draft_continuity: false`
- Strictest auto-lock validation gate (per `review-and-locking.md`, "Auto-lock validation gate")
- No relaxed filtering overrides in `connector_settings.<connector>.filtering_overrides`

Customers may deviate from any of these defaults; this subsection only defines where a fresh deployment starts. See `review-and-locking.md`, "Deployment posture" for the guardrail rules that apply after a deployment opts into riskier configurations.
