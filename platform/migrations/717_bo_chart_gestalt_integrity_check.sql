-- 717_bo_chart_gestalt_integrity_check.sql
--
-- NIRMĀṆA L2-W3 IMPLEMENT (C12; M-14 layer-wide gap). Adds a real
-- integrity_check_sql for bo_chart_gestalt. Transaction ownership belongs
-- to platform/scripts/migrate.ts. Eighth migration of L2's 710-729 range.
--
-- bo_chart_gestalt has TWO documented ANTI-DRIFT fixes in its own source
-- (§N.8 registers F-12 and F-15) that live production data currently
-- violates -- not because the writer is broken, but because this asset
-- has not been rebuilt since either fix landed:
--
--   F-12: domain_verdict_map_jsonb must NEVER carry 'verdict_class' or
--   'confidence' keys per-domain (the writer's own "PRIOR STATE" comment:
--   these were removed because they were derived from a single top-
--   salience row, not the domain's actual evidence). Live check today:
--   100% of rows (15/15) still carry both keys on every domain entry --
--   this asset predates the F-12 fix.
--
--   F-15: headline_epistemic_jsonb's fragility_class must never be the
--   literal 'multi_ayanamsha_tested' (the writer's own "PRIOR STATE"
--   comment: this was a hardcoded per-ayanamsha literal that asserted a
--   cross-ayanamsha claim no single-ayanamsha write could have measured;
--   replaced with None + a real post-loop _assess_fragility() patch).
--   Live check today: all 15 rows still carry the old literal -- this
--   asset predates the F-15 fix too, independently of F-12.
--
-- C12 forbids asserting either fix's contract here (both would be RED on
-- 100% of current data for a reason unrelated to what either check exists
-- to catch -- staleness, not corruption). Both are the same pending-rebuild
-- pattern already on record for other L2 assets this campaign (bo_bimba
-- domain nodes, bo_samskara embeddings, bo_drishti lens_formula_version) --
-- not filed as new findings.
--
-- Eight invariants that ARE universally true today, all independently
-- verified live against all three production charts before landing (C12):
--   1. No duplicate (chart_id, ayanamsha_id) row (delete-then-insert
--      idempotency -- the writer's per-ayanamsha loop can SKIP an
--      ayanamsha with zero MSR signals, so this is a distinctness bound,
--      not a tiling assertion; see the writer's own dry_run note "1 per
--      ayanamsha where MSR signals exist").
--   2. ayanamsha_id is one of the 5 canonical ayanamshas.
--   3. headline_confidence is bounded [0, 1].
--   4. domain_verdict_map_jsonb is never NULL.
--   5. defining_threads_jsonb is never NULL.
--   6. headline_jsonb is never NULL.
--   7. headline_epistemic_jsonb is never NULL.
--   8. gestalt_formula_version and engine_version always equal the
--      writer's own current constants (GESTALT_FORMULA_V, ENGINE_VERSION).

UPDATE asset_registry
   SET integrity_check_sql = $ic$
SELECT
  NOT EXISTS (
    SELECT chart_id, ayanamsha_id FROM bodha_chart_gestalt
    GROUP BY chart_id, ayanamsha_id HAVING count(*) > 1
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_chart_gestalt
    WHERE ayanamsha_id NOT IN (
      'lahiri_chitrapaksha', 'raman', 'krishnamurti',
      'surya_siddhanta_classical', 'true_chitra'
    )
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_chart_gestalt
    WHERE headline_confidence < 0 OR headline_confidence > 1
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_chart_gestalt WHERE domain_verdict_map_jsonb IS NULL
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_chart_gestalt WHERE defining_threads_jsonb IS NULL
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_chart_gestalt WHERE headline_jsonb IS NULL
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_chart_gestalt WHERE headline_epistemic_jsonb IS NULL
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_chart_gestalt
    WHERE gestalt_formula_version != 'gestalt_formula_v1'
       OR engine_version != 'bo_chart_gestalt_v1.0'
  )
$ic$
 WHERE asset_id = 'bo_chart_gestalt';
