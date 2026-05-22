# Atlas Slack Ingestion Framework

> Loaded by `slack-categorize` before processing Slack messages.

## The principle

Slack generates noise. Most messages don't belong in the second brain. The Atlas method applies the same three-category lens used in meeting debriefs — **decisions, commitments, open threads** — to filter Slack down to only what's durable and actionable. Everything else is dropped.

The goal: if a skill needs to know what was decided, committed to, or left unresolved in Slack this week, the answer is in the vault — not buried in a Slack search.

## What belongs in the second brain

A Slack message earns a place in the digest if it contains at least one of:

1. A **decision** — something explicitly agreed on, confirmed, or concluded
2. A **commitment** — something someone said they would do, by when
3. An **open thread** — a question, blocker, or unresolved item that still needs an answer

Everything else — reactions, FYIs, social messages, automated notifications, bot outputs — is noise. Drop it.

## The three categories

### Decisions

Something explicitly agreed on in Slack. A decision is something that:

- Was stated as agreed, confirmed, or settled (not "I think we should…" — that's a thread)
- Will affect future work or behavior
- Has at least one named person behind it

Examples:
- "Confirmed — we're going with Composio as the default Calendar connector."
- "Russ approved the Calendar MCP deprioritization."

What's NOT a decision: an opinion shared, a suggestion floated, a question asked, a thing someone might do.

### Commitments

Something someone said they will do. Every commitment has:

- **What** — a concrete deliverable, not a vague intention
- **Who** — a single named person
- **By when** — a date or timeframe if mentioned, or `TBD` if not. Do not fabricate dates.

Commitments are always split into two sub-categories:

1. **User's commitments** — things the exec / user said they will do
2. **Others' commitments** — things other people said they will do

This split is non-negotiable. It mirrors how the user thinks about accountability.

### Open threads

Something that came up in Slack but wasn't resolved. Could be:

- A question that nobody answered
- A blocker or risk raised but not addressed
- A topic that needs a decision but doesn't have one yet
- A thread someone said "I'll get back to you on" without following through

These are not commitments (no one committed) and not decisions (not concluded). They're what future prep skills will surface as "things still in flight."

## Noise exclusion rules

Noise filtering is performed by `slack-fetch` before messages reach this stage. The categorizer does not re-filter — it trusts the fetcher's output. See `slack-fetch/SKILL.md` for the full universal + per-path filter rules.

If a noise message slips through (rare), drop it from categorization rather than forcing it into a category.

## Signal prioritization

When multiple messages qualify, rank by:

1. DM from a VIP sender
2. Message starred or saved by the exec (or their EA, if `exec_ea_handle` is configured)
3. Message carrying a configured high-signal reaction (e.g. `🔴`, `👀`, `‼️`)
4. Direct @mention of the exec in a monitored channel
5. DM thread where the exec's most recent message has not received a reply (pending reply)

## Scope rule

Only read:
- DMs between the exec and VIP contacts
- Channel messages where the exec is directly @mentioned
- Messages starred, saved, or reacted to with a high-signal reaction
- Threads in explicitly configured monitored channels

Do NOT scan all channels the exec is a member of.

**Fallbacks if not configured:**
- No `vip_senders` set → fall back to DMs from the exec's direct manager and direct reports only
- No `monitored_channels` set → channels path returns empty; the mentions path still catches all direct @mentions across joined channels

## Output format

Every ingestion run produces one markdown file. The format is source-agnostic — the same shape can be produced by future ingestion sources (meetings, email, etc.).

### Filename

`slack-ingest/{window_start}-to-{window_end}.md`

Examples:
- 7-day window: `slack-ingest/2026-05-15-to-2026-05-21.md`
- 14-day window: `slack-ingest/2026-05-08-to-2026-05-21.md`
- Single day: `slack-ingest/2026-05-21-to-2026-05-21.md`

Different windows naturally produce different filenames — no collision logic needed. Same-window re-runs overwrite the previous file.

### Frontmatter

```yaml
---
title: Slack Digest — <window_start> to <window_end>
date: <window_end>
type: ingestion-digest
source: slack
window_start: <YYYY-MM-DD>
window_end: <YYYY-MM-DD>
sources_scanned:
  - DMs
  - <channel-name-1>
  - <channel-name-2>
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
---
```

### Body sections

In this order, every time:

1. **`## Configuration notes`** — *only appears if any handles were skipped during the run.* Omit entirely if `skipped_handles` is empty. Format per skipped handle:

   ```markdown
   - **`@handle`** (vip|ea) — <one-line reason>.
     → Fix in `client-profile/slack-config.md` under `<config_field>`.
   ```

   Example:
   ```markdown
   - **`@russel`** (vip) — not found in Slack (typo, deactivated account, or wrong workspace).
     → Fix in `client-profile/slack-config.md` under `vip_senders`.
   - **`@jenny-ea`** (ea) — agent not authenticated for this account, so EA's stars/saves were not scanned.
     → Either re-authenticate with EA access, or remove `exec_ea_handle`.
   ```

2. **`## Run integrity`** — *always present.* Confirms what the run actually fetched, so the operator can trust the digest is complete (or know exactly where it isn't). Format:

   ```markdown
   - **Window:** 2026-05-23 to 2026-05-28 (mode: since-last, from 2026-05-22)
   - **Paths:**
     - ✅ DMs: 4 messages
     - ✅ Mentions: 2 messages
     - ✅ Reactions: 8 messages
     - ✅ Channels: 12 messages
   - **Threads expanded:** 3
   - **Total unique messages after dedupe:** 21
   ```

   If any path failed or partial, replace the ✅ with ❌ (failed) or ⚠️ (partial) and append the rerun command:

   ```markdown
   - ❌ Reactions: failed (Slack API timeout).
     → Rerun: `slack-fetch --mode reactions --window-start 2026-05-23 --window-end 2026-05-28`
   ```

   If a path was intentionally disabled via `paths_enabled` config, mark it `disabled` (not failed):

   ```markdown
   - ⊘ Reactions: disabled in `slack-config.md` (paths_enabled excludes this mode)
   ```

   If `--since-last` detected a boundary gap with the previous digest, append a gap warning:

   ```markdown
   - ⚠️ Gap detected: previous digest ended 2026-05-20, this one starts 2026-05-23. May 21–22 are not covered by any digest.
     → Rerun with `--start-date 2026-05-21 --end-date 2026-05-22` to fill the gap.
   ```

   The principle: **fail loud, not silent.** If anything was incomplete, the digest tells the operator exactly what and where. Never produce a partial digest that looks fine but missed signal.

3. **`## Summary`** — 2–3 sentences. What the main threads were this period. Written so a reader who wasn't on Slack still gets the picture.

4. **`## Decisions`** — bullet list per the decisions definition above. Each bullet is one decision in declarative form. If nothing qualifies, write `*No decisions captured.*` — do not omit the section.

5. **`## User's Commitments`** — bullet list of things the exec committed to. Format:
   ```
   - <what> — due <date or TBD>
   ```
   If none, write `*No commitments from user.*`

6. **`## Others' Commitments`** — bullet list of others' commitments, grouped by name. Format:
   ```
   - **Name**: <what> — due <date or TBD>
   ```
   If none, write `*No commitments from others.*`

7. **`## Open Threads`** — bullet list of unresolved items. Each bullet names who raised it and what's unresolved. If none, write `*No open threads.*`

## What good output looks like

- **Specific.** Names, dates, exact deliverables. Not "follow up on project" — "Paolo will confirm Hootmata pipeline is live by Friday."
- **Categories cleanly separated.** No commitments hiding in the open threads. No decisions buried in the summary.
- **Conservative.** If a message is ambiguous, lean toward dropping it or filing it as an open thread rather than inventing a commitment.
- **Complete enough to stand alone.** A reader who wasn't on Slack should understand what happened.
- **Honest about gaps.** If a commitment's due date was never stated, write `TBD`. Don't fabricate.

## What bad output looks like (avoid)

- Treating every message as a decision
- Fabricating due dates because "it seemed like soon"
- Including FYIs, greetings, or bot outputs
- Mixing commitments and open threads together
- Scanning all channels indiscriminately
- Writing the file before filtering — filter first, write second
