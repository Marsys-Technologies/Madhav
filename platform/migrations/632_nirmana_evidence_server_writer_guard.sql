-- Migration 632: bind server-reconstructed Nirmana evidence to its own
-- dedicated database login. Migration 592 remains immutable.
BEGIN;

-- This role deliberately has no password here: the deploy owner must provision
-- a distinct secret-backed credential in a separate controlled action before
-- any server-reconstructed receipt can be recorded. Until then the application
-- fails closed rather than falling back to DATABASE_URL/DB_USER.
DO $$
DECLARE
  relation_name text;
  target_table text;
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nirmana_evidence_ingress_writer') THEN
    CREATE ROLE nirmana_evidence_ingress_writer LOGIN NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
  END IF;

  EXECUTE format('GRANT USAGE ON SCHEMA %I TO nirmana_evidence_ingress_writer', current_schema());
  FOREACH relation_name IN ARRAY ARRAY[
    'nirmana_elevation_campaign_definitions',
    'nirmana_elevation_campaign_events',
    'asset_registry',
    'build_runs',
    'build_run_assets',
    'asset_provenance_receipts',
    'nirmana_elevation_monitor_observations',
    '_migrations_applied'
  ] LOOP
    IF to_regclass(format('%I.%I', current_schema(), relation_name)) IS NOT NULL THEN
      EXECUTE format('GRANT SELECT ON TABLE %I.%I TO nirmana_evidence_ingress_writer', current_schema(), relation_name);
    END IF;
  END LOOP;
  IF to_regclass(format('%I.%I', current_schema(), 'nirmana_elevation_campaign_events')) IS NOT NULL THEN
    EXECUTE format('GRANT INSERT ON TABLE %I.nirmana_elevation_campaign_events TO nirmana_evidence_ingress_writer', current_schema());
  END IF;

  -- Integrity detectors are constrained to their current registry target
  -- tables. Any query reaching outside this grant set fails closed.
  IF to_regclass(format('%I.%I', current_schema(), 'asset_registry')) IS NOT NULL THEN
    FOR target_table IN
      SELECT registry.target_table
        FROM asset_registry AS registry
       WHERE registry.target_table ~ '^[a-z_][a-z0-9_]{0,62}$'
    LOOP
      IF to_regclass(format('%I.%I', current_schema(), target_table)) IS NOT NULL THEN
        EXECUTE format('GRANT SELECT ON TABLE %I.%I TO nirmana_evidence_ingress_writer', current_schema(), target_table);
      END IF;
    END LOOP;
  END IF;
END;
$$;

CREATE OR REPLACE FUNCTION nirmana_elevation_guard_server_reconstructed_insert()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  IF NEW.source_kind = 'server_reconstructed'
     AND (session_user <> 'nirmana_evidence_ingress_writer'
          OR current_user <> 'nirmana_evidence_ingress_writer') THEN
    RAISE EXCEPTION 'server-reconstructed Nirmana evidence may only be inserted by the dedicated evidence ingress login';
  END IF;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS nirmana_elevation_events_server_writer
  ON nirmana_elevation_campaign_events;
CREATE TRIGGER nirmana_elevation_events_server_writer
  BEFORE INSERT ON nirmana_elevation_campaign_events
  FOR EACH ROW EXECUTE FUNCTION nirmana_elevation_guard_server_reconstructed_insert();

COMMENT ON FUNCTION nirmana_elevation_guard_server_reconstructed_insert() IS
  'Rejects server_reconstructed receipt insertion unless session_user and current_user are the dedicated Nirmana evidence ingress login.';

COMMIT;
