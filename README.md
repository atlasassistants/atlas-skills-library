# Atlas Skills Library

A collection of Claude Code plugins and portable skills built and battle-tested by Atlas Assistants. Install what you need, customize for your workflow, and let your agents do more out of the box.

## What's inside

Plugins live under `plugins/`. Each one is independently installable via the Claude Code marketplace flow. See each plugin's own README for details.

**v1 plugins:**
- [`meeting-ops`](plugins/meeting-ops/) — meeting prep (internal and external), calendar scanning, and structured debriefs

## Installing a plugin

```
/plugin marketplace add colin-atlas/atlas-skills-library
/plugin install <plugin-name>@atlas
```

See [`docs/installing-a-plugin.md`](docs/installing-a-plugin.md) for the full guide, including how to use these skills outside Claude Code.

## Contributing

Atlas teammates (and friends) can propose new plugins and skills. Read [`docs/contributing.md`](docs/contributing.md) before opening a PR.

## Methodology

Many of these plugins encode Atlas's opinionated way of doing things — it's a differentiator, not a bug. See [`docs/methodology-patterns.md`](docs/methodology-patterns.md) for how opinionated vs neutral skills are structured.

## Quality tiers

Plugins and skills ship at one of two tiers:
- **lightweight** — reviewed + smoke-tested
- **validated** — also passed eval-based review

See [`docs/validation-badge.md`](docs/validation-badge.md).
