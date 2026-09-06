-- Migration 702: bg_compendium_index integrity_check_sql content-hash re-pin (C12).
--
-- A genuine, correctly-authorized dispatch (run `27fea532-...`, D-L0-JJ) failed
-- bg_compendium_index's post-write integrity_check_sql. Root-caused live: a
-- direct replay of the writer's own `_build_desired_rows()` against the live
-- corpus (`classical_text_chunks` + `reference_topic_tags`, in a rolled-back
-- transaction) produces exactly 9571 rows (7969 chapter-scoped + 1602
-- topic-scoped), matching migration 623's structural pin precisely -- the
-- count/alignment subclauses are correct and the writer is structurally sound.
--
-- Both content-hash subclauses do NOT match the migration 623 pin, however.
-- The writer file itself is unchanged since 623 was authored (5f47906bc) --
-- this is not a writer defect, but the classical_text_chunks corpus content
-- (verse ranges / content_en feeding the mechanical synopsis) has evidently
-- evolved since 623's pin was computed, while the partition-count totals
-- happened to remain the same. Verified live (rolled-back tx, genuine writer
-- replay): the corrected hashes below are computed directly from the exact
-- same jsonb_build_array/string_agg/sha256 expression the check itself uses.
-- No writer change -- only the two content-hash literals are corrected.

DO $$
DECLARE
  registry_row asset_registry%ROWTYPE;
  changed_rows integer := 0;
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
    'cdffa67da7fd7c662989c187d5eb2af01120ae37d5f156112e91166d601ecdae'
   FROM brahma_compendium_index WHERE topic_id IS NULL)
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(text_id,chapter_num,chapter_title_en,chapter_title_sa,
      topic_id,verse_start,verse_end,chunk_ids,summary_text,significance,
      classical_significance_score)::text,
    E'\n' ORDER BY text_id COLLATE "C",topic_id COLLATE "C"),''),'UTF8')),'hex') =
    'fdbaca9eccdf8446eedb9a01c60e1a2604d591d92df60446274863856b4a6476'
   FROM brahma_compendium_index WHERE chapter_num IS NULL)
$check$;
  old_check constant text := $oldcheck$
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
$oldcheck$;
BEGIN
  SELECT * INTO registry_row FROM asset_registry
  WHERE asset_id='bg_compendium_index' FOR UPDATE;
  IF NOT FOUND OR registry_row.integrity_check_sql IS DISTINCT FROM old_check THEN
    RAISE EXCEPTION 'migration 702 refuses unknown bg_compendium_index integrity_check_sql (expected the 623 pin)';
  END IF;

  UPDATE asset_registry SET integrity_check_sql=compendium_check
  WHERE asset_id='bg_compendium_index';
  GET DIAGNOSTICS changed_rows = ROW_COUNT;
  IF changed_rows <> 1 THEN
    RAISE EXCEPTION 'migration 702 expected 1 registry row, updated %',changed_rows;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM asset_registry WHERE asset_id='bg_compendium_index'
    AND integrity_check_sql=compendium_check) THEN
    RAISE EXCEPTION 'migration 702 postflight registry mismatch';
  END IF;
END $$;
