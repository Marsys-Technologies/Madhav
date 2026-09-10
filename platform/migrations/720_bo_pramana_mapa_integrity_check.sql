-- 720_bo_pramana_mapa_integrity_check.sql
--
-- NIRMĀṆA L2-W3 IMPLEMENT (C12; M-14 layer-wide gap). Adds a real
-- integrity_check_sql for bo_pramana_mapa. Transaction ownership belongs
-- to platform/scripts/migrate.ts. Eleventh migration of L2's 710-729 range.
--
-- bo_pramana_mapa is the terminal Bodha writer -- it reads count(*) from
-- nine other bodha_* tables at build time and stores each as a scorecard
-- column. This is the strongest C12 check pattern this campaign has
-- shipped: a genuine cross-table TRUTH re-derivation, not a self-
-- referential count. All nine were independently verified live to match
-- their live source table's CURRENT count(*) on all three production
-- charts before landing -- this is possible today because nothing in
-- those nine tables has been independently rebuilt since bo_pramana_mapa
-- last ran (the same reason M-14's other checks keep finding pending-
-- rebuild staleness elsewhere: builds are currently HELD/synchronized
-- campaign-wide, not asynchronous).
--
-- Twelve invariants, all independently verified live before landing:
--   1-9. Each of msr_signal_count / cdlm_cell_count / cgm_node_count /
--        cgm_edge_count / rm_resonance_count / rm_prescription_count /
--        embedding_count / convergence_count / contradiction_count
--        equals a live count(*) FROM its source table for that chart_id.
--   10. two_pass_verified_pct / documented_approximation_pct /
--       msr_citation_ref_coverage_pct are all bounded [0, 100].
--   11. linkage_formula_version / resonance_formula_version /
--       convergence_formula_version always equal the current source
--       constants (all "v1.0", brahmagyan/../formulas.py).
--   12. Exactly one scorecard row per chart_id (this writer has no
--       ayanamsha loop -- "the scorecard is chart-scoped").
--
-- Deliberately NOT checked:
--   - salience_formula_version: live data shows "v2.0" on 2 charts but
--     "v2" on the third -- a real inconsistency (stale pre-cleanup value
--     on one chart), not a corruption this check exists to catch. C12
--     forbids asserting a value currently false on 1/3 of production data.
--   - centrality_formula_version: NULL on all 3 live rows -- never
--     populated by this writer path; not a load-bearing assertion either
--     way.
--   - no_pre_answer_pass / ledger_independence_pass /
--     discovery_not_fabricated_pass: NULL on all 3 live rows. This is the
--     CORRECT §N.8 behaviour (an honest null beats an invented judgment
--     when a detector hasn't run) -- not a defect, just incomplete
--     detector coverage, so nothing to assert here either way.

UPDATE asset_registry
   SET integrity_check_sql = $ic$
SELECT
  NOT EXISTS (
    SELECT 1 FROM synthesis_quality_scorecard s
    WHERE s.msr_signal_count != (SELECT count(*) FROM bodha_msr_signals m WHERE m.chart_id = s.chart_id)
  )
  AND NOT EXISTS (
    SELECT 1 FROM synthesis_quality_scorecard s
    WHERE s.cdlm_cell_count != (SELECT count(*) FROM bodha_cdlm_cells c WHERE c.chart_id = s.chart_id)
  )
  AND NOT EXISTS (
    SELECT 1 FROM synthesis_quality_scorecard s
    WHERE s.cgm_node_count != (SELECT count(*) FROM bodha_cgm_nodes n WHERE n.chart_id = s.chart_id)
  )
  AND NOT EXISTS (
    SELECT 1 FROM synthesis_quality_scorecard s
    WHERE s.cgm_edge_count != (SELECT count(*) FROM bodha_cgm_edges e WHERE e.chart_id = s.chart_id)
  )
  AND NOT EXISTS (
    SELECT 1 FROM synthesis_quality_scorecard s
    WHERE s.rm_resonance_count != (SELECT count(*) FROM bodha_rm_resonances r WHERE r.chart_id = s.chart_id)
  )
  AND NOT EXISTS (
    SELECT 1 FROM synthesis_quality_scorecard s
    WHERE s.rm_prescription_count != (SELECT count(*) FROM bodha_rm_remedy_prescriptions r WHERE r.chart_id = s.chart_id)
  )
  AND NOT EXISTS (
    SELECT 1 FROM synthesis_quality_scorecard s
    WHERE s.embedding_count != (SELECT count(*) FROM bodha_signal_embeddings e WHERE e.chart_id = s.chart_id)
  )
  AND NOT EXISTS (
    SELECT 1 FROM synthesis_quality_scorecard s
    WHERE s.convergence_count != (SELECT count(*) FROM bodha_convergence c WHERE c.chart_id = s.chart_id)
  )
  AND NOT EXISTS (
    SELECT 1 FROM synthesis_quality_scorecard s
    WHERE s.contradiction_count != (SELECT count(*) FROM bodha_contradictions c WHERE c.chart_id = s.chart_id)
  )
  AND NOT EXISTS (
    SELECT 1 FROM synthesis_quality_scorecard
    WHERE two_pass_verified_pct < 0 OR two_pass_verified_pct > 100
       OR documented_approximation_pct < 0 OR documented_approximation_pct > 100
       OR msr_citation_ref_coverage_pct < 0 OR msr_citation_ref_coverage_pct > 100
  )
  AND NOT EXISTS (
    SELECT 1 FROM synthesis_quality_scorecard
    WHERE linkage_formula_version != 'v1.0'
       OR resonance_formula_version != 'v1.0'
       OR convergence_formula_version != 'v1.0'
  )
  AND NOT EXISTS (
    SELECT chart_id FROM synthesis_quality_scorecard GROUP BY chart_id HAVING count(*) > 1
  )
$ic$
 WHERE asset_id = 'bo_pramana_mapa';
