# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

The Atlas Skills Library is a collection of Claude Code plugins published to a marketplace. Each plugin is an independently installable unit that groups one or more skills. Skills are markdown files (`SKILL.md`) with YAML frontmatter that any Claude-compatible agent runtime can load and execute.

There are no build steps, no test runner, and no package manager. All authoring is markdown and JSON.

## Installing and using plugins

```
/plugin marketplace add colin-atlas/atlas-skills-library
/plugin install <plugin-name>@atlas
```

Marketplace source of truth: `.claude-plugin/marketplace.json` at the repo root.

## Architecture: how plugins are structured

Every plugin under `plugins/<plugin-name>/` follows this shape:

```
plugins/<plugin-name>/
├── .claude-plugin/plugin.json     # name, version, description, tier, tags
├── README.md                      # 10-section user-facing doc (see below)
├── skills/
│   └── <skill-name>/
│       ├── SKILL.md               # YAML frontmatter + skill body
│       └── references/            # methodology docs loaded via progressive disclosure
├── implementations/               # optional — platform-specific code (gmail/, notion/, etc.)
├── shared/                        # optional — scripts shared across skill implementations
└── client-profile/                # optional — templates for per-client state files
```

`plugin.json` declares `tier`: either `lightweight` (reviewed + smoke-tested) or `validated` (also passed eval-based review).

## Skill authoring contract

Every `SKILL.md` begins with required YAML frontmatter:

```yaml
---
name: <matches directory name exactly>
description: <trigger-rich — this is what the host agent matches against>
when_to_use: <three or more concrete trigger situations, not abstract theory>
atlas_methodology: opinionated   # or: neutral
---
```

- `opinionated` — skill loads Atlas methodology reference docs. Clients fork the plugin and edit references to customize, not the skill body.
- `neutral` — mechanical task with no Atlas-specific method; no references required.

Skill bodies reference capabilities **abstractly** — "read the file", "list calendar events" — never hardcoding Claude Code tool names like `Read`, `WebFetch`, `Grep`. Required capabilities are listed in the plugin README so any agent runtime can wire them.

## Plugin README structure

Every plugin README must cover exactly these 10 sections in order:

1. What it does
2. Who it's for
3. Required capabilities (abstract — not tool names)
4. Suggested tool wiring (concrete Claude Code tools / MCP servers)
5. Installation
6. First-run setup
7. Skills included
8. Customization notes
9. Atlas methodology
10. Troubleshooting (at least 3 failure modes)

Missing or empty sections block merge. If a section genuinely doesn't apply, say so and why.

## Methodology stances

`methodology-patterns.md` is the authoritative guide. In brief:

- Mark `opinionated` when Atlas has a battle-tested approach meaningfully better than the naive default. The method lives in `references/atlas-<topic>-methodology.md` (or `-framework.md`). Keep the skill body stable; clients override by editing references.
- Mark `neutral` when the work is mechanical, or when the right approach varies too much by client to encode.
- When in doubt, start `neutral` and promote later.

## Adding a new plugin

1. Create `plugins/<plugin-name>/` following the directory shape above.
2. Write `plugin.json` — mirror an existing plugin's manifest structure.
3. Add an entry to `.claude-plugin/marketplace.json`.
4. Author each skill's `SKILL.md` — description must be trigger-rich; `when_to_use` must name at least three concrete triggers.
5. Write the README covering all 10 required sections.
6. Run a real smoke test on a real input (not a toy example) and paste results in the PR.
7. Open a PR using `.github/PULL_REQUEST_TEMPLATE.md`.

## Portability rule

Skills must work outside Claude Code. Any agent runtime should be able to load a `SKILL.md` and wire capabilities to its own tools. This means no Claude Code–specific syntax in skill bodies. The only exception is if a plugin is intentionally CC-only — mark it in `plugin.json` and document it in the README. Full guidance: `docs/using-outside-claude-code.md`.

## PR and review

- One Atlas reviewer required to merge.
- The PR template (`PULL_REQUEST_TEMPLATE.md`) is the checklist — use it.
- Lightweight tier is the default for all new work. Validated tier is a separate promotion PR.
- Smoke test results (real input, real output, honest assessment) are required in the PR description — reviewers will push back on missing or obviously synthetic tests.
