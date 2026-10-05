-- 1297_bo_cdlm_summary_count_sql_three_tables.sql
--
-- Suvarna S-L2 FAST PATH (number 1297 allocated by SS): widen asset_registry.count_sql of bo_cdlm_summary so the cockpit /
-- Build.completion probe counts what the writer actually writes. ONE md5-guarded UPDATE of ONE column (count_sql) of ONE
-- asset_registry row; nothing else. Transaction ownership belongs to platform/scripts/migrate.ts (no BEGIN/COMMIT here). Data-only:
-- no table or function is created or altered, so it runs fine as amjis_app (no CREATE on schema public needed).
--
-- THE DEFECT. pipeline/orchestrator/writers/bo_cdlm_summary.py writes THREE tables per chart (_SUMMARY_INSERT ->
-- bodha_cdlm_chart_summary, _ROLLUP_INSERT -> bodha_cdlm_domain_rollups, _CLUSTER_INSERT -> bodha_cdlm_pattern_clusters; 5 + 60 rollups +
-- 5 clusters = 70 rows on the canonical chart 482012f1-710e-4a25-994a-93821f5871aa), but the registered count_sql counts only
-- bodha_cdlm_chart_summary (5). Build.completion therefore compares rows_written 70 with the live count 5.
--
--   OLD (live, read 2026-10-05 as suvarna_reader; md5 a6ff09db0588b92339d631f422d69cc7, 65 chars):
--     SELECT count(*) FROM bodha_cdlm_chart_summary WHERE chart_id = $1
--   NEW (md5 436138f8ef007f232680cf2673233019, 292 chars; the "AS count" shape of bo_anveshana / bo_sangati /
--   mi_adhilepa, which also sum several tables; the chart parameter $1 appears EXACTLY ONCE, in a CTE, on purpose: the orchestrator's
--   data-presence probe asset_runner._data_rows_present does count_sql.replace("$1", "%s") and binds ONE parameter, so a text with
--   $1 repeated per table would raise in psycopg and the probe would silently answer None for this asset, a regression from today's
--   working probe; node-postgres and the cockpit/watchdog routes bind [chart_id] to $1 and are indifferent):
--     WITH p AS (SELECT $1::uuid AS cid) SELECT (SELECT count(*) FROM bodha_cdlm_chart_summary s, p WHERE s.chart_id = p.cid) + (SELECT count(*) FROM bodha_cdlm_domain_rollups r, p WHERE r.chart_id = p.cid) + (SELECT count(*) FROM bodha_cdlm_pattern_clusters c, p WHERE c.chart_id = p.cid) AS count
--   All three tables carry chart_id uuid (read from information_schema, 2026-10-05).
--
-- GUARD AND WHAT HAPPENS WHEN IT DOES NOT MATCH. The UPDATE is guarded by md5(count_sql) of the OLD text, so it only ever replaces the
-- exact text it was written against. If the live text is anything else (someone edited it meanwhile) the UPDATE matches 0 rows and the
-- migration is a NO-OP that emits a NOTICE and does NOT fail the deploy (count_sql is a cockpit/completion probe, not data; failing every
-- deploy for it would be disproportionate, unlike an integrity check). Consequence of that no-op: the probe keeps whatever text it has
-- (Build.completion keeps comparing 70 with the old count) until the new text is reconciled by hand; the NOTICE names the md5 found.
-- If the live text already equals the NEW text the migration is an idempotent no-op (NOTICE, nothing rewritten). The ONE case that
-- RAISES: the post-check finds the row still carries the OLD md5 (the UPDATE silently did nothing; never trust a silent no-op,
-- CLAUDE.md N.4 / Trap 103).
--
-- NO TRIGGER EFFECT. nirmana_registry_receipt_invalidation (migration 596) fires only AFTER UPDATE OF depends_on, natural_key_partition,
-- health_probe, integrity_check_sql, target_floor, asset_kind, asset_type, scope, has_writer, is_active, target_table. count_sql is NOT
-- among them and none of those columns is written here, so no asset_freshness row of any asset changes (proved by the live test with the
-- production trigger body). No active-run guard is needed for the same reason: the text is read at completion time by the probe, and a
-- run that straddles the apply simply reads the new text.
--
-- NOT CHANGED HERE: target_table (stays bodha_cdlm_chart_summary), target_floor (5; floors are aspirational), size_sql,
-- volume_explanation, the TypeScript seed (its registry insert is ON CONFLICT DO NOTHING; a fresh database replaying the seed and then
-- the migrations holds the OLD text, matches the guard, and is widened here), any data row, any writer.
--
-- VERIFICATION BY PRODUCTION STRUCTURE (Trap 103: never trust a deploy log). After the deploy, as suvarna_reader, expect
-- md5 436138f8ef007f232680cf2673233019 and length 292:
--   SELECT asset_id, md5(count_sql), length(count_sql) FROM asset_registry WHERE asset_id = 'bo_cdlm_summary';
-- and, executed with the canonical chart in place of $1 (read-only), 70 on the canonical chart while the current rows stand (read
-- 2026-10-05: 5 summary + 60 rollups + 5 clusters; re-read at verification, not asserted by this migration).
--
-- ROLLBACK (not executed by migrate.ts): UPDATE asset_registry SET count_sql = 'SELECT count(*) FROM bodha_cdlm_chart_summary WHERE chart_id = $1'
-- WHERE asset_id = 'bo_cdlm_summary' AND md5(count_sql) = '436138f8ef007f232680cf2673233019';

SET LOCAL lock_timeout = '5s';

DO $pre$
DECLARE v_n int; v_md5 text;
BEGIN
  SELECT count(*), max(md5(count_sql)) INTO v_n, v_md5 FROM asset_registry WHERE asset_id = 'bo_cdlm_summary';
  IF v_n = 0 THEN
    RAISE NOTICE '1297: no bo_cdlm_summary registry row (empty registry); nothing to do';
  ELSIF v_md5 = '436138f8ef007f232680cf2673233019' THEN
    RAISE NOTICE '1297: bo_cdlm_summary count_sql already counts the three tables; nothing to do';
  ELSIF v_md5 IS DISTINCT FROM 'a6ff09db0588b92339d631f422d69cc7' THEN
    RAISE NOTICE '1297: bo_cdlm_summary count_sql is not the text this migration was written against (md5 %); NO-OP, count_sql left as is', v_md5;
  END IF;
END
$pre$;

UPDATE asset_registry
SET count_sql = $cs$WITH p AS (SELECT $1::uuid AS cid) SELECT (SELECT count(*) FROM bodha_cdlm_chart_summary s, p WHERE s.chart_id = p.cid) + (SELECT count(*) FROM bodha_cdlm_domain_rollups r, p WHERE r.chart_id = p.cid) + (SELECT count(*) FROM bodha_cdlm_pattern_clusters c, p WHERE c.chart_id = p.cid) AS count$cs$
WHERE asset_id = 'bo_cdlm_summary'
  AND md5(count_sql) = 'a6ff09db0588b92339d631f422d69cc7';

DO $post$
DECLARE v_md5 text;
BEGIN
  SELECT max(md5(count_sql)) INTO v_md5 FROM asset_registry WHERE asset_id = 'bo_cdlm_summary';
  IF v_md5 = 'a6ff09db0588b92339d631f422d69cc7' THEN
    RAISE EXCEPTION '1297: bo_cdlm_summary count_sql update did not take (still the old text)';
  END IF;
END
$post$;
