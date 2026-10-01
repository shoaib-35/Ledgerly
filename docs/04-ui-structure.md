# UI Structure — Family Expense Tracker

## 1. Purpose

This document defines the confirmed user interface structure and visual design language for the Family Expense Tracker application across desktop, tablet, and mobile layouts.

The UI is designed around:
- Family/person financial positions
- Bank and cash account balances
- Credit card usage
- Transaction management
- Clear financial effects
- Responsive navigation
- A premium Apple-inspired visual and interaction language

The UI structure and financial rules in this document are authoritative. The Apple-inspired design language is a visual and interaction layer and must not change the information architecture, workflows, terminology, financial rules, page order, or required actions.

Features not defined in this document should not be added without a confirmed requirement.

---

# 2. Global Navigation

## 2.1 Desktop Navigation

Desktop uses a persistent left sidebar.

```text
Dashboard
People
Accounts
Transactions
────────────────
+ Add Transaction
+ Card Pay
────────────────
Settings
```

The main content area changes according to the selected section.

### Desktop navigation actions

- **Dashboard** → financial overview
- **People** → people/family ledgers
- **Accounts** → bank accounts and credit cards
- **Transactions** → transaction history and management
- **+ Add Transaction** → opens Add Transaction drawer
- **+ Card Pay** → opens Credit Card Payment drawer
- **Settings** → application and data settings

Add Transaction and Card Pay are actions rather than ordinary data-navigation pages.

### Desktop visual treatment

The sidebar should feel like premium application chrome:
- Subtle translucent/glass material may be used.
- Backdrop blur may be used where supported.
- A fine border and restrained depth should separate the sidebar from the content.
- The active destination should be distinguishable through surface, icon, typography, and position; color must not be the only indicator.
- Avoid excessive blur, gradients, shadows, or decorative effects.

---

## 2.2 Mobile Navigation

Mobile uses a fixed bottom navigation bar with five positions:

```text
Dashboard    People       +       Accounts    Transactions
```

The center `+` is the primary action button.

### Fixed bottom navigation — locked behavior

The mobile bottom navigation is **fixed to the bottom of the viewport**.

It is not part of the scrollable dashboard/content area.

The user must be able to access:
- Dashboard
- People
- Add actions through `+`
- Accounts
- Transactions

at all times without scrolling to the bottom of the page.

Conceptually:

```text
┌─────────────────────────────────────┐
│ Top application bar                 │
├─────────────────────────────────────┤
│                                     │
│                                     │
│      Scrollable page content        │
│                                     │
│                                     │
│                                     │
├─────────────────────────────────────┤
│ Dashboard People  +  Accounts Txns  │
└─────────────────────────────────────┘
                    ↑
              FIXED TO BOTTOM
```

The content area must include sufficient bottom padding so that the fixed navigation does not cover the last piece of content.

The navigation should remain visible and usable while the user scrolls.

### Center + menu

Tapping `+` expands:
- Add Transaction
- Card Payment

The `+` action may use a tactile/spring interaction and a compact floating action presentation.

There is no hamburger/three-dot navigation menu for these actions.

### Mobile top bar

The mobile top bar contains:
- Current page/application title
- Settings icon

Example:

```text
Dashboard                                      ⚙
```

The top bar remains directly accessible while browsing the page. It may use a subtle translucent/glass treatment.

### Mobile navigation principles

- Dashboard, People, Accounts and Transactions are primary destinations.
- Add Transaction and Card Payment are primary actions.
- Settings is an application-level function.
- The bottom navigation is fixed to the viewport.
- The bottom navigation does not scroll away with page content.
- Mobile content scrolls independently behind/above the navigation.
- The navigation must remain accessible without requiring the user to scroll down.
- Mobile does not use a hamburger menu for the primary destinations or these actions.

### Mobile navigation iconography

Use simple, recognizable icons for the primary navigation:

- Dashboard → Home icon
- People → People/Users icon
- `+` → Add/Plus action
- Accounts → Bank/Building icon
- Transactions → List/Receipt icon

Icons should follow a consistent simple, classy visual style with a restrained black/monochrome theme in light mode.

Icons must remain visually consistent in:
- Stroke weight
- Size
- Alignment
- Corner treatment
- Active/inactive states

Icons should support the navigation labels rather than replace them, ensuring the interface remains understandable and accessible.

---

# 3. Dashboard

The Dashboard provides a high-level overview of the entire financial system.

## 3.1 Order of content

The order is locked:

1. Greeting
2. Financial overview cards
3. Financial Accounts
4. Family Position Overview
5. Family Positions
6. Recent Transactions

No additional dashboard sections should be introduced without a confirmed requirement.

## 3.2 Desktop dashboard

The desktop dashboard uses the same information hierarchy with a wider composition.

```text
Dashboard

Good morning, Shoaib

┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Cash / Bank  │ │ Credit       │ │ Credit       │
│ Balance      │ │ Available    │ │ Used         │
└──────────────┘ └──────────────┘ └──────────────┘

Financial Accounts                              Expand ▼

Family Positions

Recent Transactions
```

Dashboard cards may be displayed horizontally where space permits.

### 3.3 Family Position Overview

The Dashboard includes a compact three-card overview before the individual family positions:

- **Total Held** — sum of positive family ledger positions.
- **Total Receivables** — absolute value of negative family ledger positions.
- **Current Balance** — `Total Held - Total Receivables`.

The three cards use the existing financial-overview semantic palette: green for held, red/coral for receivables, and blue for the current position.

## 3.3 Mobile dashboard structure

The mobile Dashboard is one vertically scrolling content area.

The fixed top application bar and fixed bottom navigation are separate from this scrollable content.

```text
┌─────────────────────────────────────────────┐
│ Dashboard                              ⚙   │
├─────────────────────────────────────────────┤
│                                             │
│ Good morning, Shoaib                        │
│                                             │
│ Financial overview                          │
│                                             │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐     │
│ │ Cash /   │ │ Credit   │ │ Credit   │     │
│ │ Bank     │ │ Available│ │ Used     │     │
│ │ Balance  │ │          │ │          │     │
│ └──────────┘ └──────────┘ └──────────┘     │
│                                             │
│ Financial Accounts                    ▼     │
│                                             │
│ Family Positions                            │
│ ┌─────────────────────────────────────────┐ │
│ │ Mom                 ₹1,500 Receivable   │ │
│ │ Dad                 ₹4,250 Held         │ │
│ │ Grandpa             Settled             │ │
│ └─────────────────────────────────────────┘ │
│                                             │
│ Recent Transactions                         │
│ ┌─────────────────────────────────────────┐ │
│ │ Recent transaction list                 │ │
│ └─────────────────────────────────────────┘ │
│                                             │
│              View All →                     │
│                                             │
├─────────────────────────────────────────────┤
│ Dashboard  People   +   Accounts  Txns      │
└─────────────────────────────────────────────┘
                    ↑
             fixed navigation
```

The dashboard content scrolls. The bottom navigation does not.

The financial summary should remain clearly separate even on narrow screens. If the three cards cannot comfortably fit at the target width, they may form a horizontally scrollable summary row rather than changing their meaning or merging the metrics.

## 3.4 Greeting

Example:

```text
Dashboard

Good morning, Shoaib
```

The greeting may adapt to the current time.

## 3.5 Financial overview

Three separate metrics are displayed:
- Cash / Bank Balance
- Credit Available
- Credit Used

Example:

```text
Cash / Bank Balance     ₹60,700
Credit Available        ₹178,200
Credit Used              ₹21,800
```

These must remain separate.

Available credit must not be added to bank/cash balances and presented as owned money.

### Financial overview visual treatment

Cards should use:
- Rounded geometry
- Clear hierarchy between label and value
- Calm typography
- Subtle depth
- Comfortable spacing
- Strong alignment of financial values

The cards must not introduce visual ambiguity between owned cash and available credit.

## 3.6 Financial Accounts

The Financial Accounts section is expandable.

Collapsed:

```text
Financial Accounts                         Expand ▼
```

Expanded:

```text
Financial Accounts                         Collapse ▲

Bank Accounts
HDFC Bank                                  ₹35,700
SBI Bank                                   ₹25,000

Credit Cards
HDFC Credit Card                           ₹45,000 used
Available Credit                           ₹55,000
```

The Dashboard provides a summary; detailed account management remains on the Accounts page.

The expandable interaction should provide immediate feedback and may use a restrained spring/height transition.

## 3.7 Family Positions

Each active person can be displayed with a derived financial position.

Examples:

```text
Mom                         ₹1,500 Receivable
Dad                         ₹4,250 Held
Grandpa                     Settled
```

Meaning:
- Receivable → the person owes the user money.
- Held → the user is holding money belonging to the person.
- Settled → balance is zero.

The section should use a clean, readable list/card treatment with strong alignment of person, amount, and status.

## 3.8 Recent Transactions

The Dashboard shows a limited number of recent transactions.

Example:

```text
Date       Person      Description       Account       Amount
Sep 23     Mom         Groceries         HDFC Bank     -₹500
Sep 22     Dad         Received          SBI Bank     +₹2,000
Sep 21     Mom         Medicine          HDFC Card    -₹700

                         View All Transactions →
```

`View All Transactions` opens the Transactions page.

On mobile, recent transactions should become mobile-friendly list/card rows rather than forcing a wide desktop table.

---

# 4. People

## 4.1 People list

The People page contains a list of people/family members.

```text
People

                              + Add Person

Person       Position              Status
────────────────────────────────────────────
Mom          ₹1,500 Receivable     Active
Dad          ₹4,250 Held           Active
Grandpa      Settled               Active
Choti Didi   ₹800 Receivable       Active
```

Position is calculated automatically from the person's ledger.

### Visual treatment

Use:
- Rounded list/card surfaces where appropriate
- Comfortable row height
- Clear person/position/status hierarchy
- Subtle separators
- Visible actions
- No unnecessary three-dot action menu

## 4.2 Person actions

Each person supports:
- View
- Edit
- Archive

### Archive behavior

Archived people:
- Remain in historical records.
- Remain associated with historical transactions.
- Cannot be selected for new transactions.
- Can be viewed from Settings → Archived People.

## 4.3 Person details

Opening a person displays:

```text
Mom

₹1,500 Receivable

[ Edit ] [ Archive ]

Financial Position
Receivable                         ₹1,500

Recent Transactions
────────────────────────────────────
Date       Description       Account      Amount
Sep 23     Groceries         HDFC Bank    ₹500
Sep 20     Medicine          HDFC Card   ₹1,000

                              View All →
```

`View All` opens the Transactions page filtered to that person.

---

# 5. Accounts

Accounts contain two account types:
- Bank Accounts
- Credit Cards

The Accounts page uses:

```text
[ All ] [ Bank Accounts ] [ Credit Cards ]

                              + Add Account
```

## 5.1 Bank account card

```text
HDFC Bank

₹42,500
Current Balance

24 Transactions

View Transactions    Edit    Archive
```

Current balance is calculated from the account's opening balance and applicable transaction effects.

Bank account actions:
- View transactions
- Edit
- Archive

## 5.2 Credit card card

```text
HDFC Credit Card

₹85,000
Available Credit

Used       ₹15,000
Limit      ₹1,00,000

View       Pay Card    Edit    Archive
```

Credit card relationships:

```text
Used Credit = Credit Limit - Available Credit
```

Credit card actions:
- View
- Pay Card
- Edit
- Archive
- Change credit limit through editing

A credit card payment increases available credit and decreases used credit.

## 5.3 Account archive behavior

Archived accounts:
- Remain in historical records.
- Remain associated with historical transactions.
- Cannot be selected for new applicable transactions.
- Can be viewed from Settings → Archived Accounts.

## 5.4 Account action presentation

The confirmed UI uses visible actions rather than duplicating actions inside a three-dot menu.

Apple-inspired styling must not reintroduce a hidden action menu.

---

# 6. Transactions

The Transactions page is the primary transaction-management area and is intended to be the most powerful page in the application.

## 6.1 Transaction list

```text
Transactions

[ Search transactions... ]          + Add Transaction

[ Filters (3 active) ▼ ]

Date | Person | Description | Account | Type | Amount
──────────────────────────────────────────────────────
Sep23 | Mom | Groceries | HDFC | Expense | -₹500
Sep22 | Dad | Received | SBI | Received | +₹2,000
Sep21 | Mom | Medicine | HDFC CC | Expense | -₹700
```

## 6.2 Search

Search should allow the user to search transaction records.

## 6.3 Filters

Filters are expandable so they do not consume excessive screen space.

Available filters:
- Person
- Account
- Account Type
- Transaction Type
- Date/date range
- Amount/amount range

Filters can be combined.

Example:

```text
[ Filters (5 active) ▼ ]
```

Expanded:

```text
Person
☑ Mom
☐ Dad
☐ Grandpa

Account Type
☐ Bank
☑ Credit Card

Type
☑ Expense
☐ Received

Date
From: 01/09/2026
To:   23/09/2026

Amount
Min: ₹500
Max: ₹5,000

[ Apply ] [ Clear ]
```

Filter controls may use translucent/elevated surfaces and rounded controls, while preserving clear labels, focus states, and accessibility.

## 6.4 Transaction types

Confirmed types:
- Expense
- Received
- Card Payment

`Received` is preferred over `Income` because received money associated with a person is not necessarily the user's personal income.

## 6.5 Add Transaction

Add Transaction opens as a right-side drawer on desktop.

```text
Add Transaction

Date
[ 23 / 09 / 2026 ]

Person
[ Mom ▼ ]

Transaction Type
[ Expense ▼ ]

Account
[ HDFC Bank ▼ ]

Amount
[ ₹500 ]

Description
[ Groceries ]

[ Cancel ] [ Save ]
```

Saving the transaction automatically applies all relevant financial effects.

The user does not enter those effects separately.

Example:

```text
Mom ledger       -₹500
HDFC Bank        -₹500
```

### Desktop drawer treatment

The right-side drawer should:
- Use a rounded leading edge.
- Have a clear elevated/glass surface.
- Preserve strong form hierarchy.
- Provide immediate open/close feedback.
- Remain interruptible.
- Avoid excessive animation.

## 6.6 Mobile Add Transaction

On mobile, Add Transaction is launched through the center `+` button in the fixed bottom navigation.

The form should use a mobile-appropriate:
- Sheet
- Modal
- Full-screen presentation

while preserving the same fields and behavior.

The sheet may use rounded top corners, safe-area spacing, and tactile spring-based motion.

---

# 7. Credit Card Payment

Credit Card Payment is a separate quick action because it is a transfer/payment workflow rather than a normal expense.

```text
Pay Credit Card

Credit Card
[ HDFC Credit Card ▼ ]

Amount
[ ₹5,000 ]

Payment From
○ Bank Account
○ Cash

Bank Account
[ SBI Bank ▼ ]

Date
[ 23 / 09 / 2026 ]

Available after payment
₹80,000 → ₹85,000

[ Cancel ] [ Make Payment ]
```

When Cash is selected, the Bank Account selector is hidden.

When a bank account is selected:
- Bank balance decreases.
- Credit card available credit increases.
- Credit card used credit decreases.

A card payment is recorded as a Card Payment transaction and is not treated as a normal expense.

### Presentation

Desktop:
- Right-side drawer.

Mobile:
- Sheet/modal/full-screen presentation.

The interaction should clearly communicate the financial consequence without dramatic effects.

---

# 8. Transaction Details

Selecting a transaction opens its detailed view.

```text
Transaction Details

Mom
Expense

₹2,000

23 September 2026

Description
Groceries

Paid From
HDFC Bank

Financial Effects
────────────────────────
Mom              -₹2,000
HDFC Bank        -₹2,000

Status
Active

[ Edit ] [ Void ]
```

The Financial Effects section provides transparency into the changes caused by the transaction.

The detail view should emphasize:
- Transaction type
- Amount
- Person
- Account
- Financial effects
- Status
- Available actions

---

# 9. Edit Transaction

Editing reuses the Add Transaction form.

Before saving, the application may show the financial change summary.

Example:

```text
Current
Mom · ₹5,000 · HDFC Bank

New
Mom · ₹3,000 · SBI Bank

Financial Changes
HDFC Bank        +₹5,000
SBI Bank         -₹3,000
Mom              -₹3,000

[ Cancel ] [ Save Changes ]
```

The underlying operation is:

1. Reverse the complete original transaction effects.
2. Apply the complete updated transaction effects.
3. Keep the same historical transaction record.

If multiple fields change, the complete original effect is reversed before the updated effect is applied.

The UI should communicate consequential changes clearly but calmly.

---

# 10. Void Transaction

Transactions are voided rather than physically deleted.

When a transaction is voided:

1. Its financial effects are reversed.
2. Its historical record remains.
3. Its status changes from Active to Voided.
4. It no longer contributes to current balances.

Example confirmation:

```text
Void Transaction?

This will reverse the financial effects
of this transaction.

Mom              +₹2,000
HDFC Bank        +₹2,000

The transaction will remain in history
with status "Voided".

[ Cancel ] [ Void Transaction ]
```

The confirmation should make the consequence clear without using dramatic animation or visual alarm.

---

# 11. Settings

Settings are intentionally minimal in the initial version.

```text
Settings

Application
├── Currency
├── Date Format
└── Theme

Data
├── Archived People
├── Archived Accounts
└── Voided Transactions
```

## 11.1 Application

### Currency

Controls the currency displayed by the application.

Initial/default currency: INR (₹).

### Date Format

Controls how dates are displayed throughout the UI.

The stored date value is independent of display formatting.

### Theme

Provides the application's supported theme options.

The theme should support the application's Apple-inspired visual language in both light and dark presentation.

## 11.2 Data

### Archived People

View archived people and their historical information.

### Archived Accounts

View archived bank accounts and credit cards.

### Voided Transactions

View transactions that have been voided.

No additional settings should be added until an actual requirement exists.

---

# 12. Responsive Design

The application must be responsive from the beginning.

## 12.1 Desktop

- Persistent left sidebar.
- Wide tables where appropriate.
- Right-side drawers for Add Transaction and Card Payment.
- Dashboard cards displayed horizontally where space permits.
- Premium application chrome with selective glass/translucent surfaces.
- Rounded containers and restrained depth.
- Content should use available width without becoming visually stretched.

## 12.2 Tablet

Tablet layouts should preserve the same information hierarchy and navigation model while adapting spacing and composition to the available width.

The tablet layout should be intentionally responsive rather than being a scaled desktop or oversized mobile layout.

Where the desktop sidebar would consume too much space, navigation may adapt to a compact responsive composition, but the primary destinations and confirmed actions must remain directly accessible.

No new navigation model should be introduced without a confirmed requirement.

## 12.3 Mobile

Mobile uses:

- Fixed bottom navigation.
- Center `+` action.
- Settings in the top bar.
- One vertically scrolling content area.
- Bottom navigation remains fixed to the bottom of the viewport.
- Bottom navigation remains usable without scrolling to the bottom.
- Adequate bottom content padding so navigation does not cover content.
- Transaction data presented as mobile-friendly lists/cards rather than forcing a wide desktop table.
- Forms presented as mobile-appropriate sheets, modals, or full-screen views.
- Safe-area-aware spacing around the fixed bottom navigation.
- The same financial rules and functionality as desktop.

### Mobile dashboard behavior

The mobile Dashboard follows this exact hierarchy:

```text
Top bar
  Dashboard + Settings

Scrollable content
  Greeting
  Financial Summary
  Financial Accounts
  Family Positions
  Recent Transactions
  View All

Fixed bottom navigation
  Dashboard | People | + | Accounts | Transactions
```

The bottom navigation is not included in the scrolling content.

---

# 13. Apple-Inspired Design Language

The application uses an Apple-inspired design language as a visual and interaction layer.

This is not a literal Apple UI clone and does not replace the confirmed UI structure.

## 13.1 Design goal

The visual target is:

> Premium, calm, precise, tactile, responsive, and refined.

The interface should feel intentional rather than like a generic administrative dashboard.

## 13.2 Geometry

Use rounded geometry consistently but not excessively.

Suggested hierarchy:
- Large containers: approximately 20–28px radius
- Medium containers: approximately 16–22px radius
- Inputs/buttons: approximately 12–16px radius
- Small controls: approximately 10–14px radius
- Icon containers: rounded-square geometry where appropriate

The exact values should be centralized in design tokens.

## 13.3 Crystal/glass material

Use crystal-like translucent surfaces selectively for:
- Desktop sidebar
- Mobile bottom navigation
- Floating action controls
- Drawers/sheets
- Popovers/filter controls where appropriate

Glass should not be applied to every card or every background.

A glass surface may combine:
- Semitransparent background
- Backdrop blur
- Fine border
- Subtle highlight
- Controlled shadow/depth

The result should remain readable and accessible.

If transparency or backdrop blur is unavailable or reduced by the user's accessibility settings, use an opaque fallback surface.

## 13.4 Typography

Use a system-native typography stack where appropriate:

```css
-apple-system,
BlinkMacSystemFont,
"SF Pro Display",
"SF Pro Text",
"Segoe UI",
system-ui,
sans-serif
```

Do not bundle proprietary fonts unless they are properly licensed.

Typography should prioritize:
- Clear hierarchy
- Comfortable reading
- Strong financial values
- Calm secondary text
- Consistent line height

## 13.5 Color and semantics

Use restrained color.

Color should support hierarchy and interaction rather than become decoration.

Important states must not rely on color alone. Use combinations of:
- Typography
- Icons
- Labels
- Position
- Surface treatment

Financial meaning must remain clear.

## 13.6 Motion

Motion should be:
- Immediate
- Functional
- Subtle
- Spring-based where appropriate
- Interruptible
- Responsive to user input

Good candidates:
- Navigation selection
- Bottom `+` expansion
- Drawer/sheet presentation
- Expand/collapse of Financial Accounts
- Button press feedback
- Filter popovers

Avoid animation that exists only for decoration.

Support reduced-motion preferences and provide a useful static presentation when motion is reduced.

## 13.7 Buttons and controls

Controls should feel tactile.

Use:
- Clear labels
- Rounded geometry
- Adequate touch targets
- Strong focus states
- Subtle press feedback

A subtle press-scale effect such as approximately `scale(0.97)` may be used where appropriate.

## 13.8 Drawers and sheets

Desktop:
- Right-side drawers
- Rounded leading corners
- Elevated/translucent surface
- Clear close/cancel action

Mobile:
- Native-like sheets
- Rounded top corners
- Safe-area spacing
- Drag behavior only where useful and accessible
- Full-screen fallback for complex forms

All transitions should be interruptible.

## 13.9 Lists and tables

Avoid a generic admin-dashboard appearance.

Use:
- Comfortable row height
- Subtle separators
- Clear alignment
- Strong amount alignment
- Clear primary/secondary hierarchy

On mobile, transform dense tables into readable list/card structures instead of merely shrinking columns.

## 13.10 Financial cards

Financial cards should use:
- Rounded geometry
- Strong primary value
- Secondary metadata
- Clear labels
- Calm visual hierarchy
- Visible actions where required

Do not merge financially distinct concepts merely to simplify the visual design.

## 13.11 Filters and popovers

Filters and popovers should use:
- Rounded controls
- Elevated/translucent surfaces
- Clear selected states
- Strong focus indication
- Adequate touch targets

## 13.12 Accessibility

The design must support:
- Keyboard navigation
- Visible focus states
- Sufficient contrast
- Reduced motion
- Reduced transparency where applicable
- Screen-reader labels
- Adequate touch targets
- Non-color-only state communication

Premium visual effects must never reduce usability.

## 13.13 Iconography

The application should use a consistent, minimal icon system inspired by native platform interfaces.

Icons should be:
- Simple
- Recognizable
- Clean
- Consistent in stroke weight
- Visually restrained
- Classy rather than decorative

Primary navigation icons:

Dashboard → Home
People → People/Users
Accounts → Bank/Building
Transactions → List/Receipt
Add → Plus

Use a monochrome icon treatment by default, adapting automatically to the active theme.

Icons must not rely on color alone to communicate navigation state. Active navigation may use subtle surface, weight, opacity, or positional changes while preserving the overall minimal aesthetic.

---

# 14. Design Tokens

Design values should be centralized rather than hard-coded throughout the application.

Suggested token categories:

```text
Radius
Spacing
Typography
Surface
Border
Shadow
Motion
Color
Interaction
```

Example conceptual structure:

```text
radius
├── small
├── medium
├── large
└── extra-large

spacing
├── xs
├── sm
├── md
├── lg
└── xl

motion
├── fast
├── standard
└── spring
```

The exact token values may be refined during implementation without changing the confirmed UI structure.

---

# 15. Design Anti-Patterns

Do not introduce:

- Excessive glass everywhere
- Excessive blur
- Excessive rounded corners
- Heavy shadows
- Neon or overly saturated decorative styling
- Decorative gradients without a clear purpose
- Excessive animation
- Non-interruptible transitions
- Generic admin-dashboard styling
- Tiny mobile controls
- Hidden essential actions
- Unnecessary hamburger/three-dot menus
- New navigation destinations without approval
- Changes to the locked page hierarchy
- Financially ambiguous visualizations
- Treatment of available credit as cash
- `Income` terminology in place of `Received`
- Physical deletion of transactions
- UI features not defined by the confirmed requirements

---

# 16. AI Coding Agent / Implementation Rules

When implementing this UI with an AI coding agent:

1. This document is the source of truth for UI structure.
2. The Apple-inspired design language is the visual/interaction layer.
3. Never change locked navigation or financial behavior for aesthetic reasons.
4. Preserve the exact mobile bottom navigation:
   `Dashboard | People | + | Accounts | Transactions`.
5. The mobile bottom navigation must be fixed to the viewport.
6. Never place the mobile bottom navigation inside the scrollable page content.
7. The user must be able to switch primary pages without scrolling to the bottom.
8. Preserve the mobile top bar with current page title and Settings.
9. Preserve the Dashboard content order.
10. Keep Cash/Bank Balance, Credit Available, and Credit Used separate.
11. Use glass selectively rather than turning the entire application into glassmorphism.
12. Use motion to communicate interaction, not as decoration.
13. Respect reduced-motion and reduced-transparency preferences.
14. Preserve accessibility while applying premium visual styling.
15. Do not introduce new UI features without a confirmed requirement.
16. Prefer prototyping and validating interaction before overengineering the visual system.
17. Keep design tokens centralized.
18. Treat financial meaning as more important than visual simplification.

---

# 17. UI Consistency Decisions

The following decisions are locked:

1. Desktop uses a left sidebar.
2. Mobile uses five bottom-navigation positions: Dashboard, People, +, Accounts, Transactions.
3. The mobile bottom navigation is fixed to the bottom of the viewport.
4. Mobile page content scrolls independently from the fixed bottom navigation.
5. The mobile bottom navigation must remain usable without scrolling down.
6. The mobile content area must reserve space so the fixed navigation never hides the final content.
7. The center `+` expands to Add Transaction and Card Payment.
8. Settings is accessed from the mobile top bar.
9. There is no mobile hamburger menu for transaction actions or primary navigation.
10. Dashboard shows Cash/Bank Balance, Credit Available and Credit Used separately.
11. Available credit is never treated as owned cash.
12. Financial Accounts on the Dashboard are expandable.
13. People positions are derived automatically.
14. Archived people and accounts remain historically intact.
15. Transactions are never physically deleted.
16. Voiding reverses financial effects while preserving history.
17. Editing reverses the original transaction and applies the updated transaction.
18. Transactions support combined filters.
19. Add Transaction and Card Payment are action drawers/sheets rather than primary navigation pages.
20. Card Payment is distinct from an Expense.
21. `Received` is used instead of `Income`.
22. Settings remains intentionally small.
23. Mobile must not simply shrink desktop tables; information should be presented in mobile-appropriate layouts.
24. Apple-inspired design is a visual and interaction layer, not a replacement for the UI structure.
25. Glass/translucency is selective rather than universal.
26. Motion is functional, subtle, spring-oriented where appropriate, interruptible, and accessibility-aware.
27. Accessibility is required across the visual system.
28. No additional UI features should be introduced without a confirmed requirement.

---

# 18. UI Review Status

The UI structure has been reviewed across:

- Desktop navigation
- Mobile navigation
- Fixed mobile bottom navigation behavior
- Mobile top bar
- Dashboard
- People
- Accounts
- Transactions
- Add Transaction
- Credit Card Payment
- Transaction Details
- Edit/Void workflows
- Settings
- Desktop responsiveness
- Tablet responsiveness
- Mobile responsiveness
- Apple-inspired visual language
- Glass/translucent surfaces
- Motion
- Accessibility
- Terminology
- Status handling
- AI coding-agent implementation rules

This document represents the confirmed UI structure and design direction to use as the basis for the subsequent data model, database design, architecture, API specification, and implementation planning.
