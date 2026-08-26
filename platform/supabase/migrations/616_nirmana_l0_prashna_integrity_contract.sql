-- Migration 616: install the exact composite integrity contract for the
-- source-owned Prashna reference corpus.
--
-- The June L0 enrichment added five attested Tajik yogas directly to
-- production and migration 305 ratified the resulting 41-row floor, but the
-- Python writer retained its original 11-yoga corpus. The writer now owns and
-- converges all 16 yogas. Read-only production hashes were reproduced by a
-- clean local writer replay on 2026-08-26.
--
-- Registry metadata only; transaction ownership belongs to migrate.ts.

DO $$
DECLARE
  registry_row asset_registry%ROWTYPE;
  changed_rows integer := 0;
  partition_contract constant text :=
    'bg_prashna_lagna_methods.method_id; bg_prashna_tajik_yogas.yoga_id; '
    'bg_prashna_significators.question_class; '
    'bg_prashna_fructification_rules.rule_id; '
    'bg_prashna_special_techniques.technique_id';
  canonical_explanation constant text :=
    '41 rows across 5 prashna sub-tables (5 lagna methods + 16 Tajik yogas + '
    '12 significators + 5 fructification rules + 3 special techniques).';
  corpus_check constant text := $check$
SELECT
  (SELECT count(*) = 5 FROM bg_prashna_lagna_methods)
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(method_id,method_name,method_name_sa,derivation_rule,
      derivation_rule_jsonb,classical_citation,is_primary,tradition)::text,
    E'\n' ORDER BY method_id COLLATE "C"
  ),''),'UTF8')),'hex') =
    '1fcf4a29aada13aeb3458a601f42206111cdd0e7132f1d3973f49b65de239b11'
  FROM bg_prashna_lagna_methods)
  AND (SELECT count(*) = 16 FROM bg_prashna_tajik_yogas)
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(yoga_id,yoga_name,yoga_name_sa,judgment_meaning,
      formation_rule,formation_rule_jsonb,classical_citation,
      is_fructification_indicator)::text,
    E'\n' ORDER BY yoga_id COLLATE "C"
  ),''),'UTF8')),'hex') =
    'd67e84e57e5c616f132929e845dec3ee8d5fccd4d9530d9c5c90b0a275662638'
  FROM bg_prashna_tajik_yogas)
  AND (SELECT count(*) = 12 FROM bg_prashna_significators)
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(question_class,querent_house,querent_planet,
      quesited_house,quesited_planet,significator_rule,classical_citation)::text,
    E'\n' ORDER BY question_class COLLATE "C"
  ),''),'UTF8')),'hex') =
    '8a02f4bd19ad23ab67ec1b7354d6c537e0c54453d4a6c405caf033c630879427'
  FROM bg_prashna_significators)
  AND (SELECT count(*) = 5 FROM bg_prashna_fructification_rules)
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(rule_id,time_unit,degree_conversion_rule,applicable_when,
      classical_citation)::text,E'\n' ORDER BY rule_id COLLATE "C"
  ),''),'UTF8')),'hex') =
    '96ac27661e071bac4e372272f4eea1472cca37c0b47dbd7d9f07b37f159a99a0'
  FROM bg_prashna_fructification_rules)
  AND (SELECT count(*) = 3 FROM bg_prashna_special_techniques)
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(technique_id,technique_name,technique_name_sa,
      application_rule,classical_citation)::text,
    E'\n' ORDER BY technique_id COLLATE "C"
  ),''),'UTF8')),'hex') =
    '065791ee29ce9a1c6b98ed9d356151b06e0a463b1bcb02c9904ea160846488cd'
  FROM bg_prashna_special_techniques)
$check$;
BEGIN
  SELECT * INTO registry_row FROM asset_registry
  WHERE asset_id = 'bg_prashna_rules' FOR UPDATE;

  IF NOT FOUND OR (
    registry_row.layer = 'brahmagyan'
    AND registry_row.sort_order = 55
    AND registry_row.scope = 'global'
    AND registry_row.asset_kind = 'data'
    AND registry_row.catalog_status = 'CURRENT'
    AND registry_row.is_active IS TRUE
    AND registry_row.has_writer IS TRUE
    AND registry_row.target_table IS NULL
    AND registry_row.count_sql =
      'SELECT (SELECT COUNT(*) FROM bg_prashna_lagna_methods) + (SELECT COUNT(*) FROM bg_prashna_tajik_yogas) + (SELECT COUNT(*) FROM bg_prashna_significators) + (SELECT COUNT(*) FROM bg_prashna_fructification_rules) + (SELECT COUNT(*) FROM bg_prashna_special_techniques) AS count'
    AND registry_row.depends_on = ARRAY[]::text[]
    AND registry_row.english_description =
      'Static horary astrology rules — Prashna lagna methods, Tajik yogas, significators, fructification rules, and special techniques.'
    AND (
      (
        registry_row.target_floor IN (36,41)
        AND registry_row.volume_explanation IN (
          '36 rows across 5 prashna sub-tables (5 lagna methods + 11 Tajik yogas + 12 significators + 5 fructification rules + 3 special techniques).',
          canonical_explanation
        )
        AND registry_row.natural_key_partition IS NULL
        AND registry_row.data_disposition IS NULL
        AND registry_row.integrity_check_sql IS NULL
      ) OR (
        registry_row.target_floor = 41
        AND registry_row.volume_explanation = canonical_explanation
        AND registry_row.natural_key_partition = partition_contract
        AND registry_row.data_disposition IS NULL
        AND registry_row.integrity_check_sql = corpus_check
      )
    )
  ) IS NOT TRUE THEN
    RAISE EXCEPTION 'migration 616 refuses unknown bg_prashna_rules registry contract';
  END IF;

  UPDATE asset_registry
  SET target_floor = 41,
      volume_explanation = canonical_explanation,
      natural_key_partition = partition_contract,
      data_disposition = NULL,
      integrity_check_sql = corpus_check
  WHERE asset_id = 'bg_prashna_rules';
  GET DIAGNOSTICS changed_rows = ROW_COUNT;
  IF changed_rows <> 1 THEN
    RAISE EXCEPTION 'migration 616 expected 1 registry row, updated %', changed_rows;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM asset_registry
    WHERE asset_id = 'bg_prashna_rules'
      AND target_floor = 41
      AND volume_explanation = canonical_explanation
      AND natural_key_partition = partition_contract
      AND data_disposition IS NULL
      AND integrity_check_sql = corpus_check
  ) THEN
    RAISE EXCEPTION 'migration 616 postflight registry mismatch';
  END IF;
END $$;
