# Family Expense Tracker --- User Flows

## Dashboard

Open application → Dashboard → view Cash/Bank Balance, Credit Available,
Credit Used, and family positions → expand Financial Accounts when
needed → view individual accounts.

## Add Person

People → Add Person → enter details → Save → person becomes Active and
can be selected for new transactions.

## Edit Person

People → select person → Edit → change details → Save → historical
transactions remain unchanged.

## Archive Person

People → select person → Archive → status becomes Archived → removed
from normal new-transaction selection → history remains intact.

## View Person

People → select person → view financial position and transaction
history.

## Add Bank Account

Accounts → Add Bank Account → enter name and opening balance → Save →
account becomes Active.

## Edit Bank Account

Accounts → select account → Edit → update details → Save → historical
transactions remain associated.

## Archive Bank Account

Accounts → select account → Archive → account becomes Archived →
unavailable for normal new transactions → history remains intact.

## Add Credit Card

Accounts → Add Credit Card → enter name, credit limit, and opening
available credit → Save → card becomes Active. If available credit
equals the limit, used credit is zero.

## Edit Credit Card / Change Limit

Accounts → select card → Edit → change permitted details/limit → Save →
historical transactions remain intact and current credit position
remains consistent.

## Archive Credit Card

Accounts → select card → Archive → card becomes Archived → unavailable
for normal new transactions → history remains intact.

## Add Expense Using Bank

Add Transaction → Date → Person → Expense → Bank Account → Amount →
Description → Save → decrease person's ledger and bank balance.

## Add Expense Using Credit Card

Add Transaction → Date → Person → Expense → Credit Card → Amount →
Description → Save → decrease person's ledger, decrease available
credit, and increase used credit.

## Record Money Received

Add Transaction → Date → Person → Received → Bank Account → Amount →
Description → Save → increase person's ledger and bank balance.

## Pay Credit Card from Bank

Credit Card → Make Payment → select card → amount → payment source =
bank account → select bank account → date → Confirm → decrease bank
balance and increase available credit.

## Pay Credit Card with Cash

Credit Card → Make Payment → select card → amount → payment source =
cash → date → Confirm → increase available credit and decrease used
credit. Cash does not need to be modeled as a bank account unless
requirements later change.

## Edit Transaction

Open active transaction → Edit → change one or more fields → reverse
effects of original transaction → apply effects of updated transaction →
save.

Examples: - Amount changed: reverse old amount and apply new amount. -
Account changed: restore old account and apply new account. - Person
changed: restore old person's effect and apply new person's effect. -
Type changed: reverse old effects and apply the new type's effects. -
Multiple fields changed: reverse the complete original transaction and
apply the complete updated transaction.

## Void Transaction

Open active transaction → Void → reverse all financial effects → set
status to Voided → retain transaction in historical records.

## Transaction History

Transactions → view all records → search/filter → combine filters → sort
→ open transaction → view details → edit or void when permitted.

Supported filters: person, account, account type, transaction type,
date/date range, and amount/range.

## Status Model

People and accounts: Active / Archived. Transactions: Active / Voided.
