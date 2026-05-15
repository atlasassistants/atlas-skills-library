# daily-reporting (v0.2.0 update — team-test)

> **This is an update PR, not a standalone plugin.**
> The live plugin lives at `plugins/daily-reporting/`. This `team-test/daily-reporting/` folder contains only the files being added or changed. Reference paths in skill files (e.g. `../../references/...`) resolve correctly in the context of the installed `plugins/daily-reporting/` directory.

## What changed in v0.2.0

- Added `skills/slack/` — a new connector for the `email` source family that reads Slack DMs and @mentions instead of Gmail. Allows deployments to point `source_map.email.provider` at Slack.
- Updated `skills/daily-reporting/SKILL.md` — added `../slack/` to the companion components list, co-located with `../gmail/`.

## Accompanying schema and policy updates (in `plugins/daily-reporting/references/`)

- `references/schemas/deployment-config-schema.md` — added `slack` to the connector names list; added `connector_settings.slack` section documenting `vip_senders`, `monitored_channels`, `high_signal_reactions`, and `resolved_reaction` fields.
- `references/policies/source-filtering.md` — added `### slack` section with noise exclusion rules, signal prioritization, scope rule, and fallback behavior.

## Files in this folder

| File | Change type |
|------|-------------|
| `.claude-plugin/plugin.json` | Updated — version bumped to 0.2.0 |
| `skills/slack/SKILL.md` | New |
| `skills/daily-reporting/SKILL.md` | Updated — companion list only |
