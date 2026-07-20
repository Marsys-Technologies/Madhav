---
artifact: ASSET_AND_CONCEPT_MAP.md
canonical_id: NATIVE_REVIEW_PACKET_W1_ASSET_CONCEPT_MAP
version: 1.0
status: NATIVE REVIEW PACKET — §F human gate deliverable 1/5
governing_brief: RETRIEVAL_IMPLEMENTATION_MASTER_BRIEF_v1_0.md §F item 1
source_data:
  - 00_ARCHITECTURE/briefs/retrieval_impl/TABLE_CONCEPT_DISPOSITIONS_v1_0.md
  - platform/src/generated/harvest/adjudication_queue.json
  - platform/src/generated/harvest/e2_db_truth.json
  - platform/src/generated/census/concept_reachability_v1.json
  - platform/src/lib/retrieval/registry/service_manifest/service_manifest.json
generated_for_native: 2026-07-20
---

# Asset & Concept Map — every asset/service → the concepts it holds

Every number below traces to a real generated artifact — no hand-typed estimate. "Concept" here
means the W1 harvest's three concept_kinds: **fact_category** (a `chart_facts.fact_category`
value, L1 granularity), **dark_table** (a real DB table with zero TS-registry-declared serving
route), **signal_class** (`bodha_msr_signals.signal_type_class`, the one confirmed cross-plane
signal-class column E4 found). The concept_ledger (`platform/supabase/migrations/461_concept_ledger.sql`)
is the durable home for this — 355 rows staged (218 + 19 + 118), not yet applied to the live DB
(conductor's call, W1 Lane L1a/L1b).

## Layer L0 — Brahmagyan (reference/compute-input plane)

29 DARK tables (zero serving route found by the TS-registry scan) out of L0's reference-table
estate. Disposition breakdown (`TABLE_CONCEPT_DISPOSITIONS_v1_0.md`):

| disposition | count | representative concepts |
|---|---:|---|
| INTERNAL-BY-DESIGN | 14 | `bg_avastha_schemes`, `bg_combustion_orbs`, `bg_graha_dik`, `bg_graha_naisargika_friendship`, `bg_medical_mappings`, `bg_motion_state_thresholds`, `bg_nakshatra_medical`, `bg_prashna_fructification_rules`, `bg_shashtiamsha_deities`, `bg_transit_moorti`, `bg_transit_rules`, `bg_transit_vedha`, `bg_vastu_direction_remedials`, `bg_vastu_directions` |
| SERVED (corrected this lane) | 1 | `bg_dignity_reference` — served by `platform-mcp/src/tools/register_p1_reference.ts`, a directory L1b's scan didn't cover |
| NEEDS-OWNER | 14 | `bg_prashna_lagna_methods`, `bg_prashna_significators`, `bg_prashna_special_techniques`, `bg_prashna_tajik_yogas`, `bg_transit_av_gates`, `bg_transit_engine`, `brahma_activity_ontology`, `brahma_class_priors`, `brahma_compendium_index`, `brahma_dasha_systems`, `brahma_event_ontology`, `brahma_formula_constants`, `brahma_prospective_ledger`, `brahma_vichara_constants` |

L0 also holds the served orientation-digest surfaces (`asset_registry_all/L0`, `intent_classify`,
`ephemeris_cache_*`) plus 27 served L0 tool capabilities (query_planet_position, query_yoga_catalog,
query_dosha_catalog, query_sutravali_rules family, remedy/mantra/text query family — see
`RETRIEVAL_TOOL_CENSUS_v1_0.md` rows tagged `layer: L0`).

## Layer L1 — Gaṇita (chart_facts + per-chart compute)

**228 concepts** at L1: 218 live `fact_category` values (100% of the live DB set, per
`CONCEPT_COVERAGE_CENSUS_v1_0.md`) + 10 dark L1 tables.

- **fact_category (218 total):** all 218 are technically SERVED — `chart_facts_query`'s category
  filter (`fact_category = ANY($n::text[])`) has no enum gate, so every live category is queryable
  by string today. Of these, **152 are documented** in `coverage_matrix.ts`'s 158-entry list (6 of
  that list's entries are declared but never populated live — see FCAT-003 below); **66 are
  SERVED-UNDOCUMENTED** — queryable but absent from every hand-maintained list, so a caller must
  already know the exact category string. **0 are planner-known** (no vidhi primitive/floor
  references any of the 218 by name).
- **10 dark L1 tables:** disposition split — `chart_facts_history`/`chart_facts_supersedence`/
  `chart_panchanga_cache` = INTERNAL-BY-DESIGN (bookkeeping-suffix pattern); `chart_panchanga` =
  **SERVED (corrected this lane)** via `platform/src/lib/tools/brahma/l1/query_panchanga.ts`, a
  third serving directory outside both scans; `chart_grants`, `ga_condition_composite`,
  `ga_prashna_judgment`, `ga_prashna_lagna`, `ganita_dashas`, `ganita_graha_sthana` = NEEDS-OWNER.

**Fact-category enumeration disagreement (`FACT_CATEGORY_ENUMERATION_RECONCILIATION_v1_0.md`,
W-23):** the live DB is chosen as the single authoritative source (218 categories) over five
disagreeing static sources found across the repo: `CHART_FACTS_SCHEMA.json` (147, two byte-identical
copies) · a third undocumented Python-sidecar copy of the same filename (191) ·
`coverage_matrix.ts` `CHART_FACTS_CATEGORIES` (158, 1 real import site — a CI test gate, not a
runtime consumer) · `ganita/types.ts` `CHART_FACTS_CATEGORIES` (26, a 5th source this lane found,
2 import sites, re-export only).

L1 also serves ~46 flat_fact/temporal leaf tools (`get_positions`, `get_dashas`, `get_dignity`,
`get_yoga_dosha`, `get_yoga_firings`, `get_av_transit_gating`, etc. — full list in
`RETRIEVAL_TOOL_CENSUS_v1_0.md`).

## Layer L2 — Bodha (35 concepts: 19 served signal_class + 16 dark tables)

- **signal_class (19 of 19 — full set, not a sample):** `bodha_msr_signals.signal_type_class`
  values (`composite_state`, `karaka_alignment`, `sade_sati`, `varga_pattern`, `panchanga`,
  `tradition_specific`, `annual`, `parivartana`, `configuration`, `yoga`, `dosha`,
  `bhavat_bhavam_amplifier`, `nakshatra_semantic`, `sudarshana_agreement`,
  `varga_ratification_divergence`, `arudha`, `special_lagna`, `dhana_axis`,
  `vargottama_amplification`) — all SERVED via `judgment_query`, `yoga_activation_by_dasha`,
  `query_signals`, `call_priority_ranking`. E4's real, counter-to-the-plan finding: this is the
  ONLY populated, shared signal-class column found across `bodha_*`/`kala_*`/`phala_*` — "no
  UNIFIED cross-plane signal-class registry" is the accurate framing, not a flat absence claim.
- **16 dark L2 tables, all NEEDS-OWNER, none INTERNAL-BY-DESIGN:** `bodha_anomalies` (4954 rows),
  `bodha_cdlm_domain_rollups` (60), `bodha_cdlm_evolution_gradients` (0), `bodha_cdlm_pattern_clusters`
  (10), `bodha_cgm_chart_topology_summary` (10), `bodha_cgm_edges` (1573), `bodha_cgm_nodes` (649),
  `bodha_cgm_sub_graphs` (10), `bodha_contradictions` (23), `bodha_convergence` (60),
  `bodha_rm_chart_summary` (10), `bodha_rm_dasha_windowed_prescriptions` (0),
  `bodha_rm_dosha_remedy_bundles` (0), `bodha_rm_pattern_remedies` (90), `bodha_signal_embeddings`
  (85,997 — estimate), `bodha_triangulation` (200). See `DARK_SET_WIRING_PLAN_v1_0.md` for the
  proposed wiring shape on the highest-value items (RM prescriptions, CDLM rollup tiers,
  triangulation, CGM sub-graphs — the last flagged as **likely already served**, matching the
  GT-51 false-dark pattern, pending a platform-mcp-directory re-scan).

L2 also serves 17 tool capabilities (`graha_portrait`, `query_cdlm_summary`, `query_cgm_motifs`/
`query_cgm_paths`, `query_chart_gestalt`, `query_contradictions`, `query_discoveries`,
`query_domain_reading`, `query_pratijna`, `query_quality_scorecard`, `query_question_lenses`,
`query_remedies`, `query_rm_prescriptions`/`query_rm_resonances`, `query_signals`, `query_ucd`,
`traverse_chart_graph`, `classical_attribution_lookup`) plus the L-DOMAIN/L-JUDGMENT/L-PACT
cross-domain umbrella family.

## Layer L3 — Kāla (3 dark tables + 2 dark services)

- **3 dark tables:** `kala_activation_predicates` (78,996 rows, estimate — NEEDS-OWNER),
  `kala_convergence_staging` (0 rows — INTERNAL-BY-DESIGN, `_staging` suffix pattern),
  `kala_gochara_windows` (5 rows — NEEDS-OWNER).
- **2 dark services, both plan-settled dispositions carried forward (GT-49/GT-50), NOT
  re-derived:** `kala_timeline` — DARK-UNWIRED, "one-line fix, not a build gap" (handler exists,
  never imported into `server.ts`). `ka_graha_sancara` (`call_ephemeris_at_t`) — DARK SERVICE, the
  single highest-impact coverage item found this wave; `call_service_wrappers.ts:196-214`
  unconditionally returns "not yet wired to a compute sidecar endpoint". Full design proposal at
  `platform/src/lib/retrieval/registry/service_manifest/DESIGN_KA_GRAHA_SANCARA_WIRING.md` — see
  TOOL_SHAPE_DESIGN.md worked example (c) in this packet.
- **A second, undocumented dark service found this wave (not in GT-50):** `ka_muhurta_seva`
  (`call_muhurta_score`) — same stub shape, same file, flagged in `service_manifest.json`'s
  `dark_set` but not GT-50-named.

L3 serves 13 temporal tool capabilities (dasha eligibility, ephemeris-at-t stub, muhurta-score
stub, priority ranking, transit search, activation waveform, convergence windows, dasha dossier,
life arc, obstruction periods, projections, temporal activation/view).

## Layer L5 — Mīmāṃsā (19 dark tables, the two largest DARK tables in the whole 77-row set)

19 dark `mimamsa_*` tables: 6 INTERNAL-BY-DESIGN bookkeeping/log tables
(`mimamsa_adjudication_log`, `mimamsa_calibration_snapshot`, `mimamsa_export_log`,
`mimamsa_pool_contributions`, `mimamsa_resonance_feedback`, `mimamsa_snapshot_cosign`) + 13
NEEDS-OWNER, including the two largest DARK tables in the entire 77-row set:
`mimamsa_fact_adjustment` (121,100 rows, estimate) and `mimamsa_signal_adjustment` (97,504 rows,
estimate). Per CLAUDE.md §E, L5 is SEALED in STRUCTURAL mode — these two are almost certainly the
row-level calibration deltas the already-live `mimamsa_calibration_get`/`mimamsa_insight_get`
umbrella tools aggregate over, i.e. likely correctly INTERNAL-BY-DESIGN, not a coverage gap — but
this is NOT independently verified per-table and needs the L5 seal-owner's sign-off before any new
leaf tool is built against these calibration-ledger internals (B.1/B.10 caution).

L5 serves 6 tool capabilities (`lel_query`, `query_calibration`, `query_insights`,
`query_manifestation_grammar`, `query_predictions`, `query_signal_families`).

## Services plane — the Python sidecar (20 routers / 49 endpoints + `/health` = 50)

`service_manifest.json` (W1 Lane L1c) — real router/endpoint count, mechanically cross-checked
against a live `GET /openapi.json` snapshot (200 OK, 71KB, exact match, 0 missing/extra). The
plan's own "~12 routers" estimate undercounts by ~8 routers (40%+). Two dark services live in this
plane (`ka_graha_sancara`, `ka_muhurta_seva`), both single-Cloud-Run-process (no per-router
concurrency isolation exists — `--concurrency` flag absent from `deploy.yml`, platform default 80/
instance applies undifferentiated). Two orphaned-artifact findings beyond the GT-50 ask, flagged
not fixed: a dead `pyjhora_adapter.main:app` Docker CMD referencing a `main.py` that has never
existed in this repo's history; several `l4_*`-prefixed router files defined but never
`include_router()`'d.

## Roll-up (all real, cross-checked against `ADJUDICATION_QUEUE.md`'s summary block)

| | count |
|---|---:|
| Live capabilities (`getCatalog()`) | **118** |
| Live `chart_facts.fact_category` values | **218** (152 documented, 66 served-undocumented, 0 planner-known) |
| Real DARK tables (zero TS-registry route) | **77** (24 INTERNAL-BY-DESIGN, 2 SERVED-corrected, 51 NEEDS-OWNER) |
| DRIFT (declared table_hint, no real table) | **0** (positive result, post backtick-scan fix) |
| Confirmed cross-plane `signal_class` values | **19** (`bodha_msr_signals.signal_type_class`) |
| DARK tables by layer | L0=29, L1=10, L2=16, L3=3, L5=19 |
| Sidecar routers / endpoints | **20 / 49** (+`/health`=50) |
| concept_ledger rows staged (not yet live) | **355** (218 + 19 + 118) |

---

*End of ASSET_AND_CONCEPT_MAP v1.0 — NATIVE_REVIEW_PACKET_W1, deliverable 1/5.*
