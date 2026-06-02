---
artifact: BRAHMA_L1_L5_REGISTRY_SEED_v1_0.md
canonical_id: BRAHMA_L1_L5_REGISTRY_SEED
version: 1.0
status: CURRENT (the L1–L5 plan + the master L0→L5 queue the autonomous swarm consumes)
project_codename: Brahma
authored_by: Claude (Cowork) 2026-06-03
grounds_in:
  - LAYER_1_CHART_FACTS_DESIGN_v1_0 + LAYER_1_STORAGE_STRATEGY_v1_0 (Gaṇita)
  - LAYER_2_CHART_INTELLIGENCE_DESIGN_v1_0 (Bodha)
  - LAYER_3_TEMPORAL_FABRIC_DESIGN_v1_0 (Kāla)
  - LAYER_4_PREDICTIVE_ENGINE_DESIGN_v1_0 (Phala)
  - LAYER_5_LEARNING_DESIGN_v1_0 + LEL_SCHEMA_AND_INTAKE_v1_0 (Mīmāṃsā)
pairs_with: L0_CONTRACT_REGISTRY_SEED_v1_0 (Brahmagyan)
governed_by: BUILD_GUARANTOR_SWARM_CHARTER + BUILD_GUARANTOR_AUTONOMOUS_MODE
purpose: >
  Completes the plan. Together with the L0 seed, this spans the entire instrument. The Conductor walks
  the master queue (§A); each layer releases when its upstream layer is verified-green, so the autonomous
  swarm builds Brahmagyan → Gaṇita → Bodha → Kāla → Phala → Mīmāṃsā in one unattended run. Each L1–L5
  unit = build its writers + retrieval tool(s) + schema + tests, deploy (web+MCP), and verify by RUNNING
  the layer against the native's chart. Racayitā drafts each detailed brief from the layer's design doc.
test_subject: the native's chart (Abhisek Mohanty, 1984-02-05) — the one chart every layer is verified against.
---

# Brahma L1–L5 — Contract Registry Seed + Master Queue

## §A — Master queue (the full instrument; cross-layer dependency-gated)

```
L0 Brahmagyan  (global foundation)                                 ← L0_CONTRACT_REGISTRY_SEED
   │ green ▼
L1 Gaṇita      depends_on L0                  (engine + facts + tools)
   │ green ▼
L2 Bodha       depends_on L1 (+ L0 rules/concordance)   (signals + graph + lenses + tools)
   │ green ▼
L3 Kāla        depends_on L1 + L2             (temporal fabric + tools)
   │ green ▼
L4 Phala       depends_on L2 + L3             (predictive ensemble + muhurta + tools)
   │ green ▼
L5 Mīmāṃsā     depends_on L4 + isolated LEL   (learning loop + tools)  → instrument complete
```
Each layer is released the moment its upstream `depends_on` layers pass their layer-complete gate.
Within a layer, independent assets build in parallel worktrees. No human in the loop (AUTONOMOUS_MODE).

## §B — Gaṇita / L1 (Chart Facts)  — design: LAYER_1_CHART_FACTS_DESIGN

**Shape:** 1 engine computation (PyJHora, enumerated **superset of FORENSIC v8.0**) → typed Fact Store +
forensic render (2 projections). Ayanamsha-invariant/dependent split; dashas to **Sukshma (SD)** depth.
**Verify:** run the engine on the native's chart; the Fact Store passes the enumerated-coverage contract +
internal-consistency + per-domain volume floors.

| Asset | tool | acceptance gate |
|---|---|---|
| `ganita.engine` (positions, houses, vargas, dashas, panchanga, sensitive points per ayanamsha) | `query_chart_facts` (composite) | engine emits the full enumerated superset; coverage ≥ FORENSIC benchmark; determinism hash-stable |
| `ganita.positions` | `query_positions` | every graha + sensitive point present, provenance envelope |
| `ganita.divisionals` | `query_divisional` | all vargas D1–D60 present per the catalog |
| `ganita.dashas` (to SD) | `query_dasha` | the curated dasha systems to Sukshma depth |
| `ganita.strength` (shadbala/ashtakavarga/bala) | `query_strength` | full strength tables, non-null |
| `ganita.sensitive_points` (upagrahas, special lagnas, sahams, arudhas) | `query_sensitive_points` | full set vs the benchmark |
| `ganita.panchanga` (birth) | `query_panchanga` | birth-moment limbs correct vs reference |
| `ganita.facts_store` (typed schema) + `ganita.forensic_render` (markdown) | (projections of the engine JSONL) | both reproduce the engine output; render coverage ≥ contract |
**Layer-complete:** all assets + tools green on the native's chart; Fact Store ≥ superset; tools live web+MCP.

## §C — Bodha / L2 (Chart Intelligence)  — design: LAYER_2_CHART_INTELLIGENCE_DESIGN

**Shape:** rule-generated **signals** + **signal graph** + lenses + activation + negative-space + salience +
embeddings, over Gaṇita's facts + Brahmagyan's rules/concordance. **Correlation-aware confidence** (no
school double-counting). **Verify:** run on the native's chart; signals are grounded + cited.

| Asset | tool | acceptance gate |
|---|---|---|
| `bodha.signals` (MSR) | `query_signals` (domain/valence/confidence/salience filters) | every signal grounded to L1 facts + L0 rules, cited |
| `bodha.graph` (CGM) | `cgm_subgraph` | valenced edges (reinforce/contradict/…); traversal returns provenance |
| `bodha.domain_links` (CDLM) | `cdlm_lookup` | cross-domain linkages present |
| `bodha.resonance` (RM) | `rm_walk` | resonance elements present |
| `bodha.lenses` (concordance/contradiction) + `bodha.negative_space` + `bodha.salience` | (views over the graph) | concordance distinguishes silent vs contradicts; negative-space computed |
| `bodha.remediation` (new) | `query_remediation` | each contradiction-hub/anchor → cited L0 remedy; no hallucinated remedies |
| `bodha.embeddings` (signal vectors) | (feeds vector search) | one vector per signal in pgvector |
| `bodha.holistic_bundle` (composite, whole-chart-read B.11) | `holistic_bundle` | one call returns MSR+CGM+CDLM+RM coherently |
**Note:** `bodha.relational` (composite/synastry graph) is **deferred** — needs multi-native data + consent;
parked in the queue until those exist. **Layer-complete:** signal-set grounded + cited; all tools green.

## §D — Kāla / L3 (Temporal Fabric)  — design: LAYER_3_TEMPORAL_FABRIC_DESIGN

**Shape:** deterministic temporal activity map — where dashas/transits/active-signals **align** in time.
States only that an alignment exists (not what it means — that's Phala). **Verify:** run on the native's
chart; convergence windows reproduce against known life-period alignments.

| Asset | tool | acceptance gate |
|---|---|---|
| `kala.timeline` (dasha×transit alignment) | `timeline_query` | alignment series computed over the life range; deterministic |
| `kala.convergence` (measured convergence windows) | `convergence_window` | convergence windows surfaced with their constituent factors |
| `kala.obstruction` (overlaps) + `kala.snapshot` (period point-in-time) | `period_snapshot` | snapshot returns the active state at any date |
| `kala.temporal` (composite) | `temporal` | one call returns the fabric for a date range |
**Note:** `kala.spatial` (relocational activation index) is a **deferred specialist module** — parked.
**Layer-complete:** fabric deterministic (rebuild-stable) on the native's chart; all tools green.

## §E — Phala / L4 (Prediction)  — design: LAYER_4_PREDICTIVE_ENGINE_DESIGN

**Shape:** calibrated **ensemble** of classical predictors → falsifiable, probabilistic **event anchors** +
mitigation + rectification. **Hybrid build:** precompute the major lifetime anchor set; ad-hoc windows lazy.
**Correlation-aware confidence + rectification train/test holdout.** L4 v1 = classical ensemble + slow
learning veneer (multiplier ~1.0 until corpus). **Verify:** run on the native's chart; anchors carry a
falsifier; rectification uses a held-out split.

| Asset | tool | acceptance gate |
|---|---|---|
| `phala.anchors` (event anchors: window+theme+confidence+falsifier) | `event_anchors` | every anchor has an explicit falsifier + calibrated confidence |
| `phala.mitigation` (mitigation map) | `mitigation_map` | mitigations cite L0/L2 remediation |
| `phala.rectification` (birth-time) | `rectification` | uses a train/test split inside LEL; no leakage |
| `phala.muhurta` (electional — inverts Phala) | `muhurta_finder` | given a desired action, returns ranked future windows |
| `phala.outlook` (composite) | (bundle) | one call returns the predictive picture for a horizon |
**Layer-complete:** anchors falsifiable + calibrated on the native's chart; rectification leak-free; tools green.

## §F — Mīmāṃsā / L5 (Learning)  — design: LAYER_5_LEARNING_DESIGN + LEL_SCHEMA_AND_INTAKE

**Shape:** held-out learning loop. **Not** a 0→100% per-chart build — a thin always-active substrate.
**Tracked one-time:** LEL intake = ingest the **full 57 events** from `LIFE_EVENT_LOG_v1_2.md` (NOT the
wiped DB) into the pure-event `life_events`; build the derived Event Chart-State Index. **Verify:** the
prediction ledger logs before outcome; LEL stays isolated (never feeds generation).

| Asset | tool | acceptance gate |
|---|---|---|
| `mimamsa.lel_intake` (one-time: 57 events from the .md → pure-event store) | `lel_query` | life_events = 57; Event Chart-State Index derived; LEL isolated |
| `mimamsa.prediction_ledger` (log before outcome) | `log_prediction` | predictions logged with confidence+horizon+falsifier before outcome |
| `mimamsa.outcome` (record + score) | `record_outcome` | Brier/calibration/timing/per-technique/per-ayanamsha scoring |
| `mimamsa.multiplier` (recalibration) | (internal) | bounded learning_multiplier moves only from outcomes; classical layer modulated not overwritten |
| `mimamsa.research` (cross-corpus → BigQuery/Parquet OLAP) | (analytics) | exports L1/L2 to Parquet→BigQuery; rule validation/discovery runs off-OLTP |
| `mimamsa.answer_quality` (golden Q&A eval) | (eval) | reading-quality eval distinct from prediction calibration |
**Layer-complete:** ledger live + held-out discipline enforced + LEL isolated + the multiplier wired →
**instrument complete.**

## §G — How it runs to completion, unattended

The Conductor walks §A. Brahmagyan builds (L0 seed) → on green, Gaṇita releases → on green, Bodha → Kāla →
Phala → Mīmāṃsā. Each layer's assets build in parallel worktrees, each verified by running on the native's
chart; pass → green → next, fail → bounded auto-fix → park. Deferred modules (`bodha.relational`,
`kala.spatial`) stay parked (they need multi-native/consent or are specialist) and surface in the report
without blocking the run. When Mīmāṃsā is green, the queue is drained and the swarm emits the final
instrument-complete report — and stops. **You do not come in between layers.**

---

*End of BRAHMA_L1_L5_REGISTRY_SEED v1.0 — with the L0 seed, this is the complete plan. Load both into the
Conductor as the master queue; the autonomous swarm builds the entire instrument Brahmagyan → Mīmāṃsā in
one unattended run, verified throughout against the native's chart.*
