# Atlas Inbox Zero — Reference Rules (Gmail)

> This document is the source of truth for the Atlas Inbox Zero Plugin. All skills reference this file for rules, labels, decision logic, and templates. Rules marked **[FIXED]** are Atlas standards and never change. Rules marked **[CONFIGURABLE]** are set per client during onboarding.

## How This Reference Doc is Used During the Build

This is the MASTER reference. During the plugin build, Claude Code will:
1. Read this entire file to understand the full Atlas system
2. Copy the full file into `inbox-onboarding/references/atlas-inbox-rules.md` (the setup skill needs everything)
3. Extract relevant sections into each other skill's `references/` folder (e.g., Section 4 Decision Tree → `inbox-triage/references/decision-tree.md`, Section 6 Escalation Rules → `escalation-handler/references/escalation-rules.md`)

This file does NOT ship as-is in the final plugin. It gets broken into pieces.

---

## CRITICAL: This Plugin is an Executing Agent

This plugin is NOT a set of instructions for a human to follow. It is an **AI agent that performs the work directly**:
- The agent **creates** labels in Gmail
- The agent **creates** filters in Gmail
- The agent **configures** Gmail settings
- The agent **reads** emails and **applies** labels
- The agent **triages** every email using the decision tree
- The agent **creates draft** replies, forwards, and follow-ups in the exec's voice
- The agent **archives** emails according to label lifecycle rules
- The agent **reads** the exec's sent folder for voice extraction
- The agent **generates** reports

**The one thing the agent does NOT do is send emails.** It creates drafts. The human (EA or exec) reviews and sends. Every other step is agent-executed.

---

## 1. The Atlas Label System [FIXED]

Every email gets exactly ONE label. No email stays in the inbox unlabeled.

| Label | Purpose | When to Apply |
|-------|---------|---------------|
| **0 — Leads** | Revenue opportunities | Sales inquiries, referrals, partnership offers with revenue potential. *Optional by client — enable if exec receives leads via email.* |
| **1 — Action Required** | Needs exec voice or decision | Decisions only the exec can make, replies that should come from the exec personally, items needing exec signature or approval, and narrow security/access exceptions |
| **2 — Read Only** | FYI | Newsletters the exec wants, industry news, team updates that are informational only |
| **3 — Waiting For** | Pending responses | Emails where we sent something and are waiting for a reply. Track with follow-up cadence. |
| **4 — Delegated** | EA or team handling | Anything the EA handles directly OR routes to a team member. The EA owns this label. |
| **5 — Follow Up** | Future action needed | Items that need action later but not today. Date-specific follow-ups. |
| **6 — Receipts/Invoices** | Financial records | Receipts, invoices, payment confirmations, billing statements |
| **7 — Subscriptions** | Automated emails | Newsletters, marketing, automated notifications, SaaS alerts |
| **8 — Reference** | Tickets, confirmations | Calendar invites, meeting recordings, booking confirmations, support tickets |

### Label Lifecycle — Sweep Rules [DEFAULTS — shown during onboarding, user keeps or adjusts]

Labels are not permanent holding bins. The agent runs a label sweep during the EOD triage and auto-archives items based on these rules:

Atlas-managed queue items also do **not** stay in Inbox. Once a message is triaged into an Atlas label, it is worked from the label queue, not from Inbox. Inbox is reserved for untriaged mail.

| Label | Default Sweep Rule | Agent Action |
|-------|-------------------|--------------|
| 1 — Action Required | Archive once exec has responded (agent checks for outgoing reply in thread) | Agent detects reply in thread → archive. If no reply after 48hrs → re-flag in next SOD report. |
| 2 — Read Only | Archive after 48 hours from labeling | Agent tracks timestamp when label was applied → auto-archives at 48hrs. |
| 3 — Waiting For | Check follow-up cadence → if response received, re-triage. If no response and cadence is due, draft follow-up. If cadence exhausted, move to 5-Follow Up for exec decision. | Agent checks thread for new replies. If reply found → remove label, re-triage the response through decision tree. If no reply → check cadence schedule → draft follow-up if due. |
| 4 — Delegated | Archive once the routed team member has replied or confirmed handled | Agent checks thread for team member response. If response found → archive. If no activity after 72hrs → flag to EA. |
| 5 — Follow Up | Archive when follow-up action is completed or exec decides to drop it | Agent tracks — stays until actioned. Surfaces in SOD report weekly. |
| 0 — Leads | Archive once lead is actioned (call scheduled, declined, or handed off) | Agent checks for calendar event or reply in thread. If found → archive. Otherwise → stays and surfaces in SOD. |
| 6, 7, 8 | Auto-archived by filters on arrival — no sweep needed | No agent action required. |

For Morning and EOD daily runs, triage continues in batches until no untriaged Inbox items remain, or until the orchestrator hits its safety cap for that session. Dry-run previews show only the first batch.

**During onboarding:** The agent presents these default rules to the user and asks: "These are the recommended label sweep rules. Would you like to keep these or adjust any?" User can modify timing (e.g., change Read Only from 48hrs to 24hrs) or rules (e.g., never auto-archive Leads).

---

## 2. Gmail Configuration [FIXED]

### Settings → General
- "Show Send & Archive button in reply" → ON
- "Desktop notifications" → OFF
- "Keyboard shortcuts" → ON
- "Default reply behavior" → Reply all
- "Auto-advance" → ON
- "Maximum page size" → 50 conversations

### Settings → Advanced
- Multiple Inboxes → Enable
- Templates → Enable
- Auto-advance → Enable

### Settings → Inbox
- Inbox type → Multiple Inboxes
- Reading pane position → Right of inbox
- Maximum page size → 20 conversations

### Multiple Inbox Sections
- Section 1: `label:0-leads` → name: "💰 Revenue"
- Section 2: `label:1-action-required` → name: "⚡ Needs You"
- Section 3: `label:2-read-only` → name: "📖 FYI"
- Section 4: `label:3-waiting-for` → name: "⏰ Pending"
- Section 5: `label:4-delegated` → name: "✅ EA Handling"

---

## 3. Filter Automation [FIXED]

The agent creates these Gmail filters directly via the Gmail API during setup. Each filter is created programmatically — the agent does not provide instructions for a human to create them.

**Core filters (agent creates all of these):**

| Condition | Action |
|-----------|--------|
| Contains "unsubscribe" | Skip inbox → apply 7-Subscriptions |
| Contains "receipt" OR "invoice" OR "payment" OR "billing" | Skip inbox → apply 6-Receipts/Invoices |
| Contains ".ics" OR "calendar" OR "invitation" | Apply 8-Reference |
| From: [VIP contacts — **CONFIGURABLE**, collected during onboarding] | Apply 1-Action Required, never send to spam |
| From: [unwanted newsletters — **CONFIGURABLE**, identified during cleanup] | Skip inbox, mark read, archive |
| From: noreply@zoom.us OR recordings@ OR @fathom.video | Skip inbox → apply 8-Reference |

**Bulk filter creation during initial cleanup:**
During the first inbox cleanup, the agent scans all emails, identifies senders with 5+ messages, and creates filters for each one automatically — labeling appropriately and applying to existing conversations.

---

## 4. The Decision Tree [FIXED]

When a new email arrives in the inbox, process it in this exact order:

```
New email arrives
│
├─ Is it spam or marketing? → Archive (or filter it)
│
├─ Can the EA/agent handle it?
│   YES → Reply, forward, or process it → Label 4-Delegated → Archive
│   (Check team-delegation-map: if a team member is CC'd or the content
│    matches their domain, route to them specifically)
│
├─ Is it revenue-related? → Label 0-Leads + flag in daily report
│
├─ Does it require the exec's input/decision or personal voice?
│   YES → Label 1-Action Required + draft only if the next step is an outbound exec reply
│
├─ Are we waiting for someone to respond? → Label 3-Waiting For
│
├─ Is it FYI/informational the exec wants to see? → Label 2-Read Only or Archive
│
└─ None of the above → Archive
```

**Critical rule:** Escalation check happens BEFORE the decision tree. Always scan for red flags first (see Escalation Rules).

**Critical rule:** If a team member is CC'd AND the email content falls in their domain, label it 4-Delegated. Do NOT send it to 2-Read Only. This is a common error.

**Critical rule:** `1-Action Required` is not a catch-all for any inbound ask. Use it only when the message truly needs the exec's voice, decision, approval, signature, or a narrow security/access intervention. If the EA can handle the reply, routing, or follow-up, it belongs in `4-Delegated`.

---

## 5. Daily Triage Cadence [FIXED]

### Morning Sweep — 15 minutes, before exec starts their day
1. Open inbox, start from the oldest email
2. For each email, run the Escalation check, then the Decision Tree
3. For any reply-worthy 1-Action Required items: draft a response in the exec's voice, save as draft. Review-only security/access items should be surfaced without forcing a reply draft.
4. Generate SOD inbox report section

### Midday Check — 10 minutes, around lunch
Quick scan ONLY. Look for:
- New messages from VIP contacts → escalate if needed
- Meeting changes for today → update calendar
- Urgent team flags → action or escalate
- Responses to 3-Waiting For items → move label, action if needed

Do NOT process the full inbox. Do NOT get pulled into long threads.

### EOD Review — 15 minutes, before exec logs off
1. Full triage of all remaining emails → inbox back to zero
2. Label sweep: archive items in labels that have been acted on
3. Check 3-Waiting For: send any follow-ups due today
4. Note priorities that need flagging tomorrow morning
5. Generate EOD summary

---

## 6. Escalation Rules [FIXED + CONFIGURABLE]

### Immediate Escalation — text or call exec [FIXED]
- Board member marked urgent
- Legal notice or litigation threat
- Media or press inquiry
- Client crisis (revenue at risk)
- Employee resignation
- Wire transfer request
- Anything marked "Confidential"

### Flag in Next Report [FIXED]
- Revenue opportunity over $50K
- Speaking or board invitations
- Strategic partnership offers
- Investor communications
- Key client feedback

### VIP Contacts [CONFIGURABLE]
- Emails from contacts in vip-contacts.md ALWAYS get 1-Action Required
- Never send VIP emails to spam
- VIP list is set during onboarding and updated as relationships change

### Common Scenarios [FIXED]
- Exec didn't review EOD → carry flagged items to next morning
- Urgent email during exec's meeting → text: "[Person] needs [decision] by [time]"
- Unsure whether to handle → default to handling it, document the decision
- Exec traveling or sick → handle everything possible, one consolidated daily report, escalate only true emergencies

---

## 7. Delegation Logic [CONFIGURABLE]

### How to Identify Delegatable Emails
1. **CC check:** If a team member from the delegation map is CC'd, the email likely belongs to them
2. **Domain match:** Match email content/subject to team member domains:
   - Finance keywords (invoice, billing, payment, expenses, budget) → Finance team
   - HR keywords (hiring, benefits, employee, PTO, onboarding new hire) → HR
   - Client-related (onboarding, renewal, client request, account) → Client Success
   - Scheduling (calendar, meeting, reschedule, availability) → EA handles
   - Operations/general → EA handles
3. **Reply-all threads:** If a team member is already actively replying, it's their thread
4. **Exec forwards:** If the exec forwarded with no additional instruction, it means "handle this"

### Delegation Actions (Agent Executes)
1. Apply label 4-Delegated
2. Create a draft forward to the correct team member (agent does NOT send — EA reviews and sends)
3. Note which team member it's routed to in the daily report
4. Track completion: agent checks thread for team member response → archive once confirmed handled

### Team Delegation Map Template [CONFIGURABLE — set during onboarding]
```
Team Member | Domain | Keywords | Email
[Name]      | Finance | invoice, billing, payment, expenses | [email]
[Name]      | HR | hiring, benefits, employee | [email]
[Name]      | Client Success | onboarding, renewal, client | [email]
EA          | Scheduling, Operations | calendar, meeting, general | —
```

---

## 8. Follow-Up Cadences [FIXED]

Track all items in 3-Waiting For. Follow up on this schedule:

| Category | Follow-Up Schedule |
|----------|-------------------|
| Revenue / Sales | Day 1 → Day 2 → Day 4 → Day 7 (final) |
| Internal (team, partners) | Day 1 → Day 3 → Day 5 (escalate to exec) |
| Vendors / External Partners | Day 3 → Week 2 → Week 3 (close or escalate) |

When a follow-up is due:
- Draft a short message in the exec's voice
- Send it (or save as draft for EA review)
- Log it in the daily report under ⏰ Following Up Today

---

## 9. SOD Report — Inbox Section Template [FIXED]

```
Inbox Management Update:

⚡ **Needs Your Decision** (X min)
1. [Person] re: [topic] — [draft ready / draft pending / review directly]
2. [Subject] — [one-line context + what's needed]

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

Rules: One line per item. Specific names and subjects. Action needed is clear. Time estimates for exec decision items.

---

## 10. Executive Voice Extraction Method [FIXED]

### To Build the Voice Guide
The agent reads the last 30 sent emails directly from the exec's Gmail sent folder. It then analyzes them and extracts:

- **Opening style:** Hi / Hey / Hello / first name only / no greeting
- **Closing style:** Thanks / Best / just their name / no sign-off
- **Overall tone:** Formal / direct / warm / casual
- **Recurring phrases:** Expressions they use repeatedly
- **How they decline:** Direct no / soft redirect / offer alternative
- **How they push back:** Language patterns when disagreeing
- **How they signal urgency:** Words, punctuation, structure
- **How they show enthusiasm:** Language for positive responses

### Voice Guide Output Format
```
EXECUTIVE VOICE PROFILE

Name: [Exec name]
Tone: [1-2 word descriptor]

Opens with: [typical greeting]
Closes with: [typical sign-off]
Signature phrases: [list 3-5]

When saying yes: [pattern]
When saying no: [pattern]
When urgent: [pattern]
When delegating: [pattern]

Anti-patterns (never use):
- [phrases to avoid]
- [tone to avoid]
```

---

## 11. Initial Inbox Cleanup Procedure [FIXED]

The agent executes this once during onboarding:

1. **Mass archive:** Agent searches for emails older than 90 days (`before:YYYY/MM/DD`) and archives all of them (never delete)
2. **Bulk filter creation:** Agent scans remaining emails by sender, identifies senders with 5+ emails, creates Gmail filters for each, applies labels, and applies to existing conversations
3. **Triage remaining:** Agent processes all remaining inbox emails through the Decision Tree (Section 4), applying labels and creating drafts as needed

---

## 12. Executive Profile Setup — Production-Ready Version [FIXED]

Do **not** force a long discovery questionnaire in first-run onboarding unless the answers already power live behavior.

### Required during onboarding
Ask only for the inputs that change behavior immediately:
1. **VIP contacts** → save to `client-profile/vip-contacts.md`
2. **Team routing / who handles what** → save to `client-profile/team-delegation-map.md`
3. **Label sweep defaults or adjustments** → save to `client-profile/label-sweep-rules.md`
4. **Scheduling/check-in preferences** only if the deployment is actually using them → save the live schedule to `client-profile/sweep-schedule.json` and keep any extra rationale in `client-profile/exec-preferences.md`

### Optional later calibration
Ask these only when the exec wants deeper tuning, or when a skill genuinely uses them:
- reply voice convention
- EA autonomy boundaries
- custom escalation triggers
- definition of done
- priority tiers
- current inbox rhythm
- inbox vision / frustrations / habits
- feedback preferences and weekly success metrics

Rule: if an answer does not clearly change current behavior, do not make it a blocking onboarding question.

---

## 13. Red Flags — Stop and Ask [FIXED]

During ANY phase (setup, triage, or follow-up), stop and escalate if you encounter:
- Email marked "Confidential" or "Legal"
- Email from a board member or investor
- Contains termination or litigation language
- Wire transfer or payment instructions
- Press or media inquiry
- Complaint from a key client

---

## 14. Common Setup Mistakes to Avoid [FIXED]

- Never delete emails — always archive
- Never mark emails as spam — use filters instead
- Stick to exactly 9 labels — don't create extras
- Always check "Apply to existing" when creating filters
- Always test each filter with a sample email
- Don't skip the initial cleanup — the system works better starting clean
