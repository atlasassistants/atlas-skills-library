---
name: thread-close
description: Run the Thread / Session Close Gate before wrapping up any thread, session, or conversation. Asks the compound test question, extracts any final learnings not already captured mid-session, and gates closure until the compound test passes. Use whenever a task is complete, a question has been answered, or a session is winding down.
when_to_use: Fire when a thread or session is winding down — solution delivered, question answered, task complete. Trigger phrases: "we're done", "that's it", "thanks", "wrap up", "close this out", "we're finished", "session handoff", "write a handoff", "what did we learn", "are we done here". This is a gate, not an optional step — the thread does not close until capture is confirmed.
atlas_methodology: opinionated
---

# thread-close

Run the close gate before ending any thread — ask what we learned, capture it, then close.

## Purpose

Sessions are independent contexts. If the learning from a session isn't written down before the session ends, the next session starts from zero. The thread-close gate makes capture mandatory — it is not a suggestion and it has no exceptions. The thread doesn't get marked done until the compound test passes.

## Inputs

- **Session context** (required) — what was worked on, what problems were solved, what was built or decided
- **Existing captures this session** (optional) — any skills, insights, or patterns already captured mid-session via `session-capture`. These don't need to be recaptured — the gate just needs to confirm they exist.

## Required capabilities

- **Knowledge base write** — write final captures to `brain/knowledge/skills/` or `brain/knowledge/lessons-learned.md`
- **Memory write** — write to appropriate `memory/` files per the routing table

## Steps

1. **Load the methodology reference.** `references/atlas-compounding-learning-methodology.md` — the Thread Close Sequence and the Compound Test definition.
2. **Detect the wind-down.** Confirm the session is actually wrapping up (solution delivered, task complete, user signals closure).
3. **Ask the close gate question:** "Are we done here? What did we learn that saves >10 minutes next time? Any new skills to extract?"
4. **Run the Compound Test:** "If a fresh session started this same task tomorrow, would it be faster because of what we logged?"
   - If yes → proceed to close
   - If no → identify what's missing and capture it before closing
5. **Extract any remaining learnings** not already captured mid-session. Apply `session-capture` logic for each one.
6. **Write any new captures** to the appropriate files (skill, insight, or pattern, per the routing table in the methodology reference).
7. **Close the thread** — confirm closure with ✅ or the equivalent signal for the current channel.

## Output

When the gate passes cleanly:

```
Thread close gate — passed ✅

Captured this session:
- Skill: google-sheets-postgres-sync → brain/knowledge/skills/
- Insight: Zapier webhook delays are unreliable for time-sensitive flows → memory/corrections.md

Compound test: ✅ Fresh session tomorrow would skip ~45 minutes of debugging.
```

When everything was already captured mid-session:

```
Thread close gate — passed ✅

Nothing new to capture — session-capture already logged everything mid-session.
Compound test: ✅
```

## Customization

Common things clients adjust:

- **Close gate question wording.** Edit the phrasing in this skill to match your team's language.
- **Compound test threshold.** Default is >10 minutes saved. Adjust to match your work cadence.
- **✅ signal.** In Slack workflows, this may be a reaction emoji. In document threads, a written confirmation. Customize for the channel.

## Why opinionated

The gate has to be hard — not a suggestion. Any version of "wrap up unless there's something to capture" produces the same result as no gate at all. The methodology makes this a mandatory stop: the thread doesn't close until the compound test passes. That's the only version that works.
