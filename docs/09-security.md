# 09 — Security Specification

## 1. Purpose

This document defines the security architecture and security requirements for the Family Expense Tracker.

The application handles private financial information, including:

* Family member financial positions.
* Bank account balances.
* Credit-card limits and usage.
* Expenses.
* Received money.
* Card payments.
* Transaction history.

Security must therefore be considered a core application requirement rather than a feature added after development.

---

# 2. Security Principles

The application follows these principles:

1. Authentication is required before accessing financial data.
2. Authorization is enforced on the server.
3. Users can access only their own financial records.
4. Financial business rules are enforced by the backend.
5. Financial operations are atomic.
6. Sensitive communication uses HTTPS/TLS.
7. Passwords are never stored in plaintext.
8. Secrets are never committed to source control.
9. PostgreSQL is not publicly exposed.
10. Historical financial records are preserved rather than physically deleted.
11. Security failures must fail safely.
12. The frontend must never be treated as a trusted security boundary.

---

# 3. Security Architecture

Production communication follows:

```text id="d0k0rm"
User Browser
     │
     │ HTTPS / TLS
     ▼
Internet
     │
     ▼
Reverse Proxy / Web Server
     │
     ▼
Django Application
     │
     ▼
Application Services
     │
     ▼
PostgreSQL
```

PostgreSQL should reside in a private network or otherwise be configured so that it is not directly accessible from the public internet.

---

# 4. Authentication

The application provides:

* Signup.
* Login.
* Logout.
* Current-user/session information.

Authentication is required for access to application financial data.

Unauthenticated users should only be able to access explicitly public/authentication functionality.

---

# 5. Password Security

User passwords must never be stored as plaintext.

Django's established password-hashing mechanisms should be used.

The application must not implement custom password hashing.

Passwords must not appear in:

* Database records.
* Application logs.
* API responses.
* Error messages.
* Debug output.
* Analytics data.

---

# 6. Signup Security

During signup:

```text id="h1q5nq"
User submits credentials
        ↓
Validate input
        ↓
Validate password requirements
        ↓
Validate email uniqueness
        ↓
Hash password
        ↓
Create account
```

The application must validate all signup data server-side even if the frontend performs the same validation.

Client-side validation is for usability, not security.

---

# 7. Login Security

Login must:

* Validate credentials server-side.
* Avoid revealing whether an account exists through unnecessarily detailed errors.
* Establish a secure authenticated session.
* Avoid returning sensitive credential information.
* Prevent session-related vulnerabilities.

Authentication failures should be handled consistently.

---

# 8. Session Security

The initial application uses Django's session-based authentication.

Production session configuration must use secure settings.

Important cookie properties include:

```text id="nq8z3b"
Secure
HttpOnly
SameSite
```

The session cookie must only be transmitted over HTTPS in production.

The application must protect against session fixation and ensure that authentication state is correctly established after login.

Logout must invalidate the authenticated session.

---

# 9. Authorization

Authentication determines:

> Who is the user?

Authorization determines:

> What data and operations is the user allowed to access?

Authorization must be enforced server-side.

The application must never rely on:

* Hidden frontend fields.
* Disabled buttons.
* JavaScript checks.
* URL obscurity.
* UUID secrecy.

For example:

```text id="l4qv1s"
User A
  ↓
/api/people/{User-A-person-id}/
  ↓
Allowed

User B
  ↓
/api/people/{User-A-person-id}/
  ↓
Denied
```

---

# 10. Data Ownership

All user-owned financial data must be associated with the authenticated user through the application's ownership model.

This applies to:

* People.
* Accounts.
* Transactions.
* Transaction effects.
* Card payment details.
* Dashboard calculations.

When retrieving or modifying data, the backend must scope the operation to the authenticated user.

The client must not be allowed to choose or override ownership.

---

# 11. Object-Level Authorization

Every object referenced through an identifier must be checked for ownership.

For example:

```text id="g3i6x8"
PATCH /api/transactions/{transaction_id}/
```

must verify:

```text id="8sj0ca"
Transaction exists
        ↓
Transaction belongs to current user
        ↓
Transaction is editable
        ↓
Perform operation
```

An attacker must not be able to access another user's data by changing an ID in the request.

---

# 12. CSRF Protection

Because the application uses Django sessions and browser-based authentication, CSRF protection must be enabled for state-changing requests.

Protected operations include:

* Signup where applicable.
* Login where applicable.
* Creating transactions.
* Editing transactions.
* Voiding transactions.
* Creating accounts.
* Updating accounts.
* Archiving records.
* Restoring records.
* Card payments.
* Other state-changing operations.

Django's CSRF protection should be used rather than implementing a custom CSRF mechanism.

---

# 13. HTTPS and TLS

Production traffic must use HTTPS.

The application must:

* Use a valid TLS certificate.
* Redirect HTTP to HTTPS.
* Avoid transmitting authenticated sessions over HTTP.
* Configure secure cookies.
* Enable HSTS after the production HTTPS configuration has been verified.

HTTPS protects information while it travels between the browser and application server.

---

# 14. HTTPS Is Not Strict E2EE

The application must distinguish between:

```text id="3pvb3m"
Transport Encryption
        ↓
HTTPS / TLS
```

and:

```text id="9qjpby"
Strict End-to-End Encryption
        ↓
Only endpoints possess decryption keys
```

Version 1 uses HTTPS/TLS but does not implement strict cryptographic end-to-end encryption for financial data.

This is intentional.

Django must be able to process financial information to:

* Validate transactions.
* Calculate balances.
* Generate transaction effects.
* Search transactions.
* Filter transactions.
* Produce dashboard values.
* Enforce financial business rules.

---

# 15. Future Client-Side Encryption

A future version may introduce client-side encryption if the requirement becomes:

> The cloud infrastructure must not be capable of reading the user's financial data.

Such a change would require a separate architecture for:

* Key generation.
* Key storage.
* Encryption/decryption.
* Multi-device synchronization.
* Account recovery.
* Search.
* Filtering.
* Financial calculations.

It must not be introduced casually because it would affect the current server-side financial architecture.

---

# 16. Input Validation

All externally supplied data must be validated on the server.

Examples include:

* Names.
* Email addresses.
* Passwords.
* Amounts.
* Dates.
* Descriptions.
* Account identifiers.
* Person identifiers.
* Transaction types.
* Payment source types.

The backend must not trust data merely because it originated from the application's own frontend.

---

# 17. Financial Input Rules

Financial amounts must use exact decimal arithmetic.

The application must use:

```text id="4ddf0a"
Python Decimal
        ↓
Django DecimalField
        ↓
PostgreSQL NUMERIC(19,2)
```

Floating-point arithmetic must not be used for authoritative monetary calculations.

Amounts must be:

* Numeric.
* Greater than zero where required.
* Represented with appropriate decimal precision.
* Validated before financial effects are generated.

---

# 18. Financial Integrity

Financial operations must be atomic.

For example:

```text id="z09l8g"
Create Expense
      ↓
Validate
      ↓
Create Transaction
      ↓
Generate Effects
      ↓
Commit
```

If any step fails:

```text id="7j9c1k"
ROLLBACK
```

The system must never intentionally leave behind a transaction without its required financial effects.

The same principle applies to:

* Received transactions.
* Credit-card expenses.
* Card payments.
* Transaction edits.
* Transaction voids.

---

# 19. Transaction Editing Security

Editing a transaction must not directly manipulate individual balances.

Instead:

```text id="x0x0ik"
Existing Transaction
       ↓
Validate ownership
       ↓
Reverse/rebuild existing effects
       ↓
Apply new transaction
       ↓
Generate new effects
       ↓
Commit atomically
```

The frontend cannot submit arbitrary financial effects.

This prevents users or malicious requests from directly manipulating balances.

---

# 20. Transaction Voiding

Transactions must not be physically deleted.

Voiding changes the transaction state:

```text id="ukw6hx"
ACTIVE
  ↓
VOIDED
```

Voided transactions remain available for historical purposes.

Current financial calculations exclude their effects.

This preserves financial history and reduces the risk of irreversible data loss.

---

# 21. Archived Records

People and accounts use archival rather than destructive deletion.

```text id="d5z8ba"
ACTIVE
  ↓
ARCHIVED
```

Archived records:

* Remain in historical data.
* Cannot be selected for new transactions.
* May be restored where supported.

---

# 22. Transaction Effects Protection

Transaction effects are internal financial records.

Clients must not directly create, modify, or delete them through ordinary application endpoints.

Supported effect types are:

```text id="3n6v0j"
PERSON_BALANCE
BANK_BALANCE
CREDIT_USED
```

The application service layer generates the appropriate effects from the requested financial operation.

---

# 23. Database Security

PostgreSQL must not be publicly exposed.

The production architecture should restrict database connectivity to trusted application infrastructure.

Database credentials must be stored securely.

The application should use the minimum database privileges required for normal operation.

Database administration credentials must not be embedded in source code.

---

# 24. Database Connection Security

Where supported by the production environment, the connection between Django and PostgreSQL should use encrypted transport.

Production database connections should be configured using secure connection settings appropriate to the hosting environment.

---

# 25. Secrets Management

Sensitive configuration must never be committed to Git.

Examples:

```text id="l5ixg4"
SECRET_KEY
DATABASE_URL
DATABASE_PASSWORD
EMAIL_PASSWORD
API_KEYS
OTHER_PRIVATE_CREDENTIALS
```

Local development may use environment variables loaded from a local `.env` file.

Production should use the hosting provider's secure environment-variable or secret-management mechanism.

The `.env` file must be excluded from version control.

---

# 26. Django Secret Key

Django's production `SECRET_KEY` must:

* Be unique to the production deployment.
* Not be committed to Git.
* Not be exposed to the frontend.
* Not be reused unnecessarily across environments.

Development and production environments should use separate secrets.

---

# 27. Debug Mode

Production must never run with:

```text id="0py2zj"
DEBUG = True
```

Production debug mode must be disabled.

Detailed internal errors must not be exposed to users.

---

# 28. Security Headers

Production should configure appropriate security-related HTTP headers.

The configuration should address areas such as:

* HTTPS enforcement.
* Content type sniffing.
* Clickjacking protection.
* Referrer behavior.
* Content security where appropriate.

The exact header configuration will be finalized during deployment.

---

# 29. CORS

Version 1 uses Django Templates and therefore does not require an unrestricted cross-origin API architecture.

CORS should remain restrictive.

The application must not use a configuration equivalent to:

```text
Allow every origin
```

for authenticated financial endpoints.

If React is introduced later, the approved frontend origin(s) can be explicitly configured.

---

# 30. Rate Limiting

Rate limiting should be applied to sensitive endpoints where appropriate.

Priority areas include:

* Signup.
* Login.
* Password-related operations if added.
* Other authentication endpoints.
* Potentially sensitive API operations.

Rate limiting is intended to reduce:

* Credential attacks.
* Automated abuse.
* Excessive requests.
* Resource exhaustion.

Exact limits will be established during implementation and deployment testing.

---

# 31. Error Handling

Errors must not expose sensitive implementation information.

Responses should not reveal:

* Database credentials.
* Internal filesystem paths.
* Stack traces.
* Secret configuration.
* Internal infrastructure details.
* Sensitive user information.

Example:

```json id="h3x6qd"
{
  "error": {
    "code": "AUTHENTICATION_REQUIRED",
    "message": "Authentication is required."
  }
}
```

Production users should receive controlled error responses.

Detailed technical information belongs in secure server-side logs.

---

# 32. Logging

Security-relevant events should be logged appropriately.

Examples:

* Authentication failures.
* Successful authentication events where useful.
* Authorization failures.
* Unexpected financial-operation failures.
* Server errors.
* Security configuration failures.

Logs must not contain:

* Passwords.
* Session secrets.
* Authentication tokens.
* Database passwords.
* Other sensitive credentials.

Financial descriptions and information should only be logged when genuinely necessary.

---

# 33. Auditability

The application preserves financial history through:

* Active/Voided transaction status.
* Archived people.
* Archived accounts.
* Transaction effects.

The application should be designed so that significant financial changes can be traced through the transaction history.

A dedicated audit-log subsystem is not required for Version 1 unless later requirements call for it.

---

# 34. Account Security

The application should provide appropriate protections for user accounts.

The initial authentication system includes:

* Signup.
* Login.
* Logout.
* Authenticated sessions.

Future account-security features may include:

* Password reset.
* Email verification.
* Multi-factor authentication.
* Login/session management.

These are not required to introduce unrelated functionality into Version 1 unless explicitly approved.

---

# 35. Authorization Failure Behavior

When a user attempts to access another user's protected resource, the server must prevent the operation.

The application should avoid exposing unnecessary information about resources that the user is not authorized to access.

For example, an unauthorized user should not receive sensitive details merely because they guessed a valid UUID.

---

# 36. Frontend Security

The frontend is not a trusted security boundary.

JavaScript validation, disabled controls, hidden fields, and UI restrictions can improve usability but cannot enforce security.

For example:

```text id="6qg4d2"
Frontend:
"Archived account cannot be selected."

Backend:
"Archived account is rejected."
```

The backend validation is authoritative.

---

# 37. API Security

Protected APIs must:

* Require authentication.
* Verify authorization.
* Validate all inputs.
* Validate object ownership.
* Apply business rules.
* Use CSRF protection where applicable.
* Return controlled errors.
* Avoid leaking sensitive information.

---

# 38. Security of Financial Calculations

The frontend must not be trusted to calculate authoritative:

* Bank balances.
* Person positions.
* Credit used.
* Available credit.

The backend calculates these values from authoritative financial data.

This prevents manipulated browser requests from changing the financial truth of the application.

---

# 39. Account and Credit-Card Separation

The security model must preserve the distinction between:

```text id="8w6s6x"
Bank Account
    ↓
Actual available money

Credit Card
    ↓
Borrowing capacity
```

Available credit must not be treated as cash.

Dashboard and financial calculations must maintain this separation.

---

# 40. Secure Deployment Requirements

Before production release:

* HTTPS must be configured.
* Production debug mode must be disabled.
* Production secrets must be configured securely.
* Database access must be restricted.
* Secure cookies must be enabled.
* CSRF configuration must be verified.
* Allowed hosts must be configured.
* CORS must be restrictive.
* Security headers must be configured.
* Error handling must be production-safe.
* Database backups must be considered.
* Logging must be reviewed for sensitive information.

---

# 41. Backup and Recovery

Financial data must be protected against accidental loss.

Production deployment should provide an appropriate PostgreSQL backup strategy.

Backups should be protected with appropriate access controls.

Recovery procedures should be tested rather than assuming that backups are usable.

Backup retention and frequency will be finalized during deployment planning.

---

# 42. Development Security

Developers must not commit:

* `.env` files containing secrets.
* Production credentials.
* Database passwords.
* API keys.
* Private certificates.
* Session secrets.

The repository should contain an example configuration such as:

```text id="p3p4h5"
.env.example
```

containing placeholders rather than real secrets.

---

# 43. Dependency Security

Project dependencies should be kept reasonably current.

Before production deployment:

* Review installed packages.
* Remove unnecessary dependencies.
* Apply security updates.
* Avoid adding libraries without a clear requirement.

The application should keep its dependency surface intentionally small.

---

# 44. Security Testing

Security testing should be included in the development process.

At minimum, test:

### Authentication

* Signup.
* Login.
* Logout.
* Invalid credentials.
* Unauthenticated access.

### Authorization

* Access to own data.
* Attempted access to another user's data.
* Attempted modification of another user's data.

### Financial integrity

* Transaction creation.
* Transaction editing.
* Transaction voiding.
* Card payments.
* Atomic rollback behavior.

### Input validation

* Invalid amounts.
* Invalid identifiers.
* Invalid account types.
* Invalid transaction types.
* Invalid payment sources.

### Web security

* CSRF protection.
* Secure cookies.
* HTTPS behavior.
* Security headers.
* Production debug configuration.

---

# 45. Security Priorities

Security implementation should follow this order:

```text id="s9m9ex"
1. Authentication
       ↓
2. Authorization / Ownership
       ↓
3. HTTPS / TLS
       ↓
4. CSRF / Session Security
       ↓
5. Financial Integrity / Atomicity
       ↓
6. Database Security
       ↓
7. Secrets Management
       ↓
8. Input Validation
       ↓
9. Security Headers / CORS
       ↓
10. Rate Limiting / Monitoring
```

This ordering is intended to ensure that fundamental security controls are implemented before deployment.

---

# 46. Version 1 Security Boundary

Version 1 provides:

```text id="c6s2xk"
Authentication
        +
Authorization
        +
HTTPS/TLS
        +
CSRF Protection
        +
Secure Sessions
        +
Server-side Validation
        +
Financial Atomicity
        +
Database Protection
        +
Secrets Management
        +
Controlled Logging
```

Version 1 does not provide strict cryptographic end-to-end encryption of financial records.

HTTPS/TLS should be described as **encryption in transit**, not strict E2EE.

---

# 47. Security Principle

The fundamental security principle for the application is:

> The browser is untrusted, the backend is authoritative, and financial operations must be validated, authorized, and executed atomically.

Security controls should protect both the user's account and the integrity and confidentiality of their financial records.
