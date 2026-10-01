# Family Expense Tracker --- Features

## Dashboard

-   Financial summary for Cash / Bank Balance, Credit Available, and
    Credit Used.
-   Expandable account section.
-   Individual bank-account and credit-card balances.
-   Family settlement/financial-position summary.

## People Management

-   View all people.
-   Add person.
-   Edit/update person.
-   Archive person.
-   View person's financial position.
-   View person's transactions.

## Bank Account Management

-   View accounts.
-   Add account.
-   Edit/update account.
-   Set opening balance.
-   View current balance.
-   View transactions.
-   Archive account.

## Credit Card Management

-   View cards.
-   Add card.
-   Edit card.
-   Change credit limit.
-   View available and used credit.
-   View transactions.
-   Make full or partial payment.
-   Select bank account or cash as payment source.
-   Archive card.

## Transaction Management

### Add Transaction

Fields: date, person, transaction type, account/source, amount,
description.

### Transaction Types

-   Expense.
-   Money received.
-   Credit-card payment/transfer.
-   Money transfer between financial accounts.

### Edit Transaction

Editing must update every affected financial position. Amount, person,
account, and type changes must correctly reverse the old effects and
apply the new effects.

### Void Transaction

Voiding reverses all financial effects, marks the transaction Voided,
and preserves the record.

## Transaction History

-   View all records.
-   Search.
-   Sort.
-   Filter by person.
-   Filter by account.
-   Filter by account type.
-   Filter by transaction type.
-   Filter by date/date range.
-   Filter by amount/range.
-   Combine filters.

## Credit Card Payment

-   Select card.
-   Enter amount.
-   Select payment source: bank account or cash.
-   Enter date.
-   Restore available credit.
-   Reduce used credit.
-   Deduct from selected bank account when applicable.

## Archiving

-   Archive people and accounts rather than permanently deleting them.
-   Keep historical records.
-   Archived items cannot normally be selected for new transactions.

## Data Integrity

-   One user action produces all linked financial effects.
-   Person and account balances remain synchronized with active
    transactions.
-   Voided transactions no longer contribute to current balances.

## Transaction import and export
- Import and export transactions as CSV, XLSX, or legacy XLS.
- Provide downloadable import templates.
- Validate the complete file before writing transactions.
- Use stable transaction/account/person IDs where available to prevent ambiguity and duplicate imports.
- Preserve transaction type, account endpoints, card payment source, status, and same-day ordering metadata.

