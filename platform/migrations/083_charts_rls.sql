-- 083_charts_rls.sql
-- Unit 2c (Stream B) — Postgres Row-Level Security on charts (defense-in-depth
-- behind authorizeChartAccess.ts).
--
-- Principal identity carried per-request via `SET LOCAL app.principal_id = '<uid>'`
-- (issued by the web layer's pg-pool wrapper after Firebase verify).
-- Service-role bypass: a session that has not set app.principal_id (e.g. the
-- migration runner, batch jobs, super_admin server context) is treated as
-- unrestricted — current_setting('app.principal_id', true) returns NULL,
-- and the policy's USING clause then falls through to TRUE for app-context-less
-- callers.
--
-- Policies are additive (FOR ALL + FOR SELECT). App-layer authorizeChartAccess
-- is the primary gate; RLS is the keeper.
--
-- Idempotent.

BEGIN;

ALTER TABLE charts ENABLE ROW LEVEL SECURITY;

-- Drop pre-existing policies for clean re-apply.
DROP POLICY IF EXISTS chart_owner_policy   ON charts;
DROP POLICY IF EXISTS chart_grant_policy   ON charts;
DROP POLICY IF EXISTS chart_service_policy ON charts;

-- 1. Service-role bypass: when app.principal_id is unset (NULL), allow all.
--    Migrations + Cloud SQL admin connections + super_admin server fetches
--    that do not set the GUC will pass through.
CREATE POLICY chart_service_policy ON charts
  AS PERMISSIVE
  FOR ALL
  USING ( current_setting('app.principal_id', true) IS NULL
          OR current_setting('app.principal_id', true) = '' );

-- 2. Owner: full access when principal matches owner_id.
CREATE POLICY chart_owner_policy ON charts
  AS PERMISSIVE
  FOR ALL
  USING ( owner_id = current_setting('app.principal_id', true) );

-- 3. Grant: view-only access through chart_grants.
CREATE POLICY chart_grant_policy ON charts
  AS PERMISSIVE
  FOR SELECT
  USING (
    EXISTS (
      SELECT 1
        FROM chart_grants g
       WHERE g.chart_id     = charts.id
         AND g.principal_id = current_setting('app.principal_id', true)
    )
  );

COMMIT;
