-- 745_nirmana_l1_ga_structural_integrity_contract.sql
--
-- NIRMĀṆA L1 Gaṇita — W3 IMPLEMENT. Discharges F-A14 for ga_structural: integrity_check_sql was
-- NULL, so the freeze-time detector fell back to count(*) > 0 (§N.8 -- an unearned signal).
--
-- Target: chart_facts, scoped to a SINGLE fact_category (graha_vargottama_amplification_factor)
-- of ga_structural's 57 owned categories (fact_category_ownership). ga_structural_writer.py is
-- ~7,900 lines covering 57 structural fact_categories across 16 shodasha vargas -- this is a
-- bounded first F-A14 pass on its most cross-checkable single category, not exhaustive coverage.
--
-- Discovered a genuine, previously-untracked defect while authoring this contract, filed as F-A15
-- (see conjunct (b) below): ga_structural re-derives D9 vargottama independently via its own
-- inline formula rather than citing ga_vargas' authoritative varga_vargottama_flag (§N.5),
-- disagreeing on 4/105 live rows. Conjunct (b) is shipped RED today, matching the F-C8 precedent
-- (migration 658, PR #1853): a real detector that will clear once the underlying writer bug is
-- fixed, verified via a synthetic post-fix overlay that clears cleanly.
--
-- Both conjuncts were EXECUTED against live production and MUTATION-PROVED before landing.
--
-- Transaction ownership belongs to platform/scripts/migrate.ts.

UPDATE asset_registry SET integrity_check_sql = $ck$
-- ga_structural integrity contract (target: chart_facts, scoped to
-- graha_vargottama_amplification_factor). D-CND-03: chart-partitioned / row-wise,
-- attribution-preserving. No bare count pin (C12). No distinctness conjunct -- this is not the
-- category's natural key (chart_facts_unique_null_formula already covers it).
SELECT
  -- (a) amplification_factor domain: the writer's own inline comment states it is "1.25 if
  -- vargottama, 1.0 otherwise" -- no third value is ever legitimate.
  NOT EXISTS (
    SELECT 1 FROM chart_facts
    WHERE fact_category = 'graha_vargottama_amplification_factor'
      AND fact_value_num NOT IN (1.0, 1.25)
  )
  -- (b) F-A15: amplification_factor must agree with ga_vargas' own authoritative D9
  -- varga_vargottama_flag (chart_divisionals, §N.5) for the SAME (chart, ayanamsha, graha) --
  -- re-derived here directly rather than restated. GENUINELY RED TODAY on 4/105 rows (2 charts,
  -- surya_siddhanta_classical/raman ayanamshas): ga_structural's own inline vargottama
  -- re-derivation (a hardcoded navamsha_starts table + float degree arithmetic, this writer's own
  -- comment: "Simplified: derive from position") disagrees with ga_vargas' authoritative D9
  -- computation. This is a NEW §N.5 violation (ga_structural re-derives instead of citing the
  -- authority) tracked as F-A15 -- verified as a genuine detector, not a permanently-broken
  -- placeholder, via a synthetic post-fix overlay (recomputing amplification_factor from
  -- ga_vargas' own flag) that clears cleanly.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts a
    JOIN chart_divisionals v
      ON v.chart_id = a.chart_id AND v.ayanamsha_id = a.ayanamsha_id
     AND v.fact_category = 'varga_vargottama_flag' AND v.varga = 'D9'
     AND v.graha = initcap(
       CASE a.fact_subject
         WHEN 'SUN' THEN 'Sun' WHEN 'MOON' THEN 'Moon' WHEN 'MAR' THEN 'Mars'
         WHEN 'MER' THEN 'Mercury' WHEN 'JUP' THEN 'Jupiter' WHEN 'VEN' THEN 'Venus'
         WHEN 'SAT' THEN 'Saturn' ELSE a.fact_subject END
     )
    WHERE a.fact_category = 'graha_vargottama_amplification_factor'
      AND (a.fact_value_num = 1.25) <> v.vargottama
  )
  AS integrity_passed
$ck$
 WHERE asset_id = 'ga_structural';
