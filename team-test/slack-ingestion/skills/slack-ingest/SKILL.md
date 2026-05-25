---
name: slack-ingest
description: Full-pipeline Slack ingestion orchestrator. This skill should be used when the user asks to "ingest slack", "run the slack digest", "build the slack digest", "what happened on slack this week", "run slack ingestion", or "process slack for the last N days". Also invoked when a prep or report skill needs Slack context for the period and the digest is missing.
when_to_use: |
  Three concrete situations:
  1. Manual run — operator wants a digest of what happened on Slack over a window (defaults to last 7 days).
  2. Scheduled rollup — weekly cron or similar trigger producing a recurring Slack digest.
  3. Upstream dependency — a prep or report skill (daily-reporting, meeting-prep) needs Slack context for the period and the digest file is missing or stale.
atlas_methodology: neutral
---

# slack-ingest

Run the full Slack ingestion pipeline for a window — multi-path fetch, single categorize, one digest written.

## Purpose

Slack is high-volume and low-density. Most of it is noise. This skill is the single entry point that turns a Slack window into a durable second-brain artifact: a digest of what was decided, what was committed to, and what's still open. The pipeline is intentionally simple — fetch each path separately, categorize once together, write one file. Volume-aware fan-out is deferred until real volume data justifies it.

## Inputs

- **Window** (optional) — choose one of:
  - `--days N` — number of days back from yesterday
  - `--start-date YYYY-MM-DD --end-date YYYY-MM-DD` — explicit window
  - `--since-last` — read the most recent digest in `output_path`, use its `window_end + 1 day` as the new `window_start`. `window_end` is yesterday. Falls back to `default_window_days` if no previous digest exists. **Recommended for ongoing ops** — cadence-agnostic, zero overlap, missed-day catch-up automatic.
  - Omitted — defaults to `default_window_days` from config (7 days out of the box).

  `window_end` is yesterday by default (last fully-completed calendar day), not today, to avoid partial-day coverage.
- **Config override** (optional) — alternate path to a `slack-config.md` if not using the plugin default.

## Required capabilities

- All capabilities required by `slack-fetch` (Slack reads, user lookup, search)
- All capabilities required by `slack-categorize` (none beyond reasoning)
- **Config read** — read the `slack-config.md` file
- **Vault write** — write the digest markdown to the configured output path

## Steps

1. **Resolve config.** Read `slack-config.md` and parse it into a structured config object — VIP senders, monitored channels, high-signal reactions, resolved reaction, default window, output path, optional `exec_ea_handle`, optional `paths_enabled` (defaults to all four if omitted). If the config file is missing or has unfilled placeholders, halt with a clear error pointing to the template. If `paths_enabled` is present but empty, halt — nothing to fetch.

2. **Resolve the window.**
   - If `--start-date` and `--end-date` provided → use them as `window_start` / `window_end`.
   - Else if `--days N` provided → `window_end = yesterday`, `window_start = window_end - (N-1) days`.
   - Else if `--since-last` → scan `output_path` for the most recent digest by filename. Parse its `window_end` from frontmatter. New `window_start = previous_window_end + 1 day` (exclusive — no overlap). New `window_end = yesterday`. If no previous digest exists, fall back to `default_window_days` from config.
   - Else (default) → `window_end = yesterday`, `window_start = window_end - (default_window_days - 1) days`.

   **Boundary continuity check (for `--since-last` only):** if `window_start` does not equal `previous_window_end + 1 day` exactly, flag a gap in Run integrity. The skill does not auto-correct gaps — surface them for operator decision.

   `window_end = yesterday` (not today) avoids partial-day coverage from running mid-day.

3. **Resolve handles once.** Look up every VIP handle (and `exec_ea_handle` if set) against Slack to produce a `{handle: user_id}` map. For each handle that cannot be resolved, add an entry to `skipped_handles` with role (`vip` or `ea`) and a one-line reason. Do not halt — continue with the handles that resolved successfully.

4. **Fetch enabled paths concurrently.** Invoke `slack-fetch` for each mode listed in `paths_enabled` (defaults to all four: `dms`, `mentions`, `reactions`, `channels`) **in parallel**, passing the parsed config and the resolved handle map. Each invocation is independent and returns `{ messages, skipped_handles, threads_expanded, completion_status, failure_reason }`. Paths not in `paths_enabled` are skipped entirely — record them as `disabled` (not `failed`) in the Run integrity section so the operator knows the omission was intentional.

5. **Combine and dedupe.** Merge all four `messages` lists into one. Deduplicate by message `id` — a message reached by multiple paths appears once. When deduping, prefer the path with the strongest **dedup signal ranking** (reactions > dms > mentions > channels). Note: this dedup ranking is intentionally different from the framework's signal priority for categorization — dedup is about which path "owns" the message; categorization signal priority is about ranking output within categories. Also merge all `skipped_handles` lists from the fetch calls with the orchestrator-level list from Step 3, deduplicating by handle. Track per-path counts (messages returned per mode) and `completion_status` per path for the Run integrity section.

6. **Skip if empty.** If the combined message list is empty, write a minimal digest (frontmatter + Configuration notes if any + Summary noting no qualifying messages + the four empty-section markers) and exit cleanly. The categorizer is not invoked.

7. **Categorize.** Invoke `slack-categorize` once with the combined message list. It returns four arrays plus a summary. Ambiguous messages have already been downgraded inside the categorizer — do not re-classify here.

8. **Write the digest.** Build the digest at `{output_path}/{window_start}-to-{window_end}.md`. The full output format — frontmatter schema, section order, empty markers, Configuration notes block, and Run integrity block — lives in `slack-categorize/references/atlas-slack-ingestion-framework.md` under "Output format". Follow that reference exactly. The **Run integrity** section must include: window resolution mode (default / since-last / explicit), per-path counts and completion statuses, threads expanded count, total unique messages after dedupe, and any boundary gap warnings. Same-window re-runs naturally overwrite (same filename); different windows produce different filenames.

9. **Return.** Surface the digest path to the caller plus a one-line summary (e.g. `Wrote slack-ingest/2026-05-15-to-2026-05-21.md — 3 decisions, 2 user commitments, 5 others' commitments, 4 open threads, 1 handle skipped`).

## Path dedupe rules

When the same message ID comes back from multiple paths, keep the one with the strongest signal for ranking purposes. Message text and metadata are identical across paths, so no merge logic is needed.

1. `reactions` (highest — exec already curated)
2. `dms` (high — VIP one-on-one signal)
3. `mentions` (medium — direct ask)
4. `channels` (lowest — broadest scope)

This ranking is for **deduplication only** — deciding which path "owns" a duplicated message. It is intentionally different from the framework's **signal priority** list (VIP DM > starred/saved > high-signal reaction > @mention > pending reply), which is used by the categorizer to rank items within their output category. Do not conflate the two.

## Empty-state handling

A normal run with no qualifying messages is *not* an error. Write the digest with:
- `## Configuration notes` — only if any handles were skipped (per format in framework reference).
- `## Summary` — one sentence noting the window was scanned and nothing qualified.
- All four category sections present with their empty markers.

This keeps downstream prep skills' assumptions about file presence intact.

## Error handling

- **Missing config** — halt with a message pointing to `client-profile/templates/slack-config.template.md`.
- **Slack auth failure (entire workspace)** — halt and surface the auth error; do not write a partial digest.
- **Unresolvable handle (single VIP or EA)** — never halt. Skip the handle, record it in `skipped_handles`, surface in the digest's Configuration notes section. The rest of the run continues.
- **One fetch path fails, others succeed** — log the failed path in the digest Summary (`Note: monitored-channels path failed — see logs.`) and continue with the remaining paths. Never silently drop a slice.
- **Categorize returns nothing on a non-empty input** — surface as a fatal error; this is a methodology failure, not an empty window.
- **Vault write fails** — surface the path and error; do not retry to a different location.

## What this skill does NOT do

- Does not load the methodology framework — `slack-categorize` owns that.
- Does not fan out by volume — single categorize call across the combined list, deferred by design.
- Does not write to anywhere besides the configured `output_path`.
- Does not send Slack messages, react, or modify Slack state in any way. Read-only.
