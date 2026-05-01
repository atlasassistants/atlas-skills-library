# Normalized Context Schema

**Schema version:** `schema_version: "1.0"`

## Purpose

This schema defines the clean handoff between source connectors and the main `daily-reporting` skill.

A client or tool may gather data however it wants, but the main skill should work from this shape rather than raw source payloads.

## Top-level shape

```text
normalized_context
- mode
- report_date
- timezone
- continuity_status
- participants?
- source_family_results
- merged_context
```

`participants?`, when present, uses the canonical participant shape declared in `deployment-config-schema.md` ("Participants (canonical shape)"): `{ name, role, owner_type: "exec" | "ea" | "assistant" }`. Do not redeclare.

## Continuity status

Allowed values:
- `available`
- `unavailable`
- `first_run`

See `../policies/continuity-model.md` ("Continuity status vocabulary") for the rule distinguishing when each value applies.

## Source results

`source_family_results` is keyed by the six source keys declared canonically in `deployment-config-schema.md` §Source keys. Each entry is optional (a source that did not contribute may be absent or empty):

```text
source_family_results
- calendar?
- email?
- tasks?
- meetings?
- prior_state?
- manual?
```

Use source keys only.

## Expected result shapes

### `calendar`
Should contribute `calendar_summary`:

```text
calendar_summary
- key_events[]?
- prep_items[]?
- collisions[]?
- focus_windows[]?
- tomorrow_preview[]?
```

### `email`
Should contribute `inbox_flags`:

```text
inbox_flags
- unresolved_threads[]?
- pending_decisions[]?
- urgent_followups[]?
- executive_risks[]?
```

### `tasks`
Should contribute `priority_context` and `task_snapshot`:

```text
priority_context
- current_priorities[]
- blockers[]?
- dependencies[]?
- carryover_candidates[]?
- exec_relevant_support_work[]?

task_snapshot
- active_items[]?
- completed_today[]?
- stalled_items[]?
```

### `meetings`
Should contribute `meeting_note_summaries`:

```text
meeting_note_summaries
- decisions[]?
- followups[]?
- blockers[]?
- dependencies[]?
- owner_actions[]?
```

### `prior_state`
Should contribute `prior_locked_state`:

```text
prior_locked_state
- mode
- report_date
- priorities[]?
- carryovers[]?
- dependencies[]?
- risks[]?
- unresolved_items[]?
- notes_for_next_cycle[]?
```

### `manual`
Should contribute any of:

```text
manual
- freeform_operator_notes[]?
- confirmed_priorities[]?
- manual_overrides?
```

Recommended `manual_overrides` shape:

```text
manual_overrides
- priorities[]?
- carryovers[]?
- blockers[]?
- dependencies[]?
- risks[]?
- notes_for_this_cycle[]?
```

## Merged context

`merged_context` is the executive-centered working set used to draft the report.

```text
merged_context
- priorities[]
- blockers[]?
- dependencies[]?
- carryovers[]?
- completed_items[]?
- unresolved_items[]?
- risks[]?
- schedule_signals[]?
- inbox_signals[]?
- meeting_signals[]?
- support_work[]?
- prep_items[]?
- proposed_focus[]?
- planned_priorities[]?
- stalled_items[]?
- next_cycle_focus[]?
- notes_for_next_cycle[]?
```

### Field derivation

All `merged_context` fields must be derivable from `source_family_results`. Template slots draw from `merged_context` (see each template's "Slot-to-field reference" table). Each rule below is a per-field precedence + dedup formula: it names every contributing source, the order used to resolve conflicts, and how duplicates are collapsed. Unless a rule says otherwise, dedup is by **case-insensitive string equivalence after trimming whitespace**, and when duplicates collapse the higher-precedence entry is kept.

- `priorities[]` — precedence follows the canonical ladder in `../policies/retrieval-rules.md` ("Source Priority"), deduped by case-insensitive string equivalence; ties broken by ladder rank. See "How to decide priorities" below for the schema-level restatement of how carryovers interact.
- `blockers[]?` — precedence: (1) `tasks.priority_context.blockers`, (2) blockers surfaced by `meetings.meeting_note_summaries.blockers`, (3) executive-relevant blockers inferred from `email.inbox_flags.pending_decisions`/`executive_risks`. Union the three after filtering for executive relevance; dedup by string equivalence.
- `dependencies[]?` — precedence: (1) `tasks.priority_context.dependencies`, (2) `meetings.meeting_note_summaries.dependencies`, (3) `prior_state.prior_locked_state.dependencies` that still matter this cycle. Union and dedup by string equivalence.
- `carryovers[]?` — precedence: (1) `prior_state.prior_locked_state.carryovers`, (2) still-relevant items from `tasks.priority_context.carryover_candidates`. Union and dedup by string equivalence. A candidate is "still-relevant" when current-cycle context (tasks, email, meetings) still references the underlying commitment; otherwise drop it.
- `completed_items[]?` — copy verbatim from `tasks.task_snapshot.completed_today` (EOD-primary); dedup by string equivalence.
- `unresolved_items[]?` — precedence: (1) `prior_state.prior_locked_state.unresolved_items` that still matter, (2) still-open items from `tasks.task_snapshot.stalled_items`, (3) `email.inbox_flags.pending_decisions`, (4) `email.inbox_flags.unresolved_threads` that still matter this cycle. Union and dedup by string equivalence; an item already promoted to `blockers[]` or `dependencies[]` is omitted from `unresolved_items[]`.
- `risks[]?` — precedence: (1) `prior_state.prior_locked_state.risks`, (2) `email.inbox_flags.executive_risks`, (3) risks surfaced by `meetings.meeting_note_summaries`. Union and dedup by string equivalence.
- `schedule_signals[]?` — from `calendar.calendar_summary.key_events`, `focus_windows`, `collisions`, and `tomorrow_preview`. Preserve source order; dedup by string equivalence.
- `inbox_signals[]?` — from `email.inbox_flags.urgent_followups` and `email.inbox_flags.pending_decisions`; exclude any item already promoted to `blockers[]` or `unresolved_items[]`. Dedup by string equivalence.
- `meeting_signals[]?` — from `meetings.meeting_note_summaries.decisions` and `meetings.meeting_note_summaries.followups`. Dedup by string equivalence.
- `support_work[]?` — copy verbatim from `tasks.priority_context.exec_relevant_support_work`; dedup by string equivalence.
- `prep_items[]?` — (SOD-primary) copy verbatim from `calendar.calendar_summary.prep_items`; dedup by string equivalence.
- `proposed_focus[]?` — (SOD-primary) synthesized one-line recommendation(s) for the day's focus, derived from `priorities[]`, the first `schedule_signals[]`, and top `blockers[]`/`dependencies[]`. Synthesis: implementation-defined — connectors or the main skill may phrase the recommendation differently provided the inputs listed are the only sources consulted. Template slot `{{proposed_focus_statement}}` reads from this field.
- `planned_priorities[]?` — (EOD-only) copy verbatim from `source_family_results.prior_state.prior_locked_state.priorities` so EOD can compare "what was planned" against "what moved." No dedup or reordering.
- `stalled_items[]?` — (EOD-relevant) copy verbatim from `source_family_results.tasks.task_snapshot.stalled_items`; dedup by string equivalence.
- `next_cycle_focus[]?` — (EOD-only) forward-looking priorities for tomorrow's SOD. Normally copy verbatim from `merged_context.priorities` at EOD finalization; may be a tighter subset if the reviewer trims (reviewer trim wins over the verbatim copy).
- `notes_for_next_cycle[]?` — precedence: (1) `manual.freeform_operator_notes`, (2) `manual.manual_overrides.notes_for_this_cycle` (legacy field name in the manual-override shape), (3) at EOD, still-relevant `prior_state.prior_locked_state.notes_for_next_cycle`. Union and dedup by string equivalence.

### Mode-specific expectations

Every `merged_context` field except `priorities[]` is technically optional in the schema. A valid `merged_context` is not necessarily a *meaningful* one. The following fields SHOULD be populated per `mode` for the run to be substantively useful. A run that omits them is formally valid but substantively thin, and a reviewer should treat the omission as a gap worth flagging.

| Field | SOD | EOD | Both |
|---|---|---|---|
| `priorities[]` | required | required | x |
| `blockers[]?` | SHOULD | SHOULD | x |
| `dependencies[]?` | SHOULD | SHOULD | x |
| `carryovers[]?` | SHOULD | SHOULD | x |
| `risks[]?` | SHOULD | SHOULD | x |
| `schedule_signals[]?` | SHOULD | may | SOD-primary |
| `inbox_signals[]?` | SHOULD | SHOULD | x |
| `meeting_signals[]?` | SHOULD | SHOULD | x |
| `support_work[]?` | may | may | x |
| `prep_items[]?` | SHOULD | not expected | SOD-only |
| `proposed_focus[]?` | SHOULD | not expected | SOD-only |
| `unresolved_items[]?` | SHOULD | SHOULD | x |
| `completed_items[]?` | not expected | SHOULD | EOD-only |
| `stalled_items[]?` | may | SHOULD | EOD-relevant |
| `planned_priorities[]?` | not expected | SHOULD | EOD-only |
| `next_cycle_focus[]?` | not expected | SHOULD | EOD-only |
| `notes_for_next_cycle[]?` | SHOULD | SHOULD | x |

Key:
- `required` — schema-required; a run missing this is invalid.
- `SHOULD` — populate when the underlying source has content; absence when content is available makes the run substantively weaker.
- `may` — optional; populate when relevant, but absence is not a gap.
- `not expected` — the field is outside this mode's scope; leave it empty or absent.

An EOD run that omits `completed_items`, `unresolved_items`, `planned_priorities`, `next_cycle_focus`, and `notes_for_next_cycle` all at once is formally valid but fails the EOD-specific obligations in `../../skills/daily-reporting/SKILL.md` ("Mode-specific obligations") and cannot produce a load-bearing handoff per `../policies/continuity-model.md` ("EOD → next-SOD handoff payload"). An SOD run that omits `prep_items` and `proposed_focus` similarly fails the SOD-specific obligations.

## Merge rules

Per-field precedence and dedup semantics for every `merged_context` field are specified in "Field derivation" above — consult that section for the resolution order used when multiple source families contribute to the same field. This section captures only the cross-field rules that are not already encoded there.

- **Manual overrides.** `manual.manual_overrides.<field>`, when present, replaces the corresponding `merged_context.<field>` after Field derivation resolves it. Override applies only to the fields explicitly named in the override payload; other fields are untouched.
- **Human-confirmed priorities.** `manual.confirmed_priorities` and in-run reviewer corrections enter `priorities[]` at the top of the canonical ladder (see `../policies/retrieval-rules.md` §Source Priority) and therefore win dedup ties against any lower-ranked source.
- **Empty sources.** If a source family returns nothing relevant, leave its contribution empty — do not invent data, and do not substitute content from other source families beyond what the per-field precedence rules already allow.

The `../examples/normalized-context.sod.json` example reflects one valid resolution of the per-field rules; it is illustrative, not normative. Deviations that still satisfy "Field derivation" are conformant.

## How to decide priorities

See the canonical priority ladder in `../policies/retrieval-rules.md` ("Source Priority"). It defines the ordering used when resolving `priorities[]` from `source_family_results`, along with the role that email, meeting, and calendar signals play relative to human-confirmed and task-derived priorities. Do not restate it here.

Schema-specific notes that complement the canonical ladder:
- older carryovers from `prior_state.prior_locked_state.carryovers` and `tasks.priority_context.carryover_candidates` should survive only if current-cycle context still suggests they matter.

Examples:
- an email can surface a blocker or dependency that changes how a current priority is framed
- a meeting can create a new follow-up that becomes a priority if no stronger current priority source contradicts it
- a calendar item can elevate urgency or sequencing, even when it does not create the priority by itself

## Usage rule

If an AI tool can build or validate this context cleanly, it can use the package without depending on one specific client environment.
