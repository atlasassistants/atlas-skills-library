# meeting-ops

> Meeting prep, calendar scanning, and structured debriefs — Atlas-style.
> v0.1.0 — `lightweight` tier.

## What it does

Handles the full meeting lifecycle for someone who runs a lot of meetings:

- **Scans your calendar** ahead of time, finds meetings missing prep, and dispatches the right prep skill.
- **Drafts a prep brief** for each meeting, tailored to whether it's internal (mines your second brain for context) or external (pulls prior history from your meeting log first, then layers on web research only as needed).
- **Schedules a 15-minute prep block** on your calendar immediately before each meeting, with the prep brief written directly into the calendar event description so you read it in the slot that's already protected.
- **Debriefs each meeting afterward** by parsing the transcript or notes into a structured Atlas-format meeting log entry — decisions, action items (split between you and others), open threads — and optionally routes action items to your task system, projects, or follow-up emails.

The result is a closed loop: every meeting gets prepped before, gets debriefed after, and the debrief feeds the prep for the next meeting with the same person or team.

## Who it's for

People who run a high volume of meetings — operators, founders, executives, account managers — and want an agent to handle the prep/debrief discipline using Atlas's opinionated approach. Atlas built this for the way our human EAs operate: prep blocks on the calendar, structured meeting logs, and second-brain-first context retrieval. If that maps to how you (or the person you're building this for) work, this plugin will earn its keep.

## Required capabilities

The plugin's skills depend on these capabilities. Each one is named abstractly — wire it up to whatever tool the host agent has access to.

- **Calendar read + write** — list events in a time window with attendees and statuses; create events for prep blocks
- **Knowledge base / second-brain search** — search the user's notes, project pages, session logs, and meeting log
- **Meeting log read + write** — query the meeting log database for prior history with attendees, and write new debrief entries
- **Web search / research** — fetch public information about people and companies (for `external-meeting-prep`)
- **Transcript fetch** — pull a transcript by meeting ID from the user's recording tool (for `meeting-debrief`)
- **Action item routing write** (optional) — write to a task system, project state files, draft emails, or a CRM

## Suggested tool wiring

The plugin doesn't ship with any specific tool wiring — you connect each capability to whatever the user already uses. Common stacks:

| Capability | Common options |
|---|---|
| Calendar | Google Calendar MCP, Outlook MCP |
| Knowledge base | Filesystem MCP pointed at an Obsidian vault, Notion MCP, Mem0 |
| Meeting log | A directory of markdown files (default), or a row-per-meeting database |
| Web search | Any web search MCP, Perplexity, Brave Search |
| Transcript fetch | Fathom API, Otter API, Granola API, Read.ai, Zoom Meeting API |
| Task system | Todoist, Things, Linear, a markdown todo file |
| Email drafting | Gmail MCP, Outlook MCP |
| CRM | HubSpot, Attio, Notion CRM |

These are examples, not requirements. Pick what the user actually has.

## Installation

```
/plugin marketplace add colin-atlas/atlas-skills-library
/plugin install meeting-ops@atlas
```

After installing, complete the first-run setup below before running any of the skills.

## First-run setup

The user (or their agent) should configure the following once:

1. **Internal email domain.** Used by `meeting-scan` and `external-meeting-prep` to classify meetings as internal vs external. Example: `atlas-assistants.com`.
2. **Knowledge base location.** Where the user's second brain lives, and any conventions the agent needs to know about (frontmatter contract, project structure, wikilink format).
3. **Meeting log location.** The directory or database where meeting log entries are written and read. Default convention: one markdown file per meeting at `meetings/YYYY-MM-DD-meeting-title-slug.md` with the frontmatter described in the [debrief framework](skills/meeting-debrief/references/atlas-debrief-framework.md).
4. **Recording tool API.** Which transcript source the agent should use (Fathom, Otter, etc.), with whatever credentials are needed.
5. **Calendar wiring.** Confirm the calendar capability has both read and write access.
6. **Action item routing destinations** (optional). Wire up any combination of: task system, project state files, draft email, CRM. Each is independent.
7. **Leadership Coaching opt-in** (optional). Per meeting type, decide whether `meeting-debrief` should include the optional coaching section. Off by default.

## Skills included

- **`meeting-scan`** — *neutral.* Scans your calendar over a time window, classifies each meeting, checks for existing prep, and dispatches the right prep skill for any meeting still missing a brief.
- **`internal-meeting-prep`** — *opinionated.* Mines your second brain for prior context (with the meeting log as the highest-priority source) and produces an Atlas-format prep brief for an internal team meeting. Schedules a 15-minute prep block.
- **`external-meeting-prep`** — *opinionated.* Layered approach: checks the meeting log first for prior history with the person or company, then runs medium-depth web research only as much as needed. Generates a prep brief and schedules a prep block.
- **`meeting-debrief`** — *opinionated.* Parses a transcript or notes into a structured meeting log entry — decisions, your action items, others' commitments, open threads — and routes action items to configured destinations.

## Customization notes

This plugin is opinionated by design but every layer is editable. Common things clients change:

- **The methodology references.** They live next to the skills that use them, under `skills/<skill>/references/` and the shared `references/` folder. Edit them to encode your own variant of the Atlas method, or to adjust formats for your team's preferences.
- **The internal/external classification heuristic.** Default is single-domain matching. Multi-domain orgs override this in `meeting-scan`.
- **The 30-day search window** for second-brain context. Default in `internal-meeting-prep`; adjust to your meeting cadence.
- **The 5-minute research budget** in `external-meeting-prep`. Adjust if your tempo allows more or demands less.
- **The prep block length and format.** Default is 15 minutes with the brief in the event description. Edit `references/atlas-prep-block-methodology.md` to change.
- **The meeting log frontmatter contract.** Default matches the Atlas standard; override to match your own vault contract.
- **Action item routing.** All optional, all configurable. Wire only the routes you actually want.

When customizing, edit the SKILL.md and reference files in your installed copy or your fork. The plugin is meant to be a starting point you adapt — not a black box.

## Atlas methodology

This plugin encodes several Atlas methodologies. They're not generic prep/debrief templates — they came from how Atlas's human EAs actually run executive meeting workflows, and they've been validated in production. Specifically:

- **The 15-minute prep block discipline** — [`references/atlas-prep-block-methodology.md`](references/atlas-prep-block-methodology.md). The single highest-leverage habit in the meeting workflow: a calendar block before every meeting, with the prep right there in the event description.
- **Second-brain-first internal prep** — [`skills/internal-meeting-prep/references/atlas-internal-meeting-prep-methodology.md`](skills/internal-meeting-prep/references/atlas-internal-meeting-prep-methodology.md). The user already knows everything in an internal meeting; surface it from their existing notes instead of generating fresh "insights."
- **Layered external prep with the meeting log first** — [`skills/external-meeting-prep/references/atlas-external-meeting-research-methodology.md`](skills/external-meeting-prep/references/atlas-external-meeting-research-methodology.md). Don't research someone you've already met three times. Check the meeting log first; layer research only when it's genuinely needed.
- **Three-category structured debriefs** — [`skills/meeting-debrief/references/atlas-debrief-framework.md`](skills/meeting-debrief/references/atlas-debrief-framework.md). Decisions, action items (split user vs others), open questions — never mixed. Every meeting becomes a permanent log entry that the prep skills depend on.

## Troubleshooting

**`meeting-scan` finds no meetings.** The calendar capability may not have permission for the requested time window, or the user's calendar may not have any events in that window. Check calendar wiring and the time window settings.

**A meeting is being classified wrong (internal flagged as external or vice versa).** Check the configured internal email domain and confirm the attendee list on the calendar event includes email addresses the agent can read. For multi-domain orgs, override the classification step in `meeting-scan`.

**Prep block is being scheduled in the wrong slot.** Check whether the meeting is part of a back-to-back chain — the prep block consolidation rule anchors the block at the start of the chain. See `references/atlas-prep-block-methodology.md`.

**Prep brief is missing context the user knows is in the second brain.** The KB search heuristics may not match your vault's conventions. Override the search step in the relevant prep skill, or adjust the heuristics in the methodology doc.

**`meeting-debrief` says the transcript isn't available.** Recording tools sometimes need a few minutes after the meeting ends to process the transcript. Retry, or fall back to raw notes.

**Action items aren't being routed.** Routing is optional and skipped silently if not configured. Check first-run setup for which routing destinations are wired up. The meeting log entry is always written even if routing fails.

**A skill isn't triggering when expected.** The `description` and `when_to_use` in the skill's frontmatter may be too narrow for your phrasing. Edit them to match how you actually ask for the work.
