-- Migration 1394: the 1379 statement locks serve the charts a statement touches (KĀLA-YANTRA J-2a / SR-J2A-N18).
-- Created: 2026-10-17. NEEDS-PROTECTED-WINDOW: creates functions/triggers in public.
-- Allocated in run/MIGRATION_ALLOCATION.json (1394 -> J-2a N18). Replaces, never edits, 1379.
-- No row of any table is read for content, changed, or deleted. migrate.ts owns the transaction (no nested BEGIN/COMMIT).
--
-- DEFECT. 1379 put ka_gochara_chart_statement_lock() (1153) on kala_gochara_publication and kala_gochara_authority as a BEFORE
-- STATEMENT trigger. That function walks EVERY chart present in the table and takes each chart's family key through
-- ka_gochara_lock_chart(). Production holds a non-canonical chart in both tables (publication 1c826d5a-…/4.0/candidate; one
-- authority row), so ANY UPDATE/DELETE statement on them -- even a zero-row DELETE -- raised P0001: bound to the canonical
-- chart, the walk reached the other chart (N18, 1153 :441-444); unbound, D-SCOPE (:446-449). The J-2a teardown's zero-row
-- DELETE on kala_gochara_publication hit exactly that.
--
-- FIX (SR-J2A-N18, B). Lock exactly the DISTINCT charts the statement touches, in ascending order, through the same
-- ka_gochara_lock_chart(), so N18 (one chart per transaction) and D-SCOPE (canonical only) still refuse every chart
-- actually touched. PostgreSQL allows REFERENCING transition tables only on AFTER triggers, and only one event per trigger.
-- The N13 order (the family key precedes the first tuple lock, 1153 :525-529) cannot be given up -- an UPDATE locks its tuples
-- before an AFTER trigger could run. So each table gets, per the 0_ ordering:
--   (a) BEFORE STATEMENT  <table>_0_…statement_lock (same name, ENABLE ALWAYS as 1379): takes the family key of the one governed
--       chart (D-SCOPE: the canonical chart) iff that chart has rows in the table -- exactly what 1153 did for it. A foreign
--       chart is NOT walked here: it was the only thing that made a statement on an unrelated chart fail.
--   (b) AFTER STATEMENT, one trigger for UPDATE and one for DELETE, with transition tables: runs ka_gochara_lock_chart() for every
--       DISTINCT chart_id in the OLD (and, for UPDATE, NEW) table, ascending. A statement touching a non-canonical chart raises
--       D-SCOPE, one touching two charts raises N18 (or D-SCOPE), and the statement rolls back; a zero-row statement touches nothing.
-- INSERT is not covered by either (as in 1379); the row guards own it. Other 1153-family tables keep ka_gochara_chart_statement_lock().
-- (I) INTERPRETATION: the ruling's "transition tables" are the AFTER half; the BEFORE half is kept (not a weakening: it is the
-- same governed-chart lock 1153 took) because dropping it would let an UPDATE lock tuples before the key (the N13 deadlock order).

DO $$
BEGIN
  IF to_regprocedure('public.ka_gochara_lock_chart(uuid)') IS NULL
     OR to_regprocedure('public.ka_gochara_chart_statement_lock()') IS NULL
     OR to_regclass('public.kala_gochara_publication') IS NULL
     OR to_regclass('public.kala_gochara_authority') IS NULL
     OR (SELECT count(*) FROM pg_trigger WHERE tgname IN (
           'kala_gochara_authority_0_statement_lock', 'kala_gochara_authority_1_sealed_guard',
           'kala_gochara_publication_0_authority_statement_lock', 'kala_gochara_publication_1_authority_guard')
         AND NOT tgisinternal AND tgenabled = 'A') <> 4 THEN
    RAISE EXCEPTION '1394 preflight: migration 1379 (four ALWAYS triggers) and the 1153 locking schema required';
  END IF;
END;
$$;

-- (a) BEFORE STATEMENT: the governed chart's family key, ahead of any tuple lock (N13).
CREATE OR REPLACE FUNCTION public.ka_gochara_governed_chart_statement_lock()
RETURNS trigger LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
DECLARE
  -- D-SCOPE: the only chart ka_gochara_lock_chart() issues a family key for (1153 :446-449).
  governed constant uuid := '482012f1-710e-4a25-994a-93821f5871aa';
  present boolean;
BEGIN
  EXECUTE format('SELECT EXISTS (SELECT 1 FROM public.%I WHERE chart_id = $1)', TG_TABLE_NAME)
    INTO present USING governed;
  IF present THEN
    PERFORM public.ka_gochara_lock_chart(governed);
  END IF;
  RETURN NULL;
END;
$$;
REVOKE ALL ON FUNCTION public.ka_gochara_governed_chart_statement_lock() FROM PUBLIC;

-- (b) AFTER STATEMENT: every distinct chart in the statement's transition tables, ascending.
CREATE OR REPLACE FUNCTION public.ka_gochara_touched_chart_statement_lock()
RETURNS trigger LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
DECLARE c uuid;
BEGIN
  IF TG_OP = 'DELETE' THEN
    FOR c IN SELECT DISTINCT chart_id FROM ka_old_rows WHERE chart_id IS NOT NULL ORDER BY chart_id LOOP
      PERFORM public.ka_gochara_lock_chart(c);
    END LOOP;
  ELSIF TG_OP = 'UPDATE' THEN
    FOR c IN SELECT chart_id FROM (SELECT chart_id FROM ka_old_rows UNION SELECT chart_id FROM ka_new_rows) t
             WHERE chart_id IS NOT NULL ORDER BY chart_id LOOP
      PERFORM public.ka_gochara_lock_chart(c);
    END LOOP;
  ELSE
    RAISE EXCEPTION 'ka_gochara_touched_chart_statement_lock: % is not covered (UPDATE and DELETE only)', TG_OP;
  END IF;
  RETURN NULL;
END;
$$;
REVOKE ALL ON FUNCTION public.ka_gochara_touched_chart_statement_lock() FROM PUBLIC;

-- kala_gochara_publication
DROP TRIGGER IF EXISTS kala_gochara_publication_0_authority_statement_lock ON public.kala_gochara_publication;
CREATE TRIGGER kala_gochara_publication_0_authority_statement_lock
  BEFORE UPDATE OR DELETE ON public.kala_gochara_publication
  FOR EACH STATEMENT EXECUTE FUNCTION public.ka_gochara_governed_chart_statement_lock();
DROP TRIGGER IF EXISTS kala_gochara_publication_9_touched_charts_update_lock ON public.kala_gochara_publication;
CREATE TRIGGER kala_gochara_publication_9_touched_charts_update_lock
  AFTER UPDATE ON public.kala_gochara_publication
  REFERENCING OLD TABLE AS ka_old_rows NEW TABLE AS ka_new_rows
  FOR EACH STATEMENT EXECUTE FUNCTION public.ka_gochara_touched_chart_statement_lock();
DROP TRIGGER IF EXISTS kala_gochara_publication_9_touched_charts_delete_lock ON public.kala_gochara_publication;
CREATE TRIGGER kala_gochara_publication_9_touched_charts_delete_lock
  AFTER DELETE ON public.kala_gochara_publication
  REFERENCING OLD TABLE AS ka_old_rows
  FOR EACH STATEMENT EXECUTE FUNCTION public.ka_gochara_touched_chart_statement_lock();
ALTER TABLE public.kala_gochara_publication ENABLE ALWAYS TRIGGER kala_gochara_publication_0_authority_statement_lock;
ALTER TABLE public.kala_gochara_publication ENABLE ALWAYS TRIGGER kala_gochara_publication_9_touched_charts_update_lock;
ALTER TABLE public.kala_gochara_publication ENABLE ALWAYS TRIGGER kala_gochara_publication_9_touched_charts_delete_lock;

-- kala_gochara_authority
DROP TRIGGER IF EXISTS kala_gochara_authority_0_statement_lock ON public.kala_gochara_authority;
CREATE TRIGGER kala_gochara_authority_0_statement_lock
  BEFORE UPDATE OR DELETE ON public.kala_gochara_authority
  FOR EACH STATEMENT EXECUTE FUNCTION public.ka_gochara_governed_chart_statement_lock();
DROP TRIGGER IF EXISTS kala_gochara_authority_9_touched_charts_update_lock ON public.kala_gochara_authority;
CREATE TRIGGER kala_gochara_authority_9_touched_charts_update_lock
  AFTER UPDATE ON public.kala_gochara_authority
  REFERENCING OLD TABLE AS ka_old_rows NEW TABLE AS ka_new_rows
  FOR EACH STATEMENT EXECUTE FUNCTION public.ka_gochara_touched_chart_statement_lock();
DROP TRIGGER IF EXISTS kala_gochara_authority_9_touched_charts_delete_lock ON public.kala_gochara_authority;
CREATE TRIGGER kala_gochara_authority_9_touched_charts_delete_lock
  AFTER DELETE ON public.kala_gochara_authority
  REFERENCING OLD TABLE AS ka_old_rows
  FOR EACH STATEMENT EXECUTE FUNCTION public.ka_gochara_touched_chart_statement_lock();
ALTER TABLE public.kala_gochara_authority ENABLE ALWAYS TRIGGER kala_gochara_authority_0_statement_lock;
ALTER TABLE public.kala_gochara_authority ENABLE ALWAYS TRIGGER kala_gochara_authority_9_touched_charts_update_lock;
ALTER TABLE public.kala_gochara_authority ENABLE ALWAYS TRIGGER kala_gochara_authority_9_touched_charts_delete_lock;

DO $$
BEGIN
  -- the two 0_ BEFORE STATEMENT (tgtype 26 = STATEMENT|BEFORE|DELETE|UPDATE) triggers now run the governed-chart lock ...
  IF (SELECT count(*) FROM pg_trigger WHERE NOT tgisinternal AND tgenabled = 'A' AND tgtype = 26
        AND tgfoid = 'public.ka_gochara_governed_chart_statement_lock()'::regprocedure
        AND tgname IN ('kala_gochara_authority_0_statement_lock', 'kala_gochara_publication_0_authority_statement_lock')) <> 2
     -- ... the four AFTER STATEMENT transition-table triggers (tgtype 8 = STATEMENT|AFTER|DELETE, 16 = STATEMENT|AFTER|UPDATE) exist ...
     OR (SELECT count(*) FROM pg_trigger WHERE NOT tgisinternal AND tgenabled = 'A'
           AND tgfoid = 'public.ka_gochara_touched_chart_statement_lock()'::regprocedure
           AND ((tgtype = 8 AND tgoldtable IS NOT NULL AND tgnewtable IS NULL)
             OR (tgtype = 16 AND tgoldtable IS NOT NULL AND tgnewtable IS NOT NULL))
           AND tgname IN ('kala_gochara_authority_9_touched_charts_update_lock', 'kala_gochara_authority_9_touched_charts_delete_lock',
                          'kala_gochara_publication_9_touched_charts_update_lock', 'kala_gochara_publication_9_touched_charts_delete_lock')) <> 4
     -- ... and 1379's two ROW guards are untouched and still ALWAYS.
     OR (SELECT count(*) FROM pg_trigger WHERE NOT tgisinternal AND tgenabled = 'A'
           AND tgname IN ('kala_gochara_authority_1_sealed_guard', 'kala_gochara_publication_1_authority_guard')) <> 2 THEN
    RAISE EXCEPTION '1394 postflight: two ALWAYS governed-chart BEFORE locks, four ALWAYS transition-table AFTER locks and the two 1379 row guards required';
  END IF;
END;
$$;
