-- DRAFT_f_a2_key_widening.sql  (PLACEHOLDER NAME: SS allocates the migration number; do NOT number or apply)
--
-- STATUS: DRAFT. Not in platform/migrations on purpose: the deploy-time runner applies every file there.
-- Author: S-L1 mandatory item Q01 writer lane. Nothing here has been applied to any database.
--
-- WHAT THIS IS. The registry-only half of Q-L1-01 (SS-ruled, N-62): the ga_vargas integrity_check_sql gains
--   (e) a non-vacuity clause (zero or too few varga_position rows for any declared ayanamsha x varga FAILS), and
--   (f) a key-grain clause (the families the six-column key collapsed must exist at their intended grain).
-- asset_registry is owned by amjis_app (read from the catalog, 2026-10-02), so this is an ordinary migration:
-- no owner path. Pattern: migration 884 (UPDATE asset_registry, one row) with the I-8 / 1215 guards (lock_timeout,
-- a DO $pre$ that proves the text being replaced is the text we read, a DO $post$ that proves the new text took).
--
-- WHAT THIS IS NOT. The unique-index widening, the capture-trigger widening and the capture-function hunk live on
-- the OWNER path (chart_divisionals, its index and the L1 attestation tables are owned by data_plane_l1_owner):
-- see F_A2_KEY_WIDENING_D6_PLAN_v1_0.md and d6_f_a2_key_widening_DRAFT.py in this directory.
--
-- ORDER (see the plan, section 6): D6 owner-path change -> this migration -> S-L1 ga_vargas rebuild. Conjunct (f) is
-- RED on the data in production today (24,392 rows on the canonical chart, widened grain absent) and turns green only
-- after the rebuild; (e) is green today (measured: the nine position rows exist for every ayanamsha x varga, 5 x 30).
-- If SS prefers (f) to land only after the rebuild, drop the (f) blocks from this file and apply them as a second
-- migration; (e) alone has no ordering constraint.
--
-- BASE TEXT. The live ga_vargas integrity_check_sql was read as suvarna_reader on 2026-10-02: 4,216 chars, md5
-- 255af7c5194553e19f7009c1e8774d8a, byte-identical to migration 884's body. The pre-check below refuses to run on any other text.

BEGIN;

SET LOCAL lock_timeout = '5s';

DO $pre$
DECLARE v_md5 text; v_n int;
BEGIN
  SELECT count(*), max(md5(integrity_check_sql)) INTO v_n, v_md5 FROM asset_registry WHERE asset_id = 'ga_vargas';
  IF v_n <> 1 THEN
    RAISE EXCEPTION 'F-A2 integrity: expected exactly one ga_vargas registry row, found %', v_n;
  END IF;
  IF v_md5 IS DISTINCT FROM '255af7c5194553e19f7009c1e8774d8a' THEN
    RAISE EXCEPTION 'F-A2 integrity: ga_vargas integrity_check_sql is not the text this migration was written against (md5 %)', v_md5;
  END IF;
END
$pre$;

UPDATE asset_registry
SET integrity_check_sql = $ck$
-- ga_vargas integrity contract (target table: chart_divisionals)
-- D-CND-03: chart-partitioned / row-wise, attribution-preserving. No bare count pin (C12).
-- chart_divisionals_unique_idx (chart_id, graha, ayanamsha_id, varga, fact_category, fact_key, fact_subject)
-- (widened by F-A2) is ALREADY a DB UNIQUE, so no distinctness conjunct appears here (D-CND-03 rule 4).
-- Conjuncts (e) and (f) (F-A2 / Q-L1-01) are the presence-and-grain detectors; every other
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
  -- (f) KEY-GRAIN COMPLETENESS (F-A2). The three row families the six-column key silently collapsed
  -- must exist at their intended grain: 12 house-lord rows per (ayanamsha, varga) (a lord ruling two
  -- houses kept one), 96 ashtakavarga rows per (ayanamsha, varga) (12 signs x 7 grahas + SARVA; only
  -- the Aries row survived), and 60 D30 lord rows per ayanamsha (5 lords x 12 signs; 10 survived).
  -- These are per-scope structural cardinalities of the writer's own tables (houses, signs, D30
  -- regions), not a volume pin of the table (C12). RED on pre-F-A2 data BY DESIGN until the S-L1
  -- ga_vargas rebuild lands the widened rows (the migration 654 precedent).
  AND NOT EXISTS (
    SELECT 1
    FROM unnest(ARRAY['lahiri_chitrapaksha','true_chitra','krishnamurti','raman','surya_siddhanta_classical']) AS ay(ayanamsha_id)
    CROSS JOIN unnest(ARRAY['D1','D2','D3','D4','D5','D6','D7','D8','D9','D10','D11','D12','D14','D15','D16','D20','D21','D24','D27','D30','D32','D33','D40','D45','D50','D54','D60','D108','D150','D2700']) AS vg(varga)
    WHERE (SELECT count(*) FROM chart_divisionals cd
            WHERE cd.chart_id = '482012f1-710e-4a25-994a-93821f5871aa' AND cd.ayanamsha_id = ay.ayanamsha_id AND cd.varga = vg.varga
              AND cd.fact_category = 'varga_house_lord') <> 12
       OR (SELECT count(*) FROM chart_divisionals cd
            WHERE cd.chart_id = '482012f1-710e-4a25-994a-93821f5871aa' AND cd.ayanamsha_id = ay.ayanamsha_id AND cd.varga = vg.varga
              AND cd.fact_category = 'varga_ashtakavarga') <> 96
  )
  AND NOT EXISTS (
    SELECT 1
    FROM unnest(ARRAY['lahiri_chitrapaksha','true_chitra','krishnamurti','raman','surya_siddhanta_classical']) AS ay(ayanamsha_id)
    WHERE (SELECT count(*) FROM chart_divisionals cd
            WHERE cd.chart_id = '482012f1-710e-4a25-994a-93821f5871aa' AND cd.ayanamsha_id = ay.ayanamsha_id
              AND cd.fact_category = 'varga_d30_lord_per_amsa') <> 60
  )
  AS integrity_passed
$ck$
WHERE asset_id = 'ga_vargas';

DO $post$
DECLARE v_sql text; v_md5 text;
BEGIN
  SELECT integrity_check_sql, md5(integrity_check_sql) INTO v_sql, v_md5 FROM asset_registry WHERE asset_id = 'ga_vargas';
  IF v_md5 IS DISTINCT FROM 'c0070b06735d8ed4035b1634c4f9599c'
     OR position('(e) NON-VACUITY' in v_sql) = 0
     OR position('(f) KEY-GRAIN COMPLETENESS' in v_sql) = 0 THEN
    RAISE EXCEPTION 'F-A2 integrity: the new integrity_check_sql did not take (md5 %)', v_md5;
  END IF;
END
$post$;

COMMIT;
