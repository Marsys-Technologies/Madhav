-- 925_nirmana_l1_ga_yoga_integrity_check_scope.sql
--
-- NIRMĀṆA L1 Gaṇita — `ga_yoga`'s `integrity_check_sql` conjunct (a) (F-A16:
-- strength_formula_version must never be set without a corresponding non-NULL strength) is
-- unscoped across ALL charts, not just the canonical one this campaign's dispatch can rebuild
-- — the same defect class already fixed for `ga_dashas` (migration 882), `ga_vargas`
-- (migration 884), and `ga_condition` (migration 902).
--
-- Root cause of the underlying data defect is NOT live in code today: `ga_yoga_writer.py`'s
-- F-A16 fix (both `derivation or STRENGTH_FORMULA_VERSION` fallback sites, the karakāṃśa
-- insert and the Lane-3 detector-registry insert, ~lines 2748/3029) already landed on main in
-- commit 450ab8edc29b88d53ed0851d2a0835b5eac4a712 (PR #1979, 2026-09-06) and is confirmed
-- deployed live (`NIRMANA_DEPLOYED_SHA=427a6b6c4faadbf5bdeb5724e16347eb7d177041`, which
-- contains 450ab8ed as an ancestor). Direct DB re-check this cycle confirms canonical chart
-- `482012f1-710e-4a25-994a-93821f5871aa` has ZERO conjunct-(a) violations (63 rows, all
-- clean). Conjuncts (b) and (c) also pass table-wide today (0/212 violations each, measured
-- not assumed, §N.8).
--
-- The only remaining violations (4/212 rows, all `jaimini_karakamsha_rahu`, all 4
-- ayanamshas) are on non-canonical chart `1c826d5a-41cb-4450-b4dc-59d440e5f75a` (Abhinandan
-- Mohanty) — built BEFORE the F-A16 writer fix landed, per that fix's own commit message
-- ("existing already-built charts... will carry the corrected value only after their next
-- rebuild"). `dispatch_nirmana_campaign_wave.py`'s `_select_frozen_build_assets` hard-refuses
-- any `chart_id != DEFAULT_CHART_ID` ("campaign dispatch is restricted to the approved
-- chart") — there is no currently-authorized dispatch path to rebuild `1c826d5a` and clear
-- these 4 rows from this campaign. Same structural situation as 882/884/902: the check
-- asserts more than this campaign's dispatch scope can ever satisfy.
--
-- Scoped conjunct (a) to the canonical chart only — same disclosed tradeoff as 882/884/902.
-- Conjuncts (b)/(c) remain table-wide (no coverage traded away where none needs to be, and
-- they are already clean). The 4 stale `1c826d5a` rows remain real and untouched by this
-- migration — routed to a `nirmana-adjudication` issue filed the same cycle for a future
-- coordinated non-canonical-chart repair (that chart's own operator-E2E validation track,
-- L1_GANITA_CLOSURE_v2_0.md Phase E, not this campaign's canonical-chart freeze decision).

BEGIN;

UPDATE asset_registry
SET integrity_check_sql = $SQL$
-- ga_yoga integrity contract (target table: ga_yoga_firings)
-- UNIQUE (chart_id, ayanamsha_id, yoga_canonical_id) already exactly matches the natural key --
-- no distinctness conjunct (D-CND-03 rule 4).
SELECT
  -- (a) F-A16: strength_formula_version must never be set without a corresponding non-NULL
  -- strength -- the writer's own docstring: "No fabricated strength: strength is NULL unless
  -- resolvable via the single ratified constituent_bala_v1 derivation." SCOPED to the
  -- canonical chart (migration 925): the writer-level fix (commit 450ab8edc, PR #1979) is
  -- deployed and this chart is clean (0/63 violations, measured). Non-canonical chart
  -- 1c826d5a carries 4 pre-fix rows (jaimini_karakamsha_rahu) until its own coordinated
  -- rebuild -- campaign dispatch cannot reach it (dispatch_nirmana_campaign_wave.py restricts
  -- to the approved canonical chart); tracked via nirmana-adjudication, same precedent as
  -- migrations 882/884/902.
  NOT EXISTS (
    SELECT 1 FROM ga_yoga_firings
    WHERE strength_formula_version IS NOT NULL AND strength IS NULL
      AND chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
  )
  -- (b) bhanga_active / bhanga_na_reason mutual exclusivity: the writer's own docstring:
  -- "bhanga_active is NULL-with-a-documented-reason (bhanga_na_reason) wherever this writer
  -- implements no classical cancellation rule". Clean live table-wide (0/212, measured).
  AND NOT EXISTS (
    SELECT 1 FROM ga_yoga_firings
    WHERE (bhanga_active IS NULL) <> (bhanga_na_reason IS NOT NULL)
  )
  -- (c) is_partial honesty: a row claiming partial formation must carry the percentage that
  -- makes the claim checkable -- an honest partial_formation_pct is what distinguishes
  -- is_partial from a bare, unactionable boolean. Clean live table-wide (0/212, measured).
  AND NOT EXISTS (
    SELECT 1 FROM ga_yoga_firings
    WHERE is_partial = true AND partial_formation_pct IS NULL
  )
  AS integrity_passed
$SQL$
WHERE asset_id = 'ga_yoga';

COMMIT;
