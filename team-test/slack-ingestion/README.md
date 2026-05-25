# slack-ingestion

> Slack → Second Brain ingestion. Turns Slack noise into a structured digest of decisions, commitments, and open threads.
> v0.1.0

## What it does

Reads the exec's Slack over a configurable window, drops the noise, and writes a single durable digest into the second brain.

- **Filters Slack down to what's durable.** Most Slack messages don't belong in the second brain. The same three-category lens used in meeting debriefs — decisions, commitments, open threads — is applied to Slack. Everything else is dropped.
- **Processes four message paths separately.** DMs, @mentions, reactions/saves, and configured monitored channels each have their own signal profile and noise rules. Treating them with one filter gives worse output.
- **Splits commitments by who.** User's commitments and others' commitments are always separate sections — non-negotiable, mirrors how the exec thinks about accountability.
- **Never fabricates.** Ambiguous messages downgrade to Open Threads. Missing due dates write `TBD`. The skill won't invent a deadline or attribute a decision.
- **One file per run.** Standard frontmatter, five fixed sections, predictable filename — so prep skills downstream can find it.

The result: if a future skill needs to know what was decided, committed, or left open on Slack this week, the answer is in the vault.

## Who it's for

Executives and EAs where Slack carries real decisions and commitments — not just chatter — and where searching back through threads to reconstruct what happened is a recurring tax. Designed for use inside the Atlas managed-service model, where it sits at the second-brain layer downstream of the AI workspace setup.

## Required capabilities

The skills depend on these capabilities. Each is named abstractly — wire it to whatever Slack-capable tool the host agent has.

- **Slack DM read** — list and read direct messages, with date filters
- **Slack channel read** — read channel messages, including @mention filters
- **Slack reactions read** — list messages carrying a specific reaction or saved/starred status
- **Slack user lookup** — resolve handles to user IDs and back
- **Slack search** — query messages across DMs and joined channels
- **Vault write** — create a markdown file at a configured path
- **Config read** — read a markdown config file from the plugin's client-profile

## Suggested tool wiring

| Capability | Common options |
|---|---|
| Slack DM / channel / reactions read | `mcp__claude_ai_Slack__slack_read_channel`, `mcp__claude_ai_Slack__slack_read_thread`, `mcp__claude_ai_Slack__slack_search_public_and_private` |
| Slack user lookup | `mcp__claude_ai_Slack__slack_search_users`, `mcp__claude_ai_Slack__slack_read_user_profile` |
| Slack search | `mcp__claude_ai_Slack__slack_search_public_and_private` |
| Vault write | Filesystem write |
| Config read | Filesystem read |

The Claude Code Slack MCP is the default wiring. Any agent with equivalent Slack access can substitute.

## Installation

This plugin is currently in **team test**. Once promoted, install via:

```
/plugin install slack-ingestion@atlas
```

For now, point your plugin loader at the `team-test/slack-ingestion/` directory directly.

## First-run setup

1. Copy `client-profile/templates/slack-config.template.md` to a live location (e.g. `client-profile/slack-config.md` in the deployed plugin, or a vault-side location the skill can read).
2. Fill in the config blocks: exec identity (and optional EA handle), VIP senders, monitored channels, high-signal reactions, default window, output path. Defaults are documented inline in the template.
3. Confirm the Slack MCP is authenticated for the exec's workspace — run any read-only Slack tool once to verify.
4. Confirm the digest output path exists (default `slack-ingest/` at vault root, parallel to `meetings/`).

No labels to create, no filters to set — Slack ingestion is read-only and write-once-per-run. Each run writes a single file named `{window_start}-to-{window_end}.md` so the window covered is obvious at a glance.

## Skills included

- **`slack-ingest`** — *neutral.* Orchestrator. Resolves config, decides the window, invokes `slack-fetch` once per path, hands the combined message list to `slack-categorize`, and writes the digest. The only entry point for a normal run.
- **`slack-fetch`** — *neutral.* Multi-path fetcher. Accepts a `mode` argument (`dms`, `mentions`, `reactions`, `channels`). Each mode has its own scope rules and noise-drop pass tuned to its signal profile. Returns a filtered message list.
- **`slack-categorize`** — *opinionated.* Owns the Atlas methodology. Loads `references/atlas-slack-ingestion-framework.md` and applies it to the combined message list to produce Decisions, User's Commitments, Others' Commitments, and Open Threads.

## Customization notes

Common things clients change:

- **VIP senders.** Set in `slack-config.md`. Drives the `dms` path scope and signal ranking. Update whenever key relationships change.
- **EA handle (optional).** `exec_ea_handle` in `slack-config.md`. When set, the reactions path also includes messages the EA starred/saved. Requires the agent to be authenticated for the EA's account.
- **Monitored channels.** Set in `slack-config.md`. Drives the `channels` path. Empty list = no channel scanning (only DMs + mentions + reactions).
- **High-signal reactions.** Set in `slack-config.md`. Reactions like `🔴`, `👀`, `‼️` mark a message as worth ingesting regardless of source.
- **Resolved reaction.** A reaction (default `✅`) that marks a thread as already handled — `slack-fetch` will skip it.
- **Default window.** Set in `slack-config.md`. Defaults to 7 days back.
- **Output path.** Set in `slack-config.md`. Defaults to `slack-ingest/` at vault root.
- **The methodology itself.** Lives in `skills/slack-categorize/references/atlas-slack-ingestion-framework.md`. Fork the plugin and edit references to customize.

## Atlas methodology

Atlas's Slack ingestion methodology is the same three-category lens as meeting debriefs: **decisions, commitments, open threads.** Anything else is noise. Commitments are always split into the user's and others'. Ambiguous messages downgrade to Open Threads rather than inflate a Decision or fabricate a commitment. Full methodology in `skills/slack-categorize/references/atlas-slack-ingestion-framework.md`.

The plugin separates orchestration (`slack-ingest`), fetching (`slack-fetch`), and categorization (`slack-categorize`) deliberately. Only the categorize skill loads the methodology — so small runs that fetch zero messages never load the full reference into context.

## Troubleshooting

**Digest is empty even though the exec had a busy Slack week.** Check `slack-config.md` — empty VIP list and empty monitored channels means only @mentions and reactions are scanned. Add VIPs or monitored channels.

**Commitments are showing up under Decisions or vice versa.** The categorize methodology distinguishes them strictly — a commitment has a *who* and a *what*; a decision is something agreed on that affects future work. If outputs are drifting, the framework reference is the source of truth — re-check `slack-categorize/references/atlas-slack-ingestion-framework.md`.

**Same message appears in multiple paths (e.g. a DM that's also reacted to).** Expected. `slack-ingest` dedupes by message ID after fetching all paths, so it appears once in the digest. The path with the strongest signal wins for ranking.

**Digest shows a "Configuration notes" section at the top.** Means one or more configured handles (VIP or EA) couldn't be resolved during the run. Each entry tells you the handle, the likely reason (typo, deactivated account, wrong workspace, no auth), and exactly where to fix it. The rest of the digest is still valid — only that specific handle was skipped.

**Slack MCP returns "not in channel" errors.** The exec's Slack user needs to be a member of the channel for `slack_read_channel`. Confirm membership before configuring a channel as monitored.

**Run feels slow on big windows.** The four fetch paths run concurrently, so a 7-day window should complete quickly. Volume-aware fan-out within a single path is deliberately deferred until real volume data is available. If a 7-day window regularly produces >250 qualifying messages, revisit the adaptive-fan-out design.
