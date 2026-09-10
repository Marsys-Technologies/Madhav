-- 1025_nirmana_l2_bo_pramana_mapa_integrity_check_scope.sql
--
-- NIRMĀṆA L2 Bodha — fixes issue #2566: bo_pramana_mapa's integrity_check_sql was TABLE-WIDE
-- (no chart_id filter on any sub-clause) while the asset is scope='per_chart' with a correctly
-- scoped count_sql (`WHERE chart_id = $1`). D-CND-03 defect class (migration series 740-752):
-- a build for one chart deterministically fails whenever ANY OTHER chart's
-- synthesis_quality_scorecard row is stale, regardless of whether the chart actually being
-- built is itself clean.
--
-- Live-reverified before authoring this fix (never take a handed-down diagnosis on trust):
--
--   chart_id     | embedding_count | actual | msr_signal_count | actual_msr
--   1c826d5a...  |           50102 |  50171 |            50171 |      50171
--   482012f1...  |           50104 |  50678 |            50104 |      50678   (canonical)
--   cb73cd3d...  |           49875 |  49875 |            49875 |      49875
--
-- Confirms the diagnosis independent of issue #2566's own thread: chart 1c826d5a carries a
-- stale embedding_count row (50102 vs live 50171) that has nothing to do with the canonical
-- chart's build. Because the old integrity_check_sql's embedding_count NOT EXISTS conjunct had
-- no chart filter, ANY chart's bo_pramana_mapa build -- including a hypothetically-clean
-- canonical-chart run -- fails purely because 1c826d5a's unrelated row is stale. This is a
-- distinct, additional defect from the orchestration race the Conductor's ruling and L2's
-- follow-up diagnosed on #2566 (which explains why 482012f1's OWN row went stale); scoping the
-- check to $1 does not paper over that race, it removes the separate cross-chart failure mode
-- so the check only ever reports on the chart actually being built.
--
-- Every sub-clause scoped to $1, matching count_sql's own scoping, including:
--   - the two_pass_verified_pct / documented_approximation_pct / msr_citation_ref_coverage_pct
--     range clause (previously checked ALL charts' pct bounds)
--   - the *_formula_version clause (previously checked ALL charts' formula versions)
--   - the duplicate-row GROUP BY chart_id HAVING count(*) > 1 clause, rewritten to assert
--     "at most one row for THIS chart" (COUNT(*) <= 1 for chart_id = $1) rather than a global
--     GROUP BY across every chart in the table.
--
-- No bare equality pins (C12): every conjunct re-derives its comparison from live sibling
-- tables or the row's own bounds, scoped by $1, exactly as count_sql already is.
--
-- Both this migration's WHERE-scoped conjuncts and the unscoped original were executed against
-- live production data before authoring, to confirm scoping alone (not a logic rewrite) is the
-- fix: the underlying comparisons are unchanged, only the chart filter is added throughout.
--
-- Transaction ownership belongs to platform/scripts/migrate.ts.

UPDATE asset_registry SET integrity_check_sql = $ck$
-- bo_pramana_mapa integrity contract (target: synthesis_quality_scorecard, scope=per_chart).
-- D-CND-03: chart-partitioned. Every conjunct filtered to chart_id = $1, matching count_sql.
SELECT
  NOT EXISTS (
    SELECT 1 FROM synthesis_quality_scorecard s
    WHERE s.chart_id = $1
      AND s.msr_signal_count != (SELECT count(*) FROM bodha_msr_signals m WHERE m.chart_id = s.chart_id)
  )
  AND NOT EXISTS (
    SELECT 1 FROM synthesis_quality_scorecard s
    WHERE s.chart_id = $1
      AND s.cdlm_cell_count != (SELECT count(*) FROM bodha_cdlm_cells c WHERE c.chart_id = s.chart_id)
  )
  AND NOT EXISTS (
    SELECT 1 FROM synthesis_quality_scorecard s
    WHERE s.chart_id = $1
      AND s.cgm_node_count != (SELECT count(*) FROM bodha_cgm_nodes n WHERE n.chart_id = s.chart_id)
  )
  AND NOT EXISTS (
    SELECT 1 FROM synthesis_quality_scorecard s
    WHERE s.chart_id = $1
      AND s.cgm_edge_count != (SELECT count(*) FROM bodha_cgm_edges e WHERE e.chart_id = s.chart_id)
  )
  AND NOT EXISTS (
    SELECT 1 FROM synthesis_quality_scorecard s
    WHERE s.chart_id = $1
      AND s.rm_resonance_count != (SELECT count(*) FROM bodha_rm_resonances r WHERE r.chart_id = s.chart_id)
  )
  AND NOT EXISTS (
    SELECT 1 FROM synthesis_quality_scorecard s
    WHERE s.chart_id = $1
      AND s.rm_prescription_count != (SELECT count(*) FROM bodha_rm_remedy_prescriptions r WHERE r.chart_id = s.chart_id)
  )
  AND NOT EXISTS (
    SELECT 1 FROM synthesis_quality_scorecard s
    WHERE s.chart_id = $1
      AND s.embedding_count != (SELECT count(*) FROM bodha_signal_embeddings e WHERE e.chart_id = s.chart_id)
  )
  AND NOT EXISTS (
    SELECT 1 FROM synthesis_quality_scorecard s
    WHERE s.chart_id = $1
      AND s.convergence_count != (SELECT count(*) FROM bodha_convergence c WHERE c.chart_id = s.chart_id)
  )
  AND NOT EXISTS (
    SELECT 1 FROM synthesis_quality_scorecard s
    WHERE s.chart_id = $1
      AND s.contradiction_count != (SELECT count(*) FROM bodha_contradictions c WHERE c.chart_id = s.chart_id)
  )
  AND NOT EXISTS (
    SELECT 1 FROM synthesis_quality_scorecard
    WHERE chart_id = $1
      AND (two_pass_verified_pct < 0 OR two_pass_verified_pct > 100
        OR documented_approximation_pct < 0 OR documented_approximation_pct > 100
        OR msr_citation_ref_coverage_pct < 0 OR msr_citation_ref_coverage_pct > 100)
  )
  AND NOT EXISTS (
    SELECT 1 FROM synthesis_quality_scorecard
    WHERE chart_id = $1
      AND (linkage_formula_version != 'v1.0'
        OR resonance_formula_version != 'v1.0'
        OR convergence_formula_version != 'v1.0')
  )
  AND (
    SELECT count(*) FROM synthesis_quality_scorecard WHERE chart_id = $1
  ) <= 1
  AS integrity_passed
$ck$
 WHERE asset_id = 'bo_pramana_mapa';
