# Production Profile Setup Questions

> This file replaces the old 14-question first-run interview.
>
> Best practice: ask only for inputs that change live behavior now. Keep first-run onboarding short. Move the rest into optional later calibration.

## How to Use This File

- Ask questions **one at a time**.
- Keep the required setup short and operational.
- Do **not** force every optional question into onboarding.
- If a question does not clearly affect live behavior yet, skip it for now.
- At the end, summarize what you heard and confirm before saving.

---

## Required Now — Production-Critical Inputs

These are the questions worth asking during first-run onboarding because they power real behavior immediately.

### 1. Who are your VIP contacts that need immediate escalation?

**Why we ask:** VIPs are operational today. They drive escalation logic and VIP filters.

**How to collect:**
- Ask for names first.
- Then ask for email addresses.
- Prompt for likely categories they may forget: board, top clients, investors, legal, family, key partners.

**Save to:** `client-profile/vip-contacts.md`

---

### 2. Who handles what on your team?

**Why we ask:** This powers delegation hints, follow-up handling, and team routing.

**What to collect:**
- person or role
- email address if available
- what they own (finance, HR, recruiting, client issues, vendor ops, etc.)

**Follow-ups if vague:**
- "If a finance email comes in, who should it go to?"
- "Who owns recruiting?"
- "Who handles client issues?"
- "Who should vendor/admin threads go to?"

**Save to:** `client-profile/team-delegation-map.md`

---

### 3. Do you want to keep the default label sweep rules, or adjust any?

**Why we ask:** Sweep behavior affects how labels clear automatically at EOD.

**Frame it like:**
- "These are the recommended auto-archive rules for each label. Most people keep the defaults. Want to keep them, or change any?"

**Save to:** `client-profile/label-sweep-rules.md`

---

### 4. What check-in times or processing window should we use?

**Ask this only if the deployment is actually using scheduling or pre-check processing windows.**

**Why we ask:** Useful only when run timing is wired to the user's actual schedule.

**What to collect:**
- preferred morning / midday / EOD check times
- timezone
- whether midday should be off by default
- how far ahead triage should run before the exec checks

**Save to:** `client-profile/sweep-schedule.json` for the live schedule, plus `client-profile/exec-preferences.md` only for any extra rationale or workflow notes

---

## Optional Later Calibration

These can be useful, but should **not** be part of mandatory first-run onboarding unless they already power behavior or the exec explicitly wants a deeper setup pass.

### Optional A. Reply voice convention
- Should the EA reply as themselves or as the exec?
- **Use when:** drafting behavior is live and needs this instruction.
- **Save to:** `client-profile/exec-preferences.md`

### Optional B. EA autonomy boundaries
- What can the EA fully handle without executive input?
- **Use when:** delegation/autonomy logic is being wired into triage or drafting.
- **Save to:** `client-profile/exec-preferences.md`

### Optional C. Custom escalation triggers
- What keywords or situations should trigger immediate notification?
- **Use when:** escalation rules are configurable in the deployment.
- **Save to:** `client-profile/exec-preferences.md`

### Optional D. Definition of done
- What does a successful EOD inbox state look like?
- **Use when:** reporter/EOD success criteria consume it.
- **Save to:** `client-profile/exec-preferences.md`

### Optional E. Priority tiers
- What needs immediate attention, what can wait, what can be delegated?
- **Use when:** triage logic or review workflows are actually reading it.
- **Save to:** `client-profile/exec-preferences.md`

### Optional F. Current inbox rhythm
- When do you currently check inbox?
- **Use when:** useful for change management or schedule tuning.
- **Save to:** `client-profile/exec-preferences.md`

### Optional G. Vision, frustrations, habits
- What does a perfect inbox feel like?
- What frustrates you most?
- What habits are you trying to change?
- **Use when:** doing coaching, service calibration, or weekly review.
- **Save to:** `client-profile/exec-preferences.md`

### Optional H. Feedback loop and weekly success metrics
- How should the exec give feedback?
- How should success be measured weekly?
- **Use when:** there is an actual reporting/review cadence that reads it.
- **Save to:** `client-profile/exec-preferences.md`

---

## Recommended First-Run Script

Use something like:

> "I just need a few things to make this work well in production: your VIPs, who handles what on the team, and whether you want the default sweep rules. Optional preference tuning can happen later if we decide to wire more behavior to it."

---

## Wrap-Up

After the required setup questions:
1. Summarize back what you heard.
2. Confirm it matches.
3. Save to:
   - `client-profile/vip-contacts.md`
   - `client-profile/team-delegation-map.md`
   - `client-profile/label-sweep-rules.md`
   - `client-profile/exec-preferences.md` only for any actually-used scheduling/calibration items
4. Tell the exec what happens next: they are production-ready, and optional calibration can happen later without blocking use.
5. If scheduling is enabled, run `python inbox-onboarding/scripts/capture_schedule.py` to ask the schedule questions, write the live schedule, and install the chosen backend.
