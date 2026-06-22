---
artifact: L4_PHALA_REGISTRY_AND_WIRING_SPEC_v1_0.md
canonical_id: L4_PHALA_REGISTRY_AND_WIRING_SPEC
version: 1.0
status: CURRENT — GATE D/E spec: the exact registry rows, count_sql, migrations, manifest + wiring the swarm applies
authored_by: Cowork 2026-06-22
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
role: >
  The REGISTER + WIRE spec for L4 Phala (GATE D/E of the closure plan). Gives the swarm the exact
  asset_registry rows (5 updated + 3 new), the count_sql, the migration pre-allocation, the
  CAPABILITY_MANIFEST entries, and the orchestrator/DAG/Dockerfile wiring requirements — verified
  against the live seed format (platform/scripts/seed/asset_registry_seed.ts lines 1437-1522).
applies_findings: L4_PHALA_HOLISTIC_REVIEW_v1_0.md (F1 waves, F3 serialization, F5 cross-links)
---

# L4 Phala — Registry + Wiring Spec (GATE D/E)

## §1 — asset_registry rows (the "asset catalog/CTS")
The 5 existing `ph_*` rows (seed lines 1438-1522) have the right STRUCTURE but their `depends_on` +
`english_description` are from the OLD 6-asset draft. **Update all 5 + add 3 new** (sort_order 6/7/8).
Every `count_sql` uses `$1` (verified pattern). `target_floor: null` (set to achieved post-build,
floors-aspirational). `estimated_seconds: null` (measured on first build). `asset_kind: 'artifact'`.

### Updated rows (corrected depends_on per the supreme briefs)
```ts
// ph_nimitta — sort_order 1 — UPDATE depends_on + description
depends_on: ['ka_sangam','kala_bhavishya','bodha_discoveries','bodha_signal_embeddings',
             'bodha_cgm_paths','bodha_cdlm_cells','u1_dasha_consensus','u4_school_consensus'],
english_description: 'Predictive anchors: 8 derivation axes (graph-causal, discovery-seeded, embedding-precedent, dāśā+school consensus, ayanāṃśa-robustness, subsystem) + 5 elevations (magnitude, ranged-confidence, karmic-arc, actionability, contradiction); inherits kala_bhavishya',

// ph_muhurta — sort_order 2 — UPDATE
depends_on: ['ph_nimitta','ka_kalasutra','ga_panchanga'],   // + calls ka_muhurta_seva, ka_vighnakara, ka_gochara, ga_condition
english_description: 'Personalized auspicious windows: chart-strength + live-transit scored, personal-danger-avoiding, prediction-fused (rides ph_nimitta windows), honest no-good-window verdict',

// ph_sodhana — sort_order 3 — UPDATE
depends_on: ['ph_nimitta','bo_laksana'],   // + PyJHora compute_ascendant; consumes U1/U3/U4 as the scorer
english_description: 'Whole-instrument birth-time rectification: PyJHora ascendant per candidate, scored by rebuilt dāśā+convergence vs 57 LEL events, body-pattern + multi-school/dāśā consensus cross-check, leakage-firewall, confidence interval',

// ph_pratikara — sort_order 4 — UPDATE
depends_on: ['ph_nimitta','bo_upaya','ka_vighnakara'],   // soft-links ph_muhurta
english_description: 'Managed remedy program: economics/feasibility tiers, sequenced+conflict-free schedule, muhūrta-timed initiation, severity-proportional, cross-tradition choice, outcome loop',

// ph_suddha_sodhana — sort_order 5 — UPDATE
depends_on: ['ph_sodhana'],
english_description: 'Living rectification verdict: decisiveness (decisive/probable/unresolved), self-correcting verification loop, competing-hypotheses ledger, self-falsifier; flag+stage chart revision (never auto-override)',
```

### NEW rows (append after ph_suddha_sodhana; before the MIMAMSA block)
```ts
{
  asset_id: 'ph_sankrama',
  layer: 'phala', sort_order: 6,
  sanskrit_name: 'Saṅkrama',
  english_name: 'Cross-domain spillover',
  english_description: 'Grounded multi-hop cross-domain dynamics: lag from real activation windows + graph-bridge mechanism, A→B→C cascades, cross-domain conflicts, trajectory + mitigation routing',
  storage_type: 'postgres_table',
  target_table: 'phala_sankrama',
  count_sql: 'SELECT count(*) FROM phala_sankrama WHERE chart_id = $1',
  size_sql: "SELECT pg_total_relation_size('phala_sankrama')",
  target_floor: null, expected_volume_formula: null, expected_volume_inputs: null,
  volume_explanation: 'One row per (anchor × target-domain × relationship); count depends on linkage density',
  depends_on: ['ph_nimitta'],   // + reads bodha_cdlm_cells, soft-links ph_pratikara
  scope: 'per_chart', is_active: true, estimated_seconds: null,
},
{
  asset_id: 'ph_pramana',
  layer: 'phala', sort_order: 7,
  sanskrit_name: 'Pramāṇa',
  english_name: 'Falsifiability scaffolding',
  english_description: 'Unified machine-evaluable falsifiers for every L4 prediction + the L5 onboarding contract + evaluation-staging (no scoring) + portfolio/reverse-calibration channel. Strictly non-scoring (L5 owns calibration)',
  storage_type: 'postgres_table',
  target_table: 'phala_pramana',
  count_sql: 'SELECT count(*) FROM phala_pramana WHERE chart_id = $1',
  size_sql: "SELECT pg_total_relation_size('phala_pramana')",
  target_floor: null, expected_volume_formula: null, expected_volume_inputs: null,
  volume_explanation: 'One row per L4 prediction across all ph_* prediction-emitting assets',
  depends_on: ['ph_nimitta','ph_sankrama','ph_muhurta','ph_pratikara','ph_sodhana','ph_suddha_sodhana'],
  scope: 'per_chart', is_active: true, estimated_seconds: null,
},
{
  asset_id: 'ph_phaladesa',
  layer: 'phala', sort_order: 8,
  sanskrit_name: 'Phaladeśa',
  english_name: 'Delivered outlook',
  english_description: 'The master-acharya reading: narrative weave (B.11), apex item, honest confident/contested/speculative registers, multi-horizon + multi-lens, person-anchored to the gestalt, fully traceable; deterministic scaffold + serve-time narration (Gemini/DeepSeek)',
  storage_type: 'postgres_table',
  target_table: 'phala_outlook',
  count_sql: 'SELECT count(*) FROM phala_outlook WHERE chart_id = $1',
  size_sql: "SELECT pg_total_relation_size('phala_outlook')",
  target_floor: null, expected_volume_formula: null, expected_volume_inputs: null,
  volume_explanation: 'One row per composed (horizon × question-lens) dossier',
  depends_on: ['ph_nimitta','ph_muhurta','ph_pratikara','ph_suddha_sodhana','ph_sankrama','ph_pramana'],
  scope: 'per_chart', is_active: true, estimated_seconds: null,
},
```
> **CS1 serialization:** all seed edits land in ONE post-wave commit (no concurrent edits).
> **Note on `depends_on` with u*_ ids:** U1/U4 are enabler workstreams, not registry assets. In the
> registry `depends_on` use the real asset_ids they produce/touch (ka_sangam carries the enriched
> convergence; the dāśā-consensus + school-consensus are consumed via services at build time, not as
> DAG-parent assets). The DAG dependency on the ENABLERS is enforced by the **session_queue wave order**
> (W1/W2 before W3), not the registry depends_on. Keep registry depends_on to real upstream ASSETS.

## §2 — Migration pre-allocation (the two-174 trap; D14)
All in `platform/supabase/migrations/`. L4 assets 330-337; the L3-side enabler migrations get the next
free numbers AFTER 337 (U2/U3 extend kala_convergence; U4 persists the school tables).

| # | File | Asset |
|---|---|---|
| 330 | `330_phala_anchors_and_drop_kala_timeline.sql` | ph_nimitta (+ DROP kala_timeline / CF.L3.2) |
| 331 | `331_phala_muhurta.sql` | ph_muhurta |
| 332 | `332_phala_mitigation.sql` | ph_pratikara |
| 333 | `333_phala_rectification.sql` | ph_sodhana |
| 334 | `334_phala_rectification_best.sql` | ph_suddha_sodhana |
| 335 | `335_phala_sankrama.sql` | ph_sankrama |
| 336 | `336_phala_pramana.sql` | ph_pramana |
| 337 | `337_phala_outlook.sql` | ph_phaladesa |
| 338 | `338_kala_convergence_horizon_tier.sql` | U2 (horizon_tier column) |
| 339 | `339_kala_convergence_current_breakdown.sql` | U3 (per-current breakdown, optional §3.5) |
| 340 | `340_school_consensus_tables.sql` | U4 (the 057-060 schema, renumbered + chart-scoped) |

> Pre-fan-out (PRE-2) re-confirms the global max across BOTH migration dirs before allocating.

## §3 — CAPABILITY_MANIFEST.json entries
For EACH new writer + table (3 new assets + the U2/U3/U4 changes), add a manifest entry:
```json
{ "canonical_id": "PH_SANKRAMA_WRITER", "path": "platform/python-sidecar/pipeline/orchestrator/writers/ph_sankrama.py",
  "version": "1.0", "status": "CURRENT", "layer": "L4", "expose_to_chat": false, "fingerprint": "<sha256>" }
```
+ a DB-table entry per `phala_*` table. The fingerprint is set after first commit (rotation job).
drift_detector + schema_validator must exit clean (registry ↔ manifest ↔ filesystem agree).

## §4 — Orchestrator / DAG / Dockerfile wiring (E1–E3)
- **E1 — writer registration:** each ph_* is `@register('ph_*')` `WriterBase` in
  `platform/python-sidecar/pipeline/orchestrator/writers/`. Auto-discovered via pkgutil. The DAG order
  is the F1-corrected wave structure (enforced by the session_queue, not registry depends_on alone).
- **E2 — Dockerfile.pipeline COPY (the silent-hang gotcha):** confirm `COPY ... pipeline/orchestrator/
  writers/` includes the 8 new ph_* files AND the new `services/ph_*/` dirs. (The bo_pramana_mapa bug:
  a missing COPY → ModuleNotFoundError at runtime → job hangs IN_PROGRESS.) Add an explicit pre-build check.
- **E3 — cockpit render:** the Phala layer is derived from `asset_registry.layer='phala'` (no frontend
  hardcode — verified). After build, the Phala panel shows 8 lit assets.
- **build-state authority (CF.L3.8):** the orchestrator is the SOLE `asset_throughput`/`last_built_at`
  writer; ph_* writers never stamp it. L4 builds go through the orchestrator click-Build path (NOT a reconcile script).

## §5 — The 3 cross-link enhancements (F5 — fold into the briefs' read sets)
- **ph_phaladesa** adds `ph_pramana` to its read set (PD3 confident/contested/speculative reads the
  structured confidence tiers).
- **ph_sodhana** tags rectification predictions with an `epistemic_caveat` (the partly-circular
  confidence, D43) so ph_pramana → L5 weights them carefully.
- **ph_phaladesa** surfaces ph_suddha_sodhana's `revision_recommended` flag in its honest-framing
  ("this reading assumes the recorded 10:43; rectification suggests a possible revision").

## §6 — The U2/U3 shared-engine serialization (F3 — for the session_queue)
W2 internal order (NOT parallel on ka_sangam): **U3 currents (6)** → **U4** (de-hardcode/persist/wire)
→ **U3 school-consensus current (C13, 2nd pass)** → **U2 lifetime run** → re-seal L3. (U1 wire-only is
independent in W1.) The convergence is rebuilt ONCE, enriched, over both horizon tiers.

---
*End of L4_PHALA_REGISTRY_AND_WIRING_SPEC v1.0. The exact registry rows (5 updated + 3 new), count_sql,
migrations 330-340, manifest, orchestrator/Dockerfile wiring, cross-links, serialization. The swarm
applies this at REGISTER+WIRE.*
