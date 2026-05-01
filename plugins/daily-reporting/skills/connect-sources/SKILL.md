---
name: connect-sources
description: Help an operator create the connections the plugin's source families need (calendar, email, tasks, meetings). Use when a deployment has no connectors wired, the operator does not want to manage OAuth or API keys per app, or the runtime lacks native provider connectors.
when_to_use: User says "connect my accounts", "connect my gmail", "connect my calendar", "I do not have connectors", "set up connectors", "help me connect", "no api keys", "aggregator setup", "composio setup", "connect sources". Also triggered by the precondition gate in `daily-reporting-setup` when a deployment has no active connections. Do NOT use for configuring a deployment that already has connections — invoke `daily-reporting-setup` for that.
atlas_methodology: neutral
---

# Connect Sources

Help an operator set up the connections `daily-reporting` needs
before `daily-reporting-setup` runs.

This file is a router. The concrete walkthrough lives in
`../../references/connector-onboarding.md`.

## When to use this

Use this when the deployment has no connections for the external
source families (`calendar`, `email`, and whatever backs `tasks` /
`meetings`) yet, OR the operator does not want to manage OAuth or
API keys per provider.

## Recommendation

The recommended path is an aggregated-connector backend, because
one-time OAuth covers every app the plugin needs and the same
connections work across AI tools.

**Constraint — read this before following the walkthrough:** this
is operator guidance, not a plugin dependency. The plugin works
with any runtime that satisfies Capability 3 (Connector invocation).
The aggregator path is a fast path, not the only path. See
`../../references/connector-onboarding.md` §Alternatives for other
paths.

## Handoff Contract

| Output | Target | When |
|--------|--------|------|
| Active connections for the source families the deployment plans to enable | the operator's aggregator account (or native runtime connectors) | before running `daily-reporting-setup` step 4 |

**Done when:** every source family the deployment plans to enable
in `source_map` has at least one active connection reachable from
the runtime.

## How an AI tool should run this

Walk the operator through §Walkthrough in
`../../references/connector-onboarding.md` one step at a time. Do
not present the full list at once — the operator is here because
they are stuck; each step is a gate.

Before step 2 (install in the AI tool), ask the operator which
AI tool is hosting this plugin, then read and apply only the
install path for that tool. Do not read install paths for other
AI tools to the operator.

Before step 3 (connect apps), ask the operator which of the
plugin's source families the deployment plans to enable
(calendar, email, tasks, meetings), then enumerate only the
Composio apps for those source families from §Required apps by
source key. Do not ask the operator to connect apps they will
not use.

After step 4 (confirm Active), ask the operator to report the
status of each connection in their own words before proceeding.
Do not assume success from step completion alone.

If the operator indicates confusion at any step, pause and
clarify before moving to the next. Do not batch-confirm multiple
steps in one turn.

## After you're connected

Return to `../daily-reporting-setup/SKILL.md` and proceed with
setup. The precondition is now resolved; connections are ready
for step 4 (source map).

## References

- `../../references/connector-onboarding.md`
- `../daily-reporting-setup/SKILL.md`
- `../../references/schemas/deployment-config-schema.md` §Source keys
- `../../references/policies/runtime-capabilities.md` §Capability 3
