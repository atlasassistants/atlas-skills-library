# Inbox Report Templates

Source: Atlas Inbox Rules Section 9 + operational notes from Phases 3–4.

The reporter generates two reports: **SOD** (Start of Day) and **EOD** (End of Day). Both are short, scannable, and actionable — the exec reads them in under two minutes.

---

## Rules That Apply to Every Report

1. **One line per item.** Never wrap to multi-line bullets. If something can't fit on one line, it's too detailed — trim it.
2. **Specific names and subjects.** `Sarah @ Acme re: Q2 terms` is good. `A prospect` is not.
3. **Action needed is clear.** Every item in "Needs Your Decision" says what the exec has to do (`approve`, `Y/N`, `pick a time`, `reply`).
4. **Time estimates for exec decision items.** If the exec has to choose something, say how long it'll take.
5. **No fluff.** No emoji salad, no "here's what I did today!" narration, no weather, no motivational openings. Just the sections.
6. **Label categories match the label system.** Don't invent new buckets — use the 9 labels.
7. **If a section has zero items, omit the section entirely.** Don't print empty headers.
8. **Use emoji headers (⚡💰⏰✅📅).** They act as visual anchors so the exec can jump to the section they care about.

---

## SOD (Start of Day) Report — Inbox Section

This runs at the start of the exec's day after the morning sweep. It feeds into the broader SOD doc the EA produces for the exec — this skill only generates the **Inbox Management Update** section.

### Template

```
Inbox Management Update:

⚡ **Needs Your Decision** ({total_time} min)
1. [Person] re: [topic] — [draft ready / needs Y or N / 2 min]
2. [Subject] — [one-line context + what's needed / 3 min]

💰 **Revenue**
3. [Prospect/Lead] — [amount/opportunity] [I'll handle / scheduling call]
4. [Referral source] — [context]

⏰ **Following Up Today**
5. [Thread subject] ([X days no response])
6. [Thread subject] ([X days — check-in])

✅ **Handled For You**
7. [What was done — one line]
8. [What was done — one line]

📅 **Today's Email-Driven Actions**
9. [Time]: [Action] (docs in calendar invite)
```

### Section-by-section rules

#### ⚡ Needs Your Decision
- Pulls from: `1-Action Required` items that the morning triage surfaced (both escalation-handler's Tier 2 and inbox-triage's Action Required bucket).
- Format: `[Person/source] re: [topic] — [what the exec does] / [time estimate]`
- Include the time estimate even for 1-minute items. The total in the header is the sum.
- If a draft is ready, say `draft ready` so the exec knows to open Gmail and hit review.
- If no drafts are ready (e.g., voice guide was missing), say `draft pending` and note the reason.
- Sort by priority: Tier 1 escalations first (from escalation-handler), then by urgency/age.
- Target count: 3–7 items. More than 7 means something upstream is mislabeling and the exec's inbox is effectively drowning.

#### 💰 Revenue
- Pulls from: `0-Leads` items surfaced this session.
- Format: `[Prospect/Lead name or company] — [amount or opportunity], [EA action]`
- If there's an explicit dollar value, include it. If not, a one-line opportunity description.
- EA action = what the EA is doing with it: `scheduling call`, `I'll handle the intro`, `drafted warm reply`, `sent to [team member]`.
- Omit the section entirely if zero leads this session.

#### ⏰ Following Up Today
- Pulls from: `follow-up-tracker` scan output — specifically the `due_today` array.
- Format: `[recipient/thread subject] ([X days waiting], [cadence step])`
- Include what's in the drafts folder (`draft ready`) vs. what's pending exec decision (`Day 7 final — exec decides drop or keep`).
- Sort by urgency: escalations first, then Day 7 finals, then internal (Day 5), then revenue (Day 4, 2, 1), then vendors.
- Also surface `follow-up-tracker` escalations (exhausted cadences moved to `5-Follow Up`) as a separate bullet at the bottom: `Exhausted: [thread] — exec decides`.

#### ✅ Handled For You
- Pulls from: `inbox-triage` summary (items auto-archived, filtered, or labeled without needing exec attention — including `4-Delegated` items routed to the EA for review).
- Format: `[What] — [who/how]`. One line each.
- Examples:
  - `Invoice from Stripe — auto-labeled to 6-Receipts/Invoices`
  - `47 newsletters filtered to Subscriptions`
  - `12 receipts auto-labeled — no action needed`
  - `Calendar invite from [Name] — accepted, on your schedule`
  - `8 emails routed to 4-Delegated for EA review`
- Group by type when possible: instead of 47 individual newsletter lines, a single summary line with the count.
- Cap at ~5 lines. This section is a trust signal ("look, I did stuff") but it shouldn't bury the actionable items above.

#### 📅 Today's Email-Driven Actions
- Pulls from: calendar events triggered by emails the agent processed (accepted meetings, scheduled calls, follow-up deadlines).
- Format: `[Time]: [Action] ([context/link])`
- Only include items that came from email processing — not the exec's full calendar. That's a different skill.
- Examples:
  - `10:30am: Call with Sarah @ Acme (from Q2 terms thread)`
  - `2pm: Review quarterly report draft (from CFO request — Action Required)`
- Omit the section if there's nothing email-driven today.

---

## EOD (End of Day) Report — Inbox Section

This runs at the end of the exec's day after the EOD sweep. Shorter than the SOD — focused on what happened and what carries over.

### Template

```
Inbox EOD Summary:

**Today's Numbers**
- Processed: {total_processed} emails
- Drafts created: {drafts_count}
- Archived: {archived_count}
- Delegated to team: {delegated_count}

**Still in Your Queue**
- ⚡ Action Required: {count} items ({est_time} min)
- 💰 Leads: {count} items
- ⏰ Waiting For: {count} threads ({due_tomorrow} follow up tomorrow)
- 🔁 Follow Up: {count} items

**Carryover for Tomorrow Morning**
1. [Most urgent unresolved item] — [why]
2. [Next unresolved item] — [why]

**Label Sweep**
- {label}: archived {n} ({reason}), {kept} kept

**Alerts (if any)**
- [Any errors, stuck items, or things the exec should know about — e.g., "voice guide still empty — drafts skipped", "12 items flagged for re-flag after 48h no reply"]
```

### Section-by-section rules

#### Today's Numbers
- Pulls from: inbox-triage summary + follow-up-tracker output.
- Always in this order: Processed / Drafts / Archived / Delegated.
- If `processed == 0` (e.g., midday-only day), replace this section with a one-line note: `No full triage today — midday check only. X new items touched.`

#### Still in Your Queue
- Pulls from: Gmail label counts (use `client.search_messages` with `label:<name>` and read `resultSizeEstimate`).
- Only surface labels the exec interacts with: `1-Action Required`, `0-Leads`, `3-Waiting For`, `5-Follow Up`.
- Don't include `2-Read Only`, `4-Delegated`, `6/7/8` — those are handled.
- `(due tomorrow)` for Waiting For comes from the follow-up-tracker output — it's the count of items whose next cadence step fires tomorrow.

#### Carryover for Tomorrow Morning
- Items in `1-Action Required` that the exec didn't respond to today AND that are high enough priority to flag.
- Detection: items where `labelIds` includes `1-Action Required` and the thread has no outgoing message from the exec dated today.
- Format: `[Item] — [why it's carrying over]`. Examples: `board member re: strategy — not yet reviewed`, `legal threat from ex-employee — escalated yesterday, no reply from counsel`.
- Cap at 5 items. If more, something upstream is broken.

#### Label Sweep
- Pulls from: inbox-triage `label_sweep.py` output.
- One line per label that had sweep activity. Omit labels with zero activity.
- Format: `{label}: archived {n} ({reason}), {kept} kept`
- Examples:
  - `1-Action Required: archived 7 (exec replied), 2 kept (>48h no reply, flagged for tomorrow)`
  - `2-Read Only: archived 6 (aged out)`
  - `4-Delegated: archived 9 (team replied), 1 flagged to EA (>72h no activity)`

#### Alerts
- Only appears if there's an actual alert. Omit the section entirely otherwise.
- Things that belong here: voice guide missing, repeated API errors, team member not responding to delegations, cadence mismatches, credential refresh needed.
- Format: one-line plain-English notice per alert.

---

## Examples (Filled Templates)

### Example: Full SOD report

```
Inbox Management Update:

⚡ **Needs Your Decision** (11 min)
1. Jordan (investor) re: cap table update — needs your approval / 3 min — draft ready
2. Board chair re: strategic review meeting — pick a time next week / 2 min
3. Marketing lead re: Q3 campaign sign-off — Y/N / 1 min — draft ready
4. Legal re: vendor contract red-line — review and initial / 5 min — draft pending

💰 **Revenue**
1. Acme Corp (Sarah Kim) — Q2 enterprise terms ($180K ARR), scheduling call
2. Referral from Alex @ Acme — warm intro to their VP Eng, drafted reply

⏰ **Following Up Today**
1. Sarah @ Acme re: Q2 terms (4 days waiting, Day 4 draft ready)
2. Marcus re: vendor contract review (5 days, Day 5 draft ready)
3. Morgan @ Acme re: partnership (7 days, Day 7 final draft ready)
4. Exhausted: Jordan @ Globex re: licensing — exec decides drop or keep

✅ **Handled For You**
1. 47 newsletters filtered to Subscriptions
2. Invoice from Stripe ($2,140) — routed to Finance
3. Expense reports from 3 team members — routed to Finance
4. Calendar invite from [Name] (Thursday 10am) — accepted
5. Client success renewal question — routed to CS team

📅 **Today's Email-Driven Actions**
1. 10:30am: Call with Sarah @ Acme (from Q2 terms thread)
2. 2pm: Review Q3 campaign assets before 3pm sign-off
```

### Example: Full EOD report

```
Inbox EOD Summary:

**Today's Numbers**
- Processed: 94 emails
- Drafts created: 8
- Archived: 61
- Delegated to team: 14

**Still in Your Queue**
- ⚡ Action Required: 5 items (13 min)
- 💰 Leads: 2 items
- ⏰ Waiting For: 11 threads (3 follow up tomorrow)
- 🔁 Follow Up: 4 items

**Carryover for Tomorrow Morning**
1. Board chair re: strategic review — not yet answered (draft was ready)
2. Legal re: vendor contract red-line — draft pending (voice guide recently refreshed)

**Label Sweep**
- 1-Action Required: archived 6 (exec replied), 2 kept (flagged for tomorrow)
- 2-Read Only: archived 9 (aged out)
- 4-Delegated: archived 11 (team replied), 0 flagged
- 0-Leads: archived 1 (call scheduled), 2 kept

**Alerts**
- Jordan @ Globex cadence exhausted — moved to 5-Follow Up for your decision
```

### Example: Midday check (tiny)

Midday doesn't get a full SOD/EOD report — just a tiny status line from the reporter:

```
Midday inbox check (12:47pm):
- 18 new emails since morning
- 2 VIP messages — both in 1-Action Required (drafts ready)
- 1 reply to a Waiting For thread (Sarah @ Acme — moved to 1-Action Required, draft ready)
- 15 routine items left alone (will get triaged at EOD)
```

---

## Input Data Shapes

The reporter is the consumer at the end of the chain. Here's what it reads from each upstream skill:

### From `escalation-handler`
```json
{
  "tier_1_items": [{"message_id": "...", "subject": "...", "from": "...", "category": "legal", "severity": "immediate"}],
  "tier_2_items": [{"message_id": "...", "subject": "...", "from": "...", "category": "revenue_opportunity", "amount": "$75K"}]
}
```
Tier 1 goes into "Needs Your Decision" first. Tier 2 also goes there but below Tier 1.

### From `inbox-triage`
```json
{
  "mode": "morning",
  "scanned": 47,
  "labeled": {"0-Leads": 2, "1-Action Required": 5, "2-Read Only": 8, "3-Waiting For": 3, "4-Delegated": 11},
  "archived": 18,
  "drafts_created": [{"message_id": "...", "draft_id": "...", "subject": "..."}],
  "skipped": [{"message_id": "...", "reason": "voice profile missing"}]
}
```
Used for the header counts (EOD numbers) and to surface the `1-Action Required` list into "Needs Your Decision".

### From `follow-up-tracker`
```json
{
  "scanned": 18,
  "replied": 3,
  "drafts_created": 5,
  "escalated_to_followup": 2,
  "still_waiting": 8,
  "due_today": [{"to": "prospect@acme.com", "subject": "Q2 renewal", "days_waiting": 4, "cadence_step": "day_4"}],
  "escalations": [{"to": "vendor@example.com", "subject": "Contract red-line", "days_waiting": 21}]
}
```
Directly feeds "Following Up Today".

### From `inbox-triage label_sweep.py`
```json
{
  "1-Action Required": {"archived": 7, "reflagged": 2, "errors": []},
  "2-Read Only": {"archived": 6, "errors": []},
  "4-Delegated": {"archived": 9, "flagged_ea": 1, "errors": []},
  "0-Leads": {"archived": 1, "kept": 2, "errors": []}
}
```
Feeds "Label Sweep" section of the EOD report only.

### From `orchestrator` top-level result (`result["quota"]`)
```json
{
  "calls_24h": 1234,
  "budget": 30000,
  "pct": 4.11,
  "over_warn": false
}
```
Feeds the "📊 Quota" section in SOD and EOD reports. `calls_24h` may be `null` when the tracker is disabled (state store unreadable) — render as `quota: unknown (tracking disabled this session)` in that case. `over_warn` is the 80%-of-budget threshold flag; when `true`, also add an Alerts line.

### From `orchestrator` top-level result (`result["health"]`)
```json
{
  "findings": [
    {
      "check": "voice_guide_age",
      "severity": "warn",
      "detail": "voice guide is 45 days old (threshold 30)",
      "file": "client-profile/exec-voice-guide.md"
    },
    {
      "check": "config_template",
      "severity": "warn",
      "detail": "placeholders: [Name], TODO",
      "file": "client-profile/team-delegation-map.md"
    }
  ],
  "errored_checks": []
}
```
Feeds the "📋 Health" section in SOD and EOD reports.

- `findings` — zero or more dicts. Each has `check` (stable identifier like `voice_guide_age`, `empty_vip_list`, `config_template`), `severity` (one of `"info"`, `"warn"`, `"error"`), `detail` (human-readable one-line description), and `file` (path to the file that triggered the finding, or `null` when the finding is not file-bound).
- `errored_checks` — zero or more check names that raised an exception during the pre-flight. Each one means a check did not run at all this session — surface it so the operator can investigate, but do not infer "clean" from its absence.
- If both arrays are empty, the reporter omits the entire Health section.
- If any finding has severity `"error"` OR `errored_checks` is non-empty, the EOD Alerts section MUST also include a one-line notice — the Health block alone is informational; Alerts is what pages the operator.

---

## Common Mistakes to Avoid

- **Inventing categories.** If a label isn't in the 9-label system, it doesn't get its own report section. Don't create a "Cool Stuff" section.
- **Narrating instead of listing.** The report is bullets, not prose. No "Hi Alex, here's what happened today — it was a busy one!"
- **Leaking message IDs.** Never put raw Gmail message IDs in the report. The exec doesn't care.
- **Showing raw JSON.** If the upstream JSON can't be rendered as a one-line bullet, trim it.
- **Padding empty sections.** If there are no leads, don't write "💰 Revenue: none today 🎉". Omit the section.
- **Missing time estimates on Action Required.** Every single item in "Needs Your Decision" needs a time estimate. No exceptions.
- **Wrong sort order.** Tier 1 escalations ALWAYS come first in "Needs Your Decision". Age/priority is the tiebreaker, not the primary sort.
- **Duplicating items across sections.** An item appears in exactly ONE section. Leads go in Revenue, not also in Needs Your Decision.
