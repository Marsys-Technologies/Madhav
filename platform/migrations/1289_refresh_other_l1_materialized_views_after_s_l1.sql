-- 1289_refresh_other_l1_materialized_views_after_s_l1.sql
--
-- Suvarna (S-L1 post-window; L1_MV_REFRESH_AFTER_REBUILD_v1_0.md section 3 and its "whether 1256 also covers the other views is
-- SS's call" paragraph): refresh the OTHER materialized views that are derived from the L1 tables, as their owner. Sibling of
-- migration 1256, which did the same for mv_chart_sade_sati_lifetime_summary and is NOT repeated here.
--
-- WHY. The S-L1 job runs as data_plane_builder, which owns none of these views (every one is owned by amjis_app), and no L1
-- writer on the orchestrator path refreshes any of them (only ga_sade_sati ever tried, and that one is 1256's). They were last
-- refreshed before the S-L1 rebuild, so each still reflects the pre-rebuild builds. Measured read-only as suvarna_reader on
-- 2026-10-05: the definition of each view, run as a plain SELECT, returns about three times the rows the stored view holds
-- (for example mv_chart_ashtakavarga_summary 1560 vs 520, mv_chart_sensitive_points_summary 4500 vs 1515, mv_chart_aspect_matrix
-- 2296 vs 0, mv_chart_t1_composite_strengths 135 vs 0). This migration runs through the routine migrate job as amjis_app, the
-- owner, and recomputes them from the rebuilt chart_facts / chart_divisionals. amjis_app holds SELECT on both tables (verified).
--
-- WHAT. One refresh per view, in dependency order (a view that reads another view is refreshed after it:
-- mv_chart_sensitive_points_summary before mv_sensitive_points_cross_ayanamsha). The thirteen views:
--   from chart_facts:        mv_chart_planet_summary, mv_chart_shadbala_summary, mv_chart_ashtakavarga_summary,
--                            mv_chart_bhava_bala_summary, mv_cross_ayanamsha_consensus, mv_chart_panchanga_birth_summary,
--                            mv_chart_sensitive_points_summary, mv_chart_aspect_matrix, mv_chart_t1_composite_strengths,
--                            mv_chart_yogas_fired_summary
--   from chart_divisionals:  mv_chart_vargas_summary, mv_chart_super_vargottama_bodies
--   from another view:       mv_sensitive_points_cross_ayanamsha (reads mv_chart_sensitive_points_summary)
-- For each view: absent in this database (a fresh or disposable database that never created it) -> NOTICE, nothing else;
-- present, populated AND carrying a valid, non-partial, non-expression UNIQUE index -> REFRESH ... CONCURRENTLY (never blocks
-- SELECT on the view); present otherwise (never populated, or no usable unique index: mv_cross_ayanamsha_consensus,
-- mv_sensitive_points_cross_ayanamsha, mv_chart_aspect_matrix) -> plain REFRESH (CONCURRENTLY is illegal there; the plain form
-- takes ACCESS EXCLUSIVE for the duration, and no served reader reads any of these views: the retrieval layer reads chart_facts
-- directly). Idempotent: a second run recomputes the same views from the same rows. A refresh changes no table data and no
-- chart_facts / chart_divisionals value.
--
-- NOT. The sade-sati view (1256), the bodha_* / tool_* / session views (not L1), no grant, no DDL, no table write, no
-- chart-scoped statement, no other session setting.
--
-- LOCKS. SET LOCAL lock_timeout = '10s' bounds the wait for each view's lock; the migrate runner applies each file in one
-- transaction, so on a timeout or any error the whole file rolls back and every view simply stays as it was (safe to re-run).

SET LOCAL lock_timeout = '10s';

DO $mv$
DECLARE
  v_view       text;
  v_populated  boolean;
  v_unique_idx boolean;
BEGIN
  FOREACH v_view IN ARRAY ARRAY[
    'mv_chart_planet_summary',
    'mv_chart_shadbala_summary',
    'mv_chart_ashtakavarga_summary',
    'mv_chart_bhava_bala_summary',
    'mv_cross_ayanamsha_consensus',
    'mv_chart_panchanga_birth_summary',
    'mv_chart_sensitive_points_summary',
    'mv_sensitive_points_cross_ayanamsha',
    'mv_chart_vargas_summary',
    'mv_chart_aspect_matrix',
    'mv_chart_super_vargottama_bodies',
    'mv_chart_t1_composite_strengths',
    'mv_chart_yogas_fired_summary'
  ]
  LOOP
    SELECT m.ispopulated,
           EXISTS (SELECT 1
                     FROM pg_catalog.pg_index i
                    WHERE i.indrelid = format('public.%I', m.matviewname)::regclass
                      AND i.indisunique
                      AND i.indisvalid
                      AND i.indpred IS NULL
                      AND i.indexprs IS NULL)
      INTO v_populated, v_unique_idx
      FROM pg_catalog.pg_matviews m
     WHERE m.schemaname = 'public'
       AND m.matviewname = v_view;

    IF NOT FOUND THEN
      RAISE NOTICE '1289: public.% does not exist in this database; nothing to refresh', v_view;
      CONTINUE;
    END IF;

    IF v_populated AND v_unique_idx THEN
      EXECUTE format('REFRESH MATERIALIZED VIEW CONCURRENTLY public.%I', v_view);
    ELSE
      EXECUTE format('REFRESH MATERIALIZED VIEW public.%I', v_view);
    END IF;
  END LOOP;
END
$mv$;
