# composio-connect

> Shared Composio onboarding for Atlas plugins. Install this once — every Atlas plugin that connects to your external apps uses it.

## What it does

`composio-connect` is the shared skill that walks a user through Composio setup: installing Composio in their AI, connecting specific apps the calling Atlas plugin needs, re-authorizing when a session loses auth, and verifying each connection works. Other Atlas plugins invoke this skill instead of writing their own Composio flow.

It's stateless — every invocation re-checks Composio's live state. There's no marker file, no cache, no per-plugin local config. The plugin you're using (energy-audit, ideal-week-ops, etc.) owns its own state; `composio-connect` only owns the connection mechanism.

The skill has a single contract: caller passes a list of user-facing tool names, the skill resolves each name to a Composio toolkit via Composio's own search, ensures each one reaches a final status (`active`, `failed: <reason>`, `skipped`, or `not in composio`), and hands back a per-tool status report with plain-language reasons for anything that didn't end up `active`. No invocation modes, no flags, no slug catalog anywhere.

## Who it's for

Two audiences:

- **Atlas plugin authors** who want to add Composio onboarding to a new plugin without re-implementing the install + re-auth + connect-tools + verify flow. Invoke `composio-connect` from your plugin's setup or work skill.
- **End users** of Atlas plugins. You don't normally invoke `composio-connect` directly — it gets called automatically by whichever Atlas plugin you're using. But it's safe to run on its own to set up Composio ahead of time.

## Required capabilities

The host agent needs these capabilities. Names are abstract — map them to whatever tools your runtime provides.

- **MCP server connection** — the host can install and load an MCP server (specifically Composio's MCP)
- **Conversational interview** — the skill walks the user through Composio install with multi-step prompts
- **Tool-list introspection** — the skill detects which Composio meta-tools are loaded vs. which are missing, to branch on state
- **Composio meta-tools at runtime** — a toolkit-search capability (resolve user names to Composio toolkits), a connection-listing capability (live connected-toolkit query), auth-bootstrap calls (re-auth), plus the ability to call any tool from each requested toolkit for verification
- **Image input** — the user can paste screenshots when stuck; the skill uses them to diagnose

## Suggested tool wiring

| Capability | Validated default | Alternatives |
|---|---|---|
| MCP server connection | Composio MCP installed in the user's AI (Claude Code, Claude Desktop, Codex, ChatGPT, etc.) | None for v1 — `composio-connect` is Composio-only |
| Composio meta-tools | Composio MCP itself (`COMPOSIO_SEARCH_TOOLS`, `COMPOSIO_MANAGE_CONNECTIONS`, `mcp__composio__authenticate`, `mcp__composio__complete_authentication`) | None for v1 |
| Image input | The host AI's native image-paste support | If image input isn't available, the user-stuck path degrades to text-only diagnosis |

The plugin is intentionally Composio-only in v1. Direct vendor MCPs (Anthropic Google Calendar MCP, standalone Slack MCPs, etc.) are not supported; users with those would need to connect via Composio instead.

## Installation

```
/plugin marketplace add colin-atlas/atlas-skills-library
/plugin install composio-connect@atlas
```

After install, you don't need to run anything directly. The first Atlas plugin you set up will invoke `composio-connect` automatically. You can also invoke it manually by saying *"set up Composio"* or *"connect my tools"* if you want to set things up ahead of time.

## First-run setup

No first-run setup required for `composio-connect` itself. It's stateless — every invocation re-detects Composio state from scratch.

If you don't have Composio installed in your AI yet, the skill walks you through it the first time it's invoked (about 5 minutes — sign up at composio.dev, install in your AI tool, connect the apps the calling plugin needs).

## Skills included

**`composio-connect`** — *neutral.*
Single skill, single contract. Invoked by other Atlas plugins (or directly by the user) with a list of user-facing tool names. Resolves each name to a Composio toolkit via Composio's own search, detects Composio state, walks the user through install / re-auth / connect-apps as needed, verifies each toolkit with a test call, hands back a per-tool status report with plain-language reasons for anything that didn't end up `active`.
**Trigger phrases (direct user invocation):** *"set up Composio"*, *"connect my tools"*, *"composio setup"*. Most usage is via other plugins invoking it inline — see `references/integration-guide.md`.

## Customization notes

`composio-connect` is `atlas_methodology: neutral`. The plugin is mechanical — there's no Atlas opinion baked into how Composio gets set up that a client would want to change. The user-facing prose lives in `skills/composio-connect/references/canonical-messages.md`; clients can fork and edit those strings if they want different language, but the underlying flow doesn't change per-client.

## Atlas methodology

None. Marked `neutral` because the connection lifecycle (install / re-auth / connect-apps / verify) is mechanical, not an Atlas-specific approach. Atlas opinions live in the calling plugins (which decide what tools they need, how to interpret skipped tools, etc.), not in this shared layer.

## Troubleshooting

**The skill says Composio isn't installed, but I just installed it.**
Most AI clients (Claude Code, Claude Desktop, Codex, etc.) need a session restart to pick up newly-added MCP servers. Restart the AI and try again.

**The skill keeps asking me to re-authorize.**
Composio's session auth expires on a schedule. If it keeps re-prompting in the same session, check that the OAuth window completed successfully (the redirect to localhost may show a connection error — that's fine, the auth still went through). If you have the redirected URL handy, paste it to the skill and it'll complete the auth.

**I can't find the tool I want in Composio's app list.**
Composio's catalog is updated frequently. If your tool isn't there, you have two options: pick a different tool that does the same job (Notion vs. Asana for project management, Gmail vs. Outlook for email), or skip that capability and continue. The Atlas plugin calling `composio-connect` decides whether skipping is acceptable.

**The verification test call fails even though Composio says the tool is connected.**
Most often this means the underlying app's authorization expired even though Composio's UI hasn't refreshed. Re-authorize from Composio's dashboard, then re-run the failing step in your Atlas plugin.

**A tool I named comes back as "not in composio."**
`composio-connect` resolves your tool name via Composio's own search — if Composio finds no match for the name you gave, the tool gets marked `not in composio`. Try a variation (e.g., "Google Calendar" vs. "GCal") or pick a different tool. If you're sure the tool exists in Composio's catalog and search isn't matching, raise it with the Atlas team.
