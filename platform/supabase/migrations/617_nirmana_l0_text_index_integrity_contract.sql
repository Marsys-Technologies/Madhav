-- Migration 617: install the exact bg_text_index integrity contract.
--
-- The deterministic classifier was replayed read-only against all 10,651
-- production chunks on 2026-08-26: 10,651/10,651 current topic_tag values
-- matched, including 3,641 honest nulls. The writer now recomputes the complete
-- embedded partition and repairs wrong non-null tags instead of treating
-- non-null as proof of correctness.
--
-- Registry metadata only; transaction ownership belongs to migrate.ts.

DO $$
DECLARE
  registry_row asset_registry%ROWTYPE;
  changed_rows integer := 0;
  canonical_partition constant text :=
    'classical_text_chunks.chunk_id; value=topic_tag';
  canonical_explanation constant text :=
    '361 distinct topic_tag values is the achieved deterministic-classifier '
    'coverage ratified by migrations 196 and 231. Raise this floor only with '
    'an evidence-backed classifier or corpus expansion; never fabricate '
    'assignments to meet the former aspirational 400.';
  audited_digest constant text :=
    '19964c1f91e149f4a136632af0f1e3c88b28e213f1bb4e45de98fcf395a94e21';
  index_check constant text := $check$
SELECT
  count(*) = 10651
  AND count(*) FILTER (WHERE embedding IS NOT NULL) = 10651
  AND count(*) FILTER (WHERE topic_tag IS NOT NULL) = 7010
  AND count(*) FILTER (WHERE topic_tag IS NULL) = 3641
  AND count(DISTINCT topic_tag) = 361
  AND NOT EXISTS (
    SELECT 1 FROM classical_text_chunks AS chunk
    WHERE chunk.topic_tag IS NOT NULL
      AND NOT EXISTS (
        SELECT 1 FROM reference_topic_tags AS topic
        WHERE topic.canonical_id = chunk.topic_tag
      )
  )
  AND encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(chunk_id,topic_tag)::text,
    E'\n' ORDER BY chunk_id COLLATE "C"
  ),''),'UTF8')),'hex') =
    '19964c1f91e149f4a136632af0f1e3c88b28e213f1bb4e45de98fcf395a94e21'
FROM classical_text_chunks
$check$;
BEGIN
  IF position(audited_digest IN index_check) = 0 THEN
    RAISE EXCEPTION 'migration 617 internal digest contract mismatch';
  END IF;

  SELECT * INTO registry_row FROM asset_registry
  WHERE asset_id = 'bg_text_index' FOR UPDATE;

  IF NOT FOUND OR (
    registry_row.layer = 'brahmagyan'
    AND registry_row.sort_order = 5
    AND registry_row.scope = 'global'
    AND registry_row.asset_kind = 'data'
    AND registry_row.catalog_status = 'CURRENT'
    AND registry_row.is_active IS TRUE
    AND registry_row.has_writer IS TRUE
    AND registry_row.target_table = 'classical_text_chunks'
    AND registry_row.count_sql =
      'SELECT count(DISTINCT topic_tag) AS count FROM classical_text_chunks WHERE embedding IS NOT NULL AND topic_tag IS NOT NULL'
    AND registry_row.depends_on = ARRAY['bg_texts']::text[]
    AND registry_row.english_description =
      'Measurement of retrieval index health — distinct topic tags across embedded + indexed chunks. Retrieval tools point at bg_texts; this asset reports the index coverage metric.'
    AND (
      (
        registry_row.target_floor IN (361,400)
        AND registry_row.volume_explanation IN (
          'Distinct topic_tag count from embedded chunks. Floor 400 = topic-vocabulary coverage target; not scaled with chunk count (vocabulary size is independent of corpus depth). Per design §2.2.',
          'Distinct topic_tag values present on embedded classical_text_chunks. Grew from 327 to 361 after classifying 1,493 new chunks from bhrigu_nandi_nadi (608) and nadi_navamsa_patel (1,850); 3,716 nadi chunks had no keyword match and remain NULL topic_tag.',
          canonical_explanation
        )
        AND registry_row.natural_key_partition IS NULL
        AND registry_row.data_disposition IS NULL
        AND registry_row.integrity_check_sql IS NULL
      ) OR (
        registry_row.target_floor = 361
        AND registry_row.volume_explanation = canonical_explanation
        AND registry_row.natural_key_partition = canonical_partition
        AND registry_row.data_disposition IS NULL
        AND registry_row.integrity_check_sql = index_check
      )
    )
  ) IS NOT TRUE THEN
    RAISE EXCEPTION 'migration 617 refuses unknown bg_text_index registry contract';
  END IF;

  UPDATE asset_registry
  SET target_floor = 361,
      volume_explanation = canonical_explanation,
      natural_key_partition = canonical_partition,
      data_disposition = NULL,
      integrity_check_sql = index_check
  WHERE asset_id = 'bg_text_index';
  GET DIAGNOSTICS changed_rows = ROW_COUNT;
  IF changed_rows <> 1 THEN
    RAISE EXCEPTION 'migration 617 expected 1 registry row, updated %', changed_rows;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM asset_registry
    WHERE asset_id = 'bg_text_index'
      AND target_floor = 361
      AND volume_explanation = canonical_explanation
      AND natural_key_partition = canonical_partition
      AND data_disposition IS NULL
      AND integrity_check_sql = index_check
  ) THEN
    RAISE EXCEPTION 'migration 617 postflight registry mismatch';
  END IF;
END $$;
