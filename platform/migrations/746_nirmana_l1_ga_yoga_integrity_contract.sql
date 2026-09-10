-- 746_nirmana_l1_ga_yoga_integrity_contract.sql
--
-- NIRMĀṆA L1 Gaṇita — W3 IMPLEMENT. Discharges F-A14 for ga_yoga: integrity_check_sql was
-- NULL, so the freeze-time detector fell back to count(*) > 0 (§N.8 -- an unearned signal).
--
-- Target table: ga_yoga_firings, a DEDICATED table with an existing UNIQUE
-- (chart_id, ayanamsha_id, yoga_canonical_id) -- no distinctness conjunct here (D-CND-03 rule 4).
--
-- Discovered a genuine, previously-untracked defect while authoring this contract, filed as
-- F-A16 (see conjunct (a) below): a formula-version-label fallback invents an unrelated
-- constant whenever the ratified constituent_bala_v1 derivation legitimately returns nothing
-- (Rahu-only constituents, no classical shadbala). Ships RED today, matching the F-C8/F-A15
-- precedent -- a real detector, not a permanently-broken placeholder, verified via a synthetic
-- post-fix overlay that clears cleanly.
--
-- All three conjuncts were EXECUTED against live production and MUTATION-PROVED before landing.
--
-- Transaction ownership belongs to platform/scripts/migrate.ts.

UPDATE asset_registry SET integrity_check_sql = $ck$
-- ga_yoga integrity contract (target table: ga_yoga_firings)
-- UNIQUE (chart_id, ayanamsha_id, yoga_canonical_id) already exactly matches the natural key --
-- no distinctness conjunct (D-CND-03 rule 4).
SELECT
  -- (a) F-A16: strength_formula_version must never be set without a corresponding non-NULL
  -- strength -- the writer's own docstring: "No fabricated strength: strength is NULL unless
  -- resolvable via the single ratified constituent_bala_v1 derivation." GENUINELY RED TODAY on
  -- 4/212 rows (jaimini_karakamsha_rahu, non-canonical chart, 4 ayanamshas): the fallback
  -- `derivation or STRENGTH_FORMULA_VERSION` (ga_yoga_writer.py:2748,3029) invents the UNRELATED
  -- 'yoga_strength_formula_v1' label whenever _compute_constituent_bala_strength returns
  -- (None, None, ...) for a Rahu-only constituent (no classical shadbala, the writer's own
  -- documented exception) -- strength stays honestly NULL but the version LABEL wrongly claims a
  -- formula ran.
  NOT EXISTS (
    SELECT 1 FROM ga_yoga_firings
    WHERE strength_formula_version IS NOT NULL AND strength IS NULL
  )
  -- (b) bhanga_active / bhanga_na_reason mutual exclusivity: the writer's own docstring:
  -- "bhanga_active is NULL-with-a-documented-reason (bhanga_na_reason) wherever this writer
  -- implements no classical cancellation rule". Clean live (0/212).
  AND NOT EXISTS (
    SELECT 1 FROM ga_yoga_firings
    WHERE (bhanga_active IS NULL) <> (bhanga_na_reason IS NOT NULL)
  )
  -- (c) is_partial honesty: a row claiming partial formation must carry the percentage that
  -- makes the claim checkable -- an honest partial_formation_pct is what distinguishes
  -- is_partial from a bare, unactionable boolean.
  AND NOT EXISTS (
    SELECT 1 FROM ga_yoga_firings
    WHERE is_partial = true AND partial_formation_pct IS NULL
  )
  AS integrity_passed
$ck$
 WHERE asset_id = 'ga_yoga';
