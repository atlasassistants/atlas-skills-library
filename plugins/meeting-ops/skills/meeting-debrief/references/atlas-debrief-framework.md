# Atlas debrief framework

> Loaded by `meeting-debrief` before processing a transcript or notes.

## The principle

A debrief that mixes decisions, action items, and open questions together is unactionable. The Atlas method **structurally separates these three categories**, every time, no exceptions. This makes the debrief readable in 60 seconds, makes routing trivial, and makes the resulting meeting log searchable by future prep skills.

The other principle: **every debrief becomes a permanent meeting log entry.** It's not just for "what happened today" — it's the foundation for "what happened the last time I met with this person." The prep skills depend on the meeting log being complete, structured, and searchable.

## The three categories

### Decisions made

Things the group concluded during the meeting and now agree on. A decision is something that:

- Was actively decided in the meeting (not an action, not an idea, not a question)
- Has consensus or at least no objection from the relevant people
- Will affect future work or behavior

Examples (from a real Atlas L10):
- "Atlas will convert the EA recruitment pipeline toward higher-AI-capability EAs instead of running a separate AI-operator sandbox."
- "Connect Team will remain in place for HR operations during the transition; Circle becomes the training and community layer."

What's NOT a decision: a discussion topic, an opinion someone shared, a thing someone is going to think about, an action item.

### Action items

Things someone committed to doing. Every action item has:

- **What** — a concrete deliverable, not a vague intention
- **Who** — a single named owner
- **By when** — a date if mentioned, or "TBD" if not (don't fabricate dates)

Action items are always split into **two sub-categories**:

1. **User's action items** — things the user (whoever the meeting log belongs to) committed to
2. **Commitments from others** — things other people committed to

This split is non-negotiable. It mirrors how the user actually thinks about a meeting and what they need to track.

### Open questions / threads

Things that came up but weren't resolved. Could be:

- A question that needs an answer the meeting didn't have
- A thread someone wanted to come back to but didn't
- A concern raised but not addressed
- A topic that needs more thought before becoming a decision

These are not action items (no owner committed) and not decisions (not concluded). They're the connective tissue future prep skills will surface as "things still in flight with this person/team."

## Meeting log entry format

Every debrief becomes a markdown file in the meeting log with this exact structure.

### Filename

`YYYY-MM-DD-meeting-title-slug.md`

The slug is lowercase kebab-case derived from the meeting title. Multiple meetings on the same day are fine — slug differentiates them.

### Frontmatter

```yaml
---
title: <human-readable meeting title>
date: <YYYY-MM-DD>
type: <meeting type: l10 | 1on1 | sync | standup | external | training | coaching | meeting>
attendees:
  - <Name>
  - <Name>
tags:
  - <type tag>
  - <attendee first names, lowercase>
  - <project tags if applicable>
source_id: <recording tool's meeting ID, e.g., fathom_id>
source_url: <link to recording or transcript>
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
---
```

The exact frontmatter contract may vary by user — e.g., the user's vault may have additional required fields. The skill should respect the user's vault contract (read it from CLAUDE.md or equivalent if available) and fall back to the format above.

### Body sections

In this order, every time:

1. **`## Summary`** — one paragraph (3–5 sentences) capturing what the meeting was about and what came out of it. Written so that someone reading only the summary still gets the gist.

2. **`## Key Discussion Points`** — bullet list of the substantive things that were discussed. Each bullet is one sentence. Not a transcript — the takeaways.

3. **`## Decisions Made`** — bullet list per the "decisions" definition above. Each bullet is one decision in declarative form. Empty list is OK if no decisions were made — write `*No formal decisions made.*` rather than omitting the section.

4. **`## <User>'s Action Items`** — bullet list of the user's commitments. Each bullet: action — due date (or `due TBD`).

5. **`## Commitments from Others`** — bullet list of others' commitments, grouped by name. Format:
   ```
   - **Name**: action — due date (or `due TBD`)
   ```

6. **`## Open Questions / Threads`** — bullet list of unresolved items. Empty list is OK; write `*Nothing unresolved.*` rather than omitting.

7. **(Optional) `## Leadership Coaching`** — only included for meetings where the user has explicitly opted in to coaching analysis (L10s, leadership reviews, certain 1on1s). When included, this is a 3–4 paragraph qualitative observation: what the user did well, what they could tighten, the unspoken dynamic in the room, and one concrete growth area. Skip for routine syncs and standups.

## Action item routing

The debrief itself is the durable record. **Routing action items to other systems is configurable per user** — the skill doesn't hardcode any specific destination. The user wires up routing during first-run setup.

Default routing destinations (each can be enabled or disabled, and pointed at the user's actual tools):

- **User's task system** — for the user's own action items. Wired up to whatever the user uses (Todoist, Things, Linear, a markdown todo file, etc.).
- **Project state files** — for action items tied to a specific project, append to that project's `state.md` or equivalent.
- **Draft follow-up email** — for external meetings, draft an email to attendees summarizing decisions and confirming commitments. User reviews and sends.
- **CRM note** — for external meetings, write a note to the CRM record for the company / contact.

The routing step is **post-debrief** — first the meeting log entry is written (always), then routing happens (if configured). If routing fails or isn't configured, the meeting log entry is still complete and the user can route manually.

## Process

1. **Receive transcript or notes** from the user or from a meeting recording tool API.
2. **Identify the meeting** — title, date, attendees, source URL. If invoked right after a meeting and the user hasn't named one, ask which meeting (or pick the most recent if obvious).
3. **Classify the meeting type** — l10, 1on1, sync, external, etc. Use the type tag from the user's vault contract if it exists.
4. **Parse the transcript or notes** into the three categories: decisions, actions (user's vs others'), open questions.
5. **Draft the meeting log entry** in the format above. Be honest about gaps — if no decisions were made, say so. Don't fabricate.
6. **Write the entry** to the meeting log location (configured during first-run setup).
7. **Route action items** to configured destinations (if any). Skip silently if not configured.
8. **Confirm to the user** — what was written, where, what was routed where.

## What good output looks like

- **Categories cleanly separated.** No action items hiding in the discussion section. No decisions buried in the summary.
- **Specific.** Names, dates, exact deliverables. Not "discuss the new initiative" — "Cesar will draft the client FAQ by 2026-04-17."
- **Complete enough to be the only record.** A reader who didn't attend should be able to understand what happened and what's owed by whom.
- **Honest about gaps.** If the transcript is missing a section, say so. If a decision is unclear, mark it as an open question instead.
- **Compatible with the meeting log contract.** Frontmatter matches the user's vault format. Filename follows convention.

## What bad output looks like (avoid)

- Mixing decisions, actions, and discussion in one section
- Inventing action items because "every meeting should have some"
- Vague action items without owners or concrete deliverables
- Fabricating dates
- Long Summary sections that retell the meeting instead of distilling it
- Skipping the file write because "it didn't seem important enough"
- Trying to route action items before the meeting log entry is written
