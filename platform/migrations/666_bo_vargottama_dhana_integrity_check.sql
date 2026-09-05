-- 666_bo_vargottama_dhana_integrity_check.sql
--
-- NIRMĀṆA L2-W3 IMPLEMENT (C12; M-14 layer-wide gap). Adds a real
-- integrity_check_sql for bo_vargottama_dhana. Transaction ownership
-- belongs to platform/scripts/migrate.ts.
--
-- Four real invariants, all independently verified live on all three
-- production charts before landing (C12: never a check that has yet to be
-- green):
--
--   1. dhana_axis tiling: EXACTLY 2 rows per (chart_id, ayanamsha_id) --
--      the writer's own docstring names this ("one row per house, 2 rows
--      minimum per ayanamsha" -- and it never emits more, since houses 2
--      and 11 are the only dhana/labha slots). Verified: 2/2 on all 15
--      (chart x ayanamsha) combinations, no exceptions.
--   2. dhana_axis house guard: configuration_jsonb->>'house' is always 2
--      or 11 -- the tenancy analysis this signal class exists for.
--   3. vargottama_amplification is never vacuous: every row's
--      configuration_jsonb->>'is_vargottama' is true. The writer's own
--      docstring is explicit about this ("fires ONLY when true -- an
--      amplification signal that never amplifies is not a signal"); this
--      check makes that claim falsifiable instead of merely documented.
--   4. vargottama_amplification is bounded and distinct: at most 9 rows
--      per (chart_id, ayanamsha_id) (GRAHAS has 9 candidates,
--      sudarshana_emitter.py:57) and no graha_code repeats within one
--      (chart, ayanamsha) pair -- a real cardinality + distinctness bound,
--      not a count(*) = N pin (this class's real count legitimately
--      varies 0-9 by chart, so no fixed N would ever be honest here).
--
-- Deliberately NOT checked here: the vargottama_amplification COLUMN's
-- own NULL-vs-0.0 state. PR #1847 (D5/§N.7 item 3, not yet merged/rebuilt
-- at the time of writing) changes that column from a hardcoded 0.0 to an
-- honest NULL for vargottama_amplification-class rows specifically --
-- asserting either value here would make this check RED the moment the
-- other PR's rebuild lands, for a column state this migration has no
-- opinion on. Once #1847 is live and bo_vargottama_dhana rebuilds, a
-- follow-up can add that check honestly.

UPDATE asset_registry
   SET integrity_check_sql = $ic$
SELECT
  (
    NOT EXISTS (
      SELECT chart_id, ayanamsha_id
      FROM bodha_msr_signals
      WHERE signal_type_class = 'dhana_axis'
      GROUP BY chart_id, ayanamsha_id
      HAVING count(*) != 2
    )
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_msr_signals
    WHERE signal_type_class = 'dhana_axis'
      AND (configuration_jsonb->>'house')::int NOT IN (2, 11)
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_msr_signals
    WHERE signal_type_class = 'vargottama_amplification'
      AND (configuration_jsonb->>'is_vargottama')::boolean IS NOT TRUE
  )
  AND NOT EXISTS (
    SELECT chart_id, ayanamsha_id
    FROM bodha_msr_signals
    WHERE signal_type_class = 'vargottama_amplification'
    GROUP BY chart_id, ayanamsha_id
    HAVING count(*) > 9 OR count(DISTINCT configuration_jsonb->>'graha_code') != count(*)
  )
$ic$
 WHERE asset_id = 'bo_vargottama_dhana';
