-- Migration 618: install the exact bg_rules integrity contract.
--
-- Production currently carries 3,003 python_regex_v2 rows, but a clean clone
-- replay exposed two hash-seed-dependent identities in Pattern 27. Preserving
-- first textual planet occurrence makes antecedent identity and cross-pattern
-- duplicate suppression deterministic. Full 10,651-chunk replays under
-- PYTHONHASHSEED=0 and 3 both produced 3,002 rows and the digest below.
-- The detector is expected to remain false after deploy until bg_rules rebuilds.
--
-- Registry metadata only; transaction ownership belongs to migrate.ts.

DO $$
DECLARE
  registry_row asset_registry%ROWTYPE;
  changed_rows integer := 0;
  canonical_partition constant text := 'sutravali_rules.rule_id';
  canonical_explanation constant text :=
    '3,002 deterministic regex-extracted rules from the frozen 10,651-chunk '
    'corpus after canonicalizing Pattern 27 planet order and duplicate '
    'suppression across Python hash seeds.';
  rules_check constant text := $check$
SELECT
  count(*) = 3002
  AND count(DISTINCT rule_id) = 3002
  AND count(*) FILTER (WHERE extracted_by = 'python_regex_v2') = 3002
  AND count(*) FILTER (WHERE confidence < 0.600 OR quality_score < 0.600) = 0
  AND count(*) FILTER (WHERE confidence IS DISTINCT FROM quality_score) = 0
  AND count(*) FILTER (WHERE yoga_canonical_id IS NOT NULL) = 17
  AND count(*) FILTER (WHERE dasha_system_id IS NOT NULL) = 0
  AND count(*) FILTER (WHERE transit_marker IS TRUE) = 25
  AND NOT EXISTS (
    SELECT 1 FROM sutravali_rules AS rule
    WHERE NOT EXISTS (
      SELECT 1 FROM classical_text_chunks AS chunk
      WHERE chunk.text_id = rule.text_id
    )
       OR (rule.yoga_canonical_id IS NOT NULL AND NOT EXISTS (
         SELECT 1 FROM brahma_yoga_catalog AS yoga
         WHERE yoga.canonical_id = rule.yoga_canonical_id
       ))
       OR (rule.dasha_system_id IS NOT NULL AND NOT EXISTS (
         SELECT 1 FROM brahma_dasha_systems AS dasha
         WHERE dasha.canonical_id = rule.dasha_system_id
       ))
  )
  AND encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(rule_id,text_id,verse_ref,antecedent_jsonb,predicate_jsonb,
      prediction_jsonb,confidence,extracted_by,extraction_pass_log,quality_score,
      yoga_canonical_id,dasha_system_id,transit_marker)::text,
    E'\n' ORDER BY rule_id::text COLLATE "C"
  ),''),'UTF8')),'hex') =
    '87b697041c73359e12daf8258cfdd6e85a38eb5c63fa39865e42f5b46e610dbd'
FROM sutravali_rules
$check$;
BEGIN
  SELECT * INTO registry_row FROM asset_registry
  WHERE asset_id = 'bg_rules' FOR UPDATE;

  IF NOT FOUND OR (
    registry_row.layer = 'brahmagyan'
    AND registry_row.sort_order = 6
    AND registry_row.scope = 'global'
    AND registry_row.asset_kind = 'data'
    AND registry_row.catalog_status = 'CURRENT'
    AND registry_row.is_active IS TRUE
    AND registry_row.has_writer IS TRUE
    AND registry_row.target_table = 'sutravali_rules'
    AND registry_row.count_sql = 'SELECT count(*) FROM sutravali_rules'
    AND registry_row.depends_on = ARRAY['bg_texts']::text[]
    AND registry_row.english_description =
      'Classical rules extracted from text chunks via Python regex patterns — verse-traceable'
    AND (
      (
        registry_row.target_floor IN (2912,3002)
        AND registry_row.volume_explanation IN (
          '2,912 rules = honest count from actual build against 10,651-chunk corpus.',
          'Rows in sutravali_rules: deterministic regex-extracted rules from classical_text_chunks (3.4% coverage — most chunks are narrative, not aphoristic). Grew from 1,976 to 2,912 after processing all 10,651 chunks including bhrigu_nandi_nadi (608) and nadi_navamsa_patel (1,850); 936 new rules inserted with 1,976 conflict-skipped (existing rules untouched).',
          canonical_explanation
        )
        AND registry_row.natural_key_partition IS NULL
        AND registry_row.data_disposition IS NULL
        AND registry_row.integrity_check_sql IS NULL
      ) OR (
        registry_row.target_floor = 3002
        AND registry_row.volume_explanation = canonical_explanation
        AND registry_row.natural_key_partition = canonical_partition
        AND registry_row.data_disposition IS NULL
        AND registry_row.integrity_check_sql = rules_check
      )
    )
  ) IS NOT TRUE THEN
    RAISE EXCEPTION 'migration 618 refuses unknown bg_rules registry contract';
  END IF;

  UPDATE asset_registry
  SET target_floor = 3002,
      volume_explanation = canonical_explanation,
      natural_key_partition = canonical_partition,
      data_disposition = NULL,
      integrity_check_sql = rules_check
  WHERE asset_id = 'bg_rules';
  GET DIAGNOSTICS changed_rows = ROW_COUNT;
  IF changed_rows <> 1 THEN
    RAISE EXCEPTION 'migration 618 expected 1 registry row, updated %', changed_rows;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM asset_registry
    WHERE asset_id = 'bg_rules'
      AND target_floor = 3002
      AND volume_explanation = canonical_explanation
      AND natural_key_partition = canonical_partition
      AND data_disposition IS NULL
      AND integrity_check_sql = rules_check
  ) THEN
    RAISE EXCEPTION 'migration 618 postflight registry mismatch';
  END IF;
END $$;
