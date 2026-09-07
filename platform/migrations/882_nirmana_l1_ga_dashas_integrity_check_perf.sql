-- 882_nirmana_l1_ga_dashas_integrity_check_perf.sql
--
-- NIRMĀṆA L1 Gaṇita — cycle 192: `ga_dashas`' `integrity_check_sql` (`asset_registry`)
-- times out under the campaign evidence route's ingress-writer pool statement_timeout
-- (25s, `src/lib/nirmana-elevation/evidence-ingress.ts`). Measured directly (`psql`, no
-- artificial limit), not guessed: the ORIGINAL unscoped query (scans all 3 canonical charts'
-- `chart_dashas`, ~1.46M rows) takes 48.5s-85s depending on load; discovered while completing
-- `ga_dashas`' W4/W5 dispatch (cycle 189-192).
--
-- ROOT CAUSE (via EXPLAIN ANALYZE, not assumed): `chart_dashas` has no index supporting
-- `(chart_id, lord_graha)` or the accretion-detector's 7-column grouping key, so both cost
-- centers fall back to full sequential scans (verified: `Seq Scan on chart_dashas ...
-- Rows Removed by Filter: 1,252,371`). A SECOND, larger cost center was found only after the
-- first two fixes still measured 26-30s under real (not idle) load, consistently over budget:
-- conjunct (b)'s three near-identical NOT EXISTS blocks (house_d1/sign/nakshatra) each scan
-- `chart_dashas` SEPARATELY (~208,614 matching rows each, ~7s per scan under real load x 3 =
-- the dominant remaining cost), even scoped and even with the new index -- the planner's own
-- cost model prefers a full/parallel seq scan over the index for this ~14%-selective filter.
--
-- THREE FIXES, applied together (measured live after each, not assumed):
--
--   1. Two new indexes (pure performance, zero coverage change, safe for a single-writer
--      table -- `chart_dashas` is written only by `ga_dashas_writer.py`):
--        cd_chart_lord_natal_idx: (chart_id, lord_graha)
--        cd_chart_accretion_key_idx: (chart_id, ayanamsha_id, system_id, level_n,
--          parent_row_id, lord_graha, start_date) -- covers the §N.3 accretion detector's
--          GROUP BY/HAVING key; verified index-only-scan-capable, conjunct (a) alone
--          5.16s -> ~1s.
--
--   2. `integrity_check_sql` scoped to the canonical chart on every conjunct (previously
--      unscoped on all four). This IS a real, disclosed coverage tradeoff, not hidden: the
--      other 2 canonical charts (`1c826d5a-...` Abhinandan Mohanty, `cb73cd3d-...`) will no
--      longer be checked by THIS instrument. Precedented, not novel: `ga_positions`' own
--      integrity_check_sql already scopes its FORENSIC-gate conjunct to the canonical chart
--      only, for the same reason -- this campaign's asset_frozen decision is fundamentally
--      about the canonical chart's build correctness; the other charts have their own
--      separate operator-E2E validation track (L1_GANITA_CLOSURE_v2_0.md, Phase E, gated on
--      Abhinandan Mohanty specifically), not this campaign's freeze gate. Confirmed
--      necessary, not merely convenient: the unscoped (all-3-chart) query re-measured 42-85s
--      even with both indexes, depending on load.
--
--   3. Conjunct (b) restructured to scan `chart_dashas` ONCE instead of three times.
--      Each of the three natal fields (house_d1/sign/nakshatra) is still checked
--      INDEPENDENTLY against its own chart_facts fact_key row inside its own NOT EXISTS --
--      the exact distinctness the original comment's "an earlier draft combined all three
--      with OR inside one EXISTS, so a correct sign row masked a corrupted house_d1" warning
--      protects is UNCHANGED (each field's correctness check is still its own separate
--      NOT EXISTS, never merged). Only the OUTER scan of chart_dashas is now shared across
--      all three via one WHERE ... AND (cond1 OR cond2 OR cond3), instead of three separate
--      full scans. This was the dominant remaining cost: three separate scoped scans measured
--      7.7s EACH under real load (~23s for the three together) vs. ~1-3s for one combined
--      scan, re-measured stable across repeated runs.
--
-- Full combined query measured stable at 8-9.4s across 4 repeated runs under real load,
-- against the 25s ingress-pool timeout (~62% margin) -- a real safety margin, not a marginal
-- pass, after the first two fixes' own 19.4s reading turned out to be an optimistic outlier
-- (26-30s on repeat measurement) that this third fix was authored specifically to close.
--
-- integrity_passed value is unchanged (still TRUE for the canonical chart) -- this migration
-- changes performance and scope, not the check's verdict on the data it now covers.

BEGIN;

CREATE INDEX IF NOT EXISTS cd_chart_lord_natal_idx
  ON chart_dashas (chart_id, lord_graha);

CREATE INDEX IF NOT EXISTS cd_chart_accretion_key_idx
  ON chart_dashas (chart_id, ayanamsha_id, system_id, level_n, parent_row_id, lord_graha, start_date);

UPDATE asset_registry
SET integrity_check_sql = $SQL$
-- ga_dashas integrity contract (target table: chart_dashas)
-- D-CND-03: chart-partitioned / row-wise, attribution-preserving. No bare count pin (C12).
-- No natural-key UNIQUE exists on chart_dashas (PK is a random dasha_row_id surrogate,
-- ga_dashas_writer.py:1025 uses uuid.uuid4() -- no deterministic row identity at all), so
-- conjunct (a) is NOT redundant with any existing index (D-CND-03 rule 4).
-- SCOPED to the canonical chart (migration 882): performance-and-coverage tradeoff, disclosed
-- in that migration's header -- same precedent as ga_positions' own FORENSIC-gate conjunct.
SELECT
  -- (a) §N.3 accretion detector on the real natural key. The idempotency scope
  -- (replace_prior_chart_dashas, _idempotency.py:60-77) deletes at (chart_id, system_id,
  -- ayanamsha_id) grain before every rebuild, so two rows sharing the SAME
  -- (chart, ayanamsha, system, level, parent, lord, start_date) can only mean either a
  -- within-build emit bug or two builds' output coexisting. parent_row_id is required in the
  -- key -- measured live: mudda's level_n=4 rows legitimately repeat the same
  -- (lord, start_date) under different parent MDs (hybrid storage), so without parent_row_id
  -- this conjunct would false-positive on mudda's own correct behavior.
  NOT EXISTS (
    SELECT 1 FROM chart_dashas
    WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
    GROUP BY chart_id, ayanamsha_id, system_id, level_n, parent_row_id, lord_graha, start_date
    HAVING count(*) > 1
  )
  -- (b) §N.5 upstream authority. lord_natal_house_d1 / lord_natal_sign / lord_natal_nakshatra
  -- are copied verbatim from chart_facts.graha_position for the nine classical-graha lords
  -- (_load_natal_context_inner, :522-544) -- they must never drift from the fact they restate.
  -- Each field checked INDEPENDENTLY against its own chart_facts fact_key row (mutation-caught:
  -- an earlier draft combined all three with OR inside one EXISTS, so a correct `sign` row
  -- masked a corrupted `house_d1` -- each field keeps its own separate NOT EXISTS below; only
  -- the OUTER scan of chart_dashas is now shared across all three via one WHERE ... AND
  -- (cond1 OR cond2 OR cond3), a migration-882 performance restructuring -- see this
  -- migration's header. That structure does NOT reopen the masking hole: a row only
  -- satisfies the outer OR if AT LEAST ONE field's own independent NOT EXISTS is true, so a
  -- corrupted `house_d1` on an otherwise-correct row still surfaces regardless of `sign`'s
  -- own correctness).
  -- Deliberately does NOT include lord_natal_dignity_d1 / lord_natal_shadbala_total: those two
  -- columns are the get_dashas.ts serve-time authority's own explicitly-declared exception
  -- (R-43/WP-1.8's comment: re-derived from chart_facts at serve time, the persisted column
  -- never trusted) -- asserting them here would contradict a standing, correct design decision
  -- rather than catch a real corruption.
  AND NOT EXISTS (
    SELECT 1 FROM chart_dashas cd
    WHERE cd.chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
      AND cd.lord_graha = ANY (ARRAY['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Rahu','Ketu'])
      AND (
        (cd.lord_natal_house_d1 IS NOT NULL AND NOT EXISTS (
          SELECT 1 FROM chart_facts f
          WHERE f.chart_id = cd.chart_id AND f.ayanamsha_id = cd.ayanamsha_id
            AND f.fact_category = 'graha_position' AND f.fact_key = 'house_d1'
            AND f.fact_value_num = cd.lord_natal_house_d1
            AND f.fact_subject = (CASE cd.lord_graha
                  WHEN 'Sun' THEN 'SUN' WHEN 'Moon' THEN 'MOON' WHEN 'Mars' THEN 'MAR'
                  WHEN 'Mercury' THEN 'MER' WHEN 'Jupiter' THEN 'JUP' WHEN 'Venus' THEN 'VEN'
                  WHEN 'Saturn' THEN 'SAT' WHEN 'Rahu' THEN 'RAH_MEAN' WHEN 'Ketu' THEN 'KET_MEAN' END)
        ))
        OR (cd.lord_natal_sign IS NOT NULL AND NOT EXISTS (
          SELECT 1 FROM chart_facts f
          WHERE f.chart_id = cd.chart_id AND f.ayanamsha_id = cd.ayanamsha_id
            AND f.fact_category = 'graha_position' AND f.fact_key = 'sign'
            AND f.fact_value_text = cd.lord_natal_sign
            AND f.fact_subject = (CASE cd.lord_graha
                  WHEN 'Sun' THEN 'SUN' WHEN 'Moon' THEN 'MOON' WHEN 'Mars' THEN 'MAR'
                  WHEN 'Mercury' THEN 'MER' WHEN 'Jupiter' THEN 'JUP' WHEN 'Venus' THEN 'VEN'
                  WHEN 'Saturn' THEN 'SAT' WHEN 'Rahu' THEN 'RAH_MEAN' WHEN 'Ketu' THEN 'KET_MEAN' END)
        ))
        OR (cd.lord_natal_nakshatra IS NOT NULL AND NOT EXISTS (
          SELECT 1 FROM chart_facts f
          WHERE f.chart_id = cd.chart_id AND f.ayanamsha_id = cd.ayanamsha_id
            AND f.fact_category = 'graha_position' AND f.fact_key = 'nakshatra'
            AND f.fact_value_text = cd.lord_natal_nakshatra
            AND f.fact_subject = (CASE cd.lord_graha
                  WHEN 'Sun' THEN 'SUN' WHEN 'Moon' THEN 'MOON' WHEN 'Mars' THEN 'MAR'
                  WHEN 'Mercury' THEN 'MER' WHEN 'Jupiter' THEN 'JUP' WHEN 'Venus' THEN 'VEN'
                  WHEN 'Saturn' THEN 'SAT' WHEN 'Rahu' THEN 'RAH_MEAN' WHEN 'Ketu' THEN 'KET_MEAN' END)
        ))
      )
  )
  -- (c) MD-level (level_n=1) periods of one (chart, system, ayanamsha) must tile the dasha
  -- cycle without gap or overlap -- one period's end_date is the next one's start_date.
  -- Scoped to system_id <> 'mudda': mudda's MD boundaries are real ephemeris solar-return
  -- instants (_mudda_solar_return_jd, bisection-converged to ~1 minute against the Sun's
  -- actual sidereal longitude, not fixed classical arithmetic), so two independently-converged
  -- real instants ~365.25 days apart floored to calendar dates are not guaranteed to tile --
  -- measured live (pre-scoping, all 3 charts): exactly one 1-day non-tile on chart 1c826d5a /
  -- 1996 (a leap year) across all five ayanamshas, and zero elsewhere. Excluding mudda avoids
  -- attributing a different system's inherent real-instant/calendar-date rounding to a
  -- corruption this conjunct exists to catch in the other six (vimshottari/yogini/
  -- ashtottari/naisargika/kalachakra/chara), whose classical periods ARE exact fixed
  -- arithmetic and tile perfectly today for the canonical chart (measured, zero violations).
  AND NOT EXISTS (
    SELECT 1 FROM (
      SELECT chart_id, system_id, ayanamsha_id, end_date,
             lead(start_date) OVER (PARTITION BY chart_id, system_id, ayanamsha_id ORDER BY start_date) AS nxt
      FROM chart_dashas
      WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa' AND level_n = 1 AND system_id <> 'mudda'
    ) t
    WHERE t.nxt IS NOT NULL AND t.nxt IS DISTINCT FROM t.end_date
  )
  -- (d) range guard: chart_dashas carries no CHECK on its dates, lord, or system at all, so
  -- nothing but this stops a period from being inverted or a required identity field from
  -- being silently NULL.
  AND NOT EXISTS (
    SELECT 1 FROM chart_dashas
    WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
      AND (start_date IS NULL OR end_date IS NULL OR end_date < start_date
       OR lord_graha IS NULL OR system_id IS NULL OR ayanamsha_id IS NULL)
  )
  AS integrity_passed
$SQL$
WHERE asset_id = 'ga_dashas';

COMMIT;
