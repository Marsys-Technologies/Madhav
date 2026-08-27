-- Migration 630: restrict server-reconstructed Nirmana evidence to the
-- validated application evidence ingress. Migration 592 remains immutable.
BEGIN;

-- A caller must explicitly assume this NOLOGIN role inside its transaction.
-- It is granted only to the database principal applying the governed service
-- migrations; a bare SQL client cannot manufacture current_user by setting an
-- application GUC.  The role itself holds no broad database privileges.
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nirmana_evidence_ingress') THEN
    CREATE ROLE nirmana_evidence_ingress NOLOGIN NOINHERIT;
  END IF;
  EXECUTE format('GRANT nirmana_evidence_ingress TO %I', current_user);
END;
$$;

CREATE OR REPLACE FUNCTION nirmana_elevation_guard_server_reconstructed_insert()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  IF NEW.source_kind = 'server_reconstructed'
     AND current_user <> 'nirmana_evidence_ingress' THEN
    RAISE EXCEPTION 'server-reconstructed Nirmana evidence may only be inserted by the validated evidence ingress';
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
  'Rejects server_reconstructed receipt insertion unless the validated application transaction has assumed nirmana_evidence_ingress.';

COMMIT;
