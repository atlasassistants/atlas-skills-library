---
name: inbox-triage
description: Core daily triage workflow. Processes every inbox email through the Atlas 9-label decision tree in bounded batches, applies exactly one label per message, and drafts replies in exec voice for Action Required items that need an outbound response.
when_to_use: Called by the inbox-zero orchestrator during morning and EOD sessions. Also invoked directly: "triage my inbox", "process new emails", "label my inbox", "run triage". Do NOT use for escalation detection (use escalation-handler) or follow-up cadences (use follow-up-tracker).
atlas_methodology: opinionated
---

# inbox-triage

Process every inbox email through the decision tree, one label per message, in bounded batches.

## Purpose

A labeled inbox is a decision queue. Unlabeled email is noise. This skill turns every message into a classified item — one label, no exceptions, no stacking — so the exec only touches their inbox to review and act, not to sort.

## Inputs

- **Mode** (required) — `morning` (oldest-first, full drain), `midday` (newest-first, interrupts only), `eod` (newest-first, full drain + sweep)
- **Existing escalation output** (optional) — JSON from `escalation-handler`. Already-labeled escalation items are skipped in triage.

## Required capabilities

- **Email read** — fetch inbox messages with query, order, and batch size controls
- **Label apply** — apply exactly one Atlas label to a message; remove from inbox if archiving
- **Draft create** — create a draft reply in the exec's sent-from address (never send)
- **State storage** — read `client-profile/exec-voice-guide.md` for drafting; read `client-profile/team-delegation-map.md` for delegation classification

## Steps

1. **Load references.** `skills/inbox-triage/references/decision-tree.md` (label logic and sweep rules) and `client-profile/exec-voice-guide.md` (drafting voice). If voice guide is missing or stale, skip drafting and flag in output.
2. **Fetch a batch.** Retrieve up to 100 messages for full triage (50 for midday). Skip messages already labeled by `escalation-handler`.
3. **Run the decision tree per message** per `decision-tree.md`. Assign exactly one label. Assign a confidence score (deterministic / high / medium / low).
4. **Build the decisions batch.** For each message: label, archive flag, confidence.
5. **Apply the batch** using the email label capability. Apply labels and archive as decided.
6. **For `1-Action Required` items that need an outbound reply:** draft a reply in exec voice using `exec-voice-guide.md`. Only draft if an outbound reply is genuinely needed — not for review-only or security items.
7. **Loop** — fetch the next batch and repeat until inbox is empty or the safety cap is reached.
8. **EOD only:** after the final batch, run label sweep per the rules in `decision-tree.md`.
9. **Return summary JSON** — counts per label, drafts created, messages skipped, confidence breakdown, any errors.

**Gmail implementation:** `implementations/gmail/skills/inbox-triage/triage_inbox.py` (fetch and apply-batch subcommands) and `label_sweep.py` (EOD sweep).

## Output

```json
{
  "skill": "inbox-triage",
  "mode": "morning",
  "status": "ok",
  "summary": {
    "scanned": 47,
    "labeled": {"0-Leads": 2, "1-Action Required": 5, "2-Read Only": 8, "4-Delegated": 12, "6-Receipts/Invoices": 7, "7-Subscriptions": 13},
    "drafts_created": ["msg-id-1", "msg-id-2"],
    "confidence_flags": [{"id": "msg-id-3", "label": "1-Action Required", "confidence": "medium"}],
    "inbox_remaining": 0
  }
}
```

## Customization

- **Batch size.** Default 100 for full triage, 50 for midday. Reduce if context pressure is an issue.
- **Safety cap.** Default halts after N batches if inbox doesn't reach zero. Adjust to inbox volume.
- **Confidence flag threshold.** Default surfaces medium and low confidence items in the report. Override to surface only low.
- **Drafting opt-out.** Disable drafting per mode if exec prefers to write all replies themselves.

## Why opinionated

One label per message, applied in bounded batches, with a confidence score — these are the constraints that make triage reliable and auditable. The decision tree in the reference file encodes the actual logic; this skill enforces the discipline around how it runs.
