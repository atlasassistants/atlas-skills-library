---
name: prior-state
description: Retrieve the most recent locked reporting state for continuity. Use when daily-reporting needs carryovers, dependencies, risks, unresolved items, or next-cycle notes from the prior locked cycle.
when_to_use: Invoked by `daily-reporting` at the start of every non-first-run SOD or EOD cycle to load continuity from the previous locked state. Returns normalized `prior_locked_state` and a `continuity_status` signal (`available`, `unavailable`, or `first_run`) per the contract in this file. Do NOT use directly by an operator — invoke `daily-reporting` instead.
atlas_methodology: neutral
---

# Prior State Connector

Use this connector when `daily-reporting` needs continuity from the most relevant locked prior report or state.

## Write Contract

| Output | Target | When |
|--------|--------|------|
| Normalized prior locked state | current `daily-reporting` run | whenever the `prior_state` source family is enabled and continuity is available |

**Naming:** return the result as `prior_locked_state`.

**Populates these fields** (per `../../references/schemas/normalized-context-schema.md` §`prior_state`):

| Container | Sub-fields |
|-----------|------------|
| `prior_locked_state` | `mode`, `report_date`, `priorities[]?`, `carryovers[]?`, `dependencies[]?`, `risks[]?`, `unresolved_items[]?`, `notes_for_next_cycle[]?` |

**Skip write when:** if no eligible locked state exists, signal `continuity_status: "unavailable"` or `continuity_status: "first_run"` per the normalized-context schema's enum. See `../../references/policies/continuity-model.md` ("Continuity status vocabulary") for the rule distinguishing the two values. Do not create durable state.

Retrieve the most relevant prior locked state.

## Default windows

See `../../references/policies/continuity-model.md` ("Default Continuity Flow") for the canonical SOD/EOD prior-state preference rule. See `../../references/policies/source-windows.md` for the `prior_state` retrieval window.

### Fallbacks when the default lock is missing (`send_only` interaction)

If the default preferred lock is missing — most commonly because the prior cycle ran under `send_only` and therefore did not lock — follow the fallback chains in `../../references/policies/continuity-model.md`:

- **SOD direction** (no locked EOD for the prior day): fall back to the most recent locked EOD within a bounded look-back window (per deployment, recommended 7 days), then surface `continuity_status: "unavailable"` with a `validation_meta.warnings` entry if no lock is found within the window. See `../../references/policies/continuity-model.md` ("SOD fallback chain").
- **EOD direction** (no current-day locked SOD): fall back to the most recent locked EOD from the prior day so EOD has some anchor, then surface `continuity_status: "unavailable"` with a `validation_meta.warnings` entry if none is available. See `../../references/policies/continuity-model.md` ("EOD fallback chain").

Do not silently reach further back than the configured window, and do not silently use a stale lock from more than one cycle ago without surfacing it.

## Produce

- `prior_locked_state` populated from the most relevant locked prior report per the Default Continuity Flow and fallback chains above
- `continuity_status` signal (`"available"`, `"unavailable"`, or `"first_run"`) per the normalized-context schema's enum

## Rules

- prefer structured state over raw report text
- do not use draft state unless the deployment explicitly allows draft continuity (`allow_draft_continuity = true`). See `../../references/policies/review-and-locking.md` ("Draft state") for the canonical definition of draft state as a persisted continuity class, the rule for when a host runtime writes it, and the read-side rule this connector must follow
- if no locked state exists, signal `continuity_status: "first_run"` or `"unavailable"` per the canonical rule in `../../references/policies/continuity-model.md` ("Continuity status vocabulary")
- if a candidate locked state record is located but fails validation against the `prior_locked_state` schema (malformed, truncated, or otherwise unreadable), do not seed any `merged_context` field from it. Signal `continuity_status: "unavailable"`, populate `validation_meta.warnings` with the specific validation failure, and emit `validation_meta.missing_sources[]` with `{ source_family: "prior_state", reason: "invalid_payload" }`. See `../../references/policies/continuity-model.md` ("Corrupted prior state rule") and `../../references/schemas/output-schema.md` ("`missing_sources[]`").
- retrieval budget: see `../../references/policies/retrieval-budgets.md` ("Default budgets")
- source filtering: see `../../references/policies/source-filtering.md` (this connector's section)
