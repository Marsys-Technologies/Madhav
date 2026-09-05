-- 712_bo_sangati_integrity_check.sql
--
-- NIRMĀṆA L2-W3 IMPLEMENT (C12; M-14 layer-wide gap). Adds a real
-- integrity_check_sql for bo_sangati. Transaction ownership belongs to
-- platform/scripts/migrate.ts. Third migration of L2's 710-729 range.
--
-- bo_sangati writes two genuinely sparse, chart-data-dependent tables
-- (bodha_cdlm_cells, bodha_convergence -- both loops `continue` on zero
-- signals, so no fixed row count is honest here), but the writer's own
-- construction logic guarantees several real structural invariants
-- regardless of how many rows exist. Eight conjuncts, all independently
-- verified live against all three production charts before landing (C12):
--
-- bodha_cdlm_cells (writers/bo_sangati.py:_build_cdlm_cells):
--   1. domain_row < domain_col always -- combinations(CANONICAL_DOMAINS_
--      SORTED, 2) only ever yields alphabetically-ordered pairs.
--   2. Both domain_row and domain_col are members of the 13-name canonical
--      domain vocabulary (brahmagyan/domain_vocabulary.py), not just the
--      values observed live.
--   3. shared_signal_count = shared_factor_count -- both columns are set
--      from the same `len(shared_ids)` at write time; they must never
--      drift apart even though nothing enforces it at the DB level.
--   4. shared_signal_count is never <= 0 -- the writer's own `if not
--      shared_ids: continue` guarantees a stored cell always has >=1
--      shared signal.
--   5. array_length(shared_signal_ids_array) = shared_signal_count.
--   6. domain_relationship_class TRUTH re-derivation: recomputed here from
--      net_linkage_strength via the writer's own threshold ladder (>=2000
--      strong, >=500 moderate, >0 weak, =0 neutral, else inverse) --
--      catches a wrong-but-legal class a vocabulary check alone would miss.
--   7. top_k_rank_in_snapshot is a contiguous 1..N sequence per (chart_id,
--      ayanamsha_id) group (the writer ranks by computed_strength
--      descending and assigns 1-based ranks with no gaps).
--   8. Rank monotonicity: for consecutive ranks r and r+1 in the same
--      group, computed_linkage_strength never increases -- the ranking
--      the writer computed is actually sorted correctly.
--
-- bodha_convergence (writers/bo_sangati.py:_build_convergence_rows):
--   9. domain is a member of the same 13-name canonical vocabulary.
--   10. convergence_count is never <= 0 -- the writer's `if not sigs:
--       continue` guarantees a stored row always has >=1 signal.
--   11. array_length(top_signal_ids_array) never exceeds 5 -- the writer
--       takes `sorted_sigs[:5]`.
--   12. No duplicate (chart_id, ayanamsha_id, domain) row.
--
-- Deliberately NOT checked: exact row counts (genuinely chart-data-
-- dependent, explicitly documented in the writer's own SPARSITY NOTE) and
-- the numeric formula outputs themselves (linkage_formula_v1 /
-- convergence_formula_v1 -- re-deriving a whole formula here would
-- duplicate the writer, not verify its contract).

UPDATE asset_registry
   SET integrity_check_sql = $ic$
SELECT
  NOT EXISTS (
    SELECT 1 FROM bodha_cdlm_cells WHERE domain_row >= domain_col
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_cdlm_cells
    WHERE domain_row NOT IN (
      'career','wealth','relationship','progeny','health','education',
      'family','residence','travel','spirituality','character','transition','general'
    )
    OR domain_col NOT IN (
      'career','wealth','relationship','progeny','health','education',
      'family','residence','travel','spirituality','character','transition','general'
    )
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_cdlm_cells WHERE shared_signal_count != shared_factor_count
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_cdlm_cells WHERE shared_signal_count <= 0
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_cdlm_cells
    WHERE array_length(shared_signal_ids_array, 1) IS NULL
       OR array_length(shared_signal_ids_array, 1) != shared_signal_count
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_cdlm_cells
    WHERE domain_relationship_class != (
      CASE
        WHEN net_linkage_strength >= 2000 THEN 'positive_strong'
        WHEN net_linkage_strength >= 500 THEN 'positive_moderate'
        WHEN net_linkage_strength > 0 THEN 'positive_weak'
        WHEN net_linkage_strength = 0 THEN 'neutral'
        ELSE 'inverse'
      END
    )
  )
  AND NOT EXISTS (
    SELECT chart_id, ayanamsha_id FROM bodha_cdlm_cells
    GROUP BY chart_id, ayanamsha_id
    HAVING count(*) != count(DISTINCT top_k_rank_in_snapshot)
        OR min(top_k_rank_in_snapshot) != 1
        OR max(top_k_rank_in_snapshot) != count(*)
  )
  AND NOT EXISTS (
    SELECT 1
    FROM bodha_cdlm_cells a
    JOIN bodha_cdlm_cells b
      ON a.chart_id = b.chart_id AND a.ayanamsha_id = b.ayanamsha_id
     AND b.top_k_rank_in_snapshot = a.top_k_rank_in_snapshot + 1
    WHERE a.computed_linkage_strength < b.computed_linkage_strength
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_convergence
    WHERE domain NOT IN (
      'career','wealth','relationship','progeny','health','education',
      'family','residence','travel','spirituality','character','transition','general'
    )
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_convergence WHERE convergence_count <= 0
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_convergence WHERE array_length(top_signal_ids_array, 1) > 5
  )
  AND NOT EXISTS (
    SELECT chart_id, ayanamsha_id, domain FROM bodha_convergence
    GROUP BY 1, 2, 3
    HAVING count(*) > 1
  )
$ic$
 WHERE asset_id = 'bo_sangati';
