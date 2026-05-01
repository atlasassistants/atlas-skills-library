# EOD Template

Use this template for an end-of-day report draft.

The report must stay executive-centered. Do not widen into a whole-team retrospective.

## Report Skeleton

```md
Daily End of Day - {{report_date}}

**Day verdict**
- {{day_verdict_summary}}

**What moved today**
- {{completed_or_progress_item_1}}
- {{completed_or_progress_item_2}}
- {{completed_or_progress_item_3}}

**What did not move**
- {{stalled_item_1}}
- {{stalled_item_2}}

**Key blockers and dependencies**
- {{blocker_or_dependency_1}}
- {{blocker_or_dependency_2}}

**Decisions, commitments, and inbox signals**
- {{decision_or_external_commitment_1}}
- {{decision_or_external_commitment_2}}

**Carry forward into next cycle**
- {{carryforward_1}}
- {{carryforward_2}}
- {{carryforward_3}}

**Support work affecting executive execution**
- {{support_work_1}}
- {{support_work_2}}

**Risks and watchouts**
- {{risk_1}}
- {{risk_2}}

**Next cycle focus**
- {{next_cycle_focus_1}}
- {{next_cycle_focus_2}}

**Notes for next cycle**
- {{notes_for_next_cycle_1}}
- {{notes_for_next_cycle_2}}
```

## Slot-to-field reference

Every slot above is derived from `merged_context` (see `../schemas/normalized-context-schema.md`). This mapping is mechanical:

| Slot | `merged_context` field |
|------|------------------------|
| `{{report_date}}` | `normalized_context.report_date` |
| `{{day_verdict_summary}}` | polished one-line verdict; see "Polished slots" below |
| `{{completed_or_progress_item_N}}` | `completed_items[]` (N-th entry) |
| `{{stalled_item_N}}` | `stalled_items[]` (N-th entry) |
| `{{blocker_or_dependency_N}}` | `blockers[]` and `dependencies[]` (merged, ordered blockers first) |
| `{{decision_or_external_commitment_N}}` | `meeting_signals[]` and `inbox_signals[]` (decisions first) |
| `{{carryforward_N}}` | `carryovers[]` (N-th entry) |
| `{{support_work_N}}` | `support_work[]` (N-th entry) |
| `{{risk_N}}` | `risks[]` (N-th entry) |
| `{{next_cycle_focus_N}}` | `next_cycle_focus[]` (N-th entry; EOD populates this from `merged_context.priorities` unless the reviewer trims) |
| `{{notes_for_next_cycle_N}}` | `notes_for_next_cycle[]` (N-th entry) |

Implementation note for EOD-specific comparison: `merged_context.planned_priorities[]?` carries forward what SOD locked in (copied verbatim from `source_family_results.prior_state.prior_locked_state.priorities`). Use it inside `{{day_verdict_summary}}` or as evidence for what moved vs. stalled; it is not itself a rendered slot.

### Polished slots

One slot in this template accepts a bounded "polish" pass when drafting `human_readable_report`:

- `{{day_verdict_summary}}` — one-line narrative verdict for the day, synthesized from `completed_items[]`, `stalled_items[]`, `planned_priorities[]`, and `carryovers[]`.

Polish is only permitted in `human_readable_report`. `structured_state` must copy values verbatim from `merged_context` — see `../schemas/output-schema.md` ("Polish rule").

## Inclusion Rules

- Distinguish completed work from partial movement.
- Keep the day verdict to one tight sentence or bullet.
- Carry forward only unresolved items that still matter to executive execution.
- Include next-cycle focus only when it materially sharpens tomorrow's starting point.
- Do not create a separate meetings section unless meeting outcomes materially changed priorities, blockers, or carryforwards.
- If the report is `send_only`, do not treat it as continuity unless saved policy explicitly allows it.
