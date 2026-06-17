---
brief_id: EXEC_BRIEF_PORTAL_REDESIGN_R1_ROSTER
version: 1.0
status: AUTHORED
authored_by: Cowork (Opus)
authored_at: 2026-04-30
target_executor: Claude Code (CLI), Sonnet 4.6 in Anti-Gravity / VS Code
trigger_phrase: "Read EXEC_BRIEF_PORTAL_REDESIGN_R1_ROSTER_v1_0.md and execute it."
phase: Portal Redesign R1
phase_name: Roster — stats ribbon + filters + grid/table toggle + upgraded ClientCard
parent_artifact: 00_ARCHITECTURE/PORTAL_REDESIGN_VISION_v1_0.md
tracker: 00_ARCHITECTURE/PORTAL_REDESIGN_TRACKER_v1_0.md
risk_classification: LOW
parallelizable_with: [R2, R4, R5, R6]
must_complete_before: [R7]
depends_on: [R0]
output_artifact: 00_ARCHITECTURE/PORTAL_REDESIGN_R1_REPORT_v1_0.md
---

# EXEC_BRIEF — Portal Redesign R1 — Roster modernization

## Mission

Modernize `/dashboard` (the Roster) so a 10-client roster is as scannable as a 1-client roster. Land four additions on top of the existing `<ClientRoster>` + `<ClientCard>` flow: a top stats ribbon, a search-and-filter row, a grid/table view toggle, and an upgraded `<ClientCard>` carrying a one-line "moment phrase" plus a freshness health dot. Add a brand-styled zero-state wizard for empty rosters.

This phase is parallelizable with R2, R4, R5, R6 — none of them touch `/dashboard` or `components/dashboard/*`.

## Pre-flight gate

Halt if any fail.

1. R0 is closed. `<AppShell>` and `<ZoneRoot>` exist and `/dashboard` already renders inside `<AppShell>`.
2. `00_ARCHITECTURE/PORTAL_REDESIGN_VISION_v1_0.md` exists.
3. The R1 row in `00_ARCHITECTURE/PORTAL_REDESIGN_TRACKER_v1_0.md §3` reflects `status: authored` (or earlier — start work flips it to in_flight).
4. Working tree clean. Branch `redesign/r1-roster`.

## Scope declaration

```yaml
may_touch:
  - platform/src/app/dashboard/page.tsx                              # add stats fetch + view-toggle wrapper
  - platform/src/components/dashboard/ClientRoster.tsx               # accept new view-mode prop
  - platform/src/components/dashboard/ClientCard.tsx                 # add MomentPhrase + health dot
  - platform/src/components/dashboard/RosterStatsRibbon.tsx          # NEW
  - platform/src/components/dashboard/RosterFilters.tsx              # NEW
  - platform/src/components/dashboard/RosterTableView.tsx            # NEW (composes build/RegistryTable patterns)
  - platform/src/components/dashboard/MomentPhrase.tsx               # NEW
  - platform/src/components/dashboard/RosterEmptyWizard.tsx          # NEW (zero-state)
  - platform/src/lib/roster/                                         # NEW directory for stats/filter helpers
  - tests/e2e/portal/roster.spec.ts                                  # NEW
  - tests/components/RosterStatsRibbon.test.tsx                      # NEW
  - tests/components/RosterFilters.test.tsx                          # NEW
  - tests/components/MomentPhrase.test.tsx                           # NEW
must_not_touch:
  - 01_FACTS_LAYER/, 025_HOLISTIC_SYNTHESIS/, 03_DOMAIN_REPORTS/, 035_DISCOVERY_LAYER/
  - 04_REMEDIAL_CODEX/, 05_TEMPORAL_ENGINES/, 06_LEARNING_LAYER/, 99_ARCHIVE/
  - platform/migrations/, platform/supabase/migrations/
  - platform/python-sidecar/
  - platform/src/app/api/**                                          # no API change
  - platform/src/lib/db/types.ts                                     # types read; not modified
  - platform/src/components/shared/AppShell.tsx                      # R0 scope
  - platform/src/app/clients/[id]/**                                 # R2/R3/R4 scope
  - platform/src/components/build/, consume/, chat/                  # other-phase scope
  - 00_ARCHITECTURE/CANONICAL_ARTIFACTS_v1_0.md
```

## §1 — `<RosterStatsRibbon>`

Path: `platform/src/components/dashboard/RosterStatsRibbon.tsx`. A horizontal strip rendered above the cards/table. Vellum-zone styled. Pulls four counts (passed in as props):

```ts
interface RosterStatsRibbonProps {
  total: number;
  inActiveBuild: number;        // pyramid_layers status='in_progress' OR last close < 7d
  consumedToday: number;        // conversations created today
  predictionsOverdue: number;   // pass 0 in R1; segment hidden if 0 — R5 wires this up
}
```

Format: "5 charts · 2 in active build · 3 consumed today" with each metric a clickable filter shortcut that pre-fills `<RosterFilters>`.

## §2 — `<RosterFilters>`

Path: `platform/src/components/dashboard/RosterFilters.tsx`. Controlled component above the cards/table. Filter controls: free-text search (matches name, birth_place, current dasha if available); birth-place dropdown (distinct values); current dasha dropdown (disabled with tooltip if dasha not yet exposed via Phase 14C tables); build % range slider; last activity dropdown.

State lives in URL query params (`?q=&place=&dasha=&buildMin=&buildMax=&since=`). Filter logic runs client-side in R1 — page fetches all visible charts (already does), `<ClientRoster>` filters in-memory. Refactor to server-side filtering only when chart count exceeds ~200.

## §3 — Grid/Table view toggle

`<ViewToggle>` segmented control to the right of `<RosterFilters>`: Grid | Table. State persisted to `localStorage` (`marsys.roster.view = 'grid' | 'table'`).

`<ClientRoster>` accepts `view: 'grid' | 'table'` and renders either the existing card grid or the new `<RosterTableView>`.

`<RosterTableView>` composes table primitives from `platform/src/components/build/RegistryTable.tsx`. DO NOT duplicate logic — lift shared parts into `lib/ui/table-primitives.ts` if needed. Columns: Name, Birth (date · place), Current dasha, Build %, Last activity, Actions (Build / Consume buttons).

## §4 — Upgraded `<ClientCard>`

Edit `platform/src/components/dashboard/ClientCard.tsx`. Two additions:

**Moment phrase**: one-line summary between birth-meta line and action buttons. Helper `composeMomentPhrase(chart, lastActivity, currentDasha)` returns strings like "Saturn–Jupiter · last queried 4d ago". If neither dasha nor activity is known, render the existing badge alone.

**Health dot**: 6px colored dot top-right next to the % badge. Green when `freshness < 7d AND mirror_pair_status === 'ok'`; amber when stale or known-residuals; red when mirror desync or build error. Server-evaluated in `dashboard/page.tsx`.

Primary CTA change deferred to R2. R1 leaves the Build / Consume buttons as-is.

## §5 — `<RosterEmptyWizard>`

Zero-state. Mandala backdrop at low opacity (reuse `platform/src/components/brand/Mandala.tsx`). Heading "Welcome. Begin with your first chart." Single CTA → `/clients/new`. Replaces the current text-only empty state.

## §6 — Tests

- `tests/e2e/portal/roster.spec.ts`: super_admin lands with seeded fixtures (3 charts, varied build %); asserts stats ribbon counts; tests search filter; tests grid/table toggle; tests view persistence; tests deep-link with query params.
- Unit tests for the three new components (RosterStatsRibbon, RosterFilters, MomentPhrase).
- Visual regression on /dashboard.
- Governance: `mirror_enforcer.py` / `drift_detector.py` / `schema_validator.py` exit 0 (R1 doesn't touch any mirror-pair file).

## §7 — Closure report

`00_ARCHITECTURE/PORTAL_REDESIGN_R1_REPORT_v1_0.md` with `status: COMPLETE`. Update `PORTAL_REDESIGN_TRACKER_v1_0.md §3` R1 row to `status: closed` with `session_id`, `closed_at`, `follow_ups`. Append SESSION_LOG entry.

## §8 — Out of scope

- Do NOT change `clients/[id]/page.tsx` or any per-client surface — R2's job.
- Do NOT change ClientCard's primary click target — R2's job.
- Do NOT introduce server-side filtering — defer until chart count warrants.
- Do NOT touch the Cockpit's `RegistryTable` — borrow patterns, don't modify.

## §9 — One-line summary

Make the Roster scannable at scale by composing existing table primitives, brand assets, and per-card helpers into a search-and-filter shell over the existing card grid.

---

*End of EXEC_BRIEF_PORTAL_REDESIGN_R1_ROSTER_v1_0.md (AUTHORED, re-authored 2026-04-30 after surgical-fix data loss).*
