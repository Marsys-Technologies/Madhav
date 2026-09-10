-- Migration 623: exact bg_compendium_index integrity contract.
-- Production currently has 9,538 rows. A clean replay from the same live
-- source corpus deterministically produces 9,571 rows: the existing 7,969
-- chapter rows plus 1,602 topic rows. Transaction ownership belongs to
-- migrate.ts; this file intentionally has no BEGIN/COMMIT.

DO $$
DECLARE
  registry_row asset_registry%ROWTYPE;
  changed_rows integer := 0;
  canonical_partition constant text :=
    'brahma_compendium_index.(text_id,chapter_num WHERE topic_id IS NULL; text_id,topic_id WHERE chapter_num IS NULL)';
  legacy_explanation constant text :=
    '9,538 index entries = honest count from actual build. Per design §3.12.';
  canonical_explanation constant text :=
    '9,571 deterministic index rows from the production source corpus: 7,969 '
    'per-text chapter projections + 1,602 valid per-text topic projections. '
    'Rebuild adds 33 Muhurta Chintamani topic identities and refreshes 68 stale '
    'mechanical summaries.';
  canonical_count_sql constant text :=
    'SELECT count(*) FROM brahma_compendium_index';
  compendium_check constant text := $check$
SELECT
  (SELECT count(*) = 9571 FROM brahma_compendium_index)
  AND (SELECT count(*) = 7969 FROM brahma_compendium_index WHERE topic_id IS NULL)
  AND (SELECT count(*) = 1602 FROM brahma_compendium_index WHERE chapter_num IS NULL)
  AND NOT EXISTS (
    SELECT 1 FROM brahma_compendium_index
    WHERE (chapter_num IS NULL) = (topic_id IS NULL)
  )
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(text_id,chapter_num,chapter_title_en,chapter_title_sa,
      topic_id,verse_start,verse_end,chunk_ids,summary_text,significance,
      classical_significance_score)::text,
    E'\n' ORDER BY text_id COLLATE "C",chapter_num),''),'UTF8')),'hex') =
    '6994a142e5c6d1832cbeba82070ff444495dc83211d57331175505e74f70c2e9'
   FROM brahma_compendium_index WHERE topic_id IS NULL)
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(text_id,chapter_num,chapter_title_en,chapter_title_sa,
      topic_id,verse_start,verse_end,chunk_ids,summary_text,significance,
      classical_significance_score)::text,
    E'\n' ORDER BY text_id COLLATE "C",topic_id COLLATE "C"),''),'UTF8')),'hex') =
    '093884a730b1743cf6e04d9b838f7bacd6741ee7111daa6522c655e1fa0d4c19'
   FROM brahma_compendium_index WHERE chapter_num IS NULL)
$check$;
BEGIN
  SELECT * INTO registry_row
  FROM asset_registry
  WHERE asset_id = 'bg_compendium_index'
  FOR UPDATE;

  IF NOT FOUND OR (
    registry_row.layer = 'brahmagyan'
    AND registry_row.sort_order = 12
    AND registry_row.scope = 'global'
    AND registry_row.asset_kind = 'data'
    AND registry_row.catalog_status = 'CURRENT'
    AND registry_row.is_active IS TRUE
    AND registry_row.has_writer IS TRUE
    AND registry_row.target_table = 'brahma_compendium_index'
    AND registry_row.count_sql = canonical_count_sql
    AND registry_row.depends_on = ARRAY['bg_texts','bg_reference']::text[]
    AND registry_row.english_description =
      'Cross-reference index over the 15 classical texts — chapter summaries, topic-coverage map, significance scores'
    AND registry_row.data_disposition IS NULL
    AND (
      (
        registry_row.natural_key_partition IS NULL
        AND registry_row.integrity_check_sql IS NULL
        AND (
          (registry_row.target_floor = 9538 AND registry_row.volume_explanation = legacy_explanation)
          OR (registry_row.target_floor = 9571 AND registry_row.volume_explanation = canonical_explanation)
        )
      )
      OR (
        registry_row.target_floor = 9571
        AND registry_row.volume_explanation = canonical_explanation
        AND registry_row.natural_key_partition = canonical_partition
        AND registry_row.integrity_check_sql = compendium_check
      )
    )
  ) IS NOT TRUE THEN
    RAISE EXCEPTION 'migration 623 refuses unknown bg_compendium_index registry contract';
  END IF;

  UPDATE asset_registry
  SET target_floor = 9571,
      count_sql = canonical_count_sql,
      volume_explanation = canonical_explanation,
      natural_key_partition = canonical_partition,
      data_disposition = NULL,
      integrity_check_sql = compendium_check
  WHERE asset_id = 'bg_compendium_index';

  GET DIAGNOSTICS changed_rows = ROW_COUNT;
  IF changed_rows <> 1 THEN
    RAISE EXCEPTION 'migration 623 expected 1 row, updated %', changed_rows;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM asset_registry
    WHERE asset_id = 'bg_compendium_index'
      AND target_floor = 9571
      AND count_sql = canonical_count_sql
      AND volume_explanation = canonical_explanation
      AND natural_key_partition = canonical_partition
      AND data_disposition IS NULL
      AND integrity_check_sql = compendium_check
  ) THEN
    RAISE EXCEPTION 'migration 623 postflight registry mismatch';
  END IF;
END $$;
