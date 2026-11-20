-- Migration 1418: validate school-specific Gaṇita functional classes
-- Created: 2026-11-20
--
-- A8 requires both schools. DR-9 classifies Aries Mars as a functional benefic.
-- BPHS lagna-lord corrections follow Ch. 34. Raman classifications use How to Judge
-- a Horoscope, Vol. I, pp. 7–10. The old source formula remains valid for historical
-- rows and for a worker completing during the transition to the new engine.
--
-- Only the ga_structural registry check changes. The standard registry trigger marks
-- previous build receipts stale. The migration does not regenerate chart facts.
-- Transaction ownership belongs to platform/scripts/migrate.ts.

SET LOCAL lock_timeout = '5s';

DO $m1418$
DECLARE
  expected_before constant text := 'b746387fd48e2a7df4383d48433afc79';
  expected_after constant text := 'cacc07d6ce4f610ee031f6d56f89394e';
  old_school_check constant text := $old_school$    WHERE a.fact_category = 'graha_functional_class_per_ascendant' AND a.fact_key = 'bphs_canonical'
      AND a.fact_value_text <> b.fact_value_text
  )
  -- (bb3) full re-derivation:$old_school$;
  new_school_check constant text := $new_school$    WHERE a.fact_category = 'graha_functional_class_per_ascendant' AND a.fact_key = 'bphs_canonical'
      AND NOT starts_with(a.source_calculation, 'ga_structural.bphs_functional_class_v2/')
      AND a.fact_value_text <> b.fact_value_text
  )
  -- New functional classes have distinct sources and still require both school rows.
  AND NOT EXISTS (
    SELECT 1 FROM chart_facts a
    WHERE a.fact_category = 'graha_functional_class_per_ascendant'
      AND a.fact_key IN ('bphs_canonical', 'raman_variant')
      AND (starts_with(a.source_calculation, 'ga_structural.bphs_functional_class_v2/')
        OR starts_with(a.source_calculation, 'ga_structural.raman_functional_class_v2/'))
      AND NOT EXISTS (
        SELECT 1 FROM chart_facts b
        WHERE b.chart_id = a.chart_id AND b.ayanamsha_id = a.ayanamsha_id
          AND b.build_id = a.build_id AND b.fact_subject = a.fact_subject
          AND b.fact_category = a.fact_category
          AND (
            (a.fact_key = 'bphs_canonical' AND b.fact_key = 'raman_variant'
              AND starts_with(b.source_calculation, 'ga_structural.raman_functional_class_v2/'))
            OR (a.fact_key = 'raman_variant' AND b.fact_key = 'bphs_canonical'
              AND starts_with(b.source_calculation, 'ga_structural.bphs_functional_class_v2/'))
          )
      )
  )
  -- (bb3) full re-derivation:$new_school$;
  old_lordship_check constant text := $old_lordship$        CASE WHEN lg.fact_value_text = 'Aries' THEN (
          CASE a.fact_subject
            WHEN 'SUN' THEN 'temporal_malefic' WHEN 'MOON' THEN 'functional_benefic'$old_lordship$;
  new_lordship_check constant text := $new_lordship$        CASE
          WHEN starts_with(a.source_calculation, 'ga_structural.bphs_functional_class_v2/')
            AND (hs.house1 = 1 OR hs.house2 = 1)
          THEN CASE lg.fact_value_text
            WHEN 'Aries' THEN 'functional_benefic'
            WHEN 'Taurus' THEN 'temporal_malefic'
            WHEN 'Cancer' THEN 'functional_benefic'
            WHEN 'Leo' THEN 'functional_benefic'
            WHEN 'Virgo' THEN 'functional_benefic'
            WHEN 'Aquarius' THEN 'functional_benefic'
            WHEN 'Pisces' THEN 'functional_benefic'
            ELSE 'neutral'
          END
          WHEN lg.fact_value_text = 'Aries' THEN (
          CASE a.fact_subject
            WHEN 'SUN' THEN 'temporal_malefic' WHEN 'MOON' THEN 'functional_benefic'$new_lordship$;
  current_sql text;
  updated_sql text;
BEGIN
  SELECT integrity_check_sql INTO current_sql
    FROM public.asset_registry WHERE asset_id = 'ga_structural' FOR UPDATE;
  IF md5(current_sql) = expected_after THEN
    RETURN;
  END IF;
  IF md5(current_sql) IS DISTINCT FROM expected_before THEN
    RAISE EXCEPTION '1418: expected the integrity check from migration 1414, found %', md5(current_sql);
  END IF;

  updated_sql := replace(replace(current_sql, old_school_check, new_school_check),
                         old_lordship_check, new_lordship_check);
  IF md5(updated_sql) IS DISTINCT FROM expected_after THEN
    RAISE EXCEPTION '1418: school-specific integrity check did not match its expected digest';
  END IF;

  UPDATE public.asset_registry SET integrity_check_sql = updated_sql
    WHERE asset_id = 'ga_structural';
END
$m1418$;
