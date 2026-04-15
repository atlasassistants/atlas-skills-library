# Atlas external meeting research methodology

> Loaded by `external-meeting-prep` before generating a brief.

## The principle

External meetings — calls with clients, prospects, partners, or anyone outside the org — are different from internal meetings in one key way: **the user usually doesn't have deep prior context on the people**. The Atlas method handles this with a layered approach:

1. **Check internal context first.** Has the user met this person before? If yes, the meeting log already has the most important context. Pull it.
2. **Add live external research only where needed.** If the user has met them before, research is light — just a refresh on what's new since last time. If it's a first meeting, research is the full medium-depth treatment.

This avoids the failure mode where the agent burns time researching someone the user already knows well, and also the failure mode where the agent walks the user into a first meeting cold.

## The three scenarios

### Scenario A: User has met this person before

Detected by: meeting log query returns one or more prior meetings with this attendee.

**Research load:** light. The user doesn't need a fresh dossier — they need a refresh.

**What to include:**
- Every prior meeting from the meeting log: date, what was discussed, decisions, open threads, anything they committed to following up on
- A short "what's new since last time" check: any notable public activity from the person or their company since the last meeting (one-line items, not a deep dive)

### Scenario B: First meeting with this person, but their company is known

Detected by: meeting log returns nothing for this person, but returns prior meetings with other people from the same company.

**Research load:** medium-light. The user has institutional history with the company, but not this person.

**What to include:**
- Prior meetings with anyone else from the same company (from the meeting log)
- A standard medium-depth research block on the person specifically (see Scenario C)
- Brief note on the company relationship state (any open commitments, recent contract status, etc.) pulled from the KB

### Scenario C: First meeting with this person AND first meeting with anyone from this company

Detected by: meeting log returns nothing for the person or the company.

**Research load:** full medium-depth. This is a true cold meeting and the user needs the standard prep.

**What to include:** the full medium-depth research treatment, defined below.

## Medium-depth research (the standard for first meetings)

This is the default research load for external prep when the user has no prior history with the person.

### Per-attendee research

For each external attendee, gather:

- **Role** — current title and team
- **Company** — name, what they do (one sentence), size or stage
- **Background** — a 2–3 sentence summary of their career arc and how they ended up where they are
- **Recent public activity** — anything they've put out publicly in the last ~3 months: posts, podcasts, articles, talks, public announcements. Keep it to a few items max.
- **Relevant context for this meeting** — anything that makes them specifically interesting for this conversation (e.g., they just shipped something related to the meeting topic, they recently moved into a new role)

### Per-company research

For the company (do this once, not per attendee):

- **What they do** — one sentence
- **Stage / size** — funding, headcount, lifecycle stage
- **Recent news** — last ~3 months of meaningful public activity (launches, raises, strategic moves)
- **Why they might be in this meeting** — what's the likely intent on their side, given the meeting title and context

### Output format for the research block

Per-attendee blocks use structured sections. Example:

```
## Sarah Chen — VP Product, Acme

- **Role:** VP Product since 2024-08, previously Director at Beta Co
- **Background:** 12 years in B2B SaaS product, started in design, moved into PM at scale
- **Recent activity:**
  - Spoke at SaaStr 2026-02 on AI-native product orgs
  - Posted on LinkedIn 2026-04-01 about Acme's new agentic features
- **Relevant for this meeting:** her LinkedIn post directly references the use case we're discussing
```

Then a single company block:

```
## Acme

- **What they do:** B2B project management for engineering teams
- **Stage:** Series B, ~200 employees
- **Recent news:** raised $40M Series B 2026-01; launched AI assistant 2026-03
- **Likely intent:** evaluating us as an integration partner for their new AI surface
```

## Time budget

Research has a soft cap of **5 minutes** of agent time. This is enough for medium-depth on 2–3 external attendees with a normal-sized company. Hard rules:

- **Stop researching** once you have enough to fill the structured blocks above. Don't keep going for thoroughness.
- **Skip rabbit holes.** If you find an interesting thread (their podcast appearance, a deep technical post they wrote), note it and move on. The user can dig in during the prep block if they want.
- **If a search comes up empty, log it and move on.** Don't try four different queries to find something that isn't there.
- **For meetings with more than 3 external attendees**, do per-attendee research only on the most senior attendee (or the meeting organizer), and a single shared note on the rest. The 5-minute budget doesn't scale linearly.

The 5-minute cap is not enforced by code — it's a discipline. Respect it.

## What good output looks like

A good external prep brief is:

- **Layered correctly.** Heavy on internal/meeting-log context if it exists, heavy on research only when it's a true first meeting.
- **Specific.** Names of products, dates of news, exact quotes from posts when relevant. No generic "they work in tech."
- **Honest about gaps.** If research turned up nothing notable on a person, say so. Don't manufacture a narrative.
- **Time-respecting.** Inside the 5-minute research budget. Inside a 1–2 minute reading budget for the user.

## What bad output looks like (avoid)

- Researching someone the user has met three times already and ignoring the meeting log
- Spending 10 minutes building a dossier on a junior attendee while the senior decision-maker gets one bullet
- Padding the research block with generic LinkedIn-summary content
- Surfacing controversial or personal information that has no relevance to the meeting
- Going deeper than medium-depth without being asked
