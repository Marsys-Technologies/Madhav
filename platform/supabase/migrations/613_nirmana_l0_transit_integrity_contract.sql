-- Migration 613: install exact integrity contracts for the composite transit
-- producer and repair the stale bg_transit_rules registry floor.
--
-- The accepted disposition preserves all 75 rules: 68 rows are convergently
-- rebuilt by the Python writer, while migration 397's seven double-transit
-- rows remain migration-owned retained capital. The detector also covers the
-- producer's nine engine rows and 27 Moorti rows. Read-only production hashes
-- were matched to a local deterministic replay on 2026-08-26.
--
-- Registry metadata only; transaction ownership belongs to migrate.ts.

DO $$
DECLARE
  registry_row asset_registry%ROWTYPE;
  changed_rows integer := 0;
  legacy_rules_description constant text :=
    'Classical transit rules (favourable/unfavourable/vedha houses) from BPHS Ch.29 and Phaladeepika Ch.26.';
  canonical_rules_description constant text :=
    '75 classical transit rules: 42 favourable, 26 unfavourable, and 7 double-transit rules from BPHS Ch.29, Phaladeepika Ch.26, Saravali, and Jataka Parijata.';
  legacy_rules_explanation constant text :=
    '50 classical gochara transit rules per actual build count (41 base + 9 Venus gochara phala rows added Phase B).';
  canonical_rules_explanation constant text :=
    '75 rows = 68 writer-owned Gochara rules (42 favourable + 26 unfavourable) plus 7 preserved migration-owned Jupiter–Saturn double-transit rules.';
  engine_check constant text := $check$
SELECT
  (SELECT count(*) = 9 FROM bg_transit_engine)
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(graha,avg_daily_motion_deg,zodiac_period_days,
      sign_residence_days,classical_citation)::text,
    E'\n' ORDER BY graha COLLATE "C"
  ),''),'UTF8')),'hex') =
    'e2dafc84d7fef9b8a05ad01b98b036686e8ec0af9694a4d43ac4b2b8c425797b'
  FROM bg_transit_engine)
$check$;
  rules_check constant text := $check$
SELECT
  (SELECT count(*) = 9 FROM bg_transit_engine)
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(graha,avg_daily_motion_deg,zodiac_period_days,
      sign_residence_days,classical_citation)::text,
    E'\n' ORDER BY graha COLLATE "C"
  ),''),'UTF8')),'hex') =
    'e2dafc84d7fef9b8a05ad01b98b036686e8ec0af9694a4d43ac4b2b8c425797b'
  FROM bg_transit_engine)
  AND (SELECT count(*) = 75 FROM bg_transit_rules)
  AND (SELECT count(*) FILTER (WHERE rule_type = 'favourable') = 42
       AND count(*) FILTER (WHERE rule_type = 'unfavourable') = 26
       AND count(*) FILTER (WHERE rule_type = 'double_transit') = 7
       FROM bg_transit_rules)
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(rule_type,graha,primary_house,vedha_house,phala,
      classical_citation,rule_notes)::text,
    E'\n' ORDER BY graha COLLATE "C",rule_type COLLATE "C",primary_house
  ),''),'UTF8')),'hex') =
    '13616890d782a47cf667a4b1d3c52d2be08408a80f647d0e4aed4fc38cae3e54'
  FROM bg_transit_rules)
  AND (SELECT count(*) = 27 FROM bg_transit_moorti)
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(nakshatra_offset,moorti_name,quality_tier,phala_brief,
      classical_citation,rule_notes)::text,
    E'\n' ORDER BY nakshatra_offset
  ),''),'UTF8')),'hex') =
    'b411c02abb7fec89c971353190f1ebe117a31a85e1bba06aeadc6509d0256450'
  FROM bg_transit_moorti)
$check$;
BEGIN
  SELECT * INTO registry_row FROM asset_registry
  WHERE asset_id = 'bg_transit_engine' FOR UPDATE;
  IF NOT FOUND OR (
    registry_row.layer = 'brahmagyan'
    AND registry_row.sort_order = 61
    AND registry_row.scope = 'global'
    AND registry_row.asset_kind = 'data'
    AND registry_row.catalog_status = 'CURRENT'
    AND registry_row.is_active IS TRUE
    AND registry_row.has_writer IS FALSE
    AND registry_row.target_table = 'bg_transit_engine'
    AND registry_row.count_sql = 'SELECT COUNT(*) FROM bg_transit_engine'
    AND registry_row.target_floor = 9
    AND registry_row.depends_on = ARRAY[]::text[]
    AND (registry_row.integrity_check_sql IS NULL
      OR registry_row.integrity_check_sql = engine_check)
  ) IS NOT TRUE THEN
    RAISE EXCEPTION
      'migration 613 refuses unknown registry contract for bg_transit_engine';
  END IF;

  SELECT * INTO registry_row FROM asset_registry
  WHERE asset_id = 'bg_transit_rules' FOR UPDATE;
  IF NOT FOUND OR (
    registry_row.layer = 'brahmagyan'
    AND registry_row.sort_order = 62
    AND registry_row.scope = 'global'
    AND registry_row.asset_kind = 'data'
    AND registry_row.catalog_status = 'CURRENT'
    AND registry_row.is_active IS TRUE
    AND registry_row.has_writer IS TRUE
    AND registry_row.target_table = 'bg_transit_rules'
    AND registry_row.count_sql = 'SELECT COUNT(*) FROM bg_transit_rules'
    AND registry_row.depends_on = ARRAY[]::text[]
    AND (
      (
        registry_row.target_floor = 50
        AND registry_row.english_description = legacy_rules_description
        AND registry_row.volume_explanation = legacy_rules_explanation
        AND registry_row.integrity_check_sql IS NULL
      ) OR (
        registry_row.target_floor = 75
        AND registry_row.english_description = canonical_rules_description
        AND registry_row.volume_explanation = canonical_rules_explanation
        AND (registry_row.integrity_check_sql IS NULL
          OR registry_row.integrity_check_sql = rules_check)
      )
    )
  ) IS NOT TRUE THEN
    RAISE EXCEPTION
      'migration 613 refuses unknown registry contract for bg_transit_rules';
  END IF;

  UPDATE asset_registry
  SET integrity_check_sql = CASE asset_id
        WHEN 'bg_transit_engine' THEN engine_check
        WHEN 'bg_transit_rules' THEN rules_check
      END,
      target_floor = CASE asset_id
        WHEN 'bg_transit_rules' THEN 75
        ELSE target_floor
      END,
      english_description = CASE asset_id
        WHEN 'bg_transit_rules' THEN canonical_rules_description
        ELSE english_description
      END,
      volume_explanation = CASE asset_id
        WHEN 'bg_transit_rules' THEN canonical_rules_explanation
        ELSE volume_explanation
      END
  WHERE asset_id IN ('bg_transit_engine','bg_transit_rules');
  GET DIAGNOSTICS changed_rows = ROW_COUNT;
  IF changed_rows <> 2 THEN
    RAISE EXCEPTION 'migration 613 expected 2 registry rows, updated %', changed_rows;
  END IF;

  IF (SELECT count(*) FROM asset_registry
      WHERE (asset_id = 'bg_transit_engine'
             AND integrity_check_sql = engine_check)
         OR (asset_id = 'bg_transit_rules'
             AND target_floor = 75
             AND english_description = canonical_rules_description
             AND volume_explanation = canonical_rules_explanation
             AND integrity_check_sql = rules_check)) <> 2 THEN
    RAISE EXCEPTION 'migration 613 postflight registry mismatch';
  END IF;
END $$;
