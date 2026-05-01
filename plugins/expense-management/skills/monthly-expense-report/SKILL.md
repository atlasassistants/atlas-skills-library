---
name: monthly-expense-report
description: Pull the previous (or specified) month's bookkeeping transactions from the configured bookkeeping system via Composio, filter to the configured SaaS / software bucket, write a dated markdown report to the finance docs root, and reconcile the living subscriptions registry. Detects new vendors, missing charges, and price changes >10%. Bookkeeping system is pluggable per implementation; v0.1 ships with QuickBooks.
when_to_use: |
  User asks to "run the monthly expense report", "pull this month's expenses", "generate the April expense report", "what did we spend on tools last month", or "update the subscriptions list". Also when a scheduled monthly run fires (typically the 1st of the month). Do NOT use this for full P&L pulls or non-software expense categories — this skill only pulls the configured bookkeeping bucket.
atlas_methodology: opinionated
---

# monthly-expense-report

Generate a monthly expense report for recurring software/SaaS spend by pulling transactions from a bookkeeping system via Composio, normalizing them through a system-specific implementation, writing a dated markdown report into the configured finance docs root, and keeping the living `subscriptions.md` registry in sync.

## Architecture — pluggable per bookkeeping system

This skill is structured in two halves:

- **The universal half (this file):** loads config, computes the date range, dispatches to the implementation, reconciles the result against `subscriptions.md`, writes the report, summarizes to the user.
- **The system-specific half (`../../implementations/<system>/procedure.md`):** pulls transactions from the configured bookkeeping system, filters to the configured bucket, and returns a list of normalized transactions in the shape defined in `references/schemas.md`.

`<system>` is `bookkeeping.system` from the client config. v0.1 supports `quickbooks`. Adding a new system is a folder, not a refactor.

The opinionated reasoning behind the single-bucket bookkeeping pattern is in `../../references/atlas-expense-methodology.md` (plugin root). Read it before changing the classification rules.

## Path conventions in this file

Paths in this SKILL.md are **relative to this file's location** (`<plugin>/skills/monthly-expense-report/SKILL.md`). `references/...` resolves to this skill's siblings; `../../references/...` and `../../implementations/...` resolve to plugin-root locations.

## Prerequisites

Before running, verify:

1. **Locate the client config (`expense-config.md`).** Try these in order:
   1. If a previous session recorded the config path in session memory or knowledge base, use it.
   2. Otherwise, ask the user: "Where is your `expense-config.md`? (Default convention is `<finance_docs_root>/expense-config.md`.)"
   3. If the user can't tell you, check common locations: `<cwd>/expense-config.md`, `<cwd>/areas/finances/expense-config.md`, `<cwd>/finances/expense-config.md`. If none exist, stop and instruct the user to copy the template from `../../client-profile/templates/expense-config.template.md` to a known location, then retry.
   
   Once located, persist the path so future runs don't have to ask. Then read it and extract `finance_docs_root`, `bookkeeping.system`, and the system-specific bucket identifiers (e.g. for `quickbooks`: `bookkeeping.account.id` and `bookkeeping.account.fully_qualified_name`). If any required field is empty, stop and ask the user to fill it in.
2. **An implementation exists for `bookkeeping.system`.** Look for `../../implementations/<bookkeeping.system>/procedure.md`. If the folder is missing, stop and tell the user this implementation hasn't been built yet — list the implementations that do exist (i.e. directories under `../../implementations/`).
3. **The system's Composio toolkit is linked.** Each implementation lists the required toolkit slug in its `README.md`. Confirm with `composio connections list`. If the toolkit is not linked, instruct the user to run `composio link <toolkit>` and stop.
4. **Finance docs directories exist.** `<finance_docs_root>/` and `<finance_docs_root>/monthly-reports/` must exist. Create them if missing.

## Inputs

Determine the target month from the user's request:

- Explicit month: "April expense report" → `2026-04`
- "This month" → current month-to-date
- "Last month" or unspecified → previous complete month (default)

Always resolve to `YYYY-MM` and confirm with the user before pulling, unless the run is non-interactive (a scheduled run sets the month automatically).

## Procedure

### 1. Compute the date range

- `start_date = YYYY-MM-01`
- `end_date = last day of the month` — compute it; do not hardcode 30/31.

### 1b. Load the prior month's report (if it exists)

The Summary's MoM delta and the per-vendor price-change check both need last month's totals. Read this once now so step 3 and step 5 don't have to.

- Open `<finance_docs_root>/monthly-reports/<prev>-report.md` (where `<prev>` is the month before the target, in `YYYY-MM` form).
- If the file exists, extract:
  - **Last month's totals** from the Summary table: `prior_total_expenses`, `prior_transaction_count`.
  - **Per-vendor totals** from the "Subscriptions this month" table: a dict `{tool_name → {total: <amount>, charge_count: <int>}}`. Match prior reports may use slightly different column names (`Total`, `Amount`, `Amount (total)` are all valid synonyms across versions); take the dollar column regardless of header.
- If the file does NOT exist, set `prior_total_expenses = None`, `prior_transaction_count = None`, `prior_per_vendor = {}`. The skill must continue gracefully:
  - Step 3's per-vendor price-change check is skipped for every vendor (no flags raised).
  - Step 5's Summary table omits the "Last month" and "Δ" columns and adds a one-line note: "No prior report; MoM comparison skipped."

### 2. Pull transactions via the configured implementation

Read `../../implementations/<bookkeeping.system>/procedure.md` and follow it. Pass:

- The date range from step 1.
- The bookkeeping bucket identifiers from the client config (the implementation's README documents which fields it expects).

The implementation is responsible for:

- Calling the right Composio tool slug.
- Handling that system's response shape and quirks.
- Filtering server-side or client-side as the system requires.
- Normalizing each surviving transaction to the universal shape in `references/schemas.md`.

The output of this step is a list of `{date, vendor, amount, currency, memo, raw}` records — already filtered to the bucket. The rest of the procedure is system-agnostic.

### 3. Reconcile against `subscriptions.md`

Read `<finance_docs_root>/subscriptions.md` (create it from the template in `references/schemas.md` if missing). Use the parse recipe in that same file.

**Match key:** compare each transaction's `vendor` field (from the implementation's normalized output) against the `- vendor:` field of each registered subscription — **not** the `### <Tool Name>` heading. The H3 is a human display name; the bullet `vendor` is the merchant string that the bookkeeping system reports. Match is case-insensitive exact-string. If the merchant string varies across months for the same vendor (e.g. "Anthropic" vs "Anthropic, Inc"), the user has to merge them by hand in `subscriptions.md` — see the README's troubleshooting section.

**Group transactions by vendor first.** A vendor may charge multiple times in one month (AWS, Adobe, OpenAI). For each vendor's group, compute:

- `this_month_total` — sum of all charges in the group
- `this_month_charge_count` — number of charges
- `this_month_latest_date` — the latest charge date (use plain max; same-date ties don't matter because we only need the date)

For each unique vendor:

- **Known vendor** (already in `subscriptions.md`) → set:
  - `last_charged = this_month_latest_date`
  - `last_amount = this_month_total` (the **total** charged this month for the vendor — single-charge vendors are unaffected; multi-charge vendors get the aggregate)
  - `last_charge_count = this_month_charge_count` (omit if `1`; the field is optional and only emitted when >1)
  
  Then run the price-change check (see below).

- **New vendor** (no matching `vendor:` in registry) → add a new entry under `## Under review` with these defaults:

  | Field | Default |
  |---|---|
  | `### <Tool Name>` heading | The vendor string, title-cased |
  | `vendor` | The vendor string verbatim from the transaction |
  | `category` | `other` |
  | `cost_monthly` | `this_month_total` |
  | `billing_cycle` | `monthly` |
  | `status` | `needs-review` |
  | `first_charged` | `this_month_latest_date` |
  | `last_charged` | `this_month_latest_date` |
  | `last_amount` | `this_month_total` |
  | `last_charge_count` | `this_month_charge_count` (only if >1) |
  | `notes` | `Auto-detected in <YYYY-MM> expense pull, not previously registered.` |

  Flag in the report under "New subscriptions detected" so the user knows to confirm category and billing cycle at the next audit.

**Price-change check.** Compare `this_month_total` against **last month's total** for the same vendor. The prior total comes from the previous monthly report at `<finance_docs_root>/monthly-reports/<prev>-report.md` — read its "Subscriptions this month" table, locate the vendor's row by `Tool` (H3) name, and take the dollar column. If the prior report doesn't exist, or the vendor isn't in its table, **skip the price-change check** for this vendor (no flag, no error).

Also skip the price-change check entirely if the registry entry has `status: needs-review` — its prior `last_amount` is auto-detected and unreliable until the user confirms it.

The flag triggers when `|this_month_total − prior_total| / prior_total > 0.10`. Show both totals and the percent change in the report's "Price changes this month" section.

**After processing all transactions**, scan the `## Active` section only for vendors with no matching transaction this month and flag them under "Subscriptions that did not charge this month" (may indicate cancellation, annual billing, or a sync gap). Do **not** scan `## Under review`, `## Archived`, or any sub with `status: cancelled` — those are expected to have no charges.

### 4. Update `<finance_docs_root>/subscriptions.md`

Apply the classifications from step 3. Keep the file sorted by `cost_monthly` descending **within each section**. Recompute and refresh the **Totals** block at the top (active monthly cost, active annual cost, count of active subs and subs under review).

Bump the `updated` field in the frontmatter.

### 5. Write the monthly report

Write to `<finance_docs_root>/monthly-reports/YYYY-MM-report.md`. Use the frontmatter and body structure in `references/schemas.md` — that file is the source of truth for the report's exact section layout, columns, and wording. The skill's job here is to fill in the data; the schema file owns the form.

In short, the report has these sections (see schemas.md for the exact nesting):

- **Summary** — totals, MoM delta, transaction count, top 5 vendors.
- **Subscriptions this month** — one row per matched vendor, with sub-sections for new subscriptions detected, subs that didn't charge, and price changes >10%.
- **Appendix** — flat date-sorted list of every transaction pulled this month.

**Reading the prior month's totals (for MoM delta).** Read `<finance_docs_root>/monthly-reports/<prev>-report.md` (where `<prev>` is the month before the target). Parse its **Summary** table to get last month's total expenses and transaction count. Parse its **Subscriptions this month** table to get per-vendor totals (used by the price-change check in step 3). If the prior report doesn't exist, omit the "Last month" and "Δ" columns from this report's Summary table and skip the per-vendor price-change check entirely — surface a one-line note in the Summary saying "No prior report; MoM comparison skipped."

Cross-link the report to the registry with `[[subscriptions]]` (or the host knowledge base's equivalent internal link). Make the `Source:` line system-aware (`Source: <bookkeeping.system> (via Composio) — pulled YYYY-MM-DD`).

### 6. Report back

Summarize to the user:

- Bookkeeping system used and total expenses pulled (from the configured bucket only).
- Count of new subscriptions detected (`needs-review`).
- Count of subs that didn't charge this month (potential cancellations).
- Count of price changes flagged.
- A link to the generated report.

Do not read the full report back — the user will open the file.

## When the implementation errors out

The implementation's `procedure.md` lists its own error handling. If it surfaces an error you can't resolve at the universal layer, stop and report it. Never fabricate transaction data.

## Additional Resources

### Reference Files

- **`references/schemas.md`** — `subscriptions.md` schema, parse recipe, the universal normalized transaction shape, and the monthly report structure.
- **`../../implementations/<system>/procedure.md`** — System-specific pull procedure. v0.1 ships `quickbooks`.
- **`../../implementations/<system>/README.md`** — System-specific setup, required Composio toolkit, and field-naming conventions.
- **`../../references/atlas-expense-methodology.md`** — Why Atlas uses a single bookkeeping bucket, the >10% price-change rule, and what this plugin deliberately does not do.

### Examples

- **`examples/subscriptions.md`** — A populated subscriptions registry.
- **`examples/monthly-report.md`** — A fully-rendered monthly report.
