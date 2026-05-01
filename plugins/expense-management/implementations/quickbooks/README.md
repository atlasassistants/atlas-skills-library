# QuickBooks Implementation

This is the `quickbooks` implementation for the `expense-management` plugin. It pulls transactions from QuickBooks Online via the Composio `quickbooks` toolkit and normalizes them into the shape the universal skill body expects.

## Status

Verified against Composio toolkit `quickbooks` (105 tools). Maintained and used in production by Atlas.

## Required setup

1. **Link the Composio toolkit:** `composio link quickbooks`. Verify with `composio connections list`.
2. **In your client config (`expense-config.md`):**
   ```yaml
   bookkeeping:
     system: quickbooks
     composio_toolkit: quickbooks
     account:
       id: "<QuickBooks Account.Id, e.g. 121>"
       fully_qualified_name: "<full chart-of-accounts path>"
   ```
   Find the values by querying `QUICKBOOKS_QUERY_ENTITIES` with `SELECT Id, Name, FullyQualifiedName, AccountType FROM Account` and locating your SaaS / software bucket.

## Files in this implementation

| File | Purpose |
|---|---|
| [`procedure.md`](procedure.md) | The system-specific procedure: which slug to call, request shape, parse logic, normalization to the universal transaction shape. |
| [`references/composio-tools.md`](references/composio-tools.md) | Pinned QuickBooks Composio tool slugs and known toolkit quirks. |

## Read-only

This implementation only calls QuickBooks `GET_*`, `QUERY_*`, and `READ_*` slugs. The plugin never writes to QuickBooks. Bookkeeping mutations belong to the bookkeeping team, not this plugin.
