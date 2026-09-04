---
artifact: L3 W1 ANALYSIS — BATCH D
canonical_id: L3_W1_ANALYSIS_BATCH_D
version: "1.0"
status: DRAFT-FOR-W2
produced_on: 2026-09-05
campaign_id: nirmana-elevation
layer: L3
batch: D
assets: [ka_kshetra, ka_avadhi, ka_taranga, ka_yojaka]
theme: "The heavy data core — the field, the dossiers, the waveform, the predicates"
read_only: true
db_statements_issued: SELECT only
---

# L3 W1 ANALYSIS — BATCH D: the heavy data core

**Measurement discipline.** Every number below came from a command run in this session against
production (`q.sh`, `SELECT` only) or from reading source. Where a figure is a Postgres
`reltuples` planner estimate rather than a real count, it is labelled as such. Nothing is
inferred and stated as measured; inference is labelled INFER.

## Batch summary

1. **`ka_kshetra` is not chunk-parallelisable under the FROZEN contract, and this is a
   STOP-and-raise, not a tuning knob.** Substeps execute strictly serially on the single
   orchestrator-owned `ctx.db_conn` inside `SAVEPOINT writer_exec` → `RELEASE` → `conn.commit()`
   (`pipeline/orchestrator/asset_runner.py:716-736`). Parallel substeps need a second connection;
   a writer opening one violates "orchestrator owns the transaction + savepoint per substep"
   (CLAUDE.md §N.2). **What CAN be tuned instead is asset-level scheduler width + LPT ordering in
   `runner.py`** (which rides the §3.5 freeze exception as scheduling constants only) — and, far
   more valuable, the measured hot spot below.
2. **The measured hot spot is NOT stage 4.** Native chart `482012f1`, MEASURED from
   `build_substep_progress` deltas: total 22,685 s (6 h 18 m). `stage5dhara` = **15,415 s (68 %)**
   in 50 substeps for 1.87 M rows; `stage4` = 5,418 s (24 %) in 250 substeps for 8.60 M rows;
   `stage8` = 1,224 s for **6 rows nothing reads**. Registry `estimated_seconds = 237` is a **96×
   understatement**, and `asset_throughput.rows_per_second` is NULL with `measurement_count = 0`
   for all four assets — the measurement substrate that should have corrected it has never run.
3. **The layer's single biggest leverage defect: 8.60 M field rows the serving plane believes are
   not there.** `kala_field` = 8,599,775 rows (native) and `kala_field_windows` = 31,350 rows, but
   `platform-mcp/src/lib/kala_ritual_resonance.ts`'s `scoreTemporalIntensity()` is a
   **zero-argument function that unconditionally returns `state:'not_computed'`** with the reason
   string *"field empty — ka_kshetra has written no rows"*. `kala_views/ritual.ts:781` hardcodes the
   same claim. This is §N.8 inverted: a hardcoded negative signal with **no detector that could
   ever read true**.
4. **`ka_avadhi`'s headline output is 100 % empty and nothing notices.**
   `dossier->'lord_condition_fact_refs'` is `[]` on **1,169 / 1,169 rows (100.00 %)**. Root cause
   measured: the writer queries `chart_facts` with `fact_subject = 'Sun'` (title case) while L1
   stores `SUN` (upper case), and 5 of its 7 `fact_key` values (`dispositor`, `D9_sign`,
   `karaka_role`, `longitude`, `dignity_score`) **do not exist in `chart_facts` at all**. The
   asset's entire B.3 derivation-ledger function is silently void.
5. **`ka_taranga` verdict is a SPLIT, and the split is the honest answer** (§ below): the
   `scope_kind='domain'` half (43,488 rows/chart) is a genuine independent witness on an axis
   `kala_field` does not carry; the `scope_kind='event_class'` half (48,924 rows/chart, 53 %) is
   structurally incapable of informative disagreement — its dasha term has **1 distinct value
   across all 48,924 rows** (a tautology in the code), its transit term is scope-blind, and its
   promise term is time-invariant.
6. **`ka_yojaka` writes 50,104 predicates; its heaviest consumer loads ≤ 200.** `ka_sangam` ranks
   per `signature_class` with `_MAX_PREDICATES = 200`, then re-cuts to 200 total via
   `_select_top_predicates_with_class_quota` — **≈ 0.4 % reach the convergence engine.** Separately,
   9,347 predicates (18.7 %) carry no `constituent_lords` (structurally undatable) and only **20 of
   them (0.2 %)** carry the `always_on_reason` the design requires for an honest UNDATED.
7. **All 8 Kāla `__ssv_*` shadows are dead ŚUDDHA-VĀCA rollback snapshots (2026-07-28); 727 MiB
   reclaimable.** Zero application reads; `idx_scan` is NULL on every one (no indexes — plain CTAS
   heaps) and `seq_scan` is 4–12 (creation + the tested-rollback drill + audits). One weak
   reference exists and must be handled before any drop (§ dispositions).
8. **Registry health is uniformly NULL across the batch**: `integrity_check_sql`,
   `expected_volume_formula`, `expected_volume_inputs`, `service_health` all NULL; `target_floor`
   is 0 or NULL; `size_sql` present only on `ka_yojaka`; and `ka_yojaka` is mis-typed
   `asset_kind='artifact'` despite being a per-chart data writer with a chart-scoped `count_sql`.

---

## ka_kshetra

**One-line identity:** The Kāla field — a 9-stage hazard/intensity pipeline that materialises a
per-(event_class, time-segment) λ field with a null-model baseline, windows, salience, insights and
timeline specs.

**Temporal question (D-TIME):** *"Over the native's life, where does each event class's hazard
intensity λ concentrate — and is that concentration distinguishable from a null model?"*

### 1. Instrument fit
Serves **D-TIME** (it is the layer's only continuous-time intensity engine), **D-SALIENCE**
(stage 6 writes the five-axis salience vector consumed by `kala_priority_get`), **D-GROUNDING**
(`kala_field_provenance`, 2.14 M rows est., carries per-window fact provenance) and **D-SYNTHESIS**
(stage 6.5 insights). It is the right instrument — no other L3 asset produces a calibrated
intensity with a null baseline. **But its D-SERVICE fit is currently near-zero** (item 3) and
76.0 % of its windows carry `baseline_is_synthetic = true` (MEASURED, 31,350 native rows), so the
"distinguishable from null" half of its question is answered against a synthetic baseline three
times out of four.

### 2. Dependencies (declared vs real)
Registry `depends_on` (8): `ka_dasha_kala, ka_gochara_resonance, ga_panchanga, bo_pratijna,
bo_sangati, bo_upaya, bg_cohort, bg_class_lifetime_counts`.

Real reads, extracted from every `FROM` in `services/ka_kshetra/*.py` and mapped to producing
asset via `asset_registry.target_table`:

| Table read | Producer | Status |
|---|---|---|
| `gochara_resonance_map` | `ka_gochara_resonance` | declared ✓ |
| `chart_facts` (panchanga limbs, §N.5 reference) | `ga_panchanga` / `ga_chart_facts` | declared ✓ (via `ga_panchanga`) |
| `bodha_pratijna` | `bo_pratijna` | declared ✓ |
| `bg_synthetic_cohort` | `bg_cohort` | declared ✓ |
| `brahma_class_priors` | `bg_class_lifetime_counts` | declared ✓ |
| `kala_gochara_windows` | `ka_gochara_sweep` | **UNDECLARED in registry** (the shim docstring *does* declare it; the registry row is the one that is wrong) |
| `chart_dashas` | `ga_dashas` | **UNDECLARED** (registry names the L3 service `ka_dasha_kala`, not the L1 producer) |
| `bodha_msr_signals` | `bo_laksana` | **UNDECLARED** |
| `bodha_cgm_nodes`, `bodha_cgm_edges` | `bo_bimba` | **UNDECLARED** |
| `brahma_event_ontology` | `bg_ghatana` | **UNDECLARED** |
| `ephemeris_daily` | `bg_ephemeris` | **UNDECLARED** |
| `bg_transit_rules` | `bg_transit_rules` | **UNDECLARED** |
| `bg_kp_sublord_division` | (L0 reference) | **UNDECLARED** |
| **`phala_rectification`** | **`ph_rectification` (L4)** | **UNDECLARED — and a backward L3←L4 edge** (`services/ka_kshetra/uncertainty.py:186-191`, a live `SELECT ... FROM phala_rectification`, used to derive `sigma_T`) |

**Declared-but-unread:** `bo_sangati` (→ `bodha_cdlm_cells`) and `bo_upaya` (→ `bodha_rm_resonances`)
— VERIFIED absent: `grep -rn 'bodha_cdlm_cells\|bodha_rm_resonances' services/ka_kshetra/` returns
zero hits.

The `phala_rectification` edge is the serious one: it is a real read of an L4 table by an L3 writer,
undeclared in the DAG. The writer's own §7.5 acyclicity note explains at length why `mi_bhara` was
kept out to avoid a cycle; the same reasoning was never applied to `ph_rectification`.

### 3. Leverage / NULL check — **the batch's highest-value finding**
- `kala_field.refinement_residual` is **100.00 % NULL** (MEASURED, `TABLESAMPLE SYSTEM (1)`,
  n = 113,424); `refinement_exhausted` is **0.00 % true**; `refinement_depth` is 0 on 105,240 /
  113,589 sampled rows (92.7 %), 1 on 311, 2 on 38. Every other numeric column
  (`alpha`, `gamma`, `promise_term`, `clock_term_start`, `modifier_term_start`,
  `suppression_term_start`, `signed_obstruction_start`, `integral_days`) is 0.00 % NULL.
- **`kala_field` itself has ZERO serving-plane consumers.** The only production TS references are a
  test fixture list and a comment. A production test
  (`platform-mcp/src/__tests__/kala_ahead_get_period_echo_w3.test.ts:239`) actively **asserts** that
  *"no `kala_field` / `ka_kshetra` dispatch is ever made"*.
- **The serving plane's stated belief is factually false.**
  `platform-mcp/src/lib/kala_ritual_resonance.ts:485-498`:
  `export function scoreTemporalIntensity(): ScoredFactor { return { value: null, state:
  'not_computed', reason: TEMPORAL_INTENSITY_UNAVAILABLE_REASON, ... } }` — a **zero-argument
  function, no query, no branch**, whose reason string reads *"field empty — ka_kshetra has written
  no rows; see the N_e critical path"*. `kala_views/ritual.ts:779-784` emits the same claim via
  `notInCorpusCoverage('temporal_intensity_field_lambda', ...)`.
  MEASURED reality: `kala_field_windows` = 31,350 rows (native) / 7,650 (Abhinandan), spanning
  1984-02-10 → 2068-03-11, across 25 event classes.
- `ahead_autofile.ts`'s real `kala_field_windows` read exists but is gated behind
  `SM_GAMMA_C5_ENABLED` (`ahead_autofile.ts:478`), **default off**; no production setting for that
  flag exists anywhere in the repo (searched `*.ts|*.yaml|*.yml|*.tf|*.env*|*.json`).
- **`kala_timeline_spec` has zero production consumers of any kind** — 6 rows/chart, a 16 MB table,
  and `stage8` spent **1,224 s** (5.4 % of the whole build) producing them. Only Python test
  fixtures reference the table name.
- One genuine live consumer exists and works: `kala_priority_get`
  (`platform-mcp/src/tools/kala_views/priority.ts:108`) reads `kala_field_salience` (31,350 native
  rows) through the allowlisted DB proxy, with an honest-empty reason. `kala_insights` (431 native
  rows) is read by `kala_story_get`/`kala_ahead_get`. `kala_field_snapshots` and `kala_field_skill`
  are read by the envelope builder.

**Net:** of ~11.0 M rows across the `kala_field*` family, the surfaces actually reachable from the
serving plane are `kala_field_salience` (31,350), `kala_insights` (431), `kala_field_skill` (7),
`kala_field_snapshots`, and `kala_field_windows` only behind an off-by-default flag. The 8.60 M-row
`kala_field` base and the 2.14 M-row `kala_field_provenance` are unreachable.

### 4. Grounding tier
Correctly **`pratyaksa`** — instrument-emergent. The field is a computed hazard integral with a
Monte-Carlo/analytic null model; it makes no classical claim and should not. The one place a
`yukti` label would be honest is stage 6.5's insight synthesis (`kala_insights`), which composes
7 non-LEL insight types from computed field state — principle-derived narration over `pratyaksa`
substrate. **The 76.0 % `baseline_is_synthetic` rate must be surfaced on any served claim**: a
`pratyaksa` label over a synthetic baseline is a weaker claim than over an empirical one, and
nothing currently discloses the difference.

### 5. Temporal identity + arbitration
**Question:** *"Where is each event class's hazard intensity concentrated over life-time, relative
to a null model?"*

Overlapping engines (all answer some form of "when"):
- `ka_sangam` / `kala_convergence` — "when do multiple predicates converge?" (14,868 native rows)
- `ka_gochara_sweep` / `kala_gochara_windows` — "when does classical transit doctrine fire?"
- `ka_taranga` — "how activated is a domain/class this month?"
- `ka_dasha_kala` / `chart_dashas` — "which lord rules this instant?"
- `ka_bhavishya`, `ka_jivana_parva` — forward windows / life chapters

**Who arbitrates today: nobody.** There is no code path that reconciles a `kala_field` window with a
`kala_convergence` window or a `kala_gochara_windows` firing. Because `kala_field` is unreachable
from the serving plane, disagreements are structurally invisible — which is *why* the Temporal
Concordance Contract is the layer's headline deliverable. **Recommended arbitration rank for the
contract, from measured evidence:** `kala_field` is the only engine with a null-model p-value
(`null_p`, `null_r`, `robustness`, `confidence_tier`, all 0.00 % NULL on 31,350 rows) and therefore
the only one that can state a *calibrated* disagreement — it should be the arbiter of record for
event-class intensity, **conditioned on disclosing `baseline_is_synthetic`**.

### 6. Service
Density: none of the L3 capabilities in this batch declares `density_contract`. Drill-to-L1: the
field's provenance chain is `kala_field_windows.window_id → kala_field_provenance → chart_facts`
= 2 hops, so the drill is architecturally available — but no serving surface exercises it. `count_sql`
is chart-scoped and correct (`SELECT COUNT(*) FROM kala_field WHERE chart_id=$1`); `size_sql` is NULL.

### 7. Measured cost
**Build (MEASURED, `build_substep_progress` completed_at deltas):**

| Chart | Substeps recorded | Rows written | Wall clock |
|---|---|---|---|
| `482012f1` (native) | 308 | 10,502,780 | **22,685 s = 6 h 18 m** |
| `1c826d5a` (Abhinandan) | 123 | 2,818,814 | **16,210 s = 4 h 30 m** |

Native breakdown:

| Stage | Substeps | Rows | Total s | Avg s | Max s |
|---|---|---|---|---|---|
| `stage5dhara` | 50 | 1,871,218 | **15,415 (68 %)** | 308.3 | 488 |
| `stage4` | 250 | 8,599,775 | 5,418 (24 %) | 21.8 | 184 |
| `stage8` | 6 | 6 | 1,224 (5 %) | 204.0 | **1,210** |
| `stage6` | 1 | 31,350 | 468 | 468 | 468 |
| `stage65` | 1 | 431 | 160 | 160 | 160 |

`build_run_assets`: 67 `error`, 33 `queued`, 15 `complete`, 11 `aborted`; complete avg 1,025 s,
max 7,129 s; error max **121,757 s** (33.8 h). Registry `estimated_seconds = 237`.
`asset_throughput.rows_per_second` NULL, `measurement_count = 0`.

**Current state is INCOMPLETE, honestly.** `asset_throughput` for the native chart reads
`state='stale'`, `last_error =` *"orphan-watchdog: heartbeat went stale while a substep plan was in
flight. 301 substep(s) committed and 8599775 data row(s) are present, but this route cannot prove the
plan finished, so the asset was NOT promoted to 'lit'. Re-run the build to complete the plan (substep
progress is resumable)."* — this is the §N.8 no-op-completion predicate working exactly as designed.

**Serve cost:** unmeasured (no serving consumer exists to measure).

### The WP-4 heavy-pass profiling verdict

**(a) The 8.6 M vs 11.0 M gap is multi-chart, not growth.** MEASURED: `kala_field` holds
8,599,775 rows for `482012f1` + 2,412,882 for `1c826d5a` = **11,012,657** exact. The plan's "8.6 M"
is precisely the native chart's count. Separately, several campaign-facing figures are Postgres
`reltuples` planner estimates and are stale by 20–45 %: `pg_class` reports `kala_field` 10,669,603
(actual 11,012,657), `kala_taranga` 194,543 (actual 277,236), `kala_activation_predicates` 100,859
(actual 150,150). **Any tracker number sourced from `reltuples` should be re-derived from
`count(*)`.**

**(b) Chunk grain.** `plan_substeps(ctx)` (`services/ka_kshetra/writer.py:254-380`) emits, in
pipeline order: optional stage 0–3 plugin substeps (`stage0:{body}`, `stage1:run`, `stage2:run`,
`stage3:run` — note: **none of these appear in `build_substep_progress`**, so stages 0–3 either did
not run in the recorded builds or do not record progress; either way it is an unexplained gap);
then `stage4:{event_class}:{decade}` for `DECADES = 10` × 25 discovered event classes = **250
chunks**; then `stage5dhara:{event_class}:{1|2}` = **50 chunks** (analytic engine) or
`stage5:{ec}:{block}` × ⌈256/16⌉ + `stage5finalize:{ec}` (Monte-Carlo engine — 48 + 6 such rows
exist in the ledger from an earlier engine setting); then `stage6`, `stage65`,
`stage8:{view}` × 6 (`now, ahead, elect, story, priority, explain`), then `snapshot`.
**Chunk key = `(event_class, decade)` for stage 4; `(event_class, half)` for stage 5.**
Total plan for one chart ≈ 309 substeps.

**(c) Is chunk-parallelism possible under the FROZEN contract? — NO.**
`asset_runner.py:697-736` drives substeps in a plain `for` loop on **one** connection:
`SAVEPOINT writer_exec` → `writer.run_substep(ctx, step)` → `RELEASE SAVEPOINT writer_exec` →
`conn.commit()`. A psycopg connection serialises statements; two substeps cannot execute at once on
it. Parallelism therefore requires the writer to open connections of its own, which forfeits both
"orchestrator owns the transaction + savepoint per sub-step" and "writer never commits or closes
`ctx.db_conn`" (CLAUDE.md §N.2 / `ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md` §2). §3.5's
freeze-exception register does **not** list `writers/` or the `WriterBase` contract.
**→ STOP-and-raise territory. Do not attempt it in W3.**

**(d) What CAN be tuned, ranked by measured payoff:**
1. **Delete `stage8` work, or wire it.** 1,224 s (5.4 %) for 6 rows with zero consumers, one view
   costing 1,210 s alone. Highest ratio of cost to delivered value in the batch. *(This is a
   scheduling/scope decision, not a contract change.)*
2. **`stage5dhara` is the real long pole (15,415 s, 68 %) and is the only stage worth a chunking
   design.** Its 50 substeps are already at the finest grain the contract permits
   (`(event_class, half)`); `chunk:1` writes `kala_field_null`, `chunk:2` reads it back — a genuine
   serial dependency *within* a class, but the 25 classes are mutually independent. The only
   contract-legal lever is reducing per-substep work: `DEFAULT_REPLICATES = 1024`
   (`dhara_null.py:74`) at avg 308 s/substep is the dominant term. Halving replicates is a
   measurable, reversible experiment; parallelising is not available.
3. **Scheduler width / LPT ordering (`runner.py`, §3.5-permitted).** `_WORKER_LIMIT = 4`,
   `_MAX_CONCURRENT_RUNS = 6`, budget-bound by `_MAX_CONCURRENT_RUNS × (1 + _WORKER_LIMIT) ≤ ~33`
   against Cloud SQL `max_connections = 50`. Because `ka_kshetra` is a 6-hour serial pole,
   **longest-processing-time-first ordering matters more than width**: scheduling it first in the
   L3 wave lets every other Kāla asset overlap it. This is a scheduling-constant change only.
4. **`_WRITER_TIMEOUT_SECONDS = 600` is a live hazard for this asset.** MEASURED max substep is
   488 s (`stage5dhara`) and 1,210 s (`stage8:{view}`) — **the stage-8 substep already exceeds the
   per-writer timeout**, which is a plausible contributor to the 67 `error` rows and the
   orphan-watchdog stall. Raise it for L3, or shorten stage 8.

### 8. Findings

- **F-KSHETRA-1 — `scoreTemporalIntensity()` hardcodes "field empty" against 31,350 live rows.**
  `kala_ritual_resonance.ts:491-498` + `kala_views/ritual.ts:779-784`. A negative signal with no
  detector behind it (CLAUDE.md **§N.8**, the inverse of the Earned-Signal defect; **§N.7 item 4**).
  Serving-plane (TS) fix — lands in W3 without a freeze exception. **RECOMMEND: MUST.**
- **F-KSHETRA-2 — `kala_field` (8.60 M rows) has no serving consumer, and a production test asserts
  it never will be dispatched.** D-SERVICE. The campaign's biggest build is unreachable inventory.
  **RECOMMEND: MUST** (decide the surface, or route the asset `empty`/`retired` honestly — do not
  keep paying 6 h/chart for unreachable rows).
- **F-KSHETRA-3 — `estimated_seconds = 237` vs 22,685 s measured (96×), and
  `asset_throughput.rows_per_second` is NULL / `measurement_count = 0`.** C12; the scheduler cannot
  do LPT ordering on a 96×-wrong estimate. **RECOMMEND: MUST** (registry value is cheap and gates
  WP-4's own tuning).
- **F-KSHETRA-4 — undeclared `phala_rectification` (L4) read by an L3 writer.**
  `services/ka_kshetra/uncertainty.py:186-191`. A backward layer edge, invisible to the DAG, in an
  asset whose own docstring reasons carefully about acyclicity for `mi_bhara`. **RECOMMEND: MUST**
  (declare it and prove acyclicity, or remove the read).
- **F-KSHETRA-5 — 9 further undeclared upstream edges** (`kala_gochara_windows`, `chart_dashas`,
  `bodha_msr_signals`, `bodha_cgm_nodes/edges`, `brahma_event_ontology`, `ephemeris_daily`,
  `bg_transit_rules`, `bg_kp_sublord_division`) **and 2 declared-but-unread edges** (`bo_sangati`,
  `bo_upaya`). Rubric 2 / C12. **RECOMMEND: NOW.**
- **F-KSHETRA-6 — `stage8` costs 1,224 s to write 6 rows with zero consumers**, and its per-view
  substep (1,210 s) exceeds `_WRITER_TIMEOUT_SECONDS = 600`. **RECOMMEND: NOW.**
- **F-KSHETRA-7 — 76.0 % of `kala_field_windows` carry `baseline_is_synthetic = true` with no
  serving disclosure.** §N.6 (density signalling is data) / §N.7 item 5. **RECOMMEND: NOW.**
- **F-KSHETRA-8 — `refinement_residual` is 100 % NULL and `refinement_exhausted` 0 % true across a
  113k-row sample.** Either the refinement loop never engages (92.7 % depth 0) or the column is
  vestigial. A column that can only ever be NULL is an unimplemented check wearing a schema's
  clothes (§N.7 item 4). **RECOMMEND: NOW** (decide: populate or drop the claim).
- **F-KSHETRA-9 — stages 0–3 record no `build_substep_progress` rows**, so the §N.8 substep-plan
  completeness detector cannot see them; a build missing all of stages 0–3 would still satisfy the
  ledger for stages 4–8. **RECOMMEND: NOW.**
- **F-KSHETRA-10 — chunk-parallelism is contract-forbidden; do not attempt.** Logged so W2 does not
  re-open it. Alternatives are F-KSHETRA-6, replicate-count tuning, and `runner.py` LPT ordering.
  **RECOMMEND: NEVER-LATER** (reason: CLAUDE.md §N.2 freeze; would require a native-authorised
  contract change, which §3.5 does not grant).
- **F-KSHETRA-11 — `integrity_check_sql`, `expected_volume_formula`, `expected_volume_inputs`,
  `size_sql` all NULL; `target_floor = 0`.** C12/D-126.
  *Proposed real invariant (NOT a count pin):* per `(chart_id, event_class)` the stage-4 segments
  must **tile with no gaps or overlaps** —
  `SELECT count(*) FROM (SELECT chart_id, event_class, t_end, lead(t_start) OVER (PARTITION BY
  chart_id, event_class ORDER BY t_start) nxt FROM kala_field WHERE chart_id=$1) z WHERE nxt IS NOT
  NULL AND nxt <> t_end` **must equal 0**; plus every `kala_field_windows.field_snapshot_id` must
  equal the chart's newest `kala_field_snapshots` row (single-snapshot consistency).
  *Proposed volume formula:* `rows ≈ n_event_classes × DECADES × segments_per_decade`, inputs
  `{n_event_classes: count(distinct event_class) in kala_field_routes, DECADES: 10,
  horizon_days: HORIZON_DAYS}`; measured native = 25 × 10 × ~34,399 = 8,599,775.
  *Proposed floor (§N.4, achieved-count):* 8,599,775 for a completed native build.
  **RECOMMEND: NOW.**

**Route recommendation (W2 input):** `changed` — the asset is measurably INCOMPLETE on the canonical
chart (orphan-watchdog stall, correctly un-promoted), it carries a MUST-class undeclared L4 edge, and
its output is unreachable from the serving plane. It needs code + registry changes before any rebuild
is worth 6 hours. *(If W2 rules the serving surface out of scope, the honest alternative route is
`empty` with a logged reason — never `rebuild_only`, which would spend 6 h/chart to refill an
unreachable table.)*

---

## ka_avadhi

**One-line identity:** Per-dasha-period dossiers — one row per (system, level, period) carrying L1
fact references for the period lord, the pratijna the period activates, and sub-lord modulation.

**Temporal question (D-TIME):** *"For a given dasha period, who is its lord, what does that lord's
natal condition say, and which promises does that period put on the table?"*

### 1. Instrument fit
Serves **D-GROUNDING** (its stated purpose is `lord_condition_fact_refs` — *refs only, never
restated values*, an explicit §N.5 guard) and **D-TIME** (period spine). It is the right instrument
in principle. In practice its grounding function is **100 % void** (item 3), which reduces it to a
period index — a job `chart_dashas` already does.

### 2. Dependencies (declared vs real)
Registry `depends_on`: `ga_dashas, bo_pratijna, bg_ghatana`. Real reads: `chart_dashas`
(→ `ga_dashas` ✓), `bodha_pratijna` (→ `bo_pratijna` ✓), `brahma_event_ontology` (→ `bg_ghatana` ✓),
**`chart_facts` (→ `ga_chart_facts` — UNDECLARED)**. The writer's own module docstring still claims
*"DAG: ka_yojaka → ka_avadhi"*, which contradicts the registry (no `ka_yojaka` edge) and is not
supported by the SQL — a stale docstring.

### 3. Leverage / NULL check
- **`dossier->'lord_condition_fact_refs'` = `[]` on 1,169 / 1,169 native rows = 100.00 %.**
- **`dossier->'activated_pratijna_ids'` = `[]` on 41.49 %.**
- `dossier->'sublord_modulation'` NULL on 10.78 % (expected — MD rows have no sub-lord; MD rows are
  126/1,169 = 10.8 %, so this one is correct by construction).
- **Root cause, MEASURED.** `_FETCH_FACT_REFS_SQL` filters
  `fact_subject = %s AND fact_key IN ('sign','nakshatra','dispositor','D9_sign','karaka_role',
  'longitude','dignity_score')` with `%s` = `'Sun'`/`'Moon'`/… (title case, from `_GRAHA_DOMAINS`).
  Live `chart_facts` for the native chart stores `fact_subject` as **`SUN`, `MOON`, `SATURN`**
  (upper case). Independently, restricting only on those 7 `fact_key` values across the whole
  canonical chart returns **just two keys**: `sign` (316 rows) and `nakshatra` (139) — the other
  five (`dispositor`, `D9_sign`, `karaka_role`, `longitude`, `dignity_score`) **do not exist in
  `chart_facts`**. The real vocabulary for `SUN` includes `sign, sign_lord, nakshatra,
  nakshatra_lord, navamsa_sign, effective_dignity_score, longitude_sidereal, is_debilitated, …`.
  So the query fails on both axes at once.
- **Consumer impact.** `query_dasha_dossier` (`platform/src/lib/retrieval/registry/layers/L3_kala/
  query_dasha_dossier.ts:93`) serves `dossier` directly, and `platform-mcp/src/tools/retrieval/
  kala_temporal.ts` cites `kala_avadhi` as the source of `timeline_excerpt`. **A caller reading a
  dossier today receives an empty grounding array with no flag that it is empty.** That is exactly
  the B.3 derivation-ledger mandate failing silently.
- `chara` is listed in `_DASHA_SYSTEMS` (7 systems) but **`chart_dashas` holds zero `chara` rows for
  the canonical chart at any ayanamsha** — so 6 systems produce. The writer's `notes` field
  nonetheless reports `systems=7`.

### 4. Grounding tier
The dossier's *refs* are pure `pratyaksa` pointers into L1 — correct, and correctly refusing to
restate values. `quality->'domains'` (the `_GRAHA_DOMAINS` table: Sun→dharma/career/authority/health,
etc.) is **`yukti`** — classical natural-signification doctrine encoded as a Python dict with **no
citation and no source table**. `citations` is a hardcoded single-element array
`['BPHS ch. Vimshottari-Dasha / Classical dasha lord tables']` on every row — a chapter-less,
verse-less string that cannot be resolved. That is not a `sruti` claim; it should either resolve to
`classical_text_chunks` or be honestly demoted to `yukti` with the mapping table named.

### 5. Temporal identity + arbitration
**Question:** *"Which dasha period am I in, under which system, and what does its lord bring?"*
Overlapping engines: `ka_dasha_kala`/`chart_dashas` (the same spine, one layer down — `ka_avadhi`
adds only dossier decoration), `ka_taranga` (same lord→domain mapping, monthly grain),
`ka_yojaka` (predicates keyed to dasha lords), `ka_jivana_parva` (life chapters over the same spine).
**Arbiter: `ga_dashas`/`chart_dashas` is unambiguously authoritative** — `ka_avadhi` inherits period
boundaries verbatim and does not recompute them (a genuine §N.5 win). The CR-110 fix in the header
(pinning `_CANONICAL_AYANAMSHA = 'lahiri_chitrapaksha'` on both fetches) is the record of what
happens when that inheritance is not pinned: two Mercury MD rows with different end dates in one
served spine.
**Note the identity collision with `ka_taranga`:** both hardcode a `_GRAHA_DOMAINS` lord→domain
table. `ka_taranga` imports it from `services/taranga_kernel/kernel.py`; `ka_avadhi` defines its own
private copy at `writers/ka_avadhi.py:38-48`. Two copies of one doctrine table that can drift —
§N.7 item 3.

### 6. Service
Real consumer: `query_dasha_dossier` capability → `kala_timeline` MCP tool family. `count_sql`
chart-scoped and correct. No `density_contract`, no `empty_reason`. Drill to L1: **intended in ≤1
hop via `lord_condition_fact_refs`, actually impossible — the array is always empty.**

### 7. Measured cost
`estimated_seconds = 14`. MEASURED `build_run_assets`: 43 `complete`, avg **14 s**, max 61 s — the
registry estimate is accurate here. 16 `error` (avg 499 s, max 900 s), 27 `queued`, 9 `aborted`.
Rows: 1,169 native / 1,160 Abhinandan / 1,291 `cb73cd3d`. `asset_throughput` native = `stale`.
Serve cost: unmeasured.

### 8. Findings
- **F-AVADHI-1 — `lord_condition_fact_refs` is `[]` on 100.00 % of rows** because of a
  `fact_subject` case mismatch (`'Sun'` vs `SUN`) compounded by 5 of 7 `fact_key` values not
  existing in `chart_facts`. The asset's entire B.3 grounding function is void and is served as an
  empty array with no flag. **B.3 / §N.5 / §N.7 item 2.** Fix is one SQL literal set plus
  `graha.upper()`. **RECOMMEND: MUST.**
- **F-AVADHI-2 — no detector exists for F-AVADHI-1.** The writer logs
  `"%d period dossier rows"` and returns success with every dossier hollow. §N.8: a status with no
  detector behind the claim. A post-write assertion (`≥1 fact ref on ≥90 % of rows, else fail`) is
  the fix. **RECOMMEND: MUST.**
- **F-AVADHI-3 — `citations` is an unresolvable hardcoded string on 100 % of rows.** B.3 forbids
  "as is known classically" without a source; a chapter-less BPHS string is that. **RECOMMEND: NOW.**
- **F-AVADHI-4 — `_GRAHA_DOMAINS` is duplicated between `ka_avadhi` and `taranga_kernel`.**
  §N.7 item 3 (no wrapper-local constant may shadow a shared source). **RECOMMEND: NOW.**
- **F-AVADHI-5 — `chara` declared in `_DASHA_SYSTEMS`, zero rows exist; `notes` reports
  `systems=7`.** An honest count would be 6. §N.7 item 6. **RECOMMEND: NOW.**
- **F-AVADHI-6 — undeclared `chart_facts` edge; stale docstring claiming `ka_yojaka → ka_avadhi`.**
  **RECOMMEND: NOW.**
- **F-AVADHI-7 — registry NULLs.** *Proposed integrity invariant (not a count pin):* within each
  `(chart_id, system_id, level_n)`, periods must be **contiguous and non-overlapping** —
  `SELECT count(*) FROM (SELECT period_end, lead(period_start) OVER (PARTITION BY chart_id,
  system_id, level_n ORDER BY period_start) nxt FROM kala_avadhi WHERE chart_id=$1) z
  WHERE nxt IS NOT NULL AND nxt <> period_end + 1` = 0; **plus** every `period_start` must exist in
  `chart_dashas` for the same `(system_id, level_n, lahiri_chitrapaksha)` — the §N.5 inheritance
  invariant, which would have caught CR-110 automatically.
  *Proposed volume formula:* `rows = Σ_systems (MD_count + AD_count)` from `chart_dashas` at
  `level_n ∈ {1,2}`, `ayanamsha_id='lahiri_chitrapaksha'`. *Floor (§N.4):* 1,169 achieved.
  **RECOMMEND: NOW.**

**Route recommendation (W2 input):** `changed` — cheap asset (14 s), one MUST-class correctness
defect with a small, well-understood fix, and a rebuild is nearly free once the fix lands.

---

## ka_taranga

**One-line identity:** A monthly activation waveform, 1950-01 → 2100-12, per scope
(24 domains + 27 event classes = 51 scopes × 1,812 months = 92,412 rows/chart), computed as a
harmonic mean of a dasha term, a transit term and a promise term.

**Temporal question (D-TIME):** *"In month M, how activated is domain (or event class) S — as a
convolution of who rules, what is transiting, and what was promised?"*

### 1. Instrument fit
Nominally D-TIME + D-SYNTHESIS. It is the only L3 asset offering a **domain**-keyed temporal
series — every other engine keys on event class, house, graha or window. That axis is its real
contribution. The event-class half duplicates `kala_field`'s axis at lower resolution (item 5).

### 2. Dependencies (declared vs real)
Registry `depends_on`: `ka_avadhi, bo_pratijna, ka_sangam, ga_dashas, bg_ghatana`.
Real reads (every `FROM` in the writer): `chart_dashas` (→ `ga_dashas` ✓), `kala_convergence`
(→ `ka_sangam` ✓), `bodha_pratijna` (→ `bo_pratijna` ✓), `brahma_event_ontology` (→ `bg_ghatana` ✓),
`kala_taranga` (its own).
**`ka_avadhi` is DECLARED BUT UNREAD** — VERIFIED: no `kala_avadhi` reference anywhere in
`writers/ka_taranga.py` or `services/taranga_kernel/`. This is a phantom DAG edge that serialises
`ka_taranga` behind `ka_avadhi` for no reason.

### 3. Leverage / NULL check
No NULL columns. The defect here is **degeneracy**, not nullity (MEASURED, native chart):

| scope_kind | rows | scopes | distinct `activation` | distinct `dasha_contribution` | distinct `transit_contribution` | distinct `promise_contribution` |
|---|---|---|---|---|---|---|
| `domain` | 43,488 | 24 | 994 | **2** | 708 | 14 |
| `event_class` | 48,924 | 27 | 264 | **1** | **11** | 24 |

- The **`event_class` dasha term has exactly one distinct value across 48,924 rows.** This is a
  code tautology, not a data artefact: `writers/ka_taranga.py` computes
  `d_contrib = 1.0 if lord and any(d in lord_domains for d in _GRAHA_DOMAINS.get(lord, [])) else 0.1`
  where two lines earlier `lord_domains = set(_GRAHA_DOMAINS.get(lord, []))`. The `any(...)` is
  therefore **always true whenever `lord` is not None**. The term can never discriminate.
- The **`event_class` transit term is scope-blind**: `t_vals = [s for d_vals in
  transit_this_month.values() for s in d_vals]; t_contrib = max(t_vals)` — the max over *all*
  domains, identical for every event class in that month. 11 distinct values over 1,812 months.
- The **promise term is time-invariant** for both halves (`pratijna_domain` / `pratijna_ec` are
  computed once, outside the month loop).
- **Consequence:** for `scope_kind='event_class'`, activation(M, S) = f(global_transit_max(M),
  const(S)) with a constant dasha term — the ranking of event classes is **fixed for all 1,812
  months**. It cannot express a claim of the form "class A is hotter than class B in 2027".
- **22.6 % of rows (20,910 native) are for months BEFORE the native's birth** (1950-01 …
  1984-01), and 20,043 are beyond `kala_field_windows`' 2068-03-11 horizon. A served pre-birth
  activation value is a correctness hazard, not just waste.

### 4. Grounding tier
`pratyaksa` for the arithmetic; **`yukti`** for the lord→domain mapping (`_GRAHA_DOMAINS`, the same
uncited classical table as `ka_avadhi`). `formula_version = 'ka_taranga_v1.0'` is carried on every
row, which is good practice. **The `event_class` half should not carry any tier label at all** while
its dasha term is a tautology — an honest `pratyaksa` over a degenerate formula is still a
misleading number.

### 5. Temporal identity + arbitration
**Question:** *"How activated is scope S in month M?"* Overlapping engines: `kala_field`
(event-class λ, finer grain, with a null model), `kala_convergence`/`ka_sangam` (its own input —
so it cannot arbitrate against it), `chart_dashas` (its own input), `kala_gochara_windows`.
**Arbiter:** for the `event_class` axis, `kala_field` should win outright — it has `null_p`,
`robustness` and `confidence_tier`; `ka_taranga` has none of those and one of its three inputs is
constant. For the `domain` axis there is **no competing engine**, so `ka_taranga` is the arbiter of
record by default, and the concordance contract should say so explicitly.

### 6. Service
One real consumer: the `query_activation_waveform` capability
(`platform/src/lib/retrieval/registry/layers/L3_kala/query_activation_waveform.ts`, exposed as
`kala_activation_waveform_get` via `tool_name_bridge.ts:591`, present in
`mcp_surface_profiles.generated.ts`). **No `density_contract`, no `empty_reason`.** It is *not*
shelf inventory but it is thinly consumed: the VIDHI primitive named `taranga_curve`
(`registry_data.ts:215-224`, used in the wealth/career/health/marriage/education recipes) resolves
to `live_tool: 'kala_bundle_get'` and **does not read `kala_taranga` at all** — the name is
inherited, the wiring is not. Every VIDHI use is `domain`-scoped; **nothing anywhere consumes the
`event_class` half.**

### 7. Measured cost
`estimated_seconds = 23`. MEASURED `build_run_assets`: 43 `complete`, avg **27 s**, max 83 s —
registry estimate accurate. 30 `error` (avg 1,902 s, max 2,463 s), 25 `queued`, 11 `aborted`.
Rows: exactly **92,412 per chart on all three charts** (identical — the scope set does not vary by
chart). Live table 277,236 rows / 186 MB (`reltuples` reports 194,543 — stale by 30 %).
Serve cost: unmeasured.

### The `ka_taranga` DECISION (plan §5 L3(b)) — **derived view vs independent witness**

**VERDICT: neither wholly — it is a SPLIT, and the two halves must be dispositioned separately.**

**It is NOT a derived view of `kala_field`.** VERIFIED by reading every `FROM` in the writer and the
kernel: `ka_taranga` never touches `kala_field` or any `kala_field_*` table. Its substrate is
`chart_dashas` + `kala_convergence` + `bodha_pratijna` — three sources the field also uses but
combines differently (the field integrates a hazard over continuous time with a null model; taranga
takes a harmonic mean over a calendar month). Retiring it "as a view" is therefore **not available**:
there is no SQL over `kala_field` that reproduces it.

**Half A — `scope_kind='domain'` (43,488 rows/chart, 47 %): KEEP as an independent witness.**
- It is the *only* engine in Kāla keyed on **domain**. `kala_field` covers 25 event classes and no
  domains; MEASURED, all 25 field event classes are a strict subset of taranga's 27 event-class
  scopes, but the 24 domain scopes have **no counterpart anywhere**.
- Its three terms are genuinely time-varying and scope-specific on this axis: 2 distinct dasha
  values (the real 1.0/0.15 in-domain test), **708** distinct transit values, 994 distinct
  activations.
- It is the axis every actual consumer uses (all five VIDHI recipes pass `domain`).
- Its disagreement with the field **is** informative: field λ is event-class-keyed and
  transit-driven; taranga-domain is dasha-driven. A month where the dasha lord owns a domain but no
  transit converges is exactly the case the two engines should split on, and the concordance
  contract should capture that as a first-class arbitration case.

**Half B — `scope_kind='event_class'` (48,924 rows/chart, 53 %): RETIRE or REPAIR — it cannot be an
informative witness in its current form.**
- Same axis as `kala_field` (25/25 overlap), coarser grain, no null model.
- Its dasha term is a **proven tautology** (1 distinct value / 48,924 rows, from an `any()` over the
  set it was derived from).
- Its transit term is **scope-blind** (a global monthly max, 11 distinct values).
- Its promise term is **time-invariant**.
- Therefore the *only* time-varying input is a scope-independent scalar: the event-class ordering is
  frozen for all 151 years. **A witness that cannot vary its ranking cannot informatively disagree
  with anything.**

**What would falsify this verdict** (stated per the brief's requirement):
1. *Half B is fine after all* — if `components->>'dasha_contribution'` were shown to take ≥2
   distinct values for `scope_kind='event_class'` on any chart. **Measured: 1, on the canonical
   chart.** Re-run on `1c826d5a` and `cb73cd3d` before W2 commits.
2. *Half B carries scope-specific transit information* — if `distinct transit_contribution` for
   event-class rows were of the same order as the 708 seen for domain rows.
   **Measured: 11.**
3. *`kala_field` does not in fact cover taranga's event classes* — if the intersection of
   `kala_field.event_class` and taranga's event-class `scope_id` were < 25.
   **Measured: 25 of 25** (`career_change` and `birth_anchor` are taranga-only).
4. *Half A is redundant too* — if any engine were found producing a domain-keyed temporal series.
   None found; searched all `kala_*` tables.
5. *The monthly table is needed because nothing can compute it on demand* — **this one is already
   falsified.** `services/taranga_service.py` is a live service (`routers/taranga.py`, endpoints
   `/activation`, `/curve`, `/record_evidence`) that computes activation at **arbitrary `t`** from
   the ephemeris + chart substrate, sharing the identical formula primitives via
   `services/taranga_kernel/kernel.py`, and its own docstring states the table's header anticipated
   exactly this ("*Fine grain (daily/hourly) = SERVICE computation, never stored here… this service
   IS that fine-grain service*"). **The batch table is a precomputed monthly cache of a function
   that is already callable live.** That materially weakens the case for materialising 92,412
   rows/chart — most of all the 22.6 % that precede the native's birth.

**Recommended disposition for W2:** keep Half A, declare it in the Temporal Concordance Contract as
the domain-axis arbiter, and **retire Half B** (or repair both degeneracies first and re-measure —
but repair means a real per-event-class transit term, which is what `kala_field` already computes,
so retirement is the cheaper honest answer). Additionally clamp the waveform's start to the birth
date. Half B + pre-birth rows together are ≈ 63,000 of 92,412 rows per chart.

### 8. Findings
- **F-TARANGA-1 — DECISION delivered: SPLIT.** `scope_kind='domain'` = independent witness (keep,
  it is the only domain-keyed temporal engine); `scope_kind='event_class'` = degenerate duplicate of
  `kala_field`'s axis (retire or repair). Not a derived view of the field under any reading —
  it never reads it. **Doctrine: D-TIME (Temporal Concordance Contract), plan §5 L3(b).**
  **RECOMMEND: MUST** (this is a named layer deliverable and must be logged either way).
- **F-TARANGA-2 — the `event_class` dasha term is a code tautology.**
  `d_contrib = 1.0 if lord and any(d in lord_domains for d in _GRAHA_DOMAINS.get(lord, []))` where
  `lord_domains` *is* that set. 1 distinct value / 48,924 rows. §N.7 item 6 (a value chosen for how
  it reads rather than for what it measures) + §N.8. **RECOMMEND: MUST.**
- **F-TARANGA-3 — 22.6 % of rows (20,910/chart) are pre-birth months.** A served activation value
  for 1970 on a 1984 native is a correctness hazard, and `query_activation_waveform` applies no
  birth-date floor. **RECOMMEND: MUST.**
- **F-TARANGA-4 — `ka_avadhi` is a declared-but-unread DAG edge**, serialising this asset behind an
  upstream it never reads. Rubric 2 / C12. **RECOMMEND: NOW.**
- **F-TARANGA-5 — two writers share one table with different semantics.** `ka_taranga` (batch,
  delete-then-insert per chart) and `taranga_service.record_evidence()` (on-demand upsert with
  `cited_by`) both write `kala_taranga`. A batch rebuild **silently destroys** every cited-evidence
  row the service persisted, and nothing warns. §N.3 (delete-then-insert scoped to chart) collides
  with an evidence-retention contract. **RECOMMEND: MUST.**
- **F-TARANGA-6 — `query_activation_waveform` declares no `density_contract` and no
  `empty_reason`,** and serves the degenerate event-class rows undifferentiated from the
  informative domain rows. §N.6 items 1 and 4. **RECOMMEND: NOW.**
- **F-TARANGA-7 — `taranga_curve` VIDHI primitive is named for this asset but wired to
  `kala_bundle_get`,** which does not read `kala_taranga`. A misleading name across 5 reading
  recipes. **RECOMMEND: NEVER-LATER** (cosmetic; log it so the concordance contract does not treat
  the primitive as evidence of consumption).
- **F-TARANGA-8 — registry NULLs.** *Proposed integrity invariant:* the grid must be **complete and
  distinct** — for each chart, `count(*) = count(distinct (month, scope_kind, scope_id))` **and**
  every `(month, scope_kind, scope_id)` in the Cartesian product of
  `[min(month)…max(month)] × scopes` must be present (a tiling check, not a count pin); plus
  `activation BETWEEN 0 AND 1` on every row. *Proposed volume formula:*
  `rows = months × (n_domains + n_event_classes)` with inputs
  `{months: 1812 (1950-01…2100-12, or birth→horizon after F-TARANGA-3),
  n_domains: |distinct domains in _GRAHA_DOMAINS ∪ bodha_pratijna|,
  n_event_classes: |distinct event_class_id in bodha_pratijna|}`; measured native = 1,812 × 51 =
  92,412 exactly. *Floor (§N.4):* 92,412. **RECOMMEND: NOW.**

**Route recommendation (W2 input):** `changed` — the SPLIT decision is a required deliverable and
carries three MUST-class fixes (tautology, pre-birth rows, two-writer collision) that all touch the
writer. Cheap to rebuild afterwards (27 s measured).

---

## ka_yojaka

**One-line identity:** The activation-predicate bridge — one predicate row per L2 MSR signal,
declaring *what would have to be true in time* (dasha eligibility, transit trigger,
strength/affliction hook) for that signal to fire.

**Temporal question (D-TIME):** *"Under what temporal conditions would this natal signal actually
activate?"* — the layer's arbitration **substrate**: it does not answer *when*, it declares *what
counts as when*.

### 1. Instrument fit
This is the D-TIME arbitration substrate, correctly identified. It is the join point between L2's
static signal inventory and L3's temporal engines: `ka_sangam`, `ka_vighnakara`, `ka_kalasutra`,
`ka_jivana_parva` and **`ph_nimitta` (L4)** all read it. It is the right instrument, and it is the
most consumed asset in this batch. Its weakness is volume-vs-reach (item 3), not fit.

### 2. Dependencies (declared vs real)
Registry `depends_on`: `bo_laksana, bg_transit_rules, ga_dashas, bo_bimba, bo_sangati, bo_pratijna,
bg_ghatana`. Real reads (writer + `services/ka_yojaka/`): `bodha_msr_signals` (→ `bo_laksana` ✓),
`bodha_pratijna` (→ `bo_pratijna` ✓), `brahma_event_ontology` (→ `bg_ghatana` ✓), `bodha_cdlm_cells`
(→ `bo_sangati` ✓), `bodha_cgm_nodes` (→ `bo_bimba` ✓), plus **`chart_facts` (→ `ga_chart_facts`,
UNDECLARED)** and **`ga_yoga_firings` (→ `ga_yoga`, UNDECLARED)**.
**Declared but unread:** `bg_transit_rules` and `ga_dashas` — VERIFIED absent from every `FROM`.
This is notable because the transit-trigger templates the writer emits (`kendra`, `trikona`,
`orb_deg: 1.0`, `trigger_events`) look like `bg_transit_rules` content but are **Python literals in
the writer**, not read from the declared table. §N.7 item 3 (a wrapper-local constant shadowing a
source that is right there and declared).

### 3. Leverage / NULL check
- **50,104 predicates written for the native chart; ≤ 200 ever reach the convergence engine.**
  `ka_sangam` (`writers/ka_sangam.py:275-304`) selects `ROW_NUMBER() OVER (PARTITION BY
  signature_class ORDER BY raw_dignity_score DESC NULLS LAST, content_hash) <= _MAX_PREDICATES`
  with `_MAX_PREDICATES = 200`, then re-cuts the union to 200 total via
  `_select_top_predicates_with_class_quota` (line 388) and to 60 for the lifetime tier. That is
  **≈ 0.4 % of the asset's output**. The comment at `ka_sangam.py:150` records the reason: SUBSYSTEM
  is ~85 % of the table and was winning every slot (MEASURED here: 42,295/50,104 = 84.4 % — the
  comment is accurate).
- **9,347 predicates (18.66 %) carry no `constituent_lords` and are therefore structurally
  UNDATABLE; only 20 (0.21 %) carry the `always_on_reason` the CR-37 design requires.** MEASURED
  breakdown of undated rows: SUBSYSTEM 8,586 (0 with reason), DISPOSITOR_RELATIONAL 379 (0),
  DIGNITY 256 (0), DOSHA 56 (0), YOGA 55 (**20 with reason** — the distribution-yoga case the design
  actually implemented), CLASSIFY_RESIDUAL 15 (0). The honest-UNDATED discipline was implemented for
  YOGA only and never generalised.
- **`transit_trigger_jsonb->>'type'` has exactly 1 distinct value per `signature_class`** (MEASURED,
  all six classes). The transit trigger is a per-class template, not a per-signal computation. Not
  wrong, but it means `transit_trigger_jsonb` carries ~0 bits of per-row information across 220 MB.
- The CR-5/CR-12/CR-48 repair held: `strength_affliction_hook_jsonb->>'non_affliction'` now has 22
  distinct values (SUBSYSTEM/DISPOSITOR/DIGNITY) rather than the old flat 0.5. `dignity_score` has
  3 distinct values, which is thin but real.
- `cgm_centrality_weight` and `cdlm_domain_strength` are present on 100 % of rows (50,104/50,104)
  but are near-constant: 10 and 3 distinct values respectively for SUBSYSTEM, **1 and 1** for YOGA.
  The D6 enrichment is populated but barely discriminating.
- **Registry volume claim is stale and contradicted by the data**: `volume_explanation` says
  *"total ≈ 66,738 for native chart"*; MEASURED 50,104. The same 66,738 figure is repeated in
  `query_temporal_activation.ts:6`. Two surfaces restating a number that has drifted (§N.7 item 3).

### 4. Grounding tier
Mixed, and the mix is honest. The **derivation** (`derivation_ledger_jsonb`, `constituent_lords`
traced to `ga_yoga_firings.constituent_planets` or `graha_position` facts) is `pratyaksa` — every
emitted lord traces to a real L1 row, which the CR-37 header claims and the data supports. The
**trigger templates** (`benefic_transit_to_kendra_trikona`, kendra `[1,4,7,10]`, trikona `[1,5,9]`,
`orb_deg: 1.0`) are **`yukti`** — classical doctrine, and they are exactly the content
`bg_transit_rules` exists to hold with citations. Moving them out of Python literals into the
declared, citable table would upgrade them from uncited `yukti` toward `sruti`. Nothing here should
be labelled `sruti` today.

### 5. Temporal identity + arbitration
**Question:** *"What temporal conditions must hold for this natal signal to activate?"*
It is the **only** asset in Kāla that answers a *conditional* rather than a *positional* temporal
question, which makes it the natural substrate of the Temporal Concordance Contract: every other
engine can be expressed as an evaluator of these predicates.

**Overlaps, named precisely (as the task requires):**
| Overlap | Where | Nature |
|---|---|---|
| **vs dasha timing** | `dasha_eligibility_rule_jsonb.match = "MD_or_AD_lord IN constituent_lords OR dispositors OR house_lords"` vs `chart_dashas` | The predicate *declares* the rule; `ka_sangam`'s `KaDashaKalaService` *evaluates* it. No conflict in principle — but the predicate names no ayanamsha-pinning rule, while `ka_avadhi` had to add one (CR-110). **Same latent double-spine hazard, unaddressed here.** |
| **vs gochara windows** | `transit_trigger_jsonb.trigger_events` (`constituent_lord_ingress_kendra_trikona`, `benefic_transit_conjoin_yoga_lord`, `constituent_lord_return`) vs `kala_gochara_windows` (`ka_gochara_sweep`, the protected v1 corpus) and `bg_transit_rules` | **Direct overlap.** Both express "which transit matters". `ka_yojaka` hardcodes its version in Python; `bg_transit_rules` is the declared-but-unread table holding the citable version; `kala_gochara_windows` holds the materialised firings. **Three representations of one doctrine, with no arbiter and no cross-check.** This is the single most important entry for the Temporal Concordance Contract. |
| **vs convergence** | `ka_sangam` reads predicates → writes `kala_convergence`; `ka_taranga` reads `kala_convergence` | A clean producer→consumer chain, not a conflict — but it means a predicate dropped by the 200-row cut is invisible to *everything* downstream, including `ka_taranga` and `ph_nimitta`. |
| **vs L4** | `ph_nimitta.py:412,450` reads `dasha_eligibility_rule_jsonb->>'multi_system_confirmation_count'` | A cross-layer read of an L3 predicate field; correct direction (L4 reads L3), declared? — outside this batch's write-set, flagged as a **hand-off**. |

**Arbiter recommendation:** `ka_yojaka` should be the *declarer*, `bg_transit_rules` the *doctrine of
record* for trigger content, and `ka_gochara_sweep`'s v1 corpus the *evidence of firing*. Today
`ka_yojaka` silently plays all three roles for its own rows.

### 6. Service
Consumers are real and numerous: `ka_sangam`, `ka_vighnakara` (`:414`), `ka_kalasutra` (`:45`),
`ka_jivana_parva` (`:111`), `ph_nimitta` (L4), plus serving surfaces `query_temporal_activation`
(`platform/src/lib/retrieval/registry/layers/L3_kala/query_temporal_activation.ts:270`),
`register_d8_assess_domain.ts:1458`, and citation strings in `kala_now_get` / `kala_ahead_get`.
`query_temporal_activation` **does** emit `empty_reason` (three branches) — the best of the four
assets — but **declares no `density_contract`**, and it does not distinguish datable from undatable
predicates (§N.6 item 1: the caller cannot tell a firing-capable predicate from a structurally
undatable one). Drill to L1: `signal_id → bodha_msr_signals.constituent_facts_array → chart_facts`
= 2 hops ✓.

### 7. Measured cost
`estimated_seconds = 36`. MEASURED `build_run_assets`: 51 `complete`, avg **40 s**, max 111 s —
registry accurate. 15 `error` (avg 0 s — instant BLOCKED), 27 `queued`, 11 `aborted`.
Rows: 50,104 native / 50,171 Abhinandan / 49,875 `cb73cd3d` = 150,150 total (live table 220 MB;
`reltuples` reports 100,859 — stale by 33 %). `asset_throughput` native = `stale`.
Serve cost: unmeasured.

### 8. Findings
- **F-YOJAKA-1 — 9,327 predicates (18.6 % of the table) are structurally undatable with NO stated
  reason.** The CR-37 `always_on_reason` discipline was implemented for the 20 distribution-yoga
  rows and never extended to SUBSYSTEM (8,586), DISPOSITOR_RELATIONAL (379), DIGNITY (256), DOSHA
  (56) or CLASSIFY_RESIDUAL (15). §N.7 item 6 / §N.6 item 3 (an honest empty must be *reported*, not
  merely be empty). **RECOMMEND: MUST.**
- **F-YOJAKA-2 — `bg_transit_rules` is declared as a dependency and never read; the trigger doctrine
  it holds is hardcoded as Python literals in the writer instead.** §N.7 item 3 (no wrapper-local
  constant may shadow a source), and it is the root of the three-way gochara doctrine overlap above.
  **RECOMMEND: MUST** (it is the Temporal Concordance Contract's load-bearing case).
- **F-YOJAKA-3 — 99.6 % of output never reaches its principal consumer.** `ka_sangam` caps at 200
  of 50,104. Either the cap is right and the asset is over-producing by 250×, or the cap is wrong
  and the convergence engine is starved. Both readings are defects; W2 must pick one. D-SERVICE /
  §N.4 (floors are aspirational — but so is volume without reach). **RECOMMEND: NOW.**
- **F-YOJAKA-4 — `volume_explanation` claims ≈66,738 rows; measured 50,104**, and the same stale
  figure is restated in `query_temporal_activation.ts:6`. §N.7 item 3 / C12. **RECOMMEND: NOW.**
- **F-YOJAKA-5 — `asset_kind = 'artifact'` on a per-chart data writer** with a target table and a
  chart-scoped `count_sql`. The other three assets in this batch are `'data'`. A kind mismatch
  affects cockpit and probe routing. **RECOMMEND: NOW.**
- **F-YOJAKA-6 — undeclared `chart_facts` and `ga_yoga_firings` edges** (the latter is the
  authoritative source CR-37 was built around — it should be a first-class DAG edge, not an
  implicit one). **RECOMMEND: NOW.**
- **F-YOJAKA-7 — the dasha-eligibility rule names no ayanamsha pinning**, while `ka_avadhi` needed
  exactly that fix (CR-110, a live double-spine bug). The same hazard is latent wherever a consumer
  evaluates `MD_or_AD_lord IN constituent_lords` against unpinned `chart_dashas`.
  **RECOMMEND: NOW.**
- **F-YOJAKA-8 — `query_temporal_activation` declares no `density_contract` and does not separate
  datable from undatable predicates in its response.** §N.6 items 1 and 4. Serving-plane (TS), W3.
  **RECOMMEND: NOW.**
- **F-YOJAKA-9 — registry NULLs.** *Proposed integrity invariant:* **referential + distinctness**
  — every `kala_activation_predicates.signal_id` must resolve to a `bodha_msr_signals.signal_id` for
  the same `(chart_id, ayanamsha_id)` (zero orphans), and `(chart_id, ayanamsha_id, signal_id)` must
  be unique; **plus** every row whose `constituent_lords` is empty must carry a non-null
  `always_on_reason` (this is F-YOJAKA-1 expressed as a machine check). *Proposed volume formula:*
  `rows = count(bodha_msr_signals WHERE chart_id=$1)` — one predicate per signal; MEASURED
  correspondence should be checked, since 50,104 predicates vs the writer's own comment about
  "49,315 rows" and the registry's "66,738" disagree. *Floor (§N.4):* 50,104 achieved.
  **RECOMMEND: NOW.**

**Route recommendation (W2 input):** `changed` — two MUST-class findings (silent undatable
predicates; the unread `bg_transit_rules` doctrine edge that anchors the concordance contract), cheap
build (40 s measured), and it is the substrate the layer's headline deliverable is built on.

---

## Kāla `__ssv_*` shadow-table disposition (mandate (b))

### Provenance — what created them
Established from repo evidence, not inference:
`00_ARCHITECTURE/llm_consumption_audit/briefs/suddha_vaca/SUDDHA_VACA_REPORT_v1_0.md` §Phase D
records that the ŚUDDHA-VĀCA campaign built *"`CREATE TABLE ... AS SELECT` snapshots … scoped to
both charts, tag `__ssv_20260728a`"* as the first genuinely restorable rollback baseline in the
codebase's history, and §Step-3 records a second wave: *"Snapshotted 25 chart-scoped tables for both
charts (tag `ssv_20260728b`); tested-rollback drill PROVEN"*. Tag `c` is a third, smaller wave
covering `kala_gochara_windows`, `build_substep_progress` and `asset_throughput`.
`__ssv_` = **ŚUDDHA-VĀCA**, 2026-07-28. Corroborating: every one of these tables has
`idx_scan = NULL` (no indexes at all — the signature of a plain CTAS heap, not a maintained table).

### Is anything reading them?
- **Repo grep for `__ssv`** across `*.py|*.ts|*.sql|*.md|*.json|*.sh` returns **8 files**, of which
  only **one** is production code: `platform/python-sidecar/services/w2g_validations/
  v5_corpus_readiness.py`. That module's `_detect_generation_discriminator()` queries
  `information_schema.tables WHERE table_name LIKE 'kala_gochara_windows\_\_%'` and reports the
  matches as `sibling_tables` — so `kala_gochara_windows__ssv_20260728c` **is** returned in its
  payload. Its PASS/FAIL verdict, however, is driven by `per_row_discriminator_exists` (a *column*
  check), not by `sibling_tables`; dropping the table changes reported evidence, not the outcome.
- `verification_artifacts/DEFECT_SALVAGE_2026-08-05/SALVAGE_LEDGER.md:275-277` records that the
  salvage drain's `tables_with_column()` **deliberately excludes** `'%__ssv_%'` — i.e. the codebase
  already treats these as non-participating.
- **`pg_stat_user_tables`** (MEASURED): `seq_scan` 4–12 on every Kāla shadow, `idx_scan` NULL on
  all. Those counts are consistent with creation + the tested-rollback drill + a handful of audits.
  **No application traffic.**

### Disposition table (evidence-based; nothing dropped — this analysis is read-only)

| Shadow table | Rows (exact) | Bytes | Charts covered | Repo readers | Live table now | Disposition |
|---|---|---|---|---|---|---|
| `kala_activation__ssv_20260728b` | 337,270 | 672,849,920 | `1c826d5a` 335,951 · `482012f1` 1,095 | none | `kala_activation` 671,254 (est.) | **drop-after-snapshot** — rollback window closed at PŪRṆATĀ (2026-07-31); 88 % of the batch's reclaimable bytes |
| `kala_taranga__ssv_20260728b` | 184,824 | 55,246,848 | both, 92,412 each | none | 277,236 (3 charts) | **drop-after-snapshot** |
| `kala_convergence__ssv_20260728b` | 34,046 | 29,523,968 | `1c826d5a` 32,134 · `482012f1` 1,912 | none | 35,365 | **drop-after-snapshot** |
| `kala_gochara_windows__ssv_20260728c` | 1,267 | 3,768,320 | `1c826d5a` only | **`v5_corpus_readiness.py`** (sibling-pattern evidence, non-verdict) | 40,171 (est.) | **retain-as-evidence** until `v5_corpus_readiness.py`'s `sibling_tables` probe is re-pointed; it is also the only surviving artefact cited by ADJUDICATION-6 as the precedent for the generation-discriminator pattern. **Do not drop in this campaign.** |
| `kala_obstruction__ssv_20260728b` | 723 | 360,448 | unmeasured | none | 1,283 (est.) | **drop-after-snapshot** |
| `kala_darshana__ssv_20260728b` | 750 | 344,064 | unmeasured | none | 1,500 | **drop-after-snapshot** |
| `kala_jivana_parva__ssv_20260728b` | 200 | 114,688 | unmeasured | none | 309 | **drop-after-snapshot** |
| `kala_bhavishya__ssv_20260728b` | 100 | 114,688 | unmeasured | none | 200 | **drop-after-snapshot** |

**Total Kāla `__ssv_*` footprint: 762,322,944 bytes = 727.0 MiB.**
**Reclaimable if the four-of-eight verdict above is taken as written (all but
`kala_gochara_windows__ssv_20260728c`): 758,554,624 bytes = 723.4 MiB**, of which
`kala_activation__ssv_20260728b` alone is 642 MiB.

**Adjacent tables that are NOT `__ssv_*` and must be handled differently:**
- **`kala_gochara_windows_archive_20260805` — 35,620 rows / 103 MB. This is the v1 gochara corpus
  archive. The campaign hard floor names it explicitly: *"no destructive operation on irreplaceable
  data — specifically the `ka_gochara_sweep` v1 corpus and any snapshots directory."* **RETAIN,
  PROTECTED. Flagging it here so no `__ssv_*` sweep catches it by adjacency.**
- `kala_gochara_v2_build_state` (552 rows), `kala_gochara_windows_v2` (1,934), `gochara_v3_calibration`,
  `kala_convergence_staging`, `kala_gochara_authority` — live v2/v3 surfaces, out of this batch's
  scope (Batch owning `ka_gochara_*` should disposition them).
- Non-Kāla `__ssv_*` (bodha/phala/mimamsa/l1_tajik/build_substep_progress/asset_throughput,
  30 tables) total a further ~578 MiB — **hand-off to the L2/L4/L5 batches; not this batch's
  write-set.** `bodha_signal_embeddings__ssv_20260728a` alone is 423 MB.

**Findings:**
- **F-SSV-1 — 723.4 MiB of dead ŚUDDHA-VĀCA rollback snapshots in the Kāla namespace with zero
  application readers.** ONGOING_HYGIENE_POLICIES §A (archival retain-in-place) is satisfied by the
  campaign report that documents them; the tables themselves are past their rollback window (the
  rebuild they guarded was accepted and sealed at PŪRṆATĀ, 2026-07-31). **RECOMMEND: NOW** —
  drop-after-snapshot, executed by whoever owns the DB write-set, never by W1.
- **F-SSV-2 — `kala_gochara_windows__ssv_20260728c` has one real (if weak) reader** and is cited by
  ADJUDICATION-6 as the production precedent for the sibling-table generation pattern.
  **RECOMMEND: NEVER-LATER** (retain-as-evidence; re-evaluate only after `v5_corpus_readiness.py`'s
  probe is re-pointed).
- **F-SSV-3 — the `__ssv_*` naming has no registry entry, no retention policy, and no expiry.**
  A future campaign creating `__ssv_*` snapshots will leave the same residue. A one-line retention
  rule in ONGOING_HYGIENE_POLICIES (snapshot tables expire at the sealing of the campaign that
  created them) is the durable fix. **RECOMMEND: NOW** (governance hand-off, not L3 code).

---

## Cross-batch registry-health summary (C12)

| | `ka_kshetra` | `ka_avadhi` | `ka_taranga` | `ka_yojaka` |
|---|---|---|---|---|
| `asset_kind` | data | data | data | **artifact (mismatch)** |
| `estimated_seconds` | 237 | 14 | 23 | 36 |
| **measured wall clock** | **22,685 s** | 14 s | 27 s | 40 s |
| estimate accuracy | **96× low** | accurate | accurate | accurate |
| `has_substeps` | t | f | f | f |
| `target_floor` | 0 | 0 | 0 | NULL |
| `count_sql` chart-scoped | ✓ | ✓ | ✓ | ✓ |
| `integrity_check_sql` | NULL | NULL | NULL | NULL |
| `expected_volume_formula` | NULL | NULL | NULL | NULL |
| `expected_volume_inputs` | NULL | NULL | NULL | NULL |
| `size_sql` | NULL | NULL | NULL | present |
| `volume_explanation` | NULL | NULL | NULL | **stale (66,738 vs 50,104)** |
| `service_health` | NULL (n/a, data) | NULL (n/a) | NULL (n/a) | NULL (n/a) |
| `rows_per_second` / `measurement_count` | NULL / 0 | NULL / 0 | NULL / 0 | NULL / 0 |

Proposed `integrity_check_sql` and `expected_volume_formula` for each asset are written out in that
asset's finding F-*-{7,8,9,11}. **None is a `count(*) = N` equality pin** (C12/D-126): they are
tiling/contiguity checks, referential-resolution checks, range checks, and the §N.5 inheritance
check that would have caught CR-110 mechanically.

## Hard-floor compliance for this batch
- Read-only throughout: only `SELECT` (plus `information_schema` / `pg_class` / `pg_stat_user_tables`
  reads) were issued via `q.sh`. No `INSERT/UPDATE/DELETE/DDL`. No build was run.
- No git write commands issued. One file written: this one.
- **Flagged, not touched:** `kala_gochara_windows_archive_20260805` (v1 gochara corpus, 35,620 rows)
  and `kala_field_snapshots` — both fall under the hard floor's irreplaceable-data rule. No
  disposition proposed for either beyond RETAIN.
- No gate, check or trigger weakening is proposed anywhere in this document. Where a check is
  missing (all four `integrity_check_sql`), a *stronger* replacement is proposed, never a relaxation.
