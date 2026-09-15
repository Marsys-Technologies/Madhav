-- Migration 1037: restart-safe planner inquiry action reservations
-- Created: 2026-09-15
--
-- 1035 and 1036 are reserved by the governed Data Plane stack. This source-only
-- migration has not been applied to any shared or production database.

BEGIN;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_roles
     WHERE rolname='purna_inquiry_owner'
       AND NOT rolcanlogin AND NOT rolinherit AND NOT rolsuper
       AND NOT rolcreatedb AND NOT rolcreaterole
       AND NOT rolreplication AND NOT rolbypassrls
  ) THEN
    RAISE EXCEPTION 'Pūrṇa migrations require normalized NOLOGIN purna_inquiry_owner';
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM pg_auth_members membership
      JOIN pg_roles owner ON owner.oid=membership.roleid
      JOIN pg_roles actor ON actor.oid=membership.member
     WHERE owner.rolname='purna_inquiry_owner'
       AND actor.rolname=session_user
       AND membership.admin_option
  ) THEN
    RAISE EXCEPTION 'Pūrṇa migrations require direct temporary owner membership with admin option';
  END IF;
  IF NOT has_schema_privilege('purna_inquiry_owner', 'public', 'CREATE') THEN
    RAISE EXCEPTION 'Pūrṇa migrations require temporary owner CREATE on public';
  END IF;
END $$;

SET LOCAL ROLE purna_inquiry_owner;

CREATE TABLE IF NOT EXISTS planner_inquiry_action_reservations (
  inquiry_id uuid NOT NULL REFERENCES planner_inquiry_lifecycles(inquiry_id) ON DELETE CASCADE,
  revision integer NOT NULL CHECK (revision >= 0),
  plan_item_id text NOT NULL CHECK (plan_item_id ~ '^item-[0-9]{3}$'),
  source_jti_hash text NOT NULL,
  reservation_hash text NOT NULL UNIQUE,
  state text NOT NULL DEFAULT 'reserved'
    CHECK (state IN ('reserved', 'dispatched', 'committed', 'failed_closed')),
  lease_expires_at timestamptz NOT NULL,
  reserved_at timestamptz NOT NULL DEFAULT now(),
  dispatch_started_at timestamptz,
  committed_at timestamptz,
  PRIMARY KEY (inquiry_id, revision, plan_item_id),
  CHECK (lease_expires_at > reserved_at),
  CHECK ((state = 'reserved' AND dispatch_started_at IS NULL AND committed_at IS NULL)
      OR (state = 'dispatched' AND dispatch_started_at IS NOT NULL AND committed_at IS NULL)
      OR (state IN ('committed', 'failed_closed') AND dispatch_started_at IS NOT NULL AND committed_at IS NOT NULL))
);

CREATE INDEX IF NOT EXISTS planner_inquiry_action_reservations_lease_idx
  ON planner_inquiry_action_reservations (lease_expires_at)
  WHERE state = 'reserved';

CREATE OR REPLACE FUNCTION planner_inquiry_action_reservation_guard()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF ROW(NEW.inquiry_id, NEW.revision, NEW.plan_item_id, NEW.source_jti_hash, NEW.reserved_at)
     IS DISTINCT FROM
     ROW(OLD.inquiry_id, OLD.revision, OLD.plan_item_id, OLD.source_jti_hash, OLD.reserved_at) THEN
    RAISE EXCEPTION 'planner inquiry action reservation identity cannot change';
  END IF;

  IF OLD.state = 'reserved' AND NEW.state = 'reserved' THEN
    IF OLD.lease_expires_at > now()
       OR NEW.reservation_hash = OLD.reservation_hash
       OR NEW.lease_expires_at <= now()
       OR NEW.dispatch_started_at IS NOT NULL
       OR NEW.committed_at IS NOT NULL THEN
      RAISE EXCEPTION 'invalid planner inquiry reservation recovery';
    END IF;
  ELSIF OLD.state = 'reserved' AND NEW.state = 'dispatched' THEN
    IF NEW.reservation_hash <> OLD.reservation_hash
       OR NEW.lease_expires_at <= now()
       OR NEW.dispatch_started_at IS NULL
       OR NEW.committed_at IS NOT NULL THEN
      RAISE EXCEPTION 'invalid planner inquiry dispatch transition';
    END IF;
  ELSIF OLD.state = 'dispatched' AND NEW.state IN ('committed', 'failed_closed') THEN
    IF NEW.reservation_hash <> OLD.reservation_hash
       OR NEW.dispatch_started_at IS DISTINCT FROM OLD.dispatch_started_at
       OR NEW.committed_at IS NULL THEN
      RAISE EXCEPTION 'invalid planner inquiry terminal transition';
    END IF;
  ELSE
    RAISE EXCEPTION 'invalid planner inquiry action state transition % -> %', OLD.state, NEW.state;
  END IF;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS planner_inquiry_action_reservation_guard_trigger
  ON planner_inquiry_action_reservations;
CREATE TRIGGER planner_inquiry_action_reservation_guard_trigger
BEFORE UPDATE ON planner_inquiry_action_reservations
FOR EACH ROW EXECUTE FUNCTION planner_inquiry_action_reservation_guard();

COMMENT ON TABLE planner_inquiry_action_reservations IS
  'One durable reservation per inquiry revision/action. lease_expires_at is a pre-dispatch recovery lease and, after dispatch starts, the in-progress deadline. Dispatched work is never replayed; only an expired dispatched deadline is failed closed as ambiguous.';
COMMENT ON COLUMN planner_inquiry_action_reservations.source_jti_hash IS
  'Hash of the client lifecycle token consumed by the first reservation; required to recover only that same authorized action.';

REVOKE ALL ON planner_inquiry_action_reservations FROM role_web_serve;
GRANT SELECT, INSERT ON planner_inquiry_action_reservations TO role_web_serve;
GRANT UPDATE (reservation_hash, state, lease_expires_at, dispatch_started_at, committed_at)
  ON planner_inquiry_action_reservations TO role_web_serve;

ALTER TABLE planner_inquiry_action_reservations ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS planner_inquiry_action_reservations_principal_chart
  ON planner_inquiry_action_reservations;
CREATE POLICY planner_inquiry_action_reservations_principal_chart
  ON planner_inquiry_action_reservations AS PERMISSIVE FOR ALL TO role_web_serve
  USING (EXISTS (
    SELECT 1 FROM planner_inquiry_lifecycles lifecycle
    WHERE lifecycle.inquiry_id = planner_inquiry_action_reservations.inquiry_id
      AND lifecycle.principal_uid = current_setting('app.principal_id', true)
      AND lifecycle.chart_id = app_chart_context()
  ))
  WITH CHECK (EXISTS (
    SELECT 1 FROM planner_inquiry_lifecycles lifecycle
    WHERE lifecycle.inquiry_id = planner_inquiry_action_reservations.inquiry_id
      AND lifecycle.principal_uid = current_setting('app.principal_id', true)
      AND lifecycle.chart_id = app_chart_context()
  ));

COMMIT;

-- DOWN (manual, destructive; retain/export inquiry evidence before use):
-- DROP TABLE IF EXISTS planner_inquiry_action_reservations;
-- DROP FUNCTION IF EXISTS planner_inquiry_action_reservation_guard();
