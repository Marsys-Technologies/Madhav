-- 1336_bo_samskara_writer_timeout_budget.sql
--
-- Suvarna FALLBACK: raise asset_registry.writer_timeout_seconds for bo_samskara from 10800 to 18000.
-- Data-only: ONE column of ONE asset_registry row, no DDL, no new object. Transaction ownership belongs to
-- platform/scripts/migrate.ts (no BEGIN/COMMIT here). Same pattern as migrations 1218, 1296 and 1329.
--
-- WHY. bo_samskara re-embeds every shared MSR row (about 25,000 texts) once per ayanamsha, five ayanamshas, at roughly 30 minutes
-- per ayanamsha. That is ~2.5 h of pure embedding against a 10800 s (3 h) registry budget, which leaves too little margin for
-- retries and quota backoff. The per-asset registry value overrides the job-level WRITER_TIMEOUT_SECONDS, so a thin registry
-- value caps the writer no matter what the job allows.
--
-- THIS IS A FALLBACK. It is to be merged and applied ONLY if bo_samskara breaches its current budget in production run 2af5c8a2.
-- If that run completes inside 10800 s this migration is not needed.
--
-- GUARD. The row is read FOR UPDATE. A missing or inactive row RAISES (the budget must land on a live asset). A row already at or
-- above 18000 is a NOTICE no-op: the migration only ever RAISES a budget, never lowers one, so replaying it is idempotent.
-- A row below 18000 is updated and re-read; if the UPDATE did not take, RAISE (never trust a silent no-op, CLAUDE.md N.4).
--
-- NO TRIGGER EFFECT. nirmana_registry_receipt_invalidation fires only AFTER UPDATE OF depends_on, natural_key_partition, health_probe,
-- integrity_check_sql, target_floor, asset_kind, asset_type, scope, has_writer, is_active, target_table (definition read on production
-- with pg_get_triggerdef, 2026-10-09). writer_timeout_seconds is not among them, so no asset_freshness receipt is staled.
-- Production value read 2026-10-09: bo_samskara writer_timeout_seconds = 10800, is_active = true.
--
-- Seed: platform/scripts/seed/asset_registry_seed.ts carries the same value (its ON CONFLICT preserves live values).
-- Tests: platform/tests/unit/migrations/bo_samskara_writer_timeout_1336_static.test.ts.
--
-- Post-apply verification:
--   SELECT asset_id, writer_timeout_seconds FROM asset_registry WHERE asset_id = 'bo_samskara';   -- expect 18000
--
-- ROLLBACK (not executed by migrate.ts):
--   UPDATE asset_registry SET writer_timeout_seconds = 10800 WHERE asset_id = 'bo_samskara' AND writer_timeout_seconds = 18000;

SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '60s';

DO $m1336$
DECLARE
  r      record;
  cur    integer;
  active boolean;
BEGIN
  FOR r IN
    SELECT * FROM (VALUES
      ('bo_samskara', 18000)
    ) AS v(asset_id, new_v)
  LOOP
    SELECT writer_timeout_seconds, is_active INTO cur, active
      FROM asset_registry WHERE asset_id = r.asset_id FOR UPDATE;
    IF NOT FOUND THEN
      RAISE EXCEPTION '1336: % has no asset_registry row', r.asset_id;
    ELSIF active IS DISTINCT FROM true THEN
      RAISE EXCEPTION '1336: % is not active in asset_registry', r.asset_id;
    ELSIF cur >= r.new_v THEN
      RAISE NOTICE '1336: % writer_timeout_seconds already % (>= %); nothing to do', r.asset_id, cur, r.new_v;
    ELSE
      UPDATE asset_registry
         SET writer_timeout_seconds = r.new_v
       WHERE asset_id = r.asset_id
         AND (writer_timeout_seconds IS NULL OR writer_timeout_seconds < r.new_v);
      SELECT writer_timeout_seconds INTO cur FROM asset_registry WHERE asset_id = r.asset_id;
      IF cur IS DISTINCT FROM r.new_v THEN
        RAISE EXCEPTION '1336: % writer_timeout_seconds update did not take (expected %, found %)', r.asset_id, r.new_v, cur;
      END IF;
    END IF;
  END LOOP;
END
$m1336$;
