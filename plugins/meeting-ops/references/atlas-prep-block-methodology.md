# Atlas prep block methodology

> Loaded by `internal-meeting-prep` and `external-meeting-prep` after they generate a prep brief.

## The principle

A prep brief that the user never reads is worthless. The single best lever for ensuring prep gets used is to **carve out time on the calendar for it, immediately before the meeting**, with the prep content embedded right in the calendar event. That way the user opens the event, sees the prep, and reads it in the slot that's already protected.

This came directly from how Atlas EAs operate. It's been validated in practice and is one of the highest-leverage habits in Atlas's meeting workflow.

## The mechanics

After generating a prep brief, the prep skill must:

1. **Identify the prep slot.** Default to a 15-minute block ending exactly when the meeting starts.
2. **Create a calendar event** in that slot with:
   - **Title:** `Prep: <meeting title>` (e.g., `Prep: Acme Q2 kickoff`)
   - **Description:** the full prep brief, written directly into the event description
3. **Confirm to the user** that the prep block was scheduled, and where (date/time).

### Why the brief goes in the description

The simplest version of "where does the brief live" is "wherever the user is already looking when they open the calendar event." Putting the brief directly in the calendar event description means:
- One fewer connector to set up (no Google Docs / Notion / Obsidian wiring required)
- Zero clicks between opening the event and reading the prep
- Works on any calendar platform the agent can write to

Clients who want the brief somewhere else (a Google Doc, a Notion page, a vault note) can customize the skill to write there and put a link in the description instead. That's a customization, not the default.

## Defaults

- **Block length:** 15 minutes. Most prep needs less time than people think; longer blocks rarely improve quality and crowd the calendar.
- **Block placement:** the 15 minutes immediately before the meeting starts.
- **Title format:** `Prep: <meeting title>` — short, scannable, sorts naturally next to the meeting.

## Edge cases

### Back-to-back meetings → consolidated prep block

If the user has multiple back-to-back meetings, **do not schedule a separate 15-minute block before each one.** Instead, schedule **one consolidated 15-minute prep block immediately before the first meeting in the run**, with all the prep briefs concatenated in the description in chronological order. The user preps for the whole block at once.

A "run of back-to-back meetings" is a sequence of meetings with no gap (or a gap shorter than 15 minutes) between them. Use this rule:

- For each meeting needing prep, walk backward in time looking for an unbroken chain of prior meetings (with gaps < 15 min).
- The earliest meeting in that chain anchors the prep block placement.
- All prep briefs for meetings in the chain land in that single block's description, separated by clear headings (`## <meeting title> — <time>`).

If a chain already has a consolidated prep block scheduled, append new prep briefs to the same block rather than creating duplicates.

### Meeting starts in less than 15 minutes from now

In normal operation this shouldn't happen — the agent should be scanning the calendar ahead of time, so prep is set up well before the meeting. If it does happen (e.g., the agent is invoked manually right before a meeting), generate the prep brief and surface it inline to the user immediately. **Do not create a calendar event in the past.**

### All-day or tentative meetings

Skip entirely. Do not generate a prep brief or a prep block for events marked all-day or tentative.

### Conflicts in the prep slot

If the prep slot (or the consolidated prep slot, for back-to-backs) is already occupied by another event:
- If that event is itself a `Prep:` event from this skill, treat it as an existing consolidated block and append (see back-to-back rule above).
- Otherwise, log a conflict warning to the user — surface the meeting that needs prep and the conflict — and skip creating the prep block. Let the user decide what to do.

## Output expectations

After completing the prep block step, the skill reports back something like:

> Prep brief generated for "Acme Q2 kickoff" (Tomorrow, 2:00 PM).
> Prep block scheduled: Tomorrow, 1:45–2:00 PM. Brief is in the event description.

For consolidated blocks:

> Prep briefs generated for 3 back-to-back meetings starting at 2:00 PM tomorrow.
> Consolidated prep block scheduled: Tomorrow, 1:45–2:00 PM. All briefs are in the event description.
