---
name: slack-categorize
description: Atlas-methodology categorizer for Slack messages. This skill should be used when the user asks to "categorize these slack messages", "apply the atlas slack lens to this", or "tell me what's a decision vs commitment vs open thread in this list". Also invoked by slack-ingest after all fetch paths complete. Loads the framework reference and produces four arrays; never fabricates.
when_to_use: |
  Three concrete situations:
  1. Internal dispatch — slack-ingest invokes this skill once after all four fetch paths complete and messages are deduped.
  2. Ad-hoc categorization — operator already has a list of Slack messages (from a manual fetch or another source) and wants the Atlas methodology applied to it.
  3. Methodology audit — operator wants to see how the categorizer would classify a specific message or set of messages before committing to a full pipeline run.
atlas_methodology: opinionated
---

# slack-categorize

Apply the Atlas methodology to a filtered Slack message list. Return four categorized arrays.

## Purpose

This is the only skill in the plugin that loads the methodology. By design — keeping the framework reference confined here means orchestration and fetching stay context-light, and the methodology lives in exactly one place. Clients customize by editing the reference, not the skill body.

The skill takes already-filtered messages (noise already dropped by `slack-fetch`) and assigns each one to a category — or drops it as ambiguous. Conservative by default: when in doubt, file as Open Thread rather than fabricate a Decision or invent a commitment due date.

## Inputs

- **`messages`** (required) — list of message objects from `slack-fetch` (combined and deduped by `slack-ingest`). Each has `id`, `path`, `sender`, `text`, `timestamp`, and optional `reactions`, `pending_reply`.
- **`user_identity`** (required) — the exec's name and Slack handle. Used to split commitments into user's vs others'.

## Required capabilities

- **Reasoning only.** No external reads, no writes. Pure transformation.

## Methodology

Load `references/atlas-slack-ingestion-framework.md` before processing. The reference is authoritative for:

- What qualifies as a decision vs commitment vs open thread
- How commitments split between the user and others
- What counts as ambiguous (and why ambiguous → Open Thread, not a fabricated Decision)
- How due dates are handled (extract if stated, write `TBD` if not, never invent)
- Signal prioritization when ranking within a category

## Output

```
{
  "decisions": [
    { "text": "<declarative one-line decision>", "source_id": "<message id>", "permalink": "<...>" }
  ],
  "user_commitments": [
    { "what": "<concrete deliverable>", "due": "<date or 'TBD'>", "source_id": "<...>", "permalink": "<...>" }
  ],
  "others_commitments": [
    { "who": "<name>", "what": "<concrete deliverable>", "due": "<date or 'TBD'>", "source_id": "<...>", "permalink": "<...>" }
  ],
  "open_threads": [
    { "raised_by": "<name>", "summary": "<one-line unresolved item>", "source_id": "<...>", "permalink": "<...>" }
  ],
  "summary": "<2-3 sentence summary of the window — what the main threads were>"
}
```

## Steps

1. **Load the framework.** Read `references/atlas-slack-ingestion-framework.md` into context. This is the source of truth for every classification decision below.

2. **Rank by signal first.** Order the input messages by signal priority (per the framework's signal prioritization list — DMs from VIPs first, then starred/saved, then high-signal reactions, then @mentions, then pending replies). This ordering doesn't change category assignment but affects how Summary is written.

3. **Classify each message.** For each message, ask in order:
   - **Is this a decision?** Something explicitly agreed, confirmed, or settled, that will affect future work, with at least one named person behind it. *Not* an opinion shared, a suggestion floated, or a question asked.
   - **Is this a commitment?** Someone said they will do something concrete. Must have a *who* (single named person) and a *what* (concrete deliverable). Due date if stated, else `TBD`.
   - **Is this an open thread?** A question nobody answered, a blocker raised but not addressed, a topic needing a decision but lacking one, or a "let me get back to you" without follow-through. Messages flagged `pending_reply: true` by the DMs fetcher (exec sent a message and never received a reply) are strong candidates here — treat them as open threads unless the thread itself contains a clear decision or commitment.
   - **None of the above?** Drop it. Filtering already happened in `slack-fetch`; if it slipped through and doesn't fit any category, it's noise that escaped.

4. **Split commitments by who.** For every commitment, compare the *who* to `user_identity`. If it's the exec, append to `user_commitments`. Otherwise to `others_commitments`. This split is non-negotiable.

5. **Apply the ambiguity rule.** If a message *could* be a decision OR an open thread (e.g. "I think we should go with X" — opinion or settled?), file it as **Open Thread**, never a Decision. If a commitment lacks either a clear *who* or a clear *what*, file it as Open Thread. **Never fabricate** a due date, a person, or a deliverable to make a message fit a category.

6. **Write the summary.** Two to three sentences describing what the main threads were over the window. Written so a reader who wasn't on Slack still gets the picture. Reference the top-signal items first; don't try to summarize every category.

7. **Return the four arrays plus summary.**

## Conservative defaults

- A message that "sounds like" a decision but isn't explicit — drop or file as Open Thread.
- A commitment with no due date — `due: "TBD"`. Do not infer from context like "soon" or "this week" unless the message literally said that.
- A reaction-only message (the exec reacted but didn't reply) — treat the reacted-to message as an Open Thread unless the message itself already contains a decision or commitment.
- A message in a thread where the most recent reaction is `resolved_reaction` (e.g. `✅`) — should have been filtered out by `slack-fetch`. If it gets here, drop it.

## Output ranking within categories

Within each category, order by:

1. Signal priority of the source message (per the framework's signal prioritization list)
2. Recency (newer first) as a tiebreaker

## What this skill does NOT do

- Does not fetch from Slack. That's `slack-fetch`'s job.
- Does not write the digest file. That's `slack-ingest`'s job.
- Does not dedupe — input is assumed already deduped by `slack-ingest`.
- Does not modify the input messages.
- Does not fabricate. Ever. When in doubt, drop or Open Thread.

## Additional resources

- **`references/atlas-slack-ingestion-framework.md`** — the full Atlas Slack methodology. Decisions/commitments/open threads definitions, examples, noise rules, signal prioritization, and output format details. Loaded into context on every run of this skill.
