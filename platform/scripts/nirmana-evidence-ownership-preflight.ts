/** One-shot direct-legacy-owner handoff into the isolated Nirmana evidence schema. */
import { Pool, type PoolClient } from 'pg'

const LEGACY_URL = 'NIRMANA_EVIDENCE_LEGACY_OWNER_DATABASE_URL'
const SCHEMA = 'nirmana_evidence'
const MARKER = '633_nirmana_evidence_writer_ownership.sql'
const TABLES = ['nirmana_elevation_campaign_definitions', 'nirmana_elevation_campaign_events', 'nirmana_elevation_asset_labels']
const FUNCTIONS = [
  'nirmana_elevation_prevent_event_mutation', 'nirmana_elevation_guard_definition_mutation',
  'nirmana_elevation_prevent_label_mutation', 'nirmana_elevation_guard_server_reconstructed_insert',
  'nirmana_elevation_guard_control_writer', 'nirmana_elevation_prevent_campaign_truncate',
]

async function markerApplied(databaseUrl: string): Promise<boolean> {
  const pool = new Pool({ connectionString: databaseUrl, max: 1 })
  try {
    const result = await pool.query<{ applied: boolean }>(`SELECT EXISTS (SELECT 1 FROM public._migrations_applied WHERE filename = $1) AS applied`, [MARKER])
    return result.rows[0]?.applied === true
  } finally { await pool.end() }
}

type HandoffState = 'initial' | 'handed_off_unmarked' | 'partial'

async function handoffState(client: PoolClient): Promise<HandoffState> {
  const result = await client.query<{ complete: boolean; touched: boolean }>(`
    WITH expected_tables(name) AS (SELECT unnest($1::text[])), expected_functions(name) AS (SELECT unnest($2::text[]))
    SELECT
      EXISTS (SELECT 1 FROM pg_namespace namespace JOIN pg_roles owner ON owner.oid = namespace.nspowner WHERE namespace.nspname = $3 AND owner.rolname = 'nirmana_evidence_owner')
      AND NOT EXISTS (SELECT 1 FROM expected_tables expected LEFT JOIN pg_class relation ON relation.relname = expected.name LEFT JOIN pg_namespace namespace ON namespace.oid = relation.relnamespace LEFT JOIN pg_roles owner ON owner.oid = relation.relowner WHERE namespace.nspname IS DISTINCT FROM $3 OR owner.rolname IS DISTINCT FROM 'nirmana_evidence_owner')
      AND NOT EXISTS (SELECT 1 FROM expected_functions expected LEFT JOIN pg_proc procedure ON procedure.proname = expected.name LEFT JOIN pg_namespace namespace ON namespace.oid = procedure.pronamespace LEFT JOIN pg_roles owner ON owner.oid = procedure.proowner WHERE namespace.nspname IS DISTINCT FROM $3 OR owner.rolname IS DISTINCT FROM 'nirmana_evidence_owner')
      AND NOT EXISTS (SELECT 1 FROM pg_auth_members membership JOIN pg_roles role ON role.oid = membership.roleid OR role.oid = membership.member WHERE role.rolname = 'nirmana_evidence_owner')
      AND NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'amjis_app' AND (rolcreatedb OR rolcreaterole))
      AND NOT has_schema_privilege('amjis_app', $3, 'CREATE') AS complete,
      EXISTS (SELECT 1 FROM pg_namespace WHERE nspname = $3)
      OR EXISTS (SELECT 1 FROM pg_class relation JOIN pg_roles owner ON owner.oid = relation.relowner WHERE relation.relname = ANY($1::text[]) AND owner.rolname = 'nirmana_evidence_owner') AS touched
  `, [TABLES, FUNCTIONS, SCHEMA])
  if (result.rows[0]?.complete) return 'handed_off_unmarked'
  return result.rows[0]?.touched ? 'partial' : 'initial'
}

export async function runNirmanaEvidenceOwnershipPreflight(databaseUrl = process.env[LEGACY_URL]): Promise<void> {
  if (!databaseUrl) throw new Error(`${LEGACY_URL} is required for the one-shot Nirmana ownership preflight.`)
  // A minimally provisioned marker login cannot read the tracker before this handoff.
  if (await markerApplied(databaseUrl)) return
  const pool = new Pool({ connectionString: databaseUrl, max: 1 })
  const client = await pool.connect()
  try {
    const actor = await client.query<{ session_user: string; current_user: string }>('SELECT session_user, current_user')
    if (actor.rows[0]?.session_user !== 'amjis_app' || actor.rows[0]?.current_user !== 'amjis_app') throw new Error('Nirmana ownership preflight must authenticate directly as legacy owner amjis_app.')
    if (await markerApplied(databaseUrl)) return
    const state = await handoffState(client)
    if (state === 'handed_off_unmarked') return
    if (state === 'partial') throw new Error('Nirmana ownership preflight found a partial handoff without marker; refusing recovery by mutation.')

    await client.query('BEGIN')
    await client.query(`
      DO $$ BEGIN
        IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'amjis_app' AND (rolsuper OR rolreplication OR rolbypassrls)) THEN RAISE EXCEPTION 'refusing elevated generic application role'; END IF;
        IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nirmana_evidence_owner') THEN CREATE ROLE nirmana_evidence_owner NOLOGIN NOINHERIT; END IF;
        IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nirmana_evidence_owner' AND (rolcanlogin OR rolsuper OR rolcreatedb OR rolcreaterole OR rolreplication OR rolbypassrls)) THEN RAISE EXCEPTION 'refusing elevated evidence owner'; END IF;
        IF EXISTS (SELECT 1 FROM pg_auth_members membership JOIN pg_roles role ON role.oid = membership.roleid OR role.oid = membership.member WHERE role.rolname = 'nirmana_evidence_owner') THEN RAISE EXCEPTION 'refusing evidence owner with pre-existing memberships'; END IF;
        IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nirmana_migrator') THEN RAISE EXCEPTION 'nirmana_migrator must be provisioned before the ownership preflight'; END IF;
        IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nirmana_migrator' AND (NOT rolcanlogin OR rolsuper OR rolcreatedb OR rolcreaterole OR rolreplication OR rolbypassrls)) THEN RAISE EXCEPTION 'refusing elevated nirmana_migrator'; END IF;
        IF EXISTS (SELECT 1 FROM pg_auth_members membership JOIN pg_roles role ON role.oid = membership.roleid OR role.oid = membership.member WHERE role.rolname = 'nirmana_migrator') THEN RAISE EXCEPTION 'refusing nirmana_migrator with memberships'; END IF;
        IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nirmana_evidence_ingress_writer') THEN RAISE EXCEPTION 'nirmana_evidence_ingress_writer must be provisioned by migration 632 before the ownership preflight'; END IF;
        IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nirmana_evidence_ingress_writer' AND (NOT rolcanlogin OR rolinherit OR rolsuper OR rolcreatedb OR rolcreaterole OR rolreplication OR rolbypassrls)) THEN RAISE EXCEPTION 'refusing non-normalized evidence ingress writer'; END IF;
        IF EXISTS (SELECT 1 FROM pg_auth_members membership JOIN pg_roles role ON role.oid = membership.roleid OR role.oid = membership.member WHERE role.rolname = 'nirmana_evidence_ingress_writer') THEN RAISE EXCEPTION 'refusing evidence ingress writer with memberships'; END IF;
        IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nirmana_campaign_control_writer') THEN CREATE ROLE nirmana_campaign_control_writer LOGIN NOINHERIT NOCREATEDB NOCREATEROLE; END IF;
        IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nirmana_campaign_control_writer' AND (NOT rolcanlogin OR rolsuper OR rolcreatedb OR rolcreaterole OR rolreplication OR rolbypassrls)) THEN RAISE EXCEPTION 'refusing elevated control writer'; END IF;
        IF EXISTS (SELECT 1 FROM pg_auth_members membership JOIN pg_roles role ON role.oid = membership.roleid OR role.oid = membership.member WHERE role.rolname = 'nirmana_campaign_control_writer') THEN RAISE EXCEPTION 'refusing control writer with memberships'; END IF;
      END $$;
      -- The directly authenticated legacy owner needs ADMIN OPTION only long
      -- enough to remove this temporary membership before commit.  No role
      -- crossing is used by runtime writers.
      GRANT nirmana_evidence_owner TO amjis_app WITH ADMIN OPTION;
      CREATE SCHEMA nirmana_evidence AUTHORIZATION nirmana_evidence_owner;
      GRANT USAGE, CREATE ON SCHEMA nirmana_evidence TO nirmana_evidence_owner;
      -- PostgreSQL requires the incoming owner to hold CREATE on the source
      -- schema while changing object ownership; revoke it immediately after
      -- every campaign object has moved to the dedicated schema.
      GRANT USAGE, CREATE ON SCHEMA public TO nirmana_evidence_owner;
      GRANT SELECT, INSERT ON public._migrations_applied TO nirmana_migrator;
      GRANT SELECT ON public.asset_registry, public.nirmana_elevation_monitor_observations, public.build_runs, public.build_run_assets, public.asset_provenance_receipts, public.asset_output_digest_specs, public._migrations_applied TO nirmana_campaign_control_writer;
      ALTER TABLE public.nirmana_elevation_campaign_definitions OWNER TO nirmana_evidence_owner;
      ALTER TABLE public.nirmana_elevation_campaign_events OWNER TO nirmana_evidence_owner;
      ALTER TABLE public.nirmana_elevation_asset_labels OWNER TO nirmana_evidence_owner;
      ALTER FUNCTION public.nirmana_elevation_prevent_event_mutation() OWNER TO nirmana_evidence_owner;
      ALTER FUNCTION public.nirmana_elevation_guard_definition_mutation() OWNER TO nirmana_evidence_owner;
      ALTER FUNCTION public.nirmana_elevation_prevent_label_mutation() OWNER TO nirmana_evidence_owner;
      ALTER FUNCTION public.nirmana_elevation_guard_server_reconstructed_insert() OWNER TO nirmana_evidence_owner;
      SET LOCAL ROLE nirmana_evidence_owner;
      ALTER TABLE public.nirmana_elevation_campaign_definitions SET SCHEMA nirmana_evidence;
      ALTER TABLE public.nirmana_elevation_campaign_events SET SCHEMA nirmana_evidence;
      ALTER TABLE public.nirmana_elevation_asset_labels SET SCHEMA nirmana_evidence;
      ALTER FUNCTION public.nirmana_elevation_prevent_event_mutation() SET SCHEMA nirmana_evidence;
      ALTER FUNCTION public.nirmana_elevation_guard_definition_mutation() SET SCHEMA nirmana_evidence;
      ALTER FUNCTION public.nirmana_elevation_prevent_label_mutation() SET SCHEMA nirmana_evidence;
      ALTER FUNCTION public.nirmana_elevation_guard_server_reconstructed_insert() SET SCHEMA nirmana_evidence;
      RESET ROLE;
      REVOKE CREATE ON SCHEMA public FROM nirmana_evidence_owner;
      -- Avoid a PUBLIC CREATE grant becoming an indirect DDL path for any
      -- dedicated login.  amjis_app remains the legacy public-schema owner
      -- needed by the repository's ordinary migration runner.
      REVOKE CREATE ON SCHEMA public FROM PUBLIC, nirmana_evidence_owner, nirmana_evidence_ingress_writer, nirmana_campaign_control_writer, nirmana_migrator;
      GRANT USAGE ON SCHEMA public TO nirmana_evidence_ingress_writer, nirmana_campaign_control_writer, nirmana_migrator;
      SET LOCAL ROLE nirmana_evidence_owner;
      SET LOCAL search_path TO nirmana_evidence, public;
      ALTER TABLE nirmana_elevation_campaign_events ADD COLUMN IF NOT EXISTS writer_identity text;
      -- Table-level REVOKE does not clear historical column grants.  Remove
      -- those explicitly before granting the three exact writer envelopes.
      DO $$ DECLARE relation_name text; column_name text; BEGIN
        FOR relation_name, column_name IN
          SELECT relation.relname, attribute.attname
            FROM pg_class relation
            JOIN pg_attribute attribute ON attribute.attrelid = relation.oid
           WHERE relation.relnamespace = 'nirmana_evidence'::regnamespace
             AND relation.relname IN ('nirmana_elevation_campaign_definitions', 'nirmana_elevation_campaign_events', 'nirmana_elevation_asset_labels')
             AND attribute.attnum > 0 AND NOT attribute.attisdropped
        LOOP
          EXECUTE format('REVOKE ALL PRIVILEGES (%I) ON TABLE nirmana_evidence.%I FROM PUBLIC, amjis_app, nirmana_evidence_ingress_writer, nirmana_campaign_control_writer, nirmana_migrator', column_name, relation_name);
        END LOOP;
      END $$;
      REVOKE ALL PRIVILEGES ON SCHEMA nirmana_evidence FROM PUBLIC, amjis_app, nirmana_evidence_ingress_writer, nirmana_campaign_control_writer, nirmana_migrator;
      GRANT USAGE ON SCHEMA nirmana_evidence TO amjis_app, nirmana_evidence_ingress_writer, nirmana_campaign_control_writer;
      REVOKE ALL PRIVILEGES ON TABLE nirmana_elevation_campaign_definitions, nirmana_elevation_campaign_events, nirmana_elevation_asset_labels FROM PUBLIC, amjis_app, nirmana_evidence_ingress_writer, nirmana_campaign_control_writer, nirmana_migrator;
      GRANT SELECT ON nirmana_elevation_campaign_definitions, nirmana_elevation_campaign_events, nirmana_elevation_asset_labels TO amjis_app;
      GRANT SELECT, INSERT, UPDATE ON nirmana_elevation_campaign_definitions TO nirmana_campaign_control_writer;
      GRANT SELECT, INSERT ON nirmana_elevation_campaign_events, nirmana_elevation_asset_labels TO nirmana_campaign_control_writer;
      GRANT SELECT ON nirmana_elevation_campaign_definitions, nirmana_elevation_campaign_events TO nirmana_evidence_ingress_writer;
      GRANT INSERT ON nirmana_elevation_campaign_events TO nirmana_evidence_ingress_writer;
      CREATE OR REPLACE FUNCTION nirmana_elevation_guard_server_reconstructed_insert() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN
        IF session_user <> current_user THEN RAISE EXCEPTION 'Nirmana evidence writers may not cross roles'; END IF;
        IF NEW.source_kind = 'server_reconstructed' THEN IF session_user <> 'nirmana_evidence_ingress_writer' THEN RAISE EXCEPTION 'server evidence requires ingress writer'; END IF;
        ELSIF session_user <> 'nirmana_campaign_control_writer' THEN RAISE EXCEPTION 'non-server evidence requires control writer'; END IF;
        NEW.writer_identity := session_user; RETURN NEW;
      END $$;
      CREATE OR REPLACE FUNCTION nirmana_elevation_guard_control_writer() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN
        IF session_user <> current_user OR session_user <> 'nirmana_campaign_control_writer' THEN RAISE EXCEPTION 'campaign definition and label writes require the dedicated control writer without role crossing'; END IF;
        IF TG_OP = 'DELETE' THEN RETURN OLD; END IF; RETURN NEW;
      END $$;
      CREATE OR REPLACE FUNCTION nirmana_elevation_prevent_campaign_truncate() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'Nirmana campaign ownership tables may not be truncated'; END $$;
      DROP TRIGGER IF EXISTS nirmana_elevation_events_server_writer ON nirmana_elevation_campaign_events;
      CREATE TRIGGER nirmana_elevation_events_server_writer BEFORE INSERT ON nirmana_elevation_campaign_events FOR EACH ROW EXECUTE FUNCTION nirmana_elevation_guard_server_reconstructed_insert();
      DROP TRIGGER IF EXISTS nirmana_elevation_definitions_control_writer ON nirmana_elevation_campaign_definitions;
      CREATE TRIGGER nirmana_elevation_definitions_control_writer BEFORE INSERT OR UPDATE OR DELETE ON nirmana_elevation_campaign_definitions FOR EACH ROW EXECUTE FUNCTION nirmana_elevation_guard_control_writer();
      DROP TRIGGER IF EXISTS nirmana_elevation_labels_control_writer ON nirmana_elevation_asset_labels;
      CREATE TRIGGER nirmana_elevation_labels_control_writer BEFORE INSERT ON nirmana_elevation_asset_labels FOR EACH ROW EXECUTE FUNCTION nirmana_elevation_guard_control_writer();
      DROP TRIGGER IF EXISTS nirmana_elevation_definitions_no_truncate ON nirmana_elevation_campaign_definitions;
      CREATE TRIGGER nirmana_elevation_definitions_no_truncate BEFORE TRUNCATE ON nirmana_elevation_campaign_definitions FOR EACH STATEMENT EXECUTE FUNCTION nirmana_elevation_prevent_campaign_truncate();
      DROP TRIGGER IF EXISTS nirmana_elevation_events_no_truncate ON nirmana_elevation_campaign_events;
      CREATE TRIGGER nirmana_elevation_events_no_truncate BEFORE TRUNCATE ON nirmana_elevation_campaign_events FOR EACH STATEMENT EXECUTE FUNCTION nirmana_elevation_prevent_campaign_truncate();
      RESET ROLE;
      REVOKE nirmana_evidence_owner FROM amjis_app;
      ALTER ROLE amjis_app NOINHERIT NOCREATEDB NOCREATEROLE;
    `)
    const memberships = await client.query<{ count: string }>(`SELECT count(*)::text AS count FROM pg_auth_members membership JOIN pg_roles role ON role.oid = membership.roleid OR role.oid = membership.member WHERE role.rolname = 'nirmana_evidence_owner'`)
    if (memberships.rows[0]?.count !== '0') throw new Error('Evidence owner membership cleanup did not converge.')
    await client.query('COMMIT')
  } catch (error) {
    await client.query('ROLLBACK').catch(() => {})
    await client.query('REVOKE nirmana_evidence_owner FROM amjis_app').catch(() => {})
    throw error
  } finally { client.release(); await pool.end() }
}

if (require.main === module) runNirmanaEvidenceOwnershipPreflight().catch((error) => { console.error(error); process.exitCode = 1 })
