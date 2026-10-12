-- 1370_bg_concordance_rule_ids_digest_reseal.sql
--
-- APPLY ORDER (rebuilds are governed, nothing here queues one):
--   (1) merge + deploy this migration;
--   (2) rebuild bg_concordance ALONE through the governed dispatch tool (forced; the rebuilt projection hashes to the NEW digest below, so the stored check reads TRUE).
--   Until (2) the stored check reads FALSE: the live projection still lists rule ids that the rules table no longer holds (see WHY).
--
-- WHY. bg_concordance's projection (classical_attributions, 721 rows) lists, per (topic, school), the ids of EVERY rule of the source texts (the writer joins the rules table by
-- text_id), and its stored check (a) requires every listed rule id to exist and (b) pins a sha256 content digest over all 721 rows INCLUDING the rule_ids column. The rules table
-- dropped 8 rules that had no consequence (3,002 -> 2,994; migration 1368): 357 of the 721 rows listed at least one of them. A rebuild therefore (correctly) drops those ids and the
-- old pin 9e283738... can no longer hold: the first rebuild after that release failed its post-write check (run 966719ef, write rolled back, projection unchanged). The writer is
-- right, the PIN is stale: the same class as 1366 / 1368.
--
-- MEASUREMENT (the real writer, brahmagyan/pipeline/orchestrator/writers/bg_concordance.py ConcordanceWriter.run, on a disposable PostgreSQL 17, PYTHONHASHSEED 0 and 3, same digest):
--   * inputs read from production as the read-only role: 481 reference topic tags, the 7,010 tagged chunk rows (topic_tag, text_id), the live 2,994 rules (rule_id, text_id);
--   * CONTROL: the writer on the 3,002-rule corpus (the 8 rules added back) reproduces the OLD pin 9e2837388c783be0dc57361e52d8de344b2b041f9bb5e9eb39fa4b67412f5893 exactly;
--     the OLD live rows hashed with the check's own expression give the same value (method validated two ways);
--   * the writer on the 2,994-rule corpus: 721 rows, digest
--       NEW a19bebde564c17c4ae39b883da3bf206122a3803098cca0b3de8087001152525
--   * old live rows vs new rows (joined on topic_id, school): 721 joined, 357 rows differ in rule_ids ONLY (991 rule ids removed in total), 0 rows differ in any other column,
--     the smallest new rule_ids list still has 4 ids (so the cardinality clause stays true); the NEW check text evaluates TRUE on the new rows and the OLD pin text FALSE on them.
--
-- WHAT CHANGES (and nothing else; the static test proves NEW = OLD with exactly this one literal replaced): in the stored check the sha256 digest literal, ONE column of ONE
-- registry row. The prose in volume_explanation ("canonical 3,002-rule projection") is NOT touched: the check never reads it, and moving it would move three more pins (the
-- migration that set it, the registry seed and its contract test); it is left as a stale description and listed as a follow-up. target_floor (721), natural_key_partition and
-- volume_explanation are guarded and unchanged. ONE md5-guarded UPDATE of ONE registry row; no data row is read or changed. Transaction ownership belongs to
-- platform/scripts/migrate.ts (no BEGIN/COMMIT here). Data-only.
--   OLD check md5 4327da1774c67a35a43ed0c2e2a19fe2 (1994 chars)       NEW check md5 c4dd504f6a112569a176d749489f6bbd (1994 chars)
--
-- STARTING STATES (exactly two accepted, anything else RAISES): (a) the OLD check text byte-for-byte with floor 721, the registered explanation and the partition key; (b) this migration's
-- NEW text with the same floor, explanation and partition (replay: NOTICE, no-op, trigger not fired). POSTFLIGHT verifies the stored text, floor, explanation and partition are as expected; it does NOT execute the check (the live rows
-- are the pre-run projection until the governed rebuild).
-- SERVING EFFECT AT APPLY: the UPDATE fires nirmana_registry_receipt_invalidation: this asset's freshness becomes 'stale' (registry_changed) until the rebuild writes fresh receipts.
--
-- VERIFICATION BY PRODUCTION STRUCTURE (Trap 103). After the deploy expect md5 c4dd504f6a112569a176d749489f6bbd, length 1994, target_floor 721:
--   SELECT asset_id, md5(integrity_check_sql), length(integrity_check_sql), target_floor FROM asset_registry WHERE asset_id = 'bg_concordance';
-- ROLLBACK (not executed by migrate.ts): UPDATE asset_registry SET integrity_check_sql = <the OLD text> WHERE asset_id = 'bg_concordance'
-- AND md5(integrity_check_sql) = 'c4dd504f6a112569a176d749489f6bbd'; only meaningful together with the old rules table.

SET LOCAL lock_timeout = '5s';

DO $$
DECLARE
  registry_row asset_registry%ROWTYPE;
  changed_rows integer := 0;
  canonical_partition constant text := 'classical_attributions.(topic_id,school)';
  canonical_explanation constant text := $expl$721 deterministic topic×school concordance rows from the frozen 10,651-chunk topic index and canonical 3,002-rule projection. The convergent rebuild repairs stale pointers and includes lord_1st_in_11th, whose tagged chunks existed in production while its historical concordance row was absent.$expl$;
  old_digest constant text := '9e2837388c783be0dc57361e52d8de344b2b041f9bb5e9eb39fa4b67412f5893';
  new_digest constant text := 'a19bebde564c17c4ae39b883da3bf206122a3803098cca0b3de8087001152525';
  old_md5 constant text := '4327da1774c67a35a43ed0c2e2a19fe2';
  new_md5 constant text := 'c4dd504f6a112569a176d749489f6bbd';
  old_check constant text := $oldcheck$
SELECT
  count(*) = 721
  AND count(DISTINCT topic_id) = 361
  AND count(DISTINCT (topic_id,school)) = 721
  AND array_agg(DISTINCT school ORDER BY school) =
    ARRAY['jaimini','nadi','parashari','phaladeepika']::text[]
  AND count(*) FILTER (WHERE cardinality(source_text_ids) > 0) = 721
  AND count(*) FILTER (WHERE cardinality(source_chunk_ids) = 0) = 721
  AND count(*) FILTER (WHERE cardinality(rule_ids) > 0) = 721
  AND count(*) FILTER (WHERE match_method = 'topic_tag') = 721
  AND count(*) FILTER (
    WHERE match_confidence IN (0.200,0.400,0.600,0.800,1.000)
  ) = 721
  AND NOT EXISTS (
    SELECT 1 FROM classical_attributions AS attribution
    LEFT JOIN reference_topic_tags AS topic
      ON topic.canonical_id = attribution.topic_id
    WHERE topic.canonical_id IS NULL
       OR topic.name IS DISTINCT FROM attribution.topic_canonical_name
       OR topic.category IS DISTINCT FROM attribution.topic_category
  )
  AND NOT EXISTS (
    SELECT 1
    FROM classical_attributions AS attribution
    CROSS JOIN LATERAL unnest(attribution.source_text_ids) AS source(text_id)
    WHERE NOT EXISTS (
      SELECT 1 FROM classical_text_chunks AS chunk
      WHERE chunk.topic_tag = attribution.topic_id
        AND chunk.text_id = source.text_id
    )
  )
  AND NOT EXISTS (
    SELECT 1
    FROM classical_attributions AS attribution
    CROSS JOIN LATERAL unnest(attribution.rule_ids) AS source(rule_id)
    WHERE NOT EXISTS (
      SELECT 1 FROM sutravali_rules AS rule
      WHERE rule.rule_id = source.rule_id
        AND rule.text_id = ANY(attribution.source_text_ids)
    )
  )
  AND encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(topic_id,topic_canonical_name,topic_category,school,
      source_text_ids,source_chunk_ids,rule_ids,match_method,match_confidence)::text,
    E'\n' ORDER BY topic_id COLLATE "C",school COLLATE "C"
  ),''),'UTF8')),'hex') =
    '9e2837388c783be0dc57361e52d8de344b2b041f9bb5e9eb39fa4b67412f5893'
FROM classical_attributions
$oldcheck$;
  new_check constant text := $newcheck$
SELECT
  count(*) = 721
  AND count(DISTINCT topic_id) = 361
  AND count(DISTINCT (topic_id,school)) = 721
  AND array_agg(DISTINCT school ORDER BY school) =
    ARRAY['jaimini','nadi','parashari','phaladeepika']::text[]
  AND count(*) FILTER (WHERE cardinality(source_text_ids) > 0) = 721
  AND count(*) FILTER (WHERE cardinality(source_chunk_ids) = 0) = 721
  AND count(*) FILTER (WHERE cardinality(rule_ids) > 0) = 721
  AND count(*) FILTER (WHERE match_method = 'topic_tag') = 721
  AND count(*) FILTER (
    WHERE match_confidence IN (0.200,0.400,0.600,0.800,1.000)
  ) = 721
  AND NOT EXISTS (
    SELECT 1 FROM classical_attributions AS attribution
    LEFT JOIN reference_topic_tags AS topic
      ON topic.canonical_id = attribution.topic_id
    WHERE topic.canonical_id IS NULL
       OR topic.name IS DISTINCT FROM attribution.topic_canonical_name
       OR topic.category IS DISTINCT FROM attribution.topic_category
  )
  AND NOT EXISTS (
    SELECT 1
    FROM classical_attributions AS attribution
    CROSS JOIN LATERAL unnest(attribution.source_text_ids) AS source(text_id)
    WHERE NOT EXISTS (
      SELECT 1 FROM classical_text_chunks AS chunk
      WHERE chunk.topic_tag = attribution.topic_id
        AND chunk.text_id = source.text_id
    )
  )
  AND NOT EXISTS (
    SELECT 1
    FROM classical_attributions AS attribution
    CROSS JOIN LATERAL unnest(attribution.rule_ids) AS source(rule_id)
    WHERE NOT EXISTS (
      SELECT 1 FROM sutravali_rules AS rule
      WHERE rule.rule_id = source.rule_id
        AND rule.text_id = ANY(attribution.source_text_ids)
    )
  )
  AND encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(topic_id,topic_canonical_name,topic_category,school,
      source_text_ids,source_chunk_ids,rule_ids,match_method,match_confidence)::text,
    E'\n' ORDER BY topic_id COLLATE "C",school COLLATE "C"
  ),''),'UTF8')),'hex') =
    'a19bebde564c17c4ae39b883da3bf206122a3803098cca0b3de8087001152525'
FROM classical_attributions
$newcheck$;
BEGIN
  IF new_digest = old_digest OR new_md5 = old_md5 THEN
    RAISE EXCEPTION 'migration 1370 refuses: a re-seal must move the pin';
  END IF;
  -- Self-consistency of the embedded texts: NEW is OLD with exactly the digest literal replaced.
  IF md5(old_check) <> old_md5 OR length(old_check) <> 1994 THEN
    RAISE EXCEPTION 'migration 1370: embedded OLD check does not hash to the live text md5 %', old_md5;
  END IF;
  IF md5(new_check) <> new_md5
     OR position(old_digest IN new_check) <> 0
     OR (length(new_check) - length(replace(new_check, new_digest, ''))) <> 64
     OR replace(old_check, old_digest, new_digest) IS DISTINCT FROM new_check THEN
    RAISE EXCEPTION 'migration 1370: embedded NEW check is not OLD with exactly the digest replaced (or does not hash to %)', new_md5;
  END IF;

  SELECT * INTO registry_row FROM asset_registry WHERE asset_id = 'bg_concordance' FOR UPDATE;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'migration 1370 refuses: no bg_concordance registry row';
  END IF;

  IF registry_row.integrity_check_sql IS NOT DISTINCT FROM new_check
     AND registry_row.target_floor = 721
     AND registry_row.volume_explanation = canonical_explanation
     AND registry_row.natural_key_partition = canonical_partition THEN
    RAISE NOTICE '1370: bg_concordance registry row already carries the re-sealed digest; nothing to do';
    RETURN;
  END IF;

  IF registry_row.integrity_check_sql IS DISTINCT FROM old_check
     OR registry_row.target_floor IS DISTINCT FROM 721
     OR registry_row.volume_explanation IS DISTINCT FROM canonical_explanation
     OR registry_row.natural_key_partition IS DISTINCT FROM canonical_partition THEN
    RAISE EXCEPTION 'migration 1370 refuses unknown bg_concordance registry state (expected the OLD check, floor 721, the registered explanation and partition, or this migration''s row); found check md5 %, floor %',
      md5(registry_row.integrity_check_sql), registry_row.target_floor;
  END IF;

  UPDATE asset_registry
     SET integrity_check_sql = new_check
   WHERE asset_id = 'bg_concordance'
     AND md5(integrity_check_sql) = old_md5
     AND target_floor = 721
     AND volume_explanation = canonical_explanation
     AND natural_key_partition = canonical_partition;
  GET DIAGNOSTICS changed_rows = ROW_COUNT;
  IF changed_rows <> 1 THEN
    RAISE EXCEPTION 'migration 1370 expected to update exactly 1 bg_concordance registry row, updated % (update did not take)', changed_rows;
  END IF;

  -- Postflight (does not execute the stored check; see the header).
  SELECT * INTO registry_row FROM asset_registry WHERE asset_id = 'bg_concordance';
  IF md5(registry_row.integrity_check_sql) IS DISTINCT FROM new_md5
     OR registry_row.integrity_check_sql IS DISTINCT FROM new_check
     OR position(old_digest IN registry_row.integrity_check_sql) <> 0
     OR position(new_digest IN registry_row.integrity_check_sql) = 0
     OR registry_row.target_floor IS DISTINCT FROM 721
     OR registry_row.volume_explanation IS DISTINCT FROM canonical_explanation
     OR registry_row.natural_key_partition IS DISTINCT FROM canonical_partition THEN
    RAISE EXCEPTION 'migration 1370 postflight registry mismatch';
  END IF;
END $$;
