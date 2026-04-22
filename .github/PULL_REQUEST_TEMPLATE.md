## What this PR does

<!-- One-paragraph summary. -->

## Type of change

- [ ] New plugin
- [ ] New skill in existing plugin
- [ ] Update to existing skill
- [ ] Methodology reference doc change
- [ ] Infrastructure / docs only

## Plugin / skill authoring checklist

- [ ] Follows standard layout (plugin.json, README with all required sections, SKILL.md per skill)
- [ ] Each skill description is trigger-rich per skill-creator standards
- [ ] Methodology stance declared for each skill (`opinionated` or `neutral`)
- [ ] Required capabilities listed abstractly — no hardcoded tool names in skill bodies
- [ ] Plugin README covers all 10 standard sections
- [ ] Marketplace manifest updated (if new plugin)

## Self-test gate

- [ ] skill-creator review passed
- [ ] Smoke test run on real input — paste results below

### Smoke test results

<!-- What input you ran it on, what output you got, whether it was good. -->

## Target phase

- [ ] Merge to `team-test/` (new plugin or update to a team-test plugin)
- [ ] Promotion to `plugins/` (Team Test → Live — include teammate validation evidence below)

### Teammate validation (promotion PRs only)

<!-- Who used the plugin, on what real work, and whether the outcome was good. -->

## Reviewer

Requires one Atlas reviewer.
