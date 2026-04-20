---
name: follow-up-tracker
description: Manages the 3-Waiting For queue. Tracks every thread where the exec sent something and is waiting for a reply. Applies cadences by category (revenue/internal/vendors), drafts follow-up messages in exec voice, escalates exhausted threads to 5-Follow Up for exec decision.
when_to_use: Called by inbox-zero orchestrator during morning and EOD sessions. Also invoked directly: "check follow-ups", "what am I waiting on", "any follow-ups due", "check waiting for", "run follow-up tracker". Skip midday — runs morning and EOD only.
atlas_methodology: opinionated
---

# follow-up-tracker

Track every waiting thread, apply cadences, draft follow-ups, escalate exhausted threads.

## Purpose

A `3-Waiting For` label with no cadence behind it is just a pile. This skill gives every waiting thread a structured timeline — how long to wait before following up, how many times to try, and what to draft at each step. The exec never has to remember what they're waiting on.

## Inputs

- **Exec email address** (required) — used to identify threads where the exec sent the last message
- **Team delegation map** (required for internal classification) — read from `client-profile/team-delegation-map.md`

## Required capabilities

- **Email read** — fetch all threads in the `3-Waiting For` label; read thread history to detect replies
- **Label apply** — remove `3-Waiting For`, apply `5-Follow Up` for exhausted threads
- **Draft create** — create follow-up draft replies in exec voice
- **State storage** — read/write cadence state in `.plugin-state.json` (which cadence step has fired per thread)

## Steps

1. **Load references.** `skills/follow-up-tracker/references/follow-up-cadences.md` — cadence timing, classification rules, drafting templates, non-negotiable drafting constraints.
2. **Fetch all `3-Waiting For` threads.**
3. **Per thread, classify into one of four buckets:**
   - **Bucket 0 (invalid):** No exec-sent outgoing message in the thread. Remove `3-Waiting For`, re-triage.
   - **Bucket A (reply received):** Someone replied. Remove `3-Waiting For`, re-triage the response through the decision tree.
   - **Bucket B (follow-up due):** Cadence step is due today based on days since labeling. Draft follow-up in exec voice, leave in `3-Waiting For`.
   - **Bucket C (cadence exhausted):** All steps fired with no reply. Move to `5-Follow Up`, flag for exec decision.
4. **Classify each valid thread** by cadence category:
   - Internal if recipient domain matches team-delegation-map
   - Revenue if subject/body contains revenue keywords OR thread has `0-Leads` label
   - Vendor/External: default
5. **For Bucket B:** Apply the due cadence step. Draft using exec voice guide. Keep it 2–3 sentences, thread correctly, one ask, give an exit. Create draft — never send.
6. **For Bucket A:** Clear `3-Waiting For`, pass response to triage decision tree.
7. **For Bucket C:** Apply `5-Follow Up`. Flag in session output.
8. **State check:** Only fire one cadence step per thread per session. If multiple steps are overdue (gap between sessions), fire the step matching the current day count — not all missed steps.
9. **Return summary JSON.**

**Gmail implementation:** `implementations/gmail/skills/follow-up-tracker/check_followups.py`

## Output

```json
{
  "skill": "follow-up-tracker",
  "status": "ok",
  "summary": {
    "scanned": 12,
    "replies_received": 3,
    "due_today": [
      {"to": "prospect@acme.com", "subject": "Q2 proposal", "days_waiting": 4, "cadence_step": "day_4", "category": "revenue"}
    ],
    "escalations": [
      {"to": "vendor@example.com", "subject": "Contract renewal", "days_waiting": 21}
    ],
    "drafts_created": 2,
    "still_waiting": 6
  }
}
```

## Customization

- **Cadence timing.** All timing (Day 1/2/4/7 for revenue, Day 1/3/5 for internal, Day 3/Week 2/Week 3 for vendors) is defined in `follow-up-cadences.md`. Adjust per exec preference.
- **Classification rules.** Revenue keyword list and internal domain matching are in `follow-up-cadences.md`. Add keywords or domains as needed.
- **Max drafts per session.** Default: one draft per thread per session. Override if exec prefers batch catch-up.

## Why opinionated

Cadence timing and classification aren't negotiable — they're what make the system reliable. An exec who doesn't know which cadence a thread is on, or who has to manually decide "is this revenue or vendor?", is doing the work the skill should do. The classification rules encode that judgment once.
