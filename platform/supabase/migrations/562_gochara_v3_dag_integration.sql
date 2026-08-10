-- Migration 562: gochara v3 DAG integration — depends_on, count_sql, target_table
-- =============================================================================
-- GOCHARA-UTKARSHA campaign, wave W5.2 (Nirmana/DAG integration).
--
-- WHY: Migration 560 seeded ka_gochara_v3_century_materialize with
-- depends_on = ARRAY['ka_gochara_resonance'] only.  The v3 writer's true
-- runtime inputs are broader:
--
--   ka_gochara_resonance  — gochara_resonance_map (resonance targets, step 1
--                           of ClassContext.fetch(); already present)
--   ka_vedha_gochara      — kala_vedha_gochara (W1.3 quality_gates, wired
--                           into engine.py via _compute_quality_gates_from_context
--                           + ClassContext.fetch() step 12; first new dependency)
--   ka_moorti_nirnaya     — kala_moorti_nirnaya (W2.2 moorti-nirnaya modifier;
--                           reads pre-built rows via ClassContext)
--   ka_kota_chakra        — kala_kota_chakra (W2.5 kota-chakra ring modifier;
--                           reads pre-built rows via ClassContext)
--   ka_tithi_pravesha     — kala_tithi_pravesha (W2.7b tithi-pravesha annual
--                           tone; reads pre-built rows via ClassContext)
--   bg_sky_calendar       — bg_sky_events (W2.6 real eclipses; reads pre-built
--                           eclipse rows via ClassContext.sky_calendar_rows)
--
-- count_sql for the v3 asset already scopes to era_slice_key LIKE 'g3_%'
-- (migration 560 set it correctly).  This migration re-asserts the same value
-- in the ON CONFLICT branch so the cockpit always reflects §N.4 truth.
--
-- Sibling assets (ka_moorti_nirnaya, ka_vedha_gochara, ka_kota_chakra,
-- ka_tithi_pravesha) already carry correct count_sql pointing at their own
-- kala_* tables with chart_id=$1; verified against seed and confirmed correct.
-- Their UPDATEs below are included as explicit idempotent assertions (no-ops
-- if already correct, correct if something drifted).
--
-- IDEMPOTENCY: All statements use UPDATE ... WHERE, never DROP/TRUNCATE/DELETE.
-- Safe to re-apply.
--
-- SCOPE: asset_registry only.  No kala_gochara_windows,
-- kala_gochara_windows_v2, or any other data table is touched.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 1. Update ka_gochara_v3_century_materialize: add full depends_on set and
--    re-assert count_sql + target_table.
-- ---------------------------------------------------------------------------

UPDATE asset_registry
SET
    depends_on = ARRAY[
        'ka_gochara_resonance',
        'ka_vedha_gochara',
        'ka_moorti_nirnaya',
        'ka_kota_chakra',
        'ka_tithi_pravesha',
        'bg_sky_calendar'
    ]::text[],
    count_sql  = 'SELECT COUNT(*) FROM kala_gochara_windows_v2 WHERE chart_id=$1 AND generation LIKE ''g3_%''',
    target_table = 'kala_gochara_windows_v2'
WHERE asset_id = 'ka_gochara_v3_century_materialize';

-- ---------------------------------------------------------------------------
-- 2. Idempotent assertion: ka_moorti_nirnaya count_sql (correct in seed;
--    re-stated here as an explicit §N.4 cockpit-truth guarantee).
-- ---------------------------------------------------------------------------

UPDATE asset_registry
SET
    count_sql    = 'SELECT COUNT(*) FROM kala_moorti_nirnaya WHERE chart_id=$1',
    target_table = 'kala_moorti_nirnaya'
WHERE asset_id = 'ka_moorti_nirnaya';

-- ---------------------------------------------------------------------------
-- 3. Idempotent assertion: ka_vedha_gochara count_sql.
-- ---------------------------------------------------------------------------

UPDATE asset_registry
SET
    count_sql    = 'SELECT COUNT(*) FROM kala_vedha_gochara WHERE chart_id=$1',
    target_table = 'kala_vedha_gochara'
WHERE asset_id = 'ka_vedha_gochara';

-- ---------------------------------------------------------------------------
-- 4. Idempotent assertion: ka_kota_chakra count_sql.
-- ---------------------------------------------------------------------------

UPDATE asset_registry
SET
    count_sql    = 'SELECT COUNT(*) FROM kala_kota_chakra WHERE chart_id=$1',
    target_table = 'kala_kota_chakra'
WHERE asset_id = 'ka_kota_chakra';

-- ---------------------------------------------------------------------------
-- 5. Idempotent assertion: ka_tithi_pravesha count_sql.
-- ---------------------------------------------------------------------------

UPDATE asset_registry
SET
    count_sql    = 'SELECT COUNT(*) FROM kala_tithi_pravesha WHERE chart_id=$1',
    target_table = 'kala_tithi_pravesha'
WHERE asset_id = 'ka_tithi_pravesha';

-- =============================================================================
-- Rollback (manual — no automated down path for asset_registry changes):
--   UPDATE asset_registry
--     SET depends_on = ARRAY['ka_gochara_resonance']::text[]
--   WHERE asset_id = 'ka_gochara_v3_century_materialize';
-- Only the depends_on widening is material; count_sql/target_table are correct
-- in both states.  Sibling asset UPDATEs are no-ops in both directions.
-- =============================================================================
