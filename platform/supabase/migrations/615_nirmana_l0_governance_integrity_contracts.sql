-- Migration 615: install exact integrity contracts for the two scoped
-- brahma_class_priors producers and the mixed-ownership formula registry.
--
-- bg_class_priors owns exactly prior_version='1.0'; bg_class_lifetime_counts
-- owns exactly prior_version='ne_v01' + fact_kind='lifetime_count_per_100y'.
-- bg_formula_constants converges ten source-backed operational constants while
-- preserving seven later migration-owned constants as retained capital.
-- Read-only production hashes were reproduced by local writer replay on
-- 2026-08-26. Registry metadata only; migrate.ts owns the transaction.

DO $$
DECLARE
  registry_row asset_registry%ROWTYPE;
  changed_rows integer := 0;
  class_partition constant text :=
    'prior_version=1.0; (signal_type_class,fact_kind,source_subsystem,signal_tradition)';
  lifetime_partition constant text :=
    'prior_version=ne_v01 AND fact_kind=lifetime_count_per_100y; signal_type_class';
  formula_partition constant text := 'constant_id';
  class_check constant text := $check$
SELECT
  count(*) = 171
  AND encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(prior_version,signal_type_class,fact_kind,source_subsystem,
      signal_tradition,class_prior,varga_weights,contested,citation,ratified_by,
      prior_basis,source_ref)::text,E'\n'
    ORDER BY prior_version COLLATE "C",signal_type_class COLLATE "C",
      fact_kind COLLATE "C",source_subsystem COLLATE "C",signal_tradition COLLATE "C"
  ),''),'UTF8')),'hex') =
    'a12fd986e469d417ff2ff54d3902b69809d40be42cc2228854220bb63f7139b2'
FROM brahma_class_priors WHERE prior_version='1.0'
$check$;
  lifetime_check constant text := $check$
SELECT
  count(*) = 6
  AND encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(prior_version,signal_type_class,fact_kind,source_subsystem,
      signal_tradition,class_prior,varga_weights,contested,citation,ratified_by,
      prior_basis,source_ref)::text,E'\n'
    ORDER BY prior_version COLLATE "C",signal_type_class COLLATE "C",
      fact_kind COLLATE "C",source_subsystem COLLATE "C",signal_tradition COLLATE "C"
  ),''),'UTF8')),'hex') =
    '0a7b3be21e8b20a96f5d2a7a820cb1492c9e2e5ed889ff7bfcceec2bb4808800'
FROM brahma_class_priors
WHERE prior_version='ne_v01' AND fact_kind='lifetime_count_per_100y'
$check$;
  formula_check constant text := $check$
SELECT
  count(*) = 17
  AND count(*) FILTER (WHERE class='conflation_bug') = 0
  AND encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(constant_id,value_jsonb,class,consumer_assets,
      citation_or_ratification,calibratable,bounds,version)::text,E'\n'
    ORDER BY constant_id COLLATE "C"
  ),''),'UTF8')),'hex') =
    '14a06b00379e0fc23f00e87984a8e58bc962a1c44849045ff6ac354431576f33'
FROM brahma_formula_constants
$check$;
BEGIN
  SELECT * INTO registry_row FROM asset_registry
  WHERE asset_id='bg_class_priors' FOR UPDATE;
  IF NOT FOUND OR (
    registry_row.layer='brahmagyan'
    AND registry_row.sort_order IN (16,67)
    AND registry_row.scope='global'
    AND registry_row.asset_kind='data'
    AND registry_row.catalog_status='CURRENT'
    AND registry_row.is_active IS TRUE
    AND registry_row.has_writer IS TRUE
    AND registry_row.target_table='brahma_class_priors'
    AND registry_row.target_floor=171
    AND registry_row.count_sql=
      'SELECT COUNT(*) FROM brahma_class_priors WHERE prior_version=''1.0'''
    AND registry_row.depends_on=ARRAY[]::text[]
    AND (
      (registry_row.natural_key_partition IS NULL
       AND registry_row.data_disposition IS NULL
       AND registry_row.integrity_check_sql IS NULL)
      OR
      (registry_row.natural_key_partition=class_partition
       AND registry_row.data_disposition IS NULL
       AND registry_row.integrity_check_sql=class_check)
    )
  ) IS NOT TRUE THEN
    RAISE EXCEPTION 'migration 615 refuses unknown bg_class_priors registry contract';
  END IF;

  SELECT * INTO registry_row FROM asset_registry
  WHERE asset_id='bg_class_lifetime_counts' FOR UPDATE;
  IF NOT FOUND OR (
    registry_row.layer='brahmagyan'
    AND registry_row.sort_order=21
    AND registry_row.scope='global'
    AND registry_row.asset_kind='data'
    AND registry_row.catalog_status='CURRENT'
    AND registry_row.is_active IS TRUE
    AND registry_row.has_writer IS TRUE
    AND registry_row.target_table='brahma_class_priors'
    AND registry_row.target_floor=6
    AND registry_row.count_sql=
      'SELECT COUNT(*) FROM brahma_class_priors WHERE prior_version=''ne_v01'' AND fact_kind=''lifetime_count_per_100y'''
    AND registry_row.depends_on=ARRAY[]::text[]
    AND (
      (registry_row.natural_key_partition IS NULL
       AND registry_row.data_disposition IS NULL
       AND registry_row.integrity_check_sql IS NULL)
      OR
      (registry_row.natural_key_partition=lifetime_partition
       AND registry_row.data_disposition IS NULL
       AND registry_row.integrity_check_sql=lifetime_check)
    )
  ) IS NOT TRUE THEN
    RAISE EXCEPTION
      'migration 615 refuses unknown bg_class_lifetime_counts registry contract';
  END IF;

  SELECT * INTO registry_row FROM asset_registry
  WHERE asset_id='bg_formula_constants' FOR UPDATE;
  IF NOT FOUND OR (
    registry_row.layer='brahmagyan'
    AND registry_row.sort_order IN (18,68)
    AND registry_row.scope='global'
    AND registry_row.asset_kind='data'
    AND registry_row.catalog_status='CURRENT'
    AND registry_row.is_active IS TRUE
    AND registry_row.has_writer IS TRUE
    AND registry_row.target_table='brahma_formula_constants'
    AND registry_row.target_floor=17
    AND registry_row.count_sql='SELECT count(*) FROM brahma_formula_constants'
    AND registry_row.depends_on=ARRAY[]::text[]
    AND (
      (registry_row.natural_key_partition IS NULL
       AND registry_row.data_disposition IS NULL
       AND registry_row.integrity_check_sql IS NULL)
      OR
      (registry_row.natural_key_partition=formula_partition
       AND registry_row.data_disposition='RETAINED_AS_CAPITAL'
       AND registry_row.integrity_check_sql=formula_check)
    )
  ) IS NOT TRUE THEN
    RAISE EXCEPTION 'migration 615 refuses unknown bg_formula_constants registry contract';
  END IF;

  UPDATE asset_registry
  SET sort_order=CASE asset_id
        WHEN 'bg_class_priors' THEN 67
        WHEN 'bg_formula_constants' THEN 68
        ELSE sort_order
      END,
      natural_key_partition=CASE asset_id
        WHEN 'bg_class_priors' THEN class_partition
        WHEN 'bg_class_lifetime_counts' THEN lifetime_partition
        WHEN 'bg_formula_constants' THEN formula_partition
      END,
      data_disposition=CASE asset_id
        WHEN 'bg_formula_constants' THEN 'RETAINED_AS_CAPITAL'
        ELSE NULL
      END,
      integrity_check_sql=CASE asset_id
        WHEN 'bg_class_priors' THEN class_check
        WHEN 'bg_class_lifetime_counts' THEN lifetime_check
        WHEN 'bg_formula_constants' THEN formula_check
      END
  WHERE asset_id IN ('bg_class_priors','bg_class_lifetime_counts','bg_formula_constants');
  GET DIAGNOSTICS changed_rows=ROW_COUNT;
  IF changed_rows<>3 THEN
    RAISE EXCEPTION 'migration 615 expected 3 registry rows, updated %',changed_rows;
  END IF;

  IF (SELECT count(*) FROM asset_registry WHERE
      (asset_id='bg_class_priors' AND sort_order=67
       AND natural_key_partition=class_partition AND data_disposition IS NULL
       AND integrity_check_sql=class_check)
      OR
      (asset_id='bg_class_lifetime_counts' AND sort_order=21
       AND natural_key_partition=lifetime_partition AND data_disposition IS NULL
       AND integrity_check_sql=lifetime_check)
      OR
      (asset_id='bg_formula_constants' AND sort_order=68
       AND natural_key_partition=formula_partition
       AND data_disposition='RETAINED_AS_CAPITAL'
       AND integrity_check_sql=formula_check))<>3 THEN
    RAISE EXCEPTION 'migration 615 postflight registry mismatch';
  END IF;
END $$;
