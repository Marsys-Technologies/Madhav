-- 081_chart_grants_and_owner_id.sql
-- Unit 2c (Stream B) — Multi-guest tenancy + one authorization brain.
-- ADDITIVE (strangler pattern): owner_id + subject_name on charts, new chart_grants table.
-- charts.client_id is RETAINED for the cutover window — drops deferred to post-cutover.
--
-- Backfill: owner_id := client_id (today these are the same Firebase UID).
--
-- Idempotent: re-runnable.

BEGIN;

-- 1. charts.owner_id (text Firebase UID; the guest who owns this chart).
ALTER TABLE charts ADD COLUMN IF NOT EXISTS owner_id TEXT;

-- 2. charts.subject_name (the chart subject's name — not necessarily the owner).
ALTER TABLE charts ADD COLUMN IF NOT EXISTS subject_name TEXT;

-- 3. Backfill owner_id from client_id for any row still NULL.
UPDATE charts SET owner_id = client_id WHERE owner_id IS NULL AND client_id IS NOT NULL;

-- 4. Backfill subject_name from name for any row still NULL.
UPDATE charts SET subject_name = name WHERE subject_name IS NULL AND name IS NOT NULL;

-- 5. Index for owner lookups (single-owner dashboard query path).
CREATE INDEX IF NOT EXISTS idx_charts_owner_id ON charts(owner_id);

-- 6. chart_grants — view-only share table.
CREATE TABLE IF NOT EXISTS chart_grants (
  id           UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  chart_id     UUID        NOT NULL REFERENCES charts(id) ON DELETE CASCADE,
  principal_id TEXT        NOT NULL,                       -- Firebase UID of grantee
  permission   TEXT        NOT NULL DEFAULT 'view'
                             CHECK (permission IN ('view')),
  granted_by   TEXT        NOT NULL,                       -- Firebase UID of granter (super_admin or owner)
  granted_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (chart_id, principal_id)
);

CREATE INDEX IF NOT EXISTS idx_chart_grants_chart_id      ON chart_grants(chart_id);
CREATE INDEX IF NOT EXISTS idx_chart_grants_principal_id  ON chart_grants(principal_id);

COMMIT;
