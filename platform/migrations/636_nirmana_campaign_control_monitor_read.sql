-- Migration 636: restore the campaign-control monitor-observation read.
-- Created: 2026-08-29
--
-- The control writer must read one fresh, in-sync monitor row inside the
-- serializable definition-acceptance transaction.  Monitor observations are
-- append-only and immutable, so row locking is neither necessary nor
-- least-privilege: PostgreSQL row-locking SELECTs require write-class table
-- privilege.  Migration 629 can have created this public relation after the
-- one-shot ownership preflight, leaving the exact read envelope absent in
-- production.

DO $$
BEGIN
  IF session_user <> 'amjis_app' OR current_user <> 'amjis_app' THEN
    RAISE EXCEPTION 'migration 636 must run directly as amjis_app';
  END IF;

  IF to_regclass('public.nirmana_elevation_monitor_observations') IS NULL THEN
    RAISE EXCEPTION 'migration 636 requires public.nirmana_elevation_monitor_observations';
  END IF;

  IF NOT EXISTS (
    SELECT 1
      FROM pg_roles
     WHERE rolname = 'nirmana_campaign_control_writer'
       AND rolcanlogin
       AND NOT rolinherit
       AND NOT rolsuper
       AND NOT rolcreatedb
       AND NOT rolcreaterole
       AND NOT rolreplication
       AND NOT rolbypassrls
  ) THEN
    RAISE EXCEPTION 'migration 636 requires the normalized campaign-control writer';
  END IF;

  REVOKE ALL PRIVILEGES ON TABLE public.nirmana_elevation_monitor_observations
    FROM nirmana_campaign_control_writer;
  GRANT SELECT ON TABLE public.nirmana_elevation_monitor_observations
    TO nirmana_campaign_control_writer;

  IF NOT has_table_privilege(
    'nirmana_campaign_control_writer',
    'public.nirmana_elevation_monitor_observations',
    'SELECT'
  ) OR has_table_privilege(
    'nirmana_campaign_control_writer',
    'public.nirmana_elevation_monitor_observations',
    'INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER'
  ) THEN
    RAISE EXCEPTION 'migration 636 could not establish the exact campaign-control monitor read';
  END IF;
END;
$$;
