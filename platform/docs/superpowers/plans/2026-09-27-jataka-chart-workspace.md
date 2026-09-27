# Jātaka Chart Workspace and Safe Recompute Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace dashboard action-heavy chart cards with a quiet Jātaka directory, make `/clients/[id]` the chart workspace, and add a safe edit-and-recompute operation that preserves chart identity while invalidating old derived results and archiving prior Paripraśna history read-only.

**Architecture:** One shared server-side readiness resolver supplies the dashboard, chart workspace, and Paripraśna availability gate. A chart-update domain service validates and classifies changes; display-only edits update directly, while computation-affecting edits run one strict PostgreSQL transaction that archives conversations, updates chart inputs, clears governed derived data, resets throughput, and creates a frozen rebuild run. Existing cockpit build logic is first extracted into focused server-only preparation, clearing, persistence, and dispatch helpers so the edit endpoint and cockpit use the same planner and manifest rules without changing the frozen Python orchestrator.

**Tech Stack:** Next.js 16.2 App Router, React 19.2, TypeScript 5, PostgreSQL through `pg`, Zod 4, Vitest 4 + Testing Library, Playwright 1.59, Tailwind 4, existing Marsys brand tokens and Paripraśna visual patterns, existing Python pipeline orchestrator invoked locally through `BUILD_EXECUTOR=local`.

**Spec:** `platform/docs/superpowers/specs/2026-09-27-jataka-chart-workspace-design.md`

## Global Constraints

- Work only in `/Users/Dev/.codex/worktrees/jataka-chart-workspace/Madhav` on branch `codex/jataka-chart-workspace`; the design baseline is commit `bf604c39b`.
- Do not implement in `/Users/Dev/Vibe-Coding/Apps/Madhav`; that shared checkout was intentionally left untouched.
- Before changing code, read root `CLAUDE.md` in full, follow its mandatory-reading sequence and session-open protocol, then read root `AGENTS.md`, `platform/AGENTS.md`, this plan, and the linked design specification.
- After `npm ci`, read the relevant Next.js 16 guides under `platform/node_modules/next/dist/docs/` before changing App Router pages or handlers.
- Local-only means: no deployment, push, merge, production migration, production database write, Cloud Run dispatch, or real-user chart correction.
- Use a disposable local PostgreSQL database. Stop if `DATABASE_URL` points to a non-local host.
- Set `BUILD_EXECUTOR=local` for end-to-end recompute proof. Never remove that guard to make local testing easier.
- Do not change `platform/python-sidecar/**`, the frozen orchestrator contract, writer contracts, Jyotish computations, or governed asset definitions.
- Keep chart UUID, `owner_id`, `client_id`, `chart_grants`, consent, manually entered life events, recorded outcomes, answered journal rows, and global audit/export material intact.
- Server-side normalized comparison is authoritative. Client-side change detection exists only to choose copy and confirmation behaviour.
- A preparation or clear failure must roll back every chart/conversation/run mutation. A post-commit dispatch failure must leave corrected inputs committed, old derived data absent, the run failed, and the UI in `Needs rebuild`.
- Paripraśna conversations archived because chart details changed are readable but immutable; manual archives with no correction reason retain their existing semantics.
- Reuse Marsys ceremonial tokens and Paripraśna's visual principles; do not apply the scoped `.pp-root` shell outside Paripraśna.
- Preserve accessibility: one semantic link per dashboard card, visible focus, text state beside progress, 44px coarse-pointer targets, dialog focus return, reduced motion, and readable mobile D1 ordering.
- Use test-driven development and make the commits listed below. Do not combine tasks into one large commit.

---

## Executor Environment

### Required checkout

```bash
cd /Users/Dev/.codex/worktrees/jataka-chart-workspace/Madhav
git branch --show-current
git status --short
git log -1 --oneline
```

Expected before implementation:

```text
codex/jataka-chart-workspace
<clean status>
bf604c39b docs: design Jataka chart workspace and safe recompute
```

If the branch, cleanliness, or design commit differs, stop and reconcile that state before editing. Do not reset or discard someone else's changes.

### JavaScript dependencies

```bash
cd /Users/Dev/.codex/worktrees/jataka-chart-workspace/Madhav/platform
npm ci
npm run guard:migration-numbers
npm run migration:next
```

At the recorded baseline, the highest migration number across both migration directories is `1079`, so the planned migration filename is `platform/supabase/migrations/1080_jataka_conversation_archive_context.sql`. The migration guard remains authoritative; if it reports a different next number before the migration is created, use that reported number and update every reference in this plan in the same commit.

### Local secrets and runtime safety

Use an ignored `platform/.env.local` configured for local resources. It must include the existing application auth settings plus these local execution values:

```dotenv
DATABASE_URL=postgresql://<local-user>:<local-password>@127.0.0.1:<local-port>/<disposable-database>
BUILD_EXECUTOR=local
MARSYS_REPO_ROOT=/Users/Dev/.codex/worktrees/jataka-chart-workspace/Madhav
LOCAL_PYTHON_PATH=/absolute/path/to/a-compatible-venv/bin/python
PARIPRASHNA_ENABLED=true
NEXT_PUBLIC_PARIPRASHNA_LIVE=1
```

Do not print secret values. Verify only that the parsed database hostname is `localhost`, `127.0.0.1`, or `::1`. The Python interpreter may come from an existing compatible virtual environment, but `MARSYS_REPO_ROOT` must remain the isolated worktree so the local runner imports this branch's sidecar code.

### Local processes

```bash
# terminal 1
cd /Users/Dev/.codex/worktrees/jataka-chart-workspace/Madhav/platform
npm run dev

# terminal 2, only if the application flow requires the query sidecar
cd /Users/Dev/.codex/worktrees/jataka-chart-workspace/Madhav/platform/python-sidecar
"$LOCAL_PYTHON_PATH" -m uvicorn main:app --host 127.0.0.1 --port 8000
```

The rebuild route spawns the orchestrator itself when `BUILD_EXECUTOR=local`; do not manually start a second orchestrator for the same run ID.

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `platform/src/lib/charts/readiness.ts` | Create | Pure readiness state derivation plus batched server resolver used by dashboard/workspace/gates |
| `platform/src/lib/charts/__tests__/readiness.test.ts` | Create | Readiness state and aggregation contract |
| `platform/src/app/dashboard/page.tsx` | Modify | Replace inline readiness calculations with the shared resolver |
| `platform/src/components/dashboard/ClientCard.tsx` | Modify | Minimal single-link chart card |
| `platform/src/components/dashboard/RosterTableView.tsx` | Modify | Minimal roster row with no action or empty daśā columns |
| `platform/src/components/dashboard/__tests__/ClientCard.test.tsx` | Modify | Minimal-content and single-link assertions |
| `platform/src/components/dashboard/__tests__/RosterTableView.test.tsx` | Modify | No-action-column and accessible chart-link assertions |
| `platform/src/components/profile/ChartHero.tsx` | Modify | D1-first chart identity surface and secondary action trigger slot |
| `platform/src/components/profile/ChartReadinessBand.tsx` | Create | Shared-state workspace readiness band and six layer pips |
| `platform/src/components/profile/CapabilityCard.tsx` | Create | Extensible capability card with available/blocked state |
| `platform/src/components/profile/ChartActionsMenu.tsx` | Create | Permission-aware Edit/Sharing/Audit/Delete secondary actions |
| `platform/src/components/profile/__tests__/ChartReadinessBand.test.tsx` | Create | Textual states and layer accessibility tests |
| `platform/src/components/profile/__tests__/CapabilityCard.test.tsx` | Create | Permission and blocked-link behaviour |
| `platform/src/app/clients/[id]/page.tsx` | Modify | Compose D1 hero, readiness, capabilities, summaries, and secondary actions |
| `platform/supabase/migrations/1080_jataka_conversation_archive_context.sql` | Create | Add correction archive reason, immutable chart-input snapshot, and rebuild-run linkage |
| `platform/tests/unit/migrations/jataka_conversation_archive_context.test.ts` | Create | Additive/idempotent migration contract |
| `platform/src/lib/charts/types.ts` | Create | Shared normalized chart-input and historical snapshot types |
| `platform/src/lib/conversations.ts` | Modify | Expose archive metadata and correction-read-only helper |
| `platform/src/lib/build/runPreparation.ts` | Create | Shared registry/plan/manifest resolution and build-run persistence |
| `platform/src/lib/build/assetInvalidation.ts` | Create | Operator best-effort and correction strict invalidation policies |
| `platform/src/lib/build/runDispatch.ts` | Create | Dispatch plus failed-run/aborted-assets handling |
| `platform/src/lib/build/__tests__/runPreparation.test.ts` | Create | Plan, protected asset, manifest, active-run, and persistence tests |
| `platform/src/lib/build/__tests__/assetInvalidation.test.ts` | Create | Strict rollback signals and preservation boundary tests |
| `platform/src/app/api/cockpit/runs/route.ts` | Modify | Delegate existing orchestration to shared services without changing response contracts |
| `platform/src/app/api/cockpit/runs/__tests__/route.test.ts` | Modify | Characterize and preserve cockpit behaviour after extraction |
| `platform/src/lib/charts/updateChart.ts` | Create | Request schema, normalization, timezone verification, and authoritative change classification |
| `platform/src/lib/charts/recomputeChart.ts` | Create | Atomic chart correction transaction and post-commit dispatch |
| `platform/src/lib/charts/__tests__/updateChart.test.ts` | Create | Validation/normalization/classification matrix |
| `platform/src/lib/charts/__tests__/recomputeChart.test.ts` | Create | Transaction ordering, rollback, preservation, and dispatch failure tests |
| `platform/src/app/api/charts/[id]/route.ts` | Modify | Add authenticated `PATCH` backed by chart-update domain service |
| `platform/src/app/api/charts/[id]/__tests__/route.patch.test.ts` | Create | HTTP status, authority, no-op, display-only, recompute, and failure contract |
| `platform/src/app/clients/[id]/edit/page.tsx` | Modify | Load all stored editable fields and workspace permission state |
| `platform/src/components/clients/EditClientForm.tsx` | Modify | Correct endpoint, grouped Marsys form, server response handling, workspace redirect |
| `platform/src/components/dialogs/EditRebuildConfirmDialog.tsx` | Modify | Exact before/after changes, archival notice, and progress copy |
| `platform/src/components/clients/__tests__/EditClientForm.test.tsx` | Create | Display-only/recompute confirmation and error-state behaviour |
| `platform/src/components/dialogs/__tests__/EditRebuildConfirmDialog.test.tsx` | Create | Changed-field and accessibility assertions |
| `platform/src/lib/pariprashna/pipeline/safety_gate.ts` | Modify | Reject continuation of correction-archived conversations and non-ready charts |
| `platform/src/app/api/chat/consult/route.ts` | Modify | Reject new turns on correction-archived conversations |
| `platform/src/app/api/chat/consult/__tests__/archived-read-only.test.ts` | Create | Legacy consult correction-archive write gate |
| `platform/src/app/api/chat/consult/continue/route.ts` | Modify | Reject continuation of correction-archived conversations |
| `platform/src/app/api/chat/consult/continue/__tests__/archived-read-only.test.ts` | Create | Continue-route correction-archive write gate |
| `platform/src/app/api/chat/consult/regenerate/route.ts` | Modify | Reject regeneration of correction-archived conversations |
| `platform/src/app/api/chat/consult/regenerate/__tests__/archived-read-only.test.ts` | Create | Regenerate-route correction-archive write gate |
| `platform/src/app/api/conversations/[id]/route.ts` | Modify | Prevent mutation/unarchive of correction-archived conversations |
| `platform/src/components/consume/HistoricalConversationView.tsx` | Create | Read-only historical transcript with old-input notice |
| `platform/src/components/consume/__tests__/HistoricalConversationView.test.tsx` | Create | Read-only notice and no composer/actions assertions |
| `platform/src/lib/conversations/historicalReading.ts` | Create | Reader-safe historical transcript loader with canonical-text fallback |
| `platform/src/lib/conversations/__tests__/historicalReading.test.ts` | Create | No reasoning/tool/audit leakage and legacy text fallback |
| `platform/src/app/clients/[id]/consult/[conversationId]/page.tsx` | Modify | Render historical view for correction-archived conversations |
| `platform/src/components/pariprashna/PariprashnaApp.tsx` | Modify | Include archived readings and link historical rows to read-only page |
| `platform/src/components/pariprashna/history/types.ts` | Modify | Carry archived/read-only metadata and destination |
| `platform/src/components/pariprashna/history/Sidebar.tsx` | Modify | Present historical correction badge and navigation semantics |
| `platform/src/components/pariprashna/__tests__/history_merge.test.tsx` | Modify | Archived history navigation/read-only tests |
| `platform/tests/e2e/jataka-chart-workspace.spec.ts` | Create | Local directory/workspace/edit/history acceptance flow |

---

## Task 1: Establish the shared readiness authority

**Files:**
- Create: `platform/src/lib/charts/readiness.ts`
- Create: `platform/src/lib/charts/__tests__/readiness.test.ts`
- Modify: `platform/src/app/dashboard/page.tsx`
- Modify: `platform/src/lib/roster/types.ts`

**Interfaces:**
- Produces `ChartReadinessState`, `ChartReadiness`, `deriveChartReadiness()`, `emptyChartReadiness()`, `getChartReadinessMap()` and `isDerivedChartReady()`.
- Dashboard, workspace, and conversation gates must consume these exact names instead of issuing independent `pyramid_layers` calculations.

- [ ] **Step 1: Write failing pure-state tests**

Create a table-driven test covering `not-built`, `building`, `partially-built`, `ready`, `failed`, and correction dispatch failure as `needs-rebuild`:

```typescript
import { describe, expect, it } from 'vitest'
import { deriveChartReadiness } from '../readiness'

describe('deriveChartReadiness', () => {
  it.each([
    ['empty chart', [], null, 'not-built', 0],
    ['active run', [], { state: 'running', last_error: null }, 'building', 0],
    ['partial layers', [{ asset_id: 'ga_positions', state: 'lit', rows_written: 9 }], null, 'partially-built', 33],
    ['dispatch failure after correction', [], { state: 'failed', last_error: 'JOB_DISPATCH_FAILED: local spawn failed' }, 'needs-rebuild', 0],
  ] as const)('%s', (_label, throughput, run, expectedState, expectedPercent) => {
    const actual = deriveChartReadiness({ throughput: [...throughput], latestRun: run })
    expect(actual.state).toBe(expectedState)
    expect(actual.percent).toBe(expectedPercent)
  })
})
```

The final fixture must include all six public layers and assert `ready` only when Brahmagyan plus all five per-chart layers are lit. Do not hardcode the illustrative `33` once the real six-layer mapping is used; assert the percentage produced by `BRAHMA_LAYER_ORDER`.

- [ ] **Step 2: Run the focused test and confirm the red state**

```bash
cd platform
npx vitest run src/lib/charts/__tests__/readiness.test.ts
```

Expected: failure because `@/lib/charts/readiness` does not exist.

- [ ] **Step 3: Implement the readiness types and pure derivation**

Use the existing Brahma lexicon as the only layer order:

```typescript
import 'server-only'
import { query } from '@/lib/db/client'
import { BRAHMA_LAYER_ORDER } from '@/lib/brahma/lexicon'
import type { LayerPip } from '@/lib/roster/types'

export type ChartReadinessState =
  | 'not-built'
  | 'building'
  | 'partially-built'
  | 'ready'
  | 'failed'
  | 'needs-rebuild'

export interface ChartReadiness {
  state: ChartReadinessState
  percent: number
  label: string
  layerPips: LayerPip[]
  lastActivity: string | null
  activeRunId: string | null
  latestRunId: string | null
  latestError: string | null
}

interface ThroughputRow {
  chart_id: string
  asset_id: string
  state: string
  rows_written: number | null
  last_built_at: string | null
}

interface LatestRunRow {
  id: string
  chart_id: string
  state: string
  action: string
  last_error: string | null
  created_at: string
  started_at: string | null
  ended_at: string | null
}

export function isDerivedChartReady(readiness: ChartReadiness): boolean {
  return readiness.state === 'ready'
}

export function emptyChartReadiness(): ChartReadiness {
  return deriveChartReadiness({ throughput: [], latestRun: null })
}
```

Rules:

```text
latest planned/running/paused run OR any building throughput -> building
latest failed run with last_error prefix JOB_DISPATCH_FAILED -> needs-rebuild
latest failed run otherwise -> failed
all six public layer pips lit -> ready
some but not all pips lit -> partially-built
no per-chart computed data and no failure -> not-built
```

Brahmagyan is global infrastructure and remains represented as lit, matching the current dashboard. Map `ga_`, `bo_`, `ka_`, `ph_`, and `mi_` assets to the other five public layers. Treat `lit` or `rows_written > 0` as data; retain `stale` data as present but let failure/run context determine the label.

- [ ] **Step 4: Implement one batched database resolver**

`getChartReadinessMap(chartIds: string[])` must perform two bounded queries: active registry throughput for all chart IDs and the latest run for each chart regardless of state. The latest-run query must select `id`, `state`, `action`, `last_error`, `created_at`, `started_at`, and `ended_at` with `DISTINCT ON (chart_id)`.

```typescript
export async function getChartReadinessMap(
  chartIds: string[],
): Promise<Map<string, ChartReadiness>> {
  if (chartIds.length === 0) return new Map()
  const [throughput, runs] = await Promise.all([
    query<ThroughputRow>(
      `SELECT at.chart_id, at.asset_id, at.state, at.rows_written, at.last_built_at
         FROM asset_throughput at
         JOIN asset_registry ar ON ar.asset_id=at.asset_id AND ar.is_active=true
        WHERE at.chart_id=ANY($1::uuid[])`,
      [chartIds],
    ),
    query<LatestRunRow>(
      `SELECT DISTINCT ON (chart_id)
              id, chart_id, state, action, last_error, created_at, started_at, ended_at
         FROM build_runs
        WHERE chart_id=ANY($1::uuid[])
        ORDER BY chart_id, created_at DESC`,
      [chartIds],
    ),
  ])
  return new Map(chartIds.map((id) => [id, deriveChartReadiness({
    throughput: throughput.rows.filter((row) => row.chart_id === id),
    latestRun: runs.rows.find((row) => row.chart_id === id) ?? null,
  })]))
}
```

- [ ] **Step 5: Replace dashboard inline readiness calculation**

In `dashboard/page.tsx`, retain roster authorization and stats, but replace the throughput/build query block and local mapping functions with `getChartReadinessMap(chartIds)`. Populate existing roster metadata from the shared value:

```typescript
const readinessMap = await getChartReadinessMap(chartIds)
const chartsWithMeta: ChartWithMeta[] = charts.map((chart) => {
  const readiness = readinessMap.get(chart.id) ?? emptyChartReadiness()
  return {
    ...chart,
    readiness,
    pyramidPercent: readiness.percent,
    lastLayerActivity: readiness.lastActivity,
    buildState: null,
    layerPips: readiness.layerPips,
    canBuild: role === 'super_admin' || chart.owner_id === user.uid,
  }
})
```

Add `readiness: ChartReadiness` to `ChartWithMeta`. Keep old fields until Tasks 2–3 finish their consumers; remove redundant fields only after all focused tests are green.

- [ ] **Step 6: Run readiness and dashboard tests**

```bash
cd platform
npx vitest run src/lib/charts/__tests__/readiness.test.ts src/app/dashboard/__tests__/dashboard.test.tsx
```

Expected: all pass; no dashboard query references `pyramid_layers`.

- [ ] **Step 7: Commit**

```bash
git add platform/src/lib/charts platform/src/app/dashboard/page.tsx platform/src/lib/roster/types.ts
git commit -m "refactor(jataka): centralize chart readiness"
```

---

## Task 2: Make the Jātakas directory minimal and navigational

**Files:**
- Modify: `platform/src/components/dashboard/ClientCard.tsx`
- Modify: `platform/src/components/dashboard/RosterTableView.tsx`
- Modify: `platform/src/components/dashboard/__tests__/ClientCard.test.tsx`
- Modify: `platform/src/components/dashboard/__tests__/RosterTableView.test.tsx`

**Interfaces:**
- Consumes `ChartWithMeta.readiness` from Task 1.
- Produces one workspace link per grid card and one name link per table row.

- [ ] **Step 1: Replace action-oriented tests with the approved directory contract**

Assert the card has exactly one link, that it targets `/clients/<id>`, and that no direct actions or overflow controls render:

```typescript
render(<ClientCard chart={BASE_CHART} />)
const links = screen.getAllByRole('link')
expect(links).toHaveLength(1)
expect(links[0]).toHaveAttribute('href', '/clients/chart-abc')
expect(screen.queryByText('Nirmāṇa')).not.toBeInTheDocument()
expect(screen.queryByText('Paripraśna')).not.toBeInTheDocument()
expect(screen.queryByRole('button', { name: /more actions/i })).not.toBeInTheDocument()
expect(screen.getByText(BASE_CHART.name)).toBeInTheDocument()
expect(screen.getByLabelText(/readiness/i)).toBeInTheDocument()
```

For the table, assert headers are exactly the truthful roster fields and contain no `Actions` or `Current dasha`:

```typescript
expect(screen.queryByRole('columnheader', { name: 'Actions' })).not.toBeInTheDocument()
expect(screen.queryByRole('columnheader', { name: /current dasha/i })).not.toBeInTheDocument()
expect(screen.getByRole('link', { name: 'Roster Chart' })).toHaveAttribute(
  'href',
  '/clients/chart-xyz',
)
```

- [ ] **Step 2: Run both component suites and confirm they fail against current actions**

```bash
cd platform
npx vitest run src/components/dashboard/__tests__/ClientCard.test.tsx src/components/dashboard/__tests__/RosterTableView.test.tsx
```

- [ ] **Step 3: Simplify `ClientCard` to one semantic link**

Remove `MomentPhrase`, local overflow state, `DeleteChartDialog`, and direct capability buttons. Retain the birth line and render the shared readiness label/progress inside the single link:

```tsx
export function ClientCard({ chart }: Props) {
  return (
    <Link
      href={`/clients/${chart.id}`}
      aria-label={`Open ${chart.name} Jātaka — ${chart.readiness.label}`}
      className="brand-card group flex rounded-xl p-4 transition-[border-color,transform] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#d4af37] motion-reduce:transform-none"
    >
      <div className="min-w-0 flex-1">
        <h2 className="bt-heading truncate text-[#fce29a]">{chart.name}</h2>
        <p className="bt-label mt-1 truncate text-[rgba(212,175,55,0.48)]">
          {formatDate(chart.birth_date)} · {chart.birth_place}
        </p>
        <DirectoryReadiness readiness={chart.readiness} chartName={chart.name} />
      </div>
    </Link>
  )
}
```

Keep the progress helper in this file only if it remains under roughly 80 lines; otherwise move the purely presentational bar to `components/dashboard/DirectoryReadiness.tsx` and test through `ClientCard`.

- [ ] **Step 4: Simplify `RosterTableView`**

Render `Name`, `Birth details`, `Build`, and `Last activity`. The name is the row's only link. Remove Nirmāṇa, Paripraśna, action buttons, and the empty daśā column.

- [ ] **Step 5: Run component and dashboard suites**

```bash
cd platform
npx vitest run src/components/dashboard/__tests__/ClientCard.test.tsx src/components/dashboard/__tests__/RosterTableView.test.tsx src/app/dashboard/__tests__/dashboard.test.tsx
```

- [ ] **Step 6: Commit**

```bash
git add platform/src/components/dashboard platform/src/app/dashboard/__tests__/dashboard.test.tsx
git commit -m "feat(jataka): simplify chart directory cards and rows"
```

---

## Task 3: Build the D1-first Jātaka workspace

**Files:**
- Modify: `platform/src/app/clients/[id]/page.tsx`
- Modify: `platform/src/components/profile/ChartHero.tsx`
- Create: `platform/src/components/profile/ChartReadinessBand.tsx`
- Create: `platform/src/components/profile/CapabilityCard.tsx`
- Create: `platform/src/components/profile/ChartActionsMenu.tsx`
- Create: `platform/src/components/profile/__tests__/ChartReadinessBand.test.tsx`
- Create: `platform/src/components/profile/__tests__/CapabilityCard.test.tsx`

**Interfaces:**
- Consumes `getChartReadinessMap([id])`, `resolveChartPageAccess()`, `getForensicSnapshot()`, and the existing `RasiChartSVG`.
- Produces a capability deck where Nirmāṇa is omitted for `canBuild=false`, Paripraśna is disabled while rebuilding/needs-rebuild/not-ready after correction, and Pañcāṅga remains a chart capability.

- [ ] **Step 1: Write readiness-band component tests**

```typescript
render(<ChartReadinessBand readiness={fixture({ state: 'needs-rebuild' })} />)
expect(screen.getByText('Needs rebuild')).toBeInTheDocument()
expect(screen.getByText('Gaṇita')).toBeInTheDocument()
expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '0')
expect(screen.getByText(/retry in nirmāṇa/i)).toBeInTheDocument()
```

Cover all six state labels and ensure each Brahma layer has text or an accessible name, not colour-only meaning.

- [ ] **Step 2: Write capability-card tests**

```typescript
render(<CapabilityCard name="Paripraśna" href="/clients/c1/pariprashna" available={false} reason="Chart recomputation is in progress." />)
expect(screen.queryByRole('link', { name: /paripraśna/i })).not.toBeInTheDocument()
expect(screen.getByText('Chart recomputation is in progress.')).toBeInTheDocument()
expect(screen.getByText('Unavailable')).toBeInTheDocument()
```

Also assert available cards render exactly one link and meet the 44px target class.

- [ ] **Step 3: Run focused tests and confirm they fail**

```bash
cd platform
npx vitest run src/components/profile/__tests__/ChartReadinessBand.test.tsx src/components/profile/__tests__/CapabilityCard.test.tsx
```

- [ ] **Step 4: Implement the three focused workspace components**

`ChartReadinessBand` renders `readiness.label`, percentage, six pips, last activity, active run context, and retry copy. `CapabilityCard` accepts:

```typescript
interface CapabilityCardProps {
  name: string
  description: string
  href: string
  available: boolean
  stateHint: string
  reason?: string
}
```

`ChartActionsMenu` accepts:

```typescript
interface ChartActionsMenuProps {
  chartId: string
  chartName: string
  canBuild: boolean
  isSuperAdmin: boolean
  canShare: boolean
}
```

Edit and Delete render only for `canBuild`; Sharing follows existing authorization; Audit renders only for super admin. Reuse `DeleteChartDialog` rather than duplicating delete behaviour.

- [ ] **Step 5: Refine `ChartHero` without replacing `RasiChartSVG`**

Maintain mobile order `D1 -> identity`. Add the `Jātaka` eyebrow, formatted timezone label from `timezone_id`, Lagna when available, and an action-menu slot. Use Cormorant display typography and gold hairlines but no `.pp-root` class.

- [ ] **Step 6: Recompose `/clients/[id]`**

Replace the `pyramid_layers` query and `JourneyStrip` construction with shared readiness. Query recent conversations only with `archived_at IS NULL`. Render:

```text
ChartHero
ChartReadinessBand
Capability deck: Nirmāṇa / Paripraśna / Pañcāṅga
At a glance: current daśā, verified yogas, recent active conversations, freshness
Secondary controls through ChartActionsMenu
```

Capability policy:

```typescript
const pariprashnaAvailable = isDerivedChartReady(readiness)
const panchangAvailable =
  !['building', 'needs-rebuild', 'failed'].includes(readiness.state) &&
  readiness.layerPips.some((pip) => pip.layer === 'ganita' && pip.state === 'lit')
```

Do not render the disabled Timeline placeholder. Keep only summaries backed by `forensicChart` or explicit query results.

- [ ] **Step 7: Run profile, page-security, and dashboard regression tests**

```bash
cd platform
npx vitest run \
  src/components/profile/__tests__/ChartReadinessBand.test.tsx \
  src/components/profile/__tests__/CapabilityCard.test.tsx \
  src/app/clients/[id]/__tests__/generateMetadata.security.test.tsx \
  src/app/dashboard/__tests__/dashboard.test.tsx
```

- [ ] **Step 8: Commit**

```bash
git add platform/src/app/clients/'[id]'/page.tsx platform/src/components/profile
git commit -m "feat(jataka): add D1-first chart workspace"
```

---

## Task 4: Add governed historical archive context

**Files:**
- Create: `platform/supabase/migrations/1080_jataka_conversation_archive_context.sql`
- Create: `platform/tests/unit/migrations/jataka_conversation_archive_context.test.ts`
- Create: `platform/src/lib/charts/types.ts`
- Modify: `platform/src/lib/conversations.ts`

**Interfaces:**
- Adds `archive_reason`, `archived_chart_snapshot`, and `archived_by_run_id` to `conversations`.
- Produces `isCorrectionArchived(conversation)` for every write gate.

- [ ] **Step 1: Write the migration contract test first**

The test reads the migration text and requires additive/idempotent DDL, a constrained reason, a run FK, and no destructive statement:

```typescript
const sql = fs.readFileSync(path.join(REPO_ROOT, 'platform/supabase/migrations/1080_jataka_conversation_archive_context.sql'), 'utf8')
expect(sql).toMatch(/ADD COLUMN IF NOT EXISTS archive_reason TEXT/i)
expect(sql).toMatch(/ADD COLUMN IF NOT EXISTS archived_chart_snapshot JSONB/i)
expect(sql).toMatch(/ADD COLUMN IF NOT EXISTS archived_by_run_id UUID/i)
expect(sql).toMatch(/REFERENCES public\.build_runs\(id\) ON DELETE SET NULL/i)
expect(sql).toMatch(/chart_details_changed/i)
expect(sql).not.toMatch(/DROP TABLE|TRUNCATE|DELETE FROM conversations/i)
```

- [ ] **Step 2: Run the test and confirm the missing-file failure**

```bash
cd platform
npx vitest run tests/unit/migrations/jataka_conversation_archive_context.test.ts
```

- [ ] **Step 3: Create the additive migration**

Use this semantic shape:

```sql
ALTER TABLE public.conversations
  ADD COLUMN IF NOT EXISTS archive_reason TEXT,
  ADD COLUMN IF NOT EXISTS archived_chart_snapshot JSONB,
  ADD COLUMN IF NOT EXISTS archived_by_run_id UUID;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'conversations_archive_reason_check'
  ) THEN
    ALTER TABLE public.conversations
      ADD CONSTRAINT conversations_archive_reason_check
      CHECK (archive_reason IS NULL OR archive_reason IN ('chart_details_changed'));
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'conversations_archived_by_run_id_fkey'
  ) THEN
    ALTER TABLE public.conversations
      ADD CONSTRAINT conversations_archived_by_run_id_fkey
      FOREIGN KEY (archived_by_run_id)
      REFERENCES public.build_runs(id)
      ON DELETE SET NULL;
  END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_conversations_chart_archive_reason
  ON public.conversations(chart_id, archive_reason, archived_at DESC)
  WHERE archived_at IS NOT NULL;
```

Add comments explaining that the snapshot is the pre-correction input set and that only `chart_details_changed` archives are system-locked read-only.

- [ ] **Step 4: Add the shared immutable snapshot type**

Create `platform/src/lib/charts/types.ts`:

```typescript
export interface ChartInputSnapshot {
  name: string
  preferred_name: string | null
  subject_name: string | null
  birth_date: string
  birth_time: string
  birth_place: string
  birth_lat: number
  birth_lng: number
  timezone_id: string
  effective_tz_offset_minutes: number
  ayanamshas: string[]
  captured_at: string
}
```

- [ ] **Step 5: Extend the conversation model**

Add to `ConversationSummary`:

```typescript
archive_reason: 'chart_details_changed' | null
archived_chart_snapshot: ChartInputSnapshot | null
archived_by_run_id: string | null
```

Update all conversation projections in `listConversations()` and `getConversation()`. Add:

```typescript
export function isCorrectionArchived(
  conversation: Pick<ConversationSummary, 'archived_at' | 'archive_reason'>,
): boolean {
  return conversation.archived_at !== null && conversation.archive_reason === 'chart_details_changed'
}
```

- [ ] **Step 6: Run migration guards and conversation tests**

```bash
cd platform
npm run guard:migration-numbers
npx vitest run tests/unit/migrations/jataka_conversation_archive_context.test.ts tests/unit/chat-v2
```

- [ ] **Step 7: Commit**

```bash
git add platform/supabase/migrations/1080_jataka_conversation_archive_context.sql platform/tests/unit/migrations/jataka_conversation_archive_context.test.ts platform/src/lib/charts/types.ts platform/src/lib/conversations.ts
git commit -m "feat(jataka): preserve chart context on archived readings"
```

---

## Task 5: Extract shared build preparation, invalidation, and dispatch services

**Files:**
- Create: `platform/src/lib/build/runPreparation.ts`
- Create: `platform/src/lib/build/assetInvalidation.ts`
- Create: `platform/src/lib/build/runDispatch.ts`
- Create: `platform/src/lib/build/__tests__/runPreparation.test.ts`
- Create: `platform/src/lib/build/__tests__/assetInvalidation.test.ts`
- Modify: `platform/src/app/api/cockpit/runs/route.ts`
- Modify: `platform/src/app/api/cockpit/runs/__tests__/route.test.ts`
- Modify: `platform/src/app/api/cockpit/runs/__tests__/route.authz.test.ts`

**Interfaces:**
- Produces `resolveRunPreparation()`, `persistPreparedRun()`, `invalidateAssets()`, and `dispatchPreparedRun()`.
- Accepts a `Queryable`/`PoolClient`; the chart-correction transaction must call these helpers using its own client.
- Cockpit keeps its current HTTP surface and best-effort operator policy.

- [ ] **Step 1: Add characterization assertions before moving code**

Extend the existing cockpit route tests to lock the following current responses and mutations:

```text
unauthorized or view-only caller -> no registry query, clear, run insert, or dispatch
active run -> 409 RUN_ACTIVE
protected-only plan -> 422 PROTECTED
upstream block -> 422 UPSTREAM_BLOCKED
clear_before operator path -> savepoint-based best effort remains
run + build_run_assets persist atomically
dispatch failure -> run failed, queued assets aborted, HTTP 503
```

Run:

```bash
cd platform
npx vitest run src/app/api/cockpit/runs/__tests__/route.test.ts src/app/api/cockpit/runs/__tests__/route.authz.test.ts
```

- [ ] **Step 2: Define shared service contracts**

```typescript
export type ClearPolicy = 'none' | 'operator-best-effort' | 'chart-correction-strict'

export interface RunPreparationRequest {
  chartId: string
  scope: BuildScope
  scopeTarget: string | null
  action: BuildAction
  allowedScopes: string[]
  clearPolicy: ClearPolicy
  triggeredBy: string
}

export interface PreparedRun {
  chartId: string
  plan: string[]
  planWaves: string[][]
  registry: RegistryEntryWithScope[]
  clearAssets: RegistryEntryWithScope[]
  protectedAssets: string[]
  manifest: FrozenRunManifest
  manifestDigest: string
}

export type Queryable = Pick<PoolClient, 'query'>

export class BuildPreparationError extends Error {
  constructor(
    readonly code: 'RUN_ACTIVE' | 'PROTECTED' | 'UPSTREAM_BLOCKED' | 'INVALID_BUILD_PLAN' | 'CODE_DIGEST_UNAVAILABLE' | 'CLEAR_SPEC_MISSING',
    message: string,
    readonly details: Record<string, unknown> = {},
  ) { super(message) }
}
```

Export the registry, frozen-manifest types, canonical manifest serialization, digest calculation, active-run guard, registry/throughput/protection/freshness reads, and plan construction from `runPreparation.ts`. Keep service-probe-only HTTP validation in the cockpit route.

- [ ] **Step 3: Write service tests for plan and manifest behaviour**

Use a fake `Queryable` to prove:

```typescript
await expect(resolveRunPreparation(db, correctionRequest)).rejects.toMatchObject({ code: 'PROTECTED' })
expect(prepared.manifest.version).toBe('nirmana-run-manifest/v1')
expect(prepared.manifestDigest).toMatch(/^[a-f0-9]{64}$/)
expect(prepared.plan.every((id) => !id.startsWith('bg_'))).toBe(true)
```

The correction request is `scope='global'`, `action='rebuild'`, `allowedScopes=['per_chart']`, and never includes global/L0 or no-writer source assets.

- [ ] **Step 4: Implement explicit invalidation policy**

`assetInvalidation.ts` must use `EXPLICIT_CLEAR_OPS`, `deriveDeleteSqlFromCountSql()`, registry `target_table`, and reverse dependency order. Return counts and throw on strict failures:

```typescript
export async function invalidateAssets(args: {
  db: Queryable
  chartId: string
  assets: RegistryEntryWithScope[]
  policy: Exclude<ClearPolicy, 'none'>
}): Promise<{ clearedAssetIds: string[]; preservedAssetIds: string[] }>
```

Create an explicit preservation map with tested reasons:

```typescript
export const CORRECTION_PRESERVATION = {
  lel_events: 'user-authored life events and chart-state index',
  mi_seva: 'user preferences are not chart-derived output',
  mi_vistara: 'global append-only export log',
} as const
```

The existing scoped operations for `mi_abhilekha` and `mi_bhavisya` preserve answered journal rows and confirmed/denied outcomes while clearing regenerable rows. In strict mode:

```text
explicit null + listed preservation reason -> skip and record preserved
explicit operations -> every operation must succeed
derivable count_sql -> generated DELETE must succeed
safe per-chart `target_table` fallback -> the validated template `DELETE FROM ${asset.target_table} WHERE chart_id = $1` must succeed
writer asset with no safe clear specification -> throw CLEAR_SPEC_MISSING
any SQL failure -> throw; caller transaction rolls back
```

Do not use savepoints in strict mode. Operator best-effort retains the current savepoint behaviour.

- [ ] **Step 5: Implement run persistence and dispatch helpers**

```typescript
export async function persistPreparedRun(
  db: Queryable,
  prepared: PreparedRun,
  triggeredBy: string,
): Promise<string>

export async function dispatchPreparedRun(runId: string): Promise<
  | { ok: true; executionName: string }
  | { ok: false; code: 'JOB_DISPATCH_FAILED'; message: string }
>
```

`persistPreparedRun()` inserts one `build_runs` row and all queued `build_run_assets`; it never starts its own transaction. `dispatchPreparedRun()` calls existing `invokeRunJob()`. On failure it must write:

```sql
UPDATE build_runs
SET state='failed', ended_at=NOW(), last_error='JOB_DISPATCH_FAILED: ' || $1
WHERE id=$2;

UPDATE build_run_assets
SET state='aborted'
WHERE run_id=$1 AND state='queued';
```

- [ ] **Step 6: Refactor the cockpit route onto shared helpers**

Keep validation, authorization, service-probe constraints, HTTP mappings, and response JSON in the route. Replace duplicated registry/manifest/persistence/dispatch logic with the new services. Keep `operator-best-effort` for `clear_before=true`; do not silently tighten cockpit semantics as part of this feature.

- [ ] **Step 7: Run all build/cockpit tests**

```bash
cd platform
npx vitest run \
  src/lib/build/__tests__/runPreparation.test.ts \
  src/lib/build/__tests__/assetInvalidation.test.ts \
  src/lib/build/__tests__/reliability.test.ts \
  src/app/api/cockpit/runs/__tests__/route.test.ts \
  src/app/api/cockpit/runs/__tests__/route.authz.test.ts
```

- [ ] **Step 8: Commit**

```bash
git add platform/src/lib/build platform/src/app/api/cockpit/runs
git commit -m "refactor(build): share run preparation and invalidation"
```

---

## Task 6: Implement authoritative chart-change classification and atomic recompute

**Files:**
- Create: `platform/src/lib/charts/updateChart.ts`
- Create: `platform/src/lib/charts/recomputeChart.ts`
- Create: `platform/src/lib/charts/__tests__/updateChart.test.ts`
- Create: `platform/src/lib/charts/__tests__/recomputeChart.test.ts`

**Interfaces:**
- Produces `ChartUpdateInputSchema`, `normalizeChartUpdate()`, `classifyChartChanges()`, `updateChartAndMaybeRecompute()` and `ChartUpdateResult`.
- Consumes the Task 5 service functions using the same transaction client.

- [ ] **Step 1: Write the validation and classification matrix**

Use the same ayanāṃśa source as chart creation (`VALID_AYANAMSHAS`). Cover whitespace normalization, second-vs-minute time normalization, sorted ayanāṃśas, numeric coordinates, IANA timezone validation, name-only changes, every computation field, no-op, and malformed values.

```typescript
expect(classifyChartChanges(stored, { ...stored, name: 'New display name' })).toEqual({
  mode: 'display-only',
  changedFields: ['name'],
})

for (const field of ['birth_date', 'birth_time', 'birth_place', 'birth_lat', 'birth_lng', 'timezone_id', 'ayanamshas'] as const) {
  expect(classifyChartChanges(stored, changed(field))).toMatchObject({ mode: 'recompute' })
}
```

- [ ] **Step 2: Run classification tests and confirm failure**

```bash
cd platform
npx vitest run src/lib/charts/__tests__/updateChart.test.ts
```

- [ ] **Step 3: Implement normalization and timezone verification**

Request shape:

```typescript
export const ChartUpdateInputSchema = z.object({
  name: z.string().trim().min(1).max(200),
  preferred_name: z.string().trim().max(100).nullable().optional(),
  subject_name: z.string().trim().max(200).nullable().optional(),
  birth_date: z.iso.date(),
  birth_time: z.string().regex(/^([01]\d|2[0-3]):[0-5]\d(?::[0-5]\d)?$/),
  birth_place: z.string().trim().min(1).max(300),
  lat: z.number().finite().min(-90).max(90),
  lon: z.number().finite().min(-180).max(180),
  timezone_id: z.string().trim().min(1).max(100),
  tz_offset: z.number().finite().min(-14).max(14),
  ayanamshas: z.array(z.enum(VALID_AYANAMSHAS)).min(1),
}).strict()
```

Validate `timezone_id` with `Intl.DateTimeFormat(undefined, { timeZone: timezoneId })`. Derive the effective offset at `birth_date + birth_time` and reject a submitted `tz_offset` that differs by more than one minute. Do not add a `tz_offset` database column: the orchestrator already derives `tz_offset_hours` from `charts.timezone_id` at the birth instant in `python-sidecar/pipeline/orchestrator/birth_params.py`.

- [ ] **Step 4: Write transaction tests before implementation**

The fake pool client records statements. Test:

```text
no-op -> SELECT FOR UPDATE, COMMIT, no UPDATE/archive/clear/run
display-only -> chart UPDATE only, no archive/clear/run
active run -> RUN_ACTIVE error and rollback
protected required asset -> PROTECTED error and rollback
clear operation throws -> rollback; no persisted chart/conversation/run mutation
success -> archive, chart update, reverse clears, throughput reset, run insert, run-assets insert, commit, then dispatch
success preserves chart id, ownership, grants, life events, answered journal rows, confirmed/denied outcomes
dispatch failure -> transaction already committed; run marked failed with JOB_DISPATCH_FAILED
```

Assert ordering from recorded statements rather than only call counts.

- [ ] **Step 5: Implement the transaction service**

```typescript
export type ChartUpdateResult =
  | { mode: 'noop'; chartId: string; changedFields: [] }
  | { mode: 'display-only'; chartId: string; changedFields: string[] }
  | { mode: 'recompute-started'; chartId: string; changedFields: string[]; runId: string }
  | { mode: 'needs-rebuild'; chartId: string; changedFields: string[]; runId: string; error: string }

export async function updateChartAndMaybeRecompute(args: {
  chartId: string
  principalId: string
  input: unknown
}): Promise<ChartUpdateResult>
```

Transaction sequence:

```sql
BEGIN ISOLATION LEVEL SERIALIZABLE;
SELECT id, name, preferred_name, subject_name,
       birth_date::text, birth_time::text, birth_place,
       birth_lat::float8, birth_lng::float8, timezone_id,
       ayanamsa, owner_id, client_id
FROM charts
WHERE id=$1
FOR UPDATE;
SELECT id FROM build_runs WHERE chart_id=$1 AND state IN ('planned','running','paused') LIMIT 1;
-- resolve complete per-chart rebuild plan and protected assets using this client
-- capture old normalized inputs as JSON
UPDATE conversations
SET archived_at=NOW(),
    updated_at=NOW(),
    archive_reason='chart_details_changed',
    archived_chart_snapshot=$2::jsonb
WHERE chart_id=$1 AND archived_at IS NULL
RETURNING id;
UPDATE charts
SET name=$2,
    preferred_name=$3,
    subject_name=$4,
    birth_date=$5::date,
    birth_time=$6::time,
    birth_place=$7,
    birth_lat=$8,
    birth_lng=$9,
    timezone_id=$10,
    ayanamsa=$11
WHERE id=$1;
-- strict reverse-order derived-data invalidation
UPDATE asset_throughput
SET state='dormant',
    last_built_at=NULL,
    rows_written=NULL,
    built_against_upstream_hash=NULL,
    built_against_writer_hash=NULL,
    last_error=NULL
WHERE chart_id=$1 AND asset_id=ANY($2::text[]);
-- insert frozen rebuild run + run assets
UPDATE conversations
SET archived_by_run_id=$2
WHERE id=ANY($1::uuid[]);
COMMIT;
```

Keep the IDs returned by the archival statement and attach the new run only to that exact set; never sweep older historical rows into a later correction run.

The snapshot must satisfy the exact `ChartInputSnapshot` contract created in Task 4; do not add live chart fields, ownership, or derived facts to that historical input record.

After commit, call `dispatchPreparedRun(runId)`. Return `needs-rebuild` when dispatch fails; never attempt to restore cleared data from application code.

- [ ] **Step 6: Run chart domain and build service tests**

```bash
cd platform
npx vitest run \
  src/lib/charts/__tests__/updateChart.test.ts \
  src/lib/charts/__tests__/recomputeChart.test.ts \
  src/lib/build/__tests__/runPreparation.test.ts \
  src/lib/build/__tests__/assetInvalidation.test.ts
```

- [ ] **Step 7: Commit**

```bash
git add platform/src/lib/charts
git commit -m "feat(jataka): add atomic chart correction and recompute"
```

---

## Task 7: Expose PATCH and complete the edit experience

**Files:**
- Modify: `platform/src/app/api/charts/[id]/route.ts`
- Create: `platform/src/app/api/charts/[id]/__tests__/route.patch.test.ts`
- Modify: `platform/src/app/clients/[id]/edit/page.tsx`
- Modify: `platform/src/components/clients/EditClientForm.tsx`
- Modify: `platform/src/components/dialogs/EditRebuildConfirmDialog.tsx`
- Create: `platform/src/components/clients/__tests__/EditClientForm.test.tsx`
- Create: `platform/src/components/dialogs/__tests__/EditRebuildConfirmDialog.test.tsx`

**Interfaces:**
- `PATCH /api/charts/[id]` returns `{ data: ChartUpdateResult }` and structured `{ error, code, fields? }` failures.
- Client always returns to `/clients/[id]`; `needs-rebuild` adds `?status=needs-rebuild&run=<id>`.

- [ ] **Step 1: Write route tests first**

Mock authentication, permission, and `updateChartAndMaybeRecompute()`. Assert:

```text
401 UNAUTHENTICATED
403 FORBIDDEN_CHART for view grants, unrelated callers, and nonexistent chart IDs (the existing non-enumeration contract)
422 VALIDATION_FAILED with field errors
409 RUN_ACTIVE with no mutation
422 PROTECTED / INVALID_BUILD_PLAN
500 RECOMPUTE_PREPARATION_FAILED after rollback
200 noop/display-only
202 recompute-started
503 needs-rebuild with run_id
```

Use `requireChartPermission({ access: 'write' })`; do not duplicate owner/super-admin logic.

- [ ] **Step 2: Implement PATCH error mapping**

```typescript
export async function PATCH(req: NextRequest, ctx: RouteContext) {
  const user = await getServerUser()
  if (!user) return NextResponse.json({ error: 'Authentication required', code: 'UNAUTHENTICATED' }, { status: 401 })
  const { id: chartId } = await ctx.params
  const denied = await requireChartPermission({ uid: user.uid, chartId, access: 'write' })
  if (denied) return denied
  const result = await updateChartAndMaybeRecompute({ chartId, principalId: user.uid, input: await req.json() })
  if (result.mode === 'needs-rebuild') {
    return NextResponse.json({
      error: 'Chart details were saved, but the rebuild did not start.',
      code: 'JOB_DISPATCH_FAILED',
      data: result,
    }, { status: 503 })
  }
  return NextResponse.json({ data: result }, { status: result.mode === 'recompute-started' ? 202 : 200 })
}
```

Map domain errors explicitly by `code`; do not expose stack traces or raw SQL.

- [ ] **Step 3: Write component tests**

Cover:

```text
name-only edit -> no dialog, PATCH /api/charts/<id>, Save changes
birth/time/place/coordinates/timezone/ayanāṃśa change -> Save and recompute + dialog
dialog lists each before/after field and the archive/read-only notice
409 leaves form values intact and announces build-in-progress
422 maps server field errors
202 redirects to workspace
503 redirects to workspace Needs rebuild state
dialog Cancel returns focus to submit trigger
```

- [ ] **Step 4: Load complete stored values in the edit page**

Select `name`, `preferred_name`, `subject_name`, `birth_date::text`, `birth_time::text`, `birth_place`, `birth_lat`, `birth_lng`, `timezone_id`, and `ayanamsa`. Derive the initial `tz_offset` with the same exported `resolveTimezoneOffsetMinutes(birth_date, birth_time, timezone_id)` used by server validation and pass it to the form. Do not default stored timezone silently; surface missing or invalid timezone as a form error requiring correction before recompute.

- [ ] **Step 5: Refactor the form around four visual groups**

Use Identity, Birth coordinates, Time standard, and Computation frame. Preserve the existing map/location assistance if it is already shared from `NewClientForm`; do not fork a second geocoding implementation.

Correct request:

```typescript
const response = await fetch(`/api/charts/${chart.id}`, {
  method: 'PATCH',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    name: form.full_name.trim(),
    preferred_name: form.preferred_name.trim() || null,
    subject_name: form.subject_name.trim() || null,
    birth_date: form.birth_date,
    birth_time: form.birth_time,
    birth_place: form.birth_place.trim(),
    lat: Number(form.latitude),
    lon: Number(form.longitude),
    timezone_id: form.timezone_id,
    tz_offset: Number(form.tz_offset),
    ayanamshas: [...form.ayanamshas].sort(),
  }),
})
```

Do not mutate arrays with `.sort()` inside comparison; sort copies. Button text is `Save changes` for display-only and `Save and recompute` when the client hint detects computation fields.

Handle `503 JOB_DISPATCH_FAILED` before the generic `!response.ok` branch: its `data.chartId` and `data.runId` are a committed degraded result, so navigate to `/clients/<id>?status=needs-rebuild&run=<runId>` and let the shared readiness surface explain the retry. Other non-2xx responses keep the populated form in place.

- [ ] **Step 6: Expand the confirmation dialog**

Pass a typed list:

```typescript
interface ChangedField {
  key: string
  label: string
  before: string
  after: string
}
```

The dialog must state that previous computed results will be replaced, prior Paripraśna conversations will be archived read-only under the old chart details, and progress remains visible on the chart workspace.

- [ ] **Step 7: Run route and edit tests**

```bash
cd platform
npx vitest run \
  src/app/api/charts/[id]/__tests__/route.patch.test.ts \
  src/components/clients/__tests__/EditClientForm.test.tsx \
  src/components/dialogs/__tests__/EditRebuildConfirmDialog.test.tsx
```

- [ ] **Step 8: Commit**

```bash
git add platform/src/app/api/charts/'[id]' platform/src/app/clients/'[id]'/edit platform/src/components/clients platform/src/components/dialogs
git commit -m "feat(jataka): complete chart edit and recompute flow"
```

---

## Task 8: Enforce and render correction history as read-only

**Files:**
- Modify: `platform/src/lib/pariprashna/pipeline/safety_gate.ts`
- Modify: `platform/src/app/api/chat/consult/route.ts`
- Create: `platform/src/app/api/chat/consult/__tests__/archived-read-only.test.ts`
- Modify: `platform/src/app/api/chat/consult/continue/route.ts`
- Create: `platform/src/app/api/chat/consult/continue/__tests__/archived-read-only.test.ts`
- Modify: `platform/src/app/api/chat/consult/regenerate/route.ts`
- Create: `platform/src/app/api/chat/consult/regenerate/__tests__/archived-read-only.test.ts`
- Modify: `platform/src/app/api/conversations/[id]/route.ts`
- Modify: `platform/src/app/api/pariprashna/__tests__/route.test.ts`
- Create: `platform/src/components/consume/HistoricalConversationView.tsx`
- Create: `platform/src/components/consume/__tests__/HistoricalConversationView.test.tsx`
- Create: `platform/src/lib/conversations/historicalReading.ts`
- Create: `platform/src/lib/conversations/__tests__/historicalReading.test.ts`
- Modify: `platform/src/app/clients/[id]/consult/[conversationId]/page.tsx`
- Modify: `platform/src/components/pariprashna/PariprashnaApp.tsx`
- Modify: `platform/src/components/pariprashna/history/types.ts`
- Modify: `platform/src/components/pariprashna/history/Sidebar.tsx`
- Modify: `platform/src/components/pariprashna/__tests__/history_merge.test.tsx`

**Interfaces:**
- Every turn-writing door uses `isCorrectionArchived()`.
- Historical rows navigate to the existing consult conversation URL, which renders a dedicated non-interactive transcript when the archive reason is `chart_details_changed`.

- [ ] **Step 1: Add failing write-gate tests**

For Paripraśna, consult, continue, and regenerate, pass a conversation with:

```typescript
{
  archived_at: '2026-09-27T10:00:00Z',
  archive_reason: 'chart_details_changed',
  archived_chart_snapshot: { birth_date: '1984-02-05', birth_time: '10:43:00' },
}
```

Assert no planner, model, persistence, or insert call occurs and the branchable code is `CONVERSATION_ARCHIVED_READ_ONLY`. Also test that Paripraśna refuses a fresh conversation while shared readiness is not ready, with `CHART_RECOMPUTE_REQUIRED`.

- [ ] **Step 2: Enforce gates at the earliest authenticated point**

In `authorizeTurn()`, after chart authorization and before consent/planning:

```typescript
const readiness = (await getChartReadinessMap([chartId])).get(chartId)
if (!readiness || !isDerivedChartReady(readiness)) {
  em.error({
    code: 'CHART_RECOMPUTE_REQUIRED',
    message: 'This chart is being recomputed. New readings will be available when it is ready.',
    retryable: true,
    phase: 'plan',
  })
  return halt('error')
}
```

When resolving `clientConversationId`, reject correction-archived rows before any new content. Mirror this guard in legacy consult/continue/regenerate so changing the URL cannot bypass read-only history.

- [ ] **Step 3: Lock correction archives in the generic conversation endpoint**

Allow GET. For PATCH title/pin/archive/folder and DELETE, return HTTP 409 with:

```json
{
  "error": "This conversation is historical and read-only.",
  "code": "CONVERSATION_ARCHIVED_READ_ONLY"
}
```

Manual archives whose `archive_reason` is null keep existing behaviour.

- [ ] **Step 4: Write the historical view test**

```typescript
render(<HistoricalConversationView conversation={historical} messages={messages} />)
expect(screen.getByRole('note')).toHaveTextContent(/before the chart details were corrected/i)
expect(screen.getByText(/05 Feb 1984/i)).toBeInTheDocument()
expect(screen.queryByRole('textbox')).not.toBeInTheDocument()
expect(screen.queryByRole('button', { name: /send|regenerate|unarchive/i })).not.toBeInTheDocument()
```

- [ ] **Step 5: Implement a reader-safe historical transcript loader**

Create `loadHistoricalConversationMessages(conversationId)` in `historicalReading.ts`. It returns:

```typescript
export interface HistoricalTranscriptMessage {
  id: string
  role: 'user' | 'assistant'
  text: string
  createdAt: string
}
```

For each `conversation_messages` row, prefer ordered canonical `message_parts` where `kind='text'` and concatenate only `body->>'text'`. If canonical text is absent, concatenate only `{ type: 'text', text: string }` entries from `parts_json`. Drop rows with no reader-visible text. Never return reasoning, raw tool calls, tool results, provider payloads, or audit metadata. The focused loader test must prove both the canonical preference and the legacy fallback.

- [ ] **Step 6: Implement the read-only historical transcript component**

Render the loader's user and assistant messages in `HistoricalConversationView`.

The header shows the pre-correction snapshot's birth date, time, place, timezone, coordinates, and ayanāṃśas plus `Historical · read-only`. Link back to `/clients/[id]`.

- [ ] **Step 7: Branch the consult conversation page**

After loading the conversation:

```tsx
if (isCorrectionArchived(conversation)) {
  const historicalMessages = await loadHistoricalConversationMessages(conversationId)
  return <HistoricalConversationView conversation={conversation} messages={historicalMessages} />
}
```

Leave the page's existing `ConsumeChat` return unchanged immediately after this early historical branch.

This prevents a composer from rendering even if a client-side guard regresses.

- [ ] **Step 8: Include archived Paripraśna history in the sidebar**

Fetch with `archived=true&readingsOnly=true`; carry `archived_at`, `archive_reason`, and `href`. `Sidebar` uses a real `Link` for persisted rows and invokes the in-shell callback only for the live session row. Correction-history rows display a quiet `Historical` badge and open `/clients/<chartId>/consult/<conversationId>`.

- [ ] **Step 9: Run conversation and Paripraśna suites**

```bash
cd platform
npx vitest run \
  src/app/api/pariprashna/__tests__/route.test.ts \
  src/app/api/conversations/__tests__/route.authz.test.ts \
  src/lib/conversations/__tests__/historicalReading.test.ts \
  src/components/consume/__tests__/HistoricalConversationView.test.tsx \
  src/components/pariprashna/__tests__/history_merge.test.tsx
```

Run the three new legacy-consult write-gate suites in the same verification pass:

```bash
npx vitest run \
  src/app/api/chat/consult/__tests__/archived-read-only.test.ts \
  src/app/api/chat/consult/continue/__tests__/archived-read-only.test.ts \
  src/app/api/chat/consult/regenerate/__tests__/archived-read-only.test.ts
```

- [ ] **Step 10: Commit**

```bash
git add platform/src/lib/pariprashna/pipeline/safety_gate.ts platform/src/lib/conversations platform/src/app/api/chat/consult platform/src/app/api/conversations platform/src/app/api/pariprashna platform/src/app/clients/'[id]'/consult platform/src/components/consume platform/src/components/pariprashna
git commit -m "feat(jataka): make corrected-chart history read-only"
```

---

## Task 9: Prove the complete local flow

**Files:**
- Create: `platform/tests/e2e/jataka-chart-workspace.spec.ts`

**Interfaces:**
- Uses a disposable local owner account and disposable local chart fixture.
- Must never target a remote base URL or non-local database.

- [ ] **Step 1: Add a local-only Playwright safety assertion**

```typescript
test.beforeAll(() => {
  const baseURL = process.env.PLAYWRIGHT_BASE_URL ?? 'http://127.0.0.1:3000'
  const host = new URL(baseURL).hostname
  expect(['localhost', '127.0.0.1', '::1']).toContain(host)
})
```

The test setup must create or identify disposable local data and record its IDs for cleanup. It must not delete any pre-existing chart.

- [ ] **Step 2: Implement the browser journey**

Cover these observable checkpoints:

```text
1. Jātakas grid/table has no Nirmāṇa, Paripraśna, Edit, Delete, Actions, or Current dasha.
2. Clicking the chart opens `/clients/<id>`.
3. D1 chart, identity, readiness, Nirmāṇa (owner), Paripraśna, and Pañcāṅga are visible.
4. Name-only edit returns to workspace and creates no new build run.
5. Birth-detail edit shows before/after and archival warning.
6. Confirming starts exactly one rebuild while retaining the same chart UUID.
7. Progress becomes Building and Paripraśna is unavailable.
8. Prior conversation is present in historical history and has no composer.
9. Once all required local assets are ready, Paripraśna becomes available again.
10. Desktop, 768px, and 390px layouts have no horizontal overflow.
11. Keyboard reaches card, actions menu, form, dialog, and historical back link.
12. Reduced-motion mode has no required animation; forced-colours/high-contrast retains state text.
```

For the expensive full build, mark the test with a clear `@local-recompute` tag so fast component CI can exclude it while the local acceptance command includes it.

- [ ] **Step 3: Apply migration only to the disposable local database**

After confirming the parsed `DATABASE_URL` host is local, preview and apply only this migration through the repository runner:

```bash
cd platform
npx tsx --env-file-if-exists=.env.local scripts/migrate.ts --dry-run --only 1080_jataka_conversation_archive_context.sql
npx tsx --env-file-if-exists=.env.local scripts/migrate.ts --only 1080_jataka_conversation_archive_context.sql
```

The dry run must name only the Jātaka archive-context migration. Record both command results in the final implementation report; do not apply through Supabase Cloud or any remote console.

- [ ] **Step 4: Run focused automated suites**

```bash
cd platform
npx vitest run \
  src/lib/charts/__tests__ \
  src/lib/build/__tests__/runPreparation.test.ts \
  src/lib/build/__tests__/assetInvalidation.test.ts \
  src/components/dashboard/__tests__/ClientCard.test.tsx \
  src/components/dashboard/__tests__/RosterTableView.test.tsx \
  src/components/profile/__tests__ \
  src/components/clients/__tests__/EditClientForm.test.tsx \
  src/components/dialogs/__tests__/EditRebuildConfirmDialog.test.tsx \
  src/components/consume/__tests__/HistoricalConversationView.test.tsx \
  src/components/pariprashna/__tests__/history_merge.test.tsx \
  src/app/api/charts/[id]/__tests__/route.patch.test.ts \
  src/app/api/cockpit/runs/__tests__/route.test.ts \
  src/app/api/cockpit/runs/__tests__/route.authz.test.ts \
  src/app/api/pariprashna/__tests__/route.test.ts
```

- [ ] **Step 5: Run static checks**

```bash
cd platform
npm run guard:migration-numbers
npx tsc --noEmit
npm run lint -- \
  src/lib/charts \
  src/lib/build/runPreparation.ts \
  src/lib/build/assetInvalidation.ts \
  src/lib/build/runDispatch.ts \
  src/app/dashboard \
  src/app/clients/'[id]' \
  src/app/api/charts/'[id]' \
  src/components/dashboard \
  src/components/profile \
  src/components/clients \
  src/components/dialogs/EditRebuildConfirmDialog.tsx \
  src/components/consume/HistoricalConversationView.tsx
```

If the repository-wide TypeScript baseline has pre-existing failures, compare against `.gate3_tsc_baseline.txt`, report only new failures, and do not claim a clean full typecheck.

- [ ] **Step 6: Run local browser acceptance**

```bash
cd platform
PLAYWRIGHT_BASE_URL=http://127.0.0.1:3000 npx playwright test tests/e2e/jataka-chart-workspace.spec.ts --project=chromium
```

Expected: the tagged local recompute journey passes against disposable data, including the transition back to Ready.

- [ ] **Step 7: Inspect the final diff for scope and secrets**

```bash
cd /Users/Dev/.codex/worktrees/jataka-chart-workspace/Madhav
git status --short
git diff --check
git diff --stat bf604c39b..HEAD
git diff --name-only bf604c39b..HEAD
```

Confirm no `.env*`, credentials, generated build output, Python-sidecar changes, governance artifacts, or unrelated files are present.

- [ ] **Step 8: Commit the acceptance test**

```bash
git add platform/tests/e2e/jataka-chart-workspace.spec.ts
git commit -m "test(jataka): prove workspace and recompute flow locally"
```

---

## Task 10: Final review and Claude Code handoff report

**Files:**
- No new product files unless a failing check requires an in-scope fix.

- [ ] **Step 1: Review every acceptance criterion against evidence**

Produce a table in the final Claude Code response with these columns:

```text
Criterion | Code/tests proving it | Local browser evidence | Status
```

Every item from specification section 14 must appear once. Use `Implemented`, `Locally proven`, or `Blocked`; do not use `Done` for a criterion lacking browser/database evidence.

- [ ] **Step 2: Run the final targeted verification once more after the last fix**

```bash
cd platform
npm run guard:migration-numbers
npx vitest run src/lib/charts/__tests__ src/components/dashboard/__tests__/ClientCard.test.tsx src/components/dashboard/__tests__/RosterTableView.test.tsx src/components/profile/__tests__ src/components/clients/__tests__/EditClientForm.test.tsx src/components/consume/__tests__/HistoricalConversationView.test.tsx src/app/api/charts/[id]/__tests__/route.patch.test.ts src/app/api/cockpit/runs/__tests__/route.test.ts src/app/api/pariprashna/__tests__/route.test.ts
npx tsc --noEmit
git diff --check bf604c39b..HEAD
```

- [ ] **Step 3: Request code review without deployment**

Report:

```text
- branch and final commit
- exact commands and exit status
- local migration applied/not applied and database identity without credentials
- disposable chart ID used for acceptance
- build run ID and terminal state
- archived conversation ID and read-only proof
- screenshots or Playwright trace paths if captured
- known pre-existing failures separated from new failures
- explicit statement: not pushed, not deployed, not production-verified
```

Do not push or open a pull request unless the user separately asks for it.

---

## Required Error Contract

The following codes are stable UI/API contracts for this feature:

| HTTP | Code | Meaning |
|---:|---|---|
| 401 | `UNAUTHENTICATED` | No authenticated user |
| 403 | `FORBIDDEN_CHART` | Caller lacks chart write authority, or the chart ID is absent; the endpoint does not enumerate chart existence |
| 409 | `RUN_ACTIVE` | A planned/running/paused build already exists |
| 409 | `CONVERSATION_ARCHIVED_READ_ONLY` | Historical correction conversation cannot mutate |
| 422 | `VALIDATION_FAILED` | Invalid normalized edit fields |
| 422 | `PROTECTED` | A required per-chart asset is protected |
| 422 | `INVALID_BUILD_PLAN` | Complete Gaṇita→Mīmāṃsā plan cannot be frozen |
| 422 | `CLEAR_SPEC_MISSING` | A writer asset has no safe strict invalidation path |
| 500 | `RECOMPUTE_PREPARATION_FAILED` | Transaction rolled back in full |
| 503 | `JOB_DISPATCH_FAILED` | Correction committed and cleared, local job did not start |

The Paripraśna SSE gate additionally emits `CHART_RECOMPUTE_REQUIRED` before planning when the chart is not ready.

## Completion Definition

Implementation is complete locally only when all of the following are true:

```text
dashboard is minimal and navigates to chart workspace
workspace shows D1, truthful shared readiness, capability deck, and permission-aware secondary actions
name-only edit does not create a build
chart-defining correction preserves chart identity and grants
strict transaction archives history, clears governed derived data, resets throughput, and freezes one rebuild run
pre-commit failure rolls back everything
post-commit local dispatch failure is shown as Needs rebuild
correction-archived conversations remain readable and cannot accept any mutation or turn
Paripraśna cannot start until shared readiness is Ready
focused tests, migration guard, scoped lint, and new-code typecheck are green
the full flow is demonstrated against disposable local data
no deployment, push, production mutation, or production acceptance claim has occurred
```
