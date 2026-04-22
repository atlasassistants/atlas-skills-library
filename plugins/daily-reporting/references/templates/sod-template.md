# SOD Template

Use this template for a start-of-day report draft.

The report must stay executive-centered. Do not widen into a whole-team status rollup.

## Report Skeleton

```md
Daily Start of Day - {{report_date}}

**Today's shape**
- {{schedule_window_or_focus_block_1}}
- {{schedule_window_or_focus_block_2}}
- {{prep_note_or_timing_constraint}}

**Top priorities**
1. {{priority_1}}
2. {{priority_2}}
3. {{priority_3}}

**Why these matter today**
- {{priority_context_summary}}

**Carryovers / open loops**
- {{carryover_1}}
- {{carryover_2}}

**Blockers and dependencies**
- {{blocker_or_dependency_1}}
- {{blocker_or_dependency_2}}

**Inbox and decision flags**
- {{email_or_external_commitment_1}}
- {{email_or_external_commitment_2}}

**Support work affecting executive execution**
- {{support_work_1}}
- {{support_work_2}}

**Watchouts**
- {{risk_or_constraint_1}}
- {{risk_or_constraint_2}}

**Proposed lock-in**
- {{proposed_focus_statement}}

**Notes for next cycle**
- {{notes_for_next_cycle_1}}
- {{notes_for_next_cycle_2}}
```

## Slot-to-field reference

Every slot above is derived from `merged_context` (see `../schemas/normalized-context-schema.md`). This mapping is mechanical:

| Slot | `merged_context` field |
|------|------------------------|
| `{{report_date}}` | `normalized_context.report_date` |
| `{{schedule_window_or_focus_block_N}}` | `schedule_signals[]` (calendar-derived focus blocks and key events) |
| `{{prep_note_or_timing_constraint}}` | `prep_items[]` (first item, or joined short list) |
| `{{priority_N}}` | `priorities[]` (N-th entry) |
| `{{priority_context_summary}}` | polished one-line summary; see "Polished slots" below |
| `{{carryover_N}}` | `carryovers[]` (N-th entry) |
| `{{blocker_or_dependency_N}}` | `blockers[]` and `dependencies[]` (merged, ordered blockers first) |
| `{{email_or_external_commitment_N}}` | `inbox_signals[]` (N-th entry) |
| `{{support_work_N}}` | `support_work[]` (N-th entry) |
| `{{risk_or_constraint_N}}` | `risks[]` (N-th entry) |
| `{{proposed_focus_statement}}` | `proposed_focus[]` (first item, or polished one-line; see "Polished slots" below) |
| `{{notes_for_next_cycle_N}}` | `notes_for_next_cycle[]` (N-th entry) |

### Polished slots

Two slots in this template accept a bounded "polish" pass when drafting `human_readable_report`:

- `{{priority_context_summary}}` — one-line narrative summary of why the listed priorities matter today, synthesized from `priorities[]`, `schedule_signals[]`, and top `blockers[]`/`dependencies[]`.
- `{{proposed_focus_statement}}` — one-line proposed lock-in, derived from `proposed_focus[]` (or synthesized from `priorities[]` + first `schedule_signals[]` if `proposed_focus[]` is absent).

Polish is only permitted in `human_readable_report`. `structured_state` must copy values verbatim from `merged_context` — see `../schemas/output-schema.md` ("Polish rule").

## Inclusion Rules

- Prefer 3 priorities unless the deployment intentionally configures fewer.
- Keep the opening shape section short and decision-relevant.
- Carryovers should only include items that still matter today.
- Include support-layer work only when it materially affects executive execution.
- If continuity is unavailable, say so explicitly instead of inventing carryovers.
- If a source is manual or unverified, keep that clear in the draft.
