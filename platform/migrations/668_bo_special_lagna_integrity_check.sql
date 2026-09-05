-- 668_bo_special_lagna_integrity_check.sql
--
-- NIRMĀṆA L2-W3 IMPLEMENT (C12; M-14 layer-wide gap). Adds a real
-- integrity_check_sql for bo_special_lagna. Transaction ownership belongs
-- to platform/scripts/migrate.ts.
--
-- Three real invariants, all independently verified live on all three
-- production charts before landing (C12: never a check that has yet to
-- be green):
--
--   1. Tiling by NAME, not just count: the writer's own
--      _TARGET_LAGNAS dict (special_lagna_emitter.py:43-48) names exactly
--      four lagnas -- Indu, Sree, Ghati, Hora -- and CR-76 deliberately
--      excludes the other special_lagna facts L1 also carries (Bhava/
--      Varnada/Vighati Lagna). This check verifies the exact SET of four
--      signal_type_ids is present per (chart_id, ayanamsha_id), not just
--      that the count is 4 -- a writer bug that dropped one canonical
--      lagna and duplicated another would still count(*) = 4 but fail
--      this check.
--   2. Classical domain assignment, re-derived from the writer's own
--      docstring/dict rather than restated as a separate literal:
--      GHATI_LAGNA -> career (the authority/timing upapada); the other
--      three (INDU/SREE/HORA) -> wealth. A signal whose domains_affected_
--      array disagrees with its own lagna's classical assignment fails.
--   3. house_d1 range guard: every row's configuration_jsonb->>'house_d1'
--      is in [1, 12].
--
-- Verified live against all three production charts before landing: all
-- three conjuncts evaluate TRUE today.

UPDATE asset_registry
   SET integrity_check_sql = $ic$
SELECT
  (
    NOT EXISTS (
      SELECT 1
      FROM (SELECT DISTINCT chart_id, ayanamsha_id FROM bodha_msr_signals
            WHERE signal_type_class = 'special_lagna') c
      CROSS JOIN unnest(ARRAY['INDU_LAGNA','SREE_LAGNA','GHATI_LAGNA','HORA_LAGNA']) AS lk(lagna_key)
      LEFT JOIN bodha_msr_signals s
        ON s.chart_id = c.chart_id AND s.ayanamsha_id = c.ayanamsha_id
       AND s.signal_type_class = 'special_lagna'
       AND s.signal_type_id = 'special_lagna:' || lk.lagna_key
      WHERE s.signal_id IS NULL
    )
  )
  AND NOT EXISTS (
    SELECT chart_id, ayanamsha_id
    FROM bodha_msr_signals
    WHERE signal_type_class = 'special_lagna'
    GROUP BY chart_id, ayanamsha_id
    HAVING count(*) != 4
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_msr_signals
    WHERE signal_type_class = 'special_lagna'
      AND (
        (signal_type_id = 'special_lagna:GHATI_LAGNA' AND domains_affected_array != ARRAY['career'])
        OR (signal_type_id != 'special_lagna:GHATI_LAGNA' AND domains_affected_array != ARRAY['wealth'])
      )
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_msr_signals
    WHERE signal_type_class = 'special_lagna'
      AND (configuration_jsonb->>'house_d1')::int NOT BETWEEN 1 AND 12
  )
$ic$
 WHERE asset_id = 'bo_special_lagna';
