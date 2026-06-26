-- 345_register_ka_assets.sql
--
-- Back-fill: idempotent registration of all 12 ka_* (L3 Kāla) asset_registry rows
-- + their depends_on edges.
--
-- PROBLEM FIXED: The 12 ka_* rows exist ONLY in prod (seeded by the retired
-- run_ka_*_prod.py path). They are in NO prior migration. topoSort/click-Build
-- depends on these prod-resident edges; a fresh DB cannot reconstruct the L3 DAG.
-- This migration closes that reproducibility gap.
--
-- Source of truth: platform/scripts/seed/asset_registry_seed.ts (ka_* block).
-- Values copied VERBATIM from the seed — do NOT invent or adjust.
--
-- SAFETY:
--   ON CONFLICT (asset_id) DO NOTHING — safe on prod (rows exist) and correct
--   on a fresh DB (rows created from source). NEVER overwrites live prod data.
--   Touches asset_registry ONLY — zero kala_* data tables touched.
--
-- has_writer=true for ALL 12 ka_* (matches migrations 342 + 344).
-- asset_type='service' for the 5 service assets (matches migrations 342 + 344).
-- asset_type='data'    for the 7 artifact assets (default; artifacts use data path).
-- asset_kind='service' for services; asset_kind='artifact' for artifacts.

INSERT INTO asset_registry (
  asset_id,
  layer,
  sort_order,
  sanskrit_name,
  english_name,
  english_description,
  storage_type,
  target_table,
  count_sql,
  size_sql,
  volume_explanation,
  depends_on,
  scope,
  is_active,
  asset_type,
  asset_kind,
  catalog_status,
  layer_name,
  layer_index,
  has_writer
)
VALUES

  -- ── K1 services (4) — global scope, no stored rows ────────────────────────

  (
    'ka_graha_sancara', 'kala', 100,
    'Graha-sañcara', 'Ephemeris service',
    'Ephemeris-at-T service: sidereal positions for all 9 grahas at any datetime. Two read paths: bg_ephemeris (1900–2150) and live swisseph fallback. Per-call memo cache keyed on (T, ayanamsha). TRUE_NODE throughout.',
    'service', NULL, NULL, NULL,
    'Service asset — no stored rows; returns computed positions on demand',
    ARRAY['bg_ephemeris']::text[],
    'global', true, 'service', 'service', 'DRAFT', 'Kāla', 'L3', true
  ),

  (
    'ka_dasha_kala', 'kala', 101,
    'Daśā-kāla', 'Daśā Eligibility Service',
    'Lazy-pruning tree-walk over chart_dashas (level-4 Sookshma) with cross-system agreement scoring. Serves all 7 daśā systems; KP as Vimśottarī sub-level via kp_sublevel column. Nārāyaṇa absent.',
    'service', NULL, NULL, NULL,
    'Service asset — no stored rows; eligibility bands computed on demand from chart_dashas',
    ARRAY['ga_dashas']::text[],
    'per_chart', true, 'service', 'service', 'DRAFT', 'Kāla', 'L3', true
  ),

  (
    'ka_muhurta_seva', 'kala', 102,
    'Muhūrta-sevā', 'Panchāṅga-Muhūrta Service',
    'Deterministic panchāṅga/muhūrta scoring service. Wraps panchang_engine; Tāra Bala native-chart overlay wired (birth_nakshatra_id=25 Purva Bhadrapada). Location mandatory — no silent Bhubaneswar default. 8 event classes including upaya_ritual and sadhana_initiation.',
    'service', NULL, NULL, NULL,
    'Service asset — no stored rows; panchāṅga computed live per (date, location)',
    ARRAY['ka_graha_sancara']::text[],
    'global', true, 'service', 'service', 'DRAFT', 'Kāla', 'L3', true
  ),

  (
    'ka_gochara', 'kala', 103,
    'Gocara', 'Transit-search service',
    'Live-compute transit-event search service (K2 wave). Finds aspect crossings, conjunctions, ingresses, returns, stations, eclipse proximity, multi-planet confluence, and transit-to-transit events using pyswisseph TRUE_NODE. Coarse-to-fine long-horizon search for 50-year windows. Lahiri sidereal throughout.',
    'service', NULL, NULL, NULL,
    'Service asset — no stored rows; transit events computed on demand via pyswisseph',
    ARRAY['bg_ephemeris', 'ka_graha_sancara']::text[],
    'global', true, 'service', 'service', 'DRAFT', 'Kāla', 'L3', true
  ),

  -- ── K-artifact assets (7) — per_chart, table-backed ──────────────────────

  (
    'ka_yojaka', 'kala', 5,
    'Yojaka', 'Activation bridge',
    'Classifies each L2 signal into a signature_class, binds the RATIFIED class template, stores concrete activation predicates for ka_sangam/ka_vighnakara to search. NEVER writes into L2 tables. Per-chart artifact; delete-then-insert idempotency.',
    'postgres_table', 'kala_activation_predicates',
    'SELECT count(*) FROM kala_activation_predicates WHERE chart_id = $1',
    'SELECT pg_total_relation_size(''kala_activation_predicates'')',
    'One predicate per L2 signal per ayanamsha; total ≈ 66,738 for native chart',
    ARRAY['bo_laksana', 'bg_transit_rules', 'ga_dashas']::text[],
    'per_chart', true, 'data', 'artifact', 'DRAFT', 'Kāla', 'L3', true
  ),

  (
    'ka_sangam', 'kala', 2,
    'Saṅgam', 'Convergence engine',
    'Rigor-scored intersection windows (Mode A daśā-prior funnel + Mode B off-daśā sweep). Extends kala_convergence with convergence_score (I-16 multiplicative+saturating), orb-strength (I-17 cos²), rarity_years, confidence_score (I-21), independent_current_count (I-22). THE VALUABLE CORE.',
    'postgres_table', 'kala_convergence',
    'SELECT count(*) FROM kala_convergence WHERE chart_id = $1',
    'SELECT pg_total_relation_size(''kala_convergence'')',
    'Runtime-derived from dasha + transit cluster analysis; count depends on alignment density',
    ARRAY['ka_yojaka', 'ka_dasha_kala', 'ka_gochara', 'ka_muhurta_seva']::text[],
    'per_chart', true, 'data', 'artifact', 'DRAFT', 'Kāla', 'L3', true
  ),

  (
    'ka_vighnakara', 'kala', 3,
    'Vighnakāra', 'Obstruction periods',
    'Obstruction/counter-indicator detector. Identifies malefic transits, daśā veto, panchāṅga obstructions, papakartari that suppress convergence windows. Writes kala_obstruction with severity + override_score.',
    'postgres_table', 'kala_obstruction',
    'SELECT count(*) FROM kala_obstruction WHERE chart_id = $1',
    'SELECT pg_total_relation_size(''kala_obstruction'')',
    'Runtime-derived from transit analysis over sensitive points; count depends on graha configuration',
    ARRAY['ka_sangam', 'ka_gochara', 'ka_muhurta_seva']::text[],
    'per_chart', true, 'data', 'artifact', 'DRAFT', 'Kāla', 'L3', true
  ),

  (
    'ka_kalasutra', 'kala', 1,
    'Kālasūtra', 'Bounded Activation',
    'Bounded activation artifact (1 row per signal×ayanamsha). Fills L2 null hooks (active_dasha_periods, activation_predicted_dates, dasha_activation_proximity_score) at L3. Retires row-per-day kala_timeline. Upstream: ka_yojaka + ka_sangam.',
    'postgres_table', 'kala_activation',
    'SELECT count(*) FROM kala_activation WHERE chart_id = $1',
    'SELECT pg_total_relation_size(''kala_activation'')',
    'One row per signal × ayanamsha; count grows with number of active MSR signals in kala_activation_predicates',
    ARRAY['ka_yojaka', 'ka_sangam']::text[],
    'per_chart', true, 'data', 'artifact', 'DRAFT', 'Kāla', 'L3', true
  ),

  (
    'ka_kala_darshana', 'kala', 6,
    'Kāla-darśana', 'Display-ready temporal view',
    'Display-ready temporal view. Synthesizes kala_convergence + kala_obstruction into effective_score (convergence × obstruction discount), net_label, and structured narrative. Serve-time layer for UI.',
    'postgres_table', 'kala_darshana',
    'SELECT count(*) FROM kala_darshana WHERE chart_id = $1',
    'SELECT pg_total_relation_size(''kala_darshana'')',
    'One display row per convergence window (up to 300 per chart); count depends on ka_sangam output',
    ARRAY['ka_sangam', 'ka_vighnakara', 'ka_kalasutra']::text[],
    'per_chart', true, 'data', 'artifact', 'DRAFT', 'Kāla', 'L3', true
  ),

  (
    'ka_jivana_parva', 'kala', 7,
    'Jīvana-parva', 'Life-arc biographical chapter',
    'Life-arc biographical chapter artifact. Segments native life into daśā-anchored parvas with theme keywords, quality labels (building/peak/consolidating/receding/transitional), and convergence density. Historical characterization, not prediction.',
    'postgres_table', 'kala_jivana_parva',
    'SELECT count(*) FROM kala_jivana_parva WHERE chart_id = $1',
    'SELECT pg_total_relation_size(''kala_jivana_parva'')',
    'One row per mahadasha (typically 9 for a full Vimshottari cycle)',
    ARRAY['ka_kala_darshana', 'ka_dasha_kala']::text[],
    'per_chart', true, 'data', 'artifact', 'DRAFT', 'Kāla', 'L3', true
  ),

  (
    'ka_bhavishya_lekha', 'kala', 8,
    'Bhāviṣya-lekha', 'Probabilistic forward projections',
    'Probabilistic forward projections (3-year horizon). Assigns probability tiers (tier_1_high/tier_2_moderate/tier_3_speculative), domain labels, falsifiability hooks, and calibration records. The testable-prediction artifact per §A mission.',
    'postgres_table', 'kala_bhavishya',
    'SELECT count(*) FROM kala_bhavishya WHERE chart_id = $1',
    'SELECT pg_total_relation_size(''kala_bhavishya'')',
    'Up to 50 ranked projections per chart over a 3-year forward horizon; depends on ka_kala_darshana output',
    ARRAY['ka_kala_darshana', 'ka_vighnakara']::text[],
    'per_chart', true, 'data', 'artifact', 'DRAFT', 'Kāla', 'L3', true
  ),

  -- ── K-service: ka_tulana (5th service; sort_order=9 per seed) ────────────

  (
    'ka_tulana', 'kala', 9,
    'Tulanā', 'Cross-pattern prioritization',
    'Serve-time QT-4 ranking engine. Ranks windows ACROSS patterns and life-domains by I-11 composite (convergence×0.40 + rarity×0.25 + confidence×0.20 + proximity×0.15). Provides head-to-head compare(A,B) with dissonance-aware verdicts (proceed/defer/proceed_with_mitigation) and multi-domain attention map. Pure serve-time: no stored rows.',
    'service', NULL, NULL, NULL,
    'Serve-time service — no stored rows; rankings computed on demand over kala_convergence + kala_darshana.',
    ARRAY['ka_sangam', 'ka_vighnakara', 'ka_kala_darshana']::text[],
    'per_chart', true, 'service', 'service', 'DRAFT', 'Kāla', 'L3', true
  )

ON CONFLICT (asset_id) DO NOTHING;
