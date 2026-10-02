# What changed in this pass

Ten issues reported after using the app, fixed in the same order:

1. **Signup** — added a confirm-password field, a visible list of Django's
   password criteria, and a live strength meter (`core/templates/core/signup.html`,
   `core/static/core/app.js`). Mismatched passwords are rejected server-side too.
2. **Dashboard "View more"** — Financial Accounts is now an in-place
   `<details>` expander on the dashboard itself; it no longer navigates away.
   People and Transactions keep a "View all" link to their own pages, matching
   `docs/04-ui-structure.md` \u00a73.6/3.7/3.8.
3. **Sidebar / mobile nav**
   - Desktop sidebar is collapsible (chevron button, persisted in
     `localStorage`) and the active link is now driven by an `active_nav`
     context variable per page instead of being hard-coded to Dashboard.
   - Mobile bottom nav uses icons instead of words.
   - The center `+` opens a small popup with "Add transaction" / "Card
     payment" instead of linking straight to Add Transaction.
4. **Dashboard not updating** — the template was reading
   `account.bank_details.opening_balance` / `credit_card_details.credit_limit`
   directly instead of the computed balance. It now uses a bulk
   `account_summaries()` service call. Family Positions shows Held / Receivable
   / Settled and an amount, not `effects.count`.
5. **People page** — added View, Edit, Archive/Unarchive per person (`/people/<id>/edit/`,
   `/people/<id>/archive-toggle/`), plus their current position.
6. **Accounts page** — added Edit, Archive/Unarchive, and "Pay card" for credit
   cards (`/accounts/<id>/edit/`, `/accounts/<id>/archive-toggle/`).
7. **Transactions page** — search is now paired with a collapsed "Filters"
   panel (person, account, account type, transaction type, status, date
   range, amount range). Rows show description, type, account name + type,
   amount, and running balance after the transaction. Voided transactions can
   be restored (`/transactions/<id>/restore/`), guarded the same way void is
   guarded (see #4 below in the correctness list).
8. **Add Transaction form** — payment source / bank source account fields
   only appear for Card Payment; the Account field's label and options adapt
   to the type. Added Income, Bonus, and Extra transaction types (deposit to
   a bank account, no person required).
9. **Settings** — currency is now shown everywhere money is displayed (via a
   `money` template filter and a context processor), and the theme actually
   changes the app: `data-theme` drives a full dark palette, with `system`
   following `prefers-color-scheme`.
10. **Topbar settings icon** — hidden above 760px width via CSS; desktop and
    tablet use the sidebar's Settings link instead.

## Also fixed while in there (correctness bugs found during review)

- Voiding a transaction is now rejected if it would push a bank balance
  negative or a card's used-credit negative; editing keeps the original
  effect rows instead of deleting them; balances are checked against the
  full date-ordered timeline, not just today's total, so backdated and
  postdated transactions can't create impossible states; a restore action
  was added for voided transactions with the same guard.
- `core/services.py` now has one shared "plan" builder for create/edit
  instead of ~100 duplicated lines; N+1 queries in the dashboard/people/
  accounts pages were replaced with three bulk queries; `core/admin.py`
  registers `User` with Django's real `UserAdmin` so the password field is
  hashed instead of stored as plain text through the admin.

## Not done in this pass (flagged, not fixed)

Deployment hygiene from the first review (git init, `.env` loading,
`SECRET_KEY`, gunicorn/whitenoise, CI) and the bigger structural refactor
(splitting `views.py` into pages/api, moving to DRF) are unchanged. Detail
pages for an individual person/account (docs \u00a74.3) were not added; existing
list-page actions cover view/edit/archive.
