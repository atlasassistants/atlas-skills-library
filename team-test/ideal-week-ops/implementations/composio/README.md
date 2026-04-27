# Composio Implementation

> Use Composio to wire calendar reading and notification sending for `ideal-week-ops`. Composio is a hosted tool router — you configure app connections once at https://app.composio.dev, and the plugin uses those connections without per-app credential setup.

## What this implements

| Capability | How it's fulfilled |
|---|---|
| Calendar read | Composio Tool Router → Google Calendar (or Outlook Calendar) |
| Notification send | Composio Tool Router → Slack / Gmail / Outlook / iMessage |
| Recurring trigger | **Not provided by Composio.** Wire this through your runtime's native recurring-task feature (Cowork Scheduled tasks, Claude Code `/schedule`, GitHub Actions, etc.) — see plugin README §4. A local OS-cron fallback is provided at `scripts/setup_schedule.py` for cases with no runtime-native option (note: only fires when the device is on). |

The plugin's skills call into this implementation when they need to read the calendar or send a notification. The skills themselves do not know which Composio tool ID to call — they call `scripts/calendar_fetch.py` and `scripts/notify_send.py`, which discover the right tool via Composio's search and execute it.

## Setup walkthrough

Follow these steps in order. Steps 1–4 are one-time per machine; step 5 is per scan target.

### Step 1 — Create your Composio account

1. Open <https://composio.dev>
2. Click **Get Started**
3. Continue with Google (or GitHub / email)

> If your account requires an organization at first sign-in, create one with any name. Most accounts skip this step.

### Step 2 — Connect your apps

You'll land on "Connect your apps, unlock your workflows."

- **Required:** **Google Calendar** (or Outlook Calendar) — for the daily scan to read events
- **Required:** at least one of **Slack**, **Gmail**, **Outlook**, or **iMessage** — for delivering the scan notification

Connect each by clicking **Connect** and granting permissions. You can add more apps later from **Connect Apps** in the left sidebar.

### Step 3 — Install Composio for Claude Code

1. In the left sidebar, click **Install**
2. Find your tool (Claude Code, Cowork, OpenClaw, Codex)
3. Click **Install** — follow the prompts (typically a CLI install command and a confirmation in your tool)
4. **Restart your tool** so the Composio MCP loads

After restart, your agent has access to Composio's Tool Router. Verify by running this skill's smoke test (step 5).

### Step 4 — Verify CLI access (optional but recommended)

The implementation scripts use the Composio CLI. Check it's installed:

```bash
composio --version
```

If not found, install it from <https://docs.composio.dev/cli> (curl one-liner provided on the Install page of your dashboard).

Confirm your connections:

```bash
composio connections list
```

You should see Google Calendar (or Outlook) as `Connected`, plus your chosen notification app(s).

### Step 5 — Smoke test the wiring

From the plugin's directory, run the check script:

```bash
python implementations/composio/scripts/composio_check.py
```

Expected output:
```
✅ Composio CLI installed (vX.Y.Z)
✅ Calendar connected: googlecalendar
✅ Notification channel connected: slack
   (alternates available: gmail)
✅ All required tools discoverable via search

Ready to run scan-ideal-week.
```

Any ❌ tells you exactly what's missing and links back to the relevant step above.

## Scripts in this implementation

- **`scripts/composio_check.py`** — pre-flight verification. Run after setup to confirm everything is wired correctly.
- **`scripts/calendar_fetch.py`** — fetches calendar events for a date range. Discovers the right calendar tool dynamically; supports `--fixture` mode for testing without a live connection.
- **`scripts/notify_send.py`** — sends a notification to the configured channel. Reads channel from `.claude/ideal-week-ops.local.md`. Supports `--dry-run` to print without sending.
- **`scripts/setup_schedule.py`** — registers the recurring scan with the local OS scheduler (cron on Linux/macOS, Task Scheduler on Windows). Runs once per machine.

## Configuration file

The plugin reads `.claude/ideal-week-ops.local.md` from the user's workspace. Example:

```yaml
---
ideal_week_path: client-profile/ideal-week.md
calendar_provider: googlecalendar
# notification_channel: where to send — slack | imessage | gmail | outlook | file
# notification_target:  who receives — Slack handle, email address, phone, or file path
# IMPORTANT: Slack and iMessage do NOT notify when the target is your own connected account.
# For self-pinging, use gmail or outlook (lands in your inbox + Sent with normal notifications).
# For slack/imessage, set the target to a different recipient (EA handle, shared channel).
notification_channel: slack
notification_target: "@sam.reyes"
scan_window_days: 1
scan_schedule:
  - "0 17 * * *"   # 5pm — flag tomorrow's calendar
  - "0 7 * * *"    # 7am — flag today's calendar
dry_run: false
---
```

Create this file once during setup. The `extract-ideal-week` skill writes a starter version after the first extraction; edit by hand to change channels or schedule.

## Multi-account note

If the exec uses multiple calendars (work + personal), connect each in Composio (you can connect the same app type with multiple accounts). Set `calendar_accounts:` as a list in the local config:

```yaml
calendar_accounts:
  - googlecalendar:work
  - googlecalendar:personal
```

The fetch script reads from all listed accounts and merges results.

## Troubleshooting

**`composio: command not found`.** The CLI install didn't complete or isn't on `PATH`. Open the Install page in your Composio dashboard and re-run the install command.

**Connections list is empty.** You connected apps in the dashboard but the CLI doesn't see them. Run `composio login` to authenticate the CLI to your dashboard account, then `composio connections list` again.

**MCP tools aren't visible to the agent.** You installed Composio for Claude Code but didn't restart. Restart your tool fully (close and reopen the terminal/window). Confirm by asking the agent "what Composio tools do you have?" — it should list `COMPOSIO_SEARCH_TOOLS`, `COMPOSIO_MULTI_EXECUTE_TOOL`, etc.

**`scan-ideal-week` runs but no notification arrives.** Check `.claude/ideal-week-ops.local.md`'s `notification_channel` matches a Connected app, and `notification_target` is correct (Slack handle, email address). Run `python scripts/notify_send.py --dry-run` to print the formatted message and confirm it looks right before debugging the send.

**The send returns success but the recipient never sees it.** Self-notification trap. If `notification_channel` is `slack` or `imessage` AND `notification_target` is the same account that's connected to Composio, the message is delivered silently — Slack does not push self-DMs, and iMessage does not notify messages sent to your own Apple ID. Either (a) change `notification_target` to a different recipient (EA handle, shared channel), or (b) switch `notification_channel` to `gmail` or `outlook`, which deliver to inbox + Sent normally even when the recipient and the connected account are the same.

**Scheduled scan didn't run.** On Linux/macOS: `crontab -l` should show the entries `setup_schedule.py` registered. On Windows: open Task Scheduler and look for tasks named `ideal-week-scan-*`. If missing, re-run `setup_schedule.py`.
