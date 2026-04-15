# Installing a Plugin

This guide walks through adding the Atlas Skills Library marketplace to Claude Code, installing a plugin from it, and setting things up so the skills actually trigger on real work. It also covers how to use these skills outside Claude Code.

> **Note:** Claude Code's plugin command syntax evolves over time. If anything below doesn't match what your version of Claude Code shows, treat the official Claude Code plugin docs as the source of truth and adjust accordingly.

## 1. Prerequisites

Before you begin, make sure you have:

- **Claude Code installed** and working (you can open a session and run slash commands).
- **Git configured** on your machine with access to GitHub — the marketplace is a public GitHub repo, but your Claude Code environment needs to be able to fetch from it.
- **Agent permission to install plugins.** In some Claude Code setups, plugin installation is gated by a permission or policy. If you're not sure, try the marketplace add command below — if it's blocked, your admin will need to allow plugin installs first.

## 2. Adding the marketplace

Run this in Claude Code:

```
/plugin marketplace add colin-atlas/atlas-skills-library
```

This registers the Atlas Skills Library as a marketplace source named `atlas` (the name comes from the marketplace manifest at the root of the repo). You only need to do this once per environment.

## 3. Listing available plugins

To see what's published in the marketplace:

```
/plugin marketplace list
```

You'll see each plugin the library exposes, along with a short description. As of v1, the flagship is `meeting-ops`.

## 4. Installing a plugin

Install a specific plugin by name, qualified by the marketplace:

```
/plugin install <plugin-name>@atlas
```

For example:

```
/plugin install meeting-ops@atlas
```

The `@atlas` suffix tells Claude Code which marketplace to pull from — it matches the marketplace name declared in this library's manifest. If you ever have multiple marketplaces registered, the qualifier disambiguates them.

## 5. Post-install

After install, **read the plugin's own README** before using it. Each plugin README covers:

- **Required capabilities** — what the host agent needs to be able to do for the skills to work.
- **Suggested tool wiring** — which Claude Code tools to map those capabilities to (e.g., which MCP servers, which built-ins).
- **First-run setup** — any one-time config: environment variables, reference doc edits, calendar or email permissions.

Skipping the README is the most common reason a skill "doesn't work" after install. If a meeting-prep skill can't read your calendar, it's almost always because the calendar tool wasn't wired up, not because the skill is broken.

## 6. Updating plugins

Claude Code exposes a marketplace update flow to pull the latest version of a plugin. The exact command may differ by Claude Code version — check `/plugin help` or the official docs for the current syntax. In general, updates are opt-in: the plugin won't change underneath you unless you ask for an update.

## 7. Uninstalling

To remove a plugin you no longer want, use Claude Code's plugin uninstall flow (again, the exact command may vary by version — check `/plugin help`). Uninstalling a plugin removes it from the session's available skills but doesn't affect the marketplace registration.

## 8. Using skills outside Claude Code

You don't need Claude Code to benefit from this library. Every skill in this repo is just a `SKILL.md` file with YAML frontmatter and markdown body — any agent runtime that can read markdown can load and use it. Clone the repo (or just the plugin folder you care about), point your agent at the `SKILL.md`, and wire up the capabilities listed in the plugin README to whatever tools your agent has available.

Full details on the portability conventions, including how non-CC agents should consume `SKILL.md` and reference docs, are in [`using-outside-claude-code.md`](using-outside-claude-code.md).

## 9. Troubleshooting

A few concrete issues and fixes:

- **Marketplace not found** — Double-check the repo name (`colin-atlas/atlas-skills-library`) and confirm your environment has access to GitHub. If the repo is private to your org, make sure your Claude Code environment is authenticated.
- **Plugin install fails** — Re-check the plugin name and the `@atlas` marketplace qualifier. Run `/plugin marketplace list` to confirm the plugin is actually published in the marketplace you think it is.
- **Skill doesn't trigger on a task you expected it to** — The skill's `description` or `when_to_use` may be too narrow for your use case. Open the plugin's README "Customization notes" section for guidance on tweaking it, or fork the plugin and broaden the triggers.
- **Skill loads but produces bad output** — Check the plugin's first-run setup. Most commonly the required capabilities aren't wired up to real tools, so the skill runs without the data it expects.
- **Skill runs but ignores your preferences** — Opinionated skills load Atlas methodology references by default. If you want your own method, fork the plugin and edit the reference docs under `skills/<skill-name>/references/`.

If none of the above match, open an issue on the library repo with the plugin name, what you expected, and what actually happened.
