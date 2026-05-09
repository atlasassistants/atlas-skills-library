# Atlas Skills Library

Built and battle-tested by [Atlas Assistants](https://atlasassistants.com) — a collection of Claude plugins that give your AI assistant the skills to handle meetings, inbox, travel, reporting, and more. Install what you need and start saving your exec hours from day one.

---

## How to Install

There are four ways to get these plugins running. Choose the one that fits your setup.

---

### Option 1: Claude Code or Claude Co-work (Recommended for most users)

The setup is identical for both. The difference is what each platform can run — see the callout below.

**Steps:**
1. Open Claude Code or Claude.ai
2. Click the **+** button in the sidebar
3. Select **Plugins**
4. Click **Add Marketplace**
5. Paste this link: `colin-atlas/atlas-skills-library`
6. Browse the available plugins and click **Install** next to the one you want

**Pros:** Easiest setup, automatic updates, no command line needed
**Cons:** Co-work has capability limits — some skills require Claude Code (see below)
**Best for:** EAs and executives who already have Claude and want the fastest path to running a skill

> **Co-work vs. Claude Code — what's the difference?**
>
> The install steps are the same. The difference is capability:
>
> - **Co-work** works when a skill only needs connectors — Google Calendar, Gmail, Slack, and similar integrations. If the connectors are present and authorized, the skill runs.
> - **Claude Code** is required when a skill needs to read or write files, run scripts, or do anything beyond what connectors provide.
>
> Each plugin in the Skills Directory below lists which options it supports.

---

### Option 2: Clone the Repo

**Steps:**
1. Make sure you have [Git](https://git-scm.com/) installed
2. Clone the repository:
   ```
   git clone https://github.com/atlasassistants/atlas-skills-library
   ```
3. In Claude Code, install a plugin by its local path:
   ```
   /plugin install ./plugins/<plugin-name>
   ```

**Pros:** Full control — you can edit skills, customize methodology, and pin to a specific version
**Cons:** Requires Git familiarity; updates are manual; not available in Co-work
**Best for:** Teams who want to customize skills for a specific client or workflow

---

### Option 3: Custom Agent / API

**Steps:**
1. Clone or download the repository (see Option 2)
2. Open the `SKILL.md` file for the skill you want to use
3. Load its contents as system prompt instructions in your agent
4. Wire the required capabilities listed in that plugin's README to your agent's tools

**Pros:** Works in any agent runtime — not just Claude Code
**Cons:** Requires development work to wire capabilities; no marketplace browser
**Best for:** Developers building their own agent with the Claude API who want to embed Atlas skills

---

## Skills Directory

Organized by what you're trying to get done. Each plugin listing shows what it does, what problem it solves, which skills it includes, and which installation options it supports.

---

### Communications & Inbox

**[Inbox Zero](plugins/inbox-zero/)**
Runs end-to-end inbox management for your exec — triages every email through a decision tree, surfaces escalations first, tracks follow-ups with automatic cadences, and drafts replies in your exec's voice. Eliminates the daily inbox burden so urgent emails never get buried and routine ones are handled without your exec seeing them.

*Skills: `inbox-audit`, `inbox-onboarding`, `inbox-zero`, `inbox-triage`, `escalation-handler`, `follow-up-tracker`, `exec-voice-builder`, `inbox-reporter`, `health-check`*
*Works with: Claude Code, Co-work (with Gmail connector), Clone, Custom Agent*

---

**[Conference Contact Capture](plugins/conference-contact-capture/)**
Takes a free-form brain dump of people you met at a conference, researches each one on LinkedIn and their company website, and builds a structured brief per contact. Drafts personalized follow-up emails in your exec's voice and logs everything to your CRM — turning scattered notes into research-backed outreach within minutes of leaving the event. Note: LinkedIn research uses browser automation and requires Claude Code.

*Skills: `setup`, `linkedin-research`, `capture-contacts`*
*Works with: Claude Code, Clone*

---

### Meetings & Calendar

**[Meeting Ops](plugins/meeting-ops/)**
Handles the full meeting lifecycle — scans the calendar for unprepared meetings, drafts tailored prep briefs (internal and external), schedules prep blocks, and debriefs every meeting into structured logs with decisions, action items, and open threads captured. Ensures your exec walks into every meeting prepared and walks out with nothing falling through the cracks.

*Skills: `meeting-scan`, `internal-meeting-prep`, `external-meeting-prep`, `meeting-debrief`*
*Works with: Claude Code, Clone, Custom Agent*

---

**[Proactive Actions](plugins/proactive-actions/)**
Scans meeting debriefs for action items, classifies each as something the agent can execute, draft, chase, or hand back to a human, and immediately handles the routine parts without waiting. Closes the gap between identifying post-meeting actions and actually completing them.

*Skills: `run-proactive-actions`*
*Works with: Claude Code, Clone, Custom Agent*

---

**[Ideal Week Ops](plugins/ideal-week-ops/)**
Extracts your exec's ideal week into a documented ruleset — rhythms, deep-work blocks, protected time, and VIP overrides — then runs daily calendar scans that flag violations and suggest concrete fixes. Prevents the slow calendar creep that quietly eats the focused time your exec needs most.

*Skills: `setup`, `extract-ideal-week`, `scan-ideal-week`*
*Works with: Claude Code, Co-work (with Composio calendar + notification connectors), Clone, Custom Agent*

---

### Reporting & Visibility

**[Daily Reporting](plugins/daily-reporting/)**
Runs a structured daily reporting cycle at start-of-day and end-of-day — gathers context from calendar, email, tasks, and meeting notes, drafts a reviewable report, and writes continuity state for the next session. Ensures your exec always has a grounded view of what happened and what's next, with nothing lost between days.

*Skills: `daily-reporting`, `daily-reporting-setup`, `connect-sources`, `gmail`, `google-calendar`, `outlook-calendar`, `executive-workflow`, `meeting-notes`, `prior-state`, `manual`*
*Works with: Claude Code, Clone, Custom Agent*

---

### Travel & Logistics

**[Travel Prep](plugins/travel-prep/)**
Captures your exec's travel preferences once in a playbook, then proactively delivers comprehensive pre-trip briefings when flights appear on the calendar, and provides day-of support for flight status, gate changes, and ground transport. Eliminates the manual prep work so your exec is always ready before they think to ask.

*Skills: `travel-onboarding`, `pre-trip-briefing`, `day-of-support`*
*Works with: Claude Code, Clone, Custom Agent*

---

### Finance & Ops

**[Expense Management](plugins/expense-management/)**
Pulls monthly software and SaaS transactions from your bookkeeping system, reconciles them against a living subscriptions registry, flags new vendors and price changes above 10%, and on demand audits subscriptions interactively and drafts build-vs-buy specs for replacement candidates. Closes the loop on recurring software spend so nothing goes unreviewed month to month.

*Skills: `monthly-expense-report`, `subscription-audit`*
*Works with: Claude Code, Clone, Custom Agent*

---

### Learning & Knowledge

**[Compounding Learning](plugins/compounding-learning/)**
Captures reusable skills, insights, and patterns during work sessions, logs corrections and promotes rules into the agent's instruction file, and gates session closure on ensuring learnings are saved. Prevents repeated problem-solving by building a growing knowledge base — each session makes the next one faster.

*Skills: `session-capture`, `thread-close`, `correction-promote`*
*Works with: Claude Code, Clone*

---

**[Presentation Builder](plugins/presentation-builder/)**
Builds polished, self-contained HTML slide decks from scratch with arrow-key navigation and brand-consistent styling, then updates existing decks surgically based on feedback. Eliminates slide assembly work so the focus stays on content, not formatting.

*Skills: `build-deck`, `update-deck`*
*Works with: Claude Code, Clone*

---

## Contributing

Atlas teammates and friends can propose new plugins and skills. Read [`docs/contributing.md`](docs/contributing.md) before opening a PR. New plugins enter the repo in `team-test/` and are promoted to `plugins/` only after a teammate validates them on real work. See [`docs/skill-lifecycle.md`](docs/skill-lifecycle.md) for the full process.
