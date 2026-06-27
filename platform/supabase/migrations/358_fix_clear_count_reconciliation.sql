-- Migration 358: Reconcile clear count_sql with actual cleared tables (L2 + L5)
--
-- Several L2 Bodha and L5 Mīmāṃsā writers emit more than one table, but the
-- asset_registry count_sql / target_table only referenced one of them. Combined
-- with the single-target_table delete fallback, the secondary tables were never
-- cleared AND were mis-counted, so a layer clear appeared to "not clear" (the
-- residual rows reappeared in the next preview).
--
-- The DELETE completeness is fixed in code (EXPLICIT_CLEAR_OPS in
-- platform/src/lib/cockpit/assetClearSpec.ts — deletes every table each writer
-- emits, FK-child-first). This migration fixes the PREVIEW side so the per-asset
-- count reconciles with what the clear actually deletes:
--   * count_sql now sums exactly the tables the asset's writer emits
--   * mi_adhilepa.target_table is corrected from mimamsa_signal_adjustment
--     (a table it never writes) to mimamsa_load_bearing (its real output)
--
-- All affected assets are scope='per_chart', so every count_sql is chart-scoped.
-- Idempotent: pure UPDATEs of count_sql / target_table.

-- ── L2 Bodha ────────────────────────────────────────────────────────────────

-- bo_karanajala writes bodha_cgm_edges + bodha_contradictions
-- (was counting bodha_cgm_edges + bodha_cgm_paths; bodha_cgm_paths has no writer,
--  and bodha_contradictions was mis-attributed to bo_sangati's count).
UPDATE asset_registry
SET count_sql = 'SELECT (SELECT count(*) FROM bodha_cgm_edges WHERE chart_id = $1) + (SELECT count(*) FROM bodha_contradictions WHERE chart_id = $1) AS count'
WHERE asset_id = 'bo_karanajala';

-- bo_sangati writes bodha_cdlm_cells + bodha_convergence
-- (was also counting bodha_contradictions, which belongs to bo_karanajala).
UPDATE asset_registry
SET count_sql = 'SELECT (SELECT count(*) FROM bodha_cdlm_cells WHERE chart_id = $1) + (SELECT count(*) FROM bodha_convergence WHERE chart_id = $1) AS count'
WHERE asset_id = 'bo_sangati';

-- bo_upaya writes bodha_rm_resonances + bodha_rm_remedy_prescriptions, with
-- bodha_rm_dasha_windowed_prescriptions as a further FK child — count all three.
UPDATE asset_registry
SET count_sql = 'SELECT (SELECT count(*) FROM bodha_rm_resonances WHERE chart_id = $1) + (SELECT count(*) FROM bodha_rm_remedy_prescriptions WHERE chart_id = $1) + (SELECT count(*) FROM bodha_rm_dasha_windowed_prescriptions WHERE chart_id = $1) AS count'
WHERE asset_id = 'bo_upaya';

-- bo_anveshana already counts bodha_discoveries + bodha_anomalies correctly — no change.

-- ── L5 Mīmāṃsā ──────────────────────────────────────────────────────────────

-- mi_bhavisya writes mimamsa_predictions + mimamsa_manifestation_sets
UPDATE asset_registry
SET count_sql = 'SELECT (SELECT count(*) FROM mimamsa_predictions WHERE chart_id = $1) + (SELECT count(*) FROM mimamsa_manifestation_sets WHERE chart_id = $1) AS count'
WHERE asset_id = 'mi_bhavisya';

-- mi_pramana writes mimamsa_calibration + mimamsa_reliability
UPDATE asset_registry
SET count_sql = 'SELECT (SELECT count(*) FROM mimamsa_calibration WHERE chart_id = $1) + (SELECT count(*) FROM mimamsa_reliability WHERE chart_id = $1) AS count'
WHERE asset_id = 'mi_pramana';

-- mi_pariksha writes mimamsa_qa_eval + mimamsa_attribution + mimamsa_discoveries
UPDATE asset_registry
SET count_sql = 'SELECT (SELECT count(*) FROM mimamsa_qa_eval WHERE chart_id = $1) + (SELECT count(*) FROM mimamsa_attribution WHERE chart_id = $1) + (SELECT count(*) FROM mimamsa_discoveries WHERE chart_id = $1) AS count'
WHERE asset_id = 'mi_pariksha';

-- mi_darshana writes mimamsa_insight_units + mimamsa_insight_embeddings
UPDATE asset_registry
SET count_sql = 'SELECT (SELECT count(*) FROM mimamsa_insight_units WHERE chart_id = $1) + (SELECT count(*) FROM mimamsa_insight_embeddings WHERE chart_id = $1) AS count'
WHERE asset_id = 'mi_darshana';

-- mi_adhilepa writes mimamsa_load_bearing — its target_table/count_sql pointed at
-- mimamsa_signal_adjustment (never written by any writer).
UPDATE asset_registry
SET target_table = 'mimamsa_load_bearing',
    count_sql    = 'SELECT count(*) FROM mimamsa_load_bearing WHERE chart_id = $1'
WHERE asset_id = 'mi_adhilepa';
