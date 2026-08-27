/**
 * One-shot direct-legacy-owner handoff for Nirmana campaign evidence objects.
 * This must use the distinct deploy-only legacy-owner connection, never a
 * serving credential. It intentionally precedes migration 633, which merely
 * verifies this postcondition under nirmana_migrator.
 */
import { Pool } from 'pg'

const LEGACY_URL = 'NIRMANA_EVIDENCE_LEGACY_OWNER_DATABASE_URL'
const MIGRATOR_URL = 'NIRMANA_MIGRATOR_DATABASE_URL'

async function migration633Applied(databaseUrl: string): Promise<boolean> {
  const pool = new Pool({ connectionString: databaseUrl, max: 1 })
  try {
    const marker = await pool.query<{ applied: boolean }>(`
      SELECT EXISTS (SELECT 1 FROM _migrations_applied
        WHERE filename = '633_nirmana_evidence_writer_ownership.sql') AS applied
    `)
    return marker.rows[0]?.applied === true
  } finally {
    await pool.end()
  }
}

export async function runNirmanaEvidenceOwnershipPreflight(
  databaseUrl = process.env[LEGACY_URL],
  markerDatabaseUrl = process.env[MIGRATOR_URL],
): Promise<void> {
  // A normal replay is checked through the dedicated migration login first, so
  // the legacy-owner secret can be retired once 633 is recorded.  A missing
  // marker still requires the one-shot direct legacy-owner credential.
  if (markerDatabaseUrl && await migration633Applied(markerDatabaseUrl)) return
  if (!databaseUrl) throw new Error(`${LEGACY_URL} is required for the one-shot Nirmana ownership preflight.`)
  const pool = new Pool({ connectionString: databaseUrl, max: 1 })
  const client = await pool.connect()
  try {
    const actor = await client.query<{ session_user: string; current_user: string }>('SELECT session_user, current_user')
    if (actor.rows[0]?.session_user !== 'amjis_app' || actor.rows[0]?.current_user !== 'amjis_app') {
      throw new Error('Nirmana ownership preflight must authenticate directly as legacy owner amjis_app.')
    }
    if (await migration633Applied(databaseUrl)) return
    await client.query('BEGIN')
    await client.query(`
      DO $$ BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nirmana_evidence_owner') THEN
          CREATE ROLE nirmana_evidence_owner NOLOGIN NOINHERIT;
        END IF;
        IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nirmana_evidence_owner'
          AND (rolcanlogin OR rolsuper OR rolcreatedb OR rolcreaterole OR rolreplication OR rolbypassrls)) THEN
          RAISE EXCEPTION 'refusing elevated evidence owner';
        END IF;
        -- An existing owner with either incoming or outgoing memberships is
        -- already an administrative escape hatch.  Do not guess which edge
        -- was intended: refuse before the temporary legacy-owner edge below.
        IF EXISTS (
          SELECT 1 FROM pg_auth_members membership
          JOIN pg_roles role ON role.oid = membership.roleid OR role.oid = membership.member
          WHERE role.rolname = 'nirmana_evidence_owner'
        ) THEN
          RAISE EXCEPTION 'refusing evidence owner with pre-existing memberships';
        END IF;
        IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nirmana_migrator' AND rolcanlogin) THEN
          RAISE EXCEPTION 'nirmana_migrator must be provisioned before the ownership preflight';
        END IF;
        -- Role administration is performed while the legacy object owner is
        -- still current_user.  The NOLOGIN evidence owner cannot create this
        -- login after the handoff.
        IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nirmana_campaign_control_writer') THEN
          CREATE ROLE nirmana_campaign_control_writer LOGIN NOINHERIT NOCREATEDB NOCREATEROLE;
        ELSIF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nirmana_campaign_control_writer'
          AND (NOT rolcanlogin OR rolsuper OR rolcreatedb OR rolcreaterole OR rolreplication OR rolbypassrls)) THEN
          RAISE EXCEPTION 'refusing elevated control writer';
        END IF;
      END $$;
      GRANT nirmana_evidence_owner TO amjis_app;
      GRANT USAGE, CREATE ON SCHEMA public TO nirmana_evidence_owner;
      -- These operational relations remain owned outside the campaign
      -- boundary.  Grant their reviewed read-only contract while the legacy
      -- owner still owns them; the NOLOGIN campaign owner must never acquire
      -- authority over unrelated build/provenance tables merely to delegate a
      -- SELECT privilege.
      GRANT SELECT ON asset_registry, nirmana_elevation_monitor_observations, build_runs,
        build_run_assets, asset_provenance_receipts, asset_output_digest_specs,
        _migrations_applied TO nirmana_campaign_control_writer;
      GRANT SELECT, INSERT, UPDATE ON _migrations_applied TO nirmana_migrator;
      -- The legacy login cannot retain database ownership: that authority can
      -- otherwise reconfigure the schema boundary after its table DML has
      -- been revoked.  The direct database owner may transfer ownership to
      -- its temporary NOLOGIN member without granting a durable membership.
      DO $$ BEGIN
        EXECUTE format('ALTER DATABASE %I OWNER TO nirmana_evidence_owner', current_database());
      END $$;
      ALTER TABLE nirmana_elevation_campaign_definitions OWNER TO nirmana_evidence_owner;
      ALTER TABLE nirmana_elevation_campaign_events OWNER TO nirmana_evidence_owner;
      ALTER TABLE nirmana_elevation_asset_labels OWNER TO nirmana_evidence_owner;
      ALTER FUNCTION nirmana_elevation_prevent_event_mutation() OWNER TO nirmana_evidence_owner;
      ALTER FUNCTION nirmana_elevation_guard_definition_mutation() OWNER TO nirmana_evidence_owner;
      ALTER FUNCTION nirmana_elevation_prevent_label_mutation() OWNER TO nirmana_evidence_owner;
      ALTER FUNCTION nirmana_elevation_guard_server_reconstructed_insert() OWNER TO nirmana_evidence_owner;
      SET LOCAL ROLE nirmana_evidence_owner;
      ALTER TABLE nirmana_elevation_campaign_events ADD COLUMN IF NOT EXISTS writer_identity text;
      REVOKE ALL PRIVILEGES ON TABLE nirmana_elevation_campaign_definitions,
        nirmana_elevation_campaign_events, nirmana_elevation_asset_labels FROM PUBLIC;
      REVOKE ALL PRIVILEGES ON TABLE nirmana_elevation_campaign_definitions,
        nirmana_elevation_campaign_events, nirmana_elevation_asset_labels FROM nirmana_campaign_control_writer;
      GRANT USAGE ON SCHEMA public TO nirmana_campaign_control_writer;
      GRANT SELECT, INSERT, UPDATE ON nirmana_elevation_campaign_definitions TO nirmana_campaign_control_writer;
      GRANT SELECT, INSERT ON nirmana_elevation_campaign_events TO nirmana_campaign_control_writer;
      GRANT SELECT, INSERT ON nirmana_elevation_asset_labels TO nirmana_campaign_control_writer;
      -- This is the exhaustive reader contract for the control-writer paths:
      -- definition validation, baseline/freeze validation, receipt provenance,
      -- and build-run authorization.  New reads require an explicit reviewed
      -- addition here rather than inheriting generic application privileges.
      CREATE OR REPLACE FUNCTION nirmana_elevation_guard_server_reconstructed_insert()
      RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN
        IF session_user <> current_user THEN RAISE EXCEPTION 'Nirmana evidence writers may not cross roles'; END IF;
        IF NEW.source_kind = 'server_reconstructed' THEN
          IF session_user <> 'nirmana_evidence_ingress_writer' THEN RAISE EXCEPTION 'server evidence requires ingress writer'; END IF;
        ELSIF session_user <> 'nirmana_campaign_control_writer' THEN
          RAISE EXCEPTION 'non-server evidence requires control writer';
        END IF;
        NEW.writer_identity := session_user; RETURN NEW;
      END $$;
      DROP TRIGGER IF EXISTS nirmana_elevation_events_server_writer ON nirmana_elevation_campaign_events;
      CREATE TRIGGER nirmana_elevation_events_server_writer BEFORE INSERT ON nirmana_elevation_campaign_events
        FOR EACH ROW EXECUTE FUNCTION nirmana_elevation_guard_server_reconstructed_insert();
      CREATE OR REPLACE FUNCTION nirmana_elevation_guard_control_writer()
      RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN
        IF session_user <> current_user OR session_user <> 'nirmana_campaign_control_writer' THEN
          RAISE EXCEPTION 'campaign definition and label writes require the dedicated control writer without role crossing';
        END IF;
        IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
        RETURN NEW;
      END $$;
      CREATE OR REPLACE FUNCTION nirmana_elevation_prevent_campaign_truncate()
      RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN
        RAISE EXCEPTION 'Nirmana campaign ownership tables may not be truncated';
      END $$;
      DROP TRIGGER IF EXISTS nirmana_elevation_definitions_control_writer ON nirmana_elevation_campaign_definitions;
      CREATE TRIGGER nirmana_elevation_definitions_control_writer
        BEFORE INSERT OR UPDATE OR DELETE ON nirmana_elevation_campaign_definitions
        FOR EACH ROW EXECUTE FUNCTION nirmana_elevation_guard_control_writer();
      DROP TRIGGER IF EXISTS nirmana_elevation_labels_control_writer ON nirmana_elevation_asset_labels;
      CREATE TRIGGER nirmana_elevation_labels_control_writer
        BEFORE INSERT ON nirmana_elevation_asset_labels
        FOR EACH ROW EXECUTE FUNCTION nirmana_elevation_guard_control_writer();
      DROP TRIGGER IF EXISTS nirmana_elevation_definitions_no_truncate ON nirmana_elevation_campaign_definitions;
      CREATE TRIGGER nirmana_elevation_definitions_no_truncate
        BEFORE TRUNCATE ON nirmana_elevation_campaign_definitions
        FOR EACH STATEMENT EXECUTE FUNCTION nirmana_elevation_prevent_campaign_truncate();
      DROP TRIGGER IF EXISTS nirmana_elevation_events_no_truncate ON nirmana_elevation_campaign_events;
      CREATE TRIGGER nirmana_elevation_events_no_truncate
        BEFORE TRUNCATE ON nirmana_elevation_campaign_events
        FOR EACH STATEMENT EXECUTE FUNCTION nirmana_elevation_prevent_campaign_truncate();
      GRANT USAGE, CREATE ON SCHEMA public TO nirmana_migrator;
      -- The public schema normally conveys CREATE through PUBLIC. Removing only the
      -- CREATE bit preserves ordinary object lookup while preventing the
      -- generic runtime (or any other unreviewed login) from creating a
      -- replacement campaign object in the transferred schema.
      REVOKE CREATE ON SCHEMA public FROM PUBLIC;
      REVOKE ALL PRIVILEGES ON TABLE nirmana_elevation_campaign_definitions,
        nirmana_elevation_campaign_events, nirmana_elevation_asset_labels FROM amjis_app;
      GRANT SELECT ON TABLE nirmana_elevation_campaign_definitions,
        nirmana_elevation_campaign_events, nirmana_elevation_asset_labels TO amjis_app;
      RESET ROLE;
      ALTER SCHEMA public OWNER TO nirmana_evidence_owner;
      REVOKE nirmana_evidence_owner FROM amjis_app;
      ALTER ROLE amjis_app NOINHERIT NOCREATEDB NOCREATEROLE;
      REVOKE ALL PRIVILEGES ON SCHEMA public FROM amjis_app;
      GRANT USAGE ON SCHEMA public TO amjis_app;
    `)
    const memberCount = await client.query<{ count: string }>(`SELECT COUNT(*)::text AS count FROM pg_auth_members m
      JOIN pg_roles r ON r.oid = m.roleid OR r.oid = m.member WHERE r.rolname = 'nirmana_evidence_owner'`)
    if (memberCount.rows[0]?.count !== '0') throw new Error('Evidence owner membership cleanup did not converge.')
    const genericOwnership = await client.query<{ count: string }>(`
      SELECT COUNT(*)::text AS count FROM pg_database database
      JOIN pg_roles owner ON owner.oid = database.datdba
      WHERE database.datname = current_database() AND owner.rolname = 'amjis_app'
    `)
    if (genericOwnership.rows[0]?.count !== '0') throw new Error('Legacy application database ownership cleanup did not converge.')
    await client.query('COMMIT')
  } catch (error) {
    await client.query('ROLLBACK').catch(() => {})
    // A fresh committed cleanup is intentional: an outer rollback must never
    // leave a temporary owner membership from a failed preflight attempt.
    await client.query('REVOKE nirmana_evidence_owner FROM amjis_app').catch(() => {})
    throw error
  } finally {
    client.release()
    await pool.end()
  }
}

if (require.main === module) {
  runNirmanaEvidenceOwnershipPreflight().catch((error) => {
    console.error(error)
    process.exitCode = 1
  })
}
