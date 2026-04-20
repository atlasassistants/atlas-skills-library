# Follow-Up Cadences

> Timing rules and drafting templates for the Atlas Inbox Zero follow-up system. Extracted from Section 8 of `atlas-inbox-rules-reference.md`. Used by the `follow-up-tracker` skill to pace follow-ups on `3-Waiting For` threads.

---

## The Three Cadences

Every thread in `3-Waiting For` falls into exactly one category and follows exactly one cadence. The category is set when the item first enters the label and doesn't change mid-cadence.

Only *outgoing* threads belong here. If the exec never sent a message in the thread, it is invalid queue state and should be cleared/re-triaged rather than paced on a cadence.

### Revenue / Sales — Fast cadence

Used for: prospects, leads, sales opportunities, contract negotiations, proposals, pricing discussions, renewals, partnership offers with revenue attached, deal-close threads. Also applied to anything currently labeled `0-Leads` that's waiting on a response.

| Step | When | What to Do |
|------|------|-----------|
| Day 1 | 1 calendar day after label applied | Short "just checking in" follow-up, restate the ask |
| Day 2 | 2 calendar days after label applied | Slightly more direct, offer a quick call as an alternative |
| Day 4 | 4 calendar days after label applied | Direct ask — "is this still on your radar?" |
| Day 7 (final) | 7 calendar days after label applied | Close-out framing — "no worries if not a fit, just let me know either way" |
| After Day 7 | — | Move to `5-Follow Up` for exec decision |

**Why so fast:** revenue deals cool off quickly. If a prospect hasn't replied in 48 hours, they're looking at something else. Fast, light touches keep you top of mind without being annoying.

### Internal — Medium cadence

Used for: anyone in `team-delegation-map.md`, trusted internal partners, close collaborators, portfolio companies, co-founders, internal stakeholders. Basically anyone who should be responsive and whose delay means something's wrong.

| Step | When | What to Do |
|------|------|-----------|
| Day 1 | 1 calendar day after label applied | Direct check-in: "any update on X?" |
| Day 3 | 3 calendar days after label applied | Firmer: "still need this, when can I expect it?" |
| Day 5 (escalate) | 5 calendar days after label applied | Escalate to exec in-session — the team member is dropping a ball and the exec needs to know |

After Day 5, move to `5-Follow Up` AND flag in the SOD report so the exec can intervene directly.

**Why:** internal deadlines matter most. If a team member is three days late on an ask from the exec, that's a management signal — the exec needs to see it, not just another draft in their Drafts folder.

### Vendors / External — Slow cadence

Used for: suppliers, contractors, service providers, vendors, external consultants, anyone the exec has a transactional rather than strategic relationship with. Also the default category when classification is ambiguous — vendors get the longest cadence because they genuinely take longer and over-chasing burns goodwill.

| Step | When | What to Do |
|------|------|-----------|
| Day 3 | 3 calendar days after label applied | Light check-in, polite |
| Week 2 | 14 calendar days after label applied | More direct ask with a deadline |
| Week 3 (final) | 21 calendar days after label applied | Close-out or escalate framing |
| After Week 3 | — | Move to `5-Follow Up` for exec decision |

**Why so slow:** vendors have their own queues. Pinging every 24 hours just moves you down their list.

---

## Classification Rules

How the script decides which category a thread falls into:

1. **Check for internal first.** If the recipient's email domain matches any team member's email domain in `team-delegation-map.md`, OR the recipient's email is directly in the map → **internal**. Done.

2. **Then check for revenue.** If the subject or the first 500 chars of the original outgoing body contain revenue keywords → **revenue**. Keywords include:
   - `proposal`, `pricing`, `quote`, `quotation`
   - `renewal`, `contract`, `terms`, `signed`, `sign off`
   - `close`, `closing`, `deal`, `opportunity`
   - `Q1 terms`, `Q2 terms`, `Q3 terms`, `Q4 terms`
   - `MRR`, `ARR`, `ACV`, `revenue`
   - `invoice approval`, `PO number`, `PO#`
   Also → revenue if the thread already has `0-Leads` applied.

3. **Otherwise vendor.** Default category. Safer to chase slowly.

**Override hints:** the script accepts `--category revenue|internal|vendors` for manual overrides on specific threads. Use sparingly — the default classification works for 95% of cases.

**Ambiguity rule:** if a thread is both revenue AND internal (e.g., internal team member negotiating an internal deal), internal wins. Internal deadlines always beat sales cadence.

---

## Drafting Templates

These are starting points only. The actual drafts MUST be rewritten in the exec's voice using `client-profile/exec-voice-guide.md`. The templates show the structure, length, and framing; the voice guide provides the phrasing.

### Revenue — Day 1

```
Hey [Name],

Just following up on [specific ask] — any questions on our end? Happy to
jump on a quick call if that's easier.

[Exec sign-off]
```

### Revenue — Day 2

```
Hey [Name],

Wanted to check back on [specific ask]. If a 15-minute call this week would
help move things forward, just pick a time: [calendar link if available].

[Exec sign-off]
```

### Revenue — Day 4

```
Hey [Name],

Circling back on [specific ask] — is this still on your radar for this
quarter? Want to make sure I understand where you're at.

[Exec sign-off]
```

### Revenue — Day 7 (final, close-out)

```
Hey [Name],

Last check-in on [specific ask]. If the timing isn't right or it's not a
fit, no problem at all — just want to make sure I know either way so I
can plan accordingly.

[Exec sign-off]
```

### Internal — Day 1

```
Hey [Name],

Any update on [specific ask]? Let me know if there's anything blocking you.

[Exec sign-off]
```

### Internal — Day 3

```
Hey [Name],

Still need [specific ask] — when can I expect it? If something's in the way,
tell me now and we'll sort it.

[Exec sign-off]
```

### Internal — Day 5 (escalate)

> **Don't draft this one automatically.** At Day 5 the agent flags the item to the exec directly via the report instead. The exec chooses whether to escalate in their own words or delegate it to someone else.

### Vendors — Day 3

```
Hey [Name],

Just a check-in on [specific ask] — any ETA on your end? Let me know if
you need anything more from me to move it forward.

[Exec sign-off]
```

### Vendors — Week 2

```
Hey [Name],

Following up on [specific ask] from a couple of weeks back. I'd like to
have this sorted by [specific deadline] — is that doable on your side?

[Exec sign-off]
```

### Vendors — Week 3 (final)

```
Hey [Name],

Last check on [specific ask] — if this isn't something your team can
prioritize, no problem, just let me know so I can look at alternatives.

[Exec sign-off]
```

---

## Drafting Rules (Non-Negotiable)

1. **Short.** Two to three sentences. Maximum four. Follow-ups get skimmed, not read.
2. **Specific.** Reference the actual ask ("Q2 terms", "the vendor contract", "the Acme proposal") — never "my last email" or "the thing we talked about".
3. **One ask per follow-up.** Don't bundle three questions into a follow-up. Pick the most important one.
4. **Give them an exit.** Especially on Day 4+ and Week 3, make it easy for them to say "not now" — a polite out gets you a reply faster than more pressure.
5. **Never passive-aggressive.** No "per my last email", no "gentle reminder", no "following up again", no "bumping this to the top of your inbox", no "circling back" (yes that's overused — find another word).
6. **Voice, voice, voice.** Match `exec-voice-guide.md` exactly. If the exec opens with "Hey", don't use "Hi". If they sign with "Best,", don't use "Thanks,". The person on the other end knows the exec's voice and will notice immediately if it shifts.
7. **Always thread.** Use `create_reply_draft` on the original outgoing message. A new thread breaks context and looks like spam.
8. **Only one draft per thread per session.** Re-running the skill should not create a second draft on the same thread.

---

## Day-Counting

- "Day 1" means 1 calendar day after the label was applied. If labeled Monday, Day 1 fires Tuesday.
- The script approximates label-application time using the original outgoing message's `internalDate`. Close enough in practice since labels go on shortly after sending.
- Weekends count the same as weekdays for Atlas purposes — a Monday-morning follow-up on a Friday ask still fires correctly (3 calendar days).
- **Missed step rule:** if the skill wasn't run for a few days and several steps are now due, fire only the step that matches the current day count. Don't send Day 1, Day 2, and Day 4 in one session to catch up — just send the one that's due now.

---

## Escalation to `5-Follow Up`

When a cadence exhausts without a response, the item moves from `3-Waiting For` to `5-Follow Up`. This is not an archive — it's a parking spot where the exec decides what to do. Options the exec typically picks from:

- **Drop it.** Archive — not worth chasing further. The agent archives when the exec confirms.
- **Restart.** Move back to `3-Waiting For`, reset the cadence, draft a Day 1 follow-up (often with new framing).
- **Call them.** Exec handles it offline; no more email follow-ups needed.
- **Hand off.** Delegate to a team member via `4-Delegated`.

The `inbox-reporter` surfaces `5-Follow Up` items weekly so they don't get lost.

---

## What the Script Does vs. What the Agent Does

**Script (`check_followups.py`):**
- Fetches every item in `3-Waiting For`
- Parses each thread for the last message from the waiter (reply detection)
- Classifies each item into revenue / internal / vendors
- Computes `label_age_days` from `internalDate`
- Decides which cadence step is due (or `none`)
- Outputs structured JSON

**Agent (Claude, using this skill):**
- Reads the JSON
- For replies → runs the decision tree and re-triages the new incoming message
- For due follow-ups → drafts in the exec's voice using the templates in this file + the voice guide
- For exhausted cadences → moves items to `5-Follow Up`
- Builds the summary JSON for `inbox-reporter`

The split lines up with the rest of the plugin: the script does the mechanical Gmail-talking, the agent makes the judgment calls.
