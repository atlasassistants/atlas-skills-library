# Design: README Overhaul — Installation Guide + Skills Directory

**Date:** 2026-05-10
**Status:** Approved

---

## Goal

Rewrite the root `README.md` to serve executives and EAs as the primary audience. Two jobs:

1. Teach users how to install plugins across multiple paths, with clear pros/cons and a Co-work vs. Claude Code capability explanation.
2. Replace the flat plugin list with a rich skills directory organized by jobs-to-be-done, so users can find the right plugin for their situation without reading every README.

---

## Audience

Executives and EAs who want to install and use plugins. Not contributors, not developers (those are secondary). Tone: plain language, step-by-step, no jargon.

---

## Structure: Option B (README as hub + linked docs)

The root README is a strong landing page. Deep per-skill detail stays in each plugin's own README. The root README gets someone from "I found this repo" to "I'm running my first skill" fast.

---

## Section 1 — Header & Intro

- Lead with Atlas attribution + exec value proposition
- Format: "Built and battle-tested by Atlas Assistants — [value prop about saving exec hours]"
- Keep it to 2–3 sentences max

---

## Section 2 — How to Install

Four installation paths. Each gets:
- A clear name
- Step-by-step instructions (numbered, plain language)
- Pros/cons
- A "Best for" line

### Path 1: Claude Code or Co-work (same setup)

**Steps:**
1. Open Claude Code or Claude.ai
2. Click the **+** button
3. Go to **Plugins**
4. Click **Add Marketplace**
5. Paste: `colin-atlas/atlas-skills-library`
6. Browse available plugins and click **Install** next to the one you want

**Callout — Co-work vs. Claude Code:**
The setup is identical. The difference is what each can run:
- **Co-work** works when a skill only needs connectors (Google Calendar, Gmail, Slack, etc.). If the connectors are present and wired, the skill runs.
- **Claude Code** is required when a skill needs scripts, file system access, or capabilities beyond what connectors provide.
The Skills Directory below shows which options are compatible with each plugin.

**Best for:** Most users — EAs and execs who already have Claude and want the fastest path to running a skill.

**Pros:** Easiest setup, automatic updates, marketplace browser for discovery
**Cons:** Co-work has capability limits; some skills require Claude Code

---

### Path 2: Clone the Repo

**Steps:**
1. Install [Git](https://git-scm.com/) if you don't have it
2. Run: `git clone https://github.com/colin-atlas/atlas-skills-library`
3. In Claude Code, install a plugin by local path: `/plugin install ./plugins/<plugin-name>`

**Best for:** Teams who want to customize skills, fork for client-specific versions, or pin to a specific version.

**Pros:** Full control, can edit skill files, can customize methodology references
**Cons:** Manual updates, requires Git familiarity, not available in Co-work

---

### Path 3: Custom Agent / API

**Steps:**
1. Clone or download the repo (see Path 2)
2. Open the `SKILL.md` file for the skill you want
3. Load its contents as system prompt content or a tool instruction in your agent
4. Wire the required capabilities listed in that plugin's README to your agent's tools

**Best for:** Developers building their own agent with the Claude API who want to embed Atlas skills.

**Pros:** Works in any agent runtime, full portability, no Claude Code dependency
**Cons:** Requires development work to wire capabilities; no marketplace browser

---

## Section 3 — Skills Directory

Organized by jobs-to-be-done. Each plugin entry contains:
- Plugin name (linked to its README)
- 1–2 sentence description: what it does + problem it solves (length flexes by complexity)
- Skills list (skill names only)
- "Works with" line: list of compatible installation options from {Claude Code, Co-work, Clone, Custom Agent}

### Jobs-to-be-done groupings

| Group | Plugins |
|---|---|
| Communications & Inbox | inbox-zero, conference-contact-capture |
| Meetings & Calendar | meeting-ops, proactive-actions, ideal-week-ops |
| Reporting & Visibility | daily-reporting |
| Travel & Logistics | travel-prep |
| Finance & Ops | expense-management |
| Learning & Knowledge | compounding-learning, presentation-builder |

### "Works with" assessment (to verify during implementation)

Each plugin needs to be assessed against its actual capability requirements. First-pass read:

| Plugin | Assessment |
|---|---|
| meeting-ops | Connectors (calendar, email) — likely Co-work capable |
| inbox-zero | Gmail connector — Co-work capable for most skills |
| compounding-learning | Writes local files — Claude Code + Clone only |
| presentation-builder | Writes HTML files to filesystem — Claude Code + Clone only |
| proactive-actions | Mixed — depends on which actions the skill takes |
| travel-prep | Calendar connector + web search — likely Co-work capable |
| conference-contact-capture | LinkedIn research (web) + CRM — verify; likely Code |
| daily-reporting | Calendar + email + file writing — mixed |
| expense-management | QuickBooks + file writing — likely Code |
| ideal-week-ops | Calendar connector + notifications — likely Co-work capable |

**During implementation:** Read each plugin's "Required capabilities" README section to confirm before labeling.

---

## Section 4 — Contributing

One paragraph. Link to `docs/contributing.md`. Keep brief — this audience is users, not contributors.

---

## Content Rules

- No jargon (no "YAML frontmatter", no "agent runtime", no "portability rule")
- Step numbers for every setup path — no prose-only instructions
- "Works with" is a plain list, not a table or badge
- Plugin descriptions: 1–2 sentences, flex to 3 if genuinely needed (conference-contact-capture is the main candidate)
- Skills list under each plugin: names only, code-formatted

---

## What Stays the Same

- Links to `docs/installing-a-plugin.md`, `docs/contributing.md`, `docs/methodology-patterns.md`, `docs/skill-lifecycle.md` remain
- Plugin READMEs are not changed — they carry the deep detail
- `team-test/` plugins (energy-audit) are not listed in the directory — only promoted plugins

---

## Out of Scope

- Updating individual plugin READMEs (separate task)
- Updating `docs/installing-a-plugin.md` (may be redundant after this change — flag for later)
- Adding team-test plugins to the directory
