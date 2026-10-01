# 07 — Architecture

## 1. Purpose

This document defines the application architecture for the Family Expense Tracker.

The architecture is designed for:

- A beginner-friendly development experience
- Clear separation of responsibilities
- Strong financial integrity
- Easy testing and maintenance
- Straightforward deployment
- Future expansion toward APIs, React, and AI features

The selected architecture is a **Django modular monolith** using Django Templates and PostgreSQL.

---

# 2. Confirmed Technology Stack

| Layer | Technology |
|---|---|
| Programming Language | Python 3 |
| Backend Framework | Django |
| Database | PostgreSQL |
| ORM | Django ORM |
| Frontend | Django Templates |
| Markup | HTML |
| Styling | CSS |
| Client-side Logic | JavaScript |
| API Layer | Django REST Framework when required |
| Validation | Django Forms + DRF Serializers |
| Money | Python `Decimal` |
| Database Money | PostgreSQL `NUMERIC(19,2)` |
| Testing | pytest + pytest-django |
| Version Control | Git + GitHub |
| IDE | VS Code |
| AI Coding Assistant | GitHub Copilot |
| Environment Configuration | `.env` variables |
| Local/Optional Containerization | Docker |
| Production Database | PostgreSQL |

---

# 3. High-Level Architecture

```text
                         FAMILY EXPENSE TRACKER

                              Web Browser
                                   |
                         HTML + CSS + JavaScript
                                   |
                                   v
                           Django Templates
                                   |
                                   v
                           Django Application
                                   |
             +---------------------+---------------------+
             |                     |                     |
             v                     v                     v
          Views /             Application           Forms /
        Controllers            Services             Validation
             |                     |                     |
             +---------------------+---------------------+
                                   |
                                   v
                              Django ORM
                                   |
                                   v
                              PostgreSQL
```

The browser is responsible for presentation and user interaction.

Django is responsible for HTTP handling, validation, business operations, authentication when introduced, and database access.

PostgreSQL is responsible for persistent relational data and database-level integrity.

---

# 4. Architectural Style

The application will use a **modular monolith**.

A modular monolith means:

- One deployable Django application
- One PostgreSQL database
- Multiple logically separated Django applications/modules
- Clear boundaries between business domains
- No unnecessary distributed services

This is preferred over microservices for the current project because the application is small enough to operate as one system and does not require independent service scaling.

---

# 5. Why a Modular Monolith?

The application contains several closely related domains:

```text
People
Accounts
Transactions
Dashboard
Settings
```

These domains need frequent interaction.

For example:

```text
Expense
  |
  +--> Person
  |
  +--> Account
  |
  +--> Transaction Effects
  |
  +--> Dashboard calculations
```

Splitting these into separate network services would introduce unnecessary complexity.

The modular monolith gives the project:

- Simpler development
- Easier debugging
- Easier local setup
- Easier deployment
- Fewer network failure points
- Strong database transactions
- Clear internal boundaries

Microservices may be considered only if future requirements justify them.

---

# 6. Django Project Structure

The conceptual project structure will be:

```text
family_expense_tracker/
│
├── config/
│   ├── settings/
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
├── apps/
│   ├── people/
│   ├── accounts/
│   ├── transactions/
│   ├── dashboard/
│   └── core/
│
├── templates/
├── static/
├── media/
├── tests/
│
├── manage.py
├── requirements.txt
├── .env
├── .env.example
└── README.md
```

The exact filesystem organization may be refined during implementation.

---

# 7. Django Application Modules

## 7.1 `people`

Responsible for:

- Creating people
- Updating people
- Archiving people
- Restoring people
- Viewing people
- Calculating/displaying person financial position
- Person transaction history

The module does not independently modify account balances.

---

## 7.2 `accounts`

Responsible for:

- Creating bank accounts
- Creating credit cards
- Updating account information
- Updating credit limits
- Archiving accounts
- Restoring accounts
- Viewing account details
- Account transaction history

The module does not directly perform transaction effects.

Financial changes are created through transaction operations.

---

## 7.3 `transactions`

This is the central financial module.

Responsible for:

- Expenses
- Received transactions
- Card payments
- Transaction effects
- Transaction filtering
- Transaction search
- Transaction editing
- Transaction voiding
- Financial calculations related to transaction effects

This module contains the core financial business logic.

---

## 7.4 `dashboard`

Responsible for presenting aggregated information:

- Bank/cash balance
- Credit available
- Credit used
- Financial accounts
- Family positions
- Recent transactions

The dashboard should consume financial services rather than duplicate financial calculation rules.

---

## 7.5 `core`

Contains shared functionality that does not belong to one business domain.

Potential responsibilities:

- Base model utilities
- Shared constants
- Common error handling
- Common decorators/utilities
- Shared validation helpers
- Application-wide configuration helpers

The `core` module must not become a dumping ground for unrelated business logic.

---

# 8. Layered Application Architecture

Within the Django application, responsibilities will be separated into layers.

```text
Browser
   |
   v
URLs
   |
   v
Views
   |
   v
Forms / Validation
   |
   v
Services
   |
   v
Models / Django ORM
   |
   v
PostgreSQL
```

---

# 9. URL Layer

Django URL configuration maps incoming HTTP requests to application views.

Example conceptual routes:

```text
/people/
/people/<id>/

/accounts/
/accounts/<id>/

/transactions/
/transactions/<id>/

/dashboard/

/settings/
```

URLs should describe resources and user-facing actions clearly.

---

# 10. View Layer

Views handle HTTP concerns.

A view is responsible for:

- Receiving the request
- Reading request parameters
- Calling validation
- Calling the appropriate service
- Preparing a response
- Rendering a template or returning an API response

Views should **not** contain complex financial calculations.

Avoid:

```text
View
 ├── Calculate person balance
 ├── Update bank balance
 ├── Calculate credit usage
 └── Create effects
```

Prefer:

```text
View
  |
  v
Transaction Service
  |
  v
Financial Logic
```

This makes business rules reusable and testable.

---

# 11. Service Layer

The service layer contains business operations.

Conceptual services:

```text
TransactionService
├── create_expense()
├── create_received()
├── create_card_payment()
├── update_transaction()
└── void_transaction()

PersonService
├── create_person()
├── update_person()
├── archive_person()
└── restore_person()

AccountService
├── create_account()
├── update_account()
├── archive_account()
└── restore_account()

FinancialCalculationService
├── get_person_position()
├── get_bank_balance()
├── get_credit_used()
└── get_available_credit()
```

The exact implementation names may be refined during development.

---

# 12. Financial Service Responsibility

Financial operations must be centralized.

For example, creating an expense should follow:

```text
User
  |
  v
Expense View
  |
  v
Transaction Service
  |
  +--> Validate Person
  |
  +--> Validate Account
  |
  +--> Create Transaction
  |
  +--> Generate Effects
  |
  v
PostgreSQL Transaction
```

The browser must never be trusted as the authority for financial calculations.

For example, the frontend may display:

```text
Available credit after payment: ₹90,000
```

but Django must independently calculate and validate the result.

---

# 13. Model Layer

Django models represent persistent database structures.

The models will correspond to the database design:

```text
Person
Account
BankAccountDetails
CreditCardDetails
Transaction
TransactionEffect
CardPaymentDetails
```

Models are responsible for:

- Database structure
- Relationships
- Basic model-level validation
- Constraints
- Database indexes
- Django ORM access

Complex financial workflows should remain in service-layer operations rather than being scattered throughout models.

---

# 14. Database Layer

PostgreSQL is the authoritative persistence layer.

Django ORM will be used for normal application database operations.

The application will use database transactions for multi-step financial operations.

Conceptually:

```text
transaction.atomic()
       |
       +-- Validate
       +-- Create/update transaction
       +-- Create/update effects
       +-- Commit
```

Failure results in rollback.

---

# 15. Frontend Architecture

Version 1 will use Django Templates rather than React.

Frontend technologies:

```text
HTML
CSS
JavaScript
Django Templates
```

This keeps the first implementation focused while allowing the user to learn fundamental web development.

The frontend must remain responsive for:

- Desktop
- Tablet
- Mobile

The desktop and mobile layouts will use the same underlying business concepts but can have different presentation structures.

---

# 16. Frontend Organization

Conceptual structure:

```text
templates/
├── base.html
├── dashboard/
├── people/
├── accounts/
├── transactions/
├── settings/
└── components/

static/
├── css/
├── js/
└── images/
```

Reusable interface elements should be implemented as Django template partials/components where appropriate.

Examples:

- Navigation
- Cards
- Tables
- Forms
- Modals/drawers
- Status badges
- Empty states
- Confirmation dialogs

---

# 17. JavaScript Responsibility

JavaScript is used for client-side interaction such as:

- Opening drawers
- Mobile navigation
- Form interactions
- Dynamic field visibility
- Search
- Filters
- Confirmation dialogs
- Preview calculations
- Asynchronous requests when useful

JavaScript must not become the authoritative financial calculation layer.

For example, a card payment preview may be calculated client-side for convenience, but Django must validate the actual operation on submission.

---

# 18. Forms and Validation

Django Forms will handle server-side form validation for HTML-based interactions.

Validation should include:

- Required fields
- Data types
- Amount validity
- Date validity
- Account/person selection
- Transaction-specific fields

Cross-table financial rules will be enforced by application services.

Example:

```text
Received
   |
   v
Validate account
   |
   +--> Is account active?
   +--> Is account a bank account?
   |
   v
Create transaction
```

---

# 19. Financial Transaction Flow

## Expense

```text
User submits expense
        |
        v
Django View
        |
        v
Transaction Service
        |
        +--> Validate person
        +--> Validate account
        +--> Validate amount
        |
        +--> Create Transaction
        |
        +--> Generate Effects
        |
        v
PostgreSQL COMMIT
```

## Received

```text
User submits received transaction
        |
        v
Validate person
        |
        v
Validate bank account
        |
        v
Create transaction
        |
        v
Create person + bank effects
        |
        v
COMMIT
```

## Card Payment

```text
User submits card payment
        |
        v
Validate credit card
        |
        +--> Bank payment?
        |      |
        |      +--> Validate active bank account
        |
        +--> Cash payment?
        |
        v
Create transaction
        |
        v
Create credit-card effect
        |
        +--> Bank effect if bank-funded
        |
        v
COMMIT
```

---

# 20. Transaction Editing

Editing must use one atomic operation.

```text
BEGIN
   |
   +--> Validate new data
   |
   +--> Replace old effects
   |
   +--> Update transaction
   |
   +--> Generate new effects
   |
COMMIT
```

If any step fails:

```text
ROLLBACK
```

The database remains in the previous valid state.

---

# 21. Transaction Voiding

Voiding does not physically delete the transaction.

```text
ACTIVE
   |
   v
VOIDED
```

Current financial calculations only include effects belonging to active transactions.

Historical views may display both active and voided transactions.

---

# 22. Balance Calculation Architecture

Balances are derived through dedicated financial calculation logic.

```text
PostgreSQL
    |
    v
Transaction Effects
    |
    +--> Person Position
    |
    +--> Bank Balance
    |
    +--> Credit Used
             |
             v
       Credit Available
```

The dashboard consumes these calculations.

The same financial calculation logic should be reused across:

- Dashboard
- People details
- Account details
- Transaction details
- APIs

This prevents different screens from calculating different values.

---

# 23. API Architecture

Version 1 primarily uses Django server-rendered pages.

Django REST Framework can be introduced for structured API endpoints when needed.

Future architecture:

```text
React + TypeScript
        |
        v
Django REST Framework
        |
        v
Application Services
        |
        v
Django ORM
        |
        v
PostgreSQL
```

The API should call the same service layer used by HTML views.

This prevents duplicated business logic.

---

# 24. Future React Migration

React is intentionally not part of version 1.

If introduced later:

```text
Current:

Django Templates
      |
Django Views
      |
Services
      |
PostgreSQL
```

can evolve into:

```text
Future:

React + TypeScript
      |
REST API
      |
Django REST Framework
      |
Services
      |
PostgreSQL
```

The financial service layer and database design can remain largely unchanged.

---

# 25. Authentication and User Scope

Version 1 is planned as a single-user application unless requirements change.

Authentication architecture can later use Django's authentication system.

Future multi-user architecture would add:

```text
User
  |
  +--> People
  +--> Accounts
  +--> Transactions
```

and enforce ownership boundaries at the service/API level.

Multi-user support is not required for the initial implementation.

---

# 26. Configuration

Sensitive or environment-specific settings must not be hard-coded.

Examples:

```text
SECRET_KEY
DATABASE_URL
DEBUG
ALLOWED_HOSTS
CSRF_TRUSTED_ORIGINS
```

A `.env` file will be used locally.

A `.env.example` file will document required configuration without containing real secrets.

Production secrets must be supplied through the hosting environment.

---

# 27. Security Architecture

Security will be documented in detail in `09-security.md`.

The architecture will follow these principles:

- Server-side validation
- Django CSRF protection
- Secure session handling
- Environment-based secrets
- ORM parameterization
- No raw SQL unless justified
- Authentication when required
- Authorization before financial operations
- Secure production settings
- No sensitive secrets committed to Git

---

# 28. Testing Architecture

Testing will exist at multiple levels.

```text
Unit Tests
   |
   +--> Financial calculations
   +--> Validation
   +--> Service logic

Integration Tests
   |
   +--> Django ORM
   +--> PostgreSQL
   +--> Transaction operations

Functional/UI Tests
   |
   +--> Important user workflows
```

Most financial business rules should be covered by automated tests before deployment.

---

# 29. Error Handling

The application should use consistent error handling.

For HTML pages:

- Display user-friendly validation messages.
- Preserve valid form input when possible.
- Avoid exposing internal errors.

For future APIs:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The transaction could not be created.",
    "details": [
      {
        "field": "amount",
        "message": "Amount must be greater than zero."
      }
    ]
  }
}
```

Internal exceptions should be logged without exposing sensitive implementation details to users.

---

# 30. Logging

Version 1 will use basic structured application logging.

Logs should help diagnose:

- Application errors
- Failed financial operations
- Database failures
- Authentication/security events when authentication is introduced

Sensitive financial or authentication information should not be unnecessarily written to logs.

---

# 31. Background Processing

No background job system is required initially.

The application does not currently need:

- Celery
- Redis
- Kafka
- Message queues

These can be introduced later if a real requirement appears.

---

# 32. Caching

No application-wide caching system is required initially.

Financial data is relatively small and correctness is more important than premature caching.

If caching is introduced later, it must never become the authoritative source for financial balances.

PostgreSQL remains authoritative.

---

# 33. Microservices Decision

Microservices are explicitly out of scope for version 1.

The system will remain:

```text
One Django Application
        +
One PostgreSQL Database
```

This is sufficient for the expected scale and makes development substantially easier.

---

# 34. Deployment Architecture

The deployment architecture will be defined in detail in `10-deployment.md`.

The expected production structure is:

```text
User Browser
     |
     v
Web Server / Hosting Platform
     |
     v
Django Application
     |
     v
PostgreSQL
```

The exact hosting provider will be selected later based on current Python/Django/PostgreSQL support, limits, and deployment requirements.

The application should remain portable and must not depend on one provider's proprietary features.

---

# 35. Development Environment

Recommended local development environment:

```text
Windows
   |
VS Code
   |
Python
   |
Django
   |
PostgreSQL
   |
Git + GitHub
```

Docker is optional for local infrastructure and may be used to simplify PostgreSQL setup.

The project should remain understandable and runnable without requiring a large infrastructure stack.

---

# 36. Git Architecture

Development will use Git.

Recommended branches:

```text
main
  |
  +-- feature/people
  +-- feature/accounts
  +-- feature/transactions
  +-- feature/dashboard
```

Feature branches should contain focused changes.

Commits should describe what changed.

Examples:

```text
feat: add people management
feat: implement bank accounts
feat: add expense transaction flow
fix: prevent archived accounts from new transactions
test: add card payment service tests
docs: update database design
```

---

# 37. Development Principles

The implementation should follow these principles:

1. Do not duplicate business logic.
2. Keep financial calculations on the server.
3. Keep database writes atomic.
4. Do not store redundant authoritative balances.
5. Do not delete financial history.
6. Validate at the server even when the frontend validates.
7. Prefer simple architecture over unnecessary infrastructure.
8. Write tests around financial rules.
9. Keep documentation synchronized with implementation.
10. Make changes incrementally and verify each feature before moving on.

---

# 38. Architectural Decision Summary

The final architecture is:

```text
Frontend
HTML + CSS + JavaScript
        |
Django Templates
        |
Django Views
        |
Forms / Validation
        |
Application Services
        |
Django ORM
        |
PostgreSQL
```

Business modules:

```text
people
accounts
transactions
dashboard
core
```

The most important architectural rule is:

```text
HTTP/UI concerns
        !=
Financial business logic
        !=
Database persistence
```

Each responsibility should remain in its appropriate layer.

---

# 39. Future Evolution

The architecture intentionally allows future expansion.

Potential future evolution:

```text
Version 1
Django + Templates + PostgreSQL
        |
        v
Version 2
Django REST Framework
        |
        v
React + TypeScript
        |
        v
Version 3
AI/ML features using Python
```

Potential future AI features could be added without redesigning the core financial database.

Examples might include:

- Expense categorization
- Spending summaries
- Natural-language financial queries
- Financial insights

These are future possibilities and are not part of the current financial core.

---

# 40. Architecture Status

The architecture is considered complete for the current requirements.

Confirmed decisions:

- Django
- PostgreSQL
- Django ORM
- Django Templates for version 1
- HTML/CSS/JavaScript
- Modular monolith
- Domain-based Django apps
- Service layer for financial operations
- Server-side financial calculations
- Atomic financial operations
- No microservices
- No Redis/Celery initially
- React deferred to a future version
- AI features deferred until the core application is stable
