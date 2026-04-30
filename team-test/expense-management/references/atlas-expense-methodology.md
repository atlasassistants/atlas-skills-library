# Atlas Expense Methodology

This plugin encodes how Atlas Assistants tracks SaaS spend, classifies subscriptions, and decides what to cancel or replace with custom AI builds. It is opinionated. The patterns below are battle-tested in Atlas's own bookkeeping flow; clients may fork this reference and edit it to match their own bookkeeping discipline.

## 1. The single-bucket bookkeeping pattern

Atlas's bookkeepers classify **every recurring software/SaaS/subscription charge under one expense account** — `Office Expenses:Software & Apps`. The plugin pulls only that bucket every month.

**Why it matters:**

- One pull, one filter, one source of truth. The agent does not have to crawl every expense category guessing what is or isn't software.
- Bookkeeping discipline forces vendors to be coded correctly at intake, not after the fact.
- The "subscriptions registry" (`subscriptions.md`) is a near-perfect 1:1 with this bucket — drift between the two surfaces real bookkeeping errors.

**What Atlas does NOT do:**

- We do not run the report against every expense category and post-classify by vendor name. That is brittle and produces false positives.
- We do not split SaaS across multiple buckets (e.g. "tools by team", "AI vs non-AI"). That is a reporting concern, not a bookkeeping concern. Splits live in the registry's `category:` field, not in the chart of accounts.

**Adapting this for your org:**

If your bookkeeping team uses multiple buckets, you have two choices:

1. **Negotiate single-bucket** with bookkeeping. This is the cheapest fix and is what we recommend. It also makes their close cycle faster.
2. **Multi-bucket support.** Edit `client-profile/templates/expense-config.template.md` to list multiple `account` entries and update the skill body to loop the pull. This is more code and weakens the source-of-truth guarantee.

## 2. The subscription classification rules

Both skills agree on three statuses (plus a holding status for new detections):

- **`active`** — confirmed core subscription, charged on schedule.
- **`needs-review`** — auto-detected from a transaction this month but not yet confirmed by a human. Default for any new vendor.
- **`cancel-candidate`** — flagged for cancellation. The user explicitly said "drop", or the subscription has not been used in 30+ days, or the user rated it 1/5 on the criticality scale.
- **`replace-candidate`** — used but rated 2-3/5, or the user said "we could build this". A replacement mini-spec gets drafted.
- **`cancelled`** — terminal state. Recorded with `cancelled_date`.

Evaluation is **first match wins** in this order: cancel-candidate → keep → replace-candidate.

**Why first-match-wins:**

The audit interview is structured (3 questions per tool), but humans give messy answers. The order ensures we don't accidentally classify a "drop it" answer as a replace-candidate just because the user also mentioned a feature they like.

## 3. The 3-question audit interview

Per subscription, ask exactly three questions in a single message:

1. When did you last use this?
2. Is it still needed — would workflow break if we cancelled it?
3. On a scale of 1-5, how core is it (1 = could drop today, 5 = critical)?

**Why three questions and no more:**

A subscription audit is a fatigue test. The interview pace is the only thing standing between "audited 3 tools" and "audited 30 tools". Three questions is the maximum that fits in one message; six is where the user starts skipping. Keep it tight.

The 1-5 rating doubles as a forcing function — humans who refuse to give a number are usually defending a tool they should cancel. Note when the rating is reluctant.

## 4. The price-change flag (>10%)

If a subscription's amount this month differs from its previous `last_amount` by more than 10%, it gets flagged in the monthly report's "Price changes this month" section.

**Why 10%:**

This is the threshold where a price change is large enough to be a real signal — vendor rate hikes, plan upgrades the user forgot about, currency-conversion drift on annual subs charged monthly — but small enough that the alert isn't overwhelmed by routine variance (sales tax shifts, prorated charges, etc.).

The user should respond to a price-change flag by asking "did we knowingly upgrade?" — if not, the answer is usually "vendor raised rates, push back or cancel".

## 5. The replacement-with-AI mini-spec

For every `replace-candidate`, the audit produces a one-page mini-spec at `audits/replacement-ideas/<tool-slug>.md`. The mini-spec is short on purpose — it is a forcing function, not an architecture document.

**Required content:**

- **Problem** — what the tool actually does for the org (1-2 sentences). Grounded in the user's own answer to question 2 of the interview.
- **Proposed replacement** — concrete design: Claude skill, Composio workflow, custom micro-app, or hybrid. Vague proposals are rejected.
- **Tools / APIs needed** — list the Composio toolkits, external APIs, or infra. Don't name toolkits that aren't already connected (or flag the `composio link <toolkit>` step explicitly).
- **Rough complexity** — hours/days to build, scale 1-5.
- **Estimated savings** — `cost_monthly × 12` minus any new infra/API cost. Be honest about Claude API costs if the replacement is LLM-heavy.
- **Risks / tradeoffs** — where the SaaS does something the build can't.
- **Recommendation** — build now, build later, or do not replace. Default to "build later" unless complexity is low and savings are large.

**Why short and concrete:**

Atlas has tried long replacement specs and they sit in the audit folder unread. One-page mini-specs are the right unit because the next step is always either "go build it" or "drop it". If the mini-spec needs to be longer than one page, the right move is to spin out a separate planning session, not to bloat the audit.

## 6. Prioritizing builds across mini-specs

After the audit, rank `replace-candidate` mini-specs by:

1. **Annual savings** — higher = higher priority.
2. **Build complexity** — lower = higher priority.
3. **Reusability** — if one build replaces three tools (e.g. one Composio Gmail automation replacing three email tools), boost.
4. **Strategic fit** — Atlas's domain is AI agents, ops, automation. Tools in those categories score higher than peripheral tools.

The audit summary surfaces the **top 3** with a one-sentence "why this one first" each. Three is the right number — top 1 is too narrow, top 5+ is paralysis.

## 7. What this plugin does NOT try to do

- **Pulling non-software expenses.** Out of scope. If you want a full P&L pull, use a separate tool against the QuickBooks P&L report.
- **Forecasting / budgeting.** The plugin reports historical spend and flags anomalies. It does not project future spend.
- **Approving expenses.** The plugin is read-only against QuickBooks. Approvals belong in the bookkeeping system.
- **Cancelling subscriptions for the user.** The plugin generates the cancel list; the user logs into vendor portals and cancels. Atlas has not built reliable auto-cancel flows yet, and we'd rather have a clean human gate than a flaky automation.

These omissions are deliberate. Adding any of them changes the plugin's job from "monthly bookkeeping companion" to "finance system", which is a different product.
