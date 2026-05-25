---
name: composio-connect
description: Walks the user through getting Composio installed in their AI, connecting specific Composio toolkits the calling plugin asked for, and verifying each one returns successfully on a test call. Other Atlas plugins invoke this skill instead of writing their own Composio setup flow. Use when an Atlas plugin's setup or work skill needs to ensure specific Composio toolkits are ready before proceeding.
when_to_use: Invoked BY other Atlas plugins (not directly by the user). Trigger phrases when called from another skill — "invoke composio-connect", "now hand off to composio-connect", "ensure the tools the user just named are connected via Composio", or any inline reference inside a calling plugin's SKILL.md that names this skill. Also fires if the user explicitly says "set up Composio" or "connect my tools" without being inside a calling plugin's flow — in that case the skill drives a full install in standalone mode.
atlas_methodology: neutral
---

# composio-connect

Shared Composio onboarding for Atlas plugins. Called by other plugins to ensure a list of tools is installed, connected, and verified. Single contract — the calling plugin has already asked the user what tools they want; this skill reads those names from the conversation, resolves them to Composio toolkits, ensures each reaches a final status (`active`, `failed: <reason>`, `skipped`, or `not in composio`), and hands back.

## Purpose

When an Atlas plugin needs the user's external apps connected (calendar, email, project management, etc.), it invokes this skill instead of writing its own Composio onboarding flow. The skill detects what's already wired, walks the user through any gaps, verifies each tool with a real test call, and hands back a per-tool status report. The calling plugin reads the report and decides what to do (continue, ask the user about skipped tools, etc.).

## Inputs (from conversation context, not formal parameters)

Skills are markdown documents executed by an LLM. There is no parameter syntax between skills; "input" is whatever the LLM has in its working context when it starts following this SKILL.md.

- **Tools to connect** — the calling plugin already asked the user something like *"which tools do you want to use for [purpose]?"* and the user answered (e.g., *"Google Calendar, Gmail, Notion"*). Those names are in the recent conversation. Read them from there.
- **Calling-plugin context (optional)** — the calling plugin's bridge message often includes a one-line description of what it does (e.g., *"For this plugin to scan your calendar for conflicts, we need to connect a few of your tools."*). Read that line, if present, and use it as an optional lead-in to the Intro message.
- **Standalone mode** — if no calling plugin context is present and no tools were named (the user invoked this skill directly), proceed in standalone mode: install Composio if needed, then ask the user what apps they want to connect.
- **Host's loaded tool list** — required, used to detect Composio MCP state and pick a verification tool per resolved toolkit.

## Required capabilities

(Abstract — no specific tool names. Validated default wiring is Composio MCP itself; see plugin README §4.)

- Detection of Composio meta-tools in the host's loaded tool list
- Composio MCP authentication tool (the auth-bootstrap call)
- Composio MCP connection-listing tool (live connected-toolkit query)
- Composio MCP toolkit-search tool (resolve user names to Composio slugs)
- The ability to call arbitrary loaded tools (used for generic verification)
- Conversational interview (one prompt at a time)
- Ability to receive image input from the user (for stuck-help screenshots)

## Steps

> **User-facing language rule.** Run detection silently. Do NOT narrate the model's internal reasoning or specific tool names to the user. Brand names users recognize (Composio, Google Calendar, Slack, Gmail, Outlook) are fine. Internal mechanism words ("MCP," "wire," "schema," "meta-tool," "toolkit slug," "Stage 1.5") are not. Load every user-facing message from `references/canonical-messages.md` rather than writing prose inline. When in doubt, write the message the way you'd write it to a non-technical executive assistant.

> **What "the tools" means in this skill.** This SKILL.md refers throughout to "the tools the user named," "the tool list," and similar phrases. There is no formal parameter — the user (or a calling plugin establishing the list on the user's behalf) named some tool names in the recent conversation. The orchestrator (the LLM) has those names in its working context. When this skill says "for each tool the user named," that means: look at the recent conversation, find the tool names, and proceed. The list lives in conversation, not in a data structure.

### 0. Detect Composio state (and disambiguate standalone invocations)

**Invocation mode check (first action):**

- If invoked from another plugin (the orchestrator was inside a calling plugin's SKILL.md when it routed here, AND tool names are present in conversation) → proceed directly to the Composio state check below.
- If invoked directly by the user (no calling plugin context, OR no tools named yet) → show the **Standalone — disambiguation check** section from `references/canonical-messages.md` first. If the user names a specific Atlas plugin, tell them: *"Let me hand you to [plugin]'s setup instead."* and exit. If they confirm they just want Composio setup → proceed in standalone mode (no tool list captured yet; this happens in Step 1.5).

**Composio state check:**

Three states, checked in order:

1. **Composio meta-tools absent.** The host's loaded tool list has no `mcp__composio__*` entries at all. The user does not have Composio installed in their AI.
2. **Auth-bootstrap only.** The host has `mcp__composio__authenticate` and `mcp__composio__complete_authentication` loaded BUT the real meta-tools (e.g., `COMPOSIO_SEARCH_TOOLS`, `COMPOSIO_MANAGE_CONNECTIONS`) are NOT loaded. The MCP server is installed but the session has no active auth.
3. **Fully wired.** The real meta-tools are loaded. Composio is ready to query.

Branch:

- State 1 → Step 1 (full install).
- State 2 → Step 2 (re-auth flow).
- State 3 → if standalone mode and no tools named yet → Step 1.5; otherwise → Step 3 (per-tool resolution + check).

### 1. Full install (when Composio meta-tools are absent)

Load and show the **Intro** section from `references/canonical-messages.md`. Substitute `[CALLING-PLUGIN-PURPOSE]` with the calling plugin's one-line context if provided. If not provided, drop both the placeholder line AND the blank line after it (the remaining prose is grammatically complete on its own).

Then load and show the **Composio install walkthrough** section. Substitute `[LIST-OF-REQUESTED-TOOLS]` with the user-facing tool names from the recent conversation, joined naturally (e.g., `"Google Calendar, Slack, and Gmail"`). If no tools have been named (standalone invocation), substitute with the literal string `"the apps you want to use"`.

**Three-way gate (verbatim from the walkthrough section's prompt):**

- **(a) Done — installed and authenticated.** Wait for confirmation. Then re-run detection (Step 0). If the host now has the real meta-tools, proceed to Step 3 (or Step 1.5 if standalone). If detection still doesn't see Composio, ask: *"Which AI client did you install for? Did you reload/restart the client after authorizing?"* (most clients need a session restart to pick up newly-added MCP servers).
- **(b) Got stuck on a specific step.** Ask which step. Common gotchas:
  - **Step 1 (signup)** — blocked by SSO/corporate firewall → suggest personal Google login or different network
  - **Step 3 (connecting an app)** — OAuth window doesn't open or closes immediately → check popup blocker; suggest incognito window
  - **Step 5 (AI install)** — terminal command errors out → check the AI client version is recent; suggest reinstalling
- **(c) Composio's dashboard looks different from what I described.** Load and show the **Stuck help** section. Accept screenshot input from the user, walk them through based on what you see in the image.

Iterate until detection re-runs and lands on State 3.

### 1.5. Standalone tool capture (only when invoked directly with no tools named)

Reached when standalone mode AND Composio is now wired (post-install OR was already wired).

Load and show the **Standalone — ask what tools** section from `references/canonical-messages.md`.

The user replies. Two paths:

**Path A — User names specific tools** (e.g., "Google Calendar, Slack, Notion"). Capture each as a plain string in the conversation — these names become the working "tools the user named" list for the remaining steps. **Do NOT try to derive slugs here** — that happens in Step 3a via Composio's search. Just collect the names. Proceed to Step 3.

**Path B — User asks what's already connected** (e.g., "what do I have wired?", "what's connected?", "show me what's set up"). Don't push them to name tools — answer the question first.

1. Read the connected-toolkit list from Composio. Two sources work:
   - The `COMPOSIO_SEARCH_TOOLS` tool description often includes an annotation like *"User has manually connected the apps: <comma-separated slug list>"* — read that directly if present.
   - Otherwise call `COMPOSIO_MANAGE_CONNECTIONS` with `action: "list"` across the toolkit slugs Composio's catalog covers, and collect the ones returning at least one active account.
2. **Map each slug to a user-friendly display name.** Use general knowledge — `googlecalendar` → "Google Calendar", `slack` → "Slack", `slackbot` → "Slack (for notifications)", `gmail` → "Gmail", `googledrive` → "Google Drive", `notion` → "Notion", `fathom` → "Fathom", `github` → "GitHub", etc. If a slug isn't obvious, capitalize it but keep it as-is. **Never show raw lowercase slugs to the user.** When `slack` and `slackbot` both appear, list them once as "Slack" plus a parenthetical note that `slackbot` is the notification-sender variant.
3. Load and show the **Standalone — listing connected tools** section from `references/canonical-messages.md`, substituting `[CONNECTED-TOOLS-LIST]` with the mapped display names.
4. The user's response routes the next step:
   - Names a new tool to connect → treat as Path A above, add the new name to the tools list, proceed to Step 3 for that tool.
   - Says they're done / the listed tools are enough → no work to do; go straight to Step 5 (handoff) with `active` statuses for the already-connected tools (verification optional in standalone mode since the user didn't request a specific check).
   - Asks to verify the listed tools work → proceed to Step 4 for each connected toolkit, then Step 5.

### 2. Re-auth (when only auth-bootstrap tools are loaded)

Load and show the **Composio re-auth (Stage 1.5)** section from `references/canonical-messages.md`.

Call `mcp__composio__authenticate` to get the OAuth URL. Deliver the URL to the user verbatim. Wait for them to either confirm "done" or paste the redirected URL.

If they paste a redirected URL, call `mcp__composio__complete_authentication` with that URL.

Re-run detection (Step 0). If now in State 3, proceed to Step 3 (or Step 1.5 if standalone). If still in State 2, surface the error and ask the user to try again or check whether the OAuth window completed successfully.

### 3. Per-tool resolution + connection check (when Composio meta-tools are loaded)

For each tool name the user named (read from conversation), the wizard does TWO things: resolve the user's name to a Composio slug, then check connection state.

**Step 3a — Resolve name to slug.**

For each name:

1. **Check the `COMPOSIO_SEARCH_TOOLS` description annotation first.** Composio annotates the tool description with a line like *"User has manually connected the apps: gmail, googlecalendar, notion, slack, ..."* — the connected slugs are listed there explicitly. If the user's name maps obviously to one of those slugs ("Gmail" → `gmail`, "Google Calendar" → `googlecalendar`, "Notion" → `notion`, "Slack" → `slack`), use it directly. **No search call needed for the obvious cases.** This saves a round-trip per tool.
2. **Only when the annotation doesn't have an obvious match** (less common tools, ambiguous spellings, the user named a tool that isn't already connected), call `COMPOSIO_SEARCH_TOOLS` with the user's name as the query.
3. Read the response (whether from annotation or search call):
   - If a matching toolkit was found → remember the `slug` for API calls; keep the user's original `name` for all prose. Proceed to Step 3b for this tool.
   - If no match anywhere (annotation didn't have it AND search returned no result OR an error indicating the toolkit is unknown) → mark this tool as `not in composio`. Include in the handoff reason: *"Composio's app search couldn't find a match for '[NAME].'"* Move on; do not run Step 3b for this tool.

**Step 3b — Check connection state.**

For tools that resolved to a slug, call `COMPOSIO_MANAGE_CONNECTIONS` with `toolkits: [{name: <slug>, action: "list"}]` for each (batch in one call when possible). Read each response:

- **Already active** → `accounts.length >= 1` AND at least one account has an Active status. **Capture the most useful identifier per account** using this priority (use the FIRST one that exists in Composio's response):
  1. Email address — `user_info.emailAddress` (Gmail), `user_info.email`, `user_info.person.email`, or any other email-shaped value nested in the account data
  2. Workspace / account name — for toolkits that don't expose an email directly (Notion, GitHub, etc.), use `user_info.bot.workspace_name`, `user_info.workspace_name`, `user_info.name`, or equivalent
  3. Account alias — if Composio set one (`accounts[].alias`)
  4. Account ID — last resort (e.g., `notion_doater-amok`); ugly but better than nothing
  
  Remember only ONE identifier per account for the Step 5 handoff — don't list multiple. Pick the most recognizable. If a response surfaces both an email and a workspace (e.g., Notion via OAuth with the connecting user's email nested deep), prefer the email if it's clearly the connecting user, OR include the workspace name with the email in parentheses if both add useful context (e.g., *"lamya@atlasassistants.com (Atlas Assistants workspace)"*).
  
  Then proceed to Step 4 verification for this tool.
- **Not yet connected** → `accounts.length == 0` or no Active account. The toolkit IS recognized but has no live connection. → Walk the user through connecting it (below).
- **Connection-list call errors** → if the call itself errors (rather than just returning no accounts), treat as a transient Composio issue. Show the user a plain-language version of the error, offer to retry once. If the retry also errors, mark as `failed` with the translated reason (*"Composio returned an error when checking the connection status"*).

**Walking the user through connecting a not-yet-connected toolkit (max 2 attempts, with reasoning):**

1. **Attempt 1.** Load and show the **Tool not yet connected** section from `references/canonical-messages.md`, substituting `[TOOL-NAME]` with the user's name.
2. Wait for the user to say "done." Re-call `COMPOSIO_MANAGE_CONNECTIONS` for this slug.
   - If now active → capture account identifiers, proceed to Step 4.
   - If still not active → present a **soft retry prompt** (NOT a screenshot demand). Use Composio's actual response to compose a short, specific reason, and ask if they want to try once more. Examples:
     - *"Composio's still showing Slack as not connected — sometimes there's a sync delay after you click Connect. Want to try once more?"*
     - *"Composio says the OAuth flow was started but didn't complete. That usually means the popup was closed early. Want to try again?"*

   Do NOT show the **Stuck help** section at this point. The user's first "done" may have been premature; a soft retry is the right next move. Screenshots are opt-in only — load and show **Stuck help** ONLY if the user explicitly says they're stuck, asks for help, or shares a screenshot of their own accord.

3. **Attempt 2.** Wait for the user to either say "done" again (they re-tried the connection) or to spontaneously share a screenshot / say they're stuck.
   - If they re-tried and say "done" → re-call `COMPOSIO_MANAGE_CONNECTIONS`. If now active → capture identifiers, proceed to Step 4. If still not active → proceed to the give-up prompt below.
   - If they share a screenshot or say they're stuck at any point → load and show the **Stuck help** section, use what they shared to give specific guidance, then go back to waiting for "done." This still counts as the same Attempt 2 (don't restart the attempt counter).

4. If Attempt 2 also fails (second "done" with still-not-active result), load and show the **Tool still not connected after retry** section. Three paths:
   - User picks "try a different tool" → ask which one. Accept their name, restart Step 3 for that new name. Mark the original tool as `skipped` with reason: *"User switched to a different tool."*
   - User picks "skip" → mark as `skipped` with reason: *"User couldn't get [TOOL-NAME] connected after 2 attempts and chose to skip."*
   - The wizard escalates: mark as `failed` with the reason whatever the last connection-state response indicated (e.g., *"Composio reports the toolkit is not connected and the user couldn't complete the OAuth flow"*).

The user may also explicitly say they want to skip at any point → mark as `skipped` immediately with reason *"User chose to skip."*

If at any point the user says they can't find the tool in Composio's app list → the slug resolved in 3a but the toolkit isn't surfaceable in their dashboard. Load and show the **Tool not available in Composio** section. Same two paths (try another / skip with reason *"User couldn't find this tool in Composio's dashboard."*).

**Important: every status that isn't `active` carries a reason string.** The reason is plain language, translated from whatever Composio returned. No raw error codes in the handoff. The calling plugin reads the reason and decides what to do.

### 4. Verification (generic test call per active toolkit)

For each toolkit marked active in Step 3:

1. **Find a benign tool from this toolkit to test with.** Two paths depending on what's loaded:

   **Path A — per-toolkit tools are pre-loaded in the host.** Some clients (e.g., older Composio MCP setups, or hosts with eager loading) pre-load all toolkit tools. If the host's loaded tool list contains tool names matching the toolkit's slug (e.g., for `slack`, any tool whose name contains `slack` or `SLACK_`), pick the first one and call it directly with minimal or default arguments.

   **Path B — only Composio meta-tools are loaded.** This is the common case with Claude Code's lazy-loading Composio MCP setup. Per-toolkit tools like `GMAIL_GET_PROFILE` or `GOOGLECALENDAR_LIST_CALENDARS` are NOT pre-loaded — they have to be discovered. Do this:
   
   - Call `COMPOSIO_SEARCH_TOOLS` with a query like *"verify [toolkit] connection"* or *"read from [toolkit]"*. Composio returns one or more benign read tools and their slugs.
   - Take the first returned read tool slug (e.g., `GMAIL_GET_PROFILE`, `GOOGLECALENDAR_LIST_CALENDARS`, `NOTION_LIST_USERS`).
   - Invoke it via `COMPOSIO_MULTI_EXECUTE_TOOL` with that slug and minimal/default arguments.
   - When verifying multiple toolkits in a single Step 4 run, batch all the invocations into ONE `COMPOSIO_MULTI_EXECUTE_TOOL` call.

2. Interpret the result:
   - **Returns data, or returns an error other than an auth error** → mark this toolkit as `active` (verified). A "wrong arguments" or "validation" error still means the connection works — auth got through.
   - **Returns an auth error** (401, 403, "unauthorized," "token expired," "not authenticated," etc.) → **reason about the error first**, then offer recovery. Translate the technical error into plain language:
     - `401 / unauthorized` → *"[TOOL-NAME]'s authorization seems to have expired."*
     - `403 / forbidden` → *"[TOOL-NAME] is rejecting reads — usually means the connection needs new permissions."*
     - Generic auth failure → *"[TOOL-NAME] says it's connected but isn't responding to a read."*

     Load and show the **Test call failed** section from `references/canonical-messages.md`, leading with the translated reason. Offer the user a choice:
     - Re-authorize → invoke the Composio re-auth flow (Step 2 logic) targeted at this toolkit. After re-auth, retry the test call once.
       - If now succeeds → mark `active`.
       - If still auth error → mark `failed` with reason *"Re-authorization didn't repair the [TOOL-NAME] connection; the auth error persists."*
     - Skip → mark `skipped` with reason *"User chose to skip [TOOL-NAME] after the test call failed."*

### 5. Hand back to calling skill

Once every requested tool has reached a final status (`active`, `failed`, `skipped`, or `not in composio`), assemble the handoff message. **Each tool is listed by the user's name** — not by Composio slug. Every non-active status includes a plain-language reason.

```
composio-connect complete.

Per-tool status:
- <TOOL-NAME>: <status> [(<N> accounts: <comma-separated identifiers>) if active and accounts.length >= 1]
  [<plain-language reason if not active>]
- ...

Returning control to calling skill.
```

Example output:

```
composio-connect complete.

Per-tool status:
- Google Calendar: active (1 account: sam@atlas.co)
- Gmail: active (3 accounts: sam@atlas.co, sam@personal.com, sam@old.com)
- Slack: failed
  (Composio shows Slack as connected, but the test call returned an
   auth error — the user declined to re-authorize during setup.)
- Notion: skipped
  (User chose to skip; not connected.)
- LinearX: not in composio
  (Composio's app search couldn't find a match for "LinearX." The
   user picked a different tool.)

Returning control to calling skill.
```

Status types and what they mean:
- `active` — connected AND test call passed
- `failed` — tried but didn't work; reason includes the plain-language translation of whatever Composio returned
- `skipped` — user chose to skip; reason includes the user's stated reason or context
- `not in composio` — Composio's search couldn't find a match for the user's tool name

Then load and show the **Handoff back to calling skill** section from `references/canonical-messages.md` as the user-facing line — substitute `[SUMMARY-OF-WHAT-HAPPENED]` with a plain-language summary appropriate to the outcome.

The calling skill reads the per-tool status block (and reasons) to decide its next move (proceed, ask the user about skipped/failed tools, retry, fail with a clear message, etc.).

## Handoff Contract

| Output | Target | When |
|--------|--------|------|
| Per-tool status message (every requested tool → `active` / `failed: <reason>` / `skipped` / `not in composio`) | The calling skill | After Step 5 |
| Composio MCP fully installed and authenticated in the user's AI | The user's environment | After Step 1 or Step 2 completes |

**Done when:** every tool the user named has reached one of the four final statuses AND the handoff message has been printed.

This skill writes NO state files. Composio's own state is the source of truth and is queried live every invocation.
