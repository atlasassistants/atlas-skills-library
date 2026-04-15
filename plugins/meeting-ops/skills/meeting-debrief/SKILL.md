---
name: meeting-debrief
description: Use after a meeting to convert a transcript or raw notes into a structured debrief and append it to the meeting log. Extracts decisions made, action items (split between the user and others), and open questions. Writes a permanent meeting log entry that future meeting prep skills will use as context. Optionally routes action items to the user's task system, project state files, draft follow-up emails, or a CRM, depending on what's wired up.
when_to_use: User shares a transcript or notes and asks to "debrief this meeting", "process these notes", "extract action items", "write up the meeting", or "log this meeting". Also triggered automatically after a meeting if the user has a post-meeting capture workflow that hands off transcripts. Works for both internal and external meetings — the framework is the same; routing destinations differ based on configuration.
atlas_methodology: opinionated
---

# meeting-debrief

Convert a meeting transcript or notes into a structured Atlas debrief, append it to the meeting log, and route action items.

## Purpose

Every meeting needs a permanent record that's structured enough to be useful, complete enough to be the only artifact the user needs, and consistent enough to feed the prep skills next time the user meets with the same person or team. Atlas's debrief framework structurally separates decisions, action items (split user vs others), and open questions — every time, no exceptions. The result is a meeting log entry that's readable in a minute and searchable forever.

## Inputs

- **Transcript or notes** (required) — full meeting transcript from a recording tool, or raw notes the user typed during the meeting, or both
- **Meeting metadata** (required) — title, date, attendees. Source URL if the transcript came from a recording tool. If invoked right after a meeting, the agent can infer most of this from the user's calendar.
- **Meeting type hint** (optional) — l10, 1on1, sync, external, training, etc. If not given, the agent infers from the title and attendees.

## Required capabilities

- **Transcript fetch** — pull a transcript by meeting ID from the user's recording tool. Configurable per user — common options: Fathom, Otter, Granola, Read.ai, Zoom transcripts. The user wires up their tool's API during first-run setup.
- **Meeting log write** — create a new markdown file in the meeting log directory with the standard frontmatter and body
- **Calendar read** — used to infer meeting metadata when the user invokes the skill without providing it
- **Action item routing write** (optional) — write to the user's task system, project state files, draft email, or CRM. Each routing destination is configured separately.

## Steps

1. **Load the methodology reference.** `references/atlas-debrief-framework.md` — defines the three categories (decisions, actions, open questions), the meeting log entry format (frontmatter + body sections), the two-tier action item split (user vs others), and the routing rules.
2. **Identify the meeting.**
   - If the user provided a transcript and metadata directly, use those.
   - If the user said "debrief my last meeting", look up the most recently ended meeting on the calendar and fetch its transcript.
   - If multiple recent meetings could match, ask which one.
3. **Fetch the transcript** (if not already provided) using the configured recording tool's API. If the transcript isn't available yet (still processing), surface this to the user and offer to retry or work from raw notes.
4. **Classify the meeting type** — use the type hint if given, otherwise infer from title, attendees, and any tags in the user's calendar.
5. **Parse the transcript** into the three categories per the framework:
   - Decisions made
   - Action items, split into user's actions and others' commitments
   - Open questions / threads
   Be conservative — don't fabricate content. If the transcript has gaps, say so in the meeting log entry.
6. **Draft the meeting log entry** in the exact format from the framework:
   - Filename: `YYYY-MM-DD-meeting-title-slug.md`
   - Frontmatter matching the user's vault contract (read from CLAUDE.md or equivalent if available; otherwise use the framework default)
   - Body sections in order: Summary, Key Discussion Points, Decisions Made, `<User>'s Action Items`, Commitments from Others, Open Questions / Threads
   - Optional Leadership Coaching section only for meeting types where the user has opted in
7. **Write the entry** to the meeting log directory (configured during first-run setup).
8. **Route action items** to configured destinations:
   - User's task system → user's action items
   - Project state files → action items tagged to a specific project
   - Draft follow-up email → for external meetings, summary + commitments
   - CRM note → for external meetings, brief log entry
   Skip silently for any destination not configured. Never block the meeting log write on routing.
9. **Confirm to the user** — what was written, where, what was routed where, and any gaps or warnings.

## Output

A short confirmation:

```
Meeting log entry written: meetings/2026-04-15-product-huddle-discussion.md
- 4 decisions
- 3 of your action items
- 5 commitments from others
- 2 open threads

Routed:
- 3 action items → your task system (Todoist)
- 2 commitments tied to project "Atlas Skills Library" → projects/atlas-skills-library/state.md
- Draft follow-up email created for external attendees (Acme)
```

If a section is empty or routing was skipped, surface that:

```
Meeting log entry written: meetings/2026-04-15-standup-lamya-x-daniel-x-colin.md
- 0 decisions (none made)
- 1 of your action items
- 2 commitments from others
- 0 open threads

Routing: skipped (task system not configured for standups)
```

## Customization

Common things clients adjust:

- **Recording tool API.** Default skill ships with no specific API wired up — point it at whatever you use during first-run setup (Fathom, Otter, Granola, Zoom transcripts, etc.).
- **Meeting log location.** Default is `meetings/` in the user's vault. Change to wherever your meeting log lives.
- **Frontmatter contract.** Default uses the framework's standard frontmatter. Override with your vault's own contract — read it from CLAUDE.md or the equivalent.
- **Action item routing destinations.** All optional, all configurable. Wire up only the routes you actually want.
- **Leadership Coaching section.** Off by default. Enable per meeting type for L10s, leadership reviews, or specific 1on1s where you want qualitative coaching.
- **Meeting type vocabulary.** Default uses l10, 1on1, sync, standup, external, training, coaching, meeting. Adjust for your team's vocabulary.

## Why opinionated

Atlas has a battle-tested debrief framework — three-category separation, user-vs-others split for actions, structured meeting log entries that future prep skills depend on. The default failure modes (mixing decisions and actions, fabricating action items, vague commitments, missing the meeting log write) all hurt downstream value. The methodology reference encodes the thinking. Customize routing in your fork; respect the structure of the meeting log entry itself, because the prep skills depend on it.
