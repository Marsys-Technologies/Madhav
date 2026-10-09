-- 1345_bo_pratijna_integrity_chart_aware.sql
--
-- ONE_AYANAMSHA P2-1 (SS N-309/N-315/N-316): make bo_pratijna.integrity_check_sql CHART-AWARE. Chart 482012f1 will hold ONE ayanamsha
-- (lahiri_chitrapaksha); other charts keep all five. The orchestrator runs asset_registry.integrity_check_sql UNSCOPED (no chart
-- parameter: asset_runner.py _probe_asset, cur.execute(integrity_sql)) and a red result is BUILD-FATAL for the asset, so a check that
-- assumes five ayanamshas would error the asset for EVERY chart as soon as one chart holds one. ONE md5-guarded UPDATE of ONE column
-- (integrity_check_sql) of ONE asset_registry row; nothing else. Transaction ownership belongs to platform/scripts/migrate.ts (no
-- BEGIN/COMMIT here). Data-only: no table or function is created or altered (routine path, amjis_app).
--
-- THE DEFECT. The live integrity_check_sql (last set by migration 665; 727 only touched the volume columns) requires a FIXED grid
-- of 5 ayanamshas x 27 event classes for EVERY chart_id that has any bodha_pratijna row (SELECT DISTINCT chart_id FROM bodha_pratijna,
-- table-wide, no chart parameter). A chart that holds one ayanamsha leaves 27 x 4 cells missing and the check goes red.
--
-- THE CHANGE. The 5-element unnest becomes the chart's own set: COALESCE(charts.build_ayanamshas, <the five>) joined on charts.id
-- (LEFT JOIN: a chart_id with no charts row keeps the five, so today's meaning is unchanged for it). Everything else (the 27 event
-- classes, the duplicate / status-grade / range / status-vocabulary conjuncts) is byte-for-byte the live text. Meaning kept: NULL
-- build_ayanamshas still needs all 5 x 27; ['lahiri_chitrapaksha'] needs exactly its 27 cells; a missing cell of a configured
-- ayanamsha is red; rows of ayanamshas outside the chart's set are NOT flagged (the old check never flagged extras either).
--
-- THE SCOPE SOURCE. charts.build_ayanamshas text[] (migration 1344; NULL = the five canonical ids). The scope leads the data: it is read
-- from charts, NEVER derived from chart_facts or from the rows under test. This migration requires 1344 (numeric order guarantees it; the
-- pre-check below RAISES if the column is missing rather than installing a check that errors at run time). The new text also works when
-- build_ayanamshas is NULL for all charts (the state right after 1344 and until the Lahiri-only switch): there it behaves exactly as the
-- old text. The five-id literal that remains in the text is the COALESCE default only (the NULL meaning), not a second source of scope.
--
--   OLD (live, read 2026-10-10 as suvarna_reader; md5 145bac545d0808c46d6d929f9dc58153, 1586 chars)
--   NEW (md5 55b0f65453ca8a5d9f7fdf56c15cc7ec, 1966 chars; the dollar-quoted literal in the UPDATE below)
--
-- WHEN THIS APPLIES (SS N-316). Apply in the PHASE 4 window, immediately BEFORE the first Lahiri-only build of chart 482012f1 (1344, the
-- column, may go earlier; this file may not). Because platform/scripts/migrate.ts applies every unapplied migration on the next deploy,
-- MERGING this file IS applying it: the PR is held until that window.
--
-- TRIGGER EFFECT (the load-bearing fact; proved by the live test with the production trigger body). nirmana_registry_receipt_invalidation
-- (migration 596) fires AFTER UPDATE OF depends_on, natural_key_partition, health_probe, integrity_check_sql, target_floor, asset_kind,
-- asset_type, scope, has_writer, is_active, target_table. integrity_check_sql IS one of those columns and the text changes, so this UPDATE
-- STALES the asset_freshness receipt of bo_pratijna on EVERY chart (freshness_state 'stale', reason 'registry_changed'). The trigger is NOT
-- touched here (SS N-316 ruling 3). EXPECTED EFFECT, accepted: charts 1c826d5a and cb73cd3d show bo_pratijna as stale after the apply. Clearing
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
-- VERIFICATION BY PRODUCTION STRUCTURE (after the apply, as suvarna_reader; expect md5 55b0f65453ca8a5d9f7fdf56c15cc7ec and length 1966):
--   SELECT asset_id, md5(integrity_check_sql), length(integrity_check_sql) FROM asset_registry WHERE asset_id = 'bo_pratijna';
-- and run the integrity text read-only against the database: it must return true while every chart still has NULL build_ayanamshas and
-- the data holds five ayanamshas (same answer as the OLD text).
--
-- ROLLBACK (not executed by migrate.ts; also fires the staling trigger): UPDATE asset_registry SET integrity_check_sql = <the OLD live
-- text, recoverable from git history of the migration that last set it plus this header's md5> WHERE asset_id = 'bo_pratijna' AND
-- md5(integrity_check_sql) = '55b0f65453ca8a5d9f7fdf56c15cc7ec';

SET LOCAL lock_timeout = '5s';

DO $pre$
DECLARE v_n int; v_md5 text;
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                  WHERE table_schema = 'public' AND table_name = 'charts' AND column_name = 'build_ayanamshas') THEN
    RAISE EXCEPTION '1345: charts.build_ayanamshas is missing (migration 1344 must apply first)';
  END IF;
  SELECT count(*), max(md5(integrity_check_sql)) INTO v_n, v_md5 FROM asset_registry WHERE asset_id = 'bo_pratijna';
  IF v_n = 0 THEN
    RAISE NOTICE '1345: no bo_pratijna registry row (empty registry); nothing to do';
  ELSIF v_md5 = '55b0f65453ca8a5d9f7fdf56c15cc7ec' THEN
    RAISE NOTICE '1345: bo_pratijna integrity_check_sql is already chart-aware; nothing to do';
  ELSIF v_md5 IS DISTINCT FROM '145bac545d0808c46d6d929f9dc58153' THEN
    RAISE NOTICE '1345: bo_pratijna integrity_check_sql is not the text this migration was written against (md5 %); NO-OP, integrity_check_sql left as is', v_md5;
  END IF;
END
$pre$;

UPDATE asset_registry
SET integrity_check_sql = $chk$
SELECT
  (
    NOT EXISTS (
      SELECT 1
      -- (migration 1345) the ayanamsha set is PER CHART: charts.build_ayanamshas, NULL = the five. A chart
      -- present in bodha_pratijna but absent from charts (LEFT JOIN) falls back to the five, as before.
      FROM (SELECT d.chart_id, a.ayanamsha_id
            FROM (SELECT DISTINCT chart_id FROM bodha_pratijna) d
            LEFT JOIN charts ch ON ch.id = d.chart_id
            CROSS JOIN LATERAL unnest(COALESCE(ch.build_ayanamshas, ARRAY[
              'krishnamurti','lahiri_chitrapaksha','raman','surya_siddhanta_classical','true_chitra'
            ]::text[])) AS a(ayanamsha_id)) aya
      CROSS JOIN unnest(ARRAY[
        'achievement_recognition','bereavement','birth_anchor','business_launch',
        'career_advancement','career_change','career_entry','career_setback',
        'childbirth','chronic_onset','education_milestone','exam_outcome',
        'financial_deception','foreign_settlement','illness_acute','major_gain',
        'major_loss','marriage','parental_event','property_acquisition',
        'psychological_arc','relocation','romantic_start','separation',
        'spiritual_turn','surgery','travel_event'
      ]) AS ec(event_class_id)
      LEFT JOIN bodha_pratijna p
        ON p.chart_id = aya.chart_id AND p.ayanamsha_id = aya.ayanamsha_id
       AND p.event_class_id = ec.event_class_id
      WHERE p.pratijna_id IS NULL
    )
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_pratijna
    GROUP BY chart_id, ayanamsha_id, event_class_id
    HAVING count(*) > 1
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_pratijna
    WHERE (status = 'no_evidence' AND grade IS NOT NULL)
       OR (status != 'no_evidence' AND grade IS NULL)
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_pratijna
    WHERE grade IS NOT NULL AND (grade < 0 OR grade > 10)
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_pratijna
    WHERE status NOT IN ('promised', 'denied', 'conditional', 'no_evidence')
  )
$chk$
WHERE asset_id = 'bo_pratijna'
  AND md5(integrity_check_sql) = '145bac545d0808c46d6d929f9dc58153';

DO $post$
DECLARE v_md5 text;
BEGIN
  SELECT max(md5(integrity_check_sql)) INTO v_md5 FROM asset_registry WHERE asset_id = 'bo_pratijna';
  IF v_md5 = '145bac545d0808c46d6d929f9dc58153' THEN
    RAISE EXCEPTION '1345: bo_pratijna integrity_check_sql update did not take (still the old text)';
  END IF;
END
$post$;
