---
artifact: GOCHARA_V2_PARITY_CAMPAIGN_PLAN
version: 1.0
status: SUPERSEDED (2026-08-10, native redirect) — superseded by
  ../gochara_elevation/GOCHARA_UTKARSHA_CAMPAIGN_PLAN_v1_0.md, which absorbs this
  plan's Phase-0 governance/safety tasks as its Wave 0 and demotes parity from goal
  to safety-net (Wave-6 gate leg (a)). Retained in place per hygiene §A.
date: 2026-08-10
author: Claude (Fable 5), native-directed session
parent_design: GOCHARA_SWEEP_2_0_DESIGN_v1_0.md (RATIFICATION-READY DRAFT, 2026-07-21)
campaign_lineage: Doctrine-Waves candidate D-6 → ṢAḌ-DARŚANA item 19 (W2G) → this campaign
native_decision_basis: >
  Native ratified (2026-08-10 session) the three-part verdict: (1) v2 can reach parity
  with ka_gochara_sweep; (2) v2 can exceed it (precision, stations, Moon completeness,
  onboarding speed); (3) consumers switch via the pre-installed kala_gochara_authority
  generation seam, per-chart, reversibly. "Let's get V2 plan in place."
changelog:
  - v1.0 (2026-08-10): First draft. Five phases, governance gates isolated in Phase 0,
    protected-two-chart discipline stated as invariants I1–I5. Same-session
    independent plan review found 10 issues, all fixed in place before first
    presentation: natural-key index replacement + v1-writer arbiter sequencing moved
    into Task 0.2 with collision test; post-cutover live write path specified (4.2);
    era-slice boundary semantics defined to protect the no-continuity claim (3.1/2.1);
    §3.5 post-cutover battery restored as Task 4.5; station source added as Task 1.5
    with named §2.2 non-coverage note; Tier-B gating spelled per ADJUDICATION-14
    (2.3); GUC fallback struck from backfill; drishti directionality specified (1.3);
    protection-trigger tests routed to the existing TS DB-integration harness (0.2);
    seed-drift citation corrected (0.3). Second review round (same session) found 4
    secondary tensions introduced by the fixes; all resolved: `station` added to the
    closed mechanism vocabulary; `era_slice_key` provenance column specified
    (Architecture note (c), Task 0.2 migration, two-level idempotency scope in
    3.1/4.2); cockpit `count_sql`/`target_table` repoint added to 4.2 (§N.4);
    Task 0.2 arbiter sequencing restated as an explicit two-phase deploy (writer
    to delete-then-insert first, index replacement second).
---

# Gochara 2.0 Parity → Elevation → Cutover — Campaign Plan of Record

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task.
> Steps use checkbox (`- [ ]`) syntax for tracking. Every lane's PR is subject to
> independent verification (PARĪKṢAKA pattern) before merge, per campaign precedent.

**Goal:** Bring `ka_gochara_v2_materialize` from its landed validation-only state
(±3y, point-shape, Tier-A, 0.78% raw match) to certified usability-parity with
`ka_gochara_sweep`, then beyond it, then flip serving authority per chart — without
ever endangering the two protected sweep corpora.

**Architecture:** All work happens in the writer/service layer (`services/w2g/`,
`pipeline/orchestrator/writers/`) under the FROZEN orchestrator contract — **no freeze
exception is required by any lane in this plan.** Scoring stays the frozen v1 grammar
(`compute_lambda_e` and friends, imported not reimplemented, per design §5 "changes HOW,
never WHAT"). The only schema-layer changes are: (a) a native-authorized amendment to
migration 540's protection trigger + natural-key index replacement (Phase 0, gated);
(b) the W6 cutover mechanism; (c) a nullable `era_slice_key TEXT` slice-provenance
column on `kala_gochara_windows_v2` and — via the same Task 0.2 migration — on
`kala_gochara_windows`, required by Task 3.1's ownership-scoped idempotency.

**Tech stack:** Python sidecar (writers/services, pytest), Postgres (CloudSQL),
`bg_gochara_arcs` substrate (34,553 arcs, `arcs_v01`), equivalence tooling in
`services/w2g/equivalence_report.py`, serving in `platform-mcp/src/tools/retrieval/
register_gochara_windows.ts` + `platform/src/lib/retrieval/registry/layers/reading_checklist.ts`.

---

## Invariants (binding on every lane, every phase)

- **I1 — The two protected corpora are inviolable.** `kala_gochara_windows` rows for
  charts `482012f1-…` (native) and `1c826d5a-…` (Abhinandan) are the frozen validation
  benchmark (native ruling 2026-08-06, SHAD_DARSHANA_STATE.md:2071-2100). No lane
  writes, updates, or deletes them. The v2 writer never sets
  `app.allow_protected_sweep_rewrite`. The only exception is the Phase 4 backfill
  transaction, which runs under its own native-authorized, audited, one-time ruling.
- **I2 — Frozen grammar.** No lane changes what a window *means*. All scoring goes
  through the v1 functions already imported by `services/w2g/materialize.py:58-68`.
  A lane that believes it needs a scoring change STOPS and files for native ruling.
- **I3 — Earned signals only (§N.8).** Every parity/SLO/coverage claim in this campaign
  must be produced by a detector: the equivalence report's closed classification
  vocabulary (no `unclassified_*` rows at lane close), measured wall-clock timings,
  asserted (not narrated) query-count tests.
- **I4 — Honest tiers.** Where v2 cannot yet produce something v1 produces (a shape, a
  body tier, a mechanism), it emits an explicit `skipped_reason` / build-state marker —
  never a silent gap, never a fabricated row.
- **I5 — Orchestrator contract untouched.** Writers stay `@register` WriterBase
  subclasses on `ctx.db_conn`, never committing, never writing `asset_throughput`.

---

## Phase 0 — Governance gates & hygiene (blocking; mostly native decisions)

### Task 0.1 — W6 ruling: choose the cutover mechanism

**Files:** none (ruling record → SHAD_DARSHANA_STATE.md or successor ledger)

- [ ] Draft the ruling memo presenting the two mechanisms:
  - **Option A (recommended):** v2 writes `generation='2.0'` rows INTO
    `kala_gochara_windows`; the existing per-chart
    `kala_gochara_authority.authoritative_generation` seam
    (`register_gochara_windows.ts:277-280`, `reading_checklist.ts` same COALESCE)
    becomes load-bearing exactly as designed. Requires Task 0.2.
  - **Option B:** repoint all consumers to `kala_gochara_windows_v2`. Touches every
    consumer (3 MCP tools, reading_checklist, LEL prospective ledger, db/query
    allowlist at `platform/src/app/api/mcp/db/query/route.ts:64`) and orphans the
    authority seam. Not recommended.
- [ ] Native rules; record verbatim in the campaign ledger.
- [ ] **Gate:** Phase 4 cannot start without this ruling. Phases 1–3 are unaffected.

### Task 0.2 — Migration 540 amendment: generation-aware protection (gated on 0.1=A)

**Files:**
- Create: `platform/supabase/migrations/5xx_protection_generation_aware.sql`
  (next free number at authoring time; use /create-migration conventions)
- Modify: `platform/python-sidecar/services/ka_gochara_sweep/writer.py` (ON CONFLICT
  arbiter, see below)
- Test: extend `platform/tests/integration/build_protected_assets_sweep_guard.db.test.ts`
  (the existing authoritative harness for this trigger — do NOT create a parallel
  Python harness for the same rail)

- [ ] Write the failing tests first, in the existing TS DB-integration suite: with a
  protected fixture chart (non-canonical, rolled-back transaction), (a) DELETE of
  `generation='v1'` rows RAISES `BUILD-PROTECTED`; (b) DELETE scoped
  `generation='2.0'` succeeds; (c) UPDATE of v1 rows still raises; (d) TRUNCATE still
  raises regardless of generation; (e) **collision test:** INSERT of a `generation='2.0'`
  row carrying the same `(chart_id, event_class, window_start, peak_date, milestone_id)`
  as an existing v1 row SUCCEEDS (this fails before the index replacement below).
- [ ] Amend `build_protected_assets_guard_row()` to consult `OLD.generation`:
  protection applies to `generation='v1'` rows (the frozen corpora) — and to any
  generation listed in a new `build_protected_assets.protected_generations text[]`
  column (default `{v1}`), so a certified 2.0 corpus can later be protected the same
  way. TRUNCATE guard stays generation-blind (a TRUNCATE cannot be scoped).
  Discipline note: migration 527 deliberately left `generation` unconstrained free
  text — `protected_generations` matching is exact-string; document this in the
  migration header.
- [ ] **Replace (not add) the natural-key unique index** on `kala_gochara_windows`:
  drop `uq_kala_gochara_windows_natural_key` (migration 460, generation-blind) and
  create the generation-inclusive equivalent — mirroring what migration 542 already
  did for the v2 table. Without this, a parity-grade 2.0 backfill (Phase 4) collides
  with v1 rows by construction: parity MEANS same natural keys.
- [ ] **Two-phase deploy for the v1 writer's conflict handling** (`ka_gochara_sweep/
  writer.py:691-716` infers its ON CONFLICT target from the old index expression
  list; Postgres arbiter inference requires an exact match, so no single static
  expression list can tolerate both index forms). Phase A (writer PR, merged
  first): replace the upsert with §N.3 delete-then-insert scoped to the natural
  key + `generation='v1'` — needs no arbiter inference at all, works under either
  index, and aligns the v1 writer with the layer's standard idempotency pattern.
  Phase B (this migration): drop/replace the index. Never deploy B before A.
- [ ] **Same migration: add nullable `era_slice_key TEXT`** to both
  `kala_gochara_windows_v2` and `kala_gochara_windows` (Architecture note (c);
  consumed by Task 3.1's ownership-scoped idempotency and carried through the
  Phase 4 backfill). Nullable so v1 rows and pre-3.1 v2 rows are untouched.
- [ ] Verify migration actually applied (SELECT trigger def + index def + column —
  §N.4 surgical-migrations-verified), run both harnesses, commit.
- [ ] **Authorization line in the PR description:** this touches the untouchables
  rail; merge requires explicit native approval comment, not just CI green.

### Task 0.3 — Registry & seed hygiene

**Files:**
- Modify: `platform/scripts/seed/asset_registry_seed.ts`
- Test: existing `catalog_reconciliation.test.ts` + `platform/python-sidecar/tests/test_has_writer_completeness.py`

- [ ] Add the missing seed rows: `ka_gochara_sweep`, `ka_gochara_resonance`,
  `ka_gochara_v2_materialize` (and restore `ka_kshetra.depends_on` to the 8-edge
  migration-494 truth in the seed). Source of truth = live `asset_registry` (verified
  2026-08-10: 127 rows, all active, no orphans).
- [ ] Reconcile the full seed↔live drift: 17 asset_ids present in code+migrations but
  absent from the seed (list produced by live-DB reconciliation, 2026-08-10 session;
  the hazard class itself is documented in the seed's own ka_kshetra merge-train
  note at `asset_registry_seed.ts:2405-2432` — the 17-row figure comes from the
  reconciliation, not from that file). Record the reconciliation output in the PR.
- [ ] Add a CI guard: three-way diff (code `@register` ids ∪ migration INSERTs ∪ seed)
  → red on any writer id missing a seed row. Extend
  `test_has_writer_completeness.py` rather than a new harness.
- [ ] Separately: file a one-line native ruling request for the two
  `has_writer=false` flags on `bg_nakshatra_medical` / `bg_transit_engine`
  (registered writers exist; flag contradicts code; decide intent, document).

### Task 0.4 — Triage `ka_gochara_v2_materialize` error state on the native chart

**Files:** read-only diagnosis first; likely resolution is operational, not code.

- [ ] Read `asset_throughput.error` payload for chart `482012f1`/asset
  `ka_gochara_v2_materialize` (state `error` since 2026-08-07T23:49Z).
- [ ] Expected root cause per plan.ts:258: `bg_gochara_arcs` is `scope='global'`,
  super-admin L0 — confirm whether the arc substrate is built in the target
  environment; if absent, run the L0 build (super-admin), then rebuild the asset.
- [ ] If instead a real writer exception: file it as a campaign defect lane before
  Phase 1 proceeds (Phase 1 builds on this writer).
- [ ] Also run it once for Abhinandan (currently no throughput row) so both charts
  have a v2 baseline before parity work begins.

---

## Phase 1 — Candidate-net parity (the bulk of the distance)

**Shared design note for all Phase 1 lanes.** v2's only candidate generator today is
"body reaches exact natal degree" (`services/w2g/materialize.py`,
`candidate_point_jds` → `ContactSolver.solve`). v1's windows fire predominantly via
drishti / kakshya / ingress / bhava mechanisms. Each is a degree-crossing event, i.e.
expressible as arc-substrate range queries. Phase 1 adds one candidate **source** per
lane behind a single new module boundary so `materialize_event_class` composes sources
uniformly.

**New module:** `platform/python-sidecar/services/w2g/candidates.py`
- `class CandidateSource(Protocol): def candidate_jds(chart_ctx, event_class_ctx, horizon) -> list[CandidateJD]`
- `CandidateJD = (jd: float, mechanism: str, body: str, trigger_deg: float)` —
  mechanism ∈ closed vocabulary `{degree_contact, sign_ingress, kakshya_crossing,
  drishti_contact, bhava_boundary, station}`; unknown mechanism raises (I3/I4: no
  default).
- Dedup across sources at 1e-6 JD as today (`materialize.py` step 4), keeping the
  mechanism list per candidate for provenance.
- The mechanism tag is **discovery provenance only** — it must NOT flow into scoring
  inputs (scoring remains `compute_lambda_e` at the JD, blind to why we asked).

Each lane below follows the same step template (write failing unit test → implement
source → wire into composition → re-run per-class equivalence vs the protected corpus →
classify deltas → commit). Equivalence runs are **read-only** against
`kala_gochara_windows` (I1) via `scripts/w2g_equivalence_report.py`.

### Task 1.1 — Sign-ingress candidate source

**Files:**
- Create: `services/w2g/candidates.py` (module + this first source)
- Modify: `services/w2g/materialize.py` (compose sources; preserve existing behavior as `DegreeContactSource`)
- Test: `platform/python-sidecar/tests/test_w2g_candidates.py`

- [ ] Failing test: for Saturn over a known year, `SignIngressSource` returns JDs
  matching the arc substrate's crossings of {0,30,…,330}° within 1″ tolerance;
  assert count equals the arc-table-derived ingress count for that span; assert zero
  live swisseph calls (patch and count, mirroring
  `test_solver_query_count_is_constant_in_target_count` style).
- [ ] Implement: reuse `ContactSolver.solve` with the 12 boundary degrees as targets
  per body; direction-aware (an arc's `direction` disambiguates retrograde re-ingress
  — each crossing is its own candidate).
- [ ] Wire into `materialize_event_class` behind composition; existing degree-contact
  path must produce byte-identical rows to pre-change (regression test: golden
  comparison on the 482012f1 ±3y run output, read from `kala_gochara_windows_v2`).
- [ ] Re-run equivalence for both charts; record per-class match-rate delta in the
  lane PR (I3: measured, not asserted).
- [ ] Commit.

### Task 1.2 — Kakshya-crossing candidate source

**Files:** same module/test files as 1.1.

- [ ] Failing test: 96 cell boundaries (3°45′ grid) for a body/span; spot-check three
  crossings against independent spline evaluation; zero-swisseph assertion.
- [ ] Implement `KakshyaCrossingSource` (targets = k·3.75°, k∈0..95).
  Guard cardinality: Tier-A bodies only in this lane; measure candidate volume and
  record it (ADJUDICATION-14 band discipline — if out of band, STOP and file, don't
  silently materialize).
- [ ] Wire, equivalence re-run, classify, commit.

### Task 1.3 — Drishti-contact candidate source

**Files:** same, plus read of the frozen aspect grammar (locate the v1 drishti
offsets in the resonance/grammar layer — `services/ka_gochara_sweep/` and
`gochara_resonance_map` enrichment; do NOT re-declare aspect angles in w2g).

- [ ] Failing test: for a natal target at λ, `DrishtiContactSource` proposes JDs where
  the transiting body sits at the position FROM WHICH it aspects λ — drishti is
  directional (Mars aspects its 4th/8th *from its own position*), so the trigger
  degree is λ **minus** the house-offset arc, with both the offsets AND the direction
  convention imported from the v1 grammar module, never hardcoded or symmetrized
  here (I2). A `±` net would double candidate volume against the ADJUDICATION-14
  band and mislabel provenance.
- [ ] Implement; targets = natal degrees shifted per the imported convention,
  normalized to [0,360).
- [ ] Wire, equivalence re-run — **this lane is expected to close most of the
  1128-row gap**; classify every remaining v1-only row, commit.

### Task 1.4 — Bhava-boundary candidate source

**Files:** same; natal bhava cusp degrees from L1 (`chart_facts` /
`ga_structural` surface — reference fact_ids, never recompute cusps in w2g, §N.5).

- [ ] Failing test: enter/exit JD pairs for a body crossing a bhava span; assert
  pairing (every enter has an exit or an honest open-interval marker at horizon edge).
- [ ] Implement `BhavaBoundarySource` (two boundary degrees per bhava of interest).
- [ ] Wire, equivalence re-run, classify, commit.

### Task 1.5 — Station candidate source (arc-boundary events)

**Files:** same module/test files as 1.1.

- [ ] Failing test: `StationSource` returns exactly the station instants already
  encoded as arc cut-points in `bg_gochara_arcs` (adjacent arcs with opposite
  `direction` for a body) within the horizon; zero root-solving, zero swisseph —
  stations are free, they ARE the arc boundaries.
- [ ] Implement; wire; equivalence re-run; commit. (This is also the named
  "exceed-parity" deliverable: v1's daily grid cannot see stations as events.)

**Phase-1 scope note (I4, named non-coverage).** Design §2.2's chart-independent
calendar also names: nakshatra ingresses (27 boundaries of 13°20′ — same mechanism
as Task 1.1/1.2, add as a source the moment an event class consumes it), eclipses,
Sāde-Satī phase edges, planetary returns, and synodic double-transit geometry.
These are NOT delivered by Phase 1. They are deferred by name: none of the three
currently populated event classes' v1 rows require them for parity (verify this
claim during Task 1.6 classification — if any v1-only row traces to one of these
mechanisms, that family is promoted into a Phase 1 lane, not left deferred).

### Task 1.6 — Phase-1 exit: zero-unclassified certification

- [ ] Full equivalence battery, both charts, all populated event classes, ±3y horizon.
- [ ] **Exit criterion:** `unclassified_v1_only_needs_review` = 0 and
  `unclassified_v2_only_needs_review` = 0. Every v1-only row carries one of the
  closed classes (`v1_grid_artifact`, `v1_moon_undersampling_miss`, matched, or a
  new native-adjudicated class added to the closed vocabulary by ruling — never
  free text).
- [ ] Record raw + classified match rates in the ledger. Independent verification
  pass (PARĪKṢAKA pattern) on the numbers before the phase is declared closed.

---

## Phase 2 — Shapes and tiers

### Task 2.1 — Interval shape (root-solved enter/exit)

**Files:**
- Modify: `services/w2g/materialize.py` (lift the `shape != 'point' → skipped_reason` gate for `interval`)
- Create: `services/w2g/intervals.py`
- Test: `platform/python-sidecar/tests/test_w2g_intervals.py`

- [ ] Failing tests: (a) an interval window's `window_start`/`window_end` are the
  root-solved instants where `raw_lambda` crosses `ACTIVATION_EPS` (bracketed
  bisection between adjacent candidate JDs of opposite activation state);
  (b) `peak_date` = argmax over the analytic λ_e between bounds (design §2 piece 4);
  (c) an interval truncated by the horizon edge carries an explicit open-edge marker.
- [ ] Implement. **Deliberately do NOT port** v1's chunk-continuity machinery
  (`sweep.py:37-120`, four failed generations documented). Docstring must state the
  claim precisely: continuity is unnecessary **provided chunking never truncates an
  interval** — which Task 3.1 must uphold (its era-slices scope candidate
  *discovery* only; interval root-solving is always free to cross slice edges).
  An unconditional "no chunking exists" claim would be falsified by 3.1.
- [ ] Equivalence re-run now includes interval-shape classes; classify; commit.

### Task 2.2 — Chain shape (milestone templates)

**Files:**
- Modify: `services/w2g/materialize.py`, `services/w2g/intervals.py`
- Test: extend `test_w2g_intervals.py`

- [ ] Failing test: for a chain-shaped event class, one row per `milestone_template`
  entry with correct `milestone_id` and `is_irreversibility_milestone`, scored on its
  own configuration (import the v1 milestone logic; do not re-derive).
- [ ] Implement, equivalence, classify, commit.

### Task 2.3 — Tier B bodies (Sun, Mercury, Venus) — **depends on Task 2.1**

- [ ] Implement Tier B per its actual ratified semantics (`tiers.py`
  `_POLICY_REASONS`): Sun/Mercury/Venus candidates are materialized **only inside
  intervals Tier A has already elevated, plus their own stations** — NOT full-span
  candidate discovery (full-span Tier B is exactly what ADJUDICATION-14 forbade to
  hold the volume band). This is why the task hard-depends on 2.1: "elevated
  interval" must exist as a computed object first.
- [ ] Failing test: a Tier-B candidate outside every Tier-A elevated interval and
  not a station is never proposed; one inside is.
- [ ] Measure candidate volume per chart, assert within the ratified band, record.
- [ ] Equivalence re-run, classify, commit.

### Task 2.4 — Tier C Moon: lazy refinement service (elevation, not parity)

**Files:**
- Create: `services/w2g/moon_lazy.py` + serving hook (design §2 piece 5)
- Test: `platform/python-sidecar/tests/test_w2g_moon_lazy.py`

- [ ] Failing test: a muhurta-scale query for a specific day materializes Moon
  contacts for that day only, on demand, cached by `(chart_id, jd_day)`; never a
  full-span Moon materialization (the ADJUDICATION-14 clause that keeps the SLO
  reachable).
- [ ] Implement minimal: an internal function the serving layer can call; full
  serving integration is Phase 4 scope.
- [ ] Commit. **Parity note (I4):** v1's daily grid *does* include Moon-driven rows;
  until this lane's serving hook is live, the equivalence classifier must keep
  routing Moon-driven v1-only rows to their own class — visible, counted, honest.

---

## Phase 3 — Horizon and SLO

### Task 3.1 — Full-century horizon

**Files:**
- Modify: `pipeline/orchestrator/writers/ka_gochara_v2_materialize.py`
  (wire `full_century_horizon()`, already present at `materialize.py:138-144`)
- Test: extend `writers/tests/test_ka_gochara_v2_materialize.py`

- [ ] Failing test: `plan_substeps` under century mode = one substep per
  (event_class × era-slice) where era-slice is a **decade**, not a year — v2's
  per-substep cost profile is minutes, not v1's 4+ minutes/year; keep substeps
  well under the 1800s watchdog with margin measured, not assumed.
- [ ] **Slice-boundary semantics (binding, protects Task 2.1's no-continuity
  claim):** era-slices partition candidate *discovery* only. Any interval whose
  bracketing candidates straddle a slice edge is root-solved across the edge by
  whichever substep discovers its opening candidate. Idempotency scoping is
  two-level: `(chart_id, event_class, generation='2.0')` is the OUTER invariant
  (a full-class rebuild deletes at this scope); a per-slice delta re-run deletes
  at the INNER scope `… AND era_slice_key = $slice`, where `era_slice_key` is a
  stored provenance column (Architecture note (c); populated at insert time with
  the slice that owned the opening candidate — stored, not derived, precisely
  because a root-solved `window_start` can precede the owning slice's date range,
  making any date-range proxy wrong at exactly the edge this bullet exists for).
  No interval is ever truncated or double-written at a non-horizon edge. Failing
  tests: an interval spanning a decade edge yields exactly one row with correct
  root-solved bounds; a delta re-run of the adjacent slice does not delete it.
- [ ] `horizon_status` transitions `progressive_partial → full_century` only when
  every era-slice's fingerprint is current (earned, I3).
- [ ] Per-slice delta-aware skip: extend `class_fingerprint` to
  `(class, GRAMMAR_VERSION, targets, bodies, arc_fps, era_slice)` so one changed
  input re-runs only affected slices — this is the plan-level embodiment of the
  Nirmāṇa slice-receipt principle (cross-ref NIRMANA target-state artifact when it
  lands).
- [ ] Build century for BOTH charts into `kala_gochara_windows_v2`; record wall-clock.

### Task 3.2 — SLO: ≤15 min full-century per chart

- [ ] Profile first (I3): confirm the bottleneck is per-candidate `compute_lambda_e`
  calls (922s/±3y implies ~century ≫ SLO without change). Publish the profile in
  the lane PR.
- [ ] Optimization candidates, in order of safety: (a) batch DB reads inside the
  scoring context (targets/sentences fetched once per class, not per candidate);
  (b) memoize pure sub-computations across adjacent candidates; (c) parallelism
  across event classes **within the chart-level advisory lock** — design §7 N5
  flags lock granularity as a PARK-class question: if (c) is needed, file for
  native ruling rather than weakening the lock silently.
- [ ] **Exit criterion:** century build ≤15 min per chart, measured on both charts,
  reproducible from build logs (closing debt D1089-2: SLO figures must be
  independently reproducible).

---

## Phase 4 — Certification and cutover (gated on W6 ruling, Task 0.1)

### Task 4.1 — Full certification battery

- [ ] Implement the deferred equivalence items §3.3–3.4 (specimen continuity,
  determinism run-to-run, adversarial probes) — they are named on every report as
  deferred; certification requires them implemented, not waived. (§3.5 is the
  POST-cutover battery — it is Task 4.5, not this task; naming it here would
  silently narrow the design.)
- [ ] Run the full pre-cutover battery: both charts, all classes, all shapes,
  century horizon. Exit: zero unclassified; determinism byte-stable across two
  runs; adversarial probes pass.
- [ ] Independent PARĪKṢAKA verification of the battery output. Record in ledger.

### Task 4.2 — Execute cutover (mechanism per W6 ruling; steps below assume Option A)

- [ ] Backfill: one audited transaction per chart, native pre-authorized, plain
  INSERT of `generation='2.0'` rows. Migration 540 gates DELETE/UPDATE/TRUNCATE
  only — INSERT is never trigger-gated — and Task 0.2's replaced natural-key index
  (generation-inclusive) makes same-natural-key coexistence with v1 rows legal by
  construction. v1 rows are READ but never written (I1). **The
  `app.allow_protected_sweep_rewrite` GUC is NOT used in this task under any
  circumstance** — no failure mode of an INSERT can require it; on ANY error the
  transaction rolls back and the campaign STOPS to diagnose. Normalizing the master
  override inside the campaign's most dangerous transaction is exactly the habit I1
  exists to prevent.
- [ ] **Repoint the ongoing write path (cutover is a live pipeline, not a
  snapshot):** after backfill, `ka_gochara_v2_materialize`'s target table switches
  `kala_gochara_windows_v2 → kala_gochara_windows` with its §N.3 delete-then-insert
  at the two-level scope defined in Task 3.1 (outer invariant
  `(chart_id, event_class, generation='2.0')`; per-slice delta re-runs add
  `era_slice_key = $slice`) — legal against the two protected charts precisely
  because Task 0.2's guard protects `protected_generations` (=`{v1}`) rows, not
  2.0 rows. The `_v2` table is thereafter retained as the certification workbench,
  not a serving source. Update the writer's mutation-guard test
  (`test_ka_gochara_v2_mutation_guard.py` — its `PROTECTED_TABLE_RE` currently
  treats any `kala_gochara_windows` reference as forbidden) to instead assert the
  new invariant: every DML statement in the writer carries the `generation='2.0'`
  scope predicate.
- [ ] **Cockpit truth follows the repoint (§N.4):** same PR ships a registry
  migration updating `ka_gochara_v2_materialize`'s `target_table` to
  `kala_gochara_windows` and its `count_sql` to count
  `kala_gochara_windows WHERE chart_id = $1 AND generation = '2.0'`. Without this,
  Nirmāṇa stats keep counting the retained `_v2` workbench while real builds write
  the serving table — the exact "cockpit reads `count_sql`, not throughput" trap
  §N.4 names.
- [ ] Flip `kala_gochara_authority.authoritative_generation = '2.0'` for
  **Abhinandan first** (the standing SAFE rehearsal chart), verify all three MCP
  tools + reading_checklist serve v2 rows correctly (spot-check against battery
  output), soak for a native-decided period, then flip the native chart.
- [ ] Update `register_gochara_windows.ts` `SOURCE_CITATION` (currently hardcodes
  "D-5 Lane G-4 ka_gochara_sweep writer") to be generation-conditional; add
  `kala_gochara_windows_v2` to the db/query allowlist only if W6 chose Option B
  (otherwise not needed).

### Task 4.3 — Rollback rehearsal (before the native-chart flip)

- [ ] On Abhinandan: flip authority back to 'v1', assert serving returns the frozen
  corpus byte-identically (this is what makes the cutover *reversible in fact*,
  not just in design); flip forward again. Record both flips in the ledger.

### Task 4.4 — v1 retire-in-place

- [ ] `ka_gochara_sweep` writer: mark superseded in docstring + `catalog_status`
  → 'RETIRED' path decision (native ruling; the asset row stays, per
  retain-in-place hygiene §A). Data: **never deleted**; protection (I1) stays on
  both charts permanently, now additionally covering the certified 2.0 generation
  via `protected_generations` (Task 0.2's column).
- [ ] LEL prospective ledger (`prospective_ledger.ts:164-252`) — verify
  `computeConfigurationSignature` behaves identically over v2-generation rows
  (it requires a *real* row; generation flip must not change its semantics).
  Add a regression test beside `reading_checklist.fetch_gochara_sweep.test.ts`.

### Task 4.5 — Post-cutover battery (design §3.5 — the full item, not waived)

- [ ] After BOTH charts are flipped and the ongoing write path is live (4.2): run
  the design's §3.5 post-cutover regression battery — full serving-surface
  regression plus the D-4b gate scoring assertions with the
  calibration-multiplier-stability tolerance, results dispositioned by the native.
- [ ] Exit: battery green or every divergence carries a native disposition in the
  ledger. The campaign does not close CLOSED without this task — closing without
  it would be the §N.8 no-op-completion defect at campaign scale.

---

## Phase 5 — Follow-on (pointers, not scope)

- Nirmāṇa target-state integration: surface per-slice fingerprints/receipts in the
  cockpit; blast-radius preview reads v2's delta-aware skip data. Lives in the
  NIRMANA_TARGET_STATE artifact (separate ratification).
- ka_kshetra strangler-fig: its `load_legacy_crosscheck`
  (`services/ka_kshetra/stage4_field.py:937-955`) can gain a v2 cross-check leg
  once authority flips — W6-adjacent, file when Phase 4 closes.
- Consider extending Tier C lazy refinement to serving surfaces beyond muhurta
  (kala_now_get / kala_windows_get fallbacks).

## Sequencing & effort

Phase 0 first (0.3/0.4 immediately; 0.1/0.2 are native-paced). Phases 1→2→3 strictly
ordered (each equivalence re-baseline depends on the prior). Phase 4 only after 0.1,
0.2, and Phase 3 exit. Rough effort: P1 ≈ 1.5–2 wks · P2 ≈ 1–1.5 wks · P3 ≈ 1 wk ·
P4 ≈ 1 wk, all single-engineer-equivalent, parallelizable across lanes within P1/P2.

*End GOCHARA_V2_PARITY_CAMPAIGN_PLAN_v1_0.md v1.0*
