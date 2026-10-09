-- 1346_ga_vargas_integrity_chart_aware.sql
--
-- ONE_AYANAMSHA P2-1 (SS N-309/N-315/N-316): make ga_vargas.integrity_check_sql CHART-AWARE. Chart 482012f1 will hold ONE ayanamsha
-- (lahiri_chitrapaksha); other charts keep all five. The orchestrator runs asset_registry.integrity_check_sql UNSCOPED (no chart
-- parameter: asset_runner.py _probe_asset, cur.execute(integrity_sql)) and a red result is BUILD-FATAL for the asset, so a check that
-- assumes five ayanamshas would error the asset for EVERY chart as soon as one chart holds one. ONE md5-guarded UPDATE of ONE column
-- (integrity_check_sql) of ONE asset_registry row; nothing else. Transaction ownership belongs to platform/scripts/migrate.ts (no
-- BEGIN/COMMIT here). Data-only: no table or function is created or altered (routine path, amjis_app).
--
-- THE DEFECT. Conjunct (e) (migration 1222, the non-vacuity detector) pins the canonical chart by literal and requires, for each of
-- 5 ayanamshas x 30 vargas, at least nine graha varga_position/sign rows. With one ayanamsha 4 x 30 cells are empty and EVERY ga_vargas
-- build (the check has no chart parameter) goes red.
--
-- THE CHANGE. Only conjunct (e): the 5-element unnest becomes the canonical chart's own set, COALESCE(charts.build_ayanamshas, <the five>)
-- read from the charts row whose id is the same literal (LEFT JOIN from a one-row VALUES-like subselect, so a MISSING charts row falls
-- back to the five and an empty table stays red, never vacuously green). The scope of the check stays the canonical chart (the disclosed
-- 882/884/902/1019/1022/1215 tradeoff; widening it to every chart would change what the check measures and could redden other charts, so
-- it is NOT done here). Conjuncts (a)-(d), the 30 varga ids and the >= 9 threshold are byte-for-byte the live text. Meaning kept:
-- NULL -> 5 x 30 x 9 as today; ['lahiri_chitrapaksha'] -> 1 x 30 x 9; a missing cell of a configured ayanamsha is red.
--
-- THE SCOPE SOURCE. charts.build_ayanamshas text[] (migration 1344; NULL = the five canonical ids). The scope leads the data: it is read
-- from charts, NEVER derived from chart_facts or from the rows under test. This migration requires 1344 (numeric order guarantees it; the
-- pre-check below RAISES if the column is missing rather than installing a check that errors at run time). The new text also works when
-- build_ayanamshas is NULL for all charts (the state right after 1344 and until the Lahiri-only switch): there it behaves exactly as the
-- old text. The five-id literal that remains in the text is the COALESCE default only (the NULL meaning), not a second source of scope.
--
--   OLD (live, read 2026-10-10 as suvarna_reader; md5 d2f897535c8c6237f464c81f11624701, 5804 chars)
--   NEW (md5 51e04fbaf5b60e4b2f89d9463aaac93d, 6302 chars; the dollar-quoted literal in the UPDATE below)
--
-- WHEN THIS APPLIES (SS N-316). Apply in the PHASE 4 window, immediately BEFORE the first Lahiri-only build of chart 482012f1 (1344, the
-- column, may go earlier; this file may not). Because platform/scripts/migrate.ts applies every unapplied migration on the next deploy,
-- MERGING this file IS applying it: the PR is held until that window.
--
-- TRIGGER EFFECT (the load-bearing fact; proved by the live test with the production trigger body). nirmana_registry_receipt_invalidation
-- (migration 596) fires AFTER UPDATE OF depends_on, natural_key_partition, health_probe, integrity_check_sql, target_floor, asset_kind,
-- asset_type, scope, has_writer, is_active, target_table. integrity_check_sql IS one of those columns and the text changes, so this UPDATE
-- STALES the asset_freshness receipt of ga_vargas on EVERY chart (freshness_state 'stale', reason 'registry_changed'). The trigger is NOT
-- touched here (SS N-316 ruling 3). EXPECTED EFFECT, accepted: charts 1c826d5a and cb73cd3d show ga_vargas as stale after the apply. Clearing
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
-- VERIFICATION BY PRODUCTION STRUCTURE (after the apply, as suvarna_reader; expect md5 51e04fbaf5b60e4b2f89d9463aaac93d and length 6302):
--   SELECT asset_id, md5(integrity_check_sql), length(integrity_check_sql) FROM asset_registry WHERE asset_id = 'ga_vargas';
-- and run the integrity text read-only against the database: it must return true while every chart still has NULL build_ayanamshas and
-- the data holds five ayanamshas (same answer as the OLD text).
--
-- ROLLBACK (not executed by migrate.ts; also fires the staling trigger): UPDATE asset_registry SET integrity_check_sql = <the OLD live
-- text, recoverable from git history of the migration that last set it plus this header's md5> WHERE asset_id = 'ga_vargas' AND
-- md5(integrity_check_sql) = '51e04fbaf5b60e4b2f89d9463aaac93d';

SET LOCAL lock_timeout = '5s';

DO $pre$
DECLARE v_n int; v_md5 text;
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                  WHERE table_schema = 'public' AND table_name = 'charts' AND column_name = 'build_ayanamshas') THEN
    RAISE EXCEPTION '1346: charts.build_ayanamshas is missing (migration 1344 must apply first)';
  END IF;
  SELECT count(*), max(md5(integrity_check_sql)) INTO v_n, v_md5 FROM asset_registry WHERE asset_id = 'ga_vargas';
  IF v_n = 0 THEN
    RAISE NOTICE '1346: no ga_vargas registry row (empty registry); nothing to do';
  ELSIF v_md5 = '51e04fbaf5b60e4b2f89d9463aaac93d' THEN
    RAISE NOTICE '1346: ga_vargas integrity_check_sql is already chart-aware; nothing to do';
  ELSIF v_md5 IS DISTINCT FROM 'd2f897535c8c6237f464c81f11624701' THEN
    RAISE NOTICE '1346: ga_vargas integrity_check_sql is not the text this migration was written against (md5 %); NO-OP, integrity_check_sql left as is', v_md5;
  END IF;
END
$pre$;

UPDATE asset_registry
SET integrity_check_sql = $chk$
-- ga_vargas integrity contract (target table: chart_divisionals)
-- D-CND-03: chart-partitioned / row-wise, attribution-preserving. No bare count pin (C12).
-- chart_divisionals_unique_idx (chart_id, graha, ayanamsha_id, varga, fact_category, fact_key, fact_subject)
-- (widened by F-A2) is ALREADY a DB UNIQUE, so no distinctness conjunct appears here (D-CND-03 rule 4).
-- Conjunct (e) (F-A2 / Q-L1-01, migration 1222) is the presence detector; every other
-- conjunct is NOT EXISTS-shaped and passes on an empty or unreadable table (CLAUDE.md N.8).
-- Conjunct (c) SCOPED to the canonical chart (migration 884): performance-and-coverage
-- tradeoff, disclosed in that migration's header -- same precedent as ga_dashas' own
-- integrity_check_sql (migration 882) and ga_positions' original FORENSIC-gate conjunct.
SELECT
  -- (a) sign / sign_number internal consistency. Nothing enforces this mapping at the DB level
  -- (sign_number has a 1-12 range CHECK, sign has none) -- a row could carry a valid sign_number
  -- with a sign name that doesn't correspond to it.
  NOT EXISTS (
    SELECT 1 FROM chart_divisionals
    WHERE sign IS NOT NULL AND sign_number IS NOT NULL
      AND sign <> (ARRAY['Aries','Taurus','Gemini','Cancer','Leo','Virgo','Libra','Scorpio',
                          'Sagittarius','Capricorn','Aquarius','Pisces'])[sign_number]
  )
  -- (b) vargottama correctness. The writer's own definition (_compute_vargottama, ga_vargas_writer.py
  -- :533-535: "True if same sign in D1 and this varga") is re-derived here directly from the
  -- varga_position rows it must agree with -- a dedicated varga_vargottama_flag row that drifts
  -- from the two position rows it is supposed to compare is a stale or miscomputed flag.
  AND NOT EXISTS (
    SELECT 1 FROM chart_divisionals vg
    WHERE vg.fact_category = 'varga_vargottama_flag'
      AND NOT EXISTS (
        SELECT 1 FROM chart_divisionals d1pos
        JOIN chart_divisionals vpos
          ON vpos.chart_id = d1pos.chart_id AND vpos.ayanamsha_id = d1pos.ayanamsha_id
         AND vpos.graha = d1pos.graha AND vpos.varga = vg.varga
        WHERE d1pos.chart_id = vg.chart_id AND d1pos.ayanamsha_id = vg.ayanamsha_id
          AND d1pos.graha = vg.graha AND d1pos.varga = 'D1'
          AND d1pos.fact_category = 'varga_position' AND d1pos.fact_key = 'sign'
          AND vpos.fact_category = 'varga_position' AND vpos.fact_key = 'sign'
          AND vg.vargottama = (d1pos.sign = vpos.sign)
      )
  )
  -- (c) §N.5 D1 authority: chart_divisionals' own D1 sign is a re-derivation of the SAME fact
  -- ga_positions/chart_facts already computed. SCOPED to the canonical chart (migration 884) --
  -- see that migration's header. Chart 1c826d5a carries 3 real, known, untouched mismatches
  -- (Mercury/Rahu/Ketu, surya_siddhanta_classical) out of this campaign's dispatch scope; the
  -- canonical chart's own prior F-A1 instance (raman/Moon) is confirmed fixed by PR #1766 and
  -- this rebuild.
  AND NOT EXISTS (
    SELECT 1 FROM chart_divisionals cd
    WHERE cd.chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
      AND cd.varga = 'D1' AND cd.fact_category = 'varga_position' AND cd.fact_key = 'sign'
      AND cd.graha = ANY (ARRAY['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Rahu','Ketu'])
      AND NOT EXISTS (
        SELECT 1 FROM chart_facts f
        WHERE f.chart_id = cd.chart_id AND f.ayanamsha_id = cd.ayanamsha_id
          AND f.fact_category = 'graha_position' AND f.fact_key = 'sign'
          AND f.fact_value_text = cd.sign
          AND f.fact_subject = (CASE cd.graha
                WHEN 'Sun' THEN 'SUN' WHEN 'Moon' THEN 'MOON' WHEN 'Mars' THEN 'MAR'
                WHEN 'Mercury' THEN 'MER' WHEN 'Jupiter' THEN 'JUP' WHEN 'Venus' THEN 'VEN'
                WHEN 'Saturn' THEN 'SAT' WHEN 'Rahu' THEN 'RAH_MEAN' WHEN 'Ketu' THEN 'KET_MEAN' END)
      )
  )
  -- (d) identity range guard for every position-bearing row: chart_divisionals carries no CHECK
  -- on chart_id/graha/ayanamsha_id/varga/fact_category/fact_key being non-null at all -- only the
  -- UNIQUE index requires them jointly (NULLS NOT DISTINCT), which cannot fail on a single NULL
  -- field appearing consistently.
  AND NOT EXISTS (
    SELECT 1 FROM chart_divisionals
    WHERE chart_id IS NULL OR graha IS NULL OR ayanamsha_id IS NULL
       OR varga IS NULL OR fact_category IS NULL OR fact_key IS NULL
  )
  -- (e) NON-VACUITY (F-A2, Q-L1-01; CLAUDE.md N.8). Conjuncts (a)-(d) are all NOT EXISTS, so a table the
  -- builder cannot read (row-level security with no policy, the 2026-10-01 incident), or an emptied
  -- table, passed every one of them. This conjunct FAILS when any declared (ayanamsha, varga) of the
  -- canonical chart has fewer than the nine graha varga_position/sign rows -- zero rows is the extreme
  -- case, too few is the partial one. Scoped to the canonical chart by literal, the disclosed
  -- 882/884/902/1019/1022/1215 tradeoff: other charts' builds are not measured here.
  -- (migration 1346) The ayanamsha set of the grid is the canonical chart's OWN charts.build_ayanamshas
  -- (NULL = the five). If the charts row is missing the LEFT JOIN falls back to the five, so an absent
  -- charts row stays red on an empty table (never vacuously green).
  AND NOT EXISTS (
    SELECT 1
    FROM (SELECT a.ayanamsha_id
          FROM (SELECT '482012f1-710e-4a25-994a-93821f5871aa'::uuid AS id) k
          LEFT JOIN charts ch ON ch.id = k.id
          CROSS JOIN LATERAL unnest(COALESCE(ch.build_ayanamshas, ARRAY['lahiri_chitrapaksha','true_chitra','krishnamurti','raman','surya_siddhanta_classical']::text[])) AS a(ayanamsha_id)) AS ay
    CROSS JOIN unnest(ARRAY['D1','D2','D3','D4','D5','D6','D7','D8','D9','D10','D11','D12','D14','D15','D16','D20','D21','D24','D27','D30','D32','D33','D40','D45','D50','D54','D60','D108','D150','D2700']) AS vg(varga)
    WHERE (SELECT count(*) FROM chart_divisionals cd
            WHERE cd.chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
              AND cd.ayanamsha_id = ay.ayanamsha_id AND cd.varga = vg.varga
              AND cd.fact_category = 'varga_position' AND cd.fact_key = 'sign'
              AND cd.graha = ANY (ARRAY['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Rahu','Ketu'])) < 9
  )
  AS integrity_passed
$chk$
WHERE asset_id = 'ga_vargas'
  AND md5(integrity_check_sql) = 'd2f897535c8c6237f464c81f11624701';

DO $post$
DECLARE v_md5 text;
BEGIN
  SELECT max(md5(integrity_check_sql)) INTO v_md5 FROM asset_registry WHERE asset_id = 'ga_vargas';
  IF v_md5 = 'd2f897535c8c6237f464c81f11624701' THEN
    RAISE EXCEPTION '1346: ga_vargas integrity_check_sql update did not take (still the old text)';
  END IF;
END
$post$;
