---
name: slack
description: Retrieve Slack-based attention flags and unresolved message context for daily-reporting. Use when SOD or EOD needs executive-relevant inbox signals from Slack DMs and @mentions — pending decisions, important follow-ups, and message-derived risks from VIP contacts.
when_to_use: Invoked by `daily-reporting` when SOD or EOD needs the `email` source family and the deployment's source_map points at Slack. Returns normalized `inbox_flags` per the contract in this file. Do NOT use directly by an operator — invoke `daily-reporting` or `daily-reporting-setup` instead.
atlas_methodology: neutral
---

# Slack Connector

Use this connector when `daily-reporting` needs messaging-based attention
flags from Slack.

## Write Contract

| Output | Target | When |
|--------|--------|------|
| Normalized inbox flags | current `daily-reporting` run | whenever the `email` source family is enabled and selected |

**Naming:** return the result as `inbox_flags`.
**Skip write when:** if the source is disabled, unavailable, or has no
reporting-relevant unresolved messages, return an empty result. Do not
create durable state.

Only gather message context that matters for the report.

## Default windows

See `../../references/policies/source-windows.md`.

## Produce

- `unresolved_threads` (unresolved DMs or threads requiring executive action)
- `pending_decisions` (messages waiting on a response or decision from the executive)
- `urgent_followups` (time-sensitive follow-ups surfaced by VIP contacts or signal reactions)
- `executive_risks` (commitments, blockers, or risks raised through Slack that affect the executive's cycle)

## Rules

- do not scan all of Slack — scope, fallback behavior, noise exclusion, and
  signal prioritization are fully specified in
  `../../references/policies/source-filtering.md` (§slack)
- do not scan channel message history beyond the retrieval window
- retrieval budget: see `../../references/policies/retrieval-budgets.md`
  ("Default budgets")
- source filtering: see `../../references/policies/source-filtering.md`
  (§slack)
- connector settings: see `../../references/schemas/deployment-config-schema.md`
  (§connector_settings.slack) for configurable fields — `vip_senders`,
  `monitored_channels`, `high_signal_reactions`, `resolved_reaction`
