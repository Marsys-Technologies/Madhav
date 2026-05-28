---
status: COMPLETE
unit: 3.consult_nav
wave: 3
title: Role-gated navigation + per-chart pages + sharing UI
stream: B
worktree: ../MadhavStreamB
blockedBy: [2c]
on_red: rollback
---

## Context (self-contained)
With owner/subject + chart_grants + `authorizeChartAccess` live (2c), build the Experience layer
(MASTER_PLAN §4): role-gated dashboard, per-chart pages, chart switcher, sharing UI.

## Scope
- **Dashboard, role-gated:** guest sees **Roster + Panchang** only; super-admin adds **Cockpit, Audit,
  Performance, AI Ops, Admin** (all `requireSuperAdmin` on page + API). Stop auto-redirecting a single-chart guest.
- **Per-chart pages** under `/clients/[id]/`: **Profile** (at-rest identity + nav hub with Build/Consult/
  Panchang) · **Build** (live build DAG + per-asset verification + progress + Rebuild) · **Consult** (chat) ·
  **Panchang** (personalized). Granted (view-only) guests: Profile/Consult/Panchang only — **no Build button**.
- **Chart switcher** in header: persists selection, chart_id in URL, no silent context switch mid-conversation.
- **Sharing UI:** super-admin grant/revoke (writes `chart_grants`, view-only); revoke invalidates access.
- All access via `authorizeChartAccess` (2c) — never a tier check.

## Acceptance criteria (all automated)
1. **Click-through (mount, not prop-inject):** a guest session sees only owned + granted charts; a non-granted
   chart 403s; a granted chart shows no Build button; super-admin sees all + admin surfaces.
2. Chart switcher persists + reflects chart_id in URL.
3. Sharing UI grant/revoke writes/removes `chart_grants` rows; revoke blocks access on next request.
4. No tier/depth selector anywhere (consistent with tier excision).

## must_not_touch
`platform/src/lib/retrieve/**`, `platform/python-sidecar/**`, `platform/src/app/api/chat/consume/route.ts`
(gateway owns), `platform/src/lib/disclosure/**` (tier_excision owns), `chart_facts`/`l25_*` (2a).

## Commit cadence / rollback
Commits: (1) role-gated dashboard + nav, (2) Profile/Build/Consult/Panchang per-chart pages + switcher,
(3) sharing UI. Rollback = revert (frontend only; no data effect).
