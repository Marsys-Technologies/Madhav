/** One-shot direct-legacy-owner handoff into the isolated Nirmana evidence schema. */
import { Pool, type PoolClient } from 'pg'

const LEGACY_URL = 'NIRMANA_EVIDENCE_LEGACY_OWNER_DATABASE_URL'
const CONTROL_URL = 'NIRMANA_CAMPAIGN_CONTROL_DATABASE_URL'
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

async function assertControlWriterAuthentication(databaseUrl = process.env[CONTROL_URL]): Promise<void> {
  if (!databaseUrl) throw new Error(`${CONTROL_URL} is required: the campaign control writer must be secret-backed and preprovisioned before ownership handoff.`)
  const pool = new Pool({ connectionString: databaseUrl, max: 1 })
  try {
    const actor = await pool.query<{ session_user: string; current_user: string }>('SELECT session_user, current_user')
    if (actor.rows[0]?.session_user !== 'nirmana_campaign_control_writer'
      || actor.rows[0]?.current_user !== 'nirmana_campaign_control_writer') {
      throw new Error(`${CONTROL_URL} must authenticate directly as nirmana_campaign_control_writer.`)
    }
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
      -- A legacy direct database-owner membership is the one exceptional
      -- bootstrap path.  It must be gone before an unmarked handoff can be
      -- replayed: NOINHERIT alone still permits SET ROLE.
      AND NOT EXISTS (
        SELECT 1 FROM pg_auth_members membership
          JOIN pg_roles parent ON parent.oid = membership.roleid
          JOIN pg_roles member ON member.oid = membership.member
         WHERE parent.rolname = 'amjis_app' OR member.rolname = 'amjis_app'
      )
      AND NOT EXISTS (
        SELECT 1 FROM pg_database database
         WHERE database.datname = current_database()
           AND (database.datdba = 'amjis_app'::regrole
             OR pg_has_role('amjis_app', database.datdba, 'MEMBER'))
      )
      AND NOT has_database_privilege('amjis_app', current_database(), 'CREATE')
      AND NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'amjis_app' AND (rolinherit OR rolcreatedb OR rolcreaterole OR rolsuper OR rolreplication OR rolbypassrls))
      AND NOT has_schema_privilege('amjis_app', $3, 'CREATE') AS complete,
      EXISTS (SELECT 1 FROM pg_namespace WHERE nspname = $3)
      OR EXISTS (SELECT 1 FROM pg_class relation JOIN pg_roles owner ON owner.oid = relation.relowner WHERE relation.relname = ANY($1::text[]) AND owner.rolname = 'nirmana_evidence_owner') AS touched
  `, [TABLES, FUNCTIONS, SCHEMA])
  if (result.rows[0]?.complete) return 'handed_off_unmarked'
  return result.rows[0]?.touched ? 'partial' : 'initial'
}

export async function runNirmanaEvidenceOwnershipPreflight(databaseUrl = process.env[LEGACY_URL]): Promise<void> {
  if (!databaseUrl) throw new Error(`${LEGACY_URL} is required for the one-shot Nirmana ownership preflight.`)
  const pool = new Pool({ connectionString: databaseUrl, max: 1 })
  const client = await pool.connect()
  try {
    const actor = await client.query<{ session_user: string; current_user: string }>('SELECT session_user, current_user')
    if (actor.rows[0]?.session_user !== 'amjis_app' || actor.rows[0]?.current_user !== 'amjis_app') throw new Error('Nirmana ownership preflight must authenticate directly as legacy owner amjis_app.')
    if (await markerApplied(databaseUrl)) {
      if (await handoffState(client) !== 'handed_off_unmarked') {
        throw new Error('Nirmana ownership marker exists but the final evidence boundary no longer converges.')
      }
      return
    }
    const state = await handoffState(client)
    if (state === 'handed_off_unmarked') return
    if (state === 'partial') throw new Error('Nirmana ownership preflight found a partial handoff without marker; refusing recovery by mutation.')
    await assertControlWriterAuthentication()

    await client.query('BEGIN')
    await client.query(`
      DO $$ BEGIN
        -- The only allowed initial generic-role edge is a direct membership
        -- in the current database owner.  This is the managed Cloud SQL
        -- topology we can close transaction-locally; every other parent,
        -- child, or indirect route is an ambiguous escalation path.
        IF EXISTS (
          SELECT 1
            FROM pg_auth_members membership
            JOIN pg_roles app ON app.oid = membership.member
            JOIN pg_database database ON database.datname = current_database()
           WHERE app.rolname = 'amjis_app'
             AND NOT (membership.roleid = database.datdba)
        ) OR EXISTS (
          SELECT 1 FROM pg_auth_members membership
            JOIN pg_roles app ON app.oid = membership.roleid
           WHERE app.rolname = 'amjis_app'
        ) THEN
          RAISE EXCEPTION 'refusing unexpected amjis_app role membership topology';
        END IF;
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
        IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nirmana_campaign_control_writer') THEN RAISE EXCEPTION 'nirmana_campaign_control_writer must be secret-backed and preprovisioned before the ownership preflight'; END IF;
        IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nirmana_campaign_control_writer' AND (NOT rolcanlogin OR rolsuper OR rolcreatedb OR rolcreaterole OR rolreplication OR rolbypassrls)) THEN RAISE EXCEPTION 'refusing elevated control writer'; END IF;
        IF EXISTS (SELECT 1 FROM pg_auth_members membership JOIN pg_roles role ON role.oid = membership.roleid OR role.oid = membership.member WHERE role.rolname = 'nirmana_campaign_control_writer') THEN RAISE EXCEPTION 'refusing control writer with memberships'; END IF;
      END $$;
      -- Cloud SQL keeps the database owner/provider administrator able to
      -- CREATE in public even after a PUBLIC revoke.  If amjis_app has the
      -- one permitted *direct* owner membership, use it only inside this
      -- transaction to close PostgreSQL's hard-wired PUBLIC defaults for
      -- that owner, then reset immediately.  No membership is created here.
      DO $$
      DECLARE database_owner name; direct_owner_membership boolean;
      BEGIN
        SELECT owner.rolname,
               EXISTS (SELECT 1 FROM pg_auth_members membership WHERE membership.roleid = database.datdba AND membership.member = app.oid)
          INTO database_owner, direct_owner_membership
          FROM pg_database database
          JOIN pg_roles owner ON owner.oid = database.datdba
          JOIN pg_roles app ON app.rolname = 'amjis_app'
         WHERE database.datname = current_database();
        IF direct_owner_membership THEN
          IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = database_owner AND rolcreatedb AND rolcreaterole) THEN
            RAISE EXCEPTION 'refusing non-provider database owner delegation';
          END IF;
          EXECUTE format('SET LOCAL ROLE %I', database_owner);
          IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nirmana_evidence_owner') THEN
            CREATE ROLE nirmana_evidence_owner NOLOGIN NOINHERIT;
          END IF;
          -- This membership exists only for the object-owner transfer below
          -- and is explicitly revoked before the transaction can commit.
          GRANT nirmana_evidence_owner TO amjis_app WITH ADMIN OPTION;
          ALTER DEFAULT PRIVILEGES REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC;
          ALTER DEFAULT PRIVILEGES REVOKE USAGE ON TYPES FROM PUBLIC;
          RESET ROLE;
        END IF;
      END $$;
      -- Remove direct stale grants before constructing the two explicit
      -- non-owner envelopes.  Effective grants inherited from PUBLIC are
      -- attested below by migration 633 and fail closed rather than being
      -- silently treated as part of either writer's contract.
      DO $$ DECLARE target_role text; schema_name text; relation_name text; column_name text; BEGIN
        FOREACH target_role IN ARRAY ARRAY['nirmana_campaign_control_writer', 'nirmana_migrator'] LOOP
          EXECUTE format('REVOKE ALL PRIVILEGES ON DATABASE %I FROM %I', current_database(), target_role);
          FOR schema_name IN SELECT nspname FROM pg_namespace WHERE nspname !~ '^pg_' AND nspname <> 'information_schema' LOOP
            EXECUTE format('REVOKE ALL PRIVILEGES ON SCHEMA %I FROM %I', schema_name, target_role);
            EXECUTE format('REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA %I FROM %I', schema_name, target_role);
            EXECUTE format('REVOKE ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA %I FROM %I', schema_name, target_role);
            FOR relation_name, column_name IN
              SELECT relation.relname, attribute.attname
                FROM pg_class relation
                JOIN pg_attribute attribute ON attribute.attrelid = relation.oid
                JOIN pg_namespace namespace ON namespace.oid = relation.relnamespace
               WHERE namespace.nspname = schema_name
                 AND relation.relkind IN ('r', 'p', 'v', 'm', 'f')
                 AND attribute.attnum > 0 AND NOT attribute.attisdropped
            LOOP
              EXECUTE format('REVOKE ALL PRIVILEGES (%I) ON TABLE %I.%I FROM %I', column_name, schema_name, relation_name, target_role);
            END LOOP;
          END LOOP;
        END LOOP;
      END $$;
      -- Default ACLs are a future-object grant channel. Normalize every
      -- default ACL made by the direct legacy owner before it loses control
      -- of campaign objects. Defaults from another grantor are attested
      -- below and fail closed when they could affect a protected writer.
      DO $$
      DECLARE default_acl record; object_kind text; scope_clause text;
      BEGIN
        FOR default_acl IN
          SELECT defaults.defaclobjtype, namespace.nspname AS schema_name
            FROM pg_default_acl defaults
            JOIN pg_roles grantor ON grantor.oid = defaults.defaclrole
            LEFT JOIN pg_namespace namespace ON namespace.oid = defaults.defaclnamespace
           WHERE grantor.rolname = 'amjis_app'
        LOOP
          object_kind := CASE default_acl.defaclobjtype
            WHEN 'r' THEN 'TABLES' WHEN 'S' THEN 'SEQUENCES'
            WHEN 'f' THEN 'FUNCTIONS' WHEN 'T' THEN 'TYPES'
            WHEN 'n' THEN 'SCHEMAS' ELSE NULL
          END;
          IF object_kind IS NULL THEN
            RAISE EXCEPTION 'refusing unknown amjis_app default ACL object kind %', default_acl.defaclobjtype;
          END IF;
          scope_clause := CASE WHEN default_acl.schema_name IS NULL OR default_acl.defaclobjtype = 'n'
            THEN '' ELSE format(' IN SCHEMA %I', default_acl.schema_name) END;
          EXECUTE format(
            'ALTER DEFAULT PRIVILEGES FOR ROLE amjis_app%s REVOKE ALL PRIVILEGES ON %s FROM PUBLIC, nirmana_evidence_owner, nirmana_evidence_ingress_writer, nirmana_campaign_control_writer, nirmana_migrator',
            scope_clause, object_kind
          );
        END LOOP;
      END $$;
      -- pg_default_acl omits PostgreSQL's built-in PUBLIC EXECUTE (functions)
      -- and PUBLIC USAGE (types) defaults. Revoke them unconditionally; doing
      -- this only when a catalog row exists would leave fresh grantors open.
      ALTER DEFAULT PRIVILEGES FOR ROLE amjis_app REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC;
      ALTER DEFAULT PRIVILEGES FOR ROLE amjis_app REVOKE USAGE ON TYPES FROM PUBLIC;
      CREATE SCHEMA nirmana_evidence AUTHORIZATION nirmana_evidence_owner;
      GRANT USAGE, CREATE ON SCHEMA nirmana_evidence TO nirmana_evidence_owner;
      -- PostgreSQL requires the incoming owner to hold CREATE on the source
      -- schema while changing object ownership; revoke it immediately after
      -- every campaign object has moved to the dedicated schema.
      GRANT USAGE, CREATE ON SCHEMA public TO nirmana_evidence_owner;
      DO $$ BEGIN
        EXECUTE format('GRANT CONNECT ON DATABASE %I TO nirmana_campaign_control_writer, nirmana_migrator', current_database());
      END $$;
      GRANT USAGE ON SCHEMA public TO nirmana_campaign_control_writer, nirmana_migrator;
      GRANT SELECT, INSERT ON public._migrations_applied TO nirmana_migrator;
      GRANT SELECT ON public.asset_registry, public.nirmana_elevation_monitor_observations, public.build_runs, public.build_run_assets, public.asset_provenance_receipts, public._migrations_applied TO nirmana_campaign_control_writer;
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
      -- The incoming owner is normally fresh, but normalize its defaults too
      -- while the temporary transaction-local owner membership still exists.
      DO $$
      DECLARE default_acl record; object_kind text; scope_clause text;
      BEGIN
        FOR default_acl IN
          SELECT defaults.defaclobjtype, namespace.nspname AS schema_name
            FROM pg_default_acl defaults
            JOIN pg_roles grantor ON grantor.oid = defaults.defaclrole
            LEFT JOIN pg_namespace namespace ON namespace.oid = defaults.defaclnamespace
           WHERE grantor.rolname = 'nirmana_evidence_owner'
        LOOP
          object_kind := CASE default_acl.defaclobjtype
            WHEN 'r' THEN 'TABLES' WHEN 'S' THEN 'SEQUENCES'
            WHEN 'f' THEN 'FUNCTIONS' WHEN 'T' THEN 'TYPES'
            WHEN 'n' THEN 'SCHEMAS' ELSE NULL
          END;
          IF object_kind IS NULL THEN
            RAISE EXCEPTION 'refusing unknown evidence-owner default ACL object kind %', default_acl.defaclobjtype;
          END IF;
          scope_clause := CASE WHEN default_acl.schema_name IS NULL OR default_acl.defaclobjtype = 'n'
            THEN '' ELSE format(' IN SCHEMA %I', default_acl.schema_name) END;
          EXECUTE format(
            'ALTER DEFAULT PRIVILEGES%s REVOKE ALL PRIVILEGES ON %s FROM PUBLIC, amjis_app, nirmana_evidence_ingress_writer, nirmana_campaign_control_writer, nirmana_migrator',
            scope_clause, object_kind
          );
        END LOOP;
      END $$;
      -- Same hard-wired-default closure for the only future campaign-object
      -- grantor.  This runs as the temporary NOLOGIN evidence owner.
      ALTER DEFAULT PRIVILEGES REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC;
      ALTER DEFAULT PRIVILEGES REVOKE USAGE ON TYPES FROM PUBLIC;
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
      -- Finish the provider-owner handoff before testing default ACLs.  The
      -- role switch is transaction-local and the only use of the legacy
      -- direct owner membership; its REVOKE is durable on COMMIT.
      DO $$
      DECLARE database_owner name; direct_owner_membership boolean;
      BEGIN
        SELECT owner.rolname,
               EXISTS (SELECT 1 FROM pg_auth_members membership JOIN pg_roles app ON app.oid = membership.member WHERE membership.roleid = database.datdba AND app.rolname = 'amjis_app')
          INTO database_owner, direct_owner_membership
          FROM pg_database database JOIN pg_roles owner ON owner.oid = database.datdba
         WHERE database.datname = current_database();
        IF direct_owner_membership THEN
          EXECUTE format('SET LOCAL ROLE %I', database_owner);
          ALTER ROLE amjis_app NOINHERIT NOCREATEDB NOCREATEROLE;
          EXECUTE format('REVOKE %I FROM amjis_app', database_owner);
          RESET ROLE;
        ELSE
          ALTER ROLE amjis_app NOINHERIT NOCREATEDB NOCREATEROLE;
        END IF;
      END $$;
      -- Provider-admin roots (the current database owner and postgres) are
      -- exempted from the future-default predicate below only after proving
      -- they are outside every generic/protected writer membership closure.
      DO $$ BEGIN
        IF EXISTS (
          SELECT 1 FROM pg_auth_members membership
            JOIN pg_roles parent ON parent.oid = membership.roleid
            JOIN pg_roles member ON member.oid = membership.member
           WHERE parent.rolname IN ('amjis_app', 'nirmana_evidence_owner', 'nirmana_evidence_ingress_writer', 'nirmana_campaign_control_writer', 'nirmana_migrator')
              OR member.rolname IN ('amjis_app', 'nirmana_evidence_owner', 'nirmana_evidence_ingress_writer', 'nirmana_campaign_control_writer', 'nirmana_migrator')
        ) THEN
          RAISE EXCEPTION 'refusing provider-root default ACL exemption with writer membership closure';
        END IF;
        IF EXISTS (
          SELECT 1 FROM pg_database database WHERE database.datname = current_database()
            AND (database.datdba = 'amjis_app'::regrole OR pg_has_role('amjis_app', database.datdba, 'MEMBER'))
        ) OR has_database_privilege('amjis_app', current_database(), 'CREATE')
          OR EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'amjis_app' AND (rolinherit OR rolcreatedb OR rolcreaterole OR rolsuper OR rolreplication OR rolbypassrls)) THEN
          RAISE EXCEPTION 'generic application role cleanup did not converge';
        END IF;
      END $$;
      -- A default ACL owned by another role cannot be repaired by this
      -- direct-owner transaction.  The provider roots are deliberately
      -- excluded only after the immediately preceding closure proof.
      DO $$
      BEGIN
        IF EXISTS (
          WITH protected_roles(name) AS (
            SELECT unnest(ARRAY['nirmana_evidence_owner', 'nirmana_evidence_ingress_writer', 'nirmana_campaign_control_writer', 'nirmana_migrator'])
          ), provider_roots(oid) AS (
            SELECT datdba FROM pg_database WHERE datname = current_database()
            UNION SELECT oid FROM pg_roles WHERE rolname = 'postgres'
          )
          SELECT 1
            FROM pg_default_acl defaults
            JOIN pg_roles grantor ON grantor.oid = defaults.defaclrole
            CROSS JOIN LATERAL aclexplode(defaults.defaclacl) AS default_grant
            LEFT JOIN pg_roles grantee ON grantee.oid = default_grant.grantee
           WHERE grantor.oid NOT IN (SELECT oid FROM provider_roots)
             AND default_grant.grantee <> defaults.defaclrole
             AND (default_grant.grantee = 0 OR grantee.rolname IN (SELECT name FROM protected_roles))
             AND (
               (defaults.defaclobjtype = 'n' AND has_database_privilege(grantor.rolname, current_database(), 'CREATE'))
               OR (defaults.defaclobjtype <> 'n' AND EXISTS (
                 SELECT 1 FROM pg_namespace namespace
                  WHERE (defaults.defaclnamespace = 0 OR defaults.defaclnamespace = namespace.oid)
                    AND namespace.nspname !~ '^pg_' AND namespace.nspname <> 'information_schema'
                    AND has_schema_privilege(grantor.rolname, namespace.oid, 'CREATE')
                    AND EXISTS (SELECT 1 FROM protected_roles protected WHERE has_schema_privilege(protected.name, namespace.oid, 'USAGE'))
               ))
             )
        ) THEN
          RAISE EXCEPTION 'refusing relevant protected-writer default ACLs';
        END IF;
        -- Missing global f/T rows are not neutral.  The preceding closure
        -- proof is what makes the provider-root exception safe; all other
        -- relevant grantors remain strict fail-closed checks.
        IF EXISTS (
          WITH protected_roles(name) AS (
            SELECT unnest(ARRAY['nirmana_evidence_owner', 'nirmana_evidence_ingress_writer', 'nirmana_campaign_control_writer', 'nirmana_migrator'])
          ), provider_roots(oid) AS (
            SELECT datdba FROM pg_database WHERE datname = current_database()
            UNION SELECT oid FROM pg_roles WHERE rolname = 'postgres'
          )
          SELECT 1
            FROM pg_roles grantor
           WHERE NOT grantor.rolsuper
             AND grantor.oid NOT IN (SELECT oid FROM provider_roots)
             AND EXISTS (
             SELECT 1 FROM pg_namespace namespace
              WHERE namespace.nspname !~ '^pg_' AND namespace.nspname <> 'information_schema'
                AND has_schema_privilege(grantor.rolname, namespace.oid, 'CREATE')
                AND EXISTS (SELECT 1 FROM protected_roles protected WHERE has_schema_privilege(protected.name, namespace.oid, 'USAGE'))
           )
             AND (
               NOT EXISTS (
                 SELECT 1 FROM pg_default_acl defaults
                  WHERE defaults.defaclrole = grantor.oid AND defaults.defaclnamespace = 0 AND defaults.defaclobjtype = 'f'
                    AND NOT EXISTS (
                      SELECT 1 FROM aclexplode(defaults.defaclacl) AS default_grant
                       WHERE default_grant.grantee = 0 AND default_grant.privilege_type = 'EXECUTE'
                    )
               )
               OR NOT EXISTS (
                 SELECT 1 FROM pg_default_acl defaults
                  WHERE defaults.defaclrole = grantor.oid AND defaults.defaclnamespace = 0 AND defaults.defaclobjtype = 'T'
                    AND NOT EXISTS (
                      SELECT 1 FROM aclexplode(defaults.defaclacl) AS default_grant
                       WHERE default_grant.grantee = 0 AND default_grant.privilege_type = 'USAGE'
                    )
               )
             )
        ) THEN
          RAISE EXCEPTION 'refusing hard-wired PUBLIC function/type defaults for a protected-writer grantor';
        END IF;
      END $$;
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
