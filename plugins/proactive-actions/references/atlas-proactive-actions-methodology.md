# Atlas proactive actions methodology

> Loaded by `run-proactive-actions` before processing any meeting debrief batch.

## The principle

The bottleneck after a meeting isn't identifying what needs to happen — it's acting on it fast enough that nothing falls through the cracks. The Atlas method: **classify first, then act**. Every action item from every debrief gets a bucket before anything is executed. The bucket determines what happens next. Nothing gets skipped. Nothing gets over-actioned.

## The four buckets

### CAN EXECUTE

**Criteria:** The agent has the tools, context, and authorization to complete this without any human involvement.

Examples: creating task board entries, updating project state files, writing internal documents or guides, drafting frameworks, updating knowledge base entries.

**Action:** Do it immediately. Create a task (owner: agent, status: done or in_progress). Log what was done.

### CAN DRAFT

**Criteria:** The work requires the user's voice, approval, or a judgment call — but the agent can produce a quality draft that shortens the user's work to review-and-send.

Examples: scripts, email drafts, proposals, training content, client-facing summaries, anything that will be sent externally.

**Action:** Write the draft to `brain/` or the appropriate location. Create a task (owner: agent, status: needs_review). Flag clearly: "Draft ready at [path] — needs your review before sending."

**Never publish, send, or schedule a CAN DRAFT item without explicit approval.**

### CAN CHASE

**Criteria:** Someone else committed to something in the meeting. Enough time has passed that a status check is appropriate.

**Timing rule:** Don't chase same-day commitments unless explicitly marked "ASAP" or "by EOD." The default window before chasing is 24 hours.

**Action:** Send a friendly status-check message to the person via the configured internal messaging tool. Keep it brief — a check, not a nag. Create a task (owner: agent, status: in_progress) to track the follow-up. If no response within 24 hours, escalate to the user in the next status report.

**Scope rule:** CAN CHASE only applies to internal team members. Never send autonomous follow-up messages to external parties (clients, prospects, vendors).

### NEEDS HUMAN

**Criteria:** The action requires the user to be present, make a judgment call, attend something, make a financial decision, or take an action only they can authorize.

**Action:** Create a task (owner: user, status: today or backlog based on urgency). Include full context from the meeting so the user doesn't need to re-read the debrief. Surface in the next start-of-day briefing or status report.

**Don't attempt. Don't skip. Don't block other actions waiting for it.**

## People pre-flight check

Before classifying or writing any output, for every person mentioned in the action items:

1. Check `memory/people/{name}.md` if it exists — look for role boundaries, corrections, and known mistakes
2. Check `memory/corrections.md` for that person's name
3. If a correction exists (e.g., wrong role assumed previously), ensure all output respects that boundary
4. This step is mandatory — skipping it is how wrong context leaks into action summaries

## Classification process

For each action item extracted from the debriefs:

1. **Identify the type of action** — what it is, who it's for, what it would take to complete it
2. **Check against the four bucket criteria** — is the agent authorized? Does it need human voice? Is it a commitment from someone else? Does it require human presence?
3. **Check AGENTS.md** — confirm the action type is authorized. For any action not explicitly pre-authorized, classify up (toward NEEDS HUMAN) rather than assuming permission.
4. **Assign the bucket and act accordingly**

When in doubt between CAN EXECUTE and CAN DRAFT: default to CAN DRAFT. The user can always convert a draft to execution; an action taken without approval can't be undone.

## Status report format

After processing all debriefs, send the user a structured summary:

```
Post-Meeting Actions — {Date}

Executed:
- {item} — {what was done} ✅

Drafted (needs your review):
- {item} — draft at {location}

Following up with team:
- {person}: {commitment} — message sent

On your plate (needs you):
- {item} — added to task board as {task reference}
```

If a section is empty, omit it from the report — don't include empty headers.

## Task board hygiene

- Every classified item gets a task board entry, regardless of bucket
- Source meeting goes in task notes: "From: {meeting title} {YYYY-MM-DD}"
- Tags: `proactive`, `meeting-action`, `follow-up` (as applicable)
- Agent-owned tasks are assigned to the agent label
- User-owned tasks are assigned to the user with urgency set from meeting context (today vs. backlog)

## Constraints

These constraints are non-negotiable:

- **Never send external messages autonomously.** External = clients, prospects, vendors, anyone outside the internal team. Always NEEDS HUMAN.
- **Never make commitments on the user's behalf.** If an action would commit the user's time, resources, or agreement, it's NEEDS HUMAN.
- **Drafts are always flagged.** No CAN DRAFT item gets published or sent without explicit approval.
- **Financial decisions are always NEEDS HUMAN.** No exceptions.
- **Confirm before irreversible actions.** Any action that can't be undone (deleting records, sending official communications, changing permissions) escalates to NEEDS HUMAN even if it would otherwise qualify as CAN EXECUTE.

## What good output looks like

- Every action item classified — nothing is left without a bucket
- CAN EXECUTE items are done before the report is sent
- CAN DRAFT items have complete, ready-to-review drafts
- CAN CHASE messages are friendly, brief, and specific about what was committed
- NEEDS HUMAN tasks have enough context that the user doesn't need to re-read the debrief
- Status report is scannable in under 60 seconds

## What bad output looks like (avoid)

- Leaving action items unclassified because they're ambiguous
- Sending CAN CHASE messages to external contacts
- Publishing or sending CAN DRAFT items without review
- Creating tasks without source meeting context
- Classifying financial or commitment items as CAN EXECUTE
- Chasing same-day commitments
