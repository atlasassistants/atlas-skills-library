# proactive-actions — Setup Instructions

> Follow these steps before running `run-proactive-actions` for the first time.

## What requires setup

This plugin takes autonomous actions — sending messages, creating tasks, writing files. Three things must be wired up before it runs safely:

1. **Meeting debrief source** — where it reads action items from
2. **Task system** — where it logs and tracks work
3. **Messaging capability** — how it sends internal follow-ups

It also requires an `AGENTS.md` (or equivalent rules file) that the skill checks before every autonomous action. Without it, the skill will not proceed.

---

## Setup step 1: Confirm meeting debrief source

The skill reads debrief files to extract action items. These are typically produced by the `meeting-ops` plugin.

- **Default path:** `brain/meetings/debriefs/YYYY-MM-DD-*.md`
- **Default format:** Atlas debrief format (decisions / action items / commitments from others / open threads)

If your debriefs live somewhere else or use a different format:
1. Note the file path and naming convention
2. Edit `skills/run-proactive-actions/SKILL.md` — update Step 1 to point to your debrief location
3. If the format differs from the Atlas standard, update Step 2 to describe how to parse your format

**Using `meeting-ops`?** No changes needed — the formats are compatible out of the box.

---

## Setup step 2: Wire up the task system

The skill creates tasks for every action item it processes.

Configure the following:
- **Task system tool** — which task system the agent has access to (Linear, Todoist, Things, a markdown file, etc.)
- **Owner labels** — what to call agent-owned tasks vs. user-owned tasks in your system (e.g., "atlas" vs. your name)
- **Source tag** — the skill tags tasks with `proactive` and `meeting-action` by default. Confirm these tags exist in your system or adjust the labels.

Note your configuration in `skills/run-proactive-actions/SKILL.md` under the Inputs section.

---

## Setup step 3: Wire up messaging

The skill sends status-check messages to internal team members when chasing outstanding commitments. It also sends a summary report to the user after each run.

Configure:
- **Internal messaging tool** — which tool the agent uses to send messages (Slack, Teams, etc.)
- **Internal team scope** — which contacts are "internal" (the skill only sends to these contacts autonomously). List them or define the scope (e.g., "anyone in the company workspace").
- **User report destination** — where to send the end-of-run summary (DM, ops channel, etc.)

**Important:** The skill never sends messages to external parties (clients, prospects, vendors) without explicit approval. Confirm your internal scope is correctly defined.

---

## Setup step 4: Confirm AGENTS.md is readable

The skill checks `AGENTS.md` before every autonomous action to confirm what it's authorized to do.

- Confirm `AGENTS.md` exists at the root of the agent's context
- Confirm it contains any permission rules relevant to this plugin (e.g., which actions require approval, which are pre-authorized)
- Confirm the agent can read it at session start

If you don't have an `AGENTS.md`, create a minimal one:

```markdown
# AGENTS.md

## Proactive actions permissions
- Task creation: pre-authorized
- Draft writing: pre-authorized (review required before publishing)
- Internal messaging (team only): pre-authorized
- External messaging: requires explicit approval
- Financial decisions: requires explicit approval
```

---

## Setup step 5: Verify

Run a test with a known debrief file:

```
Run proactive actions on yesterday's debriefs.
```

Confirm:
- The skill finds and parses the debrief
- Action items are classified into the four buckets
- Tasks appear in your task system
- The summary report reaches you via the configured channel

---

## Notes

- **Chase timing:** The skill won't chase same-day commitments by default. Don't be alarmed if no chase messages go out on day one — this is by design.
- **Drafts are never published automatically.** Any CAN DRAFT item is written to a file and flagged for your review. Nothing gets sent.
- **The skill runs on today's debriefs by default.** Pass a specific date or path if you want to process a different batch.
