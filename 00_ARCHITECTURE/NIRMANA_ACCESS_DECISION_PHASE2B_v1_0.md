---
artifact: NIRMANA_ACCESS_DECISION_PHASE2B_v1_0.md
canonical_id: NIRMANA_ACCESS_DECISION_PHASE2B
version: 1.0
status: ACTIVE
authored_by: Claude (Cowork) 2026-06-25
parent: NIRMANA_REMAINING_THREADS_PHASED_BRIEF_v1_0.md
purpose: >
  Phase 2B implementation — the native ruled on the Nirmāṇa build-access policy. Decision:
  BUILD = owner or super_admin ONLY; view-grantees are READ-ONLY and see the Nirmāṇa affordance
  DISABLED with a reason (not a silent redirect). This reverses the over-broad ae9a4634 behavior and
  restores the documented 'view = read-only' contract.
audience: Claude Code (Antigravity)
---

# Phase 2B — Nirmāṇa access: owner/admin-only build, viewer sees disabled+reason

## §0 — Decision (native, 2026-06-25)
- **Build (Nirmāṇa) = `owner_id` match OR `super_admin` only.** A `chart_grants` 'view' grant is
  READ-ONLY: Profile / Consult / Panchang, NO build. This matches `authorizeChartAccess.ts`'s own
  documented contract ("'view' grants Profile/Consult/Panchang read-only — Build/edit/delete reject").
- **Viewer UX:** a view-grantee sees the Nirmāṇa affordance **disabled with a 'view-only — build
  restricted' reason** — never a silent bounce to Consult.
- **Nava Jātaka** stays super_admin-only (unchanged).
- This is NOT the product expansion (subjects owning charts) — that is a separate future workstream.

## §1 — Diagnosis recap (already confirmed on prod)
1c826d5a is owned by the super_admin (owner_id = xl2wYZRPwsVgPSAgtn9XJ80Xkub2); the non-admin user is a
`view` grantee (EiThXD5YRPfzwfoAtYeGDXHxsTv2). Commit `ae9a4634` changed `canBuild` to
`permission !== 'deny'`, which let view-grantees build — too broad. We are reverting that semantic.

## §2 — Code changes
2.1 — `platform/src/lib/auth/chart-page-guard.ts`: restore `canBuild = (permission === 'all')`
  (revert the ae9a4634 `permission !== 'deny'` relaxation). 'all' = owner or super_admin only.

2.2 — `platform/src/app/clients/[id]/nirmana/page.tsx`: it currently `redirect('/clients/${id}')` when
  `!access.canBuild`. KEEP a guard (a view-grantee must not reach the build instrument), but the
  primary "don't look broken" fix is in the dashboard affordance (2.3) so users don't click into a
  bounce in the first place. Leave the server guard as a redirect (defense in depth) OR render a
  minimal "view-only — build restricted" page for permission==='view' (your call; the affordance fix
  is what the user actually sees). Do NOT let a 'view' user run any build control.

2.3 — Dashboard per-chart Nirmāṇa affordance — the user-visible fix. The Nirmāṇa link is rendered per
  chart in `platform/src/components/dashboard/ClientCard.tsx` (grid) and
  `platform/src/components/dashboard/RosterTableView.tsx` (table). For each chart the dashboard must
  know the viewer's permission on THAT chart:
  - In `dashboard/page.tsx`, the roster query already returns owned ∪ granted charts. Compute a
    per-chart `canBuild` for the current user: `true` if role==='super_admin' OR chart.owner_id===uid;
    `false` if the chart is present only via a chart_grants 'view'. Pass it to the card/row.
  - In ClientCard + RosterTableView: when `canBuild===false`, render the Nirmāṇa control DISABLED
    (not a link) with an accessible reason — tooltip/aria-label "View-only — build restricted". The
    Vimarśa (Consult) link stays enabled. Keep the visual consistent with the existing disabled-state
    styling.

2.4 — Tests:
  - Guard unit test (`lib/auth/__tests__`): the access matrix — super_admin→'all'(canBuild true);
    owner→'all'(true); view-grantee→'view'(canBuild FALSE); other→'deny'(false).
  - Dashboard/component test: a view-grantee chart renders the Nirmāṇa affordance disabled with the
    reason; an owned/admin chart renders it enabled.
  - Confirm no existing test asserted the ae9a4634 `permission !== 'deny'` behavior; if one does, update
    it to the restored contract.

2.5 — `cd platform && npm run typecheck && npm test` green. COMMIT:
  `fix(auth): build is owner/super_admin only; view-grantees read-only with disabled Nirmāṇa affordance (revert ae9a4634 over-broad canBuild)`

## §3 — Verify (Chrome MCP, after deploy)
As the view-grantee (the guest profile), on the dashboard: the Nirmāṇa control on 1c826d5a is disabled
with the 'view-only — build restricted' reason, Vimarśa works, and directly visiting
`/clients/1c826d5a-.../nirmana` does NOT expose a usable build instrument. As super_admin: Nirmāṇa works
normally. Screenshot both. (Use a real second session/account if available; otherwise assert via the
guard/component tests + a DB-permission-driven render check.)

## §4 — Guardrails
- This is a permission tightening — make sure it does NOT lock the super_admin or a real owner OUT.
  The acceptance is: owner/admin CAN build; view-grantee CANNOT and sees why.
- No data changes; purely auth + UI. Native 482012f1 untouched.
- Independent of the in-flight ga_dashas build — can land anytime; no rebuild needed.
