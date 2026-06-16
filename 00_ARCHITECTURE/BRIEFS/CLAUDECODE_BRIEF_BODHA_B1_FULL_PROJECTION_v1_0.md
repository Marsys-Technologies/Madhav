---
artifact: CLAUDECODE_BRIEF_BODHA_B1_FULL_PROJECTION_v1_0.md
canonical_id: BODHA_B1_FULL_PROJECTION_BRIEF
version: 1.0
status: READY_TO_EXECUTE
authored_by: Cowork (planning) 2026-06-16
authored_for: Claude Code in Antigravity IDE (NOT the CLI)
execution_mode: CONTINUOUS / AUTONOMOUS — phase-by-phase, no human gate between phases. Stop only on a real dependency miss or a Tier-3 event (destructive op, genuine ambiguity, needed architecture change → raise to native). Native reviews retrospectively via cockpit/Atlas + Smṛti.
data_plane: ALWAYS prod via the Cloud SQL Auth Proxy (platform/scripts/start_db_proxy.sh, 127.0.0.1:5433)
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
governing:
  - BODHA_BUILDOUT_CONTEXT_HANDOFF_v1_0.md (the self-contained context — read it first)
  - L1_L2_RELATIONSHIP_ARCHITECTURE_DECISION_v1_0.md (the projection model — intrinsic L1 vs population-level L2)
  - A10_MSR_SPEC_v1_0.md (§4 salience_formula_v1, §11 MVs) + A11/A12/A13/A14 specs
  - ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md §2 (FROZEN WriterBase contract) + §5 (conformance checklist)
  - MSR_COMPUTED_VALUE_DRIFT_HANDOFF_v1_0.md (Trap 1) + MSR_UCN_CONTAMINATION_AUDIT_v1_0.md (Trap 2)
supersedes_for_b1: >
  CLAUDECODE_BRIEF_WAVE3_4_RETRIEVAL_AND_BODHA_v1_0.md §PHASE B1 is REVISED by this brief.
  Wave-4 B2–B5 still stand; this brief restates them (§B2–§B5) so it is a complete arc. The B1
  difference is the NATIVE DECISION below (full-enumeration parity, not the merged 32-category subset).
native_decision_2026_06_16:
  projection_scope: FULL_ENUMERATION_PARITY
  meaning: >
    bo_laksana projects EVERY ga_structural fact row (and the other projected ga_* categories) to one
    MSR signal — NOT the curated 32-category allow-list the merged writer currently hardcodes. MSR
    signal count tracks the ga_structural fact count (handoff acceptance read literally). Salience is
    still computed per signal (salience_formula_v1) but strength is a COLUMN, never a FILTER — the
    weak tail is kept (no-threshold-drop). This is the single most important change in §B1.
---

# Bodha B1 — bo_laksana as FULL Projection + the anti-drift spine, then B2–B5 to L2 seal

> **Read order before you touch code:** (1) `BODHA_BUILDOUT_CONTEXT_HANDOFF_v1_0.md`; (2)
> `L1_L2_RELATIONSHIP_ARCHITECTURE_DECISION_v1_0.md`; (3) `A10_MSR_SPEC_v1_0.md`; (4) both trap docs;
> (5) `ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md §2 + §5`. Verify live state from `CURRENT_STATE_v1_0.md`
> §2 + `git log`, never a frozen doc. Then execute.

## §0 — Why this brief exists (the one thing the prior brief got wrong)

The Wave-4 brief said: *"signal count tracks ga_structural fact count, not a predicate catalog."* But
the **merged** `bo_laksana.py` reads `chart_facts WHERE fact_category = ANY(<hardcoded 32-item list>)`
— a curated subset, not the full enumeration. Cowork verified (2026-06-16) that all 32 names match L1
output exactly (no silent-zero drift) — **but a curated subset is not full projection.** It would
populate `bodha_msr_signals` with the salient signals and silently leave the long tail of raw
per-varga aspect / argala / dispositor rows un-projected.

**Native ruled (2026-06-16): FULL ENUMERATION PARITY.** Every ga_structural row → one MSR signal.
That makes the projection model literally provable (count parity), keeps the weak tail (no-threshold-
drop, §N.4), and removes the "which 32 categories?" curation judgment from the deterministic base
(Trap 2 — no human/LLM judgment in what fires). This brief makes that the core of B1.

**Inherited non-negotiables (every phase):** deterministic-first (Python, no generative LLM in the
build; embeddings-as-transform OK); no audience tier; no silent drops (errors surfaced/flagged, never
hidden); per-chart isolation by `chart_id`; **real `fact_id` references, never mock**; FROZEN
orchestrator contract (`@register('bo_*')` WriterBase, runs on `ctx.db_conn`, NEVER commits/closes it,
NEVER writes `asset_throughput`, gets `chart_id`+`birth_params` from `ctx.config`); `count_sql` is
data-truth; floors aspirational (`target_floor` = achieved after build, never fabricate to a number).
**If a writer seems to need an orchestrator-contract change → STOP, raise with the native.**

---

## §B1 — bo_laksana: FULL projection of ga_structural (the root; everything fans from it)

### B1.0 — Preconditions (verify before writing code; fix-forward if any fail)
1. **Cloud SQL proxy up.** `platform/scripts/start_db_proxy.sh`; confirm `127.0.0.1:5433` reachable.
   The build cannot run without it (this was the B5 blocker — `CURRENT_STATE` v5.75).
2. **Migrations 226 + 230 actually applied to prod.** Don't infer from file presence — query prod:
   confirm `bodha_msr_signals` exists at full spec schema (the ~50 cols the INSERT targets), and that
   the registry rows for the 8 `bo_*` assets carry the spec `count_sql` / `target_table` (mig 230).
   If a migration is on disk but not applied, apply it **surgically** (psql against prod, not deploy.yml
   auto / bulk migrate.ts — [[feedback-deploy-migrations-silent-noop]]); readback after apply.
3. **L1 is built on the native chart.** `ga_structural` has its full row count for `482012f1` across
   all vargas × 5 ayanamshas (handoff cites 74,644). If L1 isn't built for this chart, STOP — B1 has
   nothing to project. (FORENSIC 7/7 is the L1 authority gate; do not proceed past a FORENSIC fail.)

### B1.1 — Convert bo_laksana from curated-subset to full-enumeration projection
This is the load-bearing change. In `platform/python-sidecar/pipeline/orchestrator/writers/bo_laksana.py`:

- **Remove the hardcoded category allow-list as a FILTER.** The merged writer fetches only rows whose
  `fact_category` ∈ the 32-item `ALL_SIGNAL_CATEGORIES`. Replace that with a fetch of **the full
  ga_structural fact population** for `(chart_id, ayanamsha_id)` — every relationship/conjunction/
  aspect/argala/dispositor/parivartana/composite/avastha row ga_structural emits, plus the other
  genuinely-projected ga_* categories the spec wants as signals (sensitive, panchanga, sade-sati).
  - **Decision rule for "which categories are signals":** project every `fact_category` that
    `source_asset_id = 'ga_structural'` produces (the relational fabric), UNION the explicitly-named
    sensitive / sade-sati / panchanga signal categories. Do **NOT** project the pure *helper* lookups
    (`graha_shadbala_total`, `graha_dignity_per_varga`, `ashtakavarga_pinda_sarva`) — those are salience
    INPUTS, not signals; keep them as the lookup dicts they already are. Make this a single documented
    constant (e.g. `SIGNAL_SOURCE_ASSETS` + `SIGNAL_HELPER_CATEGORIES_EXCLUDED`) so the include/exclude
    boundary is auditable, not scattered.
  - **Net effect:** the allow-list stops being a curation gate. If ga_structural enumerates it, it
    becomes a signal. The 32 categories become a *domain/tradition mapping table* (keep
    `CATEGORY_DOMAIN_MAP` / `CATEGORY_TRADITION_MAP` for the categories you can map; for an unmapped
    category, default `domains_affected = ['general']`, `tradition = 'parashari'`, and **flag it** in
    the writer notes so the native can extend the maps — do not drop the row for lacking a mapping).

- **Keep salience as a column, never a filter.** `salience_formula_v1` still runs per signal;
  `computed_salience` + the decomposition columns are stored; `top_k_salience_rank` is assigned across
  the full population per `(chart_id, ayanamsha_id)`. **No `WHERE salience > x`, no `LIMIT N` drop.**
  Every projected row is inserted. (This is the no-threshold-drop pillar + Trap 2 anti-contamination.)

- **constituent_facts_array = the real L1 fact_id, always.** Each signal references its source
  `chart_facts.fact_id` (it already does: `constituent_facts_array = [fact_id]`). It must NEVER restate
  the L1 computed value as its own truth (Trap 1) — it inherits by reference. FORENSIC-anchored signals
  inherit L1 values (e.g. Muntha = Libra/7H/Venus is read from L1, not re-derived).

- **Heavy-writer shape stays:** `plan_substeps` = one SubStep per ayanamsha; `run_substep` builds the
  lookups, fetches the full fact population, builds one row per fact, ranks, DELETE-then-INSERT scoped
  to `(chart_id, ayanamsha_id)` (per-layer idempotency, §N.3). Do NOT commit/close `ctx.db_conn`.

- **Performance:** full enumeration is ~15× the curated subset. Keep the `_batch_insert` batching;
  if a single ayanamsha's row build is large, stream/iterate rather than holding everything before
  ranking is fine (ranking needs the full per-ayanamsha set in memory — acceptable at this scale, but
  log row counts so a regression is visible). Do not introduce a row cap to "make it fast."

### B1.2 — Update the unit/contract tests for bo_laksana to the parity model
- Tests must assert: **(a)** no category allow-list gates the fetch (projection is by source-asset, not
  a curated name list); **(b)** salience is never used as an insert filter; **(c)** every built row
  carries a non-empty `constituent_facts_array` whose element is a real `fact_id` string;
  **(d)** unmapped categories still produce rows (flagged, not dropped). Keep the existing salience-
  formula unit tests green (the formula itself is unchanged).

### B1.3 — Run B1 and PROVE THE ANTI-DRIFT SPINE before anything else fans out
Run **only** `bo_laksana` for the native chart first (single-asset run, not the whole layer):
`POST /api/cockpit/runs scope=asset/bo_laksana` for `482012f1` (or the orchestrator's single-asset
entry). Then verify, against **prod**, in this order — and **HALT on any failure; do not fan out onto
a broken root**:

1. **Spine resolves (the load-bearing acceptance).** Every `bodha_msr_signals.constituent_facts_array`
   element resolves to a real `chart_facts.fact_id` row for this chart. Query for any signal whose
   array element has no matching `chart_facts` row → **must be zero**. `[verify-against: prod] [via: psql_prod]`
2. **Count parity (the native decision).** `count(bodha_msr_signals WHERE chart_id=native)` ==
   `count(projected ga_structural + sensitive/sade-sati/panchanga signal rows)` for the same chart.
   The MSR signal count **tracks the ga_structural fact count** (not a curated subset, not a predicate
   catalog). Record both numbers in the run notes. `[verify-against: prod]`
3. **No re-derivation / no value-restatement (Trap 1).** Spot-check ≥10 signals across categories:
   the signal's stored configuration reflects the L1 value it cites, not a recomputed one. Pick the
   FORENSIC anchors explicitly (Sun=Capricorn, Moon=Purva Bhadrapada, Lagna=Aries, + Muntha) and
   confirm the signal inherits the L1 value. `[verify-against: prod]`
4. **Weak tail present (no-threshold-drop).** Confirm low-`computed_salience` signals ARE in the table
   (query the bottom decile of `computed_salience`; it must be non-empty and far below the top). A
   curated build would be missing these. `[verify-against: prod]`
5. **Idempotency.** Re-run bo_laksana for one ayanamsha; row count is stable (delete-then-insert
   replaced, did not accrete). `[verify-against: prod]`

**If 1 or 2 fail, the projection is wrong — fix the projection, do NOT proceed to B2.** Everything
downstream inherits from this root; a broken root contaminates the whole layer.

### B1.4 — Build the A10 §11 materialized views
`mv_top_signals`, `mv_recurring_patterns`, `mv_domain_summary` (or the names the spec/migration use).
Refresh after the insert. These are read-optimization over the now-complete signal set.

---

## §B2 — Fan-out (parallel on bo_laksana; only AFTER B1.3 passes)

All project/aggregate from the now-complete `bodha_msr_signals`. Each populates its A11/A12/§14 tables.

- **`bo_sangati` (CDLM, A11):** `bodha_cdlm_cells`, `_domain_rollups`, `_chart_summary`,
  `_pattern_clusters` via `linkage_formula_v1`, **plus `bodha_convergence`** (convergence-density-per-
  domain via `convergence_formula_v1`, §13.1). Convergence rows are **first-class rows**, not just
  columns — N independent L1 signals → one domain = weight of evidence.
- **`bo_karanajala` (CGM edges, A12):** `bodha_cgm_edges`, `_sub_graphs`, `_motifs`, `_chart_summary`,
  **plus `bodha_contradictions`** (signals in tension — doubles as the drift guardrail) **and
  `bodha_cgm_paths`** (§13.1). This is the graph — **invest deepest**: final-dispositor (chart's center
  of gravity), parivartana cycle structure, weighted centrality via `centrality_formula_v1` (most
  consequential factor), significator path-analysis. (A12 is ONE igraph compute; `bo_bimba` is a thin
  nodes face on the same compute — confirm against the DAG executor.)
- **`bo_bimba` (CGM nodes, A12):** `bodha_cgm_nodes` (graha + bhava + domain nodes per ayanamsha).
- **`bo_samskara` (embeddings):** `bodha_signal_embeddings`, **1:1 with MSR signals.** Note: the
  merged writer uses `placeholder_hash_v1` (deterministic 768-dim, NOT real semantic embeddings).
  **Keep the placeholder for this build** (deterministic-first; it satisfies the 1:1 + schema), but
  **flag explicitly in the run notes + L2_BODHA_CLOSE** that real semantic embeddings are a follow-up
  before retrieval quality depends on them. Do not silently present the placeholder as semantic.
- **`bo_samvada` (UCD, A14) = Option A:** a read-side join — `vw_chart_digest` view + `query_ucd` tool.
  **NOT a per-chart writer.** (UCN narrative writer is retired per A14.)

**B2 acceptance [verify-against: prod]:** each fan-out asset's tables populated; convergence +
contradiction are first-class ROWS; CGM graph metrics present (centrality, paths, final-dispositor);
embeddings 1:1 with MSR; `query_ucd` returns the digest. Convergence/contradiction formulas stamped
with their `_v1` version on each row.

---

## §B3 — bo_upaya (RM); depends_on bo_laksana + bo_sangati
All 6 `bodha_rm_*` tables via `resonance_score_v1` + `resonance_match_score_v1`. Every remedy is
**labelled from `brahma_remedy_corpus` (L0)** — grounded, never invented; each carries a classical
citation. **Acceptance [verify-against: prod]:** 6 RM tables populated; every remedy row resolves to a
`brahma_remedy_corpus` citation; resonance scored deterministically (formula-versioned).

## §B4 — bo_pramana_mapa (global scorecard) + the UCD read surface
- `bo_pramana_mapa` → global `synthesis_quality_scorecard` + the **Trap-1 audit baked in** (the
  scorecard itself re-checks that constituent_facts resolve — the spine becomes a standing CI-able
  metric, not a one-time check).
- Confirm the UCD read surface (`vw_chart_digest` + `query_ucd`) returns the unified digest.
- **Acceptance:** scorecard populated; Trap-1 audit reports zero unresolved fact_ids; `query_ucd` works.

## §B5 — Orchestrator full-layer build + cockpit verify + retrieval tools + L2 seal
1. **Full-layer run via the orchestrator:** `POST /api/cockpit/runs scope=layer/bodha` for `482012f1`.
   The orchestrator self-orders from `depends_on` (bo_laksana → fan-out → bo_upaya → bo_pramana_mapa).
   Confirm the whole layer builds from ONE run in DAG order (not asset-by-asset by hand).
2. **Cockpit/Atlas truth:** 8 `bo_` assets lit; each headline count = the **summed `count_sql`** over
   all that asset's tables (per handoff §4 — e.g. `bo_sangati` = cdlm_cells + domain_rollups +
   chart_summary + pattern_clusters + bodha_convergence, all `WHERE chart_id=$1`). Atlas shows real
   sample rows + astrological notes. Fix any NOT-MIGRATED/zero-count surface at its `count_sql`, not
   the UI ([[reference-cockpit-v1-v2-split]] — trace from the registry/route, the cockpit's the v2 tree).
3. **target_floors:** set each `bo_*` `target_floor` = the achieved summed count (floors aspirational).
4. **Retrieval tools for Bodha outputs (Wave-3 gate extension):** add ≥1 retrieval tool per new
   `bodha_*` table to the existing retrieval layer (`platform/src/lib/retrieval` +
   `python-sidecar/pipeline/retrieval`) and extend `tests/retrieval/coverage_gate.test.ts` so every
   `bodha_*` table is covered (the gate fails if one is orphaned). Do NOT build a parallel retrieval
   layer; no tier gating; weak tail retrievable (paginate, never LIMIT-drop).
5. **Promote + seal:** flip the 8 `bo_*` registry rows DRAFT→CURRENT (the same flip L1 had — only
   AFTER the build verifies). Reconcile the registry to the §14 map. Author/finalize
   `L2_BODHA_CLOSE_v1_0.md` with the validated state + the **L3 Kāla onboarding contract** (§4).
   Update `CURRENT_STATE_v1_0.md` §2 + append `SESSION_LOG.md` atomically at close.

**B5 acceptance:** layer builds from one orchestrator run in DAG order; FORENSIC 7/7 still passes; no
silent drops; cockpit/Atlas reflect true summed counts; Bodha retrieval tools + CI gate green;
`L2_BODHA_CLOSE` written; CURRENT_STATE + SESSION_LOG updated.

---

## §FINAL — Whole-arc acceptance
- [ ] **B1 (the spine):** bo_laksana is a FULL projection — constituent_facts_array resolves for every
      signal (zero unresolved); MSR signal count tracks the ga_structural fact count (parity, not a
      curated subset, not a predicate catalog); FORENSIC anchors inherit L1 values; weak tail present;
      idempotent. **Proven on bo_laksana ALONE before any fan-out.**
- [ ] **B2:** convergence + contradiction first-class ROWS; CGM graph built deepest (centrality / paths
      / final-dispositor); embeddings 1:1 (placeholder flagged); UCD read surface live.
- [ ] **B3/B4:** RM grounded to L0 corpus (every remedy cited); scorecard + standing Trap-1 audit.
- [ ] **B5:** one orchestrator run builds the layer in DAG order; cockpit/Atlas true; Bodha retrieval
      tools + CI gate; DRAFT→CURRENT; L2_BODHA_CLOSE sealed with L3 onboarding; CURRENT_STATE/SESSION_LOG.
- [ ] Ran continuously phase-by-phase — no human gate fired (dependency gates + Tier-3 rails only).
- [ ] Migration numbers fresh (no collisions); surgical apply + post-apply readback held.

## §OUT OF SCOPE (named so they aren't pulled in)
L3 Kāla / dasha-temporal activation (the time layer — when a relationship is active/dormant by period);
any `ga_structural` re-amendment (it is complete at 74,644 rows — do not re-open it); cross-chart
correlation (L5 Mīmāṃsā — never compute it in L2, it contaminates the deterministic base, Trap 2). Do
NOT reintroduce the predicate-firing model or G52 as a firing engine. Do NOT change the FROZEN
orchestrator contract.

---
*End of BODHA_B1_FULL_PROJECTION v1.0. The one delta from the prior Wave-4 brief: bo_laksana is a FULL
enumeration projection (native decision 2026-06-16), MSR count tracks ga_structural fact count, the
weak tail is kept, and the anti-drift spine is PROVEN on bo_laksana alone before B2 fans out. Then the
fan-out (convergence/contradiction first-class, graph deepest), bo_upaya grounded to L0, scorecard with
a standing Trap-1 audit, full orchestrator layer build, Bodha retrieval tools, and the L2 seal.*
