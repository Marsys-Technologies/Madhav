-- 599_nirmana_t0_l0_hidden_dependencies.sql
--
-- NIRMĀṆA ELEVATION v6 — corrected T0 L0 build-order contract.
--
-- Source audit found five writers whose direct database inputs were absent from
-- asset_registry.depends_on. That omission allowed a frozen campaign wave to
-- schedule the consumer beside, rather than after, its source authority:
--   * bg_reference validates against brahma_ontology (bg_ontology);
--   * bg_remedies extracts governed corpus remedies from bg_texts;
--   * bg_gochara_arcs reads ephemeris_daily (bg_ephemeris);
--   * bg_kp_sublord_division verifies reference_nakshatra (bg_nakshatra);
--   * bg_parihara_rules reads brahma_dosha_catalog and classical_texts
--     (bg_doshas and bg_texts).
--
-- Catalogue metadata only: this migration does not rebuild or mutate asset data.
-- IDEMPOTENT: exact corrected arrays are accepted; only the known empty legacy
-- contract is changed. Any third state fails before mutation.
-- REVERSIBLE: restore ARRAY[]::text[] for only these five assets after first
-- proving that none of their writers reads the named authorities.
-- TRANSACTION: migrate.ts owns the surrounding transaction; this file must not
-- commit independently of the runner's migration ledger write.

DO $$
DECLARE
  actual text[];
  bad_source text;
BEGIN
  SELECT string_agg(
           format('%s (%s)', required.asset_id,
             CASE
               WHEN source.asset_id IS NULL THEN 'missing'
               WHEN source.catalog_status IS DISTINCT FROM 'CURRENT' THEN 'not CURRENT'
               WHEN source.is_active IS DISTINCT FROM true THEN 'inactive'
             END),
           ', ' ORDER BY required.asset_id
         )
    INTO bad_source
    FROM unnest(ARRAY[
      'bg_ontology', 'bg_ephemeris', 'bg_nakshatra', 'bg_doshas', 'bg_texts'
    ]::text[]) AS required(asset_id)
    LEFT JOIN asset_registry source ON source.asset_id = required.asset_id
   WHERE source.asset_id IS NULL
      OR source.catalog_status IS DISTINCT FROM 'CURRENT'
      OR source.is_active IS DISTINCT FROM true;

  IF bad_source IS NOT NULL THEN
    RAISE EXCEPTION
      'migration 599 requires CURRENT active source authorities: %', bad_source;
  END IF;

  SELECT depends_on INTO actual
    FROM asset_registry
   WHERE asset_id = 'bg_reference';
  IF NOT FOUND THEN
    RAISE EXCEPTION 'migration 599 requires asset_registry.bg_reference';
  END IF;
  IF actual IS DISTINCT FROM ARRAY[]::text[]
     AND actual IS DISTINCT FROM ARRAY['bg_ontology']::text[] THEN
    RAISE EXCEPTION
      'migration 599 refuses drifted bg_reference dependencies: %', actual;
  END IF;

  SELECT depends_on INTO actual
    FROM asset_registry
   WHERE asset_id = 'bg_remedies';
  IF NOT FOUND THEN
    RAISE EXCEPTION 'migration 599 requires asset_registry.bg_remedies';
  END IF;
  IF actual IS DISTINCT FROM ARRAY[]::text[]
     AND actual IS DISTINCT FROM ARRAY['bg_texts']::text[] THEN
    RAISE EXCEPTION
      'migration 599 refuses drifted bg_remedies dependencies: %', actual;
  END IF;

  SELECT depends_on INTO actual
    FROM asset_registry
   WHERE asset_id = 'bg_gochara_arcs';
  IF NOT FOUND THEN
    RAISE EXCEPTION 'migration 599 requires asset_registry.bg_gochara_arcs';
  END IF;
  IF actual IS DISTINCT FROM ARRAY[]::text[]
     AND actual IS DISTINCT FROM ARRAY['bg_ephemeris']::text[] THEN
    RAISE EXCEPTION
      'migration 599 refuses drifted bg_gochara_arcs dependencies: %', actual;
  END IF;

  SELECT depends_on INTO actual
    FROM asset_registry
   WHERE asset_id = 'bg_kp_sublord_division';
  IF NOT FOUND THEN
    RAISE EXCEPTION 'migration 599 requires asset_registry.bg_kp_sublord_division';
  END IF;
  IF actual IS DISTINCT FROM ARRAY[]::text[]
     AND actual IS DISTINCT FROM ARRAY['bg_nakshatra']::text[] THEN
    RAISE EXCEPTION
      'migration 599 refuses drifted bg_kp_sublord_division dependencies: %', actual;
  END IF;

  SELECT depends_on INTO actual
    FROM asset_registry
   WHERE asset_id = 'bg_parihara_rules';
  IF NOT FOUND THEN
    RAISE EXCEPTION 'migration 599 requires asset_registry.bg_parihara_rules';
  END IF;
  IF actual IS DISTINCT FROM ARRAY[]::text[]
     AND actual IS DISTINCT FROM ARRAY['bg_doshas', 'bg_texts']::text[] THEN
    RAISE EXCEPTION
      'migration 599 refuses drifted bg_parihara_rules dependencies: %', actual;
  END IF;
END $$;

UPDATE asset_registry
   SET depends_on = ARRAY['bg_ontology']::text[]
 WHERE asset_id = 'bg_reference'
   AND depends_on = ARRAY[]::text[];

UPDATE asset_registry
   SET depends_on = ARRAY['bg_texts']::text[]
 WHERE asset_id = 'bg_remedies'
   AND depends_on = ARRAY[]::text[];

UPDATE asset_registry
   SET depends_on = ARRAY['bg_ephemeris']::text[]
 WHERE asset_id = 'bg_gochara_arcs'
   AND depends_on = ARRAY[]::text[];

UPDATE asset_registry
   SET depends_on = ARRAY['bg_nakshatra']::text[]
 WHERE asset_id = 'bg_kp_sublord_division'
   AND depends_on = ARRAY[]::text[];

UPDATE asset_registry
   SET depends_on = ARRAY['bg_doshas', 'bg_texts']::text[]
 WHERE asset_id = 'bg_parihara_rules'
   AND depends_on = ARRAY[]::text[];

DO $$
DECLARE
  dangling text;
  cyclic text;
BEGIN
  SELECT string_agg(format('%s -> %s', asset.asset_id, dependency), ', ')
    INTO dangling
    FROM asset_registry asset,
         unnest(asset.depends_on) AS dependency
   WHERE asset.is_active
     AND NOT EXISTS (
       SELECT 1 FROM asset_registry source WHERE source.asset_id = dependency
     );

  IF dangling IS NOT NULL THEN
    RAISE EXCEPTION 'migration 599 produced dangling DAG edge(s): %', dangling;
  END IF;

  WITH RECURSIVE walk(root, node, path, cycle) AS (
    SELECT asset.asset_id,
           dependency,
           ARRAY[asset.asset_id, dependency]::text[],
           dependency = asset.asset_id
      FROM asset_registry asset,
           unnest(asset.depends_on) AS dependency
     WHERE asset.is_active

    UNION ALL

    SELECT walk.root,
           dependency,
           walk.path || dependency,
           dependency = ANY(walk.path)
      FROM walk
      JOIN asset_registry asset
        ON asset.asset_id = walk.node
       AND asset.is_active
      CROSS JOIN LATERAL unnest(asset.depends_on) AS dependency
     WHERE NOT walk.cycle
  )
  SELECT string_agg(DISTINCT root, ', ' ORDER BY root)
    INTO cyclic
    FROM walk
   WHERE cycle;

  IF cyclic IS NOT NULL THEN
    RAISE EXCEPTION 'migration 599 detected DAG cycle involving: %', cyclic;
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM asset_registry
     WHERE asset_id = 'bg_reference'
       AND depends_on = ARRAY['bg_ontology']::text[]
  ) THEN
    RAISE EXCEPTION 'migration 599 failed to correct bg_reference dependencies';
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM asset_registry
     WHERE asset_id = 'bg_remedies'
       AND depends_on = ARRAY['bg_texts']::text[]
  ) THEN
    RAISE EXCEPTION 'migration 599 failed to correct bg_remedies dependencies';
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM asset_registry
     WHERE asset_id = 'bg_gochara_arcs'
       AND depends_on = ARRAY['bg_ephemeris']::text[]
  ) THEN
    RAISE EXCEPTION 'migration 599 failed to correct bg_gochara_arcs dependencies';
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM asset_registry
     WHERE asset_id = 'bg_kp_sublord_division'
       AND depends_on = ARRAY['bg_nakshatra']::text[]
  ) THEN
    RAISE EXCEPTION 'migration 599 failed to correct bg_kp_sublord_division dependencies';
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM asset_registry
     WHERE asset_id = 'bg_parihara_rules'
       AND depends_on = ARRAY['bg_doshas', 'bg_texts']::text[]
  ) THEN
    RAISE EXCEPTION 'migration 599 failed to correct bg_parihara_rules dependencies';
  END IF;
END $$;
