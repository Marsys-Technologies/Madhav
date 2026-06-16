---
brief_id: EXEC_BRIEF_PORTAL_REDESIGN_R6_COCKPIT
version: 1.0
status: AUTHORED
authored_by: Cowork (Opus)
authored_at: 2026-04-30
target_executor: Claude Code (CLI), Sonnet 4.6 in Anti-Gravity / VS Code
trigger_phrase: "Read EXEC_BRIEF_PORTAL_REDESIGN_R6_COCKPIT_v1_0.md and execute it."
phase: Portal Redesign R6
phase_name: Cockpit elevation — promote to AppShell rail + Active Charts widget
parent_artifact: 00_ARCHITECTURE/PORTAL_REDESIGN_VISION_v1_0.md
tracker: 00_ARCHITECTURE/PORTAL_REDESIGN_TRACKER_v1_0.md
risk_classification: LOW
parallelizable_with: [R1, R2, R3, R5]
unblocks: [R7]
must_complete_before: [R7]
depends_on: [R0]
output_artifact: 00_ARCHITECTURE/PORTAL_REDESIGN_R6_REPORT_v1_0.md
---

# EXEC_BRIEF — Portal Redesign R6 — Cockpit elevation

## Mission

Promote the Cockpit (the super_admin governance application at `/cockpit`, freshly renamed from `/build` in R0) from "buried behind an avatar dropdown" to a first-class rail item in `<AppShell>`, and add one new widget to `<CockpitGrid>` — `<ActiveChartsWidget>` — that closes the loop between the governance side of the platform and the per-chart side. R6 does NOT change any Cockpit internals beyond this addition.

## Pre-flight gate

Halt if any fail.

1. R0 closed. `<AppShell>` exists; `/build → /cockpit` rename is live.
2. Vision exists; R6 row in TRACKER §3 reflects authored or earlier.
3. Working tree clean. Branch `redesign/r6-cockpit`.

## Scope declaration

```yaml
may_touch:
  - platform/src/components/shared/AppShell.tsx                      # narrow edit: rail item ordering if needed
  - platform/src/components/build/CockpitGrid.tsx                    # add <ActiveChartsWidget> tile
  - platform/src/components/build/ActiveChartsWidget.tsx             # NEW
  - platform/src/components/build/BuildHeader.tsx                    # narrow edit: cleanup
  - platform/src/lib/build/dataSource.ts                             # narrow edit: add active-charts query
  - tests/e2e/portal/cockpit-rail.spec.ts                            # NEW
  - tests/components/ActiveChartsWidget.test.tsx                     # NEW
must_not_touch:
  - 01_FACTS_LAYER/, 025_HOLISTIC_SYNTHESIS/, 03_DOMAIN_REPORTS/, 035_DISCOVERY_LAYER/
  - 04_REMEDIAL_CODEX/, 05_TEMPORAL_ENGINES/, 06_LEARNING_LAYER/, 99_ARCHIVE/
  - platform/migrations/, platform/supabase/migrations/
  - platform/python-sidecar/
  - platform/src/app/api/**                                          # no API change
  - platform/src/lib/db/types.ts
  - platform/src/lib/firebase/
  - platform/src/components/dashboard/, consume/, chat/              # other-phase scope
  - platform/src/components/build/CockpitGrid.tsx (other tiles)      # only ADD widget; don't reorganize
  - platform/src/components/build/JourneyStrip.tsx, BriefPanel.tsx, InsightCards.tsx, etc.  # untouched
  - platform/src/app/clients/[id]/**                                 # R2/R3/R4 scope
  - 00_ARCHITECTURE/CANONICAL_ARTIFACTS_v1_0.md
```

## §1 — AppShell rail promotion

R0 already added a `Cockpit` icon-link to `<AppShellRail>` for super_admin. R6's job is to verify it's there and prominent. If R0 rendered Cockpit below Admin and that ordering felt buried, swap to: Sigil → Roster → Cockpit → Admin → spacer → avatar. Capture rationale in closure report.

If R0 already shipped Cockpit-prominent, R6's rail edit is a no-op assertion.

## §2 — `<ActiveChartsWidget>`

Path: `platform/src/components/build/ActiveChartsWidget.tsx`. Tile on `<CockpitGrid>`. Renders top N active charts (default N=5) sorted by recent activity. Each row:

- Native name (link → `/clients/{id}` Chart Profile)
- Build % (small inline meter)
- Last activity (relative time)
- Health dot (same logic as R1's ClientCard health dot — green/amber/red)

**Data source:** small server helper `getActiveCharts({ limit: 5 })` in `platform/src/lib/build/dataSource.ts`. Queries `charts` joined with `pyramid_layers` and `conversations` (most recent of each). If join is expensive at scale, materialize via in-memory cache with 60s TTL (`platform/src/lib/cache/`).

Click-through: row navigates to `/clients/{id}` (Chart Profile, R2 deliverable). If R2 not yet closed when R6 lands, link still works — `/clients/{id}` will silently redirect (R2 hasn't replaced redirect yet) and user lands somewhere reasonable.

## §3 — `BuildHeader` cleanup

R0 already retired `BuildHeader`'s avatar in favor of `<AppShell>`'s. R6 verifies and tightens. If `BuildHeader` still hosts the avatar at R6 start, remove it. If R0 removed it, R6's edit is a no-op assertion.

`BuildHeader`'s post-R0+R6 role: render Cockpit's secondary nav strip (Cockpit, Plan, Sessions, Registry, Interventions, Parallel, Health, Activity) BELOW the AppShell breadcrumb. Two-row pattern: AppShell row + Cockpit-secondary-nav row.

## §4 — Tests

`tests/e2e/portal/cockpit-rail.spec.ts`: super_admin lands on /dashboard; clicks Cockpit rail link; lands on /cockpit; clicks Sigil; returns to /dashboard. Assert rail ordering.

`tests/components/ActiveChartsWidget.test.tsx`: renders with fixture of 5 charts; click on first row navigates to /clients/{id}.

Visual regression on /cockpit: before vs. after (only the new widget should be visible). Governance scripts exit 0.

## §5 — Closure report

`00_ARCHITECTURE/PORTAL_REDESIGN_R6_REPORT_v1_0.md`. Update TRACKER §3 R6 row to closed.

**R6 unblocks R7.** Closure report MUST include follow-up note: "R7 brief now authorable — polish pass scope is now fully defined by what landed in R0–R6."

## §6 — Out of scope

- Do NOT modify any Cockpit internals beyond adding the new widget.
- Do NOT reorganize the `<CockpitGrid>` layout.
- Do NOT touch `JourneyStrip`, `BriefPanel`, `InsightCards`, etc. — R3 owns the per-client Build composition.
- Do NOT add a server-side route for active-charts; reuse existing data path.

## §7 — One-line summary

Make the Cockpit a first-class destination from anywhere in the app, plus surface live links into per-chart profiles via one new widget.

---

*End of EXEC_BRIEF_PORTAL_REDESIGN_R6_COCKPIT_v1_0.md (AUTHORED, re-authored 2026-04-30 after surgical-fix data loss).*
