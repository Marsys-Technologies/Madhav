-- Migration 1375: K6-123 bind integrity to the chart and exact build under verification.
-- Created: 2026-10-14
-- Additive registry correction; applied migrations 1353-1356 stay unchanged.
-- (I) INTERPRETATION: the parameterless orchestrator probe consumes transaction-local
-- kala.integrity_chart_id / kala.integrity_build_id set by the three K6 writers.
-- A standalone/completed-build probe must bind both pins in its own transaction.
-- Missing pins or a mismatched chart/build return false; completion state is irrelevant.
-- Preserve the complete existing candidate predicate and legacy ELSE detector verbatim.
-- count_sql already pins chart_id and orders by created_at,id (1356); it stays unchanged.
-- Atomic DO block: migrate.ts owns the transaction. Repeat application is a no-op.
-- Serving effect: registry integrity changes invalidate the affected freshness receipts
-- through the existing registry trigger; no candidate/published/legacy data is modified.
DO $migration$
DECLARE
  -- Keep each quoted target query complete for the governance SQL parser.
  -- Replace its final SELECT to recover the exact stored-detector prefix.
  old_target constant text := replace($old$WITH k6_target AS (
    SELECT b.chart_id,c.generation,c.conventions FROM public.build_runs b
    LEFT JOIN public.kala_layer_candidate c ON c.chart_id=b.chart_id AND c.build_id=b.id
    ORDER BY b.created_at DESC,b.id DESC LIMIT 1
  ) SELECT true FROM k6_target$old$, 'SELECT true FROM k6_target', 'SELECT CASE WHEN EXISTS');
  new_target constant text := replace($new$WITH k6_target AS (
    SELECT b.chart_id,c.generation,c.conventions FROM public.build_runs b
    LEFT JOIN public.kala_layer_candidate c ON c.chart_id=b.chart_id AND c.build_id=b.id
    WHERE b.chart_id = NULLIF(current_setting('kala.integrity_chart_id',true),'')::uuid
      AND b.id = NULLIF(current_setting('kala.integrity_build_id',true),'')::uuid
    ORDER BY b.created_at DESC,b.id DESC LIMIT 1
  ) SELECT true FROM k6_target$new$, 'SELECT true FROM k6_target',
    'SELECT CASE WHEN EXISTS (SELECT 1 FROM k6_target) THEN CASE WHEN EXISTS');
  asset text;
  stored_sql text;
BEGIN
  FOREACH asset IN ARRAY ARRAY['ka_kalasutra','ka_kala_darshana','ka_jivana_parva'] LOOP
    SELECT integrity_check_sql INTO stored_sql FROM public.asset_registry
      WHERE asset_id = asset FOR UPDATE;
    IF NOT FOUND THEN
      RAISE EXCEPTION '1375: missing K6 asset registration %', asset;
    END IF;
    IF starts_with(stored_sql, new_target) THEN
      CONTINUE;
    END IF;
    IF NOT COALESCE(starts_with(stored_sql, old_target),false) THEN
      RAISE EXCEPTION '1375: unexpected K6 detector for %; apply 1356 first or review registry drift', asset;
    END IF;
    UPDATE public.asset_registry
      SET integrity_check_sql = new_target || substr(stored_sql,length(old_target)+1) || ' ELSE false END'
      WHERE asset_id = asset;
  END LOOP;
END
$migration$;
