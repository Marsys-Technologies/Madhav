-- ─────────────────────────────────────────────────────────────────────────────
-- 230_bodha_registry_reconcile.sql
-- B5 reconciliation: update asset_registry count_sql + target_table for all
-- 8 bo_* assets to match the spec tables created in migration 226.
--
-- Prior state: count_sql pointed to legacy tables (bodha_signals, bodha_graph,
-- bodha_graph_edges, bodha_domain_links, bodha_remediation, bodha_resonance)
-- which were NOT the migration-226 spec tables.
--
-- This migration pins each asset to its canonical spec table and the correct
-- chart-scoped count_sql that the cockpit stats route reads.
--
-- Canonical chart_id for cockpit display:
--   482012f1-710e-4a25-994a-93821f5871aa  (Abhisek Mohanty, FORENSIC 7/7 native)
-- ─────────────────────────────────────────────────────────────────────────────

-- bo_laksana → bodha_msr_signals
UPDATE asset_registry
SET
  count_sql       = 'SELECT count(*) FROM bodha_msr_signals WHERE chart_id = ''482012f1-710e-4a25-994a-93821f5871aa''',
  target_table    = 'bodha_msr_signals',
  target_floor    = 0,
  description     = 'L2 Bodha root: MSR Signal Store — projects ga_structural L1 facts into bodha_msr_signals via salience_formula_v1'
WHERE asset_id = 'bo_laksana';

-- bo_bimba → bodha_cgm_nodes
UPDATE asset_registry
SET
  count_sql       = 'SELECT count(*) FROM bodha_cgm_nodes WHERE chart_id = ''482012f1-710e-4a25-994a-93821f5871aa''',
  target_table    = 'bodha_cgm_nodes',
  target_floor    = 0,
  description     = 'L2 Bodha: CGM nodes (one per unique entity: graha/bhava/domain per ayanamsha)'
WHERE asset_id = 'bo_bimba';

-- bo_karanajala → bodha_cgm_edges (primary) + bodha_contradictions
UPDATE asset_registry
SET
  count_sql       = 'SELECT count(*) FROM bodha_cgm_edges WHERE chart_id = ''482012f1-710e-4a25-994a-93821f5871aa''',
  target_table    = 'bodha_cgm_edges',
  target_floor    = 0,
  description     = 'L2 Bodha: CGM edges (aspect/conjunction/yoga→domain) + contradiction pairs'
WHERE asset_id = 'bo_karanajala';

-- bo_samskara → bodha_signal_embeddings
UPDATE asset_registry
SET
  count_sql       = 'SELECT count(*) FROM bodha_signal_embeddings WHERE chart_id = ''482012f1-710e-4a25-994a-93821f5871aa''',
  target_table    = 'bodha_signal_embeddings',
  target_floor    = 0,
  description     = 'L2 Bodha: deterministic signal embeddings (1:1 with bodha_msr_signals, placeholder_hash_v1)'
WHERE asset_id = 'bo_samskara';

-- bo_sangati → bodha_cdlm_cells (primary) + bodha_convergence
UPDATE asset_registry
SET
  count_sql       = 'SELECT count(*) FROM bodha_cdlm_cells WHERE chart_id = ''482012f1-710e-4a25-994a-93821f5871aa''',
  target_table    = 'bodha_cdlm_cells',
  target_floor    = 0,
  description     = 'L2 Bodha: Cross-Domain Linkage Matrix cells + convergence density rows'
WHERE asset_id = 'bo_sangati';

-- bo_upaya → bodha_rm_resonances (primary) + bodha_rm_remedy_prescriptions
UPDATE asset_registry
SET
  count_sql       = 'SELECT count(*) FROM bodha_rm_resonances WHERE chart_id = ''482012f1-710e-4a25-994a-93821f5871aa''',
  target_table    = 'bodha_rm_resonances',
  target_floor    = 0,
  description     = 'L2 Bodha: Remediation Map — resonance scores + G27-grounded prescriptions'
WHERE asset_id = 'bo_upaya';

-- bo_samvada → vw_chart_digest (view; count via underlying MSR signals)
UPDATE asset_registry
SET
  count_sql       = 'SELECT count(*) FROM vw_chart_digest WHERE chart_id = ''482012f1-710e-4a25-994a-93821f5871aa''',
  target_table    = 'vw_chart_digest',
  target_floor    = 0,
  description     = 'L2 Bodha: UCD read surface — vw_chart_digest view + query_ucd retrieval tool'
WHERE asset_id = 'bo_samvada';

-- bo_pramana_mapa → synthesis_quality_scorecard (chart-scoped count)
UPDATE asset_registry
SET
  count_sql       = 'SELECT count(*) FROM synthesis_quality_scorecard WHERE chart_id = ''482012f1-710e-4a25-994a-93821f5871aa''',
  target_table    = 'synthesis_quality_scorecard',
  target_floor    = 0,
  description     = 'L2 Bodha: terminal scorecard + MV refresh — synthesis_quality_scorecard'
WHERE asset_id = 'bo_pramana_mapa';

-- ── Confirm update ─────────────────────────────────────────────────────────────
-- After this migration, all 8 bo_* assets should have:
--   count_sql → pointing to the new spec tables / vw_chart_digest
--   target_table → canonical spec table name
--   target_floor → 0 (set to achieved count after first build, per §N.4)
DO $$
DECLARE
  missing_count INT;
BEGIN
  SELECT count(*) INTO missing_count
  FROM asset_registry
  WHERE asset_id IN (
    'bo_laksana','bo_bimba','bo_karanajala','bo_samskara',
    'bo_sangati','bo_upaya','bo_samvada','bo_pramana_mapa'
  )
  AND (target_table IS NULL OR count_sql IS NULL);

  IF missing_count > 0 THEN
    RAISE WARNING '230_bodha_registry_reconcile: % bo_* assets still missing count_sql or target_table. Check that asset_ids exist.', missing_count;
  ELSE
    RAISE NOTICE '230_bodha_registry_reconcile: all 8 bo_* assets reconciled OK.';
  END IF;
END $$;
