# 08 — API Specification

## 1. Purpose

This document defines the backend API contracts, request/response structures, authentication requirements, validation rules, financial operations, and security behavior for the Family Expense Tracker.

The API specification is designed to support:

* The initial Django Templates frontend.
* Future React + TypeScript frontend integration.
* Centralized business logic in the Django application service layer.
* PostgreSQL as the authoritative data store.
* Authenticated access to each user's financial data.

The API must not duplicate financial business logic in the frontend.

---

# 2. API Architecture

The application follows:

```text
Browser
   ↓
HTTPS / TLS
   ↓
Django
   ↓
Views / API Layer
   ↓
Forms / Serializers / Validation
   ↓
Application Services
   ↓
Django ORM
   ↓
PostgreSQL
```

The API layer is responsible for:

* Receiving requests.
* Authenticating the user.
* Authorizing access.
* Validating input.
* Calling application services.
* Returning appropriate responses.

Financial rules remain in the application service layer.

---

# 3. API Version

The initial API namespace is:

```text
/api/
```

A versioned namespace may be introduced when a public or long-lived API is required.

The initial project does not require multiple API versions.

---

# 4. Authentication

The application includes a user login and signup portal.

## 4.1 Authentication Flow

```text
User
 ↓
Signup
 ↓
Account created
 ↓
Login
 ↓
Authenticated session
 ↓
Protected application
```

Unauthenticated users may access authentication-related pages and endpoints.

Financial application data requires authentication.

---

# 5. Authentication Endpoints

## 5.1 Signup

```http
POST /api/auth/signup/
```

Request:

```json
{
  "name": "Shoaib",
  "email": "user@example.com",
  "password": "password"
}
```

The backend must:

1. Validate the submitted information.
2. Validate email uniqueness.
3. Validate password requirements.
4. Hash the password using Django's password-hashing system.
5. Create the user account.
6. Never store the plaintext password.

The response must not return the user's password.

---

## 5.2 Login

```http
POST /api/auth/login/
```

Request:

```json
{
  "email": "user@example.com",
  "password": "password"
}
```

A successful login establishes an authenticated session.

The application uses secure server-managed authentication rather than exposing raw authentication credentials to application business endpoints.

---

## 5.3 Logout

```http
POST /api/auth/logout/
```

The server invalidates the authenticated session.

---

## 5.4 Current User

```http
GET /api/auth/me/
```

Example response:

```json
{
  "id": "uuid",
  "name": "Shoaib",
  "email": "user@example.com"
}
```

This endpoint allows the frontend to determine the currently authenticated user.

---

# 6. Authentication Requirements

Protected endpoints require an authenticated user.

Unauthenticated access must return an appropriate unauthorized response.

Example:

```json
{
  "error": {
    "code": "AUTHENTICATION_REQUIRED",
    "message": "Authentication is required."
  }
}
```

Authentication must be checked before accessing user-owned financial information.

---

# 7. Authorization and Data Ownership

Every financial record must belong to the authenticated application user through the application's ownership model.

A user must only be able to access their own:

* People.
* Accounts.
* Transactions.
* Transaction effects.
* Card payment details.
* Dashboard information.

The client must never be trusted to determine ownership.

For example, changing:

```text
/persons/{id}/
```

to another UUID must not allow access to another user's data.

Authorization must be enforced server-side.

---

# 8. People API

## 8.1 List People

```http
GET /api/people/
```

Returns people belonging to the authenticated user.

---

## 8.2 Create Person

```http
POST /api/people/
```

Request:

```json
{
  "name": "Mom"
}
```

---

## 8.3 Retrieve Person

```http
GET /api/people/{id}/
```

The response includes the person's current financial position.

---

## 8.4 Update Person

```http
PATCH /api/people/{id}/
```

Example:

```json
{
  "name": "Mom"
}
```

---

## 8.5 Archive Person

```http
POST /api/people/{id}/archive/
```

Archived people remain in historical records but cannot be selected for new transactions.

---

## 8.6 Restore Person

```http
POST /api/people/{id}/restore/
```

Restoration makes the person available for new transactions again.

---

## 8.7 Person Transactions

```http
GET /api/people/{id}/transactions/
```

Returns transactions associated with the person.

---

## 8.8 Person Position

```http
GET /api/people/{id}/position/
```

The position is calculated from active financial effects.

```text
Person Position =
SUM(active PERSON_BALANCE effects)
```

---

# 9. Accounts API

Accounts consist of:

* Bank accounts.
* Credit cards.

## 9.1 List Accounts

```http
GET /api/accounts/
```

Optional filtering:

```text
/api/accounts/?type=BANK
/api/accounts/?type=CREDIT_CARD
```

---

## 9.2 Create Bank Account

```http
POST /api/accounts/
```

Example:

```json
{
  "name": "HDFC Bank",
  "account_type": "BANK",
  "opening_balance": "42500.00"
}
```

---

## 9.3 Create Credit Card

```http
POST /api/accounts/
```

Example:

```json
{
  "name": "HDFC Credit Card",
  "account_type": "CREDIT_CARD",
  "credit_limit": "100000.00"
}
```

---

## 9.4 Retrieve Account

```http
GET /api/accounts/{id}/
```

The response includes the appropriate derived financial values.

For a bank:

```text
Opening Balance
Current Balance
```

For a credit card:

```text
Credit Limit
Used Credit
Available Credit
```

---

## 9.5 Update Account

```http
PATCH /api/accounts/{id}/
```

The backend must preserve historical transactions.

Changing a credit limit does not modify historical transactions.

---

## 9.6 Archive Account

```http
POST /api/accounts/{id}/archive/
```

Archived accounts remain in historical records but cannot be selected for new financial transactions.

---

## 9.7 Restore Account

```http
POST /api/accounts/{id}/restore/
```

---

## 9.8 Account Transactions

```http
GET /api/accounts/{id}/transactions/
```

Returns transactions associated with the account.

---

# 10. Transactions API

Transactions represent the user-facing financial actions.

Supported types:

```text
EXPENSE
RECEIVED
CARD_PAYMENT
```

Amounts are always positive at the transaction level.

The direction of financial movement is represented by generated transaction effects.

---

# 11. List Transactions

```http
GET /api/transactions/
```

Default ordering:

```text
Newest first
```

Supported filters:

```text
person_id
account_id
account_type
transaction_type
date_from
date_to
amount_min
amount_max
search
status
```

Example:

```text
/api/transactions/?person_id={id}
/api/transactions/?transaction_type=EXPENSE
/api/transactions/?date_from=2026-09-01&date_to=2026-09-30
/api/transactions/?search=groceries
```

Filters may be combined.

---

# 12. Create Expense

```http
POST /api/transactions/
```

Example:

```json
{
  "transaction_type": "EXPENSE",
  "person_id": "person-uuid",
  "account_id": "account-uuid",
  "amount": "5000.00",
  "date": "2026-09-23",
  "description": "Groceries"
}
```

The backend determines the financial effects.

### Bank Expense

```text
Person        - ₹5,000
Bank Account  - ₹5,000
```

### Credit Card Expense

```text
Person        - ₹5,000
Credit Used   + ₹5,000
```

The client does not submit `TransactionEffect` records directly.

---

# 13. Create Received Transaction

```http
POST /api/transactions/
```

Example:

```json
{
  "transaction_type": "RECEIVED",
  "person_id": "person-uuid",
  "account_id": "bank-uuid",
  "amount": "3000.00",
  "date": "2026-09-23",
  "description": "Money received"
}
```

Backend effects:

```text
Person        + ₹3,000
Bank Account  + ₹3,000
```

The UI terminology remains **Received**, not Income.

---

# 14. Card Payment API

Card payment is a separate financial action.

```http
POST /api/card-payments/
```

Example bank-funded payment:

```json
{
  "credit_card_account_id": "card-uuid",
  "amount": "10000.00",
  "payment_source_type": "BANK_ACCOUNT",
  "source_account_id": "bank-uuid",
  "date": "2026-09-23"
}
```

Example cash payment:

```json
{
  "credit_card_account_id": "card-uuid",
  "amount": "10000.00",
  "payment_source_type": "CASH",
  "date": "2026-09-23"
}
```

---

# 15. Card Payment Effects

## Bank-funded payment

```text
Bank Account       - ₹10,000
Credit Used        - ₹10,000
Available Credit   + ₹10,000
```

## Cash payment

```text
Credit Used        - ₹10,000
Available Credit   + ₹10,000
```

Cash payment does not create a bank balance effect.

A card payment is not treated as a normal expense.

---


# 15.5 Money Transfers

Money transfers move funds between two owned financial accounts without being treated as income or an expense.

```http
POST /api/money-transfers/
```

Request:

```json
{
  "date": "2026-09-25",
  "source_account_id": "uuid",
  "destination_account_id": "uuid",
  "amount": "1000.00",
  "description": "Move savings"
}
```

The service creates one `TRANSFER` transaction and two account effects. Source and destination must be different active accounts.

# 16. Transaction Details

```http
GET /api/transactions/{id}/
```

The response should provide:

* Person.
* Transaction type.
* Amount.
* Date.
* Description.
* Account/payment source.
* Financial effects.
* Status.

Example structure:

```json
{
  "id": "uuid",
  "person": {},
  "transaction_type": "EXPENSE",
  "amount": "5000.00",
  "date": "2026-09-23",
  "description": "Groceries",
  "account": {},
  "financial_effects": [],
  "status": "ACTIVE"
}
```

---

# 17. Update Transaction

```http
PATCH /api/transactions/{id}/
```

The frontend submits the new transaction information.

The application service must:

1. Validate the request.
2. Validate ownership.
3. Validate referenced people/accounts.
4. Reverse the old active financial effects.
5. Apply the new transaction information.
6. Generate the new financial effects.
7. Commit the operation atomically.

The complete operation must succeed or fail as one database transaction.

---

# 18. Void Transaction

```http
POST /api/transactions/{id}/void/
```

Voiding does not physically delete the transaction.

The transaction status becomes:

```text
VOIDED
```

Its effects no longer contribute to current financial calculations.

Historical information remains available.

The operation must be atomic.

---

# 19. Financial Calculation Endpoints

Financial values are derived from authoritative transaction/effect data.

## Person Position

```text
SUM(active PERSON_BALANCE effects)
```

## Bank Balance

```text
Opening Balance
+
SUM(active BANK_BALANCE effects)
```

## Credit Used

```text
SUM(active CREDIT_USED effects)
```

## Available Credit

```text
Credit Limit - Credit Used
```

The frontend must not independently calculate authoritative balances.

---

# 20. Dashboard API

```http
GET /api/dashboard/
```

The dashboard response may contain:

```json
{
  "greeting": "Good morning, Shoaib",
  "financial_overview": {
    "bank_balance": "42500.00",
    "credit_available": "85000.00",
    "credit_used": "15000.00"
  },
  "accounts": [],
  "family_positions": [],
  "recent_transactions": []
}
```

The three financial overview values remain separate.

Available credit must not be combined with bank/cash balance.

---

# 21. Validation Rules

The backend must enforce business rules independently of frontend validation.

## People

* Name is required.
* Archived people cannot be selected for new transactions.
* Historical transactions remain associated with archived people.

## Accounts

* Account name is required.
* Account type must be supported.
* Bank opening balance must satisfy the database/business validation rules.
* Credit limit must be greater than zero.
* Archived accounts cannot be selected for new transactions.
* Historical transactions remain associated with archived accounts.

## Transactions

* Amount must be greater than zero.
* Date is required.
* Transaction type must be supported.
* Required person/account relationships must be valid.
* Referenced records must belong to the authenticated user.
* Voided transactions cannot be treated as active financial records.

## Card Payments

* Credit card must be a credit-card account.
* Amount must be greater than zero.
* Payment source must be BANK_ACCOUNT or CASH.
* BANK_ACCOUNT requires a bank account.
* CASH must not reference a bank account.

---

# 22. Error Handling

API errors use a consistent structure.

Example:

```json
{
  "error": {
    "code": "INVALID_AMOUNT",
    "message": "Amount must be greater than zero."
  }
}
```

Possible categories include:

```text
AUTHENTICATION_REQUIRED
PERMISSION_DENIED
NOT_FOUND
VALIDATION_ERROR
INVALID_AMOUNT
INVALID_ACCOUNT_TYPE
INVALID_PAYMENT_SOURCE
ARCHIVED_PERSON
ARCHIVED_ACCOUNT
TRANSACTION_ALREADY_VOIDED
INVALID_TRANSACTION_STATE
CONFLICT
```

Exact error codes may expand as implementation develops.

---

# 23. HTTP Status Codes

The API uses standard HTTP status semantics.

```text
200 OK
201 Created
400 Bad Request
401 Unauthorized
403 Forbidden
404 Not Found
409 Conflict
422 Unprocessable Entity
500 Internal Server Error
```

Only status codes required by the implemented behavior should be used.

---

# 24. Security Requirements

All production API communication must use HTTPS/TLS.

The application must implement:

* HTTPS-only communication.
* HTTP to HTTPS redirection.
* Secure session cookies.
* HttpOnly cookies.
* Appropriate SameSite cookie settings.
* CSRF protection.
* Authentication on protected endpoints.
* Server-side authorization.
* Input validation.
* Ownership validation.
* Secure error responses.
* Security headers.
* Rate limiting where appropriate.
* Secure secrets management.
* Database access restrictions.
* Encrypted database connections where supported.
* Security-conscious logging.

PostgreSQL must not be directly exposed to the public internet.

---

# 25. End-to-End Encryption Clarification

The application uses HTTPS/TLS to encrypt data while it travels between the user's browser and the server.

This is transport encryption and must not be described as strict cryptographic end-to-end encryption.

The Django server needs access to financial data because it performs:

* Financial calculations.
* Transaction validation.
* Transaction effect generation.
* Dashboard aggregation.
* Authorization.
* Search and filtering.

Therefore, strict client-only end-to-end encryption of all financial fields is not part of Version 1.

A future client-side encryption architecture can be considered separately if the requirement becomes that the cloud server itself must not be able to read financial data.

---

# 26. Atomic Financial Operations

All financial operations must use database transactions.

Examples:

```text
Create Expense
    ↓
Validate
    ↓
Create Transaction
    ↓
Create Effects
    ↓
Commit
```

If any step fails:

```text
ROLLBACK
```

The same principle applies to:

* Received transactions.
* Credit-card expenses.
* Card payments.
* Transaction edits.
* Transaction voiding.

This prevents incomplete financial operations.

---

# 27. Transaction Effects

Clients must not directly create or modify financial effects.

The application service layer generates effects according to the transaction type.

Supported effect types:

```text
PERSON_BALANCE
BANK_BALANCE
CREDIT_USED
```

Effects must reference valid targets according to their effect type.

This preserves centralized financial logic.

---

# 28. API and UI Relationship

The API specification must remain aligned with the locked UI structure.

Examples:

```text
People page
    ↓
People API

Accounts page
    ↓
Accounts API

Transactions page
    ↓
Transactions API

Card Payment action
    ↓
Card Payment API

Dashboard
    ↓
Dashboard API
```

The UI must not introduce financial behavior that is absent from the backend rules.

---

# 29. Future React Compatibility

Version 1 uses Django Templates.

The application architecture must allow a future frontend such as:

```text
React + TypeScript
        ↓
Django REST Framework
        ↓
Application Services
        ↓
Django ORM
        ↓
PostgreSQL
```

The application service layer remains responsible for financial business rules.

Therefore, introducing React later should not require rewriting the financial domain logic.

---

# 30. Out of Scope for Version 1

The API does not introduce functionality that has not been approved.

The following are outside the current specification:

* Bank account synchronization.
* Automatic bank transaction imports.
* Recurring transactions.
* Budgets.
* Categories.
* Monthly credit-card statements.
* Multi-currency accounting.
* AI financial recommendations.
* Notifications.
* Microservices.
* GraphQL.
* Public third-party API access.

These may be considered as future requirements separately.

---

# 31. API Design Principle

The central principle is:

> The frontend requests financial actions; the backend owns the financial rules.

For example:

```text
Frontend:
"Create ₹5,000 expense for Mom using HDFC Bank."

Backend:
Validate
→ Create transaction
→ Generate financial effects
→ Commit atomically
→ Return result
```

The browser does not decide how the financial effects are calculated.

This keeps the financial system consistent, secure, and compatible with future frontend implementations.
