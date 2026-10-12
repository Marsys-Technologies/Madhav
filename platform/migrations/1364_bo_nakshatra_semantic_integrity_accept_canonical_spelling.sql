-- 1364_bo_nakshatra_semantic_integrity_accept_canonical_spelling.sql
--
-- Certification migration 1364 (HELD with the one-canonical-nakshatra-spelling component PR): bo_nakshatra_semantic's registered
-- integrity_check_sql, vocabulary conjunct widened so it accepts BOTH nakshatra spellings during the merge-to-rebuild window.
-- ONE md5-guarded UPDATE of ONE column of ONE asset_registry row (asset_id 'bo_nakshatra_semantic'); nothing else. Transaction ownership
-- belongs to platform/scripts/migrate.ts (no BEGIN/COMMIT here). Data-only: no table, index or function is created or altered, so it runs as the
-- routine role (no DDL).
--
-- WHY. Migration 669 registered an eight-conjunct check whose third conjunct bounds configuration_jsonb->>'nakshatra' to 27 hard-coded names, and
-- those names are the OLD L1 spellings (Mrigashira, Mula, Dhanishta). The component PR this migration ships with makes L1 write the L0
-- lexicon's spellings instead (pyjhora_adapter._names derives from brahmagyan.nakshatra_vocabulary, whose names are the bg_nakshatra seed's
-- name_en): nakshatra no. 5 "Mrigasira", no. 19 "Moola", no. 23 "Dhanishtha". The bo_nakshatra_semantic emitter forwards the L1 fact's own text
-- into configuration_jsonb.nakshatra, so after the rebuild the native's Jupiter (in Moola) would read 'Moola', which the OLD list does not hold:
-- conjunct 3 would turn the asset's integrity check FALSE on the canonical chart, for a spelling that is correct. This migration prevents that.
--
-- WHAT. NEW = OLD (the live text: migration 669's $ic$ body, 2481 chars, md5 24f6f27a4d7a941445def16ebe95e899) with exactly ONE change: the NOT IN list of the
-- vocabulary conjunct holds 30 names instead of 27:
--   * the 27 names of the lexicon (CANONICAL_NAKSHATRA_NAMES, in nakshatra order; 24 of them are spelled exactly as the old list spelled them), and
--   * the three legacy L1 spellings (LEGACY_L1_SPELLINGS: Mrigashira, Mula, Dhanishta),
-- so a database that is still at the old spelling (between this migration's deploy and the L1/L2 rebuild) and a database after the rebuild both
-- read TRUE. Every other conjunct (tiling 9 per (chart, ayanamsha), pada 1..4, house_d1 1..12, tara range, tara_favorable truthfulness,
-- gandanta flag/zone consistency, dispositor_chain_length) is byte-identical. The list is built from the lexicon: a test
-- (platform/python-sidecar/tests/test_migration_1364_bo_nakshatra_semantic_integrity_spelling.py) pins this migration's list to
-- brahmagyan.nakshatra_vocabulary (canonical names + legacy keys), so a future lexicon change cannot silently leave this list behind.
--
-- NOT A WEAKER CHECK. The conjunct still rejects every string that is not one of the 27 nakshatras in either of the two spellings. It accepts
-- three additional strings, and each is the legacy spelling of a nakshatra already in the list; no other value passes that did not pass before
-- except the three canonical spellings. A follow-up migration may drop the three legacy names once the rebuild has rewritten every stored row
-- (the same retirement is owed to the tolerant readers named in the component PR); until then accepting them is what keeps the check honest on a
-- chart that has not been rebuilt yet.
--
-- WHY A REPLACEMENT AND NOT AN EDIT OF 669. 669 has been applied; a migration file is never edited after it is applied (CLAUDE.md N.4).
-- No later migration rewrites this text: a search of platform/migrations for 'bo_nakshatra_semantic' finds 669 (the only one that sets
-- integrity_check_sql for this asset), 450/660/905/908 (registry rows, output-digest spec, natural-key partition) and 1218/1296 (writer
-- timeouts, comment-only mentions of integrity_check_sql); 591 only describes the column in a comment.
--
-- GUARD AND WHAT HAPPENS WHEN IT DOES NOT MATCH (precedents 1326, 1340, 1324, 1363). The UPDATE is guarded by md5(integrity_check_sql) of the OLD
-- text. If the live text is anything else the migration is a NOTICE-and-NO-OP that does not fail the deploy (the NOTICE names the md5 found); the
-- check keeps whatever text it has until reconciled by hand. If the live text already equals the NEW text it is an idempotent no-op (NOTICE,
-- nothing rewritten, trigger not fired). The ONE case that RAISES: the UPDATE ran on the OLD text and the row does not carry the NEW md5
-- afterwards (the update silently did not take; never trust a silent no-op, CLAUDE.md N.4 / N.8).
--
-- SERVING EFFECT AT APPLY (binding). UPDATE ... SET integrity_check_sql fires the live trigger nirmana_registry_receipt_invalidation (migration
-- 596): AFTER UPDATE OF depends_on, natural_key_partition, health_probe, integrity_check_sql, target_floor, asset_kind, asset_type, scope,
-- has_writer, is_active, target_table, FOR EACH ROW WHEN (old.* IS DISTINCT FROM new.*), which sets asset_freshness.freshness_state = 'stale'
-- (reason registry_changed) WHERE asset_id = NEW.asset_id. So applying this STALES bo_nakshatra_semantic's freshness rows (every chart that
-- holds one) until its next build writes fresh receipts, exactly as 1221 / 1326 / 1363 did for ga_structural: the accepted cost of ANY change to
-- this text. No other asset is touched. A re-run updates 0 rows and does not fire the trigger.
--
-- VERIFICATION BY PRODUCTION STRUCTURE (never trust a deploy log). After the deploy, as the read-only role, expect md5 819cb0d44572c41dd26129dfce1679d6 and
-- length 2865:
--   SELECT asset_id, md5(integrity_check_sql), length(integrity_check_sql) FROM asset_registry WHERE asset_id = 'bo_nakshatra_semantic';
-- (these two figures are computed from the text in this file; the author read no production catalog).
--
-- NOT CHANGED HERE: any other asset's check, the writer, the L1/L2 rows (old spellings stay in chart_facts / bodha_msr_signals until the rebuild),
-- the TypeScript, any data row.
--
-- ROLLBACK (not executed by migrate.ts): UPDATE asset_registry SET integrity_check_sql = <migration 669's $ic$ body, md5 24f6f27a4d7a941445def16ebe95e899>
-- WHERE asset_id = 'bo_nakshatra_semantic' AND md5(integrity_check_sql) = '819cb0d44572c41dd26129dfce1679d6'; fires the same trigger.

SET LOCAL lock_timeout = '5s';

DO $m1364$
DECLARE
  c_old_md5  constant text := '24f6f27a4d7a941445def16ebe95e899';
  c_new_md5  constant text := '819cb0d44572c41dd26129dfce1679d6';
  c_new_text constant text := $nt$
SELECT
  (
    NOT EXISTS (
      SELECT chart_id, ayanamsha_id
      FROM bodha_msr_signals
      WHERE signal_type_class = 'nakshatra_semantic'
      GROUP BY chart_id, ayanamsha_id
      HAVING count(*) != 9
    )
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_msr_signals
    WHERE signal_type_class = 'nakshatra_semantic'
      AND (configuration_jsonb->>'pada')::int NOT BETWEEN 1 AND 4
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_msr_signals
    WHERE signal_type_class = 'nakshatra_semantic'
      AND configuration_jsonb->>'nakshatra' NOT IN (
        -- Migration 1364: the 27 names of the L0 lexicon (bg_nakshatra name_en), in nakshatra order, ...
        'Ashwini','Bharani','Krittika','Rohini','Mrigasira','Ardra',
        'Punarvasu','Pushya','Ashlesha','Magha','Purva Phalguni','Uttara Phalguni',
        'Hasta','Chitra','Swati','Vishakha','Anuradha','Jyeshtha',
        'Moola','Purva Ashadha','Uttara Ashadha','Shravana','Dhanishtha','Shatabhisha',
        'Purva Bhadrapada','Uttara Bhadrapada','Revati',
        -- ... plus the three spellings the L1 name table wrote before it adopted the lexicon (read-side tolerance for
        -- rows built before the single rebuild that rewrites them; retire these three once that rebuild has landed)
        'Mrigashira','Mula','Dhanishta'
      )
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_msr_signals
    WHERE signal_type_class = 'nakshatra_semantic'
      AND (configuration_jsonb->>'house_d1')::int NOT BETWEEN 1 AND 12
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_msr_signals
    WHERE signal_type_class = 'nakshatra_semantic'
      AND configuration_jsonb->>'tara_position' IS NOT NULL
      AND (configuration_jsonb->>'tara_position')::int NOT BETWEEN 1 AND 9
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_msr_signals
    WHERE signal_type_class = 'nakshatra_semantic'
      AND configuration_jsonb->>'tara_position' IS NOT NULL
      AND (configuration_jsonb->>'tara_favorable')::boolean
          != ((configuration_jsonb->>'tara_position')::int NOT IN (1,3,5,7))
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_msr_signals
    WHERE signal_type_class = 'nakshatra_semantic'
      AND (
        ((configuration_jsonb->>'gandanta_flag')::boolean = true
          AND configuration_jsonb->>'gandanta_zone' NOT LIKE 'gandanta_%')
        OR ((configuration_jsonb->>'gandanta_flag')::boolean = false
          AND configuration_jsonb->>'gandanta_zone' NOT IN ('not_applicable')
          AND configuration_jsonb->>'gandanta_zone' NOT LIKE 'end_pada_%'
          AND configuration_jsonb->>'gandanta_zone' NOT LIKE 'start_pada_%')
      )
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_msr_signals
    WHERE signal_type_class = 'nakshatra_semantic'
      AND (configuration_jsonb->>'dispositor_chain_length')::int
          != jsonb_array_length(configuration_jsonb->'dispositor_chain')
  )
$nt$;
  v_found boolean;
  v_live  text;
  v_md5   text;
BEGIN
  SELECT true, integrity_check_sql INTO v_found, v_live
    FROM asset_registry WHERE asset_id = 'bo_nakshatra_semantic' FOR UPDATE;
  IF v_found IS NOT TRUE THEN
    RAISE NOTICE '1364: no bo_nakshatra_semantic registry row (empty registry); nothing to do';
    RETURN;
  END IF;
  v_md5 := md5(v_live);
  IF v_md5 = c_new_md5 THEN
    RAISE NOTICE '1364: bo_nakshatra_semantic integrity_check_sql already accepts both nakshatra spellings; nothing to do';
    RETURN;
  ELSIF v_md5 IS DISTINCT FROM c_old_md5 THEN
    RAISE NOTICE '1364: bo_nakshatra_semantic integrity_check_sql is not the text this migration was written against (md5 %); NO-OP, integrity_check_sql left as is', v_md5;
    RETURN;
  END IF;

  UPDATE asset_registry
     SET integrity_check_sql = c_new_text
   WHERE asset_id = 'bo_nakshatra_semantic'
     AND md5(integrity_check_sql) = c_old_md5;

  SELECT md5(integrity_check_sql) INTO v_md5 FROM asset_registry WHERE asset_id = 'bo_nakshatra_semantic';
  IF v_md5 IS DISTINCT FROM c_new_md5 THEN
    RAISE EXCEPTION '1364: bo_nakshatra_semantic integrity_check_sql update did not take (md5 now %, expected %)', v_md5, c_new_md5;
  END IF;
END
$m1364$;
