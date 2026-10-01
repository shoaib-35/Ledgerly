# Family Expense Tracker --- Requirements

## 1. Project Purpose

A platform-independent web application for tracking family-related money
from the user's perspective, including money held for family members,
money owed to the user, and the financial accounts used for
transactions.

## 2. Core Financial Rules

-   Positive person balance: the user is holding excess money belonging
    to that person.
-   Negative person balance: that person owes the user money.
-   Zero person balance: settled.
-   Person balance = Total Credits - Total Debits.
-   Bank/cash balances represent money actually held.
-   Credit-card available credit is borrowing capacity, not owned cash.

## 3. People

The application must allow users to add, edit/update, archive, view
people, and view each person's transactions and financial position.
Archived people remain in historical records but cannot normally be
selected for new transactions.

## 4. Financial Accounts

### Bank Accounts

Support name, opening balance, current balance, status, and transaction
history. Users can add, edit, update, archive, and view transactions.
Current balance = Opening Balance + Money Received - Expenses.

### Credit Cards

Support card name, credit limit, available credit, used credit, status,
and transaction history. Users can add, edit, change credit limit,
archive, view transactions, and make payments. Used Credit = Credit
Limit - Available Credit. An expense decreases available credit and
increases used credit. A payment increases available credit and
decreases used credit. No separate monthly statement/bill entity is
required.

## 5. Transactions

Every transaction includes at least date, person where applicable,
transaction type, financial account/source where applicable, amount, and
description. Historical dates must be supported.

### Expense

Decreases the person's ledger and decreases the selected bank balance or
credit-card available credit.

### Money Received

Increases the person's ledger and increases the selected bank balance.

### Credit-Card Payment

Select credit card, amount, payment source (bank account or cash), and
date. Decrease the bank balance when applicable and restore the
credit-card available credit.

## 6. Transaction History

A dedicated page must show all transactions with search, sorting, and
combinable filters for person, account, account type, transaction type,
date/date range, and amount/range.

## 7. Dashboard

Show separately: - Cash / Bank Balance - Credit Available - Credit Used

Individual accounts are displayed inside an expandable section.

## 8. Archiving

People and accounts use Active/Archived status instead of destructive
deletion. Historical transactions and relationships remain intact.

Transactions use Active/Voided status. Voiding reverses all financial
effects while preserving the historical record.

## 9. Data Integrity

A transaction can affect both a person's ledger and a financial account.
These linked effects must remain consistent and the user must not enter
the same effect twice.
