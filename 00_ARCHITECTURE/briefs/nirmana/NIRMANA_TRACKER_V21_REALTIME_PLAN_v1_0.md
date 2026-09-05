---
artifact: NIRMANA_TRACKER_V21_REALTIME_PLAN_v1_0.md
canonical_id: NIRMANA_TRACKER_V21_REALTIME_PLAN
version: "1.0"
status: DRAFT — awaiting native approval, then execute via subagent-driven-development
produced_on: 2026-09-05
supersedes_presentation_of: NIRMANA_TRACKER_V2_ALIGNMENT_PLAN_v1_0.md (the v2.0-sequential spine
  rendering only; everything that plan built — wave bars, provenance chips, SSE wiring, the
  fabrication fix — is retained and built upon)
---

# Nirmāṇa Tracker — v2.1 Real-Time Progress Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `/admin/nirmana-elevation` show the TRUE, real-time progress of the v2.1
asset-frontier campaign: one overall progress bar + percentage for the entire 128-asset arc, a
cumulative completion percentage per layer, six concurrently-active layer cards instead of a
sequential locked chain, and sub-2-second refresh on every evidence write.

**Architecture:** Additive re-aggregation, same discipline as the previous plan. The per-asset
6-milestone projection (the one evidence stream that is actually populated — verified 2026-09-05:
zero `stage_transition_accepted` and zero `foundation_lane_accepted` events exist) becomes the
sole source of completion arithmetic. The 13-stage machine, its validator, and its schema fields
are left untouched (history + future W6 ceremonies) but the programme view stops deriving layer
state from them. Provenance discipline unchanged: every number is evidence-derived or wears a
`repo-declared` chip.

**Tech Stack:** unchanged (Next.js/TS/Zod/Vitest; existing SSE + Pub/Sub wiring from PR #1701).

**Spec:** The native's direct request (2026-09-05): (1) real-time view of execution progress, not
stale; (2) overall completion of the entire arc — progress bar + percentage, covering all layers;
(3) per-layer cumulative current completion percentage; (4) wired to the execution programme that
is actually running — v2.1 Asset-Frontier Pipelining per `sessions/SESSION_CHARTER_V21.md`
(native-ratified 2026-09-05) and `NIRMANA_UNIFIED_ELEVATION_PLAN_v2_0.md §1.1`.

## Ground truth this plan is built on (verified by SQL/gh, 2026-09-05)

- Campaign runs as **7 concurrent sessions** (CONDUCTOR + L0–L5); gating is per-ASSET (E-gate,
  charter C2/C10), not per-layer. Only W6 freeze *ceremonies* stay ordered L0→L5.
- Evidence ledger (definition `t0-2026-09-01-0e5b06fb`, 128 assets): L0 29/40 frozen, 40/40
  analysed+decided; L1 11 analysed; L2 0; L3 1; L5 3 — with lanes' own state files reporting
  W1/W2 complete for ALL layers and acceptance receipts actively backfilling since PR #1736
  merged (10+ events/hour observed).
- **Zero stage-spine events have ever been written** → the current spine renders "unknown"
  everywhere; `current_stage` is null; the position chip says "O-WAVE · WP-3".
- O-wave is FINISHED: WP-1 #1697 merged 2026-09-03T23:18Z, WP-3 #1698 merged 2026-09-03T23:55Z,
  WP-2 #1699 merged 2026-09-04T00:21Z. A post-wave WP-6 "blast radius" guard (#1781, charter
  C13/D-NATIVE-05) merged 2026-09-05. `programme.ts` still declares WP-2 `not_started` /
  WP-3 `in_progress` — stale.
- Monitor banner is `evidence_refresh_required`, 66–67 assets — registry-contract drift caused by
  the campaign's own W3 Conform migrations (L3 22/23, L5 15/15, L4 9/9 drifted). Structural: it
  will grow all campaign and never self-clear.
- Since PR #1701, only `definitions.ts` changed under `lib/nirmana-elevation` (3 commits, all
  evidence-acceptance logic). `projection.ts`, `snapshot.ts`, `types.ts`, `programme.ts`, and all
  components are byte-identical to what PR #1701 shipped — but re-verify with git log at task
  time; ~20 campaign PRs are open at any moment.

## Global Constraints

- **Write-set:** ONLY `platform/src/{components,lib}/nirmana-elevation/**`, the snapshot/evidence
  route files, the admin page, and tests. Do NOT touch: `monitor.ts`'s
  `classifyNirmanaDivergence` status semantics (supersession machinery keys on it — presentation
  changes happen in `snapshot.ts`/components); the stage-transition validator in `definitions.ts`;
  `NIRMANA_STAGE_IDS`; any O-wave/orchestrator file; `NirmanaElevationTrackerV1.tsx` (schema-1.0
  fallback). No DB migrations.
- **Truth model unchanged:** every displayed number is evidence-derived, or carries the
  `repo-declared` ProvenanceChip. No invented weights, no parsed markdown, honest nulls (`—`)
  over fabricated zeros/percentages (§N.8, §N.7 item 6).
- **Coordination:** under charter C5 the tracker is CONDUCTOR-owned; this work is done under the
  native's direct authority (which the charter delegates from), but the Finish section posts a
  heads-up on coordination issue #1713 before merging, to avoid colliding with Conductor work.
- Existing suites stay green throughout. Full slice after every task:
  `npx vitest run src/lib/nirmana-elevation src/components/nirmana-elevation src/app/api/admin/nirmana-elevation src/app/api/admin/internal/nirmana-elevation-executor src/app/api/admin/internal/nirmana-elevation-monitor`
- Percentages: integer, **floor** not round (never show 100% until literally 100%); `required = 0`
  → percent is `null`, rendered "—".
- Scope cap: **1 PR** (tripwire 2). Merge via queue; deploy verified live.

## Rulings (pre-flight — read before dispatching Task 1)

**R1 — Overall % is the asset-milestone aggregate, nothing else.** Overall completion =
Σ`milestones_earned` / Σ`milestones_required` across all manifest assets with non-null
`milestones_required` (the existing fabrication-fix filter). PHASE A, O-WAVE, and PHASE Z are
shown as arc-strip STATES (✓/✓/pending), never folded into the percentage — folding them in
would require inventing weights for phases that have no milestone denominators. The bar is
labeled "asset elevation" so 100% ≠ "campaign closed" (Phase Z close-out follows).

**R2 — Layer states under v2.1 are `completed | active | pending`; "locked" is retired from the
programme view.** Nothing is layer-locked anymore (charter C2: "W1/W2 are NEVER gated"). Derivation,
purely from ledger evidence per layer: `completed` = frozen == assets_total; `active` = any
milestone earned; `pending` = zero milestones earned. The old `stages` array, its schema, and
`projectCampaignStages` remain untouched for history/drawer/W6-ceremony use — the programme view
just stops consuming them for layer state.

**R3 — The O-wave manifest is updated as stable history, not made dynamic.** The staleness
happened because the manifest declared an in-flight race. The race is over: all three WPs merged
(verified via `gh pr view` by exact PR number — not search, which burned us last time). Completed
history doesn't go stale. WP-6 (#1781) is listed as a labeled **post-wave addendum** row — the
plan's own §3.4 says WP-4/5 are out of O-wave scope and WP-6 was born later from charter C13, so
it must not be presented as O-wave scope.

**R4 — The drift banner gets a detector-backed presentation split; the classifier is untouched.**
`evidence_refresh_required` is structurally permanent while W3 Conform work lands — a red light
that means "working as intended" is a bad instrument. Fix in presentation: split the observation's
`affected_asset_ids` into those WITH ≥1 accepted campaign receipt in the current definition cohort
("under active elevation — expected") vs WITHOUT ("unexplained — attention"). Warn-tone only when
unexplained > 0 or the status is genuinely alarming (`plan_adaptation_required`,
`source_unavailable`, `release_attention`); calm/info tone otherwise. Wording stays honest: "under
active elevation with accepted receipts", never "change verified sanctioned" — we detect receipt
existence, not that the specific contract edit was the sanctioned one.

**R5 — Lane markdown state files are NOT parsed for numbers.** They're unverified narration; the
ledger is the territory. The known W1/W2 receipt lag (L2 at 0 in the ledger vs 22/22 in its state
file) is temporary — receipts are backfilling since #1736 — and the tracker shows it honestly via
per-layer `last_evidence_at` timestamps so movement is visible. If the backfill stalls, that is a
campaign problem to raise with the Conductor, not something the tracker papers over.

**R6 — No evidence backfill writes from this task, and the W6-ceremony landmine is escalated,
not fixed here.** Finding: the stage-transition validator requires each `stage_transition_accepted`
to follow its predecessor's receipt, and NO spine receipts exist — so L0's upcoming freeze
ceremony (`→ L0`) will be REJECTED for missing BOOTSTRAP→…→F0_FOUNDATION receipts. That is the
Conductor's to resolve (backfill the historical ceremonies with real provenance, or amend the
validator). The Finish section files it as a `nirmana-adjudication` issue with evidence; the
tracker plan does not depend on those events existing.

**R7 — Frontier counts mirror the charter's C10 SQL exactly** (transitive `depends_on` closure,
ancestors satisfied by `asset_frozen` only), with the known limitation named in the UI title
attribute: C12's service-probe satisfaction is NOT modeled, so frontier counts may under-report
eligibility for assets with service-kind ancestors. Honest and cheap beats complete and fragile.

## File Structure

```
platform/src/lib/nirmana-elevation/
  programme.ts                  MODIFY — WP statuses → merged (history), WP-6 addendum, arc-phase
                                          declarations (PHASE_A/O_WAVE completed, repo-declared)
  __tests__/programme.test.ts   MODIFY
  projection.ts                 MODIFY — + projectCompletion, projectAssetFrontier,
                                          deriveLayerActivityState, v2.1 position label
  __tests__/projection.test.ts  MODIFY
  types.ts                      MODIFY — programme.overall / programme.arc / conform_drift;
                                          per-layer completion / frontier_ready / last_evidence_at
  snapshot.ts                   MODIFY — wire the above from data already loaded
  __tests__/snapshot.test.ts    MODIFY
  evidence-command.ts           MODIFY — unified publish on every created evidence write
  __tests__/evidence-command.test.ts MODIFY

platform/src/components/nirmana-elevation/
  ProgrammeOverview.tsx         NEW — overall bar + % + arc strip (Phase A ✓ · O-wave ✓ ·
                                       Phase Z pending), replaces the spine header block
  ProgrammeOverview.test.tsx    NEW
  LayerCard.tsx                 NEW — one concurrently-active layer: cumulative % bar, existing
                                       WaveProgressBar, frozen/total, frontier count,
                                       last-activity; expands to existing LayerStage internals
  LayerCard.test.tsx            NEW
  CampaignSpine.tsx             MODIFY — becomes: ProgrammeOverview + 6-card grid + collapsed
                                          history drawer (old stage rows preserved inside)
  CampaignSpine.test.tsx        MODIFY
  CampaignSnapshotStrip.tsx     MODIFY — position label + banner tone/split rendering
  CampaignSnapshotStrip.test.tsx MODIFY
  NirmanaElevationTracker.tsx   MODIFY — add 'nirmana.evidence_accepted' to SSE event list
  NirmanaElevationTracker.test.tsx MODIFY
```

---

### Task 1: Programme manifest — v2.1 history refresh

**Files:** Modify `programme.ts` + its test.

**Interfaces produced:** existing exports keep names/shapes; `PROGRAMME_O_WAVE_WPS` values change
to all `'merged'` with a new optional `merged_pr` field `{ number: number; merged_at: string }`;
new export `PROGRAMME_POST_WAVE_ADDENDA: readonly ProgrammeOWaveWpDeclaration[]` (WP-6); new
export `PROGRAMME_ARC_PHASES: readonly { phase_id: 'PHASE_A'|'O_WAVE'|'LAYERS'|'PHASE_Z';
label: string; declared_state: 'completed'|'in_progress'|'pending'|null; provenance:
'repo_declared'|'evidence_derived'; note: string }[]` — `LAYERS` and `PHASE_Z` carry
`declared_state: null` (their state is evidence-derived downstream; the manifest never declares it).

- [ ] Step 1: Verify WP merge facts by exact PR number (never search): `gh pr view 1697/1698/1699
  --json number,state,mergedAt` and `gh pr view 1781` for WP-6. Record outputs in the task report.
- [ ] Step 2: Update `PROGRAMME_O_WAVE_WPS`: all three `status: 'merged'`, add `merged_pr` with
  the verified numbers/dates. Note fields keep the repo-declared framing but now say "verified via
  gh pr view <n>, <date> — stable history".
- [ ] Step 3: Add `PROGRAMME_POST_WAVE_ADDENDA` = [{ wp_id: 'WP-6', name: 'Blast radius — dispatch
  refuses unacknowledged downstream destruction (charter C13 / D-NATIVE-05)', status: 'merged',
  merged_pr: { number: 1781, ... }, note: 'post-O-wave addendum — NOT O-wave scope per plan §3.4' }].
  Widen `ProgrammeWpId` to include `'WP-6'`.
- [ ] Step 4: Add `PROGRAMME_ARC_PHASES` per the interface above. PHASE_A note cites the plan's
  "PHASE A (COMPLETE)" line; O_WAVE note cites the three merged WPs.
- [ ] Step 5: Update tests — WPs all merged; addenda separate from `PROGRAMME_O_WAVE_WPS` (length
  still 3); arc phases: exactly 4, LAYERS/PHASE_Z have `declared_state: null` (test asserts the
  manifest CANNOT declare evidence-derived states — this is the §N.8 guard).
- [ ] Step 6: Run focused test + commit.

### Task 2: Projection — completion, frontier, v2.1 layer state

**Files:** Modify `projection.ts` + `__tests__/projection.test.ts`. Read the real file first —
confirm the current shapes of `WaveProgressCount`, the milestone-bearing asset structural type
used by `projectLayerWaveProgress`, and `NirmanaLayerId`.

**Interfaces produced (Task 3 depends on these verbatim):**

```typescript
export interface CompletionCount { earned: number; required: number; percent: number | null }
// percent = required === 0 ? null : Math.floor((earned / required) * 100)

export function projectCompletion(
  assets: { milestones_earned: number | null; milestones_required: number | null }[],
): CompletionCount
// Sums ONLY assets with non-null milestones_required (the fabrication-fix filter, reused).

export function projectAssetFrontier(args: {
  manifestAssets: { asset_id: string; layer: NirmanaLayerId; depends_on?: string[] }[]
  frozenAssetIds: ReadonlySet<string>
  decidedAssetIds: ReadonlySet<string>
}): Partial<Record<NirmanaLayerId, string[]>>
// Per layer: asset_ids where NOT frozen AND decided AND every TRANSITIVE depends_on ancestor
// (memoized DFS over the manifest; mirror charter C10: ancestor satisfied by frozen ONLY)
// is in frozenAssetIds. Deterministic (sorted) output.

export function deriveLayerActivityState(args: {
  assetsTotal: number | null
  frozen: number
  milestonesEarned: number
}): 'completed' | 'active' | 'pending' | 'unknown'
// null/unknown total → 'unknown'; frozen===total→'completed'; earned>0→'active'; else 'pending'.

export function projectProgrammePositionV21(args: {
  overall: CompletionCount
  frozenTotal: number
  assetsTotal: number | null
}): string
// "34% · 29/128 frozen" — or "Execution not yet evidenced" when percent is null.
```

- [ ] Step 1 (TDD): append new describes with these cases — completion: mixed nulls excluded,
  floor semantics (199/200 → 99 not 100), required=0 → percent null; frontier: linear chain,
  diamond dependency, undecided asset excluded, frozen asset excluded, ancestor-unfrozen excluded,
  cross-layer ancestor honored (an L3 asset whose only ancestor is a frozen L0 asset IS eligible —
  this is the v2.1 semantics the old dispatcher got wrong, #1730/#1737); layer state: all four
  outcomes; position: normal + null cases. Watch them fail.
- [ ] Step 2: Implement, run to green, full-slice check, commit. Do not modify any existing
  export (the old `projectProgrammePosition` stays — Task 3 stops calling it, Task 5 of the
  previous plan's tests still cover it).

### Task 3: Schema + snapshot wiring

**Files:** `types.ts`, `snapshot.ts`, `__tests__/snapshot.test.ts` (+ any inline-fixture test that
breaks; `fixture-v2.ts` derives from the real projector, so it self-updates). Read the real
assembly points first — `buildProgrammeSnapshot` and the layer-assembly `.map()` — line numbers
have NOT moved since PR #1701 (verified) but confirm.

**Schema additions (all required, no `.optional()` escape hatches):**
- `V2LayerSchema` += `completion: CompletionSchema` (`{earned:int≥0, required:int≥0,
  percent:int 0..100 nullable}` with superRefine earned≤required), `frontier_ready:
  z.array(z.string())`, `last_evidence_at: nullableIso`.
- `ProgrammeSnapshotSchema` += `overall: CompletionSchema`,
  `arc: z.array(ArcPhaseSchema).length(4)` (phase_id enum, state enum
  `completed|in_progress|active|pending|unknown`, provenance enum, note string),
  `conform_drift: z.object({ status_echo: z.string(), affected: int≥0,
  with_accepted_receipts: int≥0, without_accepted_receipts: int≥0 }).nullable()`.
- `o_wave` block += `addenda` array (same WP shape), `wps[].merged_pr` optional object.

**Snapshot wiring (all from data already loaded — no new queries):**
- Per-layer: `completion = projectCompletion(layer's wavable assets)`; `frontier_ready` from
  `projectAssetFrontier` (frozen/decided sets built from the events already in memory);
  `last_evidence_at` = max accepted_at over the layer's asset events; layer card state via
  `deriveLayerActivityState`.
- `programme.overall = projectCompletion(all wavable assets)`; `programme.arc` from
  `PROGRAMME_ARC_PHASES` — PHASE_A/O_WAVE pass the declared state through (provenance
  repo_declared); LAYERS state = 'completed' if all six layers completed else 'active' if any
  active else 'pending'; PHASE_Z = 'pending' until L5 completed, then 'unknown'→no — 'pending'
  until L5 frozen==total, then 'active' is wrong too (Phase Z is Conductor work) → use 'pending' /
  'active' only when a real signal exists; default 'pending'. Keep it simple and honest.
- `position_label` → `projectProgrammePositionV21`.
- `conform_drift`: null when no monitor observation; else affected = observation's
  affected_asset_ids; with/without = partition by "asset has ≥1 accepted event in the current
  definition cohort" (any of the acceptance event types already enumerated in the snapshot's
  event handling).
- [ ] TDD: extend snapshot tests — overall equals hand-computed sum from the fixture; a layer with
  zero events reads `pending` + percent null-or-real per fixture; frontier respects cross-layer
  frozen ancestor; conform_drift partition correct (fixture: 2 affected, 1 with receipts);
  `arc.length === 4`. Run full slice; fix any inline-fixture breakage by fixing fixtures, never by
  weakening schema. Commit.

### Task 4: UI — overall bar, arc strip, six concurrent layer cards

**Files:** new `ProgrammeOverview.tsx` + `LayerCard.tsx` (+tests); modify `CampaignSpine.tsx`,
`CampaignSnapshotStrip.tsx` (+tests). Read every file you modify in full first; preserve every
aria attribute and keyboard pattern (the previous plan's review verified these byte-for-byte —
keep that bar).

- [ ] `ProgrammeOverview`: `role="progressbar"` with aria-valuenow = overall percent (omit
  aria-valuenow when percent null; render "—"), text "N% · F/128 frozen", and the arc strip:
  4 chips (PHASE A ✓, O-WAVE ✓ with popover/details listing WPs + addendum, LAYERS live, PHASE Z
  pending) each with its ProvenanceChip. Tests: percent renders, floor case, null case, arc chips
  + provenance labels present.
- [ ] `LayerCard`: header `L<N> · <name>` + state badge (completed/active/pending — no "locked"
  anywhere), cumulative % mini-bar (same progressbar pattern as MilestoneBar), `WaveProgressBar`
  (existing, unchanged), `frozen/total`, `frontier: N ready` (title attr carries the R7
  limitation sentence), `last activity <relative time>`, expandable body reusing the existing
  LayerStage content (eligible-next preview, wave lanes, AssetCards) unchanged. Tests: all four
  states render correctly; frontier count renders; expansion shows existing internals.
- [ ] `CampaignSpine`: render `ProgrammeOverview` then a responsive grid of six `LayerCard`s
  (all visible simultaneously — the UI must communicate concurrency, not sequence), then ONE
  collapsed `<details>` "Stage-machine history (13-stage record + Phase A drawer)" containing the
  previous implementation's stage-row rendering unchanged (the old per-stage `<article>` markup,
  FoundationStage dispatch, PHASE A group — all preserved inside the drawer). Update tests:
  concurrency assertions (six cards all present regardless of state), history drawer opens to old
  rows, O-wave chips show all-merged.
- [ ] `CampaignSnapshotStrip`: position label passthrough unchanged (new value arrives via
  snapshot); banner: render `conform_drift` split when present — calm/info tone when
  `without_accepted_receipts === 0` and status is a refresh-type; warn tone otherwise
  (`plan_adaptation_required`, `source_unavailable`, `release_attention`, or unexplained > 0).
  Copy: "N registry contracts differ from the T0 baseline — M under active elevation with
  accepted receipts, K unexplained." Tests: both tones, exact copy, unexplained>0 forces warn.
- [ ] Full component suite green; commit.

### Task 5: Real-time — publish every accepted evidence write

**Files:** `evidence-command.ts`, `__tests__/evidence-command.test.ts`,
`NirmanaElevationTracker.tsx` + test.

- [ ] In the generic record path: replace the `asset_frozen`-only publish with a publish on EVERY
  `outcome === 'created'`: `publishCockpitEvent({ type: 'nirmana.evidence_accepted', event_type:
  parsedData.event_type, asset_id: parsedData.entity_id, layer: parsedData.layer })`. Keep the
  supersession publish unchanged. Update the existing tests that pinned the old
  `nirmana.asset_frozen` type (they assert gating on created-only and no-publish-on-replay —
  those invariants stay, only the type/payload changes) and add: analysis-accepted publishes,
  idempotent replay still does not.
- [ ] Client: add `'nirmana.evidence_accepted'` to `RELEVANT_SSE_EVENT_TYPES` (keep the old
  entries — historical publishes and cockpit build events still matter). Extend the existing
  debounce test with the new type.
- [ ] Full slice + tsc + eslint; commit.

---

## After all tasks — Finish (controller, not dispatched)

1. Full gate (`npx vitest run`, tsc, eslint) on the final branch.
2. **Post a heads-up comment on coordination issue #1713** (Conductor owns the tracker under C5):
   one paragraph — native-directed tracker rework landing, files touched, no orchestrator/
   dispatcher/monitor-classifier changes, PR link.
3. **File a `nirmana-adjudication` issue** for the R6 landmine: zero stage-spine receipts exist +
   validator enforces predecessor chain ⇒ L0's W6 `stage_transition_accepted` will be rejected;
   evidence (SQL counts, validator lines); options (backfill historical ceremonies with real
   provenance / amend validator); recommendation: backfill, since the ceremonies genuinely
   happened with PR evidence. The Conductor rules; the tracker does not wait on it.
4. ONE PR → merge queue → deploy; verify Cloud Run revision commit-sha matches.
5. Live verification WITH the native (they hold the authed browser session): overall bar shows
   the SQL-cross-checked percent; six cards all visible with L0 active 29/40 (or current), L1–L5
   states matching a fresh per-layer ledger query run in the session; trigger observed — next
   evidence write (they're landing hourly) appears within ≤10s without reload.
6. Update `CAMPAIGN_STATE.md` (append-only section, per its conventions) + mark this plan COMPLETE.

## Self-review notes (plan authoring)

- Requirement (2) overall bar+% → Tasks 2/3/4 (`projectCompletion` → `programme.overall` →
  `ProgrammeOverview`); requirement (3) per-layer cumulative % → same chain into `LayerCard`;
  requirement (1)+(4) real-time & current-model → R2 states, frontier per C10, Task 5 SSE, R4
  banner. Placeholder scan: every step has concrete shape or an explicit read-first instruction.
  Type chain: `CompletionCount` (T2) → `CompletionSchema` (T3) → `ProgrammeOverview`/`LayerCard`
  props (T4) — names locked in T2's Produces block.
- Deliberately OUT of scope: parsing lane state files (R5), evidence backfill (R6), monitor
  classifier changes (R4), per-asset duration/cost views (that is Phase Z WP-5 polish).
