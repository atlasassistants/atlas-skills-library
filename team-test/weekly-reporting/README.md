# weekly-reporting

## 1. What it does

Aggregates locked SOD and EOD daily reports into a weekly or monthly rollup summary. Surfaces completed work, recurring blockers, stalled items, carryover patterns, and priority shifts across the period — giving the executive and their EA a retrospective view of how the week or month actually went.

## 2. Who it's for

Executive assistants and agent operators who run `daily-reporting` and want a periodic retrospective for their exec. Also useful for executives who want a structured way to review their own workload patterns, track goal progress, and prepare for weekly reviews or monthly check-ins.

## 3. Required capabilities (abstract)

- Read files from a local directory
- List files in a directory by name pattern
- Parse structured content from markdown files
- Create a structured document in an external system

## 4. Suggested tool wiring

| Capability | Claude Code tool |
|------------|-----------------|
| Read report files | `Read` |
| List reports directory | `Bash` (find / ls) or `Glob` |
| Create Notion page | Notion MCP (`notion-create-pages`) |

Notion MCP is required for delivery. The skill reads from local locked report files and writes the rollup to Notion.

## 5. Installation

```
/plugin install weekly-reporting@atlas
```

**Dependency:** requires `daily-reporting` to be installed and producing locked reports. `weekly-reporting` reads the files `daily-reporting` writes — it has no value without them.

## 6. First-run setup

No dedicated setup skill. Before first run, confirm:

1. `daily-reporting` is deployed and has produced at least 3 locked EOD reports.
2. The reports directory path matches the default (`areas/daily-reports/reports/`) or is overridden in your deployment config.
3. Locked files follow the naming convention `sod-YYYY-MM-DD.md` and `eod-YYYY-MM-DD.md`.
4. Notion MCP is connected and authenticated.
5. `notion_parent_page_id` is configured — set it to a shared Reports or Weekly Reviews page accessible to both the exec and their EA.

## 7. Skills included

| Skill | What it does |
|-------|-------------|
| `weekly-reporting` | Aggregates locked daily reports into weekly or monthly rollup |

## 8. Customization notes

- **Reports directory:** override `reports_directory` in your deployment config if your locked files live somewhere other than `areas/daily-reports/reports/`.
- **Minimum data threshold:** the skill requires at least 3 locked EOD files per window before surfacing patterns. This is intentional — fewer than 3 is not enough to distinguish signal from noise.
- **Scheduled runs:** configure a weekly Friday EOD trigger or a monthly first-working-day trigger to run this automatically after the last daily report of the period locks.

## 9. Atlas methodology

This plugin is `opinionated`. The aggregation logic, minimum data rules, output field definitions, and the distinction between verbatim fields and the single synthesized narrative slot encode Atlas's approach to executive retrospectives. Clients who want different rollup logic should fork the skill and edit the references, not the skill body.

The core principle: a rollup report is only as trustworthy as the daily reports it reads. This skill never invents data — it surfaces what was already locked.

## 10. Troubleshooting

**No files found for the period**
The reports directory path may be wrong, or `daily-reporting` has not yet produced locked reports for the requested window. Check that EOD runs are completing with `finalization_mode: reviewed_locked` or `auto_locked` — `send_only` runs do not write locked state and will not appear here.

**Fewer than 3 locked EODs — partial result returned**
The skill ran but hit the minimum data rule. Either the window is too early in the week/month, some EOD runs ended in `send_only` mode, or reports were not locked due to review policy. Check `daily-reporting` finalization settings.

**A file was skipped (malformed or unreadable)**
One or more locked report files failed to parse. Open the flagged file and check that `structured_state` is present and well-formed. This can happen if an EOD run was interrupted mid-write.

**Rollup looks thin despite a full week of reports**
The daily reports may have been locked with minimal context (thin `structured_state`). The rollup can only surface what the daily reports captured — if daily context was sparse, the rollup will be sparse. Review the daily-reporting retrieval and source configuration.

**Notion page not created / auth error**
Notion MCP is not connected or the token has expired. Reconnect via your aggregator and confirm the connection is active before re-running. If the page was created but landed in the wrong location, check that `notion_parent_page_id` is set correctly in your deployment config.
