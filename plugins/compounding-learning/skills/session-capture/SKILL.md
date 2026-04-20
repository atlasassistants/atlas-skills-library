---
name: session-capture
description: Fires during active work when something reusable was just built (an integration, workflow, data pattern, or repeatable process) or when explaining a concept required more than 2 minutes of back-and-forth. Classifies the capture as a skill, insight, or pattern and writes it to the right destination immediately — not at session end.
when_to_use: Fire when any of these signals appear during work — (1) something reusable was just built: an integration, pipeline, workflow, data pattern, or repeatable UI component that would apply to future problems; (2) an explanation or concept required >2 minutes of back-and-forth to resolve; (3) the same type of problem has now appeared for the second time (pattern trigger). Also fires on: "capture this", "log that insight", "extract this as a skill", "save this pattern", "we should remember this", "write that down", "don't forget this".
atlas_methodology: opinionated
---

# session-capture

Capture skills, insights, and patterns the moment they surface — not at session end.

## Purpose

The number one reason knowledge doesn't compound is timing. People plan to log it after they finish, and then the context is gone. This skill fires mid-session, at the moment the learning is freshest, and writes it to the right destination immediately. There is no end-of-session step.

## Inputs

- **The thing to capture** (required) — a skill just built, a concept just resolved, or a pattern that just appeared for the second time
- **Capture type** (inferred from context) — skill, insight, or pattern
- **Context** (optional) — project, client, or problem domain. Used to route and tag the capture correctly.

## Required capabilities

- **Knowledge base write** — create files at `brain/knowledge/skills/{name}.md` (for skills); append to `brain/knowledge/lessons-learned.md` (for strategic insights)
- **Memory write** — append to `memory/patterns.md` (execution patterns), `memory/decisions.md` (decision rationale), `memory/corrections.md` (technical gotchas); create `memory/people/{name}.md` (person insights)

## Steps

1. **Load the methodology reference.** `references/atlas-compounding-learning-methodology.md` — defines capture triggers, the skill template, the insight routing table, and anti-patterns.
2. **Classify the capture type:**
   - Was something reusable just built? → **Skill**
   - Did an explanation take >2 minutes? → **Insight** (route by subtype)
   - Same problem appearing for the second time? → **Pattern**
3. **For a Skill:** Apply the skill template from the methodology reference. Extract: name, what it does, inputs/outputs, steps to reproduce, gotchas, and the "if we needed this in 3 months on a different project, could we skip the learning curve?" test. Write to `brain/knowledge/skills/{name}.md`.
4. **For an Insight:** Route by subtype per the methodology reference:
   - Strategic/business → `brain/knowledge/lessons-learned.md`
   - Execution/workflow → `memory/patterns.md`
   - Decision rationale → `memory/decisions.md`
   - Technical gotcha → `memory/corrections.md`
   - Person insight → `memory/people/{name}.md`
5. **For a Pattern:** If the pattern is technical, also create a skill. If strategic, add to `memory/patterns.md` or `brain/knowledge/`. Write the pattern with: the signal that triggers it and the recommended response.
6. **Confirm back** in one line — what was captured and where it lives.

## Output

A short inline confirmation that doesn't interrupt the work:

```
Captured: Google Sheets → PostgreSQL sync pattern → memory/patterns.md
```

For a skill:

```
Skill extracted: google-sheets-postgres-sync → brain/knowledge/skills/google-sheets-postgres-sync.md
```

No long summaries. The capture shouldn't slow the session.

## Customization

Common things clients adjust:

- **File paths.** Default paths assume Atlas vault structure. Override to match your knowledge base layout.
- **Skill template.** The default extraction template is in `references/atlas-compounding-learning-methodology.md`. Edit it to match your team's preferred skill format.
- **Insight routing table.** The default maps insight types to destinations. Add destinations or change routing logic to match your system.
- **The 2-minute threshold.** Adjust how much back-and-forth qualifies as an insight trigger.

## Why opinionated

The timing rule and the routing table are what make this work. Logging "later" consistently fails — the context that made it valuable is gone. Routing everything to one file creates noise that makes the knowledge base unsearchable. The methodology encodes both disciplines: fire immediately, route precisely.
