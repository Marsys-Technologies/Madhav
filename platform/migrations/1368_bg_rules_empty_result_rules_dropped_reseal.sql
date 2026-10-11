-- 1368_bg_rules_empty_result_rules_dropped_reseal.sql
--
-- APPLY ORDER (rebuilds are governed, nothing here queues one):
--   (1) merge + deploy this migration TOGETHER WITH the l0_rules.py writer change it re-seals (same PR);
--   (2) rebuild bg_rules via the dispatch tool (forced; the rebuilt table has 2,994 rows and hashes to the NEW digest below, so the stored check reads TRUE);
--   (3) then rebuild what the dispatch tool names for a moved bg_rules fingerprint (bg_concordance and the dependants; see the PR for the measured set).
--   Until (2) the stored check reads FALSE (the live table still holds the 3,002 rows of migration 1366's content), exactly as after 1366 before its rebuild.
--
-- WHAT THIS IS. Census run A (Narr.agree, bg_rules) found 8 stored rules with no consequence: prediction_jsonb.result is "" (the trigger word ends the chunk) or a dash run.
-- The writer (platform/python-sidecar/brahmagyan/l0_rules.py extract_rules_from_chunk) now drops a match whose result has no word character. Replayed over the live 10,651-chunk
-- corpus (the real seed_rules, disposable PG17, PYTHONHASHSEED 0 and 3, both identical): 3,002 -> 2,994 rows, exactly those 8 rule ids removed (1e821404, 250e16ee, 89f90951,
-- a2074310, b1fe019d, bf8559e5, c5505bf1, f07803f3), the other 2,994 rows byte-identical, yoga links 17, transit markers 25, dasha links 0, content digest
--   OLD 1a0c275d9c175cef7df07825985f52dfb06e50c87fca84707530df3f959915c5  (migration 1366)
--   NEW 8e18dc1c02c8b815ed9f78be1e1843d917fb079f50b2ebee5d4dc032674cb9fc
-- The same replay with the unfixed writer reproduces the live 1a0c275d... (control).
--
-- WHAT CHANGES IN THE CHECK (and nothing else; the static test proves NEW = OLD with exactly these replacements): the three count literals 3002 -> 2994 (count(*), count(DISTINCT rule_id),
-- the python_regex_v2 count) and the content digest. The other seven clauses are untouched. Registry row asset_id 'bg_rules': integrity_check_sql, target_floor 3002 -> 2994 (the achieved
-- count, CLAUDE.md N.4: floors are aspirational, never fabricated rows) and volume_explanation (the number and the reason). ONE md5-guarded UPDATE of ONE row; no data row is read or changed.
-- Transaction ownership belongs to platform/scripts/migrate.ts (no BEGIN/COMMIT here). Data-only.
--   OLD check md5 b70718d7b77040c435f0aee2c436b287 (1463 chars, migration 1366)     NEW check md5 5b27581cbeee1e91f65951d9a30e7b62 (1463 chars)
--
-- NUMBER. 1368 (1364 is reserved for the nakshatra canonicalisation; 1365-1367 are applied). Re-check before opening.
--
-- STARTING STATES (exactly two accepted, anything else RAISES; precedent 1365/1366): (a) migration 1366's check byte-for-byte with target_floor 3002, the old volume_explanation and
-- natural_key_partition 'sutravali_rules.rule_id'; (b) this migration's NEW text, floor and explanation (replay: NOTICE, no-op, trigger not fired).
-- POSTFLIGHT: verifies the stored text, floor and explanation are exactly NEW; it does NOT execute the check (the live rows are the 3,002 until the governed rebuild).
-- SERVING EFFECT AT APPLY: the UPDATE fires nirmana_registry_receipt_invalidation: bg_rules freshness 'stale' (registry_changed) until the rebuild writes fresh receipts.
--
-- VERIFICATION BY PRODUCTION STRUCTURE (Trap 103). After the deploy expect md5 5b27581cbeee1e91f65951d9a30e7b62, length 1463, target_floor 2994:
--   SELECT asset_id, md5(integrity_check_sql), length(integrity_check_sql), target_floor FROM asset_registry WHERE asset_id = 'bg_rules';
-- ROLLBACK (not executed by migrate.ts): UPDATE asset_registry SET integrity_check_sql = <migration 1366's text>, target_floor = 3002, volume_explanation = <old text> WHERE asset_id = 'bg_rules'
-- AND md5(integrity_check_sql) = '5b27581cbeee1e91f65951d9a30e7b62'; only meaningful together with restoring the writer.

SET LOCAL lock_timeout = '5s';

DO $$
DECLARE
  registry_row asset_registry%ROWTYPE;
  changed_rows integer := 0;
  canonical_partition constant text := 'sutravali_rules.rule_id';
  old_explanation constant text :=
    '3,002 deterministic regex-extracted rules from the frozen '
    '10,651-chunk corpus after canonicalizing Pattern 27 planet order '
    'and duplicate suppression across Python hash seeds.';
  new_explanation constant text :=
    '2,994 deterministic regex-extracted rules from the frozen '
    '10,651-chunk corpus after canonicalizing Pattern 27 planet order '
    'and duplicate suppression across Python hash seeds; a match whose '
    'consequence has no word character is not kept (8 of the earlier '
    '3,002 were blank or dash-only).';
  old_digest constant text := '1a0c275d9c175cef7df07825985f52dfb06e50c87fca84707530df3f959915c5';
  new_digest constant text := '8e18dc1c02c8b815ed9f78be1e1843d917fb079f50b2ebee5d4dc032674cb9fc';
  old_md5 constant text := 'b70718d7b77040c435f0aee2c436b287';
  new_md5 constant text := '5b27581cbeee1e91f65951d9a30e7b62';
  old_check constant text := $oldcheck$
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
    '1a0c275d9c175cef7df07825985f52dfb06e50c87fca84707530df3f959915c5'
FROM sutravali_rules
$oldcheck$;
  new_check constant text := $newcheck$
SELECT
  count(*) = 2994
  AND count(DISTINCT rule_id) = 2994
  AND count(*) FILTER (WHERE extracted_by = 'python_regex_v2') = 2994
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
    '8e18dc1c02c8b815ed9f78be1e1843d917fb079f50b2ebee5d4dc032674cb9fc'
FROM sutravali_rules
$newcheck$;
BEGIN
  IF new_digest = old_digest OR new_md5 = old_md5 THEN
    RAISE EXCEPTION 'migration 1368 refuses: a re-seal must move the pin';
  END IF;
  -- Self-consistency of the embedded texts: OLD is migration 1366's text; NEW is OLD with exactly the digest and the three count literals replaced.
  IF md5(old_check) <> old_md5 OR length(old_check) <> 1463 THEN
    RAISE EXCEPTION 'migration 1368: embedded OLD check does not hash to migration 1366''s md5 %', old_md5;
  END IF;
  IF md5(new_check) <> new_md5
     OR position(old_digest IN new_check) <> 0
     OR (length(new_check) - length(replace(new_check, new_digest, ''))) <> 64
     OR position('3002' IN new_check) <> 0
     OR (length(new_check) - length(replace(new_check, '2994', ''))) <> 12
     OR replace(replace(replace(replace(old_check, old_digest, new_digest), 'count(*) = 3002', 'count(*) = 2994'),
                'count(DISTINCT rule_id) = 3002', 'count(DISTINCT rule_id) = 2994'),
                'extracted_by = ''python_regex_v2'') = 3002', 'extracted_by = ''python_regex_v2'') = 2994') IS DISTINCT FROM new_check THEN
    RAISE EXCEPTION 'migration 1368: embedded NEW check is not OLD with exactly the digest and the three count literals replaced (or does not hash to %)', new_md5;
  END IF;

  SELECT * INTO registry_row FROM asset_registry WHERE asset_id = 'bg_rules' FOR UPDATE;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'migration 1368 refuses: no bg_rules registry row';
  END IF;

  IF registry_row.integrity_check_sql IS NOT DISTINCT FROM new_check
     AND registry_row.target_floor = 2994 AND registry_row.volume_explanation = new_explanation THEN
    RAISE NOTICE '1368: bg_rules registry row already carries the 2,994-rule re-seal; nothing to do';
    RETURN;
  END IF;

  IF registry_row.integrity_check_sql IS DISTINCT FROM old_check
     OR registry_row.target_floor IS DISTINCT FROM 3002
     OR registry_row.volume_explanation IS DISTINCT FROM old_explanation
     OR registry_row.natural_key_partition IS DISTINCT FROM canonical_partition THEN
    RAISE EXCEPTION 'migration 1368 refuses unknown bg_rules registry state (expected migration 1366''s check, floor 3002, the old explanation and partition, or this migration''s row); found check md5 %, floor %',
      md5(registry_row.integrity_check_sql), registry_row.target_floor;
  END IF;

  UPDATE asset_registry
     SET integrity_check_sql = new_check,
         target_floor = 2994,
         volume_explanation = new_explanation
   WHERE asset_id = 'bg_rules'
     AND md5(integrity_check_sql) = old_md5
     AND target_floor = 3002
     AND volume_explanation = old_explanation
     AND natural_key_partition = canonical_partition;
  GET DIAGNOSTICS changed_rows = ROW_COUNT;
  IF changed_rows <> 1 THEN
    RAISE EXCEPTION 'migration 1368 expected to update exactly 1 bg_rules registry row, updated % (update did not take)', changed_rows;
  END IF;

  -- Postflight (does not execute the stored check; see the header).
  SELECT * INTO registry_row FROM asset_registry WHERE asset_id = 'bg_rules';
  IF md5(registry_row.integrity_check_sql) IS DISTINCT FROM new_md5
     OR registry_row.integrity_check_sql IS DISTINCT FROM new_check
     OR position(old_digest IN registry_row.integrity_check_sql) <> 0
     OR position(new_digest IN registry_row.integrity_check_sql) = 0
     OR registry_row.target_floor IS DISTINCT FROM 2994
     OR registry_row.volume_explanation IS DISTINCT FROM new_explanation
     OR registry_row.natural_key_partition IS DISTINCT FROM canonical_partition THEN
    RAISE EXCEPTION 'migration 1368 postflight registry mismatch';
  END IF;
END $$;
