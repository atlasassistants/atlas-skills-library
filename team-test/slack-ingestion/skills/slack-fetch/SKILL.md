---
name: slack-fetch
description: Single-path Slack fetcher with per-path noise rules. This skill should be used when the user asks to "fetch just the slack DMs", "pull only my slack reactions", "scan monitored channels for the week", or wants to debug what one path returns before a full ingestion run. Invoked by slack-ingest once per path; can also be called directly.
when_to_use: |
  Three concrete situations:
  1. Internal dispatch — slack-ingest invokes this skill four times in parallel (one per mode) during a normal ingestion run.
  2. Operator debugging — operator wants to see what a single path returns in isolation before running the full pipeline.
  3. Single-path manual pull — operator needs only one slice (e.g. "show me this week's reactions") without writing a full digest.
atlas_methodology: neutral
---

# slack-fetch

Fetch and noise-filter Slack messages for one of four paths. One mode per invocation.

## Purpose

DMs, @mentions, reactions/saves, and monitored channels have different signal profiles. A DM from a VIP is almost always signal; a message in a busy channel is almost always noise; a reaction the exec placed is pre-curated. Running one noise filter across all four leaves precision on the table. This skill isolates each path so the filter strictness can be tuned per source.

The output goes to `slack-categorize` for methodology-driven categorization. This skill does not categorize — it only fetches and noise-drops.

## Inputs

- **`mode`** (required) — one of `dms`, `mentions`, `reactions`, `channels`.
- **`window_start`** (required) — ISO date, inclusive.
- **`window_end`** (required) — ISO date, inclusive.
- **Config object** (required) — parsed `slack-config.md` (VIP senders, monitored channels, high-signal reactions, resolved reaction).
- **Resolved handles** (optional) — pre-resolved map of `{handle: user_id}` from the orchestrator. If provided, skip live lookups for those handles. If not provided (direct invocation for debugging), resolve handles inline.

## Required capabilities

- **Slack DM read** — for `dms` mode
- **Slack channel read** — for `mentions` and `channels` modes
- **Slack reactions read** — for `reactions` mode
- **Slack search** — supports `mentions` (cross-channel @mention scan) and `reactions` modes
- **Slack user lookup** — resolve VIP handles to user IDs once at the start

## Output

An object with four fields:

```
{
  "messages": [
    {
      "id": "<slack message id>",
      "path": "dms|mentions|reactions|channels",
      "sender": "<display name>",
      "sender_id": "<user id>",
      "channel_or_dm": "<channel name or 'DM:<name>'>",
      "timestamp": "<ISO timestamp>",
      "text": "<message body>",
      "permalink": "<slack permalink>",
      "reactions": ["<reaction name>", ...],         // optional
      "thread_ts": "<thread parent ts, if part of a thread>"   // optional
    }
  ],
  "skipped_handles": [
    { "handle": "<@handle>", "role": "vip|ea", "reason": "<short reason>" }
  ],
  "threads_expanded": <integer>,
  "completion_status": "ok" | "partial" | "failed",
  "failure_reason": "<short reason if status != ok>"
}
```

If no messages qualify, return `messages: []`. Empty is a valid, non-error result.
If no handles were skipped, return `skipped_handles: []`.
`completion_status: "ok"` means the fetch finished cleanly. `"partial"` means some pagination or thread expansion failed but most data came through. `"failed"` means the path could not produce reliable results (e.g., API auth error, timeout); the orchestrator will surface this in Run integrity for the operator to rerun this single path.

## Universal noise rules (apply to every mode)

Before any path-specific filter, drop:

- Messages outside `[window_start, window_end]`
- Bot and integration messages (sender handle ends in `bot`, `app`, contains `[APP]`, or is `Slackbot`)
- Slack Workflow Builder outputs and system notifications
- Threads where the most recent message carries the configured `resolved_reaction` (default `✅`)
- Pure social messages and emoji-only replies

## Path-specific rules

### Mode: `dms`

**Scope:** DMs between the exec and any handle in `vip_senders`. If `vip_senders` is empty, fall back to DMs from the exec's direct manager and direct reports only (config flag).

**Filter strictness:** Lenient. DM content from VIPs is mostly signal. Drop only the universal noise rules and pure-social messages.

**Special handling:**
- Pending replies — if the exec's most recent message in a DM has not received a reply, flag the thread with `pending_reply: true` in metadata. Useful signal for the categorizer.

### Mode: `mentions`

**Scope:** Channel messages across all joined channels where the exec is directly `@mentioned` in the window.

**Filter strictness:** Standard. Drop universal noise plus:
- @here / @channel broadcasts (only direct @exec mentions count)
- Messages whose only content beyond the mention is "thanks", "cool", "ok", or similar

**Special handling:** none.

### Mode: `reactions`

**Scope:** Messages matching either of:
1. Any reaction in `high_signal_reactions` placed by the exec (or by `exec_ea_handle` if configured)
2. Saved/starred by the exec (or by EA if configured) **AND** in a VIP DM or a monitored channel

Only include messages where the exec (or EA) placed the reaction — this path is pre-curated signal. Do not include messages that others reacted to, even if the exec authored them.

The saved-message scope is intentionally tightened to VIP DMs and monitored channels. Operators save things broadly across many channels for personal context; only saves within scope-relevant places are meaningful for the digest. Saves outside that scope are operational context, not signal for this run.

**Filter strictness:** Minimal. The exec already curated these — apply only universal noise rules. Do not second-guess.

**Special handling:** Tag with the reaction(s) in the `reactions` field of each message object.

### Mode: `channels`

**Scope:** All messages in channels listed in `monitored_channels` for the window. If `monitored_channels` is empty, this mode returns an empty list immediately — do not fall back to scanning all joined channels.

When resolving channel names from `monitored_channels` to IDs, always search with `channel_types: public_channel,private_channel` — monitored channels are often private and a public-only search silently misses them.

When reading each channel, pass `window_start` and `window_end` as Unix timestamps (Slack's `oldest`/`latest` parameters) to constrain the read at the API level. Do not pull full channel history and filter afterward — quieter channels can return months of irrelevant messages, wasting API quota and context window.

**Filter strictness:** Strict. Drop universal noise plus:
- Messages that are pure status/standup posts unless they contain a commitment phrase ("will", "by", "next", "ETA", "due")
- Messages with no replies, no reactions, and no @mention of anyone
- Messages from people not in `vip_senders` OR not in a configured per-channel watch list (if present) — this is a hard signal floor for channel scanning

**Special handling:** Group by thread — if a message is part of a thread, include the thread parent and any replies that themselves pass the filter, so the categorizer has thread context.

## Steps

1. **Resolve mode.** Validate the `mode` argument; halt if invalid.
2. **Resolve handles.** If the orchestrator passed a pre-resolved map, use it directly. Otherwise look up each VIP handle (and `exec_ea_handle` if set and needed for this mode) against Slack. For each handle that cannot be resolved — typo, deactivated account, wrong workspace, or no auth access — add an entry to `skipped_handles` with a one-line reason and continue. Do not halt the run on unresolved handles.
3. **Fetch raw messages** for the mode using the scope rules above, using only successfully resolved IDs. **Paginate until exhausted** — do not stop at the first page. Slack search returns a page cursor; follow it until no more results in the window. There is no hard cap; Atlas-scale message volume does not require one.
4. **Apply universal noise filter** to the raw list.
5. **Apply path-specific filter** to the remaining list.
6. **Expand threads for context.** For each surviving message that is part of a thread (its `thread_ts` is set and differs from its own `ts`), fetch the full thread via `slack_read_thread`. Replace the single-message result with the thread parent + all replies that themselves pass the universal noise filter. Most decisions and commitments happen in thread replies — without the parent context, the categorizer can't judge what's a decision vs. an opinion. Increment `threads_expanded` for each unique thread fetched.
7. **Shape output objects** with the fields above. Convert Slack's raw `ts` field (Unix epoch as a decimal string) to an ISO 8601 timestamp for the `timestamp` output field. Do not use search-response display strings — they may be formatted inconsistently across MCPs and aren't reliably parseable.
8. **Set completion status.** If steps 3–6 finished cleanly, set `completion_status: "ok"`. If some pagination pages or thread expansions failed but the bulk of data came through, set `"partial"` with a short `failure_reason`. If the path could not produce reliable results at all (auth error, repeated timeouts, etc.), set `"failed"` with the reason; the orchestrator surfaces this so the operator can rerun this single path.
9. **Return** `{ messages, skipped_handles, threads_expanded, completion_status, failure_reason }`.

## What this skill does NOT do

- Does not categorize. That's `slack-categorize`'s job.
- Does not load the methodology framework. Noise rules here are mechanical, not methodology.
- Does not dedupe across paths — that happens in `slack-ingest`.
- Does not write to the vault.
- Does not modify Slack state (no reactions, no sends, no marking-as-read).
