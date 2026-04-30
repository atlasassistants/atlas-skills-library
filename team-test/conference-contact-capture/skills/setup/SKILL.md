---
name: setup
description: One-time onboarding wizard for the conference-contact-capture plugin. Detects whether the host's AI has email / web / CRM capabilities wired (via Composio MCP, direct vendor MCPs, or any other source). If capabilities are missing, walks the user through wiring them — Composio MCP is the easy default; own MCPs work too. Captures executive identity, extracts email voice from past sent emails, captures themes / focuses, runs the embedded LinkedIn skill's setup, saves the canonical profile. Resumable mid-flow. Re-runnable to refresh any field.
when_to_use: Run before using `capture-contacts` for the first time. Trigger phrases — "set up conference contact capture", "onboard conference plugin", "configure conference capture", "refresh conference profile", "redo conference setup". Auto-trigger when `capture-contacts` reports no profile exists at the configured path.
atlas_methodology: neutral
---

# setup

Onboarding wizard for `conference-contact-capture`. Detection-first: figures out what the user already has wired and only walks them through what's missing. Three branches: refresh (profile exists), fast (capabilities wired, no profile yet), full onboarding (capabilities missing).

## Purpose

The capture-contacts skill can only produce good briefs and on-brand emails if it knows the executive's identity, voice, themes, and connected tools. This skill captures all of that in one structured flow, while skipping any setup the user has already completed.

## Inputs

- **Existing profile** (optional) — if `client-profile/exec-conference-profile.md` exists, the skill enters refresh mode automatically.
- **Host's loaded tool list** — required. Skill reads what tools the host has wired and uses that to detect capability presence.
- **Conversational interview** — questions in `references/onboarding-questions.md`, asked one at a time, paraphrased back for confirmation.

## Required capabilities

(Abstract list — no specific tool names. Validated default wiring is Composio MCP; see plugin README §4 for alternatives.)

- Detection of available email / web / CRM tools in the host's loaded tool list
- Email read (pull recent sent emails) — needed for voice extraction
- Web search and web extract (single URL) — optional, recommended
- CRM list databases / get schema (used at step 3.2 when a CRM provider is picked) — optional
- Subprocess (runs `../linkedin-research/linkedin_scraper.py` — the embedded LinkedIn skill's CLI entry point; multi-stage `setup` and `verify` subcommands)
- File read + write
- Conversational interview (one question at a time)

## Steps

> **Note on "workspace".** "Workspace" = the user's current working directory at the time the skill is invoked (i.e. where the host runtime was started). All `client-profile/...` paths and the `.conference-onboarding-in-progress.json` marker resolve relative to this directory. Do NOT write these into the plugin's own install directory — that location is read-only / shared across users.
>
> **Note on paths.** Profile is workspace-relative (default `client-profile/exec-conference-profile.md`). Templates are plugin-relative (`<plugin-root>/client-profile/templates/`).
>
> **Note on tool calls.** Throughout this skill, "use the available email tool" / "use the available web search tool" / etc. means: pick from the host's loaded tools the one that best fits the described capability. If multiple candidates exist (e.g. Composio Gmail toolkit and Anthropic's Gmail MCP both loaded), prefer the one matching the provider name in the profile (or ask the user once for this run only if no profile yet).
>
> **Note on detecting capabilities.** Detection uses two patterns depending on how the user wired their tools.
>
> **Pattern A — Aggregator MCPs (Composio, Zapier MCP, etc.).** These expose generic *meta-tools* (a small fixed set) rather than one tool per app. The connected apps live *inside* the meta-tool parameters, not in tool names.
>
> Detection is two-stage:
>
> 1. **Presence check** — does the host have a meta-tool prefix loaded? Look for `mcp__composio__*` (Composio) or `mcp__zapier__*` (Zapier MCP) etc. If yes, the aggregator MCP itself is wired.
>
> 2. **Connection query (authoritative).** For **Composio specifically**, call `COMPOSIO_SEARCH_TOOLS` with one query per capability the plugin cares about (use cases like `"send an email"`, `"search the web"`, `"create a record in CRM"`) and parse the response's `toolkit_connection_statuses` array — each entry has `{toolkit: <slug>, has_active_connection: <bool>, accounts: [...]}`. A capability is wired iff at least one matched toolkit has `has_active_connection: true`.
>
>    Map slugs to capabilities:
>    - `gmail`, `outlook` → email
>    - `tavily`, `exa`, `firecrawl` → web search/extract
>    - `notion`, `airtable`, `hubspot`, `salesforce`, `pipedrive` → CRM
>    - Other slugs (e.g. `googlecalendar`, `slack`, `github`) → not used by this plugin; ignore
>
>    **Fast-path optimization (refresh mode only).** Composio also embeds a connected-apps list in `COMPOSIO_SEARCH_TOOLS`'s tool description as `"manually connected the apps: <comma-separated-list>"`. This is *cached at session start* and goes stale if the user connects/disconnects apps mid-session — verified empirically. Use it ONLY as a quick hint when the user is in refresh mode and capabilities haven't changed; do NOT trust it during first-run onboarding.
>
>    For **other aggregator MCPs** (Zapier, etc.), use their equivalent discovery / list-connections function. Whatever returns authoritative live state, not cached metadata.
>
> If stage 2 errors or returns empty, treat all capabilities behind that aggregator as NOT wired (don't assume — the user may have installed the MCP but not connected any apps yet).
>
> **Pattern B — Direct vendor MCPs (Anthropic Gmail MCP, Tavily direct MCP, Notion's MCP, etc.).** These expose one or more tools per service, with the vendor name in the prefix. Look for tool names containing keywords:
> - **Email read/draft** — `gmail`, `outlook`, `email`, `imap` (e.g. `mcp__claude_ai_Gmail__*`, `mcp__gmail__*`, `mcp__zapier__email_*`)
> - **Web search/extract** — `tavily`, `search`, `extract`, `firecrawl`, `exa`, `fetch_url` (e.g. `mcp__tavily__*`)
> - **CRM** — `notion`, `airtable`, `hubspot`, `salesforce`, `pipedrive`, `crm` (e.g. `mcp__notion__*`)
>
> A capability counts as "wired" only if at least one tool matching that capability is BOTH discoverable AND callable in the current session. Auth-bootstrap tools (e.g. `*_authenticate` with no fetch/draft companion) do NOT count — they require a separate auth step before usable tools appear.
>
> **Both patterns can coexist.** A user might have Composio (meta-tools) AND Anthropic's Gmail MCP (direct) loaded. Run pattern A first, then pattern B; merge the results; if a capability is satisfied by both, present both options to the user at step 3.

### 0. Detection (always first)

Before any other step:

1. **Check for existing profile** at `client-profile/exec-conference-profile.md`.
2. **Check for capabilities** in the host's loaded tool list:
   - Email-pulling tool present?
   - Web search/extract tool present?
   - CRM-write tool present?
3. **Check for in-progress onboarding** marker `.conference-onboarding-in-progress.json` in the workspace.

Branch:
- **Profile exists + all needed capabilities wired** → refresh mode (jump to "Refresh mode" section after step 10).
- **Capabilities wired, no profile** → fast path (skip to step 3).
- **In-progress marker found** → resumed session (load marker, skip questions already answered, continue from where left off).
- **Capabilities missing** → full onboarding (step 1).

---

### 1. Explain what's needed (full onboarding only)

Use canonical-messages §10.1 from `references/canonical-messages.md` (introduces Composio at a high level), with this updated lead-in (since we now offer alternatives):

> "This plugin needs three capabilities wired into your AI: read & draft emails, search & read web pages, and (optionally) write records to your CRM.
>
> The easiest way to get all three is to install **Composio MCP** — a free service that connects your AI to your tools (Gmail, Notion, Tavily, etc.) in one place.
>
> If you'd rather wire your own MCPs (e.g., the Gmail MCP from Anthropic, Tavily's own MCP, etc.), that works too — just let me know what you have and I'll check.
>
> Which would you like to do? (Default is Composio.)"

If user picks Composio → step 2a. If user picks own MCPs → step 2b.

### 2a. Composio path (default)

Direct the user (don't run shell commands for them):

> "Here's the Composio setup, in order:
>
> 1. Sign up at composio.dev (free).
> 2. Click **Connect Apps** in the left sidebar.
> 3. Connect the apps you want to use:
>    - Your email tool (required) — Gmail or Outlook
>    - Tavily (optional, strongly recommended for company research)
>    - Your CRM (optional) — Notion, HubSpot, Airtable, Salesforce, etc.
> 4. Click **Install** in the left sidebar.
> 5. Pick the install card for your AI (Claude Code, Claude Desktop, Codex, ChatGPT, etc.) and follow the steps on that page — they're tailored to your AI and OS. The install uses **OAuth (one browser-based 'authorize' click)**; no API keys to copy or paste.
>
> Where are you?
> - **(a) Done — installed and authenticated.** I'll re-check what's wired.
> - **(b) Got stuck on a specific step.** Tell me which one and what you saw.
> - **(c) Composio's dashboard looks different from what I described.** Send a screenshot."

On **(a)**: re-run detection. If now successful → continue to step 3 (or step 2a-i if Tavily was picked, see below). If detection still doesn't see Composio tools, ask: "Which AI client did you install for? Did you reload/restart the client after authorizing?" (most clients need a session restart to pick up newly-added MCP servers).

On **(b)**: ask what error or screen they're seeing at that specific step. Common gotchas:
- **Step 1 (signup)**: blocked by SSO / corporate firewall → suggest personal Google login or a different network
- **Step 3 (connecting an app)**: OAuth window doesn't open or closes immediately → check popup blocker; suggest trying in an incognito window
- **Step 5 (AI install)**: terminal command errors out for Claude Code → check `claude --version` is recent enough; suggest reinstalling Claude Code; check `claude mcp list` to see if the server already exists with the wrong name

On **(c)**: deliver §10.3-MCP from `references/canonical-messages.md` and walk based on screenshots.

Iterate until install succeeds.

#### 2a-i. Tavily-specific sub-step (only if user picked Tavily during step 2a)

Deliver this canonical message verbatim from `references/canonical-messages.md` §10.2-MCP (loaded by Task 12):

> "For Tavily specifically, the connection in Composio needs your API key:
>
> 1. Go to tavily.com → Sign up (Sign up with Google is fastest).
> 2. Copy your API key from the Tavily dashboard.
> 3. In Composio's Connect Apps page, search 'Tavily', click Connect, paste your API key, save.
> 4. Tell me when done — I'll verify with a test search."

When user confirms done, run a test web search via the available web search tool with query `"test search"`. If it returns results → Tavily is wired correctly. If error returns:

- "Tool not found" or similar → likely the user connected "Tavily MCP" instead of "Tavily" (these are two different toolkits in Composio). Tell them: *"Looks like you may have connected 'Tavily MCP' instead of 'Tavily' — they're separate. Go back to Connect Apps, search 'Tavily' (no MCP suffix), click Connect, paste your API key."*
- "Unauthorized" or API-key error → API key not pasted correctly. Walk them through re-pasting.

### 2b. Own-MCPs path

Ask: *"What MCPs do you have wired? (e.g., Gmail MCP, Tavily MCP, Notion MCP, etc.)"*

User describes their setup. Re-run detection (per the "Note on detecting capabilities" at the top of Steps).

**Verify each claimed capability with a real test call.** Don't trust self-report — MCPs frequently break silently (auth expired, server crashed, wrong scope). For each capability the user says is wired:

- **Email** — call the email tool with a minimal "list 1 recent email" / "fetch latest message" request. If it returns metadata for at least one message → ✓. If it errors with auth/permission/network failure → tell the user the specific error; offer to either fix it (re-auth in their MCP's dashboard) or wire Composio's Gmail/Outlook as a backup for this one capability.
- **Web search** — call the web search tool with query `"test"`. If it returns >0 results → ✓. If it errors → same options as above.
- **CRM** — call the CRM tool's "list databases" / "list bases" / "list tables" function. If it returns a non-empty list → ✓. If it errors → same options.

Show the user the result of each test:

> "Tested your wiring:
> - **Email** (your Gmail MCP): ✓ — pulled the latest message in your inbox
> - **Web search** (your Tavily MCP): ✗ — got `Unauthorized: API key invalid`
> - **CRM** (Notion MCP): ✓ — found 3 databases in your workspace
>
> One issue: your Tavily MCP isn't authorized. Want to fix that, or wire Tavily via Composio as a fallback (~2 minutes)?"

If gaps remain (capability not wired at all, or wired but failed verification), point at the specific missing capability and offer the Composio fallback for that one capability only:

> "I see you have email and CRM wired, but no web search/extract. Want me to walk you through getting Tavily wired via Composio? Takes ~2 minutes."

Iterate until all needed capabilities are wired AND verified (or user explicitly skips a capability — only Tavily and CRM are skip-tolerant; email is required).

---

### 3. Confirm what's wired and pick what to use

Query the host's loaded tools and identify which ones can handle each capability. Present back to user:

> "Looks like you have these wired:
> - **Email**: [Gmail via Composio | Outlook via Composio | Anthropic's Gmail MCP | etc.]
> - **Web search/extract**: [Tavily via Composio | Tavily direct MCP | none]
> - **CRM**: [Notion via Composio | HubSpot via Composio | etc. | none]
>
> Which should this plugin use?"

User picks. Capture the **provider name** in running state (`gmail`, `outlook`, `tavily`, `notion`, etc.) — NOT the specific tool slug or MCP source.

If only one option exists for a capability, confirm-and-skip ("Using Gmail for email — sound good?").

If web tool or CRM is missing entirely → ask: "Skip [web research / CRM]?" (Both are skip-tolerant; email is not.)

#### 3.1. Account selection (multi-account check)

After the user picks a provider, check whether multiple accounts exist for that provider in the wiring. The detection mechanism varies by aggregator:

- **Composio (Pattern A).** The `toolkit_connection_statuses[].accounts[]` array from `COMPOSIO_SEARCH_TOOLS` lists all connected accounts. If `accounts.length > 1` OR `account_selection: "required"`, multi-account selection is needed. Each account has `id`, optional `alias`, and a `user_info` block with the email address (or equivalent identifier).
- **Direct vendor MCPs (Pattern B).** Most direct-vendor MCPs are single-account by design (one OAuth token per server). If a vendor MCP supports multi-account, follow its discovery convention (often `list_accounts` or similar). If unclear, treat as single-account.

If multiple accounts exist for the chosen provider, ask the user which one to use:

> "I see [N] [provider] accounts connected: [list — show alias if set, otherwise email address, plus a short identifier]. Which one should this plugin use?"

Capture the user's choice as the **account identifier** for that provider — prefer the human-readable `alias` when set; otherwise the email/identifier; otherwise the `id`. Store in the profile under the provider's `account` field. The orchestrator passes this identifier when invoking the email/CRM tool so calls hit the right account.

If only one account exists, capture the single account's identifier silently (no prompt) so subsequent runs are deterministic.

#### 3.2. CRM target database + field mapping (skip if CRM not picked)

If the user picked a CRM provider in step 3 (i.e. didn't choose "skip CRM"), capture the target database and field mapping now. This is one-time setup — `capture-contacts` uses the saved mapping silently for every subsequent run.

**3.2a. List databases.** Use the available CRM tool to list databases / tables / bases in the user's connected CRM account. Cache the result for the next two sub-steps.

If the list is empty (no databases exist yet in the user's CRM):

> "I don't see any databases in your `<CRM provider>` account yet. Two options:
> - **Create one now** — go to `<CRM provider>`, set up a database with at least 4 fields (a name field, a company field, a long-text field for the brief, and a long-text field for the email draft), then tell me 'done' and I'll re-list.
> - **Skip CRM for now** — I'll mark CRM as `none` in your profile; briefs and email drafts will still work, you just won't get a CRM record. You can re-run setup later to add it."

If the user creates a DB and confirms 'done', re-list and continue. If the user picks skip, set `crm_provider: none` in running state and skip ahead to step 4 (identity).

**3.2b. Pick the target database.** Deliver the first part of canonical-messages §10.6-CRM verbatim ("I see these databases/tables in your `<CRM provider>`: `<list>`. Which one should contacts go to?"). Show the list, ask which one. Save the chosen target's ID and human-readable name to running state under `CRM > Target database`.

**3.2c. Get the schema.** Use the available CRM tool to fetch the chosen target's schema (fields / properties + types). Cache.

**3.2d. Map the four fields.** Deliver the second part of canonical-messages §10.6-CRM verbatim, listing the available field names from the schema. Ask the four mapping questions — name, company, brief, email draft — one at a time, paraphrasing each answer back. Save the mapping to running state under `CRM > Field mapping`.

If the schema is missing the field types the plugin needs (e.g. no long-text / rich-text field exists for the brief content), surface plainly:

> "Your `<CRM provider>` database doesn't have a long-text field for the brief content. Want me to map only the fields that fit (name, company) and leave the brief field blank in CRM records, or pause here so you can add a long-text field and we re-pick the target?"

Save running state to `.conference-onboarding-in-progress.json`.

### 4. Identity

Use Question 1 from `references/onboarding-questions.md`. Capture: name, title, company, one-line company description.

**Handle partial answers gracefully.** If the user replies with fewer than 4 sub-fields, do not re-deliver the whole prompt or guess the missing ones. Capture what they gave and ask for the missing fields one at a time, conversationally:

- Got name only → *"Got it — [Name]. What's your title?"*, then *"And your company?"*, then *"And a one-line description of what [Company] does?"*
- Got name + title → *"Got it — [Name], [Title]. What's your company?"*, then *"And a one-line description of what [Company] does?"*
- Got name + title + company → *"Got it — [Name], [Title] at [Company]. And a one-line description of what [Company] does?"*

Once all four are captured, deliver the paraphrase from Q1 (*"Got it: [Name], [Title] at [Company]. The company [one-line description]. Got that all right?"*) and accept correction or confirmation.

**Paraphrase cleanup rule.** When echoing the user's input back, do **light cleanup** — fix capitalization, fix obvious typos, tighten run-on phrasing — but preserve the user's voice and word choices. Don't rewrite for clarity, don't add details that weren't said, and don't drop nuance. The user must recognize their own description in the paraphrase. If you make any non-trivial change, the user should be able to spot it and correct you.

Update `.conference-onboarding-in-progress.json`.

### 5. Voice extraction

Use Question 3 from `references/onboarding-questions.md`. Use the available email tool to pull last 30–50 of the user's **outbound** sent emails (i.e. emails sent to other people, not emails the user sent to themselves as drafts/notes/automated reports).

**Filter for outbound communications.** Self-addressed emails (todo lists sent to self, automated reports, drafts) pollute voice analysis — they reflect private note-taking style, not how the user writes to others. Build the query to exclude self:

- Get the user's own email address first (from the email tool's metadata / the chosen account info).
- Use the email tool's query syntax to exclude self-recipients. For Gmail: `in:sent -to:<self_email> -cc:<self_email> -bcc:<self_email>`. For other email tools, use the equivalent — the principle is the same: keep only emails where at least one recipient is not the sender.
- If filtering returns fewer than 10 outbound emails, fall back to the unfiltered `in:sent` query and note in the voice profile that some self-emails may have been included.

> **Path convention reminder.** Templates referenced are **plugin-relative** (`../../client-profile/templates/...`). Outputs are **workspace-relative** (`client-profile/...`).

**Process emails in batches, not all at once.** Email-with-full-body responses can be large — pulling 30–50 emails with bodies often exceeds the orchestrator's working context window in a single response, regardless of which email tool is used. Some aggregators (e.g. Composio) auto-offload large responses to a sandbox file and surface a path; others may truncate or paginate. Either way, the orchestrator should NOT try to read all emails inline at once.

Recommended batching pattern (works across email tools):

1. Pull metadata + IDs for the full set first (lightweight call — `ids_only: true` for Gmail, equivalent for others). Confirms the count and lets the user see how many will be analyzed.
2. Hydrate bodies in batches of 5–10 emails at a time.
3. Per batch: extract structured signals (sentence length distribution, opening phrases, closing phrases, vocabulary markers, formality cues) — keep the per-batch summary tight, not raw text.
4. After all batches, synthesize one consolidated voice profile from the per-batch summaries. The consolidated profile is what gets written; raw bodies and per-batch summaries are discarded after consolidation.

If the email tool returns the full set offloaded to a sandbox/temp file, use the equivalent of a stream-and-batch approach against that file instead of reading it whole.

If pull returns 30+ outbound emails: run the batched voice analysis above (use the LLM's reasoning — analysis structure follows the section headings in `../../client-profile/templates/email-voice.template.md`: Tone, Sentence structure, Vocabulary patterns, Opening patterns, Closing patterns, Formatting habits, Things this voice avoids, Sample emails).

Write the consolidated result to `client-profile/email-voice.md` (workspace-relative). Show the synthesized voice profile to the user; ask if anything should be refined before saving.

If pull returns <10 outbound emails or errors: ask the user to paste 5–10 sample emails directly. Build the voice profile from those. If they decline, skip voice extraction (drafter will use generic professional tone — flag in profile as `Profile completeness: partial — voice missing`).

### 6. Email signoff detection

Use Question 4 from `references/onboarding-questions.md`. From the emails pulled in step 5, detect the most common closing pattern (e.g., "Best,", "Thanks,", "— Sam"). Show the detected signoff to the user and ask: keep it, or pick something else? Save the confirmed signoff to the `Email signoff` field in running state — it lands in the main `exec-conference-profile.md` at step 10, not in a separate file.

If voice extraction in step 5 was skipped (no emails available), ask directly: *"What signoff would you like to use for follow-up emails?"* Save the answer the same way.

### 7. Themes capture

Use Question 5 from `references/onboarding-questions.md`. Capture 3–5 themes + 2–4 current initiatives + value props + things to NOT bring up + conversation hooks. Write to `client-profile/exec-themes.md` using the structure in `../../client-profile/templates/exec-themes.template.md`.

### 8. LinkedIn skill setup

The embedded `linkedin-research` skill has its own CLI entry point: `python <plugin-root>/skills/linkedin-research/linkedin_scraper.py {setup|verify|scrape}`. The `cmd_setup.py` / `cmd_verify.py` / `cmd_scrape.py` files are *module libraries imported by linkedin_scraper.py* — invoking them directly does nothing. Always invoke `linkedin_scraper.py`, never the `cmd_*.py` modules.

**Setup is multi-stage**, not a single command. The orchestrator coordinates 5 stages, prompting the user only when needed (Chrome path missing, login required).

#### 8.0. Pre-check — already onboarded?

Check whether `~/.linkedin-scraper-config.json` exists and contains a `chrome_path`. If yes, the LinkedIn skill is likely already set up from a prior plugin install — skip to **verify-only** below.

If the file is absent or missing `chrome_path`, run **fresh onboarding** below.

#### 8.1. Verify-only path (config exists)

Tell the user:
> "LinkedIn skill is already set up from a previous install — verifying it still works…"

Run: `python ../linkedin-research/linkedin_scraper.py verify`

The script returns JSON on stdout and an exit code:
- **Exit 0** → onboarded and logged in. Record `LinkedIn research skill > Onboarded: yes`, `Last verified: <today>`. Move to step 9.
- **Exit 20** → config exists but LinkedIn session expired. Tell the user: *"Your LinkedIn session expired — opening a Chrome window now to re-log in. Sign in, then tell me 'done'."* Run `linkedin_scraper.py setup --reauth-only`, then after user confirms, run `linkedin_scraper.py setup --stage verify-login`. Loop until exit 0.
- **Other exit codes** → fall through to fresh onboarding below.

#### 8.2. Fresh onboarding path (no config)

Tell the user:
> "Setting up the LinkedIn research piece. Two parts — first I need to find Chrome on your machine, then you'll log into LinkedIn one time in a Chrome window I'll open. Takes about 2 minutes. Ready?"

When user confirms, run the multi-stage flow:

**Stage 1 — Detect Chrome.** Run: `python ../linkedin-research/linkedin_scraper.py setup --stage detect`

- Exit 0 with JSON `{chrome_path: "..."}` → Chrome found at that path. Capture and proceed to Stage 2.
- Exit 11 with JSON `{chrome_path: null}` → Chrome not found in standard locations. Ask the user: *"I can't find Chrome on your machine in the usual spots. If you have Chrome installed somewhere custom, paste the full path to chrome.exe (or `Google Chrome` on Mac). Or, if you don't have Chrome, install from google.com/chrome and tell me when done; I'll retry."*

**Stage 2 — Save paths.** Run: `python ../linkedin-research/linkedin_scraper.py setup --stage save-paths --chrome-path "<path-from-stage-1>" --output-dir "<workspace-relative-output-dir>"`

The output-dir defaults to the value already detected from `get_default_output_dir()` (returned by Stage 1's JSON as `output_dir_default`); pass that unless user wants a custom location. Exit 0 → config saved.

**Stage 3 — Launch Chrome for login.** Run: `python ../linkedin-research/linkedin_scraper.py setup --stage launch-for-login`

This opens a visible Chrome window navigated to linkedin.com/login. Exit 0 once the window is up.

Tell the user:
> "Chrome should have just opened to LinkedIn's login page. Sign in there, then tell me when you're signed in and I'll verify."

Wait for user to confirm they've logged in. Don't proceed automatically.

**Stage 4 — Verify login.** When user confirms signed in, run: `python ../linkedin-research/linkedin_scraper.py setup --stage verify-login`

- Exit 0 → logged in. Record `LinkedIn research skill > Onboarded: yes`, `Last verified: <today>`. Move to step 9.
- Exit 20 → still signed out. Tell user: *"I still don't see you signed in — looks like the login didn't take. Try again in the same Chrome window, then tell me when done."* Re-run Stage 4. Loop with reasonable retry limit (3 attempts before falling back to error handling).

#### 8.3. Error handling

For any non-zero exit code that isn't covered above (e.g., 12 chrome_launch_failed, 13 cdp_attach_failed, network timeouts), use canonical-messages §10.4 from 2026-04-29 spec — read that section and deliver the message verbatim, substituting `[plain-language version of the actual error]` with a humanized rendering of the JSON's `reason` and `detail` fields (not the raw traceback).

Offer common fixes inline. Retry on user request. Never instruct the user to run diagnostic commands themselves. If the user explicitly says "skip LinkedIn", record `LinkedIn research skill > Onboarded: no` and proceed — `capture-contacts` will degrade gracefully (briefs use brain-dump notes only for that section).

### 9. Output folder

Use Question 8 from `references/onboarding-questions.md`. Default `~/Documents/conference-followup/`. Create the folder if it doesn't exist.

### 10. Display, confirm, save

Show the synthesized profile to the user:

> "Here's the profile. Read through it. Tell me anything to change. I'll only save once you say it's right."

Iterate on edits. On confirmation:
1. Write to `client-profile/exec-conference-profile.md` (using the structure in `../../client-profile/templates/exec-conference-profile.template.md`).
2. Delete `.conference-onboarding-in-progress.json`.
3. Show the final summary:

> "Saved to `<path>`. Connected: [email tool], [Tavily | skipped], [CRM | skipped]. LinkedIn skill: ready. Output folder: `<folder>`.
>
> Run `capture contacts from [event]` any time. Re-run setup if anything needs to change."

If any field is `partial` (e.g., voice extraction skipped), flag at top of profile as `Profile completeness: partial — [list of missing fields]`. Capture-contacts will still run with a partial profile.

### Refresh mode (alternative entry from step 0)

If a profile already exists at the workspace path AND capabilities are wired, skip the normal step-by-step flow and run refresh mode instead.

For each field in the existing profile, show the current value and ask: *"Keep this, or change?"* Accept the answer per-field. If the user says change, ask the corresponding question for that field and run the relevant logic (re-pull voice samples, re-verify a connection, re-pick CRM target, etc.).

Refresh does not re-walk the Composio install (already done) but DOES re-verify capabilities by re-detecting the host's loaded tools. Re-runs `linkedin_scraper.py setup` only if the user explicitly asks (e.g., to re-login or fix a broken setup); otherwise just runs `linkedin_scraper.py verify` to confirm.

After the walk-through, fall through to step 10 (display, confirm, save).

## Output

A confirmed `exec-conference-profile.md` plus optional `email-voice.md` and `exec-themes.md`, all in `client-profile/`. The profile is the source of truth for `capture-contacts`. If a CRM provider was picked, the target database and field mapping are filled here too (step 3.2) so `capture-contacts` can write records silently from its first run forward.

## Customization

To change what voice extraction captures: edit `../../client-profile/templates/email-voice.template.md` (the section headings drive the analysis structure).

To change what themes are asked about: edit `references/onboarding-questions.md` Question 5.

To change wizard wording: edit `references/canonical-messages.md` (per-section).
