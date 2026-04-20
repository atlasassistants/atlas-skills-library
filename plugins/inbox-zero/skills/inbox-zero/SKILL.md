---
name: inbox-zero
description: Orchestrator skill — the single entry point for a full inbox management session. Sequences escalation detection, triage, follow-up tracking, label sweep, and reporting in the correct order based on time of day. Three modes — morning, midday, EOD.
when_to_use: User says "do the inbox", "run inbox zero", "check my inbox", "process my email", "morning emails", "EOD inbox", "midday check". Also runs on a scheduled trigger if configured. Do NOT use for a single specific sub-task (escalations only, follow-ups only) — invoke the relevant skill directly for those.
atlas_methodology: opinionated
---

# inbox-zero

Run a full inbox management session — the right skills, in the right order, for the time of day.

## Purpose

Running inbox skills out of order is how things go wrong: triaging before escalations means a Tier 1 alert gets buried in a batch. Running follow-ups before triage means threading against an unsorted inbox. Running the reporter mid-chain means incomplete data in the report. This skill enforces the correct sequence every time, adapts to the time of day, and handles failures without bailing on the whole session.

## Inputs

- **Mode** (optional) — `morning`, `midday`, or `eod`. If not given, inferred from current time: before ~11am = morning, ~11am–4pm = midday, after ~4pm = EOD.
- **Mode override** (optional) — pass explicitly to override time-based inference.

## Required capabilities

All capabilities required by the sub-skills (email read, label apply, draft create, state storage). See each skill's Required capabilities section.

## Steps

1. **Load the methodology reference.** `references/atlas-inbox-methodology.md` — the 9-label system, chain rules, and mode definitions.
2. **Determine mode** — from argument or time of day.
3. **Run pre-flight.** Invoke `health-check` — confirm voice guide is current, client profile is complete, credentials are valid. Non-fatal findings surface in the report; fatal findings (missing credentials, missing labels) halt the chain.
4. **Run label reconciliation.** Fix any inconsistencies in current label state before touching the inbox. Always runs first.
5. **Run `escalation-handler`.** Always second, before normal triage. If this fails fatally, halt the entire chain.
6. **Branch by mode:**

   **Morning / EOD (full triage):**
   - Run `inbox-triage` in full-triage mode — drain inbox in bounded batches until empty or safety cap
   - Run `follow-up-tracker` — scan `3-Waiting For`, draft due follow-ups
   - EOD only: run label sweep after triage completes

   **Midday (quick scan):**
   - Skip full triage
   - Run `escalation-handler` only (already done in step 5) + surface any urgent interrupts
   - Skip follow-up-tracker
   - Skip label sweep

7. **Run `inbox-reporter` last.** Always last. Pass all upstream JSON. Produce SOD (morning), midday one-liner, or EOD report.
8. **Surface to user.** Return the report plus any fatal errors encountered.

## Chain rules

- Label reconciliation → ALWAYS first
- `escalation-handler` → ALWAYS second; fatal failure halts chain
- Full triage → only morning and EOD
- `follow-up-tracker` → only morning and EOD
- Label sweep → only EOD, after triage
- `inbox-reporter` → ALWAYS last

## Error handling

- **Fatal errors** (missing credentials, escalation-handler crash, systemic triage failure): halt the chain, report what ran and what didn't
- **Non-fatal errors** (voice guide missing → skip drafting; individual message failures): log, skip, continue
- Never silently drop errors — always surface in the report

## Output

The output of `inbox-reporter` — a structured SOD report, midday one-liner, or EOD report. See `skills/inbox-reporter/references/report-templates.md` for formats.

## Customization

- **Mode thresholds.** Default time boundaries (11am for midday, 4pm for EOD) are adjustable.
- **Skip a step.** Any non-fatal step can be disabled per mode in this skill.
- **Schedule.** Wire to a CronCreate trigger for automated morning/EOD runs without manual invocation.

## Why opinionated

Order matters. Escalation-handler before triage is a hard rule — not a preference. Reporter last is a hard rule. The methodology reference encodes the reasoning. Clients customize timing and which optional steps run; they don't reorder the chain.
