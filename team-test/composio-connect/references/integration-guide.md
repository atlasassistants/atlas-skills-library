# Integration guide — `composio-connect` for plugin authors

This document is for engineers building Atlas plugins that need to connect to external apps via Composio. Instead of writing your own Composio onboarding flow, invoke `composio-connect`.

## What `composio-connect` owns vs. what your plugin owns

**Your plugin owns:**
- The conversation with the user about which tools they want (your plugin knows the use case and can frame the question naturally)
- Capturing the user's specific tool picks (as plain words in the conversation — no slug knowledge required)
- Reading the handoff message from `composio-connect` and deciding what to do per-tool (proceed, push, alternative, skip)
- Multi-account selection when a toolkit returns multiple accounts in the handoff
- All plugin-specific capture (channels, recipients, output folders, ruleset extraction)
- Writing your plugin's `client-profile/<plugin>.local.md` config and any `.in-progress.json` marker
- All provider-specific introspection (Notion DB schema, Asana project picking, etc.)

**`composio-connect` owns:**
- Detecting Composio MCP state (not installed / auth-bootstrap only / fully wired)
- Walking the user through Composio install when missing
- Driving re-auth when the session lost auth
- Resolving each user-spoken tool name to a Composio slug via Composio's own search (no catalog anywhere)
- Walking the user through connecting each requested toolkit in Composio's dashboard
- Generic per-toolkit verification (calling any benign tool from the toolkit, checking it returns)
- Reporting per-toolkit account info in the handoff
- Telling the user when a requested tool isn't available in Composio's catalog

`composio-connect` writes no state files. It is stateless — every invocation re-detects Composio state live.

## How to invoke `composio-connect`

Since skills are markdown documents executed by an LLM orchestrator (not function calls), invocation is prose-shaped. In your plugin's SKILL.md, write something like:

> **Bridge message to the user (your plugin's voice):**
> *"For this to work, we need to connect a few of your tools. I'll walk you through it now."*
>
> **Then to the orchestrator (in your SKILL.md prose):**
> *Invoke `composio-connect`. It will pick up the tools the user just named from the conversation. Continue from Step N below when it hands back.*

That's it. The orchestrator goes to `composio-connect/skills/composio-connect/SKILL.md`, executes its flow, and returns to your plugin's Step N when done.

### How handoff actually works (no parameters, no APIs)

There's no parameter syntax. Skills are markdown — the orchestrator is an LLM that reads them in sequence and carries conversation state across.

When you write *"Invoke `composio-connect`"* in your SKILL.md, you're telling the LLM to read `composio-connect`'s SKILL.md next. The user's named tools are still in the chat history (they were just typed a few turns ago). `composio-connect`'s SKILL.md says *"read the tool names the user just gave the calling plugin"* — the LLM looks at the conversation and finds them.

So the "contract" between your plugin and `composio-connect` is conversational, not structural:
1. **Your plugin asks the user what tools they want, in plain conversation.** No slug knowledge required — your plugin lists example tools in plain prose ("Google Calendar or Outlook," "Notion / Asana / Linear / etc.").
2. **The user names tools in their own words.**
3. **Your plugin acknowledges and hands off to `composio-connect`.** The user's tool names are now in conversation history.
4. **`composio-connect` reads those names from conversation** and resolves each to a Composio toolkit via Composio's own search. Your plugin never needs to know any slug.

The names the user said are the names they see in every prompt and in the final handoff message. Their words stay their words end-to-end.

If Composio doesn't have a tool the user named, `composio-connect` reports back `not in composio` for that tool and the user is offered a way out (pick another / skip). Your plugin doesn't need to validate names against any catalog.

## The handoff message format

When `composio-connect` finishes, it prints:

```
composio-connect complete.

Per-tool status:
- <TOOL-NAME>: <status> [(N accounts: <identifiers>) if active]
  [<plain-language reason if not active>]
- ...

Returning control to calling skill.
```

Tools are listed by the name your plugin passed in — not by Composio slug. Each tool has one of four statuses:

| Status | Meaning | What your plugin should do |
|--------|---------|---------------------------|
| `active` | Connected in Composio AND test call passed | Proceed using this tool. If `N accounts > 1`, ask the user which account(s) to use. |
| `failed: <reason>` | Tried to connect but didn't work; reason is plain-language (e.g., "authorization expired," "OAuth flow didn't complete") | Decide based on the reason — sometimes worth pushing the user to retry (offer to invoke `composio-connect` again), sometimes worth proceeding without (if the tool was optional). |
| `skipped` | User explicitly chose to skip; reason gives context (e.g., "user switched to a different tool," "user couldn't get it connected") | Same as `failed` — decide based on whether the tool was required. |
| `not in composio` | Composio's search couldn't find a match for the name | Tell the user the tool isn't available through Composio. Offer them to try a different tool or proceed without. |

For every non-active status, the wizard includes a plain-language REASON that explains what happened. Your plugin reads the reason and decides what to do (push, retry, alternative, proceed).

## Example A — Simple setup, one tool

Hypothetical `meeting-followups` plugin needing only Google Calendar.

### `meeting-followups/skills/setup/SKILL.md` (excerpt)

```
### Step 2: Connect your calendar

Ask the user (in this plugin's voice):
> "What calendar do you use? Most users have Google Calendar or Outlook."

The user's answer (e.g., "Google Calendar") is now in conversation
history. No mapping or transformation needed — just keep going.

### Step 3: Hand off to composio-connect

Bridge message to user (your plugin's voice):
> "For this to work, we need to connect your calendar. I'll walk you
>  through it now."

Then invoke composio-connect — it picks up the calendar tool the user
just named from the conversation. Continue from Step 4 when it hands
back.

### Step 4: Read the handoff

The handoff message lists one tool. Four possible statuses:
- active → continue to Step 5 (plugin-specific capture)
- failed: <reason> → tell the user the reason, offer to invoke composio-connect again to retry:
  "Looks like [name] didn't connect — [reason]. Want me to walk through
   connecting it again?"
- skipped or not in composio → ask the user: "I can't run this without
  a calendar. Want to try a different calendar tool, or come back later?"
```

This is the smallest possible integration. The baseline template every plugin author copies.

## Example B — Multi-tool with multi-account

Hypothetical `inbox-triage` plugin needing Gmail + Calendar where the user has 3 Gmail accounts.

### `inbox-triage/skills/setup/SKILL.md` (excerpt)

```
### Step 2: Ask which tools

Ask the user:
> "What email and calendar do you use? Common picks: Gmail + Google
>  Calendar, or Outlook for both."

The user's answers ("Gmail" and "Google Calendar") are now in
conversation history.

### Step 3: Hand off to composio-connect

Bridge message to user, then invoke composio-connect. It picks up the
named tools from the conversation.

### Step 4: Read the handoff, ask about multi-account

The handoff message might look like:

  composio-connect complete.

  Per-tool status:
  - Gmail: active (3 accounts: sam@atlas.co, sam@personal.com, sam@old.com)
  - Google Calendar: active (1 account: sam@atlas.co)

  Returning control to calling skill.

Notice Gmail has 3 accounts. Ask the user (this plugin's voice):
> "I see 3 Gmail accounts connected: sam@atlas.co, sam@personal.com,
>  sam@old.com. Which should I use for the inbox triage? You can pick
>  one or merge several."

Capture the choice. Continue to Step 5.
```

**Inline note on non-active statuses:** If a tool comes back as `failed: <reason>`, `skipped`, or `not in composio`, your plugin reads the reason and decides what to do — push the user on needing it (show them the reason and offer to invoke composio-connect again), offer to pick an alternative tool, or proceed with what they have. Pick whichever fits your plugin's behavior. The wizard always includes a plain-language reason; surface it to the user rather than dropping the context.

## Example C — Work-skill pre-flight pattern

Hypothetical `inbox-triage` plugin's main work skill, invoked any time the user wants to triage their inbox.

### `inbox-triage/skills/triage/SKILL.md` (excerpt)

```
### Step 1: Check setup completed

Read client-profile/inbox-triage.local.md.
- If missing → tell the user (plain language):
  "Looks like we haven't set this up yet — let me walk you through
   it." Then invoke inbox-triage/skills/setup/SKILL.md directly.
- If exists → read the saved tool names (e.g., "Gmail", "Google Calendar")
  and the saved Gmail account choice.

### Step 2: Pre-flight via composio-connect

Mention the saved tool names in conversation (e.g., "Quick check — making
sure Gmail and Google Calendar are still connected..."), then invoke
composio-connect. It picks up the named tools from your acknowledgement
sentence. Continue from Step 3 when it hands back.

### Step 3: Read the handoff

- If every required tool is active → proceed to Step 4 (the actual
  triage work).
- If any required tool came back as failed/skipped/not in composio →
  tell the user (plain language) using the reason from the handoff:
  "I can't run the triage without [tool]. [Reason from handoff.]
   Want me to walk through connecting it now or come back later?"

### Step 4: Do the triage work

[plugin-specific logic — fetch emails, classify, etc.]
```

**Inline note on mid-flow recovery:** If your work skill catches a Composio error mid-task (e.g., a Gmail API call returns "unauthorized"), re-invoke `composio-connect` mentioning the failing toolkit in conversation, then retry the failed call once. This pattern catches mid-flow session drops.

## Example D — Refresh-mode setup that does NOT invoke composio-connect

A common pitfall: invoking `composio-connect` for refresh flows that don't actually touch tool selection. Example: the user just wants to change their notification recipient.

### `inbox-triage/skills/setup/SKILL.md` (refresh-mode excerpt)

```
### Step 0: Detect refresh mode

If client-profile/inbox-triage.local.md exists, enter refresh mode.

### Step 1 (refresh): Ask what to change

> "What do you want to change? Options:
>  - The Gmail account you're using
>  - Which calendar accounts to scan
>  - The notification recipient (email address)
>  - The tools themselves (which Gmail / Calendar provider)"

### Step 2 (refresh): Branch on the change

- If "tools themselves" → ask which tool (user's name), capture the
  name, invoke composio-connect with the new name, continue to Step 3.
- If anything else (account choice, calendar choice, recipient) →
  update the local config in place, write, done. DO NOT invoke
  composio-connect.
```

The rule: only invoke `composio-connect` when the user's tool SELECTION changes. Plugin-specific config (recipients, output folders, scheduling anchors, etc.) is your plugin's responsibility to update without involving Composio.

## Template — README §Prerequisites for your plugin

Add a section to your plugin's `README.md` (around §First-run setup):

> ## Prerequisites
>
> This plugin connects to external apps (Google Calendar, Slack, etc.)
> through Composio. Install `composio-connect` first — it handles all
> the Composio onboarding so you only have to do it once across every
> Atlas plugin.
>
> ```
> /plugin install composio-connect@atlas
> ```
>
> When you run this plugin's setup, it'll automatically hand off to
> `composio-connect` for the Composio steps.

## What NOT to put in your plugin's setup skill

These belong in `composio-connect`, not in your plugin. If you find yourself writing any of these, you're duplicating the shared skill:

- Composio install walkthrough prose ("Sign up at composio.dev, click Connect Apps, ...")
- Re-auth flow prose ("Open this OAuth link, click Authorize, ...")
- Auth-bootstrap detection logic (the `mcp__composio__authenticate`-only state)
- Common gotcha branches for the Composio install steps
- Per-toolkit verification test calls
- A catalog of "which toolkits Composio supports for X"
- Any slug-to-display-name mapping (Composio's search resolves names; you never need slugs in your plugin)

If you think `composio-connect` is missing a step or branch you need, raise it with the Atlas team rather than re-inventing in your plugin. Drift across plugins is exactly what this shared skill exists to prevent.
