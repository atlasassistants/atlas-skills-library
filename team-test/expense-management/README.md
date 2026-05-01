# expense-management

> Monthly bookkeeping pull, living subscriptions registry, and AI-replacement audit — Atlas-style. Pluggable per bookkeeping system; v0.1 ships QuickBooks.
> v0.1.0

## What it does

Closes the loop on recurring software spend. Each month, the plugin pulls every transaction in the configured "Software & Apps" bookkeeping bucket via Composio, reconciles the charges against a living `subscriptions.md` registry in your knowledge base, and writes a dated monthly report. New vendors, missing charges, and price changes >10% are flagged for review.

On demand, a separate audit skill walks the registry interactively, asks three structured questions per tool, classifies each one as keep / cancel-candidate / replace-candidate, and drafts a one-page mini-spec for every replace-candidate describing how an AI-built replacement would work, what it would cost to build, and what the org would save annually.

The bookkeeping system is **pluggable**. The `monthly-expense-report` skill dispatches to a per-system procedure under `implementations/<system>/`, and the universal logic (reconcile, classify, write report) is system-agnostic. v0.1 ships an implementation for QuickBooks. The audit skill works with any implementation because it operates on the registry, not the bookkeeping system.

The opinionated reasoning behind the single-bucket bookkeeping pattern, the 3-question interview, the >10% price flag, and the one-page mini-spec format is documented in `references/atlas-expense-methodology.md`.

## Who it's for

Operators, founders, and finance leads who manage a portfolio of SaaS subscriptions and want a recurring discipline for both bookkeeping reconciliation and "build vs buy" reviews. Atlas built this for ourselves — we use it monthly against our own QuickBooks — and the structure is designed to extend cleanly to clients running Xero, NetSuite, Zoho Books, or FreshBooks via the same Composio integration layer.

If your bookkeeping is split across many expense accounts, you'll need to either consolidate (recommended — see the methodology doc) or extend the active implementation to loop multiple buckets.

## Required capabilities

The plugin's skills depend on these capabilities. Each is named abstractly — wire it to whatever the host agent has access to.

- **Filesystem read + write** — read the per-client config and existing subscriptions registry; write monthly reports, audit summaries, and replacement-idea pages into a configured root directory.
- **Composio CLI invocation** — execute Composio tool slugs and read their JSON responses (inline or via `outputFilePath` for large payloads).
- **Bookkeeping toolkit access via Composio** — the user's bookkeeping toolkit (e.g. `quickbooks`, `xero`) must be linked. Read-only — the plugin never writes to the bookkeeping system.
- **JSON parsing + traversal** — bookkeeping reports are nested with system-specific shapes; the agent must be able to walk the response and apply a filter (jq, Python, JS, etc.).
- **User question + free-text response** (for `subscription-audit`) — ask the user three questions per subscription and parse a 1-5 rating from a natural-language reply.
- **Date math** — compute "previous complete month" and "last day of month" without hardcoding 30/31.

## Suggested tool wiring

| Capability | Common options |
|---|---|
| Filesystem read/write | Claude Code's `Read`/`Write`/`Edit`, Filesystem MCP, any agent runtime's filesystem tools |
| Composio CLI | `composio` CLI installed locally, or the Composio MCP server |
| Bookkeeping toolkit | Linked once via `composio link <toolkit>` — see "Supported bookkeeping systems" below |
| JSON traversal | `jq` (recipe shipped per implementation), Python, or any language the agent can run |
| Structured user question | Claude Code's `AskUserQuestion`, plain chat fallback |
| Date math | The agent's shell, or any language runtime |

These are examples, not requirements. Pick what the host actually has.

## Supported bookkeeping systems

The plugin's integration layer is Composio. Each bookkeeping system that has a Composio toolkit can be supported via an `implementations/<system>/` folder. Status as of v0.1:

| System | Composio toolkit | Tools | Implementation status |
|---|---|---|---|
| QuickBooks Online | `quickbooks` | 105 | ✅ Shipped (v0.1) |
| Xero | `xero` | 41 | Toolkit available — implementation not yet authored |
| NetSuite | `netsuite` | 85 | Toolkit available — implementation not yet authored |
| Zoho Books | `zoho_books` | 265 | Toolkit available — implementation not yet authored |
| FreshBooks | `freshbooks` | 10 | Toolkit available (smaller) — implementation not yet authored |

**Not currently supported via Composio:** Wave, Sage, Bench (no public API), Pilot (no public API), and raw bank-data approaches (e.g. Plaid). Supporting these would require a different integration layer; out of v0.x scope.

### Adding a new implementation

To add support for an already-toolkitted system (Xero, NetSuite, Zoho Books, FreshBooks):

1. Create `implementations/<system>/README.md` documenting required setup and the toolkit slug.
2. Create `implementations/<system>/procedure.md` following the contract in `skills/monthly-expense-report/SKILL.md` — input is the date range and bucket identifiers, output is a list of normalized transactions in the shape defined in `references/schemas.md`.
3. (Optional) Add `implementations/<system>/references/composio-tools.md` pinning the relevant tool slugs and known quirks.
4. Update the Supported systems table here, the example block in `client-profile/templates/expense-config.template.md`, and the entry in `monthly-expense-report/SKILL.md`'s prerequisites.

The audit skill, methodology doc, and reconcile/write-report logic do not need to change.

## Installation

```
/plugin marketplace add colin-atlas/atlas-skills-library
/plugin install expense-management@atlas
```

After installing, complete the first-run setup before running either skill.

> **Note (Team Test phase):** until this plugin is promoted to `plugins/`, install directly from the `team-test/` path rather than via the marketplace. See `docs/skill-lifecycle.md` for the team-test installation pattern.

## First-run setup

1. **Pick your bookkeeping system and link the Composio toolkit.** Once per machine: `composio link <toolkit>` (e.g. `composio link quickbooks`). Verify with `composio connections list`. v0.1 only ships an implementation for `quickbooks` — see "Supported bookkeeping systems" above for what else has a Composio toolkit.
2. **Create the per-client config.** Copy `client-profile/templates/expense-config.template.md` into your knowledge base — typical location is `<finance_docs_root>/expense-config.md`. Fill in:
   - `finance_docs_root` — absolute path to the directory where the plugin will read and write generated content.
   - `bookkeeping.system` — `quickbooks` for v0.1.
   - The system-specific account / category fields — see the example block in the template that matches your system.
3. **Create the directory structure.** The skills will auto-create missing folders, but you can pre-create them:

   ```
   <finance_docs_root>/
   ├── subscriptions.md            # seed empty, or let the first run create it
   ├── monthly-reports/
   └── audits/
       └── replacement-ideas/
   ```

4. **(Optional) Schedule the monthly run.** To pull the report automatically on the 1st of each month, pair this plugin with the `/schedule` skill — for example: `/schedule run /expense-management:monthly-expense-report on the 1st of each month at 9am`. The plugin itself ships no cron / launchd / systemd wiring; lifecycle scheduling belongs to the host.
5. **Smoke test.** Run `monthly-expense-report` against the previous month before relying on it. The first run is when bookkeeping miscategorizations and connection issues surface — fix them once, then trust the pipeline.

## Skills included

- **`monthly-expense-report`** — *opinionated.* Pulls the previous (or named) month's transactions from the configured bookkeeping system via Composio, dispatches to the matching `implementations/<system>/procedure.md`, reconciles `subscriptions.md`, and writes a dated report. Detects new vendors, missing charges, and price changes >10%.
- **`subscription-audit`** — *opinionated.* Walks the populated `subscriptions.md` registry interactively, runs the 3-question interview per tool, classifies each as keep / cancel-candidate / replace-candidate, and drafts an AI-replacement mini-spec for every replace-candidate. System-agnostic.

## Customization notes

This plugin is opinionated by design but every layer is editable. Common things clients change:

- **The bookkeeping bucket.** If your org uses multiple SaaS buckets, edit your `expense-config.md` to list multiple `account` entries and update the active implementation's `procedure.md` to loop the pull. The default assumes one bucket — see the methodology doc for why.
- **The classification rules.** Default: cancel if rated 1 or unused 30+ days; keep if rated 4-5; replace otherwise. Edit `references/atlas-expense-methodology.md` and the rules section of `skills/subscription-audit/SKILL.md` if your team uses different cutoffs.
- **The 3-question interview.** Default is three questions in one message. Some teams prefer five questions or a structured form — edit `subscription-audit/SKILL.md` step 2.
- **The >10% price-change threshold.** Default in `monthly-expense-report` step 3. Adjust to match your tolerance for noise vs signal.
- **The replacement mini-spec template.** Default in `skills/subscription-audit/references/templates.md`. Edit if you want different sections (e.g. add a "stakeholder sign-off" line).
- **The category list.** Default in `expense-config.template.md`. Add domain-specific categories (`compliance`, `legal-tooling`, etc.) as needed.

When customizing, edit the SKILL.md and reference files in your installed copy or your fork. The plugin is meant to be a starting point you adapt — not a black box.

## Atlas methodology

This plugin encodes Atlas's monthly bookkeeping discipline. The opinions are:

- **Single-bucket bookkeeping** — every recurring SaaS charge lives in one expense account, not split across many. The agent pulls that one bucket and reconciles. Bookkeeping correctness becomes an upstream concern instead of an agent guessing game.
- **The 3-question audit interview** — three questions per tool is the maximum that survives audit fatigue. The 1-5 rating is a forcing function; reluctant ratings predict replacements.
- **The >10% price-change flag** — small enough to catch real signals, large enough to ignore routine variance.
- **The one-page mini-spec** — replacement ideas are short on purpose. Long specs sit unread; one-pagers force a "build now / build later / drop" decision.

Full reasoning lives in [`references/atlas-expense-methodology.md`](references/atlas-expense-methodology.md). That is the file clients fork to encode their own variant.

## Troubleshooting

**`composio execute QUICKBOOKS_GET_TRANSACTION_LIST_REPORT` returns transactions from every account, not just yours.** Expected. The `account_ids` parameter does not filter server-side for this report — that is a known QuickBooks toolkit quirk. The implementation filters client-side on the `Split` column using your configured `fully_qualified_name`. If your filter is producing zero rows, log the distinct `Split` values from the response and confirm the FullyQualifiedName matches exactly (whitespace and colons are significant).

**Schema validation error: `account_ids: Expected array, received string`.** Pass `account_ids` as `["121"]`, not `"121"`. The Composio schema is strict about the array wrapper even for single values. Same pattern likely applies to other systems' `*_ids` parameters.

**Auth error 401/403 from QuickBooks (or another bookkeeping system).** The Composio connection has expired or is unlinked. Re-run `composio link <toolkit>` and retry. QuickBooks's OAuth token cycle is shorter than most other integrations.

**`subscription-audit` says `subscriptions.md` is empty.** Run `monthly-expense-report` at least once first — the registry is seeded by detection, not by hand. If the first run produces an empty registry, your bucket identifier (`fully_qualified_name`, `code`, `category.id`, etc.) is probably wrong; see the first troubleshooting item.

**A subscription was charged but doesn't appear in the report.** Two likely causes: (a) bookkeeping coded the charge to a different expense account, or (b) the charge posted just outside the date range. Query the bookkeeping system directly for the transaction to see which account it landed in.

**The same vendor shows up under two different names across months** (e.g., "Anthropic" vs "Anthropic, Inc"). Manually merge them in `subscriptions.md` — the plugin doesn't yet de-duplicate vendor name variants. If this happens often, add a vendor-aliases section to your client config and edit the active implementation to map aliases before normalization.

**`monthly-expense-report` says no implementation exists for my system.** v0.1 only ships `implementations/quickbooks/`. To add another: see "Adding a new implementation" above. The Composio toolkit existing is necessary but not sufficient — you also need a procedure.md that handles that system's response shape.

**Skill triggers when you didn't ask for it.** The `description` and `when_to_use` in the skill frontmatter may be matching too broadly for your phrasing. Edit them to narrow the triggers. Common: "expense" alone is too broad if the agent also has a non-software expense skill loaded.
