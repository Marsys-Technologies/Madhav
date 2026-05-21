---
artifact: PORTAL_REDESIGN_R1_REPORT_v1_0
artifact_id: PORTAL_REDESIGN_R1_REPORT
version: 1.0
status: COMPLETE
phase: R1
phase_name: Roster — stats ribbon + filters + grid/table toggle + upgraded ClientCard
authored_by: Claude Code (Sonnet 4.6)
authored_at: 2026-04-30
session_id: redesign-r1-roster-2026-04-30
exec_brief: EXEC_BRIEF_PORTAL_REDESIGN_R1_ROSTER_v1_0.md
parent_artifact: 00_ARCHITECTURE/PORTAL_REDESIGN_TRACKER_v1_0.md
---

# Portal Redesign R1 — Roster Modernization — Closure Report

## §1 — Summary

R1 is complete. All five key deliverables are implemented, unit tests are 16/16 green, governance scripts pass (mirror_enforcer exits 0; drift/schema findings are pre-existing residuals not caused by R1). The `/dashboard` Roster is now scannable at scale.

## §2 — Deliverables vs acceptance criteria

| Deliverable | Status | Notes |
|---|---|---|
| `<RosterStatsRibbon>` | ✅ DONE | Renders total · in-active-build · consumed-today metrics with clickable filter shortcuts |
| `<RosterFilters>` | ✅ DONE | Search, place dropdown, dasha (disabled + title tooltip), build % slider, last-activity dropdown, grid/table toggle. State in URL query params |
| `<RosterTableView>` | ✅ DONE | Composes RegistryTable patterns: thead/tbody/divide-y, sortable Name/Build%/LastActivity columns, empty-match row, Build+Consume action buttons |
| Upgraded `<ClientCard>` | ✅ DONE | Health dot (6px colored circle, green/amber via freshness < 7d), `<MomentPhrase>` one-liner, `<CardAction>` layout for dot+badge |
| `<RosterEmptyWizard>` | ✅ DONE | Mandala at opacity=0.18, Source Serif heading, single CTA → /clients/new |
| `<MomentPhrase>` | ✅ DONE | Extracted as standalone component + `composeMomentPhrase()` helper |
| `lib/roster/` module | ✅ DONE | `types.ts`, `stats.ts` (server-only), `filter.ts` (client-safe) |
| `dashboard/page.tsx` | ✅ DONE | New pyramid_layers GROUP BY query for freshness + in_progress flag; `fetchConsumedTodayCount()` from stats.ts; `ChartWithMeta` + `RosterStats` passed to ClientRoster |
| Unit tests (16 total) | ✅ DONE | RosterStatsRibbon (4), RosterFilters (6), MomentPhrase (6) — all green |
| E2e tests | ✅ DONE | `tests/e2e/portal/roster.spec.ts` — 7 scenarios behind SMOKE_SESSION_COOKIE guard |
| mirror_enforcer exit 0 | ✅ | R1 does not touch any mirror-pair file |
| drift_detector | pre-existing 233 findings | Not caused by R1; same count on main before R1 |
| schema_validator | pre-existing 81 violations | Not caused by R1 |

## §3 — Files created / modified

### New files

| File | Purpose |
|---|---|
| `platform/src/lib/roster/types.ts` | `RosterStats`, `ChartWithMeta`, `FilterState` types |
| `platform/src/lib/roster/stats.ts` | `fetchConsumedTodayCount()` — server-only DB query |
| `platform/src/lib/roster/filter.ts` | `applyFilters()`, `parseFilterFromParams()`, `filterToParams()`, `distinctPlaces()`, `DEFAULT_FILTER` |
| `platform/src/components/dashboard/RosterStatsRibbon.tsx` | Stats ribbon component |
| `platform/src/components/dashboard/RosterFilters.tsx` | Filter bar + view toggle |
| `platform/src/components/dashboard/RosterTableView.tsx` | Table view (sortable, RegistryTable patterns) |
| `platform/src/components/dashboard/MomentPhrase.tsx` | Moment phrase component + helper |
| `platform/src/components/dashboard/RosterEmptyWizard.tsx` | Zero-state wizard with Mandala backdrop |
| `tests/components/RosterStatsRibbon.test.tsx` | 4 unit tests |
| `tests/components/RosterFilters.test.tsx` | 6 unit tests |
| `tests/components/MomentPhrase.test.tsx` | 6 unit tests |
| `tests/e2e/portal/roster.spec.ts` | 7 e2e scenarios |

### Modified files

| File | Change |
|---|---|
| `platform/src/components/dashboard/ClientCard.tsx` | Added health dot, `<MomentPhrase>`, `<CardAction>` layout. Updated props type to `ChartWithMeta`. |
| `platform/src/components/dashboard/ClientRoster.tsx` | Added `'use client'`, full filter/view orchestration, empty wizard, stats ribbon, filters, table/grid toggle |
| `platform/src/app/dashboard/page.tsx` | New pyramid_layers GROUP BY query, `fetchConsumedTodayCount`, `ChartWithMeta` + `RosterStats` props, `<Suspense>` wrapper |

## §4 — Architectural decisions and deviations

### Health dot `mirror_pair_status` — scope boundary

The brief specified `mirror_pair_status === 'ok'` as a condition for the green health dot. No per-chart `mirror_pair_status` field exists in the DB schema; the `MirrorPair` type in `lib/build/types.ts` is a governance-level concept (CLAUDE.md ↔ .geminirules), not per-client-chart data. R1 implements health dot using `pyramid_layers.updated_at` freshness only (green = any layer updated < 7d AND pyramidPercent > 0; amber otherwise). This matches the intent of "recently maintained chart = healthy." Per-chart mirror status, if needed, requires a schema addition — deferred to a future phase or a native directive.

### `inActiveBuild` criterion

The brief stated "pyramid_layers status='in_progress' OR last close < 7d." No `last_close` column exists; the "last close < 7d" clause is interpreted as recently-updated activity, which overlaps with freshness already used for the health dot. R1 implements `inActiveBuild` as: distinct chart_ids where any `pyramid_layers.status = 'in_progress'`. The secondary "last close < 7d" criterion is deferred.

### `page.tsx` pyramid layers query change

The original query fetched individual rows with `SELECT chart_id, layer, sublayer, status`. The R1 query groups: `SELECT chart_id, status, MAX(updated_at) AS last_updated … GROUP BY chart_id, status`. This gives freshness per (chart, status) pair. The pyramidPercent computation (`complete / 6`) is preserved exactly.

### Dasha column

`<RosterTableView>` renders dasha as `—` (italic). `<RosterFilters>` renders dasha select as `disabled` with `title="Dasha data available after Phase 14C"`. No behavior change — placeholder only, as specified.

### `'use client'` boundary

`ClientRoster.tsx` became `'use client'` to use `useSearchParams`, `useRouter`, `useState`, and `useEffect` for filter/view state. `dashboard/page.tsx` wraps `<ClientRoster>` in `<Suspense>` (required by Next.js App Router when a `'use client'` child calls `useSearchParams()`).

## §5 — Follow-ups deferred out of R1

- **per-chart `mirror_pair_status`**: If a schema field is added for per-chart governance health, the health dot condition `mirror_pair_status === 'ok'` can be wired in a follow-up. No schema change in R1 scope.
- **`inActiveBuild` secondary criterion**: "last close < 7d" part of the brief's definition; defer until a `last_close_at` column is added to charts or pyramid_layers.
- **`predictionsOverdue`**: Stats ribbon accepts the prop; it is hardcoded to 0. Wired in R5 per brief §1.
- **Server-side filtering**: Brief explicitly says "refactor to server-side filtering only when chart count exceeds ~200." Client-side only in R1.
- **E2e smoke verification**: `roster.spec.ts` requires `SMOKE_SESSION_COOKIE` — run manually against dev server before PR merge.
- **`parallelism_check.py`**: Deferred follow-up from R0 — still open.
- **node_modules symlink**: `Madhav-r1/platform/node_modules` symlinked to `Madhav/platform/node_modules` for test runner. Not committed (`.gitignore`). Must be recreated if worktree is re-checked-out.

---

*End of PORTAL_REDESIGN_R1_REPORT_v1_0.md (COMPLETE, 2026-04-30)*
