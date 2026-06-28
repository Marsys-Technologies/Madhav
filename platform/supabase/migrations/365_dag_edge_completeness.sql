-- 365_dag_edge_completeness.sql
-- ============================================================================
-- DAG EDGE COMPLETENESS CORRECTION (asset_registry.depends_on)
-- ============================================================================
-- Purpose: make `depends_on` a TRUE SUPERSET of each writer's actual data reads,
-- so the build's completeness/consistency invariant holds under the upcoming
-- wave-parallel scheduler. Today the serial sort-order accidentally orders most
-- producers before consumers; under parallelism that accident disappears and any
-- undeclared edge becomes a live "build on incomplete/missing data" violation.
--
-- Method: each added edge below was VERIFIED against the writer source (file:line
-- + the exact table / fact_category read). This migration ADDS edges only — it
-- never removes a declared edge ("spurious" edges are harmless ordering insurance
-- and several become real once writers read chart_facts instead of recomputing).
-- Adds-only is the conservative direction: more gating, never less.
--
-- Producer map for chart_facts (shared table, partitioned by fact_category):
--   graha_position / graha_sign_attributes      -> ga_positions
--   graha_shadbala_* / bhava_bala_* / ashtakavarga_* -> ga_strength
--   upagraha/saham/arudha/karaka_chara/kp_/tajik_    -> ga_sensitive
--   panchanga%                                    -> ga_panchanga
--   sade_sati_*                                   -> ga_sade_sati
--   aspect_/avastha(non-per-varga)/dispositor/special_state_rollup/dignity_per_varga/yoga_karaka_flag -> ga_structural
--   nakshatra joins / tara_bala                   -> ga_nakshatra
--   graha_avastha_*_per_varga (5 baladi/deeptaadi/jagradadi/lajjitadi/sayanadi) -> ga_condition
--   chart_divisionals -> ga_vargas | chart_dashas -> ga_dashas
--   l1_tajik_varsha_year_lords -> ga_tajaka  (NEW producer edge, previously unmodeled)
--
-- KNOWN SEPARATE BUGS surfaced during this audit (NOT fixed here — code, not registry):
--   * ph_muhurta.py:216 reads `FROM ka_vighnakara` — no such table (real table:
--     kala_obstruction). Silently swallowed -> obstruction overlap always empty.
--   * ph_muhurta.py:273 reads `FROM kala_gochara` — no such table (ka_gochara is a
--     SERVICE, no table). Silently swallowed -> transit score always default.
--   The depends_on edges ph_muhurta->ka_vighnakara / ->ka_gochara are still correct
--   intent and are added below; the table-name bugs are tracked separately.
--
-- EXTERNAL (non-asset) dependency, documented for the planner, not added as an edge:
--   * life_event_log / life_events — read by ph_pramana (ph_pramana.py:175) and
--     mi_jivanaghatana; it is an ingest table with NO producing asset. The DAG
--     cannot gate on it; treat as an external precondition.
--
-- Runner note: the migration runner wraps this file in one transaction. No BEGIN/
-- COMMIT, no CREATE INDEX CONCURRENTLY here.
-- ============================================================================

-- ── L1 GAṆITA ───────────────────────────────────────────────────────────────
-- ga_strength reads chart_divisionals (ga_strength_writer.py:1007,1306) -> ga_vargas
UPDATE asset_registry SET depends_on = ARRAY['ga_positions','ga_vargas']::text[]
 WHERE asset_id = 'ga_strength';

-- ga_sade_sati reads chart_facts %tara_bala% (ga_sade_sati_writer.py:1215) -> ga_nakshatra
UPDATE asset_registry SET depends_on = ARRAY['ga_positions','ga_strength','ga_panchanga','ga_vargas','ga_dashas','ga_structural','ga_nakshatra']::text[]
 WHERE asset_id = 'ga_sade_sati';

-- ga_tajaka reads chart_facts 'tajik_triraashipathi' (ga_tajaka_writer.py:345) -> ga_sensitive
UPDATE asset_registry SET depends_on = ARRAY['ga_positions','ga_dashas','ga_sensitive']::text[]
 WHERE asset_id = 'ga_tajaka';

-- ── L2 BODHA ────────────────────────────────────────────────────────────────
-- bo_laksana _FETCH_SQL reads chart_facts with NO fact_category filter
-- (bo_laksana.py:631-637) + chart_divisionals (:1042) -> the COMPLETE L1 fact set.
UPDATE asset_registry SET depends_on = ARRAY['bg_rules','ga_positions','ga_strength','ga_sensitive','ga_panchanga','ga_sade_sati','ga_structural','ga_nakshatra','ga_condition','ga_vargas']::text[]
 WHERE asset_id = 'bo_laksana';

-- bo_karanajala reads chart_facts graha_position (bo_karanajala.py:158-161) -> ga_positions
UPDATE asset_registry SET depends_on = ARRAY['bo_laksana','bo_bimba','ga_positions']::text[]
 WHERE asset_id = 'bo_karanajala';

-- bo_sangati reads bodha_contradictions (bo_sangati.py:134) -> bo_karanajala
UPDATE asset_registry SET depends_on = ARRAY['bo_laksana','bo_karanajala']::text[]
 WHERE asset_id = 'bo_sangati';

-- bo_upaya reads chart_facts: shadbala/bhava_bala (124,140 -> ga_strength),
-- special_state_rollup/dignity_per_varga/yoga_karaka_flag (160,201 -> ga_structural),
-- graha_position/graha_sign_attributes (180,249 -> ga_positions),
-- karaka_chara_position (218 -> ga_sensitive).
UPDATE asset_registry SET depends_on = ARRAY['bo_laksana','bo_sangati','ga_strength','ga_structural','ga_positions','ga_sensitive']::text[]
 WHERE asset_id = 'bo_upaya';

-- bo_samvada CREATE VIEW binds bodha_contradictions(56 -> bo_karanajala),
-- bodha_rm_resonances(60,65 -> bo_upaya), bodha_convergence(74 -> bo_sangati),
-- synthesis_quality_scorecard(81 -> bo_pramana_mapa).
UPDATE asset_registry SET depends_on = ARRAY['bo_laksana','bo_karanajala','bo_upaya','bo_sangati','bo_pramana_mapa']::text[]
 WHERE asset_id = 'bo_samvada';

-- bo_anveshana reads bodha_cgm_nodes (132,335 -> bo_bimba), bodha_msr_signals (131 -> bo_laksana)
UPDATE asset_registry SET depends_on = ARRAY['bo_sangati','bo_karanajala','bo_samskara','bo_drishti','bo_bimba','bo_laksana']::text[]
 WHERE asset_id = 'bo_anveshana';

-- bo_pramana_mapa counts bodha_msr_signals(114 -> bo_laksana), bodha_cdlm_cells/convergence(120,126 -> bo_sangati),
-- bodha_cgm_nodes(121 -> bo_bimba), bodha_cgm_edges/contradictions(122,127 -> bo_karanajala),
-- bodha_signal_embeddings(125 -> bo_samskara).
UPDATE asset_registry SET depends_on = ARRAY['bo_upaya','bo_drishti','bo_anveshana','bo_laksana','bo_sangati','bo_bimba','bo_karanajala','bo_samskara']::text[]
 WHERE asset_id = 'bo_pramana_mapa';

-- bo_chart_gestalt (was []) reads bodha_msr_signals(118 -> bo_laksana), bodha_cdlm_cells(154 -> bo_sangati),
-- bodha_cgm_nodes(166 -> bo_bimba), bodha_cgm_paths(179 -> bo_cgm_paths), bodha_discoveries(281 -> bo_anveshana)
UPDATE asset_registry SET depends_on = ARRAY['bo_laksana','bo_sangati','bo_bimba','bo_cgm_paths','bo_anveshana']::text[]
 WHERE asset_id = 'bo_chart_gestalt';

-- bo_cdlm_summary (was []) reads bodha_cdlm_cells (bo_cdlm_summary.py:106) -> bo_sangati
UPDATE asset_registry SET depends_on = ARRAY['bo_sangati']::text[]
 WHERE asset_id = 'bo_cdlm_summary';

-- bo_cgm_motifs (was []) reads bodha_cgm_nodes(271 -> bo_bimba), bodha_cgm_edges(284 -> bo_karanajala)
UPDATE asset_registry SET depends_on = ARRAY['bo_bimba','bo_karanajala']::text[]
 WHERE asset_id = 'bo_cgm_motifs';

-- bo_cgm_paths (was []) reads bodha_cgm_nodes(218,246 -> bo_bimba), bodha_cgm_edges(232 -> bo_karanajala)
UPDATE asset_registry SET depends_on = ARRAY['bo_bimba','bo_karanajala']::text[]
 WHERE asset_id = 'bo_cgm_paths';

-- ── L3 KĀLA ─────────────────────────────────────────────────────────────────
-- ka_yojaka reads bodha_cgm_nodes(130 -> bo_bimba), bodha_cdlm_cells(165 -> bo_sangati)
UPDATE asset_registry SET depends_on = ARRAY['bo_laksana','bg_transit_rules','ga_dashas','bo_bimba','bo_sangati']::text[]
 WHERE asset_id = 'ka_yojaka';

-- ka_sangam reads bodha_msr_signals(133 -> bo_laksana), chart_dashas(388 -> ga_dashas),
-- chart_facts ashtakavarga_bindu(507 -> ga_strength), l1_tajik_varsha_year_lords(576 -> ga_tajaka),
-- chart_facts LAGNA(623 -> ga_positions), bg_transit_rules(548 -> bg_transit_rules).
UPDATE asset_registry SET depends_on = ARRAY['ka_yojaka','ka_dasha_kala','ka_gochara','ka_muhurta_seva','bo_laksana','ga_dashas','ga_strength','ga_positions','ga_tajaka','bg_transit_rules']::text[]
 WHERE asset_id = 'ka_sangam';

-- ka_kalasutra LEFT JOIN bodha_msr_signals (ka_kalasutra.py:27) -> bo_laksana
UPDATE asset_registry SET depends_on = ARRAY['ka_yojaka','ka_sangam','bo_laksana']::text[]
 WHERE asset_id = 'ka_kalasutra';

-- ka_vighnakara reads chart_facts LAGNA (ka_vighnakara.py:252) -> ga_positions
UPDATE asset_registry SET depends_on = ARRAY['ka_sangam','ka_gochara','ka_muhurta_seva','ga_positions']::text[]
 WHERE asset_id = 'ka_vighnakara';

-- ka_jivana_parva reads kala_convergence(74 -> ka_sangam), kala_activation_predicates(78 -> ka_yojaka),
-- chart_dashas(42,202 -> ga_dashas)
UPDATE asset_registry SET depends_on = ARRAY['ka_kala_darshana','ka_dasha_kala','ka_sangam','ka_yojaka','ga_dashas']::text[]
 WHERE asset_id = 'ka_jivana_parva';

-- ka_bhavishya_lekha JOIN kala_convergence(41 -> ka_sangam), bodha_msr_signals(65 -> bo_laksana)
UPDATE asset_registry SET depends_on = ARRAY['ka_kala_darshana','ka_vighnakara','ka_sangam','bo_laksana']::text[]
 WHERE asset_id = 'ka_bhavishya_lekha';

-- ── L4 PHALA ────────────────────────────────────────────────────────────────
-- ph_nimitta reads bodha_discoveries(221 -> bo_anveshana), bodha_cgm_paths(266 -> bo_cgm_paths),
-- bodha_msr_signals(240 -> bo_laksana)
UPDATE asset_registry SET depends_on = ARRAY['ka_sangam','ka_bhavishya_lekha','bo_bimba','bo_samskara','bo_karanajala','bo_sangati','bo_anveshana','bo_cgm_paths','bo_laksana']::text[]
 WHERE asset_id = 'ph_nimitta';

-- ph_muhurta reads kala_obstruction(216, via ka_vighnakara -> ka_vighnakara), ga_condition_composite(247 -> ga_condition),
-- ka_gochara transit(273 -> ka_gochara), chart_facts LAGNA(390 -> ga_positions). (216/273 table-name bug noted in header.)
UPDATE asset_registry SET depends_on = ARRAY['ph_nimitta','ka_kalasutra','ga_panchanga','ka_vighnakara','ga_condition','ka_gochara','ga_positions']::text[]
 WHERE asset_id = 'ph_muhurta';

-- ph_pratikara LEFT JOIN kala_convergence (ph_pratikara.py:169) -> ka_sangam
UPDATE asset_registry SET depends_on = ARRAY['ph_nimitta','bo_upaya','ka_vighnakara','ka_sangam']::text[]
 WHERE asset_id = 'ph_pratikara';

-- ph_suddha_sodhana reads phala_anchors (ph_suddha_sodhana.py:124) -> ph_nimitta
UPDATE asset_registry SET depends_on = ARRAY['ph_sodhana','ph_nimitta']::text[]
 WHERE asset_id = 'ph_suddha_sodhana';

-- ph_phaladesa reads bodha_msr_signals (ph_phaladesa.py:189,200) -> bo_laksana
UPDATE asset_registry SET depends_on = ARRAY['ph_nimitta','ph_muhurta','ph_pratikara','ph_suddha_sodhana','ph_sankrama','ph_pramana','bo_laksana']::text[]
 WHERE asset_id = 'ph_phaladesa';

-- ── L5 MĪMĀṂSĀ ──────────────────────────────────────────────────────────────
-- mi_bhavisya reads bodha_msr_signals (mi_bhavisya.py:95) -> bo_laksana
UPDATE asset_registry SET depends_on = ARRAY['ph_pramana','ph_nimitta','ph_phaladesa','mi_kula','mi_jivanaghatana','bo_laksana']::text[]
 WHERE asset_id = 'mi_bhavisya';

-- mi_gunanaka reads mimamsa_signal_families (mi_gunanaka.py:70) -> mi_kula
UPDATE asset_registry SET depends_on = ARRAY['mi_pramana','mi_kula']::text[]
 WHERE asset_id = 'mi_gunanaka';

-- mi_adhilepa reads bodha_msr_signals(181 -> bo_laksana), chart_facts(206 -> ga_positions; fact_category
-- IN ('graha','yoga') — base chart_facts, ga_positions is the safe root producer),
-- kala_convergence(231 -> ka_sangam), phala_anchors(251 -> ph_nimitta)
UPDATE asset_registry SET depends_on = ARRAY['mi_gunanaka','bo_laksana','ka_sangam','ph_nimitta','ga_positions']::text[]
 WHERE asset_id = 'mi_adhilepa';

-- mi_sambandha reads mimamsa_manifestation_sets (mi_sambandha.py:60) -> mi_bhavisya
UPDATE asset_registry SET depends_on = ARRAY['mi_pramana','mi_pariksha','mi_bhavisya']::text[]
 WHERE asset_id = 'mi_sambandha';

-- ============================================================================
-- SELF-VALIDATION 1: every declared edge must resolve to a real active asset.
-- ============================================================================
DO $$
DECLARE bad text;
BEGIN
  SELECT string_agg(format('%s -> %s', a.asset_id, dep), ', ')
    INTO bad
  FROM asset_registry a, unnest(a.depends_on) AS dep
  WHERE a.is_active
    AND dep NOT IN (SELECT asset_id FROM asset_registry);
  IF bad IS NOT NULL THEN
    RAISE EXCEPTION 'DAG edge(s) reference unknown asset(s): %', bad;
  END IF;
END $$;

-- ============================================================================
-- SELF-VALIDATION 2: the dependency graph must be ACYCLIC.
-- Walks depends_on transitively; raises if any asset reaches itself.
-- ============================================================================
DO $$
DECLARE cyc text;
BEGIN
  WITH RECURSIVE edges AS (
    SELECT a.asset_id AS node, dep AS reaches
    FROM asset_registry a, unnest(a.depends_on) AS dep
    WHERE a.is_active
  ),
  walk AS (
    SELECT node, reaches FROM edges
    UNION ALL
    SELECT w.node, e.reaches
    FROM walk w JOIN edges e ON e.node = w.reaches
    WHERE w.node <> w.reaches            -- stop expanding a path once it self-loops
  )
  SELECT string_agg(DISTINCT node, ', ') INTO cyc
  FROM walk WHERE node = reaches;
  IF cyc IS NOT NULL THEN
    RAISE EXCEPTION 'DAG cycle detected involving: %', cyc;
  END IF;
END $$;
