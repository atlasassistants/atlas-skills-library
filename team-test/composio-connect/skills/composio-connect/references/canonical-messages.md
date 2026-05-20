# Canonical user-facing messages — composio-connect

These messages are the user-facing prose for the `composio-connect` skill.
The skill loads this reference and uses these messages verbatim at the
points specified in `SKILL.md`. They were sourced from
`plugins/energy-audit/skills/setup/references/canonical-messages.md`
(validated through real user testing) and generalized to remove
plugin-specific framing.

`[bracketed]` = substitute at runtime (tool names, errors, etc.).

**User-facing language rule.** Never use plugin/system terminology in
these messages — no "wizard," "skill," "MCP," "meta-tool," "schema,"
"wire," "toolkit slug." Composio is named by brand because the user
needs to know what they're installing. Everything else is plain
conversational language.

---

### Intro

Used at: `SKILL.md` Step 1, full-onboarding branch.

If `[CALLING-PLUGIN-PURPOSE]` is provided, lead with it as a standalone
line. Otherwise omit the entire first line and start at "To make this
work."

> "[CALLING-PLUGIN-PURPOSE]
>
>  To make this work, we need to connect a few of your tools. The
>  easiest way is **Composio** — a free service that connects your AI
>  to your apps in one place. Walk through the setup once and you're
>  done; takes about 5 minutes."

The optional first line is structurally separable — drop the line AND
the blank line after it if not provided. The remainder is grammatically
complete on its own.

### Composio install walkthrough

Used at: `SKILL.md` Step 1, full-install branch.

`[LIST-OF-REQUESTED-TOOLS]` is substituted with the user-facing tool
names from the recent conversation, joined naturally (e.g.,
`"Google Calendar, Slack, and Gmail"`). When invoked standalone
(no tools named yet), substitute with the literal string `"the apps
you want to use"`.

> "Here's the Composio setup, in order:
>
> 1. Sign up at composio.dev (free).
> 2. Click **Connect Apps** in the left sidebar.
> 3. Connect the apps you need: [LIST-OF-REQUESTED-TOOLS]
> 4. Click **Install** in the left sidebar.
> 5. Pick the install card for your AI (Claude Code, Claude Desktop,
>    Codex, ChatGPT, etc.) and follow the steps on that page —
>    they're tailored to your AI and OS. The install uses **OAuth
>    (one browser-based 'authorize' click)**; no API keys to copy
>    or paste.
>
> Where are you?
> - **(a) Done — installed and authenticated.** I'll re-check what's connected.
> - **(b) Got stuck on a specific step.** Tell me which one and what you saw.
> - **(c) Composio's dashboard looks different from what I described.** Send a screenshot."

### Composio re-auth (Stage 1.5)

Used at: `SKILL.md` Step 2, when Composio's MCP server is installed in
the AI but only the auth-bootstrap tools are loaded (no live meta-tools
yet). Lead with the status line so it's obvious nothing is being
skipped silently:

> "Composio is already installed in your AI from a prior session — I just
>  need to re-authorize it for this session, not walk through the full
>  install. Here's the auth link:
>
>  Composio's connected to your AI but needs re-authorizing for this
>  session. Open the URL I'll send next in your browser, sign in,
>  approve access, and tell me when you're done — your connected apps
>  will light up automatically. If the redirect page fails to load (it
>  usually does — that's just localhost), copy the full URL from your
>  address bar and paste it back to me."

### Stuck help

Used at: `SKILL.md` Step 1 (full install), when the user picks (c)
"Dashboard looks different" or otherwise needs visual help.

> "No worries. Send me a screenshot of what you see on your screen and
>  tell me which device you're on (Mac / Windows / Linux). I'll walk
>  you through it from there based on what you see."

### Tool not yet connected

Used at: `SKILL.md` Step 3, for each requested toolkit that isn't yet
connected after Composio is installed. `[TOOL-NAME]` is substituted
with the user's display name (from the conversation).

> "[TOOL-NAME] isn't connected yet. Open Composio's Connect Apps
>  page, find [TOOL-NAME], click Connect, and follow the prompts.
>  Tell me when you're done."

### Tool still not connected after retry

Used at: `SKILL.md` Step 3, when the user says "done" but Composio
still reports the toolkit as not connected, AFTER the Stuck help
section has already been shown once.

> "I still don't see [TOOL-NAME] as connected in Composio. Sometimes
>  this is a sync delay; sometimes the connection silently failed.
>  Want to try a different tool for this, or skip [TOOL-NAME] and
>  continue?"

### Tool not available in Composio

Used at: `SKILL.md` Step 3, when a requested tool can't be found
in Composio's Connect Apps catalog (either the `COMPOSIO_MANAGE_CONNECTIONS`
call returns an error indicating the slug is unknown, OR the response
contains no record of the toolkit existing).

> "I couldn't find [TOOL-NAME] in Composio's app list — it may not
>  be supported yet. Want to pick a different tool for this, or skip
>  it and continue?"

### Test call failed

Used at: `SKILL.md` Step 4, when a toolkit reports as connected
but the verification call returns an auth error.

> "[TOOL-NAME] says it's connected, but I couldn't read from it just
>  now. The most common cause is the authorization expired. Want me
>  to walk you through re-authorizing?"

### Standalone — ask what tools

Used at: `SKILL.md` Step 1.5, when the skill is invoked directly by the
user (no tools named by a calling plugin), AFTER Composio install
completes (or was already installed).

> "Composio's all set. What apps do you want to connect? You can name
>  any tools you use — calendar, email, project management, Slack,
>  whatever. I'll check Composio for each and walk you through
>  connecting the ones that aren't already wired.
>
>  Or, if you'd rather see what's already connected first, just ask
>  and I'll show you."

### Standalone — listing connected tools

Used at: `SKILL.md` Step 1.5 Path B, when the user asks what's already
connected instead of naming specific tools.

`[CONNECTED-TOOLS-LIST]` is substituted with connected toolkits' user-friendly
display names — never raw slugs. Map per the rule in `SKILL.md` Step 1.5
Path B Step 2 (e.g., `googlecalendar` → "Google Calendar", `slackbot` →
"Slack (notifications)").

> "Here's what's currently connected to Composio: [CONNECTED-TOOLS-LIST].
>
>  What would you like to do?
>  - Name another tool you want to connect (I'll add it)
>  - Verify the ones above are still working (I'll do a quick read on each)
>  - Done — these are enough"

### Standalone — disambiguation check

Used at: `SKILL.md` Step 0, before anything else, when invoked directly
by the user (not from a calling plugin).

> "Quick check — are you trying to set up a specific Atlas plugin
>  (like energy-audit, ideal-week-ops, daily-reporting, etc.), or
>  just setting up Composio for general use?
>
>  If you have a specific plugin in mind, tell me which and I'll
>  hand you to that plugin's setup. Otherwise I'll walk you through
>  Composio on its own."

### Handoff back to calling skill

Used at: `SKILL.md` Step 5, when all requested tools have reached a
final status.

> "All set — [SUMMARY-OF-WHAT-HAPPENED]. Continuing."

(`[SUMMARY-OF-WHAT-HAPPENED]` examples: "your tools are connected
and verified" / "Notion is connected, Slack was skipped" / etc.
Always plain language. Never reference per-tool status codes.)
