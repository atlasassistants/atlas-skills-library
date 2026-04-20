---
name: correction-promote
description: When the user gives a correction, behavioral feedback, or flags a mistake — log it to corrections.md immediately AND promote a rule to AGENTS.md. Always both destinations, every time. The detail lives in corrections.md. The rule that prevents recurrence lives in AGENTS.md. Confirm back that both were written.
when_to_use: Fire on any correction, behavioral feedback, or explicit mistake signal from the user. Trigger phrases: "no, not like that", "stop doing X", "I already told you this", "that's incorrect", "don't do that again", "wrong approach", "you got that wrong", "that's not right". Also fires on: "log this correction", "add this to AGENTS.md", "make a rule about this". Does not require the user to specify where to log — that's automatic.
atlas_methodology: opinionated
---

# correction-promote

Log every correction in two places — the detail record and the prevention rule. Always both.

## Purpose

Corrections are the highest-value captures in the system. They represent something that actually went wrong, with a real human saying "this isn't right." If that signal only lives in `corrections.md` (which may not load at every session start), the next session makes the same mistake. `AGENTS.md` loads every session — that's where the rule that prevents recurrence must live. Having to give the same feedback twice means the system broke trust.

## Inputs

- **The correction** (required) — what was wrong, what the right approach is, any context the user provides
- **Correction type** (inferred):
  - Behavioral or procedural mistake → rule in `AGENTS.md`
  - Identity, values, or communication style → `SOUL.md` if the agent uses one (in addition to AGENTS.md)

## Required capabilities

- **Memory write** — append to `memory/corrections.md`
- **Rules file write** — add or update a rule in `AGENTS.md`

## Steps

1. **Load the methodology reference.** `references/atlas-compounding-learning-methodology.md` — the Correction Promotion Gate and the "always both" rule.
2. **Log to `memory/corrections.md` immediately.** Full detail, using this format:
   ```
   ## YYYY-MM-DD — {Short title}
   **What happened:** {brief description of the mistake}
   **Correction:** {what the right approach is}
   **Context:** {project / client / situation}
   ```
3. **Extract the principle.** Every correction contains a principle — what rule, if followed, would have prevented this? Write it as a single declarative statement in present tense.
4. **Write the rule to `AGENTS.md`.** Format:
   ```
   Rule {N} (YYYY-MM-DD, ref: corrections.md {date}): {Rule statement.}
   ```
   Append under the relevant section or create a new rule with the next available number.
5. **If the correction is about identity, values, or communication style:** also write to `SOUL.md` if the agent uses one.
6. **Confirm back.** Always confirm both destinations were written: "Logged in corrections AND promoted to AGENTS.md Rule [N]."

## Output

```
Correction logged ✅

corrections.md: "2026-04-21 — Don't send external messages without approval"
AGENTS.md Rule 14 added: "Never send messages to external parties (clients, prospects, vendors) without explicit approval. Internal team only for autonomous follow-ups."
```

## Customization

Common things clients adjust:

- **`corrections.md` location.** Default is `memory/corrections.md`. Override for your vault structure.
- **`AGENTS.md` path and rule numbering.** Default is `AGENTS.md` at the agent root. If your rules file has a different path or uses a different numbering convention, adjust here.
- **`SOUL.md` routing.** Only applies if the agent uses a SOUL.md file. Skip this step if not applicable.

## Why opinionated

The "always both" rule has no exceptions because every exception scenario is wrong:

- "Only log if it seems serious" → fails when you misjudge seriousness in the moment
- "Promote to AGENTS.md later" → later doesn't happen; the next session starts without the rule
- "The user will remember to mention it again" → the user gave feedback once; that's all they should ever have to do

The rule: receive correction → log detail → extract principle → write rule. Every time. No judgment required about whether this one deserves it.
