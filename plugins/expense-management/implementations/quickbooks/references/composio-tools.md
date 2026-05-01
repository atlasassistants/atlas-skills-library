# Pinned Composio tool slugs — QuickBooks

Slugs last verified 2026-04-23 against the Composio `quickbooks` toolkit. Update the verification date and pinning notes after running this plugin against your own QuickBooks connection.

## Read-only rule

**This plugin only reads from QuickBooks. Never call any tool that mutates QBO state.**

Only call tools whose slug starts with one of:
- `QUICKBOOKS_GET_*` (reports, company info, single-record reads)
- `QUICKBOOKS_QUERY_*` (entity queries)
- `QUICKBOOKS_READ_*` (single-entity detail reads)

Never call any slug starting with `QUICKBOOKS_CREATE_`, `QUICKBOOKS_UPDATE_`, `QUICKBOOKS_DELETE_`, `QUICKBOOKS_POST_`, or similar. Bookkeeping lives in QBO — writes belong to the bookkeeping team, not this plugin.

## Primary slugs (for monthly expense report)

| Purpose | Slug | Status |
|---------|------|--------|
| Full transaction list for a date range (main pull for the report) | `QUICKBOOKS_GET_TRANSACTION_LIST_REPORT` | PINNED |
| Vendor-scoped expense summary (use for the Subscriptions section) | `QUICKBOOKS_GET_VENDOR_EXPENSES_REPORT` | PINNED |
| General entity query (bills, vendors, payments, etc.) | `QUICKBOOKS_QUERY_ENTITIES` | PINNED — verified with vendor query |

## Secondary slugs (use if primary fails or richer context needed)

| Purpose | Slug |
|---------|------|
| P&L summary for the period | `QUICKBOOKS_GET_PROFIT_AND_LOSS_REPORT` |
| P&L with line-item detail | `QUICKBOOKS_GET_PROFIT_AND_LOSS_DETAIL_REPORT` |
| General ledger | `QUICKBOOKS_GET_GENERAL_LEDGER_REPORT` |
| Aged payables | `QUICKBOOKS_GET_REPORT_AGED_PAYABLE_DETAIL` |
| Chart of accounts (formatted) | `QUICKBOOKS_GET_REPORT_ACCOUNT_LIST` |
| Chart of accounts (raw entities) | `QUICKBOOKS_QUERY_ACCOUNT` |
| Trial balance | `QUICKBOOKS_GET_REPORT_TRIAL_BALANCE` |
| List of available report types | `QUICKBOOKS_GET_REPORTS` |
| Company profile | `QUICKBOOKS_GET_COMPANY_INFO` |
| Company settings / accounting method | `QUICKBOOKS_GET_PREFERENCES` |
| Single bill / payment detail | `QUICKBOOKS_GET_BILL`, `QUICKBOOKS_GET_BILL_PAYMENT` |
| Single vendor / account detail | `QUICKBOOKS_READ_VENDOR`, `QUICKBOOKS_READ_ACCOUNT` |

## Known quirks (from Composio's toolkit guidance)

**`QUICKBOOKS_GET_TRANSACTION_LIST_REPORT`:**
- Rows are report-structured (Header/Columns/Rows). Only `row.type == "Data"` are transaction lines; skip Section/Header/Summary rows. Rows may be nested inside Sections.
- Map each `Row.ColData[i]` to its column by the `Columns.Column[i].ColTitle` — positional.
- Large ranges can hit `ToolRouterV2_PayloadTooLarge`. Split the month by week if needed.
- Narrow windows may return `Header.Option NoReportData == "true"` — treat as valid empty result.

**`QUICKBOOKS_QUERY_ENTITIES`:**
- No-match queries omit the entity key: `QueryResponse` may come back `{}` with no `Vendor`/`Bill` array. Guard against missing keys.
- Paginate with `STARTPOSITION`/`MAXRESULTS`; default page size is ~100 for Bills.
- Avoid complex `LIKE`/`OR` patterns in WHERE — QueryParserError 4000 is common. Keep literals quoted.
- `VendorRef.*` filters on Bill sometimes fail with ValidationFault 4001 — filter client-side instead.

**`QUICKBOOKS_GET_VENDOR_EXPENSES_REPORT`:**
- Same report-row shape as the transaction list report. Parse recursively for Sections.

## Sample: verified query (2026-04-23)

```bash
composio execute QUICKBOOKS_QUERY_ENTITIES -d '{"query":"SELECT Id, DisplayName FROM Vendor MAXRESULTS 3"}'
```

Response shape:
```yaml
top_level_key: data.QueryResponse
entity_array_key: Vendor         # varies by entity type
per_vendor_fields:
  Id: string
  DisplayName: string
  sparse: bool
pagination:
  type: offset
  page_size_default: 100
  page_param: STARTPOSITION       # passed inside the SQL-style query string, not as a top-level arg
```

## How to pin / update

After a successful `composio execute` call against a new slug:
1. Move the slug from "Secondary" to "Primary", or add it to the tables if new.
2. Record the observed response shape and any gotchas.
3. Update the `Status` column to `PINNED` with the verification date.
