---
name: internal-meeting-prep
description: Use to prep for an internal team meeting — a meeting where every attendee shares the user's email domain. Mines the user's second brain for relevant context (prior meetings, active projects, open threads, recent decisions) and produces a prep brief in the Atlas internal format. After generating the brief, schedules a 15-minute prep block on the calendar immediately before the meeting with the brief embedded in the event description.
when_to_use: User asks to prep for a specific internal meeting ("prep me for my 1on1 with Sam tomorrow", "get me ready for the weekly sync"), or dispatched by `meeting-scan` for an internal meeting that doesn't yet have a prep brief. Do NOT use this for meetings with external attendees — use `external-meeting-prep` instead.
atlas_methodology: opinionated
---

# internal-meeting-prep

Generate an Atlas-format prep brief for an internal meeting and schedule a prep block.

## Purpose

Internal meetings are with people the user already works with. The user already has the context — it's just scattered across past notes, project state, and prior meetings. This skill mines the user's second brain and surfaces what they need loaded into working memory walking into the meeting. Then it carves out 15 minutes on the calendar so the prep actually gets read.

## Inputs

- **Meeting title** (required)
- **Date and time** (required, with timezone)
- **Attendees** (required — names and email addresses)
- **Agenda** (optional, if one exists)

If invoked by `meeting-scan`, all of these come from the calendar event. If invoked directly by the user, ask for whatever's missing.

## Required capabilities

- **Knowledge base / second-brain search** — search prior meeting notes, project pages, session logs, and decision records by attendee name, project tag, and recent date
- **Calendar write** — create a new calendar event (the prep block) with title, time range, and description
- **Calendar read** — check for existing prep blocks and back-to-back meetings (for the consolidation rule in the prep-block methodology)

## Steps

1. **Load the methodology references.**
   - `references/atlas-internal-meeting-prep-methodology.md` — defines the brief format, search heuristics, and meeting-type adaptations
   - `../../references/atlas-prep-block-methodology.md` — defines how to schedule the prep block, including back-to-back consolidation
2. **Detect meeting type** from title, attendee count, and recurrence (1on1, small sync, standup, larger meeting). Use this to decide which sections to emphasize.
3. **Mine the second brain for context** using the search heuristics in the methodology doc:
   - Recent interactions with attendees (last 30 days)
   - Active projects involving attendees
   - Recent decisions involving attendees or relevant projects
   - Open threads / action items in flight
   - Direct topic match if title or agenda mentions a specific subject
4. **Draft the prep brief** in the Atlas internal format. Adapt section emphasis to the detected meeting type. Keep it scannable — 1–2 minutes to read.
5. **Schedule the prep block** per the prep-block methodology:
   - Default: 15 minutes immediately before the meeting
   - If there's a back-to-back chain, anchor the block at the start of the chain and consolidate this brief into any existing prep block for the chain
   - Title: `Prep: <meeting title>`
   - Description: the full prep brief, written directly into the event description
6. **Confirm to the user** what was generated and where the prep block is scheduled.

## Output

A short confirmation message:

```
Prep brief generated for "Weekly Eng Sync" (Tomorrow, 11:00 AM).
Prep block scheduled: Tomorrow, 10:45–11:00 AM. Brief is in the event description.
Sections: metadata, purpose, context (4 active projects), open questions (2), talking points (3).
```

If consolidating into an existing prep block, say so:

```
Prep brief generated for "1on1 with Sam" (Tomorrow, 2:00 PM).
Appended to existing consolidated prep block: Tomorrow, 1:45–2:00 PM (now covers 3 meetings).
```

## Customization

Common things clients adjust:

- **Knowledge base location and structure.** The default assumes an Obsidian-style vault with frontmatter, wikilinks, and a `state.md` per project. If your KB is Notion / Mem0 / something else, override the search step.
- **Search time window.** Default is the last 30 days. Adjust if your meeting cadence is much slower or faster.
- **Meeting type detection.** Default uses keyword matching on title plus attendee count. Override with your own classifier if needed.
- **Brief format.** The Atlas format is a strong starting point but can be edited in `references/atlas-internal-meeting-prep-methodology.md` for your team's preferences.

## Why opinionated

Atlas has a battle-tested method for internal meeting prep that's meaningfully better than "summarize the calendar event": second-brain-first context retrieval, scannable Atlas brief format, prep block discipline. The methodology references encode the thinking. Customize them in your fork rather than working around them.
