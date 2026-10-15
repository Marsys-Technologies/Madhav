-- 1340_bo_cgm_motifs_count_sql_three_tables.sql
--
-- After-certification fix (SS N-290/N-291; the Engine's exact text, madhav-39 2026-10-09): widen asset_registry.count_sql of
-- bo_cgm_motifs so the cockpit / Build.completion probe counts what the writer actually writes, and so the N-286 curated-corpus
-- lift (which needs the chart-bound three-table form) can apply. ONE md5-guarded UPDATE of ONE column (count_sql) of ONE
-- asset_registry row; nothing else. Transaction ownership belongs to platform/scripts/migrate.ts (no BEGIN/COMMIT here). Data-only:
-- no table or function is created or altered, so it runs as amjis_app on the routine path (no CREATE on schema public needed).
-- Same shape as 1297 (bo_cdlm_summary).
--
-- THE DEFECT. pipeline/orchestrator/writers/bo_cgm_motifs.py writes THREE tables per chart (bodha_cgm_motifs, bodha_cgm_sub_graphs,
-- bodha_cgm_chart_topology_summary; 600 + 5 + 5 = 610 rows on the canonical chart 482012f1-710e-4a25-994a-93821f5871aa, read
-- 2026-10-09), but the registered count_sql counts only bodha_cgm_motifs.
--
--   OLD (live, read 2026-10-09 as suvarna_reader; md5 610fd9db0ecced863abfe7cd31764a53, 57 chars):
--     SELECT count(*) FROM bodha_cgm_motifs WHERE chart_id = $1
--   NEW (md5 1c2dc6a2c4a26699635eecb0309d5f18, 284 chars; the "AS count" CTE shape of 1297. The chart parameter $1 appears EXACTLY
--   ONCE, in a CTE, on purpose: the orchestrator's data-presence probe asset_runner._data_rows_present does
--   count_sql.replace("$1", "%s") and binds ONE parameter, so a text with $1 repeated per table would raise in psycopg):
--     WITH p AS (SELECT $1::uuid AS cid) SELECT (SELECT count(*) FROM bodha_cgm_motifs m, p WHERE m.chart_id = p.cid) + (SELECT count(*) FROM bodha_cgm_sub_graphs g, p WHERE g.chart_id = p.cid) + (SELECT count(*) FROM bodha_cgm_chart_topology_summary t, p WHERE t.chart_id = p.cid) AS count
--
-- GUARD. The UPDATE is guarded by md5(count_sql) of the OLD text, so it only ever replaces the exact text it was written against.
-- If the live text is anything else the UPDATE matches 0 rows and the migration is a NO-OP with a NOTICE (count_sql is a cockpit /
-- completion probe, not data; failing every deploy for it would be disproportionate). If the live text already equals the NEW text
-- it is an idempotent no-op. The ONE case that RAISES: the post-check finds the row still carries the OLD md5 (the UPDATE silently
-- did nothing; never trust a silent no-op, CLAUDE.md N.4).
--
-- NO TRIGGER EFFECT. nirmana_registry_receipt_invalidation (migration 596) fires only AFTER UPDATE OF depends_on, natural_key_partition,
-- health_probe, integrity_check_sql, target_floor, asset_kind, asset_type, scope, has_writer, is_active, target_table. count_sql is NOT
-- among them, so no asset_freshness row of any asset changes.
--
-- NOT CHANGED HERE: target_table, target_floor, size_sql, volume_explanation (a follow-up), the TypeScript seed (its registry
-- insert keeps an existing live count_sql rather than overwriting it; a fresh database replaying the seed and then the migrations
-- holds the OLD text, matches the guard, and is widened here), any data row, any writer. A row whose count_sql is NULL or any other
-- text is skipped with a NOTICE, not failed (count_sql is a probe, not data).
--
-- VERIFICATION BY PRODUCTION STRUCTURE (never trust a deploy log). After the deploy, as suvarna_reader, expect md5
-- 1c2dc6a2c4a26699635eecb0309d5f18 and length 284:
--   SELECT asset_id, md5(count_sql), length(count_sql) FROM asset_registry WHERE asset_id = 'bo_cgm_motifs';
-- and, executed read-only with the canonical chart in place of $1, 610 while the current rows stand.
--
-- ROLLBACK (not executed by migrate.ts): UPDATE asset_registry SET count_sql = 'SELECT count(*) FROM bodha_cgm_motifs WHERE chart_id = $1'
-- WHERE asset_id = 'bo_cgm_motifs' AND md5(count_sql) = '1c2dc6a2c4a26699635eecb0309d5f18';

SET LOCAL lock_timeout = '5s';

DO $pre$
DECLARE v_n int; v_md5 text;
BEGIN
  SELECT count(*), max(md5(count_sql)) INTO v_n, v_md5 FROM asset_registry WHERE asset_id = 'bo_cgm_motifs';
  IF v_n = 0 THEN
    RAISE NOTICE '1340: no bo_cgm_motifs registry row (empty registry); nothing to do';
  ELSIF v_md5 = '1c2dc6a2c4a26699635eecb0309d5f18' THEN
    RAISE NOTICE '1340: bo_cgm_motifs count_sql already counts the three tables; nothing to do';
  ELSIF v_md5 IS DISTINCT FROM '610fd9db0ecced863abfe7cd31764a53' THEN
    RAISE NOTICE '1340: bo_cgm_motifs count_sql is not the text this migration was written against (md5 %); NO-OP, count_sql left as is', v_md5;
  END IF;
END
$pre$;

UPDATE asset_registry
SET count_sql = $cs$WITH p AS (SELECT $1::uuid AS cid) SELECT (SELECT count(*) FROM bodha_cgm_motifs m, p WHERE m.chart_id = p.cid) + (SELECT count(*) FROM bodha_cgm_sub_graphs g, p WHERE g.chart_id = p.cid) + (SELECT count(*) FROM bodha_cgm_chart_topology_summary t, p WHERE t.chart_id = p.cid) AS count$cs$
WHERE asset_id = 'bo_cgm_motifs'
  AND md5(count_sql) = '610fd9db0ecced863abfe7cd31764a53';

DO $post$
DECLARE v_md5 text;
BEGIN
  SELECT max(md5(count_sql)) INTO v_md5 FROM asset_registry WHERE asset_id = 'bo_cgm_motifs';
  IF v_md5 = '610fd9db0ecced863abfe7cd31764a53' THEN
    RAISE EXCEPTION '1340: bo_cgm_motifs count_sql update did not take (still the old text)';
  END IF;
END
$post$;
