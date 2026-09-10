-- Migration 603: retire the resolved ka_sangam conflation documentation sentinel.
--
-- Migration 389 inserted `_bug_ka_sangam_confidence_conflation` even though its
-- own contract said "Do NOT seed as a constant". The source defect was fixed in
-- the ka_sangam writer by commit b672324fff: confidence_score is now derived from
-- independent-current count while convergence_score remains alignment strength.
-- A later governed rebuild completed with 1,580 ka_sangam rows and direct
-- PostgreSQL verification (STATE_D-3.md cycle2b_rebuild). The canonical
-- bg_formula_constants writer in this release also stops seeding the sentinel.
-- The other 17 governed constants are deliberately untouched.
--
-- Transaction ownership: platform/scripts/migrate.ts wraps this file and the
-- _migrations_applied ledger insert in one transaction. This file must not issue
-- BEGIN or COMMIT independently.

DO $$
DECLARE
  sentinel RECORD;
  registry RECORD;
  deleted_rows INTEGER := 0;
  remaining_rows INTEGER := 0;
BEGIN
  SELECT
    constant_id,
    value_jsonb,
    class,
    consumer_assets,
    citation_or_ratification,
    calibratable,
    bounds,
    version
  INTO sentinel
  FROM brahma_formula_constants
  WHERE constant_id = '_bug_ka_sangam_confidence_conflation'
  FOR UPDATE;

  IF FOUND THEN
    IF sentinel.value_jsonb IS DISTINCT FROM
         '{"bug":"ka_sangam stores confidence as convergence score (0-1) but this field is not a prediction confidence — it is a dasha/transit alignment strength. These are different quantities.","fix":"W4A: separate convergence_strength from prediction_confidence in ka_sangam output","status":"OPEN"}'::jsonb
       OR sentinel.class IS DISTINCT FROM 'conflation_bug'
       OR sentinel.consumer_assets IS DISTINCT FROM ARRAY[]::TEXT[]
       OR sentinel.citation_or_ratification IS DISTINCT FROM
         'W1_SEED_PACKAGE_v1_0 §7 BA_MASTER C10: CONFLATION-BUG — fix at source in W4A. Do NOT seed as a constant.'
       OR sentinel.calibratable IS DISTINCT FROM false
       OR sentinel.bounds IS NOT NULL
       OR sentinel.version IS DISTINCT FROM '1.0'
    THEN
      RAISE EXCEPTION
        'migration 603 refuses unknown formula-constant sentinel contract';
    END IF;

    DELETE FROM brahma_formula_constants
    WHERE constant_id = '_bug_ka_sangam_confidence_conflation'
      AND value_jsonb =
        '{"bug":"ka_sangam stores confidence as convergence score (0-1) but this field is not a prediction confidence — it is a dasha/transit alignment strength. These are different quantities.","fix":"W4A: separate convergence_strength from prediction_confidence in ka_sangam output","status":"OPEN"}'::jsonb
      AND class = 'conflation_bug'
      AND consumer_assets = ARRAY[]::TEXT[]
      AND citation_or_ratification =
        'W1_SEED_PACKAGE_v1_0 §7 BA_MASTER C10: CONFLATION-BUG — fix at source in W4A. Do NOT seed as a constant.'
      AND calibratable = false
      AND bounds IS NULL
      AND version = '1.0';

    GET DIAGNOSTICS deleted_rows = ROW_COUNT;
    IF deleted_rows <> 1 THEN
      RAISE EXCEPTION
        'migration 603 expected to retire exactly one formula-constant sentinel, retired %',
        deleted_rows;
    END IF;
  ELSIF EXISTS (
    SELECT 1 FROM brahma_formula_constants WHERE class = 'conflation_bug'
  ) THEN
    RAISE EXCEPTION
      'migration 603 refuses unknown formula-constant sentinel contract';
  END IF;

  SELECT target_floor, count_sql, COALESCE(volume_explanation, '') AS volume_explanation,
         COALESCE(english_description, '') AS english_description
  INTO registry
  FROM asset_registry
  WHERE asset_id = 'bg_formula_constants'
  FOR UPDATE;

  IF NOT FOUND THEN
    RAISE EXCEPTION 'migration 603 requires bg_formula_constants registry row';
  END IF;

  IF (
    (
      registry.target_floor IS NULL
      AND registry.count_sql =
        'SELECT COUNT(*) FROM brahma_formula_constants WHERE class != ''conflation_bug'''
      AND registry.volume_explanation = ''
      AND registry.english_description =
        'Canonical formula constants registry — combustion orbs, obstruction thresholds, magnitude tiers, dignity scores, house weights, attention budget, and engineering constants. Classes: CLASSICAL (cite, never tune) | NATIVE_JUDGMENT (versioned, L5-calibratable) | ENGINEERING | CONFLATION_BUG.'
    )
    OR
    (
      registry.target_floor = 14
      AND registry.count_sql = 'SELECT count(*) FROM brahma_formula_constants'
      AND registry.volume_explanation =
        'Live-measured 14 constants, 2026-07-05 (grows as new formula constants are registered, e.g. migration 408 mi_pramana_dropped_dimensions).'
      AND registry.english_description =
        'Canonical formula constants registry — combustion orbs, obstruction thresholds, dignity scores, house weights, attention budget, calibration constants. Classified CLASSICAL/NATIVE_JUDGMENT/ENGINEERING/CONFLATION_BUG (migration 389).'
    )
    OR
    (
      registry.target_floor = 17
      AND registry.count_sql = 'SELECT count(*) FROM brahma_formula_constants'
      AND registry.volume_explanation =
        '17 governed constants after migration 603 retires the resolved non-operational ka_sangam conflation sentinel. The table remains accretive only through reviewed formula-constant migrations.'
      AND registry.english_description =
        'Canonical formula constants registry — combustion orbs, obstruction thresholds, dignity scores, house weights, attention budget, and calibration constants. Current governed rows are CLASSICAL/NATIVE_JUDGMENT/ENGINEERING; unresolved defects must not be operationalized as constants.'
    )
  ) IS NOT TRUE THEN
    RAISE EXCEPTION
      'migration 603 refuses unknown bg_formula_constants registry contract';
  END IF;

  UPDATE asset_registry
  SET target_floor = 17,
      count_sql = 'SELECT count(*) FROM brahma_formula_constants',
      volume_explanation =
        '17 governed constants after migration 603 retires the resolved non-operational '
        'ka_sangam conflation sentinel. The table remains accretive only through '
        'reviewed formula-constant migrations.',
      english_description =
        'Canonical formula constants registry — combustion orbs, obstruction thresholds, '
        'dignity scores, house weights, attention budget, and calibration constants. '
        'Current governed rows are CLASSICAL/NATIVE_JUDGMENT/ENGINEERING; unresolved '
        'defects must not be operationalized as constants.'
  WHERE asset_id = 'bg_formula_constants';

  IF NOT FOUND THEN
    RAISE EXCEPTION 'migration 603 requires bg_formula_constants registry row';
  END IF;

  SELECT target_floor, count_sql, COALESCE(volume_explanation, '') AS volume_explanation,
         COALESCE(english_description, '') AS english_description
  INTO registry
  FROM asset_registry
  WHERE asset_id = 'bg_formula_constants';

  IF registry.target_floor IS DISTINCT FROM 17
     OR registry.count_sql IS DISTINCT FROM 'SELECT count(*) FROM brahma_formula_constants'
     OR registry.volume_explanation IS DISTINCT FROM
       '17 governed constants after migration 603 retires the resolved non-operational ka_sangam conflation sentinel. The table remains accretive only through reviewed formula-constant migrations.'
     OR registry.english_description IS DISTINCT FROM
       'Canonical formula constants registry — combustion orbs, obstruction thresholds, dignity scores, house weights, attention budget, and calibration constants. Current governed rows are CLASSICAL/NATIVE_JUDGMENT/ENGINEERING; unresolved defects must not be operationalized as constants.'
  THEN
    RAISE EXCEPTION 'migration 603 failed bg_formula_constants registry postflight';
  END IF;

  SELECT count(*) INTO remaining_rows FROM brahma_formula_constants;
  IF remaining_rows <> 17 THEN
    RAISE EXCEPTION
      'migration 603 expected 17 governed constants after sentinel retirement, found %',
      remaining_rows;
  END IF;

  IF EXISTS (
    SELECT 1 FROM brahma_formula_constants WHERE class = 'conflation_bug'
  ) THEN
    RAISE EXCEPTION 'migration 603 left a conflation-bug row after retirement';
  END IF;
END
$$;
