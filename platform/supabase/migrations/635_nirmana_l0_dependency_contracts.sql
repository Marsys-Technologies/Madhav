-- Migration 635: correct the three source-backed L0 dependency contracts.
--
-- The normal registry seed intentionally preserves an existing dependency array,
-- so these corrections need an immutable live-registry migration. This migration
-- accepts only the known legacy or already-correct states and refuses all drift.
-- migrate.ts owns the surrounding transaction; do not add BEGIN or COMMIT here.

DO $$
DECLARE
  actual text[];
  missing_sources text;
  missing_targets text;
BEGIN
  -- Lock every source and target before reading its contract. The migration
  -- runner supplies the enclosing transaction, so a concurrent registry change
  -- cannot turn a validated topology into a different update target.
  PERFORM 1
    FROM asset_registry
   WHERE asset_id IN (
     'bg_ghatana', 'bg_panchanga', 'bg_prashna_rules', 'ga_positions',
     'bg_class_lifetime_counts', 'ga_panchanga', 'ga_prashna'
   )
   FOR UPDATE;

  SELECT string_agg(required.asset_id, ', ' ORDER BY required.asset_id)
    INTO missing_sources
    FROM (
      VALUES
        ('bg_ghatana'::text, 'brahmagyan'::text, 'global'::text),
        ('bg_panchanga'::text, 'brahmagyan'::text, 'global'::text),
        ('bg_prashna_rules'::text, 'brahmagyan'::text, 'global'::text),
        ('ga_positions'::text, 'ganita'::text, 'per_chart'::text)
    ) AS required(asset_id, layer, scope)
    LEFT JOIN asset_registry source ON source.asset_id = required.asset_id
   WHERE source.asset_id IS NULL
      OR source.layer IS DISTINCT FROM required.layer
      OR source.scope IS DISTINCT FROM required.scope
      OR source.catalog_status IS DISTINCT FROM 'CURRENT'
      OR source.is_active IS DISTINCT FROM true;
  IF missing_sources IS NOT NULL THEN
    RAISE EXCEPTION 'migration 635 requires CURRENT active source authorities: %', missing_sources;
  END IF;

  SELECT string_agg(required.asset_id, ', ' ORDER BY required.asset_id)
    INTO missing_targets
    FROM (
      VALUES
        ('bg_class_lifetime_counts'::text, 'brahmagyan'::text, 'global'::text),
        ('ga_panchanga'::text, 'ganita'::text, 'per_chart'::text),
        ('ga_prashna'::text, 'ganita'::text, 'per_chart'::text)
    ) AS required(asset_id, layer, scope)
    LEFT JOIN asset_registry target ON target.asset_id = required.asset_id
   WHERE target.asset_id IS NULL
      OR target.layer IS DISTINCT FROM required.layer
      OR target.scope IS DISTINCT FROM required.scope
      OR target.catalog_status IS DISTINCT FROM 'CURRENT'
      OR target.is_active IS DISTINCT FROM true;
  IF missing_targets IS NOT NULL THEN
    RAISE EXCEPTION 'migration 635 requires CURRENT active target contracts: %', missing_targets;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM asset_registry
     WHERE asset_id = 'bg_panchanga'
       AND scope = 'global'
       AND has_writer IS FALSE
       AND asset_kind = 'service'
       AND asset_type = 'service'
       AND health_probe IS NOT NULL
  ) THEN
    RAISE EXCEPTION 'migration 635 requires the vetted bg_panchanga service-probe contract';
  END IF;

  SELECT depends_on INTO actual FROM asset_registry
   WHERE asset_id = 'bg_class_lifetime_counts'
     AND layer = 'brahmagyan' AND scope = 'global';
  IF NOT FOUND THEN
    RAISE EXCEPTION 'migration 635 requires asset_registry.bg_class_lifetime_counts';
  END IF;
  IF actual IS DISTINCT FROM ARRAY[]::text[]
     AND actual IS DISTINCT FROM ARRAY['bg_ghatana']::text[] THEN
    RAISE EXCEPTION 'migration 635 refuses drifted bg_class_lifetime_counts dependencies: %', actual;
  END IF;

  SELECT depends_on INTO actual FROM asset_registry
   WHERE asset_id = 'ga_panchanga'
     AND layer = 'ganita' AND scope = 'per_chart';
  IF NOT FOUND THEN
    RAISE EXCEPTION 'migration 635 requires asset_registry.ga_panchanga';
  END IF;
  IF actual IS DISTINCT FROM ARRAY['ga_positions']::text[]
     AND actual IS DISTINCT FROM ARRAY['ga_positions', 'bg_panchanga']::text[] THEN
    RAISE EXCEPTION 'migration 635 refuses drifted ga_panchanga dependencies: %', actual;
  END IF;

  SELECT depends_on INTO actual FROM asset_registry
   WHERE asset_id = 'ga_prashna'
     AND layer = 'ganita' AND scope = 'per_chart';
  IF NOT FOUND THEN
    RAISE EXCEPTION 'migration 635 requires asset_registry.ga_prashna';
  END IF;
  IF actual IS DISTINCT FROM ARRAY['ga_positions']::text[]
     AND actual IS DISTINCT FROM ARRAY['ga_positions', 'bg_prashna_rules']::text[] THEN
    RAISE EXCEPTION 'migration 635 refuses drifted ga_prashna dependencies: %', actual;
  END IF;

  UPDATE asset_registry
     SET depends_on = ARRAY['bg_ghatana']::text[]
   WHERE asset_id = 'bg_class_lifetime_counts'
     AND depends_on = ARRAY[]::text[];

  UPDATE asset_registry
     SET depends_on = ARRAY['ga_positions', 'bg_panchanga']::text[]
   WHERE asset_id = 'ga_panchanga'
     AND depends_on = ARRAY['ga_positions']::text[];

  UPDATE asset_registry
     SET depends_on = ARRAY['ga_positions', 'bg_prashna_rules']::text[]
   WHERE asset_id = 'ga_prashna'
     AND depends_on = ARRAY['ga_positions']::text[];

  IF NOT EXISTS (
    SELECT 1 FROM asset_registry
     WHERE asset_id = 'bg_class_lifetime_counts'
       AND depends_on = ARRAY['bg_ghatana']::text[]
  ) OR NOT EXISTS (
    SELECT 1 FROM asset_registry
     WHERE asset_id = 'ga_panchanga'
       AND depends_on = ARRAY['ga_positions', 'bg_panchanga']::text[]
  ) OR NOT EXISTS (
    SELECT 1 FROM asset_registry
     WHERE asset_id = 'ga_prashna'
       AND depends_on = ARRAY['ga_positions', 'bg_prashna_rules']::text[]
  ) THEN
    RAISE EXCEPTION 'migration 635 failed to establish exact L0 dependency contracts';
  END IF;

  -- The preconditions above make every new direct edge resolvable. Also reject
  -- a transitive return to any changed target rather than recording a cycle in
  -- the live registry. Scope this traversal to the three changed targets so an
  -- unrelated pre-existing registry defect is not silently claimed as this
  -- migration's concern.
  IF EXISTS (
    WITH RECURSIVE dependency_paths(root_asset_id, asset_id, path) AS (
      SELECT target.asset_id, dependency.asset_id,
             ARRAY[target.asset_id, dependency.asset_id]::text[]
        FROM asset_registry AS target
        CROSS JOIN LATERAL unnest(target.depends_on) AS dependency(asset_id)
       WHERE target.asset_id IN ('bg_class_lifetime_counts', 'ga_panchanga', 'ga_prashna')
      UNION ALL
      SELECT paths.root_asset_id, dependency.asset_id,
             paths.path || dependency.asset_id
        FROM dependency_paths AS paths
        JOIN asset_registry AS current ON current.asset_id = paths.asset_id
        CROSS JOIN LATERAL unnest(current.depends_on) AS dependency(asset_id)
       WHERE paths.asset_id <> paths.root_asset_id
         AND (dependency.asset_id = paths.root_asset_id OR NOT dependency.asset_id = ANY(paths.path))
    )
    SELECT 1
      FROM dependency_paths
     WHERE asset_id = root_asset_id
  ) THEN
    RAISE EXCEPTION 'migration 635 refuses a cycle through a corrected L0 dependency contract';
  END IF;
END $$;
