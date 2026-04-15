---
name: meeting-scan
description: Use when the user wants to check upcoming meetings and ensure each one has a prep brief. Scans the user's calendar over a time window (default tomorrow if invoked daily, or the next 7 days if invoked weekly), classifies each meeting as internal or external by attendee email domain, checks whether a prep brief already exists, and dispatches internal-meeting-prep or external-meeting-prep for any meeting still missing a brief. Works on a schedule (daily / weekly) or on demand.
when_to_use: User asks "what meetings do I have tomorrow?", "what's my week look like?", or "scan my calendar for meetings that need prep". Also runs on a scheduled daily or weekly trigger if the user has one configured. Do NOT use this for prepping a single specific meeting the user just named — use internal-meeting-prep or external-meeting-prep directly.
atlas_methodology: neutral
---

# meeting-scan

Look ahead on the calendar, find meetings that need prep, and make sure each one gets prepped.

## Purpose

`meeting-scan` is the entry point for the meeting-ops workflow. It answers the question "what's coming up, and is everything prepped?" and then makes sure the answer to the second half is "yes." It does not generate prep briefs itself — it dispatches to the right prep skill for each meeting that needs one.

## Inputs

- **Time window** (optional). Defaults:
  - Daily mode: tomorrow (00:00–23:59 local time)
  - Weekly mode: today through 7 days from now
  - On-demand: ask the user, or accept an explicit window
- **Filters** (optional): exclude declined meetings, exclude recurring meeting series the user has marked "no prep needed", etc.

## Required capabilities

- **Calendar read** — list events in a time window with title, start/end times, attendees, status (confirmed / tentative / declined), and all-day flag.
- **Prep brief location read** — check whether a prep brief already exists for a given meeting (the location and naming convention are configured during first-run setup).

This skill does not write to anything itself; it dispatches to other skills that do.

## Steps

1. **Read configuration.** Get the user's internal email domain and the prep brief location convention from the plugin's first-run setup.
2. **Fetch meetings.** Use the calendar capability to list events in the requested window.
3. **Filter out non-meetings.**
   - Skip events marked all-day.
   - Skip events marked tentative.
   - Skip events the user has declined.
4. **Classify each remaining meeting** as internal or external:
   - Look at the attendee list (excluding the user themselves).
   - If **all** non-user attendees have email domains matching the configured internal domain, the meeting is **internal**.
   - If **any** non-user attendee has a different email domain, the meeting is **external**.
   - If a meeting has no other attendees (solo work block, focus time), skip it — no prep needed.
5. **Check for existing prep.** For each meeting that needs prep, check the prep brief location for a brief matching this meeting (by title and date, or by event ID — depends on the convention).
6. **Dispatch prep for meetings missing a brief:**
   - Internal meetings → invoke `internal-meeting-prep`
   - External meetings → invoke `external-meeting-prep`
7. **Return a status summary.** A short table or list showing each meeting, its classification, and its prep status (already had prep / prep dispatched / skipped and why).

## Output format

A short markdown summary the user can scan in seconds:

```
Meetings in window (Tomorrow):

| Time   | Meeting                  | Type     | Status              |
|--------|--------------------------|----------|---------------------|
| 09:00  | Eng standup              | internal | already prepped     |
| 11:00  | Acme Q2 kickoff          | external | prep dispatched     |
| 14:00  | 1on1 with Sam            | internal | prep dispatched     |
| 15:30  | (all-day) Team offsite   | -        | skipped (all-day)   |
```

## Customization

Common things clients adjust:

- **Time window defaults.** A heads-down weekly user might prefer a 5-day window (M–F).
- **Internal/external heuristic.** The default is single-domain matching. Multi-domain orgs (consultants, holding companies) can override the classification step to check against a list of internal domains.
- **Prep brief lookup convention.** The default assumes prep briefs are named after the meeting and live in a configured location; change this if your prep briefs live in a different system.
- **Scheduling cadence.** Wire this skill to a daily or weekly trigger, or leave it on-demand.

To customize, edit this `SKILL.md` and the configuration loaded in step 1.

## Why it's neutral

The scan itself is mechanical — list meetings, classify, check prep, dispatch. Atlas has no opinionated method for "the right way to scan a calendar." The opinionated work happens in the prep skills, which is where the methodology references live.
