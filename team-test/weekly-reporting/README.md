# weekly-reporting

## 1. What it does

Aggregates locked SOD and EOD daily reports into a weekly rollup summary. Surfaces completed work, recurring blockers, stalled items, carryover patterns, and priority shifts across the ISO week — giving the executive and their EA a retrospective view of how the week actually went.

Triggers on Friday EOD to close the week clean, or Monday SOD to refresh before the new week starts.

## 2. Who it's for

Executive assistants and agent operators who run `daily-reporting` and want a weekly retrospective for their exec. Also useful for executives who want a structured way to review their own workload patterns and prepare for weekly check-ins.

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
/plugin install weekly-reporting@atlas
```

**Dependency:** requires `daily-reporting` to be installed and producing locked reports. `weekly-reporting` reads the files `daily-reporting` writes — it has no value without them.

## 6. First-run setup

No dedicated setup skill. Before first run, confirm:

1. `daily-reporting` is deployed and has produced at least 3 locked EOD reports for the target week.
2. The reports directory path matches the default (`areas/daily-reports/reports/`) or is overridden in your deployment config.
3. Locked files follow the naming convention `sod-YYYY-MM-DD.md` and `eod-YYYY-MM-DD.md`.
4. Notion MCP is connected and authenticated.
5. `notion_parent_page_id` is configured — set it to a shared Reports or Weekly Reviews page accessible to both the exec and their EA.

## 7. Skills included

| Skill | What it does |
|-------|-------------|
| `weekly-reporting` | Aggregates locked daily reports into a weekly rollup |

## 8. Customization notes

- **Reports directory:** override `reports_directory` in your deployment config if your locked files live somewhere other than `areas/daily-reports/reports/`.
- **Trigger timing:** configure a Friday EOD trigger to close the week, or a Monday SOD trigger to use it as a weekly refresher. Both are valid — pick based on how the exec prefers to review.
- **Minimum data threshold:** the skill requires at least 3 locked EOD files per week before surfacing patterns. This is intentional — fewer than 3 is not enough to distinguish signal from noise.

## 9. Atlas methodology

This plugin is `neutral`. The aggregation logic is mechanical — list files, extract fields, group by day. There is no Atlas-opinionated method for "the right way to roll up a week." The output structure and minimum data rule reflect practical defaults, not a proprietary framework.

Clients who want different output fields or aggregation logic can fork the skill and edit directly.

## 10. Troubleshooting

**No files found for the week**
The reports directory path may be wrong, or `daily-reporting` has not yet produced locked reports for the requested week. Check that EOD runs are completing with `finalization_mode: reviewed_locked` or `auto_locked` — `send_only` runs do not write locked state and will not appear here.

**Fewer than 3 locked EODs — partial result returned**
The skill ran but hit the minimum data rule. Either the week is not yet complete, some EOD runs ended in `send_only` mode, or reports were not locked due to review policy. Check `daily-reporting` finalization settings.

**A file was skipped (malformed or unreadable)**
One or more locked report files failed to parse. Open the flagged file and check that `structured_state` is present and well-formed. This can happen if an EOD run was interrupted mid-write.

**Rollup looks thin despite a full week of reports**
The daily reports may have been locked with minimal context. The rollup can only surface what the daily reports captured — if daily context was sparse, the rollup will be sparse. Review the daily-reporting retrieval and source configuration.

**Notion page not created / auth error**
Notion MCP is not connected or the token has expired. Reconnect via your aggregator and confirm the connection is active before re-running. If the page was created but landed in the wrong location, check that `notion_parent_page_id` is set correctly in your deployment config.
