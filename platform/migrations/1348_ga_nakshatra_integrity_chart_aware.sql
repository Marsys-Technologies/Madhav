-- 1348_ga_nakshatra_integrity_chart_aware.sql
--
-- ONE_AYANAMSHA P2-1 (SS N-309/N-315/N-316): make ga_nakshatra.integrity_check_sql CHART-AWARE. Chart 482012f1 will hold ONE ayanamsha
-- (lahiri_chitrapaksha); other charts keep all five. The orchestrator runs asset_registry.integrity_check_sql UNSCOPED (no chart
-- parameter: asset_runner.py _probe_asset, cur.execute(integrity_sql)) and a red result is BUILD-FATAL for the asset, so a check that
-- assumes five ayanamshas would error the asset for EVERY chart as soon as one chart holds one. ONE md5-guarded UPDATE of ONE column
-- (integrity_check_sql) of ONE asset_registry row; nothing else. Transaction ownership belongs to platform/scripts/migrate.ts (no
-- BEGIN/COMMIT here). Data-only: no table or function is created or altered (routine path, amjis_app).
--
-- THE DEFECT. Conjunct (d) (migration 742): every nakshatra_cross_ayanamsha/stable_nakshatra_id row needs its sibling
-- nak_5ay_consistency row to read the literal '5/5'. The writer (ga_nakshatra.py, `{agree}/{total}`) emits '1/1' beside a stable row for a
-- one-ayanamsha chart, so the check is red for any chart that is not on five ayanamshas, table-wide, no chart parameter.
--
-- THE CHANGE. Only conjunct (d): the expected text is n || '/' || n where n = the number of DISTINCT ids in the chart's own set,
-- COALESCE(charts.build_ayanamshas, <the five>) (LEFT JOIN on charts.id; a chart_id with no charts row keeps the five), so a default chart
-- still requires exactly '5/5' and a ['lahiri_chitrapaksha'] chart requires '1/1'. Conjuncts (a), (b), (c) are byte-for-byte the live text.
-- COUPLING TO THE WRITER (not changed here): if the Phase 1 writer stops emitting stable_nakshatra_id for a single-ayanamsha chart the
-- conjunct is vacuously green for it (the honest outcome); if it emits any text other than 'n/n' beside a stable row the check goes red
-- and says so. That decision belongs to the writer batch (B5 finding C-04) and must be re-confirmed before the Lahiri-only build.
--
-- THE SCOPE SOURCE. charts.build_ayanamshas text[] (migration 1344; NULL = the five canonical ids). The scope leads the data: it is read
-- from charts, NEVER derived from chart_facts or from the rows under test. This migration requires 1344 (numeric order guarantees it; the
-- pre-check below RAISES if the column is missing rather than installing a check that errors at run time). The new text also works when
-- build_ayanamshas is NULL for all charts (the state right after 1344 and until the Lahiri-only switch): there it behaves exactly as the
-- old text. The five-id literal that remains in the text is the COALESCE default only (the NULL meaning), not a second source of scope.
--
--   OLD (live, read 2026-10-10 as suvarna_reader; md5 c2612c48b7d192977a1331db0ea2f7e7, 4376 chars)
--   NEW (md5 45561c60ecb90e95450aba776337f47a, 4898 chars; the dollar-quoted literal in the UPDATE below)
--
-- WHEN THIS APPLIES (SS N-316). Apply in the PHASE 4 window, immediately BEFORE the first Lahiri-only build of chart 482012f1 (1344, the
-- column, may go earlier; this file may not). Because platform/scripts/migrate.ts applies every unapplied migration on the next deploy,
-- MERGING this file IS applying it: the PR is held until that window.
--
-- TRIGGER EFFECT (the load-bearing fact; proved by the live test with the production trigger body). nirmana_registry_receipt_invalidation
-- (migration 596) fires AFTER UPDATE OF depends_on, natural_key_partition, health_probe, integrity_check_sql, target_floor, asset_kind,
-- asset_type, scope, has_writer, is_active, target_table. integrity_check_sql IS one of those columns and the text changes, so this UPDATE
-- STALES the asset_freshness receipt of ga_nakshatra on EVERY chart (freshness_state 'stale', reason 'registry_changed'). The trigger is NOT
-- touched here (SS N-316 ruling 3). EXPECTED EFFECT, accepted: charts 1c826d5a and cb73cd3d show ga_nakshatra as stale after the apply. Clearing
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
-- VERIFICATION BY PRODUCTION STRUCTURE (after the apply, as suvarna_reader; expect md5 45561c60ecb90e95450aba776337f47a and length 4898):
--   SELECT asset_id, md5(integrity_check_sql), length(integrity_check_sql) FROM asset_registry WHERE asset_id = 'ga_nakshatra';
-- and run the integrity text read-only against the database: it must return true while every chart still has NULL build_ayanamshas and
-- the data holds five ayanamshas (same answer as the OLD text).
--
-- ROLLBACK (not executed by migrate.ts; also fires the staling trigger): UPDATE asset_registry SET integrity_check_sql = <the OLD live
-- text, recoverable from git history of the migration that last set it plus this header's md5> WHERE asset_id = 'ga_nakshatra' AND
-- md5(integrity_check_sql) = '45561c60ecb90e95450aba776337f47a';

SET LOCAL lock_timeout = '5s';

DO $pre$
DECLARE v_n int; v_md5 text;
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                  WHERE table_schema = 'public' AND table_name = 'charts' AND column_name = 'build_ayanamshas') THEN
    RAISE EXCEPTION '1348: charts.build_ayanamshas is missing (migration 1344 must apply first)';
  END IF;
  SELECT count(*), max(md5(integrity_check_sql)) INTO v_n, v_md5 FROM asset_registry WHERE asset_id = 'ga_nakshatra';
  IF v_n = 0 THEN
    RAISE NOTICE '1348: no ga_nakshatra registry row (empty registry); nothing to do';
  ELSIF v_md5 = '45561c60ecb90e95450aba776337f47a' THEN
    RAISE NOTICE '1348: ga_nakshatra integrity_check_sql is already chart-aware; nothing to do';
  ELSIF v_md5 IS DISTINCT FROM 'c2612c48b7d192977a1331db0ea2f7e7' THEN
    RAISE NOTICE '1348: ga_nakshatra integrity_check_sql is not the text this migration was written against (md5 %); NO-OP, integrity_check_sql left as is', v_md5;
  END IF;
END
$pre$;

UPDATE asset_registry
SET integrity_check_sql = $chk$
-- ga_nakshatra integrity contract (target table: chart_facts, scoped to 16 fact_categories)
-- D-CND-03: chart-partitioned / row-wise, attribution-preserving. No bare count pin (C12).
-- chart_facts_unique_null_formula (chart_id, ayanamsha_id, fact_category, fact_subject, fact_key,
-- build_id) already exactly matches the natural key -- no distinctness conjunct (D-CND-03 rule 4).
SELECT
  -- (a) FORENSIC gate re-asserted at the data layer for the writer's own build-time check
  -- (_forensic_gate, ga_nakshatra.py:283-295, all five ayanamshas -- no ayanamsha scope, same as
  -- the writer's own guard): Moon must be in Purva Bhadrapada (nakshatra_id=25) for the canonical
  -- chart.
  NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
      AND fact_category = 'graha_nakshatra_join' AND fact_subject = 'MOON'
      AND fact_key = 'nakshatra_id_ref' AND fact_value_num <> 25
  )
  -- (b) verification_pass_status honesty (§N.7 item 4 / §N.8): a two_pass_verified or
  -- divergent_flagged status may appear ONLY on the four (fact_category, fact_key) pairs a real
  -- detector runs for -- _nakshatra_pada_verdicts's second-pass re-derivation
  -- (graha_nakshatra_join.nakshatra_id_ref, graha_pada_join.pada_number_ref) and the KP
  -- significator emitter's own two_pass_verdict cross-check against bg_kp_sublord_division
  -- (kp_planet_significations.star_lord, kp_planet_significations.sub_lord). Every other row in
  -- this asset's 16 fact_categories keeps the honest UNVERIFIED_DEFAULT ('single') -- a verified
  -- claim anywhere else would be an unearned status with no detector behind it.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category IN ('graha_nakshatra_join', 'graha_pada_join', 'nakshatra_lord_placement',
                             'graha_kp_lords', 'cusp_kp_lords', 'graha_gandanta',
                             'graha_degree_flags', 'nakshatra_dispositor', 'nakshatra_exchange',
                             'nakshatra_conjunction', 'nakshatra_cogravity', 'graha_tara_bala',
                             'nakshatra_statistics', 'nakshatra_cross_ayanamsha',
                             'kp_house_significators', 'kp_planet_significations')
      AND verification_pass_status IN ('two_pass_verified', 'divergent_flagged')
      AND NOT (
        (fact_category = 'graha_nakshatra_join' AND fact_key = 'nakshatra_id_ref')
        OR (fact_category = 'graha_pada_join' AND fact_key = 'pada_number_ref')
        OR (fact_category = 'kp_planet_significations' AND fact_key = 'star_lord')
        OR (fact_category = 'kp_planet_significations' AND fact_key = 'sub_lord')
      )
  )
  -- (c) nakshatra_id_ref must equal the independent 27-fold division of the SAME
  -- (chart, ayanamsha, subject)'s own longitude_sidereal fact (ga_positions authority, §N.5) --
  -- re-derived here directly (floor(lon / (360/27)) + 1) rather than restated. A row whose
  -- longitude partner is missing entirely also fails this NOT EXISTS.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts n
    WHERE n.fact_category = 'graha_nakshatra_join' AND n.fact_key = 'nakshatra_id_ref'
      AND NOT EXISTS (
        SELECT 1 FROM chart_facts p
        WHERE p.chart_id = n.chart_id AND p.ayanamsha_id = n.ayanamsha_id
          AND p.fact_subject = n.fact_subject
          AND p.fact_category = 'graha_position' AND p.fact_key = 'longitude_sidereal'
          AND n.fact_value_num::int = (floor(p.fact_value_num / (360.0/27.0))::int + 1)
      )
  )
  -- (d) cross-ayanamsha sentinel internal consistency: a stable_nakshatra_id row (emitted only
  -- when all 5 ayanamshas agree, ga_nakshatra.py:468-478) implies its sibling
  -- nak_5ay_consistency row for the same subject must read the unanimous "n/n" -- the two rows
  -- are written from the same len(unique)==1 branch and must never disagree about whether
  -- agreement was unanimous. (migration 1348) n is the size of the chart's OWN ayanamsha set
  -- (charts.build_ayanamshas, NULL = the five, so a default chart still requires exactly "5/5"; a chart
  -- absent from charts falls back to the five).
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts s
    LEFT JOIN charts ch ON ch.id = s.chart_id
    CROSS JOIN LATERAL (SELECT count(DISTINCT u.a)::text AS n
                        FROM unnest(COALESCE(ch.build_ayanamshas, ARRAY['lahiri_chitrapaksha','true_chitra','krishnamurti','raman','surya_siddhanta_classical']::text[])) AS u(a)) sc
    WHERE s.fact_category = 'nakshatra_cross_ayanamsha' AND s.fact_key = 'stable_nakshatra_id'
      AND NOT EXISTS (
        SELECT 1 FROM chart_facts c
        WHERE c.chart_id = s.chart_id AND c.fact_subject = s.fact_subject
          AND c.fact_category = 'nakshatra_cross_ayanamsha' AND c.fact_key = 'nak_5ay_consistency'
          AND c.fact_value_text = sc.n || '/' || sc.n
      )
  )
  AS integrity_passed
$chk$
WHERE asset_id = 'ga_nakshatra'
  AND md5(integrity_check_sql) = 'c2612c48b7d192977a1331db0ea2f7e7';

DO $post$
DECLARE v_md5 text;
BEGIN
  SELECT max(md5(integrity_check_sql)) INTO v_md5 FROM asset_registry WHERE asset_id = 'ga_nakshatra';
  IF v_md5 = 'c2612c48b7d192977a1331db0ea2f7e7' THEN
    RAISE EXCEPTION '1348: ga_nakshatra integrity_check_sql update did not take (still the old text)';
  END IF;
END
$post$;
