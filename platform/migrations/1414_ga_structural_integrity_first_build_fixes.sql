-- 1414_ga_structural_integrity_first_build_fixes.sql
--
-- Routine data-only migration: ONE md5-guarded UPDATE of ONE column (integrity_check_sql) of ONE asset_registry row
-- (asset_id 'ga_structural'). Transaction ownership belongs to platform/scripts/migrate.ts (no BEGIN/COMMIT here). No DDL.
--
-- THE DEFECT. A brand-new chart's first Ganita build (chart 87724183-..., Adyasha Priyadarshini, run 2268c9e2, 2026-10-29)
-- wrote ga_structural correctly, but the post-write integrity check returned false, so ga_structural and its four dependents
-- (ga_sade_sati, ga_yoga, ga_vichara, ga_fact_identity) never built. Splitting the check into its conjuncts against live data
-- found exactly two false conjuncts, both defects in the CHECK, not the writer:
--
--   1. graha_functional_class_per_ascendant (bphs_canonical) re-derivation: house2 is NULL for a single-sign lord (Sun, Moon),
--      so `hs.house1 IN (...) OR hs.house2 IN (...)` evaluates to NULL instead of false whenever house1 misses. Every CASE
--      branch then falls through to 'neutral'. For a Sagittarius lagna the Moon owns the 8th; the writer
--      (_get_functional_class_dynamic) says 'temporal_malefic' and the check, by NULL accident, said 'neutral' (5 rows, one per
--      ayanamsha). The four flags now COALESCE the house2 term to false, which is exactly the writer's set arithmetic.
--      The Aries branch (the canonical chart) is unaffected; no other chart had a violation.
--
--   2. graha_composite_state_classification re-derivation reads ga_yoga_firings for neecha_bhanga_raja_yoga, but ga_yoga depends
--      on ga_structural and runs AFTER it. On a chart's first build ga_yoga_firings holds no rows, so every correct
--      'debilitation_cancelled' verdict (the writer's own evaluate_nbry, the same function ga_yoga uses) fails the check.
--      Adyasha: Mars (Cancer; Moon, lord of Cancer, in the lagna kendra) and Venus (Virgo; Mercury, lord of Virgo, in kendra)
--      -- 8 rows. The conjunct now exempts a debilitated, non-combust 'debilitation_cancelled' row ONLY while that
--      chart/ayanamsha has no ga_yoga_firings rows at all; once ga_yoga has built, the strict branch applies unchanged.
--
-- Proven before writing (read-only, live DB): OLD text -> integrity_passed false; NEW text -> true (table-wide).
--
--   OLD md5 fcd217e25127653ee28ad41c629946aa (208378 chars, = migration 1326 NEW)
--   NEW md5 b746387fd48e2a7df4383d48433afc79 (209250 chars)
--
-- GUARD (precedent 1326): md5 of the whole OLD text; anything else is a NOTICE-and-NO-OP; already-NEW is an idempotent no-op;
-- RAISES only if the UPDATE ran and the NEW md5 is not present afterwards.
--
-- SERVING EFFECT AT APPLY: the UPDATE fires nirmana_registry_receipt_invalidation (migration 596), which marks ga_structural's
-- asset_freshness rows 'stale' (registry_changed) on every chart that holds one, as 1326 did. A chart's ga_structural is fresh
-- again after its next ga_structural rebuild.
--
-- ROLLBACK (not executed by migrate.ts): reverse the five replace() calls under md5 guard 'b746387fd48e2a7df4383d48433afc79'.

SET LOCAL lock_timeout = '5s';

DO $m1414$
DECLARE
  c_old_md5 constant text := 'fcd217e25127653ee28ad41c629946aa';
  c_new_md5 constant text := 'b746387fd48e2a7df4383d48433afc79';
  c_old_1 constant text := $o1$(hs.house1 IN (1,4,7,10) OR hs.house2 IN (1,4,7,10)) AS is_kendra$o1$;
  c_new_1 constant text := $n1$(hs.house1 IN (1,4,7,10) OR COALESCE(hs.house2 IN (1,4,7,10), false)) AS is_kendra$n1$;
  c_old_2 constant text := $o2$(hs.house1 IN (1,5,9) OR hs.house2 IN (1,5,9)) AS is_trikona$o2$;
  c_new_2 constant text := $n2$(hs.house1 IN (1,5,9) OR COALESCE(hs.house2 IN (1,5,9), false)) AS is_trikona$n2$;
  c_old_3 constant text := $o3$(hs.house1 IN (6,8,12) OR hs.house2 IN (6,8,12)) AS is_dusthana$o3$;
  c_new_3 constant text := $n3$(hs.house1 IN (6,8,12) OR COALESCE(hs.house2 IN (6,8,12), false)) AS is_dusthana$n3$;
  c_old_4 constant text := $o4$(hs.house1 IN (3,11) OR hs.house2 IN (3,11)) AS is_upachaya$o4$;
  c_new_4 constant text := $n4$(hs.house1 IN (3,11) OR COALESCE(hs.house2 IN (3,11), false)) AS is_upachaya$n4$;
  c_old_5 constant text := $o5$          WHEN re.retrograde_flag = 'retrograde' AND a.fact_subject NOT IN ('RAH_MEAN', 'KET_MEAN') THEN 'weak'
          ELSE 'neutral'
        END)
$o5$;
  c_new_5 constant text := $n5$          WHEN re.retrograde_flag = 'retrograde' AND a.fact_subject NOT IN ('RAH_MEAN', 'KET_MEAN') THEN 'weak'
          ELSE 'neutral'
        END)
          -- Migration 1414 (first-build order): ga_yoga runs AFTER ga_structural, so on a chart's first Ganita build
          -- ga_yoga_firings holds no rows yet and the NBRY branch above cannot be confirmed. Only while that chart/ayanamsha
          -- has NO ga_yoga_firings rows at all, a debilitated, non-combust graha may read 'debilitation_cancelled' (the writer's
          -- own evaluate_nbry verdict). Once ga_yoga_firings exists for the chart/ayanamsha the strict branch applies again.
      AND NOT (
        a.fact_value_text = 'debilitation_cancelled'
        AND re.re_dignity = 'debilitated'
        AND re.combustion_state IS DISTINCT FROM 'combust'
        AND NOT EXISTS (SELECT 1 FROM ga_yoga_firings y0 WHERE y0.chart_id = a.chart_id AND y0.ayanamsha_id = a.ayanamsha_id)
      )
$n5$;
  v_found boolean;
  v_live  text;
  v_md5   text;
BEGIN
  SELECT true, integrity_check_sql INTO v_found, v_live
    FROM asset_registry WHERE asset_id = 'ga_structural' FOR UPDATE;
  IF v_found IS NOT TRUE THEN
    RAISE NOTICE '1414: no ga_structural registry row (empty registry); nothing to do';
    RETURN;
  END IF;
  v_md5 := md5(v_live);
  IF v_md5 = c_new_md5 THEN
    RAISE NOTICE '1414: ga_structural integrity_check_sql already carries the first-build fixes; nothing to do';
    RETURN;
  ELSIF v_md5 IS DISTINCT FROM c_old_md5 THEN
    RAISE NOTICE '1414: ga_structural integrity_check_sql is not the text this migration was written against (md5 %); NO-OP, integrity_check_sql left as is', v_md5;
    RETURN;
  END IF;

  UPDATE asset_registry
     SET integrity_check_sql = replace(replace(replace(replace(replace(integrity_check_sql, c_old_1, c_new_1), c_old_2, c_new_2), c_old_3, c_new_3), c_old_4, c_new_4), c_old_5, c_new_5)
   WHERE asset_id = 'ga_structural'
     AND md5(integrity_check_sql) = c_old_md5;

  SELECT md5(integrity_check_sql) INTO v_md5 FROM asset_registry WHERE asset_id = 'ga_structural';
  IF v_md5 IS DISTINCT FROM c_new_md5 THEN
    RAISE EXCEPTION '1414: ga_structural integrity_check_sql update did not take (md5 now %, expected %)', v_md5, c_new_md5;
  END IF;
END
$m1414$;
