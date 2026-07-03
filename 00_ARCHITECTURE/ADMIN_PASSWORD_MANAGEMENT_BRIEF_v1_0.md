---
artifact: ADMIN_PASSWORD_MANAGEMENT_BRIEF
canonical_id: ADMIN_PASSWORD_MANAGEMENT_BRIEF
version: 1.0
status: READY_FOR_BUILD
branch: feature/admin-password-mgmt
target_executor: Claude Code in Antigravity
date: 2026-06-25
scope:
  may_touch:
    - platform/src/app/api/admin/users/route.ts
    - platform/src/app/api/admin/users/[id]/password/route.ts   # NEW
    - platform/src/components/admin/NewUserDialog.tsx
    - platform/src/components/admin/SetPasswordDialog.tsx        # NEW
    - platform/src/components/admin/UsersTable.tsx
    - platform/src/lib/admin/audit.ts
    - platform/src/lib/auth/password.ts                          # NEW (shared validator)
  must_not_touch:
    - platform/src/app/api/admin/users/[id]/send-reset/route.ts  # keep as-is (secondary path)
    - platform/migrations/**                                     # NO schema change needed
    - any cockpit / bodha / ganita surface
---

# Admin Password Management — In-Portal

## Goal
Keep all password management inside the portal. Two capabilities:
1. **Set a password at user creation** — the super admin types an initial
   password in the New User dialog.
2. **Change any user's password from the admin tab** — a "Set password" action
   in the row Actions menu, changed in-portal, no external Firebase reset page.

The existing email-reset-link flow **stays** as a secondary option (do not remove
`send-reset`).

## Decisions (locked by native 2026-06-25)
- **No forced change on next login.** The admin-set password is the user's real
  password. No `must_change_password` flag, no forced-change screen. (This is why
  **no migration is needed** — nothing to store.)
- **Placement:** "Set password" lives in the existing row **Actions** dropdown in
  `UsersTable.tsx`, opening a modal. Password creation field lives in
  `NewUserDialog.tsx`.
- **Rules:** minimum **8 characters** (Firebase floor is 6; we set 8). Password +
  Confirm fields, with a show/hide toggle. No complexity/strength meter.
- **Email reset:** keep "Send reset link" in the Actions menu as the secondary
  path for when the admin wants the user to set their own.

## Why this is straightforward
Firebase Admin SDK does both server-side, no external page:
- Creation: `adminAuth.createUser({ email, password, displayName })`
- Change:   `adminAuth.updateUser(uid, { password })`

`adminAuth` is already imported in the admin routes. The audit helper already has
a `reset_password` action; reuse it (or add `set_password` — see step 5).

---

## Build steps

### Step 1 — Shared password validator
Create `platform/src/lib/auth/password.ts`:
```ts
import 'server-only'
export function validatePassword(pw: string): string | null {
  if (typeof pw !== 'string' || pw.length < 8) {
    return 'Password must be at least 8 characters.'
  }
  if (pw.length > 128) return 'Password is too long.'
  return null
}
```
(Client mirrors the 8-char check for instant feedback, but the server is authority.)

### Step 2 — Password at creation (`api/admin/users/route.ts` POST)
- Extend `CreateBody` with `password?: string`.
- After existing field validation, if `password` is provided, run
  `validatePassword`; on error return `res.badRequest(error)`.
- Pass it to Firebase: `adminAuth.createUser({ email, emailVerified: false,
  displayName: fullName, password })`.
- **Backward-compatible:** if `password` is omitted/empty, keep current behavior
  (Firebase auto-generates, reset link returned). Do not break the
  access-request approval path, which has its own createUser call — leave that one
  untouched.
- Audit detail: add `{ password_set: Boolean(password) }` to the existing
  `create_user` audit entry so the log records whether an initial password was set
  (never log the password itself).

### Step 3 — New password change route
Create `platform/src/app/api/admin/users/[id]/password/route.ts`:
```ts
import { NextResponse } from 'next/server'
import { requireSuperAdmin } from '@/lib/auth/access-control'
import { adminAuth } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'
import { validatePassword } from '@/lib/auth/password'
import { writeAuditLog } from '@/lib/admin/audit'
import { res } from '@/lib/errors'

export async function POST(
  request: Request,
  ctx: { params: Promise<{ id: string }> },
) {
  const auth = await requireSuperAdmin()
  if (auth instanceof NextResponse) return auth
  const { id } = await ctx.params

  let body: { password?: string }
  try { body = await request.json() } catch { return res.badRequest('invalid request body') }

  const error = validatePassword(body.password ?? '')
  if (error) return res.badRequest(error)

  // Confirm the target exists (and grab email for the audit detail).
  let email: string | null = null
  try {
    const { rows } = await query<{ email: string | null }>(
      'SELECT email FROM profiles WHERE id=$1', [id],
    )
    if (rows.length === 0) return res.notFound('user')
    email = rows[0].email
  } catch { return res.dbError() }

  try {
    await adminAuth.updateUser(id, { password: body.password })
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : 'Could not set password.'
    return res.internal(message)
  }

  await writeAuditLog(auth.user.uid, 'set_password', id, { email })
  return NextResponse.json({ ok: true })
}
```
Notes:
- **Self-change allowed?** The other admin routes block acting on your own uid.
  For password it is reasonable to allow the super admin to change their **own**
  password too — but to stay consistent with the existing pattern and avoid
  scope creep, **block self** here as well (`if (id === auth.user.uid) return
  res.badRequest(...)`) and note self-service password change as a future item.
  Confirm with native if you'd rather allow self.
- Never log or echo the password back in the response.

### Step 4 — New User dialog field (`NewUserDialog.tsx`)
- Add `const [password, setPassword] = useState('')` and a `showPw` toggle.
- Add an optional Password field below Username:
  - label it "Initial password (optional)" with helper "Min 8 chars. Leave blank
    to send a reset link instead."
  - show/hide eye toggle.
- Client-side: if non-empty and < 8 chars, block submit with inline error.
- Include `password` in the POST body only when non-empty.
- After success: if a password was set, show "User created. Share the password
  with them securely." instead of the reset-link sheet; if blank, keep the
  current reset-link behavior.

### Step 5 — Audit action
In `platform/src/lib/admin/audit.ts`, add `'set_password'` to the `AuditAction`
union (keep `'reset_password'` for the email-link path so the two are
distinguishable in the activity panel).

### Step 6 — Set Password dialog + Actions menu (`UsersTable.tsx` + new dialog)
- Create `platform/src/components/admin/SetPasswordDialog.tsx`:
  - props: `user: AdminUser | null`, `open`, `onOpenChange`, `onSaved`.
  - fields: Password + Confirm, show/hide toggle, inline "must match" + "min 8"
    validation.
  - POST to `/api/admin/users/${user.id}/password`; on `!res.ok` toast
    `body.error.message` (note: this codebase wraps errors as `{error:{message}}`
    — match BUG-3's fix, use `body.error.message`).
  - on success: toast "Password updated." and call `onSaved()`.
- In `UsersTable.tsx`: add a `settingPwUser` state + a `<DropdownMenuItem>` "Set
  password" in the Actions menu (place it just above "Send password reset link",
  so in-portal is primary and email is the secondary fallback). Render the dialog
  alongside the others.

---

## Acceptance criteria  `[verify-against: prod]`
1. **Create with password:** new user created with an initial password → that user
   can log in with it immediately, no reset link needed. `[via: live admin tab + login]`
2. **Create without password:** leaving the field blank reproduces today's behavior
   (reset link surfaced). `[via: live admin tab]`
3. **Change password:** "Set password" on an existing non-self user → user can log
   in with the new password; old one rejected. `[via: live admin tab + login]`
4. **Validation:** < 8 chars rejected both client and server; mismatched confirm
   blocked client-side. `[via: live admin tab]`
5. **Audit:** every create-with-password and set-password writes a row
   (`create_user` w/ `password_set:true`, and `set_password`) visible in "Recent
   admin activity". Password value never appears in the log. `[via: psql_prod admin_audit_log]`
6. **Email reset still works** as the secondary option. `[via: live admin tab]`
7. No migration was added; `git diff --stat` touches no file under
   `platform/migrations/`.

## Out of scope (do not build)
- Forced password change on next login / `must_change_password` flag.
- Password strength meter / complexity rules beyond min-8.
- Self-service "change my own password" for the logged-in admin (note as future).
- Removing the email-reset path.

## Commit / ship
- One feature branch `feature/admin-password-mgmt`, discrete commits per step.
- No prod migration to apply this time — ships with deploy only.
- Smoke test all 7 ACs on prod before declaring done.

*End ADMIN_PASSWORD_MANAGEMENT_BRIEF v1.0 — READY_FOR_BUILD.*
