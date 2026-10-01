# 06 — Database Design

## 1. Purpose

This document defines the PostgreSQL database design for the Family Expense Tracker using Python, Django, Django ORM, and PostgreSQL.

The design prioritizes financial integrity, historical preservation, derived balances, and atomic financial operations.

## 2. Database Technology

PostgreSQL is the primary relational database. Django ORM provides the application interface.

PostgreSQL is used for relational integrity, foreign keys, constraints, transactions, rollback, exact numeric types, indexes, and reliable concurrent operations.

## 3. Design Principles

- Transactions and transaction effects are the authoritative financial source.
- Balances are derived, not independently editable.
- Money uses PostgreSQL `NUMERIC(19,2)`, Django `DecimalField(max_digits=19, decimal_places=2)`, and Python `Decimal`.
- Transactions are never physically deleted; they become `VOIDED`.
- People and accounts are archived rather than deleted.
- Multi-record financial operations execute atomically.

## 4. Core Tables

1. `people`
2. `accounts`
3. `bank_account_details`
4. `credit_card_details`
5. `transactions`
6. `transaction_effects`
7. `card_payment_details`
8. `money_transfer_details`

## 5. people

| Column | Type | Required | Description |
|---|---|---:|---|
| `id` | UUID | Yes | Unique identifier |
| `name` | VARCHAR | Yes | Person name |
| `status` | Choice | Yes | `ACTIVE` / `ARCHIVED` |
| `created_at` | TIMESTAMP | Yes | Creation time |
| `updated_at` | TIMESTAMP | Yes | Last modification time |

Person position is derived from active `PERSON_BALANCE` effects:

`Position = SUM(active PERSON_BALANCE effects)`

Positive = Receivable, negative = Held, zero = Settled.

## 6. accounts

| Column | Type | Required | Description |
|---|---|---:|---|
| `id` | UUID | Yes | Unique identifier |
| `name` | VARCHAR | Yes | Account name |
| `account_type` | Choice | Yes | `BANK` / `CREDIT_CARD` |
| `status` | Choice | Yes | `ACTIVE` / `ARCHIVED` |
| `created_at` | TIMESTAMP | Yes | Creation time |
| `updated_at` | TIMESTAMP | Yes | Last modification time |

Each account has exactly one type and one corresponding detail record.

## 7. bank_account_details

| Column | Type | Required | Description |
|---|---|---:|---|
| `account_id` | UUID | Yes | PK and FK to `accounts.id` |
| `opening_balance` | NUMERIC(19,2) | Yes | Opening balance |

Current balance:

`Opening Balance + SUM(active BANK_BALANCE effects)`

Version 1 requires opening balance >= 0.

## 8. credit_card_details

| Column | Type | Required | Description |
|---|---|---:|---|
| `account_id` | UUID | Yes | PK and FK to `accounts.id` |
| `credit_limit` | NUMERIC(19,2) | Yes | Current credit limit |

Used credit:

`SUM(active CREDIT_USED effects)`

Available credit:

`Credit Limit - Used Credit`

Credit limit must be > 0.

## 9. transactions

| Column | Type | Required | Description |
|---|---|---:|---|
| `id` | UUID | Yes | Unique transaction ID |
| `date` | DATE | Yes | Financial event date |
| `person_id` | UUID | Conditional | FK to `people.id` |
| `account_id` | UUID | Conditional | FK to `accounts.id` |
| `transaction_type` | Choice | Yes | `EXPENSE` / `RECEIVED` / `CARD_PAYMENT` / `TRANSFER` |
| `amount` | NUMERIC(19,2) | Yes | Positive amount |
| `description` | VARCHAR/TEXT | Yes | Description |
| `status` | Choice | Yes | `ACTIVE` / `VOIDED` |
| `created_at` | TIMESTAMP | Yes | Creation time |
| `updated_at` | TIMESTAMP | Yes | Last modification time |

Transaction amount is always positive; financial direction is represented by effects.

### Expense
- Person required.
- Account required.
- Account must be BANK or CREDIT_CARD.
- Amount > 0.

Bank expense effects:
- Person `-amount`
- Bank `-amount`

Credit-card expense effects:
- Person `-amount`
- Credit card `+amount` as `CREDIT_USED`

### Received
- Person required.
- Account required.
- Account must be BANK.
- Amount > 0.

Effects:
- Person `+amount`
- Bank `+amount`

### Card Payment
- Person is NULL.
- Account is required and must be CREDIT_CARD.
- Amount > 0.
- Payment source is stored in `card_payment_details`.

Bank payment effects:
- Credit card `-amount` as `CREDIT_USED`
- Bank `-amount`

Cash payment effect:
- Credit card `-amount` as `CREDIT_USED`
- No bank effect.

## 10. transaction_effects

This is the core financial ledger.

| Column | Type | Required | Description |
|---|---|---:|---|
| `id` | UUID | Yes | Unique effect ID |
| `transaction_id` | UUID | Yes | FK to transaction |
| `person_id` | UUID | Conditional | FK to person |
| `account_id` | UUID | Conditional | FK to account |
| `effect_type` | Choice | Yes | `PERSON_BALANCE` / `BANK_BALANCE` / `CREDIT_USED` |
| `amount` | NUMERIC(19,2) | Yes | Signed change |
| `created_at` | TIMESTAMP | Yes | Creation time |

The reviewed design deliberately does **not** use a polymorphic `target_type` + `target_id`.

Instead, exactly one of `person_id` or `account_id` must be populated:

```text
(person_id IS NOT NULL AND account_id IS NULL)
OR
(person_id IS NULL AND account_id IS NOT NULL)
```

Effect rules:
- `PERSON_BALANCE` -> person target.
- `BANK_BALANCE` -> bank account target.
- `CREDIT_USED` -> credit-card target.

Cross-table account-type rules are enforced by Django/domain logic.

Effect amounts are signed.

## 11. Financial Calculations

Person:

`SUM(active PERSON_BALANCE effects)`

Bank:

`opening_balance + SUM(active BANK_BALANCE effects)`

Credit card:

`used_credit = SUM(active CREDIT_USED effects)`

`available_credit = credit_limit - used_credit`

## 12. card_payment_details

| Column | Type | Required | Description |
|---|---|---:|---|
| `transaction_id` | UUID | Yes | Unique FK to card-payment transaction |
| `payment_source_type` | Choice | Yes | `BANK_ACCOUNT` / `CASH` |
| `source_account_id` | UUID | Conditional | FK to bank account |

`transaction_id` is unique, creating a 1:1 relationship with `transactions`.

Rules:
- BANK_ACCOUNT -> `source_account_id` required and must be an active bank account.
- CASH -> `source_account_id` must be NULL.

Cash is not modeled as a full account in version 1.

## 12.5 money_transfer_details

| Column | Type | Required | Description |
|---|---|---:|---|
| `transaction_id` | UUID | Yes | Unique FK to the transfer transaction |
| `source_account_id` | UUID | Yes | Account/card providing funds |
| `destination_account_id` | UUID | Yes | Account/card receiving funds |

The source and destination must be different accounts. Both endpoints must belong to the same user and be active when a transfer is created or edited.

Transfer effects are generated as follows:

- Bank source: `BANK_BALANCE - amount`
- Credit-card source: `CREDIT_USED + amount`
- Bank destination: `BANK_BALANCE + amount`
- Credit-card destination: `CREDIT_USED - amount`

## 13. Relationships

```text
people
  |
  v
transactions
  |
  +--> transaction_effects --> people/accounts
  |
  +--> card_payment_details --> accounts

accounts
  |
  +--> bank_account_details
  |
  +--> credit_card_details
```

## 14. Foreign-Key and Deletion Policy

Financial history must not be destroyed accidentally.

Use protective deletion behavior for people/accounts referenced by financial history. The application uses archive/void semantics rather than destructive deletion.

## 15. Database Constraints

- Required names/status/type fields.
- `opening_balance >= 0`.
- `credit_limit > 0`.
- Transaction `amount > 0`.
- Valid choice values.
- Effect `amount != 0`.
- Exactly one effect target (`person_id` or `account_id`).
- Unique `account_id` in each account-detail table.
- Unique `transaction_id` in `card_payment_details`.

## 16. Application-Level Business Rules

Django/domain services enforce cross-table rules:

- RECEIVED -> bank account only.
- EXPENSE -> bank or credit card.
- CARD_PAYMENT -> credit card only.
- TRANSFER -> source and destination must be different active accounts.
- Bank card payment -> source account required and must be active bank.
- Cash card payment -> source account NULL.
- Archived people/accounts cannot be used for new transactions.
- Effect type must match target type.
- Financial operations must be atomic.

## 17. Index Strategy

Recommended indexes:

`transactions`:
- `person_id`
- `account_id`
- `date`
- `status`
- `transaction_type`

`transaction_effects`:
- `transaction_id`
- `person_id`
- `account_id`
- `effect_type`

`people`:
- `status`

`accounts`:
- `account_type`
- `status`

Add composite indexes later only when actual query patterns justify them.

## 18. Atomic Operations

### Create
```text
BEGIN
  Validate
  Create transaction
  Generate effects
  Create effects
COMMIT
```

### Edit
```text
BEGIN
  Validate new data
  Replace old effects
  Update transaction
  Generate new effects
COMMIT
```

### Void
```text
BEGIN
  Set transaction status = VOIDED
COMMIT
```

Voided transactions remain historical records but are excluded from current financial calculations.

## 19. Final Schema

```text
PEOPLE
├── id
├── name
├── status
├── created_at
└── updated_at

ACCOUNTS
├── id
├── name
├── account_type
├── status
├── created_at
└── updated_at

BANK_ACCOUNT_DETAILS
├── account_id
└── opening_balance

CREDIT_CARD_DETAILS
├── account_id
└── credit_limit

TRANSACTIONS
├── id
├── date
├── person_id
├── account_id
├── transaction_type
├── amount
├── description
├── status
├── created_at
└── updated_at

TRANSACTION_EFFECTS
├── id
├── transaction_id
├── person_id
├── account_id
├── effect_type
├── amount
└── created_at

CARD_PAYMENT_DETAILS
├── transaction_id
├── payment_source_type
└── source_account_id

MONEY_TRANSFER_DETAILS
├── transaction_id
├── source_account_id
└── destination_account_id
```

## 20. Implementation Boundary

This document defines the database design. Actual Django model implementation will be performed during the development phase.

Implementation will use:
- Django models
- `TextChoices`
- `ForeignKey`
- `OneToOneField`
- `DecimalField`
- `CheckConstraint`
- `UniqueConstraint`
- database indexes
- Django migrations
- `transaction.atomic()`
- application/service-layer financial logic

No production database schema should be created until these implementation decisions are reviewed against this document.
