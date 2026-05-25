---
template: slack-config
version: 0.1.0
---

# Slack Ingestion Config

> Copy this file to your deployed plugin's `client-profile/slack-config.md` (or a vault-side equivalent) and fill in the four blocks. Defaults are sensible — leave them alone unless you have a reason.

## Exec identity

The exec whose Slack is being ingested. Used to split commitments into the user's vs others'.

```yaml
exec_name: <Full Name>
exec_slack_handle: <@handle without the @>

# Optional. If the exec's EA also manages Slack on their behalf (starring, saving, flagging messages),
# set their handle here. When present, the reactions path will also scan the EA's stars and saves
# as high-signal items. Leave blank if no EA or if EA access is not needed.
exec_ea_handle: <@ea-handle without the @>   # optional
```

## VIP senders

DMs from these handles always get ingested. Empty list = fall back to DMs from the exec's direct manager and direct reports only.

```yaml
vip_senders:
  - <handle1>
  - <handle2>
  - <handle3>
```

## Monitored channels

Channels to scan. Empty list = scan no channels (only DMs + mentions + reactions). Do **not** add busy general channels here — the scan applies a strict signal floor but high-volume channels still produce noise.

```yaml
monitored_channels:
  - <channel-name-without-hash>
  - <channel-name-without-hash>
```

Optional per-channel signal floor — only ingest channel messages from these handles:

```yaml
channel_watch_list:
  <channel-name>:
    - <handle1>
    - <handle2>
```

## Reactions

```yaml
# Reactions that mark a message as worth ingesting regardless of source.
# Common choices: 🔴 (critical), 👀 (eyes-on), ‼️ (important), 🌶️ (spicy).
high_signal_reactions:
  - 🔴
  - 👀
  - ‼️

# Reaction that marks a thread as resolved — slack-fetch skips it.
resolved_reaction: ✅
```

## Paths enabled

Which fetch paths to run for this deployment. Default is all four. Omit a path to skip it.

Disabling a path is a per-client tuning decision. For example, an exec who doesn't actively save/react to Slack messages may not want the reactions path running — the other paths still cover decisions, commitments, and open threads.

```yaml
paths_enabled:
  - dms
  - mentions
  - reactions
  - channels
```

If `paths_enabled` is omitted, all four paths run. If it's an empty list, the skill halts with a clear error (nothing to fetch).

## Window

```yaml
# Default look-back in days when slack-ingest is called without an explicit window.
default_window_days: 7
```

## Output

```yaml
# Where the digest is written. Path is relative to the vault root.
# Default is a top-level slack-ingest/ folder, parallel to meetings/.
# Filenames are auto-generated as {window_start}-to-{window_end}.md
output_path: slack-ingest/
```

## Notes

- Slack search requires the exec's Slack to be authenticated through the wired MCP / API. The plugin does not handle auth.
- Adding a channel to `monitored_channels` requires the exec to already be a member of that channel — Slack's API will return "not in channel" otherwise.
- Re-run with a tighter window (`--days 1`) for a daily snapshot; the default 7-day window is the weekly rollup.
