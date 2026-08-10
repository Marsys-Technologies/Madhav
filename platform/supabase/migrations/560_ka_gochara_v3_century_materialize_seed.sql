-- Migration 560: asset_registry seed — ka_gochara_v3_century_materialize (W3.4)
-- =============================================================================
-- GOCHARA-UTKARSHA campaign, wave W3.4 (century-horizon heavy writer).
--
-- WHY: The GOCHARA-UTKARSA W3.4 heavy writer
-- (pipeline/orchestrator/writers/ka_gochara_v3_century_materialize.py) is
-- registered via @register('ka_gochara_v3_century_materialize') in the
-- orchestrator's writer registry.  The governance gate
-- test_has_writer_completeness.py requires every registered writer to have
-- a corresponding asset_registry row with has_writer=true.  This migration
-- seeds that row for existing databases (fresh installs get it from
-- asset_registry_seed.ts; this migration is required for prod upgrade).
--
-- WHAT: a single asset_registry INSERT ON CONFLICT for the new asset, plus
-- a depends_on UPDATE to associate it with ka_gochara_resonance.
--
-- IDEMPOTENCY: INSERT ON CONFLICT (asset_id) DO UPDATE — safe to re-apply.
--
-- SCOPE: asset_registry only (catalog/bookkeeping table).
-- No kala_gochara_windows or kala_gochara_windows_v2 rows are touched.
-- =============================================================================

INSERT INTO asset_registry (
    asset_id, layer, sort_order,
    sanskrit_name, english_name, english_description,
    storage_type, target_table, count_sql, size_sql,
    target_floor, scope, is_active, has_writer, has_substeps,
    writer_timeout_seconds,
    layer_name, layer_index, catalog_status
) VALUES (
    'ka_gochara_v3_century_materialize',
    'kala',
    108,
    'Gochara Shatabhdi Matrika (v3)',
    'GOCHARA-UTKARSA Century Materialize (v3, decade slices)',
    'GOCHARA-UTKARSA W3.4 heavy writer: plan_substeps returns 60 substeps '
    '(6 event classes x 10 decade slices spanning birth-century 1984-2084). '
    'Each run_substep calls gochara_v3.interval_solver.find_threshold_crossings '
    'over the decade JD range, applies delta fingerprinting (MD5 of '
    'event_class+era_slice_key+ENGINE_VERSION+resonance_targets) for '
    'skip-on-unchanged semantics, and DELETE-then-INSERTs into '
    'kala_gochara_windows_v2 with era_slice_key=g3_{year_start}_{year_end}. '
    'I2: ZERO imports from gochara_grammar/*, gochara_intensity/*, or '
    'ka_gochara_sweep/*. I4: empty resonance targets -> honest 0 rows, no '
    'fabrication.',
    'postgres_table', 'kala_gochara_windows_v2',
    'SELECT COUNT(*) FROM kala_gochara_windows_v2 WHERE chart_id=$1 AND generation LIKE ''g3_%''',
    NULL,
    0, 'per_chart', true, true, true,
    3600,
    'Kala', 'L3', 'CURRENT'
) ON CONFLICT (asset_id) DO UPDATE SET
    count_sql              = EXCLUDED.count_sql,
    target_table           = EXCLUDED.target_table,
    has_writer             = EXCLUDED.has_writer,
    has_substeps           = EXCLUDED.has_substeps,
    writer_timeout_seconds = EXCLUDED.writer_timeout_seconds,
    sort_order             = EXCLUDED.sort_order,
    english_description    = EXCLUDED.english_description,
    catalog_status         = EXCLUDED.catalog_status;

UPDATE asset_registry
    SET depends_on = ARRAY['ka_gochara_resonance']::text[]
WHERE asset_id = 'ka_gochara_v3_century_materialize';

-- =============================================================================
-- Rollback (manual — no automated down path for asset_registry seed rows):
--   DELETE FROM asset_registry WHERE asset_id = 'ka_gochara_v3_century_materialize';
-- Only safe AFTER the writer is fully decommissioned and the branch retracted.
-- =============================================================================
