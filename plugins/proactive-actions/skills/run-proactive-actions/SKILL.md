---
name: run-proactive-actions
description: Scan all meeting debriefs from today (or a specified date), extract every action item and commitment, classify each into one of four buckets (CAN EXECUTE / CAN DRAFT / CAN CHASE / NEEDS HUMAN), and process each bucket. Produces a structured status report for the user.
when_to_use: Runs automatically after a batch of meeting debriefs is processed. Also triggered manually: "run proactive actions", "check action items", "what can you handle from today's meetings", "process today's action items", "post-meeting actions". Can be scoped to a specific date, a specific meeting, or the full day's batch.
atlas_methodology: opinionated
---

# run-proactive-actions

Classify every action item from today's meetings. Execute, draft, chase, or escalate — and report back.

## Purpose

After meetings, there are always things to do — but not all of them require the user. This skill separates the work the agent can handle autonomously from the work that needs a human, and then acts. The goal: by the time the user reads the status report, routine follow-up is already done.

## Inputs

- **Debrief files** (required) — structured meeting debrief files for the target date. Default: today's debriefs at `brain/meetings/debriefs/YYYY-MM-DD-*.md`. Can be scoped to a specific path or date.
- **Date scope** (optional) — defaults to today. Pass "yesterday" or a specific date to process a different batch.

## Required capabilities

- **Meeting debrief read** — read and parse structured debrief files (decisions, action items, commitments from others)
- **Task system write** — create tasks with owner, status, source, and tags
- **Messaging send** — send internal status-check messages (internal team only)
- **File write** — write drafts to `brain/` or appropriate location
- **Rules file read** — read `AGENTS.md` before any autonomous action

## Steps

1. **Load the methodology reference.** `references/atlas-proactive-actions-methodology.md` — the four-bucket classification rules, timing constraints, constraints, and status report format.
2. **Check AGENTS.md.** Read the rules file. Confirm which action types are pre-authorized. Note any constraints that affect classification.
3. **Run the people pre-flight check.** For every person mentioned in the debriefs, check `memory/people/{name}.md` and `memory/corrections.md`. Correct any role or context errors before proceeding.
4. **Load debrief files.** Read all debrief files in the target date range. Extract:
   - User's action items (things the user committed to)
   - Commitments from others (things other people committed to)
   - Any decisions requiring follow-through
5. **Classify every item** into one of four buckets per the methodology reference. When in doubt between CAN EXECUTE and CAN DRAFT: default to CAN DRAFT.
6. **Process CAN EXECUTE items.** Do the work. Create a task (owner: agent, status: done or in_progress). Log what was done.
7. **Process CAN DRAFT items.** Write the draft to `brain/` or the appropriate location. Create a task (owner: agent, status: needs_review). Note the draft location clearly.
8. **Process CAN CHASE items.** Check timing — don't chase same-day commitments unless marked ASAP. Send a brief, friendly status-check message via the configured messaging tool. Create a task (owner: agent, status: in_progress).
9. **Process NEEDS HUMAN items.** Create a task (owner: user, status: today or backlog based on urgency). Include full meeting context in task notes.
10. **Send the status report.** Use the format from the methodology reference. Send to the user's configured escalation channel.

## Output

```
Post-Meeting Actions — 2026-04-21

Executed:
- Created task: "Prep onboarding doc for new hire" (owner: atlas, status: done)
- Updated project state: atlas-skills-library/state.md with Q2 milestone

Drafted (needs your review):
- Email to Acme re: Q2 proposal timeline — draft at brain/drafts/2026-04-21-acme-followup.md

Following up with team:
- Sam Chen: "Review updated SLA doc by Friday" — message sent via Slack

On your plate (needs you):
- Approve budget increase for vendor X — added to task board (today, high priority)
- Call with legal re: contract terms — added to task board (backlog)
```

## Customization

Common things clients adjust:

- **Debrief file path.** Default is `brain/meetings/debriefs/YYYY-MM-DD-*.md`. Override to match your debrief location.
- **Chase timing threshold.** Default is 24 hours. Adjust in this SKILL.md for faster or slower cadences.
- **Classification overrides.** Edit the four-bucket rules in `references/atlas-proactive-actions-methodology.md` to match your agent's specific authorization scope.
- **Status report destination.** Configure the escalation channel in first-run setup. Can be a DM, an ops channel, or an email.
- **Task owner labels.** Default uses "atlas" and the user's name. Change to match your task system's labeling conventions.

## Why opinionated

The classification rules are opinionated because the failure modes are asymmetric. Over-actioning (executing things that needed approval) damages trust and can't be undone. Under-actioning (leaving everything on the user) defeats the purpose. The four-bucket framework and the constraints in the methodology reference encode the safe defaults — the line between what an agent should do autonomously and what must stay with the human.
