# compounding-learning

> Capture skills, insights, and patterns during work — never solve the same problem twice.
> v0.1.0 — `lightweight` tier.

## What it does

Turns every working session into compounding knowledge:

- **Captures skills** built during sessions — if something took time to figure out, it gets extracted to a reusable file so future sessions (and other agents) can skip the learning curve entirely.
- **Closes threads properly** — before any thread or session wraps up, runs the Compound Test and gates closure on capture. If a fresh session started this same task tomorrow, it should be faster because of what was logged today.
- **Promotes corrections immediately** — every correction gets logged to `corrections.md` AND promoted to an `AGENTS.md` rule so the next session never repeats the same mistake. Always both destinations. No exceptions.

The result: every session makes the next session faster. Knowledge compounds across sessions, agents, and teammates.

## Who it's for

Agents and operators running high-frequency, high-variety work where the same problems keep resurfacing. Atlas built this for EA-style workflows where sessions are independent contexts — if something isn't written down before the session ends, the next session starts from zero. This plugin enforces the discipline to prevent that.

## Required capabilities

The plugin's skills depend on these capabilities. Each is named abstractly — wire it up to whatever tools the host agent has access to.

- **Knowledge base write** — create and update files in `brain/knowledge/skills/`, `brain/knowledge/lessons-learned.md`
- **Memory write** — create and update files in `memory/patterns.md`, `memory/decisions.md`, `memory/corrections.md`, `memory/people/`
- **Rules file write** — update the agent's `AGENTS.md` (or equivalent rules file) when corrections are promoted

## Suggested tool wiring

| Capability | Common options |
|---|---|
| Knowledge base write | Filesystem MCP, Notion MCP, Obsidian vault |
| Memory write | Filesystem MCP, Mem0, any key-value store |
| Rules file write | Filesystem MCP |

These are examples, not requirements. Pick what the agent already has.

## Installation

```
/plugin install compounding-learning@atlas
```

No first-run setup required. The plugin works with any file paths — configure them in each skill if your knowledge base uses a different directory structure than the Atlas defaults.

## Skills included

- **`session-capture`** — *opinionated.* Fires mid-session when something reusable is built or when a concept required >2 minutes of back-and-forth. Classifies the capture type (skill, insight, or pattern) and routes it to the right destination immediately.
- **`thread-close`** — *opinionated.* Runs the Thread / Session Close Gate before wrapping up any thread or session. Asks the compound test question, extracts any remaining learnings, and gates closure until capture is done.
- **`correction-promote`** — *opinionated.* When a correction or behavioral feedback is received, logs it to `corrections.md` and promotes a rule to `AGENTS.md`. Always both destinations, every time.

## Customization notes

Common things clients change:

- **File paths.** Defaults are `brain/knowledge/skills/`, `brain/knowledge/lessons-learned.md`, `memory/patterns.md`, `memory/decisions.md`, `memory/corrections.md`. Override to match your vault structure.
- **Skill template.** The default skill extraction template is in `references/atlas-compounding-learning-methodology.md`. Edit it to match how your team formats skills.
- **The >2 minute insight threshold.** The default trigger for logging an insight is when a back-and-forth exchange takes more than 2 minutes to resolve. Adjust in `session-capture`.
- **Rules file location.** Default is `AGENTS.md` at the root of the agent's context. If your agent uses a different rules file path or name, update `correction-promote`.
- **Compound test threshold.** Default is >10 minutes saved. Adjust to match your team's cadence in `thread-close`.

When customizing, edit the `SKILL.md` and reference files in your installed copy or fork. The plugin is meant to be a starting point you adapt — not a black box.

## Atlas methodology

This plugin encodes the Atlas Compounding Learning Protocol — the discipline that turns one-time solutions into institutional knowledge. Core principles:

- **First time costs 10–60 minutes. Second time costs zero.** This only holds if the first session actually captures what it learned.
- **Log during the session, not after.** End-of-session capture misses 70%+ of insights because the context is gone.
- **Every correction needs two destinations.** `corrections.md` is the detailed record. `AGENTS.md` is the rule that prevents recurrence. If a correction only lives in `corrections.md`, the next session won't load it and the same mistake will happen again.

The full protocol lives at [`references/atlas-compounding-learning-methodology.md`](references/atlas-compounding-learning-methodology.md).

## Troubleshooting

**`session-capture` isn't firing at the right moment.** The skill triggers on specific signals (something reusable was built, or a back-and-forth took >2 minutes). If those signals are present but the skill isn't triggering, check the `when_to_use` frontmatter and broaden the trigger phrases.

**`thread-close` is getting skipped at session end.** The close gate depends on detecting that a thread is winding down. If your phrasing doesn't match (e.g., you use "all done" instead of "wrap up"), edit `when_to_use` to include your patterns.

**`correction-promote` logged to `corrections.md` but didn't update `AGENTS.md`.** Check that the rules file path is correct and the agent has write access. The rule: both destinations, every time, no exceptions.

**Captured files are landing in the wrong location.** The default paths assume an Atlas-standard vault structure. Override the file paths in each skill's configuration to match your knowledge base layout.

**The same problem keeps surfacing despite captures.** Check that `AGENTS.md` is actually loaded at session start. Skills and patterns in `brain/knowledge/` and `memory/` only help if the agent reads them — confirm the load path is in your agent's context configuration.
