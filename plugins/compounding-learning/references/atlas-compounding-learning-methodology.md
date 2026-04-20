# Atlas compounding learning methodology

> Loaded by `session-capture`, `thread-close`, and `correction-promote` before processing any capture or close.

## The principle

Every working session contains knowledge that is worth more the second time than the first — but only if it's written down before the session ends. Sessions are independent contexts. If a skill, insight, or correction isn't captured before the session closes, the next session starts from zero. The Atlas method makes capture mandatory, not optional, and it happens **during** the session — not after.

The Compound Test: "If a fresh session started this same task tomorrow, would it be faster because of what we logged today?" If the answer is no, capture hasn't happened yet.

## Three capture triggers

Capture fires during work — not at session end.

### Trigger 1: Skill

**Signal:** Something reusable was just built — an integration pattern, a deployment workflow, a data transformation, a UI component, an API setup, a reporting pipeline.

**Test:** "If we needed this in 3 months on a different project, could we skip the learning curve?"

**Action:** Extract to `brain/knowledge/skills/{name}.md` using the skill template below.

### Trigger 2: Insight

**Signal:** An explanation or concept required more than 2 minutes of back-and-forth to resolve.

**Action:** Log immediately to the relevant destination:

| Insight type | Destination |
|---|---|
| Strategic or business | `brain/knowledge/lessons-learned.md` |
| Execution or workflow | `memory/patterns.md` |
| Decision rationale | `memory/decisions.md` |
| Technical gotcha | `memory/corrections.md` |
| Person-specific | `memory/people/{name}.md` |

### Trigger 3: Pattern

**Signal:** The same type of problem appears for the second time.

**Rule:** First time = solution. Second time = pattern. Patterns must be documented.

**Action:** If technical → also create a skill. If strategic → add to `memory/patterns.md` or `brain/knowledge/`. Write the pattern with: the signal that triggers it, the recommended response, and any exceptions.

## Skill template

Every extracted skill goes in `brain/knowledge/skills/{name}.md` with this structure:

```markdown
---
name: {skill-name}
description: {one-line description of what this skill does}
last_used: {YYYY-MM-DD}
tags: [{relevant tags}]
---

# {Skill Name}

## What it does
{1-2 sentence summary}

## When to use
{The signal or condition that makes this skill relevant}

## Inputs
- {input 1}
- {input 2}

## Steps
1. {Step}
2. {Step}

## Gotchas
- {Known failure modes or non-obvious constraints}

## Output
{What the skill produces}
```

## Thread / Session close gate

Before closing any thread or writing a session handoff, the following sequence runs — in order, without skipping:

1. **Ask the close gate question:** "Are we done here? What did we learn that saves >10 minutes next time? Any new skills to extract?"
2. **Run the Compound Test:** "If a fresh session started this same task tomorrow, would it be faster because of what we logged?" If no → go back and capture what's missing.
3. **Extract remaining learnings** not already captured mid-session.
4. **Write all new captures** to the appropriate files.
5. **Close the thread** — confirm with ✅ or equivalent.

This is a gate, not a suggestion. The thread doesn't close until capture is done.

## Correction promotion gate

When a correction or feedback is received, two things always happen — in order, both required:

1. **Log to `memory/corrections.md`** — full detail: what happened, what the correction was, date, context.
2. **Promote to `AGENTS.md`** — extract the principle from the correction and write a rule. Format: rule statement, date, reference to the corrections.md entry.

**Format for corrections.md:**

```markdown
## YYYY-MM-DD — {Short title}
**What happened:** {brief description of the mistake}
**Correction:** {what the right approach is}
**Context:** {project / client / situation}
```

**Format for AGENTS.md rule:**

```
Rule {N} (YYYY-MM-DD, ref: corrections.md {date}): {Rule statement in present tense.}
```

**Why both destinations are required:**

`corrections.md` is the detailed record — useful for audits and understanding patterns. `AGENTS.md` loads every session — it's what actually prevents recurrence. A correction that only lives in `corrections.md` will be forgotten at the next session start. Having to give the same feedback twice means the system broke trust.

## Anti-patterns

These patterns produce the illusion of capture without the benefit:

- **"I'll log it later."** End-of-session capture misses 70%+ of insights because context is gone. Log during the session.
- **"Too small to document."** If it took >5 minutes to figure out, it's worth a one-liner.
- **"The code IS the documentation."** Code shows WHAT, not WHY or WHAT WENT WRONG.
- **"We'll remember."** Sessions are independent contexts. If it's not written, it doesn't exist.
- **"I logged the correction."** Only logging to `corrections.md` without promoting to `AGENTS.md` means the next session will repeat the mistake.

## What good capture looks like

- **Specific.** "The Zapier webhook has a 30-second processing delay — don't use it for time-sensitive flows" is useful. "Zapier has delays" is not.
- **Actionable.** Any reader should know exactly what to do (or avoid) based on what was written.
- **Stored in the right place.** Strategic insights don't belong in `memory/corrections.md`. Technical gotchas don't belong in `brain/knowledge/lessons-learned.md`. Route matters.
- **Immediately findable.** A skill that lives in `brain/knowledge/skills/` but has a vague name isn't findable. Name it after the problem it solves.

## What bad capture looks like (avoid)

- Vague summaries that don't convey the actual learning
- Insights stored in a single catch-all file with no differentiation
- Corrections logged but not promoted to AGENTS.md
- Skill files that describe what was built but not the gotchas
- Missing the two-destination rule on any correction
