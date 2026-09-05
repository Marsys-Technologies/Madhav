-- 716_bo_cdlm_summary_integrity_check.sql
--
-- NIRMĀṆA L2-W3 IMPLEMENT (C12; M-14 layer-wide gap). Adds a real
-- integrity_check_sql for bo_cdlm_summary. Transaction ownership belongs
-- to platform/scripts/migrate.ts. Seventh migration of L2's 710-729 range.
--
-- bo_cdlm_summary's own DESIGN FLOOR NOTE claims "exactly 5 rows per chart"
-- (one per ayanamsha) -- but _write_aya() (writers/bo_cdlm_summary.py:157-
-- 159) skips and returns early when bodha_cdlm_cells is empty for that
-- ayanamsha, so 5 is honestly a floor/target, not an unconditional
-- guarantee (the note's own text: "A count of fewer than 5... valid for
-- sparse charts"). bo_cdlm_cells is itself genuinely sparse (bo_sangati's
-- own SPARSITY NOTE, migration 712). So this check does NOT assert exactly
-- 5 -- it checks what the writer's construction logic DOES guarantee.
--
-- Ten invariants, all independently verified live against all three
-- production charts before landing (C12):
--   1. No duplicate (chart_id, ayanamsha_id) row -- delete-then-insert
--      idempotency, one row max per ayanamsha per chart.
--   2. ayanamsha_id is one of the 5 canonical ayanamshas (CANONICAL_AYAS).
--   3. verification_pass_status is always UNVERIFIED_DEFAULT ('single') --
--      the writer's own honest self-assessment (SAMĀPTI B-VERIFSTATUS-VOCAB
--      audit note in source: nothing here re-derives or cross-checks the
--      row, so per §N.8 it must not claim a stronger tier).
--   4. citation_ref is always the writer's fixed literal
--      'bo_cdlm_summary:aggregation_v1:bodha_cdlm_cells'.
--   5. dominant_3_domains_array is never NULL and never longer than 3
--      elements (dominant_3 = sorted_domains[:3] -- can be shorter for a
--      chart with fewer than 3 connected domains, never longer).
--   6. weakest_3_domains_array is never NULL and never longer than 3
--      elements (same shape, [-3:]).
--   7. chart_typology_class is one of the 5 values the writer's own
--      deterministic decision tree can produce (concentrated,
--      highly_connected, contradictory, asymmetric, distributed) --
--      vocabulary derived from source, not just observed live values.
--   8. total_chart_linkage is never negative (a sum of
--      computed_linkage_strength values, which bo_sangati's own migration
--      712 check already guarantees are non-negative at the source).
--   9. contradiction_density is never negative (a mean of non-negative
--      asymmetry_score values).
--   10. pattern_cluster_markers_jsonb is never NULL and its own
--       total_cells field is always a positive integer -- the writer only
--       reaches the INSERT after confirming bodha_cdlm_cells was non-empty
--       for that ayanamsha (the early-return path never writes a row), so
--       a written row can never claim zero constituent cells.
--
-- Deliberately NOT checked: exact row count per chart (genuinely capped by
-- bo_sangati's own sparsity, not a bo_cdlm_summary defect) and
-- chart_typology_class TRUTH re-derivation (the "concentrated" branch's
-- total_domains <= 2 condition is not reconstructable from any stored
-- column -- domain_connectivity_jsonb is computed in the writer but never
-- inserted, a separate finding not fixed here).

UPDATE asset_registry
   SET integrity_check_sql = $ic$
SELECT
  NOT EXISTS (
    SELECT chart_id, ayanamsha_id FROM bodha_cdlm_chart_summary
    GROUP BY chart_id, ayanamsha_id HAVING count(*) > 1
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_cdlm_chart_summary
    WHERE ayanamsha_id NOT IN (
      'lahiri_chitrapaksha', 'raman', 'krishnamurti',
      'surya_siddhanta_classical', 'true_chitra'
    )
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_cdlm_chart_summary WHERE verification_pass_status != 'single'
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_cdlm_chart_summary
    WHERE citation_ref != 'bo_cdlm_summary:aggregation_v1:bodha_cdlm_cells'
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_cdlm_chart_summary
    WHERE dominant_3_domains_array IS NULL
       OR array_length(dominant_3_domains_array, 1) > 3
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_cdlm_chart_summary
    WHERE weakest_3_domains_array IS NULL
       OR array_length(weakest_3_domains_array, 1) > 3
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_cdlm_chart_summary
    WHERE chart_typology_class NOT IN (
      'concentrated', 'highly_connected', 'contradictory', 'asymmetric', 'distributed'
    )
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_cdlm_chart_summary WHERE total_chart_linkage < 0
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_cdlm_chart_summary WHERE contradiction_density < 0
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_cdlm_chart_summary
    WHERE pattern_cluster_markers_jsonb IS NULL
       OR (pattern_cluster_markers_jsonb->>'total_cells')::int IS NULL
       OR (pattern_cluster_markers_jsonb->>'total_cells')::int <= 0
  )
$ic$
 WHERE asset_id = 'bo_cdlm_summary';
