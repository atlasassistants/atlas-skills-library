# Setup Wizard — Canonical User-Facing Messages

> The setup skill loads this reference and uses these messages verbatim at the points specified in `SKILL.md`. They were drafted during the design phase to preserve a careful, explicit, non-jargony voice. Substitute `[bracketed]` placeholders at runtime; otherwise preserve the wording.

`[bracketed]` = substitute at runtime (names, paths, errors).

---

## §10.1 Composio introduction

Used at: `SKILL.md` step 1, when Composio is not yet reachable.

> Before we go further, this plugin needs **Composio**. Composio is a free service that lets one tool (like this plugin) talk to all your other tools — your email, your CRM, web research — without you having to set up separate integrations for each.
>
> I'm going to walk you through the setup using our setup guide — it's about 5 steps and takes ~3 minutes. We'll connect your email tool (required), and optionally Tavily for company research and your CRM for contact storage.
>
> Whenever you're ready, say "ok" and I'll start.

**Note:** This §10.1 is from the 2026-04-29 (pre-MCP-pivot) wizard. The MCP-pivot wizard uses §10.1-MCP below instead — kept here for reference only.

---

## §10.2 Tavily explanation

Used at: `SKILL.md` step 4, before asking the user whether to set up Tavily.

> Next: **Tavily**. This is what makes the company research in your briefs good — it reads company websites (including modern AI-built ones that other tools can't read) and pulls out the useful info. Without it, briefs only have the LinkedIn info on the person, which is thinner.
>
> Strongly recommended — free for our usage (1000 calls/month, you'll use way less). Setup takes ~1 minute:
> 1. Go to **tavily.com** and sign up (Sign up with Google is fastest)
> 2. Copy your API key from the Tavily dashboard
> 3. Open your **Composio dashboard** → Connect Apps → search "Tavily" → click Connect → paste your API key
>
> Tell me when done — I'll verify it.
>
> If you'd rather skip, say "skip Tavily." Briefs will use LinkedIn-only context. You can add Tavily later by re-running setup.

---

## §10.3 CRM introduction

Used at: `SKILL.md` step 5, when introducing CRM connection.

> Now for your **CRM**. This is where the contacts you process get saved as records, so you can track who you've followed up with and find them again later. It could be Notion, HubSpot, Airtable, Salesforce — whatever you already use to keep contacts.
>
> If you don't use a CRM, totally fine — output goes to local files + email drafts only. You can add a CRM later by re-running setup.
>
> To connect one:
> 1. In your **Composio dashboard** → Connect Apps → search for your CRM (Notion, HubSpot, etc.) → follow their connection steps
> 2. Tell me when done. I'll then show you the databases/tables in your CRM and walk you through which one to use and how to map the fields (Name, Company, Brief, Email).
>
> Or say "skip CRM" to keep output as files + drafts only.

---

## §10.4 LinkedIn skill setup failed

Used at: `SKILL.md` step 8 (LinkedIn skill setup), when any stage of the `linkedin_scraper.py setup` multi-stage flow exits non-zero. Substitute `[plain-language version of the actual error]` with a humanized rendering of the JSON `reason`/`detail` fields — not the raw traceback.

> The LinkedIn research piece couldn't finish setting up. Here's what happened: *[plain-language version of the actual error]*
>
> Most likely fix:
> - **If Python isn't on your computer:** install it from python.org (any 3.10 or newer version is fine). Tell me when done — I'll retry.
> - **If the install couldn't complete (network or permission issue):** this is usually temporary. Want me to retry now?
> - **If Chrome wasn't detected:** install Chrome from google.com/chrome and tell me when done; I'll retry.
> - **If LinkedIn login didn't complete:** I can re-run the login flow now.
> - **If you saw something else:** describe what you saw on screen and I'll help figure out what happened.
>
> Either way — you don't need to run anything technical yourself.

---

*These messages were drafted in the design phase (spec §10.1–§10.4). Drift is fine over time — but the starting point lives here so the careful tone work isn't lost on first implementation.*

---

### 10.1-MCP — MCP-aware Composio introduction (replaces 10.1 for the MCP-pivot wizard)

> "This plugin needs three capabilities wired into your AI: read & draft emails, search & read web pages, and (optionally) write records to your CRM.
>
> The easiest way to get all three is to install **Composio MCP** — a free service that connects your AI to your tools (Gmail, Notion, Tavily, etc.) in one place. We'll walk through the setup together; takes about 5 minutes.
>
> If you'd rather wire your own MCPs (e.g., the Gmail MCP from Anthropic, Tavily's own MCP, etc.), that works too — just let me know what you have and I'll check.
>
> Which would you like to do? (Default is Composio.)"

### 10.2-MCP — Tavily wizard step (replaces 10.2 for the MCP-pivot wizard)

> "For Tavily specifically, the connection in Composio needs your API key:
>
> 1. Go to tavily.com → Sign up (Sign up with Google is fastest).
> 2. Copy your API key from the Tavily dashboard.
> 3. In Composio's Connect Apps page, search 'Tavily', click Connect, paste your API key, save.
> 4. Tell me when done — I'll verify with a test search."

(Note: there's a separate Composio toolkit called "Tavily MCP" — it currently has issues at Tavily's end. If the user accidentally connects that one, the verification test search will fail and the wizard surfaces a hint to switch to plain "Tavily" instead. See Phase 0 detection in `setup/SKILL.md`.)

### 10.3-MCP — Composio install help when user is stuck

> "No worries. Send me a screenshot of what you see on your screen and tell me which device you're on (Mac / Windows / Linux). I'll walk you through it from there based on what you see."

### 10.4-Phase0 — Capabilities not wired (capture-contacts pre-flight)

> "Heads up — I don't see [an email tool / a web research tool / a CRM tool] wired into your AI right now. This plugin needs that to [pull your sent emails for voice analysis / research the people you met / save contacts to your CRM].
>
> Want me to walk you through getting one connected? The easiest path is Composio MCP — takes about 5 minutes. If you have your own MCP for [email / web / CRM], that works too — just let me know what you have and I'll check."

### 10.6-CRM — CRM target + field mapping ask (setup wizard step 3.2)

> "Setting up your CRM connection for this plugin (one-time — won't ask again unless your CRM schema changes).
>
> I see these databases/tables in your <CRM provider>: <list>. Which one should contacts go to?"

(After user picks)

> "Got it — using <chosen database>. Now I need to know which fields to use for each piece of contact info.
>
> Here are the fields available: <list of field names>.
>
> 1. Which field should hold the contact's name?
> 2. Which field for their company?
> 3. Which long-text field for the brief content?
> 4. Which long-text field for the email draft?"
