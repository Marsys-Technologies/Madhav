-- 1026_nirmana_l3_ka_service_selftest_clock_timestamp_fix.sql
--
-- NIRMĀṆA L3 Kāla — fixes issue #2574: four service-handler assets' integrity_check_sql
-- conjunct `last_selftest_at <= now()` fails almost every build, not just occasionally.
-- Root cause (diagnosed live by Conductor, re-verified live here before applying):
-- migration 933_nirmana_l3_service_selftest_shape_contracts.sql installed this conjunct.
-- Postgres `now()` == `transaction_timestamp()`, pinned to transaction START. Each writer
-- stamps `last_selftest_at` with Python wall-clock time captured strictly AFTER the
-- transaction began (a real self-test DB round-trip takes non-zero time), so
-- `last_selftest_at` (wall-clock, later) is almost always > `now()` (tx start, earlier) —
-- a near-guaranteed integrity-check failure, not a race.
--
-- Live-reverified before authoring this fix (never apply a handed-down diagnosis on trust):
--
--   SELECT now() AS tx_now_before, (SELECT pg_sleep(0.3)), clock_timestamp() AS wallclock_after_sleep,
--          now() AS tx_now_after, (clock_timestamp() > now()) AS would_fail_check;
--   -- would_fail_check: true (reproduced live, 2026-09-11)
--
-- Confirmed all four asset_registry rows literally contain `last_selftest_at <= now()` as of
-- this migration's authoring time.
--
-- Fix: replace `now()` with `clock_timestamp()` in the conjunct for all four migration-933
-- assets. `clock_timestamp()` returns actual current wall-clock time at each call, matching
-- the semantics the check actually needs (self-test timestamp is not in the future relative
-- to right now), instead of the transaction-start snapshot `now()` provides.
--
-- Scope note: this migration touches ONLY the `last_selftest_at <= now()` conjunct's text.
-- Per issue #2574's ruling (b), `ka_graha_sancara`'s separate pre-existing
-- `service_health = 'unhealthy'` row is a different, already-routed, out-of-scope finding —
-- NOT touched here.
--
-- Transaction ownership belongs to platform/scripts/migrate.ts.

UPDATE asset_registry
SET integrity_check_sql = replace(integrity_check_sql, 'last_selftest_at <= now()', 'last_selftest_at <= clock_timestamp()')
WHERE asset_id IN ('ka_dasha_kala', 'ka_graha_sancara', 'ka_muhurta_seva', 'ka_tulana')
  AND integrity_check_sql LIKE '%last_selftest_at <= now()%';
