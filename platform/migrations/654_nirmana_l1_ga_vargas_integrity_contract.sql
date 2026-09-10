-- 654_nirmana_l1_ga_vargas_integrity_contract.sql
--
-- NIRMĀṆA L1 Gaṇita — W3 IMPLEMENT. Discharges F-A14 for ga_vargas: integrity_check_sql was
-- NULL, so the freeze-time detector fell back to `count(*) > 0` (§N.8 -- an unearned signal).
--
-- Standard: D-CND-03 (Conductor ruling on #1723/#1727) -- chart-partitioned, attribution-
-- preserving invariants in preference to whole-table aggregates. C12: no bare count(*)=N
-- equality pin. chart_divisionals_unique_idx (chart_id, graha, ayanamsha_id, varga,
-- fact_category, fact_key) is ALREADY a DB UNIQUE, so no distinctness conjunct appears here
-- (D-CND-03 rule 4) -- and per F-A1(b) that index is itself part of a KNOWN, separately-tracked
-- defect (fact_subject not in the key silently collapses D30/D60 lord-chain rows via
-- ON CONFLICT DO NOTHING), not re-encoded here as if it were a passing check.
--
-- Every conjunct below was EXECUTED against live production and MUTATION-PROVED before landing:
-- each was re-run against a corruption injected inside a CTE overlay and shown to return false.
--
-- ONE CONJUNCT RETURNS FALSE TODAY. That is deliberate, per the same discipline as ga_dashas'
-- migration 653 and the L3 W3 batch (migration 670): a contract that passes over known-bad data
-- would be the gate-weakening the hard floor forbids.
--   (c) D1-sign cross-check against chart_facts.graha_position -- 4 rows, two charts:
--       - chart 482012f1 / raman: Moon reads Pisces here, Aquarius in chart_facts. Traced to a
--         precise, quantified confirmation of F-A1 (ga_vargas' already-tracked "computed for the
--         wrong instant" defect): chart_facts longitude_sidereal=328.50153 (Aquarius, 28.5 deg in
--         sign, close to the Pisces boundary at 330); chart_divisionals reconstructs to
--         330+1.2184=331.2184 -- an offset of 2.717 deg, matching F-A1's own measured Moon offset
--         ("+2.7169 deg") to three decimal places. This is the SAME already-tracked defect,
--         caught crossing a D1 sign boundary specifically on the raman ayanamsha, not previously
--         measured at this precision.
--       - chart 1c826d5a / surya_siddhanta_classical: Mercury/Rahu/Ketu each read one sign
--         earlier than chart_facts (Aquarius/Pisces, Aries/Taurus, Libra/Scorpio respectively) --
--         the same systematic one-sign-early pattern a constant time offset produces.
--   This conjunct is NOT suppressed, scoped around, or given slack to pass -- it is the correct,
--   working detector for F-A1's already-known defect, and stays red until ga_vargas rebuilds
--   with its already-landed timing fix (D-L1-18, PR #1766).
--
-- Transaction ownership belongs to platform/scripts/migrate.ts.

UPDATE asset_registry SET integrity_check_sql = $ck$
-- ga_vargas integrity contract (target table: chart_divisionals)
-- D-CND-03: chart-partitioned / row-wise, attribution-preserving. No bare count pin (C12).
-- chart_divisionals_unique_idx (chart_id, graha, ayanamsha_id, varga, fact_category, fact_key)
-- is ALREADY a DB UNIQUE, so no distinctness conjunct appears here (D-CND-03 rule 4).
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
  -- ga_positions/chart_facts already computed (D-L1-19: "three L1 assets declare ga_positions
  -- and then re-derive positions... exactly how ga_vargas came to hold a different D1 from the
  -- authority it declares a dependency on" -- F-A1). RED TODAY on 4 rows (chart 482012f1/raman
  -- Moon; chart 1c826d5a/surya_siddhanta_classical Mercury+Rahu+Ketu) -- see this migration's
  -- header for the traced root cause (F-A1's timing bug, precisely quantified). Clean on every
  -- other (chart, ayanamsha, graha) combination measured. This conjunct exists to hold that D1
  -- ground and catch a FUTURE regression as well as report the current, already-tracked one --
  -- it is deliberately NOT scoped to exclude the rows it currently catches.
  AND NOT EXISTS (
    SELECT 1 FROM chart_divisionals cd
    WHERE cd.varga = 'D1' AND cd.fact_category = 'varga_position' AND cd.fact_key = 'sign'
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
  AS integrity_passed
$ck$
 WHERE asset_id = 'ga_vargas';
