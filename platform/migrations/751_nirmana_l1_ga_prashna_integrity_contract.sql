-- 751_nirmana_l1_ga_prashna_integrity_contract.sql
--
-- NIRMĀṆA L1 Gaṇita — W3 IMPLEMENT. Discharges F-A14 for ga_prashna: integrity_check_sql was
-- NULL, so the freeze-time detector fell back to count(*) > 0 (§N.8 -- an unearned signal).
--
-- Target: ga_prashna_lagna + ga_prashna_judgment, both DEDICATED tables each already carrying a
-- UNIQUE matching their own natural key -- no distinctness conjunct (D-CND-03 rule 4).
--
-- ga_prashna_judgment is genuinely empty on every built chart today (dormant disposition, R-1 --
-- the facility is live-mounted but no prashna question has ever been asked against a built
-- chart). No conjunct is scoped to it: an untestable conjunct on zero live rows could not be
-- mutation-proved, and shipping one anyway would be exactly the "unearned signal" §N.8 forbids.
-- All three conjuncts below target ga_prashna_lagna, which carries 5 live rows (all on one
-- non-canonical orphaned chart, the same 5 rows the W1 finding already documented).
--
-- Every conjunct below was EXECUTED against live production and MUTATION-PROVED before landing:
-- each was re-run against a corruption injected inside a CTE overlay and shown to return false.
-- Passes clean (integrity_passed = true) on live production today.
--
-- Transaction ownership belongs to platform/scripts/migrate.ts.

UPDATE asset_registry SET integrity_check_sql = $ck$
-- ga_prashna integrity contract (target: ga_prashna_lagna)
SELECT
  -- (a) lagna_rashi must be one of the twelve classical signs.
  NOT EXISTS (
    SELECT 1 FROM ga_prashna_lagna
    WHERE lagna_rashi NOT IN ('Aries','Taurus','Gemini','Cancer','Leo','Virgo',
                              'Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces')
  )
  -- (b) lagna_degree, when stored, must be a genuine degree-within-sign value (0-30).
  AND NOT EXISTS (
    SELECT 1 FROM ga_prashna_lagna
    WHERE lagna_degree IS NOT NULL AND (lagna_degree < 0 OR lagna_degree >= 30)
  )
  -- (c) every ga_prashna_lagna row must reference a real prashna_charts registration -- the
  -- writer's own step 1 (ga_prashna_writer.py: "Check if chart_id is in prashna_charts. If not
  -- -> 0 rows") means a row existing at all implies this lookup succeeded at build time;
  -- re-asserted here as a live referential-integrity check.
  AND NOT EXISTS (
    SELECT 1 FROM ga_prashna_lagna l
    WHERE NOT EXISTS (SELECT 1 FROM prashna_charts pc WHERE pc.chart_id = l.chart_id)
  )
  AS integrity_passed
$ck$
 WHERE asset_id = 'ga_prashna';
