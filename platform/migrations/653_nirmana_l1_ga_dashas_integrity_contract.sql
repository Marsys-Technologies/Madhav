-- 653_nirmana_l1_ga_dashas_integrity_contract.sql
--
-- NIRMĀṆA L1 Gaṇita — W3 IMPLEMENT. Discharges F-A14 for ga_dashas: integrity_check_sql was
-- NULL, so the freeze-time detector fell back to `count(*) > 0` (§N.8 -- an unearned signal;
-- see D-L1-6).
--
-- Standard: D-CND-03 (Conductor ruling on #1723/#1727) -- chart-partitioned, attribution-
-- preserving invariants in preference to whole-table aggregates. C12: no bare count(*)=N
-- equality pin; a count may appear only as a conjunct of something that can fail on corruption
-- a count cannot see.
--
-- Every conjunct below was EXECUTED against live production and MUTATION-PROVED before landing:
-- each was re-run against a corruption injected inside a CTE overlay and shown to return false.
-- One conjunct (upstream-authority) was CAUGHT WRONG by its own mutation test during authoring --
-- an OR-across-fields draft let a correct `sign` match mask a corrupted `house_d1`, so it was
-- rewritten as three independent per-field checks before shipping (§N.8: a conjunct that cannot
-- fail on the corruption it claims to detect is not a detector).
--
-- Passes clean on live production today -- no red conjuncts here, unlike ga_condition/ga_tajaka's
-- rebuild-pending fixes. The MD-tiling conjunct is deliberately scoped to exclude the `mudda`
-- system: mudda's period boundaries are real ephemeris solar-return instants (bisection-converged
-- against the Sun's actual sidereal longitude), not fixed classical arithmetic, and two
-- independently-converged real instants ~365.25 days apart floored to calendar dates are not
-- guaranteed to tile -- measured live, exactly one 1-day non-tile exists (chart 1c826d5a, the
-- 1996 leap-year boundary, across all five ayanamshas) and it is not what this contract exists to
-- catch. The other six systems' classical periods ARE exact fixed arithmetic and tile perfectly
-- today (measured, zero violations).
--
-- Transaction ownership belongs to platform/scripts/migrate.ts.

UPDATE asset_registry SET integrity_check_sql = $ck$
-- ga_dashas integrity contract (target table: chart_dashas)
-- D-CND-03: chart-partitioned / row-wise, attribution-preserving. No bare count pin (C12).
-- No natural-key UNIQUE exists on chart_dashas (PK is a random dasha_row_id surrogate,
-- ga_dashas_writer.py:1025 uses uuid.uuid4() -- no deterministic row identity at all), so
-- conjunct (a) is NOT redundant with any existing index (D-CND-03 rule 4).
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
    GROUP BY chart_id, ayanamsha_id, system_id, level_n, parent_row_id, lord_graha, start_date
    HAVING count(*) > 1
  )
  -- (b) §N.5 upstream authority. lord_natal_house_d1 / lord_natal_sign / lord_natal_nakshatra
  -- are copied verbatim from chart_facts.graha_position for the nine classical-graha lords
  -- (_load_natal_context_inner, :522-544) -- they must never drift from the fact they restate.
  -- Each field checked INDEPENDENTLY against its own chart_facts fact_key row (mutation-caught:
  -- an earlier draft combined all three with OR inside one EXISTS, so a correct `sign` row
  -- masked a corrupted `house_d1` -- three separate conjuncts close that hole).
  -- Deliberately does NOT include lord_natal_dignity_d1 / lord_natal_shadbala_total: those two
  -- columns are the get_dashas.ts serve-time authority's own explicitly-declared exception
  -- (R-43/WP-1.8's comment: re-derived from chart_facts at serve time, the persisted column
  -- never trusted) -- asserting them here would contradict a standing, correct design decision
  -- rather than catch a real corruption.
  AND NOT EXISTS (
    SELECT 1 FROM chart_dashas cd
    WHERE cd.lord_graha = ANY (ARRAY['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Rahu','Ketu'])
      AND cd.lord_natal_house_d1 IS NOT NULL
      AND NOT EXISTS (
        SELECT 1 FROM chart_facts f
        WHERE f.chart_id = cd.chart_id AND f.ayanamsha_id = cd.ayanamsha_id
          AND f.fact_category = 'graha_position' AND f.fact_key = 'house_d1'
          AND f.fact_value_num = cd.lord_natal_house_d1
          AND f.fact_subject = (CASE cd.lord_graha
                WHEN 'Sun' THEN 'SUN' WHEN 'Moon' THEN 'MOON' WHEN 'Mars' THEN 'MAR'
                WHEN 'Mercury' THEN 'MER' WHEN 'Jupiter' THEN 'JUP' WHEN 'Venus' THEN 'VEN'
                WHEN 'Saturn' THEN 'SAT' WHEN 'Rahu' THEN 'RAH_MEAN' WHEN 'Ketu' THEN 'KET_MEAN' END)
      )
  )
  AND NOT EXISTS (
    SELECT 1 FROM chart_dashas cd
    WHERE cd.lord_graha = ANY (ARRAY['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Rahu','Ketu'])
      AND cd.lord_natal_sign IS NOT NULL
      AND NOT EXISTS (
        SELECT 1 FROM chart_facts f
        WHERE f.chart_id = cd.chart_id AND f.ayanamsha_id = cd.ayanamsha_id
          AND f.fact_category = 'graha_position' AND f.fact_key = 'sign'
          AND f.fact_value_text = cd.lord_natal_sign
          AND f.fact_subject = (CASE cd.lord_graha
                WHEN 'Sun' THEN 'SUN' WHEN 'Moon' THEN 'MOON' WHEN 'Mars' THEN 'MAR'
                WHEN 'Mercury' THEN 'MER' WHEN 'Jupiter' THEN 'JUP' WHEN 'Venus' THEN 'VEN'
                WHEN 'Saturn' THEN 'SAT' WHEN 'Rahu' THEN 'RAH_MEAN' WHEN 'Ketu' THEN 'KET_MEAN' END)
      )
  )
  AND NOT EXISTS (
    SELECT 1 FROM chart_dashas cd
    WHERE cd.lord_graha = ANY (ARRAY['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Rahu','Ketu'])
      AND cd.lord_natal_nakshatra IS NOT NULL
      AND NOT EXISTS (
        SELECT 1 FROM chart_facts f
        WHERE f.chart_id = cd.chart_id AND f.ayanamsha_id = cd.ayanamsha_id
          AND f.fact_category = 'graha_position' AND f.fact_key = 'nakshatra'
          AND f.fact_value_text = cd.lord_natal_nakshatra
          AND f.fact_subject = (CASE cd.lord_graha
                WHEN 'Sun' THEN 'SUN' WHEN 'Moon' THEN 'MOON' WHEN 'Mars' THEN 'MAR'
                WHEN 'Mercury' THEN 'MER' WHEN 'Jupiter' THEN 'JUP' WHEN 'Venus' THEN 'VEN'
                WHEN 'Saturn' THEN 'SAT' WHEN 'Rahu' THEN 'RAH_MEAN' WHEN 'Ketu' THEN 'KET_MEAN' END)
      )
  )
  -- (c) MD-level (level_n=1) periods of one (chart, system, ayanamsha) must tile the dasha
  -- cycle without gap or overlap -- one period's end_date is the next one's start_date.
  -- Scoped to system_id <> 'mudda': mudda's MD boundaries are real ephemeris solar-return
  -- instants (_mudda_solar_return_jd, bisection-converged to ~1 minute against the Sun's
  -- actual sidereal longitude, not fixed classical arithmetic), so two independently-converged
  -- real instants ~365.25 days apart floored to calendar dates are not guaranteed to tile --
  -- measured live: exactly one 1-day non-tile on chart 1c826d5a / 1996 (a leap year) across all
  -- five ayanamshas, and zero elsewhere. Excluding mudda avoids attributing a different
  -- system's inherent real-instant/calendar-date rounding to a corruption this conjunct exists
  -- to catch in the other six (vimshottari/yogini/ashtottari/naisargika/kalachakra/chara),
  -- whose classical periods ARE exact fixed arithmetic and tile perfectly today (measured,
  -- zero violations).
  AND NOT EXISTS (
    SELECT 1 FROM (
      SELECT chart_id, system_id, ayanamsha_id, end_date,
             lead(start_date) OVER (PARTITION BY chart_id, system_id, ayanamsha_id ORDER BY start_date) AS nxt
      FROM chart_dashas
      WHERE level_n = 1 AND system_id <> 'mudda'
    ) t
    WHERE t.nxt IS NOT NULL AND t.nxt IS DISTINCT FROM t.end_date
  )
  -- (d) range guard: chart_dashas carries no CHECK on its dates, lord, or system at all, so
  -- nothing but this stops a period from being inverted or a required identity field from
  -- being silently NULL.
  AND NOT EXISTS (
    SELECT 1 FROM chart_dashas
    WHERE start_date IS NULL OR end_date IS NULL OR end_date < start_date
       OR lord_graha IS NULL OR system_id IS NULL OR ayanamsha_id IS NULL
  )
  AS integrity_passed
$ck$
 WHERE asset_id = 'ga_dashas';
