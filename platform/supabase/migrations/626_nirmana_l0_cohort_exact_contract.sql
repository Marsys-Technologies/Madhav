-- Migration 626: exact bg_cohort integrity, ownership, and DAG contract.
--
-- The writer owns both bg_synthetic_cohort and bg_synthetic_cohort_md, but the
-- legacy registry counted only the 10,000 parent rows and declared no
-- ephemeris dependency. Structural checks also allowed stale keyed values.
-- This metadata-only migration pins all semantic writer-owned columns across
-- the 110,000-row output and places the writer after the pinned ephemeris
-- service probe. The governed rebuild performs the metadata convergence.
-- Transaction ownership belongs to platform/scripts/migrate.ts.

DO $$
DECLARE
  registry_row asset_registry%ROWTYPE;
  changed_rows integer := 0;
  legacy_structural_check_sha256 constant text :=
    'aa16a9aae42edd4107ab818e82ed14c0584a4333a1c902be94195210c20e1bf5';
  legacy_count_sql constant text :=
    'SELECT COUNT(*) FROM bg_synthetic_cohort';
  canonical_count_sql constant text :=
    'SELECT (SELECT COUNT(*) FROM bg_synthetic_cohort) + (SELECT COUNT(*) FROM bg_synthetic_cohort_md) AS count';
  legacy_explanation constant text :=
    '10,000 synthetic birth charts, uniform-random over 1900-2099, fixed RNG seed. See bg_cohort.py module docstring for full sampling methodology.';
  canonical_explanation constant text :=
    '10,000 deterministic synthetic birth charts + 100,000 Vimshottari mahadasha age-chain rows from fixed RNG seed 20260729 and the pinned Swiss Ephemeris corpus.';
  canonical_partition constant text :=
    'bg_synthetic_cohort.synthetic_id; bg_synthetic_cohort_md.(synthetic_id,md_index)';
  exact_check constant text := $check$
SELECT
  (SELECT count(*) = 10000
      AND count(DISTINCT synthetic_id) = 10000
      AND min(synthetic_id) = 1
      AND max(synthetic_id) = 10000
   FROM bg_synthetic_cohort)
  AND (SELECT count(*) = 100000
      AND count(DISTINCT (synthetic_id,md_index)) = 100000
      AND min(synthetic_id) = 1
      AND max(synthetic_id) = 10000
      AND min(md_index) = 1
      AND max(md_index) = 10
   FROM bg_synthetic_cohort_md)
  AND NOT EXISTS (
    SELECT 1
    FROM bg_synthetic_cohort parent
    LEFT JOIN bg_synthetic_cohort_md md
      ON md.synthetic_id = parent.synthetic_id
    GROUP BY parent.synthetic_id
    HAVING count(md.synthetic_id) <> 10
       OR min(md.md_index) <> 1
       OR max(md.md_index) <> 10
       OR abs(min(md.start_age_years)) > 0.000001
       OR abs(max(md.end_age_years) - 120.0) > 0.000001
  )
  AND NOT EXISTS (
    SELECT 1
    FROM (
      SELECT synthetic_id,md_index,start_age_years,end_age_years,
        lag(end_age_years) OVER (
          PARTITION BY synthetic_id ORDER BY md_index
        ) AS previous_end
      FROM bg_synthetic_cohort_md
    ) chain
    WHERE end_age_years <= start_age_years
       OR (md_index > 1 AND abs(start_age_years - previous_end) > 0.000001)
  )
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(
      synthetic_id,birth_datetime_utc,birth_lat,birth_lon,ayanamsha_key,
      positions,sampling_method,source_citation
    )::text,E'\n' ORDER BY synthetic_id),''),'UTF8')),'hex') =
    '921b0f62ca118932608ea3d3da89e8757ba7c6fbb64c41c2bbdc6b1f99e0c5fa'
   FROM bg_synthetic_cohort)
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(
      synthetic_id,md_index,md_lord,start_age_years,end_age_years,
      md_full_years,is_partial,chain_version
    )::text,E'\n' ORDER BY synthetic_id,md_index),''),'UTF8')),'hex') =
    '1f9e7fcf96941e891462ba1acd46b6c053f58d72d0dcb243a65d16a818c4decd'
   FROM bg_synthetic_cohort_md)
$check$;
BEGIN
  SELECT * INTO registry_row
  FROM asset_registry
  WHERE asset_id = 'bg_cohort'
  FOR UPDATE;

  IF NOT FOUND OR (
    registry_row.layer = 'brahmagyan'
    AND registry_row.sort_order = 20
    AND registry_row.scope = 'global'
    AND registry_row.asset_kind = 'data'
    AND registry_row.catalog_status = 'CURRENT'
    AND registry_row.is_active IS TRUE
    AND registry_row.has_writer IS TRUE
    AND registry_row.target_table = 'bg_synthetic_cohort'
    AND (
      (
        registry_row.count_sql = legacy_count_sql
        AND registry_row.target_floor = 10000
        AND registry_row.expected_volume_formula = 'COHORT_SIZE'
        AND registry_row.expected_volume_inputs = '{"COHORT_SIZE":10000}'::jsonb
        AND registry_row.volume_explanation = legacy_explanation
        AND registry_row.depends_on = ARRAY[]::text[]
        AND registry_row.natural_key_partition IS NULL
        AND registry_row.data_disposition IS NULL
        AND (
          registry_row.integrity_check_sql IS NULL
          OR encode(sha256(convert_to(registry_row.integrity_check_sql,'UTF8')),'hex') =
            legacy_structural_check_sha256
        )
      )
      OR (
        registry_row.count_sql = canonical_count_sql
        AND registry_row.target_floor = 110000
        AND registry_row.expected_volume_formula IS NULL
        AND registry_row.expected_volume_inputs IS NULL
        AND registry_row.volume_explanation = canonical_explanation
        AND registry_row.depends_on = ARRAY['bg_ephemeris_engine']::text[]
        AND (
          (
            registry_row.natural_key_partition IS NULL
            AND registry_row.data_disposition IS NULL
            AND registry_row.integrity_check_sql IS NULL
          )
          OR (
            registry_row.natural_key_partition = canonical_partition
            AND registry_row.data_disposition = 'RETAINED_AS_CAPITAL'
            AND registry_row.integrity_check_sql = exact_check
          )
        )
      )
    )
  ) IS NOT TRUE THEN
    RAISE EXCEPTION 'migration 626 refuses unknown bg_cohort registry contract';
  END IF;

  UPDATE asset_registry
  SET count_sql = canonical_count_sql,
      target_floor = 110000,
      expected_volume_formula = NULL,
      expected_volume_inputs = NULL,
      volume_explanation = canonical_explanation,
      depends_on = ARRAY['bg_ephemeris_engine']::text[],
      natural_key_partition = canonical_partition,
      data_disposition = 'RETAINED_AS_CAPITAL',
      integrity_check_sql = exact_check
  WHERE asset_id = 'bg_cohort';

  GET DIAGNOSTICS changed_rows = ROW_COUNT;
  IF changed_rows <> 1 THEN
    RAISE EXCEPTION 'migration 626 expected 1 row, updated %', changed_rows;
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM asset_registry
    WHERE asset_id = 'bg_cohort'
      AND count_sql = canonical_count_sql
      AND target_floor = 110000
      AND expected_volume_formula IS NULL
      AND expected_volume_inputs IS NULL
      AND volume_explanation = canonical_explanation
      AND depends_on = ARRAY['bg_ephemeris_engine']::text[]
      AND natural_key_partition = canonical_partition
      AND data_disposition = 'RETAINED_AS_CAPITAL'
      AND integrity_check_sql = exact_check
  ) THEN
    RAISE EXCEPTION 'migration 626 postflight registry mismatch';
  END IF;
END $$;
