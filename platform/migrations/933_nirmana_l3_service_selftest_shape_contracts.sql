-- 933_nirmana_l3_service_selftest_shape_contracts.sql
--
-- NIRMANA v2.5 -- L3 (Kala). Transaction ownership belongs to
-- platform/scripts/migrate.ts.
--
-- #2455 priority-3 finding A (RESOLUTION v4 item 3 / Conductor ruling, issue #2455
-- comment 2026-09-08T18:09:43Z, "AUTHORIZED, proceed now"): the w299 sweep of all
-- 46 ka_*/ph_*/mi_* registry rows found four assets with integrity_check_sql IS
-- NULL and no count_sql pin: ka_dasha_kala, ka_graha_sancara, ka_muhurta_seva,
-- ka_tulana. This migration closes all four.
--
-- All four are TRUE service assets (asset_kind='service') in the narrowest sense
-- seen so far in this contract series: unlike bo_laksana_rerank (932, UPDATE-only
-- but still enriching a real domain table) or the mi_abhilekha/mi_seva service
-- contracts (which own mimamsa_journal/mimamsa_preferences rows), these four own
-- NO domain table at all. Confirmed by reading every writer
-- (ka_dasha_kala/writer.py, ka_graha_sancara.py, ka_muhurta_seva/writer.py,
-- ka_tulana/writer.py): each runs a self-test against derived state (chart_dashas,
-- ephemeris, birth panchanga, synthetic rank inputs) and writes exactly THREE
-- columns back onto its own asset_registry row -- service_health,
-- last_selftest_at, selftest_detail -- always together in one UPDATE. No rows in
-- any chart-scoped table are inserted, updated, or deleted. asset_registry itself
-- carries no chart_id column, so the asset's own row is already chart-agnostic by
-- construction -- no chart literal is needed or wanted here.
--
-- Detector shape (w298 lesson: UPDATE-only assets need shape-only detection, not
-- accretion/coverage/fact_key clauses -- and this narrows even that: there is no
-- owned table to size or key at all):
--   * NO accretion clause -- nothing is ever inserted.
--   * NO coverage/count pin -- there is exactly one row per asset_id, forever.
--   * NO fact_key clause -- no facts are produced.
-- What IS honestly gate-able is the STRUCTURAL WELL-FORMEDNESS of the one mark
-- each writer leaves on itself: the reported health must be a value that asset's
-- OWN code can actually produce (read from source, not assumed uniform -- see
-- below), the timestamp must be a real past instant, and the detail payload must
-- be a genuine non-empty JSON object rather than a null/truncated/hand-edited
-- placeholder. This mirrors 932's clauses 1-4 (hook payload key set / closed set
-- / value band / closed set): none of those assert the self-test's VERDICT
-- either, only the mark's shape. Every clause below was mutation-tested to a
-- reachable false (N.8): NULL health, an out-of-set health literal, NULL or
-- future last_selftest_at, NULL/array-typed/empty-object selftest_detail --
-- each verified false in isolation before this migration was posted.
--
-- Closed health sets are NOT fleet-uniform and are read from each writer's own
-- source, not assumed:
--   ka_dasha_kala / ka_tulana        -> health = 'healthy' if ok else 'degraded'
--   ka_graha_sancara / ka_muhurta_seva -> health = 'healthy' if ok else 'unhealthy'
-- Using a shared closed set across all four would either falsely accept a value
-- that asset's code can never write, or falsely reject a value it legitimately
-- can -- both violate N.7 item 3 (no wrapper-local constant may shadow what the
-- source actually does).
--
-- Deliberately NOT gated: whether service_health = 'healthy'. All four writers
-- already raise RuntimeError on a failing self-test (N.8 fix, see
-- ka_graha_sancara.py/ka_muhurta_seva/writer.py/ka_dasha_kala/writer.py/
-- ka_tulana/writer.py inline comments), which routes through mark_asset_error --
-- a contract requiring 'healthy' would duplicate that gate one layer up and,
-- worse, would immediately register RED on ka_graha_sancara, whose live row
-- (service_health='unhealthy', last_selftest_at=2026-08-02, predating the N.8
-- fix, state='lit') is a pre-existing anomaly this lane is not authoring a fix
-- for -- filed as a separate finding below (routing decision, not a contract
-- job; same "diagnose, do not silently paper over, do not fix out-of-lane"
-- discipline as the w299 red-contract findings).
--
-- FINDING (for Conductor routing, not actioned here): ka_graha_sancara's
-- asset_throughput row shows state='lit' with chart_id NULL while
-- service_health='unhealthy' from a self-test dated 2026-08-02 -- five weeks
-- stale relative to this migration and predating the mark_asset_error fix
-- documented inline in ka_graha_sancara.py. Because that fix now raises on any
-- non-healthy self-test, a fresh rebuild would either re-lit it healthy or
-- correctly error it; nothing here forces that rebuild. Out of integrity-
-- contract lane scope -- filed for whichever lane owns L3 service rebuilds.
--
-- Post-apply verification (N.4 -- never trust a silent no-op): expect
-- UPDATE 1 x4, then
--   SELECT asset_id, integrity_check_sql IS NOT NULL FROM asset_registry
--    WHERE asset_id IN ('ka_dasha_kala','ka_graha_sancara','ka_muhurta_seva',
--                        'ka_tulana')  -- expect all t


-- ── ka_dasha_kala ─────────────────────────────────────────────────────────────
UPDATE asset_registry
   SET integrity_check_sql = $INTEGRITY$
SELECT
  service_health IS NOT NULL
  AND service_health IN ('healthy', 'degraded')
  AND last_selftest_at IS NOT NULL
  AND last_selftest_at <= now()
  AND selftest_detail IS NOT NULL
  AND jsonb_typeof(selftest_detail) = 'object'
  AND selftest_detail <> '{}'::jsonb
  AS integrity_passed
FROM asset_registry
WHERE asset_id = 'ka_dasha_kala'
$INTEGRITY$
 WHERE asset_id = 'ka_dasha_kala'
   AND integrity_check_sql IS NULL;

-- ── ka_graha_sancara ──────────────────────────────────────────────────────────
UPDATE asset_registry
   SET integrity_check_sql = $INTEGRITY$
SELECT
  service_health IS NOT NULL
  AND service_health IN ('healthy', 'unhealthy')
  AND last_selftest_at IS NOT NULL
  AND last_selftest_at <= now()
  AND selftest_detail IS NOT NULL
  AND jsonb_typeof(selftest_detail) = 'object'
  AND selftest_detail <> '{}'::jsonb
  AS integrity_passed
FROM asset_registry
WHERE asset_id = 'ka_graha_sancara'
$INTEGRITY$
 WHERE asset_id = 'ka_graha_sancara'
   AND integrity_check_sql IS NULL;

-- ── ka_muhurta_seva ───────────────────────────────────────────────────────────
UPDATE asset_registry
   SET integrity_check_sql = $INTEGRITY$
SELECT
  service_health IS NOT NULL
  AND service_health IN ('healthy', 'unhealthy')
  AND last_selftest_at IS NOT NULL
  AND last_selftest_at <= now()
  AND selftest_detail IS NOT NULL
  AND jsonb_typeof(selftest_detail) = 'object'
  AND selftest_detail <> '{}'::jsonb
  AS integrity_passed
FROM asset_registry
WHERE asset_id = 'ka_muhurta_seva'
$INTEGRITY$
 WHERE asset_id = 'ka_muhurta_seva'
   AND integrity_check_sql IS NULL;

-- ── ka_tulana ─────────────────────────────────────────────────────────────────
UPDATE asset_registry
   SET integrity_check_sql = $INTEGRITY$
SELECT
  service_health IS NOT NULL
  AND service_health IN ('healthy', 'degraded')
  AND last_selftest_at IS NOT NULL
  AND last_selftest_at <= now()
  AND selftest_detail IS NOT NULL
  AND jsonb_typeof(selftest_detail) = 'object'
  AND selftest_detail <> '{}'::jsonb
  AS integrity_passed
FROM asset_registry
WHERE asset_id = 'ka_tulana'
$INTEGRITY$
 WHERE asset_id = 'ka_tulana'
   AND integrity_check_sql IS NULL;
