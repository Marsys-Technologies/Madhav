-- Migration 378: set target_floor=0 for ka_tulana per-chart service writer.
--
-- ka_tulana (cross-pattern prioritization) is a per_chart service writer that
-- emits 0 data rows at build time — it serves data at query time by reading
-- kala_convergence and kala_darshana. Same rationale as migration 377 for
-- ka_dasha_kala: without target_floor=0, asset_runner marks the asset dormant
-- after building any chart, showing a misleading unlit state in the cockpit.
-- Nothing in the L4/L5 DAG declares a hard dep on ka_tulana, so dormant does
-- not block downstream builds — but this fix is correct hygiene.

UPDATE asset_registry
SET target_floor = 0
WHERE asset_id = 'ka_tulana';

-- Sanity check: confirm the row was found.
DO $$
DECLARE
  updated_floor int;
BEGIN
  SELECT target_floor INTO updated_floor
  FROM asset_registry
  WHERE asset_id = 'ka_tulana';

  IF updated_floor IS DISTINCT FROM 0 THEN
    RAISE EXCEPTION
      'migration 378 sanity check failed: ka_tulana.target_floor = %, expected 0.',
      updated_floor;
  END IF;
END $$;
