
-- ga_condition integrity contract (target table: ga_condition_composite).
-- D-CND-03: chart-partitioned / row-wise, attribution-preserving. No bare count pin (C12).
-- Distinctness already DB-enforced (ga_condition_composite_unique); not re-asserted (rule 4).
-- Conjunct (a) SCOPED to the canonical chart (migration 899): disclosed coverage tradeoff,
-- same precedent as ga_dashas (migration 882) and ga_vargas (migration 884). Non-canonical
-- charts carry pre-F-C8-writer rows until their own coordinated rebuild (see migration 899
-- header); conjuncts (b)/(c)/(d) remain table-wide.
SELECT
  -- (a) varga_dignity_composite must equal the weighted average of per-varga dignity scores in
  -- varga_dignity_spread, re-derived here using the SAME weight table
  -- (ga_condition_writer.py's _VARGA_WEIGHTS) and the SAME dignity-label normalization
  -- (_DIVISIONAL_DIGNITY_NORMALIZE -> DIGNITY_SCORES) the corrected writer uses.
  -- GREEN for the canonical chart since the first post-F-C8 rebuild (build_run e2ac2b9d, 2026-09-07).
  NOT EXISTS (
    SELECT 1 FROM ga_condition_composite gc
    WHERE gc.chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
      AND gc.varga_dignity_spread IS NOT NULL
      AND (
        SELECT round(sum(weight * score) / NULLIF(sum(weight) FILTER (WHERE score IS NOT NULL), 0), 6)
        FROM (
          SELECT
            CASE spread.key
              WHEN 'D1' THEN 3.5 WHEN 'D9' THEN 3.0 WHEN 'D2' THEN 0.5 WHEN 'D3' THEN 0.5
              WHEN 'D4' THEN 0.5 WHEN 'D7' THEN 0.5 WHEN 'D10' THEN 1.5 WHEN 'D12' THEN 0.5
              WHEN 'D16' THEN 0.5 WHEN 'D20' THEN 0.5 WHEN 'D24' THEN 0.5 WHEN 'D27' THEN 0.5
              WHEN 'D30' THEN 0.5 WHEN 'D40' THEN 0.5 WHEN 'D45' THEN 0.5 WHEN 'D60' THEN 1.0
              ELSE 0.25
            END AS weight,
            CASE spread.value->>'dignity'
              WHEN 'Exalted' THEN 1.0 WHEN 'Moolatrikona' THEN 0.9 WHEN 'Own' THEN 0.8
              WHEN 'Friend' THEN 0.6 WHEN 'Neutral' THEN 0.5 WHEN 'Enemy' THEN 0.3
              WHEN 'Debilitated' THEN 0.0 ELSE NULL
            END AS score
          FROM jsonb_each(gc.varga_dignity_spread) AS spread
        ) per_varga
        WHERE score IS NOT NULL
      ) IS DISTINCT FROM gc.varga_dignity_composite
  )
  -- (b) is_deeply_combust implies is_combust -- a graha cannot be "deeply" combust without
  -- being combust at all. Checked the writer's own combustion-penalty comment
  -- (compute_condition_score_v1: "0.15 for combust, 0.25 for deeply combust") before asserting
  -- this: the two are graded severities of the SAME condition, not independent flags.
  AND NOT EXISTS (
    SELECT 1 FROM ga_condition_composite WHERE is_deeply_combust AND NOT is_combust
  )
  -- (c) range guard, re-derived from the writer's own documented ranges rather than the
  -- currently-observed min/max (which could under-cover a valid future value): dignity_score_d1
  -- is a direct DIGNITY_SCORES lookup (0.0-1.0 by construction); condition_score is documented
  -- "0.0-1.0" in compute_condition_score_v1's own docstring.
  AND NOT EXISTS (
    SELECT 1 FROM ga_condition_composite
    WHERE dignity_score_d1 IS NOT NULL AND (dignity_score_d1 < 0 OR dignity_score_d1 > 1)
  )
  AND NOT EXISTS (
    SELECT 1 FROM ga_condition_composite
    WHERE condition_score IS NOT NULL AND (condition_score < 0 OR condition_score > 1)
  )
  -- (e) X2 / I-29: a composite row that used the D1 fallback (breakdown.varga_fallback_used) on a
  -- chart that HAS divisional rows for that (chart, ayanamsha, graha) is a failure. Same claim the
  -- writer's assert_fallback_legitimate enforces at write time, read here from the stored rows.
  AND NOT EXISTS (
    SELECT 1 FROM ga_condition_composite gc
    WHERE gc.chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
      AND COALESCE((gc.condition_score_breakdown->>'varga_fallback_used') = 'true', false)
      AND EXISTS (
        SELECT 1 FROM chart_divisionals cd
        WHERE cd.chart_id = gc.chart_id AND cd.ayanamsha_id = gc.ayanamsha_id AND cd.graha = gc.graha
          AND cd.fact_category IN ('varga_position', 'varga_dignity')
      )
  )
  -- (f) the detector must be able to SEE chart_divisionals: if row-level security applies to the
  -- checking role and the table reads empty, conjunct (e) would pass vacuously (the 2026-09-18
  -- incident class), so the whole check fails closed instead.
  AND (
    NOT row_security_active('public.chart_divisionals')
    OR EXISTS (SELECT 1 FROM chart_divisionals LIMIT 1)
  )
  AS integrity_passed
