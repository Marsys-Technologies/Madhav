-- 1256_refresh_mv_chart_sade_sati_lifetime_summary_after_s_l1.sql
--
-- Suvarna PW.2 (S-L1 post-window; L1_MV_REFRESH_AFTER_REBUILD_v1_0.md section 3, SS decision of 2026-10-02):
-- refresh public.mv_chart_sade_sati_lifetime_summary after the S-L1 rebuild.
--
-- WHY. The S-L1 job runs as data_plane_builder, which does not own the view (owner amjis_app), so the ga_sade_sati
-- writer SKIPPED its in-writer refresh (the INFO line "MV mv_chart_sade_sati_lifetime_summary NOT refreshed: this
-- connection does not own it (owner=amjis_app) -- left stale", logged by both rehearsals and by the production run
-- 75524b3e-102a-43ec-8cee-3f57fee752c3). The view therefore still holds the builds that existed before S-L1
-- (60 rows, 3 charts, 3 builds, recorded as "knowingly stale" at W3.7 / W7.12). This migration runs through the
-- routine migrate job as amjis_app, the view's owner, and recomputes it from the rebuilt chart_facts.
--
-- WHAT. One REFRESH of ONE view, nothing else. CONCURRENTLY when the view is already populated (the unique index
-- mv_sade_sati_summary_idx exists, so SELECT on the view is never blocked); a plain REFRESH only if the view exists
-- but was never populated (CONCURRENTLY is illegal on an unpopulated view). If the view does not exist (a fresh or
-- disposable database that never created it) the migration is a NOTICE no-op. Idempotent: running it twice
-- recomputes the same view from the same rows. A refresh changes no table data and no chart_facts value.
--
-- NOT. No other view (the other L1 materialized views are not refreshed by the S-L1 path at all and are not in
-- this migration), no grant, no DDL, no table write, no chart-scoped statement.
--
-- LOCKS. SET LOCAL lock_timeout = '10s' bounds the wait for the view's lock; the migrate runner applies each file in
-- one transaction, so on a timeout or any error the file rolls back and the view simply stays stale (safe to re-run).

SET LOCAL lock_timeout = '10s';

DO $mv$
DECLARE
  v_populated boolean;
BEGIN
  SELECT m.ispopulated
    INTO v_populated
    FROM pg_catalog.pg_matviews m
   WHERE m.schemaname = 'public'
     AND m.matviewname = 'mv_chart_sade_sati_lifetime_summary';

  IF NOT FOUND THEN
    RAISE NOTICE '1256: public.mv_chart_sade_sati_lifetime_summary does not exist in this database; nothing to refresh';
    RETURN;
  END IF;

  IF v_populated THEN
    REFRESH MATERIALIZED VIEW CONCURRENTLY public.mv_chart_sade_sati_lifetime_summary;
  ELSE
    REFRESH MATERIALIZED VIEW public.mv_chart_sade_sati_lifetime_summary;
  END IF;
END
$mv$;
