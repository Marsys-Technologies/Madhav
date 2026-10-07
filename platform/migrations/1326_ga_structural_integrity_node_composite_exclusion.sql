-- 1326_ga_structural_integrity_node_composite_exclusion.sql
--
-- Suvarna routine migration 1326 (block 1320-1329 claimed on campaign-coordination; reviewer finding (d) of PR #3215, REVIEW_3215):
-- exclude the two mean nodes (Rahu, Ketu) from ga_structural's integrity conjunct (b4) ONLY, so the check stays true after the pass.
-- ONE md5-guarded UPDATE of ONE column of ONE asset_registry row (asset_id 'ga_structural'); nothing else. Transaction ownership
-- belongs to platform/scripts/migrate.ts (no BEGIN/COMMIT here). Data-only: no table or function is created or altered, so it runs
-- as the routine role (amjis_app: no DDL, no CREATE on public).
--
-- THE DEFECT (a time bomb, not a failing check today). Conjunct (b4) re-derives the whole composite-state decision tree of
-- graha_composite_state_classification table-wide from first principles, and its last two branches read
--     WHEN re.re_dignity IN ('exalted', 'own_sign') THEN 'well_placed'
--     WHEN re.retrograde_flag = 'retrograde' THEN 'weak'
--     ELSE 'neutral'
-- where retrograde_flag is graha_position.retrograde_flag. For the mean nodes re_dignity is always 'neutral' (the dignity tables
-- carry the seven tara grahas only). PR #3205 (merged) makes ga_positions store retrograde_flag = 'retrograde' for Rahu and Ketu
-- (they are always retrograde; today the 30 node rows read 'direct'), while the writer deliberately keeps the retrograde composite
-- downgrade OFF the nodes (N-185 / N-187; PR #3215: ga_structural_writer.py composite weak branch excludes _MEAN_NODE_GRAHA_NAMES), so
-- every node composite row stays 'neutral'. After the pass's ga_positions and ga_structural rebuild the check would re-derive 'weak'
-- for those 30 node rows (RAH_MEAN and KET_MEAN, 15 each, read 2026-10-07: all 'neutral') and flag every one of them: (b4) false on a
-- CORRECT build.
--
-- THE CHANGE. In (b4) the one line
--           WHEN re.retrograde_flag = 'retrograde' THEN 'weak'
-- becomes a three-line explanatory comment plus
--           WHEN re.retrograde_flag = 'retrograde' AND a.fact_subject NOT IN ('RAH_MEAN', 'KET_MEAN') THEN 'weak'
-- The exclusion is ONLY for the two node subjects (the exact fact_subject values ga_structural writes for them, as every other
-- conjunct of the same text uses them). A tara-graha (Sun..Saturn) row that is retrograde and not downgraded still FAILS the check.
-- The rest of the text, all other conjuncts and all other lines of (b4), is BYTE-IDENTICAL to the live text (a static test proves the
-- new text is the live text with exactly this one line replaced).
--
-- OTHER RETROGRADE-CONDITIONAL CONJUNCTS (audited; none changed). The live text (207,959 chars) mentions retrograde in two
-- executable places only: (b4) above and (c7). (c7) says graha_special_state_rollup.is_retrograde must equal
-- (graha_position.retrograde_flag = 'retrograde'); with #3215 the rollup stores 'true' for the nodes, so (c7) holds once ga_positions
-- AND ga_structural have both rebuilt on every chart (it reads table-wide), and it needs NO node exclusion (it is an equality of two
-- stored flags, not a re-derived classification). The avastha deepta conjuncts (ss), (vv) and the jagrad<->deepta term read stored
-- deepta_state and the dignity branch only (no retrograde read), and no conjunct reads retrograde_aspect_modification. No other
-- asset's integrity text reads graha_position.retrograde_flag, graha_special_state_rollup or graha_composite_state_classification
-- (read 2026-10-07: only ga_structural and, unrelatedly, ga_sade_sati's transit-retrograde-period ordering term).
--
--   OLD (live, read 2026-10-07 as suvarna_reader; md5 c56f9e12b2002269eb5f27a7abc42105, 207959 chars; = migration 904 as patched by 1219/1221)
--   NEW (md5 fcd217e25127653ee28ad41c629946aa, 208378 chars)
--
-- WHY replace() AND NOT THE FULL TEXT. The text is 208 KB; the precedent for a surgical edit of it is migration 1221 (replace of a
-- named block). Here the replacement is guarded by the md5 of the WHOLE old text (not by a block count), so it can only ever produce
-- the one NEW text: the block is present exactly once in the text with the OLD md5 (proved by the static test).
--
-- GUARD AND WHAT HAPPENS WHEN IT DOES NOT MATCH (precedents 1259, 1297, 1299). The UPDATE is guarded by md5(integrity_check_sql) of
-- the OLD text. If the live text is anything else the migration is a NOTICE-and-NO-OP that does not fail the deploy (the NOTICE
-- names the md5 found); the check keeps whatever text it has until reconciled by hand. If the live text already equals the NEW text
-- it is an idempotent no-op (NOTICE, nothing rewritten, trigger not fired). The ONE case that RAISES: the UPDATE ran on the OLD
-- text and the row does not carry the NEW md5 afterwards (the update silently did not take; never trust a silent no-op, CLAUDE.md
-- N.4 / Trap 103). No active-run guard (as 1299): a build straddling the apply reads the new text at its next check.
--
-- SERVING EFFECT AT APPLY (binding). `UPDATE ... SET integrity_check_sql` fires the live trigger
-- nirmana_registry_receipt_invalidation (migration 596): AFTER UPDATE OF depends_on, natural_key_partition, health_probe,
-- integrity_check_sql, target_floor, asset_kind, asset_type, scope, has_writer, is_active, target_table, FOR EACH ROW WHEN
-- (old.* IS DISTINCT FROM new.*), which sets asset_freshness.freshness_state = 'stale' (reason registry_changed) WHERE asset_id =
-- NEW.asset_id. So applying this STALES ga_structural's freshness rows (every chart that holds one), and integrity_check_sql is part
-- of the Nirmana registry-contract fingerprint (see 1221's header: a frozen ga_structural manifest goes to evidence_refresh_required
-- until re-bound). That is accepted: ga_structural is rebuilt in the pass (#3204 / #3215), which writes fresh receipts. No other
-- asset is touched (the trigger is keyed on NEW.asset_id). A re-run updates 0 rows and does not fire the trigger.
--
-- VERIFICATION BY PRODUCTION STRUCTURE (Trap 103: never trust a deploy log). After the deploy, as suvarna_reader, expect
-- md5 fcd217e25127653ee28ad41c629946aa and length 208378:
--   SELECT asset_id, md5(integrity_check_sql), length(integrity_check_sql) FROM asset_registry WHERE asset_id = 'ga_structural';
-- (the acceptance SELECTs are 00_ARCHITECTURE/briefs/suvarna/exec/s_l2_acceptance/ACCEPTANCE_GA_STRUCTURAL_NODE_INTEGRITY.sql.txt).
--
-- NOT CHANGED HERE: any other conjunct or line, any other asset's check, the writer, the TypeScript (ga_structural's integrity text
-- is carried by no TypeScript seed; its sources are migrations 904/1219/1221, which are never edited after apply), any data row.
--
-- ROLLBACK (not executed by migrate.ts): UPDATE asset_registry SET integrity_check_sql = replace(integrity_check_sql, <the NEW
-- three-comment-plus-WHEN block>, <the OLD single line>) WHERE asset_id = 'ga_structural' AND md5(integrity_check_sql) =
-- 'fcd217e25127653ee28ad41c629946aa'; fires the same trigger. Restoring the old text makes (b4) false on any build that stores
-- retrograde nodes.

SET LOCAL lock_timeout = '5s';

DO $m1326$
DECLARE
  c_old_md5  constant text := 'c56f9e12b2002269eb5f27a7abc42105';
  c_new_md5  constant text := 'fcd217e25127653ee28ad41c629946aa';
  c_old_line constant text := $ol$          WHEN re.retrograde_flag = 'retrograde' THEN 'weak'
$ol$;
  c_new_line constant text := $nl$          -- Migration 1326 (node exclusion): the mean nodes Rahu/Ketu are always retrograde and ga_positions stores
          -- retrograde_flag 'retrograde' for them (N-185/N-187), but the retrograde composite downgrade does NOT apply to the
          -- nodes (their re_dignity is always 'neutral'); a node row therefore stays 'neutral'. Tara grahas are unchanged.
          WHEN re.retrograde_flag = 'retrograde' AND a.fact_subject NOT IN ('RAH_MEAN', 'KET_MEAN') THEN 'weak'
$nl$;
  v_found boolean;
  v_live  text;
  v_md5   text;
BEGIN
  SELECT true, integrity_check_sql INTO v_found, v_live
    FROM asset_registry WHERE asset_id = 'ga_structural' FOR UPDATE;
  IF v_found IS NOT TRUE THEN
    RAISE NOTICE '1326: no ga_structural registry row (empty registry); nothing to do';
    RETURN;
  END IF;
  v_md5 := md5(v_live);
  IF v_md5 = c_new_md5 THEN
    RAISE NOTICE '1326: ga_structural integrity_check_sql already carries the node exclusion in (b4); nothing to do';
    RETURN;
  ELSIF v_md5 IS DISTINCT FROM c_old_md5 THEN
    RAISE NOTICE '1326: ga_structural integrity_check_sql is not the text this migration was written against (md5 %); NO-OP, integrity_check_sql left as is', v_md5;
    RETURN;
  END IF;

  UPDATE asset_registry
     SET integrity_check_sql = replace(integrity_check_sql, c_old_line, c_new_line)
   WHERE asset_id = 'ga_structural'
     AND md5(integrity_check_sql) = c_old_md5;

  SELECT md5(integrity_check_sql) INTO v_md5 FROM asset_registry WHERE asset_id = 'ga_structural';
  IF v_md5 IS DISTINCT FROM c_new_md5 THEN
    RAISE EXCEPTION '1326: ga_structural integrity_check_sql update did not take (md5 now %, expected %)', v_md5, c_new_md5;
  END IF;
END
$m1326$;
