---
artifact: BODHA_ONECLICK_BUILD_REMEDIATION_PLAN
canonical_id: BODHA_ONECLICK_BUILD_REMEDIATION_PLAN
version: 1.0
status: CURRENT
created: 2026-06-27
owner: native (Abhisek Mohanty)
scope_decision: "Correctness + loud-fail (efficiency deferred); plan-only proof (no live build test this round)"
relates_to: [L2_BODHA_CLOSE, ORCHESTRATOR_CONVERGENCE_CLOSE, CURRENT_STATE]
---

# Bodha One-Click-Build Remediation Plan v1.0

## Purpose

Make **clicking Build (Rebuild) on the Bodha layer** a trustworthy one-action operation:
the layer either **builds out completely and correctly, following the DAG**, or **fails
loudly and visibly** — never silently thin, never green-but-empty. This plan remediates
the six gaps found by the 2026-06-27 four-axis cold-start audit (idempotency, upstream-data
assumptions, layer-build/error-isolation, external-service/cost).

**This plan does NOT reopen the L2 seal.** The current native data is correct and verified
(L2_BODHA_CLOSE v1.3). These fixes govern the *next* build, not the current state.

## What is already sound (audit-confirmed — do NOT touch)

- **Idempotency:** all 10 writers delete-then-insert (or ON CONFLICT) scoped to
  (chart_id × natural key) before insert; rebuild-over-populated is safe — no unique/FK
  violations. The historical bo_upaya FK-order hazard is fixed (child prescriptions deleted
  before parent resonances).
- **Orchestrator:** single FROZEN driver; topo-sorted plan processed in one Cloud Run
  execution; per-substep SAVEPOINT + commit; successfully-built assets commit durably.
- **Error isolation:** one writer raising marks that asset `error` and **continues** the run
  (does not abort); earlier assets stay committed.
- **Deterministic-first:** only bo_samskara calls an external service (Vertex embeddings);
  the other 9 are pure Python/SQL/numpy. No generative-LLM call anywhere. Rule intact.

## The six gaps

| # | Gap | Class | Symptom on a click |
|---|-----|-------|--------------------|
| G1 | `action='build'` on a fully-lit layer = no-op (422); must use Rebuild | UX trap | "Build" appears to do nothing |
| G2 | `bo_karanajala` reads `bodha_cgm_nodes` (bo_bimba output) but `depends_on` omits `bo_bimba` | **Correctness** | topo may run karanajala before bimba → empty node map → **0 CGM edges, silently, build green** |
| G3 | Pervasive **silent degradation** on empty/partial upstream (the bo_anveshana bug as a class) | **Correctness** | thin/0 rows reported as success |
| G4 | Layer-scoped Bodha build does **not** verify L1/L0 present | **Correctness (cross-layer)** | Bodha builds thin + green if chart_facts / ga_structural / brahma_remedy_corpus absent |
| G5 | 5 of 8 materialized views never refreshed by any build | Staleness | MV readers see old data post-rebuild |
| G6 | bo_samskara re-embeds all ~333,690 vectors every rebuild; no retry/backoff; no Cloud Run mem floor | Efficiency | slow (~75–160 min), Vertex quota blip = hard fail | 

**Scope of THIS plan (native decision 2026-06-27): G1–G5 (correctness + loud-fail).
G6 (efficiency) is DEFERRED to a follow-on — documented here, not built now.**

---

## Phased remediation (G1–G5)

### Phase 0 — Pre-flight (no code)
- Confirm prod registry still matches the post-#304 state (10 bo_* CURRENT, depends_on intact)
  before changing any edge. Snapshot `asset_registry` bodha rows.
- Confirm the seed (`asset_registry_seed.ts`) is the edit surface for DAG edges (it is, per
  the #304 reconcile) — the G2 edge fix lands in the seed AND a migration, kept in agreement.

### Phase 1 — G2: close the hidden DAG edge (smallest, highest-severity)
- Add `bo_bimba` to `bo_karanajala.depends_on` → `[bo_laksana, bo_bimba]`.
- Land in BOTH the seed (`asset_registry_seed.ts`) and a new migration (next number after 326;
  verify live max first — there were 327+ in flight) as `ON CONFLICT DO UPDATE SET depends_on=...`.
  Do NOT revert migration 326. Keep seed == migration (the #304 idempotence discipline).
- Verify: topo-sort now always orders bimba before karanajala; re-run the registry acyclicity
  check; confirm no new cycle.
- **Acceptance:** in a layer plan, `bo_bimba.position < bo_karanajala.position`, always.

### Phase 2 — G3: replace silent degradation with loud failure (the core correctness work)
For each writer, convert "empty/partial upstream → 0 rows + success" into an explicit raise
(`RuntimeError`/`ValueError`) with a clear message, mirroring the bo_anveshana embedding fix
already shipped. Specific sites the audit named (verify line numbers live before editing):
- **bo_laksana:** empty `chart_facts` for the chart → RAISE (currently logs + returns 0).
  Keep the per-row SAVEPOINT skip for individual bad facts, but if the **whole** projection is
  empty, fail loud.
- **bo_karanajala:** empty `bodha_cgm_nodes` (node_map empty) → RAISE rather than silently
  creating zero edges. (With G2 fixed this shouldn't happen, but the guard makes it loud if it does.)
- **bo_bimba:** all `configuration_jsonb` unparseable → RAISE rather than emitting 0 nodes.
- **bo_upaya:** empty shadbala / bhava_bala → RAISE (currently defaults strengths to 1.0,
  silently flattening judgment); empty `brahma_remedy_corpus` → RAISE (no remedies = broken, not thin).
- **bo_samskara:** Vertex failure or 0 embeddings written when signals > 0 → RAISE
  (the per-row skip-all-and-continue path must not report success on total failure).
- **bo_drishti:** lens with zero wildcards → at minimum log ERROR (violates the ADDITIVE
  guard); escalate to RAISE if a template-only lens is structurally invalid.
- **bo_anveshana:** already fixed (loud parse failure) — confirm no remaining silent path.
- **bo_pramana_mapa:** `_count_one` swallowing a missing-table exception → distinguish
  "table empty (0, legitimate)" from "table/asset missing (build defect → surface, not 0)".
**Principle:** a writer producing materially-below-floor output because its input was thin must
FAIL, not pass. The B6 G-MAG floor gate is the backstop; the writer is the first line.

### Phase 3 — G4: L1/L0 precondition gate for layer-scoped builds
- Before the Bodha writers run (or at plan-resolution for a layer-scoped Bodha build), verify
  the cross-layer preconditions exist for the chart: `chart_facts` rows > 0, `ga_structural`
  present, and `brahma_remedy_corpus` (L0) present. If any is missing/empty → fail the build
  with a precondition error naming the missing upstream, BEFORE running writers (fail fast).
- Decide the gate's home: cleanest is a build-plan precondition check (layer-scoped Bodha
  requires L1+L0 lit) OR a bo_laksana-entry assertion (it's the root and reads all three).
  Prefer the plan-level check so the failure is surfaced before any Cloud Run cost.
- Do NOT auto-build L1/L0 from a Bodha click — surface the precondition and let the operator
  build upstream first (matches the layer-scoped intent).
- **Acceptance:** clicking Build on Bodha for a chart with empty chart_facts returns a clear
  "L1/L0 not built" error, not a thin green build.

### Phase 4 — G5: refresh all materialized views
- Extend the MV-refresh step (currently 3 MSR MVs in bo_pramana_mapa) to cover all 8, OR move
  MV refresh to an explicit end-of-layer build step. The 5 unrefreshed:
  `mv_cdlm_static_summary`, `mv_cdlm_top_K_links_per_chart`, `mv_cdlm_per_tradition_summary`,
  `mv_cdlm_dasha_window_lookup`, `mv_cdlm_pattern_summary`.
- Each REFRESH wrapped so a single MV failure logs loud but doesn't silently leave a stale MV
  reported as fresh. (CONCURRENTLY only if a unique index exists; else plain REFRESH.)
- **Acceptance:** after a full Bodha rebuild, all 8 MVs reflect current base-table data.

### Phase 5 — G1: Build-vs-Rebuild UX clarity
- The cockpit must make it unmistakable that **Build** acts only on dormant/error/missing
  assets, and **Rebuild** forces all-in-scope. Options (native to choose at implementation):
  (a) when a Build resolves to an empty plan on a lit layer, return a friendly message that
      names Rebuild as the action for a fully-built layer (not a bare 422);
  (b) auto-label the primary action per current state (the cockpit-build-action model already
      specifies auto-labelled Build/Update/Rebuild — confirm it surfaces Rebuild when lit);
  (c) both.
- **Acceptance:** a user intending "rebuild my already-built Bodha layer" cannot land on a
  silent no-op; the right action is obvious or the message redirects them.

### Phase 6 — Proof (PLAN-ONLY this round, per native decision)
- No live end-to-end cold build is run in this round. Instead:
  - Add/extend tests that assert the fixes structurally: G2 topo-order test (bimba<karanajala);
    G3 loud-fail unit tests (each guarded writer RAISES on empty upstream — RED proves the guard
    fires); G4 precondition test (empty chart_facts → precondition error); G5 test that a rebuild
    refreshes all 8 MVs; G1 plan test (Build on lit layer → friendly redirect, Rebuild → full plan).
  - These are the same RED-first discipline that proved the B6 gates: each new guard must be
    shown to FIRE on the broken/empty state before the fix flips it green.
- The live one-click cold-build verification (build Bodha from empty on a 2nd chart through the
  real orchestrator, assert all 10 hit floor in one pass) is **deferred to when the native next
  runs a real build** — captured as a follow-on, not executed here.

---

## Deferred (documented, NOT built this round)

**G6 — embedding-build efficiency + resilience.** Follow-on workstream:
- Incremental embeddings: track a per-signal content hash; skip re-embedding unchanged signals
  on rebuild (today: full DELETE + re-embed of ~333,690 vectors / ~3,337 Vertex calls every click).
- Vertex retry/backoff: exponential backoff + jitter on 429/quota; a quota blip currently hard-fails
  bo_samskara with no recovery.
- Explicit Cloud Run Job memory floor (`--memory>=1Gi`); current default 512MB vs ~450MB peak = no margin.
These are efficiency/robustness, not correctness — a build today is correct (or loud-fails after G1–G5),
just slow and quota-fragile. Open when the native prioritizes build cost/latency.

## Out of scope / guardrails
- Do NOT modify the FROZEN orchestrator contract, migration 326, or the writers' idempotency pattern.
- Every DAG-edge change lands in seed AND migration, kept in agreement (no drift — the #304 lesson).
- Loud-fail conversions must not break the legitimate per-row bad-fact skip (skip one row = fine;
  whole-asset-empty-because-upstream-thin = fail).

## Changelog
- v1.0 (2026-06-27): initial plan from the four-axis cold-start build audit; scope = correctness +
  loud-fail (G1–G5), efficiency (G6) deferred; proof = plan-only (live cold-build deferred).
