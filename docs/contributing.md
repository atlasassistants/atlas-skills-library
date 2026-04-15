# Contributing to the Atlas Skills Library

This library is where Atlas Assistants publishes the plugins and skills we actually use in production. Contributions are welcome, but the bar is high: everything here should be useful out of the box, readable outside Claude Code, and — where it makes sense — encode an opinionated Atlas way of doing the work.

## 1. Who can contribute

Atlas teammates are the primary contributors. If you work at Atlas and you've built a skill or plugin that's earned its keep on real work, please publish it here.

External contributions are welcome on a case-by-case basis. If you're not on the Atlas team and you'd like to contribute a plugin, **open an issue first** describing what you want to build and why. We'll tell you quickly whether it fits the library's direction before you spend time authoring. Drive-by PRs without a preceding issue will usually be closed.

## 2. Plugin layout

Every plugin follows the same directory shape:

```
plugins/<plugin-name>/
├── .claude-plugin/
│   └── plugin.json
├── README.md
└── skills/
    └── <skill-name>/
        ├── SKILL.md
        └── references/
            └── atlas-<topic>-methodology.md
```

- `.claude-plugin/plugin.json` — plugin manifest. Includes `name`, `description`, `version`, `tier` (`lightweight` or `validated`), and any capability metadata.
- `README.md` — user-facing plugin documentation. Must cover all 10 standard sections (see below).
- `skills/<skill-name>/SKILL.md` — the skill itself, with YAML frontmatter and skill body.
- `skills/<skill-name>/references/` — optional folder of reference docs loaded by the skill via progressive disclosure. Opinionated skills typically ship methodology references here.

`meeting-ops/` is the canonical v1 example. It may not exist at the moment you read this — it's built alongside these docs — but once it lands, use it as the reference shape for your own plugin.

## 3. Authoring flow

Five concrete steps from idea to PR:

1. **Scaffold the plugin.** Run the `plugin-dev:create-plugin` workflow. It sets up `plugin.json`, the skills directory, and the README skeleton.
2. **Author each skill.** Use `skill-creator` to draft SKILL.md. This ensures the description is trigger-rich, the `when_to_use` is specific, and the body follows progressive-disclosure conventions.
3. **Fill out the plugin README.** Use the 10-section template in section 4 below. Do not ship a README with empty sections — if a section genuinely doesn't apply, say so explicitly and why.
4. **Run the lightweight gate locally.** This is not a script — it's a discipline. Have `skill-creator` review each skill, then run a real smoke test on a real input (a real meeting, a real inbox item, whatever the skill operates on). Keep the output so you can paste it into the PR description.
5. **Open a PR.** Use the PR template. Fill in the smoke test results. Request review from one Atlas reviewer.

## 4. Plugin README template

Every plugin README must cover these ten sections, in this order. Each sentence below describes what belongs in that section:

1. **What it does** — one paragraph explaining the problem this plugin solves and the kind of outputs it produces.
2. **Who it's for** — the concrete role or situation where this is valuable (e.g., "operators who run back-to-back external meetings").
3. **Required capabilities** — an abstract list of what the host agent needs to be able to do (read files, search the web, read a calendar, send a message) — not specific tool names.
4. **Suggested tool wiring** — concrete suggestions for which tools to map those capabilities to, in Claude Code and in other environments.
5. **Installation** — the exact marketplace add/install commands, plus any prerequisite steps.
6. **First-run setup** — anything the user has to configure once: environment variables, reference doc edits, calendar permissions, etc.
7. **Skills included** — bullet list of each skill in the plugin with a one-line description and its methodology stance.
8. **Customization notes** — how to fork or override behavior: editing references, adjusting `when_to_use`, changing prompts for a specific client.
9. **Atlas methodology** — short statement of whether this plugin encodes an opinionated Atlas method and, if so, a pointer to the reference docs that define it.
10. **Troubleshooting** — at least three common failure modes with one-line resolutions.

## 5. Skill frontmatter contract

Every SKILL.md begins with YAML frontmatter. Required fields:

```yaml
---
name: meeting-debrief
description: [trigger-rich description per skill-creator standards]
when_to_use: [specific situations that should trigger this skill]
atlas_methodology: opinionated   # or: neutral
---
```

- `name` — must match the skill directory name.
- `description` — trigger-rich, per `skill-creator` standards. This is what the host agent matches against when deciding whether to load the skill.
- `when_to_use` — concrete situations, not abstract theory. If you can't name three specific triggers, the skill is too vague.
- `atlas_methodology` — `opinionated` or `neutral`. See the next section.

## 6. Methodology stance

Every skill declares whether it encodes Atlas's opinionated way of doing something or stays methodology-neutral. Mark a skill `opinionated` when Atlas has a battle-tested approach that's meaningfully better than the naive default. Mark it `neutral` when the work is mechanical or when the right approach varies too much by client context to bake in.

Full guidance lives in [`methodology-patterns.md`](methodology-patterns.md). Read it before you decide.

## 7. Portability rule

Skills in this library must be readable by non–Claude-Code agents. Atlas runs agents outside Claude Code, and other teams may too. That means skill bodies refer to capabilities **abstractly** — "read the file", "search the web", "list calendar events" — rather than hardcoding tool names like `Read`, `Grep`, or `WebFetch`. Required capabilities are listed in the plugin README's "Required capabilities" section so any agent runtime can wire them up.

The only exception is when a plugin is genuinely Claude-Code-only (because it relies on a specific command or hook). In that case, mark the plugin accordingly in `plugin.json` and document it in the README. Full guidance: [`using-outside-claude-code.md`](using-outside-claude-code.md).

## 8. Quality gate (lightweight)

Every plugin and skill ships at the `lightweight` tier by default. The gate is operationally simple:

- `skill-creator` review passes for each skill (description quality, progressive disclosure, structure).
- The author runs a real smoke test on a real input — not a toy example, not a hypothetical.
- The smoke test input and output are documented in the PR description, with an honest assessment of whether the output was good.

No automation enforces this. It's a discipline, and reviewers will push back if the smoke test is missing or obviously synthetic.

## 9. Validated tier

A separate, higher tier called `validated` exists for plugins that have passed eval-based review. Promotion is a distinct PR that adds 3–5 representative eval cases per skill, runs the eval with variance analysis, and flips `"tier": "validated"` in `plugin.json`.

The validated tier is **not required** for merge. It's a trust signal for clients who want extra confidence. Full details: [`validation-badge.md`](validation-badge.md).

## 10. PR checklist

When you open a PR, the template will present this checklist. It's reproduced here so contributors know what's coming:

**Type of change**
- [ ] New plugin
- [ ] New skill in existing plugin
- [ ] Update to existing skill
- [ ] Methodology reference doc change
- [ ] Infrastructure / docs only

**Plugin / skill authoring checklist**
- [ ] Follows standard layout (plugin.json, README with all required sections, SKILL.md per skill)
- [ ] Each skill description is trigger-rich per skill-creator standards
- [ ] Methodology stance declared for each skill (`opinionated` or `neutral`)
- [ ] Required capabilities listed abstractly — no hardcoded tool names in skill bodies
- [ ] Plugin README covers all 10 standard sections
- [ ] Marketplace manifest updated (if new plugin)

**Quality gate**
- [ ] skill-creator review passed
- [ ] Smoke test run on real input — results pasted in PR description

**Tier**
- [ ] `lightweight` (default for new work)
- [ ] `validated` (separate promotion PR — include eval results)

## 11. One-reviewer rule

A PR needs **one Atlas reviewer** to merge. There is no CODEOWNERS file in v1 — any Atlas teammate can approve. Pick someone who has context on the domain your plugin touches, or who you trust to push back honestly. If no one with context is available, pick the reviewer most likely to actually run the smoke test themselves.
