-- Migration 242: L3 Kāla service-asset-type infrastructure
-- Adds asset_kind (canonical kind field — distinct from asset_type which is a
-- pre-existing categorical column) + service-health telemetry columns.
-- Makes count_sql / target_table explicitly NULLABLE (already nullable by default;
-- this migration adds DROP NOT NULL guards for idempotency on stricter schemas).
-- Per: L3_KALA_CAMPAIGN_PLAN_v0_8.md §K0 wave "service-asset-type infra"
--
-- Idempotent: every ALTER uses IF NOT EXISTS / DROP CONSTRAINT IF EXISTS.

BEGIN;

-- §1 — Add asset_kind column ─────────────────────────────────────────────────
-- 'data'     — table-backed asset (default; existing rows)
-- 'service'  — engine/API service with health probe (count_sql IS NULL)
-- 'artifact' — GCS/external artifact, no DB table

ALTER TABLE asset_registry ADD COLUMN IF NOT EXISTS asset_kind text NOT NULL DEFAULT 'data';

-- Add CHECK constraint (drop-first for idempotency)
ALTER TABLE asset_registry DROP CONSTRAINT IF EXISTS asset_registry_asset_kind_check;
ALTER TABLE asset_registry ADD CONSTRAINT asset_registry_asset_kind_check
  CHECK (asset_kind IN ('data', 'service', 'artifact'));

-- §2 — Backfill existing rows ────────────────────────────────────────────────
-- Rows already marked asset_type='service' → asset_kind='service'
-- All others → asset_kind='data' (already covered by DEFAULT but be explicit)

UPDATE asset_registry SET asset_kind = 'service' WHERE asset_type = 'service' AND asset_kind = 'data';
UPDATE asset_registry SET asset_kind = 'data'    WHERE asset_type != 'service' AND asset_kind NOT IN ('service', 'artifact');

-- §3 — Service-health telemetry columns ──────────────────────────────────────
-- service_health   : latest probe result ('healthy'|'degraded'|'unhealthy'|'unknown')
-- last_invoked_at  : when the service was last successfully probed / invoked
-- last_selftest_at : when the self-test writer last ran (writer-managed)
-- selftest_detail  : JSONB blob from the self-test (checks[], message, etc.)

ALTER TABLE asset_registry ADD COLUMN IF NOT EXISTS service_health    text        NULL;
ALTER TABLE asset_registry ADD COLUMN IF NOT EXISTS last_invoked_at   timestamptz NULL;
ALTER TABLE asset_registry ADD COLUMN IF NOT EXISTS last_selftest_at  timestamptz NULL;
ALTER TABLE asset_registry ADD COLUMN IF NOT EXISTS selftest_detail   jsonb       NULL;

-- CHECK constraint on service_health (drop-first for idempotency)
ALTER TABLE asset_registry DROP CONSTRAINT IF EXISTS asset_registry_service_health_check;
ALTER TABLE asset_registry ADD CONSTRAINT asset_registry_service_health_check
  CHECK (service_health IN ('healthy', 'degraded', 'unhealthy', 'unknown'));

-- §4 — Ensure count_sql / target_table are explicitly nullable ───────────────
-- They were already nullable by default (no NOT NULL constraint was added in prior
-- migrations). This block is a belt-and-suspenders guard: it drops any NOT NULL
-- constraint if one exists, making a service-kind row (count_sql IS NULL) safe.

ALTER TABLE asset_registry ALTER COLUMN count_sql    DROP NOT NULL;
ALTER TABLE asset_registry ALTER COLUMN target_table DROP NOT NULL;

COMMIT;

-- ── Reversible DOWN block (run manually to roll back) ────────────────────────
-- BEGIN;
-- ALTER TABLE asset_registry
--   DROP COLUMN IF EXISTS asset_kind,
--   DROP COLUMN IF EXISTS service_health,
--   DROP COLUMN IF EXISTS last_invoked_at,
--   DROP COLUMN IF EXISTS last_selftest_at,
--   DROP COLUMN IF EXISTS selftest_detail;
-- ALTER TABLE asset_registry DROP CONSTRAINT IF EXISTS asset_registry_asset_kind_check;
-- ALTER TABLE asset_registry DROP CONSTRAINT IF EXISTS asset_registry_service_health_check;
-- COMMIT;
