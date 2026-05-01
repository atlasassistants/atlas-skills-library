# Conference Contact Capture

> Turn a post-event brain dump into researched briefs and ready-to-send personalized emails. The executive returns from a conference, pastes notes on the people they met, and gets back a full brief per person plus drafted follow-up emails in their voice — routed to their CRM.

## 1. What it does

You paste a free-form text dump of the people you met at an event:

> *"Met Sarah Chen, VP Product at Acme. Talked about pricing models. Met Marcus from LeanBrew, he's a 2nd-time founder doing coffee tech."*

The plugin:
1. Parses it into discrete contacts.
2. Researches each person on LinkedIn (using the embedded `linkedin-research` skill).
3. Researches their company website via Tavily — handles AI-built sites.
4. Builds a structured brief per person (Person summary / Company snapshot / Conversation context / Common ground / Suggested follow-up angle).
5. Drafts a personalized post-event email in your voice and adds it to your email Drafts.
6. Logs the brief as a file and writes a record to your CRM.

What you see in chat at the end:

```
Done — processed 5 contacts from SaaStr 2026.

Sarah Chen — VP Product, Acme Corp
She leads product at a Series B SaaS focused on enterprise onboarding.
Brief covers her background + the pricing-model conversation you had
Tuesday night. Gmail draft ready — opens with the dinner reference,
leads into your shared interest in usage-based pricing. Added to
your Notion contacts DB.

[...one block per contact, failures called out warmly...]

All briefs: ~/Documents/conference-followup/SaaStr-2026/
Gmail drafts are in your Drafts folder, ready to review and send.
```

## 2. Who it's for

Founders, executives, and EAs who attend conferences or networking events and want post-event followup that feels personal — without spending three hours per contact on LinkedIn and email drafting.

## 3. Required capabilities

- **Email read + draft** — pull recent sent emails for voice extraction; create email drafts
- **LinkedIn research** — per-person dossier with summary (provided by embedded sub-skill)
- **Web research / extraction** — read company websites, including AI-built ones
- **CRM write** — create records with mapped fields (optional — file-only mode supported)
- **File read + write** — store profile, voice, themes, briefs, checkpoints
- **Conversational interview** — onboarding wizard, intake parsing, mapping wizard

## 4. Suggested tool wiring

The skill body references capabilities abstractly. The default validated wiring is Composio MCP for everything except LinkedIn (embedded) and filesystem (host). Alternative wirings (direct vendor MCPs, Zapier MCP, etc.) work without code changes — the orchestrator picks tools from whatever the host has loaded.

| Capability | Validated default wiring | Alternative wirings (unvalidated, expected to work) |
|---|---|---|
| Email read+draft | Composio MCP → Gmail / Outlook / other email toolkit | Anthropic's Gmail MCP; Microsoft's Outlook MCP; Zapier MCP |
| Web search | Composio MCP → `TAVILY_SEARCH` (basic Tavily toolkit, not "Tavily MCP") | Tavily's direct MCP; Composio's `composio_search` toolkit (Exa-powered, no auth) |
| Web extract single URL | Composio MCP → `TAVILY_EXTRACT` | Tavily's direct MCP; Composio's `composio_search` `FETCH_URL_CONTENT` |
| CRM list/schema/insert | Composio MCP → Notion / HubSpot / Airtable / Salesforce / Pipedrive / etc. | Direct vendor MCPs (Notion's MCP); Zapier MCP |
| LinkedIn research | Embedded `linkedin-research` skill (Chrome automation; no MCP) | (no alternative — embedded skill is the only path) |
| File read+write | Host runtime's filesystem | (host-provided) |
| Conversational interview | Host runtime's chat | (host-provided) |

**Validated empirically:** `TAVILY_CRAWL` and `TAVILY_MAP_WEBSITE` returned empty results for typical small-company / SPA-style websites in testing. The plugin uses `TAVILY_SEARCH` + `TAVILY_EXTRACT` (with skill-body-driven sub-page selection) instead.

The `setup` skill walks first-time users through wiring Composio MCP if no email/web/CRM tools are detected. The `capture-contacts` skill discovers tools at runtime — there are no hardcoded tool names in the skill body.

## 5. Installation

```
/plugin marketplace add colin-atlas/atlas-skills-library
/plugin install conference-contact-capture@atlas
```

After install, you'll need:
- A Composio account ([composio.dev](https://composio.dev))
- A Tavily account ([tavily.com](https://tavily.com)) — optional but recommended
- Whatever email tool and CRM you already use, connected to Composio

The `setup` skill walks you through all of this.

## 6. First-run setup

Run the setup wizard on first use:

> "set up conference contact capture"

Or it auto-prompts when you try to use `capture-contacts` without a profile.

The wizard is detection-first: it checks what's already wired into your AI and only walks you through what's missing. Three branches:

- **Capabilities already wired, profile exists** → refresh mode (review each field, change anything you want)
- **Capabilities wired, no profile yet** → fast path (skip MCP install, jump straight to capturing identity / voice / themes)
- **Capabilities missing** → full onboarding (walks through wiring an email tool, web search, and optionally a CRM)

**Full onboarding** (only when capabilities are missing):

1. Picks a path — Composio MCP (the easy default; one signup connects all your tools) or your own MCPs (Anthropic's Gmail MCP, Tavily's direct MCP, etc.)
2. If Composio: walks you through signup, app connections (Gmail/Outlook, Tavily, your CRM), and installing the Composio MCP into your AI — using install instructions tailored to your AI by Composio's own onboarding page

**All branches then capture:**

3. Executive identity (name, title, company, one-line description)
4. **CRM target + field mapping** (only if a CRM provider was picked) — lists databases in your connected CRM, asks which one contacts should go to, then asks 4 mapping questions (which field for name / company / brief / email draft). One-time setup; saved to your profile so capture-contacts can write records silently from its first run.
5. Pulls last 30–50 sent emails to analyze your writing voice
6. Detects your usual email signoff
7. Asks for 3–5 themes you typically talk about with people in your network
8. LinkedIn skill setup (Chrome detection, LinkedIn login, virtual environment install)
9. Sets your output folder
10. Shows the synthesized profile, lets you tweak, then saves

If your connected CRM has no databases yet at setup time, the wizard will offer to skip CRM (mark provider as `none` in profile) or pause so you can create one and re-run setup.

You can re-run the wizard any time to refresh voice, themes, or change connections.

## 7. Skills included

- **`setup`** — onboarding wizard. Run once, refresh as needed.
- **`linkedin-research`** — researches a person on LinkedIn end-to-end. Auto-detects Chrome, walks the user through LinkedIn login on first run, paces requests safely (45s avg between scrapes, 25/day cap), and produces both a raw and a clean dossier per person. Independently invocable for ad-hoc LinkedIn lookup; also called by `capture-contacts` during contact processing.
- **`capture-contacts`** — main orchestrator. Trigger with phrases like "capture contacts from [event]" or "process my contacts from the conference."

## 8. Customization notes

- **Voice file** at `client-profile/conference-email-voice.md` — refine after first generation if it doesn't sound like you. The drafter reads from this file directly.
- **Themes file** at `client-profile/exec-themes.md` — edit any time to change what the briefs and emails emphasize.
- **CRM field mapping** — captured during `setup` (step 3.2) and saved to your profile. If your CRM schema changes later (a mapped field is renamed or deleted), the next `capture-contacts` run detects the stale mapping, halts only the CRM phase, and tells you to re-run `setup` to remap. Briefs and email drafts still save normally even when CRM is broken.
- **Methodology reference** at `skills/capture-contacts/references/atlas-conference-followup-methodology.md` — fork the plugin to override Atlas's defaults for brief structure or email tone.

## 9. Atlas methodology

This plugin is `opinionated` (per `methodology-patterns.md`):
- **Brief structure** — fixed sections (Person summary / Company snapshot / Conversation context / Common ground / Suggested follow-up angle / Source). Designed for conference-followup specifically, not generic CRM notes.
- **Email structure** — Personal opener (mentions where met + something specific) → Substance (common-ground angle) → Soft CTA → Signoff. Tested by Atlas on real exec follow-ups.
- **LinkedIn research methodology** — preserved from the existing `linkedin-research-skill` (Atlas-developed, tested, opinionated about dossier structure and pacing).

Override by editing the methodology reference docs — skill bodies stay stable.

## 10. Troubleshooting

**"My AI doesn't see my Composio tools."** Re-run `setup` — it will list what's currently wired into your AI's loaded tools. If Composio's tools are missing entirely, the most common causes are (1) the Composio MCP wasn't installed into your specific AI client (each client has its own install path — re-check Composio's install page for your AI), (2) the connection in Composio is for the wrong account (check the Connect Apps page in Composio's web dashboard), or (3) your AI hasn't reloaded since you connected the apps (restart your AI client). If you'd rather use a different MCP entirely (Anthropic's Gmail MCP, Tavily's direct MCP, etc.), tell setup which MCP you have and it will check.

**"Briefs feel thin — only LinkedIn info, no company info."** Tavily isn't connected. Re-run `setup` and complete the Tavily step, or check that your Tavily key is connected in your Composio dashboard.

**"LinkedIn rate limit reached."** The LinkedIn skill caps at 25 scrapes/day (account safety). The plugin saves a checkpoint and tells you the resume phrase. Resume the next day with "continue conference capture for [event name]".

**"My CRM records are missing fields."** Your CRM schema may have changed since onboarding. Re-run `setup` and the wizard will walk you through re-mapping only the fields that changed.

**"The drafted email doesn't sound like me."** Edit `client-profile/conference-email-voice.md` directly — add a paragraph describing the voice traits the auto-extraction missed. Or re-run `setup` after sending more emails (gives the analyzer more recent samples).

**"Setup says LinkedIn skill setup failed."** The most common cause is Chrome not being installed — install from google.com/chrome and re-run setup. Other causes: Python 3.10+ not installed, or the LinkedIn login session didn't complete in the browser window. The skill describes which one it hit; you don't need to debug manually.
