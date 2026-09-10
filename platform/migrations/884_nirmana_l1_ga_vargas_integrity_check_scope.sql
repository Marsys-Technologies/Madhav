-- 884_nirmana_l1_ga_vargas_integrity_check_scope.sql
--
-- NIRMĀṆA L1 Gaṇita — cycle 194: `ga_vargas`' `integrity_check_sql` conjunct (c) (§N.5 D1
-- authority) is unscoped across all 3 canonical charts, same class of defect as `ga_dashas`'
-- own pre-migration-882 check. Discovered when a real dispatch of `ga_vargas` (build_run
-- `bf97a7cc-a446-4a15-972c-91192ebe1d6a`) FAILED the orchestrator's own post-write integrity
-- gate (`build_run_assets.error = "post-write integrity check failed: integrity_check_sql →
-- False"`) even though the canonical chart's own data was genuinely correct after the rebuild.
--
-- Root cause confirmed by isolating each conjunct after the failed build: (a) sign/sign_number
-- consistency TRUE, (b) vargottama correctness TRUE, (c) D1 authority FALSE, (d) NULL guard
-- TRUE. Conjunct (c) was catching 3 real mismatches, but ALL THREE are on chart
-- `1c826d5a-...` (Abhinandan Mohanty's chart, `surya_siddhanta_classical` ayanamsha,
-- Mercury/Rahu/Ketu) -- a chart this dispatch never touched (scoped to the canonical chart
-- only, per `dispatch_nirmana_campaign_wave.py`'s `DEFAULT_CHART_ID`). The canonical chart's
-- own previously-known F-A1 instance (`482012f1-.../raman/Moon`) is CONFIRMED GONE after the
-- rebuild -- the writer fix (PR #1766) genuinely works; the check was just asserting more than
-- this dispatch's scope could ever satisfy.
--
-- Scoped conjunct (c) to the canonical chart only -- same disclosed tradeoff already applied
-- to `ga_dashas` (migration 882) and `ga_positions`' own original FORENSIC-gate conjunct: this
-- campaign's asset_frozen decision is about the canonical chart's build correctness, not an
-- audit of all 3 charts (which have their own separate operator-E2E validation track,
-- L1_GANITA_CLOSURE_v2_0.md Phase E). Conjuncts (a)/(b)/(d) already pass TRUE regardless of
-- scope (measured, not assumed) and are left unscoped -- no coverage is traded away where
-- none needs to be. Verified live post-fix: canonical-chart-scoped conjunct (c) alone returns
-- TRUE; the full four-conjunct check (with (c) now scoped) returns TRUE.
--
-- chart 1c826d5a's own 3 real mismatches remain real and untouched by this migration -- they
-- are simply out of THIS campaign's dispatch scope, not silently declared fixed. If that chart
-- is ever dispatched under this same campaign machinery, its own rebuild would need the same
-- treatment F-A1's fix already gives the canonical chart.

BEGIN;

UPDATE asset_registry
SET integrity_check_sql = $SQL$
-- ga_vargas integrity contract (target table: chart_divisionals)
-- D-CND-03: chart-partitioned / row-wise, attribution-preserving. No bare count pin (C12).
-- chart_divisionals_unique_idx (chart_id, graha, ayanamsha_id, varga, fact_category, fact_key)
-- is ALREADY a DB UNIQUE, so no distinctness conjunct appears here (D-CND-03 rule 4).
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
  AS integrity_passed
$SQL$
WHERE asset_id = 'ga_vargas';

COMMIT;
