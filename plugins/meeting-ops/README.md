# meeting-ops

> Status: v0.1.0 — lightweight tier. Skeleton README; finalized in Task 18.

## What it does

Handles the full meeting lifecycle: scans your calendar for upcoming meetings, drafts prep briefs (with different methodologies for internal vs external meetings), schedules a 15-minute prep block before each meeting, and produces structured debriefs after.

## Who it's for

People who run a lot of meetings and want an agent to handle the prep/debrief discipline using Atlas's opinionated approach.

## Required capabilities

- Calendar read + write
- Knowledge base / second-brain search
- Web search / research (for external meeting prep)
- Prep brief and debrief file write
- Action item routing (task system, project notes, email drafts, or CRM — depends on your workflow)

## Suggested tool wiring

Filled in during Task 18.

## Installation

```
/plugin marketplace add colin-atlas/atlas-skills-library
/plugin install meeting-ops@atlas
```

## First-run setup

Filled in during Task 18.

## Skills included

- `meeting-scan` — neutral. Scans calendar, checks for missing prep, dispatches the right prep skill.
- `internal-meeting-prep` — opinionated. Pulls context from your second brain.
- `external-meeting-prep` — opinionated. Researches attendees and their company.
- `meeting-debrief` — opinionated. Extracts decisions, actions, open questions; routes action items.

## Customization notes

Filled in during Task 18.

## Atlas methodology

This plugin encodes several Atlas methodologies. References live alongside their skills under `skills/<skill>/references/` and the shared `references/` folder. Filled in during Task 18.

## Troubleshooting

Filled in during Task 18.
