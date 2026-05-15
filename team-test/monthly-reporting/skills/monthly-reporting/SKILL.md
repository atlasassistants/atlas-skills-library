---
name: monthly-reporting
description: Generate a monthly rollup report for an executive by aggregating locked SOD and EOD daily reports across the current or last calendar month. Use when an operator or exec needs a retrospective summary of the month — persistent blockers, what moved vs. stalled over a longer arc, goal progress, and how priorities shifted across the full period.
when_to_use: User says "monthly report", "monthly rollup", "monthly summary", "how did this month go", "summarize the month", "what did we complete this month", "end of month report", "monthly review", "month in review", "show me patterns this month". Also runs on a scheduled first-working-day-of-month trigger if configured.
atlas_methodology: neutral
---

# Monthly Reporting

Aggregate locked daily reports into a month-level retrospective summary
for the executive.

This skill is a companion to `daily-reporting`. It reads what has already
been locked across the calendar month and surfaces patterns that are only
visible at a longer time horizon — persistent blockers, multi-week
carryovers, and goal-level progress that a weekly view would miss.

## Scope

This skill answers:
- what the executive completed across the month
- what blocked progress persistently — not just this week, but across weeks
- which items carried forward repeatedly without resolution
- how priorities shifted across the month's arc
- what support-layer work had sustained impact on execution
- what month-level patterns are worth surfacing for the exec's review

It does not:
- re-run or re-generate daily or weekly reports
- pull live data from any connector
- replace the weekly rollup as the week-close mechanism

## Input

Read locked report files from the configured reports directory
(default: `areas/daily-reports/reports/`).

Include all files matching the naming pattern `sod-YYYY-MM-DD.md` and
`eod-YYYY-MM-DD.md` within the current or last calendar month.

**Minimum data rule:** if fewer than 10 locked EOD files exist within the
target month, do not fabricate trends. Draft the narrowest honest summary
possible and flag the gap explicitly: state how many locked EODs were found
and that month-level patterns require more data.

If no locked files exist for the month, return a blocked status with a
clear explanation.

## Produce

- `completed_items_rollup` — all completed items across the month, grouped
  by week
- `stalled_items_rollup` — items that appeared as stalled across multiple
  weeks
- `recurring_blockers` — blockers that appeared across more than one week
- `carryover_log` — items that carried forward across days or weeks without
  resolution, with a count of how many times each appeared
- `priority_shifts` — priorities that were replaced, dropped, or added
  during the month, with approximate timing
- `support_work_summary` — support-layer work that had sustained impact on
  executive execution across the month
- `narrative_summary` — a short synthesized narrative of the month (one of
  the narrative slots that may be polished — see output rules below)

## Output rules

- List-typed fields (`completed_items_rollup`, `stalled_items_rollup`,
  `persistent_blockers`, `carryover_log`, `priority_shifts`,
  `support_work_summary`) must be verbatim aggregations of the source
  report content. Do not rephrase or editorialize.
- `narrative_summary` is the only field that may be synthesized. Keep it
  to 4–6 sentences. Surface the most important pattern or signal from the
  month — not a recap of every item, but the signal that matters at a
  month-level view.
- Do not invent completed work, blockers, or priorities not present in the
  source files.

## Write Contract

| Output | Target | When |
|--------|--------|------|
| Monthly rollup report | configured rollup delivery destination | after aggregation is complete and minimum data rule is met |

**Naming:** return the result as `rollup_report`. When delivered to a
document system, the title should follow the pattern
`Monthly Rollup — [Month YYYY]` (e.g. `Monthly Rollup — May 2026`).

**Skip write when:** minimum data rule is not met, or no locked files exist
for the month. Surface the reason instead.

## Timing

Trigger on the first working day of the month, after the prior month's
last EOD has locked. This gives a complete picture of the prior month
before the new month's daily reporting begins.

## Workflow

1. Resolve the target date range — current or last calendar month
   (first day through last day).
2. List all locked report files in the configured reports directory that
   fall within the date range.
3. Check the minimum data rule — at least 10 locked EOD files required.
   If not met, return a partial result with a warning.
4. Read each file and extract the relevant fields from `structured_state`.
5. Aggregate into the produce fields above, grouping completed items by
   week for readability.
6. Synthesize `narrative_summary` from the aggregated data.
7. Emit `rollup_report`.
8. Deliver to the configured rollup delivery destination. Page body should
   follow this section order: Summary (narrative), Completed (by week),
   Stalled, Recurring Blockers, Carryover Log, Priority Shifts, Support
   Work, Skipped Files (if any). Include the month, date range, and
   locked-EOD count in the page header.

## If data is missing or malformed

- If a file exists but cannot be read or fails to parse, skip it, add it
  to a `skipped_files` list in the output, and continue with remaining files.
- If skipped files reduce the available EOD count below 10, apply the
  minimum data rule and flag it.
- Do not halt the entire run because one file is malformed.

## Configuration

Defaults:
- `reports_directory`: `areas/daily-reports/reports/`
- `notion_parent_page_id`: workspace-level (no parent) if not set

Operators should configure `notion_parent_page_id` during setup to ensure
rollups land in the right place for the exec and EA to find them. A shared
Monthly Reviews or Reports page is the recommended parent.

## Dependencies

This plugin requires `daily-reporting` to be installed. The locked report
files this skill reads are produced by `daily-reporting`.

This plugin is independent of `weekly-reporting`. Both read directly from
locked daily files — monthly does not depend on weekly rollup output.

## References

- `../../../../plugins/daily-reporting/references/schemas/output-schema.md`
  (shape of the locked structured_state this skill reads)
- `../../../../plugins/daily-reporting/references/policies/continuity-model.md`
  (what gets written to locked state and when)
