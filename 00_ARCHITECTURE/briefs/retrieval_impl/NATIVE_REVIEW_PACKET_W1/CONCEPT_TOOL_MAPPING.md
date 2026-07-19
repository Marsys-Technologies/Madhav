---
artifact: CONCEPT_TOOL_MAPPING.md
canonical_id: NATIVE_REVIEW_PACKET_W1_CONCEPT_TOOL_MAPPING
version: 1.0
status: NATIVE REVIEW PACKET — §F human gate deliverable 2/5
governing_brief: RETRIEVAL_IMPLEMENTATION_MASTER_BRIEF_v1_0.md §F item 2
source_data:
  - 00_ARCHITECTURE/briefs/retrieval_impl/REACHABILITY_MATRIX_v1.md
  - platform/src/generated/census/concept_reachability_v1.json
  - 00_ARCHITECTURE/briefs/retrieval_impl/RETRIEVAL_TOOL_CENSUS_v1_0.md
generated_for_native: 2026-07-20
---

# Concept → Tool Mapping — the reachability matrix, rendered readably

Renders `REACHABILITY_MATRIX_v1.md`'s 314-row SERVED × NAVIGABLE × PLANNER-KNOWN matrix, grouped
by lifecycle scannability so a reader can see "fully reachable / dark / needs a decision" at a
glance, rather than reading the raw table. Vidhi-primitive column is populated only where the
generator found a real citation (`grep`-verified against `vidhi/registry_data.ts`); "—" means no
citation was found, not that one was hidden.

## Group 1 — Fully reachable (SERVED + NAVIGABLE), 100% umbrella tool = `chart_facts_query`

**218/218 fact_category concepts** are SERVED and NAVIGABLE via the single umbrella
`marsys://tool/L1/chart_facts_query` (`category` facet param, no enum gate — any live category
string reaches it in one hop, `traversal_level=L-SIGNAL`, `emits_references=true`). Split by
documentation status:

| sub-group | count | example concepts | umbrella path | vidhi primitive |
|---|---:|---|---|---|
| SERVED (documented + queryable) | 152 | `graha_position`, `graha_dignity_per_varga`, `bhava_bala_total_extended`, `panchanga_tithi`, `sade_sati_phase` | `chart_facts_query` → `category=<name>` | — (0/218 planner-known) |
| SERVED-UNDOCUMENTED (queryable, absent from every static list) | 66 | `ashtakavarga_bindu_per_varga` (13,440 rows), `ashtakavarga_bindu_sign` (960), `dispositor_tree` (2900), `graha_centrality` (2610), `sambandha_grade` (10,440), `special_lagna` (490) | `chart_facts_query` → `category=<name>` (caller must already know the exact string) | — |

**19/19 signal_class concepts** (`bodha_msr_signals.signal_type_class`) are SERVED and reachable
via 4 tools: `judgment_query`, `yoga_activation_by_dasha`, `query_signals`, `call_priority_ranking`.
7 of the 19 have a real vidhi-primitive citation (`dhana_yoga_scan`, `dosha_scan`,
`nakshatra_semantics`, `sudarshana_agreement_check`, `arudha_read`, `special_lagna_read`, plus a
`tool_args`-shaped reference for `bhavat_bhavam_amplifier`/`varga_ratification_divergence`); 12
have no vidhi citation.

**2 dark tables independently corrected to SERVED this wave** (false-dark, caught by a
directory-scope gap in L1b's scan — same failure mode GT-51 already named):

| table | now served by | umbrella path |
|---|---|---|
| `bg_dignity_reference` | `platform-mcp/src/tools/register_p1_reference.ts` | direct capability call |
| `chart_panchanga` | `platform/src/lib/tools/brahma/l1/query_panchanga.ts` | direct capability call |

## Group 2 — Dark, deliberately unserved (INTERNAL-BY-DESIGN), 24 tables

No wiring needed — confirmed-plausible sidecar computation inputs / bookkeeping tables, not
caller-facing concepts. Not individually re-verified per-table (naming-pattern proposal, per
L1b's own scope statement).

| pattern | count | representative concepts |
|---|---:|---|
| `bg_*` reference/rule/threshold tables (L0) | 14 | `bg_avastha_schemes`, `bg_combustion_orbs`, `bg_graha_dik`, `bg_transit_rules`, `bg_vastu_directions` |
| bookkeeping-suffix tables (`_history`/`_supersedence`/`_cache`/`_staging`/`_log`/`_contributions`/`_feedback`/`_cosign`/`_snapshot`) | 10 | `chart_facts_history`, `chart_facts_supersedence`, `chart_panchanga_cache`, `kala_convergence_staging`, `mimamsa_adjudication_log`, `mimamsa_export_log`, `mimamsa_pool_contributions`, `mimamsa_resonance_feedback`, `mimamsa_snapshot_cosign`, `mimamsa_calibration_snapshot` |

## Group 3 — Dark, NEEDS-OWNER (51 tables) — the honest "needs a human call" set

Zero tools reach these; evidence does not yet support a confident disposition. Grouped by how
close a decision is, per `DARK_SET_WIRING_PLAN_v1_0.md`'s design analysis:

### 3a — Real, populated data; wiring plan already sketched (highest-value, lowest-ambiguity)

| concept | rows | proposed shape | est. effort |
|---|---:|---|---|
| `bodha_triangulation` | 200 | new `bodha_triangulation_get` leaf (or facet on `bodha_discoveries_get`/`bodha_signals_get`) | M |
| `bodha_rm_dasha_windowed_prescriptions` | 0 | new `bodha_remedy_prescriptions_get` drill off existing `bodha_remedies_get` — **first confirm 0-rows is real, not a build gap** | M |
| `bodha_cdlm_domain_rollups` / `bodha_cdlm_evolution_gradients` / `bodha_cdlm_pattern_clusters` | 60 / 0 / 10 | extend the already-serving CDLM tool with a `tier`/`rollup_level` facet (siblings `bodha_cdlm_cells`/`chart_summary` are already served) | S |
| `bodha_cgm_sub_graphs` (+ siblings `bodha_cgm_nodes`/`edges`/`chart_topology_summary`) | 10 / 649 / 1573 / 10 | **investigate first** — live tools (`get_cgm_subgraph`, `bodha_graph_subgraph_get`, `bodha_graph_traverse_get`) already exist; this may turn out already-SERVED via a route this scan couldn't see (same GT-51 pattern) | S if already served (likely), M if a genuine gap |

### 3b — Plausible-internal but not individually verified; owner-assignment pass needed

- **L0 `bg_prashna_*`/`bg_transit_*` (6 tables):** `bg_prashna_lagna_methods`, `bg_prashna_significators`,
  `bg_prashna_special_techniques`, `bg_prashna_tajik_yogas`, `bg_transit_av_gates`, `bg_transit_engine`
  — most likely to be caller-relevant (prashna/transit are live query domains — `prashna_undertaking_get`,
  `ganita_av_transit_gating_get` already exist); check whether those handlers already join these
  tables server-side before proposing anything new.
- **L5 `mimamsa_fact_adjustment`/`mimamsa_signal_adjustment`** (121,100 / 97,504 rows, the two
  largest DARK tables in the whole set): almost certainly the row-level calibration deltas
  `mimamsa_calibration_get` already aggregates over — likely correctly internal, but **do not build
  against calibration-ledger internals without native/L5-owner sign-off** (L5 is SEALED STRUCTURAL
  mode; B.1/B.10 caution against exposing raw adjustment rows as settled facts).
- **11 remaining ungrouped NEEDS-OWNER tables** (no design-note coverage this wave): `chart_grants`,
  `ga_condition_composite`, `ga_prashna_judgment`, `ga_prashna_lagna`, `ganita_dashas`,
  `ganita_graha_sthana`, `brahma_activity_ontology`, `brahma_class_priors`,
  `brahma_compendium_index`, `brahma_dasha_systems`, `brahma_event_ontology`,
  `brahma_formula_constants`, `brahma_prospective_ledger`, `brahma_vichara_constants`,
  `bodha_anomalies`, `bodha_contradictions`, `bodha_convergence`, `bodha_rm_chart_summary`,
  `bodha_rm_dosha_remedy_bundles`, `bodha_rm_pattern_remedies`, `bodha_signal_embeddings`,
  `kala_activation_predicates`, `kala_gochara_windows`, `mimamsa_anchor_adjustment`,
  `mimamsa_attribution`, `mimamsa_convergence_adjustment`, `mimamsa_discoveries`,
  `mimamsa_event_provenance`, `mimamsa_load_bearing`, `mimamsa_manifestation_sets`,
  `mimamsa_negative_controls`, `mimamsa_preferences`. These are the ones this packet flags most
  strongly for the native's own judgment call — see SUMMARY.md.

### 3c — Dark services (not tables), plan-settled dispositions carried forward

| service | disposition | reachability today |
|---|---|---|
| `kala_timeline` | DARK-UNWIRED — handler exists, never imported into `server.ts`; a one-line fix, not a build gap | not served |
| `ka_graha_sancara` (`call_ephemeris_at_t`) | DARK SERVICE — highest-impact single coverage item; stub unconditionally errors | not served — see TOOL_SHAPE_DESIGN.md worked example (c) |
| `ka_muhurta_seva` (`call_muhurta_score`) | same stub shape, found this wave, not GT-50-named | not served |

### 3d — Naming anomaly, not a wiring question

`chart_ayanamsha_reports` (cited in the master brief's aspirational examples) **does not exist**
in the live DB — verified against L1b's full 247-table live scan, zero match. Closest real tables:
`concordance_ayanamsha_flags` (2 rows), `concordance_ayanamsha_flags_staging` (0 rows). Flagged for
the native: either the naming is stale/aspirational, or it refers to a computed report (not a
table) `chart_facts_query`'s `ayanamsha_id` filter already serves without a dedicated table.

## Group 4 — RETIRE (5 concepts, plan-settled, not re-derived)

`reference_aspects`, `reference_signs`, `reference_planets`, `reference_nakshatras`,
`reference_vargas` — dead, superseded by the served `bg_*` equivalents (GT-52). Not wire-up
candidates.

## FACT_CATEGORY_GAP rows (E3, 3 summary rows, full lists in the JSON)

| id | description | count |
|---|---|---:|
| FCAT-001 | live-DB categories absent from `CHART_FACTS_SCHEMA.json` | 144 |
| FCAT-002 | live-DB categories absent from `coverage_matrix.ts`'s enum | 66 |
| FCAT-003 | `coverage_matrix.ts`-declared categories with 0 live rows | 6 (`ashtakavarga_anubindu`, `dosha_fires`, `esoteric_point_chatushphuta`, `esoteric_point_panchasphuta`, `esoteric_point_trisphuta`, `yoga_fires`) |

---

*End of CONCEPT_TOOL_MAPPING v1.0 — NATIVE_REVIEW_PACKET_W1, deliverable 2/5. Full 314-row matrix
at `platform/src/generated/census/concept_reachability_v1.json` / `REACHABILITY_MATRIX_v1.md`.*
