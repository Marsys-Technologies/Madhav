-- 1347_ph_rectification_integrity_chart_aware.sql
--
-- ONE_AYANAMSHA P2-1 (SS N-309/N-315/N-316): make ph_rectification.integrity_check_sql CHART-AWARE. Chart 482012f1 will hold ONE ayanamsha
-- (lahiri_chitrapaksha); other charts keep all five. The orchestrator runs asset_registry.integrity_check_sql UNSCOPED (no chart
-- parameter: asset_runner.py _probe_asset, cur.execute(integrity_sql)) and a red result is BUILD-FATAL for the asset, so a check that
-- assumes five ayanamshas would error the asset for EVERY chart as soon as one chart holds one. ONE md5-guarded UPDATE of ONE column
-- (integrity_check_sql) of ONE asset_registry row; nothing else. Transaction ownership belongs to platform/scripts/migrate.ts (no
-- BEGIN/COMMIT here). Data-only: no table or function is created or altered (routine path, amjis_app).
--
-- THE DEFECT. The live integrity_check_sql (migration 681) has `GROUP BY 1,2 HAVING count(DISTINCT ayanamsha_id) <> 5` over
-- (chart_id, offset_minutes): every offset must be scored under exactly five ayanamshas. With one ayanamsha every offset has 1 distinct
-- id and the check is red for every chart.
--
-- THE CHANGE. Only that clause. Each (chart_id, offset) group is compared with the chart's own set, scope_ids =
-- COALESCE(charts.build_ayanamshas, <the five>) (LEFT JOIN on charts.id; a chart_id with no charts row keeps the five). The group is red
-- when its distinct ayanamsha count differs from the size of the (de-duplicated) set, OR the set is not contained in the group's ids
-- (so a chart configured for ['lahiri_chitrapaksha'] that holds only true_chitra rows is red, which a bare count would let through). For
-- NULL build_ayanamshas and data that holds only the five ids this is exactly `count(DISTINCT ayanamsha_id) <> 5` (the added containment
-- test can only differ when a group carries an id outside the five). All other conjuncts are byte-for-byte the live text.
--
-- THE SCOPE SOURCE. charts.build_ayanamshas text[] (migration 1344; NULL = the five canonical ids). The scope leads the data: it is read
-- from charts, NEVER derived from chart_facts or from the rows under test. This migration requires 1344 (numeric order guarantees it; the
-- pre-check below RAISES if the column is missing rather than installing a check that errors at run time). The new text also works when
-- build_ayanamshas is NULL for all charts (the state right after 1344 and until the Lahiri-only switch): there it behaves exactly as the
-- old text. The five-id literal that remains in the text is the COALESCE default only (the NULL meaning), not a second source of scope.
--
--   OLD (live, read 2026-10-10 as suvarna_reader; md5 08d0d48159cdd942376277a37d4f69b6, 1692 chars)
--   NEW (md5 fc036a2d3e9e75a6f1a5ce6ebfb4c494, 2498 chars; the dollar-quoted literal in the UPDATE below)
--
-- WHEN THIS APPLIES (SS N-316). Apply in the PHASE 4 window, immediately BEFORE the first Lahiri-only build of chart 482012f1 (1344, the
-- column, may go earlier; this file may not). Because platform/scripts/migrate.ts applies every unapplied migration on the next deploy,
-- MERGING this file IS applying it: the PR is held until that window.
--
-- TRIGGER EFFECT (the load-bearing fact; proved by the live test with the production trigger body). nirmana_registry_receipt_invalidation
-- (migration 596) fires AFTER UPDATE OF depends_on, natural_key_partition, health_probe, integrity_check_sql, target_floor, asset_kind,
-- asset_type, scope, has_writer, is_active, target_table. integrity_check_sql IS one of those columns and the text changes, so this UPDATE
-- STALES the asset_freshness receipt of ph_rectification on EVERY chart (freshness_state 'stale', reason 'registry_changed'). The trigger is NOT
-- touched here (SS N-316 ruling 3). EXPECTED EFFECT, accepted: charts 1c826d5a and cb73cd3d show ph_rectification as stale after the apply. Clearing
-- procedure: a forced run of the four assets (bo_pratijna, ga_vargas, ph_rectification, ga_nakshatra) per such chart in the same window,
-- or fold them into that chart's full rebuild. Chart 482012f1 is rebuilt by the Lahiri-only build anyway.
--
-- GUARD AND WHAT HAPPENS WHEN IT DOES NOT MATCH. The UPDATE is guarded by md5(integrity_check_sql) of the OLD text, so it only ever
-- replaces the exact text it was written against. If the live text is anything else (edited meanwhile, or a fresh database whose registry
-- row carries no check) the UPDATE matches 0 rows and the migration is a NO-OP that emits a NOTICE naming the md5 found and does NOT fail
-- the deploy. Consequence: the five-ayanamsha check stays installed and the Lahiri-only build would go red on it, so VERIFY AFTER THE
-- APPLY (below), never trust the deploy log (Trap 103). If the live text already equals the NEW text the migration is an idempotent
-- no-op (NOTICE, nothing rewritten, so the trigger does not fire a second time). The cases that RAISE: charts.build_ayanamshas is
-- missing, or the post-check finds the row still carrying the OLD md5 (the UPDATE silently did nothing; CLAUDE.md N.4).
--
-- NOT CHANGED HERE: any other asset_registry column, the writer, any data row, the trigger (migration 596), the other three checks (own file).
--
-- VERIFICATION BY PRODUCTION STRUCTURE (after the apply, as suvarna_reader; expect md5 fc036a2d3e9e75a6f1a5ce6ebfb4c494 and length 2498):
--   SELECT asset_id, md5(integrity_check_sql), length(integrity_check_sql) FROM asset_registry WHERE asset_id = 'ph_rectification';
-- and run the integrity text read-only against the database: it must return true while every chart still has NULL build_ayanamshas and
-- the data holds five ayanamshas (same answer as the OLD text).
--
-- ROLLBACK (not executed by migrate.ts; also fires the staling trigger): UPDATE asset_registry SET integrity_check_sql = <the OLD live
-- text, recoverable from git history of the migration that last set it plus this header's md5> WHERE asset_id = 'ph_rectification' AND
-- md5(integrity_check_sql) = 'fc036a2d3e9e75a6f1a5ce6ebfb4c494';

SET LOCAL lock_timeout = '5s';

DO $pre$
DECLARE v_n int; v_md5 text;
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                  WHERE table_schema = 'public' AND table_name = 'charts' AND column_name = 'build_ayanamshas') THEN
    RAISE EXCEPTION '1347: charts.build_ayanamshas is missing (migration 1344 must apply first)';
  END IF;
  SELECT count(*), max(md5(integrity_check_sql)) INTO v_n, v_md5 FROM asset_registry WHERE asset_id = 'ph_rectification';
  IF v_n = 0 THEN
    RAISE NOTICE '1347: no ph_rectification registry row (empty registry); nothing to do';
  ELSIF v_md5 = 'fc036a2d3e9e75a6f1a5ce6ebfb4c494' THEN
    RAISE NOTICE '1347: ph_rectification integrity_check_sql is already chart-aware; nothing to do';
  ELSIF v_md5 IS DISTINCT FROM '08d0d48159cdd942376277a37d4f69b6' THEN
    RAISE NOTICE '1347: ph_rectification integrity_check_sql is not the text this migration was written against (md5 %); NO-OP, integrity_check_sql left as is', v_md5;
  END IF;
END
$pre$;

UPDATE asset_registry
SET integrity_check_sql = $chk$
-- D-CND-03: every clause partitions on chart_id already -- the scan lattice is a per-chart
-- structure, so a defect in one chart's lattice cannot be masked by another's.
SELECT
  -- Contiguous, gap-free offset lattice at the declared step.
  NOT EXISTS (SELECT 1 FROM (
     SELECT chart_id, offset_minutes,
            lead(offset_minutes) OVER (PARTITION BY chart_id ORDER BY offset_minutes) nx
     FROM (SELECT DISTINCT chart_id, offset_minutes FROM phala_rectification) o) g
    WHERE nx IS NOT NULL AND nx - offset_minutes <> 5
    GROUP BY chart_id HAVING count(*) > 0)
  -- Symmetric and centred on the recorded birth time.
  AND NOT EXISTS (SELECT 1 FROM phala_rectification
     GROUP BY chart_id HAVING min(offset_minutes) <> -max(offset_minutes) OR NOT bool_or(offset_minutes = 0))
  -- Complete cross-product: every offset scored under every ayanamsha BUILT FOR THAT CHART
  -- (migration 1347: charts.build_ayanamshas, NULL = the five; a chart absent from charts falls back
  -- to the five). Red when the offset's distinct ayanamsha count differs from the chart's set size OR
  -- when any configured ayanamsha is missing from the offset (so a wrong single id cannot pass by count).
  AND NOT EXISTS (SELECT 1 FROM (SELECT chart_id, offset_minutes
        FROM (SELECT r.chart_id, r.offset_minutes, r.ayanamsha_id,
                     COALESCE(ch.build_ayanamshas, ARRAY['lahiri_chitrapaksha','true_chitra','krishnamurti','raman','surya_siddhanta_classical']::text[]) AS scope_ids
              FROM phala_rectification r
              LEFT JOIN charts ch ON ch.id = r.chart_id) q
        GROUP BY chart_id, offset_minutes, scope_ids
        HAVING count(DISTINCT ayanamsha_id) <> (SELECT count(DISTINCT s.a) FROM unnest(scope_ids) AS s(a))
            OR NOT (array_agg(DISTINCT ayanamsha_id) @> scope_ids)) x
     GROUP BY chart_id HAVING count(*) > 0)
  -- lagna_stable is an all-or-nothing property of an offset across ayanamshas.
  AND NOT EXISTS (SELECT 1 FROM (SELECT chart_id, offset_minutes FROM phala_rectification
        GROUP BY 1,2 HAVING count(DISTINCT lagna_stable) > 1) x
     GROUP BY chart_id HAVING count(*) > 0)
  -- The best row must resolve to a real candidate of its OWN chart.
  AND NOT EXISTS (SELECT 1 FROM phala_rectification_best b WHERE b.best_candidate_id IS NOT NULL
       AND NOT EXISTS (SELECT 1 FROM phala_rectification c
             WHERE c.id = b.best_candidate_id AND c.chart_id = b.chart_id)
     GROUP BY b.chart_id HAVING count(*) > 0)
$chk$
WHERE asset_id = 'ph_rectification'
  AND md5(integrity_check_sql) = '08d0d48159cdd942376277a37d4f69b6';

DO $post$
DECLARE v_md5 text;
BEGIN
  SELECT max(md5(integrity_check_sql)) INTO v_md5 FROM asset_registry WHERE asset_id = 'ph_rectification';
  IF v_md5 = '08d0d48159cdd942376277a37d4f69b6' THEN
    RAISE EXCEPTION '1347: ph_rectification integrity_check_sql update did not take (still the old text)';
  END IF;
END
$post$;
