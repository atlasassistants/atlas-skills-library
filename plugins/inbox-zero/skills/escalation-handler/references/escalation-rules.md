# Escalation Rules

> Red flag detection for the Atlas Inbox Zero system. These rules are extracted from Sections 6 and 13 of `atlas-inbox-rules-reference.md`. The escalation-handler skill runs BEFORE any other triage — red flags MUST be caught before the decision tree applies normal labels.

---

## Two Tiers of Escalation

### Tier 1 — Immediate Escalation (text or call the exec)

These items cannot wait for the next report. The agent surfaces them to the user (EA or exec) in the current session AND applies `1-Action Required`.

| Trigger | What to look for |
|---------|------------------|
| **Board member urgent** | From a board member AND subject/body contains urgency words (urgent, asap, today, emergency) |
| **Legal notice / litigation threat** | Subject or body contains: legal, attorney, counsel, cease and desist, lawsuit, litigation, subpoena, deposition, settlement, claim against, dispute |
| **Media or press inquiry** | From a journalist/publication, or subject/body contains: press, media, journalist, reporter, quote, interview request, publication, story |
| **Client crisis — revenue at risk** | Key client + negative sentiment. Keywords: cancel, canceling, terminating, ending contract, dissatisfied, refund, not working, disappointed, escalate, unhappy, losing confidence |
| **Employee resignation** | Subject or body contains: resignation, resigning, two weeks notice, last day, stepping down, leaving the company, my departure |
| **Wire transfer request** | Subject or body contains: wire transfer, wire instructions, routing number, account number, swift code, payment details, bank details (especially combined with urgency) |
| **Confidential marker** | Subject starts with `[Confidential]`, `CONFIDENTIAL:`, body contains "confidential" in a first-line position, attorney-client privileged |
| **Security alert** | Subject or body contains: password changed, review this sign in, security alert, verify it's you, suspicious login, unusual sign-in |

### Tier 2 — Flag in Next Report

These are important but don't require interrupting the exec's current work. The agent applies `1-Action Required`, flags the item in the next SOD/EOD report, and moves on.

| Trigger | What to look for |
|---------|------------------|
| **Revenue opportunity over $50K** | Sales/partnership email with explicit dollar amount ≥ $50,000 OR qualitative signals (enterprise deal, major account, six-figure, seven-figure) |
| **Speaking or board invitation** | Subject/body contains: speaking engagement, keynote, panel, conference invite, board seat, advisory role, board invitation |
| **Strategic partnership offer** | Body contains: partnership, strategic alliance, joint venture, co-marketing, white label, licensing deal |
| **Investor communications** | From a known investor domain OR body contains: investor update, cap table, round, valuation, term sheet, due diligence |
| **Key client feedback** | Feedback from top-tier client (positive or negative), NPS comments, case study request, reference call |
| **Access request** | Subject or body contains: share request, requesting access, invited you to collaborate, accept invitation, access request, collaboration invite, or an upcoming 2FA requirement notice |

---

## VIP Contacts (Always Escalate)

Emails from anyone listed in `client-profile/vip-contacts.md` ALWAYS get escalated:

- **Always** apply `1-Action Required` regardless of content.
- **Never** allow VIP mail to reach spam. (Filters set up during onboarding enforce this at the mailbox level — the escalation handler is a second line of defense.)
- **Immediate tier** if VIP content also matches a Tier 1 trigger (e.g., VIP + "urgent").
- **Report tier** otherwise — flagged in next SOD/EOD report.

The VIP list is read fresh each scan so updates to `vip-contacts.md` take effect immediately.

---

## Detection Strategy

### Pass 1 — Sender Match (fastest)
Check `From:` header against the VIP list. If match, escalate.

### Pass 2 — Subject Scan (fast)
Check `Subject:` for trigger keywords. Case-insensitive substring match.

### Pass 3 — Body Scan (slower, only when needed)
For messages that didn't match Pass 1 or Pass 2 but might be borderline, scan the first ~500 characters of the plain-text body for trigger phrases. Don't scan the full body — most red flags show up in the first paragraph or the subject.

### Pass 4 — Combined signals
Wire transfer detection needs at least 2 signals (e.g., "wire" + "routing number") to reduce false positives on normal banking newsletters. Client crisis detection needs at least 1 strong negative word + a recognized client sender (or unknown sender — better to over-escalate than miss).

---

## What the Skill Does After Detection

For each flagged item:

1. Apply `1-Action Required` label immediately (Gmail API call).
2. Record `{message_id, tier, trigger, subject, from, snippet}` in the scan output.
3. **Tier 1 items:** print a prominent alert in the current session (the agent shows these to the user right now, with subject and trigger). The agent asks: "I spotted these 3 items that need your attention now. Want me to read any of them in full?"
4. **Tier 2 items:** collected into the scan report. These flow into the next SOD/EOD report via `inbox-reporter`.

The skill does NOT send any notifications (text/call) directly — it surfaces the items in-session to the agent, and the agent relays them to the human. If there's a Slack or SMS integration configured elsewhere, that's a separate concern — not this skill's job.

---

## Common Scenarios (From Section 6)

- **Exec didn't review EOD:** carry flagged items to next morning. The scan picks them up again — nothing is lost.
- **Urgent email during exec's meeting:** agent surfaces it as: "[Person] needs [decision] by [time]". One-line format.
- **Unsure whether to escalate:** default to escalating. Better to over-surface than miss a real fire.
- **Exec traveling or sick:** handle everything possible, one consolidated daily report, escalate only true emergencies (Tier 1 only, never Tier 2).

---

## Red Flags — Stop and Ask (Section 13)

In addition to the above, the agent should STOP and ask the user what to do if it encounters any of:

- Email marked "Confidential" or "Legal"
- Email from a board member or investor the agent doesn't recognize
- Contains termination or litigation language the agent isn't sure how to categorize
- Wire transfer or payment instructions (never auto-process payment details, ever)
- Press or media inquiry
- Complaint from a key client
- Security alert or access request the agent is not comfortable classifying

"Stop and ask" means: the agent does NOT draft a response, does NOT apply a label other than `1-Action Required`, and explicitly asks the user how to proceed.

---

## Anti-Patterns (Do Not Do)

- **Don't auto-draft responses to Tier 1 items.** The exec handles these personally; a pre-drafted reply is a liability (wrong tone, wrong facts, legal exposure).
- **Don't skip the escalation scan to save time.** Even during a "quick" midday check, Tier 1 detection runs first. This is the one non-negotiable step.
- **Don't de-escalate based on sender volume.** A VIP who sends 50 emails a day is still a VIP — don't train the scan to ignore high-volume senders.
- **Don't trust a filter to replace the scan.** Filters catch senders, not content. The scan catches content the filter missed.
