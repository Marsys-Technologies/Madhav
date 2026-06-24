# Chart Sharing — Design Spec
**Date:** 2026-06-25  
**Status:** Approved by native  
**Feature:** Super-admin chart access management (grant / revoke chart visibility to guests)

---

## 1. Problem Statement

Super admins can see all charts on the platform. Guests can only see charts they created themselves. There is no mechanism for a super admin to share a platform chart with a specific guest. This feature adds that capability.

---

## 2. Existing Infrastructure (no changes needed)

The grant infrastructure is already fully built:

| Artifact | Location | Notes |
|---|---|---|
| `chart_grants` table | `migrations/001_baseline.sql` | `chart_id · principal_id · permission · granted_by · granted_at · UNIQUE(chart_id, principal_id)` |
| `authorizeChartAccess()` | `src/lib/auth/authorizeChartAccess.ts` | Already checks `chart_grants` for every chart view; returns `'all' \| 'view' \| 'deny'` |
| Grant API | `src/app/api/clients/[id]/grants/route.ts` | GET · POST (idempotent) · DELETE already work |

Nothing in the grant or authorization layer needs to change.

---

## 3. What Gets Built

### 3.1 Two new read-only API routes

**`GET /api/admin/charts`** — super_admin only  
Returns all charts on the platform with owner display name and total grant count.

Both new routes use `requireSuperAdmin` from `@/lib/auth/access-control` (not the inline version in the existing grants route). Guard pattern: `if (auth instanceof NextResponse) return auth`. All non-2xx responses use `res.*` from `@/lib/errors`.

```ts
// Response shape
{
  charts: Array<{
    id: string           // charts.id (UUID)
    name: string         // charts.name
    subject_name: string | null  // COALESCE(preferred_name, subject_name, name)
    birth_date: string   // charts.birth_date (ISO date)
    birth_place: string  // charts.birth_place
    owner_id: string
    owner_username: string | null
    owner_name: string | null
    grant_count: number  // total distinct principals granted
  }>
  // Note: lagna is omitted from the MVP. The fact_key path in chart_facts requires
  // verification against live ga_* writer output before it can be safely queried.
  // Add in a follow-up once the exact fact_category/fact_key values are confirmed.
}
```

SQL:
```sql
SELECT
  c.id, c.name,
  COALESCE(c.preferred_name, c.subject_name, c.name) AS subject_name,
  c.birth_date, c.birth_place,
  c.owner_id,
  p.id       AS owner_profile_id,
  p.username AS owner_username,
  p.name     AS owner_name,
  COUNT(g.id)::int AS grant_count
FROM charts c
LEFT JOIN profiles p ON p.id = c.owner_id
LEFT JOIN chart_grants g ON g.chart_id = c.id
GROUP BY c.id, p.id, p.username, p.name   -- p.id in GROUP BY makes username/name functionally dependent
ORDER BY c.created_at DESC
```

---

**`GET /api/admin/users/[id]/chart-grants`** — super_admin only  
Returns all platform charts annotated with whether the specified user (`[id]`) has a grant row.

```ts
// Response shape
{
  charts: Array<{
    id: string
    subject_name: string | null
    birth_date: string
    birth_place: string
    owner_id: string
    owner_username: string | null
    is_own: boolean      // owner_id === [id] — shown greyed out, no grant button
    granted: boolean     // chart_grants row exists for (chart_id, principal_id=[id])
    // grant_id is omitted: the existing DELETE endpoint takes ?principal_id=<uid>,
    // not a grant UUID — see §3.1 note below
  }>
}
```

SQL sketch:
```sql
SELECT
  c.id,
  COALESCE(c.preferred_name, c.subject_name, c.name) AS subject_name,
  c.birth_date, c.birth_place,
  c.owner_id,
  p.username AS owner_username,
  (c.owner_id = $1) AS is_own,
  (g.id IS NOT NULL) AS granted   -- grant_id not selected; DELETE uses ?principal_id, not a UUID
FROM charts c
LEFT JOIN profiles p ON p.id = c.owner_id
LEFT JOIN chart_grants g ON g.chart_id = c.id AND g.principal_id = $1
ORDER BY granted DESC, c.created_at DESC
```

**Grant / revoke call contract:**
- **Grant:** `POST /api/clients/[chartId]/grants` with body `{ principal_id: guestUid }`
- **Revoke:** `DELETE /api/clients/[chartId]/grants?principal_id=<guestUid>`  
  The DELETE endpoint identifies the row by `(chart_id, principal_id)`, not by a grant UUID. The `grant_id` field is therefore not returned by the read endpoint and not needed by the UI.

---

### 3.2 New UI components

#### `ChartsTab.tsx`
Split-panel component mounted as the fourth tab in `AdminClient.tsx`.

**Left panel — Guest list**
- Lists all active guests (from the existing users query, filtered `role = 'guest'`)
- Each row: username · email · gold badge showing granted chart count
- Selected guest is highlighted with gold border + background tint
- Clicking a guest fetches `/api/admin/users/[id]/chart-grants` and populates the right panel

**Right panel — Chart access panel**
- Header: `"<username>'s chart access"` · subtitle: `"N of M charts shared"` · search input
- Chart rows sorted: granted first (green tint), then ungranted (muted), then owned (greyed out)
- Each chart row shows: subject name (serif) · birth date · key chart indicators (lagna · Sun sign · Moon nakshatra · birth place)
- **Grant button** (ungranted): gold border, `"+ Grant access"` — instant toggle on click
- **Revoke button** (granted): green border, `"✓ Granted · Revoke"` — instant toggle on click
- **Own chart** (is_own): no button, muted italic label `"their own chart"`
- Search filters by subject name or birth place (client-side, no re-fetch)

**Interaction — instant toggle:**
1. Click grant/revoke → button enters loading state (spinner, disabled)
2. API call fires (POST or DELETE to existing grants endpoint)
3. On success → row re-renders in new state immediately (optimistic update confirmed)
4. On error → row reverts, `toast.error(detail ?? message)` shown

#### `AdminClient.tsx` (extended)
- Add `"Charts"` tab between `"Users"` and `"Audit Log"`
- Tab state driven by `?tab=` URL search param (replaces current local state)  
  Values: `pending | users | charts | audit`
- `ChartsTab` reads `?guest=<uid>` param on mount and auto-selects that guest

#### `UsersTable.tsx` (extended)
- Add `"✦ Manage chart access"` item to the Actions dropdown (above the separator before role change)
- On click: `router.push('/admin?tab=charts&guest=' + user.id)`

**"← from Users" breadcrumb:** When `?guest=` param is present in the URL, the right panel header shows a small muted chip `"← from Users"` linking back to `?tab=users`. Removed when the user manually selects a different guest.

---

### 3.3 Audit logging

Grant and revoke actions are already routed through the existing `/api/clients/[id]/grants` endpoints. Add `writeAuditLog` calls to those endpoints.

> **Auth note for implementer:** The grants route uses its own locally-defined `requireSuperAdmin` that returns `{ error: NextResponse | null, user }` — guard with `if (auth.error) return auth.error`. Do **not** import from `@/lib/auth/access-control` into that file. This differs from the two new `/api/admin/` routes (which use the canonical helper).

- Grant: `writeAuditLog(actorId, 'chart_grant', granteeId, { chart_id, chart_name })`
- Revoke: `writeAuditLog(actorId, 'chart_revoke', granteeId, { chart_id, chart_name })`

`targetUserId` (third argument) is the **grantee's** user ID — the guest gaining or losing access. `detail` carries chart identification. This mirrors the pattern used by `role_change` and `disable_user`.

Add both action strings to the `AuditAction` type in `src/lib/admin/audit.ts`.

---

## 4. Navigation Contract

| User action | URL | Effect |
|---|---|---|
| Click "Charts" tab directly | `/admin?tab=charts` | Charts tab, no guest pre-selected; right panel shows placeholder "Select a guest" |
| Click "Manage chart access" on a user | `/admin?tab=charts&guest=<uid>` | Charts tab, that guest auto-selected |
| Click a different guest in left panel | URL updates to `?tab=charts&guest=<new-uid>` | Right panel re-fetches for new guest |
| Browser Back from Charts (came from Users) | `/admin?tab=users` | Returns to Users tab |

---

## 5. Empty & edge states

| State | What the user sees |
|---|---|
| Guest list fails to load | Left panel: "Could not load guests." with a retry hint; right panel hidden |
| No guests exist yet | Left panel: "No guests yet — create one in the Users tab." Right panel: hidden |
| No guest selected | Right panel: centred placeholder "Select a guest to manage their chart access." |
| Guest has access to all charts | Right panel shows all rows green; subtitle "All charts shared" |
| No charts on platform | Right panel: "No charts on the platform yet." |
| Grant/revoke API error | Row reverts to prior state; `toast.error` with detail message |
| Search returns nothing | "No charts match…" inline message |

---

## 6. Files touched

| File | Change |
|---|---|
| `src/app/api/admin/charts/route.ts` | **NEW** — GET all platform charts |
| `src/app/api/admin/users/[id]/chart-grants/route.ts` | **NEW** — GET charts + grant status for one user |
| `src/app/api/clients/[id]/grants/route.ts` | **EXTEND** — add `writeAuditLog` on POST + DELETE |
| `src/lib/admin/audit.ts` | **EXTEND** — add `chart_grant` and `chart_revoke` to `AuditAction` |
| `src/components/admin/ChartsTab.tsx` | **NEW** — split-panel component |
| `src/components/admin/AdminClient.tsx` | **EXTEND** — add Charts tab, URL-param tab routing |
| `src/components/admin/UsersTable.tsx` | **EXTEND** — add "Manage chart access" dropdown item |
| `src/components/admin/types.ts` | **EXTEND** — add `AdminChart` and `AdminChartGrant` interfaces |

**No migrations needed.** `chart_grants` table already exists.

---

## 7. Design decisions & rationale

| Decision | Rationale |
|---|---|
| Instant toggle (no confirmation on grant or revoke) | Consistent with user's explicit choice during brainstorm; low risk — chart_grants can be toggled back in seconds |
| URL-param tab routing | Enables deep-linking from Users tab; browser Back works naturally; no extra state management |
| Reuse existing grants endpoints for write | Avoids duplicating grant logic; keeps auth checks in one place |
| Own charts greyed out with no button | Owner already has `'all'` permission via `authorizeChartAccess`; granting would be a no-op and confusing |
| Granted rows float to top, sorted | Fastest scan of what access the guest actually has |
| Grant count badge on left panel | At-a-glance awareness without opening each guest |
| "← from Users" breadcrumb chip | Orients the admin when they arrive via the user-first flow; disappears when they navigate manually |
