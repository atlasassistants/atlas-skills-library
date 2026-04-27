---
name: extract-ideal-week
description: Onboards an executive's ideal week into a structured, enforceable document. Explains the concept, checks if one is already documented, parses it if so, otherwise interviews the exec with Atlas's standard 10 + 3 questions (week rhythm + zone of genius), synthesizes the answers into a canonical format with rule buckets and protected blocks, and confirms with the exec before saving. Resumable mid-flow.
when_to_use: Run before any other ideal-week-ops skill. Trigger phrases — "set up ideal week", "extract ideal week", "onboard ideal week", "document the exec's calendar rules", "build the ideal week ruleset", "we need an ideal week for [exec]". Also trigger automatically when scan-ideal-week reports that no ideal week document exists at the configured path.
atlas_methodology: opinionated
---

# extract-ideal-week

Document the exec's ideal week as a structured, enforceable ruleset — once, with the exec's confirmation, in a canonical format the scan skill can read.

## Purpose

The scan skill can only flag what's been written down. This skill writes it down. Two paths: parse an existing document the exec has, or interview the exec from scratch using Atlas's standard question set. Either way, the output is the same shape — a single ideal-week document at the configured path, with the exec's sign-off.

## Inputs

- **Existing ideal-week document** (optional) — pasted contents or a path. If provided, the skill parses and re-shapes into the canonical format rather than re-asking.
- **Exec availability for interview** — if no document exists, the skill walks through 10 rhythm questions and 3 zone-of-genius questions. Anyone with the answer can provide it (the exec, an assistant, an AM) — not all questions need to come from the exec directly.

## Required capabilities

- **File read + write** — read existing documents the exec points to; write the final ideal-week document; read and write a small marker file to support resume mid-interview
- **Conversational interview** — ask one question at a time, accept free-form answers, paraphrase back for confirmation

## Steps

### 0. Phase detection (always first)

Before doing anything else, check state in this order:

1. Does a document exist at the configured `ideal_week_path` (default `client-profile/ideal-week.md`)? → If yes, ask the user "an ideal week already exists at <path>. Do you want to (a) view it, (b) update it, or (c) re-extract from scratch?" Branch accordingly.
2. Does a `.extract-in-progress.json` marker exist next to the configured path? → If yes, this is a resumed session. Load the marker, skip questions already answered, continue from the last unanswered one.
3. Otherwise → fresh extraction. Continue to step 1.

### 1. Explain what an ideal week is

Before asking any extraction questions, load and walk the user through `references/what-is-an-ideal-week.md` (the plugin-wide reference). This is non-negotiable — people interpret "ideal week" differently, and the skill's questions assume Atlas's specific definition (rhythms + protected blocks + rule buckets + zone of genius). Skip only if the user explicitly confirms they already know the framework.

### 2. Check for existing documentation

Ask the user directly:

> "Do you already have your ideal week documented somewhere — in a doc, a file, a calendar template, anything? If yes, share the path or paste the contents and I'll work from that. If no, I'll walk you through the questions to extract it now."

- **Existing doc provided** → go to step 3 (parse).
- **None** → go to step 4 (interview).

Do not guess locations or auto-search the filesystem. Ask explicitly.

### 3. Parse existing documentation

Read the document the user provides. Extract the following fields into the canonical format defined in `../../references/ideal-week-format.md`:

- Workday boundaries (start time, end time, weekend rules)
- Day-by-day rhythm (theme + time blocks per weekday)
- Protected blocks (non-negotiable times)
- Rule buckets — ALWAYS / NEVER / PREFER / FLEXIBLE
- Default meeting lengths by type
- VIP overrides
- Zone of genius (what only the exec can do; what drains them; what to delegate)

For any field the existing document does not cover, ask the corresponding question(s) from `references/extraction-questions.md`. Do not invent answers. Skip to step 5 once the canonical document is filled.

### 4. Interview from scratch

Walk through the 10 + 3 questions in `references/extraction-questions.md`, one at a time. Rules:

- **One question per turn.** Never batch questions — people lose patience and answers get shallow.
- **Free-form answers.** Don't constrain to multiple choice. Paraphrase back what you heard before moving on.
- **Save after every answer.** Write the running state to `.extract-in-progress.json` next to the configured path. This makes the flow resumable.
- **Anyone can answer.** If someone already knows the answer (e.g., "his lunch is always 12-1"), accept it and move on. Mark which person each answer came from.
- **Don't ask what's been answered.** If a previous answer covered a later question, skip the later one and note the source answer.

After all 13 questions are answered, synthesize them into the canonical format per `../../references/ideal-week-format.md`. Use `../../references/example-ideal-week.md` as the structural reference for the output.

### 5. Display and confirm

Show the synthesized document to the user. Ask explicitly:

> "Here's what I captured. Read through it. Tell me anything to change, add, or remove. I'll only save once you say it's right."

Iterate on edits in conversation. Do not save until the user explicitly confirms.

### 6. Save

Write the confirmed document to the configured `ideal_week_path`. Default location: `client-profile/ideal-week.md` in the user's workspace. Create parent directories if needed. Delete the `.extract-in-progress.json` marker.

### 7. Configure notification channel and recipient

The scan skill needs two settings to deliver its daily ping. Ask the user, in order:

1. **Channel** — "Where should the daily scan notification be delivered? Options: `slack`, `imessage`, `gmail`, `outlook`, or `file` (writes to a local markdown file)."
2. **Recipient (target)** — "Who should receive it? This is the Slack handle, email address, phone number, or file path the message will be sent to. Often the executive themselves, the EA, or a shared channel both are in — pick one primary recipient."

**Before saving, surface the self-notification trap if it applies.** If the chosen channel is `slack` or `imessage`, tell the user explicitly:

> "Heads up — if the recipient is your own account (your own Slack handle from your own connected workspace, or your own number on iMessage), you will NOT be notified. Slack does not push self-DMs and iMessage does not notify messages sent to your own Apple ID — the message lands silently. For self-pinging, switch to `gmail` or `outlook` (the email lands in your inbox AND in Sent, with normal notifications). For `slack` or `imessage`, set the recipient to a different person — typically the EA's handle, or a shared channel both of you are in. Want to change either setting before I save?"

Let the user adjust. Do not write the config until they confirm.

Then write `.claude/ideal-week-ops.local.md` in the user's workspace with at minimum these keys:

```yaml
---
ideal_week_path: <path saved in step 6>
notification_channel: <chosen channel>
notification_target: <chosen recipient>
---
```

If the file already exists, update only `notification_channel` and `notification_target` (and `ideal_week_path` if it changed) — do not overwrite other settings the user may have configured (`calendar_provider`, `scan_schedule`, `dry_run`, etc.). Create parent directories if needed.

### 8. Offer to set up a recurring scan

After save, ask:

> "Want to set up a recurring scan? Recommended cadence: weekdays 5pm (flags tomorrow) and weekdays 7am (flags today) — one notification per run. Or you can skip this and invoke the scan manually any time with phrases like 'scan calendar' or 'what's wrong with tomorrow'."

If yes, walk the user through registering the recurring trigger via their runtime's mechanism. The plugin does not auto-configure scheduling — see `../../README.md` §4 for runtime-specific options (Cowork Scheduled tasks, Claude Code `/schedule`, GitHub Actions cron, OS cron via the helper script, etc.).

If no, confirm they can invoke `scan-ideal-week` on demand any time, and that they can re-run this skill later to set up the schedule.

## Output

A confirmed, saved ideal-week document at the configured path. Final message:

```
Ideal week saved to <path> ✅

Contains: 5 weekday rhythms, N protected blocks, M rules across ALWAYS / NEVER / PREFER / FLEXIBLE, K VIP overrides, zone-of-genius notes.

Schedule: <set up | not set up — run scan-ideal-week manually>

Next: run scan-ideal-week to do the first calendar scan, or wait for the next scheduled run.
```

## Customization

- **Question set.** The 10 + 3 questions in `references/extraction-questions.md` are Atlas's standard. Add or remove for specific clients — but keep the count low. Long interviews produce shallow answers.
- **Output location.** Default `client-profile/ideal-week.md`. Override in `.claude/ideal-week-ops.local.md`.
- **Resume marker.** `.extract-in-progress.json` filename is fixed — the skill looks for that exact name. Don't rename without updating the skill body.
- **Save format.** Markdown with structured sections per `../../references/ideal-week-format.md`. The scan skill parses this format directly. If you change the format, you must also update the scan skill's parser.

## Why opinionated

Atlas has a battle-tested method for what to capture (and what to leave out) when documenting an exec's ideal week. The 10 + 3 question set, the rule-bucket structure (ALWAYS / NEVER / PREFER / FLEXIBLE), and the rhythm-by-weekday format come from Atlas's experience running this extraction with executives across roles. The full framework lives in `references/atlas-ideal-week-extraction-framework.md`. Clients wanting a different framework should fork the references — keep the skill body stable.
