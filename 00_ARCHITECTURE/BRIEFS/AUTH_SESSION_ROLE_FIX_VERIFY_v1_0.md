---
title: AUTH_SESSION_ROLE_FIX_VERIFY
version: 1.0
status: COMPLETE
verdict: PASS
date: 2026-06-19
author: Claude Code / verify session
branch: feature/prashna-embed-across-layers
---

# Auth-Session Role Fix — Live Verification Report

## Verdict: PASS

All three acceptance criteria met:
1. **Domain sweep PASS** — every `'client'→'guest'` change was a `profiles.role` sense; zero `client_id`/chart-subject references altered.
2. **Live signup PASS** — new non-admin signup returns HTTP 200 and creates `role='guest'` profile row in DB.
3. **L0 permission PASS** — that guest user builds L1–L5 (ALLOWED, 16 per-chart assets, zero global) and is 403 FORBIDDEN_L0 on brahmagyan.

---

## §1 — Domain Lane Sweep (regression risk check)

**Method:** Inspected the full `git diff HEAD` for all 21 production files and 6 test files changed. Confirmed every removed (`-`) line containing `'client'` was in the `profiles.role` sense.

**All removed `'client'` references were:**
| Pattern | Sense | Count |
|---|---|---|
| `role: 'super_admin' \| 'client'` (type union) | `profiles.role` ✅ | 12 |
| `'client'` as INSERT value / fallback (`?? 'client'`) | `profiles.role` ✅ | 7 |
| `access.role === 'super_admin' ? 'super_admin' : 'client'` | `profiles.role` ✅ | 3 |
| `useState<'client' \| 'super_admin'>('client')` | UI role picker ✅ | 2 |
| `<option value="client">client</option>` | UI role picker ✅ | 2 |
| `roles: ['super_admin', 'admin', 'client']` | nav role array ✅ | 2 |
| test mocks `role: 'client'` | `profiles.role` test ✅ | 5 |
| `export type Role = 'super_admin' \| 'client'` | `profiles.Role` type ✅ | 1 |

**`client_id` / chart-subject references — confirmed UNTOUCHED:**

```bash
$ git diff HEAD -- src/ | grep "^[-+].*client_id"
(no output — zero client_id lines changed)
```

```bash
$ grep -n "client_id" src/app/clients/\[id\]/layout.tsx \
    src/app/clients/\[id\]/page.tsx \
    src/app/clients/\[id\]/timeline/layout.tsx
layout.tsx:54:    OR c.client_id = $1
page.tsx:29:    client_id: string
page.tsx:30:  }>('SELECT id, name, ... client_id FROM charts WHERE id=$1', [id])
timeline/layout.tsx:21:  query<{ name: string; client_id: string }>('SELECT ... FROM charts WHERE id=$1', [id])
timeline/layout.tsx:28:  if (profile?.role !== 'super_admin' && chart.client_id !== user.uid) redirect('/dashboard')
```

**63 `client_id` references in production source — all intact.** The charts table retains `client_id` as a chart-subject/ownership column; the rename touched only `profiles.role`.

**One missed straggler caught during sweep:**
`ApproveDialog.tsx` line 99 had `<option value="client">client</option>` still present after the `replace_all` edit. Found during diff review and fixed (changed to `value="guest"`). tsc confirmed clean after fix.

---

## §2 — Live Signup (the actual 500 bug)

**Setup:** Brand-new Firebase user created via Identity Toolkit REST API. UID had no existing `profiles` row.

**New user:**
- Email: `verify-auth-fix-1781812359@test-madhav.invalid`
- UID: `gLwXk0xQ4mddauSuJdKq9XMEcUp1`
- Not the SUPER_ADMIN_EMAIL

**Request:**
```
POST http://localhost:3000/api/auth/session
Content-Type: application/json
{"idToken": "<firebase-idToken>"}
```

**Response:**
```
HTTP/1.1 200 OK
{"ok":true}
```

**DB row created:**
```
SELECT id, role, status, email, created_at FROM profiles WHERE id='gLwXk0xQ4mddauSuJdKq9XMEcUp1';

              id              | role  | status |                     email                      |          created_at
------------------------------+-------+--------+------------------------------------------------+-------------------------------
 gLwXk0xQ4mddauSuJdKq9XMEcUp1 | guest | active | verify-auth-fix-1781812359@test-madhav.invalid | 2026-06-18 19:53:21.139113+00
```

**`role='guest'`** — correct. Previously this INSERT would have written `role='client'`, which the CHECK constraint would reject → HTTP 500.

**DB constraint confirmed:**
```sql
SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint
WHERE conrelid='profiles'::regclass AND contype='c';

       conname         |                            definition
-----------------------+-------------------------------------------------------
 profiles_role_check   | CHECK ((role = ANY (ARRAY['guest'::text, 'super_admin'::text])))
 profiles_status_check | CHECK ((status = ANY (ARRAY['pending'::text, 'active'::text, 'disabled'::text])))
```

**No migration needed** — constraint already `['guest','super_admin']`. The code was the laggard.

---

## §3 — L0 Permission Regression (with the freshly-created guest)

Both tests used the session cookie minted for UID `gLwXk0xQ4mddauSuJdKq9XMEcUp1` (role=guest) against chart `482012f1-710e-4a25-994a-93821f5871aa`.

### Test A: scope=layer/ganita → ALLOWED

```
POST /api/cockpit/runs
Cookie: __session=<guest-cookie>
{"chart_id":"482012f1-...","scope":"layer","scope_target":"ganita","action":"rebuild"}

HTTP 200
{
  "data": {
    "run_id": "a04e2c81-0857-49e9-b458-1cd331f05dc8",
    "plan": [
      "ga_positions","ga_vargas","ga_dashas","ga_strength",
      "ga_sensitive","ga_panchanga","ga_prashna","ga_structural",
      "ga_sade_sati","ga_tajaka","ga_nakshatra","ga_yoga",
      "ga_condition","ga_vastu","ga_transit_anchors","ga_medical"
    ],
    "asset_count": 16
  }
}
```

**16 assets, ALL `ga_*` (per-chart scope). ZERO `bg_*` / global assets.** The `allowedRegistry` filter (`scope IN ('per_chart')` for non-super-admin) silently excluded all L0/global assets before plan resolution.

(Note: `action=build` returned HTTP 422 "No assets to build" because all ganita assets were already current — this is correct behavior: auth PASSED, plan was empty because nothing was stale. `action=rebuild` forces a rebuild and confirms the plan shape.)

### Test B: scope=layer/brahmagyan → 403 FORBIDDEN_L0

```
POST /api/cockpit/runs
Cookie: __session=<guest-cookie>
{"chart_id":"482012f1-...","scope":"layer","scope_target":"brahmagyan","action":"build"}

HTTP 403
{"error":"Only super_admin can build L0 Brahmagyan layer","code":"FORBIDDEN_L0"}
```

**Exact FORBIDDEN_L0 gate confirmed.** `isSuperAdmin` resolves correctly for `role='guest'`.

---

## §4 — Chart-Subject Domain Intact

The `client_id` column on the `charts` table is a chart-ownership/subject column — completely separate from `profiles.role`. Confirmed live:

```sql
SELECT id, name, client_id, owner_id FROM charts LIMIT 4;

          name           |          client_id           |          owner_id
-------------------------+------------------------------+------------------------------
 Abhisek Mohanty         | xl2wYZRPwsVgPSAgtn9XJ80Xkub2 | xl2wYZRPwsVgPSAgtn9XJ80Xkub2
 Abhinandan Mohanty      | xl2wYZRPwsVgPSAgtn9XJ80Xkub2 | xl2wYZRPwsVgPSAgtn9XJ80Xkub2
 Kiran Shenoy            | xl2wYZRPwsVgPSAgtn9XJ80Xkub2 | xl2wYZRPwsVgPSAgtn9XJ80Xkub2
 Arunima Samantray       | xl2wYZRPwsVgPSAgtn9XJ80Xkub2 | xl2wYZRPwsVgPSAgtn9XJ80Xkub2
```

`client_id` values intact. The column, its SQL queries, and all chart-ownership logic were untouched by this change.

---

## §5 — Files Changed Summary

**21 production files, 6 test files.** Every `'client'→'guest'` change was a `profiles.role` sense.

| File | Change |
|---|---|
| `src/lib/db/types.ts` | `Role = 'super_admin' \| 'guest'` |
| `src/app/api/auth/session/route.ts` | Type union + INSERT `'guest'` (the 500 fix) |
| `src/lib/auth/access-control.ts` | `ProfileAuth.role` type |
| `src/app/api/admin/access-requests/[id]/approve/route.ts` | Interface, fallback, SQL INSERT |
| `src/app/api/admin/users/route.ts` | Interface + fallback |
| `src/app/api/cockpit/clear/route.ts` | `?? 'guest'` fallback |
| `src/app/api/cockpit/clear/execute/route.ts` | `?? 'guest'` fallback |
| `src/app/api/cockpit/runs/route.ts` | `?? 'guest'` fallback |
| `src/app/api/me/role/route.ts` | `?? 'guest'` fallback |
| `src/app/api/panchang/charts/route.ts` | `?? 'guest'` fallback |
| `src/app/clients/[id]/layout.tsx` | Ternary result |
| `src/app/clients/[id]/page.tsx` | Ternary result |
| `src/app/clients/[id]/timeline/layout.tsx` | Cast + fallback |
| `src/components/admin/types.ts` | `AdminUser.role` type |
| `src/components/admin/NewUserDialog.tsx` | State type, onChange cast, option value |
| `src/components/admin/ApproveDialog.tsx` | State type, onChange cast, option value |
| `src/components/shared/AppShell.tsx` | Prop type |
| `src/components/shared/AppShellRail.tsx` | Prop type |
| `src/components/shared/MobileNavSheet.tsx` | Prop type + nav roles array |
| `src/components/profile/ProfileSideRail.tsx` | Prop type |
| `tests/components/AppShell.test.tsx` | Test assertions |
| `src/app/cockpit/__tests__/command_center.test.ts` | Test mock |
| `src/__tests__/lib/admin/trace_route.test.ts` | Test mock |
| `src/app/dashboard/__tests__/dashboard.test.tsx` | setProfile type + test call |
| `src/lib/components/observatory/__tests__/AuthGate.test.tsx` | Test mock |
| `src/lib/components/cockpit/v2/__tests__/LayerPanel_L0Gate.test.tsx` | Test mocks (×4) |

**tsc:** 0 errors. **Vitest:** 398 files passed, 4552 tests passed, 0 failures.

---

## §6 — Notes

- **No DB migration required.** `profiles_role_check` already constrains to `['guest','super_admin']`. The bug was entirely code-side.
- **`AppShellRail` retains `'client'` in its `roles[]` array** (alongside `'guest'`) for the transition period. The `normalizeRole()` function maps any legacy stored `'client'` value → `'guest'` at render time. This is harmless and intentional backward-compat for any profiles that might have been created before this fix.
- **Guest chart-build scope gate is authorization by role, not chart ownership.** A guest user can currently trigger a build of any chart they know the ID of (not just their own). This is a pre-existing design characteristic of the cockpit — not introduced by this fix — and is appropriate for the single-native instrument use case.
