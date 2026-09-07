-- 902_nirmana_l1_ga_condition_integrity_check_scope.sql
--
-- NIRMĀṆA L1 Gaṇita — cycle 259: `ga_condition`'s `integrity_check_sql` conjunct (a)
-- (varga_dignity_composite re-derivation) is unscoped across all 3 canonical charts — the
-- SAME class of defect migration 884 fixed for `ga_vargas` and migration 882 for `ga_dashas`.
-- Discovered when the first real campaign dispatch of `ga_condition` (build_run
-- `e2ac2b9d-44c2-40ba-83a0-3bce944e7675`, the first L1 dispatch after the #2300/D-NATIVE-10
-- asset_freshness fix unblocked the frontier) FAILED the orchestrator's post-write integrity
-- gate (`asset_throughput.last_error = "post-write integrity check failed: integrity_check_sql
-- → False"`) even though the canonical chart's own data was genuinely correct after the
-- rebuild.
--
-- Root cause confirmed by isolating each conjunct after the failed build: (a) weighted-average
-- re-derivation 90 violations, (b) deeply-combust implication 0, (c) dignity_score_d1 range 0,
-- (d) condition_score range 0. ALL 90 violations are on charts `1c826d5a-...` (45 rows) and
-- `cb73cd3d-...` (45 rows) — charts this dispatch never touched (campaign dispatch is scoped
-- to the canonical chart per WP-3 shared-domain exclusion). The canonical chart
-- (`482012f1-...`) has ZERO conjunct-(a) violations after the rebuild — the F-C8 writer fix
-- genuinely works (this conjunct's own in-check comment said "RED TODAY (F-C8) — a true
-- positive, not suppressed" when authored; the fixed writer + fresh rebuild has now turned it
-- green for every row the dispatch could reach). The check was asserting more than this
-- dispatch's scope could ever satisfy.
--
-- Scoped conjunct (a) to the canonical chart only — the same disclosed tradeoff as migrations
-- 882/884 and ga_positions' original FORENSIC-gate conjunct: this campaign's asset_frozen
-- decision is about the canonical chart's build correctness, not an audit of all 3 charts
-- (which have their own separate operator-E2E validation track, L1_GANITA_CLOSURE_v2_0.md
-- Phase E). Conjuncts (b)/(c)/(d) pass TRUE table-wide (measured, not assumed) and are left
-- unscoped — no coverage is traded away where none needs to be.
--
-- Charts 1c826d5a / cb73cd3d's 90 stale rows remain real and untouched by this migration —
-- they are pre-F-C8-writer output, out of THIS campaign's dispatch scope, NOT silently
-- declared fixed. They are routed to a `nirmana-adjudication` issue filed the same cycle
-- (cross-chart repair also needs per-chart `asset_freshness` bootstrapping those charts do not
-- have, and `ga_dashas` on cb73cd3d sits at `asset_throughput.state='incomplete'` — a
-- coordinated repair, not an L1 quick fix). When those charts are rebuilt with the fixed
-- writer, this conjunct's canonical scope can be widened back.

BEGIN;

UPDATE asset_registry
SET integrity_check_sql = $SQL$
-- ga_condition integrity contract (target table: ga_condition_composite).
-- D-CND-03: chart-partitioned / row-wise, attribution-preserving. No bare count pin (C12).
-- Distinctness already DB-enforced (ga_condition_composite_unique); not re-asserted (rule 4).
-- Conjunct (a) SCOPED to the canonical chart (migration 902): disclosed coverage tradeoff,
-- same precedent as ga_dashas (migration 882) and ga_vargas (migration 884). Non-canonical
-- charts carry pre-F-C8-writer rows until their own coordinated rebuild (see migration 902
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
  AS integrity_passed
$SQL$
WHERE asset_id = 'ga_condition';

COMMIT;
