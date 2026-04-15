# Atlas internal meeting prep methodology

> Loaded by `internal-meeting-prep` before generating a brief.

## The principle

The point of internal prep is **to surface what the user already knows but doesn't have loaded into working memory.** Internal meetings are with people the user works with regularly. The user has prior context on every attendee, every project, and every open thread — it's just scattered across past notes. A good internal prep pulls that context forward so the user walks in with the right things on their mind.

Atlas's method is **second-brain-first**: the agent's job is to mine the user's existing notes, projects, and meeting history — not to generate fresh insights. If the brief is full of things the user has never seen before, something is wrong.

## The brief format

Every internal prep brief includes these sections, in this order. Some sections are de-emphasized or skipped depending on meeting type (see "Meeting type adaptations" below).

### 1. Meeting metadata

- Title
- Date and time
- Attendees (names; flag anyone who's new or rarely met with)
- Agenda (if one exists; otherwise note "no agenda set")

### 2. Purpose / desired outcome

One sentence — what is this meeting actually for? If the user set the meeting, infer from title and context. If someone else set it, infer from the agenda or recent threads with the organizer. If unclear, say so explicitly.

### 3. Context from your second brain

The substantive section. Pulled from second-brain search using the heuristics in the next section. Organize as:

- **Recent interactions** — most recent meetings/notes/messages with these attendees (last 30 days), one bullet each with date and one-line summary
- **Active projects involving these attendees** — current state from `state.md` or equivalent, one bullet per project
- **Recent decisions** — anything decided in the last 30 days that's relevant to this meeting or these people
- **Threads in flight** — open threads or commitments involving anyone in the meeting

### 4. Open questions / decisions needed

Things that are unresolved and might need to be addressed. Pulled from prior meeting notes, project state, and any open action items.

### 5. Talking points

What the user should bring up. This is opinionated — based on the context above, suggest 2–4 specific things worth surfacing in the meeting. Each talking point is one sentence with a "why" so the user can decide whether to use it.

### 6. (Optional) Pre-meeting actions

Anything the user should do in the 15 minutes before the meeting (read a doc, check on a deliverable, draft a quick reply). Skip this section if there's nothing.

## Second-brain search heuristics

When pulling context in section 3, the agent searches across the user's knowledge base using these signals:

- **Attendee names** — every meeting note, project page, or session log mentioning any attendee
- **Project tags / wikilinks** — any project page where the attendees show up as active contributors
- **Recent meeting notes** — last 30 days of notes mentioning any attendee, regardless of project
- **Open action items** — any open action assigned to or owed by anyone in the meeting
- **Recent decisions** — last 30 days of decisions tagged or wikilinked to attendees or relevant projects
- **Direct topic match** — if the meeting title or agenda mentions a specific topic, search the KB for that topic

Time-box the search. Don't try to read everything — read enough to populate the brief sections honestly. If the KB has nothing relevant, say so in the brief rather than padding with noise.

## Meeting type adaptations

The brief format is the same, but emphasis shifts:

### 1on1 with a teammate or direct report

- **Emphasize:** recent interactions with this specific person, threads in flight involving them, open commitments either way, anything they've flagged as a concern in prior notes
- **De-emphasize:** project state (unless directly relevant), broad context
- **Talking points:** lean toward personal/relational — how is this person doing, what do they need from you, what feedback have you been sitting on

### Small team sync (3–6 people)

- **Emphasize:** active projects involving the group, recent decisions, open questions, anything that needs alignment
- **De-emphasize:** individual attendee history (too much noise with 6 people)
- **Talking points:** lean toward decisions and alignment — what does the group need to converge on

### Standup or recurring status meeting

- **Emphasize:** what's changed since last time (new decisions, new blockers, completed action items)
- **De-emphasize:** long-form context, talking points
- **Brief should be SHORT.** Standups don't need a full prep — just a delta from the last instance. If there's nothing new, the brief can be one paragraph that says so.

### Larger meeting (7+ people)

- **Emphasize:** the user's specific role in this meeting (presenter, decision-maker, observer), and the 1–2 things they personally need to be ready for
- **De-emphasize:** everything else
- **Talking points:** only if the user has a speaking role

The agent infers meeting type from title (`standup`, `sync`, `1on1`, `1:1`, `weekly`), attendee count, and recurrence pattern. When uncertain, default to "small team sync" format.

## What good output looks like

A good internal prep brief is:

- **Short.** 1–2 minutes to read. The user has 15 minutes total in the prep block.
- **Scannable.** Headings, bullets, no walls of prose.
- **Specific.** Names, dates, project names, exact decisions — not abstractions.
- **Honest about gaps.** If the KB has nothing relevant on a section, say so. Don't pad.
- **Actionable.** The user finishes reading and knows what they want to bring up.

## What bad output looks like (avoid)

- Generic talking points that aren't grounded in the actual context ("ask about their priorities")
- Long paragraphs the user won't read in 15 minutes
- Restating the agenda back to the user
- Padding sections with irrelevant notes just to fill space
- Inventing context that isn't in the KB
