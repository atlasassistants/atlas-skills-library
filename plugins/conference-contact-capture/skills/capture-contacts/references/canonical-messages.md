# Capture-Contacts — Canonical User-Facing Messages

> The capture-contacts skill loads this reference and uses these messages verbatim at the points specified in `SKILL.md`. They were drafted during the design phase to preserve a careful, explicit, non-jargony voice. Substitute `[bracketed]` placeholders at runtime; otherwise preserve the wording.

`[bracketed]` = substitute at runtime (names, paths, errors).

---

## §10.5 Phase 0 prerequisite checks

Used at: `SKILL.md` Phase 0, when one of the pre-flight checks fails.

**Profile not found:**

> Looks like this is your first time using the plugin — let me walk you through setup right now (takes ~10 minutes).

**LinkedIn skill not onboarded:**

> Heads up — the LinkedIn research piece isn't set up yet. Without it, briefs are much less rich.
>
> Want me to run that setup now? Takes about 2 minutes (Chrome auto-detect, LinkedIn login in a browser window, then we're ready).
>
> Or if you want to proceed without it, say "skip LinkedIn" — I'll continue with company research only.

**Composio unreachable:**

> Can't reach Composio right now. Two common causes:
> - Your `COMPOSIO_API_KEY` env var isn't set, or has the wrong key
> - You're offline or behind a network blocking Composio's API
>
> Want me to walk you through verifying your API key? Or check your network and try again.

---

## §10.6 Phase 1 intake

Used at: `SKILL.md` Phase 1, when asking for the brain dump and confirming the parsed contact list.

**Asking for the brain dump:**

> Tell me about the people you met. Free-form is fine — names, companies, anything you remember from the conversation. I'll parse it into individual contacts and read it back to you before doing anything.
>
> Example: *"Met Sarah Chen, VP Product at Acme. Talked about pricing models. Met Marcus from LeanBrew, he's a 2nd-time founder doing coffee tech. Priya runs ops at some logistics company, didn't catch the name."*

**Confirming parsed contacts:**

> Here's what I parsed — *[N contacts]*:
>
> 1. Sarah Chen (Acme) — pricing models conversation
> 2. Marcus (LeanBrew) — 2nd-time founder, coffee tech
> 3. Priya (logistics company, name not captured) — runs ops
>
> Look right? Tell me anything to add, fix, or remove. When it's right, I'll start researching.

---

## §10.7 Phase 4 brief retry

Used at: `SKILL.md` Phase 4, only after one silent auto-retry has already failed.

(Triggered only after one silent auto-retry has already failed.)

> *[Person name]* — *[Title], [Company]*
>
> The brief for *[Name]* didn't come together this run. *(Their LinkedIn research and company info are saved, so a retry won't re-do that work.)*
>
> Want me to try the brief again, or skip *[Name]* for now and continue with the others?

---

## §10.8 Phase 5 email draft fallback

Used at: `SKILL.md` Phase 5, when draft creation fails after retry; email content saved as file.

(When draft creation fails after retry; email content saved as file.)

> *[Person name]* — *[Title], [Company]*
>
> Brief written ✓. The email draft creation didn't work this run — saved the email content here: `[output_folder]/[event-slug]/[person-slug].email.md`. You can paste it into a new draft when you're ready.

---

## §10.9 Phase 6 CRM mapping mismatch

Used at: `SKILL.md` Phase 6, when the CRM rejects writes with a field-not-found-style error.

> Your CRM looks a little different from when you set this up — some of the fields don't match anymore. Want me to walk through the mapping again? I'll only ask about the fields that changed, not all of them.
>
> Briefs and email drafts are still being created — the CRM step is the only thing on hold.

---

## §10.10 Phase 7 humanized summary

Used at: `SKILL.md` Phase 7, the final chat summary every successful run uses.

The format every successful run uses. One block per contact, failures called out warmly inline, file paths summary at the end.

```
Done — processed [N] contacts from [event name].

[Person name] — [Title], [Company]
[1–2 sentences on the person, drawn from brief]. Brief covers
[what's in it, including the conversation reference if present].
[Email tool] draft ready — opens with [the personal opener angle],
leads into [the substance angle]. Added to your [CRM] [target name].

[Repeat per contact. For failures:]

[Person name] — [Title], [Company] (heads up)
[Plain-language description of what didn't work.] [What you got
instead.] [Where it landed.]

[After all contacts:]

All briefs: [output_folder]/[event-slug]/
[Email tool] drafts are in your Drafts folder, ready to review and send.
```

**Concrete example** (anonymized — also goes in README §1):

```
Done — processed 5 contacts from SaaStr 2026.

Sarah Chen — VP Product, Acme Corp
She leads product at a Series B SaaS focused on enterprise onboarding.
Brief covers her background + the pricing-model conversation you had
Tuesday night. Gmail draft ready — opens with the dinner reference,
leads into your shared interest in usage-based pricing. Added to your
Notion contacts DB.

Marcus Lee — Founder, LeanBrew
8-year founder, ex-Stripe engineer. Brief covers his coffee-tech
startup and the SF pop-up he mentioned. Gmail draft ready — references
your offer to intro him to investors. Added to your Notion DB.

Priya Shah — Head of Ops, Northwind (heads up)
Couldn't find a clear LinkedIn match — brief uses your conversation
notes only. Gmail draft is more generic. Added to Notion with a flag.

[+2 more — Jess Kim, Tom Ruiz — both fully processed]

All briefs: ~/Documents/conference-followup/SaaStr-2026/
Gmail drafts are in your Drafts folder, ready to review and send.
```

---

## §10.11 Resume after LinkedIn rate limit

Used at: `SKILL.md` Phase 2 (on rate-limit hit) and the resume flow (on resume trigger).

**On hit:**

> LinkedIn limit reached at contact *[N]* of *[total]*. Saved progress — your completed contacts are done, the rest are waiting.
>
> Resume tomorrow with: **"continue conference capture for [event name]"**.
>
> (LinkedIn caps scrapes at 25/day to keep your account safe. The cap resets ~24 hours after your earliest scrape today.)

**On resume:**

> Picking up where we left off on *[event name]*. *[N]* contacts were already processed; *[remaining]* to go.
>
> Starting LinkedIn research on *[next contact name]*…

---

*These messages were drafted in the design phase (spec §10.5–§10.11). Drift is fine over time — but the starting point lives here so the careful tone work isn't lost on first implementation.*

---

### 10.4-Phase0 — Capabilities not wired (capture-contacts pre-flight)

Used at: `SKILL.md` Phase 0, when a required capability is missing from the host's loaded tool list.

> "Heads up — I don't see [an email tool / a web research tool / a CRM tool] wired into your AI right now. This plugin needs that to [pull your sent emails for voice analysis / research the people you met / save contacts to your CRM].
>
> Want me to walk you through getting one connected? The easiest path is Composio MCP — takes about 5 minutes. If you have your own MCP for [email / web / CRM], that works too — just let me know what you have and I'll check."

---

### 10.6-CRM-incomplete — CRM provider set but target/mapping missing (capture-contacts Phase 6)

Used at: `SKILL.md` Phase 6, when the profile names a CRM provider but `crm_target` or `crm_field_map` is empty (CRM target+mapping is captured at setup; this state means setup didn't finish the CRM step — e.g. no databases existed at the time).

> "Your CRM (<provider>) is connected but not fully set up — I don't have a target database or field mapping in your profile yet. Briefs and email drafts are saving fine; the CRM record write is the only thing on hold.
>
> Run `set up conference contact capture` and walk through the CRM step when your <provider> has a database ready, then this'll work the next time you capture contacts."
