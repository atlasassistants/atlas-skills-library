---
title: Expense Management Plugin — Client Config
type: config
plugin: expense-management
---

# Expense Management — Client Config

Both skills in this plugin read from this config. Copy this template to a known location in your knowledge base (e.g. `<finance_docs_root>/expense-config.md`) and fill in the values for your org. The skill bodies refer to these values abstractly — they read this file at the start of every run.

## Finance docs root

The directory where the skills will read and write generated content.

```yaml
finance_docs_root: <absolute path to the directory>
```

The skill expects this directory layout (it will create missing subdirectories on first run):

```
<finance_docs_root>/
├── subscriptions.md                         # living registry — written by monthly-expense-report
├── monthly-reports/
│   └── YYYY-MM-report.md                    # one per month
└── audits/
    ├── YYYY-MM-DD-subscription-audit.md     # one per audit run
    └── replacement-ideas/
        └── <tool-slug>.md                   # one per replace-candidate
```

## Bookkeeping system + bucket

Atlas's bookkeeping convention is to classify every recurring SaaS / subscription / software charge under a **single expense account** in your chart of accounts. The plugin pulls only that bucket — it does not pull every category. If your bookkeeping team uses multiple buckets, see the README's "Customization notes".

Pick the block matching your bookkeeping system. Delete the others. v0.1 ships an implementation for `quickbooks` only — the other systems below have Composio toolkits available but the implementations have not been authored yet (see plugin README for the contribution path).

### QuickBooks Online (v0.1 — supported)

```yaml
bookkeeping:
  system: quickbooks
  composio_toolkit: quickbooks
  account:
    id: "<QuickBooks Account.Id, numeric string>"
    fully_qualified_name: "<full chart-of-accounts path>"
    type: Expense
    sub_type: <e.g. OfficeGeneralAdministrativeExpenses>
```

Example (Atlas's actual values — do not copy unless you are Atlas):

```yaml
bookkeeping:
  system: quickbooks
  composio_toolkit: quickbooks
  account:
    id: "121"
    fully_qualified_name: "003 Other Operating Expenses:Office Expenses:Software & Apps"
    type: Expense
    sub_type: OfficeGeneralAdministrativeExpenses
```

### Xero (Composio toolkit available — implementation not yet shipped)

```yaml
bookkeeping:
  system: xero
  composio_toolkit: xero
  account:
    code: "<Xero account code, e.g. 478>"
    name: "<account name, e.g. 'Subscriptions'>"
    type: Expense
```

### NetSuite (Composio toolkit available — implementation not yet shipped)

```yaml
bookkeeping:
  system: netsuite
  composio_toolkit: netsuite
  account:
    internal_id: "<NetSuite internal ID>"
    full_name: "<full account path>"
    type: Expense
```

### Zoho Books (Composio toolkit available — implementation not yet shipped)

```yaml
bookkeeping:
  system: zoho_books
  composio_toolkit: zoho_books
  account:
    account_id: "<Zoho Books account_id>"
    account_name: "<account name>"
    account_type: expense
```

### FreshBooks (Composio toolkit available — implementation not yet shipped, smaller toolkit)

```yaml
bookkeeping:
  system: freshbooks
  composio_toolkit: freshbooks
  category:
    id: "<FreshBooks category id>"
    name: "<category name, e.g. 'Software & Subscriptions'>"
```

### Other systems

Wave, Sage, Bench, Pilot, and raw bank-data alternatives (Plaid, etc.) are not currently available via Composio. Supporting them would require a separate integration layer; out of v0.x scope.

## Optional: category mappings

When new vendors are auto-added to `subscriptions.md` with `status: needs-review`, the skill assigns a placeholder category. Override the mapping below if your org uses different categories:

```yaml
categories:
  - ai-tools
  - infra
  - dev-tools
  - productivity
  - design
  - analytics
  - marketing
  - ops
  - other
```

## Optional: scheduled run

If you want the monthly report to run automatically, pair this plugin with the `/schedule` skill — see the plugin README's "First-run setup" section.

## How the skills find this file

The skills look for the config at `<finance_docs_root>/expense-config.md` first, then fall back to asking the user where it lives. Once located, the path is persisted in the user's session memory or knowledge base so it doesn't have to be re-asked each run.
