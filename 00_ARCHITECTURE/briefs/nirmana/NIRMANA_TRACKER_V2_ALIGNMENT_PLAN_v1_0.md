---
artifact: NIRMANA_TRACKER_V2_ALIGNMENT_PLAN_v1_0.md
canonical_id: NIRMANA_TRACKER_V2_ALIGNMENT_PLAN
version: "1.0"
status: ACTIVE
produced_on: 2026-09-04
---

# Nirmāṇa Tracker v2 Alignment — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `/admin/nirmana-elevation` render the v2.0 programme spine (PHASE A → O-WAVE →
L0..L5 → PHASE Z, each layer with a W1–W6 milestone-aggregate bar) instead of the old flat
13-stage list, and make it refresh in near-real-time via the existing cockpit SSE bus — without
manufacturing any status the evidence ledger doesn't support.

**Architecture:** Additive layering, not a rewrite. The existing 6-milestone-per-asset projection
(`projectAssetMilestones`) and 13-stage machine (`projectCampaignStages`) are the source of truth
and are UNCHANGED. Three new pieces sit on top: (1) a tiny static "programme manifest"
(`programme.ts`) declaring the W1–W6 label↔milestone mapping and the O-wave's repo-declared WP
statuses; (2) two new pure projection functions that re-aggregate existing per-asset milestone
data into per-layer W1–W6 counts and summarize the pre-L0 / post-L5 stage groups into PHASE A /
PHASE Z; (3) UI components that group the existing flat stage list into the four programme
sections and render the new aggregate bars, with an explicit `repo-declared` vs `evidence-derived`
provenance chip on every programme-level field. Real-time refresh adds an `EventSource`
subscription to the existing chart-scoped cockpit SSE bus (scoped to the campaign's canonical
chart) plus a best-effort Pub/Sub publish on accepted capsule/supersession evidence writes.

**Tech Stack:** Next.js (App Router) + TypeScript, Zod schemas, Vitest + Testing Library, Google
Cloud Pub/Sub (`@google-cloud/pubsub`, already a dependency — see `watchdog/route.ts`).

**Spec:** `00_ARCHITECTURE/briefs/nirmana/NIRMANA_TRACKER_V2_ALIGNMENT_PROMPT_v1_0.md` (native-
authorized). This plan is written from a live fact-finding pass over the current code (verified
2026-09-04); where the spec's prose and the verified current code create a choice, this plan
records the ruling in **Rulings** below and the reasoning travels with it.

## Global Constraints

- **Write-set** (from spec §6): ONLY `platform/src/{components,lib}/nirmana-elevation/**`, the
  snapshot/evidence route files (`platform/src/app/api/admin/nirmana-elevation/{snapshot,evidence}/route.ts`),
  the admin page (`platform/src/app/admin/nirmana-elevation/page.tsx`), and tests. Do NOT touch
  `staleness.py`, `asset_runner.py`, `provenance.py`, `runner.py`/`global_runner.py`,
  `build/plan.ts`, `cockpit/runs/route.ts`, or `app/api/cockpit/sse/route.ts` /
  `app/api/cockpit/watchdog/route.ts` — the O-wave owns those files concurrently; this plan only
  ever *consumes* the SSE endpoint as an HTTP client and *duplicates* (never imports from) the
  watchdog's publish pattern into a file inside the allowed write-set.
- **No fabricated states** (spec §6 / CLAUDE.md §N.8): an ungrounded status is `unknown` with a
  reason, never green. `repo-declared` is a labeled provenance, not a loophole — every
  manifest-sourced field renders with the chip; evidence-derived fields never read from the
  manifest.
- **Vocabulary compatibility** (spec §3.2): `NIRMANA_STAGE_IDS` is NOT modified by this plan (see
  Ruling R1 below) — historical `stage_transition_accepted` events keep parsing unchanged, and
  `NirmanaCampaignStageSchema.order.max(12)` stays at 12.
- Existing suites (`projection.test.ts`, `definitions.test.ts`, `snapshot.test.ts`,
  `CampaignSpine.test.tsx`, `NirmanaElevationTracker.test.tsx`,
  `NirmanaElevationTracker.a11y.test.tsx`, `AssetCard.test.tsx`, `LayerStage.test.tsx`) must stay
  green throughout. Run the full nirmana-elevation slice after every task:
  `npx vitest run src/lib/nirmana-elevation src/components/nirmana-elevation src/app/api/admin/nirmana-elevation src/app/api/admin/internal/nirmana-elevation-executor src/app/api/admin/internal/nirmana-elevation-monitor`
- **Naming**: the new milestone-lifecycle "sub-wave" concept (`W1`..`W6`, one per
  `NIRMANA_MILESTONE_IDS` entry) is a DIFFERENT concept from the existing per-asset dependency
  batch "wave" (`V2WaveSchema.wave_index`, the 25/12/3-style batches gating build order). Never
  call the new concept "wave" unqualified in code or copy — always "programme wave" / `W1`–`W6`
  in code identifiers, "Wave 3 of 3" (existing) stays exactly as-is for the dependency batches.
- Every new/changed exported function needs a docstring only if it isn't self-evident from name +
  types (repo convention: default to none — see project CLAUDE.md "default to writing no
  comments").

## Rulings (pre-flight — read before dispatching Task 1)

**R1 — Do NOT add `O_WAVE` (or any phase id) to `NIRMANA_STAGE_IDS`.** The spec's §3.2 mentions
extending the vocab "additively... only where an event will actually be written," and offers it
as something the executor *may* do later. Verified fact-finding shows `NIRMANA_STAGE_IDS` is
consumed *positionally* in five places (`projection.ts`'s private `STAGE_KINDS`/`STAGE_GATES`
parallel arrays, `types.ts`'s `.max(12)` bound and `OrderedStagesSchema` exact-length check,
`definitions.ts`'s `indexOf`-based prerequisite check, `components/vocab.ts`'s exhaustive
`Record` type). PHASE A, O-WAVE, and PHASE Z are all achievable as a **pure presentation grouping**
over the *existing* 13 stage ids (PHASE A = the 5 pre-`L0` stages, O-WAVE = a manifest-only row
with no stage id at all, PHASE Z = `CLOSING`+`COMPLETE`) — zero vocab risk, zero positional-array
surgery, stays inside a 1-PR scope cap. If a future session wants a real `stage_transition_accepted
→ O_WAVE` evidence event, that is new scope for a later task, not this one.

**R2 — O-Wave's "active" state and a layer's "active" state are independent, not sequential.**
Spec §3 item 1's shorthand "L0..L5:... active = the first non-complete layer after O-wave
completes" reads as a strict gate, but the live campaign (`CAMPAIGN_STATE.md`, verified
2026-09-04) explicitly runs L0's W1 analysis *concurrently* with O-wave still open ("bounded-
pipelining default... W4 EXECUTE waits for O-wave to close" — only W4 waits, not W1-W3). The
existing `projectCampaignStages` layer `state` (`completed|active|locked|blocked|paused|unknown`)
already correctly reflects this concurrency because it's driven by real evidence, unchanged by
this plan. Overriding it with a new "only active after O-wave" rule would suppress real evidence,
violating the truth model ("the tracker projects evidence; it never manufactures it"). Ruling:
layer state in the programme spine is the EXISTING unchanged `stage.state` value, full stop. The
O-wave row's own state is independently derived purely from the manifest's WP statuses (never
gates or is gated by layer state). Both can show "active" at once — this is correct, not a bug.

**R3 — W1–W6 map 1:1 onto the 6 existing milestones, not a merge.** Spec's "PHASE A → O-WAVE → L0
→ ... each layer: W1 ANALYZE → W2 DECIDE → W3 IMPLEMENT → W4 EXECUTE → W5 VERIFY+CAPSULE → W6
FREEZE" lists exactly 6 sub-waves for exactly 6 milestones (`analysed, decision_accepted,
built_or_dispositioned, deployed_and_executed, verified, frozen`). A later bullet's shorthand "W3+W4
= built_or_dispositioned + deployed_and_executed" is read as listing that pair's *individual*
mappings (W3→built_or_dispositioned, W4→deployed_and_executed), not merging them into one bar —
6 milestones, 6 bars, exact existing names, zero new semantics.

**R4 — Evidence-write freshness ships the real Pub/Sub emit, not the poll fallback.** Spec §5.3
permits falling back to a 10s visible-poll "if wiring an emit is not cheap." Fact-finding confirms
it IS cheap: `app/api/cockpit/watchdog/route.ts` already has a working, minimal `publishEvent`
pattern (`@google-cloud/pubsub`, no-ops cleanly when `GOOGLE_CLOUD_PROJECT`/topic env is absent).
Task 5 duplicates this ~15-line pattern into a new file inside the allowed write-set (never edits
or imports from `watchdog/route.ts` itself, per the write-set constraint) and calls it from
`evidence-command.ts`. State this explicitly in the PR description per spec §5.3's own
instruction ("state which you shipped and why").

**R5 — O-wave WP statuses in the manifest are a snapshot, verified best-effort at Task 1 time,
not fabricated.** The manifest is repo-declared data this PR ships once; the O-wave's own PRs
(WP-1/WP-2/WP-3) are expected to update it going forward (spec §4). Task 1 instructs the
implementer to check live PR state for WP-1/WP-2/WP-3 before committing the initial values,
falling back to a stated conservative default if unreachable — never guess a `merged` status.

## File Structure

```
platform/src/lib/nirmana-elevation/
  programme.ts                  NEW — static manifest: W1-W6 defs, O-wave WP declarations
  __tests__/programme.test.ts   NEW
  projection.ts                 MODIFY — + projectLayerWaveProgress, summarizeStageGroupState,
                                          projectProgrammePosition
  types.ts                      MODIFY — + WaveProgressSchema, ProgrammeSnapshotSchema, wire into
                                          V2LayerSchema + NirmanaElevationSnapshotV2Schema
  snapshot.ts                   MODIFY — call new projection fns, populate new fields
  cockpit-events.ts             NEW — publishCockpitEvent() (Pub/Sub, duplicated pattern)
  __tests__/cockpit-events.test.ts  NEW
  evidence-command.ts           MODIFY — call publishCockpitEvent on asset_frozen / supersede
  __tests__/projection.test.ts  MODIFY — + describes for the 3 new functions
  __tests__/snapshot.test.ts    MODIFY — + programme field assertions
  __tests__/fixture-v2.ts       MODIFY — extend fixture with programme + wave_progress fields

platform/src/components/nirmana-elevation/
  vocab.ts                      MODIFY — + programmeWaveLabel, provenance copy helpers
  WaveProgressBar.tsx           NEW — per-layer W1-W6 aggregate bar
  WaveProgressBar.test.tsx      NEW
  ProvenanceChip.tsx            NEW — "repo-declared" / "evidence-derived" chip
  ProvenanceChip.test.tsx       NEW
  CampaignSpine.tsx             MODIFY — group stages into 4 programme sections
  CampaignSpine.test.tsx        MODIFY — assert new grouping
  CampaignSnapshotStrip.tsx     MODIFY — render snapshot.programme.position_label
  CampaignSnapshotStrip.test.tsx MODIFY
  LayerStage.tsx                MODIFY — render <WaveProgressBar> above existing wave lanes
  LayerStage.test.tsx           MODIFY
  NirmanaElevationTracker.tsx   MODIFY — + SSE subscription effect
  NirmanaElevationTracker.test.tsx MODIFY — + SSE-triggered refetch/debounce test
```

---

### Task 1: Programme manifest

**Files:**
- Create: `platform/src/lib/nirmana-elevation/programme.ts`
- Test: `platform/src/lib/nirmana-elevation/__tests__/programme.test.ts`

**Interfaces:**
- Produces: `PROGRAMME_WAVE_IDS`, `type ProgrammeWaveId`, `interface ProgrammeWaveDefinition
  { wave_id: ProgrammeWaveId; label: string; milestone_id: NirmanaMilestoneId }`,
  `PROGRAMME_WAVES: readonly ProgrammeWaveDefinition[]` (length 6, order W1..W6),
  `type ProgrammeWpId = 'WP-1' | 'WP-2' | 'WP-3'`, `type ProgrammeWpStatus = 'not_started' |
  'in_progress' | 'merged'`, `interface ProgrammeOWaveWpDeclaration { wp_id: ProgrammeWpId; name:
  string; status: ProgrammeWpStatus; note: string }`, `PROGRAMME_O_WAVE_WPS: readonly
  ProgrammeOWaveWpDeclaration[]` (length 3, order WP-1..WP-3), `PRE_L0_STAGE_IDS: readonly
  NirmanaStageId[]`, `POST_L5_STAGE_IDS: readonly NirmanaStageId[]`.

- [ ] **Step 1: Check live WP-1/WP-2/WP-3 PR state before writing values**

Run (best-effort — if this fails or `gh` is unavailable, use the fallback values below and note
it in your task report):

```bash
gh pr list --search "nirmana-owave" --state all --json number,title,state,mergedAt --limit 20
```

Map results to WP-1 (truthful invalidation / delta-directional staleness), WP-2 (delta-skip),
WP-3 (total plans) by title-matching. For each: `status = 'merged'` only if `mergedAt` is
non-null; `status = 'in_progress'` if an open PR exists; else `status = 'not_started'`. If you
cannot reach `gh` or find no matching PR for a WP, use `status: 'not_started'` for that WP and
say so in your report — never guess `'merged'`.

- [ ] **Step 2: Write `programme.ts`**

```typescript
import type { NirmanaStageId } from './projection'
import { NIRMANA_MILESTONE_IDS, NIRMANA_STAGE_IDS } from './vocab'

type NirmanaMilestoneId = typeof NIRMANA_MILESTONE_IDS[number]

export const PROGRAMME_WAVE_IDS = ['W1', 'W2', 'W3', 'W4', 'W5', 'W6'] as const
export type ProgrammeWaveId = typeof PROGRAMME_WAVE_IDS[number]

export interface ProgrammeWaveDefinition {
  wave_id: ProgrammeWaveId
  label: string
  milestone_id: NirmanaMilestoneId
}

/**
 * 1:1 mapping onto NIRMANA_MILESTONE_IDS — six programme sub-waves, six existing
 * asset milestones. Never merge or split these; see plan Ruling R3.
 */
export const PROGRAMME_WAVES: readonly ProgrammeWaveDefinition[] = [
  { wave_id: 'W1', label: 'ANALYZE', milestone_id: 'analysed' },
  { wave_id: 'W2', label: 'DECIDE', milestone_id: 'decision_accepted' },
  { wave_id: 'W3', label: 'IMPLEMENT', milestone_id: 'built_or_dispositioned' },
  { wave_id: 'W4', label: 'EXECUTE', milestone_id: 'deployed_and_executed' },
  { wave_id: 'W5', label: 'VERIFY+CAPSULE', milestone_id: 'verified' },
  { wave_id: 'W6', label: 'FREEZE', milestone_id: 'frozen' },
]

export type ProgrammeWpId = 'WP-1' | 'WP-2' | 'WP-3'
export type ProgrammeWpStatus = 'not_started' | 'in_progress' | 'merged'

export interface ProgrammeOWaveWpDeclaration {
  wp_id: ProgrammeWpId
  name: string
  status: ProgrammeWpStatus
  note: string
}

/**
 * Repo-declared, not evidence-derived (CLAUDE.md §N.8 / plan Ruling R5). Updated by the
 * O-wave PRs themselves as they merge — this file's values are a snapshot as of the PR
 * that introduces it, verified against live PR state at write time (see Task 1 Step 1).
 */
export const PROGRAMME_O_WAVE_WPS: readonly ProgrammeOWaveWpDeclaration[] = [
  {
    wp_id: 'WP-1',
    name: 'Truthful invalidation (delta-directional staleness)',
    status: 'in_progress', // REPLACE with the value found in Step 1
    note: 'repo-declared — flipped by the WP-1 PR on merge, not evidence-derived',
  },
  {
    wp_id: 'WP-2',
    name: 'Delta-skip',
    status: 'not_started', // REPLACE with the value found in Step 1
    note: 'repo-declared — flipped by the WP-2 PR on merge, not evidence-derived',
  },
  {
    wp_id: 'WP-3',
    name: 'Total plans',
    status: 'not_started', // REPLACE with the value found in Step 1
    note: 'repo-declared — flipped by the WP-3 PR on merge, not evidence-derived',
  },
]

const L0_INDEX = NIRMANA_STAGE_IDS.indexOf('L0')

/** The 5 stages that fold into PHASE A's collapsed history (plan Ruling R1). */
export const PRE_L0_STAGE_IDS: readonly NirmanaStageId[] = NIRMANA_STAGE_IDS.slice(0, L0_INDEX)

/** The stages that map onto PHASE Z. */
export const POST_L5_STAGE_IDS: readonly NirmanaStageId[] = ['CLOSING', 'COMPLETE']
```

- [ ] **Step 3: Write the test**

```typescript
import { describe, expect, it } from 'vitest'
import {
  PRE_L0_STAGE_IDS,
  POST_L5_STAGE_IDS,
  PROGRAMME_O_WAVE_WPS,
  PROGRAMME_WAVE_IDS,
  PROGRAMME_WAVES,
} from '../programme'
import { NIRMANA_MILESTONE_IDS, NIRMANA_STAGE_IDS } from '../vocab'

describe('programme manifest', () => {
  it('declares exactly 6 waves, one per milestone, in milestone order', () => {
    expect(PROGRAMME_WAVES.map((w) => w.wave_id)).toEqual(PROGRAMME_WAVE_IDS)
    expect(PROGRAMME_WAVES.map((w) => w.milestone_id)).toEqual(NIRMANA_MILESTONE_IDS)
  })

  it('declares exactly 3 O-wave WPs, all repo-declared, none guessed merged without a source', () => {
    expect(PROGRAMME_O_WAVE_WPS.map((wp) => wp.wp_id)).toEqual(['WP-1', 'WP-2', 'WP-3'])
    for (const wp of PROGRAMME_O_WAVE_WPS) {
      expect(['not_started', 'in_progress', 'merged']).toContain(wp.status)
      expect(wp.note).toContain('repo-declared')
    }
  })

  it('PRE_L0_STAGE_IDS is exactly the stages before L0, in order', () => {
    expect(PRE_L0_STAGE_IDS).toEqual(['BOOTSTRAP', 'T0_CENSUS', 'PLAN_FROZEN', 'DENOMINATOR_FROZEN', 'F0_FOUNDATION'])
    expect(NIRMANA_STAGE_IDS.slice(0, PRE_L0_STAGE_IDS.length)).toEqual(PRE_L0_STAGE_IDS)
  })

  it('POST_L5_STAGE_IDS is exactly CLOSING, COMPLETE', () => {
    expect(POST_L5_STAGE_IDS).toEqual(['CLOSING', 'COMPLETE'])
  })
})
```

- [ ] **Step 4: Run the test, verify it passes**

Run: `npx vitest run src/lib/nirmana-elevation/__tests__/programme.test.ts`
Expected: PASS, 4/4.

- [ ] **Step 5: Commit**

```bash
git add src/lib/nirmana-elevation/programme.ts src/lib/nirmana-elevation/__tests__/programme.test.ts
git commit -m "feat(nirmana-tracker): add v2 programme manifest (W1-W6 waves, O-wave WP declarations)"
```

---

### Task 2: Projection — wave-progress aggregation and stage-group summarization

**Files:**
- Modify: `platform/src/lib/nirmana-elevation/projection.ts`
- Modify: `platform/src/lib/nirmana-elevation/__tests__/projection.test.ts`

**Interfaces:**
- Consumes: `PROGRAMME_WAVES`, `ProgrammeWaveId` from `./programme` (Task 1); `AssetMilestoneProjection`
  (already exported from this file — has `.milestones: { milestone_id, state, ... }[]`, confirm
  shape by reading the existing interface before writing new code — do not guess its fields).
- Produces: `interface WaveProgressCount { wave_id: ProgrammeWaveId; label: string; milestone_id:
  string; earned: number; required: number }`, `function projectLayerWaveProgress(assets:
  { layer: NirmanaLayerId; milestones: { milestone_id: string; state: string }[] }[], layerId:
  NirmanaLayerId): WaveProgressCount[]` (always returns exactly 6 entries, in W1..W6 order),
  `function summarizeStageGroupState(stages: { stage_id: NirmanaStageId; state:
  NirmanaCampaignStage_state }[], groupIds: readonly NirmanaStageId[]): 'completed' | 'active' |
  'locked' | 'blocked' | 'paused' | 'unknown'`, `interface ProgrammePosition { phase_id: 'PHASE_A'
  | 'O_WAVE' | NirmanaLayerId | 'PHASE_Z'; label: string }`, `function projectProgrammePosition(args:
  { currentStage: NirmanaStageId | null; layerWaveProgress: Partial<Record<NirmanaLayerId,
  WaveProgressCount[]>>; layerNames: Partial<Record<NirmanaLayerId, string>>; openWp:
  { wp_id: string } | null }): ProgrammePosition`.

Read `projection.ts` in full before starting (650 lines) — in particular the exact shape of
`AssetMilestoneProjection` (what field holds the milestones array and each milestone's `state`
union) and the state type used by `NirmanaCampaignStage`-like objects (`completed | active |
locked | blocked | paused | unknown`), so your new function signatures type-check against what
actually exists rather than what this plan assumes.

- [ ] **Step 1: Write the failing tests** — append 3 new `describe` blocks to the end of
  `projection.test.ts` (do not touch the existing 3 describes):

```typescript
describe('projectLayerWaveProgress', () => {
  const asset = (layer: NirmanaLayerId, states: Record<string, 'earned' | 'current' | 'pending' | 'not_applicable'>) => ({
    layer,
    milestones: Object.entries(states).map(([milestone_id, state]) => ({ milestone_id, state })),
  })

  it('returns exactly 6 entries in W1..W6 order for a layer with no assets', () => {
    const result = projectLayerWaveProgress([], 'L0')
    expect(result.map((w) => w.wave_id)).toEqual(['W1', 'W2', 'W3', 'W4', 'W5', 'W6'])
    expect(result.every((w) => w.earned === 0 && w.required === 0)).toBe(true)
  })

  it('counts earned/required per milestone, excluding not_applicable from the denominator', () => {
    const assets = [
      asset('L0', { analysed: 'earned', decision_accepted: 'earned', built_or_dispositioned: 'earned', deployed_and_executed: 'not_applicable', verified: 'current', frozen: 'pending' }),
      asset('L0', { analysed: 'earned', decision_accepted: 'pending', built_or_dispositioned: 'pending', deployed_and_executed: 'earned', verified: 'pending', frozen: 'pending' }),
    ]
    const result = projectLayerWaveProgress(assets, 'L0')
    const byWave = Object.fromEntries(result.map((w) => [w.wave_id, w]))
    expect(byWave.W1).toMatchObject({ earned: 2, required: 2 })
    expect(byWave.W2).toMatchObject({ earned: 1, required: 2 })
    expect(byWave.W4).toMatchObject({ earned: 1, required: 1 }) // one asset's deployed_and_executed is not_applicable, excluded
  })

  it('ignores assets from other layers', () => {
    const assets = [asset('L1', { analysed: 'earned', decision_accepted: 'pending', built_or_dispositioned: 'pending', deployed_and_executed: 'pending', verified: 'pending', frozen: 'pending' })]
    const result = projectLayerWaveProgress(assets, 'L0')
    expect(result.every((w) => w.required === 0)).toBe(true)
  })
})

describe('summarizeStageGroupState', () => {
  const stage = (stage_id: string, state: string) => ({ stage_id: stage_id as NirmanaStageId, state: state as never })

  it('is completed only when every member is completed', () => {
    const stages = [stage('BOOTSTRAP', 'completed'), stage('T0_CENSUS', 'completed')]
    expect(summarizeStageGroupState(stages, ['BOOTSTRAP', 'T0_CENSUS'])).toBe('completed')
  })

  it('surfaces blocked over any other non-completed state', () => {
    const stages = [stage('BOOTSTRAP', 'completed'), stage('T0_CENSUS', 'blocked'), stage('PLAN_FROZEN', 'locked')]
    expect(summarizeStageGroupState(stages, ['BOOTSTRAP', 'T0_CENSUS', 'PLAN_FROZEN'])).toBe('blocked')
  })

  it('surfaces active when nothing is blocked or paused', () => {
    const stages = [stage('BOOTSTRAP', 'completed'), stage('T0_CENSUS', 'active'), stage('PLAN_FROZEN', 'locked')]
    expect(summarizeStageGroupState(stages, ['BOOTSTRAP', 'T0_CENSUS', 'PLAN_FROZEN'])).toBe('active')
  })

  it('is unknown for an empty or unmatched group', () => {
    expect(summarizeStageGroupState([], ['BOOTSTRAP'])).toBe('unknown')
  })
})

describe('projectProgrammePosition', () => {
  it('reports execution not yet evidenced when there is no current stage', () => {
    const position = projectProgrammePosition({ currentStage: null, layerWaveProgress: {}, layerNames: {}, openWp: null })
    expect(position.phase_id).toBe('PHASE_A')
  })

  it('reports PHASE_A for any pre-L0 stage', () => {
    const position = projectProgrammePosition({ currentStage: 'F0_FOUNDATION', layerWaveProgress: {}, layerNames: {}, openWp: null })
    expect(position.phase_id).toBe('PHASE_A')
  })

  it('reports the layer id for a layer stage, independent of openWp', () => {
    const layerWaveProgress = { L0: [{ wave_id: 'W1' as const, label: 'ANALYZE', milestone_id: 'analysed', earned: 17, required: 40 }] }
    const position = projectProgrammePosition({ currentStage: 'L0', layerWaveProgress, layerNames: { L0: 'Brahmagyan' }, openWp: { wp_id: 'WP-1' } })
    expect(position.phase_id).toBe('L0')
    expect(position.label).toContain('L0')
    expect(position.label).toContain('W1')
    expect(position.label).toContain('17/40')
  })

  it('reports PHASE_Z for CLOSING/COMPLETE', () => {
    expect(projectProgrammePosition({ currentStage: 'CLOSING', layerWaveProgress: {}, layerNames: {}, openWp: null }).phase_id).toBe('PHASE_Z')
    expect(projectProgrammePosition({ currentStage: 'COMPLETE', layerWaveProgress: {}, layerNames: {}, openWp: null }).phase_id).toBe('PHASE_Z')
  })
})
```

Add the necessary new imports at the top of `projection.test.ts`:
`projectLayerWaveProgress, summarizeStageGroupState, projectProgrammePosition` from `../projection`.

- [ ] **Step 2: Run the tests, verify they fail** (functions don't exist yet)

Run: `npx vitest run src/lib/nirmana-elevation/__tests__/projection.test.ts`
Expected: FAIL — `projectLayerWaveProgress is not a function` (or TS compile error naming it).

- [ ] **Step 3: Implement the three functions in `projection.ts`**

Add near the bottom of the file, after the existing `deriveEligibleNextAssetIds` (append, do not
reorder existing exports):

```typescript
import { PROGRAMME_WAVES, type ProgrammeWaveId } from './programme'

export interface WaveProgressCount {
  wave_id: ProgrammeWaveId
  label: string
  milestone_id: string
  earned: number
  required: number
}

export function projectLayerWaveProgress(
  assets: { layer: NirmanaLayerId; milestones: { milestone_id: string; state: string }[] }[],
  layerId: NirmanaLayerId,
): WaveProgressCount[] {
  const layerAssets = assets.filter((asset) => asset.layer === layerId)
  return PROGRAMME_WAVES.map((wave) => {
    let earned = 0
    let required = 0
    for (const asset of layerAssets) {
      const milestone = asset.milestones.find((candidate) => candidate.milestone_id === wave.milestone_id)
      if (!milestone || milestone.state === 'not_applicable') continue
      required += 1
      if (milestone.state === 'earned') earned += 1
    }
    return { wave_id: wave.wave_id, label: wave.label, milestone_id: wave.milestone_id, earned, required }
  })
}

type StageGroupState = 'completed' | 'active' | 'locked' | 'blocked' | 'paused' | 'unknown'

export function summarizeStageGroupState(
  stages: { stage_id: NirmanaStageId; state: StageGroupState }[],
  groupIds: readonly NirmanaStageId[],
): StageGroupState {
  const members = groupIds
    .map((id) => stages.find((stage) => stage.stage_id === id))
    .filter((stage): stage is { stage_id: NirmanaStageId; state: StageGroupState } => stage !== undefined)
  if (members.length === 0) return 'unknown'
  if (members.every((stage) => stage.state === 'completed')) return 'completed'
  if (members.some((stage) => stage.state === 'blocked')) return 'blocked'
  if (members.some((stage) => stage.state === 'paused')) return 'paused'
  if (members.some((stage) => stage.state === 'active')) return 'active'
  if (members.some((stage) => stage.state === 'locked')) return 'locked'
  return 'unknown'
}

export interface ProgrammePosition {
  phase_id: 'PHASE_A' | 'O_WAVE' | NirmanaLayerId | 'PHASE_Z'
  label: string
}

export function projectProgrammePosition(args: {
  currentStage: NirmanaStageId | null
  layerWaveProgress: Partial<Record<NirmanaLayerId, WaveProgressCount[]>>
  layerNames: Partial<Record<NirmanaLayerId, string>>
  openWp: { wp_id: string } | null
}): ProgrammePosition {
  const { currentStage, layerWaveProgress, layerNames, openWp } = args

  if (currentStage === null || !/^L[0-5]$/.test(currentStage)) {
    if (currentStage === 'CLOSING' || currentStage === 'COMPLETE') {
      return { phase_id: 'PHASE_Z', label: currentStage === 'COMPLETE' ? 'PHASE Z · Complete' : 'PHASE Z · Closing' }
    }
    if (openWp) return { phase_id: 'O_WAVE', label: `O-WAVE · ${openWp.wp_id}` }
    return { phase_id: 'PHASE_A', label: currentStage ? 'PHASE A' : 'Execution not yet evidenced' }
  }

  const layerId = currentStage as NirmanaLayerId
  const progress = layerWaveProgress[layerId] ?? []
  const activeWave = progress.find((wave) => wave.required > 0 && wave.earned < wave.required)
  const layerName = layerNames[layerId] ?? layerId
  const openWpPrefix = openWp ? `O-WAVE · ${openWp.wp_id} · ` : ''
  if (activeWave) {
    return {
      phase_id: layerId,
      label: `${openWpPrefix}${layerId} · ${activeWave.wave_id} (${activeWave.earned}/${activeWave.required} ${activeWave.milestone_id})`,
    }
  }
  return { phase_id: layerId, label: `${openWpPrefix}${layerId} · ${layerName}` }
}
```

Adjust the exact field/type names above to match what you found reading the file in the setup
step (e.g. if the campaign-stage state type is exported under a different name, use that name —
the behavior specified by the tests is authoritative, not the exact type syntax shown here).

- [ ] **Step 4: Run the tests, verify they pass**

Run: `npx vitest run src/lib/nirmana-elevation/__tests__/projection.test.ts`
Expected: PASS, all describes including the 3 new ones.

- [ ] **Step 5: Run the full existing suite to confirm no regression**

Run: `npx vitest run src/lib/nirmana-elevation`
Expected: PASS, same pass count as before plus the new tests.

- [ ] **Step 6: Commit**

```bash
git add src/lib/nirmana-elevation/projection.ts src/lib/nirmana-elevation/__tests__/projection.test.ts
git commit -m "feat(nirmana-tracker): add wave-progress aggregation and programme-position projection"
```

---

### Task 3: Schema extension and snapshot wiring

**Files:**
- Modify: `platform/src/lib/nirmana-elevation/types.ts`
- Modify: `platform/src/lib/nirmana-elevation/snapshot.ts`
- Modify: `platform/src/lib/nirmana-elevation/__tests__/snapshot.test.ts`
- Modify: `platform/src/lib/nirmana-elevation/__tests__/fixture-v2.ts`

**Interfaces:**
- Consumes: `PROGRAMME_WAVES`, `PROGRAMME_WAVE_IDS`, `PROGRAMME_O_WAVE_WPS`, `PRE_L0_STAGE_IDS`,
  `POST_L5_STAGE_IDS` (Task 1); `projectLayerWaveProgress`, `summarizeStageGroupState`,
  `projectProgrammePosition`, `WaveProgressCount`, `ProgrammePosition` (Task 2).
- Produces: `V2LayerSchema` gains `wave_progress: WaveProgressCount[]` (6 entries);
  `NirmanaElevationSnapshotV2Schema` gains `programme: { position_label: string; o_wave: {
  provenance: 'repo_declared'; state: 'locked'|'active'|'completed'; wps: { wp_id: string; name:
  string; status: string; note: string }[] }; phase_a: { provenance: 'evidence_derived'; state:
  string; collapsed_stage_ids: string[] }; phase_z: { provenance: 'evidence_derived'; state:
  string } }`.

Read `types.ts` lines 1-350 and `snapshot.ts` in full (or at minimum grep for where `layers:` and
`campaign:` fields of the V2 snapshot object are assembled) before editing, so the new fields are
populated at the exact point the rest of the V2-only data is assembled (search for where the
code branches on `schema_version === '2.0'` or equivalent — do not guess the location).

- [ ] **Step 1: Add the new Zod schemas to `types.ts`**, directly above
  `NirmanaElevationSnapshotV2Schema` (around line 321):

```typescript
import { PROGRAMME_WAVE_IDS } from './programme'

const WaveProgressSchema = z.object({
  wave_id: z.enum(PROGRAMME_WAVE_IDS),
  label: z.string(),
  milestone_id: z.enum(NIRMANA_MILESTONE_IDS),
  earned: z.number().int().nonnegative(),
  required: z.number().int().nonnegative(),
}).superRefine((wave, context) => {
  if (wave.earned > wave.required) {
    context.addIssue({ code: 'custom', path: ['earned'], message: 'A wave cannot have earned more than its required count.' })
  }
})

const ProgrammeOWaveWpSchema = z.object({
  wp_id: z.enum(['WP-1', 'WP-2', 'WP-3']),
  name: z.string(),
  status: z.enum(['not_started', 'in_progress', 'merged']),
  note: z.string(),
})

const ProgrammeOperationalStateSchema = z.enum(['completed', 'active', 'locked', 'blocked', 'paused', 'unknown'])

const ProgrammeSnapshotSchema = z.object({
  position_label: z.string(),
  o_wave: z.object({
    provenance: z.literal('repo_declared'),
    state: ProgrammeOperationalStateSchema,
    wps: z.array(ProgrammeOWaveWpSchema).length(3),
  }),
  phase_a: z.object({
    provenance: z.literal('evidence_derived'),
    state: ProgrammeOperationalStateSchema,
    collapsed_stage_ids: z.array(z.enum(NIRMANA_STAGE_IDS)),
  }),
  phase_z: z.object({
    provenance: z.literal('evidence_derived'),
    state: ProgrammeOperationalStateSchema,
  }),
})
```

- [ ] **Step 2: Wire `wave_progress` into `V2LayerSchema`** — find the `V2LayerSchema` definition
  (around line 176) and add `wave_progress: z.array(WaveProgressSchema).length(6),` to its
  `.extend({...})` object, alongside the existing `waves: z.array(V2WaveSchema)` field (do not
  remove `waves` — it stays, unchanged, for the existing per-asset dependency-batch lanes).

- [ ] **Step 3: Wire `programme` into `NirmanaElevationSnapshotV2Schema`** — inside its
  `.extend({...})` (around line 322), add `programme: ProgrammeSnapshotSchema,` alongside the
  existing `stages`, `layers`, `program_sync` fields.

- [ ] **Step 4: Populate the new fields in `snapshot.ts`**

Find where each V2 layer object is assembled (search for where `waves:` or `eligible_next_asset_ids:`
is set per layer) and add a `wave_progress:` field computed via `projectLayerWaveProgress(assets,
layer.layer_id)`, passing the already-computed per-asset `milestones` array for that layer's
assets (the same assets list already used elsewhere in this function — do not re-fetch).

Find where the top-level V2 snapshot object is assembled (search for where `stages:` and `layers:`
are set at the top level) and add:

```typescript
const phaseAState = summarizeStageGroupState(stages, PRE_L0_STAGE_IDS)
const phaseZState = summarizeStageGroupState(stages, POST_L5_STAGE_IDS)
const oWaveState: 'locked' | 'active' | 'completed' =
  phaseAState !== 'completed' ? 'locked'
    : PROGRAMME_O_WAVE_WPS.every((wp) => wp.status === 'merged') ? 'completed'
      : 'active'
const openWp = oWaveState === 'active' ? PROGRAMME_O_WAVE_WPS.find((wp) => wp.status !== 'merged') ?? null : null
const layerWaveProgress = Object.fromEntries(layers.map((layer) => [layer.layer_id, layer.wave_progress]))
const layerNames = Object.fromEntries(layers.map((layer) => [layer.layer_id, layer.layer_name]))
const position = projectProgrammePosition({
  currentStage: campaign.current_stage,
  layerWaveProgress,
  layerNames,
  openWp: openWp ? { wp_id: openWp.wp_id } : null,
})

const programme = {
  position_label: position.label,
  o_wave: {
    provenance: 'repo_declared' as const,
    state: oWaveState,
    wps: PROGRAMME_O_WAVE_WPS.map((wp) => ({ wp_id: wp.wp_id, name: wp.name, status: wp.status, note: wp.note })),
  },
  phase_a: {
    provenance: 'evidence_derived' as const,
    state: phaseAState,
    collapsed_stage_ids: PRE_L0_STAGE_IDS,
  },
  phase_z: {
    provenance: 'evidence_derived' as const,
    state: phaseZState,
  },
}
```

Then include `programme` in the object passed to `NirmanaElevationSnapshotV2Schema.parse(...)` (or
equivalent construction site), alongside the existing `stages`, `layers` fields. Adjust variable
names above (`stages`, `layers`, `campaign`, `assets`) to whatever the actual local variable names
are at that point in `snapshot.ts` — read the surrounding ~40 lines before inserting so this
slots into the real assembly order (the V2-only fields must be computed after `stages`/`layers`
exist, since `programme` depends on both).

- [ ] **Step 5: Update the V2 test fixture**

In `__tests__/fixture-v2.ts`, extend the fixture layer objects with a `wave_progress` array (6
entries matching `PROGRAMME_WAVE_IDS`, arbitrary consistent earned/required numbers) and the
top-level fixture snapshot with a `programme` object matching the new schema shape (use
`in_progress` for one O-wave WP, `not_started` for the other two, to keep the fixture realistic).

- [ ] **Step 6: Extend `snapshot.test.ts`**

Add assertions (in whichever existing `it`/`describe` builds and validates a full V2 snapshot)
that: `result.programme.position_label` is a non-empty string; `result.programme.o_wave.wps` has
length 3; every layer in `result.layers` has `wave_progress` with length 6 and each entry's
`earned <= required`; `result.programme.phase_a.collapsed_stage_ids` equals `['BOOTSTRAP',
'T0_CENSUS', 'PLAN_FROZEN', 'DENOMINATOR_FROZEN', 'F0_FOUNDATION']`.

- [ ] **Step 7: Run the tests**

Run: `npx vitest run src/lib/nirmana-elevation`
Expected: PASS — all prior tests plus the new/extended ones. If `types-v2.test.ts` or
`definitions.test.ts` fail due to the schema extension, fix the fixtures they use (they must also
gain the new required fields) — do not weaken the new schema fields to `.optional()` to make old
fixtures pass; fix the fixtures.

- [ ] **Step 8: Commit**

```bash
git add src/lib/nirmana-elevation/types.ts src/lib/nirmana-elevation/snapshot.ts src/lib/nirmana-elevation/__tests__/snapshot.test.ts src/lib/nirmana-elevation/__tests__/fixture-v2.ts
git commit -m "feat(nirmana-tracker): wire programme spine data into the v2 snapshot schema"
```

---

### Task 4: UI — programme spine rendering

**Files:**
- Create: `platform/src/components/nirmana-elevation/WaveProgressBar.tsx`
- Create: `platform/src/components/nirmana-elevation/WaveProgressBar.test.tsx`
- Create: `platform/src/components/nirmana-elevation/ProvenanceChip.tsx`
- Create: `platform/src/components/nirmana-elevation/ProvenanceChip.test.tsx`
- Modify: `platform/src/components/nirmana-elevation/vocab.ts`
- Modify: `platform/src/components/nirmana-elevation/CampaignSpine.tsx`
- Modify: `platform/src/components/nirmana-elevation/CampaignSpine.test.tsx`
- Modify: `platform/src/components/nirmana-elevation/CampaignSnapshotStrip.tsx`
- Modify: `platform/src/components/nirmana-elevation/CampaignSnapshotStrip.test.tsx`
- Modify: `platform/src/components/nirmana-elevation/LayerStage.tsx`
- Modify: `platform/src/components/nirmana-elevation/LayerStage.test.tsx`

**Interfaces:**
- Consumes: `snapshot.programme` and `layer.wave_progress` (Task 3); the existing
  `NirmanaCampaignStage`, `NirmanaElevationSnapshotV2` types; the existing `FoundationStage`,
  `LayerStage` components (unchanged internally, just relocated in the render tree — see Step 3).

Read the CURRENT `CampaignSpine.tsx` and `CampaignSnapshotStrip.tsx` in full before editing (both
under 150 lines) — this plan's snippets below are additive edits, not full replacements; preserve
every existing prop, accessibility attribute (`aria-expanded`, `aria-controls`, keyboard handler),
and CSS class not explicitly changed here.

- [ ] **Step 1: `ProvenanceChip.tsx`** — small, no dependency on any other new file:

```typescript
export function ProvenanceChip({ kind }: { kind: 'repo_declared' | 'evidence_derived' }) {
  const label = kind === 'repo_declared' ? 'Repo-declared' : 'Evidence-derived'
  const className = kind === 'repo_declared'
    ? 'border-brand-warn/60 text-brand-warn'
    : 'border-brand-ok/50 text-brand-ok'
  return <span
    className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.1em] ${className}`}
    title={kind === 'repo_declared' ? 'Sourced from the committed programme manifest, not the evidence ledger' : 'Derived from accepted campaign evidence'}
  >{label}</span>
}
```

Test (`ProvenanceChip.test.tsx`):

```typescript
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { ProvenanceChip } from './ProvenanceChip'

describe('ProvenanceChip', () => {
  it('renders Repo-declared for repo_declared', () => {
    render(<ProvenanceChip kind="repo_declared" />)
    expect(screen.getByText('Repo-declared')).toBeInTheDocument()
  })
  it('renders Evidence-derived for evidence_derived', () => {
    render(<ProvenanceChip kind="evidence_derived" />)
    expect(screen.getByText('Evidence-derived')).toBeInTheDocument()
  })
})
```

- [ ] **Step 2: `WaveProgressBar.tsx`** — takes the 6-entry `wave_progress` array for one layer:

```typescript
import type { WaveProgressCount } from '@/lib/nirmana-elevation/projection'

export function WaveProgressBar({ waveProgress }: { waveProgress: WaveProgressCount[] }) {
  return <ol aria-label="Programme sub-wave progress" className="grid grid-cols-6 gap-1.5">
    {waveProgress.map((wave) => {
      const complete = wave.required > 0 && wave.earned === wave.required
      const empty = wave.required === 0
      return <li key={wave.wave_id} className={`rounded-md border px-1.5 py-1 text-center text-[10px] ${
        complete ? 'border-brand-ok/60 bg-brand-ok/10 text-brand-ok'
          : empty ? 'border-brand-border text-brand-text-3'
            : 'border-brand-gold-1/50 text-brand-gold-2'
      }`}>
        <span className="block font-semibold">{wave.wave_id}</span>
        <span className="block">{wave.label}</span>
        <span className="mt-0.5 block font-mono">{wave.earned}/{wave.required}</span>
      </li>
    })}
  </ol>
}
```

Test (`WaveProgressBar.test.tsx`):

```typescript
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { WaveProgressBar } from './WaveProgressBar'

const waveProgress = [
  { wave_id: 'W1' as const, label: 'ANALYZE', milestone_id: 'analysed', earned: 17, required: 40 },
  { wave_id: 'W2' as const, label: 'DECIDE', milestone_id: 'decision_accepted', earned: 0, required: 40 },
  { wave_id: 'W3' as const, label: 'IMPLEMENT', milestone_id: 'built_or_dispositioned', earned: 0, required: 40 },
  { wave_id: 'W4' as const, label: 'EXECUTE', milestone_id: 'deployed_and_executed', earned: 0, required: 40 },
  { wave_id: 'W5' as const, label: 'VERIFY+CAPSULE', milestone_id: 'verified', earned: 0, required: 40 },
  { wave_id: 'W6' as const, label: 'FREEZE', milestone_id: 'frozen', earned: 0, required: 40 },
]

describe('WaveProgressBar', () => {
  it('renders all 6 waves with their earned/required counts', () => {
    render(<WaveProgressBar waveProgress={waveProgress} />)
    expect(screen.getByText('17/40')).toBeInTheDocument()
    expect(screen.getAllByText('0/40')).toHaveLength(5)
    expect(screen.getByText('W1')).toBeInTheDocument()
    expect(screen.getByText('FREEZE')).toBeInTheDocument()
  })
})
```

- [ ] **Step 3: Render `<WaveProgressBar>` inside `LayerStage.tsx`**

Read the current file (59 lines). Add a `waveProgress: WaveProgressCount[]` prop to `LayerStage`'s
props type, thread it in from wherever `<LayerStage>` is invoked (`CampaignSpine.tsx`'s
`StageBody`, passing `layer.wave_progress`), and render `<WaveProgressBar waveProgress={waveProgress} />`
immediately above the existing overall progress bar / legend, inside the same top section — do
not touch the eligible-next-preview or wave-lane iteration below it. Update `LayerStage.test.tsx`'s
existing render calls to pass a `waveProgress` fixture (6 entries, same shape as Step 2's test
fixture) so the existing tests keep compiling and passing; add one new assertion that the bar's
`W1`..`W6` labels render.

- [ ] **Step 4: Group `CampaignSpine.tsx`'s stage list into 4 programme sections**

Replace the current single flat `<ol>{stages.map(...)}</ol>` with 4 sections, reusing the EXACT
same per-stage `<article>` rendering (the `StageBody`/`statusIcon`/`statusLabel`/`countLabel`
helpers and the `toggle`/`expanded` state stay as-is, unchanged) for each stage still rendered
individually. Structure:

```typescript
import { ProvenanceChip } from './ProvenanceChip'
import { PRE_L0_STAGE_IDS } from '@/lib/nirmana-elevation/programme'

// inside CampaignSpine, after `const stages = [...snapshot.stages].sort(...)`:
const phaseAStages = stages.filter((stage) => PRE_L0_STAGE_IDS.includes(stage.stage_id))
const layerStages = stages.filter((stage) => /^L[0-5]$/.test(stage.stage_id))
const phaseZStages = stages.filter((stage) => stage.stage_id === 'CLOSING' || stage.stage_id === 'COMPLETE')
```

Render order: (1) a PHASE A section — a single summary row showing `snapshot.programme.phase_a.state`
via the existing `statusIcon`/`statusLabel` helpers plus a `<ProvenanceChip kind="evidence_derived" />`,
that expands (reusing the existing `expanded`/`toggle` state, keyed by a sentinel id e.g.
`'PHASE_A_GROUP'` added to the `Set<NirmanaStageId | 'PHASE_A_GROUP'>` type) to reveal the
`phaseAStages` rendered exactly as today (same `<li>`/`<article>` markup, looped); (2) an O-WAVE
section — one row (no expand/collapse needed, or optionally expandable to list the 3 WPs) showing
`snapshot.programme.o_wave.state` via the same icon/label helpers, a `<ProvenanceChip
kind="repo_declared" />`, and each `snapshot.programme.o_wave.wps` entry as `${wp.name}: ${wp.status}`;
(3) the `layerStages` rendered exactly as today, one `<li>` each (no grouping change — each layer
keeps its own expand/collapse); (4) a PHASE Z section, same summary-row pattern as PHASE A but for
`phaseZStages` and `snapshot.programme.phase_z`. Keep the existing `aria-label="Nirmāṇa campaign
stages"` semantics — wrap each of the 4 sections in a `<section>` with its own `aria-label` (e.g.
`"Phase A"`, `"O-Wave"`, `"Layers"`, `"Phase Z"`) inside the outer spine `<section>`, each
containing its own `<ol>`.

Do not delete `FoundationStage` usage — it still renders inside the PHASE A group's expanded
`phaseAStages` items exactly as it does today (via the unchanged `StageBody` dispatch on
`stage.kind === 'census' | 'foundation'`).

Update `CampaignSpine.test.tsx`: existing tests that assert individual stage rows render should
still pass once the PHASE A group is expanded (adjust any test that expects `T0_CENSUS` etc. to
render un-collapsed by default — expand the PHASE A group first via the same click/keyboard
interaction pattern the existing tests already use for other stages). Add new assertions: an
"O-WAVE" heading renders; each of the 3 WP names + statuses render; a `Repo-declared` chip
renders next to the O-wave section; an `Evidence-derived` chip renders next to Phase A and Phase
Z; `L0`'s row still renders exactly as before (unchanged layer rendering, now receiving
`waveProgress` via Step 3's prop threading).

- [ ] **Step 5: `CampaignSnapshotStrip.tsx`'s position chip**

Replace the current `stagePosition()` function's body with:

```typescript
function stagePosition(snapshot: NirmanaElevationSnapshotV2): string {
  return snapshot.programme.position_label
}
```

Leave every other function in this file untouched. Update `CampaignSnapshotStrip.test.tsx`: any
test asserting the OLD `stagePosition` format (e.g. `"L0 · Brahmagyan · Wave 3"`) must instead
assert against a `programme.position_label` value set directly in that test's fixture snapshot
(construct the fixture's `programme.position_label` to match what the test wants to verify is
displayed — do not re-derive it in the test, since the derivation is now covered by Task 2's
`projectProgrammePosition` unit tests, not this component test).

- [ ] **Step 6: `vocab.ts`** — no changes required if Steps 1-5 above didn't introduce a need for
  new display-name lookups (the O-wave/Phase A/Phase Z labels are inline strings in Step 4, not
  routed through `stageDisplayName`). Skip this file unless a step above created a compile error
  referencing a missing export — if so, add the minimal named export needed and note it in your
  report.

- [ ] **Step 7: Run the full component test suite**

Run: `npx vitest run src/components/nirmana-elevation`
Expected: PASS — every existing test file plus the 2 new ones (`ProvenanceChip.test.tsx`,
`WaveProgressBar.test.tsx`) and the extended assertions in `CampaignSpine.test.tsx`,
`CampaignSnapshotStrip.test.tsx`, `LayerStage.test.tsx`.

- [ ] **Step 8: Commit**

```bash
git add src/components/nirmana-elevation
git commit -m "feat(nirmana-tracker): render the v2 programme spine (PHASE A / O-WAVE / layers / PHASE Z)"
```

---

### Task 5: Real-time wiring — SSE subscription and evidence-write publish

**Files:**
- Create: `platform/src/lib/nirmana-elevation/cockpit-events.ts`
- Create: `platform/src/lib/nirmana-elevation/__tests__/cockpit-events.test.ts`
- Modify: `platform/src/lib/nirmana-elevation/evidence-command.ts`
- Modify: `platform/src/components/nirmana-elevation/NirmanaElevationTracker.tsx`
- Modify: `platform/src/components/nirmana-elevation/NirmanaElevationTracker.test.tsx`

**Interfaces:**
- Produces: `async function publishCockpitEvent(event: { chart_id: string; type: string; [key:
  string]: unknown }): Promise<void>` — no-ops silently (catches and logs, never throws) when
  `PUBSUB_DISABLED` is set or `GOOGLE_CLOUD_PROJECT` is unset, exactly mirroring
  `watchdog/route.ts`'s `publishEvent` (per Ruling R4 — duplicated, not imported, since
  `watchdog/route.ts` is outside the write-set).

- [ ] **Step 1: Write `cockpit-events.ts`**

```typescript
import 'server-only'

const CANONICAL_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

export async function publishCockpitEvent(event: { type: string; [key: string]: unknown }): Promise<void> {
  if (process.env.PUBSUB_DISABLED || !process.env.GOOGLE_CLOUD_PROJECT) return
  try {
    const { PubSub } = await import('@google-cloud/pubsub')
    const client = new PubSub({ projectId: process.env.GOOGLE_CLOUD_PROJECT })
    const topic = client.topic(process.env.PUBSUB_TOPIC ?? 'cockpit-events')
    const payload = { chart_id: CANONICAL_CHART_ID, ...event }
    await topic.publishMessage({
      data: Buffer.from(JSON.stringify(payload)),
      attributes: { chart_id: CANONICAL_CHART_ID, type: String(event.type) },
    })
  } catch (err) {
    console.error('[nirmana-elevation/cockpit-events] publish failed:', (err as Error).message)
  }
}
```

- [ ] **Step 2: Write the test** (mock `@google-cloud/pubsub`, matching the pattern used to test
  `watchdog/route.ts`'s publish call — grep for how that route's own test mocks the module and
  copy the mocking style, not the assertions):

```typescript
import { afterEach, describe, expect, it, vi } from 'vitest'

const publishMessage = vi.fn().mockResolvedValue(undefined)
const topic = vi.fn(() => ({ publishMessage }))
vi.mock('@google-cloud/pubsub', () => ({ PubSub: vi.fn(() => ({ topic })) }))

describe('publishCockpitEvent', () => {
  afterEach(() => {
    vi.unstubAllEnvs()
    publishMessage.mockClear()
  })

  it('no-ops when GOOGLE_CLOUD_PROJECT is unset', async () => {
    vi.stubEnv('GOOGLE_CLOUD_PROJECT', '')
    const { publishCockpitEvent } = await import('../cockpit-events')
    await publishCockpitEvent({ type: 'nirmana.capsule_accepted' })
    expect(publishMessage).not.toHaveBeenCalled()
  })

  it('no-ops when PUBSUB_DISABLED is set', async () => {
    vi.stubEnv('GOOGLE_CLOUD_PROJECT', 'test-project')
    vi.stubEnv('PUBSUB_DISABLED', '1')
    const { publishCockpitEvent } = await import('../cockpit-events')
    await publishCockpitEvent({ type: 'nirmana.capsule_accepted' })
    expect(publishMessage).not.toHaveBeenCalled()
  })

  it('publishes with the canonical chart_id attribute when configured', async () => {
    vi.stubEnv('GOOGLE_CLOUD_PROJECT', 'test-project')
    vi.stubEnv('PUBSUB_DISABLED', '')
    const { publishCockpitEvent } = await import('../cockpit-events')
    await publishCockpitEvent({ type: 'nirmana.capsule_accepted', asset_id: 'bg_vedha_malefic_scale' })
    expect(publishMessage).toHaveBeenCalledWith(expect.objectContaining({
      attributes: { chart_id: '482012f1-710e-4a25-994a-93821f5871aa', type: 'nirmana.capsule_accepted' },
    }))
  })

  it('never throws when publishMessage rejects', async () => {
    vi.stubEnv('GOOGLE_CLOUD_PROJECT', 'test-project')
    publishMessage.mockRejectedValueOnce(new Error('boom'))
    const { publishCockpitEvent } = await import('../cockpit-events')
    await expect(publishCockpitEvent({ type: 'x' })).resolves.toBeUndefined()
  })
})
```

If the module-mock pattern above needs adjusting to match how this repo's Vitest config handles
dynamic `import()` inside a mocked module (some setups need `vi.doMock` + fresh `import()` per
test instead of top-level `vi.mock`), adapt it to whatever pattern `watchdog`'s own tests (or any
other existing test mocking `@google-cloud/pubsub` in this repo) already use — grep for
`@google-cloud/pubsub` under `__tests__` first.

- [ ] **Step 3: Run the test, verify it passes**

Run: `npx vitest run src/lib/nirmana-elevation/__tests__/cockpit-events.test.ts`
Expected: PASS, 4/4.

- [ ] **Step 4: Call `publishCockpitEvent` from `evidence-command.ts` on capsule/supersession acceptance**

In `handleNirmanaEvidenceCommand` (around line 320, the `supersede_definition` branch), after the
existing `writeAuditLog` call and only when `outcome === 'superseded'`, add:

```typescript
if (outcome === 'superseded') {
  await publishCockpitEvent({ type: 'nirmana.definition_superseded', definition_revision: parsedData.new_definition_revision })
}
```

And in the generic evidence-record branch (around line 381, after `recordNirmanaElevationEvidence`),
after its `writeAuditLog` call, only when `outcome === 'created' && parsedData.event_type ===
'asset_frozen'`, add:

```typescript
if (outcome === 'created' && parsedData.event_type === 'asset_frozen') {
  await publishCockpitEvent({ type: 'nirmana.asset_frozen', asset_id: parsedData.entity_id })
}
```

Add the import: `import { publishCockpitEvent } from '@/lib/nirmana-elevation/cockpit-events'` at
the top of `evidence-command.ts`. Both calls are best-effort (the function never throws) — do not
wrap them in their own try/catch, and do not let a publish failure change the HTTP response
already being returned.

Find (or create, if none exists) a test file exercising `handleNirmanaEvidenceCommand`'s
`asset_frozen` and `supersede_definition` paths (check `__tests__/evidence-ingress.test.ts` first
— it may already cover this function under a different describe) and add assertions, with
`@google-cloud/pubsub` mocked the same way as Step 2, that `publishCockpitEvent`'s underlying
`publishMessage` is called once for a successful `asset_frozen` record and once for a successful
`supersede_definition`, and NOT called for other event types or for a duplicate/idempotent replay
(`outcome !== 'created'`/`'superseded'`).

- [ ] **Step 5: Run the tests, verify they pass**

Run: `npx vitest run src/lib/nirmana-elevation`
Expected: PASS — all prior tests plus the new evidence-command publish assertions.

- [ ] **Step 6: Add the SSE subscription effect to `NirmanaElevationTracker.tsx`**

Read the current file in full (272 lines) first. Add a new `useEffect`, alongside the existing two
(`visibilitychange`/`focus`/`online` effect and the polling-interval effect), that:

```typescript
const CANONICAL_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const SSE_REFETCH_DEBOUNCE_MS = 2_000
const RELEVANT_SSE_EVENT_TYPES = ['run.state_change', 'asset.progress', 'asset.state_change', 'nirmana.asset_frozen', 'nirmana.definition_superseded']

// inside the component, alongside the existing effects:
useEffect(() => {
  let debounceTimer: ReturnType<typeof setTimeout> | null = null
  const scheduleRefetch = () => {
    if (debounceTimer) clearTimeout(debounceTimer)
    debounceTimer = setTimeout(() => { refresh() }, SSE_REFETCH_DEBOUNCE_MS)
  }

  const source = new EventSource(`/api/cockpit/sse?chart_id=${CANONICAL_CHART_ID}`)
  for (const type of RELEVANT_SSE_EVENT_TYPES) {
    source.addEventListener(type, scheduleRefetch)
  }
  source.onerror = () => {
    // EventSource retries on its own; no action needed beyond letting the
    // existing poll (Effect 2, unchanged) remain the freshness fallback.
  }

  return () => {
    if (debounceTimer) clearTimeout(debounceTimer)
    source.close()
  }
}, [refresh])
```

Place this so it does not replace or disable the existing polling effect — the poll stays as the
baseline/fallback exactly as spec §5.1/§5.4 require ("keep polling as the base... existing
stale/unavailable semantics... must survive unchanged"). Confirm `refresh` is a stable
`useCallback` already (it is referenced by the existing effects) so this new effect's dependency
array is correct — read how the existing effects declare their own dependency on `refresh` and
match that pattern exactly.

- [ ] **Step 7: Test the SSE-triggered refetch**

Add to `NirmanaElevationTracker.test.tsx` (check how the file already mocks `fetch`/`EventSource`
if at all; if no `EventSource` mock exists yet, add a minimal one):

```typescript
class MockEventSource {
  static instances: MockEventSource[] = []
  listeners: Record<string, ((event: MessageEvent) => void)[]> = {}
  onerror: (() => void) | null = null
  constructor(public url: string) { MockEventSource.instances.push(this) }
  addEventListener(type: string, listener: (event: MessageEvent) => void) {
    this.listeners[type] = [...(this.listeners[type] ?? []), listener]
  }
  close() {}
  emit(type: string) { this.listeners[type]?.forEach((listener) => listener(new MessageEvent(type))) }
}
vi.stubGlobal('EventSource', MockEventSource)
```

Add a test asserting: after the component mounts, an `EventSource` was constructed with a URL
containing `chart_id=482012f1-710e-4a25-994a-93821f5871aa`; emitting a `run.state_change` event on
the mock instance, then advancing fake timers past `SSE_REFETCH_DEBOUNCE_MS`, triggers exactly one
additional `fetch` call to the snapshot URL beyond the initial mount fetch; emitting the same event
twice within the debounce window (before advancing timers) still triggers only one additional
fetch (debounce coalesces bursts). Use `vi.useFakeTimers()` for the timer assertions, matching
whatever fake-timer setup (if any) the existing polling-interval tests in this file already use —
read them first rather than introducing a second, inconsistent timer-mocking style.

- [ ] **Step 8: Run the tests, verify they pass and existing freshness/degraded tests are unaffected**

Run: `npx vitest run src/components/nirmana-elevation/NirmanaElevationTracker.test.tsx src/components/nirmana-elevation/NirmanaElevationTracker.a11y.test.tsx`
Expected: PASS — all prior assertions (stale banner, backoff, visibility handling) plus the new
SSE ones.

- [ ] **Step 9: Run the entire nirmana-elevation slice one final time**

Run: `npx vitest run src/lib/nirmana-elevation src/components/nirmana-elevation src/app/api/admin/nirmana-elevation src/app/api/admin/internal/nirmana-elevation-executor src/app/api/admin/internal/nirmana-elevation-monitor`
Expected: PASS, full slice, zero failures.

- [ ] **Step 10: Commit**

```bash
git add src/lib/nirmana-elevation/cockpit-events.ts src/lib/nirmana-elevation/__tests__/cockpit-events.test.ts src/lib/nirmana-elevation/evidence-command.ts src/components/nirmana-elevation/NirmanaElevationTracker.tsx src/components/nirmana-elevation/NirmanaElevationTracker.test.tsx
git add -u src/lib/nirmana-elevation
git commit -m "feat(nirmana-tracker): SSE-triggered refetch + evidence-write Pub/Sub freshness signal"
```

---

## After all tasks — Finish (controller, not a dispatched task)

Not part of the SDD task loop — done directly by the controlling session per
`superpowers:finishing-a-development-branch`, because it needs live judgment (PR review, CI
triage, merge-queue babysitting, production verification) rather than a fresh subagent's isolated
context:

1. Run the full platform test/lint/typecheck gate (equivalent of `/run-checks`) on the final
   branch state.
2. Open ONE PR (spec §6 scope cap: 1-2 PRs, tripwire 3 — this plan's 5 tasks are cohesive and
   interdependent enough to ship as a single PR) titled around "Nirmāṇa tracker: v2 programme
   spine + real-time wiring", body citing this plan file, the alignment prompt, and Rulings
   R1-R5.
3. Merge via the queue (5 required checks, per spec §6).
4. Verify live in production per spec §7:
   - `/admin/nirmana-elevation` shows PHASE A completed (evidence-cited), O-WAVE current with WP
     chips, L0..L5 with W1-W6 bars whose numbers match a hand-run SQL aggregation of milestone
     events for the frozen definition's assets, PHASE Z locked.
   - Observe a real campaign event (next capsule or supersession) appear within ≤10s without a
     manual reload.
   - Old stage history visible in the PHASE A drawer.
   - Freshness/degraded semantics unchanged (re-run the relevant tests against the deployed
     build if practical, or re-confirm via the existing test suite's continued pass).
5. Update `00_ARCHITECTURE/briefs/nirmana/CAMPAIGN_STATE.md` recording the tracker-v2 alignment,
   the PR number(s), and the live verification evidence gathered in step 4 — following the
   file's existing table/section conventions (read its current content before editing, do not
   restructure it).

## Self-Review Notes (from plan authoring)

- **Spec coverage**: §3 item 1 (programme spine: Task 4) · §3 item 2 (vocab compatibility: Ruling
  R1, no vocab change needed) · §3 item 3 (position chip: Task 2 + Task 4 Step 5) · §4 (manifest:
  Task 1) · §5.1-§5.2 (poll base + SSE subscribe: Task 5 Step 6) · §5.3 (evidence-write freshness:
  Task 5 Steps 1-5, Ruling R4) · §5.4 (freshness semantics unchanged: enforced by "keep existing
  effects" instruction + full-suite reruns after every task) · §6 (write-set: Global Constraints;
  scope cap: Finish step 2) · §7 acceptance criteria 1-5: Finish steps 4-5.
- **Placeholder scan**: no TBD/TODO; every step has concrete code or an exact grep/read
  instruction with a stated fallback rule (Task 1 Step 1, Task 5 Step 2's mock-pattern note).
- **Type consistency**: `WaveProgressCount` (Task 2) flows unchanged into `types.ts`'s
  `WaveProgressSchema` (Task 3) and `WaveProgressBar`'s props (Task 4); `ProgrammePosition.label`
  (Task 2) flows unchanged into `snapshot.programme.position_label` (Task 3) into
  `CampaignSnapshotStrip` (Task 4 Step 5); `publishCockpitEvent`'s signature (Task 5 Step 1) is
  used identically in both `evidence-command.ts` call sites (Task 5 Step 4).
