# Decision Tree + Label Sweep Rules

> The triage logic for the Atlas Inbox Zero system. Extracted from Sections 1, 4, and 5 of `atlas-inbox-rules-reference.md`. Every email processed by `inbox-triage` flows through the decision tree in this exact order.

---

## The 9 Atlas Labels

Every triaged email gets exactly ONE label. No email stays in the inbox unlabeled.

The operating model is: **bounded batches until zero, or until a safety stop.** The system should never try to load an entire large inbox into one agent pass.

| Label | Purpose | Applied when |
|-------|---------|--------------|
| `0-Leads` | Revenue opportunities | Sales inquiries, referrals, partnership offers with revenue potential |
| `1-Action Required` | Needs exec voice or decision | Exec decisions, personal replies only the exec should send, signatures, approvals, security/access items that should not be delegated |
| `2-Read Only` | FYI | Newsletters the exec wants, industry news, informational team updates |
| `3-Waiting For` | Pending responses | We sent something and are waiting for a reply |
| `4-Delegated` | EA or team handling | EA handles directly OR routes to a team member |
| `5-Follow Up` | Future action | Needs action later but not today |
| `6-Receipts/Invoices` | Financial records | Receipts, invoices, payment confirmations |
| `7-Subscriptions` | Automated | Newsletters, marketing, SaaS alerts |
| `8-Reference` | Tickets/confirmations | Calendar invites, meeting recordings, bookings |

`6`, `7`, and `8` are handled by filters at arrival — triage should rarely touch them.

---

## Decision Tree (per message)

1. **Spam / marketing** → archive (remove from inbox)
2. **Receipt / invoice** → `6-Receipts/Invoices`
3. **Calendar / booking / recording** → `8-Reference`
4. **Automated newsletter / SaaS notification** → `7-Subscriptions`
5. **Revenue-related** (sales inquiry, referral, partnership with revenue) → `0-Leads`
   - Guardrail: internal/team threads do NOT become `0-Leads` just because they mention pricing, contracts, terms, partnerships, or payment. Internal context wins and routes to `4-Delegated`.
   - Guardrail: existing account-management or vendor-support threads do NOT become `0-Leads` just because they mention pricing, billing, account status, or reactivation.
6. **Needs exec voice or decision?** (approval, signature, personal decision, exec's voice needed, or a true security/access exception) → `1-Action Required` + draft reply only when the next action is an outbound exec email
7. **Waiting for reply** (we sent something, awaiting response) → `3-Waiting For`
8. **FYI exec wants to see** (industry news, internal updates) → `2-Read Only`
9. **Everything else** → `4-Delegated` (EA reviews — the catch-all, NOT archive)

---

## Confidence Tagging

Every AI-classified item includes a confidence level:

- **deterministic** — pre-classifier decided (receipts, subscriptions, calendar)
- **high** — clear match, applied immediately
- **medium** — could go either way, applied but flagged in SOD: "medium confidence — EA verify"
- **low** — genuinely unsure → goes to `4-Delegated` with note: "unsure — best guess was [X] but confidence low. EA decide."

Output JSON per item:
```json
{
  "message_id": "...",
  "label": "1-Action Required",
  "confidence": "high",
  "reason": "exec approval explicitly requested in body"
}
```

---

## Critical Triage Rules

1. **Escalation check runs first, as a separate skill.** By the time `inbox-triage` processes a message, `escalation-handler` has already labeled anything urgent. Don't second-guess those items — they already have `1-Action Required`.

2. **CC + domain match → Delegated, NOT Read Only.** This is the single most common error. If Anna (Finance) is CC'd on a billing thread, that thread is `4-Delegated`, not `2-Read Only`. The reasoning: Read Only means "nothing needs to happen" — but if a team member is CC'd, something is happening.

3. **One label per email. Exactly one.** Never stack. If you're tempted to apply both `0-Leads` and `1-Action Required`, pick the more actionable one (`1-Action Required` — the exec needs to decide) and mention the revenue aspect in the report or draft, depending on whether a reply is actually needed.

4. **Draft responses only for reply-worthy `1-Action Required` items.** Not for Leads, not for Delegated, and not for review-only security/access/system notifications. Leads go in the SOD report for the exec to decide on. Delegated items are the EA's responsibility — the EA reviews and handles any needed forwards or replies.

5. **`1-Action Required` is not a generic "someone asked for something" bucket.** Use it only when the message genuinely needs the exec's personal voice, decision, approval, signature, or a narrow security/access intervention. If the EA can handle the reply, routing, coordination, or follow-up, it belongs in `4-Delegated` instead.

6. **Voice profile is required for drafts.** Before drafting any response, read `client-profile/exec-voice-guide.md`. If it's still the empty template, do NOT draft in generic AI voice. Flag it: "I can't draft this reply yet — exec-voice-guide.md isn't populated. Run `exec-voice-builder` first." Then label the item `1-Action Required` without a draft.

7. **Unlabel before relabel.** When changing a label (e.g., a `3-Waiting For` item got a response → should be re-triaged), remove the old label AND `INBOX` separately. `modify_message` handles both in one call.

8. **"Everything else" goes to `4-Delegated` — it doesn't go to Read Only or archive.** `2-Read Only` is for informational items the exec explicitly wants to see. `4-Delegated` is the catch-all: the EA reviews and decides the next step.

---

## Time-of-Day Modes

The triage skill supports three modes. Each is called by the `inbox-zero` orchestrator based on time of day, but the skill can also be invoked directly.

### Morning Sweep — 15 minutes
- **Goal:** inbox to zero before the exec starts their day.
- **Scope:** every message currently in `in:inbox`.
- **Order:** oldest first (process backlogs before new arrivals).
- **Actions per message:** decision tree → one label → move Atlas-labeled items out of Inbox immediately.
- **Drain behavior:** live morning runs continue batch-by-batch until there are no untriaged inbox items left, or a safety cap is hit. Dry-run previews only the first batch.
- **Drafts:** yes, only for `1-Action Required` items that genuinely need an outbound exec reply. Review-only security/access items stay surfaced without a Gmail draft.
- **Output:** count of items per label, list of `1-Action Required` items with draft IDs, any items skipped (voice profile missing, etc.).

### Midday Check — 10 minutes
- **Goal:** quick sanity pass, NOT a full triage.
- **Scope:** `in:inbox is:unread newer_than:6h`.
- **Order:** newest first.
- **Actions per message:**
  - VIP message → already caught by escalation-handler, skip.
  - Meeting change for today → label `1-Action Required` + surface to user.
  - Urgent team flag → label `1-Action Required` + draft if clearly an exec call.
  - Response to a `3-Waiting For` item → remove `3-Waiting For`, re-run the decision tree on the new message.
  - **Everything else → leave alone.** Do NOT full-triage at midday. Save it for EOD.
- **Drafts:** only for items that clearly need a reply in the next hour.

### EOD Review — 15 minutes
- **Goal:** inbox back to zero + label sweep + flag priorities for tomorrow.
- **Scope:** every message currently in `in:inbox`.
- **Order:** newest first (most recent context matters most at EOD).
- **Actions per message:** full decision tree, like morning.
- **Drain behavior:** live EOD runs continue batch-by-batch until there are no untriaged inbox items left, or a safety cap is hit. Dry-run previews only the first batch.
- **Extra step:** run label sweep AFTER triage (see below).
- **Output:** same as morning + sweep results.

### Batching and safety contract

This reference assumes all full-triage implementations follow these rules:

1. Fetch only the next bounded batch of untriaged inbox mail.
2. Classify and apply decisions for that batch.
3. Roll up summary state and discard unnecessary per-message body context from the previous batch.
4. Repeat until the next fetch is empty, the next fetch is smaller than the batch size, or the safety cap is reached.
5. If Gmail/API/platform limits or context limits are encountered, stop cleanly and report partial drain status rather than switching to unsafe behavior.

**Default bounds:** full triage batches of `100`, midday quick scan `50`, plus an implementation-level safety cap on total batches per run.

**Never do this:** fetch the entire inbox backlog in one giant call just because the goal is inbox zero.

---

## Label Sweep Rules

After EOD triage, the agent runs the label sweep to archive items in labels that have been acted on. Sweep rules come from `client-profile/label-sweep-rules.md` — these are the DEFAULTS shown to the exec during onboarding, which they kept or adjusted.

| Label | Default Rule | Check Logic |
|-------|-------------|-------------|
| `1-Action Required` | Archive once exec has replied | For each item, `thread_has_reply_from(thread_id, exec_email)` → if True, archive. If False and older than 48h → keep but re-flag in next SOD. |
| `2-Read Only` | Archive after 48h | For each item, check `internalDate` — if > 48h old, archive. |
| `3-Waiting For` | Handled by follow-up-tracker | Skip in label sweep — `follow-up-tracker` owns this label's lifecycle. |
| `4-Delegated` | Archive once routed team member has replied after delegation | For each item, check thread for a routed team-member reply that arrived after `4-Delegated` was applied → if True, archive. If False and > 72h → flag to EA in next report. If no team map is loaded, fail safe: keep the item in `4-Delegated` and only flag it for EA review rather than auto-archiving. |
| `5-Follow Up` | Stays until actioned | Skip in sweep — manual exec decision. Surfaces in SOD weekly. |
| `0-Leads` | Archive once actioned | Check for calendar event or reply in thread → archive if found. Otherwise leave (surfaces in SOD). |
| `6-Receipts/Invoices` | Already filtered at arrival | Safety-net clears `INBOX` only if one slipped through, but keeps the label for records/search. |
| `7`, `8` | Already filtered at arrival | Skip — nothing to sweep. |

**Sweep-specific rules:**
- Read rules from `client-profile/label-sweep-rules.md` on every run — don't hardcode.
- Use `thread_has_reply_from` on `gmail_client` for the reply checks.
- For `1-Action Required` 48h checks, compare `internalDate` (ms since epoch) to current time minus 172800000.
- Archive = `archive_message(id)` which removes INBOX label. Never delete.
- Log every sweep action: label → message count archived vs. left.

---

## Drafting Responses in Exec Voice

Before drafting a reply for a `1-Action Required` item:

1. Confirm the item truly needs an outbound exec reply, then read `client-profile/exec-voice-guide.md` (cached for the session).
2. If it's still a template (no real content under "Opens with:", etc.), STOP and flag. Don't generate generic drafts.
3. Read the original message body in full (not just the snippet).
4. Draft in 3-10 sentences maximum. Exec replies are short.
5. Use the exec's opening style, closing style, and 1-2 signature phrases.
6. If declining, use the exec's decline pattern (direct no / soft redirect / offer alternative).
7. If pushing back, match the exec's pushback tone.
8. Create the draft via `client.create_reply_draft(message, body, reply_all=<based on original>)`.
9. Log the draft ID in the triage output so the SOD report can link to it.

**Reply-all rule:** Mirror the original. If the exec was replying on a thread with multiple recipients, keep the CC. If it was 1-on-1, don't CC anyone.

**Subject handling:** Handled automatically by `create_reply_draft` — it adds `Re:` prefix if needed.

---

## Output Format (for Triage Scripts)

The triage scripts write JSON to stdout so the agent can consume results:

```json
{
  "mode": "morning" | "midday" | "eod",
  "scanned": 47,
  "labeled": {
    "0-Leads": 2,
    "1-Action Required": 5,
    "2-Read Only": 8,
    "3-Waiting For": 3,
    "4-Delegated": 11,
    "archived": 18
  },
  "drafts_created": [
    {"message_id": "...", "draft_id": "...", "subject": "...", "to": "..."}
  ],
  "skipped": [
    {"message_id": "...", "reason": "voice profile missing"}
  ],
  "errors": [
    {"message_id": "...", "error": "..."}
  ]
}
```

Label sweep output:

```json
{
  "sweep_run_at": "2026-04-11T17:30:00Z",
  "results": {
    "1-Action Required": {"checked": 12, "archived": 7, "reflag": 2, "kept": 3},
    "2-Read Only": {"checked": 8, "archived": 6, "kept": 2},
    "4-Delegated": {"checked": 11, "archived": 9, "flagged_ea": 1, "kept": 1},
    "0-Leads": {"checked": 3, "archived": 1, "kept": 2}
  },
  "errors": []
}
```
