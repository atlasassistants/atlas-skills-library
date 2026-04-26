---
name: scan-ideal-week
description: Scans the executive's calendar for a target window against the documented ideal week, flags every event that violates a rule with severity (block / warning / nudge), generates a concrete reschedule suggestion for each flagged event, and sends a single summary notification. Designed to run on a schedule (default end-of-day for tomorrow, morning-of for today) but can also be invoked manually.
when_to_use: Run after extract-ideal-week. Trigger phrases — "scan calendar", "scan ideal week", "check tomorrow's calendar", "flag calendar conflicts", "calendar guardian scan", "what's wrong with tomorrow", "is today's calendar clean". Also triggered by the scheduler set up at the end of extract-ideal-week.
atlas_methodology: opinionated
---

# scan-ideal-week

Compare the calendar to the documented ideal week, flag every violation with a fix suggestion, send one notification.

## Purpose

The exec's ideal week is enforceable only if something is checking the calendar against it on a cadence. This skill is that check. Loads the canonical ideal-week document, pulls calendar events for the target window, runs every event through every rule, produces a structured flag list, and sends one summary notification through the configured channel.

## Inputs

- **Target window** — default: `tomorrow` if invoked at or after 4pm; `today` otherwise (covers all hours from midnight through 4pm). Override with explicit dates if needed.
- **Ideal week document** — read from `ideal_week_path` in the local config (default `client-profile/ideal-week.md`)
- **Local config** — `.claude/ideal-week-ops.local.md` for paths, notification channel, scan window, severity overrides

## Required capabilities

- **Calendar read** — list events for the target date range across all relevant calendar accounts
- **File read** — read the ideal-week document and the local config
- **Notification send** — deliver one summary message to the configured channel
- **(Optional) Date / time math** — for buffer calculations between events. Use the runtime's date facilities; do not implement timezone logic in the skill body.

## Steps

### 0. Pre-flight

1. Read `.claude/ideal-week-ops.local.md`. If it doesn't exist, fail loudly: "no config — run `extract-ideal-week` first." Do not invent defaults silently.
2. Read the ideal-week document at the configured path. If absent or unparseable per `../../references/ideal-week-format.md`, fail with the same instruction.
3. Resolve target window from inputs or invocation time (rule above).
4. Detect dry-run mode (config flag `dry_run: true` or skill argument). In dry-run, skip the notification send and print the output to terminal instead.

### 1. Load events

List calendar events for every date in the target window, across every calendar account configured. For each event, capture: title, start, end, attendees (count and identifiers), is_recurring, organizer, account it came from.

Sort events by start time per day.

### 2. Run the rule engine

For each day in the window, evaluate the documented ideal week against the day's events. Categories of checks (full taxonomy in `references/atlas-calendar-enforcement-methodology.md`):

- **Protected-block violations.** Any event scheduled inside a protected block (e.g., thinking time 7-8am, deep-work day, lunch window) → severity `block` unless the event title or organizer matches a VIP override.
- **NEVER rule violations.** Any event matching a NEVER rule (e.g., meeting on Tuesday/Wednesday for a no-meeting-day exec, back-to-back without buffer, before-workday-start) → severity `block` unless VIP override.
- **Cap violations.** Sum of meeting hours per day exceeds the configured daily cap (e.g., 4-hour ceiling). → severity `block` if hard cap, `warning` if target cap.
- **PREFER rule violations.** Soft-pattern violations (e.g., 1on1 not on a Thursday for a Thursday-batched exec, external call not on Mon/Thu/Fri) → severity `warning` or `nudge` per rule definition.
- **Overlap (double-booking).** Two or more events whose time ranges overlap → severity `block`. The exec literally cannot attend both. Distinct from a buffer violation; this is a true conflict, not just tightness.
- **Buffer violations.** Two meetings less than the configured buffer apart (default 15 min) but not overlapping → severity `warning`.
- **Missing prep blocks.** External calls without a 15-min prep block in front → severity `warning`.

For every flagged event, generate a **concrete suggestion** — name a specific alternative slot or action ("move to Thursday afternoon block", "shorten to 30 min", "add 15-min prep at 9:45"). A flag without a suggestion is invalid output and must be regenerated.

### 3. VIP override pass

For every flag, check the event's organizer/attendees against the VIP override list in the ideal-week document. If matched, downgrade severity by one level (block → warning, warning → nudge, nudge → drop). Annotate the flag with "VIP override applied: <name>".

### 4. Build the summary

Format per `../../references/scan-output-format.md`. Required structure:

- Header: target window + scan timestamp + total flag count by severity
- One section per day, ordered chronologically
- Within each day: blocks first, then warnings, then nudges
- Each flag: event title + time + rule violated + suggestion
- Footer: clean-day note if any day in the window has zero flags

If the entire window is clean, the summary is a single line: "Calendar clean for <window>. No flags."

### 5. Send notification

Deliver the summary to the channel configured in `.claude/ideal-week-ops.local.md`. Channels supported via the implementation layer: Slack DM, iMessage, Gmail, Outlook, file write. The skill body itself does not know the channel mechanics — it calls into the configured implementation (e.g., `../../implementations/composio/scripts/notify_send.py`).

In dry-run mode: print the summary to terminal and skip the send.

### 6. Persist scan log

Write a one-line log entry to `.claude/ideal-week-ops.scan-log.jsonl` with: timestamp, window, flag counts, channel, send-success. The log is for debugging "did the scan run?" — not for analytics.

## Output

The notification body itself (the summary built in step 4). In dry-run mode, also printed to terminal. In live mode, the skill returns a one-line confirmation: `Scan complete — N flags sent to <channel>`.

## Customization

- **Severity mapping.** Per-rule severities live in the ideal-week document. The scan skill reads them — it does not embed defaults. To change the meaning of "block" vs "warning" globally, edit `references/atlas-calendar-enforcement-methodology.md`.
- **Suggestion engine.** The "where to move it" suggestion logic is per the methodology reference. The default looks for the next-available slot inside the same day's allowed blocks. Override per-rule in the ideal-week document if a specific rule needs a different suggestion strategy (e.g., "always suggest declining, never moving").
- **Notification format.** The channel-specific renderer (Slack vs file vs email) lives in the implementation, not the skill. Edit `../../implementations/composio/scripts/notify_send.py` to change formatting per channel.
- **Window detection.** The "tomorrow if afternoon, today if morning" rule can be overridden by passing an explicit window argument when invoking the skill, or by setting `default_window:` in the local config.

## Why opinionated

The rule taxonomy (protected-block / NEVER / cap / PREFER / buffer / missing-prep) and the severity model (block / warning / nudge with VIP downgrade) are Atlas's specific approach to calendar enforcement. The full methodology, including why VIP overrides downgrade rather than skip, lives in `references/atlas-calendar-enforcement-methodology.md`. Clients wanting different rule categories or severity mechanics should fork the references — keep the skill body stable.
