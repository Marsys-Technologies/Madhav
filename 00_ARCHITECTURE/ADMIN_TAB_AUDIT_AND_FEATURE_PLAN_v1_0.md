---
artifact: ADMIN_TAB_AUDIT_AND_FEATURE_PLAN
canonical_id: ADMIN_TAB_AUDIT_AND_FEATURE_PLAN
version: 1.0
status: DRAFT
branch: feature/admin-tab-overhaul
author: Cowork (planning/audit) — implementation deferred to Claude Code in Antigravity
date: 2026-06-25
scope: platform/src/app/admin/**, platform/src/components/admin/**, platform/src/app/api/admin/users/**, platform/src/app/api/admin/access-requests/**, platform/migrations/**
---

# Admin Tab — Audit & Feature Plan

The "Admin → manage users" surface. This document is two things: (1) a forensic
audit of the current admin tab and the bug that makes it fail, and (2) a scoped
feature plan for what to build to make it genuinely useful for a single super
admin running this portal — no more, no less.

---

## §1 — What exists today (map)

**Route surface** `platform/src/app/admin/`
- `layout.tsx` — gates `role === 'super_admin'` AND `status === 'active'`; else redirect. Solid.
- `page.tsx` → renders `AdminClient` with the current uid.
- `error.tsx` — generic admin error boundary.

**UI** `platform/src/components/admin/`
- `AdminClient.tsx` — two react-query panels: pending access requests + users table.
- `PendingRequestsTable.tsx`, `ApproveDialog.tsx` — approve/reject access requests.
- `UsersTable.tsx` — list, search, row actions (edit username, send reset, disable/enable, delete), New-user button, reset-link sheet.
- `NewUserDialog.tsx`, `EditUsernameDialog.tsx`, `ConfirmDialog.tsx`.

**API** `platform/src/app/api/admin/`
- `users/route.ts` — GET list, POST create (Firebase user + profile row + reset link).
- `users/[id]/route.ts` — PATCH (username / status), DELETE (Firebase + profile).
- `users/[id]/send-reset/route.ts` — generate Firebase password-reset link.
- `access-requests/route.ts` + `[id]/approve` + `[id]/reject`.

**Data model** `platform/migrations/001_baseline.sql`
- `profiles(id, role, name, created_at, username, email, status, approved_at, approved_by)`
  - `role ∈ {guest, super_admin}` · `status ∈ {pending, active, disabled}`
- `access_requests(id, full_name, email, reason, status, requested_at, reviewed_at, reviewed_by, approved_user_id)`

The architecture is clean and correct in shape. The tab is not failing because it
was badly built — it is failing because of one concrete schema bug plus a few
rough edges.

---

## §2 — Why it is failing (root cause)

### BUG-1 (CRITICAL — this is "the admin tab fails") · `profiles.updated_at` does not exist
`api/admin/users/[id]/route.ts` PATCH unconditionally appends `updated_at=now()`
to every UPDATE:

```ts
setClauses.push(`updated_at=now()`)
```

But **no migration ever adds an `updated_at` column to `profiles`** (verified
across `001_baseline.sql` and all `migrations/*.sql`; the baseline CREATE has no
such column). Postgres therefore throws `column "updated_at" of relation
"profiles" does not exist` on **every** PATCH. That means:

- "Edit username" → fails
- "Disable account" → fails (and worse: Firebase `updateUser({disabled:true})`
  runs FIRST and succeeds, THEN the DB write throws — leaving Firebase and the
  profile row **out of sync**: user is disabled in Firebase but still `active`
  in the profile).
- "Re-enable account" → fails (same split-brain risk in reverse).

The user sees a red "Action failed" toast and nothing sticks. This is the
reported failure.

**Fix options (pick one, Antigravity decides):**
- (A) Add the column: migration `ALTER TABLE public.profiles ADD COLUMN updated_at TIMESTAMPTZ DEFAULT now();` — preferred; `updated_at` is genuinely useful and the code already wants it. Surgical migration only (per N.4 — never bulk migrate.ts).
- (B) Remove the `updated_at=now()` line from the PATCH route.
- Recommended: **(A)** + reorder the disable/enable path so the **DB write commits before** the Firebase `updateUser` call (or wrap so a Firebase success with DB failure rolls Firebase back), to kill the split-brain window.

### BUG-2 (LOW) · phantom `'admin'` role in nav
`MobileNavSheet.tsx` line 45: `roles: ['super_admin', 'admin']`. There is no
`admin` role in the schema (`guest | super_admin` only). Harmless today but it is
a latent lie; drop `'admin'`.

### GAP-1 · reset links are copy-paste only
`send-reset/route.ts` carries a `TODO: wire SMTP`. Today the super admin must
manually copy the Firebase reset URL out of a textarea and send it to the user
by hand. Functional but not "fully functional."

### GAP-2 · no audit trail
No record of who disabled/deleted/created whom or when. For a portal with real
user accounts this is the single biggest "feels unfinished" gap.

---

## §3 — Feature plan (what to build)

Framed from the perspective of **one super admin running this portal**. The bar:
relevant, not toy, not enterprise-bloat. Each item is tagged
**P0 (fix/ship)** · **P1 (clearly worth it)** · **P2 (nice, do if cheap)**.

### Tier P0 — make the existing tab actually work
1. **Fix BUG-1** (the `updated_at` migration + write-order). Without this the tab
   is broken; everything else is moot.
2. **Fix BUG-2** (drop phantom `'admin'` role).
3. **Firebase/DB consistency on disable/delete** — ensure the two stores never
   diverge (DB-first, or compensating rollback). Show a clear error if they do.

### Tier P1 — the features that make it genuinely useful
4. **Email the reset link automatically** (close GAP-1). Wire the existing SMTP/
   transactional path; fall back to the copy sheet only if send fails. Also add a
   one-click **"Send reset"** from the row that confirms "Sent to <email>" instead
   of surfacing a raw URL.
5. **Audit log** (close GAP-2). New table `admin_audit_log(id, actor_id,
   action, target_user_id, detail jsonb, created_at)`; write a row on every
   create/disable/enable/delete/role-change/reset. Surface as a simple reverse-
   chronological "Recent admin activity" panel at the bottom of the tab. This is
   the highest-leverage single addition.
6. **Change a user's role** (guest ↔ super_admin). Currently role is set only at
   creation; there is no way to promote/demote. Add to the PATCH route + a row
   action with a confirm ("Promote to super admin?"). Guard against removing the
   last super admin (count check — never let the admin lock themselves out).
7. **Resend / cancel a pending access request, and show request → user linkage.**
   The access-requests panel approves/rejects but there's no view of *who became
   which user*. Link `approved_user_id` through so an approved request shows the
   resulting account.
8. **Empty/error states that teach.** Replace bare "No users." / "Could not load
   users." with actionable copy (e.g. "Could not load users — check DB proxy" in
   dev). Small, but it's what "easy to use" means here.

### Tier P2 — worth it only if cheap
9. **Sort + filter by status/role** on the users table (client-side; data is tiny).
   A status filter chip row (All / Active / Disabled / Pending) is more useful
   than the current free-text search alone.
10. **Last sign-in column.** Firebase exposes `metadata.lastSignInTime`; pull it
    into the GET list so the admin can see dormant accounts. Read-only, cheap.
11. **Bulk select for disable/delete.** Only worth it once user count > ~20.
    Defer until it hurts.
12. **CSV export of the user list.** One button, trivial, occasionally handy for
    record-keeping. Low priority.

### Explicitly OUT of scope (deliberately not building)
- Granular RBAC / permission matrices — there are two roles; a matrix is bloat.
- Per-user activity dashboards, login heatmaps, session management UI — that's
  what the Observatory super-admin surface is for; don't duplicate it here.
- Self-service org/team management, invites-with-quota, SSO config — no second
  org exists. YAGNI.
- In-app messaging/notifications to users — out of band for a user-admin tab.

---

## §4 — Recommended build order (for the Antigravity session)

1. P0-1 migration + PATCH fix + write-order (the unblock).
2. P0-2, P0-3 cleanups.
3. P1-5 audit log (table + writes + panel) — do this early; later features write to it.
4. P1-6 role change (writes to audit log).
5. P1-4 email reset (writes to audit log).
6. P1-7 request→user linkage; P1-8 states.
7. P2 items only if time remains.

Each step = one discrete commit on `feature/admin-tab-overhaul`. Surgical
migrations only. Verify against **prod** (data-plane is always prod) per the
established `[verify-against: prod]` AC discipline, not a worktree DB.

---

## §5 — Open decisions for the native (resolve before/at build open)
- **D1.** Email transport for reset links — is there an existing SMTP/transactional
  sender in the codebase to reuse, or should the reset stay copy-paste for v1?
- **D2.** Should `updated_at` be added portal-wide as a profiles column (it's
  generally useful), or should the PATCH simply stop writing it? (Plan assumes ADD.)
- **D3.** Audit-log retention — keep forever, or prune after N months?
- **D4.** Confirm the two-role model is final (guest / super_admin) — the whole
  plan assumes no third role is coming.

---

*End ADMIN_TAB_AUDIT_AND_FEATURE_PLAN v1.0 — DRAFT. Implementation to be executed
by Claude Code in Antigravity on branch `feature/admin-tab-overhaul` after native
sign-off on §5.*
