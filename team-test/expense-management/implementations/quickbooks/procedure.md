# QuickBooks — Pull procedure

System-specific procedure for the `quickbooks` implementation. Called from `skills/monthly-expense-report/SKILL.md` step "pull transactions" when `bookkeeping.system == quickbooks` in the client config.

The procedure's job is simple: given a date range and the configured bookkeeping bucket, return a list of normalized transactions in the shape defined in [`schemas.md`](../../skills/monthly-expense-report/references/schemas.md#normalized-transaction-shape).

## Inputs

From the calling skill:

- `start_date` — `YYYY-MM-01`
- `end_date` — last day of the target month
- `account_id` — from `bookkeeping.account.id` in the client config
- `account_fully_qualified_name` — from `bookkeeping.account.fully_qualified_name` in the client config

## 1. Pull the transaction list report

Pinned slug: `QUICKBOOKS_GET_TRANSACTION_LIST_REPORT` (see [`references/composio-tools.md`](references/composio-tools.md)). Pass `account_ids` as an **array of strings** — passing it as a bare string fails schema validation with `Expected array, received string`.

Request body shape:

```json
{
  "start_date": "<start_date>",
  "end_date":   "<end_date>",
  "account_ids": ["<account_id>"]
}
```

Issue the call via the Composio CLI's `execute` command for the chosen tool slug.

**Critical quirk:** `account_ids` does **not filter server-side** for this report — the response includes transactions from every account. Filter client-side on the `Split` field in step 3.

Large responses are saved to a temp file and returned via `outputFilePath`. Handle both inline and file-path cases — read the response body, look for `outputFilePath`, and if present read the file at that path; otherwise the report is in `.data` directly.

## 2. Parse the report structure

The response is report-formatted, not entity-formatted:

- `.data.Header` — `{Currency, StartPeriod, EndPeriod, Option[{Name,Value}], ReportName, Time}`
- `.data.Columns` — `{Column: [{ColTitle, ColType}, ...]}`
- `.data.Rows` — `{Row: [...]}`. Nested Sections; leaf rows have `type == "Data"`.

**Columns (positional, in order):** Date, Transaction Type, Num, Posting, Name, Memo/Description, Account, Split, Amount.

- `Name` — the vendor.
- `Account` — the **paying** account (credit card / bank), not the expense category.
- `Split` — the **expense category** FullyQualifiedName (this is the filter target).

**Empty-results case:** if `Header.Option[Name="NoReportData"].Value == "true"`, treat as zero transactions (valid, not an error). Return an empty list.

## 3. Filter, flatten, and normalize

Walk the response tree recursively to extract every `type == "Data"` row (rows can be nested inside Sections). Map each `ColData[i].value` to its column title by position. Filter to the configured `account_fully_qualified_name`; drop zero-amount rows and rows with empty `Name`.

Reference `jq` recipe (adapt to your runtime — bash + jq, Python, etc.):

```bash
TARGET="<account_fully_qualified_name>"
jq -r --arg target "$TARGET" '
  .data.Columns.Column as $cols
  | [.. | objects | select(.type? == "Data")]
  | map(
      [ .ColData[] | .value ] as $vals
      | reduce range(0; $cols|length) as $i ({}; .[$cols[$i].ColTitle] = $vals[$i])
    )
  | map(select(.Split == $target and .Name != "" and (.Amount | tonumber) != 0))
' "$REPORT_JSON_PATH"
```

Then normalize each surviving row to the universal transaction shape:

```json
{
  "date":     "<row.Date>",
  "vendor":   "<row.Name>",
  "amount":   <row.Amount as number>,
  "currency": "<.data.Header.Currency, default USD>",
  "memo":     "<row['Memo/Description']>",
  "raw":      <the full row dict>
}
```

Return the list. The calling skill takes over from here for reconcile + write-report.

## 4. Error handling

- **Auth error (401/403)** — surface to the caller; the user must re-link the QuickBooks toolkit.
- **Rate limit** — wait 10s and retry once, then surface.
- **Schema mismatch** — re-fetch the tool schema with `composio execute QUICKBOOKS_GET_TRANSACTION_LIST_REPORT --get-schema` and adjust input shape. Do not guess.
- **Empty response (`NoReportData`)** — return an empty list. This is a valid month with no charges in the bucket, not a failure.
- **Payload too large** — split the date range by week and merge the results client-side. The skill body should accept multiple sub-pulls for one month.

Never fabricate transaction data. If the pull fails, stop and report the error to the caller.
