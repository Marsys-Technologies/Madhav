-- 1366_bg_rules_integrity_digest_reseal.sql
--
-- APPLY ORDER (rebuilds are governed, nothing here queues one):
--   (1) merge + deploy this migration (it only matches the state migration 618 left: md5 7c155f20d9a983b3c86586007c01550d, target_floor 3002);
--   (2) rebuild bg_rules via the governed dispatch tool; the rebuilt sutravali_rules content hashes to the NEW digest below and the stored check reads TRUE;
--   (3) then rebuild the dependants/siblings the dispatch tool names for a moved bg_rules fingerprint (do not rebuild them before bg_rules).
--
-- WHAT THIS IS. Commit 829d8db1d (#3435) changed the bg_rules writer (platform/python-sidecar/brahmagyan/l0_rules.py `_graha_label`): graha labels in every
-- predicate_jsonb.description are now Title-case, and two stand-in rewrites changed. The rebuilt 3,002 rows therefore no longer hash to the sha256 content digest pinned by
-- migration 618 (87b697041c73359e12daf8258cfdd6e85a38eb5c63fa39865e42f5b46e610dbd), so the stored check reads FALSE after the rebuild. This migration RE-SEALS
-- asset_registry.integrity_check_sql of bg_rules; it never loosens the check. Nine of its ten clauses (row count, distinct rule ids, extractor, confidence floors,
-- confidence = quality_score, the 17 yoga links, the 0 dasha links, the 25 transit markers, the referential NOT EXISTS) are untouched; only the last clause's digest literal moves.
-- ONE md5-guarded UPDATE of ONE asset_registry row (asset_id = 'bg_rules'); no data row is read or changed here. Transaction ownership belongs to platform/scripts/migrate.ts
-- (no BEGIN/COMMIT here). Data-only: no table or function is created or altered. target_floor (3002), volume_explanation and natural_key_partition are guarded and unchanged.
--
-- NUMBER. 1366: highest on main is 1365 (1364 is claimed by another worker's unmerged work); no open PR claims 1366 or above. Re-check before opening.
--
-- WHAT CHANGES IN THE CHECK (and nothing else; the static test and a runtime assertion below prove NEW = OLD with exactly this one replacement):
--   OLD digest 87b697041c73359e12daf8258cfdd6e85a38eb5c63fa39865e42f5b46e610dbd  (migration 618; check md5 7c155f20d9a983b3c86586007c01550d, 1463 chars)
--   NEW digest 1a0c275d9c175cef7df07825985f52dfb06e50c87fca84707530df3f959915c5
--   NEW check md5 b70718d7b77040c435f0aee2c436b287
-- The NEW digest is measured from the rebuilt rows (the writer replayed on the evaluation copy, the method that produced migration 618's pin); it is NOT the output of this migration.
--
-- THIS FILE REFUSES TO RUN until the digest and md5 constants below are real hex (the fill script /Users/Dev/suvarna-evidence/N431/fill_bg_rules_reseal_digest.sh substitutes them
-- in this file and in its static test, and computes the md5 from the check text itself).
--
-- STARTING STATES (exactly two accepted, anything else RAISES; precedent 1365): (a) the integrity_check_sql is migration 618's text byte-for-byte (target_floor 3002,
-- canonical volume_explanation, natural_key_partition 'sutravali_rules.rule_id'); (b) it already is this migration's NEW text (replay: NOTICE, no-op, trigger not fired).
--
-- POSTFLIGHT CHOICE (precedent 1361, not 1365). The postflight does NOT execute the stored check: until the governed bg_rules rebuild the table still holds the OLD rows, so the
-- check would correctly read FALSE here and the migration would fail for the wrong reason. Instead it verifies the stored text is exactly NEW (md5 and text equality) and that
-- the old digest is gone and the new digest present exactly once. Replay-verification of the check on rebuilt rows happens at the rebuild, not here.
--
-- SERVING EFFECT AT APPLY (binding for every migration PR). UPDATE of integrity_check_sql fires the live trigger nirmana_registry_receipt_invalidation (migration 596;
-- WHEN old.* IS DISTINCT FROM new.*): it sets asset_freshness.freshness_state = 'stale' (reason registry_changed) WHERE asset_id = 'bg_rules' until the rebuild writes fresh receipts.
-- A re-run updates 0 rows and does not fire it. bg_rules reads FALSE on its integrity check from apply until the rebuild (it already does, with the old pin, after the writer change).
--
-- VERIFICATION BY PRODUCTION STRUCTURE (Trap 103). After the deploy, expect md5 b70718d7b77040c435f0aee2c436b287, length 1463, target_floor 3002:
--   SELECT asset_id, md5(integrity_check_sql), length(integrity_check_sql), target_floor FROM asset_registry WHERE asset_id = 'bg_rules';
--
-- ROLLBACK (not executed by migrate.ts): UPDATE asset_registry SET integrity_check_sql = <migration 618's rules_check> WHERE asset_id = 'bg_rules' AND md5(integrity_check_sql) = 'b70718d7b77040c435f0aee2c436b287';
-- (fires the same trigger; only meaningful together with restoring the previous writer labels).

SET LOCAL lock_timeout = '5s';

DO $$
DECLARE
  registry_row asset_registry%ROWTYPE;
  changed_rows integer := 0;
  canonical_partition constant text := 'sutravali_rules.rule_id';
  canonical_explanation constant text :=
    '3,002 deterministic regex-extracted rules from the frozen 10,651-chunk '
    'corpus after canonicalizing Pattern 27 planet order and duplicate '
    'suppression across Python hash seeds.';
  old_digest constant text := '87b697041c73359e12daf8258cfdd6e85a38eb5c63fa39865e42f5b46e610dbd';
  new_digest constant text := '1a0c275d9c175cef7df07825985f52dfb06e50c87fca84707530df3f959915c5';
  old_md5 constant text := '7c155f20d9a983b3c86586007c01550d';
  new_md5 constant text := 'b70718d7b77040c435f0aee2c436b287';
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
    '87b697041c73359e12daf8258cfdd6e85a38eb5c63fa39865e42f5b46e610dbd'
FROM sutravali_rules
$oldcheck$;
  new_check constant text := $newcheck$
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
$newcheck$;
BEGIN
  -- The constants must be real before anything is touched.
  IF new_digest !~ '^[0-9a-f]{64}$' OR new_md5 !~ '^[0-9a-f]{32}$' THEN
    RAISE EXCEPTION 'migration 1366 refuses: the NEW digest / NEW check md5 constants are not filled in (run fill_bg_rules_reseal_digest.sh with the measured digest)';
  END IF;
  IF new_digest = old_digest THEN
    RAISE EXCEPTION 'migration 1366 refuses: the NEW digest equals the OLD digest (a re-seal must move the pin)';
  END IF;
  -- Self-consistency of the embedded texts: OLD is migration 618's text, NEW is OLD with exactly the digest replaced.
  IF md5(old_check) <> old_md5 THEN
    RAISE EXCEPTION 'migration 1366: embedded OLD check does not hash to migration 618''s md5 %', old_md5;
  END IF;
  IF (length(old_check) - length(replace(old_check, old_digest, ''))) <> 64
     OR (length(new_check) - length(replace(new_check, new_digest, ''))) <> 64
     OR position(old_digest IN new_check) <> 0
     OR replace(old_check, old_digest, new_digest) IS DISTINCT FROM new_check
     OR md5(new_check) <> new_md5 THEN
    RAISE EXCEPTION 'migration 1366: embedded NEW check is not OLD with exactly one digest replacement (or does not hash to the stated md5 %)', new_md5;
  END IF;

  SELECT * INTO registry_row FROM asset_registry WHERE asset_id = 'bg_rules' FOR UPDATE;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'migration 1366 refuses: no bg_rules registry row';
  END IF;

  IF registry_row.integrity_check_sql IS NOT DISTINCT FROM new_check THEN
    RAISE NOTICE '1366: bg_rules integrity_check_sql already carries the re-sealed content digest; nothing to do';
    RETURN;
  END IF;

  IF registry_row.integrity_check_sql IS DISTINCT FROM old_check
     OR registry_row.target_floor IS DISTINCT FROM 3002
     OR registry_row.volume_explanation IS DISTINCT FROM canonical_explanation
     OR registry_row.natural_key_partition IS DISTINCT FROM canonical_partition THEN
    RAISE EXCEPTION 'migration 1366 refuses unknown bg_rules registry state (expected migration 618''s check, floor 3002, canonical explanation and partition, or this migration''s check); found check md5 %, floor %',
      md5(registry_row.integrity_check_sql), registry_row.target_floor;
  END IF;

  UPDATE asset_registry
     SET integrity_check_sql = new_check
   WHERE asset_id = 'bg_rules'
     AND md5(integrity_check_sql) = old_md5
     AND target_floor = 3002
     AND volume_explanation = canonical_explanation
     AND natural_key_partition = canonical_partition;
  GET DIAGNOSTICS changed_rows = ROW_COUNT;
  IF changed_rows <> 1 THEN
    RAISE EXCEPTION 'migration 1366 expected to update exactly 1 bg_rules registry row, updated % (update did not take)', changed_rows;
  END IF;

  -- Postflight (does not execute the stored check; see POSTFLIGHT CHOICE above).
  SELECT * INTO registry_row FROM asset_registry WHERE asset_id = 'bg_rules';
  IF md5(registry_row.integrity_check_sql) IS DISTINCT FROM new_md5
     OR registry_row.integrity_check_sql IS DISTINCT FROM new_check
     OR position(old_digest IN registry_row.integrity_check_sql) <> 0
     OR position(new_digest IN registry_row.integrity_check_sql) = 0
     OR registry_row.target_floor IS DISTINCT FROM 3002
     OR registry_row.volume_explanation IS DISTINCT FROM canonical_explanation
     OR registry_row.natural_key_partition IS DISTINCT FROM canonical_partition THEN
    RAISE EXCEPTION 'migration 1366 postflight registry mismatch';
  END IF;
END $$;
