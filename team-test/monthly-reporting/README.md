# monthly-reporting

## 1. What it does

Aggregates locked SOD and EOD daily reports across a full calendar month into a retrospective summary. Surfaces completed work, persistent blockers, multi-week carryover patterns, and priority shifts across the month — giving the executive and their EA a longer-arc view that a weekly rollup cannot provide.

Triggers on the first working day of the month, after the prior month's last EOD has locked.

## 2. Who it's for

Executive assistants and agent operators who run `daily-reporting` and want a monthly retrospective for their exec. Useful for executives who want to review goal progress, prepare for monthly check-ins, or identify patterns that only emerge at a month-level view.

## 3. Required capabilities (abstract)

- Read files from a local directory
- List files in a directory by name pattern
- Parse structured content from markdown files
- Create a structured document in an external system

## 4. Suggested tool wiring

| Capability | Common options |
|---|---|
| File reading | Filesystem MCP, or any agent runtime's local file-read capability |
| Directory listing by pattern | Filesystem MCP, shell execution, or a built-in glob capability |
| Notion page creation | Notion MCP (`notion-create-pages`) |

Notion MCP is required for delivery. The skill reads from local locked report files and writes the rollup to Notion.

## 5. Installation

```
/plugin install monthly-reporting@atlas
```

**Dependency:** requires `daily-reporting` to be installed and producing locked reports. `monthly-reporting` reads the files `daily-reporting` writes — it has no value without them.

This plugin is independent of `weekly-reporting`. Both read directly from locked daily files — do not chain them.

## 6. First-run setup

No dedicated setup skill. Before first run, confirm:

1. `daily-reporting` is deployed and has produced locked EOD reports for the target month (at least 10 required).
2. The reports directory path matches the default (`areas/daily-reports/reports/`) or is overridden in your deployment config.
3. Locked files follow the naming convention `sod-YYYY-MM-DD.md` and `eod-YYYY-MM-DD.md`.
4. Notion MCP is connected and authenticated.
5. `notion_parent_page_id` is configured — set it to a shared Monthly Reviews or Reports page accessible to both the exec and their EA.

## 7. Skills included

| Skill | What it does |
|-------|-------------|
| `monthly-reporting` | Aggregates locked daily reports into a monthly rollup |

## 8. Customization notes

- **Reports directory:** override `reports_directory` in your deployment config if your locked files live somewhere other than `areas/daily-reports/reports/`.
- **Trigger timing:** configure a first-working-day-of-month trigger. The prior month's last EOD must be locked before running.
- **Minimum data threshold:** the skill requires at least 10 locked EOD files before surfacing patterns. A full working month has approximately 20 — 10 is the floor for meaningful signal. Adjust if your exec's schedule typically produces fewer locked reports.
- **Completed items grouping:** completed items are grouped by week for readability at month scale. This is the main structural difference from the weekly rollup, which groups by day.

## 9. Atlas methodology

This plugin is `neutral`. The aggregation logic is mechanical — list files, extract fields, group by week. There is no Atlas-opinionated method for "the right way to roll up a month." The output structure and minimum data rule reflect practical defaults, not a proprietary framework.

Clients who want different output fields or aggregation logic can fork the skill and edit directly.

## 10. Troubleshooting

**No files found for the month**
The reports directory path may be wrong, or `daily-reporting` has not produced locked reports for the requested month. Check that EOD runs are completing with `finalization_mode: reviewed_locked` or `auto_locked` — `send_only` runs do not write locked state and will not appear here.

**Fewer than 10 locked EODs — partial result returned**
The skill ran but hit the minimum data rule. Some EOD runs may have ended in `send_only` mode, or reports were not locked due to review policy. Check `daily-reporting` finalization settings. If the exec had a lighter month (travel, holidays), the threshold can be lowered in a deployment fork.

**A file was skipped (malformed or unreadable)**
One or more locked report files failed to parse. Open the flagged file and check that `structured_state` is present and well-formed. This can happen if an EOD run was interrupted mid-write.

**Rollup looks thin despite a full month of reports**
The daily reports may have been locked with minimal context. The rollup can only surface what the daily reports captured — if daily context was sparse across the month, the rollup will reflect that. Review the daily-reporting retrieval and source configuration.

**Notion page not created / auth error**
Notion MCP is not connected or the token has expired. Reconnect via your aggregator and confirm the connection is active before re-running. If the page was created but landed in the wrong location, check that `notion_parent_page_id` is set correctly in your deployment config.
