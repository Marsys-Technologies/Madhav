-- 366_ph_muhurta_kala_sangam_edge.sql
-- ============================================================================
-- Follow-up to 365: the ph_muhurta obstruction-window bug fix now JOINs
-- kala_obstruction -> kala_convergence to recover the temporal window
-- (kala_obstruction has no dates of its own). kala_convergence is produced by
-- ka_sangam, so ph_muhurta gains a DIRECT read of ka_sangam's output. It was
-- already transitively covered (ph_muhurta -> ka_vighnakara -> ka_sangam), but
-- the DAG discipline (and the edge-completeness CI guard) requires declaring
-- direct reads. Adds-only.
-- ============================================================================
UPDATE asset_registry
SET depends_on = ARRAY['ph_nimitta','ka_kalasutra','ga_panchanga','ka_vighnakara','ga_condition','ka_gochara','ga_positions','ka_sangam']::text[]
WHERE asset_id = 'ph_muhurta';

-- Re-assert acyclicity (same guard as 365).
DO $$
DECLARE cyc text;
BEGIN
  WITH RECURSIVE edges AS (
    SELECT a.asset_id AS node, dep AS reaches
    FROM asset_registry a, unnest(a.depends_on) AS dep
    WHERE a.is_active
  ),
  walk AS (
    SELECT node, reaches FROM edges
    UNION ALL
    SELECT w.node, e.reaches FROM walk w JOIN edges e ON e.node = w.reaches
    WHERE w.node <> w.reaches
  )
  SELECT string_agg(DISTINCT node, ', ') INTO cyc FROM walk WHERE node = reaches;
  IF cyc IS NOT NULL THEN
    RAISE EXCEPTION 'DAG cycle detected involving: %', cyc;
  END IF;
END $$;
