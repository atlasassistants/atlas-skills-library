# Setup Wizard — Question Reference

> The setup skill loads this reference and walks through the questions one at a time. Each question has: a prompt, a paraphrase format (for confirmation), and what to capture into the profile.

## Skip support (general principle)

Most questions are **opt-in** — the user can choose not to answer any individual prompt. The orchestrator should:

1. **Make "skip" obvious.** Every prompt should make it clear the user can pass. When delivering, append (or imply) something like *"...or say 'skip' if you'd rather not."* Don't make people feel cornered.
2. **Communicate the cost of skipping clearly.** When a user skips, the orchestrator briefly tells them what's lost so they can make an informed choice. E.g.: *"Got it — skipping themes. Your briefs and email drafts will be less tied to your actual focus areas; they'll lean on conversation notes alone for relevance angles. You can re-run setup any time to fill these in."* Per-question cost messages live in the question's section below.
3. **Mark the profile as `partial` when skips happen.** The final saved profile's `Profile completeness` field lists each skipped section. This signal is read by capture-contacts for graceful degradation (e.g. drafts without voice profile use generic professional tone, briefs without themes drop the Common Ground section).
4. **Some questions are not skip-tolerant.** Identity (name + company at minimum), email tool wiring, and output folder are required for the plugin to do anything useful. The orchestrator should be explicit when a question can't be skipped: *"This one I do need — without [field] I can't [downstream consequence]. Want to give me [field], or stop here?"*

Per-question skip cost messages are written into each question section below.

## Question 1 — Identity (4 sub-fields, asked together)

> **Voice convention.** This plugin is exec-first — written for an executive running it on their own contacts. If an EA chooses to use it on the executive's behalf, they read "you" as referring to the executive they support. Keep all user-facing strings in second person.

**Prompt:**
> "Let's start with the basics. Tell me:
> - Your name
> - Your title
> - Your company
> - A one-line description of what your company does (e.g., 'We help X do Y')"

**Paraphrase format:**
> "Got it: [Name], [Title] at [Company]. The company [one-line description]. Got that all right?"

**Captures:** `Identity` block in the profile.

---

## Question 2 — Email tool *(retired in MCP-pivot wizard)*

This question is now handled by step 3 in `setup/SKILL.md` — capabilities are detected from the host's loaded tool list, and the user picks from what's already wired. No standalone question needed.

---

## Question 3 — Voice extraction (auto, with review)

**Prompt:**
> "Now I'll pull the last 30–50 of your sent emails to learn how you write — tone, sentence patterns, signoff. This takes about 30 seconds. Ready?"

After the pull and analysis, show the synthesized voice profile and ask:

> "Here's what I learned about your writing style: [summary]. Read through `client-profile/email-voice.md` — anything to refine before saving?"

**Captures:** `client-profile/email-voice.md`.

---

## Question 4 — Email signoff

**Prompt (after voice extraction):**
> "Detected your most common signoff: '[detected signoff]'. Use this for follow-up emails, or pick something else?"

**Captures:** `Email signoff` field in the profile.

---

## Question 5 — Themes (5 sub-prompts, asked one at a time as a short interview)

Q5 captures all 5 sections of `client-profile/exec-themes.md`. Ask the sub-prompts in order, accept the user's answer, paraphrase back if more than a one-liner, then move to the next. Don't deliver all 5 in one block — it overwhelms.

### Q5 preamble (always deliver before Q5a)

Before launching into the sub-prompts, give the user the option to skip the whole interview:

> "Next up: a short interview to learn what you talk about, what you're working on, how you frame your work, and how you tend to open conversations. About 5 quick questions — totals ~2 minutes.
>
> The more context you give here, the better the briefs and email drafts can tie to your real focus areas and voice. **But all of this is optional** — you can skip individual questions, or skip the whole block. If you skip everything, briefs will summarize the people you meet but won't have your common-ground angles, and email drafts will use a generic professional tone.
>
> Want to do the interview, or skip the whole themes block?"

If user says "do it" / "go ahead" / similar → proceed to Q5a.

If user says "skip" / "skip all" / "pass" / "skip the whole thing" → don't deliver Q5a-e. Acknowledge:
> "No problem — skipping themes entirely. Your briefs and drafts will work, but they'll have less personal connection to your actual work and voice. You can re-run setup any time to fill these in."
Mark all 5 sections in `exec-themes.md` as `(skipped during setup — re-run setup to add)`. Mark the profile as `Profile completeness: partial — themes section skipped`. Move directly to step 8 (output folder).

### Per-sub-prompt skip handling (within the interview)

**Each sub-prompt is also independently skip-tolerant.** If the user says "skip" / "pass" / "I'd rather not" mid-interview, record that section as `(skipped during setup — re-run setup to add)`, deliver the per-section cost message (below), then move to the next sub-prompt. After all 5, if 2+ are skipped, flag the profile as `Profile completeness: partial — themes section incomplete`.

**Cost-of-skipping messages, per sub-prompt:**
- **Q5a skipped** → *"Got it. Briefs won't have a 'common ground' angle pulling from your topics — they'll just summarize the person and lean on your conversation notes for relevance. Email drafts won't reference any shared interest area."*
- **Q5b skipped** → *"Got it. Briefs won't reference what you're working on, so the suggested follow-up angle won't tie to your current initiatives. Drafts may feel less timely."*
- **Q5c skipped** → *"Got it. The drafter won't lead with your specific positioning — emails will use a generic 'what your company does' framing instead."*
- **Q5d skipped** → *"Got it. The drafter has no off-limits list, so it may surface topics you'd normally avoid in cold-touch emails. Review drafts carefully before sending."*
- **Q5e skipped** → *"Got it. Drafts will use a default conversational opener instead of one of your usual angles."*

If the user wants to skip the entire Q5 block (all 5), accept that and skip to step 8: *"No problem — skipping themes entirely. Your briefs and drafts will work, but they'll have less personal connection to your actual work and voice. You can re-run setup any time to fill these in."* Mark the profile as `Profile completeness: partial — themes section skipped`.

### Q5a — Topics talked about with the network (3–5 bullets)

> "Three to five topics you typically talk about with people in your network — domain stuff, things you have a strong point of view on, areas you follow closely. What comes to mind? *(Or say 'skip' to pass — I'll tell you what that costs.)*"

If the user gives 1–2 bullets only, probe one at a time: *"Anything else? Even niche topics count."*

If the user says "skip" / "pass": deliver the Q5a skip-cost message from the per-question list above, then move to Q5b.

**Captures:** `## What I typically talk about with people in my network` section.

### Q5b — Current initiatives (2–4 bullets)

> "What are 2–4 things you're actively working on right now? Could be a product line, a goal for the quarter, a partnership in progress, a hiring push — whatever's in flight. *(Or skip if you'd rather.)*"

If user skips, deliver the Q5b skip-cost message from above.

**Captures:** `## Current initiatives / things I'm working on` section.

### Q5c — Value props (1–3 bullets in user's own voice)

> "How do you typically frame what your company does, in your own words? Give me 1–2 sentences in your voice — these are the value props you lead with when meeting someone new. *(Or skip — I'll use a generic framing instead.)*"

If user skips, deliver the Q5c skip-cost message from above.

**Captures:** `## Value props I lead with` section.

### Q5d — Things to NOT bring up (any number of bullets)

> "Anything to NOT bring up in cold or early-relationship emails? (Specific revenue figures, internal team stuff, anything unannounced — that kind of thing.) *(Or 'nothing comes to mind' is a fine answer.)*"

If user says "nothing comes to mind", record that as a single bullet ("Nothing flagged — use general professional discretion") — this is NOT a skip; it's an explicit answer. If user explicitly skips, deliver the Q5d skip-cost message.

**Captures:** `## Things to NOT bring up in cold/early-relationship emails` section.

### Q5e — Conversation hooks (1–3 examples)

> "Last one — what's a line or angle you tend to open with naturally? Something like 'Curious how you're thinking about X' or 'Wanted to share something we're seeing — would love your read.' Give me 1–3 examples in your voice. *(Or skip — drafts will use a default opener.)*"

If user skips, deliver the Q5e skip-cost message from above.

**Captures:** `## Conversation hooks I tend to use` section.

---

After all 5 sub-prompts, write all sections to `client-profile/exec-themes.md` using the structure in `../../client-profile/templates/exec-themes.template.md`. Show the populated file to the user; ask: *"Read through it — anything to refine before we move on?"* Iterate on edits.

---

## Question 6 — Tavily (optional) *(retired in MCP-pivot wizard)*

This question is now handled by step 3 in `setup/SKILL.md` — Tavily presence is detected from the host's loaded tool list. The Composio-install path's Tavily-specific sub-step (step 2a-i) covers the case where the user is wiring it for the first time; see `canonical-messages.md` §10.2-MCP.

---

## Question 7 — CRM connection (optional) *(superseded by setup step 3.2)*

CRM provider selection is detected via step 3 in `setup/SKILL.md`. The CRM target database + 4-field mapping (Name / Company / Brief / Email draft) is captured during setup step 3.2 — the wizard lists databases in the user's connected CRM, asks which one contacts go to, fetches the live schema, and asks the 4 mapping questions there. The mapping is saved to the profile and reused silently by `capture-contacts` from its first run forward. See `canonical-messages.md` §10.6-CRM for the database-selection + mapping prompts.

---

## Question 8 — Output folder

**Prompt:**
> "Where should briefs and email-fallback files be saved? Default: `~/Documents/conference-followup/`. Accept this, or pick a different folder?"

**Captures:** `Output folder` field.

---

## Question 9 — LinkedIn skill setup *(detailed multi-stage flow lives in setup/SKILL.md step 8)*

The conversational opener:
> "Setting up the LinkedIn research piece. Two parts — first I need to find Chrome on your machine, then you'll log into LinkedIn one time in a Chrome window I'll open. Takes about 2 minutes. Ready?"

The full multi-stage protocol (detect Chrome → save paths → launch Chrome for login → wait for user → verify) is in `setup/SKILL.md` step 8. Always invoke `linkedin_scraper.py {setup|verify}` — never invoke the `cmd_*.py` files directly (they are module libraries with no main block).

If setup fails at any stage, use canonical wording from `canonical-messages.md` §10.4.

**Captures:** `LinkedIn research skill > Onboarded`, `Last verified` fields.

---

## Final confirmation

Before saving, show the synthesized profile and ask:

> "Here's the profile. Read through it. Tell me anything to change. I'll only save once you say it's right."

After confirmation, write the profile to `client-profile/exec-conference-profile.md` and confirm:

> "Saved to `<path>`. Connected: [Email tool], [Tavily | skipped], [CRM | skipped]. LinkedIn skill: ready. Output folder: `<folder>`.
>
> You can run `capture contacts from [event]` any time to process a brain dump. Or re-run setup if anything needs to change."
