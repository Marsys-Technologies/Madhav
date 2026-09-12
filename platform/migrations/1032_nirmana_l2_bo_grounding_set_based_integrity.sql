-- 1032_nirmana_l2_bo_grounding_set_based_integrity.sql
-- Migration 1032: make bo_grounding's five-invariant detector set-based.
-- Created: 2026-09-12
--
-- The original migration 899 detector used two correlated count(*) subqueries
-- across roughly fifty thousand MSR rows.  On the canonical chart that kept a
-- PostgreSQL backend CPU-active beyond bo_grounding's 600-second writer
-- watchdog, so the otherwise-complete transaction was rolled back.
--
-- This rewrite preserves the complete detector contract:
--   1. grounding tier vocabulary is valid;
--   2. every sruti row carries its earning rule;
--   3. every grounding identity resolves to a source identity;
--   4. every fired yoga in a built chart has exactly one grounding row;
--   5. every MSR signal in a built chart has exactly one grounding row.
--
-- Grounding and source identities are materialized once, then compared with
-- set differences.  No invariant is weakened and the registry timeout
-- remains 600 seconds: the defect is the query shape, not the safety budget.

BEGIN;

DO $MIGRATION$
DECLARE
  current_sql text;
  current_hash text;
  detector_ok boolean;
  updated_count integer;
  new_sql CONSTANT text := $ICHECK$
WITH grounding_identities AS MATERIALIZED (
  SELECT chart_id,
         ayanamsha_id,
         target_kind,
         target_id,
         count(*) AS match_count
    FROM bodha_grounding_matches
   GROUP BY chart_id, ayanamsha_id, target_kind, target_id
),
built_charts AS MATERIALIZED (
  SELECT DISTINCT chart_id
    FROM grounding_identities
),
source_identities AS MATERIALIZED (
  SELECT s.chart_id,
         s.ayanamsha_id,
         'msr_signal'::text AS target_kind,
         s.signal_id::text AS target_id,
         true AS requires_grounding
    FROM bodha_msr_signals s
    JOIN built_charts b ON b.chart_id = s.chart_id
  UNION ALL
  SELECT f.chart_id,
         f.ayanamsha_id,
         'yoga_dosha_firing'::text AS target_kind,
         f.id::text AS target_id,
         f.fired AS requires_grounding
    FROM ga_yoga_firings f
    JOIN built_charts b ON b.chart_id = f.chart_id
)
SELECT
  NOT EXISTS (
    SELECT 1
      FROM bodha_grounding_matches
     WHERE grounding_tier NOT IN ('sruti','yukti','pratyaksa')
  )
  AND NOT EXISTS (
    SELECT 1
      FROM bodha_grounding_matches
     WHERE grounding_tier = 'sruti'
       AND matched_rule_id IS NULL
  )
  AND NOT EXISTS (
    SELECT chart_id, ayanamsha_id, target_kind, target_id
      FROM grounding_identities
    EXCEPT
    SELECT chart_id, ayanamsha_id, target_kind, target_id
      FROM source_identities
  )
  AND NOT EXISTS (
    SELECT chart_id, ayanamsha_id, target_kind, target_id
      FROM source_identities
     WHERE requires_grounding
    EXCEPT
    SELECT chart_id, ayanamsha_id, target_kind, target_id
      FROM grounding_identities
     WHERE match_count = 1
  )
$ICHECK$;
BEGIN
  SELECT integrity_check_sql
    INTO current_sql
    FROM asset_registry
   WHERE asset_id = 'bo_grounding'
   FOR UPDATE;

  IF current_sql IS NULL THEN
    RAISE EXCEPTION 'migration 1032: bo_grounding registry row or integrity detector is missing';
  END IF;

  current_hash := encode(sha256(convert_to(current_sql, 'UTF8')), 'hex');
  IF current_hash NOT IN (
    -- Exact deployed migration-899 detector fingerprint.
    '266ed3d30f63f601f1f5a8f515da147e272d0fcd7f9afe52f8861925d2b2800e',
    -- Idempotent replay after this migration is already installed.
    encode(sha256(convert_to(new_sql, 'UTF8')), 'hex')
  ) THEN
    RAISE EXCEPTION
      'migration 1032: refusing to overwrite unexpected bo_grounding detector fingerprint %',
      current_hash;
  END IF;

  UPDATE asset_registry
     SET integrity_check_sql = new_sql
   WHERE asset_id = 'bo_grounding';
  GET DIAGNOSTICS updated_count = ROW_COUNT;

  IF updated_count <> 1 THEN
    RAISE EXCEPTION 'migration 1032: updated % bo_grounding registry rows, expected exactly 1', updated_count;
  END IF;

  EXECUTE new_sql INTO detector_ok;
  IF detector_ok IS DISTINCT FROM true THEN
    RAISE EXCEPTION 'migration 1032: installed bo_grounding integrity detector is red on current data';
  END IF;
END
$MIGRATION$;

COMMIT;
