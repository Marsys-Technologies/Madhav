-- Migration 634: grant the deployment-only marker its sole tracker sequence capability.
-- Created: 2026-08-28
-- The preflight grants this before unmarked marker attestation because deploy.yml
-- runs the marker before the ordinary migration runner. This forward migration
-- declares the converged state for subsequent normal migration runs.

DO $$
BEGIN
  IF current_user <> 'amjis_app' OR NOT EXISTS (
    SELECT 1
      FROM pg_class sequence
      JOIN pg_roles owner ON owner.oid = sequence.relowner
     WHERE sequence.oid = pg_get_serial_sequence('public._migrations_applied', 'id')::regclass
       AND sequence.oid = 'public._migrations_applied_id_seq'::regclass
       AND owner.rolname = current_user
  ) THEN
    RAISE EXCEPTION 'migration 634 requires amjis_app ownership of the expected migration-ledger sequence';
  END IF;
  GRANT USAGE ON SEQUENCE public._migrations_applied_id_seq TO nirmana_migrator;
END $$;
