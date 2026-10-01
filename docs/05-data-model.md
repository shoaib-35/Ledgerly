# Data Model

## 1. Purpose

This document defines the application's logical data model.

The model separates:

- People/family ledgers
- Financial accounts
- Bank account details
- Credit card details
- Transactions
- Transaction effects
- Credit card payment details

The primary design goal is to keep financial balances derived from transaction data so that editing and voiding transactions can safely reverse and reapply their effects.

---

# 2. Core Entities

The initial data model contains these entities:

```text
Person
Account
BankAccountDetails
CreditCardDetails
Transaction
TransactionEffect
CardPaymentDetails
```

The entities are related as follows:

```text
Person
  │
  │ 1 ──────── *
  │
Transaction
  │
  │ 1 ──────── *
  │
TransactionEffect
  │
  └────────────── Account

Account
 ├── BankAccountDetails
 └── CreditCardDetails

Transaction
  ├── CardPaymentDetails (only for Card Payment transactions)
  └── MoneyTransferDetails (only for Money Transfer transactions)
```

---

# 3. Person

Represents a family member/person whose money is tracked through the application.

## Fields

| Field | Description |
|---|---|
| `id` | Unique identifier |
| `name` | Person's display name |
| `status` | `ACTIVE` or `ARCHIVED` |
| `created_at` | Creation timestamp |
| `updated_at` | Last update timestamp |

## Rules

- An active person can be selected for new applicable transactions.
- An archived person cannot be selected for new transactions.
- Historical transactions continue to reference archived people.
- A person's current financial position is derived from active transactions.

## Financial position

```text
Person Balance = Total Credits - Total Debits
```

Interpretation:

```text
Balance > 0  → User is holding money belonging to the person
Balance < 0  → Person owes money to the user
Balance = 0  → Settled
```

The UI can translate this into:

```text
Positive → Held
Negative → Receivable
Zero     → Settled
```

---

# 4. Account

Represents a financial account used by the application.

An account has one of two types:

```text
BANK
CREDIT_CARD
```

## Common fields

| Field | Description |
|---|---|
| `id` | Unique identifier |
| `name` | Account display name |
| `account_type` | `BANK` or `CREDIT_CARD` |
| `status` | `ACTIVE` or `ARCHIVED` |
| `created_at` | Creation timestamp |
| `updated_at` | Last update timestamp |

The account type should not change after creation unless a future migration explicitly supports it.

---

# 5. BankAccountDetails

Stores fields specific to bank accounts.

## Fields

| Field | Description |
|---|---|
| `account_id` | References `Account` |
| `opening_balance` | Balance at the starting point of tracking |

## Current balance

```text
Current Balance =
Opening Balance
+ Active incoming account effects
- Active outgoing account effects
```

A bank account can be used as a source for:

- Expenses
- Card payments

It can also receive money through Received transactions.

---

# 6. CreditCardDetails

Stores fields specific to credit cards.

## Fields

| Field | Description |
|---|---|
| `account_id` | References `Account` |
| `credit_limit` | Current credit limit |

## Credit card balance model

```text
Used Credit =
Active Card Expenses
- Active Card Payments

Available Credit =
Credit Limit - Used Credit
```

The application should treat available credit as borrowing capacity, not owned cash.

Therefore:

```text
Available Credit
```

must not be added to:

```text
Cash / Bank Balance
```

to produce a combined owned-money balance.

## Credit limit changes

The credit limit can be edited.

Changing the limit must not modify historical transactions.

Example:

```text
Old limit: ₹1,00,000
New limit: ₹1,20,000
```

Existing card usage remains unchanged.

---

# 7. Transaction

Represents one user-visible financial event.

## Fields

| Field | Description |
|---|---|
| `id` | Unique identifier |
| `date` | Financial transaction date |
| `person_id` | Associated person where applicable |
| `account_id` | Primary account where applicable |
| `transaction_type` | `EXPENSE`, `RECEIVED`, `CARD_PAYMENT`, or `TRANSFER` |
| `amount` | Positive monetary amount |
| `description` | Human-readable description |
| `status` | `ACTIVE` or `VOIDED` |
| `created_at` | Record creation timestamp |
| `updated_at` | Last update timestamp |

The transaction stores the amount as a positive value.

The direction of the financial effect is represented separately by transaction effects.

This avoids relying on negative input values in the Add Transaction form.

---

# 8. Transaction Types

## 8.1 Expense

Represents money spent for a person.

Example:

```text
Person: Mom
Account: HDFC Bank
Amount: ₹500
Type: Expense
```

Effects:

```text
Mom       -₹500
HDFC Bank -₹500
```

For a credit card:

```text
Mom             -₹500
HDFC Card Used  +₹500
Available Credit -₹500
```

The user enters the transaction once. The system applies the linked effects automatically.

---

## 8.2 Received

Represents money received for a person.

Example:

```text
Person: Dad
Account: SBI Bank
Amount: ₹2,000
Type: Received
```

Effects:

```text
Dad       +₹2,000
SBI Bank  +₹2,000
```

`Received` is used instead of `Income` because the money is associated with the tracked person's financial position and is not necessarily the user's personal income.

---

## 8.3 Card Payment

Represents a payment made toward a credit card.

A Card Payment:

- Targets one credit card.
- Has an amount.
- Has a payment source.
- Has a date.
- May use a bank account or cash.

Example using a bank account:

```text
Credit Card: HDFC Credit Card
Payment: ₹5,000
Source: SBI Bank
```

Effects:

```text
SBI Bank              -₹5,000
HDFC Credit Card Used -₹5,000
HDFC Available Credit +₹5,000
```

A Card Payment is not a normal Expense.

---

# 8.4 Money Transfer

Represents money moved directly between two owned financial accounts. It is distinct from an Expense, Received transaction, or Card Payment.

A transfer stores both endpoints in `MoneyTransferDetails`:

| Field | Description |
|---|---|
| `transaction_id` | References the transfer transaction |
| `source_account_id` | Account/card providing the funds |
| `destination_account_id` | Account/card receiving the funds |

Effects are generated atomically:

- Bank source → `BANK_BALANCE - amount`
- Credit-card source → `CREDIT_USED + amount`
- Bank destination → `BANK_BALANCE + amount`
- Credit-card destination → `CREDIT_USED - amount`

The source and destination must be different active accounts.

# 9. TransactionEffect

TransactionEffect records the financial effect produced by a transaction.

This provides a consistent mechanism for reversing transactions during editing and voiding.

## Fields

| Field | Description |
|---|---|
| `id` | Unique identifier |
| `transaction_id` | Parent transaction |
| `effect_target_type` | `PERSON` or `ACCOUNT` |
| `effect_target_id` | ID of affected person/account |
| `effect_type` | Defines the financial dimension affected |
| `amount` | Signed effect amount |

Examples:

```text
Transaction: Mom grocery expense ₹500

Effect 1
Target: PERSON / Mom
Effect Type: PERSON_BALANCE
Amount: -₹500

Effect 2
Target: ACCOUNT / HDFC Bank
Effect Type: BANK_BALANCE
Amount: -₹500
```

For a credit card expense:

```text
Effect 1
PERSON_BALANCE
-₹500

Effect 2
CREDIT_USED
+₹500
```

For a card payment:

```text
Effect 1
BANK_BALANCE
-₹5,000

Effect 2
CREDIT_USED
-₹5,000
```

The exact database implementation of effects may use a more normalized ledger structure later, but the logical model must preserve these financial effects.

---

# 10. CardPaymentDetails

Stores payment-specific information for a Card Payment transaction.

## Fields

| Field | Description |
|---|---|
| `transaction_id` | References the Card Payment transaction |
| `credit_card_account_id` | Credit card being paid |
| `payment_source_type` | `BANK_ACCOUNT` or `CASH` |
| `source_account_id` | Bank account used when source type is `BANK_ACCOUNT` |

## Rules

If:

```text
payment_source_type = BANK_ACCOUNT
```

then:

```text
source_account_id
```

is required.

If:

```text
payment_source_type = CASH
```

then:

```text
source_account_id
```

must be null.

Cash is not modeled as a full financial account in the current version.

---

# 10.5 MoneyTransferDetails

Stores the two account endpoints for a Money Transfer. It is a one-to-one child of the transfer transaction.

Rules:
- `source_account_id` is required.
- `destination_account_id` is required.
- Source and destination must differ.
- Both accounts must belong to the current user and be active when the transfer is created or edited.

# 11. Relationships

## Person → Transactions

```text
Person 1 ───────── * Transaction
```

A person can have many transactions.

A transaction may have a person when the transaction affects a person's ledger.

## Account → Transactions

```text
Account 1 ───────── * Transaction
```

An account can be involved in many transactions.

## Transaction → Effects

```text
Transaction 1 ───────── * TransactionEffect
```

Every active financial transaction should have the effects required to represent its financial impact.

## Transaction → CardPaymentDetails

```text
Transaction 1 ───── 0..1 CardPaymentDetails
```

Only Card Payment transactions have CardPaymentDetails.

---

# 12. Derived Values

The application should avoid storing balances that can be reliably calculated from source data.

## Person position

```text
Person Balance =
Sum of active person effects
```

Interpretation:

```text
Positive → Held
Negative → Receivable
Zero → Settled
```

## Bank current balance

```text
Current Balance =
Opening Balance
+ Sum of active bank balance effects
```

## Credit used

```text
Used Credit =
Sum of active credit-used effects
```

## Available credit

```text
Available Credit =
Credit Limit - Used Credit
```

## Dashboard values

```text
Cash / Bank Balance =
Sum of active bank account current balances

Credit Available =
Sum of active credit card available credit

Credit Used =
Sum of active credit card used credit
```

These three Dashboard values remain separate.

---

# 13. Transaction Lifecycle

Transactions use:

```text
ACTIVE
VOIDED
```

## Create

```text
Create Transaction
        ↓
Create transaction record
        ↓
Create financial effects
        ↓
Balances reflect effects
```

## Edit

The application should not directly mutate the old financial effects.

Instead:

```text
Existing Transaction
        ↓
Reverse old effects
        ↓
Update transaction details
        ↓
Create/apply new effects
        ↓
Recalculate/reflect balances
```

The transaction remains the same logical historical record.

## Void

```text
Active Transaction
        ↓
Reverse financial effects
        ↓
Mark transaction VOIDED
        ↓
Keep historical record
```

A voided transaction must not contribute to current balances.

---

# 14. Historical Integrity

The data model must preserve historical relationships.

Examples:

- Archived people remain connected to old transactions.
- Archived accounts remain connected to old transactions.
- Voided transactions remain visible in history.
- Editing a transaction does not create a second unrelated transaction record.
- Historical transaction dates are preserved.
- Changing a credit limit does not alter historical card transactions.

---

# 15. Validation Rules

The application should enforce at least the following:

### Person

- Name is required.
- Archived people cannot be selected for new transactions.

### Account

- Name is required.
- Account type is required.
- Bank accounts require opening balance.
- Credit cards require credit limit.
- Archived accounts cannot be selected for new applicable transactions.

### Transaction

- Date is required.
- Amount must be greater than zero.
- Transaction type is required.
- Person is required for transaction types that affect a person's ledger.
- Account is required for transaction types that require an account.
- Description may be optional unless a later requirement makes it mandatory.
- Voided transactions cannot be edited as active transactions.

### Card Payment

- Credit card is required.
- Amount must be greater than zero.
- Payment source is required.
- Bank account is required when Bank Account is selected.
- Cash does not require a source account.
- Payment amount must not exceed the card's currently used credit.

---

# 16. Important Design Principle

The application should have one authoritative financial model.

The UI should not independently calculate balances using separate formulas in different screens.

Instead:

```text
Transactions
     ↓
Transaction Effects
     ↓
Derived Financial Positions
     ↓
Dashboard / People / Accounts / Transactions
```

This keeps the Dashboard, People page, Accounts page, and transaction details consistent.

---

# 17. Current Scope

The initial data model does not include:

- Monthly credit card statements
- Credit card bills
- Budgets
- Categories
- Recurring transactions
- Notifications
- Multiple application users
- Roles and permissions
- Cash as a standalone account
- Investment accounts
- Loans
- Reports/analytics entities

These should only be added when a confirmed requirement exists.

---

# 18. Data Model Review Status

The logical data model is now defined for:

- People
- Bank Accounts
- Credit Cards
- Transactions
- Transaction Effects
- Card Payments
- Active/Archived/Voided states
- Derived balances
- Historical integrity
- Transaction reversal and editing

This model should be used as the foundation for the database design.

The next document should define the actual database schema, tables, columns, primary keys, foreign keys, indexes, constraints, and transaction/rollback strategy.
