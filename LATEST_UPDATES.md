# Ledgerly — Latest project updates

This build includes the latest requested UI and account-management changes on top of the transaction import/export build.

## Included
- Transaction import/export for CSV, XLS, and XLSX from the existing build.
- Add Transaction page action band contains only Money transfer and Card payment.
- Dashboard Financial accounts details is collapsed by default.
- People, Accounts, and Transactions intro bands remain left-aligned without changing the centered content below them.
- Desktop/tablet logout is separated above Settings in the sidebar.
- Mobile logout remains inside Settings.
- Profile page at `/profile/` for changing first name, last name, email, and password.
- Email changes require the current password; password changes validate against Django's configured password validators and preserve the current session.
- Profile input borders remain visible in both light and dark themes, including browser autofill.
- Dashboard greeting displays the greeting and user's name on separate lines.
- Application timezone is set to `Asia/Kolkata` for local date/time behavior.
- Existing dark-theme native dropdown fixes are preserved.
### 2026-10-01 — Mobile system-dark theme
- Fixed the mobile sticky topbar and bottom navigation when the app theme is set to **System** and the device/browser is using dark mode.
- Added targeted `prefers-color-scheme: dark` overrides for `[data-theme="system"]` so the mobile chrome uses the dark translucent backgrounds instead of the light/grey appearance.
