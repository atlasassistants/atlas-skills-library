# Connector Onboarding

## Preamble

This is operator guidance, not a plugin dependency.

The `daily-reporting` plugin works with any runtime that satisfies
Capability 3 (Connector invocation — see
`policies/runtime-capabilities.md`). The recommendation below is
a fast path for operators who have no connectors wired and do not
want to manage OAuth or API keys per provider. It is not the only
path. See §Alternatives.

## Why recommend an aggregator

An aggregated-connector backend lets an operator authorize each
external provider once, from a single dashboard, without handling
per-provider OAuth credentials or API keys. The same connections
work across AI tools that support MCP.

For the struggling operator, this removes the three highest-cost
steps of a cold setup:
- creating OAuth clients per provider
- handling refresh tokens and secrets
- re-authorizing each provider inside each AI tool

## The recommended path: Composio

Composio is the recommended aggregator because it covers every
external provider this plugin's source families need, it exposes
an MCP endpoint that works with any MCP-capable AI tool, and it
offers a Google-OAuth signup that skips API-key provisioning.

### Walkthrough

1. **Sign up** at `composio.dev`. Google OAuth is the fastest
   signup — no API keys to create upfront.
2. **Install Composio in the AI tool hosting this plugin.** Every
   MCP-capable AI tool (Claude Code, Claude Desktop, ChatGPT,
   Codex, OpenClaw, and others) can consume Composio through its
   MCP endpoint. From Composio's Install page, copy the MCP URL
   and the API key, then add them to your AI tool following that
   tool's MCP install instructions. Some tools offer a first-class
   Composio extension; prefer the extension when available.
3. **Connect the apps this plugin needs.** From Composio's Connect
   Apps page, connect each app for the source families the
   deployment plans to enable in `source_map`. See §Required apps
   by source key below.
4. **Confirm every connection is Active** in the Composio
   dashboard. Inactive or expired connections surface as connector
   failures at runtime (Capability 3) and will downgrade a report
   to `status: partial` or `blocked` per
   `policies/retrieval-rules.md` ("Required vs. optional sources").
5. **Verify from inside the AI tool** that the Composio tools are
   listed. If they are not, the install in step 2 is incomplete.

### Verify

For each app the operator connected in step 3:

1. **Composio-side check** — the app row on the Connect Apps page
   shows an Active indicator. A "Connect" button that has not
   turned into an Active indicator means the connection did not
   complete.
2. **AI-tool-side check** — ask the AI tool to list its available
   Composio tools. The tool list should include the apps the
   operator connected. If a connected app is missing from the
   tool list, the install from step 2 is incomplete, not the
   connection.

If both checks pass, the source family the app backs is ready
for `source_map` in `daily-reporting-setup` step 4.

### Required apps by source key

Map each source key the deployment plans to enable to the
Composio app the deployment will authorize for it.

| Source key    | Required? (per `policies/retrieval-rules.md`) | Typical Composio app(s) |
|---------------|-----------------------------------------------|-------------------------|
| `calendar`    | optional                                      | Google Calendar, or Outlook Calendar |
| `email`       | optional                                      | Gmail, or Outlook |
| `tasks`       | `tasks`-or-`manual` is always required        | Airtable, HubSpot, Linear, Notion, Asana, Jira — depends on the operator's executive-workflow system |
| `meetings`    | optional                                      | Google Drive (for meeting docs), Notion, or the operator's meeting-note provider of record |
| `prior_state` | required on non-first-run                     | internal — not aggregator-backed |
| `manual`      | `tasks`-or-`manual` is always required        | internal — not aggregator-backed |

Minimum to cold-start a deployment: enable `manual` (no connection
needed) as the tasks source, plus whichever of `calendar` /
`email` / `meetings` the operator wants. The aggregator covers
the external ones; `manual` and `prior_state` stay runtime-local.

## After you're connected

Return to `../skills/daily-reporting-setup/SKILL.md` and proceed with
setup. The precondition is now resolved. When setup reaches
step 4 (source map), name the Composio-backed app for each
source family in `source_map` per
`schemas/deployment-config-schema.md`.

## Alternatives

The aggregator path is one way to satisfy Capability 3 (Connector
invocation). Equivalent paths:

- **Native runtime connectors** — if the AI tool hosting this
  plugin already ships provider connectors, skip the aggregator
  and use those directly.
- **Direct OAuth per provider** — create OAuth clients per
  provider and wire them into the runtime. Highest friction,
  lowest dependency footprint.
- **Other aggregators** — e.g., Pipedream Connect, Merge, Nango.
  The plugin does not prefer any specific aggregator; Composio
  is named here because it is the aggregator this plugin's
  reference operator documentation was written against.

Whatever path is chosen, the runtime still owes every obligation
in `policies/runtime-capabilities.md` and demonstrates them per
`conformance.md`.
