---
name: external-meeting-prep
description: Use to prep for an external meeting — a call with a client, prospect, partner, or any attendee whose email domain differs from the user's. First checks the meeting log for prior history with this person or their company. If the user has met them before, pulls that context as the primary source. If it's a first meeting, performs medium-depth web research on the person and their company. Generates a prep brief in the Atlas external format and schedules a 15-minute prep block on the calendar with the brief embedded.
when_to_use: User asks to prep for a call with a client, prospect, partner, or any external person. Dispatched by `meeting-scan` for external meetings missing a brief. Do NOT use this for internal team meetings — use `internal-meeting-prep` instead.
atlas_methodology: opinionated
---

# external-meeting-prep

Generate an Atlas-format prep brief for an external meeting, including layered research, and schedule a prep block.

## Purpose

External meetings are with people the user often has limited prior context on. The Atlas method handles this in layers: check the meeting log first (have I met this person before?), pull that history if it exists, and add live research only as much as needed. First-meeting cold calls get full medium-depth research; refresh meetings get a light "what's new since last time" treatment. Then schedule a prep block so the user actually reads the brief.

## Inputs

- **Meeting title** (required)
- **Date and time** (required, with timezone)
- **Attendees** (required — names, email addresses, and which ones are external)
- **Agenda** (optional, if one exists)

If invoked by `meeting-scan`, all of these come from the calendar event. If invoked directly by the user, ask for whatever's missing.

## Required capabilities

- **Knowledge base / second-brain search** — query the meeting log database and other KB content for prior history with attendees and their company
- **Web search / research** — fetch public information about people and companies (LinkedIn-style basics, recent posts, news, public activity)
- **Calendar write** — create the prep block calendar event with the brief in the description
- **Calendar read** — check for back-to-back meetings (for the prep-block consolidation rule)

## Steps

1. **Load the methodology references.**
   - `references/atlas-external-meeting-research-methodology.md` — defines the layered research approach, scenarios, output formats, and time budget
   - `../../references/atlas-prep-block-methodology.md` — defines how to schedule the prep block, including back-to-back consolidation
2. **Identify external attendees.** Filter the attendee list to those whose email domain doesn't match the user's configured internal domain.
3. **Query the meeting log** for each external attendee:
   - Direct hit on the person? → Scenario A (refresh)
   - No hit on the person, but hit on their company → Scenario B (first meeting, known company)
   - No hit at all → Scenario C (true cold meeting)
4. **Run research according to the scenario:**
   - Scenario A: light refresh — pull the prior meeting history, add a brief "what's new" check
   - Scenario B: medium-light — prior company history from KB, plus medium-depth research on the person
   - Scenario C: full medium-depth research per the methodology doc, respecting the 5-minute time budget
5. **Pull any other relevant KB context** (active deals, prior notes mentioning the company, related project state).
6. **Draft the prep brief** in the Atlas external format. Sections:
   - Meeting metadata (title, time, attendees flagged internal/external)
   - Purpose / desired outcome
   - Prior history (if any) — from the meeting log
   - Attendee research — structured per-attendee blocks (skip or condense for refresh meetings)
   - Company context — single block on the company
   - Open questions / decisions needed
   - Talking points — grounded in the research and history
7. **Schedule the prep block** per the prep-block methodology:
   - 15 minutes immediately before the meeting
   - If a back-to-back chain exists, anchor at the start and consolidate
   - Title: `Prep: <meeting title>`
   - Description: the full prep brief
8. **Confirm to the user** what was generated, which scenario triggered, and where the prep block is scheduled.

## Output

A short confirmation message:

```
Prep brief generated for "Acme Q2 kickoff" (Tomorrow, 2:00 PM).
Scenario: B (first meeting with Sarah Chen, but prior history with Acme).
Prep block scheduled: Tomorrow, 1:45–2:00 PM. Brief is in the event description.
Research time: 4 min. Found: 2 prior Acme meetings, 1 recent LinkedIn post from Sarah.
```

For Scenario A:

```
Prep brief generated for "Sarah Chen catch-up" (Tomorrow, 2:00 PM).
Scenario: A (refresh — last met 2026-03-12).
Prep block scheduled: Tomorrow, 1:45–2:00 PM. Brief is in the event description.
Pulled context from 1 prior meeting + 1 new post since.
```

## Customization

Common things clients adjust:

- **Research depth.** Default is medium. If you want lighter (just basics) or heavier (full dossier), edit the methodology doc.
- **Time budget.** Default is 5 minutes of research. Adjust if your meeting tempo allows more or demands less.
- **Research sources.** Default is general web search. Add or restrict sources (LinkedIn-only, exclude social media, prefer company website, etc.) by overriding the search step.
- **Scenario classification.** Default uses meeting log queries. If your meeting log lives somewhere unusual or has a different schema, override the queries.
- **Brief format.** Atlas format is a strong starting point but can be edited in the methodology doc for your team's preferences.

## Why opinionated

Atlas has a battle-tested layered approach: meeting log first, research as a layer on top, time budget enforced as a discipline. The default failure modes for external prep — researching people you already know, padding briefs with generic LinkedIn content, going deeper than needed — are real and costly. The methodology references encode the thinking. Customize them in your fork rather than working around them.
