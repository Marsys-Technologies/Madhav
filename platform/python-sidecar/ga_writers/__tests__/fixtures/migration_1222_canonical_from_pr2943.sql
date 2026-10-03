-- 1222_nirmana_l1_ga_vargas_integrity_nonvacuity.sql
--
-- S-L1 mandatory item Q01 (L1 decision sheet Q-L1-01, SS-ruled N-62; SS direction on F-A2, #2858): the
-- ga_vargas integrity_check_sql gains a NON-VACUITY conjunct. Transaction ownership belongs to
-- platform/scripts/migrate.ts (no BEGIN/COMMIT here). Data-only: one UPDATE of one asset_registry row
-- (amjis_app-owned, read from the catalog 2026-10-02); no table is altered; no owner path.
--
-- HELD. This file lives in its own draft PR (suvarna/land/TI-mig-1222-1223-001) together with migration 1223, split out of
-- the F-A2 PR (#2858). MERGE = APPLY at the next deploy (migrate.ts runs on every deploy, before that deploy's
-- images roll), so it merges ONLY in the S-L1 window W1.
--
-- ORDERING (hard rule).
--   * Merges ONLY in the S-L1 window W1, BACK TO BACK with 1221 and 1226 and 1223, so ONE deploy applies all four.
--     Numeric apply order: 1221, 1222, 1223, 1226. Not earlier, not in a deploy of its own.
--   * Valid with the OLD ga_vargas writer image AND the NEW F-A2 writer image: conjunct (e) counts only
--     varga_position/sign rows per declared (ayanamsha, varga) of the canonical chart, and both images write
--     the nine graha rows per pair. It is TRUE on production today (the new check text was evaluated read-only
--     as suvarna_reader on 2026-10-02: integrity_passed = true; the old text: true).
--   * Applied BEFORE the F-A2 ga_vargas rebuild, never after: the rebuild's post-write integrity gate and the
--     freeze-time integrity_verified detector then run the non-vacuity conjunct against the rebuilt rows.
--   * Independent of 1221, 1223 and 1226 in content: it writes asset_registry.integrity_check_sql of ga_vargas
--     only; the md5 guard below is on that column of that row, which none of the other three touches
--     (1221: ga_structural integrity_check_sql; 1226: depends_on of ga_dashas, ga_yoga, ga_vargas).
--   * 0 ACTIVE RUNS AT APPLY: no build run may be in flight for ga_vargas at apply (read-only check, expected 0):
--       SELECT count(*) FROM build_runs r JOIN build_run_assets a ON a.run_id = r.id
--        WHERE a.asset_id = 'ga_vargas' AND r.state NOT IN ('completed', 'failed', 'stopped');
--
-- SERVING EFFECT AT APPLY (binding for every migration PR; read from the catalog 2026-10-02, suvarna_reader).
--   `UPDATE ... SET integrity_check_sql` fires the live trigger nirmana_registry_receipt_invalidation
--   (migration 596): AFTER UPDATE OF depends_on, natural_key_partition, health_probe, integrity_check_sql,
--   target_floor, asset_kind, asset_type, scope, has_writer, is_active, target_table, FOR EACH ROW
--   WHEN (old.* IS DISTINCT FROM new.*), function nirmana_invalidate_registry_receipts(), which sets
--   asset_freshness.freshness_state = 'stale' (reason registry_changed) WHERE asset_id = NEW.asset_id.
--   So ga_vargas freshness goes STALE ON EVERY CHART (every scope/partition row of ga_vargas; the one row
--   readable as suvarna_reader is the canonical chart's, 'fresh' today) the moment this applies. No other
--   asset is touched. A stale receipt reads `receipt_not_fresh` in the served-generation resolver
--   (platform/src/lib/retrieval/registry/generation/served_generation.ts, partitionDefect), so ga_vargas is
--   UNRESOLVED for serving until a governed ga_vargas rebuild writes a fresh receipt.
--   Degraded set when this PR merges in W1 together with 1221, 1223 and 1226 =
--   {ga_structural (1221), ga_vargas (1222, 1223, 1226), ga_dashas (1226), ga_yoga (1226)}; all four are
--   rebuilt inside the S-L1 window, so the degradation is bounded by the window. A re-run (idempotent no-op,
--   below) updates 0 rows and does NOT fire the trigger again.
--
-- WHY. The four existing conjuncts (a)-(d) are all NOT EXISTS, so a chart_divisionals the builder cannot read
-- (row-level security with no policy, the 2026-10-01 incident) or an emptied table passes every one of them
-- (CLAUDE.md N.8; incident review F1). Conjunct (e) FAILS when any declared (ayanamsha, varga) of the canonical
-- chart has fewer than the nine graha varga_position/sign rows: zero rows is the extreme case, too few the partial one.
-- It is scoped to the canonical chart by literal, the disclosed 882/884/902/1019/1022/1215 tradeoff: other charts'
-- builds are not measured here. The key-grain numbers (12 house_lord / 96 ashtakavarga per ayanamsha x varga, 60 D30
-- per ayanamsha, canonical total 38,596) are deliberately NOT in this check: SS ruled them S-L1 acceptance criteria
-- (bare count pins), checked by f_a2_key_widening/s_l1_ga_vargas_acceptance_check.sql (stays with #2858).
--
-- BASE TEXT. The live ga_vargas integrity_check_sql was read as suvarna_reader on 2026-10-02: 4,216 chars, md5
-- 255af7c5194553e19f7009c1e8774d8a, byte-identical to migration 884's body. The new text is 5,804 chars, md5
-- d2f897535c8c6237f464c81f11624701; it is byte-identical to the text carried by #2858's version of this file
-- (the check text was not changed in the split; only this header and the guard shape below).
--
-- IDEMPOTENT SHAPE. The pre-check accepts exactly two states: the base text (apply) or the target text (already
-- applied: NOTICE, and the UPDATE below matches 0 rows, so nothing is rewritten and the trigger does not fire).
-- Any other md5 RAISES: the migration refuses to overwrite a text it was not written against. (#2858's version
-- raised on the target text too, i.e. was not re-runnable.) The post-check proves the new text took.
--
-- VERIFICATION BY PRODUCTION STRUCTURE (CLAUDE.md N.4, Trap 103: never trust a deploy log). After the deploy,
-- as suvarna_reader, expect one row with md5 = d2f897535c8c6237f464c81f11624701 and length 5804:
--   SELECT md5(integrity_check_sql), length(integrity_check_sql) FROM asset_registry WHERE asset_id = 'ga_vargas';
-- and expect the trigger's effect on ga_vargas only (stale until the rebuild writes a fresh receipt):
--   SELECT asset_id, freshness_state, reasons FROM asset_freshness WHERE asset_id = 'ga_vargas';
--
-- ROLLBACK (not executed by migrate.ts): UPDATE asset_registry SET integrity_check_sql = <migration 884's $SQL$ body,
-- md5 255af7c5194553e19f7009c1e8774d8a> WHERE asset_id = 'ga_vargas'; fires the same trigger (freshness is already stale, so
-- a rollback does not restore the pre-apply 'fresh'; only a governed ga_vargas rebuild does).

SET LOCAL lock_timeout = '5s';

DO $pre$
DECLARE v_md5 text; v_n int;
BEGIN
  SELECT count(*), max(md5(integrity_check_sql)) INTO v_n, v_md5 FROM asset_registry WHERE asset_id = 'ga_vargas';
  IF v_n <> 1 THEN
    RAISE EXCEPTION '1222: expected exactly one ga_vargas registry row, found %', v_n;
  END IF;
  IF v_md5 = 'd2f897535c8c6237f464c81f11624701' THEN
    RAISE NOTICE '1222: ga_vargas integrity_check_sql already carries the non-vacuity text; nothing to do';
  ELSIF v_md5 IS DISTINCT FROM '255af7c5194553e19f7009c1e8774d8a' THEN
    RAISE EXCEPTION '1222: ga_vargas integrity_check_sql is not the text this migration was written against (md5 %)', v_md5;
  END IF;
END
$pre$;

UPDATE asset_registry
SET integrity_check_sql = $ck$
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
  AND NOT EXISTS (
    SELECT 1
    FROM unnest(ARRAY['lahiri_chitrapaksha','true_chitra','krishnamurti','raman','surya_siddhanta_classical']) AS ay(ayanamsha_id)
    CROSS JOIN unnest(ARRAY['D1','D2','D3','D4','D5','D6','D7','D8','D9','D10','D11','D12','D14','D15','D16','D20','D21','D24','D27','D30','D32','D33','D40','D45','D50','D54','D60','D108','D150','D2700']) AS vg(varga)
    WHERE (SELECT count(*) FROM chart_divisionals cd
            WHERE cd.chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
              AND cd.ayanamsha_id = ay.ayanamsha_id AND cd.varga = vg.varga
              AND cd.fact_category = 'varga_position' AND cd.fact_key = 'sign'
              AND cd.graha = ANY (ARRAY['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Rahu','Ketu'])) < 9
  )
  AS integrity_passed
$ck$
WHERE asset_id = 'ga_vargas'
  AND md5(integrity_check_sql) = '255af7c5194553e19f7009c1e8774d8a';

DO $post$
DECLARE v_md5 text;
BEGIN
  SELECT md5(integrity_check_sql) INTO v_md5 FROM asset_registry WHERE asset_id = 'ga_vargas';
  IF v_md5 IS DISTINCT FROM 'd2f897535c8c6237f464c81f11624701' THEN
    RAISE EXCEPTION '1222: the new ga_vargas integrity_check_sql did not take (md5 %)', v_md5;
  END IF;
END
$post$;
