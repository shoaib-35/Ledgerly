# Transaction Import & Export

Ledgerly supports transaction import/export in CSV, XLSX, and legacy XLS formats.

## Canonical import columns

The safest workflow is to download a Ledgerly import template or export existing Ledgerly transactions and use that file as the source for future imports.

| Column | Required | Meaning |
|---|---|---|
| `transaction_id` | No | Stable Ledgerly UUID. Existing IDs are skipped during import, which prevents accidental duplicate re-imports. |
| `date` | Yes | Transaction date. Preferred format: `YYYY-MM-DD`. |
| `transaction_type` | Yes | `EXPENSE`, `RECEIVED`, `INCOME`, `BONUS`, `EXTRA`, `CARD_PAYMENT`, or `TRANSFER`. Display labels are also accepted. |
| `amount` | Yes | Positive decimal amount without a currency symbol. |
| `description` | Yes | Transaction description. |
| `status` | No | `ACTIVE` or `VOIDED`. Blank means `ACTIVE`. |
| `person_id` / `person_name` | No | Person reference. Expense and Received transactions require a person. |
| `account_id` / `account_name` | No | Normal transaction account. For a transfer this may also identify the destination. |
| `source_account_id` / `source_account_name` | No | Source account for transfers or bank-funded card payments. |
| `destination_account_id` / `destination_account_name` | No | Destination account for transfers. |
| `payment_source` | No | For card payments: `BANK_ACCOUNT` or `CASH`. |
| `created_at` | No | ISO datetime used to preserve same-day ordering when moving data between Ledgerly instances. |

## Transaction types

- `EXPENSE`: requires a person and account.
- `RECEIVED`: requires a person and bank account.
- `INCOME`, `BONUS`, `EXTRA`: require a bank account.
- `CARD_PAYMENT`: requires a credit card and `payment_source`. Bank-funded payments also require a bank source account.
- `TRANSFER`: requires different source and destination accounts.

## Account and person matching

IDs are preferred because names can be duplicated. If an ID is blank, Ledgerly performs a case-insensitive exact name match. If more than one active record has the same name, the row is rejected and the corresponding UUID must be supplied.

Archived people and accounts cannot be used for newly imported transactions.

## Safety rules

- The file is validated before any transaction is written.
- If a row fails validation, the import is rejected without a partial import.
- Imported transactions still pass through Ledgerly's normal balance/timeline validation.
- Existing `transaction_id` values are skipped rather than duplicated.
- Imports are limited to 10 MB and 10,000 rows per upload.
- Spreadsheet-exported text is protected against formula injection.
