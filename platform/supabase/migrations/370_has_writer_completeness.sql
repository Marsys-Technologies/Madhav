-- Migration 370 — has_writer completeness: mark all writers discovered by discover_all()
-- Root cause: migration 342 set has_writer=true for assets known at 2026-06-26.
-- Four L2 Bodha assets (bo_cdlm_summary, bo_cgm_motifs, bo_cgm_paths, bo_chart_gestalt)
-- and all 12 L5 Mīmāṃsā (mi_*) assets were added/registered after that sweep and never
-- received has_writer=true.
--
-- Effect of the gap (pre-fix):
--   The plan resolver query (WHERE is_active=true AND has_writer=true) silently excluded
--   all 16 assets. For a global build this means:
--     • L5 (Mīmāṃsā) is entirely absent from the build plan → never built.
--     • bo_cgm_paths is absent → any asset that declared it as a dep via migration 365
--       (e.g. ph_phaladesa) sees an unlit out-of-plan dep → execute_dag blocks it.
--     • bo_chart_gestalt, bo_cdlm_summary, bo_cgm_motifs → missing L2 sub-layers.
--
-- Fix: set has_writer=true for all 16 real writers.
-- bg_nakshatra_medical and bg_transit_engine are sub-registrations sharing a writer with
-- bg_medical_mappings / bg_transit_rules; they are not independent plan-level assets
-- and are intentionally excluded here.

UPDATE asset_registry
SET has_writer = true
WHERE asset_id IN (
  -- L2 Bodha — four assets added after migration 342
  'bo_cdlm_summary',
  'bo_cgm_motifs',
  'bo_cgm_paths',
  'bo_chart_gestalt',
  -- L3 Kāla — ka_tulana omitted from migration 342
  'ka_tulana',
  -- L5 Mīmāṃsā — entire layer omitted from migration 342
  'mi_abhilekha',
  'mi_adhilepa',
  'mi_bhavisya',
  'mi_darshana',
  'mi_gunanaka',
  'mi_jivanaghatana',
  'mi_kula',
  'mi_pariksha',
  'mi_pramana',
  'mi_sambandha',
  'mi_seva',
  'mi_vistara'
);

-- Sanity check: confirm all 17 rows were found in asset_registry.
DO $$
DECLARE
  marked   int;
  expected int := 17;
BEGIN
  SELECT count(*) INTO marked
  FROM asset_registry
  WHERE asset_id IN (
    'bo_cdlm_summary','bo_cgm_motifs','bo_cgm_paths','bo_chart_gestalt',
    'ka_tulana',
    'mi_abhilekha','mi_adhilepa','mi_bhavisya','mi_darshana','mi_gunanaka',
    'mi_jivanaghatana','mi_kula','mi_pariksha','mi_pramana','mi_sambandha',
    'mi_seva','mi_vistara'
  ) AND has_writer = true;

  IF marked <> expected THEN
    RAISE EXCEPTION
      'migration 370 sanity check failed: expected % rows marked has_writer=true, got %.'
      ' Check that all 17 asset_ids exist in asset_registry.',
      expected, marked;
  END IF;
END $$;
