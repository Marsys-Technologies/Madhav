-- Migration 1343: bo_grounding's integrity detector resolves a yoga grounding row through the firing's STABLE identity.
-- Created: 2026-10-10   (SS N-307; number claimed on the coordination §2)
--
-- WHY. bo_grounding stored str(ga_yoga_firings.id) as `target_id` for yoga rows. That id is a SERIAL, and ga_yoga deletes and re-inserts its
-- firings on every rebuild, so the digested key of identical content changed whenever ga_yoga was rebuilt (output_changed = true on unchanged
-- inputs). The writer now stores the firing's natural key instead: `yoga_canonical_id`, which the table makes UNIQUE per (chart_id, ayanamsha_id)
-- (migration 240). This migration moves the registry's integrity detector (installed by 1032, a set-based rewrite of 899) onto the same identity.
--
-- TRANSITION. Until bo_grounding next rebuilds, the table still holds rows whose target_id is the old serial. The detector therefore resolves a
-- yoga row by EITHER form (hash joins on equality, no OR join) to the firing's yoga_canonical_id and counts them under that one identity, so it
-- reads green before the rebuild (legacy rows), after it (new rows) and never double-counts a firing (two rows for one firing = match_count 2 =
-- red). Every other invariant of 1032 is preserved: tier vocabulary, sruti rows carry their rule, every grounding identity resolves to a source
-- identity, every fired yoga and every MSR signal in a built chart has exactly one grounding row. A follow-up may drop the legacy form once no
-- legacy row remains.
--
-- SAFETY. Fingerprint-guarded and idempotent exactly like 1032: it overwrites ONLY the three known detector texts (899's, 1032's, this one's),
-- refuses anything else, updates exactly one registry row, and the installed detector must be green on current data or the transaction rolls back.

BEGIN;

DO $MIGRATION$
DECLARE
  current_sql text;
  current_hash text;
  detector_ok boolean;
  updated_count integer;
  new_sql CONSTANT text := $ICHECK$
WITH built_charts AS MATERIALIZED (
  SELECT DISTINCT chart_id
    FROM bodha_grounding_matches
),
firing_identities AS MATERIALIZED (
  SELECT f.chart_id,
         f.ayanamsha_id,
         f.yoga_canonical_id,
         f.id::text AS legacy_id,
         f.fired
    FROM ga_yoga_firings f
    JOIN built_charts b ON b.chart_id = f.chart_id
),
grounding_identities AS MATERIALIZED (
  SELECT g.chart_id,
         g.ayanamsha_id,
         g.target_kind,
         COALESCE(fn.yoga_canonical_id, fl.yoga_canonical_id, g.target_id) AS target_id,
         count(*) AS match_count
    FROM bodha_grounding_matches g
    LEFT JOIN firing_identities fn
      ON g.target_kind = 'yoga_dosha_firing'
     AND fn.chart_id = g.chart_id
     AND fn.ayanamsha_id = g.ayanamsha_id
     AND fn.yoga_canonical_id = g.target_id
    LEFT JOIN firing_identities fl
      ON g.target_kind = 'yoga_dosha_firing'
     AND fl.chart_id = g.chart_id
     AND fl.ayanamsha_id = g.ayanamsha_id
     AND fl.legacy_id = g.target_id
   GROUP BY g.chart_id, g.ayanamsha_id, g.target_kind,
            COALESCE(fn.yoga_canonical_id, fl.yoga_canonical_id, g.target_id)
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
  SELECT fi.chart_id,
         fi.ayanamsha_id,
         'yoga_dosha_firing'::text AS target_kind,
         fi.yoga_canonical_id AS target_id,
         fi.fired AS requires_grounding
    FROM firing_identities fi
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
    RAISE EXCEPTION 'migration 1343: bo_grounding registry row or integrity detector is missing';
  END IF;

  current_hash := encode(sha256(convert_to(current_sql, 'UTF8')), 'hex');
  IF current_hash NOT IN (
    -- Exact deployed migration-899 detector fingerprint.
    '266ed3d30f63f601f1f5a8f515da147e272d0fcd7f9afe52f8861925d2b2800e',
    -- Exact migration-1032 (set-based) detector fingerprint.
    'd37370572154ff1216db18f83fa4513d9beb6c9cee6d8c98e30415c665319d78',
    -- Idempotent replay after this migration is already installed.
    encode(sha256(convert_to(new_sql, 'UTF8')), 'hex')
  ) THEN
    RAISE EXCEPTION
      'migration 1343: refusing to overwrite unexpected bo_grounding detector fingerprint %', current_hash;
  END IF;

  UPDATE asset_registry
     SET integrity_check_sql = new_sql
   WHERE asset_id = 'bo_grounding';
  GET DIAGNOSTICS updated_count = ROW_COUNT;

  IF updated_count <> 1 THEN
    RAISE EXCEPTION 'migration 1343: updated % bo_grounding registry rows, expected exactly 1', updated_count;
  END IF;

  EXECUTE new_sql INTO detector_ok;
  IF detector_ok IS DISTINCT FROM true THEN
    RAISE EXCEPTION 'migration 1343: installed bo_grounding integrity detector is red on current data';
  END IF;
END
$MIGRATION$;

COMMIT;
