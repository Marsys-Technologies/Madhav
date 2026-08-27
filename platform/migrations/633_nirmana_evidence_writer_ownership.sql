-- Migration 633: separate Nirmana campaign ownership from application writers.
--
-- Prerequisite (intentionally not provisioned here): a deployment-only,
-- non-superuser nirmana_migrator LOGIN role with CREATEROLE/CREATEDB and the
-- temporary ability to SET ROLE amjis_app and USAGE on this schema. Cloud Run
-- must never receive that credential. The migration fails closed when that
-- controlled handoff cannot be performed.
DO $$
DECLARE
  campaign_relation text;
  legacy_function text;
  inherited_role text;
  granted_member text;
BEGIN
  IF session_user <> 'nirmana_migrator' OR current_user <> 'nirmana_migrator' THEN
    RAISE EXCEPTION 'migration 633 must run as the deployment-only nirmana_migrator login';
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_roles
     WHERE rolname = 'nirmana_migrator'
       AND rolcanlogin AND rolcreaterole AND rolcreatedb
       AND NOT rolsuper AND NOT rolreplication AND NOT rolbypassrls
  ) THEN
    RAISE EXCEPTION 'migration 633 requires a non-superuser nirmana_migrator with CREATEROLE and CREATEDB';
  END IF;

  IF EXISTS (
    SELECT 1 FROM pg_roles
     WHERE rolname = 'nirmana_evidence_owner'
       AND (rolcanlogin OR rolsuper OR rolcreatedb OR rolcreaterole OR rolreplication OR rolbypassrls)
  ) THEN
    RAISE EXCEPTION 'migration 633 refuses an elevated or login-capable nirmana_evidence_owner';
  ELSIF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nirmana_evidence_owner') THEN
    CREATE ROLE nirmana_evidence_owner NOLOGIN NOINHERIT;
  END IF;

  IF EXISTS (
    SELECT 1 FROM pg_roles
     WHERE rolname = 'nirmana_campaign_control_writer'
       AND (NOT rolcanlogin OR rolsuper OR rolreplication OR rolbypassrls)
  ) THEN
    RAISE EXCEPTION 'migration 633 refuses an elevated or disabled nirmana_campaign_control_writer';
  ELSIF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nirmana_campaign_control_writer') THEN
    CREATE ROLE nirmana_campaign_control_writer LOGIN NOINHERIT NOCREATEDB NOCREATEROLE;
  ELSE
    ALTER ROLE nirmana_campaign_control_writer LOGIN NOINHERIT NOCREATEDB NOCREATEROLE;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_roles
     WHERE rolname = 'nirmana_evidence_ingress_writer'
       AND rolcanlogin AND NOT rolinherit AND NOT rolsuper
       AND NOT rolcreatedb AND NOT rolcreaterole AND NOT rolreplication AND NOT rolbypassrls
  ) THEN
    RAISE EXCEPTION 'migration 633 requires the normalized migration 632 ingress login';
  END IF;

  IF EXISTS (
    SELECT 1 FROM pg_roles
     WHERE rolname = 'amjis_app'
       AND (rolsuper OR rolreplication OR rolbypassrls)
  ) THEN
    RAISE EXCEPTION 'migration 633 refuses an elevated generic amjis_app role';
  END IF;
  -- The legacy generic runtime login currently has role-creation capabilities.
  -- Remove them before it loses campaign ownership: otherwise it could restore
  -- a writer membership after this migration.
  ALTER ROLE amjis_app NOINHERIT NOCREATEDB NOCREATEROLE;

  -- Membership in the NOLOGIN owner role exists only while this migration is
  -- executing and is revoked in its postflight. No serving role may inherit it.
  GRANT nirmana_evidence_owner TO nirmana_migrator WITH ADMIN OPTION;

  FOR inherited_role IN
    SELECT parent.rolname
      FROM pg_auth_members AS membership
      JOIN pg_roles AS parent ON parent.oid = membership.roleid
      JOIN pg_roles AS member ON member.oid = membership.member
     WHERE member.rolname = 'nirmana_campaign_control_writer'
  LOOP
    EXECUTE format('REVOKE %I FROM nirmana_campaign_control_writer', inherited_role);
  END LOOP;
  FOR granted_member IN
    SELECT member.rolname
      FROM pg_auth_members AS membership
      JOIN pg_roles AS granted ON granted.oid = membership.roleid
      JOIN pg_roles AS member ON member.oid = membership.member
     WHERE granted.rolname = 'nirmana_campaign_control_writer'
  LOOP
    EXECUTE format('REVOKE nirmana_campaign_control_writer FROM %I', granted_member);
  END LOOP;
  IF EXISTS (
    SELECT 1
      FROM pg_class AS relation
      JOIN pg_namespace AS namespace ON namespace.oid = relation.relnamespace
     WHERE namespace.nspname <> current_schema()
       AND namespace.nspname !~ '^pg_' AND namespace.nspname <> 'information_schema'
       AND relation.relkind IN ('r', 'p', 'v', 'm', 'f')
       AND has_table_privilege('nirmana_campaign_control_writer', relation.oid,
         'SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER')
  ) THEN
    RAISE EXCEPTION 'migration 633 refuses campaign control writer privileges outside the evidence schema';
  END IF;
  EXECUTE format('GRANT CONNECT ON DATABASE %I TO nirmana_campaign_control_writer', current_database());
END;
$$;

-- The legacy application owns these deployed objects. Its authority is a
-- one-time handoff: after the transfer the migration revokes the temporary
-- nirmana_migrator -> amjis_app edge, and a replay refuses to continue if it
-- has survived. That prevents the DDL login from becoming a generic app role.
DO $$
DECLARE
  legacy_ownership_remaining boolean;
BEGIN
  SELECT EXISTS (
    SELECT 1 FROM pg_class AS relation
      JOIN pg_namespace AS namespace ON namespace.oid = relation.relnamespace
      JOIN pg_roles AS owner ON owner.oid = relation.relowner
     WHERE namespace.nspname = current_schema()
       AND relation.relname IN (
         'nirmana_elevation_campaign_definitions',
         'nirmana_elevation_campaign_events',
         'nirmana_elevation_asset_labels'
       )
       AND owner.rolname = 'amjis_app'
  ) INTO legacy_ownership_remaining;

  IF legacy_ownership_remaining THEN
    IF NOT EXISTS (
      SELECT 1 FROM pg_auth_members AS membership
        JOIN pg_roles AS parent ON parent.oid = membership.roleid
        JOIN pg_roles AS member ON member.oid = membership.member
       WHERE parent.rolname = 'amjis_app' AND member.rolname = session_user
         AND membership.admin_option
    ) THEN
      RAISE EXCEPTION 'migration 633 requires temporary SET ROLE membership in legacy owner amjis_app for the one-time ownership handoff';
    END IF;
    GRANT nirmana_evidence_owner TO amjis_app;
    EXECUTE 'SET LOCAL ROLE amjis_app';
    EXECUTE format(
      'GRANT USAGE, CREATE ON SCHEMA %I TO nirmana_evidence_owner WITH GRANT OPTION',
      current_schema()
    );
    ALTER TABLE nirmana_elevation_campaign_definitions OWNER TO nirmana_evidence_owner;
    ALTER TABLE nirmana_elevation_campaign_events OWNER TO nirmana_evidence_owner;
    ALTER TABLE nirmana_elevation_asset_labels OWNER TO nirmana_evidence_owner;
    ALTER FUNCTION nirmana_elevation_prevent_event_mutation() OWNER TO nirmana_evidence_owner;
    ALTER FUNCTION nirmana_elevation_guard_definition_mutation() OWNER TO nirmana_evidence_owner;
    ALTER FUNCTION nirmana_elevation_prevent_label_mutation() OWNER TO nirmana_evidence_owner;
    ALTER FUNCTION nirmana_elevation_guard_server_reconstructed_insert() OWNER TO nirmana_evidence_owner;
    EXECUTE 'RESET ROLE';
  ELSIF pg_has_role(session_user, 'amjis_app', 'member') THEN
    RAISE EXCEPTION 'migration 633 refuses a replay with surviving nirmana_migrator membership in amjis_app';
  END IF;
END;
$$;

REVOKE nirmana_evidence_owner FROM amjis_app;
REVOKE amjis_app FROM nirmana_migrator;

SET LOCAL ROLE nirmana_evidence_owner;

-- New rows are tagged by the database trigger. Existing receipts intentionally
-- remain NULL: no historical event is retroactively trusted as a dedicated
-- writer receipt.
ALTER TABLE nirmana_elevation_campaign_events
  ADD COLUMN IF NOT EXISTS writer_identity text;

CREATE OR REPLACE FUNCTION nirmana_elevation_guard_server_reconstructed_insert()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  IF session_user <> current_user THEN
    RAISE EXCEPTION 'Nirmana evidence writers may not cross roles';
  END IF;

  IF NEW.source_kind = 'server_reconstructed' THEN
    IF session_user <> 'nirmana_evidence_ingress_writer' THEN
      RAISE EXCEPTION 'server-reconstructed Nirmana evidence may only be inserted by the dedicated evidence ingress login';
    END IF;
  ELSIF session_user <> 'nirmana_campaign_control_writer' THEN
    RAISE EXCEPTION 'non-server Nirmana evidence may only be inserted by the campaign control writer';
  END IF;

  NEW.writer_identity := session_user;
  RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION nirmana_elevation_guard_control_writer()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  IF session_user <> 'nirmana_campaign_control_writer'
     OR current_user <> 'nirmana_campaign_control_writer' THEN
    RAISE EXCEPTION 'Nirmana campaign definitions and labels may only be written by the campaign control writer';
  END IF;
  RETURN COALESCE(NEW, OLD);
END;
$$;

CREATE OR REPLACE FUNCTION nirmana_elevation_prevent_campaign_truncate()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  RAISE EXCEPTION 'Nirmana campaign evidence, definitions, and labels cannot be truncated';
END;
$$;

DROP TRIGGER IF EXISTS nirmana_elevation_definitions_control_writer
  ON nirmana_elevation_campaign_definitions;
CREATE TRIGGER nirmana_elevation_definitions_control_writer
  BEFORE INSERT OR UPDATE OR DELETE ON nirmana_elevation_campaign_definitions
  FOR EACH ROW EXECUTE FUNCTION nirmana_elevation_guard_control_writer();

DROP TRIGGER IF EXISTS nirmana_elevation_labels_control_writer
  ON nirmana_elevation_asset_labels;
CREATE TRIGGER nirmana_elevation_labels_control_writer
  BEFORE INSERT OR UPDATE OR DELETE ON nirmana_elevation_asset_labels
  FOR EACH ROW EXECUTE FUNCTION nirmana_elevation_guard_control_writer();

DROP TRIGGER IF EXISTS nirmana_elevation_definitions_no_truncate
  ON nirmana_elevation_campaign_definitions;
CREATE TRIGGER nirmana_elevation_definitions_no_truncate
  BEFORE TRUNCATE ON nirmana_elevation_campaign_definitions
  FOR EACH STATEMENT EXECUTE FUNCTION nirmana_elevation_prevent_campaign_truncate();

DROP TRIGGER IF EXISTS nirmana_elevation_events_no_truncate
  ON nirmana_elevation_campaign_events;
CREATE TRIGGER nirmana_elevation_events_no_truncate
  BEFORE TRUNCATE ON nirmana_elevation_campaign_events
  FOR EACH STATEMENT EXECUTE FUNCTION nirmana_elevation_prevent_campaign_truncate();

-- The label migration already protects truncate; replace it with the common
-- owner-controlled function so replay has one exact protection contract.
DROP TRIGGER IF EXISTS nirmana_elevation_asset_labels_append_only
  ON nirmana_elevation_asset_labels;
CREATE TRIGGER nirmana_elevation_asset_labels_append_only
  BEFORE UPDATE OR DELETE OR TRUNCATE ON nirmana_elevation_asset_labels
  FOR EACH STATEMENT EXECUTE FUNCTION nirmana_elevation_prevent_label_mutation();

-- No generic application principal can mutate the governed campaign ledger.
REVOKE ALL PRIVILEGES ON TABLE nirmana_elevation_campaign_definitions,
  nirmana_elevation_campaign_events, nirmana_elevation_asset_labels FROM PUBLIC;
REVOKE ALL PRIVILEGES ON TABLE nirmana_elevation_campaign_definitions,
  nirmana_elevation_campaign_events, nirmana_elevation_asset_labels FROM amjis_app;
GRANT SELECT ON TABLE nirmana_elevation_campaign_definitions,
  nirmana_elevation_campaign_events, nirmana_elevation_asset_labels TO amjis_app;

-- Rebuild both dedicated writer privilege envelopes on every safe replay.
REVOKE ALL PRIVILEGES ON TABLE nirmana_elevation_campaign_definitions,
  nirmana_elevation_campaign_events, nirmana_elevation_asset_labels FROM nirmana_campaign_control_writer;
REVOKE ALL PRIVILEGES ON TABLE nirmana_elevation_campaign_definitions,
  nirmana_elevation_campaign_events, nirmana_elevation_asset_labels FROM nirmana_evidence_ingress_writer;
DO $$
BEGIN
  EXECUTE format(
    'REVOKE ALL PRIVILEGES ON SCHEMA %I FROM nirmana_campaign_control_writer',
    current_schema()
  );
  EXECUTE format(
    'REVOKE ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA %I FROM nirmana_campaign_control_writer',
    current_schema()
  );
  EXECUTE format(
    'GRANT USAGE ON SCHEMA %I TO nirmana_campaign_control_writer, nirmana_evidence_ingress_writer',
    current_schema()
  );
END;
$$;
GRANT SELECT, INSERT, UPDATE ON TABLE nirmana_elevation_campaign_definitions TO nirmana_campaign_control_writer;
GRANT SELECT, INSERT ON TABLE nirmana_elevation_campaign_events TO nirmana_campaign_control_writer;
GRANT SELECT, INSERT ON TABLE nirmana_elevation_asset_labels TO nirmana_campaign_control_writer;
GRANT SELECT ON TABLE nirmana_elevation_campaign_definitions TO nirmana_evidence_ingress_writer;
GRANT SELECT, INSERT ON TABLE nirmana_elevation_campaign_events TO nirmana_evidence_ingress_writer;

COMMENT ON COLUMN nirmana_elevation_campaign_events.writer_identity IS
  'Database-derived dedicated login for receipts recorded after migration 633; historical NULL rows are not writer-trusted.';
COMMENT ON FUNCTION nirmana_elevation_guard_server_reconstructed_insert() IS
  'Requires exact session/current dedicated ingress for server receipts and exact control writer for every other receipt, then derives writer_identity.';

RESET ROLE;

DO $$
DECLARE
  campaign_relation text;
BEGIN
  IF EXISTS (
    SELECT 1 FROM pg_class AS relation
      JOIN pg_namespace AS namespace ON namespace.oid = relation.relnamespace
      JOIN pg_roles AS owner ON owner.oid = relation.relowner
     WHERE namespace.nspname = current_schema()
       AND relation.relname IN (
         'nirmana_elevation_campaign_definitions',
         'nirmana_elevation_campaign_events',
         'nirmana_elevation_asset_labels'
       )
       AND owner.rolname <> 'nirmana_evidence_owner'
  ) THEN
    RAISE EXCEPTION 'migration 633 could not transfer Nirmana campaign relation ownership';
  END IF;

  IF NOT has_schema_privilege('nirmana_evidence_owner', current_schema(), 'USAGE, CREATE') THEN
    RAISE EXCEPTION 'migration 633 could not grant the evidence owner required schema DDL privileges';
  END IF;

  IF EXISTS (
    SELECT 1 FROM pg_proc AS routine
      JOIN pg_namespace AS namespace ON namespace.oid = routine.pronamespace
      JOIN pg_roles AS owner ON owner.oid = routine.proowner
     WHERE namespace.nspname = current_schema()
       AND routine.proname IN (
         'nirmana_elevation_prevent_event_mutation',
         'nirmana_elevation_guard_definition_mutation',
         'nirmana_elevation_prevent_label_mutation',
         'nirmana_elevation_guard_server_reconstructed_insert',
         'nirmana_elevation_guard_control_writer',
         'nirmana_elevation_prevent_campaign_truncate'
       )
       AND owner.rolname <> 'nirmana_evidence_owner'
  ) THEN
    RAISE EXCEPTION 'migration 633 could not transfer Nirmana protective function ownership';
  END IF;

  IF pg_has_role('amjis_app', 'nirmana_evidence_owner', 'member')
     OR pg_has_role('nirmana_migrator', 'amjis_app', 'member')
     OR EXISTS (
       SELECT 1 FROM pg_roles
        WHERE rolname = 'amjis_app'
          AND (rolinherit OR rolcreatedb OR rolcreaterole OR rolsuper OR rolreplication OR rolbypassrls)
     )
     OR has_table_privilege('amjis_app', 'nirmana_elevation_campaign_definitions', 'INSERT, UPDATE, DELETE, TRUNCATE')
     OR has_table_privilege('amjis_app', 'nirmana_elevation_campaign_events', 'INSERT, UPDATE, DELETE, TRUNCATE')
     OR has_table_privilege('amjis_app', 'nirmana_elevation_asset_labels', 'INSERT, UPDATE, DELETE, TRUNCATE') THEN
    RAISE EXCEPTION 'migration 633 could not reduce amjis_app to read-only campaign access';
  END IF;

  IF EXISTS (
    SELECT 1 FROM pg_auth_members AS membership
      JOIN pg_roles AS role ON role.oid = membership.roleid OR role.oid = membership.member
     WHERE role.rolname = 'nirmana_campaign_control_writer'
  ) THEN
    RAISE EXCEPTION 'migration 633 could not remove campaign control writer role memberships';
  END IF;

  IF NOT has_table_privilege('nirmana_campaign_control_writer', 'nirmana_elevation_campaign_definitions', 'INSERT, UPDATE')
     OR NOT has_table_privilege('nirmana_campaign_control_writer', 'nirmana_elevation_campaign_events', 'INSERT')
     OR NOT has_table_privilege('nirmana_campaign_control_writer', 'nirmana_elevation_asset_labels', 'INSERT')
     OR NOT has_table_privilege('nirmana_evidence_ingress_writer', 'nirmana_elevation_campaign_events', 'INSERT') THEN
    RAISE EXCEPTION 'migration 633 could not establish dedicated Nirmana writer privileges';
  END IF;
END;
$$;

REVOKE nirmana_evidence_owner FROM nirmana_migrator;

DO $$
BEGIN
  IF pg_has_role('nirmana_migrator', 'nirmana_evidence_owner', 'member')
     OR pg_has_role('nirmana_migrator', 'amjis_app', 'member') THEN
    RAISE EXCEPTION 'migration 633 could not remove temporary nirmana_migrator authority';
  END IF;
END;
$$;
