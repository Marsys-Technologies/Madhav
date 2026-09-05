-- 658_nirmana_l1_ga_condition_varga_composite_integrity_contract.sql
--
-- NIRMĀṆA L1 Gaṇita — W3 IMPLEMENT. Discharges F-A14 for ga_condition: integrity_check_sql was
-- NULL, so the freeze-time detector fell back to count(*) > 0 (§N.8 -- an unearned signal).
--
-- Target table: ga_condition_composite, a DEDICATED table (not shared chart_facts) with an
-- existing UNIQUE (chart_id, ayanamsha_id, graha) -- no distinctness conjunct appears here
-- (D-CND-03 rule 4).
--
-- ONE CONJUNCT RETURNS FALSE TODAY, deliberately, on ALL 135 rows -- this is F-C8
-- (L1_W1_ANALYSIS_BATCH_C.md): varga_dignity_composite is NULL everywhere in production right
-- now. The fix (PR #1853, migration content lives on that branch, not yet merged -- stuck for
-- several cycles on an unrelated L2 pin-drift issue, #1852) is CONFIRMED to exist and CONFIRMED
-- correct: diffed origin/main against #1853's branch directly rather than trusting memory of
-- having "already fixed this" -- _compute_varga_composite's dignity-label fallback currently
-- looks up the RAW chart_divisionals label ("Enemy", Title-Case) directly in DIGNITY_SCORES
-- (whose keys are snake_case, "enemy_sign") and always misses, so total_w stays 0 and the
-- function always returns None. #1853 fixes this by routing the label through
-- _DIVISIONAL_DIGNITY_NORMALIZE first (this file's own existing chart_divisionals-label map,
-- already used for the same rows' deeptaadi avastha) -- the SAME map F-A12 (ga_dashas, PR #1926)
-- used for an analogous bug. Conjunct (a) below re-derives the CORRECT (post-#1853) formula
-- directly in SQL and compares it to what's actually stored -- it will go green automatically
-- once #1853 merges and ga_condition rebuilds, with no further action needed here. Verified this
-- SQL re-derivation both ways: against today's live data (135/135 mismatches, matching the
-- known bug) and against a synthetic "already fixed" overlay (0/135 mismatches) -- the conjunct
-- is a real detector of correctness, not merely a permanent-red placeholder.
--
-- Every conjunct was EXECUTED against live production and MUTATION-PROVED before landing.
--
-- Transaction ownership belongs to platform/scripts/migrate.ts.

UPDATE asset_registry SET integrity_check_sql = $ck$
-- ga_condition integrity contract (target table: ga_condition_composite).
-- D-CND-03: chart-partitioned / row-wise, attribution-preserving. No bare count pin (C12).
-- Distinctness already DB-enforced (ga_condition_composite_unique); not re-asserted (rule 4).
SELECT
  -- (a) varga_dignity_composite must equal the weighted average of per-varga dignity scores in
  -- varga_dignity_spread, re-derived here using the SAME weight table
  -- (ga_condition_writer.py's _VARGA_WEIGHTS) and the SAME dignity-label normalization
  -- (_DIVISIONAL_DIGNITY_NORMALIZE -> DIGNITY_SCORES) the corrected writer uses.
  -- RED TODAY (F-C8, see this migration's header) -- a true positive, not suppressed.
  NOT EXISTS (
    SELECT 1 FROM ga_condition_composite gc
    WHERE gc.varga_dignity_spread IS NOT NULL
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
  AS integrity_passed
$ck$
 WHERE asset_id = 'ga_condition';
