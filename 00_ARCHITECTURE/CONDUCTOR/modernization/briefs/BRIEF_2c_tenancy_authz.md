---
status: COMPLETE
unit: 2c
wave: 2
title: Multi-guest tenancy + one authorization brain (sets G2_authz_live)
stream: B
worktree: ../MadhavStreamB
blockedBy: [naming_ci]
sets_gate: G2_authz_live
on_red: rollback
file_fence: "shares the charts table with 2a — Conductor must NEVER run 2c and 2a concurrently"
---

## Context (self-contained)
The portal fuses owner and subject: `charts.client_id` is the chart's subject AND a Firebase login, and
`POST /api/clients` mints a Firebase user per chart (`route.ts:51/57`). Target (MASTER_PLAN §3): a guest owns
many charts; a client is birth-data, not a login; super-admin can share charts view-only. One
`authorizeChartAccess` governs web + MCP. This must land before tier-excision (G2 gates it).

## Scope (additive / strangler — never destructive)
- **Schema (additive):** add `charts.owner_id text` (the guest), keep `client_id` until reads migrate
  (backfill `owner_id` from `client_id` — they're the same Firebase UID today); add `charts.subject_name`;
  new `chart_grants(id, chart_id, principal_id, permission DEFAULT 'view', granted_by, granted_at)`. Migrate
  on the staging DB + staging→live swap pattern; column drops deferred to a post-cutover window.
- **Role rename:** `profiles.role` value `client` → `guest` (CHECK + every `role==='client'` read, e.g.
  `dashboard/page.tsx`); `super_admin` unchanged.
- **Authorization brain:** `platform/src/lib/auth/authorizeChartAccess.ts` — `super_admin` → all; `owner_id ==
  principal` → all; a `chart_grants` row → view-only (Profile/Consult/Panchang, no Build/edit/delete); else
  deny. Replace the inline `chart.client_id !== user.uid` check in `consume/route.ts` and route every
  per-chart web + MCP read through it.
- **Defense-in-depth:** Postgres **Row-Level Security** on `owner_id` behind the app check (Gemini keeper).
- **Stop minting a Firebase user per chart** in `POST /api/clients` (the owner/subject split removes the need).

## Acceptance criteria (all automated)
1. `npx vitest run platform/src/lib/auth/__tests__/authorize_chart_access.test.ts` green (the G2 gate):
   super_admin/all, owner/all, grant/view-only, none/deny.
2. Migration applies cleanly on the staging DB; `owner_id` backfilled = `client_id` for existing rows; RLS active.
3. **Click-through:** a guest session sees only owned + granted charts; a granted chart shows no Build button;
   a non-granted chart 403s (mounts the real dashboard/route, not prop-injection).
4. No `role==='client'` literal remains (grep); no new per-chart Firebase user is created on chart create.
5. No tier path is consulted for access (tier excision is Wave-3, but authz must not depend on tiers).

## must_not_touch
`platform/src/lib/retrieve/**` + the unified contract (2b owns), `platform/python-sidecar/**`, the `l25_*`
data-build tables (2a owns). Coordinate the charts-table migration so it does not collide with 2a.

## Commit cadence / rollback
Commits: (1) additive migration (owner_id/subject_name/chart_grants + RLS) on staging, (2) authorizeChartAccess
+ route wiring + role rename, (3) /api/clients change + tests. Rollback = revert code; the additive columns are
harmless if unused (drop only in the deferred window).
