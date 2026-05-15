---
name: weekly-reporting
description: Generate a weekly or monthly rollup report for an executive by aggregating locked SOD and EOD daily reports. Use when an operator or exec needs a retrospective summary of the week or month — what was completed, what stalled, what kept recurring, and how priorities shifted over time.
when_to_use: User says "weekly report", "weekly rollup", "weekly summary", "monthly report", "monthly rollup", "how did this week go", "how did this month go", "summarize the week", "summarize the month", "what did we complete this week", "what kept blocking us", "show me patterns". Also runs on a scheduled weekly or monthly trigger if configured.
atlas_methodology: neutral
---

# Weekly Reporting

Aggregate locked daily reports into a retrospective summary for the executive.

This skill is a companion to `daily-reporting`. It does not generate new
daily reports — it reads what has already been locked and finds the patterns.

## Modes

- `weekly` — aggregates locked reports across the current or last ISO week
  (Monday through Friday, 5 working days)
- `monthly` — aggregates locked reports across the current or last calendar
  month

The operator specifies the mode at runtime. If no mode is given, default
to `weekly`.

## Scope

This skill answers:
- what the executive completed across the period
- what stalled or recurred as a blocker
- how often items carried forward without resolution
- how priorities shifted day over day
- what support-layer work affected execution
- what patterns in the exec's week or month are worth surfacing

It does not:
- re-run or re-generate daily reports
- pull live data from any connector
- replace the EOD report as a continuity mechanism

## Input

Read locked report files from the configured reports directory
(default: `areas/daily-reports/reports/`).

Include all files matching the naming pattern `sod-YYYY-MM-DD.md` and
`eod-YYYY-MM-DD.md` within the target date range.

**Minimum data rule:** if fewer than 3 locked EOD files exist within the
target window, do not fabricate trends. Draft the narrowest honest summary
possible and flag the gap explicitly: state how many locked EODs were found
and that patterns require more data.

If no locked files exist for the period, return a blocked status with a
clear explanation.

## Produce

- `completed_items_rollup` — all completed items across the period, grouped
  by day
- `stalled_items_rollup` — items that appeared as stalled across multiple
  days
- `recurring_blockers` — blockers that appeared in more than one cycle
- `carryover_log` — items that carried forward from one day to the next
  without resolution, with a count of how many times each appeared
- `priority_shifts` — priorities that were replaced, dropped, or added
  mid-week
- `support_work_summary` — support-layer work that materially affected
  executive execution across the period
- `narrative_summary` — a short synthesized narrative of the period (one of
  the narrative slots that may be polished — see output rules below)

## Output rules

- List-typed fields (`completed_items_rollup`, `stalled_items_rollup`,
  `recurring_blockers`, `carryover_log`, `priority_shifts`,
  `support_work_summary`) must be verbatim aggregations of the source
  report content. Do not rephrase or editorialize.
- `narrative_summary` is the only field that may be synthesized. Keep it
  to 3–5 sentences. Surface the most important pattern or signal from the
  period — do not recap every item.
- Do not invent completed work, blockers, or priorities not present in the
  source files.

## Write Contract

| Output | Target | When |
|--------|--------|------|
| Weekly or monthly rollup report | configured rollup delivery destination | after aggregation is complete and minimum data rule is met |

**Naming:** return the result as `rollup_report`. When delivered to a
document system, the title should follow the pattern
`Weekly Rollup — [Month DD–DD, YYYY]` or `Monthly Rollup — [Month YYYY]`.

**Skip write when:** minimum data rule is not met, or no locked files exist
for the period. Surface the reason instead.

## Workflow

1. Resolve the target date range from the requested mode and report date.
2. List all locked report files in the configured reports directory that
   fall within the date range.
3. Check the minimum data rule — at least 3 locked EOD files required.
   If not met, return a partial result with a warning.
4. Read each file and extract the relevant fields from `structured_state`.
5. Aggregate into the produce fields above.
6. Synthesize `narrative_summary` from the aggregated data.
7. Emit `rollup_report`.
8. Deliver to the configured rollup delivery destination. Page body should
   follow this section order: Summary (narrative), Completed, Stalled,
   Recurring Blockers, Carryover Log, Priority Shifts, Support Work,
   Skipped Files (if any). Include the date range, mode, and locked-EOD
   count in the page header.

## If data is missing or malformed

- If a file exists but cannot be read or fails to parse, skip it, add it
  to a `skipped_files` list in the output, and continue with remaining files.
- If skipped files reduce the available EOD count below 3, apply the
  minimum data rule and flag it.
- Do not halt the entire run because one file is malformed.

## Configuration

The reports directory path and Notion destination are deployment-specific.

Defaults:
- `reports_directory`: `areas/daily-reports/reports/`
- `notion_parent_page_id`: workspace-level (no parent) if not set

Operators should configure `notion_parent_page_id` during setup to ensure
rollups land in the right place for the exec and EA to find them. A shared
Reports or Weekly Reviews page is the recommended parent.

## Dependencies

This plugin requires `daily-reporting` to be installed. The locked report
files this skill reads are produced by `daily-reporting`.

## References

- `../../../../plugins/daily-reporting/references/schemas/output-schema.md`
  (shape of the locked structured_state this skill reads)
- `../../../../plugins/daily-reporting/references/policies/continuity-model.md`
  (what gets written to locked state and when)
