# Fix /api/auth/session role bug — align to canonical `guest` (paste into Claude Code / Antigravity)

**Read CLAUDE.md §C first.** New non-admin signups 500 because `/api/auth/session` INSERTs `role='client'` but
the `profiles` CHECK constraint only allows `'guest'`/`'super_admin'`. **The codebase ALREADY chose `guest` as the
canonical non-admin role** — only the auth-session route + the `Role` type are stale laggards still saying
`client`. This is a CODE alignment fix, **NOT a DB migration** (the constraint is already correct). Fold onto the
current branch (`feature/prashna-embed-across-layers`) before its PR, so the L0-permission model is reachable by a
real client.

## STANDING RAILS
no DB schema change unless proven necessary (the constraint is ALREADY `guest`/`super_admin` — verify, don't
re-migrate); FROZEN orchestrator contract untouched (this is auth, not build); endpoint-verify with a LIVE
signup, not a unit test; align the role value consistently everywhere (no stragglers); the L0-permission model
(just shipped) keys on `isSuperAdmin` so it must keep working with the corrected role.

---

## THE FINDING (code-verified — do not re-decide the role)

Canonical non-admin role = **`guest`**. Evidence:
- `profiles_role_check CHECK (role = ANY (ARRAY['guest','super_admin']))` — `supabase/migrations/
  0001_brahma_baseline.sql:3339` (the live constraint — ALREADY correct).
- `src/components/nav/role-gates.ts:10` comment: *"legacy 'client' role rolled into 'guest' per Unit 2c"*;
  `NavRole = 'super_admin' | 'guest'`.
- `auth_and_chart.ts:64`, `chart-page-guard.ts`, `authorizeChartAccess.ts` all normalize to
  `'guest' | 'super_admin'`. Build-route tests use `'guest'`.

The bug is isolated to TWO stale spots still saying `client`:
1. `src/app/api/auth/session/route.ts` (lines ~25, 27, 47) — types role as `'super_admin' | 'client'` and
   INSERTs `'client'` → CHECK rejects → HTTP 500.
2. `src/lib/db/types.ts:1` — `export type Role = 'super_admin' | 'client'` (stale type definition).

---

## THE FIX (code only — confirm no migration needed)

1. **`auth/session/route.ts`:** change the new-profile INSERT to `role='guest'` (the default for any
   non-super-admin signup), and fix the TypeScript role union on lines ~25/27 from `'super_admin' | 'client'` to
   `'super_admin' | 'guest'`. (Super-admin assignment is out of band — confirm how an admin is promoted; this
   route just creates the default `guest` profile on first signup.)
2. **`db/types.ts:1`:** `export type Role = 'super_admin' | 'guest'`.
3. **Straggler sweep:** grep the WHOLE codebase for `'client'` as a role value (not the word "client" in
   "client_id"/"clients" which are chart-owner concepts — only the profiles.role sense). Fix any remaining
   profiles.role `'client'` references in non-test code. **Test files** that assert `role: 'client'` (e.g.
   `command_center.test.ts:49`, `trace_route.test.ts:40`) must be updated to `'guest'` so they match reality —
   confirm these tests still pass against the corrected role.
4. **Confirm NO migration is needed:** the `profiles` CHECK already allows `guest`. Verify via the live DB
   (`\d profiles` or the constraint query) that the constraint is `['guest','super_admin']` — if (and only if)
   prod somehow diverges, THEN a surgical migration; otherwise NO schema change. State which.

---

## VERIFY (LIVE signup — the bug, proven fixed end-to-end)
1. **⭐ A NEW non-admin signup returns 2xx + creates a profile.** Mint a session for a fresh UID with no profile,
   hit `/api/auth/session`, confirm HTTP 2xx (NOT 500) and a `profiles` row created with `role='guest'`. Paste the
   status + the row. (This is the exact case that previously 500'd and the L0 probe had to bypass with the Admin
   SDK — no bypass this time.)
2. **L0-permission regression:** with that freshly-created `guest` user, re-run the two load-bearing cells —
   build `scope=layer/ganita` → ALLOWED with ZERO L0/global assets in plan; build `scope=layer/brahmagyan` →
   403 FORBIDDEN_L0. Confirm `isSuperAdmin` still resolves correctly for `guest` (the role rename didn't break
   the authorization path).
3. **Role consistency:** grep confirms no `profiles.role='client'` stragglers remain in non-test code; updated
   tests green; CI green.
4. Migration: confirm none needed (or, if prod diverged, applied + ledger-reconciled).

**VERDICT:** PASS only if (1) a real new non-admin signup returns 2xx + creates a `guest` profile, and (2) that
user builds L1-L5 but is blocked from L0. Paste the live signup row + the two permission results — NOT a test
summary. Then this folds into the branch PR.

**Why this matters:** the L0-permission model we just shipped is correct but currently unreachable-by-a-real-client
— no `guest` can be created because signup 500s. This is the missing half: it makes the permission model
actually usable by a real non-admin user.
