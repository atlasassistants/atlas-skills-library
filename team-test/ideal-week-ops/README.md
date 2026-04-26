# ideal-week-ops

> Capture an executive's ideal week, document enforceable scheduling rules, and run a daily calendar scan that flags conflicts and suggests fixes.
> v0.1.0

## What it does

Turns "how this exec wants their week to run" from tribal knowledge into a documented, enforced ruleset:

- **Extracts the ideal week once.** A guided onboarding flow either parses an existing ideal-week document the exec already has, or interviews them with Atlas's standard extraction questions (rhythms, deep-work blocks, protected time, meeting limits, VIP overrides, zone of genius). Synthesizes the answers into a structured, machine-readable ideal-week document and confirms it with the user before saving.
- **Documents rules in a canonical format.** Output is a single source-of-truth file: rhythm by day-of-week, ALWAYS / NEVER / PREFER / FLEXIBLE rule buckets, protected blocks, VIP override list, default meeting lengths, and zone-of-genius notes.
- **Enforces the rules on a schedule.** Runs twice a day by default — end-of-day for tomorrow, morning-of for today. Pulls calendar events, checks them against every rule, flags violations with severity, suggests concrete fixes ("move this to Thursday afternoon", "add 15-min buffer before X"), and sends a single notification (Slack / iMessage / email / file).

The result: no one has to manually re-check the calendar against a mental model, and the exec gets one clean daily ping when something breaks the rules.

## Who it's for

Executives and the people who support them — chiefs of staff, executive assistants, operators, account managers, or executives running their own calendar with an agent. Atlas built this for execs who already know how their week should run but lose hours every week to meetings that violate that pattern, because no one is enforcing it.

If the exec doesn't yet have an ideal week, the extraction skill creates one from scratch via interview. If they do, the plugin parses it.

## Required capabilities

The plugin's skills depend on these capabilities. Each is named abstractly — wire it up to whatever tools the host agent has access to.

- **Calendar read** — list events for a given date or date range across all relevant calendar accounts (work + personal if both are scheduled into)
- **File read + write** — read and write the ideal-week document and the plugin's local config file
- **Notification send** — send a single message to a chosen channel (Slack DM, iMessage, email, or write to a file the user checks)
- **Recurring trigger** *(optional but strongly recommended)* — the ability for the runtime to invoke `scan-ideal-week` on a recurring schedule. Recommended cadence: weekdays 5pm (flags tomorrow), weekdays 7am (flags today). Without this, the user must invoke the scan manually each cycle. The plugin does not depend on a specific scheduling implementation — wire it through whatever recurring-task mechanism your runtime provides.

## Suggested tool wiring

| Capability | Common options |
|---|---|
| Calendar read | Composio (Google Calendar / Outlook routing — recommended), Google Calendar MCP direct, Outlook MCP direct |
| File read + write | Filesystem MCP, native file tools |
| Notification send | Composio (Slack / Gmail / Outlook routing — recommended), Slack MCP direct, iMessage MCP, plain file output |
| Recurring trigger | Whatever recurring-task feature your runtime provides — Claude Cowork "Scheduled tasks" with frequency Weekdays, Claude Code `/schedule`, an SDK-driven scheduled agent, GitHub Actions cron, OS cron, anything else. The plugin is agnostic about which one. If your runtime has no recurring mechanism, the local OS-cron helper at `implementations/composio/scripts/setup_schedule.py` is provided as a fallback — note that local OS scheduling only fires when the device is on. |

The recommended wiring for calendar and notification is **Composio** because it routes both through one connection layer the user configures once at https://app.composio.dev. The plugin ships an opinionated Composio implementation under `implementations/composio/` with a setup walkthrough. Direct MCP wiring also works — see customization notes.

## Installation

```
/plugin install ideal-week-ops@atlas
```

After installing, complete the first-run setup below — `extract-ideal-week` must run before `scan-ideal-week` will produce useful output.

## First-run setup

1. **Wire calendar + notification capabilities.** If using Composio (recommended), follow [`implementations/composio/README.md`](implementations/composio/README.md) — covers Composio account setup, app installation for your runtime, and connecting Google Calendar plus a notification channel. If using direct MCPs, install Google Calendar MCP and one notification MCP yourself.
2. **Decide where the ideal-week document will live.** Default: `client-profile/ideal-week.md` in the user's workspace. Override via `.claude/ideal-week-ops.local.md` (see customization notes).
3. **Run `extract-ideal-week`.** The skill explains what an ideal week is, asks if the exec already has one documented, parses it if yes or runs the extraction interview if no, and writes the documented result to the configured path. Confirm before the file is finalized.
4. **Pick how the scan gets triggered.** Two options, not mutually exclusive:
   - **Manual** — invoke `scan-ideal-week` on demand at any time with phrases like "scan calendar", "what's wrong with tomorrow", or "is today's calendar clean". The skill works fully without scheduling.
   - **Recurring** *(recommended for foolproofness)* — register a recurring task in your runtime that invokes `scan-ideal-week`. Recommended cadence: weekdays 5pm (flags tomorrow) + weekdays 7am (flags today). Wire this via your runtime's native mechanism (see Suggested tool wiring above). The plugin is agnostic about which scheduler.
5. **First scan.** Run `scan-ideal-week` once manually to confirm the wiring works end-to-end and the flag output looks reasonable before relying on the schedule.

## Skills included

- **`extract-ideal-week`** — *opinionated.* Onboarding flow. Explains the concept, checks for existing documentation, parses it or runs the standard 10 + 3 question interview (week rhythm + zone of genius), synthesizes a structured ideal-week document, confirms with the user, saves to the configured path. Resumable — if interrupted mid-interview, picks up where it left off.
- **`scan-ideal-week`** — *opinionated.* Loads the documented ideal week, pulls calendar events for the target window (default: tomorrow if invoked at or after 4pm, today otherwise), checks every event against every rule, flags violations with severity (block / warning / nudge), generates concrete reschedule suggestions, sends a single summary notification. Designed to be invoked by a recurring trigger twice a day, but works on demand any time.

## Customization notes

Common things clients change:

- **Ideal-week document location.** Default is `client-profile/ideal-week.md`. Override by editing `.claude/ideal-week-ops.local.md` (`ideal_week_path: <your-path>`). Both skills read the same path.
- **Notification channel.** Set via `.claude/ideal-week-ops.local.md` (`notification_channel: slack | imessage | gmail | outlook | file`). The Composio implementation auto-discovers which apps are connected and uses the configured one.
- **Scan window.** Default: end-of-day scan looks at tomorrow only; morning scan looks at today only. Override via `scan_window_days` in the local config.
- **Rule severities.** Each of the seven rule categories (protected-block, NEVER, cap, PREFER, overlap, buffer, missing-prep) has a default severity (block / warning / nudge) — see [`skills/scan-ideal-week/references/atlas-calendar-enforcement-methodology.md`](skills/scan-ideal-week/references/atlas-calendar-enforcement-methodology.md) for the full taxonomy. Severities can be overridden per-rule in the ideal-week document.
- **Schedule cadence.** Default twice daily (weekdays 5pm + 7am). Adjust in `.claude/ideal-week-ops.local.md` (`scan_schedule:`). Wire the actual recurrence in your runtime's scheduling mechanism — see Suggested tool wiring.
- **Extraction questions.** The 10 + 3 questions in `references/extraction-questions.md` are Atlas's standard set. Edit if a particular client needs additional questions or fewer.

When customizing, edit the `SKILL.md`, reference files, and config in your installed copy or fork.

## Atlas methodology

This plugin encodes Atlas's view that an exec's calendar should be defended by an explicit, documented ruleset — not by anyone's memory. Key principles:

- **Document the week before you defend it.** You can't enforce a rule you haven't written down. The extract skill exists because verbal "deep work on Tuesdays" doesn't survive a real meeting request from a VIP under pressure. Written rules with severities + override lists do.
- **Flag every violation, even small ones.** Nudge-severity flags (preferred-pattern violations) are still surfaced. The exec can decide what to ignore — the plugin's job is to surface, not to filter silently.
- **Suggest concrete fixes, not just complaints.** A flag without a suggestion is noise. Every flag in the scan output names a specific alternative slot.
- **Twice-daily cadence, not real-time.** Two scheduled scans per day beats real-time alerts. Real-time interrupts the exec for things that haven't happened yet; twice-daily gives the user time to fix or escalate before the day starts.

The full extraction framework lives at [`skills/extract-ideal-week/references/atlas-ideal-week-extraction-framework.md`](skills/extract-ideal-week/references/atlas-ideal-week-extraction-framework.md). The enforcement methodology lives at [`skills/scan-ideal-week/references/atlas-calendar-enforcement-methodology.md`](skills/scan-ideal-week/references/atlas-calendar-enforcement-methodology.md).

## Troubleshooting

**`extract-ideal-week` can't find an existing document.** The skill asks the user explicitly whether one exists and where. If the answer is yes, paste the path or contents. If no, the skill runs the interview from scratch — that's the expected fallback, not an error.

**`scan-ideal-week` reports "no ideal week documented".** The scan skill reads from the path configured in `.claude/ideal-week-ops.local.md` (default `client-profile/ideal-week.md`). Run `extract-ideal-week` first, or update the config path if the document lives elsewhere.

**Calendar events aren't being detected.** If using Composio, run the verification step in [`implementations/composio/README.md`](implementations/composio/README.md) — `COMPOSIO_MANAGE_CONNECTIONS` should show Google Calendar (or Outlook) as Connected. If using direct MCP, confirm the MCP is authenticated and can list events for the target date range. Also check that the calendar account being read is the one the exec actually schedules into (work vs personal).

**Notifications aren't arriving.** Confirm the notification channel in `.claude/ideal-week-ops.local.md` matches an app you've connected (in Composio or via direct MCP). Run `scan-ideal-week --dry-run` (or the equivalent flag in your wiring) to print the notification body to terminal — if that looks right, the issue is in the send step, not the scan logic.

**Scheduled scan didn't run.** Check that the recurring trigger was actually registered in your runtime — Cowork's Scheduled tasks list, Claude Code's scheduled-agents list, `crontab -l`, or wherever applicable. Local OS cron only runs when the device is on; if scans are silently missing, switch to a server-side scheduler (Cowork, scheduled agents, GitHub Actions).

**The flagged violations don't match what the exec actually cares about.** The rule severities and the rules themselves live in the ideal-week document — edit it directly. The scan skill is deterministic against whatever the document says, so adjust the source of truth, not the scan logic.
