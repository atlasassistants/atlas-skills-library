---
name: subscription-audit
description: Interactively walk through every active subscription in the configured subscriptions registry, classify each as keep / cancel-candidate / replace-candidate using a structured 3-question interview, and draft a one-page AI-replacement mini-spec for every replace-candidate. Writes a dated audit summary plus per-tool replacement-idea pages into the finance docs root.
when_to_use: |
  User asks to "audit our subscriptions", "which tools can we cancel", "find tools we could replace with AI", "review our SaaS spend", or "do a tool cleanup". Run after monthly-expense-report has been run at least once so the registry is populated. Do NOT use this skill before subscriptions.md exists — instruct the user to run monthly-expense-report first.
atlas_methodology: opinionated
---

# subscription-audit

Interactively review every active subscription in the configured `subscriptions.md`, classify each as keep, cancel-candidate, or replace-candidate, and produce mini-spec replacement ideas for tools where a custom AI build could replace a paid vendor.

The audit method is opinionated — the 3-question interview, the first-match-wins classification rules, and the one-page mini-spec format are documented in `../../references/atlas-expense-methodology.md` (plugin root). Read it before customizing.

## Path conventions in this file

Paths in this SKILL.md are **relative to this file's location** (`<plugin>/skills/subscription-audit/SKILL.md`). `references/...` resolves to this skill's siblings; `../monthly-expense-report/references/...` reaches the sibling skill's references; `../../references/...` resolves to plugin-root locations.

## Prerequisites

Before running:

1. **Locate the client config (`expense-config.md`).** Try these in order (same procedure as `monthly-expense-report` so both skills find the same file):
   1. If a previous session recorded the config path in session memory or knowledge base, use it.
   2. Otherwise, ask the user: "Where is your `expense-config.md`? (Default convention is `<finance_docs_root>/expense-config.md`.)"
   3. If the user can't tell you, check common locations: `<cwd>/expense-config.md`, `<cwd>/areas/finances/expense-config.md`, `<cwd>/finances/expense-config.md`. If none exist, stop and instruct the user to copy the template from `../../client-profile/templates/expense-config.template.md` to a known location, then retry.
   
   Once located, persist the path so future runs don't have to ask. Then read it and extract `finance_docs_root`. If missing or empty, stop and ask the user to fill it in.
2. **`subscriptions.md` is populated.** Read `<finance_docs_root>/subscriptions.md`. If empty (no entries under `## Active`) or missing, instruct the user to run the `monthly-expense-report` skill first to seed it, then stop.
3. **Audits folder exists.** Ensure `<finance_docs_root>/audits/` and `<finance_docs_root>/audits/replacement-ideas/` exist. Create if missing.
4. **Schema is shared with `monthly-expense-report`.** The canonical schema and parse recipe live in `../monthly-expense-report/references/schemas.md`. Read it before parsing.

## Inputs

No required arguments. The user may optionally specify in natural language:

- **a category filter** — e.g. "just audit the AI tools" → filter by `category: ai-tools`
- **a minimum monthly cost** — e.g. "only the ones over $20/mo" → filter by `effective_cost >= N` (see "Cost ranking" below)

If no filter is specified, audit every subscription in `## Active` and `## Under review`, sorted by `effective_cost` descending.

### Cost ranking

For ranking and filtering, use `effective_cost = max(cost_monthly, last_amount)` rather than `cost_monthly` alone.

- For steady-state subs (Notion, Slack, Active Campaign), `cost_monthly` and `last_amount` agree — `effective_cost` is the same number either way.
- For usage-based or multi-charge subs (AWS, OpenAI API, Claude AI Team), `cost_monthly` is the user-set canonical, but `last_amount` reflects the most recent month's actual total — which may be substantially higher in growth months. Using `max()` ensures a vendor whose actual spend just doubled doesn't get deprioritized in the audit because the canonical hasn't been bumped yet.
- If a sub has no `last_amount` (genuinely never charged), fall back to `cost_monthly`.

## Procedure

### 1. Load and parse

Read `subscriptions.md`. Use the parse recipe in `../monthly-expense-report/references/schemas.md` — each subscription is a `### <Tool Name>` heading followed by bulleted `- field: value` lines.

Parse the `## Active` and `## Under review` sections into a structured list. Apply any filters from the user's request. Compute `effective_cost` for each (see above). Sort by `effective_cost` descending so the highest-cost items get attention first.

Announce the plan to the user before starting:

> "About to walk through N subscriptions totaling $X/mo. Highest first. For each I'll ask three questions and then classify it. Ready?"

Wait for confirmation.

### 2. Walk each subscription

For each subscription, open with the cost context so the user has the relevant numbers in mind, then ask the three usage questions in a single concise prompt:

> "**<Tool Name>** — $<effective_cost>/mo (cost_monthly $<X>, last month $<last_amount>{ across N charges if multi-charge}). Three questions:
> 1. When did you last use this?
> 2. Is it still needed — would workflow break if we cancelled it?
> 3. On a scale of 1-5, how core is it (1 = could drop today, 5 = critical)?"

Surface `last_charge_count` only if it's set (>1) — useful context for usage-based vendors (e.g. "AWS — $247/mo across 4 charges").

Keep the message tight — one message per tool, not a form. If the host runtime offers a structured-question capability (a UI tool that returns one of N options), use it for the rating. Otherwise accept free-text and parse the number out.

**Special case — `needs-review` entries.** These were auto-detected by `monthly-expense-report` but not yet confirmed. Before classifying, first ask the user to identify what the tool actually is — for example: "I see a $49 charge from SomeNewTool — what is this?" — and assign a category. Then run the three usage questions.

Based on the response, classify. **Evaluate rules in order; first match wins:**

1. **cancel-candidate** — user explicitly says "drop it" / "cancel", OR last-used was 30+ days ago, OR rated 1.
2. **keep** — rated 4-5, OR used within last 14 days AND user says workflow breaks without it.
3. **replace-candidate** — everything else: used but rated 2-3, or user hints the functionality is "something we could build".

Update the classification in `subscriptions.md` by changing the `status:` field for each reviewed sub.

**Refresh stale auto-detection notes.** If the entry has the auto-detection placeholder note (`Auto-detected in <YYYY-MM> expense pull, not previously registered.`) and the user told you what the tool actually is, replace the note with a one-line description grounded in the user's answer (e.g. `Email automation tool used for nurture sequences.`). Keep it short — the audit summary and replacement-idea page hold longer context.

### 3. Generate replacement mini-specs

For each **replace-candidate**, create a page at `<finance_docs_root>/audits/replacement-ideas/<tool-slug>.md` using the template in `references/templates.md`. Fill out:

- **Problem** — what does this tool actually do for the org (1-2 sentences, grounded in the user's answer to question 2).
- **Proposed replacement** — what to build: Claude skill, Composio workflow, custom micro-app, or hybrid? Concrete design, not vague ideas.
- **Tools / APIs needed** — list the Composio toolkits, external APIs, or infra required.
- **Rough complexity** — hours or days to build, scale 1-5.
- **Estimated savings** — `cost_monthly × 12` per year, minus any new infra cost and a realistic Claude API cost estimate if the build is LLM-heavy.
- **Risks / tradeoffs** — where the custom build might fall short vs the SaaS tool.

Ground each proposal in things the org already has. Before proposing Composio-based replacements, check which toolkits are actually connected. Don't propose building against toolkits that aren't linked unless the mini-spec explicitly flags the required `composio link <toolkit>` step.

### 4. Write the audit summary

Write `<finance_docs_root>/audits/YYYY-MM-DD-subscription-audit.md` using the template in `references/templates.md`. Include:

- Date of audit.
- Total subs reviewed + combined monthly cost.
- Breakdown by classification (keep / cancel-candidate / replace-candidate) with monthly and annual totals.
- Projected annual savings if all cancel-candidates + replace-candidates are acted on.
- Wikilinks to each replacement-idea page.
- Recommended **top 3** next builds (one-sentence "why this one first" each).

### 5. Update `subscriptions.md`

Bump the `updated` frontmatter field. Ensure every reviewed sub has a correct `status:`. Immediately under the registry's main H1 heading (e.g. `# <Org Name> Subscriptions`) and above the Totals block, add or replace a "Last audit" line:

> Last audit: [[audits/YYYY-MM-DD-subscription-audit]] — N cancel candidates, M replace candidates.

### 6. Report back

Tell the user:

- How many subs audited.
- Total monthly cost reviewed.
- Number of cancel candidates + dollar savings.
- Number of replacement ideas drafted + dollar savings.
- A link to the audit summary.
- Top 3 recommended next builds.

## Prioritizing replacement ideas

Rank `replace-candidate` mini-specs by:

1. **Annual savings** — higher = higher priority.
2. **Build complexity** — lower = higher priority.
3. **Reusability** — if one build replaces multiple tools, boost.
4. **Strategic fit** — tools in the org's core domain score higher than peripheral tools.

The full prioritization rationale is in `../../references/atlas-expense-methodology.md` §6.

## Stop conditions

Stop and hand back to the user if:

- `subscriptions.md` is empty (no entries under `## Active`) — instruct the user to run `monthly-expense-report` first.
- A subscription entry can't be parsed per the recipe in `schemas.md` — surface the raw text and ask for manual cleanup rather than guessing.
- The user rejects the classification of >3 tools in a row — recalibrate the rules with them before continuing.
- A single replacement mini-spec becomes complex enough to warrant its own planning session — write a stub note, flag it, and continue.

## Additional Resources

### Reference Files

- **`references/templates.md`** — Mini-spec template (replacement-ideas pages) and audit summary template.
- **`../monthly-expense-report/references/schemas.md`** — Shared schema and parse recipe for `subscriptions.md`. This skill reads but does not own that schema.
- **`../../references/atlas-expense-methodology.md`** — The 3-question interview rationale, classification rules, mini-spec rules, and prioritization weighting.

### Examples

- **`examples/replacement-idea.md`** — A fully-filled-out replacement mini-spec.
- **`examples/audit-summary.md`** — A completed audit summary file.
